#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
# revision: Guillaume Vareille
#
#########################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/ViewerFramework/VF.py,v 1.205.2.4 2011/10/13 17:28:43 sanner Exp $
#
# $Id: VF.py,v 1.205.2.4 2011/10/13 17:28:43 sanner Exp $
#

"""defines base classe ViewerFramework

The ViewerFramework class can be subclassed to create applications that
use a DejaVu Camera object to display 3D geometries. In the following
we'll call Viewer a class derived from ViewerFramework.

The design features of the viewer framework include:

  - extensibility: new commands can be written by subclassing the VFCommand
  base class.
  - dynamically configurable: commands (or set of commands called modules)
  can be loaded dynamically from libraries.
  - Commands loaded into an application can create their own GUI elements
  (menus, cascading menus, buttons, sliders, etc...). The viewer framework
  provides support for the creation of such GUI elements.
  - Commands can be invoked either through the GUI or throught the Python
  Shell.
  - Macros provide a lightweight mechanism to add simple commands. In fact
  any Python function can be added as a Macro
  - Support for logging of commands: this allows to record and play back a
  session.
  - documentation: the module and command documentation is provided in the
  source code. This documentation can be extracted using existing tools and
  made available in various formats including HTML and man pages. The document
  ation is also accessible through the application's Help command which uses
Python's introspection capabilities to retrieve the documentation.

A ViewerFramework always has at least one menu bar called "menuRoot" and at
least one buttonbar called "Toolbar".

The geometried displayed in a Viewer can be stored in objects derived from the
base class GeometryContainer. This container holds a dictionnary of geometries
where the keys are the geometry's name and the values instances of DejaVu
Geometries.

Commands:

Commands for an application derived from ViewerFramework can be developped by
sub-classing the VFCommand base class (see VFCommand overview).The class
VFCommandGUI allows to define GUI to be associated with a command. Command can
be added dynamically to an application using the AddCommand command of the
ViewerFramework.

    example:

        # derive a new command
        class ExitCommand(Command):
            doit(self):
                import sys
                sys.exit()

        # get a CommandGUI object
        g = CommandGUI()

        # add information to create a pull-down menu in a menu bar called
        # 'MoVi' under a menu-button called 'File' with a menu Command called
        # 'Exit'. We also specify that we want a separator to appear above
        # this entry in the menu
        g.addMenuCommand('MoVi', 'File', 'Exit', separatorAbove=1)

        # add an instance of an ExitCommand with the alias 'myExit' to a
        viewer
        # v. This will automatically add the menu bar, the menu button
        # (if necessary) the menu entry and bind the default callback function
        v.addCommand( ExitCommand(), 'myExit', g )

        The command is immediately operational and can be invoked through the
        pull down menu OR using the Python shell: v.myExit()

CommandGUI objects allow to specify what type of GUI a command should have. It
is possible to create pull-down menu entries, buttons of different kinds etc..

Modules:
    A bunch of related commands can be groupped into a module. A module is a
    .py file that defines a number of commands and provides a functions called
    initModule(viewer) used to register the module with an instance of a
    viewer.
    When a module is added to a viewer, the .py file is imported and the
    initModule function is executed. Usually this functions instanciates a
    number of command objects and their CommandGUI objects and adds them to
    the viewer.
"""

import os, string, warnings
import traceback, sys, glob, time

class VFEvent:
    """Base class for ViewerFramework events.
"""

    def __init__(self, arg=None, objects=[], *args, **kw):
        """  """
        self.arg = arg
        self.objects = objects
        if len(args):
            self.args = args
        if len(kw):
            for k,v in kw.items():
                setattr(self, k, v)
        
class AddObjectEvent(VFEvent):
    pass

class DeleteObjectEvent(VFEvent):
    pass


class LogEvent(VFEvent):
    """created each time a log string is written to the log"""

    def __init__(self, logstr):
        """  """
        self.logstr = logstr


class ModificationEvent:


    def __init__(self, action, arg=None, objects=[]):
        """  """
        self.action = action
        self.arg = arg
        self.objects = objects


class GeomContainer:
    """Class to hold geometries to be shown in a viewer.
    This class provides a dictionnary called geoms in which the name of a
    DejaVu geometry is the key to access that particular geometry object
    Geometries can be added using the addGeometry method.
    """

    def __init__(self, viewer=None):
        """constructor of the geometry container"""

        ## Dictionary of geometries used to display atoms from that molecule
        ## using sticks, balls, CPK spheres etc ...
        self.geoms = {}
        self.VIEWER = viewer # DejaVu Viewer object
        self.masterGeom = None

        ## Dictionary linking geom names to cmds which updates texture coords
        ## for the current set of coordinates
        self.texCoordsLookup = {}
        self.updateTexCoords = {}


    def delete(self):
        """Function to remove self.geoms['master'] and
        self.geoms['selectionSpheres'] from the viewer when deleted"""

        # switch the object and descendant to protected=False
        for c in self.geoms['master'].AllObjects():
            c.protected = False

        if self.VIEWER:
            self.VIEWER.RemoveObject(self.geoms['master'])
        #for item in self.geoms.values():
        #    item.delete()
        #    if item.children!=[]:
        #        self.VIEWER.RemoveObject(item)

    def addGeom(self, geom, parent=None, redo=False):
        """
This method should be called to add a molecule-specific geometry.
geom     -- DejaVu Geom instance
parent   -- parent geometry, if not specified we use self.masterGeom
"""
        if parent is None:
            parent = self.masterGeom

        # we need to make sure the geometry name is unique in self.geoms
        # and in parent.children
        nameUsed=False
        geomName = geom.name
        for object in parent.children:
            if object.name==geomName:
                nameUsed=True
                break

        if nameUsed or self.geoms.has_key(geomName):
            newName = geomName+str(len(self.geoms))
            geom.name = newName
            warnings.warn("renaming geometry %s to %s"%(geomName, newName))#, stacklevel=14)
        self.geoms[geomName]=geom

        # add the geometry to the viewer.  At this point the name should be
        # unique in both the parent geoemtry and the geomContainer.geoms dict
        if self.VIEWER:
            self.VIEWER.AddObject( geom, parent=parent, redo=redo)
        else:
            parent.children.append(geom)
            geom.parent = parent
            geom.fullName = parent.fullName+'|'+geom.name


#from DejaVu.Labels import Labels
from DejaVu.Spheres import Spheres

##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.util.callback import CallBackFunction
from mglutil.util.packageFilePath import findResourceFile, getResourceFolderWithVersion


try:
    from ViewerFramework.VFGUI import ViewerFrameworkGUI
except:
    pass

from ViewerFramework.VFCommand import Command,CommandGUI,InteractiveCmdCaller

# Import basic commands.
from ViewerFramework.basicCommand import loadCommandCommand, loadMacroCommand
from ViewerFramework.basicCommand import ShellCommand, ShellCommandGUI, ExitCommand
from ViewerFramework.basicCommand import loadModuleCommand
from ViewerFramework.basicCommand import BrowseCommandsCommand, RemoveCommand
from ViewerFramework.basicCommand import SaveSessionCommand, SaveSessionCommandGUI

from ViewerFramework.helpCommands import helpCommand

try:
    from comm import Comm
except:
    pass

from DejaVu import Viewer
from DejaVu.Camera import Camera

import types, Tkinter
import thread
import os, sys, traceback
import tkMessageBox
from mglutil.preferences import UserPreference
class ViewerFramework:
    """
    Base class for applications providing a 3D geometry Viewer based on a
    DejaVu Camera object along with support for adding GUI and commands
    dynamically.
    """
    
    def __init__(self, title='ViewerFrameWork', logMode='no',
                 libraries=[], gui=1, resourceFile = '_vfrc',
                 viewerClass=Viewer, master=None, guiVisible=1, withShell=1,
                 verbose=True, trapExceptions=True):
        """
        Construct an instance of a ViewerFramework object with:
        - an instance of a VFGUI that provides support for adding to the
          GUI of the application
        - a dictionnary of commands
        - a list of commands that create geometry
        - a list of objects to be displayed
        - a dictionary of colorMaps 

        * logMode can be:
            'no': for no loging of commands at all
            'overwrite': the log files overwrite the one from the previous
                         session
            'unique': the log file name include the date and time
        * libraries is a list of names of Python package that provide a
          cmdlib.py and modlib.py
        - trapExceptions should be set to False when creating a ViewerFramework
          for testing, such that exception are seen by the testing framework
        """

        self.hasGui = gui
        self.embeded=False
	self.cmdHistory = [] # history of command [(cmd, args, kw)]
	
        global __debug__
        self.withShell = withShell
        self.trapExceptions = trapExceptions
        self.__debug__ = 0
        # create a socket communication object
        try:
            self.socketComm = Comm()
            self.webControl = Comm()
            self.cmdQueue = None # queue of command comming from server
        except:
            self.socketComm = None
            self.webControl = None

        self.timeUsedForLastCmd = 0. # -1 when command fails

        assert logMode in ['no', 'overwrite', 'unique']
        self.resourceFile = resourceFile
        self.commands = {}    # dictionnary of command added to a Viewer
        self.userpref = UserPreference()
        #self.removableCommands = UserPreference(os.path.dirname(self.resourceFile), 'commands')
        self.userpref.add('Sharp Color Boundaries for MSMS', 'sharp', ('sharp', 'blur'),
                doc="""Specifies color boundaries for msms surface [sharp or blur]
(will not modify already displayed msms surfaces,
 only new surfaces will be affected)""", category="DejaVu")

#Warning: changing the cursor tends to make the window flash.""")

        # Interface to Visual Programming Environment, if available
        self.visionAPI = None
        if self.hasGui :
    	    try:
                    # does this package exists?
                    from Vision.API import VisionInterface
                    # create empty object. Note that this will be filled with life
                    # when the visionCommand is executed 
                    self.visionAPI = VisionInterface()
            except:
                pass

        self.objects = []     # list of objects
        self.colorMaps = {}   # available colorMaps
        self.colorMapCt = 0   # used to make sure names are unique
        self.undoCmdStack = [] # list of strings used to undo

        # lock needs to be acquired before object can be added
        self.objectsLock = thread.allocate_lock()

        # lock needs to be acquired before topcommands can be run
        self.commandsLock = thread.allocate_lock()

        # nexted commands counter
        self.commandNestingLevel = 0
        
        # place holder for a list of command that can be carried out each time
        # an object is added to the application
        # every entry is a tuple (function, args_tuple, kw_dict)
        self.onAddObjectCmds = []

        # list of commands that have an onRemoveMol
        self.cmdsWithOnAddObj = []

        # list of commands that have an onAddMol
        self.cmdsWithOnRemoveObj = []

        # dict cmd:[cm1, cmd2, ... cmdn].  When cmd runs the onCmdRun method
        # of all cmds in the list will be called with the arguments passed
        # to cmd
        self.cmdsWithOnRun = {}

        # list of commands that have an onExit 
        self.cmdsWithOnExit = []
        
        self.firstPerspectiveSet = True
        self.logMode = logMode
        self.libraries = libraries + ['ViewerFramework']

        # you cannot create a GUI and have it visible.
        if not self.hasGui:
            self.guiVisible=0
        else:
            self.guiVisible=guiVisible

        self.master=master
        if gui:
            self.GUI = ViewerFrameworkGUI(self, title=title,
                                          viewerClass=viewerClass,
                                          root=master, withShell=withShell,
                                          verbose=verbose)
            self.GUI.VIEWER.suspendRedraw = True
           
            self.viewSelectionIcon = 'cross' # or 'spheres' or 'labels'

            self.userpref.add('Show Progress Bar', 'hide',
                              ['show','hide'],
                              doc = """When set to 'show' the progress bar is displayed.
When set to 'hide', the progress bar widget is widthdrawn, but can be
redisplayed by choosing 'show' again.""", category='Viewer',
                              callbackFunc=[self.GUI.showHideProgressBar_CB],
                              )
        if gui:
            cbList = [self.GUI.logUserPref_cb,]
        else:
            cbList = []

        #if gui:
        #    self.guiSupport = __import__( "DejaVu.ViewerFramework.gui", globals(),
        #                                  locals(), ['gui'])

        if gui and self.guiVisible==0:

            # if gui == 1 but self.guiVisible == 0: the gui is created but
            # withdrawn immediatly
            self.GUI.ROOT.withdraw()
            if self.withShell:
                # Uses the pyshell as the interpreter when the VFGUI is hidden.
                self.GUI.pyshell.top.deiconify()

        self.viewSelectionIcon = 'cross' # or 'spheres' or 'labels'

        self.userpref.add( 'Transformation Logging', 'no',
                           validValues = ['no', 'continuous', 'final'],
                           callbackFunc = cbList,
                           doc="""Define when transformation get logged.\n'no' : never; 'continuous': after every transformation; 'final': when the Exit command is called""")
        self.userpref.add( 'Visual Picking Feedback', 1,
                           [0, 1], category="DejaVu",
                           callbackFunc = [self.SetVisualPickingFeedBack,],
                           doc="""When set to 1 a sphere is drawn at picked vertex""")
        self.userpref.add( 'Fill Selection Box', 1,
                           [0,1], category="DejaVu",
                           callbackFunc = [self.fillSelectionBoxPref_cb],
                           doc="""Set this option to 1 to have the program
 draw a solid selection box after 'fillSelectionBoxDelay' miliseconds without a motion""")

        self.userpref.add( 'Fill Selection Box Delay', 200, category="DejaVu",
                           validateFunc = self.fillDelayValidate,
                           callbackFunc = [self.fillSelectionBoxDelayPref_cb],
                           doc="""Delay in miliseconds after which the selection box turns solid if the 'fillSelectionBox' is set. Valide values are >0 and <10000""")


        self.userpref.add( 'Warning Message Format', 'pop-up', 
                           ['pop-up', 'printed'],
                           callbackFunc = [self.setWarningMsgFormat],
                           category="Viewer",
                           doc="""Set format for warning messages. valid values are 'pop-up' and 'printed'""")
        self._cwd = os.getcwd()
        self.userpref.add( 'Startup Directory', self._cwd, 
                           validateFunc = self.startupDirValidate,
                           callbackFunc = [self.startupDirPref_cb],
                           doc="""Startup Directory uses os.chdir to change the startup directory.
Startup Directory is set to current working directory by default.""")
        
        rcFolder = getResourceFolderWithVersion()
        self.rcFolder = rcFolder
        
        self.userpref.add( 'Log Mode', 'no',  ['no', 'overwrite', 'unique'],
                           callbackFunc = [self.setLogMode],
                           category="Viewer",
                           doc="""Set the log mode which can be one of the following:
                           
no - do not log the commands.
overwrite - stores the log in mvAll.log.py.
unique - stores the log in mvAll_$time.log.py.

log.py files are stored in resource folder located under ~/.mgltools/$Version
""")
        

        if self.hasGui: 
            # add an interactive command caller
            self.ICmdCaller = InteractiveCmdCaller( self )

            # remove DejaVu's default picking behavior
            vi = self.GUI.VIEWER
            vi.RemovePickingCallback(vi.unsolicitedPick)

            # overwrite the Camera's DoPick method to set the proper pickLevel
            # based on the interactive command that will be called for the 
            # current modifier configuration
            for c in vi.cameras:
                c.DoPick = self.DoPick
                
        self.addBasicCommands()

        if self.hasGui:
            from mglutil.util.recentFiles import RecentFiles
            fileMenu = self.GUI.menuBars['menuRoot'].menubuttons['File'].menu
            
            rcFile = rcFolder
            if rcFile:
                rcFile += os.sep + 'Pmv' + os.sep + "recent.pkl"
                self.recentFiles = RecentFiles(
                    self, fileMenu, filePath=rcFile,
                    menuLabel='Recent Files', index=2)

            self.logMode = 'no'
            self.GUI.dockCamera()         
            self.logMode = logMode
            # load out default interactive command which prints out object names
            self.ICmdCaller.setCommands( self.printGeometryName )
            self.ICmdCaller.go()
            
        if gui:
            self.userpref.add( 'Icon Size', 'medium',
                               ['very small', 'small', 'medium', 'large',
                                'very large'],
                               callbackFunc = [self.SetIconSize,],
                               category="Viewer",
                               doc="""Sets the size of icons for the Toolbar.""")
                 
            self.userpref.add( 'Save Perspective on Exit', 'yes', 
                           validValues = ['yes', 'no'],
                           doc="""Saves GUI perspective on Exit. The following features are saved:
GUI geometry, and whether camera is docked or not.
""")
            self.GUI.VIEWER.suspendRedraw = False
            self.GUI.VIEWER.currentCamera.height = 600
        # dictionary of event:[functions]. functions will be called by
        # self.dispatchEvent
        self.eventListeners = {}
        self.userpref.saveDefaults()
        self.userpref.loadSettings()
        if self.userpref.has_key('Save Perspective on Exit') and  self.userpref['Save Perspective on Exit']['value'] == 'yes':
            self.restorePerspective()        
        #self.GUI.VIEWER.ReallyRedraw()


    def registerListener(self, event, function):
        """registers a function to be called for a given event.
event has to be a class subclassing VFEvent
"""
        assert issubclass(event, VFEvent)
        assert callable(function)
        if not self.eventListeners.has_key(event):
            self.eventListeners[event] = [function]
        else:
            if function in self.eventListeners[event]:
                warnings.warn('function %s already registered for event %s'%(
                    function,event))
            else:
                self.eventListeners[event].append(function)


    def dispatchEvent(self, event):
        """call all registered listeners for this event type
"""
        assert isinstance(event, VFEvent)
        if self.eventListeners.has_key(event.__class__):
            if self.hasGui:
                vi=self.GUI.VIEWER
                autoRedraw = vi.autoRedraw
                vi.stopAutoRedraw()
                for func in self.eventListeners[event.__class__]:
                    func(event)
                if autoRedraw:
                    vi.startAutoRedraw()
            else:
                for func in self.eventListeners[event.__class__]:
                    func(event)  
            
        
    def DoPick(self, x, y, x1=None, y1=None, type=None, event=None):
        vi = self.GUI.VIEWER

        def getType(vf, mod):
            cmd = vf.ICmdCaller.commands.value[mod]
            if cmd:
                vf.ICmdCaller.currentModifier = mod
                vf.ICmdCaller.getObjects = cmd.getObjects
                return cmd.pickLevel
            else: return None

        if vi.isShift(): type = getType(self, 'Shift_L')
        elif vi.isControl(): type = getType(self, 'Control_L')
        elif vi.isAlt(): type = getType(self, 'Alt_L')
        else: type = getType(self, None)
        if type:
            return Camera.DoPick(vi.currentCamera, x, y, x1, y1, type, event)
        else:
            from DejaVu.Camera import PickObject
            return PickObject('pick', self.GUI.VIEWER.currentCamera)

        
    def clients_cb(self, client, data):
        """get called every time a client sends a message"""
        import sys
        sys.stdout.write('%s sent %s\n'%(client,data) )
        #exec(data)

    def embedInto(self, hostApp,debug=0):
        """
        function to define an hostapplication, take the string name of the application
        """
        if self.hasGui:
			raise RuntiomeError("VF with GUI cannot be embedded")
        from ViewerFramework.hostApp import HostApp
        self.hostApp = HostApp(self, hostApp, debug=debug)
        self.embeded=True

    def sendViewerState (self, event=None):
        # get call every so often when this PMV is a server
        state1 = self.GUI.VIEWER.getViewerStateDefinitionCode(
            'self.GUI.VIEWER', withMode=False)
        state2 = self.GUI.VIEWER.getObjectsStateDefinitionCode(
            'self.GUI.VIEWER', withMode=False)

        if self.socketComm is not None and len(self.socketComm.clients):
            cmdString = """"""
            for line in state1:
                cmdString += line
            for line in state2:
                cmdString += line
            self.socketComm.sendToClients(cmdString)

        self.GUI.ROOT.after(500, self.sendViewerState)
        
        
    def runServerCommands (self, event=None):
        # get call every so often when this PMV is a client of a server
        if not self.cmdQueue.empty():
            cmd = self.cmdQueue.get(False) # do not block if queue empty
            if cmd:
                #if pmv is embedded without a gui in a third application
                #have to parse the command and remove all cmd that imply GUI
                if self.embedded :
                    #mesg=cmd[1]
                    mesg=self.hostApp.driver.parsePmvStates(cmd[1])				
                    exec(mesg, {'self':self})
                #print 'client executing', cmd
                else : 
                    exec(cmd[1])
        if not self.embeded : 
            #if embeded the runServerCommand is handle by a thread define by the hosAppli class		
            self.GUI.ROOT.after(10, self.runServerCommands)

    def updateIMD(self):
        """get called every time the server we are connected to sends a
        message
        what about more than one molecule attached
        currently under develppment
        """
        from Pmv.moleculeViewer import EditAtomsEvent
        #print "pause",self.imd.pause
        if self.imd.mindy:
            #print "ok update mindy"
            self.imd.updateMindy()
            if self.hasGui and self.imd.gui : 
                self.GUI.VIEWER.OneRedraw()
                self.GUI.VIEWER.update()
                self.GUI.ROOT.after(1, self.updateIMD)
        else :
          if not self.imd.pause:
            self.imd.lock.acquire()
            coord = self.imd.imd_coords[:]
            self.imd.lock.release()
            if coord != None:
                #how many mol
                if type(self.imd.mol) is list :
                    b=0
                    for i,m in enumerate(self.imd.mol) :
                        n1 = len(m.allAtoms.coords)
                        self.imd.mol.allAtoms.updateCoords(coord[b:n1], self.imd.slot[i])
                        b=n1
                else :
                    self.imd.mol.allAtoms.updateCoords(coord, self.imd.slot)
                import DejaVu
                if DejaVu.enableVBO :
                    if type(self.imd.mol) is list :
                        b=0
                        for i,m in enumerate(self.imd.mol) :
                            N=len(m.geomContainer.geoms['cpk'].vertexSet.vertices.array)
                            m.geomContainer.geoms['cpk'].vertexSet.vertices.array[:]=coord[b:N]
                            b=N
                    else :
                        N=len(self.imd.mol.geomContainer.geoms['cpk'].vertexSet.vertices.array)
                        self.imd.mol.geomContainer.geoms['cpk'].vertexSet.vertices.array[:]=coord[:N]
                        #self.GUI.VIEWER.OneRedraw()
                        #self.GUI.VIEWER.update()
                else :
                    from Pmv.moleculeViewer import EditAtomsEvent
                    if type(self.imd.mol) is list :
                        for i,m in enumerate(self.imd.mol) :
                            event = EditAtomsEvent('coords', m.allAtoms)
                            self.dispatchEvent(event)
                    else :             
                        event = EditAtomsEvent('coords', self.imd.mol.allAtoms)
                        self.dispatchEvent(event)
                    #self.imd.mol.geomContainer.geoms['balls'].Set(vertices=coord)
                    #self.imd.mol.geomContainer.geoms['sticks'].Set(vertices=coord.tolist())
                    #self.imd.mol.geomContainer.geoms['lines'].Set(vertices=coord)
                    #self.imd.mol.geomContainer.geoms['bonds'].Set(vertices=coord)
                    #self.imd.mol.geomContainer.geoms['cpk'].Set(vertices=coord)
                if self.handler.isinited : 
                    self.handler.getForces(None)
                    self.handler.updateArrow() 
             #"""
        if self.hasGui and self.imd.gui : 
            self.GUI.VIEWER.OneRedraw()
            self.GUI.VIEWER.update()
            self.GUI.ROOT.after(5, self.updateIMD)
        #self.GUI.ROOT.after(10, self.updateIMD)

    def server_cb(self, server, data):
        """get called every time the server we are connected to sends a
        message"""
        import sys
        #sys.stderr.write('server %s sent> %s'%(server,data) )
        self.cmdQueue.put( (server,data) )
        #exec(data) # cannot exec because we are not in main thread
                    # and Tkitner is not thread safe
        #self.GUI.VIEWER.Redraw()
        
    def drawSelectionRectangle(self, event):
        c = self.GUI.VIEWER.currentCamera
        c.drawSelectionRectangle(event)

    def initSelectionRectangle(self, event):
        c = self.GUI.VIEWER.currentCamera
        c.initSelectionRectangle(event)
        
    def endSelectionRectangle(self, event):
        c = self.GUI.VIEWER.currentCamera
        c.endSelectionRectangle(event)
        
    def fillSelectionBoxPref_cb(self, name, old, new):
        if self.hasGui:
            for c in self.GUI.VIEWER.cameras:
                c.fillSelectionBox = new

    def fillDelayValidate(self, value):
        return (value > 0 and value < 10000)

    def fillSelectionBoxDelayPref_cb(self, name, old, new):
        if self.hasGui:
            for c in self.GUI.VIEWER.cameras:
                c.fillDelay = new
        
    def SetVisualPickingFeedBack(self, name, old, new):
        if self.hasGui:
            self.GUI.VIEWER.showPickedVertex = new
        
    def SetIconSize(self, name, old, new):
        if self.hasGui:
            self.GUI.configureToolBar(iconsize=new)

    def startupDirPref_cb(self, name, old, new):
        if not os.path.isdir(new):
            if not hasattr(self,'setUserPreference') and not hasattr(self.setUserPreference, 'form'): return
            root = self.setUserPreference.form.root
            from tkMessageBox import showerror
            showerror("Invalid Startup Directory", "Directory %s "%new +
           " does not exists. Please select a valid Directory", parent=root)
            from tkFileDialog import askdirectory
            dir = askdirectory(parent=root, 
                               title='Please select startup directory')
            if dir:
                os.chdir(dir)
                self.userpref.data["Startup Directory"]['value'] = dir
                w=self.setUserPreference.form.descr.entryByName[name]['widget']
                w.setentry(dir)
                #this removes updateGUI so that wrong new is not shown
                self.userpref.data["Startup Directory"]['callbackFunc'].pop(-1)
            else:
                self.userpref.set("Startup Directory", old)
        else:
            os.chdir(new)

    def startupDirValidate(self, value):
            return 1
        
    def restorePerspective(self):
        if not self.hasGui:
            return
        if self.resourceFile:
            rcFile = os.path.join(os.path.split(self.resourceFile)[0], "perspective")
        else:
            rcFolder = getResourceFolderWithVersion()
            rcFile = os.path.join(rcFolder, "ViewerFramework", "perspective")

        if os.path.exists(rcFile):
            try:
                self.source(rcFile, globalNames=1, log=1)
                return True
            except Exception, inst:
                print inst, rcFile
        return
        
    def tryOpenFileInWrite(self, filename):
        try:
            self.logAllFile = open( filename, 'w' )
            from Support.version import __version__
            from mglutil import __revision__           
            self.logAllFile.write("# Pmv version %s revision %s\n"%(__version__, __revision__))
            return 1
        except:
            try:
                from mglutil.util.packageFilePath import getResourceFolderWithVersion
                rc = getResourceFolderWithVersion()
                self.logAllFile = open(rc + os.sep + filename, 'w' )
            except:
                return 0
        
    def customize(self, file=None):
        """if a file is specified, this files gets sourced, else we look for
        the file specified in self.resourceFile in the following directories:
        1 - current directory
        2 - user's home directory
        3 - the package to which this instance belongs to
        """
        #print 'ZZZZZZZZZZZZZZZZZZZZZZZZ'
        #import traceback
        #traceback.print_stack()
        if file is not None:
            if not os.path.exists(file):
                return
            self.source(file, globalNames=1, log=0)
            return

        resourceFileLocation = findResourceFile(self,
                                                resourceFile=self.resourceFile)

        if resourceFileLocation.has_key('currentdir') and \
           not resourceFileLocation['currentdir'] is None:
            path = resourceFileLocation['currentdir']

        elif resourceFileLocation.has_key('home') and \
             not resourceFileLocation['home'] is None:
            path = resourceFileLocation['home']

        elif resourceFileLocation.has_key('package') and \
             not resourceFileLocation['package'] is None:
            path = resourceFileLocation['package']
        else:
            return
        
        self.source(path, globalNames=1, log=0)
        path = os.path.split(path)[-1]
        if os.path.exists(path):
            self.source(path, globalNames=1, log=0)
        return
    
    def after(func, *args, **kw):
        """method to run a thread enabled command and wait for its completion.
        relies on the command to release a lock called self.done
        only works for commands, not for macros
        """
        lock = thread.allocate_lock()
        lock.acquire()
        func.private_threadDone = lock
        apply( func, args, kw )
        func.waitForCompletion()


    def getLog(self):
        """
        generate log strings for all commands so far
        """
        logs = []
        i = 0
        for cmd, args, kw in self.cmdHistory:
            try:
                log = cmd.logString( *args, **kw)+'\n'
            except:
                log = '#failed to create log for %d in self.cmdHistory: %s\n'%(
                    i, cmd.name) 
            logs.append(log)
            i += 1       
        return logs


    def addCmdToHistory(self, cmd, args, kw):
        """
        append a commadn to the historyu of commands
        """
        self.cmdHistory.append( (cmd, args, kw))


    def log(self, cmdString=''):
        """append command to logfile
        FIXME: this should also get whatever is typed in the PythonShell
        """
        if self.logMode == 'no': return
        
        if cmdString[-1]!='\n': cmdString = cmdString + '\n'
        
        if hasattr(self, 'logAllFile'):
            self.logAllFile.write( cmdString )
            self.logAllFile.flush()

        if self.socketComm is not None and len(self.socketComm.clients):
            #is it really need?
            cmdString=cmdString.replace("log=0","log=1")
            self.socketComm.sendToClients(cmdString)

        self.dispatchEvent( LogEvent( cmdString ) )
##          if self.selectLog:
##              self.logSelectFile.write( cmdString )


    def tryto(self, command, *args, **kw ):
        """result <- tryto(command, *args, **kw )
        if an exception is raised print traceback and continue
        """
        self.commandNestingLevel = self.commandNestingLevel + 1
        try:
            if self.commandNestingLevel==1:
                self.commandsLock.acquire()

            if not self.trapExceptions:
                # we are running tests and want exceptions not to be caught
                result = command( *args, **kw )
            else:
                # exception should be caught and displayed
                try:
                    result = command( *args, **kw )

                except:
                    print 'ERROR *********************************************'
                    if self.guiVisible==1 and self.withShell:
                        self.GUI.pyshell.top.deiconify()
                        self.GUI.ROOT.config(cursor='')
                        self.GUI.VIEWER.master.config(cursor='')    
                        self.GUI.MESSAGE_BOX.tx.component('text').config(cursor='xterm')

                    traceback.print_exc()
                    sys.last_type, sys.last_value, sys.last_traceback = sys.exc_info()
                    result = 'ERROR'
                    # sets cursors back to normal
                   

        finally:
            if self.commandNestingLevel==1:
                self.commandsLock.release()
            self.commandNestingLevel = self.commandNestingLevel - 1

        return result
            

    def message(self, str, NL=1):
        """ write into the message box """
        if self.hasGui:
            self.GUI.message(str,NL)
        else:
            print str

    def unsolicitedPick(self, pick):
        """treat and unsollicited picking event"""
        
        vi = self.GUI.VIEWER
        if vi.isShift() or vi.isControl():
            vi.unsolicitedPick(pick)
        else:
            #print picked geometry
            for k in pick.hits.keys():
                self.message(k)
        
    def addBasicCommands(self):
        """Create a frame to hold menu and button bars"""

        from ViewerFramework.dejaVuCommands import PrintGeometryName, \
             SetCameraSizeCommand, SetCamSizeGUI
        # Basic command that needs to be added manually.
        self.addCommand( PrintGeometryName(), 'printGeometryName ', None )
        g = CommandGUI()
        g.addMenuCommand('menuRoot', 'File', 'Browse Commands',
                         separatorAbove=1, )
        self.addCommand( BrowseCommandsCommand(), 'browseCommands', g)

        self.addCommand( SetCameraSizeCommand(), 'setCameraSize',
                         SetCamSizeGUI)

        from ViewerFramework.basicCommand import UndoCommand, \
             ResetUndoCommand

#        g = CommandGUI()
#        g.addMenuCommand('menuRoot', 'File', 'Remove Command')
#        self.addCommand( RemoveCommand(), 'removeCommand', g)

        from mglutil.util.packageFilePath import getResourceFolderWithVersion
        self.vfResourcePath = getResourceFolderWithVersion()
        if self.vfResourcePath is not None:
            self.vfResourcePath += os.sep + "ViewerFramework"
            if not os.path.isdir(self.vfResourcePath):
                try:
                    os.mkdir(self.vfResourcePath)
                except Exception, inst:
                    print inst
                    txt="Cannot create the Resource Folder %s" %self.vfResourcePath
                    self.vfResourcePath = None                

        g = CommandGUI()
        g.addMenuCommand('menuRoot', 'Edit', 'Undo ', index=0)
        g.addToolBar('Undo', icon1 = '_undo.gif', icon2 = 'undo.gif', 
                             type = 'ToolBarButton',state = 'disabled',
                             balloonhelp = 'Undo', index = 2)
        
        self.addCommand( UndoCommand(), 'undo ', g)
        self.addCommand( ResetUndoCommand(), 'resetUndo ', None)


        g = CommandGUI()
        #g.addMenuCommand('menuRoot', 'File', 'Load Command')
        self.addCommand( loadCommandCommand(), 'loadCommand', g)

        g = CommandGUI()
        #g.addMenuCommand('menuRoot', 'File', 'Load Module')
        self.addCommand( loadModuleCommand(), 'loadModule', g)

        g = CommandGUI()
        g.addMenuCommand('menuRoot', 'File', 'Load Macros', separatorBelow=1)
        self.addCommand( loadMacroCommand(), 'loadMacro', g)

        # Load Source command from customizationCommands module:
        self.browseCommands('customizationCommands', commands=['source',],
                            package='ViewerFramework', topCommand=0)

        # force the creation of the default buttonbar and PyShell checkbutton
        # by viewing the Python Shell widget
        if self.withShell:
            self.addCommand( ShellCommand(), 'Shell', ShellCommandGUI )       
            
        # add the default 'Help' menubutton in the default menubar
        if self.hasGui:
            bar = self.GUI.menuBars['menuRoot']
            help = self.GUI.addMenuButton( bar, 'Help', {}, {'side':'right'})
            self.GUI.addMenuButton( bar, 'Grid3D', {}, {'side':'right'})
            
            try:
                import grid3DCommands
                self.browseCommands("grid3DCommands", package="ViewerFramework", topCommand=0)
            except Exception, inst:
                print inst
                print "Cannot import grid3DCommands. Disabling grid3DCommands..."
            #self.GUI.ROOT.after(1500, self.removeCommand.loadCommands)
             
        # load helpCommand and searchForCmd
        self.browseCommands('helpCommands',
                            commands=['helpCommand','searchForCmd', 'citeThisScene',
                                      'showCitation'],
                            package='ViewerFramework', topCommand = 0)

        # load SetUserPreference and setOnAddObjectCmds Commands
        self.browseCommands('customizationCommands',
                            commands=['setUserPreference',
                                      'setOnAddObjectCommands'],
                            package='ViewerFramework', topCommand = 0)


        # load ChangeVFGUIvisGUI and SetOnAddObjectCmds Command
        self.browseCommands('customizeVFGUICommands',
                            package='ViewerFramework', topCommand = 0)


        self.addCommand( SaveSessionCommand(), 'saveSession ', SaveSessionCommandGUI)

        # Add the Exit command under File
        g = CommandGUI()
        g.addMenuCommand('menuRoot', 'File', 'Exit', separatorAbove=1)
        self.addCommand( ExitCommand(), 'Exit', g )

        # load object transformation, camera transformation,
        # light transformation, Clipping Plane transformation,
        # CenterGeom, centerScene commands
        self.browseCommands("dejaVuCommands", commands=[
            'transformObject', 'transformCamera', 'setObject',
            'setCamera', 'setLight', 'setClip', 'addClipPlane',
            'centerGeom', 'centerScene', 'centerSceneOnVertices',
            'alignGeomsnogui','alignGeoms', 'toggleStereo',
            'centerSceneOnPickedPixel'],
                    package='ViewerFramework', topCommand = 0)

        
    def validInstance(self, classList, obj):
        """Checks whether an object is an instance of one the classes in the
        list"""
        ok = 0
        for Klass in classList:
            if isinstance(obj, Klass):
                OK=1
                break
        return OK


    def getOnAddObjectCmd(self):
        """
returns a copy of the list of commands currently executed when a new object
is added
"""
        return self.onAddObjectCmds[:]

    
    def addOnAddObjectCmd(self, cmd, args=[], kw={}):
        """
adds a command to the list of commands currently executed when a new object
is added
"""
        assert callable(cmd)
        assert type(args)==types.TupleType or type(args)==types.ListType
        assert type(kw)==types.DictType
        assert cmd.flag & Command.objArgOnly
        kw['topCommand'] = 0
        if type(args)==types.ListType:
            args = tuple(args)
        self.onAddObjectCmds.append( (cmd, args, kw) )


    def removeOnAddObjectCmd(self, cmd):
        """
removes a command to the list of commands currently executed when a new object
is added
"""
        for com in self.onAddObjectCmds:
            if com[0]==cmd:
                self.onAddObjectCmds.remove(com)
                return com
        print 'WARNING: command %s not found'%cmd.name
        return None

        
    def addObject(self, name, obj, geomContainer=None):
        """Add an object to a Viewer"""
        #print 'acquiring addObject lock'
        self.objectsLock.acquire()
        self.objects.append(obj)
        self.objectsLock.release()
        #print 'releasing addObject lock'
##          if geomContainer is None:
##              obj.geomContainer = GeomContainer( self.GUI.VIEWER )
##          else:
##              obj.geomContainer = geomContainer
        obj.geomContainer = geomContainer

        # prepare progress bar
        lenCommands = len(self.cmdsWithOnAddObj)
        if self.hasGui:
            self.GUI.configureProgressBar(init=1, mode='increment',
                                          max=lenCommands,
                                          progressformat='ratio',
                                          labeltext='call initGeom methods')
        
        #call initGeom method of all commands creating geometry
        #from mglutil.util import misc
        #mem0 = misc.memory()
        for com in self.cmdsWithOnAddObj:
            com.onAddObjectToViewer(obj)
            #mem = misc.memory()
            #print (mem-mem0)/1024., com.name
            #check for gui
            if self.hasGui:
                self.GUI.updateProgressBar()

        # now set progress bar back to '%' format
        if self.hasGui:
            self.GUI.configureProgressBar(progressformat='percent')
        
        # prepare progress bar
        lenCommands = len(self.onAddObjectCmds)

        #call functions that need to be called on object
        for com in self.onAddObjectCmds:
            com[2]['redraw']=0
            com[2]['log']=0
            apply( com[0], (obj,)+com[1], com[2])
            # note we have to re-configure the progress bar because doitWrapper
            # will overwrite the mode to 'percent'
            #check for gui
            if self.hasGui:
                self.GUI.configureProgressBar(init=1, mode='increment',
                                          max=lenCommands,
                                          progressformat='ratio',
                                          labeltext='call geom functions')
                self.GUI.updateProgressBar()

        if self.hasGui:
        # now set progress bar back to '%' format
            self.GUI.configureProgressBar(progressformat='percent')

        # create add object event
        event = AddObjectEvent(objects=[obj])
        self.dispatchEvent(event)
        
        if self.hasGui:
            self.centerScene(topCommand=0)
            self.GUI.VIEWER.Redraw()


    def removeObject(self, obj, undoable=False):
        """Remove an object from a Viewer"""
        #1 Delete the obj from the list of objects. 
        del(self.objects[self.objects.index(obj)])


        # call onRemoveMol method of all commands creating geometry
        # To remove geometries created by these commands from the VIEWER

        ## MS chose to cerate undoableDelete__ variable in VF to let cmd's
        ## onRemoveObjectFromViewer method decide what to do when delete is
        ## undoable. Passign undoable into th method would require changing
        ## the signature in each implementation when onyl a hand full do
        ## something s[pecial when undoable is True
        self.undoableDelete__ = undoable
        for com in self.cmdsWithOnRemoveObj:
            self.tryto( com.onRemoveObjectFromViewer, (obj) )
        del self.undoableDelete__

        # clean up the managedGeometries list
        if obj.geomContainer:
            for cmd in self.commands.values():
                if len(cmd.managedGeometries)==0: continue
                geomList = []
                for g in cmd.managedGeometries:
                    if hasattr(g, 'mol') and g.mol==obj:
                        continue
                    geomList.append(g)
                cmd.managedGeometries = geomList

        # remove everything created in the geomContainer associated to the
        # mol we want to destroy,
        if obj.geomContainer:
            obj.geomContainer.delete()

        # create remove object event
        event = DeleteObjectEvent(objects=[obj])
        self.dispatchEvent(event)
        

    def addColorMap(self, colorMap):
        from DejaVu.colorMap import ColorMap
        assert isinstance(colorMap, ColorMap)
        if self.colorMaps.has_key('colorMap.name'):
            warnings.warn('invalid attemp to replace an existing colormap')
        else:
            self.colorMaps[colorMap.name] = colorMap

    def addCommandProxy(self, commandProxy):
        """To make startup time faster this function add GUI elements without
        importing and loading the full dependiencies for a command
        """
        if self.hasGui:
            gui = commandProxy.gui
            if gui is not None:
                gui.register(self, commandProxy)
                gui.registered = True
                
    def addCommand(self, command, name, gui=None):
        """
        Add a command to a viewer.
        arguments:
           command: Command instance
           name: string
           gui: optional CommandGUI object
           objectType: optional type of object for which we need to add geoms
           geomDescr: optional dictionary of 'name:objectType' items
           
        name is used to create an alias for the command in the viewer
        if a gui is specified, call gui.register to add the gui to the viewer
        """
        #print "addCommand", name, command
        
        assert isinstance(command, Command)

        # happens because of dependencies
        if name in self.commands.keys():
            return  self.commands[name]

        error = self.tryto(command.checkDependencies, self)
        if error=='ERROR':
            print '\nWARNING: dependency check failed for command %s' % name
            return
        
##              def download_cb():
##                  import os
##                  os.system('netscape http://www.scripps.edu/pub/olson-web/people/scoon/login.html &')
##              def Ok_cb(idf):
##                  idf.form.destroy()

##              tb = traceback.extract_tb(sys.exc_traceback)
##              from gui import InputFormDescr, CallBackFunction
##              import Tkinter
##              idf = InputFormDescr("Missing dependencies !")
##              idf.append({'widgetType': Tkinter.Label,
##                         'text':"%s can't be loaded, needs  %s module"
##                         % (tb[1][-1][7:],command.__class__.__name__),
##                          'gridcfg':{'columnspan':2}})
##              idf.append({'widgetType':Tkinter.Button, 'text':'OK',
##                          'command':CallBackFunction(Ok_cb, idf),
##                          'gridcfg':{'sticky':Tkinter.W+Tkinter.E}})
##              idf.append({'widgetType':Tkinter.Button, 'text':'Download',
##                          'command':download_cb,
##                          'gridcfg':{'row':-1,  'sticky':Tkinter.W+Tkinter.E,
##                                     'columnspan':5 }})
##              form = self.getUserInput(idf, modal=0, blocking=0)

            
##              self.warningMsg(title = "Missing dependencies !",
##                              message = "%s can't be loaded, needs  %s module"
##                              % (tb[1][-1][7:],command.__class__.__name__))
##              return

        command.vf = self
        name = string.strip(name)
        name = string.replace(name, ' ', '_')
        self.commands[name] = command
        command.name=name
        command.undoMenuString=name      # string used to change menu entry for Undo
        command.undoMenuStringPrefix=''  # prefix used to change menu entry for Undo

        setattr(self, name, command)
        #exec ( 'self.%s = command' % name )
        
        if self.hasGui:
            if gui is not None:
                assert isinstance(gui, CommandGUI)
                gui.register(self, command)
                gui.registered = True
        #call the onAddCmdToViewer method of the new command
        command.onAddCmdToViewer()

        for c in self.commands.values():
            c.onAddNewCmd(command)
            
        if hasattr(command, 'onAddObjectToViewer'):
            if callable(command.onAddObjectToViewer):
                self.cmdsWithOnAddObj.append(command)
                for o in self.objects:
                    command.onAddObjectToViewer(o)

        if hasattr(command, 'onRemoveObjectFromViewer'):
            if callable(command.onRemoveObjectFromViewer):
                self.cmdsWithOnRemoveObj.append(command)

        if hasattr(command, 'onExitFromViewer'):
            if callable(command.onExitFromViewer):
                self.cmdsWithOnExit.append(command)
            
    def updateGeomContainers(self, objectType, geomDescr):
        """To be called when a new command that requires geometry is add to
        a viewer. This method loops over existing objects to create the
        required geometry for already existing objects"""

        for o in self.objects:
            if not isinstance(object, objectType): continue
            o.geomContainer.addGeom( geomDescr )
            
           
    def askFileOpen(self, idir=None, ifile=None, types=None, title='Open',
                    relative=True, parent=None, multiple=False):
        """filename <- askFileOpen( idir, ifile, types, title)
        if the viewer is run with a gui this function displays a file browser
        else it askes for a file name
        idir:  optional inital directory
        ifile: optional initial filename
        types: list of tuples [('PDB files','*.pdb'),]
        title: widget's title
        relative: when set to True the file name is realtive to the directory
                  where the application has been started
        multiple: allow selecting multiple files
        returns: a filename ot None if the Cancel button
        """
        if self.hasGui:
            if parent:
                file = self.GUI.askFileOpen(parent, idir=idir, ifile=ifile,
                                            types=types, title=title,
                                            multiple=multiple)
            else:
                file = self.GUI.askFileOpen(
                    self.GUI.ROOT, idir=idir, ifile=ifile,
                    types=types, title=title, multiple=multiple)
            

            if file is () or file is None: # this is returned if one click on the file list and
                           # then clicks Cancel
                return
        else:
            default = ''
            if idir: default = idir
            if ifile: default = os.path.join( default, ifile )
            file = raw_input("file name [%s] :"%default)
            if file=='':
                if default != '' and os.path.exists(file):
                    file = default

        if multiple is False:
            fpath,fname = os.path.split(file)

            if relative and file and os.path.abspath(os.path.curdir) == fpath:
                file  = os.path.join(
                    os.path.curdir,
                    file[len(os.path.abspath(os.path.curdir))+1:])
            return file
        else:
            files = []
            for f in file:
                fpath,fname = os.path.split(f)
                if relative and f and os.path.abspath(os.path.curdir) == fpath:
                    f = os.path.join(os.path.curdir,
                            f[len(os.path.abspath(os.path.curdir))+1:])
                files.append(f)
            return files


    def askFileSave(self, idir=None, ifile=None, types=None, title='Save',
                    relative=True):
        if self.hasGui:
            file = self.GUI.askFileSave(self.GUI.ROOT, idir=idir, ifile=ifile,
                                        types=types, title=title)
            if file is () or file is None: # this is returned if one clcik on the file list and
                           # then clicks Cancel
                return
        else:
            default = ''
            if idir: default = idir
            if ifile: default = os.path.join( default, ifile )
            file = raw_input("file name [%s] :"%default)
            if file=='':
                if default != '' and os.path.exists(file):
                    file = default
        fpath,fname = os.path.split(file)
        if relative and file and os.path.abspath(os.path.curdir) == fpath:
            file  = os.path.join(os.path.curdir,
                                 file[len(os.path.abspath(os.path.curdir))+1:])
        return file

    def setLogMode(self, name, oldval, newval):
        "Sets the Lig Mode"
        self.logMode = newval
        # open log file for all commands
        if self.logMode == 'unique':
            import time
            t = time.localtime(time.time())
            fname1 = 'mvAll_%04d-%02d-%02d_%02d-%02d-%02d.log.py'%(t[0],t[1],t[2],t[3],t[4],t[5])
            fname1 = os.path.join(self.rcFolder, fname1)
            if self.hasGui:
                self.GUI.ROOT.after_idle(self.clearOldLogs)
            
        elif self.logMode == 'overwrite':
            fname1 = os.path.join(self.rcFolder, 'mvAll.log.py')

        if self.logMode != 'no':
            flag = self.tryOpenFileInWrite(fname1)
            while flag == 0:
                idf = InputFormDescr(title = 'Directory not writable ...')
                variable = Tkinter.StringVar()
                idf.append({'name':'noLog','widgetType': Tkinter.Radiobutton,
                            'text':'noLog','variable':variable,
                            'value':'noLog','defaultValue':'noLog',
                            'gridcfg':{'sticky':Tkinter.W}})

                idf.append({'name':'browse','widgetType': 'SaveButton',
                            'typeofwidget':Tkinter.Radiobutton,
                            'types':[ ('Python Files', '*.py')],
                            'title':'Choose a log File...',
                            'text':'browse',
                            'variable':variable,
                            'defaultValue':'noLog',
                            'value':'browse',
                            'gridcfg':{'sticky':Tkinter.W}})
                self.GUI.ROOT.deiconify()
                self.GUI.ROOT.update()
                result = self.getUserInput(idf)
                if result == {}:
                    self.GUI.ROOT.destroy()
                    return
                elif result['noLog'] == 'noLog':
                    self.logMode  = 'no'
                    flag = 1
                elif result['noLog'] == 'browse' and result.has_key('browse'):
                    assert not result['browse'] in ['']
                    flag = self.tryOpenFileInWrite(result['browse'])
                elif result['noLog'] == 'browse' and not result.has_key('browse'):
                    print "you didn't enter a proper file name try again"
                    flag = 0


    def setWarningMsgFormat(self, name, oldval, newval):
        """ newval can be either 'pop-up' or 'printed'"""
    
        self.messageFormat = newval


    def warningMsg(self, msg, title='WARNING: ', parent = None):
        """None <- warningMsg(msg)"""
        if type(title) is not types.StringType:
            title = 'WARNING: '
        if self.hasGui and self.messageFormat=='pop-up':
            tkMessageBox.showwarning(title, msg,parent = parent)
        else:
            sys.stdout.write(title+msg+'\n')


    def askOkCancelMsg(self, msg):
        """None <- okCancelMsg(msg)"""
        if self.hasGui:
            return tkMessageBox.askyesno('expand selection', msg)
        else:
            val = raw_input('anser [0]/1: '+msg+'\n')
            if val=='1': return 1
            else: return 0


    ## FIXME .. do we need this ?
    def errorMsg(self, msg, errtype=RuntimeError):
        """None <- errorMsg(errorType, msg)"""
        if self.hasGui:
            tkMessageBox.showerror(msg)
        raise errtype(msg)


    def getUserInput(self, formDescription, master=None, root=None,
                     modal=1, blocking=0,
                     defaultDirection = 'row', closeWithWindow = 1,
                     okCfg={'text':'OK'}, cancelCfg={'text':'Cancel'},
                     initFunc=None, scrolledFrame=0, width=None, height=None,
                     okcancel=1,  onDestroy = None
                     ):
        """val[] <- getUserInput(formDescription)
        Returns a list of values obtained either from an InputForm or by
        prompting the user for values
        """
##          from gui import InputForm, InputFormDescr
        from mglutil.gui.InputForm.Tk.gui import InputForm, InputFormDescr
        assert isinstance(formDescription, InputFormDescr)
        if self.hasGui:
            if master==None:
                master = self.GUI.ROOT

            form = InputForm(master, root, formDescription,
                             modal=modal, blocking=blocking,
                             defaultDirection=defaultDirection,
                             closeWithWindow=closeWithWindow,
                             okCfg=okCfg, cancelCfg=cancelCfg,
                             initFunc=initFunc, scrolledFrame=scrolledFrame,
                             width=width, height=height,
                             okcancel=okcancel, onDestroy=onDestroy)
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

            if not (modal or blocking):
                return form
            else:
                return form.go()
        else:
            self.warningMsg("nogui InputForm not yet implemented")


    def transformedCoordinatesWithInstances(self, hits):
        """ hist is pick.hits = {geom: [(vertexInd, intance),...]}
This function will use the instance information to return a list of transformed
coordinates
"""
        # FIXME this is in DejaVu.VIewer and should go away here
        vt = []
        for geom, values in hits.items():
            coords = geom.vertexSet.vertices.array
            for vert, instance in values:
                M = geom.GetMatrix(geom.LastParentBeforeRoot(), instance[1:])
                pt = coords[vert]
                ptx = M[0][0]*pt[0]+M[0][1]*pt[1]+M[0][2]*pt[2]+M[0][3]
                pty = M[1][0]*pt[0]+M[1][1]*pt[1]+M[1][2]*pt[2]+M[1][3]
                ptz = M[2][0]*pt[0]+M[2][1]*pt[1]+M[2][2]*pt[2]+M[2][3]
                vt.append( (ptx, pty, ptz) )
        return vt
        
    def clearOldLogs(self):
        currentTime = time.time()
        for file in glob.glob(os.path.join(self.rcFolder, "*.log.py")):
            stats = os.stat(file)
            if currentTime - stats[8] > 3000000: #~month
                os.remove(file)
        
        
        
        
if __name__ == '__main__':
    v = ViewerFramework()
    import pdb
