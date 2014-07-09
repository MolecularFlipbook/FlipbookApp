from . import bgui
from .settings import *

from bge import logic
from bgl import *

import os, subprocess, math, cProfile

# aliases
inputInactive = logic.KX_SENSOR_INACTIVE
inputActivated = logic.KX_SENSOR_JUST_ACTIVATED
inputActive = logic.KX_SENSOR_ACTIVE
inputDeactivated = logic.KX_SENSOR_JUST_DEACTIVATED
pi = 3.1415926


def profile(cmd, g, l):
	cProfile.runctx(cmd, g, l, sort=1)

def smoothstep(x):
	'''returns a smoothed float given an input between 0 and 1'''
	return x * x * (3-2*(x))

def computeFlatS(period, b, time, offset=1):
	"""compute the position of the object based on time using this curve:
	http://www.wolframalpha.com/input/?i=y%3D%281%2F%281%2Be%5E%28-10-x%29%29+%2B+1%2F%281%2Be%5E%2810-x%29%29%29"""
	time = (time%period)+offset
	time = (time-period/2)*(20/period)
	x = 1/(1+math.e**(-b-time))+1/(1+math.e**(b-time))
	x /= 2.0
	x += offset/10
	return x

def mix(a,b,factor):
	'''mix two number together using a factor'''
	if type(a) is list or type(a) is tuple:
		if len(a)==len(b)==2:
			return [a[0]*factor + b[0]*(1.0-factor), a[1]*factor + b[1]*(1.0-factor)]
		elif len(a)==len(b)==3:
			return [a[0]*factor + b[0]*(1.0-factor), a[1]*factor + b[1]*(1.0-factor), a[2]*factor + b[2]*(1.0-factor)]
		elif len(a)==len(b)==4:
			return [a[0]*factor + b[0]*(1.0-factor), a[1]*factor + b[1]*(1.0-factor), a[2]*factor + b[2]*(1.0-factor), a[3]*factor + b[3]*(1.0-factor)]
		else:
			raise Exception(ArithmeticError)
	else:
		return (a*factor + b*(1.0-factor))


def drawLine(x1,y1,x2,y2, rgba):
	''' draw a line in screen space'''
	glEnable(GL_BLEND)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

	# Draw an outline
	r, g, b, a = rgba
	glColor4f(r, g, b, a)
	glPolygonMode(GL_FRONT, GL_LINE)
	glLineWidth(1.0)

	glBegin(GL_LINES)
	glVertex2i(x1, y1)
	glVertex2i(x2, y2)
	glEnd()

	glLineWidth(1.0)
	glPolygonMode(GL_FRONT, GL_FILL)
	glDisable(GL_BLEND)

def createBusyBar(container, size, pos):
	container.systemBusyBar = bgui.Frame(container.panel, 'systemBusyBar', size=size, pos=pos, sub_theme="invisible")
	container.busyDot1 = bgui.Label(container.systemBusyBar, 'dot1', text=".", pos=[0, 0], sub_theme='busyAnts', options=bgui.BGUI_NORMALIZED|bgui.BGUI_CENTERY)
	container.busyDot2 = bgui.Label(container.systemBusyBar, 'dot2', text=".", pos=[0, 0], sub_theme='busyAnts', options=bgui.BGUI_NORMALIZED|bgui.BGUI_CENTERY)
	container.busyDot3 = bgui.Label(container.systemBusyBar, 'dot3', text=".", pos=[0, 0], sub_theme='busyAnts', options=bgui.BGUI_NORMALIZED|bgui.BGUI_CENTERY)
	container.busyDot4 = bgui.Label(container.systemBusyBar, 'dot4', text=".", pos=[0, 0], sub_theme='busyAnts', options=bgui.BGUI_NORMALIZED|bgui.BGUI_CENTERY)
	container.busyDot5 = bgui.Label(container.systemBusyBar, 'dot5', text=".", pos=[0, 0], sub_theme='busyAnts', options=bgui.BGUI_NORMALIZED|bgui.BGUI_CENTERY)



def updateBusyBar(container, time):
	'''update a Windows 8 style progress bar'''
	color = [1,1,1,0]
	if not time:
		container.busyDot1.color = color
		container.busyDot2.color = color
		container.busyDot3.color = color
		container.busyDot4.color = color
		container.busyDot5.color = color

		container.busyDot1.position = [0.5, 0.5]
		container.busyDot2.position = [0.5, 0.5]
		container.busyDot3.position = [0.5, 0.5]
		container.busyDot4.position = [0.5, 0.5]
		container.busyDot5.position = [0.5, 0.5]
		return


	period = 3.0				# speed of animation, smaller number is faster
	b = 5						# flatness of curve
								# opacity computation
	opacity = (1-abs(computeFlatS(period, 5, time) - 0.5)*2.0) + 0.2
	color = [1,1,1,opacity]

	xPos = computeFlatS(period, b, time, -0.2)
	container.busyDot1.position = [xPos, 0.5]
	container.busyDot1.color = color

	xPos = computeFlatS(period, b, time, -0.1)
	container.busyDot2.position = [xPos, 0.5]
	container.busyDot2.color = color

	xPos = computeFlatS(period, b, time, 0)
	container.busyDot3.position = [xPos, 0.5]
	container.busyDot3.color = color

	xPos = computeFlatS(period, b, time, 0.1)
	container.busyDot4.position = [xPos, 0.5]
	container.busyDot4.color = color

	xPos = computeFlatS(period, b, time, 0.2)
	container.busyDot5.position = [xPos, 0.5]
	container.busyDot5.color = color



def guiKill(widget):
	"""remove widgets completely"""
	try:
		children = widget.kill()
		for key, child in children.items():
			try:
				exec ("del logic.gui.%s" %key)
			except Exception as E:
				pass
		exec ("del logic.gui.%s" %widget.name)
	except:
		pass

def themeRoot(filename=""):
	if not filename:
		return os.path.join(logic.basePath, "ge", "themes")
	else:
		return os.path.join(logic.basePath, "ge", "themes", filename)

def createPath(path):
	'''takes a full path, and make sure it's there and accessible'''
	if os.path.isdir(path):
		return True
	else:
		try:
			os.makedirs(path)
		except:
			return False
		else:
			return True

def activeContext(*regions):
	'''check to see if the focused widget is part of a 'region' '''
	focused = logic.gui.focused_widget
	if not focused:
		return False
	for region in regions:
		# match logic.gui
		if region == logic.gui and focused == logic.gui.system:
			return True
		# match all other regions, ignore system
		for key, item in region.__dict__.items():
			if (item is focused) and ('ystem' not in item.name):
				return True
	return False


def openPath(path):
	if 'win' in releaseOS:
		os.system("explorer " + path)
	elif 'mac' in releaseOS:
		os.system("open -- " + path)