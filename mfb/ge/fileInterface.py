# import gamengine modules
from bge import logic
from bge import events
from bge import render

import json, base64, os, pprint, time, subprocess, pdb, hashlib

from . import restart
from .settings import *
from .helpers import *


def saveBrowse():
	''' show ui for saving'''
	try:
		filename = logic.filePath or browseFile(save = True, filetype='flipbook')
	except Exception as E:
		logic.logger.new(str(E))

	if filename:
		save(filename)
		logic.filePath = filename
	else:
		logic.logger.new('Saving Cancelled')


def loadBrowse():
	''' show ui for loading'''

	def reallyLoadBrowse():
		try:	
			filename = browseFile(filetype = 'flipbook')
		except Exception as E:
			logic.logger.new(str(E))
		
		if filename:
			load(filename)
			logic.filePath = None
		else:
			logic.logger.new('Loading Cancelled')

	def doDelayRestart():
		restart.reallyRestart()
		return False

	def saveRestart():
		saveBrowse()
		logic.registeredFunctions.append(doDelayRestart)

	def justRestart():
		logic.registeredFunctions.append(doDelayRestart)

		
	if logic.mvb.objects:
		msg = 'Loading a scene will delete any changes you made. Save before continue?'
		logic.gui.showModalConfirm(subject='Save Before Continue?', message=msg,
						verb="Save First", cancelVerb="Discard Change", action=saveRestart, cancelAction=justRestart)
	else:
		reallyLoadBrowse()
		

def save(path):
	''' entry point for saving to file'''
	blob = saveSession()
	fp = open(path, mode='w')
	success = toFile(blob, fp)
	if success:
		logic.logger.new("Saved session to disk")
		return path
	else:
		logic.logger.new("Error saving session to disk", 'WARNING')
		return False


def load(path=None, append=False):
	'''entry point for loading session from file'''
	fp = open(path)
	success = loadSession(fp)
	if success:
		logic.logger.new("Loaded session from disk")
		return path
	else:
		logic.logger.new("Error loading session from disk", 'WARNING')
		return False


def saveSession():
	''' cherry pick data from model and marshall them into a json-friendly format'''

	# save objs
	objects=[]
	for name, obj in logic.mvb.objects.items():
		if obj.inactive:
			continue	# do not save deleted object

		newObj = {}
		newObj['name'] = obj.name
		newObj['rot'] = [float(rot) for rot in obj.rot]
		newObj['loc'] = [float(loc) for loc in obj.loc]
		newObj['type'] = obj.type										# obj type (blobber, pdb, etc)
		newObj['scale'] = obj.scale										# only used by blobber
		newObj['largeRadius'] = obj.largeRadius							# import options
		newObj['bioMT'] = obj.bioMT										# import options
		#newObj['residueSequenceMarked'] = obj.residueSequenceMarked 	# todo
		newObj['drawMode'] = obj.drawMode
		newObj['color'] = obj.color
		newObj['shader'] = obj.shader

		if obj.type == 0:												# this is true for pdb objects
			newObj['pdbData'] = [obj.pdbData.name, obj.pdbData.getFilename(), obj.chainData.name]
		else:
			newObj['pdbData'] = obj.pdbData
		
		objects.append(newObj)

	# save animations
	slides=[]
	for slide in logic.mvb.slides:
		newSlide = {}
		newSlide['id'] = slide.id
		newSlide['time'] = slide.time
		newSlide['animeData'] = slide.animeData

		slides.append(newSlide)

	# save pdb blobs
	pdbs = {}
	for obj in objects:
		if obj['type'] != 0:
			continue

		pdbFileName = obj['pdbData'][1]
		pdbFullPath = os.path.join(logic.tempFilePath, "pdb", pdbFileName)

		try:
			fileContent = open(pdbFullPath).read()
		except Exception as E:
			logic.logger.new('Cannot include PDB file' + E, type='ERROR')
		else:
			pdbs[pdbFileName] = fileContent

	view = {}
	view['loc'] = [float(loc) for loc in logic.controllerObject.worldPosition]
	view['rot'] = logic.viewRotCurrent
	view['zoom'] = logic.viewZoomCurrent
	view['gateVisible'] = logic.gate.visible
	view['gateAR'] = logic.gate._arIndex

	env = {}
	env['useGrid'] = logic.scene.objects['Grid'].visible
	env['useSSAO'] = logic.controllerObject['ssao']
	env['bgColor'] = logic.mvb.bgColor
	env['bgColorFactor'] = logic.mvb.bgColorFactor
	env['bgImageStretch'] = logic.mvb.bgImageStretch
	
	if logic.mvb.bgImage:
		try:
			blob = open(logic.mvb.bgImage, mode='r+b').read()
			env['bgImage'] = base64.urlsafe_b64encode(blob).decode('ascii')
		except Exception as E:
			logic.logger.new('Cannot include bgImage' + E, type='ERROR')
			env['bgImage'] = None
	else:
		env['bgImage'] = None

	options = logic.options.datastore.copy()

	# deals with file ancestry
	dat = json.dumps(slides, sort_keys=True).encode()
	newFileID = hashlib.sha1(dat).hexdigest()
	if hasattr(logic, 'fileIDs'):
		if newFileID not in logic.fileIDs:
			logic.fileIDs.append(newFileID)
		else:
			pass
	else:
		logic.fileIDs = [newFileID]


	scene = {'name': logic.projectName,
			'version': 3,
			'objects': objects,
			'slides': slides,
			'pdbs': pdbs,
			'view': view,
			'env': env,
			'options': options,
			'fileIDs': logic.fileIDs,
			}
	
	return scene


def loadSession(fp):
	start = time.time()
	scene = json.load(fp)

	# check file version:
	if 'version' in scene:
		if int(scene['version']) > 3:
			logic.logger.new('File was saved with a newer version of the app.', type='WARNING')
			logic.logger.new('Please update Molecular Flipbook.', type='WARNING')
			return False

	# clean up previous scene
	# just clean up blobbers since regular proteins are kept
	for name, obj in logic.mvb.objects.items():
		if obj.type == 1:
			logic.mvb.deleteObject(obj)

	# write pdb
	for filename, content in scene['pdbs'].items():
		folder = os.path.join(logic.tempFilePath, "pdb")
		if not createPath(folder):
			logic.logger.new('Cannot create folder for writing PDB', type='ERROR')
			return False
		pdbFullPath = os.path.join(folder, filename)

		fp = open(pdbFullPath, mode='w')
		fp.write(content)
		fp.close()

	# load objects
	for obj in scene['objects']:
		#0 = normal. 1 = blobber. 2 = aux
		if obj['type'] == 0:
			if obj['name'] not in logic.mvb.objects:
				name, pdbFileName, chainName = obj['pdbData']
				pdbFullPath = os.path.join(logic.tempFilePath, "pdb", pdbFileName)
				logic.gui.importDialog.fileLoadingArgs['largeRadius'] = obj['largeRadius']
				logic.gui.importDialog.fileLoadingArgs['bioMT'] = obj['bioMT']
				logic.gui.importDialog.previewPDB(source=pdbFullPath)
				logic.gui.importDialog.importMol(silent=True)
			# else:
			# 	print ("pdb obj already imported")

		elif obj['type'] == 1:
			from . import OPCreate
			OPCreate.loadBlob(scale = obj['scale'], name=obj['name'])
		else:
			logic.logger.new("No handler for object type " + obj['type'], type='ERROR')

		mvbObj = logic.mvb.objects[obj['name']]
		mvbObj.rot = obj['rot']
		mvbObj.loc = obj['loc']
		mvbObj.drawMode = obj['drawMode']
		mvbObj.color = obj['color']
		mvbObj.shader = obj['shader']

	logic.outliner.updateModel()


	# load slides
	logic.mvb.activeSlide = 0
	logic.mvb.slides = []

	for slide in scene['slides']:
		logic.timeline.slideAdd(silent=True)
		newSlide = logic.mvb.slides[logic.mvb.activeSlide]
		# newSlide['id'] = slide.id
		newSlide.time = slide['time']
		newSlide.animeData = slide['animeData']
	
	logic.timeline.viewUpdate()
	
	# do another update
	logic.deferredFunctions.append(lambda: logic.timeline.viewUpdate())
	
	# load view
	view = scene['view']
	logic.controllerObject.worldPosition = view['loc']
	logic.viewRotTarget = view['rot']
	logic.viewZoomTarget = view['zoom']
	logic.gate.visible = view['gateVisible']
	logic.gate.ar = view['gateAR']
	logic.gate.ARSwitch(switch=False)


	# load env
	env = scene['env']
	logic.mvb.bgColor = env['bgColor']
	logic.mvb.bgColorFactor = env['bgColorFactor']
	logic.mvb.bgImageStretch = env['bgImageStretch']
	
	if env['bgImage']:
		folder = os.path.join(logic.tempFilePath, "background")
		if not createPath(folder):
			return False
		
		fpath = os.path.join(folder, 'extractedImage')
		fp = open(fpath, mode='wb')
		fp.write(base64.urlsafe_b64decode(env['bgImage']))
		fp.close()

		logic.mvb.bgImage = fpath
		from . import OPCamera
		OPCamera.updateTexture()
	else:
		logic.mvb.bgImage = None

	
	logic.scene.objects['Grid'].visible = env['useGrid']
	logic.controllerObject['ssao'] = env['useSSAO']

	logic.options.datastore = {}
	logic.options.datastore = scene['options']

	# file history
	logic.fileIDs = scene['fileIDs']

	# projectName
	logic.projectName = scene['name']

	return True

# -------------------
def toFile(blob, fp):
	''' handles the final serializing and saving to disk'''
	out = json.dumps(blob, indent=4, skipkeys=True)

	try:
		json.dump(blob, fp, indent=4, skipkeys=True)
	except:
		return False
	else:
		return True


def browseFile(save=False, filetype=None):
	"""access local file """
	
	logic.mouseExitHack = True


	# win32 code path, uses tkinter to invoke native file selector
	if 'win' in releaseOS:
		import tkinter
		from tkinter import filedialog
		root = tkinter.Tk()
		root.withdraw()
		if save:
			if filetype == 'flipbook':
				return filedialog.asksaveasfilename(defaultextension = '.flipbook', filetypes = [('Flipbook Session', '.flipbook'), ('All', '*')])
		else:
			if filetype == 'pdb':
				return filedialog.askopenfilename(filetypes = [('PDB', '.pdb'), ('All', '*')])
			elif filetype == 'flipbook':
				return filedialog.askopenfilename(filetypes = [('Flipbook Session', '.flipbook'), ('All', '*')])
			else:
				return filedialog.askopenfilename()


	# os x code path, uses externally called tkinter to avoid threading bug
	elif 'mac' in releaseOS:
		script = os.path.join(logic.basePath, 'ge', 'tkinterOSX.py')
		if save:
			if filetype == 'flipbook':
				stdout, stderr = subprocess.Popen(['python', script, 'save'], stdout=subprocess.PIPE).communicate()
				return stdout.decode('ascii').replace('\n', '')
		else:
			if filetype == 'pdb':
				stdout, stderr = subprocess.Popen(['python', script, 'openPDB'], stdout=subprocess.PIPE).communicate()
				return stdout.decode('ascii').replace('\n', '')
			elif filetype == 'flipbook':
				stdout, stderr = subprocess.Popen(['python', script, 'openFlipbook'], stdout=subprocess.PIPE).communicate()
				return stdout.decode('ascii').replace('\n', '')
			else:
				stdout, stderr = subprocess.Popen(['python', script, 'openAny'], stdout=subprocess.PIPE).communicate()
				return stdout.decode('ascii').replace('\n', '')
