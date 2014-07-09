# import gamengine modules
from bge import logic
from bge import events
from bge import render

from .helpers import *
from .settings import *

import re

def incrementName(text, container):
	'''auto increament name to avoid 'already imported' warnings'''
	if text not in container:
		return text

	newName = text

	for i in range(1, 100):
		hasNumber = re.search('(\d+)$', newName)

		if hasNumber:
			newName =  newName[:hasNumber.start()] + str(i)
		else:
			newName = newName + '1'

		if newName not in container:
			return newName
