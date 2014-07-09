# import gamengine modules
from bge import logic
from bge import events
from bge import render

from . import OPCreate
from . import datastoreUtils

from .helpers import *
from .settings import *

import random, pdb

def deleteObjs():
	if any(logic.mvb.preActiveObj):
		logic.undo.append("Deleted")
		for obj in logic.mvb.preActiveObj:
			mvbObj = logic.mvb.getMVBObject(obj)
			logic.mvb.deleteObject(mvbObj)

	elif logic.mvb.activeObjs:
		logic.undo.append("Deleted")
		for obj in logic.mvb.activeObjs:
			mvbObj = logic.mvb.getMVBObject(obj)
			logic.mvb.deleteObject(mvbObj)
	
	else:
		if useDebug:
			print('Nothing to delete')

	logic.mvb.activeObjs.clear()
	logic.outliner.updateModel()


def scatterObjs():
	scatterRadius = 5
	if logic.mvb.activeObjs:
		logic.undo.append("Scattered")
		for obj in logic.mvb.activeObjs:
			mvbObj = logic.mvb.getMVBObject(obj)
			pos = mvbObj.loc
			pos[0] += random.uniform(-1,1) * scatterRadius
			pos[1] += random.uniform(-1,1) * scatterRadius
			pos[2] += random.uniform(-1,1) * scatterRadius
			mvbObj.loc = pos

		logic.mvb.slides[logic.mvb.activeSlide].capture()


def gatherObjs():
	gatherStrength = 0.5
	if logic.mvb.activeObjs:
		logic.undo.append("Gathered")
		for obj in logic.mvb.activeObjs:
			mvbObj = logic.mvb.getMVBObject(obj)
			pos = mvbObj.loc
			target = logic.widgetObject.worldPosition
			pos = mix(pos, target, gatherStrength)
			mvbObj.loc = pos

		logic.mvb.slides[logic.mvb.activeSlide].capture()


def gatherBioMT():
	pass


def duplicateObjs():

	# collect objects to duplicate
	objs = None
	if any(logic.mvb.preActiveObj):
		objs = logic.mvb.preActiveObj.copy()
	elif logic.mvb.activeObjs:
		objs = logic.mvb.activeObjs.copy()

	if objs:
		# duplicate
		for obj in objs:
			# get source mvbObj Data
			mvbObj = logic.mvb.getMVBObject(obj)
			newName = datastoreUtils.incrementName(mvbObj.name, logic.mvb.objects)

			if mvbObj.type == 1:
				# blobby
				objList = OPCreate.loadBlob(scale = mvbObj.scale[:], name=newName)
				if objList:
					for newObj in objList:
						newObj.color = mvbObj.color[:]
			elif mvbObj.type == 0:
				# pdb
				name = mvbObj.pdbData.name
				pdbFileName = mvbObj.pdbData.getFilename()
				chainName = mvbObj.chainData.name

				pdbFullPath = os.path.join(logic.tempFilePath, "pdb", pdbFileName)
				logic.gui.importDialog.fileLoadingArgs['largeRadius'] = hasattr(obj, 'largeRadius') or False
				logic.gui.importDialog.fileLoadingArgs['bioMT'] = hasattr(obj, 'bioMT') or False
				logic.gui.importDialog.previewPDB(source=pdbFullPath)

				chains = mvbObj.pdbMetaData.chaininfo

				for key,value in chains.items():
					chains[key] = False

				chainName = mvbObj.chainData.name

				if chainName in chains:
					chains[chainName] = True
				logic.gui.importDialog.chains = chains

				objList = logic.gui.importDialog.importMol(silent=True)
				if objList:
					for newObj in objList:
						newObj.color = mvbObj.color[:]
		# done with looping, update scene
		logic.outliner.updateModel()

