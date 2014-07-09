from bgl import *

from .widget import *
from .frame import *
from .label import *

class Swatch(Widget):
	"""A clickable frame-based button."""
	theme_section = 'Swatch'
	theme_options = {'Color': (0.4,0.4,0.4,1),
					 'BorderSize': 1,
					 'BorderColor': (0, 0, 0, 1),
					 'BorderColor2': (0, 0, 0, 1),
				}

	def __init__(self, parent, name, base_color=None, size=[1,1], pos=[0,0], offset=[0,0], sub_theme='', radius = 0, options=BGUI_NONE):
		"""
		:param parent: the widget's parent
		:param name: the name of the widget
		:param base_color: the color of the button
		:param size: a tuple containing the width and height
		:param pos: a tuple containing the x and y position
		:param sub_theme: name of a sub_theme defined in the theme file (similar to CSS classes)
		:param options: various other options
		"""

		Widget.__init__(self, parent, name, size, pos, offset, sub_theme, options)

		self.frame = Frame(self, name + '_frame', size=[1,1], pos=[0,0], padding=0, radius = radius, options=BGUI_NORMALIZED | BGUI_NO_FOCUS)
		if not base_color:
			base_color = self.theme['Color']
		self.base_color = base_color
		self.frame.border = self.theme['BorderSize']
		self.frame.border_color = self.theme['BorderColor']
		self.frame.colors = [base_color, base_color, base_color, base_color]


	@property
	def border(self):
		return self.frame.border

	@border.setter
	def border(self, value):
		self.frame.border = value

	@property
	def color(self):
		return self.base_color

	@color.setter
	def color(self, value):
		self.base_color = value
		self.frame.colors = [value, value, value, value]

	def _draw(self):
		"""Draw the button"""

		# Draw the children before drawing an additional outline
		Widget._draw(self)

