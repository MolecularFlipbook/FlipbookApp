# import blender gamengine modules
from bge import logic
from bge import render

from . import bgui
from .helpers import *
from .settings import *

import fractions, time, os

class Gate:
	'''gate singleton'''

	#offset = [10, 5]
	offset = [0, 0]

	arList = [	[1,1,'1:1'],
				[4,3,'4:3'],
				[16,10,'16:10'],
				[16,9,'16:9'],
				[235,100,'2.35:1']
	]

	def __init__(self, system):
		self.sys = system
		self._arIndex = 3
		self.offset = [0,0,0,0]
		self.edgeOffsetOriginal = [180,170,180,170]
		self.edgeOffset = self.edgeOffsetOriginal[:]
		self._visible = True


		# resolution gate
		self.resolutionGate = bgui.Box(self.sys, 'resolutionGate', offset=self.edgeOffset, options=bgui.BGUI_LEFT|bgui.BGUI_BOTTOM|bgui.BGUI_FILLED|bgui.BGUI_NO_FOCUS)

		self.RG1 = bgui.Frame(self.sys, 'RG1', size=[0,0], sub_theme='neutral', options=bgui.BGUI_FILLX|bgui.BGUI_TOP|bgui.BGUI_NO_FOCUS)
		self.RG2 = bgui.Frame(self.sys, 'RG2', size=[0,0], sub_theme='neutral', options=bgui.BGUI_FILLX|bgui.BGUI_BOTTOM|bgui.BGUI_NO_FOCUS)
		self.RG3 = bgui.Frame(self.sys, 'RG3', size=[0,0], sub_theme='neutral', options=bgui.BGUI_FILLY|bgui.BGUI_LEFT|bgui.BGUI_BOTTOM|bgui.BGUI_NO_FOCUS)
		self.RG4 = bgui.Frame(self.sys, 'RG4', size=[0,0], sub_theme='neutral', options=bgui.BGUI_FILLY|bgui.BGUI_RIGHT|bgui.BGUI_BOTTOM|bgui.BGUI_NO_FOCUS)

		# capture button
		# self.capture = bgui.ImageButton(self.resolutionGate, 'capture', size=[16,16], offset=[-2,-1],  sub_theme='slideCapture', options=bgui.BGUI_TOP|bgui.BGUI_RIGHT)
		# self.capture.on_left_release = self.captureScreen

		self.slideNumber = bgui.Label(self.resolutionGate, 'slideNumber', text='', sub_theme='bigLabel', pos=[0,0], offset=[0,-10], options=bgui.BGUI_TOP|bgui.BGUI_LEFT|bgui.BGUI_NO_FOCUS)

		# keeps track of captured screenshots
		self.screenshotList = []


	@property
	def dimension(self):
		g = self.resolutionGate
		dimension = [g.position[0], g.position[1], g.size[0], g.size[1]]
		return [int(i) for i in dimension]

	@property
	def visible(self):
		return self._visible

	@visible.setter
	def visible(self, value):
		self._visible = value
		self.RG1.visible = value
		self.RG2.visible = value
		self.RG3.visible = value
		self.RG4.visible = value
		self.resolutionGate.visible = value

	@property
	def ar(self):
		num, dem, arString = Gate.arList[self._arIndex]
		return fractions.Fraction(num, dem), arString


	@ar.setter
	def ar(self, index):
		self._arIndex = index


	def ARSwitch(self, widget=None, switch=True):
		if switch:
			self._arIndex = (self._arIndex+1)%len(Gate.arList)
		self.viewUpdate(widget)


	def captureScreen(self, widget=None, path=None, zoom=0, crop=True):
		silent = True
		if not path:
			path = os.path.join(logic.tempFilePath, 'media', "{0}.png".format(time.asctime()))
			silent = False

		try:
			if zoom == 0:
				if crop:
					render.makeScreenshot(path, *self.dimension)
				else:
					render.makeScreenshot(path)
			else:
				d=[
				self.dimension[0]+self.dimension[2]*zoom,
				self.dimension[1]+self.dimension[3]*zoom,
				self.dimension[2]-self.dimension[2]*zoom,
				self.dimension[3]-self.dimension[3]*zoom
				]
				d = [int(i) for i in d]
				render.makeScreenshot(path, *d)
				
		except Exception as E:
			if useDebug:
				print("Warning: Cropping screenshot not supported in this version of Blender", E)
			render.makeScreenshot(path)

		if not silent:
			self.screenshotList.append(path)
			logic.registeredFunctions.append(self.captureScreenVerifier)


	def captureScreenVerifier(self):
		if not self.screenshotList:
			return False

		for path in self.screenshotList:
			if os.path.exists(path):
				logic.logger.new("Saved screen capture")
				logic.gui.showModalMessage(subject='Screen capture saved to:', message=path)
				self.screenshotList.remove(path)
		return True


	def viewUpdate(self, widget=None):
		w=render.getWindowWidth()
		h=render.getWindowHeight()
		idealWidth = w-self.edgeOffset[0]-self.edgeOffset[2]
		idealHeight = h-self.edgeOffset[1]-self.edgeOffset[3]

		if idealWidth/idealHeight > self.ar[0]:
			# window too wide for gate, pan&scan
			newHeight = int(idealHeight)
			newWidth = int(idealHeight * float(self.ar[0]))
			newOffset=[ (w - newWidth)/2 + Gate.offset[0],
						self.edgeOffset[1],
						(w - newWidth)/2 - Gate.offset[0],
						self.edgeOffset[3],
						]
		else:
			# window too tall for gate, letterbox
			newWidth = int(idealWidth)
			newHeight = int(idealWidth / float(self.ar[0]))
			newOffset=[ self.edgeOffset[0] - Gate.offset[1],
						(h - newHeight)/2,
						self.edgeOffset[2] + Gate.offset[1],
						(h - newHeight)/2,
						]

		newOffset = [int(i) for i in newOffset]
		self.offset = newOffset[:]
		self.resolutionGate._offsetTarget = newOffset[:]
		self.RG1.size=[0,newOffset[1]-2]
		self.RG2.size=[0,newOffset[3]-2]
		self.RG3.size=[newOffset[0]-1, 0]
		self.RG3.offset = [0, newOffset[1]-2, 0, newOffset[1]-2]
		self.RG4.size=[newOffset[2]-1, 0]
		self.RG4.offset = [0, newOffset[1]-2, 0, newOffset[1]-2]

		if widget:
			widget.text = self.ar[1]


def init(system):
	# create the gate singleton
	return Gate(system)
