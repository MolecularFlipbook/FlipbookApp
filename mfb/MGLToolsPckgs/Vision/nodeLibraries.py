########################################################################
#
# Date: Jul 2003  Authors: Daniel Stoffler, Michel Sanner
#
#       stoffler@scripps.edu
#       sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Daniel Stoffler, Michel Sanner and TSRI
#
#########################################################################

import os, sys
import re
import string
import types
import Tkinter, Pmw
from mglutil.gui.BasicWidgets.Tk.fileBrowsers import FileOpenBrowser
from mglutil.util.packageFilePath import findAllPackages, \
     findModulesInPackage, findModulesInDirectory
from mglutil.gui.BasicWidgets.Tk.colorWidgets import ColorChooser

# this file contains the node libraries that can be loaded into Vision
# the key is the name of the library, the value is a tuple with the first
# entry providing the path to the file and the second a list of required Python
# packages
libraries = {
 'stdlib': ('Vision.StandardNodes',[]) 
 }


class LoadLibraryPanel:
    """A GUI to load Vision libraries. This object needs to be aware of the
Vision editor, which has to be passed to the constructor."""
    
    def __init__(self, editor):
        self.editor = editor   # Vision editor
        self.panel = None      # this Tkinter panel
        self.buildPanel()      # build the panel
        # pattern used to find the libname in the library file
        self.pattern = re.compile('=NodeLibrary')  
        self.openFileBrowser = FileOpenBrowser() # File Browser widget
        

    def buildPanel(self):
        # avoid rebuilding by potentially silly user...
        if self.panel is not None:
            self.show()
            return
        
        from Vision.nodeLibraries import libraries
        libKeys = libraries.keys()
	libKeys.sort()    
        
        root = self.panel = Tkinter.Toplevel()
        root.title('Load Libraries')
        root.protocol("WM_DELETE_WINDOW", self.hide)
        frame = Tkinter.Frame(root)
        frame.grid(columnspan=2)

        # Scrolled widget
        w = self.loadModuleWidget = Pmw.ScrolledListBox(
            frame,
            items=libKeys,
            labelpos = 'n',
            label_text = 'Select Library to be loaded',
            dblclickcommand=self.loadLibs_cb)
        w.grid(row=2, columnspan=2, padx=10, pady=10)
        w.component('listbox').configure(selectmode=Tkinter.EXTENDED,
                                         exportselection=0)
        # widget balloon
        balloon3 = Pmw.Balloon(frame)
        balloon3.bind(w,
              'Double-click entry, or choose multiple\nand hit OK')

        b1 = Tkinter.Button(frame, text='OK',command=self.loadLibs_cb)
        b1.grid(row=3,column=0,sticky='we')

        b2 = Tkinter.Button(frame, text='Dismiss', command=self.hide)
        b2.grid(row=3,column=1,sticky='we')
        # bring to front
        self.show()


    def loadLibrary(self, libname, libfile):
        from Vision.nodeLibraries import libraries
        libraries[libname] = (libfile, [])
        self.editor.addLibraryFromName(libname)


    def loadLibs_cb(self, event=None):
        # loading all the libraries currently selected in the widget
        libnames = self.loadModuleWidget.getcurselection()
        for libname in libnames:
            self.editor.addLibraryFromName(libname)


    def show(self, event=None):
        self.panel.deiconify()


    def hide(self, event=None):
        self.panel.withdraw()


class BrowseLibraryPanel:
    """A GUI to browse for NodeLibraries in all available packages"""
    
    def __init__(self, editor):
        self.editor = editor   # Vision editor
        self.panel = None      # this Tkinter panel
        self.mode = 'default'  # can be 'default' or 'all'
        self.buildPanel()      # build the panel


    def buildPanel(self):
        if self.panel is not None:
            self.show()
            return
        
        root = self.panel = Tkinter.Toplevel()
        root.title('Browse Vision Node Libraries')
        root.protocol("WM_DELETE_WINDOW", self.hide)
        frame = Tkinter.Frame(root)
        frame.grid(columnspan=3)

        #self.packages = findAllPackages()
        #packNames = self.packages.keys()
        #packNames.sort()

        self.findDefaultPackages()
        packNames = self.packages.keys()
        packNames.sort()
        
        rownum = 0

#        # browse button
#        browseLab = Tkinter.Label(frame, text='Directory of File: ')
#        browseLab.grid(row=rownum, column=0, sticky='e')
#        self.fileOrDirTkVar = Tkinter.StringVar()
#        browseEntry = Tkinter.Entry(frame, textvariable=self.fileOrDirTkVar)
#        browseEntry.grid(row=rownum, column=1, columnspan=2, sticky='ew')
#        browseEntry.bind('<Double-1>', self.fileBrowser_cb)
#        browseEntry.bind('<Return>', self.open_cb) 
#        rownum+=1

        # Scrolled widget showing all available packages
        self.packageGUI = Pmw.ScrolledListBox(
            frame,
            hscrollmode='static',
            items=packNames,
            labelpos = 'n',
            label_text = 'Select Package:',
            #dblclickcommand=self.browsePackage_cb,
            selectioncommand=self.browsePackage_cb,
            listbox_exportselection=0)
        self.packageGUI.component('horizscrollbar').configure(width=10)
        self.packageGUI.component('vertscrollbar').configure(width=10)
        
        self.packageGUI.grid(row=rownum, column=0, padx=10, pady=10)

        # Scrolled widget showing all modules with potential NodeLibraries 
        self.moduleGUI = Pmw.ScrolledListBox(
            frame,
            hscrollmode='static',
            items='',
            labelpos = 'n',
            label_text = 'Select Module:',
            #dblclickcommand=self.browseLibs_cb,
            selectioncommand=self.browseLibs_cb,
            listbox_exportselection=0)
        self.moduleGUI.grid(row=rownum, column=1, padx=10, pady=10)
        self.moduleGUI.component('horizscrollbar').configure(width=10)

        # Scrolled widget showing all NodeLibraries in a given module
        self.libraryGUI = Pmw.ScrolledListBox(
            frame,
            hscrollmode='static',
            items='',
            labelpos = 'n',
            label_text = 'Select Library:',
            dblclickcommand=self.loadLib_cb,
            #selectioncommand=self.loadLib_cb,
            listbox_exportselection=0)
        self.libraryGUI.grid(row=rownum, column=2, padx=10, pady=10)
        self.libraryGUI.component('horizscrollbar').configure(width=10)
        rownum+=1
        
##          reload = Tkinter.Button(frame, text='Reload Packages',
##                                  command=self.reloadPackages_cb)
##          reload.grid(row=rownum, column=0, sticky='we')

        load = Tkinter.Button(frame, text='Load Library',
                                command=self.loadLib_cb)
        load.grid(row=rownum, column=2, sticky='we')
        
##          rownum+=1
        
        self.modeButton = Tkinter.Button(frame, text='Show All',
                                         command=self.switchButton_cb)
        self.modeButton.grid(row=rownum, column=0, sticky='we')

        rownum+=1
        dismiss = Tkinter.Button(frame, text='Dismiss', command=self.hide)
        dismiss.grid(row=rownum, columnspan=3, sticky='we')


#    def open_cb(self, event=None):
#        name = self.fileOrDirTkVar.get()
#        from os import path
#        if path.isdir(name):
#            from glob import glob
#            self.moduleGUI.component('listbox').delete(0,'end')
#            mods = glob(path.join(name, '*.PY'))
#            mods.sort()
#            self.modules = findModulesInDirectory(name, 'NodeLibrary')
#            modNames = []
#            for key, value in self.modules.items():
#                pathPack = key.split(os.path.sep)
#                if pathPack[-1] == packName:
#                    newModName = map(lambda x: x[:-3], value)
#                    modNames = modNames + newModName
#                else:
#                    pIndex = pathPack.index(packName)
#                    prefix = string.join(pathPack[pIndex+1:], '.')
#                    newModName = map(lambda x: "%s.%s"%(prefix, x[:-3]), value)
#                    modNames = modNames + newModName
#            modNames.sort()
#            self.moduleGUI.setlist(modNames)
#
#        elif path.isfile(name):
#            import sys
#            direct, file = path.split(name)
#            sys.path.insert(0, direct)
#            mod = __import__(file)
#            self.libs = self.getLibraries(mod)
#            sys.path = sys.path[1:]


#    def fileBrowser_cb(self, event=None):
#        from tkFileDialog import asksaveasfilename
#        from tkFileDialog import askopenfilename
#        #file = asksaveasfilename(
#        file = askopenfilename(
#            filetypes=[ ('python', '*.py'), ('All files', '*')],
##            initialdir=self.currentdir, initialfile=libName+'.py',
#            title='Open library file')
#
#        if file=='':
#            return
#        else:
#            self.fileOrDirTkVar.set(file)
#            self.open_cb()


    def getLibraries(self, mod):
        from Vision.VPE import NodeLibrary
        libs = {}

        filename = mod.__file__
        if filename[-1] in ["c","o"]: # slice c from pyc or o from pyo 
            filename = filename[:-1]
        f = open(filename)
        sourceCode = f.read()
        f.close()

        for name in dir(mod):
            obj = getattr(mod, name)
            if isinstance(obj, NodeLibrary):
                # only add libraries that are actually created in this file
                patt = re.compile(".*%s *= *NodeLibrary"%name)
                found = patt.search(sourceCode)
                if found:
                    obj.modName = name
                    libs[obj.name] = obj
                else:
                    patt = re.compile("locals *\( *\) *\[ *libInstanceName *\] *= *NodeLibrary")
                    found = patt.search(sourceCode)
                    if found:
                        obj.modName = name
                        libs[obj.name] = obj
                
        libNames = libs.keys()
        libNames.sort()
        self.libraryGUI.setlist(libNames)
        return libs


    def getModules(self, package):
        self.modules = findModulesInPackage(package, 'NodeLibrary')
        packName = self.packageGUI.getcurselection()[0]
        modNames = []
        for key, value in self.modules.items():
            pathPack = key.split(os.path.sep)
            if pathPack[-1] == packName:
                newModName = map(lambda x: x[:-3], value)
                modNames = modNames + newModName
            else:
                pIndex = pathPack.index(packName)
                prefix = string.join(pathPack[pIndex+1:], '.')
                newModName = map(lambda x: "%s.%s"%(prefix, x[:-3]), value)
                modNames = modNames + newModName
        modNames.sort()
        self.moduleGUI.setlist(modNames)
        self.libraryGUI.clear()
        
    def browsePackage_cb(self, event=None):
        sel = self.packageGUI.getcurselection()
        if len(sel) == 0:
            return
        packName = sel[0]
        package = self.packages[packName]
        self.getModules(package)


    def browseLibs_cb(self, event=None):
        if len(self.moduleGUI.getcurselection()) == 0:
            return
        modName = self.moduleGUI.getcurselection()[0]
        packName = self.packageGUI.getcurselection()[0]
        importName = modName.replace(".", os.path.sep)
        #pathName = "%s%s%s.py"%(packName,os.path.sep,importName)
        #dir, file = os.path.split(pathName)
        #sys.path.insert(0, dir)
        mod = __import__(packName+'.'+modName, globals(), locals(),
                         [modName.split('.')[-1]])
        #sys.path = sys.path[1:]
        self.libs = self.getLibraries(mod)


    def loadLib_cb(self, event=None):
        try:
            libName = self.libraryGUI.getcurselection()[0]
        except:
            return
        lib = self.libs[libName]
        packName = self.packageGUI.getcurselection()[0]
        modName = self.moduleGUI.getcurselection()[0]
        self.editor.addLibraryInstance(lib, packName+'.'+modName, lib.modName)


    def show(self, event=None):
        self.panel.deiconify()


    def hide(self, event=None):
        self.panel.withdraw()


    def reloadPackages_cb(self, event=None):
        self.packages = findAllPackages()
        packNames = self.packages.keys()
        packNames.sort()
        self.packageGUI.setlist(packNames)
        self.moduleGUI.clear()
        self.libraryGUI.clear()


    def showDefaultPackages_cb(self, event=None):
        self.findDefaultPackages()
        packNames = self.packages.keys()
        packNames.sort()
        self.packageGUI.setlist(packNames)
        self.moduleGUI.clear()
        self.libraryGUI.clear()


    def showAllPackages_cb(self, event=None):
        self.reloadPackages_cb()


    def switchButton_cb(self, event=None):
        if self.mode == 'default':
            self.reloadPackages_cb()
            self.mode = 'all'
            self.modeButton.configure(text='Show Default')
        else:
            self.showDefaultPackages_cb()
            self.mode = 'default'
            self.modeButton.configure(text='Show All')
            

    def findDefaultPackages(self):
        packages = findAllPackages()
        default =  [
            'ARTK', 'DejaVu', 'FlexTree', 'MolKit', 'Pmv', 'Vision',
            'Volume', 'symserv', 'WebServices']

        # do these default values exist?
        tmp = []
        for k in default:
            if k in packages.keys():
                tmp.append(k)
        default = tmp

        # add the user libs to default
        from mglutil.util.packageFilePath import getResourceFolderWithVersion
        userResourceFolder = getResourceFolderWithVersion()
        if userResourceFolder is not None:
            userLibsDir = userResourceFolder + os.sep + 'Vision' + os.sep + 'UserLibs'
            from Vision import __path__
            lVisionLibrariesPath = __path__[0]+'Libraries'
            for k,v in packages.items():
                if v.startswith(userLibsDir):
                    default.append(k)
                elif v.startswith(lVisionLibrariesPath):
                    default.append(k)

        # now build the default list
        for k in packages.keys():
            if k not in default:
                del packages[k]
        self.packages = packages


class CreateLibraryPanel:
    """A GUI to create a new library of nodes"""
    
    def __init__(self, editor):
        self.editor = editor   # Vision editor
        self.panel = None      # this Tkinter panel
        self.buildPanel()      # build the panel
        

    def buildPanel(self):
        if self.panel is not None:
            self.show()
            return
        
        root = self.panel = Tkinter.Toplevel()
        root.title('Create Node Library')
        root.protocol("WM_DELETE_WINDOW", self.hide)
        frame = Tkinter.Frame(root)
        frame.pack(expand=1, fill='both')

        rownum=0
        self.libclassnametkvar = Tkinter.StringVar()
        Tkinter.Label(frame, text='Library class name:').grid(
            row=rownum, column=0,sticky='e')
        self.libclassnametk = Tkinter.Entry(
            frame, textvariable=self.libclassnametkvar)
        self.libclassnametk.grid(row=rownum, column=1, sticky='w')
        rownum += 1

        self.libnametkvar = Tkinter.StringVar()
        Tkinter.Label(frame, text='Library name:').grid(row=rownum, column=0,
                                                    sticky='e')
        self.libnametk = Tkinter.Entry(frame, textvariable=self.libnametkvar)
        self.libnametk.grid(row=rownum, column=1, sticky='w')
        rownum += 1

        self.libfiletkvar = Tkinter.StringVar()
        Tkinter.Label(frame, text='Library file:').grid(row=rownum, column=0,
                                                        sticky='e')
        self.libfiletk = Tkinter.Entry(frame, textvariable=self.libfiletkvar)
        self.libfiletk.grid(row=rownum, column=1, sticky='w')
        rownum += 1

        libDirs = []
        for directory in self.editor.userLibsDirs.keys():
            libDirs.append(directory)

        self.libsGUI = Pmw.ScrolledListBox(frame, items=libDirs,
            labelpos = 'n',
            label_text = 'Select library directory:',
            dblclickcommand=None)
        self.libsGUI.grid(row=rownum, columnspan=2, padx=1, pady=1)

        rownum += 1

        self.colorButton = Tkinter.Button(frame, text='Library Color ...',
                                          command=self.chooseColor)
        self.colorButton.grid(row=rownum, column=0, columnspan=2, sticky='ew')
        rownum += 1

        createButton = Tkinter.Button(frame, text='Create',
                                command=self.createLib_cb)
        createButton.grid(row=rownum, column=0, sticky='we')

        dismiss = Tkinter.Button(frame, text='Dismiss', command=self.hide)
        dismiss.grid(row=rownum, column=1, sticky='we')


    def chooseColor(self, event=None):
        top = Tkinter.Toplevel()
        colorChooser = ColorChooser(top, title='library color', immediate=1,
                                    commands=[self.setColor])
        colorChooser.pack()


    def setColor(self, color):
        from mglutil.util.colorUtil import ToHEX
        self.colorButton.configure(bg=ToHEX(color))
        

    def createLib_cb(self, event=None):
        classname = self.libclassnametkvar.get()
        if classname is None or len(classname)==0:
            return

        name = self.libnametkvar.get()
        if name is None or len(name)==0:
            return


        libfilename = self.libfiletkvar.get()
        if libfilename is None or len(libfilename) == 0:
            return

        if libfilename[-3:] != ".py":
            libfilename = libfilename + ".py"

        directory = self.libsGUI.get()
        if directory is None or len(directory)==0 or directory==():
            return

        # libsGUI might return the data packed in a tuple
        if type(directory) == types.TupleType:
            directory = directory[0]

        # build path by joining the directory with the parent path
        path = os.path.join(self.editor.userLibsDirs[directory], directory)

        # then add the file name
        file = os.path.join(path, libfilename)
            
        if os.path.exists(file):
            from Dialog import Dialog
            d = Dialog(None, {'title': 'File exisits',
                              'text':
                              'File "%s" already exists.'
                              ' Do you want to overwrite it ?'%file,
                              'bitmap': 'warning',
                              'default': 1,
                              'strings': ('Yes',
                                          'No')})
            if d.num==1: # 'No'
                return

        from Vision.VPE import NodeLibrary
        col = self.colorButton.cget('bg')
        newlib = NodeLibrary(name, col, mode='readWrite')
        newlib.varName = classname

        # write the library header
        f = open(file, 'w')
        map( f.write, newlib.getHeader())
        f.write("%s = NodeLibrary('%s', '%s', mode='readWrite')\n"%(
            newlib.varName, name, col))

        f.close()

        # load the library from the file using same mechanism as saved network
        from mglutil.util.packageFilePath import getObjectFromFile
        newlib = getObjectFromFile( file, classname)
        newlib.varName = classname

        modName = directory + "." + libfilename[:-3]
        modName = string.replace(modName, "/", ".")
        newlib.modName = modName
        # we need to __import__ to add this module to sys.modules
        # This fixes a problem when trying to add nodes to this new lib before
        # we restart and load the new library through 'loadLibrary'
        __import__(modName)
        
        self.editor.libraries[ newlib.name] = newlib
        self.editor.showLibrary(newlib)
        self.hide()


    def show(self, event=None):
        self.panel.deiconify()


    def hide(self, event=None):
        self.panel.withdraw()


class AddNodeToUserLibraryPanel:
    """A GUI to add a node to a user-defined node library"""
    
    def __init__(self, editor):
        self.editor = editor   # Vision editor
        self.panel = None      # this Tkinter panel
        self.buildPanel()      # build the panel
        self.currentdir = os.getcwd() # memory of directory used to save
        

    def buildPanel(self):
        if self.panel is not None:
            self.show()
            return
        
        root = self.panel = Tkinter.Toplevel()
        root.title('Add Node To User Library')
        self.frame = Tkinter.Frame(root)

        # find all readWrite libraries
        libs = []
        for libname, lib in self.editor.libraries.items():
            if lib.mode == 'readWrite':
                libs.append(libname)
        libs.sort()

        row = 0

        self.label1 = Tkinter.Label(self.frame, text='Node class name: ')
        self.label1.grid(row=row, column=0, sticky='w')

        self.classNameTk = Tkinter.StringVar()
        self.classNameEntry = Tkinter.Entry(self.frame,
                                            textvariable= self.classNameTk)
        self.classNameEntry.grid(row=row, column=1, sticky='ew')

        row += 1

        self.label2 = Tkinter.Label(self.frame, text='Library Category: ')
        self.label2.grid(row=row, column=0, sticky='w')

        self.categoryNameTk = Tkinter.StringVar()
        self.categoryNameEntry = Tkinter.Entry(self.frame,
                                            textvariable= self.categoryNameTk)
        self.categoryNameEntry.grid(row=row, column=1, sticky='ew')

        row += 1
        
        # Scrolled widget showing all available readWrite libraries
        self.libsGUI = Pmw.ScrolledListBox(
            self.frame, items=libs, labelpos = 'n',
            label_text = 'Select library to add node',
            dblclickcommand=None)
        self.libsGUI.grid(row=row, column=0, columnspan=2, padx=10, pady=10)

        row += 1

        self.save = Tkinter.Button(self.frame, text='Add Node...',
                                   command=self.addNode_cb)
        self.save.grid(row=row, column=0, sticky='we')

        self.cancel = Tkinter.Button(self.frame, text='Dismiss',
                                     command=self.hide)
        self.cancel.grid(row=row, column=1, sticky='we')
        self.frame.grid(columnspan=3, sticky='ew')


    def addNode_cb(self, event=None):
        classname = self.classNameTk.get()
        if classname is None or len(classname) == 0:
            return

        category = self.categoryNameTk.get()
        if category is None or len(category) == 0:
            return
        
        libname = self.libsGUI.get()
        if libname is None or len(libname) == 0 or libname == ():
            return
        libname = libname[0]
        library = self.editor.libraries[libname]

        if len(self.editor.currentNetwork.selectedNodes) != 1:
            return
        node = self.editor.currentNetwork.selectedNodes[0]

        self.editor.addNodeToUserLibrary(node, classname, category, library)
        self.hide()


    def show(self, event=None):
        self.panel.deiconify()

        # find all readWrite libraries
        libs = []
        for libname, lib in self.editor.libraries.items():
            if lib.mode == 'readWrite':
                libs.append(libname)
        libs.sort()
        self.libsGUI.setlist(libs)
        
       


    def hide(self, event=None):
        self.panel.withdraw()






