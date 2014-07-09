# import gamengine modules
from bge import logic
from bge import events
from bge import render

# early import
from .settings import *
from .helpers import *


def makeLink(pos1, pos2):
	''' Create a linked chain from A to B'''

	added = logic.scene.addObject('linkSegment', logic.pivotObject)

	return

	

