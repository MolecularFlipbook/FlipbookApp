# import gamengine modules
from bge import logic
from bge import events
from bge import render

# import mvb's own module
from . import bgui
from .helpers import *
from .settings import *

import os


class FeedbackDialogUI():

	def __init__(self, guiSys):

		# common variables
		self.gui = guiSys
		self.panel = None

		self.name = None
		self.email = None
		self.feedback = None
		self.log = None


	@property
	def visible(self):
		'''toggle visibility of self - the feedback dialog'''
		if self.panel:
			return self.panel.visible
		else:
			return False

	@visible.setter
	def visible(self, value):
		'''toggle visibility of self - the feedback dialog'''
		if value:
			if self.panel:
				#move panel widget back to centre
				self.panel.options = self.panel.options | bgui.BGUI_CENTERED
			else:
				# create the UI on first use
				self.createUI()
			self.panel.visible = True

		else:
			self.panel.visible = False
			# remove centering
			if self.panel.options & bgui.BGUI_CENTERED:
				self.panel.options = self.panel.options ^ bgui.BGUI_CENTERED
			self.panel.position = [-1000, -1000]


	def createUI(self):
		'''create the feedback Dialog'''
		# Main Image held in Frame container, self.feedbackDialog
		self.panel = bgui.Image(self.gui, 'feedbackDialog', themeRoot('feedbackDialog.png'),size=[512,450],options=bgui.BGUI_CACHE|bgui.BGUI_MOVABLE|bgui.BGUI_CENTERED)
		self.panel.on_left_click = self.onClick

		#close button
		self.feedbackDialogClose = bgui.ImageButton(self.panel, 'feedbackDialogClose', size=[24,24], pos=[480,418], sub_theme="close")
		self.feedbackDialogClose.on_left_release = self.onClick

		offset = 10
		#name
		bgui.Label(self.panel, 'namelb', "Name:", pos=[50,340])
		self.nameInput = bgui.TextInput(self.panel, 'name', size=[300, 32], pos=[130, 340-offset])
		self.nameInput.on_enter_key = self.next

		bgui.Label(self.panel, 'emaillb', "Email:", pos=[50,300])
		self.emailInput = bgui.TextInput(self.panel, 'email', size=[300, 32], pos=[130, 300-offset])
		self.emailInput.on_enter_key = self.next

		bgui.Label(self.panel, 'feedbacklb', "Feedback:", pos=[50,250])
		self.feedbackInput1 = bgui.TextInput(self.panel, 'feedback1', radius=0, size=[300, 20], pos=[130, 271-offset])
		self.feedbackInput2 = bgui.TextInput(self.panel, 'feedback2', radius=0, size=[300, 20], pos=[130, 271-offset-20])
		self.feedbackInput3 = bgui.TextInput(self.panel, 'feedback3', radius=0, size=[300, 20], pos=[130, 271-offset-20*2])
		self.feedbackInput4 = bgui.TextInput(self.panel, 'feedback4', radius=0, size=[300, 20], pos=[130, 271-offset-20*3])
		self.feedbackInput5 = bgui.TextInput(self.panel, 'feedback5', radius=0, size=[300, 20], pos=[130, 271-offset-20*4])
		self.feedbackInput6 = bgui.TextInput(self.panel, 'feedback6', radius=0, size=[300, 20], pos=[130, 271-offset-20*5])
		self.feedbackInput7 = bgui.TextInput(self.panel, 'feedback7', radius=0, size=[300, 20], pos=[130, 271-offset-20*6])
		self.feedbackInput1.on_edit = self.testWrap
		self.feedbackInput2.on_edit = self.testWrap
		self.feedbackInput3.on_edit = self.testWrap
		self.feedbackInput4.on_edit = self.testWrap
		self.feedbackInput5.on_edit = self.testWrap
		self.feedbackInput6.on_edit = self.testWrap
		self.feedbackInput7.on_edit = self.testWrap
		self.feedbackInput1.on_enter_key = self.newLine
		self.feedbackInput2.on_enter_key = self.newLine
		self.feedbackInput3.on_enter_key = self.newLine
		self.feedbackInput4.on_enter_key = self.newLine
		self.feedbackInput5.on_enter_key = self.newLine
		self.feedbackInput6.on_enter_key = self.newLine
		self.feedbackInput7.on_enter_key = self.newLine
		self.feedbackInput1.on_backspace = self.backspace
		self.feedbackInput2.on_backspace = self.backspace
		self.feedbackInput3.on_backspace = self.backspace
		self.feedbackInput4.on_backspace = self.backspace
		self.feedbackInput5.on_backspace = self.backspace
		self.feedbackInput6.on_backspace = self.backspace
		self.feedbackInput7.on_backspace = self.backspace

		legal = "Debug information will help us track down the problem faster, it contains various usage information."
		self.sendLoglb = bgui.Label(self.panel, 'sendLoglb', "Include Debugging Information", pos=[240,90], sub_theme='blackLabel')
		self.sendLogcb = bgui.Checkbox(self.panel, 'sendLog', small=True, state = True, size = [100,30], pos=[225,90])
		self.sendLogcb.tooltip = legal

		#send button
		self.sendBtn = bgui.FrameButton(self.panel, 'sendBtn', text='Send', radius = 5, size=[100,30],pos=[206,30])
		self.sendBtn.on_left_release = self.onClick


	def onClick(self, widget):
		'''Generic handler for dealing with button clicks'''
		# set panel to movable
		if self.panel.options & bgui.BGUI_CENTERED:
			self.panel.position = [self.panel.parent.size[0]/2 - self.panel.size[0]/2, self.panel.parent.size[1]/2 - self.panel.size[1]/2]
			self.panel.options = self.panel.options ^ bgui.BGUI_CENTERED

		elif widget.name == 'feedbackDialogClose':						#reset entire panel after closing dialog
			self.visible = False

		elif widget.name == 'sendBtn':
			print("trying to send feedback")
			self.name = self.nameInput.text
			self.email = self.emailInput.text
			allText = [self.feedbackInput1.text,self.feedbackInput2.text,self.feedbackInput3.text,self.feedbackInput4.text,self.feedbackInput5.text,self.feedbackInput6.text,self.feedbackInput7.text]
			self.feedback = '\n'.join(allText)
			if self.sendLogcb.state:
				path = os.path.join(logic.tempFilePath, 'debug.log')
				try:
					fp = open(path)
					self.log = fp.read()
				except Exception as E:
					self.log = "Error Reading log: " + str(E)
			else:
				self.log = 'No Debug Info attached'

			self.post()


	def next(self, widget):
		'''go to the next widget'''
		if widget.name == 'name':
			logic.registeredFunctions.append(lambda: self.delayedActivate('email'))
		elif widget.name == 'email':
			logic.registeredFunctions.append(lambda: self.delayedActivate('feedback1'))

	def testWrap(self, widget):
		'''see if we shoudl wrap to next line'''
		lineCount = int(widget.name[-1])
		lineLength = 38
		if len(widget.text) > lineLength:
			# move cursor down
			if lineCount < 7:
				widget.deactivate()
				widgetName = 'feedback'+ str(lineCount + 1)
				logic.registeredFunctions.append(lambda: self.delayedActivate(widgetName))
			else:
				logic.logger.new('Maximum length reached', type='WARNING')
				widget.deactivate()

	def backspace(self, widget, text=''):
		''' see if we shoudl go back to the previous line'''
		lineCount = int(widget.name[-1])
		if len(text) == 0:
			# move cursor up
			if lineCount > 1:
				widget.deactivate()
				widgetName = 'feedback'+ str(lineCount-1)
				logic.registeredFunctions.append(lambda: self.delayedActivate(widgetName))

	def newLine(self, widget):
		'''jump to next line'''
		lineCount = int(widget.name[-1])
		if lineCount < 7:
			logic.registeredFunctions.append(lambda: self.delayedActivate('feedback'+str(lineCount+1)))
		else:
			logic.logger.new('Maximum length reached', type='WARNING')


	def delayedActivate(self, widgetName):
		''' active a widget'''
		self.panel.children[widgetName].activate()
		return False


	def post(self):
		import platform
		from . import sendy

		okay = sendy.sendMail('', platform.node(), [self.name, self.email, self.feedback, self.log])
		if okay:
			logic.gui.showModalMessage('Message Sent', 'Thanks for your input!')
			self.visible = False
		else:
			logic.gui.showModalMessage('Error sending message', 'Please get in touch with us using the website.')


def init(guiSys):
	'''instantiate the UI singleton'''
	return FeedbackDialogUI(guiSys)

