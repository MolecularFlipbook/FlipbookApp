# import blender gamengine modules
from bge import logic
from bge import events
from bge import render

import mathutils

from . import bgui
from . import manipulator
from .settings import *
from .helpers import *
from . import shader

import pdb
import random
import copy
import logging

header = "Protein\nEditor"

#http://en.wikipedia.org/wiki/Amino_acid
#http://www.csb.pitt.edu/prody/reference/atomic/flags.html
aaLookup = {
		'CYS': 'C',
		'ASP': 'D',
		'SER': 'S',
		'GLN': 'Q',
		'LYS': 'K',
		'ILE': 'I',
		'PRO': 'P',
		'THR': 'T',
		'PHE': 'F',
		'ASN': 'N',
		'GLY': 'G',
		'HIS': 'H',
		'LEU': 'L',
		'ARG': 'R',
		'TRP': 'W',
		'ALA': 'A',
		'VAL': 'V',
		'GLU': 'E',
		'TYR': 'Y',
		'MET': 'M',
		'SEC': 'U',
		'PYL': 'O',
		'ASX': 'B',
		'GLX': 'Z',
		'XLE': 'J',
		'XAA': 'X',
		'CSO': 'C',
		'HIP': 'H',
		'HSD': 'H',
		'HSE': 'H',
		'HSP': 'H',
		'SEP': 'S',
		'TPO': 'T',
		'PTR': 'Y'
		}

aaIgnore = ['HOH']

def update(panel):
	''' called when model has changed'''
	drawModeReset()
	showPanel(panel)


def destroy(panel):
	''' called when the panel is removed '''
	drawModeReset()


def showPanel(panel):
	'''set up the UI'''
	valid = False
	aaStringMarker = ''   	# top text string, used for marking residue
	aaStringText = ''		# residue text string
	aaStringIndex = ''		# bottom residue number string

	if not (logic.mvb._activeObjs):
		chainLabel = "Nothing Selected"
	elif len(logic.mvb._activeObjs) > 1:
		chainLabel = "Multiple Selection"
	else:
		chainName, residues, residueStr, residueNumStr = getAAString(list(logic.mvb._activeObjs)[0])
		if chainName:
			chainLabel = chainName + " Chain Data"
			aaStringText = residueStr
			aaStringIndex = residueNumStr
			valid = True
		else:
			chainLabel = "Non-PDB objects are not supported"

	if valid:
		# show backbone geometry for active selection
		if logic.mvb._activeObjs:
			for obj in logic.mvb._activeObjs:
				mvbObj = logic.mvb.getMVBObject(obj)
				drawOverride(mvbObj, 'ribbon')

			# ensure consistent display of markers
			textList = [' ']*len(aaStringText)
			for residue, data in mvbObj.residueSequenceMarked.items():
				index, kxObj = data
				textList[index] = "•"
			aaStringMarker = "".join(textList)


	titleBG = bgui.Frame(panel, 'title', size=[450,20], pos=[0,110], options=bgui.BGUI_NO_FOCUS)
	titleBG.border = 0

	bgui.Label(titleBG, 'titleText', text= chainLabel, sub_theme="whiteLabel", pos=[10,3])
	bgui.Label(titleBG, 'titleSubText', text='', pos=[200,3], sub_theme='whiteLabel')

	scroller = bgui.Scroll(panel, 'scroller', size=[450,60], pos=[0,50], actual=[1,1])
	scroller.extraPadding = [10,10,10,10]

	scrollerBG = bgui.Frame(scroller, 'scrollerBG', size=[0,0], pos=[0,0], sub_theme="lowOpacityDark", options=bgui.BGUI_NO_FOCUS|bgui.BGUI_FILLED)
	aaStringTop = bgui.Label(scroller, 'aaStringTop', text=aaStringMarker, pos=[0,48], sub_theme='mono', options=bgui.BGUI_NO_FOCUS)
	aaStringBottom = bgui.Label(scroller, 'aaStringBottom', text=aaStringIndex, pos=[0,21], sub_theme='monoHalf', options=bgui.BGUI_NO_FOCUS)
	aaString = bgui.Label(scroller, 'aaString', text=aaStringText, pos=[0,35], sub_theme='mono')
	aaString.extraPadding = [0,0,10,30]
	aaString.on_hover = previewResidue
	aaString.on_mouse_exit = previewResidueExit
	aaString.on_left_click = selectResidue

	but1 = bgui.FrameButton(panel, 'but1', text="Add Marker", radius=5, size=[120,30], pos=[0,10])
	but1.on_left_click = markResidue
	but2 = bgui.FrameButton(panel, 'but2', text="Cut Chain", radius=5, size=[120,30], pos=[140,10])
	but2.on_left_click = splitResidue
	but3 = bgui.FrameButton(panel, 'but3', text="View Sidechains", radius=5, size=[120,30], pos=[280,10])
	but3.on_left_click = notImplemented

	subPanel = bgui.Frame(panel, 'subPanel', size=[225,120], pos=[460,10], radius=3, sub_theme="lowOpacityDark", options=bgui.BGUI_NO_FOCUS)

	if adjustDimension not in logic.registeredFunctions:
		logic.registeredFunctions.append(adjustDimension)

	return


def previewResidue(widget):
	''' handles mouse-over event for residue string widget'''
	rdata = __getResidue__(widget)
	if rdata:
		mvbObj, index, residue = rdata
		aaStringTop = widget.parent.children['aaStringTop']
		textList = aaStringMarkerUpdate(aaStringTop, mvbObj)
		textList[index] = "."
		aaStringTop.text = "".join(textList)

		# show selected residue
		showSelectedResidue(widget, real=False)

		# show residue in panel
		detail = widget.parent.parent.children['title'].children['titleSubText']
		detail.text = residue.name

		# show residue in 3d space
		loc = residueToWorldPosition(mvbObj, residue)
		showResidue(mvbObj, loc)
		
		# showTempMarker at loc
		logic.markerKey.worldPosition = loc


def previewResidueExit(widget):
	''' handles mouse-leave event for residue string widget'''

	showSelectedResidue(widget, real=False)

	aaStringTop = widget.parent.children['aaStringTop']
	textList = aaStringTop.text[:].replace('.', ' ')
	aaStringTop.text = "".join(textList)

	# kill the line widget
	try:
		widget = logic.gui.children['residueInfoLine']
		widget.kill()
		del widget
	except:
		pass

	logic.markerKey.worldPosition = (10000,0,0)


def selectResidue(widget):
	logic.rdata = __getResidue__(widget)
	showSelectedResidue(widget)
	logic.pluggable.panel.rData.notify()


def showSelectedResidue(widget, real=True):
	if hasattr(logic, 'rdata') and logic.rdata:
		mvbObj, listIndex, residue = logic.rdata

		aaStringTop = widget.parent.children['aaStringTop']
		textList = list(aaStringTop.text[:])
		if real:
			textList[listIndex] = "•"
		else:
			textList[listIndex] = "v"

		aaStringTop.text = "".join(textList)

		if residue in mvbObj.residueSequenceMarked:
			# present remove marker option
			logic.options.container.children['but1'].text = 'Remove Marker ' + residue.name
			logic.options.container.children['but2'].text = 'Cut Chain at ' + residue.name
		else:
			# present Marker marker option
			logic.options.container.children['but1'].text = 'Add Marker ' + residue.name
			logic.options.container.children['but2'].text = 'Cut Chain at ' + residue.name
			

def showResidue(mvbObj, loc):
	''' point to the residue in screenspace'''
	mousex, mousey = logic.gui.mousePos
	mousey = render.getWindowHeight() - 180

	finalx,finaly = logic.viewCamObject.getScreenPosition(loc)[:]
	finaly = 1- finaly
	finalx *= render.getWindowWidth()
	finaly *= render.getWindowHeight()

	def drawLineDark():
		drawLine(int(mousex),int(mousey), int(finalx),int(finaly), (0.0, 0.0, 0.0, 0.2))
	bgui.Custom(logic.gui, 'residueInfoLine', func=drawLineDark)


def markResidue(widget):
	if hasattr(logic, 'rdata') and logic.rdata:
		mvbObj, listIndex, residue = logic.rdata

		if residue in mvbObj.residueSequenceMarked:
			# remove marker
			del mvbObj.residueSequenceMarked[residue]
			mvbObj.updateMarkers()
		else:
			# set marker
			mvbObj.residueSequenceMarked[residue] = (listIndex, None)
			mvbObj.updateMarkers()

		logic.rdata = None
		panel = logic.options.container
		update(panel)
		logic.pluggable.panel.rData.notify()

		# keyframe
		logic.mvb.slides[logic.mvb.activeSlide].capture()


def splitResidue(widget):
	''' handles click event for residue string'''
	notImplemented()
	return
	rdata = __getResidue__(widget)
	if rdata:
		mvbObj, listIndex, residue = rdata
		print(mvbObj, listIndex, residue)
	
		chainA = mvbObj.chainData.residues[listIndex:]
		chainB = mvbObj.chainData.residues[:listIndex]


		# # pdb.set_trace()
		# # from . import backbone
		# # backbone.Build(pdbid, self.pdbFullPath, logic.basePath, logic.tempFilePath, self.mol)


		# A = mvbObj.chainData.split(chainA)
		# B = mvbObj.chainData.split(chainB)
		


# ----- utility functions --------
def getAAString(obj):
	''' given the obj, outputs the residueSequence'''
	mvbObj = logic.mvb.getMVBObject(obj)

	if (not mvbObj) or mvbObj.type != 0 or not mvbObj.pdbData:          # invalide obj
		return [None, None, None, None]

	if mvbObj.residueSequence:
		# Using cached data
		return mvbObj.residueSequence

	else:
		# go through the molkit datastructure
		counter = -1
		shortNameStr = ''
		residueObjects = []
		numberStr = ''
		fuzzyness = 5 			# Used to prevent residue addition using the 100A, 100B notation.

		isProteic = mvbObj.chainData.isProteic()   	# does not seem to be reliable
		isDNA = mvbObj.chainData.isDna()			# does not seem to be reliable

		logging.info(str(mvbObj.chainData.full_name()) + " is Proteic: " + str(isProteic))
		logging.info(str(mvbObj.chainData.full_name()) + " is Dna: " + str(isDNA))

		# decide which parser to use
		if isProteic:
			useProteinParser = True
		elif isDNA:
			useProteinParser = False
		else:
			#sample some randome residues:
			logging.info("Sampling the chain to see whether it's protein or nucleic acid")

			proteinBias = 0

			for i in range(20):
				maxRange = len(mvbObj.chainData.residues)
				randomInt = random.randrange(1,maxRange)
				try:
					sample = mvbObj.chainData.residues[randomInt].type.strip()
				except:
					pass
				else:
					if len(sample) == 3:
						proteinBias += 1
					elif len(sample) == 2:
						proteinBias -= 1

			if proteinBias > 10:
				useProteinParser = True
			elif proteinBias < -10:
				useProteinParser = False
			else:
				logging.warning("Ambiguous chain, unsure if protein or nucleic acid")
				return '', '', ''

		logging.info("Parsing using ProteinParser: " + str(useProteinParser))

		# ensure consistent display of index
		interval = 5
		fontScaling = 1

		for i, residue in enumerate(mvbObj.chainData.residues):

			# get name
			aa = residue.type.strip().upper()

			if useProteinParser:
				# sanity check
				if (int(residue.number)+fuzzyness) < counter:
					print("Possible problem at", residue.number)
				counter = int(residue.number)

				if len(aa) == 3:
					shortName = aaLookup.get(aa)
					if shortName is not None:
						shortNameStr += shortName
						residueObjects.append(residue)
					elif aa in aaIgnore:
						...
					else:
						#print("Unknown residue:", aa)
						shortNameStr += '?'
						residueObjects.append(residue)
				else:
					print("Uncomforming residue (Not 3 letters):", aa)
			else:
				# sanity check
				if (int(residue.number)+fuzzyness) < counter:
					print("Possible problem at", residue.number)
				counter = int(residue.number)

				if len(aa) == 2 and aa.startswith("D"):
					shortNameStr += aa[1]
					residueObjects.append(residue)
				elif aa in aaIgnore:
					...
				else:
					#print ("Unknown Non AA Residue", aa)
					shortNameStr += '?'
					residueObjects.append(residue)


			if i%interval==0:
				seg = str(residue.number).ljust(interval*fontScaling)
				numberStr += seg

		mvbObj.residueSequence = [mvbObj.chainData.full_name(), residueObjects, shortNameStr, numberStr]
		return mvbObj.residueSequence


def __getResidue__(widget):
	''' get residue from the mouse position over the text widget'''
	charWidth = widget.size[0]/len(widget.text)  	# replace with widget.dimension[0]/len(widget.text)?
	mousePos = widget.system.mousePos
	mouseHitPoint = mousePos[0] - widget.position[0]
	index = int(round(mouseHitPoint/charWidth-0.5, 0))
	obj = list(logic.mvb._activeObjs)[0]
	mvbObj = logic.mvb.getMVBObject(obj)
	chainName, residues, residueStr, residueNumStr = mvbObj.residueSequence
	try:
		res = residues[index]
		return (mvbObj, index, res)
	except:
		return None


def notImplemented(widget=None):
	logic.logger.new("This function is not implemented yet", "WARNING")


def drawModeReset():
	'''make drawmode consistent'''
	for name, mvbObj in logic.mvb.objects.items():
		if mvbObj.type == 0:
			prevMode = mvbObj.drawMode 	# Needed to avoid the caching behavior
			mvbObj.drawMode = None
			mvbObj.drawMode = prevMode


def drawOverride(mvbObj, value):
	'''used to override the drawmode without actually committing to datastore'''
	if value == 'surface':
		mvbObj.obj.replaceMesh(mvbObj.surfaceMesh)
	elif value == 'fineSurface':
		mvbObj.obj.replaceMesh(mvbObj.fineSurfaceMesh)
	elif value == 'ribbon':
		mvbObj.obj.replaceMesh(mvbObj.ribbonMesh)
	else:
		pass

	shader.initProtein(mvbObj.obj, 'semLit')


def residueToWorldPosition(mvbObj, residue):
	'''compute location of residue in worldSpace'''
	locMarker = None

	# find keystone atom
	for atom in residue.atoms:
		if atom.name == 'CA':
			locMarker = atom._coords[0]
			#print ("using alpha carbon placement")
		if atom.name == 'P':
			locMarker = atom._coords[0]
			#print ("using phosphorous placement")

	# use center of residue (fallback)
	if not locMarker:
		locMarker = residue.getCenter()

	locChain = mvbObj.chainData.getCenter()

	locWorld = mvbObj.loc
	rotWorld = mvbObj.rot

	scaleFactor = 0.1

	markerLoc = [0,0,0]
	markerLoc[0] = (locMarker[0]-locChain[0])*scaleFactor
	markerLoc[1] = (locMarker[1]-locChain[1])*scaleFactor
	markerLoc[2] = (locMarker[2]-locChain[2])*scaleFactor

	rotMatrix = mvbObj.rot.to_matrix().to_4x4()
	locMatrix = mathutils.Matrix.Translation(mvbObj.loc)

	combinedMatrix = locMatrix * rotMatrix

	newLoc = combinedMatrix * mathutils.Vector(markerLoc)

	return newLoc


def aaStringMarkerUpdate(widget, mvbObj):
	textList = [' ']*len(widget.text)
	for residue, data in mvbObj.residueSequenceMarked.items():
		markerIndex, kxobj = data
		textList[markerIndex] = "•"

	return textList


def adjustDimension():
	'''fit the scrollable area to the widget of content'''
	try:
		scroller = logic.gui.optionsPane.children['container'].children['scroller']
		aaString = scroller.children['aaString']
	except:
		return False

	if aaString.dimension:
		# fit and remove self
		scroller.fitX(int(aaString.dimension[0])+20.0)
		return False
	else:
		# wait next tic
		return True
