## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

# $Header: /opt/cvs/python/packages/share1.5/Pmv/mvCommand.py,v 1.53.2.4 2011/06/13 17:44:30 sanner Exp $
#
# $Id: mvCommand.py,v 1.53.2.4 2011/06/13 17:44:30 sanner Exp $
#

import types, numpy.oldnumeric as Numeric, warnings

from ViewerFramework.VFCommand import Command, CommandGUI, \
     InteractiveCmdCaller, ActiveObject
from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Molecule, MoleculeSet, Atom, AtomSet, BondSet
from MolKit.protein import Protein, Chain, ChainSet, Residue, ResidueSet
from mglutil.util.uniq import uniq3

# used by BindGeomToMolecularFragment
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
import Pmw, Tkinter, string
from MolKit.molecule import AtomSet, Atom

class MVInteractiveCmdCaller(InteractiveCmdCaller):
    """subclass InteractiveCmdCaller to add the concept of selection level
    This object holds a dictionary of commands and a level. Both are active
    objects.
    """

    def __init__(self, vf, level=Molecule):
        apply( InteractiveCmdCaller.__init__, (self, vf) )
        self.level = ActiveObject(level)
        self.levelColors = {
            'Atom':(1.,1.,0.),
            'Residue':(0.,1.,0.),
            'Chain':(0.,1.,1.),
            'Molecule':(1.,0.,0.),
            'Protein':(1.,0.,0.),
            }
        if self.vf.hasGui:
            for c in self.vf.GUI.VIEWER.cameras:
                c.selectionColor = self.levelColors[level.__name__]
        

    def execCmd(self, objects, cmd):
        # objects is an AtomSet
        if len(objects)==0: return
        if len(self.commands.value)==0: return

        # Add a check in case objects is not a TreeNodeSet, i.e geometry.
        if isinstance(objects, TreeNodeSet) and \
           not isinstance(objects, BondSet) :
            # change objects from atom to current selected level
            typ = self.level.value
            if typ in [Molecule, Protein]:
                nodes = objects.findType(Molecule)
                if nodes is None:
                    nodes = objects.findType(Protein)
            else:
                nodes = objects.findType(typ)
            nodes = nodes.uniq()

            # if we are not at the Atom level we have to create the
            # pickedInstances for each node
            pickedInstances = {}
            for n in nodes:
                pickedInstances[n] = []
            if self.level.value != Atom:
                for atom in objects:
                    p = atom.parent
                    while p and not isinstance(p,self.level.value):
                        p = p.parent
                    if p:
                        pickedInstances[n].extend( atom.pickedInstances )
                # now set the pickedInstances attribute for all nodes
                for n in nodes:
                    n.pickedInstances = pickedInstances[n]

        else:
            nodes = objects
        if nodes:
            InteractiveCmdCaller.execCmd(self, nodes, cmd)
        

    def setLevel(self, Klass, KlassSet=None):
        if Klass==self.vf.ICmdCaller.level.value:
            return self.vf.ICmdCaller.level.value
        self.vf.ICmdCaller.level.Set(Klass)
        if self.vf.hasGui:
            for c in self.vf.GUI.VIEWER.cameras:
                c.selectionColor = self.levelColors[Klass.__name__]


from ViewerFramework.VFCommand import ICOM

class MVICOM(ICOM):
    """Specialize ViewerFramework.VFCommand.ICOM class for a molecular viewer
    """
    pass



class MVAtomICOM(MVICOM):
    """Specialize ViewerFramework.VFCommand.ICOM class for a molecular viewer.
    use this mixin class if 
    """

    def getObjects(self, pick):
        """to be implemented by sub-class"""
        return self.vf.findPickedAtoms(pick)



class MVBondICOM(MVICOM):
    """Specialize ViewerFramework.VFCommand.ICOM class for a molecular viewer.
    use this mixin class if 
    """

    def getObjects(self, pick):
        return self.vf.findPickedBonds(pick)



class MVCommand(Command):
    """
Base class for command objects for a molecule viewer.
    
Base class for command objects for a molecule viewer
This command class derives from the ViewerFramework.VFCommand.Command class.
Classes derived from that class can be added to a MoleculeViewer using the
addCommand method.
To write a command the programmer has to create a class MyCmd derived from the
MVCommand class and should overwrite the following methods when relevant.

Information on how to write an inputForm is also available at
http://www.scripps.edu/~sanner/software/python/inputform/tableOfContent.html

    __init__(self, func=None)
        The constructor has to be overwritten to set the self.flag attribute
        properly.
        self.objArgOnly is turned on when the doit only has one required
        argument which is the current selection.
        This will automatically make this command a Picking command
        self.negateKw is turned on when the doit method takes a boolean
        flag negate which makes this command undoable.

        see Pmv.colorCommands.color command class for an example

    __call__(self, *args, **kw):
        Entrypoint to the command from the command line. It overloads
        calling the object (command) as a function, which enables calling
        an instance of a command as a method of a viewer once it it has
        been loaded.
        
        Typically, this method checks the arguments supplied and calls the
        doitWrapper method with the arguments supplied.
        
        This method needs to have the same signature than the doit.
        A documentation string supplying the following information will be
        displayed in a tooltip when calling the command from the python
        idle shell.
        This documentation string should provide the synopsis of the
        command and a description of the arguments.

        See Pmv.colorCommands.py, Pmv.displayCommands.py for good example
        of documentation string.
            
    guiCallback(self, event=None, *args, **kw):
        This method is bound by default as the callback of the GUI item
        associated with the command.
        It is the entrypoint of the command through the GUI.
        
        It typically creates an inputform allowing the user to specify any
        argument required for the command.
        The command method showForm is typically called with the name of
        the form to be created and a bunch of optional argument described
        later.
        Once all the parameters are known, the doitWrapper method is
        called to carry out the command.

        The old behavior was to call self.vf.getUserInput. The showForm method
        is a command method and replace the getUserInput method of the
        ViewerFramework. Although some commands still implement the
        getUserInput mechanism.
        
        
    buildFormDescr(self, formName):
        This method typically creates the inputform descriptor used by the
        guiCallback method to get user input for the command.
        The formName is a string which will be used as a key in the
        cmdForms dictionary to store the form information.
        This method is called by self.showForm
        This method returns an instance of an InputFormDescr which is the
        object describing a inputform in ViewerFramework.
        More information can be found in mglutil/gui/InputForm/Tk/gui.py

        For an example see:
         Pmv.secondaryStructureCommands.py module
         Almost all the PMV command implement an inputform.
        
    doit(self, *args, **kw):
        This method does the actual work. It should not implement any
        functionality that should be available outside the application
        for scripting purposes. This method should call such functions or
        object. 
        
    setUpUndo(self, *args, **kw):
        Typically this method should be implemented if the command is
        undoable. It should have the same signature than the doit and the
        __call__ method.

        See displayCommands and colorCommands for a good example 
        
Of course, one is free to overwrite any of these methods and for instance
rename doit using a more appropriate name. But, when doing so,
the programmer has to overwrite both __call__ and guiCallback to call
the right method to carry out the work.

Besides these methods which are required to be implemented in a command there
are the following optional methods:
     strArg(self, arg):
         Method to turn a command argument into a string. Used by the log
         method to generate a log string for the command.
         This method can be overwritten or extended by classes subclassing
         Command in order to handle properly instances of objects defined
         by the application when not handled properly by the base class.
         This method has been overwritten to be 'Molecule' aware.
         If you need to handle an argument a particular way this method should
         be overwritten.
         
    checkDependencies():
        This method called when command is loaded. It typically checks for dependencies and
        if all the dependencies are not found the command won't be loaded.
        See msmsCommands for an example
        
    onAddCmdToViewer():
        (previously initCommand)
        onAddCmdToViewer is called once when a command is loaded into a
        Viewer. 
        Typically, this method :
            takes care of dependencies (i.e. load other commands that
                                        might be required)
            creates/initializes variables.
        see Pmv.traceCommands.py, Pmv.secondaryStructureCommands.py etc...
            
    customizeGUI(self):
        (obsolete)
        method allowing to modify the GUI associated with a command
        
    onAddObjectToViewer(self, obj):
        (previously named initGeom)
        When a command is loaded that implements an onAddObjectToViewer
        function,this function id called for every object present in the
        application.
        Once the command is loaded, this function will be called for every
        new object added to the application.
        In general, onAddObjectToViewer is used by a command to add a new
        geometry to the geometry container of an object.
        It is also where picking events and building arrays of colors specific
        to each geometry can be registered.

        See secondaryStructureCommands, msmsCommadns etc.. for an example
        
    onRemoveObjectFromViewer(self, obj):
        In python if all references to an object are not deleted, memory
        space occupied by that object even after its deletion is not freed.
        
        This function will be called for every object removed (deleted) from
        the application.
        When references to an object are created inside a command which are
        not related to the geomContainer of the object, in order to prevent
        memory leak this command has to implement an onRemoveObjectFromViewer
        to delete those references.
        See secondaryStructureCommands for an example
        

The following methods are helper methods.
    log(self, *args, **kw):
         Method to log a command. args provides a list of positional
         arguments and kw is a dictionary of named arguments. This method
         loops over both args and kw and builds a string representation of
         their values. When a class is passed as one the arguments, an
         additional command is logged to load that class.
         This method also sets the command's lastCmdLog member.

    showForm(self, *args, **kw):
         
        If the inputForm object associated with the given formName already
        exists than it just deiconify the forms unless the force argument is
        set to true.
        Otherwise, showForm calls buildFormDescr with the given
        formName, then it creates an instance of InputForm with the given
        parameters and stores this object in the cmdForms dictionary, where
        the key is the formName and the value the InputForm object.
        (see the showForm documentation string for the description of the
        arguments)
        showForm will return the dictionary containing the values of the
        widgets if modal or blocking other it will return the form object.
        
If a command generates geometries to be displayed in the camera, it is
expected to create the geometry objects and add them to the appropriate
GeometryContainer.

A Python module implementing commands should implement the following at the
end of the file so the commands are loadable in the application using
the browseCommands command.

commandList -- which is a list of dictionaries containing the following:
               'name': command name (string) used as an alias to invoke
                       the command from the commandline.
               'cmd' : Command Class
               'gui' : Typically is a commandGUI object but can be None
                       if no GUI is associated with the Command

An initModule method
def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])

This method will be used by the browseCommands command to load the
given module into the application but also to determine which
modules implement commands.
    """
    def __init__(self, func=None):
        self.nodeLogString = None
        Command.__init__(self, func)


    def guiCallback(self,event=None, log=None, redraw=None):
        kw = {}
        if log!=None: kw['log']=log
        if redraw!=None: kw['redraw']=redraw
        args, kw = apply( self.getArguments, (), kw)
        if not kw.has_key('redraw'): kw['redraw']=1
        if not kw.has_key('log'): kw['log']=1
        if event:
            return apply( self.doitWrapper, (event,)+args, kw )
        else:
            return apply( self.doitWrapper, args, kw )

    def _strArg(self, arg):
        """
        Method to turn a command argument into a string for logging purposes
        Add support for TreeNodes and TreeNodeSets
        """
        #if type(arg)==types.InstanceType:
        from mglutil.util.misc import isInstance
        if isInstance(arg) is True:
            if issubclass(arg.__class__, TreeNode):
                return '"' + arg.full_name() + '", ', None
                
            if issubclass(arg.__class__, TreeNodeSet):
                stringRepr = arg.getStringRepr()
                if stringRepr:
                    return '"' + stringRepr + '", ', None
                else:
                    name = ""
                    mols, elems = self.vf.getNodesByMolecule(arg)
                    for elem in elems:
                        name = name + elem.full_name() +';'
                    return '"' + name + '", ', None

        return Command._strArg(self, arg)
    
##             if issubclass(arg.__class__, TreeNode) or \
##                issubclass(arg.__class__, TreeNodeSet):
##                 # 'self.getSelection()' will be used instead of the
##                 # the arg.full_name() when :
##                 #  - expandNodeLogString userpref is set to False 
##                 #  - the command objArgOnly is True
##                 #  - arg is the current selection
##                 if not self.vf.userpref['expandNodeLogString']['value'] and \
##                        self.flag & self.objArgOnly and \
##                        self.vf.selection is arg:
##                     return 'self.getSelection(), ', None
##                 else:
##                     # full_name can only create smart (i.e. short string repr)
##                     # within a single molecule, so we break args by molecule
##                     name = ""
##                     mols, elems = self.vf.getNodesByMolecule(arg)
##                     for elem in elems:
##                         name = name + elem.full_name() +';'
##                     return '"' + name + '", ', None
##             else:
##                 return Command.strArg(self, arg)
##         else:
##             return Command.strArg(self, arg)

##     def buildLogArgList(self, args, kw):
##         """build and return the log string representing the arguments
##         a list of python statements called before is also built. This list
##         has to be exec'ed to make sure the log can be played back.
##         The first argument is treated differently to cover the cases of
##         the expansion of nodes. If the attribute nodeLogString is set then
##         this string is used to build the log otherwise call strArg."""
##         if self.vf is None: return
##         argString = ''
##         args, kw = self.getLogArgs( args, kw )
##         before = []
##         if len(args)>0:
##             arg = args[0]
##             # In the case the __call__ was called with a string
##             # we don't want it to be replaced by self.getSelection
##             if not self.nodeLogString is None and \
##                type(self.nodeLogString) is types.StringType:
##                 s, bef = self.nodeLogString +",", None
##                 self.nodeLogString = None
##             else:
##                 s, bef = self.strArg(arg)
##             argString = argString + s
##             if bef is not None: before.append(bef)
        
##         for arg in args[1:]:
##             s, bef = self.strArg(arg)
##             argString = argString + s
##             if bef is not None: before.append(bef)
##         for name,value in kw.items():
##             s, bef = self.strArg(value)
##             argString = argString + '%s=%s'%(name, s)
##             if bef is not None: before.append(bef)
##         return '('+argString[:-2]+')', before # remove last ", "


class MVCommandGUI(CommandGUI):
    """Base class for GUI objects associated with MVCommands.
    """
    pass



class MVPrintNodeNames(MVCommand, MVAtomICOM):
    """Print the name of molecular fragments.  The name is a colon separated
list of string mol:chain:residue:atom.  If the geoemtry depicting the fragments
have multiple instances a list of (geom,instance) tuples is printed after the
moelcular fragment name.
"""

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        MVAtomICOM.__init__(self)
        self.flag = self.flag | self.objArgOnly


    def doit(self, nodes):
        nodes = self.vf.expandNodes(nodes)
        for n in nodes:
            msgBase = n.full_name()
            positions = []
            labels = []
            for instance in n.pickedInstances:
                if max(instance[1])>0:
                    geomNames = instance[0].fullName.split('|')                
                    msg = msgBase+'  instance: ' + \
                          str(zip(geomNames,instance[1]))
                    self.vf.message( msg )
                    lab = msg
                else:
                    self.vf.message( msgBase )
                    lab = msgBase
                if hasattr(n, 'coords'):
                    positions.append(n.coords)
                labels.append(lab)
        self.vf.flashSphere.Set(vertices=positions)
        self.vf.flashLabel.Set(vertices=positions, labels=labels)
        self.vf.flashSphere.flashT()
        self.vf.flashLabel.flashT()


    def __call__(self, nodes, topCommand=0, **kw):
        # we do not want this command to log or undo itself
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"

        if not kw.has_key('topCommand'): kw['topCommand'] = topCommand
        apply( self.doitWrapper, (nodes,), kw )



class MVCenterOnNodes(MVCommand, MVAtomICOM):
    """Set the pivot point (i.e. center of rotation) of the entire scene to
the geometric center of the picked atoms.  this command is aware of instance
matrices.
"""
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        MVAtomICOM.__init__(self)
        self.flag = self.flag | self.objArgOnly


    def doit(self, nodes):
        if len(nodes)==0:
            return 'ERROR' # prevent logging if nothing was picked
        vt = self.vf.transformedCoordinatesWithInstances(nodes)
        g = [0.,0.,0.]
        i = 0
        for v in vt:
            g[0] += v[0]
            g[1] += v[1]
            g[2] += v[2]
            i+=1
        g[0] = g[0]/i
        g[1] = g[1]/i
        g[2] = g[2]/i

        vi = self.vf.GUI.VIEWER
        if vi.redirectTransformToRoot or vi.currentObject == vi.rootObject:
            self.vf.centerGeom(vi.rootObject, g, topCommand=0, log=1, setupUndo=1)
        else:
            m = vi.currentObject.GetMatrixInverse(root=vi.currentObject)
            g.append(1.0)
            g = Numeric.dot(m, g)[:3]
            self.vf.centerGeom(vi.currentObject, g, topCommand=0, log=1, setupUndo=1)


    def __call__(self, nodes, **kw):
        # we do not want this command to log or undo itself
        kw['topCommand']=0
        kw['busyIdle']=1
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
            nodes = self.vf.expandNodes(nodes)
        apply( self.doitWrapper, (nodes,), kw )


from DejaVu.colorTool import TkColor
               
class MVSetIcomLevel(MVCommand):

    def setupUndoBefore(self, Klass, KlassSet=None):
        if not (self.vf.ICmdCaller.level.value in [Molecule, Protein] and \
           Klass in [Molecule, Protein]) and \
           self.vf.ICmdCaller.level.value != Klass:
            self.addUndoCall( (self.vf.ICmdCaller.level.value,),
                                  {'KlassSet':None}, self.name )
                
        
    def doit(self, Klass, KlassSet=None):
        #print "in MVSetIComLevel"
        if Klass is Protein: Klass = Molecule
        self.vf.ICmdCaller.setLevel(Klass, KlassSet=None)
        if hasattr(self.vf,'ICOMbar') and self.vf.hasGui:
            col =self.vf.ICmdCaller.levelColors[Klass.__name__]
            c = (col[0]/1.5,col[1]/1.5,col[2]/1.5)
            self.vf.ICOMbar.LevelOption.setvalue(Klass.__name__)
            self.vf.ICOMbar.LevelOption._menubutton.configure(
                                           background = TkColor(c),
                                           activebackground = TkColor(col))

            #self.vf.GUI.pickLabel.configure(background = TkColor(c))
            

    def __call__(self, Klass, KlassSet=None, **kw):
        """None <- setIcomLevel(Klass, KlassSet=None, **kw)
        set the current IcomLevel level 
        """
        kw['KlassSet'] = KlassSet
        apply( self.doitWrapper, (Klass,), kw)


levels = ['Molecule', 'Chain', 'Residue', 'Atom']
class MVSetSelectionLevel(MVCommand):

    def __init__(self):
        MVCommand.__init__(self)
        self.levelDict={"Molecule":Molecule,
                        "Protein":Molecule,
                        "Chain":Chain,
                        "Residue":Residue,
                        "Atom":Atom}
        self.levelColors = {
            'Atom':'yellow',
            'Residue':'green',
            'Chain':'cyan',
            'Molecule':'red',
            'Protein':'red',
            }


    def onAddCmdToViewer(self):
        if self.vf.hasGui:
            self.levelVar = Tkinter.StringVar()
            menu = self.GUI.menuButton.menu
            topMenu = Tkinter.Menu(menu)
            self.bottomMenu = Tkinter.Menu(self.vf.GUI.pickLabel, tearoff=0)
            
            for level in levels:
                topMenu.add_radiobutton(
                    label=level, variable=self.levelVar,
                    command=self.setLevel_cb,  
                    activebackground=self.levelColors[level],
                    selectcolor=self.levelColors[level])
                self.bottomMenu.add_radiobutton(
                    label=level, variable=self.levelVar,
                    command=self.setLevel_cb,  
                    activebackground=self.levelColors[level],
                    selectcolor=self.levelColors[level])
            self.bottomMenu.add_command(label='Dismiss',
                                        command=self.cancelMenu)
            menu.add_cascade(label="Set Selection Level", menu=topMenu)
            self.GUI.menuButton.menu.delete(1)

        
    def cancelMenu(self, event=None):
        self.bottomMenu.unpost()


    def popup(self, event):
        self.bottomMenu.post(event.x_root, event.y_root)


    def setupUndoBefore(self, Klass, KlassSet=None):
        if not (self.vf.selectionLevel in [Molecule, Protein] and \
           Klass in [Molecule, Protein]) and \
           self.vf.selectionLevel!= Klass:
            if len(self.vf.selection)!=0:
                # if there is a selection that will expand we add undoing
                # the selection expansion to the undo stack
                self.addUndoCall( (self.vf.selectionLevel, self.vf.getSelection()),
                                  {'KlassSet':None,}, self.name )
            else:
                self.addUndoCall( (self.vf.selectionLevel,),
                                  {'KlassSet':None}, self.name )
         
    def undo(self, **kw):
        "Customized undo that does self.svf.select if necessary"
        undoVars = self.undoStack.pop()
        if len(undoVars[0]) == 2:
            self.vf.select(undoVars[0][1], only=1, topCommand=0, setupUndo=0, log=0)
            undoVars[0] = (undoVars[0][0],)
        self.undoStack.append(undoVars)
        MVCommand.undo(self, **kw)
    
    def doit(self, Klass, KlassSet=None):
        if type(Klass)==types.StringType:
            if Klass in self.levelDict.keys():
                Klass = self.levelDict[Klass]
            else:
                msg = Klass + "string does not map to a valid level"
                self.warningMsg(msg)
                return "ERROR"
        if Klass is Protein:
            Klass = Molecule
        
        if len(self.vf.selection):
            self.vf.selection = self.vf.selection.findType(Klass).uniq()
        else:
            if Klass==Molecule: self.vf.selection = MoleculeSet([])
            elif Klass==Chain: self.vf.selection = ChainSet([])
            elif Klass==Residue: self.vf.selection = ResidueSet([])
            elif Klass==Atom: self.vf.selection = AtomSet([])

        self.vf.selectionLevel = Klass
        self.vf.ICmdCaller.setLevel(Klass, KlassSet=None)        
        if self.vf.hasGui:
            col = self.vf.ICmdCaller.levelColors[Klass.__name__]
            c = (col[0]/1.5,col[1]/1.5,col[2]/1.5)
            self.vf.GUI.pickLabel.configure(background = TkColor(c))
            msg = '%d %s(s)' % ( len(self.vf.selection),
                                 self.vf.selectionLevel.__name__ )
            self.vf.GUI.pickLabel.configure( text=msg )
            if hasattr(self.vf, 'select'):
                self.vf.select.updateSelectionIcons()
            self.levelVar.set(self.vf.selectionLevel.__name__)
            

    
    def Close_cb(self, event=None):
        self.form.withdraw()


    def guiCallback(self, event=None):
        if not hasattr(self, 'ifd'):
            self.buildForm()
        else:
            self.form.deiconify()
        selLevel = self.vf.selectionLevel
        if selLevel != TreeNodeSet:
            level = selLevel.__name__
            self.levelVar.set(level)


    def setLevel_cb(self, event=None):
        self.doitWrapper(self.levelVar.get())


    def __call__(self, Klass, KlassSet=None, **kw):
        """selectionLevel <- setSelectionLevel(Klass, KlassSet=None, **kw)
        set the current selection level and promotes current selection to
        this level
        """
        kw['KlassSet'] = KlassSet
        apply( self.doitWrapper, (Klass,), kw)


    def buildForm(self):
        ifd = self.ifd = InputFormDescr(title = "Selection level:")
        levelLabels = ['Molecule      ', 'Chain           ', 
                       'Residue       ', 'Atom           ']
        self.levelVar.set("Molecule")
        for level, levlabel in zip(levels, levelLabels):
            ifd.append({'name':level, 
                        'widgetType': Tkinter.Radiobutton,
                        'wcfg':{'text':levlabel,
                                'variable':self.levelVar,
                                'value':level,
                                'justify':'left',
                                'activebackground':self.levelColors[level],
                                'selectcolor':self.levelColors[level],
                                'command':self.setLevel_cb},
                        'gridcfg':{'sticky':'we'}})
        ifd.append({'name':'dismiss',
                    'widgetType':Tkinter.Button,
                    'defaultValue':1,
                    'wcfg':{'text':'Dismiss',
                            'command':self.Close_cb},
                    'gridcfg':{'sticky':'we'}
                    })
        self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW',self.Close_cb)
  


MVSetSelectionLevelGUI = CommandGUI()
MVSetSelectionLevelGUI.addMenuCommand('menuRoot', 'Select','Set Selection Level')


