###########################################################################
#
# Author: Michel F. SANNER, Yong Zhao
#
# Copyright: M. Sanner TSRI 2006
#
#############################################################################

#
# $Header
# 
# $Id
#

## BUGS
# - checkbutton canvas glides further than header at far right (when xscroll
#   is enabled)
# - order of chained command is no longer guaranteed as we use a dict
#
##   
## TODO
##
# - Support return key for jumping to next match
#   This might be doable using iterators or generators
# - support sets in selector
# - allow to embbed into Pmv GUI
# - allow somehow to select  node based on PMV selection
# - make secondary structure glyphs pickable for selection
#
#   Partially done
# - make checkbuttons reflect current state
#      labels not done yet
#      color commands do not work with undo because the undo command uses
#      self.vf.color command with a list of colors and the coloring type 
#      is lost
#
##########################################################################
##
## Tree customization  stuff
##
##########################################################################
import Tkinter, os, Pmw, types, re
from PIL import Image, ImageTk

from mglutil.gui.BasicWidgets.Tk.TreeWidget.tree import TreeView, Node, OFFSET
from mglutil.util.callback import CallbackFunction

from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Atom, AtomSet, Molecule, MoleculeSet
from MolKit.protein import Chain, ChainSet, Residue, ResidueSet, Protein, ProteinSet

from Pmv.displayCommands import DisplayCommand

class NodeWithCheckbuttons(Node):

    def __init__(self, name, object=None, mouseBinding=None,
                 hasChildren=False, firstExpand_cb=None):

        Node.__init__(self, name, object=object, mouseBinding=mouseBinding,
                      hasChildren=hasChildren, firstExpand_cb=firstExpand_cb)
        
        self.chkbtVar = []
        self.chkbt = []


    def createTkVar(self, nbColumns):
        # create all the buttons intially, so we can set the variables and keep
        # them in sync with Pmv
        for i in range(nbColumns):
            self.chkbtVar.append(Tkinter.IntVar())

            
    def displayValue(self):
        """Add things to the rigth side of the tree
"""
        if len(self.chkbtVar)==0: return
        master = self.tree.master
        canvas = self.tree.scrolledCanvas.interior()
        tree = self.tree
        dx = self.x-self.tree.offx
        level = dx/OFFSET
        col = ['gray75', 'red', 'cyan', 'green', 'yellow']

        for i in range(tree.nbColumns):
            if not tree.colHasButtton(i, self.objectKey.__class__):
                self.chkbt.append(None)
                continue

            v = self.chkbtVar[i]
            cb = CallbackFunction(self.buttonClick, self, i )
            button = Tkinter.Checkbutton(canvas, variable=v, command=cb,
                                         padx=0, pady=0,
                                         background=col[level-1],
                                         activeforeground='pink')

            self.chkbt.append(button)
            cid = canvas.create_window( 20 + self.tree.offx + 175 + i*35,
                                       self.y, window=button,
                                       width=20, height=15)
            self.canvasIDs.append(cid)

            # add secondary structure glyph
            molFrag = self.objectKey
            if isinstance(molFrag, Residue):
                if hasattr(molFrag, 'secondarystructure'):
                    ssname = molFrag.secondarystructure.name
                    if ssname[:6]=='Strand': color = '#FFF700'
                    elif ssname[:4]=='Coil': color = 'grey45'
                    elif ssname[:5]=='Helix': color = '#FF198C'
                    elif ssname[:4]=='Turn': color = 'blue'

                    cid = canvas.create_rectangle(
                        150 + self.tree.offx, self.y-10, 
                        160 + self.tree.offx, self.y+10, outline=color,fill=color)
                    self.canvasIDs.append(cid)

                    cid = canvas.create_text( 162 + self.tree.offx,
                            self.y, text=ssname, anchor=Tkinter.W)
#                                              fill=color)
                    self.canvasIDs.append(cid)

            func = tree.buttonValFunc[i]
            if func:
                func(self)


    def buttonClick(self, node, column):
        # get called for each checkbutton
        tree = node.tree
        tree.inChain = False
        tree.initCallback(node, column)
        tree.callbacks[column](node, column)
        tree.chainCommands(node, column)
        

    def getNodes(self, column):
        # return the objects associated with this node
        # handle the backbone, sidechain and both value for the command
        result = molFrag = self.objectKey

        bbmode = self.tree.bbmodevar.get()
        if bbmode=='Cmd setting':
            #print 'Cmd setting found'
            bbmode = self.tree.bbmode[column]

        #print 'bbmode in getNode', column, bbmode
        if bbmode!='All':
            if molFrag.findType(Chain)[0].isProteic():
                atoms = molFrag.findType(Atom)
                if bbmode=='Backbone':
                    result = atoms.get('backbone')
                elif bbmode=='Sidechain+CA':
                    result = atoms.get('sidechain')+atoms.get('CA')
                else:
                    result = atoms.get('sidechain')
                try:
                    return result.setClass([result])
                except KeyError:
                    return result
                    
        try:
            return result.setClass([result])
        except KeyError:
            return result
        

    def getObjects(self, column):
        # return a list of objects associated with this node and possibly
        # other seleted nodes.  For selection we return a list for each type
        # ( i.e. Atom, Residue, etc..)
        # if the node is selected, collect object from all other selected nodes
        resultAtoms = AtomSet([])
        resultResidues = ResidueSet([])
        resultChains = ChainSet([])
        resultMolecules = MoleculeSet([])
        buttonValue = self.chkbtVar[column].get()
        if self.selected:
            for node in self.tree.list_selected:
                node.chkbtVar[column].set(buttonValue)
                result = node.getNodes(column)
                obj = result[0]
                if isinstance(obj, Atom):
                    resultAtoms += result
                elif isinstance(obj, Residue):
                    resultResidues += result
                elif isinstance(obj, Chain):
                    resultChains += result
                elif isinstance(obj, Molecule) or isinstance(obj, Protein):
                    resultMolecules += result
            result = []
            if len(resultAtoms): result.append(resultAtoms)
            if len(resultResidues): result.append(resultResidues)
            if len(resultChains): result.append(resultChains)
            if len(resultMolecules): result.append(resultMolecules)
            return result
        else:
            return [self.getNodes(column)]
        

    def _matchName(self, pat):
        if self.parent:
            name = self.parentFullname.replace('|','').lower()
            if pat.match(name+(self.name).lower()):
                return self
        else:
            if pat.match(self.name.lower()):
                return self
        if self.expanded:
            for c in self.children:
                n = c._matchName(pat)
                if n: return n
        return None


class KeySelectable:
    """Adds the ability to use keystrokes to quickly select items in a list.
root has to be a widget supporting .bind .after
"""
    
    def __init__(self, root):
        self.root = root
        self.afterID = None
        self.matchString = ''
        self.lastMatchString = ''
        root.bind('<KeyPress>', self.key_cb)
        root.bind('<KeyRelease>', self.keyUp_cb)
        self.isControl = False
        self.isShift = False
        self.isAlt = False
        self.ctrlModCallback = None
        self.shiftModCallback = None
        self.altModCallback = None
        

    def timeOut(self, event=None):
        """resets self.matchCharIndex to 0, called after a short period of
        time if no new character has been typed"""
        #print 'timeout'
        self.lastMatchString = self.matchString
        self.matchString = ''
        self.matchCharIndex = 1
        self.afterID = None
        

    def keyUp_cb(self, event=None):
        if event.keysym=='Control_L' or event.keysym=='Control_R':
            self.isControl = False
        elif event.keysym=='Shift_L' or event.keysym=='Shift_R':
            self.isShift = False
        elif event.keysym=='Alt_L' or event.keysym=='Alt_R':
            self.isAlt = False

        
    def key_cb(self, event=None):
        # use key strokes to select entry in listbox
        # strokes placed within 500 miliseconds are concatenated
        #print self.matchCharIndex, '|', self.matchString, '|', event.keysym
        if event.keysym=='Control_L' or event.keysym=='Control_R':
            self.isControl = True
            return
        elif event.keysym=='Shift_L' or event.keysym=='Shift_R':
            self.isShift = True
            return
        elif event.keysym=='Alt_L' or event.keysym=='Alt_R':
            self.isAlt = True
            return

        if self.isControl:
            if self.ctrlModCallback:
                self.ctrlModCallback(event)
            return
        elif self.isShift:
            if self.shiftModCallback:
                self.shiftModCallback(event)
            return
        elif self.isAlt:
            if self.altModCallback:
                self.altModCallback(event)
            return
            
        if event.keysym=='Return':
            str = self.lastMatchString
        else:
            str = self.matchString + event.keysym
        #print str
        item = self.match(str)
        if item:
            self.selectItem(item)
            if self.afterID is not None:
                self.root.after_cancel(self.afterID)
            self.afterID = self.root.after(1000, self.timeOut)
            self.matchString = str

    # SUBCLASS THIS
    def match(self, name):
        """has to return None if no match or an object that matches"""
        return None


    def selectItem(self, item):
        """do what has to be done to show what matches the typed string"""
        print 'selecting item', item



class TreeViewWithCheckbuttons(TreeView, KeySelectable):
    """Tree Widget class
    A TreeWiget contains tree nodes (object of Class Node). 
    Each node can have children. Nodes that do have children can be expanded 
and collapsed using the + - icon placed before de nodes' icon. Each no has an 
icon and a name. It is possible to associate an arbitrary Python object to each 
node. The node in the tree is the graphical representation of the object.
"""
    def __init__(self, master=None, name='Tree', multi_choice=False,
                 width=800, height=200, treeWidth=140, treeHeight=100,
                 historyWidth=100, historyHeight=100, mode='Extended',
                 historyVisible=False,nohistory=False,
                 mouseBinding=None,obj2Node=True, displayValue=False,
                 offx=0, offy=0):

        TreeView. __init__(self, master=master, name=name,
                           multi_choice=multi_choice,
                           width=width, height=height,
                           treeWidth=treeWidth, treeHeight=treeHeight,
                           historyWidth=historyWidth,
                           historyHeight=historyHeight,
                           mode=mode, historyVisible=historyVisible,
                           nohistory=nohistory,
                           mouseBinding=mouseBinding, obj2Node=obj2Node,
                           displayValue=displayValue,
                           offx=offx, offy=offy, canvasHeaderCol=True)

        KeySelectable.__init__(self, self.canvas)
        # assign method that need to be overriden
        self.match = self.findFirstMatchNodeFromName
        self.selectItem = self.showNode
        self.ctrlModCallback = self.handleControlKey

        self.sets = None # used to save pmv.sets so that the selector can
                         # use it to allow selecting sets
        self.balloons = Pmw.Balloon(master, yoffset=0)
        
        self.inChain = False  # true when calling chained commands.
                              # used to prevent calling chained or chained
        
        nbcol = self.nbColumns = 15
        #nbcol += 10
        self.callbacks = [None]*nbcol
            # will be the list of call backs associated with
            # columns of checkbuttons
        self.names = [None]*nbcol
            # will be the list of names associated with
            # columns of checkbuttons
        self.colHeaderButtons = [None]*nbcol
        self.colHeaderTkVars = [None]*nbcol
        self.colOptionPanels = [None]*nbcol
        self.pmvcmd = [None]*nbcol
        self.chainWith = [None]*nbcol
        for i in range(nbcol):
            self.chainWith[i] = [None]*nbcol
        self.balloonText = ['No Help']*nbcol

        self.buttonValFunc = [None]*nbcol # function for getting the current values

        # force molecule visible when selecting, displaying or labeling
        # parts of molecules
        for i in range(1,9): # chains command 0 after command 1 through 9
            # 'Checked': call 0 when command 1 is checked
            # 'True': always check the button of the chained command
            # 'All': apply to the whole moelcular fragment
            self.chainWith[i][0] = ('Checked', 'True', 'All')

        # make display lines, S&B and CPK mutually exclusive
        for i in range(2,5):
            for j in range(2,5):
                if i==j: continue
                self.chainWith[i][j] = ('Checked','False','All')

        # make color commands (9-14) radio
        for i in range(9,15):
            for j in range(9,15):
                if i==j: continue
                self.chainWith[i][j] = ('Checked','False','All')

        self.bbmode = ['All']*nbcol
        self.colHeaderTkVars = [None]*nbcol # list of button in the header

        from mglutil.util.packageFilePath import findFilePath
        self.ICONPATH = os.path.abspath(findFilePath('Icons', 'Pmv'))
        self.ICONDIR = os.path.join(self.ICONPATH, '32x32')
        self.iconList = [None]*nbcol # save references to icon images to 
            # prevent them from being garbage collected

        # add the backbone menu option
        self.bbmodevar = Tkinter.StringVar()
        self.bbmodevar.set("Cmd setting")
        self.bbmode_menu = Pmw.OptionMenu(
            self.master, labelpos = 'w', label_text = 'Protein:',
        menubutton_textvariable = self.bbmodevar,
        items = ['Cmd setting', 'Backbone', 'Sidechain',
                         'Sidechains+CA', 'All'],
        menubutton_width = 8
    )
        cid = self.canvasHeaderCol.create_window(
            10, 15, window=self.bbmode_menu, anchor='w')
        self.proteinHelp = """This option menu allows to specify for peptidic molecular fragments
whether the command should be applied to the backbone atoms only,
the side chain atoms only, the sidechain atoms and CA atoms or the
full molecular frament."""
        self.balloons.bind(self.bbmode_menu, self.proteinHelp)

        # add a compound selector entry
        self.selectorEntry = Pmw.EntryField(
            self.master, labelpos = 'w', label_text = 'Select:  ',
            entry_width=12, validate = None, command=self.selectFromString)

        cid = self.canvasHeaderCol.create_window(
            10, 40, window=self.selectorEntry, anchor='w')
        self.selectorHelp = """This entry allows selecting enties in the Tree using a Pmv compound selector.
Only expanded nodes will be selected.  Selected nodes are outlined with a
yellow selection box.  When a button is checked for a selected node, the
command is applied to all selecte nodes.
The syntax for a compound selector is a ; separated list of expressions.
Each expression is a : separated list of selectors applying at the various
levels of the tree.
for instance:
    :::CA selects all carbon alpha atoms
    :A::CA selects all CA in chain A
    ::CYS* selects all cysteins"""
        self.balloons.bind(self.selectorEntry, self.selectorHelp)

        from MolKit.stringSelector import CompoundStringSelector
        self.selector = CompoundStringSelector()


    def handleControlKey(self, event):
        if event.keysym in ['z', 'Z']:
            self.undoSelect()

            
    def colHasButtton(self, column, klass):
        """returns True if a given column has check buttons for a given klass
"""
        if column==0:
            if klass not in [Molecule, Protein, MoleculeSet, ProteinSet]:
                return False
        return True
    
        
    def findFirstMatchNodeFromName(self, name):
        """walks the tree and find the first node whose fullname
matches name"""
        
        pat = re.compile('.*'+name.lower()+'.*')
        for root in self.roots:
            n = root._matchName(pat)
            if n:
                return n
        return None

        
    def selectFromString(self):
        value = self.selectorEntry.getvalue()
        allMols = self.roots[0].objectKey
        molFrag = self.selector.select(allMols, value, self.sets)
        self.selectNodes(molFrag[0])


    def setCallback(self, column, pmvcmd, iconName=None, balloonText=None,
                    name='command', function=None, bValFunc=None):
        """define a callback for the checkbuttons in a given column.
  pmvcmd is the Pmv command to run in the callback associated with the
         checkbuttons and used to get default values using the 'default form.
  name is a string describing the command in that column, defaults to cmd.name
  iconName is the name of the icon to be used for the button
  balloonText is the tooltip, defaults to name.
  function is an option callback to override the default callback.
           It gets called with  (node, column, pmvcmd)
"""
        assert column<1000


        def callback(node, column):
            # default call back
            
            # search for button because some commands do not have
            # buttons at all levels
            while node and not node.chkbt[column]:
                node = node.parent
            if node is None: return

            # get Pmv's command default arguments
            pmvcmd = node.tree.pmvcmd[column]
            defaultValues = pmvcmd.getLastUsedValues()

            # handle negate key to reflect state of checkbutton
            val = node.chkbtVar[column].get()
            if defaultValues.has_key('negate'):
                defaultValues['negate'] = not val

            defaultValues['callListener'] = False

            # apply the command at each level of the current selection
            for obj in node.getObjects(column):
                apply( pmvcmd, (obj,), defaultValues)

            if pmvcmd.lastUsedValues['default'].has_key('callListener'):
                del pmvcmd.lastUsedValues['default']['callListener']
            
        if function is None:
            function = callback

        self.callbacks[column] = function
        self.buttonValFunc[column] = bValFunc
        
        if name is None:
            if hasattr(function, 'name'):
                name = function.name
        self.names[column] = name
        self.pmvcmd[column] = pmvcmd
        if balloonText is None:
            balloonText = name
        self.balloonText[column] = balloonText
        if iconName:
            iconfile = os.path.join(self.ICONDIR, iconName)
            image = Image.open(iconfile)
            im = ImageTk.PhotoImage(image=image, master=self.master)
            self.iconList[column] = im

            v = Tkinter.IntVar() 
            cb = CallbackFunction(self.editColumn, column)
            button = Tkinter.Checkbutton(
                self.master, variable=v, command=cb, height=32, width=32,
                indicatoron=0, image=im)

            self.colHeaderButtons[column] = button
            self.colHeaderTkVars[column] = v

            cid = self.canvasHeaderCol.create_window(
                20 + self.offx + 175 + column*35, 32, window=button,
                width=40, height=40, anchor='center')

            self.balloons.bind(button, self.balloonText[column])
        else:
            cid = self.canvasHeaderCol.create_text(
                20 + self.offx + 175 + column*35, 5, text=name, anchor='n')


    def editColumn(self, column):
        if self.colHeaderTkVars[column].get()==0: # editor is shown
            self.colOptionPanels[column].hide()
        else:
            if self.colOptionPanels[column]:
                self.colOptionPanels[column].show()
            else:
                self.colOptionPanels[column] = CPCommandEditor(column, self)


    def initCallback(self, node, column):
        self.manageChildren(node, column)


    def manageChildren(self, node, column):
        # sets the checkbutton of all children to value of parent
        if len(node.children)==0:
            return

        val = node.chkbtVar[column].get()
        for c in node.children:
            c.chkbtVar[column].set(val)
            self.manageChildren(c, column)

 
    def chainCommands(self, node, column):
        if self.inChain is True:
            return
        self.inChain = True
        
        buttonValue = node.chkbtVar[column].get()
        chainWith = self.chainWith[column]

        for col in range(self.nbColumns):
            # find out with what argument this col's command should be called
            val = chainWith[col]
            if val is None: continue
            run, arg, prot = val

            if run=='Checked' and not buttonValue: continue
            if run=='Unchecked' and buttonValue: continue

            if arg=='Same': value = buttonValue
            elif arg=='Opposite': value= not buttonValue
            elif arg=='True': value= 1
            elif arg=='False': value= 0

            # temporarly overwrite protin mode
            bbmode = self.bbmodevar
            oldbbmode = bbmode.get()
            bbmode.set(prot)

            #print 'col', col, 'run', run, 'arg', arg, 'prot', prot
            if node.selected:
                for n in self.list_selected:
                    while n and not n.chkbt[col]:
                        n = n.parent
                    if n:
                        n.chkbtVar[col].set(value)
                if n:
                    self.callbacks[col](n, col)
                    self.manageChildren(n, col)
            else:
                n = node
                while n and not n.chkbt[col]:
                    n = n.parent
                if n:
                    n.chkbtVar[col].set(value)
                    self.callbacks[col](n, col)
                    self.manageChildren(n, col)

            # restore bbmode
            bbmode.set(oldbbmode)


    def addNodeTree(self, obj):
        """recursively add a nodes for a hierarchy of objects rooted at obj
"""
        node = self.addNode(obj.name, object=obj, parent=obj.parent,
                            hasChildren=len(obj.children),
                            nodeClass=NodeWithCheckbuttons)
        node.createTkVar(self.nbColumns)
        for child in obj.children:
            self.addNodeTree(child)


class CPCommandEditor:
    """Object displaying an editor panel for a given column of button.
The editor allows to set default options for the command
and to associate other columns with with this one
"""
    def __init__(self, column, tree, master=None):
        self.column = column
        self.tree = tree
        self.editable = column < 14

        if master is None:
            self.root = Tkinter.Toplevel(tree.master)
            self.root.title('Editor for command: %s'%\
                            self.tree.names[column].replace('\n', ' '))
            self.ownsRoot = True
            self.root.protocol("WM_DELETE_WINDOW",
                               tree.colHeaderButtons[column].invoke)
        else:
            self.root = master
            self.ownsRoot = False

        self.callWhenHelp = """This option menu allows to specify when to call the chained command.
The chained command can be called wither when the command's
checkbutton in the control panel is: checked, unchecked, or always
(i.e. independently of the state of the checkbuton)."""

        self.argHelp = """The option menu allows to specify how to invokd the chained command.
Chaining a command is equivalent to simulating clicking on the chained
command's checkbutton in the control panel.  Here you can control if
the chained command checkbutton should be checked, unchecked, have the
same or opposite state as the checkbutton of the command it is chained to."""
        
        self.chainHelp = """Check the button of command to be called after this command executes.
The argument passed to the chained command can be set usign the call
with option menu. Only one lvel of chaining will be carried out to
avoid endless loops."""

        self.optionHelp = """This buttons allows displays the options
panel of the corresponding Pmv command"""
        
        self.buildGUI()


    def setChain(self, chainCol, event=None):
        cmdCol = self.column
        tree = self.tree
        if self.chainVars[chainCol].get(): # button is checked
            chainWhen = self.chainWhenVars[chainCol].get()
            chainArg = self.chainArgVars[chainCol].get()
            chainProt = self.chainProtVars[chainCol].get()
            tree.chainWith[cmdCol][chainCol] = (chainWhen,chainArg,chainProt)
        else:
            tree.chainWith[cmdCol][chainCol] = None

            
    def bbmode_cb(self, tag):
    # This is called whenever the user clicks on radio button
    # in a single select RadioSelect widget.
        self.tree.bbmode[self.column] = tag


    def buildGUI(self):
        tree = self.tree

        if tree.pmvcmd[self.column]:
            b = Tkinter.Button(self.root, command=self.getOpt, height=32,
                               width=32, image=tree.iconList[self.column])
            b.grid(row=0, column=0, sticky='e')
        
            tree.optionButton = Tkinter.Button(
                self.root, text='Set default Options for command',
                command=self.getOpt)
            tree.optionButton.grid(row=0, column=1, sticky='w')
            tree.balloons.bind(tree.optionButton, self.optionHelp)
        
        self.bbmodevar = Tkinter.StringVar()
        self.bbmodevar.set("All")
        bbmode_menu = Pmw.OptionMenu(
            self.root, labelpos='w', label_text='Protein:',
            menubutton_textvariable=self.bbmodevar,
            items=['Backbone', 'Sidechain', 'Sidechains+CA', 'All'],
            menubutton_width=8, command=self.bbmode_cb,
    )
        bbmode_menu.grid(row=0, column=2, sticky='ew', padx=10, pady=10)
        tree.balloons.bind(bbmode_menu, tree.proteinHelp)

        self.chainedPanelVar = Tkinter.IntVar()
        w = Pmw.Group(self.root,
                      tag_pyclass = Tkinter.Checkbutton,
                      tag_text='show command chaining interface',
                      tag_variable=self.chainedPanelVar,
                      tag_foreground='blue')
        self.chainedPanelVar.set(0)
        w.toggle()
        self.chainedPanelGroup = w

        def toggle(event=None):
            self.chainedPanelGroup.toggle()
            if self.chainedPanelVar.get():
                self.chainedPanelGroup.configure(
                    tag_text='hide command chaining interface',
                    tag_foreground='blue')
            else:
                self.chainedPanelGroup.configure(
                    tag_text='show command chaining interface',
                    tag_foreground='blue')
                
            
        w.configure(tag_command = toggle)
#                      tag_text='Check commands to run after %s:'%\
#                      tree.names[self.column])

        w.grid(row=1, column=0, columnspan=3, sticky='ew', padx=5, pady=5)
        tree.balloons.bind(w, self.chainHelp)

        groupMaster = w.interior()

        # add argument option menu
##         self.argVar = Tkinter.StringVar()
##         self.argOptMenu = Pmw.OptionMenu(
##             groupMaster, labelpos = 'w',
##             label_text = 'Argument to be used passed to chained command:',
##             menubutton_textvariable = self.argVar,
##             items = ['N/A', 'True', 'False', 'Same', 'Opposite'],
##             menubutton_width = 10,
##             )
##         self.argOptMenu.grid(row=0, column=0, columnspan=4)

        column1 = Tkinter.Frame(groupMaster)
        column2 = Tkinter.Frame(groupMaster)
        
        self.chainVars = []
        self.chainWhenVars = []
        self.chainArgVars = []
        self.chainProtVars = []
        chainList = tree.chainWith[self.column]
        
        col = -1
        halfLength = int(round(tree.nbColumns*0.5))
        for i in range(tree.nbColumns):
            row=(i% halfLength)+1
            if row==1:
                col += 4
                master = Tkinter.Frame(groupMaster, relief='ridge')
                l = Tkinter.Label(master, text='Cmd:')
                l.grid(row=0, column=col-3)
                l = Tkinter.Label(
                  master, text='Call when cmd\nbutton is:')
                l.grid(row=0, column=col-2)
                l = Tkinter.Label(master, text='Set chained\ncmd button to:')
                l.grid(row=0, column=col-1)
                l = Tkinter.Label(master, text='Apply to:')
                l.grid(row=0, column=col)
                master.pack(side='left', padx=10, anchor='n')

            v = Tkinter.IntVar()
            self.chainVars.append(v)
            
            whenVar = Tkinter.StringVar()
            whenVar.set('Checked')
            self.chainWhenVars.append(whenVar)

            argVar = Tkinter.StringVar()
            argVar.set('Same')
            self.chainArgVars.append(argVar)

            protVar = Tkinter.StringVar()
            protVar.set('All')
            self.chainProtVars.append(protVar)

            status = 'normal'
            if i==self.column:
                status = 'disabled'
                v.set(0)
            elif chainList[i]:
                run, arg, prot = chainList[i]
                v.set(1)
                whenVar.set(run)
                argVar.set(arg)
                protVar.set(prot)
            else:
                v.set(0)

            cb = CallbackFunction(self.setChain, i)
            if tree.iconList[i]:
                b = Tkinter.Checkbutton(master, variable=v, state=status,
                                        command=cb, height=32, width=32,
                                        indicatoron=0, image=tree.iconList[i])
            else:
                l = Tkinter.Label(master, state=status,
                                  text=tree.names[i].replace('\n', ' '))
                l.grid(column=4*col-3, row=row, sticky='e')
                b = Tkinter.Checkbutton(master, variable=v, state=status,
                                        command=cb)
            b.grid(column=col-3, row=row, sticky='w')
            tree.balloons.bind(b, tree.balloonText[i])

            argMenuCall = Pmw.OptionMenu(
                master, labelpos = 'w',
                menubutton_textvariable = whenVar,
                items = ['Checked', 'Unchecked', 'Always'],
                menubutton_width = 7, command=cb
                )
            argMenuCall.grid(column=col-2, row=row, sticky='w')
            tree.balloons.bind(argMenuCall, self.callWhenHelp)
                    
            argMenuVar = Pmw.OptionMenu(
                master, labelpos = 'w',
                menubutton_textvariable = argVar,
                items = ['True', 'False', 'Same', 'Opposite'],
                menubutton_width = 6, command=cb
                )
            argMenuVar.grid(column=col-1, row=row, sticky='w')
            tree.balloons.bind(argMenuVar, self.argHelp)
                    
            argMenuVar = Pmw.OptionMenu(
                master, labelpos = 'w',
                menubutton_textvariable = protVar,
                items = ['All', 'Backbone', 'Sidechain+CA', 'Sidechain'],
                menubutton_width = 10, command=cb
                )
            argMenuVar.grid(column=col, row=row, sticky='w')
            tree.balloons.bind(argMenuVar, tree.proteinHelp)
                    

        if self.editable:
            pass
        #cmdList = ['select', 'displayLines', 'displaySticksAndBalls',
        #               'displayCPK', 'displayExtrudedSS', 'displayMSMS',
        #               'LabelAtoms', 'LabelResidues', '', ]
        self.OK = Tkinter.Button(self.root, text='OK',
                command=tree.colHeaderButtons[self.column].invoke)
        self.OK.grid(row=2, column=0, columnspan=3, sticky='ew')


    def getOpt(self):
        # FIXME what is not pmvcmd ??
        cmd = self.tree.pmvcmd[self.column]
        values = cmd.showForm()
        cmd.lastUsedValues['default'].update(values)
        return values

    
    def show(self):
        if self.ownsRoot:
            self.root.deiconify()

    def hide(self):
        if self.ownsRoot:
            self.root.withdraw()
            
        
from Pmv.mvCommand import MVCommand, MVCommandGUI

class ControlPanel(MVCommand):

    """Display a widget showing a tree representation of the molecules in the Viewer and check buttons allowing to carry out command on parts of molecules directly.
    Certain commands such as coloring or displaying lines, CPK and S&B are implmented as mutually exclusive (i.e. like radio buttons.
"""

    def hide(self):
        self.vf.GUI.toolbarCheckbuttons['Control_Panel']['Variable'].set(0)
        self.tree.master.withdraw()

    def show(self):
        self.tree.master.deiconify()


    def onAddCmdToViewer(self):
        if not self.vf.hasGui: return

        self.vf.browseCommands('displayCommands', package='Pmv', log=0)
        self.vf.browseCommands('secondaryStructureCommands', package='Pmv',
                               log=0)
        self.hasMSMS = True
        try:
            import mslib
            self.vf.browseCommands('msmsCommands', package='Pmv', log=0)
        except:
            self.hasMSMS = False

        self.vf.browseCommands('colorCommands', package='Pmv', log=0)
        self.vf.browseCommands('labelCommands', package='Pmv', log=0)
        self.vf.browseCommands('selectionCommands', package='Pmv', log=0)

        # register intrest in other commands
        self.vf.cmdsWithOnRun[self.vf.showMolecules] = [self]
        self.vf.cmdsWithOnRun[self.vf.select] = [self]
        self.vf.cmdsWithOnRun[self.vf.clearSelection] = [self]
        self.vf.cmdsWithOnRun[self.vf.displayLines] = [self]
        self.vf.cmdsWithOnRun[self.vf.displaySticksAndBalls] = [self]
        self.vf.cmdsWithOnRun[self.vf.displayCPK] = [self]
        self.vf.cmdsWithOnRun[self.vf.displayExtrudedSS] = [self]
        if self.hasMSMS:
             self.vf.cmdsWithOnRun[self.vf.displayMSMS] = [self]
        self.vf.cmdsWithOnRun[self.vf.labelByProperty] = [self]
        self.vf.cmdsWithOnRun[self.vf.colorByAtomType] = [self]
        self.vf.cmdsWithOnRun[self.vf.colorByChains] = [self]
        self.vf.cmdsWithOnRun[self.vf.colorByMolecules] = [self]
        self.vf.cmdsWithOnRun[self.vf.colorBySecondaryStructure] = [self]
        self.vf.cmdsWithOnRun[self.vf.colorAtomsUsingDG] = [self]
        self.vf.cmdsWithOnRun[self.vf.colorByResidueType] = [self]

        from Pmv.moleculeViewer import DeleteAtomsEvent, AddAtomsEvent
        self.vf.registerListener(DeleteAtomsEvent, self.handleDeleteEvents)
        self.vf.registerListener(AddAtomsEvent, self.handleAddEvents)

        # build the tree
        master = Tkinter.Toplevel()
        master.withdraw()
        master.protocol('WM_DELETE_WINDOW',self.hide)
        self.tree = tvolist = TreeViewWithCheckbuttons(
            name='Control Panel',
            displayValue=True, # needed to show buttons
            multi_choice=True,
            master = master,
            offy=0, offx=0)
        self.tree.sets = self.vf.sets

        self.msmsDefaultValues = {} #cache used to decide if we re-compute
        # custom call back function for display MSMS column
        def displayMS_cb(node, column):            
            val = node.chkbtVar[column].get()
            defaultValues = node.tree.pmvcmd[column].getLastUsedValues()
            oldDefaultValues = self.msmsDefaultValues
            recompute = False
            if len(oldDefaultValues)==0:
                recompute=True
            else:
                for k,v in oldDefaultValues.items():
                    nv = defaultValues.get(k, None)
                    if nv!=v:
                        recompute=True
                        break
            
            molat = {}
            for obj in node.getObjects(column):
                molecules, atmSets = self.vf.getNodesByMolecule(obj, Atom)
                for mol, atoms in zip(molecules, atmSets):
                    if molat.has_key(mol):
                        molat[mol] += atoms
                    else:
                        molat[mol] = atoms

            for mol, atoms in molat.items():
                if not mol.geomContainer.geoms.has_key('MSMS-MOL'):
                    recompute=True
                if len(defaultValues):
                    if defaultValues['perMol']==0 and val:
                        recompute=True
                    if type(defaultValues['surfName'])==types.TupleType:
                        defaultValues['surfName']=defaultValues['surfName'][0]

                if recompute:
                    apply( self.vf.computeMSMS, (atoms,), defaultValues)
                else:
                    pmvcmd = self.vf.displayMSMS
                    defaultValues['callListener'] = False
                    pmvcmd(atoms, negate= not val, callListener=False)
                    if pmvcmd.lastUsedValues['default'].has_key('callListener'):
                        del pmvcmd.lastUsedValues['default']['callListener']

            if recompute:
                self.msmsDefaultValues.update(defaultValues)


        def label_cb(node, column, level=Atom, property=['name']):
            val = node.chkbtVar[column].get()
            for obj in node.getObjects(column):
                nodes = obj.findType(level)
                pmvcmd = self.vf.labelByProperty
                pmvcmd(nodes, negate=not val, callListener=False,
                       properties=property)
                if pmvcmd.lastUsedValues['default'].has_key('callListener'):
                    del pmvcmd.lastUsedValues['default']['callListener']
        #    self.labelByProperty("1crn::;", textcolor=(1.0, 1.0, 1.0,), log=0, format=None, only=0, location='Center', negate=0, font='Helvetica12', properties=['name'])

        # custom callback for color commands which runs command only if
        # button is checked
        def color_cb(node, column):
            val = node.chkbtVar[column].get()
            cmd = node.tree.pmvcmd[column]
            if val:
                for obj in node.getObjects(column):
                    apply( cmd, (obj,), {'callListener':False})
                if cmd.lastUsedValues['default'].has_key('callListener'):
                    del pmvcmd.lastUsedValues['default']['callListener']
            else:
                if node.selected:
                    for node in self.tree.list_selected:
                        node.chkbtVar[column].set(0)

                
        def showHideVal(node):
            if node.name == 'All':
                return
            mols = [node.objectKey.top]

            vis = 0
            for m in mols:
                n = self.tree.objToNode[m]
                v = m.geomContainer.geoms['master'].visible
                if v:
                    vis = 1
                n.chkbtVar[0].set(v)
            #print node.name, vis  hum not sure why the following line does not work
            self.tree.roots[0].chkbtVar[0].set(vis)
            
        col = 0
        tvolist.setCallback(col, self.vf.showMolecules, 'eye.png',
                            'show/Hide molecule', bValFunc=showHideVal)
        col += 1
        tvolist.setCallback(col, self.vf.select,'select.png',
                            'select molecular fragment')

        col += 1
        tvolist.setCallback(col, self.vf.displayLines, 'lines.png',
                            'Display/Undisplay Lines representation',
                            'Display Lines')

        col += 1
        tvolist.setCallback(col, self.vf.displaySticksAndBalls, 'sb.png',
            'Display/Undisplay atoms as small spheres and bonds as cylinders',
                            'Display Sticks and Balls')

        col += 1
        tvolist.setCallback(col, self.vf.displayCPK, 'cpk.png',
                            'Display/Undisplay atoms as spheres',
                            'Display CPK')

        col += 1
        tvolist.setCallback(col, self.vf.displayExtrudedSS, 'ss.png',
                            'Display/Undisplay secondary structure',
                            'Display Ribbon', )
        if self.hasMSMS:
            col += 1
            tvolist.setCallback(col, self.vf.computeMSMS, 'ms.png',
                            'Compute and display molecular surface',
                            'Display molecular surface',
                            displayMS_cb)

        col += 1
        cb = CallbackFunction( label_cb, level=Atom)
        tvolist.setCallback(col, None, 'labelAtom.png', 'Label atoms',
                            'Label Atoms', cb)

        col += 1
        cb = CallbackFunction( label_cb, level=Residue)
        tvolist.setCallback(col, None, 'labelRes.png', 'label Residues',
                            'Label Residues', cb)

        col += 1
        tvolist.setCallback(col, self.vf.colorByAtomType, 'colorAtom.png',
                            'Color all representations by atoms type',
                            'Color by Atom Type', color_cb)
        col += 1
        tvolist.setCallback(col, self.vf.colorByChains, 'colorChain.png',
                            'Color all representations by chain',
                            'Color by Chain', color_cb)
        col += 1
        tvolist.setCallback(col, self.vf.colorByMolecules, 'colorMol.png',
                            'Color all representations by molecule',
                            'Color by Molecule', color_cb)
        col += 1
        tvolist.setCallback(col, self.vf.colorBySecondaryStructure,
                            'colorSS.png',
              'Color all representations by secondary structure element type',
                             'Color by Secondary Structure', color_cb)
        col += 1
        tvolist.setCallback(col, self.vf.colorAtomsUsingDG, 'colorDG.png',
           'Color using the David Goodsell scheme\nin which atoms are either neutral,\nor slightly or strongly charged', 'Color by D. Goodsell', color_cb)

        col += 1
        tvolist.setCallback(col, self.vf.colorByResidueType, 'colorRes.png',
            'Color all representations by residue\nusing the RASMOL coloring scheme',
                            'color Residues by Rasmol', color_cb)
        #col += 1
        #tvolist.setCallback(col, self.vf.colorResiduesUsingShapely, ....
        #                    'color\nby\nShapely')

        # add current molecules
        n = NodeWithCheckbuttons
        hasChildren = len(self.vf.Mols)>0
        node = tvolist.addNode('All', parent=None, object=self.vf.Mols,
                            nodeClass=n, hasChildren=hasChildren)
        node.createTkVar(self.tree.nbColumns)
        #if len(self.vf.Mols):
        #    self.addMolecules(self.vf.Mols)


    def addMolecules(self, mols):
        tvolist = self.tree
        n = NodeWithCheckbuttons
        hasChildren = [True]*len(mols)
        nodes = tvolist.addNodeSet(parent='All',
                           name=[m.name for m in mols], object=list(mols),
                           nodeClass=n, hasChildren=hasChildren)

        for node in nodes:
            node.createTkVar(self.tree.nbColumns)
        
        for m in mols:
            chains = m.chains
            hasChildren = [True]*len(chains)
            nodes = tvolist.addNodeSet(
                parent=m, name=chains.name, object=list(chains),
                nodeClass=n, hasChildren=hasChildren)
            for node in nodes:
                node.createTkVar(self.tree.nbColumns)
            for c in chains:
                residues = c.residues
                hasChildren = [True]*len(residues)
                nodes = tvolist.addNodeSet(
                    parent=c, name=residues.name, object=list(residues),
                    nodeClass=n, hasChildren=hasChildren)
                for node in nodes:
                    node.createTkVar(self.tree.nbColumns)
                for r in residues:
                    atoms = r.atoms
                    hasChildren = [False]*len(atoms)
                    nodes = tvolist.addNodeSet(
                        parent=r, name=atoms.name, object=list(atoms),
                        nodeClass=n, hasChildren=hasChildren)
                    for node in nodes:
                        node.createTkVar(self.tree.nbColumns)


    def guiCallback(self):
        if self.vf.GUI.toolbarCheckbuttons['Control_Panel']['Variable'].get():
            self.show()
        else:
            self.hide()
                

    def onAddObjectToViewer(self, obj):
        """
Add the new molecule to the tree
        """
        self.addMolecules([obj])
        

    def onRemoveObjectFromViewer(self, obj):    
        node = self.tree.objToNode.get(obj, None)
        if node:
            self.tree.deleteNode(node)

   
    def handleDeleteEvents(self, event):
        """Function to update tree when molecualr fragments are delete.
"""
        # split event.objects into atoms sets per molecule
        tree = self.tree
        for obj in event.objects:
            node = tree.objToNode[obj]
            tree.deleteNode(node)
        
    def handleAddEvents(self, event):
        """Function to update tree when molecualr fragments are added.
"""
        # split event.objects into atoms sets per molecule
        tree = self.tree
        for obj in event.objects:
            self.tree.addNodeTree(obj)


    def onCmdRun(self, command, *args, **kw):
        if command==self.vf.showMolecules:
            column=0
            return
        elif command==self.vf.clearSelection:
            node = self.tree.roots[0]
            node.chkbtVar[1].set(0)
            node.tree.manageChildren(node, 1)
            return
        elif command==self.vf.select:
            column = 1
            cmdType='useNegate'
        elif command==self.vf.displayLines:
            column = 2
            cmdType='useNegate'
        elif command==self.vf.displaySticksAndBalls:
            column = 3
            cmdType='useNegate'
        elif command==self.vf.displayCPK:
            column = 4
            cmdType='useNegate'
        elif command==self.vf.displayExtrudedSS:
            column = 5
            cmdType='useNegate'
        elif command==self.vf.displayMSMS:
            column = 6
            cmdType='useNegate'
        elif command==self.vf.labelByProperty:
            column = 7
            return
        elif command==self.vf.colorByAtomType:
            column = 9
            cmdType='radioGroupColor'
        elif command==self.vf.colorByChains:
            column = 10
            cmdType='radioGroupColor'
        elif command==self.vf.colorByMolecules:
            column = 11
            cmdType='radioGroupColor'
        elif command==self.vf.colorBySecondaryStructure:
            column = 12
            cmdType='radioGroupColor'
        elif command==self.vf.colorAtomsUsingDG:
            column = 13
            cmdType='radioGroupColor'
        elif command==self.vf.colorByResidueType:
            column = 14
            cmdType='radioGroupColor'

        molFrag = args[0]
        if molFrag==self.vf.Mols:
            node=self.tree.roots[0]
            if cmdType=='useNegate':
                negate = not kw['negate']
                node.chkbtVar[column].set(negate)
                node.tree.manageChildren(node, column)
            elif cmdType=='radioGroupColor':
                node.chkbtVar[column].set(1)
                node.tree.manageChildren(node, column)
                for col in range(9,15):
                    if col==column: continue
                    node.chkbtVar[col].set(0)
                    node.tree.manageChildren(node, col)
        else:
            for o in molFrag:
                if self.tree.objToNode.has_key(o):
                    node = self.tree.objToNode[o]
                else:
                    return
                if cmdType=='useNegate':
                    negate = not kw['negate']
                    node.chkbtVar[column].set(negate)
                    node.tree.manageChildren(node, column)
                elif cmdType=='radioGroupColor':
                    node.chkbtVar[column].set(1)
                    #print 'value', node.chkbtVar[column].get()
                    node.tree.manageChildren(node, column)
                    for col in range(9,15):
                        if col==column: continue
                        node.chkbtVar[col].set(0)
                        node.tree.manageChildren(node, col)
                    
                
ControlPanel_GUI = MVCommandGUI()
from moleculeViewer import ICONPATH
ControlPanel_GUI.addToolBar('Control_Panel', icon1 = 'view_tree.gif', 
                 icon_dir=ICONPATH, balloonhelp='Control Panel Widget', index=8)
            
commandList = [
    {'name':'controlPanel', 'cmd':ControlPanel(), 'gui':ControlPanel_GUI}
]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
