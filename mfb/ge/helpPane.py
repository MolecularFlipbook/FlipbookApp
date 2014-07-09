# import blender gamengine modules
from bge import logic
from bge import events
from bge import render

from . import bgui

from .settings import *
from .helpers import *


class Helper():
	def __init__(self, canvas):
		self.canvas = canvas

		self.b1 = bgui.FrameButton(canvas, 'b1', centerText=False, text="\t1. Introduction", sub_theme='listEntry', size=[150,20], offset=[0,-20], options=bgui.BGUI_TOP|bgui.BGUI_FILLX)
		self.b1.on_left_release = self.runTut1
		self.b1.lighter = True

		self.b2 = bgui.FrameButton(canvas, 'b2', centerText=False, text="\t2. Object Manipulation", sub_theme='listEntry', size=[150,20], offset=[0,-45], options=bgui.BGUI_TOP|bgui.BGUI_FILLX)
		self.b2.on_left_release = self.runTut2
		self.b2.lighter = True

		self.b3 = bgui.FrameButton(canvas, 'b3', centerText=False, text="\t3. Timeline", sub_theme='listEntry', size=[150,20], offset=[0,-70], options=bgui.BGUI_TOP|bgui.BGUI_FILLX)
		self.b3.on_left_release = self.runTut3
		self.b3.lighter = True

		self.b4 = bgui.FrameButton(canvas, 'b4', centerText=False, text="\t4. Protein Appearance", sub_theme='listEntry', size=[150,20], offset=[0,-95], options=bgui.BGUI_TOP|bgui.BGUI_FILLX)
		self.b4.on_left_release = self.runTut4
		self.b4.lighter = True

		self.b5 = bgui.FrameButton(canvas, 'b5', centerText=False, text="\t5. Blobber Tool", sub_theme='listEntry', size=[150,20], offset=[0,-120], options=bgui.BGUI_TOP|bgui.BGUI_FILLX)
		self.b5.on_left_release = self.runTut5
		self.b5.lighter = True

		self.b6 = bgui.FrameButton(canvas, 'b6', centerText=False, text="\t6. Protein Editor", sub_theme='listEntry', size=[150,20], offset=[0,-145], options=bgui.BGUI_TOP|bgui.BGUI_FILLX)
		self.b6.on_left_release = self.runTut6
		self.b6.lighter = True

		self.b7 = bgui.FrameButton(canvas, 'b7', centerText=False, text="\t7. Creating a Movie", sub_theme='listEntry', size=[150,20], offset=[0,-170], options=bgui.BGUI_TOP|bgui.BGUI_FILLX)
		self.b7.on_left_release = self.runTut7
		self.b7.lighter = True
		
		self.b9 = bgui.FrameButton(canvas, 'b9', centerText=True, text="Help", sub_theme='listEntry', size=[150,20], offset=[0,-250], options=bgui.BGUI_TOP|bgui.BGUI_FILLX)
		self.b9.on_left_release = self.showHelp
		self.b9.lighter = True


	def runTut1(self, widget):
		logic.tutorial.state = logic.tutorial.quickStart0

	def runTut2(self, widget):
		logic.tutorial.state = logic.tutorial.manipulation0

	def runTut3(self, widget):
		logic.tutorial.state = logic.tutorial.timeline0

	def runTut4(self, widget):
		logic.tutorial.state = logic.tutorial.appearance0

	def runTut5(self, widget):
		logic.tutorial.state = logic.tutorial.blobber0

	def runTut6(self, widget):
		logic.tutorial.state = logic.tutorial.editor0

	def runTut7(self, widget):
		logic.tutorial.state = logic.tutorial.movie0

	def showHelp(self, widget):
		logic.gui.viewport.showHelp()


def init(canvas):
	return Helper(canvas)

