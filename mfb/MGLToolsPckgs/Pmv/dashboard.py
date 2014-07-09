from mglutil.gui.BasicWidgets.Tk.trees.TreeWithButtons import \
     ColumnDescriptor ,TreeWithButtons, NodeWithButtons
from MolKit.molecule import MolecularSystem
import Pmw, Tkinter, os

from MolKit.stringSelector import CompoundStringSelector
from MolKit.molecule import MoleculeSet
from mglutil.util.packageFilePath import getResourceFolderWithVersion

from mglutil.util.callback import CallbackFunction

from Pmv.moleculeViewer import ICONPATH as iconPath
from Pmv.selectionCommands import MVSelectCommand

class MolFragTreeWithButtons(TreeWithButtons):
    """Each node in the tree has an object associated in the node's .object
attribute.  The objects are expected to have a .parent and a .children
attribute describing the hierarchy."""

    def __init__(self, master, root, vf=None, iconsManager=None,
                 idleRedraw=True, nodeHeight=18, **kw):
        # add a compound selector entry
        self.vf = vf
        kw['iconsManager'] = iconsManager
        kw['idleRedraw'] = idleRedraw
        kw['nodeHeight'] = nodeHeight
        TreeWithButtons.__init__( *(self, master, root), **kw )

        # add backbone only widget
        self.bbmodevar = Tkinter.StringVar()
        self.bbmodevar.set("CMD")

        canvas = self.canvas

        ##
        ## create buttons at the top fo the dashboard
        ##

        ##
        ## add a button to save selection as a set
        filename = os.path.join(iconPath, 'AddToDashboard.gif')
        self.addSelIcon = ImageTk.PhotoImage(file=filename)
        width = self.addSelIcon.width()
        height = self.addSelIcon.height()
        x = width + 2
        self.addSelButton = canvas.create_image(
            width/2.0, height/2.0, image=self.addSelIcon,
            tags=('dashButtons',))
        canvas.tag_bind(self.addSelButton, '<ButtonRelease-1>', self.addSel_cb)

        from Pmv.dashboardCommands import addSetToDashboardmsg
        self.balloon.tagbind(canvas, self.addSelButton, addSetToDashboardmsg)

        ##
        ## add a button to clear the current selection
        def clearSel(event=None):
            self.vf.clearSelection()
            
        filename = os.path.join(iconPath, 'eraser.gif')
        self.clearSelectionIcon = ImageTk.PhotoImage(file=filename)
        width = self.clearSelectionIcon.width()
        height = self.clearSelectionIcon.height()
        self.clearSelectionButton = canvas.create_image(
            x + width/2.0, height/2.0, image=self.clearSelectionIcon,
            tags=('dashButtons',))
        x += width + 2
        canvas.tag_bind(self.clearSelectionButton, '<ButtonRelease-1>',
                        clearSel)

        from Pmv.dashboardCommands import addSetToDashboardmsg
        self.balloon.tagbind(canvas, self.clearSelectionButton,
                             "Clear current selection")

        ##
        ## add a button to set dashboard natural size
        filename = os.path.join(iconPath, 'autosizeY.gif')
        self.autoWidthIcon = ImageTk.PhotoImage(file=filename)
        width = self.autoWidthIcon.width()
        height = self.autoWidthIcon.height()
        self.autoSizeButton = canvas.create_image(
            x + width/2.0, height/2.0, image=self.autoWidthIcon,
            tags=('dashButtons',))
        x += width + 2
        canvas.tag_bind(self.autoSizeButton, '<ButtonRelease-1>', 
                        self.vf.dashboard.setNaturalSize)
        naturalSizeballoon = "Sets the dashboard width to show all columns"
        self.balloon.tagbind(canvas, self.autoSizeButton,
                             naturalSizeballoon)

        ##
        ## add a button to increase column width
        id_  = self.sizeUpButton = canvas.create_text(
            x+12, height/2.0, justify='center', text="Z", font='Arial 20',
            tags=('dashButtons',))
        x += 14
        canvas.tag_bind(id_, "<ButtonRelease-1>", self.vf.dashboard.
                        increaseColumnWidth)
        colWidthUpBalloon = "Increase column width and scale buttons down"
        self.balloon.tagbind(canvas, id_, colWidthUpBalloon)
        
        ##
        ## add a button to increase column widtg
        id_  = self.autoSizeButton = canvas.create_text(
            x+18, height/2.0, justify='center', text="Z", font='Arial 12',
            tags=('dashButtons',))
        x += 36
        canvas.tag_bind(id_, "<ButtonRelease-1>",
                        self.vf.dashboard.decreaseColumnWidth)
        colWidthDownBalloon = "Decrease column width and scale buttons down"
        self.balloon.tagbind(canvas, id_, colWidthDownBalloon)

        
    def addSel_cb(self, event=None):
        self.vf.addSelectionToDashboard.guiCallback()
        
        
    def createSelectionBox(self, master):
        master1 = Tkinter.Frame(master)

        # add selector entry
        self.selector = CompoundStringSelector()
        #self.selectorEntry = Pmw.EntryField(
        #    w, labelpos='w', label_text='Sel.:',
        #    entry_width=12, validate=None, command=self.selectFromString)
        self.selectorEntry = Pmw.ComboBox(
            master1, labelpos='w', label_text='Sel.:', entry_width=12,
            ##scrolledlist_items = self.vf.sets.keys(),
            selectioncommand=self.selectFromString, fliparrow=1)
        self.selectorEntry.pack(side='left', expand=1, fill='x')

        # add selection tree expansion checkbox
        #var = self.expandTreeOnSelection = Tkinter.IntVar(0)
        #c = self.expandTreeOnSelectionTk = Tkinter.Checkbutton(
        #    master1, text="Expand", variable=var)
        #c.pack(side='left')
        
        # add backbone only widget
        self.bbmode_menu = Pmw.ComboBox(
            master1, selectioncommand= self.bbmodevar.set,
            scrolledlist_items = ['CMD', 'BB', 'SC', 'SC+CA', 'ALL'],
            entryfield_entry_width=4, fliparrow=1)
        self.bbmode_menu.selectitem('CMD')
        self.bbmode_menu.pack(side='right', expand=0)
        master1.pack(side='top', fill='x')

        self.selectorHelp = """This entry is used to select entities in the dashboard tree. 
Nodes selected in the dashboard tree are outlined by a yellow background.
When a command button is clicked for a selected node, the command is applied to all selected nodes.
The syntax for selection is a ';' separated list of expressions.
Each expression is a ':' separated list of selectors applying at the various levels of the Tree.
For instance:
    :::CA selects all alpha carbon atoms and sets the selection level to Atom
    :A::CA selects all CA in chain A
    ::CYS* selects all cysteines and sets the selection level to Residue
    
special names such as water, ions, DNA, RNA Amino Acids and lignad can be used at the residue level
special names such as sidechain, backbone, backbone+h, hetatm can be used at the atom level
"""
        self.balloon.bind(self.selectorEntry, self.selectorHelp)

        self.bbmodeHelp = """This option menu is used to specify whether commands should be applied to the
backbone atoms only (BB), the side chain atoms only (SC), the sidechain atoms
and CA atoms (SC+CA) or the full molecular fragment (ALL).
This setting can be overridden by each column (CMD)"""
        self.balloon.bind(self.bbmode_menu, self.bbmodeHelp)

##         expandHelp = """Check in order to expand the dashboard tree upon selection and select nodes in tree.
## Uncheck to perform PMV selection add"""
##         self.balloon.bind(self.expandTreeOnSelectionTk, expandHelp)

        return master1


    def addColumnDescriptor(self, columnDescr):
        vf = columnDescr.vf
        # load Pmv commands
        for cmd, module, package in columnDescr.pmvCmdsToLoad:
            #print 'loading', cmd, module, package
            vf.browseCommands(module, commands=(cmd,), package='Pmv', log=0)

        # register interest in Pmv commands
        dashboardCmd = vf.dashboard
        for cmd in columnDescr.pmvCmdsToHandle:
            #print 'register', cmd, columnDescr.title
            vf.cmdsWithOnRun[vf.commands[cmd]] = [dashboardCmd]

        cmd = columnDescr.cmd

        if isinstance(cmd[0], str):
            cmd[2]['callListener']=False
            columnDescr.cmd = (vf.commands[cmd[0]], cmd[1], cmd[2])
            #cmd[2]['callListener'] = False # prevents dashboard issues commands
                                            # from calling dashboard.onCmdRun
        if columnDescr.title is None:
            columnDescr.title = name

        TreeWithButtons.addColumnDescriptor(self, columnDescr)


    def expandParents(self, object):
        """Expand all parents of the node"""
        p = object.parent
        if not self.objectToNode.has_key(p):
            self.expandParents(p)
            
        self.objectToNode[p].expand()


    def selectFromString(self, value):
        #value = self.selectorEntry.getvalue()
        from MolKit.molecule import MoleculeSet
        molecules = MoleculeSet(
            [x for x in self.root.object.children if not isinstance(
                x, MoleculeSet)] )
        molFrag = self.selector.select(molecules, value, sets=self.vf.sets)

##         if self.expandTreeOnSelection.get():
##             for obj in molFrag[0]:
##                 try:
##                     node = self.objectToNode[obj]
##                 except KeyError:
##                     self.expandParents(obj)
##                     node = self.objectToNode[obj]
##                 node.select(only=False)
##         else:
##             self.vf.select(molFrag[0])
        self.vf.select(molFrag[0])


    def rightButtonClick(self, columnDescr, event):
        columnDescr.bbmodeOptMenu(event)



from MolKit.molecule import Atom, AtomSet, Molecule, MoleculeSet
from MolKit.protein import Chain, ChainSet, Residue, ResidueSet, Protein, ProteinSet
import numpy
from DejaVu.glfLabels import GlfLabels

class MolFragNodeWithButtons(NodeWithButtons):

    def setRotationCenter(self):
        vf = self.tree().vf
        obj = self.object
        vf.centerOnNodes(obj.setClass([obj]))


    def makeSetsForChains(self, event=None):
        vf = self.tree().vf
        for chain in self.object.children:
            name = chain.parent.name + '_' + chain.name
            vf.addSelectionToDashboard(name, chain)


    def deleteMolecule(self, event=None):
        self.tree().vf.deleteMol(self.object, undoable=True)


    def postMoleculeMenu(self,event):
        menu = Tkinter.Menu(tearoff=False)
        obj = self.object
        #isroot = False

        if isinstance(obj, MolecularSystem):
            cb = self.tree().vf.readMolecule.guiCallback
            menu.add_command(label='Read molecule', command=cb)
            menu.add_separator()
            cb = CallbackFunction(self.showHideAll, show=1)
            menu.add_command(label='Hide all molecule', command=cb)
            cb = CallbackFunction(self.showHideAll, show=0)
            menu.add_command(label='Show all molecule', command=cb)
            
        else:
            if isinstance(obj, Protein) or isinstance(obj, Molecule) and \
               not isinstance(obj, Chain) and not isinstance(obj, Residue):
                isMol = True
            else:
                isMol = False

            if isMol:
                gcg = self.object.geomContainer.geoms
                if gcg['master'].visible:
                    menu.add_command(label='Hide molecule',
                                     command=self.showHide)
                else:
                    cb = CallbackFunction(self.showHide, show=0)
                    menu.add_command(label='Show molecule', command=cb)
                menu.add_command(label='View text file',
                                 command=self.viewSource)
                menu.add_separator()

            menu.add_command(label='Show in 3D Viewer',
                             command=self.focusCamera)
            menu.add_command(label='Set rotation center',
                             command=self.setRotationCenter)

            if isMol:
                menu.add_separator()
                if len(obj.children)>1:
                    menu.add_command(label='Make sets for chains',
                                     command=self.makeSetsForChains)
                menu.add_command(label='Delete', command=self.deleteMolecule)
                menu.add_separator()
                menu.add_command(label='Add Hydrogen', command=self.protonate)
                cb = CallbackFunction(self.protonate, polar=1)
                menu.add_command(label='Add Polar Hydrogens', command=cb)

                menu.add_command(label='Show Hydrogens',
                                 command=self.showHideHydrogens)
                cb = CallbackFunction(self.showHideHydrogens, negate=True)
                menu.add_command(label='Hide Hydrogens', command=cb)

        menu.add_separator()
        menu.add_command(label='Dismiss')
        menu.post(event.x_root, event.y_root)
        self.menu = menu
        self.label.master.bind('<FocusOut>', self.cancelMenu)


    def showHideAll(self, show=1):
        tree = self.tree()
        vi = tree.vf.GUI.VIEWER
        old = vi.suspendRedraw
        vi.suspendRedraw = True
        for child in tree.root.children:
            if isinstance(child, MolFragNodeWithButtons):
                self.showHide(show, child)
        vi.suspendRedraw = old

            
    def showHide(self, show=1, node=None):
        if node is None:
            node = self
            
        mol = node.object
        self.tree().vf.showMolecules(mol, show)
        if show:
            node.label.configure(state='disabled')
        else:
            node.label.configure(state='normal')

        
    def showHideHydrogens(self, negate=0):
        hydrogens = self.object.findType(Atom).get('H*')
        if len(hydrogens):
            vf = self.tree().vf
            gca = self.object.geomContainer.atoms
            hat = {}.fromkeys(hydrogens)

            hydat = [] # list of H atoms bound to atoms visible as lines
            atoms = gca['bonded']
            if len(atoms):
                for a in atoms:
                    for b in a.bonds:
                        a2 = b.atom1
                        if a2==a: a2 = b.atom2
                        if hat.has_key(a2):
                            hydat.append(a2)
                vf.displayLines(AtomSet(hydat), negate=negate)

            hydat = [] # list of H atoms bound to atoms visible as sticks
            atoms = gca['sticks']
            if len(atoms):
                for a in atoms:
                    for b in a.bonds:
                        a2 = b.atom1
                        if a2==a: a2 = b.atom2
                        if hat.has_key(a2):
                            hydat.append(a2)
                vf.displaySticksAndBalls(AtomSet(hydat), negate=negate)

            hydat = [] # list of H atoms bound to atoms visible as cpk
            atoms = gca['cpk']
            if len(atoms):
                for a in atoms:
                    for b in a.bonds:
                        a2 = b.atom1
                        if a2==a: a2 = b.atom2
                        if hat.has_key(a2):
                            hydat.append(a2)
                vf.displayCPK(AtomSet(hydat), negate=negate)


    def protonate(self, polar=0):
        self.tree().vf.add_hGC(self.object, redraw=1, renumber=1,
                               polarOnly=polar,  method='noBondOrder')


    def viewSource(self, event=None):
        self.object.parser.viewSource()
    

    def focusCamera(self, event=None):
        if isinstance(self, SelectionWithButtons):
            #obj = self.getNodes(0)[0]
            obj = self.object._set
            if isinstance(obj[0], Atom): sca = 1
            elif isinstance(obj[0], Residue): sca = 2
            elif isinstance(obj[0], Chain): sca = 3
            elif isinstance(obj[0], Molecule): sca = 4
            name = self.object.name
            coords = numpy.array(obj.findType(Atom).coords)
        else:
            if isinstance(self.object, Atom): sca = 1
            elif isinstance(self.object, Residue): sca = 2
            elif isinstance(self.object, Chain): sca = 3
            elif isinstance(self.object, Molecule): sca = 4
            name = self.object.full_name()
            coords = numpy.array(self.object.getAtoms().coords)

        mini = numpy.min( coords, 0)
        maxi = numpy.max( coords, 0)
        #self.currentCamera.AutoDepthCue(object=object)
        gui = self.tree().vf.GUI
        vi = gui.VIEWER

        vi.FocusOnBox(vi.rootObject, mini-6, maxi+6)

        # add flash spheres
        from DejaVu.Spheres import Spheres
        sph = Spheres('highlightFocus', vertices=coords, radii=(0.2,),
                      opacity=0.99, transparent=1, inheritMaterial=0,
                      materials=[(0,1,1),], visible=0)
        vi.AddObject(sph)
        sph.applyStrokes()

        # add flash label
        lab = GlfLabels(
            'flashLabel', fontStyle='solid3d', fontTranslation=(0,0,3.),
            fontScales=(sca*.3,sca*.3, .1), pickable=0, labels=[name],
            vertices=[numpy.sum(coords, 0)/len(coords)], visible=0)
        vi.AddObject(lab)
        lab.applyStrokes()

        #sph.fadeOut()
        cb = CallbackFunction(self.afterFlash_cb, sph)
        sph.flashT(interval=20, after_cb=cb)
        cb = CallbackFunction(self.afterFlash_cb, lab)
        lab.flashT(interval=20, after_cb=cb)


    def afterFlash_cb(self, geom):
        self.tree().vf.GUI.VIEWER.RemoveObject(geom)
        
        
    def cancelMenu(self, event=None):
        self.menu.unpost()


    def drawNodeLabel(self, x, y):
        result = NodeWithButtons.drawNodeLabel(self, x, y)
        obj = self.object
        if isinstance(obj, Protein) or isinstance(obj, Molecule) and \
           not isinstance(obj, Chain) and not isinstance(obj, Residue):
            isMol = True
        else:
            isMol = False

        if isMol:
            gcg = self.object.geomContainer.geoms
            if gcg['master'].visible:
                self.label.configure(state='normal')
            else:
                self.label.configure(state='disabled')
        return result
    

    def doubleLabel1(self, event=None):
        # override double click on label
        self.deselect() # undo yellow back ground that migh be created by first
                        # click in double click serie
        obj = self.object

        if isinstance(obj, Protein) or isinstance(obj, Molecule) and \
           not isinstance(obj, Chain) and not isinstance(obj, Residue):
            isMol = True
        else:
            isMol = False

        if isMol:
            gcg = self.object.geomContainer.geoms
            if gcg['master'].visible:
                self.showHide(show=1)
            else:
                self.showHide(show=0)

        
    def button3OnLabel(self, event=None):
        self.postMoleculeMenu(event)


    def getIcon(self):
        """return node's icons"""
        iconsManager = self.tree().iconsManager
        object = self.object
        if isinstance(object, Atom):
            icon = iconsManager.get("atom.png", self.tree().master)
        elif isinstance(object, Residue):
            icon = iconsManager.get("residue.png", self.tree().master)
        elif isinstance(object, Chain):
            icon = iconsManager.get("chain.png", self.tree().master)
        elif isinstance(object, Molecule):
            icon = iconsManager.get("ms.png", self.tree().master)
        else:
            icon = None

        if icon:
            self.iconWidth = icon.width()
        else:
            self.iconWidth = 0
        return icon


    def getNodes(self, column):
        #print 'MolFragNodeWithButtons.getNodes'
        tree = self.tree()
        # return the objects associated with this node
        # handle the backbone, sidechain and both value for the command
        result = molFrag = self.object
        if isinstance(result, MolecularSystem):
            result = MoleculeSet([x for x in result.children if \
                                  isinstance(x, Molecule)])
        bbmode = tree.bbmodevar.get()

        if bbmode=='CMD':
            #print 'Cmd setting found'
            bbmode = tree.columns[column].bbmode

        #print 'bbmode in getNode', column, bbmode
        if bbmode!='ALL':
            if result.findType(Chain)[0].isProteic():
                atoms = result.findType(Atom)
                if bbmode=='BB':
                    result = atoms.get('backbone')
                elif bbmode=='SC+CA':
                    result = atoms.get('sidechain')+atoms.get('CA')
                else:
                    result = atoms.get('sidechain')
                try:
                    return result.setClass([result])
                except KeyError:
                    return {self: [result]}

        if hasattr(result,'setClass') and result.setClass:
            return {self: [result.setClass([result])]}
        else:
            return {self: [result]}
        

    def getObjects(self, column):
        # return a list of objects associated with this node and possibly
        # other selected nodes.  For selection we return a list for each type
        # ( i.e. Atom, Residue, etc..)
        # if the node is selected, collect object from all other selected nodes
        tree = self.tree()
        if not self.isSelected:
            return self.getNodes(column)

        else:
            buttonValue = self.chkbtval[column]
            fill = tree.columns[column].buttonColors
            # loop over selected nodes
            results = {}
            for node in tree.selectedNodes:
                if node.parent is None: # 'All Molecules' is selected 
                    continue

                topNode = node  # find molecule or set level
                while topNode.parent.parent!=None:
                    topNode = topNode.parent

                if results.has_key(topNode):
                    resultAtoms = results[topNode][3]
                    resultResidues = results[topNode][2]
                    resultChains = results[topNode][1]
                    resultMolecules = results[topNode][0]
                else:
                    resultAtoms = AtomSet([])
                    resultResidues = ResidueSet([])
                    resultChains = ChainSet([])
                    resultMolecules = MoleculeSet([])
                    
                    results[topNode] = [ resultMolecules, resultChains,
                                         resultResidues, resultAtoms ]

                    
                if node.buttonType is None: # None for percent buttons
                    if node in tree.displayedNodes:
                        tree.canvas.itemconfigure(node.chkbtid[column],
                                                  fill=fill[buttonValue])
                    node.chkbtval[column] = buttonValue
                result = node.getNodes(column)
                #result.append(node.getNodes(column))
                obj = result.values()[0][0]
                #print 'HHHHH', node, result, obj
                if isinstance(obj, AtomSet):
                    resultAtoms += obj
                elif isinstance(obj, ResidueSet):
                    resultResidues += obj
                elif isinstance(obj, ChainSet):
                        resultChains += obj
                elif isinstance(obj, MoleculeSet) or isinstance(obj, ProteinSet):
                    resultMolecules += obj

            #print 'HAHA', results
            return results
                

class SelectionWithButtons(MolFragNodeWithButtons):

    def __init__(self, object, parent):

        MolFragNodeWithButtons.__init__(self, object, parent,
                                        buttonType='OnOffButtons')
        self.nbSplits = 0

    def getNodes(self, column):
        return {self: [self.tree().vf.getSelection().copy()]}

    def setRotationCenter(self):
        vf = self.tree().vf
        sel = vf.getSelection()
        obj = sel[0]
        vf.centerOnNodes(obj.setClass(sel))

    def postSetMenu(self,event):
        menu = Tkinter.Menu(tearoff=False)
        menu.add_command(label='Split', command=self.splitSelection)
        menu.add_command(label='Clone', command=self.cloneSelection)
        menu.add_separator()
        menu.add_command(label='Show in 3D Viewer', command=self.focusCamera)
        menu.add_command(label='Set rotation center',
                         command=self.setRotationCenter)
        menu.add_separator()
        menu.add_command(label='Delete selected Atoms',
                         command=self.tree().vf.deleteCurrentSelection)
        menu.add_separator()
        menu.add_command(label='Dismiss')
        menu.post(event.x_root, event.y_root)
        self.menu = menu
        self.label.master.bind('<FocusOut>', self.cancelMenu)


    def button3OnLabel(self, event=None):
        self.postSetMenu(event)


    def cloneSelection(self):
        self.splitSelection(cmdName='cloned', deleteAfterCopy=False)

        
    def splitSelection(self, cmdName='split', deleteAfterCopy=True):

        nodes = self.getNodes(1)
        if nodes == self.tree().vf.Mols:
            from tkMessageBox import showwarning
            showwarning("Warning", "select something first")
        else:
            nodes = self.getNodes(0) # does not use dashboard selection
            if len(nodes)==0:
                return
            self.nodes = nodes
            cb = CallbackFunction( self.executeSplit,
                                   deleteAfterCopy=deleteAfterCopy)
            w = self.nameSelectionDialog = Pmw.PromptDialog(
                self.tree().vf.master, title = 'Split name', 
                label_text = "Enter the name of the %s molecule"%cmdName,
                entryfield_labelpos = 'n',
                buttons = ('OK', 'Cancel'), command=cb)
            #w.insertentry(0, nodes.buildRepr()[:30].replace(';', ''))
            w.insertentry(0, "split_%d"%self.nbSplits)
            self.nbSplits += 1
            w.component('entry').selection_range(0, Tkinter.END) 
            w.component('entry').focus_set()
            w.component('entry').bind('<Return>', cb)
            self.nameSelectionDialog.geometry(
                '+%d+%d' % (self.tree().vf.master.winfo_x()+200,
                            self.tree().vf.master.winfo_y()+200))             


    def executeSplit(self, result, deleteAfterCopy=True):
        self.nameSelectionDialog.withdraw()
        if result == 'OK'  or hasattr(result, "widget"):
            name = self.nameSelectionDialog.get()   
            if not name: return  
            vf = self.tree().vf
            vf.clearSelection()
            self._splitSet(self.nodes, name=name,
                           deleteAfterCopy=deleteAfterCopy)
        

    def _splitSet(self, nodes, name=None, deleteAfterCopy=True):
        if name is None:
            name = nodes.buildRepr()[:30]
        name = name.replace(" ", "_")
        name = name.replace(";", "")
        vf = self.tree().vf

        # make one AtomSet out of all objects
        atoms = AtomSet([])
        for node,objlist in nodes.items():
            for obj in objlist: # each node has [AtomSet, ResidueSet, ...]
                if len(obj)==0: continue
                # get all atoms for this node
                atoms += obj.findType(Atom)
        from MolKit import makeMoleculeFromAtoms
        mol = makeMoleculeFromAtoms(name, atoms)
        vf.addMolecule(mol)
        
        if deleteAfterCopy:
            vf.deleteAtomSet(atoms)

        

class SetWithButtons(SelectionWithButtons):

    def setRotationCenter(self):
        vf = self.tree().vf
        sel = vf.getSelection()
        obj = sel[0]
        vf.centerOnNodes(self.object._set)

    def getNodes(self, column):
        return {self: [self.object._set]}


    def splitSet(self):
        self._splitSet(self.getNodes(0), name=self.label.configure('text')[4],
                       deleteAfterCopy=True)
        
    def copySet(self):
        self._splitSet(self.getNodes(0), name=self.label.configure('text')[4],
                       deleteAfterCopy=False)
        
    def postSetMenu(self,event):
        menu = Tkinter.Menu(tearoff=False)
        menu.add_command(label='Rename', command=self.renameSet)
        menu.add_command(label='Split', command=self.splitSet)
        menu.add_command(label='Clone', command=self.copySet)
        menu.add_command(label='Remove', command=self.removeSet)
        menu.add_separator()
        menu.add_command(label='Set rotation center',
                         command=self.setRotationCenter)
        menu.add_command(label='Show in 3D Viewer', command=self.focusCamera)
        menu.add_separator()
        menu.add_command(label='Dismiss')
        menu.post(event.x_root, event.y_root)
        self.menu = menu
        self.label.master.bind('<FocusOut>', self.cancelMenu)


    def removeSet(self):
        vf = self.tree().vf
        vf.dashboard.onRemoveObjectFromViewer(self.object)
        
        # remove molecular surface for this set if it exists
        name = 'surface_%s'% str(self).replace(' ', '_')
        name = name.replace('_','-')

        vi = vf.GUI.VIEWER
        for node,objlist in self.getNodes(0).items():
            # find molecules
            atoms = AtomSet([]) # collect atoms from objlist
            for obj in objlist:
                atoms += obj.findType(Atom)
            mols = atoms.top.uniq()
            for mol in mols:
                gc = mol.geomContainer
                if gc.geoms.has_key(name):
                    geom = gc.geoms[name]
                    del gc.geoms[name]
                    del gc.atoms[name]
                    swigsrf = gc.msms[name][0]
                    del swigsrf
                    del gc.msms[name]
                    geom.protected = 0 
                    vi.RemoveObject(geom)

        # remove set from list of sets:
        del vf.sets[str(self)]
        
        vi.Redraw()


    def renameSet(self):
        from tkSimpleDialog import askstring
        oldname = self.object.name
        name = askstring("rename set", "new name:", initialvalue=oldname)
        if name is None:
            name = self.object.name
        self.object.setSetAttribute('name', name)
        self.tree().root.refreshChildren()

        # name set in vf.sets
        sets = self.tree().vf.sets
        sets[name] = sets[oldname]
        del sets[oldname]


class WaterWithButtons(SetWithButtons):

    # all atoms in residues with name HOH or WAT
    def getNodes(self, column):
        allres = self.tree().vf.allAtoms.parent.uniq()
        res = [a for a in allres if a.type=='WAT' or a.type=='HOH']
        return {self: [ResidueSet(res)]}


from MolKit.PDBresidueNames import RNAnames, AAnames, DNAnames, ionNames, \
     allResidueNames

class IonsWithButtons(SetWithButtons):
    
    # all atoms in residues with name in the ion names list
    def getNodes(self, column):
        allres = self.tree().vf.Mols.chains.residues
        res = [a for a in allres if ionNames.has_key(a.type.strip())]
        return {self: [ResidueSet(res)]}


class DNAWithButtons(SetWithButtons):
    
    # all atoms in residues with name in the DNA names list
    def getNodes(self, column):
        allres = self.tree().vf.Mols.chains.residues
        res = [a for a in allres if DNAnames.has_key(a.type.strip())]
        return {self: [ResidueSet(res)]}


class RNAWithButtons(SetWithButtons):

    # all atoms in residues with name in the RNA names list
    def getNodes(self, column):
        allres = self.tree().vf.Mols.chains.residues
        res = [a for a in allres if RNAnames.has_key(a.type.strip())]
        return {self: [ResidueSet(res)]}


class STDAAWithButtons(SetWithButtons):
    
    # all atoms in residues with name in the amino acids names list
    def getNodes(self, column):
        allres = self.tree().vf.Mols.chains.residues
        res = [a for a in allres if AAnames.has_key(a.type.strip())]
        return {self: [ResidueSet(res)]}


class LigandAtomsWithButtons(SetWithButtons):
    
    def getNodes(self, column):
        allres = self.tree().vf.Mols.chains.residues
        res = [a for a in allres if not allResidueNames.has_key(a.type.strip())]
        return {self: [ResidueSet(res)]}



#####################################################################
#
#  Column Descriptors for common PMV commands
#
#####################################################################
ColumnDescriptors = []

import Pmv, os, ImageTk

class MVColumnDescriptor(ColumnDescriptor):         

    def __init__(self, name, cmd, btype='checkbutton', 
                 buttonShape='circle', buttonColors = ['white', 'green'],
                 inherited=True, title=None, color='black',
                 objClassHasNoButton=None,
                 pmvCmdsToLoad=[], pmvCmdsToHandle=[],
                 showPercent=False, getNodeLevel=None, iconfile=None,
                 buttonBalloon=None, onButtonBalloon=None,
                 offButtonBalloon=None):

        ColumnDescriptor.__init__(
            self, name, cmd, btype=btype, 
            buttonShape=buttonShape, buttonColors=buttonColors,
            inherited=inherited, title=title, color=color,
            objClassHasNoButton=objClassHasNoButton, showPercent=showPercent,
            buttonBalloon=buttonBalloon, onButtonBalloon=onButtonBalloon,
            offButtonBalloon=offButtonBalloon)

        self.getNodeLevel = getNodeLevel
        
        self.pmvCmdsToHandle = pmvCmdsToHandle #list of Pmv commands that
           # this column wants to know about

        self.pmvCmdsToLoad = pmvCmdsToLoad #list of Pmv commands that
           # need to be loaded. Each one is (command, module, package)

        self.bbmode = 'ALL'
        self.bbmodeWidgetcid = None

        self.iconfile = iconfile
        self.icon = None

        if iconfile: self.getIcon(iconfile)


    def optMenu_cb(self, node, column, event=None):
        cmd, args, kw = self.cmd

        #from Pmv.displayCommands import DisplayCommand
        #cmd.setLastUsedValues('default')
        # force display radio button
        if cmd.cmdForms.has_key('default'): # if form exists change widget
            dispW = cmd.cmdForms['default'].descr.entryByName['display']['widget']
            dispW.component('display').invoke() # set radio to 'display'
        else:
            # change default values so when form is created it will use display
            cmd.lastUsedValues['default']['negate'] = False
            cmd.lastUsedValues['default']['only'] = False

        ColumnDescriptor.optMenu_cb(self, node, column, event)


        
    def getIcon(self, iconfile):
        filename = os.path.join(iconPath, iconfile)
        self.icon = ImageTk.PhotoImage(file=filename)


    def _getNodes(self, node, colInd):
        #print 'MVColumnDescriptor _getNodes'
        return node.getObjects(colInd)

##         # added so that MVColumnDescriptor can override
##         objects = node.getObjects(colInd)
##         #print 'KKKK', objects, colInd
##         #print objects.__class__, len(objects), repr(objects)
##         if self.getNodeLevel:
##             if isinstance(objects, list): # special and user sets
##                 objects = [x.findType(self.getNodeLevel) for x in objects]
##             else: # MolKit node set
##                 objects = [objects.findType(self.getNodeLevel)]

##         return {self: [objects]}


    def execute(self, node, colInd):
        #print 'IN MVColumnDescriptor.execute for', str(node)
        objects = self._getNodes(node, colInd)
        val = node.chkbtval[colInd]
        cmd, args, kw = self.cmd
        defaultValues = cmd.getLastUsedValues()
        defaultValues.update( kw )
        
        if  self.commandType == 'checkbutton':
            if defaultValues.has_key('negate'):
                defaultValues['negate'] = not val
            elif not val:
                return
        # when lines in dashboard are selected objects has one entry per line
        for node,objlist in objects.items():
            for objs in objlist: # each node has [AtomSet, ResidueSet, ...]
                if len(objs)==0: continue
                
                #print 'ColumnDescriptor execute GGGG', cmd, repr(objs), objs.__class__, args, defaultValues
                if isinstance(cmd, MVSelectCommand):
                    # if the commadn is select we need to be careful about
                    # the selection level. If objs is smaller than selection
                    # level (e.g. atoms vs residues) we set the selection level
                    # to objs else we turn objs into the selection level.
                    selection = self.tree.vf.selection
                    orderedList = [ProteinSet, ChainSet, ResidueSet, AtomSet]
                    orderedList1 = [MoleculeSet, ChainSet, ResidueSet, AtomSet]
                    try:
                        objInd = orderedList.index(objs.__class__)
                    except ValueError:
                        objInd = orderedList1.index(objs.__class__)
                    try:
                        selInd = orderedList.index(selection.__class__)
                    except ValueError:
                        selInd = orderedList1.index(selection.__class__)
                    if objInd > selInd: # obj is smaller than selection
                        self.tree.vf.setSelectionLevel(objs.elementType)
                    else: # selection is smaller so we make obj smaller
                        objs = objs.findType(selection.elementType)
                cmd ( *((objs,)+args), **defaultValues)

    ## def onPmvCmd(self, command, column, *args, **kw):
    ##     pass


    def setBBmode(self, value):
        assert value in ['BB', 'SC', 'SC+CA', 'ALL']
        self.bbmode = value
        if self.bbmodeWidgetcid:
            self.tree.delete(self.bbmodeWidgetcid)
        self.bbmodeWidgetcid = None
        

    def bbmodeOptMenu(self, event):
        self.bbmodeWidget = Pmw.ComboBox(
            self.tree.interior(), selectioncommand=self.setBBmode,
            scrolledlist_items=['BB', 'SC', 'SC+CA', 'ALL'],
            entryfield_entry_width=4)#, dropdown=0)
        self.bbmodeWidget.selectitem(self.bbmode)

        self.bbmodeWidgetcid = self.tree.create_window(event.x, event.y,
                                         window=self.bbmodeWidget, anchor='nw')

        
from MolKit.molecule import Molecule, MolecularSystem
from MolKit.protein import Residue, Chain

class MVvisibilityColumnDescriptor(MVColumnDescriptor):         

    def __init__(self, name, cmd, **kw):

        MVColumnDescriptor.__init__(self, name, cmd, **kw)
        self.cbOn = self.onShowMoleculesCmd
        self.cbOff = self.onShowMoleculesCmd
            

    def onShowMoleculesCmd(self, node, colInd, val, event=None):
        tree = self.tree
        # FIXME
        obj = node.getObjects(colInd) # what to cmd will apply to
        if isinstance(obj, list): # for sets
            obj = obj[0]

            self.vf.showMolecules(obj, not val)
            for mol in obj: # loop over molecules
                node = tree.objectToNode[mol]
                node.set(colInd, val)
        else:
            self.vf.showMolecules(obj, node.chkbtval[colInd])
            node.toggle(colInd)
        tree.redraw()


    def isOn(self, node):
        try:
            return node.geomContainer.masterGeom.visible
        except AttributeError:
            return 1 # at first the master geom is not there yet

visibilityColDescr = MVvisibilityColumnDescriptor(
    'showMolecules', ('showMolecules', (), {}), title='V', 
    buttonColors=['white', 'grey75'], inherited=False,
    buttonShape='rectangle', color='black',
    objClassHasNoButton = [Atom, Residue, Chain, MoleculeSet, MolecularSystem],
    pmvCmdsToHandle = [],#'showMolecules'],
    pmvCmdsToLoad = [('showMolecules', 'displayCommands', 'Pmv'),],
    iconfile='dashboardeyeballIcon.jpg',
    buttonBalloon='show/hide %s',
    onButtonBalloon='show molecules in %s',
    offButtonBalloon='hide molecules in %s')
ColumnDescriptors.append(visibilityColDescr)


class MoleculeSetNoSelection(MoleculeSet):
    pass


class MVSelectColumnDescriptor(MVColumnDescriptor):         
    """
    class for selection column in dashboard
    """

    def __init__(self, name, cmd, btype='checkbutton', 
                 buttonShape='circle', buttonColors = ['white', 'green'],
                 inherited=True, title=None, color='black',
                 objClassHasNoButton=[MoleculeSetNoSelection],
                 pmvCmdsToLoad=[], pmvCmdsToHandle=[],
                 buttonBalloon=None, onButtonBalloon=None,
                 offButtonBalloon=None):

        MVColumnDescriptor.__init__(
            self, name, cmd, btype=btype, 
            buttonShape=buttonShape, buttonColors=buttonColors,
            inherited=inherited, title=title, color=color,
            objClassHasNoButton=objClassHasNoButton,
            pmvCmdsToLoad=pmvCmdsToLoad, pmvCmdsToHandle=pmvCmdsToHandle,
            showPercent='_selectionStatus',
            iconfile='dashboardSelectionIcon.jpg',
            buttonBalloon=buttonBalloon, onButtonBalloon=onButtonBalloon,
            offButtonBalloon=offButtonBalloon)

        self.selectionDict = {}
        self.getNodeLevel = Atom
        self.deselectVar = Tkinter.IntVar()
        self.distanceVar = Tkinter.DoubleVar()
        self.distanceVar.set(5.0)
        

    def makeNames(self, obj, selector, selLevel='atom'):
        names = ''
        for ob in obj:
            if selLevel=='atom':
                if isinstance(ob, Atom):
                    pass
                elif isinstance(ob, Residue):
                    names += '%s:%s;'%(ob.full_name(), selector) 
                elif isinstance(ob, Chain):
                    names += '%s::%s;'%(ob.full_name(), selector)
                elif isinstance(ob, Molecule):
                    names += '%s:::%s;'%(ob.full_name(), selector)
            elif selLevel=='residue':
                if isinstance(ob, Atom):
                    pass
                elif isinstance(ob, Residue):
                    pass
                elif isinstance(ob, Chain):
                    names += '%s:%s;'%(ob.full_name(), selector)
                elif isinstance(ob, Molecule):
                    names += '%s::%s;'%(ob.full_name(), selector)
        return names


    def select_cb(self, names):
        self.vf.select(names, negate=self.deselectVar.get())
        
        
    def optMenu_cb(self, node, column, event=None):
        tree = self.tree
        if len(tree.selectedNodes)>0:
            tree.clearSelection()
            
        # called upon right click
        obj = node.getObjects(column) # what to cmd will apply to
        obj = obj[node][0]

        # reset deselection button
        self.deselectVar.set(0)
        
        menu = Tkinter.Menu(tearoff=False)
        
        cb = CallbackFunction( self.vf.deselect, "*" )
        menu.add_command(label='Clear selection', command=cb)

        cb = CallbackFunction( self.vf.invertSelection, subset=obj)
        menu.add_command(label='Invert selection', command=cb)

        cb = CallbackFunction( menu.post, event.x_root, event.y_root )
        menu.add_checkbutton(label='Deselect', variable=self.deselectVar,
                             command=cb)
       
        if not isinstance(obj, AtomSet) or len(obj)>1:

            menu.add_separator()
            menu.add_command(label='Subsets', command=None, state='disable',
                             font=('Helvetica', 12, 'bold'))

            names = self.makeNames(obj, 'backbone')

            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Backbone', command=cb)

            names = self.makeNames(obj, 'sidechain')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Sidechains', command=cb)

            names = self.makeNames(obj, 'hetero')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Hetero Atoms', command=cb)

            names = self.makeNames(obj, 'H*')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Hydrogens', command=cb)

            names = self.makeNames(obj, 'C*')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Carbons', command=cb)

        if not isinstance(obj, AtomSet) and \
               (not isinstance(obj, ResidueSet) or len(obj)>1):

            menu.add_separator()
            menu.add_command(label='Special', command=None, state='disable',
                             font=('Helvetica', 12, 'bold'))

            names = self.makeNames(obj, 'Water', selLevel='residue')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Water', command=cb)

            names = self.makeNames(obj, 'ions', selLevel='residue')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Ions', command=cb)

            names = self.makeNames(obj, 'dna', selLevel='residue')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='DNA', command=cb)

            names = self.makeNames(obj, 'rna', selLevel='residue')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='RNA', command=cb)

            names = self.makeNames(obj, 'aminoacids', selLevel='residue')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Amino Acids', command=cb)

            names = self.makeNames(obj, 'ligand', selLevel='residue')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Ligand', command=cb)

        menu.add_separator()

        menu.add_command(label='Displayed as', command=None,
                         state='disable', font=('Helvetica', 12, 'bold'))
        alines = AtomSet()
        acpk = AtomSet()
        asticks = AtomSet()
        aribbon = ResidueSet()
        asurface = AtomSet()
        aalab = AtomSet()
        arlab = ResidueSet()

        for ob in obj:
            mol = ob.top
            gca = mol.geomContainer.atoms
            if gca['bonded']:
                alines += gca['bonded']
            if gca['cpk']:
                acpk += gca['cpk']
            if gca['sticks']:
                asticks += gca['sticks']
            msmsAtoms = {}
            for msmsName in mol.geomContainer.msms.keys():
                if gca.has_key(msmsName) and gca[msmsName]:
                    msmsAtoms[msmsName] = gca[msmsName]
            if gca['AtomLabels']:
                aalab += gca['AtomLabels']
            if gca['ResidueLabels']:
                arlab += gca['ResidueLabels']
            for k, v in gca.items():
                if k[:4] in ['Heli', 'Stra', 'Turn', 'Coil']:
                    aribbon += gca[k]

        if alines:
            cb = CallbackFunction( self.vf.select, alines.copy())
            menu.add_command(label='Lines', command=cb)
        if acpk:
            cb = CallbackFunction( self.vf.select, acpk.copy())
            menu.add_command(label='Spheres', command=cb)
        if asticks:
            cb = CallbackFunction( self.vf.select, asticks.copy())
            menu.add_command(label='Balls & Sticks', command=cb)
        if aribbon:
            cb = CallbackFunction( self.vf.select, aribbon.copy())
            menu.add_command(label='Ribbon', command=cb)
        if msmsAtoms:
            for name, atoms in msmsAtoms.items():
                cb = CallbackFunction( self.vf.select, atoms.copy())
                menu.add_command(label='Surface %s'%name,
                                 command=cb)
        if aalab:
            cb = CallbackFunction( self.vf.select, aalab.copy())
            menu.add_command(label='With atom labels', command=cb)
        if arlab:
            cb = CallbackFunction( self.vf.select, arlab.copy())
            menu.add_command(label='With residue labels',
                             command=cb)
                
        if len(self.vf.selection):
            menu.add_separator()
            menu.add_command(label='Edit current', command=None,
                             state='disable', font=('Helvetica', 12, 'bold'))
            self.menuPosition = (event.x_root, event.y_root)


            cb = CallbackFunction( self.setCutOff, self.expand, obj, node)
            menu.add_command(label='Expand selection', command=cb)

            cb = CallbackFunction( self.setCutOff, self.selectAround, obj, node)
            menu.add_command(label='Select around', command=cb)

        menu.add_separator()
        menu.add_command(label='Dismiss', command=self.cancelCB)

        menu.post(event.x_root, event.y_root)
        self.menu = menu


    def setCutOff(self, cmd, obj, node):
        self.menu.post( *self.menuPosition )
        self._tmproot = root = Tkinter.Toplevel()
        root.transient()
        root.geometry("+%d+%d"%root.winfo_pointerxy())
        root.overrideredirect(True)

        # add geometry to show what would be selected with this cut off
        from DejaVu.Spheres import Spheres
        self.showCutoffSph = Spheres(
            'cutOffFeedBack', inheritMaterial=0, radii=(0.3,),
            materials=((0,1,1, 0.5),), transparent=1)
        self.vf.GUI.VIEWER.AddObject(self.showCutoffSph)

        cb = CallbackFunction( self.returnCB, cmd, obj, node)
        vcb = CallbackFunction( self._custom_validate, obj, node)
        c = Pmw.Counter(
            root, #label_text = 'distance cuttoff', labelpos = 'w',
            orient = 'horizontal', #label_justify = 'left',
            entryfield_value = '%5.1f'%self.distanceVar.get(),
            entry_width = 5,
            datatype = {'counter' : 'real', 'separator' : '.'},
            entryfield_validate = vcb,
            entryfield_command = cb,
            increment = 0.5)

        c.grid(row=0, column=0)
        self._counter = c

        im = ImageTk.PhotoImage(file=os.path.join(iconPath,'ok20.png'))
        b = Tkinter.Button(root, image=im, command=cb)
        b.im = im
        b.grid(row=0, column=1)

        im = ImageTk.PhotoImage(file=os.path.join(iconPath,'cancel20.png'))
        b = Tkinter.Button(root, image=im, command=self.cancelCB)
        b.im = im
        b.grid(row=0, column=2)


    def getContextProteinNames(self, node):
        if isinstance(node, SetWithButtons):
            names = [node.object.name]
        elif node==self.tree.root: # replace 'All Molecules' by a list of names
            names = [x.name for x in node.object.children[1:]] # skip selection
        else:
            names = [node.object.full_name()]
        return names

        
    def showCutOffSelection(self, val, obj, node):
        # show what this cutoff will select
        
        centers = self.vf.selection.findType(Atom).coords
        names = self.getContextProteinNames(node)
        ats = self.vf.selectInSphere.getAtoms(centers, val, names)
        self.showCutoffSph.Set(vertices=ats.coords)

        
    def _custom_validate(self, obj, node, text):
        try:
            val = float(text)
            if val > 0.0:
                ok = True
            else:
                ok = False
        except:
            ok = False
        if ok:
            self.showCutOffSelection(val, obj, node)
            return 1
        else:
            return -1

    def cancelCB(self, event=None):
        if hasattr(self, '_tmproot'):
            self._tmproot.destroy()
            del self._tmproot
            self.vf.GUI.VIEWER.RemoveObject(self.showCutoffSph)
            del self.showCutoffSph
        self.menu.unpost()


    def returnCB(self, cmd, obj, node, event=None):
        value = self._counter.get()
        self.distanceVar.set(value)
        self.cancelCB(event)
        cmd(obj, node)
        
    
    def expand(self, obj, node):
        dist = self.distanceVar.get()
        molNames = self.getContextProteinNames(node)
        d = {}.fromkeys(molNames)
        centers = self.vf.selection.findType(Atom).coords
        oldSel = self.vf.getSelection().findType(Atom)[:]
        self.vf.expandSelection(oldSel, centers, dist, d.keys(), )



    def selectAround(self, obj, node):
        dist = self.distanceVar.get()
        molNames = self.getContextProteinNames(node)
        oldSel = self.vf.getSelection().findType(Atom)[:]
        centers = oldSel.coords
        self.vf.selectAround(oldSel, centers, dist, molNames)



selectColDescr = MVSelectColumnDescriptor(
    'select', ('select', (), {}), title='S', #title='Sel.',
    buttonColors=['white', '#FFEA60'], inherited=False,
    buttonShape='rectangle', color='magenta',
    pmvCmdsToHandle = [],#'select', 'clearSelection', 'selectFromString',
                       #'invertSelection', 'selectInSphere',
                       #'setSelectionLevel'],
    pmvCmdsToLoad = [('select', 'selectionCommands', 'Pmv'),
                     ('clearSelection', 'selectionCommands', 'Pmv'),
                     ('selectFromString', 'selectionCommands', 'Pmv'),
                     ('invertSelection', 'selectionCommands', 'Pmv'),
                     ('selectInSphere', 'selectionCommands', 'Pmv'),
                     ('expandSelection', 'selectionCommands', 'Pmv'),
                     ('selectAround', 'selectionCommands', 'Pmv'),                                          
                     ],
    buttonBalloon='select/deselect %s',
    onButtonBalloon='select %s',
    offButtonBalloon='deselect %s'
    )

ColumnDescriptors.append(selectColDescr)


displayLinesColDescr = MVColumnDescriptor(
    'display lines', ('displayLines', (), {}),
    buttonColors=['white', '#FF4F44'], title='L',
    color='#5B49BF', pmvCmdsToHandle = [],#'displayLines'],
    pmvCmdsToLoad = [('displayLines', 'displayCommands', 'Pmv')],
    showPercent='_showLinesStatus', iconfile='dashboardLineIcon.jpg',
    buttonBalloon='display/undisplay lines for %s',
    onButtonBalloon='display lines for %s',
    offButtonBalloon='undisplay lines for %s'
)
ColumnDescriptors.append(displayLinesColDescr)


# we always use 'setScale':True because when a session is saves and restored
# this keyword gets set to False suring restore and because the default value
# used by the dashboard
displayCPKColDescr = MVColumnDescriptor(
    'display CPK', ('displayCPK', (), {'setScale':True}),
    buttonColors=['white', '#FF4F44'], title='C',
    color='#BF7C66', pmvCmdsToHandle = [],#'displayCPK'],
    pmvCmdsToLoad = [('displayCPK', 'displayCommands', 'Pmv')],
    showPercent='_showCPKStatus', iconfile='dashboardAtomIcon.jpg',
    buttonBalloon='display/undisplay atomic spheres for %s',
    onButtonBalloon='display atomic spheres for %s',
    offButtonBalloon='undisplay atomic spheres for %s'
)
ColumnDescriptors.append(displayCPKColDescr)


displaySandBColDescr = MVColumnDescriptor(
    'display S&B', ('displaySticksAndBalls', (), {'setScale':True}),
    buttonColors=['white', '#FF4F44'], title='B',
    color='purple', pmvCmdsToHandle = [],#'displaySticksAndBalls'],
    pmvCmdsToLoad = [('displaySticksAndBalls', 'displayCommands', 'Pmv')],
    showPercent='_showS&BStatus', iconfile='dashboardBondIcon.jpg',
    buttonBalloon='display/undisplay Sticks and Balls for %s',
    onButtonBalloon='display sticks and balls for %s',
    offButtonBalloon='undisplay sticks and balls for %s')
ColumnDescriptors.append(displaySandBColDescr)



class RibbonColumnDescriptor(MVColumnDescriptor):


    # override Ribbon.optMenu_cb to display panel of extrude SS
    def optMenu_cb(self, node, column, event=None):
        cmd = self.vf.extrudeSecondaryStructure
        val = cmd.guiCallback(do=False)

        if val is None: return

        # get a dict ofr all selected nodes in dashboard
        nodedict = node.getObjects(column) # what to cmd will apply to
        for node, lists in nodedict.items():
            for _set in lists:
                if len(_set):
                    cmd.doitWrapper( _set, **val)


displaySSColDescr = RibbonColumnDescriptor(
    'display Second.Struct.', ('ribbon', (), {}),
    buttonColors=['white', '#FF4F44'], title='R', 
    color='#333333', pmvCmdsToHandle = [],#'displayExtrudedSS'],
    pmvCmdsToLoad = [('displayExtrudedSS', 'secondaryStructureCommands', 'Pmv')],
    showPercent='_showRibbonStatus', iconfile='dashboardRibbonIcon.jpg',
    buttonBalloon='Display/Undisplay ribbon for %s',
    onButtonBalloon='display ribbon for %s',
    offButtonBalloon='undisplay ribbon for %s')


ColumnDescriptors.append(displaySSColDescr)


import types
class MSMSColumnDescriptor(MVColumnDescriptor):

    def __init__(self, name, cmd, btype='checkbutton', 
                 buttonShape='circle', buttonColors = ['white', 'green'],
                 inherited=True, title=None, color='black',
                 pmvCmdsToLoad=[], pmvCmdsToHandle=[],
                 buttonBalloon=None, onButtonBalloon=None,
                 offButtonBalloon=None):

        MVColumnDescriptor.__init__(
            self, name, cmd, btype=btype, 
            buttonShape=buttonShape, buttonColors=buttonColors,
            inherited=inherited, title=title, color=color,
            pmvCmdsToLoad=pmvCmdsToLoad, pmvCmdsToHandle=pmvCmdsToHandle,
            showPercent='_showMSMSStatus_MSMS_MOL',
            iconfile='dashboardSurfaceIcon.jpg',
            buttonBalloon=buttonBalloon, onButtonBalloon=onButtonBalloon,
            offButtonBalloon=offButtonBalloon)

        #self.getNodeLevel = Atom


    def execute(self, node, colInd):
        # get status of clicked button (1:full, 0:empty or partial)
        val = node.chkbtval[colInd]

        # get parameter from MSMS command input form
        cmd = self.vf.computeMSMS
        formValues = cmd.getLastUsedValues()
        formValues = cmd.fixValues(formValues)

        for node,objlist in node.getObjects(colInd).items():

            # collect atoms from the 4 lists in objList
            atoms = AtomSet([]) # collect atoms from objlist
            for obj in objlist:
                atoms += obj.findType(Atom)

            if len(atoms)==0: continue
            # find molecule
            mol = atoms[0].top

            if len(atoms)==1:
                # this does not compute a surface in MSMS :(. For now we
                # simply display CPK instead
                self.vf.displayCPK(atoms, topCommand=False)
                continue
            
            #from mglutil.util import misc
            #MB = float(1040*1024)
            #mem0 = mem1 = mem2 = misc.memory()
            
            # generate surface name and force perMol based on node type
            if isinstance(node, SetWithButtons) or \
                   isinstance(node, SelectionWithButtons):
                formValues['perMol']=0
                name = 'surface_%s'% str(node).replace(' ', '_')
                name = name.replace('_','-')
            else:
                formValues['perMol']=1
                name = 'MSMS-MOL'

            #print 'AAAAA perMol',  formValues['perMol']

            # find last parameters used to compute this surface
            try:
                srf = mol.geomContainer.msms[name][0]
                lastValues = {
                    'pRadius': srf.probeRadius,
                    'density': srf.density,
                    'perMol': srf.perMol,
                    'surfName': srf.surfName,
                    'noHetatm': srf.noHetatm,
                    'hdset': srf.hdset,
                    'hdensity': srf.hdensity,
                    }
            except KeyError:
                lastValues = {}

            if val: # if button is on we might have to re-compute
                recompute = False
                if len(lastValues)==0: # surface was not computed yet
                    recompute=True
                elif isinstance(node, SelectionWithButtons):
                    # if the node is the current selection, the selection might
                    # have changed and we have to recompute the surface
                    recompute=True
                else: # compare last parameters with ones in form
                    for k,v in lastValues.items():
                        nv = formValues.get(k, None)
                        if nv!=v:
                            #print 'MSMS recompute: new param', k, nv, v
                            recompute=True
                            break

                if recompute:
                    formValues['surfName']=name
                    formValues['display']=False
                    #print 'computing MSMS surface', formValues
                    self.vf.computeMSMS( *(atoms,), **formValues)
                    srf = mol.geomContainer.msms[name][0]
            #mem1 = misc.memory()
            # endif val

            # display/undisplay
            pmvcmd = self.vf.displayMSMS
            # MS sept 2011: calling doit reduces memory leak and speeds up
            # but we lose undo capability
            #pmvcmd.doit(atoms, negate=not val, surfName=name)
            pmvcmd(atoms, negate=not val, callListener=False, surfName=name)

            #mem2 = misc.memory()
            #print "MSMS %4.2f %4.2f %4.2f %4.2f %4.2f"%(
            #    (mem1-mem0)/MB, (mem2-mem1)/MB, mem0/MB, mem1/MB, mem2/MB)


    # override MSMScol.optMenu_cb
    def optMenu_cb(self, node, column, event=None):

        # get status of clicked button (1:full, 0:empty or partial)
        #val = node.chkbtval[column]
        #if val==1: # button is on --> right click does nothing
        #    return
        cmd = self.vf.computeMSMS
        
        if isinstance(node, SelectionWithButtons):
            # not a molecule but a set
            name = 'surface_%s'% str(node).replace(' ', '_')
            name = name.replace('_','-')
        else:
            name = 'MSMS-MOL'
        
        values = cmd.showForm(posx=event.x_root, posy=event.y_root)
        
        if len(values)==0: return # Cancel was pressed
        values = cmd.fixValues(values)
        cmd.lastUsedValues['default'].update(values)
        node.buttonClick(column, val=1)


displayMSMSColDescr = MSMSColumnDescriptor(
    'compute/display Molecular Surface', ('displayMSMS', (), {}),
    buttonColors=['white', '#FF4F44'], title='MS',
    color='#333333', pmvCmdsToHandle = [],#'displayMSMS', 'computeMSMS'],
    pmvCmdsToLoad = [('displayMSMS', 'msmsCommands', 'Pmv'),
                     ('computeMSMS', 'msmsCommands', 'Pmv')],
    buttonBalloon='Display/Undisplay molecular surface for %s',
    onButtonBalloon='display molecular surface for %s',
    offButtonBalloon='undisplay molecular surface for %s')
ColumnDescriptors.append(displayMSMSColDescr)
   

from mglutil.gui.BasicWidgets.Tk.colorWidgets import ColorChooser

class ColorColumnDescriptor(MVColumnDescriptor):
    """
    Column with a menu when I click on a button
    """
    def __init__(self, name, cmd, **kw):

        MVColumnDescriptor.__init__(self, name, cmd, **kw)
        self.onOnly = self.postMenu
        self.cbOn = self.postMenu
        self.cbOff = None
        self.carbonOnly = Tkinter.IntVar()

        
    def execute(self, node, colInd):
        self.postMenu(node, colInd)


    def enableDisableColorCmdEntries(self):
        # disable menu entries if no geom is selected
        geomsToColor=[k for k,v in self.geomsVar.items() if v.get()]
        if len(geomsToColor)==0:
            state = 'disable'
        else:
            state = 'normal'

        conly = self.carbonOnly.get()
        for entry in ['By atom type', 'By polarity (David Goodsell)']:
            lstate = state
            if conly:
                lstate = 'disable'
            try:
                self.menu.entryconfig(entry, state=lstate)
            except Tkinter.TclError:
                pass
            
        for entry in ['By molecule', 'By chain',
                      'By residue type (Rasmol)',
                      'By residues type (Shapely)',
                      'By instance', 'By rainbow',
                      'By rainbow (per chain)',
                      'By secondary structure',
                      'Custom color']:
            try:
                self.menu.entryconfig(entry, state=state)
            except Tkinter.TclError:
                pass # happens for 'Chains by Rainbow' which is only in the
                     # menu for molecule entries to dashboard

    def handleFilterButtons(self):
        self.enableDisableColorCmdEntries()
        self.menu.post(self.menu.winfo_x(), self.menu.winfo_y())
        
    def handleCheckButtons(self, value):
        if value=='all':
            # toggle all check buttons
            val = self.allGeomsVar.get()
            [w.set(val) for w in self.geomsVar.values()]
        else:
            # toggle a check button
            var = self.geomsVar[value]
            var.set( var.get() )

        # repost menu in same location
        self.enableDisableColorCmdEntries()
        self.menu.post(self.menu.winfo_x(), self.menu.winfo_y())


    def colorChooser_cb(self, objects):
        geomsToColor=[k for k,v in self.geomsVar.items() if v.get()]
        if len(geomsToColor)==0:
            # repost menu in same location
            self.menu.post(self.menu.winfo_x(), self.menu.winfo_y())
            return

        def cb(color, objects=objects, geomsToColor=geomsToColor):
            for node, objlist in objects.items():
                for obj in objlist: # each node has [AtomSet, ResidueSet, ...]
                    if len(obj)==0: continue
                    if self.carbonOnly.get():
                        #obj = obj.findType(Atom).get('C*')
                        obj = AtomSet(
                            [x for x in obj.findType(Atom) if x.element=='C'])
                    self.vf.color(obj, [color], geomsToColor)

        name = str([str(o) for o in objects.keys()])
        cc = ColorChooser(immediate=1, commands=cb,
                          title='Color %s for %s'%(str(geomsToColor), name))

        cc.pack(expand=1, fill='both')


    def color_cb(self, cmd, objects):
        geomsToColor=[k for k,v in self.geomsVar.items() if v.get()]
        if len(geomsToColor)==0:
            # repost menu in same location
            self.menu.post(self.menu.winfo_x(), self.menu.winfo_y())
            return
        for node, objlist in objects.items():
            for obj in objlist: # each node has [AtomSet, ResidueSet, ...]
                if len(obj)==0: continue

                if cmd not in [self.vf.colorByAtomType,
                               self.vf.colorAtomsUsingDG,
                               self.vf.colorBySecondaryStructure] and \
                               self.carbonOnly.get():
                    #obj = obj.findType(Atom).get('C*')
                    obj = AtomSet(
                        [x for x in obj.findType(Atom) if x.element=='C'])

                cmd(obj, geomsToColor=geomsToColor)
        

    def colorChainsByRainbow(self, obj, geomsToColor=None):
        if hasattr(obj, 'chains'):
            for chain in obj.chains:
                self.vf.colorRainbow(chain, geomsToColor=geomsToColor)
        else:
            chains = obj.findType(Chain).uniq()
            for c in chains:
               atms = c.findType(Atom) & obj.findType(Atom)
               self.vf.colorRainbow(atms, geomsToColor=geomsToColor)
            

    def getVisibleGeoms(self, objects):
        geoms = {}
        for node, objlist in objects.items():
            for objs in objlist: # each node has [AtomSet, ResidueSet, ...]
                if len(objs)==0: continue

                for ob in objs:
                    gc = ob.top.geomContainer
                    for name, ats in gc.atoms.items():
                        if gc.geoms.has_key(name) and gc.geoms[name].visible \
                               and len(ats):
                            if name[:4] in ['Heli', 'Stra', 'Turn', 'Coil']:
                                geoms['secondarystructure'] = True
                            elif name in ['bonded', 'nobnds', 'bondorder']:
                                geoms['lines'] = True
                            else:
                                geoms[name] = True
                        
        return geoms.keys()

        
    def postMenu(self, node, colInd, val, event=None):
##         tree = self.tree
##         if len(tree.selectedNodes)>0:
##             tree.clearSelection()
            
        # called upon right click
        obj = node.getObjects(colInd) # what to cmd will apply to
##         obj = obj[node][0]
##         if val==0:
##             return
##         obj = node.getObjects(colInd) # what to cmd will apply to

##         if isinstance(obj, list): # for sets
##             obj = obj[0]

        menu = Tkinter.Menu(tearoff=False)

        # put entries to select geometry to color
        visibleGeoms = self.getVisibleGeoms(obj)

        if len(visibleGeoms)==1:
            varVal = 1
        elif len(visibleGeoms)==2 and 'sticks' in visibleGeoms and \
             'balls' in visibleGeoms:
            varVal = 1
        else:
            varVal = 0
            
        self.allGeomsVar = Tkinter.IntVar()
        self.allGeomsVar.set(varVal==1)
        self.geomsVar = {}

        menu.add_command(label='Geometry', command=None, state='disable',
                         font=('Helvetica', 12, 'bold'))
        if len(visibleGeoms)>1:
            cb = CallbackFunction( self.handleCheckButtons, 'all')
            menu.add_checkbutton(label='All Representations',
                                 variable=self.allGeomsVar,
                                 command=cb)

        for geom in visibleGeoms:
            v = self.geomsVar[geom] = Tkinter.IntVar()
            v.set(varVal)
            cb = CallbackFunction( self.handleCheckButtons, geom)
            menu.add_checkbutton(label=geom, variable=v, command=cb)

        menu.add_separator()

        menu.add_command(label='Filter', command=None, state='disable',
                         font=('Helvetica', 12, 'bold'))
        # add check button  for carbon only
        #cb = CallbackFunction( menu.post, event.x_root, event.y_root)
        menu.add_checkbutton(label='Carbon only', variable=self.carbonOnly,
                             command=self.handleFilterButtons)

        menu.add_separator()
        # add color command unaffected by carbon only

        menu.add_command(label='Color Scheme', command=None, state='disable',
                         font=('Helvetica', 12, 'bold'))

        cb = CallbackFunction( self.color_cb, self.vf.colorByAtomType, obj )
        menu.add_command(label='By atom type', command=cb)

        cb = CallbackFunction( self.color_cb, self.vf.colorAtomsUsingDG, obj )
        menu.add_command(label='By polarity (David Goodsell)', command=cb)

        cb = CallbackFunction( self.color_cb, self.vf.colorByMolecules, obj )
        menu.add_command(label='By molecule', command=cb)

        cb = CallbackFunction( self.color_cb, self.vf.colorByChains, obj )
        menu.add_command(label='By chain', command=cb)

        cb = CallbackFunction( self.color_cb, self.vf.colorByResidueType, obj )
        menu.add_command(label='By residue type (Rasmol)', command=cb)

        cb = CallbackFunction( self.color_cb, self.
                               vf.colorResiduesUsingShapely, obj )
        menu.add_command(label='By residues type (Shapely)', command=cb)

        cb = CallbackFunction( self.color_cb, self.vf.colorByInstance, obj )
        menu.add_command(label='By instance', command=cb)

        cb = CallbackFunction( self.color_cb, self.vf.colorRainbow, obj)
        menu.add_command(label='By rainbow', command=cb)

        added = False
        for ob in obj.values():
            for o in ob:
                if isinstance(o, MoleculeSet) or isinstance(ob, ProteinSet):
                    cb = CallbackFunction( self.color_cb,
                                           self.colorChainsByRainbow, obj)
                    menu.add_command(label='By rainbow (per chain)', command=cb)
                    added = True
                    break
            if added is True:
                break

        mols = {}
        for ob in obj.values():
            mols.update( {}.fromkeys([o.top for o in ob]) )
            
        for m in mols.keys():
            if hasattr(m, 'builder'): # there is a ribbon
                cb = CallbackFunction( self.color_cb,
                                       self.vf.colorBySecondaryStructure, obj )
                menu.add_command(label='By secondary structure', command=cb)
                break
            
        # add color command that work with carbon only
        cb = CallbackFunction( self.colorChooser_cb, obj)
        menu.add_command(label='Custom color', command=cb)


        menu.add_separator()
        
        menu.add_command(label='Dismiss')

        menu.post(event.x_root, event.y_root)
        self.menu = menu
        self.enableDisableColorCmdEntries()


    def optMenu_cb(self, node, column, event=None):
        pass # to avoid traceback on color menu right click

    
    def displayOptions(self, cmd, obj, event):
        values = cmd.showForm(posx=event.x_root, posy=event.y_root,
                              master=self.tree.master)
        if values and len(values)==0: return # Cancel was pressed
        cmd.lastUsedValues['default'].update(values)
        cmd( *(obj,), **values)

         

colorMenuColDescr = ColorColumnDescriptor(
    'color', [None], buttonColors=['white', 'white'],
    buttonShape='downTriangle',
    inherited=False, title='Cl',
    iconfile='dashboardColorIcon.jpg',
    buttonBalloon="""display coloring menu for representations of %s""",
)
ColumnDescriptors.append(colorMenuColDescr)



class LabelColumnDescriptor(MVColumnDescriptor):
    """
    Column with a menu when I click on a button
    """
    def __init__(self, name, cmd, **kw):

        MVColumnDescriptor.__init__(self, name, cmd, **kw)
        self.onOnly = self.postMenu
        self.cbOn = self.postMenu
        self.cbOff = None # self.postMenu # nothing on right click 

            
    def optMenu_cb(self, node, column, event=None):
        pass # to avoid traceback on color menu right click


    def execute(self, node):
        self.postMenu(node, colInd, label=True)


    def handleRadioButtons(self, obj):
        if self.labelVar.get():
            self.kw['negate'] = False
            self.menu.delete('All')
        else:
            self.kw['negate'] = True
            cb = CallbackFunction( self.label_cb, self.unlabelAll, obj, 0)
            self.menu.insert(self.menu.index('Dismiss')-1,
                             'command', label='All', command=cb)
 
        # repost menu in same location
        self.menu.post(self.menu.winfo_x(), self.menu.winfo_y())


    def label_cb(self, cmd, objects, useProp=1):
        # when lines in dashboard are selected objects has one entry per line
        if not useProp:
            del self.kw['properties']
        for node,objlist in objects.items():
            for objs in objlist: # each node has [AtomSet, ResidueSet, ...]
                if len(objs)==0: continue
                
                cmd(objs, **self.kw)


    def postMenu(self, node, colInd, label=True, event=None):
        #tree = self.tree
        #if len(tree.selectedNodes)>0:
        #    tree.clearSelection()
            
        # called upon right click
        obj = node.getObjects(colInd) # what to cmd will apply to
        #obj = obj[node][0]
##         obj = node.getObjects(colInd) # what to cmd will apply to
##         if isinstance(obj, list): # for sets
##             obj = obj[0]

        self.kw = {'properties':["name"]}
            
        menu = Tkinter.Menu(tearoff=False)

        self.labelVar = Tkinter.IntVar()
        self.labelVar.set(1)
        cb = CallbackFunction( self.handleRadioButtons, obj)
        menu.add_radiobutton(label='Label', variable=self.labelVar,
                             value=1, command=cb)
        menu.add_radiobutton(label='Unlabel', variable=self.labelVar,
                             value=0, command=cb)

        menu.add_separator()

        cb = CallbackFunction( self.label_cb, self.vf.labelAtoms, obj)
        menu.add_command(label='Atoms', command=cb)
        
        cb = CallbackFunction( self.label_cb, self.vf.labelResidues, obj)
        menu.add_command(label='Residues', command=cb)

        cb = CallbackFunction( self.label_cb, self.vf.labelChains, obj)
        menu.add_command(label='Chains', command=cb)

        cb = CallbackFunction( self.label_cb, self.vf.labelMolecules, obj)
        menu.add_command(label='Molecules', command=cb)
        menu.add_separator()

        cb = CallbackFunction( self.label_cb, self.vf.labelAtomsFull, obj, 0)
        menu.add_command(label='Atoms full name', command=cb)
        
        cb = CallbackFunction( self.label_cb, self.vf.labelResiduesFull, obj, 0)
        menu.add_command(label='Residues full name', command=cb)

        cb = CallbackFunction( self.label_cb, self.vf.labelChainsFull, obj, 0)
        menu.add_command(label='Chains full name', command=cb)

        menu.add_separator()
        menu.add_command(label='Dismiss')
        menu.post(event.x_root, event.y_root)
        self.menu = menu


    def unlabelAll(self, obj, **kw):
        self.vf.labelAtoms(obj, **kw)
        self.vf.labelResidues(obj, **kw)
        self.vf.labelChains(obj, **kw)
        self.vf.labelMolecules(obj, **kw)
        self.vf.labelAtomsFull(obj, **kw)
        self.vf.labelResiduesFull(obj, **kw)
        self.vf.labelChainsFull(obj, **kw)


labelMenuColDescr = LabelColumnDescriptor(
    'label', [None], buttonColors=['white', 'white'],
    buttonShape='downTriangle',
    inherited=False, title='L',
    pmvCmdsToLoad = [('labelAtoms', 'labelCommands', 'Pmv'),                  
                     ('labelResidues', 'labelCommands', 'Pmv'),
                     ('labelChains', 'labelCommands', 'Pmv'),
                     ('labelMolecules', 'labelCommands', 'Pmv')],
    iconfile='dashboardLabelIcon.jpg',
    buttonBalloon="""display labeling menu for %s""",
    onButtonBalloon='display labeling menu for %s',
    offButtonBalloon='display unlabeling menu for %s'
    )
ColumnDescriptors.append(labelMenuColDescr)



colAtColDescr = MVColumnDescriptor(
    'color by atom types', ('colorByAtomType', (), {}),
    title='Atom', color='magenta',
    pmvCmdsToHandle = ['colorByAtomType'],
    pmvCmdsToLoad = [('colorByAtomType', 'colorCommands', 'Pmv')],
    btype='button', buttonShape='diamond', )
ColumnDescriptors.append(colAtColDescr)


colMolColDescr = MVColumnDescriptor(
    'color by molecule', ('colorByMolecules', (), {}),
    title='Mol', color='#5B49BF',
    pmvCmdsToHandle = ['colorByMolecules'],
    pmvCmdsToLoad = [('colorByMolecules', 'colorCommands', 'Pmv')],
    btype='button', buttonShape='diamond', 
)
ColumnDescriptors.append(colMolColDescr)


colChainColDescr = MVColumnDescriptor(
    'color by chains', ('colorByChains', (), {}),
    title='Chain', color='#BF7C66',
    pmvCmdsToHandle = ['colorByChains'],
    pmvCmdsToLoad = [('colorByChains', 'colorCommands', 'Pmv')],
    btype='button', buttonShape='diamond', 
)
ColumnDescriptors.append(colChainColDescr)


colResRASColDescr = MVColumnDescriptor(
    'color by residue (RASMOL)', ('colorByResidueType', (), {}),
    title='RAS', color='purple',
    pmvCmdsToHandle = ['colorByResidueType'],
    pmvCmdsToLoad = [('colorByResidueType', 'colorCommands', 'Pmv')],
    btype='button', buttonShape='diamond', 
)
ColumnDescriptors.append(colResRASColDescr)


colResSHAColDescr = MVColumnDescriptor(
    'color by residue (SHAPELY)', ('colorResiduesUsingShapely', (), {}),
    title='SHA', color='#333333',
    pmvCmdsToHandle = ['colorResiduesUsingShapely'],
    pmvCmdsToLoad = [('colorResiduesUsingShapely', 'colorCommands', 'Pmv')],
    btype='button', buttonShape='diamond', 
)
ColumnDescriptors.append(colResSHAColDescr)


colDGColDescr = MVColumnDescriptor(
    'color by DG', ('colorAtomsUsingDG', (), {}),
    title='DG', color='#268E23',
    pmvCmdsToHandle = ['colorAtomsUsingDG'],
    pmvCmdsToLoad = [('colorAtomsUsingDG', 'colorCommands', 'Pmv')],
    btype='button', buttonShape='diamond', 
)
ColumnDescriptors.append(colDGColDescr)


colInstColDescr = MVColumnDescriptor(
    'color by instance', ('colorByInstance', (), {}),
    title='Inst.', color='black',
    pmvCmdsToHandle = ['colorByInstance'],
    pmvCmdsToLoad = [('colorByInstance', 'colorCommands', 'Pmv')],
    btype='button', buttonShape='diamond', 
)
ColumnDescriptors.append(colInstColDescr)


colSSColDescr = MVColumnDescriptor(
    'color by second. struct.', ('colorBySecondaryStructure', (), {}),
    title='Sec.\nStr.', color='magenta',
    pmvCmdsToHandle = ['colorBySecondaryStructure'],
    pmvCmdsToLoad = [('colorBySecondaryStructure',
                      'secondaryStructureCommands', 'Pmv')],
    btype='button', buttonShape='diamond', 
)
ColumnDescriptors.append(colInstColDescr)


## ColDescr = MVColumnDescriptor(
##     '', ('', (), {}),
##     title='', color='',
##     pmvCmdsToHandle = [''],
##     pmvCmdsToLoad = [('', 'colorCommands', 'Pmv')],
##     btype='button', buttonShape='diamond', 
## )
## ColumnDescriptors.append(ColDescr)


## cmds = [
##     ('color by atom types', 'Atom', 'colorByAtomType', (), {},
##      'magenta', 'colorCommands'),
##     ('color by molecule', 'Mol', 'colorByMolecules', (), {},
##      '#5B49BF', 'colorCommands'),

##     ('color by chains', 'Chain', 'colorByChains', (), {},
##      '#BF7C66', 'colorCommands'),
##     ('color by residue (RASMOL)', 'RAS',
##      'colorByResidueType', (), {}, 'purple', 'colorCommands'), 

##     ('color by residue (SHAPELY)', 'SHA',
##      'colorResiduesUsingShapely', (), {}, '#333333', 'colorCommands'),
##     ('color by DG', 'DG', 'colorAtomsUsingDG',(), {}, '#268E23',
##      'colorCommands'),
##     ('color by instance', 'Inst.', 'colorByInstance', (), {},
##      'black', 'colorCommands'),
##     ('color by second. struct.', 'Sec.\nStr.',
##      'colorBySecondaryStructure', (), {}, 'magenta',
##      'secondaryStructureCommands'),
## ]

## for name, title, cmd, args, opt, color, mod in cmds:
##     descr = MVColumnDescriptor(
##         name, (cmd, args, opt), title=title, color=color,
##         btype='button', buttonShape='diamond', 
##         pmvCmdsToHandle = [cmd],
##         pmvCmdsToLoad = [(cmd, mod, 'Pmv')]
##         )
##     ColumnDescriptors.append(descr)

# MS I think this funciton is not OBSOLETE
def loadAllColunms(mv):
    print ' HUMM it actually gets called !'
    raise
    # adding columns to dashboard
    mv.dashboardSuspendRedraw(True)

    mv.addDashboardCmd(visibilityColDescr, log=0)
    mv.addDashboardCmd(selectColDescr, log=0)
    mv.addDashboardCmd(displayLinesColDescr, log=0)
    mv.addDashboardCmd(displaySandBColDescr, log=0)
    mv.addDashboardCmd(displayCPKColDescr, log=0)
    mv.addDashboardCmd(displaySSColDescr, log=0)
    mv.addDashboardCmd(displayMSMSColDescr, log=0)
    #mv.addDashboardCmd(labelColDescr, log=0)
    #mv.addDashboardCmd(colAtColDescr, log=0)
    #mv.addDashboardCmd(colMolColDescr, log=0)
    #mv.addDashboardCmd(colChainColDescr, log=0)
    #mv.addDashboardCmd(colResRASColDescr, log=0)
    #mv.addDashboardCmd(colResSHAColDescr, log=0)
    #mv.addDashboardCmd(colDGColDescr, log=0)
    #mv.addDashboardCmd(colSSColDescr, log=0)
    #mv.addDashboardCmd(colInstColDescr, log=0)
    mv.addDashboardCmd(colorMenuColDescr, log=0)
    mv.addDashboardCmd(labelMenuColDescr, log=0)
    
    mv.dashboardSuspendRedraw(False)
    mv.GUI.ROOT.update()
    # set dahboard size
    mv.dashboard.setNaturalSize()


def moveTreeToWidget(oldtree, master, vf):
    # save columns
    columns = oldtree.columns

    # get handle to root node
    rootnode = oldtree.root

    # get handle to tree's objectToNode dict
    objToNode = oldtree.objectToNode
    selectedNodes = oldtree.selectedNodes
    
    # destroy docked tree
    oldtree.undisplay()
    oldtree.destroy()

    # create new tree
    tree = oldtree.__class__(master, rootnode, vf=vf, selectionMode='multiple')

    # change all references to Tree
    oldtree.reparentNodes(tree)

    tree.selectedNodes = selectedNodes
    tree.objectToNode = objToNode
    
    # put the columns back. This needs to be done by hand
    # because addColumnDescriptor appends a chkbtval and resets nodes
    tree.columns = columns
    tree.nbCol = len(columns)
    for i,c in enumerate(columns):
        tree.createColHeader(c, i)
        c.tree = tree

    tree.pack(expand=1, fill="both")
    tree.updateTreeHeight()
    return tree
