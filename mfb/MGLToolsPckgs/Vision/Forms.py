#########################################################################
#
# Date: Jul 2003  Author: Daniel Stoffler
#
#       stoffler@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Daniel Stoffler and TSRI
#
#########################################################################
#$Id: Forms.py,v 1.32 2008/02/08 23:37:12 mgltools Exp $

import Tkinter, Pmw
import sys, re, os
import string
import webbrowser
from string import join
from Tkinter import *
from types import StringType
import tkFileDialog

from NetworkEditor.customizedWidgets import kbScrolledCanvas
from mglutil.util.callback import CallBackFunction
from mglutil.util.packageFilePath import findAllPackages, findModulesInPackage
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser, \
     kbScrolledListBox
from mglutil.util.misc import ensureFontCase

VarDict={}

class Dialog:
    
    def __init__(self):
        self.panel = None
        self.bg = 'royalblue'
        self.fg = 'white'

        self.buildPanel()

        # bind OK button callback
        self.panel.protocol("WM_DELETE_WINDOW", self.Ok)
        # disable typing stuff in the window
        self.textFrame.configure(state='disabled')
##          # disable resizing
##          self.panel.resizable(height='false', width='false')


    def buildPanel(self):
        # prevent re-creation
        if self.panel is not None:
            self.panel.show()
            return
        
        root = self.panel = Tkinter.Toplevel()
        self.frame = Tkinter.Frame(root, borderwidth=2,
                                   relief='sunken', padx=5, pady=5)
        self.frame.pack(side='top', expand=1, fill='both')

        txtFrame = Tkinter.Frame(self.frame)

        self.textFrame = Tkinter.Text(txtFrame, background=self.bg,
                                      exportselection=1, padx=10, pady=10,)
        
        self.textFrame.tag_configure('big', font=(ensureFontCase('Courier'), 24, 'bold'),
                                foreground=self.fg)
        self.textFrame.tag_configure('medium', font=(ensureFontCase('helvetica'), 14, 'bold'),
                                foreground=self.fg)
        self.textFrame.tag_configure('normal12',
                                     font=(ensureFontCase('helvetica'), 12, 'bold'),
                                     foreground=self.fg)
        self.textFrame.tag_configure('normal10',
                                     font=(ensureFontCase('helvetica'), 10, 'bold'),
                                     foreground=self.fg)
        self.textFrame.tag_configure('normal8',
                                     font=(ensureFontCase('helvetica'), 8, 'bold'),
                                     foreground=self.fg)
        self.textFrame.tag_configure('email', font=(ensureFontCase('times'), 10, 'bold'),
                                     foreground='lightblue')
        self.textFrame.tag_configure('http', font=(ensureFontCase('times'), 12, 'bold'),
                                     foreground='lightblue')
        self.textFrame.tag_configure('normal10b',
                                     font=(ensureFontCase('helvetica'), 10, 'bold'),
                                     foreground='lightblue')
        
        self.textFrame.pack(side='left', expand=1, fill='both')

        # provide a scrollbar
        self.scroll = Tkinter.Scrollbar(txtFrame, command=self.textFrame.yview)
        self.textFrame.configure(yscrollcommand = self.scroll.set)
        self.scroll.pack(side='right', fill='y')
        txtFrame.pack(expand=1, fill='both')
        
        # proved an OK button
        buttonFrame = Tkinter.Frame(self.frame)
        buttonFrame.pack(side='bottom', fill='x')
        self.buttonOk = Tkinter.Button(buttonFrame, text='  Ok  ',
                                       command=self.Ok)
        self.buttonOk.pack(padx=6, pady=6)


    def Ok(self, event=None):
        self.hide()


    def show(self, event=None):
        self.panel.deiconify()


    def hide(self, event=None):
        self.panel.withdraw()


class AboutDialog(Dialog):

    def __init__(self):
        Dialog.__init__(self)


    def buildPanel(self):
        Dialog.buildPanel(self) # call base class method

        # remove scrollbar
        self.scroll.forget()

        # add own stuff
        self.panel.title('About Vision')

        self.textFrame.configure()

        self.textFrame.insert('end', 'Vision\n', 'big')
        self.textFrame.insert('end',
                         'A Visual Programming Environment for Python.\n\n',
                              'medium')
        self.textFrame.insert('end',
                                   'Michel F. Sanner','normal12')
        self.textFrame.insert('end', '\t\tsanner@scripps.edu\n', 'email')
        self.textFrame.insert('end', 'Daniel Stoffler', 'normal12')
        self.textFrame.insert('end', '\t\tstoffler@scripps.edu\n','email')
        self.textFrame.insert('end', 'Guillaume Vareille', 'normal12')
        self.textFrame.insert('end', '\tvareille@scripps.edu\n\n','email')
        self.textFrame.insert('end', 'Vision home page:\t', 'normal12')
        self.textFrame.insert('end', 
                              'http://mgltools.scripps.edu/\n\n',
                              'http')
        self.textFrame.insert('end', 'The Scripps Research Institute\n'+\
                              'Molecular Graphics Lab\n'+\
                              '10550 N Torrey Pines Rd\n'+\
                              'La Jolla CA 92037 USA\n\n', 'normal10')
        self.textFrame.insert('end',
                              'Python version:  %s\t'%sys.version.split()[0],
                              'normal8')

        # handle weird tk version num in windoze python >= 1.6 (?!?)
        # Credits for this code go to the people who brought us idlelib!
        tkVer = `Tkinter.TkVersion`.split('.')
        tkVer[len(tkVer)-1] = str('%.3g'%(
            float('.'+tkVer[len(tkVer)-1])))[2:]
        if tkVer[len(tkVer)-1] == '':
            tkVer[len(tkVer)-1] = '0'
        tkVer = string.join(tkVer,'.')
        self.textFrame.insert('end', 'Tk version:  %s\n'%tkVer,
                         'normal8')

        #self.panel.geometry("+%d+%d" %(self.panel.winfo_rootx()+30,
        #                              self.panel.winfo_rooty()+30))
        


class AcknowlDialog(Dialog):

    def __init__(self):
        Dialog.__init__(self)


    def buildPanel(self):
        Dialog.buildPanel(self) # call base class method

        # add own stuff
        self.panel.title('Acknowledgements')

        self.textFrame.insert('end', 'Vision Acknowledgements\n', 'big')
        self.textFrame.insert('end',
                         '\nThis work is supported by:\n\n', 'medium')
        self.textFrame.insert('end',
                              'Swiss National Science Foundation\n'+\
                              'Grant No. 823A-61225\n', 'normal12')
        self.textFrame.insert('end', 'http://www.snf.ch\n\n', 'http')
        
        self.textFrame.insert('end',
                              'National Biomedical Computation Resource\n'+\
                              'Grant No. NBCR/NIH RR08605\n', 'normal12')
        self.textFrame.insert('end', 'http://nbcr.sdsc.edu\n\n', 'http')

        self.textFrame.insert('end',
           'National Partnership for Advanced Computational Infrastructure\n'+\
           'Grant No. NPACI/NSF CA-ACI-9619020\n', 'normal12')
        self.textFrame.insert('end', 'http://www.npaci.edu\n\n', 'http')


        self.textFrame.insert('end',
          'The authors would like to thank all the people in the Olson lab\n'+\
          'for their support and constructive criticism.\n', 'normal10')
        self.textFrame.insert('end', 'http://www.scripps.edu/pub/olson-web\n',
                              'http')
  

class RefDialog(Dialog):

    def __init__(self):
        Dialog.__init__(self)


    def buildPanel(self):
        Dialog.buildPanel(self) # call base class method

        # remove scrollbar
        self.scroll.forget()

        # add own stuff
        self.panel.title('References')

        self.textFrame.insert('end', 'Vision References\n\n', 'big')

        self.textFrame.insert('end',
            'ViPEr, a Visual Programming Environment for Python\n','normal12') 
        self.textFrame.insert('end',
           'Sanner, M.F., Stoffler, D., and Olson, A.J. (2002)\n','normal10b') 
        self.textFrame.insert('end',
       'In proceedings of the 10th International Python Conference 2002,\n'+\
       'Virginia USA.\n\n','normal10')
        

        self.textFrame.insert('end',
       'Integrating biomolecular analysis and visual programming:\n'+\
       'flexibility and interactivity in the design of bioinformatics tools\n',
       'normal12')
        self.textFrame.insert('end',
                              'Stoffler, D., Coon, S.I., Huey, R., Olson, '+\
                              'A.J., and Sanner, M.F. (2003)\n','normal10b')
        self.textFrame.insert('end',
        'In proceedings of HICSS-36, Hawaii International conference\n'+\
        'on system sciences, 2003, Hawaii.\n\n','normal10')


class ChangeFonts:

    def __init__(self, editor=None):
        self.panel = None
        self.editor = editor # instance of VPE

        self.buildPanel()

        # bind Cancel button callback on kill window
        self.panel.protocol("WM_DELETE_WINDOW", self.Cancel_cb)


    def buildPanel(self):
        # prevent re-creation
        if self.panel is not None:
            self.panel.show()
            return
        
        root = self.panel = Tkinter.Toplevel()
        frame = Tkinter.Frame(root, borderwidth=2,
                                   relief='sunken')#, padx=5, pady=5)
        frame.pack(side='top', expand=1, fill='both')

        ## Font Group ##
        fontGroup = Pmw.Group(frame, tag_text='Font Chooser')
        fontGroup.pack(fill='both', expand=1, padx=6, pady=6)

        f1 = Tkinter.Frame(fontGroup.interior())
        f1.pack(side='top', fill='both', expand=1)
        f2 = Tkinter.Frame(fontGroup.interior())
        f2.pack(side='bottom', fill='both', expand=1)
        
        familyNames=list(root.tk.splitlist(root.tk.call('font','families')))
        familyNames.sort()
        self.fontChooser = Pmw.ComboBox(
            f1,
            label_text = 'Font Name',
            labelpos = 'n',
            scrolledlist_items = familyNames,
            selectioncommand = None
            )
        self.fontChooser.pack(side='left', expand=1, fill='both',
                              padx=6, pady=6)

        sizes = [6,7,8,10,12,14,18,24,48]
        self.sizeChooser = Pmw.ComboBox(
            f1,
            label_text = 'Font Size',
            labelpos = 'n',
            scrolledlist_items = sizes,
            selectioncommand = None,
            entryfield_entry_width=4,
            )
        self.sizeChooser.pack(side='left', expand=1, fill='both',
                              padx=6, pady=6)
        
        
        styles = ['normal', 'bold', 'italic', 'bold italic']
        self.styleVarTk = Tkinter.StringVar()
        for i in range(len(styles)):
            b = Tkinter.Radiobutton(
                f2,
                variable = self.styleVarTk,
                text=styles[i], value=styles[i])
            b.pack(side='left', expand=1, fill='both')

        ## End Font Group ## ##########################################

        ## GUI Group ##

        guiGroup = Pmw.Group(frame, tag_text='GUI Component to Apply Font')
        guiGroup.pack(fill='both', expand=1, padx=6, pady=6)
        group1 = ['All', 'Menus', 'LibTabs', 'Categories']
        group2 = ['LibNodes', 'NetTabs', 'Nodes', 'Root']
        self.groupVarTk = Tkinter.StringVar()
        frame1 = Tkinter.Frame(guiGroup.interior())
        frame2 = Tkinter.Frame(guiGroup.interior())
        frame1.pack(side='top', fill='both', expand=1)
        frame2.pack(side='bottom', fill='both', expand=1)

        for i in range(len(group1)):
            b = Tkinter.Radiobutton(
                frame1,
                variable = self.groupVarTk,
                text=group1[i], value=group1[i])
            b.grid(row=0, column=i, pady=6)
            
        for i in range(len(group2)):
            b = Tkinter.Radiobutton(
                frame2,
                variable = self.groupVarTk,
                text=group2[i], value=group2[i])
            b.grid(row=0, column=i, pady=6)
 
        buttonFrame = Tkinter.Frame(root, borderwidth=2,
                                   relief='sunken', padx=5, pady=5)
        buttonFrame.pack(side='top', expand=1, fill='both')
        self.buttonOk = Tkinter.Button(buttonFrame, text='  Ok  ',
                                       command=self.Ok_cb)
        self.buttonApply = Tkinter.Button(buttonFrame, text='  Apply  ',
                                       command=self.Apply_cb)
        self.buttonCancel = Tkinter.Button(buttonFrame, text='  Cancel  ',
                                       command=self.Cancel_cb)
                
        self.buttonOk.grid(row=0, column=0, padx=6, pady=6)
        self.buttonApply.grid(row=0, column=1, padx=6, pady=6)
        self.buttonCancel.grid(row=0, column=2, padx=6, pady=6)

        # set default values
        try:
            self.fontChooser.selectitem(ensureFontCase('helvetica'))
            self.sizeChooser.selectitem(2) # choose '8'
            self.styleVarTk.set('normal')
            self.groupVarTk.set('Nodes')
        except:
            pass


    def get(self, event=None):
        gui = self.groupVarTk.get()
        ft = self.fontChooser.get()
        sz = self.sizeChooser.get()
        sty = self.styleVarTk.get()
        font = (ft, sz, sty)
        return (gui, font)

        
    def Ok_cb(self, event=None):
        self.Apply_cb()
        self.Cancel_cb()
        

    def Apply_cb(self, event=None):
        if self.editor is not None:
            cfg = self.get()
            self.editor.setFont(cfg[0], cfg[1])
            from Vision.UserLibBuild import saveFonts4visionFile
            saveFonts4visionFile(self.editor.font)
        

    def Cancel_cb(self, event=None):
        self.hide()
    
            
    def show(self, event=None):
        self.panel.deiconify()


    def hide(self, event=None):
        self.panel.withdraw()



class SearchNodesDialog:
    """Search Vision nodes: the string matches either the node name or the
node's document string. Found nodes are displayed in the scrolled canvas of
this widget, and can be drag-and-drop-ed to the network canvas.
A new search clears the previously found nodes"""

    def __init__(self, editor=None):
        self.panel = None
        self.editor = editor      # instance of VPE
        self.entryVarTk = Tkinter.StringVar()  # Entry var
        self.cbVarTk = Tkinter.IntVar()        # checkbutton var
        self.choicesVarTk = Tkinter.StringVar()# radiobutton choices var
        self.choices = ['Search current lib only', 'Search all loaded libs',
                        'Search all packages\non system path (slower)']
        
        self.searchNodes = []     # list of found nodes
        self.libNodes = []        # list of nodes displayed in our libCanvas
        self.posyForLibNode = 15  # posy for nodes in lib canvas
        self.maxxForLibNode = 0   # maxx for nodes in lib canvas
        # build GUI
        self.buildPanel()
        # bind Cancel button callback on kill window
        self.panel.protocol("WM_DELETE_WINDOW", self.Cancel_cb)


    def buildPanel(self):
        # prevent re-creation
        if self.panel is not None:
            self.panel.show()
            return
        
        root = self.panel = Tkinter.Toplevel()

        # add menu bar
        self.menuBar = Tkinter.Menu(root)
        self.optionsMenu = Tkinter.Menu(self.menuBar, tearoff=0)
        self.optionsMenu.add_command(label="Hide Search Options",
                                     command=self.showHideOptions_cb)

        self.menuBar.add_cascade(label="Options", menu=self.optionsMenu)
        root.config(menu=self.menuBar)
                
        frame = Tkinter.Frame(root, borderwidth=2, relief='sunken')
        frame.pack(side='top', expand=1, fill='both')

        # build infrastructure for search panes with scrolled canvas
        sFrame = Tkinter.Frame(frame)
        sFrame.pack(expand=1, fill='both')
        # add panes
        self.searchPane = Pmw.PanedWidget(sFrame, orient='horizontal',
                                   hull_relief='sunken',
                                   hull_width=120, hull_height=120,
                                   )
        self.searchPane.pack(expand=1, fill="both")

        searchPane = self.searchPane.add("SearchNodes", min=60)
        self.searchPane.configurepane("SearchNodes", min=10)
        usedPane = self.searchPane.add("UsedNodes", min=10)
        # this is the canvas we use to display found nodes
        self.searchCanvas = kbScrolledCanvas(
            searchPane,
            borderframe=1,
            #usehullsize=1, hull_width=60, hull_height=80,
            #vscrollmode='static',#hscrollmode='static',
            vertscrollbar_width=8,
            horizscrollbar_width=8,
            labelpos='n', label_text="Found Nodes",
            )
        self.searchCanvas.pack(side='left', expand=1, fill='both')

        self.editor.idToNodes[self.searchCanvas] = {}

        # this is the canvas we use to display nodes we have drag-and-dropped
        # to the network
        self.libCanvas = kbScrolledCanvas(
            usedPane,
            borderframe=1,
            #usehullsize=1, hull_width=60, hull_height=80,
            #vscrollmode='static',#hscrollmode='static',
            vertscrollbar_width=8,
            horizscrollbar_width=8,
            labelpos='n', label_text="Used Nodes",
            )
        self.libCanvas.pack(side='right', expand=1, fill='both')

        self.editor.idToNodes[self.libCanvas] = {}

        
        lowerFrame = Tkinter.Frame(frame)
        lowerFrame.pack() # no expand
        
        # add options buttons
        self.optionsGroup = Pmw.Group(lowerFrame, tag_text="Search Options")
        self.optionsGroup.grid(row=0,column=0, sticky='we',padx=6, pady=6)

        cb = Tkinter.Checkbutton(self.optionsGroup.interior(),
                                 text="Case sensitive", variable=self.cbVarTk)
        cb.grid(row=0, column=0, columnspan=2, sticky='we')

        for i in range(len(self.choices)):
            b = Tkinter.Radiobutton(
                self.optionsGroup.interior(),
                variable = self.choicesVarTk, value=self.choices[i])
            l = Tkinter.Label(self.optionsGroup.interior(),
                              text=self.choices[i])
            b.grid(row=i+1, column=0, sticky='we')
            l.grid(row=i+1, column=1, sticky='w')

        self.choicesVarTk.set(self.choices[1])

        # add Entry
        eFrame = Tkinter.Frame(lowerFrame)
        eFrame.grid(row=1, column=0, sticky='we')
        eLabel = Tkinter.Label(eFrame, text='Search string:')
        eLabel.pack(side='left', expand=1, fill='x')
        entry = Tkinter.Entry(eFrame, textvariable=self.entryVarTk)
        entry.bind('<Return>', self.search)
        entry.pack(side='right', expand=1, fill='x')
        
        # add buttons
        bFrame = Tkinter.Frame(lowerFrame)
        bFrame.grid(row=2, column=0, sticky='we')
        button1 = Tkinter.Button(bFrame, text="Search", relief="raised",
                                 command=self.Apply_cb)
        button2 = Tkinter.Button(bFrame, text="Dismiss", relief="raised",
                                 command=self.Cancel_cb)
        button1.pack(side='left', expand=1, fill='x')
        button2.pack(side='right', expand=1, fill='x')

        # Pmw Balloon
        self.balloons = Pmw.Balloon(master=None, yoffset=10)
        
        # Drag-and-Drop callback for searchCanvas
        cb = CallBackFunction(self.editor.startDNDnode, self.searchCanvas)
        self.searchCanvas.component('canvas').bind('<Button-1>', cb )
        # Drag-and-Drop callback for libCanvas
        cb = CallBackFunction(self.editor.startDNDnode, self.libCanvas)
        self.libCanvas.component('canvas').bind('<Button-1>', cb )


    def Apply_cb(self, event=None):
        if self.editor is not None:
            self.search()


    def Cancel_cb(self, event=None):
        self.hide()
    
            
    def show(self, event=None):
        self.panel.deiconify()


    def hide(self, event=None):
        self.panel.withdraw()


    def search(self, event=None):
        searchStr = self.entryVarTk.get()
        if searchStr is None or len(searchStr) == 0:
            return

        canvas = self.searchCanvas.component('canvas')
        
        # clear previous matches
        if len(self.searchNodes):
            for node in self.searchNodes:
                self.deleteNodeFromPanel(node)

        self.searchNodes = []
        self.editor.idToNodes[self.searchCanvas] = {}
        posy = 15
        maxx = 0

        nodes = {}

        caseSensitive = self.cbVarTk.get()
        if not caseSensitive:
            searchStr = string.lower(searchStr)
        pat = re.compile(searchStr)
        
        # loop over libraries
        choice = self.choicesVarTk.get()
        if choice == self.choices[0]: # current lib
            lib = self.editor.ModulePages.getcurselection()
            libraries = [ (lib, self.editor.libraries[lib]) ]
            
        elif choice == self.choices[1]: # all loaded libs
            libraries = self.editor.libraries.items()

        else: # all packages on disk
            libraries = self.searchDisk()
            

        for libInd in range(len(libraries)):        
            libName, lib = libraries[libInd]
            categories = lib.libraryDescr.values()
            # loop over categories
            for catInd in range(len(lib.libraryDescr)):
                cat = categories[catInd]
                for nodeInd in range(len(cat['nodes'])):
                    node = cat['nodes'][nodeInd]

                    # match node name
                    name = node.name
                    if not caseSensitive:
                        name = string.lower(node.name)
                    res = pat.search(name)
                    if res:
                        nodes, maxx, posy = self.addNodeToSearchPanel(
                            node, nodes, maxx, posy)
                        continue

                    # match node document string
                    doc = node.nodeClass.__doc__
                    if doc is None or doc == '':
                        continue

                    if not caseSensitive:
                        doc = string.lower(doc)
                    res = pat.search(doc)
                    if res:
                        nodes, maxx, posy = self.addNodeToSearchPanel(
                            node, nodes, maxx, posy)

        # update scrolled canvas
        canvas.configure(width=60, height=150,
                         scrollregion=tuple((0,0,maxx,posy)))
                        
        self.editor.idToNodes[self.searchCanvas] = nodes

        
    def addNodeToSearchPanel(self, node, nodes, maxx, posy):
        from NetworkEditor.items import NetworkNode
        sc_canvas = self.searchCanvas
        
        font = self.editor.font['LibNodes']
        canvas = sc_canvas.component('canvas')

        n1 = NetworkNode(name=node.name)
        n1.iconMaster = sc_canvas
        n1.buildSmallIcon(sc_canvas, 10, posy, font)

        color = node.kw['library'].color
        canvas.itemconfigure(n1.id, fill=color)
        
        self.balloons.tagbind(sc_canvas, n1.iconTag,
                              node.nodeClass.__doc__)

        bb = sc_canvas.bbox(n1.id)
        w = bb[2]-bb[0]
        h = bb[3]-bb[1]
        maxx = max(maxx, w)
        posy = posy + h + 8

        nodes[n1.id] = (n1, node)
        self.searchNodes.append(n1)

        return nodes, maxx, posy


    def addNodeToLibPanel(self, node):
        if node in self.libNodes:
            return
        
        from NetworkEditor.items import NetworkNode
        sc_canvas = self.libCanvas
        
        font = self.editor.font['LibNodes']
        canvas = sc_canvas.component('canvas')

        n1 = NetworkNode(name=node.name)
        n1.iconMaster = sc_canvas

        posy = self.posyForLibNode
        n1.buildSmallIcon(sc_canvas, 10, posy, font)

        color = node.kw['library'].color
        canvas.itemconfigure(n1.id, fill=color)
        
        self.balloons.tagbind(sc_canvas, n1.iconTag,
                              node.nodeClass.__doc__)

        bb = sc_canvas.bbox(n1.id)
        w = bb[2]-bb[0]
        h = bb[3]-bb[1]
        self.maxxForLibNode = max(self.maxxForLibNode, w)
        posy = posy + h + 8
        self.posyForLibNode = posy

        self.libNodes.append(node)
        nodes = self.editor.idToNodes[self.libCanvas]
        nodes[n1.id] = (n1, node)
        self.editor.idToNodes[self.libCanvas] = nodes

        # update scrolled canvas
        maxx = self.maxxForLibNode
        canvas.configure(width=60, height=150,
                         scrollregion=tuple((0,0,maxx,posy)))
        
        
    def deleteNodeFromPanel(self, node):
        canvas = self.searchCanvas.component('canvas')
        # unbind proxy node balloon
        self.balloons.tagunbind(canvas, node.iconTag)
        # delete node icon
        canvas.delete(node.textId)
        canvas.delete(node.innerBox)
        canvas.delete(node.outerBox)
        canvas.delete(node.iconTag)


    def showHideOptions_cb(self, event=None):
        mode = 'show'
        try:
            index = self.optionsMenu.index("Hide Search Options")
            mode = 'hide'
        except:
            pass

        if mode == 'hide':
            self.optionsGroup.grid_forget()
            self.optionsMenu.entryconfig("Hide Search Options",
                                         label="Show Search Options")
        else:
            self.optionsGroup.grid(row=0, padx=6, pady=6)
            self.optionsMenu.entryconfig("Show Search Options",
                                         label="Hide Search Options")
 


    def searchDisk(self):
        libraries = []
        packages = findAllPackages()
        for packName, packNameWithPath in packages.items():
            modNames = self.getModules(packName, packNameWithPath)
            if len(modNames):
                for modName in modNames:
                    moduleName =  packName+'.'+modName
                    try:
                        mod = __import__(
                            moduleName, globals(), locals(),
                            modName.split('.')[-1])
                        libs = self.getLibraries(mod)
                        for name,lib in libs.items():
                            lib.modName = moduleName
                            libraries.append( (name,lib) )
                    except:
                        print "Could not import module %s from %s!"%(
                            modName, os.getcwd() )
                        
        return libraries
    

    def getModules(self, packName, packNameWithPath):
        modules = findModulesInPackage(packNameWithPath, 'NodeLibrary')
        modNames = []
        for key, value in modules.items():
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
        return modNames
    

    def getLibraries(self, mod):
        from Vision.VPE import NodeLibrary
        libs = {}
        for name in dir(mod):
            obj = getattr(mod, name)
            if isinstance(obj, NodeLibrary):
                obj.varName = name
                libs[obj.name] = obj
        return libs


class HelpDialog:

    def __init__(self, title="Help Dialog", message="", bg=None,
                 fg=None, font=(ensureFontCase('helvetica'), 8, 'bold'),):
        self.panel = None 
        self.title = title         # Title of this Dialog window
        self.message = message     # Help message
        self.bg = bg               # Frame background
        self.fg = fg               # text color
        self.font = font           # text font

        self.buildPanel()

        self.panel.title(self.title)
        
        # bind OK button callback
        self.panel.protocol("WM_DELETE_WINDOW", self.Ok)
        # disable typing stuff in the window
        self.textFrame.configure(state='disabled')


    def buildPanel(self):
        # prevent re-creation
        if self.panel is not None:
            self.panel.show()
            return

        root = self.panel = Tkinter.Toplevel()
        self.frame = Tkinter.Frame(
            root, borderwidth=2, relief='sunken', padx=5, pady=5)
        self.frame.pack(side='top', expand=1, fill='both')

        txtFrame = Tkinter.Frame(self.frame)

        self.textFrame = Tkinter.Text(
            txtFrame, exportselection=1, padx=10, pady=10,)

        if self.bg is not None:
            self.textFrame.configure(bg=self.bg)
 
        self.textFrame.tag_configure('standard', font=self.font)
        if self.fg is not None:
            self.textFrame.tag_configure('standard', foreground=self.fg)

        self.textFrame.pack(side='left', expand=1, fill='both')

        # now add the message
        self.textFrame.insert('end', self.message, 'standard')


        # provide a scrollbar
        self.scroll = Tkinter.Scrollbar(txtFrame, command=self.textFrame.yview)
        self.textFrame.configure(yscrollcommand = self.scroll.set)
        self.scroll.pack(side='right', fill='y')
        txtFrame.pack(expand=1, fill='both')
        
        # proved an OK button
        buttonFrame = Tkinter.Frame(self.frame)
        buttonFrame.pack(side='bottom', fill='x')
        self.buttonOk = Tkinter.Button(buttonFrame, text='  Ok  ',
                                       command=self.Ok)
        self.buttonOk.pack(padx=6, pady=6)


    def Ok(self, event=None):
        self.hide()


    def show(self, event=None):
        self.panel.deiconify()


    def hide(self, event=None):
        self.panel.withdraw()



class BugReport:
    def __init__(self, title="Bug Report", message="", bg=None,
                 fg=None, font=(ensureFontCase('helvetica'), 8, 'bold'),):
        self.panel = None 
        self.title = title         # Title of this Dialog window
        self.message = message     # Help message
        self.bg = bg               # Frame background
        self.fg = fg               # text color
        self.font = font           # text font

        self.buildPanel()

        self.panel.title(self.title)
        
        # bind OK button callback
        self.panel.protocol("WM_DELETE_WINDOW", self.Ok)
         
    
        
    def doit(self):
        self.showpdbfile_cb()
        self.show_upload_page()
        
          
            
    def __call__(self):
        
        apply(self.doitWrapper,(),{})
    
    
    def buildPanel(self):
         
        
        root = self.panel = Tkinter.Toplevel()    
        self.frame = Tkinter.Frame(root, background='white',borderwidth=2, relief='sunken', padx=5, pady=5)
        self.frame.pack(side='top', expand=1, fill='both')    
        ##### short desc################
               
        self.shortdesctext = Pmw.ScrolledText(self.frame,                 
                    label_text='Summary(one line description)',
                    labelpos='nw',text_padx=20,
                    text_pady=2,)
        self.shortdesctext.pack(side='left', expand=1, fill='both')
        self.shortdesctext.grid(sticky='nw',row=0,column=0,columnspan=2)
        
        #########desc text################
        
        self.desctext = Pmw.ScrolledText(self.frame,                 
                    label_text='Description',
                    labelpos='nw',text_padx=20,
                    text_pady=2,)
        self.desctext.pack(side='left', expand=1, fill='both')
        self.desctext.grid(sticky='nw',row=1,column=0,columnspan=2)
        #pdb file button
        self.pdbvar  = Tkinter.IntVar()
        
        
        
        ### pdbfile group####
        self.pdbGroup = Pmw.Group(self.frame,tag_text="AttachFile")
        self.pdbGroup.pack(side='left',fill='both', expand=1, padx=1, pady=1)
        
        f1 = Tkinter.Frame(self.pdbGroup.interior())
        f1.pack(side='top', fill='both', expand=1)
        self.pdbGroup.grid(row=3,column=0,columnspan=2,sticky="nesw")
        self.pdbfileadd= kbScrolledListBox(f1,items=[],listbox_exportselection=0,listbox_height=1,listbox_width=85)
        self.pdbfileadd.pack(expand=1, fill='both')
        self.pdbfileadd.grid(sticky='nw',row=0)
        self.deletefilebutton=Tkinter.Button(f1,text='Delete Selected',     
                               command=self.delete_selected,state="disabled",width=40)
        self.deletefilebutton.pack(side='left', expand=1,fill='both')
        self.deletefilebutton.grid(sticky='nw',row=1,column=0,columnspan=1)
        self.attachmorebutton=Tkinter.Button(f1,text='Attach File ..',     
                               command=self.attach_more,width=40)
        self.attachmorebutton.pack(side='left', expand=1,fill='both')
        self.attachmorebutton.grid(sticky='ne',row=1,columnspan=2)
        #email-entry
        self.email_entrylab=Tkinter.Label(self.frame,text="Enter your email address(optional:to recieve information about submitted bug)")
        self.email_entrylab.pack(side='top', fill='both', expand=1)
        self.email_entrylab.grid(sticky='nw',row=4,column=0)
        self.email_entryvar = Tkinter.StringVar()
        self.email_entry=Tkinter.Entry(self.frame,textvariable=self.email_entryvar)
        
        self.email_entry.pack(side='top', fill='both', expand=1)
        self.email_entry.grid(sticky='nesw',row=5,column=0,columnspan=2)
        
        
        
        ###############upload,dismiss buttons################
        self.uploadbutton=Tkinter.Button(self.frame,text='UpLoad Bug Report',     
                               command=self.show_upload_page,width=40)
        self.uploadbutton.pack(side='left', expand=1,fill='both')
        self.uploadbutton.grid(sticky='nw',row=6,column=0,columnspan=1)
        self.dismiss=Tkinter.Button(self.frame,text='DISMISS',
                            command=self.Ok,width=37)
        self.dismiss.pack( expand=1,fill='both')
        self.dismiss.grid(sticky='ne',row=6,columnspan=2)
        pdb_group=self.pdbGroup
        pdb_group.expand()
        shortdesc_tx=self.shortdesctext
        shortdesc_tx.configure(text_height=2)
        desc_tx=self.desctext
        desc_tx.configure(text_height=8)        
    
    def Ok(self, event=None):
        self.hide()


    def show(self, event=None):
        #self.panel.deiconify()
        self.buildPanel()

    def hide(self, event=None):
        #self.panel.withdraw()
        self.panel.destroy()
    
            
    def attach_more(self):
        """for attching files"""
        pdb_addw=self.pdbfileadd
        pdb_delw=self.deletefilebutton
        
        Filename = tkFileDialog.askopenfilename(filetypes=[('all files','*')],title="ADDFile")
        if Filename:
            inputfilename = os.path.abspath(Filename)
            files=pdb_addw.get()
            files=list(files)
            files.append(inputfilename)
            pdb_addw.setlist(files)
            pdb_addw.configure(listbox_height=len(files))
            pdb_delw.configure(state="active")
            
        else:
            if len(pdb_addw.get())==0:
                 pdb_delw.configure(state="disabled")    
            pdb_addw.setlist(pdb_addw.get())
        VarDict['attachfile'] =  pdb_addw.get()    
    
    def delete_selected(self):
        """deletes selected files"""
        pdb_addw=self.pdbfileadd
        pdb_delw=self.deletefilebutton
        files=pdb_addw.get()
        lfiles=list(files)
        selected_files=pdb_addw.getcurselection()
        for s in list(selected_files):
            if s in lfiles:
                lfiles.remove(s)
        pdb_addw.setlist(lfiles)        
        pdb_addw.configure(listbox_height=len(lfiles))        
        if len(pdb_addw.get())==0:
            pdb_delw.configure(state="disabled")    
        VarDict['attachfile'] =  pdb_addw.get()
    def get_description(self):
         
        desc_w =self.desctext
        desc_text = self.desctext.get()
        shortdesc_w = self.shortdesctext
        shortdesc_text =shortdesc_w.get()
        
        VarDict['desc_text'] = desc_text
        VarDict['shortdesc_text'] = shortdesc_text
        email_ent =  self.email_entry.get()
        VarDict['email_recipient'] = email_ent
        
    #checking validity of email address
    def validateEmail(self,email):

	        if len(email) > 7:
		        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
			        return 1
	        return 0
    def show_upload_page(self):
        self.get_description()
         
        sumcont = VarDict['shortdesc_text']
        
        fulldesc = VarDict['desc_text']
        
        desccont = fulldesc
        if len(sumcont)<=1 or len(desccont)<=1:
            import tkMessageBox
            ok = tkMessageBox.askokcancel("Input","Please enter summary and description")
            return
        from mglutil.TestUtil import BugReport
        if VarDict.has_key('attachfile'):
            upfile = VarDict['attachfile']
        else:
            upfile=[]
        
        BR = BugReport.BugReportCommand("Vision")
        if self.validateEmail(VarDict['email_recipient']):
            idnum = BR.showuploadpage_cb(sumcont,desccont,upfile,email_ent=VarDict['email_recipient'])
        else:
            idnum = BR.showuploadpage_cb(sumcont,desccont,upfile,email_ent="")
        
        self.Ok() 
        
        
        
        
        ####################################
        #Tk message Box
        ####################################
         
        root = Tk()
        t  = Text(root)
        t.pack()

        def openHLink(event):
            start, end = t.tag_prevrange("hlink",
                               t.index("@%s,%s" % (event.x, event.y)))
            webbrowser.open_new('%s' %t.get(start, end))
            #print "Going to %s..." % t.get(start, end)

        t.tag_configure("hlink", foreground='blue', underline=1)
        t.tag_bind("hlink", "<Control-Button-1>", openHLink)
        t.insert(END, "BugReport has been Submiited Successfully\n")
        t.insert(END, "BugId is %s" %idnum)
        t.insert(END,"\nYou can visit Bug at\n")
        t.insert(END,"http://mgldev.scripps.edu/bugs/show_bug.cgi?id=%i" %int(idnum),"hlink")
        t.insert(END,"\nControl-click on the link to visit this page\n")
        t.insert(END,"\n")
        

        
