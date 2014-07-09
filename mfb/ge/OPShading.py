# import blender gamengine modules
from bge import logic
from bge import events
from bge import render
from bgl import *

from . import bgui
from . import shader

from .settings import *
from .helpers import *

import os
import colorsys
import math
import pdb

swatchMsg = 'Click me to save the current color to this slot'
swatchMsgLoaded = 'Click me to apply the saved color'



# the title text for the option panel
header = "Color &\nShading"

def update(panel):
	''' panel update routine'''
	showPanel(panel)

	# reset swatch
	colPanel = panel.children['col'].children
	for name, widget in colPanel.items():
		if name.startswith('csw'):
			widget.border = 0
			widget.tooltip = swatchMsg
	
	# load swatch color from optionspane datastore
	if 'savedColor' in logic.options.datastore:
		for key, val in logic.options.datastore['savedColor'].items():
			try:
				colPanel[key].color = val
				colPanel[key].tooltip = swatchMsgLoaded
			except:
				# print('No UI widget Found for', key)
				pass

	
	if logic.mvb._activeObjs:
		if len(logic.mvb._activeObjs) == 1:
			rgb = logic.mvb.getMVBObject(list(logic.mvb._activeObjs)[0]).color
			setColorCursor(panel, rgb=rgb)
		else:
			setColorCursor(panel)
	
	else:
		setColorCursor(panel)


def destroy(panel):
	''' panel destroy routine '''
	# special kill, because this widget is not part of the panel (to use global space)
	guiKill(panel.system.children["spot"])


def showPanel(panel, rgba = [0,0,0,0]):
	''' sets up UI'''

	error = unsupported()

	# bg
	mat = bgui.Frame(panel, "mat", size=[250,140], pos=[40,0], border=0, radius=4, sub_theme="invisible", options=bgui.BGUI_NO_FOCUS)

	# label
	if error:
		matLabel = bgui.Label(mat, "matLabel", text=error, pos=[200,120], sub_theme="whiteLabel", options=bgui.BGUI_CENTERY|bgui.BGUI_NO_FOCUS)
	else:
		matLabel = bgui.Label(mat, "matLabel", text="Surface Style", pos=[0,120], sub_theme="whiteLabel", options=bgui.BGUI_CENTERX|bgui.BGUI_NO_FOCUS)

		# shader swatches
		ssw1 = bgui.ImageButton(mat, "ssw1", size=[50,50], pos=[10,60], sub_theme="shaderDefault")
		ssw1.tooltip = "Default"
		ssw1.shader = "default"
		ssw1.on_left_release = setShader

		ssw2 = bgui.ImageButton(mat, "ssw2", size=[50,50], pos=[70,60], sub_theme="shaderSEM")
		ssw2.tooltip = "SEM Look"
		ssw2.shader = "sem"
		ssw2.on_left_release = setShader

		ssw3 = bgui.ImageButton(mat, "ssw3", size=[50,50], pos=[130,60], sub_theme="shaderShiny")
		ssw3.tooltip = "Shiny Plastic"
		ssw3.shader = 'shiny'
		ssw3.on_left_release = setShader

		ssw4 = bgui.ImageButton(mat, "ssw4", size=[50,50], pos=[190,60], sub_theme="shaderToon")
		ssw4.tooltip = "Toon with Edge"
		ssw4.shader = 'toon'
		ssw4.on_left_release = setShader

		ssw5 = bgui.ImageButton(mat, "ssw5", size=[50,50], pos=[10,5], sub_theme="shaderFlat")
		ssw5.tooltip = "Flat and Bright"
		ssw5.shader = 'flat'
		ssw5.on_left_release = setShader

		ssw6 = bgui.ImageButton(mat, "ssw6", size=[50,50], pos=[70,5], sub_theme="shaderExp")
		ssw6.tooltip = "Experimental"
		ssw6.shader = 'exp'
		ssw6.on_left_release = setShader

		ssw7 = bgui.ImageButton(mat, "ssw7", size=[50,50], pos=[130,5], sub_theme="shaderXRay")
		ssw7.tooltip = "Semi-transparent"
		ssw7.shader = 'xray'
		ssw7.on_left_release = setShader

		ssw8 = bgui.ImageButton(mat, "ssw8", size=[50,50], pos=[190,5], sub_theme="shaderUndefined")
		ssw8.tooltip = "Faded"
		ssw8.shader = 'faded'
		ssw8.on_left_release = setShader

	
	# bg
	col = bgui.Frame(panel, "col", size=[400,140], pos=[300,0], border=0, radius=4, sub_theme="invisible", options=bgui.BGUI_NO_FOCUS)
	if error:
		pass
	else:
		# create color panel
		colorPicker = bgui.Image(col, "colorPicker", themeRoot('colorPicker.png'), size=[256, 115], pos=[10,5])
		colorPicker.on_left_active = pickColor
		colorPicker.on_left_release = setColorKeyframe

		# color palette
		colorPanel = bgui.Swatch(col, "colorPanel", radius = 3, size=[30,115-1], pos=[270,5])
		colorPanel.border = 0
		colorPanel.color = rgba

		# label
		swLabel = bgui.Label(col, "swLabel", text="Swatch", pos=[330,125], sub_theme="whiteLabel")
		
		# color swatches
		csw1 = bgui.Swatch(col, "csw1", size=[25,25], pos=[325, 92], sub_theme='swatch')
		csw1.on_left_click = swatchClick
		csw2 = bgui.Swatch(col, "csw2", size=[25,25], pos=[325, 62], sub_theme='swatch')
		csw2.on_left_click = swatchClick
		csw3 = bgui.Swatch(col, "csw3", size=[25,25], pos=[325, 32], sub_theme='swatch')
		csw3.on_left_click = swatchClick
		csw4 = bgui.Swatch(col, "csw4", size=[25,25], pos=[325, 2], sub_theme='swatch')
		csw4.on_left_click = swatchClick
		csw5 = bgui.Swatch(col, "csw5", size=[25,25], pos=[355, 92], sub_theme='swatch')
		csw5.on_left_click = swatchClick
		csw6 = bgui.Swatch(col, "csw6", size=[25,25], pos=[355, 62], sub_theme='swatch')
		csw6.on_left_click = swatchClick
		csw7 = bgui.Swatch(col, "csw7", size=[25,25], pos=[355, 32], sub_theme='swatch')
		csw7.on_left_click = swatchClick
		csw8 = bgui.Swatch(col, "csw8", size=[25,25], pos=[355, 2], sub_theme='swatch')
		csw8.on_left_click = swatchClick

	return


def swatchClick(widget):
	'''called by color swatch'''
	# reset active swatch
	colPanel = widget.parent.children
	for name, w in colPanel.items():
		if name.startswith('csw'):
			w.border = 0
	widget.border = 2

	# if this color is stored
	if 'savedColor' in logic.options.datastore and widget.name in logic.options.datastore['savedColor']:
		# use current color from swatch
		color = logic.options.datastore['savedColor'][widget.name]
		setColor(color)
		setColorKeyframe()
		setColorCursor(widget.parent.parent, rgb=color[:3])
		widget.color = color
		logic.logger.new("Color loaded from swatch")
	# store color to swatch
	else:	
		color = widget.parent.children["colorPanel"].color
		if 'savedColor' in logic.options.datastore:
			logic.options.datastore['savedColor'][widget.name] = color
		else:
			logic.options.datastore['savedColor'] = {}
			logic.options.datastore['savedColor'][widget.name] = color

		widget.color = color
		widget.tooltip = swatchMsgLoaded
		logic.logger.new("Color saved to swatch")

		


def setShader(widget):
	''' apply shader to selected objs'''
	for obj in logic.mvb._activeObjs:
		mvbObj = logic.mvb.getMVBObject(obj)
		mvbObj.shader = widget.shader
	logic.undo.append("Changed Shader")
	logic.mvb.slides[logic.mvb.activeSlide].capture()


def setColor(rgb):
	''' apply RGB to selected objs'''
	for obj in logic.mvb._activeObjs:
		mvbObj = logic.mvb.getMVBObject(obj)
		mvbObj.color = [rgb[0], rgb[1], rgb[2]]


def setColorKeyframe(widget=None):
	'''Only apply undo on mouse-lift'''
	if logic.mvb._activeObjs:
		logic.undo.append("Changed Color")
		logic.mvb.slides[logic.mvb.activeSlide].capture()


def pickColor(widget):
	'''called by color picker'''
	mx, my = logic.gui.mousePos
	x1, y1 = widget.position
	x2, y2 = widget.size

	# normalize mouse coord
	normx = (mx - x1) / x2
	normy = (my - y1) / y2

	# compute color from mouse coord in HSV space
	rgb = list(colorsys.hls_to_rgb(normx, 1.0-normy, 0.8))

	setColor(rgb)
	setColorCursor(widget.parent.parent, rgb = rgb)

	w = widget.parent.children
	rgba = rgb[:]
	rgba.append(1.0)

	if 'savedColor' not in logic.options.datastore:
		logic.options.datastore['savedColor'] = {}

	if w["csw1"].border == 2:
		w["csw1"].color = rgba
		logic.options.datastore['savedColor']['csw1'] = rgba
	elif w["csw2"].border == 2:
		w["csw2"].color = rgba
		logic.options.datastore['savedColor']['csw2'] = rgba
	elif w["csw3"].border == 2:
		w["csw3"].color = rgba
		logic.options.datastore['savedColor']['csw3'] = rgba
	elif w["csw4"].border == 2:
		w["csw4"].color = rgba
		logic.options.datastore['savedColor']['csw4'] = rgba
	elif w["csw5"].border == 2:
		w["csw5"].color = rgba
		logic.options.datastore['savedColor']['csw5'] = rgba
	elif w["csw6"].border == 2:
		w["csw6"].color = rgba
		logic.options.datastore['savedColor']['csw6'] = rgba
	elif w["csw7"].border == 2:
		w["csw7"].color = rgba
		logic.options.datastore['savedColor']['csw7'] = rgba
	elif w["csw8"].border == 2:
		w["csw8"].color = rgba
		logic.options.datastore['savedColor']['csw8'] = rgba



def setColorCursor(panel, rgb=None):
	''' set the color picker reticle'''
	if rgb:
		# compute color panel position
		r,g,b = rgb
		h,l,s = colorsys.rgb_to_hls(r,g,b)
		size = panel.children['col'].children["colorPicker"].size[:]
		pos = panel.children['col'].children["colorPicker"].position[:]
		x = size[0] * h + pos[0]
		y = size[1] * (1.0-l) + pos[1]
		pos = [x,y]
		# update color picker
		bgui.Label(panel.system, "spot", text="•", pos=[pos[0]-4,pos[1]-4], options=bgui.BGUI_NO_FOCUS)
		panel.children['col'].children["colorPanel"].color = [r,g,b,1.0]

	else:
		# hide
		bgui.Label(panel.system, "spot", text="•", pos=[-10,-10], options=bgui.BGUI_NO_FOCUS)
		


def unsupported():
	if logic.mvb._activeObjs:
		return False
	else:
		return 'Nothing Selected'
