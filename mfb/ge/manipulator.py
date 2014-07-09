# import gamengine modules
from bge import logic
from bge import events
from bge import render

from mathutils import Vector, Matrix, geometry
import time

# import mvb's own modules
from .settings import *
from .helpers import *

def getObjCenter(objs):
	'''get the median world location of a list of objects'''
	if not objs:
		return None

	center = [0, 0, 0]
	for obj in objs:
		objpos = obj.worldPosition
		center[0] += objpos[0]
		center[1] += objpos[1]
		center[2] += objpos[2]

	center[0] /= len(objs)
	center[1] /= len(objs)
	center[2] /= len(objs)

	return center


def setManipulator(objs):
	"""displays the 3d widget"""

	pos = getObjCenter(objs)
	rot = (0,0,0)

	# link obj(s) to pivot
	for obj in logic.pivotObject.children:
			obj.removeParent()

	if logic.mvb.playing or logic.mvb.rendering or logic.options.view == 'EDITOR':
		_hideManipulator()
	else:
		if pos:
			_showManipulator(objs, pos, rot)
		else:
			_hideManipulator()


def highlightManipulator(target):
	''' animate widget '''
	if not target:
		return

	hiddenSize = 0.999

	if target.name == 'x':
		logic.scene.objects['x.render'].playAction('ScalingRipple', 0, 20, play_mode=1)
		logic.scene.objects['rx.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['ry.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['rz.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['z.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['y.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
	elif target.name == 'y':
		logic.scene.objects['y.render'].playAction('ScalingRipple', 0, 20, play_mode=1)
		logic.scene.objects['rx.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['ry.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['rz.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['z.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['x.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
	elif target.name == 'z':
		logic.scene.objects['z.render'].playAction('ScalingRipple', 0, 20, play_mode=1)
		logic.scene.objects['rx.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['ry.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['rz.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['x.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['y.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
	elif target.name == 'rz':
		logic.scene.objects['rz.render'].playAction('ScalingRipple2', 0, 20, play_mode=1)
		logic.scene.objects['ry.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['rx.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['x.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['y.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['z.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
	elif target.name == 'ry':
		logic.scene.objects['ry.render'].playAction('ScalingRipple2', 0, 20, play_mode=1)
		logic.scene.objects['rz.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['rx.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['x.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['y.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['z.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
	elif target.name == 'rx':
		logic.scene.objects['rx.render'].playAction('ScalingRipple2', 0, 20, play_mode=1)
		logic.scene.objects['ry.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['rz.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['x.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['y.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['z.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
	# highlight rotation thingy
	elif target.name == "rotate":
		logic.scene.objects['rotateGlow'].localScale = True
	elif target.name == 'widget':
		logic.scene.objects['rx.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['ry.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['rz.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['z.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['y.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)
		logic.scene.objects['x.render'].localScale = (hiddenSize, hiddenSize, hiddenSize)

	# stop all other animations
	for widget in logic.widgetRenderList:
		if target.name+".render" != widget:
			logic.scene.objects[widget].stopAction()


def unHighlightManipulator():
	''' stop animating widget'''
	for name in logic.widgetRenderList:
		logic.scene.objects[name].stopAction()
	logic.scene.objects['rotateGlow'].visible = False

	fullSize = 1.001

	logic.scene.objects['rx.render'].localScale = (fullSize, fullSize, fullSize)
	logic.scene.objects['ry.render'].localScale = (fullSize, fullSize, fullSize)
	logic.scene.objects['rz.render'].localScale = (fullSize, fullSize, fullSize)
	logic.scene.objects['x.render'].localScale = (fullSize, fullSize, fullSize)
	logic.scene.objects['y.render'].localScale = (fullSize, fullSize, fullSize)
	logic.scene.objects['z.render'].localScale = (fullSize, fullSize, fullSize)

def _showManipulator(objs, pos, rot):
	'''show the widget'''
	#set pivot
	logic.pivotObject.worldPosition = pos
	logic.pivotObject.worldOrientation = rot

	for obj in objs:
		obj.setParent(logic.pivotObject)

	# move widget to pivot
	logic.widgetObject.worldPosition = 	pos
	logic.widgetObject.worldOrientation = rot

	# make visible
	logic.widgetObject.visible = True
	for child in logic.widgetObject.children:
		if child.name in logic.widgetRenderList:
			child.visible = True
			pass


def _hideManipulator():
	''' hides the widget'''
	logic.widgetObject.worldPosition = [0,0,10000]	# move it out of view to avoid false collision detection
	logic.widgetObject.visible = False
	for child in logic.widgetObject.children:
		child.visible = False
		pass


def handleManipulator(objs, target):
	# start move
	if logic.mouse.events[events.LEFTMOUSE] == inputActivated and target and target.name in ["x", "y", "z", "widget"]:
		logic.moving = target
		centerPos = logic.viewCamObject.getScreenPosition(logic.scene.objects["widget"])
		logic.mousePosOffset = [logic.mouse.position[0]-centerPos[0], logic.mouse.position[1]-centerPos[1]]
		logic.undo.append("Moved")

	elif logic.mouse.events[events.LEFTMOUSE] == inputActivated and target and target.name in ["rx", "ry", "rz"]:
		logic.rotating = target
		logic.undo.append("Rotated")
		logic.rotatingAmount = [0,0,0]


	# while moving widget
	elif logic.mouse.events[events.LEFTMOUSE] == inputActive and logic.moving:

		# setup variables for ray/ray intersect
		# compute camera pos
		camPos = logic.viewCamObject.worldPosition
		v1 = Vector(camPos)

		# if 'win' in releaseOS:
		# 	print("h")		#http://projects.blender.org/tracker/index.php?func=detail&aid=33943&group_id=9&atid=306

		# compute camera ray end pos
		offsettedPos = [logic.mouse.position[0]-logic.mousePosOffset[0], logic.mouse.position[1]-logic.mousePosOffset[1]]
		vec = logic.viewCamObject.getScreenVect(*offsettedPos)
		camProjPos = list(camPos[:])
		camProjPos[0] -= vec[0] * 500
		camProjPos[1] -= vec[1] * 500
		camProjPos[2] -= vec[2] * 500
		v2 = Vector(camProjPos)

		# compute widget pos
		widgetPos = logic.widgetObject.worldPosition
		v3 = Vector(widgetPos)

		# compute widget ray end pos
		mat = logic.widgetObject.worldTransform

		if logic.moving.name == 'x':
			transMat = Matrix.Translation(Vector((500,0,0)))
		elif logic.moving.name == 'y':
			transMat = Matrix.Translation(Vector((0,500,0)))
		elif logic.moving.name == 'z':
			transMat = Matrix.Translation(Vector((0,0,500)))
		else:
			transMat = Matrix.Translation(Vector((0,0,0)))

		# merge orientation/scaling with new translation
		extendedMat = mat*transMat
		v4 = extendedMat.translation

		# compute ray/ray interset, return list of tuples
		# ...for the closest point on each line to each other
		result = geometry.intersect_line_line(v1, v2, v3, v4)
		try:
			widgetTargetPos = result[1]									# this is where the widget should be
		except:
			pass

		# special case for moving center widget
		if logic.moving.name == 'widget':
			result = geometry.intersect_point_line(widgetPos, v1, v2)
			widgetTargetPos = list(result[0])

		# apply transform
		logic.pivotObject.worldPosition = widgetTargetPos
		logic.widgetObject.worldPosition = widgetTargetPos

	# while rotating widget
	elif logic.mouse.events[events.LEFTMOUSE] == inputActive and logic.rotating:
		rot = list(logic.widgetObject.worldOrientation.to_euler()[0:3])
		x = logic.mousePosDelta[0] * 10.0
		y = logic.mousePosDelta[1] * 10.0

		# flip axis
		camAlignment = 1
		widgetAlignment = 1

		# compute screenspace mouse position relative to widget centre
		# i.e. which quadrant the mouse is relative to the widget centre
		widgetPosXY = list(logic.viewCamObject.getScreenPosition(logic.widgetObject))
		mousePosXY = logic.mouse.position
		diffXY = (widgetPosXY[0]-mousePosXY[0], widgetPosXY[1]-mousePosXY[1])

		if logic.rotating.name == "rx":
			if logic.viewCamObject.worldPosition[0] > 0:
				camAlignment = -1
			if diffXY[1] < 0:
				widgetAlignment = -1
			rot[0] += x*camAlignment*widgetAlignment
			if diffXY[0] < 0:
				widgetAlignment = 1
			else:
				widgetAlignment = -1
			rot[0] += y*camAlignment*widgetAlignment

		elif logic.rotating.name == "ry":
			if logic.viewCamObject.worldPosition[1] > 0:
				camAlignment = -1
			if diffXY[1] < 0:
				widgetAlignment = -1
			rot[1] += x * camAlignment*widgetAlignment
			if diffXY[0] < 0:
				widgetAlignment = 1
			else:
				widgetAlignment = -1
			rot[1] += y * camAlignment*widgetAlignment

		elif logic.rotating.name == "rz":
			rot[2] += x * camAlignment * widgetAlignment


		# integrate over time (for the duration of the mouse interaction)
		logic.rotatingAmount[0] += rot[0]
		logic.rotatingAmount[1] += rot[1]
		logic.rotatingAmount[2] += rot[2]

		#apply transform
		logic.pivotObject.worldOrientation = rot
		logic.widgetObject.worldOrientation = rot

	# finish
	elif logic.mouse.events[events.LEFTMOUSE] == inputDeactivated and (logic.moving or logic.rotating or logic.mouseLock == 0):
		if logic.moving:
			logic.pluggable.edit.moved.notify()
		if logic.rotating:
			logic.pluggable.edit.rotated.notify()


		# set manipulation flags to false
		logic.moving = False
		logic.rotating = False

		# saves all keyframe for current slide
		# do before removing parents
		logic.mvb.slides[logic.mvb.activeSlide].capture()

		# unlink obj(s) to pivot
		for obj in logic.pivotObject.children:
			obj.removeParent()

		logic.rotatingAmount = [0,0,0]


	# set mouseLock state
	if logic.moving or logic.rotating:
		logic.mouseLock = 2
	else:
		logic.mouseLock = 0

