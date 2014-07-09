import os, weakref
import Tkinter, Pmw

from Scenario2.gui.Tk.clipboard import ClipboardGUI
from Scenario2.sequenceAnimator import SequenceAnimator
from Scenario2.gui.Tk.sequenceAnimator import SequenceAnimatorGUI
from Scenario2 import _clipboard, _MAATargets


from DejaVu.scenarioInterface.animationGUI import orientationGUI

from DejaVu.scenarioInterface.animationPanels import AnimationPanel, ShowHideGeomPanel

from Pmv.scenarioInterface.animations import PmvColorObjectMAA, PartialFadeMolGeomsMAA,colorCmds
from Pmv.scenarioInterface.GeomChooser import PmvGeomChooser, PmvSetChooser
from DejaVu.GeomChooser import GeomChooser

from mglutil.gui.BasicWidgets.Tk.colorWidgets import ColorChooser
from mglutil.util.callback import CallbackFunction
from Pmv.moleculeViewer import MoleculeViewer




from DejaVu.scenarioInterface.animationGUI import SESp_MAAEditor

class SESpOpSet_MAAEditor(SESp_MAAEditor):
    """
    Editor providing speed, easeInOut,sortPoly , Opacity and Pmv set chooser parameters
    """
    def __init__(self, master=None, title='Partial Fade Editor',
                 buttons=['OK', 'Preview', 'Cancel'],
                 defaultButton='OK', speedDict=None, pmv=None):
        
        self.pmv = pmv
        self.fadeType = "in"
        self.destOpacVal = 1.0
        SESp_MAAEditor.__init__(
            self, master=master, title=title, buttons=buttons,
            defaultButton=defaultButton, speedDict=speedDict)
        


    def populateForm(self):
        """
        add set chooser
        """
        SESp_MAAEditor.populateForm(self)
        frame = self.dialog.interior()
        grp = Pmw.Group(frame, tag_text='Fade options')
        parent = grp.interior()
        self.fadeTypeW = ft = Pmw.RadioSelect(
            parent, labelpos="w", label_text="Fade:",
            selectmode='single', orient='horizontal',
            buttontype='radiobutton',
            command=self.setFadeType_cb)
        for text in ['in', 'out']:
            ft.add(text)
        ft.setvalue(self.fadeType)
        ft.pack(side = 'left', anchor = 'w', fill = 'x',
                expand = 1, padx = 8, pady = 8)
        self.destOpac = Pmw.Counter(parent, labelpos = 'w',
                                label_text = 'Final opacity:',
                                entry_width = 8, entryfield_value = self.destOpacVal,
                                 datatype = {'counter' : 'real'}, increment = 0.1,
                                entryfield_validate = {'validator' : 'real',
                                                       'min' : 0.0 , 'max':1.0})
        self.destOpac.pack(side = 'top',  anchor = 'w', fill = 'x', expand = 1, padx = 8, pady = 8)
        grp.pack(side='top', fill='x', expand=1 )
        
        self.setChooser = PmvSetChooser(frame, self.pmv,
                                        title = "select a set:",
                                        mode="multiple")
        self.setChooser.pack(side = "top", expand=1, fill="both")
        self.balloon.bind(self.setChooser.widget, "fade in/out parts of a molecule for geometries\nwhere the atom centers correspond to the geometry\nvertices (cpk, sticks, balls, bonded)" )


    def setFadeType_cb(self, fadeType="in", val = None):
        entry = self.destOpac._counterEntry
        if fadeType == "in":
            entry.delete(0, 'end')
            if val == None: val = 1.0
            entry.insert(0, val)
        else:
            entry.delete(0, 'end')
            if val == None: val = 0.0
            entry.insert(0, val)
        self.fadeType = fadeType

    def setValues(self, **kw):
        """
        take a dictionary of p <arameterName:parameterValues set the editor
        to these values
        """
        SESp_MAAEditor.setValues(self, **kw)
        if self.maa:
            fade = "in"
            if hasattr(self.maa, 'fade'):
                fade = self.maa.fade
            self.fadeTypeW.setvalue(fade)
            destVal = None
            if hasattr(self.maa, 'destValue'):
                destVal = self.maa.destValue
            self.setFadeType_cb(fadeType=fade, val = destVal)
            
    
    def getValues(self):
        """
        return a dictionary of parameterName:parameterValues
        """
        values = SESp_MAAEditor.getValues(self)
        values['nodes'] = self.setChooser.getNodes()
        self.destOpacVal = values['destValue'] = float(self.destOpac.get())
        values['fade'] = self.fadeType
        return values
    
        
class colorsMAAGUI(AnimationPanel):
    
    """ Adds color effects buttons."""
    
    def __init__(self, pmv ,master=None):
        
        assert isinstance(pmv, MoleculeViewer)
        vi = pmv.GUI.VIEWER
        self.pmv = pmv
        
        AnimationPanel.__init__(self, vi, 'pmv.GUI.VIEWER', master)
        gc = self.geomChooser = PmvGeomChooser(pmv, root=self.geomChooserG.interior(),
                                               showAll=False, refreshButton=True, showAllButton=True,
                                               command=self.onSelect_cb)
        gc.pack(side='top', fill='both', expand=1, anchor="w")
        # select 'All' entry by default
        gc.chooserW.lb.select_set(0)
        self.selectedGeom = [ [0], [pmv.GUI.VIEWER.rootObject]]

        # add action creating buttons

        parent = self.makeActionsG.interior()

        self.colorClips = {}

        for lastRow, txt in enumerate(colorCmds.keys()):
            #if txt == "choose color": continue
            cb = CallbackFunction(self.makeMAA, PmvColorObjectMAA, (), {'pmv':pmv, 'colortype':txt})
            w = Tkinter.Button(parent, text=txt, command=cb)
            w.grid(column=0, row=lastRow, columnspan = 2, sticky='ew')
            w.bind('<Button-3>', CallbackFunction( self.showMaaEditor_cb, PmvColorObjectMAA, (), {'pmv':pmv, 'colortype':txt}) )
        
        self.lastRow = lastRow


    def getSelectedGeoms(self):
        gc = self.geomChooser
        geometries = gc.get()
        kw = {}
        if len(geometries):
            # get the name of the currently selected geometry
            en = gc.chooserW.entries
            ind = gc.chooserW.getInd()[0]
            objname= en[ind][0].strip() # remove leading blanks
            # build a name
            gparent = geometries[0].parent
            if gparent is not None and gparent.name != "root":
                objname = gparent.name + "|" + objname
            kw['objectName'] = objname
            if hasattr(gc, "getNodes"):
                kw['nodes'] = gc.getNodes()
        return geometries, kw
            

        
    def showMaaEditor_cb(self, maaClass, args, kw, event=None):
        """
        open maa editor, create maa based on specified options
        """
        geometries, geomkw = self.getSelectedGeoms()
        if len(geometries)==0:
            from tkMessageBox import showwarning
            showwarning("Warning", 'No geometry selected',
                        parent = self.geomChooser.root)
            return
        kw.update(geomkw)
        args = (geometries, )
        maa = maaClass( *args, **kw )
        if not len(maa.actors):
            return
        st = self.editMAA_cb(maa)
        if st == "OK":
                self.makeMAAButton(maa)


    def makeMAA(self, maaClass, args, kw, event=None):
        """
        callback for action creating buttons
        """

        gc = self.geomChooser
        geometries = gc.get()

        if len(geometries)==0:
            from tkMessageBox import showwarning
            showwarning("Warning", 'No geometry selected',
                        parent = gc.root)
            return

        # get the name of the currently selected geometry
        en = gc.chooserW.entries
        ind = gc.chooserW.getInd()[0]
        objname= en[ind][0].strip() # remove leading blanks
        # build a name
        gparent = geometries[0].parent
        if gparent is not None and gparent.name != "root":
            objname = gparent.name + "|" + objname
        kw['objectName'] = objname
        if hasattr(gc, "getNodes"):
            kw['nodes'] = gc.getNodes()
        args = (geometries, )
        maa = maaClass( *args, **kw )
        if len(maa.actors):
            self.makeMAAButton(maa)


    def onSelect_cb(self, event = None):
        self.selectedGeom = [self.geomChooser.chooserW.getInd(),
                             self.geomChooser.chooserW.get()]

            


class movePmvObjectsMAAGUI(ShowHideGeomPanel):
    
    def __init__(self, pmv, master=None):
        
        assert isinstance(pmv, MoleculeViewer)
        from Pmv.GeomFilter import GeomFilter
        self.gf = GeomFilter(pmv)
        filterFunction = self.gf.filter
        
        vi = pmv.GUI.VIEWER

        kw = {'showAll':False, 'filterFunction':filterFunction,
              'refreshButton':True, 'showAllButton': True}
        gcOpt = [ (), kw ]
        ShowHideGeomPanel.__init__(
            self, vi, 'pmv.GUI.VIEWER', GeomChooser, gcOpt, master=master)

        self.lastRow += 1
        # select 'All' entry by default
        gc = self.geomChooser
        gc.chooserW.lb.select_set(0)
        self.selectedGeom = [ [0], [vi.rootObject]]

        frame = self.effectsContainer
        # partial fade in button
        cb = CallbackFunction(self.makeMAA, PartialFadeMolGeomsMAA,
                              (gc,), {'pmv':pmv})
        parent = self.makeActionsG.interior()
        w = self.pfadeB = Tkinter.Button(parent, text='Partial fade',
                                         command=cb)
        w.grid(column=0, row=self.lastRow, sticky='ew')
        w.bind('<Button-3>', CallbackFunction( self.showMaaEditor_cb, PartialFadeMolGeomsMAA, (), {'pmv':pmv}))


import tkFileDialog

class AnimationNotebook:

    def __init__(self, pmv, master=None):

        """
        Create a Notebook widget. Pages contain different animation effects such
        as Fly In/Out , Fade In/Out, Rotate object, Color effects.
        There are a Clipping board and Sequence animator pages.
        """
        self.master = master
        if master is None:
            self.master = master = Tkinter.Toplevel()
            self.ownsMaster = True
        else:
            self.ownsMaster = False

        self.pmv = pmv
        vi = self.viewer = pmv.GUI.VIEWER
        
        sf = Pmw.ScrolledFrame(self.master)
        sf.pack(fill = 'both', expand = 1)
        self.master = sf.interior()        

        # create menu bar
        self.mBar = Tkinter.Frame(self.master, relief=Tkinter.RAISED, borderwidth=2)
        self.menuButtons = {}
        File_button = Tkinter.Menubutton(self.mBar, text='File', underline=0)
        File_button.menu = Tkinter.Menu(File_button)
        File_button['menu'] = File_button.menu
        File_button.pack(side=Tkinter.LEFT, padx="1m")
        File_button.menu.add_command(label='Load animation script', underline=0,
                                     #accelerator='(Ctrl-o)',
                                     command=self.loadAnimation)
##         File_button.menu.add_command(label='Save animation script', underline=0,
##                                      #accelerator="(Ctrl-s)",
##                                      command=self.saveAnimation)
        File_button.menu.add_command(label='Load Snapshots', underline=0,
                                     #accelerator='(Ctrl-o)',
                                     command=self.loadSnapshots)
##         File_button.menu.add_command(label='Save Snapshots', underline=0,
##                                      #accelerator="(Ctrl-s)",
##                                      command=self.saveSnapshots)
        
        self.mBar.pack(side='top',fill=Tkinter.X)
        # create notebook widget:
        self.showHidePanel = None
        self.colorsGUI = None
        nb = self.notebook = Pmw.NoteBook(self.master, raisecommand = self.selectPage_cb)

        # add "Snapshot" page
        self.orientP = nb.add("Snapshots")
        self.orientGUI = orientationGUI(vi, 'viewer', master=self.orientP)
        self.orientGUI._animNB = weakref.ref(self)

        # add "Move" page ( add fly and fade, show/hide, rotate effects):
        panel = nb.add("Move")
        self.showHidePanel = movePmvObjectsMAAGUI(pmv, master=panel)
        self.showHidePanel._animNB = weakref.ref(self)
        
        # add "Colors" page
        panel = nb.add("Colors")
        self.colorsGUI = colorsMAAGUI(pmv, master=panel)
        self.colorsGUI._animNB = weakref.ref(self)
        
        # add clipboard
        #self.clipbP = nb.add("Clipboard")
        #cbgui = self.clipboardGUI = ClipboardGUI(_clipboard, master=self.clipbP)
        #_MAATargets.addAnimator('Clipboard',  _clipboard, self.addMaaToClipboard)
        #cbgui.master.withdraw()
        #cbgui.master.protocol('WM_DELETE_WINDOW', cbgui.master.withdraw )
        
        # add sequence animator page
        self.sequenceP = nb.add("Sequence Anim.")
        self.addSequenceAnim()
        
        nb.pack(padx=5, pady = 5, fill=Tkinter.BOTH, expand=1)
        nb.setnaturalsize()
        
        self.balloon = Pmw.Balloon(self.master)
        self.loadedMaas = {}        


    def addSequenceAnim(self):
        self.seqAnim = SequenceAnimator()
        self.seqAnim._animNB = weakref.ref(self)
        _MAATargets.addAnimator('animation', self.seqAnim, self.seqAnim.addMaa_cb)
        self.seqAnimGUI = SequenceAnimatorGUI(self.seqAnim,  master=self.sequenceP)#, master = frame)


    def addMaaToClipboard(self, clipboard, maa):
        _clipboard.addMaa(maa)


    def selectPage_cb(self, pagename):
        """Called when a new page is selected. Updates the Geometry Chooser widgets
        on 'Move' and 'Colors' pages."""
        gc = None
        pageGUI = None
        if pagename == "Move":
            if self.showHidePanel:
                pageGUI = self.showHidePanel
                gc = pageGUI.geomChooser
        elif pagename == "Colors":
            if self.colorsGUI:
                pageGUI = self.colorsGUI
                gc = pageGUI.geomChooser
        if gc is not None:
            gc.updateList()
            if pageGUI.selectedGeom:
                gind, geom = pageGUI.selectedGeom
                if len(gind):
                    n = gind[0]
                    if len(gc.geomList)>= n+1 and geom == gc.geomList[n][1]:
                        gc.chooserW.clearSelection()
                        gc.chooserW.selectItem(n)
                    else:
                       gc.chooserW.clearSelection()


    def saveAnimation(self, file = None):
        if not len(self.seqAnim.maas):
            return
        ans, filename, savesession = self.openSaveDialog()
        if ans == "OK":
            #filename = entry.get()
            if filename:
                # save animation to file filename_animation.py
                lines = """import sys\n"""
                lines += """viewer=pmv.GUI.VIEWER \n"""
                lines += self.seqAnim.getMAASourceCode("animator")
                f = open(filename + "_animation.py", 'w')
                f.writelines(lines)
                f.close()
                # save current Pmv session
                if savesession:
                    self.pmv.saveSession(filename+"_session.psf")


    def openSaveDialog(self, title = 'Save Animation', fileext = "_animation"):
        dialog = Pmw.Dialog(self.master, buttons = ('OK','Cancel'),
                            defaultbutton = 'OK', title=title)
        dialog.withdraw()
        savesession = Tkinter.IntVar()
        savesession.set(1)
        frame = dialog.interior()
        checkb = Tkinter.Checkbutton(frame, text = "Save Pmv Session",
                                     variable=savesession)
        checkb.pack(side='top', anchor='w')
        
        entry = Pmw.EntryField(frame, label_text="File name:", labelpos='w')
        entry.pack(expand = 1, fill = 'both', padx = 4, pady = 4, side='left')
        self.balloon.bind(entry, "Enter a filename.\nfilename%s.py and filename_session.psf\nwill be created" % (fileext,))
        
        button = Tkinter.Button(frame, text="BROWSE",
                                command=CallbackFunction(self.saveFileDialog_cb,
                                                         entry, fileext))
        button.pack(side='left')
        
        ans = dialog.activate(geometry = '+%d+%d' % (self.master.winfo_x()+300, self.master.winfo_y()+100) )
        filename = entry.get()
        return ans, filename, savesession.get()
                


    def saveFileDialog_cb(self, entry, fileext):
        """Opens a file browser dialog, sets the specified entry to selected filename,
        (stripped of the '_animation.py' extension) """
        
        fname = None
        file = tkFileDialog.asksaveasfilename(parent = self.master,
                                              initialdir = '.',
                          filetypes=[('animation', '*%s.py'% fileext), ('all', '*')],
                          initialfile = "my%s.py" % fileext, title='Save Animation')
        if file:
            fname = os.path.splitext(file)[0].split(fileext)[0] 
            entry.setentry(fname)
        return fname
    

    def loadAnimation(self, file = None):
        """Loads saved animation to the sequence animator """
        ans, animfile, sessionfile, loadsession = self.openLoadDialog()
        if ans == "OK":
            #animfile = entry1.get()
            #sessionfile = entry2.get()
            if animfile:
                if loadsession and sessionfile:
                    if os.path.exists(sessionfile):
                        try:
                            self.pmv.readSourceMolecule(sessionfile)
                        except:
                            import tkMessageBox
                            tkMessageBox.showwarning('Load Session Warning', "Load Session %s  Failed" % sessionfile)
                            import traceback
                            traceback.print_exc()
                pmv = self.pmv
                lastAnimationFrame = self.seqAnim.endFrame
                if lastAnimationFrame > 0: lastAnimationFrame += 1
                glob = {'pmv' : pmv, 'offset':lastAnimationFrame,
                        'animator':self.seqAnim}
                execfile( animfile, glob)
                self.notebook.selectpage("Sequence Anim.")


    def openLoadDialog(self, title = 'Save Animation', fileext = "_animation"):
        dialog = Pmw.Dialog(self.master, buttons = ('OK','Cancel'),
                            defaultbutton = 'OK', title=title)
        dialog.withdraw()

        frame = dialog.interior()
        entry1 = Pmw.EntryField(frame, label_text="Animation file:", labelpos='w')
        entry1.grid(row = 0, column=0, padx = 5, pady = 5, sticky='w')

        button1 = Tkinter.Button(frame, text="BROWSE")
        button1.grid(row = 0, column=1, padx = 5, pady = 5, sticky='w')
        
        loadsession = Tkinter.IntVar()
        loadsession.set(1)
        checkb = Tkinter.Checkbutton(frame, text = "Load Pmv Session",
                                     variable=loadsession)
        checkb.grid(row = 1, column=0, padx = 5, pady = 5, sticky='w')
        
        entry2 = Pmw.EntryField(frame, label_text="Session file:", labelpos='w')
        entry2.grid(row = 2, column=0, padx = 5, pady = 5, sticky='w')

        button2 = Tkinter.Button(frame, text="BROWSE")
        button2.grid(row = 2, column=1, padx = 5, pady = 5, sticky='w')

        button1.configure(command=CallbackFunction(self.openFileDialog_cb, entry1,
                                                   entry2, title, fileext))
        button2.configure(command=CallbackFunction(self.openFileDialog_cb, entry2,
                                                   entry1, title, fileext))

        self.balloon.bind(entry1, "Enter path to the animation file.")
        self.balloon.bind(entry2, "Enter path to the Pmv session file.")
        
        ans = dialog.activate(geometry = '+%d+%d' % (self.master.winfo_x()+300, self.master.winfo_y()+100) )
        animfile = entry1.get()
        sessionfile = entry2.get()
        return ans, animfile, sessionfile, loadsession.get()
    
        

    def openFileDialog_cb(self, entry1, entry2, title='Load Animation', fileext="_animation"):
        """Opens a file browser dialog for selecting either an animation
        or a Pmv session file(depending on the type of entry1 argument),
        tries to find a corresponding session (or animation) file and
        sets the entries to the file names. """
        
        file2 = None
        if entry1.cget('label_text') == 'Animation file:':
            file1 = tkFileDialog.askopenfilename(parent = self.master,
                            initialdir = '.', title="%s" % (title,),
                            filetypes=[('animation', '*%s.py' % (fileext,)), ('all', '*')] )
            if file1:
                fname = os.path.splitext(file1)[0].split(fileext)[0] 
                entry1.setentry(file1)
                file2 = fname+"_session.psf"
        else:
            file1 = tkFileDialog.askopenfilename(parent = self.master,
                            initialdir = '.', title='Load Pmv Session',
                            filetypes=[('Pmv session', '*_session.psf'), ('all', '*')] )
            if file1:
                fname = os.path.splitext(file1)[0].split("_session")[0]  
                entry1.setentry(file1)
                file2 = fname+"%s.py" % (fileext,)
        if file2 is not None and os.path.exists(file2):
                entry2.setentry(file2)

    def saveAniMolSession(self, file):
        """Saves all animation actions from 'Move', 'Colors' and 'Orientations'
        pages to a file. Saves Animation in Seqence Anim."""

        snapshots = self.orientGUI.getSavedMaas()
        allmaas = len(snapshots)
        for pagegui in [self.showHidePanel, self.colorsGUI]:
            allmaas += len(pagegui.maas)
        
        if allmaas == 0:
            #import tkMessageBox
            #tkMessageBox.showwarning("Custom Animation warning", "No actions to save")
            return 0
        firstlines = """import sys \n"""
        #firstlines += """maas = []\n"""
        firstlines += """showwarning = True\n"""
        firstlines += """viewer=pmv.GUI.VIEWER\n"""
        firstlines += """from PIL import Image\n"""
        firstlines += """from numpy import array\n"""
        tab =  4*" "
        seqmaas = []
        # seqence animator info [ [None, maaPosition], ...] 
        # None will be replaced by maa index in
        # the list of all saved actions :
        seqAnim = [[None, maa[1], 0] for maa in self.seqAnim.maas]
        import os
        fname, ext = os.path.splitext(file)
        ext = ".py"
        i = 0
        f = None
        lines =""" """
        for pagegui, funcname in [(self.showHidePanel, "loadMoveAction"),
                                  (self.colorsGUI, "loadColorAction")]:
            maas = pagegui.maas
            for maa in maas:
                if hasattr(maa, "getSourceCode"):
                    maasrc = maa.getSourceCode("maa%d"%i)
                    if len(maasrc):
                        lines = firstlines
                        lines += """maa%d = None\n"""%i
                        lines += maasrc + """\n"""
                        lines += """if maa%d is not None and len(maa%d.actors)> 0: \n""" % (i, i)
                        lines += tab+ """AniMol.%s(maa%d)\n""" % (funcname, i)
                        lines += tab+ """AniMol.loadedMaas[%d] = maa%d\n""" % (i,i)
                        for ii , _maa in enumerate(self.seqAnim.maas):
                            if maa == _maa[0]:
                                seqAnim[ii][0] = i
                                seqAnim[ii][2] = maa.startOffset
                        if f is not None: f.close()
                        i = i+1
                        f = open(fname+str(i)+ext, 'w')
                        f.writelines(lines)

        # save snapshots:
        
        import numpy
        for maa in snapshots:
            #lines += """\n"""
            maasrc = maa.getSourceCode("maa%d"%i)
            if len(maasrc):
                lines = firstlines
                lines += maasrc + """\n"""
                # tab in needed because the code for snapshot[i] is created inside
                # "if" statement
                #(see DejaVuscenarioInterface.animations.py/SnapshotMAAGroup.getSourceCode() )
                #lines += tab+ """maas.append(maa%d)\n""" % i
                imstr = maa.ims.tostring()
                imarr = numpy.fromstring( imstr, 'B').tolist()
                #lines +=  tab+ """imstr%d = '%s'\n""" % (i, imstr)
                lines +=  tab+ """imstr%d = %s\n""" % (i, imarr)
                #lines +=  tab+ """maa%d.ims = Image.fromstring('RGB', (50, 50), imstr%d)\n"""% (i,i)
                lines +=  tab+ """maa%d.ims = Image.fromstring('RGB', (50, 50), array(imstr%d, 'B').tostring() )\n"""% (i,i)
                lines +=  tab+ """AniMol.loadSnapshot(maa%d)\n""" % (i,)
                lines += tab+ """AniMol.loadedMaas[%d] = maa%d\n""" % (i,i)
                for ii , _maa in enumerate(self.seqAnim.maas):
                    if maa == _maa[0]:
                        seqAnim[ii][0] = i
                i = i+1
                if f is not None: f.close()
                f = open(fname+str(i)+ext, 'w')
                f.writelines(lines)

        if len(seqAnim):
           lines = """## Add maas to the Sequence Animator\n"""
           for ind, pos, offset in seqAnim:
               if ind is not None:
                   lines += """maa%d = AniMol.loadedMaas.get(%d)\n""" % (ind, ind)
                   lines += """if maa%d is not None and len(maa%d.actors)> 0: \n""" % (ind, ind)
                   lines += tab + """AniMol.seqAnim.addMAAat(maa%d, offset+%d, check=False)\n""" % (ind, pos)
                   if offset != 0:
                      lines += tab + """maa%d.startOffset = %d\n"""%(ind, offset)
           #f = open(file, 'w')
           f.writelines(lines)
           
        if f is not None: f.close()
        return i



    def loadMoveAction(self, maa):
        # this function is called from the animation session file
        # to load a restored maa onto the "Move" page
        self.showHidePanel.makeMAAButton(maa)
        

    def loadColorAction(self, maa):
        # this function is called from the animation session file
        # to load a restored maa onto the "Colors" page
        self.colorsGUI.makeMAAButton(maa)


    def loadSnapshot(self, maagroup):
        # this function is called from the animation session file
        # to load a restored maa onto the "Snapshot" page
        gui = self.orientGUI
        gui.nbOrients += 1
        if maagroup.name and maagroup.name.find("snapshot") == 0:
            maagroup.name = 'snapshot%d'% gui.nbOrients
        if not hasattr(maagroup, 'ims'):
            if maagroup.rendering:
                setRendering(maagroup.orientMaa.viewer, maagroup.orientMaa.rendering)
                maagroup.setValuesAt(maagroup.lastPosition)
        gui.saveMAA(maagroup)


    def loadAniMolSession(self, animfile, numfiles=None):
        """Loads saved animation to the sequence animator """
        if not animfile:return
        pmv = self.pmv
        lastAnimationFrame = self.seqAnim.endFrame
        if lastAnimationFrame > 0: lastAnimationFrame += 1
        glob = {'pmv' : pmv, 'offset':lastAnimationFrame,
                'AniMol':self}
        if numfiles==None and animfile=="animation.py":
            execfile(animfile, glob)
        elif numfiles:
            import os
            #from time import time
            self.loadedMaas = {}
            for i in range(1, numfiles+1):
                file = animfile+str(i)+".py"
                #print "loadAniMolSession:", file,
                if os.path.exists(file):
                    #print "executing ...." ,
                    #t1 = time()
                    execfile(file, glob)
                    #print "done", time() - t1 


    def saveSnapshots(self, file=None, savesession=True):
        """Saves animations from snapshots page to a file"""
        maas = self.orientGUI.getSavedMaas()
        if not len(maas):
            import tkMessageBox
            tkMessageBox.showwarning("Custom Animation warning", "No snapshots to save")
            return
        
        if file is None:
            ans, filename, savesession = self.openSaveDialog(title = 'Save Animation Clips',
                                                fileext = "_snapshots")
            if ans != "OK": return
            
            if filename:
                file = filename+"_snapshots.py"
            else: return
        f = open(file, 'w')
        lines = """import sys \n"""
        lines += """maas = []\n"""
        lines += """showwarning = True\n"""
        lines +=  """viewer=pmv.GUI.VIEWER \n"""
        lines +=  """from PIL import Image\n"""
        lines += """from numpy import array\n"""
        f.writelines(lines)
        tab =  4*" "
        i = 0
        import numpy
        for i, maagroup in enumerate(maas):
            lines = """\n"""
            maasrc = maagroup.getSourceCode("snapshot%d"%i)
            if len(maasrc):
                lines += maasrc + """\n"""
                lines += tab+ """maas.append(snapshot%d)\n""" % i
                imstr = maagroup.ims.tostring()
                imarr = numpy.fromstring( imstr, 'B').tolist()
                lines +=  tab+ """imstr%d = %s\n""" % (i, imarr)
                lines +=  tab+ """snapshot%d.ims = Image.fromstring('RGB', (50, 50), array(imstr%d, 'B').tostring() )\n"""% (i,i)
                f.writelines(lines)

        #f.writelines(lines)
        f.close()
        if savesession:
            self.pmv.saveSession(filename+"_session.psf")
        


    def loadSnapshots(self, animfile = None, sessionfile=None, loadsession=True):
        """ Loads saved animation clips to the Clipboard."""
        if animfile is None:
            ans, animfile, sessionfile, loadsession = self.openLoadDialog(title='Load Snapshots', fileext="_snapshots")
            if ans != "OK": return

        if animfile:
            if loadsession and sessionfile:
                if os.path.exists(sessionfile):
                    try:
                        self.pmv.readSourceMolecule(sessionfile)
                    except:
                        import tkMessageBox
                        tkMessageBox.showwarning('Load Session Warning', "Load Session %s  Failed" % sessionfile)
                        import traceback
                        traceback.print_exc()
            #lastAnimationFrame = self.seqAnim.endFrame
            #if lastAnimationFrame > 0: lastAnimationFrame += 1
            glob = {'pmv' : self.pmv} #, 'offset': lastAnimationFrame, 'animator':self.seqAnim}
            filelocals = {}
            execfile(animfile, glob, filelocals)
            maas = filelocals.get("maas")
            #print "maas in load:", maas
            if maas is not None:
                from DejaVu.states import setRendering
                for maagroup in maas:
                    gui = self.orientGUI
                    gui.nbOrients += 1
                    if maagroup.name and maagroup.name.find("snapshot") == 0:
                        maagroup.name = 'snapshot%d'% gui.nbOrients
                    if not hasattr(maagroup, 'ims'):
                        if maagroup.rendering:
                            setRendering(maagroup.orientMaa.viewer, maagroup.orientMaa.rendering)
                        maagroup.setValuesAt(maagroup.lastPosition)
                    gui.saveMAA(maagroup)
                #self.notebook.selectpage("Snapshots")


    

    

    

   

