from bgl import *
from .widget import *

class Custom(Widget):
	"""Frame for storing other widgets"""
	theme_section = 'Custom'
	theme_options = {}

	def __init__(self, parent, name, func=None, size=[1, 1], pos=[0,0], offset=[0,0],
				sub_theme='', options=BGUI_NONE):
		"""
		:param parent: the widget's parent
		:param name: the name of the widget
		:param border: the size of the border around the frame (0 for no border)
		:param size: a tuple containing the width and height
		:param pos: a tuple containing the x and y position
		:param sub_theme: name of a sub_theme defined in the theme file (similar to CSS classes)
		:param options: various other options

		"""
		Widget.__init__(self, parent, name, size, pos, offset, sub_theme, options)
		self.func = func


	def _draw(self):
		"""Draw the frame"""
		if callable(self.func):
			self.func()
