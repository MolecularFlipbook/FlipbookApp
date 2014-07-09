from bgl import *

from .widget import *
from .frame import *
from .label import *

class FrameButton(Widget):
	"""A clickable frame-based button."""
	theme_section = 'FrameButton'
	theme_options = {'Color': (0.4,0.4,0.4,1),
					 'BorderSize': 1,
					 'BorderColor': (0, 0, 0, 1),
					 'LabelSubTheme': '',
				}

	def __init__(self, parent, name, base_color=None, text="", font=None,
					pt_size=None, size=[1,1], pos=[0,0], offset=[0,0], sub_theme='', centerText=True, stipple = False, radius = 0, options=BGUI_NONE):
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
		if centerText:
			self.label = Label(self, name + '_label', text, font, pt_size, pos=[0,0], sub_theme=self.theme['LabelSubTheme'], options=BGUI_NORMALIZED | BGUI_CENTERED | BGUI_NO_FOCUS)
		else:
			self.label = Label(self, name + '_label', text, font, pt_size, pos=[0,0], sub_theme=self.theme['LabelSubTheme'], options=BGUI_NORMALIZED | BGUI_CENTERY | BGUI_NO_FOCUS)

		if not base_color:
			base_color = self.theme['Color']
		self.base_color = base_color
		self.frame.border = self.theme['BorderSize']
		self.frame.border_color = self.theme['BorderColor']

		self.light = [
			self.base_color[0] + 0.1,
			self.base_color[1] + 0.1,
			self.base_color[2] + 0.1,
			self.base_color[3]]
		self.dark = [
			self.base_color[0],
			self.base_color[1],
			self.base_color[2],
			self.base_color[3]]
		self.frame.colors = [self.dark, self.dark, self.light, self.light]

		self.lighter = False

	@property
	def text(self):
		return self.label.text

	@text.setter
	def text(self, value):
		self.label.text = value

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
		self.light = [
			self.base_color[0] + 0.1,
			self.base_color[1] + 0.1,
			self.base_color[2] + 0.1,
			self.base_color[3]]
		self.dark = [
			self.base_color[0],
			self.base_color[1],
			self.base_color[2],
			self.base_color[3]]
		self.frame.colors = [self.dark, self.dark, self.light, self.light]

	def _handle_hover(self, pos):
		light = self.light[:]
		dark = self.dark[:]

		# Lighten button when hovered over.
		if self.lighter:
			for n in range(3):
				light[n] += .4
				dark[n] += .4
		else:
			for n in range(3):
				light[n] -= .4
				dark[n] -= .4
		light[3] += 0.3
		dark[3] += 0.3
		self.frame.colors = [dark, dark, light, light]

	def _handle_left_active(self, pos):
		light = self.light[:]
		dark = self.dark[:]

		# Darken button when clicked.
		if self.lighter:
			for n in range(3):
				light[n] -= .2
				dark[n] -= .2
		else:
			for n in range(3):
				light[n] += .2
				dark[n] += .2
		light[3] += 0.3
		dark[3] += 0.3
		self.frame.colors = [light, light, dark, dark]


	def _draw(self):
		"""Draw the button"""
		if  (self._position[0] > 2560 or self._position[0] < -200) or (self._position[1] > 1440 or self._position[1] < -200):
			return

		# Draw the children before drawing an additional outline
		Widget._draw(self)

		def mix(a,b,factor):
			"""mix two number together using a factor"""
			return [a[0]*factor + b[0]*(1.0-factor), a[1]*factor + b[1]*(1.0-factor), a[2]*factor + b[2]*(1.0-factor), a[3]*factor + b[3]*(1.0-factor)]

		# Reset the button's color slowly
		newLight = mix(self.dark, self.frame.colors[2], 0.5)
		newDark = mix(self.light, self.frame.colors[1], 0.5)
		self.frame.colors = [newLight, newLight, newDark, newDark]
