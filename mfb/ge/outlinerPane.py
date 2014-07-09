# import gamengine modules
from bge import logic
from bge import events
from bge import render

# import mvb's own module
from . import bgui
from .helpers import *

# native python modules
import math, pdb


outlinerLabel = "outlinerLabel_"
outlinerHelper1 = "outlinerHelper1_"
outlinerHelper2 = "outlinerHelper2_"


class Outliner():
	''' singleton class for managing the outliner'''
	def __init__(self, widget):
		self.panel = widget 		# the scroll area
		self.cursor = [0,20]			# the position of the drawing cursor
		self.uiList = {}			# a temp space to store all the generated UI elements, for easy removal
		self.root = {}				# holds the outliner tree

	def __repr__(self, verbose=False):
		''' display the data model'''
		s = ""
		for key, value in sorted(self.root.items()):
			if value.children:
				s += (value.name + "\n")
				for child in sorted(value.children):
					s += ('  -' + child.name + "\n")
			else:
				s += (value.name + "\n")
			
		return s


	def updateModel(self):
		
		self.root = {}

		for objName, obj in logic.mvb.objects.items():
			if not obj.inactive and obj.type <= 1:   # only work on active blobber or PDB objects
				isBlobber = bool(obj.type)
				mol = obj.pdbData
				parent = obj.parent

				if parent:
					# has parent; generate or udpate root
					listEntry = OutlinerLevel1(name = objName, children = [], kxObj = obj.obj, matrix=bool(obj.matrix))
					
					try:
						# add children to root
						if obj.matrix:
							self.root[parent+' (bioMT)'].addChildren(listEntry)
						else:
							self.root[parent].addChildren(listEntry)

					except KeyError:
						# create root, then add children
						if obj.matrix:
							self.root[parent+' (bioMT)'] = OutlinerLevel0(name = parent+' (bioMT)', children = [listEntry], kxObj = None)
						else:
							self.root[parent] = OutlinerLevel0(name = parent, children = [listEntry], kxObj = None)

				else:
					# no parent; promote obj to root directly
					try:
						self.root[objName]
						# print('Warning: Root object already exist in outliner.')
					except KeyError:
						self.root[objName] = OutlinerLevel0(name = objName, children = [], kxObj = obj.obj)
					
		# draw the UI
		self.updateView()


	def updateView(self):
		''' draw outliner UI'''
		# reset the cursor
		self.cursor = [0,20]

		# remove previous labels
		for key, i in self.uiList.items():
			try:
				i.kill()
				del i
			except:
				pass
		self.uiList = {}

		# add new labels
		for key, item in sorted(self.root.items()):
			if item.children:
				item._draw(self.cursor)				# draw root of children
				for child in sorted(item.children):
					child._draw(self.cursor)		# draw children
			else:
				item._draw(self.cursor)				# childless items
				
		# fit Scroll area based on the used up area
		self.panel.fitY(math.fabs(self.cursor[1])+40)
		self.updateSelection()


	def updateSelection(self):
		''' do a quick update, without destroying any widgets'''
		greenLow = (0.3, 0.9627, 0.35, 0.2)
		greenHigh =(0.3, 0.9627, 0.35, 0.4)
		grey = (0.6627, 0.6627, 0.6627, 0.2)

		for key, item in self.root.items():
			if item.children:
				
				# handle children first
				combinedSelection = []
				combinedLocked = []
				for child in item.children:
					selected = child.kxObj in logic.mvb._activeObjs
					if selected:
						if child.widget: child.widget.color = greenHigh
						combinedSelection.append(True)
					else:
						if child.widget: child.widget.color = grey
						combinedSelection.append(False)

					# update
					if child.widget:
						lbName = outlinerHelper2+child.name
						h2 = child.widget.children[lbName]
						h2.state = logic.mvb.getMVBObject(child.kxObj).locked
						combinedLocked.append(h2.state)
	
				# handle parent of children
				if all(combinedSelection) and combinedSelection:
					# all are selected
					item.widget.color = greenHigh
				elif any(combinedSelection):
					# some are selected
					item.widget.color = greenLow
				else:
					# none are selected
					item.widget.color = grey

				if all(combinedLocked) and combinedLocked:
					# all are locked
					lbName = outlinerHelper2+item.name
					item.widget.children[lbName].state = True
				elif any(combinedLocked):
					# some are locked
					lbName = outlinerHelper2+item.name
					item.widget.children[lbName].state = False
				else:
					# none are locked
					lbName = outlinerHelper2+item.name
					item.widget.children[lbName].state = False


			else:
				# handle root entries
				selected = item.kxObj in logic.mvb._activeObjs
				if selected:
					item.widget.color = greenHigh
				else:
					item.widget.color = grey


				lbName = outlinerHelper2+item.name
				item.widget.children[lbName].state = logic.mvb.getMVBObject(item.kxObj).locked

		# Update the dots that represent the number of selected objects
		num = len(logic.mvb._activeObjs)
		if num <=0:
			logic.gui.selectionCounter.text= ""
		elif num > 18:
			logic.gui.selectionCounter.text= "."*18
		else:
			logic.gui.selectionCounter.text= "."*num
				



class OutlinerBase():
	''' base class containing ui info for children, to be extended. do not use directly'''
	def __init__(self, name, children, kxObj, expanded = True):
		self.name = name
		self.children = children
		self.kxObj = kxObj
		self.expanded = expanded
		self.widget = None
		

	def __lt__(self, other):
         return self.name < other.name


	def toggleLock(self, widget):
		''' toggle selection locking'''
	
		if self.children:
			for child in self.children:
				mvbObj = logic.mvb.getMVBObject(child.kxObj)
				mvbObj.locked = widget.state
		else:
			mvbObj = logic.mvb.getMVBObject(self.kxObj)
			mvbObj.locked = widget.state

		logic.outliner.updateSelection()

	
	def _onRClick(self, widget):
		'''	handles when an the entry is right clicked'''
		pass


	def _onLClick(self, widget):
		'''	handles when an the entry is clicked'''
		# clicked on main entry
		isShifted = logic.gui.isShifted or logic.gui.isCtrled or logic.gui.isCommanded
		subtractSelection = logic.gui.isAlted

		if not isShifted and not subtractSelection:
			logic.mvb.activeObjs.clear()
				

		if self.children:
			# select all children
			for child in self.children:
				if subtractSelection:
					logic.mvb.activeObjs.remove(child.kxObj)
				else:
					logic.mvb.activeObjs.add(child.kxObj)
		else:
			# select self
			if subtractSelection:
				logic.mvb.activeObjs.remove(self.kxObj)
			else:
				logic.mvb.activeObjs.add(self.kxObj)

		logic.outliner.updateSelection()


	def _onHover(self, widget):
		''' handles when the mouse is over an entry'''
		# highlight kxObjects when hovering over the outline
		if self.children:
			# mouse is over a molecule (i.e. parent of chains)
			logic.mvb.preActiveObj = [child.kxObj for child in self.children]
		else:
			# mouse is over a chain
			logic.mvb.preActiveObj = [self.kxObj]
		

	def _draw(self, label, cursor):
		''' create UIs'''

		indent = cursor[0]
		cursor[0] = 10
		cursor[1] -= 20

		# setup label text
		try:
			if self.expanded:
				text = " "*indent + " -   " + label
			else:
				text = " "*indent + " +   " + label
		except AttributeError:
			text = " "*indent + " -   " + label

		# draw entry
		lbName = outlinerLabel+self.name
		item = bgui.FrameButton(logic.outliner.panel, lbName, text=text, size=[190,18], \
			pos=[0,0], sub_theme = "listEntry", offset=cursor[:], centerText=False, \
			options=bgui.BGUI_TOP|bgui.BGUI_LEFT)

		item.lighter = True
		item.on_left_release = self._onLClick
		item.on_right_release = self._onRClick
		item.on_mouse_enter = self._onHover
		logic.outliner.uiList[lbName] = item
		self.widget = item

		# draw helper buttons
		lbName = outlinerHelper2+self.name
		item =  bgui.ImageButton(item, lbName, size=[16,16],  pos=[138,0], sub_theme="helper2")
		item.state = False
		item.on_left_release = self.toggleLock
		logic.outliner.uiList[lbName] = item

	def addChildren(self, child):
		self.children.append(child)


class OutlinerLevel0(OutlinerBase):
	def __init__(self, name, children, kxObj, expanded = True):
		self.label = name[:]
		OutlinerBase.__init__(self, name, children, kxObj, expanded = expanded)

	def _draw(self, cursor):
		cursor[0] = 2
		if self.kxObj:
			if self.kxObj.visible:
				OutlinerBase._draw(self, self.label, cursor)
			else:
				OutlinerBase._draw(self, self.label+' (hidden)', cursor)
		else:
			OutlinerBase._draw(self, self.label, cursor)


class OutlinerLevel1(OutlinerBase):
	def __init__(self, name, children, kxObj, expanded = False, matrix=False):
		self.label = name[:]
		self.matrix = matrix
		OutlinerBase.__init__(self, name, children, kxObj, expanded = expanded)

	def _draw(self, cursor):
		if self.matrix:
			return
		cursor[0] = 10
		if self.kxObj:
			if self.kxObj.visible:
				OutlinerBase._draw(self, self.label, cursor)
			else:
				OutlinerBase._draw(self, self.label+' (hidden)', cursor)
		else:
			OutlinerBase._draw(self, self.label, cursor)



class OutlinerLevel2(OutlinerBase):
	def __init__(self, name, children, kxObj, expanded = False):
		self.label = name[:]
		OutlinerBase.__init__(self, name, children, kxObj, expanded = expanded)

	def _draw(self, cursor):
		cursor[0] = 16
		if self.kxObj:
			if self.kxObj.visible:
				OutlinerBase._draw(self, self.label, cursor)
			else:
				OutlinerBase._draw(self, self.label+' (hidden)', cursor)
		else:
			OutlinerBase._draw(self, self.label, cursor)



def init(widget):
	''' initializes the outliner object '''
	return Outliner(widget)
