import threading, os, sys, logging, time

from .settings import *
from .helpers import *
from bge import logic


class threadedWrapper(threading.Thread):

	def __init__(self, func=None, args=None):
		self.args = args
		self.func = func
		threading.Thread.__init__(self)

	def run(self):

		# collect metadata
		# capture screenshot
		# save everything to file
		# authenticate
		# make post request
		
		# confirm upload
		# launch browser

		logic.gui.showModalMessage(subject="Uploading will be available soon!", message='Thanks for your patience.')
		
		return "Okay!"