# import gamengine modules
from bge import logic
from bge import events
from bge import render

# import mvb's own module
from . import bgui
from . import pdbLoader
from . import pdbFetcher
from . import pdbParser
from . import surfacer
from . import backbone
from . import fileInterface
from . import datastoreUtils
from .helpers import *
from .settings import *

import os, math, textwrap, time, logging, pdb


class ImportDialogUI():

	def __init__(self, guiSys):

		# common variables
		self.gui = guiSys
		self.panel = None

		self.chains = {}			# key: 'Letter', value: Boolean
		self.pdbFullPath = None		# directory location of local PDB
		self.childPID = None		# stores the Process ID of the child (second instance) process, None when no process is running
		self.thread = None			# stores the thread ID of a thread; otherwise, None upon termination
		self.thread2 = None			# stores the thread ID of a thread; otherwise, None upon termination
		self.mol = None
		self.molInfo = None
		self.fileLoadingArgs = {}

	@property
	def visible(self):
		'''toggle visibility of self - the import dialog'''
		if self.panel:
			return self.panel.visible
		else:
			return False

	@visible.setter
	def visible(self, value):
		'''toggle visibility of self - the import dialog'''
		if value:
			if self.panel:
				#move panel widget back to centre
				self.panel.options = self.panel.options | bgui.BGUI_CENTERED
			else:
				# create the UI on first use
				self.createUI()
			self.panel.visible = True
			self.createFolders()
			logic.pluggable.view.importDialogOn.notify()
		else:
			self.resetPreview()
			self.pdbid.text = 'PDB ID'
			self.pdbFullPath = None
			self.panel.visible = False
			# remove centering
			if self.panel.options & bgui.BGUI_CENTERED:
				self.panel.options = self.panel.options ^ bgui.BGUI_CENTERED
			self.panel.position = [-1000, -1000]

			if self.meshingThread in logic.registeredFunctions:
				logic.registeredFunctions.remove(self.meshingThread)
			if self.remoteLoadThread in logic.registeredFunctions:
				logic.registeredFunctions.remove(self.remoteLoadThread)
			logic.pluggable.view.importDialogOff.notify()


	def createUI(self):
		'''create the Import Dialog'''
		# Main Image held in Frame container, self.importDialog.
		self.panel = bgui.Image(self.gui, 'importDialog', themeRoot('importDialog.png'),size=[617,512],options=bgui.BGUI_CACHE|bgui.BGUI_MOVABLE|bgui.BGUI_CENTERED)
		self.panel.on_left_click = self.onClick

		self.importPlaceholder = bgui.Custom(self.panel, 'placeholder', size=[540, 64], pos=[45, 374], options=bgui.BGUI_NO_FOCUS)

		#browse local
		self.browseLocalBtn = bgui.ImageButton(self.panel, 'browseLocalBtn',size=[256,64],pos=[45,374],sub_theme="browselocalbutton")
		self.browseLocalBtn.on_left_release = self.onClick
		self.browseLocalBtn.tooltip = "Load PDB file from local disk"

		# fetch pdb
		self.fetchRemoteBtn = bgui.ImageButton(self.panel, 'fetchRemoteBtn',size=[170,64],pos=[410,374],sub_theme="fetchremotebutton")
		self.fetchRemoteBtn.on_left_release = self.onClick
		self.fetchRemoteBtn.tooltip = "Load PDB file from Internet"

		#pdbid
		self.pdbid = bgui.TextInput(self.panel, 'pdbid', "PDB ID", sub_theme="pdbid", size=[55, 32], pos=[330, 382+6])
		self.pdbid.on_activate = self.onActivate
		self.pdbid.on_enter_key = self.onClick
		self.pdbid.on_edit = self.resetPreview

		# structure summary container
		summarySize = [323, 200]
		summaryPos = [39, 145]
		self.summaryScroll = bgui.Scroll(self.panel, 'summaryScroll', pos=summaryPos, size=summarySize, actual = [1, 1])

		# structure summary info; child widgets positioned off of parent scroll widget
		self.lbl_pdbid = bgui.Label(self.summaryScroll, 'lbl_pdbid', text="PDB ID : ", offset=[-10, 20], sub_theme='whiteLabel', options=bgui.BGUI_LEFT|bgui.BGUI_TOP)
		self.lbl_pdbidVal = bgui.Label(self.summaryScroll, 'lbl_pdbidVal', text="", offset=[63, -20], sub_theme='whiteLabelSmall',options=bgui.BGUI_LEFT|bgui.BGUI_TOP)
		self.lbl_structure = bgui.Label(self.summaryScroll, 'lbl_structure', text="Structure Name : ", offset=[-10, 40], sub_theme='whiteLabel',options=bgui.BGUI_LEFT|bgui.BGUI_TOP)
		self.lbl_structureVal = bgui.Label(self.summaryScroll, 'lbl_structureVal', text="", offset=[114, -39], sub_theme='whiteLabelSmall',options=bgui.BGUI_LEFT|bgui.BGUI_TOP)
		self.lbl_detMethod = bgui.Label(self.summaryScroll, 'lbl_detMethod', text="Det. Method : ", offset=[-10, 60], sub_theme='whiteLabel',options=bgui.BGUI_LEFT|bgui.BGUI_TOP)
		self.lbl_detMethodVal = bgui.Label(self.summaryScroll, 'lbl_detMethodVal', text="", offset=[94, -59], sub_theme='whiteLabelSmall',options=bgui.BGUI_LEFT|bgui.BGUI_TOP)
		self.lbl_resoltn = bgui.Label(self.summaryScroll, 'lbl_resoltn', text="Resolution : ", offset=[-10, 80], sub_theme='whiteLabel',options=bgui.BGUI_LEFT|bgui.BGUI_TOP)
		self.lbl_resoltnVal = bgui.Label(self.summaryScroll, 'lbl_resoltnVal', text="", offset=[84, -79], sub_theme='whiteLabelSmall',options=bgui.BGUI_LEFT|bgui.BGUI_TOP)

		# chains info
		chainSize = [208, 200]
		chainPos = [371, 145]
		self.chainScroll = bgui.Scroll(self.panel, 'chainScroll', size=chainSize, pos=chainPos, actual = [1, 1])

		#import button
		self.loadPDBBtn = bgui.ImageButton(self.panel, 'loadPDBBtn',size=[238,61],pos=[200,50],sub_theme="loadPDBbutton")
		self.loadPDBBtn.on_left_release = self.onClick
		self.loadPDBBtn.tooltip = "Load PDB file into viewport"
		self.loadPDBBtn.visible = False

		self.bioMT = bgui.Checkbox(self.panel, "bioMT", text='use BIOMT', size=[80,15], pos=[45,110])
		self.bioMT.tooltip = 'Check to build a full biological assembly from the asymmetric unit.'
		self.bioMT.on_left_release = self.onClick
		self.bioMT.on_right_release = self.onClick
		if useDebug:
			self.bioMT.state = True
		self.largeRadius = bgui.Checkbox(self.panel, "largeRadius", text='use Large Solvent Radius', size=[160,15], pos=[160,110])
		self.largeRadius.tooltip = 'Check to use large detection radius for Solvent Excluded Surface computation. Prevent crashes for certain PDBs'
		self.largeRadius.on_left_release = self.onClick
		self.largeRadius.on_right_release = self.onClick
		self.center = bgui.Checkbox(self.panel, "center", text="Center PDB on Screen", size=[120,15], pos=[370,110])
		self.center.tooltip = 'Center PDB on Screen'
		self.center.on_left_release = self.onClick
		self.center.on_right_release = self.onClick
		self.center.state = True
		self.noCache = bgui.Checkbox(self.panel, "noCache", text="Ignore Cache", size=[80,15], pos=[45,80])
		self.noCache.tooltip = 'Check to ignore any previously cached PDB and geometry data. Slower, but more correct.'
		self.noCache.on_left_release = self.onClick
		self.noCache.on_right_release = self.onClick
		

		#close button
		self.importDialogClose = bgui.ImageButton(self.panel, 'importDialogClose', size=[24,24], pos=[570,466], sub_theme="close")
		self.importDialogClose.on_left_release = self.onClick

		# lookup PDB
		self.PDBurl = bgui.Label(self.panel, 'PDBurl', text="Lookup PDB >>", pos=[480,80], sub_theme="whiteLabelSmall")
		self.PDBurl.on_left_click = self.openSite

		# loading bar
		createBusyBar(self, size=[330,30], pos=[225,70])
		
		
	def openSite(self, widget):
		''' opens homepage in default browser'''
		logic.mouseExitHack = True
		import webbrowser
		webbrowser.open("http://www.pdb.org/")


	def onActivate(self, widget):
		'''handler for on_activate for pdbid text input'''
		if widget.text == 'PDB ID':
			widget.text = ''


	def onClick(self, widget):
		'''Generic handler for dealing with button clicks'''
		# set panel to movable
		if self.panel.options & bgui.BGUI_CENTERED:
			self.panel.position = [self.panel.parent.size[0]/2 - self.panel.size[0]/2, self.panel.parent.size[1]/2 - self.panel.size[1]/2]
			self.panel.options = self.panel.options ^ bgui.BGUI_CENTERED

		if widget.name == "browseLocalBtn":								#local fetch button
			self.pdbid.text = 'PDB ID'									# clear the online fetch to reduce user confusion
			self.resetPreview()
			self.loadPDBLocal()

		elif widget.name == "fetchRemoteBtn" or widget.name == "pdbid":	#remote fetch button
			self.resetPreview()
			self.loadPDBRemote()

		elif widget.name == 'bioMT' or widget.name == 'largeRadius' or widget.name == 'noCache':
			# redo preview because options have changed
			self.loadPDBRefresh()

		elif widget.name == "loadPDBBtn":								#load PDB button w/user options
			self.importMol()
			self.visible = False

		elif widget.name == "importDialogClose":						#reset entire panel after closing dialog
			self.visible = False


	def dupPDB(self, name):
		''' allows import of multiple identical PDBS'''
		pdbIDs = []
		for key, mvbObj in logic.mvb.objects.items():
			if mvbObj.type == 0:
				pdbID = mvbObj.pdbData.name
			else:
				pdbID = mvbObj.pdbData

			pdbIDs.append(pdbID)

		newName = datastoreUtils.incrementName(name, pdbIDs)
		return newName
		

	def loadPDBRemote(self):
		'''Download PDB from a remote address and call previewPDB()'''
		pdbid = self.pdbid.text.strip()
		# sanity check
		if len(pdbid) != 4:
			logic.logger.new("PDB ID is invalid", type = "ERROR")
		else:
			pdbfile = pdbid + ".pdb"
			cache = os.path.join(logic.tempFilePath, "pdb")
			self.pdbFullPath = os.path.join(cache, pdbfile)

			# fetch pdb & store in cache
			if os.path.exists(self.pdbFullPath):
				self.previewPDB()
			else:
				logic.logger.new("Fetching PDB from pdb.org")
				remoteaddr = "http://www.pdb.org/pdb/files/" + pdbid + ".pdb"
				self.thread = pdbFetcher.Fetch(pdbfile, self.pdbFullPath, remoteaddr)
				self.thread.start()
				logic.registeredFunctions.append(self.remoteLoadThread)


	def loadPDBLocal(self):
		'''Copy the PDB from the local file system and call previewPDB()'''
		
		self.pdbFullPath = os.path.normpath(fileInterface.browseFile(filetype = 'pdb'))

		if self.pdbFullPath and self.pdbFullPath[-4:].lower() == ".pdb":
			filename = os.path.basename(self.pdbFullPath)
			# copy to cache
			dest = os.path.join(logic.tempFilePath, "pdb")
			if 'mac' in releaseOS:
				os.system("cp %s %s" %(self.pdbFullPath, dest))
			elif 'win' in releaseOS:
				os.system("copy %s %s" %(self.pdbFullPath, dest))
			self.pdbFullPath = os.path.join(dest, filename)
			self.previewPDB()
		else:
			logic.logger.new("No PDB Loaded", type = "ERROR")


	def loadPDBRefresh(self):
		self.refresh = True
		self.resetPreview()
		self.previewPDB()


	def previewPDB(self, source=None):
		'''Parse PDB file and store info into datastore module.
		Create a digested preview for dialog box,
		and run surfacer module to generate mesh;
		source is set when the function is called from a non-gui setup'''

		if source:
			self.pdbFullPath = source
		else:
			logging.info("Previewing PDB:\t" + str(self.pdbFullPath))

		# deal with dup pdbs
		name = os.path.basename(self.pdbFullPath).split('.')[0]
		newName = self.dupPDB(name)
		if name != newName:
			head, tail = os.path.split(self.pdbFullPath)
			newPath = os.path.join(head, tail.replace(name, newName))

			if 'mac' in releaseOS:
				os.system("cp %s %s" %(self.pdbFullPath, newPath))
			elif 'win' in releaseOS:
				os.system("copy %s %s" %(self.pdbFullPath, newPath))

			self.pdbFullPath = newPath


		try:
			start = time.time()
			self.mol = pdbParser.getMol(self.pdbFullPath)
			logging.info("MolKit Time:\t" + str(time.time()-start))
			start = time.time()
			self.molInfo = pdbParser.getMolInfo(self.pdbFullPath, self.mol)
			logging.info("MolInfo Time:\t" + str(time.time()-start))
		except Exception as E:
			logic.logger.new("Cannot parse PDB file.", type = "ERROR")
			logic.logger.new(str(E), type = "ERROR")
			return

		
		if hasattr(self, 'bioMT') and self.bioMT.state:
			# parse BIOMT
			logging.info("Parsing BioMT data...")
			with open(self.pdbFullPath) as f:
				content = f.read()

			remarks = [x for x in content.split('\n') if x.startswith('REMARK 350   BIOMT')]
			matrix={}

			for line in remarks:
				spl = line.split()
				symOpNum = int(spl[3])				#id of matrice

				if symOpNum not in matrix:
					matrix[symOpNum] = []
				
				symx = float(spl[4])
				symy = float(spl[5])
				symz = float(spl[6])
				tr = float(spl[7])

				matrix[symOpNum].append([symx,symy,symz,tr])

			self.matrix = matrix
		else:
			self.matrix = None

		try:
			title,chaininfo,detmethod, resolution, authors, articlename, journal, issn, doi = self.molInfo
			pdbid = self.mol.name
			if source:
				self.createPreviewBG(chaininfo)
			else:
				self.createPreview(title, chaininfo, detmethod, resolution, pdbid)
		except Exception as E:
			logic.logger.new("Cannot generate PDB preview from metadata.", type = "ERROR")
			logic.logger.new(str(E), type = "ERROR")
			return

		logic.pluggable.loader.validFile.notify()

		validCacheFlag = os.path.join(logic.tempFilePath, 'geometry', pdbid.lower(), 'validCache')
		if os.access(validCacheFlag, os.R_OK):
			validCache = True
		else:
			validCache = False

		# check for force refresh
		if hasattr(self, 'refresh'):
			validCache = validCache and (not self.refresh)
			del self.refresh

		if useCache and validCache:
			meshFolder = os.path.join(logic.tempFilePath, 'geometry', pdbid.lower())
			folderOk = createPath(meshFolder)
			meshPath = os.path.join(meshFolder, "geometry.blend")

			if os.access(meshPath, os.R_OK):
				logging.info("Skipping meshing, Cached at: " + str(meshPath))
				self.meshingThreadDone()
				return

		try:
			# generate backbone
			logging.info("Making Backbone")
			backbone.Build(pdbid, self.pdbFullPath, logic.basePath, logic.tempFilePath, self.mol, self.matrix)
			logging.info("done making backbone")

			# generate surface
			logging.info("Making surface")

			if hasattr(self, 'largeRadius'):
				largeRadius = self.largeRadius.state
			else:
				largeRadius = self.fileLoadingArgs['largeRadius']

			self.thread2 = surfacer.BuildSurface(pdbid, self.pdbFullPath, logic.basePath, logic.tempFilePath, self.mol, defaultSurfacing, largeRadius)
			
			if source:
				self.thread2.run()
			else:
				self.thread2.start()

			logic.registeredFunctions.append(self.meshingThread)

		except Exception as E:
			logic.logger.new("Cannot generate mesh.", type = "ERROR")
			logic.logger.new(str(E), type = "ERROR")

		logging.info("Finished preprocessing PDB")


	def resetPreview(self, widget=None):
		''' Reset variables for digested Preview in dialog box'''
		for key in self.chains.keys():
			try:
				exec("self.importdialog_checkbox_chain_%s.kill()" %key)
			except:
				# no UI to delete, probably because it was called from the BG last time
				pass 

		# move widgets positioned off of parent scroll widget
		self.lbl_pdbid.offset = [-10,20]
		self.lbl_structure.offset = [-10,40]
		self.lbl_detMethod.offset = [-10,60]
		self.lbl_resoltn.offset = [-10,80]
		self.lbl_pdbidVal.offset = [63,-20]
		self.lbl_structureVal.offset = [114,-39]
		self.lbl_detMethodVal.offset = [94, -59]
		self.lbl_resoltnVal.offset = [84, -79]
		self.lbl_pdbidVal.text = ''
		self.lbl_detMethodVal.text = ''
		self.lbl_resoltnVal.text = ''
		self.lbl_structureVal.text = ''
		self.chains = {}

		self.loadPDBBtn.visible = False


	def offsetSummaryInfo(self, textlength):
		'''helper method to layout summary labels and values of det. method & resoluton'''
		textlength = int(textlength)

		self.lbl_detMethod.offset[1] = (self.lbl_detMethod.offset[1]-(10+10*textlength))
		self.lbl_detMethodVal.offset[1] = (self.lbl_detMethodVal.offset[1]-(10+10*textlength))

		self.lbl_resoltn.offset[1] = (self.lbl_detMethod.offset[1]-25)
		self.lbl_resoltnVal.offset[1] = (self.lbl_detMethod.offset[1]-25)


	def createPreviewBG(self, chaininfo):
		'''Condensed version of resetPreview and createPreview for use in non-gui circumstances'''
		self.chains = {}
		for key,value in chaininfo.items():
			self.chains[key] = True


	def createPreview(self, title, chaininfo, detmethod, resolution, pdbid):
		'''Preview displayed in Import Dialog window'''

		# checkbox
		sx = 100
		sy = 20
		posx = 10 	# pertaining to chain scroll area
		posy = -20 	# pertaining to chain scroll area

		# move widgets back into view on parent scroll widget
		self.lbl_pdbid.offset = [10,-20]
		self.lbl_structure.offset = [10,-40]
		self.lbl_detMethod.offset = [10,-60]
		self.lbl_resoltn.offset = [10,-80]

		# compute TextBox Widget for structure name; adjust det. method and
		# resolution labels and textblock widgets appropriately
		lblStructureLines = textwrap.wrap(title.title(), 35)
		structureLines = ''
		for line in lblStructureLines:
			structureLines = structureLines + line + '\n'

		# number of text lines for structure summary
		self.lbl_structureVal.text = structureLines

		# helper method: adjust Preview labels and summary information
		self.offsetSummaryInfo(len(lblStructureLines))

		self.lbl_pdbidVal.text = pdbid
		self.lbl_detMethodVal.text = detmethod.title()
		self.lbl_resoltnVal.text = resolution.title().strip()

		# set Structure Summary Scroll area based on the length in terms of lines for a given PDB file
		self.summaryScroll.actual[1] = math.ceil(math.fabs(self.lbl_resoltnVal.offset[1])/self.summaryScroll.size[1]*self.summaryScroll.actual[1])

		# set up checkbox variables for each chain contained in Import Preview Dialog box
		for key,value in chaininfo.items():

			titleVal = key + ' : ' +  value.title()
			lines = textwrap.wrap(titleVal,30)
			newtitleVal = ''
			for line in lines:
				newtitleVal = newtitleVal + line + '\n'


			exec("self.importdialog_checkbox_chain_%s = bgui.Checkbox(self.chainScroll, 'importdialog_checkbox_chain_%s', text='', size=[sx,sy], offset=[posx, posy], sub_theme='small', options=bgui.BGUI_TOP|bgui.BGUI_LEFT)" %(key,key))
			exec("self.importdialog_checkbox_chain_%s.state = True" %(key))
			exec("self.tempChain = self.importdialog_checkbox_chain_%s" % key)		# avoid unexpected escape chars in string
			self.tempChain.text = newtitleVal
			self.chains[key] = True
			exec("self.importdialog_checkbox_chain_%s.on_left_click = self.onCheck" %key)
			exec("self.importdialog_checkbox_chain_%s.on_right_click = self.onCheck" %key)
			if len(lines) <= 1:
				posy = (posy-30)
			elif len(lines) == 2:
				posy = (posy-40)
			elif len(lines) == 2:
				posy = (posy-50)
			elif len(lines) == 3:
				posy = (posy-60)
			elif len(lines) == 4:
				posy = (posy-70)
			elif len(lines) == 5:
				posy = (posy-80)
			elif len(lines) == 6:
				posy = (posy-90)
			else:
				posy = (posy-100)

		# set chain Scroll area based on the number of chains for a given PDB file
		self.chainScroll.actual[1] = math.ceil(math.fabs(posy)/self.chainScroll.size[1]*self.chainScroll.actual[1])


	def onCheck(self, widget):
		'''Change the state of a checkbox and track its state in the dictionary variable, chains'''
		key = widget.name.split("_")[-1]
		exec("logic.gui.importDialog.chains['%s'] = not %s" %(key, widget.state))


	def createFolders(self):
		''' temp children folders '''
		children = ['pdb', 'geometry']
		for child in children:
			path = os.path.join(logic.tempFilePath, child)
			if not createPath(path):
				logging.error("Cannot create path: " + str(path))


	def importMol(self, silent=False):
		'''do the real import'''
		meshPath = os.path.join(logic.tempFilePath, "geometry", self.mol.name, "geometry.blend")

		try:
			if hasattr(self, 'largeRadius'):
				largeRadius = self.largeRadius
			else:
				largeRadius = self.fileLoadingArgs['largeRadius']

			result = pdbLoader.importGeometry(meshPath, self.mol, self.molInfo, availableChains=self.chains, matrix = self.matrix, largeRadius = largeRadius, centerToScreen = self.center.state)
			if result and not silent:
				logic.outliner.updateModel()
			if result:
				return result
		except Exception as E:
			logic.logger.new("Cannot import PDB", type="ERROR")
			logging.error('Cannot import PDB: '+ str(E))


	def remoteLoadThread(self):
		''' tracks the completion of the preview thread '''
		if self.thread:
			if not self.thread.isAlive():
				self.thread = None
				updateBusyBar(self, None)
				if os.path.exists(self.pdbFullPath):
					self.previewPDB()
				return False
			else:
				updateBusyBar(self, time.time())
		return True

	def meshingThread(self):
		''' tracks the completion of the meshing thread '''
		if self.thread2:
			if not self.thread2.isAlive():
				self.meshingThreadDone()
				return False
			else:
				try:
					updateBusyBar(self, time.time())
				except:
					pass
				return True
		return True

	def meshingThreadDone(self):
		self.thread2 = None
		try:
			self.loadPDBBtn.visible = True
			updateBusyBar(self, None)
		except:
			pass

def init(guiSys):
	'''instantiate the UI singleton'''
	return ImportDialogUI(guiSys)

