## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

"""
This module implements the following classes
Command   : base class to implement commands for application derived from
           ViewerFramework.
           
CommandGUI: class describing the GUI associated with a command.
            (menu, button etc...)

ICOM      : Base class to implement Picking command for application dercived
            from ViewerFramework. Picking command are bound to the picking event.

"""

# $Header: /opt/cvs/python/packages/share1.5/ViewerFramework/VFCommand.py,v 1.99.2.1 2011/06/22 21:27:46 sargis Exp $
#
# $Id: VFCommand.py,v 1.99.2.1 2011/06/22 21:27:46 sargis Exp $
#

import numpy.oldnumeric as Numeric
import os, types, string, Tkinter,Pmw, warnings #, webbrowser
import tkMessageBox
from time import time, sleep
##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr

from mglutil.util.callback import CallBackFunction
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser

from DejaVu.Geom import Geom
from DejaVu.colorMap import ColorMap

from mglutil.util.packageFilePath import findFilePath
ICONPATH = findFilePath('Icons', 'ViewerFramework')
ICONSIZES = {
    'very small':'16x16',
    'small':'22x22',
    'medium':'32x32',
    'large':'48x48',
    'very large':'64x64',
    }


class ActiveObject:
    """An ActiveObject is an object that is capable to call a number of
    functions whenever it changes, These function take 2 arguments, newValue
    and oldValue.

    WARNING: the callback function should NOT trigger setting of the value.
    If it did the program goes into an endless loop.
    """

    def __init__(self, value, type=None):
        self.value = value
        self.type = type
        self.callbacks = []
        self.private_threadDone = None # lock used commands running in threads

    def waitForCompletion(self):
        # used for commands running in threads
	while (1):
	   if not  self.private_threadDone.locked():
               return
	   sleep(0.01)


    def AddCallback(self, callback):
        """Add a callback fuction"""

        assert callable(callback)
        # Here we should also check that callback has exactly 2 arguments
        self.callbacks.append(callback)


    def FindFunctionByName(self, funcName, funcList):
        """find a function with a given name in a list of functions"""

        for f in funcList:
            if f.__name__==funcName: return f
        return None


    def HasCallback(self, callback):
        """Check whether a function is registered as a callback for an event
        """
        if type(callback) in types.StringTypes:
            callback = self.FindFunctionByName(callback, self.callbacks)
            if callback is None: return 0
        assert callable(callback)
        for f in self.callbacks:
            if f==callback: return 1
        return 0


    def RemoveCallback(self, func):
        """Delete function func from the list of callbacks for eventType"""

        if type(func)==type('string'):
            func = self.FindFunctionByName(func, self.callbacks )
            if func is None: return

        self.callbacks.remove(func)


    def Set(self, value):
        oldvalue = self.value
        self.value = value
        self.callCallbacks(value, oldvalue)


    def callCallbacks(self, value, oldvalue):
        for f in self.callbacks:
            f(value, oldvalue)



class ICOM:
    """Mixin class used to specify that a command is usable interactively,
    i.e. be called for each picking operation
    """

    def __init__(self):
        self.pickLevel = 'vertices'

        
    def getObjects(self, pick):
        return pick.hits


    def initICOM(self, modifier):
        """gets called when the ICOM is registered using the set method of the
        interactiveCommandCaller."""
        pass

    
    def startICOM(self):
        """gets called every time this command is about to be run becuase
        of a picking event. It is called just before the Pick is converted into
        objects."""
        pass

    
    def stopICOM(self):
        """gets called when this command stops being bound to picking
        here one should withdraw forms mainly"""
        pass

    
#
# We still have the problem of not being able to pick vertices and parts
# at the same time. This implies that interactive commands assigned to
# some modifiers might not get called is the picking level isnot right
#
class InteractiveCmdCaller:
    """Object used to bind interactive commands to picking operations.
- self.commands is a dictionnary: modifier:cmd.
- self.pickerLevel reflects and sets the DejaVu picking level to 'vertices' or
'parts'.
- self.getObject is a function called with the pick object to return a list of
picked objects.
    """

    def __init__(self, vf):
        self.vf = vf # viewer application
        # commands for pick (i.e button down and up without move)
        self.commands = ActiveObject({None:None, 'Shift_L':None,
                                      'Control_L':None, 'Alt_L':None})
        # commands for pick (i.e button down and up after move)
        self.commands2 = ActiveObject({None:None, 'Shift_L':None,
                                      'Control_L':None, 'Alt_L':None})
        self.getObjects = None
        self.currentModifier = None
        self.running = 0


    def _setCommands(self, command, modifier=None, mode=None):
        if command:
            assert isinstance(command, ICOM)

        if mode == 'pick':
            ao = self.commands
        elif mode == 'drag select':
            ao = self.commands2
        else:
            raise ValueError("ERROR: mode can only be 'pick' or 'drag select' got %s"%mode)
        
        if ao.value[modifier]:
            ao.value[modifier].stopICOM()
            oldvalue = ao.value[modifier]
        else:
            oldvalue = None

        if command:
            command.initICOM(modifier)
            ao.value[modifier] = command
        elif oldvalue:
            ao.value[modifier]= None
            
        ao.callCallbacks(command, modifier)


    def setCommands(self, command, modifier=None, mode=None):
        if mode is None:
            self._setCommands(command, modifier, 'pick')
            self._setCommands(command, modifier, 'drag select')
        else:
            self._setCommands(command, modifier, mode)
        

    def go(self):
        if self.running: return
        self.running = 1
        if self.vf.hasGui:
            vi = self.vf.GUI.VIEWER
            vi.SetPickingCallback(self.pickObject_cb)


    def pickObject_cb(self, pick):
        # self.getObjects was set in ViewerFramework.DoPick
        if pick.mode=='pick':
            cmd = self.commands.value[self.currentModifier]
        else:
            cmd = self.commands2.value[self.currentModifier]
        if cmd:
            cmd.startICOM()
            objects = cmd.getObjects(pick)
            if objects and len(objects):
                self.execCmd(objects, cmd)

        
    def execCmd(self, objects, cmd):
        # self.currentModifer was set in ViewerFramework.DoPick
        #cmd = self.commands.value[self.currentModifier]
        #if cmd:
        if hasattr(cmd, 'getLastUsedValues'):
            defaultValues = cmd.getLastUsedValues('default')
        else:
            defaultValues = {}
        # ignore lastusedValue of negate as it might have been set by
        # control panel and in interactive commands we do call the
        # display or undisplay, slect or deselect command explicitly
        if defaultValues.has_key('negate'):
            del defaultValues['negate']
        cmd( *(objects,), **defaultValues)
        #cmd(objects)



class CommandGUI:
    """Object allowing to define the GUI to be associated with a Command object.
    Currently there are two possible types of GUI:
    either menu type or button type. The Command class provides a method
    'customizeGUI' allowing individual commands to configure their GUI
    """

    menuEntryTypes = ['command', 'cascade', 'checkbutton', 'radiobutton']
                     
    def __init__(self):
        # menu related stuff
        self.menu = None
        self.menuBar = None
        self.menuButton = None
        self.menuCascade = None
        self.menuDict = {}
        #self.menuBarCfg = {'borderwidth':2, 'relief':'raised'}
        self.menuBarCfg = {'borderframe':0, 'horizscrollbar_width':7,
                           'vscrollmode':'none', 'frame_relief':'groove',
                           'frame_borderwidth':0,}

        self.menuBarPack = {'side':'top', 'expand':1, 'fill':'x'}
        self.menuButtonCfg = {}
        self.menuButtonPack = {'side':'left', 'padx':"1m"}
        self.menuEntryLabelCfg = {}

        # checkbutton related stuff
        self.checkbutton = None
        #self.checkbuttonBarCfg = {'borderwidth':2, 'relief':'raised'}
        self.checkbuttonBarCfg = {'borderframe':0, 'horizscrollbar_width':7,
                                  'vscrollmode':'none',
                                  'frame_relief':'raised',
                                  'frame_borderwidth':0,}
        self.checkbuttonBarPack = {'side':'bottom', 'expand':1, 'fill':'x'}
        self.checkbuttonCfg = {}
        self.checkbuttonPack = {'side':'left', 'padx':"1m"}
        self.checkbuttonDict = {}
        
        # radiobutton related stuff
        self.radiobutton = None
        #self.radiobuttonBarCfg = {'borderwidth':2, 'relief':'raised'}
        self.radiobuttonBarCfg = {'borderframe':0, 'horizscrollbar_width':7,
                                  'vscrollmode':'none',
                                  'frame_relief':'raised',
                                  'frame_borderwidth':0,}

        self.radiobuttonBarPack = {'side':'bottom', 'expand':1, 'fill':'x'}
        self.radiobuttonCfg = {}
        self.radiobuttonPack = {'side':'left', 'padx':"1m"}
        self.radiobuttonDict = {}
        
        # button related stuff
        self.button = None
        #self.buttonBarCfg = {'borderwidth':2, 'relief':'raised'}
        self.buttonBarCfg = {'borderframe':0, 'horizscrollbar_width':7,
                           'vscrollmode':'none', 'frame_relief':'raised',
                           'frame_borderwidth':0,}
        self.buttonBarPack = {'side':'bottom', 'expand':1, 'fill':'x'}
        self.buttonCfg = {}
        self.buttonPack = {'side':'left', 'padx':"1m"}
        self.buttonDict = {}
        
        # Distionary holding Toolbar related stuff
        self.toolbarDict = {}
        
        # toplevel related stuff
        # toplevel related stuff
        #there may be more than one
        self.topLevels = []
        self.registered = False

    def addCheckbutton(self, BarName, ButtonName, cb=None ):
        self.checkbuttonDict['barName'] = BarName
        self.checkbuttonDict['buttonName'] = ButtonName
        self.checkbuttonDict['cb'] = cb
        self.checkbutton = (self.checkbuttonBarCfg, self.checkbuttonBarPack,
                            self.checkbuttonCfg, self.checkbuttonPack,
                            self.checkbuttonDict )
        

    def addRadiobutton(self, BarName, ButtonName, cb=None ):
        self.radiobuttonDict['barName'] = BarName
        self.radiobuttonDict['buttonName'] = ButtonName
        self.radiobuttonDict['cb'] = cb
        self.radiobutton = (self.radiobuttonBarCfg, self.radiobuttonBarPack,
                            self.radiobuttonCfg, self.radiobuttonPack,
                            self.radiobuttonDict )


    def addButton(self, BarName, ButtonName, cb=None ):
        self.buttonDict['barName'] = BarName
        self.buttonDict['buttonName'] = ButtonName
        self.buttonDict['cb'] = cb
        self.button = (self.buttonBarCfg, self.buttonBarPack,
                            self.buttonCfg, self.buttonPack,
                            self.buttonDict )

    def addMenuCommand(self,
                       menuBarName,
                       menuButtonName,
                       menuEntryLabel,
                       cb=None,
                       index = -1,
                       cascadeName = None,
                       menuEntryIndex=None,
                       menuEntryType='command',
                       separatorAbove=0,
                       separatorBelow=0,
                       separatorAboveCascade=0,
                       separatorBelowCascade=0,
                       before=None,
                       after=None,
                       image=None,
                       cascadeIndex=-1,
                       cascadeBefore=None,
                       cascadeAfter=None,
                       ):
        """Add a menu item"""
        
        assert menuEntryType in self.menuEntryTypes
        if cb is not None: assert callable(cb)
        
        self.menuDict['menuBarName']= menuBarName
        self.menuDict['menuButtonName']= menuButtonName
        self.menuDict['menuEntryLabel']= menuEntryLabel
        self.menuDict['menuCascadeName']= cascadeName
        self.menuDict['menuEntryType'] = menuEntryType
        self.menuDict['separatorAbove'] = separatorAbove
        self.menuDict['separatorBelow'] = separatorBelow
        self.menuDict['separatorAboveCascade'] = separatorAboveCascade
        self.menuDict['separatorBelowCascade'] = separatorBelowCascade
        self.menuDict['cb'] = cb
        self.menuDict['index'] = index
        self.menuDict['before'] = before
        self.menuDict['after'] = after
        self.menuDict['image'] = image
        self.menuDict['cascadeIndex'] = cascadeIndex
        self.menuDict['cascadeBefore'] = cascadeBefore
        self.menuDict['cascadeAfter'] = cascadeAfter

        self.menu = (self.menuBarCfg, self.menuBarPack,
                     self.menuButtonCfg, self.menuButtonPack,
                     self.menuEntryLabelCfg, self.menuDict )

    def addToolBar(self, name, cb=None, icon1=None, icon2=None,  
                   icon_dir=ICONPATH,
                   type='Checkbutton', 
                   radioLabels=None,
                   radioValues=None,
                   radioInitialValue=None,
                   state='normal', variable=None,
                   balloonhelp='', index=0):
        """Adds a Toolbar item"""
        self.toolbarDict['name'] = name
        self.toolbarDict['cb'] = cb
        self.toolbarDict['icon1'] = icon1
        self.toolbarDict['icon2'] = icon2
        self.toolbarDict['icon_dir'] = icon_dir
        self.toolbarDict['type'] = type
        self.toolbarDict['state'] = state
        self.toolbarDict['balloonhelp'] = balloonhelp
        self.toolbarDict['index'] = index
        self.toolbarDict['variable'] = variable
        self.toolbarDict['radioLabels'] = radioLabels
        self.toolbarDict['radioValues'] = radioValues
        self.toolbarDict['radioInitialValue'] = radioInitialValue
        if radioLabels and radioValues:
            assert len(radioLabels) == len(radioValues)


    def register(self, viewer, cmd=None):
        if not viewer.hasGui: return
        cb = None
        if cmd:
            self.cmd = cmd
            cmd.GUI = self
            cb = cmd.guiCallback

        if self.registered: return
        if self.menu is not None:
            viewer.GUI.addCommandMenuGUI(self, cb)

        if self.checkbutton is not None:
            viewer.GUI.addCheckbuttonMenuGUI(self, cb)

        if self.button is not None:
            viewer.GUI.addButtonMenuGUI(self, cb)

        if self.radiobutton is not None:
            viewer.GUI.addradiobuttonMenuGUI(self, cb)

        if self.toolbarDict:
            viewer.GUI.addtoolbarDictGUI(self, cb)
            
        for m in self.topLevels:
            viewer.GUI.addCommandToplevelGUI(self)



class Command:
    """
Base class for adding commands to a Viewer derived from ViewerFramework
Classes derived from that class can be added to a viewer using the
addCommand method.
Commands are derived from the VFCommand base class and should implement or
overwrite the following methods:

    __init__(self, func=None)
        The constructor has to be overwritten to set the self.flag attribute
        properly.
        self.objArgOnly is turned on when the doit only has one required
        argument which is the current selection.
        This will automatically make this command a Picking command
        self.negateKw is turned on when the doit method takes a boolean
        flag negate which makes this command undoable.

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
        ViewerFramework.basicCommand.BrowseCommandsCommand: 
         This command creates a non modal non blocking form
         
    setLastUsedValues(self, **kw):
        This method can be used to set the values to that appear in the GUI
        
    getLastUsedValues(self):
        Returns the values fo the parameters for the command

    doit(self, *args, **kw):
        This method does the actual work. It should not implement any
        functionality that should be available outside the application
        for scripting purposes. This method should call such functions or
        object. 
        
    setUpUndo(self, *args, **kw):
        Typically this method should be implemented if the command is
        undoable. It should have the same signature than the doit and the
        __call__ method.
        
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
         
    checkDependencies():
        This method called when command is loaded. It typically checks for
        dependencies and if all the dependencies are not found the command
        won't be loaded.
        
    onAddCmdToViewer():
        (previously initCommand)
        onAddCmdToViewer is called once when a command is loaded into a
        Viewer. 
        Typically, this method :
            takes care of dependencies (i.e. load other commands that
                                        might be required)
            creates/initializes variables.
        see ViewerFramework.basicCommand.py UndoCommand for an example
            
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
        
    onRemoveObjectFromViewer(self, obj):
        In python if all references to an object are not deleted, memory
        space occupied by that object even after its deletion is not freed.
        
        This function will be called for every object removed (deleted) from
        the application.
        When references to an object are created inside a command which are
        not related to the geomContainer of the object, in order to prevent
        memory leak this command has to implement an onRemoveObjectFromViewer
        to delete those references.

    onCmdRun(self, cmd, *args, **kw):
        if the list in self.vf.cmdsWithOnRun[cmd] holds this command, each
        time cmd runs command.onCmdRun will be called if callListener is true
        
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

If a command generates geometries to be displayed in the camera, it is
expected to create the geometry objects and add them to the appropriate
GeometryContainer.  The geometry should be be added to the molecule's geometry
container using the .addGeom method of the geometry container.  If the
geoemtry should be updated uon modification events (i.e. atoms addition,
deletion or editing) the command should pass itself as the 3rd argument to
gcontainer.addGeom().  This will trigger the updateGeom method to be called
upon modification events.

    if the default modification event method is not applicable, a command can
    overwrite it.
    
    def updateGeom(self, event, geomList):
        the event is a ViewerFramework.VF.ModificationEvent instance
        geomList is a list of geometries to be updated

        check out Pmv/mvCommand for an example of updateGeom working for
        several Pmv display commands
         
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
    objArgOnly = 1
    negateKw = 2
    
    def __init__(self, func=None):
        self.vf=None
        self.GUI=None
        self.name = ''
        self.lastCmdLog = []
        self.undoCmds = ''
        self.flag = 0
        self.busyCursor = 'watch'
        self.timeUsedForLastRun = 0. # -1 when command fails
        self.cmdForms = {}
        if func: self.func = func
        else: self.func = self.doit
        self.lastUsedValues = {} # key is formName, values is dict of defaults
        self.lastUsedValues['default'] = self.getValNamedArgs()

        # initialize list of callbacks which are called in beforeDoit()
        # and afterDoit()
        self.callbacksBefore = []  # contains tuples of (method, args, kw)
        self.callbacksAfter = []   # contains tuples of (method, args, kw)

        self.managedGeometries = [] # list of geometries 'owned' by this
                                    # command, used in updateGeoms
        self.createEvents = True # set to False to avoid command from issuing events
        self.undoStack = [] # SD Oct 2010 
        # self.undoStack stores objects needed to perform undo. 
        # This replaces the need to store nodes and string representation for the undo log.     
        
    def setLastUsedValues(self, formName='default', **kw):
        form = self.cmdForms.get(formName, None)
        values = self.lastUsedValues[formName]
        for k,v in kw.items():
            if values.has_key(k):
                values[k] = v
                if form is None:
                    values[k] = v
                else:
                    widget = form.descr.entryByName[k]['widget']
                    if hasattr(widget, 'set'):
                        widget.set(v)
                    elif hasattr(widget, 'setvalue'):
                        widget.setvalue(v)
                    elif hasattr(widget, 'selectitem'):
                        widget.selectitem(v)
                    elif hasattr(widget, 'invoke'):
                        try:
                            widget.invoke(v)
                        except:
                            widget.invoke()
                    else:
                        print "Could not set the value of ", k, v


    def getLastUsedValues(self, formName='default', **kw):
        """Return dictionary of last used values
"""
        return self.lastUsedValues[formName].copy()


    def updateGeom(self, event):
        """ Methad used to update geoemtries created by this command upon
ModificationEvents.

The event is a ViewerFramework.VF.ModificationEvent instance

check out Pmv/mvCommand for an example of updateGeom working for
several Pmv display commands
"""
        return

    
    def warningMsg(self, msg):
        """
Method to display a popup window with a warning message, the title
of the pop up window is the name of the command
        """
        title = '%s WARNING'%self.name
        self.vf.warningMsg(msg, title=title)
    
    def getValNamedArgs(self):
        """
         """
        from inspect import getargspec
        args = getargspec(self.__call__.im_func)
        allNames = args[0][1:]
        defaultValues = args[3]
        if defaultValues is None:
            defaultValues = []
        nbNamesArgs = len(defaultValues)
        posArgsNames = args[0][1:-nbNamesArgs]
        d = {}
        for name, val in zip(args[0][-nbNamesArgs:], defaultValues):
            d[name] = val
        return d

    #def __repr__(self):
    #    return 'self.'+self.name

    
    def onAddCmdToViewer(self):
        """
method called when an instance of this command is added to the
viewer. This enable viewer-addition time initializations"""
        pass


    def onAddNewCmd(self, newcommand):
        """
method called whenever a new command is added to the viewer
        """
        pass


    def onCmdRun(self, command, *args, **kw):
        """
if the list in self.vf.cmdsWithOnRun[cmd] holds this command, each
time cmd runs this method will be called
"""
        pass


    def setupUndoBefore(self, *args, **kw):
        """
This method builds the self.undoCmds string.
This method should have the same signature than the __call__.
When this string is executed it should undo the actions of this command.
This string will be appended to the undoCmdStack list if the command is successfuly
carried out.
This method handles only commands with the negateKw. Other commands
have to overwrite it.
"""

        # we handle commands that have a negate keyword argument
        if self.flag & self.negateKw:
            if kw.has_key('negate'):
                kw['negate'] = not kw['negate']
            else:
                kw['negate'] = 1
                
            if not kw['negate']: # negate off for undo ==> prefix with 'un'
                self.undoMenuStringPrefix = 'un'
            else:
                self.undoMenuStringPrefix = ''

            self.addUndoCall( args, kw, self.name )
            

    def addUndoCall(self, args, kw, name ):
        """build an undo command as a string using name as the name of the
command args and kw provide arguments to that command. The string
is appended to self.undoCmds which will be added to the undoCmdStack
by afterDoit if the command is successfully executed"""
        self.undoStack.append([args, kw])
        self.undoCmds = self.undoCmds + "self."+name+".undo()" + '\n'
        #import traceback;traceback.print_stack()

    def undo(self):
        if  self.undoStack:
            args1, kw1 = self.undoStack.pop() 
            self.doitWrapper(log=0, setupUndo=0, *args1, **kw1)
        else: 
            self.doitWrapper(log=0, setupUndo=0) 
        
    def setupUndoAfter(self, *args, **kw):
        """A chance to modify self.undoCmds after the command was carried
        out"""
        pass

    
    def beforeDoit(self, args, kw, log, setupUndo, busyIdle, topCommand):
        """called before specialized doit method is called"""
        if self.vf.hasGui: 
            if busyIdle:
                self.vf.GUI.busy(self.busyCursor)

            if log and topCommand:
                w1 = self.vf.showHideGUI.getWidget('MESSAGE_BOX')
                if w1.winfo_ismapped():
                    if self.lastCmdLog and log:
                        self.vf.message( self.lastCmdLog[-1] )

        if setupUndo and self.vf.userpref['Number of Undo']['value']>0:
            apply( self.setupUndoBefore, args, kw )

        # call callbacks
        for cb, args, kw in self.callbacksBefore:
            if callable(cb):
                apply(cb, args, kw)


    def afterDoit(self, args, kw, setupUndo, busyIdle):
        """called after specialized doit method is called"""
        # calls the cleanup methods after the doit has been called.
        self.cleanup()

        if self.vf.hasGui: 
            if busyIdle:
                self.vf.GUI.idle()
            if kw.has_key('redraw') :
                if kw['redraw']: self.vf.GUI.VIEWER.Redraw()

        # call callbacks
        for cb, args, kw in self.callbacksAfter:
            if callable(cb):
                apply(cb, args, kw)


    def doitWrapper(self, *args, **kw):
        """wrapper of doit() to call beforeDoit and afterDoit()"""

        self.undoCmds = ''

        if kw.has_key('redraw'):
            redraw = kw['redraw']
            del kw['redraw']
        else:
            redraw = 0
            
        # when called with topCommand=0, then  log=0, busyIdle=0 and
        # setupUndo=0
        if kw.has_key('topCommand'):
            topCommand = kw['topCommand']
            del kw['topCommand']
        else:
            topCommand = 1

        if kw.has_key('createEvents'):
            self.createEvents = kw.pop('createEvents')
        
        if topCommand: log = setupUndo = busyIdle = 1
        else: log = setupUndo = busyIdle = 0

        callListener = 1
        
        if kw.has_key('log'):
            log = kw['log']
            del kw['log']
                
        if kw.has_key('callListener'):
            callListener = kw['callListener']
            del kw['callListener']
                
        if kw.has_key('setupUndo'):
            setupUndo = kw['setupUndo']
            del kw['setupUndo']

        if kw.has_key('busyIdle'):
            busyIdle = kw['busyIdle']
            del kw['busyIdle']

        # build log string here because will be messaged to gui
        if log and self.vf.hasGui:
            w1 = self.vf.showHideGUI.getWidget('MESSAGE_BOX')
            if w1.winfo_ismapped():
                kw['log']=0
                logst = apply( self.logString, args, kw)
                if logst is None:
                    log = False
                else:    
                    self.lastCmdLog.append(logst)
                del kw['log']

        # initialize the progress bar, set it to 'percent' mode
        if self.vf.hasGui and busyIdle:
            self.vf.GUI.VIEWER.currentCamera.pushCursor('busy')
            gui = self.vf.GUI
            gui.configureProgressBar(mode='percent', labeltext=self.name)
            gui.updateProgressBar(progress=0) # set to 0%
       
        self.beforeDoit(args, kw, log, setupUndo, busyIdle, topCommand)

        # Update self.lastUsedValues
        defaultValues = self.lastUsedValues['default']
        for key, value in kw.items():
            if defaultValues.has_key(key):
                defaultValues[key] = value

        t1 = time()
        result = apply( self.vf.tryto, (self.func,)+args, kw )
        t2 = time()

        # call onCmdRun of listeners
        #if callListener and self.vf.cmdsWithOnRun.has_key(self):
        #    for listener in self.vf.cmdsWithOnRun[self]:
        #        apply( listener.onCmdRun, (self,)+args, kw ) 

        # after run, set the progress bar to 100% and write 'Done'
        if self.vf.hasGui and busyIdle:
            # Need to set the mode of your progress bar to percent
            # so that once the command is done it always displays Done 100%.
            # This is done because of floating value problems.
            gui.configureProgressBar(labeltext='Done', mode='percent',
                                     progressformat='percent')
            if gui.progressBar.mode == 'percent':
                gui.updateProgressBar(progress=100) # set to 100%
            
        if result != 'ERROR':
            self.timeUsedForLastRun = t2 - t1
            kw['redraw'] = redraw

            if topCommand and log:
                self.vf.addCmdToHistory( self, args, kw)

            if log and self.vf.logMode != 'no':
                kw['log'] = log
                if self.lastCmdLog:
                    # Only log if self.lastCmdLog is not None.
                    self.vf.log( self.lastCmdLog[-1])
                    self.lastCmdLog.remove(self.lastCmdLog[-1])

            if setupUndo and self.vf.userpref['Number of Undo']['value']>0:
                apply( self.setupUndoAfter, args, kw )
                if  len(self.undoCmds)>0:
                    name = self.undoMenuStringPrefix+self.undoMenuString
                    self.vf.undo.addEntry( self.undoCmds, name )
        else:
            self.timeUsedForLastRun = -1.

        self.vf.timeUsedForLastCmd = self.timeUsedForLastRun

        if self.vf.hasGui and busyIdle:
            self.vf.GUI.VIEWER.currentCamera.popCursor()

        if self.vf.hasGui and self.vf.GUI.ROOT is not None:
            t = '%.3f'%self.vf.timeUsedForLastCmd
            self.vf.GUI.lastCmdTime.configure(text=t)
        
        self.afterDoit(args, kw, setupUndo, busyIdle)
        return result
    

    def doit(self, *args, **kw):
        """virtual method. Has to be implemented by the sub classes"""
        pass

    def cleanup(self, *args, **kw):
        """ virtual method. Has to be implemented by sub classes if some
        things need to be clean up after doit has been executed.
        Will be called by doitWrapper"""
        pass
    
    def checkDependencies(self, vf):
        """virtual method. Has to be implemented by the sub classes.
        Method called when command is loaded, if all the dependencies are
        not found the command won't be loaded."""
        pass

        
    def strArg(self, arg):
        before = ""
        if type(arg) is types.ListType or type(arg) is types.TupleType:
            seenBefore = {} # used to save only once each before line needed
            if type(arg) is types.ListType:
                argstr = "["
                endstr = "], "
            else:
                argstr = "("
                endstr = ",), "
            for a in arg:
                astr, before = self._strArg(a)
                argstr += astr
                if before is not None:
                    seenBefore[before] = True
            # if condition is needed to fix bug #734 "incomplete log string"
            if len(argstr) > 1:
                argstr = argstr[:-2]+endstr
            else:
                argstr = argstr+endstr
            for s in seenBefore.keys():
                before += s+'\n'
            return argstr, before
        elif type(arg) is types.DictionaryType:
            seenBefore = {} # used to save only once each before line needed
            # d = {'k1':5, 'k2':6, 'k3':7, 'k8':14}
            argstr = "{"
            endstr = "}, "
            if len(arg)==0:
                #special handling for empty dictionary
                return "{}, ", before
            for key, value in arg.items():
                astr, before = self._strArg(key)
                if before is not None:
                    seenBefore[before] = True
                argstr += astr[:-2] + ':'
                astr, before = self._strArg(value)
                if before is not None:
                    seenBefore[before] = True
                argstr += astr[:-2] + ','
            argstr = argstr[:-1]+endstr
            return argstr, before
        else: # not a sequence
            return self._strArg(arg)
        
        
    def _strArg(self, arg):
        """
        Method to turn a command argument into a string,
FIXME describe what types of arguments are handled
        """
        from mglutil.util.misc import isInstance
        if type(arg)==types.ClassType:
            before = 'from %s import %s'%(arg.__module__, arg.__name__)
            return arg.__name__+', ', before

        #elif type(arg)==types.InstanceType:
        elif isInstance(arg) is True:
            if isinstance(arg, Command):
                return 'self.'+arg.name+', ', None
            elif isinstance(arg, Geom):
                return "'"+arg.fullName+"', ", None
            elif isinstance(arg, ColorMap):
                return "'"+arg.name+"', ", None
            elif hasattr(arg, 'returnStringRepr'):
                # the returnStringRepr method has to be implemented by
                # the instance class and needs to return
                # the before string which can be None but usually is the
                # from module import class string
                # and the argst which is also a string allowing the
                # instanciation of the object.
                before, argst = arg.returnStringRepr()
                return argst+', ', before

            try:
                import cPickle
                pickle = cPickle
                before = 'import cPickle; pickle = cPickle'
            except:
                import pickle
                before = 'import pickle'
                self.vf.log( before )
            sp = pickle.dumps(arg)
            # Add a \ so when the string is written in a file the \ or \n
            # are not interpreted.
            pl1 =  string.replace(sp, '\\', '\\\\')
            picklelog = string.replace(pl1, '\n', '\\n')
            return 'pickle.loads("' + picklelog + '"), ', before

        elif type(arg) in types.StringTypes:
            arg1 = string.replace(arg, '\n', '\\n')
            if string.find(arg, "'") != -1:
                return '"'+ arg1 + '",', None
            else:
                return "'" + arg1 + "', ", None

        elif type(arg)==Numeric.ArrayType:
            before = 'from numpy.oldnumeric import array\n'
            #arg = arg.tolist()
            return repr(arg)+ ', ', before

        else:
            return str(arg) + ', ', None

    # FIXME seems unnecessary, one can simply override the strarg method
##     def getLogArgs(self, args, kw):
##         """hook for programers to modify arguments before they get logged"""
##         return args, kw


    def buildLogArgList(self, args, kw):
        """build and return the log string representing the arguments
        a list of python statements called before is also built. This list
        has to be exec'ed to make sure the log can be played back"""
        if self.vf is None: return
        argString = ''
##         args, kw = self.getLogArgs( args, kw )
        before = []
        for arg in args:
            s, bef = self.strArg(arg)
            argString = argString + s
            if bef is not None: before.append(bef)
        for name,value in kw.items():
            s, bef = self.strArg(value)
            argString = argString + '%s=%s'%(name, s)
            if bef is not None: before.append(bef)
        return '('+argString[:-2]+')', before # remove last ", "
    

    def logString(self, *args, **kw):
        """build and return the log string"""

        argString, before = self.buildLogArgList(args, kw)
        log = ''
        for l in before: log = log + l + '\n'
        log = log + 'self.' + self.name + argString
        return log

    
    # this method will disappear after all commands are updated
    def log(self, *args, **kw):
        """
        Method to log a command.
        args provides a list of positional arguments.
        kw is a dictionary of named arguments.
        """
        import traceback
        traceback.print_strack()
        print 'VFCommand.log STILL USED'
        
        if self.vf.logMode == 'no': return
        logStr = apply( self.logString, args, kw)
        self.vf.log( logStr )
        

    def __call__(self, *args, **kw):
        """None <- commandName( *args, **kw)"""
        return apply( self.doitWrapper, args, kw)


    def tkCb(self, event=None):
        """Call back function for calling this command from a Tkevent
        for instance key combinations"""
        self()


    def getArguments(self, *args, **kw):
        """This is where GUIs can be used to ask for arguments. This function
        shoudl always return a tuple (args and a dictionary kw)"""
        if self.flag & self.objArgOnly:
            args = (self.vf.getSelection(),)
        else:
            args = ()
        return args, kw

    
    def guiCallback(self, event=None, log=None, redraw=None):
        """Default callback function called by the gui"""
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

    def getHelp(self):
        modName = self.__module__
        pName = modName.split('.')[0]
        path = __import__(modName).__path__[0]
        docDir = os.path.split(path)[0]
        cName = '%s'%self.__class__
        docHTML = '%s-class.html'%cName
        docPath = os.path.join(docDir, 'doc')
        if not os.path.exists(docPath):
            urlHelp = "http://mgltools.scripps.edu/api/"
            urlHelp += "%s"%modName.split('.')[0]
            urlHelp = urlHelp + "/" + docHTML
        else:
            urlHelp = os.path.join(docPath, docHTML)
        return urlHelp
            
    def showForm(self, formName='default', force=0, master=None, root=None,
                 modal=1, blocking=0, defaultDirection='row',
                 closeWithWindow=1, okCfg={'text':'OK'},
                 cancelCfg={'text':'Cancel'}, initFunc=None,
                 scrolledFrame=0, width=100, height=200,
                 okcancel=1, onDestroy=None, okOnEnter=False, help=None, posx=None, posy=None):
        """
val/form <- getUserInput(self, formName, force=0, master=None, root=None,
                         modal=1, blocking=0, defaultDirection='row',
                         closeWithWindow=1, okCfg={'text':'OK'},
                         cancelCfg={'text':'Cancel'}, initFunc=None,
                         scrolledFrame=0, width=100, height=200,
                         okcancel=1, onDestroy=None, help=None,
                         posx=None, posy=None)

MAKE SURE that the list of arguments passed to showForm is up to date
with the list of arguments of the InputForm constructor.
showForm will return either the dictionary of values (name of the widget: value
of the widget) if the form has a OK/CANCEL button or the form object itself.

required arguments:
    formName -- String which will be given to buildFormDescr. It refers to
                the name of the inputform to be created.

optional arguments :
    master  -- container widget or the master of the widget to be created
               which means that the current form will be a 'slave' of the
               given master if None is specified then self.vf.GUI.ROOT
               
    root    -- if root is not specified a Tkinter.TopLevel will
               be created.

    modal   -- Flag specifying if the form is modal or not. When a form
               is modal it grabs the focus and only releases it when the
               form is dismissed. When a form is modal an OK and a CANCEL
      button will be automatically added to the form.
      (default = 1)

    blocking -- Flag specifying if the form is blocking or not. When set to
      1 the form is blocking and the calling code will be stopped until the
      form is dismissed. An OK and a CANCEL button will be automatically
      added to the form. (default = 0)

    defaultDirection -- ('row', 'col') specifies the direction in
      which widgets are gridded  into the form by default. (default='row')

    closeWithWindow -- Flag specifying whether or not the form should be
      minimized/maximized  when the master window is. (default=1)

    okCfg -- dictionnary specifying the configuration of the OK button.
             if a callback function is specified using the keyword
             command this callback will be added to the default callback
             Ok_cb

    cancelCfg -- dictionnary specifying the configuration of the CANCEL button
             if a callback function is specified using the keyword
             command this callback will be added to the default callback
             Ok_cb

    initFunc  -- specifies a function to initialize the form.

    onDestroy -- specifies a function to be called when using the close
       widget of a window.

    okcancel -- Boolean Flag to specify whether or not to create the OK and
               CANCEL
                button.
    scrolledFrame -- Flag when set to 1 the main frame is a scrollable frame
                     else it is static Frame (default 0)
    width -- specifies the width of the main frame (400)
    height -- specifies the height of the main frame. (200)
    help   -- specifies the web adress to a help page. If this is provided
              a Help (?) button will be created which will open a
              web browser to the given adress.
              By default help URL is:
              http://www.scripps.edu/~sanner/software/help/PACKNAME/doc/moduleName.html#guiCallback
              Which is the documentation generated by Happydoc from the
              code's documentation strings.
    posy posy position wher the form is displayed
         """
        from mglutil.gui.InputForm.Tk.gui import InputForm, InputFormDescr
        if self.vf.hasGui:
            if self.cmdForms.has_key(formName) and force == 1:
                self.cmdForms[formName].destroy()
                del self.cmdForms[formName]
            
            if not self.cmdForms.has_key(formName):
                formDescription = self.buildFormDescr(formName)
                if formDescription is None:
                    val = {}
                    return val

                if master==None:
                    master = self.vf.GUI.ROOT
                if help is None:
                    help = self.getHelp()

                form = InputForm(master, root, formDescription, modal=modal,
                                 blocking=blocking,
                                 defaultDirection=defaultDirection,
                                 closeWithWindow=closeWithWindow,
                                 okCfg=okCfg, cancelCfg= cancelCfg,
                                 scrolledFrame=scrolledFrame,
                                 width=width,height=height,initFunc=initFunc,
                                 okcancel=okcancel, onDestroy=onDestroy,
                                 help=help, okOnEnter=okOnEnter)

                if posx and posy:
                    form.root.geometry("+%d+%d"%(posx,posy))
                else:
                    geom = form.root.geometry()
                    # make sure the upper left dorner is visible
                    w = string.split(geom, '+')
                    changepos = 0
                    if w[1][0]=='-':
                        posx = '+50'
                        changepos=1
                    else:
                        posx = '+'+w[1]
                    if w[2][0]=='-':
                        posy ='+50'
                        changepos=1
                    else:
                        posy = '+'+w[2]
                    if changepos:
                        form.root.geometry(posx+posy)
                self.cmdForms[formName] = form
                if not (modal or blocking):
                    form.go()
                    return form
                else:
                    values = form.go()
                    return values

            else:
                form = self.cmdForms[formName]
                form.deiconify()
                if posx and posy:
                    form.root.geometry("+%d+%d"%(posx,posy))
                else:
                    # move form to middle of ViewerFramework GUI
                    geom = self.vf.GUI.ROOT.geometry()
                    # make sure the upper left dorner is visible
                    dum,x0,y0 = geom.split('+')
                    w,h = [int(x) for x in dum.split('x')]
                    posx = int(x0)+(w/2)
                    posy = int(y0)+15
                    form.root.geometry("+%d+%d"%(posx,posy))
                if not (modal or blocking):
                    return form
                else:
                    values = form.go()
                    return values

        else:
            self.warningMsg("nogui InputForm not yet implemented")


    def buildFormDescr(self, formName):
        """
        descr <- buildFormDescr(self, formName):
        this virtual method is implemented in the classes derived from Command.
        This is where the inputFormDescr is created and the description of
        the widgets appended.
        If a command has several inputForm buildFormDescr should build all the
        inputFormDescr and you do a if / elif check to know which one to
        create.
        formName   : string name of the form corresponding to this descr.
        """
        pass
    
    def customizeGUI(self):
        """gets called by register method of the CommandGUI object after the
        gui for a command has been added to a viewer's GUI.
        It allows each command to set the configuration of the widgets in its
        GUI.

        Here is how to get to the widgets:

            # find the mneu bar name
            barName = self.GUI.menuDict['menuBarName']

            # find the bar itsel
            bar = self.vf.GUI.menuBars[barName]

            # find the button name
            buttonName = self.GUI.menuDict['menuButtonName']

            # find the button itself
            button = bar.menubuttons[buttonName]

            # find the entry name
            entryName = self.GUI.menuDict['menuEntryLabel']

            # configure the entry name
            n = button.menu
            n.entryconfig(n.index(entryName), background = 'red' )
        """
        pass


    def addCallbackBefore(self, cb, *args, **kw):
        """ add a callback to be called before the doit method is executed"""
        assert callable(cb)
        self.callbacksBefore.append( (cb, args, kw) )

    def addCallbackAfter(self, cb, *args, **kw):
        """ add a callback to be called after the doit method was executed"""
        assert callable(cb)
        self.callbacksAfter.append( (cb, args, kw) )

class CommandProxy(object):
    def __init__(self, vf, gui):
        self.command = None
        self.vf = vf
        self.gui = gui
        
    def guiCallback(self, event=None, log=None, redraw=None):
        pass
            
        
    
