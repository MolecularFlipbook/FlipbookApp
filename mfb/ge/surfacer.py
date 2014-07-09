import threading, os, sys, logging, subprocess, pdb, imp, math

from .settings import *
from .helpers import *
from bge import logic


class BuildSurface(threading.Thread):

	def __init__(self, pdbid, pdbFullPath, basePath, tempFilePath, mol, method, largeRadius):
		self.pdbid = pdbid
		self.pdbFullPath = pdbFullPath
		self.basePath = basePath
		self.tempFilePath = tempFilePath
		self.mol = mol
		self.method = method
		self.largeRadius = largeRadius
		threading.Thread.__init__(self)

	def run(self):

		if 'msms' in self.method:
			import mslib
		if 'cms' in self.method:
			from . import coarsems
			gridsize = 20 			# value taken from epmv
			isovalue = 3.0
			resolution = -0.6

		chains = []
		chainsCenter = {}
		outputFolder = os.path.join(self.tempFilePath, 'geometry', self.pdbid.lower())

		for chain in self.mol.chains:
			selectedAtoms = chain.getAtoms()
			chainID = chain.name

			# filter out HETATOMS
			for a in selectedAtoms:
				if a.hetatm:
					selectedAtoms.remove(a)


			if 'msms' in self.method:
				# compute msms surface and write geometry to disk
				surf = mslib.MSMS(coords=selectedAtoms.coords, radii=selectedAtoms.vdwRadius)
			
				if self.largeRadius:
					r = 7.0
				else:
					r = 2.0
				surf.compute(probe_radius = r, density = 0.3)
				if not os.path.isdir(outputFolder):
					os.mkdir(outputFolder)
				outputFile = os.path.join(outputFolder, str(ord(chainID)))
				surf.write_triangulation(outputFile)
				logging.info('Generated MSMS '+str(chainID))



			if 'cms' in self.method:
				# compute coarse molecular surface and write to disk
				vert, face = coarsems.coarseMolSurface(selectedAtoms,[gridsize,gridsize,gridsize], name=chainID)
				if not os.path.isdir(outputFolder):
					os.mkdir(outputFolder)
				outputFile = os.path.join(outputFolder, "cms"+str(ord(chainID)))
				vert.dump(outputFile+".vert")
				face.dump(outputFile+".face")
				logging.info('Generated CMS '+str(chainID))

			chains += chainID

			# compute and store chain center
			x,y,z = chain.getCenter()
			chainsCenter[chainID] = [float(x), float(y), float(z)]


		# use previous backbone file
		blend = os.path.join(self.tempFilePath, 'geometry', self.pdbid.lower(), "geometry.blend")
		script = os.path.join(self.basePath, "creator", "surfaceGenerator.py")
		cache =	os.path.join(self.tempFilePath, 'geometry')
		pdbid = self.pdbid
		chains = " ".join(chains)

		arg = [cache, pdbid, chains, self.method]
		call = [logic.binaryBlenderPath, blend, '--background', '--python', script, '--', cache, pdbid, chains, self.method]
		callBinary = " ".join(call)

		try:

			subprocess.call(call)
		except:
				logic.logger.new("Unable to generate surface", type="ERROR")
				logging.exception("Unable to generate surface")
