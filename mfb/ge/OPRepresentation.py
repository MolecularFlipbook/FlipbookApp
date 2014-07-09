# import blender gamengine modules
from bge import logic
from bge import events
from bge import render

from . import bgui

from .settings import *
from .helpers import *

# the title text for the option panel
header = "Display as"

def update(panel):
	showPanel(panel)

def destroy(panel):
	pass

def showPanel(panel):
	error = unsupported()

	b = bgui.FrameButton(panel, "hidden", text="Invisible", size=[100,28], pos = [135,96], radius=3)
	b.on_hover = hover
	b.on_left_release = click
	b = bgui.FrameButton(panel, "surface", text="Surface", size=[100,28], pos = [135,67], radius=3)
	b.on_hover = hover
	b.on_left_release = click
	b = bgui.FrameButton(panel, "fineSurface", text="Fine Surface", size=[100,28], pos = [135,38], radius=3)
	b.on_hover = hover
	b.on_left_release = click
	b = bgui.FrameButton(panel, "ribbon", text="Ribbon", size=[100,28], pos = [135,9], radius=3)
	b.on_hover = hover
	b.on_left_release = click

	frame = bgui.Frame(panel, 'frame', size=[115,115], border=0, radius=0, pos=[21,9], options=bgui.BGUI_NO_FOCUS )
	scroller = bgui.Scroll(panel, 'scroll', size=[128,128], pos=[15,0], actual=[1,4], options=bgui.BGUI_NO_FOCUS)
	if error:
		bgui.Label(panel, 'error', text = error, pos = [30,70], sub_theme='whiteLabelSmall', options=bgui.BGUI_NO_FOCUS)
	else:
		bgui.Label(panel, 'error', text = '', pos = [30,70], sub_theme='whiteLabelSmall', options=bgui.BGUI_NO_FOCUS)
		bgui.Image(scroller, 'image', themeRoot("displayModes.png"), pos=[0,0], size=[128, 512], options=bgui.BGUI_NO_FOCUS)

	# global display options
	def drawLine1():
		drawLine(panel.position[0]+270, panel.position[1]+130, panel.position[0]+270, panel.position[1], (1.0, 1.0, 1.0, 0.2))
	line1 = bgui.Custom(panel, 'line1', func=drawLine1)
	

def unsupported():
	if logic.mvb._activeObjs:
		for obj in logic.mvb._activeObjs:
			mvbObj = logic.mvb.getMVBObject(obj)
			if mvbObj.type != 0:
				return "Non-PDB objects\nare not supported"
	else:
		return "Nothing Selected"
	return False


def hover(widget):
	scroll = widget.parent.children["scroll"]
	if widget.name == "hidden":
		scroll._desiredScroll = [0,1.66]
	if widget.name == "surface":
		scroll._desiredScroll = [0,1.0]
	if widget.name == "fineSurface":
		scroll._desiredScroll = [0,0.66]
	if widget.name == "ribbon":
		scroll._desiredScroll = [0,0.33]


def click(widget):
	mode = widget.name
	if logic.mvb._activeObjs:
		for obj in logic.mvb._activeObjs:
			mvbObj = logic.mvb.getMVBObject(obj)

			try:
				mvbObj.drawMode = mode
				# save keyframe
				logic.mvb.slides[logic.mvb.activeSlide].capture()
			except Exception as E:
				print (E)