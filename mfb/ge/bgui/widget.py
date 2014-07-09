"""

This module defines the following constants:

*Widget options*
  * BGUI_NONE = 0
  * BGUI_CENTERX = 1
  * BGUI_CENTERY = 2
  * BGUI_NORMALIZED = 4
  * BGUI_THEMED = 8
  * BGUI_NO_FOCUS = 16
  * BGUI_CACHE = 32
  * BGUI_LEFT = 64
  * BGUI_RIGHT = 128
  * BGUI_TOP = 256
  * BGUI_BOTTOM = 512
  * BGUI_FILLX = 1024
  * BGUI_FILLY = 2048
  * BGUI_MOVABLE = 4096

  * BGUI_CENTERED = BGUI_CENTERX | BGUI_CENTERY
  * BGUI_FILLED = BGUI_FILLX | BGUI_FILLY

*Widget overflow*
  * BGUI_OVERFLOW_NONE = 0
  * BGUI_OVERFLOW_HIDDEN = 1
  * BGUI_OVERFLOW_REPLACE = 2
  * BGUI_OVERFLOW_CALLBACK = 3

*Mouse event states*
  * BGUI_MOUSE_NONE = 0
  * BGUI_MOUSE_LEFT_CLICK = 1
  * BGUI_MOUSE_RIGHT_CLICK = 2
  * BGUI_MOUSE_LEFT_RELEASE = 4
  * BGUI_MOUSE_RIGHT_RELEASE = 8
  * BGUI_MOUSE_LEFT_ACTIVE = 16
  * BGUI_MOUSE_RIGHT_ACTIVE = 32
  * BGUI_MOUSE_WHEEL_UP = 64
  * BGUI_MOUSE_WHEEL_DOWN = 128

.. note::

	The Widget class should not be used directly in a gui, but should instead
	be subclassed to create other widgets.

"""

from .key_defs import *
from collections import OrderedDict
import weakref
import time
from bge import logic

# Widget options
BGUI_NONE = 0
BGUI_CENTERX = 1
BGUI_CENTERY = 2
BGUI_NORMALIZED = 4
BGUI_THEMED = 8 		# deprecated. Theme is always implied
BGUI_NO_FOCUS = 16
BGUI_CACHE = 32
BGUI_LEFT = 64
BGUI_RIGHT = 128
BGUI_TOP = 256
BGUI_BOTTOM = 512
BGUI_FILLX = 1024
BGUI_FILLY = 2048
BGUI_MOVABLE = 4096

BGUI_CENTERED = BGUI_CENTERX | BGUI_CENTERY
BGUI_FILLED = BGUI_FILLX | BGUI_FILLY

# Widget overflow
BGUI_OVERFLOW_NONE = 0
BGUI_OVERFLOW_HIDDEN = 1
BGUI_OVERFLOW_REPLACE = 2
BGUI_OVERFLOW_CALLBACK = 3

# Mouse event states
BGUI_MOUSE_NONE = 0
BGUI_MOUSE_LEFT_CLICK = 1
BGUI_MOUSE_RIGHT_CLICK = 2
BGUI_MOUSE_LEFT_RELEASE = 4
BGUI_MOUSE_RIGHT_RELEASE = 8
BGUI_MOUSE_LEFT_ACTIVE = 16
BGUI_MOUSE_RIGHT_ACTIVE = 32
BGUI_MOUSE_WHEEL_UP = 64
BGUI_MOUSE_WHEEL_DOWN = 128

class WeakMethod:
	def __init__(self, f):
		if hasattr(f, "__func__"):
			self.f = f.__func__
			self.c = weakref.ref(f.__self__)
		else:
			self.f = f
			self.c = None

	def __call__(self, *args):
		if self.c == None:
			self.f(*args)
		elif self.c() == None:
			return None
		else:
			self.f(*((self.c(),)+args))

class Animation:
	def __init__(self, widget, newpos, time_, callback):
		self.widget = widget
		self.prevpos = widget.position[:]
		if widget.options & BGUI_NORMALIZED:
			self.prevpos[0] /= widget.parent.size[0]
			self.prevpos[1] /= widget.parent.size[1]
		self.newpos = newpos
		self.start_time = self.last_update = time.time()
		self.time = time_
		self.callback = callback

	def update(self):
		if (time.time()-self.start_time)*1000 >= self.time:
			# We're done, run the callback and
			# return false to let widget know we can be removed
			# force animation to lock in new position
			self.widget.position = self.newpos[:]
			if self.callback: self.callback()
			return False

		dt = (time.time() - self.last_update)*1000
		self.last_update = time.time()


		dx = ((self.newpos[0] - (self.prevpos[0] - self.widget.parent.position[0]))/self.time)*dt
		dy = ((self.newpos[1] - (self.prevpos[1] - self.widget.parent.position[1]))/self.time)*dt

		p = self.widget.position

		if self.widget.options & BGUI_NORMALIZED:
			p[0] /= self.widget.parent.size[0]
			p[1] /= self.widget.parent.size[1]

		p[0] += dx
		p[1] += dy

		p[0] -= self.widget.parent.position[0]
		p[1] -= self.widget.parent.position[1]

		self.widget.position = p
		return True



class Widget:
	"""The base widget class"""

	theme_section = 'Widget'
	theme_options = {}

	def __repr__(self):
		return self.__module__

	def __init__(self, parent, name, size=[0, 0], pos=[0, 0], offset=[0,0], sub_theme='',
			options=BGUI_NONE):
		"""
		:param parent: the widget's parent
		:param name: the name of the widget
		:param size: a tuple containing the width and height
		:param pos: a tuple containing the x and y position
		:param sub_theme: name of a sub_theme defined in the theme file (similar to CSS classes)
		:param options: various other options

		"""

		self._name = name
		self.options = options

		# Store the system so children can access theming data
		self.system = parent.system

		if sub_theme:
			self.theme_section += ':'+sub_theme

		self._generate_theme()

		self._hover = False
		self._frozen = False

		if self.options & BGUI_NO_FOCUS:
			self._frozen = True

		# The widget is visible by default
		self._visible = True

		# Event callbacks
		self._on_left_click = None
		self._on_right_click = None
		self._on_left_release = None
		self._on_right_release = None
		self._on_hover = None
		self._on_left_active = None
		self._on_right_active = None
		self._on_mouse_wheel_up = None
		self._on_mouse_wheel_down = None
		self._on_mouse_enter = None
		self._on_mouse_exit = None

		# helper text for widget
		self._tooltip = ""

		# helps with layout positioning
		self._offset = offset
		self._offsetTarget = offset

		# Setup the parent
		parent._attach_widget(self)
		self._parent = weakref.proxy(parent)

		# A dictionary to store children widgets
		self._children = OrderedDict()

		# The z-index of the widget, determines drawing order
		self._z_index = 100

		# Setup the widget's position
		self._position = [None]*4
		self._update_position(size, pos)

		# A list of running animations
		self.anims = []

		# used to store the position delta between the mouse and the widget, for moving
		self._mouseWidgetDelta = []

		self.extraPadding = [0,0,0,0]

	def __del__(self):
		"""Deletes the widget"""
		self._cleanup()


	def	kill(self):
		"""Removes self from the drawing hierachy"""
		c = self.children.copy()

		# remove parent recursively
		for key, child in self.children.items():
			returnedChildren = child.kill()
			c = dict(list(c.items()) + list(returnedChildren.items()))

		# remove self from parent
		self.parent._remove_widget(self)

		return c



	def _generate_theme(self):
		if isinstance(self.theme_options, set):
			if self.system.theme:
				self.system.theme.warn_legacy(self.theme_section)
			if not hasattr(self, "theme"):
				self.theme = None
		else:
			theme = self.system.theme
			theme = theme[self.theme_section] if theme.has_section(self.theme_section) else None

			if theme:
				self.theme = {}

				for k, v in self.theme_options.items():
					if k in theme:
						self.theme[k] = theme[k]
					else:
						self.theme[k] = v
			elif not hasattr(self, "theme"):
				self.theme = self.theme_options

	def _cleanup(self):
		"""Override this if needed"""
		for child in self.children:
			self.children[child]._cleanup()

	def _update_position(self, size=None, pos=None):
		if size is not None:
			self._base_size = size[:]
		else:
			size = self._base_size[:]
		if pos is not None:
			self._base_pos = pos[:]
		else:
			pos = self._base_pos[:]

		# normalize vars
		if self.options & BGUI_NORMALIZED:
			pos[0] *= self.parent.size[0]
			pos[1] *= self.parent.size[1]

			size[0] *= self.parent.size[0]
			size[1] *= self.parent.size[1]

		# Make aliase for animating offsets
		a = self._offset
		b = self._offsetTarget
		factor = 0.5

		if len(self._offset) == 4:
			# offset contains 4 argument, use offset value for position as well as size (fill-offset)

			# LERP between A and B to animate
			self._offset = [a[0]*factor + b[0]*(1.0-factor), a[1]*factor + b[1]*(1.0-factor), a[2]*factor + b[2]*(1.0-factor), a[3]*factor + b[3]*(1.0-factor)]

			if self.options & BGUI_FILLX:
				size[0] = self.parent.size[0] - self._offset[0] - self._offset[2]

			if self.options & BGUI_FILLY:
				size[1] = self.parent.size[1] - self._offset[1] - self._offset[3]

		elif len(self._offset) == 2:
			# offset contains 2 argument, use offset for position only

			# LERP between A and B to animate
			self._offset = [a[0]*factor + b[0]*(1.0-factor), a[1]*factor + b[1]*(1.0-factor)]

			if self.options & BGUI_FILLX:
				size[0] = self.parent.size[0]

			if self.options & BGUI_FILLY:
				size[1] = self.parent.size[1]

		else:
			print ("Warning: unexpected length for widget.offset")

		# round to int
		self._offset = [int(i) for i in self._offset]

		if self.options & BGUI_CENTERX:
			pos[0] = self.parent.size[0]/2 - size[0]/2

		if self.options & BGUI_CENTERY:
			pos[1] = self.parent.size[1]/2 - size[1]/2

		if self.options & BGUI_LEFT:
			pos[0] = self._offset[0]

		if self.options & BGUI_RIGHT:
			pos[0] = self.parent.size[0] - size[0] + self._offset[0]

		if self.options & BGUI_TOP:
			pos[1] = self.parent.size[1] - size[1] + self._offset[1]

		if self.options & BGUI_BOTTOM:
			pos[1] = self._offset[1]

		if self.parent != self:
			x = pos[0] + self.parent.position[0]
			y = pos[1] + self.parent.position[1]
		else: # A widget should only be its own parent if it's the system...
			x = pos[0]
			y = pos[1]

		width = size[0]
		height = size[1]
		self._size = [width, height]
		self._position = [x, y]

		# OpenGL starts at the bottom left and goes counter clockwise
		self.gl_position = 	[
								[x, y],
								[x+width, y],
								[x+width, y+height],
								[x, y+height]
							]

		# Update any children
		for widget in self.children.values():
			if isinstance(widget, Widget):
				widget._update_position(widget._base_size, widget._base_pos)
			else:
				print('Error: Not a Widget > ', widget)

	@property
	def name(self):
		"""The widget's name"""
		return self._name

	@name.setter
	def name(self, value):
		self._name = value

	@property
	def z_index(self):
		"""The widget's z-index. Widget's with a higher z-index are drawn
		over those that have a lower z-index"""
		return self._z_index

	@z_index.setter
	def z_index(self, value):
		self._z_index = value
		self.parent._children = OrderedDict(sorted(self.parent._children.items(),
		key=lambda item: item[1].z_index))

	@property
	def frozen(self):
		"""Whether or not the widget should accept events"""
		return self._frozen

	@frozen.setter
	def frozen(self, value):
		self._frozen = value

	@property
	def visible(self):
		"""Whether or not the widget is visible"""
		return self._visible

	@visible.setter
	def visible(self, value):
		self._visible = value

	@property
	def offset(self):
		return self._offsetTarget

	@offset.setter
	def offset(self, value):
		self._offset = value
		self._offsetTarget = value

	@property
	def tooltip(self):
		return self._tooltip

	@tooltip.setter
	def tooltip(self, value):
		self._tooltip = value

	@property
	def on_left_click(self):
		"""The widget's on_left_click callback"""
		return self._on_left_click

	@on_left_click.setter
	def on_left_click(self, value):
		"""Set the value for on_left_click"""
		self._on_left_click = WeakMethod(value)

	@property
	def on_right_click(self):
		"""The widget's on_right_click callback"""
		return self._on_right_click

	@on_right_click.setter
	def on_right_click(self, value):
		"""Set the value for on_right_click"""
		self._on_right_click = WeakMethod(value)

	@property
	def on_left_release(self):
		"""The widget's on_left_release callback"""
		return self._on_left_release

	@on_left_release.setter
	def on_left_release(self, value):
		self._on_left_release = WeakMethod(value)

	@property
	def on_right_release(self):
		"""The widget's on_right_release callback"""
		return self._on_right_release

	@on_right_release.setter
	def on_right_release(self, value):
		self._on_right_release = WeakMethod(value)

	@property
	def on_left_active(self):
		"""The widget's on_left_active callback"""
		return self._on_left_active

	@on_left_active.setter
	def on_left_active(self, value):
		self._on_left_active = WeakMethod(value)

	@property
	def on_right_active(self):
		"""The widget's on_right_active callback"""
		return self._on_right_active

	@on_right_active.setter
	def on_right_active(self, value):
		self._on_right_active = WeakMethod(value)

	@property
	def on_hover(self):
		"""The widget's on_hover callback"""
		return self._on_hover

	@on_hover.setter
	def on_hover(self, value):
		self._on_hover = WeakMethod(value)

	@property
	def on_mouse_enter(self):
		"""The widget's on_mouse_enter callback"""
		return self._on_mouse_enter

	@on_mouse_enter.setter
	def on_mouse_enter(self, value):
		self._on_mouse_enter = WeakMethod(value)

	@property
	def on_mouse_exit(self):
		"""The widget's on_mouse_exit callback"""
		return self._on_mouse_exit

	@on_mouse_exit.setter
	def on_mouse_exit(self, value):
		self._on_mouse_exit = WeakMethod(value)

	@property
	def on_mouse_wheel_up(self):
		"""The widget's on_mouse_wheel_up callback"""
		return self._on_mouse_wheel_up

	@on_mouse_wheel_up.setter
	def on_mouse_wheel_up(self,value):
		self._on_mouse_wheel_up = WeakMethod(value)

	@property
	def on_mouse_wheel_down(self):
		"""The widget's on_mouse_wheel_down callback"""
		return self._on_mouse_wheel_down

	@on_mouse_wheel_down.setter
	def on_mouse_wheel_down(self,value):
		self._on_mouse_wheel_down = WeakMethod(value)

	@property
	def parent(self):
		"""The widget's parent"""
		return self._parent

	@parent.setter
	def parent(self, value):
		self._parent = value
		self._update_position(self._base_size, self._base_value)

	@property
	def children(self):
		"""The widget's children"""
		return self._children

	@property
	def position(self):
		"""The widget's position"""
		return self._position

	@position.setter
	def position(self, value):
		self._update_position(self._base_size, value)

	@property
	def size(self):
		"""The widget's size"""
		return self._size

	@size.setter
	def size(self, value):
		self._update_position(value, self._base_pos)

	def move(self, position, time, callback=None):
		"""Move a widget to a new position over a number of frames

		:param positon: The new position
		:param time: The time in milliseconds to take doing the move
		:param callback: An optional callback that is called when he animation is complete
		"""
		self.anims.append(Animation(self, position, time, callback))

	def _update_anims(self):
		self.anims[:] = [i for i in self.anims if i.update()]

		for widget in self.children.values():
			widget._update_anims()

	def _handle_mouse(self, pos, event):
		"""Run any event callbacks"""
		# used to keep track of if a child widget has already been handled
		# implying the parent shouldn't handle it again
		handled = False

		if logic.moving or logic.rotating:
			return
			
		# Run any children callback methods
		for widget in self.children.values():
			if (widget.gl_position[0][0]-widget.extraPadding[0] <= pos[0] <= widget.gl_position[1][0]+widget.extraPadding[1]) and \
				(widget.gl_position[0][1]-widget.extraPadding[2] <= pos[1] <= widget.gl_position[2][1]+widget.extraPadding[3]):
					handled = widget._handle_mouse(pos, event)
					# lock ui
					if widget.visible and not widget.frozen:
						logic.mouseLock = 3
			else:
				widget._update_hover(False)

		# Don't run if we're not visible or frozen
		if (not self.visible) or self.frozen: return handled

		# special case: mouse wheel should always be regardless of children status handled
		if event == BGUI_MOUSE_WHEEL_UP:
			if not self.on_mouse_wheel_up:
			 	self._handle_wheel_up()
			 	return True
					
		elif event == BGUI_MOUSE_WHEEL_DOWN:
			if not self.on_mouse_wheel_down:
			  	self._handle_wheel_down()

		#don't run if mouse was already handled by a child
		if handled:
			#pass along the message that the mouse had been handled
			return True
		# Being the 'youngest' child, we should now handle the mouse
		else:
			if event == BGUI_MOUSE_WHEEL_UP:
				self._handle_wheel_up()
				if self.on_mouse_wheel_up:
					self.on_mouse_wheel_up(self)
			elif event == BGUI_MOUSE_WHEEL_DOWN:
				self._handle_wheel_down()
				if self.on_mouse_wheel_down:
					self.on_mouse_wheel_down(self)

			self._handle_hover(pos)
			if self.tooltip:
				if self.visible: self.system.showToolTip(self)

			if self.on_hover:
				self.on_hover(self)

			if event == BGUI_MOUSE_LEFT_CLICK:
				self._handle_left_click(pos)
				if self.tooltip:
					self.system.hideToolTip(self)
				if self.on_left_click:
					self.on_left_click(self)
			elif event == BGUI_MOUSE_RIGHT_CLICK:
				self._handle_right_click(pos)
				if self.tooltip:
					self.system.hideToolTip(self)
				if self.on_right_click:
					self.on_right_click(self)
			elif event == BGUI_MOUSE_LEFT_RELEASE:
				self._handle_left_release(pos)
				if self.on_left_release:
					self.on_left_release(self)
			elif event == BGUI_MOUSE_RIGHT_RELEASE:
				self._handle_right_release(pos)
				if self.on_right_release:
					self.on_right_release(self)
			elif event == BGUI_MOUSE_LEFT_ACTIVE:
				self._handle_left_active(pos)
				if self.on_left_active:
					self.on_left_active(self)
			elif event == BGUI_MOUSE_RIGHT_ACTIVE:
				self._handle_right_active(pos)
				if self.on_right_active:
					self.on_right_active(self)
			elif event == BGUI_MOUSE_WHEEL_UP:
				self._handle_wheel_up()
				if self.on_mouse_wheel_up:
					self.on_mouse_wheel_up(self)
			elif event == BGUI_MOUSE_WHEEL_DOWN:
				self._handle_wheel_down()
				if self.on_mouse_wheel_down:
					self.on_mouse_wheel_down(self)

			# Update focus
			if (event == BGUI_MOUSE_LEFT_CLICK or event == BGUI_MOUSE_RIGHT_CLICK) and not (self.system.lock_focus) and not self.options & BGUI_NO_FOCUS:
				self.system.focused_widget = self

			if not self._hover:
				self._handle_mouse_enter()
				if self.on_mouse_enter:
					self.on_mouse_enter(self)
			self._hover = True

			#signal that the mouse has been handled)
			return True

	def _update_hover(self, hover=False):
		if not hover and self._hover:
			self._handle_mouse_exit()
			if self.tooltip:
				self.system.hideToolTip(self)
			if self.on_mouse_exit:
				self.on_mouse_exit(self)
		self._hover = hover

		for widget in self.children.values():
			widget._update_hover(hover)

	def _handle_key(self, key, is_shifted, is_ctrled):
		"""Handle any keyboard input"""
		# Don't run if we're not visible or frozen
		if not self.visible or self.frozen: return

		for widget in self.children.values():
			#if self._hover:
			widget._handle_key(key, is_shifted, is_ctrled)

	# These exist so they can be overridden by subclasses
	def _handle_left_click(self, pos):
		# init left drag
		if self.options & BGUI_MOVABLE:
			self._mouseWidgetDelta = [pos[0]-self._position[0], pos[1]-self._position[1]]

	def _handle_right_click(self, pos):
		pass
	def _handle_left_release(self, pos):
		# finish dragging
		if self.options & BGUI_MOVABLE and self._mouseWidgetDelta:
			self._mouseWidgetDelta = []
	def _handle_right_release(self, pos):
		pass
	def _handle_hover(self, pos):
		pass
	def _handle_left_active(self, pos):
		pass
	def _handle_right_active(self, pos):
		pass
	def _handle_mouse_enter(self):
		pass
	def _handle_mouse_exit(self):
		pass
	def _handle_wheel_up(self):
		pass
	def _handle_wheel_down(self):
		pass

	def _attach_widget(self, widget):
		"""Attaches a widget to this widget"""

		if not isinstance(widget, Widget):
			raise TypeError("Expected a Widget object")

		if widget in self.children:
			raise ValueError("%s is already attached to this widget" % (widget.name))

		self.children[widget.name] = widget

	def _remove_widget(self, widget):
		"""Removes the widget from this widget's children"""

		del self.children[widget.name]

	def _draw(self):
		"""Draws the widget and the widget's children"""

		# This base class has nothing to draw, so just draw the children
		for child in self.children:
			if self.children[child].visible:
				self.children[child]._draw()

		# handles dragging
		if self.options & BGUI_MOVABLE and self._mouseWidgetDelta:
			pos = self.system.mousePos
			self.position = [pos[0] - self._mouseWidgetDelta[0], pos[1] - self._mouseWidgetDelta[1]]
