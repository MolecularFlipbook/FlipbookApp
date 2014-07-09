# import blender gamengine modules
from bge import logic
from .settings import *
from . import bgui

import logging

allowDuplicate = True

class Logger:
	"""Message logger singleton"""
	def __init__(self, widget):
		self.bigList = []
		self.panel = widget

		# init secondary UI elements
		self.logger1 = bgui.Label(self.panel, 'logger1', sub_theme='whiteLabelSmall', options=bgui.BGUI_CENTERX|bgui.BGUI_NO_FOCUS)
		self.logger2 = bgui.Label(self.panel, 'logger2', sub_theme='whiteLabelSmall', options=bgui.BGUI_CENTERX|bgui.BGUI_NO_FOCUS)
		self.logger3 = bgui.Label(self.panel, 'logger3', sub_theme='whiteLabelSmall', options=bgui.BGUI_CENTERX|bgui.BGUI_NO_FOCUS)

		self.panel.visible = useLogger

	def new(self, msg, type = "MESSAGE", repeat = True):				# type can be "ERROR", "WARNING", or "MESSAGE"
		"""creates a new log entry and add to memory"""
		if self.bigList:												# make sure bigList is not empty
			if (not repeat) and (msg == self.bigList[-1].msg):
				pass
			else:
				self._addEntry(msg, type)								# add to logger if repeat mode is set to false
		else:
			self._addEntry(msg, type)

		# trim list when it gets too long
		if len(self.bigList) > 200:
			self.bigList = self.bigList[-100:]


	def _addEntry(self, msg, type):
		try:
			if self.bigList[-1].msg != msg or allowDuplicate:
				self.bigList.append(entry(msg, type))
				self._updateDisplay()
		except IndexError:
			self.bigList.append(entry(msg, type))
			self._updateDisplay()


	def _getEntry(self, count = 0):
		"""returns a particular entry, 0th is last entry, -1 returns the second last entry, ad infinitum"""
		return (self.bigList[count-1].msg, self.bigList[count-1].color)


	def _updateDisplay(self):
		"""refreshes the bgui elements"""
		animationTime = 400
		x = 0

		try:
			self.logger1.position = [x,10]
			text, color = self._getEntry()
			color[3] = 0.9
			self.logger1.text = text
			self.logger1.color = color

			self.logger2.position = [x,30]
			text, color = self._getEntry(-1)
			color[3] = 0.6
			self.logger2.text = text
			self.logger2.color = color

			self.logger3.position = [x,50]
			text, color = self._getEntry(-2)
			color[3] = 0.3
			self.logger3.text = text
			self.logger3.color = color

			self.logger1.move([x, 25], animationTime/4.0)
			self.logger2.move([x, 45], animationTime/2.0)
			self.logger3.move([x, 65], animationTime)
		except IndexError:
			pass


class entry:
	"""The log entry"""
	def __init__(self, msg, msgType):
		self.msg = str(msg)
		self.type = msgType

		if msgType == "ERROR":
			self.color = [0.5,0,0,1]
			logging.error("Logger Message: \t" + msg)
		elif msgType == "WARNING":
			self.color = [0.7,0.4,0,1]
			logging.warning("Logger Message: \t" + msg)
		else:
			self.color = [0,0,0,1]
			logging.debug("Logger Message: \t" + msg)

def init(widget):
	# create the logger singleton
	return Logger(widget)
