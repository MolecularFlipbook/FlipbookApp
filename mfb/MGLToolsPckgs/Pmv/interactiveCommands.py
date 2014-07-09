#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/interactiveCommands.py,v 1.33.2.1 2011/10/07 18:21:08 sanner Exp $
#
# $Id: interactiveCommands.py,v 1.33.2.1 2011/10/07 18:21:08 sanner Exp $
#

from MolKit.molecule import Atom, Molecule
from MolKit.protein import Protein, Residue, Chain
from MolKit.tree import TreeNode
from Pmv.mvCommand import MVCommand, MVICOM
from Pmv.picker import AtomPicker
from ViewerFramework.VFCommand import CommandGUI, ICOM, ActiveObject, Command
##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
import Tkinter, Pmw, types, string, os


class MVSetInteractiveCmd(MVCommand):


    def getLevelName(self, level ):
        if level==Atom: level = 'Atom'
        elif level==Residue: level = 'Residue'
        elif level==Chain: level = 'Chain'
        elif level==Molecule or isinstance(newValue,Protein):
            level = 'Molecule'
        return level
    
       
    def setupUndoBefore(self, cmd, modifier=None, mode=None):
        if mode==None or mode=='pick':
            cmdDict = self.vf.ICmdCaller.commands.value
        else:
            cmdDict = self.vf.ICmdCaller.commands2.value

        cmd = cmdDict[modifier]
        self.addUndoCall( (cmd, modifier, mode), {}, self.name )


    def doit(self, cmd, modifier=None, mode=None):
        icom = self.vf.ICmdCaller
        icom.setCommands(cmd, modifier, mode)
        
        
    def __call__(self, cmd, modifier=None, mode=None, **kw):
        """None <- setICOM(cmd, modifier, **kw)
           cmd: command
           modifier: name of the modifier ('Shift_L', 'Control_L', 'Alt_L' ...)
           mode can be None, 'pick' or 'drag select'
           """
        if cmd is not None:
            assert isinstance(cmd, ICOM)
        kw['modifier'] = modifier
        kw['mode'] = mode
        apply( self.doitWrapper, (cmd, ), kw )


    def command_cb(self, val):
        cmd = self.vf.commands[val]
        apply( self.doitWrapper, (cmd, None), {} )


    def level_cb(self, val):
        apply( self.vf.setIcomLevel, (eval(val),), {} )
       


def getICOMBar(viewer):
    # selection command use buttons in a selectionBar
    # this function creates the bar if it does not exist yet else returns it
    if not viewer.GUI.menuBars.has_key('icomBar'):
##         viewer.GUI.addMenuBar('icomBar',
##                               {'borderwidth':2, 'relief':'raised'},
##                               {'side':'top', 'expand':1, 'fill':'x'})
        viewer.GUI.addMenuBar('icomBar',
                    {'borderframe':0, 'horizscrollbar_width':7,
                     'vscrollmode':'none', 'frame_relief':'groove',
                     'frame_borderwidth':2,},
#                              {'frame_borderwidth':2,
#                               'frame_relief':'raised',
#                               'horizscrollbar_width':7,
#                               'vscrollmode':'none',
#                               'usehullsize':1, 'hull_width':300,
#                               'hull_height':53},
                              {'side':'top', 'expand':1, 'fill':'x'})
    return viewer.GUI.menuBars['icomBar']


from DejaVu.colorTool import TkColor

from mglutil.gui.BasicWidgets.Tk.customizedWidgets import kbComboBox

        
class MVIcomGUI(MVCommand):


    def updateICOMWidget(self, command, modifier):
        if command is None:
            name='None'
        else:
            if hasattr(command, 'name'):
                name = command.name
            else:
                name = 'None'
##         if modifier==None:
##             self.NoModWidget.selectitem(name)
        if modifier=='Shift_L':
            self.ShiftWidget.selectitem(name)
        elif modifier=='Control_L':
            self.CtrlWidget.selectitem(name)
##         elif modifier=='Alt_L':
##             self.AltWidget.selectitem(name)


    def onAddNewCmd(self, cmd):
        if not self.vf.hasGui: return
        names = ['None'] + self.getICOMNames()
        #self.NoModWidget.setitems(names)
        #self.NoModWidget.setlist(names)
        #self.ShiftWidget.setitems(names)
        self.ShiftWidget.setlist(names)
        #self.CtrlWidget.setitems(names)
        self.CtrlWidget.setlist(names)
        #self.AltWidget.setitems(names)
        #self.AltWidget.setlist(names)


    def getICOMNames(self):
        names = filter( lambda x, klass=ICOM: isinstance(x, klass),
                        self.vf.commands.values() )
        names = map( lambda x: x.name, names )
        names.sort()
        return names


    def onAddCmdToViewer(self):
        if not self.vf.hasGui:
            return

        bar = getICOMBar(self.vf)
        if isinstance(bar, Pmw.ScrolledFrame):
            barFrame = bar.interior()
        else:
            barFrame = bar
        self.vf.ICmdCaller.commands.AddCallback(self.updateICOMWidget)
        
        # create level radio buttons
        options = ['Atom', 'Residue', 'Chain', 'Molecule' ]
        col = self.vf.ICmdCaller.levelColors
        self.LevelOption = Pmw.OptionMenu(barFrame, 
                                          label_text = 'picking level:',
                                          labelpos = 'w',
                                          initialitem = options[0],
                                          command = self.setLevel_cb,
                                          items = options,
                                          menubutton_pady=0,
                                         )
        self.LevelOption.pack(side = 'left', anchor = 'nw',
                              expand = 1, padx = 2, pady = 1)

        for o in options:
            c = (col[o][0]/1.5,col[o][1]/1.5,col[o][2]/1.5)
            self.LevelOption._menu.entryconfigure(
                self.LevelOption._menu.index(o),
                background = TkColor(c), activebackground = TkColor(col[o])) 

        c = (col[options[0]][0]/1.5,col[options[0]][1]/1.5,col[options[0]][2]/1.5)
        self.LevelOption._menubutton.configure(
            background = TkColor(c),
            activebackground = TkColor(col[options[0]]))

        bar = getICOMBar(self.vf)
        if isinstance(bar, Pmw.ScrolledFrame):
            barFrame = bar.interior()
        else:
            barFrame = bar
        #self.Label = Tkinter.Label(barFrame, text='PCOM: ')
        #self.Label.pack(side='left')

        # get the sorted list of ICOMS
        names = ['None'] + self.getICOMNames()

        # create modifier dropDown combo box
        #self.NoModWidget = Pmw.OptionMenu(barFrame, labelpos = 'w',
        #                              command = self.NoMod_cb, items = names )
##         def comboBoxValidatorNoMod(event=None):
##             return event in self.NoModWidget._list.get()

##         self.NoModWidget = Pmw.ComboBox( barFrame, 
##                                          #label_text = 'NoMod:', 
##                                          labelpos = 'w',
##                                          entryfield_value='None',
##                                          selectioncommand=self.NoMod_cb, 
##                                          scrolledlist_items=names,
##                                          history = False,
##                                          #entryfield_entry_width=12,
##                                          )
##         self.NoModWidget.configure(entryfield_validate=comboBoxValidatorNoMod) 
##         self.NoModWidget.pack(side = 'left', anchor = 'nw',
##                               expand = 1, padx = 2, pady = 1)

        cmdDict = self.vf.ICmdCaller.commands.value
        cmd=cmdDict[None]
        if cmd is None: name = 'None'
        else: name = cmd.name
##         self.NoModWidget.selectitem(name)

        #self.ShiftWidget = Pmw.OptionMenu(barFrame, 
        #                                 label_text = 'Shift:', labelpos = 'w',
        #                                 command = self.Shift_cb, items = names)
        def comboBoxValidatorShift(event=None):
            return event in self.ShiftWidget._list.get()

        self.ShiftWidget = Pmw.ComboBox( barFrame, 
                                         label_text = 'Shift:', 
                                         labelpos = 'w',
                                         entryfield_value='None',
                                         selectioncommand=self.Shift_cb, 
                                         scrolledlist_items=names,
                                         history = False,
                                         #entryfield_entry_width=12,
                                         )
        self.ShiftWidget.configure(entryfield_validate=comboBoxValidatorShift) 
        self.ShiftWidget.pack(side = 'left', anchor = 'nw',
                              expand = 1, padx = 2, pady = 1)
        cmd = cmdDict['Shift_L']
        if cmd is None: name = 'None'
        else: name = cmd.name
        self.ShiftWidget.selectitem(name)

        #self.CtrlWidget = Pmw.OptionMenu(barFrame, 
        #                             label_text = 'Ctrl:', labelpos = 'w',
        #                             command = self.Ctrl_cb, items = names)
        def comboBoxValidatorCtrl(event=None):
            return event in self.CtrlWidget._list.get()

        self.CtrlWidget = Pmw.ComboBox( barFrame, 
                                         label_text = 'Ctrl:', 
                                         labelpos = 'w',
                                         entryfield_value='None',
                                         selectioncommand=self.Ctrl_cb, 
                                         scrolledlist_items=names,
                                         history = False,
                                         #entryfield_entry_width=12,
                                         )
        self.CtrlWidget.configure(entryfield_validate=comboBoxValidatorCtrl) 
        self.CtrlWidget.pack(side = 'left', anchor = 'nw',
                             expand = 1, padx = 2, pady = 1)
        cmd = cmdDict['Control_L']
        if cmd is None: name = 'None'
        else: name = cmd.name
        self.CtrlWidget.selectitem(name)

        #self.AltWidget = Pmw.OptionMenu(barFrame, 
        #                            label_text = 'Alt:', labelpos = 'w',
        #                            command = self.Alt_cb, items = names)
##         def comboBoxValidatorAlt(event=None):
##             return event in self.AltWidget._list.get()
##         self.AltWidget = Pmw.ComboBox( barFrame, 
##                                          label_text = 'Alt:', 
##                                          labelpos = 'w',
##                                          entryfield_value='None',
##                                          selectioncommand=self.Alt_cb, 
##                                          scrolledlist_items=names,
##                                          history = False,
##                                          #entryfield_entry_width=12,
##                                          )
##         self.AltWidget.configure(entryfield_validate=comboBoxValidatorAlt) 
##         self.AltWidget.pack(side = 'left', anchor = 'nw',
##                             expand = 1, padx = 2, pady = 1)
        cmd = cmdDict['Alt_L']
        if cmd is None: name = 'None'
        else: name = cmd.name
##         self.AltWidget.selectitem(name)
        self.bar = bar
        self.bar.pack_forget()


    def guiCallback(self, event=None):
        self.vf.ICOMbar.bar.pack()
        if self.vf.GUI.toolbarCheckbuttons['PCOM']['Variable'].get():
            self.vf.ICOMbar.bar.pack(fill='x')
            self.vf.GUI.ROOT.update()
            w = self.vf.GUI.ROOT.winfo_width()
            h = self.vf.GUI.ROOT.winfo_reqheight()
            h1 = self.vf.GUI.ROOT.winfo_height()
            if h1 > h:
                h = h1
            self.vf.GUI.ROOT.geometry('%dx%d' % ( w, h) )
        else:
            self.vf.ICOMbar.bar.pack_forget()


##     def NoMod_cb(self, cmdName):
##         if isinstance(cmdName, Tkinter.Event):
##             cmdName = cmdName.widget.get(cmdName.widget.curselection())
##         if cmdName=='None' or cmdName is None: cmd=None
##         else: cmd = self.vf.commands[cmdName]
##         self.vf.setICOM(cmd, None)


    def Shift_cb(self, cmdName):
        if isinstance(cmdName, Tkinter.Event):
            cmdName = cmdName.widget.get(cmdName.widget.curselection())
        if cmdName=='select': # special treatment to restore default picking
            ICmdCaller =  self.vf.ICmdCaller
            ICmdCaller.setCommands( self.vf.select, modifier='Shift_L',
                                    mode='pick')
            ICmdCaller.setCommands( self.vf.select, modifier='Shift_L',
                                    mode='drag select')
            ICmdCaller.setCommands( self.vf.deselect, modifier='Control_L',
                                    mode='pick')
            ICmdCaller.setCommands( self.vf.deselect, modifier='Control_L',
                                    mode='drag select')            
        else:
            if cmdName=='None' or cmdName is None: cmd=None
            else: cmd = self.vf.commands[cmdName]
            self.vf.setICOM(cmd, 'Shift_L', mode='pick')


    def Ctrl_cb(self, cmdName):
        if isinstance(cmdName, Tkinter.Event):
            cmdName = cmdName.widget.get(cmdName.widget.curselection())
        if cmdName=='None' or cmdName is None: cmd=None
        else: cmd = self.vf.commands[cmdName]
        self.vf.setICOM(cmd, 'Control_L', mode='pick')


##     def Alt_cb(self, cmdName):
##         if isinstance(cmdName, Tkinter.Event):
##             cmdName = cmdName.widget.get(cmdName.widget.curselection())
##         if cmdName=='None' or cmdName is None: cmd=None
##         else: cmd = self.vf.commands[cmdName]
##         self.vf.setICOM(cmd, 'Alt_L')
        
    
    def setLevel_cb(self, level):
        col = self.vf.ICmdCaller.levelColors
        c = (col[level][0]/1.5,col[level][1]/1.5,col[level][2]/1.5)
        self.LevelOption._menubutton.configure(
            background = TkColor(c),
            activebackground = TkColor(col[level]))
        if level=='Atom':
            self.vf.setIcomLevel(Atom)
        elif level=='Residue':
            self.vf.setIcomLevel(Residue)
        elif level=='Chain':
            self.vf.setIcomLevel(Chain)
        elif level=='Molecule':
            self.vf.setIcomLevel(Molecule)

PCOMGUI = CommandGUI()
from moleculeViewer import ICONPATH
PCOMGUI.addToolBar('PCOM', icon1 = 'mouse.gif', icon_dir=ICONPATH,
                   balloonhelp = 'Picking COMmands', index = 0)


class MVBindCmdToKey(MVCommand):

    def __init__(self, func=None):
        MVCommand.__init__(self, func=None)
        otherKeys = ['Escape', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8',
                     'F9', 'Tab', 'space', 'Return', 'Insert', 'Delete',
                     'Home', 'End', 'Prior', 'Next', 'Up', 'Down', 'Left',
                     'Right', 'Caps_Lock', 'Num_Lock', 'BackSpace']
                     
        self.bindings = {}
        for key in string.letters+string.digits:
            self.bindings[key] = {'None':None, 'Shift_L':None,\
                                  'Control_L':None, 'Alt_L':None,
                                  'Shift_R':None, 'Control_R':None,
                                  'Alt_R':None }
        for key in otherKeys:
            self.bindings[key] = {'None':None, 'Shift_L':None,\
                                  'Control_L':None, 'Alt_L':None,
                                  'Shift_R':None, 'Control_R':None,
                                  'Alt_R':None }


    def onAddCmdToViewer(self):
        if self.vf.hasGui:
            self.vf.GUI.addCameraCallback('<KeyRelease>',
                                          self.processRelease_cb)

    def processRelease_cb(self, event):
        if not self.bindings.has_key(event.keysym):
            return
        dict = self.bindings[event.keysym]
        mod = self.vf.GUI.VIEWER.getModifier()
        c = dict[mod]
        if c:
            apply( c[0], c[1], c[2] )


    def setupUndoBefore(self, key, modifier, cmd, args, kw):
        if not self.bindings.has_key(key): return
        c = self.bindings[key][modifier]
        if c: cmd = c
        else: c = None
        self.addUndoCall( (key, modifier, cmd, args, kw), {}, self.name )


    def doit(self, key, modifier, cmd, args=(), kw={}):
        assert isinstance(cmd, Command)
        assert modifier in ['None', 'Shift_L', 'Control_L', 'Alt_L',
                            'Shift_R', 'Control_R', 'Alt_R']
        assert key in self.bindings.keys()
        if cmd is None: cmd='None'
        self.bindings[key][modifier] = (cmd, args, kw)


    def __call__(self, key, modifier, cmd, args=(), kwa={}, **kw):
        """None <- bindCmdToKey(key, modifier, cmd, args=(), kwa={}, **kw)
           key: name of the key
           modifier: name of the modifier ('Shift_L', 'Control_L', 'Alt_L' ...)
           cmd: name of the command which wanted to be bound to the key"""
           
        apply( self.doitWrapper, (key, modifier, cmd, args, kwa), kw)
        
        
 
commandList = [
                {'name':'ICOMbar', 'cmd':MVIcomGUI(), 'gui':PCOMGUI},
    {'name':'setICOM', 'cmd':MVSetInteractiveCmd(), 'gui':None},
    
    {'name':'bindCmdToKey', 'cmd':MVBindCmdToKey(), 'gui':None},
]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])

