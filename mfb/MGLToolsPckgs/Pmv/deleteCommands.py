
#############################################################################
#
# Author: Ruth Huey, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/deleteCommands.py,v 1.56.2.9 2012/03/14 21:01:06 sanner Exp $
#
# $Id: deleteCommands.py,v 1.56.2.9 2012/03/14 21:01:06 sanner Exp $
#

"""
This Module implements commands to delete items from the MoleculeViewer:
for examples:
    Delete Molecule
"""

import types, string

from ViewerFramework.VFCommand import CommandGUI
from Pmv.moleculeViewer import DeleteAtomsEvent

class AfterDeleteAtomsEvent(DeleteAtomsEvent):
    pass

from Pmv.mvCommand import MVCommand
from Pmv.guiTools import MoleculeChooser
##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.util.callback import CallBackFunction

from MolKit.protein import Coil, Helix, Strand, Turn
from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import MoleculeSet, AtomSet, Atom
from MolKit.protein import SecondaryStructure

import Tkinter

from ViewerFramework.VF import VFEvent

class BeforeDeleteMoleculesEvent(VFEvent):
    pass


class DeleteMolecule(MVCommand):
    """Command to delete a molecule from the MoleculeViewer
    \nPackage : Pmv
    \nModule  :
    deleteCommands
    \nClass   : DeleteMolecule
    \nCommand : deleteMolecule
    \nSynopsis:\n
        None<---deleteMol(nodes, **kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection
           It resets the undo stack automatically.\n
    """
    
    def onAddCmdToViewer(self):
        self.vf._deletedLevels = []
        if  not self.vf.commands.has_key('select'):
            self.vf.loadCommand("selectionCommands", "select", "Pmv",
                                topCommand=0)
        if  not self.vf.commands.has_key('clearSelection'):
            self.vf.loadCommand("selectionCommands", "clearSelection", "Pmv",
                                topCommand=0)

    def onAddObjectToViewer(self, obj):
        if hasattr(self, 'chooser')\
               and self.chooser is not None \
               and self.form.root.winfo_exists():        
            w = self.chooser.form.descr.entryByName['Molecule']['widget']
            molParser = obj.parser
            molStr = molParser.getMoleculeInformation()
            w.add((obj.name, molStr))
 
           
    def deleteMolecule_cb(self):
        """called each time the 'Delete Molecule' button is pressed"""
        mols = self.chooser.getMolSet()
        if mols is not None and len(mols):
            if self.vf.undoCmdStack == []:
                undoable = self.undoableVar.get()
                for mol in mols:
                    self.doitWrapper(mol, redraw=0, undoable=undoable)
            else:
                self.continue_cb()
                

    def hide_cb(self):
        if hasattr(self, 'chooser'):
            if self.chooser.ipf.form is not None:
                mols = self.chooser.getMolSet()
                self.vf.showMolecules(mols.name, negate=1, topCommand=0)
                self.chooser.done_cb()
            self.idf.form.destroy()
            

    def continue_cb(self):
        if hasattr(self, 'chooser'):
            if self.chooser.ipf.form is not None:
                mols = self.chooser.getMolSet()
                undoable = self.undoableVar.get()
                if not undoable:
                    self.vf.resetUndo(topCommand=0)
                for mol in mols:
                    self.doitWrapper(mol, redraw=0, undoable=undoable)
            #self.idf.form.destroy()


    def cancel_cb(self):
        self.idf.form.destroy()
        
    def guiCallback(self):
        if len(self.vf.Mols) == 0: return
        self.chooser = MoleculeChooser(self.vf,mode = 'extended',
                                       title='Choose Molecules to delete' )

        self.undoableVar =Tkinter.IntVar()
        self.undoableVar.set(1)
        self.chooser.ipf.append({'name':'Undo',
                                 'widgetType':Tkinter.Checkbutton,
                                 'wcfg':{ 'text':' Undoable Delete', 'variable':self.undoableVar},
                                 'gridcfg':{'sticky':Tkinter.E+Tkinter.W}}
                                 )
        
        self.chooser.ipf.append({'name':'Delete Button',
                                 'widgetType':Tkinter.Button,
                                 'text':'Delete Molecule',
                                 'wcfg':{'bd':6},
                                 'gridcfg':{'sticky':Tkinter.E+Tkinter.W},
                                 'command': self.deleteMolecule_cb})
        self.form = self.chooser.go(modal=0, blocking=0)


    def deleteMol(self, mol, undoable=False):
        """ Function to delete all the references to each elements of a
        molecule and then these elements and the molecule to free the
        memory space."""

        #  Call the removeObject function for all the command having an
        # onRemoveMol function
        self.vf.removeObject(mol, undoable=undoable)

        # Maybe do that in moleculeViewer ???
        # also need to clean up selector.selection:
        nodes = self.vf.getSelection()
        mol.__class__._numberOfDeletedNodes = 0
        node = mol
        while len(node.children):
            node = node.children

        # Initialize the variable _numberOfDeletedNodes at 0
        node[0].__class__._numberOfDeletedNodes = 0
        sslevels = [Coil, Helix, Strand, Turn]
        # Initialize the variable _numberOfDeletedNodes for each secondary
        # structure to 0.
        for sl in sslevels:
            # Initialize the variable _numberOfDeletedNodes at 0
            sl._numberOfDeletedNodes = 0

        # but only change selection if there is any
        if nodes is not None and len(nodes)>0:
            setClass = nodes.__class__
            thisMolNodes = setClass(nodes.get(lambda x, mol=mol: x.top==mol))
            #only change selection if this molecule has any nodes in it
            if len(thisMolNodes)>0:
                nodes = nodes-thisMolNodes
                self.vf.clearSelection(topCommand=0)
                if nodes is not None:
                    self.vf.select(nodes)
                    #self.vf.selector.select(nodes)

        if hasattr(self, 'chooser') and self.form.root.winfo_exists():
            # update the listChooser
            lc = self.chooser.ipf.entryByName['Molecule']['widget']
            lc.remove(mol.name)
            #lc.clearComments()

        #check for any possible reference in self.vf.GUI.VIEWER.lastPick
        if self.vf.hasGui and self.vf.GUI.VIEWER.lastPick:
            for key in self.vf.GUI.VIEWER.lastPick.hits.keys():
                if hasattr(key,'mol'):
                    if mol==key.mol:
                        del self.vf.GUI.VIEWER.lastPick.hits[key]

        # Remove the atoms of the molecule you are deleting from the
        # the AtomSet self.vf.allAtoms
        self.vf.allAtoms = self.vf.allAtoms - mol.allAtoms

        if not undoable:
            # Delete all the reference to the atoms you want to delete
            if hasattr(mol.allAtoms, 'bonds'):
                bnds = mol.allAtoms.bonds[0]
                for b in bnds:
                    b.__dict__.clear()
                    del(b)
            
            mol.allAtoms.__dict__.clear()
            del mol.allAtoms
    
            if self.vf.hasGui and hasattr(mol, 'geomContainer'):
                for g in mol.geomContainer.geoms.values():
                    if hasattr(g, 'mol'):
                        delattr(g, 'mol')
    
                mol.geomContainer.geoms.clear()
                mol.geomContainer.atoms.clear()
                delattr(mol.geomContainer, 'mol')
                del mol.geomContainer
    
            if hasattr(mol, 'atmNum'):
                mol.atmNum.clear()
                del mol.atmNum
    
            if hasattr(mol, 'childByName'):
                mol.childByName.clear()
                del mol.childByName
    
            if hasattr(mol, 'parser') and hasattr(mol.parser, 'mol'):
                delattr(mol.parser,'mol')
                del mol.parser

        # delete molecule from Vision, if Vision is running
        if self.vf.visionAPI:
            self.vf.visionAPI.remove(mol)

        if not undoable:
            if len(mol.children):
                deletedLevels = mol.deleteSubTree()
            else:
                deletedLevels = []
            # then delete all the refences to the molecule
            del mol.top
            # Then delete the molecule
            deletedLevels.insert(0, mol.__class__)
    
            mol.__dict__.clear()
            del mol
        
            self.vf._deletedLevels = deletedLevels

        if len(self.vf.Mols) == 0 and hasattr(self, 'chooser') \
                and self.form.root.winfo_exists():
            self.chooser.done_cb()


    def getFreeMemoryInformation(self):
        """Store how many TreeNodes have been actually free'ed during the
        last delete operation in a dictionary"""

        memoryInformation = {}
        #print 'self.vf._deletedLevels=', self.vf._deletedLevels
        for d in self.vf._deletedLevels:
            #print 'checking ', d, ' for deletedNodes'
            memoryInformation[d.__name__] = d._numberOfDeletedNodes
        sslevels = [Coil, Helix, Strand, Turn]
##          geomslevels = [IndexedPolylines, IndexedPolygons]
        # Have to loop on the known secondarystructure because our
        # Data structure doesn't support multiple children and parents.
        for sl in sslevels:
            if sl._numberOfDeletedNodes!=0:
                memoryInformation[sl.__name__] = sl._numberOfDeletedNodes

##          for sg in geomslevels:
##              if sl._numberOfDeletedNodes!=0:
##                  memoryInformation[sl.__name__] = sl._numberOfDeletedNodes
                
        return memoryInformation


    def doit(self, nodes,  undoable=False):
        #if called with no selection, just return
        molecules, nodeSets = self.vf.getNodesByMolecule(nodes)
        event = BeforeDeleteMoleculesEvent(molecules)
        self.vf.dispatchEvent(event)
        for mol in molecules:
            self.deleteMol(mol, undoable)
        if self.vf.hasGui:
            self.vf.GUI.VIEWER.SetCurrentObject(self.vf.GUI.VIEWER.rootObject)
        if not undoable:
            self.vf.resetUndo(topCommand=0)

            
    def __call__(self, nodes, undoable=False, **kw):
        """None <- deleteMol(nodes, **kw)
        \nnodes: TreeNodeSet holding the current selection.
        """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        kw['undoable'] = undoable
        self.doitWrapper( *(nodes,), **kw )


    def setupUndoBefore(self, molecule, undoable=False):
        if undoable:
            if type(molecule) is types.StringType:
                molecules, nodeSets = self.vf.getNodesByMolecule(molecule)
                if not len(molecules):return
                molecule = molecules[0]
            molecule.code = self.vf.getStateCodeForMolecule(molecule)
            self.addUndoCall( [molecule], {},  self.name )
            
    def undo(self):
        """Undo for DeleteMolecule:
        We use self.vf.getStateCodeForMolecule from setupUndoBefore to restore the state of the molecule.
        """
        mol = self.undoStack.pop()
        mol = mol[0][0]
        self.vf.addMolecule(mol)
        exec(mol.code, {'self':self.vf})
            
from Pmv.deleteCommandsGUI  import DeleteMoleculeGUI  

class DeleteAllMolecules(DeleteMolecule):
    """Command to delete all molecules from the MoleculeViewer
    \nPackage : Pmv
    \nModule  : deleteCommands
    \nClass   : DeleteAllMolecules
    \nCommand : deleteAllMolecules
    \nSynopsis:\n
        None<---deleteAllMolecules( **kw)
    \nRequired Arguments:\n
         It resets the undo stack automatically.\n
    """
            
    def onAddCmdToViewer(self):
        self.vf._deletedLevels = [] 
           
    def guiCallback(self):
        """called each time the 'Delete All Molecules' button is pressed"""
        if len(self.vf.Mols) == 0: 
            self.warningMsg("No molecules present in the Viewer")
            return
        mols = self.vf.Mols
        if mols is not None and len(mols):
            text = """WARNING: This command cannot be undone.
            if you choose to continue the undo list will be reset.
            Do you want to continue?""" 
            if not hasattr(self, 'idf'): 
                self.idf = InputFormDescr(title="WARNING")
                self.idf.append({'widgetType':Tkinter.Label,
                            'wcfg':{'text':text},
                            'gridcfg':{'columnspan':3,'sticky':'w'}})

                self.idf.append({'name': 'Continue Button',
                            'widgetType':Tkinter.Button,
                            'wcfg':{'text':'CONTINUE',
                                    'command':self.continue_cb},
                            'gridcfg':{'sticky':'we'}})

                self.idf.append({'name': 'Cancel Button',
                            'widgetType':Tkinter.Button,
                            'wcfg':{'text':'CANCEL',
                                    'command':self.cancel_cb},
                            'gridcfg':{'row':-1,'sticky':'we'}})
            self.vf.getUserInput(self.idf, okcancel=0)

                


    def continue_cb(self):
        self.vf.resetUndo(topCommand=0)
        self.doitWrapper()
        if hasattr(self, 'idf') and hasattr(self.idf, 'form'):
            self.idf.form.destroy()


    def cancel_cb(self):
        if hasattr(self, 'idf') and hasattr(self.idf, 'form'):
            self.idf.form.destroy()
        

    def getFreeMemoryInformation(self):
        """Store how many TreeNodes have been actually free'ed during the
        last delete operation in a dictionary"""

        memoryInformation = {}
        #print 'self.vf._deletedLevels=', self.vf._deletedLevels
        for d in self.vf._deletedLevels:
            #print 'checking ', d, ' for deletedNodes'
            memoryInformation[d.__name__] = d._numberOfDeletedNodes
        sslevels = [Coil, Helix, Strand, Turn]
##          geomslevels = [IndexedPolylines, IndexedPolygons]
        # Have to loop on the known secondarystructure because our
        # Data structure doesn't support multiple children and parents.
        for sl in sslevels:
            if sl._numberOfDeletedNodes!=0:
                memoryInformation[sl.__name__] = sl._numberOfDeletedNodes

##          for sg in geomslevels:
##              if sl._numberOfDeletedNodes!=0:
##                  memoryInformation[sl.__name__] = sl._numberOfDeletedNodes
                
        return memoryInformation


    def doit(self):
        for i in range(len(self.vf.Mols)):
            self.deleteMol(self.vf.Mols[-1])
        if self.vf.hasGui:
            self.vf.GUI.VIEWER.SetCurrentObject(self.vf.GUI.VIEWER.rootObject)
            self.vf.GUI.VIEWER.Redraw()


    def __call__(self, **kw):
        """ None<---deleteAllMolecules( **kw)
        \nRemove all molecules in the viewer
        \nIt resets the undo stack automatically.
        """
        self.vf.resetUndo(topCommand=0)
        apply ( self.doitWrapper, (), kw )

    def setupUndoBefore(self):
        "DeleteALLMolecules is undoable"
        pass
from Pmv.deleteCommandsGUI  import DeleteAllMoleculesGUI


class DeleteAtomSet(MVCommand):
    """ Command to remove an AtomSet from the MoleculeViewer
    \nPackage : Pmv
    \nModule  : deleteCommands
    \nClass   : DeleteAtomSet
    \nCommand : deleteAtomSet
    \nSynopsis:\n
        None<---deleteAtomSet(atoms, **kw)\n
    \nRequired Arguments:\n
        atoms --- AtomSet to be deleted.\n
    """
    
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def onAddCmdToViewer(self):
        self.vf._deletedLevels = []
        #if self.vf.hasGui and not self.vf.commands.has_key('deleteMol'):
        if not self.vf.commands.has_key('deleteMol'):
            self.vf.loadCommand("deleteCommands", "deleteMol", "Pmv",
                            topCommand=0)
        if  not self.vf.commands.has_key('select'):
            self.vf.loadCommand("selectionCommands", "select", "Pmv",
                                topCommand=0)
        if  not self.vf.commands.has_key('clearSelection'):
            self.vf.loadCommand("selectionCommands", "clearSelection", "Pmv",
                                topCommand=0)


    def __call__(self, atoms, **kw):
        """None <- deleteAtomSet(atoms, **kw)
        \natoms: AtomSet to be deleted."""
        if type(atoms) is types.StringType:
            self.nodeLogString = "'"+atoms+"'"
        ats = self.vf.expandNodes(atoms)
        if not len(ats):
            return 'ERROR'
        ats = ats.findType(Atom)
        kw['redraw'] = True
        apply(self.doitWrapper, (ats,), kw)


    def doit(self, ats):
        """ Function to delete all the references to each atom  of a
        AtomSet."""

        # Remove the atoms of the molecule you are deleting from the
        # the AtomSet self.vf.allAtoms
        self.vf.allAtoms = self.vf.allAtoms - ats

        # If the current selection
        atmsInSel = self.vf.selection.findType(Atom)[:]
        atmsInSel.sort()
        ats.sort()
        #  Call the updateGeoms function for all the command having an
        # updateGeom function
        molecules, atomSets = self.vf.getNodesByMolecule(ats)
        done = 0
        
        event = DeleteAtomsEvent(objects=ats)
        self.vf.dispatchEvent(event)

        allAtoms = AtomSet([])
        for mol, atSet in map(None, molecules, atomSets):
            if len(atSet)==len(mol.allAtoms):
                #have to add atoms back to allAtoms for deleteMol to work
                self.vf.allAtoms = self.vf.allAtoms + atSet
                self.vf.deleteMol.deleteMol(mol)
                #if this is the last atom, quit the loop
                if mol==molecules[-1]:
                    done=1
                    break
                continue

            mol.allAtoms = mol.allAtoms - atSet
            allAtoms = allAtoms + atSet
            #FIRST remove any possible hbonds
            hbondAts = atSet.get(lambda x: hasattr(x, 'hbonds'))
            if hbondAts is not None:
                #for each atom with hbonds
                for at in hbondAts:
                    if not hasattr(at, 'hbonds'):
                        continue
                    #remove each of its hbonds 
                    for b in at.hbonds:
                        self.removeHBond(b)
            atSetCopy = atSet.copy() #fixed bug#:       1143
            for at in atSetCopy:
                for b in at.bonds:
                    at2 = b.atom1
                    if at2 == at: at2 = b.atom2
                    at2.bonds.remove(b)
                if at.parent.children:
                    at.parent.remove(at, cleanup=1)

        if len(atmsInSel):
            if atmsInSel == ats:
                # the current selection was deleted 
                self.vf.clearSelection(topCommand=0, createEvents=False)
            else:
                nodes = self.vf.selection
                lenSel = len(nodes)
                setClass = nodes.__class__
                elementClass = nodes.elementType
                if lenSel>0:
                    # this breaks if selectionlevel is Molecule, for instance
                    # setClass = nodes.__class__
                    # newSel = setClass(nodes.findType(Atom) - ats)
                    # newSel2 = setClass([])
                    newSel = atmsInSel-ats
                    newSel2 = AtomSet([])
                    # may have ats which have been deleted everywhere else
                    for at in newSel:
                        if at in at.top.allAtoms:
                            newSel2.append(at)
                    if len(newSel2)!=lenSel:
                        self.vf.clearSelection(topCommand=0)
                        if len(newSel2):
                            newSel2 = newSel2.findType(elementClass).uniq()
                            self.vf.select(newSel2, topCommand=0)

        # this fixes an exception that occured when the last chain was split
        # out of a ptrotein
        if not done:
            event = AfterDeleteAtomsEvent(objects=ats)
            self.vf.dispatchEvent(event)
        
        #this fixed a bug which occured when only 1 molecule present
        #and cmd invoked with mv.deleteAtomSet(mv.Mols[0].allAtoms)
        if not done:
            for at in ats: del at
        self.vf.resetUndo(topCommand=0)
                    
    def removeHBond(self, b):
        atList = [b.donAt, b.accAt]
        if b.hAt is not None:
            atList.append(b.hAt)
        for at in atList:
            #hbonds might already be gone
            if not hasattr(at, 'hbonds'):
                continue
            okhbnds = []
            for hb in at.hbonds:
                if hb!=b:
                    okhbnds.append(hb)
            if len(okhbnds):
                at.hbonds = okhbnds
            else:
                delattr(at, 'hbonds')
        return 

from Pmv.deleteCommandsGUI  import DeleteCurrentSelectionGUI


class DeleteCurrentSelection(DeleteAtomSet):
    """ Command to remove an AtomSet from the MoleculeViewer
    \nPackage : Pmv
    \nModule  : deleteCommands
    \nClass   : DeleteCurrentSelection
    \nCommand : deleteCurrentSelection
    \nSynopsis:\n
        None<---deleteCurrentSelection(**kw)\n
    \nRequired Arguments:\n
        None
    """
    
    def __call__(self, *args, **kw):
        """None <- deleteCurrentSelection(atoms, **kw)
        \natoms: AtomSet to be deleted."""
        self.doitWrapper(**kw)




    def guiCallback(self, event=None):
        """called each time the 'Delete Selected Atoms' button is pressed"""
        z = self.vf.getSelection()
        if z:
            ats = z.findType(Atom)
##             if self.vf.userpref['Expand Node Log String']['value'] == 0:
##                 self.vf.deleteAtomSet.nodeLogString = "self.getSelection()"
        else:
            self.vf.warningMsg('no atoms selected')
            return 'ERROR'
        if ats:
            if self.vf.undoCmdStack == []:
                self.doitWrapper(ats, redraw=0)
            else:
                text = """WARNING: This command cannot be undone.
                if you choose to continue the undo list will be reset.
                Do you want to continue?""" 

                idf = self.idf = InputFormDescr(title="WARNING")
                idf.append({'widgetType':Tkinter.Label,
                            'wcfg':{'text':text},
                            'gridcfg':{'columnspan':2,'sticky':'w'}})

                idf.append({'name': 'continueBut',
                            'widgetType':Tkinter.Button,
                            'wcfg':{'text':'CONTINUE',
                                    'command':self.continue_cb},
                            'gridcfg':{'sticky':'we'}})

                idf.append({'name': 'cancelBut',
                            'widgetType':Tkinter.Button,
                            'wcfg':{'text':'CANCEL', 'command':self.cancel_cb},
                            'gridcfg':{'row':-1,'sticky':'we'}})

                self.form = self.vf.getUserInput(idf, modal = 0, blocking = 0)
                self.form.root.protocol('WM_DELETE_WINDOW',self.cancel_cb)



    def continue_cb(self):
        self.vf.resetUndo(topCommand=0)
        self.doitWrapper()
        #self.doitWrapper(ats, log=0)
        self.form.destroy()


    def cancel_cb(self):
        self.idf.form.destroy()
        

    def doit(self):
        """ Function to delete all the references to each atom of a
        the currentSelection."""

        atoms = old = self.vf.getSelection()[:] # make copy of selection
        ats = self.vf.expandNodes(atoms)
        if not len(ats):
            return
        ats = ats.findType(Atom)

        self.vf.clearSelection(log=0)
        self.vf.deleteAtomSet(ats, redraw=True, log=0)


class DeleteHydrogens(DeleteAtomSet):
    """ Command to remove hydrogen atoms from the MoleculeViewer
    \nPackage : Pmv
    \nModule  : deleteCommands
    \nClass   : DeleteHydrogens
    \nCommand : deleteHydrogens
    \nSynopsis:\n
        None<---deleteAtomSet(atoms, **kw)\n
    \nRequired Arguments:\n 
        atoms --- AtomSet to be deleted.\n
    """
    def guiCallback(self):
        """called each time the 'Delete Selected Atoms' button is pressed"""
        z = self.vf.getSelection()
        hats = None
        if z:
            ats = z.findType(Atom)
            if ats:
                hats = ats.get(lambda x: x.element=='H')
        else:
            self.vf.warningMsg('no atoms selected')
            return 'ERROR'
        if hats is None:
            self.vf.warningMsg('no hydrogens selected')
            return 'ERROR'

        #only get to this point if hats
        if self.vf.undoCmdStack == []:
            self.doitWrapper(hats, redraw=0)
        else:
            text = """WARNING: This command cannot be undone.
            if you choose to continue the undo list will be reset.
            Do you want to continue?""" 

            idf = self.idf = InputFormDescr(title="WARNING")
            idf.append({'widgetType':Tkinter.Label,
                        'wcfg':{'text':text},
                        'gridcfg':{'columnspan':2,'sticky':'w'}})

            idf.append({'name': 'continueBut',
                        'widgetType':Tkinter.Button,
                        'wcfg':{'text':'CONTINUE',
                                'command':CallBackFunction(self.continue_cb,
                                                           hats)},
                        'gridcfg':{'sticky':'we'}})

            idf.append({'name': 'cancelBut',
                        'widgetType':Tkinter.Button,
                        'wcfg':{'text':'CANCEL', 'command':self.cancel_cb},
                        'gridcfg':{'row':-1,'sticky':'we'}})

            self.form = self.vf.getUserInput(idf, modal = 0, blocking = 0)
            self.form.root.protocol('WM_DELETE_WINDOW',self.cancel_cb)


    def continue_cb(self, hats):
        self.vf.resetUndo(topCommand=0)
        self.doitWrapper(hats, redraw=0)
        if hasattr(self, 'idf') and hasattr(self.idf, 'form'):
            self.idf.form.destroy()

    def cancel_cb(self):
        self.idf.form.destroy()
        

    def __call__(self, atoms, **kw):
        """None <- deleteAtomSet(atoms, **kw)
        \natoms: AtomSet to be deleted."""
        if type(atoms) is types.StringType:
            self.nodeLogString = "'"+atoms+"'"
        
        ats = self.vf.expandNodes(atoms)
        if not len(ats):
            return 'ERROR'
        hats = ats.get(lambda x: x.element=='H')
        if not len(hats):
            return 'ERROR'
        ats = hats
        #WHY???
        #kw['log'] = 0
        apply(self.doitWrapper, (ats,), kw)

from Pmv.deleteCommandsGUI  import DeleteHydrogensGUI

commandList = [
    {'name':'deleteMol','cmd': DeleteMolecule(),'gui': DeleteMoleculeGUI},
    {'name':'deleteAllMolecules','cmd': DeleteAllMolecules(),'gui': DeleteAllMoleculesGUI},
#    {'name':'deleteAtomSet','cmd': DeleteAtomSet(),'gui': DeleteAtomSetGUI},
        {'name':'deleteAtomSet','cmd': DeleteAtomSet(),'gui': None },
    {'name':'deleteCurrentSelection','cmd': DeleteCurrentSelection(),
     'gui': DeleteCurrentSelectionGUI },
    {'name':'deleteHydrogens','cmd': DeleteHydrogens(),'gui': DeleteHydrogensGUI}
    ]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
