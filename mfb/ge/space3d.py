# import gamengine modules
from bge import logic
from bge import events
from bge import render

import mathutils

import imp

# import mvb's own modules
from . import manipulator
from .settings import *
from .helpers import *

from . import bgui

from math import sqrt

def navCubeHandler(cont):
	""" this function is invoked on mouse-over of the navcube object, via logic brick """

	# scale up
	cont.owner.localScale = [1.1, 1.1, 1.1]

	if logic.mouse.events[events.LEFTMOUSE] == inputDeactivated:
		logic.mouseLock = 3
		view = cont.owner.name[1:]
		if view == 'Front':
			logic.viewRotTarget = [0,0,0]
		elif view == 'Back':
			logic.viewRotTarget = [0,0,pi]
		elif view == 'Top':
			logic.viewRotTarget = [-pi/2.0,0,0]
		elif view == 'Left':
			logic.viewRotTarget = [0,0,-pi/2.0]
		elif view == 'Right':
			logic.viewRotTarget = [0,0,pi/2.0]
		elif view == 'Bottom':
			logic.viewRotTarget = [pi/2.0,0,0]

	if logic.mouse.events[events.LEFTMOUSE] == inputActive:
		view = cont.owner.name[1:]
		if view == 'panUp':
			logic.mouseLock = 3
			logic.viewLocTarget[2] = 0.1 * moveSpeed * logic.viewZoomCurrent
		elif view == 'panDown':
			logic.mouseLock = 3
			logic.viewLocTarget[2] = -0.1 * moveSpeed * logic.viewZoomCurrent
		elif view == 'panLeft':
			logic.mouseLock = 3
			logic.viewLocTarget[0] = -0.1 * moveSpeed * logic.viewZoomCurrent
		elif view == 'panRight':
			logic.mouseLock = 3
			logic.viewLocTarget[0] = 0.1 * moveSpeed * logic.viewZoomCurrent
		elif view == 'zoomOut':
			logic.viewZoomTarget += zoomSpeed*logic.viewZoomTarget * 0.05
		elif view == 'zoomIn':
			logic.viewZoomTarget -= zoomSpeed*logic.viewZoomTarget * 0.05

def navigationCubeUpdate():
	"""update navigation cube rotation"""
	logic.scene2D.objects["NavCube"].localOrientation = logic.viewRotCurrent
	logic.scene2D.objects["NavCube"].localOrientation.invert()

	for obj in ['Front', 'Back', 'Top', 'Left', 'Right', 'Bottom', 'panDown', 'panUp', 'panLeft', 'panRight', 'zoomIn', 'zoomOut']:
		o = logic.scene2D.objects['f'+obj]
		o.localScale = mix([1.0, 1.0, 1.0], o.localScale, 0.5)


def focusView():
	"""recenters the camera based on a list of kx_objects"""
	if logic.mvb._activeObjs:
		objs = logic.mvb._activeObjs
	elif logic.mvb.objects:
		objs = [mvbObj.obj for name, mvbObj in logic.mvb.objects.items()]
	else:
		logic.registeredFunctions.append(resetView)
		return

	# set pivot
	centre = manipulator.getObjCenter(objs)
	currentPos = list(logic.controllerObject.worldPosition)
	pivot = logic.controllerObject

	# set zoom
	zoom = 0

	screenCoords=[]
	for obj in objs:
		pos = logic.viewCamObject.getScreenPosition(obj)
		screenCoords.append(pos)

	def inCircle(coord, r):
		return sqrt((coord[0] - 0.5) ** 2 + (coord[1] - 0.5) ** 2) < r

	allIn = True
	for pos in screenCoords:
		if not inCircle(pos, 0.5):
			zoom =  5

	logic.viewZoomTarget += zoom


	if pivot.getDistanceTo(centre) < 0.1:
		# done focus view
		logic.logger.new('Focused view')
		logic.pluggable.view.reset.notify()
		return False
	else:
		pivot.worldPosition = mix(currentPos, centre, 0.5)
		return True


def resetView():
	""" reset camera pivot to centre """

	viewLocCenter = [0,0,0]
	viewRotTarget = [-0.5,0,1]
	cameraPivot = logic.controllerObject

	logic.viewRotTarget = viewRotTarget
	curPos = list(cameraPivot.localPosition)
	cameraPivot.localPosition = mix(curPos, viewLocCenter, 0.8)

	#reset zoom
	logic.viewZoomTarget = 8.0
	logic.mouseLock = 1

	if cameraPivot.getDistanceTo(viewLocCenter) < 0.02:
		return False

	return True

def cameraUpdate():
	"""Update the viewport camera's position and orientation"""
	# get mouse movement delta
	keyboard = logic.keyboard.events
	mousePosNew = logic.mouse.position
	mousePosDelta = [mousePosNew[0]-logic.mousePosOld[0], mousePosNew[1]-logic.mousePosOld[1]]
	logic.mousePosOld = mousePosNew
	logic.mousePosDelta = mousePosDelta

	# update camera position
	cameraPivot = logic.controllerObject
	# pan camera
	logic.viewLocTarget = mix(logic.viewLocTarget, [0,0,0], 0.8)
	cameraPivot.applyMovement(logic.viewLocTarget, True)											# apply pivot location

	# rotate camera
	logic.viewRotCurrent = mix(logic.viewRotCurrent, logic.viewRotTarget, 0.7)
	cameraPivot.localOrientation = logic.viewRotCurrent											# apply rotation

	#zoom camera
	logic.viewZoomTarget = min(viewMaxZoom, max(viewMinZoom, logic.viewZoomTarget))					# clamp zoom value
	logic.viewZoomCurrent = mix(logic.viewZoomCurrent, logic.viewZoomTarget, 0.7)
	cameraPivot.localScale = [logic.viewZoomCurrent, logic.viewZoomCurrent, logic.viewZoomCurrent]	# apply zoom

	# move skybox with camera
	logic.scene.objects["Sphere"].localPosition = mix(cameraPivot.worldPosition, logic.scene.objects["Sphere"].localPosition, 0.1)


def cameraManipulator():
	"""main 3d viewport navigation code"""
	keyboard = logic.keyboard.events
	mouse = logic.mouse.events
	mousePosDelta = logic.mousePosDelta

	# mouse controlled view orbit
	x = -mousePosDelta[0]*rotateSpeed * 5.0
	y = -mousePosDelta[1]*rotateSpeed * 5.0

	if mouse[events.LEFTMOUSE] == inputActive and not(logic.gui.isCtrled or logic.gui.isCommanded or logic.gui.isShifted or logic.gui.isAlted):
		logic.viewRotTarget[0] += y
		logic.viewRotTarget[2] += x
		logic.mouseLock = 1
		if abs(y) > 0.1 or abs(x) > 0.1:
			logic.pluggable.view.rotated.notify()

	# keyboard controlled view zoom
	if keyboard[events.EQUALKEY] == inputActive:
		logic.viewZoomTarget -= zoomSpeed*logic.viewZoomTarget * 0.05
		logic.mouseLock = 1
		logic.pluggable.view.zoomed.notify()
	if keyboard[events.MINUSKEY] == inputActive:
		logic.viewZoomTarget += zoomSpeed*logic.viewZoomTarget * 0.05
		logic.mouseLock = 1
		logic.pluggable.view.zoomed.notify()

	# mouse wheel controlled view zoom
	if mouse[events.WHEELUPMOUSE] == inputActive\
		or mouse[events.WHEELUPMOUSE] == inputActivated:
		logic.viewZoomTarget -= zoomSpeed*logic.viewZoomTarget  * 0.1
		logic.mouseLock = 1
		logic.pluggable.view.zoomed.notify()
	if mouse[events.WHEELDOWNMOUSE] == inputActive\
		or mouse[events.WHEELDOWNMOUSE] == inputActivated:
		logic.viewZoomTarget += zoomSpeed*logic.viewZoomTarget * 0.1
		logic.mouseLock = 1
		logic.pluggable.view.zoomed.notify()

	# mouse controlled view zoom
	if mouse[events.LEFTMOUSE] == inputActive and logic.gui.isShifted:
		val = y*zoomSpeed*logic.viewZoomTarget * 0.3
		logic.viewZoomTarget -= val
		
		if abs(val) > 0.01:
			logic.pluggable.view.zoomed.notify()


	# keyboard controlled view pan
	if keyboard[events.UPARROWKEY] == inputActive:
		logic.viewLocTarget[2] = 0.1 * moveSpeed * logic.viewZoomCurrent
		logic.pluggable.view.moved.notify()
	if keyboard[events.DOWNARROWKEY] == inputActive:
		logic.viewLocTarget[2] = -0.1 * moveSpeed * logic.viewZoomCurrent
		logic.pluggable.view.moved.notify()
	if keyboard[events.LEFTARROWKEY] == inputActive:
		logic.viewLocTarget[0] = -0.1 * moveSpeed * logic.viewZoomCurrent
		logic.pluggable.view.moved.notify()
	if keyboard[events.RIGHTARROWKEY] == inputActive:
		logic.viewLocTarget[0] = 0.1 * moveSpeed * logic.viewZoomCurrent
		logic.pluggable.view.moved.notify()
	
	# mouse controlled view pan
	if mouse[events.RIGHTMOUSE] == inputActive or (mouse[events.LEFTMOUSE] == inputActive and (logic.gui.isCtrled or logic.gui.isCommanded or logic.gui.isAlted)):
		logic.viewLocTarget[0] = -mousePosDelta[0] * moveSpeed * 10.0 * logic.viewZoomCurrent
		logic.viewLocTarget[2] = mousePosDelta[1] * moveSpeed * 10.0 * logic.viewZoomCurrent
		logic.mouseLock = 1
		if abs(mousePosDelta[0]) > 0.02 or abs(mousePosDelta[1]) > 0.02:
			logic.pluggable.view.moved.notify()


	#keyboard controlled navigation
	if keyboard[events.PAD7] == inputActivated:
		logic.viewRotTarget = [-pi/2.0,0,0]					# top view
	if keyboard[events.PAD1] == inputActivated:
		logic.viewRotTarget = [0,0,0]						# front view
	if keyboard[events.PAD3] == inputActivated:
		logic.viewRotTarget = [0,0,pi/2.0]					# side view
	if keyboard[events.PAD0] == inputActivated:
		logic.registeredFunctions.append(resetView)	# reset view
	if keyboard[events.PAD4] == inputActivated:
		logic.viewRotTarget[2] -= pi/10						# rotate left
	if keyboard[events.PAD6] == inputActivated:
		logic.viewRotTarget[2] += pi/10						# rotate right
	if keyboard[events.PAD8] == inputActivated:
		logic.viewRotTarget[0] -= pi/10						# tilt up
	if keyboard[events.PAD2] == inputActivated:
		logic.viewRotTarget[0] += pi/10						# tilt down



def cameraManipulatorPulse():
	"""keyboard controlled view rotation, only execuated 6 times a second"""
	keyboard = logic.keyboard.events
	if keyboard[events.PAD4] == inputActive:
		logic.viewRotTarget[2] -= pi/10						# rotate left
	if keyboard[events.PAD6] == inputActive:
		logic.viewRotTarget[2] += pi/10						# rotate right
	if keyboard[events.PAD8] == inputActive:
		logic.viewRotTarget[0] -= pi/10						# tilt up
	if keyboard[events.PAD2] == inputActive:
		logic.viewRotTarget[0] += pi/10						# tilt down



def mouseHandler():
	'''mouse handler for 3d interactions'''
	x, y = logic.mouse.position

	# display the manipulator widget, this shoudl happen before the mouseLock check, to ensutre setManipulator is called always
	manipulator.setManipulator(logic.mvb.activeObjs)

	# skip if the mouse is locked for interactions
	if logic.mouseLock == 3:
		# release it for next frame
		logic.mouseLock = 0
		return

	# register initial click position
	if logic.mouse.events[events.LEFTMOUSE] == inputActivated:
		logic.clickLInit = (x,y)
		logic.pluggable.system.leftClick.notify()
	if logic.mouse.events[events.RIGHTMOUSE] == inputActivated:
		logic.clickRInit = (x,y)
		logic.pluggable.system.rightClick.notify()
	if logic.mouse.events[events.MIDDLEMOUSE] == inputActivated or \
		(logic.mouse.events[events.LEFTMOUSE] == inputActivated and logic.gui.isAlted):
		logic.boxSelect = True

		if logic.boxSelect:
			# box select start
			logic.boxSelectCoord = [x, y, 0, 0]

			def boxSelect():
				if logic.mouse.events[events.MIDDLEMOUSE] == inputActive or \
				(logic.mouse.events[events.LEFTMOUSE] == inputActive and logic.gui.isAlted):
					logic.boxSelectCoord[2] = logic.mouse.position[0]
					logic.boxSelectCoord[3] = logic.mouse.position[1]

					# render preview
					pos = logic.boxSelectCoord[:2]
					pos[1] = 1.0 - pos[1]
					size = logic.boxSelectCoord[2:]
					size[0] -= pos[0]
					size[1] = 1.0 - size[1]
					size[1] -= pos[1]

					logic.gui.boxSel = bgui.Frame(logic.gui, 'boxSel', size=size, pos=pos, sub_theme='lowOpacityDark' , options=bgui.BGUI_NO_FOCUS|bgui.BGUI_NORMALIZED)
					logic.mouseLock = 3
					return True

				elif logic.mouse.events[events.MIDDLEMOUSE] == inputDeactivated or \
					logic.mouse.events[events.LEFTMOUSE] == inputDeactivated or \
					logic.mouse.events[events.LEFTMOUSE] == inputActive and not logic.gui.isAlted:
					logic.mvb.activeObjs.clear()
					# find objects under box selection
					for name, MVBObj in logic.mvb.objects.items():
						
						if MVBObj.locked:
							continue

						screenPos = logic.viewCamObject.getScreenPosition(MVBObj.obj)
						p1 = mathutils.Vector(logic.boxSelectCoord[2:])
						p2 = mathutils.Vector((logic.boxSelectCoord[0], logic.boxSelectCoord[3]))
						p3 = mathutils.Vector(logic.boxSelectCoord[:2])
						p4 = mathutils.Vector((logic.boxSelectCoord[2], logic.boxSelectCoord[1]))

						result = mathutils.geometry.intersect_point_quad_2d(mathutils.Vector(screenPos), p1, p2, p3, p4)
						if result != 0:
							logic.mvb.activeObjs.add(MVBObj.obj)
					# reset
					logic.mouseLock = 0
					logic.boxSelect = False
					logic.boxSelectCoord = [0,0,0,0]
					logic.gui.boxSel.kill()
					return False
				else:
					logic.mouseLock = 3
					return True

			# register handler
			logic.registeredFunctions.append(boxSelect)
			return

		logic.pluggable.system.middleClick.notify()



	# get obj under mouse
	if logic.mvb.playing or logic.moving or logic.rotating or logic.mouseLock > 0:
		target = None 													# do not run if these operations are in progress
		targetXRay = None
	else:
		vect = logic.viewCamObject.getScreenVect(x,y)					# try to get widget, xray through other objects
		try:
			length = -logic.viewCamObject.position[2]/vect[2]
			p = vect * length
			pos = logic.viewCamObject.position + p
			targetXRay = logic.viewCamObject.rayCast(pos, None, 500, "isWidget", 0, 1, 0)[0]
		except Exception as E:
			print (E)
			targetXRay = None

		if targetXRay:
			target = targetXRay
		else:
			target = logic.viewCamObject.getScreenRay(x,y, 500)			# get object under mouse in 3D scene

	# ignore invisible objects
	if target and ("template" in target.name) and (not target.visible): # and ('linkSegment' in targetName):
		target = None

	try:
		if target and logic.mvb.getMVBObject(target).locked:
			target = None
	except Exception as E:
		...


	logic.mvb.preActiveObj = [target]								# set object as preActive object

	# mouse over widget
	if target and target.name in logic.widgetList or logic.moving or logic.rotating:
		manipulator.highlightManipulator(target)
		# hide info tooltip
		if hasattr(logic.gui.viewport, "infoPanel"):
			guiKill(logic.gui.viewport.infoPanel)

	# not over widget
	else:
		manipulator.unHighlightManipulator()

		# mouse over protein object
		if target and target not in logic.mvb.activeObjs:
			# show info
			try:
				logic.gui.viewport.showInfo(target)
			except:
				pass							#probably isn't a protein

		else:
			# hide info
			if hasattr(logic.gui.viewport, "infoPanel"):
				guiKill(logic.gui.viewport.infoPanel)

		# set state for modifier keys
		shifted =  logic.gui.isShifted
		ctrled = logic.gui.isCtrled

		# set active Object
		if logic.mouse.events[events.LEFTMOUSE] == inputDeactivated and logic.clickLInit:
			if (abs(x-logic.clickLInit[0]) < clickRegion) and  (abs(y-logic.clickLInit[1]) < clickRegion):

				if target:										# valid selection
					if shifted or ctrled:						# append to the selection
						logic.mvb.activeObjs.add(target)
					else:										# replace the selection
						logic.mvb.activeObjs.clear()
						logic.mvb.activeObjs.add(target)
				else:											# empty selection
					if shifted or ctrled:						# do nothing
						pass
					else:										# clear the selection
						logic.mvb.activeObjs.clear()



	# manipulate object
	manipulator.handleManipulator(logic.mvb.activeObjs, target)

	# make the size of the manipulator size consistent
	scale = [logic.viewZoomCurrent*manipulatorSize, logic.viewZoomCurrent*manipulatorSize, logic.viewZoomCurrent*manipulatorSize]
	logic.widgetObject.localScale = mix(scale, [1,1,1], 0.8)


	# manipulate view
	if (not target) and (logic.mouseLock == 0) and (logic.gui.focused_widget == logic.gui.system)\
		or logic.mouse.events[events.WHEELUPMOUSE] or logic.mouse.events[events.WHEELDOWNMOUSE]:
		cameraManipulator()

