from bge import logic

from .appinfo import *

import threading
import time
import re
import logging
import webbrowser
import urllib.request


def check():
	''' perform the check in the bg'''
	thread = VersionCheck()
	thread.start()
	return False


class VersionCheck(threading.Thread):
	''' a threading object that checks the web for the latest release'''

	def __init__(self, widget=None):
		threading.Thread.__init__(self)
		self.widget = widget

	def getVersion(self):
		try:
			req = urllib.request.Request(AppUpdateURL)
			response = urllib.request.urlopen(req)
			content = response.read()
			return content.decode()
		except Exception as E:
			logging.error("Unable to check for new version:" + str(E))
			return '0'


	def run(self):
		# check for new version

		time.sleep(0.2)

		officialVersion = self.getVersion()

		# convert to float
		pattern = re.search('([\d.]+)', officialVersion)
		if pattern:
			officialVersion = float(pattern.group(0))
		else:
			officialVersion = None

		# convert to float
		pattern = re.search('([\d.]+)', AppVersion)
		if pattern:
			currentVersion = float(pattern.group(0))
		else:
			currentVersion = None

		if self.widget:
			# write to about box
			if not (currentVersion and officialVersion):
				self.widget.text = 'Error checking for update'
			else:
				if officialVersion < currentVersion:
					self.widget.text = 'You have the latest version.'
				elif officialVersion == currentVersion:
					self.widget.text = 'You have the current version.'
				else:
					upgradeTxt = 'New version ' + str(officialVersion) + ' is available for download.'
					self.widget.text = upgradeTxt

		else:
			# create modal dialog
			if (currentVersion and officialVersion):
				if officialVersion > currentVersion:
					message = 'Molecular Flipbook version ' + str(officialVersion) + ' is available for download.'
					subject = 'New version available'
					verb = 'Download'
					cancelVerb = 'Not Now'
					def action():
						logic.mouseExitHack = True
						webbrowser.open(AppURL)

					logic.gui.showModalConfirm(subject=subject, message=message, verb=verb, cancelVerb=cancelVerb, action=action)
		return