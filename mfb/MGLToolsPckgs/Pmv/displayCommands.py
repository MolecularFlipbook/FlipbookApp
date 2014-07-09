## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

###########################################################################
#
# Author: Michel F. SANNER, Sophie COON
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/displayCommands.py,v 1.213.2.4 2012/06/14 19:30:33 rhuey Exp $
# 
# $Id: displayCommands.py,v 1.213.2.4 2012/06/14 19:30:33 rhuey Exp $
#

import warnings
import traceback, math
from types import ListType, TupleType, StringType, IntType, FloatType, LongType, StringType
import Tkinter, Pmw
import string
import numpy
import numpy.oldnumeric as Numeric

from Pmv.mvCommand import MVCommand, MVAtomICOM
from Pmv.stringSelectorGUI import StringSelectorGUI

from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Atom, AtomSet, Molecule, MoleculeSet, BondSet
from MolKit.protein import Protein, Residue, ResidueSet, Chain

from DejaVu.Cylinders import Cylinders
from DejaVu.IndexedPolylines import IndexedPolylines
from DejaVu.Spheres import Spheres
from DejaVu.Points import Points, CrossSet
from DejaVu.Geom import Geom

from ViewerFramework.VFCommand import CommandGUI
from Pmv.moleculeViewer import DeleteAtomsEvent, AddAtomsEvent, EditAtomsEvent, ShowMoleculesEvent
from Pmv.moleculeViewer import DeleteGeomsEvent, AddGeomsEvent, EditGeomsEvent

from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from mglutil.util.misc import ensureFontCase

from mglutil.gui.InputForm.Tk.gui import InputFormDescr, evalString
from mglutil.util.callback import CallBackFunction
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ExtendedSliderWidget, ListChooser
import types

import Pmv
if hasattr( Pmv, 'numOfSelectedVerticesToSelectTriangle') is False:
    Pmv.numOfSelectedVerticesToSelectTriangle = 1


class DisplayCommand(MVCommand, MVAtomICOM):
    """The DisplayCommand class is the base class from which all the display commands implemented for PMV will derive.It implements the general functionalities to display/undisplay parts of a geometry representing a molecule.
    \nPackage : Pmv
    \nModule  : displayCommands
    \nClass   : DisplayCommand
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        MVAtomICOM.__init__(self)
        self.flag = self.flag | self.objArgOnly
        self.flag = self.flag | self.negateKw


    def setLastUsedValues(self, formName=None, **kw):
        """Special handling of display widget based on values of only and
negate in self.lastUsedValues
"""
        form = None
        if len(self.cmdForms):
            if formName is None:
                form = self.cmdForms.values()[0]
            else:
                form = self.cmdForms.get(formName, None)

            if kw.has_key('only') and kw['only']:
                disp = 'display only'
                del kw['only']
            elif  kw.has_key('negate') and kw['negate']:
                disp = 'undisplay'
                del kw['negate']
            else:
                disp = 'display'
            widget = form.descr.entryByName['default']['widget']
            widget.invoke(disp)
        apply(MVCommand.setLastUsedValues, (self, formName), kw)


    def handleNegateOnly(self):
        """return the values to be used for the display widget based on the
negate and only values in self.lastUsedValues
"""
        if self.lastUsedValues['default']['only']:
            disp = 'display only'
        elif self.lastUsedValues['default']['negate']:
            disp = 'undisplay'
        else:
            disp = 'display'

        return disp


    def getLastUsedValues(self, formName='default', **kw):
        """Return dictionary of last used values
"""
        values = self.lastUsedValues[formName].copy()
        return self.handleDisplayValue(values)
    

    def handleDisplayValue(self, val):
        # creates the only and negate keywords based on the 'display' entry
        if val.has_key('display'):
            if val['display']=='display':
                val['only']= False
                val['negate'] = False
                del val['display']
            elif val['display']=='display only':
                val['only']= True
                val['negate'] = False
                del val['display']
            elif val['display']== 'undisplay':
                val['negate'] = True
                val['only'] = False
                del val['display']
            val['redraw'] = True
        return val


    def onAddCmdToViewer(self):
        self.vf.registerListener(DeleteAtomsEvent, self.updateGeom)
        self.vf.registerListener(AddAtomsEvent, self.updateGeom)
        self.vf.registerListener(EditAtomsEvent, self.updateGeom)


    def updateGeom(self, event):
        """Function to update geometry objects created by this command
upon Modification events.  This function is called by the
the ViewerFramework.dispatchEvent command.
The function will compute the a set of atoms by combining
the atoms currently used to display the geometry (i.e.
adding or substracting event.objects for action =='add' or
'delete', then execute this command for the set of
atoms.
\nevent --- instance of a VFEvent object
"""
        if isinstance(event, AddAtomsEvent):
            action='add'
        elif isinstance(event, DeleteAtomsEvent):
            action='delete'
        elif isinstance(event, EditAtomsEvent):
            action='edit'
        else:
            import warnings
            warnings.warn('Bad event %s for DisplayCommand.updateGeom'%event)
            return
        
        geomList = self.managedGeometries

        # split event.objects into atoms sets per molecule
        molecules, ats = self.vf.getNodesByMolecule(event.objects)

        # build list of optional command arguments
        doitoptions = self.lastUsedValues['default']
        doitoptions['redraw']=1
        doitoptions['topCommand']=0
        if not self.vf.hasGui :
            doitoptions['log']=1
        # allAts is the set of atoms for which we will invoke this command
        allAts = AtomSet([])

        # loop over molecules to update geometry objects
        for mol, atomSets in zip(molecules, ats):

            # loop over the geometry objects
            for geom in geomList:
                # get the list of atoms currently displayed with this geom
                atoms = mol.geomContainer.atoms[geom.name]
                if len(atoms)==0:
                    continue
                # handle event.action
                if action=='delete':
                    changed = atoms.inter(atomSets)
                    doitoptions['negate'] = 1
                    if len(changed):
                        apply(self.doitWrapper,(changed,), doitoptions)
                    doitoptions['negate'] = 0
                else:
                    if action == 'add':
                        allAts = allAts + atoms + atomSets
                    elif action == 'edit':
                        if len(allAts)==0:
                            allAts = atoms
                        else:
                            allAts = allAts.union(atoms)

        ## if there are atoms to be displayed in geoemtries created by this
        ## command, invoke the command
        if len(allAts):
            apply(self.doitWrapper,(allAts,), doitoptions)
            
        ## FIXME not sure we need this !
        try:
            self.cleanup()
        except:
            pass


    def getNodes(self, nodes):
        """expand nodes argument into a list of atoms sets and a list of
        molecules.\n
        This function is used to prevent the expansion operation to be done in both doit and setupUndoBefore The nodes.findType( Atom ) is the operation that is potentially expensive.\n
        """
        #import pdb;pdb.set_trace()
        if not hasattr(self, 'expandedNodes____AtomSets'):
            mol, atms = self.vf.getNodesByMolecule(nodes, Atom)
            self.expandedNodes____AtomSets = atms
            self.expandedNodes____Molecules = mol

        return self.expandedNodes____Molecules, \
               self.expandedNodes____AtomSets


    def buildFormDescr(self, formName='default', title=None):
        if formName == 'default':
            if title is None:
                title = self.name
            idf =  InputFormDescr(title=title)
            idf.name = formName
            idf.append({'name':'display',
                        'widgetType':Pmw.RadioSelect,
                        'tooltip':"display only: display the selection and undisplay the non selected part of the molecule",
                        'listtext':['display','display only', 'undisplay'],
                        'defaultValue': self.handleNegateOnly(),
                        'wcfg':{'orient':'horizontal',
                                'buttontype':'radiobutton'},
                        'gridcfg':{'sticky': 'we'}})
            return idf


    def getFormValues(self):
        val = self.showForm()

        if val:
            if val['display']=='display':
                val['only']= False
                val['negate'] = False
                del val['display']
            elif val['display']=='display only':
                val['only']= True
                val['negate'] = False
                del val['display']
            elif val['display']== 'undisplay':
                val['negate'] = True
                val['only'] = False
                del val['display']
                
            val['redraw'] = True

        return val
        

    def guiCallback(self):
        nodes = self.vf.getSelection()
        if not nodes: return
        val = self.getFormValues()
        if val:
            apply( self.doitWrapper, (nodes,), val )



class DisplayLines(DisplayCommand):
    """The displayLines allows the user to display/undisplay the selected nodes using a lines for bonded atoms, dots for non bonded atoms and doted lines for an aromatic ring. The number of lines when representing a bond will vary depending on the bondOrder.
    \nPackage : Pmv
    \nModule  : displayCommands
    \nClass   : DisplayLines
    \nCommand : displayLines
    \nSynopsis:\n
    None <--- displayLines(self, nodes, lineWidth=2, displayBO = 1, only = 0,
                         negate = 0, **kw)\n
    \nRequired Arguments:\n
    nodes --- any set of MolKit nodes describing molecular components\n

    \nOptional Arguments:\n
    lineWidth --- int specifying the width of the lines, dots or doted lines
                 representing the selection. (default = 2)\n
    displayBO --- boolean flag specifying whether or not to display the
                 bond order (default = False)\n
    only   --- boolean flag specifying whether or not to display only the
                 current selection. (default = False)\n
    negate --- boolean flag  specifying whether or not to negate the current
                 selection. (default = False)\n
                 

    keywords: display wireframe, lines, bond order, non bonded atoms.
    """
    

    def onAddObjectToViewer(self, obj):
        """
        Creates the lines, the points , the dotted lines and the bond order
        lines geometries and add these new geometries to the
        geomContainer.geoms of the new molecule.
        New AtomSet are created as well and added to the geomContainer.atoms
        """
        if self.vf.hasGui and self.vf.commands.has_key('dashboard'):
            self.vf.dashboard.resetColPercent(obj, '_showLinesStatus')

        #if not self.vf.hasGui: return
        geomC = obj.geomContainer
        vi = geomC.VIEWER
        # lines representation needs 4 different geometries need to create
        # a master geometrie Geom.
        #wire = geomC.geoms['lines'] = Geom('lines',  shape=(0,0))
        if not geomC.geoms.has_key('lines'):
            wire = Geom('lines',
                        shape=(0,0),
                        inheritLighting=False,
                        lighting=False,
                        protected=True)
            
        else:
            wire = geomC.geoms['lines']
        geomC.addGeom(wire, parent=geomC.masterGeom, redo=0 )    

        geomC.atomPropToVertices["bonded"] = self.atomPropToVertices
        geomC.atomPropToVertices["nobnds"] = self.atomPropToVertices
        #geomC.atomPropToVertices["sharedbonds"] = self.atomPropToVertices
        geomC.atomPropToVertices["bondorder"] = self.atomPropToVertices

        # lines: Bonded atoms are represented by IndexedPolyLines
        l = IndexedPolylines("bonded", 
                             vertices=geomC.allCoords, 
                             visible=0,
                             pickableVertices=1,
                             inheritMaterial=1,
                             protected=True,
                             disableStencil=True,
                             transparent=True
                             )
        geomC.addGeom(l, parent=wire, redo=0)
        self.managedGeometries.append(l)
               
        # nobnds : Non Bonded atoms are represented by Points
        p = Points( "nobnds", shape=(0,3), visible=0,
                    inheritMaterial=1, protected=True,
                    disableStencil=True,
                    transparent=True
                    )
        
        geomC.addGeom( p, parent=wire, redo=0)
        self.managedGeometries.append(p)
        b = IndexedPolylines('bondorder', visible=0,
                             inheritMaterial=1, protected=True,
                             disableStencil=True,
                             transparent=True
                             )
        
        geomC.addGeom( b, parent=wire, redo=0 )
        self.managedGeometries.append(b)
        
        # shared bonds are represented by dotted lines.
##         a = IndexedPolylines('sharedbonds', visible=0, lineWidth=3,
##                              inheritMaterial=0, stipleLines=1)
##         vi.AddObject(a, parent=wire, replace=True, redo=0)
##         geomC.addGeom(p)
##         self.managedGeometries.append(p)
        
        
        # Create the entry 'lines' and 'nobnds' in the atom.colors dictionary
        for atm in obj.allAtoms:
            atm.colors['lines'] = (1.0, 1.0, 1.0)



    def atomPropToVertices(self, geom, atms, propName, propIndex=None):
        """Function called to compute the array of properties"""
        if atms is None or len(atms)==0 : return None
        prop = []
        if propIndex == 'bondorder':
            mol = geom.mol
            atms = mol.geomContainer.atoms['bondorder']

        propIndex = 'lines'
        for a in atms:
            d = getattr(a, propName)
            prop.append( d[propIndex] )
        return prop


    def setupUndoBefore(self, nodes, only=False, negate=False, displayBO=False,
                        lineWidth=2):
        kw = {}
        #kw['displayBO'] = displayBO
        kw['lineWidth'] = self.lastUsedValues['default']['lineWidth']
        kw['redraw'] = True
        geomSet = []
        boSet = []
        for mol in self.vf.Mols:
            geomSet = geomSet + mol.geomContainer.atoms['bonded']
            boSet = boSet + mol.geomContainer.atoms['bondorder'].uniq()
        if len(boSet) == 0:
            kw['displayBO']=False
        else:
            kw['displayBO']=True
        if len(geomSet) == 0:
            # The undo of a display command is undisplay what you just
            # displayed if nothing was displayed before.
            kw['negate'] = True
            kw['displayBO'] = False
            self.addUndoCall( (nodes,), kw, self.name)
        else:
            # The undo of a display command is to display ONLY what was
            # displayed before, if something was already displayed
            kw['only'] = True
            self.addUndoCall( (geomSet,), kw, self.name)

##         # we overwrite setupUndoBefore enven though this command implements
##         # the negate kw because the only kw would not be handled properly
##         molecules, atomSets = self.getNodes(nodes)
##         for mol, atm in map(None, molecules, atomSets):
##             # set is the atoms part of a bonds and displayed as lines and 
##             # the atoms not part of a bond and displayed as points
##             set = mol.geomContainer.atoms['bonded']
##             if len(set)==0: # nothing is displayed
##                 kw = {}
##                 kw['negate'] = True
##                 kw['redraw'] = True
##                 kw['displayBO'] = not displayBO
                
##                 self.addUndoCall( (mol,), kw, self.name )
##             else:
##                 kw={}
##                 kw['only'] = True
##                 kw['redraw'] = True
##                 kw['displayBO'] = not displayBO
##                 kw['lineWidth'] = lineWidth
##                 self.addUndoCall( (set,), kw, self.name )


    def __call__(self, nodes, lineWidth=2, displayBO=False, only=False,
                 negate=False, **kw):
        """None <- displayLinesBO(self, nodes, lineWidth=2, displayBO=False,only=False, negate=False, **kw)\n
        \nRequired Arguments:\n
        nodes --- any set of MolKit nodes describing molecular components\n

        \nOptional Arguments:\n
        lineWidth --- int specifying the width of the lines, dots or doted lines
                     representing the selection. (default = 2)\n
        displayBO --- boolean flag specifying whether or not to display the
                     bond order (default = False)\n
        only --- boolean flag specifying whether or not to display only
                     the current selection. (default = False)\n
        negate --- boolean flag specifying whether or not to negate the
                     current selection. (default = False)\n
        """
        if not (type(lineWidth) in [IntType, FloatType] and lineWidth>0):
            return 'ERROR'
        kw['lineWidth'] = lineWidth
        kw['displayBO'] = displayBO
        kw['only'] = only
        kw['negate'] = negate
        kw['redraw'] = True
        if type(nodes) is StringType:
            self.nodeLogString = "'" + nodes +"'"
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return
        apply(self.doitWrapper, (nodes,), kw)

        
    def doit(self, nodes, lineWidth=2, displayBO=False , only=False,
             negate=False, **kw):

        #print 'DISPLAY LINES'
        ###################################################################
        def drawAtoms(mol, atm, displayBO, lineWidth, only, negate):
            """ Function to represent the given atoms as lines if they are
            bonded and points otherwise"""
            ggeoms = mol.geomContainer.geoms
            gatoms = mol.geomContainer.atoms
            # DISPLAY BONDED ATOMS AND NOBNDS ATOMS

            # special case all atoms in the molecule for efficiency
            if len(atm) == len(mol.allAtoms): #atm is all atoms in mol
                if negate:
                    _set = AtomSet() # evrythign gets undisplayed
                    setOff = atm
                    setOn = None
                else:
                    _set = atm
                    setOff = None
                    setOn = atm

            else: # atm is a subset of mol's atoms
                _set = gatoms['bonded']
                setnobnds = gatoms['nobnds']
                if negate: #if negate, remove current atms from displayed _set
                    setOff = atm
                    setOn = None
                    _set = _set - atm

                else:     #if only, replace displayed _set with current atms 
                    if only:
                        setOff = _set - atm
                        setOn = atm
                        _set = atm
                    else: 
                        _set = atm + _set
                        setOff = None
                        setOn = _set

            # Update geoms lines and nobnds with new information.
            # If no lines then donnot display bondorder.
            if len(_set)==0:
                ggeoms['bonded'].Set(faces=[], vertices=[], tagModified=False)
                gatoms['bonded'] = _set
                ggeoms['nobnds'].Set(vertices=[], tagModified=False)
                gatoms['nobnds'] = _set
                return setOn, setOff
            # This is done only if _set contains some atoms.
            bonds, atnobnd = _set.bonds

            # 1st lines need to store the whole _set in the
            # mol.geomContainer.atoms['lines'] because of the picking.
            gatoms['bonded'] = _set

            if len(bonds) == 0:
                ggeoms['bonded'].Set(faces=[], vertices=[], tagModified=False)
            else:
                # need the indices for the indexedPolylines
                indices = map(lambda x: (x.atom1._bndIndex_,
                                         x.atom2._bndIndex_), bonds)
                if len(indices)==0:
                    ggeoms['bonded'].Set(visible=0, tagModified=False)
                else:
                    colors = map(lambda x: x.colors['lines'], _set)
                    ggeoms['bonded'].Set( vertices=_set.coords,
                                          faces=indices,
                                          materials = colors,
                                          lineWidth=lineWidth,
                                          inheritLineWidth=False,
                                          visible=1,
                                          tagModified=False,
                                          inheritMaterial=False)
            # the nobnds
            gatoms['nobnds']= atnobnd
            if len(atnobnd)==0:
                ggeoms['nobnds'].Set(vertices=[], tagModified=False)
            else:
                vertices = atnobnd.coords
                colors = map(lambda x: x.colors['lines'], atnobnd)
                ggeoms['nobnds'].Set(vertices=vertices,
                                     pointWidth=lineWidth,
                                     materials = colors,
                                     visible=1, inheritMaterial=False, 
                                     tagModified=False)
                
            #DISPLAY BOND ORDER.
            if not displayBO:
                setBo = AtomSet()

            else:
                if len(atm) == len(mol.allAtoms):
                    if negate:
                        setBo = AtomSet()
                    else:
                        setBo = atm

                else:
                    setBo = gatoms['bondorder'].uniq()
                    if negate:
                        # if negate, remove current atms from displayed set
                        setBo = mol.allAtoms - atm
                    else:
                        # if only, replace displayed set with
                        # current atms 
                        if only:
                            setBo = atm
                        else: 
                            setBo = mol.allAtoms
            
            if len(setBo) == 0:
                ggeoms['bondorder'].Set(vertices=[], tagModified=False)
                gatoms['bondorder'] = setBo
                return setOn, setOff
            
            bonds = setBo.bonds[0]

            # Get only the bonds with a bondOrder greater than 1
            bondsBO= BondSet(filter(lambda x: not x.bondOrder is None and \
                                    x.bondOrder>1, bonds)) 
            if not bondsBO: return setOn, setOff
            withVec = filter(lambda x: not hasattr( x.atom1, 'dispVec') \
                             and not hasattr(x.atom2, 'dispVec'),bondsBO)
            if len(withVec):
                map(lambda x: x.computeDispVectors(), bondsBO)

            vertices = []
            indices = []
            col = []
            i = 0
            realSet  = AtomSet([])
            ar = Numeric.array
            for b in bonds:
                bondOrder = b.bondOrder
                if bondOrder == 'aromatic' : bondOrder = 2
                if not bondOrder > 1: continue

                at1 = b.atom1
                at2 = b.atom2
                if (not hasattr(at1, 'dispVec') \
                    and not hasattr(at2, 'dispVec')):
                    continue
                realSet.append(at1)
                realSet.append(at2)

                nc1 = ar(at1.coords) + \
                      ar(at1.dispVec)
                nc2 = ar(at2.coords) + \
                      ar(at2.dispVec)
                vertices.append(list(nc1))
                vertices.append(list(nc2))
                indices.append( (i, i+1) )
                i = i+2
            gatoms['bondorder'] = realSet
            #col = mol.geomContainer.getGeomColor('bondorder')
            ggeoms['bondorder'].Set( vertices=vertices, 
                                     faces=indices,
                                     visible=1,
                                     lineWidth=lineWidth,
                                     tagModified=False)
            return setOn, setOff
        
        ##################################################################
        molecules, atomSets = self.getNodes(nodes)
        setOn = AtomSet([])
        setOff = AtomSet([])
        for mol, atms, in map(None, molecules, atomSets):
            # Get the set of atoms currently represented as wireframe
            geomC = mol.geomContainer
            son, sof = drawAtoms(mol, atms, displayBO, lineWidth, only, negate)
            if son: setOn += son
            if sof: setOff += sof

        if only and len(molecules) != len(self.vf.Mols):
            mols = self.vf.Mols - molecules
            for mol in mols:
                only=0
                negate=1
                drawAtoms(mol, mol.allAtoms, displayBO, lineWidth, only,
                          negate)
        redraw = False
        if kw.has_key("redraw") : redraw=True
        if self.createEvents:
            event = EditGeomsEvent(
                'lines', [nodes,[lineWidth, only, negate,redraw]],
                setOn=setOn, setOff=setOff)
            self.vf.dispatchEvent(event)


    def buildFormDescr(self, formName='default'):
        if formName == 'default':
            idf = DisplayCommand.buildFormDescr(
                self, formName, title='Display Lines:')

            defaultValues = self.lastUsedValues['default']

            idf.append({'name':'displayBO',
                        'widgetType':Tkinter.Checkbutton,
                        'defaultValue': defaultValues['displayBO'],
                        'wcfg':{'text': 'show BondOrder',
                                'variable': Tkinter.IntVar()},
                        'gridcfg':{'sticky':'w'}})

            idf.append({'name':'lineWidth',
                        'widgetType':ExtendedSliderWidget,
                        'wcfg':{'label': 'Line Width',
                                'minval':1,'maxval':10 ,
                                'init': defaultValues['lineWidth'],
                                'labelsCursorFormat':'%d',
                                'sliderType':'int',
                                'entrywcfg':{'width':4},
                                'entrypackcfg':{'side':'right'}},
                        'gridcfg':{'columnspan':2,'sticky':'we'}})


            return idf


    def guiCallback(self):
        nodes = self.vf.getSelection()
        if not nodes: return
        val = DisplayCommand.getFormValues(self)
        if val:
            if val['displayBO'] == 1: val['displayBO'] = True
            else:
                val['displayBO'] = False
            apply( self.doitWrapper, (nodes,), val)
        

    def onRemoveObjectFromViewer(self, mol):
       """Function to remove the sets able to reference a TreeNode created
       in this command : Here remove bbDisconnectedAfter created for each
       chains  and bonds created for each elements of each level in
       buildBondsByDistance."""
       if self.vf.undoableDelete__: return
       levels = mol.levels
       for l in levels:
           try:
               levelNodes = mol.findType(l)
               for n in levelNodes:
                   if hasattr(n, 'bbDisconnectedAfter'):
                       del n.bbDisconnectedAfter
                   if hasattr(n, 'bonds'):
                       del n.bonds
           except:
               print "exception displayCommands line 712"
       del levelNodes


    def cleanup(self):
        """
        Method called by afterDoit to cleanup things eventhough doit failes
        """
        #print 'dl: in cleanup'
        del self.expandedNodes____AtomSets
        del self.expandedNodes____Molecules


displayLinesGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                       'menuButtonName':'Display', 'menuEntryLabel':
                       'Lines' }

DisplayLinesGUI = CommandGUI()
DisplayLinesGUI.addMenuCommand('menuRoot', 'Display', 'Lines')


class UndisplayLines(DisplayCommand):
    """The undisplayLines command is a picking command allowing the user to undisplay the lines geometry representing the picked nodes.This command can also be called from the Python shell with a set of nodes.
    \nPackage : Pmv
    \nModule  : displayCommands
    \nClass   : UnDisplayLines
    \nCommand : undisplayLines
    \nSynopsis:\n
        None <- undisplayLines(nodes, **kw)\n
        nodes --- any set of MolKit nodes describing molecular components\n
        keywords --- undisplay, lines\n
    """

    def onAddCmdToViewer(self):
        DisplayCommand.onAddCmdToViewer(self)
        #if not self.vf.hasGui: return 
        if not self.vf.commands.has_key('displayLines'):
            self.vf.loadCommand('displayCommands', ['displayLines'], 'Pmv',
                                topCommand=0)

    def __call__(self, nodes, **kw):
        """None <- undisplayLines(nodes, **kw)
           nodes: TreeNodeSet holding the current selection"""
        if not nodes: return
        kw['negate']=1
        kw['redraw']=1
        if type(nodes) is StringType:
            self.nodeLogString = "'" + nodes +"'"
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return
        apply(self.vf.displayLines, (nodes,), kw)


class DisplayCPK(DisplayCommand):
    """ The displayCPK command allows the user to display/undisplay the given nodes using a CPK representation, where each atom is represented with a sphere. A scale factor and the quality of the spheres are user
    defined parameters.
    \nPackage : Pmv
    \nModule  : displayCommands
    \nClass   : DisplayCPK
    \nCommand : displayCPK
    \nSynopsis:\n
        None <- displayCPK(nodes, only=False, negate=False, 
                           scaleFactor=None, quality=None, **kw)\n
        nodes --- any set of MolKit nodes describing molecular components\n
        only --- Boolean flag specifying whether or not to only display
                     the current selection\n
        negate --- Boolean flag specifying whether or not to undisplay
                     the current selection\n
        scaleFactor --- specifies a scale factor that will be applied to the atom
                     radii to compute the spheres radii. (default is 1.0)\n
        quality  --- specifies the quality of the spheres. (default 10)\n
        keywords --- display, CPK, space filling, undisplay.\n
    """

        
    def onAddCmdToViewer(self,):
        DisplayCommand.onAddCmdToViewer(self)

        if self.vf.hasGui:
            self.showAtomProp = Tkinter.IntVar()
            self.showAtomProp.set(0)

        if not self.vf.commands.has_key('assignAtomsRadii'):
            self.vf.loadCommand('editCommands', 'assignAtomsRadii', 'Pmv',
                                topCommand=0)
        from MolKit.molecule import Molecule, Atom
        from MolKit.protein import Protein, Residue, Chain
        from mglutil.util.colorUtil import ToHEX
        self.molDict = {'Molecule':Molecule,
                        'Atom':Atom, 'Residue':Residue, 'Chain':Chain}
        self.nameDict = {Molecule:'Molecule', Atom:'Atom', Residue:'Residue',
                         Chain:'Chain'}

        self.leveloption={}
        for name in ['Atom', 'Residue', 'Molecule', 'Chain']:
            col = self.vf.ICmdCaller.levelColors[name]
            bg = ToHEX((col[0]/1.5,col[1]/1.5,col[2]/1.5))
            ag = ToHEX(col)
            self.leveloption[name]={#'bg':bg,
                                    'activebackground':bg, 'selectcolor':ag ,
                                    'borderwidth':3 , 'width':15}
        self.propValues = None
        self.getVal = 0
        self.propertyLevel = self.nameDict[self.vf.selectionLevel]

        

    def onAddObjectToViewer(self, obj):
        """Adds the cpk geometry and the cpk Atomset to the object's
        geometry container
        """
        if self.vf.hasGui and self.vf.commands.has_key('dashboard'):
            self.vf.dashboard.resetColPercent(obj, '_showCPKStatus')

        #if not self.vf.hasGui: return
        obj.allAtoms.cpkScale = 1.0
        obj.allAtoms.cpkRad = 0.0
        geomC = obj.geomContainer
        # CPK spheres
        g = Spheres( "cpk", quality=0 ,visible=0, protected=True)
        geomC.addGeom(g, parent=geomC.masterGeom, redo=0)
        self.managedGeometries.append(g)
        geomC.geomPickToBonds['cpk'] = None
        for atm in obj.allAtoms:
            atm.colors['cpk'] = (1.0, 1.0, 1.0)
            atm.opacities['cpk'] = 1.0


    def setupUndoBefore(self, nodes, only=False, negate=False, scaleFactor=1.0,
                        cpkRad=0.0, quality=0, byproperty = False,
                        propertyName = None, propertyLevel = 'Molecule',
                        setScale=True):

        #print "in setupUndoBefore: only= ", only, "negate=", negate, "scaleFactor=", scaleFactor, "cpkRad=", cpkRad, "quality=", quality, "property = ", propertyName, "propertyLevel = ", propertyLevel

        kw = self.getLastUsedValues()
        kw['redraw'] = True
        #print "kw:", kw
        geomSet = []
        for mol in self.vf.Mols:
            geomSet = geomSet + mol.geomContainer.atoms['cpk']

        if len(geomSet) == 0:
            # If nothing was displayed before, the undo of a display
            # command is to undisplay what you just displayed 
            kw['negate'] = True
            self.addUndoCall( (nodes,), kw, self.name)
        else:
            # If the current was already displayed and only is False and negate
            # is False then the undo is to display this set using the last used
            # values.
            
            # If something was already displayed, the undo of a display
            # command is to display ONLY what was displayed before.
            kw['only'] = True
            self.addUndoCall( (geomSet,), kw, self.name)


    def getLastUsedValues(self, formName='default', **kw):
        vals = apply(DisplayCommand.getLastUsedValues, (self, formName), kw)
        if vals.has_key('byproperty'):
            if vals['byproperty']:
                if vals.has_key('quality1'):
                    vals['quality']= vals.pop('quality1')
                if vals.has_key('scaleFactor1'):
                    vals['scaleFactor'] = vals.pop('scaleFactor1')
                if vals.has_key('offset'):
                    vals['cpkRad'] = vals.pop('offset')
                vals['propertyLevel'] = self.propertyLevel
            else:
                if vals.has_key('quality1'):
                    vals.pop('quality1')
                if vals.has_key('scaleFactor1'):
                    vals.pop('scaleFactor1')
                if vals.has_key('propertyName'):
                    vals.pop('propertyName')
                if vals.has_key('propertyLevel'):
                    vals.pop('propertyLevel')
                if vals.has_key('offset'):
                    vals.pop('offset')
        return vals
    

    def doit(self, nodes, only=False, negate=False, 
             scaleFactor=1.0, cpkRad=0.0, quality=0,  byproperty = False,
             propertyName=None, propertyLevel='Molecule', setScale=True, **kw):

        ##############################################################
        def drawAtoms( mol, atm, only, negate, scaleFactor, cpkRad, quality,
                       propertyName = None, propertyLevel="Molecule",
                       setScale=True):

            if setScale:
                atm.cpkScale = scaleFactor
                atm.cpkRad = cpkRad
            _set = mol.geomContainer.atoms['cpk']
            if len(atm) == len(mol.allAtoms):
                if negate:
                    setOff = atm
                    setOn = None
                    _set = AtomSet()
                else:
                    _set = atm
                    setOff = None
                    setOn = atm
            else:
                ##if negate, remove current atms from displayed _set
                if negate:
                    setOff = atm
                    setOn = None
                    _set = _set - atm

                ##if only, replace displayed _set with current atms 
                else:
                    if only:
                        setOff = _set - atm
                        setOn = atm
                        _set = atm
                    else: 
                        _set = atm + _set
                        setOff = None
                        setOn = _set

            mol.geomContainer.atoms['cpk']=_set

            g = mol.geomContainer.geoms['cpk']
            if len(_set)==0: 
                g.Set(visible=0, tagModified=False)
            else:
                _set.sort()   # EXPENSIVE...
                colors = map(lambda x: x.colors['cpk'], _set)
                cd = {}.fromkeys(['%f%f%f'%tuple(c) for c in colors])
                if len(cd)==1:
                    colors = [colors[0]]

                cpkSF = Numeric.array(_set.cpkScale)
                if propertyName:
                    atmRadOld = atm.radius[:]
                    propvals = Numeric.array(self.getPropValues(atm, propertyName, propertyLevel), "f")
                    atm.radius = propvals

                atmRad = Numeric.array(_set.radius)
                cpkRad = Numeric.array(_set.cpkRad)
                sphRad = cpkRad + cpkSF*atmRad
                sphRad = sphRad.tolist()
                if propertyName:
                    atm.radius = atmRadOld
                g.Set(vertices=_set.coords, inheritMaterial=False, 
                      materials=colors, radii=sphRad, visible=1,
                      quality=quality, tagModified=False)
                
                # highlight selection
                selMols, selAtms = self.vf.getNodesByMolecule(self.vf.selection, Atom)
                lMolSelectedAtmsDict = dict( zip( selMols, selAtms) )
                lSelectedAtoms = lMolSelectedAtmsDict.get(mol, None)
                if lSelectedAtoms is not None:
                    lVertexClosestAtomSet = mol.geomContainer.atoms['cpk']
                    if len(lVertexClosestAtomSet) > 0:
                        lVertexClosestAtomSetDict = dict(zip(lVertexClosestAtomSet,
                                                             range(len(lVertexClosestAtomSet))))
                        highlight = [0] * len(lVertexClosestAtomSet)
                        for i in range(len(lSelectedAtoms)):
                            lIndex = lVertexClosestAtomSetDict.get(lSelectedAtoms[i], None)
                            if lIndex is not None:
                                highlight[lIndex] = 1
                        g.Set(highlight=highlight)
            return setOn, setOff
        
        ##################################################################
                
        molecules, atmSets = self.getNodes(nodes)
        setOn = AtomSet([])
        setOff = AtomSet([])
        try:
            radii = molecules.allAtoms.radius
        except:
            self.vf.assignAtomsRadii(molecules, 
                                     overwrite=False, topCommand=False)

        for mol, atms in map(None, molecules, atmSets):
            if byproperty:
                son, sof = drawAtoms(
                    mol, atms, only, negate, scaleFactor, cpkRad,
                    quality, propertyName, propertyLevel,setScale=setScale)
            else:
                son, sof = drawAtoms(mol, atms, only, negate, 
                                     scaleFactor, cpkRad, quality,
                                     setScale=setScale)
            if son: setOn += son
            if sof: setOff += sof

        if only and len(molecules)!=len(self.vf.Mols):
            mols = self.vf.Mols - molecules
            for mol in mols:
                only = False
                negate = True
                if byproperty:
                    son, sof = drawAtoms(
                        mol, mol.allAtoms, only, negate, scaleFactor, cpkRad,
                        quality, propertyName, propertyLevel, setScale)
                else:
                    son, sof = drawAtoms(mol, mol.allAtoms, only, negate, 
                                         scaleFactor, cpkRad, quality,
                                         setScale=setScale)
                if son: setOn += son
                if sof: setOff += sof
                
        redraw = False
        if kw.has_key("redraw") : redraw=True
        if self.createEvents:
            event = EditGeomsEvent(
            'cpk', [nodes,[only, negate,scaleFactor,cpkRad,quality,
                           byproperty,propertyName, propertyLevel,redraw]],
                                    setOn=setOn, setOff=setOff)
            self.vf.dispatchEvent(event)

        
    def cleanup(self):
        if hasattr(self, 'expandedNodes____AtomSets'):
            del self.expandedNodes____AtomSets
        if hasattr(self, 'expandedNodes____Molecules'):
            del self.expandedNodes____Molecules


    def __call__(self, nodes, only=False, negate=False, 
                 scaleFactor=1.0,  cpkRad=0.0, quality=0,  byproperty = False, propertyName = None,
                 propertyLevel = 'Molecule', setScale=True, **keywords):
        """None <- displayCPK(nodes, only=False, negate=False,scaleFactor=None, cpkRad=0.0, quality=None, propertyName = None, propertyLevel = 'Molecule', **kw)
           \nnodes --- TreeNodeSet holding the current selection
           \nonly --- Boolean flag when True only the current selection will be
                    displayed
           \nnegate --- Boolean flag when True undisplay the current selection
           \nscaleFactor --- value used to compute the radii of the sphere representing the atom (Sphere Radii = cpkRad + atom.radius * scaleFactor (default is 1.0)
           \ncpkRad --- value used to compute the radii of the sphere representing the atom (Sphere Radii = cpkRad + atom.radius * scaleFactor (default 0.0)
           \nquality --- sphere quality default value is 10
           \npropertyName --- if specified,  the property is used to compute the sphere radii (Sphere Radii = cpkRad + property * scaleFactor),
           \npropertyLevel --- can be one of the following: 'Atom', 'Residue', 'Chain', 'Molecule'.
           \nsetScale --- when true atm.scaleFactor and atm.cpkRad are set"""

        #print "in __call__: only= ", only, "negate=", negate, "scaleFactor=", scaleFactor, "cpkRad=", cpkRad, "quality=", quality, "property = ", propertyName, "propertyLevel = ", propertyLevel, "kw:", keywords, "nodes:", nodes
        kw = {}
        if not keywords.has_key('redraw'): kw['redraw'] = True
        if not type(scaleFactor) in [IntType, FloatType,
                                    LongType]: return 'ERROR'
        if not isinstance(quality, IntType) and quality>=0:
            return 'ERROR'
        kw['only'] = only
        kw['negate'] = negate
        kw['scaleFactor'] = scaleFactor
        kw['cpkRad'] = cpkRad
        kw['quality'] = quality
        kw['setScale']= setScale
        if propertyName is not None:
            if type(propertyName) != types.StringType:
                propertyName = propertyName[0]
            kw['propertyName'] = propertyName
            kw['propertyLevel']= propertyLevel
            byproperty = True
            kw['byproperty'] = byproperty
        else:
            byproperty = False

        if type(nodes) is StringType:
            self.nodeLogString = "'" + nodes +"'"
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return
        kw.update(keywords)
        apply( self.doitWrapper, (nodes,), kw)
        
        #if self.showAtomProp.get() != byproperty:
        #   self.showAtomProp.set(byproperty)
        self.lastUsedValues['default']['byproperty'] = byproperty
        self.lastUsedValues['default']['propertyName'] = propertyName
        


    def updateLevel_cb(self, tag):
        if tag != self.propertyLevel:
            self.propertyLevel = tag
            
        #if self.molDict[tag]  != self.vf.ICmdCaller.level.value:
            #self.vf.setIcomLevel(self.molDict[tag])
            #force a change of selection level too in order to get
            #list of property values at 'tat' level
            #self.vf.setSelectionLevel(self.molDict[tag])

            lSelection = self.vf.getSelection().uniq().findType(
                self.molDict[tag]).uniq()
            lSelection.sort()
            self.updateChooser(lSelection)


    def buildFormDescr(self, formName='default'):
        # Need to create the InputFormDescr here if there is a gui.
        if formName == 'default':
            idf = DisplayCommand.buildFormDescr(
                self, formName, title ="Display CPKs:")

            defaultValues = self.lastUsedValues['default']
            idf.append({'name': 'byproperty',
                        'widgetType': Tkinter.Checkbutton,
                        'tooltip': 'allows the user to specify a property used to display/undisplay selected nodes using CPK representation',
                        'wcfg': {'text': 'By property',
                                 'variable': self.showAtomProp,
                                 'command': self.toggleInputByProp},
                        'gridcfg':{'sticky':'w'}} )
            idf.append({'name':'radiiGroup', #'cpkradii',
                        'widgetType':Pmw.Group,
                        'container':{'radiiGroup':"w.interior()"},
                        
                        'wcfg':{'ring_borderwidth':3,},
                        'gridcfg':{'sticky':'we', 'columnspan':1}})
            idf.append({'name':'cpkRad',
                        'parent':'radiiGroup',
                        'widgetType':ThumbWheel,
                        'tooltip':'The radius of the sphere for any atom is computed as Offset Radius + Atomic Radius * Scale Factor', 
                        'wcfg':{ 'labCfg':{'text':'Offset Radius:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0.0, 'type':float,
                                 'precision':1,
                                 'value': defaultValues['cpkRad'],
                                 'continuous':1,
                                 'oneTurn':2, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})

            idf.append({'name':'scaleFactor',
                        'parent':'radiiGroup',
                        'widgetType':ThumbWheel,
                        'tooltip':'The radius of the sphere for any atom is computed as Offset Radius + Atomic Radius * Scale Factor',
                        'wcfg':{ 'labCfg':{'text':'Scale Factor:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0.0, 'max':100,
                                 'increment':0.01, 'type':float,
                                 'precision':1,
                                 'value': defaultValues['scaleFactor'],
                                 'continuous':1,
                                 'oneTurn':2, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})

            idf.append({'name':'quality',
                        'parent':'radiiGroup',
                        'widgetType':ThumbWheel,
                        'tooltip':'if quality = 0 a default value will be determined based on the number of atoms involved in the command',
                        'wcfg':{ 'labCfg':{'text':'Sphere Quality:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0, 'max':5, 'type':int, 'precision':1,
                                 'value': defaultValues['quality'],
                                 'continuous':1,
                                 'oneTurn':10, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})
            
            
            return idf

        
    def guiCallback(self):
        
        nodes = self.vf.getSelection()
        if not nodes:
            self.warningMsg("no nodes selected")
            return

        val = self.showForm()
        kw ={}

        if val:
            kw['redraw'] = True
            if val['display']=='display':
                kw['only']= False
                kw['negate'] = False

            elif val['display']=='display only':
                kw['only'] = True
                kw['negate'] = False

            elif val['display']== 'undisplay':
                kw['negate'] = True
                kw['only'] = False
                del val['display']
            bp = val.get("byproperty")
            if not bp:
                kw['quality'] = int(val['quality'])
                kw ['cpkRad'] = val['cpkRad']
                kw['scaleFactor']= val['scaleFactor']

            else:
                kw['byproperty'] = val['byproperty']
                kw['propertyName'] = val['propertyName'][0]
                kw ['cpkRad'] = val['offset']
                kw['quality'] = int(val['quality1'])
                kw['scaleFactor']= val['scaleFactor1']
                kw['propertyLevel'] = self.propertyLevel
            apply(self.doitWrapper, (nodes,), kw)


    def toggleInputByProp(self):
        #print "toggleInputByProp",
        val = self.showAtomProp.get()
        form = self.cmdForms['default']
        
        if val:
            form.descr.entryByName['radiiGroup']['widget'].grid_forget()
            defaultValues = self.lastUsedValues['default']
            if not form.descr.entryByName.get('propsGroup'):
                lSelection = self.vf.getSelection().uniq().findType(
                self.molDict[self.propertyLevel]).uniq()
                lSelection.sort()
                #molecules, atmSet = self.getNodes(self.vf.getSelection())
                #properties = self.getProperties(atmSet[0])
                properties = self.getProperties(lSelection)
                propertyNames = map(lambda x: (x[0],None), properties)
                propertyNames.sort()
                descr = []
                descr.append ({'name':'propsGroup',
                        'widgetType':Pmw.Group,
                        'container':{'propsGroup':"w.interior()"},
                        
                        'wcfg':{'ring_borderwidth':3,},
                        'gridcfg':{'sticky':'we', 'columnspan':1}})
                
                descr.append({'widgetType':Pmw.RadioSelect,
                              'parent':'propsGroup',
                              'name':'propertyLevel',
                              'listtext':['Atom', 'Residue', 'Chain','Molecule'],
                              'defaultValue':self.propertyLevel,'listoption':self.leveloption,
                              'wcfg':{'label_text':'Change the property level:',
                                      'labelpos':'nw','orient': Tkinter.VERTICAL,
                                      'buttontype': "radiobutton",
                                      'command':self.updateLevel_cb,
                                      },
                            'gridcfg':{'sticky':'we','columnspan':2}})
                
                
                descr.append({'name':'propertyName',
                       'parent':'propsGroup',
                       'widgetType':ListChooser,
                       'required':1,
                       'wcfg':{'entries': propertyNames,
                               'title':'Choose property:',
                               'lbwcfg':{'exportselection':0},
                               'mode':'single','withComment':0,
                               'command':self.updateValMinMax
                               },
                       'gridcfg':{'sticky':'we', 'rowspan':4, 'padx':5}#, 'columnspan':2}
                              })
                descr.append({'name':'valueMiniMaxi',
                        'widgetType':Pmw.Group,
                        'parent':'propsGroup',
                        'container':{"valminimaxi":'w.interior()'},
                        'wcfg':{'tag_text':"Property Values:"},
                        'gridcfg':{'sticky':'wnse'}})
##                 descr.append({'name':"valMin",
##                             'widgetType':Pmw.EntryField,
##                             'parent':'valminimaxi',
##                             'wcfg':{'label_text':'Minimum',
##                                     'labelpos':'w'},
##                             })
##                 descr.append({'name':"valMax",
##                               'widgetType':Pmw.EntryField,
##                               'parent':'valminimaxi',
##                               'wcfg':{'label_text':'Maximum',
##                                       'labelpos':'w'},
##                               #'gridcfg':{'row': -1}
##                               })
                descr.append({'name':"valMin",
                              'widgetType': Tkinter.Label,
                              'parent':'valminimaxi',
                              'wcfg': {'text':"Minimum:"},
                              'gridcfg':{'sticky':'w', 'columnspan':2}
                              })
                descr.append({'name':"valMax",
                              'widgetType': Tkinter.Label,
                              'parent':'valminimaxi',
                              'wcfg': {'text':"Maximum:"},
                              'gridcfg':{'sticky':'w', 'columnspan':2}
                              })
                
                
                descr.append({'name':'offset',
                          'parent':'propsGroup',
                          'widgetType':ThumbWheel,
                          'tooltip':' Radii of the sphere geom representing the atom will be equal to ( PropertyValue * Scale Factor + Offset)', 
                          'wcfg':{ 'labCfg':{'text':'Offset:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                   'showLabel':1, 'width':100,
                                   'min':0.0, 'type':float,
                                   'precision':1,
                                   'value': defaultValues.get('cpkRad', 0.0),
                                   'continuous':1,
                                   'oneTurn':2, 'wheelPad':2, 'height':20},
                          'gridcfg':{'sticky':'e'}#, 'columnspan':2}
                              })

                descr.append({'name':'scaleFactor1',
                      'parent':'propsGroup',
                      'widgetType':ThumbWheel,
                      'tooltip':'The Radii of the sphere geom representing the atom will be equal to (CPK Radii + Atom Radii * Scale Factor)',
                      'wcfg':{ 'labCfg':{'text':'Scale Factor:', 
                                         'font':(ensureFontCase('helvetica'),12,'bold')},
                               'showLabel':1, 'width':100,
                               'min':0.1, 'max':100,
                               'increment':0.01, 'type':float,
                               'precision':1,
                               'value': defaultValues.get('scaleFactor', 1.0),
                               'continuous':1,
                               'oneTurn':2, 'wheelPad':2, 'height':20},# 'columnspan':2},
                      'gridcfg':{'sticky':'e'} })
                descr.append({'name':'quality1',
                        'parent':'propsGroup',
                        'widgetType':ThumbWheel,
                        'tooltip':'if quality = 0 a default value will be determined based on the number of atoms involved in the command',
                        'wcfg':{ 'labCfg':{'text':'Sphere Quality:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0, 'max':5, 'type':int, 'precision':1,
                                 'value': defaultValues.get('quality', 2),
                                 'continuous':1,
                                 'oneTurn':10, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})
                
                for entry in descr:
                    form.addEntry(entry)
                    form.descr.entryByName[entry['name']] = entry
                form.autoSize()
            else:
                w = form.descr.entryByName['propsGroup']
                apply( w['widget'].grid ,(),w['gridcfg'])
                form.autoSize()
        else:
            if form.descr.entryByName.get('propertyName').has_key('required'):
                form.descr.entryByName.get('propertyName').pop('required')
            if form.descr.entryByName.get('propsGroup'):
                form.descr.entryByName['propsGroup']['widget'].grid_forget()
            w = form.descr.entryByName['radiiGroup']
            apply( w['widget'].grid ,(),w['gridcfg'])
            form.autoSize()


    def updateValMinMax(self, event=None):
        #print "updateValMinMax"
        ebn = self.cmdForms['default'].descr.entryByName
        widget = ebn['propertyName']['widget']
        properties = widget.get()
        if len(properties)==0:
            propValues=None
        else:
            propValues = self.getPropValues(self.vf.getSelection(),
                                            properties[0], self.propertyLevel)
            #print "in update:", propValues
        minEntry = ebn['valMin']['widget']
        maxEntry = ebn['valMax']['widget']
        self.getVal = 1
        if propValues is None :
            mini = 0
            maxi = 0
        else:
            mini = min(propValues)
            maxi = max(propValues)
        minEntry.configure(text="Minimum: " + str(mini))
        maxEntry.configure(text="Maximum: " + str(maxi))
        #minEntry.setentry(mini)
        #maxEntry.setentry(maxi)


    def getPropValues(self, nodes, prop, propertyLevel=None):
        #import pdb;pdb.set_trace()
        try:
            if propertyLevel is not None:
                #lNodesInLevel = self.vf.getSelection().findType(self.molDict[propertyLevel])
                lNodesInLevel = nodes.findType(self.molDict[propertyLevel])     
                num = len(lNodesInLevel.findType(Atom))
                propValues = getattr(lNodesInLevel, prop)
            else:
                propValues = getattr(nodes, prop)
        except:
            msg= "Some nodes do not have the selected property, therefore the \
current selection cannot be colored using this function."
            self.warningMsg(msg)
            propValues=None
        return propValues

    def getProperties(self, selection):
        properties = filter(lambda x: type(x[1]) is types.IntType \
                                 or type(x[1]) is types.FloatType,
                                 selection[0].__dict__.items())

        # Filter out the private members starting by __.
        properties = filter(lambda x: x[0][:2]!='__', properties)
        return properties
        

    def updateChooser(self, selection):
        ## if not hasattr(self, 'properties'): self.properties = []
##         oldProp = self.properties
##         self.properties = filter(lambda x: isinstance(x[1], IntType) \
##                                  or isinstance(x[1], FloatType),
##                                  selection[0].__dict__.items())

##         # Filter out the private members starting by __.
##         self.properties = filter(lambda x: x[0][:2]!='__', self.properties)
        properties = self.getProperties(selection)
        
        if self.cmdForms.has_key('default'):
            # If the list of properties changed then need to update the listbox
            ebn = self.cmdForms['default'].descr.entryByName
            widget = ebn['propertyName']['widget']
            propertyNames = map(lambda x: (x[0],None),properties)
            propertyNames.sort()
            oldsel = widget.get()
            widget.setlist(propertyNames)
            if len(oldsel)>0 and (oldsel[0], None) in propertyNames:
                widget.set(oldsel[0])
            

displayCPKGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                     'menuButtonName':'Display', 'menuEntryLabel':
                     'CPK' }

DisplayCPKGUI = CommandGUI()
DisplayCPKGUI.addMenuCommand('menuRoot', 'Display', 'CPK')



class DisplayCPKByProperty(DisplayCommand):
    """ The displayCPKByProperty command allows the user to specify a property used to display/undisplay the given nodes using a CPK representation, where each atom is represented with a sphere whose radius is set by the particular value of the property for that atom. A scale factor and the quality of the spheres are also used.
    defined parameters.
    \nPackage : Pmv
    \nModule  : displayCommands
    \nClass   : DisplayCPKByProperty
    \nCommand : displayCPKByProperty
    \nSynopsis:\n
        None <- displayCPKByProperty(nodes, only=False, negate=False, 
                           scaleFactor=None, quality=None, **kw)\n
        nodes --- any set of MolKit nodes describing molecular components\n
        only --- Boolean flag specifying whether or not to only display
                     the current selection\n
        negate --- Boolean flag specifying whether or not to undisplay
                     the current selection\n
        scaleFactor --- specifies a scale factor that will be applied to the atom
                     radii to compute the spheres radii. (default is 1.0)\n
        property ---  property name of type integer or float or property defined by a 
                     function returning a list of float or int.\n
        quality  --- specifies the quality of the spheres. (default 10)\n
        keywords --- display, CPK, space filling, undisplay.\n
    """
    levelOrder = {'Atom':0 , 
                  'Residue':1,
                  'Chain':2,
                  'Molecule':3 }


    def __init__(self, func=None):
        DisplayCommand.__init__(self, func)
        self.flag = self.flag & 0
        self.level = None  # class at this level (i.e. Molecule, Residue, Atom)


    def onAddCmdToViewer(self,):
        from mglutil.util.colorUtil import ToHEX
        DisplayCommand.onAddCmdToViewer(self)
        if not self.vf.commands.has_key('assignAtomsRadii'):
            self.vf.loadCommand('editCommands', 'assignAtomsRadii', 'Pmv',
                                topCommand=0)
        from MolKit.molecule import Molecule, Atom
        from MolKit.protein import Protein, Residue, Chain
        self.molDict = {'Molecule':Molecule,
                        'Atom':Atom, 'Residue':Residue, 'Chain':Chain}
        self.nameDict = {Molecule:'Molecule', Atom:'Atom', Residue:'Residue',
                         Chain:'Chain'}

        self.leveloption={}
        for name in ['Atom', 'Residue', 'Molecule', 'Chain']:
            col = self.vf.ICmdCaller.levelColors[name]
            bg = ToHEX((col[0]/1.5,col[1]/1.5,col[2]/1.5))
            ag = ToHEX(col)
            self.leveloption[name]={'bg':bg,'activebackground':ag,
                                    'borderwidth':3}
        self.propValues = None
        self.getVal = 0
        self.level = self.nameDict[self.vf.selectionLevel]
        self.propertyLevel = self.level
                       


    def getPropValues(self, nodes, prop, propertyLevel=None):
        #import pdb;pdb.set_trace()
        try:
            if propertyLevel is not None:
                lNodesInLevel = self.vf.getSelection().findType(self.molDict[propertyLevel])     
                num = len(lNodesInLevel.findType(Atom))
                self.propValues = getattr(lNodesInLevel, prop)
            else:
                self.propValues = getattr(nodes, prop)
        except:
            msg= "Some nodes do not have the selected property, therefore the \
current selection cannot be colored using this function."
            self.warningMsg(msg)
            self.propValues=[]


    def onAddObjectToViewer(self, obj):
        """Adds the cpkByProp geometry and the cpkByProp Atomset to the object's
        geometry container
        """
        #if not self.vf.hasGui: return
        obj.allAtoms.cpkByPropScale = 1.0
        obj.allAtoms.cpkByPropRad = 0.0
        geomC = obj.geomContainer
        # CPK spheres
        g = Spheres( "cpkByProp", quality=0 ,visible=0, protected=True)
        geomC.addGeom(g, parent=geomC.masterGeom, redo=0)
        self.managedGeometries.append(g)
        geomC.geomPickToBonds['cpkByProp'] = None
        for atm in obj.allAtoms:
            atm.colors['cpkByProp'] = (1.0, 1.0, 1.0)
            atm.opacities['cpkByProp'] = 1.0
        self.managedGeometries.append(g)


    def setupUndoBefore(self, nodes, only=False, negate=False, scaleFactor=1.0,
                        cpkRad=0.0, quality=0, **kw):
        kw = {}
        # use last used values for the undo
        defaultValues = self.lastUsedValues['default']
        kw['scaleFactor'] = defaultValues['scaleFactor']
        kw['quality'] = defaultValues['quality']
        kw['cpkRad'] = defaultValues['cpkRad']
        kw['redraw'] = True
        geomSet = []
        for mol in self.vf.Mols:
            geomSet = geomSet + mol.geomContainer.atoms['cpkByProp']

        if len(geomSet) == 0:
            # If nothing was displayed before, the undo of a display
            # command is to undisplay what you just displayed 
            kw['negate'] = True
            self.addUndoCall( (nodes,), kw, self.name)
        else:
            # If the current was already displayed and only is False and negate
            # is False then the undo is to display this set using the last used
            # values.
            
            # If something was already displayed, the undo of a display
            # command is to display ONLY what was displayed before.
            kw['only'] = True
            self.addUndoCall( (geomSet,), kw, self.name)


    def doit(self, nodes, only=False, negate=False, 
             scaleFactor=1.0, cpkRad=0.0, quality=0, **kw):

        ##############################################################
        def drawAtoms( mol, atm, only, negate, 
                       scaleFactor, cpkRad, quality):
            #atm.cpkScale = scaleFactor
            #atm.cpkRad = cpkRad
            _set = mol.geomContainer.atoms['cpkByProp']
            if len(atm) == len(mol.allAtoms):
                if negate:
                    setOff = atm
                    setOn = None
                    _set = AtomSet()
                else:
                    _set = atm
                    setOff = None
                    setOn = atm
            else:
                ##if negate, remove current atms from displayed _set
                if negate:
                    setOff = atm
                    setOn = None
                    _set = _set - atm

                ##if only, replace displayed _set with current atms 
                else:
                    if only:
                        setOff = _set - atm
                        setOn = atm
                        _set = atm
                    else: 
                        _set = atm + _set
                        setOff = None
                        setOn = _set

            mol.geomContainer.atoms['cpkByProp']=_set

            g = mol.geomContainer.geoms['cpkByProp']
            if len(_set)==0: 
                g.Set(visible=0, tagModified=False)
            else:
                _set.sort()   # EXPENSIVE...
                colors = map(lambda x: x.colors['cpkByProp'], _set)
                #cpkSF = Numeric.array(_set.cpkScale)
                #atmRad = Numeric.array(self.propValues) * scaleFactor
                #cpkRad = Numeric.array(self.propValues)
                #cpkRad = Numeric.array(_set.cpkRad)
                #sphRad = cpkRad + cpkSF*atmRad
                #sphRad = sphRad.tolist()
                sphRad = Numeric.array(self.propValues) * scaleFactor
                g.Set(vertices=_set.coords, inheritMaterial=False, 
                      materials = colors, radii=sphRad, visible=1,
                      quality=quality, tagModified=False)

                # highlight selection
                selMols, selAtms = self.vf.getNodesByMolecule(self.vf.selection, Atom)
                lMolSelectedAtmsDict = dict( zip( selMols, selAtms) )
                lSelectedAtoms = lMolSelectedAtmsDict.get(mol, None)
                if lSelectedAtoms is not None:
                    lVertexClosestAtomSet = mol.geomContainer.atoms['cpkByProp']
                    if len(lVertexClosestAtomSet) > 0:
                        lVertexClosestAtomSetDict = dict(zip(lVertexClosestAtomSet,
                                                             range(len(lVertexClosestAtomSet))))
                        highlight = [0] * len(lVertexClosestAtomSet)
                        for i in range(len(lSelectedAtoms)):
                            lIndex = lVertexClosestAtomSetDict.get(lSelectedAtoms[i], None)
                            if lIndex is not None:
                                highlight[lIndex] = 1
                        g.Set(highlight=highlight)


        ##################################################################
                
        molecules, atmSets = self.getNodes(nodes)
        try:
            radii = self.propValues
        except:
            self.vf.assignAtomsRadii(molecules, 
                                     overwrite=False, topCommand=False)

        for mol, atms in map(None, molecules, atmSets):
            drawAtoms(mol, atms, only, negate, 
                      scaleFactor, cpkRad, quality)
        if only and len(molecules)!=len(self.vf.Mols):
            mols = self.vf.Mols - molecules
            for mol in mols:
                only = False
                negate = True
                drawAtoms(mol, mol.allAtoms, only, negate, 
                          scaleFactor, cpkRad, quality)

        
    def cleanup(self):
        try:
            del self.expandedNodes____AtomSets
            del self.expandedNodes____Molecules
        except:
            print 'cleanup could not find any expandedNodes____AtomSets'


    def __call__(self, nodes, property, only=False, negate=False, 
                 scaleFactor=1.0,  cpkRad=0.0, quality=0,  **kw):
        """None <- displayCPKByProperty(nodes, property,  only=False, negate=False,scaleFactor=None, cpkRad=0.0, quality=None, **kw)
           \nnodes --- TreeNodeSet holding the current selection
           \nproperty --- property used to set radii
           \nonly --- Boolean flag when True only the current selection will be
                    displayed
           \nnegate --- Boolean flag when True undisplay the current selection
           \nscaleFactor --- value used to compute the radii of the sphere representing the atom (Sphere Radii = cpkRad + atom.radius * scaleFactor (default is 1.0)
           \ncpkRad --- value used to compute the radii of the sphere representing the atom (Sphere Radii = cpkRad + atom.radius * scaleFactor (default 0.0)
           \nquality --- sphere quality default value is 10"""
        if not kw.has_key('redraw'): kw['redraw'] = True
        if not type(scaleFactor) in [IntType, FloatType,
                                    LongType]: return 'ERROR'
        if not isinstance(quality, IntType) and quality>=0:
            return 'ERROR'
        kw['only'] = only
        kw['negate'] = negate
        kw['scaleFactor'] = scaleFactor
        #kw['cpkRad'] = cpkRad
        kw['quality'] = quality
        if type(nodes) is StringType:
            self.nodeLogString = "'" + nodes +"'"
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return
        apply( self.doitWrapper, (nodes,property), kw)


    def updateLevel_cb(self, tag):
        #if tag != self.level:
        #    self.level = tag
        if tag != self.propertyLevel:
            self.propertyLevel = tag
            
        #if self.molDict[tag]  != self.vf.ICmdCaller.level.value:
            #self.vf.setIcomLevel(self.molDict[tag])
            #force a change of selection level too in order to get
            #list of property values at 'tat' level
            #self.vf.setSelectionLevel(self.molDict[tag])

            lSelection = self.vf.getSelection().uniq().findType(
                self.molDict[tag]).uniq()
            lSelection.sort()
            self.updateChooser(lSelection)
            #self.cleanup()


    def updateChooser(self, selection):
        if not hasattr(self, 'properties'): self.properties = []
        oldProp = self.properties
        self.properties = filter(lambda x: isinstance(x[1], IntType) \
                                 or isinstance(x[1], FloatType),
                                 selection[0].__dict__.items())

        # Filter out the private members starting by __.
        self.properties = filter(lambda x: x[0][:2]!='__', self.properties)
        
        if self.cmdForms.has_key('default'):
            # If the list of properties changed then need to update the listbox
            ebn = self.cmdForms['default'].descr.entryByName
            widget = ebn['properties']['widget']
            propertyNames = map(lambda x: (x[0],None), self.properties)
            propertyNames.sort()
            oldsel = widget.get()
            widget.setlist(propertyNames)
            if len(oldsel)>0 and (oldsel[0], None) in propertyNames:
                widget.set(oldsel[0])


    def getPropValues2(self, nodes, function, lambdaFunc):
        try:
            func = evalString(function)
        except:
            self.warningMsg("Error occurred while evaluating the expression")
            traceback.print_exc()
            return

        if lambdaFunc == 1:
            try:
                self.propValues = map(func, nodes)
            except KeyError:
                msg= "Some nodes do not have this property, therefore the current selection cannot be colored using this function."
                self.warningMsg(msg)
                self.propValues = None
        else:
            try:
                self.propValues = func(nodes)
            except:
                msg= "Some nodes do not have this property, therefore the current selection cannot be colored using this function."
                self.warningMsg(msg)
                self.propValues = None

    def updateMiniMaxi(self, cmName, event=None):
        # get the colorMap
        #cm = self.vf.colorMaps[cmName]
        #mini = cm.mini
        #maxi = cm.maxi
        #FIX THIS!!!
        mini = 0
        maxi = 1000
        ebn = self.cmdForms['default'].descr.entryByName
        if mini is not None:
            ebn["cmMin"]['widget'].setentry(mini)
        if maxi is not None:
            ebn['cmMax']['widget'].setentry(maxi)


    def updateValMinMax(self, event=None):
        #print "updateValMinMax"
        ebn = self.cmdForms['default'].descr.entryByName
        widget = ebn['properties']['widget']
        properties = widget.get()
        if len(properties)==0:
            self.propValues=None
        else:
            self.getPropValues(self.selection, properties[0], self.propertyLevel)
        minEntry = ebn['valMin']['widget']
        maxEntry = ebn['valMax']['widget']
        self.getVal = 1
        if self.propValues is None :
            mini = 0
            maxi = 0
        else:
            mini = min(self.propValues)
            maxi = max(self.propValues)
        minEntry.setentry(mini)
        maxEntry.setentry(maxi)




    def updatePropVals(self, event=None):
        #print "updatePropVals event=", event
        ebn = self.cmdForms['default'].descr.entryByName
        widget = ebn['properties']['widget']
        properties = widget.get()
        if len(properties)==0:
            self.propValues=[]
            return
        else:
            self.getPropValues(self.selection, properties[0], self.propertyLevel)
        minEntry = ebn['valMin']['widget']
        maxEntry = ebn['valMax']['widget']
        self.getVal = 1
        if self.propValues is None or self.propValues==[] :
            mini = 0
            maxi = 0
        else:
            mini = min(self.propValues)
            maxi = max(self.propValues)
        minEntry.setentry(mini)
        maxEntry.setentry(maxi)




    def updateCM(self, event=None):
        ebn = self.cmdForms['default'].descr.entryByName
        mini = ebn['valMin']['widget'].get()
        maxi = ebn['valMax']['widget'].get()
        ebn["cmMin"]['widget'].setentry(mini)
        ebn['cmMax']['widget'].setentry(maxi)


    def buildFormDescr(self, formName='default'):
        # Need to create the InputFormDescr here if there is a gui.
        if formName == 'default':
            idf = DisplayCommand.buildFormDescr(
                self, 'default', title ="Display CPK with radii set by property:")

            defaultValues = self.lastUsedValues['default']
            if len(self.properties)>0 :
                #val = self.nameDict[self.vf.ICmdCaller.level.value]
                val = self.level
                listoption = {'Atom':{'bg':'yellow',
                                      'activebackground':'yellow',
                                      'borderwidth':3},
                              'Residue':{'bg':'green',
                                         'activebackground':'green',
                                         'borderwidth':3},
                              'Chain':{'bg':'cyan',
                                       'activebackground':'cyan',
                                       'borderwidth':3},
                              'Molecule':{'bg':'red',
                                          'activebackground':'red',
                                          'borderwidth':3}
                              }
                
                idf.append({'widgetType':Pmw.RadioSelect,
                            'name':'level',
                            'listtext':['Atom', 'Residue', 'Chain','Molecule'],
                            'defaultValue':val,'listoption':self.leveloption,
                            'wcfg':{'label_text':'Change the property level:',
                                    'labelpos':'nw',
                                    'command':self.updateLevel_cb,
                                    },
                            'gridcfg':{'sticky':'we','columnspan':2}})

                propertyNames = map(lambda x: (x[0],None), self.properties)
                propertyNames.sort()
                idf.append({'name':'properties',
                            'widgetType':ListChooser,
                            'required':1,
                            'wcfg':{'entries': propertyNames,
                                    'title':'Choose one property:',
                                    'lbwcfg':{'exportselection':0},
                                    'mode':'single','withComment':0,
                                    'command':self.updatePropVals,
                                    },
                            'gridcfg':{'sticky':'we', 'rowspan':4, 'padx':5}})
           #------------------------------------------------------------------
                idf.append({'name':'minMax',
                            'widgetType':Pmw.Group,
                            'parent':'cmdGroup',
                            'container':{"minMax":"w.interior()"},
                            'gridcfg':{'sticky':'wnse'}})

                idf.append({'name':'valueMiniMaxi',
                            'widgetType':Pmw.Group,
                            'parent':'minMax',
                            'container':{"valminimaxi":'w.interior()'},
                            'wcfg':{'tag_text':"Property Values:"},
                            'gridcfg':{'sticky':'wnse'}})
                            
                idf.append({'name':'updateCM',
                            'parent':'minMax',
                            'widgetType':Tkinter.Button,
                            'tooltip':"Set cpk radii min and max values \n with the property values min\
 and maxi",
                            'wcfg':{'text':">>", 'command':self.updateCM},
                            'gridcfg':{'row':-1}
                            })


                idf.append({'name':'cmninmaxi',
                            'widgetType':Pmw.Group,
                            'parent':'minMax',
                            'container':{"cmminimaxi":'w.interior()'},
                            'wcfg':{'tag_text':"CPK Radii:"},
                            'gridcfg':{'sticky':'wnse', 'row':-1}})

                idf.append({'name':"valMin",
                            'widgetType':Pmw.EntryField,
                            'parent':'valminimaxi',
                            'wcfg':{'label_text':'Minimum',
                                    'labelpos':'w'},
                            })
                idf.append({'name':"valMax",
                            'widgetType':Pmw.EntryField,
                            'parent':'valminimaxi',
                            'wcfg':{'label_text':'Maximum',
                                    'labelpos':'w'},
                            })
                
                idf.append({'name':"cmMin",
                            'widgetType':Pmw.EntryField,
                            'parent':'cmminimaxi',
                            'wcfg':{'label_text':'Minimum',
                                    'labelpos':'w'},
                            'gridcfg':{}
                            })

                idf.append({'name':"cmMax",
                            'widgetType':Pmw.EntryField,
                            'parent':'cmminimaxi',
                            'wcfg':{'label_text':'Maximum',
                                    'labelpos':'w'},
                            })
                        
           #------------------------------------------------------------------

            idf.append({'name':'cpkRad',
                        'widgetType':ThumbWheel,
                        'tooltip':'The Radii of the sphere geom representing the atom will be equal to (CPK Radii + Atom Radii * Scale Factor)', 
                        'wcfg':{ 'labCfg':{'text':'CPK Radii:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0.0, 'type':float,
                                 'precision':1,
                                 'value': defaultValues['cpkRad'],
                                 'continuous':1,
                                 'oneTurn':2, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})

            idf.append({'name':'scaleFactor',
                        'widgetType':ThumbWheel,
                        'tooltip':'The Radii of the sphere geom representing the atom will be equal to (CPK Radii + Atom Radii * Scale Factor)',
                        'wcfg':{ 'labCfg':{'text':'Scale Factor:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0.1, 'max':100,
                                 'increment':0.01, 'type':float,
                                 'precision':1,
                                 'value': defaultValues['scaleFactor'],
                                 'continuous':1,
                                 'oneTurn':2, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})

            idf.append({'name':'quality',
                        'widgetType':ThumbWheel,
                        'tooltip':'if quality = 03 a default value will be determined based on the number of atoms involved in the command',
                        'wcfg':{ 'labCfg':{'text':'Sphere Quality:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0, 'max':5, 'type':int, 'precision':1,
                                 'value': defaultValues['quality'],
                                 'continuous':1,
                                 'oneTurn':10, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})
            return idf


    def guiCallback(self):
        self.propValues = []
        nodes = self.vf.getSelection()
        if not nodes:
            self.warningMsg("no nodes selected")
            return
        self.selection = self.vf.getSelection().findType(self.vf.selectionLevel)
        if not self.selection: return 'ERROR' # to prevent logging
        self.level = self.nameDict[self.vf.selectionLevel]
        self.selection.sort()
        self.updateChooser(self.selection)
        if self.cmdForms.has_key('default'):
            # Check if the level is the same than the one on the menu bar
            ebn = self.cmdForms['default'].descr.entryByName
            levelwid = ebn['level']['widget']
            oldlevel = levelwid.getcurselection()
            #if oldlevel != self.nameDict[self.vf.ICmdCaller.level.value]:
            #    levelwid.invoke(self.nameDict[self.vf.ICmdCaller.level.value])
            if oldlevel != self.level:
                #print 'calling levelwid.invoke with ', self.level
                levelwid.invoke(self.level)
            self.updatePropVals()
        val = self.showForm('default')
        #if val:
        if val=={} or not val['properties']: return
        property = val['properties'][0]
        del val['properties']
        try:
            mini = float(val['cmMin'])
            val['mini'] = mini
        except:
            mini = None
            val['mini'] = None
        try:
            maxi = float(val['cmMax'])
            val['maxi'] = maxi
        except:
            maxi = None
            val['maxi'] = None

        val['redraw'] = True
        if val['display']=='display':
            val['only']= False
            val['negate'] = False
            del val['display']

        elif val['display']=='display only':
            val['only'] = True
            val['negate'] = False
            del val['display']

        elif val['display']== 'undisplay':
            val['negate'] = True
            val['only'] = False
            del val['display']

        val['quality'] = int(val['quality'])
        try:
            del val['level']
            del val['only']
        except:
            print 'error in removing level from dict'
        apply( self.doitWrapper, (nodes, property), val)


displayCPKByPropertyGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                     'menuButtonName':'Display', 'menuEntryLabel':
                     'CPKByProperty' }

DisplayCPKByPropertyGUI = CommandGUI()
DisplayCPKByPropertyGUI.addMenuCommand('menuRoot', 'Display', 'CPKByProperty')



class UndisplayCPK(DisplayCommand):
    """ The undisplayCPK command is a picking command allowing the user to undisplay the CPK geometry representing the picked nodes when used as a picking command or the given nodes when called from the Python shell.
    \nPackage : Pmv
    \nModule  : displayCommands
    \nClass   : UnDisplayCPK
    \nCommand : undisplayCPK
    \nSynopsis:\n
        None <- undisplayCPK(nodes, **kw)\n
        nodes : any set of MolKit nodes describing molecular components\n
        keywords: undisplay, CPK\n
    """

    def onAddCmdToViewer(self):
        DisplayCommand.onAddCmdToViewer(self)
        #if not self.vf.hasGui: return 
        if not self.vf.commands.has_key('displayCPK'):
            self.vf.loadCommand('displayCommands', ['displayCPK'], 'Pmv',
                                topCommand=0)

    def __call__(self, nodes, **kw):
        """None <- undisplayCPK(nodes, **kw)
           nodes: TreeNodeSet holding the current selection"""
        kw['negate']= 1
        if type(nodes) is StringType:
            self.nodeLogString = "'" + nodes +"'"
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return
        apply(self.vf.displayCPK, (nodes,),kw)


       
class DisplaySticksAndBalls(DisplayCommand):
    """The displaySticksAndBalls command allows the user to display/undisplay
the given nodes using the sticks and balls representation, where the bonds are
represented by cylinders and the atoms by balls.The radii of the cylinders and
the balls, and the quality of the spheres are user defined. The user can chose
to display or not the balls.
Package : Pmv
Module  : displayCommands
Class   : DisplaySticksAndBalls
Command : displaySticksAndBalls
Synopsis:
    None <--- displaySticksAndBalls(nodes,  only=0, negate=0,
                                    sticksBallsLicorice='Sticks and Balls',
                                    bradii=0.4, bquality=0, cradius=0.2,
                                    absolute=1, **kw)
    nodes --- any set of MolKit nodes describing molecular components
    only  --- Boolean flag specifying whether or not to only display
              the current selection\n
    negate --- Boolean flag specifying whether or not to undisplay
               the current selection\n
    sticksBallsLicorice --- String specifying the type of rendering
    cradius --- specifies the cylinder radius\n
    bradii --- specifies the radius of the balls if displayed.
    bquality --- specifies the quality of the balls if displayed.
    keywords --- display sticks and balls representation
"""

    def onRemoveObjectFromViewer(self, mol):
        pass

    def onAddCmdToViewer(self):
        DisplayCommand.onAddCmdToViewer(self)

        if not self.vf.commands.has_key('assignAtomsRadii'):
            self.vf.loadCommand('editCommands', 'assignAtomsRadii', 'Pmv',
                                topCommand=0)


    def onAddObjectToViewer(self, obj):
        #if not self.vf.hasGui: return
        if self.vf.hasGui and self.vf.commands.has_key('dashboard'):
            self.vf.dashboard.resetColPercent(obj, '_showS&BStatus')
        defaultValues = self.lastUsedValues['default']
        obj.allAtoms.ballRad = defaultValues['bRad']
        obj.allAtoms.ballScale = defaultValues['bScale']
        obj.allAtoms.cRad = defaultValues['cradius']

        geomC = obj.geomContainer

        # Cylinders (sticks)
        g = Cylinders( "sticks", visible=0, vertices=geomC.allCoords, protected=True)
        geomC.addGeom(g, parent=geomC.masterGeom, redo=0)
        self.managedGeometries.append(g)

        # Spheres at atomic positions (used for stick and balls)
        g = Spheres( "balls", vertices = geomC.allCoords,
                     radii = 0.4, quality = 4 ,visible=0, protected=True)
        geomC.addGeom(g, parent=geomC.masterGeom, redo=0)
        self.managedGeometries.append(g)
        geomC.geomPickToBonds['balls'] = None

        for atm in obj.allAtoms:
            atm.colors['sticks'] = (1.0, 1.0, 1.0)
            atm.opacities['sticks'] = 1.0
            atm.colors['balls'] = (1.0, 1.0, 1.0)
            atm.opacities['balls'] = 1.0


    def setupUndoBefore(self, nodes, only=False, negate=False,
                        bRad=0.3, bScale=0.0,
                        bquality=0, cradius=0.2, cquality=0, absolute=True,
                        sticksBallsLicorice='Licorice', setScale=True):
        
##         molecules, atomSets = self.getNodes(nodes)
        kw={}
        defaultValues = self.lastUsedValues['default']
        
        kw['bRad'] = defaultValues['bRad']
        kw['bScale'] = defaultValues['bScale']
        kw['bquality'] = defaultValues['bquality']
        kw['cradius'] = defaultValues['cradius']
        kw['cquality'] = defaultValues['cquality']
        kw['sticksBallsLicorice'] = defaultValues['sticksBallsLicorice']
        
        ballset = AtomSet()
        stickset = AtomSet()
        for mol in self.vf.Mols:
            ballset = ballset + mol.geomContainer.atoms['balls']
            stickset = stickset + mol.geomContainer.atoms['sticks']

        if len(ballset)==0:
            # no balls displayed
            if len(stickset) == 0: # negate
                # no stick displayed 
                kw['negate'] = True
                kw['redraw'] = True
                self.addUndoCall( (nodes,), kw,
                                  self.name )
            else:
                # noballs was on
                kw['negate'] = False
                kw['redraw'] = True
                kw['only'] = True
                self.addUndoCall( (stickset,), kw,
                                  self.name )
        else:

            kw['redraw'] = True
            kw['only'] = True
            self.addUndoCall( (stickset,), kw,
                              self.name )


    def doit(self, nodes, only=False, negate=False, bRad=0.3,
             bScale=0.0, bquality=0, cradius=0.2, cquality=0,
             sticksBallsLicorice='Licorice', setScale=True, **kw):
        #import pdb;pdb.set_trace()
        if kw.get('noballs') is not None:
            warnings.warn("noballs is deprected, use sticksBallsLicorice='Sticks Only' instead")

        ########################################################

        def drawBalls(mol, atm, only, noBalls, negate, bRad, bScale,
                      bquality, setScale):
            if setScale:
                atm.ballRad = bRad
                atm.ballScale = bScale
            _set = mol.geomContainer.atoms['balls']
            if len(_set)>mol.allAtoms:
                _set = mol.allAtoms
                mol.geomContainer.atoms['balls'] = _set
            if len(mol.geomContainer.atoms['balls']) > mol.allAtoms:
                mol.geomContainer.atoms['balls'] = mol.allAtoms

             ## case noballs:
            if noBalls:
                 if only:
                     if len(atm) == len(mol.allAtoms):
                         _set = atm
                     else:
                         _set = atm.union(_set)
                     mol.geomContainer.geoms['balls'].Set(visible=0,
                                                          tagModified=False)
                     mol.geomContainer.atoms['balls'] = _set
                     return
                 else:
                     negate = True
            
            ## Then handle only and negate    
            ##if negate, remove current atms from displayed _set
            if len(atm) == len(mol.allAtoms):
                if negate:
                    _set = AtomSet([])
                    setOff = atm
                    setOn = None
                else: 
                    _set = atm
                    setOff = None
                    setOn = atm
            else:
                if negate:
                    _set = _set - atm
                    setOff = atm
                    setOn = None
                else:
                    ##if only, replace displayed _set with current atms
                    if only:
                        setOff = _set - atm
                        setOn = atm
                        _set = atm
                    else: 
                        _set = atm + _set
                        setOff = None
                        setOn = _set

            if len(_set) == 0:
                mol.geomContainer.geoms['balls'].Set(visible=0,
                                                     tagModified=False)
                mol.geomContainer.atoms['balls'] = _set
                return setOn, setOff
            
            mol.geomContainer.atoms['balls']=_set
            #_set.sort()
            bScale = Numeric.array(_set.ballScale)
            bRad = Numeric.array(_set.ballRad)
            aRad = Numeric.array(_set.radius)
            
            ballRadii = bRad + bScale * aRad
            ballRadii = ballRadii.tolist()
            
            b = mol.geomContainer.geoms['balls']
            bcolors = map(lambda x: x.colors['balls'], _set)
            b.Set(vertices=_set.coords, radii=ballRadii,
                  materials=bcolors, inheritMaterial=False, 
                  visible=1, tagModified=False)
            if bquality and isinstance(bquality, IntType):
                b.Set(quality=bquality, tagModified=False)

            # highlight selection
            selMols, selAtms = self.vf.getNodesByMolecule(self.vf.selection, Atom)
            lMolSelectedAtmsDict = dict( zip( selMols, selAtms) )
            lSelectedAtoms = lMolSelectedAtmsDict.get(mol, None)
            if lSelectedAtoms is not None:
                    lVertexClosestAtomSet = mol.geomContainer.atoms['balls']
                    if len(lVertexClosestAtomSet) > 0:
                        lVertexClosestAtomSetDict = dict(zip(lVertexClosestAtomSet,
                                                             range(len(lVertexClosestAtomSet))))
                        highlight = [0] * len(lVertexClosestAtomSet)
                        for i in range(len(lSelectedAtoms)):
                            lIndex = lVertexClosestAtomSetDict.get(lSelectedAtoms[i], None)
                            if lIndex is not None:
                                highlight[lIndex] = 1
                        b.Set(highlight=highlight)

            return setOn, setOff

 
        def drawSticks(mol, atm, only, negate, cradius, cquality,
                       setScale):
            if setScale:
                atm.cRad = cradius
            _set = mol.geomContainer.atoms['sticks']
            ##if negate, remove current atms from displayed _set
            if len(atm) == len(mol.allAtoms):
                if negate:
                    _set = AtomSet()
                    setOff = atm
                    setOn = None
                else:
                    _set = atm
                    setOff = None
                    setOn = atm
            else:
                if negate:
                    setOff = atm
                    setOn = None
                    _set = _set - atm
                else:
                    ## if only, replace displayed _set with current atms
                    if only:
                        setOff = _set - atm
                        setOn = atm
                        _set = atm
                    else: 
                        _set = atm.union(_set)
                        setOff = None
                        setOn = _set

            if len(_set) == 0:
                mol.geomContainer.geoms['sticks'].Set(visible=0,
                                                      tagModified=False)
                mol.geomContainer.atoms['sticks']= _set
                return setOn, setOff

            bonds, atnobnd = _set.bonds
            mol.geomContainer.atoms['sticks'] = _set
            indices = map(lambda x: (x.atom1._bndIndex_,
                                     x.atom2._bndIndex_), bonds)
            g = mol.geomContainer.geoms['sticks']
            if len(indices) == 0:
                g.Set(visible=0, tagModified=False, redo=False)
            else:
                cRad = _set.cRad
                scolors = map(lambda x: x.colors['sticks'], _set)
                g.Set( vertices=_set.coords, faces=indices, radii=cRad,
                       materials=scolors, visible=1, quality=cquality,
                       tagModified=False, inheritMaterial=False)

            # highlight selection
            selMols, selAtms = self.vf.getNodesByMolecule(self.vf.selection, Atom)
            lMolSelectedAtmsDict = dict( zip( selMols, selAtms) )
            lSelectedAtoms = lMolSelectedAtmsDict.get(mol, None)
            if lSelectedAtoms is not None:
                    lVertexClosestAtomSet = mol.geomContainer.atoms['sticks']
                    if len(lVertexClosestAtomSet) > 0:
                        lVertexClosestAtomSetDict = dict(zip(lVertexClosestAtomSet,
                                                             range(len(lVertexClosestAtomSet))))
                        highlight = [0] * len(lVertexClosestAtomSet)
                        for i in range(len(lSelectedAtoms)):
                            lIndex = lVertexClosestAtomSetDict.get(lSelectedAtoms[i], None)
                            if lIndex is not None:
                                highlight[lIndex] = 1
                        g.Set(highlight=highlight)
            return setOn, setOff


##             

#DISPLAY BOND ORDER.
##             if len(atm) == len(mol.allAtoms):
##                 if negate or not displayBO:
##                     setBo = AtomSet()
##                 else:
##                     setBo = atm

##             else:
##                 setBo = gatoms['bondorder'].uniq()
##                 if negate or not displayBO:
##                     #if negate, remove current atms from displayed set
##                     setBo = setBo - atm
##                 else:     #if only, replace displayed set with current atms 
##                     if only:
##                         setBo = atm
##                     else: 
##                         setBo = atm.union(setBo)
            
##             if len(setBo) == 0:
##                 ggeoms['bondorder'].Set(vertices = [], tagModified=False )
##                 gatoms['bondorder'] = setBo
##                 return
            
##             bonds = setBo.bonds[0]

##             # Get only the bonds with a bondOrder greater than 1
##             bondsBO= BondSet(filter(lambda x: not x.bondOrder is None and \
##                                     x.bondOrder>1, bonds)) 
##             if not bondsBO: return
##             withVec = filter(lambda x: not hasattr( x.atom1, 'dispVec') \
##                              and not hasattr(x.atom2, 'dispVec'),bondsBO)
##             if len(withVec):
##                 map(lambda x: x.computeDispVectors(), bondsBO)

##             vertices = []
##             indices = []
##             col = []
##             i = 0
##             realSet  = AtomSet([])
##             ar = Numeric.array
##             for b in bonds:
##                 bondOrder = b.bondOrder
##                 if bondOrder == 'aromatic' : bondOrder = 2
##                 if not bondOrder > 1: continue

##                 at1 = b.atom1
##                 at2 = b.atom2
##                 if (not hasattr(at1, 'dispVec') \
##                     and not hasattr(at2, 'dispVec')):
##                     continue
##                 realSet.append(at1)
##                 realSet.append(at2)

##                 nc1 = ar(at1.coords) + \
##                       ar(at1.dispVec)
##                 nc2 = ar(at2.coords) + \
##                       ar(at2.dispVec)
##                 vertices.append(list(nc1))
##                 vertices.append(list(nc2))
##                 indices.append( (i, i+1) )
##                 i = i+2
##             gatoms['bondorder'] = realSet
##             col = mol.geomContainer.getGeomColor('bondorder')
##             ggeoms['bondorder'].Set( vertices=vertices, faces=indices,
##                                      visible=1, lineWidth=lineWidth,
##                                      materials=col, inheritMaterial=0,
##                                      tagModified=False)
        ###########################################################

        molecules, atomSets = self.getNodes(nodes)
        setOn = AtomSet([])
        setOff = AtomSet([])
        try:
            radii = molecules.allAtoms.radius
        except:
            self.vf.assignAtomsRadii(molecules, 
                                     overwrite=False,
                                     united=False,
                                     topCommand=False)

        for mol, atm in map(None, molecules, atomSets):
             try:
                 if sticksBallsLicorice == 'Licorice':
                     son, sof = drawBalls(mol, atm, only, 0, negate, cradius,
                                          0.0, cquality, setScale)
                 elif sticksBallsLicorice == 'Sticks only':
                     son, sof = drawBalls(mol, atm, only, 1, negate, bRad,
                                          bScale, bquality, setScale)
                 else:
                     son, sof = drawBalls(mol, atm, only, 0, negate, bRad,
                                          bScale, bquality, setScale)
                 
                 if son: setOn += son
                 if sof: setOff += sof

                 son, sof = drawSticks(mol, atm, only, negate, cradius,
                                       cquality, setScale)
                 if son: setOn += son
                 if sof: setOff += sof
                 
             except:
                 print 'ERROR command %s failed on molecule %s *****' %\
                       (self.name, mol.name)
                 if self.vf.hasGui and self.vf.guiVisible==1 \
                    and self.vf.withShell:
                     self.vf.GUI.pyshell.top.deiconify()
                 traceback.print_exc()
                 print 'ERROR *************************************'

        if only and len(self.vf.Mols) != len(molecules):
            mols = self.vf.Mols - molecules
            for mol in mols:
                negate = True
                only=0
                if sticksBallsLicorice == 'Licorice':
                    son, sof = drawBalls(mol, mol.allAtoms, only, 0, negate,
                                         cradius, 0, cquality, setScale)
                elif sticksBallsLicorice == 'Sticks only':
                    son, sof = drawBalls(mol, mol.allAtoms, only, 1, negate,
                                         bRad, bScale, bquality, setScale)
                else:
                    son, sof = drawBalls(mol, mol.allAtoms, only, 0, negate,
                                         bRad, bScale, bquality, setScale)
                if son: setOn += son
                if sof: setOff += sof
                son, sof = drawSticks(mol, mol.allAtoms, only, negate,
                                      cradius, cquality, setScale)
                if son: setOn += son
                if sof: setOff += sof

        redraw = False
        if kw.has_key("redraw") : redraw=True
        if self.createEvents:
            event = EditGeomsEvent('bs', [nodes,[only, negate, bRad,
                                bScale, bquality, cradius, cquality,
                                sticksBallsLicorice,redraw]],
                                setOn=setOn, setOff=setOff)
            self.vf.dispatchEvent(event)


    def cleanup(self):
        del self.expandedNodes____AtomSets
        del self.expandedNodes____Molecules


    def ballsAndLicorice_cb(self, sticksBallsLicorice=None):
        #print "ballsAndLicorice_cb", sticksBallsLicorice
        if (sticksBallsLicorice == 'Licorice') or (sticksBallsLicorice == 'Sticks only'):
            self.idf.entryByName['ballgroup']['widget'].grid_forget()
        else :
            apply( self.idf.entryByName['ballgroup']['widget'].grid,(),
                   self.idf.entryByName['ballgroup']['gridcfg'])


    def buildFormDescr(self, formName='default', title ="Display sticks and balls"):
        """
This is where descr gets created. It is called for each formName if
the associated form doesn't already exists. If a command has several
form buildFormDescr will be called for each formName.
"""
        # Need to create the InputFormDescr here if there is a gui.
        if formName == 'default':
            self.idf = DisplayCommand.buildFormDescr(
                self, formName, title=title)

            defaultValues = self.lastUsedValues['default']

            self.idf.append({'name':"stickgroup",
                        'widgetType':Pmw.Group,
                        'container':{'stickgroup':'w.interior()'},
                        'wcfg':{'tag_text':"Sticks parameters:"},
                        'gridcfg':{'sticky':'wnse'}
                        })

            self.idf.append({'name':'cradius',
                        'widgetType':ThumbWheel,
                        'parent':'stickgroup',
                        'wcfg':{ 'labCfg':{'text':'Sticks Radius:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0.1, 'max':10.0, 'type':float,
                                 'precision':2,
                                 'value': defaultValues['cradius'],
                                 'continuous':1,
                                 'oneTurn':2, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})

            self.idf.append({'name':'cquality',
                        'widgetType':ThumbWheel,
                        'parent':'stickgroup',
                        'tooltip':'if quality = 0 a default value will be determined based on the number of atoms involved in the command',
                        'wcfg':{ 'labCfg':{'text':'Sticks Quality:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0, 'max':5,'lockMin':1, 'type':int,
                                 'precision':1,
                                 'value': defaultValues['cquality'],
                                 'continuous':1,
                                 'oneTurn':10, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})

            self.idf.append({'name':"ballgroup",
                        'widgetType':Pmw.Group,
                        'container':{'ballgroup':'w.interior()'},
                        'wcfg':{'tag_text':"Balls parameters:"},
                        'gridcfg':{'sticky':'wnse'}
                        })

            self.idf.append({'name':'sticksBallsLicorice',
                        'widgetType':Pmw.RadioSelect,
                        'tooltip':"Licorice: sticks and balls have the same radius and quality",
                        'listtext':['Sticks and Balls', 'Licorice', 'Sticks only'],
                        'defaultValue': defaultValues['sticksBallsLicorice'],
                        'wcfg':{'orient':'horizontal',
                                'buttontype':'radiobutton',
                                'command':self.ballsAndLicorice_cb},
                        'gridcfg':{'row':2,'column':0, 'sticky':'e'}})

            self.idf.append({'name':'bRad',
                        'parent':'ballgroup',
                        'widgetType':ThumbWheel,
                        'tooltip':'The Radii of the sphere geom representing the atom will be equal to (Ball Radii + Atom Radii * Scale Factor)', 
                        'wcfg':{ 'labCfg':{'text':'Ball Radii:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0.0, 'type':float,
                                 'precision':1,
                                 'value': defaultValues['bRad'],
                                 'continuous':1,
                                 'oneTurn':2, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})

            self.idf.append({'name':'bScale',
                        'widgetType':ThumbWheel,
                        'parent':'ballgroup',
                        'tooltip':'The Radii of the sphere geom representing the atom will be equal to (Ball Radii + Atom Radii * Scale Factor)',
                        'wcfg':{ 'labCfg':{'text':'Scale Factor:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0.0, 'max':10.0, 'type':float,
                                 'precision':2,
                                 'value': defaultValues['bScale'],
                                 'continuous':1,
                                 'oneTurn':2, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})
            

            self.idf.append({'name':'bquality',
                        'widgetType':ThumbWheel,
                        'parent':'ballgroup',
                        'tooltip':'if quality = 0 a default value will be determined based on the number of atoms involved in the command',
                        'wcfg':{ 'labCfg':{'text':'Balls Quality:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0, 'max':5, 'lockMin':1, 'type':int,
                                 'precision':1,
                                 'value': defaultValues['bquality'],
                                 'continuous':1,
                                 'oneTurn':10, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})

            return self.idf


    def guiCallback(self):
        nodes = self.vf.getSelection()
        if not nodes:
             self.warningMsg("no nodes selected")
             return
        nodes = nodes.findType(Atom)
        
        val = self.showForm()

        #self.ballsAndLicorice_cb()

        if val:
            if val['display']=='display':
                val['only']= False
                val['negate'] = False
                del val['display']
            elif val['display']=='display only':
                val['only']= True
                val['negate'] = False
                del val['display']
            elif val['display']== 'undisplay':
                val['negate'] = True
                val['only'] = False
                del val['display']
            val['redraw'] = True

            apply( self.doitWrapper, (self.vf.getSelection(),), val)
        

    def __call__(self, nodes, only=False, negate=False,
                 bRad=0.3, bScale=0.0, bquality=0, cradius=0.2, cquality=0,
                 sticksBallsLicorice='Licorice', setScale=True, **kw):

        """None <- displaySticksAndBalls(nodes, only=False, negate=False,
                                      noballs=False, bRad=0.3,bScale=0.0,
                                      bquality=4, cradius=0.2,
                                      absolute=True, **kw)
        \nnodes --- any set of MolKit nodes describing molecular components
        \nonly  --- flag to only display the current selection
        \nnegate  --- flag to undisplay the current selection
        \nnoballs --- flag to undisplay the balls of the current selection
        \nbRad  --- defines the radius of the balls
        \nbScale --- defines the scale factor to be applied to the atom radius to
                  compute the sphere radius. (sphere radius = bRad + atom.radius *bScale)
        \nbquality --- defines the quality of the balls
        \ncradius --- defines the cylinder radius
        \nabsolute --- flag to get absolute or not radii for the atoms
        """

        if kw.get('noballs') is not None:
            warnings.warn("noballs is deprected, use sticksBallsLicorice='Sticks Only' instead")
            kw.pop('noballs')

        if not kw.has_key('redraw'): kw['redraw'] = True
        if not kw.has_key('only'): kw['only'] = only
        if not kw.has_key('negate'): kw['negate'] = negate
        if not kw.has_key('sticksBallsLicorice'): kw['sticksBallsLicorice'] = sticksBallsLicorice
        if not kw.has_key('bRad'): kw['bRad'] = bRad
        if not kw.has_key('bScale'): kw['bScale'] = bScale
        if not kw.has_key('bquality'): kw['bquality'] = bquality
        if not kw.has_key('cradius'): kw['cradius'] = cradius   
        if not kw.has_key('cquality'): kw['cquality'] = cquality
        if not kw.has_key('setScale'): kw['setScale'] = setScale
        if type(nodes) is StringType:
            self.nodeLogString = "'" + nodes +"'"
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return 
        nodes = nodes.findType(Atom)
        apply( self.doitWrapper, (nodes,), kw)


displaySticksAndBallsGuiDescr = {'widgetType':'Menu', 'menuBarName':
                                 'menuRoot', 'menuButtonName':'Display',
                                 'menuEntryLabel':'Stick And Balls'}

DisplaySticksAndBallsGUI = CommandGUI()
DisplaySticksAndBallsGUI.addMenuCommand('menuRoot', 'Display',
                                        'Sticks And Balls')
        


class DisplaySSSB(DisplaySticksAndBalls):
    """The displaySSSB command allows the user to display/undisplay the given chains using the sticks and balls representation for non protein chains and ribbon diagram for proteic chains.
\nPackage : Pmv
\nModule  : displayCommands
\nClass   : DisplaySSSB
\nCommand : displaySSSB
\nSynopsis:\n
        None <- displaySSSB(nodes, only=0, negate=0, noballs=0,
                            bradii=0.4, bquality=4, cradius=0.2,
                            absolute=1, **kw)\n
        nodes   : any set of MolKit nodes describing molecular components\n
        only    : Boolean flag specifying whether or not to only display
                  the current selection\n
        negate  : Boolean flag specifying whether or not to undisplay
                  the current selection\n
        noballs : Boolean flag specifying whether or not to undisplay the
                  balls geometry of the current selection\n
        cradius : specifies the cylinder radius\n
        bradii  : specifies the radius of the balls if displayed.\n
        bquality: specifies the quality of the balls if displayed.\n
        keywords: display ribbon and sticks and balls representation\n
"""
    def onAddObjectToViewer(self, obj):
        self.vf.browseCommands('displayCommands',
                               commands=('displaySticksAndBalls',), log=0)
        self.vf.browseCommands('displayCommands',
                               commands=('displayLines',), log=0)
        self.vf.browseCommands('secondaryStructureCommands',
                               commands=('displayExtrudedSS',), log=0)
    
    def doit(self, nodes, only=False, negate=False, bRad=0.3,
             bScale=0.0, bquality=0, cradius=0.2, cquality=0, 
             sticksBallsLicorice='Licorice', **kw):

        if kw.get('noballs') is not None:
            warnings.warn("noballs is deprected, use sticksBallsLicorice='Sticks Only' instead")

        molecules, atomSets = self.getNodes(nodes)

        AAlist = {'ALA':0,'ARG':0,'ASN':0,'ASP':0,'CYS':0,'GLU':0,'GLN':0,
                  'GLY':0,'HIS':0,'ILE':0,'LEU':0,'LYS':0,'MET':0,'PHE':0,
                  'PRO':0,'SER':0,'THR':0, 'TRP':0,'TYR':0,'VAL':0}

        for mol, atm in zip(molecules, atomSets):
            # build list of AA and other residues
            proteic = []
            notproteic = []
            for res in atm.parent.uniq():
                if AAlist.has_key(res.type):
                    proteic.append(res)
                else:
                    notproteic.append(res)

            # display ribbon for AA
            #print 'ribbon for', len(proteic), negate
            self.vf.displayExtrudedSS(ResidueSet(proteic), only=only,
                                      negate=negate, topCommand=0)

            # split non AA into residues with and without bonds
            bonded = []
            nonbonded = []
            for r in ResidueSet(notproteic):
                if len(r.atoms.bonds[0]):
                    bonded.append(r)
                else:
                    nonbonded.append(r)

            if len(bonded):
                #print 'S&B', len(bonded), negate
                self.vf.displaySticksAndBalls( ResidueSet(bonded),
                            only=only, negate=negate,
                            bRad=bRad, bScale=bScale, bquality=bquality,
                            cradius=cradius, cquality=cquality, topCommand=0,
                            sticksBallsLicorice=sticksBallsLicorice)
            if len(nonbonded):
                #print 'Lines', len(nonbonded), negate
                self.vf.displayLines(ResidueSet(nonbonded), only=True,
                                     negate=negate, topCommand=0)

        self.proteic = ResidueSet(proteic)
        self.bonded = ResidueSet(bonded)
        self.nonbonded = ResidueSet(nonbonded)
    

displaySSSBDescr = {'widgetType':'Menu', 'menuBarName':
                    'menuRoot', 'menuButtonName':'Display',
                    'menuEntryLabel':'ribbon and S&B'}

DisplaySSSBGUI = CommandGUI()
DisplaySSSBGUI.addMenuCommand('menuRoot', 'Display', 'ribbon and S&B')



class UndisplaySticksAndBalls(DisplayCommand):
    """ The UndisplaySticksAndBalls command is an interactive command to undisplay part of the molecule when represented as sticks and balls.
    \nPackage : Pmv
    \nModule  : displayCommands
    \nClass   : UnDisplaySticksAndBalls
    \nCommand : undisplaySticksAndBalls
    \nSynopsis:\n
        None <- undisplaySticksAndBalls(nodes, **kw)\n
        nodes --- any set of MolKit nodes describing molecular components\n
        keywords --- undisplay, SticksAndBalls\n
    """

    def onAddCmdToViewer(self):
        DisplayCommand.onAddCmdToViewer(self)
        #if not self.vf.hasGui: return 
        if not self.vf.commands.has_key('displaySticksAndBalls'):
            self.vf.loadCommand('displayCommands', ['displaySticksAndBalls'],
                                'Pmv',topCommand=0)


    def __call__(self, nodes, **kw):
        """None <- undisplaySticksAndBalls(nodes, **kw)
           nodes: TreeNodeSet holding the current selection"""
        if not nodes: return
        kw['negate']= 1
        if type(nodes) is StringType:
            self.nodeLogString = "'" + nodes +"'"
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return
        apply(self.vf.displaySticksAndBalls, (nodes,),kw)
        


class DisplayBackboneTrace(DisplaySticksAndBalls):
    """The displayBackboneTrace command allows the user to display/undisplay the given nodes using the sticks and balls representation, where the bonds are represented by cylinders and the atoms by balls.The radii of the cylinders and the balls, and the quality of the spheres are user defined. The user can chose to display or not the balls.
    \nPackage : Pmv
    \nModule  : displayCommands
    \nClass   : DisplayBackboneTrace
    \nCommand : displayBackboneTrace
    \nSynopsis:\n
        None <- displayBackboneTrace(nodes,  only=0, negate=0, noballs=0,
                                      bradii=0.4, bquality=4, cradius=0.2,
                                      absolute=1, **kw)\n
        nodes   : any set of MolKit nodes describing molecular components\n
        only    : Boolean flag specifying whether or not to only display
                  the current selection\n
        negate  : Boolean flag specifying whether or not to undisplay
                  the current selection\n
        noballs : Boolean flag specifying whether or not to undisplay the
                  balls geometry of the current selection\n
        cradius : specifies the cylinder radius\n
        bradii  : specifies the radius of the balls if displayed.\n
        bquality: specifies the quality of the balls if displayed.\n
        keywords: display BackboneTrace representation\n
    """

    def onAddObjectToViewer(self, obj):
        #if not self.vf.hasGui: return
        defaultValues = self.lastUsedValues['default']
        obj.allAtoms.ballRad = defaultValues['bRad']
        obj.allAtoms.ballScale = defaultValues['bScale']
        obj.allAtoms.cRad = defaultValues['cradius']

        geomC = obj.geomContainer

        # Cylinders (sticks)
        g = Cylinders( "CAsticks", visible=0, vertices = geomC.allCoords, protected=True)
        geomC.addGeom(g)
        self.managedGeometries.append(g)

        # Spheres at atomic positions (used for stick and balls)
        g = Spheres( "CAballs", vertices = geomC.allCoords,
                     radii = 0.4, quality = 4 ,visible=0, protected=True)
        geomC.addGeom(g)
        self.managedGeometries.append(g)
        geomC.geomPickToBonds['CAballs'] = None

        for atm in obj.allAtoms:
            atm.colors['CAsticks'] = (1.0, 1.0, 1.0)
            atm.opacities['CAsticks'] = 1.0
            atm.colors['CAballs'] = (1.0, 1.0, 1.0)
            atm.opacities['CAballs'] = 1.0


    def setupUndoBefore(self, nodes, only=False, negate=False,
                        bRad=0.3, bScale=0.0,
                        bquality=0, cradius=0.2, cquality=0, absolute=True,
                        sticksBallsLicorice='Sticks and Balls', setScale=True):
        
##         molecules, atomSets = self.getNodes(nodes)
        kw={}
        defaultValues = self.lastUsedValues['default']

        kw['bRad'] = defaultValues['bRad']
        kw['bScale'] = defaultValues['bScale']
        kw['bquality'] = defaultValues['bquality']
        kw['cradius'] = defaultValues['cradius']
        kw['cquality'] = defaultValues['cquality']
        kw['sticksBallsLicorice'] = defaultValues['sticksBallsLicorice']
        
        caballset = AtomSet()
        castickset = AtomSet()
        for mol in self.vf.Mols:
            caballset =  caballset+mol.geomContainer.atoms['CAballs']
            castickset = castickset+mol.geomContainer.atoms['CAsticks']
           
        if len(caballset)==0:
            # no balls displayed
            if len(castickset) == 0: # negate
                # no stick displayed 
                kw['negate'] = True
                kw['redraw'] = True
                self.addUndoCall( (nodes,), kw,
                                  self.name )
            else:
                # noballs was on
                kw['negate'] = False
                kw['redraw'] = True
                kw['only'] = True
                self.addUndoCall( (castickset,), kw,
                                  self.name )
        else:

            kw['redraw'] = True
            kw['only'] = True
            self.addUndoCall( (castickset,), kw,
                              self.name )


    def buildFormDescr(self, formName='default', title ="Display backbone trace"):
        """
This is where descr gets created. It is called for each formName if
the associated form doesn't already exists. If a command has several
form buildFormDescr will be called for each formName.
"""
        return DisplaySticksAndBalls.buildFormDescr(self, formName=formName, title=title)


    def doit(self, nodes, only=False, negate=False, bRad=0.3,
             bScale=0.0, bquality=0, cradius=0.2, cquality=0, 
             sticksBallsLicorice='Sticks and Balls', **kw):

        if kw.get('noballs') is not None:
            warnings.warn("noballs is deprected, use sticksBallsLicorice='Sticks Only' instead")

        ########################################################
            
        def drawCABalls(mol, atm, only, noBalls, negate, bRad, bScale,
                      bquality):
            atm.ballRad = bRad
            atm.ballScale = bScale
            
            _set = mol.geomContainer.atoms['CAballs']
            ## case noballs:
            if noBalls:
                if only:
                    if len(atm) == len(mol.allAtoms):
                        _set = atm
                    else:
                        _set = atm.union(_set)
                    mol.geomContainer.geoms['CAballs'].Set(visible=0,
                                                         tagModified=False)
                    mol.geomContainer.atoms['CAballs'] = _set
                    return
                else:
                    negate = True
            
            ## Then handle only and negate    
            ##if negate, remove current atms from displayed _set
            if len(atm) == len(mol.allAtoms):
                if negate: _set = AtomSet([])
                else: _set = atm
            else:
                if negate:
                    _set = _set - atm
                else:
                    ##if only, replace displayed _set with current atms
                    if only:
                        _set = atm
                    else: 
                        _set = atm.union(_set)
            if len(_set) == 0:
                mol.geomContainer.geoms['CAballs'].Set(visible=0,
                                                     tagModified=False)
                mol.geomContainer.atoms['CAballs'] = _set
                return
            
            mol.geomContainer.atoms['CAballs']=_set
            #_set.sort()
            bScale = Numeric.array(_set.ballScale)
            bRad = Numeric.array(_set.ballRad)
            aRad = Numeric.array(_set.radius)
            ballRadii = bRad + bScale * aRad
            ballRadii = ballRadii.tolist()

            b = mol.geomContainer.geoms['CAballs']
            bcolors = map(lambda x: x.colors['CAballs'], _set)
            b.Set(vertices=_set.coords, radii=ballRadii,
                  materials=bcolors, inheritMaterial=False, 
                  visible=1, tagModified=False)
            if bquality:
                b.Set(quality=bquality, tagModified=False)

            # highlight selection
            selMols, selAtms = self.vf.getNodesByMolecule(self.vf.selection, Atom)
            lMolSelectedAtmsDict = dict( zip( selMols, selAtms) )
            lSelectedAtoms = lMolSelectedAtmsDict.get(mol, None)
            if lSelectedAtoms is not None:
                    lVertexClosestAtomSet = mol.geomContainer.atoms['CAballs']
                    if len(lVertexClosestAtomSet) > 0:
                        lVertexClosestAtomSetDict = dict(zip(lVertexClosestAtomSet,
                                                             range(len(lVertexClosestAtomSet))))
                        highlight = [0] * len(lVertexClosestAtomSet)
                        for i in range(len(lSelectedAtoms)):
                            lIndex = lVertexClosestAtomSetDict.get(lSelectedAtoms[i], None)
                            if lIndex is not None:
                                highlight[lIndex] = 1
                        b.Set(highlight=highlight)


        def drawCASticks(mol, atm, only, negate, cradius, cquality):

                atm.sort() 
                atm.cRad = cradius
                _set = mol.geomContainer.atoms['CAsticks']
                 
                if negate:
                    _set = mol.geomContainer.atoms['CAsticks']
                    _set = _set - atm
                         
                else:                       
                     if only: 
                            _set = atm                            
                     else: 
                            _set = atm.union(_set)
                            
                if len(_set) == 0:
                    mol.geomContainer.geoms['CAsticks'].Set(visible=0,
                                                      tagModified=False)
                    mol.geomContainer.atoms['CAsticks']= _set
                    return

                mol.geomContainer.atoms['CAsticks'] = _set
             
                indices =[]
                                   
                for i in range(0,len(_set)):
                        if i+1 <=len(_set)-1:
                            indices.append((i,i+1))
                                     
                for ch in range(0,len(mol.chains)-1):
                      list =[]
                    
                      if len(mol.chains)>1: 
                        a=mol.chains[ch].getAtoms().get(lambda x: x.name=='CA')
                        a.sort()
                        for l in _set:
                            for k in a:
                                if l==k:            
                                    list.append(l)
                        i =len(list)
                        if _set !=list:
                            if (i-1,i) in indices:
                                ind=indices.index((i-1,i))
                                del indices[ind]

                for ch in range(0,len(mol.chains)):    
                    #finding tranformed coordsd to pass in to FindGap
                    chatoms=_set
                    mats=[]
                    for ca in chatoms:
                        c = self.vf.transformedCoordinatesWithInstances(AtomSet([ca]))
                        mat =Numeric.array(c[0], 'f')
                        mats.append(mat)
                        
                    from MolKit.GapFinder import FindGap
                    #calling Find Gap such that chains with residues not connected will 
                    #have an attribute 'hasGap' and CA atoms have "gap" attribute
                    
                    if len(_set)!=0:
                         _set.sort()
                         mygap =FindGap(mats,mol.chains[ch],_set)
                         if hasattr(mol.chains[ch],'hasGap'):
                             for i in range(0,len(chatoms)):
                                 if hasattr(chatoms[i],"gap"):
                                     if i+1<=len(chatoms)-1:
                                         if chatoms[i].gap=='start':
                                             #indi=chatoms.index(chatoms[i])
                                             for at in _set:
                                                 if chatoms[i]==at:
                                                     indi =_set.index(at)
                                             if (indi,indi+1) in indices:
                                                 ind=indices.index((indi,indi+1))    
                                                 del indices[ind] 
                                            
                mol.geomContainer.atoms['CAsticks']=_set
                g = mol.geomContainer.geoms['CAsticks'] 
                if len(indices) == 0:
                    g.Set(visible=0, tagModified=False)
                else:
                    cRad = _set.cRad
                    scolors = map(lambda x: x.colors['CAsticks'], _set)
                    g.Set( vertices=_set.coords, faces=indices, radii=cRad,
                           materials=scolors, visible=1, quality=cquality,
                           tagModified=False,  inheritMaterial=False)

                # highlight selection
                selMols, selAtms = self.vf.getNodesByMolecule(self.vf.selection, Atom)
                lMolSelectedAtmsDict = dict( zip( selMols, selAtms) )
                lSelectedAtoms = lMolSelectedAtmsDict.get(mol, None)
                if lSelectedAtoms is not None:
                    lVertexClosestAtomSet = mol.geomContainer.atoms['CAsticks']
                    if len(lVertexClosestAtomSet) > 0:
                        lVertexClosestAtomSetDict = dict(zip(lVertexClosestAtomSet,
                                                             range(len(lVertexClosestAtomSet))))
                        highlight = [0] * len(lVertexClosestAtomSet)
                        for i in range(len(lSelectedAtoms)):
                            lIndex = lVertexClosestAtomSetDict.get(lSelectedAtoms[i], None)
                            if lIndex is not None:
                                highlight[lIndex] = 1
                        g.Set(highlight=highlight)


        ########################################################
        
        molecules, atmSets = self.getNodes(nodes)

        try:
            radii = molecules.allAtoms.radius
        except:
            self.vf.assignAtomsRadii(molecules, 
                                     overwrite=False,
                                     united=False,
                                     topCommand=False)

        for mol, atom in map(None, molecules, atmSets):
           #for chain in mol.chains:

             try:
                 #atm=chain.getAtoms().get(lambda x: x.name=='CA')
                 atm =atom.get(lambda x:x.name =='CA')
                 if len(atm)==0 and len(molecules)==1:
                    self.warningMsg("No CA atoms in %s"%mol.name) 
                    return
                 elif len(atm)==0 and len(molecules)>1:
                    print "No CA atoms in %s"%mol.name
                 if sticksBallsLicorice == 'Licorice':
                     drawCABalls(mol,atm , only, 0, negate, cradius, 0,
                           cquality)
                 elif sticksBallsLicorice == 'Sticks only':
                     drawCABalls(mol,atm , only, 1, negate, bRad, bScale,
                           bquality)
                 else:
                     drawCABalls(mol,atm , only, 0, negate, bRad, bScale,
                           bquality)
                 drawCASticks(mol,atm, only, negate, cradius, cquality)
                 
                                       
             except:
                 print 'ERROR command %s failed on molecule %s *****' %\
                       (self.name, mol.name)
                 if self.vf.hasGui and self.vf.guiVisible==1 \
                    and self.vf.withShell:
                     self.vf.GUI.pyshell.top.deiconify()
                 traceback.print_exc()
                 print 'ERROR *************************************'

            
        if only and len(self.vf.Mols) != len(molecules):
            mols = self.vf.Mols - molecules
            for mol in mols:
                negate = True
                only=0
                if sticksBallsLicorice == 'Licorice':
                    drawCABalls(mol, mol.allAtoms, only, 0, negate, cradius,
                          0, cquality)
                elif sticksBallsLicorice == 'Sticks only':
                    drawCABalls(mol, mol.allAtoms, only, 1, negate, bRad,
                          bScale, bquality)
                else:
                    drawCABalls(mol, mol.allAtoms, only, 0, negate, bRad,
                          bScale, bquality)
                drawCASticks(mol, mol.allAtoms, only, negate, cradius, cquality)

        redraw = False
        if kw.has_key("redraw") : redraw=True
        if self.createEvents:
            event = EditGeomsEvent('trace', [nodes,[only, negate, bRad,bScale, bquality, 
						cradius, cquality,sticksBallsLicorice]])
            self.vf.dispatchEvent(event)


displayBackboneTraceGuiDescr = {'widgetType':'Menu', 'menuBarName':
                                 'menuRoot', 'menuButtonName':'Display',
                                 'menuEntryLabel':'BackboneTrace'}

DisplayBackboneTraceGUI = CommandGUI()
DisplayBackboneTraceGUI.addMenuCommand('menuRoot', 'Display',
                                        'BackboneTrace')



class UndisplayBackboneTrace(DisplayCommand):
    """ The UndisplayBackboneTrace command is an interactive command to undisplay part of the molecule when represented as sticks and balls.
    \nPackage : Pmv
    \nModule  : displayCommands
    \nClass   : UnDisplayBackboneTrace
    \nCommand : undisplayBackboneTrace
    \nSynopsis:\n
        None <- undisplayBackboneTrace(nodes, **kw)\n
        nodes --- any set of MolKit nodes describing molecular components\n
        keywords --- undisplay, lines\n 
    """

    def onAddCmdToViewer(self):
        DisplayCommand.onAddCmdToViewer(self)
        #if not self.vf.hasGui: return 
        if not self.vf.commands.has_key('displayBackboneTrace'):
            self.vf.loadCommand('displayCommands', ['displayBackboneTrace'],
                                'Pmv',topCommand=0)


    def __call__(self, nodes, **kw):
        """None <- undisplayBackboneTrace(nodes, **kw)
           nodes: TreeNodeSet holding the current selection"""
        if not nodes: return
        kw['negate']= 1
        if type(nodes) is StringType:
            self.nodeLogString = "'" + nodes +"'"
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return
        apply(self.vf.displayBackboneTrace, (nodes,),kw)



class ShowMolecules(MVCommand):
    """The showMolecules command allows the user to show or hide chosen molecules.
    \nPackage : Pmv
    \nModule  : displayCommands
    \nClass   : ShowMolecules
    \nCommand : showMolecules
    \nSynopsis:\n
        None <--- showMolecules(molName, negate = 0, **kw)\n
        molName --- list of the string representing the name of the molecules to be hidden or shown\n
        negate --- Boolean Flag when True the molecules corresponding to the given names are hidden, when set to 0 they will be shown\n
        keywords --- show hide molecules\n
    \nEvents: generates ShowMoleculesEvent
    """

    def __init__(self):
        MVCommand.__init__(self)

        self.flag = self.flag | self.negateKw
        self.callbacks=[]
        self.force = 0

    def addCallback(self, f, event=None):
        """add a callback function to be called when the visibility 
        flag of a molecule is toggled. The function is called after the flag
        has been toggled and takes one argument which is the molecule"""
        assert callable(f)
        self.callbacks.append(f)


    def removeCallback(self, f, event=None):
        """remove a callback function called when the visibility 
        flag of a molecule is toggled. """
        self.callbacks.remove(f)


    def onRemoveObjectFromViewer(self, obj):
        if hasattr(obj, 'displayMode'):
            delattr(obj, 'displayMode')
        if self.vf.hasGui:
            if self.molList.has_key(obj.name):
                del self.molList[obj.name]
                if self.cmdForms.has_key('default'):
                    self.cmdForms['default'].descr.entryByName[obj.name]\
                                                        ['widget'].grid_forget()
            else:
                self.force = 1


    def onAddObjectToViewer(self, obj):
        if not self.vf.hasGui:
            return
        if not hasattr(self, 'molList') : self.molList = {}
        #if not self.vf.hasGui: return
        obj.geomName = filter(lambda x, geomC = obj.geomContainer:
                              geomC.geoms[x].visible == 1,
                              obj.geomContainer.geoms.keys())
        obj.geomName.remove('master')
                              
        self.molList[obj.name] = Tkinter.IntVar()
        self.molList[obj.name].set(1)

        if self.cmdForms.has_key('default'):
            if self.cmdForms['default'].root.state() == 'normal':
                form = self.cmdForms['default']
                cb = CallBackFunction(self.checkButton_cb,obj.name)
                entry = {'name':obj.name,
                         'widgetType': Tkinter.Checkbutton,
                         'defaultValue':self.molList[obj.name].get(),
                         'wcfg':{'text':obj.name+':'+'ON/OFF',
                                 'variable':self.molList[obj.name],
                                 'command':cb},
                         'gridcfg':{'sticky':Tkinter.W}}

                form.addEntry(entry)
                form.descr.entryByName[entry['name']] = entry
                form.f.pack(fill='both', expand=1)
                form.mf.pack(fill='both', expand=1)
            else:
                self.force = 1


    def doit(self, molName, negate=False):
        from types import TupleType, ListType
        if not type(molName) in [TupleType, ListType]:
            return
        mols = []
        for name in molName:
            mol = self.vf.Mols.NodesFromName(name)[0]
            mol.geomContainer.geoms['master'].Set(visible = not negate,
                                                  tagModified=False)
            mols.append(mol)
            # ????
            for f in self.callbacks:
                f(mol)
        if self.createEvents and len(mols):
            event = ShowMoleculesEvent( mols, visible = not negate)
            self.vf.dispatchEvent(event)

    def __call__(self, molName, negate=False, **kw):
        """None <- showMolecules(molName, negate=0, **kw)
           \nmolName : list of string name of molecules (mol.name)
           \nnegate  : flag when set to 1 hide the given molecule
        """
        if molName == 'all':
            molName = self.vf.Mols.name

        if isinstance(molName, TreeNode):
            molName = [molName.top.name]
        elif isinstance(molName, TreeNodeSet):
            molName = molName.top.uniq().name

        if not molName or not type(molName) in [TupleType, ListType]:
            return

        if not kw.has_key('redraw'): kw['redraw']=1
        kw['negate'] = negate
        apply( self.doitWrapper, (molName,), kw)
        # Should not be done here
        if self.vf.hasGui:
            for name in molName:
                self.molList[name].set(not negate)


    def buildFormDescr(self, formName='default'):

        if formName == 'default':
            idf = InputFormDescr(title = "show/hide molecules")
            if len(self.vf.Mols) == 0: return idf
            names = self.vf.Mols.name
            idf.append({'name':'checkall',
                        'widgetType':Tkinter.Button,
                        'wcfg':{'text':'Hide All',
                                'command':self.showHideAll_cb},
                        'gridcfg':{'sticky':'ew'}
                        })
            for name in self.vf.Mols.name:
                idf.append({'name':name, 
                            'widgetType': Tkinter.Checkbutton,
                            'defaultValue':self.molList[name].get(),
                            'wcfg':{'text':name+':'+'ON/OFF',
                                    'variable':self.molList[name],
                                    'command':CallBackFunction(self.checkButton_cb,name)},
                            'gridcfg':{'sticky':'w'}})
            return idf

    def checkButton_cb(self, molName):
        # checkbuttom checked var = 1 --> ON the mol is shown
        # checkbutton unchecked var = 0 --> OFF the mol is hidden
        show = self.molList[molName].get()
        self.doitWrapper([molName,], negate=not show, redraw=1)


    def showHideAll_cb(self):
        if not len(self.vf.Mols): return
        ebn = self.cmdForms['default'].descr.entryByName
        # Get the value of the check button
        w = ebn['checkall']['widget']
        value = ebn['checkall']['widget'].cget('text')
        if value == 'Show All':
            # show all the molecules
            w.configure(text='Hide All')
            value = 1
        else:
            w.configure(text='Show All')
            value = 0
        for molName in self.vf.Mols.name:
            ebn[molName]['wcfg']['variable'].set(value)
        self.doitWrapper(self.vf.Mols.name, negate=not value, redraw=True)


    def guiCallback(self):

        if not hasattr(self, 'molList'): self.molList = {}
        form = self.showForm('default', force = self.force, modal = 0,
                             blocking=0, scrolledFrame = 1, width=200,
                             height=150, onDestroy = self.dismissForm )

        close_button = Tkinter.Button(form.help.master,
                                         text='Close', command=self.dismissForm)
        close_button.grid(row=0,column=0,sticky='we')

    def dismissForm(self):
        if self.cmdForms.has_key('default'):
            self.cmdForms['default'].withdraw()
    


showMoleculeGuiDescr = {'widgetType':Tkinter.Button, 'barName':'Toolbar',
                        'buttonName':'show/hide molecule'}
        
ShowMoleculeGUI = CommandGUI()
ShowMoleculeGUI.addMenuCommand('menuRoot', 'Display', 'Show/Hide Molecule')


BHTree_CUT = 40.0

class BindGeomToMolecularFragmentBase(MVCommand):
    data = {}   # data will be shared between all instances of the class

from DejaVu.Geom import Geom
from DejaVu.IndexedGeom import IndexedGeom
from DejaVu.IndexedPolygons import IndexedPolygons
    
class BindGeomToMolecularFragment(BindGeomToMolecularFragmentBase):
    """Command to bind an Indexed Geometry to a molecule."""    

    def __init__(self):
        MVCommand.__init__(self)
        #self.cl_atoms = {}
        self.isDisplayed=0
        self.objects = {}

    def checkDependencies(self, vf):
        from bhtree import bhtreelib
        

    def doit(self, g, nodes, cutoff_from=3.5, cutoff_to=BHTree_CUT, instanceMatrices=None, **kw):
        mols = nodes.top.uniq()
        if len(mols) > 1:
            print "bindGeomToMolecularFragment: ERROR: atoms belong to more than one molecule"
            return
        mol = mols[0]

        #mol = self.vf.Mols.NodesFromName( molname )[0]
        cl_atoms = None
        geomC = mol.geomContainer

        reparent = True
        # check if geom g is already under the molecule's hierarchy of
        # DejaVu Objects

        obj = g
        while obj.parent:
            if g.parent==geomC.masterGeom:
                reparent=False
                break
            obj = obj.parent

        if mol:
            atoms = nodes.findType(Atom)
            gname = g.name
            vi= geomC.VIEWER
            vs = g.vertexSet.vertices.array
            if isinstance(g, IndexedGeom):
                fs = g.faceSet.faces.array
                fns = g.getFNormals()
            else:
                fs = fns = None
            #print "in doit: lenvs:", len(vs)
            cl_atoms = self.findClosestAtoms(vs, atoms, cutoff_from, cutoff_to, instanceMatrices)
            if cl_atoms is not None:
                if hasattr(g, 'mol') and g.mol==mol:
                    # we are binding to a new molecule
                    for a in g.mol.allAtoms:
                        del a.colors[gname]
                        del a.opacities[gname]
                if g.parent==None:   #add geometry to Viewer:
                    #vi.AddObject(g, parent=geomC.masterGeom, redo=0)
                    geomC.addGeom(g, parent=geomC.masterGeom, redo=0)
                    reparent = False
                if reparent: # need to reparent geometry
                    if vi:
                        vi.ReparentObject(g, geomC.masterGeom)
                    else:
                        oldparent = g.parent
                        oldparent.children.remove(g)
                        geomC.masterGeom.children.append(g)
                        g.parent = geomC.masterGeom
                    g.fullName = g.parent.fullName+'|'+gname
                geomC.atomPropToVertices[gname] = self.atomPropToVertices
                geomC.geomPickToAtoms[gname] = self.pickedVerticesToAtoms
                geomC.geomPickToBonds[gname] = None
                
                for a in mol.allAtoms:
                    a.colors[gname] = (1.,1.,1.)
                    a.opacities[gname] = 1.0

                g.userName = gname
                geomC.geoms[gname] = g
                g.mol = mol
                u_atoms = self.findUniqueAtomSet(cl_atoms, atoms )
                geomC.atoms[gname]=u_atoms
                #self.cl_atoms[gname] = cl_atoms
                #create a unique identifier for all atoms
                ids = map(lambda x, y: x.name+str(y), atoms, range(len(atoms)))
                atoms.sl_id = ids
                mol_lookup = {}
                i=0
                for id in ids:
                    mol_lookup[id] = i
                    i=i+1

                # highlight selection
                lAtomVerticesDict = {}
                for lIndex in range(len(cl_atoms)):
                    lAtomVerticesDict[atoms[cl_atoms[lIndex]]]=[]
                for lIndex in range(len(cl_atoms)):
                    lAtomVerticesDict[atoms[cl_atoms[lIndex]]].append(lIndex)

                self.data[g.fullName]={'cl_atoms':cl_atoms, 'fs':fs, 'fns':fns,
                                       'mol_lookup':mol_lookup, 'atoms':atoms,
                                       'atomVertices':lAtomVerticesDict}
                #print self.data[g.fullName]['atoms']
                
        return cl_atoms
            
    def pickedVerticesToAtoms(self, geom, vertInd):
        """Function called to convert picked vertices into atoms"""
        
        # this function gets called when a picking or drag select event has
        # happened. It gets called with a geometry and the list of vertex
        # indices of that geometry that have been selected.
        # This function is in charge of turning these indices into an AtomSet
        mol = geom.mol
        l = []
        #atom_inds = self.cl_atoms[geom.name]
        atom_inds = self.data[geom.fullName]['cl_atoms']
        #atoms = mol.allAtoms
        atoms  = self.data[geom.fullName]['atoms']
        for ind in vertInd:
            l.append(atoms[atom_inds[ind]])
        return AtomSet( AtomSet( l ) )


    def findUniqueAtomSet(self, atomIndices, atoms ):
        #atoms - array of indices of closest atoms
        l = []
        natoms = len(atoms)
        maxind = max(atomIndices)
        seen = {}
#        for i in range(maxind+1):
#            if i in atomIndices:
        for i in atomIndices:
            if not seen.has_key(i):
                l.append(atoms[i])
                seen[i] = 1
        atomset = AtomSet( l )
        return atomset

    def atomPropToVertices(self, geom, atoms, propName, propIndex=None):
        """Function called to map atomic properties to the vertices of the
        geometry"""
        
        if len(atoms)==0: return None
        #print "len atoms:", len(atoms)
        #print "propIndex:", propIndex
        #for a in atoms.data:
        #    print a.__dict__['number'],
        #print 
        # array of propperties of all atoms for the geometry.
        prop = []
        atoms = self.data[geom.fullName]['atoms']
        if propIndex is not None:
            for a in atoms:
                d = getattr(a, propName)
                prop.append( d[propIndex] )
        else:
            for a in atoms:
                prop.append( getattr(a, propName) )
        #atind = self.cl_atoms[geom.name]
        atind = self.data[geom.fullName]['cl_atoms']

        # get lookup col using closest atom indicies
        mappedProp = Numeric.take(prop, atind).astype('f')

        return mappedProp


    def __call__(self, geom, nodes, cutoff_from=3.5, cutoff_to=BHTree_CUT, instanceMatrices=None,
                 **kw):
       
        """cl_atoms<-bindGeomToMolecularFragment(geom, molname,
        cutoff_from=3.5, cutoff_to=10.0 )
        Finds the closest atom to each vertex of a given indexed geometry.
        Binds the geometry to the molecule.
        geom  is an input Geom object;
        molname is the name of an input molecule;
        cutoff_from is the initial distance from vertices in which the search
        for the closest atoms is performed. If no atoms are found,
        the search distance is gradually increased untill it reaches the
        'cutoff_to' value."""
        
        nodes = self.vf.expandNodes(nodes)
        if type(geom)==StringType:
            geom = self.vf.GUI.VIEWER.FindObjectByName(geom)
            
        #if isinstance(geom, IndexedPolygons):
        if isinstance(geom, Geom):
            cl_atoms = apply(self.doitWrapper, (
                geom , nodes, cutoff_from, cutoff_to, instanceMatrices), kw)
            if cl_atoms is None:
                print "Warning: no closest atoms found in cutoff : ", cutoff_to
                print geom.name, "is not bound to molecule "
                return 0
            return 1
        
    def guiCallback(self):
        val = self.showForm('bindGeom', force = 1, modal = 1)
        val = self.idf.form.checkValues()
        mol = None
        geom = None
        if len(val['mols']):
            mol = val['mols'][0]
        if len(val['geoms']):
            geom = val['geoms'][0]
        if not mol or not geom:
            return

        cutoff_from = float(val['cutoff_from'])
        cutoff_to = float(val['cutoff_to'])
        mol = self.vf.expandNodes(mol)
        cl_atoms = apply(self.doitWrapper, (self.objects[geom], mol,
                                cutoff_from, cutoff_to), {})
        if cl_atoms is None or len(cl_atoms) == 0:
            self.warningMsg("No atoms found in cutoff %.2f "%cutoff_to)
    
    def buildFormDescr(self, formName):
        if formName == "bindGeom":
            idf = self.idf = InputFormDescr(title = "Select Geometry and Molecule")
            objects = {}
            vi = self.vf.GUI.VIEWER
            for o in vi.rootObject.AllObjects():
                if isinstance(o, Geom):#IndexedPolygons):
                    if not hasattr(o, 'mol'):
                        objects[o.name]=o
            molecules = []
            for i in range(len(self.vf.Mols)):
                mol = self.vf.Mols[i]
                molParser = mol.parser
                molStr = molParser.getMoleculeInformation()
                molecules.append(mol.name)
            self.objects = objects
            sortedKeys = objects.keys()
            sortedKeys.sort()
            idf.append({'name': 'geoms',
                        'widgetType':Pmw.ComboBox,
                        'wcfg':{'labelpos': 'n',
                                'label_text':'Geometric object',
                                'scrolledlist_items': sortedKeys,
                                'scrolledlist_listbox_width': 5},
                        'gridcfg':{'sticky':'we', 'column': 0,
                                   'columnspan':2},
                        })
            idf.append({'name': 'mols',
                        'widgetType':Pmw.ComboBox,
                        'wcfg':{'labelpos': 'n',
                                'label_text':'Molecule',
                                'scrolledlist_items': molecules,
                                'scrolledlist_listbox_width': 5},
                        'gridcfg':{'sticky':'we', 'row': -1, 'column': 2,
                                   'columnspan':2},
                        })
            idf.append({'widgetType':Tkinter.Label,
                        'wcfg': {'text':"Specify cutoff interval \n(for finding atoms closest to object's surface):"},
                        'gridcfg':{'sticky':'we', 'columnspan':4}
                        })
            idf.append({'name':'cutoff_from',
                        'widgetType' : Pmw.EntryField,
                        'wcfg': {'labelpos':'w',
                                 'label_text' : "From: ",
                                 'entry_width' : 5,
                                 'value' :'3.5',
                                 'validate' : {'validator': 'real',
                                               'min': 0.2} },
                                 'gridcfg':{'sticky': 'we', 'column':0,}
                        })
            idf.append({'name':'cutoff_to',
                        'widgetType' : Pmw.EntryField,
                        'wcfg': {'labelpos':'w',
                                 'label_text' : "to: ",
                                 'entry_width' : 5,
                                 'value' :'10.0',
                                 'validate' : {'validator': 'real',
                                               'min': 0.2} },
                        'gridcfg':{'sticky': 'we', 'row':-1, 'column':1,}
                        })

            return idf
        
    def findClosestAtoms(self, obj_verts,  atoms,
                         cutoff_from=3.5, cutoff_to=BHTree_CUT,instanceMatrices=None ):
        """For every vertex in a given set of vertices finds the closest atom.
        Returns an array of corresponding atom indices. Based on bhtree
        library. """
        if not len(obj_verts):
            return None
        from bhtree import bhtreelib
        atom_coords = atoms.coords
        natoms = len(atom_coords)
        if instanceMatrices:
            coordv = Numeric.ones(natoms *4, "f")
            coordv.shape = (natoms, 4)
            coordv[:,:3] = atom_coords[:]
            new_coords = []
            ## for im in instanceMatrices:
##                 for v in coordv:
##                     atom_coords.append(list(Numeric.dot(im, v)))
            
            for m in instanceMatrices:
                new_coords.append(Numeric.dot(coordv, \
                                   Numeric.transpose(m))[:, :3])
            atom_coords = Numeric.concatenate(new_coords)
        print "len atom_coords: ", len(atom_coords)
        bht = bhtreelib.BHtree( atom_coords, None, 10)
        cl_atoms = []
        mdist = cutoff_from
        print "** Bind Geometry to Molecule Info: **"
        print "** looking for closest atoms (cutoff range: %2f-%2f)...   **"%(cutoff_from, cutoff_to)
        cl_atoms = bht.closestPointsArray(obj_verts, mdist)
        while len(cl_atoms) == 0 and mdist <cutoff_to:
            print "** ... no closest atoms found for cutoff = %2f; continue looking ... **"%mdist
            mdist=mdist+0.2
            cl_atoms = bht.closestPointsArray(obj_verts, mdist)
            #print "mdist: ", mdist, "  len cl_atoms: ", len(cl_atoms)
        print "**... done. %d closest atoms found within distance: %2f **"%(len(cl_atoms) , mdist)
        if instanceMatrices:
            if cl_atoms:
                return map(lambda x: x%natoms, cl_atoms)
        return cl_atoms
    
BindGeomToMolecularFragmentGUI = CommandGUI()
BindGeomToMolecularFragmentGUI.addMenuCommand('menuRoot', '3D Graphics','Bind Geometry To Molecule', index = 4)



class DisplayBoundGeom(DisplayCommand, BindGeomToMolecularFragmentBase):
    """Command to display/undisplay geometries that were bound to molecules with
    'bindGeomToMolecularFragment' command. """
    
    def checkDependencies(self, vf):
        from bhtree import bhtreelib

    def buildFormDescr(self, formName='default'):
        if formName == 'default':
            idf = DisplayCommand.buildFormDescr(self, formName)
            gnames = self.getBoundGeomNames()
            idf.append({'name':'geomNames',
                        'widgetType':Pmw.ScrolledListBox,
                        'tooltip':'surface to be display/undisplayed',
                        'wcfg':{'label_text':'Bound geometry: ',
                                'labelpos':'nw',
                                'items':gnames,
                                'listbox_selectmode':'extended',
                                'usehullsize': 1,
                                'hull_width':100,'hull_height':150,
                                'listbox_height':5,
                                },
                        'gridcfg':{'sticky': 'we'}})
            idf.append({'name':'nbVert',
                        'widgetType':Pmw.ComboBox,
                        'tooltip':'number of vertices in a triangle that have to belong\nto a selected atom, for that face to be shown',
                        'defaultValue':'1',
                        'wcfg':{'label_text':'nb. Vert Per face: ',
                                'labelpos':'w',
                                'scrolledlist_items': ['1', '2', '3']},
                        'gridcfg':{'sticky': 'we'}})
            return idf


    def guiCallback(self):
        # Update the comboBox with the name of the geometries
        if self.cmdForms.has_key('default'):
            geomNames = self.getBoundGeomNames()
            ebn = self.cmdForms['default'].descr.entryByName
            w = ebn['geomNames']['widget']
            w.clear()
            w.setlist(geomNames)
            
        val = DisplayCommand.getFormValues(self)
        if val:
            val['nbVert'] = int(val['nbVert'][0])
            apply( self.doitWrapper, (self.vf.getSelection(),), val )

    def getBoundGeomNames(self):
        # get all objects(geometries) that were bound with  'bindGeomToMolecularFragment' command:
        molecules = self.vf.getSelection().top.uniq()
        objects = self.data.keys()
        mol_geoms = []
        if not len(objects):
            return []
        for mol in molecules:
            # find geoms that were bound to molecule mol:
            for o in objects:
                obj = string.split(o, '|')[-1]
                if mol.geomContainer.geoms.has_key(obj):
                    g = mol.geomContainer.geoms[obj]
                    if g.viewer !=None: # checking that the geometry is still in the viewer.
                        if g.mol == mol:
                            mol_geoms.append(o)
        return mol_geoms


    def doit(self, nodes, geomNames=None, only=0, negate=0, nbVert=3):
        #print "nbVert: ", nbVert
        #print "geomNames:", geomNames
        if not geomNames:
            return
        molecules, atomSets = self.vf.getNodesByMolecule(nodes, Atom)
        if not molecules: return
        # get all objects(geometries) that were bound with  'bindGeomToMolecularFragment' command:
        for mol, atm  in map(None,molecules,atomSets):
            # find geoms that were bound to molecule mol:
            allatoms = mol.allAtoms
            for obj in geomNames:
                oname = string.split(obj, '|')[-1]
                # get the set of atoms for the geometry
                _set = mol.geomContainer.atoms[oname]

                #if negate, remove current atms from displayed _set
                if negate: _set = _set - atm

                #if only, replace displayed _set with current atms 
                else:
                    if only: _set = atm
                    else: 
                        _set = atm.union(_set)
                mol.geomContainer.atoms[oname]=_set
                g = mol.geomContainer.geoms[oname]
                if len(_set) == 0:
                    g.Set(visible=0, tagModified=False)
                    return
                # get the atom indices
                atomindices = []
                cl_atoms = self.data[obj]['cl_atoms']
                vs = []
                mol_lookup = self.data[obj]['mol_lookup']
                for a in _set:
                    if hasattr(a, "sl_id"):
                        ind = mol_lookup[a.sl_id]
                        atomindices.append(ind)
                cond = map(lambda x, y=atomindices: x in y, cl_atoms)
                #a new subset of vertex indices:
                nvs = Numeric.nonzero(cond) #returns indices of cond,
                                            #where its elements != 0

                #print "atom inds to display: " , nvs
                faces = self.data[obj]['fs']
                norms = self.data[obj]['fns']
                s = faces.shape
                ####################################
##                  fs_lookup = Numeric.zeros(s, 'i')
##                  for i in range(s[0]):
##                      for j in range(s[1]):
##                          f=faces[i][j]
##                          if f != -1:
##                              if f in nvs:
##                                  fs_lookup[i][j] = 1
##                  vs_per_face = Numeric.sum(fs_lookup, 1)
##                  cond = Numeric.greater_equal(vs_per_face, nbVert)
##                  nfs_ind = Numeric.nonzero(cond)
##                  print "len(nfs_ind):", len(nfs_ind)
##                  nfs = Numeric.take(faces, nfs_ind)
                #####################
                # find a subset of faces and face normals:
                from bhtree import bhtreelib
                from time import time
                t1=time()
                nvs = nvs.astype('i')
                nfs_ind = bhtreelib.findFaceSubset(nvs, faces, nbVert)#indices of
                                                                      #subset of faces
                nfs = Numeric.take(faces, nfs_ind)
                nfns = Numeric.take(norms, nfs_ind)
                t2=time()
                #print "time to loop: ", t2-t1
                #print "nfs.shape: ", nfs.shape
                if len(atomindices)==0:
                    g.Set(visible=0, tagModified=False)
                else:
                    col = mol.geomContainer.getGeomColor(oname)
                    g.Set(faces=nfs, fnormals = nfns, materials=col,
                          inheritMaterial=False, visible=1, tagModified=False)
                    if g.transparent:
                        opac = mol.geomContainer.getGeomOpacity(oname)
                        g.Set( opacity=opac, redo=0, tagModified=False)

                    # update texture coordinate if needed
                    if g.texture and g.texture.enabled and g.texture.auto==0:
                        mol.geomContainer.updateTexCoords[o](mol)


    def __call__(self, nodes, only=0, negate=0,
                 nbVert=Pmv.numOfSelectedVerticesToSelectTriangle, **kw):
        """None <- DisplayBoundGeom(nodes, only=0, negate=0, **kw)
           nodes  : TreeNodeSet holding the current selection
           only   : flag when set to 1 only the current selection will be
                    displayed
           negate : flag when set to 1 undisplay the current selection
           nbVert : Nb of vertices per triangle need to select a triangle"""
        if not kw.has_key('redraw'): kw['redraw']=1
        kw['only'] = only
        kw['negate'] = negate
        kw['nbVert'] = nbVert
        if type(nodes) is StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        apply( self.doitWrapper, (nodes, ), kw)


DisplayBoundGeomGUI = CommandGUI()
DisplayBoundGeomGUI.addMenuCommand('menuRoot', 'Display', "Bound Geometry")



class UndisplayBoundGeom(DisplayBoundGeom):
    def __call__(self, nodes, **kw):
        """None <- UndisplayBoundGeom(nodes, **kw)
           nodes  : TreeNodeSet holding the current selection (mv.getSelection())
           """
        kw['negate']= 1
        apply(self.vf.displayBoundGeom, (nodes,),kw)



class DisplayInteractionsCommand(MVCommand):
    """The DisplayInteractionsCommand class is used to display interactions between a 'ligand' and a 'receptor' molecule: the ligand is displayed with a msms surface...
    \nPackage : Pmv
    \nModule  : displayCommands
    \nClass   : DisplayInteractionsCommand
    """


    def onAddCmdToViewer(self):
        self.vf.loadModule('labelCommands', 'Pmv')
        self.vf.loadModule('displayCommands', 'Pmv')
        self.vf.loadModule('hbondCommands', 'Pmv')
        self.showHbatSpheres = Tkinter.IntVar()
        self.showCloseContactSpheres = Tkinter.IntVar()
        self.showSS = Tkinter.IntVar()
        self.showMM = Tkinter.IntVar()
        self.showMsms = Tkinter.IntVar()
        self.showResLabels = Tkinter.IntVar()
        self.showPiPi = Tkinter.IntVar()
        self.showPiCation = Tkinter.IntVar()
        self.infoType = Tkinter.StringVar()
        self.infoType.set("")
        self.infoTypeList = ["ligand contacts", "receptor contacts", "hydrogen bonds"]
        self.sphereType = Tkinter.StringVar()
        self.sphereType.set("wireframe")
        self.sphereTypeList = ["wireframe", "solid"]
        self.managed_sets = {}  #current sets to display
        for v in [self.showCloseContactSpheres, self.showSS, self.showMsms, self.showResLabels]:
            v.set(1)
        self.masterGeom = Geom('displayIntGeom', shape=(0,0), 
                                pickable=0, protected=True)
        self.masterGeom.isScalable = 0
        display_geoms_list  = self.vf.GUI.VIEWER.findGeomsByName('display_geoms')
        if display_geoms_list==[]:
            display_geoms = Geom("display_geoms", shape=(0,0), protected=True)
            self.vf.GUI.VIEWER.AddObject(display_geoms, parent=self.vf.GUI.miscGeom)
            display_geoms_list = [display_geoms]
        display_geoms = display_geoms_list[0]
        display_int_geom = Geom('displayInteractions_geoms', shape=(0,0), 
                                pickable=0, protected=True)
        display_int_geom.isScalable = 0
        self.vf.GUI.VIEWER.AddObject(display_int_geom, parent = display_geoms)
        self.pi_pi_geom = Cylinders('pi_pi',quality=50,
                            inheritLineWidth=0, lineWidth=10,
                            radii=(0.7), pickable=0,
                            materials = ((1,1,0),),
                            inheritMaterial=False)
        self.t_shaped_geom = Cylinders('t_shaped',quality=50,
                            inheritLineWidth=0, lineWidth=10,
                            radii=(0.7), pickable=0,
                            materials = ((1,0,0),),
                            inheritMaterial=False)
        self.cation_pi_geom = Cylinders('cation_pi',quality=50,
                            inheritLineWidth=0, lineWidth=10,
                            radii=(0.2, 0.7), pickable=0,
                            materials = ((1,1,0),),
                            inheritMaterial=False)
        self.pi_cation_geom = Cylinders('pi_cation',quality=50,
                            inheritLineWidth=0, lineWidth=10,
                            radii=((0.7, 0.01),), pickable=0,
                            materials = ((1,1,0),),
                            inheritMaterial=False)
        for obj in [self.pi_pi_geom, self.t_shaped_geom, self.cation_pi_geom,
                self.pi_cation_geom]:
            self.vf.GUI.VIEWER.AddObject(obj, parent=display_int_geom)
            from opengltk.OpenGL import GL
            obj.Set(inheritFrontPolyMode = 0, 
                    frontPolyMode=GL.GL_LINE,
                    opacity=(.3,.3), inheritLineWidth=0,
                    inheritCulling=0, lineWidth=1)

    def checkDependencies(self, vf):
        if not vf.hasGui:
            return 'ERROR'


    def update_managed_sets(self, event=None):
        rDict = self.intDescr.results
        #from macromolecule
        key_list = [('macro_close_res','mResLab'),   ('ss_res','mSSRes'),\
                    ('macro_close_non_hb','mClose'), ('macro_hb_atoms','mhbnds'), \
                    ('lig_close_non_hb','lClose'), ('lig_hb_atoms','lhbnds'), \
                    ('lig_close_carbons', 'lcloseCs')]
        for k1,k2 in key_list:
            nodes = rDict[k1]
            if k2 in self.vf.sets.keys():
                self.vf.sets.pop(k2)
                self.vf.saveSet(nodes, k2, addToDashboard=False)
            else:
                self.vf.saveSet(nodes, k2, addToDashboard=True)


    def getSSResidues(self, mol):
        mols = mol.findType(Protein) 
        from MolKit.protein import ResidueSet
        res = ResidueSet()
        for m in mols:
            for k, v in m.geomContainer.atoms.items():
	            if k[:3] in ['Coi', 'Hel', 'Str', 'Tur']:
		            res += v
        return res


    def setupUndoBefore(self, lig, macro):
        #???color???
        lig = self.vf.expandNodes(lig)[0].top
        macro = self.vf.expandNodes(macro)[0].top
        kw = {'log':0,'topCommand':0, 'redraw':True}
        kw['lineWidth'] = self.vf.displayLines.lastUsedValues['default']['lineWidth']
        macro_gca = macro.geomContainer.atoms
        geomSet = macro_gca['bonded']
        boSet =  macro_gca['bondorder'].uniq()
        if len(boSet) == 0:
            kw['displayBO']=False
        else:
            kw['displayBO']=True
        # The undo of a display command is to display ONLY what was
        # displayed before, if something was already displayed
        self.addUndoCall( (geomSet,), kw, self.vf.displayLines.name)
        kw = {'log':0,'topCommand':0, 'redraw':True}
        old_colors = macro.findType(Atom).colors['lines']
        #old_colors = macro.allAtoms.colors['lines']
        self.addUndoCall( (geomSet,old_colors,), kw, self.vf.color.name)
        #self.vf.labelByProperty(macro_res, textcolor=(0.1, 0.1, 0.1),  properties=['name'],log=0)
        geomSet = macro_gca['ResidueLabels']
        kw = self.vf.labelByProperty.lastUsedValues['default']
        if len(geomSet):
            kw['only'] = 1
        else:
            geomSet = macro.findType(Residue)
            kw['negate'] = 1
        self.addUndoCall( (geomSet,), kw, self.vf.labelByProperty.name)
        kw = {'log':0,'topCommand':0, 'redraw':True}
        geomSet = macro_gca['cpk']
        if len(geomSet):
            kw['only'] = 1
        else:
            geomSet = macro.findType(Atom)
            #geomSet = macro.allAtoms
            kw['negate'] = 1
        self.addUndoCall( (geomSet,), kw, self.vf.displayCPK.name)
        #macro ss
        res = self.getSSResidues(macro)
        if len(res):
             kw = {'log':0,'topCommand':0, 'redraw':True, 'negate':1}
             self.addUndoCall( (res,), kw, self.vf.ribbon.name)
        #kw = {'log':0,'topCommand':0, 'redraw':True, 'negate':1}
        #self.addUndoCall( (macro.findType(Atom),), kw, self.vf.ribbon.name)
        #self.addUndoCall( (macro.allAtoms,), kw, self.vf.ribbon.name)
        #ligand
        lgca = lig.geomContainer.atoms
        defaultValues = self.vf.displaySticksAndBalls.lastUsedValues['default']
        kw={}
        kw['bRad'] = defaultValues['bRad']
        kw['bScale'] = defaultValues['bScale']
        kw['bquality'] = defaultValues['bquality']
        kw['cradius'] = defaultValues['cradius']
        kw['cquality'] = defaultValues['cquality']
        kw['sticksBallsLicorice'] = defaultValues['sticksBallsLicorice']
        ballset = lgca['balls']
        stickset = lgca['sticks']
        if len(ballset)==0:
            # no balls displayed
            if len(stickset) == 0: # negate
                # no sticks displayed 
                kw['negate'] = True
                kw['redraw'] = True
                #self.addUndoCall( (lig.allAtoms,), kw,
                self.addUndoCall( (lig.findType(Atom),), kw,
                                  self.vf.displaySticksAndBalls.name )
            else:
                # noballs was on
                kw['negate'] = False
                kw['redraw'] = True
                kw['only'] = True
                self.addUndoCall( (stickset,), kw,
                                  self.vf.displaySticksAndBalls.name )
        else:
            kw['redraw'] = True
            kw['only'] = True
            self.addUndoCall( (stickset,), kw,
                              self.vf.displaySticksAndBalls.name )
        lgcg = lig.geomContainer.geoms
        surfName = lig.name + '_msms'
        self.addUndoCall( (lig,), {'surfName':surfName, 'negate':1}, self.vf.displayMSMS.name)
        lgca = lig.geomContainer.atoms
        geomSet = lgca['cpk']
        kw = {'log':0,'topCommand':0, 'redraw':True}
        if len(geomSet):
            #undisplay all
            kw['negate'] = 1
            self.addUndoCall( (lig.allAtoms,), kw, self.vf.displayCPK.name)
            #redisplay current only...
            kw['negate'] = 0
            self.addUndoCall( (geomSet,), kw, self.vf.displayCPK.name)
        else:
            geomSet = lig.allAtoms
            kw['negate'] = 1
            self.addUndoCall( (geomSet,), kw, self.vf.displayCPK.name)
        #extrudedSS
        keys_to_exclude = ['sticks', 'AtomLabels', 'CAsticks', 'bonded', 'cpk', 'ChainLabels',\
                'ProteinLabels', 'ResidueLabels', 'nobnds', 'balls', 'bondorder', 'lines', 'CAballs']
        displayed_res = ResidueSet()
        gc = macro.geomContainer
        for k in gc.atoms.keys():
            if not k in keys_to_exclude:
                displayed_res += gc.atoms[k].findType(Residue)
        if len(displayed_res):
            kw = {'log':0,'topCommand':0, 'only':True, 'redraw':True}
            self.addUndoCall( (displayed_res,), kw, self.vf.displayExtrudedSS.name)
        else:
            kw = {'log':0,'topCommand':0, 'redraw':True, 'negate':True}
            self.addUndoCall( (macro.chains.residues,), kw, self.vf.displayExtrudedSS.name)
        old_color = self.vf.GUI.VIEWER.currentCamera.backgroundColor
        if len(old_color)>3: old_color = list(old_color[:3])
        self.addUndoCall( [old_color,], {}, self.vf.setbackgroundcolor.name)
        self.addUndoCall( (lig, macro), {}, 'displayInteractions.restoreCpk')
        self.addUndoCall( (), {}, 'displayInteractions.close')
        self.addUndoCall( (), {}, 'hbondsAsSpheres.dismiss_cb')
        self.addUndoCall( (), {}, 'setbackgroundcolor.dismiss_cb')


    def updateCpk(self, lig, macro):
        m_cpk = macro[0].top.geomContainer.geoms['cpk']
        l_cpk = lig[0].top.geomContainer.geoms['cpk']
        self.vf.GUI.VIEWER.CurrentCameraBackgroundColor((1.00,1.00,1.00))
        from opengltk.OpenGL import GL
        for g in [m_cpk, l_cpk]:
            g.inheritFrontPolyMode = 0
            if self.sphereType.get()=='wireframe':
                g.Set(frontPolyMode=GL.GL_LINE)
                g.Set(opacity=[.3,.3])
                #g.Set(inheritLineWidth=0)
                #g.Set(inheritCulling=0)
                g.Set(lineWidth=1, inheritLineWidth=0)
                g.Set(slices=25, stacks=25)
            else:
                #solid
                g.Set(frontPolyMode=GL.GL_FILL)
                #g.Set(opacity=[1., 1.])


    def restoreCpk(self, lig, macro, **kw ):
        from opengltk.OpenGL import GL
        macro = self.vf.expandNodes(macro)[0].top
        lig = self.vf.expandNodes(lig)[0].top
        from opengltk.OpenGL import GL
        m_cpk = macro.geomContainer.geoms['cpk']
        l_cpk = lig.geomContainer.geoms['cpk']
        for g in [m_cpk, l_cpk]:
            g.inheritFrontPolyMode = 0
            if self.sphereType.get()=='solid':
                g.Set(frontPolyMode=GL.GL_FILL)
            else:
                g.Set(frontPolyMode=GL.GL_LINE)
                g.Set(opacity=[.3,.3])
                g.Set(lineWidth=1, inheritLineWidth=0)
                g.Set(slices=25, stacks=25)
            #g.Set(opacity=[1., 1.])


    def guiCallback(self):
        """called each time the 'Visualize Complex in Context' button is pressed"""
        if not len(self.vf.Mols):
            self.warningMsg('no molecules in viewer')
            return 
        if not hasattr(self, 'form'):
            self.buildForm()
        else:
            try:
                self.form.deiconify()
            except:
                self.buildForm()


    def Accept_cb(self, event=None):
        self.form.withdraw()
        nodesToCheck1 = self.ifd1.entryByName['group1']['widget'].get()
        nodesToCheck2 = self.ifd1.entryByName['group2']['widget'].get()
        if not len(nodesToCheck1):
            self.warningMsg('no atoms in first set')
            return
        if not len(nodesToCheck2):
            self.warningMsg('no atoms in second set')
            return
        self.Close_cb()
        return self.doitWrapper(nodesToCheck1, nodesToCheck2)


    def buildForm(self):
        ifd = self.ifd1 = InputFormDescr(title = "Specify two groups of nodes for interactions display:")
        ifd.append({'name':'keyLab',
                    'widgetType':Tkinter.Label,
                    'text':"First is treated as 'ligand' and second as 'receptor'",
                    'gridcfg':{'sticky':'w'}})
        ifd.append({'name': 'group1',
            'wtype':StringSelectorGUI,
            'widgetType':StringSelectorGUI,
            'wcfg':{ 'molSet': self.vf.Mols,
                    'vf': self.vf,
                    'tooltip': 'display solvent-excluded-surface geometry for ligand',
                    'all':1,
                    'crColor':(0.,1.,.2),
            },
            'gridcfg':{'sticky':'we', 'columnspan':2 }})
        ifd.append({'name': 'group2',
            'wtype':StringSelectorGUI,
            'widgetType':StringSelectorGUI,
            'wcfg':{ 'molSet': self.vf.Mols,
                    'vf': self.vf,
                    'all':1,
                    'crColor':(1.,2.,0.),
            },
            'gridcfg':{'sticky':'we', 'columnspan':2}})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Ok',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we'},
            'command':self.Accept_cb})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Cancel',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we', 'column':1,'row':-1},
            'command':self.Close_cb})
        self.form = self.vf.getUserInput(self.ifd1, modal=0, blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW', self.Close_cb)
        self.form.autoSize()


    def __call__(self, lig, macro, **kw):
        """None<-displayInteractions(self, lig, macro)\n
        \nlig: 
        \nmacro: 
        """
        try:
            lig = self.vf.expandNodes(lig)
        except:
            raise  IOError
        try:
            macro = self.vf.expandNodes(macro)
        except:
            raise  IOError
        return apply(self.doitWrapper, (lig, macro,), kw)


    def cleanUpCrossSet(self):
        chL = []
        for item in self.vf.GUI.VIEWER.rootObject.children:
            if isinstance(item, CrossSet) and item.name[:8]=='strSelCr':
                chL.append(item)
        if len(chL):
            for item in chL: 
                item.Set(vertices=[], tagModified=False)
                self.vf.GUI.VIEWER.Redraw()
                self.vf.GUI.VIEWER.RemoveObject(item)


    def Close_cb(self, event=None):
        self.cleanUpCrossSet()
        try:
            self.form.withdraw()
        except:
            pass
        try:
            self.close()
        except:
            pass


    def revert(self, event=None, **kw):
        try:
            s = self.vf.undoCmdStack[-1]
            while len(s)>1 and s[1]!=self.name:
                self.vf.undo()
                s = self.vf.undoCmdStack[-1]
            self.vf.undo()
            self.form.withdraw()
            self.close()
        except:
            pass


    def close(self, event=None, **kw):
        try:
            self.displayform.destroy()
            delattr(self, 'displayform')
            delattr(self, 'ifd2')
            for g in [self.pi_pi_geom, self.cation_pi_geom, 
                        self.pi_cation_geom]:
                g.Set(visible=0)
        except:
            pass


    def save(self,filename=None,event=None):
        self.vf.saveImage.guiCallback()


    def updatePercentCutoff(self, lig, macro, event=None):
        percentCutoff = self.ifd2.entryByName['vdwPercentCutoff']['widget'].get()
        msg = 'resetting percentCutoff to ' + str(percentCutoff)
        self.warningMsg(msg)
        self.build(lig, macro, percentCutoff)
        

    def buildDisplayForm(self, lig, macro, event=None):
        ifd = self.ifd2 = InputFormDescr(title='Interactions Display Options')
        ifd.append({'name': 'msmsCB',
                    'widgetType':Tkinter.Checkbutton,
                    'tooltip': "display solvent-excluded-surface geometry for 'ligand'",
                    'wcfg':{'text':"display msms",
                            'variable':self.showMsms},
                    'command': CallBackFunction(self.updateMsms, lig, macro),
                    'gridcfg':{'sticky':Tkinter.W, 'columnspan':3}})
        ifd.append({'widgetType':Tkinter.Label,
                    'tooltip': 'set which spheres to display and whether to use wireframe or solid',
                    'wcfg': {'text':"display spheres as"},
                    'gridcfg':{'sticky':'w'} })
        ifd.append({'widgetType':Pmw.ComboBox,
            'name':'sphere_type',
            'wcfg':{'entryfield_value':self.sphereType.get(),
                    'labelpos':'w',
                    'listheight':'50',
                    'scrolledlist_items': self.sphereTypeList,
                    'selectioncommand': CallBackFunction(self.updateSphereDisplay, lig, macro),
                    },
            'gridcfg':{'sticky':'w', 'row':-1, 'column':1}})
        ifd.append({'widgetType':Tkinter.Label,
                    'tooltip': 'set which spheres to display ',
                    'wcfg': {'text':"on atoms in:"},
                    'gridcfg':{'sticky':'e'} })
        ifd.append({'name': 'closeAtsCB',
                    'widgetType':Tkinter.Checkbutton,
                    'tooltip': "display spheres on pairs of atoms closer than sum of vdw radii*Scaling Factor.\nWhen msms surface for 'ligand' is displayed, spheres are displayed only on the 'receptor'",
                    'wcfg':{'text':"close contact",
                            'variable':self.showCloseContactSpheres},
                    'command': CallBackFunction(self.updateCCCpk, lig, macro),
                    'gridcfg':{'sticky':Tkinter.W, 'row':-1, 'column':1}})
        ifd.append({'name': 'hbondsCB',
                    'widgetType':Tkinter.Checkbutton,
                    'tooltip': "display spheres on atoms involved in hydrogen bonds\nbetween ligand atoms and receptor atoms.\nWhen msms surface for ligand is displayed, spheres are displayed only on the receptor\n(Hbonds are displayed as small green spheres)",
                    'wcfg':{'text':"hydrogen bonds",
                            'variable':self.showHbatSpheres},
                    'command': CallBackFunction(self.updateHBonds,lig, macro),
                    'gridcfg':{'sticky':Tkinter.W, 'row':-1, 'column':2}})
        ifd.append({'name':'vdwPercentCutoff',
                    'widgetType':ThumbWheel,
                    'tooltip': "used in finding 'close atoms' which are closer than:\ndistance = (atom1.vdw+atom2.vdw)*scaling_factor\n(smaller values find fewer contacts; larger values more)",
                    'wcfg':{'labCfg':{'text': 'VDW Scaling Factor'},
                             'showLabel':1, 'width':150,
                             'width':75, 'height':20,
                             'min':0.1, 'type':float, 'precision':2,
                             'callback': CallBackFunction(self.updatePercentCutoff, lig, macro),
                             'value':1.0, 'continuous':0, 'oneTurn':2,
                             'wheelPad':2, 'height':20},
                    'gridcfg':{'sticky':'e', 'columnspan':3}})
        ifd.append({'name': 'ssCB',
                    'widgetType':Tkinter.Checkbutton,
                    'tooltip': 'display ribbon secondary structure for sequences of >3\nresidues in receptor with atoms close to ligand atoms.\nGaps of 1 residue are allowed',
                    'wcfg':{'text':"display ribbon for near residues",
                            'variable':self.showSS},
                    'command': CallBackFunction(self.showHideSecondaryStructure, lig, macro),
                    'gridcfg':{'sticky':Tkinter.W, 'columnspan':2}})
        ifd.append({'name': 'ssALLCB',
                    'widgetType':Tkinter.Checkbutton,
                    'tooltip': 'show/hide ribbon secondary structure for all residues',
                    'wcfg':{'text':"for all residues",
                            'variable':self.showMM},
                    'command': CallBackFunction(self.updateMM, lig, macro),
                    'gridcfg':{'sticky':Tkinter.W, 'row':-1, 'column':2 }})
        ifd.append({'name': 'resLabCB',
                    'widgetType':Tkinter.Checkbutton,
                    'tooltip': "display labels on all residues in 'receptor' which have\none or more atoms close to an atom in the 'ligand'",
                    'wcfg':{'text':"display labels on residues",
                            'variable':self.showResLabels},
                    'command': self.updateResLabels,
                    'gridcfg':{'sticky':Tkinter.W, 'columnspan':3}})
        ifd.append({'widgetType':Tkinter.Label,
                    'tooltip': 'print list of residue contacts in python shell',
                    'wcfg': {'text':"output list of:"},
                    'gridcfg':{'sticky':'w'} })
        ifd.append({'widgetType':Pmw.ComboBox,
            'name':'info_type',
            'wcfg':{ 'entryfield_value':self.infoType.get(),
                    'labelpos':'w',
                    'listheight':'70',
                    'scrolledlist_items': self.infoTypeList,
                    'selectioncommand': self.printInfo,
                    },
            'gridcfg':{'sticky':'w', 'row':-1, 'column':1, 'columnspan':2}})
        ifd.append({'name': 'piLabCB',
                    'widgetType':Tkinter.Checkbutton,
                    'tooltip': "display pi-pi interactions between 'ligand' and 'receptor'. Note: initial calculation is slow...",
                    'wcfg':{'text':"display pi-pi interactions",
                            'variable':self.showPiPi},
                    'command': self.updatePiPi,
                    'gridcfg':{'sticky':Tkinter.W}})
        ifd.append({'name': 'piCationLabCB',
                    'widgetType':Tkinter.Checkbutton,
                    'tooltip': "display cation-pi and pi-cation interactions between 'ligand' and 'receptor'. Note: initial calculation is slow...",
                    'wcfg':{'text':"display pi-cation interactions",
                            'variable':self.showPiCation},
                    'command': self.updatePiCation,
                    'gridcfg':{'sticky':Tkinter.W, 'row':-1, 'column':2}})
        ifd.append({'name': 'revertB',
                    'widgetType': Tkinter.Button,
                    'text':'Revert',
                    'tooltip': "Revert to previous display and destroy this form",
                    'wcfg':{'bd':4},
                    'gridcfg':{'sticky':'we'},
                    'command':self.revert})
        ifd.append({'name': 'closeB',
                    'widgetType': Tkinter.Button,
                    'text':'Close',
                    'tooltip': "Close without changing display\nUse 'Edit->Undo displayInteractions' to restore",
                    'wcfg':{'bd':4},
                    'gridcfg':{'sticky':'we', 'row':-1, 'column':1},
                    'command':self.close})
        ifd.append({'name': 'saveButton',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Save Image'},
                    'command': self.save,
                    'gridcfg':{'sticky':'we','row':-1,'column':2}})
        self.displayform = self.vf.getUserInput(self.ifd2, modal=0, blocking=0)
        self.displayform.root.protocol('WM_DELETE_WINDOW', self.close)
        e = self.ifd2.entryByName['sphere_type']['widget']._entryfield
        e._entryFieldEntry.configure(width=8)
        e2 = self.ifd2.entryByName['info_type']['widget']._entryfield
        e2._entryFieldEntry.configure(width=12)
        self.displayform.autoSize()
          

    def updateSphereDisplay(self, lig, macro, event=None):
        oldVal = self.sphereType.get()
        if hasattr(self, 'ifd2'):
            t = self.ifd2.entryByName['sphere_type']['widget'].get()
            self.sphereType.set(t)
            if oldVal!=t:
                if t =='wireframe':
                    self.updateCpk(lig, macro)
                elif t=='solid':
                    self.restoreCpk(lig, macro)
        else:
            if self.sphereType.get()=='solid':
                self.restoreCpk(lig, macro)
            else:
                self.updateCpk(lig, macro)


    def printInfo(self, event=None):
        t = self.ifd2.entryByName['info_type']['widget'].get()
        if t =='ligand contacts':
            self.print_ligand_residue_contacts()
        elif t=='receptor contacts':
            self.print_macro_residue_contacts()
        if t=='hydrogen bonds':
            self.print_hydrogen_bonds()
        self.infoType.set(t)


    def print_macro_residue_contacts(self, event=None):
        print "\n\nresidues in 'receptor'-> 'ligand' residues in close contact"
        self.intDescr.print_macro_residue_contacts()
        print "\n"


    def print_ligand_residue_contacts(self, event=None):
        print "\n\nresidues in 'ligand'-> 'receptor' residues in close contact"
        self.intDescr.print_ligand_residue_contacts()
        print "\n"


    def print_hydrogen_bonds(self, event=None):
        print "\n\nhydrogen bonds (donor residue->acceptor residue(s))"
        self.intDescr.print_hb_residue()
        print "\n"


    def updateMsms(self, lig, macro): 
        rDict = self.intDescr.results
        lig_all_ats = rDict['lig_close_atoms']
        lig_hb_ats = rDict['lig_hb_atoms']
        lig_close_non_hb = rDict['lig_close_non_hb']
        surfName = lig[0].top.name + '_msms'
        if self.showMsms.get():
            #when display msms, hide ligand cpk
            self.vf.displayCPK(lig_all_ats, negate=1, topCommand=0)
            lig_atoms = lig.findType(Atom)
            self.vf.displayMSMS(lig_atoms, topCommand=0)
            g = lig[0].top.geomContainer.geoms[surfName]
            from opengltk.OpenGL import GL
            g.inheritFrontPolyMode = 0
            if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
                g.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False)
            g.Set(opacity=[.75,.75])
            lig_close_atoms = rDict['lig_close_atoms']
            if len(lig_close_atoms):
                self.vf.colorByAtomType(lig_close_atoms, geomsToColor= [surfName, 'balls', 'sticks'], topCommand=0 ) 
            try:
                g.sortPoly()
            except:
                pass
        else:
            #when hide msms, show ligand cpk
            cpk_ats = AtomSet()
            if self.showCloseContactSpheres.get():
                cpk_ats += lig_close_non_hb[:]
            if self.showHbatSpheres.get():
                cpk_ats += lig_hb_ats[:]
            self.vf.displayCPK(cpk_ats, scaleFactor=1.0, quality=25, topCommand=0)
            self.vf.colorByAtomType(cpk_ats, geomsToColor= ['cpk'], topCommand=0 )
            lig_atoms = lig.findType(Atom)
            self.vf.displayMSMS(lig_atoms, negate=1)
        self.updateSphereDisplay(lig, macro)


    def updateHBonds(self, lig, macro): 
        c = self.vf.hbondsAsSpheres
        rDict = self.intDescr.results
        macro_hb_atoms = rDict['macro_hb_atoms']
        lig_hb_atoms =  rDict['lig_hb_atoms']
        if not len(macro_hb_atoms + lig_hb_atoms):
            return
        h_ats = rDict['macro_hb_atoms'][:]
        if not self.showMsms.get():
            h_ats += rDict['lig_hb_atoms'][:]
        if self.showHbatSpheres.get(): 
            self.vf.displayCPK(h_ats, scaleFactor=1.0, quality=25, topCommand=0)
            self.vf.colorByAtomType(h_ats, geomsToColor= ['cpk'], topCommand=0 )
        else:
            self.vf.displayCPK(h_ats, negate=1, topCommand=0)
        self.updateSphereDisplay(lig, macro)


    def updateCCCpk(self, lig, macro, event=None):
        rDict = self.intDescr.results
        cpk_atoms = rDict['macro_close_non_hb'][:]
        if not self.showMsms.get():
            cpk_atoms+=rDict['lig_close_non_hb'][:]
        if self.showCloseContactSpheres.get(): 
            self.vf.displayCPK(cpk_atoms, scaleFactor=1.0, quality=25, topCommand=0)
            self.vf.colorByAtomType(cpk_atoms, geomsToColor= ['cpk'], topCommand=0 )
        else:
            self.vf.displayCPK(cpk_atoms, negate=1, topCommand=0)
        self.updateSphereDisplay(lig, macro)


    def showHideSecondaryStructure(self, lig, macro):
        rDict = self.intDescr.results
        ss_res = rDict['ss_res']
        if self.showSS.get():
            if len(ss_res)>3:
                if not self.showMM.get():
                    self.vf.displayExtrudedSS(ss_res.findType(Atom), only=True, topCommand=0)
                else:
                    self.vf.displayExtrudedSS(macro.findType(Atom), only=True, topCommand=0)
        else:
            #just hide the ribbon for the adjacent-close-residue sequences
            self.vf.displayExtrudedSS(ss_res.atoms, negate=True, topCommand=0)


    def updateSecondaryStructure(self, lig, macro):
        from opengltk.OpenGL import GL
        #attempt to show ribbon for contiguous residues in macromolecule
        rDict = self.intDescr.results
        ss_res = rDict['ss_res']
        if self.showSS.get():
            if len(ss_res)>3:
                if not self.showMM.get():
                    self.vf.ribbon(ss_res.findType(Atom), topCommand=0)
                else:
                    self.vf.ribbon(macro.findType(Atom), topCommand=0)
                macro[0].top.geomContainer.geoms['secondarystructure'].Set(culling=GL.GL_NONE)
            else:
                self.showSS.set(0)
        elif self.showMM.get():
            self.vf.ribbon(macro.findType(Atom), topCommand=0)
            macro[0].top.geomContainer.geoms['secondarystructure'].Set(culling=GL.GL_NONE)


    def updateMM(self, lig, macro, event=None):
        macro_atoms = macro.findType(Atom)
        if self.showMM.get():
            keys_to_exclude = ['sticks', 'AtomLabels', 'CAsticks', 'bonded', 'cpk', 'ChainLabels',\
                    'ProteinLabels', 'ResidueLabels', 'nobnds', 'balls', 'bondorder', 'lines', 'CAballs']
            displayed_atoms = AtomSet()
            gc = macro[0].top.geomContainer
            for k in gc.atoms.keys():
                if not k in keys_to_exclude:
                    displayed_atoms += gc.atoms[k].findType(Atom)
            if len(displayed_atoms)!= len(macro_atoms):
                self.vf.ribbon(macro_atoms, topCommand=0)
            else:
                self.vf.displayExtrudedSS(macro_atoms, topCommand=0 )
        else:
            ss_res = self.intDescr.results['ss_res']
            if self.showSS.get() and len(ss_res)>3:
                self.vf.displayExtrudedSS(ss_res.atoms, only=True, topCommand=0)
            else:
                self.vf.displayExtrudedSS(macro_atoms, negate=True, topCommand=0)


    def reset(self, lig, macro):
        gca = macro[0].top.geomContainer.atoms
        macro_cpk = gca['cpk']
        self.vf.displayCPK(macro_cpk, negate=True, topCommand=0)
        macro_res_lab = gca['ResidueLabels']
        self.vf.labelByProperty(macro_res_lab, textcolor=(0.15,0.15,0.15), negate=True, topCommand=0)
        #macro_ss_res = macro.findType(Residue)
        #self.vf.displayExtrudedSS(macro_ss_res, negate=True, topCommand=0)
        mtops = macro.top.uniq()
        for t in mtops:
            macro_ss_res = self.getSSResidues(t)
            if len(macro_ss_res):
                try:
                    self.vf.displayExtrudedSS(macro_ss_res, negate=True, topCommand=0)
                except:
                    pass
        ltops = lig.top.uniq()
        for t in ltops:
            macro_ss_res = self.getSSResidues(t)
            if len(macro_ss_res):
                try:
                    self.vf.displayExtrudedSS(macro_ss_res, negate=True, topCommand=0)
                except:
                    pass
            lig_cpk = t.geomContainer.atoms['cpk']
            self.vf.displayCPK(lig_cpk, negate=True, topCommand=0)
        #lig_cpk = lig[0].top.geomContainer.atoms['cpk']
        #self.vf.displayCPK(lig_cpk, negate=True, topCommand=0)


    def buildLigandDisplay(self, lig, macro):
        #1. displayligand as sticksNballs, labelled by name
        #check whether the ligand is already displayed
        lgc = lig[0].top.geomContainer
        lig_atoms = lig.findType(Atom)
        if len(lgc.atoms['sticks'])!=len(lig_atoms):
            self.vf.displaySticksAndBalls(lig_atoms, cquality=25, bquality=25, cradius=0.1, 
                            bRad=0.15,topCommand=0)
            self.vf.colorByAtomType(lig, geomsToColor=['sticks', 'balls'], topCommand=0) #byAtom
            g = lgc.geoms['sticks']
            if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
                g.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False)
        #1b. displayligand as msms, with low opacity
        surfName = lig[0].top.name+ '_msms'
        self.vf.computeMSMS(lig, surfName, perMol=0,topCommand=0, display=self.showMsms.get())
        l_msms = lgc.geoms[surfName]
        l_msms.Set(inheritMaterial=0, opacity=[.75,.75],)
        if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
            l_msms.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False,)
        l_msms._setTransparent(1)
        lig.msmsatoms = lgc.atoms[surfName][:]
        self.vf.color(lig.findType(Atom),[(0.5,0.5,0.5),], [surfName], topCommand=0)
        g = lgc.geoms[surfName]
        lig_close_atoms = self.intDescr.results['lig_close_atoms']
        if len(lig_close_atoms):
            self.vf.colorByAtomType(lig_close_atoms, geomsToColor=[surfName, 'balls', 'sticks'],topCommand=0)
        l_msms.sortPoly()


    def buildCloseAtoms(self, lig, macro):
        mgc = macro[0].top.geomContainer
        macro_atoms = macro.findType(Atom)
        self.vf.displayLines(macro_atoms, negate=1,topCommand=0)
        rDict = self.intDescr.results
        macro_close_res = rDict['macro_close_res']
        macro_hbond_res = rDict['macro_hb_res']
        macro_res = macro_close_res + macro_hbond_res
        if len(macro_res):
            self.vf.displayLines(macro_res.atoms,topCommand=0)
            self.vf.labelByProperty(macro_res, textcolor=(0.15, 0.15, 0.15),  
                                    properties=['name'],topCommand=0)
            reslabels = mgc.geoms['ResidueLabels']
            reslabels.Set(fontScales =(0.3, 0.3, 0.3))
            self.vf.colorByAtomType(macro_close_res.atoms, geomsToColor= ['lines', 'cpk'], topCommand=0 )
        surfName = lig[0].top.name+ '_msms'
        lig_atoms = lig.findType(Atom)
        self.vf.color(lig_atoms, [(0.5,0.5,0.5),], [surfName],topCommand=0)
        self.vf.color(lig_atoms.get(lambda x:x.element=='C'), [(0.5,0.5,0.5),], 
                        ['balls', 'sticks'],topCommand=0)
        lig_close_atoms = rDict['lig_close_atoms']
        if len(lig_close_atoms):
            self.vf.colorByAtomType(lig_close_atoms, geomsToColor= [surfName, 'balls', 'sticks'],topCommand=0 )
            
 
    def buildHbondDisplay(self, lig, macro):
        lig_atoms = lig.findType(Atom)
        macro_atoms = macro.findType(Atom)
        rDict = self.intDescr.results
        c = self.vf.hbondsAsSpheres
        c.dismiss_cb()
        hbas = rDict['macro_hbas']
        if len(hbas):
            self.vf.displayLines(hbas, topCommand=0)
            self.vf.colorByAtomType(hbas, geomsToColor= ['lines'], topCommand=0 )
            #display hbonds as spheres 
            all = lig_atoms + macro_atoms
            c(all, topCommand=0)
            c.spacing_esw.set(.35)
            c.radii_esw.set(.06)
            self.vf.colorByAtomType(hbas, geomsToColor= ['sticks', 'balls', 'lines'], topCommand=0)
        surfName = lig[0].top.name+ '_msms'
        lig_cs = rDict['lig_close_carbons']
        if len(lig_cs): 
            self.vf.color(lig_cs, [(1,1,1),], [surfName,'balls', 'sticks'], topCommand=0)
        cpk_ats = AtomSet()
        if self.showCloseContactSpheres.get():
            cpk_ats += rDict['macro_close_non_hb'][:]
            if not self.showMsms.get():
                cpk_ats += rDict['lig_close_non_hb'][:]
        if self.showHbatSpheres.get(): 
            cpk_ats += rDict['macro_hb_atoms'][:]
            if not self.showMsms.get():
                cpk_ats += rDict['lig_hb_atoms'][:]
        if len(cpk_ats):
            self.vf.displayCPK(cpk_ats, scaleFactor=1.0, quality=25, topCommand=0)
            self.vf.colorByAtomType(cpk_ats, geomsToColor= ['cpk'], topCommand=0 )
            self.updateSphereDisplay(lig, macro)


    def build(self, lig, macro, percentCutoff=1.):
        from MolKit.interactionDescriptor import InteractionDescriptor
        #(1)
        self.intDescr = InteractionDescriptor(lig, macro, percentCutoff)
        self.reset(lig, macro)
        self.vf.GUI.VIEWER.stopAutoRedraw()
        self.buildLigandDisplay(lig, macro)
        self.buildCloseAtoms(lig, macro)
        self.buildHbondDisplay(lig, macro)
        self.updateSphereDisplay(lig, macro)
        self.updateSecondaryStructure(lig,macro)
        # add an input form here to toggle 
        # various displayed geometries on and off
        if not hasattr(self, 'displayform'):
            self.buildDisplayForm(lig, macro)
        macro.bindingSite = True
        self.update_managed_sets()
        self.vf.GUI.VIEWER.startAutoRedraw()
        c = self.vf.setbackgroundcolor
        if len(c.cmdForms):
            f = c.cmdForms.values()[0]
            try:
                if not f.f.master.master.winfo_ismapped():
                    self.vf.setbackgroundcolor.guiCallback()
            except:
                pass
        else:
            self.vf.setbackgroundcolor.guiCallback()
        self.update_managed_sets()


    def updatePiCation(self, event=None):
        rDict = self.intDescr.results
        #add_geom = False
        if not 'cation_pi' in rDict.keys():
            self.intDescr.detectPiInteractions()
        cation_pi = rDict['cation_pi']
        pi_cation = rDict['pi_cation']
        if len(cation_pi)==0 and len(pi_cation)==0:
            self.warningMsg('no cation_pi or pi_cation interactions detected')
            self.showPiCation.set(0)
            return
        if self.showPiCation.get():
            verts = []
            faces = []
            radii = []
            ctr = 0
            #these are ordered ligand_receptor 
            #and can be ligand_cation, receptor_pi OR ligand_pi, receptor_cation
            if len(cation_pi):
                for first,second in cation_pi: 
                    #either (atom, list of atoms) OR (list, atom)
                    if type(first)==ListType:
                        center1 = (Numeric.add.reduce(AtomSet(first).coords)/len(first)).tolist()
                        radii.append(0.7)
                    else:
                        center1 = (first.coords)
                        radii.append(0.1)
                    if type(second)==ListType:
                        center2 = (Numeric.add.reduce(AtomSet(second).coords)/len(second)).tolist()
                        radii.append(0.7)
                    else:
                        center2 = (second.coords)
                        radii.append(0.1)
                    faces.append((ctr,ctr+1))
                    verts.append(center1)
                    verts.append(center2)
                    ctr += 2
                self.cation_pi_geom.Set(radii=radii, faces=faces, 
                                        vertices=verts, visible=1)
            verts = []
            faces = []
            radii = []
            ctr = 0
            if len(pi_cation):
                for first,second in pi_cation: #either (atom, list of atoms)
                    if type(first)==ListType:
                        center1 = (Numeric.add.reduce(AtomSet(first).coords)/len(first)).tolist()
                        radii.append(0.7)
                    else:
                        center1 = (first.coords)
                        radii.append(0.1)
                    if type(second)==ListType:
                        center2 = (Numeric.add.reduce(AtomSet(second).coords)/len(second)).tolist()
                        radii.append(0.7)
                    else:
                        center2 = (second.coords)
                        radii.append(0.1)
                    faces.append((ctr,ctr+1))
                    verts.append(center1)
                    verts.append(center2)
                    ctr += 2
                self.pi_cation_geom.Set(radii=radii, faces=faces, 
                                            vertices=verts, visible=1)
        else:
            self.cation_pi_geom.Set(visible=0)
            self.pi_cation_geom.Set(visible=0)
    

    def updatePiPi(self, event=None):
        rDict = self.intDescr.results
        add_geom = False
        if not 'pi_pi' in rDict.keys():
            self.intDescr.detectPiInteractions()
            add_geom = True
        pi_pi = rDict['pi_pi']
        if not len(pi_pi):
            self.warningMsg('no pi_pi interactions detected')
            self.showPiPi.set(0)
            return
        if self.showPiPi.get():
            verts = []
            faces = []
            ctr = 0
            for first,second in pi_pi: #either (atom, list of atoms)
                center1 = (Numeric.add.reduce(first.coords)/len(first)).tolist()
                center2 = (Numeric.add.reduce(second.coords)/len(second)).tolist()
                faces.append((ctr,ctr+1))
                verts.append(center1)
                verts.append(center2)
                ctr += 2
            self.pi_pi_geom.Set(faces=faces, vertices=verts, visible=1)
        else:
            self.pi_pi_geom.Set(visible=0)
        
    
    def updateResLabels(self, event=None):
        rDict = self.intDescr.results
        macro_close_res = rDict['macro_close_res'] + rDict['macro_hb_res']
        show = self.showResLabels.get()
        negate = not show
        self.vf.labelByProperty(macro_close_res, negate=negate, 
                                textcolor=(0.15, 0.15, 0.15),  
                                properties=['name'],topCommand=0)


    def doit(self, lig, macro, **kw):
        self.build(lig, macro)


displayInteractionsCommandGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                            'menuButtonName':'Display',
                            'menuEntryLabel':'Complex',
                                    }


DisplayInteractionsCommandGUI=CommandGUI()
DisplayInteractionsCommandGUI.addMenuCommand('menuRoot', 'Display', 'Interactions')


commandList = [
    {'name':'displayBackboneTrace', 'cmd':DisplayBackboneTrace(),
     'gui':DisplayBackboneTraceGUI},
    {'name':'displaySticksAndBalls', 'cmd':DisplaySticksAndBalls(),
     'gui':DisplaySticksAndBallsGUI},
    {'name':'displaySSSB', 'cmd':DisplaySSSB(), 'gui':DisplaySSSBGUI},
    {'name':'displayCPK','cmd': DisplayCPK(), 'gui': DisplayCPKGUI},
    {'name':'displayLines','cmd': DisplayLines(), 'gui': DisplayLinesGUI},
    {'name':'undisplayLines','cmd': UndisplayLines(), 'gui': None},
    {'name':'undisplayCPK','cmd': UndisplayCPK(), 'gui': None},
    {'name':'undisplaySticksAndBalls','cmd': UndisplaySticksAndBalls(),
     'gui': None},
    {'name':'undisplayBackboneTrace','cmd': UndisplayBackboneTrace(), 'gui': None},
     {'name':'showMolecules','cmd': ShowMolecules(), 'gui': ShowMoleculeGUI},
    {'name':'DisplayBoundGeom', 'cmd':DisplayBoundGeom(), 'gui':DisplayBoundGeomGUI},
    {'name':'UndisplayBoundGeom', 'cmd':UndisplayBoundGeom(), 'gui':None},
    {'name':'displayInteractions', 'cmd':DisplayInteractionsCommand(), 'gui':DisplayInteractionsCommandGUI},
    #{'name':'displayBondOrder', 'cmd': DisplayBondOrder(), 'gui':DisplayBOGUI}
    {'name':'displayCPKByProperty','cmd': DisplayCPKByProperty(), 'gui': DisplayCPKByPropertyGUI},
    ]

def initModule(viewer):
    for dict in commandList[:-1]:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
