from bgl import *

from .widget import *
from .frame import *
from .label import *
from .. helpers import *

import time

class ToolTip(Widget):
	"""A clickable frame-based button."""
	theme_section = 'ToolTip'
	theme_options = {'Color': (0.4,0.4,0.4,1),
					 'BorderSize': 1,
					 'BorderColor': (0, 0, 0, 1),
					 'LabelSubTheme': '',
				}

	def __init__(self, parent, name, base_color=None, text="", font=None,
					pt_size=None, size=[1,1], pos=[0,0], offset=[0,0], sub_theme='', stipple = False, radius = 5, options=BGUI_NONE):
		"""
		:param parent: the widget's parent
		:param name: the name of the widget
		:param base_color: the color of the button
		:param text: the text to display (this can be changed later via the text property)
		:param font: the font to use
		:param pt_size: the point size of the text to draw (defaults to 30 if None)
		:param size: a tuple containing the width and height
		:param pos: a tuple containing the x and y position
		:param sub_theme: name of a sub_theme defined in the theme file (similar to CSS classes)
		:param options: various other options
		"""

		Widget.__init__(self, parent, name, size, pos, offset, sub_theme, options)

		self.frame = Frame(self, name + '_frame', size=[1,1], pos=[0,0], padding=0, stipple = stipple, radius = radius, options=BGUI_NORMALIZED | BGUI_NO_FOCUS)
		self.label = Label(self, name + '_label', text, font, pt_size, pos=[0,0], sub_theme=self.theme['LabelSubTheme'], options=BGUI_NORMALIZED | BGUI_CENTERED | BGUI_NO_FOCUS)

		if not base_color:
			base_color = self.theme['Color']
		self.base_color = base_color
		self.frame.border = self.theme['BorderSize']
		self.frame.border_color = self.theme['BorderColor']
		self.frame.colors = [self.base_color, self.base_color, self.base_color, self.base_color]
		self._age = time.time()

	@property
	def age(self):
		return self._age

	@property
	def text(self):
		return self.label.text

	@text.setter
	def text(self, value):
		self.label.text = value


	def _draw(self):
		"""Draw the button"""
		# Draw the children before drawing an additional outline
		Widget._draw(self)

		if (time.time() - self.age) > 0.5:
			self.kill()
