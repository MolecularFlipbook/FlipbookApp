from .widget import *
from .frame import *
from .label import *


class MenuRenderer():
	"""Base class for rendering an item in a Menu"""
	def __init__(self, menu):
		"""
		:param menu: the menu the renderer will be used
		with (used for parenting)
		"""
		self.label = Label(menu, "label", sub_theme = "ItemLabel", options=BGUI_NONE)

	def render_item(self, item):
		"""Creates and returns a :py:class:`bgui.label.Label`
		representation of the supplied item

		:param item: the item to be rendered
		:rtype: :py:class:`bgui.label.Label`
		"""
		self.label.text = str(item)
		return self.label


class Menu(Widget):
	"""Widget for displaying a list of data"""

	theme_section = 'Menu'
	theme_options = {'HighlightColor1': (1, 1, 1, 1),
					 'HighlightColor2': (0, 0, 1, 1),
					 'HighlightColor3': (0, 0, 1, 1),
					 'HighlightColor4': (0, 0, 1, 1),
					 'Border': 0,
					 'Padding': 0,
					 'itemHeight': 32,
					 'BGSubTheme': ''
					 }

	def __init__(self, parent, name, items=[], padding=0,
				 size=[150, 1], pos=[0, 0], offset=[0, 0], clickHandler=None,
				 sub_theme='', radius=5, border=None, caller=None, hideHandler=None, options=BGUI_NONE):
		"""
		:param parent: the widget's parent
		:param name: the name of the widget
		:param items: the items to fill the list with (can also be changed via Menu.items)
		:param padding: the amount of extra spacing to put between items (can also be changed via Menu.padding)
		:param size: a tuple containing the width and height
		:param pos: a tuple containing the x and y position
		:param sub_theme: name of a sub_theme defined in the theme file (similar to CSS classes)
		:param options: various other options
		"""

		Widget.__init__(self, parent, name, size=size, pos=pos, offset=offset, sub_theme=sub_theme, options=options)

		self.container = Frame(self, "frameContainer", size=[1, 1], pos=[0, 0], sub_theme=self.theme['BGSubTheme'], radius = radius, options=BGUI_NORMALIZED)

		self.itemHeight = self.theme['itemHeight']

		self._items = items
		if padding:
			self._padding = padding
		else:
			self._padding = self.theme['Padding']

		self.highlight = Frame(self, "frame", radius = 0)
		self.highlight.visible = False

		if border is not None:
			self.highlight.border = border
		else:
			self.highlight.border = self.theme['Border']

		self.highlight.colors = [self.theme['HighlightColor1'],
								 self.theme['HighlightColor2'],
								 self.theme['HighlightColor3'],
								 self.theme['HighlightColor4']]

		self.selected = None
		self._spatial_map = {}

		self._renderer = MenuRenderer(self)
		self._clickHandler = clickHandler
		self._caller = caller
		self._hideHandler = hideHandler

	##
	# These props are created simply for documentation purposes
	#
	@property
	def renderer(self):
		"""The MenuRenderer to use to display items"""
		return self._renderer

	@renderer.setter
	def renderer(self, value):
		self._renderer = value

	@property
	def padding(self):
		"""The amount of extra spacing to put between items"""
		return self._padding

	@padding.setter
	def padding(self, value):
		self._padding = value

	@property
	def items(self):
		"""The list of items to display in the Menu"""
		return self._items

	@items.setter
	def items(self, value):
		self._items = value
		self._spatial_map.clear()

	def _handle_mouse_exit(self):
		self.selected = None

	def _draw(self):

		# this goes above _draw to avoid 1-frame delay artifact
		self.size = [self.size[0], len(self.items)*self.itemHeight+self._padding*2]
		self.container._draw()

		for idx, item in enumerate(self.items):
			w = self.renderer.render_item(item)
			w.position = [0, self.size[1]-self._padding-(idx+1)*self.itemHeight]
			w.size = [self.size[0], self.itemHeight]

			if self.selected == item:
				self.highlight.gl_position = [i[:] for i in w.gl_position]
				self.highlight.visible = True
				self.highlight._draw()
			elif not self.selected:
				self.highlight.visible = False

		for idx, item in enumerate(self.items):
			w = self.renderer.render_item(item)
			w.position = [0, self.size[1]-self._padding-(idx+1)*self.itemHeight]
			w.size = [self.size[0], self.itemHeight]
			self._spatial_map[item] = [i[:] for i in w.gl_position]  # Make a full copy
			w.position = [0+10, self.size[1]-self._padding-(idx+1)*self.itemHeight + (self.itemHeight - w.pt_size)/2]
			w._draw()

		# check to see if focus has changed
		if self.system.focused_widget != self and self.system.focused_widget != self._caller:
			self._hideHandler(self)

	def _handle_mouse(self, pos, event):

		# mouse over item
		for item, gl_position in self._spatial_map.items():
			if (gl_position[0][0] <= pos[0] <= gl_position[1][0]) and \
				(gl_position[0][1] <= pos[1] <= gl_position[2][1]):
					self.selected = item
					break
			else:
				self.selected = None

		# mouse release
		if event == BGUI_MOUSE_RIGHT_RELEASE or event == BGUI_MOUSE_LEFT_RELEASE or event == BGUI_MOUSE_RIGHT_CLICK or event == BGUI_MOUSE_LEFT_CLICK:
			if self.selected:
				index = self.items.index(self.selected)
				self._clickHandler(index)
				self._hideHandler(self)

		return True
