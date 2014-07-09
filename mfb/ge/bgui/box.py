from bgl import *
from .widget import *

class Box(Widget):
	"""Frame for storing other widgets"""
	theme_section = 'Box'
	theme_options = {'BorderSize': 1,
					 'BorderColor': (0, 0, 0, 0.2)
				}

	def __init__(self, parent, name, border=1, size=[1, 1], pos=[0,0], offset=[0,0],
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

		self.border_color = self.theme['BorderColor']

		if border is not None:
			self._border = border
		else:
			self._border = self.theme['BorderSize']


	@property
	def border(self):
		"""The size of the border around the frame."""
		return self._border

	@border.setter
	def border(self, value):
		self._border = value

	def _draw(self):
		"""Draw the frame"""

		# Enable alpha blending
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

		# Draw an outline
		if self.border > 0:
			r, g, b, a = self.border_color
			glColor4f(r, g, b, a)
			glPolygonMode(GL_FRONT, GL_LINE)
			glLineWidth(self.border)

			glBegin(GL_QUADS)
			for i in range(4):
				glVertex2f(self.gl_position[i][0], self.gl_position[i][1])

			glEnd()

			glLineWidth(1.0)
			glPolygonMode(GL_FRONT, GL_FILL)

		glDisable(GL_BLEND)
		Widget._draw(self)
