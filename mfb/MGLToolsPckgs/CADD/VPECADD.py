#########################################################################
#########################################################################
# $Header: /opt/cvs/CADD/VPECADD.py,v 1.6 2011/05/20 00:10:08 nadya Exp $
# $Id: VPECADD.py,v 1.6 2011/05/20 00:10:08 nadya Exp $


import re
import sys
import os
import string
import Pmw, Tkinter
import webbrowser
import warnings
import types

from NetworkEditor.simpleNE import NetworkBuilder, NoGuiNetworkBuilder 
from mglutil.util.callback import CallBackFunction
from mglutil.gui.BasicWidgets.Tk.toolbarbutton import ToolBarButton

from mglutil.gui.BasicWidgets.Tk.customizedWidgets import kbComboBox
from Vision.VPE import NoGuiVPE, VisualProgramingEnvironment
from CADD.FormsCADD import AboutWF, AboutDialogCADD, AcknowlDialogCADD, ChangeFontsCADD, BugReportCADD, RefDialogCADD
from CADD import WFTypes
from WFType import NodeWFType

class CADDToolBarButton(ToolBarButton):
    def __init__(self, balloonmaster=None, master=None, name=None, icon1=None,
                 icon2=None, command=None, balloonhelp='',
                 statushelp='', height=20, width=21,
                 bd=1, activebackground='lightgrey', padx=0, pady=0,
                 state='normal', bg=None, iconpath=None):

        ToolBarButton.__init__(self, balloonmaster=balloonmaster, master=master, name=name, icon1=icon1,
                               icon2=icon2, command=command, balloonhelp=balloonhelp,
                               statushelp=statushelp, height=height, width=width,
                               bd=bd, activebackground=activebackground, padx=padx, pady=pady,
                               state=state, bg=bg, iconpath=iconpath
                              )

    def recolorButton(self, bg):
        self.bg = bg

class CADDCheckbutton (Tkinter.Checkbutton):

    def __init__(self, master=None, image=None, indicatoron=0,
                 variable=None, command=None, selectcolor=None, bg=None):
        Tkinter.Checkbutton.__init__(self, master=master,image=image, indicatoron=indicatoron,
                            variable=variable, command=command, selectcolor=selectcolor, bg=bg)

    def recolorButton(self, bg):
        self.bg = bg

class CADDMenubutton(Tkinter.Menubutton):

    def __init__(self, master=None, text='', image=None):
        Tkinter.Menubutton.__init__(self, master=master, text = text, image=image)

    def recolorButton(self, bg):
        self.bg = bg


class NoGuiVPECADD(NoGuiVPE):
    def __init__(self):
        self.libraries = {}         # stores node libraries

        try:
            # add VisionLibraries to system path
            from Vision.UserLibBuild import addDirToSysPath
            from Vision import __path__
            addDirToSysPath(__path__[0]+'Libraries')
            
            # add UserLibs to system path 
            from mglutil.util.packageFilePath import getResourceFolderWithVersion
            lCADDResourceFolder = getResourceFolderWithVersion() \
                                    + os.sep + 'CADD' + os.sep
            addDirToSysPath(lCADDResourceFolder + 'UserLibs')
        except:
            pass


class NoGuiExecCADD(NoGuiNetworkBuilder, NoGuiVPECADD):

    def __init__(self):
        NoGuiNetworkBuilder.__init__(self)
        NoGuiVPECADD.__init__(self)
        
   
class VisualProgramingEnvironmentCADD(VisualProgramingEnvironment, NoGuiVPECADD):

    def __init__(self, name='CADD', master=None, font=None,
                 withShell=1, width=750, height=700, **kw):
        NoGuiVPECADD.__init__(self)
        
        self.width = width
        self.height = height
        self.master = master

        from CADD.UserLibBuildCADD import ensureDefaultUserLibFileCADD, ensureCADDResourceFile, ensureCADDFontsFile
        ensureDefaultUserLibFileCADD()
        caddRCFile = ensureCADDResourceFile()
        ensureCADDFontsFile()

        # set workflows dir and copy workflows from the installed distro
        self.setWFDir(caddRCFile)
        self.copyWorkflows()

        self.top = Pmw.PanedWidget(master, orient='vertical', 
                                   hull_relief='sunken',
                                   hull_width=width, hull_height=height)
        self.top.component('hull').master.title(name)

        wfmenus = self.top.add('WFMenuBars', min=20, max=40,size=20)

        menus = self.top.add('MenuBars', min=20, max=40, size=20)
        if sys.platform == 'win32':
            modulePagesPane = self.top.add('ModulePages', min=150, size=200)
        else: 
            modulePagesPane = self.top.add('ModulePages', min=100, size=200)

        # horizontal pane for for buttons
        self.buttonBar = self.top.add('ButtonBar', min=20, max=20, size=20)
        self.buttonBarFunc = {} # key:buttonName, value:function
   
        # horizontal pane for networks notebook
        ed = self.top.add('Editor', min=100)

        # create scrolled frame for ModulePage (libraries)
        self.modulePagesF = Pmw.ScrolledFrame(modulePagesPane,
             borderframe=1, horizscrollbar_width=7, vscrollmode='none',
             frame_relief='flat',
             frame_borderwidth=0, horizflex='fixed',
             vertflex='elastic')
        self.modulePagesF.pack(expand=1, fill='both')
        self.ModulePages = Pmw.NoteBook(self.modulePagesF.interior(), raisecommand=self.selectLibrary)
        self.ModulePages.pack(fill='both', expand = 1)# padx = 5, pady = 5) 

        self.idToNodes = {} # key is canvas, values {nodeID:nodeType}

        self.setColors()  # definte clors before toolbar buttons are creaed
        self.addButtonsToButtonBar(master) # add buttons to buttonBar
        
        self.modSearch = kbComboBox( self.buttonBar, labelpos='w',
            entryfield_entry_width=12, selectioncommand=self.searchModules,
            scrolledlist_items = [])
        self.modSearch.pack(side='left', anchor=Tkinter.NW)
           
        self.lastSearchString = None
        self.searchAfterId = None # used to deselect nodes found by search
        self.lastMatchIndices = [0,0,0] # library index and category index of last found node

        apply( NetworkBuilder.__init__, (self, name, ed, font, withShell), kw )
        self.mBar.destroy()

        self.createMenus(menus)
        self.setFont("Menus", self.font['Menus'])
        
        self.top.pack(expand=1, fill='both')

        handle = self.eventHandler['deleteNetwork']
        handle.AddCallback(self.handleDeleteNetworkButtons)

        self.setForms()

        from NetworkEditor.widgets import widgetsTable
        self.widgetsTable = widgetsTable

        self.userLibsDirs = {}      # stores path to user defined node libs 

        from Vision.UserLibBuild import ensureDefaultUserLibFile
        ensureDefaultUserLibFile()
        from Vision.UserLibBuild import ensureVisionResourceFile
        ensureVisionResourceFile()

        if hasattr(self,"currentNetwork"):
            self.currentNetwork.glyphKeywords ={}
            self.currentNetwork.glyphKeywords['fontstyle']=''
            self.currentNetwork.glyphKeywords['font']= "courier"
            self.currentNetwork.glyphKeywords['fontsize'] = 12 
            self.currentNetwork.glyphKeywords['fill'] = ''
            self.currentNetwork.glyphKeywords['outline'] = "black"
            self.currentNetwork.glyphKeywords['spray'] = False

        self.master.master.master.protocol("WM_DELETE_WINDOW", self.interactiveExit_cb)
        self.changeColor()

    def setWFDir(self, file):
        import user
        lines = open(file).read().splitlines()
        for line in lines: 
            if "workflowDir" in line : 
                dir, val = line.split('=')
		self.workflowDir = eval(val)

    def copytree(self, source, target, ignore_patterns):
        # recursive copy. WIll not be needed as of python 2.7.
        from os.path import join, splitext, split, exists
        from shutil import copyfile

        if not os.path.exists(target):
            os.mkdir(target)
        for root, dirs, files in os.walk(source):
            for pat in ignore_patterns:
                if pat in dirs:
                    dirs.remove(pat)  # don't visit ignored directories           
            for file in files:
                if splitext(file)[-1] in ('.pyc', '.pyo', '.fs'):
                    continue
                from_ = join(root, file)           
                to_ = from_.replace(source, target, 1)
                to_directory = split(to_)[0]
                if not exists(to_directory):
                    os.makedirs(to_directory)
                copyfile(from_, to_)

    def copyWorkflows(self):
        # copy workflows from the distribution to user's home
        from CADD import __path__  
        self.__path__ = __path__[0]
        print "PATH", self.__path__

        if os.path.exists(self.workflowDir):
            print "Using existing workflows from %s" % self.workflowDir
        else:
            print "Copying distribution workflows to %s" % self.workflowDir
            wfDistroDir = os.path.join( self.__path__, 'workflows')
            print "CADD PATH", wfDistroDir, self.workflowDir
            try:
                self.copytree(wfDistroDir, self.workflowDir, ('.svn', 'CVS') )
                # use next lines for python 2.7+
                #from shutil import copytree, ignore_patterns
                #copytree(wfDistroDir, self.workflowDir, ignore = ignore_patterns('.svn', 'CVS') )
            except:
                txt = "Can not copy distribution workflows into directory %s" % self.workflowDir
                warnings.warn(txt)

    def setColors(self):
        # Create the list of colors to cycle through
        self.colorList = []
        self.colorIndex = 0
        self.colorList.append(('ivory', '#000022'))

        #for color in Pmw.Color.spectrum(6, 1.5, 1.0, 1.0, 1):
        for color in Pmw.Color.spectrum(6, 1.0, 1.0, 1.0, 1, 0):
            bg = Pmw.Color.changebrightness(self.master.master, color, 0.85)
            self.colorList.append((bg, 'black'))
            bg = Pmw.Color.changebrightness(self.master.master, color, 0.65)
            self.colorList.append((bg, 'black'))

            #bg = Pmw.Color.changebrightness(self.master.master, color, 0.45)
            #self.colorList.append((bg, 'white'))
            #bg = Pmw.Color.changebrightness(self.master.master, color, 0.25)
            #self.colorList.append((bg, 'white'))

        self.bg, self.fg = self.colorList[self.colorIndex]
        self.colorIndex = -1


    def changeColor(self):
        self.colorIndex = self.colorIndex + 1
        if self.colorIndex == len(self.colorList):
            self.colorIndex = 0

        self.bg, self.fg = self.colorList[self.colorIndex]
        Pmw.Color.changecolor(self.master.master, self.bg, foreground = self.fg)
        Pmw.Color.changecolor(self.buttonBar, self.bg, foreground = self.fg)
        self.ModulePages.recolorborders()

        bl = self.buttonBar.toolbarButtonDict
        for buttonName, button in bl.items():
                button.config(bg=self.bg, activebackground=self.bg)
                button.recolorButton(self.bg)


    def setForms(self):
        # a dictionary holding various forms:
        self.forms = {}              
        self.forms['configureFontsPanel'] = None # a form to change the fonts
        self.forms['loadLibraryPanel']    = None # a widget created by showLoadLibraryForm_cb 
        self.forms['browseLibsPanel']     = None # a widget created by showBrowseLibraryForm_cb
        self.forms['createLibsPanel']     = None # a widget created by showCreateLibraryForm_cb
        self.forms['addNodeToLibsPanel']  = None # a widget created by AddNodeToLibrary_cb
        self.forms['aboutDialog']         = None # aboutDialog window
        self.forms['acknowlDialog']       = None # acknowledgements dialog
        self.forms['refDialog']           = None # references dialog window
        self.forms['searchNodesDialog']   = None # search nodes dialog window
        self.forms['BugReport']           = None # bugreport window


    def createMenus(self, parent):
        NetworkBuilder.createMenus(self, parent)
        self.makeLibrariesMenu()
        self.makeHelpMenu()
        self.addToEditMenu()

        self.hideLibsPane()
        wfmenus = self.top.pane('WFMenuBars')
        self.createWFMenu(wfmenus)
        self.colorButton()


    def createWFMenu(self, parent):
        self.WFmBar = Tkinter.Frame(parent, relief=Tkinter.RAISED, borderwidth=2) 
        self.WFmBar.pack(side='top',fill=Tkinter.X)

        self.WFTypeButtons = {}
        self.WFMenus = {}
        entries = WFTypes.keys()
        entries.sort()
        for item in entries:
           self.makeWFTypes(item)

        apply( self.WFmBar.tk_menuBar, self.WFTypeButtons.values() )


    def colorButton(self):
        #buttonbox = Pmw.ButtonBox(self.WFmBar)
        #buttonbox.pack(side = Tkinter.TOP, fill = 'none', padx='0m', pady='0m', expand=1)
        #buttonbox.add('Change color', command = self.changeColor)
        cbutton = Tkinter.Button(self.WFmBar, text="Change color", command = self.changeColor)
        cbutton.pack(side=Tkinter.RIGHT)


    def makeWFTypes(self, str):
        wfType = NodeWFType(str, dir=self.workflowDir)
        assert isinstance(wfType, NodeWFType)

        self.font['SubMenus'] = ('helvetica', 12, 'bold')

        WFType_button = Tkinter.Menubutton(self.WFmBar, text=str,
                                           relief=Tkinter.FLAT,
                                           underline = None
                                          )

        self.WFTypeButtons[str] = WFType_button
        self.WFMenus[str] = wfType.showWFlist()

        WFType_button.pack(side=Tkinter.LEFT, padx="0m")
        WFType_button.configure(font=self.font['SubMenus'])

        WFType_button.menu = Tkinter.Menu(WFType_button, tearoff=False)
        WFType_button.menu.add_separator()
        key = "About %s" % str
        WFType_button.menu.add_command(label=key, command=(lambda:self.showAboutWF(key, wfType.showType())))

        wflist = Tkinter.Menu(WFType_button.menu, tearoff=0)
        wflist.configure(font=self.font['SubMenus'])

        WFType_button.menu.add_cascade(label="Load workflow", menu=wflist)

        for item in self.WFMenus[str]:
            label = item[0]
            file = item[1]
            wflist.add_command(label=label, command=(lambda file=file : self.directLoadNetwork_cb(file)))

        WFType_button.menu.add_separator()
        WFType_button['menu'] = WFType_button.menu

    def showConfigureFontsForm_cb(self, event=None):
        if self.forms['configureFontsPanel'] is None:
           self.forms['configureFontsPanel'] = ChangeFontsCADD(editor=self)
        else:
            self.forms['configureFontsPanel'].show()


    def directLoadNetwork_cb(self, file): 
        if file:
            self.loadNetwork(file, network=None)
            self.recentFiles.add(file, 'loadNetwork')


    def hideLibsPane(self):
        menu = self.menuButtons['Libraries'].menu
        self.modulePagesF.forget()
        menu.entryconfigure('Hide libraries', label='Show libraries')
        self.top.configurepane('ModulePages', min=0, max=0)


    def updateFastLibs(self):
        from CADD.nodeLibrariesCADD import libraries
        for key, value in libraries.items():
            try:
                if hasattr(self,'fastLibsMenu'):
                    self.fastLibsMenu.index(key)
            except:
                if len(value) == 2:
                    func = CallBackFunction(self.loadLibModule, value[0], dependents=value[1])
                else:
                    func = CallBackFunction(self.loadLibModule, value)
                if hasattr(self,'fastLibsMenu'):
                    self.fastLibsMenu.add_command(label=key, command=func)

            try:
                if hasattr(self,'fastLibsMenu2'):
                    self.fastLibsMenu2.index(key)
            except:
                if len(value) == 2:
                    func = CallBackFunction(self.loadLibModule, value[0], dependents=value[1])
                else:
                    func = CallBackFunction(self.loadLibModule, value)
                if hasattr(self,'fastLibsMenu2'):
                    self.fastLibsMenu2.add_command(label=key, command=func)


    def showBugReport(self, event=None):
        """the 'about CADD' dialog window"""
        if self.forms['BugReport'] is None:
            self.forms['BugReport'] = BugReportCADD()
        else:
            self.forms['BugReport'].show()

    def showAboutWF(self, key, about, event=None):
        """the 'about workflow type' dialog window"""
        if not self.forms.has_key(key) :
            self.forms[key] = None

        if self.forms[key] is None:
            self.forms[key] = AboutWF(key, about, self.bg, self.fg)
        else:
            self.forms[key].setDialogColor(self.bg, self.fg)
            self.forms[key].show()

    def showAbout(self, event=None):
        """the 'about CADD' dialog window"""
        if self.forms['aboutDialog'] is None:
            self.forms['aboutDialog'] = AboutDialogCADD(bg = self.bg, fg = self.fg)
        else:
            self.forms['aboutDialog'].setDialogColor(self.bg, self.fg)
            self.forms['aboutDialog'].show()

    def showAcknowl(self, event=None):
        """the 'acknowledgements' dialog window"""
        if self.forms['acknowlDialog'] is None:
            self.forms['acknowlDialog'] = AcknowlDialogCADD(bg = self.bg, fg = self.fg)
        else:
            self.forms['acknowlDialog'].setDialogColor(self.bg, self.fg)
            self.forms['acknowlDialog'].show()


    def showTutorials(self):
        import tkMessageBox
        tkMessageBox.showinfo("Tutorials and examples",
"""Tutorials and examples must be downloaded separately from the section "Supplementary Material" at http://mgltools.scripps.edu/downloads

In the archive file, you will find a beginner's tutorial: doc/Tutorial/tutorial.rtf

and Jose Unpingco has prepared some nice video tutorials http://www.osc.edu/blogs/index.php/sip
""")


    def showRefs(self, event=None):
        """the 'references' dialog window"""
        if self.forms['refDialog'] is None:
            self.forms['refDialog'] = RefDialogCADD(bg = self.bg, fg = self.fg)
        else:
            self.forms['refDialog'].setDialogColor(self.bg, self.fg)
            self.forms['refDialog'].show()


    def showFAQ(self, event=None):
        from mglutil.util.packageFilePath import findFilePath
        file = findFilePath('FAQ.html', 'CADD')
        if file:
            webbrowser.open(file)

        
    def runWithoutGui_cb(self, event=None):
        """VPE wrapper of runWithoutGui_cb. toggle button bar buttons
"""
        if self.currentNetwork is None \
          or len(self.currentNetwork.nodes) == 0:
            warnings.warn('no Network to run without GUI')
            return
        else:
            print "running current network without GUI"

        bl = self.buttonBar.toolbarButtonDict
        bl['runWithoutGui'].disable()        
        bl['stopWithoutGui'].enable()
        net = self.currentNetwork
        net.canvas.update_idletasks()

        # save the temporary file to be run
        if self.currentNetwork.filename is not None:
            lNetworkDir = os.path.dirname(self.currentNetwork.filename)
        else:
            import CADD
            lNetworkDir = CADD.networkDefaultDirectory

        try:
            self.removeTemporaryNetworkFile()
            from tempfile import mktemp
            self.temporaryFilename = mktemp(dir=lNetworkDir)
            self.saveNetwork(self.temporaryFilename, temporary=True)

            self.killRunWithoutGui()

            from subprocess import Popen, PIPE, call, check_call
            if sys.platform == 'win32':
                net.processWithoutGui = Popen(
                    ['python',
                     self.temporaryFilename,'-w'],
                     shell=False, cwd=lNetworkDir)
            else:
                net.processWithoutGui = Popen(
                    [self.resourceFolder+'/pythonsh',
                     self.temporaryFilename,'-w'],
                     shell=False, cwd=lNetworkDir)

            
            ## bind widget in setwork to remote process
            for node in self.currentNetwork.nodes:
                for p in node.inputPorts:
                    if p.widget:
                        p.widget.bindToRemoteProcessNode()

            def verifyProcessWithoutGui():
                net = self.currentNetwork
                #print verifyProcessWithoutGui, net.processWithoutGui.poll()
                if hasattr(net, 'processWithoutGui') \
                  and net.processWithoutGui.poll() != 0:
                    self.after(1000, verifyProcessWithoutGui)
                else:
                    self.stopWithoutGui_cb()

            self.after(1000, verifyProcessWithoutGui)

            # wait for process to start and write self.temporaryFilename.sock
            from os import path
            from time import sleep
            while 1:
                if path.exists(self.temporaryFilename+'.sock'):
                    break
                else:
                    sleep(0.1)

            f = open(self.temporaryFilename+'.sock')
            host, port = f.readlines()[0].split()
            f.close()

            net = self.currentNetwork
            net.remoteProcessSocket = self.currentNetwork.connectToProcess(
                host, int(port))
            
        except Exception, e:
            warnings.warn("""can't save or run temporary file to run without GUI,
on unix make sure ksh is installed as /bin/ksh""")
            print e

    def addButtonsToButtonBar(self, master):
        # balloons were moved from the cursor to fix a problem with
        # node library balloons flashing 

        buttonList = [
            {'sep1':{'icon1':'sep.gif', 'icon2':None, 'state':'disabled',
                   'func':None, 'balloon':None}},

            {'new':{'icon1':'new.gif', 'icon2':None, 'state':'normal',
                   'func':self.newNet_cb, 'balloon':'new network'}},
            {'open':{'icon1':'open.gif', 'icon2':'lib-close.gif', 'state':'normal',
                   'func':self.loadNetwork_cb, 'balloon':'open network'}},
            {'merge':{'icon1':'merge1.gif', 'icon2':'merge2.gif',
                      'state':'disabled',
                   'func':self.mergeNetwork_cb, 'balloon':'merge networks'}},
            {'loadLib':{'type':'menubutton',
                        'icon1':'loadLib2.gif',
                        'func':self.showLoadLibraryForm2_cb,
                        'balloon':'load library'}},
            {'showHideLib':{'state':'normal',
                        'icon1':'lib-open.gif',
                        'icon2':'lib-close.gif',
                        'func':self.showHideLibraries_cb,
                        'balloon':'show/hide library'}},

            {'save':{'icon1':'save1.gif', 'icon2':'save2.gif',
                    'state':'disabled', 'func':self.saveNetwork_cb,
                    'balloon':'save network'}},
            {'print':{'icon1':'print1.gif', 'icon2':'print2.gif',
                    'state':'disabled', 'func':self.print_cb,
                    'balloon':'print network'}},

            {'sep3':{'icon1':'sep.gif', 'icon2':None, 'state':'disabled',
                   'func':None, 'balloon':None}},

            {'runOnNewData':{'type':'checkbutton',
                             'icon1':'tapclosed.gif',
                             'icon2':'tapopen.gif',
                             'func':self.setRunOnNewData_cb,
                             'balloon':'toggle immediate run'}},

            {'softrun':{'icon1':'run1.gif', 'icon2':'runGreen.gif',
                    'state':'disabled', 'func':self.softrunCurrentNet_cb,
                    'balloon':'soft run current network'}},

            {'run':{'icon1':'run1.gif', 'icon2':'run2.gif',
                    'state':'disabled', 'func':self.runCurrentNet_cb,
                    'balloon':'hard run current network (force run)'}},
        
            {'pause':{'icon1':'pause1.gif', 'icon2':'pause2.gif',
                    'state':'disabled', 'func':self.togglePauseCurrentNet_cb,
                    'balloon':"pause current network's execution"}},
            
            {'stop':{'icon1':'stop1.gif', 'icon2':'stop2.gif',
                    'state':'disabled', 'func':self.stopCurrentNet_cb,
                    'balloon':"stop current network's execution"}},

            {'sep4':{'icon1':'sep.gif', 'icon2':None, 'state':'disabled',
                   'func':None, 'balloon':None}},

            {'runWithoutGui':{'icon1':'run1.gif', 'icon2':'runBlack.gif',
                    'state':'disabled', 'func':self.runWithoutGui_cb,
                    'balloon':'run current network without GUI in a separate process'}},

            {'stopWithoutGui':{'icon1':'stop1.gif', 'icon2':'stop2.gif',
                    'state':'disabled', 'func':self.stopWithoutGui_cb,
                    'balloon':"stop execution without GUI"}},

            {'sep5':{'icon1':'sep.gif', 'icon2':None, 'state':'disabled',
                   'func':None, 'balloon':None}},

            {'gantt':{'icon1':'teprla1.gif', 'icon2':'teprla1.gif',
                    'state':'enabled', 'func':self.toggleGantt_cb,
                    'balloon':"show/hide GANTT diagram of execution times"}},

            {'debug':{'icon1':'flowengine_6.gif', 'icon2':'flowengine_6.gif',
                    'state':'enabled', 'func':self.debugCurrentNet_cb,
                    'balloon':"build the list of node to execute and step through them"}},

            {'step':{'icon1':'stepover_6.gif', 'icon2':'stepover_6.gif',
                    'state':'disabled', 'func':self.debugStep_cb,
                    'balloon':"Execute current node in node list"}},

            {'sep5a':{'icon1':'sep.gif', 'icon2':None, 'state':'disabled',
                   'func':None, 'balloon':None}},

            {'cut':{'icon1':'cut1.gif', 'icon2':'cut2.gif',
                    'state':'disabled', 'func':self.cutNetwork_cb,
                    'balloon':'cut'}},
            {'copy':{'icon1':'copy1.gif', 'icon2':'copy2.gif',
                    'state':'disabled', 'func':self.copyNetwork_cb,
                    'balloon':'copy'}},
            {'paste':{'icon1':'paste1.gif', 'icon2':'paste2.gif',
                    'state':'disabled', 'func':self.pasteNetwork_cb,
                    'balloon':'paste'}},

            {'sep6':{'icon1':'sep.gif', 'icon2':None, 'state':'disabled',
                   'func':None, 'balloon':None}},

            {'find':{'icon1':'find2.gif', 'icon2':'find2.gif',
                    'state':'enabled', 'func':self.searchNodes_cb,
                    'balloon':'open search nodes panel'}},
           ]

        from mglutil.util.packageFilePath import findFilePath
        ICONPATH = findFilePath('Icons', 'CADD')

        self.buttonIcons = {} #otherwise the icon is lost and not displayed (tk bug)
        for item in buttonList:
            name=item.keys()[0]
            icon1 = item[name]['icon1']
            func  = item[name]['func']
            balloon = item[name]['balloon']
            self.buttonBarFunc[name] = func
            if item[name].has_key('type') is False:
                icon2 = item[name]['icon2']
                state = item[name]['state']
                # Note: we pass balloonmaster=None to class ToolBarButton
                # so it will create an attribute 'balloons' in self.buttonBar
                # so Pmw.Balloon will be an instance in self.buttonBar.balloons
                CADDToolBarButton(None, self.buttonBar, name=name, icon1=icon1,
                          icon2=icon2, state=state,
                          command=self.selectFunc, balloonhelp=balloon,
                          statushelp=balloon,
                          bg=self.bg,
                          iconpath=ICONPATH )
            else:
                head, ext = os.path.splitext(icon1)
                ICONPATH1 = os.path.join(ICONPATH, icon1)
                if ext == '.gif':
                    Icon = Tkinter.PhotoImage(file=ICONPATH1, master=master)#, master=self.ROOT)
                else:
                    import Image
                    import ImageTk
                    image = Image.open(ICONPATH1)
                    Icon = ImageTk.PhotoImage(image=image, master=master)
                if item[name]['type'] == 'menubutton':
                    self.buttonIcons[name] = Icon
                    #lButton = Tkinter.Menubutton(self.buttonBar, 
                    lButton = CADDMenubutton(self.buttonBar, 
                                                     text = 'load library',
                                                     image=Icon
                                                     )
                    self.fastLibsMenu2 = Tkinter.Menu(lButton, tearoff=0)
                    self.updateFastLibs()
                    lButton.menu = self.fastLibsMenu2
                    lButton['menu'] = lButton.menu
                elif item[name]['type'] == 'checkbutton':
                    if hasattr(self, 'buttonVariables') is False:
                        self.buttonVariables = {}
                    if self.buttonVariables.has_key(name) is False:
                        self.buttonVariables[name] = Tkinter.IntVar()
                    self.buttonIcons[name] = [Icon,]   
                    #lButton = Tkinter.Checkbutton(self.buttonBar,
                    lButton = CADDCheckbutton(self.buttonBar,
                                               image=Icon,
                                               indicatoron=0,
                                               variable=self.buttonVariables[name],
                                               command=func,
                                               selectcolor='lightgrey',
                                               bg=self.bg,
                                               #background='white',
                                               )

                    if item[name].has_key('icon2'):
                        icon2 = item[name]['icon2']
                        head2, ext2 = os.path.splitext(icon2)
                        ICONPATH2 = os.path.join(ICONPATH, icon2)
                        if ext2 == '.gif':
                            Icon2 = Tkinter.PhotoImage(file=ICONPATH2, master=master)#, master=self.ROOT)
                        else:
                            image2 = Image.open(ICONPATH2)
                            Icon2 = ImageTk.PhotoImage(image=image2, master=master)
                        self.buttonIcons[name].append(Icon2)
                        lButton.configure(selectimage=Icon2)

                # add ballon to this button
                if hasattr(self.buttonBar, 'balloons') is False:
                    self.buttonBar.balloons = Pmw.Balloon(self.buttonBar, yoffset=0)
                self.buttonBar.balloons.bind(lButton, balloon, balloon)
                
                lButton.pack(side=Tkinter.LEFT, padx="1m")
                # add the button to the list stored in the master
                self.buttonBar.toolbarButtonDict[name] = lButton


    def showHideLibraries_cb(self, event=None):
        """Display or hide the node libraries"""

        bl = self.buttonBar.toolbarButtonDict

        mybutton = bl['showHideLib']

        menu = self.menuButtons['Libraries'].menu
        try:
            menu.index("Show libraries")
            show = True
        except:
            show = False

        if show: # pack the frame
            self.modulePagesF.pack(expand=1, fill='both')
            menu.entryconfigure('Show libraries', label='Hide libraries')
            # extend pane, we need 2 steps, else the pane is displd. too big
            self.top.configurepane('ModulePages', min=150, max=150)
            self.top.configurepane('ModulePages', min=100, max=10000000)
            mybutton.config(image=mybutton.icon2)


        else: # forget the frame
            self.modulePagesF.forget()
            menu.entryconfigure('Hide libraries', label='Show libraries')
            # and shrink pane
            self.top.configurepane('ModulePages', min=0, max=0)
            mybutton.config(image=mybutton.icon1)

