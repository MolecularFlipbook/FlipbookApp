
useDebug = True			# for development use

# features
useTutorial = not useDebug		# show tutorial at beginning
useCache = False					# use cached meshing data if available
useAmbientOcclusion = True		# use screen space ambient occlusion shader
useSceneOverlay = True			# use 3d navigation cube
useLogger = True				# shows the program status log
useTooltip = True 				# use help tooltip
useMultitouch = False			# use mt lib
usePowerNap = False				# Skips rendering when app is idle, requires patched Blender
defaultSurfacing = 'cms'		# 'msms' or  'cms'

useBinaryMSMS = True		# use executable instead of ePMV

updateInterval = 7 	 		# checks for MFB update with server every n day

moveSpeed = 1.0
zoomSpeed = 2.0
rotateSpeed = 1.0
manipulatorSize = 0.2

viewMinZoom = 0.2
viewMaxZoom = 20.0

highlightColor = (0.2,0.2,0.2)
defaultSkyColor = [0.9, 0.9, 0.9]
defaultSkyColorDark = [0.1, 0.1, 0.1]

defaultAnimationInterval = 2.0

# edit with caution:
clickRegion = 0.01			# threshold for mouse-drift while clicking
maxObject = 100				# max allowed object in scene
nominalFrameTime = 0.03333  # tic time of the mfb
lensZoomFactor = 19


import platform
if 'windows' in platform.system().lower():
	releaseOS = 'win'
elif 'mac' in platform.system().lower():
	releaseOS = 'mac'
elif 'darwin' in platform.system().lower():
	releaseOS = 'mac'
else:
	raise Exception("Unknown OS")