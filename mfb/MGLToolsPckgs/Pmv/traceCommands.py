#############################################################################
#
# author: Sophie COON, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################
"""Module for Compute,Extrude and Display Trace.
This module provides a set of commands:
- ComputeTraceCommand (computeTrace) to compute a trace and the corresponding
  sheet2D using the given control atoms and torsion atoms. Typically used to
  compute a CA trace for a protein
- ExtrudeTraceCommand (extrudeTrace) to extrude a 2D geometry along the 3D
  path to represent the given trace.
- DisplayTraceCommand (displayTrace) to display, undisplay or display only
  parts of the molecule using the geometry created to represent the given
  trace.
  Keywords:
  Trace, CA 
  
"""
#
#$Header: /opt/cvs/python/packages/share1.5/Pmv/traceCommands.py,v 1.32 2010/10/13 01:37:28 sanner Exp $
#
#$Id: traceCommands.py,v 1.32 2010/10/13 01:37:28 sanner Exp $
#

from MolKit.protein import Coil, Chain, ResidueSet, SecondaryStructureSet
from MolKit.protein import Residue
from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Atom, AtomSet

from DejaVu.Shapes import Shape2D, Triangle2D, Circle2D, Rectangle2D,\
     Square2D, Ellipse2D

from DejaVu.IndexedPolygons import IndexedPolygons
from DejaVu.Geom import Geom

from Pmv.mvCommand import MVCommand
from Pmv.displayCommands import DisplayCommand
from Pmv.extruder import ExtrudeSSElt, Sheet2D

from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ExtendedSliderWidget
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser

from ViewerFramework.VFCommand import CommandGUI
from opengltk.OpenGL import GL
from types import StringType
import Tkinter, Pmw,types



class ComputeTraceCommand(MVCommand):
    """This command computes the oriented spline (trace) for the molecules in the current selection. It creates a Coil object for each chaine of the molecule having at least one node in the current selection.The Coil object can only be created for the residues having the chosen ctlAtm and torsAtm.
    \nPackage : Pmv
    \nModule  : traceCommands
    \nClass   : ComputeTraceCommand
    \nCommand : computeTrace
    \nkeywords: compute trace
    \nSynopsis:\n
        None <- computeTrace(nodes, traceName='CATrace', ctlAtmName='CA',
                             torsAtmName='O',nbchords = 4, **kw)
    \nRequired Arguments:\n    
        nodes --- any set of MolKit nodes describing molecular components
    \nOptional Arguments:\n    
        traceName --- string representing the name of the computed trace.
                     default 'CATrace'
        \nctlAtmName --- name of the atom to be used for control (defaul='CA')
        \ntorsAtmName --- name of the atom to be used to control the torsion.
                     default='O'
        \nnbchords --- number of points per residue. The higher the number the
                     smoother the trace will be.
    """

    def __init__(self):
        MVCommand.__init__(self)
        self.flag = self.flag | self.objArgOnly

    def pickedVerticesToAtoms(self, geom, vertInd ):
        """
        Function called to convert a picked vertex into the first atom
        of the picked residue
        """
        trace = geom.trace
        l = []
        for vi in vertInd:
            resInd = trace.exElt.getResIndexFromExtrudeVertex( vi )
            l.append(trace.children[resInd].atoms[0])
        return AtomSet( AtomSet( l ) )


    def onAddCmdToViewer(self):
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('computeSheet2D'):
            self.vf.loadCommand("extrusionCommands", 'computeSheet2D',
                                "Pmv", topCommand = 0)
     
    
    
    def atomPropToVertices(self, geom, residues, propName, propIndex = None):
        """
        Function called to compute the array of property for the given
        residues
        """
        
        if residues is None or len(residues)==0 : return None
        propVect = []
        if not propIndex is None:
          propIndex = self.traceName
        for r in residues:
            prop = getattr(r.atoms[0], propName)
            if not propIndex is None:
                propVect.append(prop[propIndex])
            else:
                propVect.append(prop)

        geom.trace.exElt.setResProperties(propVect, propName, residues)
        properties = geom.trace.exElt.getExtrudeProperties( residues,
                                                            propName )
        return properties

    
    
    def dialog(self,mol):
        msg ="Use Previous Trace for %s" %(mol.name)
        from SimpleDialog import SimpleDialog
        d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['No','Yes'], default=1, 
                title='Display?')
        ok =d.go()
        if ok ==0:
            self.disp = False
        else:
            self.disp = True
        return self.disp    
       
    def createGeometries(self, mol,nodes):
        """
        Initialize the geometries that will be used to represent the CA Trace
        objects for the given molecule mol.
        """
        traceName = self.traceName
        # get a handle on the geomContainer
        geomC = mol.geomContainer
        # Create a trace parent geometry for the molecule if doesn't
        # exist already
        if not geomC.geoms.has_key('trace'):
            p = Geom('trace',  shape=(0,0), protected=True)
            geomC.addGeom( p, parent=geomC.masterGeom,redo=0 )
        else:
            p = geomC.geoms['trace']
             
        # Then create a traceName parent geometry 
        if not geomC.geoms.has_key(traceName) :
            c = Geom(traceName,  shape=(0,0), protected=True)
            geomC.addGeom(c, parent=p,redo=0)
            self.managedGeometries.append(c)
            
            for a in mol.allAtoms:
                a.colors[traceName]=(1.,1.,1.)
                a.opacities[traceName]=1.0 
        else:
            newval =0
            self.mol=mol
            c = geomC.geoms[traceName]
            for chain in mol.chains:
                cname = traceName+chain.id
                #if geomC.geoms.keys has cname
                if geomC.geoms.has_key(cname):
                    #if morethan one chain not to display dialogbox for each
                    #chain ,newval var is initialized to zero.If No selected in                                           #dialog box(doesn't want to use existing same trace and want to compute new one)
                    #then newvar set to 1  
                    if newval ==0 and geomC.atoms[cname]!=[]:
                        rval =self.dialog(mol)
                    #if doesn't want to use existing trace 
                    #trace is made invisible
                    #and is removed since in color commands for coloring geom
                    #checks for coords so trace is removed 
                        if rval ==False:
                            newval =1
                            geomC.geoms[cname].Set(visible=0, tagModified=False, protected=False)
                            self.vf.GUI.VIEWER.RemoveObject(geomC.geoms[cname])
                            del geomC.geoms[cname]
                            del geomC.atoms[cname]       
                        else:
                            return 
            # Initialize the atom colors and opacities dictionary for the
            # 'trace' entry

        # loop over the chain of the given molecule
        for chain in mol.chains:
            if not hasattr(chain, 'trace') or \
               not chain.trace.has_key(traceName): continue
            if chain.trace[traceName] is None: continue        
            # get a handle on the trace object
            trace = chain.trace[traceName]
            # name of the geometry representing the catrace is the
            # concatenation of the catrace object name and the chain id.
            name = traceName+chain.id
            # Create an empty IndexedPolygons to represent the ca trace of the
            # chain and add it to the Viewer
            g = IndexedPolygons(name, visible=0, pickableVertices=1, protected=True,)
            if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
                g.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False,)
            if not geomC.geoms.has_key(name) or (geomC.geoms.has_key(name) and (geomC.atoms[name] == [])):
                geomC.addGeom(g, parent=c)
                self.managedGeometries.append(g)
            
            #g.RenderMode(GL.GL_FILL, face=GL.GL_FRONT)
            geomC.atoms[name] = ResidueSet()
            g.Set(frontPolyMode=GL.GL_FILL)
            g.trace = trace
            g.mol = mol #need for backtracking picking
            geomC.atomPropToVertices[name] = self.atomPropToVertices
            geomC.geoms[name] = g
            geomC.geomPickToAtoms[name] = self.pickedVerticesToAtoms
            geomC.geomPickToBonds[name] = None
            
            childtrace=traceName+chain.id
            if not hasattr(chain, 'trace') or \
               not chain.trace.has_key(traceName): continue
            
    def doit(self, nodes, traceName='CATrace', ctlAtmName = 'CA',
             torsAtmName='O', nbchords = 4):
        if len(nodes) == 0:
            return
        self.vf.computeSheet2D(nodes, traceName, ctlAtmName, torsAtmName,
                               nbchords=nbchords, topCommand=0)
        j = 0
        
        self.traceName = traceName
        molecules, chainSet = self.vf.getNodesByMolecule(nodes, Chain)
        for mol, chains in map(None, molecules, chainSet):
            for chain in chains:
                if not hasattr(chain, 'trace'): chain.trace = {}
                if chain.sheet2D[traceName] is None:
                    chain.trace[traceName]=None
                    msg = "WARNING: the %s for the chain %s of the molecule %s\ncould not be computed with the given parameters"%(traceName,chain.id, mol.name)
                    self.warningMsg(msg)
                    continue
                else:
                    res = chain.sheet2D[traceName].resInSheet
                    chain.trace[traceName] = Coil(chain=chain,
                                                  structureType=traceName,
                                                  index = j, start = res[0],
                                                  end = res[-1],
                                                  createNewLevel=0)
                    j = j+1
                    chain.trace[traceName].sheet2D = chain.sheet2D[traceName]

            self.createGeometries(mol,nodes)
                
    def getAvailableTrace(self):
        mols = self.vf.getSelection().top.uniq()
        tracesName = []
        for m in mols:
            if not m.geomContainer.geoms.has_key('trace'): continue
            names = map(lambda x: x.name,
                        m.geomContainer.geoms['trace'].children)
            for n in names:
                if not n in tracesName: tracesName.append(n)
        return tracesName
         
                
    def buildFormDescr(self, formName):
        if formName == 'traceForm':
            idf = InputFormDescr('Compute Trace')
            idf.append({'name':'traceName',
                        'widgetType':Pmw.ComboBox,
                        'tooltip':'Create a new trace by typing a new trace \n\
name in the entry of the combobox. \nHit the Enter key to add it to the list \
of trace name. \nYou can also choose from the existing list of trace names.\n\
To see the list click on the down arrow.',
                        'defaultValue':self.traceNames[0],
                        'wcfg':{'label_text':'Choose a trace: ',
                                'labelpos':'w',
                                'scrolledlist_items': self.traceNames,
                                },
                        'gridcfg':{'sticky':'w','columnspan':2}})

            idf.append({'name':'ctlAtmName',
                        'widgetType':Pmw.EntryField,
                        'tooltip':'String representing the name of the atom \n\
to be used as control atom. Specify only one atom name.',
                        'wcfg':{'label_text':'Control atom name:',
                                'labelpos':'w', 'entry_width':4,
                                'value':'CA'},
                        'gridcfg':{'sticky':'w'}})
            
            idf.append({'name':'torsAtmName',
                        'widgetType':Pmw.EntryField,
                        'tooltip':'String representing the name of the atom \n\
to be used to control the torsion. Specify only one atom name.',
                        'wcfg':{'label_text':'Torsion atom name:',
                                'labelpos':'w', 'entry_width':4,
                                'value':'O'},
                        'gridcfg':{'sticky':'w', 'row':-1}})


            idf.append( {'name': 'nbchords',
                         'widgetType':ExtendedSliderWidget,
                         'type':int,
                         'tooltip':'Specifies the number of points per \
residues.\n The higher the number the smoother the trace will be.',
                        'wcfg':{'label': 'nb points per residues',
                                 'minval':4,'maxval':15,
                                 'incr': 1, 'init':4,
                                 'labelsCursorFormat':'%d',
                                 'sliderType':'int'
                                 },
                         'gridcfg':{'sticky':'w', 'columnspan':2},
                         })

            return idf
                
    def guiCallback(self):
        self.traceNames = self.getAvailableTrace()
        if not self.traceNames:self.traceNames = ['CATrace',]
        if self.cmdForms.has_key('traceForm'):
            form = self.cmdForms['traceForm']
            combo = form.descr.entryByName['traceName']['widget']
            if self.traceNames != combo.get():
                combo.setlist(self.traceNames)

        val = self.showForm('traceForm')
        if not val: return
        if len(val['traceName']) == 0:
            return
        val['traceName'] = val['traceName'][0]
        if not val['ctlAtmName'] or not val['torsAtmName']: return
        val['redraw']=0
        apply(self.doitWrapper, (self.vf.getSelection(), ), val)


    def __call__(self, nodes, traceName='CATrace', ctlAtmName='CA',
                 torsAtmName='O', nbchords=4, **kw):
        """None <- computeTrace(nodes, traceName='CATrace', ctlAtmName='CA',
                             torsAtmName='O',nbchords = 4, **kw)
        \nRequired Arguments:\n
            nodes     : any set of MolKit nodes describing molecular components
        \nOptional Arguments:\n
            traceName : string representing the name of the computed trace.
                    (default 'CATrace')
            \nctlAtmName : name of the atom to be used for control (defaul='CA')
            \ntorsAtmName: name of the atom to be used to control the torsion.
                     (default='O')
            \nnbchords   : number of points per residue. The higher the number the smoother the trace will be. (default = 4)
        """
        if nodes is None:
            return
        nodes=self.vf.expandNodes(nodes)
        if not nodes:
            return "ERROR"
        kw['traceName'] = traceName
        kw['ctlAtmName'] = ctlAtmName
        kw['torsAtmName'] = torsAtmName
        kw['nbchords'] = nbchords
        kw['redraw']=0
        if type(nodes) is StringType:
            self.nodeLogString = "'" + nodes +"'"
        apply (self.doitWrapper, (nodes,), kw )


class ExtrudeTraceCommand(MVCommand):
    """This command extrude a shape 2D along the path 3D of a given trace computed by the computeTrace command.
    \nPackage : Pmv
    \nModule  : traceCommands
    \nClass   : ExtrudeTraceCommand
    \nCommand : extrudeTrace
    \nSynopsis:
       None <- extrudeTrace(nodes, traceName='CATrace', shape2D=None,
                            frontCap=1, endCap=1, display=1, **kw)
    \nRequired Arguments:\n   
       nodes --- any set of MolKit nodes describing molecular components.
    \nOptional Arguments:\n  
       traceName --- string representing the name of the trace to be represented
                  the default value is 'CATrace'.
       \nshape2D --- instance of a DejaVu.Shape class describing the shape 2D
                  to be extruded along the path3D of the selected trace.
                  By default a Circle2D will be extruded
       \nfrontCap --- when set to 1 a cap is added to all the front of the extruded
                  geometry created to represent the selected trace.
       \nendCap --- when set to 1 a cap is added to all the end of the extruded
                  geometry representing the selected trace.
       \ndisplay  --- when set to 1 the displayTrace command is called.
    """
    def __init__(self, func=None):
        MVCommand.__init__(self, func=func)
        self.flag = self.flag | self.objArgOnly
    

    def onAddCmdToViewer(self):
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('computeTrace'):
            self.vf.loadCommand("traceCommands", 'computeTrace',
                                "Pmv", topCommand = 0)
            
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('displayTrace'):
            self.vf.loadCommand("traceCommands", 'displayTrace',
                                'Pmv', topCommand = 0)



    def __call__(self, nodes, traceName='CATrace', shape2D=None,
                 frontCap=True, endCap=True, display=True, **kw):
        """None <- extrudeTrace(nodes, traceName='CATrace', shape2D=None,
                            frontCap=1, endCap=1, display=1, **kw)
        \nRequired Arguments:\n
            nodes --- any set of MolKit nodes describing molecular components.
        \nOptional Arguments:\n
            traceName --- string representing the name of the trace to be represented
                   the default value is 'CATrace'.
            \nshape2D  --- instance of a DejaVu.Shape class describing the shape 2D
                   to be extruded along the path3D of the selected trace.
                   By default a Circle2D will be extruded
            \nfrontCap --- when set to True a cap is added to all the front of the
                   extruded geometry created to represent the selected trace.
            \nendCap --- when set to True a cap is added to all the end of the extruded
                   geometry representing the selected trace.
            \ndisplay --- when set to True the displayTrace command is called.
        """
        nodes = self.vf.expandNodes(nodes)
        if not nodes:
            return "ERROR"
        kw['shape2D'] = shape2D
        kw['display'] = display
        kw['traceName'] = traceName
        kw['frontCap'] = frontCap
        kw['endCap'] = endCap
        if type(nodes) is StringType:
            self.nodeLogString = "'" + nodes +"'"
        apply(self.doitWrapper, (nodes,), kw)


    def doit(self, nodes, traceName='CATrace', shape2D=None, frontCap=True,
             endCap=True, display=True):

        if shape2D is None:
            shape2D = Circle2D(radius=0.1)
        molecules, atomsSet = self.vf.getNodesByMolecule(nodes, Atom)
        self.shape = shape2D
        arrowf = 0
        for mol, atoms in map(None, molecules, atomsSet):
            chains = atoms.findType(Chain).uniq()
            gc = mol.geomContainer
            for chain in chains:
                # Cannot get the trace thing id no trace has been computed.
                if not hasattr(chain, 'trace'):
                    continue
                elif not chain.trace.has_key(traceName) or \
                     chain.trace[traceName] is None:
                    continue

                name = traceName + chain.id
                trace = chain.trace[traceName]
                trace.exElt = ExtrudeSSElt(trace, shape2D, cap1=frontCap,
                                           cap2=endCap, arrow=arrowf)
                resfaces, resfacesDict = trace.exElt.getExtrudeResidues(trace.residues)
                g = mol.geomContainer.geoms[name]
                g.Set(vertices=trace.exElt.vertices,
                      faces=resfaces, vnormals=trace.exElt.vnormals,
                      redo=0, tagModified=False)
        if display:
            self.vf.displayTrace(nodes, traceName, negate=False,
                                 setupUndo=True, topCommand=False, redraw=True)
            
    def getAvailableTrace(self):
        mols = self.vf.getSelection().top.uniq()
        tracesName = []
        for m in mols:
            if not m.geomContainer.geoms.has_key('trace'): continue
            names = map(lambda x: x.name,
                        m.geomContainer.geoms['trace'].children)
            for n in names:
                if not n in tracesName: tracesName.append(n)
        return tracesName


    def buildFormDescr(self, formName):
        if formName == 'geomChooser':
            nbchordEntryVar = Tkinter.StringVar()
            idf = InputFormDescr(title ="Choose a shape :")
            idf.append({'name':'traceName',
                        'widgetType':Pmw.ComboBox,
                        'tooltip':'Choose a trace to extrude.',
                        'defaultValue':self.traceNames[0],
                        'wcfg':{'label_text':'Choose a trace: ',
                                'labelpos':'w',
                                'scrolledlist_items': self.traceNames,
                                },
                        'gridcfg':{'sticky':'w'}})

            entries = ['circle','rectangle','ellipse', 'square','triangle']

            idf.append({'name':'shape',
                        'widgetType':Pmw.ComboBox,
                        'tooltip':'Choose a shape2D to be extruded.',
                        'defaultValue':entries[0],
                        'wcfg':{'label_text':'Choose a shape',
                                'labelpos':'w',
                                'scrolledlist_items':entries},
                        'gridcfg':{'sticky':'w'}
                        })
            
        else:
            initRadius = 0.1
            radiusWidgetDescr = {'name': 'radius',
                                 'widgetType':ExtendedSliderWidget,
                                 'wcfg':{'label': 'Radius',
                                         'minval':0.05,'maxval':3.0 ,
                                         'init':initRadius,
                                         'labelsCursorFormat':'%1.2f',
                                         'sliderType':'float',
                                         'entrywcfg':{'width':4},
                                         'entrypackcfg':{'side':'right'}},
                                 'gridcfg':{'columnspan':2,'sticky':'we'}
                                 }
            initWidth = 1.2
            widthWidgetDescr =  {'name': 'width',
                                 'widgetType':ExtendedSliderWidget,
                                 'wcfg':{'label': 'Width',
                                         'minval':0.05,'maxval':3.0 ,
                                         'init':initWidth,
                                         'labelsCursorFormat':'%1.2f',
                                         'sliderType':'float',
                                         'entrywcfg':{'width':4},
                                         'entrypackcfg':{'side':'right'}},
                                 'gridcfg':{'columnspan':2,'sticky':'we'}
                                 }
            initHeight = 0.2
            heightWidgetDescr = {'name': 'height',
                                 'widgetType':ExtendedSliderWidget,
                                 'wcfg':{'label': 'Height',
                                         'minval':0.05,'maxval':3.0 ,
                                         'init':initHeight,
                                         'labelsCursorFormat':'%1.2f',
                                         'sliderType':'float' ,
                                         'entrywcfg':{'width':4},
                                         'entrypackcfg':{'side':'right'}},
                                 'gridcfg':{'columnspan':2,'sticky':'we'}
                             }
            initSide = 1.0
            sideWidgetDescr = {'name': 'sidelength',
                               'widgetType':ExtendedSliderWidget,
                               'wcfg':{'label': 'Length of side:',
                                       'minval':0.05,'maxval':3.0 ,
                                       'init':initSide,
                                       'labelsCursorFormat':'%1.2f',
                                       'sliderType':'float',
                                       'entrywcfg':{'width':4},
                                       'entrypackcfg':{'side':'right'}},
                               'gridcfg':{'columnspan':2,'sticky':'we'}
                               }
            
            frontCapWidgetDescr = {'name':'frontcap',
                                   'widgetType':Tkinter.Checkbutton,
                                   'tooltip':'when set to 1 a cap is added \nat the front',
                                   'defaultValue':1,
                                   'wcfg':{'text':'front cap',
                                           'variable': Tkinter.IntVar()},
                                   'gridcfg':{'sticky':'we'}}
            endCapWidgetDescr = {'name':'endcap',
                                 'widgetType':Tkinter.Checkbutton,
                                 'defaultValue':1,
                                 'tooltip':"""when set to 1 a cap is added
                                 at the end""",
                                 'wcfg':{'text':'end cap ',
                                         'variable': Tkinter.IntVar()},
                                 'gridcfg':{'sticky':'we','row':-1}}
            

            if formName == 'rectangle':
                idf = InputFormDescr(title ="Rectangle size :")
                idf.append(widthWidgetDescr)
                initHeight = 0.4
                idf.append(heightWidgetDescr)

            elif formName == 'circle':
                idf = InputFormDescr(title="Circle size :")
                idf.append(radiusWidgetDescr)

            elif formName == 'ellipse':
                idf = InputFormDescr(title="Ellipse size")
                idf.append( {'name': 'grand',
                             'widgetType':ExtendedSliderWidget,
                             'wcfg':{'label': 'demiGrandAxis',
                                     'minval':0.05,'maxval':3.0 ,
                                     'init':0.5,
                                     'labelsCursorFormat':'%1.2f',
                                     'sliderType':'float',
                                     'entrywcfg':{'width':4},
                                     'entrypackcfg':{'side':'right'}},
                             'gridcfg':{'columnspan':2,'sticky':'we'}
                             })
                idf.append( {'name': 'small',
                             'widgetType':ExtendedSliderWidget,
                             'wcfg':{'label': 'demiSmallAxis',
                                     'minval':0.05,'maxval':3.0 ,
                                     'init':0.2,
                                     'labelsCursorFormat':'%1.2f',
                                     'sliderType':'float',
                                     'entrywcfg':{'width':4},
                                     'entrypackcfg':{'side':'right'}},
                             'gridcfg':{'columnspan':2,'sticky':'we'}
                             })
            elif formName == 'square':
                idf = InputFormDescr(title="Square size :")
                idf.append(sideWidgetDescr)

            elif formName == 'triangle':
                idf = InputFormDescr(title="Triangle size :")
                idf.append(sideWidgetDescr)
                
                
            # These widgets are present in everyInputForm.
            idf.append(frontCapWidgetDescr)
            idf.append(endCapWidgetDescr)
        return idf

    def guiCallback(self):
        from ViewerFramework.drawShape import DrawShape
        self.traceNames = self.getAvailableTrace()
        if not self.traceNames : return
        if self.cmdForms.has_key('geomChooser'):
            form = self.cmdForms['geomChooser']
            combo = form.descr.entryByName['traceName']['widget']
            if self.traceNames != combo.get():
                combo.setlist(self.traceNames)

        typeshape = self.showForm('geomChooser')
        
        if typeshape == {} or typeshape['shape'] == []: return
        traceName = typeshape['traceName'][0]
        if not traceName or traceName == " ":
            return
            
        # Shape is a Rectangle
        if typeshape['shape'][0]=='rectangle':
            val = self.showForm('rectangle')
            if val:
                shape2D = Rectangle2D(width = val['width'],
                                      height = val['height'],
                                      vertDup=1)
                frontCap, endCap = int(val['frontcap']),int(val['endcap'])

        # Shape is a Circle:
        elif typeshape['shape'][0]=='circle':
            
            val = self.showForm('circle')
            if val:
                shape2D = Circle2D(radius=val['radius'])
                frontCap, endCap = val['frontcap'],val['endcap']

        # Shape is an Ellipse
        elif typeshape['shape'][0]=='ellipse':
            val = self.showForm('ellipse')
            if val:
                shape2D = Ellipse2D(demiGrandAxis= val['grand'],
                                  demiSmallAxis=val['small'])
                frontCap, endCap = val['frontcap'],val['endcap']
                
        # Shape is a Square:
        elif typeshape['shape'][0]=='square':
            val = self.showForm('square')
            if val:
                shape2D = Square2D(side=val['sidelength'], vertDup=1)
                frontCap, endCap = val['frontcap'],val['endcap']

        # Shape is a Triangle:
        elif typeshape['shape'][0]=='triangle':
            val = self.showForm('triangle')
            if val:
                shape2D = Triangle2D(side=val['sidelength'], vertDup=1)
                frontCap, endCap = val['frontcap'], val['endcap']

        else: return

        if val:
            self.doitWrapper(self.vf.getSelection(),traceName=traceName,
                             shape2D=shape2D,
                             frontCap=frontCap, endCap=endCap,
                             redraw=0)
        else: return


class DisplayTraceCommand(DisplayCommand):
    """This command allows the user to display, undisplay or display only the current selection using the extruded trace representation of the given
    traceName.
    \nPackage : Pmv
    \nModule  : traceCommands
    \nClass   : DisplayTraceCommand
    \nCommand : displayTrace
    \nkeywords: display trace CA...
    \nSynopsis:\n
        None <- displayTrace(nodes, traceName, negate=0, only=0, **kw)
    \nRequired Arguments:\n    
        nodes --- any set of MolKit nodes describing molecular components.
    \nOptional Arguments:\n   
        traceName --- string representing the extruded trace to be displayed,
                    undisplayed or displayed only
        \nnegate --- flag when set to 1 undisplay the trace corresponding to
                    the current selection
        \nonly --- flag when set to 1 the part of the trace geometry
                    corresponding to the current selection will be displayed
                    only.
     """
    def onAddCmdToViewer(self):
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('computeTrace'):
            self.vf.loadCommand("traceCommands", 'computeTrace',
                                "Pmv", topCommand = 0)

        #if self.vf.hasGui and
        if not self.vf.commands.has_key('extrudeTrace'):
            self.vf.loadCommand("traceCommands", 'extrudeTrace',
                                "Pmv", topCommand = 0)
            
    def setupUndoBefore(self, nodes, traceName='CATrace', only=False,
                        negate=False, setScale=True):
        if len(nodes)==0: return
        kw = {'redraw':1}
        kw['traceName']=traceName
        geomSet=[]
        for mol in self.vf.Mols:
            gc = mol.geomContainer
            for chain in mol.chains:
                if not hasattr(chain, 'trace'): continue
                if not chain.trace.has_key(traceName): continue
                if not hasattr(chain.trace[traceName], 'exElt'):
                    continue
                name = "%s%s"%(traceName, chain.id)
                geomSet = geomSet + gc.atoms[name]

        if len(geomSet) == 0:
            # The undo of a display command is undisplay what you just
            # displayed if nothing was displayed before.
            kw['negate'] = True
            self.addUndoCall( (nodes,), kw, self.name)
        else:
            # The undo of a display command is to display ONLY what was
            # displayed before, if something was already displayed
            kw['only'] = True
            self.addUndoCall( (geomSet,), kw, self.name)

    def doit(self, nodes, traceName='CATrace', only=False, negate=False ):
        """ displays the secondary structure for the selected treenodes """

        ###############################################################
        def drawResidues(trace, traceName, res, only, negate):
            mol = trace.chain.parent
	    name = '%s%s'%(traceName, trace.chain.id)
            set = mol.geomContainer.atoms[name]
            if negate :
                set =  set - res

            ##if only, replace displayed set with current atms 
            else:
                if only:
                    set = res
                else:
                    set = res.union(set)
            ##now, update the geometries:
            # draw residues' secondary strucuture
	    if len(set)==0:
		    mol.geomContainer.geoms[name].Set(visible=0,
                                                      tagModified=False)
                    mol.geomContainer.atoms[name] = set
                    return

            #the rest is done only if there are some residues           
            g = mol.geomContainer.geoms[name]
            mol.geomContainer.atoms[name] = set
            
            #resfaces = catrace.getExtrudeResidues(set)
            resfaces, resfacesDict = trace.exElt.getExtrudeResidues(set)
	    col = mol.geomContainer.getGeomColor(name)
            g.Set(faces=resfaces, vnormals=trace.exElt.vnormals,
                  visible=1, materials=col, tagModified=False)

        ###############################################################

        molecules, residueSets = self.vf.getNodesByMolecule(nodes, Residue)
        for mol,residues in map(None,molecules, residueSets):
            for chain in mol.chains:
                if not hasattr(chain, 'trace'): continue
                if not chain.trace.has_key(traceName):
                    continue
                if not hasattr(chain.trace[traceName], 'exElt'):
                    continue
                trace = chain.trace[traceName]
                res = residues.get(lambda x, tr = trace:
                                   x in tr.residues)
                if not res:
                    res = ResidueSet()
                drawResidues(trace, traceName,res, only, negate)


    def buildFormDescr(self, formName):
        if formName == 'displayTrace':
            idf = InputFormDescr(title='Display Extruded Trace')
            idf.append({'name':'display',
                        'widgetType':Pmw.RadioSelect,
                        'listtext':['display','display only', 'undisplay'],
                        'defaultValue':'display',
                        'wcfg':{'orient':'horizontal',
                                'buttontype':'radiobutton'},
                        'gridcfg':{'sticky': 'we','columnspan':3}})

            idf.append({'name':'traceName',
                        'widgetType':Pmw.ComboBox,
                        'tooltip':'Choose a trace to extrude.',
                        'defaultValue':self.traceNames[0],
                        'wcfg':{'label_text':'Choose a trace: ',
                                'labelpos':'w',
                                'scrolledlist_items': self.traceNames,
                                },
                        'gridcfg':{'sticky':'w','columnspan':2}})
            return idf

    def guiCallback(self):
        self.traceNames = self.vf.extrudeTrace.getAvailableTrace()
        if not self.traceNames: return
        if self.cmdForms.has_key('displayTrace'):
            form = self.cmdForms['displayTrace']
            combo = form.descr.entryByName['traceName']['widget']
            if self.traceNames != combo.get():
                combo.setlist(self.traceNames)

        val = self.showForm('displayTrace')
        if not val: return
        display = val['display']
        del val['display']
        if display == 'undisplay':
            val['negate'] = 1
            val['only'] = 0
        elif display == 'display only':
            val['negate'] = 0
            val['only'] = 1
        elif display == 'display':
            val['negate'] = 0
            val['only'] = 0
        val['traceName'] = val['traceName'][0]
        if not val['traceName']: return
        val['redraw']=1

        apply(self.doitWrapper, (self.vf.getSelection(),), val)
        
    def __call__(self, nodes, traceName='CATrace', only=False,
                 negate=False, **kw):
        """None <- displayTrace(nodes, traceName, negate=False, only=False, **kw)
        \nRequired Arguments:\n
            nodes --- any set of MolKit nodes describing molecular components.
        \nOptional Arguments:\n
            traceName --- string representing the extruded trace to be displayed,
                    undisplayed or displayed only
            \nnegate --- flag when set to True undisplay the trace corresponding to
                    the current selection
            \nonly --- flag when set to True the part of the trace geometry
                    corresponding to the current selection will be displayed
                    only.
        """
        kw['only'] = only
        kw['negate'] = negate
        kw['traceName'] = traceName
        kw['redraw'] = True
        if type(nodes) is StringType:
            self.nodeLogString = "'" + nodes +"'"
        apply ( self.doitWrapper, (nodes,), kw )

class CustomTraceCommand(MVCommand):
    """This command computes and extrudes Trace 
        \nPackage : Pmv
        \nModule  : traceCommands
        \nClass   : CustomTraceCommand
        \nCommand : customTrace
        \nkeywords: custom trace
        \nSynopsis:\n
        None<---customTrace(nodes,traceName='CATrace',shape2D=None,frontCap=1, endCap=1,ctlAtmName='CA',torsAtmName='O',nbchords=4,display=1,**kw)
        \nRequired Arguments:\n
            nodes --- TreeNodeSet holding the current selection
        \nOptional Arguments:\n:
            traceName --- string representing the name of the computed trace.
                     default 'CATrace'
            \nctlAtmName --- name of the atom to be used for control (defaul='CA')
            \ntorsAtmName --- name of the atom to be used to control the torsion.
                     default='O'
            \nnbchords --- number of points per residue. The higher the number the
                     smoother the trace will be. 
            \nshape2D  --- instance of a DejaVu.Shape class describing the shape 2D
                   to be extruded along the path3D of the selected trace.
                   By default a Circle2D will be extruded
            \nfrontCap --- when set to True a cap is added to all the front of the
                   extruded geometry created to represent the selected trace.
            \nendCap --- when set to True a cap is added to all the end of the extruded
                   geometry representing the selected trace.
            \ndisplay --- when set to True the displayTrace command is called.
    """
    def __init__(self):
        MVCommand.__init__(self)
        self.flag = self.flag | self.objArgOnly
        self.flag = self.flag | self.negateKw

    def onAddCmdToViewer(self):
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('computeTrace'):
            self.vf.loadCommand("traceCommands",
                                "computeTrace", "Pmv",
                                topCommand = 0)
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('extrudeTrace'):
            self.vf.loadCommand("traceCommands",
                                "extrudeTrace", "Pmv",
                                topCommand = 0)
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('displayTrace'):
            self.vf.loadCommand("traceCommands",
                                "displayTrace", "Pmv",topCommand = 0)
    def buildFormDescr(self, formName):                            
        if formName == 'CustomTraceForm':
            idf = InputFormDescr('Custom Trace')
            idf.append({'name':'traceName',
                        'widgetType':Pmw.ComboBox,
                        'tooltip':'Create a new trace by typing a new trace \n\
name in the entry of the combobox. \nHit the Enter key to add it to the list \
of trace name. \nYou can also choose from the existing list of trace names.\n\
To see the list click on the down arrow.',
                        'defaultValue':self.traceNames[0],
                        'wcfg':{'label_text':'Choose a trace: ',
                                'labelpos':'w',
                                'scrolledlist_items': self.traceNames,
                                },
                        'gridcfg':{'sticky':'w','columnspan':2}})

            idf.append({'name':'ctlAtmName',
                        'widgetType':Pmw.EntryField,
                        'tooltip':'String representing the name of the atom \n\
to be used as control atom. Specify only one atom name.',
                        'wcfg':{'label_text':'Control atom name:',
                                'labelpos':'w', 'entry_width':4,
                                'value':'CA'},
                        'gridcfg':{'sticky':'w'}})
            
            idf.append({'name':'torsAtmName',
                        'widgetType':Pmw.EntryField,
                        'tooltip':'String representing the name of the atom \n\
to be used to control the torsion. Specify only one atom name.',
                        'wcfg':{'label_text':'Torsion atom name:',
                                'labelpos':'w', 'entry_width':4,
                                'value':'O'},
                        'gridcfg':{'sticky':'w'}})


            idf.append( {'name': 'nbchords',
                         'widgetType':ExtendedSliderWidget,
                         'type':int,
                         'tooltip':'Specifies the number of points per \
residues.\n The higher the number the smoother the trace will be.',
                        'wcfg':{'label': 'nb points per residues',
                                 'minval':4,'maxval':15,
                                 'incr': 1, 'init':4,
                                 'labelsCursorFormat':'%d',
                                 'sliderType':'int'
                                 },
                         'gridcfg':{'sticky':'w', 'columnspan':2},
                         })

           
            nbchordEntryVar = Tkinter.StringVar()
            entries = ['circle','rectangle','ellipse', 'square','triangle']

            idf.append({'name':'shape',
                        'widgetType':Pmw.ComboBox,
                        'tooltip':'Choose a shape2D to be extruded.',
                        'defaultValue':entries[0],
                        'wcfg':{'label_text':'Choose a shape',
                                'labelpos':'w',
                                'scrolledlist_items':entries},
                        'gridcfg':{'sticky':'w'}
                        })
            
        else:
            initRadius = 0.1
            radiusWidgetDescr = {'name': 'radius',
                                 'widgetType':ExtendedSliderWidget,
                                 'wcfg':{'label': 'Radius',
                                         'minval':0.05,'maxval':3.0 ,
                                         'init':initRadius,
                                         'labelsCursorFormat':'%1.2f',
                                         'sliderType':'float',
                                         'entrywcfg':{'width':4},
                                         'entrypackcfg':{'side':'right'}},
                                 'gridcfg':{'columnspan':2,'sticky':'we'}
                                 }
            initWidth = 1.2
            widthWidgetDescr =  {'name': 'width',
                                 'widgetType':ExtendedSliderWidget,
                                 'wcfg':{'label': 'Width',
                                         'minval':0.05,'maxval':3.0 ,
                                         'init':initWidth,
                                         'labelsCursorFormat':'%1.2f',
                                         'sliderType':'float',
                                         'entrywcfg':{'width':4},
                                         'entrypackcfg':{'side':'right'}},
                                 'gridcfg':{'columnspan':2,'sticky':'we'}
                                 }
            initHeight = 0.2
            heightWidgetDescr = {'name': 'height',
                                 'widgetType':ExtendedSliderWidget,
                                 'wcfg':{'label': 'Height',
                                         'minval':0.05,'maxval':3.0 ,
                                         'init':initHeight,
                                         'labelsCursorFormat':'%1.2f',
                                         'sliderType':'float' ,
                                         'entrywcfg':{'width':4},
                                         'entrypackcfg':{'side':'right'}},
                                 'gridcfg':{'columnspan':2,'sticky':'we'}
                             }
            initSide = 1.0
            sideWidgetDescr = {'name': 'sidelength',
                               'widgetType':ExtendedSliderWidget,
                               'wcfg':{'label': 'Length of side:',
                                       'minval':0.05,'maxval':3.0 ,
                                       'init':initSide,
                                       'labelsCursorFormat':'%1.2f',
                                       'sliderType':'float',
                                       'entrywcfg':{'width':4},
                                       'entrypackcfg':{'side':'right'}},
                               'gridcfg':{'columnspan':2,'sticky':'we'}
                               }
            
            frontCapWidgetDescr = {'name':'frontcap',
                                   'widgetType':Tkinter.Checkbutton,
                                   'tooltip':'when set to 1 a cap is added \nat the front',
                                   'defaultValue':1,
                                   'wcfg':{'text':'front cap',
                                           'variable': Tkinter.IntVar()},
                                   'gridcfg':{'sticky':'we'}}
            endCapWidgetDescr = {'name':'endcap',
                                 'widgetType':Tkinter.Checkbutton,
                                 'defaultValue':1,
                                 'tooltip':"""when set to 1 a cap is added
                                 at the end""",
                                 'wcfg':{'text':'end cap ',
                                         'variable': Tkinter.IntVar()},
                                 'gridcfg':{'sticky':'we','row':-1}}
            

            if formName == 'rectangle':
                idf = InputFormDescr(title ="Rectangle size :")
                idf.append(widthWidgetDescr)
                initHeight = 0.4
                idf.append(heightWidgetDescr)

            elif formName == 'circle':
                idf = InputFormDescr(title="Circle size :")
                idf.append(radiusWidgetDescr)

            elif formName == 'ellipse':
                idf = InputFormDescr(title="Ellipse size")
                idf.append( {'name': 'grand',
                             'widgetType':ExtendedSliderWidget,
                             'wcfg':{'label': 'demiGrandAxis',
                                     'minval':0.05,'maxval':3.0 ,
                                     'init':0.5,
                                     'labelsCursorFormat':'%1.2f',
                                     'sliderType':'float',
                                     'entrywcfg':{'width':4},
                                     'entrypackcfg':{'side':'right'}},
                             'gridcfg':{'columnspan':2,'sticky':'we'}
                             })
                idf.append( {'name': 'small',
                             'widgetType':ExtendedSliderWidget,
                             'wcfg':{'label': 'demiSmallAxis',
                                     'minval':0.05,'maxval':3.0 ,
                                     'init':0.2,
                                     'labelsCursorFormat':'%1.2f',
                                     'sliderType':'float',
                                     'entrywcfg':{'width':4},
                                     'entrypackcfg':{'side':'right'}},
                             'gridcfg':{'columnspan':2,'sticky':'we'}
                             })
            elif formName == 'square':
                idf = InputFormDescr(title="Square size :")
                idf.append(sideWidgetDescr)

            elif formName == 'triangle':
                idf = InputFormDescr(title="Triangle size :")
                idf.append(sideWidgetDescr)
                
                
            # These widgets are present in everyInputForm.
            idf.append(frontCapWidgetDescr)
            idf.append(endCapWidgetDescr)
        return idf
    
    

    def guiCallback(self):
        self.traceNames = self.vf.extrudeTrace.getAvailableTrace()
        if not self.traceNames:self.traceNames = ['CATrace',]
        if self.cmdForms.has_key('CustomTraceForm'):
            form = self.cmdForms['CustomTraceForm']
            combo = form.descr.entryByName['traceName']['widget']
            if self.traceNames != combo.get():
                combo.setlist(self.traceNames)

        typeshape = self.showForm('CustomTraceForm')
        if not typeshape: return
        if len(typeshape['traceName']) == 0:
            return
        typeshape['traceName'] = typeshape['traceName'][0]
        if not typeshape['ctlAtmName'] or not typeshape['torsAtmName']: return
        typeshape['redraw']=0
        self.vf.computeTrace(self.vf.getSelection(),traceName=typeshape['traceName'],ctlAtmName=typeshape['ctlAtmName'],torsAtmName=typeshape['torsAtmName'],nbchords=typeshape['nbchords'])   

        from ViewerFramework.drawShape import DrawShape
       
        # Shape is a Rectangle
        if typeshape['shape'][0]=='rectangle':
            val = self.showForm('rectangle')
            if val:
                shape2D = Rectangle2D(width = val['width'],
                                      height = val['height'],
                                      vertDup=1)
                frontCap, endCap = int(val['frontcap']),int(val['endcap'])

        # Shape is a Circle:
        elif typeshape['shape'][0]=='circle':
            
            val = self.showForm('circle')
            if val:
                shape2D = Circle2D(radius=val['radius'])
                frontCap, endCap = val['frontcap'],val['endcap']

        # Shape is an Ellipse
        elif typeshape['shape'][0]=='ellipse':
            val = self.showForm('ellipse')
            if val:
                shape2D = Ellipse2D(demiGrandAxis= val['grand'],
                                  demiSmallAxis=val['small'])
                frontCap, endCap = val['frontcap'],val['endcap']
                
        # Shape is a Square:
        elif typeshape['shape'][0]=='square':
            val = self.showForm('square')
            if val:
                shape2D = Square2D(side=val['sidelength'], vertDup=1)
                frontCap, endCap = val['frontcap'],val['endcap']

        # Shape is a Triangle:
        elif typeshape['shape'][0]=='triangle':
            val = self.showForm('triangle')
            if val:
                shape2D = Triangle2D(side=val['sidelength'], vertDup=1)
                frontCap, endCap = val['frontcap'], val['endcap']

        else: return
        
        if val: 
            self.vf.extrudeTrace(self.vf.getSelection(),traceName=typeshape['traceName'],
                             shape2D=shape2D,
                             frontCap=frontCap, endCap=endCap,
                             redraw=0)
        else: return

    def __call__(self, nodes,traceName='CATrace',shape2D=None,frontCap=1, endCap=1,ctlAtmName='CA',torsAtmName='O',nbchords=4,display=1,**kw):
        """None<---customTrace(nodes,traceName='CATrace',shape2D=None,frontCap=1, endCap=1,ctlAtmName='CA',torsAtmName='O',nbchords=4,display=1,**kw)
        \nRequired Arguments:\n
            nodes --- TreeNodeSet holding the current selection
        \nOptional Arguments:\n
            traceName --- string representing the name of the computed trace.
                     default 'CATrace'
            \nctlAtmName --- name of the atom to be used for control (defaul='CA')
            \ntorsAtmName --- name of the atom to be used to control the torsion.
                     default='O'
            \nnbchords --- number of points per residue. The higher the number the
                     smoother the trace will be. 
            \nshape2D  --- instance of a DejaVu.Shape class describing the shape 2D
                   to be extruded along the path3D of the selected trace.
                   By default a Circle2D will be extruded
            \nfrontCap --- when set to True a cap is added to all the front of the
                   extruded geometry created to represent the selected trace.
            \nendCap --- when set to True a cap is added to all the end of the extruded
                   geometry representing the selected trace.
            \ndisplay --- when set to True the displayTrace command is called.             
        """
        nodes = self.vf.expandNodes(nodes) 
        if not nodes:
            return "ERROR"
        kw['traceName']=traceName
        kw['ctlAtmName']=ctlAtmName
        kw['torsAtmName']=torsAtmName
        kw['nbchords']=nbchords
        kw['frontCap']=frontCap
        kw['endCap']=endCap
        kw['display']=display
        kw['shape2D']=shape2D
        if type(nodes) is StringType:
            self.nodeLogString = "'" + nodes +"'"
        apply(self.doitWrapper, (nodes,), kw)
        
    def doit(self, nodes,**kw):     
        nkw={}
        if kw!={}:
            if kw['display']==0:
                nkw['negate']=1
                apply(self.vf.displayTrace,(nodes,),nkw)
                return

            elif kw['display']==1:
                if kw.has_key('negate'):
                    if kw['negate']==1:
                        nkw['negate']=1
                        apply(self.vf.displayTrace,(nodes,),nkw)
                        return    
        self.vf.computeTrace(nodes,traceName=kw['traceName'],ctlAtmName=kw['ctlAtmName'],torsAtmName=kw['torsAtmName'],nbchords=kw['nbchords'])
        self.vf.extrudeTrace(nodes,traceName=kw['traceName'],shape2D=kw['shape2D'],frontCap=kw['frontCap'], endCap=kw['endCap'],display = kw['display']) 
        
    
class ComputeExtrudeTraceCommand(MVCommand):
    """This command computes and Extrudes Trace with default arguements
    \nPackage : Pmv
    \nModule  : traceCommands
    \nClass   : ComputeExtrudeTraceCommand
    \nCommand : computeExtrudeTrace
    \nkeywords: computeExtrude trace
    \nSynopsis:\n
        None<---computeExtrudeTrace(nodes, only=False, negate=False, **kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection
    \nOptional Arguments:\n
        only --- flag when set to 1 only the current selection
                  will be displayed
        \nnegate ---  flag when set to 1 undisplay the current selection    
    """
    def __init__(self):
        MVCommand.__init__(self)
        self.flag = self.flag | self.objArgOnly
        self.flag = self.flag | self.negateKw



    def onAddCmdToViewer(self):
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('computeTrace'):
            self.vf.loadCommand("traceCommands",
                                "computeTrace", "Pmv",
                                topCommand = 0)
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('extrudeTrace'):
            self.vf.loadCommand("traceCommands",
                                "extrudeTrace", "Pmv",
                                topCommand = 0)
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('displayTrace'):
            self.vf.loadCommand("traceCommands",
                                "displayTrace", "Pmv",
                                topCommand = 0)

    def __call__(self, nodes, only=False, negate=False,**kw):
        """None <- computeExtrudeTrace(nodes, only=False, negate=False, **kw)
        \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection
        \nOptional Arguments:\n
        only --- flag when set to 1 only the current selection
                  will be displayed
        \nnegate ---  flag when set to 1 undisplay the current selection
        """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        
        if not kw.has_key('redraw'): kw['redraw']=1
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return "ERROR"
        kw['only']=only
        kw['negate']=negate
        apply(self.doitWrapper, (nodes,), kw)

    def doit(self, nodes, **kw):
        if kw!={}:
            if kw['negate']==1:
                apply(self.vf.displayTrace,(nodes,), kw)
                return
        apply(self.vf.computeTrace,(nodes,), {'topCommand':False})
        kw['topCommand'] = 0
        apply(self.vf.extrudeTrace,(nodes,),{})        
        



computeTraceGuiDescr = {'widgetType':'Menu', 'menuBarName':'Compute',
                          'menuButtonName':'Compute CA Trace',
                          'separatorAbove':1}

ComputeTraceGUI = CommandGUI()
ComputeTraceGUI.addMenuCommand('menuRoot', 'Compute', 'Compute Trace',
                                 cascadeName = 'Trace')

extrudeTraceGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                        'menuButtonName':'Compute',
                        'menuEntryLabel':'Extrude Trace'}

ExtrudeTraceGUI = CommandGUI()
ExtrudeTraceGUI.addMenuCommand('menuRoot', 'Compute', 'Extrude Trace',
                             cascadeName = 'Trace')

computeExtrudeTraceGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                  'menuButtonName':'ComputeExtrude CA Trace',
                  'menuEntryLabel':'ComputeExtrude Trace'}
ComputeExtrudeTraceGUI = CommandGUI()
ComputeExtrudeTraceGUI.addMenuCommand('menuRoot','Compute','ComputeExtrude Trace',cascadeName ='Trace')

customTraceGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                  'menuButtonName':'Custom CA Trace',
                  'menuEntryLabel':'Custom Trace'}
CustomTraceGUI = CommandGUI()
CustomTraceGUI.addMenuCommand('menuRoot','Compute','Custom Trace',cascadeName ='Trace')

displayTraceGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                          'menuButtonName':'Display',
                          'menuEntryLabel':'Display Trace'}

DisplayTraceGUI = CommandGUI()
DisplayTraceGUI.addMenuCommand('menuRoot', 'Display','Trace')



commandList = [
    {'name': 'computeTrace','cmd':ComputeTraceCommand(),
     'gui':ComputeTraceGUI},
    {'name': 'extrudeTrace','cmd': ExtrudeTraceCommand(),
     'gui':ExtrudeTraceGUI},
    {'name': 'displayTrace', 'cmd': DisplayTraceCommand(),
     'gui':DisplayTraceGUI},
    {'name': 'computeExtrudeTrace', 'cmd': ComputeExtrudeTraceCommand(),
    'gui':ComputeExtrudeTraceGUI},
    {'name': 'customTrace', 'cmd': CustomTraceCommand(),
    'gui':CustomTraceGUI}
    ]

def initModule(viewer):
    """ initializes commands for secondary structure and extrusion.  Also
    imports the commands for Secondary Structure specific coloring, and
    initializes these commands also. """

    for dict in commandList:
	viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
