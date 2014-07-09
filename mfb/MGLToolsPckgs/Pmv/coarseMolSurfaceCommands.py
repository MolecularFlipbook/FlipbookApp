from mglutil.gui.InputForm.Tk.gui import InputFormDescr, InputForm, \
CallBackFunction
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import LoadButton, \
SaveButton, SliderWidget, ExtendedSliderWidget
from mglutil.util.callback import CallBackFunction
import Pmw, Tkinter
import types
from Pmv.mvCommand import MVCommand
from ViewerFramework.VFCommand import CommandGUI
from MolKit.molecule import Atom, Molecule
from Pmv.computeIsovalue import computeIsovalue
from mglutil.gui.InputForm.Tk.gui import AutoPlaceWidget
import time
import numpy
import numpy.oldnumeric as Numeric
from types import ListType

class coarseMolSurface(MVCommand):
    """Command to compute a coarse molecular surface.
    Selected atoms are first blurred as gaussians into a grid.
    The grid is then isocontoured at a user specified value.
    An indexed polygon geometry is added to the viewer. """
    
    
    def __init__(self, func=None):
        MVCommand.__init__(self)
        self.ifd = None
        self.resolutions={"very smooth":-0.1, "medium smooth": -0.3, "smooth": -0.5}
        self.resolution_type = "medium smooth"
        self.surf_resolution = self.resolutions[self.resolution_type] 
        self.isovalue=self.piecewiseLinearInterpOnIsovalue(self.surf_resolution)
        self.isovalue_type = "fast approximation"
        self.precise_isovalues = {}
        self.custom_isovalue_flag = 0
        self.custom_resolution_flag = 0
        self.surfName = "CoarseMolSurface"
        self.surfNameList = []
        self.mol_surfNames = {}
        self.CSparams = {} # used to store arguemnts to save session
        self.molName = None
        self.selection = None
        self.atomSet = None
        self.bindGeom = True
        
        self.perMol = True
        self.immediate = False

        self.gridSize = (32, 32, 32)
        self.buildFormFlag = False
        self.newSelection =False
        self.padding = 0.0
        self.surfaces = None
        self.UTblurData = None
        self.UTisocontourData = None
        self.isoCoords = None
        self.isoIndices = None
        self.isoNormals = None
        
    def onAddCmdToViewer(self):
        #if not self.vf.commands.has_key('vision'):
        #    self.vf.browseCommands('visionCommands',log=False)
        #if self.vf.vision.ed is None:
        #    self.vf.vision(log=False)
        self.vf.browseCommands('displayCommands', commands=('DisplayBoundGeom',), log=0, package='Pmv')

        if self.vf.hasGui:
            self.bindFlag = Tkinter.BooleanVar()
            self.bindFlag.set(self.bindGeom)

            self.perMolFlag = Tkinter.BooleanVar()
            self.perMolFlag.set(self.perMol)
        
            self.checkComponentsFlag = Tkinter.BooleanVar()
            self.checkComponentsFlag.set(False)
        
            self.messageDialog = Pmw.MessageDialog(self.vf.master, buttons=(), iconpos = 'w',
                                               icon_bitmap = 'warning')
            self.messageDialog.withdraw()
            self.messageDialog.configure(message_text="Please wait.\n It will take time to compute.")
            self.autoPlaceWidget = AutoPlaceWidget()
            self.autoPlaceWidget.root = self.messageDialog.winfo_toplevel()
        else:
            from mglutil.util.misc import BooleanVar
            self.bindFlag = BooleanVar(self.bindGeom)
            self.checkComponentsFlag = BooleanVar(False)
            self.perMolFlag = BooleanVar(self.perMol)

        from DejaVu.VisionInterface.GeometryNodes import ConnectedComponents
        self.connectedComp = ConnectedComponents()


##     def checkDependencies(self):
##         """check availability of mdules the command depends on"""
##         from UTpackages.UTisocontour import isocontour
##         from UTpackages.UTblur import blur
##         from mslib import MSMS
##         from QSlimLib import qslimlib

    def onAddObjectToViewer(self, obj):
        pass
    
    def guiCallback(self):
        selection = self.vf.getSelection()
        if not selection:
            return
        self.buildFormFlag = 1
        val = self.showForm( modal = 0, blocking=0, force = 1)
        if not self.custom_isovalue_flag:
            self.disableThumbWheel(self.ifd.entryByName['customIsovalue']['widget'])
        if not self.custom_resolution_flag:
            self.disableThumbWheel(self.ifd.entryByName['customResolution']['widget'])
##         if self.ifd:
##             bindmol = self.ifd.entryByName['bindToMolecule']
##             if len(selection.top.uniq()) > 1:
##                 # selected more than one molecule ->
##                 # disable "Bind to molecule" chekbutton
            
##                 bindmol['widget'].configure(state='disabled')
##                 bindmol['wcfg']['state']='disabled'
##             else:
##                 if bindmol['wcfg']['state']=='disabled':
##                     bindmol['widget'].configure(state='normal')
##                     bindmol['wcfg']['state']='normal'
        self.buildFormFlag = 0


    def buildFormDescr(self, formName="default"):
        
        if formName == 'default':
            ifd = self.ifd = InputFormDescr(title ="Compute Coarse Molecular Surface")
            #defaultValues = self.getLastUsedValues()
            #print "default values:", defaultValues

            self.immediate = False
            ifd.append({'widgetType':Tkinter.Checkbutton,
                        'tooltip':"""enables immediate update of the selected\n input parameter""",
                        'name': 'mode',
                        'defaultValue': self.immediate,
                        'wcfg':{'text':'Immediate',
                                'command':self.mode_cb,
                                'variable':Tkinter.BooleanVar()},
                        'gridcfg':{'sticky':'w','columnspan':2 }
                        })
            
            ifd.append({'widgetType':Pmw.ComboBox,
                        'name':'surfName',
                        'required':1,
                        'tooltip': "Type-in a new name or chose one \nfrom the list below,\n '_' are not accepted.",
                        'wcfg':{'labelpos':'n',
                                'label_text':'Select/type surface name: ',
                                'entryfield_validate':self.entryValidate,
                                'entryfield_value':self.surfName,
                                'scrolledlist_items':self.surfNameList,
                                'fliparrow':1,
                                'selectioncommand': self.select_surfname
                                },
                        'gridcfg':{'sticky':'we', 'columnspan':2},
                        
                        })
            
            ifd.append({'name':'perMol',
                        'tooltip':"""Check to compute a separate surface for each molecule (using selected atoms only).\nUncheck to compute a single surface for all selected atoms (possibly across multiple molecules).""",
                        'widgetType':Tkinter.Checkbutton,
                        'defaultValue': self.perMol,
                        'wcfg':{'text':'Per Molecule',
                                'variable':self.perMolFlag,
                                'command':self.perMol_cb},
                        'gridcfg':{'sticky':'w','columnspan':2}
                        })

            ifd.append({'widgetType':Pmw.EntryField,
                        'name':'gridsize',
                        'tooltip':'Type-in the grid size',
                        'wcfg':{'labelpos':'w',
                                'label_text':'Grid size: ',
                                'entry_width':8,
                                'value': self.gridSize[0],
                                'validate':{'validator': 'numeric',},
                                'command':self.set_gridsize},
                        'gridcfg':{'column':0, 'columnspan':2, 'sticky':'w'}
                        })
            ifd.append({
                        'widgetType':ThumbWheel,
                        'name':'padding',
                        'tooltip':
                        """size of the padding around the molecule """,
                        'gridcfg':{'sticky':'w','column':0,  'columnspan':2},
                        'wcfg':{'value':self.padding,
                                'oneTurn':10, 'min':0.0, 'lockMin':True,
                                'type':'float', 'precision':1,
                                'continuous':False,
                                'wheelPad':1,'width':90,'height':15,
                                'callback': self.set_padding,
                                'labCfg':{'text':'padding:'},
                                }
                        })
            ifd.append({'name':'resolutionGroup',
                        'widgetType':Pmw.Group,
                        'container':{'resolutionGroup':"w.interior()"},
                        
                        'wcfg':{'tag_text':"Surface resolution:", 'ring_borderwidth':3,},
                        'gridcfg':{'sticky':'we', 'columnspan':2}})

            ifd.append({'name':'resolution_type',
                        'widgetType':Pmw.RadioSelect,
                         'parent':'resolutionGroup',
                        'tooltip':
                        """ very smooth, medium smooth and smooth correspond to the blobbyness\n value (used in the gaussian blurring) of -0.1, -0.3, and -0.5 respectively""",
                        'listtext':['very smooth', 'medium smooth', 'smooth', 'custom'],
                        'defaultValue':self.resolution_type,
                        'wcfg':{'orient':'vertical','labelpos':'n',
                                'labelpos':None,
                                #'label_text':'Surface resolution: ',
                                'command':self.set_resolution,
                                #'hull_relief':'ridge',
                                #'hull_borderwidth':2,
                                'padx':0,
                                'buttontype':'radiobutton'},
                        'gridcfg':{'sticky': 'nw','column':0,  'columnspan':2}
                        })
            
            ifd.append({'name':'customResolution',
                        'parent':'resolutionGroup',
                        'widgetType':ThumbWheel,
                        'tooltip':
                        """Set custom resolution value""",
                        'gridcfg':{'sticky':'w','column':0,  'columnspan':2},
                        'wcfg':{'value':self.surf_resolution,'oneTurn':2, 
                                'type':'float',
                                'increment':0.05,
                                'precision':1,
                                'continuous':False,
                                "max":-0.009,
                                'wheelPad':2,'width':145,'height':18,
                                'showLabel':self.custom_resolution_flag, 'lockShowLabel':1,
                                'callback': self.set_custom_resolution
                                #'labCfg':{'text':'Surface Resolution:'},
                                }
                        })
           
            
            ifd.append({'name':'isovalueGroup',
                        'widgetType':Pmw.Group,
                        'container':{'isovalueGroup':"w.interior()"},
                        'wcfg':{'tag_text':"Isocontour values:",'ring_borderwidth':3},
                        'gridcfg':{'sticky':'we', 'columnspan':2}})
            ifd.append({'name':'isovalue_type',
                        'widgetType':Pmw.RadioSelect,
                        'parent': 'isovalueGroup',
                        'tooltip': "select isovalue option",
                        'listtext':['fast approximation',
                                        'precise value', 'custom'],
                        'defaultValue':self.isovalue_type,
                        'wcfg':{'orient':'vertical','labelpos':'n',
                                #'label_text':'Isocontour values:',
                                'labelpos':None,
                                'command':self.set_isovalue,
                                #'hull_relief':'ridge',
                                #'hull_borderwidth':2,
                                'padx':0,
                                'buttontype':'radiobutton'},
                        'gridcfg':{'sticky': 'nw','column':0,  'columnspan':2}
                        })
            isovalue = self.isovalue
            if type(self.isovalue) == ListType:
                isovalue = isovalue[0]
            ifd.append({'name':'customIsovalue',
                        'widgetType':ThumbWheel,
                        'parent': 'isovalueGroup',
                        'tooltip':
                        """Set custom isovalue""",
                        'gridcfg':{'sticky':'w','column':0,  'columnspan':2},
                        'wcfg':{'value':isovalue,'oneTurn':2, 
                                'type':'float',
                                'increment':0.1,
                                'precision':1,
                                'continuous':False,
                                'wheelPad':2,'width':145,'height':18,
                                'showLabel':self.custom_isovalue_flag, 'lockShowLabel':1,
                                'callback': self.set_custom_isovalue,
                                }
                        })


            ifd.append({'widgetType':Tkinter.Checkbutton,
                    'tooltip':"""Select/deselect this button to bind/unbind\nsurface to molecule""",
                        'name': 'bindToMolecule',
                        'wcfg':{'text':'Bind Surface to molecule',
                                'command':self.bind_cb,
                                'variable':self.bindFlag,
                                'state':'normal'},
                        'gridcfg':{'sticky':'w', 'pady': 10,'columnspan':2 }
                    })
            
            ifd.append({'widgetType':Tkinter.Checkbutton,
                    'tooltip':"""enable/disable checking for surface components.\nIf two or more componens are found - the largest\nis chosen for output""",
                        'name': 'checkComponents',
                        'wcfg':{'text':'Check surface components',
                                'variable':self.checkComponentsFlag,
                                'state':'normal'},
                        'gridcfg':{'sticky':'w', 'pady': 10,'columnspan':2 }
                    })
            
            ifd.append({'name':'compute',
                        'widgetType':Tkinter.Button,
                        'wcfg':{'text':'Compute',
                                'state': 'normal',
                                'command':self.compute},
                        'gridcfg':{'sticky':'wne','column':0}
                        })
                        
            ifd.append({'name':'dismiss',
                        'widgetType':Tkinter.Button,
                        'wcfg':{'text':'Dismiss',
                                'command':self.dismiss},
                        'gridcfg':{'sticky':'wne','row': -1, 'column':1}
                        })

            return ifd



    def doit(self, **kw):
        """list of keywords: nodes, surfName, perMol, gridSize, isovalue,
        resolution, bindGeom, immediate, padding.
        """
        #print "in doit kw:", kw
        surfName = kw.get("surfName")
        if surfName is None:
            surfName = self.surfName
        perMol = kw.get("perMol", None)
        if perMol == None:
            perMol = self.perMol
        nodes = kw.get("nodes", None)
        immediate = kw.get("immediate", None)
        if immediate is None:
            immediate = self.immediate
        gs = kw.get("gridSize", None)
        pd = kw.get("padding", None)
        resolution = kw.get("resolution", None)
        isotype = kw.get("isovalue", None)
        bindGeom = kw.get("bindGeom", None)
        if bindGeom == None:
            bindGeom = self.bindGeom
        bindcmd = self.vf.bindGeomToMolecularFragment

        parents = None
        surfaces = []
        mols = None
        atomSet = self.atomSet
        if perMol == True and bindGeom == False:
            perMol = False
            self.perMolFlag.set(False)
        if nodes:
            if perMol:
                mols, atomSet = self.vf.getNodesByMolecule(nodes, Atom)
                parents = []
                for mol in mols:
                    parents.append(mol.geomContainer.masterGeom)
                #atomSet = nodes.top.uniq()
            else:
                atomSet = nodes

        if bindGeom and not perMol: 
            if len(atomSet.top.uniq()) > 1:
                msg =  "More than one molecule selected-can not bind the geometry"
                self.vf.warningMsg(msg)
                bindGeom = False
                parents = None
            else:
                mol = atomSet.top.uniq()[0]
                parents = [mol.geomContainer.masterGeom]

        if atomSet != self.atomSet:
            self.atomSet = atomSet
            self.newSelection = True
            if nodes:
                for mol in nodes.top.uniq():
                    mol.defaultRadii()
##             if immediate:
##                 print "Immediate 1"
##                 self.surfaces = self.getSurface(mols, atomSet, bindGeom, parents)
        

        if surfName not in self.surfNameList:
            self.surfNameList.append(surfName)
            #print "surfNameList:", self.surfNameList
            if immediate and  self.vf.hasGui:
                self.ifd.entryByName['surfName']['widget'].setlist(self.surfNameList)
        if surfName != self.surfName:
            self.surfName = surfName
            if immediate:
                self.surfaces = self.getSurface(mols, atomSet, bindGeom, parents)
                return
                
        if perMol != self.perMol:
            self.perMol = perMol
            if immediate:
                self.surfaces = self.getSurface(mols, atomSet,  bindGeom, parents)
                return
                    
        if gs:
            gridSize = (gs, gs, gs)
            if gridSize != self.gridSize:
                self.gridSize = gridSize
                if immediate:
                    self.surfaces = self.getSurface(mols, atomSet,  bindGeom, parents)
                    return

        if pd is not None:
            if pd != self.padding:
                self.padding = pd
                if immediate:
                    self.surfaces = self.getSurface(mols, atomSet, bindGeom, parents)
                    return
        if resolution:
            if resolution != self.surf_resolution:
                self.surf_resolution = resolution
                if not isotype:
                    #check if we need to recompute isovalue:
                    if self.isovalue_type != "custom":
                        if self.isovalue_type == 'fast approximation':
                            isovalue = self.piecewiseLinearInterpOnIsovalue(resolution)
                        else:
                            isovalue = self.get_precise_isovalue(resolution)
                            
                        if isovalue is not None:
                            self.isovalue = isovalue

                        else:
                            print "Setting isocontour value to custom"
                            self.set_isovalue("custom")
                            self.isovalue_type = "custom"
                if immediate:
                    self.surfaces = self.getSurface(mols, atomSet, bindGeom, parents)
                    return

        if isotype:
            if type(isotype) == types.StringType:
                self.isovalue_type = isotype
                if isotype == 'fast approximation':
                    isovalue = self.piecewiseLinearInterpOnIsovalue(self.surf_resolution)
                else:
                    #check if we need to recompute precise isovalue:
                    isovalue = self.get_precise_isovalue(self.surf_resolution)
            else:
                self.isovalue_type = "custom"
                isovalue = isotype
            if isovalue is not None:
                if isovalue != self.isovalue:
                    self.isovalue = isovalue
                    if immediate:
                        self.surfaces = self.getSurface(mols, atomSet, bindGeom, parents)
                        return
            else:
                self.set_isovalue("custom")
                self.isovalue_type = "custom"
                
        if bindGeom != self.bindGeom:
            self.bindGeom = bindGeom
            if immediate:
                self.surfaces = self.getSurface(mols, atomSet, bindGeom, parents)
                return
                
        if not immediate:
            surfaces = self.getSurface(mols, atomSet, bindGeom, parents)
        self.surfaces = surfaces


    def __call__(self, **kw):
        """None <- mv.coarseMolSurface(**kw)\n
        list of available keywords:
        nodes    -- atomic fragment; \n
        surfName -- string - name of created surface; \n
        perMol   -- True or False; if True, a surface is computed for each 
                    molecule having at least one node in the current selection,
                    else the surface is computed for the current selection;\n
        gridZise -- integer; Size of computed grid will be: gridSize x gridSize x gridSize;\n
        isovalue -- can be one of the following: 'fast approximation', 'precise value' or
                      a numeric value specifying the isovalue;\n
        resolution -- resolution of the blurred surface - a negative value; \n
        bindGeom   -- True or False; if True - the surface is bound to the selected molecule.
        """
        nodes = kw.get("nodes")
        if nodes:
            kw["nodes"] = self.vf.expandNodes(nodes)
        apply(self.doitWrapper, (), kw)


    ## methods to compute UTblur grid, isocontour:

    def UTblur(self, molFrag, Xdim, Ydim, Zdim, padding, blobbyness):
        from UTpackages.UTblur import blur
        from Volume.Grid3D import Grid3DF
        from MolKit.molecule import Atom
        atoms = molFrag.findType(Atom)
        coords = atoms.coords
        #print "coords:", len(coords)
        radii = atoms.radius
        #print "radii,", radii
        #print "Xdim, Ydim, Zdim", Xdim, Ydim, Zdim
        #print "padding", padding
        #print "blobbyness:", blobbyness
        volarr, origin, span = blur.generateBlurmap(coords, radii, [Xdim, Ydim, Zdim], blobbyness, padding = padding)
        volarr.shape = (Zdim, Ydim, Xdim)
        volarr = Numeric.ascontiguousarray(Numeric.transpose(volarr), 'f')
        self.UTblurData = (volarr, origin, span)
        #print "volarr", volarr
        h = {}
        grid3D= Grid3DF( volarr, origin, span , h)
        #print "data:", grid3D.data
        h['amin'], h['amax'],h['amean'],h['arms']= grid3D.stats()
        return grid3D


    def UTisocontour(self, grid3D, isovalue, verbosity=None):
        from UTpackages.UTisocontour import isocontour
        if verbosity is not None:
            isocontour.setVerboseLevel(verbosity)

        data = grid3D.data
        #print 'isovalue', isovalue
        origin = Numeric.array(grid3D.origin).astype('f')
        stepsize = Numeric.array(grid3D.stepSize).astype('f')
        # add 1 dimension for time steps amd 1 for multiple variables
        if data.dtype != Numeric.float32:
            #print 'converting from ', data.dtype.char
            data = data.astype('f')

        newgrid3D = Numeric.ascontiguousarray(Numeric.reshape( Numeric.transpose(data),
                                                           (1, 1)+tuple(data.shape) ), data.dtype.char)
        # destroy the ConDataset structure
        if self.UTisocontourData:
            isocontour.delDatasetReg(self.UTisocontourData)

        self.UTisocontourData = gridData = isocontour.newDatasetRegFloat3D(\
                newgrid3D, origin, stepsize)
        #print "UTisocontourData", self.UTisocontourData
        sig = [gridData.getSignature(0, 0, 0),
               gridData.getSignature(0, 0, 1),
               gridData.getSignature(0, 0, 2),
               gridData.getSignature(0, 0, 3)]
        if self.UTisocontourData:
            isoc = isocontour.getContour3d(self.UTisocontourData, 0, 0, isovalue,
                                           isocontour.NO_COLOR_VARIABLE)

            vert = Numeric.zeros((isoc.nvert,3)).astype('f')
            norm = Numeric.zeros((isoc.nvert,3)).astype('f')
            col = Numeric.zeros((isoc.nvert)).astype('f')
            tri = Numeric.zeros((isoc.ntri,3)).astype('i')
            isocontour.getContour3dData(isoc, vert, norm, col, tri, 0)

            if grid3D.crystal:
                vert = grid3D.crystal.toCartesian(vert)
            self.isoCoords = vert
            self.isoIndices = tri
            self.isoNormals = norm
            return [vert, tri, norm]
        else:
            print "Warning: UTisocontourData is None, using saved coords, indices and normals"
            return [self.isoCoords, self.isoIndices, self.isoNormals]
        

    def objectByNameAndParent(self, name, parent):

        vi = self.vf.GUI.VIEWER
        if parent == None: parent = vi.rootObject
        ol = vi.rootObject.AllObjects()
        n, name = vi.GUI.lstripChar(name, '~')
        for o in ol:
            if o.name==name and o.parent==parent: return o
        return None


    def getSurface(self, mols, atomSet, bindGeom, parents=None):
        if not mols:
            atomSet = [atomSet]
            mols = [None]
        from types import ListType
        if type(self.isovalue) != ListType:
            isovals = [self.isovalue]
        else:
            isovals = self.isovalue
        if len(isovals) != len(mols):
            isovals = [isovals[0]]*len(mols)
        if not parents:
            if self.vf.hasGui:
                parents = [self.vf.GUI.VIEWER.rootObject]
            else:
                parents = [None]
        Xdim, Ydim, Zdim = self.gridSize
        bindcmd = self.vf.bindGeomToMolecularFragment
        surfaces = []
        checkComp = self.checkComponentsFlag.get()
        #print "in getSurface:", "mols:", mols, "atomSet:", atomSet, "bindGeom:", bindGeom, "parents:", parents
        for mol, atms, parent, isovalue in zip(mols, atomSet, parents, isovals):
            coords = None
            surf = None
            params = {"nodes": atms, "resolution": self.surf_resolution, "perMol":True,
                      "gridSize":self.gridSize[0], "bindGeom": bindGeom, "padding":self.padding, "isovalue":isovalue} 
            
            grid3D = self.UTblur(atms, Xdim, Ydim, Zdim, self.padding, self.surf_resolution)
            #print "UTblur", grid3D
            coords, indices, normals = self.UTisocontour(grid3D, isovalue)
            if coords is None:
                continue
            #print "UTisocontour", "coords:", len(coords)
            if self.vf.hasGui:
                surf = self.objectByNameAndParent(self.surfName, parent)
            if surf:
                #print "surface %s with parent %s exists, resetinng its verts and indices" % (self.surfName, parent.name)
                
                surf.Set(vertices=coords, faces=indices, 
                         tagModified=False, vnormals=normals, inheritMaterial=None)
                if checkComp:
                    #print "checking for connected components"
                    newindices, newfaces = self.checkConnectedComponents(surf)
                    surf.Set(vertices=newfaces, faces=newindices)
            else:
                from DejaVu.IndexedPolygons import IndexedPolygons
                surf = IndexedPolygons(name=self.surfName, vertices=coords, faces=indices, 
                                       tagModified=False, vnormals=normals, inheritMaterial=None)
                #print "surf:", surf
                if checkComp:
                    newindices, newfaces = self.checkConnectedComponents(surf)
                    surf.Set(vertices=newfaces, faces=newindices)
                if parent:
                    surf.parent = parent
                    surf.fullName = parent.fullName+"|"+self.surfName
                else:
                    surf.fullName=self.surfName
                #print "Adding surf to viewer, parent:", parent
                if self.vf.hasGui:
                    self.vf.GUI.VIEWER.AddObject(surf, parent)
            if not surf:
                continue
            if bindGeom:
                #print "binding geom ", surf
                bindcmd(surf, atms, log=0)
            surfaces.append(surf)
            self.CSparams[surf.fullName] = params
            
        if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
            for surf in surfaces:
                surf.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False,)   
        # highlight selection
        selMols, selAtms = self.vf.getNodesByMolecule(self.vf.selection, Atom)
        lMolSelectedAtmsDict = dict( zip( selMols, selAtms) )
        for surf in surfaces:
            if hasattr(surf, 'mol') and lMolSelectedAtmsDict.has_key(surf.mol):
                lSelectedAtoms = lMolSelectedAtmsDict[surf.mol]
                if len(lSelectedAtoms) > 0 and len(surf.vertexSet.vertices) > 0:
                    lAtomVerticesDict = bindcmd.data[surf.fullName]['atomVertices']
                    highlight = [0] * len(surf.vertexSet.vertices)
                    for lSelectedAtom in lSelectedAtoms:
                        try:
                            lVertexIndices = lAtomVerticesDict.get(lSelectedAtom, [])
                            for lVertexIndex in lVertexIndices:
                                highlight[lVertexIndex] = 1
                        except: pass
                    surf.Set(highlight=highlight)
##                     if perMol:
##                         surf.removeFacesWithoutHighlightedVertices()
        return surfaces


    # Callbacks

                
    def perMol_cb(self, event=None):
        """calback of perMol check button of the input form"""
        ebn = self.ifd.entryByName
        perMol = ebn['perMol']['wcfg']['variable'].get()
        print  "in perMol_cb:", perMol
        #self.perMol = perMol
        ebn = self.ifd.entryByName
        immediate = ebn['mode']['wcfg']['variable'].get()
        if immediate:
            surfName = self.ifd.entryByName['surfName']['widget'].get()
            if surfName != self.surfName:
                self.surfName = surfName
            self.doitWrapper(nodes = self.vf.getSelection(), perMol = perMol,immediate=True, bindGeom = self.bindFlag.get())
        
        
    def mode_cb (self, event=None):
        """callback of the input form's immediate mode check button""" 
        ebn = self.ifd.entryByName
        immediate = ebn['mode']['wcfg']['variable'].get()
        computeButton = ebn['compute']['widget']
        if immediate:
            computeButton.configure(state='disabled')
            ebn['compute']['wcfg']['state']='disabled'
        else:
            computeButton.configure(state='normal')
            ebn['compute']['wcfg']['state']='normal'
        self.immediate = immediate

    def select_surfname(self, surfName):
        """callback of surface name ComboBox """
        if surfName:
            if surfName in self.surfNameList:
                surf = self.vf.GUI.VIEWER.GUI.objectByName(surfName)
                if surf and hasattr(surf, "mol"):
                    self.bindFlag.set(True)
            immediate = self.ifd.entryByName['mode']['wcfg']['variable'].get()
            if immediate:
                selection = self.vf.getSelection()
                self.doitWrapper(nodes=selection, surfName = surfName, immediate = immediate, bindGeom = self.bindFlag.get())
            
    def set_gridsize(self):
        """callback of the 'grid size' entry field"""
        val = self.ifd.entryByName['gridsize']['widget'].get()
        if val:
            immediate = self.ifd.entryByName['mode']['wcfg']['variable'].get()
            if immediate:
                selection = self.vf.getSelection()
                #check if self.surfName corresponds to the name typed in the entryform:
                surfName = self.ifd.entryByName['surfName']['widget'].get()
                if surfName != self.surfName:
                    self.surfName = surfName
                    #self.doitWrapper(nodes=selection, surfName = surfName, immediate =False)#do not run the network yet
                    
                self.doitWrapper(nodes=selection, immediate = True, gridSize = int(val), bindGeom = self.bindFlag.get())
        
    def set_resolution(self, val):
        """callback of the input form's resolution radio buttons"""
        #print "in set_resolution val = ", val
        if self.buildFormFlag:
            return
        self.resolution_type = val
        if val == "custom":
            self.custom_resolution_flag = 1
            self.enableThumbWheel(self.ifd.form.descr.entryByName['customResolution']['widget'],
                                  val = self.surf_resolution)
        else:
            self.custom_resolution_flag = 0
            self.disableThumbWheel(self.ifd.form.descr.entryByName['customResolution']['widget'])
            surf_resolution = self.resolutions[val]
            cb = self.ifd.entryByName['isovalue_type']['widget']
            if surf_resolution < -3.0  or surf_resolution > -0.1:
                # resolution is out of range of values for isovalue fast approximation -
                # need to disable the check button:
                cb.component('fast approximation').configure(state='disabled')
                if cb.getvalue() == "fast approximation":
                    self.set_isovalue("custom")
            else:
                if cb.component('fast approximation').cget('state') == 'disabled':
                    cb.component('fast approximation').configure(state = "normal")
            immediate = self.ifd.entryByName['mode']['wcfg']['variable'].get()
            if immediate:
                selection = self.vf.getSelection()
                #check if self.surfName corresponds to the name typed in the entryform:
                surfName = self.ifd.entryByName['surfName']['widget'].get()
                if surfName != self.surfName:
                    self.surfName = surfName
                    #self.doitWrapper(nodes=selection,surfName = surfName, immediate =False)#do not run the network yet
                self.doitWrapper(nodes=selection, resolution = surf_resolution, immediate = True, bindGeom = self.bindFlag.get())

    def set_isovalue(self, val):
        """ callback of the input form's isovalue radio buttons """
        #print "in set_isovalue val = ", val
        if self.buildFormFlag:
            return
        if val == "custom":
            self.isovalue_type = "custom"
            self.custom_isovalue_flag = 1
            if self.ifd:
                isovalue = self.isovalue
                if type(self.isovalue) == ListType:
                    isovalue = self.isovalue[0]
                self.enableThumbWheel(self.ifd.entryByName['customIsovalue']['widget'],
                                      val = isovalue)
        else:
            self.custom_isovalue_flag = 0
            self.disableThumbWheel(self.ifd.entryByName['customIsovalue']['widget'])
            immediate = self.ifd.entryByName['mode']['wcfg']['variable'].get()
            if immediate:
                #check if self.surfName corresponds to the name typed in the entryform:
                surfName = self.ifd.entryByName['surfName']['widget'].get()
                selection = self.vf.getSelection()
                if surfName != self.surfName:
                    self.surfName = surfName
                    #self.doitWrapper(nodes=selection,surfName = surfName, immediate =False)#do not run the network yet
                self.doitWrapper(nodes=selection, isovalue=val, immediate = True, bindGeom = self.bindFlag.get())
            

    def set_padding(self, val):
        """callback of the thumbwheel widget for setting padding around the molecule."""
        #print "calls set_padding"
        immediate = self.ifd.entryByName['mode']['wcfg']['variable'].get()
        if immediate:
           #check if self.surfName corresponds to the name typed in the entryform:
            surfName = self.ifd.entryByName['surfName']['widget'].get()
            selection = self.vf.getSelection()
            if surfName != self.surfName:
                self.surfName = surfName
                #self.doitWrapper(nodes=selection,surfName = surfName, immediate =False)#do not run the network yet
            self.doitWrapper(nodes=selection,padding=val, immediate = True, bindGeom = self.bindFlag.get() ) 

            
    def set_custom_isovalue(self, val):
        """callback of the thumbwheel widget used for setting custom isovalue """
        #print "in set_custom_isovalue val = ", val
        immediate = self.ifd.entryByName['mode']['wcfg']['variable'].get()
        if immediate:
            #check if self.surfName corresponds to the name typed in the entryform:
            surfName = self.ifd.entryByName['surfName']['widget'].get()
            selection = self.vf.getSelection()
            if surfName != self.surfName:
                self.surfName = surfName
                #self.doitWrapper(nodes=selection,surfName = surfName, immediate =False)#do not run the network yet
            self.doitWrapper(nodes=selection,isovalue=val, immediate = True, bindGeom = self.bindFlag.get() )

    def set_custom_resolution(self, val):
        """callback of the thumbwheel widget used for setting custom resolution"""
        #print "in set_custom_resolution val = ", val
        cb = self.ifd.entryByName['isovalue_type']['widget'].component('fast approximation')
        if val < -3.0  or val > -0.1:
            # resolution is out of range of values for isovalue fast approximation -
            # need to disable the check button:
            cb.configure(state='disabled')
            if self.ifd.entryByName['isovalue_type']['widget'].getvalue() == "fast approximation":
                self.set_isovalue("custom")
                self.isovalue_type = "custom"
        else:
            if cb.cget('state') == 'disabled':
                cb.configure(state = "normal")
        immediate = self.ifd.entryByName['mode']['wcfg']['variable'].get()
        if immediate:
            #check if self.surfName corresponds to the name typed in the entryform:
            surfName = self.ifd.entryByName['surfName']['widget'].get()
            selection = self.vf.getSelection()
            if surfName != self.surfName:
                self.surfName = surfName
                #self.doitWrapper(nodes=selection,surfName = surfName, immediate =False)#do not run the network yet
            self.doitWrapper(nodes=selection,resolution = val, immediate = True, bindGeom = self.bindFlag.get())

                
    def dismiss (self, event = None):
        """Withdraws the input form"""
        
        self.cmdForms['default'].withdraw()


    def bind_cb(self):
        """callback of the 'bind surface to molecule' check button """

        immediate = self.ifd.entryByName['mode']['wcfg']['variable'].get()
        if immediate:
            surfName = self.ifd.entryByName['surfName']['widget'].get()
            if surfName != self.surfName:
                self.surfName = surfName
            self.doitWrapper(nodes=self.vf.getSelection(), immediate = True, bindGeom = self.bindFlag.get())

    def checkConnectedComponents(self, geometry):
        newfaces, newverts = self.connectedComp.findComponents(geometry)
        # find the largest set of faces:
        maxn = 0
        maxind = None
        for i, newfs  in enumerate(newfaces):
            lenf = len(newfs)
            if lenf > maxn:
                maxn = lenf
                maxind = i
        #print 'len faces of %s is %d'%(name, len(newfaces[maxind]))
        return newfaces[maxind], newverts[maxind]


    def get_precise_isovalue(self, resolution):
        """Computes precise isovalue using methods from computeIsovalue.py """
        
        from types import ListType
        if type(self.atomSet) == ListType:
            atomSets = self.atomSet
        else:
            atomSets = [self.atomSet]
            
        res_str = "%.2f"%resolution
        isovalue = []
        for atms in atomSets:
            mols = ""
            for mol in  atms.top.uniq():
                mols += mol.name + " "
            # check if the precise isovalue has been computed vor this atomset and resolution:
            atmsString = atms.buildRepr()
            val = None
            if self.precise_isovalues.has_key(atmsString):
                val = self.precise_isovalues[atmsString].get(res_str)
            else:
                self.precise_isovalues[atmsString]={}
            if val is not None:
                isovalue.append(val)
            else:
                # need to compute isovalue:
                if self.vf.hasGui:
                    if self.vf.master:
                        self.autoPlaceWidget._set_transient(self.vf.master, 0.5, 0.9)
                    self.messageDialog.configure(message_text="Please wait.\n It will take time to compute isovalue\nfor %s." % mols)
                    self.messageDialog.show()
                    self.messageDialog.update()
                else:
                    print "Please wait. It will take time to compute..."
                val = computeIsovalue(atms, resolution, self.gridSize)
                if val is not None:
                    isovalue.append(val)
                    self.precise_isovalues[atmsString][res_str] = val
                if self.vf.hasGui:
                    self.messageDialog.withdraw()
                else:
                    print "...done"
        if not len(isovalue):
            isovalue = None
        return isovalue


    def entryValidate(self, text):
        """
        Method to validate the name of the msms surface. This name
        will be used by other command to build Pmw widget so it can't
        contain an '_'.
        """
        if '_' in text:
            return Pmw.ERROR
        else:
            return Pmw.OK

    def compute(self, event = None):
        """callback of 'Compute' button of the input form """
        kw = {}
        surfName = self.ifd.entryByName['surfName']['widget'].get()
        if surfName != self.surfName:
            kw['surfName']=surfName

        restype = self.ifd.entryByName['resolution_type']['widget'].getvalue()
        if restype == "custom":
            resolution = self.ifd.entryByName['customResolution']['widget'].get()
        else:
            resolution = self.resolutions[restype]
        kw['resolution'] = resolution
        isovalue = self.ifd.entryByName['isovalue_type']['widget'].getvalue()
        if isovalue == "custom":
            isovalue = self.ifd.entryByName['customIsovalue']['widget'].get()
        kw['isovalue'] = isovalue
        perMol = self.ifd.entryByName['perMol']['wcfg']['variable'].get()
        kw['perMol'] = perMol
        kw['immediate'] = False
        gs= self.ifd.entryByName['gridsize']['widget'].get()
        if gs:
            kw['gridSize'] = int(gs)
        kw['bindGeom'] = self.bindFlag.get()
        kw['nodes'] = self.vf.getSelection().copy()
        kw['padding'] = self.ifd.entryByName['padding']['widget'].get()
        self.dismiss()
        apply(self.doitWrapper, (), kw)
        #self.dismiss()


    def disableThumbWheel(self, tw):
        """disables a thumbwheel widgets used to specify custom resolution/isovalue"""
        def foo(val):
            pass
        tw.configure(showLabel=0)
        tw.canvas.bind("<ButtonPress-1>", foo)
	tw.canvas.bind("<ButtonRelease-1>", foo)
	tw.canvas.bind("<B1-Motion>", foo)
        tw.canvas.bind("<Button-3>", foo)
        
        
    def enableThumbWheel(self, tw, val =None):
        """enables a thumbwheel widgets used to specify custom resolution/isovalue"""
        tw.canvas.bind("<ButtonPress-1>", tw.mouseDown)
	tw.canvas.bind("<ButtonRelease-1>", tw.mouseUp)
	tw.canvas.bind("<B1-Motion>", tw.mouseMove)
        tw.canvas.bind("<Button-3>", tw.toggleOptPanel)
        tw.configure(showLabel=1)
        if val:
            tw.set(val, update=0)

    def piecewiseLinearInterpOnIsovalue(self, x):
        """Piecewise linear interpretation on isovalue that is a function
        blobbyness.
        """
        import sys
        X = [-3.0, -2.5, -2.0, -1.5, -1.3, -1.1, -0.9, -0.7, -0.5, -0.3, -0.1]
        Y = [0.6565, 0.8000, 1.0018, 1.3345, 1.5703, 1.8554, 2.2705, 2.9382, 4.1485, 7.1852, 26.5335]
        if x<X[0] or x>X[-1]:
            print "WARNING: Fast approximation :blobbyness is out of range [-3.0, -0.1]"
            return None
        i = 0
        while x > X[i]:
            i +=1
        x1 = X[i-1]
        x2 = X[i]
        dx = x2-x1
        y1 = Y[i-1]
        y2 = Y[i]
        dy = y2-y1
        return y1 + ((x-x1)/dx)*dy


coarseMolSurfaceGUI = CommandGUI()
coarseMolSurfaceGUI.addMenuCommand('menuRoot','Compute', 'Coarse Molecular Surface')
commandList  = [{'name':'coarseMolSurface','cmd':coarseMolSurface(),'gui':coarseMolSurfaceGUI},]

def initModule(viewer):
    for com in commandList:
        viewer.addCommand(com['cmd'],com['name'],com['gui'])
