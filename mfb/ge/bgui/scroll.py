from bgl import *
from .widget import *


class Scroll(Widget):
	"""Scrollable Frame for storing other widgets"""
	theme_section = 'Scroll'
	theme_options = {}

	def __init__(self, parent, name, border=None, size=[1,1], actual=[1,1], pos=[0, 0], offset=[0,0], scroll=[0,1],
				sub_theme='', options=BGUI_NONE):
		"""
		:param parent: the widget's parent
		:param name: the name of the widget
		:param border: the size of the border around the frame (0 for no border)
		:param size: the clipped size of the vieable scroll region
		:param actual: a tuple containing the width and height of the entire usable area
		:param pos: a tuple containing the x and y position
		:param scroll: a tuple containing the percentage of the scrolling, relative to actual canvas size
		:param sub_theme: name of a sub_theme defined in the theme file (similar to CSS classes)
		:param options: various other options

		"""
		Widget.__init__(self, parent, name, size, pos, offset, sub_theme, options)

		if options & BGUI_NO_FOCUS:
			self._interactive = False
		else:
			self._interactive = True

		self._actual = actual
		self._scroll = scroll
		self._desiredScroll = [0,1]
		self._barScrolling = False
		self._mousePos = [0,0]
		self._locked = False
		self.barWidth = 5

	@property
	def locked(self):
	    return self._locked
	
	@locked.setter
	def locked(self, value):
	    self._locked = value
	
	@property
	def actual(self):
		return self._actual

	@actual.setter
	def actual(self, value):
		self._actual = value

	@property
	def scroll(self):
		return self._scroll

	@scroll.setter
	def scroll(self, value):
		x = max(min(value[0],1),0)
		y = max(min(value[1],1),0)
		self._scroll = [x,y]

	@property
	def size(self):
		"""The widget's actual usable size"""
		return [self._size[0]*self._actual[0], self._size[1]*self._actual[1]]

	@property
	def position(self):
		"""The widget's position"""
		return [self._position[0]-self._scroll[0]*(self._actual[0] * self._size[0]-self._size[0]),
				self._position[1]-self._scroll[1]*(self._actual[1] * self._size[1]-self._size[1])]

	def fitY(self, totalSize):
		"""given the size of the content in pixels, fit the scroll area to it"""
		desiredMultiplier = (totalSize/(self.size[1]/self._actual[1]))
		if desiredMultiplier < 1:
			desiredMultiplier = 1
		self._actual[1] = desiredMultiplier

	def fitX(self, totalSize):
		"""given the size of the content in pixels, fit the scroll area to it"""
		desiredMultiplier = (totalSize/(self.size[0]/self._actual[0]))
		if desiredMultiplier < 1:
			desiredMultiplier = 1
		self._actual[0] = desiredMultiplier

	def _handle_wheel_up(self):
		if self.locked:
			self.locked = False
			return
		if self._actual[1] > 1.0:
			self._desiredScroll[1] += (0.4 / self._actual[1])
		else:
			# disables horizontal scroll
			self._desiredScroll[0] -= (0.2 / self._actual[0])
			pass

	def _handle_wheel_down(self):
		if self.locked:
			self.locked = False
			return
		if self._actual[1] > 1.0:
			self._desiredScroll[1] -= (0.4 / self._actual[1])
		else:
			# disables horizontal scroll
			self._desiredScroll[0] += (0.2 / self._actual[0])
			pass

	def _handle_left_click(self, pos):
		"""save the start-draging mouse position"""
		self._mousePos = pos[:]

	def _handle_left_active(self, pos):
		"""compute the amount of movement requires"""
		if self._mousePos:
			if self._barScrolling:
				delta = [pos[0] - self._mousePos[0], pos[1] - self._mousePos[1]]
				canvas = self._size

				x = delta[0] / canvas[0] / self._actual[0]
				y = delta[1] / canvas[1] / self._actual[1]

				self._desiredScroll[0] += x * 6.0
				self._desiredScroll[1] += y * 6.0

				self._mousePos = pos[:]


			else:
				delta = [pos[0] - self._mousePos[0], pos[1] - self._mousePos[1]]
				canvas = self._size

				x = delta[0] / canvas[0] / self._actual[0]
				y = delta[1] / canvas[1] / self._actual[1]

				#self._desiredScroll[0] -= x * 4.0
				self._desiredScroll[1] -= y * 4.0

				self._mousePos = pos[:]


	def _handle_left_release(self, pos):
		self._mousePos = []
		self._barScrolling = False

	def _handle_mouse_exit(self):
		self._mousePos = []
		self._barScrolling = False

	def _handle_hover(self, pos):
		if self._actual[0] > 1.0:	# horizontal scrolling
			if (pos[1] < self._position[1]+20):
				self._barScrolling = True
			elif (pos[1] > self._position[1] + 40):
				self._barScrolling = False
		if self._actual[1] > 1.0:	# vertical scrolling
			if (pos[0] > self._position[0]+self._size[0]-20):
				self._barScrolling = True
			elif (pos[0] < self._position[0]+self._size[0]-40):
				self._barScrolling = False

	def _handle_key(self, key, is_shifted, is_ctrled):
		"""Handle any keyboard input"""
		if self.system.focused_widget == self:
				
			# Try char to int conversion for alphanumeric keys... kinda hacky though
			try:
				key = ord(key)
			except:
				pass

			if key == LEFTARROWKEY:
				self._desiredScroll[0] -= (0.2 / self._actual[0])
			if key == RIGHTARROWKEY:
				self._desiredScroll[0] += (0.2 / self._actual[0])
			if key == UPARROWKEY:
				self._desiredScroll[1] += (0.2 / self._actual[0])
			if key == DOWNARROWKEY:
				self._desiredScroll[1] -= (0.2 / self._actual[0])

		for widget in self.children.values():
			widget._handle_key(key, is_shifted, is_ctrled)

	def _mix(self, a, b, factor):
		"""docstring for _mix"""
		return 	[a[0]*factor + b[0]*(1.0-factor), a[1]*factor + b[1]*(1.0-factor)]

	def _draw(self):
		"""Draw the frame"""

		# iOS rubber band effect
		if self._desiredScroll[0] < 0:
			self._desiredScroll[0] = self._desiredScroll[0] * 0.5
		elif self._desiredScroll[0] > 1:
			self._desiredScroll[0] = self._desiredScroll[0] * 0.5 + 0.5

		if self._desiredScroll[1] < 0:
			self._desiredScroll[1] = self._desiredScroll[1] * 0.5
		elif self._desiredScroll[1] > 1:
			self._desiredScroll[1] = self._desiredScroll[1] * 0.5 + 0.5

		self._scroll = self._mix(self._scroll, self._desiredScroll, 0.6)

		width = int(self.gl_position[2][0] - self.gl_position[0][0])
		height = int(self.gl_position[2][1] - self.gl_position[0][1])
		glScissor(int(self.gl_position[0][0]),int(self.gl_position[0][1]), width, height)
		glEnable(GL_SCISSOR_TEST)
		Widget._draw(self)

		if self._interactive:
			# scrollbar color, width, padding
			rgba = [1,1,1, 0.3]
			borderrgba = [0.8,0.8,0.8,0.1]
			if self._barScrolling:
				if self.barWidth < 10:
					self.barWidth += 1
			else:
				if self.barWidth > 5:
					self.barWidth -= 1

			width = self.barWidth
			spacing = 1

			glEnable(GL_BLEND)
			glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

			# draw v scroll bar
			if self._actual[1] > 1:

				_height = (self.gl_position[2][1] - self.gl_position[1][1])
				scrollBarLength = _height / self._actual[1]
				scrollBarBottom = self._scroll[1] * _height  + self.gl_position[1][1] - scrollBarLength * self._scroll[1] + 2
				scrollBarTop = scrollBarBottom + scrollBarLength - 2

				if self._barScrolling:
					# draw container:
					glBegin(GL_QUADS)
					glColor4f(0,0,0,0.2)
					glVertex2f(self.gl_position[1][0]-width, self.gl_position[2][1])
					glVertex2f(self.gl_position[1][0]-spacing, self.gl_position[2][1])
					glVertex2f(self.gl_position[1][0]-spacing, self.gl_position[1][1])
					glVertex2f(self.gl_position[1][0]-width, self.gl_position[1][1])
					glEnd()

				# draw fill
				glBegin(GL_QUADS)
				glColor4f(*rgba)
				glVertex2f(self.gl_position[1][0]-width, scrollBarBottom)
				glVertex2f(self.gl_position[1][0]-spacing, scrollBarBottom)
				glVertex2f(self.gl_position[1][0]-spacing, scrollBarTop)
				glVertex2f(self.gl_position[1][0]-width, scrollBarTop)
				glEnd()


				# draw outline
				glColor4f(*borderrgba)
				glPolygonMode(GL_FRONT, GL_LINE)
				glLineWidth(2)
				glBegin(GL_QUADS)
				glVertex2f(self.gl_position[1][0]-width, scrollBarBottom)
				glVertex2f(self.gl_position[1][0]-spacing, scrollBarBottom)
				glVertex2f(self.gl_position[1][0]-spacing, scrollBarTop)
				glVertex2f(self.gl_position[1][0]-width, scrollBarTop)
				glEnd()
				glLineWidth(1.0)
				glPolygonMode(GL_FRONT, GL_FILL)

			# draw h scroll bar
			if self._actual[0] > 1:

				_width = (self.gl_position[1][0] - self.gl_position[0][0])
				scrollBarLength = _width / self._actual[0]
				scrollBarLeft = self._scroll[0] * _width  + self.gl_position[0][0] - scrollBarLength * self._scroll[0] + 2
				scrollBarRight = scrollBarLeft + scrollBarLength - 2

				if self._barScrolling:
					# draw container:
					glBegin(GL_QUADS)
					glColor4f(0,0,0,0.2)
					glVertex2f(self.gl_position[1][0], self.gl_position[0][1]+spacing)
					glVertex2f(self.gl_position[0][0], self.gl_position[1][1]+spacing)
					glVertex2f(self.gl_position[0][0], self.gl_position[1][1]+width)
					glVertex2f(self.gl_position[1][0], self.gl_position[0][1]+width)
					glEnd()


				# draw fill
				glBegin(GL_QUADS)
				glColor4f(*rgba)
				glVertex2f(scrollBarLeft, self.gl_position[0][1]+spacing)
				glVertex2f(scrollBarRight, self.gl_position[1][1]+spacing)
				glVertex2f(scrollBarRight, self.gl_position[1][1]+width)
				glVertex2f(scrollBarLeft, self.gl_position[0][1]+width)
				glEnd()

				# draw outline
				glColor4f(*borderrgba)
				glPolygonMode(GL_FRONT, GL_LINE)
				glLineWidth(2)
				glBegin(GL_QUADS)
				glVertex2f(scrollBarLeft, self.gl_position[0][1]+spacing)
				glVertex2f(scrollBarRight, self.gl_position[1][1]+spacing)
				glVertex2f(scrollBarRight, self.gl_position[1][1]+width)
				glVertex2f(scrollBarLeft, self.gl_position[0][1]+width)
				glEnd()
				glLineWidth(1.0)
				glPolygonMode(GL_FRONT, GL_FILL)

			glDisable(GL_BLEND)

		glDisable(GL_SCISSOR_TEST)
