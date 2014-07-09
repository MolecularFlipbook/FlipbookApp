# import blender gamengine modules
from bge import logic
from bge import events
from bge import render

from . import space3d

from . import bgui

from .settings import *
from .helpers import *

import os, time, logging, pdb, shutil

header = "Export\nAnimation"

hideOffset = 200

def update(panel):
	''' called when model has changed'''
	showPanel(panel)
	pass


def destroy(panel):
	pass


def showPanel(panel):
	# encoding options
	encodingOptions = ["MPEG4 (MP4)"]
	sizeOptions = ["Full Resolution", "Half Resolution"]
	encoding = bgui.Frame(panel, "bgEncoding", size=[290,135], pos=[0,0], sub_theme="invisible")
	bgui.Label(encoding, "formatLb", text="Format:", pos=[10, 110], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	bgui.Dropdown(encoding, "encodingSel", items=encodingOptions, pos=[70, 105], caller=panel)

	bgui.Label(encoding, "sizeLb", text="Size:", pos=[30, 70], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	bgui.Dropdown(encoding, "sizeSel", items=sizeOptions, pos=[70, 65], caller=panel)

	bgui.Label(encoding, "nameLb", text="Name:", pos=[20, 25], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	projectName = bgui.TextInput(encoding, "filename", text = logic.projectName, size=[150,25], pos=[70, 20])
	projectName.on_edit = saveText
	projectName.on_enter_key = saveText

	# general options
	options = bgui.Frame(panel, "bgOptions", size=[290,135], pos=[280,0], sub_theme="invisible")
	bgui.Label(options, "slidesLb", text="Slides:", pos=[10, 110], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	cb = bgui.Checkbox(options, "allSlide", small=True, state=True, size=[30,15], pos=[60,110])
	cb.on_left_release = toggleSlide
	cb = bgui.Checkbox(options, "selectSlide", small=True, size=[50,15], pos=[60,90])
	cb.on_left_release = toggleSlide

	bgui.Label(options, "lb1", text="All", pos=[75, 110], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	bgui.Label(options, "lb2", text="From\t\t\t\t\tto", pos=[75, 90], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
	bgui.TextInput(options, "t1", size=[40,20], pos=[115, 85])
	bgui.TextInput(options, "t2", size=[40,20], pos=[185, 85])

	w = bgui.Checkbox(options, "rough", text="Draft (faster)", small=True, size=[80,15], pos=[20,30])
	w.tooltip = "Make the export faster by rendering at draft quality"

	w = bgui.Checkbox(options, "overwrite", text="Overwrite", small=True, size=[80,15], pos=[150,30])
	w.tooltip = "Overwrite exisitng files"


	exportPic = bgui.FrameButton(panel, "ExportPic",  text="Export Picture", radius = 5, size=[100,32], pos=[580, 50])
	exportPic.on_left_release = renderStartPic

	exportVid = bgui.FrameButton(panel, "ExportVid",  text="Export Animation", radius = 5, size=[100,32], pos=[580, 10])
	exportVid.on_left_release = renderStartVid


	def drawLine1():
		drawLine(encoding.position[0]+260, encoding.position[1]+130, encoding.position[0]+260, encoding.position[1], (1,1,1,0.2))

	def drawLine2():
		drawLine(options.position[0]+280, options.position[1]+130, options.position[0]+280, options.position[1], (1,1,1,0.2))

	line1 = bgui.Custom(panel, 'infoLine1', func=drawLine1)
	line2 = bgui.Custom(panel, 'infoLine2', func=drawLine2)

def saveText(widget):
	if widget.text != logic.projectName:
		logic.videoPath = None
		logic.imagePath = None
		logic.projectName = widget.text

def toggleSlide(widget):
	''' mimic radio buttons '''
	widget.parent.children["allSlide"].state = False
	widget.parent.children["selectSlide"].state = False
	widget.state = True


def renderStartPic(widget):
	renderStart(still=True)

def renderStartVid(widget):
	renderStart(still=False)


def renderStart(still, publish=False):
	try:
		logic.tutorial.state = None
	except:
		pass

	if len(logic.mvb.slides)<=1 and not still:
		logic.gui.showModalMessage(subject="No Animation to Export", message="Try adding a few slides first, or export as an image.", action=None)
		return

	# get options
	options = logic.options.container.children['bgOptions'].children
	logic.useDraft = options["rough"].state
	logic.useOverwrite = options["overwrite"].state

	options = logic.options.container.children['bgEncoding'].children
	# logic.filename = options["filename"].text
	logic.filename = logic.projectName
	logic.filesize = options["sizeSel"].selectedItem

	# create render folder
	path = os.path.join(logic.tempFilePath, 'frames', logic.filename)
	shutil.rmtree(path, ignore_errors=True)
	if not createPath(path):
		logic.logging.new("Error creating path", type="ERROR")
		return
	logic.renderFilePath = path
	logging.debug('Render File Path:\t' + str(logic.renderFilePath))
	logging.info("Started exporting " + str(logic.mvb.getTotalTime()) + " seconds of vid")
	
	logic.mvb.playing = False
	logic.mvb.rendering = True
	
	if not still:
		logic.mvb.time = 0

	logic.mvb.activeObjs.clear()
	logic.startTime = time.time()

	if hasattr(logic, 'skyTextureAnimated') and logic.skyTextureAnimated:
	 	logic.skyTexture.stop()
	 	logic.skyTexture.play()

	if logic.gui.importDialog.visible:
		logic.gui.importDialog.visible = False
	if logic.gui.publishDialog.visible:
		logic.gui.publishDialog.visible = False
	logic.gui.viewport.close()

	interfaceToggle(visible = False)
	space3d.mouseHandler() 			# call once to hide manipulator, etc

	# register main render function to be called each frame
	logic.registeredFunctions.append(renderLoop)
	logic.renderForPublish = publish
	logic.renderStill = still

	logging.info("Rendering started at: \t" + str(time.asctime()))


def renderLoop():

	if logic.useDraft:
		speed = 2.0
	else:
		speed = 1.0

	keyboard = logic.keyboard.events
	if keyboard[events.ESCKEY]:
		renderFinish(abort = True)
		return False

	# wait some time for things to settle
	if time.time() - logic.startTime < 0.3:
		return True

	# render still
	if logic.renderStill:
		path = os.path.join(logic.renderFilePath, "snapshot.png")
		logic.gate.captureScreen(path=path, crop=True)
		try:
			renderFinish()
		except:
			logic.logger.new("Rendering failed", type="ERROR")
		
		# signals that the function is completed
		return False


	# rendering loop
	if logic.mvb.time < logic.mvb.getTotalTime():

		# render into screenshots
		logic.mvb.time += nominalFrameTime * speed
		logic.mvb._frameCounter += 1
		path = os.path.join(logic.renderFilePath, str(logic.mvb._frameCounter).zfill(4)+".png")
		logic.gate.captureScreen(path=path, crop=True)
		logic.gui.renderProgress.percent = logic.mvb.time / logic.mvb.getTotalTime()

		# signals that the function isn't done yet
		return True
	# finishing rendering
	else:
		logging.info("Rendering finished at:\t" + str(time.asctime()))
		# clean up
		try:
			renderFinish()
		except:
			logic.logger.new("Rendering failed", type="ERROR")
		# signals that the function is completed
		return False


def renderFinish(abort=False):
	videoFolderPath =  os.path.join(logic.tempFilePath, "video")
	imageFolderPath =  os.path.join(logic.tempFilePath, "frames", logic.projectName)


	if logic.renderStill:
		
		logic.videoPath = os.path.join(imageFolderPath, 'snapshot.png')

		if logic.renderForPublish:
			logic.gui.publishDialog.visible = True
		else:
			def openPathWrapper():
				openPath(imageFolderPath)
			logic.gui.showModalConfirm(subject="Done!", message="The image can be found at " + str(imageFolderPath), verb="Open Folder", cancelVerb="Okay", action=openPathWrapper)

		

		
	else:
		start = 0
		end = logic.mvb._frameCounter
		if createPath(videoFolderPath):
			doneFilePath = ""

			if logic.useOverwrite:
				doneFilePath = os.path.join(videoFolderPath, logic.filename + ".mp4")
				
			else:
				for i in range(999):
					doneFilePath =  os.path.join(videoFolderPath, logic.filename + str(i).zfill(4) + ".mp4")
					if not os.path.exists(doneFilePath):
						break

			if abort:
				logic.gui.showModalMessage(subject="Render Aborted", message="No video file is created.")
			else:
				try:
					import subprocess

					if 'mac' in releaseOS:
						if useDebug:
							ffmpegPath = os.path.normpath(os.path.join(logic.binaryBlenderPath, '../../../../', 'ffmpeg'))
						else:
							ffmpegPath = os.path.normpath(os.path.join(logic.binaryBlenderPath, '..', 'ffmpeg'))
					else:
						ffmpegPath = os.path.normpath(os.path.join(logic.binaryBlenderPath, '..', 'ffmpeg.exe'))

					logging.info(ffmpegPath)

					if logic.useDraft:
						fps = '15'
					else:
						fps = '30'

					bitrate = '2000k'
					inputFiles = logic.renderFilePath+'/%04d.png'
					# -vf scale="trunc(oh*a/2)*2:720"
					if logic.filesize:
						scaling = 'scale=trunc(iw/4)*2:trunc(ih/4)*2'
					else:
						scaling = 'scale=trunc(iw/2)*2:trunc(ih/2)*2'

					cmd = [ffmpegPath, '-y', '-r', fps, '-i', inputFiles, '-vf', scaling, '-vcodec', 'mpeg4', '-b:v', bitrate, doneFilePath]

					logging.info(cmd)
					ok = subprocess.call(cmd)
					
					if ok != 0:
						raise Exception('Video Encoder unsuccessful')

				except Exception as E:
					print (E)
					logic.logger.new("Failed to assembly video", type="ERROR")
					logic.logger.new(str(E), type="ERROR")
				else:
					logic.videoPath = doneFilePath
		
					if logic.renderForPublish:
						logic.gui.publishDialog.visible = True

					else:
						def openPathWrapper():
							openPath(imageFolderPath)
						
						logic.gui.showModalConfirm(subject="Done!", message="The video can be found at " + str(videoFolderPath), verb="Open Folder", cancelVerb="Okay", action=openPathWrapper)


	interfaceToggle(visible = True)

	logic.mvb.rendering = False
	logic.mvb._frameCounter = 0


def interfaceToggle(visible = True):
	# restore UI
	logic.gui.renderProgress.visible = not visible
	logic.gui.renderProgress.percent = 0.0

	logic.gui.timeline.visible = visible
	logic.timeline.timeLineTrain.visible = visible
	logic.gui.outlinerVisible(visible)
	logic.gui.helpVisible(visible)
	logic.gui.outlinerPane.visible = visible
	logic.gui.helpPane.visible = visible

	if visible:
		offset = hideOffset
	else:
		offset = -hideOffset
	
	logic.gui.groupicons._offsetTarget = [logic.gui.groupicons._offsetTarget[0]+offset,logic.gui.groupicons._offsetTarget[1]]
	logic.gui.optionsPane._offsetTarget = [logic.gui.optionsPane._offsetTarget[0],logic.gui.optionsPane._offsetTarget[1]-offset]
	logic.gui.loggerPane._offsetTarget = [logic.gui.loggerPane._offsetTarget[0],logic.gui.loggerPane._offsetTarget[1]-offset]
	
	if useSceneOverlay:
		if visible:
			logic.scene2D.objects['camera2d'].position[1] -= 2000
		else:
			logic.scene2D.objects['camera2d'].position[1] += 2000

	if visible:
		logic.gate.edgeOffset = logic.gate.edgeOffsetOriginal
	else:
		logic.gate.edgeOffset = [0,0,0,0]

	logic.gate.viewUpdate()
	logic.gate.visible = visible

	if visible:
		logic.viewCamObject.lens -= lensZoomFactor
	else:
		logic.viewCamObject.lens += lensZoomFactor
	
