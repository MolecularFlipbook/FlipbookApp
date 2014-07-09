from bge import logic
from .settings import *


def reallyRestart():
	if useDebug:
		print('Restarting is not supported in Debug Mode')
	else:
		import subprocess
		subprocess.Popen(logic.binaryPlayerPath)
		logic.endGame()


def restart():
	s = 'Start over?'
	m = 'Starting over will wipe out any unsaved modification you made to the scene.'
	logic.gui.showModalConfirm(subject=s, message=m, verb="Start Over", cancelVerb="Cancel", action=reallyRestart, cancelAction=None)
