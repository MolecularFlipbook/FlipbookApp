# import blender gamengine modules
from bge import logic
from bge import events
from bge import render

from . import bgui
from . import pdbLoader
from . import datastoreUtils

from .settings import *
from .helpers import *

import os, imp, pdb, re
from math import pi

header = "Blobber"

def update(panel):
	''' called when model has changed'''
	# do nothing, because this is not an object sensitive panel
	pass


def destroy(panel):
	'''called when the panel is killed'''
	try:
		logic.registeredFunctions.remove(dragging)
	except:
		pass

	try:
		logic.registeredFunctions.remove(computeDimension)
	except:
		pass

	hideProxy()


def showPanel(panel):

	logic.blobberSliderPriority = False

	# expand options panel size, since this panel might be invoked before a PDB is loaded
	logic.gui.optionsPane.size = [800,150]

	# make sure old listener is removed
	for func in logic.registeredFunctions:
		if func.__name__ == computeDimension.__name__:
			logic.registeredFunctions.remove(func)

	# add new listener
	logic.registeredFunctions.append(computeDimension)

	# invisible placeholder
	optPanel = bgui.Frame(panel, "bgOpt", size=[530,130], pos=[0,5], radius=2, border=0, sub_theme="invisible")

	weightLabel = bgui.Label(optPanel, "weightLabel", text="Molecular Weight", pos=[10,85], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	weightText = bgui.TextInput(optPanel, "weightText", text="40.4", size=[50,25], pos=[20, 50])
	weightText.on_activate = setPriority
	weightText.on_enter_key = setPriority
	weightText.on_edit = setPriority
	unitLabel = bgui.Label(optPanel, "unitLabel", text="kDa", pos=[75,55], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)

	diameterLabel = bgui.Label(optPanel, "diameterLabel", text="Diameter:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  Å", pos=[130,85], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	heightLabel = bgui.Label(optPanel, "heightLabel", text="Height:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tÅ", pos=[140,45], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)

	# draw frame widget containter that will hold train ##
	diameterSlider = bgui.Frame(optPanel, 'diameterSlider', size=[170, 10], pos=[190,85], sub_theme="lowOpacityDark", options=bgui.BGUI_NO_FOCUS)
	diameterSlider.extraPadding = [25,25,10,10]
	diameterSliderTrain = bgui.ImageButton(diameterSlider, 'diameterSliderTrain',sub_theme="timelineTrain", size=[32, 16],options=bgui.BGUI_CACHE|bgui.BGUI_CENTERY)
	diameterSliderTrain.on_left_click = dragStart
	diameterSliderTrain.on_left_release = dragEnd
	diameterSliderTrainLabel = bgui.Label(diameterSliderTrain, 'diameterSliderTrainLabel', text='', sub_theme='blackLabel', offset=[-5,-3], options=bgui.BGUI_TOP|bgui.BGUI_RIGHT|bgui.BGUI_NO_FOCUS)

	# draw frame widget containter that will hold train ##
	heightSlider = bgui.Frame(optPanel, 'heightSlider', size=[170, 10], pos=[190,45], sub_theme="lowOpacityDark", options=bgui.BGUI_NO_FOCUS)
	heightSlider.extraPadding = [25,25,10,10]
	heightSliderTrain = bgui.ImageButton(heightSlider, 'heightSliderTrain',sub_theme="timelineTrain", size=[32, 16],options=bgui.BGUI_CACHE|bgui.BGUI_CENTERY)
	heightSliderTrain.on_left_click = dragStart
	heightSliderTrain.on_left_release = dragEnd
	heightSliderTrainLabel = bgui.Label(heightSliderTrain, 'heightSliderTrainLabel', text='', sub_theme='blackLabel', offset=[-5,-3], options=bgui.BGUI_TOP|bgui.BGUI_RIGHT|bgui.BGUI_NO_FOCUS)

	def drawLine1():
		drawLine(optPanel.position[0]+120, optPanel.position[1]+130, optPanel.position[0]+120, optPanel.position[1], (1.0, 1.0, 1.0, 0.2))

	def drawLine2():
		drawLine(optPanel.position[0]+400, optPanel.position[1]+130, optPanel.position[0]+400, optPanel.position[1], (1.0, 1.0, 1.0, 0.2))

	line1 = bgui.Custom(panel, 'infoLine1', func=drawLine1)
	line2 = bgui.Custom(panel, 'infoLine2', func=drawLine2)

	# name label
	nameLabel = bgui.Label(panel, "nameLabel", text="Name", pos=[430,85], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	nameText = bgui.TextInput(panel, "nameText", text="blobby", size=[80,25], pos=[410, 50])

	okay = bgui.FrameButton(panel, "okay",  text="OK", radius = 5, size=[80,30], pos=[550, 45])
	okay.on_left_release = loadBlob

	showProxy()
	nameText.text = datastoreUtils.incrementName(nameText.text, logic.mvb.objects)




def setPriority(widget):
	logic.blobberSliderPriority = False
	logic.pluggable.panel.createMolecularWeight.notify()

# handler for drag actions
def dragStart(widget):
	"""registers the mouse handler"""
	if dragging in logic.registeredFunctions:
		logic.registeredFunctions.remove(dragging)
	else:
		logic.registeredFunctions.append(dragging)

	showProxy()

# handler for drag actions
def dragging():
	""" handles the draggable timline label widget"""
	if logic.gui.mouse_state == bgui.BGUI_MOUSE_LEFT_RELEASE:
		dragEnd(None)
	else:
		orb = logic.gui.focused_widget
		if 'SliderTrain' in orb.name:	# make sure the slider is the one being dragged
			x = int(logic.gui.mousePos[0] - orb.parent.position[0])

			if x > (orb.parent.size[0]-20):
				x = orb.parent.size[0]-20
			if x < 0:
				x = 0

			orb.position = [x-5, -5]

			return True
		else:
			dragEnd(None)

# handler for drag actions
def dragEnd(widget):
	"""delete the mouse handler"""
	try:
		logic.registeredFunctions.remove(dragging)
		logic.mouseLock = 0
	except:
		pass

# map value from one range to another range
def translate(value, leftMin, leftMax, rightMin, rightMax):
	# Figure out how 'wide' each range is
	leftSpan = leftMax - leftMin
	rightSpan = rightMax - rightMin

	# Convert the left range into a 0-1 range (float)
	valueScaled = float(value - leftMin) / float(leftSpan)

	# Convert the 0-1 range into a value in the right range.
	return rightMin + (valueScaled * rightSpan)

# compuate the cylindrical dimension of the blob given its volume.
def computeDimension():
	def setSliderValue(widget, curr, minn, maxx):
		# clamp value
		if curr>maxx:
			curr = maxx
		elif curr < 0:
			curr = 0

		absPos = translate(curr, minn, maxx, widget.position[0], widget.position[0]+widget.size[0])
		widgetTrain = str(widget.name)+"Train"
		widgetTrainLabel = widgetTrain + "Label"
		widget.children[widgetTrain].position = [absPos-widget.position[0], -5]
		currAngstrom = curr * 10 		# convert from nm to angtrom
		widget.children[widgetTrain].children[widgetTrainLabel].text = str(int(currAngstrom))

	# move placeholder object to centre ob view
	proxy = logic.scene.objects['blobbyPlaceholder']
	proxy.worldPosition = logic.controllerObject.worldPosition

	if logic.options.view == 'CREATE':
		root = logic.options.container.children['bgOpt']
		try:
			kDa = float(root.children['weightText'].text)
		except:
			logic.logger.new("Invalid numeric input", type="ERROR", repeat = False)
			return True
		else:

			# Size and Shape of Protein Molecules at the Nanometer Level Determined by Sedimentation, Gel Filtration, and Electron Microscopy
			# by Harold P. Erickson
			# dimensions are in nm when not specified.

			# compute volume of sphere in nm^3 from weight, assuming specific partial volume of 0.73cm^3/g
			vol = kDa * 1.212

			# r given the molecular weight, use cylindrical volume formula
			r = pow(vol/pi/2, 1/3)

			minScale = 0.3
			maxScale = 3.0

			rMax = r * maxScale
			rMin = r * minScale

			# compute diameter
			dMin = 2.0*rMin
			dMax = 2.0*rMax
			d = 2.0 * r

			# compute height
			h = d

			hMin = h * minScale
			hMax = h * maxScale

			# bail if there is no active widget
			if not logic.gui.focused_widget:
				return True

			# update UI on drag
			if 'diameterSliderTrain' == logic.gui.focused_widget.name and dragging in logic.registeredFunctions:
				track = root.children['diameterSlider']
				widget = track.children['diameterSliderTrain']
				ratio = (logic.gui.mousePos[0] - track.position[0]) / (track.size[0])
				dCurr = (dMax - dMin) * ratio + dMin
				if dCurr < dMin:
					dCurr = dMin
				if dCurr > dMax:
					dCurr = dMax
				widget.children['diameterSliderTrainLabel'].text = str(int(dCurr*10)) 	# display in Angstrom

				#update height
				area = pi*((dCurr/2)**2)
				hDesired = vol / area
				setSliderValue(root.children['heightSlider'], hDesired, hMin, hMax)

				logic.blobberSliderPriority = True

				updateProxy(dCurr=dCurr, hCurr=hDesired)

			# update UI on drag
			elif 'heightSliderTrain' == logic.gui.focused_widget.name and dragging in logic.registeredFunctions:
				track = root.children['heightSlider']
				widget = track.children['heightSliderTrain']
				ratio = (logic.gui.mousePos[0] - track.position[0]) / (track.size[0])
				hCurr = (hMax - hMin) * ratio + hMin
				if hCurr < hMin:
					hCurr = hMin
				widget.children['heightSliderTrainLabel'].text = str(int(hCurr*10)) 	# display in Angstrom

				#update diameter
				area = vol / hCurr
				rDesired = (area/pi)**0.5
				dDesired = 2.0 * rDesired
				setSliderValue(root.children['diameterSlider'], dDesired, dMin, dMax)

				logic.blobberSliderPriority = True

				updateProxy(dCurr=dDesired, hCurr=hCurr)

			# update UI
			elif not logic.blobberSliderPriority:

				diameter = root.children['diameterSlider']
				height = root.children['heightSlider']
				setSliderValue(diameter, d, dMin, dMax)
				setSliderValue(height, h, hMin, hMax)

				logic.blobberSliderPriority = True

				updateProxy(dCurr=d, hCurr=h)

			return True
	else:
		return False


def showProxy():
	''' shows the shape preview'''
	logic.scene.objects['blobbyPlaceholder'].visible = True

def updateProxy(hCurr, dCurr):
	''' updates the shape of the proxy'''
	# blender scene displays everything in nm., i.e. 1 BU == 1 NM
	proxy = logic.scene.objects['blobbyPlaceholder']
	logic.blobbyScale = [dCurr, dCurr, hCurr] # scale in NM
	proxy.worldScale = logic.blobbyScale

def hideProxy():
	''' removes the shape preview'''
	logic.scene.objects['blobbyPlaceholder'].visible = False


def loadBlob(widget=None, scale=None, name=None):
	''' imports the blobber'''
	meshPath = os.path.join(logic.basePath, 'creator', 'geometry.blend')
	if widget:
		blobName = widget.parent.children['nameText'].text
	else:
		blobName = name
	# compute aspect ratio of the blob, in order to load optimal geometry
	if widget:
		ar = logic.blobbyScale[2]/logic.blobbyScale[1]
		blobScale = logic.blobbyScale
	else:
		ar = scale[2]/scale[1]
		blobScale = scale

	if ar < 0.5:
		meshName = "cylinder0x"
	elif ar < 2.0:
		meshName = "cylinder1x"
	elif ar < 4.0:
		meshName = "cylinder2x"
	else:
		meshName = "cylinder4x"

	result = pdbLoader.importGeometry(meshPath, template = meshName, name = blobName, scale = blobScale)
	if result and widget:
		logic.outliner.updateModel()
		hideProxy()
		nameText = widget.parent.children['nameText']
		nameText.text = datastoreUtils.incrementName(nameText.text, logic.mvb.objects)

		logic.pluggable.panel.createBlobby.notify()

	if result:
		return result



