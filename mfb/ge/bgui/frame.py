from bgl import *
from .widget import *
from math import cos, sin
# 2x2 alternating block, starting with empty
pat = [ 51,51,51,51,
		51,51,51,51,
		204,204,204,204,
		204,204,204,204,
		51,51,51,51,
		51,51,51,51,
		204,204,204,204,
		204,204,204,204,
		51,51,51,51,
		51,51,51,51,
		204,204,204,204,
		204,204,204,204,
		51,51,51,51,
		51,51,51,51,
		204,204,204,204,
		204,204,204,204,
		51,51,51,51,
		51,51,51,51,
		204,204,204,204,
		204,204,204,204,
		51,51,51,51,
		51,51,51,51,
		204,204,204,204,
		204,204,204,204,
		51,51,51,51,
		51,51,51,51,
		204,204,204,204,
		204,204,204,204,
		51,51,51,51,
		51,51,51,51,
		204,204,204,204,
		204,204,204,204,]


class Frame(Widget):
	"""Frame for storing other widgets"""
	theme_section = 'Frame'
	theme_options = {'Color1': (1, 1, 1, 1),
					 'Color2': (0, 0, 1, 1),
					 'Color3': (0, 0, 1, 1),
					 'Color4': (0, 0, 1, 1),
					 'BorderSize': 0,
					 'BorderColor': (0, 0, 0, 1)
				}

	def __init__(self, parent, name, border=None, size=[1, 1], pos=[0,0],offset=[0,0],
				sub_theme='', padding = 0, radius = 0, stipple = False, options=BGUI_NONE):
		"""
		:param parent: the widget's parent
		:param name: the name of the widget
		:param border: the size of the border around the frame (0 for no border)
		:param size: a tuple containing the width and height
		:param pos: a tuple containing the x and y position
		:param sub_theme: name of a sub_theme defined in the theme file (similar to CSS classes)
		:param options: various other options

		"""
		self.padding = padding
		self.stipple = stipple
		self.radius = radius

		Widget.__init__(self, parent, name, size, pos, offset, sub_theme, options)

		self._colors = [
				self.theme['Color1'],
				self.theme['Color2'],
				self.theme['Color3'],
				self.theme['Color4']
				]

		self.border_color = self.theme['BorderColor']

		if border is not None:
			self._border = border
		else:
			self._border = self.theme['BorderSize']


	@property
	def colors(self):
		"""The colors for the four corners of the frame."""
		return self._colors

	@colors.setter
	def colors(self, value):
		self._colors = value

	@property
	def border(self):
		"""The size of the border around the frame."""
		return self._border

	@border.setter
	def border(self, value):
		self._border = value




	def _draw(self):
		"""Draw the frame"""

		def drawRoundedRectangle(x, y, w, h, radius, color, res = 8, line = False):
			M_PI = 3.141592653589793238462643383279502

			glColor4f(*color)
			if line:
				glBegin(GL_LINE_STRIP)
			else:
				glBegin(GL_POLYGON)
			glVertex2f(x+radius,y)
			glVertex2f(x+w-radius,y)
			i = M_PI*1.5
			while i < M_PI*2.0:
				i += M_PI / res
				glVertex2f(x+w-radius+cos(i)*radius,y+radius+sin(i)*radius)
			glVertex2f(x+w,y+radius)
			glVertex2f(x+w,y+h-radius)
			i = 0
			while i < M_PI*0.5:
				i += M_PI / res
				glVertex2f(x+w-radius+cos(i)*radius,y+h-radius+sin(i)*radius)
			glVertex2f(x+w-radius,y+h)
			glVertex2f(x+radius,y+h)
			i = M_PI*0.5
			while i < M_PI:
				i += M_PI / res
				glVertex2f(x+radius+cos(i)*radius,y+h-radius+sin(i)*radius)
			glVertex2f(x,y+h-radius)
			glVertex2f(x,y+radius)
			i = M_PI
			while i < M_PI*1.5:
				i += M_PI / res
				glVertex2f(x+radius+cos(i)*radius,y+radius+sin(i)*radius)
			glEnd()


		# Enable alpha blending
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

		# Enable polygon offset
		glEnable(GL_POLYGON_OFFSET_FILL)
		glPolygonOffset(1.0, 1.0)

		padx = [self.padding, -self.padding, -self.padding, self.padding]
		pady = [self.padding, self.padding, -self.padding, -self.padding]


		if self.stipple:
			stipplePattern = Buffer(GL_BYTE, 4*32, pat)
			glEnable(GL_POLYGON_STIPPLE)
			glPolygonStipple(stipplePattern)

		if self.radius:
			w = self.gl_position[1][0] - self.gl_position[0][0]
			h = self.gl_position[2][1] - self.gl_position[1][1]
			drawRoundedRectangle(self.gl_position[0][0], self.gl_position[0][1], w, h, self.radius, self.colors[0])
			if self.border:
				glLineWidth(self.border)
				drawRoundedRectangle(self.gl_position[0][0], self.gl_position[0][1], w, h, self.radius, self.border_color, line = True)
				glLineWidth(1.0)
		else:
			glBegin(GL_QUADS)
			for i in range(4):
				glColor4f(self.colors[i][0], self.colors[i][1], self.colors[i][2], self.colors[i][3])
				glVertex2f(self.gl_position[i][0]+padx[i], self.gl_position[i][1]+pady[i])
			glEnd()

		if self.stipple:
			glDisable(GL_POLYGON_STIPPLE)

		glDisable(GL_POLYGON_OFFSET_FILL)

		# Draw an outline
		if self.border > 0 and not self.radius:
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

