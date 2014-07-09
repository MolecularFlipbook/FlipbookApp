# import gamengine modules
from bge import logic
from bge import events
from bge import render

# import mvb's own module
from . import bgui
from . import appinfo
from . import fileInterface
from .helpers import *
from .settings import *

import os, math, textwrap, sys, time, imp, webbrowser, urllib, shutil


class PublishDialogUI():
	def __init__(self, guiSys):

		# common variables
		self.gui = guiSys
		self.panel = None
		self.thread = None

		self.imageIndex = 0

	@property
	def visible(self):
		if not self.panel:
			return False
		else:
			return self.panel.visible

	@visible.setter
	def visible(self, value):
		if value:
			if not self.panel:
				# create the UI on first use
				self.createUI()
			else:
				#move panel widget back to centre
				self.panel.options = self.panel.options | bgui.BGUI_CENTERED
				self.createUI()		# force update
			self.panel.visible = True

		else:
			self.panel.visible = False
			# remove centering
			if self.panel.options & bgui.BGUI_CENTERED:
				self.panel.options = self.panel.options ^ bgui.BGUI_CENTERED
			self.panel.position = [-1000, -1000]


	def createUI(self):
		"""create the Dialog"""

		# panel
		self.panel = bgui.Image(self.gui, 'publishDialog', themeRoot('publishDialog.png'),size=[512,450],options=bgui.BGUI_CACHE|bgui.BGUI_MOVABLE|bgui.BGUI_CENTERED)
		self.panel.on_left_click = self.onBlur

		#close button
		self.publishDialogClose = bgui.ImageButton(self.panel, 'publishDialogClose', size=[24,24], pos=[480,420], sub_theme="close")
		self.publishDialogClose.on_left_release = self.onClick


		#project name
		bgui.Label(self.panel, 'namelb', "Project Name:", pos=[50,350], sub_theme='whiteLabel', options=bgui.BGUI_NO_FOCUS)
		self.nameInput = bgui.TextInput(self.panel, 'name', text=logic.projectName, size=[290, 32], pos=[150, 340])
		self.nameInput.on_edit = self.saveText
		self.nameInput.on_enter_key = self.onBlur

		# video
		bgui.Label(self.panel, 'prompt1', "Video:", pos=[97,300], sub_theme='whiteLabel', options=bgui.BGUI_NO_FOCUS)
		if logic.videoPath:
			bgui.Label(self.panel, 'prompt1Field', str(logic.videoPath)[-30:], pos=[150,300], sub_theme='whiteLabelDisabled', options=bgui.BGUI_NO_FOCUS)
			self.previewVid = bgui.FrameButton(self.panel, 'previewVid', text='Preview', radius = 5, size=[90,30],pos=[350,290])
			self.previewVid.on_left_release = self.onClick
		else:
			bgui.Label(self.panel, 'prompt1Field', str(logic.videoPath)[-30:], pos=[150,300], sub_theme='whiteLabelDisabled', options=bgui.BGUI_NO_FOCUS)
			self.renderVid = bgui.FrameButton(self.panel, 'renderVid', text='Create Video', radius = 5, size=[90,30],pos=[350,290])
			self.renderVid.on_left_release = self.onClick
		
		# thumbnail
		bgui.Label(self.panel, 'prompt2', "Cover Image:", pos=[56,250], sub_theme='whiteLabel')
		if logic.videoPath:
			imgs = self.getImageFiles()
			
			self.pickImageL = bgui.FrameButton(self.panel, 'pickImageL', text='    >>  ', radius = 5, size=[50,30],pos=[385,240])
			self.pickImageL.on_left_release = self.onClick

			self.pickImageR = bgui.FrameButton(self.panel, 'pickImageR', text='    <<  ', radius = 5, size=[50,30],pos=[385,140])
			self.pickImageR.on_left_release = self.onClick

			try:
				self.image = bgui.Image(self.panel, 'image', imgs[0][0], size=[240,130], pos=[150, 140], options=bgui.BGUI_NO_FOCUS)
				logic.imagePath = imgs[0][0]
			except:
				self.image = bgui.Image(self.panel, 'image', '', size=[240,130], pos=[150, 140], options=bgui.BGUI_NO_FOCUS)
				logic.imagePath = None

		else:
			self.imagePath = bgui.Label(self.panel, 'prompt2Field', str(logic.imagePath)[-30:], pos=[150,250], sub_theme='whiteLabelDisabled', options=bgui.BGUI_NO_FOCUS)


		#save button
		self.saveBtn = bgui.FrameButton(self.panel, 'saveBtn', text='Save To Disk', radius = 5, size=[100,30],pos=[145,90])
		self.saveBtn.on_left_release = self.onClick
		
		#send button
		self.sendBtn = bgui.FrameButton(self.panel, 'sendBtn', text='Upload to Web', radius = 5, size=[100,30],pos=[255,90])
		self.sendBtn.on_left_release = self.onClick

		
		# legal text
		explain = 'After you click the Upload button, the current session will be saved to a temporary folder and you will be taken to the Molecular Flipbook site. You will have a chance to fill in more detail about this project there.'
		self.textblock = bgui.TextBlock(self.panel, 'textblock', pos=[0,30], size=[400,50] , text = explain, sub_theme = 'greyBlockSmall', options=bgui.BGUI_CENTERX|bgui.BGUI_NO_FOCUS)

		# new style loading bar
		# createBusyBar(self,  size=[300,30], pos=[170,200])


	def saveText(self, widget):
		if widget.text != logic.projectName:
			logic.videoPath = None
			logic.imagePath = None
			logic.projectName = widget.text
		
	
	def onBlur(self, widget):
		self.createUI()

	def onClick(self, widget):
		"""Generic handler for dealing with button clicks"""
		# set panel to movable
		if self.panel.options & bgui.BGUI_CENTERED:
			self.panel.position = [self.panel.parent.size[0]/2 - self.panel.size[0]/2, self.panel.parent.size[1]/2 - self.panel.size[1]/2]
			self.panel.options = self.panel.options ^ bgui.BGUI_CENTERED

		if widget.name == "publishDialogClose":
			self.visible = False
		elif widget.name == 'previewVid':
			openPath(logic.videoPath)
		elif widget.name == 'renderVid':
			self.startRender()
		elif widget.name == 'pickImageR':
			fileList = self.getImageFiles()
			self.imageIndex -= 1
			self.imageIndex = self.imageIndex%(len(fileList)-1 or 1)
			imgPath = fileList[self.imageIndex][0]
			logic.imagePath = imgPath
			self.image.update_image(imgPath)
		elif widget.name == 'pickImageL':
			fileList = self.getImageFiles()
			self.imageIndex += 1
			self.imageIndex = self.imageIndex%(len(fileList)-1 or 1)
			imgPath = fileList[self.imageIndex][0]
			logic.imagePath = imgPath
			self.image.update_image(imgPath)
		elif widget.name == 'sendBtn':
			self.upload(confirm=True)
		elif widget.name == 'saveBtn':
			fileInterface.saveBrowse()


	def startRender(self):
		logic.options.view = 'FINALIZE'
		logic.options.activeModule.renderStart(still=len(logic.mvb.slides)<2, publish=True)
		

	def save(self):
		# save session
		projectName = self.nameInput.text
		projectPath = os.path.join(logic.tempFilePath, 'publish', projectName)

		# clean up path
		shutil.rmtree(projectPath, ignore_errors=True)

		createPath(projectPath)
		path = os.path.join(logic.tempFilePath, 'publish', projectName, projectName+'.flipbook')
		rpath = fileInterface.save(path)
		if rpath:
			sourceFile = rpath
		else:
			return

		# copy media
		if logic.videoPath:
			if logic.videoPath.endswith('.mp4'):
				if 'mac' in releaseOS:
					os.system("cp %s %s" %(logic.videoPath, os.path.join(projectPath, projectName+'_video.mp4')))
				elif 'win' in releaseOS:
					os.system("copy %s %s" %(logic.videoPath, os.path.join(projectPath, projectName+'_video.mp4')))
			else:
				if 'mac' in releaseOS:
					os.system("cp %s %s" %(logic.videoPath, os.path.join(projectPath, projectName+'_cover.png')))
				elif 'win' in releaseOS:
					os.system("copy %s %s" %(logic.videoPath, os.path.join(projectPath, projectName+'_cover.png')))


		if logic.imagePath:
			if 'mac' in releaseOS:
				os.system("cp %s %s" %(logic.imagePath, os.path.join(projectPath, projectName+'_cover.png')))
			elif 'win' in releaseOS:
				os.system("copy %s %s" %(logic.imagePath, os.path.join(projectPath, projectName+'_cover.png')))

		return projectPath


	def upload(self, confirm=False):
		'''Save and upload '''

		# check to make sure we have everything
		if confirm and not logic.videoPath:
			logic.gui.showModalConfirm(subject='Create Video Before Upload?',
									message='It would be best if a video animation is uploaded along with the Flipbook file. Create video first?',
									verb='Create Video',
									cancelVerb='Just Upload',
									action=self.startRender,
									cancelAction=self.upload
									)

			return
		
		# save all data to publish folder
		projectPath = self.save()

		webbrowser.open(appinfo.AppSubmitURL)
		openPath(projectPath)
		return
		


	def getImageFiles(self):
		imageFolderPath =  os.path.join(logic.tempFilePath, "frames", logic.projectName)
		filesList = []
		for path, dirs, files in os.walk(imageFolderPath):
			filesList.extend([(os.path.join(path, file), os.path.getsize(os.path.join(path, file))) for file in files])
		
		truncatedList = filesList[0::int((len(filesList)/5)) or 1]

		# print(truncatedList)
		return truncatedList


	def getPDBs(self):
		''' Get a list of PDBs '''
		pdbs = set()
		for objName, obj in logic.mvb.objects.items():
			if obj.type != 0:
				continue

			pdbs.add(obj.pdbData.name[:])

		pdbString = '+'.join(pdbs)
		print(pdbString)
		return pdbString



# instantiate the UI singleton
def init(guiSys):
	return PublishDialogUI(guiSys)

