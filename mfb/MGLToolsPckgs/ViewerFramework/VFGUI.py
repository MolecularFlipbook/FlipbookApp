#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

"""
This module implements the class viewerFrameworkGUI.
This class provides support for extending the GUI of a Viewer derived from the
ViewerFramework base class
"""

# $Header: /opt/cvs/python/packages/share1.5/ViewerFramework/VFGUI.py,v 1.187.2.3 2011/08/18 19:01:46 sanner Exp $
#
# $Id: VFGUI.py,v 1.187.2.3 2011/08/18 19:01:46 sanner Exp $
#


import Tkinter, thread, string, Pmw, types
from PIL import Image, ImageTk
try:
    from TkinterDnD2 import COPY
    hasDnD2 = True
except ImportError:
    hasDnD2 = False
    
try:
    from DejaVu.Viewer import Viewer
except ValueError:
    print "Can't find a suitable Viewer\n"
    

import tkFileDialog

from mglutil.util.misc import ensureFontCase
from mglutil.util.callback import CallbackFunction
from mglutil.util.packageFilePath import findFilePath
from mglutil.gui.BasicWidgets.Tk.progressBar import ProgressBar, \
     ProgressBarConf, ProgressBarUpd
from mglutil.util.packageFilePath import getResourceFolderWithVersion
import ViewerFramework, os

from VFCommand import CommandGUI, ICONSIZES, ICONPATH
from VF import VFEvent


class RaiseToolPageEvent(VFEvent):
    pass


class msg_box(Tkinter.Frame):
    """ message box with scrollable text """
    def __init__(self, master=None, txt='', w=80, h=8):
        Tkinter.Frame.__init__(self, master)

        self.tx = Pmw.ScrolledText(self, usehullsize=1, hull_height=300)
        self.tx.pack(expand=1, fill='both', anchor='s')

        self.pack(side='bottom', expand=1, fill='both')
        
        # insert initial message
        self.tx.insert('end', txt)

    def append(self, str):
        """ insert at the end of the list """
        self.tx.insert('end', str)
        self.tx.yview('end')

    def clear(self):
        self.tx.clear()

    def setText(self, text):
        self.tx.setvalue(text)
        self.tx.yview('end')


import sys
from mglutil.util.idleUtil import getShell

class ViewerFrameworkGUI:
    """This class builds the GUI for the MoleculeViewer Class. The GUI 
    consists of a Frame, containing 1 or more menuBars, a canvas holding 
    the 3-D camera instance and a message box.  Methods addMenuBar, addMenu
    and addMenuCommand modify the menuBars."""


    def beforeRebuildDpyLists(self):
        if self.VIEWER.autoRedraw:
            self.VIEWER.currentCamera.update_idletasks()
        self.busyRedraw()

    def afterRedraw(self):
        if self.VIEWER.lastFrameTime:
            frameRate = 1./self.VIEWER.lastFrameTime
        else:
            frameRate = self.VIEWER.lastFrameTime
        self.frameRateTk.configure(text="%4.1f"%(frameRate))

    def afterRebuildDpyLists(self):
        if self.suspendLight is False:
            self.setIdleLight(self.previousState)
        
    def dialog(self):
        
#        t="Do you wish to Quit?"
#        from SimpleDialog import SimpleDialog
#        d = SimpleDialog(self.ROOT, text=t,
#                                     buttons=["Quit","Cancel"],
#                                     default=0, title="Quit?")
#        ok=d.go()
        import tkMessageBox
        ok = tkMessageBox.askokcancel("Quit?","Do you Wish to Quit?")
        if ok:
            self.quit_cb()
        else:
            return

#    def keydown(self,event):
#        if event.keysym == 'Shift_L':
#            print 'Shift_l'
#            self.vf.setICOM(self.vf.select, modifier=None, log=0)
#
#        #'Shift_R', 'Control_L', 'Control_R',
#        #                    'Alt_L', 'Alt_R']:
#        #print 'key down'
#
#    def keyup(self,event):
#        self.vf.setICOM(self.vf.printNodeNames, modifier=None, log=0)
#        #print 'key up'

        
#    def Enter_cb(self, event=None):
#        self.ROOT.focus_set()
#        self.ROOT.bind('<KeyPress>', self.keydown)
#        self.ROOT.bind('<KeyRelease>', self.keyup)
#
#    def Leave_cb(self, event=None):
#        self.ROOT.unbind('<KeyPress>')
#        self.ROOT.unbind('<KeyRelease>')


    def softquit_cb(self):
        #print "ViewerFrameworkGUI.softquit_cb"

        #self.vf.GUI.ROOT.option_clear()

        # set .GUI.registered to false for each command to force the GUI
        # to be created again if another ViewerFramework is created
        for cmd in self.vf.commands.items():
            if cmd[1].GUI:
                cmd[1].GUI.registered=False

        for com in self.vf.cmdsWithOnExit:
            com.onExitFromViewer()

        for c in self.VIEWER.cameras:
            c.eventManager.RemoveCallback('<Map>', c.Map)
            c.eventManager.RemoveCallback('<Expose>', c.Expose)
            c.eventManager.RemoveCallback('<Configure>', c.Expose)
            c.eventManager.RemoveCallback('<Enter>', c.Enter_cb)

        if hasattr(self.vf, 'logAllFile'):
            rcFolder = getResourceFolderWithVersion()
            dirList = os.listdir(rcFolder)
            import time
            lTimeNow = time.time()
            for fname in dirList:
                if fname.startswith('mvAll_') \
                  and ( fname.endswith('.log.py') or fname.endswith('.log.py~') ) \
                  and self.vf.logAllFile.name.endswith(fname) is False: #so we keep last ten days current session files
                    lDecomposedCurrentLogFilename = fname.strip('mvAll_')
                    lDecomposedCurrentLogFilename = lDecomposedCurrentLogFilename.rstrip('.log.py')
                    lDecomposedCurrentLogFilename = lDecomposedCurrentLogFilename.replace('-', ' ')
                    lDecomposedCurrentLogFilename = lDecomposedCurrentLogFilename.replace('_', ' ')
                    #print "lDecomposedCurrentLogFilename", lDecomposedCurrentLogFilename
                    lTime = time.strptime(lDecomposedCurrentLogFilename, "%Y %m %d %H %M %S")
                    lTimeDifference = lTimeNow - time.mktime(lTime)
                    #print "lTimeDifference", lTimeDifference
                    if lTimeDifference >  3600*24*10 : #so we keep last ten days current session files
                        os.remove(os.path.join(rcFolder,fname))
            self.vf.logAllFile.close()

        if hasattr(self.vf, 'logSelectFile'):
            self.vf.logSelectFile.close()

        if self.vf.userpref.has_key('Save Perspective on Exit'):
            logPerspective = self.vf.userpref['Save Perspective on Exit']['value']
            if logPerspective == 'yes':
                self.vf.Exit.savePerspective()
            
        if self.pyshell:
            self.pyshell._close()

        self.VIEWER.Exit()

        if self.VIEWER.autoRedraw:
            self.ROOT.update()           

        # this test is a hack to stop a tclerror when destroying ROOT in continuity
        if hasattr(self,'dontDestroyRoot'):
            self.ROOT = None
        else:
            self.ROOT.quit()           
            self.ROOT.destroy()
            self.ROOT = None


    def quit_cb(self):
        #print "ViewerFrameworkGUI.quit_cb"
        self.softquit_cb()
        # added to kill python shell
        if self.withShell:
            try:
                sys.exit(0)      
            finally:        
                os._exit(0) # this is needed to avoid Tracebacks
        else:
            sys.stdin.__exit__() # hack to really exit code.interact


    def __init__(self, viewer, title='ViewerFramework', root=None, tro=1,
                 viewerClass=None, withShell=1, verbose=True):
        """Construct a ViewerFrameworkGUI for the ViewerFramework 'viewer',
            tro is TransformRootOnly for viewer"""
        self.vf = viewer       
        self.TITLE = title
        self.ICONDIR = os.path.join(ICONPATH, '32x32')
        self.toolbarList = []
        self.toolbarCheckbuttons = {}
        if root == None:
            if hasDnD2:
                try:
                    from TkinterDnD2 import TkinterDnD
                    self.ROOT = TkinterDnD.Tk()
                except ImportError:
                    self.ROOT = Tkinter.Tk()
            else:
                self.ROOT = Tkinter.Tk()
            
            if sys.platform=='darwin': 
                self.ROOT.geometry("600x200+20+20")
            else:
                self.ROOT.geometry("+20+20")
        else:
            assert isinstance(root, Tkinter.Tk) or \
                   isinstance(root, Tkinter.Toplevel) or \
                   isinstance(root, Tkinter.Frame) or \
                   isinstance(root, Tkinter.Canvas) 
            self.ROOT = root

        #self.ROOT.bind('<Enter>', self.Enter_cb)
        #self.ROOT.bind('<Leave>', self.Leave_cb)
        self.ROOT.minsize(width = 200, height = 200)
        if isinstance(self.ROOT, Tkinter.Tk) or \
           isinstance(self.ROOT, Tkinter.Toplevel):
            # bind to the close box
            self.ROOT.protocol("WM_DELETE_WINDOW", self.dialog)
            # give a title
            self.ROOT.title(self.TITLE)
            # HOW DO I UPDATE THIS RIGHT AWAY...
            swidth = self.ROOT.winfo_screenwidth()
            sheight = self.ROOT.winfo_screenheight()
            self.ROOT.maxsize(swidth-50, sheight-50)
            # set font size based on screen resolution (Jeff 02/02)

            # use highest priority (i.e. 100) to amke sure that
            # ChangeFont.getCurrentFont() ets this font
            priority=100
            #if self.ROOT.winfo_screenwidth() < 1280:
            #  self.ROOT.option_add(
            #     '*font',(ensureFontCase('helvetica'), 12, 'normal'), priority)
            #else:
            self.ROOT.option_add(
                '*font',(ensureFontCase('helvetica'), 10, 'normal'), priority)

            filePath = findFilePath(fileName = 'Tkinter.defaults',
                                    packageName = 'ViewerFramework')
            if filePath:
                #self.ROOT.option_readfile('./Tkinter.defaults')
                self.ROOT.option_readfile(filePath)

        # create a paned widget
##         self.pw = Pmw.PanedWidget(self.ROOT,
##                                   orient='horizontal',
##                                   hull_borderwidth = 1,
##                                   hull_relief = 'sunken')
##         self.aboveCamPane = self.pw.add('above', min = .1, max = .1)
##         self.cameraPane = self.pw.add('camera', min = .1, max = .1)
##         self.belowCamPane = self.pw.add('below', min = .1, max = .1)

        self.menuBars={}       # dictionary of menubars and buttonbars
            # create frame to hold menubars and buttonbars
        self.mBarFrame = Tkinter.Frame(self.ROOT, borderwidth=2,
                                       relief='raised')
        self.mBarFrame.pack(side='top', expand=0, fill='x')

        # create a paned widget to hold workspace and sequence widget
        self.VPane = Pmw.PanedWidget(
            self.ROOT, orient='vertical', hull_relief='sunken',)
        self.VPane.pack(anchor='n', expand=1, fill='both')
        
        self.workspaceM = self.VPane.add('Workspace', min=200)
        self.workspaceM.pack(anchor='n', expand=1, fill='both')
        
        # workspace is a paned widget in which to pack the camera and
        # other panes such a tools GUI
        self.workspace = Pmw.PanedWidget(
            self.workspaceM, orient='horizontal', hull_relief='sunken',
            separatorthickness=6)

        #hull_width=width, hull_height=height)
        self.workspace.pack(anchor='n', expand=1, fill='both')

        # add a pane for tools such as dashboards and styles
        self.toolsNoteBookMaster = self.workspace.add('ToolsNoteBook',
                                                      min=10)#, size=.4)

##         self.toolsNoteBookMasterWidth = None
##         cb = CallbackFunction(self.workspace.after, 100, self.expandTools)
##         self.toolsNoteBookMaster.bind('<Enter>', cb)
##         cb = CallbackFunction(self.workspace.after, 100, self.collapseTools)
##         self.toolsNoteBookMaster.bind('<Leave>', cb)
        
        # add a pane for camera
        dockCamMaster = self.workspace.add('DockedCamera', min=100)#, size=.6)

        # add button to collapse tools area
        filename = os.path.join(ICONPATH, 'leftarrow1.png')
        self.collapsePhoto = ImageTk.PhotoImage(file=filename)
        filename = os.path.join(ICONPATH, 'rightarrow1.png')
        self.expandPhoto = ImageTk.PhotoImage(file=filename)
        self.collapseToolsW = Tkinter.Button(
            self.toolsNoteBookMaster, image=self.collapsePhoto,
             command=self.collapseTools)
        self.collapseToolsW.pack(side='top', anchor='e')
        
        # add a notebook in the tools area
        self.toolsNoteBook = Pmw.NoteBook(self.toolsNoteBookMaster,
                                          raisecommand=self.raiseToolPage)
        self.toolsNoteBook.pack(fill='both', expand=1, padx=1, pady=1)

        # create a frame for the docked camera
        self.vwrCanvasDocked = Tkinter.Frame(dockCamMaster,
                                             width=500, height=200)
        self.vwrCanvasDocked.pack(side='left', anchor='nw', expand=1,
                                  fill='both')
        self.vwrCanvasDocked.forget()
        
        self.vwrCanvasFloating = Tkinter.Toplevel(width=600, height=600)
        self.vwrCanvasFloating.withdraw()
        self.vwrCanvasFloating.update_idletasks()
        self.vwrCanvasFloating.transient(self.ROOT)

    # build a 3D window
        VIEWER_root = Tkinter.Toplevel()
        VIEWER_root.withdraw()
        self.VIEWER = viewerClass( self.vwrCanvasFloating, 1, autoRedraw=True,
                                   verbose=verbose,guiMaster=VIEWER_root,)
                                   #cnf = {"addScenarioButton": False})

        ## we suspend redraw here to avoid added geoemtries from
        ## triggering unneeded redraws
        self.VIEWER.suspendRedraw = True
        self.VIEWER.TransformRootOnly(tro)
        # create Geom container for misc geoms
        from DejaVu.Geom import Geom
        miscGeom = Geom("misc", shape=(0,0), pickable=0, protected=True)
        miscGeom.isScalable = 0
        miscGeom.animatable = False
        self.VIEWER.AddObject(miscGeom)
        self.miscGeom = miscGeom
        
        # used to make sure only main thread handles expose events
        import thread
        self.mainThread = thread.get_ident()

        # add the InfoBar
        self.infoBar = Tkinter.Frame(self.ROOT,relief = 'sunken', bd = 1)
        self.infoBar.pack(side='bottom', fill='x')
        Tkinter.Label(self.infoBar, text="Mod.:").pack(side='left')

        self.icomLabelMod=Tkinter.Label(self.infoBar, text="None", width=8,
                                        relief='sunken', borderwidth=1,
                                        anchor='w')
        self.icomLabelMod.pack(side='left')

        Tkinter.Label(self.infoBar, text="Time:").pack(side='left')
        self.lastCmdTime=Tkinter.Label(self.infoBar, text="0.0",
                                       width=6, relief='sunken',
                                       borderwidth=1, anchor='w')
        self.lastCmdTime.pack(side='left')
        Tkinter.Label(self.infoBar, text="Selected:").pack(side='left')
        self.pickLabel=Tkinter.Label(self.infoBar, text="None", width=15,
                                     relief='sunken', borderwidth=1,
                                     anchor='w', cursor='hand2')
        self.pickLabel.pack(side='left')
        
        # add DejaVu GUI Checkbutton to Toolbar
        toolbarDict = {}
        toolbarDict['name'] = 'DejaVu_GUI'
        toolbarDict['type'] = 'Checkbutton'
        toolbarDict['icon1'] = '3Dgeom.gif'
        toolbarDict['icon_dir'] = ICONPATH
        toolbarDict['balloonhelp'] = 'DejaVu GUI'
        toolbarDict['index'] = 4
        toolbarDict['cmdcb'] = self.showHideDejaVuGUI
        self.DejaVuGUIVariable = Tkinter.IntVar()
        toolbarDict['variable'] = self.DejaVuGUIVariable
        self.toolbarList.append(toolbarDict) 
        self.VIEWER.GUI.top.master.title('DejaVu GUI')
        self.VIEWER.GUI.top.master.protocol("WM_DELETE_WINDOW",self.showHideDejaVuGUI)
        # add Float Camera Checkbutton to Toolbar
        toolbarDict = {}
        toolbarDict['name'] = 'Float_Camera'
        toolbarDict['type'] = 'Checkbutton'
        toolbarDict['icon1'] = 'float.gif'
        toolbarDict['icon_dir'] = ICONPATH
        toolbarDict['balloonhelp'] = 'Float Camera'
        toolbarDict['index'] = 3
        toolbarDict['cmdcb'] = self.floatCamera_cb
        self.floatCamVariable = Tkinter.IntVar()
        self.floatCamVariable.set(1)
        toolbarDict['variable'] = self.floatCamVariable
        self.toolbarList.append(toolbarDict) 

        # add the busy indicator
        self.currentState = self.previousState = 'idle' # can be 'busy' or 'redraw' or 'idle'
        # flag when turn on the idle light cannot be changed
        self.suspendLight = False
        self.busyLight=Tkinter.Frame(self.infoBar, relief=Tkinter.SUNKEN,
                                     borderwidth=1)

        self.suspendLight = False
        
        self.idleImage = os.path.join(self.ICONDIR,'idle.gif')
        self.redrawImage = os.path.join(self.ICONDIR,'redraw.gif')
        self.busyImage = os.path.join(self.ICONDIR,'busy.gif')
        self.busyIcon = Tkinter.PhotoImage(file=self.idleImage, master=self.ROOT)
        self.busyCanvas = Tkinter.Canvas(self.busyLight,
                                         width=self.busyIcon.width(),
                                         height=self.busyIcon.height() - 4 )
        self.busyCanvas.create_image(0, 0, anchor = Tkinter.NW,
                                     image=self.busyIcon)
        self.busyCanvas.pack()
        self.busyLight.pack(side='right')
        
        # add the frameRate indicator
        self.frameRateTk=Tkinter.Label(self.infoBar, relief=Tkinter.SUNKEN,
                                       borderwidth=1, width=5, text="00.0")
        self.frameRateTk.pack(side='right')
        Tkinter.Label(self.infoBar, text="FR:").pack(side='right')


        # spinOptionMenu
        lSpinTuple = ('Spin off', 'Spin', 'Bounce', 'Oscillate', 'Show settings')
        def spinOptionMenuFunc(val):
            lSpinVar = self.VIEWER.currentCamera.trackball.spinVar.get()
            self.VIEWER.currentCamera.trackball.lastSpinVar = 0
            if val == 'Show settings':
                self.VIEWER.currentCamera.trackball.showSpinGui()
                self.spinOptionMenu.invoke(lSpinVar)
            else:
                lSpinItems = {'Spin off':0, 'Spin':1, 'Bounce':2, 'Oscillate':3 }
                if lSpinVar != lSpinItems[val]:
                    self.VIEWER.currentCamera.trackball.spinVar.set(lSpinItems[val])
                self.VIEWER.currentCamera.trackball.toggleCycle(docb=False)
        from DejaVu import defaultSpinningMode
        self.spinOptionMenu = Pmw.OptionMenu(
                                     self.infoBar, 
                                     initialitem=lSpinTuple[defaultSpinningMode],
                                     command=spinOptionMenuFunc,
                                     items=lSpinTuple,
                                     menubutton_pady=0,
                                     )
        self.VIEWER.spinCallBack = self.spinOptionMenu.invoke
        self.spinOptionMenu.pack(side='right')

        self.VIEWER.beforeRebuildDpyLists = self.beforeRebuildDpyLists
        self.VIEWER.afterRebuildDpyLists = self.afterRebuildDpyLists
        self.VIEWER.afterRedraw = self.afterRedraw

        self.screenHeight = self.ROOT.winfo_screenheight()
        self.screenWidth = self.ROOT.winfo_screenwidth()

        # scrollable text to log the events
        self.MESSAGE_BOX = None
        self.set_up_message_box('')

        # create the Python shell
        self.withShell = withShell

        if self.withShell:
            self.pyshell = getShell(self.mainThread, rootTk = self.ROOT,
                                    enable_shell=True, enable_edit=False,
                                    debug=False)
            self.pyshell.menubar.children['file'].delete('Close','Exit')
            self.pyshell.menubar.children['file'].add_command(
                label='Clear Ouput', command=self.clearPyShell )
            # hide it
            self.pyshell.top.withdraw()
            self.pyshell.begin()
        else:
            self.pyshell = None

        Tkinter._default_root = self.ROOT

        #FIXME this won't work when we have multiple cameras
    #self.ehm = self.VIEWER.cameras[0].eventManager

        # stack to store name of current cursor before setting a newOne
        self.oldcursor = []

        # instanciate the progress bar widget and 2 callable objects
        self.progressBar = ProgressBar(master=self.infoBar, labelside=None,
                                       width=150, height=15, mode='percent')
        self.progressBarConf = ProgressBarConf(self.progressBar)
        self.progressBarUpd  = ProgressBarUpd(self.progressBar)

        # Position the floating camera above the menu bar and set
        # its width to the width -100 of the menu.
        cam = self.VIEWER.currentCamera
        import DejaVu
        if isinstance(cam,DejaVu.Camera.Camera):
            self.VIEWER.currentCamera.frame.master.protocol("WM_DELETE_WINDOW",self.camdialog)
        cposx = cam.winfo_x()
        cposy = cam.winfo_y()
        posx, posy, w, h = self.getGeom()
        camwidth = w - 150
        if camwidth <=0 :
            camwidth = 500
        cam.Set(rootx=posx, rooty=posy, width=camwidth)
        camheight = cam.winfo_height()
        # need to make sure that this is not outside of the screen.
        #self.setGeom(posx, posy+camheight+80, int(w), int(h)+50)
        self.ROOT.geometry('+%s+%s' % ( posx, posy+camheight+8) )
        self.naturalSize()

        self.VIEWER.suspendRedraw = False

        self.addCameraCallback('<KeyPress>', self.updateInfoBar)
        self.addCameraCallback('<KeyRelease>',self.updateInfoBar)

        if hasDnD2:
            if hasattr(self.ROOT, "drop_target_register"):
                self.ROOT.drop_target_register('*') # make root drop target
                self.ROOT.dnd_bind('<<Drop>>', self.drop) # drop call back


    def raiseToolPage(self, page):
        # create an event when page is selected in the Tools notebook
        event = RaiseToolPageEvent( page)
        self.vf.dispatchEvent( event )
        
        
    
    def collapseTools(self, event=None):
        # get starting width
        self.toolsNoteBookMasterWidth = width = self.toolsNoteBookMaster.winfo_width()
        workspace = self.workspace
        nbSteps = 10.
        w = self.collapseToolsW.winfo_width()
        dx = (width-w)/(nbSteps-1)
        for i in range(int(nbSteps)):
            w = width - i*dx
            workspace.configurepane('ToolsNoteBook', size=int(w))
        self.collapseToolsW.configure(image=self.expandPhoto,
                                      command=self.expandTools)


    def expandTools(self, event=None):
        width = self.toolsNoteBookMasterWidth
        if width is None:
            return
        workspace = self.workspace
        nbSteps = 10
        dx = (width-10)/(nbSteps-1)
        for i in range(nbSteps):
            w = 10 + i*dx
            workspace.configurepane('ToolsNoteBook', size=int(w))
        self.collapseToolsW.configure(image=self.collapsePhoto,
                                      command=self.collapseTools)


    def drop_cb(self, files):
        # to be overriden
        for f in files:
            print f


    def drop(self, event):
        #print 'Dropped file(s):', type(event.data), event.data
        if event.data:
            # windows file name with space are between { }
            if '{' in event.data:
                files = []
                file = ''
                for c in event.data:
                    if c=='{': continue
                    if c=='}':
                        files.append(file)
                        file = ''
                        continue
                    file+=c
            else:
                files = event.data.split()
            self.drop_cb(files)
        return COPY


    def updateInfoBar(self, event=None):
        vi = self.VIEWER
        if vi.isShift(): mod='Shift_L'
        elif vi.isControl(): mod='Control_L'
        elif vi.isAlt(): mod='Alt_L'
        else: mod=None
        self.icomLabelMod.configure( text=str(mod) )


    def naturalSize(self):
        self.ROOT.update()
        w = self.ROOT.winfo_reqwidth()
        h = self.ROOT.winfo_reqheight()
        self.ROOT.geometry('%dx%d' % ( w, h) )


    def removeCameraCallback(self, event, function):
        """
        Remove function as a call back to the event handler
        managers of all cameras
        """
        for c in self.VIEWER.cameras:
            c.eventManager.RemoveCallback(event, function)


    def addCameraCallback(self, event, function):
        """Add function as a call back to the event handler managers of all
        cameras
        """
        for c in self.VIEWER.cameras:
            c.eventManager.AddCallback(event, function)


    def isCameraFloating(self):
        """returns true id camera is floating and false if it is docked
"""
        return self.floatCamVariable.get()==1


    def rebuildCamera(self, stereo=None):
        #print "rebuildCamera"

        vi = self.VIEWER
        vi.stopAutoRedraw()

        # get the position and the height of the camera
        cam = vi.currentCamera
        camx = cam.rootx
        camy = cam.rooty
        camheight = cam.height
        camwidth = cam.width

        # save the currentCamera camera state
        camState = cam.getState()
        fogState = cam.fog.getState()
        camCallbacks = cam.eventManager.eventHandlers
        if stereo is None:
            if cam.stereoMode == 'STEREO_BUFFERS':
                stereo = 'native'
            else:
                stereo = 'none'

        # get the camera canvas
        if self.vwrCanvasDocked.winfo_ismapped():
            lCameraCanvas = self.vwrCanvasDocked
        else:
            lCameraCanvas = self.vwrCanvasFloating           

        # withdraw the trackball gui (because it belongs to the camera)
        cam.trackball.hideSpinGui()

        vi.removeAllTheDisplayListsExceptTemplatesAndVBO()
        for g in vi.rootObject.AllObjects():
            if hasattr(g, 'templateDSPL'):
                g.deleteTemplate()        

        # Create a new camera in lCameraCanvas
        lNewCam = vi.AddCamera(master=lCameraCanvas, stereo=stereo)

        for g in vi.rootObject.AllObjects():
            if hasattr(g, 'templateDSPL'):
                g.makeTemplate()        

        # attach the new trackball gui to the viewergui
        vi.GUI.spinMenuButton.configure(command=lNewCam.trackball.toggleSpinGui)
        lNewCam.trackball.set(cam.trackball)

        # Delete the previous camera
        lNewCamIndex = len(vi.cameras) - 1
        lNewCam.shareCTXWith = vi.cameras[0].shareCTXWith
        lNewCam.shareCTXWith.remove(lNewCam)
        lNewCam.shareCTXWith.append(vi.cameras[0])
        del(vi.cameras[0].shareCTXWith)
        lNewCam.SelectCamera()
        cam.Set(height=vi.cameras[0].height, width=vi.cameras[0].width)
        lCamTemp = vi.cameras[0]
        vi.cameras[0] = vi.cameras[lNewCamIndex]
        vi.cameras[lNewCamIndex] = lCamTemp
        vi.DeleteCamera(vi.cameras[lNewCamIndex])
        cam = vi.currentCamera

        # Restore the light model
        vi.lightModel.apply()
        for l in vi.lights:
            if l.enabled:
                l.apply()

        # Restore the state of the camera
        lNewCamState = cam.getState()
        for key, value in lNewCamState.items():
            if camState.has_key(key) and value == camState[key]:
                camState.pop(key)
        apply(cam.Set,(1, 0), camState )
        apply(cam.fog.Set,(), fogState)
        vi.startAutoRedraw()

        cam.Expose()  #to update projection
        cam.Enter_cb() # as current Camera
        events = ['<KeyPress>', '<KeyRelease>']
        for event in events:
            for cb in camCallbacks[event]:
                if not cb in cam.eventManager.eventHandlers[event]:
                    self.addCameraCallback(event, cb)

        # Overwrite the Camera DoPick by the viewerFramework DoPick method.
        cam.DoPick = self.vf.DoPick


    def floatCamera_cb(self, event=None):
        if self.floatCamVariable.get()==1:
            self.floatCamera()
        else:
            self.dockCamera()


    def dockCamera(self, stereo=None):
        #print "dockCamera"

        # to avoid going twice in the func at startup as it creates 
        # problems if _pmvrc contains a call to dockCamera()
        if self.vwrCanvasDocked.winfo_ismapped() == 0 \
           and self.vwrCanvasFloating.winfo_ismapped() == 0 \
           and self.floatCamVariable.get() == 0 :
                return

        if self.vwrCanvasDocked.winfo_ismapped():
            # the camera is already docked
            return
        else:
            if self.floatCamVariable.get() == 1:
                self.floatCamVariable.set(0)
        vi = self.VIEWER
        vi.stopAutoRedraw()

        # get the position and the height of the floating camera
        cam = vi.currentCamera
        camx = cam.rootx
        camy = cam.rooty
        camheight = cam.height
        camwidth = cam.width
        # the currentCamera is floating
        # save the floating camera state
        camState = cam.getState()
        fogState = cam.fog.getState()
        camCallbacks = cam.eventManager.eventHandlers
        if stereo is None:
            if cam.stereoMode == 'STEREO_BUFFERS':
                stereo = 'native'
            else:
                stereo = 'none'
        self.vwrCanvasFloating.withdraw()

        # withdraw the trackball gui (because it belongs to the camera)
        cam.trackball.hideSpinGui()

        # Create a new camera in vwrCanvasDocked
        lNewCam = vi.AddCamera(master=self.vwrCanvasDocked, stereo=stereo)
        
        # attach the new trackball gui to the viewergui
        vi.GUI.spinMenuButton.configure(command=lNewCam.trackball.toggleSpinGui)
        lNewCam.trackball.set(cam.trackball)

        # Delete the floating camera
        lNewCamIndex = len(vi.cameras) - 1
        #lNewCam = vi.cameras[lNewCamIndex]
        lNewCam.shareCTXWith = vi.cameras[0].shareCTXWith
        lNewCam.shareCTXWith.remove(lNewCam)
        lNewCam.shareCTXWith.append(vi.cameras[0])
        del(vi.cameras[0].shareCTXWith)
        lNewCam.SelectCamera()
        cam.Set(height=vi.cameras[0].height, width=vi.cameras[0].width)
        lCamTemp = vi.cameras[0]
        vi.cameras[0] = vi.cameras[lNewCamIndex]
        vi.cameras[lNewCamIndex] = lCamTemp
        vi.DeleteCamera(vi.cameras[lNewCamIndex])
        cam = vi.currentCamera

        # Restore the state of the floating camera
        lNewCamState = cam.getState()
        for key, value in lNewCamState.items():
            if camState.has_key(key) and value == camState[key]:
                camState.pop(key)
        apply(cam.Set,(1, 0),camState )
        apply(cam.fog.Set,(), fogState)
        vi.startAutoRedraw()
## MS no longer needed as camera is in its  own pane
##         # See if infobar then need to pack it before infobar.
##         if hasattr(self,'infoBar'):
##             infobar = self.infoBar
##             w1 = self.vf.showHideGUI.getWidget('MESSAGE_BOX')
##             if w1.winfo_ismapped():
##                 self.vwrCanvasDocked.pack(before=w1,anchor='n',
##                                           expand=1, fill='both')            
##             elif infobar.winfo_ismapped():
##                 self.vwrCanvasDocked.pack(before=infobar,anchor='n',
##                                           expand=1, fill='both')
##             else:
##                 self.vwrCanvasDocked.pack(anchor='n', expand=1, fill='both')
##         else:
##             self.vwrCanvasDocked.pack(anchor='n',expand=1, fill='both')
        # see if text messages box is visible
        w1 = self.vf.showHideGUI.getWidget('MESSAGE_BOX')
        if w1.winfo_ismapped():
            self.vwrCanvasDocked.pack(before=w1,anchor='n',
                                      expand=1, fill='both')
        else:
            self.vwrCanvasDocked.pack(anchor='n',expand=1, fill='both')

        cam.Expose()  #to update projection
        cam.Enter_cb() # as current Camera
        #self.addCameraCallback('<KeyPress>', self.updateInfoBar)
        #self.addCameraCallback('<KeyRelease>',self.updateInfoBar)
        events = ['<KeyPress>', '<KeyRelease>']
        for event in events:
            for cb in camCallbacks[event]:
                if not cb in cam.eventManager.eventHandlers[event]:
                    self.addCameraCallback(event, cb)

        # Overwrite the Camera DoPick by the viewerFramework DoPick method.
        cam.DoPick = self.vf.DoPick

        # Need to reposition and resize the menubar.
        menux, menuy, menuw, menuh = self.getGeom()

        width = max(menuw, camwidth)
        height = menuh + camheight
        self.setGeom(camx, 0, width, height)
        crooty = menuy+menuh-30
        cam.Set(rootx=camx, rooty=crooty,
                             width=width, height=camheight)
        if self.vf.logMode != 'no':
            txt = "self.GUI.dockCamera(stereo=\""+str(stereo)+"\")"
            self.vf.log(txt)
            self.MESSAGE_BOX.append(txt+"\n")
        

    def camdialog(self):
        import tkMessageBox
        ok = tkMessageBox.askokcancel("Quit camdialog?","Do you Wish to Quit?")
        if ok:
            self.quit_cb()
        else:
            return


    def floatCamera(self, stereo=None, parent=None):
        if parent is None:
            vwrCanvasFloating = self.vwrCanvasFloating
            if vwrCanvasFloating.winfo_ismapped():
                return
            else:
                if self.floatCamVariable.get()==0:
                    self.floatCamVariable.set(1)
        else:
            vwrCanvasFloating = parent

        vi = self.VIEWER
        vi.stopAutoRedraw()

        # the currentCamera is docking
        # save the docking camera state
        cam = vi.currentCamera
        camState = cam.getState()
        fogState = cam.fog.getState()
        camCallbacks = cam.eventManager.eventHandlers
        if stereo is None:
            if cam.stereoMode == 'STEREO_BUFFERS':
                stereo = 'native'
            else:
                stereo = 'none'
        self.vwrCanvasDocked.forget()

        # withdraw the trackball gui (because it belongs to the camera)
        cam.trackball.hideSpinGui()

        # Create a new camera in vwrCanvasFloating
        lNewCam = vi.AddCamera(master=vwrCanvasFloating, stereo=stereo)

        # attach the new trackball gui to the viewergui
        vi.GUI.spinMenuButton.configure(command=lNewCam.trackball.toggleSpinGui)
        lNewCam.trackball.set(cam.trackball)

        # Delete the floating camera
        lNewCamIndex = len(vi.cameras) - 1
        #lNewCam = vi.cameras[lNewCamIndex]
        lNewCam.shareCTXWith = vi.cameras[0].shareCTXWith
        lNewCam.shareCTXWith.remove(lNewCam)
        lNewCam.shareCTXWith.append(vi.cameras[0])

        del(vi.cameras[0].shareCTXWith)
        lNewCam.SelectCamera()
        lNewCam.Set(height=vi.cameras[0].height, width=vi.cameras[0].width)
        lCamTemp = vi.cameras[0]
        vi.cameras[0] = vi.cameras[lNewCamIndex]
        vi.cameras[lNewCamIndex] = lCamTemp
        vi.DeleteCamera(vi.cameras[lNewCamIndex])
        cam = vi.currentCamera

        # Restore the state of the docking camera
        lNewCamState = cam.getState()
        for key, value in lNewCamState.items():
            if camState.has_key(key) and value == camState[key]:
                camState.pop(key)
        apply(cam.Set,(1, 0),camState )
        apply(cam.fog.Set,(), fogState)
        vi.startAutoRedraw()
        vwrCanvasFloating.deiconify()
        cam.Expose()  # for to update projection
        cam.Enter_cb(None) # for as current Camera

        # Overwrite the Camera DoPick by the viewerFramework DoPick method.
        cam.DoPick = self.vf.DoPick

        # Need to reposition and resize the menu bar and the camera
        # get the position and the height of the floating camera
        camx = cam.rootx
        camy = cam.rooty
        camheight = cam.height
        camwidth = cam.width

        menux, menuy, menuw, menuh = self.getGeom()
        width = menuw
        height = menuh - camheight
        rooty = menuy + camheight + 35 #35 leaves space for window decoration
        rootx = menux
        #cam.Set(rootx=rootx, rooty=menuy+1)
        cam.Enter_cb()
        #self.addCameraCallback('<KeyPress>', self.updateInfoBar)
        #self.addCameraCallback('<KeyRelease>',self.updateInfoBar)
        events = ['<KeyPress>', '<KeyRelease>']
        for event in events:
            for cb in camCallbacks[event]:
                if not cb in cam.eventManager.eventHandlers[event]:
                    self.addCameraCallback(event, cb)
        self.setGeom(rootx, rooty, width, self.ROOT.winfo_reqheight())

        cam.frame.master.protocol("WM_DELETE_WINDOW",self.camdialog)
        if self.vf.logMode != 'no':
            txt = "self.GUI.floatCamera(stereo=\""+str(stereo)+"\")"
            self.vf.log(txt)
            self.MESSAGE_BOX.append(txt+"\n")
            

    def showHideDejaVuGUI(self):
        """show and hide the original DejaVu GUI."""
        if self.VIEWER.GUI.shown:
            self.VIEWER.GUI.withdraw()
            self.DejaVuGUIVariable.set(0)
        else:
            self.VIEWER.GUI.deiconify()
            self.DejaVuGUIVariable.set(1)

    def geometry(self, width, height, xoffset=None, yoffset=None):
        """(width, height) <- geometry(width, height, xoffset=None, yoffset=None)
configure the DejaVu camera to have the given height and width
the xoffset and yoffset specify the upper left corner of the GUI
"""

        vi = self.VIEWER
        cam = vi.cameras[0]

        # get dimensions of top window
        master = cam.frame.master.master
        dims = map(int, ((master.geometry()).split('+')[0]).split('x'))

        # first we set the width because it migh change the height of menus
        # we add 6 for the 2x3 camera border pixels
        geomstring = "%dx%d"%(width+6, dims[1])
        if xoffset is not None:
            geomstring += "+%d"%xoffset
        if yoffset is not None:
            geomstring += "+%d"%yoffset

        # set the cam width and x,y offset
        vi.master.master.geometry(geomstring)
        cam.update()
        
        # compute the difference between the cam height and the top window
        # height
        dy = dims[1] - cam.height
        
        geomstring = "%dx%d"%(width+6, height+dy)
        vi.master.master.geometry(geomstring)
        cam.update()

        return cam.width, cam.height


    def showHideProgressBar_CB(self, name, oldvalue, value):
        #this callback is called when the user preference is set
        if value == 'hide':
            self.progressBar.hide()
        elif value == 'show':
            self.progressBar.show()
            

    def clearPyShell(self, event=None):
        self.pyshell.text.delete("1.0", "end-1c")

    def TB_cb(self, event=None):
        on = self.toolbarCheckbuttons['MESSAGE_BOX']['Variable'].get()
        self.vf.showHideGUI('MESSAGE_BOX', on)
        

##     def setGeometryX(self):
##         v = self.geometryX.get()
##         x, y, w, h = self.getGeom()
##         if v:
##             self.setGeom( v, y, w, h)
##         else:
##             self.geometryX.setentry(x)
                                 
##     def setGeometryY(self):
##         v = self.geometryY.get()
##         x, y, w, h = self.getGeom()
##         if v:
##             self.setGeom( x, v, w, h)
##         else:
##             self.geometryY.setentry(y)

##     def setGeometryW(self):
##         v = self.geometryW.get()
##         x, y, w, h = self.getGeom()
##         if v:
##             self.setGeom( x, y, v, h)
##         else:
##             self.geometryW.setentry(w)

##     def setGeometryH(self):
##         v = self.geometryH.get()
##         x, y, w, h = self.getGeom()
##         if v:
##             self.setGeom( x, y, w, v)
##         else:
##             self.geometryH.setentry(h)

    def setGeom(self, posx, posy, width, height):
        self.ROOT.geometry('%dx%d+%d+%d' % (width, height, posx, posy) )

      
    def getGeom(self):
        geom = self.ROOT.winfo_geometry()
        size, x, y = string.split(geom, '+')
        w, h = string.split(size, 'x')
        return int(x), int(y), int(w), int(h)


    def belowCamera(self):
        """
move the menu window under the Camera
"""
        if self.isCameraFloating():
            menux, menuy, menuw, menuh = self.getGeom()
            camgeom = self.VIEWER.cameras[0].winfo_toplevel().geometry()
            camw, rest = camgeom.split('x')
            camw = int(camw)
            camh, camx, camy = [int(n) for n in rest.split('+')]
            screenh = self.ROOT.winfo_screenheight()
            if camy+camh+menuh+25 < screenh:
                self.setGeom(camx, camy+camh+25,menuw, menuh)
            else:
                diff = camy+camh+menuh+25-screenh
                self.setGeom(camx, camy+camh+25-diff,menuw, menuh)
                
## this configure was causing all the beeping on resize
## and was only use to update the X, Y W and H entries
## so I removed them
    
##     def configure_cb(self, event=None):
        
##         x, y, w, h = self.getGeom()
##         self.geometryX.setentry(x)
##         self.geometryY.setentry(y)
##         self.geometryW.setentry(w)
##         self.geometryH.setentry(h)


    def setIdleLight(self, state):
        if self.ROOT is None:
            return

        from os import path
        self.previousState = path.basename(self.busyIcon.cget('file'))[:-4]
        if state == 'idle':
            self.suspendLight = True
            # turn led green
            self.busyIcon.config(file=self.idleImage)
            if self.VIEWER.autoRedraw:
                self.busyCanvas.update()
            self.suspendLight = False
            if self.ROOT is None:
                return
            self.ROOT.config(cursor='')
            self.VIEWER.master.config(cursor='')    
            self.MESSAGE_BOX.tx.component('text').config(cursor='xterm')
            

        elif state == 'busy':
            self.ROOT.config(cursor='watch')
            self.VIEWER.master.config(cursor='watch')    
            self.MESSAGE_BOX.tx.component('text').config(cursor='watch')
            self.suspendLight = True
            # turn led red
            self.busyIcon.config(file=self.busyImage)
            if self.VIEWER.autoRedraw:
                self.busyCanvas.update()
            self.suspendLight = False
            
        elif state == 'redraw':
            self.ROOT.config(cursor='watch')
            self.VIEWER.master.config(cursor='watch')    
            self.MESSAGE_BOX.tx.component('text').config(cursor='watch')
            self.suspendLight = True
            # turn led purple
            self.busyIcon.config(file=self.redrawImage)
            if self.VIEWER.autoRedraw:
                self.busyCanvas.update()
            self.suspendLight = False
            
        self.currentState = path.basename(self.busyIcon.cget('file'))[:-4]


    def setCursor(self, newCursor):
        """Set the cursor. list can be found in /usr/include/X11/cursorfont.h
        but remove the leading 'XC_' string"""
        if self.vf.userpref['changeCursor']['value']:
            c = self.vwrCanvasDocked.cget('cursor')
            self.vwrCanvasDocked.configure(cursor=newCursor)    
            return c
        else: return ''


    def busyRedraw(self, cursor=None):
        self.setIdleLight('redraw')

    def busy(self, cursor=None):
        self.setIdleLight('busy')
        
    def idle(self):
        self.setIdleLight('idle')


    def configureProgressBar(self, **kw):
        # configure progress bar such as mode and max, size etc 
        apply(self.progressBar.configure, (), kw)
        

    def updateProgressBar(self, progress=None):
        # set the progress bar to a given value
        self.progressBar.set(progress)
        

    def setShiftFlag(self,event):
        self.shiftFlag=1


    def unSetShiftFlag(self,event):
        if event.state == 513:
            self.logScale(event)
        self.shiftFlag=0


    def logUserPref_cb(self, name,old, new):
        if new=='continuous':
            # Bind all the Keys Releases to be able to log transformations.
            self.shiftFlag=0
            self.pendingLog = []
            self.addCameraCallback("<ButtonRelease-2>", self.logRotation)
            self.addCameraCallback("<ButtonRelease-3>", self.logTranslation)
            self.addCameraCallback("<Shift-ButtonRelease-3>",self.logTranslation)
            self.addCameraCallback("<Shift-ButtonRelease-2>", self.logScale)
            self.addCameraCallback("<Shift-ButtonRelease-1>", self.logPivot)
            self.addCameraCallback("<Shift-Button-1>", self.setShiftFlag)
            self.addCameraCallback("<Shift-Button-2>", self.setShiftFlag)
            self.addCameraCallback("<Shift-Button-3>", self.setShiftFlag)
            self.addCameraCallback("<KeyRelease>", self.unSetShiftFlag)
##             self.ehm.AddCallback("<ButtonRelease-2>", self.logRotation)
##             self.ehm.AddCallback("<ButtonRelease-3>", self.logTranslation)
##             self.ehm.AddCallback("<Shift-ButtonRelease-3>",self.logTranslation)
##             self.ehm.AddCallback("<Shift-ButtonRelease-2>", self.logScale)
##             self.ehm.AddCallback("<Shift-ButtonRelease-1>", self.logPivot)

##             self.ehm.AddCallback("<Shift-Button-1>", self.setShiftFlag)
##             self.ehm.AddCallback("<Shift-Button-2>", self.setShiftFlag)
##             self.ehm.AddCallback("<Shift-Button-3>", self.setShiftFlag)
##             self.ehm.AddCallback("<KeyRelease>", self.unSetShiftFlag)
            if os.name == 'nt': #sys.platform == 'win32':
                self.addCameraCallback("<MouseWheel>", self.logFOV)
            else:
                self.addCameraCallback("<Button-4>", self.logFOV)
                self.addCameraCallback("<Button-5>", self.logFOV)
        elif old=='continuous':
            self.removeCameraCallback("<ButtonRelease-2>", self.logRotation)
            self.removeCameraCallback("<ButtonRelease-3>", self.logTranslation)
            self.removeCameraCallback("<Shift-ButtonRelease-3>",
                                    self.logTranslation)
            self.removeCameraCallback("<Shift-ButtonRelease-2>", self.logScale)
            self.removeCameraCallback("<Shift-ButtonRelease-1>", self.logPivot)
            self.removeCameraCallback("<Shift-Button-1>", self.setShiftFlag)
            self.removeCameraCallback("<Shift-Button-2>", self.setShiftFlag)
            self.removeCameraCallback("<Shift-Button-3>", self.setShiftFlag)
            self.removeCameraCallback("<KeyRelease>", self.unSetShiftFlag)
            if os.name == 'nt': #sys.platform == 'win32':
                self.removeCameraCallback("<MouseWheel>", self.logFOV)
            else:
                self.removeCameraCallback("<Button-4>", self.logFOV)
                self.removeCameraCallback("<Button-5>", self.logFOV)
 ##             self.ehm.RemoveCallback("<ButtonRelease-2>", self.logRotation)
##             self.ehm.RemoveCallback("<ButtonRelease-3>", self.logTranslation)
##             self.ehm.RemoveCallback("<Shift-ButtonRelease-3>",
##                                     self.logTranslation)
##             self.ehm.RemoveCallback("<Shift-ButtonRelease-2>", self.logScale)
##             self.ehm.RemoveCallback("<Shift-ButtonRelease-1>", self.logPivot)
                     
##             self.ehm.RemoveCallback("<Shift-Button-1>", self.setShiftFlag)
##             self.ehm.RemoveCallback("<Shift-Button-2>", self.setShiftFlag)
##             self.ehm.RemoveCallback("<Shift-Button-3>", self.setShiftFlag)
##             self.ehm.RemoveCallback("<KeyRelease>", self.unSetShiftFlag)

            
    def logRotation(self, event):
        
        mode = self.VIEWER.currentCamera.currentTransfMode

        #if self.pendingLog and self.pendingLog[0] != 'rotation':
        #    self.vf.log(self.pendingLog[-1])
        #    self.pendingLog = []
        
        if mode == 'Object':
            obj = self.VIEWER.currentObject
            if self.pendingLog and \
               (self.pendingLog[1] != 'object' or \
                self.pendingLog[2]!=obj.name):
                self.vf.log(self.pendingLog[-1])
            log = "self.transformObject('rotation', '%s', matrix=(%9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f),log=0)"%((obj.name,)+tuple(obj.rotation))
            self.pendingLog = ["rotation","object",obj.name,log]

        elif mode == 'Clip':
            clip = self.VIEWER.currentClip
            if self.pendingLog and \
               (self.pendingLog[1] != 'clip' or \
                self.pendingLog[2]!=clip.name):
                self.vf.log(self.pendingLog[-1])

            log = "self.setClip('%s', ratation=(%9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f),log = 0)"%((clip.name,)+tuple(clip.rotation))
            self.pendingLog = ["rotation","clip",clip.name,log]
            
        elif mode == 'Camera':
            cam = self.VIEWER.currentCamera
            if self.pendingLog and \
               (self.pendingLog[1] != 'camera' or \
                self.pendingLog[2]!=cam.name):
                self.vf.log(self.pendingLog[-1])
            log = "self.setCamera('%s', rotation=(%9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f),log = 0)"%((cam.name,)+tuple(cam.rotation))
            self.pendingLog = ["rotation","camera",cam.name,log]

        elif mode == 'Light':
            light = self.VIEWER.currentLight
            if self.pendingLog and \
               (self.pendingLog[1] != 'light' or \
                self.pendingLog[2]!=light.name):
                self.vf.log(self.pendingLog[-1])
            if not light.positional:
                log = "self.setLight('%s', direction=(%9.3f, %9.3f, %9.3f, %9.3f),log = 0)"%((light.name,)+tuple(light.direction))
                self.pendingLog = ["rotation","light",light.name, log]

        elif mode == 'Texture':
            print 'log rotation Texture'
        self.vf.log(self.pendingLog[-1])

        
    def logTranslation(self, event):
        mode = self.VIEWER.currentCamera.currentTransfMode
##          if self.pendingLog and self.pendingLog[0] != 'translation':
##              self.vf.log(self.pendingLog[-1])
##              self.pendingLog = []
            
        if mode == 'Object':
            obj = self.VIEWER.currentObject
            if self.pendingLog and \
               (self.pendingLog[1] != 'object' or \
                self.pendingLog[2]!=obj.name):
                self.vf.log(self.pendingLog[-1])

            log = "self.transformObject('translation', '%s', matrix=(%9.3f, %9.3f, %9.3f), log=0 )"%((obj.name,)+tuple(obj.translation))
            self.pendingLog = ["translation","object",obj.name,log]

        elif mode == 'Clip':
            clip = self.VIEWER.currentClip
            if self.pendingLog and \
               (self.pendingLog[1] != 'clip' or \
                self.pendingLog[2]!=clip.name):
                self.vf.log(self.pendingLog[-1])

            log="self.setClip('%s', translation=(%9.3f, %9.3f, %9.3f), log=0 )"%((clip.name,)+tuple(clip.translation))
            self.pendingLog = ["translation","clip",clip.name,log]

        elif mode == 'Camera':
            cam = self.VIEWER.currentCamera
            if self.pendingLog and \
               (self.pendingLog[1] != 'camera' or \
                self.pendingLog[2]!=cam.name):
                self.vf.log(self.pendingLog[-1])

            log = "self.setCamera('%s', translation=(%9.3f, %9.3f, %9.3f), log=0 )"%((cam.name,)+tuple(cam.translation))
            self.pendingLog = ["translation","camera",cam.name,log]

        elif mode == 'Texture':
            print 'log translationtion Texture'

        self.vf.log(self.pendingLog[-1])


    def logScale(self, event):
        mode = self.VIEWER.currentCamera.currentTransfMode
##          if self.pendingLog and self.pendingLog[0] != 'scale':
##              self.vf.log(self.pendingLog[-1])
##              self.pendingLog = []

        if mode == 'Object':
            obj = self.VIEWER.currentObject
            if self.pendingLog and \
               (self.pendingLog[1] != 'object' or \
                self.pendingLog[2]!=obj.name):
                self.vf.log(self.pendingLog[-1])

            log = "self.transformObject('scale', '%s', matrix=(%2.7f, %2.7f, %2.7f), log=0 )"%((obj.name,)+tuple(obj.scale))
            self.pendingLog = ["scale","object",obj.name,log]

        elif mode == 'Clip':
            clip= self.VIEWER.currentClip
            if self.pendingLog and \
               (self.pendingLog[1] != 'clip' or \
                self.pendingLog[2]!=clip.name):
                self.vf.log(self.pendingLog[-1])

            log = "self.setClip('%s', scale=(%2.7f, %2.7f, %2.7f), log=0 )"%((clip.name,)+tuple(clip.scale))
            self.pendingLog = ["scale","clip",clip.name,log]

        elif mode == 'Camera':
            camera = self.VIEWER.currentCamera
            if self.pendingLog and \
               (self.pendingLog[1] != 'camera' or \
                self.pendingLog[2]!=camera.name):
                self.vf.log(self.pendingLog[-1])

            log = "self.setCamera('%s', scale=(%2.7f, %2.7f, %2.7f), log=0 )"%((camera.name,)+tuple(camera.scale))
            self.pendingLog = ["scale","camera",camera.name,log]
            
        elif mode == 'Texture':
            print 'log scale Texture'

        self.vf.log(self.pendingLog[-1])


    def logPivot(self, event):
        mode = self.VIEWER.currentCamera.currentTransfMode
##          if self.pendingLog and self.pendingLog[0] != 'pivot':
##              self.vf.log(self.pendingLog[-1])
##              self.pendingLog = []
        
        if mode == 'Object':
            obj = self.VIEWER.currentObject
            if self.pendingLog and \
               (self.pendingLog[1] != 'object' or \
                self.pendingLog[2]!=obj.name):
                self.vf.log(self.pendingLog[-1])
            log = "self.transformObject('pivot', '%s', matrix=(%9.3f, %9.3f, %9.3f), log=0 )"%((obj.name,)+tuple(obj.pivot))
            self.pendingLog = ["pivot","object",obj.name,log]

        self.vf.log(self.pendingLog[-1])

        
    def logFOV(self, event):
        cam = self.VIEWER.currentCamera
        log = "self.transformCamera('fov', matrix=%6.3f, log=0 )"%(cam.fovy)
        self.vf.log(log)

        
    def set_up_message_box(self, welcome_message=''):
        """ set up the message box with a welcome message """
        
        # already defined : retreat
        if self.MESSAGE_BOX != None:
            return
        
        self.MESSAGE_BOX = msg_box(self.ROOT, welcome_message)
        self.MESSAGE_BOX.forget()
        toolbarDict = {}
        toolbarDict['name'] = 'MESSAGE_BOX'
        toolbarDict['type'] = 'Checkbutton'
        toolbarDict['icon1'] = 'textBox.gif'
        toolbarDict['icon_dir'] = ICONPATH
        toolbarDict['balloonhelp'] = 'Message Box'
        toolbarDict['index'] = 2
        toolbarDict['variable'] = None
        toolbarDict['cmdcb'] = self.TB_cb
        self.toolbarList.append(toolbarDict)
        


    def configMenuEntry(self, menuButton, menuEntry, **kw):
        """Method to modify the Tkinter properties of a menu entry"""
        index = menuButton.menu.index(menuEntry)
        apply( menuButton.menu.entryconfig, (index,), kw )

        
    def message(self, str, NL=1):
        """ write into the message box """
        if thread.get_ident()==self.mainThread:
            if NL: str = str+'\n'
            self.MESSAGE_BOX.append(str)
        else:
            print str
    

    def addMenuBar(self, name, kw={}, kw2={}):
        """add a menu bar to a viewer"""
        # Description of the frame
        mbar = apply(Pmw.ScrolledFrame, (self.mBarFrame,), kw)
        self.mbar = mbar
    #mbar = apply( Tkinter.Frame, (self.mBarFrame,) , kw)
        apply( mbar.pack, (), kw2)
        # this line is needed, else root menu hase huge padding
        mbar.component('frame').pack()
        self.menuBars[name] = mbar
        mbar.menubuttons = {}
        mbar.checkbuttons = {}
        mbar.radiobuttons = {}
        mbar.buttons = {}
        return mbar


    def addMenuButton(self, mbar, name, kw={}, kw2={}):
        """add a pull down menu to a menu bar"""
        #create menu button
        kw['text'] = name
        #kw['font'] = (ensureFontCase('helvetica'), 14)
        import Pmw
        if isinstance(mbar, Pmw.ScrolledFrame):
            menuB = apply( Tkinter.Menubutton, (mbar.interior(),), kw )
        else:
            menuB = apply( Tkinter.Menubutton, (mbar,), kw )
        apply( menuB.pack, (), kw2)
        #create pull down
        menuB.menu = Tkinter.Menu(menuB)
        mbar.menubuttons[name] = menuB
        # attach pull down menu to button
        menuB['menu'] = menuB.menu
        return menuB

    
    def addMenuCommand(self, menu, name, cb, index, after, before, image,
                       kw={}):
        """
        add a command entry to a pull down menu

        menu is a Tk menu bar
        name is the string of the menu entry
        cb is  the callback to be called
        index is the rank in the menu
        after is a string of the menu entry after which to insert
        before is a string of the menu entry before which to insert
        image is a tring that point to a gif image
        
        index defaults to -1 which adds at the end. If an index != -1 is
        provided it will be used, else before i sused if specified, else
        after is used
        """
        assert callable(cb)
        kw['label'] = name
        kw['command'] = cb
        #print name
        if index is -1:
            #if after: print name, 'AFTER', after, index

            if after is not None:
                #try:
                index = menu.index(after)+1
                #except:
                #    pass
            #if after: print name, 'AFTER', after, index
            #if before: print name, 'BEFORE', before, index
            if before is not None:
                try:
                    index = menu.index(before)-1
                except:
                    pass
            #if before: print name, 'BEFORE', before, index
        if image is not None:
            import Image, ImageTk
            image = Image.open(image)
            image1 = ImageTk.PhotoImage(image, master=menu.master)
            kw['image'] = image1

        if index==-1:
            apply( menu.add_command, (), kw)
        else:
            apply( menu.insert_command, (index,), kw )


    def addCheckbutton(self, bar, name, cb, var, kw={}, kw2={}):
        """add a Checkbutton command to a menubar"""
        kw['text'] = name
        kw['command'] = cb
        kw['var'] = var
        if isinstance(bar, Pmw.ScrolledFrame):
            button = apply( Tkinter.Checkbutton, (bar.interior(),), kw)
        else:
            button = apply( Tkinter.Checkbutton, (bar,), kw)
        apply( button.pack, (), kw2)
        bar.checkbuttons[name] = button

        
    def addRadiobutton(self, bar, name, cb, var, kw={}, kw2={}):
        """add a Radiobutton command to a menubar"""
        kw['text'] = name
        kw['command'] = cb
        kw['var'] = var
        if isinstance(bar, Pmw.ScrolledFrame):
            button = apply( Tkinter.Radiobutton, (bar.interior(),), kw)
        else:
            button = apply( Tkinter.Radiobutton, (bar,), kw)
        apply( button.pack, (), kw2)
        bar.radiobuttons[name] = button
        
    def addButton(self, bar, name, cb,  kw={}, kw2={}):
        """add a Button command to a menubar"""
        kw['text'] = name
        kw['command'] = cb
        if isinstance(bar, Pmw.ScrolledFrame):
            button = apply( Tkinter.Button, (bar.interior(),), kw)
        else:
            button = apply( Tkinter.Button, (bar,), kw)
        apply( button.pack, (), kw2)
        bar.buttons[name] = button
    

    def addCommandToplevelGUI(self):
        """add a toplevel"""
        pass


    def addCommandMenuGUI(self, cmdGUI, cmdcb):
        """add the menus for a Command to the current set of menus"""
        assert isinstance(cmdGUI, CommandGUI)
        gui = cmdGUI.menu
        # get the menu bar, create it if necessary
        barname = gui[5]['menuBarName']
        if barname != None:
            if barname in self.menuBars.keys():
                bar = self.menuBars[gui[5]['menuBarName']]
            else:
                bar = self.addMenuBar(barname, gui[0], gui[1])
        else:
            bar = self.menuBars[self.menuBars.keys()[0]]
        cmdGUI.menuBar=bar
        
        # get the menuButton, create if if necessary
        menuname = gui[5]['menuButtonName']
        if menuname != None:
            if menuname in bar.menubuttons.keys():
                but = bar.menubuttons[gui[5]['menuButtonName']]
            else:
                but = self.addMenuButton(bar, menuname, gui[2], gui[3])
        else:
            but = bar.menubuttons[bar.buttons.keys()[0]]
        cmdGUI.menuButton=but

        # check wether this entry should go into a cascade
        cname = gui[5]['menuCascadeName']

        #if menuname=='File':
        #    print 'ADDING', gui[5]['menuEntryLabel'], cname, gui[5]['cascadeIndex']

        if cname is not None:
            index = gui[5]['cascadeIndex']
            before = gui[5]['cascadeBefore']
            after = gui[5]['cascadeAfter']
            if index is -1:
                if after is not None:
                    try:
                        index = but.menu.index(after)+1
                    except:
                        pass
                if before is not None:
                    try:
                        index = but.menu.index(before)-1
                    except:
                        pass

            if gui[5]['separatorAboveCascade']==1:
                #print '    separatore above cascade',
                but.menu.add_separator()

            if but.menu.children.has_key(cname):
                menu = but.menu.children[cname]
            else:
                menu = Tkinter.Menu(but.menu)
                #print 'ADDING cascade %s at %d'%(cname, index)
                if index==-1:
                    but.menu.add_cascade( label=cname, menu=menu )
                else:
                    but.menu.insert_cascade( index, label=cname, menu=menu )
                # save this entry in the children dict
                but.menu.children[cname] = menu

        else:
            menu = but.menu

        if gui[5]['separatorAbove']==1:
            menu.add_separator()

        if gui[5]['separatorBelow']==1: sepBelow=1
        else: sepBelow=0

        # find out the call back function we need to call
        cb = gui[5]['cb']
        if cb is None: cb = cmdcb

        if gui[5]['menuEntryType']=='command':
            self.addMenuCommand(
                menu, gui[5]['menuEntryLabel'], cb, gui[5]['index'],
                gui[5]['after'], gui[5]['before'], gui[5]['image'], gui[4] )

        elif gui[5]['menuEntryType']=='checkbutton':
            cmdGUI.menuCheckbuttonVar = Tkinter.IntVar()
            cmdGUI.menuCheckbuttonVar.set(0)
            gui[4]['label'] = gui[5]['menuEntryLabel']
            gui[4]['command'] = cb
            gui[4]['variable'] = cmdGUI.menuCheckbuttonVar
            index = gui[5]['index']
            if index == -1:
                menu.add_checkbutton(gui[4])
            else:
                menu.insert(index, 'checkbutton', gui[4])

        if sepBelow: menu.add_separator()

        if gui[5]['separatorBelowCascade']==1:
            but.menu.add_separator()



    def addCheckbuttonMenuGUI(self, cmdGUI, cmdcb=None):
        """add the menus for a Command to the current set of menus"""
        assert isinstance(cmdGUI, CommandGUI)
        gui = cmdGUI.checkbutton
        cmdGUI.checkbuttonVar = Tkinter.IntVar()
        cmdGUI.checkbuttonVar.set(0)
        
        # get the menu bar, create it if necessary
        barname = gui[4]['barName']
        if barname != None:
            if barname in self.menuBars.keys():
                bar = self.menuBars[gui[4]['barName']]
            else:
                bar = self.addMenuBar(barname, gui[0], gui[1])
        else:
            bar = self.menuBars[self.menuBars.keys()[0]]
        cmdGUI.menuBar=bar

        # find out the call back function we need to call
        cb = gui[4]['cb']
        if cb is None: cb = cmdcb

        # add the button
        name = gui[4]['buttonName']
        self.addCheckbutton( bar, name, cb,
                             cmdGUI.checkbuttonVar, gui[2], gui[3])


    def addRadiobuttonMenuGUI(self, cmdGUI, cmdcb=None):
        """add the menus for a Radiobutton to the current set of menus"""
        assert isinstance(cmdGUI, CommandGUI)
        gui = cmdGUI.radiobutton
        cmdGUI.radiobuttonVar = Tkinter.IntVar()
        cmdGUI.radiobuttonVar.set(0)
        
        # get the menu bar, create it if necessary
        barname = gui[4]['barName']
        if barname != None:
            if barname in self.menuBars.keys():
                bar = self.menuBars[gui[4]['barName']]
            else:
                bar = self.addMenuBar(barname, gui[0], gui[1])
        else:
            bar = self.menuBars[self.menuBars.keys()[0]]
        cmdGUI.menuBar=bar

        # find out the call back function we need to call
        cb = gui[4]['cb']
        if cb is None: cb = cmdcb

        # add the button
        name = gui[4]['buttonName']
        self.addRadiobutton( bar, name, cb,
                             cmdGUI.radiobuttonVar, gui[2], gui[3])


    def addButtonMenuGUI(self, cmdGUI, cmdcb=None):
        """add the menus for a Button to the current set of menus"""
        assert isinstance(cmdGUI, CommandGUI)
        gui = cmdGUI.button
        
        # get the menu bar, create it if necessary
        barname = gui[4]['barName']
        if barname != None:
            if barname in self.menuBars.keys():
                bar = self.menuBars[gui[4]['barName']]
            else:
                bar = self.addMenuBar(barname, gui[0], gui[1])
        else:
            bar = self.menuBars[self.menuBars.keys()[0]]
        cmdGUI.menuBar=bar

        # find out the call back function we need to call
        cb = gui[4]['cb']
        if cb is None: cb = cmdcb

        # add the button
        name = gui[4]['buttonName']
        self.addButton( bar, name, cb, gui[2], gui[3])

    
    def setObjLabel(self, event):
        self.objLab.configure(text="current molecule:" + self.current.name)


    def askFileOpen(self, master, idir = None, ifile=None, types=None,
                    title='open', multiple=False):
        file = fileOpenAsk(master, idir, ifile, types,title, multiple)
        return file
        
    def askFileSave(self, master, idir=None, ifile=None, types = None,
                    title='Save'):
        file  = fileSaveAsk(master, idir, ifile, types, title)
        return file

    def addtoolbarDictGUI(self,cmdGUI, cmdcb=None):
        cmdGUI.toolbarDict['cmdcb'] = cmdcb
        self.toolbarList.append(cmdGUI.toolbarDict)
        self.configureToolBar(resizeGUI=False)
        
    def configureToolBar(self, iconsize='medium', resizeGUI = True):
        """
        Adds a tool bar
Optional iconsize parameter can be passed that currently is 
either small (22x22) or large (32x32)
        """
        
        from mglutil.gui.BasicWidgets.Tk.toolbarbutton import ToolBarButton
        if self.menuBars.has_key('Toolbar'):
            self.menuBars['Toolbar']._frame.toolbarButtonDict = {}
            slaves = self.menuBars['Toolbar']._frame.slaves()
            self.menuBars['Toolbar']._frame.spare = []
            for slave in slaves:
                if isinstance( slave, (ToolBarButton,Tkinter.Checkbutton) ):
                    slave.destroy()
                else:
                    self.menuBars['Toolbar']._frame.spare.append(slave)
                    slave.pack_forget()
        else:
            self.addMenuBar(
                        'Toolbar',
                        {'borderframe':0, 'horizscrollbar_width':7,
                         'vscrollmode':'none', 'frame_relief':'groove',
                         'vertflex':'shrink',
                         'frame_borderwidth':1,},
                        {'side':'top', 'expand':1, 'fill':'x'})

        self.iconsize = iconsize
        iconsizedir = ICONSIZES[iconsize]
        h_w = int(iconsizedir[:2])
        
        decorated = [(dict_['index'], dict_) for dict_ in self.toolbarList 
            if dict_['type']=='Checkbutton' or dict_['type']=='MenuRadiobutton']
        decorated.sort()
        Sorted_Checkbuttons = [dict_ for (key, dict_) in decorated]
        decorated = [(dict_['index'], dict_) for dict_ in self.toolbarList 
                     if dict_['type']=='ToolBarButton']
        decorated.sort()
        Sorted_ToolBarButtons = [dict_ for (key, dict_) in decorated]
                
        for item in Sorted_ToolBarButtons:            
            ToolBarButton(None, 
              self.menuBars['Toolbar']._frame, name = item['name'], 
              icon1 = item['icon1'], state = item['state'],
              icon2 = item['icon2'],
              height = h_w, width = h_w, command = item['cmdcb'],
              padx=2, pady=2,
              balloonhelp=item['balloonhelp'],
              iconpath=item['icon_dir'] + os.sep + iconsizedir)

        tmp_txt = 'sep.gif'
        ToolBarButton(None, self.menuBars['Toolbar']._frame, name = 'sep1', 
                      icon1 = tmp_txt, state = 'disabled', 
                      pady=2,                      
                      height=h_w, width=5,
                      iconpath=ICONPATH + os.sep + iconsizedir)

        bar = self.menuBars['Toolbar']
        self.toolbarCheckbuttons = {}
        for item in Sorted_Checkbuttons:
            tmpDict = {}
            try:
                item['icon_dir'] + os.sep + iconsizedir
            except:
                import pdb
                pdb.set_trace()
            iconfile = os.path.join(item['icon_dir'] + os.sep + iconsizedir,item['icon1'])
            head, ext = os.path.splitext(iconfile)
            if ext == '.gif':
                Icon = Tkinter.PhotoImage(file=iconfile, master=self.ROOT)
            else:
                image = Image.open(iconfile)
                Icon = ImageTk.PhotoImage(image=image, master=self.ROOT)
            tmpDict['Icon'] = Icon
            if item['type'] == 'Checkbutton':
                if item['variable']:
                    Variable = item['variable']
                else:
                    Variable = Tkinter.IntVar()
                tmpDict['Variable'] = Variable
                Checkbutton = Tkinter.Checkbutton(bar.interior(),
                                           image=Icon,
                                           indicatoron=0,
                                           variable=Variable,
                                           command=item['cmdcb'],
                                           )
            elif item['type'] == 'MenuRadiobutton':
                if item['variable']:
                    Variable = item['variable']
                else:
                    Variable = Tkinter.StringVar()
                tmpDict['Variable'] = Variable
                Checkbutton = Tkinter.Menubutton(
                                           bar.interior(),
                                           image=Icon,
                                           indicatoron=0,
                                           #relief='raised'
                                           )
                self.radioMenu = Tkinter.Menu(Checkbutton, tearoff=0)
                for i in range( len(item['radioLabels'])):
                    self.radioMenu.add_radiobutton(
                                          label=item['radioLabels'][i], 
                                          value=item['radioValues'][i],
                                          variable=Variable,
                                          command=item['cmdcb']
                                          )
                Variable.set(item['radioInitialValue'])
                Checkbutton['menu']= self.radioMenu

            Checkbutton.pack(side='left') 
            Checkbutton.ballon = Pmw.Balloon(self.ROOT)
            Checkbutton.ballon.bind(Checkbutton,item['balloonhelp'] )
            tmpDict['Checkbutton'] = Checkbutton
            self.toolbarCheckbuttons[item['name']] = tmpDict

        tmp_txt = 'sep.gif'                
        ToolBarButton(None, self.menuBars['Toolbar']._frame, name = 'sep2', 
                      icon1 = tmp_txt, state = 'disabled', 
                      padx=1, pady=2, 
                      height=h_w, width=5, iconpath=ICONPATH + os.sep + iconsizedir)
#        if hasattr(self.menuBars['Toolbar']._frame,'spare'):
#            for repack in self.menuBars['Toolbar']._frame.spare:
#                repack.pack(side='left')
        self.menuBars['Toolbar']._frame.pack()
        if resizeGUI:            
            top = self.ROOT.winfo_toplevel()
            geom = top.geometry()
            geom = geom.split('x')
            self.menuBars['Toolbar']._frame.update()
            winfo_width = self.menuBars['Toolbar']._frame.winfo_width()        
            if int(geom[0]) < winfo_width + 10:
                geom[0] = str(winfo_width + 10)
            top.geometry(geom[0]+'x'+geom[1])

            
def fileOpenAsk(master, idir=None, ifile=None, types=None,
                title='Open', multiple=False):
    if types is None: types = [ ('All files', '*') ]
    if multiple:
        result = tkFileDialog.askopenfilenames(
            parent = master, filetypes=types, initialdir=idir,
            initialfile=ifile, title=title)
        return result
    else: 
        result = tkFileDialog.askopenfilename(
            parent = master, filetypes=types, initialdir=idir,
            initialfile=ifile, title=title)
        if isinstance(result, tuple): # "Cancel" was pressed
            return None
        else:
            return result


def fileSaveAsk(master, idir=None, ifile=None, types = None,
                title='Save'):
    if types is None: types = [ ('All files', '*') ]
    file = tkFileDialog.asksaveasfilename( parent = master,
                                           filetypes=types,
                                           initialdir=idir,
                                           initialfile=ifile,
                                           title=title)
    if file=='': file = None
    return file

def dirChoose(master, idir=None, title='Choose Directory'):
    from mglutil.gui.BasicWidgets.Tk.dirDialog import askdirectory
    dirpath = askdirectory( initialdir=idir,title=title)
    if dirpath=='': dirpath = None
    return dirpath
        
def dirCreate(master, idir=None, title='Create Directory'):
    from mglutil.gui.BasicWidgets.Tk.dirDialog import createdirectory
    dirpath = createdirectory( initialdir=idir,title=title)
    if dirpath=='': dirpath = None
    return dirpath
        
if __name__=="__main__":
    pass
