#########################################################################
#
# Date: Jan 2004 Author: Daniel Stoffler
#
#    stoffler@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Daniel Stoffler and TSRI
#
#########################################################################

import Tkinter, Pmw
import warnings
import types
import string, types, weakref
from mglutil.util.callback import CallBackFunction


class OneGrid:
    """Basic object that builds a grid editor GUI and provides a get() and
set() method"""

    def __init__(self, root=None, port=None, label=False, callback=None):
        # set root
        if root is None:
            self.root = self.panel = Tkinter.Toplevel()
        else:
            self.root = root

        self.callback = callback # callback function that is called when
                                 # <RETURN> is pressed in a given Entry

        # set weakref to port
        if port is not None:
            self.port = weakref.ref(port)
        else:
            self.port = None

        # set the flag self.label:
        self.label = label # if set to True, entries to specify label name and
                           # side are created

        # now define the Tkinter variables needed to set/get values
        self.rowTk = Tkinter.IntVar()
        self.rowspanTk = Tkinter.IntVar()
        self.columnTk = Tkinter.IntVar()
        self.columnspanTk = Tkinter.IntVar()
        self.stickyTk = Tkinter.StringVar()
        self.labelNameTk = Tkinter.StringVar()
        self.labelSideTk = Tkinter.StringVar()
        self.padxTk =  Tkinter.IntVar()
        self.padyTk =  Tkinter.IntVar()
        self.ipadxTk =  Tkinter.IntVar()
        self.ipadyTk =  Tkinter.IntVar()


        # initialize with default values that are different from '0'
        self.rowspanTk.set(1)
        self.columnspanTk.set(1)
        self.stickyTk.set('w')

        # variable for checkutton:
        self.cbVar = Tkinter.IntVar()
        self.cbVar.set(0)

        # and finally, create the GUI
        self.createForm()
        

    def createForm(self):
        """this method builds the GUI"""
        
        mainFrame = Tkinter.Frame(self.root)
        mainFrame.pack(side='top', expand=1, fill='both')

        cb = Tkinter.Checkbutton(mainFrame, text='more options',
                                 command=self.toggleOpts_cb,
                                 var=self.cbVar)
        cb.pack()
        gridFrame = Tkinter.Frame(mainFrame, borderwidth=2,
                                  relief='sunken', padx=5, pady=5)
        gridFrame.pack(side='top', expand=1, fill='both')
        

        self.topGrid = Tkinter.Frame(gridFrame)
        self.topGrid.grid(row=0, column=0, sticky='wens')
        self.bottomGrid = Tkinter.Frame(gridFrame)
        self.topGrid.grid(row=1, column=0, sticky='wens')
       
        row = 0
        ## Build the widgets which are visible by default (one line): topGrid
        if self.label:
            self.l1 = Tkinter.Label(self.topGrid, text='name:')
            self.l1.grid(row=row, column=0, sticky='w')
            self.b1 = Pmw.Balloon(self.topGrid)
            self.b1.bind(self.l1, "Change the name of the Label")
            self.e1 = Tkinter.Entry(self.topGrid, width=10,
                                     textvariable=self.labelNameTk)
            self.e1.grid(row=row, column=1, sticky='we')

            self.l2 = Tkinter.Label(self.topGrid, text='side:')
            self.l2.grid(row=row, column=2, sticky='w')
            self.b2 = Pmw.Balloon(self.topGrid)
            self.b2.bind(self.l2, "Change the side of the Label")
            self.e2 = Tkinter.Entry(self.topGrid, width=5,
                                     textvariable=self.labelSideTk)
            self.e2.grid(row=row, column=3, sticky='we')
            row += 1

        else:
            self.l1 = Tkinter.Label(self.topGrid, text="row:")
            self.l1.grid(row=row, column=0, sticky='w')
            self.b1 = Pmw.Balloon(self.topGrid)
            self.b1.bind(self.l1,
                     "Insert the widget at this row. Row numbers start with\n"+
                     "0. If omitted, defaults to the first empty row in the\n"+
                     "grid.")
            self.e1 = Tkinter.Entry(self.topGrid, width=3,
                                    textvariable=self.rowTk)
            self.e1.grid(row=row, column=1)
            
            self.l2 = Tkinter.Label(self.topGrid, text="column:")
            self.l2.grid(row=row, column=2, sticky='w')
            self.b2 = Pmw.Balloon(self.topGrid)
            self.b2.bind(self.l2,
                         "Insert the widget at this column. Column numbers\n"+
                         "start with 0. If omitted, defaults to 0.")
            self.e2 = Tkinter.Entry(self.topGrid, width=3,
                                    textvariable=self.columnTk)
            self.e2.grid(row=row, column=3)

        ## now build the widgets which are hidden by default: bottomGrid
        row += 1
        self.l3 = Tkinter.Label(self.bottomGrid, text="rowspan:")
        self.l3.grid(row=row, column=0, sticky='w')
        self.b3 = Pmw.Balloon(self.bottomGrid)
        self.b3.bind(self.l3,
                     "If given, indicates that the widget cell should span\n"+
                     "more than one row.")
        self.e3 = Tkinter.Entry(self.bottomGrid, width=3,
                                textvariable=self.rowspanTk)
        self.e3.grid(row=row, column=1)

        self.l4 = Tkinter.Label(self.bottomGrid, text="columnspan:")
        self.l4.grid(row=row, column=2, sticky='w')
        self.b4 = Pmw.Balloon(self.bottomGrid)
        self.b4.bind(self.l4,
                     "If given, indicates that the widget cell should span\n"+
                     "more than one column.")
        self.e4 = Tkinter.Entry(
            self.bottomGrid, width=3, textvariable=self.columnspanTk)
        self.e4.grid(row=row, column=3)

        row += 1
        self.l5 = Tkinter.Label(self.bottomGrid, text='sticky:')
        self.l5.grid(row=row, column=0, sticky='w')
        self.b5 = Pmw.Balloon(self.bottomGrid)
        self.b5.bind(
            self.l5,
            "Defines how to expand the widget if the resulting cell\n"+
            "is larger than the widget itself. This can be any\n"+
            "combination of the constants S, N, E, and W, or NW, NE,\n"+
            "SW, and SE. For example, W (west) means that the\n"+
            "widget should be aligned to the left cell border. W+E\n"+
            "means that the widget should be stretched horizontally\n"+
            "to fill the whole cell. W+E+N+S means that the widget\n"+
            "should be expanded in both directions. Default is to\n"+
            "center the widget in the cell.")
        self.e5 = Tkinter.Entry(self.bottomGrid, width=3,
                                textvariable=self.stickyTk)
        self.e5.grid(row=row, column=1, sticky='w')

        row += 1
        self.l6 = Tkinter.Label(self.bottomGrid, text="padx:")
        self.l6.grid(row=row, column=0, sticky='w')
        self.b6 = Pmw.Balloon(self.bottomGrid)
        self.b6.bind(self.l6,
                    "Optional padding to place around the widget in a cell.\n"+
                    "Default is 0.")
        self.e6 = Tkinter.Entry(self.bottomGrid, width=3,
                                textvariable=self.padxTk)
        self.e6.grid(row=row, column=1)

        self.l7 = Tkinter.Label(self.bottomGrid, text="pady:")
        self.l7.grid(row=row, column=2, sticky='w')
        self.b7 = Pmw.Balloon(self.bottomGrid)
        self.b7.bind(self.l7,
                    "Optional padding to place around the widget in a cell.\n"+
                    "Default is 0.")
        self.e7 = Tkinter.Entry(self.bottomGrid, width=3,
                                textvariable=self.padyTk)
        self.e7.grid(row=row, column=3)

        row += 1
        self.l8 = Tkinter.Label(self.bottomGrid, text="ipadx:")
        self.l8.grid(row=row, column=0, sticky='w')
        self.b8 = Pmw.Balloon(self.bottomGrid)
        self.b8.bind(self.l8,
                     "Optional internal padding. Works like padx and\n"+
                     "pady, but the padding is added inside the widget\n"+
                     "borders. Default is 0.")
        self.e8 = Tkinter.Entry(self.bottomGrid, width=3,
                                textvariable=self.ipadxTk)
        self.e8.grid(row=row, column=1)

        self.l9 = Tkinter.Label(self.bottomGrid, text="ipady:")
        self.l9.grid(row=row, column=2, sticky='w')
        self.b9 = Pmw.Balloon(self.bottomGrid)
        self.b9.bind(self.l9,
                     "Optional internal padding. Works like padx and\n"+
                     "pady, but the padding is added inside the widget\n"+
                     "borders. Default is 0.")
        self.e9 = Tkinter.Entry(self.bottomGrid, width=3,
                                textvariable=self.ipadyTk)
        self.e9.grid(row=row, column=3)

        # bind callback for pressing <Return> in Entry widget
        self.e1.bind('<Return>', self.callCallback)
        self.e2.bind('<Return>', self.callCallback)
        self.e3.bind('<Return>', self.callCallback)
        self.e4.bind('<Return>', self.callCallback)
        self.e5.bind('<Return>', self.callCallback)
        self.e6.bind('<Return>', self.callCallback)
        self.e7.bind('<Return>', self.callCallback)
        self.e8.bind('<Return>', self.callCallback)
        self.e9.bind('<Return>', self.callCallback)

        # by default, we do not show all options
        self.removeOptions()


    def set(self, gridcfg):
        """inputs a dict describing a Tkinter grid configuration"""

        keysLabel = ['labelName', 'labelSide', 'rowspan', 'column',
                     'columnspan', 'sticky', 'padx', 'pady', 'ipadx', 'ipady']
        keysWidget = ['row', 'rowspan', 'column', 'columnspan', 'sticky',
                     'padx', 'pady', 'ipadx', 'ipady']
        
        if self.label:
            keys = keysLabel
        else:
            keys = keysWidget
        
        for k,v in gridcfg.items():
            if k not in keys:
                continue

            attr = eval('self.'+k+'Tk')
            if attr == self.stickyTk:
                attr.set(string.lower(str(v)))
            else:
                attr.set(str(v))


    def get(self):
        """returns a dict describing a Tkinter grid configuration"""
        cfg = {}
        keysLabel = ['labelName', 'labelSide', 'rowspan', 'column',
                     'columnspan', 'sticky', 'padx', 'pady', 'ipadx', 'ipady']
        keysWidget = ['row', 'rowspan', 'column', 'columnspan', 'sticky',
                      'padx', 'pady', 'ipadx', 'ipady']

        if self.label:
            keys = keysLabel
        else:
            keys = keysWidget
        
        for k in keys:
            attr = eval('self.'+k+'Tk')
            val = attr.get()
            if val is not None and val != '':

                if k == 'sticky':
                    val = string.lower(val)
                    if len(val)>4:
                        val = 'w'
                    for i in range(len(val)):
                        if val[i] not in ['w', 'e', 'n', 's']:
                            val = 'w'
                            break
                    
                elif k == 'rowspan':
                    if val < 1:
                        val = 1

                elif k == 'columnspan':
                    if val < 1:
                        val = 1

                elif k == 'labelSide':
                    if val not in ['left', 'right', 'top', 'bottom']:
                        val = 'left'

                elif k in ['row', 'column', 'padx', 'pady', 'ipadx', 'ipady']:
                    if val < 0:
                        val = 0
                
                attr.set(val)
                cfg[k] = val
        return cfg
        

    def toggleOpts_cb(self, event=None):
        """toggle between displaying more or fewer options"""
        if self.cbVar.get() == 0:
            self.removeOptions()
        else:
            self.addOptions()


    def removeOptions(self):
        """remove certain entries from GUI"""
        self.bottomGrid.grid_remove()


    def addOptions(self):
        """add entries back to GUI"""
        self.bottomGrid.grid()


    def callCallback(self, event=None):
        if self.callback is not None and callable(self.callback):
            self.callback()
    

class GridEditor:

    def __init__(self, node=None):
        if node is not None:
            self.node = weakref.ref(node)   # weak reference to Vision node
        else:
            self.node = None
        self.top = Tkinter.Toplevel()       # root/top of this GUI
        self.top.title("Widget Grid Editor")

        self.grids = []                     # storing all the grid objects
        self.gridCounter = 0 # used to set callback for <Return> in each grid
                             # entry widget to call ApplyToOneGrid() instead
                             # calling Apply_cb() which would rebuild all
                             # widgets.

        # create two frames, one to hold all the grid GUIs, one for the buttons
        self.gridFrame = Tkinter.Frame(self.top)
        self.gridFrame.pack(side='top', expand=1, fill='both')
        self.buttonFrame = Tkinter.Frame(self.top)
        self.buttonFrame.pack(side='bottom', expand=1, fill='both')
        # and now build the form
        self.buildForm()
        self.top.protocol("WM_DELETE_WINDOW", self.Cancel_cb)
        

    def buildForm(self):
        if self.node is None:
            return

        row = 0
        column = 0
        l1 = Tkinter.Label(#group.interior(),
            self.gridFrame,
                           text='Label Conf')
        l2 = Tkinter.Label(#group.interior(),
            self.gridFrame,
                          text='Widget Conf')
        l1.grid(row=0, column=0)
        l2.grid(row=0, column=1)

        row = row + 1
        for i in range(len(self.node().inputPorts)):
            port = self.node().inputPorts[i]
            if port.widget is None:
                continue
            widgetDescr = port.widget.getDescr()
            name = port.name
            
            group = Pmw.Group(
                self.gridFrame, tag_text='Widget '+\
                #widgetDescr['class']+\
                ' '+name)
            group.grid(row=row, column=column, columnspan=2, padx=6, pady=6,
                       sticky='wens')
            f1 = Tkinter.Frame(group.interior())
            f2 = Tkinter.Frame(group.interior())
            cb = CallBackFunction(self.ApplyToOneGrid, self.gridCounter)
            g1 = OneGrid(f1, port=port, label=True, callback=cb)
            g2 = OneGrid(f2, port=port, label=False, callback=cb)
            self.gridCounter += 1

            # append to self.grids
            self.grids.append((g1, g2))
            
            # get current grid_info and set gui accordingly
            # we do not use widgetDescr, because this might not be up do date!
            g1.set(port.widget.tklabel.grid_info())
            g1.set({'labelName':widgetDescr['labelCfg']['text'],
                    'labelSide':widgetDescr['widgetGridCfg']['labelSide']})
            g2.set(port.widget.widgetFrame.grid_info())
            
            #l1.grid(row=0, column=0)
            f1.grid(row=2, column=0, padx=6, pady=6)
            

            #l2.grid(row=0, column=1)
            f2.grid(row=2, column=1, padx=6, pady=6)
            row = row + 1

        # add buttons
        ok = Tkinter.Button(self.buttonFrame, text='Ok', command=self.OK_cb)
        ok.pack(side='left', expand=1, fill='x')
        apply = Tkinter.Button(self.buttonFrame, text='Apply',
                               command=self.Apply_cb)
        apply.pack(side='left', expand=1, fill='x')
        cancel = Tkinter.Button(self.buttonFrame, text='Cancel',
                                command=self.Cancel_cb)
        cancel.pack(side='left', expand=1, fill='x')


    def OK_cb(self, event=None):
        self.Apply_cb()
        self.Cancel_cb()


    def ApplyToOneGrid(self, number, autoResize=True):
        """Apply to a specified grid pair"""
        lgrid, wgrid = self.grids[number] # get the pairs of label&widget grids
        
        ldescr = lgrid.get()
        wdescr = wgrid.get()
        if lgrid.port is None or wgrid.port is None:
            return

        widget = wgrid.port().widget
        node = widget.port.node
        labName = ldescr.pop('labelName','')
        labSide = ldescr.pop('labelSide', 'left')

        wdescr['labelSide'] = labSide

        applyDict = dict(labelCfg=dict(text=labName), labelGridCfg=ldescr)
        applyDict['widgetGridCfg%s'%widget.master] = wdescr

        apply(widget.configure, (),applyDict)

        if autoResize:
            self.node().autoResize() 
            

    def Apply_cb(self, event=None):
        for i in range(len(self.grids)):
            self.ApplyToOneGrid(i, autoResize=False)
        self.node().autoResize()
        

    def Cancel_cb(self, event=None):
        if self.node is not None and self.node().objEditor is not None:
            ed = self.node().objEditor
            ed.editGridVarTk.set(0)
            ed.nbEditorWindows -= 1
            ed.manageEditorButtons()
            
        self.top.destroy()
