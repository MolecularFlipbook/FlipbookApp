# import blender gamengine modules
from bge import logic
from bge import events
from bge import render

from . import bgui

from .settings import *
from .helpers import *


header = "Lighting"

def update(panel):
	''' called when model has changed'''
	showPanel(panel)

def destroy(panel):
	pass


def showPanel(panel):
	return

