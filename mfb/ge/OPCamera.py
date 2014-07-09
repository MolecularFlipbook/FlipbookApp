# import blender gamengine modules
from bge import logic
from bge import events
from bge import render
from bge import texture

from . import bgui
from . import shader
from . import fileInterface

from .settings import *
from .helpers import *

import colorsys, random

header = "Display"

def update(panel):
	''' called when model has changed'''
	showPanel(panel)

def destroy(panel):
	pass

def showPanel(panel):
	w = bgui.Checkbox(panel, "gate", small=True, size=[180,20], pos=[0,100])
	w.state = getGate()
	w.on_left_release = setGate
	w.tooltip = 'Toggles the boundary that marks the edge of the camera'

	bgui.Label(panel, 'arPrompt', text='Show Viewport at Aspect Ratio', sub_theme='whiteLabel', pos=[20,100])
	arLabel = bgui.FrameButton(panel, 'indicator', text='', size=[50,20], pos=[200,95], radius=3, sub_theme='icons')
	arLabel.lighter = True
	arLabel.on_left_release = logic.gate.ARSwitch
	arLabel.tooltip = "Camera Aspect Ratio, click to change"
	logic.gate.ARSwitch(arLabel, switch=False)

	bgui.Label(panel, "gridLb", text="Show Grid", pos=[20, 80], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	w = bgui.Checkbox(panel, "grid", small=True, size=[80,20], pos=[0,80])
	w.state = getGrid()
	w.on_left_release = setGrid
	w.tooltip = 'Toggles the XY grid in the scene'

	bgui.Label(panel, "ssaoLb", text="Show Ambient Occlusion", pos=[20, 60], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	w = bgui.Checkbox(panel, "ssao", small=True, size=[150,20], pos=[0,60])
	w.state = getSSAO()
	w.on_left_release = setSSAO
	w.tooltip = 'Toggles contact shadow. Turn off for better performance.'

	def drawLine1():
		drawLine(panel.position[0]+270, panel.position[1]+130, panel.position[0]+270, panel.position[1], (1.0, 1.0, 1.0, 0.2))
	line1 = bgui.Custom(panel, 'line1', func=drawLine1)

	bgui.Label(panel, "skyLabel", text="Background Color", pos=[290, 100], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	white = bgui.FrameButton(panel, 'bgWhite', text='White', size=[80,22], pos=[300,70], radius=3, sub_theme='icons')
	white.on_left_release = setSky
	white = bgui.FrameButton(panel, 'bgBlack', text='Black', size=[80,22], pos=[300,45], radius=3, sub_theme='icons')
	white.on_left_release = setSky
	white = bgui.FrameButton(panel, 'bgRandom', text='Random', size=[80,22], pos=[300,20], radius=3, sub_theme='icons')
	white.on_left_release = setSky
	
	def drawLine2():
		drawLine(panel.position[0]+420, panel.position[1]+130, panel.position[0]+420, panel.position[1], (1.0, 1.0, 1.0, 0.2))
	line1 = bgui.Custom(panel, 'line2', func=drawLine2)

	bgui.Label(panel, "skyLabel2", text="Background Image", pos=[450, 100], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	white = bgui.FrameButton(panel, 'bgImage', text='Image', size=[80,22], pos=[460,70], radius=3, sub_theme='icons')
	white.on_left_release = setSky

	w = bgui.Checkbox(panel, 'fixed', text='Stretch', small=True, size=[50,15], pos=[460,50])
	w.state = getUseBGStretch()
	w.on_left_release = setUseBGStretch
	w.tooltip = 'Toggles streching of the image'

	return


def setGate(widget):
	logic.gate.visible = widget.state


def getGate():
	return logic.gate.visible


def setGrid(widget):
	logic.gui.gridVisible(widget.state)


def getGrid():
	return logic.scene.objects['Grid'].visible


def setSky(widget):
	if widget.name == 'bgWhite':
		logic.mvb.bgColor = defaultSkyColor[:]
		logic.mvb.bgColorFactor = 1.0
		removeTexture()
	elif widget.name == 'bgBlack':
		logic.mvb.bgColor = defaultSkyColorDark[:]
		logic.mvb.bgColorFactor = 1.0
		removeTexture()
	elif widget.name == 'bgRandom':
		logic.mvb.bgColor = list(colorsys.hsv_to_rgb(random.random(), 0.3, 0.3))
		logic.mvb.bgColorFactor = 1.0
		removeTexture()
	elif widget.name == 'bgImage':
		logic.mvb.bgColorFactor = 0.0
		url = fileInterface.browseFile()
		logic.mvb.bgImage = url
		if url.endswith(('.mp4', '.avi', '.mov', '.wmv')):
			updateTexture(animated = True)
		else:
			updateTexture(animated = False)

	else:
		return
	
	shader.updateSky(logic.scene.objects['Sphere'])


def updateTexture(animated = False):
	print('animated: ', animated)
	obj = logic.scene.objects['Sphere']
	ID = texture.materialID(obj, 'MAsky')
	objectTextures = texture.Texture(obj, ID)

	# create a new source with an external image
	if animated:
		source = texture.VideoFFmpeg(logic.mvb.bgImage)
	else:
		source = texture.ImageFFmpeg(logic.mvb.bgImage)


	# the texture has to be stored in a permanent Python object
	logic.skyTexture = objectTextures
	logic.skyTexture.source = source

	logic.skyTextureAnimated = animated
	
	if animated:
		logic.skyTexture.source.repeat = -1
		logic.skyTexture.source.play()
	logic.skyTexture.refresh(True)


def removeTexture():
	"""Delete the Dynamic Texture, reversing back the final to its original state."""
	try:
		del logic.skyTexture
		del logic.skyTextureAnimated
	except:
		pass


def getSSAO():
	return logic.controllerObject['ssao']


def setSSAO(widget):
	logic.controllerObject['ssao'] = widget.state


def getUseBGStretch():
	return logic.mvb.bgImageStretch
	

def setUseBGStretch(widget):
	logic.mvb.bgImageStretch = widget.state
	shader.updateSky(logic.scene.objects['Sphere'])
	