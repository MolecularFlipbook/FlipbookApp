## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Sophie I. COON, William LINDSTROM, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/superImposeCommands.py,v 1.24.4.1 2010/12/30 21:56:18 rhuey Exp $
#
# $Id: superImposeCommands.py,v 1.24.4.1 2010/12/30 21:56:18 rhuey Exp $
#

import numpy.oldnumeric as Numeric, os
import Tkinter, Pmw

from Pmv.stringSelectorGUI import StringSelectorGUI
from Pmv.mvCommand import MVCommand, MVAtomICOM
from Pmv.guiTools import MoleculeChooser

from ViewerFramework.VFCommand import CommandGUI

from MolKit.molecule import Molecule, Atom, AtomSet
from MolKit.protein import Protein, Residue, Chain, ProteinSet, ResidueSet, ChainSet

from DejaVu.Spheres import Spheres
from DejaVu.IndexedPolylines import IndexedPolylines

from mglutil.alignmentEditor import *
from mglutil.gui.InputForm.Tk.gui import InputFormDescr, InputForm
from mglutil.util.callback import CallBackFunction
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser
#from mglutil.math import rigidFit
from mglutil.math.rigidFit import RigidfitBodyAligner

from SimpleDialog import SimpleDialog

class PmvAlignmentEditor(AlignmentEditor,MVCommand):
    """ An alignment editor that knows about Pmv
    """
    
    def __init__(self,alignment=None,vf=None,name=None,**kw):
        MVCommand.__init__(self)
        self.vf = vf
        AlignmentEditor.__init__(self,alignment=alignment,master=vf.GUI.ROOT,
                                 name=name)
        self.addPmvMenu()
        
    def addPmvMenu(self):
        if isinstance(self.mBar, Pmw.ScrolledFrame):
            PmvButton = Tkinter.Menubutton(self.mBar.interior(),
                                           text='Pmv commands',
                                           underline=0)
        else:
            PmvButton = Tkinter.Menubutton(self.mBar, text='Pmv commands',
                                           underline=0)
            
        self.menuButtons['Pmv commands']=PmvButton
        PmvButton.pack(side=Tkinter.LEFT, padx='1m')
        PmvButton.menu = Tkinter.Menu(PmvButton)
        PmvButton.menu.add_command(
            label='Get/Assign Molecule Sequence',
            command = self.getSequence)
        PmvButton.menu.add_command(
            label='Set reference sequence',
            command = self.setRefSequence)
        PmvButton.menu.add_command(
            label='Set mobile sequence',
            command = self.setMobSequence)
        PmvButton.menu.add_command(
            label='Calculate Superposition',
            command = self.getPairsFromAlignment)
        PmvButton['menu']=PmvButton.menu
        apply(self.mBar.tk_menuBar, self.menuButtons.values())

    def setRefSequence(self):
        molName = MoleculeChooser(self.vf).go().name
        self.vf.alnEditor.master.lift()
        if molName not in self.vf.alignment.seqNames:
            return
        #recolor the previous reference sequence, if it exists
        if hasattr(self,'refMolName'):
            uniqtag = self.refMolName+'_name'
            item = self.vf.alnEditor.canvas.find_withtag(uniqtag)
            color = self.vf.alnEditor.colors['default']
            self.vf.alnEditor.canvas.itemconfig(item,fill=color)
        uniqtag = molName+'_name'
        self.vf.alnEditor.colors['special'][uniqtag]='red'
        item = self.vf.alnEditor.canvas.find_withtag(uniqtag)
        self.vf.alnEditor.canvas.itemconfig(item,fill='red')
        self.refMolName = molName
        
    def setMobSequence(self):
        molName = MoleculeChooser(self.vf).go().name
        self.vf.alnEditor.master.lift()
        if molName not in self.vf.alignment.seqNames:
            return
        #recolor the previous reference sequence, if it exists
        if hasattr(self,'mobMolName'):
            uniqtag = self.mobMolName+'_name'
            item = self.vf.alnEditor.canvas.find_withtag(uniqtag)
            color = self.vf.alnEditor.colors['default']
            self.vf.alnEditor.canvas.itemconfig(item,fill=color)
        uniqtag = molName+'_name'
        self.vf.alnEditor.colors['special'][uniqtag]='green'
        item = self.vf.alnEditor.canvas.find_withtag(uniqtag)
        self.vf.alnEditor.canvas.itemconfig(item,fill='green')
        self.mobMolName = molName
        
    def getPairsFromAlignment(self):
        """ This is where we want to figure out the selection
        """
        refCount=0
        mobCount=0
        refResidues = self.vf.expandNodes(self.refMolName)[0].children.children
        mobResidues = self.vf.expandNodes(self.mobMolName)[0].children.children
        refNodes = ResidueSet()
        mobNodes = ResidueSet()
        #get the item no's for each sequence
        refItems = self.vf.alnEditor.canvas.find_withtag(self.refMolName)
        mobItems = self.vf.alnEditor.canvas.find_withtag(self.mobMolName)
        for x in range(len(refItems)):
            ref = self.vf.alnEditor.canvas.itemcget(refItems[x],'text')
            mob = self.vf.alnEditor.canvas.itemcget(mobItems[x],'text')
            if ref.isalpha():
                refRes = refResidues[refCount]
                refCount=refCount+1
            if mob.isalpha():
                mobRes = mobResidues[mobCount]
                mobCount=mobCount+1
            refTags = self.vf.alnEditor.canvas.gettags(refItems[x])
            mobTags = self.vf.alnEditor.canvas.gettags(mobItems[x])
            if 'selected' in mobTags and 'selected' in refTags:
                if ref.isalpha() and mob.isalpha():
                    refNodes.append(refRes)
                    mobNodes.append(mobRes)
        print len(refNodes),len(mobNodes),refNodes[0],mobNodes[0]
        #return refNodes,mobNodes
        apply(self.vf.superimposeAtomsGC.doitWrapper, (refNodes,), {'log':0})
        apply(self.vf.superimposeAtomsGC.doitWrapper, (mobNodes,), {'log':0})
        self.vf.superimposeAtomsGC.typeVar.set('By Picking')
        
    def getSequence(self,mol=None):
        if not mol:
            mol = MoleculeChooser(self.vf).go()
            if not mol:
                return
        self.vf.alnEditor.master.lift()
        #for extracting sequence(s) from molecules
        chains = mol.children
        seqList = []
        numbers = []
        for chain in chains:
            seqList = seqList+chain.children.type+['-','|','-']
            for residue in chain.children:
                numbers.append(chain.name + residue.type + residue.number)
        molSequence = Sequence(sequence=seqList,numbers=numbers,name=mol.name)
        seqName = mol.name
        if seqName in self.vf.alignment.seqNames:
            # if sequence with this molecule name is already in the alignment,
            # only need to update the numbers
            sequence = self.vf.alignment.sequences[seqName]
            sequence.applyNumbers(numbers)
            return
        self.vf.alignment.addSequence(molSequence)
        self.vf.alnEditor.redraw()

    def select(self,items,deselect=0):
        icomLevel = self.vf.ICOMbar.LevelOption._menubutton.config()['text'][-1]
        if icomLevel == 'Atom':
            msg = "The selection level is currently ATOM. Continuing will\nchange it to RESIDUE"
            d = SimpleDialog(self.vf.GUI.ROOT,text=msg,
                             buttons = ["Abort","Continue"],
                             title = "Warning",
                             default=1)
            if not d.go():
                return
        AlignmentEditor.select(self,items,deselect)
        lastSelect = self.lastSelect #just been updated by previous line
        negate=lastSelect[0]
        selStrings={}
        for item in lastSelect[1]:
            resTag,seqTag,uniqTag = self.canvas.gettags(item)[:3]
            # if the item is part of a sequence linked to a molecule,
            # the selection can be applied to Pmv. Since the resTag in this case
            # is the unique object identifier for the residue, this is easy
            if seqTag in self.vf.Mols.name:
                molName = seqTag
                selectionKey = molName+':'+resTag[:1]+':'
                resnum = resTag[1:]
                if selectionKey in selStrings.keys():
                    selStrings[selectionKey]=selStrings[selectionKey]+','+resnum
                else:
                    selStrings[selectionKey]=','+resnum
        for selStr in selStrings.keys():
            print selStr+selStrings[selStr]
            self.vf.select(selStr+selStrings[selStr],negate)
                
class SuperImposeAtomsCommand(MVCommand):

    def onAddCmdToViewer(self):
        self.rigidfitAligner = RigidfitBodyAligner()
        
    def doit(self, refAtoms, mobAtoms):
        """
        The SuperImposeAtomsCommand takes two set of Atoms of the same length
        compute the rotation and translation matrices to superimpose the
        mobAtoms onto the refAtoms using rigidFit module and then transform the
        corresponding geometry.
        """
        refCoords = refAtoms.coords
        mobCoords = mobAtoms.coords
        
        self.rigidfitAligner.setRefCoords(refCoords)

        # Nothing can be done if the two sets of coords are not of the same
        # size
        if not len(refCoords) == len(mobCoords):
            print " ERROR: Cannot perform the superimposition because the 2 \
            mv.lsets of Atoms are not of the same length"
            return

        # Get the rotation and the translation ysing mglutil.math.rigidFit
        self.rigidfitAligner.rigidFit(mobCoords)
        #rotation, translation= rigidFit.rigid_fit( refCoords, inCoords)
        rotMat =  Numeric.identity(4).astype('f')
        rotMat[:3,:3] = self.rigidfitAligner.rotationMatrix
        rotMat = Numeric.reshape(rotMat, (16,))
        transMat = Numeric.array(self.rigidfitAligner.translationMatrix)
        
        # transform the geometry representing the atoms only if a gui has been
        # created:
        #if not self.vf.hasGui:
        #    return

        # Transform the mob geometry
        mobMol = mobAtoms.top.uniq()[0]
        mob = mobMol.geomContainer.masterGeom
        self.vf.transformObject('rotation', mob.fullName, matrix=tuple(rotMat))
        self.vf.transformObject('translation', mob.fullName, matrix=tuple(transMat))
        

    def __call__(self, refAtoms, mobAtoms, **kw):
        """
        None <- superimposeAtoms(refAtoms, mobAtoms, **kw)
        """
        if not kw.has_key('redraw'): kw['redraw'] = 1
        apply(self.doitWrapper, (refAtoms, mobAtoms), kw)
        

class SuperImposeAtomsGUICommand(MVCommand, MVAtomICOM):
    """
    The SuperImposeAtomsGUICommand provides a GUI interface to the  SuperImposeAtomsCommand.
    - For now Only two 2 sets of Atoms belonging to a ref molecule and a mobile molecule
    can be superimposed simultaneously.

    - The command provides two way of defining those two sets of atoms:
    
      * By picking nodes at the different levels (Molecule, Chain, Residue, Atom) the first pick
      will define the reference set and the second the mobile set. The picking process will have
      be done later on the same way and defines a list of pairs of atoms.
      If the user drags a box only the first node will be considered. Nodes are then converted into
      an set of Atoms. The 'Edit Atoms Pairs' allows the user to see the pairs but also to alter those
      sets. For example only the backbone atoms can be considered or all atoms etc. The user can also
      create his own filter by typing a lambda function in the entry of the combobox.
      If the 2 sets are not of the same length the extra atoms can be removed either from the beginning,
      the end or half and half of the longest set allowing a bit more flexibility.
      If the resulting 2 sets are None then the superimposition cannot be computed. You can reset the
      process and start over or alter your set using the tools described above.

      * By string: If the user knows the set of nodes of respectively the reference molecule and mobile
      molecule to be use for the computation two string selector widgets allows him to proceed more
      efficiently.

    - Known bug:
      * If the reference molecule is transformed independently of the mobile molecule the mobile
      molecule will be superimposed onto the original location of the reference molecule. (Working on it)
      * Cannot superimpose simultaneously multiple sets of molecule.
      * And probably many more ....
    """
    
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        MVAtomICOM.__init__(self)
        self.refAtomList = []
        self.inAtomList = []
        #self.superImposedPairs = {}
        self.newPairs = {}
        self.pair = []
        self.mobMolName = None
        self.refMolName = None
        self.filters = {'CA Atoms':lambda x: x.name == 'CA',
                        'Backbone Atoms': lambda x: x.name in ['CA', 'C',
                                                               'N', 'O',
                                                               'CA@A','C@A',
                                                               'N@A','O@A'],
                        'Heavy Atoms': lambda x: not x.element == 'H',
                        'All Atoms': None}
        self.defaultFilter = 'Backbone Atoms'


    def onAddCmdToViewer(self):
        # Check first is any of the command that superimpose depends on are
        # already loaded.
        if not self.vf.commands.has_key('setICOM'):
            self.vf.loadCommand('interactiveCommands', 'setICOM', 'Pmv',
                                topCommand = 0)
        if not self.vf.commands.has_key('superimposeAtoms'):
            self.vf.loadCommand('superImposeCommands', 'superimposeAtoms',
                                'Pmv', topCommand = 0)
            
        if not self.vf.commands.has_key('startContinuousPicking'):
            self.vf.loadCommand('dejaVuCommands','startContinuousPicking',
                                'ViewerFramework', topCommand = 0)

        if not self.vf.commands.has_key('stopContinuousPicking'):
            self.vf.loadCommand('dejaVuCommands','stopContinuousPicking',
                                'ViewerFramework', topCommand = 0)
        if not self.vf.commands.has_key('labelByExpression'):
            self.vf.loadCommand('labelCommands', 'labelByExpression', 'Pmv',
                                topCommand = 0)

        self.sphere1 = Spheres(name='elt1', radii=0.5,
                               materials = ( (0.,1.,0.),), protected=True)
        self.sphere2 = Spheres(name = 'elt2', radii=0.5, 
                               materials = ( (1.,1.,0.),), protected=True)

        #self.form = None

    def onRemoveObjectFromViewer(self,obj):
        if hasattr(self.vf,'alignment'):
            self.vf.alnEditor.deleteSequence(obj.name)
            self.vf.alnEditor.redraw()
        if obj.name == self.refMolName:
            self.refMolName=None
        if obj.name == self.mobMolName:
            self.mobMolName=None
            
    def guiCallback(self):
        self.vf.setICOM(self, modifier="Shift_L",  topCommand=0)

    def buildFormDescr(self, formName):
        if formName == 'superimpose':
            idf = InputFormDescr(title="Set Superimposition Parameters")

            idf.append( {'widgetType':Tkinter.Label,
                         'wcfg': {'text':'Get Nodes:'},
                         'gridcfg':{'sticky':'w'}})

            self.typeVar = Tkinter.StringVar()
            self.typeVar.set('By Picking')

            idf.append( {'widgetType':Tkinter.Radiobutton,
                         'name': 'string',
                         'wcfg':{'variable':self.typeVar,
                                 'text': 'From String',
                                 'value':'From String',
                                 'command':self.string_cb,
                                 },
                         'gridcfg':{'sticky':'w', 'columnspan':3}})

            idf.append( {'widgetType':Tkinter.Radiobutton,
                         'name': 'string',
                         'wcfg':{'variable':self.typeVar,
                                 'text': 'From Alignment',
                                 'value':'From Alignment',
                                 'command':self.alignment_cb,
                                 },
                         'gridcfg':{'sticky':'w', 'columnspan':3}})

            idf.append( {'widgetType':Tkinter.Radiobutton,
                         'name': 'refPicking',
                         'wcfg':{'variable':self.typeVar,
                                 'text': 'By Picking',
                                 'value':'By Picking',
                                 },
                         'gridcfg':{'sticky':'w'} })

            idf.append( {'widgetType':Tkinter.Label,
                         'wcfg': {'text':'Reference nodes:'},
                         'gridcfg':{'sticky':'w'}})

            idf.append( {'widgetType':Tkinter.Label,
                         'wcfg': {'text':'Mobile nodes:'},
                         'gridcfg':{'sticky':'e', 'row':-1}})


            idf.append({'widgetType':Tkinter.Label,
                        'name':'firstNode',
                        'wcfg':{ 'text':''},
                        'gridcfg':{'sticky':'we'}})

            idf.append({'widgetType': Tkinter.Label,
                        'name':'secondNode',
                        'wcfg':{ 'text':''},
                        'gridcfg':{'sticky':'we', 'row':-1}})

            idf.append({'widgetType':Tkinter.Button,
                        'name':'editPairs',
                        'wcfg':{'text':'Edit Ref Atom -- Mob Atom Pairs',
                                'command':self.editPairs_cb,},
                        'gridcfg':{'sticky':'we','columnspan':3}
                        })

            # Continuous Superimposition
            idf.append({'widgetType':Tkinter.Checkbutton,
                        'name':'continuous',
                        'wcfg':{'variable':Tkinter.IntVar(),
                                'text':'Continuous Superimposition',
                                'command':self.continuous_cb,
                                'padx':10,'pady':10},
                        'gridcfg':{'sticky':'w'}})

            # Reset & SuperImpose button.
            idf.append({'widgetType':Tkinter.Button,
                        'name':'final',
                        'wcfg':{'width':15,'text':'Superimpose',
                                'command':self.superimpose_cb},
                        'gridcfg':{'sticky':'we', 'row':-1}})

            idf.append({'widgetType':Tkinter.Button,
                        'name':'reset',
                        'wcfg':{'text':'Reset', 'command':self.reset_cb},
                        'gridcfg':{'sticky':'we', 'row':-1}})

        elif formName == 'editPair':
            idf = InputFormDescr(title='Edit Reference Atom - Mobile Atom Pairs')
            idf.append({'widgetType':Pmw.ComboBox,
                        'name':'choice',
                        'defaultValue':self.defaultFilter,
                        'wcfg':
                        {'label_text':'Atoms to be consider for superimposition:',
                         'labelpos':'n','label_padx':10,'label_pady':10,
                         'scrolledlist_items': self.filters.keys(),
                         'selectioncommand':self.setDefault},
                        'gridcfg':{'sticky':'w'}})
        
            # If sets not of the same length:
            idf.append({'widgetType':Pmw.ComboBox,
                        'name':'slice',
                        'defaultValue':'Beginning',
                        'wcfg':
                        {'label_text':'Sets not of the same length',
                         'labelpos':'n','label_padx':10,'label_pady':10,
                         'scrolledlist_items':['Beginning',
                                               'End',
                                               'Half/Half']
                         },
                        'gridcfg':{'sticky':'w', 'row':-1}})
            
            entries = map(lambda x: (x, None), self.newPairs.keys())
            idf.append({'widgetType':ListChooser,
                        'name':'newpairs',
                        'wcfg':{'mode':'extended',
                                'entries':entries,
                                'lbwcfg':{'exportselection':1},
                                'title':'Reference Atoms    --    Mobile Atoms'},
                        'gridcfg':{'sticky':'wens', 'columnspan':2}})
            

            idf.append({'widgetType':Tkinter.Button,
                        'name': 'delete',
                        'wcfg':{'width':15,'text': 'Delete Pairs',
                                'command':self.delete_cb},
                        'gridcfg':{'sticky':'we', 'columnspan':2}})
            
            idf.append({'widgetType':Tkinter.Button,
                        'name': 'dismiss',
                        'wcfg':{'text': 'DISMISS',
                                'command':self.dismiss_cb},
                        'gridcfg':{'sticky':'we', 'columnspan':2}})


        elif formName == 'editString':
            idf = InputFormDescr(title = 'Get Nodes From String')
            idf.append({'widgetType':Tkinter.Label,
                        'wcfg':{'text':'Reference Nodes: '},
                        'gridcfg':{'sticky':'w'}})

            idf.append({'widgetType':Tkinter.Label,
                        'wcfg':{'text':'Mobile Nodes: '},
                        'gridcfg':{'sticky':'w', 'row':-1}})

            idf.append({'widgetType':Tkinter.Label,
                        'wcfg':{'text':' '},
                        'gridcfg':{'columnspan':2, 'sticky':'w'}})

            idf.append({ 'widgetType':StringSelectorGUI,
                         'name':'refNodes','required':1,
                         'wcfg':{ 'molSet': self.vf.Mols,
                                  'vf': self.vf,
                                  'all':1,
                                  'crColor':(1.,0.,0.),
                                  },
                         'gridcfg':{'sticky':'we' }})

            idf.append({ 'widgetType':StringSelectorGUI,
                         'name':'mobNodes','required':1,
                         'wcfg':{ 'molSet': self.vf.Mols,
                                  'vf': self.vf,
                                  'all':1,
                                  'crColor':(0.,0.,1.),
                                  },
                         'gridcfg':{'row':-1, 'sticky':'we' }})

        return idf
    
    def initICOM(self, modifier):
        # Create the form if not existing yet
        form = self.showForm(formName = 'superimpose', modal=0, blocking=0)
        self.firstLabel = form.descr.entryByName['firstNode']['widget']
        self.secondLabel = form.descr.entryByName['secondNode']['widget']

        self.contVar = form.descr.entryByName['continuous']['wcfg']['variable']
        self.pairForm = None

        # set the callback of continuousPicking to label the picked node
        # 1- get a handle on the cbManager
        cbManager  = self.vf.startContinuousPicking.cbManager
        # 2- Save the existing callbacks
        self.oldCallBacks = cbManager.callbacks
        # 3- Set to the new callback
        cbManager.SetCallback(CallBackFunction(self.labelByName))
        
        self.vf.startContinuousPicking()
        self.supcb = 0


    def setDefault(self, text):
        self.defaultFilter = text
        if hasattr(self, 'pair') and len(self.pair) == 2:
            filter = self.filters[text]
            set1 = self.pair[0]
            set2 = self.pair[1]
            
            if filter:
                set1 = set1.get(filter)
                set2 = set2.get(filter)
            if (set1 and set2) and (len(set1) == len(set2)):
                self.updateChooser(set1, set2)
            
    def editPairs_cb(self, event=None):
        pairForm = self.showForm('editPair', force = 1, modal=0, blocking=0,
                                 onDestroy= self.dismiss_cb)
        # show panel with the listchooser of the panel and 
        # Choose the atoms to do the superimposition
        
        self.chooser = pairForm.descr.entryByName['newpairs']['widget']

    def dismiss_cb(self, event=None):
        if self.cmdForms.has_key('editPair'):
            self.cmdForms['editPair'].destroy()
            del self.cmdForms['editPair']

    def string_cb(self, event=None):
        #get rid of the alignment GUI
        if hasattr(self.vf,'alnEditor'):
            self.vf.alnEditor.exit()
        val = self.showForm('editString')
        print val
        if not val == {} or (val.has_key('refNodes') and val.has_key('mobNodes')):
            apply(self.doitWrapper, (val['refNodes'],), {'log':0})
            apply(self.doitWrapper, (val['mobNodes'],), {'log':0})
            self.typeVar.set('By Picking')


    def continuous_cb(self, event=None):
        #get rid of the alignment GUI
        if hasattr(self.vf,'alnEditor'):
            self.vf.alnEditor.exit()
        form = self.cmdForms['superimpose']
        supButton = form.descr.entryByName['final']['widget']
        if self.contVar.get() == 1:
            supButton.configure(state=Tkinter.DISABLED)
            if len(self.newPairs)>=4:
                self.superimpose_cb()
        else:
            supButton.configure(state=Tkinter.NORMAL)


    def labelByName(self, pick):
        # Continuous labeling.
        if pick is None: return
        atom = self.vf.findPickedAtoms(pick)
        if atom:
            level = self.vf.ICmdCaller.level.value
            self.vf.ICmdCaller.level.AddCallback(self.unlabelLevel)
            if level == Molecule : level = Protein
            self.node = atom.findType(level)
            funcItems = map(lambda x: x.full_name(), self.node)
            self.vf.labelByExpression(self.node,
                                      font = 'arial1.glf',
                                      location = 'First', 
                                      textcolor = 'red', only = 1,
                                      lambdaFunc = 1,negate=0,
                                      function = 'lambda x: str(x.full_name())\n\n',
                                      topCommand=0,
                                      )
            
    def unlabelLevel(self, newLevel, oldLevel):
        if not hasattr(self, 'node'): return

        if oldLevel == Molecule: oldLevel = Protein
        # need to be at the former level for all the former picked stuff
        # so take it all.
        node = self.vf.getSelection()
        nodes = node.findType(oldLevel)
        # Careful in labelByProperty fix a bug if no label should not break! 
        self.vf.labelByExpression(nodes, negate=1, log=0)
        
    def stopICOM(self):
        # Destroy the inputForm
        self.cmdForms['superimpose'].root.destroy()
        # Set the form to None.
        del self.cmdForms['superimpose']

        # Set back the continuousPicking to unsolicitedPick
        cbManager  = self.vf.startContinuousPicking.cbManager
        if not len(self.oldCallBacks) == 0:
            cbManager.SetCallback(self.oldCallBacks[0])
            if len(self.oldCallBacks)>1:
                for cb in self.oldCallBacks[1:]:
                    cbManager.AddCallBack(cb)

        # Remove the unlabel callback bound to the self.vf.ICmdCaller.level
        if self.unlabelLevel in  self.vf.ICmdCaller.level.callbacks:
            self.vf.ICmdCaller.level.RemoveCallback(self.unlabelLevel)

        # Unlabel whatever is labeled
        level = self.vf.ICmdCaller.level.value
        
        nodes = self.vf.getSelection().findType(level)
        if not nodes is None or len(nodes)!=0:
            self.vf.labelByExpression(nodes, negate=1, log=0)

        # Stop the continuous picking.
        self.vf.stopContinuousPicking()

        self.sphere1.Set(vertices=[], tagModified=False)
        self.sphere2.Set(vertices=[], tagModified=False)
##         self.visualFeedBack(vertices =[])


    def updateChooser(self, set1, set2):
        for elt1, elt2 in map(None, set1, set2):
            key = elt1.full_name() + '--' + elt2.full_name()
            self.newPairs[key] = (elt1, elt2)
            if not self.pairForm is None:
                entry = (key, None)
                self.chooser.add(entry)
        
    
    def reset_cb(self, event=None):
        """Button to reset the superimposition and the list of pairs."""
        # Reset the chooser and the lists of pairs
        if self.newPairs == {}: return 
        if not self.pairForm is None:
            self.chooser.clear()
        self.newPairs = {}
        # Reset the geometry.
        vi = self.vf.GUI.VIEWER
        geom = self.mobileMol.geomContainer.masterGeom
        oldCurrent = vi.currentObject
        vi.SetCurrentObject(geom)
        # transform only the given geometry.
        if vi.redirectTransformToRoot == 1:
            old = vi.redirectTransformToRoot
            vi.TransformRootOnly(0)
        else:
            old = 0
        # Right now reset all the transformations applied to the mobile object.
        # Maybe should separate from the superimposition and only reset these.
        vi.ResetCurrentObject()
        # Put everything back like it was before.
        if old == 1:
            vi.TransformRootOnly(1)
        vi.SetCurrentObject(oldCurrent)
        
        self.sphere1.Set(vertices=[], tagModified=False)
        self.sphere2.Set(vertices=[], tagModified=False)
        self.firstLabel.configure(text='')
        self.secondLabel.configure(text='')
        
##         self.visualFeedBack.Set(vertices=[], tagModified=False)

        
    def delete_cb(self, event = None):
        # Delete the selected pair from the listchooser and from the pairlist
        selectedNewPairs = self.chooser.get()
        # Undisplay the label (Maybe only if the last pair is being deleted )
        self.firstLabel.configure(text='')
        self.secondLabel.configure(text='')
        for pair in selectedNewPairs:
            if len(self.chooser.entries) >=4:
                self.chooser.remove(pair)
                del self.newPairs[pair]
                if self.contVar.get()==1 or self.supcb==1:
                    self.superimpose_cb()

    def superimpose_cb(self, event=None):
        if len(self.newPairs) >= 4 :
            # Need at least 4 pairs of atoms to do the superimposition
            setAtm1 = AtomSet(map(lambda x: x[0],
                                  self.newPairs.values()))
            setAtm2 = AtomSet(map(lambda x: x[1],
                                  self.newPairs.values()))
            if len(setAtm1) != len(setAtm2):
                message = ' ERROR: the 2 sets of atoms are not of the length\nthe superimposition cannot be performed. ' 
                self.warningMsg(msg)
                return

            self.vf.superimposeAtoms(setAtm1, setAtm2)
            self.supcb = 1
##             self.visualFeedBack.Set(vertices=self.visualVertices,
##                                     tagModified=False)

    def __call__(self, atoms, **kw):
        ats = self.vf.expandNodes(atoms)
        if not len(ats): return 'ERROR'
        kw['redraw']=1
        kw['log']=0
        return apply(self.doitWrapper, (ats,), kw)
        

    def doit(self, nodes):
        """
        Create the 2 sets of atom that will be used to do the superimposition.
        Then call the superImposeCommand with these 2 sets.
        If continuous is on then the superimposition will be updated each time
        a pair of atoms is added otherwise the superimposition will be updated
        every 4 pairs of atoms.
        """

        # Get the ICOM level
        icomLevel = self.vf.ICmdCaller.level.value
        # Not doing anything if no nodes picked:
        if not nodes: return

        if self.typeVar.get() == 'By Picking':
            # only take the first node picked.
            node = nodes[0]
            nodeMol = node.top

        elif self.typeVar.get() == 'From String':
            node = nodes
            molecules = nodes.top.uniq()
            if len(molecules)>1:
                # nodes need to belong to only one molecule
                return
            else: nodeMol = molecules[0]
        
        elif self.typeVar.get() == 'From Alignment':
            node = nodes
            molecules = nodes.top.uniq()
            if len(molecules)>1:
                # nodes need to belong to only one molecule
                return
            else: nodeMol = molecules[0]
        
        # 2- Get the atoms from the chosen nodes
        atms = node.findType(Atom)

        # First set of nodes == defines the first set of 1st elt in the pairs
        if len(self.pair) == 0 :
            self.secondLabel.configure(text ='')
            # Defines reference molecule:
            if self.newPairs == {}:
                self.refMol = nodeMol
                # Draw the feedBack sphere.
                mGeom = self.refMol.geomContainer.masterGeom
                self.vf.GUI.VIEWER.AddObject(self.sphere1, parent = mGeom)

            if nodeMol != self.refMol:
                self.firstLabel.configure(text ='')
                # if the node belongs to the another molecule return.
                # The pairs are defined allways in the same order.
                return

            self.pair.append(atms)
            #self.pair.append(node)
            if self.typeVar.get() == 'By Picking':
                self.firstLabel.configure(text=node.full_name())

        elif len(self.pair) == 1 :
            # Creates Second set of elt in the pair.
            if self.newPairs=={}:
                if nodeMol != self.refMol:
                    # set the mobile molecule and finish the first pair
                    self.mobileMol = nodeMol
                    mGeom = self.mobileMol.geomContainer.masterGeom
                    self.vf.GUI.VIEWER.AddObject(self.sphere2,
                                                 parent = mGeom)

            if nodeMol != self.mobileMol:
                return
            self.pair.append(atms)
            #self.pair.append(node)
            if self.typeVar.get() == 'By Picking':
                self.secondLabel.configure(text=node.full_name())

            # Now we have the two set of elts to create pairs:
            # 1- Check if the 2 sets have the same length:
            set1 = self.pair[0]
            set1.sort()
            set2 = self.pair[1]
            set2.sort()
            if not set1 or not set2:
                print "ERROR: One of the sets is None"
                return
            elif len(set1) != len(set2):
                if node.__class__ == Atom:
                    print 'ERROR: the 2 sets of atoms are not of the same size'
                    return

            set1,set2
            if node.__class__ in [Protein,ProteinSet, Residue, ResidueSet,  Chain, ChainSet]:
                filter = self.defaultFilter
                if self.filters.has_key(filter):
                    set1 = self.pair[0].get(self.filters[filter])
                    set2 = self.pair[1].get(self.filters[filter])
                if not set1 or not set2:
                    print 'ERROR: cannot compute the superimposition'
                    print 'not set1 or not set2'
                    return
                
                elif len(set1) != len(set2):
                    print 'ERROR: cannot compute the superimposition'
                    print 'len(set1) != len(set2)'
                    return

            #print 'set1', set1
            #print 'set2', set2
            self.updateChooser(set1, set2)
            self.pair = []

        if len(self.newPairs)>=4 and self.contVar.get() == 1:
            # Continuous picking is on and superimposition can be done if
            # there are more than 4 pairs.
            self.superimpose_cb()
            
    def alignment_cb(self, event=None):
        if not hasattr(self.vf,'alignment'):
            self.vf.alignment = Alignment()
        if not hasattr(self.vf,'alnEditor'):
            self.vf.alnEditor = PmvAlignmentEditor(vf=self.vf)
            self.vf.alnEditor.alignment = self.vf.alignment
        else:
            self.vf.alnEditor.redraw()
            self.vf.alnEditor.master.deiconify()
        for mol in self.vf.Mols:
            if mol.name not in self.vf.alignment.seqNames:
                self.vf.alnEditor.getSequence(mol)

       
SuperImposeAtomsGUICommandGUI = CommandGUI()
SuperImposeAtomsGUICommandGUI.addMenuCommand('menuRoot', 'Compute',
                                             'superimposeAtoms',

                                             cascadeName = "Superimpose")
    
    

class SuperimposeCoordsCommand(MVCommand):
    
    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('superimposeAtoms'):
            self.vf.loadCommand('superImposeCommands', 'superimposeAtoms',
                                'Pmv', topCommand = 0)
            

    def doit(self, refAtoms, inAtoms, inAllAtoms = None):
        """
        The SuperimposeCoordsCommand takes two set of Atoms of the same length
        refAtoms and inAtoms, a subset of inAllAtoms,
        plus an optional third set, inAllAtoms,
        It computes the rotation and translation matrices to superimpose the
        inAtoms onto the refAtoms using rigidFit module. Then transforms the
        coords of inAllAtoms.
        """
        # superimpose the inAtoms set onto the refAtoms set.
        self.vf.superimposeAtoms(refAtoms, inAtoms)
        if not inAllAtoms:
            inAllAtoms = inAtoms
        # then calls the self.vf.superimposeAtoms.rigidfitAligner
        # transformCoords method.
        ra = self.vf.superimposeAtoms.rigidfitAligner
        newcoords = ra.transformCoords(inAllAtoms.coords)
        if not newcoords is None and  newcoords.shape[1]!=3:
            newcoords=newcoords[:,:3]
        
##         refCoords = refAtoms.coords
##         inCoords = inAtoms.coords
##         #there could be other atoms which are not being used as reference pts
##         if not inAllAtoms:
##             inAllAtoms = inAtoms

##         # Nothing can be done if the two sets of coords are not of the same
##         # size
##         if not len(refCoords) == len(inCoords):
##             print " ERROR: Cannot perform the superimposition because the 2 \
##             mv.lsets of Atoms are not of the same length"
##             return

##         # Get the rotation and the translation from mglutil.math.rigidFit
##         rotation, translation = rigidFit.rigid_fit( refCoords, inCoords)
               
##         transMat = Numeric.array(translation)
##         refCoords = Numeric.array(refAtoms.coords)

##         inAllCoords = Numeric.array(inAllAtoms.coords)
        
##         # transform the coords 

##         # apply the rotation to the inAtoms.coords
##         newcoords = Numeric.dot(inAllCoords , rotation)

##         # apply the translation to inAtoms.coords
##         newcoords = newcoords + transMat

        #add the new conformation to atomSet._coords
        inAllAtoms.addConformation(newcoords)

        #set conformation of in Atoms to the new conformation
        confNum = len(inAllAtoms[0]._coords)-1
        inAllAtoms.setConformation(confNum)


    def __call__(self, refAtoms, inAtoms, inAllAtoms=None,  **kw):
        """
        None <- superimposeCoords(refAtoms, inAtoms, inAllAtoms, **kw)
        refAtoms: atoms in reference structure
        inAtoms: corresponding atoms in structure to be moved 
            by rigidFit to refAtoms
        inAllAtoms: complete set of all atoms whose coords are to be
            transformed bytranslation and rotation matrices from rigidFit.
            (Possibly inAtoms will contain all atoms in molecule to be 
            moved so inAllAtoms will be None.)
        """
        if not kw.has_key('redraw'): kw['redraw'] = 0
        apply(self.doitWrapper, (refAtoms, inAtoms, inAllAtoms), kw)
        

commandList = [
    {'name':'superimposeAtoms', 'cmd':SuperImposeAtomsCommand(),
     'gui':None},
##     {'name':'superimposeAtomsGC', 'cmd':SuperImposeAtomsGUICommand(),
##      'gui':SuperImposeAtomsGUICommandGUI},
    {'name':'superimposeCoords', 'cmd':SuperimposeCoordsCommand(),
     'gui':None}]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])


