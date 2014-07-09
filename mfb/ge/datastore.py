# import gamengine modules
from bge import logic
from bge import events
from bge import render

from .helpers import *
from .settings import *
from . import shader
from . import OPEditor

# import python builtin modules
import sys
import os
import time
import string
import random
import math
import colorsys
import pdb
import imp
import inspect

class PDBMetaData():
	""" general molecule information from parsed PDB"""
	def __init__(self, title, chaininfo, detmethod, resolution, authors, articlename, journal, issn, doi):
		self.title = title
		self.chaininfo = chaininfo
		self.detmethod = detmethod
		self.resolution = resolution
		self.authors = authors
		self.articlename = articlename
		self.journal = journal
		self.issn = issn
		self.doi = doi

class Linker():
	def __init__(self):
		self.A = None
		self.B = None
		self.KXobjects = []
		

class MVBObject():
	""" 3d object class"""
	def __init__(self, name, obj, objType):
		self.name = str(name)					# name of the protein object
		self.obj = obj							# blender game engine KX_object reference
		self._rot = [0,0,0] 					# need to store internal rot because blender wraps value past 2pi
		self.type = objType						# object type, 0 = normal. 1 = blobber. 2 = aux
		self.scale = [1,1,1]					# only used by blobber
		self.chainData = None 					# pdb data blob for just this chain / partial chain
		self.residueSequence = None 			# residue sequence used by the protein editor
		self.residueSequenceMarked = {} 		# marked residue sequence
		self.pdbData = None						# pdb data blob
		self.pdbMetaData = None					# pdbMetaData object; general mol info
		self.parent = None 						# parent in the outliner
		self._drawMode = 'fineSurface'			# surface, fineSurface, ribbon, etc
		self.surfaceMesh = None 			 	# string to lib-loaded surface mesh
		self.fineSurfaceMesh = None 			# string to lib-loaded detailed surface mesh
		self.ribbonMesh = None 					# string to lib-loaded backbone mesh
		self.color = list(colorsys.hsv_to_rgb(random.random(), 0.7, 1.0))		# surface color
		self._shader = "default"				# surface shader
		self._inactive = False					# flag for deleted object
		self._locked = False
		self.matrix = None 						# bioMT matrix

		self.largeRadius = False 				# import options
		self.bioMT = False 						# import options
		
	@property
	def locked(self):
		return self._locked
	@locked.setter
	def locked(self, value):
		self._locked = value

	

	@property
	def drawMode(self):
		return self._drawMode

	@drawMode.setter
	def drawMode(self, value):
		if value != self._drawMode:
			self._drawMode = value

			if value == 'surface':
				self.obj.replaceMesh(self.surfaceMesh)
				self.hidden = False
			elif value == 'fineSurface':
				self.obj.replaceMesh(self.fineSurfaceMesh)
				self.hidden = False
			elif value == 'ribbon':
				self.obj.replaceMesh(self.ribbonMesh)
				self.hidden = False
			elif value == 'hidden':
				self.hidden = True
			else:
				#invalid draw mode
				pass

			shader.initProtein(self.obj, self._shader)


	@property
	def inactive(self):
		return self._inactive

	@inactive.setter
	def inactive(self, value):
		self._inactive = value
		self.hidden = value

	@property
	def shader(self):
		return self._shader

	@shader.setter
	def shader(self, value):
		if value != self._shader:
			shader.initProtein(self.obj, value, update=True)
			self._shader = value

	@property
	def loc(self):
		return self.obj.worldPosition

	@loc.setter
	def loc(self, value):
		self.obj.worldPosition = value

	@property
	def rot(self):
		return self.obj.worldOrientation.to_euler()
		#return self._rot

	@rot.setter
	def rot(self, value):
		#self._rot = value
		self.obj.worldOrientation = value


	@property
	def hidden(self):
		return not self.obj.visible

	@hidden.setter
	def hidden(self, value):
		self.obj.visible = not value

		# force invisible in case the object is inactive
		if self._inactive:
			self.obj.visible = False 

		logic.outliner.updateView()


	def updateMarkers(self, value = None):
		if self.inactive:
			return

		if value != None:
			if value != self.residueSequenceMarked:
				# update model
				self.residueSequenceMarked = value
				# update the view
				if logic.options.view == 'EDITOR':
					OPEditor.update(logic.options.container)
		
		# get list of kx_obj
		kxObjs = [data[1] for residue, data in self.residueSequenceMarked.items()]

		# delete markers
		for obj in self.obj.children:
			if obj not in kxObjs:
				obj.endObject()

		# add markers
		existingMarkerObjs = self.obj.children
		for residue, data in self.residueSequenceMarked.items():
			index, kxObj = data
			if kxObj not in existingMarkerObjs:
				# add
				loc = OPEditor.residueToWorldPosition(self, residue)
				marker = logic.scene.addObject("marker", self.obj)
				marker.worldPosition = loc
				marker.localScale = [1,1,1]
				marker.setParent(self.obj)
				self.residueSequenceMarked[residue] = (index, marker)


class Slide:
	""" keyframe class"""

	def __init__(self, t):
		self.id = random.randint(0,900000000000)# unique ID
		self.time = t							# keyframe time of the slide
		self.animeData = {}						# dictionary of keyframes for individual transforms
		self.ui = None							# container to store BGUI widget
		self.connectorUI = None
		self.capture()							# capture initial animation data

	def capture(self, obj=None, key=None):
		"""capture all object's keyable data"""

		if logic.mvb.playing or logic.mvb.rendering:
			return

		"""capture all object's loc and rot"""
		for objName, obj in logic.mvb.objects.items():
			self.animeData[objName] = {}
			self.animeData[objName]['loc'] = obj.loc[:]
			self.animeData[objName]['rot'] = obj.rot[:]
			self.animeData[objName]['col'] = obj.color[:]
			self.animeData[objName]['shader'] = obj.shader
			self.animeData[objName]['drawMode'] = obj.drawMode
			self.animeData[objName]['markers'] = obj.residueSequenceMarked.copy()

		if hasattr(logic, 'pluggable'):
			logic.pluggable.timeline.keyframe.notify()

	def getUIInterval(self):
		try:
			return float(self.connectorUI.text)
		except:
			return defaultAnimationInterval

	@property
	def interval(self):
		"""Return interval for given slide to the next"""
		for i, slide in enumerate(logic.mvb.slides):
			if slide == self:
				try:
					interval = logic.mvb.slides[i+1].time - slide.time
				except IndexError:
					interval = 0
				return interval



	@interval.setter
	def interval(self, value):
		"""Set interval for given slide"""
		updateAll = False

		for i, slide in enumerate(logic.mvb.slides):
			if slide == self or updateAll:
				try:
					nextSlide = logic.mvb.slides[i+1]
				except IndexError:
					pass
				else:
					if updateAll:
						nextSlide.time = slide.time + slide.getUIInterval()
					else:
						nextSlide.time = slide.time + value

				updateAll = True
		logic.timeline.tickMarkUpdate()
		if hasattr(logic, 'pluggable'):
			logic.pluggable.timeline.intervalChange.notify()


	def __repr__(self):
		return ("\nTime:%.1f\tID: "%self.time + str(self.id)[:4] + "  " + str(self.ui))

	@property
	def time(self):
		"""Return timestamp for given slide"""
		return self._time

	@time.setter
	def time(self, value):
		"""Set timestamp for given slide"""
		self._time = value


class MVBScene:
	"""datastore container for EVERYTHING"""
	# init
	def __init__(self):

		# a dictionary containing all 3d objects
		self.objects = {}

		# a list containing all the animation keyframes
		self.slides = []

		self._activeObjs = set()			# is a set of kx_objects
		self._activeObjsOld = set()			# same as above
		self._preActiveObj = None			# is a kx_object, or, occasionally, a list of kx_objects

		self._activeSlide = 0  				# active highlighted slide

		# timeline of progress bar
		self._time = 0

		# State of Play/Pause mode initialized; UI displays Play icon
		self._playing = False
		self._scrubbing = False
		self._rendering = False
		self._frameCounter = 0

		# looping flag initialized; looping enabled by default
		self._looping = True

		# hoverTimer for random use
		self._hoverTimer = time.time()

		# background
		self.bgColor = defaultSkyColor[:]
		self.bgColorFactor = 1.0
		self.bgImageStretch = True
		self.bgImage = None


	# show all attributes
	def __repr__(self):
		string = ""
		for attr, value in self.__dict__.items():
			if attr == "objects":
				for name, mvbobj in value.items():
					# string += str(mvbobj.parent) + ' : '+ name + " : " + str(mvbobj.loc) + " | " + str(mvbobj.rot) + "\n"
					string += str(mvbobj.parent) + ' : '+ name + "\n"
			elif not attr.startswith('_'):
				string += str(attr) + ": " + str(value) + "\n"
		return string


	@property
	def preActiveObj(self):
		return self._preActiveObj

	@preActiveObj.setter
	def preActiveObj(self, value):
		if value != self._preActiveObj:
			self._hoverTimer = time.time()
		self._preActiveObj = value
		self.hoverObjectUpdate(value)

	@property
	def activeObjs(self):
		'''this functions as a getter AND a setter, because the activeObjs is mutable'''

		# compare old set and current one, if different
		if (self._activeObjs ^ self._activeObjsOld):
			self.selectObjectUpdate()

		# copy current set to back buffer
		self._activeObjsOld = self._activeObjs.copy()

		return self._activeObjs


	@property
	def time(self):
		return self._time

	@time.setter
	def time(self, value):
		value = min(max(value, 0), self.getTotalTime())		# clamp value
		self._time = value
		self.viewTime(value)

	@property
	def activeSlide(self):
		return self._activeSlide

	@activeSlide.setter
	def activeSlide(self, value):
		if value >= 0:
			self._activeSlide = value
		else:
			self._activeSlide = 0

		# go to that time
		if value != 0:
			self.time = self.slides[value].time
		else:
			self.time = 0

		# update slide number
		logic.gate.slideNumber.text = str(self._activeSlide+1)

	@property
	def playing(self):
		"""Return boolean value of the state of Play/Pause mode"""
		return self._playing

	@playing.setter
	def playing(self,value):
		"""Sets Play and Pause UI depending on boolean state of Play/Pause mode"""
		if self.getTotalTime() < 0.01:
			self._playing = False
			logic.timeline.timeLinePlayBtn.state = 0
			return

		if value:
			# check if train/playhead is near end of total time for animation, reset to 0
			self._playing = True
			logic.timeline.timeLinePlayBtn.state = 1
			logic.logger.new("Playing Animation")
			logic.pluggable.timeline.play.notify()
		else:
			self._playing = False
			logic.timeline.timeLinePlayBtn.state = 0
			self.snap()
			logic.logger.new("Paused")
			logic.pluggable.timeline.pause.notify()


	@property
	def rendering(self):
		return self._rendering

	@rendering.setter
	def rendering(self, value):
		self._rendering = value
		self._frameCounter = 0


	@property
	def looping(self):
		"""Returns boolean value of state of playhead"""
		return self._looping

	@looping.setter
	def looping(self,value):
		"""Sets the state of the playhead with boolean value"""
		self._looping = value
		if logic.mvb.looping:
			logic.logger.new("Looping On")
		else:
			logic.logger.new("Looping Off")

	def snap(self):
		"""Snap to the closest slide"""
		for i,slide in enumerate(self.slides):
			if self.time < slide.time:
				a = self.time - self.slides[i-1].time
				b = slide.time - self.time
				if a>b:
					self.activeSlide = i
					logic.timeline.slideHighlight(i)
				else:
					self.activeSlide = i-1
					logic.timeline.slideHighlight(i-1)
				break
			elif self.time == slide.time:
				last = len(self.slides)-1
				self.activeSlide = last
				logic.timeline.slideHighlight(last)

	def hoverObjectUpdate(self, value):
		pass

	def selectObjectUpdate(self):
		logic.outliner.updateSelection()
		logic.options.updateView()


	def addObject(self, name, kxObj, objType=0, molObj=None, chainObj=None, molInfo=None, parent = None, scale=[1,1,1]):
		"""instantiate new objects"""
		"""add mvbObject to GE; assign parsed python molecule object to pdbData
		and associate python object to current mvbObject"""
		self.objects[name] = MVBObject(name, kxObj, objType)
		if molInfo:
			self.objects[name].pdbMetaData = PDBMetaData(*molInfo)
		else:
			self.objects[name].pdbMetaData = None
		self.objects[name].chainData = chainObj
		self.objects[name].pdbData = molObj
		self.objects[name].parent = parent
		self.objects[name].scale = scale[:]

		return self.objects[name]


	def deleteObject(self, mvbObj):
		"""docstring for deleteObject"""
		mvbObj.inactive = True

		#delete markers
		for obj in mvbObj.obj.children:
			if obj.name == 'marker':
				obj.endObject()

		

	def getMVBObject(self, arg):
		"""return the mvb object given the arg"""
		if type(arg) is type(logic.pivotObject):
			for key, mvbobj in self.objects.items():			# arg is an kx_obj object
				if mvbobj.obj == arg:
					return mvbobj
		else:
			raise Exception("Unknown input type for getMVBObject()")


	def addSlide(self, index, silent):
		"""Create a new keyframe"""
		if not self.slides:					# empty list (i.e. happens only on init)
			self.slides.append(Slide(0))
			return 0
		else:								# non-empty list (i.e. all other times)
			time = self.slides[index-1].time + defaultAnimationInterval
			self.slides.insert(index, Slide(time))

			# update interval time
			for i, j in enumerate(self.slides[index+1:]):
				s = self.slides[i+index+1]
				s.time += defaultAnimationInterval

			self.activeSlide = index

			if not silent:
				if hasattr(logic, 'pluggable'):
					logic.pluggable.timeline.addSlide.notify()

			return index


	def deleteSlide(self, index, force=False):
		"""Delete a keyframe"""
		if len(self.slides) <= 1 and not force:
			logic.logger.new("At least one slide must be present", type="WARNING")
			return

		# delete from model
		del self.slides[index]


		if self.slides:
			# update interval time
			self.slides[0].time = 0 		# make sure first slide is at time 0
			self.activeSlide = index - 1

		if hasattr(logic, 'pluggable'):
			logic.pluggable.timeline.deleteSlide.notify()


	def moveSlide(self, a, b):
		""" move slide a to b"""
		logic.logger.new("Moving " + str(a+1) + " to " + str(b+1))


		# compute time interval for destination
		# self.slides[a].time = self.slides[b].time
		# self.slides[b].time = self.slides[b].time + defaultAnimationInterval

		if a == 0:
			self.slides[a+1].time = 0.0

		# swap
		self.slides.insert(b, self.slides.pop(a))

		# set active slide
		self.activeSlide = b

		# ensure time consistency
		self.slides[0].time = 0
		for i, slide in enumerate(self.slides):
			# brute force fixin'
			slide.interval = defaultAnimationInterval

			# try:
			# 	nextSlide = self.slides[i+1]
			# except IndexError:
			# 	pass
			# else:
			# 	if nextSlide.time < slide.time:
			# 		nextSlide.interval = defaultAnimationInterval
			# 		print("Fixing Interval for slide ", nextSlide)


	def viewTime(self, time):

		#update total animation time MM:SS in timeline
		m, s = divmod(self.getTotalTime(), 60)
		garbage, ms = divmod(s, 1000)
		if s < 10.0:
			logic.timeline.timeLabel.text = '%02i:0%03.1f'%(m,s)
		else:
			logic.timeline.timeLabel.text = '%02i:%03.1f'%(m, s)

		# display current animation time MM:SS.S in Train ImageButton widget
		m, s = divmod(self._time,60)
		garbage, ms = divmod(s,1000)
		if s < 10.0:
			logic.timeline.timeLineTrainLabel.text = '%02i:0%03.1f'%(m,s)
		else:
			logic.timeline.timeLineTrainLabel.text = '%02i:%03.1f'%(m,s)

		# do nothing
		if not self.slides:
			return

		# compute immediate previous slide and next slide (time 0 always gives None, None)
		slideA = None
		slideB = None

		try:
			for i,slide in enumerate(self.slides):
				if time > slide.time:				# assume list is in order
					slideA = self.slides[i]
					slideB = self.slides[i+1]
				elif time < 0.001: 					# first slide
					slideA = self.slides[0]
					slideB = self.slides[1]
		except IndexError:
			pass


		if slideA and slideB:
			# normalize time
			timeIntervalA = time - slideA.time 			# always positive, time from last slide
			timeIntervalB = slideB.time - time 			# always positive, time til next slide

			assert(timeIntervalA >= 0)
			assert(timeIntervalB >= 0)

			# normalized viewTime, and fancy interpolation
			if (timeIntervalA + timeIntervalB) == 0:
				return
				
			viewTime = timeIntervalB / (timeIntervalA + timeIntervalB)
			viewTime = smoothstep(viewTime)

			# update GUI progress bar and train position
			try:
				normalized = self._time / self.getTotalTime()
			except:
				normalized = 1.0

			logic.timeline.timeLineProgress.percent = normalized
			logic.timeline.timeLineTrain.position = [normalized*logic.timeline.timeLineTrainTrack.size[0], -5]

			# highlight current slide
			if (self.playing or self.rendering or self._scrubbing) and time > slideA.time:
				curSlideIndex = self.slides.index(slideA)
				logic.timeline.slideHighlight(curSlideIndex, fill = (1-viewTime))
				logic.gate.slideNumber.text = str(curSlideIndex+1)

				# move scroll area
				currentScroll = logic.timeline.scroller._scroll[0]
				newScroll = normalized
				useSmoothScroll = True
				if abs(currentScroll-newScroll) > 0.2 or useSmoothScroll:
					if logic.timeline.scroller._actual[0]> 1.0:
						logic.timeline.scroller._desiredScroll[0] = normalized
				else:
					# don't scroll
					pass

		from . import timeInterpolate
		timeInterpolate.interpolate(self, time)


	def getTotalTime(self):
		"""Return total time of animation"""
		if self.slides:
			return self.slides[-1].time
		else:
			return 0

# instantiate the mvbScene class;
# make sure only this is only called once
try:
	logic.mvb
except:
	logic.mvb = MVBScene()
else:
	logging.exception("Logic.mvb already exist.")
