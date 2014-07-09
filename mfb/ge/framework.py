#entry point for the app
print ('='*80)

# import gamengine modules
from bge import logic
from bge import events
from bge import render
from bge import constraints
import bgl

# early import
from .settings import *
from .helpers import *
from .appinfo import *

# python modules
import os, sys, time, imp, platform, logging, math, pdb

# setup temp file paths, needed for logging
path = os.path.normpath(os.path.expanduser('~/Flipbook/'+str(AppVersion)))
if createPath(path):
	logic.tempFilePath = path
else:
	logic.endGame()
	raise IOError("Cannot create temp folder at " + str(path))

# setup logging
logging.basicConfig(filename=os.path.join(logic.tempFilePath, 'debug.log'), filemode='w', level=logging.DEBUG)
logging.debug('Started:\t' + str(time.asctime()))
logging.debug('Python:\t' + str(sys.version))
logging.debug('OS:\t\t' + str(platform.platform())+ ' as ' + str(platform.node()))
logging.debug('releaseOS: \t' + str(releaseOS))
logging.debug('Temp File Path:\t' + str(logic.tempFilePath))

try:
	from . import datastore
	from . import space3d
	from . import gui
	from . import shader
	from . import undo
	from . import pluggable
	from . import actions
	from . import updater
	from . import config
	from . import liveCoding

except Exception as E:
	logging.exception('Import failed')
	logic.endGame()


# additional paths
base = logic.expandPath('//')
logic.basePath = base
logging.debug('MFB Base Path:\t' + str(logic.basePath))


# additional python lib paths
sys.path.append(os.path.join(base, 'MGLToolsPckgs'))
if 'win' in releaseOS:
	sys.path.append(os.path.join(base, 'extraWin'))
elif 'mac' in releaseOS:
	sys.path.append(os.path.join(base, 'extraMac'))


def init(cont):
	'''initializes the application'''
	try:
		logic.mouse.visible = True

		# gpu detection and ssao enabler
		vendor = bgl.glGetString(bgl.GL_VENDOR)
		renderer = bgl.glGetString(bgl.GL_RENDERER)
		version = bgl.glGetString(bgl.GL_VERSION)

		logging.debug("GL Vendor:\t" + str(vendor))
		logging.debug("GL Renderer:\t" + str(renderer))
		logging.debug("GL Version:\t" + str(version))

		fancyGPU = not "intel" in vendor.lower()

		if useAmbientOcclusion and fancyGPU:
			logging.debug("Using SSAO")
			cont.activate(cont.actuators['ssao'])
		else:
			logging.debug("Not using SSAO")


		# overlay scene enabler
		if useSceneOverlay:
			cont.activate(cont.actuators['scene2D'])
			logging.debug("Using 2D overlay")
		else:
			logging.debug("Not using 2D overlay")

		# more file paths
		if 'mac' in releaseOS:
			if useDebug:
				logic.binaryPlayerPath = logic.expandPath("//binMac/flipbook.app/Contents/MacOS/blenderplayer")
			else:
				logic.binaryPlayerPath = logic.expandPath("//../MacOS/blenderplayer")
			logic.binaryBlenderPath = logic.binaryPlayerPath[:-6]
		elif 'win' in releaseOS:
			logic.binaryPlayerPath = logic.expandPath("//MolecularFlipbook.exe")
			logic.binaryBlenderPath = logic.expandPath("//blender.exe")

		# check paths:
		if os.path.exists(logic.binaryPlayerPath):
			logging.debug('binaryPlayer:\t' + str(logic.binaryPlayerPath))
		else:
			logging.warning('binaryPlayerPath is not verified. Full functionality is improbable')

		if os.path.exists(logic.binaryBlenderPath):
			logging.debug('binaryBlender:\t' + str(logic.binaryBlenderPath))
		else:
			logging.warning('binaryBlenderPath is not verified. Full functionality is improbable')


		# load config
		configPath = os.path.join(logic.tempFilePath, 'config')
		config.load(configPath)

		# initialize bgui
		logic.gui = gui.MyUI()

		# global aliases
		logic.scene = logic.getCurrentScene()						# blender scene alias
		logic.scene2D = None										# overlay 2d ui
		logic.viewCamObject = logic.scene.objects['camera3D']		# camera object
		logic.widgetObject = logic.scene.objects['widget']			# widget object
		logic.controllerObject = logic.scene.objects['controller']	# controller empty
		logic.widgetList = ['rx','ry','rz','x','y','z', 'widget']
		logic.widgetRenderList = ['x.render', 'y.render', 'z.render', 'rx.render', 'ry.render', 'rz.render', 'widget']
		logic.pivotObject = logic.scene.objects['pivot']			# pivot object, used for multiobject transform
		logic.markerKey = logic.scene.objects['markerKey'] 			# used to mark protein

		logic.mousePosDelta = [0,0]									#
		logic.mouseUp = False
		logic.mouseDown = False
		logic.tap = False
		logic.idleTimer = 0.0										#
		logic.mouseExitHack = False

		# variables used by space 3d navigation
		logic.mousePosOld = [0,0]
		logic.mousePosOffset = [0,0]
		logic.viewLocTarget = [0.0,0.0,0.0]
		logic.viewZoomTarget = 10.0
		logic.viewZoomCurrent = 10.0
		logic.viewRotTarget = [-0.5,0,1]
		logic.viewRotCurrent = [0,0,0]

		# mouse stuff
		logic.mouseLock = 0											# 0 = No Lock; 1 = View Manipulation, 2 = Object Manipulation, 3 = UI Manipulation
		logic.multitouch = False
		logic.boxSelect = False
		logic.boxSelectCoord = [0,0,0,0]

		# UI stuff
		logic.clickLInit = None
		logic.clickRInit = None
		logic.keyCounter = 0 										# track  keyboard input delay

		logic.sleeping = False
		logic.watch = {} 											# set this var to have the debugger automatically show the value
		logic.registeredFunctions = []								# list of functions to be run every frame
		logic.deferredFunctions = [] 								# list of functions to be run occasionally

		# var used for object manipulation
		logic.offsetPos = [0,0,0]									#
		logic.rotating = False
		logic.moving = False

		# session
		logic.filePath = None
		logic.videoPath = None
		logic.imagePath = None

		logic.projectName = 'Untitled'
		
		# hacks
		logic.objCounter = 1 										# track how many obj bge has spawned
		logic.blobberSliderPriority = False 						#hack

		# init widgets shader
		for w in logic.widgetRenderList:
			shader.initWidget(logic.scene.objects[w], 'manipulator')

		# init sky
		rgba = logic.mvb.bgColor[:]
		rgba.append(1.0)
		shader.initSky(logic.scene.objects['Sphere'], 'sky', color = rgba)

		# add the first slide on startup
		logic.timeline.slideAdd(silent=True)

		# start undo stack
		logic.undo = undo.init()

		# start pluggable system
		logic.pluggable = pluggable.init()

		logic.logger.new('Welcome to')
		logic.logger.new('Molecular Flipbook')

		# init updater
		if logic.config['lastUpdate']:
			elapsedTime = int(time.time() - logic.config['lastUpdate'])
			if elapsedTime > 86400 * updateInterval:
				logic.deferredFunctions.append(updater.check)
				config.set('lastUpdate', time.time())
		else:
			logic.deferredFunctions.append(updater.check)
			config.set('lastUpdate', time.time())

		# Done Init
		logging.debug('3D scene initialization done')

		# load file
		logging.debug(sys.argv)
		from . import fileInterface
		
		if len(sys.argv) > 1:
			try:
				path = sys.argv[1]
				if path.endswith('.flipbook'):
					fileInterface.load(path=sys.argv[1])
			except Exception as E:
				logic.logger.new('Unable to load File', type='WARNING')
				logging.warning(str(E))

		# init tutorial system
		from . import tutorial
		logic.tutorial = tutorial.init()

		if logic.config['useTutorial'] and useTutorial and not logic.filePath:
			logic.tutorial.start()

		if useMultitouch:
			try:
				logging.debug('Using Multitouch')
				from . import multitouch
			except:
				logging.warning('Multitouch trackpad(s) not found')



		logic.pluggable.system.appStart.notify()

	except:
		logic.endGame()
		logging.exception('Initialization Error')
		print ('Initialization Error: Check log for more information.')
		print ('_'*80)


def init2D():
	'''initializes the orthographic overlay scene'''
	logic.scene2D = logic.getCurrentScene()
	logging.debug('2D scene initialization done')


def loop2D(cont):
	'''runs every frame in scene2D'''

	# update nav helper position to the following screen coord
	if not logic.mvb.rendering:
		x = 90
		y = 250
		size = 100

		# alias
		w = render.getWindowWidth()
		h = render.getWindowHeight()
		cam2d = logic.scene2D.objects['camera2d']

		# compute relative screen position
		zoom = w*h/20000
		size += zoom
		vect = cam2d.getScreenVect(x/w, 1.0 - y/h) * -size
		targetPos = cam2d.position + vect
		logic.scene2D.objects['Empty'].position = targetPos
		


def loop30():
	'''runs every frame on scene3D'''

	if hasattr(logic, 'skyTextureAnimated') and logic.skyTextureAnimated:
	 	logic.skyTexture.refresh(True)


	# manage idling of app
	sleepHandler()

	# handle navigation cube
	if logic.scene2D:
		space3d.navigationCubeUpdate()

	# update gui
	if logic.scene2D:
		# use overlay scene as canvas to draw BGUI
		logic.gui.loop(logic.scene2D)
	else:
		# use 3d scene as canvas to draw BGUI
		logic.gui.loop(logic.scene)

	if not logic.mvb.rendering:
		# handle viewport cam motion
		space3d.cameraUpdate()
		# handle mouse for 3d scene
		space3d.mouseHandler()
		# handle input
		keyboardHandler()

	# playback animation
	if logic.mvb.playing:
		playHandler()


	# update obj shaders
	for key, mvbobj in logic.mvb.objects.items():
		if mvbobj.obj:
			shader.updateProtein(mvbobj.obj, color = mvbobj.color)
		else:
			print ('Error: Unable to update shader. %s has no associated 3d geometry.' % mvbobj.obj)


	# update widget shader
	if logic.mvb.activeObjs:
		if not hasattr(logic, 'widgetsOpacity'):
			logic.widgetsOpacity = {}

		minOpacity = 0.0
		maxOpacity = 1.0
		mousePos = logic.mouse.position

		for w in logic.widgetRenderList:
			obj = logic.scene.objects[w]
			scale = obj.localScale[0]

			# compute distance to obj
			objPos = logic.viewCamObject.getScreenPosition(obj)
			distSq = (objPos[0]-mousePos[0])**2 + (objPos[1]-mousePos[1])**2
			dist = math.sqrt(distSq)
			dist *= 3.0
			opacity = 1.0-dist

			# hide unselected handles
			if scale > 1:
				opacityTarget = opacity
			else:
				opacityTarget = 0.1

			try:
				logic.widgetsOpacity[w] = mix(logic.widgetsOpacity[w], opacityTarget, 0.7)
			except:
				logic.widgetsOpacity[w] = opacityTarget

			if obj.name =='widget':
				if obj in logic.mvb.preActiveObj:
					shader.updateWidget(obj, opacity = 1.0)
				else:
					shader.updateWidget(obj, opacity = 0.5)
			else:
				shader.updateWidget(obj, opacity = logic.widgetsOpacity[w])

	# run registered functions
	for func in logic.registeredFunctions:
		# delete them when func returns False (i.e. finished)
		if not func():
			try:
				logic.registeredFunctions.remove(func)
			except ValueError:
				pass


def loop15():
	''' less frequent always-on timer'''
	resizeHandler()
	shader.updateSky(logic.scene.objects['Sphere'])
	


def loop5():
	'''runs every 5 frames, least often'''
	# slow keyboard repeats handler
	if useDebug: imp.reload(space3d)
	space3d.cameraManipulatorPulse()

	for func in logic.deferredFunctions:
		if not func():
			try:
				logic.deferredFunctions.remove(func)
			except ValueError:
				pass

	# toggle SSAO depend on performance
	# when just after waking up from sleep or not sleeping
	# if logic.getAverageFrameRate() < 20:
	# 	logic.controllerObject['ssao'] = False
	# elif logic.getAverageFrameRate() > 30:
	# 	logic.controllerObject['ssao'] = True



def endGame():
	'''terminate the runtime gracefully'''
	if useMultitouch:
		multitouch.stopDevices()
	logic.endGame()
	config.write()
	logging.info('Gracefully terminated: \t' + str(time.asctime()))


def keyboardHandler():
	'''keyboard handler for debugging'''
	keyboard = logic.keyboard.events

	# skip if we are in a textbox
	if hasattr(logic.gui.focused_widget, 'input_options'):
		return

	# timeline context
	if activeContext(logic.timeline):
		...

	# other context
	elif not activeContext():
		# delete
		if keyboard[events.BACKSPACEKEY] == inputActivated or keyboard[events.DELKEY] == inputActivated:
			# delete object
			actions.deleteObjs()
	
		# F
		if keyboard[events.FKEY] == inputActivated:
			logic.registeredFunctions.append(space3d.focusView)

		# Space
		if keyboard[events.SPACEKEY] == inputActivated:
			logic.mvb.playing = not logic.mvb.playing

		# Z
		if keyboard[events.ZKEY] == inputActivated and (logic.gui.isCtrled or logic.gui.isCommanded):
			logic.undo.undo()

	# debug context
	if useDebug:
		# ~
		if keyboard[events.ACCENTGRAVEKEY] == inputActivated:
			try:
				obj = list(logic.mvb.activeObjs)[0]
			except IndexError:
				pass
			else:
				mvbObj = logic.mvb.getMVBObject(obj)
			from pprint import pprint
			import code
			namespace = globals().copy()
			namespace.update(locals())
			code.interact(local=namespace)

		if keyboard[events.OKEY] == inputActivated:
			from . import fileInterface
			fileInterface.load(os.path.expanduser('~/Documents/Untitled.flipbook'))
			
		if keyboard[events.CKEY] == inputActivated:
			imp.reload(liveCoding)
			liveCoding.capture()


		

def resizeHandler():
	'''called when the window dimensions change'''
	# init
	if not hasattr(logic, 'screenSizeOld'):
		logic.screenSizeOld = 1

	# update window dimensions
	logic.screenSize = render.getWindowWidth()*render.getWindowHeight()

	# test for resizing
	if logic.screenSize != logic.screenSizeOld:
		'''
		# set size to multiples of 4, needed for screenshot png bug
		newX = int(x//4*4)
		newY = int(y//4*4)

		render.setWindowSize(newX, newY)
		'''

		# remember current setting
		logic.screenSizeOld = logic.screenSize
		logging.info('Window resized to:\t' + str(render.getWindowWidth()) + 'x' + str(render.getWindowHeight()))

		# hackish update
		logic.timeline.viewUpdate()
		logic.gate.viewUpdate()
		logic.mvb.time = logic.mvb.time 	# updates train


def playHandler():
	'''Play button functionality for animation of objects'''
	#increment time
	logic.mvb.time += nominalFrameTime

	# loop toggle enabled
	if logic.mvb.looping:		# go to beginning
		if logic.mvb.time >= logic.mvb.getTotalTime():
			logic.mvb.time = 0
	else:						#stop at last slide
		if logic.mvb.time >= logic.mvb.getTotalTime():
			logic.mvb.time = logic.mvb.getTotalTime()
			logic.mvb.playing = False



def sleepHandler():
	'''handles idling function'''
	# reset idle timer on key stroke
	for key, state in  logic.keyboard.events.items():
		if state > 0: logic.idleTimer = 0.0

	#reset idle timer when using animated bgs
	if hasattr(logic, 'skyTextureAnimated') and logic.skyTextureAnimated:
		logic.idleTimer = 0.0
		
	# reset idle timer on mouse
	if ((logic.mousePosDelta[0]+logic.mousePosDelta[1]) != 0)\
		or (logic.mouse.events[events.LEFTMOUSE] > 0) or (logic.mouse.events[events.RIGHTMOUSE] > 0)\
		or (logic.mouse.events[events.WHEELUPMOUSE] > 0) or (logic.mouse.events[events.WHEELDOWNMOUSE] > 0)\
		or logic.multitouch:
		logic.idleTimer = 0.0

	# reset idle timer on animation playback
	if logic.mvb.playing or logic.mvb.rendering or logic.registeredFunctions:
		logic.idleTimer = 0.0

	# really sleep
	if logic.idleTimer > 20:
		logic.sleeping = True
		if usePowerNap:
			try:
				render.setNap(True)
			except:
				pass
		else:
			time.sleep(0.2)
	elif logic.idleTimer > 1.0:
		logic.sleeping = True
		if usePowerNap:
			try:
				render.setNap(True)
			except:
				pass
		else:
			time.sleep(0.1)
	else:
		logic.sleeping = False

	# increment idle timer
	logic.idleTimer += nominalFrameTime