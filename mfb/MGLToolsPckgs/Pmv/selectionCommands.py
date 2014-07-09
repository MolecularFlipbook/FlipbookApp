## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Michel F. SANNER and Ruth HUEY
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################


# $Header: /opt/cvs/python/packages/share1.5/Pmv/selectionCommands.py,v 1.165.2.9 2011/10/05 17:24:57 sargis Exp $
#
# $Id: selectionCommands.py,v 1.165.2.9 2011/10/05 17:24:57 sargis Exp $
#
from ViewerFramework.VF import VFEvent

class SelectionEvent(VFEvent):
    pass

import Tkinter, types, string, Pmw, os
import time
from SimpleDialog import SimpleDialog
import numpy

from Pmv.mvCommand import MVCommand, MVAtomICOM
from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Atom, AtomSet, Molecule, MoleculeSet, AtomSetSelector
from MolKit.protein import Residue, Chain, ResidueSet, ChainSet, Protein, ProteinSet
from MolKit.protein import ResidueSetSelector
from MolKit.stringSelector import StringSelector

from ViewerFramework.VFCommand import CommandGUI, ICOM, ActiveObject
##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser,\
                                                ExtendedSliderWidget

from DejaVu.Spheres import Spheres
from DejaVu.Cylinders import Cylinders
from DejaVu.IndexedPolygons import IndexedPolygons

import Pmv
if hasattr( Pmv, 'numOfSelectedVerticesToSelectTriangle') is False:
    Pmv.numOfSelectedVerticesToSelectTriangle = 1
        
        
class MVSelectCommand(MVCommand, MVAtomICOM):
    """Class for modfying the current selection in a molecule Viewer.
       \nselection --- a TreeNodeSet holding the current selection. Modfied by SubClasses implementing a specific selection operation
       \nlevel --- level at which selection occurs
    \nPackage : Pmv
    \nModule  : selectionCommands
    \nClass   : MVSelectCommand
    \nCommand : select
    \nSynopsis:\n
    currentSelection <- select(nodes, negate=False, only=False, klass=None)
    \nRequired Arguments:\n
        nodes --- can be a string, a TreeNode or a treeNodeSet
    \nOptional Arguments:\n    
        negate --- is 1 nodes are removed from current selection
        \nonly  --- is  1 the current selection is replaced by the nodes
        \nklass ----is omitted class of objects in nodes is used, else
                  nodes is converted to a set of objects of type Klass and
                  current selection level is set to klass
    """


    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        MVAtomICOM.__init__(self)
        #self.flag = self.flag | self.objArgOnly
        #self.flag = self.flag | self.negateKw
        # current selection. Modfied by SubClasses implementing a specific
        # selection operation
        self.selection = TreeNodeSet()

    def onAddObjectToViewer(self, obj):
        if self.vf.hasGui and self.vf.commands.has_key('dashboard'):
            self.vf.dashboard.resetColPercent(obj, '_selectionStatus')
        
    def setupUndoBefore(self, nodes, negate=False,
                    only=False, klass=None, xor=False,
                    intersect=False):
        kw={}
        #if len(self.selection):
        if len(self.vf.selection):
            kw['only'] = 1
            self.addUndoCall( (self.vf.selection,), kw, self.name )
        else:
            self.addUndoCall( (), {}, self.vf.clearSelection.name )

    def __call__(self, nodes, negate=False, only=False, klass=None, 
                        xor=False, intersect=False, **kw):
        """currentSelection <- select(nodes, negate=False, only=False, 
                                klass=None, xor=False, intersect=False )
        \nRequired Arguments:\n
            nodes --- can be a string, a TreeNode or a treeNodeSet
        \nOptional Arguments:\n
            negate --- is 1 nodes are removed from current selection
            \nonly  --- is  1 the current selection is replaced by the nodes
            \nklass ----is omitted class of objects in nodes is used, else
                  nodes is converted to a set of objects of type Klass and
                  current selection level is set to klass   
        """
        if type(nodes) is types.StringType:
           self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        #if len(nodes)==0: return self.selection
        if len(nodes)==0: return self.vf.selection
        if klass is None: klass = nodes[0].__class__
        if klass != self.vf.selectionLevel:
            self.vf.setSelectionLevel(klass, topCommand=0, setupUndo=0, callListener=0)
        #if klass != self.vf.ICmdCaller.level.value:
        #    self.vf.setIcomLevel(klass, busyIdle=0, log=0)
        kw['negate']= negate
        kw['only']= only
        kw['xor']= xor
        kw['intersect']= intersect
        return apply( self.doitWrapper, (nodes,), kw )


    def doit(self, nodes, negate=False, only=False, xor=False, intersect=False):
        """add/remove nodes to the current selection
at this point it is assumed that nodes is of the same type as the
current selection
"""
        if len(nodes)==0: return self.vf.selection

        if only:
            setOn = nodes
            setOff = self.vf.selection - nodes
            self.vf.selection = nodes

        elif len(self.vf.selection): # something was selected before
            #in this case have to make selection into nodes.__class__
            if self.vf.selection.__class__!= nodes.__class__:
                self.vf.selection = nodes.__class__(self.vf.selection.data)
                #also set the level here if necessary
                self.vf.selectionLevel = nodes.elementType
            if negate: # nodes will be unselected
                setOn = None
                setOff = nodes
                self.vf.selection = self.vf.selection - nodes
            elif xor: # selected elements of node will be deselected and
                      # undelected will be selected
                setOff = self.vf.selection & nodes
                setOn = nodes 
                self.vf.selection = self.vf.selection ^ nodes
            elif intersect:
                setOff = self.vf.selection ^ nodes
                setOn = self.vf.selection & nodes
                self.vf.selection = self.vf.selection & nodes
            else: # or
                setOff = None
                setOn = nodes
                self.vf.selection = self.vf.selection | nodes

        elif not negate: # nothing was selected before
            setOff = None
            setOn = nodes
            self.vf.selection = nodes.copy()
        else:
            setOff = setOn = None
            
        # if the selection level was set on an empty selection without
        # specifying a KlassSet we have to set the proper class here
        #if len(self.selection) > 0:
            #obj = self.selection[0]
            #if self.selection.__class__ != obj:
                #self.selection = obj.setClass(self.selection.data)

        if len(self.vf.selection): 
            #remove possible duplicates
            newVal = self.vf.selection.uniq()
            if len(newVal)<len(self.vf.selection):
                # in this case duplicates are removed
                # but selection is no longer ordered
                self.vf.selection = newVal

        if not self.vf.hasGui:
            return self.vf.selection

        self.updateSelectionFeedback()
        self.highlightSelection()

        event = SelectionEvent(self.vf.selection, setOn=setOn, setOff=setOff)
        self.vf.dispatchEvent(event)

        return self.vf.selection
        

    def highlightSelection(self):
        # highlight selection
        selMols, selAtms = self.vf.getNodesByMolecule(self.vf.selection, Atom)
        allMols = set( self.vf.Mols[:] )
        unselectedMols = allMols.difference(selMols)
        for mol in unselectedMols:
            for geomName, lGeom in mol.geomContainer.geoms.items():
                if isinstance(lGeom, Spheres) \
                  or isinstance(lGeom, Cylinders) \
                  or (    isinstance(lGeom, IndexedPolygons) \
                      and hasattr(mol.geomContainer,'msmsAtoms') and mol.geomContainer.msmsAtoms.has_key(geomName) ):
                    lGeom.Set(highlight=[])
                elif isinstance(lGeom, IndexedPolygons) \
                  and lGeom.parent.name == 'secondarystructure':
                    lGeom.Set(highlight=[])

        selMols2, selResidueSets = self.vf.getNodesByMolecule(self.vf.selection, Residue)
        molSelectedResiduesDict = dict( zip( selMols2, selResidueSets) )
        for mol, selectedResidueSet in molSelectedResiduesDict.items():
            for lGeom in mol.geomContainer.geoms.values():
                if isinstance(lGeom, IndexedPolygons) and lGeom.parent.name == 'secondarystructure':
                    highlight = [0] * len(lGeom.vertexSet.vertices.array)
                    for selectedResidue in selectedResidueSet:
                        if hasattr(lGeom, 'resfacesDict') and lGeom.resfacesDict.has_key(selectedResidue):
                            for lFace in lGeom.resfacesDict[selectedResidue]:
                                for lVertexIndex in lFace:
                                    highlight[int(lVertexIndex)] = 1
                    lGeom.Set(highlight=highlight)

        for mol, atoms in map(None, selMols, selAtms):
            for geomName, lGeom in mol.geomContainer.geoms.items():
                if   isinstance(lGeom, Spheres) \
                  or isinstance(lGeom, Cylinders):
                    lAtomSet = mol.geomContainer.atoms[geomName]
                    if len(lAtomSet) > 0:
                        lAtomSetDict = dict(zip(lAtomSet, range(len(lAtomSet))))
                        highlight = [0] * len(lAtomSet)
                        for i in range(len(atoms)):
                            lIndex = lAtomSetDict.get(atoms[i], None)
                            if lIndex is not None:
                                highlight[lIndex] = 1
                        lGeom.Set(highlight=highlight)
                elif isinstance(lGeom, IndexedPolygons):
                  if hasattr(mol.geomContainer,'msmsAtoms') and mol.geomContainer.msmsAtoms.has_key(geomName):
                    lAtomSet = mol.geomContainer.msmsAtoms[geomName]
                    if len(lAtomSet) > 0:
                        lAtomSetDict = dict(zip(lAtomSet, range(len(lAtomSet))))
                        lAtomIndices = []
                        for i in range(len(atoms)):
                            lIndex = lAtomSetDict.get(atoms[i], None)
                            if lIndex is not None:
                                lAtomIndices.append(lIndex)
                        lSrfMsms = mol.geomContainer.msms[geomName][0]
                        lvf, lvint, lTri = lSrfMsms.getTriangles(lAtomIndices, 
                                                                 selnum=Pmv.numOfSelectedVerticesToSelectTriangle,
                                                                 keepOriginalIndices=1)
                        highlight = [0] * len(lGeom.vertexSet.vertices)
                        for lThreeIndices in lTri:
                            highlight[int(lThreeIndices[0])] = 1
                            highlight[int(lThreeIndices[1])] = 1
                            highlight[int(lThreeIndices[2])] = 1
                        lGeom.Set(highlight=highlight)
                  elif self.vf.bindGeomToMolecularFragment.data.has_key(lGeom.fullName) \
                    and self.vf.bindGeomToMolecularFragment.data[lGeom.fullName].has_key('atomVertices'):
                      bindcmd = self.vf.bindGeomToMolecularFragment
                      lSelectedAtoms = atoms
                      if len(lSelectedAtoms) > 0:
                        lAtomVerticesDict = bindcmd.data[lGeom.fullName]['atomVertices']
                        highlight = [0] * len(lGeom.vertexSet.vertices)
                        for lSelectedAtom in lSelectedAtoms:
                            lVertexIndices = lAtomVerticesDict.get(lSelectedAtom, [])
                            for lVertexIndex in lVertexIndices:
                                highlight[lVertexIndex] = 1
                        lGeom.Set(highlight=highlight)



    def startICOM(self):
        #print "in select.startICOM: mv.selectionLevel=", self.vf.selectionLevel
        #print "mv.selection=", self.vf.selection
        #print "in select.startICOM: mv.ICmdCaller.level.value=", self.vf.ICmdCaller.level.value
        self.vf.setSelectionLevel( self.vf.ICmdCaller.level.value, setupUndo=0)

    
    def setLevel(self, Klass, KlassSet=None):
        print "this method is deprecated"
        return "ERROR"
        #assert issubclass(Klass, TreeNode)
        #if Klass==self.vf.ICmdCaller.level.value:
        #    return self.vf.ICmdCaller.level.value
        #self.vf.ICmdCaller.level.Set(Klass)
       # 
       # if len(self.selection) > 0:
       #     newsel = self.selection.findType(Klass, uniq=1)
       #     if newsel:
       #         self.selection = newsel
       #     else:
       #         s = "level %s not found for current selection" % \
       #             Klass.__name__
       #         self.vf.warningMsg(s)
       #         return self.vf.ICmdCaller.level.value
       # else:
       #     if KlassSet:
       #         self.selection = KlassSet()
#
#        self.updateSelectionFeedback()
#        return self.vf.ICmdCaller.level


    def updateSelectionFeedback(self):
        self.updateInfoBar()
        self.updateSelectionIcons()
        

    def updateInfoBar(self):
        if self.vf.hasGui:
            if self.vf.selectionLevel:
                #msg = '\t Current selection: %d %s(s)' % ( len(self.selection),
                #                          self.vf.ICmdCaller.level.value.__name__)
                msg = '%d %s(s)' % ( len(self.vf.selection),
                                     self.vf.selectionLevel.__name__ )
            else:
                msg = '0 %s(s)'% self.vf.selectionLevel__name__
            self.vf.GUI.pickLabel.configure( text=msg )

        
    def updateSelectionIcons(self):
        """update selection icons"""
        #if SelectionSpheres is currently turned on: 
        if self.vf.userpref['Selection Object']['value'] in ['spheres', 'crosses']:
            # if there is no selection: turn all spheres off
            if len(self.vf.selection)==0:
                for mol in self.vf.Mols:
                    if self.vf.userpref['Selection Object']['value'] == 'spheres':
                        mol.geomContainer.geoms['selectionSpheres'].Set(visible=0, tagModified=False)
                    else:
                        mol.geomContainer.geoms['selectionCrosses'].Set(visible=0, tagModified=False)
            else:
                selMols, selAtms = self.vf.getNodesByMolecule(self.vf.selection,
                                                              Atom)
                for mol, atms in map(None, selMols, selAtms):
                    if self.vf.userpref['Selection Object']['value'] == 'spheres':
                        g = mol.geomContainer.geoms['selectionSpheres']
                    else:
                        g = mol.geomContainer.geoms['selectionCrosses']
                    #need to get nodes in this mol
                    if self.vf.viewSelectionIcon=='labels':
                        lab = ('O',)*len(atms)
                        g.Set(vertices=atms.coords, labels=lab, visible=1,
                              tagModified=False)
                    else:
                        g.Set(vertices=atms.coords, visible=1,
                              tagModified=False)
                #molecules w/ no atoms selected don't
                nonselMols = self.vf.Mols - selMols
                for mol in nonselMols:
                     if self.vf.userpref['Selection Object']['value'] == 'spheres':
                         mol.geomContainer.geoms['selectionSpheres'].Set(visible=0, tagModified=False)
                     else:
                         mol.geomContainer.geoms['selectionCrosses'].Set(visible=0, tagModified=False)
                    
            if self.vf.hasGui:
                self.vf.GUI.VIEWER.Redraw()

        #if SelectionSpheres is currently turned off: 
        # turn off all spheres and  update 
        else:
            for mol in self.vf.Mols:
                mol.geomContainer.geoms['selectionSpheres'].Set(
                    visible=0, tagModified=False)


    def clear(self):
        self.vf.selection.data = []
        self.updateSelectionFeedback()


    def dump(self):
        for o in self.vf.selection:
            self.message( o.full_name() )


      
class MVAddSelectCommand(MVSelectCommand):
    """This Command adds to the current selection
    \nPackage : Pmv
    \nModule  : selectionCommands
    \nClass   : MVAddSelectCommand
    \nCommand : addselect
    \nSynopsis:\n 
        currentSelection <--- addselect(nodes, klass=None, **kw)
    \nRequired Arguments:\n       
        nodes --- TreeNodeSet holding the current selection
        \nklass --- if specified nodes are converted to a set of that type otherwise
                  and selection level is set to Klass.
    """
    def __call__(self, nodes, klass=None, **kw):
        """currentSelection <- addselect(nodes, klass=None, **kw)
           \nnodes --- TreeNodeSet holding the current selection
           \nklass --- if specified nodes are converted to a set of that type otherwise
                  and selection level is set to Klass.
        """
        kw['negate']= 0
        kw['klass'] = klass
        apply( self.vf.select, (nodes,), kw )

        
class MVXorSelectCommand(MVSelectCommand):
    """This Command xors the current selection
    \nPackage : Pmv
    \nModule  : selectionCommands
    \nClass   : MVXorSelectCommand
    \nCommand : xorselect
    \nSynopsis:\n 
        currentSelection <--- xorselect(nodes, klass=None, **kw)
    \nRequired Arguments:\n       
        nodes --- TreeNodeSet holding the current selection
        \nklass --- if specified nodes are converted to a set of that type otherwise
                  and selection level is set to Klass.
    """
    def __call__(self, nodes, klass=None, **kw):
        """currentSelection <- xorselect(nodes, klass=None, **kw)
           \nnodes --- TreeNodeSet holding the current selection
           \nklass --- if specified nodes are converted to a set of that type otherwise
                  and selection level is set to Klass.
        """
        kw['negate']= 0
        kw['only']= 1
        kw['klass'] = klass
        if len(self.vf.selection):
            current = self.vf.selection.findType(nodes.setClass)
            new_sel = current ^ nodes
        else:
            new_sel = nodes
        apply( self.vf.select, (new_sel,), kw )
        #apply( self.vf.select, (nodes,), kw )


        
class MVDeSelectCommand(MVSelectCommand):
    """This Command deselects the current selection
    \nPackage : Pmv
    \nModule  : selectionCommands
    \nClass   : MVDeSelectCommand
    \nCommand : deselect
    \nSynopsis:\n 
        currentSelection <--- deselect(nodes, klass=None, **kw)
    \nRequired Arguments:\n       
        nodes --- TreeNodeSet holding the current selection
        \nklass --- if specified nodes are converted to a set of that type otherwise
                  and selection level is set to Klass.
    """
    def __call__(self, nodes, klass=None, **kw):
        """currentSelection <- deselect(nodes, klass=None, **kw)
           \nnodes --- TreeNodeSet holding the current selection
           \nklass --- if specified nodes are converted to a set of that type otherwise
                  and selection level is set to Klass.
        """
        kw['negate']= 1
        kw['klass'] = klass
        apply( self.vf.select, (nodes,), kw )



class MVClearSelection(MVCommand):
    """ MVClearSelect implements method to clear the current selection.
    \nPackage : Pmv
    \nModule  : selectionCommands
    \nClass   : MVClearSelection
    \nCommand : clearSelection
    \nSynopsis:\n
        None <- clearSelection(**kw)
   """
        
    def setupUndoBefore(self):
        select = self.vf.select
        if len(self.vf.selection):
            self.addUndoCall( (self.vf.selection,), {}, select.name )

    def guiCallback(self, event=None):
        self.doitWrapper()

        
    def doit(self):
        if self.createEvents:
            event = SelectionEvent(self.vf.selection, setOn=None,
                                   setOff=self.vf.selection)
            self.vf.dispatchEvent(event)
        self.vf.select.clear()

        if not self.vf.hasGui:
            return

        for mol in self.vf.Mols:
            for geomName, lGeom in mol.geomContainer.geoms.items():
                if   isinstance(lGeom, Spheres) \
                  or isinstance(lGeom, Cylinders) \
                  or isinstance(lGeom, IndexedPolygons):
                    lGeom.Set(highlight=[])

        
    def __call__(self, **kw):
        """None <- clearSelection(**kw)"""
        
        apply( self.doitWrapper, (), kw )
        
MVClearSelectionGUI = CommandGUI()
from moleculeViewer import ICONPATH
MVClearSelectionGUI.addToolBar('Clear', icon1 = 'eraser.gif', 
                             type = 'ToolBarButton', icon_dir=ICONPATH,
                             balloonhelp = 'Clear Selection', index = 3)
##########################################################################
##########################################################################
#
#  Support for static sets
#
##########################################################################
##########################################################################


sets__ = {} # name: (set,comments)

class MVSaveSetCommand(MVCommand):

    """Save a selection under a user specified name
    \nPackage : Pmv
    \nModule  : selectionCommands
    \nClass   : MVSaveSetCommand
    \nCommand : saveSet
    \nSynopsis:\n
         None <- saveSet(nodes, name, comments='No description', **kw)
    \nRequired Arguments:\n       
         nodes --- TreeNodeSet holding the current selection
         \nname --- name under which the selected set will be saved
    \nOptional Arguments:\n           
         comments --- description of the saved set, default is 'No description'
         addToDashboard --whether to add set name to dashboard historylist, default is do not add
    """

    def onAddCmdToViewer(self):
        from Pmv.moleculeViewer import DeleteAtomsEvent
        self.vf.registerListener(DeleteAtomsEvent,
                                 self.handleDeleteAtomsEvents)

    def handleDeleteAtomsEvents(self, event):
        atoms = event.objects
        for setName, _set in self.vf.sets.items():
            if isinstance(_set[0], Atom):
                newSet = _set - atoms
                if len(newSet):
                    self.vf.sets[setName] = _set - atoms
                else:
                    del self.vf.sets[setName]
                    
    def doit(self, nodes, name, comments=None, addToDashboard=False):
        nodes = self.vf.expandNodes(nodes)
        if nodes.stringRepr:
            nodes.setStringRepr(nodes.extendStringRepr(nodes.stringRepr))        
        if len(nodes)==0:
            return 
        if comments==None:
            comments='No description'
        #sets__[name] = (nodes.__class__( nodes.data), comments)
        nodes.comments = comments
        self.vf.sets.add(name, nodes)
        if addToDashboard:
            n = nodes[0].isBelow(Molecule)
            kstr = n*':' + name
            if  self.vf.commands.has_key('dashboard'):
                self.vf.dashboard.tree.selectorEntry.insert('end', kstr)
        # if vision is started add the set to the Pmv library
        if self.vf.visionAPI:
            fullname = nodes.full_name()
            self.vf.visionAPI.add(nodes, name, kw={
                'set':nodes,
                'selString': fullname,
                'constrkw':{
                # selString gets defined in the node's getDefinitionSourceCode
                    #'set':'masterNet.editor.vf.select(selString)',
                    'set':'masterNet.editor.vf.sets["%s"]'%(name),
                    'selString': 'selString',
                    }
                }
                                  )
        return name


    def __call__(self, nodes, name, comments='No description', **kw):
        """ None <- saveSet(nodes, name, comments='No description', **kw)
            \nnodes --- TreeNodeSet holding the current selection
            \nname --- name under which the selected set will be saved
            \ncomments --- description of the saved set, default is 'No description'
        """
        #if name in sets__.keys():
        if name in self.vf.sets.keys():
            newname = name + '_' + str(len(self.vf.sets.keys()))
            self.vf.warningMsg('set name %s already used\nrenaming it %s' % (
                name, newname ) )
            name = newname

        kw['comments'] = comments
        if type(nodes) is types.StringType:
            self.nodeLogString = "'" + nodes +"'"
            nodes = self.vf.expandNodes(nodes)
        return apply( self.doitWrapper, (nodes, name), kw )
        
    def buildFormDescr(self, formName):
        if formName=='saveSet':
            idf = InputFormDescr(title = 'Set Name')
            idf.append( { 'name': 'setname', 
                          'widgetType':Tkinter.Entry,'required':1,
                          'wcfg':{'label':'Set Name'}} )
            idf.append( {'name': 'comments',
                         'widgetType':Tkinter.Entry,
                         'defaultValue':'No description',
                         'wcfg':{'label':'Comments'}} )
            self.idf = idf
            return idf

    def guiCallback(self):
        if len(self.vf.selection)==0:
            self.warningMsg("No selection to be saved as a set")
            return

##         # create the form descriptor
##         idf = InputFormDescr(title = 'Set Name')
##         idf.append( { 'name': 'setname', 
##                       'widgetType':Tkinter.Entry,'required':1,
##                       'wcfg':{'label':'Set Name'}} )
##         idf.append( {'name': 'comments',
##                      'widgetType':Tkinter.Entry,
##                      'defaultValue':'No description',
##                      'wcfg':{'label':'Comments'}} )
## ##          idf.append( { 'name': 'setname', 'label':'Set Name',
## ##                        'widgetType':Tkinter.Entry,'required':1} )
## ##          idf.append( {'name': 'comments', 'label':'Comments',
## ##                       'widgetType':Tkinter.Entry,'defaultValue':'No description'} )
##         val = self.vf.getUserInput(idf)
        val = self.showForm('saveSet')
        if val:
            while len(val)==0 or val['setname'] in self.vf.sets.keys():
                t = 'set name %s already used' % val['setname']
                d = SimpleDialog(self.vf.GUI.ROOT, text=t,
                                 buttons=["Continue"],
                                 default=0, title="ERROR")
                ok=d.go()
                val = self.vf.getUserInput(self.idf)
            name = val['setname']
            del val['setname']
            return apply( self.doitWrapper, (self.vf.getSelection()[:], name,), val )

mvSaveSetCommandGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                            'menuButtonName':'Select',
                            'menuEntryLabel':'Store Selection'}

MVSaveSetCommandGUI = CommandGUI()
MVSaveSetCommandGUI.addMenuCommand('menuRoot', 'Select',
                                   'Store Selection')


class MVCreateSetIfNeeded(MVCommand):

    """create a set, but only if it does not already exist
    \nPackage : Pmv
    \nModule  : selectionCommands
    \nClass   : MVCreateSetIfNeeded
    \nCommand : createSetIfNeeded
    \nSynopsis:\n       
         None <- createSetIfNeeded(nodes, name, comments='No description',**kw)
    \nRequired Arguments:\n        
        nodes --- TreeNodeSet holding the current selection
        \nname --- name under which the selected set will be saved
    \nOptional Argumnets:\n    
        comments --- description of the saved set, default is 'No description'
    """

    def doit(self, nodes, name, comments=None):
        
        #nodes = self.vf.expandNodes(nodes)
        if len(nodes)==0: return
        if comments==None:
            comments='No description'
        #sets__[name] = (nodes.__class__( nodes.data), comments)
        #sets__[name] = (nodes, comments)
        nodes.comments = comments
        self.vf.sets.add(name, nodes) 
        if self.vf.visionAPI:
            fullname = nodes.full_name()
            self.vf.visionAPI.add(nodes, name, kw={
                'set':nodes,
                'selString': fullname,
                'name': name,
                'constrkw':{
                    'set':'masterNet.editor.vf.select("%s")'%fullname,
                    'selString': fullname,
                    'name':name}
                }
                                  )
        return self.vf.sets[name]


    def __call__(self, nodes, name, comments='No description', **kw):
        """ None <- createSetIfNeeded(nodes, name, comments='No description',**kw)
        \nnodes --- TreeNodeSet holding the current selection
        \nname --- name under which the selected set will be saved
        \ncomments --- description of the saved set, default is 'No description'
        """
        if name in self.vf.sets.keys():
            return

        kw['comments'] = comments
        nodes = self.vf.expandNodes(nodes)
        if type(nodes) is types.StringType:
            self.nodeLogString = "'" + nodes +"'"
        apply( self.doitWrapper, (nodes, name), kw )
        
# we do not expose this command in the menu bar

class MVSelectSetCommand(MVCommand):
    """This Command is used to select the saved set.
    \nPackage : Pmv
    \nModule  : selectionCommands
    \nClass   : MVSelectSetCommand
    \nCommand : selectSet
    \nSynopsis:\n
    None <- selectSet(setNames, only=False, negate=False)
    \nRequired Arguments:\n
        setNameStr---name
    \nOptional Argumnets:\n
        only=negate=0:selected set is added to the selection
        \nonly=0,negate=1: selected set is removed from the selection
        \nonly=1,negate=0: selected set is the only thing selected"""

    def onRemoveObjectFromViewer(self, mol):
        if not self.vf.sets.keys(): return
        for k in self.vf.sets.keys():
            nodes = self.vf.sets[k]
            if mol in nodes.top.uniq():
                if len(nodes.top.uniq())==1:
                    del self.vf.sets[k]
                else:
                    molNodes = nodes.get(lambda x, mol=mol: x.top==mol)
                    newSet = nodes - molNodes
                    newComments = self.vf.sets[k].comments + ' the elements of this set belonging to %s have been deleted with the molecule'%mol.name
                    del self.vf.sets[k]
                    newSet.comments = newComments
                    self.vf.sets.add(k, newSet)
                    del molNodes
        del nodes


    def setupUndoBefore(self, name, negate=False, only=False):
        # we overwrite setupUndoBefore enven though this command implements
        # the negate kw because the only kw would not be handled properly
        
        # create command to select the current selection
        # WARNING we cannot use getSelection here since it would
        # return everything is nothing is selected
        select = self.vf.select
        if len(self.vf.selection)==0:
            self.addUndoCall( (), {}, self.vf.clearSelection.name )
        else:
            self.addUndoCall( (self.vf.selection,), {},select.name )


    def doit(self, setNames, negate=False, only=False ):
        """None <- selectSet(setNames, only=False, negate=False)
        \nsetNames can be a string or a list of strings
        \nonly=negate=0:selected set is added to the selection
        \nonly=0, negate=1: selected set is removed from the selection
        \nonly=1, negate=0: selected set is the only thing selected"""

        if type(setNames)==types.StringType:
            names = [setNames]
        else:
            try:
                l = len(setNames)
            except:
                self.vf.warningMsg('Bad argument for set setNamess')
                return
            names = setNames
            
        if only:
            self.vf.clearSelection(topCommand=0)
        
        nodes = []
        set_names = self.vf.sets.keys()
        for name in names:
            if name not in set_names:
                msgStr='\''+name+'\'' + ' not a previously defined set!'
                self.vf.warningMsg(msgStr)
            else:
                #what if nodes and specified sets are not the same level?
                nodes = nodes + self.vf.sets[name]
            #try:
            #    nodes = nodes + sets__[name][0]
            #except KeyError:
            #    msgStr='\''+name+'\'' + ' not a previously defined set!'
            #    self.vf.warningMsg(msgStr)
        #if called with non-existent set, don't try to select it
        if nodes:
            self.vf.select( nodes, negate=negate, topCommand=0 )


    def guiCallback(self):
        idf = InputFormDescr(title ='')
        entries = []
        #names = sets__.keys()
        names = self.vf.sets.keys()
        names.sort()
        #for n in names:
        for key, value in self.vf.sets.items():
            entries.append( (key, value.comments) )
            #entries.append( (n, sets__[n][1]) )

        idf.append({'name':'set',
                    'widgetType':ListChooser,
                    'wcfg':{'mode':'extended',
                            'entries': entries,
                            'title':'Choose an item: '}})
        idf.append({'name': 'only', 'widgetType':Tkinter.Checkbutton,
                    'wcfg':{'text': 'Select this set only',
                            'variable': Tkinter.IntVar()},
                    'gridcfg':{'sticky': Tkinter.W}})
        idf.append({'name': 'negate', 'widgetType':Tkinter.Checkbutton,
                    'wcfg':{'text': 'Deselect this set',
                            'variable': Tkinter.IntVar()},
                    'gridcfg':{'sticky': Tkinter.W}})
        vals = self.vf.getUserInput(idf)
        self.ipf = idf
        if len(vals)>0 and len(vals['set'])> 0:
            setNames = vals['set']
            del vals['set']
            apply( self.doitWrapper, (setNames,), vals )


    def __call__(self, setNames, negate=False, only=False, **kw):
        """None <- selectSet(setNames, only=0, negate=0)
        \nsetNames can be a string or a list of strings
        \nonly=negate=0:selected set is added to the selection
        \nonly=0, negate=1: selected set is removed from the selection
        \nonly=1, negate=0: selected set is the only thing selected"""
        kw['negate'] = negate
        kw['only'] = only
        apply( self.doitWrapper, (setNames,), kw )

mvSelectSetCommandGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                              'menuButtonName':'Select',
                              'menuEntryLabel':'Select Set'}

MVSelectSetCommandGUI = CommandGUI()
MVSelectSetCommandGUI.addMenuCommand('menuRoot', 'Select', 'Select Set',
                                     separatorBelow=1 )

##########################################################################
##########################################################################
#
#  Support for other selection 
#
##########################################################################
##########################################################################


class MVSelectFromStringCommand(MVCommand):
    """ molStr,chainStr,residueStr,atomStr Select items by typed-in strings: one for each level. No entry corresponds to select everything at this level. Strings are parsed as would-be regular expressions, replacing * by .*.... 
    \nPackage : Pmv
    \nModule  : selectionCommands
    \nClass   : MVSelectFromStringCommand
    \nCommand : selectFromString
    \nSynopsis:\n
        None <- selectFromString(mols='', chains='', res='', atoms='', deselect=False, silent=False, **kw)
    \nArguments:\n
    mols, chains, res and atoms are strings. *?-, are supported
    \nsilent --- when true, do not warn user about errors
    \nnegate --- when True, the command does a deselect operation
    """

    def __init__(self):
        self.form = None
        MVCommand.__init__(self)


    def onAddCmdToViewer(self):
        if self.vf.hasGui:
            self.selPick = Tkinter.IntVar()
            self.showSelSpheres = Tkinter.IntVar()
        self.molCts={}
        self.chainCts={}


    def setupUndoBefore(self, *args, **kw):
        select = self.vf.select
        oldselection = self.vf.selection
        self.addUndoCall( (), {}, self.vf.clearSelection.name )
        if len(oldselection):
            self.addUndoCall( (oldselection,), {}, select.name )


    def doit(self, mols='', chains='', res='', atoms='', negate=False,
             silent=False, xor=False, intersect=False, nodes=None ):

        if not len(nodes):
            self.vf.warningMsg("no molecules in viewer")
            return 'ERROR'

        userpref = self.vf.userpref['String Matching Mode']['value']
        caseSensitive = True
        escapeCharacters=True
        if 'caseInsens' in userpref:
            caseSensitive = False
        if 'WithEscapedChars' in userpref:
            escapeCharacters=True
        #if userpref == 'caseInsensWithEscapedChars': 
        #    newitem = 'cIWEC'
        #elif userpref == 'caseInsensitive': 
        #    newitem = 'cI'
        #else: newitem = 'cS'

        selectionList = [mols, chains, res, atoms]
        #need to format this correctly
        if atoms!='':
            selectionString = string.join(selectionList, ':')
        elif res!='':
            selectionString = string.join(selectionList[:-1], ':')
        elif chains!='':
            selectionString = string.join(selectionList[:-2], ':')
        else:
            selectionString = mols
        selitem, selMsg = StringSelector().select(nodes.top.uniq(),
                            selectionString, self.vf.sets, caseSensitive,
                            escapeCharacters)

        if not selitem:
            if silent is False:
                msg = 'No new selection:\n'+ selMsg
                if self.form:
                    self.vf.warningMsg(msg, parent=self.form.root)
                else:
                    self.vf.warningMsg(msg)
            return 'ERROR'

        if len(selMsg) and self.form is not None:
            self.vf.warningMsg(selMsg, parent=self.form.root)

        if selitem and len(selitem) > 0:
            lev = selitem[0].__class__
            if lev == Protein: lev = Molecule
            if self.vf.selectionLevel != lev:
                self.vf.setSelectionLevel(selitem[0].__class__, busyIdle=0, log=0, setupUndo=0)
            #    if not silent:
            #        t = "Current selection level is %s\nThis set holds %s objects. Do \
    #you want to set the selection level to %s ?" % (self.vf.selectionLevel,
    #     lev, lev)
    #                d = SimpleDialog(self.vf.GUI.ROOT, text=t,
    #                                 buttons=["Yes","No"],
    #                                 default=0, title="change selection level")
    #                ok=d.go()
    #                if ok==0: #answer was yes
    #                    self.vf.setSelectionLevel(selitem[0].__class__, busyIdle=0, log=0)
    #                    #self.vf.setIcomLevel( selitem[0].__class__, log = 0,
    #                           #KlassSet = selitem[0].setClass , topCommand=0)
    #                else:
    #                    return 'ERROR' # prevent logging
    #            else:
    #                self.vf.setSelectionLevel(selitem[0].__class__, busyIdle=0, log=0)
                
            self.vf.select( selitem , negate=negate, xor=xor,
                            intersect=intersect, topCommand=0)
            #if not negate:
            #    self.vf.select( selitem , negate=negate, topCommand=0)
            #else:
            #    #can't just deselect because SFString inherits from select
            #    old = self.vf.getSelection()[:]
            #    if len(old)==0: return
            #    else:
            #        self.vf.clearSelection(topCommand=0)
            #        if len(selitem)!=len(old): 
            #            self.vf.select(old-selitem, topCommand=0)
        if self.form: self.form.lift()
        return self.vf.getSelection()


    def __call__(self, mols='', chains='', res='', atoms='', negate=False,
                 silent=True, xor=False, intersect=False, nodes=None, **kw):
        """None <- selectFromString(nodes, mols='', chains='', res='', atoms='', deselect=False, silent=False, **kw)
    \nmols, chains, res and atoms are strings. *?-, are supported
    \nsilent: when true, do not warn user about errors
    \nnegate: when True, the command does a deselect operation
    \nnodes : nodes that will expand to molecules to be used to select from
        """
        #print "in selectFromString.__call__ with xor=", xor
        kw['mols'] = mols
        kw['chains'] = chains
        kw['res'] = res
        kw['atoms'] = atoms
        kw['negate'] = negate
        kw['silent'] = silent
        kw['xor'] = xor
        kw['intersect'] = intersect
        kw['log'] = False
        if nodes is None:
            nodes = self.vf.Mols
        elif isinstance(nodes, TreeNode):
            nodes = nodes.setClass([nodes])
        kw['nodes'] = nodes
        return apply( self.doitWrapper, (), kw )


    def buildForm(self, event=None):
        self.selPick.set(0)
        ifd = self.ifd = InputFormDescr(title = 'Select From String')
        ifd.append({'widgetType':Tkinter.Label,
                    'wcfg':{'text': 'Molecule'}, 
                    'gridcfg':{'sticky':'w'} })
        ifd.append({'name':'molWid',
                    'widgetType':Tkinter.Entry,
                    'wcfg':{'highlightcolor':'white'}, 
                    'gridcfg':{'sticky':'ew','row':-1, 'column':1, 'columnspan':3} })
                    #'gridcfg':{'sticky':Tkinter.E,'columnspan':4} })
        ifd.append({'widgetType':Tkinter.Label,
                    'wcfg':{'text': 'Chain'}, 
                    'gridcfg':{'sticky':'w'} })
        ifd.append({'name': 'chainWid',
                    'widgetType':Tkinter.Entry,
                    'wcfg':{'highlightcolor':'white'}, 
                    'gridcfg':{'sticky':'ew','row':-1, 'column':1, 'columnspan':3} })
        #ifd.append({'widgetType':Tkinter.Entry,
        #            'wcfg':{'label': 'Chain'}, 
        #            'gridcfg':{'sticky':'ew','columnspan':4} })
        #            #'gridcfg':{'sticky':Tkinter.E, 'columnspan':4} })
        ifd.append({'widgetType':Tkinter.Label,
                    'wcfg':{'text': 'Residue'}, 
                    'gridcfg':{'sticky':'w'} })
        ifd.append({'name':'resWid',
                    'widgetType':Tkinter.Entry,
                    'wcfg':{'highlightcolor':'white'}, 
                    'gridcfg':{'sticky':'ew','row':-1, 'column':1, 'columnspan':3} })
        #ifd.append({'widgetType':Tkinter.Entry,
        #            'wcfg':{'label': 'Residue'}, 
        #            'gridcfg':{'sticky':'ew','columnspan':4} })
        #            #'gridcfg':{'sticky':Tkinter.E, 'columnspan':4} })
        ifd.append({'widgetType':Tkinter.Label,
                    'wcfg':{'text': 'Atom'}, 
                    'gridcfg':{'sticky':'w'} })
        ifd.append({'name':'atomWid',
                    'widgetType':Tkinter.Entry,
                    'wcfg':{'highlightcolor':'white'}, 
                    'gridcfg':{'sticky':'ew','row':-1, 'column':1, 'columnspan':3} })
        #ifd.append({'widgetType':Tkinter.Entry,
        #            'wcfg':{'label': 'Atom'}, 
        #            'gridcfg':{'sticky':'ew','columnspan':4} })
        #            #'gridcfg':{'sticky':Tkinter.E,'columnspan':4} })
        ifd.append({'name': 'Mol List',
                    'widgetType':Tkinter.Menubutton,
                    'wcfg':{ 'text': 'Molecule List ...'},
                    'gridcfg':{'sticky':Tkinter.W,'row':-4,'column':4,
                               'columnspan':2} })
        ifd.append({'name': 'Chain List',
                    'widgetType':Tkinter.Menubutton,
                    'wcfg':{'text': 'Chain List ...'},
                    'gridcfg':{'sticky':Tkinter.W, 'column':4,'row':-3,
                               'columnspan':2} })
        ifd.append({'name': 'Residue Sets',
                    'widgetType':Tkinter.Menubutton,
                    'wcfg':{'text': 'Residue Sets...'},
                    'gridcfg':{'sticky':Tkinter.W, 'column':4,'row':2,
                               'columnspan':2} })
        ifd.append({'name': 'Atom Sets',
            'widgetType':Tkinter.Menubutton,
            'text': 'Atom Sets...',
            'gridcfg':{'sticky':Tkinter.W, 'column':4,'row':3,
                 'columnspan':2} })
        #ifd.append({'name': 'Sets List',
        #            'widgetType':Tkinter.Menubutton,
        #            'wcfg':{'text': 'Sets List ...'},
        #            'gridcfg':{'sticky':Tkinter.W, 'column':4,
        #                       'row':3,'columnspan':2} })
        ifd.append({'name': 'addBut',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'bd':3, 'text': 'Add',
                            'command': self.add},
                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W,'row':4,
                               'column':0, 'columnspan':1},
                    })
        ifd.append({'name': 'removeBut',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'bd':3, 'text': 'Remove',
                            'command': self.remove},
                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W,'row':4,
                               'column':1, 'row':-1, 'columnspan':2},
                    })
        ifd.append({'name': 'xorBut',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'bd':3, 'text': 'Xor',
                            'command': self.xor},
                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W,'row':4,
                               'column':3,'row':-1, 'columnspan':1},
                    })
        ifd.append({'name': 'intersectBut',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'bd':3, 'text': 'Intersect',
                            'command': self.intersect},
                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W,'row':4,
                               'column':4, 'row':-1, 'columnspan':2},
                    })
                               

#        ifd.append({'name': 'Select',
#                    'widgetType':Tkinter.Button,
#                    'wcfg':{'bd':6, 'text': 'Select',
#                            'command': self.callDoit},
#                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W,'row':4,
#                               'column':0, 'columnspan':4},
#                    })
#        ifd.append({'name': 'Deselect',
#                    'widgetType':Tkinter.Button,
#                    'wcfg':{'text': 'Deselect','bd':6,
#                            'command': self.callDontDoit},
#                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W,
#                               'row':4,'column':4,
#                               'columnspan':2},
#                    })
        ifd.append({'name': 'Clear Selection',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text': 'Clear Selection',
                            'borderwidth':1, 'command': self.clearSel},
                    'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                               'columnspan':2},
                    })
        ifd.append({'name': 'invertBut',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text': 'Invert Selection',
                            'borderwidth':1, 'command': self.invert},
                    'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                               'row':-1, 'column':2, 'columnspan':2},
                    })
        ifd.append({'name': 'Save Selection',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text': 'Store Selection',
                            'borderwidth':1, 'command': self.saveSel},
                    'gridcfg':{'sticky':Tkinter.W+Tkinter.E,'row':-1, 
                               'column':4,'columnspan':2},
                    })
        ifd.append({'name': 'Clear Form',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text': 'Clear Form',
                            'borderwidth':1,
                            'command': self.clearForm},
                    'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                               'column':0, 'columnspan':2},
                    })


        ifd.append({'name': 'Select with',
                    'widgetType':Pmw.OptionMenu,
                    'defaultValue':self.vf.userpref['Selection Object']['value'],
                    'wcfg':{'label_text': 'Select Using: ',
                            'labelpos':'w',
                             'items': ["none", "crosses", "spheres"],
                             'command':self.changeSelectionObject,
                             },
                    'gridcfg':{'sticky':Tkinter.W,'row':-1,'column':3, 'columnspan':2},
                    })
        ifd.append({'widgetType':Tkinter.Button,
                    'wcfg':{'bd':4, 'text':'Dismiss',
                            'command': self.Dismiss_cb},
                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W,
                               'columnspan':6}})
        self.form = self.vf.getUserInput(self.ifd, modal = 0, blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW',self.Dismiss_cb)
        eD = self.ifd.entryByName
        eD['Mol List']['widget'].bind('<ButtonPress>',self.buildMolMenus,add='+')
        eD['Chain List']['widget'].bind('<ButtonPress>',self.buildChainMenus,add='+')
        eD['Residue Sets']['widget'].bind('<ButtonPress>',self.buildResMenus,add='+')
        eD['Atom Sets']['widget'].bind('<ButtonPress>',self.buildAtomMenus,add='+')
        #self.cb = self.ifd.entryByName['Show SelSpheres']['widget']
        #self.ifd.entryByName['Atom Sets']['widget'].bind('<ButtonPress>', self.buildAtomMenus,add='+')
        #eD['Sets List']['widget'].bind('<ButtonPress>',self.buildSetsMenus,add='+')
        self.xorBut = self.ifd.entryByName['xorBut']['widget']
        self.invertBut = self.ifd.entryByName['invertBut']['widget']
        self.intersectBut = self.ifd.entryByName['intersectBut']['widget']
        self.removeBut = self.ifd.entryByName['removeBut']['widget']
        self.addBut = self.ifd.entryByName['addBut']['widget']
        if not hasattr(self,'setsVar'): self.setsVar={}
        if not hasattr(self,'oldsetsVar'): self.oldsetsVar={}
        for button in [self.xorBut, self.intersectBut, self.removeBut]:
            if len(self.vf.selection)==0:
                button.config(state='disabled')

    def setButtonState(self, event=None):
        for button in [self.xorBut, self.intersectBut, self.removeBut]:
            if len(self.vf.selection)==0:
                button.config(state='disabled')
            else:
                button.config(state='active')


    def guiCallback(self):
        if not hasattr(self, 'ifd'):
            self.buildForm()
        else:
            self.form.deiconify()
            self.form.lift()
        if self.vf.userpref['Selection Object']['value'] == 'none':
            self.showSelSpheres.set(0)
        else:
            self.showSelSpheres.set(1)


    def increaseCts(self,dict, newStr):
        if dict.has_key(newStr):
            dict[newStr]=dict[newStr]+1
        else:
            dict[newStr]=1


    def decreaseCts(self,dict,newStr):
        #print "decreaseCts dict=", dict
        #print "newStr=", newStr
        #print "dict.has_key(", newStr,")=", dict.has_key(newStr)
        if dict.has_key(newStr):
            currentVal=dict[newStr]
            #print "currentVal =", currentVal
            if currentVal<=1: currentVal=1
            dict[newStr]=currentVal-1
            #print "finally: dict[", newStr,"]=", dict[newStr]


    def getMolVal(self, event=None):
        molWidget=self.ifd.entryByName['molWid']['widget']
        #molWidget=self.ifd[0]['widget']
        for molStr in self.molVar.keys():
            #figure out which check button was just changed
            newVal=self.molVar[molStr].get()
            if newVal==self.oldmolVar[molStr]: continue
            else:
                self.oldmolVar[molStr]=newVal
            molList=string.split(molWidget.get(),',')
            if newVal==1:
                self.increaseCts(self.molCts,molStr)
                if not molStr in molList:
                    if molWidget.index('end')==0:
                        molWidget.insert('end',molStr) 
                    else: 
                        molWidget.insert('end',','+molStr) 
            else:
                if molStr in molList:
                    self.molCts[molStr]=0
                    molList.remove(molStr)
                    molWidget.delete(0,'end')
                    molWidget.insert('end',string.join(molList,','))
                    #also turn off all of the chain checkbuttons:
                    #chainWidget=self.ifd[1]['widget']
                    chainWidget=self.ifd.entryByName['chainWid']['widget']
                    chainList=string.split(chainWidget.get(),',')
                    # chain menu may not have been built yet:
                    if not hasattr(self, 'chainVar'):
                        self.buildChainMenus()
                    for ch in self.chainVar.keys():
                        if ch in ['dna', 'proteic']: continue
                        chKeyList = string.split(ch,':')
                        thisMolStr=chKeyList[0]
                        thisChainStr=chKeyList[1]
                        #if the chain is in this molecule
                        if thisMolStr==molStr:
                            #turn off chain checkbutton
                            self.chainVar[ch].set(0)
                            self.oldchainVar[ch]=0
                            self.decreaseCts(self.chainCts,thisChainStr)
                            if len(chKeyList)>1 and thisChainStr in chainList:
                                chainList.remove(thisChainStr)
                    chainWidget.delete(0,'end')   
                    chainWidget.insert('end',string.join(chainList,','))


    def getChainVal(self, event=None):
        chains = self.vf.Mols.findType(Chain)
        molWidget=self.ifd.entryByName['molWid']['widget']
        #molWidget= self.ifd[0]['widget']
        chainWidget=self.ifd.entryByName['chainWid']['widget']
        #chainWidget= self.ifd[1]['widget']
        for item in self.chainVar.keys():
            if item in ['proteic', 'dna']:
                newVal = self.chainVar[item].get()
                if newVal==self.oldchainVar[item]:
                    continue
                if newVal==1:
                    #add item to entry
                    if chainWidget.index('end')==0:
                        chainWidget.insert('end',item)
                    else:
                        chainWidget.insert('end',','+item)
                    self.oldchainVar[item]=1
                else:
                    #remove item from entry
                    chainList=string.split(chainWidget.get(),',')
                    if item in chainList: 
                        chainList.remove(item)
                    chainWidget.delete(0,'end')
                    chainWidget.insert('end',string.join(chainList,','))
                    self.oldchainVar[item]=0
            else:
                #process standard item
                molStr,chainStr = string.split(item,':')
                newVal=self.chainVar[item].get()

                if newVal ==self.oldchainVar[item]:
                    continue
                else:
                    self.oldchainVar[item]=newVal
                    molList=string.split(molWidget.get(),',')
                    chainList=string.split(chainWidget.get(),',')
                if newVal==1:
                    self.increaseCts(self.molCts,molStr)
                    self.increaseCts(self.chainCts,chainStr)
                    if not molStr in molList:
                        if molWidget.index('end')==0:
                            molWidget.insert('end',molStr)
                        else:
                            molWidget.insert('end',','+molStr)
                    if  not chainStr in chainList:
                        if chainWidget.index('end')==0:
                            chainWidget.insert('end',chainStr)
                        else:
                            chainWidget.insert('end',','+chainStr)
                    if hasattr(self, 'molVar') and self.molVar.has_key(molStr):
                        self.molVar[molStr].set(1)
                    else: 
                        self.buildMolMenus()
                        self.molVar[molStr].set(1)
                    self.oldmolVar[molStr]=1
                else:
                    if not self.molCts.has_key(molStr): continue
                    if not self.chainCts.has_key(chainStr): continue
                    self.decreaseCts(self.molCts,molStr)
                    self.decreaseCts(self.chainCts,chainStr)
                    chainList=string.split(chainWidget.get(),',')
                    if chainStr in chainList: 
                        if chainStr in chainList and self.chainCts[chainStr]==0:
                            chainList.remove(chainStr)
                        if self.molCts[molStr]==0:
                            if hasattr(self, 'molVar') and self.molVar.has_key(molStr):
                                self.molVar[molStr].set(0)
                                self.oldmolVar[molStr]=0
                            #also remove it from Molecule entry
                            molList=string.split(molWidget.get(),',')
                            if molStr in molList:molList.remove(molStr)
                            newss1=string.join(molList,',')
                            molWidget.delete(0,'end')
                            molWidget.insert('end',newss1)
                        ##also have to fix the Chain entry:
                        chainWidget.delete(0,'end')
                        chainWidget.insert('end',string.join(chainList,','))


    def getResSetsVal(self, event=None):
        w=self.ifd.entryByName['resWid']['widget']
        #w=self.ifd[2]['widget']
        ssList=string.split(w.get(),',')
        for newStr in self.ResSetsVar.keys():
            if self.ResSetsVar[newStr].get()==1:
                if newStr not in ssList:
                    if w.index('end')==0:
                        w.insert('end',newStr) 
                    else:
                        w.insert('end',',') 
                        w.insert('end',newStr) 
            #method to remove here
            else: 
                if newStr in ssList: 
                    ssList.remove(newStr)
                    w.delete(0,'end')
                    w.insert(0,string.join(ssList,','))


    def getAtomSetsVal(self, event=None):
        w=self.ifd.entryByName['atomWid']['widget']
        #w=self.ifd[3]['widget']
        ssList=string.split(w.get(),',')
        for newStr in self.AtomSetsVar.keys():
            if self.AtomSetsVar[newStr].get()==1:
                if newStr not in ssList:
                    if w.index('end')==0:
                        w.insert('end',newStr) 
                    else:
                        w.insert('end',',') 
                        w.insert('end',newStr) 
            #method to remove here
            else: 
                if newStr in ssList: 
                    ssList.remove(newStr)
                    w.delete(0,'end')
                    w.insert(0,string.join(ssList,','))

        for i in self.setsVar.keys():
            if i not in specialCases:
                newSet = self.vf.sets[i]
                #newSet = sets__[i][0]
                newNode0 = newSet[0]
                #w/ newclass Set: level here
                lev = newNode0.__class__
                if lev == Protein: lev = Molecule
                self.vf.setSelectionLevel(lev, busyIdle=0, log=0, setupUndo=0)
                #self.vf.setIcomLevel(lev, busyIdle=0, log=0)
            newVal = self.setsVar[i].get()


    def getSetsVal(self, event=None):
        #process 'backbone', backbone+H and sidechain separately
        #these 4 are hard-wired atom sets
        specialCases = ['backbone', 'backbone+H' , 'sidechain', 'hetatm']
        sets = self.vf.sets.keys()
        #sets = sets__.keys()
        for newStr in self.setsVar.keys():
            if newStr not in specialCases:
                node0 = self.vf.sets[newStr][0]
                #node0 = sets__[newStr][0][0]
                #this would work only w/ 4 levels(/)
                nodeLevel = node0.isBelow(Protein)
                w=self.ifd[nodeLevel]['widget']
                ssList=string.split(w.get(),',')
            else:
                #hardwired to Atom level widget
                w=self.ifd.entryByName['atomWid']['widget']
                #w=self.ifd[3]['widget']
                ssList=string.split(w.get(),',')

            if self.setsVar[newStr].get()==1:
                if newStr==' ': continue
                if not newStr in ssList:
                    if w.index('end')==0:
                        w.insert('end',newStr) 
                    else:
                        w.insert('end',',') 
                        w.insert('end',newStr) 
            else: 
                if newStr in ssList:
                    ssList.remove(newStr)
                    w.delete(0,'end')
                    w.insert(0,string.join(ssList,','))


    def buildMenu(self, mB, nameList, varDict, oldvarDict, cmd):
        if nameList:
            #prune non-valid entries
            for i in varDict.keys():
                #print i, " in nameList is ", i in nameList
                if i not in nameList:
                    del varDict[i]
                    del oldvarDict[i]
            #add anything new
            for i in nameList:
                if i not in varDict.keys():
                    varDict[i]=Tkinter.IntVar()
                    oldvarDict[i]=0
        else:
            varDict={}
            oldvarDict={}
        #start from scratch and build menu
        #4/24: only build and add 1 menu
        if hasattr(mB, 'menu'):
            mB.menu.delete(1,'end')
        else:
            mB.menu = Tkinter.Menu(mB)
            mB['menu']=mB.menu
        #PACK all the entries
        for i in varDict.keys():
            mB.menu.add_checkbutton(label=i, var=varDict[i], command=cmd)


    def buildMolMenus(self,event=None):
        molMenubutton = self.ifd.entryByName['Mol List']['widget']
        if not hasattr(self,'molVar'): self.molVar={}
        if not hasattr(self,'oldmolVar'): self.oldmolVar={}
        molNames = self.vf.Mols.name
        for key in self.vf.sets.get(stype=MoleculeSet):
            molNames.append( key )
        self.buildMenu(molMenubutton,molNames,self.molVar,self.oldmolVar,self.getMolVal)


    def buildChainMenus(self,event=None):
        #selectFromString
        chainMenubutton = self.ifd.entryByName['Chain List']['widget']
        if not hasattr(self,'chainVar'): self.chainVar={}
        if not hasattr(self,'oldchainVar'): self.oldchainVar={}
        chMols=MoleculeSet(filter(lambda x: Chain in x.levels, self.vf.Mols))
        chainIDList = []
        if len(chMols):
            chains=chMols.findType(Chain)
            if chains==None: return
            for i in chains:
                chainIDList.append(i.full_name())
        for key in self.vf.sets.get(stype=ChainSet):
            chainIDList.append( key )
        chainIDList.append('dna')
        chainIDList.append('proteic')
        self.buildMenu(chainMenubutton,chainIDList,self.chainVar,self.oldchainVar,self.getChainVal)


    def buildResMenus(self,event=None):
        ResSetsMenubutton = self.ifd.entryByName['Residue Sets']['widget']
        if not hasattr(self,'ResSetsVar'): self.ResSetsVar={}
        if not hasattr(self,'oldResSetsVar'): self.oldResSetsVar={}
        resSelector = ResidueSetSelector()
        ResSetsList = resSelector.residueList.keys()
        for key in self.vf.sets.get(stype=ResidueSet):
            ResSetsList.append( key )
        self.buildMenu(ResSetsMenubutton,ResSetsList,self.ResSetsVar,self.oldResSetsVar,self.getResSetsVal)


    def buildAtomMenus(self,event=None):
        AtomSetsMenubutton = self.ifd.entryByName['Atom Sets']['widget']
        if not hasattr(self,'AtomSetsVar'): self.AtomSetsVar={}
        if not hasattr(self,'oldAtomSetsVar'): self.oldAtomSetsVar={}
        self.atomList = AtomSetSelector().atomList
        AtomSetsList = self.atomList.keys()
        for key in self.vf.sets.get(stype=AtomSet):
            AtomSetsList.append( key )
        self.buildMenu(AtomSetsMenubutton,AtomSetsList,self.AtomSetsVar,self.oldAtomSetsVar,self.getAtomSetsVal)


    def buildSetsMenus(self,event=None):
        setsMenubutton = self.ifd.entryByName['Sets List']['widget']
        if not hasattr(self,'setsVar'): self.setsVar={}
        if not hasattr(self,'oldsetsVar'): self.oldsetsVar={}
        sets = ['backbone', 'backbone+H', 'sidechain', 'hetatm']
        #for k in sets__.keys():
        for k in self.vf.sets.keys():
            sets.append(k)
        #sets = sets__.keys()  #
        self.buildMenu(setsMenubutton,sets,self.setsVar,self.oldsetsVar,self.getSetsVal)
    

    def Dismiss_cb(self):
        self.vf.GUI.removeCameraCallback("<ButtonRelease-1>",
                                         self.getPickInfo_cb)
        self.form.withdraw()


    def saveSel(self):
        self.vf.saveSet.guiCallback()
        if self.form: self.form.lift()


    def xor(self):
        #print "in xor"
        args = self.buildArgs(xor=True)
        self.callIt(args)
        self.setButtonState()


    def remove(self):
        #print "in remove"
        args = self.buildArgs(negate=True)
        self.callIt(args)
        self.setButtonState()


    def add(self):
        #print "in add"
        args = self.buildArgs()
        self.callIt(args)
        self.setButtonState()


    def intersect(self):
        #print "in intersect"
        args = self.buildArgs(intersect=True)
        self.callIt(args)
        self.setButtonState()


    def invert(self, event=None):
        if len(self.vf.Mols)>1:
            levelNames = ['all','molecule']
            # create the form descriptor
            idf  = InputFormDescr(title = 'Set Level for Invert Selection')
            idf.append({ 'name': 'level', 'widgetType':Tkinter.Radiobutton,
                         'listtext': levelNames,
                         'gridcfg':{'sticky':Tkinter.W}})
            val = self.vf.getUserInput(idf)            
            if len(val)>0: 
                newparam = val['level']
        else:
            newparam='all'
        self.vf.invertSelection(newparam, topCommand = 0, redraw = 1)
        if self.form: self.form.lift()
        self.setButtonState()


    def clearSel(self):
        self.vf.clearSelection()
        if self.form: self.form.lift()
        self.setButtonState()


    def clearForm(self):
        for widName in ['molWid','chainWid', 'resWid', 'atomWid']:
            self.ifd.entryByName[widName]['widget'].delete(0,'end')
        #self.ifd[0]['widget'].delete(0,'end')
        #self.ifd[1]['widget'].delete(0,'end')
        #self.ifd[2]['widget'].delete(0,'end')
        #self.ifd[3]['widget'].delete(0,'end')
        #move cursor back to Molecule entry
        #print 'FOGO1'
        self.ifd.entryByName['molWid']['widget'].focus()
        #self.ifd[0]['widget'].focus()
        ###SHOULD ALL THE VARIABLES BE ZEROED HERE???
        self.molCts={}
        if hasattr(self, 'oldmolVar'):
            for item in self.oldmolVar.keys():
                self.oldmolVar[item]=0
        if hasattr(self, 'oldchainVar'):
            for item in self.oldchainVar.keys():
                self.oldchainVar[item]=0
        if hasattr(self, 'molVar'):
            for item in self.molVar.keys():
                self.molVar[item].set(0)
        if hasattr(self, 'chainVar'):
            for item in self.chainVar.keys():
                self.chainVar[item].set(0)
        if hasattr(self, 'ResSetsVar'):
            for item in self.ResSetsVar.keys():
                self.ResSetsVar[item].set(0)
        if hasattr(self, 'AtomSetsVar'):
            for item in self.AtomSetsVar.keys():
                self.AtomSetsVar[item].set(0) 
        if hasattr(self, 'setsVar'):
            for item in self.setsVar.keys():
                self.setsVar[item].set(0)
        if self.form: self.form.lift()
        self.setButtonState()


    def startSelPick(self):
        from Pmv.picker import AtomPicker
        if self.selPick.get()==1:
            if hasattr(self.vf,'selectButtons'):
                self.vf.selectButtons.radioVar.set('Off')
                self.vf.selectButtons.setSelect()
            self.ap=AtomPicker(self.vf,None,gui=0,callbacks=[self.getPickInfo_cb],immediate=1)
            self.ap.go(modal=0)
        else:
            self.ap.stop()

    def changeSelectionObject(self, object='none'):
        self.vf.userpref.set('Selection Object', object)
         
    def toggleSelSpheres(self, event = None):
        if self.vf.userpref['Selection Object']['value'] != 'none':
            self.prevPref = self.vf.userpref['Selection Object']['value']
            self.vf.userpref.set('Selection Object', 'none')
            self.showSelSpheres.set(0)
        else:
            if hasattr(self, 'prevPref'):
                prevPref = self.prevPref 
            if prevPref  == 'none':
                prevPref = 'spheres'
            self.vf.userpref.set('Selection Object', prevPref)
            self.showSelSpheres.set(1)
        self.vf.select.updateSelectionFeedback()
        self.vf.GUI.VIEWER.Redraw()
        if self.form: self.form.lift()
        
    def getPickInfo_cb(self, atoms):
        if self.vf.selector.level==None: 
            self.setMolLevel()
            self.selLevel.set(1)
        if not atoms: return
        for atom in atoms:
            atomStr = atom.full_name() 
            atomList = string.split(atomStr,':')
            num = self.selLevel.get()
            #if 1 only do Mol, 2 do Chain and Mol etc
            widgetNames = ['molWid','chainWid', 'resWid', 'atomWid']
            #self.ifd.entryByName['molWid']['widget'].focus()
            for i in range(num):
                widName = widgetNames[i]
                w = self.ifd.entryByName[widName]['widget']
                #w=self.ifd[i]['widget']
                newStr=atomList[i]
                if string.find(w.get(),newStr)==-1:
                    if w.index('end')==0:
                        w.insert('end',newStr) 
                    else:
                        w.insert('end',',') 
                        w.insert('end',newStr) 
        self.ap.clear()
        if self.form: self.form.lift()


    def buildArgs(self, negate=False, xor=False, intersect=False):
        args = {}
        d = self.ifd.entryByName
        args['mols'] = d['molWid']['widget'].get()
        args['chains'] = d['chainWid']['widget'].get()
        args['res'] = d['resWid']['widget'].get()
        args['atoms'] = d['atomWid']['widget'].get()
        #if self.ifd[0]['widget'].get()=='':
        #    args['mols'] = ''
        #else:
            #args['mols'] = self.ifd[0]['widget'].get()
        #if self.ifd[1]['widget'].get()=='':
        #    args['chains'] = ''
        #else:
        #    args['chains'] = self.ifd[1]['widget'].get()
        #if self.ifd[2]['widget'].get()=='':
        #    args['res'] = ''
        #else:
        #    args['res'] = self.ifd[2]['widget'].get()
        #if self.ifd[3]['widget'].get()=='':
        #    args['atoms'] = ''
        #else:
        #    args['atoms'] = self.ifd[3]['widget'].get()
        args['negate'] = negate
        args['xor'] = xor
        args['intersect'] = intersect
        return args


    def callDontDoit(self):
        kwargs = self.buildArgs()
        kwargs['negate'] = 1
        kwargs['log']=False
        kw = kwargs.copy()
        kw['silent'] = True
        kwargs['nodes'] = self.vf.Mols
        #lastCmdLog = apply( self.logString, (), kw)
        #self.lastCmdLog.append(lastCmdLog)
        #self.vf.message( lastCmdLog )
        #self.vf.log(lastCmdLog)
        apply(self.doitWrapper, (), kwargs)


    def callDoit(self):
        kwargs = self.buildArgs()
        kwargs['negate'] = 0
        kwargs['log'] = False
        kw = kwargs.copy()
        kw['silent'] = True
        kwargs['nodes'] = self.vf.Mols
        lastCmdLog = apply( self.logString, (), kw)
        #self.lastCmdLog.append(lastCmdLog)
        #self.vf.message( lastCmdLog )
        #self.vf.log(lastCmdLog)
        apply(self.doitWrapper, (), kwargs)


    def callIt(self, args):
        args['log'] = False
        kw = args.copy()
        kw['silent'] = True
        args['nodes'] = self.vf.Mols
        #lastCmdLog = apply( self.logString, (), kw)
        #self.lastCmdLog.append(lastCmdLog)
        #self.vf.message( lastCmdLog )
        #self.vf.log(lastCmdLog)
        apply(self.doitWrapper, (), args)
        


    def updateselLevel(self,lev):
        #NEED TO SET LEVEL IF THERE IS ONE:lev= self.vf.selector.level
        #NB: currently, all items are Protein; THIS IS A PROBLEM
        ll = [Protein,Chain,Residue,Atom]
        lcoms = [self.setMolLevel,self.setChainLevel,self.setResidueLevel,self.setAtomLevel]
        if lev:
            #NB there is a problem w/Protein v Molecule
            if lev == Protein: lev = Molecule
            ind = ll.index(lev)
            self.selLevel.set(ind+1)
            lcoms[ind]()
        else:
            self.selLevel.set(1)
            self.setMolLevel()
        if self.form: self.form.lift()


mvSelectFromStringCommandGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                                     'menuButtonName':'Select',
                                     'menuEntryLabel':'Select From String',
                                     'separatorBelow':1}


MVSelectFromStringCommandGUI = CommandGUI()
MVSelectFromStringCommandGUI.addMenuCommand('menuRoot', 'Select', 'Select From String', separatorBelow=1 )



class MVDirectSelectCommand(MVSelectFromStringCommand):
    """This Command allows you to directly select from moleculelist,chainlist,setslist
    \nPackage : Pmv
    \nModule  : selectionCommands
    \nClass   : MVDirectSelectCommand
    \nCommand : directSelect
    \nSynopsis:\n
        None <- directSelect(nameStr, **kw)
    \nRequired Arguments:\n
        nameStr: name of selection from the string list
    """
    def buildForm(self):
        if hasattr(self, 'ifd'):
            return
        ifd = self.ifd = InputFormDescr(title = 'Direct Select')
        ifd.append({'name': 'Mol List',
                    'widgetType':Tkinter.Menubutton,
                    'wcfg':{'text': 'Molecule List ...'},
                    'gridcfg':{'sticky':Tkinter.W, 'columnspan':2}})
        ifd.append({'name': 'Chain List',
                    'widgetType':Tkinter.Menubutton,
                    'wcfg':{'text': 'Chain List ...'},
                    'gridcfg':{'sticky':Tkinter.W, 'columnspan':2} })
        ifd.append({'name': 'Sets List',
                    'widgetType':Tkinter.Menubutton,
                    'wcfg':{'text': 'Sets List ...'},
                    'gridcfg':{'sticky':Tkinter.W, 'columnspan':2} })
        ifd.append({'name': 'Show SelSpheres',
                    'widgetType':Tkinter.Checkbutton,
                    'wcfg':{'text': 'Highlight Selection',
                            'variable': self.showSelSpheres,
                            'command': self.toggleSelSpheres},
                    'gridcfg':{'sticky':Tkinter.W,'row':3,'column':0},
                    })
        ifd.append({'widgetType':Tkinter.Button,
                    'wcfg':{'bd':6, 'text':'Dismiss',
                            'command': self.Dismiss_cb},
                            'gridcfg':{'sticky':Tkinter.E+Tkinter.W,
                                       'columnspan':6},
                    })
        self.form = self.vf.getUserInput(self.ifd, modal = 0, blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW',self.Dismiss_cb)
        eD = self.ifd.entryByName
        eD['Mol List']['widget'].bind('<ButtonPress>', 
            self.buildMolMenus,add='+')
        eD['Chain List']['widget'].bind('<ButtonPress>', 
            self.buildChainMenus,add='+')
        eD['Sets List']['widget'].bind('<ButtonPress>', 
            self.buildSetsMenus,add='+')



    def guiCallback(self):
        if not hasattr(self, 'ifd'):
            self.buildForm()
        else:
            self.form.deiconify()
        #clear all the buttons here(?)
        sellist = self.vf.selection
        for dictName in ['molVar', 'chainVar', 'setsVar']:
            if hasattr(self, dictName):
                #dict = eval('self.%s' %dictName)
                dict = getattr(self, dictName)
                if len(sellist):
                    selnames = sellist.name
                    for item in dict.keys():
                        dict[item].set(item in selnames)
                else:
                    for item in dict.keys():
                        dict[item].set(0)
            else: continue
        if self.vf.userpref['Selection Object']['value'] == 'none':
            self.showSelSpheres.set(0)
        else:
            self.showSelSpheres.set(1)


    def findItemFromName(self,itemList,someName):
        #should add error detection at end
        for i in itemList:
            if i.name==someName:
                return i


    def findItemFromID(self,itemList,someID):
        #keys are "1hvr:A"
        for i in itemList:
            newStr = i.parent.name+":"+i.id
            if newStr == someID:
                return i


    def doit(self, nameStr):
        chNameList =[] 
        ch = self.vf.Mols.findType(Chain)
        if ch:
            chParents = ch.parent.name
            chIds=ch.id
            for i in range(len(chIds)):
                newItem=chParents[i]+':'+chIds[i]
                chNameList.append(newItem)
        if nameStr in self.vf.Mols.findType(Molecule).name:
            self.vf.setSelectionLevel(Protein, busyIdle=0, log=0, setupUndo=0)
            newMol=self.findItemFromName(self.vf.Mols, nameStr)
            self.vf.select(newMol, topCommand=0)
        elif nameStr in chNameList:
            self.vf.setSelectionLevel(Chain, busyIdle=0, log=0, setupUndo=0)
            chains = self.vf.Mols.findType(Chain)
            newChain=self.findItemFromID(chains, nameStr)
            self.vf.select(newChain, topCommand=0, )
        elif nameStr in self.vf.sets.keys():
            newSet = self.vf.sets[nameStr]
            newNode0 = newSet[0]
            lev=newNode0.__class__
            self.vf.setSelectionLevel(lev, busyIdle=0, log=0, setupUndo=0)
            self.vf.select(newSet, topCommand=0)
        else:
            msg=nameStr + " not a Molecule, Chain or Set name"
            self.vf.warningMsg(msg)


    def __call__(self, nameStr, **kw):
        """None <- directSelect(nameStr, **kw)
        \nnameStr --- name of selection from the string list"""
        
        apply( self.doitWrapper, (nameStr,), kw )
        


    def buildMolMenus(self,event=None):
        molMenubutton = self.ifd.entryByName['Mol List']['widget']
        if not hasattr(self,'molVar'): self.molVar={}
        if not hasattr(self,'oldmolVar'): self.oldmolVar={}
        molNames = self.vf.Mols.name
        if molNames:
            for i in molNames:
                if i not in self.molVar.keys():
                    self.molVar[i]=Tkinter.IntVar()
                    self.oldmolVar[i]=0
            if len(self.vf.selection):
                selNames = self.vf.selection.top.uniq().name
                for n in self.molVar.keys():
                    self.molVar[n].set(n in selNames)
                    self.oldmolVar[n] = n in selNames
            else:
                for n in self.molVar.keys():
                    self.molVar[n].set(0)
                    self.oldmolVar[n] = 0
        self.buildMenu(molMenubutton,molNames,self.molVar,self.oldmolVar,self.getMolVal)

    def getMolVal(self, event=None):
        self.vf.setSelectionLevel(Protein, busyIdle=0, log=0, setupUndo=0)
        #self.vf.setIcomLevel(Protein, busyIdle=0, log=0)
        for i in self.molVar.keys():
            newMol=self.findItemFromName(self.vf.Mols, i)
            newVal = self.molVar[i].get()
            if newVal!=self.oldmolVar[i]:
                if newVal==1:
                    #select if button on
                    self.vf.select(newMol)
                else:
                    #deselect if button off
                    self.vf.deselect(newMol)
                self.oldmolVar[i]=newVal


    def buildChainMenus(self,event=None):
        chainMenubutton = self.ifd.entryByName['Chain List']['widget']
        if not hasattr(self,'chainVar'): self.chainVar = {}
        if not hasattr(self,'oldchainVar'): self.oldchainVar = {}
        #NB this assumes there may be molecules with no chains
        chMols = MoleculeSet(filter(lambda x: Chain in x.levels, self.vf.Mols))
        chainIDList = []
        if len(chMols):
            chains = chMols.findType(Chain)
            for ch in chains:
                newname = ch.full_name()
                chainIDList.append(newname)
                if newname not in self.chainVar.keys():
                    self.chainVar[newname]=Tkinter.IntVar()
                    self.oldchainVar[newname]=0
            if len(self.vf.selection):
                selChains = self.vf.selection.findType(Chain)
            else: selChains = ChainSet([])
            selNames = []
            if len(selChains):
                for ch in selChains:
                    selNames.append(ch.full_name())
            for n in self.chainVar.keys():
                ans = n in selNames
                self.chainVar[n].set(ans)
                self.oldchainVar[n] = ans
        self.buildMenu(chainMenubutton,chainIDList,self.chainVar,self.oldchainVar,self.getChainVal)


    def getChainVal(self, event=None):
        self.vf.setSelectionLevel(Chain, busyIdle=0, log=0, setupUndo=0)
        #self.vf.setIcomLevel(Chain, busyIdle=0, log=0)
        chains = self.vf.Mols.findType(Chain)
        for i in self.chainVar.keys():
            newChain=self.findItemFromID(chains,i)
            newVal= self.chainVar[i].get()
            if newVal!=self.oldchainVar[i]:
                if self.chainVar[i].get()==1:
                    #select if button on
                    self.vf.select(newChain)
                else:
                    #deselect if button off
                    self.vf.deselect(newChain)
                self.oldchainVar[i]=newVal


    def buildSetsMenus(self,event=None):
        setsMenubutton = self.ifd.entryByName['Sets List']['widget']
        if not hasattr(self,'setsVar'): self.setsVar={}
        if not hasattr(self,'oldsetsVar'): self.oldsetsVar={}
        #cannot use this here:
        #sets = ['backbone', 'backbone+H', 'sidechain']
        sets = []
        #for k in sets__.keys():
        for k in self.vf.sets.keys():
            sets.append(k)
        #sets = sets__.keys()  #
        self.buildMenu(setsMenubutton,sets,self.setsVar,self.oldsetsVar,self.getSetsVal)
    

    def getSetsVal(self, event=None):
        for i in self.setsVar.keys():
            #newSet = sets__[i][0]
            newSet = self.vf.sets[i]
            newNode0 = newSet[0]
            #w/ newclass Set: level here
            lev = newNode0.__class__
            if lev == Protein: lev = Molecule
            self.vf.setSelectionLevel(lev, busyIdle=0, log=0, setupUndo=0)
            #self.vf.setIcomLevel(lev, busyIdle=0, log=0)
            newVal = self.setsVar[i].get()
            if newVal != self.oldsetsVar[i]:
                if newVal==1:
                    #select if button on
                    self.vf.select(newSet)
                else:
                    #deselect if button off
                    self.vf.deselect(newSet)
                self.oldsetsVar[i]=newVal


mvDirectSelectCommandGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                                 'menuButtonName':'Select',
                                 'menuEntryLabel':'Direct Select',
                                 'separatorBelow':1}


MVDirectSelectCommandGUI = CommandGUI()
MVDirectSelectCommandGUI.addMenuCommand('menuRoot', 'Select', 'Direct Select', separatorBelow=1 )



import numpy.oldnumeric as Numeric 
class MVSelectSphericalRegion(MVCommand):
    """This Command selects nodes from a specified base within specified spherical region(s) 
    \nPackage : Pmv
    \nModule  : selectionCommands
    \nClass   : MVSelectSphericalRegion
    \nCommand : selectInSphere
    \nSynopsis:\n
        None <- selectInSphere(centerList, radius, selList, **kw)
    \nRequired Arguments:\n       
        centerList --- specifies the centers of the selection spheres
        \nradius --- radius of the selection spheres
        \nselList --- specifies selection base (atoms to test)
                possible selList values are ['all'], a list of sets or a list
                of molecule names.
    """
    def onAddCmdToViewer(self):
        self.form = None
        self.radius = 5.
        self.centerList = None
        self.atar = []
        self.selList = ['all']

        from DejaVu.Spheres import Spheres
        from DejaVu.Geom import Geom
        
        self.masterGeom = Geom("selectInSphereGeoms", 
                               shape=(0,0), protected=True)

        self.selSph = Spheres(name='SelSphReg_selSph', 
                              materials=((1.,1.,0),), shape=(0,3), radii=5.0, 
                              quality=15, inheritMaterial=0, protected=True,
                              inheritFrontPolyMode=0, frontPolyMode='line')
        from opengltk.OpenGL import GL
        self.selSph.frontPolyMode = GL.GL_LINE
        #self.selSph.frontPolyMode = GL.GL_POINT
        self.selSph.Set(visible=1, tagModified=False)
        self.selSph.pickable = 0
        from DejaVu.Points import CrossSet
        self.cenCross = CrossSet('SelSphReg_cenCross', 
                                 inheritMaterial=0, materials=((1.,0.2,0),),
                                 offset=0.5,lineWidth=2, protected=True)
        self.cenCross.Set(visible=0, tagModified=False)
        self.cenCross.pickable = 0
        if self.vf.hasGui:
            miscGeom = self.vf.GUI.miscGeom
            self.vf.GUI.VIEWER.AddObject(self.masterGeom, parent=miscGeom)
            self.selLevel = Tkinter.StringVar()
            self.selectionBase = Tkinter.StringVar()
            self.selectionCenter = Tkinter.StringVar()
            self.vf.GUI.VIEWER.AddObject(self.selSph, redo=0,
                                parent=self.masterGeom)
            self.vf.GUI.VIEWER.AddObject(self.cenCross, redo=0,
                                parent=self.masterGeom)


    def onAddObjectToViewer(self,obj):
        if not self.form: return
        val =self.selectionBase.get()
        if val=='fromList':
            self.lb.insert('end',obj.name)


    def onRemoveObjectFromViewer(self, obj):
        if not self.form: return
        val =self.selectionBase.get()
        ltuple=self.lb.get(0,'end')
        llist=list(ltuple)
        if val=='fromList' and obj.name in llist:
            lindex=llist.index(obj.name)
            self.lb.delete(lindex)


    def getTransformedCoords(self, atom):
        if not atom.top.geomContainer:
            return atom.coords
        g = atom.top.geomContainer.geoms['master']
        coords = atom.coords
        pth = [coords[0], coords[1], coords[2], 1.0]
        #c = self.applyTransformation(atom.coords, g.GetMatrix(g))
        c = Numeric.dot(g.GetMatrix(g), pth)[:3]
        return c.astype('f')


    def setupUndoBefore(self,  *args, **kw):
        select = self.vf.select
        oldselection = self.vf.selection.copy()
        self.addUndoCall(oldselection, {}, self.name)

    def undo(self):
        if  self.undoStack:
            args1, kw1 = self.undoStack.pop()  
            self.vf.select(args1, only=True, topCommand=0)

    def __call__(self, centerList, radius, selList, **kw):
        """None <- selectInSphere(centerList, radius, selList, **kw)
        \ncenterList --- specifies the centers of the selection spheres
        \nradius --- radius of the selection spheres
        \nselList --- specifies selection base (atoms to test)
                possible selList values are ['all'], a list of sets or a list
                of molecule names. 
        """
        apply( self.doitWrapper, (centerList, radius, selList), kw )


    def getAtoms(self, centerList, radius, selList):
        #base_nodes is an AtomSet constructed from selList
        base_nodes = AtomSet([])
        if selList[0]=='all':
            base_nodes = self.vf.allAtoms
        elif selList[0] in self.vf.sets.keys():
            #elif selList[0] in sets__.keys():
            #need to get all atoms in all sets specified
            for item in selList:
                newnodes = self.vf.sets[item].findType(Atom)
                #newnodes = sets__[item][0].findType(Atom)
                base_nodes = base_nodes+newnodes
        else:
            for item in selList:
                mol = self.vf.Mols.NodesFromName(item)[0]
                newnodes = mol.findType(Atom)
                base_nodes = base_nodes+newnodes
        if len(base_nodes)==0:
            t = '1:no base for selection specified: selList=', selList
            self.vf.warningMsg(t)
            return 'ERROR'
        atar = Numeric.array(base_nodes.data)

        #use transformed coords:
        tcoords = []
        for at in base_nodes:
            tcoords.append(self.getTransformedCoords(at))
        coords = Numeric.array(tcoords, 'f')

        ats = []
        for center in centerList:
            d = coords - Numeric.array(center, 'f')
            d = d * d
            d = Numeric.sum(d,1)
            atindex = Numeric.nonzero(Numeric.less(d, radius * radius)) 
            newats = Numeric.take(atar, atindex)
            if len(newats)>0: 
                ats = ats + newats.tolist()
        return AtomSet(ats)


    def doit(self, centerList, radius, selList):
        """centerList, radius, selList"""
        #this cmd logs centerList as a list of arrays of coords
        #this cannot be replayed without from numpy.oldnumeric import array
        #however, in the tests self.vf has no logAllFile
        #hence this ugliness:  -rh 8/05
        if hasattr(self.vf, 'logAllFile'):
            self.vf.logAllFile.write("from numpy.oldnumeric import array, float32\n")
        if not centerList:
            t = 'no centerList specified'
            self.vf.warningMsg(t)
            return 'ERROR'
        if not radius:
            t = 'no radius specified'
            self.vf.warningMsg(t)
            return 'ERROR'
        if len(selList)==0:
            t = 'no selection base specified'
            self.vf.warningMsg(t)
            return 'ERROR'

        ats = self.getAtoms(centerList, radius, selList)

        if len(ats)>0:
            #atSet = AtomSet(list(ats))
            ###FIX ME! this assumes 4 level hierarchy
            lev = ats[0].__class__
            if lev==Protein: 
                lev = Molecule
            vflev = self.vf.selectionLevel
            if vflev!=lev:
                self.vf.setSelectionLevel(lev, busyIdle=0, log=0, setupUndo=0)
            self.vf.clearSelection(topCommand=0)
            self.vf.select(ats, topCommand=0)
        if self.form:
            self.form.lift()


    def drawSphere(self):
        #callback to update command's geoms 
        ##7/21: now self.centerList is a List of centers
        if self.centerList and self.radius:
            self.selSph.Set(vertices=self.centerList, radii=self.radius,
                            visible=1, tagModified=False)
            if self.vf.hasGui:
                self.vf.GUI.VIEWER.Redraw()
        else:
            self.selSph.Set(visible=0, tagModified=False)
            self.cenCross.Set(visible=0, tagModified=False)
            if self.vf.hasGui:
                self.vf.GUI.VIEWER.Redraw()
        if self.form:
            self.form.lift()


    def stopSelection(self):
        #????icom callback
        self.selSph.Set(visible=0, tagModified=False)
        self.cenCross.Set(visible=0, tagModified=False)
        if hasattr(self, 'ap'):
            self.ap.stop()
            del self.ap



    def buildForm(self):
        #build ifd and form
        ifd = self.ifd = InputFormDescr(title='Select In Spherical Region')
        self.selectionBase.set('all')
        ifd.append({'widgetType': Tkinter.Label,
                    'name':'cenSphLab',
                    'wcfg':{'text':'Center Spherical Region On:',
                            'bd':2,'relief':'ridge'},
                    'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                               'columnspan':4}})
        ifd.append({'widgetType':Tkinter.Radiobutton,
                    'name':'atomRB',
                    'wcfg':{'variable':self.selectionCenter,
                            'text':'an atom',
                            'value':'atom',
                            'command':self.updateCenter},
                    'gridcfg':{'sticky':Tkinter.W}}),
        ifd.append({'widgetType':Tkinter.Radiobutton,
                    'name':'curselRB',
                    'wcfg':{'variable':self.selectionCenter,
                            'text':'current selection',
                            'value':'cursel',
                            'command':self.updateCenter},
                    'gridcfg':{'sticky':Tkinter.W,'row':-1,'column':1, 'columnspan':3}}),
        ifd.append({'widgetType':Tkinter.Radiobutton,
                    'name':'pt3DRB',
                    'wcfg':{'variable':self.selectionCenter,
                            'text':'x y z',
                            'value':'xyz',
                            'command':self.updateCenter},
                    'gridcfg':{'sticky':Tkinter.W}}),
        ifd.append({'widgetType':Tkinter.Radiobutton,
                    'name':'cenSelectionRB',
                    'wcfg':{'variable':self.selectionCenter,
                            'text':'center of current selection',
                            'value':'cen_cursel',
                            'command':self.updateCenter},
                    'gridcfg':{'sticky':Tkinter.W,'row':-1,'column':1, 'columnspan':3}}),
        
        ifd.append({'name':'xval_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                        'text': 'x',
                    },
                    'type':'float',
                    'precision':2,
                    'width':30,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'value':0.,
                    'callback':self.updateCenter,
                    'oneTurn':50.,},
             'gridcfg':{'columnspan':1,'sticky':'e'}})
        ifd.append({'name':'yval_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                        'text': 'y',
                    },
                    'type':'float',
                    'precision':2,
                    'width':30,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'value':0.,
                    'callback':self.updateCenter,
                    'oneTurn':50.,},
             'gridcfg':{'columnspan':1,'sticky':'e', 'row':-1, 'column':1}})
        ifd.append({'name':'zval_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                        'text': 'z',
                    },
                    'type':'float',
                    'precision':2,
                    'width':30,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'value':0.,
                    'callback':self.updateCenter,
                    'oneTurn':50.,},
             'gridcfg':{'columnspan':1,'sticky':'e', 'row':-1, 'column':2}})
            
        ifd.append({'widgetType': Tkinter.Label,
                    'wcfg':{ 'text':'Selection Sphere Radius:',
                             'bd':2,'relief':'ridge'},
                    'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                               'columnspan':4}})
        ifd.append( {'name':'radSlider',
                     'widgetType': ExtendedSliderWidget,
                     'wcfg':{'label':' ',
                             'minval':0.1, 'maxval':30,
                             'immediate':1,
                             'init':5.0,
                             'width':300,
                             'command':self.setRadius_cb,
                             'sliderType':'float',
                             'entrypackcfg':{'side':'right'}},
                     'gridcfg':{'sticky':Tkinter.W, 'columnspan':4}})
        ifd.append({'widgetType': Tkinter.Label,
                    'wcfg':{'bd':2,'relief':'ridge',
                            'text':'Molecules To Use As Base For Selection:'},
                    'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                               'columnspan':4}})
        ifd.append({'widgetType': Tkinter.Label,
                    'wcfg':{'text':' '},
                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W,
                               'columnspan':4}})
        ifd.append({'widgetType':Tkinter.Radiobutton,
                    'name':'allRB',
                    'wcfg':{'variable':self.selectionBase,
                            'text':'all molecules',
                            'value':'all',
                            'command':self.updateBase},
                    'gridcrf':{'sticky':Tkinter.W}})
        ifd.append({'widgetType':Tkinter.Radiobutton,
                    'name':'selectionRB',
                    'wcfg':{'text':'from list',
                            'variable':self.selectionBase,
                            'value':'fromList',
                            'command':self.updateBase},
                    'gridcf':{'sticky':Tkinter.W}})
        ifd.append({'widgetType':Tkinter.Radiobutton,
                    'name':'setRB',
                    'wcfg':{'text':'a saved set',
                            'variable':self.selectionBase,
                            'value':'set',
                            'command':self.updateBase},
                    'gridcf':{'sticky':Tkinter.W}})
        ifd.append({'widgetType':ListChooser,
                    'name':'baseMols',
                    'wcfg':{'title':'Use Spheres to Select Atoms From:',
                            'mode':'multiple',
                            'lbwcfg':{'height':4,'selectmode':'multiple'}},
                    'gridcfg':{'sticky':'w','column':1,'row':-4,
                               'rowspan':10, 'columnspan':3}})
        ifd.append({'name':'selectB',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Select',
                            'command':self.select_cb},
                    'gridcfg':{'sticky':Tkinter.W+Tkinter.E}})
        ifd.append({'name':'clearB',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Clear',
                            'command':self.clear_cb},
                    'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                               'row':-1, 'column':1, 'columnspan':2}})
        ifd.append({'name':'closeB',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Close',
                            'command':self.close_cb},
                    'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                               'row':-1,'column':3}})
        self.form = self.vf.getUserInput(ifd, modal=0,blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW',self.close_cb)
        self.radSlider = self.ifd.entryByName['radSlider']['widget']
        self.lb = self.ifd.entryByName['baseMols']['widget'].lb
        self.lb.config({'selectmode':'multiple'})
        self.lb.bind('<Enter>',self.updateBase)
        self.lb.bind('<Leave>',self.updateBase)
        self.xval = self.ifd.entryByName['xval_tw']['widget']
        self.yval = self.ifd.entryByName['yval_tw']['widget']
        self.zval = self.ifd.entryByName['zval_tw']['widget']
        self.hide_xyz()
        self.old_val = ""

    def update_xyz(self, val):
        if self.old_val=="":
            if val=='xyz':
                self.repack_xyz()
        elif val!=self.old_val:
            if self.old_val=='xyz':
                self.hide_xyz()
            elif val=='xyz': 
                self.repack_xyz()


    def hide_xyz(self, event=None):
        for b in [self.xval, self.yval, self.zval]:
            b.grid_forget()


    def repack_xyz(self, event=None):
        cfgstrings = ['xval_tw', 'yval_tw', 'zval_tw']
        buttons = [self.xval, self.yval, self.zval]
        for cfg_name, b in zip(cfgstrings, buttons):
            b.grid(self.ifd.entryByName[cfg_name]['gridcfg'])


    def updateCenter(self, event=None):
        #callback for changes to radiobuttons for center
        val=self.selectionCenter.get()
        #here manage picking an atom
        selnodes= self.vf.getSelection()[:]
        self.update_xyz(val)
        if hasattr(self, 'ap'):  # if there is an atom picker delete it
            self.ap.stop()
            del self.ap
        if val == 'atom':
            from Pmv.picker import AtomPicker
            self.ap=AtomPicker(self.vf, None, gui=0,
                               callbacks=[self.setCenter_cb], immediate=1)
            self.ap.go(modal=0)
            #self.vf.GUI.setCursor('hand1')
            if len(selnodes)==1 and selnodes[0].__class__==Atom:
                #set vertices to center of selnodes[0]
                tcoords = self.getTransformedCoords(selnodes[0]) 
                self.centerList=[tcoords,]
                #self.centerList=[selnodes[0].coords]
                #!!#self.drawSphere()
            else:
                self.centerList=None
        elif val == 'cursel' or val == 'cen_cursel':
            #use current selection here
            if hasattr(self, 'ap'):
                self.ap.stop()
                del self.ap
            self.cenCross.Set(visible=0, tagModified=False)
            if len(selnodes):  
                nodes = selnodes.findType(Atom)
                tcoords = []
                for a in nodes:
                    tcoords.append(self.getTransformedCoords(a)) 
                if val=='cursel':
                    self.centerList = tcoords
                else:
                    #use average of coords of current selection here
                    npts = len(nodes)
                    self.centerList = [Numeric.array(Numeric.add.reduce(tcoords)/npts).tolist(),]
        elif val == 'xyz':
            pt = [float(self.xval.get()), float(self.yval.get()), float(self.zval.get())]
            self.cenCross.Set(vertices = (pt,))
            if hasattr(self, 'ap'):
                self.ap.stop()
                del self.ap
            #self.cenCross.Set(visible=0, tagModified=False)
            self.centerList = [(float(self.xval.get()), float(self.yval.get()), float(self.zval.get())),]
        else:
            msg = val + "is not a recognized center for SelectInSphere"
            self.vf.warningMsg(msg)
            return 'ERROR'
        self.drawSphere()
        if self.form:
            self.form.lift()
        self.old_val=val


    def setCenter_cb(self,atoms):
        #callback for self.selectionCenter=='atom'
        if atoms:
            atom=atoms[0]
            tcoords = self.getTransformedCoords(atom)
            self.centerList=[tcoords]
            self.cenCross.Set(vertices=(tcoords,),visible=1, tagModified=False)
            self.drawSphere()
            if self.form:
                self.form.lift()


    def setRadius_cb(self, eventval):
        ##callback for radius slider
        try:
            self.radius = self.radSlider.get()
            self.drawSphere()
        except ValueError:
            self.vf.warningMsg( "error in setRadius_cb" )


    def updateBase(self,event=None):
        #callback for changes to radiobuttons for mols=base of sel 
        # and changes to curselection of lb
        val=self.selectionBase.get()
        self.selList=[]
        if val == 'all':
            self.selList=['all']
            self.lb.select_clear(0,'end')
            self.lb.delete(0,'end')
        elif val == 'fromList':
             if hasattr(self, 'oldval') and self.oldval!=val:
                self.lb.select_clear(0,'end')
                self.lb.delete(0,'end')
                if not len(self.vf.Mols):
                    return
                for item in self.vf.Mols.name:
                    self.lb.insert('end',item)

             for item in self.lb.curselection():
                newstr = self.lb.get(item)
                self.selList.append(newstr)
        else:
            #here you have to select set and get its content
            #if selectionBase changed:replace entries w/set names:
            if hasattr(self, 'oldval') and self.oldval!=val:
                self.lb.select_clear(0,'end')
                self.lb.delete(0,'end')
                #for item in sets__.items():
                for item in self.vf.sets.keys():
                    self.lb.insert(0,item)
            for item in self.lb.curselection():
                newstr= self.lb.get(item)
                self.selList.append(newstr)
        self.oldval=val
        if self.form:
            self.form.lift()


    def select_cb(self, event=None):
        #callback for select button
        #NB: only in this call back if there is a form...
        apply(self.doitWrapper, (self.centerList,self.radius, self.selList),{})


    def clear_cb(self, event=None):
        #callback for clear button
        self.centerList=None
        self.drawSphere()


    def close_cb(self, event=None):
        #callback for close button
        self.vf.GUI.removeCameraCallback("<ButtonRelease-1>",
                                         self.setCenter_cb)
        if hasattr(self, 'ap'):
            self.ap.stop()
            del self.ap
        self.selSph.Set(visible=0, tagModified=False)
        self.cenCross.Set(visible=0, tagModified=False)
        self.selectionCenter.set('')
        self.vf.GUI.VIEWER.Redraw()
        self.centerList = None
        self.form.withdraw()


    def guiCallback(self):
        if not hasattr(self, 'ifd'):
            self.buildForm()
        else:
            self.form.deiconify()
            self.drawSphere()



mvSelectSphericalRegionGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                                   'menuButtonName':'Select',
                                   'menuEntryLabel':'SphericalRegion'}


MVSelectSphericalRegionGUI = CommandGUI()
MVSelectSphericalRegionGUI.addMenuCommand('menuRoot', 'Select', 'SphericalRegion')



class MVInvertSelection(MVCommand):
    """Inverts current selection within all molecules or moleuels participating
    to the selection if invertLevel is specified or a within a user specified
    set is subset is specified.

    \nPackage : Pmv
    \nModule  : selectionCommands
    \nClass   : MVInvertSelection
    \nCommand : invertSelection
    \nSynopsis:\n   
         None <- invertSelection(invertLevel=None, subset=None, **kw)
    \nArguments:\n      
         invertLevel --- 'all' or 'molecule'  
         subset      --- set of atoms, residues, chains or molecules
     """

    def __init__(self):
        self.form = None
        MVCommand.__init__(self)

    def onAddCmdToViewer(self):
        if self.vf.hasGui:
            self.invertlevel = Tkinter.StringVar()
        

    def setupUndoBefore(self,  *args, **kw):
        select = self.vf.select
        oldselection = self.vf.selection
        self.addUndoCall(oldselection, {}, self.name)

    def undo(self):
        if  self.undoStack:
            args1, kw1 = self.undoStack.pop() 
            self.vf.select(args1, only=True, topCommand=0)

    def doit(self, invertLevel=None, subset=None):
        # invertLevel can be 'all' or 'molecule'
        # if invertLevel is None and subset is not None the inversion is made
        # in the given subset
        
        level = self.vf.selectionLevel
        sel = self.vf.selection
        if len(sel):
            old=sel[:]
        else:
            old = lev([])

        if invertLevel is not None:
            if invertLevel == 'all':
                if level==Atom:
                    allobjects = self.vf.Mols.allAtoms
                else:
                    allobjects = self.vf.Mols.findType(level)

            elif invertLevel == 'molecule':
                if self.vf.selection:
                    mols = sel.top.uniq()
                    allobjects = sel[0].setClass()
                    for mol in mols:
                        allobjects = allobjects + mol.findType(level)
                                                   
##             all = self.vf.Mols.allAtoms

##             if invertLevel == 'all':
##                 all=self.vf.Mols.findType(lev)

##             elif invertLevel == 'molecule':
##                 if self.vf.selection:
##                     mols = sel.top.uniq()
##                     all = sel[0].setClass()
##                     for mol in mols:
##                         all = all + mol.findType(lev)

##             if all == None or len(all) == 0: 
##                 msg = 'No molecules!'
##                 self.vf.warningMsg(msg)
##                 return 'ERROR'

##             if len(old)==0:
##                 self.vf.setSelectionLevel(all[0].__class__, busyIdle=0, log=0, setupUndo=0)
##                 #self.vf.setIcomLevel(all[0].__class__, 
##                     #log = 0, KlassSet = all[0].setClass)
##                 self.vf.select(all, topCommand=0)
##             else:
##                 self.vf.deselect(old, topCommand=0)
##                 self.vf.select(all-old, topCommand=0)

        elif subset is not None:
            allobjects = subset.findType(level)

        if allobjects == None or len(allobjects) == 0: 
            msg = 'No molecules!'
            self.vf.warningMsg(msg)
            return 'ERROR'

        self.vf.deselect(old & allobjects, topCommand=0)
        self.vf.select(allobjects - old, topCommand=0)

            
    def __call__(self, invertLevel=None, subset=None, **kw):
        """None <--- invertSelection(invertLevel=None, subset_=None **kw)
        \ninvertLevel --- 'all' or 'molecule'
        \nsubset      --- ane set of atoms, residues, chains or molecules"""
        
        # assert invertLevel is a good value
        if invertLevel:
            assert invertLevel in ['all', 'molecule']
        if isinstance(subset, str):
            subset = self.vf.expandNodes(subset)
        if invertLevel is None and subset is None:
            return
        apply(self.doitWrapper,(invertLevel,subset), kw)

        
    def guiCallback(self):
        numMols = len(self.vf.Mols)
        if numMols > 1:
            # create the form descriptor
            levelNames = ['all', 'molecule']
            idf = self.ifd = InputFormDescr(title = 'Set Level for Invert Selection')
            idf.append({ 'name': 'level', 'widgetType':Tkinter.Radiobutton,
                         'listtext': levelNames, 'variable': self.invertlevel,
                         'gridcfg':{'sticky':Tkinter.W}})
            val = self.vf.getUserInput(idf)            
            if len(val)>0: 
                self.doitWrapper(val['level'])
            else: return
        else:
            self.doitWrapper('all', redraw = 1)

mvInvertSelectionGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                             'menuButtonName':'Select',
                             'menuEntryLabel':'invert selection',
                             'separatorBelow':1, }

MVInvertSelectionGUI = CommandGUI()
MVInvertSelectionGUI.addMenuCommand('menuRoot', 'Select', 'Invert Selection',
                 separatorBelow=1 )

#MVInvertSelectionGUI.addButton('selectionBar', 'Invert')
##next line makes the button the same width as checkbuttons
#MVInvertSelectionGUI.buttonCfg['pady']=1


class SelectNoWaterHeteroAtomsCommand(MVSelectFromStringCommand, MVSelectCommand):
    """This class provides a command to select all hetero atoms that are not
    in a water molecule.

    \nPackage:Pmv
    \nModule :selectionCommands
    \nClass:selectNonWaterHeteroAtomsCommand
    \nCommand:selectHeteroAtoms
    \nSynopsis:\n
        None <--- selectHetereoAtoms(nodes, negate=False, only=False, xor=False, intersect=False, **kw)
        this command will select hetero atoms that are not water combine
        them with the current selection. As a consequence, the current
        selection will be changed to an atom set. The selected hetero atoms
        are returned as an AtomSet object.
    \nRequired Arguments:\n   
        nodes --- TreeNodeSet from which to select hetero atoms
    \nexample:\n
      >>> SelectNoWaterHeteroAtomsCommand()\n
      >>> SelectNoWaterHeteroAtomsCommand(molecule)\n
    """
    def __init__(self):
        MVSelectFromStringCommand.__init__(self)
        self.flag = self.flag | self.objArgOnly


    def __call__(self, nodes=None, negate=False, only=False,
                        xor=False, intersect=False, **kw):
        """AtomSet <- selectHetereoAtoms(nodes, negate=False, only=False, 
                                         xor=False, intersect=False )
        \nRequired Arguments:\n
            nodes --- can be a string, a TreeNode or a treeNodeSet
        \nOptional Arguments:\n
            negate --- is 1 nodes are removed from current selection
            \nonly  --- is  1 the current selection is replaced by the nodes
            \nxor --- when True hetero atmos are xor'ed with current selection
            \nintersect -- when True hetero atoms are intersected with current selection
        """
        if nodes is None: nodes = self.vf.Mols
        if type(nodes) is types.StringType:
           self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        kw['negate']= negate
        kw['only']= only
        kw['xor']= xor
        kw['intersect']= intersect
        return apply( self.doitWrapper, (nodes,), kw )


    def doit(self, nodes, negate=False, only=False, xor=False, intersect=False):
        """
        select/deselect hetero atoms
        """
        if len(nodes)==0:
            allAtoms = self.vf.allAtoms
        else:
            allAtoms = nodes.findType(Atom)

        het = AtomSet( [a for a in allAtoms if a.hetatm and
                        a.parent.type!='WAT' and a.parent.type!='HOH'] )

        if len(het)==0:
            return AtomSet( [])
            
        self.vf.setSelectionLevel(Atom, topCommand=0, callListener=0, setupUndo=0)
        if only:
            self.vf.selection = het
                
        curSelection = self.vf.selection
        self.vf.selection = curSelection.findType(Atom)
        if negate:
            self.vf.selection = self.vf.selection - het
        elif xor:
            self.vf.selection = self.vf.selection ^ het
        elif intersect:
            self.vf.selection = self.vf.selection & het
        else:
            self.vf.selection = self.vf.selection | het

        if not self.vf.hasGui:
            return self.vf.selection

        self.updateSelectionFeedback()
        self.highlightSelection()
        
        return het


    def buildForm(self, event=None):
        self.selPick.set(0)
        ifd = self.ifd = InputFormDescr(title = 'Select no water Hetero')

        ifd.append({'name': 'addBut',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'bd':3, 'text': 'Add',
                            'command': self.add},
                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W,'row':4,
                               'column':0, 'columnspan':1},
                    })
        ifd.append({'name': 'removeBut',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'bd':3, 'text': 'Remove',
                            'command': self.remove},
                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W,'row':4,
                               'column':1, 'row':-1, 'columnspan':2},
                    })
        ifd.append({'name': 'xorBut',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'bd':3, 'text': 'Xor',
                            'command': self.xor},
                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W,'row':4,
                               'column':3,'row':-1, 'columnspan':1},
                    })
        ifd.append({'name': 'intersectBut',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'bd':3, 'text': 'Intersect',
                            'command': self.intersect},
                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W,'row':4,
                               'column':4, 'row':-1, 'columnspan':2},
                    })
        ifd.append({'widgetType':Tkinter.Button,
                    'wcfg':{'bd':4, 'text':'Dismiss',
                            'command': self.Dismiss_cb},
                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W,
                               'columnspan':6}})
        self.form = self.vf.getUserInput(self.ifd, modal = 0, blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW',self.Dismiss_cb)
        self.xorBut = self.ifd.entryByName['xorBut']['widget']
        self.intersectBut = self.ifd.entryByName['intersectBut']['widget']
        self.removeBut = self.ifd.entryByName['removeBut']['widget']
        self.addBut = self.ifd.entryByName['addBut']['widget']
        if not hasattr(self,'setsVar'): self.setsVar={}
        if not hasattr(self,'oldsetsVar'): self.oldsetsVar={}
        for button in [self.xorBut, self.intersectBut, self.removeBut]:
            if len(self.vf.selection)==0:
                button.config(state='disabled')


    def xor(self):
        self.doit(self.vf.allAtoms, xor=True)
        self.setButtonState()


    def remove(self):
        self.doit(self.vf.allAtoms, negate=True)
        self.setButtonState()


    def add(self):
        self.doit(self.vf.allAtoms)
        self.setButtonState()


    def intersect(self):
        self.doit(self.vf.allAtoms, intersect=True)
        self.setButtonState()


    def guiCallback(self):
        if not hasattr(self, 'ifd'):
            self.buildForm()
        else:
            self.form.deiconify()
            self.form.lift()
        if self.vf.userpref['Selection Object']['value'] == 'none':
            self.showSelSpheres.set(0)
        else:
            self.showSelSpheres.set(1)

MVSelectNoWaterHeteroAtomsCommandGUI = CommandGUI()
MVSelectNoWaterHeteroAtomsCommandGUI.addMenuCommand('menuRoot', 'Select', 'Select hetero Atoms')

class MVExpandSelection(MVCommand):
    """Expands selection around current selection using selectInSphere

    \nPackage : Pmv
    \nModule  : selectionCommands
    \nClass   : MVExpandSelection
    \nCommand : expandSelection
    \nSynopsis:\n   
         None <- expandSelection(selection, centers, dist, keys)
    \nArguments:\n      
     """

    def doit(self, selection, centers, dist, keys):
        self.vf.selectInSphere(centers, dist, keys, topCommand=0)
        self.vf.select(selection, topCommand=0)

    def setupUndoBefore(self,  *args, **kw):
        select = self.vf.select
        oldselection = self.vf.selection.copy()
        self.addUndoCall(oldselection, {}, self.name)

    def undo(self):
        if  self.undoStack:
            args1, kw1 = self.undoStack.pop() 
            self.vf.select(args1, only=True, topCommand=0)
            
class MVSelectAround(MVCommand):
    """Expands selection around current selection using selectInSphere

    \nPackage : Pmv
    \nModule  : selectionCommands
    \nClass   : MVExpandSelection
    \nCommand : expandSelection
    \nSynopsis:\n   
         None <- expandSelection(selection, centers, dist, keys)
    \nArguments:\n      
     """

    def doit(self, selection, centers, dist, keys):
        self.vf.selectInSphere(centers, dist, keys, topCommand=0)
        self.vf.deselect(selection, topCommand=0)

    def setupUndoBefore(self,  *args, **kw):
        select = self.vf.select
        oldselection = self.vf.selection.copy()
        self.addUndoCall(oldselection, {}, self.name)

    def undo(self):
        if  self.undoStack:
            args1, kw1 = self.undoStack.pop() 
            self.vf.select(args1, only=True, topCommand=0)


commandList = [ 
    {'name':'select', 'cmd':MVSelectCommand(),'gui': None},
    {'name':'deselect', 'cmd':MVDeSelectCommand(),'gui': None},
    {'name':'clearSelection', 'cmd':MVClearSelection(),'gui':MVClearSelectionGUI},
    {'name':'expandSelection', 'cmd':MVExpandSelection(),'gui':None},
    {'name':'selectAround', 'cmd':MVSelectAround(),'gui':None},    
    {'name':'saveSet', 'cmd':MVSaveSetCommand(), 'gui':MVSaveSetCommandGUI},
    {'name':'createSetIfNeeded', 'cmd':MVCreateSetIfNeeded(), 'gui':None},
    {'name':'invertSelection', 'cmd':MVInvertSelection(), 'gui':MVInvertSelectionGUI},
    {'name':'selectSet','cmd':MVSelectSetCommand(),
     'gui': MVSelectSetCommandGUI},
    {'name':'selectFromString','cmd':MVSelectFromStringCommand(),
            'gui': MVSelectFromStringCommandGUI},
    {'name':'directSelect','cmd':MVDirectSelectCommand(),
            'gui': MVDirectSelectCommandGUI},
    {'name':'selectInSphere','cmd':MVSelectSphericalRegion(),
         'gui': MVSelectSphericalRegionGUI},
    {'name':'selectHeteroAtoms', 'cmd':SelectNoWaterHeteroAtomsCommand(),'gui': MVSelectNoWaterHeteroAtomsCommandGUI},
]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand( dict['cmd'], dict['name'], dict['gui'])
