# import gamengine modules
from bge import logic
from bge import events
from bge import render

# import mvb's own module
from .helpers import *
from .settings import *

import copy, pdb, colorsys, random

class Snapshot():
	"""container to hold a single undo snapshot"""
	def __init__(self, desc, props, blob, timeline):
		self.description = desc
		self.props = props
		self.objBlob = blob
		self.timeline = timeline


class Undo():
	"""undo singleton for Undoing"""
	def __init__(self):
		self.stack = []				# big ol' stack of undos
		self.currentState = -1		# active index to the undo stack, -1 is latest, -2 is second latest, etc

	def __repr__(self):
		string = ""
		for stack in self.stack:
			string += str(stack) + "\n"
		return string


	def append(self, description, props='OBJ'):
		'''save snapshot'''
		logic.logger.new(description)
		if self.currentState < -1:
			# since we are creating a new undo, we need to discard all states after currentState
			try:
				self.stack = self.stack[:self.currentState + 1]
			except Exception as E:
				logic.logger.new("Undo Error: " + str(E), type='ERROR')

		# make this the latest snapshot
		self.currentState = -1

		# save snapshot
		blob = {}
		timeline = []

		if props == 'TIMELINE':
			for slide in logic.mvb.slides:
				timeline.append((slide.id, slide.time, slide.animeData))

		for name, obj in logic.mvb.objects.items():
			blob[name] = [list(obj.loc)[:], list(obj.rot)[:], list(obj.color)[:], obj.shader, obj.inactive]

		snapshot = Snapshot(description, props, blob, timeline)

		self.stack.append(snapshot)


	def undo(self):
		'''load snapshot'''
		try:
			snapshot = self.stack[self.currentState]

			if 'TIMELINE' in snapshot.props:
				# apply timeline			
				logic.mvb.activeSlide = 0
				logic.mvb.slides = []

				for slide in snapshot.timeline:
					logic.timeline.slideAdd(silent=True)
					newSlide = logic.mvb.slides[logic.mvb.activeSlide]
					newSlide.time = slide[1]
					newSlide.animeData = slide[2]
					
				logic.timeline.viewUpdate(animate=False)
		
				# do another update
				logic.deferredFunctions.append(lambda: logic.timeline.viewUpdate())
				
			if 'OBJ' in snapshot.props:
				# apply obj properties
				for name, obj in logic.mvb.objects.items():
					obj.loc = snapshot.objBlob[name][0][:]
					obj.rot = snapshot.objBlob[name][1][:]
					obj.color = snapshot.objBlob[name][2][:]
					obj.shader = snapshot.objBlob[name][3]
					obj.inactive = snapshot.objBlob[name][4]
				logic.outliner.updateModel()

			# update undo stack pointer
			self.currentState -= 1
			logic.logger.new('Undo: ' + snapshot.description)

		
		except IndexError:
			pass
		


def init():
	return Undo()