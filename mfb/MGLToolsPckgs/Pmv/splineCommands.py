#############################################################################
#
# Author: Sophie COON, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
#$Header: /opt/cvs/python/packages/share1.5/Pmv/splineCommands.py,v 1.54 2009/11/10 00:11:23 annao Exp $
#
#$Id: splineCommands.py,v 1.54 2009/11/10 00:11:23 annao Exp $
#
#

from mglutil.util.misc import ensureFontCase

from MolKit.molecule import Atom,AtomSet
from MolKit.protein import Protein,Residue, Chain, ProteinSet
from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.stringSelector import StringSelector

from DejaVu.Polylines import Polylines
from DejaVu.IndexedPolylines import IndexedPolylines
from DejaVu.spline import DialASpline
from DejaVu.GleObjects import GleExtrude, GleObject
from DejaVu.Points import Points
from DejaVu.Geom import Geom
from DejaVu.spline import SplineObject
from DejaVu.Shapes import Shape2D, Triangle2D, Circle2D, Rectangle2D,\
     Square2D, Ellipse2D



from Pmv.mvCommand import MVCommand
#from Pmv.selectionCommands import MVStringSelector
from Pmv.displayCommands import DisplayCommand

from ViewerFramework.VFCommand import CommandGUI
##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr

from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser, \
     ExtendedSliderWidget
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
import Tkinter, Pmw, string, types
import numpy.oldnumeric as Numeric

class ComputeSplineCommand(MVCommand):
    """The CompueSplineCommand omplements a set of method to create an DejaVu.splineObject per chain given:a TreeNodeSet,type of control Atoms (atmtype),number of points per control point in the smooth array (nbchords),continuity of the curves (continuity).
    \nPackage : Pmv
    \nModule  : splineCommands
    \nClass   : ComputeSplineCommand
    \nCommand : computeSpline
    \nkeywords: compute spline
    \nSynopsis:\nNone <- computeSpline(nodes, atmtype='CA', nbchords=4,
                              interp='interpolation'
                              continuity=2, closedSpline=0, **kw)
    \nRequired Arguments:\n
        nodes --- self.getSelection()
    \nOptional Arguments:\n
        \natmtype --- specifies the atom type of the control points.
                      the atoms of the current selection of the given
                      atom type are used as the control points.
                      atmtype can be 'CA'(default value) 'CA,N' 'O' etc.... 
                      
        \ncurSel --- Boolean flag to use the atoms in current selection as control
                      points. (default=False)
        \nnbchords --- number of point per control points in the smooth array
        \ninterp --- flag if set to 'interpolation' interpolate the control
                      points.
        \ncontinuity  --- specifies the continuity of the curve.
        \nclosedSpline --- Boolean flag when set to True the spline will be closed (1st atom will be connected to the last atom. (default = False)
        \nsortAtms --- Boolean flag to sort the ctlAtms or not. (default = True)
    """
    def __init__(self, func=None):
        MVCommand.__init__(self, func=func)
        self.flag = self.flag | self.objArgOnly

    def onRemoveObjectFromViewer(self, obj):
        # check if the memory is freed
        for c in obj.chains:
            if hasattr(c, 'spline'):
                delattr(c,'spline')
            else:
                continue
    

    def doit(self, nodes, atmtype="", curSel=False,  nbchords=8,
             interp='interpolation', continuity=2,
             closedSpline=False, sortAtms = True):
        molecules, atomSets = self.vf.getNodesByMolecule(nodes, Atom)
        # Build the query that will be passed to MVStringSelector.
        # args ["molname","chainname", "residuename", "atomname"]
        #args = ["","","",""]
        # Build string that will be passed to 
        # MolKit.stringSelector.StringSelector
        args = ":::"
        # get the CtlPoints for all the molecules loaded in the 
        if not curSel and atmtype:
            #args[3] = atmtype
            args = args + atmtype
            # get the CtlPoints of all the molecules
            #stringAtms = MVStringSelector(self.vf, molecules, args).go()
            stringAtms = StringSelector().select(molecules, args)
            # No atoms found.
            if stringAtms is None or stringAtms[0] is None or len(stringAtms)==0:
                return

        elif not curSel and not atmtype:
            # curSel checkbutton not selected but not atomtype given
            return
        
        
        for mol, atoms in map(None, molecules, atomSets):
            # Get a handle on the molecule geomContainer.
            geomC = mol.geomContainer
            # chainsInSel is the ChainSet of the chain having at least one
            # node in the current selection
            chainsInSel = atoms.findType(Chain).uniq()
            # Loop over the chains in the current selection.
            for chain in chainsInSel:
                atmsInChain = chain.findType(Atom).inter(atoms)
                if curSel == 1:
                    # Only computing the spline per chain.
                    atms = atmsInChain

                else:
                    # get the CtlPoints in the selection.
                    atms = stringAtms[0].inter(atmsInChain)

                # Compute the Spline Object.
                if not atms or not len(atms)>3:
                    # needs to have more than 3 atms to compute a spline.
                    # Could be changed 
                    chain.spline = None
                else:
                    
                    # 1- sort the atoms.
                    if sortAtms:
                        atms.sort()

                    # 2- get there coordinates
                    atmCoords = atms.coords
                    
                    # 3- Create a DejaVu SplineObject.
                    splineName = 'spline' + chain.id
                    splineObject = SplineObject(atmCoords, name=splineName,
                                                nbchords=nbchords,
                                                interp=interp,
                                                continuity=continuity,
                                                closed=closedSpline)

                    if not hasattr(chain, 'spline') \
                       or not chain.spline is None:
                        chain.spline = {splineName:(splineObject, atms)}
                    else:
                        chain.spline[splineName] = (splineObject, atms)
            
                

    def __call__(self, nodes, atmtype="CA", curSel=False, nbchords=8, 
                 interp='interpolation', continuity=2, closedSpline=False,
                 sortAtms=True,  **kw):
        """None <- computeSpline(nodes, atmtype='CA', nbchords=8,
                              interp='interpolation'
                              continuity=2, closedSpline=0, **kw)
        \nRequired Arguments:\n
        nodes  --- self.getSelection()
        \nOptional Arguments:\n
        atmtype  --- specifies the atom type of the control points.
                      the atoms of the current selection of the given
                      atom type are used as the control points.
                      atmtype can be 'CA'(default value) 'CA,N' 'O' etc.... 
                      
        \ncurSel  --- Boolean flag to use the atoms in current selection as control
                      points. (default=False)
        \nnbchords --- number of point per control points in the smooth array
        \ninterp --- flag if set to 'interpolation' interpolate the control
                      points.
        \ncontinuity --- specifies the continuity of the curve.
        \nclosedSpline --- Boolean flag when set to True the spline will be closed (1st atom will be connected to the last atom. (default = False)
        \nsortAtms --- Boolean flag to sort the ctlAtms or not. (default = True)
                   
        """
        kw['redraw'] = 0
        kw['nbchords'] = nbchords
        kw['interp'] = interp
        kw['continuity'] = continuity
        kw['atmtype'] = atmtype
        kw['curSel'] = curSel
        kw['closedSpline'] = closedSpline
        if type(nodes) is types.StringType:
            self.nodeLogString = "'" + nodes +"'"
        expnodes = self.vf.expandNodes(nodes)
        if len(expnodes)==0: return
        apply(self.doitWrapper, (expnodes, ), kw)



class ComputeSplineGUICommand(MVCommand):
    """ The ComputeSplineGUICommand  provides a GUI to the user and calls computeSplineCommand to compute the splineObject. This class also implement a createGeometries method to create the geometrie to represent the splineObject here a IndexedPolylines.
    \nPackage : Pmv
    \nModule  : splineCommands
    \nClass   : ComputeSplineGUICommand
    \nCommand : computeSplineGC
    \nSynopsis:\nNone <- computeSpline(nodes,atmtype='CA',nbchords=4,interp='interpolation',continuity=2,closedSpline=0, **kw)
    \nRequired Arguments:\n
        nodes --- self.getSelection()
    \nOptional Arguments:\n
        \natmtype --- specifies the atom type of the control points.
                      the atoms of the current selection of the given
                      atom type are used as the control points.
                      atmtype can be 'CA'(default value) 'CA,N' 'O' etc.... 
                      
        \ncurSel --- Boolean flag to use the atoms in current selection as control
                      points. (default=False)
        \nnbchords --- number of point per control points in the smooth array
        \ninterp --- flag if set to 'interpolation' interpolate the control
                      points.
        \ncontinuity  --- specifies the continuity of the curve.
        \nclosedSpline --- Boolean flag when set to True the spline will be closed (1st atom will be connected to the last atom. (default = False)
        \nsortAtms --- Boolean flag to sort the ctlAtms or not. (default = True)
   
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func=func)
        self.flag = self.flag | self.objArgOnly

    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('computeSpline'):
            self.vf.loadCommand("splineCommands", 'computeSpline',
                                "Pmv", topCommand = 0)
        #if self.vf .hasGui and \
        if not self.vf.commands.has_key('displaySplineAsLine'):
            self.vf.loadCommand("splineCommands",'displaySplineAsLine','Pmv',
                                topCommand = 0)


    def cursel_cb(self, event = None):
        """ if the use curSel checkbutton is on: the entryFiedl should be
        disabled."""
        if self.cmdForms.has_key('spline'):
            idf = self.cmdForms['spline'].descr
            cbVar =idf.entryByName['curSel']['wcfg']['variable']
            entry = idf.entryByName['atmtype']['widget']

            if cbVar.get() == 1:
                entry._entryFieldEntry.configure(state = Tkinter.DISABLED)
                entry.configure(label_fg = 'darkgray')

            else:
                entry._entryFieldEntry.configure(state = Tkinter.NORMAL)
                entry.configure(label_fg = 'black')
        

    def buildFormDescr(self, formName):
        if formName == 'spline':
            idf = InputFormDescr(title="Compute Spline:")
            nbchordEntryVar = Tkinter.StringVar()
            idf.append({'name':'curSel',
                        'widgetType':Tkinter.Checkbutton,
                        'defaultValue':0,
                        'wcfg':{'text':'Current Selection',
                                'variable':Tkinter.IntVar(),
                               'command':self.cursel_cb},
                        'gridcfg':{'sticky':'we'}})

            # ? maybe a list of checkbox Entryfield to choose the atomType.
            idf.append({'widgetType':Pmw.EntryField,
                        'name':'atmtype',
                        'wcfg':{'labelpos':'w',
                                'label_text':'Enter atom types: ',
                                'validate':None,
                                },
                        'gridcfg':{'sticky':'we','row':-1}})

            # number of points per residue
            idf.append( {'name': 'nbchords',
                         'widgetType':ExtendedSliderWidget,
                         'type':int,
                         'wcfg':{'label': 'nb. Pts Per Residue:  ',
                                 'minval':4,'maxval':15, 'incr': 1, 'init':8,
                                 'labelsCursorFormat':'%d', 'sliderType':'int',
                                 'entrywcfg':{'textvariable':nbchordEntryVar,
                                              'width':4},
                                 'entrypackcfg':{'side':'right'}},
                         'gridcfg':{'sticky':'we'}
                         })
            # Continuity
            idf.append( {'name': 'continuity',
                         'widgetType':ExtendedSliderWidget,
                         'type':int,
                         'wcfg':{'label': 'Continuity',
                                 'minval':0,'maxval':5, 'incr': 1, 'init':2,
                                 'labelsCursorFormat':'%d', 'sliderType':'int',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                         'gridcfg':{'sticky':'we', 'row':-1}
                         })

            idf.append({'name':'closedSpline',
                        'widgetType':Tkinter.Checkbutton,
                        'defaultValue':0,
                        'wcfg':{'text':'Closed Spline       ',
                                'variable':Tkinter.IntVar()},
                        'gridcfg':{'sticky':'we'}})

            idf.append({'name':'sortAtms',
                        'widgetType':Tkinter.Checkbutton,
                        'defaultValue':1,
                        'wcfg':{'text':'Sort control Atoms',
                                'variable':Tkinter.IntVar()},
                        'gridcfg':{'sticky':'we', 'row':-1}})

##          idf.append({'name': 'interp',
##                      'widgetType':Pmw.RadioSelect,
##                      'defaultValue':'interpolation',
##                      'listtext':['interpolation'],#,'approximation'],
##                      'wcfg':{'orient':'horizontal',
##                              'buttontype':'radiobutton'},
##                      'gridcgf':{'columnspan':2,'sticky':'w'}
##                     })

            return idf

    def guiCallback(self):

        nodes = self.vf.getSelection()
        if not nodes: return
        val = self.showForm('spline')
        if val:
            if val['curSel']==0 and \
               (val['atmtype']=='' or val['atmtype']== ' '):
                # if no atmtype given and not cursel checked nothing
                # happens
                return
                                     
            val['redraw']=0
            apply(self.doitWrapper, (nodes,), val)


    def doit(self,nodes, atmtype="", curSel=False,  nbchords=4,
             interp='interpolation', continuity=2,
             closedSpline=False, sortAtms=True):

        self.vf.computeSpline(nodes, atmtype=atmtype, curSel=curSel,
                              nbchords=nbchords,interp= interp,
                              continuity=continuity,
                              closedSpline=closedSpline, sortAtms= sortAtms,
                              topCommand=0)
        
    def __call__(self,nodes, atmtype="CA",curSel=False, nbchords=4, 
                 interp='interpolation', continuity=2, closedSpline=False,
                 sortAtms=True,  **kw):
        """None <- computeSpline(nodes,atmtype,nbchords=4,interp='interpolation',continuity=2,closedSpline=False,**kw)
        \nRequired Arguments:\n
        nodes --- self.getSelection()
    \nOptional Arguments:\n
        \natmtype --- specifies the atom type of the control points.
                      the atoms of the current selection of the given
                      atom type are used as the control points.
                      atmtype can be 'CA'(default value) 'CA,N' 'O' etc.... 
                      
        \ncurSel --- Boolean flag to use the atoms in current selection as control
                      points. (default=False)
        \nnbchords --- number of point per control points in the smooth array
        \ninterp --- flag if set to 'interpolation' interpolate the control
                      points.
        \ncontinuity  --- specifies the continuity of the curve.
        \nclosedSpline --- Boolean flag when set to True the spline will be closed (1st atom will be connected to the last atom. (default = False)
        \nsortAtms --- Boolean flag to sort the ctlAtms or not. (default = True)
        """
        kw['redraw'] = 0
        kw['nbchords'] = nbchords
        kw['interp'] = interp
        kw['continuity'] = continuity
        kw['atmtype'] = atmtype
        kw['curSel'] = curSel
        kw['closedSpline'] = closedSpline
        if type(nodes) is types.StringType:
            self.nodeLogString = "'" + nodes +"'"
        nodes = self.vf.expandNodes(nodes)
        if len(nodes)==0: return
        apply(self.doitWrapper, (nodes, ), kw)

    
class ExtrudeSplineCommand(MVCommand):
    """
    The extrudeSplineCommand implements a set of method to create the
    extrude Geometries DejaVu.GleExtrude resulting of the extrusion of a
    shape2D along a path3D computed by the DejaVu.SplineObject using the GLE
    library.
    \nPackage : Pmv
    \nModule  : splineCommands
    \nClass   : ExtrudeSplineCommand
    \nCommand : extrudeSpline
    \nkeywords: extrude spline
    \nSynopsis:\nNone <- extrudeSpline(nodes, shape2D=None, display=True, **kw)
    \nRequired Arguments:\n
        nodes --- treeNodeSet holding the current selection, or string
                 representing a treeNodeSet.
    \nOptional Arguments:\n
        shape2D --- instance of a DejaVu.Shapes class (Triangle2DDup, Circle2D...)the default shape is a circle2D
        \ncapsFlag --- Boolean flag to add caps at the end of the spline (default=False)
        \ndisplay --- Boolean flag to call or not the displayExtrudedSpline command default value is True.
    """
    def __init__(self, func=None):
        MVCommand.__init__(self, func=func)
        self.flag = self.flag | self.objArgOnly

    def onRemoveObjectFromViewer(self, obj):
        gc = obj.geomContainer
        for c in obj.chains:
            splineName = 'spline'+c.id
            if gc.geoms.has_key(splineName):
                g = gc.geoms[splineName]
                if hasattr(g, 'spline'):
                    delattr(g,'spline')

    def onAddCmdToViewer(self):
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('computeSplineGC'):
            self.vf.loadCommand("splineCommands", 'computeSplineGC',
                                "Pmv", topCommand = 0)
            
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('displayExtrudedSpline'):
            self.vf.loadCommand("splineCommands", 'displayExtrudedSpline',
                                'Pmv', topCommand = 0)

    def createGeometries(self, chain):
        """Method to create the extrude geometry"""
        geomC = chain.parent.geomContainer
        if not hasattr(chain, 'spline') or chain.spline is None:
            return 
        name = "spline"+chain.id
        if geomC.geoms.has_key(name) and geomC.atoms.has_key(name):
            g = geomC.geoms[name]
            if g.spline == chain.spline['spline'+chain.id]:
                return
            else:
                if geomC.VIEWER:
                    geomC.VIEWER.RemoveObject(g)
                else:
                    if g in geomC.masterGeom.children:
                        geomC.masterGeom.children.remove(g)
                del geomC.geoms[name]

        g = GleExtrude(name=name, visible=0)
        
        geomC.geomPickToAtoms[name] = self.pickedVerticesToAtoms
        geomC.atomPropToVertices[name] = self.atomPropToVertices
        geomC.geomPickToBonds[name] = None
        geomC.addGeom(g, parent=geomC.masterGeom, redo=0)
        self.managedGeometries.append(g)
        #geomC.VIEWER.AddObject( g, parent = geomC.masterGeom,
                                #replace=True, redo=0)
        for atm in chain.findType(Atom):
            atm.colors[name] = (1.0, 1.0, 1.0)
            atm.opacities[name] = 1.0

        
    def pickedVerticesToAtoms(self, geom, vertInd):
        """Function called to convert a picked vertex into an atom"""
        # Need to change this if there is a cap or not !
        # this function gets called when a picking or drag select event has
        # happened. It gets called with a geometry and the list of vertex
        # indices of that geometry that have been selected.
        # This function is in charge of turning these indices into an AtomSet
        lshape = self.shape.lenShape
        pickedAtms = AtomSet()
        nbchords = geom.spline[0].nbchords
        lastVertices = geom.spline[2].index(geom.spline[2][-1])
        closed = geom.spline[0].closed
        for v in vertInd:
            # 1- needs to know what is the corresponding index of the picked
            # vertex in the path3D
            splinePts = v/(2*lshape)
            # 2- need to convert that index into an atom indices in the
            # set of
            # atoms used as control points to compute the spline.
            if closed == 0:
                if splinePts>=nbchords/2 and \
                   splinePts <(lastVertices)*nbchords - nbchords/2:
                    # normal points
                    atmIndex = (splinePts-nbchords/2)/nbchords + 1
            
            
                elif splinePts<nbchords/2:
                    atmIndex = 0

                elif splinePts >= (lastVertices)*nbchords - nbchords/2:
                    atmIndex = -1

            elif closed == 1:
                
                lastIndex = (lastVertices)*nbchords - nbchords/2
                if splinePts>=nbchords/2 and \
                   splinePts <lastIndex:
                    # normal points
                    atmIndex = (splinePts-nbchords/2)/nbchords + 1
            
                elif splinePts >= lastIndex and \
                     splinePts < lastIndex + nbchords:
                    atmIndex = -1

                elif splinePts<nbchords/2 or \
                     splinePts >= lastIndex + nbchords:
                    atmIndex = 0
                

            # atoms used as control points to compute the spline.
            atm = geom.spline[1][atmIndex]
            pickedAtms.append(atm)

        # 3- need to return the corresponding atomset.
        return pickedAtms

    def atomPropToVertices(self, geom, atoms, propName, propIndex = None):
        propVect = []
        ctlAtms = geom.spline[2]
        closed = geom.spline[0].closed
        atoms.sort()
        for a in atoms:
            if closed == 0:
                if a==ctlAtms[0] or a == ctlAtms[-1]:
                    if geom.capsFlag == 1:
                        nbchords = geom.spline[0].nbchords/2 + 1
                    else:
                        nbchords = geom.spline[0].nbchords/2

                else:
                    nbchords = geom.spline[0].nbchords
            else:
                nbchords = geom.spline[0].nbchords

            prop = getattr(a, propName)
            
            if not propIndex is None:
                prop = prop[propIndex]
            for n in range(nbchords):
                propVect.append(prop)
        return(propVect)
        

    def __call__(self, nodes, shape2D=None, capsFlag=False, display=True, **kw):
        """None <- extrudeSpline(nodes, shape2D=None, display=True, **kw)
        \nRequired Arguments:\n
        nodes --- treeNodeSet holding the current selection, or string
                 representing a treeNodeSet.
        \nOptional Arguments:\n
        shape2D --- instance of a DejaVu.Shapes class (Triangle2DDup, Circle2D...)the default shape is a circle2D
        \ncapsFlag --- Boolean flag to add caps at the end of the spline (default=False)
        \ndisplay --- Boolean flag to call or not the displayExtrudedSpline command default value is True.
        """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"

        nodes = self.vf.expandNodes(nodes)
        kw['shape2D'] = shape2D
        kw['display'] = display
        kw['capsFlag']=capsFlag
        apply(self.doitWrapper, (nodes,), kw)


    def doit(self, nodes, shape2D=None, capsFlag=False, display=True):
        if shape2D is None:
            shape2D = Circle2D(radius=0.1, firstDup=1)
        molecules, atomsSet = self.vf.getNodesByMolecule(nodes, Atom)
        self.shape = shape2D
        for mol, atoms in map(None, molecules, atomsSet):
            #self.createGeometries(mol)
            chains = atoms.findType(Chain).uniq()
            gc = mol.geomContainer
            for chain in chains:
                if not hasattr(chain, 'spline'):
                    # should call the guiCallback of compute Spline.
                    print 'cannot do the extrusion the spline has not been computed for %s '%chain.full_name()
                    continue

                if chain.spline is None:
                    print "the %s chain has no spline"%chain.full_name()
                    continue
                self.createGeometries(chain)
                atmInSel = atoms.inter(chain.findType(Atom))
                ctlAtms = chain.spline['spline'+chain.id][1]
                ctlAtmsInSel = ctlAtms.inter(atmInSel)
                ctlAtmsInSel.sort()
                # here later you could let the user choose the spline
                # he wishes to extrude.
                name = 'spline'+chain.id
                smooth = chain.spline[name][0].smooth
                #atms = chain.spline[name][1]
                pts_smooth = Numeric.array((smooth),'f')
                #gc.atoms[name] = AtomSet()
                g = gc.geoms[name]
                contpts = Numeric.array(shape2D.contpts)
                contourPoints = contpts[:,:2]
                contnorm = Numeric.array(shape2D.contnorm)
                contourNormals = contnorm[:,:2]
                g.Set(trace3D = pts_smooth,
                      shape2D = self.shape,
                      contourUp = (0.,0.,1.),
                      capsFlag = capsFlag, tagModified=False)
                # add an attribute shape2D to the gleExtrude geometry to
                # have knowledge on the shape extruded
                g.shape2D = self.shape
                g.spline = (chain.spline[name][0], ctlAtmsInSel, ctlAtms)

        if display:
            self.vf.displayExtrudedSpline(nodes, negate=0, setupUndo=1,
                                          topCommand=0)
                
    def buildFormDescr(self, formName):
        if formName == 'geomChooser':
            # Build the imputForm letting the user to choose the shape to
            # be extruded
            nbchordEntryVar = Tkinter.StringVar()
            idf = InputFormDescr(title ="Choose a shape :")
        
            entries = [('rectangle',None),
                       ('circle',None), ('ellipse',None),
                       ('square',None),('triangle',None),
                       #('other', None)
                       ]

            idf.append({'name':'shape',
                        'widgetType':ListChooser,
                        'defaultValue':'circle',
                        'wcfg':{'entries': entries,
                                'title':'Choose a shape'}
                        })
            
        else:
            # Create the description of the inputForm letting the user
            # modify the parameter describing the shape to be extruded.
            initRadius = 0.1
            radiusWidgetDescr = ({'name':'radius',
                                  'widgetType':ThumbWheel,
                                  'wcfg':{ 'labCfg':{'text':'Radius:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                           'showLabel':1, 'width':100,
                                           'min':0.05, 'max':10.0,
                                           'type':float, 'precision':2,
                                           'value':initRadius,
                                           'continuous':1,
                                           'oneTurn':2, 'wheelPad':2,
                                           'height':20},
                                  'gridcfg':{'columnspan':2,'sticky':'we'}})
            initWidth = 1.2
            widthWidgetDescr = ({'name':'width',
                                 'widgetType':ThumbWheel,
                                  'wcfg':{ 'labCfg':{'text':'Width:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                           'showLabel':1, 'width':100,
                                           'min':0.05, 'max':10.0,
                                           'type':float, 'precision':2,
                                           'value':initWidth,
                                           'continuous':1,
                                           'oneTurn':2, 'wheelPad':2,
                                           'height':20},
                                  'gridcfg':{'columnspan':2,'sticky':'we'}})
            initHeight = 0.2
            heightWidgetDescr = ({'name':'height',
                                 'widgetType':ThumbWheel,
                                  'wcfg':{ 'labCfg':{'text':'Height:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                           'showLabel':1, 'width':100,
                                           'min':0.05, 'max':10.0,
                                           'type':float, 'precision':2,
                                           'value':initHeight,
                                           'continuous':1,
                                           'oneTurn':2, 'wheelPad':2,
                                           'height':20},
                                  'gridcfg':{'columnspan':2,'sticky':'we'}})
            initSide = 1.0
            sideWidgetDescr = ({'name':'sidelength',
                                'widgetType':ThumbWheel,
                                  'wcfg':{ 'labCfg':{'text':'Length of side:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                           'showLabel':1, 'width':100,
                                           'min':0.05, 'max':10.0,
                                           'type':float, 'precision':2,
                                           'value':initSide,
                                           'continuous':1,
                                           'oneTurn':2, 'wheelPad':2,
                                           'height':20},
                                  'gridcfg':{'columnspan':2,'sticky':'we'}})
            
            capsWidgetDescr = {'name':'capsFlag',
                               'widgetType':Tkinter.Checkbutton,
                               'defaultValue':0,
                               'wcfg':{'text':'caps',
                                       'variable': Tkinter.IntVar()},
                                   'gridcfg':{'sticky':'we'}}

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
                idf.append({'name':'grand',
                            'widgetType':ThumbWheel,
                            'wcfg':{ 'labCfg':{'text':'Demi-grand Axis:', 
                                               'font':(ensureFontCase('helvetica'),12,'bold')},
                                     'showLabel':1, 'width':100,
                                     'min':0.05, 'max':10.0,
                                     'type':float, 'precision':2,
                                     'value':0.5,
                                     'continuous':1,
                                     'oneTurn':2, 'wheelPad':2,
                                     'height':20},
                            'gridcfg':{'columnspan':2,'sticky':'we'}})

                idf.append({'name':'small',
                            'widgetType':ThumbWheel,
                            'wcfg':{ 'labCfg':{'text':'Demi-small Axis:', 
                                               'font':(ensureFontCase('helvetica'),12,'bold')},
                                     'showLabel':1, 'width':100,
                                     'min':0.05, 'max':10.0,
                                     'type':float, 'precision':2,
                                     'value':0.2,
                                     'continuous':1,
                                     'oneTurn':2, 'wheelPad':2,
                                     'height':20},
                            'gridcfg':{'columnspan':2,'sticky':'we'}})
            elif formName == 'square':
                idf = InputFormDescr(title="Square size :")
                idf.append(sideWidgetDescr)

            elif formName == 'triangle':
                idf = InputFormDescr(title="Triangle size :")
                idf.append(sideWidgetDescr)
                
                
            # These widgets are present in everyInputForm.
            idf.append(capsWidgetDescr)

        return idf
            
    def guiCallback(self):
        # Write a shape chooser method that should be reused in
        # secondaryStructureCommands, CATrace commands, and splineCommands.
        typeshape = self.showForm('geomChooser')
        if typeshape == {} or typeshape['shape'] == []: return
        # Shape is a Rectangle
        if typeshape['shape'][0]=='rectangle':
            val = self.showForm('rectangle')
            if val:
                shape = Rectangle2D(width = val['width'],
                                    height = val['height'],
                                    firstDup=1, vertDup=1)
                capsFlag = val['capsFlag']

        # Shape is a Circle:
        elif typeshape['shape'][0]=='circle':

            val = self.showForm('circle')
            if val:
                shape = Circle2D(radius=val['radius'], firstDup=1)
                capsFlag = val['capsFlag']

        # Shape is an Ellipse
        elif typeshape['shape'][0]=='ellipse':
            val = self.showForm('ellipse')
            if val:
                shape = Ellipse2D(demiGrandAxis= val['grand'],
                                  demiSmallAxis=val['small'], firstDup = 1)
                capsFlag = val['capsFlag']

        # Shape is a Square:
        elif typeshape['shape'][0]=='square':
            val = self.showForm('square')
            if val:
                shape = Square2D(side=val['sidelength'], firstDup=1, vertDup=1)
                capsFlag = val['capsFlag']

        # Shape is a Triangle:
        elif typeshape['shape'][0]=='triangle':
            val = self.showForm('triangle')
            if val:
                shape = Triangle2D(side=val['sidelength'], firstDup=1,
                                   vertDup=1)
                capsFlag = val['capsFlag']


        else: return

        if val:
            nodes = self.vf.getSelection()
            self.doitWrapper(nodes, shape2D=shape,
                             capsFlag=capsFlag, redraw=1)


class DisplayExtrudedSplineCommand(DisplayCommand):
    """ The DisplayExtrudeSplineCommand implements a set of methods to display/undisplay part of the geometries created by the ExtrudeSplineCommand. This command is undoable.
    \nPackage : Pmv
    \nModule  : splineCommands
    \nClass   : DisplaySplineCommand
    \nCommand : displaySpline
    \nSynopsis:\nNone<- displaySpline(nodes, negate=False, only=False, **kw)
    \nRequired Arguments:\n    
        nodes --- TreeNodeSet holding the current selection. Can also be a string representing the current selection.
    \nOptional Arguments:\n    
        only  --- flag when set to 1 only the current selection will be displayed
        \nnegate --- flag when set to 1 undisplay the current selection
    """


    def setupUndoBefore(self, nodes, only=False, negate=False):
        """ This method makes the command undoable"""
        if len(nodes)==0 : return
        geomSet = []
        for mol in self.vf.Mols:
            gc = mol.geomContainer
            for chain in mol.chains:
                if not hasattr(chain,'spline') or chain.spline is None:
                    continue
                geomSet = geomSet + gc.atoms['spline'+chain.id]
        kw = {'redraw':1}
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
    
    
    def onAddCmdToViewer(self):
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('computeSplineGC'):
            self.vf.loadCommand("splineCommands", "computeSplineGC", "Pmv",
                                topCommand = 0)


    def __call__(self, nodes, only=False,  negate=False, **kw):
        """None<- displaySpline(nodes, negate=False, only=False, **kw)
        \nRequired Arguments:\n    
        nodes --- TreeNodeSet holding the current selection. Can also be a string representing the current selection.
        \nOptional Arguments:\n    
        only --- flag when set to 1 only the current selection will be displayed
        \nnegate --- flag when set to 1 undisplay the current selection
        """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"

        nodes = self.vf.expandNodes(nodes)
        kw['only'] = only
        kw['negate'] = negate
        if not kw.has_key('redraw') : kw['redraw']=1
        apply(self.doitWrapper, (nodes,), kw)
                

    def doit(self, nodes, only=False, negate=False):
        #####################################################
        def drawAtoms(chain, atmInCurSel, splineName, only, negate):
            # Get a handle on the geomContainer
            gc = chain.parent.geomContainer
            closed = gc.geoms[splineName].spline[0].closed
            shape2D = gc.geoms[splineName].shape2D
            lshape = shape2D.lenShape
            # 1- Get the right sets of atoms.
            # Set of ctlPts displayed
            set = gc.atoms[splineName]

            # Set of control points used to compute the spline.
            # right now the 'spline'+chain.id is hard coded
            ctlAtms = chain.spline['spline'+chain.id][1]

            # Set of control points used to compute the spline contained
            # in the current selection:
            ctlAtmsInSel = ctlAtms.inter(atmInCurSel)

            ##if negate, remove current atms from displayed set
            if negate: set = set - ctlAtmsInSel

            ##if only, replace displayed set with current atms 
            else:
                if only:
                    set = ctlAtmsInSel
                else: 
                    set = ctlAtmsInSel.union(set)
            
            # 2- Now Update the GleExtrude Geometry:
            if len(set)==0:
                # no atms no GleExtrude Geometry:
                #gc.geoms[splineName].Set(visible = 0, tagModified=False)
                gc.geoms[splineName].Set(stripBegin=[], stripEnd = [],
                                         visible=0, tagModified=False)
                gc.atoms[splineName] = set
                return
            # the rest is done only if there are some atoms:
            # compute the faces indices for the atoms to be displayed.
            #set.sort()
            caps = gc.geoms[splineName].capsFlag
            nbchords = chain.spline['spline'+chain.id][0].nbchords
            stripBegin = []
            stripEnd = []
            dlshape = lshape*2
            test = []
            for a in set:
                atmIndex = ctlAtms.index(a)
                if atmIndex == 0:
                    # 1s point
                    length = nbchords/2

                    for n in range(length):
                        # last 2 strips and 2 first strips
                        sB = (atmIndex + n)*dlshape
                        sE = sB+dlshape
                        stripBegin.append(sB)
                        stripEnd.append(sE)

                    if closed:
                        # 2 first faces and 3 last.
                        index = len(ctlAtms)
                        start = (index - 1)*nbchords + nbchords/2 
                        for n in range(nbchords/2):
                            sB = (start +n)*dlshape
                            sE = sB+dlshape
                            stripBegin.append(sB)
                            stripEnd.append(sE)
                
                elif atmIndex == len(ctlAtms)-1:
                    #last point
                    if closed ==1:
                        length = nbchords
                    elif caps == 1:
                        length = nbchords/2+2
                    else:
                        length = nbchords/2

                    start = (atmIndex-1)*nbchords + nbchords/2    
                    for n in range(length):
                        sB = (start + n)*dlshape
                        stripBegin.append(sB)
                        sE = sB+dlshape
                        stripEnd.append(sE)

                else:
                    start = (atmIndex-1)*nbchords + nbchords/2
                    for n in range(nbchords):
                        sB = (start + n)*dlshape
                        sE = sB+dlshape
                        stripBegin.append(sB)
                        stripEnd.append(sE)
            gc.atoms[splineName] = set
            g = gc.geoms[splineName]
            g.Set(stripBegin=stripBegin, stripEnd=stripEnd, visible=1,
                  tagModified=False)
            stripBegin.sort()
            stripEnd.sort()
                
        ##################################################################

        
        molecules, atomSets = self.vf.getNodesByMolecule(nodes, Atom)
        for mol, atoms in map(None, molecules, atomSets):
            gc = mol.geomContainer
            chains = atoms.findType(Chain).uniq()
            for chain in chains:
                atomsInSel = atoms.inter(chain.findType(Atom))
                if not hasattr(chain,'spline') or chain.spline is None:
                    # maybe fixe that.
                    continue
                splineName = 'spline'+chain.id
                if not gc.atoms.has_key(splineName) \
                   or not gc.geoms.has_key(splineName):
                    continue
                drawAtoms(chain, atomsInSel, splineName, only, negate)
                
        
class UndisplayExtrudedSplineCommand(DisplayCommand):
    """ UndisplayExtrudeSplineCommand is the interactive command to undisplay part of the molecule when displayed as an extruded spline.It calls the displatExtrudedSpline with negate =1
    \nPackage : Pmv
    \nModule  : splineCommands
    \nClass   : UnDisplaySplineCommand
    \nCommand : undisplaySpline
    \nSynopsis:\nNone <- undisplayExtrudedSpline(nodes, **kw)
    \nRequired Arguments:\n    
     nodes --- TreeNodeSet holding the current selection. Can also be a string representing the current selection.
    """
    def onAddCmdToViewer(self):
        #if not self.vf.hasGui: return 
        if not self.vf.commands.has_key('displayExtrudedSpline'):
            self.vf.loadCommand('splineCommands',
                                ['displayExtrudedSpline'], 'Pmv',
                                topCommand=0)

    def __call__(self, nodes, **kw):
        """ None <- undisplayExtrudedSpline(nodes, **kw)
        \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection. Can also be a string representing the current selection.
        """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'" + nodes +"'"
        kw['negate']= 1
        apply(self.vf.displayExtrudedSpline, (nodes,),kw)
            
            
class DisplaySplineAsLineCommand(DisplayCommand):
    """ DisplaySplineAsLineCommand implements a set of method to display/
    undisplay part of the spline when represented as line.
    \nPackage : Pmv
    \nModule  : splineCommands
    \nClass   : DisplaySplineAsLineCommand
    \nCommand : displaySplineAsLine
    \nSynopsis:\nNone<- displaySplineAsLine(nodes, lineWidth=3, only=0, negate=0,**kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection. Can also be a string representing the current selection.
    \nOptional Arguments:\n
        only  --- Boolean flag when set to True only the current selection will be displayed
        \nnegate --- Boolean flag when set to True undisplay the current selection lineWidth: width of the line representing the spline.
    """

    def onRemoveObjectFromViewer(self, obj):
        gc = obj.geomContainer
        for c in obj.chains:
            splineName = 'linespline'+c.id
            if gc.geoms.has_key(splineName):
                g = gc.geoms[splineName]
                if hasattr(g, 'spline'):
                    delattr(g,'spline')


    def createGeometries(self, obj):
        """ Method creating the lineSpline geometry."""
        geomC = obj.geomContainer
        for chain in obj.chains:
            addGeom = False
            if not hasattr(chain, 'spline') or chain.spline is None:
                # no spline Object computed for that chain.
                continue
            name = "lineSpline" + chain.id
            if geomC.geoms.has_key(name) and geomC.atoms.has_key(name):
                g = geomC.geoms[name]
                addGeom = True
                if g.spline == chain.spline['spline'+chain.id]:
                    # same spline Object doesn't need to reconstruct the
                    # geometry
                    continue
                else:
                    # need create the geometry again and to add it again:
                    # so need to first remove it from the viewer then delete
                    # it.
                    if geomC.VIEWER:
                        geomC.VIEWER.RemoveObject(g)
                    else:
                        if g in geomC.masterGeom.children:
                            geomC.masterGeom.children.remove(g)
                    del geomC.geoms[name]
                
            smooth = chain.spline['spline'+chain.id][0].smooth
            vertices = smooth[1:-1]
            g = IndexedPolylines(name=name,
                                 vertices = vertices, inheritLineWidth=0)
                                 #protected=True fail a test in test_splineCommands.py"

            
            #3/7/05: commented out setting geomC.geoms[name] directly
            # this is handled by the geomContainer.addGeom method now...
            #if not addGeom:
            #    geomC.geoms[name] = g
                
            # need for coloring and picking.
            g.spline = chain.spline['spline'+chain.id]

            #geomC.atoms[name] = AtomSet()
            geomC.geomPickToAtoms[name] = self.pickedVerticesToAtoms
            geomC.atomPropToVertices[name] = self.atomPropToVertices
            geomC.geomPickToBonds[name] = None
            geomC.addGeom(g, parent=geomC.masterGeom, redo=0)
            self.managedGeometries.append(g)
            
            for atm in chain.parent.findType(Atom):
                atm.colors[name] = (1.0, 1.0, 1.0)
                atm.opacities[name] = 1.0
            
        
    def pickedVerticesToAtoms(self, geom, vertInd):
        """Function called to convert a picked vertex into an atom"""

        # this function gets called when a picking or drag select event has
        # happened. It gets called with a geometry and the list of vertex
        # indices of that geometry that have been selected.
        # This function is in charge of turning these indices into an AtomSet
        pickedAtms = AtomSet()
        nbchords = geom.spline[0].nbchords
        lastVertices = geom.spline[1].index(geom.spline[1][-1])
        closed = geom.spline[0].closed
        for v in vertInd:
            splinePts = v
            # 2- need to convert that index into an atom indices in the
            # set
            if not closed:
                if splinePts>=nbchords/2 and \
                   splinePts <(lastVertices)*nbchords - nbchords/2:
                    # normal points
                    atmIndex = (splinePts-nbchords/2)/nbchords + 1
            
            
                elif splinePts<nbchords/2:
                    atmIndex = 0

                elif splinePts >= (lastVertices)*nbchords - nbchords/2:
                    atmIndex = -1

            else:
                lastIndex = (lastVertices)*nbchords - nbchords/2
                if splinePts>=nbchords/2 and \
                   splinePts <lastIndex:
                    # normal points
                    atmIndex = (splinePts-nbchords/2)/nbchords + 1
            
                elif splinePts >= lastIndex and \
                     splinePts < lastIndex + nbchords:
                    atmIndex = -1
                elif splinePts<nbchords/2 or \
                     splinePts >= lastIndex + nbchords:
                    atmIndex = 0

            atm = geom.spline[1][atmIndex]
            pickedAtms.append(atm)

        # 3- need to return the corresponding atomset.
        return pickedAtms


    def atomPropToVertices(self, geom, atoms, propName, propIndex=None):
        """Function called to compute the array of colors"""
        # geom: IndexedPolylines
        # atoms: list of the atoms in the current selection.
        if len(atoms)==0: return
        propVect = []

        # same number of vertices than point in the path3D :
        # (nb of atoms used as control points used to compute the spline
        # * nbchord)
        ctlAtms = geom.spline[1]
        closed = geom.spline[0].closed
        for a in atoms:
            if not closed:
                if a==ctlAtms[0] or a == ctlAtms[-1]:
                    nbchords = geom.spline[0].nbchords/2
                else:
                    nbchords = geom.spline[0].nbchords
            else:
                nbchords = geom.spline[0].nbchords

            prop = getattr(a, propName)

            if not propIndex is None:
                prop = prop[propIndex]

            for n in range(nbchords):
                propVect.append(prop)
        return propVect

    def setupUndoBefore(self, nodes, lineWidth=3, only=False, negate=False):
        if len(nodes)==0 : return
        kw = {}
        kw['lineWidth'] = lineWidth
        kw['redraw'] = True
        geomSet = []
        for mol in self.vf.Mols:
            gc = mol.geomContainer
            for chain in mol.chains:
                if not hasattr(chain, 'spline') or chain.spline is None:
                    continue
                name = 'lineSpline%s'%chain.id
                if not gc.atoms.has_key(name):
                    continue
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


    def guiCallback(self):
        idf = InputFormDescr(title="Display Spline As Line :")
        idf.append({'name':'display',
                    'widgetType':Pmw.RadioSelect,
                    'listtext':['display','display only', 'undisplay'],
                    'defaultValue':'display',
                    'wcfg':{'orient':'horizontal',
                            'buttontype':'radiobutton'},
                    'gridcfg':{'sticky': 'we'}})

        idf.append( {'name': 'lineWidth',
                     'widgetType':ExtendedSliderWidget,
                     'wcfg':{'label': 'Line width:    ',
                             'minval':1,'maxval':10,
                             'init':3,
                             'labelsCursorFormat':'%d',
                             'sliderType':'int',
                             'entrywcfg':{'width':4},
                             'entrypackcfg':{'side':'right'}},
                     'gridcfg':{'sticky':'we'}
                     })

        val = self.vf.getUserInput(idf)

        if val:
            val['redraw'] = 1
            if val['display']=='display':
                val['only']= 0
                val['negate'] = 0
                del val['display']
            elif val['display']=='display only':
                val['only']= 1
                val['negate'] = 0
                del val['display']
            elif val['display']== 'undisplay':
                val['negate'] = 1
                val['only'] = 0
                del val['display']
            apply( self.doitWrapper, (self.vf.getSelection(),), val)
        
        


    def __call__(self, nodes, lineWidth=3, only=False, negate=False, **kw):
        """None<- displaySplineAsLine(nodes,lineWidth=3,only=0,negate=0,**kw)
        \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection. Can also be a string representing the current selection.
        \nOptional Arguments:\n
        only  --- Boolean flag when set to True only the current selection will be displayed
        \nnegate --- Boolean flag when set to True undisplay the current selection 
        \nlineWidth --- width of the line representing the spline.
        """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"

        nodes = self.vf.expandNodes(nodes)
        kw['only'] = only
        kw['negate'] = negate
        kw['lineWidth']=lineWidth
        if not kw.has_key('redraw'):kw['redraw'] = 1
        apply(self.doitWrapper, (nodes,), kw)


    def doit(self, nodes, lineWidth=3, only=False, negate=False):

        #######################################################

        def drawAtoms(chain, atmInCurSel, splineName, lineWidth,
                      only, negate):
            # Get a handle on the geomContainer            
            gc = chain.parent.geomContainer

            # 1- Get the right sets of atoms.
            # Set of ctlPts displayed
            set = gc.atoms[splineName]
            # Set of control points used to compute the spline.
            # right now the 'spline'+chain.id is hard coded
            ctlAtms = chain.spline['spline'+chain.id][1]
            # Set of control points used to compute the spline contained
            # in the current selection:
            ctlAtmsInSel = ctlAtms.inter(atmInCurSel)
            ##if negate, remove current atms from displayed set
            if negate: set = set - ctlAtmsInSel

            ##if only, replace displayed set with current atms 
            else:
                if only:
                    set = ctlAtmsInSel
                else: 
                    set = ctlAtmsInSel.union(set)

            # 2- Now Update the IndexedPolyLines geometry:
            if len(set)==0:
                # no atms no IndexedPolylines:
                gc.geoms[splineName].Set(faces=[], tagModified=False)
                gc.atoms[splineName] = set
                return

            # the rest is done only if there are some atoms:
            # compute the faces indices for the atoms to be displayed.
            #set.sort()
            nbchords = chain.spline['spline'+chain.id][0].nbchords
            closed = gc.geoms[splineName].spline[0].closed
            faces = []
            for a in set:
                atmIndex = ctlAtms.index(a)
                if atmIndex == 0:
                    # first point or last points only have 2 faces.
                    start = atmIndex
                    end = nbchords/2
                    for x in range(start, end):
                        faces.append((x, x+1))

                    if closed ==1:
                        index = len(ctlAtms)
                        start = (index - 1)*nbchords + nbchords/2
                        end = start + nbchords/2
                        for x in range(start, end):
                            faces.append((x, x+1))
                        
                elif atmIndex == len(ctlAtms)-1:
                    start = (atmIndex-1)*nbchords + nbchords/2
                    if closed ==1:
                        end = start+nbchords
                    else:
                        end =  start + nbchords/2

                    for x in range(start, end):
                        faces.append((x, x+1))
                    
                else:
                    
                    start = (atmIndex-1)*nbchords + nbchords/2
                    end = start + nbchords
                    for x in range(start, end):
                        faces.append((x, x+1))
                #faces = faces + map(lambda x: (x,x+1), range(start, end))
            gc.atoms[splineName] =  set
            g = gc.geoms[splineName]
            
            g.Set(faces=faces, lineWidth=lineWidth, visible=1,
                  tagModified=False)
            
        ##############################################################

        molecules, atomssSet = self.vf.getNodesByMolecule(nodes, Atom)
        for mol, atoms in map(None, molecules, atomssSet):
            self.createGeometries(mol)
            chains = atoms.findType(Chain).uniq()
            gc = mol.geomContainer
            for chain in chains:
                splineName = 'lineSpline'+chain.id
                atomsInSel = atoms.inter(chain.findType(Atom))
                if not hasattr(chain, 'spline') or chain.spline is None:
                    print 'the spline has not been computed for %s '%chain.full_name()
                    continue
                drawAtoms(chain, atomsInSel, splineName, lineWidth, only,
                          negate) 

class UndisplaySplineAsLineCommand(DisplayCommand):
    """ UndisplaySPlineAsLineCommand calls the displaySplineAsLine command with the flag negate set to 1
    \nPackage : Pmv
    \nModule  : splineCommands
    \nClass   : UndisplaySplineAsLineSplineCommand
    \nCommand : undisplaySplineAsLineSpline
    \nSynopsis:\n
    None <- undisplaySplineAsLine(nodes, **kw)
    \nRequired Arguments:\n
    nodes --- TreeNodeSet holding the current selection. Can also be a
                string representing the current selection.
    """

    def onAddCmdToViewer(self):
        #if not self.vf.hasGui: return 
        if not self.vf.commands.has_key('displaySplineAsLine'):
            self.vf.loadCommand('splineCommands',
                                ['displaySplineAsLine'], 'Pmv',
                                topCommand=0)

     
    def __call__(self, nodes, **kw):
        """ None <- undisplaySplineAsLine(nodes, **kw)
        \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection. Can also be a
                string representing the current selection.
        """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'" + nodes +"'"
        kw['negate']= 1
        if not nodes: return
        apply(self.vf.displaySplineAsLine, (nodes,),kw)




class CustomSplineCommand(MVCommand):
    """This command computes and extrudes spline using the values given or from the widget.
    \nPackage : Pmv
    \nModule  : splineCommands
    \nClass   : CustomSplineCommand
    \nCommand : customSpline
    \nSynopsis:\nNone<---customTrace(nodes, atmtype="CA", curSel=False, nbchords=4,interp='interpolation', continuity=2, closedSpline=False,sortAtms=True,  shape2D=None, capsFlag=False, display=True,**kw)
        \nRequired Arguments:\n
        nodes --- self.getSelection()
        \nOptional Arguments:\n
        \natmtype --- specifies the atom type of the control points.
                      the atoms of the current selection of the given
                      atom type are used as the control points.
                      atmtype can be 'CA'(default value) 'CA,N' 'O' etc.... 
                      
        \ncurSel --- Boolean flag to use the atoms in current selection as control
                      points. (default=False)
        \nnbchords --- number of point per control points in the smooth array
        \ninterp --- flag if set to 'interpolation' interpolate the control
                      points.
        \ncontinuity  --- specifies the continuity of the curve.
        \nclosedSpline --- Boolean flag when set to True the spline will be closed (1st atom will be connected to the last atom. (default = False)
        \nsortAtms --- Boolean flag to sort the ctlAtms or not. (default = True)
        \nshape2D --- instance of a DejaVu.Shapes class (Triangle2DDup, Circle2D...)the default shape is a circle2D
        \ncapsFlag --- Boolean flag to add caps at the end of the spline (default=False)
        \ndisplay --- Boolean flag to call or not the displayExtrudedSpline command default value is True.
    """
    
    def __init__(self):
        MVCommand.__init__(self)
        self.flag = self.flag | self.objArgOnly
        self.flag = self.flag | self.negateKw



    def onAddCmdToViewer(self):
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('computeSpline'):
            self.vf.loadCommand("splineCommands",
                                "computeSpline", "Pmv",
                                topCommand = 0)
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('extrudeSpline'):
            self.vf.loadCommand("splineCommands",
                                "extrudeSpline", "Pmv",
                                topCommand = 0)
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('displaySpline'):
            self.vf.loadCommand("splineCommands",
                                "displayExtrudedSpline", "Pmv",
                                topCommand = 0)

    def buildFormDescr(self, formName):
        if formName == 'customSpline':
            idf = InputFormDescr(title="Custom Spline:")
            nbchordEntryVar = Tkinter.StringVar()
            idf.append({'name':'curSel',
                        'widgetType':Tkinter.Checkbutton,
                        'defaultValue':0,
                        'wcfg':{'text':'Current Selection',
                                'variable':Tkinter.IntVar(),
                               'command':self.cursel_cb},
                        'gridcfg':{'sticky':'we'}})

            # ? maybe a list of checkbox Entryfield to choose the atomType.
            idf.append({'widgetType':Pmw.EntryField,
                        'name':'atmtype',
                        'wcfg':{'labelpos':'w',
                                'label_text':'Enter atom types: ',
                                'validate':None,
                                },
                        'gridcfg':{'sticky':'we'}})

            # number of points per residue
            idf.append( {'name': 'nbchords',
                         'widgetType':ExtendedSliderWidget,
                         'type':int,
                         'wcfg':{'label': 'nb. Pts Per Residue:  ',
                                 'minval':4,'maxval':15, 'incr': 1, 'init':8,
                                 'labelsCursorFormat':'%d', 'sliderType':'int',
                                 'entrywcfg':{'textvariable':nbchordEntryVar,
                                              'width':4},
                                 'entrypackcfg':{'side':'right'}},
                         'gridcfg':{'sticky':'we'}
                         })
            # Continuity
            idf.append( {'name': 'continuity',
                         'widgetType':ExtendedSliderWidget,
                         'type':int,
                         'wcfg':{'label': 'Continuity',
                                 'minval':0,'maxval':5, 'incr': 1, 'init':2,
                                 'labelsCursorFormat':'%d', 'sliderType':'int',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                         'gridcfg':{'sticky':'we'}
                         })

            idf.append({'name':'closedSpline',
                        'widgetType':Tkinter.Checkbutton,
                        'defaultValue':0,
                        'wcfg':{'text':'Closed Spline       ',
                                'variable':Tkinter.IntVar()},
                        'gridcfg':{'sticky':'we'}})

            idf.append({'name':'sortAtms',
                        'widgetType':Tkinter.Checkbutton,
                        'defaultValue':1,
                        'wcfg':{'text':'Sort control Atoms',
                                'variable':Tkinter.IntVar()},
                        'gridcfg':{'sticky':'we'}})


            
            nbchordEntryVar = Tkinter.StringVar()
            
        
            entries = [('rectangle',None),
                       ('circle',None), ('ellipse',None),
                       ('square',None),('triangle',None),
                       #('other', None)
                       ]

            idf.append({'name':'shape',
                        'widgetType':ListChooser,
                        'defaultValue':'circle',
                        'wcfg':{'entries': entries,
                                'title':'Choose a shape'}
                        })
            
        else:
            # Create the description of the inputForm letting the user
            # modify the parameter describing the shape to be extruded.
            initRadius = 0.1
            radiusWidgetDescr = ({'name':'radius',
                                  'widgetType':ThumbWheel,
                                  'wcfg':{ 'labCfg':{'text':'Radius:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                           'showLabel':1, 'width':100,
                                           'min':0.05, 'max':10.0,
                                           'type':float, 'precision':2,
                                           'value':initRadius,
                                           'continuous':1,
                                           'oneTurn':2, 'wheelPad':2,
                                           'height':20},
                                  'gridcfg':{'columnspan':2,'sticky':'we'}})
            initWidth = 1.2
            widthWidgetDescr = ({'name':'width',
                                 'widgetType':ThumbWheel,
                                  'wcfg':{ 'labCfg':{'text':'Width:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                           'showLabel':1, 'width':100,
                                           'min':0.05, 'max':10.0,
                                           'type':float, 'precision':2,
                                           'value':initWidth,
                                           'continuous':1,
                                           'oneTurn':2, 'wheelPad':2,
                                           'height':20},
                                  'gridcfg':{'columnspan':2,'sticky':'we'}})
            initHeight = 0.2
            heightWidgetDescr = ({'name':'height',
                                 'widgetType':ThumbWheel,
                                  'wcfg':{ 'labCfg':{'text':'Height:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                           'showLabel':1, 'width':100,
                                           'min':0.05, 'max':10.0,
                                           'type':float, 'precision':2,
                                           'value':initHeight,
                                           'continuous':1,
                                           'oneTurn':2, 'wheelPad':2,
                                           'height':20},
                                  'gridcfg':{'columnspan':2,'sticky':'we'}})
            initSide = 1.0
            sideWidgetDescr = ({'name':'sidelength',
                                'widgetType':ThumbWheel,
                                  'wcfg':{ 'labCfg':{'text':'Length of side:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                           'showLabel':1, 'width':100,
                                           'min':0.05, 'max':10.0,
                                           'type':float, 'precision':2,
                                           'value':initSide,
                                           'continuous':1,
                                           'oneTurn':2, 'wheelPad':2,
                                           'height':20},
                                  'gridcfg':{'columnspan':2,'sticky':'we'}})
            
            capsWidgetDescr = {'name':'capsFlag',
                               'widgetType':Tkinter.Checkbutton,
                               'defaultValue':0,
                               'wcfg':{'text':'caps',
                                       'variable': Tkinter.IntVar()},
                                   'gridcfg':{'sticky':'we'}}

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
                idf.append({'name':'grand',
                            'widgetType':ThumbWheel,
                            'wcfg':{ 'labCfg':{'text':'Demi-grand Axis:', 
                                               'font':(ensureFontCase('helvetica'),12,'bold')},
                                     'showLabel':1, 'width':100,
                                     'min':0.05, 'max':10.0,
                                     'type':float, 'precision':2,
                                     'value':0.5,
                                     'continuous':1,
                                     'oneTurn':2, 'wheelPad':2,
                                     'height':20},
                            'gridcfg':{'columnspan':2,'sticky':'we'}})

                idf.append({'name':'small',
                            'widgetType':ThumbWheel,
                            'wcfg':{ 'labCfg':{'text':'Demi-small Axis:', 
                                               'font':(ensureFontCase('helvetica'),12,'bold')},
                                     'showLabel':1, 'width':100,
                                     'min':0.05, 'max':10.0,
                                     'type':float, 'precision':2,
                                     'value':0.2,
                                     'continuous':1,
                                     'oneTurn':2, 'wheelPad':2,
                                     'height':20},
                            'gridcfg':{'columnspan':2,'sticky':'we'}})
            elif formName == 'square':
                idf = InputFormDescr(title="Square size :")
                idf.append(sideWidgetDescr)

            elif formName == 'triangle':
                idf = InputFormDescr(title="Triangle size :")
                idf.append(sideWidgetDescr)
                
                
            # These widgets are present in everyInputForm.
            idf.append(capsWidgetDescr)

        return idf
    def cursel_cb(self, event = None):
        """ if the use curSel checkbutton is on: the entryField should be
        disabled."""
        if self.cmdForms.has_key('customSpline'):
            idf = self.cmdForms['customSpline'].descr
            cbVar =idf.entryByName['curSel']['wcfg']['variable']
            entry = idf.entryByName['atmtype']['widget']

            if cbVar.get() == 1:
                entry._entryFieldEntry.configure(state = Tkinter.DISABLED)
                entry.configure(label_fg = 'darkgray')

            else:
                entry._entryFieldEntry.configure(state = Tkinter.NORMAL)
                entry.configure(label_fg = 'black')

    def guiCallback(self):

        nodes = self.vf.getSelection()
        if not nodes: return
        typeshape = self.showForm('customSpline')
        if typeshape:
            if typeshape['curSel']==0 and \
               (typeshape['atmtype']=='' or typeshape['atmtype']== ' '):
                # if no atmtype given and not cursel checked nothing
                # happens
                return
                                     
            typeshape['redraw']=0
            
        # Write a shape chooser method that should be reused in
        # secondaryStructureCommands, CATrace commands, and splineCommands.
        if typeshape == {} or typeshape['shape'] == []: return
        # Shape is a Rectangle
        if typeshape['shape'][0]=='rectangle':
            val = self.showForm('rectangle')
            if val:
                shape = Rectangle2D(width = val['width'],
                                    height = val['height'],
                                    firstDup=1, vertDup=1)
                capsFlag = val['capsFlag']

        # Shape is a Circle:
        elif typeshape['shape'][0]=='circle':

            val = self.showForm('circle')
            if val:
                shape = Circle2D(radius=val['radius'], firstDup=1)
                capsFlag = val['capsFlag']

        # Shape is an Ellipse
        elif typeshape['shape'][0]=='ellipse':
            val = self.showForm('ellipse')
            if val:
                shape = Ellipse2D(demiGrandAxis= val['grand'],
                                  demiSmallAxis=val['small'], firstDup = 1)
                capsFlag = val['capsFlag']

        # Shape is a Square:
        elif typeshape['shape'][0]=='square':
            val = self.showForm('square')
            if val:
                shape = Square2D(side=val['sidelength'], firstDup=1, vertDup=1)
                capsFlag = val['capsFlag']

        # Shape is a Triangle:
        elif typeshape['shape'][0]=='triangle':
            val = self.showForm('triangle')
            if val:
                shape = Triangle2D(side=val['sidelength'], firstDup=1,
                                   vertDup=1)
                capsFlag = val['capsFlag']


        else: return
        self.vf.computeSpline(nodes,atmtype=typeshape['atmtype'],curSel=typeshape['curSel'], nbchords=4, interp='interpolation', continuity=2, closedSpline=False, sortAtms=True)
        if val:
            self.vf.extrudeSpline(nodes, shape2D=shape, capsFlag=capsFlag, display=True)
        
    def __call__(self,nodes, atmtype="CA", curSel=False, nbchords=4, 
                 interp='interpolation', continuity=2, closedSpline=False,
                 sortAtms=True,  shape2D=None, capsFlag=False, display=True,**kw):
        """None<---customTrace(nodes, atmtype="CA", curSel=False, nbchords=4,interp='interpolation', continuity=2, closedSpline=False,sortAtms=True,  shape2D=None, capsFlag=False, display=True,**kw)
        \nRequired Arguments:\n
        nodes --- self.getSelection()
        \nOptional Arguments:\n
        \natmtype --- specifies the atom type of the control points.
                      the atoms of the current selection of the given
                      atom type are used as the control points.
                      atmtype can be 'CA'(default value) 'CA,N' 'O' etc.... 
                      
        \ncurSel --- Boolean flag to use the atoms in current selection as control
                      points. (default=False)
        \nnbchords --- number of point per control points in the smooth array
        \ninterp --- flag if set to 'interpolation' interpolate the control
                      points.
        \ncontinuity  --- specifies the continuity of the curve.
        \nclosedSpline --- Boolean flag when set to True the spline will be closed (1st atom will be connected to the last atom. (default = False)
        \nsortAtms --- Boolean flag to sort the ctlAtms or not. (default = True)
        \nshape2D --- instance of a DejaVu.Shapes class (Triangle2DDup, Circle2D...)the default shape is a circle2D
        \ncapsFlag --- Boolean flag to add caps at the end of the spline (default=False)
        \ndisplay --- Boolean flag to call or not the displayExtrudedSpline command default value is True.
        """
        
        nodes = self.vf.expandNodes(nodes) 
        if not nodes:
            return "ERROR"
        kw['atmtype']=atmtype
        kw['curSel']=curSel
        kw['nbchords']=nbchords
        kw['interp']=interp
        kw['continuity']=continuity
        kw['closedSpline']=closedSpline
        kw['sortAtms']=sortAtms
        kw['shape2D']=shape2D
        kw['capsFlag']=capsFlag
        kw['display']=display
        apply(self.doitWrapper, (nodes,), kw)   

    def doit(self, nodes,**kw):     
        nkw={}
        if kw!={}:
            if kw['display']==0:
                nkw['negate']=1
                apply(self.vf.displayExtrudedSpline,(nodes,),nkw)
                return

            elif kw['display']==1:
                if kw.has_key('negate'):
                    if kw['negate']==1:
                        nkw['negate']=1
                        apply(self.vf.displayExtrudedSpline,(nodes,),nkw)
                        return
                 
        self.vf.computeSpline(nodes,atmtype=kw['atmtype'],curSel=kw['curSel'], nbchords=kw['nbchords'], interp= kw['interp'], continuity=kw['continuity'], closedSpline=kw['closedSpline'], sortAtms=kw['sortAtms'])         
        self.vf.extrudeSpline(nodes, shape2D=kw['shape2D'], capsFlag=kw['capsFlag'], display=kw['display'])
        


class ComputeExtrudeSplineCommand(MVCommand):
    """This command computes and extrudes spline with default arguements.
    \nPackage : Pmv
    \nModule  : splineCommands
    \nClass   : ComputeExtrudeSplineCommand
    \nCommand : computeExtrudeSpline
    \nSynopsis:\nNone <- computeExtrudeSpline(nodes, only=False, negate=False, **kw)
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
        if not self.vf.commands.has_key('computeSpline'):
            self.vf.loadCommand("splineCommands",
                                "computeSpline", "Pmv",
                                topCommand = 0)
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('extrudeSpline'):
            self.vf.loadCommand("splineCommands",
                                "extrudeSpline", "Pmv",
                                topCommand = 0)
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('displaySpline'):
            self.vf.loadCommand("splineCommands",
                                "extrudeSpline", "Pmv",
                                topCommand = 0)


    def  __call__(self, nodes, only=False, negate=False, **kw):
        """None <- computeExtrudeSpline(nodes, only=False, negate=False, **kw)
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
        #print "in ribbon with only=", only
        apply(self.doitWrapper, (nodes,), kw)

    def doit(self, nodes, **kw):
        if kw!={}:
            if kw['negate']==1:
                apply(self.vf.displayExtrudedSpline,(nodes,), kw)
                return
        apply(self.vf.computeSpline,(nodes,), {'topCommand':False})
        kw['topCommand'] = 0
        apply(self.vf.extrudeSpline,(nodes,), {})        
        

computeSplineCommandGuiDescr = {'widgetType':'Menu',
                                'menuBarName':'menuRoot',
                                'menuButtonName':'Spline',
                                'menuEntryLabel':'Build Spline'}

ComputeSplineGUICommandGUI = CommandGUI()
ComputeSplineGUICommandGUI.addMenuCommand('menuRoot', 'Compute',
                                          'Spline', cascadeName='Spline')
ExtrudeSplineCommandGUI = CommandGUI()
ExtrudeSplineCommandGUI.addMenuCommand('menuRoot', 'Compute',
                                       'Extrude Spline',
                                       cascadeName='Spline')
DisplayExtrudedSplineCommandGUI = CommandGUI()
DisplayExtrudedSplineCommandGUI.addMenuCommand('menuRoot', 'Display',
                                       'Extruded Spline')

computeExtrudeSplineGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                  'menuButtonName':'ComputeExtrude CA Spline',
                  'menuEntryLabel':'ComputeExtrude Spline'}


ComputeExtrudeSplineGUI = CommandGUI()
ComputeExtrudeSplineGUI.addMenuCommand('menuRoot','Compute','ComputeExtrude Spline',cascadeName ='Spline')
customSplineGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                  'menuButtonName':'Custom CA Spline',
                  'menuEntryLabel':'Custom Spline'}


CustomSplineGUI = CommandGUI()
CustomSplineGUI.addMenuCommand('menuRoot','Compute','Custom Spline',cascadeName ='Spline')
DisplaySplineAsLineCommandGUI = CommandGUI()
DisplaySplineAsLineCommandGUI.addMenuCommand('menuRoot', 'Display',
                                             'Spline as Line')


commandList = [
    {'name': 'computeSpline','cmd':ComputeSplineCommand(), 'gui':None},
    {'name': 'computeSplineGC','cmd':ComputeSplineGUICommand(),
     'gui':ComputeSplineGUICommandGUI},
    {'name': 'extrudeSpline','cmd':ExtrudeSplineCommand(),
     'gui':ExtrudeSplineCommandGUI},
    {'name': 'computeExtrudeSpline', 'cmd': ComputeExtrudeSplineCommand(),
    'gui':ComputeExtrudeSplineGUI},
    {'name': 'customSpline', 'cmd': CustomSplineCommand(),
    'gui':CustomSplineGUI},
    {'name': 'displayExtrudedSpline','cmd':DisplayExtrudedSplineCommand(),
     'gui':DisplayExtrudedSplineCommandGUI},
    {'name': 'undisplayExtrudedSpline',
     'cmd':UndisplayExtrudedSplineCommand(), 'gui':None},
    {'name':'displaySplineAsLine','cmd':DisplaySplineAsLineCommand(),
     'gui':DisplaySplineAsLineCommandGUI},
    {'name':'undisplaySplineAsLine','cmd':UndisplaySplineAsLineCommand(),
     'gui':None}
    ]


def initModule(viewer):
    """ initializes commands for secondary structure and extrusion.  Also
    imports the commands for Secondary Structure specific coloring, and
    initializes these commands also. """

    for dict in commandList:
	viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
