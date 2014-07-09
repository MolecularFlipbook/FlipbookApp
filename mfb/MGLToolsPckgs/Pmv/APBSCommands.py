## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

# An Adaptive Poisson-Boltzmann Solver Graphic User Interface for the Python 
# Molecule Viewer: (APBS GUI for PMV)
# Authors: Hovig Bayandorian, Jessica Swanson, Sophie Coon, Michel Sanner, 
# Sargis Dallakyan (sargis@scripps.edu)

#$Header: /opt/cvs/python/packages/share1.5/Pmv/APBSCommands.py,v 1.176.2.2 2011/05/20 21:25:44 sargis Exp $
#
#$Id: APBSCommands.py,v 1.176.2.2 2011/05/20 21:25:44 sargis Exp $

""" GUI for Adaptive Poisson-Boltzmann Solver 

Minimal documentation follows. 
Consult APBS or PMV documentation for more detail. 
More documentation is planned for later releases.

How to set up an APBS run:

1. (Calculation tab) There are three types of calculations available:
   electrostatic potential, binding energy, and solvation energy.
   Select whichever is of interest.
2. (Calculation tab) Under Molecules, select PQR files corresponding to
   the molecules of interest. Note that binding energy requires three PQRs:
   one for the complex, and one for each compound.
3. (Grid tab) Autocenter and Autosize generate grid parameters based on
   the current selection in PMV. You may also manually set these parameters.
   It is wise to check that your machine has the system resources required to
   perform the run.
4. (Physics tab) Enter the ions of interest and change the listed parameters
   as desired.
5. (Calculation tab) All files will be stored in the specified project folder.
   Unique project folder names are automatically generated.
6. (Calculation tab) If you wish to modify the the run you created in the GUI
   later, save the profile.
7. (Calculation tab) To run APBS separately from the GUI, use the write APBS
   parameter file button, which writes to the project folder. Then call apbs
   (in say, a shell) on that file.
8. (Calculation tab) Run APBS!
""" 

import string, os, pickle, sys, threading, select, time, shutil
import numpy.oldnumeric as Numeric
import Tkinter, Pmw

from mglutil.gui.InputForm.Tk.gui import InputFormDescr, InputForm, \
CallBackFunction
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import LoadButton, \
SaveButton, SliderWidget, ExtendedSliderWidget
from mglutil.gui.BasicWidgets.Tk.progressBar import ProgressBar
from mglutil.util.callback import CallBackFunction
from mglutil.util.misc import ensureFontCase

from Pmv.mvCommand import MVCommand
from ViewerFramework.VFCommand import CommandGUI
from MolKit.pdbParser import PQRParser
from MolKit.molecule import Atom, MoleculeSet

import MolKit
import tkMessageBox

global APBS_ssl 
APBS_ssl = False # Flags whether to run Secured APBS Web Services 
from mglutil.util.packageFilePath import getResourceFolderWithVersion
ResourceFolder = getResourceFolderWithVersion()
#Proxy retrieved  from the GAMA service
if ResourceFolder is not None:
    APBS_proxy = ResourceFolder + os.sep + 'ws' + os.sep + 'proxy_gama'
else:
    APBS_proxy = None

def closestMatch(value, _set):
    """Returns an element of the set that is closest to the supplied value"""
    a = 0
    element = _set[0]
    while(a<len(_set)):
        if((_set[a]-value)*(_set[a]-value)<(element-value)*(element-value)):
            element=_set[a]
        a = a + 1
    return element

PROFILES = ('Default',)

from MolKit.APBSParameters import *

try:
    import sys, webbrowser, urllib, httplib

    APBSservicesFound = True
    from mglutil.web.services.AppService_client import AppServiceLocator, launchJobRequest, \
    getOutputsRequest, queryStatusRequest
    from mglutil.web.services.AppService_types import ns0
    class APBSCmdToWebService:
        """
        This object takes an APBSParams instance the Pmv.APBSCommands.py
        """
        def __init__(self, params, mol_1, mol_2 = None, _complex = None):
            """
            Constructor for class APBSCmdToWebService
            params is APBSPrams instance
            mol_1,mol_2 and complex are molecule instances
            Parallel_flag used to indicate parallel mode
            npx npy npz are number of processors in x-, y- and z-directions 
            ofrac is the amount of overlap between processor meshes
            """
            # set the parameters for the request
            self.req = launchJobRequest()
                
            inputFiles = []     
            
            input_molecule1 = ns0.InputFileType_Def('inputFile')
            input_molecule1._name = os.path.split(params.molecule1Path)[-1]
            input_molecule1._contents = open(params.molecule1Path).read()
            inputFiles.append(input_molecule1)
            
            if mol_2:
                input_molecule2 = ns0.InputFileType_Def()
                input_molecule2._name = os.path.split(params.molecule2Path)[-1]
                input_molecule2._contents = open(params.molecule2Path).read() 
                inputFiles.append(input_molecule2)
                if not _complex:
                    import warnings
                    warnings.warn("Complex is missing!")
                    return                
                input_complex = ns0.InputFileType_Def()
                input_complex._name = os.path.split(params.complexPath)[-1]
                input_complex._contents = open(params.complexPath).read() 
                inputFiles.append(input_complex)
            
            apbs_input = "apbs-input-file.apbs"
            apbs_input_path = params.projectFolder + os.path.sep + apbs_input
            params.molecule1Path = os.path.basename(params.molecule1Path)
            if mol_2:
                params.molecule2Path = os.path.basename(params.molecule2Path)
                params.complexPath = os.path.basename(params.complexPath)            
                
            params.SaveAPBSInput(apbs_input_path)
            input_apbs = ns0.InputFileType_Def('inputFile')
            input_apbs._name = apbs_input
            input_apbs._contents = open(apbs_input_path).read()
            inputFiles.append(input_apbs)
            
            self.req._argList = apbs_input

            self.req._inputFile = inputFiles
            
        def run(self, portAddress):
            """Runs APBS through Web Services"""
            # retrieve a reference to the remote port
            import httplib
            self.appLocator = AppServiceLocator()
            global APBS_ssl
            if APBS_ssl:
                self.appServicePort = self.appLocator.getAppServicePortType(
                                  portAddress, 
                                  ssl = 1, cert_file = APBS_proxy,  
                                  key_file = APBS_proxy, transport=httplib.HTTPSConnection)
            else:
                self.appServicePort = self.appLocator.getAppServicePort(
                                  portAddress)
            # make remote invocation

            resp = self.appServicePort.launchJob(self.req)
            self.JobID = resp._jobID
            return resp
            
except:
    APBSservicesFound = False

state_GUI = 'disabled'
blinker = 0
class APBSSetup(MVCommand):
    """APBSSetup setups all necessary parameters for Adaptive Poisson-Boltzmann 
Solver (APBS)\n
    \nPackage : Pmv
    \nModule  : APBSCommands
    \nClass   : APBSSetup
    \nCommand name : APBSSetup
    \nSynopsis:\n
    None <--- APBSSetup(**kw)\n
    \nDescription:\n
   Pmv-->APBS-->Setup creates Pmw.NoteBook with three tabbed pages:\n
   Calculation, Grid and Physics.
    
   Calculation page contains the following groups: 
        
   Mathematics - is used to setup up Calculation type (kw['calculationType']),
   Poisson-Boltzmann equation type (kw['pbeType']), Boundary conditions 
   (kw['boundaryConditions']),Charge discretization (kw['chargeDiscretization'])
   Surface-based coefficients (kw['surfaceCalculation']), and Spline window in
   Angstroms (kw['splineWindow'], present only when surfaceCalculation is set to 
   'Spline-based')
   Molecules - allows to select molecule(s)
   Output - sets output file formats
   Profiles - is used to add, remove, load, save and run different profiles
   APBS Web Services - is present only when APBSService_services module is 
   installed. It allows APBS to be run remotely
   
   Grid page contains the following groups:
   
   General - lets you select number of grid point along X, Y and Z directions
   Coarse Grid - allows changing the length and the center of the coarse grid. 
   It also allows to autoceter, autosize as well as visualize the coarse grid.
   Fine Grid - dos the same for the fine grid
   System Resources - shows total grid point and memory to be allocated for APBS
    
   Grid page contains the following groups:
       
   Parameters - allows to change protein and solevent dielectric constants, 
   solvent radius and system temperature
   Ions - allows to add and/or remove different ions
   """
    def __init__(self, func=None):
        """Constructor for class APBSSetup"""
        MVCommand.__init__(self)
        self.params = APBSParams()
        self.cmp_APBSParams = APBSParams()
        self.flag_grid_changed = False
        try:
            self.RememberLogin_var = Tkinter.BooleanVar()
            self.salt_var =Tkinter.BooleanVar()
            self.salt_var.set(1)
        except:
            self.RememberLogin_var = False
            self.salt_var = True

    def doit(self,*args, **kw):
        """doit function"""
        self.cmp_APBSParams.Set(**kw)

    def __call__(self, **kw):
        """Call method"""
        self.params.Set(**kw)
        self.refreshAll()

    def onAddObjectToViewer(self, object):
        """Called when object is added to viewer"""
        if self.cmdForms.has_key('default'):
            try:
                ebn = self.cmdForms['moleculeSelect'].descr.entryByName
                w = ebn['moleculeListSelect']['widget']
                molNames = self.vf.Mols.name
                w.setlist(molNames)
                descr = self.cmdForms['default'].descr
                descr.entryByName['APBSservicesLabel1']['widget'].\
                                                            configure(text = "")
                descr.entryByName['APBSservicesLabel2']['widget'].\
                                                            configure(text = "")
                descr.entryByName['APBSservicesLabel3']['widget'].\
                                                            configure(text = "")
                descr.entryByName['APBSservicesLabel4']['widget'].\
                                                            configure(text = "")

                
            except KeyError:
                pass    
        if hasattr(object,'chains'):
            object.APBSParams = {} 
        
#        object.APBSParams['Default'] = APBSParams()
        
    def onRemoveObjectFromViewer(self, object):
        """Called when object is removed from viewer"""
        if self.cmdForms.has_key('default'):
            try:
                ebn = self.cmdForms['moleculeSelect'].descr.entryByName
                w = ebn['moleculeListSelect']['widget']
                molNames = self.vf.Mols.name
                w.setlist(molNames)
                descr = self.cmdForms['default'].descr
                if hasattr(object,'chains'):
                    molName = object.name
                    if molName in descr.entryByName['molecule1']['widget'].get():
                        descr.entryByName['molecule1']['widget'].setentry('')
                    if molName in descr.entryByName['molecule2']['widget'].get():
                        descr.entryByName['molecule2']['widget'].setentry('')
                    if molName in descr.entryByName['complex']['widget'].get():
                        descr.entryByName['complex']['widget'].setentry('')
                
            except KeyError:
                pass              

    def onAddCmdToViewer(self):
        """Called when APBSSetup are added to viewer"""
        from DejaVu.bitPatterns import patternList
        from opengltk.OpenGL import GL
        from DejaVu import viewerConst
        from DejaVu.Box import Box
        
        face=((0,3,2,1),(3,7,6,2),(7,4,5,6),(0,1,5,4),(1,2,6,5),(0,4,7,3))
        coords=((1,1,-1),(-1,1,-1),(-1,-1,-1),(1,-1,-1),(1,1,1),(-1,1,1),
                (-1,-1,1),(1,-1,1))
        materials=((0,0,1),(0,1,0),(0,0,1),(0,1,0),(1,0,0),(1,0,0))
        
        box=Box('CoarseAPBSbox', materials=materials, vertices=coords, 
                faces=face, listed=0, inheritMaterial=0)
        box.Set(frontPolyMode=GL.GL_FILL, tagModified=False)
        box.polygonstipple.Set(pattern=patternList[0])
        box.Set(matBind=viewerConst.PER_PART, visible=0, 
                inheritStipplePolygons=0, shading=GL.GL_FLAT, inheritShading=0, 
                stipplePolygons=1, frontPolyMode=GL.GL_FILL,
                tagModified=False)
        box.oldFPM = None
        self.coarseBox = box
        if self.vf.hasGui:
            self.vf.GUI.VIEWER.AddObject(box, redo=0)
            
        box=Box('FineAPBSbox', materials=materials, vertices=coords, 
                faces=face, listed=0, inheritMaterial=0)
        box.polygonstipple.Set(pattern=patternList[3])
        box.Set(matBind=viewerConst.PER_PART, visible=0, 
                inheritStipplePolygons=0, shading=GL.GL_FLAT, 
                inheritShading=0, stipplePolygons=1, 
                frontPolyMode=GL.GL_FILL, tagModified=False)
        box.oldFPM = None
        self.fineBox = box
        if self.vf.hasGui:
            self.vf.GUI.VIEWER.AddObject(box, redo=0)

    def guiCallback(self):
        """GUI callback for APBSSetup"""
        self.refreshAll()
        mainform = self.showForm('default', modal=0, blocking=1, 
                                  initFunc=self.refreshAll)
        if mainform:
#            self.paramUpdateAll()
            tmp_dict = {}
            for key, value in self.params.__dict__.items():
                if  self.params.__dict__[key] != \
                self.cmp_APBSParams.__dict__[key]:
                    if type(value) is types.TupleType:
                        value = value[0] 
                    if key == 'ions':
                        for ion in value:
                            self.vf.message("self.APBSSetup.params.ions.\
append(Pmv.APBSCommands.Ion("+ion.toString()+"))")
                            self.vf.log("self.APBSSetup.params.ions.\
append(Pmv.APBSCommands.Ion("+ion.toString()+"))")
                        self.cmp_APBSParams.ions = self.params.ions
                        continue    
                    tmp_dict[key] = value     
            if len(tmp_dict) != 0:
                self.doitWrapper(**tmp_dict)
        
    def dismiss(self, event = None):
        """Withdraws 'default' GUI"""
        self.cmdForms['default'].withdraw()

    def coarseResolutionX(self):
        """Returns coarse grid resolution in X direction"""
        return self.params.coarseLengthX/float(self.params.gridPointsX-1)

    def coarseResolutionY(self):
        """Returns coarse grid resolution in Y direction"""
        return self.params.coarseLengthY/float(self.params.gridPointsY-1)

    def coarseResolutionZ(self):
        """Returns coarse grid resolution in Z direction"""
        return self.params.coarseLengthZ/float(self.params.gridPointsZ-1)

    def fineResolutionX(self):
        """Returns fine grid resolution in X direction"""
        return self.params.fineLengthX/float(self.params.gridPointsX-1)

    def fineResolutionY(self):
        """Returns fine grid resolution in Y direction"""
        return self.params.fineLengthY/float(self.params.gridPointsY-1)

    def fineResolutionZ(self):
        """Returns fine grid resolution in Z direction"""
        return self.params.fineLengthZ/float(self.params.gridPointsZ-1)

    def memoryToBeAllocated(self):
        """Returns memory to be allocated for APBS run"""
        return self.params.MEGABYTES_PER_GRID_POINT*self.totalGridPoints()

    def totalGridPoints(self):
        """Returns total number of grid points"""
        return self.params.gridPointsX*self.params.gridPointsY*\
        self.params.gridPointsZ

    def autocenterCoarseGrid(self):
        """Autocenters coarse grid"""            
        coords = self.getCoords()
        center=(Numeric.maximum.reduce(coords)+Numeric.minimum.reduce(coords))*0.5
        center = center.tolist()
        self.params.coarseCenterX = round(center[0],4)
        self.params.coarseCenterY = round(center[1],4)
        self.params.coarseCenterZ = round(center[2],4)
        self.refreshGridPage()

    def autosizeCoarseGrid(self):
        """Autosizes coarse grid"""
        coords = self.getCoords()
        length = Numeric.maximum.reduce(coords) - Numeric.minimum.reduce(coords)
        self.params.coarseLengthX = self.params.CFAC*(length.tolist())[0] + 10.
        self.params.coarseLengthY = self.params.CFAC*(length.tolist())[1] + 10.
        self.params.coarseLengthZ = self.params.CFAC*(length.tolist())[2] + 10.
        self.refreshGridPage()

    def autocenterFineGrid(self):
        """Autocenters fine grid"""
        coords = self.getCoords()    
        center=(Numeric.maximum.reduce(coords)+Numeric.minimum.reduce(coords))*0.5
        center = center.tolist()
        self.params.fineCenterX = round(center[0],4)
        self.params.fineCenterY = round(center[1],4)
        self.params.fineCenterZ = round(center[2],4)
        self.refreshGridPage()

    def autosizeFineGrid(self):
        """Autosizes fine grid"""
        coords = self.getCoords()
        length=Numeric.maximum.reduce(coords)-Numeric.minimum.reduce(coords)
        self.params.fineLengthX = (length.tolist())[0] + 10.0
        self.params.fineLengthY = (length.tolist())[1] + 10.0
        self.params.fineLengthZ = (length.tolist())[2] + 10.0
        self.refreshGridPage()
        
    def getCoords(self):
        """Returns coordinates of atoms included in calculation"""
        if not hasattr(self, 'mol1Name'): return [[0,0,0]]        
        mol = self.vf.getMolFromName(self.mol1Name)
        coords = mol.findType(Atom).coords
        if self.params.calculationType == 'Binding energy':
            if hasattr(self, 'mol2Name'):
                mol = self.vf.getMolFromName(self.mol2Name)
                if mol:
                    coords += mol.findType(Atom).coords
            if hasattr(self, 'complexName'):
                mol = self.vf.getMolFromName(self.complexName)
                if mol:
                    coords += mol.findType(Atom).coords
        return coords
    
    # Callbacks
    def refreshCalculationPage(self):
        """Refreshes calculation page"""
        if self.cmdForms.has_key('default'):
            descr = self.cmdForms['default'].descr

            if(self.params.calculationType=='Binding energy'):
                apply(descr.entryByName['molecule2Select']['widget'].grid,
                            (), descr.entryByName['molecule2Select']['gridcfg'])
                apply(descr.entryByName['molecule2']['widget'].grid, (),
                                      descr.entryByName['molecule2']['gridcfg'])
                apply(descr.entryByName['complexSelect']['widget'].grid, (), 
                                  descr.entryByName['complexSelect']['gridcfg'])
                apply(descr.entryByName['complex']['widget'].grid, (), 
                                        descr.entryByName['complex']['gridcfg'])
                #self.params.energyOutput = 'Total'
            elif(self.params.calculationType=='Solvation energy'):
                descr.entryByName['molecule2Select']['widget'].grid_forget()
                descr.entryByName['molecule2']['widget'].grid_forget()
                descr.entryByName['complexSelect']['widget'].grid_forget()
                descr.entryByName['complex']['widget'].grid_forget()
                #self.params.energyOutput = 'Total'
            elif(self.params.calculationType=='Electrostatic potential'):
                descr.entryByName['molecule2Select']['widget'].grid_forget()
                descr.entryByName['molecule2']['widget'].grid_forget()
                descr.entryByName['complexSelect']['widget'].grid_forget()
                descr.entryByName['complex']['widget'].grid_forget()

            descr.entryByName['calculationType']['widget'].\
                                        selectitem(self.params.calculationType)
            descr.entryByName['pbeType']['widget'].\
                                                 selectitem(self.params.pbeType)
            descr.entryByName['boundaryConditions']['widget'].\
                                      selectitem(self.params.boundaryConditions)
            descr.entryByName['chargeDiscretization']['widget'].\
                                    selectitem(self.params.chargeDiscretization)
            descr.entryByName['surfaceCalculation']['widget'].\
                                    selectitem(self.params.surfaceCalculation)
            descr.entryByName['sdens']['widget'].setentry(self.params.sdens)
            descr.entryByName['splineWindow']['widget'].\
                                              setentry(self.params.splineWindow)
    
            if self.params.surfaceCalculation == 'Cubic B-spline' or \
                       self.params.surfaceCalculation == '7th Order Polynomial':
                apply(descr.entryByName['splineWindowLabel']['widget'].grid, 
                          (), descr.entryByName['splineWindowLabel']['gridcfg'])
                apply(descr.entryByName['splineWindow']['widget'].grid, (), 
                                   descr.entryByName['splineWindow']['gridcfg'])
                descr.entryByName['sdensLabel']['widget'].grid_forget()
                descr.entryByName['sdens']['widget'].grid_forget()

            else:
                apply(descr.entryByName['sdensLabel']['widget'].grid, 
                          (), descr.entryByName['sdensLabel']['gridcfg'])
                apply(descr.entryByName['sdens']['widget'].grid, (), 
                                   descr.entryByName['sdens']['gridcfg'])
                descr.entryByName['splineWindowLabel']['widget'].grid_forget()
                descr.entryByName['splineWindow']['widget'].grid_forget()
    
            descr.entryByName['molecule1']['widget'].\
                                             setentry(self.params.molecule1Path)
            descr.entryByName['molecule2']['widget'].\
                                             setentry(self.params.molecule2Path)
            descr.entryByName['complex']['widget'].\
                                               setentry(self.params.complexPath)
    
            descr.entryByName['energyOutput']['widget'].\
                                            selectitem(self.params.energyOutput)
            descr.entryByName['forceOutput']['widget'].\
                                            selectitem(self.params.forceOutput)
            descr.entryByName['forceOutput']['widget'].\
                                            selectitem(self.params.forceOutput)
            descr.entryByName['Profiles']['widget'].\
                                            selectitem(self.params.name)
              
    def testCalculationWidgets(self):
        """Tests calculation widgets"""
        if self.cmdForms.has_key('default'):
            descr = self.cmdForms['default'].descr

            if(descr.entryByName['splineWindow']['widget'].get() == ''):
                self.errorMsg = 'You must enter a spline window value.'
                errorform = self.showForm('error',modal=1,blocking=1,force = 1)
                return 1
            return 0

    def calculationParamUpdate(self, selectItem=0):
        """Updates calculation parameters"""
        if self.cmdForms.has_key('default'):
            if selectItem == 'Binding energy':
                self.params.calculationType = 'Binding energy'
                self.refreshCalculationPage()
                return 
            descr = self.cmdForms['default'].descr
            # Prevent forcing a particular calculation type on the user
            self.params.calculationType = descr.entryByName\
                                            ['calculationType']['widget'].get()
            if self.testCalculationWidgets()==0:
                self.params.calculationType = descr.entryByName\
                                            ['calculationType']['widget'].get()
                self.params.pbeType = descr.entryByName['pbeType']['widget'].\
                                                                           get()
                self.params.boundaryConditions = descr.entryByName\
                                          ['boundaryConditions']['widget'].get()
                self.params.chargeDiscretization = descr.entryByName\
                                        ['chargeDiscretization']['widget'].get()
                self.params.surfaceCalculation = descr.entryByName\
                                          ['surfaceCalculation']['widget'].get()
                self.params.sdens = float(descr.entryByName['sdens']['widget'].\
                                                                          get())
                self.params.splineWindow =  float(descr.entryByName\
                                               ['splineWindow']['widget'].get())
                self.params.molecule1Path = descr.entryByName['molecule1']\
                                                                ['widget'].get()
                self.params.molecule2Path = descr.entryByName['molecule2']\
                                                                ['widget'].get()
                self.params.complexPath = descr.entryByName['complex']\
                                                                ['widget'].get()
                self.params.energyOutput = descr.entryByName['energyOutput']\
                                                                ['widget'].get()
                self.params.forceOutput = descr.entryByName['forceOutput']\
                                                                ['widget'].get()
                self.params.name = descr.entryByName['Profiles']['widget'].\
                                                                           get()
            else:
                return "ERROR"                                                           
            self.refreshCalculationPage()

    def refreshGridPage(self):
        """Refreshes grid page"""
        if self.cmdForms.has_key('default'):
            descr = self.cmdForms['default'].descr
            descr.entryByName['gridPointsX']['widget'].set(closestMatch(self.
                       params.gridPointsX, self.params.GRID_VALUES), update = 0)
            descr.entryByName['gridPointsY']['widget'].set(closestMatch(self.
                       params.gridPointsY, self.params.GRID_VALUES), update = 0)
            descr.entryByName['gridPointsZ']['widget'].set(closestMatch(self.
                       params.gridPointsZ, self.params.GRID_VALUES), update = 0)
            descr.entryByName['coarseLengthX']['widget'].set(self.params.
                                                      coarseLengthX, update = 0)
            descr.entryByName['coarseLengthY']['widget'].set(self.params.
                                                      coarseLengthY, update = 0)
            descr.entryByName['coarseLengthZ']['widget'].set(self.params.
                                                      coarseLengthZ, update = 0)
            descr.entryByName['coarseCenterX']['widget'].set(self.params.
                                                      coarseCenterX, update = 0)
            descr.entryByName['coarseCenterY']['widget'].set(self.params.
                                                      coarseCenterY, update = 0)
            descr.entryByName['coarseCenterZ']['widget'].set(self.params.
                                                      coarseCenterZ, update = 0)
            descr.entryByName['coarseResolutionX']['widget'].configure(text = 
                                               "%5.3f"%self.coarseResolutionX())
            descr.entryByName['coarseResolutionY']['widget'].configure(text = 
                                               "%5.3f"%self.coarseResolutionY())
            descr.entryByName['coarseResolutionZ']['widget'].configure(text = 
                                               "%5.3f"%self.coarseResolutionZ())
            descr.entryByName['fineLengthX']['widget'].set(self.params.
                                                        fineLengthX, update = 0)
            descr.entryByName['fineLengthY']['widget'].set(self.params.
                                                        fineLengthY, update = 0)
            descr.entryByName['fineLengthZ']['widget'].set(self.params.
                                                        fineLengthZ, update = 0)
            descr.entryByName['fineCenterX']['widget'].set(self.params.
                                                        fineCenterX, update = 0)
            descr.entryByName['fineCenterY']['widget'].set(self.
                                                 params.fineCenterY, update = 0)
            descr.entryByName['fineCenterZ']['widget'].set(self.params.
                                                        fineCenterZ, update = 0)
            descr.entryByName['fineResolutionX']['widget'].configure(text = 
                                                 "%5.3f"%self.fineResolutionX())
            descr.entryByName['fineResolutionY']['widget'].configure(text = 
                                                 "%5.3f"%self.fineResolutionY())
            descr.entryByName['fineResolutionZ']['widget'].configure(text = 
                                                 "%5.3f"%self.fineResolutionZ())
            descr.entryByName['gridPointsNumberLabel']['widget'].\
                                   configure(text = "%d"%self.totalGridPoints())
            descr.entryByName['mallocSizeLabel']['widget'].configure(text = 
                                             "%5.3f"%self.memoryToBeAllocated())
            self.coarseBox.Set(visible = descr.\
                entryByName['showCoarseGrid']['wcfg']['variable'].get(),
                xside = self.params.coarseLengthX, 
                yside = self.params.coarseLengthY, 
                zside = self.params.coarseLengthZ,
                center = [self.params.coarseCenterX, self.params.coarseCenterY, 
                           self.params.coarseCenterZ], tagModified=False)
            self.fineBox.Set(visible = descr.\
                entryByName['showFineGrid']['wcfg']['variable'].get(),
                xside = self.params.fineLengthX,yside = self.params.fineLengthY, 
                zside = self.params.fineLengthZ,
                center = [self.params.fineCenterX, self.params.fineCenterY, 
                           self.params.fineCenterZ], tagModified=False)
            self.vf.GUI.VIEWER.Redraw()

    def testGridWidgets(self):
        """Tests grid widget"""
        if self.cmdForms.has_key('default'):
            descr = self.cmdForms['default'].descr
            #Boundary check: make sure coarse grid encloses fine grid
            ccx = descr.entryByName['coarseCenterX']['widget'].value
            ccy = descr.entryByName['coarseCenterY']['widget'].value
            ccz = descr.entryByName['coarseCenterZ']['widget'].value
            clx = descr.entryByName['coarseLengthX']['widget'].value/2
            cly = descr.entryByName['coarseLengthY']['widget'].value/2
            clz = descr.entryByName['coarseLengthZ']['widget'].value/2
            fcx = descr.entryByName['fineCenterX']['widget'].value
            fcy = descr.entryByName['fineCenterY']['widget'].value
            fcz = descr.entryByName['fineCenterZ']['widget'].value
            flx = descr.entryByName['fineLengthX']['widget'].value/2
            fly = descr.entryByName['fineLengthY']['widget'].value/2
            flz = descr.entryByName['fineLengthZ']['widget'].value/2
            if (fcx+flx>ccx+clx) or (fcx-flx<ccx-clx) or (fcy+fly>ccy+cly) or \
                   (fcy-fly<ccy-cly) or (fcz+flz>ccz+clz) or (fcz-flz<ccz-clz):
                self.errorMsg = 'The coarse grid must enclose the fine grid.'
                errorform = self.showForm('error',modal=1,blocking=1,force=1)
                return 1
            return 0
        else :
            #Boundary check: make sure coarse grid encloses fine grid
            ccx = self.params.coarseCenterX
            ccy = self.params.coarseCenterY
            ccz = self.params.coarseCenterZ
            clx = self.params.coarseLengthX
            cly = self.params.coarseLengthY
            clz = self.params.coarseLengthZ
            fcx = self.params.fineCenterX
            fcy = self.params.fineCenterY
            fcz = self.params.fineCenterZ
            flx = self.params.fineLengthX
            fly = self.params.fineLengthY
            flz = self.params.fineLengthZ
            if (fcx+flx>ccx+clx) or (fcx-flx<ccx-clx) or (fcy+fly>ccy+cly) or \
                   (fcy-fly<ccy-cly) or (fcz+flz>ccz+clz) or (fcz-flz<ccz-clz):
                self.errorMsg = 'The coarse grid must enclose the fine grid.'
                errorform = self.showForm('error',modal=1,blocking=1,force=1)
                return 1
            return 0

    def gridParamUpdate(self, selectItem=0):
        """Updates grid parameters. Returns "ERROR" is failed"""
        if self.testGridWidgets() == 0:
            if self.cmdForms.has_key('default'):
                descr = self.cmdForms['default'].descr
    
                self.params.gridPointsX = closestMatch(descr.entryByName
                       ['gridPointsX']['widget'].get(), self.params.GRID_VALUES)
                self.params.gridPointsY = closestMatch(descr.entryByName
                       ['gridPointsY']['widget'].get(), self.params.GRID_VALUES)
                self.params.gridPointsZ = closestMatch(descr.entryByName
                       ['gridPointsZ']['widget'].get(), self.params.GRID_VALUES)
    
                self.params.coarseLengthX = descr.entryByName['coarseLengthX']\
                                                                ['widget'].value
                self.params.coarseLengthY = descr.entryByName['coarseLengthY']\
                                                                ['widget'].value
                self.params.coarseLengthZ = descr.entryByName['coarseLengthZ']\
                                                                ['widget'].value
                self.params.coarseCenterX = descr.entryByName['coarseCenterX']\
                                                                ['widget'].value
                self.params.coarseCenterY = descr.entryByName['coarseCenterY']\
                                                                ['widget'].value
                self.params.coarseCenterZ = descr.entryByName['coarseCenterZ']\
                                                                ['widget'].value
                self.params.fineLengthX = descr.entryByName['fineLengthX']\
                                                                ['widget'].value
                self.params.fineLengthY = descr.entryByName['fineLengthY']\
                                                                ['widget'].value
                self.params.fineLengthZ = descr.entryByName['fineLengthZ']\
                                                                ['widget'].value
                self.params.fineCenterX = descr.entryByName['fineCenterX']\
                                                                ['widget'].value
                self.params.fineCenterY = descr.entryByName['fineCenterY']\
                                                                ['widget'].value
                self.params.fineCenterZ = descr.entryByName['fineCenterZ']\
                                                                ['widget'].value
                self.flag_grid_changed = True
        else:
            return "ERROR"
        self.refreshGridPage()

    def refreshPhysicsPage(self):
        """Refreshes physics page"""
        if self.cmdForms.has_key('default'):
            descr = self.cmdForms['default'].descr
    
            descr.entryByName['proteinDielectric']['widget'].\
                                         setentry(self.params.proteinDielectric)
            descr.entryByName['solventDielectric']['widget'].\
                                         setentry(self.params.solventDielectric)
            descr.entryByName['solventRadius']['widget'].\
                                             setentry(self.params.solventRadius)
            descr.entryByName['systemTemperature']['widget'].\
                                         setentry(self.params.systemTemperature)
            descr.entryByName['ionsList']['widget'].clear()
            for i in range(len(self.params.ions)):
                        descr.entryByName['ionsList']['widget'].\
                                   insert('end', self.params.ions[i].toString())
            if self.params.saltConcentration:
                self.salt_var.set(1)
            else:
                self.salt_var.set(0)

    def testPhysicsWidgets(self):
        """Tests physics widget"""
        if self.cmdForms.has_key('default'):
            descr = self.cmdForms['default'].descr
    
            if(descr.entryByName['proteinDielectric']['widget'].get() == ''):
                        self.errorMsg = 'You must enter a protein dielectric\
                                                                         value.'
                        errorform = self.showForm('error', modal=1, blocking=1, 
                                                                      force = 1)
                        return 1
            if(descr.entryByName['solventDielectric']['widget'].get() == ''):
                        self.errorMsg = 'You must enter a solvent dielectric\
                                                                         value.'
                        errorform = self.showForm('error', modal=1, blocking=1, 
                                                                      force = 1)
                        return    1
            if(descr.entryByName['solventRadius']['widget'].get() == ''):
                        self.errorMsg = 'You must enter a solvent radius value.'
                        errorform = self.showForm('error', modal=1, blocking=1, 
                                                                      force = 1)
                        return 1
            if(descr.entryByName['systemTemperature']['widget'].get() == ''):
                        self.errorMsg = 'You must enter a system temperature \
                                                                         value.'
                        errorform = self.showForm('error', modal=1, blocking=1, 
                                                                      force = 1)
                        return 1
            return 0

    def physicsParamUpdate(self):
        """Updates physics parameter. Returns "ERROR" is failed"""
        if self.testPhysicsWidgets() != 1:              
            if self.cmdForms.has_key('default'):
                descr = self.cmdForms['default'].descr
        
                self.params.proteinDielectric =  float(descr.entryByName\
                                          ['proteinDielectric']['widget'].get())
                self.params.solventDielectric =  float(descr.entryByName\
                                          ['solventDielectric']['widget'].get())
                self.params.solventRadius     =  float(descr.entryByName\
                                              ['solventRadius']['widget'].get())
                self.params.systemTemperature =  float(descr.entryByName\
                                          ['systemTemperature']['widget'].get())
                salt = self.salt_var.get()
                if salt:
                    self.params.saltConcentration = float(descr.entryByName\
                                          ['saltConcentration']['widget'].get())
                else:
                    self.params.saltConcentration = 0
        else:
            return "ERROR"
        self.refreshPhysicsPage()

    def refreshAll(self,cmdForm = None):
        """Refreshes calculation, grid and physics pages"""
        if cmdForm:
            self.cmdForms['default'] = cmdForm
            descr = cmdForm.descr
            if APBSservicesFound:
                ResourceFolder = getResourceFolderWithVersion()
                if os.path.isdir(ResourceFolder):
                    pass
                else:
                    os.mkdir(ResourceFolder)
                self.rc_apbs = ResourceFolder + os.sep + "ws"
                if os.path.isdir(self.rc_apbs):
                    pass
                else:
                    os.mkdir(self.rc_apbs)
                self.rc_apbs += os.sep + "rc_apbs"
                if not os.path.exists(self.rc_apbs):
                    open(self.rc_apbs,'w')
                else:
                    file = open(self.rc_apbs)
                    text = file.read()
                    text = text.split()
                    for line in text:
                        tmp_line = line.split('User:')
                        if len(tmp_line) > 1:
                            descr.entryByName['UserName_Entry']['wcfg']\
                            ['textvariable'].set(tmp_line[1])
                        tmp_line = line.split('Password:')
                        if len(tmp_line) > 1:
                            descr.entryByName['Password_Entry']['wcfg']\
                            ['textvariable'].set(tmp_line[1])
                    file.close()
#                descr.entryByName['ParallelGroup']['widget'].toggle()
                if not descr.entryByName['web service address']['widget'].get():
                        descr.entryByName['web service address']['widget']\
                                                                  .selectitem(0)
                url = descr.entryByName['web service address']['widget'].get()
                url = url.strip()
                if url.find('https://') != 0:
                    descr.entryByName['UserName_Label']['widget'].grid_forget()
                    descr.entryByName['UserName_Entry']['widget'].grid_forget()
                    descr.entryByName['Password_Label']['widget'].grid_forget()
                    descr.entryByName['Password_Entry']['widget'].grid_forget()
                    descr.entryByName['Remember_Label']['widget'].grid_forget()
                    descr.entryByName['Remember_Checkbutton']['widget']\
                                                                  .grid_forget()
                self.progressBar = ProgressBar(
                descr.entryByName['WS_ProgressBar']['widget']
                               , labelside=None,                               
                            width=200, height=20, mode='percent')

                self.progressBar.setLabelText('Progress...')
                self.progressBar.set(0)
                descr.entryByName['WS_ProgressBar']['widget'].grid_forget()        
            else:
                descr.entryByName['WS_http']['widget'].bind( 
                                   sequence = "<Button-1>", func = self.WS_http)
            descr.entryByName['calculationType']['widget']._entryWidget.\
                                                      config(state = 'readonly')
            descr.entryByName['pbeType']['widget']._entryWidget.\
                                                      config(state = 'readonly')
            descr.entryByName['boundaryConditions']['widget']._entryWidget.\
                                                      config(state = 'readonly')
            descr.entryByName['chargeDiscretization']['widget'].\
                                         _entryWidget.config(state = 'readonly')
            descr.entryByName['surfaceCalculation']['widget']._entryWidget.\
                                                      config(state = 'readonly')
            descr.entryByName['energyOutput']['widget']._entryWidget.\
                                                      config(state = 'readonly')
            descr.entryByName['forceOutput']['widget']._entryWidget.\
                                                      config(state = 'readonly')
        self.refreshCalculationPage()
        self.refreshGridPage()
        self.refreshPhysicsPage()

    def paramUpdateAll(self):
        """Updates all parameters. Returns "ERROR" if failed """
        if self.calculationParamUpdate() == "ERROR":
            return "ERROR"
        if self.gridParamUpdate() == "ERROR":
            return "ERROR"
        if self.physicsParamUpdate() == "ERROR":
            return "ERROR"

    def setOutputFiles(self):
        """Sets output files using outputFilesForm GUI"""
        outputFilesForm = self.showForm('outputFilesForm', \
        modal = 1, blocking = 1,force=1,master=self.cmdForms['default'].f)
        descr = self.cmdForms['outputFilesForm'].descr
        self.params.chargeDistributionFile = descr.entryByName\
                                      ['chargeDistributionFile']['widget'].get()
        self.params.potentialFile = descr.entryByName['potentialFile']\
                                                                ['widget'].get()
        self.params.solventAccessibilityFile = descr.entryByName\
                                    ['solventAccessibilityFile']['widget'].get()
        self.params.splineBasedAccessibilityFile = descr.entryByName\
                                ['splineBasedAccessibilityFile']['widget'].get()
        self.params.VDWAccessibilityFile = descr.entryByName\
                                        ['VDWAccessibilityFile']['widget'].get()
        self.params.ionAccessibilityFile = descr.entryByName\
                                        ['ionAccessibilityFile']['widget'].get()
        self.params.laplacianOfPotentialFile = descr.entryByName\
                                    ['laplacianOfPotentialFile']['widget'].get()
        self.params.energyDensityFile = descr.entryByName\
                                           ['energyDensityFile']['widget'].get()
        self.params.ionNumberFile = descr.entryByName\
                                               ['ionNumberFile']['widget'].get()
        self.params.ionChargeDensityFile = descr.entryByName\
                                        ['ionChargeDensityFile']['widget'].get()
        self.params.xShiftedDielectricFile = descr.entryByName\
                                      ['xShiftedDielectricFile']['widget'].get()
        self.params.yShiftedDielectricFile = descr.entryByName\
                                      ['yShiftedDielectricFile']['widget'].get()
        self.params.zShiftedDielectricFile = descr.entryByName\
                                      ['zShiftedDielectricFile']['widget'].get()
        self.params.kappaFunctionFile = descr.entryByName\
                                           ['kappaFunctionFile']['widget'].get()

    def addIon(self):
        """Adds an Ion"""
        ionForm = self.showForm('ionForm', modal = 0, blocking = 1,
                                              master=self.cmdForms['default'].f)
        descr = self.cmdForms['ionForm'].descr
        ion = Ion()
        ion.charge = float(descr.entryByName['ionCharge']['widget'].get())
        ion.concentration = float(descr.entryByName['ionConcentration']
                                                               ['widget'].get())
        ion.radius = float(descr.entryByName['ionRadius']['widget'].get())
        self.params.ions.append(ion)
        self.vf.message("self.APBSSetup.params.ions.append(Pmv.APBSCommands.Ion\
("+ion.toString()+"))")
        self.vf.log("self.APBSSetup.params.ions.append(Pmv.APBSCommands.Ion(" \
+ion.toString()+"))")
        f = self.cmdForms['default']
        f.descr.entryByName['ionsList']['widget'].insert('end', ion.toString())

    def removeIon(self):
        """Removes an Ion"""
        descr = self.cmdForms['default'].descr
        s = repr(descr.entryByName['ionsList']['widget'].getcurselection())
        for i in range(descr.entryByName['ionsList']['widget'].size()):
                      if(string.find(s,descr.entryByName['ionsList']['widget']
                                                                   .get(i))>-1):
                              break
        descr.entryByName['ionsList']['widget'].delete(i)
        self.params.ions.pop(i)
        self.vf.message("self.APBSSetup.params.ions.pop("+`i`+")")
        self.vf.log("self.APBSSetup.params.ions.pop("+`i`+")")
        
    def moleculeListSelect(self, molName):
        """None <--- moleculeListSelect(molName)\n
           Selects molecule with molName.\n
           If the molecule was not read as pqr file moleculeListSelect\n
        """
        if self.cmdForms.has_key('default'):
            self.cmdForms['default'].root.config(cursor='watch') 
        self.vf.GUI.ROOT.config(cursor='watch')
        self.vf.GUI.VIEWER.master.config(cursor='watch')    
        #self.vf.GUI.MESSAGE_BOX.tx.component('text').config(cursor='watch')
        molName = molName.replace('-','_')
        mol = self.vf.getMolFromName(molName)
        assert mol, "Error: molecule is not loaded " + molName
        file, ext = os.path.splitext(mol.parser.filename)
        if ext:
            ext = ext.lower()
        if ext == '.pqr':
            filename = mol.parser.filename
            mol.flag_copy_pqr = True
        else: #create pqr file using pdb2pqr.py
            filename = mol.name+".pqr"
            #full_filename = os.path.join(self.params.projectFolder,filename)
            #filename = full_filename
            flag_overwrite = True
            if not os.path.exists(filename) or \
                                         self.vf.APBSPreferences.overwrite_pqr: 
                if not self.vf.commands.has_key('writePDB'):
                    self.vf.browseCommands("fileCommands", 
                                                         commands=['writePDB',])
                from user import home
                tmp_pdb = home + os.path.sep + 'tmp.pdb'
                filename = home + os.path.sep + filename
                self.vf.writePDB(mol,tmp_pdb, pdbRec=('ATOM','HETATM'), log=0)            
              # Exe_String = sys.executable + \
               #    " -Wignore::DeprecationWarning " + self.params.pdb2pqr_Path\
               #    + " --ff="+self.params.pdb2pqr_ForceField + " tmp.pdb " + \
               #                                         "\""+full_filename+"\""
                sys.argv = [sys.executable , self.params.pdb2pqr_Path]
                if self.vf.APBSPreferences.nodebump.get():
                    sys.argv.append('--nodebump')
                if self.vf.APBSPreferences.nohopt.get():
                    sys.argv.append('--noopt')
                sys.argv.append('--ff='+self.params.pdb2pqr_ForceField)
                sys.argv.append(tmp_pdb)
                sys.argv.append(filename)
                os.path.split(self.params.pdb2pqr_Path)[0]
                import subprocess
                returncode = subprocess.call(sys.argv)
                if returncode:
                    if not hasattr(self.vf,"spin"):
                        #spin is not available during unit testing
                        return ''
                    msg = "Could not convert " + mol.name +""" to pqr! 
Please try the latest pdb2pqr from: http://pdb2pqr.sourceforge.net."""
                    if self.cmdForms.has_key('default') and \
                       self.cmdForms['default'].f.winfo_toplevel().wm_state()==\
                                                                       'normal':
                        tkMessageBox.showerror("ERROR: ", msg,
                                         parent = self.cmdForms['default'].root)
                    else:
                        tkMessageBox.showerror("ERROR: ", msg)       
            
                    self.vf.GUI.ROOT.config(cursor='')
                    self.vf.GUI.VIEWER.master.config(cursor='')   
                    if self.cmdForms.has_key('default'):
                            self.cmdForms['default'].root.config(cursor='')                    
                    return ''
                try:
                    os.remove(mol.name + '-typemap.html') 
                except:
                    pass
                    
                if self.cmdForms.has_key('default'):
                        self.cmdForms['default'].root.config(cursor='')
                self.vf.GUI.ROOT.config(cursor='')
                self.vf.GUI.VIEWER.master.config(cursor='')    
                #self.vf.GUI.MESSAGE_BOX.tx.component('text').config(cursor='xterm') 
                os.remove(tmp_pdb)       
            mol_tmp = self.vf.readPQR(filename, topCommand=0)
            mol_tmp.name = str(mol.name)
            self.vf.deleteMol(mol,topCommand=0)
            mol = mol_tmp
            mol.flag_copy_pqr = False
            self.vf.assignAtomsRadii(mol, overwrite=True,log=False)
        if self.vf.hasGui:
            change_Menu_state(self.vf.APBSSaveProfile, 'normal')
        
        if self.cmdForms.has_key('default'):
            self.cmdForms['default'].root.config(cursor='')
        self.vf.GUI.ROOT.config(cursor='')
        self.vf.GUI.VIEWER.master.config(cursor='')    
#        self.vf.GUI.MESSAGE_BOX.tx.component('text').config(cursor='xterm')   
        if  self.cmdForms.has_key('default'):
            form_descr = self.cmdForms['default'].descr
            #form_descr.entryByName['Profiles']['widget'].setentry('Default')
            form_descr.entryByName['Profiles_Add']['widget'].config(state = 
                                                                       "normal")
            form_descr.entryByName['Profiles_Remove']['widget'].config(state = 
                                                                       "normal")
            form_descr.entryByName['Profiles_Run']['widget'].config(state = 
                                                                       "normal")
            form_descr.entryByName['Profiles_Save']['widget'].config(state = 
                                                                       "normal")
            form_descr.entryByName['Profiles_Load']['widget'].config(state = 
                                                                       "normal")
            if APBSservicesFound:
                form_descr.entryByName['WS_Run']['widget'].config(state = 
                                                                       "normal")
        else:
            global state_GUI 
            state_GUI = 'normal'
        mol = self.vf.getMolFromName(molName.replace('-','_'))
        if self.cmdForms.has_key('default'):
             APBSParamName = self.cmdForms['default'].descr.\
                                         entryByName['Profiles']['widget'].get()            
             mol.APBSParams[APBSParamName] = self.params
        else:
             mol.APBSParams['Default'] = self.params
        self.flag_grid_changed = False #to call autosize Grid when running APBS             
        return filename    
                 
    def molecule1Select(self):
        """Seclects  molecule1 and setups molecule1Path"""
        val = self.showForm('moleculeSelect', modal = 0, \
        blocking = 1,master=self.cmdForms['default'].f)
        if val:
            if len(val['moleculeListSelect'])==0: return
            molName = val['moleculeListSelect'][0]
            self.params.molecule1Path = self.moleculeListSelect(molName)
            self.mol1Name = molName
            if not self.params.molecule1Path:
                return
            self.refreshCalculationPage()
            
            if not self.vf.APBSSetup.flag_grid_changed:
                self.autocenterCoarseGrid()
                self.autosizeCoarseGrid()
                self.autocenterFineGrid()
                self.autosizeFineGrid()
                self.refreshGridPage()      

    def molecule2Select(self):
        """Seclects  molecule2 and setups molecule2Path"""
        val = self.showForm('moleculeSelect', modal = 0, \
        blocking = 1,master=self.cmdForms['default'].f)
        if val:
            if len(val['moleculeListSelect'])==0: return
            molName = val['moleculeListSelect'][0]
            self.params.molecule2Path = self.moleculeListSelect(molName)
            self.mol2Name  = molName
            self.refreshCalculationPage() 

    def complexSelect(self):
        """Seclects  complex and setups complexPath"""
        val = self.showForm('moleculeSelect', modal=0, blocking=1,\
        master=self.cmdForms['default'].f)
        if val:
            if len(val['moleculeListSelect'])==0: return
            molName = val['moleculeListSelect'][0]
            self.params.complexPath = self.moleculeListSelect(molName)
            self.complexName = molName
            self.refreshCalculationPage()
            if not self.params.complexPath:
                return
            if not self.vf.APBSSetup.flag_grid_changed:            
                self.autocenterCoarseGrid()
                self.autosizeCoarseGrid()
                self.autocenterFineGrid()
                self.autosizeFineGrid()
                self.refreshGridPage()       


    def apbsOutput(self, molecule1=None, molecule2=None, _complex=None, blocking=False ):
        """Runs APBS using mglutil.popen2Threads.SysCmdInThread"""
        self.add_profile()
        if self.paramUpdateAll() == "ERROR":
            return
        if molecule1:
            self.params.SaveAPBSInput(self.params.projectFolder+os.path.sep\
                                                        +"apbs-input-file.apbs")
            self.changeMenuState('disabled')
            cmdstring = "\""+self.params.APBS_Path+"\" "+'apbs-input-file.apbs'
            self.cwd = os.getcwd()

            if blocking==False and self.vf.hasGui:
                from mglutil.popen2Threads import SysCmdInThread
                os.chdir(self.params.projectFolder)    
                self.cmd = SysCmdInThread(cmdstring, shell=True)
                self.cmd.start()
                time.sleep(1)
            else:
                from popen2 import Popen4
                os.chdir(self.params.projectFolder)    
                exec_cmd = Popen4(cmdstring)
                status = exec_cmd.wait()
                if status==0:
                    print exec_cmd.fromchild.read()
                else:
                    print exec_cmd.childerr.read()

            self.SaveResults(self.params.name, )
            os.chdir(self.cwd)

        else:
            file_name, ext = os.path.splitext(self.params.molecule1Path)
            molecule1 = os.path.split(file_name)[-1]
            if self.cmdForms.has_key('default'):
                APBSParamName = self.cmdForms['default'].descr.\
                                        entryByName['Profiles']['widget'].get()
            else:
                APBSParamName = 'Default'
            if self.params.calculationType == 'Binding energy':
                file_name, ext = os.path.splitext(self.params.molecule2Path)
                molecule2 = os.path.split(file_name)[-1]
                file_name, ext = os.path.splitext(self.params.complexPath)
                _complex = os.path.split(file_name)[-1]
            try:                                    
                self.doitWrapper(self.params.__dict__)                
                self.vf.APBSRun(molecule1, molecule2, _complex, APBSParamName=APBSParamName)
            except Exception, inst:
                print inst
                tkMessageBox.showerror("Error Running APBS", "Please make sure that Molecule(s) have corrent path.\n\n"+
                                       "Use Select botton to ensure your molecules(s) exists.",
                                       parent=self.vf.APBSSetup.cmdForms['default'].root)
    
    def SaveResults(self,params_name):
        """Checks the queue for results until we get one"""
        if   hasattr(self, 'cmd') is False \
          or self.cmd.ok.configure()['state'][-1] == 'normal':
            self.saveProfile(Profilename=params_name, fileFlag=True)
            self.changeMenuState('normal')
            if hasattr(self, 'cmd') is True:
                self.cmd.com.wait()
            potential_dx = self.params.projectFolder
            file_name, ext = os.path.splitext(self.params.molecule1Path)
            mol_name = os.path.split(file_name)[-1]
            potential = os.path.join(potential_dx, mol_name+'.potential.dx')
            if not os.path.exists(potential):
                return            
            self.vf.Grid3DReadAny(potential, show=False, normalize=False)
            self.vf.grids3D[mol_name+'.potential.dx'].geomContainer['Box'].Set(visible=0)
            self.potential = mol_name+'.potential.dx'
            if self.vf.hasGui:
                change_Menu_state(self.vf.APBSDisplayIsocontours, 'normal')
                change_Menu_state(self.vf.APBSDisplayOrthoSlice, 'normal')
                if hasattr(self.vf,'APBSVolumeRender'):
                    change_Menu_state(self.vf.APBSVolumeRender, 'normal')
            return
        else:
            self.vf.GUI.ROOT.after(10, self.SaveResults, params_name)

    def select_profile(self,profile_name):
        """Selects profile"""
        if self.paramUpdateAll() == "ERROR":
            self.remove_profile()
            return
        file_name, ext = os.path.splitext(self.params.molecule1Path)
        tmp_mol_name = os.path.split(file_name)[-1]
        molecule1 = self.vf.getMolFromName(tmp_mol_name.replace('-','_'))
        if molecule1.APBSParams.has_key(profile_name):
            self.params = molecule1.APBSParams[profile_name]
            self.refreshAll()
        else:
            self.params.name = profile_name
            molecule1.APBSParams[profile_name] =  self.params

    def add_profile(self):
        """Adds profile"""
        if self.cmdForms.has_key('default'):
            ComboBox = self.cmdForms['default'].descr.entryByName['Profiles']\
                                                                          ['widget']
            profile_name = ComboBox._entryfield.get()
            list_items = ComboBox._list.get()
            if not profile_name in list_items:
                list_items += (profile_name,)
                file_name, ext = os.path.splitext(self.params.molecule1Path)
                tmp_mol_name = os.path.split(file_name)[-1]
                molecule1 = self.vf.getMolFromName(tmp_mol_name.replace('-','_'))
                self.params.name = profile_name
                molecule1.APBSParams[profile_name] =  self.params
            ComboBox.setlist(list_items)
            ComboBox.setentry(profile_name)
            
    def remove_profile(self):
        """Removes current profile"""
        ComboBox = self.cmdForms['default'].descr.entryByName['Profiles']\
                                                                      ['widget']
        profile_name = ComboBox._entryfield.get()
        list_items = ComboBox._list.get()
        if profile_name in list_items:
            list_items = list(list_items)
            list_items.remove(profile_name)
            list_items = tuple(list_items)
            ComboBox.clear()
            ComboBox.setlist(list_items)
            try:
                ComboBox.setentry(list_items[0])
            except IndexError:
                pass
        file_name, ext = os.path.splitext(self.params.molecule1Path)
        tmp_mol_name = os.path.split(file_name)[-1]
        molecule1 = self.vf.getMolFromName(tmp_mol_name.replace('-','_'))
        if molecule1 and molecule1.APBSParams.has_key(profile_name):
            del molecule1.APBSParams[profile_name]
        
    def saveProfile(self, Profilename="Default", fileFlag=False, flagCommand=False):
        """Saves current profile
        fileFlag is used to decide if Profilename is a file: False means that we need  to aks for a file first
        flagCommand is isued to check if this functionm is called from APBSSave_Profile Command """
        if fileFlag:
            if not flagCommand and self.cmdForms.has_key('default'):
                Profilename = self.cmdForms['default'].descr.\
                        entryByName['Profiles']['widget'].get()          

            file_name,ext = os.path.splitext(self.params.molecule1Path)
            mol_name = os.path.split(file_name)[-1] 
            potential_dx = os.path.join(self.params.projectFolder, mol_name+ 
                                                            '.potential.dx')
            if os.path.exists(potential_dx):
                tmp_string = os.path.basename(Profilename).\
                                                      replace(".apbs.pf","")
                dest_path = os.path.join(self.params.projectFolder, tmp_string + 
                                               '_' + mol_name + '_potential.dx')
                shutil.copyfile(potential_dx,dest_path)          

            if self.params.calculationType == 'Solvation energy':            
                potential_dx = os.path.join(self.params.projectFolder, mol_name+
                                                    '_Vacuum.potential.dx')
                if os.path.exists(potential_dx):
                    tmp_string = os.path.basename(Profilename).\
                                                          replace(".apbs.pf","")
                    dest_path = os.path.join(self.params.projectFolder,
                           tmp_string + '_' + mol_name + '_Vacuum_potential.dx')
                    shutil.copyfile(potential_dx,dest_path)          

            if self.params.calculationType == 'Binding energy':            
                file_name,ext = os.path.splitext(self.params.molecule2Path)
                mol_name = os.path.split(file_name)[-1] 
                potential_dx = os.path.join(self.params.projectFolder, mol_name+ 
                                                                '.potential.dx')
                if os.path.exists(potential_dx):
                    tmp_string = os.path.basename(Profilename).\
                                                          replace(".apbs.pf","")
                    dest_path = os.path.join(self.params.projectFolder, 
                                  tmp_string + '_' + mol_name + '_potential.dx')
                    shutil.copyfile(potential_dx,dest_path)          
                file_name,ext = os.path.splitext(self.params.complexPath)
                mol_name = os.path.split(file_name)[-1] 
                potential_dx = os.path.join(self.params.projectFolder, mol_name+ 
                                                                '.potential.dx')
                if os.path.exists(potential_dx):
                    tmp_string = os.path.basename(Profilename).\
                                                          replace(".apbs.pf","")
                    dest_path = os.path.join(self.params.projectFolder, 
                                  tmp_string + '_' + mol_name + '_potential.dx')
                    shutil.copyfile(potential_dx,dest_path)          
            if os.path.isdir(self.params.projectFolder):
                Profilename = os.path.join(self.params.projectFolder, Profilename)

            if(string.find(Profilename,'.apbs.pf')<0):
                Profilename = Profilename + '.apbs.pf'
            fp = open(Profilename, 'w')
            pickle.dump(self.params, fp)
            pickle.dump(self.params.ions, fp)
            fp.close()
        else:
            self.vf.APBSSaveProfile()

    def loadProfile(self, filename = None):
        """Loads profile"""
        if filename:
            fp = open(filename, 'r')
            self.params = pickle.load(fp)
            self.doit(**self.params.__dict__)
            fp.close()
            profile_name = os.path.basename(filename).replace(".apbs.pf","")
            if self.params.calculationType=='Solvation energy' or self.params.\
                                     calculationType=='Electrostatic potential':
                if not self.vf.getMolFromName(os.path.basename(os.path.\
                                       splitext(self.params.molecule1Path)[0])):
                    molecule1Path  = os.path.join(self.params.projectFolder,
                                                      self.params.molecule1Path)
                    self.vf.readPQR(molecule1Path, topCommand=0)
            if(self.params.calculationType=='Binding energy'):
                if not self.vf.getMolFromName(os.path.basename(os.path.\
                                       splitext(self.params.molecule1Path)[0])):
                    molecule1Path  = os.path.join(self.params.projectFolder,
                                                      self.params.molecule1Path)
                    self.vf.readPQR(molecule1Path, topCommand=0)         
                if not self.vf.getMolFromName(os.path.basename(os.path.\
                                       splitext(self.params.molecule2Path)[0])):
                    molecule2Path  = os.path.join(self.params.projectFolder,
                                                      self.params.molecule2Path)
                    self.vf.readPQR(molecule2Path, topCommand=0)
                if not self.vf.getMolFromName(os.path.basename(os.path.\
                                         splitext(self.params.complexPath)[0])):
                    complexPath  = os.path.join(self.params.projectFolder,
                                                      self.params.complexPath)
                    self.vf.readPQR(complexPath, topCommand=0)           
            # the following part updates Profiles ComboBox
            if self.cmdForms.has_key('default'):
                ComboBox = self.cmdForms['default'].descr.entryByName\
                                                          ['Profiles']['widget']
                list_items = ComboBox._list.get()
                if not profile_name in list_items:
                    list_items += (profile_name,)
                ComboBox.setlist(list_items)
                ComboBox.setentry(profile_name)
            else:
                global PROFILES
                PROFILES += (profile_name,)
            if  self.cmdForms.has_key('default'):
                form_descr = self.cmdForms['default'].descr
                form_descr.entryByName['Profiles_Add']['widget'].config(state = 
                                                                       "normal")
                form_descr.entryByName['Profiles_Remove']['widget'].config(state
                                                                     = "normal")
                form_descr.entryByName['Profiles_Run']['widget'].config(state = 
                                                                       "normal")
                form_descr.entryByName['Profiles_Save']['widget'].config(state =
                                                                       "normal")
                form_descr.entryByName['Profiles_Load']['widget'].config(state =
                                                                       "normal")
                if APBSservicesFound:
                    form_descr.entryByName['WS_Run']['widget'].config(state = 
                                                                       "normal")              
            else:
                global state_GUI 
                state_GUI = 'normal'
            if self.vf.hasGui:
                change_Menu_state(self.vf.APBSSaveProfile, 'normal')
            self.refreshAll()                
            file_name,ext = os.path.splitext(self.params.molecule1Path)
            mol_name = os.path.split(file_name)[-1] 
            file_potential = os.path.join(self.params.projectFolder,profile_name
                                             + '_' + mol_name + '_potential.dx')
            if os.path.exists(file_potential): 
                shutil.copyfile(file_potential,os.path.join(self.params.\
                                      projectFolder,mol_name + '.potential.dx'))          
                self.changeMenuState('normal')
                self.potential = mol_name+'.potential.dx'
                if self.vf.hasGui:
                    change_Menu_state(self.vf.APBSDisplayIsocontours, 'normal')
                    change_Menu_state(self.vf.APBSDisplayOrthoSlice, 'normal')
                    if hasattr(self.vf,'APBSVolumeRender'):
                        change_Menu_state(self.vf.APBSVolumeRender, 'normal')
                self.vf.Grid3DReadAny(os.path.join(self.params.projectFolder,mol_name + '.potential.dx'), 
                                      show=False, normalize=False)
                self.vf.grids3D[mol_name+'.potential.dx'].geomContainer['Box'].Set(visible=0)
                
        else:
            self.vf.APBSLoadProfile()

    def apbsRunRemote(self):
        """Runs APBS Web Services in a thread and checks for the results"""
        if self.paramUpdateAll() == "ERROR":
            return
        file_name, ext = os.path.splitext(self.params.molecule1Path)
        tmp_mol_name = os.path.split(file_name)[-1]
        mol = self.vf.getMolFromName(tmp_mol_name.replace('-','_'))
        f = self.cmdForms['default']
        address = f.descr.entryByName['web service address']['widget'].get()
        address = address.strip()
        global APBS_ssl
        if address.find('https://') != 0:
            #first check to see if APBS Web Services is up and running
            import urllib
            opener = urllib.FancyURLopener({})
            try:
                servlet = opener.open(address)
            except IOError:
                self.errorMsg=address+" could not be found"
                self.errorMsg += "\nPlease make sure that server is up and running"
                self.errorMsg += "\nFor more info on APBS Web Services visit http://www.nbcr.net/services"
                self.showForm('error') 
                return
            APBS_ssl = False
        else:
            from mgltools.web.services.SecuritymyproxyloginImplService_services import \
                                              loginUserMyProxyRequestWrapper, \
                                          SecuritymyproxyloginImplServiceLocator
            gamaLoginLocator = SecuritymyproxyloginImplServiceLocator()
            gamaLoginService = gamaLoginLocator.getSecuritymyproxyloginImpl(
                                        ssl=1,transport=httplib.HTTPSConnection)
            req = loginUserMyProxyRequestWrapper()
            username =  self.cmdForms['default'].descr.\
                                   entryByName['UserName_Entry']['widget'].get()
            passwd =  self.cmdForms['default'].descr.\
                                   entryByName['Password_Entry']['widget'].get()
            req._username = username
            req._passwd = passwd
            resp = gamaLoginService.loginUserMyProxy(req)
            f = open(APBS_proxy, "w")
            f.write(resp._loginUserMyProxyReturn)
            f.close()
            APBS_ssl = True
            if self.RememberLogin_var.get():
                file = open(self.rc_apbs,'w')
                user = self.cmdForms['default'].descr.entryByName\
                                              ['UserName_Entry']['widget'].get()
                passwd = self.cmdForms['default'].descr.entryByName\
                                              ['Password_Entry']['widget'].get()
                file.write("User:%s\nPassword:%s\n"%(user,passwd))
        self.params.projectFolder=os.path.join(os.getcwd(),"apbs-"+mol.name)    
        from thread import start_new_thread
        if self.params.calculationType == 'Binding energy':
            file_name, ext = os.path.splitext(self.params.molecule2Path)
            tmp_mol_name = os.path.split(file_name)[-1]
            mol2 = self.vf.getMolFromName(tmp_mol_name.replace('-','_'))
            file_name, ext = os.path.splitext(self.params.complexPath)
            tmp_mol_name = os.path.split(file_name)[-1]
            _complex = self.vf.getMolFromName(tmp_mol_name.replace('-','_'))
            self.params.projectFolder += "_" + mol2.name + "_"+ _complex.name
            if not os.path.exists(self.params.projectFolder):
                os.mkdir(self.params.projectFolder)
            self.runWS(address, self.params, mol, mol2, _complex) 
        else:
            if not os.path.exists(self.params.projectFolder):
                os.mkdir(self.params.projectFolder)
            self.runWS(address, self.params, mol)
        #start_new_thread( self.checkForRemoteResults, (self.webServiceResultsQueue,))
        
    def runWS(self, address, params, mol1, mol2 = None, _complex = None):
        """Runs APBS Web Services"""
        if self.cmdForms.has_key('default'):
            self.apbsWS = APBSCmdToWebService(params, mol1,mol2, _complex)
            self.Parallel_flag = False
        else:
            self.apbsWS = APBSCmdToWebService(params, mol1, mol2, _complex)
            self.Parallel_flag = False
        try:
            f = self.cmdForms['default']
            f.descr.entryByName['APBSservicesLabel1']['widget'].\
                                     configure(text = 'Connecting to '+ address)
            f.descr.entryByName['APBSservicesLabel2']['widget'].\
                       configure(text = "")                             
            f.descr.entryByName['APBSservicesLabel4']['widget'].\
                       configure(text = "")                             
            f.descr.entryByName['APBSservicesLabel3']['widget'].\
                       configure(text = "Please wait ...")        
            f.descr.entryByName['APBSservicesLabel4']['widget'].\
                       configure(text = "")                             
            self.vf.GUI.ROOT.update()
            resp = self.apbsWS.run(address)

            f.descr.entryByName['APBSservicesLabel1']['widget'].\
                       configure(text = "Received Job ID: " + resp._jobID)  

            self.vf.GUI.ROOT.after(5, self.checkForRemoteResults)
            f.descr.entryByName['WS_Run']['widget'].configure(state = 'disabled')
#            f.descr.entryByName['APBSservicesLabel1']['widget'].\
#                           configure(text = 'Remote APBS calculation is done')
            self.rml = mol1.name
        except Exception, inst:
            f.descr.entryByName['APBSservicesLabel3']['widget'].\
                       configure(text = "")                
            from ZSI import FaultException
            if isinstance(inst, FaultException):
                tmp_str = inst.fault.AsSOAP()
                tmp_str = tmp_str.split('<message>')
                tmp_str = tmp_str[1].split('</message>')
                if self.cmdForms.has_key('default') and \
                     self.cmdForms['default'].f.winfo_toplevel().wm_state() == \
                                                                       'normal':
                    tkMessageBox.showerror("ERROR: ",tmp_str[0],parent = 
                                                  self.cmdForms['default'].root)
                else:
                    tkMessageBox.showerror("ERROR: ",tmp_str[0])            
            else:
                import traceback
                traceback.print_stack()
                traceback.print_exc()
            f.descr.entryByName['APBSservicesLabel1']['widget'].\
                       configure(text = "")
            f.descr.entryByName['APBSservicesLabel2']['widget'].\
                       configure(text = "ERROR!!! Unable to complete the Run")
            f.descr.entryByName['APBSservicesLabel3']['widget'].\
                       configure(text = "Please open Python Shell for Traceback")
            
    def checkForRemoteResults(self):
        """Checks the queue for remote results until we get one"""
        resp = self.apbsWS.appServicePort.queryStatus(queryStatusRequest(self.apbsWS.JobID))
        
        if resp._code == 8: # 8 = GramJob.STATUS_DONE
            f = self.cmdForms['default']
            f.descr.entryByName['APBSservicesLabel2']['widget'].\
                                          configure(text = resp._message)
            webbrowser.open(resp._baseURL)
            f.descr.entryByName['APBSservicesLabel3']['widget'].\
            configure(text = resp._baseURL,fg='Blue',cursor='hand1')
            def openurl(event):
                webbrowser.open(resp._baseURL)
            f.descr.entryByName['APBSservicesLabel3']['widget'].\
                                  bind(sequence="<Button-1>",func = openurl)
            # read the potential back
            opener = urllib.FancyURLopener(cert_file = APBS_proxy, key_file = APBS_proxy)
            if self.Parallel_flag:
                if self.npx*self.npy*self.npz == 1:
                    f.descr.entryByName['APBSservicesLabel4']['widget'].\
                    configure(text = "Downloading %s.potential-PE0.dx"%self.rml)
                    f.descr.entryByName['WS_ProgressBar']['widget'].\
                          grid(sticky='ew', row = 9, column = 0, columnspan = 2)
                    f.descr.entryByName['APBS_WS_DX_Label']['widget'].\
                       configure(text = "URI: "+resp._baseURL+"/%s.potential-PE0.dx"%self.rml)
                    self.progressBar.configure(progressformat='precent',
                                           labeltext='Progress ... ', max =100)
                    self.progressBar.set(0)
                    self._dx = opener.open(resp._baseURL+"/%s.potential-PE0.dx"%self.rml)
                    self._dx_out = open(os.path.join(self.params.projectFolder,
                                         "%s.potential.dx"%self.rml),"w")
                    bytes = int(self._dx.headers.dict['content-length'])
                    self._progress_counter = 0
                    self._download_bytes = bytes/100
                    if self._download_bytes == 0: self._download_bytes = 1
                    self.Download()                
                else:
                    f.descr.entryByName['APBSservicesLabel4']['widget'].\
                       configure(text = "Downloading %s.potential.dx. Please wait ..."%self.rml)

                    f.descr.entryByName['WS_ProgressBar']['widget'].\
                          grid(sticky='ew', row = 9, column = 0, columnspan = 2)
                    f.descr.entryByName['APBS_WS_DX_Label']['widget'].\
                       configure(text = "URI: "+resp._baseURL+"/%s.potential-PE*.dx"%self.rml)
                    self.progressBar.configure(progressformat='ratio',
                     labeltext='Progress ... ', max =self.npx*self.npy*self.npz)
                    self._progress_counter = 0
                    self.progressBar.set(0)                   
                    self._dx_files = []
                    for i in range(self.npx*self.npy*self.npz):
                        self._dx_files.append(opener.open(resp._baseURL+
                                       "/%s.potential-PE%d.dx"%(self.rml,i)))
                    self._dx_out = open(os.path.join(self.params.projectFolder,
                                             "%s.potential.dx"%self.rml),"w")
                    self._dx_out.write("# Data from %s\n"%resp._baseURL)
                    self._dx_out.write("#\n# POTENTIAL (kT/e)\n#\n")
                    self.Download_and_Merge()                
            else:                   
                f.descr.entryByName['APBSservicesLabel4']['widget'].\
                   configure(text = "Downloading %s.potential.dx"%self.rml)
                f.descr.entryByName['WS_ProgressBar']['widget'].\
                          grid(sticky='ew', row = 9, column = 0, columnspan = 2)
                f.descr.entryByName['APBS_WS_DX_Label']['widget'].\
                   configure(text = "URI: "+resp._baseURL + "/%s.potential.dx"%self.rml)
                self.progressBar.configure(progressformat='percent',
                                            labeltext='Progress ... ', max =100)                   
                self.progressBar.set(0)

                self._dx = opener.open(resp._baseURL + "/%s.potential.dx"%self.rml)
                filePath = os.path.join(self.params.projectFolder,"%s.potential.dx"%self.rml)
                try:
                    self._dx_out = open(filePath,"w")
                except IOError:
                    showerror("Download Failed!", 
                          "Permission denied: " +filePath)                

                bytes = int(self._dx.headers.dict['content-length'])
                self._progress_counter = 0
                self._download_bytes = bytes/100
                if self._download_bytes == 0: self._download_bytes = 1
                self.Download()                
            return
        else:
            f = self.cmdForms['default']
            f.descr.entryByName['APBSservicesLabel2']['widget'].\
                     configure(text = "Status: " + resp._message)       

        self.vf.GUI.ROOT.after(500, self.checkForRemoteResults)

    def Download(self):
        self._progress_counter += 1
        if self._progress_counter >  100:
            self._progress_counter =  100
        self.progressBar.set(self._progress_counter)
        tmp = self._dx.read(self._download_bytes)
        if tmp:
            self._dx_out.write(tmp)
        else:
            self._dx.close()
            self._dx_out.close()
            f = self.cmdForms['default']
            f.descr.entryByName['WS_ProgressBar']['widget'].grid_forget()
            f.descr.entryByName['APBS_WS_DX_Label']['widget'].\
                                                            configure(text = '')
            f.descr.entryByName['APBSservicesLabel4']['widget'].\
            configure(text="%s.potential.dx has been saved"%self.rml)
            self.saveProfile(self.params.name, fileFlag=True)
            self.changeMenuState('normal')
            f.descr.entryByName['WS_Run']['widget'].configure(state = 'normal')
            return     
        self.vf.GUI.ROOT.after(10, self.Download)
        
    def Download_and_Merge(self):
        self._dx_files[0].readline()
        self._dx_files[0].readline()
        self._dx_files[0].readline()
        self._dx_files[0].readline()
        tmp_str = self._dx_files[0].readline()
        from string import split
        w = split(tmp_str)
        nx, ny, nz = int(w[5]), int(w[6]), int(w[7])
        self._dx_out.write("object 1 class gridpositions counts %d %d %d\n"
             %(nx*self.npx,ny*self.npy,nz*self.npz))
        self._dx_out.write(self._dx_files[0].readline())
        self._dx_out.write(self._dx_files[0].readline())
        self._dx_out.write(self._dx_files[0].readline())
        self._dx_out.write(self._dx_files[0].readline())
        self._dx_out.write("object 2 class gridconnections counts %d %d %d\n"
             %(nx*self.npx,ny*self.npy,nz*self.npz))
        self._dx_out.write("object 3 class array type double rank 0 items %d"
         %(nx*self.npx*ny*self.npy*nz*self.npz)+" data follows\n")
        for file in self._dx_files[1:]:
            for i in range(11):
                file.readline()
        self._dx_files[0].readline()
        self._dx_files[0].readline()
        arrays = []
        for file in self._dx_files:
            self._progress_counter += 1
            self.progressBar.set(self._progress_counter)
            data = file.readlines()
            file.close()
            array = Numeric.zeros( (nx,ny,nz), Numeric.Float32)
            values = map(split, data[0:-5])
            ind=0
            size = nx*ny*nz
            for line in values:
                if ind>=size:
                    break
                l = len(line)
                array.flat[ind:ind+l] = map(float, line)
                ind = ind + l                            
            arrays.append(array)
        self.progressBar.configure(labeltext='Merging ... ')
        for k in range(self.npz):
            for j in range(self.npy):
                for i in range(self.npx):
                    if i == 0:
                        array_x = arrays[self.npx*j+
                                            self.npx*self.npy*k]
                    else:
                        array_x = Numeric.concatenate(
                                   (array_x,arrays[i+self.npx*j+
                                   self.npx*self.npy*k]),axis=0)
                if j == 0:
                    array_y = array_x
                else:
                    array_y = Numeric.concatenate(
                                       (array_y,array_x),axis=1)
            if k == 0:
                array_out = array_y
            else:
                array_out = Numeric.concatenate(
                                     (array_out,array_y),axis=2)
        for z in array_out:
            for y in z:
                for x in y:
                    self._dx_out.write(str(x)+"    ")
                self._dx_out.write('\n')
        self._dx_out.write("attribute \"dep\" string \"positions\"\n")
        self._dx_out.write("object \"regular positions regular connections\" class field\n")
        self._dx_out.write("component \"positions\" value 1\n")
        self._dx_out.write("component \"connections\" value 2\n")
        self._dx_out.write("component \"data\" value 3\n")
        self._dx_out.close()    
        f = self.cmdForms['default']
        f.descr.entryByName['WS_ProgressBar']['widget'].grid_forget()
        f.descr.entryByName['APBS_WS_DX_Label']['widget'].\
                                                        configure(text = '')
        f.descr.entryByName['APBSservicesLabel4']['widget'].\
        configure(text="%s.potential.dx has been saved"%self.rml)
        self.saveProfile(self.params.name, fileFlag=True)
        self.changeMenuState('normal')
        f.descr.entryByName['WS_Run']['widget'].configure(state = 'normal')
# Forms defined here

    def buildFormDescr(self, formName):
        """Builds 'error','ionForm','outputFilesForm','moleculeSelect' and
        'default' forms'"""
        if formName == 'error':
            if self.cmdForms.has_key('default') and \
                self.cmdForms['default'].f.winfo_toplevel().wm_state() == \
                                                                       'normal':
                    tkMessageBox.showerror("ERROR: ", self.errorMsg,parent = 
                                                  self.cmdForms['default'].root)
            else:
                tkMessageBox.showerror("ERROR: ", self.errorMsg)       
            return
        if formName == 'ionForm':
            ifd = InputFormDescr(title = "Add Ion")
            ifd.append({'name':'ionChargeLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Charge (e):'},
                    'gridcfg':{'row':0, 'column':0, 'sticky':'wens'}
                    })

            ifd.append({'widgetType':Pmw.EntryField,
                    'name':'ionCharge',
                    'wcfg':{'validate':{'validator':'real'}, 'value':1},
                    'gridcfg':{'row':0, 'column':1, 'sticky':'wens'}
                    })

            ifd.append({'name':'ionConcentrationLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Concentration (M):'},
                    'gridcfg':{'row':1, 'column':0, 'sticky':'wens'}
                    })
            ifd.append({'widgetType':ThumbWheel,
                    'name':'ionConcentration',
                                        'wcfg':{'text':None, 'showLabel':1,
                        'min':0,
                        'value':0.01, 'oneTurn':0.1, 
                        'type':'float',
                        'increment':0.01,
                        'wheelLabcfg1':{'font':
                                          (ensureFontCase('times'), 15, 'bold'), 'fill':'grey'},
                        'wheelLabcfg2':{'font':
                                         (ensureFontCase('times'), 15, 'bold'), 'fill':'black'},
                        'continuous':1,
                        'wheelPad':1, 'width':150,'height':14},
                    'gridcfg':{'row':1, 'column':1, 'sticky':'wens'}
                    })
            ifd.append({'name':'ionRadiusLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Radius (Angstroms):'},
                    'gridcfg':{'row':2, 'column':0, 'sticky':'wens'}
                    })
            ifd.append({'widgetType':Pmw.EntryField,
                    'name':'ionRadius',
                    'wcfg':{'validate':{'validator':'real','min':0}, 'value':1},
                    'gridcfg':{'row':2, 'column':1, 'sticky':'wens'}
                    })
            return ifd
        elif formName =='outputFilesForm':
            ifd = InputFormDescr(title = "Select output files")

            ifd.append({'name':'fileTypeLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'File Type'},
                    'gridcfg':{'sticky':'e', 'row':1, 'column':0}
                    })
            ifd.append({'name':'fileFormatLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'File format'},
                    'gridcfg':{'sticky':'e', 'row':1, 'column':1}
                    })
            ifd.append({'name':'chargeDistributionFileLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Charge distribution file: '},
                    'gridcfg':{'sticky':'e', 'row':2, 'column':0}
                    })
            ifd.append({'name':'chargeDistributionFile',
                    'widgetType':Pmw.ComboBox,
                    'wcfg':{'scrolledlist_items':self.params.FILETYPES,    
                            'listheight':100, 'dropdown':1, 'history':0,},
                    'defaultValue':self.params.chargeDistributionFile,
                    'gridcfg':{'sticky':'wens', 'row':2, 'column':1}
                    })
            ifd.append({'name':'potentialFileLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Potential file: '},
                    'gridcfg':{'sticky':'e', 'row':3, 'column':0}
                    })
            ifd.append({'name':'potentialFile',
                    'widgetType':Pmw.ComboBox,
                    'wcfg':{'scrolledlist_items':self.params.FILETYPES,
                            'listheight':100, 'history':0, 'dropdown':1},
                    'defaultValue':self.params.potentialFile,
                    'gridcfg':{'sticky':'wens', 'row':3, 'column':1}
                    })
            ifd.append({'name':'solventAccessibilityFileLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Solvent accessibility file: '},
                    'gridcfg':{'sticky':'e', 'row':4, 'column':0}
                    })
            ifd.append({'name':'solventAccessibilityFile',
                    'widgetType':Pmw.ComboBox,
                    'wcfg':{'scrolledlist_items':self.params.FILETYPES,
                            'listheight':100, 'history':0, 'dropdown':1},
                    'defaultValue':self.params.solventAccessibilityFile,
                    'gridcfg':{'sticky':'wens', 'row':4, 'column':1}
                    })
            ifd.append({'name':'splineBasedAccessibilityFileLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Spline-based accessibility file: '},
                    'gridcfg':{'sticky':'e', 'row':5, 'column':0}
                    })
            ifd.append({'name':'splineBasedAccessibilityFile',
                    'widgetType':Pmw.ComboBox,
                    'wcfg':{'scrolledlist_items':self.params.FILETYPES,
                            'listheight':100, 'history':0, 'dropdown':1},
                    'defaultValue':self.params.splineBasedAccessibilityFile,
                    'gridcfg':{'sticky':'wens', 'row':5, 'column':1}
                    })
            ifd.append({'name':'VDWAccessibilityFileLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'VDW accessibility file: '},
                    'gridcfg':{'sticky':'e', 'row':6, 'column':0}
                    })
            ifd.append({'name':'VDWAccessibilityFile',
                    'widgetType':Pmw.ComboBox,
                    'wcfg':{'scrolledlist_items':self.params.FILETYPES,
                            'listheight':100, 'history':0, 'dropdown':1},
                    'defaultValue':self.params.VDWAccessibilityFile,
                    'gridcfg':{'sticky':'wens', 'row':6, 'column':1}
                    })
            ifd.append({'name':'ionAccessibilityFileLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Ion accessibility file: '},
                    'gridcfg':{'sticky':'e', 'row':7, 'column':0}
                    })
            ifd.append({'name':'ionAccessibilityFile',
                    'widgetType':Pmw.ComboBox,
                    'wcfg':{'scrolledlist_items':self.params.FILETYPES,
                            'listheight':100, 'history':0, 'dropdown':1},
                    'defaultValue':self.params.ionAccessibilityFile,
                    'gridcfg':{'sticky':'wens', 'row':7, 'column':1}
                    })
            ifd.append({'name':'laplacianOfPotentialFileLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Laplacian of potential file: '},
                    'gridcfg':{'sticky':'e', 'row':8, 'column':0}
                    })
            ifd.append({'name':'laplacianOfPotentialFile',
                    'widgetType':Pmw.ComboBox,
                    'wcfg':{'scrolledlist_items':self.params.FILETYPES,
                            'listheight':100, 'history':0, 'dropdown':1},
                    'defaultValue':self.params.laplacianOfPotentialFile,
                    'gridcfg':{'sticky':'wens', 'row':8, 'column':1}
                    })
            ifd.append({'name':'energyDensityFileLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Energy density file: '},
                    'gridcfg':{'sticky':'e', 'row':9, 'column':0}
                    })
            ifd.append({'name':'energyDensityFile',
                    'widgetType':Pmw.ComboBox,
                    'wcfg':{'scrolledlist_items':self.params.FILETYPES,
                             'listheight':100, 'history':0, 'dropdown':1},
                    'defaultValue':self.params.energyDensityFile,
                    'gridcfg':{'sticky':'wens', 'row':9, 'column':1}
                    })
            ifd.append({'name':'ionNumberFileLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Ion number file: '},
                    'gridcfg':{'sticky':'e', 'row':10, 'column':0}
                    })
            ifd.append({'name':'ionNumberFile',
                    'widgetType':Pmw.ComboBox,
                    'wcfg':{'scrolledlist_items':self.params.FILETYPES,
                             'listheight':100, 'history':0, 'dropdown':1},
                    'defaultValue':self.params.ionNumberFile,
                    'gridcfg':{'sticky':'wens', 'row':10, 'column':1}
                    })
            ifd.append({'name':'ionChargeDensityFileLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Ion charge density file: '},
                    'gridcfg':{'sticky':'e', 'row':11, 'column':0}
                    })
            ifd.append({'name':'ionChargeDensityFile',
                    'widgetType':Pmw.ComboBox,
                    'wcfg':{'scrolledlist_items':self.params.FILETYPES,
                            'listheight':100, 'history':0, 'dropdown':1},
                    'defaultValue':self.params.ionChargeDensityFile,
                    'gridcfg':{'sticky':'wens', 'row':11, 'column':1}
                    })
            ifd.append({'name':'xShiftedDielectricFileLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'X-shifted dielectric file: '},
                    'gridcfg':{'sticky':'e', 'row':12, 'column':0}
                    })
            ifd.append({'name':'xShiftedDielectricFile',
                    'widgetType':Pmw.ComboBox,
                    'wcfg':{'scrolledlist_items':self.params.FILETYPES,
                            'listheight':100, 'history':0, 'dropdown':1},
                    'defaultValue':self.params.xShiftedDielectricFile,
                    'gridcfg':{'sticky':'wens', 'row':12, 'column':1}
                    })
            ifd.append({'name':'yShiftedDielectricFileLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Y-shifted dielectric file: '},
                    'gridcfg':{'sticky':'e', 'row':13, 'column':0}
                    })
            ifd.append({'name':'yShiftedDielectricFile',
                    'widgetType':Pmw.ComboBox,
                    'wcfg':{'scrolledlist_items':self.params.FILETYPES, 
                             'listheight':100, 'history':0, 'dropdown':1},
                    'defaultValue':self.params.yShiftedDielectricFile,
                    'gridcfg':{'sticky':'wens', 'row':13, 'column':1}
                    })
            ifd.append({'name':'zShiftedDielectricFileLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Z-shifted dielectric file: '},
                    'gridcfg':{'sticky':'e', 'row':14, 'column':0}
                    })
            ifd.append({'name':'zShiftedDielectricFile',
                    'widgetType':Pmw.ComboBox,
                    'wcfg':{'scrolledlist_items':self.params.FILETYPES,
                            'listheight':100, 'history':0, 'dropdown':1},
                    'defaultValue':self.params.zShiftedDielectricFile,
                    'gridcfg':{'sticky':'wens', 'row':14, 'column':1}
                    })
            ifd.append({'name':'kappaFunctionFileLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Kappa function file: '},
                    'gridcfg':{'sticky':'e', 'row':15, 'column':0}
                    })
            ifd.append({'name':'kappaFunctionFile',
                    'widgetType':Pmw.ComboBox,
                    'wcfg':{'scrolledlist_items':self.params.FILETYPES,
                            'listheight':100, 'history':0, 'dropdown':1},
                    'defaultValue':self.params.kappaFunctionFile,
                    'gridcfg':{'sticky':'wens', 'row':15, 'column':1}
                    })
            return ifd
        elif formName == 'moleculeSelect':
            ifd=InputFormDescr(title="Select a molecule")
            self.selectedFilename = ''
            molNames = self.vf.Mols.name
            if molNames is None:
                molNames = []
            ifd.append({'name':'moleculeListSelect',
                    'widgetType':Pmw.ScrolledListBox,
                    'tooltip':'Select a molecule loaded in PMV to run APBS ',
                    'wcfg':{'label_text':'Select Molecule: ',
                        'labelpos':'nw',
                        'items':molNames,
                        'listbox_selectmode':'single',
                        'listbox_exportselection':0,
                        'usehullsize': 1,
                        'hull_width':100,'hull_height':150,
                        'listbox_height':5},
                    'gridcfg':{'sticky':'nsew', 'row':1, 'column':0}})
        elif formName == 'default':
            ifd = InputFormDescr(title="APBS Profile Setup and Execution")
            ## NOTEBOOK WIDGET
            ifd.append({'widgetType':Pmw.NoteBook,
                                    'name':'hovigNotebook',
                                    'container':{'Calculation':
                                                        "w.page('Calculation')",
                                                  'Physics':"w.page('Physics')",
                                          'Web Service':"w.page('Web Service')",
                                                 'Grid':"w.page('Grid')"},
                                    'wcfg':{'borderwidth':3},
                                    'componentcfg':[{'name':'Calculation', 
                                                      'cfg':{}},
                                                      {'name':'Grid', 'cfg':{}},
                                                   {'name':'Physics','cfg':{}},
                                              {'name':'Web Service','cfg':{}} ],
                                    'gridcfg':{'sticky':'we'},
                                    })
            ## CALCULATION PAGE
            ## MATH GROUP 
            ifd.append({'name':"mathGroup",
                    'widgetType':Pmw.Group,
                    'parent':'Calculation',
                    'container':{'mathGroup':'w.interior()'},
                    'wcfg':{'tag_text':"Mathematics"},
                    'gridcfg':{'sticky':'wne'}
                    })
            ifd.append({'name':'calculationTypeLabel',
                    'widgetType':Tkinter.Label,
                                        'parent':'mathGroup',
                    'wcfg':{'text':'Calculation type:'},
                    'gridcfg':{'row':0, 'column':0, 'sticky':'e'}
                    })
            ifd.append({'name':'calculationType',
                    'widgetType':Pmw.ComboBox,
                    'parent':'mathGroup',
                    'wcfg':{'scrolledlist_items':self.params.CALCULATIONTYPES,
                            'history':0, 'dropdown':1,
                            'selectioncommand':self.calculationParamUpdate,
                            'listheight':80
                            },
                    'gridcfg':{'sticky':'we', 'row':0, 'column':1}
                    })
            ifd.append({'name':'pbeTypeLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'mathGroup',
                    'wcfg':{'text':'Poisson-Boltzmann equation type:'},
                    'gridcfg':{'row':1, 'column':0, 'sticky':'e'}
                    })
            ifd.append({'name':'pbeType',
                    'widgetType':Pmw.ComboBox,
                    'parent':'mathGroup',
                    'wcfg':{'scrolledlist_items':self.params.PBETYPES,
                             'history':0,'dropdown':1, 'listheight':80,
                             'selectioncommand':self.calculationParamUpdate},
                    'gridcfg':{'sticky':'we', 'row':1, 'column':1}
                    })
            ifd.append({'name':'boundaryConditionsLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'mathGroup',
                    'wcfg':{'text':'Boundary conditions:'},
                    'gridcfg':{'row':2, 'column':0, 'sticky':'e'}
                    })
            ifd.append({'name':'boundaryConditions',
                    'widgetType':Pmw.ComboBox,
                    'parent':'mathGroup',
                    'wcfg':{'scrolledlist_items':self.params.BOUNDARYTYPES,
                             'history':0, 'dropdown':1, 'listheight':80, 
                             'selectioncommand':self.calculationParamUpdate},
                    'gridcfg':{'sticky':'we', 'row':2, 'column':1}
                    })
            ifd.append({'name':'chargeDiscretizationLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'mathGroup',
                    'wcfg':{'text':'Charge discretization:'},
                    'gridcfg':{'sticky':'e', 'row':3, 'column':0}
                    })
            ifd.append({'name':'chargeDiscretization',
                    'widgetType':Pmw.ComboBox,
                    'parent':'mathGroup',
                    'wcfg':{'scrolledlist_items':
                              self.params.CHARGEDISCRETIZATIONTYPES,'history':0,
                             'dropdown':1, 'listheight':80,
                             'selectioncommand':self.calculationParamUpdate},
                    'gridcfg':{'sticky':'we', 'row':3, 'column':1}
                    })
            ifd.append({'name':'surfaceCalculationLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'mathGroup',
                    'wcfg':{'text':'Surface smoothing method:'},
                    'gridcfg':{'sticky':'e', 'row':4, 'column':0}
                    })
            ifd.append({'name':'surfaceCalculation',
                    'widgetType':Pmw.ComboBox,
                    'parent':'mathGroup',
                    'wcfg':{'scrolledlist_items':
                                self.params.SURFACECALCULATIONTYPES,'history':0,
                            'dropdown':1, 'listheight':80,
                            'selectioncommand':self.calculationParamUpdate},
                    'gridcfg':{'sticky':'we', 'row':4, 'column':1}
                    })
            ifd.append({'name':'sdensLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'mathGroup',
                    'wcfg':{'text':'Sphere density:'},
                    'gridcfg':{'row':5, 'column':0, 'sticky':'e'}
                    })
            ifd.append({'widgetType':Pmw.EntryField,
                    'name':'sdens',
                    'parent':'mathGroup',
                    'wcfg':{'command':self.calculationParamUpdate,
                        'value':self.params.sdens,
                        'validate':{'validator':'real', 'min':0.01}},
                    'gridcfg':{'sticky':'nsew', 'row':5, 'column':1}
                    })  
            ifd.append({'name':'splineWindowLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'mathGroup',
                    'wcfg':{'text':'Spline window (Angstroms):'},
                    'gridcfg':{'row':6, 'column':0, 'sticky':'e'}
                    })
            ifd.append({'widgetType':Pmw.EntryField,
                    'name':'splineWindow',
                    'parent':'mathGroup',
                    'wcfg':{'command':self.calculationParamUpdate,
                        'value':self.params.splineWindow,
                        'validate':{'validator':'real', 'min':0.01}},
                    'gridcfg':{'sticky':'nsew', 'row':6, 'column':1}
                    })
            # MOLECULES GROUP
            ifd.append({'name':"moleculesGroup",
                    'widgetType':Pmw.Group,
                    'parent':'Calculation',
                    'container':{'moleculesGroup':'w.interior()'},
                    'wcfg':{'tag_text':'Molecules'},
                    'gridcfg':{'sticky':'nswe'}
                    })
            ifd.append({'widgetType':Tkinter.Button,
                    'name':'molecule1Select',
                    'parent':'moleculesGroup',
                    'wcfg':{'text':'Select Molecule 1 ...',
                            
                            'command':self.molecule1Select},
                    'gridcfg':{'sticky':'ew', 'row':0, 'column':0}
                    })
            ifd.append({'widgetType':Pmw.EntryField,
                    'name':'molecule1',
                    'parent':'moleculesGroup',
                    'tooltip':"Click on Select Molecule 1 button to set this.",
                    'wcfg':{'command':self.calculationParamUpdate,
                            'entry_state':'disabled',
                            'value':self.params.molecule1Path},
                    'gridcfg':{'sticky':'ew', 'row':0, 'column':1}
                    })
            ifd.append({'widgetType':Tkinter.Button,
                    'name':'molecule2Select',
                    'parent':'moleculesGroup',
                    'wcfg':{'text':'Select Molecule 2 ...',
                        'command':self.molecule2Select},
                    'gridcfg':{'sticky':'ew', 'row':1, 'column':0}
                    })
            ifd.append({'widgetType':Pmw.EntryField,
                    'name':'molecule2',
                    'parent':'moleculesGroup',
                    'tooltip':"Click on Select Molecule 2 button to set this.",
                    'wcfg':{'command':self.calculationParamUpdate,
                            'entry_state':'disabled',
                            'value':self.params.molecule2Path},
                    'gridcfg':{'sticky':'ew', 'row':1, 'column':1}
                    })
            ifd.append({'widgetType':Tkinter.Button,
                    'name':'complexSelect',
                    'parent':'moleculesGroup',
                    'wcfg':{'text':'Select Complex ...',
                            'command':self.complexSelect},
                    'gridcfg':{'sticky':'ew', 'row':2, 'column':0}
                    })
            ifd.append({'widgetType':Pmw.EntryField,
                    'name':'complex',
                    'parent':'moleculesGroup',
                    'tooltip':"Click on Select Complex button to set this.",
                    'wcfg':{'command':self.calculationParamUpdate,
                            'entry_state':'disabled',
                            'value':self.params.complexPath},
                    'gridcfg':{'sticky':'ew', 'row':2, 'column':1}
                    })
            ## FILE GROUP
            ifd.append({'name':"fileGroup",
                                    'widgetType':Pmw.Group,
                                    'parent':'Calculation',
                                    'container':{'fileGroup':'w.interior()'},
                                    'wcfg':{'tag_text':'Output'},
                                    'gridcfg':{'sticky':'nwe'}
                                    })
            ifd.append({'name':'energyTypesLabel',
                                    'widgetType':Tkinter.Label,
                                    'parent':'fileGroup',
                                    'wcfg':{'text':'Energy: '},
                                    'gridcfg':{'sticky':'e','row':0, 'column':0}
                                    })
            ifd.append({'name':'energyOutput',
                        'widgetType':Pmw.ComboBox,
                        'parent':'fileGroup',
                        'wcfg':{'scrolledlist_items':
                                    self.params.ENERGYOUTPUTTYPES, 
                                'dropdown':1, 'history':0,'listheight':80,
                                'selectioncommand':self.calculationParamUpdate},
                         'gridcfg':{'sticky':'we', 'row':0, 'column':1}
                                    })
            ifd.append({'name':'forceTypesLabel',
                                    'widgetType':Tkinter.Label,
                                    'parent':'fileGroup',
                                    'wcfg':{'text':'Force: '},
                                    'gridcfg':{'sticky':'e', 'row':1,'column':0}
                                    })
            ifd.append({'name':'forceOutput',
                        'widgetType':Pmw.ComboBox,
                        'parent':'fileGroup',
                        'wcfg':{'scrolledlist_items':
                                    self.params.FORCEOUTPUTTYPES,
                                'dropdown':1, 'history':0, 'listheight':80,
                                'selectioncommand':self.calculationParamUpdate},
                         'gridcfg':{'sticky':'we','row':1,'column':1}
                                    })
            ifd.append({'widgetType':Tkinter.Button,
                                    'name':'outputFilesSelect',
                                    'parent':'fileGroup',
                                    'wcfg':{'text':'More output options ...',
                                            'command':self.setOutputFiles},
                                    'gridcfg':{'sticky':'ew','row':2,'column':1}
                                    })
            ## PROFILES GROUP
            ifd.append({'name':"ProfilesGroup",
                    'widgetType':Pmw.Group,
                    'parent':'Calculation',
                    'container':{'ProfilesGroup':'w.interior()'},
                    'wcfg':{'tag_text':'Profiles'},
                    'gridcfg':{'sticky':'we'}
                    })
            ifd.append({'name':'Profiles',
                    'widgetType':Pmw.ComboBox,
                    'parent':'ProfilesGroup',
                    'wcfg':{'scrolledlist_items':PROFILES, 'listheight':80,
                            'dropdown':1,'history':1,'autoclear':1,
                            'selectioncommand':self.select_profile
                      },
                      'gridcfg':{'sticky':'we', 'row':0, 'column':0}
                      })
            ifd.append({'widgetType':Tkinter.Button,
                    'name':'Profiles_Add',
                    'parent':'ProfilesGroup',
                    'wcfg':{'text':'Add',
                             'command':self.add_profile,
                             'state':state_GUI},
                    'gridcfg':{'sticky':'ew', 'row':0, 'column':1}
                    })
            ifd.append({'widgetType':Tkinter.Button,
                    'name':'Profiles_Remove',
                    'parent':'ProfilesGroup',
                    'wcfg':{'text':'Remove',
                            'state':state_GUI,
                            'command':self.remove_profile},
                    'gridcfg':{'sticky':'ew', 'row':0, 'column':2}
                    })
            ifd.append({'widgetType':Tkinter.Button,
                    'name':'Profiles_Run',
                    'parent':'ProfilesGroup',
                    'wcfg':{'text':'Run',
                            'state':state_GUI,
                            'command':self.apbsOutput},
                    'gridcfg':{'sticky':'we', 'row':1, 'column':0}
                    })
            ifd.append({'widgetType':Tkinter.Button,
                    'name':'Profiles_Load',
                    'parent':'ProfilesGroup',
                    'wcfg':{'text':'Load',
                            'command':self.loadProfile},
                    'gridcfg':{'sticky':'we', 'row':1, 'column':1}
                    })
            ifd.append({'widgetType':Tkinter.Button,
                    'name':'Profiles_Save',
                    'parent':'ProfilesGroup',
                    'wcfg':{'text':'Save',
                            'state':state_GUI,
                            'command':self.saveProfile},
                    'gridcfg':{'sticky':'we', 'row':1, 'column':2}
                    })
            ## GRID PAGE    
            ifd.append({'name':"generalGridGroup",
                    'widgetType':Pmw.Group,
                    'parent':'Grid',
                    'container':{'generalGridGroup':'w.interior()'},
                    'wcfg':{'tag_text':'General'},
                    'gridcfg':{'sticky':'wnse'}
                    })
            ifd.append({'name':'generalXLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'generalGridGroup',
                    'wcfg':{'text':'X','fg':'red','font':(ensureFontCase('times'), 15, 'bold')},
                     'gridcfg':{'row':0, 'column':1}
                    })
            ifd.append({'name':'generalYLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'generalGridGroup',
                    'wcfg':{'text':'Y','fg':'green','font':(ensureFontCase('times'),15,'bold')},
                     'gridcfg':{'row':0, 'column':2}
                    })
            ifd.append({'name':'generalZLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'generalGridGroup',
                    'wcfg':{'text':'Z','fg':'blue','font':(ensureFontCase('times'),15,' bold')},
                     'gridcfg':{'row':0, 'column':3}
                    })
            ifd.append({'name':'gridPointsLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'generalGridGroup',
                    'wcfg':{'text':'Grid Points:'},
                     'gridcfg':{'row':1, 'column':0}
                    })
            ifd.append({'widgetType':SliderWidget,
                    'name':'gridPointsX',
                    'parent':'generalGridGroup',
                    'wcfg':{'label':' ',
                    'minval':9,'maxval':689,
                    'left':15,
                    'command':self.gridParamUpdate,
                    'init':65,'immediate':1,
                    'sliderType':'int',
                    'lookup': self.params.GRID_VALUES},
                    'gridcfg':{'sticky':'wens', 'row':1, 'column':1}
                    })
            ifd.append({'widgetType':SliderWidget,
                    'name':'gridPointsY',
                    'parent':'generalGridGroup',
                    'wcfg':{'label':' ',
                    'minval':9,'maxval':689,
                    'left':15,
                    'command':self.gridParamUpdate,
                    'init':65,'immediate':1,
                    'sliderType':'int',
                    'lookup': self.params.GRID_VALUES},
                    'gridcfg':{'sticky':'wens', 'row':1, 'column':2}
                    })
            ifd.append({'widgetType':SliderWidget,
                    'name':'gridPointsZ',
                    'parent':'generalGridGroup',
                    'wcfg':{'label':' ',
                    'minval':9,'maxval':689,
                    'left':15,
                    'command':self.gridParamUpdate,
                    'init':65,'immediate':1,
                    'sliderType':'int',
                    'lookup': self.params.GRID_VALUES},
                    'gridcfg':{'sticky':'wens', 'row':1, 'column':3}
                    })
            ifd.append({'name':"coarseGridGroup",
                    'widgetType':Pmw.Group,
                    'parent':'Grid',
                    'container':{'coarseGridGroup':'w.interior()'},
                    'wcfg':{'tag_text':'Coarse Grid'},
                    'gridcfg':{'sticky':'wnse'}
                    })
            ifd.append({'name':'coarseXLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'coarseGridGroup',
                    'wcfg':{'text':'X','fg':'red','font':(ensureFontCase('times'), 15, 'bold')},
                     'gridcfg':{'row':1, 'column':1}
                    })
            ifd.append({'name':'coarseYLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'coarseGridGroup',
                    'wcfg':{'text':'Y','fg':'green','font':(ensureFontCase('times'),15,'bold')},
                     'gridcfg':{'row':1, 'column':2}
                    })
            ifd.append({'name':'coarseZLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'coarseGridGroup',
                    'wcfg':{'text':'Z','fg':'blue','font':(ensureFontCase('times'),15, 'bold')},
                     'gridcfg':{'row':1, 'column':3}
                    })
            ifd.append({'widgetType':Tkinter.Checkbutton,
                    'name':'showCoarseGrid',
                    'parent':'coarseGridGroup',
                    'defaultValue':0,
                    'wcfg':{'text':'Show Coarse Grid',
                    'command':self.gridParamUpdate,
                    'variable':Tkinter.BooleanVar()},
                    'gridcfg':{'sticky':'w','row':5, 'column':0}
                    })
            ifd.append({'name':'coarseLengthLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'coarseGridGroup',
                    'wcfg':{'text':'Length:'},
                     'gridcfg':{'row':2, 'column':0}
                    })
            ifd.append({'name':'coarseLengthX',
                    'widgetType':ThumbWheel,
                    'tooltip':
                       """Right click on the widget to type a value manually""",
                    'parent':'coarseGridGroup',
                    'gridcfg':{'row':2, 'column':1, 'sticky':'wnse'},
                    'wcfg':{'text':None, 'showLabel':1,
                        'min':2,
                        'lockBMin':1, 'lockBMax':1,
                        'lockBIncrement':1,
                        'value':self.params.coarseLengthX, 'oneTurn':1000, 
                        'type':'float',
                        'increment':1,
                        'canvascfg':{'bg':'red'},
                        'wheelLabcfg1':{'font':
                                          (ensureFontCase('times'), 15, 'bold'), 'fill':'grey'},
                        'wheelLabcfg2':{'font':
                                         (ensureFontCase('times'), 15, 'bold'), 'fill':'black'},
                        'callback':self.gridParamUpdate,
                        'continuous':1,
                        'wheelPad':1, 'width':100,'height':15}
                    })
            ifd.append({'name':'coarseLengthY',
                    'widgetType':ThumbWheel,
                    'tooltip':
                       """Right click on the widget to type a value manually""",
                    'parent':'coarseGridGroup',
                    'gridcfg':{'row':2, 'column':2, 'sticky':'wnse'},
                    'wcfg':{ 'showLabel':1,
                        'min':2,
                        'lockBMin':1, 'lockBMax':1,
                        'lockBIncrement':1,
                        'value':self.params.coarseLengthY, 'oneTurn':1000, 
                        'type':'float',
                        'increment':1,
                        'canvascfg':{'bg':'green'},
                        'wheelLabcfg1':{'font':
                                          (ensureFontCase('times'), 15, 'bold'), 'fill':'grey'},
                        'wheelLabcfg2':{'font':
                                         (ensureFontCase('times'), 15, 'bold'), 'fill':'black'},
                        'callback':self.gridParamUpdate,
                        'continuous':1,
                        'wheelPad':1, 'width':100,'height':15}
                    })
            ifd.append({'name':'coarseLengthZ',
                    'widgetType':ThumbWheel,
                    'tooltip':
                       """Right click on the widget to type a value manually""",
                    'parent':'coarseGridGroup',
                    'gridcfg':{'row':2, 'column':3, 'sticky':'wnse'},
                    'wcfg':{'showLabel':1,
                        'min':2,
                        'lockBMin':1, 'lockBMax':1,
                        'lockBIncrement':1,
                        'value':self.params.coarseLengthZ, 'oneTurn':1000, 
                        'type':'float',
                        'increment':1,
                        'canvascfg':{'bg':'blue'},
                        'wheelLabcfg1':{'font':
                                          (ensureFontCase('times'), 15, 'bold'), 'fill':'grey'},
                        'wheelLabcfg2':{'font':
                                         (ensureFontCase('times'), 15, 'bold'), 'fill':'black'},
                        'callback':self.gridParamUpdate,
                        'continuous':1,
                        'wheelPad':1, 'width':100,'height':15}
                    })
            ifd.append({'name':'coarseCenterLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'coarseGridGroup',
                    'wcfg':{'text':'Center:'},
                     'gridcfg':{'row':3, 'column':0}
                    })
            ifd.append({'name':'coarseCenterX',
                    'widgetType':ThumbWheel,
                    'tooltip':
                       """Right click on the widget to type a value manually""",
                    'parent':'coarseGridGroup',
                    'gridcfg':{'row':3, 'column':1, 'sticky':'wnse'},
                    'wcfg':{ 'showLabel':1,
                        'min':None,
                        'lockBMin':1, 'lockBMax':1,
                        'lockBIncrement':1,
                        'value':self.params.coarseCenterX, 'oneTurn':1000, 
                        'type':'float',
                        'increment':1,
                        'canvascfg':{'bg':'red'},
                        'wheelLabcfg1':{'font':
                                          (ensureFontCase('times'), 15, 'bold'), 'fill':'grey'},
                        'wheelLabcfg2':{'font':
                                         (ensureFontCase('times'), 15, 'bold'), 'fill':'black'},
                        'callback':self.gridParamUpdate,
                        'continuous':1,
                        'wheelPad':1, 'width':100,'height':15}
                    })
            ifd.append({'name':'coarseCenterY',
                    'widgetType':ThumbWheel,
                    'tooltip':
                       """Right click on the widget to type a value manually""",
                    'parent':'coarseGridGroup',
                    'gridcfg':{'row':3, 'column':2, 'sticky':'wnse'},
                    'wcfg':{'showLabel':1,
                        'min':None,
                        'lockBMin':1, 'lockBMax':1,
                        'lockBIncrement':1,
                        'value':self.params.coarseCenterY, 'oneTurn':1000, 
                        'type':'float',
                        'increment':1,
                        'canvascfg':{'bg':'green'},
                        'wheelLabcfg1':{'font':
                                          (ensureFontCase('times'), 15, 'bold'), 'fill':'grey'},
                        'wheelLabcfg2':{'font':
                                         (ensureFontCase('times'), 15, 'bold'), 'fill':'black'},
                        'callback':self.gridParamUpdate,
                        'continuous':1,
                        'wheelPad':1, 'width':100,'height':15}
                    })
            ifd.append({'name':'coarseCenterZ',
                    'widgetType':ThumbWheel,
                    'tooltip':
                       """Right click on the widget to type a value manually""",
                    'parent':'coarseGridGroup',
                    'gridcfg':{'row':3, 'column':3, 'sticky':'wnse'},
                    'wcfg':{'text':None, 'showLabel':1,
                        'min':None,
                        'lockBMin':1, 'lockBMax':1,
                        'lockBIncrement':1,
                        'value':self.params.coarseCenterZ, 'oneTurn':1000, 
                        'type':'float',
                        'increment':1,
                        'canvascfg':{'bg':'blue'},
                        'wheelLabcfg1':{'font':
                                          (ensureFontCase('times'), 15, 'bold'), 'fill':'grey'},
                        'wheelLabcfg2':{'font':
                                         (ensureFontCase('times'), 15, 'bold'), 'fill':'black'},
                        'callback':self.gridParamUpdate,
                        'continuous':1,
                        'wheelPad':1, 'width':100,'height':15}
                    })
            ifd.append({'name':'coarseResolutionLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'coarseGridGroup',
                    'wcfg':{'text':'Resolution:'},
                     'gridcfg':{'row':4, 'column':0}
                    })
            ifd.append({'name':'coarseResolutionX',
                    'widgetType':Tkinter.Label,
                    'parent':'coarseGridGroup',
                    'wcfg':{'text':"%5.3f"%self.coarseResolutionX()},
                     'gridcfg':{'row':4, 'column':1}
                    })
            ifd.append({'name':'coarseResolutionY',
                    'widgetType':Tkinter.Label,
                    'parent':'coarseGridGroup',
                    'wcfg':{'text':"%5.3f"%self.coarseResolutionY()},
                     'gridcfg':{'row':4, 'column':2}
                    })
            ifd.append({'name':'coarseResolutionZ',
                    'widgetType':Tkinter.Label,
                    'parent':'coarseGridGroup',
                    'wcfg':{'text':"%5.3f"%self.coarseResolutionZ()},
                     'gridcfg':{'row':4, 'column':3}
                    })
            ifd.append({'widgetType':Tkinter.Button,
                    'name':'autocenterCoarseGrid',
                    'parent':'coarseGridGroup',
                    'wcfg':{'text':'Autocenter',
                            'command':self.autocenterCoarseGrid},
                    'gridcfg':{'sticky':'ew', 'row':5, 'column':1}
                    })
            ifd.append({'widgetType':Tkinter.Button,
                    'name':'autosizeCoarseGrid',
                    'parent':'coarseGridGroup',
                    'wcfg':{'text':'Autosize',
                            'command':self.autosizeCoarseGrid},
                    'gridcfg':{'sticky':'ew', 'row':5, 'column':2}
                    })
            ifd.append({'name':"fineGridGroup",
                    'widgetType':Pmw.Group,
                    'parent':'Grid',
                    'container':{'fineGridGroup':'w.interior()'},
                    'wcfg':{'tag_text':'Fine Grid'},
                    'gridcfg':{'sticky':'wnse'}
                    })
            ifd.append({'name':'fineXLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'fineGridGroup',
                    'wcfg':{'text':'X','fg':'red','font':(ensureFontCase('times'), 15, 'bold')},
                     'gridcfg':{'row':1, 'column':1}
                    })
            ifd.append({'name':'fineYLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'fineGridGroup',
                    'wcfg':{'text':'Y','fg':'green','font':(ensureFontCase('times'),15,'bold')},
                     'gridcfg':{'row':1, 'column':2}
                    })
            ifd.append({'name':'fineZLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'fineGridGroup',
                    'wcfg':{'text':'Z','fg':'blue','font':(ensureFontCase('times'),15, 'bold')},
                     'gridcfg':{'row':1, 'column':3}
                    })
            ifd.append({'widgetType':Tkinter.Checkbutton,
                    'name':'showFineGrid',
                    'parent':'fineGridGroup',
                    'defaultValue':0,
                    'wcfg':{'text':'Show Fine Grid',
                    'command':self.gridParamUpdate,
                    'variable':Tkinter.BooleanVar()},
                    'gridcfg':{'sticky':'w','row':5, 'column':0}
                    })
            ifd.append({'name':'fineLengthLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'fineGridGroup',
                    'wcfg':{'text':'Length:'},
                     'gridcfg':{'row':2, 'column':0}
                    })
            ifd.append({'name':'fineLengthX',
                    'widgetType':ThumbWheel,
                    'tooltip':
                       """Right click on the widget to type a value manually""",
                    'parent':'fineGridGroup',
                    'gridcfg':{'row':2, 'column':1, 'sticky':'wnse'},
                    'wcfg':{'showLabel':1,
                        'min':2,
                        'lockBMin':1, 'lockBMax':1,
                        'lockBIncrement':1,
                        'value':self.params.fineLengthX, 'oneTurn':1000, 
                        'type':'float',
                        'increment':.25,
                        'canvascfg':{'bg':'red'},
                        'wheelLabcfg1':{'font':
                                          (ensureFontCase('times'), 15, 'bold'), 'fill':'grey'},
                        'wheelLabcfg2':{'font':
                                         (ensureFontCase('times'), 15, 'bold'), 'fill':'black'},
                        'callback':self.gridParamUpdate,
                        'continuous':1,
                        'wheelPad':1, 'width':100,'height':15}
                    })
            ifd.append({'name':'fineLengthY',
                    'widgetType':ThumbWheel,
                    'tooltip':
                       """Right click on the widget to type a value manually""",
                    'parent':'fineGridGroup',
                    'gridcfg':{'row':2, 'column':2, 'sticky':'wnse'},
                    'wcfg':{'showLabel':1,
                        'min':2,
                        'lockBMin':1, 'lockBMax':1,
                        'lockBIncrement':1,
                        'value':self.params.fineLengthY, 'oneTurn':1000, 
                        'type':'float',
                        'increment':.25,
                        'canvascfg':{'bg':'green'},
                        'wheelLabcfg1':{'font':
                                          (ensureFontCase('times'), 15, 'bold'), 'fill':'grey'},
                        'wheelLabcfg2':{'font':
                                         (ensureFontCase('times'), 15, 'bold'), 'fill':'black'},
                        'callback':self.gridParamUpdate,
                        'continuous':1,
                        'wheelPad':1, 'width':100,'height':15}
                    })
            ifd.append({'name':'fineLengthZ',
                    'widgetType':ThumbWheel,
                    'tooltip':
                       """Right click on the widget to type a value manually""",
                    'parent':'fineGridGroup',
                    'gridcfg':{'row':2, 'column':3, 'sticky':'wnse'},
                    'wcfg':{'showLabel':1,
                        'min':2,
                        'lockBMin':1, 'lockBMax':1,
                        'lockBIncrement':1,
                        'value':self.params.fineLengthZ, 'oneTurn':1000, 
                        'type':'float',
                        'increment':.25,
                        'canvascfg':{'bg':'blue'},
                        'wheelLabcfg1':{'font':
                                          (ensureFontCase('times'), 15, 'bold'), 'fill':'grey'},
                        'wheelLabcfg2':{'font':
                                         (ensureFontCase('times'), 15, 'bold'), 'fill':'black'},
                        'callback':self.gridParamUpdate,
                        'continuous':1,
                        'wheelPad':1, 'width':100,'height':15}
                    })
            ifd.append({'name':'fineCenterLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'fineGridGroup',
                    'wcfg':{'text':'Center:'},
                     'gridcfg':{'row':3, 'column':0}
                    })
            ifd.append({'name':'fineCenterX',
                    'widgetType':ThumbWheel,
                    'tooltip':
                       """Right click on the widget to type a value manually""",
                    'parent':'fineGridGroup',
                    'gridcfg':{'row':3, 'column':1, 'sticky':'wnse'},
                    'wcfg':{'showLabel':1,
                        'min':None,
                        'lockBMin':1, 'lockBMax':1,
                        'lockBIncrement':1,
                        'value':self.params.fineCenterX, 'oneTurn':1000, 
                        'type':'float',
                        'increment':.25,
                        'canvascfg':{'bg':'red'},
                        'wheelLabcfg1':{'font':
                                          (ensureFontCase('times'), 15, 'bold'), 'fill':'grey'},
                        'wheelLabcfg2':{'font':
                                         (ensureFontCase('times'), 15, 'bold'), 'fill':'black'},
                        'callback':self.gridParamUpdate,
                        'continuous':1,
                        'wheelPad':1, 'width':100,'height':15}
                    })
            ifd.append({'name':'fineCenterY',
                    'widgetType':ThumbWheel,
                    'tooltip':
                       """Right click on the widget to type a value manually""",
                    'parent':'fineGridGroup',
                    'gridcfg':{'row':3, 'column':2, 'sticky':'wnse'},
                    'wcfg':{'showLabel':1,
                        'min':None,
                        'lockBMin':1, 'lockBMax':1,
                        'lockBIncrement':1,
                        'value':self.params.fineCenterY, 'oneTurn':1000, 
                        'type':'float',
                        'increment':.25,
                        'canvascfg':{'bg':'green'},
                        'wheelLabcfg1':{'font':
                                          (ensureFontCase('times'), 15, 'bold'), 'fill':'grey'},
                        'wheelLabcfg2':{'font':
                                         (ensureFontCase('times'), 15, 'bold'), 'fill':'black'},
                        'callback':self.gridParamUpdate,
                        'continuous':1,
                        'wheelPad':1, 'width':100,'height':15}
                    })
            ifd.append({'name':'fineCenterZ',
                    'widgetType':ThumbWheel,
                    'tooltip':
                       """Right click on the widget to type a value manually""",
                    'parent':'fineGridGroup',
                    'gridcfg':{'row':3, 'column':3, 'sticky':'wnse'},
                    'wcfg':{'showLabel':1,
                        'min':None,
                        'lockBMin':1, 'lockBMax':1,
                        'lockBIncrement':1,
                        'value':self.params.fineCenterZ, 'oneTurn':1000, 
                        'type':'float',
                        'increment':.25,
                        'canvascfg':{'bg':'blue'},
                        'wheelLabcfg1':{'font':
                                          (ensureFontCase('times'), 15, 'bold'), 'fill':'grey'},
                        'wheelLabcfg2':{'font':
                                         (ensureFontCase('times'), 15, 'bold'), 'fill':'black'},
                        'callback':self.gridParamUpdate,
                        'continuous':1,
                        'wheelPad':1, 'width':100,'height':15}
                    })
            ifd.append({'name':'fineResolutionLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'fineGridGroup',
                    'wcfg':{'text':'Resolution:'},
                     'gridcfg':{'row':4, 'column':0}
                    })

            ifd.append({'name':'fineResolutionX',
                    'widgetType':Tkinter.Label,
                    'parent':'fineGridGroup',
                    'wcfg':{'text':"%5.3f"%self.fineResolutionX()},
                     'gridcfg':{'row':4, 'column':1}
                    })
            ifd.append({'name':'fineResolutionY',
                    'widgetType':Tkinter.Label,
                    'parent':'fineGridGroup',
                    'wcfg':{'text':"%5.3f"%self.fineResolutionY()},
                     'gridcfg':{'row':4, 'column':2}
                    })
            ifd.append({'name':'fineResolutionZ',
                    'widgetType':Tkinter.Label,
                    'parent':'fineGridGroup',
                    'wcfg':{'text':"%5.3f"%self.fineResolutionZ()},
                     'gridcfg':{'row':4, 'column':3}
                    })
            ifd.append({'widgetType':Tkinter.Button,
                    'name':'autocenterFineGrid',
                    'parent':'fineGridGroup',
                    'wcfg':{'text':'Autocenter',
                            'command':self.autocenterFineGrid},
                    'gridcfg':{'sticky':'ew', 'row':5, 'column':1}
                    })
            ifd.append({'widgetType':Tkinter.Button,
                    'name':'autosizeFineGrid',
                    'parent':'fineGridGroup',
                    'wcfg':{'text':'Autosize',
                            'command':self.autosizeFineGrid},
                    'gridcfg':{'sticky':'ew', 'row':5, 'column':2}
                    })
            ifd.append({'name':"systemResourcesGroup",
                    'widgetType':Pmw.Group,
                    'parent':'Grid',
                    'container':{'systemResourcesGroup':'w.interior()'},
                    'wcfg':{'tag_text':'System Resources'},
                    'gridcfg':{'sticky':'wnse'}
                    })
            ifd.append({'name':'gridPointsLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'systemResourcesGroup',
                    'wcfg':{'text':'Total grid points: '},
                     'gridcfg':{'row':0, 'column':0, 'sticky':'e'}
                    })
            ifd.append({'name':'gridPointsNumberLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'systemResourcesGroup',
                    'wcfg':{'text':"%d"%self.totalGridPoints()},
                     'gridcfg':{'row':0, 'column':1, 'sticky':'w'}
                    })
            ifd.append({'name':'mallocLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'systemResourcesGroup',
                    'wcfg':{'text':'Memory to be allocated (MB): '},
                     'gridcfg':{'row':1, 'column':0, 'sticky':'e'}
                    })
            ifd.append({'name':'mallocSizeLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'systemResourcesGroup',
                    'wcfg':{'text':"%5.3f"%self.memoryToBeAllocated()},
                     'gridcfg':{'row':1, 'column':1, 'sticky':'w'}
                    })
            ## PHYSICS PAGE
            ifd.append({'name':'parametersGroup',
                    'widgetType':Pmw.Group,
                    'parent':'Physics',
                    'container':{'parametersGroup':'w.interior()'},
                    'wcfg':{'tag_text':"Parameters"},
                    'gridcfg':{'sticky':'snwe'}
                    })
            ifd.append({'name':'proteinDielectricLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'parametersGroup',
                    'wcfg':{'text':'Protein dielectric:'},
                    'gridcfg':{'row':0, 'column':0, 'sticky':'e'}
                    })
            ifd.append({'widgetType':Pmw.EntryField,
                    'name':'proteinDielectric',
                    'parent':'parametersGroup',
                    'wcfg':{'command':self.physicsParamUpdate,
                        'value':self.params.proteinDielectric,
                        'validate':{'validator':'real', 'min':0}},
                    'gridcfg':{'sticky':'ew', 'row':0, 'column':1}
                    })
            ifd.append({'name':'solventDielectricLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'parametersGroup',
                    'wcfg':{'text':'Solvent dielectric:'},
                    'gridcfg':{'row':1, 'column':0, 'sticky':'e'}
                    })
            ifd.append({'widgetType':Pmw.EntryField,
                    'name':'solventDielectric',
                    'parent':'parametersGroup',
                    'wcfg':{'command':self.physicsParamUpdate,
                        'value':self.params.solventDielectric,
                        'validate':{'validator':'real', 'min':0}},
                    'gridcfg':{'sticky':'nsew', 'row':1, 'column':1}
                    })
            ifd.append({'name':'solventRadiusLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'parametersGroup',
                    'wcfg':{'text':'Solvent radius (Angstroms):'},
                    'gridcfg':{'row':2, 'column':0, 'sticky':'e'}
                    })
            ifd.append({'widgetType':Pmw.EntryField,
                    'name':'solventRadius',
                    'parent':'parametersGroup',
                    'wcfg':{'command':self.physicsParamUpdate,
                        'value':self.params.solventRadius,
                        'validate':{'validator':'real', 'min':0}},
                    'gridcfg':{'sticky':'nsew', 'row':2, 'column':1}
                    })
            ifd.append({'name':'systemTemperatureLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'parametersGroup',
                    'wcfg':{'text':'System temperature (Kelvin):'},
                    'gridcfg':{'row':3, 'column':0, 'sticky':'e'}
                    })
            ifd.append({'widgetType':Pmw.EntryField,
                    'name':'systemTemperature',
                    'parent':'parametersGroup',
                    'wcfg':{'command':self.physicsParamUpdate,
                        'value':self.params.systemTemperature,
                        'validate':{'validator':'real', 'min':0}},
                    'gridcfg':{'sticky':'nsew', 'row':3, 'column':1}
                    })
            ifd.append({'name':'ionsGroup',
                    'widgetType':Pmw.Group,
                    'parent':'Physics',
                    'container':{'ionsGroup':'w.interior()'},
                    'wcfg':{'tag_text':"Ions"},
                    'gridcfg':{'sticky':'wnse'}
                    })
            ifd.append({'widgetType':Pmw.Group,
                'name':'SaltGroup',
                'container':{'SaltGroup':'w.interior()'},
                'parent':'ionsGroup',
                'wcfg':{
                'tag_pyclass':Tkinter.Checkbutton,
                'tag_text':'Salt',
                'tag_command':self.SaltUpdate,
                'tag_variable': self.salt_var,
                },
                
                })

#            ifd.append({'name':'ionConcentrationLabel',
#                    'widgetType':Tkinter.Label,
#                    'wcfg':{'text':'Salt contains ions with radius 2 (Angstrom), and charges +1(e) and -1(e)'},
#                    'parent':'SaltGroup',
#                    'gridcfg':{'row':0, 'column':0,'columnspan':2, 'sticky':'we'}
#                    })
            
            ifd.append({'name':'ionConcentrationLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Concentration (M):'},
                    'parent':'SaltGroup',
                    'gridcfg':{'row':1, 'column':0, 'sticky':'e'}
                    })
            ifd.append({'widgetType':ThumbWheel,
                    'name':'saltConcentration',
                    'parent':'SaltGroup',
                                        'wcfg':{'text':None, 'showLabel':1,
                        'min':0,
                        'value':0.01, 'oneTurn':0.1, 
                        'type':'float',
                        'increment':0.01,
                        'wheelLabcfg1':{'font':
                                          (ensureFontCase('times'), 15, 'bold'), 'fill':'grey'},
                        'wheelLabcfg2':{'font':
                                         (ensureFontCase('times'), 15, 'bold'), 'fill':'black'},
                        'continuous':1,
                        'wheelPad':1, 'width':150,'height':14},
                    'gridcfg':{'row':1, 'column':1, 'sticky':'w'}
                    })
            
            ifd.append({'name':'ionsButtons',
                    'widgetType':Pmw.ButtonBox,
                    'parent':'ionsGroup',
                    'wcfg':{},
                    'componentcfg':[{'name':'Add More...', 
                                      'cfg':{'command':self.addIon}},
                        {'name':'Remove', 'cfg':{'command':self.removeIon}}]
                    })
            ifd.append({'name':'ionsListLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'ionsGroup',
                    'wcfg':{'text':'Charge, Concentration, Radius'}
                    })
            ifd.append({'widgetType':Pmw.ScrolledListBox,
                    'name':'ionsList',
                    'parent':'ionsGroup',
                    'wcfg':{}
                    })   
            ## WEB SERVICES PAGE
            if APBSservicesFound:
                ifd.append({'name':"APBSservicesGroup",
                    'widgetType':Pmw.Group,
                    'parent':'Web Service',
                    'container':{'APBSservicesGroup':'w.interior()'},
                    'wcfg':{'tag_text':'APBS Web Services'},
                    'gridcfg':{'sticky':'wen'}
                    })
                ifd.append({'widgetType':Tkinter.Button,
                                        'name':'WS_Run',
                                        'parent':'APBSservicesGroup',
                                        'wcfg':{'text':'Run APBS Remote',
                                                 'state':state_GUI,
                                                'command':self.apbsRunRemote},
                                  'gridcfg':{'sticky':'ew', 'row':0, 'column':0}
                                        })
                ifd.append({'widgetType':Pmw.ComboBox,
                            'name':'web service address',
                            'parent':'APBSservicesGroup',
                            'wcfg':{'scrolledlist_items':
                                       ('http://ws.nbcr.net/opal2/services/ApbsOpalService',),
                                    'selectioncommand':self.toggle_usrpass,
                                    'listheight':100,
                                    'dropdown':1, 'history':1, 'autoclear':1},
                             'gridcfg':{'sticky':'ew', 'row':0, 'column':1}
                                        })
                ifd.append({'widgetType':Tkinter.Label,
                                        'name':'UserName_Label',
                                        'parent':'APBSservicesGroup',
                                        'wcfg':{'text':'User Name'},
                                  'gridcfg':{'sticky':'e', 'row':1, 'column':0}
                                        })
                ifd.append({'widgetType':Tkinter.Entry,
                                        'name':'UserName_Entry',
                                        'parent':'APBSservicesGroup',
                                        'wcfg':{},
                                  'gridcfg':{'sticky':'ew', 'row':1, 'column':1}
                                        })
                ifd.append({'widgetType':Tkinter.Label,
                                        'name':'Password_Label',
                                        'parent':'APBSservicesGroup',
                                        'wcfg':{'text':'Password'},
                                  'gridcfg':{'sticky':'e', 'row':2, 'column':0}
                                        })
                ifd.append({'widgetType':Tkinter.Entry,
                                        'name':'Password_Entry',
                                        'parent':'APBSservicesGroup',
                                        'wcfg':{'show':'*'},
                                  'gridcfg':{'sticky':'ew', 'row':2, 'column':1}
                                        })
                ifd.append({'widgetType':Tkinter.Label,
                                        'name':'Remember_Label',
                                        'parent':'APBSservicesGroup',
                                        'wcfg':{'text':'Remember User Name and Password'},
                                  'gridcfg':{'sticky':'e', 'row':3, 'column':0}
                                        })
                ifd.append({'widgetType':Tkinter.Checkbutton,
                                        'name':'Remember_Checkbutton',
                                        'parent':'APBSservicesGroup',
                                        'variable':self.RememberLogin_var,
                                  'gridcfg':{'sticky':'w', 'row':3, 'column':1}
                                        })       
#                self.Parallel_var =Tkinter.BooleanVar()
#                self.Parallel_var.set(0)
#                ifd.append({'widgetType':Pmw.Group,
#                    'name':'ParallelGroup',
#                    'container':{'ParallelGroup':'w.interior()'},
#                    'parent':'APBSservicesGroup',
#                    'wcfg':{
#                    'tag_pyclass':Tkinter.Checkbutton,
#                    'tag_text':'Parallel',
#                    'tag_command':self.ParallelParamUpdate,
#                    'tag_variable': self.Parallel_var,
#                    },
#                    'gridcfg':{'sticky':'new','row':4, 'column':0,'columnspan':2
#                             , 'pady':'10' }
#                    })
#                ifd.append({'widgetType':Pmw.EntryField,
#                    'name':'npx',
#                    'parent':'ParallelGroup',
#                    'state':'disabled',
#                    'wcfg':{
#                        'validate':{'validator':'integer', 'min':1},
#              'label_text':'The number of processors in the X direction (npx):',
#                    'labelpos':'w',
#                    'value':2,},
#                    'gridcfg':{ 'row':0, 'column':0}
#                    })
#                ifd.append({'widgetType':Pmw.EntryField,
#                    'name':'npy',
#                    'parent':'ParallelGroup',
#                    'wcfg':{
#                        'validate':{'validator':'integer', 'min':1},
#              'label_text':'The number of processors in the Y direction (npy):',
#                    'labelpos':'w',
#                    'value':1,},
#                    'gridcfg':{'row':1, 'column':0}
#                    })
#                ifd.append({'widgetType':Pmw.EntryField,
#                    'name':'npz',
#                    'parent':'ParallelGroup',
#                    
#                    'wcfg':{
#                        'validate':{'validator':'integer', 'min':1},
#              'label_text':'The number of processors in the Z direction (npz):',
#                    'labelpos':'w',
#                    'value':1,                                     
#                                     },
#                    'gridcfg':{'row':2, 'column':0}
#                    })   
#                ifd.append({'widgetType':Pmw.EntryField,
#                    'name':'ofrac',
#                    'parent':'ParallelGroup',
#                    'wcfg':{
#                        'validate':{'validator':'real', 'min':0,'max':1},
#             'label_text':'Overlap factor (ofrac); a value between 0 and 1   :',
#                    'labelpos':'w',                 
#                    'value':0.1,
#                                     },
#                    'gridcfg':{'row':3, 'column':0}
#                    })
                ifd.append({'name':'APBSservicesLabel1',
                                    'widgetType':Tkinter.Label,
                                    'parent':'APBSservicesGroup',
                                    'wcfg':{'text':''},
                                 'gridcfg':{'sticky':'ensw', 'row':5,'column':0,
                                                'columnspan':2}
                                    })
                ifd.append({'name':'APBSservicesLabel2',
                                    'widgetType':Tkinter.Label,
                                    'parent':'APBSservicesGroup',
                                    'wcfg':{'text':''},
                                 'gridcfg':{'sticky':'ensw', 'row':6,'column':0,
                                                'columnspan':2}
                                    })
                ifd.append({'name':'APBSservicesLabel3',
                                    'widgetType':Tkinter.Label,
                                    'parent':'APBSservicesGroup',
                                    'wcfg':{'text':''},
                                 'gridcfg':{'sticky':'ensw', 'row':7,'column':0,
                                                'columnspan':2}
                                    })                  
                ifd.append({'name':'APBSservicesLabel4',
                                    'widgetType':Tkinter.Label,
                                    'parent':'APBSservicesGroup',
                                    'wcfg':{'text':''},
                                 'gridcfg':{'sticky':'ensw', 'row':8,'column':0,
                                                'columnspan':2}
                                    })
                ifd.append({'name':'WS_ProgressBar',
                                    'widgetType':Tkinter.Frame,
                                    'parent':'APBSservicesGroup',
                                    'wcfg':{'height':30},
                                 'gridcfg':{'sticky':'ew', 'row':9,'column':0,
                                            'columnspan':2}
                                    })
                ifd.append({'name':'APBS_WS_DX_Label',
                                    'widgetType':Tkinter.Label,
                                    'parent':'APBSservicesGroup',
                                    'wcfg':{'text':''},
                                 'gridcfg':{'sticky':'ensw', 'row':10,'column':0,
                                                'columnspan':2}
                                    })
            else:
                ifd.append({'name':'WS_Not_Found',
                            'parent':'Web Service',
                                'widgetType':Tkinter.Label,
                                'wcfg':{'text':'Error importing APBS Web Services.',
                                         'bg':'Red'},
                                })
                ifd.append({'name':'WS_install',
                            'parent':'Web Service',
                                'widgetType':Tkinter.Label,
                                'wcfg':{'text':'Please make sure that ZSI and PyZML packages are properly installed.'},
                                })                               
                ifd.append({'name':'WS_http',
                            'parent':'Web Service',
                                'widgetType':Tkinter.Label,
                                'wcfg':{'text':'http://nbcr.sdsc.edu/services/apbs/apbs-py.html',
                                         'fg':'Blue','cursor':'hand1'},
                                })
        self.ifd = ifd
        return ifd

    def SaltUpdate(self):
        "Toggles ParallelGroup widget"
        self.cmdForms['default'].descr.entryByName['SaltGroup']['widget'].\
                                                                        toggle()

    def changeMenuState(self, state):
        "Updates the state of DisplayIsocontours, MapPotential2MSMS and SisplayOrthoSlice manues."
        #change_Menu_state(self.vf.APBSDisplayIsocontours, state)
        if self.vf.hasGui:
            if hasattr(self.vf, 'APBSMapPotential2MSMS'):
                change_Menu_state(self.vf.APBSMapPotential2MSMS, state)
        #change_Menu_state(self.vf.APBSDisplayOrthoSlice, state)
    
    
    def ParallelParamUpdate(self):
        "Toggles ParallelGroup widget"
        self.cmdForms['default'].descr.entryByName['ParallelGroup']['widget'].\
                                                                        toggle()
    def WS_http(self, event):
        "Opens webbrowser at http://nbcr.sdsc.edu/services/apbs/apbs-py.html"
        import webbrowser
        webbrowser.open('http://nbcr.sdsc.edu/services/apbs/apbs-py.html')
    
    def toggle_usrpass(self, event):
        "Toggles User Name and Parssword entry and label"
        descr = self.cmdForms['default'].descr
        address = descr.entryByName['web service address']['widget'].get()
        address = address.strip()
        if address.find('https://') != 0:
            descr.entryByName['UserName_Label']['widget'].grid_forget()
            descr.entryByName['UserName_Entry']['widget'].grid_forget()
            descr.entryByName['Password_Label']['widget'].grid_forget()
            descr.entryByName['Password_Entry']['widget'].grid_forget()
            descr.entryByName['Remember_Label']['widget'].grid_forget()
            descr.entryByName['Remember_Checkbutton']['widget'].grid_forget()
        else:
            apply(descr.entryByName['UserName_Label']['widget'].grid, () , 
                                 descr.entryByName['UserName_Label']['gridcfg'])
            apply(descr.entryByName['UserName_Entry']['widget'].grid, () , 
                                 descr.entryByName['UserName_Entry']['gridcfg'])
            apply(descr.entryByName['Password_Label']['widget'].grid, () , 
                                 descr.entryByName['Password_Label']['gridcfg'])
            apply(descr.entryByName['Password_Entry']['widget'].grid, () , 
                                 descr.entryByName['Password_Entry']['gridcfg'])
            apply(descr.entryByName['Remember_Label']['widget'].grid, () , 
                                 descr.entryByName['Remember_Label']['gridcfg'])
            apply(descr.entryByName['Remember_Checkbutton']['widget'].grid, () , 
                           descr.entryByName['Remember_Checkbutton']['gridcfg'])

cascadeName = "Electrostatics"
APBSSetupGUI = CommandGUI()
APBSSetupGUI.addMenuCommand('menuRoot','Compute','Setup', 
                            cascadeName=cascadeName, separatorAbove=1) 

class APBSRun(MVCommand):
    """APBSRun runs Adaptive Poisson-Boltzmann Solver (APBS)\n
    \nPackage : Pmv
    \nModule  : APBSCommands
    \nClass   : APBSRun
    \nCommand name : APBSRun
    \nSynopsis:\n
    None <--- APBSRun(molName, APBSParamName = "Default", **kw)
    \nOptional Arguments:\n
        molecule1 - name of the molecule1
        molecule2 - name of the molecule2
        complex - name of the complex
        APBSParamName - Name of the key in mol.APBSParams dictionary
    """
    def onAddCmdToViewer(self):
        """Called when APBSRun is loaded"""
        if self.vf.hasGui:
            change_Menu_state(self, 'disabled')

    def onAddObjectToViewer(self, object):
        """Called when object is added to viewer"""
        if self.vf.hasGui:
            change_Menu_state(self, 'normal')
    
    def onRemoveObjectFromViewer(self, object):
        """Called when object is removed from viewer"""
        if self.vf.hasGui:
            if len(self.vf.Mols) == 0:
                change_Menu_state(self, 'disabled')
            
    def guiCallback(self):
        """GUI callback"""   
        if self.vf.APBSSetup.params.projectFolder == 'apbs-project':
            self.doit()
        else:
            self.doit(self.vf.APBSSetup.params)
        
    def __call__(self,  molecule1=None, molecule2=None, _complex=None,
                  APBSParamName='Default', blocking=False, **kw):
        """None <--- APBSRun(nodes, **kw)\n
            \nOptional Arguments :\n
              molecule1 - molecule1 as MolKit object or a string
              molecule2 - name of the molecule2
              complex - name of the complex
              APBSParamName = Name of the key in mol.APBSParams dictionary
        """             
        if not molecule1 and len(self.vf.Mols) == 1:
            molecule1 = self.vf.Mols[0].name
        if not molecule1:
            tkMessageBox.showinfo("No Molecule Selected", "Please use Compute -> Electrostatics ->  Setup and select a molecule.")
            return 'ERROR'            
        mol1 = self.vf.expandNodes(molecule1)
        assert isinstance(mol1, MoleculeSet)
        assert len(mol1) == 1
        if not mol1: return 'ERROR'
        molecule1 = mol1[0].name
        
        if molecule2:
            mol2 = self.vf.expandNodes(molecule2)
            assert isinstance(mol2, MoleculeSet)
            assert len(mol2) == 1
            if not mol2: return 'ERROR'
            molecule2 = mol2[0].name

#        elif molecule1 == None:
#            val = self.vf.APBSSetup.showForm('moleculeSelect', modal=1, blocking=1)
#            if not val:
#                return
#            else:
#                if len(val['moleculeListSelect'])==0: return
#                molecule1 = val['moleculeListSelect'][0]
#            self.vf.APBSSetup.refreshAll()             
        
        params = self.vf.APBSSetup.params
        if molecule1:
            params.projectFolder=os.path.join(os.getcwd(),
                                                   "apbs-"+molecule1)                                            
            params.molecule1Path = \
                                 self.vf.APBSSetup.moleculeListSelect(molecule1)
            self.vf.APBSSetup.mol1Name = molecule1
            if not params.molecule1Path:
                return
            if molecule2:
                if not _complex:
                    import warnings
                    warnings.warn("Complex is missing!")
                    return
                params.projectFolder += "_"+molecule2+"_"+_complex
                params.molecule2Path = \
                                 self.vf.APBSSetup.moleculeListSelect(molecule2)  
                self.vf.APBSSetup.mol2Name = molecule2
                params.complexPath = \
                                 self.vf.APBSSetup.moleculeListSelect(_complex)  
                self.vf.APBSSetup.complexName = _complex
            if not os.path.exists(params.projectFolder):
                try:
                    os.mkdir(params.projectFolder)
                except:
                    from user import home
                    tmp = os.path.split(params.projectFolder)
                    params.projectFolder = home + os.sep + tmp[-1]
                    if not os.path.exists(params.projectFolder):
                        os.mkdir(params.projectFolder)
            try:
                open(params.projectFolder+os.sep+'io.mc','w')
            except:
                from user import home
                tmp = os.path.split(params.projectFolder)
                params.projectFolder = home + os.sep + tmp[-1]
                if not os.path.exists(params.projectFolder):
                    os.mkdir(params.projectFolder)
            if molecule2:    
                abs_path = os.path.join(params.projectFolder,
                                                               molecule2+".pqr")            
                if not os.path.exists(abs_path) or \
                                          self.vf.APBSPreferences.overwrite_pqr:    
                    mol = self.vf.getMolFromName(molecule2)
                    self.vf.APBSSetup.mol2Name = molecule2
                    if hasattr(mol,'flag_copy_pqr') and mol.flag_copy_pqr:
                        self.copyFix(params.molecule2Path, abs_path)
                    else:
                        shutil.move(params.molecule2Path, abs_path)
                    mol.parser.filename = abs_path
                    params.molecule2Path = molecule2+".pqr"
                params.molecule2Path = \
                      os.path.split(params.molecule2Path)[-1]
                abs_path = os.path.join(params.projectFolder, _complex +".pqr")      
                mol = self.vf.getMolFromName(_complex)      
                self.vf.APBSSetup.complexName = _complex
                if not os.path.exists(abs_path) or \
                                          self.vf.APBSPreferences.overwrite_pqr:    
                    if hasattr(mol,'flag_copy_pqr') and mol.flag_copy_pqr:
                        self.copyFix(params.complexPath, abs_path)     
                    else:
                        shutil.move(params.complexPath, abs_path)     
                    mol.parser.filename = abs_path
                    params.complexPath = _complex +".pqr"
                params.complexPath = os.path.split(params.complexPath)[-1]         
            abs_path = os.path.join(params.projectFolder, molecule1+".pqr")            
            if not os.path.exists(abs_path) or \
                                          self.vf.APBSPreferences.overwrite_pqr:    
                mol = self.vf.getMolFromName(molecule1.replace('-','_'))
                self.vf.APBSSetup.mol1Name = mol.name
                if hasattr(mol,'flag_copy_pqr') and mol.flag_copy_pqr:
                    self.copyFix(params.molecule1Path,abs_path) 
                else:
                    shutil.move(params.molecule1Path,abs_path) 
                mol.parser.filename = abs_path
                self.vf.APBSPreferences.overwrite_pqr = False
                params.molecule1Path = molecule1+".pqr"
            params.molecule1Path = os.path.split(params.molecule1Path)[-1]
            if self.vf.APBSSetup.cmdForms.has_key('default'):
                self.vf.APBSSetup.cmdForms['default'].descr.entryByName\
                                                       ['molecule1']['widget'].\
                                setentry(params.molecule1Path)
            if APBSParamName != 'Default':
                mol = self.vf.getMolFromName(molecule1.replace('-','_'))
                self.vf.APBSSetup.mol1Name = mol.name
                params = mol.APBSParams[APBSParamName]
            dest_path = os.path.join(params.projectFolder, 
                                                  APBSParamName+'_potential.dx')
            
            pickle_name = os.path.join(params.projectFolder,
                                                       APBSParamName+".apbs.pf")
            if os.path.exists(pickle_name):
                fp = open(pickle_name, 'r')
                tmp_params = pickle.load(fp)
                fp.close()
                flag_run = True # this flags if apbs with the same paramters 
                                 # has been already run
                for key in tmp_params.__dict__:
                    if key != 'ions':
                        if tmp_params.__dict__[key] !=  \
                                         params.__dict__[key]:
                            flag_run = False
                            break
                    else:
                        if len(tmp_params.ions) != \
                                             len(params.ions):
                                                 flag_run = False
                                                 break
                        for i in range(len(tmp_params.ions)):
                            if tmp_params.ions[i].charge != \
                                        params.ions[i].charge:
                                    flag_run = False
                                    break                                
                            if tmp_params.ions[i].concentration != \
                                 params.ions[i].concentration:
                                    flag_run = False
                                    break
                            if tmp_params.ions[i].radius != \
                                        params.ions[i].radius:
                                    flag_run = False
                                    break             
                if flag_run == True:
                    answer = False
                    if self.vf.APBSSetup.cmdForms.has_key('default') and \
                      self.vf.APBSSetup.cmdForms['default'].f.winfo_toplevel().\
                                                         wm_state() == 'normal':
                           answer = tkMessageBox.askyesno("WARNING",\
                          "APBS with the same parameters has been already run."+
           "\n\nWould you like to continue?",
                              parent=self.vf.APBSSetup.cmdForms['default'].root)
                    else:
                        answer = tkMessageBox.askyesno("WARNING",\
                          "APBS with the same parameters has been already run."+
           "\n\nWould you like to continue?")
                    if answer != True:
                        #self.vf.APBSSetup.loadProfile(pickle_name)
                        return
            self.vf.APBSSetup.refreshCalculationPage()     
            if not self.vf.APBSSetup.flag_grid_changed:
                self.vf.APBSSetup.autocenterCoarseGrid()
                self.vf.APBSSetup.autosizeCoarseGrid()
                self.vf.APBSSetup.autocenterFineGrid()
                self.vf.APBSSetup.autosizeFineGrid()
                self.vf.APBSSetup.refreshGridPage()            
            if self.doitWrapper(molecule1, molecule2, _complex, 
                              APBSParamName=APBSParamName,
                                blocking=blocking) == 'error':
                    self.vf.APBSSetup.showForm('default', \
                    modal=0, blocking=1,initFunc=self.vf.APBSSetup.refreshAll)
            return

            
    def copyFix(self, fileSource, fileDest):
        """Copies a file from fileSource to fileDest and fixes end-of-lines"""
        newlines = []
        for line in open(fileSource, 'rb').readlines():
            if line[-2:] == '\r\n':
                line = line[:-2] + '\n'
            newlines.append(line)
        open(fileDest, 'w').writelines(newlines)
        
    def doit(self, molecule1=None, molecule2=None, _complex=None,
             APBSParamName = 'Default', blocking=False):
        """doit function"""
        return self.vf.APBSSetup.apbsOutput(molecule1, molecule2, _complex,
                                            blocking=blocking)

APBSRun_GUI = CommandGUI()
APBSRun_GUI.addMenuCommand('menuRoot', 'Compute', 
                      'Compute Potential Using APBS', cascadeName=cascadeName)

class APBSMap_Potential_to_MSMS(MVCommand):
    """APBSMapPotential2MSMS maps APBS Potential into MSMS Surface\n
    \nPackage : Pmv
    \nModule  : APBSCommands
    \nClass   : APBSMap_Potential_to_MSMS
    \nCommand name : APBSMapPotential2MSMS
    \nSynopsis:\n
    None <---  APBSMapPotential2MSMS(mol = mol, potential = potential)
    \nRequired Arguments:\n  
            mol = name of the molecule\n
            potential = string representing where potential.dx is located\n"""
    
    def onAddCmdToViewer(self):
        """Called when added to viewer"""
        if self.vf.hasGui:
            change_Menu_state(self, 'disabled')
        self.custom_quality = 5.0

    def onAddObjectToViewer(self, object):
        """Called when object is added to viewer"""
        if self.vf.hasGui:
            change_Menu_state(self, 'normal')

    def onRemoveObjectFromViewer(self, object):
        """Called when object is removed from viewer"""
        if self.vf.hasGui:
            if len(self.vf.Mols) == 0:
                change_Menu_state(self, 'disabled')  
            cmap = self.vf.GUI.VIEWER.FindObjectByName('root|cmap')
            if cmap:
                cmap.Set(visible=False)
            self.vf.GUI.VIEWER.Redraw()

    def doit(self, mol = None, potential = None):
        """doit function for APBSMap_Potential_to_MSMS"""
        self.vf.GUI.ROOT.config(cursor='watch')
        self.vf.GUI.VIEWER.master.config(cursor='watch')    
        self.vf.GUI.MESSAGE_BOX.tx.component('text').config(cursor='watch')
        from MolKit.molecule import Molecule
        if isinstance(mol, Molecule):
            mol = self.vf.getMolFromName(mol.name.replace('-','_'))
        elif type(mol) == str:
            mol = self.vf.getMolFromName(mol.replace('-','_'))
        else:
            import warnings
            warnings.warn("APBSMap_Potential_to_MSMS doit(): mol should either be a molecule object or molecule name.")
            return
        self.vf.assignAtomsRadii(mol, overwrite=True,log=False)
        mol.allAtoms._radii = {}
        for atom in mol.allAtoms:
            if hasattr(atom,'pqrRadius'):
                atom._radii['pqrRadius'] = atom.pqrRadius
            if hasattr(atom,'vdwRadius'):
                atom._radii['vdwRadius'] = atom.vdwRadius
            if hasattr(atom,'covalentRadius'):
                atom._radii['covalentRadius'] = atom.covalentRadius
        if self.quality == 'low':
            self.vf.computeMSMS(mol, density = 1.0, log = False)
        elif self.quality == 'medium':
            self.vf.computeMSMS(mol, density = 3.0, log = False)
        elif self.quality == 'high':
            self.vf.computeMSMS(mol, density = 6.0, log = False)
        else:
            self.vf.computeMSMS(mol, density = self.custom_quality, log = False)
        if not self.vf.commands.has_key('vision'):
            self.vf.browseCommands('visionCommands',log=False) 
        g = mol.geomContainer.geoms['MSMS-MOL']
        g.Set(inheritSharpColorBoundaries = False, sharpColorBoundaries =False)
        self.vf.GUI.ROOT.config(cursor='watch')
        self.vf.GUI.VIEWER.master.config(cursor='watch')    
        self.vf.GUI.MESSAGE_BOX.tx.component('text').config(cursor='watch')          

        if self.vf.vision.ed is None:
            self.vf.vision(log=False)    
            self.vf.vision(log=False)
        self.APBS_MSMS_Net = self.vf.vision.ed.getNetworkByName("APBSPot2MSMS")
        if not self.APBS_MSMS_Net:
            from mglutil.util.packageFilePath import findFilePath
            Network_Path = findFilePath("VisionInterface/APBSPot2MSMS_net.py",
                                                                          'Pmv')
            self.vf.vision.ed.loadNetwork(Network_Path, takefocus=False)
            self.APBS_MSMS_Net = self.vf.vision.ed.getNetworkByName\
                                                             ("APBSPot2MSMS")[0]
        else:
            self.APBS_MSMS_Net = self.APBS_MSMS_Net[0]

        mol_node = self.APBS_MSMS_Net.getNodeByName('Choose Molecule')[0]
        mol_node.run(force=1)
        mol_node.inputPorts[1].widget.set(mol.name)
        self.vf.GUI.ROOT.config(cursor='watch')
        self.vf.GUI.VIEWER.master.config(cursor='watch')    
        self.vf.GUI.MESSAGE_BOX.tx.component('text').config(cursor='watch')          
        file_DX = self.APBS_MSMS_Net.getNodeByName('Pmv Grids')[0]
        potentialName = os.path.basename(potential)
        if not self.vf.grids3D.has_key(potentialName):
            self.vf.Grid3DReadAny(potential, show=False, normalize=False)
            self.vf.grids3D[potentialName].geomContainer['Box'].Set(visible=0)
        file_DX.inputPorts[0].widget.set(potentialName)
        file_DX.run(force=1)

        macro = self.APBS_MSMS_Net.getNodeByName('Map Pot On Geom')[0]
        offset =  macro.macroNetwork.getNodeByName('Offset')[0]
        check = offset.getInputPortByName('dial')
        check.widget.set(self.distance)
        button = macro.macroNetwork.getNodeByName('Checkbutton')[0]
        check = button.getInputPortByName('button')
        check.widget.set(0)
        colormap = macro.macroNetwork.getNodeByName('Color Map')[0]
        colormap.run(force=1) # this forces Color node to run  
        self.APBS_MSMS_Net.run()
        colormap.outputPortByName['legend'].data.Set(unitsString='kT/e')

    def guiCallback(self):
        """GUI callback for APBSMap_Potential_to_MSMS"""
        if not self.vf.commands.has_key('computeMSMS'):
            self.vf.browseCommands("msmsCommands",log=False)       
        file_name,ext = os.path.splitext(self.vf.APBSSetup.params.molecule1Path)
        mol_name = os.path.split(file_name)[-1]
        mol_list = ()
        for name in self.vf.Mols.name:
            mol_list += (name,)
        ifd = InputFormDescr(title = 'Map Potential to Surface Parameters')
        if mol_name in mol_list:
            default_mol =  mol_name
        else:
            default_mol = mol_list[0]
        from MolKit.molecule import Molecule
        if len(self.vf.selection):            
            selection = self.vf.selection[0]
            if isinstance(selection, Molecule):
                default_mol = selection.name
        self.default_mol = default_mol
        ifd.append({'name':'mol_list',
                'widgetType':Pmw.ComboBox,
                    'tooltip':
"""Click on the fliparrow to view 
the list of available molecules"""    ,
                'defaultValue':default_mol,
                'wcfg':{'labelpos':'new','label_text':'Please select molecule',
                        'scrolledlist_items':mol_list, 'history':0,'entry_width':15,
                        'fliparrow':1, 'dropdown':1, 'listheight':80},
                'gridcfg':{'sticky':'we', 'row':1, 'column':0}
                })                           
        ifd.append({'name':'quality',
                    'widgetType':Pmw.RadioSelect,
                    'tooltip':
""" low, medium and high correspond to molecular
surface density of 1, 3, and 6 points respectively"""    ,
                    'listtext':['low', 'medium', 'high', 'custom'],
                    'defaultValue':'medium',
                    'wcfg':{'orient':'vertical','labelpos':'w',
                            'label_text':'Surface \nquality ',
                            'command':self.select_custom,
                            'hull_relief':'ridge', 'hull_borderwidth':2,
                            'padx':0,
                             'buttontype':'radiobutton'},
                     'gridcfg':{'sticky': 'ewns', 'row':2, 'column':0, }})
        ifd.append({'name':'distance',
                    'widgetType':ThumbWheel,
                    'tooltip':
"""offset along the surface normal at which the potential will be looked up""",
                    'gridcfg':{'sticky':'we'},
                    'wcfg':{'value':1.0,'oneTurn':10, 
                        'type':'float',
                        'increment':0.1,
                        'precision':1,
                        'continuous':False,
                        'wheelPad':3,'width':140,'height':20,
                         'labCfg':{'text':'Distance from surface',
                                   'side':'top'},
                       'gridcfg':{'sticky': 'we', 'row':3, 'column':0, }
                        }
                    })                           
        val = self.vf.getUserInput(ifd,initFunc = self.initFunc)
        if not val: return
        self.quality = val['quality']
        self.distance = val['distance']
        molecule_selected = val['mol_list'][0]
        if molecule_selected == mol_name:
            potential_dx = os.path.join(self.vf.APBSSetup.params.projectFolder, 
                                                     mol_name + '.potential.dx')
            self.doitWrapper(mol = mol_name, potential =  potential_dx)
        else:
            potential_dx = os.path.join(os.getcwd(), "apbs-"+ molecule_selected)
            potential_dx = os.path.join(potential_dx, molecule_selected + \
                                         '.potential.dx')
            if not os.path.exists(potential_dx):
                self.vf.APBSRun(molecule1 = molecule_selected)
                if not hasattr(self.vf.APBSSetup, 'cmd'): return
                while self.vf.APBSSetup.cmd.ok.configure()['state'][-1] != \
                                                                       'normal':
                     self.vf.GUI.ROOT.update()
            self.doitWrapper(mol=molecule_selected, potential=potential_dx)
            self.vf.APBSSetup.potential = os.path.basename(potential_dx)
            if self.vf.hasGui:
                change_Menu_state(self.vf.APBSDisplayIsocontours, 'normal')            
                change_Menu_state(self.vf.APBSDisplayOrthoSlice, 'normal')
                if hasattr(self.vf,'APBSVolumeRender'):
                    change_Menu_state(self.vf.APBSVolumeRender, 'normal')
        

    def __call__(self, mol=None, potential=None, quality='medium', **kw):
        """Maps potential.dx into MSMS using\n
        VisionInterface/APBSPot2MSMS_net.py\n
        Required Arguments:\n  
            mol = name of the molecule\n
            potential = location of the potential.dx file\n"""

        molNode = self.vf.expandNodes(mol)
        assert isinstance(molNode, MoleculeSet)
        assert len(molNode) == 1
        if not molNode: return 'ERROR'
        mol = molNode[0].name
        kw['mol'] = mol
        if potential is None:
            potential_dx = os.path.join(os.getcwd(), "apbs-"+ mol)
            potential_dx = os.path.join(potential_dx, mol + '.potential.dx')
            kw['potential'] = potential_dx
            kw['quality'] = quality
        else:
            kw['potential'] = potential

        if kw.has_key('mol') and kw.has_key('potential'):
            if kw.has_key('quality'):
                self.quality = kw['quality']
            else:
                self.quality = 'medium' #default
            if kw.has_key('distance'):
                self.distance = kw['ditance']
            else:
                self.distance = 1.0 #default
            self.doitWrapper(mol=kw['mol'],potential=kw['potential'])
        else:
            print >>sys.stderr, "mol and/or potential is missing"
            return


    def select_custom(self, evt):
        if evt == 'custom':
            ifd = InputFormDescr(title='Select Surface Density')
            ifd.append({'name':'density',
                    'widgetType':ThumbWheel,
                    'tooltip':
                       """Right click on the widget to type a value manually""",
                    'gridcfg':{'sticky':'we'},
                    'wcfg':{'value':self.custom_quality,'oneTurn':2, 
                        'type':'float',
                        'increment':0.1,
                        'precision':1,
                        'continuous':False,
                        'wheelPad':2,'width':145,'height':18,
                         'labCfg':{'text':'Density         '},
                        }
                    })
            val = self.vf.getUserInput(ifd,)
            if val:
                self.custom_quality = val['density']
                
    def initFunc(self, ifd):
        """This function initializes GUI for APBSMap_Potential_to_MSMS"""
        ifd.descr.entryByName['mol_list']['widget']._entryWidget.\
                                       config(state='readonly')
        
    def setupUndoBefore(self, mol = None, potential = None ):
        # The undo of this display command depends on which displayMSMS cmd
        # was used previously and results in displaying what faces were displayed previously
        undoCmd = """self.displayMSMS(self.getMolFromName('%s'), surfName=['MSMS-MOL'], negate=1, redraw =1, topCommand=0)
cmap = self.GUI.VIEWER.FindObjectByName('root|cmap')
if cmap:
    cmap.Set(visible=False)"""%(mol)
        self.vf.undo.addEntry((undoCmd), ('Map Potential to Molecular Surface'))
        
APBSMap_Potential_to_MSMS_GUI = CommandGUI()
APBSMap_Potential_to_MSMS_GUI.addMenuCommand('menuRoot','Compute', 
'Map Potential to Surface', cascadeName=cascadeName) 

class APBSDisplay_Isocontours(MVCommand):
    """APBSDisplayIsocontours displays APBS Potential Isocontours\n
    \nPackage : Pmv
    \nModule  : APBSCommands
    \nClass   : APBS_Display_Isocontours
    \nCommand name : APBSDisplayIsocontours
    \nSynopsis:\n
    None <---  APBSDisplayIsocontours(potential = potential)
    \nRequired Arguments:\n  
            potential = string representing where potential.dx is located\n"""
    
    def onAddCmdToViewer(self):
        """Called when added to viewer"""
        if self.vf.hasGui:
            change_Menu_state(self, 'disabled')
                 
#    def onAddObjectToViewer(self, object):
#        """Called when object is added to viewer"""
#        change_Menu_state(self, 'normal')

    def onRemoveObjectFromViewer(self, object):
        """Called when object is removed from viewer"""
        if self.vf.hasGui:
            if len(self.vf.Mols) == 0:
                change_Menu_state(self, 'disabled')
 
    def dismiss(self, event = None):
        """Withdraws GUI form"""
        self.cancel = True
        self.ifd.entryByName['-visible']['wcfg']['variable'].set(False)
        self.ifd.entryByName['+visible']['wcfg']['variable'].set(False)
        self.Left_Visible()
        self.Right_Visible()
        self.form.withdraw()
        
    def doit(self, potential = None):
        """doit function"""       
        self.vf.GUI.ROOT.config(cursor='watch')
        self.vf.GUI.VIEWER.master.config(cursor='watch')    
        self.vf.GUI.MESSAGE_BOX.tx.component('text').config(cursor='watch')
        if not self.vf.commands.has_key('vision'):
            self.vf.browseCommands('visionCommands',log=False)        
        if self.vf.vision.ed is None:
            self.vf.vision(log=False)    
            self.vf.vision(log=False)
        self.APBS_Iso_Net = self.vf.vision.ed.getNetworkByName("APBSIsoContour")
        if not self.APBS_Iso_Net:
            from mglutil.util.packageFilePath import findFilePath
            Network_Path = findFilePath("VisionInterface/APBSIsoContour_net.py",
                                                                          'Pmv')
            self.vf.vision.ed.loadNetwork(Network_Path, takefocus=False)
            self.APBS_Iso_Net = self.vf.vision.ed.\
                                           getNetworkByName("APBSIsoContour")[0]
        else:
            self.APBS_Iso_Net = self.APBS_Iso_Net[0]
        file_DX = self.APBS_Iso_Net.getNodeByName('Pmv Grids')[0]
        potentialName = os.path.basename(potential)
        if not self.vf.grids3D.has_key(potentialName):
            grid = self.vf.Grid3DReadAny(potential, show=False, normalize=False)
            if grid:
                self.vf.grids3D[potentialName].geomContainer['Box'].Set(visible=0)
            else:
                return
        file_DX.inputPorts[0].widget.set(potentialName)
        self.APBS_Iso_Net.run()       
        
    def guiCallback(self):
        """GUI callback"""                
        file_name,ext = os.path.splitext(self.vf.APBSSetup.params.molecule1Path)
        mol_name = os.path.split(file_name)[-1]
        self.mol_list = ()
        for name in self.vf.Mols.name:
            potential_dx = os.path.join(os.getcwd(), "apbs-" + name)
            potential_dx = os.path.join(potential_dx, name + '.potential.dx')
            if os.path.exists(potential_dx):
                self.mol_list += (name,)
        potential_dx = os.path.join(self.vf.APBSSetup.params.projectFolder, 
                                                 mol_name + '.potential.dx')                
        if os.path.exists(potential_dx):
            self.mol_list += (mol_name,)

        if len(self.mol_list) == 0:
            self.vf.warningMsg("Please run APBS to generate potential.dx", "ERROR potential.dx is missing")
            return
        if mol_name in self.mol_list:
            default_mol =  mol_name
        else:
            default_mol = self.mol_list[0]
        from MolKit.molecule import Molecule
        if len(self.vf.selection):            
            selection = self.vf.selection[0]
            if isinstance(selection, Molecule):
                default_mol = selection.name
        self.combo_default = default_mol
        potential_dx = os.path.join(os.getcwd(), "apbs-" + default_mol)
        potential_dx = os.path.join(potential_dx, default_mol + '.potential.dx')
        self.doitWrapper(potential = potential_dx)
        self.Isocontour_L = self.APBS_Iso_Net.getNodeByName('Left_Isocontour')[0]       
        self.Isocontour_R = self.APBS_Iso_Net.getNodeByName('Right_Isocontour')[0]
        self.cancel = False
        if not hasattr(self, 'ifd'):
            self.buildForm()
        else:
            self.form.deiconify()
            
        self.ifd.entryByName['mol_list']['widget'].setlist(self.mol_list)
        self.ifd.entryByName['+Silder']['widget'].canvas.config(bg="Blue")
        self.ifd.entryByName['-Silder']['widget'].canvas.config(bg="Red")
        self.ifd.entryByName['-visible']['wcfg']['variable'].set(True)
        self.ifd.entryByName['+visible']['wcfg']['variable'].set(True)
        self.ifd.entryByName['mol_list']['widget'].setentry(self.mol_list[0])
        self.ifd.entryByName['mol_list']['widget']._entryWidget.\
                                             config(state='readonly')
        self.APBS_Iso_Net.run()
        self.Left_Visible()
        self.Right_Visible()
        self.vf.GUI.ROOT.config(cursor='')
        self.vf.GUI.VIEWER.master.config(cursor='')    
        self.vf.GUI.MESSAGE_BOX.tx.component('text').config(cursor='xterm')
        
    def run(self):
        """Animates isocontours"""
        inv_d = 1./(self.maxi - self.mini)
        data = Numeric.arange(inv_d,inv_d*500,inv_d*15).tolist()
        data += Numeric.arange(inv_d*500,inv_d*5000,inv_d*150).tolist()
        for values in data:
            if self.cancel:
                return
            self.ifd.entryByName['+Silder']['widget'].set(values)
            #self.Isocontour_L.getInputPortByName('isovalue').widget.set(values)
            self.ifd.entryByName['-Silder']['widget'].set(-values)
            #self.Isocontour_R.getInputPortByName('isovalue').widget.set(-values)
            self.vf.GUI.VIEWER.update()    
            
    def __call__(self, **kw):
        """Displays APBS Potential Isocontours using\n
        VisionInterface/APBSIsoContour_net.py\n
        Required Arguments:\n  
            potential = location of the potential.dx file\n"""
        if kw.has_key('potential'):
            self.doitWrapper(potential =  kw['potential'])
        else:
            print >>sys.stderr, "potential is missing"
            return

    def buildForm(self):
        """Builds 'default' GUI form'"""
        VolumeStats = self.APBS_Iso_Net.getNodeByName('VolumeStats')[0]
        self.maxi = VolumeStats.getOutputPortByName('maxi').data
        self.mini = VolumeStats.getOutputPortByName('mini').data
        self.Update(1);self.Update(-1)
        self.ifd = ifd = InputFormDescr(title="Isocontours Control Panel")
        ifd.append({'name':'mol_list',
                'widgetType':Pmw.ComboBox,
                    'tooltip':
"""Click on the fliparrow to view 
the list of available molecules""" ,
                'defaultValue': self.combo_default,
                'wcfg':{'labelpos':'e','label_text':'Select molecule',
                        'scrolledlist_items':self.mol_list, 'history':0,
                        'selectioncommand':self.Combo_Selection,
                        'entry_width':5,
                        'fliparrow':1, 'dropdown':1, 'listheight':80},
                'gridcfg':{'sticky':'we', 'row':0, 'column':0,'columnspan':2}
                })
        ifd.append({'name':'+Silder',
                    'widgetType':ThumbWheel,
                    'tooltip':
"""Right click on the widget to type the isovalue manually""",
                    'wcfg':{'value':1.0,'oneTurn':10, 
                        'type':'float',
                        'increment':0.1,
                        'min':0,
                        'precision':2,
                        'wheelPad':2,'width':120,'height':19,
                        'callback':self.Update,
                        }
                    })                           
        ifd.append({'name':'-Silder',
                    'widgetType':ThumbWheel,                    
                    'tooltip':
"""Right click on the widget to type the isovalue manually""",
                    'wcfg':{'value':-1.0,'oneTurn':10, 
                        'type':'float',
                        'increment':0.1,
                        'precision':2,
                        'max':-0.000000001,
                        'wheelPad':2,'width':120,'height':19,
                        'callback':self.Update,
                        },
                    })                           
        ifd.append({'widgetType':Tkinter.Checkbutton,
                    'tooltip':"""(De)select this checkbutton to 
(un)display blue isocontour""",
                    'name':'+visible',
                    'defaultValue':1,
                    'wcfg':{'text':'Blue isocontour',
                    'command':self.Left_Visible,
                    'bg':'Blue','fg':'White',
                    'variable':Tkinter.BooleanVar()},
                    'gridcfg':{'sticky':'e','row':1, 'column':1}
                    })
        ifd.append({'widgetType':Tkinter.Checkbutton,
                    'tooltip':"""(De)select this checkbutton to 
(un)display red isocontour""",
                    'name':'-visible',
                    'defaultValue':1,
                    'wcfg':{'text':'Red isocontour',
                    'command':self.Right_Visible,
                    'bg':'Red','fg':'White',
                    'variable':Tkinter.BooleanVar()},
                    'gridcfg':{'sticky':'e','row':2, 'column':1}
                    })
        ifd.append({'name':'dismiss',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Cancel',
                            'command':self.dismiss},
                    'gridcfg':{'sticky':'wens','row':3, 'column':0}
                    })
        ifd.append({'name':'run',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Animate',
                            'command':self.run},
                    'gridcfg':{'sticky':'wens','row':3, 'column':1}
                    })
        self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)
        return ifd
    
    def Combo_Selection(self, mol_name):
        """
        This command is triggered as selectioncommand for ComboBox mol_list
        """
        potential_dx = os.path.join(os.getcwd(), "apbs-" + mol_name)
        potential_dx = os.path.join(potential_dx, mol_name + '.potential.dx')
        self.doitWrapper(potential = potential_dx)

    def Left_Visible(self):
        """Sets "+polygons" and "left_label" objects visible state"""
        left_object = self.vf.GUI.VIEWER.GUI.objectByName('+polygons')
        left_label = self.vf.GUI.VIEWER.GUI.objectByName('LeftLabel')
        visible = self.ifd.entryByName['+visible']['wcfg']['variable'].get()
        left_object.Set(visible = visible)
        left_label.Set(visible = visible)
        self.vf.GUI.VIEWER.Redraw()
        
    def Right_Visible(self):
        """Sets "-polygons" and "right_label" objects visible states"""
        right_object = self.vf.GUI.VIEWER.GUI.objectByName('-polygons')
        right_label = self.vf.GUI.VIEWER.GUI.objectByName('RightLabel')
        visible = self.ifd.entryByName['-visible']['wcfg']['variable'].get()
        right_object.Set(visible = visible)
        right_label.Set(visible = visible)
        self.vf.GUI.VIEWER.Redraw()

    def Update(self,val):
        """Updates Isocontour_L or Isocontour_R"""
        if val > 0:
            self.Isocontour_R.getInputPortByName('isovalue').widget.set(val)
        else:
            self.Isocontour_L.getInputPortByName('isovalue').widget.set(val)
                
APBSDisplay_Isocontours_GUI = CommandGUI()
APBSDisplay_Isocontours_GUI.addMenuCommand('menuRoot', 'Compute', \
                              'Isocontour Potential', cascadeName=cascadeName) 

from DejaVu.colorTool import RedWhiteBlueARamp
class APBSDisplayOrthoSlice(MVCommand):
    """APBSDisplayOrthoslice displays APBS Potential Orthoslice\n
    \nPackage : Pmv
    \nModule  : APBSCommands
    \nClass   : APBSDisplayOrthoslice
    \nCommand name : APBSDisplayOrthoslice
    \nSynopsis:\n
    None <---  APBSDisplayOrthoslice()
"""
    
    def onAddCmdToViewer(self):
        """Called when added to viewer"""
        if self.vf.hasGui:
            change_Menu_state(self, 'disabled')
                 
#    def onAddObjectToViewer(self, object):
#        """Called when object is added to viewer"""
#        change_Menu_state(self, 'normal')

    def onRemoveObjectFromViewer(self, object):
        """Called when object is removed from viewer"""
        if self.vf.hasGui:
            if len(self.vf.Mols) == 0:
                change_Menu_state(self, 'disabled')
        potential = object.name +'.potential.dx'
        try:
            self.vf.Grid3DCommands.select(potential)
            self.vf.Grid3DAddRemove.remove()
        except:
            pass #can't remove from 3D Grid Rendering widget
         
    def doit(self):
        """doit function"""       
        self.vf.Grid3DCommands.show()
        self.vf.Grid3DCommands.select(self.vf.APBSSetup.potential)
        self.vf.Grid3DCommands.Checkbuttons['OrthoSlice'].invoke()
        grid = self.vf.grids3D[self.vf.APBSSetup.potential]
        self.vf.Grid3DOrthoSlice.select()
        self.vf.Grid3DOrthoSlice.X_vis.set(True)
        self.vf.Grid3DOrthoSlice.Y_vis.set(True)
        self.vf.Grid3DOrthoSlice.Z_vis.set(True)
        self.vf.Grid3DOrthoSlice.createX()
        self.vf.Grid3DOrthoSlice.createY()
        self.vf.Grid3DOrthoSlice.createZ()
        self.vf.Grid3DOrthoSlice.ifd.entryByName['X_Slice']['widget'].set(grid.dimensions[0]/2)
        self.vf.Grid3DOrthoSlice.ifd.entryByName['Y_Slice']['widget'].set(grid.dimensions[1]/2)
        self.vf.Grid3DOrthoSlice.ifd.entryByName['Z_Slice']['widget'].set(grid.dimensions[2]/2)
        mini = - grid.std/10.
        maxi = grid.std/10.
        grid.geomContainer['OrthoSlice']['X'].colormap.configure(ramp=RedWhiteBlueARamp(), mini=mini, maxi=maxi)
        grid.geomContainer['OrthoSlice']['Y'].colormap.configure(ramp=RedWhiteBlueARamp(), mini=mini, maxi=maxi)
        grid.geomContainer['OrthoSlice']['Z'].colormap.configure(ramp=RedWhiteBlueARamp(), mini=mini, maxi=maxi)

        
    def guiCallback(self):
        """GUI callback"""                
        self.doitWrapper()
            
    def __call__(self, **kw):
        """Displays APBS Potential Isocontours using\n
        VisionInterface/APBSIsoContour_net.py\n
        Required Arguments:\n  
            potential = location of the potential.dx file\n"""
        self.doitWrapper()
    

               
APBSDisplayOrthoSlice_GUI = CommandGUI()
APBSDisplayOrthoSlice_GUI.addMenuCommand('menuRoot', 'Compute', \
                              'Display OrthoSlice', cascadeName=cascadeName) 

class APBSVolumeRender(MVCommand):
    """APBSVolumeRender \n
    \nPackage : Pmv
    \nModule  : APBSCommands
    \nClass   : APBSVolumeRender
    \nCommand name : APBSVolumeRender
    \nSynopsis:\n
    None <---  APBSAPBSVolumeRender()
"""

    def  checkDependencies(self, vf):
        if not vf.hasGui:
            return 'ERROR'
        from Volume.Renderers.UTVolumeLibrary import UTVolumeLibrary
        test = UTVolumeLibrary.VolumeRenderer()
        flagVolume = test.initRenderer()
        if not flagVolume:
            return 'ERROR'
     
    def onAddCmdToViewer(self):
        """Called when added to viewer"""
        if self.vf.hasGui:
            change_Menu_state(self, 'disabled')
                 
#    def onAddObjectToViewer(self, object):
#        """Called when object is added to viewer"""
#        change_Menu_state(self, 'normal')

    def onRemoveObjectFromViewer(self, object):
        """Called when object is removed from viewer"""
        if self.vf.hasGui:
            if len(self.vf.Mols) == 0:
                change_Menu_state(self, 'disabled')
         
    def doit(self):
        """doit function"""       
        grid = self.vf.grids3D[self.vf.APBSSetup.potential]
        mini = - grid.std/10.
        maxi =  grid.std/10.
        tmpMax = grid.maxi
        tmpMin = grid.mini
        grid.mini = mini
        grid.maxi = maxi        

        self.vf.Grid3DCommands.show()
        self.vf.Grid3DCommands.select(self.vf.APBSSetup.potential)
        self.vf.Grid3DCommands.Checkbuttons['VolRen'].invoke()
        self.vf.Grid3DVolRen.select()
        widget = self.vf.Grid3DVolRen.ifd.entryByName['VolRen']['widget']
        widget.colorGUI()
        ramp = RedWhiteBlueARamp()
        ramp[:,3] = Numeric.arange(0,0.25,1./(4*256.),'f')
        grid = self.vf.grids3D[self.vf.APBSSetup.potential]
        widget.ColorMapGUI.configure(ramp=ramp, mini=mini, maxi=maxi)
        widget.ColorMapGUI.apply_cb()
        grid.mini = tmpMin
        grid.maxi = tmpMax

        
    def guiCallback(self):
        """GUI callback"""                
        self.doitWrapper()
            
    def __call__(self, **kw):
        """Displays APBS Potential Isocontours using\n
        VisionInterface/APBSIsoContour_net.py\n
        Required Arguments:\n  
            potential = location of the potential.dx file\n"""
        self.doitWrapper()
    

               
APBSVolumeRender_GUI = CommandGUI()
APBSVolumeRender_GUI.addMenuCommand('menuRoot', 'Compute', \
                              'Volume Renderer', cascadeName=cascadeName) 

from tkFileDialog import *

class APBSLoad_Profile(MVCommand):
    """APBSLoadProfile loads APBS parameters\n
    \nPackage : Pmv
    \nModule  : APBSCommands
    \nClass   : APBSLoad_Profile
    \nCommand name : APBSLoadProfile
    \nSynopsis:\n
    None <---  APBSLoadProfile(filename = None)
    \nOptional Arguments:\n  
            filename = name of the file containing APBS parameters\n
     """
    def doit(self, filename = None):
        """doit function"""
        self.vf.APBSSetup.loadProfile(filename=filename)

    def guiCallback(self):
        """GUI callback"""
        filename=askopenfilename(filetypes=[('APBS Profile','*.apbs.pf')],\
                                                      title="Load APBS Profile")
        if filename:
            self.doitWrapper(filename=filename)

    def __call__(self, **kw):
        """None <--- APBSSave_Profile()\n
        Calls APBSSetup.loadProfile\n"""
        if kw.has_key('filename'):
            self.doitWrapper(filename=kw['filename'])
        else:
            if self.vf.APBSSetup.cmdForms.has_key('default') and \
                self.vf.APBSSetup.cmdForms['default'].f.winfo_toplevel().\
                                                         wm_state() == 'normal':
                    filename=askopenfilename(filetypes=\
                                                 [('APBS Profile','*.apbs.pf')],
                                                      title="Load APBS Profile",
                              parent=self.vf.APBSSetup.cmdForms['default'].root)
            else:
                filename = askopenfilename(filetypes = 
                    [('APBS Profile','*.apbs.pf')], title = "Load APBS Profile")
            if filename:
                self.doitWrapper(filename=filename)
        
APBSLoad_Profile_GUI = CommandGUI()
APBSLoad_Profile_GUI.addMenuCommand('menuRoot', 'Compute', 'Load Profile',
                                    cascadeName=cascadeName, separatorAbove=1)

class APBSSave_Profile(MVCommand):
    """APBSSaveProfile saves APBS parameters\n
    \nPackage : Pmv
    \nModule  : APBSCommands
    \nClass   : APBSSave_Profile
    \nCommand name : APBSSaveProfile
    \nSynopsis:\n
    None <---  APBSSaveProfile(filename = None)
    \nOptional Arguments:\n  
            filename = name of the file where APBS parameters are to be saved\n
     """
    def onAddCmdToViewer(self):
        """Called when added to viewer"""
        if self.vf.hasGui:
            change_Menu_state(self, 'disabled')
        
    def onRemoveObjectFromViewer(self, object):
        """Called when object is removed from viewer"""
        if self.vf.hasGui:
            if len(self.vf.Mols) == 0:
                change_Menu_state(self, 'disabled')

    def doit(self, Profilename=None):
        """doit function"""
        self.vf.APBSSetup.saveProfile(Profilename=Profilename, fileFlag=True, flagCommand=True)

    def guiCallback(self):
        """GUI callback"""
        filename=asksaveasfilename(filetypes=[('APBS Profile','*.apbs.pf')],
                                                   title="Save APBS Profile As")
        if filename:
            self.doitWrapper(Profilename=filename)
        
    def __call__(self, **kw):
        """None <--- APBSSave_Profile(filename = None)\n
        Calls APBSSetup.saveProfile\n"""
        if kw.has_key('Profilename'):
            self.doitWrapper(Profilename=kw['Profilename'])
        else:
            if self.vf.APBSSetup.cmdForms.has_key('default') and \
                self.vf.APBSSetup.cmdForms['default'].f.winfo_toplevel().\
                                                         wm_state() == 'normal':
                    filename = asksaveasfilename(filetypes=[('APBS Profile',
                                     '*.apbs.pf')],title="Save APBS Profile As",
                            parent = self.vf.APBSSetup.cmdForms['default'].root)
            else:
                filename = asksaveasfilename(filetypes = 
                  [('APBS Profile','*.apbs.pf')],title = "Save APBS Profile As")
            if filename:
                self.doitWrapper(Profilename=filename)
                

APBSSave_Profile_GUI = CommandGUI()
APBSSave_Profile_GUI.addMenuCommand('menuRoot', 'Compute', 'Save Profile',
                                                      cascadeName=cascadeName)

class APBSWrite_APBS_Parameter_File(MVCommand):
    """APBSOutputWrite writes APBS input file\n
    \nPackage : Pmv
    \nModule  : APBSCommands
    \nClass   : APBSWrite_APBS_Parameter_File
    \nCommand name : APBSOutputWrite
    \nSynopsis:\n
    None <---  APBSOutputWrite(filename)
    \nRequired Arguments:\n  
        filename = name of the apbs input file \n
     """
    def doit(self, filename = None):
        """doit function for APBSWrite_APBS_Parameter_File"""
        if filename: 
            self.vf.APBSSetup.params.SaveAPBSInput(filename)
      
    def guiCallback(self, **kw):
        """
        GUI Callback for APBSWrite_APBS_Parameter_File
        Asks for the file name to save current parameters 
        """
        filename=asksaveasfilename(filetypes=[('APBS Paramter File','*.apbs')],
                                               title="Save APBS Parameters As ")       
        apply ( self.doitWrapper, (filename,), kw)

APBSWrite_Parameter_File_GUI = CommandGUI()
APBSWrite_Parameter_File_GUI.addMenuCommand('menuRoot', 'Compute', \
                         'Write APBS Parameter File', cascadeName=cascadeName)

class APBSPreferences(MVCommand):
    """APBSPreferences allows to change APBS Preferences\n
    \nPackage : Pmv
    \nModule  : APBSCommands
    \nClass   : APBSPreferences
    \nCommand name : APBSPreferences
    \nSynopsis:\n
    None <---  APBSPreferences(APBS_Path = None, pdb2pqr_Path = None, ff = None,
debump = None, hopt = None, hdebump = None, watopt = None)
    \nOptional Arguments:\n  
        APBS_Path -- path to apbs executable
        pdb2pqr_Path -- path to pdb2pqr.py script
        ff -- Force Field for pdb2pqr ('amber', 'charmm' or 'parse')
        nodebump    :  Do not perform the debumping operation
        nohopt      :  Do not perform hydrogen optimization
        nohdebump   :  Do not perform hydrogen debumping
        nowatopt    :  Do not perform water optimization
     """
    def doit(self, APBS_Path = None, pdb2pqr_Path = None, ff = None,
                                               nodebump = False, nohopt = False):
        """
        doit function for APBSPreferences class
       \nOptional Arguments:\n  
        APBS_Path -- path to apbs executable
        pdb2pqr_Path -- path to pdb2pqr.py script
        ff -- Force Field for pdb2pqr ('amber', 'charmm' or 'parse')
        nodebump    :  Do not perform the debumping operation
        nohopt      :  Do not perform hydrogen optimization
        nohdebump   :  Do not perform hydrogen debumping
        nowatopt    :  Do not perform water optimization
        """
        self.overwrite_pqr = False
        if APBS_Path:
            self.vf.APBSSetup.params.APBS_Path = APBS_Path
        if pdb2pqr_Path:
            self.vf.APBSSetup.params.pdb2pqr_Path = pdb2pqr_Path
        if ff:
            self.vf.APBSSetup.params.pdb2pqr_ForceField = ff
        if nodebump != self.nodebump_past:
            self.nodebump_past = nodebump
            self.nodebump.set(nodebump)
            self.overwrite_pqr = True
        if nohopt != self.nohopt_past:
            self.nohopt_past = nohopt
            self.nohopt.set(nohopt)
            self.overwrite_pqr = True
            
    def __init__(self):
        MVCommand.__init__(self)
	try:
	        self.nodebump = Tkinter.BooleanVar()
	        self.nodebump.set(False)
	        self.nohopt = Tkinter.BooleanVar()
	        self.nohopt.set(False)
	except:
		self.nodebump = False
		self.nohopt = False

        self.nodebump_past = False
        self.nohopt_past = False
        self.overwrite_pqr = False
        
    def guiCallback(self):
        """GUI Callback for APBSPreferences"""
        self.APBS_Path = self.vf.APBSSetup.params.APBS_Path
        self.pdb2pqr_Path = self.vf.APBSSetup.params.pdb2pqr_Path
        self.ff_arg = Tkinter.StringVar()
        self.ff_arg.set(self.vf.APBSSetup.params.pdb2pqr_ForceField)
        self.ifd = ifd = InputFormDescr(title="APBS Preferences")
        ## APBS PATH GROUP
        ifd.append({'name':"APBS_Path",
                    'widgetType':Pmw.Group,
                    'container':{'APBS_Path':'w.interior()'},
                    'wcfg':{'tag_text':"Path to APBS executable"},
                    'gridcfg':{'sticky':'nswe','columnspan':5}
                    })
        ifd.append({'widgetType':Tkinter.Button,
                    'name':'APBS_Browse',
                    'parent':'APBS_Path',
                    'wcfg':{'text':'Browse ...',
                            'command':self.set_APBS_Path},
                    'gridcfg':{'sticky':'we', 'row':1, 'column':0}
                    })
        ifd.append({'widgetType':Pmw.EntryField,
                    'name':'APBS_Location',
                    'parent':'APBS_Path',
                    'wcfg':{'value':self.APBS_Path},
                    'gridcfg':{'sticky':'ew', 'row':1, 'column':1}
                    })                    
        ifd.append({'name':'APBSLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'APBS_Path',
                    'wcfg':{'text':"""\nAdaptive Poisson-Boltzmann Solver \
(APBS) should be installed\n before it can be run locally. \n Source code \
and/or binaries for APBS can be downloaded from
http://agave.wustl.edu/apbs/download \n 
Details on how to run APBS using Pmv can be found at
http://mccammon.ucsd.edu/pmv_apbs\n"""},
               'gridcfg':{'columnspan':2, 'sticky':'ew', 'row':2, 'column':0} })
        ##pdb2pqr.py PATH GROUP
        ifd.append({'name':"pqd2pqr_Path",
                    'widgetType':Pmw.Group,
                    'container':{'pdb2pqr_Path':'w.interior()'},
                    'wcfg':{'tag_text':"Path to pdb2pqr.py"},
                    'gridcfg':{'sticky':'nswe','columnspan':5}
                    })
        ifd.append({'widgetType':Tkinter.Button,
                    'name':'pdb2pqr_Browse',
                    'parent':'pdb2pqr_Path',
                    'wcfg':{'text':'Browse ...',
                            'command':self.set_pdb2pqr_Path},
                    'gridcfg':{'sticky':'we', 'row':1, 'column':0}
                    })
        ifd.append({'widgetType':Pmw.EntryField,
                    'name':'pdb2pqr_Location',
                    'parent':'pdb2pqr_Path',
                    'wcfg':{'value':self.pdb2pqr_Path},
                    'gridcfg':{'sticky':'ew', 'row':1, 'column':1}
                    })                    
        ifd.append({'name':'pdb2pqrLabel',
                    'widgetType':Tkinter.Label,
                    'parent':'pdb2pqr_Path',
                    'wcfg':{'text':"""\npdb2pqr.py is needed to create PQR \
files used by APBS. \n One can also use PDB2PQR Server to convert PDB files \
into PQR\n http://agave.wustl.edu/pdb2pqr, \
and read that PQR file instead\n"""},
                  'gridcfg':{'columnspan':2, 'sticky':'ew', 'row':2, 'column':0} 
                    })    
        ##pdb2pqr.py FORCE FIELD GROUP                                              
        ifd.append({'name':"pdb2pqr_ForceField",
                    'widgetType':Pmw.Group,
                    'container':{'pdb2pqr_ForceField':'w.interior()'},
                    'wcfg':{'tag_text':"pdb2pqr ForceField"},
                    'gridcfg':{'sticky':'nswe','columnspan':5}
                    })        
        ifd.append({'name':"Radiobutton_AMBER",
                    'widgetType':Tkinter.Radiobutton,
                    'parent':'pdb2pqr_ForceField',                    
                    'wcfg':{'value':'amber',
                    'variable':self.ff_arg},
                    'gridcfg':{'sticky':'w','row':0, 'column':0}
                    })                   
        ifd.append({'name':'Label_AMBER',
                    'widgetType':Tkinter.Label,
                    'parent':'pdb2pqr_ForceField',
                    'wcfg':{'text':'AMBER            '},
                    'gridcfg':{'sticky':'w', 'row':0, 'column':1} })
        ifd.append({'name':"Radiobutton_CHARMM",
                    'widgetType':Tkinter.Radiobutton,
                    'parent':'pdb2pqr_ForceField',                    
                    'wcfg':{'value':'charmm',
                    'variable':self.ff_arg},
                    'gridcfg':{'sticky':'w','row':0, 'column':2}
                    })
        ifd.append({'name':'Label_CHARMM',
                    'widgetType':Tkinter.Label,
                    'parent':'pdb2pqr_ForceField',
                    'wcfg':{'text':'CHARMM            '},
                    'gridcfg':{'sticky':'w', 'row':0, 'column':3} })
        ifd.append({'name':"Radiobutton_PARSE",
                    'widgetType':Tkinter.Radiobutton,
                    'parent':'pdb2pqr_ForceField',                    
                    'wcfg':{'value':'parse',
                    'variable':self.ff_arg},
                    'gridcfg':{'sticky':'w','row':0, 'column':4}
                    })
        ifd.append({'name':'Label_PARSE',
                    'widgetType':Tkinter.Label,
                    'parent':'pdb2pqr_ForceField',
                    'wcfg':{'text':'PARSE            '},
                    'gridcfg':{'sticky':'w', 'row':0, 'column':5} })
        ##pdb2pqr.py OPTIONS GROUP           
        ifd.append({'name':"pdb2pqr_Options",
                    'widgetType':Pmw.Group,
                    'container':{'pdb2pqr_Options':'w.interior()'},
                    'wcfg':{'tag_text':"pdb2pqr Options"},
                    'gridcfg':{'sticky':'nswe','columnspan':5}
                    })
        ifd.append({'name':"pdb2pqr_debump_Checkbutton",
                    'widgetType':Tkinter.Checkbutton,
                    'parent':'pdb2pqr_Options',                    
                    'wcfg':{
                    'variable':self.nodebump},
                    'gridcfg':{'sticky':'w','row':0, 'column':0}
                    })
        ifd.append({'name':'pdb2pqr_debump_Label',
                    'widgetType':Tkinter.Label,
                    'parent':'pdb2pqr_Options',                    
                    'wcfg':{'text':'Do not perform the debumping operation'},
                    'gridcfg':{'sticky':'w', 'row':0, 'column':1} })
        ifd.append({'name':"pdb2pqr_nohopt_Checkbutton",
                    'widgetType':Tkinter.Checkbutton,
                    'parent':'pdb2pqr_Options',                 
                    'wcfg':{
                    'variable':self.nohopt},
                    'gridcfg':{'sticky':'w','row':1, 'column':0}
                    })
        ifd.append({'name':'pdb2pqr_nohopt_Label',
                    'widgetType':Tkinter.Label,
                    'parent':'pdb2pqr_Options',
                    'wcfg':{'text':'Do not perform hydrogen optimization'},
                    'gridcfg':{'sticky':'w', 'row':1, 'column':1} })
        val = self.vf.getUserInput(ifd)
        if val:
            self.doitWrapper(val['APBS_Location'],
                                     val['pdb2pqr_Location'],self.ff_arg.get(),\
                     nodebump = self.nodebump.get(), nohopt = self.nohopt.get())
        
    def set_APBS_Path(self):
        """Sets APBS Path"""
        filename=askopenfilename(filetypes=[('APBS Executable','apbs*')],\
        title="Please select APBS Executable",parent=self.ifd[3]['widget'])
        # FIXME: Maybe there is a better way to get the parent
        if filename:
            self.APBS_Path = filename
            self.ifd.entryByName['APBS_Location']['widget'].setentry(filename)
            
    def set_pdb2pqr_Path(self):
        """Sets pdb2pqr Path"""
        filename=askopenfilename(filetypes=[('Python script','pdb2pqr.py')],
                  title="Please select pdb2pqr.py",parent=self.ifd[3]['widget'])
        if filename:
            self.pdb2pqr_Path = filename
            self.ifd.entryByName['pdb2pqr_Location']['widget'].\
                                                              setentry(filename)
        
APBSPreferences_GUI = CommandGUI()
APBSPreferences_GUI.addMenuCommand('menuRoot', 'Compute', 'Preferences',
                                    cascadeName=cascadeName )

commandList  = [{'name':'APBSRun','cmd':APBSRun(),'gui':APBSRun_GUI}]

flagMSMS = False
try:    
    import mslib
    flagMSMS = True
except:
    pass

if flagMSMS:
    commandList.append({'name':'APBSMapPotential2MSMS', 'cmd':
               APBSMap_Potential_to_MSMS(),'gui':APBSMap_Potential_to_MSMS_GUI},
)

commandList.extend([
                {'name':'APBSDisplayIsocontours', 'cmd':
               APBSDisplay_Isocontours(),'gui':APBSDisplay_Isocontours_GUI},
                {'name':'APBSDisplayOrthoSlice', 'cmd':
               APBSDisplayOrthoSlice(),'gui':APBSDisplayOrthoSlice_GUI},
                {'name':'APBSVolumeRender', 'cmd':
                 APBSVolumeRender(),'gui':APBSVolumeRender_GUI}
                ])

## flagVolume = False
## try:    
##     from Volume.Renderers.UTVolumeLibrary import UTVolumeLibrary
##     test = UTVolumeLibrary.VolumeRenderer()
##     flagVolume = test.initRenderer()
## except:
##     pass

## if flagVolume:
##     commandList.append({'name':'APBSVolumeRender', 'cmd':
##                APBSVolumeRender(),'gui':APBSVolumeRender_GUI})
    
commandList.extend([
                {'name':'APBSLoadProfile','cmd':APBSLoad_Profile(),'gui':
                                                          APBSLoad_Profile_GUI},
                {'name':'APBSSaveProfile','cmd':APBSSave_Profile(),'gui':
                                                          APBSSave_Profile_GUI},
                {'name':'APBSOutputWrite','cmd':APBSWrite_APBS_Parameter_File(),
                                            'gui':APBSWrite_Parameter_File_GUI},
                {'name':'APBSSetup','cmd':APBSSetup(),'gui':APBSSetupGUI},
                {'name':'APBSPreferences','cmd':APBSPreferences(),'gui':
                                                          APBSPreferences_GUI}])
def initModule(viewer):
    for _dict in commandList:
        viewer.addCommand(_dict['cmd'],_dict['name'],_dict['gui'])

def change_Menu_state(self, state):
    index = self.GUI.menuButton.menu.children[cascadeName].\
                                                index(self.GUI.menu[4]['label'])
    self.GUI.menuButton.menu.children[cascadeName].entryconfig(index, \
                                                             state = state)
    
