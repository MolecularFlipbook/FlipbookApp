# import gamengine modules
import bge
from bge import logic
from bge import events
from bge import render

from bgl import *

# native python modules
import os, time, math, pprint, imp

# import mvb's own modules
from . import bgui
from . import timelinePane
from . import helpPane
from . import optionsPane
from . import loggerPane
from . import outlinerPane
from . import viewport
from . import importDialog
from . import publishDialog
from . import gate
from .settings import *
from .helpers import *


outlinerX = 170
outlinerY = 500

helpX = 170
helpY = 300

optionsX = 800
optionsY = 150

childIconsX = 75
childIconsY = 35
margin = 5

loggerX = 200
loggerY = 100

frameIconsX = 170
frameIconsY = 500

timelineY = 150

#*****************************************************
# Class: Layout of UI in GE
#*****************************************************
class MyUI(bgui.System):

	def __init__(self):
		# Initialize the system
		bgui.System.__init__(self, themeRoot())

		# resolution gate
		logic.gate = gate.init(self)

		# Outliner Container:
		self.outlinerPane = bgui.Frame(self,'outlinerPane',size=[outlinerX,outlinerY],offset=[0,0,0,timelineY+helpY], sub_theme='light', options=bgui.BGUI_RIGHT|bgui.BGUI_TOP|bgui.BGUI_FILLY)
		self.outlinerLabel = bgui.Label(self.outlinerPane, 'outlinerLabel', text="Outliner", offset = [0,-10], options=bgui.BGUI_CENTERX|bgui.BGUI_TOP)
		self.selectionCounter = bgui.Label(self.outlinerPane, "selectionCounter", text="", sub_theme="selectionCounter", pos=[0,0], offset=[0,-30], options=bgui.BGUI_CENTERX|bgui.BGUI_TOP|bgui.BGUI_NO_FOCUS)
		self.outlinerScroll = bgui.Scroll(self.outlinerPane, 'outlinerScroll', offset=[0,20,0,20], actual = [1, 1], options=bgui.BGUI_CENTERX|bgui.BGUI_FILLED)
		self.outlinerHandle = bgui.FrameButton(self.outlinerPane, 'outlinerHandle', size=[10,1], stipple=True, options=bgui.BGUI_LEFT|bgui.BGUI_FILLY)
		self.outlinerHandle.on_left_release = self.onClick
		logic.outliner = outlinerPane.init(self.outlinerScroll)

		# Quick Help Container
		self.helpPane = bgui.Frame(self,'helpPane', size=[helpX,helpY], offset=[0, timelineY],  sub_theme='light', options=bgui.BGUI_RIGHT|bgui.BGUI_BOTTOM)
		self.helpLabel = bgui.Label(self.helpPane, 'helpLabel', text="Help", offset = [0,-10], options=bgui.BGUI_CENTERX|bgui.BGUI_TOP)
		self.helpScroll = bgui.Scroll(self.helpPane, 'helpScroll', pos=[10,0], size=[helpX-10, helpY-20], actual=[1,1])

		self.helpHandle = bgui.FrameButton(self.helpPane, 'helpHandle', size=[10,1], stipple=True, options=bgui.BGUI_LEFT|bgui.BGUI_FILLY)
		self.helpHandle.on_left_release = self.onClick
		logic.helper = helpPane.init(self.helpScroll)

		# Options Panel Container
		self.optionsPane = bgui.Frame(self,'optionsPane', size=[optionsX,optionsY], offset=[10,-10], radius=6, sub_theme="op", options=bgui.BGUI_TOP|bgui.BGUI_LEFT)
		logic.options = optionsPane.init(self.optionsPane, self)

		# Logger Container
		self.loggerPane = bgui.Frame(self,'loggerPane', size=[loggerX,loggerY],offset=[10+optionsX+10, -10], sub_theme="invisible", options=bgui.BGUI_LEFT|bgui.BGUI_TOP|bgui.BGUI_NO_FOCUS)
		logic.logger = loggerPane.init(self.loggerPane)

		# setup timeline
		self.timeline = bgui.Frame(self, 'timeline', size=[1,timelineY], sub_theme='light', options = bgui.BGUI_FILLX|bgui.BGUI_BOTTOM|bgui.BGUI_LEFT)
		self.timelineScroll = bgui.Scroll(self.timeline, 'timelineScroll', pos=[0,0], size=[0,130], actual=[1,1], options=bgui.BGUI_FILLX)
		logic.timeline = timelinePane.init(self.timeline, self.timelineScroll, self)

		# Button Icons Container: Parent Frame is not normalized; children of Frame are relative/normalized to parent
		self.groupicons = bgui.Frame(self, 'groupicons', size=[frameIconsX, frameIconsY], offset=[10, -10-optionsY-10-margin], sub_theme='invisible', options=bgui.BGUI_TOP|bgui.BGUI_LEFT|bgui.BGUI_NO_FOCUS)

		# 1st Group: file management
		self.importBtn = bgui.FrameButton(self.groupicons, 'importBtn', text='Import PDB', size=[childIconsX, childIconsY], pos=[0,460], sub_theme="icons", radius = 3)
		self.importBtn.on_left_release = self.onClick
		self.importBtn.tooltip = "Import shape from PDB files"
		self.importBtn.lighter = True

		self.blobberBtn = bgui.FrameButton(self.groupicons, 'blobberBtn', text='Blobber', size=[childIconsX, childIconsY], pos=[80,460], sub_theme="icons", radius = 3)
		self.blobberBtn.on_left_release = self.onClick
		self.blobberBtn.tooltip = "Create primitive shapes"
		self.blobberBtn.lighter = True

		self.loadBtn = bgui.FrameButton(self.groupicons, 'loadBtn', text='Load Scene', size=[childIconsX, childIconsY], pos=[0,420], sub_theme="icons", radius = 3)
		self.loadBtn.on_left_release = self.onClick
		self.loadBtn.tooltip = "Load scene from file, opens a file-picker window"
		self.loadBtn.lighter = True

		# self.saveBtn = bgui.FrameButton(self.groupicons, 'saveBtn', text='Save Scene', size=[childIconsX, childIconsY], pos=[80,420], sub_theme="icons", radius = 3)
		# self.saveBtn.on_left_release = self.onClick
		# self.saveBtn.tooltip = "Save scene to file, opens a file-picker window"
		# self.saveBtn.lighter = True

		# 2nd group
		self.displayBtn = bgui.FrameButton(self.groupicons, 'displayBtn', text='Representation', size=[childIconsX, childIconsY], pos=[0,370-margin], sub_theme="icons", radius = 3)
		self.displayBtn.on_left_release = self.onClick
		self.displayBtn.tooltip = "Set representation modes"
		self.displayBtn.lighter = True

		self.shadingBtn = bgui.FrameButton(self.groupicons, 'shadingBtn', text='Shading', size=[childIconsX, childIconsY], pos=[80,370-margin], sub_theme="icons", radius = 3)
		self.shadingBtn.on_left_release = self.onClick
		self.shadingBtn.tooltip = "Set Color and Shading"
		self.shadingBtn.lighter = True

		self.cameraBtn = bgui.FrameButton(self.groupicons, 'cameraBtn', text='Display', size=[childIconsX, childIconsY], pos=[0,330-margin], sub_theme="icons", radius = 3)
		self.cameraBtn.on_left_release = self.onClick
		self.cameraBtn.tooltip = "Setup the virtual camera"
		self.cameraBtn.lighter = True

		self.editorBtn = bgui.FrameButton(self.groupicons, 'editorBtn', text='Editor', size=[childIconsX, childIconsY], pos=[80,330-margin], sub_theme="icons", radius = 3)
		self.editorBtn.on_left_release = self.onClick
		self.editorBtn.tooltip = "Protein Editor"
		self.editorBtn.lighter = True

		self.linkerBtn = bgui.FrameButton(self.groupicons, 'linkerBtn', text='Linker', size=[childIconsX, childIconsY], pos=[0,290-margin], sub_theme="icons", radius = 3)
		self.linkerBtn.on_left_release = self.onClick
		self.linkerBtn.tooltip = "Flexible Linker Editor"
		self.linkerBtn.lighter = True

		# self.environBtn = bgui.FrameButton(self.groupicons, 'environBtn', text='...', size=[childIconsX, childIconsY], pos=[80,290-margin], sub_theme="icons", radius = 3)
		# self.environBtn.on_left_release = self.onClick
		# self.environBtn.tooltip = "Environment"
		# self.environBtn.lighter = True

		# 3rd Group: render, format movie
		self.renderBtn = bgui.FrameButton(self.groupicons, 'renderBtn', text='Export', size=[childIconsX, childIconsY], pos=[0, 240-margin*2], sub_theme="icons", radius = 3)
		self.renderBtn.on_left_release = self.onClick
		self.renderBtn.tooltip = "Finalize Project"
		self.renderBtn.lighter = True

		self.publishBtn = bgui.FrameButton(self.groupicons, 'publishBtn', text='Save/Share', size=[childIconsX, childIconsY], pos=[80, 240-margin*2], sub_theme="icons", radius = 3)
		self.publishBtn.on_left_release = self.onClick
		self.publishBtn.tooltip = "Publish"
		self.publishBtn.lighter = True

		self.renderProgress = bgui.ProgressBar(self, 'renderProgress', percent=0.0, size=[1,10], pos=[0,0], options=bgui.BGUI_TOP|bgui.BGUI_FILLX)
		self.renderProgress.visible = False

		# debug area
		if useDebug:
			self.debuglabel = bgui.Label(self, 'debuglabel', text='Development Mode', offset = [0,0], sub_theme = 'blackLabelSmall', options=bgui.BGUI_CENTERX|bgui.BGUI_TOP|bgui.BGUI_NO_FOCUS)
			self.debug = bgui.TextBlock(self, 'debug', size=[200,500], offset=[-100,-170], sub_theme='blackBlockTiny', options=bgui.BGUI_TOP|bgui.BGUI_RIGHT|bgui.BGUI_NO_FOCUS)
			self.bgProcessCounter = bgui.Label(self, 'bgProcessCounter', offset=[-5,5], sub_theme='whiteLabelSmall', options=bgui.BGUI_BOTTOM|bgui.BGUI_RIGHT|bgui.BGUI_NO_FOCUS)

		# 3d viewport
		self.viewport = viewport.init(self)

		# setup secondary level UIs
		self.importDialog = importDialog.init(self)
		self.publishDialog = publishDialog.init(self)
		# self.feedbackDialog = feedbackDialog.init(self)

		# hide stuff on startup:
		self.showSimpleUI()

		# setup multitouch debug draws
		if useMultitouch:
			self.initMultitouch()

		# test video
		#self.vid = bgui.Video(self, 'vid', None, size=[0.4,0.2], pos=[0,0], options = bgui.BGUI_NORMALIZED|bgui.BGUI_CENTERED)
		#self.vid.z_index = 99

		# Create a keymap for keyboard input
		self.keymap = {getattr(bge.events, val): getattr(bgui, val) for val in dir(bge.events) if val.endswith('KEY') or val.startswith('PAD')}



	def showSimpleUI(self):
		# clean UI
		self.outlinerVisible(False)
		self.helpVisible(False)
		logic.options.close()

		# hide out of context UI
		iconList = [
				# self.saveBtn,
				self.displayBtn,
				self.cameraBtn,
				self.shadingBtn,
				self.editorBtn,
				self.linkerBtn,
				# self.environBtn,
				self.renderBtn,
				self.publishBtn]
		for icon in iconList:
			icon.visible = False


	def showFullUI(self):
		# reveal more UI
		iconList = [
					# self.saveBtn,
					self.loadBtn,
					self.displayBtn,
					self.cameraBtn,
					self.shadingBtn,
					self.editorBtn,
					self.linkerBtn,
					# self.environBtn,
					self.renderBtn,
					self.publishBtn]
		for icon in iconList:
			icon.visible = True

		logic.gui.outlinerVisible(True)
		logic.gui.helpVisible(True)


	def showToolTip(self, widget):
		"""draws ToolTip as a mouse on_enter event """
		if useTooltip:
			length = int(len(widget.tooltip)*4.1)
			size = [length+6, 20]
			try:
				posxy = self.system.mousePos
			except AttributeError:
				pass
			else:
				newPos = [posxy[0], int(posxy[1] - 40)]
				if newPos[1]<0:
					newPos[1] = 0
				self.tooltipWidget = bgui.ToolTip(self, 'tooltipWidget', text=widget.tooltip, size=size, pos=newPos, radius=5)


	def hideToolTip(self, widget):
		"""hides tooltip"""
		if useTooltip:
			if hasattr(self, "tooltipWidget"):
				guiKill(self.tooltipWidget)



	def showMenu(self, name="", items=[], pos=[0, 0], caller=None, callback=None):
		"""Return a pop-up menu widget at the mouse position"""
		# compute mouse position that is normalized [default: in range] to not normalized (pixels)
		pos = [int(pos[0] * self.size[0]), self.size[1] - int(pos[1] * self.size[1])]
		return bgui.Menu(self, name=name, items=items, pos=pos, caller=caller, clickHandler=callback, hideHandler=self.hideMenu)


	def hideMenu(self, widget):
		"""Removes the pop-up menu widget"""
		widget.position = [-200,-200]


	def _runAndClose(self, widget):
		if callable(widget.func):
			widget.func()				# run the on-click function
		guiKill(widget.parent)			# close


	def showModalMessage(self, subject="", message="", action=None):
		"""creates an 'Okay' modal dialog box"""
		panel = bgui.Frame(self, 'modalMessage', size=[350,150], radius=6, pos=[int(self.size[0]/2-350/2), int(self.size[1]/2.0+70)],  options=bgui.BGUI_MOVABLE)
		subject = bgui.Label(panel, 'subject', text=subject, pos=[10,125], sub_theme='whiteLabel')
		panelwhite = bgui.Frame(panel, 'panelwhite', size=[350,110], radius=0, pos=[0,0], border=0, sub_theme="light", options=bgui.BGUI_NO_FOCUS)
		text = bgui.TextBlock(panel, 'text', text=message, size=[100,70], pos=[10,40], sub_theme='blackBlock', options=bgui.BGUI_FILLX)
		okay = bgui.FrameButton(panel, "ok",  text="OK", radius = 5, size=[80,32], pos=[0, 10], options=bgui.BGUI_CENTERX)

		okay.on_left_release = self._runAndClose
		okay.func = action


	def showModalConfirm(self, subject="", message="", verb="Go", cancelVerb="Cancel", action=None, cancelAction=None):
		"""creates a 'Cancel/Affirm' modal dialog box"""
		panel = bgui.Frame(self, 'modalMessage', size=[350,150], radius=6, pos=[int(self.size[0]/2-350/2), int(self.size[1]/2.0+70)],  options=bgui.BGUI_MOVABLE)
		subject = bgui.Label(panel, 'subject', text=subject, pos=[10,125], sub_theme='whiteLabel')
		panelwhite = bgui.Frame(panel, 'panelwhite', size=[350,110], radius=0, pos=[0,0], border=0, sub_theme="light", options=bgui.BGUI_NO_FOCUS)
		text = bgui.TextBlock(panel, 'text', text=message, size=[100,70], pos=[10,40], sub_theme='blackBlock', options=bgui.BGUI_FILLX)
		okay = bgui.FrameButton(panel, "ok",  text=verb, radius = 5, size=[80,32], pos=[70, 10])
		cancel = bgui.FrameButton(panel, "cancel",  text=cancelVerb, radius = 5, size=[80,32], pos=[180, 10])

		okay.on_left_release = self._runAndClose
		okay.func = action

		cancel.on_left_release = self._runAndClose
		cancel.func = cancelAction


	def setButtonHighlight(self, widget):
		for name, w in self.groupicons.children.items():
			w.color = [0.3, 0.3, 0.3, 0.7]
		if widget:
			widget.color = [0.2, 0.3, 0.2, 0.7]


	def onClick(self, widget):
		"""Generic handler for dealing with button clicks"""
		if widget.name == "importBtn":
			if useDebug:
				imp.reload(importDialog)
				self.importDialog = importDialog.init(self)
			self.importDialog.visible = not self.importDialog.visible
		elif widget.name == "blobberBtn":
			logic.options.view = 'CREATE'
			self.setButtonHighlight(widget)
		elif widget.name == "displayBtn":
			logic.options.view = 'REPRESENTATION'
			self.setButtonHighlight(widget)
		elif widget.name == "shadingBtn":
			logic.options.view = 'SHADING'
			self.setButtonHighlight(widget)
		elif widget.name == "cameraBtn":
			logic.options.view = 'CAMERA'
			self.setButtonHighlight(widget)
		elif widget.name == "editorBtn":
			logic.options.view = 'EDITOR'
			self.setButtonHighlight(widget)
		elif widget.name == "linkerBtn":
			logic.options.view = 'LINKER'
			self.setButtonHighlight(widget)
		elif widget.name == "worldBtn":
			logic.options.view = 'WORLD'
			self.setButtonHighlight(widget)
		elif widget.name == "renderBtn":
			logic.options.view = 'FINALIZE'
			self.setButtonHighlight(widget)
		elif widget.name == "publishBtn":
			if useDebug:
				imp.reload(publishDialog)
				self.publishDialog = publishDialog.init(self)
			self.publishDialog.visible = not self.publishDialog.visible
		elif widget.name == "loadBtn":
			from . import fileInterface
			fileInterface.loadBrowse()
		elif widget.name == "saveBtn":
			from . import fileInterface
			fileInterface.saveBrowse()
		elif widget.name == "outlinerHandle":
			if self.outlinerIsVisible():
				self.outlinerVisible(False)
			else:
				self.outlinerVisible(True)

		elif widget.name == "helpHandle":
			if self.helpIsVisible():
				self.helpVisible(False)
			else:
				self.helpVisible(True)



	def outlinerIsVisible(self):
		return (self.outlinerPane._offsetTarget == [0, 0, 0, timelineY+helpY])

	def outlinerVisible(self, visible):
		if visible:
			self.outlinerPane._offsetTarget = [0, 0, 0, timelineY+helpY]
		else:
			self.outlinerPane._offsetTarget = [outlinerX-10, 0, 0, timelineY+helpY]


	def helpIsVisible(self):
		return (self.helpPane._offsetTarget == [0,timelineY])

	def helpVisible(self, visible):
		if visible:
			self.helpPane._offsetTarget = [0,timelineY]
		else:
			self.helpPane._offsetTarget = [helpX-10, timelineY]


	def gridVisible(self, visible):
		logic.scene.objects['Grid'].visible = visible


	def initMultitouch(self):
		"""docstring for initMultitouch"""
		sx = 0.02
		sy = 0.02
		self.MTpoint1 = bgui.FrameButton(self, 'mtpoint1', text="1", size=[sx,sy], pos=[.0, -0.1], sub_theme='mt')
		self.MTpoint2 = bgui.FrameButton(self, 'mtpoint2', text="2", size=[sx,sy], pos=[.0, -0.1], sub_theme='mt')
		self.MTpoint3 = bgui.FrameButton(self, 'mtpoint3', text="3", size=[sx,sy], pos=[.0, -0.1], sub_theme='mt')
		self.MTpoint4 = bgui.FrameButton(self, 'mtpoint4', text="4", size=[sx,sy], pos=[.0, -0.1], sub_theme='mt')
		self.MTpoint5 = bgui.FrameButton(self, 'mtpoint5', text="5", size=[sx,sy], pos=[.0, -0.1], sub_theme='mt')
		self.MTpoint6 = bgui.FrameButton(self, 'mtpoint6', text="6", size=[sx,sy], pos=[.0, -0.1], sub_theme='mt')
		self.MTpoint7 = bgui.FrameButton(self, 'mtpoint7', text="7", size=[sx,sy], pos=[.0, -0.1], sub_theme='mt')
		self.MTpoint8 = bgui.FrameButton(self, 'mtpoint8', text="8", size=[sx,sy], pos=[.0, -0.1], sub_theme='mt')
		self.MTpoint9 = bgui.FrameButton(self, 'mtpoint9', text="9", size=[sx,sy], pos=[.0, -0.1], sub_theme='mt')
		self.MTpoint10 = bgui.FrameButton(self, 'mtpoint10', text="0", size=[sx,sy], pos=[.0, -0.1], sub_theme='mt')


	def loop(self, scene):


		# update debug text
		if useDebug:
			try:
				t = ""
				for key, item in logic.watch.items():
					t += "%s: %s\n---------\n"%(key, item)
				self.debug.text = t

				# show number of BG process
				num = len(logic.registeredFunctions)
				if num <=0:
					self.bgProcessCounter.text = "Clean"
				elif num == 1:
					self.bgProcessCounter.text = "1 background process running"
				else:
					self.bgProcessCounter.text = str(num) + " background processes running"
			except:
				pass


			# show fps
			self.debug.text += '\n' + str(int(logic.getAverageFrameRate())) + ' fps'


		# Handle the mouse
		# hack needed since inactive window does not update mouse position
		if logic.mouseExitHack:
			pos = [0,0]				# set position to a harmless location
			# disable hack once mouse events are properly capturing again
			if logic.mousePosDelta[0] != 0 or logic.mousePosDelta[1] != 0:
				logic.mouseExitHack = False
		else:
			pos = list(logic.mouse.position)

		pos[0] *= render.getWindowWidth()
		pos[1] = render.getWindowHeight() * (1.0-pos[1])

		mouse_state = bgui.BGUI_MOUSE_NONE
		mouse_events = logic.mouse.events

		if mouse_events[events.LEFTMOUSE] == logic.KX_INPUT_JUST_ACTIVATED:
			mouse_state = bgui.BGUI_MOUSE_LEFT_CLICK
		elif mouse_events[events.LEFTMOUSE] == logic.KX_INPUT_JUST_RELEASED or logic.tap:
			mouse_state = bgui.BGUI_MOUSE_LEFT_RELEASE
		elif mouse_events[events.LEFTMOUSE] == logic.KX_INPUT_ACTIVE:
			mouse_state = bgui.BGUI_MOUSE_LEFT_ACTIVE
		elif mouse_events[events.RIGHTMOUSE] == logic.KX_INPUT_JUST_ACTIVATED:
			mouse_state = bgui.BGUI_MOUSE_RIGHT_CLICK
		elif mouse_events[events.RIGHTMOUSE] == logic.KX_INPUT_JUST_RELEASED:
			mouse_state = bgui.BGUI_MOUSE_RIGHT_RELEASE
		elif mouse_events[events.RIGHTMOUSE] == logic.KX_INPUT_ACTIVE:
			mouse_state = bgui.BGUI_MOUSE_RIGHT_ACTIVE
		elif mouse_events[events.WHEELUPMOUSE] == logic.KX_INPUT_JUST_ACTIVATED or mouse_events[events.WHEELUPMOUSE] == logic.KX_INPUT_ACTIVE or logic.mouseUp:
			mouse_state = bgui.BGUI_MOUSE_WHEEL_UP
		elif mouse_events[events.WHEELDOWNMOUSE] == logic.KX_INPUT_JUST_ACTIVATED or mouse_events[events.WHEELDOWNMOUSE] == logic.KX_INPUT_ACTIVE or logic.mouseDown:
			mouse_state = bgui.BGUI_MOUSE_WHEEL_DOWN

		logic.mouseUp = False
		logic.mouseDown = False
		logic.tap = False

		try:
			self.update_mouse(pos, mouse_state)
		except KeyError:
			pass

		self.mousePos = pos[:]

		# Handle the keyboard
		key_events = logic.keyboard.events

		is_shifted = 0 < key_events[events.LEFTSHIFTKEY] < 3 or \
					0 < key_events[events.RIGHTSHIFTKEY] < 3

		is_ctrled = 0 < key_events[events.LEFTCTRLKEY] < 3 or \
					0 < key_events[events.RIGHTCTRLKEY] < 3

		is_alted = 0 < key_events[events.LEFTALTKEY] < 3 or \
					0 < key_events[events.RIGHTALTKEY] < 3


		if 'mac' in releaseOS:
			is_commanded = 0 < key_events[events.OSKEY] < 3
		elif 'win' in releaseOS:
			is_commanded = False  # do not process WIndows OS keys (start)
		else:
			is_commanded = False  # other OS

		self.isCtrled = is_ctrled
		self.isAlted = is_alted
		self.isShifted = is_shifted
		self.isCommanded = is_commanded


		# to bgui, Command and Ctrl is one key
		for key, state in logic.keyboard.events.items():
			if state == logic.KX_INPUT_JUST_ACTIVATED:
				self.update_keyboard(self.keymap[key], is_shifted, is_ctrled or is_commanded)
				logic.keyCounter = -10 		# key repeat delay

			elif state == logic.KX_INPUT_ACTIVE:
				if logic.keyCounter % 2 == 0 and logic.keyCounter > 0:
					self.update_keyboard(self.keymap[key], is_shifted, is_ctrled or is_commanded)
				logic.keyCounter += 1 		# key repeat rate

		# Now setup the scene callback so we can draw
		scene.post_draw = [self.render]

		if useDebug and False:
			imp.reload(viewport)
			self.viewport = viewport.init(self)


