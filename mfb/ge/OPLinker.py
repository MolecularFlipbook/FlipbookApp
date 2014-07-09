# import blender gamengine modules
from bge import logic
from bge import events
from bge import render
from bge import constraints

from . import bgui
from . import OPEditor

from .settings import *
from .helpers import *

import math

angstromPerAA = 8

# the title text for the option panel
header = "Flexible\nLinker"

def update(panel):
	# do not update in release mode
	# because this is not an context sensitive panel
	if useDebug:
		# showPanel(panel)
		pass


def destroy(panel):
	try:
		logic.registeredFunctions.remove(previewLinker)
	except:
		pass


def showPanel(panel):

	# make sure old listener is removed
	for func in logic.registeredFunctions:
		if func.__name__ == previewLinker.__name__:
			logic.registeredFunctions.remove(func)

	markers = getAllMarkers()
	markersList = [label for label, value in markers.items()]

	bgui.Label(panel, "startLb", text="Starting linker marker:", pos=[10, 110], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	bgui.Dropdown(panel, "startMarker", items=markersList, size=[200,20], pos=[10, 80], caller=panel)


	bgui.Label(panel, "endLb", text="Ending linker marker:", pos=[10, 50], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	dd = bgui.Dropdown(panel, "endMarker", items=markersList, size=[200,20], pos=[10, 20], caller=panel)
	if len(markersList) >= 2:
		dd.clickHandler(1)  # set second item as default

	# global display options
	def drawLine1():
		drawLine(panel.position[0]+250, panel.position[1]+130, panel.position[0]+250, panel.position[1], (1.0, 1.0, 1.0, 0.2))
	line1 = bgui.Custom(panel, 'line1', func=drawLine1)
	
	bgui.Label(panel, "promptLb", text="Create linker based on:", pos=[280, 110], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)

	bgui.Label(panel, "r1Lb", text="current location of linker markers", pos=[300, 85], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	cb = bgui.Checkbox(panel, "r1CB", small=True, state=True, size=[160,15], pos=[280,85])
	cb.on_left_release = radioClick

	bgui.Label(panel, "r2Lb", text="length of \t\t\t\t\t amino acids", pos=[300, 60], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	bgui.TextInput(panel, "r2Text", size=[50,20], pos=[360, 55])

	cb = bgui.Checkbox(panel, "r2CB", small=True, size=[60,15], pos=[280,60])
	cb.on_left_release = radioClick

	bgui.Label(panel, "r3Lb", text="length of \t\t\t\t\t angstroms", pos=[300, 35], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	bgui.TextInput(panel, "r3Text", size=[50,20], pos=[360, 30])
	cb = bgui.Checkbox(panel, "r3CB", small=True, size=[60,15], pos=[280,35])
	cb.on_left_release = radioClick

	# create = bgui.FrameButton(panel, "createLinker",  text="Create Linker", radius = 5, size=[80,32], pos=[590, 20])
	create = bgui.FrameButton(panel, "createLinker",  text="Coming Soon", radius = 5, size=[80,32], pos=[590, 20])
	# create.on_left_release = createLinker

	# add new listener
	logic.registeredFunctions.append(previewLinker)


def createLinker(widget=None):
	previewLinker(confirm = True)


def previewLinker(confirm = False):
	if logic.options.view == 'LINKER':
		widgets = logic.options.container.children

		startKey = widgets['startMarker'].currentItem
		endKey = widgets['endMarker'].currentItem

		if startKey == endKey:
			# Cannot Create Marker to self
			return True
		else:
			markers = getAllMarkers()
			resA, indexA, markerA = markers[startKey]
			resB, indexB, markerB = markers[endKey]

			nameA, resLabelA = startKey.split(':')
			nameB, resLabelB = endKey.split(':')
			
			# compute distance
			locA = OPEditor.residueToWorldPosition(logic.mvb.objects[nameA], resA)
			locB = OPEditor.residueToWorldPosition(logic.mvb.objects[nameB], resB)
			dist_nm = (locA-locB).length
						
			if widgets['r1CB'].state:
				radioSelection = 1
				# update value in UI:
				widgets['r3Text'].text = str(int(dist_nm*10*1.1))
				widgets['r2Text'].text = str(int(dist_nm*10/angstromPerAA*1.1))
				
			elif widgets['r2CB'].state:
				radioSelection = 2
				try:
					userValue = float(widgets['r2Text'].text)
				except:
					userValue = 0

			elif widgets['r3CB'].state:
				radioSelection = 3
				try:
					userValue = float(widgets['r3Text'].text)
				except:
					userValue = 0

			else:
				radioSelection = 0

			if radioSelection == 1:
				# using current location and linear distance
				plotPath(markerA, markerB, dist_nm, confirm)
			elif radioSelection == 2:
				# using aa length
				plotPath(markerA, markerB, userValue*angstromPerAA/10.0, confirm)
			elif radioSelection == 3:
				# using nm
				plotPath(markerA, markerB, userValue/10.0, confirm)
				
		return True
	else:
		return False


def plotPath(markerA, markerB, length, confirm):
	''' plot path of linker'''

	locA = markerA.worldPosition
	locB = markerB.worldPosition

	# check length
	dist_nm = (locA-locB).length
	if int(length) < int(dist_nm):
		print('error')
		return

	# create blobs
	nmPerSphere = angstromPerAA*0.1
	nuggets = []
	steps = int(dist_nm / nmPerSphere)
	vect = locA-locB


	for i in range(steps):
		i += 1
		loc = locB + vect/steps*i
		x = (i/steps)
		sagFactor = -(2*x-1)**2+1
		loc[2] -= sagFactor*dist_nm*0.2
		
		if confirm:
			obj = logic.scene.addObject('linkerNugget', logic.pivotObject)
			obj.worldPosition = loc
			nuggets.append(obj)
		else:
			obj = logic.scene.addObject('linkerSphere', logic.pivotObject, 1)
			obj.worldPosition = loc

		
	if confirm:
 		createChain(markerA, markerB, nuggets)

def createChain(markerA, markerB, nuggets):

	return

	PhyIDA = markerA.getPhysicsId()
	PhyIDB = markerB.getPhysicsId()

	consType = 12 # 6dof

	for i, nug in enumerate(nuggets):
		PhyIDNug = nug.getPhysicsId()
		if i == 0:
			print('linking head to first nug')
			constraints.createConstraint(PhyIDA, PhyIDNug, consType)
		elif i == len(nuggets)-1:
			print('linking nug to end')
			constraints.createConstraint(PhyIDNug, PhyIDB, consType)
		else:
			print('linking nug to nug')
			PhyIDNext = nuggets[i+1].getPhysicsId()
			constraints.createConstraint(PhyIDNug,PhyIDNext, consType)
	


# ----------------------

def getAllMarkers():
	allMarkers = {}
	for name, obj in logic.mvb.objects.items():	
		for residue, tup in obj.residueSequenceMarked.items():
			label = obj.name + ': ' + residue.name
			value = (residue, tup[0], tup[1])
			allMarkers[label] = value

	if allMarkers:
		return allMarkers
	else:
		return {'Setup markers in the Editor Panel': None}


def radioClick(widget):
	''' mimic radio buttons '''
	widget.parent.children["r1CB"].state = False
	widget.parent.children["r2CB"].state = False
	widget.parent.children["r3CB"].state = False
	widget.state = True
	