# import blender gamengine modules
from bge import logic
from bge import events
from bge import render

from .settings import *
from .helpers import *

from . import bgui
from . import OPCreate
from . import OPRepresentation
from . import OPShading
from . import OPCamera
from . import OPEditor
from . import OPLinker
from . import OPFinalize


import imp

class Options():
	def __init__(self, widget, gui):
		self.gui = gui
		self.panel = widget

		# the currently displayed view
		self._view = None
		self.activeModule = None

		# placeholders
		whitespace = 100
		self.header = bgui.Label(self.panel, "header", pos=[10,125], sub_theme='OPHeader', options=bgui.BGUI_NO_FOCUS)
		self.container = bgui.Frame(self.panel, "container", pos=[whitespace,5], offset=[whitespace,5,5,5], sub_theme="invisible", options=bgui.BGUI_FILLED)

		self.closeBtn = bgui.ImageButton(self.panel, 'opClose', size=[20,20], sub_theme="close", options=bgui.BGUI_TOP|bgui.BGUI_RIGHT)
		self.closeBtn.on_left_release = self.close

		self.datastore = {}

	@property
	def view(self):
		return self._view

	@view.setter
	def view(self, value):
		if value == self._view and not useDebug:
			# no change
			pass
		else:
			if self.activeModule and useDebug:
				imp.reload(self.activeModule)

			# change view
			self._view = value

			# clear current view
			self._clearView()

			# set view
			if value == "CREATE":
				self._setView(OPCreate)
			elif value == "SHADING":
				self._setView(OPShading)
			elif value == "REPRESENTATION":
				self._setView(OPRepresentation)
			elif value == "EDITOR":
				self._setView(OPEditor)
			elif value == "CAMERA":
				self._setView(OPCamera)
			elif value == "LINKER":
				self._setView(OPLinker)
			elif value == "FINALIZE":
				self._setView(OPFinalize)
			else:
				self._setView(None)


	def _setView(self, module):
		'''create a view by calling the module'''

		# set the active module
		self.activeModule = module

		if module:
			self.closeBtn.visible = True
			self.panel.size = [800,150]
			self.header.text = module.header
			self.activeModule.showPanel(self.container)
		else:
			self.header.text = ''


	def _clearView(self):
		'''clears the current view'''
		# run destroyer
		try:
			self.activeModule.destroy(self.container)
		except Exception as E:
			# print(E)
			pass

		for key, child in self.container.children.items():
			guiKill(child)


	def close(self, widget=None):
		self.view = None
		self.panel.size = [155,150]
		self.gui.setButtonHighlight(None)
		self.closeBtn.visible = False



	def updateView(self):
		'''refreshes the view when the object scene data has been modified'''
		if self.activeModule:
			if useDebug: imp.reload(self.activeModule)
			self.activeModule.update(self.container)


def init(widget, gui):
	return Options(widget, gui)

