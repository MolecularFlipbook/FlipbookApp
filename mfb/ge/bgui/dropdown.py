from .widget import *
from .frame import *
from .label import *
from .menu import *

class Dropdown(Widget):
	"""Widget for displaying a list of data"""

	theme_section = 'Dropdown'
	theme_options = {'Color': (0.4,0.4,0.4,1)
					}

	def __init__(self, parent, name, items=[],
				 size=[150, 20], pos=[0, 0], offset=[0, 0],
				 sub_theme='', caller=None, options=BGUI_NONE):
		"""
		:param parent: the widget's parent
		:param name: the name of the widget
		:param items: the items to fill the list with (can also be changed via Dropdown.items)
		:param padding: the amount of extra spacing to put between items (can also be changed via Dropdown.padding)
		:param size: a tuple containing the width and height
		:param pos: a tuple containing the x and y position
		:param sub_theme: name of a sub_theme defined in the theme file (similar to CSS classes)
		:param options: various other options
		"""

		Widget.__init__(self, parent, name, size=size, pos=pos, offset=offset, sub_theme='', options=options)

		self.frame = Frame(self, name+'_frame', size=[1,1], pos=[0,0], offset=offset, border=0, radius=2, sub_theme="light", options=BGUI_NORMALIZED|BGUI_NO_FOCUS)
		self.text = Label(self, name+'_text', text=items[0], sub_theme="whiteLabelSmall", options=BGUI_CENTERED|BGUI_NO_FOCUS)

		self._items = items
		self.selectedItem = 0
		self.menu = None

		self.itemHeight = 24
		ContPos = [self.frame.size[0], self.itemHeight*len(items)]

		self._expanded = False

		self._caller = caller
		self._hideHandler = self.hideHandler
		self._clickHandler = self.clickHandler

	@property
	def currentItem(self):
	    return self._items[self.selectedItem]
	

	def clickHandler(self, index):
		"""handles clicks"""
		self.selectedItem = index
		self.text.text = self._items[index]
		if self.menu:
			self.menu.position = [-200,-200]

	def hideHandler(self, widget):
		"""Removes the pop-up menu widget"""
		return


	def _handle_left_click(self, pos):
		if self._expanded:
			if self.menu:
				self.hideHandler(self.menu)

		else:
			pos = [int(self.position[0]), int(self.position[1] - (self.itemHeight)*len(self._items))]
			self.menu = Menu(self.system, name=self.name+'_menu', items=self._items, pos=pos, size=self.frame.size[:], caller=self._caller,\
						clickHandler=self._clickHandler, hideHandler=self._hideHandler, radius=2, border=0, sub_theme='dropdown')


	def _draw(self):
		Widget._draw(self)

		if self != self.system.focused_widget:
			if self.menu:
				self.hideHandler(self.menu)

