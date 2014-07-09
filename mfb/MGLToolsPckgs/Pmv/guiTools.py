#############################################################################
#
# Author: Sophie COON, Ruth HUEY, Michel F. SANNER, Stefano FORLI
#
# Copyright: M. Sanner TSRI 2011
#
#############################################################################


#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/guiTools.py,v 1.13.20.2 2012/09/17 00:15:46 rhuey Exp $
#
# $Id: guiTools.py,v 1.13.20.2 2012/09/17 00:15:46 rhuey Exp $
#
"""
This Module implements useful tools for the MoleculeViewer:
for example:
        MoleculeChooser
"""
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser, ObjectChooser
#from Framework.gui import ListChooser
import Tkinter
import Pmw
from MolKit.molecule import Molecule, MoleculeSet
from MolKit.tree import TreeNodeSet
from MolKit.protein import Protein, ProteinSet
##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
import types

class MoleculeListChooser(ObjectChooser):
    """class to present a list of molecules in a scrolled listbox."""

    def __init__(self, root,mode='single', title='Choose',
                 molecules = None, cwcfg={'usehullsize':1,
                                        'hull_width':100,'hull_height':80,
                                        'text_wrap':'none'}, 
                 lbpackcfg={'fill':'x', 'expand':1}, lbwcfg={}):

        
        objects = self.buildObject(molecules)
        ObjectChooser.__init__(self,root, mode, title, objects, cwcfg,
                             lbpackcfg,lbwcfg)
        
        #self.entries = []

    def buildObject(self, molecules):
        objects = map(lambda x: (x, x.name,
                                 x.parser.getMoleculeInformation()),
                      molecules)
        return objects

    def add(self, molecule):
        "Add an entry to the moleculelistchooser."
        if not type(molecule)==types.TupleType:
            object  = self.buildEntry(molecule)
        else:
            object = molecule
        ObjectChooser.add(self,object)

    def insert(self, pos, molecule):
        object  = self.buildObject(molecule)
        ObjectChooser.insert(self,pos,object)

    def get(self, event = None):
        if not self.lb.curselection():
            res = []
        else:
            res = TreeNodeSet()
        for ent in map( int, self.lb.curselection() ):
            mol= self.nameObject[self.entries[ ent ][0]]
            res.append(mol)

        if self.mode=='single' and res:
            res = res[0]

        return res
    
class MoleculeChooser:
    """presents user w/ a list of molecules currently loaded;
mode can be 'single', 'browse', 'multiple' or 'extended'.
Molecules can be selected from the list or by picking in the camera.

OK button returns a list of entries which have been selected.
Cancel returns an empty list. 
Typical usage is:
    ans = MoleculeChooser(self.vf).go()
    if ans !=[]:
        then get the value(s)
NB: this class doesn't grab the focus and binds picking w/
B1 to selecting the molecule in the MoleculeChooser. """ 


    def __init__(self, viewer, mode = 'single', title = 'Choose Molecule'):

        self.vf = viewer
        self.mode = mode
        self.ipf = InputFormDescr(title = title)


    def done_cb(self):
        self.ap.stop()
        self.ipf.form.destroy()
        self.ipf.form = None

    def go(self, modal=1, blocking=0, event = "<ButtonRelease-1>"):
        """Start the form"""

        entries = []
        for i in range(len(self.vf.Mols)):
            mol = self.vf.Mols[i]
            molParser = mol.parser
            molStr = molParser.getMoleculeInformation()
            entries.append((mol.name, molStr))

##          self.ipf.insert(0,{'name': 'Molecule',
##                             'widgetType': 'ListChooser',
##                             'title' : 'select a molecule',
##                             'mode' : self.mode,
##                             'entries' : entries})

        self.ipf.insert(0,{'name': 'Molecule',
                           'widgetType': ListChooser,
                           'wcfg':{
                               'title' : 'select a molecule',
                               'mode' : self.mode,
                               'entries' : entries},
                           'gridcfg':{'sticky':'wens'}})

        if not (modal or blocking):
            self.ipf.append({'widgetType':Tkinter.Button,
                             'wcfg':{'text':'Dismiss',
                                     'command': self.done_cb},
                             'gridcfg':{'sticky':'we'}})

        from Pmv.picker import AtomPicker
        self.ap = AtomPicker(self.vf, None, 0, callbacks=[self.onPick],
                             immediate=1)
        self.ap.go(modal=0)
        val = self.vf.getUserInput(self.ipf, modal=modal, blocking=blocking)
        if val:
            if modal or blocking:
                if len(val['Molecule'])==1:
                    mols = self.vf.Mols.NodesFromName( val['Molecule'][0] )
                    if self.mode=='single': return mols[0]
                    return mols
                else:
                    molNames = ""
                    for m in val['Molecule']: 
                        molNames = molNames+','+m
                    mols = self.vf.Mols.NodesFromName( molNames )
                    self.ap.stop()
                    if self.mode=='single': return mols[0]
                    return mols
            else:
                self.form = val
                return val
        else:
            return val

    def getMolSet(self):
        """method to get currently selected molecules when the chooser is used
        in modal=0 and blocking=0 mode"""

        val = self.form.checkValues()
        if len(val['Molecule'])==0:
            t = "Nothing selected!"
            self.vf.warningMsg(t, title="MoleculeChooser WARNING:")
            return None
        molNames = ""
        for m in val['Molecule']:
            # Create the list of names
            if molNames == "":
                molNames = m
            else:
                molNames = molNames + ";" + m
        mols = self.vf.Mols.NodesFromName( molNames )
        if self.mode=='single': return mols[0]
        return mols

    def onPick(self,atoms):
        listChooser = self.ipf.entryByName['Molecule']['widget']
        tkListBox = listChooser.lb
        if atoms:
            pickedMol = atoms[0].top
            #then need to make pickedMol the selection in self.lc
            for i in range(len(listChooser.entries)):
                if pickedMol.name == listChooser.entries[i][0]:
                    self.pickedMolIndex= i
                    tkListBox.select_clear(0,'end')
                    listChooser.select(i)
                    return
            print "error: %s not in mv.Mols" %pickedMol.name

    
class AugmentedMoleculeChooser(MoleculeChooser):
    """presents user w/ a list of molecules currently loaded;
mode can be 'single', 'browse', 'multiple' or 'extended'.
Molecules can be selected from the list or by picking in the camera.
OK button returns a list of entries which have been selected.
Cancel returns an empty list. 
Typical usage is:
    ans = MoleculeChooser(self.vf).go()
    if ans !=[]:
        then get the value(s)

Extra dictionaries can be added to the inputform  to obtain other user defined values. To do this, set extra to not None and extraDict to a list of dictionaries to be appended to the input form.

NB: this class doesn't grab the focus and binds picking w/
B1 to selecting the molecule in the MoleculeChooser. """ 


    def __init__(self, viewer, mode = 'single', title = 'Choose Molecule', selectTitle="select a molecule", extra=[], extraDict=None):
        MoleculeChooser.__init__(self, viewer, mode, title)
        self.extra = extra
        self.extraDict = extraDict
        self.selectTitle = selectTitle


    def go(self, modal=1, blocking=0, event = "<ButtonRelease-1>"):
        """Start the form"""

        entries = []
        for i in range(len(self.vf.Mols)):
            mol = self.vf.Mols[i]
            molParser = mol.parser
            molStr = molParser.getMoleculeInformation()
            entries.append((mol.name, molStr))

        self.ipf.insert(0,{'name': 'Molecule',
                           'widgetType': ListChooser,
                           'wcfg':{
                               'title' : self.selectTitle,
                               'mode' : self.mode,
                               'entries' : entries},
                           'gridcfg':{'sticky':'wens'}})

        for k in self.extra:
            ct = 1
            for d in self.extraDict:
                self.ipf.insert(ct, d)
                ct = ct + 1

        if not (modal or blocking):
            self.ipf.append({'widgetType':Tkinter.Button,
                             'wcfg':{'text':'Dismiss',
                                     'command': self.done_cb},
                             'gridcfg':{'sticky':'we'}})

        from Pmv.picker import AtomPicker
        self.ap = AtomPicker(self.vf, None, 0, callbacks=[self.onPick],
                             immediate=1)
        self.ap.go(modal=0)
        val = self.vf.getUserInput(self.ipf, modal=modal, blocking=blocking)
        if val:
            if modal or blocking:
                if len(val['Molecule'])==1:
                    mols = self.vf.Mols.NodesFromName( val['Molecule'][0] )
                    if self.mode=='single': returnValue = mols[0]
                    #if self.mode=='single': return mols[0]
                    else: returnValue = mols
                    #return mols
                else:
                    molNames = ""
                    for m in val['Molecule']: 
                        molNames = molNames+','+m
                    mols = self.vf.Mols.NodesFromName( molNames )
                    self.ap.stop()
                    #if self.mode=='single': return mols[0]
                    if self.mode=='single': returnValue = mols[0]
                    else: returnValue = mols
                    #return mols
                #if self.extra is not None:
                for k in self.extra:
                    returnValue =  (returnValue, val[k])
                    #returnValue =  (returnValue, val[self.extra])
                return returnValue

            else:
                self.form = val
                return val
        else:
            return val

# Tkinter interface to SYSV `ps' and `kill' commands.

from Tkinter import *

if TkVersion < 4.0:
    raise ImportError, "This version of svkill requires Tk 4.0 or later"

from string import splitfields
from string import split
import commands
import sys,os

## if sys.platform!='win32':
##     user = os.environ['LOGNAME']
## else:
##     user = 'NoName'

user = os.environ.get('LOGNAME', 'NoName')


class BarButton(Menubutton):
    def __init__(self, master=None, **cnf):
        apply(Menubutton.__init__, (self, master), cnf)
        self.pack(side=LEFT)
        self.menu = Menu(self, name='menu')
        self['menu'] = self.menu

class Kill(Frame):
    # List of (name, option, pid_column)
    view_list = [
        ('Default', ''),
        ('Every (-e)', '-e'),
        ('Non process group leaders (-d)', '-d'),
        ('Non leaders with tty (-a)', '-a'),
        ('For this user (-u %s)' % user, '-u %s' % user),
    ]
    format_list = [
        ('Default', '', 0),
        ('Long (-l)', '-l', 3),
        ('Full (-f)', '-f', 1),
        ('Full Long (-f -l)', '-l -f', 3),
        ('Session and group ID (-j)', '-j', 0),
        ('Scheduler properties (-c)', '-c', 0),
        ]
    def kill(self, selected):
        c = self.format_list[self.format.get()][2]
        pid = split(selected)[c]
        os.system('kill -9 ' + pid)
        self.do_update()
    def do_update(self):
        format = self.format_list[self.format.get()][1]
        view = self.view_list[self.view.get()][1]
        s = commands.getoutput('ps %s %s' % (view, format))
        list = splitfields(s, '\n')
        self.header.set(list[0] + '          ')
        del list[0]
        self.frame.list.delete(0, AtEnd())
        for line in list:
            self.frame.list.insert(0, line)
    def do_motion(self, e):
        e.widget.select_clear('0', 'end')
        e.widget.select_set(e.widget.nearest(e.y))
    def do_leave(self, e):
        e.widget.select_clear('0', 'end')
    def do_1(self, e):
        self.kill(e.widget.get(e.widget.nearest(e.y)))
    def __init__(self, master=None, **cnf):
        apply(Frame.__init__, (self, master), cnf)
        self.pack(expand=1, fill=BOTH)
        self.bar = Frame(self, name='bar', relief=RAISED,
                 borderwidth=2)
        self.bar.pack(fill=X)
        self.bar.file = BarButton(self.bar, text='File')
        self.bar.file.menu.add_command(
            label='Quit', command=self.quit)
        self.bar.view = BarButton(self.bar, text='View')
        self.bar.format = BarButton(self.bar, text='Format')
        self.view = IntVar(self)
        self.view.set(0)
        self.format = IntVar(self)
        self.format.set(0)
        for num in range(len(self.view_list)):
            label, option = self.view_list[num]
            self.bar.view.menu.add_radiobutton(
                label=label,
                command=self.do_update,
                variable=self.view,
                value=num)
        for num in range(len(self.format_list)):
            label, option, col = self.format_list[num]
            self.bar.format.menu.add_radiobutton(
                label=label,
                command=self.do_update,
                variable=self.format,
                value=num)
        self.bar.tk_menuBar(self.bar.file,
                    self.bar.view,
                    self.bar.format)
        self.frame = Frame(self, relief=RAISED, borderwidth=2)
        self.frame.pack(expand=1, fill=BOTH)
        self.header = StringVar(self)
        self.frame.label = Label(
            self.frame, relief=FLAT, anchor=NW, borderwidth=0,
            font='*-Courier-Bold-R-Normal-*-12-*', #>0 points; <0 pixels
            textvariable=self.header)
        self.frame.label.pack(fill=Y, anchor=W)
        self.frame.vscroll = Scrollbar(self.frame, orient=VERTICAL)
        self.frame.list = Listbox(
            self.frame, 
            relief=SUNKEN,
            font='*-Courier-Medium-R-Normal-*-12-*',
            width=40, height=10,
            selectbackground='#eed5b7',
            selectborderwidth=0,
            selectmode=BROWSE,
            yscroll=self.frame.vscroll.set)
        self.frame.vscroll['command'] = self.frame.list.yview
        self.frame.vscroll.pack(side=RIGHT, fill=Y)
        self.frame.list.pack(expand=1, fill=BOTH)
        self.update = Button(self, text='Update',
                     command=self.do_update)
        self.update.pack(fill=X)
        self.frame.list.bind('<Motion>', self.do_motion)
        self.frame.list.bind('<Leave>', self.do_leave)
        self.frame.list.bind('<1>', self.do_1)
        self.do_update()

class CenterChooser:
    """
    Class to allow a center to be defined (e.g. for the center of rotation
    for a list of docking transformations). Returns either `Center on Molecule',
    'Center on Selection', or a a list [x,y,z] specifying the center explicitly
    """

    def __init__(self,viewer):
        self.ifd = InputFormDescr(title='Choose Center of Rotation')
        self.vf = viewer


    def cancel_cb(self):
        self.form.destroy()
        

    def go(self, modal= 1, blocking =0):
        self.ifd.append({'widgetType':Pmw.RadioSelect,
                         'listtext':['Center on Molecule',
                                     'Center on Selection',
                                     'Type in Center'],
                         'defaultValue':'Type in Center',
                         'wcfg':{'orient':'vertical',
                                 'buttontype':'radiobutton',
                                 'command':self.setButton,
                                 }})
        self.ifd.append({'widgetType':Pmw.EntryField,
                         'name':'X',
                         'validator':'real',
                         'wcfg':{'label_text':'X',
                                 'labelpos':'w'},
                         'gridcfg':{}})
        self.ifd.append({'widgetType':Pmw.EntryField,
                         'name':'Y',
                         'wcfg':{'label_text':'Y',
                                 'labelpos':'w'},
                         'gridcfg':{}})
        self.ifd.append({'widgetType':Pmw.EntryField,
                         'name':'Z',
                         'wcfg':{'label_text':'Z',
                                 'labelpos':'w'},
                         'gridcfg':{}})
        
        val = self.form = self.vf.getUserInput(self.ifd, modal=modal,
                                               blocking=blocking)
        if val:
            if not (val['X'] and val['Y'] and val['Z']): 
                val = self.ifd[0]['widget'].selection
                if val == 'Type in Center':
                    val = 'Center on Molecule'
                print 'In CenterChooser: val =',val
                return val
            else:
                val = [float(val['X']),float(val['Y']),float(val['Z'])]
                return val

                
    def setButton(self,button):
        x = self.ifd.entryByName['X']
        y = self.ifd.entryByName['Y']
        z = self.ifd.entryByName['Z']
        if button == 'Type in Center':
            x['widget'].grid(x['gridcfg'])
            y['widget'].grid(y['gridcfg'])
            z['widget'].grid(z['gridcfg'])
        else:
            x['widget'].grid_forget()
            y['widget'].grid_forget()
            z['widget'].grid_forget()

            
if __name__ == '__main__':
    kill = Kill(None, borderwidth=5)
    kill.winfo_toplevel().title('Tkinter Process Killer (SYSV)')
    kill.winfo_toplevel().minsize(1, 1)
    kill.mainloop()

