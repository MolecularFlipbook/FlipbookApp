from bgl import *

from .widget import *
from .frame import *
from .label import *

class Checkbox(Widget):
	"""A clickable checkbox based on frame button."""
	theme_section = 'Checkbox'
	theme_options = {'Color': (0.4,0.4,0.4,1),
					'Color2': (1, 1, 1, 1),
					 'BorderSize': 1,
					 'BorderColor': (0, 0, 0, 1),
					 'LabelSubTheme': '',
				}

	def __init__(self, parent, name, state=False, text="", font=None,
					pt_size=None, small=False, size=[0,0], pos=[0,0], offset=[0,0], sub_theme='', options=BGUI_NONE):
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

		if small:
			self.frame = Frame(self, name + '_frame', size=[10,10], pos=[0,0], padding = 1, options=BGUI_NO_FOCUS)
			self.label = Label(self, name + '_label', text, font, pt_size, pos=[20,0], sub_theme=self.theme['LabelSubTheme'], options=BGUI_NO_FOCUS)
		else:
			self.frame = Frame(self, name + '_frame', size=[20,20], pos=[0,0], padding = 2, options=BGUI_NO_FOCUS)
			self.label = Label(self, name + '_label', text, font, pt_size, pos=[28,6], sub_theme=self.theme['LabelSubTheme'], options=BGUI_NO_FOCUS)
			# self.labelTick = Label(self, name + '_labelTick', "√", font, pt_size=20, pos=[5,4], color=[1.0,1.0,1.0,1.0], options=BGUI_NO_FOCUS)


		base_color = self.theme['Color']
		base_color2 = self.theme['Color2']
		self.base_color = base_color
		self.base_color2 = base_color2
		self.frame.border = self.theme['BorderSize']
		self.frame.border_color = self.theme['BorderColor']

		self._boolState = state
		self.small = small

		if state:
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
			# if not self.small: self.labelTick.visible = True

		else:
			self.light = [
				self.base_color2[0] + 0.1,
				self.base_color2[1] + 0.1,
				self.base_color2[2] + 0.1,
				self.base_color2[3]]
			self.dark = [
				self.base_color2[0],
				self.base_color2[1],
				self.base_color2[2],
				self.base_color2[3]]
			self.frame.colors = [self.dark, self.dark, self.light, self.light]
			# if not self.small: self.labelTick.visible = False

	@property
	def text(self):
		return self.label.text

	@text.setter
	def text(self, value):
		self.label.text = value

	@property
	def color(self):
		return self.base_color

	@property
	def state(self):
		return self._boolState

	@state.setter
	def state(self, value):
		if value:
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
			# if not self.small: self.labelTick.visible = True

		else:
			self.light = [
				self.base_color2[0] + 0.1,
				self.base_color2[1] + 0.1,
				self.base_color2[2] + 0.1,
				self.base_color2[3]]
			self.dark = [
				self.base_color2[0],
				self.base_color2[1],
				self.base_color2[2],
				self.base_color2[3]]
			self.frame.colors = [self.dark, self.dark, self.light, self.light]
			# if not self.small: self.labelTick.visible = False

		self._boolState = value

	def _handle_hover(self, pos):
		light = self.light[:]
		dark = self.dark[:]

		# Lighten button when hovered over.
		for n in range(3):
			light[n] += .1
			dark[n] += .1
		self.frame.colors = [dark, dark, light, light]

	def _handle_left_release(self, pos):
		self.state = not self.state

	def _handle_right_release(self, pos):
		self.state = not self.state

	def _draw(self):
		"""Draw the button"""

		# Draw the children before drawing an additional outline
		Widget._draw(self)

		# Reset the button's color
		self.frame.colors = [self.dark, self.dark, self.light, self.light]
