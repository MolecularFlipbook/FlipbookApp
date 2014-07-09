# import gamengine modules
from bge import logic
from bge import events
from bge import render

from bgl import *

# import mvb's own module
from . import bgui
from . import updater
from . import actions

from .helpers import *
from .settings import *
from .appinfo import *

import webbrowser, time, threading, re, imp

class ViewportUI():
	''' Singleton class to store UI widget residing in the 3D canvas'''
	def __init__(self, guiSys):
		# common variables
		self.gui = guiSys				# alias to gui
		self.panel = None				# current opened panel

		self.gui.on_right_release = self.rightClick		# registers global handler
		self.gui.on_left_release = self.leftClick 		# registers global handler


	def rightClick(self,  widget=None):
		"""invoked with right click"""
		x, y = logic.mouse.position

		# do nothing if the mouse is moved by clickRegion amount
		if (abs(x-logic.clickRInit[0]) < clickRegion) and  (abs(y-logic.clickRInit[1]) < clickRegion):


			def menuOptions(itemIndex = None):
				if itemIndex == 0:
					logic.undo.undo()
				elif itemIndex == 2:
					self.showHelp()
				elif itemIndex == 3:
					self.showFeedback()
				elif itemIndex == 4:
					self.showSettings()
				elif itemIndex == 5:
					self.showAbout()

				return ['Undo', '__________________________', 'Online Help', 'Provide Feedback', 'Settings', 'About']


			def objMenuOptions(itemIndex = None):
				if useDebug:
					imp.reload(actions)

				if itemIndex == 0:
					logic.undo.undo()
				elif itemIndex == 1:
					actions.duplicateObjs()
				elif itemIndex == 2:
					actions.deleteObjs()
				elif itemIndex == 3:
					# actions.gatherObjs()
					# actions.scatterObjs()
					pass
				elif itemIndex == 4:
					self.showHelp()
				elif itemIndex == 6:
					self.showFeedback()
				elif itemIndex == 7:
					self.showSettings()
				elif itemIndex == 8:
					self.showAbout()

				return ['Undo', 'Duplicate Objects', 'Delete Object', '__________________________' ,'Online Help', 'Provide Feedback', 'Settings', 'About']
					
			if any(logic.mvb.preActiveObj):
				# object under mouse
				self.popUpMenu = logic.gui.showMenu(name="popUpMenu", pos=logic.mouse.position, caller=widget, callback=objMenuOptions, items=objMenuOptions())
			elif logic.mvb.activeObjs:
				# objects selected
				self.popUpMenu = logic.gui.showMenu(name="popUpMenu", pos=logic.mouse.position, caller=widget, callback=objMenuOptions, items=objMenuOptions())
			else:
				# no object under mouse
				self.popUpMenu = logic.gui.showMenu(name="popUpMenu", pos=logic.mouse.position, caller=widget, callback=menuOptions, items=menuOptions())


	def leftClick(self,  widget=None):
		"""invoked with left click"""
		# remove popup menu
		if hasattr(self, "popUpMenu"):
			guiKill(self.popUpMenu)


	def showSettings(self):
		if self.panel:
			self.close()

		self.panel = bgui.Frame(self.gui, 'settingPanel', size=[320,400], radius=6, options=bgui.BGUI_CENTERED)
		settingClose = bgui.ImageButton(self.panel, 'settingClose', size=[24,24], pos=[290,370], sub_theme="close")
		settingClose.on_left_release = self.close

		bgui.Label(self.panel, 'settingLb', text="Settings", pos=[0,350], sub_theme="OPHeader", options=bgui.BGUI_CENTERX|bgui.BGUI_NO_FOCUS)

		bgui.Label(self.panel, "useTutLb", text="Start tutorial on startup", pos=[60, 300], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
		cb = bgui.Checkbox(self.panel, "useTut", small=True, state=True, size=[50,15], pos=[40,300])
		cb.on_left_release = self.settingToggle


		bgui.Label(self.panel, "useUpdaterLb", text="Check for update on startup", pos=[60, 280], sub_theme="whiteLabel", options=bgui.BGUI_NO_FOCUS)
		cb = bgui.Checkbox(self.panel, "useUpdater", small=True, state=True, size=[50,15], pos=[40,280])
		cb.on_left_release = self.settingToggle


	def showFeedback(self):
		'''open default web browser'''
		logic.mouseExitHack = True
		webbrowser.open(AppFeedbackURL)
		

		# if self.panel:
		# 	self.close()

		# if not logic.gui.feedbackDialog.visible:
		# 	try:
		# 		logic.gui.importDialog.visible = False
		# 	except:
		# 		pass
		# 	try:
		# 		logic.gui.publishDialog.visible = False
		# 	except:
		# 		pass
		# 	logic.gui.feedbackDialog.visible = True


	def showAbout(self):
		''' create the about dialog box'''
		if self.panel:
			self.close()

		self.panel = bgui.Frame(self.gui, 'aboutPanel', size=[320,400], radius=6, options=bgui.BGUI_CENTERED)
		aboutClose = bgui.ImageButton(self.panel, 'aboutClose', size=[24,24], pos=[290,370], sub_theme="close")
		aboutClose.on_left_release = self.close

		bgui.Image(self.panel, 'AppNameImage', themeRoot('logo.png'), size=[256,128], pos=[0,280], options=bgui.BGUI_CACHE|bgui.BGUI_NO_FOCUS|bgui.BGUI_CENTERX)
		bgui.Label(self.panel, 'AppVersionLB', text=AppVersion, pos=[0,300], sub_theme="whiteLabel", options=bgui.BGUI_CENTERX|bgui.BGUI_NO_FOCUS)

		self.version = bgui.FrameButton(self.panel, 'latestVersion', text="Checking for latest version...", radius=5, pos=[0,277], size=[280,20], sub_theme='link', options=bgui.BGUI_CENTERX)
		self.version.lighter = True
		self.version.on_left_click = self.openSite

		self.thread = updater.VersionCheck(widget = self.version)
		self.thread.start()

		scroll = bgui.Scroll(self.panel, 'CreditScroll', pos=[0,60], size=[300, 200], actual=[1,2], options=bgui.BGUI_CENTERX)
		bgui.Frame(scroll, 'bg', border=0, pos=[0,0], options=bgui.BGUI_FILLED|bgui.BGUI_NO_FOCUS)

		bgui.TextBlock(scroll, 'creditbox', text=AppCredit, pos=[50,0], size=[200, 400], sub_theme="whiteBlockSmall", options=bgui.BGUI_NO_FOCUS)

		url = bgui.Label(self.panel, 'AppURLLB', text=AppURL, pos=[0,30], sub_theme="whiteLabel", options=bgui.BGUI_CENTERX)
		url.on_left_click = self.openSite


	def settingToggle(self, widget):
		from . import config
		if widget.name == "useTut":
			if widget.state:
				config.set('useTutorial', True)
			else:
				config.set('useTutorial', False)
		config.write()


	def showInfo(self, target):
		delaySecond = 0.05
		if time.time() - logic.mvb._hoverTimer < delaySecond:
			return

		size = [80, 40]
		mousex, mousey = logic.gui.mousePos
		if target and (not logic.mvb.playing) and (not logic.mvb.rendering):
			x,y = logic.viewCamObject.getScreenPosition(target)
			y = 1.0 - y
			centerx, centery = [int(x*render.getWindowWidth()), int(y*render.getWindowHeight())]
			finalx = int(mousex*0.2+centerx*0.8) - int(size[0]/2)
			finaly = int(mousey*0.2+centery*0.8) + 100

			try:
				mvbobj = logic.mvb.getMVBObject(target)
			except:
				pass			# not a mvb object
			else:
				if mvbobj.chainData:
					chainName = mvbobj.chainData.full_name()
					chainDescription = mvbobj.pdbMetaData.chaininfo[mvbobj.chainData.name]
				else:
					chainName = mvbobj.name
					chainDescription = "Blobber Geometry"

				def drawLineBright():
					drawLine(int(mousex), int(mousey), finalx + int(size[0]/2), finaly, (0.5, 0.5, 0.5, 0.5))

				size[0] = max(80, len(chainDescription)*7.5) + 20
				size[0] = int(size[0])
				finalx = finalx - size[0]//2
				self.infoPanel = bgui.Frame(self.gui, 'infoPanel', size=size, pos=[finalx,finaly], border=1, radius=3, sub_theme='medOpacityLight', options=bgui.BGUI_NO_FOCUS)
				bgui.Label(self.infoPanel, 'infoName', text=chainName, pos=[0,21], options=bgui.BGUI_CENTERX)
				bgui.Label(self.infoPanel, 'infoDesc', text=chainDescription, pos=[0,7], sub_theme='blackLabelSmall', options=bgui.BGUI_CENTERX)
				bgui.Custom(self.infoPanel, 'infoLine', func=drawLineBright)


	def showHelp(self):
		'''open default web browser for help'''
		logic.mouseExitHack = True
		webbrowser.open(AppHelpURL)


	def openSite(self, widget):
		''' opens homepage in default browser'''
		logic.mouseExitHack = True
		webbrowser.open(AppURL)


	def close(self, widget=None):
		''' close dialog box'''
		if widget:
			guiKill(widget.parent)
		else:
			guiKill(self.panel)
		self.panel = None


# instantiate the UI singleton
def init(guiSys):
	return ViewportUI(guiSys)
