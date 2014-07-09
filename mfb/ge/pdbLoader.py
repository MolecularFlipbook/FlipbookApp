# import gamengine modules
from bge import logic
from bge import events
from bge import render
import mathutils

# import mvb modules
from . import shader
from .settings import *

from . import datastoreUtils

import sys, os, pickle, logging, pdb


def importGeometry(meshFullPath, mol=None, molInfo=None, template = None, name="", scale=None, availableChains=None, matrix = None, largeRadius = False, centerToScreen = True):
	'''Load mesh into the GE'''
	# get pdb id
	if template:
		pdbid = name
	else:
		pdbid = mol.name.lower()


	# open blend file to load in mesh data
	f = open(meshFullPath, 'rb')
	data = f.read()
	f.close()

	try:
		logic.LibLoad(pdbid, 'Mesh', data)
	except Exception as E:
		if "file already open" in str(E):
			print("Warning: Lib Mesh already loaded")
		else:
			# file not open, but other errors
			logic.logger.new("Error loading Mesh.", type="ERROR")
			return False

	cameraPivot = logic.controllerObject

	if scale: # incoming is dimensions in nm
		scaling = scale
	else:
		scaling = [0.1, 0.1, 0.1] 		# assuming incoming model is in Ag (i.e. 1Blender Unit == 1 ang)

	objList = []
	if template:
		# get template obj, and use libLoad to replace the mesh of that object
		parentObj = "template"+str(logic.objCounter)			# because KX_Object.physicsProperty is messed up
		logic.objCounter += 1

		newObj = logic.scene.addObject(parentObj, cameraPivot, 0)

		# re-center
		np = [0,0,0]
		op = newObj.position
		newObj.position = [op[0]+np[0]*scaling[0], op[1]+np[1]*scaling[1], op[2]+np[2]*scaling[2]]

		try:
			newObj.replaceMesh(template)
		except Exception as E:
			logging.error(E)
			newObj.endObject()
			logic.logger.new("%s not imported" %(pdbid), "ERROR")
		else:
			newObj.worldScale = scaling							# reset for more predictable behavior
			newObj.worldOrientation = [0.0,0.0,0.0]				# reset for more predictable behavior
			newObj.reinstancePhysicsMesh()						# recalc physics
			newObj["name"] = name								# this, because KX_object.name is read-only

			# add pdb object and its data to module, datastore
			obj = logic.mvb.addObject(name, newObj, objType=1, molObj=name, scale=scale)
			obj.ribbonMesh = template
			obj.fineSurfaceMesh = template
			obj.surfaceMesh = template

			# apply default shader
			shader.initProtein(newObj, "default")

			logic.logger.new("Added to scene: " + str(name))
			objList.append(obj)
	else:
		# load real pdb surfaces
		parDir = os.path.dirname(meshFullPath)
		fp = open(os.path.join(parDir, "centers"), mode='rb')
		chainsCenter = pickle.load(fp)

		# make sure we have enough free object
		counter = 0
		for (key,visible) in availableChains.items():
			if visible:
				if matrix:
					counter += len(matrix)
				else:
					counter += 1
		if logic.objCounter + counter > maxObject:
			logic.logger.new(str(counter)+" is too many objects in scene", "ERROR")
			return False

		delayedError = []
		delayedOkay = []

		# prepare group name
		usedParentNames =  [obj.parent for name, obj in logic.mvb.objects.items()]
		parentName = datastoreUtils.incrementName(pdbid, usedParentNames)

		# loop through all chains
		for (key,visible) in availableChains.items():

			if visible:
				if matrix:
					for i, transform in matrix.items():

						# get template obj, and use libLoad to replace the mesh of that object
						parentObj = "template"+str(logic.objCounter)			# this, because KX_Object.physicsProperty is messed up
						logic.objCounter += 1

						cmsMeshname = pdbid + '_' + key + '_cms'
						
						newObj = logic.scene.addObject(parentObj, cameraPivot, 0)
			
						# transform
						mat = mathutils.Matrix()
						mat[0] = transform[0]
						mat[1] = transform[1]
						mat[2] = transform[2]
						loc = mat.to_translation()
						rot = mat.to_euler()

						op = loc
						newObj.position = [op[0]*scaling[0], op[1]*scaling[1], op[2]*scaling[2]]
						newObj.worldOrientation = rot

						failed = False

						try:
							newObj.replaceMesh(cmsMeshname)
						except Exception as E:
							logging.warning(E)
							failed = True

						if failed:
							newObj.endObject()
							delayedError.append("%s:%s not imported" %(pdbid, key))
						else:
							newObj.worldScale = scaling								# reset for more predictable behavior
							newObj.reinstancePhysicsMesh()							# recalc physics

							chain = None
							for c in mol.chains:
								if key == c.name:
									chain = c
							if not chain:
								logging.warning("Matching chain PDB data cannot be found")

							# add pdb object and its data to module, datastore
							name = pdbid + '_' + key
							name = datastoreUtils.incrementName(name, logic.mvb.objects)
							
							obj = logic.mvb.addObject(name, newObj, objType=0, molObj = mol, chainObj = chain, molInfo = molInfo, parent=parentName)
							obj.SESLargeRadius = largeRadius
							obj.ribbonMesh = cmsMeshname
							obj.fineSurfaceMesh = cmsMeshname
							obj.surfaceMesh = cmsMeshname

							# apply default shader
							shader.initProtein(newObj, "default")
							delayedOkay.append("Added to scene: " + str(name))

							obj.matrix = matrix


				else:
					# get template obj, and use libLoad to replace the mesh of that object
					parentObj = "template"+str(logic.objCounter)			# this, because KX_Object.physicsProperty is messed up
					logic.objCounter += 1

					msmsMeshname = pdbid + '_' + key + '_msms'
					cmsMeshname = pdbid + '_' + key + '_cms'
					ribbonMeshname = pdbid + '_' + key + '_bb'
					
					
					newObj = logic.scene.addObject(parentObj, cameraPivot, 0)
					
					# re-center
					np = chainsCenter[key]
					op = newObj.position
					
					if centerToScreen:
						newObj.position = [op[0]+np[0]*scaling[0], op[1]+np[1]*scaling[1], op[2]+np[2]*scaling[2]]
					else:
						newObj.position = [np[0]*scaling[0], np[1]*scaling[1], np[2]*scaling[2]]


					failed = False

					try:
						newObj.replaceMesh(msmsMeshname)
					except Exception as E:
						logging.warning(E)
						failed = True

					if failed:
						try:
							newObj.replaceMesh(cmsMeshname)
							failed = False
						except Exception as E:
							logging.warning(E)
							failed = True

					if failed:
						try:
							newObj.replaceMesh(ribbonMeshname)
							failed = False
						except Exception as E:
							logging.warning(E)
							failed = True

					if failed:
						newObj.endObject()
						delayedError.append("%s:%s not imported" %(pdbid, key))
					else:
						newObj.worldScale = scaling			# reset for more predictable behavior
						newObj.worldOrientation = [0.0,0.0,0.0]					# reset for more predictable behavior
						newObj.reinstancePhysicsMesh()							# recalc physics

						chain = None
						for c in mol.chains:
							if key == c.name:
								chain = c
						if not chain:
							logging.warning("Matching chain PDB data cannot be found")

						# add pdb object and its data to module, datastore
						name = pdbid + '_' + key
						name = datastoreUtils.incrementName(name, logic.mvb.objects)
						
						obj = logic.mvb.addObject(name, newObj, objType=0, molObj = mol, chainObj = chain, molInfo = molInfo, parent=parentName)
						obj.SESLargeRadius = largeRadius
						obj.ribbonMesh = ribbonMeshname
						obj.fineSurfaceMesh = msmsMeshname
						obj.surfaceMesh = cmsMeshname

						# apply default shader
						shader.initProtein(newObj, "default")
						delayedOkay.append("Added to scene: " + str(name))

						objList.append(obj)

		for msg in delayedOkay:
			logic.logger.new(msg)

		for error in delayedError:
			logic.logger.new(error, "ERROR")

		if delayedError:
			logic.pluggable.loader.loadPDBError.notify()
		else:
			# no error:
			logic.pluggable.loader.loadPDB.notify()
			
			# mark cache as good
			parDir = os.path.dirname(meshFullPath)
			filePath = os.path.join(parDir, 'validCache')
			open(filePath, 'a').close()


	logic.gui.showFullUI()
	logic.mvb.slides[logic.mvb.activeSlide].capture()
	
	return objList