from .widget import *
from .image import *
from .frame import *
from .label import *

class ImageButton(Widget):
	"""A clickable image-based button."""

	theme_section = 'ImageButton'
	theme_options = {'DefaultImage': (None, 0, 0, 1, 1),
					 'Default2Image': (None, 0, 0, 1, 1),
					 'HoverImage': (None, 0, 0, 1, 1),
					 'Hover2Image': (None, 0, 0, 1, 1),
					 'ClickImage': (None, 0, 0, 1, 1),
					 'LabelSubTheme': '',
					 }

	def __init__(self, parent, name, default_image=None, default2_image=None, hover_image=None, hover2_image=None,
					click_image=None, text="", size=[1,1], pos=[0,0],offset=[0,0], sub_theme='',
					options=BGUI_NONE):
		"""
		:param parent: the widget's parent
		:param name: the name of the widget
		:param default_image: list containing image data for the default state ('image', xcoord, ycoord, xsize, ysize)
		:param default2_image: list containing image data for a second default state, which is used for toggling ('image', xcoord, ycoord, xsize, ysize)
		:param hover_image: list containing image data for the hover state ('image', xcoord, ycoord, xsize, ysize)
		:param click_image: list containing image data for the click state ('image', xcoord, ycoord, xsize, ysize)
		:param size: a tuple containing the width and height
		:param pos: a tuple containing the x and y position
		:param sub_theme: name of a sub_theme defined in the theme file (similar to CSS classes)
		:param options: various other options
		"""

		Widget.__init__(self, parent, name, size, pos, offset, sub_theme, options)

		self.label = Label(self, name + '_label', text,  sub_theme=self.theme['LabelSubTheme'], options=BGUI_NO_FOCUS | BGUI_NORMALIZED | BGUI_CENTERED)

		if default_image:
			self.default_image = default_image
		else:
			self.default_image = self.theme['DefaultImage']

		if default2_image:
			self.default2_image = default2_image
		else:
			self.default2_image = self.theme['Default2Image']

		if hover_image:
			self.hover_image = hover_image
		else:
			self.hover_image = self.theme['HoverImage']

		if hover2_image:
			self.hover2_image = hover2_image
		else:
			self.hover2_image = self.theme['Hover2Image']

		if click_image:
			self.click_image = click_image
		else:
			self.click_image = self.theme['ClickImage']

		if self.default_image[0]:
			coords = self._get_coords(self.default_image)
			self.image = Image(self, name+'_img', self.default_image[0],
								texco=coords, size=[1,1], pos=[0,0], options=BGUI_NORMALIZED|BGUI_NO_FOCUS|BGUI_CACHE)
		else:
			self.image = Frame(self, name+'_img', size=[1,1], pos=[0, 0])

		self._state = 0

		self.noHover = False

	def _get_coords(self, image):
		v = image[1:]
		return [(v[0], v[1]), (v[0]+v[2], v[1]), (v[0]+v[2], v[1]+v[3]), (v[0], v[1]+v[3])]

	def _update_image(self, image):
		if image[0]:
			self.image.texco = self._get_coords(image)
			self.image.update_image(image[0])

	def _get_default_image(self):
		if self.state == 1 and self.default_image[0]:
			return self.default2_image

		return self.default_image

	def _handle_left_click(self, pos):
		self._state = not self._state

	def _handle_left_release(self, pos):
		self._update_image(self._get_default_image())

	def _handle_left_active(self, pos):
		self._update_image(self.click_image)

	def _handle_hover(self, pos):
		if self.noHover:
			return

		if self._state:
			self._update_image(self.hover2_image)
		else:
			self._update_image(self.hover_image)

	def _handle_mouse_exit(self):
		self._update_image(self._get_default_image())


	@property
	def state(self):
		return self._state

	@state.setter
	def state(self, value):
		self._state = value
		self._update_image(self._get_default_image())


	@property
	def text(self):
		return self.label.text

	@text.setter
	def text(self, value):
		self.label.text = value


	def _draw(self):
		Widget._draw(self)

