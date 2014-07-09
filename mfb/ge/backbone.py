import pdb
import os
import logging
import pickle
import subprocess

from bge import logic

from .settings import *
from .helpers import *

def Build(pdbid, pdbFullPath, basePath, tempFilePath, mol, matrix, partialMol=None, method = 'simple'):

	if method == 'simple':

		chains = []
		chainsCenter = {}
		outputFolder = os.path.join(tempFilePath, 'geometry', pdbid.lower())

		if mol:
			for chain in mol.chains:
				selectedAtoms = chain.getAtoms()
				chainID = chain.name

				# filter out HETATOMS
				for a in selectedAtoms:
					if a.hetatm:
						selectedAtoms.remove(a)

				# compute and store chain center
				x,y,z = chain.getCenter()
				chainsCenter[chainID] = [float(x), float(y), float(z)]

				ca = []

				for atom in selectedAtoms:
					# use alpha carbon
					if atom.name.upper() == 'CA':
						ca.append(atom._coords[0])

				if not ca:
					logging.warning("Backbone.py: No Alpha Carbon found, possibly dna")
					# use phosphorus
					for atom in selectedAtoms:
						if atom.name.upper() == 'P':
							ca.append(atom._coords[0])

				if not ca:
					logging.warning("Backbone.py: Not dna either")


				# write chain center data to file
				if not os.path.isdir(outputFolder):
					os.makedirs(outputFolder)
				outputFile = os.path.join(outputFolder, str(ord(chainID))+".backbone")

				fp = open(outputFile, mode='wb')
				pickle.dump(ca, fp)
				fp.close()


				chains += chainID

		elif partialMol:
			...

		else:
			raise Exception('Unsupported Input')


		# write chain center data to file
		fp = open(os.path.join(outputFolder, "centers"), mode='wb')
		pickle.dump(chainsCenter, fp)
		fp.close()

		# write out matrix
		outputFile = os.path.join(outputFolder, 'matrix')
		fp = open(outputFile, mode='wb')
		pickle.dump(matrix, fp)
		fp.close()


		# call blender
		binary = logic.binaryBlenderPath
		blend = os.path.join(basePath, "creator", "blank.blend")
		script = os.path.join(basePath, "creator", "boneGenerator.py")
		cache =	os.path.join(tempFilePath, 'geometry')
		chains = " ".join(chains)

		#arg = [cache, pdbid, chains, method]
		call = [binary, blend, '--background', '--python', script, '--', cache, pdbid, chains, method]
		callBinary = " ".join(call)

		try:
			subprocess.call(call)
		except:
			raise
			logic.logger.new("Unable to generate backbone geometry", type="ERROR")
			logging.exception("Unable to generate backbone geometry")
