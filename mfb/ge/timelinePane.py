# import blender gamengine modules
from bge import logic
from bge import events
from bge import render

from . import bgui
from .settings import *
from .helpers import *
import time
import pdb
import colorsys
import random


class Timeline():
	def __init__(self, timelineWidget, scrollerWidget, sys):
		'''sets-up timeline GUI'''

		self.root = timelineWidget				# alias to main timeline widget
		self.scroller = scrollerWidget			# alias to scroller widget
		self.system = sys 						# alias to gui system

		self.slides = []						# keeps track of slides
		self.connectors = []					# keeps track of connectors
		self.ticks = []							# keeps track of ticks

		self.initUI()							# init common timeline widgets

		self.clickedXY = None
		self.movingSlide = None


	def initUI(self):
		# draw decorator to hold play/pause button, progress bar, playback toggle, and total time of animation
		self.timeLinePanel = bgui.Frame(self.root, 'timeLinePanel', size=[0, 20], sub_theme='op', options=bgui.BGUI_TOP|bgui.BGUI_FILLX)
		# draw progress bar UI
		self.timeLineProgress = bgui.ProgressBar(self.root, 'timeLineProgress', size = [0,16], offset=[90,-2,210,0], options=bgui.BGUI_NO_FOCUS|bgui.BGUI_TOP|bgui.BGUI_LEFT|bgui.BGUI_FILLX)
		# draw Play/Pause button
		self.timeLinePlayBtn = bgui.ImageButton(self.root,'timeLinePlayBtn',size=[64,64],offset=[0,23],sub_theme='timelineProxy',options=bgui.BGUI_TOP|bgui.BGUI_LEFT)
		self.timeLinePlayBtn.on_left_release = self.playToggle
		#draw playback loop toggle button
		self.timeLineLoopBtn = bgui.ImageButton(self.root,'timeLineLoopBtn',size=[40,16],offset=[-120,-4],sub_theme='timelineLoop',options=bgui.BGUI_TOP|bgui.BGUI_RIGHT)
		self.timeLineLoopBtn.on_left_release = self.loopToggle
		self.timeLineLoopBtn.tooltip = 'Toggle looping of animation'
		#display total time of animation
		self.timeLabel = bgui.Label(self.root, 'timeLabel', text='', sub_theme='whiteLabelBold', offset=[-70,-6], options=bgui.BGUI_TOP|bgui.BGUI_RIGHT)
		self.timeLabel.tooltip = 'Animation duration'
		# draw frame widget containter that will hold train ##
		self.timeLineTrainTrack = bgui.Frame(self.system, 'timeLineTrainTrack', size=[0, 20], sub_theme="invisible", options=bgui.BGUI_NO_FOCUS|bgui.BGUI_BOTTOM|bgui.BGUI_LEFT|bgui.BGUI_FILLX)
		self.timeLineTrainTrack.extraPadding = [50,50,25,25]
		# draw Image widget for train which will display time format: MM:SS.S
		self.timeLineTrain = bgui.ImageButton(self.timeLineTrainTrack, 'timeLineTrain',sub_theme="timelineTrain", size=[64, 32],options=bgui.BGUI_CACHE)
		self.timeLineTrain.on_left_click = self.trainMove
		self.timeLineTrain.on_left_release = self.trainMoved
		# compute trainTrack widget's offset relative to half the size of train at beginning and end of track
		self.timeLineTrain.position = [0,-5]
		trainCenter = int(self.timeLineTrain.size[0]/2)
		self.timeLineTrainTrack.offset = [90-trainCenter,130,210+trainCenter,0]
		# draw label widget that displays the current time of the animation in the train widget
		self.timeLineTrainLabel = bgui.Label(self.timeLineTrain, 'timeLineTrainLabel', text='', sub_theme='blackLabel', offset=[-12,-10], options=bgui.BGUI_TOP|bgui.BGUI_RIGHT|bgui.BGUI_NO_FOCUS)


	def playToggle(self,  widget=None):
		"""invoked by the play button on timeline, starts from or pauses animation at active slide"""
		logic.mvb.playing = not logic.mvb.playing


	def loopToggle(self,  widget=None):
		"""invoked by the playback loop button on timeline, by default playback loop mode is enabled."""
		logic.mvb.looping = not logic.mvb.looping


	def trainMove(self, widget):
		"""registers the mouse handler"""
		if self.trainMoving in logic.registeredFunctions:
			logic.registeredFunctions.remove(self.trainMoving)
		else:
			logic.registeredFunctions.append(self.trainMoving)


	def trainMoving(self):
		""" handles the draggable timline label widget"""
		if logic.gui.mouse_state == bgui.BGUI_MOUSE_LEFT_RELEASE:
			self.trainMoved(None)
		else:
			ratio = (logic.gui.mousePos[0] - self.timeLineTrainTrack.position[0]) / (self.timeLineTrainTrack.size[0])
			logic.mvb.time = ratio * logic.mvb.getTotalTime()
			logic.mvb._scrubbing = True
			logic.mouseLock = 3
			return True


	def trainMoved(self, widget):
		"""delete the mouse handler"""
		try:
			logic.mvb._scrubbing = False
			logic.mvb.snap()
			logic.registeredFunctions.remove(self.trainMoving)
			logic.mouseLock = 0
		except:
			pass


	# ----------------- slide related functions -----------------

	def slideMove(self, widget=None):
		self.movingSlide = widget
		logic.registeredFunctions.append(self.slideMoving)

	def slideMoving(self):
		if logic.gui.mouse_state == bgui.BGUI_MOUSE_LEFT_RELEASE:
			# end drag and drop
			self.slideMoved()
			return False
		else:
			# set slide visual position
			pos = logic.gui.mousePos[:]
			pos[0] -= 50
			pos[1] -= 25
			pos[1] = self.movingSlide.position[1]
			self.movingSlide.position = pos

			# test for connectorWidget
			padding = 50
			for connector in self.connectors:

				# if mouse if over activation area (connector)
				if (connector.gl_position[0][0] <= logic.gui.mousePos[0] <= connector.gl_position[1][0]) and \
				(connector.gl_position[0][1]-padding <= logic.gui.mousePos[1] <= connector.gl_position[2][1]+padding):
							
					# get target slide form connector widget name
					name = connector.name[:-9]

					try:
						slideWidget = self.scroller.children[name]
					except:
						logic.logger.new("Error: Slide not found")
						self.slideMoved()
						return False

					a, indexA = self.getMVBSlide(self.movingSlide)		# the slide being dragged
					b, indexB = self.getMVBSlide(slideWidget)			# the slide being displaced
			
					if a and b:
						if a != b:
							logic.mvb.moveSlide(indexA, indexB)
							self.slideMoved()
							return False
					else:
						logic.logger.new('Error: Slide not found')
						self.slideMoved()
						return False

			return True

	def slideMoved(self, widget=None):
		# settle all slides to their supposed position
		self.viewUpdate()

	def slideAdd(self, widget=None, silent=False):
		'''	create the slide in the model and becomes active slide'''
		if not silent:
			logic.undo.append('Slide Copied', props='TIMELINE')

		if widget:
			# use widget as parent slide
			slide, index = self.getMVBSlide(widget.parent)
			index += 1
		else:
			# use active slide
			index = logic.mvb.activeSlide + 1

		newSlideIndex = logic.mvb.addSlide(index, silent)
		if not silent:
			self.viewUpdate()
			logic.options.updateView()


	def slideDelete(self, widget=None):
		''' delete a slide'''
		logic.undo.append('Slide Deleted', props='TIMELINE')

		selectedSlide = None
		if widget:
			slide, i = self.getMVBSlide(widget.parent)
		else:
			i = logic.mvb.activeSlide
		logic.mvb.deleteSlide(i)
		self.viewUpdate()
		logic.options.updateView()



	def viewUpdate(self, animate = True):
		'''Update the interface'''
		# check for newly added slide
		for slide in logic.mvb.slides:
			if not slide.ui:
				self.widgetAdd(slide)

		# check for newly deleted slide
		for slideWidget in self.slides:
			if slideWidget not in [slide.ui for slide in logic.mvb.slides]:
				self.widgetDelete(slideWidget)

		# at this point, we have the proper number of slides that match the model
		# placement

		# fit scroller
		self.scroller.fitX(len(logic.mvb.slides)*200)

		# animate slides
		xCoord = 20 	# initial padding
		for i, slide in enumerate(logic.mvb.slides):
			w = slide.ui
			if animate:
				w.move([xCoord, 15], 200)
			else:
				w.move([xCoord, 15], 0)
			w.text = str(i+1)
			xCoord += 200


		# interval connector

		# kill existing
		for c in self.connectors:
			c.kill()
		self.connectors = []

		# regenerate all connectors
		xCoord = 20 	# initial padding
		for i, slide in enumerate(logic.mvb.slides):
			try:
				interval = logic.mvb.slides[i+1].time - slide.time
			except:
				interval = None
			else:
				name = str(slide.id)
				intervalText = str(round(interval,1))
				connectorWidget = bgui.ImageButton(self.scroller, name+"connector", size=[40,25], pos=[xCoord+160, 46], sub_theme='timelineTrain', options=bgui.BGUI_CACHE)
				connectorWidget.image.color = [1,1,1,0.7]
				interval = bgui.TextInput(connectorWidget, "interval", text=intervalText, size=[0,0], pos=[0,2], centerText=True, sub_theme='slideConnectorNum', options=bgui.BGUI_FILLED)
				interval.tooltip = "Duration in seconds between slides"
				interval.on_mouse_wheel_up = self.onMouseWheelUp
				interval.on_mouse_wheel_down = self.onMouseWheelDown
				interval.on_edit = self.setValue
				interval.on_enter_key = self.setValueFinal
				xCoord += 200
				self.connectors.append(connectorWidget)
				slide.connectorUI = interval

		self.tickMarkUpdate()

		# highlight
		self.slideHighlight(logic.mvb.activeSlide)


	def widgetAdd(self, slide):
		name = str(slide.id) 	# name of main slide widget is the slide id

		# get prev slide
		prevPosX = 0
		for i, s in enumerate(logic.mvb.slides):
			if slide == s:
				prevSlide = logic.mvb.slides[i-1]
				try:
					prevPosX = prevSlide.ui.position[0]
				except:
					pass

		slideWidget = bgui.FrameButton(self.scroller, name, text='', size=[160, 90], pos=[prevPosX+100,100], sub_theme='slide', radius=6)
		slideWidget.lighter = True
		slideWidget.on_left_click = self.slideLeftClick
		slideWidget.on_left_active = self.slideLeftClickActive
		slideWidget.on_left_release = self.slideLeftRelease
		slideWidget.on_mouse_exit = self.slideLeftRelease

		# progress
		bgui.Frame(slideWidget, 'progress', sub_theme='slideProgress', size=[1,0], pos=[0,0], options=bgui.BGUI_NO_FOCUS|bgui.BGUI_NORMALIZED)

		# capture bg image
		...


		# bg image
		useImage = False
		if useImage:
			slideWidgetBG = bgui.Image(slideWidget, "bg", img = '', offset=[5,5,5,5], options=bgui.BGUI_NO_FOCUS|bgui.BGUI_LEFT|bgui.BGUI_BOTTOM|bgui.BGUI_FILLED)
			col = list(colorsys.hsv_to_rgb(random.random(), 1.0, 1.0)) # randomize color
			col.append(0.1)
			#col = [1,1,1,0.5]
			slideWidgetBG.color = col

		# close button
		closeWidget = bgui.ImageButton(slideWidget, 'close', size=[32,32], offset=[1,1], sub_theme='slideClose', options=bgui.BGUI_CACHE|bgui.BGUI_TOP|bgui.BGUI_RIGHT)
		closeWidget.on_left_click = self.slideDelete
		closeWidget.tooltip = "Delete this slide"

		# dup button
		dupWidget = bgui.ImageButton(slideWidget, 'dup', size=[32,32], offset=[1,1], sub_theme='slideDup', options=bgui.BGUI_CACHE|bgui.BGUI_BOTTOM|bgui.BGUI_RIGHT)
		dupWidget.on_left_click = self.slideAdd
		dupWidget.tooltip = "Duplicate this slide"

		# capture button
		# captureWidget = bgui.ImageButton(slideWidget, 'capture', size=[16,16], offset=[8,8], sub_theme='slideCapture', options=bgui.BGUI_CACHE|bgui.BGUI_BOTTOM|bgui.BGUI_LEFT)
		# captureWidget.on_left_click = self.slideCapture

		# register widget
		slide.ui = slideWidget
		self.slides.append(slideWidget)


	def widgetDelete(self, slideWidget):
		slideWidget.kill()
		self.slides.remove(slideWidget)


	def	slideLeftClick(self, widget=None):
		"""Invoked when the slide is left-clicked"""
		slide, index = self.getMVBSlide(widget)
		if slide:
			# activate slide
			logic.mvb.activeSlide = index
			self.slideHighlight(index)

			# move slide
			self.clickedXY = logic.mouse.position
			


	def slideLeftClickActive(self, widget=None):
		''' When the slide is being clicked '''
		x, y = logic.mouse.position
		threshold = 0.001

		if self.clickedXY and ((abs(x-self.clickedXY[0]) > threshold) or  (abs(y-self.clickedXY[1]) > threshold)):
			self.slideMove(widget)
			self.clickedXY = None

	def slideLeftRelease(self, widget=None):
		self.clickedXY = None


	def slideRightClick(self,  widget=None):
		"""invoked with right click on a highlighted slide for choosing option for pop-up menu widget"""

		#create the Menu UI w/its lower left corner at the mouse cursor position
		menuItems = ["Duplicate Slide", "Delete Slide", "Capture"]
		self.popUpMenu = logic.gui.showMenu(name="popUpMenu", pos=logic.mouse.position, caller=widget, callback=selectMenuOption, items=menuItems)

		#logic.mvb.deleteSlide(i)										# delete from model
		#self.slideAdd()


	# ------------utility functions ---------
	def tickMarkUpdate(self):
		"""invoked when user modifies interval value, adds or deletes slide; used for positioning tickmark at a given slide's timestamp"""
		for widget in self.ticks:
			widget.kill()
		self.ticks = []

		for slide in logic.mvb.slides:
			try:
				tickmarkPos = [(self.timeLineProgress.size[0] * (slide.time / logic.mvb.getTotalTime())),0]
			except:
				tickmarkPos = [0,0]

			tick = bgui.Frame(self.timeLineProgress, "timeLineTickmark"+str(slide.id), size=[2, 16],pos=tickmarkPos)
			self.ticks.append(tick)

		logic.mvb.activeSlide = logic.mvb.activeSlide



	def onMouseWheelUp(self, widget):
		self.increamentValue(widget, 0.1)
		self.scroller.locked = True

	def onMouseWheelDown(self, widget):
		self.increamentValue(widget, -0.1)
		self.scroller.locked = True
		
		
	def setValueFinal(self, widget):
		self.setValue(widget, final=True)

	def setValue(self, widget, final=False):
		try:
			number = float(widget.text)
		except:
			if final:
				print("Cannot parse value, resetting to default")
				widget.text = str(defaultAnimationInterval)
		else:
			if number > 100:
				number = 100
				widget.text = str(round(number,1))
			elif number < 0.1:
				number = 0.1
				widget.text = str(round(number,1))

			name = widget.parent.name[:-9]
			try:
				slideWidget = self.scroller.children[name]
			except:
				print("slide not found")

			slide, index = self.getMVBSlide(slideWidget)
			if slide:
				slide.interval = round(number, 1)


	def increamentValue(self, widget, value):
		try:
			number = float(widget.text)
		except:
			print("Cannot parse value, resetting to default")
			widget.text = str(defaultAnimationInterval)
		else:
			number += value
			if number > 100:
				number = 100
			elif number < 0.1:
				number = 0.1
			widget.text = str(round(number,1))

			name = widget.parent.name[:-9]
			try:
				slideWidget = self.scroller.children[name]
			except:
				print("slide not found")

			slide, index = self.getMVBSlide(slideWidget)
			if slide:
				slide.interval = round(number, 1)


	def getMVBSlide(self, widget):
		for i, slide in enumerate(logic.mvb.slides):
			if widget == slide.ui:
				return slide, i
		print("Error: Slide not found in model")
		return None, None


	def slideHighlight(self, index, fill = None):
		for w in self.slides:
			w.border = 0
			w.children['progress'].size = [1,0]

		slideWidget = logic.mvb.slides[index].ui
		slideWidget.border = 3

		if fill:
			slideWidget.children['progress'].size = [fill, 1]


	def slideCapture(self, widget):
		pass

# instantiates the timeline singleton
def init(timelineWidget, scrollerWidget, sys):
	return Timeline(timelineWidget, scrollerWidget, sys)
