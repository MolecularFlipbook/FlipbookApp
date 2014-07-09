# -*- coding: utf-8 -*-
"""
Created on Mon May 17 22:53:21 2010

@author: -
"""

########################################################################
#
# Authors: Sargis Dallakyan, Michel Sanner
#
#    sargis@scripps.edu
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Sargis Dallakyan, Michel Sanner and TSRI
#
#########################################################################
# 
# $Header: /opt/cvs/python/packages/share1.5/Pmv/hostappInterface/lightGridCommands.py,v 1.4 2010/07/22 18:16:09 autin Exp $
# $Id: lightGridCommands.py,v 1.4 2010/07/22 18:16:09 autin Exp $
"""This module integrates Volume.Grid3D with ViewerFramework for rendering 3D Grids.
It includes Add/Remove, Isocontour, OrthoSlice and VolRender commands, and a 
table widget for navigating between grids. 

See http://mgltools.scripps.edu/documentation/tutorial/volume-rendering for more info. 
"""
import sys
import re, types, os, math, pickle
import Tkinter, Pmw, tkFileDialog, tkMessageBox
from PIL import Image, ImageTk
from tkColorChooser import askcolor
from DejaVu.Geom import Geom
from ViewerFramework.VFCommand import Command, CommandGUI
from mglutil.gui import widgetsOnBackWindowsCanGrabFocus
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser
from mglutil.gui.InputForm.Tk.gui import InputFormDescr, InputForm
from mglutil.gui.BasicWidgets.Tk.multiListbox import MultiListbox
from mglutil.util.misc import ensureFontCase
from Volume.IO.volReaders import ReadMRC, ReadCCP4, ReadCNS, ReadGRD, ReadBRIX,\
                                    ReadSPIDER, ReadRawiv, ReadEM, ReadFLDBinary
from Volume.IO.volWriters import WriteCCP4
from Volume.IO.UHBDGridReader import UHBDReaderASCII
from Volume.IO.DelphiReader import DelphiReaderBin
from Volume.IO.dxReader import ReadDX
from Volume.IO.AutoGridReader import ReadAutoGrid
from Volume.IO.gamessOrbitalsReader import ReadGamessOrbitals
from Volume.Grid3D import Grid3D, Grid3DD, Grid3DF, Grid3DI, \
     Grid3DSI, Grid3DUI, Grid3DUSI, Grid3DUC, ArrayTypeToGrid, GridTypeToArray
from Volume.Renderers.UTVolumeLibrary.DejaVu.UTVolRenGeom import UTVolRenGeom     
from mglutil.util.packageFilePath import findFilePath
from DejaVu.extendedSlider import ExtendedSlider
try:
    from UTpackages.UTisocontour import isocontour
    isocontour.setVerboseLevel(0)
except ImportError:
    isocontour = None

from DejaVu.IndexedPolygons import IndexedPolygons
from DejaVu.Box import Box
from DejaVu.Textured2DArray import textured2DArray
import numpy.oldnumeric as Numeric
import numpy
from DejaVu.colorMap import ColorMap
from DejaVu.ColormapGui import ColorMapGUI
from opengltk.OpenGL import GL

from Pmv.moleculeViewer import DeleteGeomsEvent, AddGeomsEvent, EditGeomsEvent

def getSupportedFormat():
    return '\.mrc$|\.MRC$|\.cns$|\.xplo*r*$|\.ccp4*$|\.grd$|\.fld$|\.map$|\.omap$|\.brix$|\.dsn6$|\.dn6$|\.rawiv$|\.d*e*l*phi$|\.uhbd$|\.dx$|\.spi$'

ICONPATH = findFilePath('Icons', 'ViewerFramework')
Grid_ICONPATH = os.path.join(ICONPATH, 'Grid3D')
if sys.platform == 'darwin':
    rightClick = "Apple-Click"
else:
    rightClick = "Right-Click"
def get_icon(icon, master):
    iconfile = os.path.join(Grid_ICONPATH, icon)         
    head, ext = os.path.splitext(iconfile)
    if ext == '.gif':
        if master is None:
            Icon = Tkinter.PhotoImage(file=iconfile)
        else:
            Icon = Tkinter.PhotoImage(file=iconfile, master=master)
    else:
        image = Image.open(iconfile)
        if master is None:
            Icon = ImageTk.PhotoImage(image=image)
        else:
            Icon = ImageTk.PhotoImage(image=image, master=master)
    return Icon

class addGridCommand(Command):
    """
   \nPackage : ViewerFramework
   \nModule  : grid3DCommands
   \nClass   : addGridCommand
   \nCommand : addGrid
   \ndoit(self, grid3D, name=None):\n
    """    
    def doit(self, grid3D, name=None):    
        sys.stderr.write('doit addGrid')
        grid3D.origin_copy = grid3D.origin
        grid3D.stepSize_copy = grid3D.stepSize
        mini, maxi, mean, std = grid3D.stats()
        sys.stderr.write('doit addGrid')
        grid3D.mini = mini
        grid3D.maxi = maxi
        grid3D.mean = mean
        grid3D.std = std
        if name == None:
            name = str(grid3D) 
        if self.vf.grids3D.has_key(name):
            name += "_" 
        def returnStringRepr():
            return None, "\"" + name + "\""
        grid3D.returnStringRepr = returnStringRepr
        if not hasattr(grid3D,'geomContainer'):
            grid3D.geomContainer = {}
            g = Geom(name)
            grid3D.master_geom = g
            if self.vf.hasGui : self.vf.GUI.VIEWER.AddObject(g)
            grid3D.geomContainer['IsoSurf'] = {}
            grid3D.geomContainer['OrthoSlice'] = {}
            IsoSurf = Geom('IsoSurf')                
            OrthoSlice = Geom('OrthoSlice')
            box = Box('BoundingBox')

            pt1 = grid3D.origin
            dims = grid3D.data.shape
            pt2 = [pt1[0]+(grid3D.stepSize[0]*(dims[0]-1)),
                   pt1[1]+(grid3D.stepSize[1]*(dims[1]-1)),
                   pt1[2]+(grid3D.stepSize[2]*(dims[2]-1))]
            if grid3D.crystal:
                ptList=((pt2[0],pt2[1],pt1[2]),
                        (pt1[0],pt2[1],pt1[2]),
                        (pt1[0],pt1[1],pt1[2]),
                        (pt2[0],pt1[1],pt1[2]),
                        (pt2[0],pt2[1],pt2[2]),
                        (pt1[0],pt2[1],pt2[2]),
                        (pt1[0],pt1[1],pt2[2]),
                        (pt2[0],pt1[1],pt2[2]))
                coords = grid3D.crystal.toCartesian(ptList)
                box.Set(vertices=coords)
            else:
                coords = (pt1, pt2)
                box.Set(cornerPoints=coords)                
                
            grid3D.geomContainer['Box'] = box
            if self.vf.hasGui :
                self.vf.GUI.VIEWER.AddObject(box,parent=g)
                self.vf.GUI.VIEWER.AddObject(IsoSurf,parent=g)
                self.vf.GUI.VIEWER.AddObject(OrthoSlice,parent=g)
            grid3D.IsoSurf = IsoSurf
            grid3D.OrthoSlice = OrthoSlice
        self.vf.grids3D[name] = grid3D
        sys.stderr.write('doit addGridDone')
        if self.vf.hasGui :
            if self.vf.Grid3DCommands.root:
                grid_name = name
                grid_type = grid3D.data.dtype
                self.vf.Grid3DCommands.mlb.insert(Tkinter.END, (grid_name, 
                                                grid3D.dimensions, grid_type ))

        #self.vf.Grid3DCommands.mlb.selection_clear(0, Tkinter.END)
        #self.vf.Grid3DCommands.mlb.selection_set(Tkinter.END)
        #self.vf.Grid3DAddRemove.select()
                

class readAnyGrid(Command):
    """ The readAnyGrid reads any of the grids supported by Volume.IO and
saves Grid3D object in self.vf.grids3D[gridFile] where gridFile can be provided
by Grid3D-->Read GUI
   \nPackage : ViewerFramework
   \nModule  : grid3DCommands
   \nClass   : readAnyGrid
   \nCommand : readAnyGrid
   \nSynopsis:\n
        grid3D<-readAnyGrid(gridFile)\n
    \nRequired Arguments:\n    
        gridFile  : location of the grid file\n
    """
    def __init__(self, func=None):
        Command.__init__(self)
        mapItems = [('AutoGrid',None),
                    ('BRIX/DSN6',None),
                    ('CCP4',None),
                    ('CNS/XPLOR',None),
                    ('Data Explorer(DX)',None),
                    ('Delphi',None),
                    ('GRD',None),
                    ('MRC',None),
                    ('Rawiv',None),
                    ('SPIDER',None),
                    ('UHBD/GRID',None),
                    ('AVS/FLD Binary',None),
                    ]

        #if self.vf.hasGui :
        self.ifd=InputFormDescr(title='Map Types')
        self.ifd.append({'name':'listchooser',
                'widgetType':ListChooser,
                'wcfg':{'title':'Select a Map Type:',
                        'entries':mapItems,
                        'lbwcfg':{'width':20,'height':12},
                        'mode':'single',
                        },
                'gridcfg':{'sticky':'w','row':-1}
                })

    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'grids3D'):
            self.vf.grids3D={}

    def __call__(self, gridFile, **kw):
        """Grid3D object<-readAnyGrid(gridFile)\n
           \nRequired Arguments:\n    
                gridFile  : location of the grid file\n
        """
        return apply(self.doitWrapper, (gridFile,), kw)

    def doit(self, gridFile, name=None, show=True, normalize=True):
        """Reads gridFile and adds it to Control Panel
        Optoinal Arguments:
          name    : name of the grid file used as a key in self.vf.grid3d
                    if None os.path.basename(gridFile) is used
          show    : if True show Control panel
        normalize : if true calls Normalize the Viewer
        """
        if not gridFile: return
        if not os.path.exists(gridFile):
            print gridFile, " not exists" 
        else:
            if(re.search('\.mrc$',gridFile,re.I)):
                reader = ReadMRC()
            elif(re.search('\.ccp4*$',gridFile,re.I)):
                reader = ReadCCP4()
            elif(re.search('\.cns$|\.xplo*r*$',gridFile,re.I)):
                reader = ReadCNS()
            elif(re.search('\.grd$',gridFile,re.I)):
                reader = ReadGRD()
            elif(re.search('\.fld$',gridFile,re.I)):
                reader = ReadFLDBinary()
            elif(re.search('\.map$',gridFile,re.I)):
                reader = ReadAutoGrid()
            elif(re.search('\.omap$|\.brix$|\.dsn6$|\.dn6$',gridFile,re.I)):
                reader = ReadBRIX()
            elif(re.search('\.rawiv$',gridFile,re.I)):
                reader = ReadRawiv()
            elif(re.search('\.d*e*l*phi$',gridFile,re.I)):
                reader = DelphiReaderBin()
            elif(re.search('\.uhbd$',gridFile,re.I)):
                reader = UHBDReaderASCII()
            elif(re.search('\.dx$',gridFile,re.I)):
                reader = ReadDX()
            elif(re.search('\.spi$',gridFile,re.I)):
                reader = ReadSPIDER()
            else:
                if not show: return
                if self.vf.hasGui :
                    reader = self.askMapType()
                    if not reader:
                        return
        try:
            grid3D = reader.read(gridFile, normalize=True)
        except Exception, inst:
            print inst
            if not show: return
            if self.vf.hasGui :
                reader = self.askMapType()
                if not reader:
                    return
                try:
                    grid3D = reader.read(gridFile, normalize=True)
                except Exception, inst:
                    print inst
                    tkMessageBox.showerror("Error: in choosing a map", 
              "Could not parse %s. Please open Python shell for Traceback"%gridFile)
                    return
            else : return
        if not grid3D:
            if not show: return
            if self.vf.hasGui :
                reader = self.askMapType()
                if not reader:
                    return
                try:
                    grid3D = reader.read(gridFile, normalize=True)
                except Exception, inst:
                    print inst
                    tkMessageBox.showerror("Error: in choosing a map", 
              "Could not parse %s. Please open Python shell for Traceback"%gridFile)
                    return
            else : return
        if name:
            grid_basename = name
        else:
            grid_basename = os.path.basename(gridFile)
        if grid3D:
            grid3D.path = gridFile
            self.vf.addGrid(grid3D, grid_basename,log=0)
            if self.vf.hasGui :
                if normalize:
                    self.vf.GUI.VIEWER.Normalize_cb()
                if show:
                    self.vf.Grid3DCommands.show()
            elif self.vf.embeded and self.vf.hostApp.hostname == 'chimera':
                import VolumeViewer
                v=VolumeViewer.open_volume_file(gridFile)[-1]
                grid3D.ch_vol = v
                grid3D.master_geom.obj = v
        return grid3D
    
    def askMapType(self):
        """Opens Select Map Type widget"""
        f = InputForm(master=Tkinter._default_root,
                            root=Tkinter.Toplevel(),
                            descr=self.ifd, blocking=1, modal=1)
        maptype=f.go()
        if not maptype:
            return False
        choice=maptype['listchooser'][0]
        if choice=='AutoGrid': reader=ReadAutoGrid()
        elif choice=='BRIX/DSN6': reader=ReadBRIX()
        elif choice=='CCP4': reader=ReadCCP4()
        elif choice=='CNS/XPLOR': reader=ReadCNS()
        elif choice=='Data Explorer(DX)': reader=ReadDX()
        elif choice=='Delphi': reader=DelphiReaderBin()
        elif choice=='GRD':reader=ReadGRD()
        elif choice=='MRC':reader=ReadMRC()
        elif choice=='Rawiv':reader=ReadRawiv()
        elif choice=='SPIDER':reader=ReadSPIDER()
        elif choice=='UHBD/GRID':reader=UHBDReaderASCII()
        elif choice=='AVS/FLD Binary':self.reader=ReadFLDBinary()
        else: 
            tkMessageBox.showerror("Error: in choosing a map", 
                                   "Error: in choosing" + choice)
            return False
        return reader
        
    def guiCallback(self, parent = None):
        """called each time the 'Grid3D -> Import...' sequence is pressed"""
        fileTypes = [('All supported files', '*.map *.ccp4 *.dx *.grd '+ 
'*.omap *.brix* *.dsn6* *.cns *.xplo*r* *.d*e*l*phi *.mrc *.rawiv *.spi *.uhbd'),
                     ('AutoGrid', '*.map'),
                     ('AVS/FLD  Binary', '*.fld'),
                     ('BRIX/DSN6', '*.omap *.brix* *.dsn6*'),
                     ('CCP4', '*.ccp4'),
                     ('CNS/XPLOR', '*.cns *.xplo*r*'),
                     ('Data Explorer(DX)', '*.dx'),
                     ('Delphi', '*.d*e*l*phi'),
                     ('GRD', '*.grd'),
                     ('MRC', '*.mrc'),
                     ('Rawiv', '*.rawiv'),
                     ('SPIDER', '*.spi'),
                     ('UHBD/GRID', '*.uhbd'),
                     ('all', '*')]
        gridFile = tkFileDialog.askopenfilename(parent = parent, 
                                      filetypes=fileTypes, title = 'Grid File:')
        if gridFile is not None and len(gridFile):
            self.doitWrapper(gridFile, redraw=0)

readAnyGridGUI = CommandGUI()
readAnyGridGUI.addMenuCommand('menuRoot', 'Grid3D', 'Read...')

class GridMultiListbox(MultiListbox):
    """Extends MultiListbox from mglutil.gui.BasicWidgets.Tk.multiListbox"""
    def __init__(self, master, lists, **kw):
        MultiListbox.__init__(self, master, lists, **kw)
        self.girdName = ''
    def _select(self, y):
        self.Grid3DCommands.root.config(cursor='watch')
        self.Grid3DCommands.root.update()
        row = self.lists[0].nearest(y)
        self.selection_clear(0, Tkinter.END)
        self.selection_set(row)
        if row != -1:
            girdName = self.Grid3DCommands.get_grid_name()
            if girdName != self.girdName:
                self.Grid3DCommands.current_cmd.select()
                self.girdName = girdName
        self.Grid3DCommands.root.config(cursor='')
        return 'break'    
    
width = 440    #width of the GUI
height = 200   #height of the GUI

class Grid3DCommands(Command):
    """This is the main class that adds GridMultiListbox widget with 
       Add/Remove, Isocontour and OrthoSlice icons and widgets
    """
    def __init__(self, func=None):
        Command.__init__(self)
        self.root = None
        self.Icons = []
        self.Checkbuttons = {}
        
    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'grids3D'):
            self.vf.grids3D={}

    def get_grid_name(self):
        select = self.mlb.curselection()
        if not select:
            return None
        grid_name = self.mlb.get(select[0])
        return grid_name[0]
    
    def select(self, name):
        "Selects Listbox by Grid Name"
        grids = self.mlb.lists[0].get(0,Tkinter.END)
        grids = list(grids)
        index = grids.index(name)
        self.mlb.selection_clear(0,Tkinter.END)
        self.mlb.selection_set(index)
        
    def doit(self, show = True, **kw):
        if show:
            self.show()
        else:
            self.hide()
            
    def guiCallback(self, **kw):
        if not self.root:
            self.root = Tkinter.Toplevel()
            self.root.title('3D Grid Rendering Control Panel')
            self.root.protocol("WM_DELETE_WINDOW", self.hide)
            menu = Tkinter.Menu(self.root)
            self.root.config(menu=menu)  
            self.root.minsize(width+5,width-5)
            file = Tkinter.Menu(menu)
            file.add_command(label='Open Grid...', 
                             command=self.vf.Grid3DAddRemove.add)
            file.add_command(label='Load Settings...', command=self.open)
            file.add_command(label='Save Settings...', command=self.save)

            menu.add_cascade(label='File', menu=file)
            
            self.PanedWindow = Tkinter.PanedWindow(self.root, handlepad=0,
                                 handlesize=0, orient=Tkinter.VERTICAL, bd=1,
                                 width=width,height=2*height)
            self.PanedWindow.pack(fill=Tkinter.BOTH, expand=1)

            self.mlb = GridMultiListbox(self.PanedWindow, ((' Grid Name', 33),  
                                                 ('Dimensions   ', 15),  
                                                 ('Type', 6)),
                                                 hull_height = 100,
                                                 usehullsize = 1,
                                                 hull_width = width)

            self.mlb.pack(expand=Tkinter.NO, fill=Tkinter.X)
            self.mlb.Grid3DCommands = self
            for grid in self.vf.grids3D:
                grid_name = grid
#                if len(grid_name) > 40:
#                    grid_name = grid_name[-37:]
#                    grid_name = '...'+grid_name         
                grid_type = self.vf.grids3D[grid].data.dtype.name
                self.vf.Grid3DCommands.mlb.insert(Tkinter.END, (grid_name, 
                                  self.vf.grids3D[grid].dimensions, grid_type ))
            self.PanedWindow.add(self.mlb)            

            main_frame = Tkinter.Frame(self.PanedWindow)
            main_frame.pack(expand=Tkinter.YES, fill=Tkinter.BOTH)
            self.PanedWindow.add(main_frame, height=height+90)
            self.main_frame = main_frame
            toolbar_frame = Tkinter.Frame(main_frame, bg='white',
                                          relief=Tkinter.RIDGE, bd=2)
            toolbar_frame.pack(expand=Tkinter.NO, fill=Tkinter.X)
            self.toolbar_frame = toolbar_frame
            widget_frame = Tkinter.Frame(main_frame)
            widget_frame.pack(expand=Tkinter.YES, fill=Tkinter.BOTH)
            
            self.widget_frame = widget_frame
            cmd_list = [
            ('Add/Remove', 'add_rem.png', self.Add_Remove, 'Add/Remove 3D Gird')]
            if isocontour:
                cmd_list.append(('Isocontour', 'iso.png', self.Isocontour, 
                                 'Isocontouring Widget'))
            cmd_list.append(('OrthoSlice', 'ortho.png', self.OrthoSlice, 
                             'Orthogonal Slices'))
            from Volume.Renderers.UTVolumeLibrary import UTVolumeLibrary
            test = UTVolumeLibrary.VolumeRenderer()
            flag = test.initRenderer()
            if flag:
                cmd_list.append(('VolRen', 'VolRen.png', self.VolRen, 
                     '3D Texture-Based Volume Renderer'))
            else:
                print "Volume Renderer is Disabled"
            #font LucidaTypewriter Marumoji, MiscFixed 14
            for name, icon, func, txt in cmd_list:
                Icon = get_icon(icon, master=self.root)
                self.Icons.append(Icon)
                Checkbutton = Tkinter.Checkbutton(toolbar_frame, image=Icon,
                                                  indicatoron=0, command=func, 
                                                  bg='white')
                Checkbutton.ballon = Pmw.Balloon()
                Checkbutton.ballon.bind(Checkbutton, txt)
                self.Checkbuttons[name] = Checkbutton
                Checkbutton.pack(side=Tkinter.LEFT) 

            
            idf = self.vf.Grid3DAddRemove.ifd                
            self.add_remove_form = InputForm(main_frame,self.widget_frame,idf,
                                             okcancel=0,closeWithWindow=0,
                                             width=width, height=height)
            self.add_remove_form.mf.config(bd =0)
            self.add_remove_form.mf.pack_forget()
            idf = self.vf.Grid3DIsocontour.ifd
            self.isocontour_form = InputForm(main_frame,self.widget_frame,idf,
                                             okcancel=0,closeWithWindow=0,
                                             width=width, height=height)
            self.isocontour_form.mf.config(bd =0)
            self.isocontour_form.mf.pack_forget()

            idf = self.vf.Grid3DOrthoSlice.ifd
            self.OrthoSlice_form = InputForm(main_frame,self.widget_frame,idf,
                                             okcancel=0,closeWithWindow=0,
                                             width=width, height=height)
            self.OrthoSlice_form.mf.config(bd =0)
            self.OrthoSlice_form.mf.pack_forget()
            
            idf = self.vf.Grid3DVolRen.ifd
            self.VolRen_form = InputForm(main_frame,self.widget_frame,idf,
                                             okcancel=0,closeWithWindow=0,
                                             width=width, height=height)
            self.VolRen_form.mf.config(bd =0)
            self.VolRen_form.mf.pack_forget()
            
            self.add_remove_form.mf.pack(expand=Tkinter.YES, fill=Tkinter.BOTH)
            self.current_obj = self.add_remove_form
            self.current_cmd = self.vf.Grid3DAddRemove
            bottom_frame = Tkinter.Frame(main_frame)
            bottom_frame.pack(fill=Tkinter.X)
            self.close_b = Tkinter.Button(bottom_frame, text="  Dismiss  ", 
                                          command=self.hide)
            self.close_b.pack(expand=Tkinter.NO)
            self.current_checkbutton = self.Checkbuttons['Add/Remove']
            self.current_checkbutton.toggle()
            self.vf.GUI.toolbarCheckbuttons['Grid3D']['Variable'].set(1)
            self.GUI.menuButton.menu.entryconfig(3, label='Hide Control Panel',
                                                 command=self.hide)
            h = self.root.winfo_reqheight()
            w = self.mlb.interior().winfo_reqwidth()
            if w > self.root.winfo_width():
                self.root.geometry('%dx%d' % (w,h))

        elif self.vf.GUI.toolbarCheckbuttons['Grid3D']['Variable'].get() == 0 \
                                                                  and self.root:
            self.root.withdraw()
            self.GUI.menuButton.menu.entryconfig(3,label='Show Control Panel',
                                                 command=self.show)
            
            
        elif self.vf.GUI.toolbarCheckbuttons['Grid3D']['Variable'].get() == 1 \
                                                                  and self.root:
            self.root.deiconify()    
            self.GUI.menuButton.menu.entryconfig(3,label='Hide Control Panel',
                                                 command=self.hide)

    def show(self, event=None):
        if self.root is None:
            self.guiCallback()
        else:
            self.root.deiconify()
        self.vf.GUI.toolbarCheckbuttons['Grid3D']['Variable'].set(1)
        self.GUI.menuButton.menu.entryconfig(3, label='Hide Control Panel',
                                             command=self.hide)
        
    def hide(self, event=None):
        if self.root:
            self.root.withdraw()
        self.vf.GUI.toolbarCheckbuttons['Grid3D']['Variable'].set(0)
        self.GUI.menuButton.menu.entryconfig(3,label='Show Control Panel',
                                             command=self.show)
           
    def Add_Remove(self):
        if self.current_cmd == self.vf.Grid3DVolRen:
           self.current_cmd.ifd.entryByName['VolRen']['widget'].merge_function() 
           self.current_cmd.saveLUT_Dict()        
        self.current_checkbutton.config(state='normal')
        self.current_checkbutton.toggle()
        self.current_obj.mf.pack_forget()
        self.add_remove_form.mf.pack(expand=Tkinter.YES, fill=Tkinter.BOTH)
        self.current_obj = self.add_remove_form
        self.Checkbuttons['Add/Remove'].config(state='disabled')
        self.current_checkbutton = self.Checkbuttons['Add/Remove']
        self.current_cmd = self.vf.Grid3DAddRemove
        self.current_cmd.select()
        
    def Isocontour(self):
        self.root.configure(cursor='watch')
        self.root.update()
        if self.current_cmd == self.vf.Grid3DVolRen:
           self.current_cmd.ifd.entryByName['VolRen']['widget'].merge_function() 
           self.current_cmd.saveLUT_Dict()
        self.current_checkbutton.config(state='normal')
        self.current_checkbutton.toggle()
        self.current_obj.mf.pack_forget()
        self.isocontour_form.mf.pack(expand=Tkinter.YES, fill=Tkinter.BOTH)
        self.current_obj = self.isocontour_form
        self.Checkbuttons['Isocontour'].config(state='disabled')
        self.current_checkbutton = self.Checkbuttons['Isocontour']
        self.current_cmd = self.vf.Grid3DIsocontour
        self.current_cmd.select()

    def OrthoSlice(self):
        self.root.configure(cursor='watch')
        self.root.update()
        #This in needed to save the VolRen
        if self.current_cmd == self.vf.Grid3DVolRen:
           self.current_cmd.ifd.entryByName['VolRen']['widget'].merge_function() 
           self.current_cmd.saveLUT_Dict()           
        self.current_checkbutton.config(state='normal')
        self.current_checkbutton.toggle()
        self.current_obj.mf.pack_forget()
        self.OrthoSlice_form.mf.pack(expand=Tkinter.YES, fill=Tkinter.BOTH)
        self.current_obj = self.OrthoSlice_form
        self.Checkbuttons['OrthoSlice'].config(state='disabled')
        self.current_checkbutton = self.Checkbuttons['OrthoSlice']
        self.current_cmd = self.vf.Grid3DOrthoSlice
        self.current_cmd.select()

    def VolRen(self):
        self.root.configure(cursor='watch')
        self.root.update()
        self.current_checkbutton.config(state='normal')
        self.current_checkbutton.toggle()
        self.current_obj.mf.pack_forget()
        self.VolRen_form.mf.pack(expand=Tkinter.YES, fill=Tkinter.BOTH)
        self.current_obj = self.VolRen_form
        self.Checkbuttons['VolRen'].config(state='disabled')
        self.current_checkbutton = self.Checkbuttons['VolRen']
        self.current_cmd = self.vf.Grid3DVolRen
        self.current_cmd.select()
        
    def save(self):
        outFile = tkFileDialog.asksaveasfile(parent=self.root, 
                                             filetypes=[('Grid settings', 
                                                         '*.pkl')], 
                                       title='Save Grid Control Panel File As:')
        if not outFile:
            return
        self.vf.Grid3DCommands.root.config(cursor='watch')
        settings = []
        for gridName in self.vf.grids3D:
            gridSettings = {}
            gridSettings['name'] = gridName
            grid = self.vf.grids3D[gridName]
            gridSettings['path'] = grid.path
            gridSettings['origin'] = grid.origin
            gridSettings['stepSize'] = grid.stepSize
            gridSettings['boxVisible'] = grid.geomContainer['Box'].visible
            gridSettings['masterVisible'] = grid.master_geom.visible
            if hasattr(grid,'isoBarNumber'): #saves Isocontour attributes
                gridSettings['isoBarNumber'] = grid.isoBarNumber
                gridSettings['isoBarTags'] = grid.isoBarTags
                gridSettings['isoLastColor'] = grid.isoLastColor
                gridSettings['isoLastX'] = grid.isoLastX             
            if hasattr(grid,'_X_Slice'): #saves OrthSlice attributes
                gridSettings['_X_Slice'] = grid._X_Slice
                gridSettings['_X_Vis'] = grid._X_Vis
            if hasattr(grid,'_Y_Slice'):
                gridSettings['_Y_Slice'] = grid._Y_Slice
                gridSettings['_Y_Vis'] = grid._Y_Vis
            if hasattr(grid,'_Z_Slice'):
                gridSettings['_Z_Slice'] = grid._Z_Slice
                gridSettings['_Z_Vis'] = grid._Z_Vis
            if hasattr(grid,'volRenGrid'): #saves volRenGrid attributes
                gridSettings['LUTintervals_list'] = grid.LUT_data.intervals_list
                gridSettings['LUTshapes'] = grid.LUT_data.shapes
                gridSettings['LUTvalues'] = grid.LUT_data.values
                gridSettings['LUTcolor_arr'] = grid.LUT_data.color_arr
                gridSettings['LUTalpha_arr'] = grid.LUT_data.alpha_arr
            settings.append(gridSettings)
        pickle.dump(settings, outFile)
        outFile.close()
        self.vf.Grid3DCommands.root.config(cursor='')
        self.vf.Grid3DCommands.PanedWindow.config(cursor='')
        
    def open(self):
        inFile = tkFileDialog.askopenfile(parent=self.root, 
                                           filetypes=[('Grid settings', 
                                                          '*.pkl'),
                                                        ('all', '*')  ], 
                                          title='Open Grid Control Panel File:')
        if not inFile:
            return
        self.vf.Grid3DCommands.root.config(cursor='watch')
        
        settings = pickle.load(inFile)
        for gridSettings in settings:
            self.vf.Grid3DReadAny.doit(gridSettings['path'], 
                                       name=gridSettings['name'])
            grid = self.vf.grids3D[gridSettings['name']]
            grid.origin = gridSettings['origin']
            grid.stepSize = gridSettings['stepSize']
            grid.geomContainer['Box'].visible = gridSettings['boxVisible']
            grid.master_geom.visible = gridSettings['masterVisible']
            if gridSettings.has_key('isoBarNumber'):
                grid.isoBarNumber = gridSettings['isoBarNumber']
                grid.isoBarTags = gridSettings['isoBarTags']
                grid.isoLastColor = gridSettings['isoLastColor']
                grid.isoLastX = gridSettings['isoLastX']
                
                origin = Numeric.array(grid.origin).astype('f')
                stepsize = Numeric.array(grid.stepSize).astype('f')
                data = grid.data
                if data.dtype.char!=Numeric.Float32:
                    data = data.astype('f')
                self.vf.Grid3DIsocontour.newgrid3D = Numeric.reshape( 
                                                      Numeric.transpose(data),
                                                      (1, 1)+tuple(data.shape) )
                if self.vf.Grid3DIsocontour.iso_data:
                    isocontour.delDatasetReg(self.vf.Grid3DIsocontour.iso_data)
                self.vf.Grid3DIsocontour.iso_data = isocontour.\
                        newDatasetRegFloat3D(self.vf.Grid3DIsocontour.newgrid3D,
                                             origin, stepsize)
                for i in range(1, grid.isoBarNumber+1):
                    tag = grid.isoBarTags[i-1]
                    if grid.isoLastX[tag]<0:
                        invertNormals = True
                    else:
                        invertNormals = False
                    color = grid.isoLastColor[tag]
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                    self.vf.Grid3DIsocontour.doit(grid, name=tag, 
                                                 isovalue=grid.isoLastX[tag], 
                                                 invertNormals=invertNormals, 
                                          material=(r/255., g/255., b/255, 0.5))    
            if gridSettings.has_key('_X_Slice'):
                grid._X_Slice  = gridSettings['_X_Slice']
                grid._X_Vis  = gridSettings['_X_Vis']
                geom = textured2DArray('OrthoSlice_X',
                                       inheritLighting=False,
                                       lighting=False)
                self.vf.GUI.VIEWER.AddObject(geom, parent=grid.OrthoSlice)
                grid.geomContainer['OrthoSlice']['X'] = geom
                data, vertices = grid.get2DOrthoSlice('x', grid._X_Slice)
                geom.Set(vertices=vertices, array=data, visible=grid._X_Vis)
            if gridSettings.has_key('_Y_Slice'):
                grid._Y_Slice  = gridSettings['_Y_Slice']
                grid._Y_Vis  = gridSettings['_Y_Vis']
                geom = textured2DArray('OrthoSlice_Y',
                                       inheritLighting=False,
                                       lighting=False)
                self.vf.GUI.VIEWER.AddObject(geom, parent=grid.OrthoSlice)
                grid.geomContainer['OrthoSlice']['Y'] = geom
                data, vertices = grid.get2DOrthoSlice('y', grid._Y_Slice)
                geom.Set(vertices=vertices, array=data, visible=grid._Y_Vis)
            if gridSettings.has_key('_Z_Slice'):
                grid._Z_Slice  = gridSettings['_Z_Slice']
                grid._Z_Vis  = gridSettings['_Z_Vis']
                geom = textured2DArray('OrthoSlice_Z',
                                       inheritLighting=False,
                                       lighting=False)
                self.vf.GUI.VIEWER.AddObject(geom, parent=grid.OrthoSlice)
                grid.geomContainer['OrthoSlice']['Z'] = geom
                data, vertices = grid.get2DOrthoSlice('z', grid._Z_Slice)
                geom.Set(vertices=vertices, array=data, visible=grid._Z_Vis)
            if gridSettings.has_key('LUTintervals_list'):
                from Volume.Operators.MapData import MapGridData
                datamap = {}
                datamap['src_min'] = grid.mini
                datamap['src_max'] = grid.maxi
                datamap['dst_min'] = 0
                datamap['dst_max'] = 255
                datamap['map_type'] = 'linear'
                mapper = MapGridData()
                result = mapper(grid.data, datatype=Numeric.UInt8, datamap=datamap,
                                powerOf2=True)
                gtype = ArrayTypeToGrid[result.dtype.char]
                if grid.crystal:
                    from mglutil.math.crystal import Crystal
                    crystal = Crystal( grid.crystal.length, grid.crystal.angles)
                else:
                    crystal = None
                newgrid = gtype(result, grid.origin, grid.stepSize, 
                                grid.header.copy(), crystal)
                newgrid.dataDims = grid.data.shape[:]
                grid.volRenGrid = newgrid
                geom = UTVolRenGeom('VolRender')
                grid.geomContainer['VolRender'] = geom
                self.vf.GUI.VIEWER.AddObject(geom, parent=grid.master_geom)
                geom.AddGrid3D(newgrid)
                self.vf.GUI.VIEWER.OneRedraw()
                grid.LUT_data = LUT_data()
                grid.LUT_data.intervals_list = gridSettings['LUTintervals_list']
                grid.LUT_data.shapes = gridSettings['LUTshapes']
                grid.LUT_data.values = gridSettings['LUTvalues']
                grid.LUT_data.color_arr = gridSettings['LUTcolor_arr']
                grid.LUT_data.alpha_arr = gridSettings['LUTalpha_arr']
                geom.setVolRenAlpha([0,grid.LUT_data.alpha_arr])
                geom.setVolRenColors([0,grid.LUT_data.color_arr])
                
        inFile.close()
        self.vf.Grid3DCommands.root.config(cursor='')
        self.vf.Grid3DCommands.PanedWindow.config(cursor='')
        
Grid3DGUI = CommandGUI()
msg = '3D Grid/Volume Rendering'
Grid3DGUI.addToolBar('Grid3D', icon1='vol.png', balloonhelp=msg, index=13.,
                     icon_dir=ICONPATH)
Grid3DGUI.addMenuCommand('menuRoot', 'Grid3D', 'Show Control Panel')
"""
class AddRemove(Command):
    def __init__(self, func=None):
        if hasattr(self, 'root') is True:
            master = self.root
        else:
            master = None
        Command.__init__(self)
        self.boundingBoxVisible = Tkinter.BooleanVar()
        self.boundingBoxVisible.set(1)
        self.childGeomVisible = Tkinter.BooleanVar()
        self.childGeomVisible.set(1)
        self.Icons = []
        self.ifd = InputFormDescr(title = "Add Ion")

        self.ifd.append({'name':'step_size_label',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':''},
                    'gridcfg':{'row':0, 'column':1, 'sticky':'w'}
                    })
        Icon = get_icon('add.png', master=master)
        self.Icons.append(Icon)
        self.ifd.append({'name':'Add',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Add', 'image':Icon, 'command':self.add},
                    'gridcfg':{'row':1, 'column':0, 'sticky':'we'}
                    })

        self.ifd.append({'name':'Name',
                    'widgetType':Pmw.EntryField,
                    'wcfg':{'labelpos':'w', 'label_text':'Grid Name:', 
                            'command':self.apply},
                    'gridcfg':{'row':1, 'column':1, 'columnspan':4,'sticky':'we'}
                    })

        self.ifd.append({'name':'l_add',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Add'},
                    'gridcfg':{'row':2, 'column':0, 'sticky':'we'}
                    })

        self.ifd.append({'name':'origin_label',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'   Origin:'},
                    'gridcfg':{'row':3, 'column':1, 'sticky':'w'}
                    })

        self.ifd.append({'name':'X_origin',
                    'widgetType':Pmw.EntryField,
                    'wcfg':{'labelpos':'e', 'label_text':'X', 'entry_width':8,
                            'validate':{'validator' : 'real'},'sticky':'w',
                            'command':self.apply},
                    'gridcfg':{'row':3, 'column':2, 'sticky':'w'}
                    })

        self.ifd.append({'name':'Y_origin',
                    'widgetType':Pmw.EntryField,
                    'wcfg':{'labelpos':'e', 'label_text':'Y', 'entry_width':8,
                            'validate':{'validator' : 'real'},'sticky':'w',
                            'command':self.apply},
                    'gridcfg':{'row':3, 'column':3, 'sticky':'w'}
                    })

        self.ifd.append({'name':'Z_origin',
                    'widgetType':Pmw.EntryField,
                    'wcfg':{'labelpos':'e', 'label_text':'Z', 'entry_width':8,
                            'validate':{'validator' : 'real'},'sticky':'w',
                            'command':self.apply},
                    'gridcfg':{'row':3, 'column':4, 'sticky':'w'}
                    })

        Icon = get_icon('rem.png', master=master)        
        self.Icons.append(Icon)
        self.ifd.append({'name':'Remove',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Remove','image':Icon,'command':self.remove},
                    'gridcfg':{'row':3, 'column':0, 'sticky':'we'}
                    })

        self.ifd.append({'name':'l_remove',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Remove'},
                    'gridcfg':{'row':4, 'column':0, 'sticky':'we'}
                    })

        self.ifd.append({'name':'step_size_label',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'   Step Size:'},
                    'gridcfg':{'row':4, 'column':1, 'sticky':'w'}
                    })

        self.ifd.append({'name':'dX',
                    'widgetType':Pmw.EntryField,
                    'wcfg':{'labelpos':'e', 'label_text':'dX', 'entry_width':8,
                            'validate':{'validator' : 'real'},'sticky':'w',
                            'command':self.apply},
                    'gridcfg':{'row':4, 'column':2, 'sticky':'w'}
                    })

        self.ifd.append({'name':'dY',
                    'widgetType':Pmw.EntryField,
                    'wcfg':{'labelpos':'e', 'label_text':'dY', 'entry_width':8,
                            'validate':{'validator' : 'real'},'sticky':'w',
                            'command':self.apply},
                    'gridcfg':{'row':4, 'column':3, 'sticky':'w'}
                    })

        self.ifd.append({'name':'dZ',
                    'widgetType':Pmw.EntryField,
                    'wcfg':{'labelpos':'e', 'label_text':'dZ', 'entry_width':8,
                            'validate':{'validator' : 'real'},'sticky':'w',
                            'command':self.apply},
                    'gridcfg':{'row':4, 'column':4, 'sticky':'w'}
                    })


        self.ifd.append({'name':'Apply',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Apply', 'command':self.apply},
                    'gridcfg':{'row':5, 'column':3,'sticky':'we'}
                    })
        
        self.ifd.append({'name':'Reset',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Reset', 'command':self.reset},
                    'gridcfg':{'row':5, 'column':4, 'sticky':'we'}
                    })
        

        self.ifd.append({'name':'childGeomVisible',
                    'widgetType':Tkinter.Checkbutton,
                    'wcfg':{'text':'Show/Hide Volume',
                            'command':self.changeChildrenVisible,
                            'variable':self.childGeomVisible},
                    'gridcfg':{'row':6, 'column':0,'columnspan':3, 'sticky':'w'}
                    })

        self.ifd.append({'name':'boundingBoxVisible',
                    'widgetType':Tkinter.Checkbutton,
                    'wcfg':{'text':'Show Bounding Box','command':self.changeBox,
                            'variable':self.boundingBoxVisible},
                    'gridcfg':{'row':6,  'column':3,'columnspan':3}
                    })

        
    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'grids3D'):
            self.vf.grids3D={}

    def __call__(self, grid3D, **kw):
        apply(self.doitWrapper, (grid3D,), kw)

    def doit(self, grid3D, remove = True):
        grid3D = self.vf.grids3D[grid3D]
        self.vf.GUI.VIEWER.Redraw()

    def guiCallback(self):
        self.vf.Grid3DCommands.show()
        if self.vf.Grid3DCommands.current_cmd != self.vf.Grid3DAddRemove:
            self.vf.Grid3DCommands.Checkbuttons["Add/Remove"].toggle()
            self.vf.Grid3DCommands.Add_Remove()
        
    def changeBox(self,event=None):
        grid_name = self.vf.Grid3DCommands.get_grid_name()
        if not grid_name:
            return
        if self.boundingBoxVisible.get():
            self.vf.grids3D[grid_name].geomContainer['Box'].Set(visible=1)
        else:
            self.vf.grids3D[grid_name].geomContainer['Box'].Set(visible=0)
        self.vf.GUI.VIEWER.Redraw()     
           
    def changeChildrenVisible(self, event=None):
        grid_name = self.vf.Grid3DCommands.get_grid_name()
        if not grid_name:
            return
        if self.childGeomVisible.get():
            self.vf.grids3D[grid_name].master_geom.Set(visible=1)
            self.ifd.entryByName['boundingBoxVisible']['widget'].configure(state='normal')
        else:
            self.vf.grids3D[grid_name].master_geom.Set(visible=0)
            self.ifd.entryByName['boundingBoxVisible']['widget'].configure(state='disabled')
        self.vf.GUI.VIEWER.Redraw()        
        
    def add(self):
        self.vf.Grid3DCommands.root.config(cursor='watch')
        self.vf.Grid3DReadAny.guiCallback(parent = self.vf.Grid3DCommands.root)
        self.vf.Grid3DCommands.mlb.selection_clear(0, Tkinter.END)
        self.vf.Grid3DCommands.mlb.selection_set(Tkinter.END)
        self.select()
        self.vf.Grid3DCommands.root.config(cursor='')
        self.vf.Grid3DCommands.PanedWindow.config(cursor='')
        
    def remove(self):
        grid_name = self.vf.Grid3DCommands.get_grid_name()
        if not grid_name:
            if self.vf.Grid3DCommands.mlb.size() != 0:
                self.ifd.entryByName['Name']['widget'].\
                                   setvalue('Please select grid from the list')
            else:
                self.ifd.entryByName['Name']['widget'].\
                                     setvalue('There are no grids in the list')
            return
        grid3D = self.vf.grids3D[grid_name]
        for geoms in grid3D.geomContainer:
            if hasattr(grid3D.geomContainer[geoms],'__iter__'):                
                for geom in grid3D.geomContainer[geoms]:
                    self.vf.GUI.VIEWER.RemoveObject(grid3D.geomContainer[geoms][geom])
            else:
                self.vf.GUI.VIEWER.RemoveObject(grid3D.geomContainer[geoms])
        for children in grid3D.master_geom.children:
            children.protected = False
        grid3D.master_geom.protected = False
        self.vf.GUI.VIEWER.RemoveObject(grid3D.master_geom)
        self.vf.grids3D.pop(grid_name)
        select = self.vf.Grid3DCommands.mlb.curselection()[0]
        self.vf.Grid3DCommands.mlb.delete(select)
        self.ifd.entryByName['Name']['widget'].setvalue('')
        self.ifd.entryByName['X_origin']['widget'].setvalue('')
        self.ifd.entryByName['Y_origin']['widget'].setvalue('')
        self.ifd.entryByName['Z_origin']['widget'].setvalue('')
        self.ifd.entryByName['dX']['widget'].setvalue('')
        self.ifd.entryByName['dY']['widget'].setvalue('')
        self.ifd.entryByName['dZ']['widget'].setvalue('')
        self.vf.GUI.VIEWER.Redraw()
        self.vf.Grid3DCommands.mlb.girdName = None
        
    def select(self):
        grid_name = self.vf.Grid3DCommands.get_grid_name()
        if not grid_name:
            return
        self.vf.Grid3DCommands.mlb.girdName = grid_name
        self.ifd.entryByName['Name']['widget'].setvalue(grid_name)
        grid = self.vf.grids3D[grid_name]
        origin = grid.origin
        self.ifd.entryByName['X_origin']['widget'].setvalue(origin[0])
        self.ifd.entryByName['Y_origin']['widget'].setvalue(origin[1])
        self.ifd.entryByName['Z_origin']['widget'].setvalue(origin[2])
        stepSize = grid.stepSize
        self.ifd.entryByName['dX']['widget'].setvalue(stepSize[0])
        self.ifd.entryByName['dY']['widget'].setvalue(stepSize[1])
        self.ifd.entryByName['dZ']['widget'].setvalue(stepSize[2])
        visible = grid.geomContainer['Box'].visible
        self.boundingBoxVisible.set(visible)
        visible = grid.master_geom.visible
        self.childGeomVisible.set(visible)
        if visible:
            self.ifd.entryByName['boundingBoxVisible']['widget'].configure(state='normal')
        else:
            self.ifd.entryByName['boundingBoxVisible']['widget'].configure(state='disabled')
            
    def apply(self):
        grid_name = self.vf.Grid3DCommands.get_grid_name()
        if not grid_name:
            if self.vf.Grid3DCommands.mlb.size() != 0:
                self.ifd.entryByName['Name']['widget'].\
                                   setvalue('Please select grid from the list')
            else:
                self.ifd.entryByName['Name']['widget'].\
                                     setvalue('There a no grids added')
            return
        
        tmp_grid = self.vf.grids3D[grid_name]
        self.vf.grids3D.pop(grid_name)
        new_name = self.ifd.entryByName['Name']['widget'].getvalue()
        tmp_grid.master_geom.Set(name=new_name)
        self.vf.grids3D[new_name] = tmp_grid
        row = self.vf.Grid3DCommands.mlb.curselection()[0]
        l = self.vf.Grid3DCommands.mlb.lists[0]
        l.delete(row)
        l.insert(row,new_name)
        self.vf.Grid3DCommands.mlb.selection_set(row)        
        X = self.ifd.entryByName['X_origin']['widget'].getvalue()
        Y = self.ifd.entryByName['Y_origin']['widget'].getvalue()
        Z = self.ifd.entryByName['Z_origin']['widget'].getvalue()
        tmp_grid.origin = (float(X),float(Y),float(Z))
        dX = self.ifd.entryByName['dX']['widget'].getvalue()
        dY = self.ifd.entryByName['dY']['widget'].getvalue()
        dZ = self.ifd.entryByName['dZ']['widget'].getvalue()
        tmp_grid.stepSize = [float(dX),float(dY),float(dZ)]
        
    def reset(self):
        grid_name = self.vf.Grid3DCommands.get_grid_name()
        if not grid_name:
            return
        tmp_grid = self.vf.grids3D[grid_name]
        self.vf.grids3D.pop(grid_name)
        if hasattr(tmp_grid, 'path'):
            grid_basename = os.path.basename(tmp_grid.path)
        else:
            grid_basename = grid_name
        self.vf.grids3D[grid_basename] = tmp_grid
        tmp_grid.master_geom.Set(name=grid_basename)
        tmp_grid.origin = tmp_grid.origin_copy
        tmp_grid.stepSize = tmp_grid.stepSize_copy
        row = self.vf.Grid3DCommands.mlb.curselection()[0]
        l = self.vf.Grid3DCommands.mlb.lists[0]
        l.delete(row)
        l.insert(row,grid_basename)
        self.vf.Grid3DCommands.mlb.selection_clear(0, Tkinter.END)
        self.vf.Grid3DCommands.mlb.selection_set(row)        
        self.select()
        
AddRemoveGUI = CommandGUI()
AddRemoveGUI.addMenuCommand('menuRoot', 'Grid3D', 'Add/Remove...')
"""
class IGraph(Tkinter.Frame):
    """Extends Tkinter.Frame by adding a canvas with histogram and bars for 
    isocontouring.
    """
    def __init__(self, master, width = width, height = height, 
                 labelsBarFormat = '%4.2f'):
        self.width = width - 10
        self.height = height
        self.offset_y1 = 6
        self.offset_y2 = 20
        self.a_x = 1
        self.b_x = 0
        self.a_y = -1
        self.b_y = height
        self.sig_tags = ['area', 'min_vol', 'max_vol', 'gradient']
        self.colors = ['red', 'green', 'blue', 'orange']#used in Plot Signature
        self.labelsBarFormat = labelsBarFormat
        Tkinter.Frame.__init__(self, master)
        #Tkinter.Grid.config(self)
        self.upperLabel = Tkinter.Label(self, text = "(0, 0)",width=20)
        self.upperLabel.grid(row=0, column=0,sticky='we')
        self.log_var = Tkinter.IntVar()
        self.log_var.set(1)
        self.sig_var = Tkinter.IntVar()
        self.log_cb = Tkinter.Checkbutton(self, text='Logarithmic',anchor="w",
                                          command = self.plot_histogram, 
                                          variable=self.log_var)
        self.log_cb.grid(row=0, column=1,sticky='e')
        self.sig_cb = Tkinter.Checkbutton(self, text='Plot Signature',anchor="e",
                                          command = self.plot_signature, 
                                          variable=self.sig_var)
        self.sig_cb.grid(row=0, column=2,sticky='e')

        #self.canvasFrame = Tkinter.Frame(self)
        #self.canvasFrame.grid(row=1, column=0,columnspan=4, sticky='wens')
        self.canvas = Tkinter.Canvas(self, width=self.width,cursor = 'cross',
                                      highlightbackground = 'blue',
                        height=height,   background='white')
        self.canvas.grid(row=1, column=0,columnspan=3)
                
        self.minEntry = Pmw.ComboBox(self,label_text = 'min',labelpos = 'e',
                                dropdown=1, selectioncommand=self.setMin)
        self.minEntry.grid(row=2, column=0, sticky='w')
        self.minEntry._entryWidget.configure(width=8)
        self.balloon = Pmw.Balloon(self)
        self.balloon.bind(self, "Press Shift and mouse click inside the canvas to add Isocontour")

        self.maxEntry = Pmw.ComboBox(self,label_text = 'max',labelpos = 'w',
                                dropdown=1, selectioncommand=self.setMax)
        self.maxEntry.grid(row=2, column=2, sticky='e')
        self.maxEntry._entryWidget.configure(width=8)

        Tkinter.Widget.bind(self.canvas, "<1>", self.selectMoveBar)
        Tkinter.Widget.bind(self.canvas, "<B1-Motion>", self.moveBar)
        Tkinter.Widget.bind(self.canvas, "<Motion>", self.onMouseOver)
        Tkinter.Widget.bind(self.canvas,'<Button-3>', self.button3)
        Tkinter.Widget.bind(self.canvas,'<Shift-Button-1>', self.addBar)
        
        #Tkinter.Widget.bind(self.canvas, '<Double-Button-1>', self.showDejaVu)        
        #Tkinter.Widget.bind(self, '<Configure>', self.changeSize)        

        self.valueLabel = {}
        self.bar_text = 'IsoSurf_'
        self.isoBarNumber = 0
        self.last_tag = None
        self.canvas.create_rectangle(0,self.offset_y1,self.width, 
                                     self.offset_y1+1,fill='gray68', tag='h_bar')
        self.canvas.create_rectangle(0,self.height - self.offset_y2,self.width, 
                         self.height - self.offset_y2+1,fill='gray68', tag='h_bar')
        
        self.menu = Tkinter.Menu(self.master, title='Isocontour - Menu')
        
        self.menu.add_command(label='Set IsoValue...',command=self.isoValueGUI) 
        self.menu.add_command(label='Color...',command=self.setColor) 
        self.menu.add_command(label='Set 3D Surface Properties...',
                              command=self.showDejaVu) 
        self.menu.add_command(label='Hide', command=self.hideShowIso)         
#        self.menu.add_command(label='Transparency',command=self.setTransparency)                 
        self.menu.add_command(label='Delete',command=self.deleteCB) 
        self.menu.add_command(label='Cancel',command=self.cancelManu)
        self.menu.bind('<FocusOut>', self.cancelManu)

    def cancelManu(self, event=None):
        self.menu.unpost()

    def changeSize(self, event):
        self.canvas.scale('all',0,0,float(event.width)/float(self.width), 
                          float(event.height)/float(self.height) )
        self.width = event.width
        self.height = event.height
        
    def plot_signature(self):
        if not self.cmd.grid:
            return
        for s in range(4):
            self.canvas.delete(self.sig_tags[s])
        if not self.sig_var.get():            
            return     
        self.cmd.vf.Grid3DCommands.root.configure(cursor='watch')
        self.cmd.vf.Grid3DCommands.PanedWindow.config(cursor='watch')
        self.cmd.vf.Grid3DCommands.root.update()  
        for s in range(4):
            if hasattr(self.cmd.grid,'signature'):
                sig = self.cmd.grid.signature[s]
            else:
                self.cmd.grid.signature = []
                for si in range(4):
                    self.cmd.grid.signature.append(
                                       self.cmd.iso_data.getSignature(0, 0, si))
                sig =self.cmd.grid.signature[s]               
            x = Numeric.zeros( (sig.nval,), 'f')
            sig.getFx(x)
            y = Numeric.zeros( (sig.nval,), 'f')
            sig.getFy(y)
            max_y = max(y)
            min_y = min(y)
            a_y = (self.offset_y1 - self.height + self.offset_y2)/(max_y - min_y)
            b_y = self.height - self.offset_y2 - a_y*min_y
            coords = []
            for i in range(len(x)):
                screen_x = self.a_x*x[i] + self.b_x
                screen_y = a_y*y[i] + b_y
                coords.append(screen_x)
                coords.append(screen_y)
            self.canvas.create_line( coords,fill=self.colors[s], tag=self.sig_tags[s] )
            self.canvas.create_text( self.width-40 , 15*s + self.offset_y2, 
                                     fill=self.colors[s],
                                     text=sig.name,  tag=self.sig_tags[s])
        self.cmd.vf.Grid3DCommands.root.configure(cursor='')
        self.cmd.vf.Grid3DCommands.PanedWindow.config(cursor='')

    def plot_histogram(self, event = None, data = None):  
        if data is not None:
            self.data = data
        elif not hasattr(self, 'data'):
            return
        self.canvas.delete("rect")
        x = self.data[1].tolist()
        y = self.data[0].tolist()
        self.min_x = self.cmd.grid.hist[1][0]
        self.max_x = self.cmd.grid.hist[1][-1]
        self.maxEntry.setentry((self.labelsBarFormat)%self.max_x)
        self.minEntry.setentry((self.labelsBarFormat)%self.min_x)
        self.min_y = min(y)
        self.max_y = max(y)

        if self.log_var.get():            
            for i in range(len(y)):
                if y[i] != 0:
                    y[i] = math.log10(float(y[i]))
        self.min_y = min(y)
        self.max_y = max(y)
        self.update_a_b()
        for i in range(len(x)):
            screen_x = self.a_x*x[i] + self.b_x
            screen_y = self.a_y*y[i] + self.b_y
            self.canvas.create_rectangle(screen_x, screen_y, 
                                 screen_x+2, self.height - self.offset_y2, 
                                 outline="gray70", fill="gray70", tag = 'rect')
        for tag in self.cmd.grid.isoBarTags:
            newX = self.a_x*self.cmd.grid.isoLastX[tag] + self.b_x
            if newX < -1 or newX > self.width+1:
                self.canvas.itemconfig(self.valueLabel[tag], state='hidden')
                self.canvas.itemconfig(tag, state='hidden')
            else:
                coords = self.canvas.coords(self.valueLabel[tag])   
                self.canvas.coords(self.valueLabel[tag],newX,coords[1])   
                items = self.canvas.find_withtag(tag)
                for item in items[0:-2]:
                    coords = self.canvas.coords(item) 
                    coords[0] = newX-5
                    coords[2] = newX+5    
                    self.canvas.coords(item,coords[0],coords[1],coords[2],coords[3])   
                coords = self.canvas.coords(items[2]) 
                coords[0] = newX-1
                coords[2] = newX+1    
                self.canvas.coords(items[2],coords[0],coords[1],coords[2],coords[3])   
                                
                self.canvas.itemconfig(self.valueLabel[tag], state='normal')
                self.canvas.itemconfig(tag, state='normal')   
                self.canvas.lift(tag)
        
    def setMin(self, text):
        try:
            hMin = float(text)
        except ValueError:
            self.minEntry.setentry(str(self.min_x))
            return
        bound = [hMin,self.cmd.grid.hist[1][-1]]
        hist = numpy.histogram(self.cmd.grid.data.copy().flat,bins=self.width+100, range=bound)
        self.cmd.grid.hist = hist
        self.data = hist
        self.plot_histogram()
        self.plot_signature()
        
    def setMax(self, text):
        try:
            hMax = float(text)
        except ValueError:
            self.maxEntry.setentry(str(self.max_x))
            return
        bound = [self.cmd.grid.hist[1][0],hMax]
        hist = numpy.histogram(self.cmd.grid.data.copy().flat,bins=self.width+100, range=bound)
        self.cmd.grid.hist = hist
        self.data = hist
        self.plot_histogram()
        self.plot_signature()
        
    def onMouseOver(self, event):
        x = (event.x - self.b_x)/self.a_x
        x = (self.labelsBarFormat)%x
        y = (event.y - self.b_y)/self.a_y
        y = (self.labelsBarFormat)%y
        self.upperLabel.configure(text = "( " + x + " , " + y + " )")
        
    def update_a_b(self):
        if self.max_x == self.min_x:
            print 'Error: min and max for the X axis are equal ', self.max_x
            self.a_x = 10000000000000000000000000000000000000000
        else:
            self.a_x = self.width/float((self.max_x - self.min_x))
        self.b_x = -self.a_x*self.min_x
        if self.max_y == self.min_y:
            print 'Error: min and max for the Y axis are equal ', self.max_y
            self.a_y = 10000000000000000000000000000000000000000
        else:
            self.a_y = (self.offset_y1 - self.height + self.offset_y2)/\
                                                       float((self.max_y - self.min_y))
        self.b_y = self.height - self.offset_y2 - self.a_y*self.min_y

    def drawBar(self, x, isoBarNumber=0, doit=True, color="#ff00ff", alpha=0.5, tag = None):
        bbox = x - 5, self.offset_y1 - 5, x + 5, self.offset_y1 + 5
        if tag is not None:
            tag = tag
        else:
            tag = self.bar_text + str(isoBarNumber)
        self.canvas.create_arc(bbox, extent=180, tags=(tag,tag+"cap"))
        bbox = x - 5, self.height - self.offset_y2 -4, x + 5, \
                                               self.height - self.offset_y2 + 7
        self.canvas.create_arc(bbox, start=180, extent=180, tags=(tag,tag+"cap"))
        self.canvas.create_rectangle(x - 1, self.offset_y1, x + 1, 
                                     self.height - self.offset_y2 + 2, 
                                     tag=tag, fill='red', activefill='gray68')
        val = (x - self.b_x)/self.a_x
        lv = (self.labelsBarFormat)%val
        self.valueLabel[tag] = self.canvas.create_text(x,
                              self.height - self.offset_y2+15, text=lv, tag=tag)
        self.cmd.grid.isoLastX[tag] = val
        invertNormals = False
        if val<0:
            invertNormals = True        
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        if doit:
            self.cmd.doit(self.cmd.grid, name=tag, isovalue=val, 
                          invertNormals=invertNormals, 
                          material=(r/255., g/255., b/255, alpha))
        self.canvas.itemconfig(tag, fill=color)    
        
    def addBar(self, event):
        if not self.cmd.grid:
            tkMessageBox.showerror("Error: No grid selected", 
                                   "Please select grid first.", parent=self)
            return
        self.isoBarNumber += 1
        self.cmd.grid.isoBarNumber = self.isoBarNumber
        tag = self.bar_text + str(self.isoBarNumber)
        
        # this part was taken from ASPN/Cookbook/Python/Recipe/52273
        x = float(event.x)/float(self.width)
        yellow = min((max((4*(0.75-x), 0.)), 1.))
        red  = min((max((4*(x-0.25), 0.)), 1.))
        green= min((max((4*math.fabs(x-0.5)-1., 0.)), 1.))    
        
        color = (int(red*255), int(green*255), int(yellow*255))
        hexcolor = '#%02x%02x%02x' % color
        self.cmd.grid.isoLastColor[tag] = hexcolor
        self.drawBar(event.x, self.isoBarNumber, color=hexcolor)
        self.canvas.lift(tag)    
        
        if self.last_tag in self.cmd.grid.isoLastColor.keys():
            self.canvas.itemconfig(self.last_tag + "cap", 
                                 fill=self.cmd.grid.isoLastColor[self.last_tag])  
        self.last_tag = tag      
        self.canvas.itemconfig(tag + "cap", fill='gray68')  
        self.cmd.grid.isoBarTags.append(tag)
        self.balloon.bind(self, rightClick +" on the bar for Options")
        
        
    def deleteCB(self):
        self.canvas.delete(self.selected_tag)
        name = '|' + self.cmd.grid.master_geom.name
        self.cmd.grid.geomContainer['IsoSurf'].pop(self.selected_tag)
        name = name + '|' + 'IsoSurf' + '|' + self.selected_tag
        g = self.cmd.vf.GUI.VIEWER.FindObjectByName(name)
        self.cmd.vf.GUI.VIEWER.RemoveObject(g)
        self.isoBarNumber -= 1
        self.cmd.grid.isoBarNumber = self.isoBarNumber
        if self.last_tag == self.selected_tag:
            self.last_tag = self.cmd.grid.isoBarTags[0]
        self.cmd.grid.isoBarTags.remove(self.selected_tag)
        self.cmd.grid.isoLastColor.pop(self.selected_tag)
        self.cmd.grid.isoLastX.pop(self.selected_tag)
        self.cmd.vf.GUI.VIEWER.Redraw()        
        self.balloon.unbind(self.canvas)
        
    def showDejaVu(self):
        tag = self.selected_tag
        if not self.cmd.vf.GUI.VIEWER.GUI.shown:
            self.cmd.vf.GUI.showHideDejaVuGUI()
        name = '|' + self.cmd.grid.master_geom.name
        name = name + '|' + 'IsoSurf' + '|' + tag
        g = self.cmd.vf.GUI.VIEWER.FindObjectByName(name)
        self.cmd.vf.GUI.VIEWER.SetCurrentObject(g)
        
    def selectMoveBar(self, event):
        self.menu.unpost()
        if not self.isoBarNumber:
            self.onMouseOver(event)
            return
        x = event.x
        if  x < 0:
            x = 0
        if x > self.width:
            x = self.width
        tag = self.canvas.find_closest(event.x,event.y, halo=2)
        tag = self.canvas.gettags(tag)
        if tag:
            if tag[0] in self.cmd.grid.isoBarTags:
                tag = tag[0]
                if self.last_tag:
                    self.canvas.itemconfig(self.last_tag+"cap", 
                                 fill=self.cmd.grid.isoLastColor[self.last_tag])  
                self.last_tag = tag
                self.canvas.itemconfig(tag+"cap", fill='gray68')  
            elif self.isoBarNumber > 0:
                tag = self.last_tag
            else:
                self.onMouseOver(event)
                return
        else:
            self.onMouseOver(event)
            return

        val = (x - self.b_x)/self.a_x
        invertNormals = False
        if val<0:
            invertNormals = True        
        #move with delta worked here until we let user change the min and max
        
        self.canvas.delete(tag)   
        self.drawBar(x, doit=False, color=self.cmd.grid.isoLastColor[tag], tag=tag)

        self.cmd.grid.isoLastX[tag] = val
        self.cmd.doit(self.cmd.grid, name=tag, isovalue=val,
                                                    invertNormals=invertNormals)
        self.onMouseOver(event)

    def moveBar(self, event):
        self.menu.unpost()        
        if not self.isoBarNumber:
            self.onMouseOver(event)
            return
        x = event.x
        if  x < 0:
            x = 0
        if x > self.width:
            x = self.width       
        tag = self.last_tag
        delta_x = x - self.a_x*self.cmd.grid.isoLastX[tag] - self.b_x
        val = (x - self.b_x)/self.a_x      
        invertNormals = False
        if val<0:
            invertNormals = True        
        self.canvas.itemconfig(self.valueLabel[tag], text = (self.labelsBarFormat)%val )
        self.canvas.move(tag, delta_x, 0 )
        self.cmd.grid.isoLastX[tag] = val
        self.cmd.doit(self.cmd.grid, name=tag, isovalue=val,
                                                    invertNormals=invertNormals)
        self.onMouseOver(event)
    
    def button3(self, event):
        if not self.cmd.grid:
            return
        tag = self.canvas.find_closest(event.x,event.y)
        tag = self.canvas.gettags(tag)
        if tag:
            if tag[0] in self.cmd.grid.isoBarTags:
                tag = tag[0]
                self.selected_color = self.canvas.itemcget(tag,'fill')
                if self.cmd.grid.geomContainer['IsoSurf'][tag].visible:
                    self.menu.entryconfig(4,label="Hide")
                else:
                    self.menu.entryconfig(4,label="Show")
                self.menu.post(event.x_root, event.y_root)
                self.selected_tag = tag

                if widgetsOnBackWindowsCanGrabFocus is False:
                    lActiveWindow = self.menu.focus_get()
                    if    lActiveWindow is not None \
                      and ( lActiveWindow.winfo_toplevel() != self.menu.winfo_toplevel() ):
                        return
                self.menu.focus_set() 

    def setColor(self):
        tag = self.selected_tag
        rgb, hex = askcolor(self.selected_color,title='Choose Color')
        if rgb:
            self.cmd.grid.geomContainer['IsoSurf'][tag].Set(materials=\
                          [(rgb[0]/255.,rgb[1]/255.,rgb[2]/255.,0.5),],)
            #I'm not sure why this is needed but without this Set doen't work
            self.cmd.grid.geomContainer['IsoSurf'][tag].redoNow(1,1,4)
            
            self.canvas.itemconfig(tag,fill=hex)
            self.cmd.grid.isoLastColor[tag] = str(hex)
            
    def isoValueGUI(self):
        self.isoValueDialog = Pmw.PromptDialog(self, title = 'Set isoValue',
                                       label_text = 'Please enter isoValue',
                                       entryfield_labelpos = 'n',
                                       defaultbutton = 0,
                                       buttons = ('OK', 'Cancel'),
                                       command = self.setIsoValue)
        self.isoValueDialog.insertentry(0, 
                                        self.cmd.grid.isoLastX[self.selected_tag])
        self.isoValueDialog.activate()
        
    def setIsoValue(self, result):
        if result is None or result == 'Cancel':
            self.isoValueDialog.deactivate()
            return     
        try:
            val = float(self.isoValueDialog.get())
        except Exception, inst:
            print inst
            self.isoValueDialog.deactivate()
            return    
        
        if val > self.max_x:
            val = self.max_x
        if val < self.min_x:
            val = self.min_x
        tag = self.selected_tag
        delta_x = self.a_x*(val-self.cmd.grid.isoLastX[tag])
        delta_x = int(delta_x)
        invertNormals = False
        if val<0:
            invertNormals = True        
        
        self.canvas.itemconfig(self.valueLabel[tag], text=(self.labelsBarFormat)%val )       
        self.canvas.move(tag, delta_x, 0 )
        self.cmd.grid.isoLastX[tag] = val
        self.cmd.doit(self.cmd.grid, name=tag, isovalue=val,
                                                    invertNormals=invertNormals)
        self.isoValueDialog.deactivate()

    def hideShowIso(self):
        tag = self.selected_tag
        surfaceGeom = self.cmd.grid.geomContainer['IsoSurf'][tag]
        if surfaceGeom.visible:
            surfaceGeom.Set(visible=False)
            self.menu.entryconfig('Hide',label="Show")
        else:
            surfaceGeom.Set(visible=True)
            self.menu.entryconfig('Show',label="Hide")

    def setTransparency(self):
        tag = self.selected_tag
        root = Tkinter.Toplevel()
        root.title("Set Transparency - %s"%self.cmd.grid.master_geom.name)
        surfaceGeom = self.cmd.grid.geomContainer['IsoSurf'][tag]
        transparencySl = ExtendedSlider(root, label='  Transparency', minval=0.0,
                   maxval=1.0, init=1 - surfaceGeom.materials[GL.GL_FRONT].prop[5][0],
                   sd='left', withValue=0, immediate=1)
        transparencySl.AddCallback(self.opacity_cb)
        transparencySl.frame.pack(side='top', expand=1, fill='y')

    def opacity_cb(self, val):
        tag = self.selected_tag
        surfaceGeom = self.cmd.grid.geomContainer['IsoSurf'][tag]
        surfaceGeom.Set(opacity=1-val)

        self.cmd.vf.GUI.VIEWER.Redraw()   
        
class IsocontourCommand(Command):
    """IsocontourCommand calculates and displays isocontours for any given gridname
gridname, material = (0.,0.,1.0,0.5), isovalue = None , 
             name = None, invertNormals = False
   \nPackage : ViewerFramework
   \nModule  : grid3DCommands
   \nClass   : IsocontourCommand
   \nCommand : isocontour
   \nSynopsis:\nfF
        None<-isocontour(gridname)\n
   \nRequired Arguments:\n    
        grid3D  : grids3D object\n
   \nOptional Arguments:\n  
        isovalue : if None given, uses the first element in the Grid3D \n
        material : defaults to (0.,0.,1.0,0.5) - yellow half transparent\n
        name     : the name given to IndexedPolygons that represents isocontour.\n   
        invertNormals : defaults to False
    """
    def __init__(self, func=None):
        Command.__init__(self)
        self.ifd = InputFormDescr(title = "Isocontour")
        self.ifd.append({'name':'iso',
                    'widgetType':IGraph,
                    'wcfg':{'width':width,
                            'height':height-50},
                    'gridcfg':{'row':0, 'column':0, 'sticky':'wens'}
                    })
        self.grid = None
        self.iso_data = None
        
    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'grids3D'):
            self.vf.grids3D={}
        self.ifd[0]['widgetType'].cmd = self
        
    def __call__(self, grid3D, **kw):
        """None<-isocontour(gridname)\n
   \nRequired Arguments:\n    
        grid3D  : key for self.vf.grids3D object\n
   \nOptional Arguments:\n  
        isovalue : if None given, uses the first element in the Grid3D \n
        material : defaults to (0.,0.,1.0,0.5) - yellow half transparent\n
        name     : the name given to IndexedPolygons that represents isocontour.\n   
        invertNormals : defaults to False """
        return apply(self.doitWrapper, (grid3D,), kw)

    def doit(self, grid3D, material = None, isovalue = None , 
             name = None, invertNormals = False):
        if type(grid3D) in types.StringTypes:
            if self.vf.grids3D.has_key(grid3D):
                grid3D = self.vf.grids3D[grid3D]
            else:
                print "ERROR!!! "+ grid3D + "is not in the self.vf.grids3D"
        if isovalue == None:
            isovalue = float(grid3D.data[0][0][0])
        isoc = isocontour.getContour3d(self.iso_data, 0, 0, isovalue,
                                       isocontour.NO_COLOR_VARIABLE)
        
        vert = Numeric.zeros((isoc.nvert,3)).astype('f')
        norm = Numeric.zeros((isoc.nvert,3)).astype('f')
        col = Numeric.zeros((isoc.nvert)).astype('f')
        tri = Numeric.zeros((isoc.ntri,3)).astype('i')

        if invertNormals:
            isocontour.getContour3dData(isoc, vert, norm, col, tri, 1)
        else:
            isocontour.getContour3dData(isoc, vert, norm, col, tri, 0)

        if grid3D.crystal:
            vert = grid3D.crystal.toCartesian(vert)

        if not name:
            name = "Grid3D_Iso_%4.4f"%isovalue
        if name in  grid3D.geomContainer['IsoSurf']:
            g = grid3D.geomContainer['IsoSurf'][name]
        else:
            g = IndexedPolygons(name)
            if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
                g.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False,)
            g.Set(culling='none')
            g.Set(vertices=vert,vnormals=norm,faces=tri)
            if self.vf.hasGui : self.vf.GUI.VIEWER.AddObject(g, parent = grid3D.IsoSurf)
            grid3D.geomContainer['IsoSurf'][name] = g

        if material:
            g.inheritMaterial = False
            g.Set(materials=[material,],)

        g.Set(vertices=vert,vnormals=norm,faces=tri)
        if self.vf.hasGui :
            if vert is not None:
                g.sortPoly()
            self.vf.GUI.VIEWER.Redraw()
        event = EditGeomsEvent('iso', [grid3D,[name,isovalue]])
        self.vf.dispatchEvent(event)
            
        return g
    
    def select(self,grid_name=None):
        if grid_name == None and self.vf.hasGui:
            entry = self.ifd.entryByName['iso']
            grid_name = self.vf.Grid3DCommands.get_grid_name()
            isoBarNumber = entry['widget'].isoBarNumber 
            if not grid_name:
                self.vf.Grid3DCommands.root.configure(cursor='')
                self.vf.Grid3DCommands.PanedWindow.config(cursor='')    
                for i in range(1, isoBarNumber + 1):
                    tag = entry['widget'].bar_text + str(i)
                    entry['widget'].canvas.delete(tag)                
                entry['widget'].canvas.delete("rect")
                self.grid = None
                return
        grid = self.vf.grids3D[grid_name]
        if not hasattr(grid,'hist'):
            bound = None #this is used to set the limits on the histogram
            if grid_name.endswith('.map'):
                if grid.mini < 0:
                    bound = [grid.mini,-grid.mini]
            if self.vf.hasGui : bins =   entry['widget'].width+100
            else : bins = 101 #????
            hist = numpy.histogram(grid.data.copy().flat,bins=bins)
            grid.hist = hist
        if not hasattr(grid,'isoBarNumber'):
            grid.isoLastX = {}
            grid.isoLastColor = {}
            grid.isoBarNumber = 0
            grid.isoBarTags = []

        if self.vf.hasGui:
            for i in range(1, isoBarNumber + 1):
                tag = entry['widget'].bar_text + str(i)
                entry['widget'].canvas.delete(tag)
                
            self.vf.Grid3DCommands.root.config(cursor='watch')            
            self.vf.Grid3DCommands.PanedWindow.config(cursor='watch')            
            self.vf.Grid3DCommands.root.update()            
        
        self.grid = grid
        if self.vf.hasGui:
            entry['widget'].isoBarNumber = self.grid.isoBarNumber
        origin = Numeric.array(grid.origin).astype('f')
        stepsize = Numeric.array(grid.stepSize).astype('f')
        data = grid.data
        if data.dtype != Numeric.Float32:
            print 'converting %s from %s to float'%(grid_name,data.dtype)
            data = data.astype('f')
        self.newgrid3D = Numeric.ascontiguousarray(Numeric.reshape( Numeric.transpose(data),
                                              (1, 1)+tuple(data.shape) ) , data.dtype.char)
        if self.iso_data:
            isocontour.delDatasetReg(self.iso_data)
        self.iso_data = isocontour.newDatasetRegFloat3D(self.newgrid3D, origin, 
                                                        stepsize)
        if self.vf.hasGui:
            for i in range(1, grid.isoBarNumber+1):
                tag = grid.isoBarTags[i-1]
                x = entry['widget'].a_x*grid.isoLastX[tag] + entry['widget'].b_x
                entry['widget'].drawBar(x, i, doit=False, 
                                        color=grid.isoLastColor[tag])
                #entry['widget'].canvas.lift(tag)    
            entry['widget'].plot_signature()
            entry['widget'].plot_histogram(data=self.grid.hist)
            entry['widget'].canvas.tag_raise('h_bar')
            self.vf.Grid3DCommands.root.configure(cursor='')
            self.vf.Grid3DCommands.PanedWindow.config(cursor='')
        
displayIsocontourGUI = CommandGUI()
displayIsocontourGUI.addMenuCommand('menuRoot', 'Grid3D', 'Isocontour...')

class OrthoSliceCommand(Command):
    def __init__(self, func=None):
        Command.__init__(self)
        self.ifd = InputFormDescr(title="OrthoSlice")
        self.X_vis = Tkinter.BooleanVar()
        self.X_vis.set(1)
        self.Y_vis = Tkinter.BooleanVar()
        self.Z_vis = Tkinter.BooleanVar()
        self.grid = None
        
        self.ifd.append({'widgetType':Pmw.Group, 'name':'XGroup',
                         'container':{'XGroup':'w.interior()'},
                         'wcfg':{'tag_pyclass':Tkinter.Checkbutton,
                                 'tag_text':'X Direction',
                                 'tag_command':self.createX,
                                 'tag_variable': self.X_vis, 
                                 },
                     'gridcfg':{'sticky':'we','columnspan':2} })
                
        self.ifd.append({'name':'X_Slice', 'widgetType':Tkinter.Scale,
                         'parent':'XGroup',                         
                         'wcfg':{'orient':'horizontal','sliderrelief':'sunken',
                                 'sliderlength':10,'width':12,
                                 'troughcolor':'red', 'command':self.X_Slice},
                         'gridcfg':{'row':0, 'column':0,'sticky':'ew',
                                    'weight':10}})

        self.ifd.append({'name':'X_ColorMap', 'widgetType':Tkinter.Button,
                         'parent':'XGroup',                         
                         'wcfg':{'text':'Colormap', 'command':self.X_ColorMap},
                         'gridcfg':{'row':0, 'column':1,'sticky':'se'}
                        })

        self.ifd.append({'widgetType':Pmw.Group, 'name':'YGroup',
                         'container':{'YGroup':'w.interior()'},
                         'wcfg':{'tag_pyclass':Tkinter.Checkbutton,
                                 'tag_text':'Y Direction',
                                 'tag_command':self.createY,
                                 'tag_variable': self.Y_vis, 
                                 }, 
                         'gridcfg':{'sticky':'we','columnspan':2} })
                
        self.ifd.append({'name':'Y_Slice', 'widgetType':Tkinter.Scale,
                         'parent':'YGroup',                         
                         'wcfg':{'orient':'horizontal','sliderrelief':'sunken',
                                 'sliderlength':10,'width':12,
                                 'troughcolor':'red', 'command':self.Y_Slice},
                         'gridcfg':{'row':0, 'column':0,'sticky':'ew',
                                    'weight':10} })

        self.ifd.append({'name':'Y_ColorMap', 'widgetType':Tkinter.Button,
                         'parent':'YGroup',                         
                         'wcfg':{'text':'Colormap', 'command':self.Y_ColorMap},
                         'gridcfg':{'row':0, 'column':1,'sticky':'se'}
                        })

        self.ifd.append({'widgetType':Pmw.Group, 'name':'ZGroup',
                         'container':{'ZGroup':'w.interior()'},
                         'wcfg':{'tag_pyclass':Tkinter.Checkbutton,
                                 'tag_text':'Z Direction',
                                 'tag_command':self.createZ,
                                 'tag_variable': self.Z_vis, 
                                 },
                         'gridcfg':{'sticky':'we','columnspan':2} })
                
        self.ifd.append({'name':'Z_Slice', 'widgetType':Tkinter.Scale,
                         'parent':'ZGroup',                         
                         'wcfg':{'orient':'horizontal','sliderrelief':'sunken',
                                 'sliderlength':10,'width':12,
                                 'troughcolor':'red', 'command':self.Z_Slice},
                         'gridcfg':{'row':0, 'column':0,'sticky':'ew',
                                    'weight':10} })

        self.ifd.append({'name':'Z_ColorMap', 'widgetType':Tkinter.Button,
                         'parent':'ZGroup',                         
                         'wcfg':{'text':'Colormap', 'command':self.Z_ColorMap},
                         'gridcfg':{'row':0, 'column':1,'sticky':'se'}
                        })

    def X_ColorMap(self):
        if not self.X_vis.get():
            return
        elif self.grid:
            colormap = self.grid.geomContainer['OrthoSlice']['X'].colormap
            name = "X Slice - " 
            name += self.vf.Grid3DCommands.get_grid_name()
            colormap.name = name
            self.X_ColorMapGUI = ColorMapGUI(cmap=colormap,modifyMinMax=True)
            self.X_ColorMapGUI.addCallback( self.X_ColorMap_cb )
            self.ifd.entryByName['X_ColorMap']['widget'].configure(state='disabled')
            
            def dismissXCmap():
                self.ifd.entryByName['X_ColorMap']['widget'].configure(state='normal')
                if self.X_ColorMapGUI.master.winfo_ismapped():
                    self.X_ColorMapGUI.master.withdraw()

            self.X_ColorMapGUI.dismiss.configure(command = dismissXCmap)
            self.X_ColorMapGUI.master.protocol('WM_DELETE_WINDOW', dismissXCmap)
        else:
            parent = self.vf.Grid3DCommands.root
            tkMessageBox.showerror("Error: No grid selected", 
                                   "Please add and select grid first.", parent=parent)
                
    def X_ColorMap_cb(self, colorMap):
        self.grid.geomContainer['OrthoSlice']['X'].Set(colormap=colorMap)
                
    def X_Slice(self, event):
        if not self.X_vis.get():
            return
        elif self.grid:
            data, vertices = self.grid.get2DOrthoSlice('x', int(event))
            geom = self.grid.geomContainer['OrthoSlice']['X']
            geom.Set(vertices=vertices, array=data)
            self.grid._X_Slice = int(event)
            self.grid._X_Vis = True
            self.vf.GUI.VIEWER.Redraw()
#        else:
#            parent = self.vf.Grid3DCommands.root
#            tkMessageBox.showerror("Error: No grid selected", 
#                                   "Please add and select grid first.", parent=parent)
           
    def createX(self):
        if not self.grid:
            return
        if self.X_vis.get():
            geom = textured2DArray('OrthoSlice_X',
                                   inheritLighting=False,
                                   lighting=False)
            self.vf.GUI.VIEWER.AddObject(geom, parent=self.grid.OrthoSlice)
            self.grid.geomContainer['OrthoSlice']['X'] = geom
            slice_number = self.ifd.entryByName['X_Slice']['widget'].get()
            data, vertices = self.grid.get2DOrthoSlice('x', slice_number)
            self.grid._X_Slice = slice_number
            self.grid._X_Vis = True
            geom.Set(vertices=vertices, array=data)
            if hasattr(self.grid, 'path') and self.grid.path.endswith('.map'):
                if self.grid.mini < 0:
                    geom.Set(max=-self.grid.mini, min=self.grid.mini)
                else:
                    geom.Set(max=self.grid.maxi, min=self.grid.mini)
            else:
                geom.Set(max=self.grid.maxi, min=self.grid.mini)
            
            self.ifd.entryByName['XGroup']['widget'].expand()
        else:
            name = '|' + self.grid.master_geom.name + '|' + 'OrthoSlice' + \
                                                      '|' + 'OrthoSlice_X'
            geom = self.vf.GUI.VIEWER.FindObjectByName(name)
            self.vf.GUI.VIEWER.RemoveObject(geom)
            self.grid.geomContainer['OrthoSlice'].pop('X')
            self.ifd.entryByName['XGroup']['widget'].collapse()            
            self.grid._X_Vis = False
        self.vf.GUI.VIEWER.Redraw()


    def Y_Slice(self, event):
        if not self.Y_vis.get():
            return
        elif self.grid:
            data, vertices = self.grid.get2DOrthoSlice('y', int(event))
            geom = self.grid.geomContainer['OrthoSlice']['Y']
            geom.Set(vertices=vertices, array=data)
            self.grid._Y_Slice = int(event)
            self.grid._Y_Vis = True
            self.vf.GUI.VIEWER.Redraw()
#        else:
#            parent = self.vf.Grid3DCommands.root
#            tkMessageBox.showerror("Error: No grid selected", 
#                                   "Please add and select grid first.", parent=parent)
           
    def createY(self):
        if not self.grid:
            return        
        if self.Y_vis.get():
            geom = textured2DArray('OrthoSlice_Y',
                                   inheritLighting=False,
                                   lighting=False)
            self.vf.GUI.VIEWER.AddObject(geom, parent=self.grid.OrthoSlice)
            self.grid.geomContainer['OrthoSlice']['Y'] = geom
            slice_number = self.ifd.entryByName['Y_Slice']['widget'].get()
            data, vertices = self.grid.get2DOrthoSlice('y', slice_number)
            geom.Set(vertices=vertices, array=data)
            if hasattr(self.grid, 'path') and self.grid.path.endswith('.map'):
                if self.grid.mini < 0:
                    geom.Set(max=-self.grid.mini, min=self.grid.mini)
                else:
                    geom.Set(max=self.grid.maxi, min=self.grid.mini)
            else:
                geom.Set(max=self.grid.maxi, min=self.grid.mini)
            self.ifd.entryByName['YGroup']['widget'].expand()
            self.grid._Y_Slice = slice_number
            self.grid._Y_Vis = True            
        else:
            name = '|' + self.grid.master_geom.name + '|' + 'OrthoSlice' + \
                                                      '|' + 'OrthoSlice_Y'
            geom = self.vf.GUI.VIEWER.FindObjectByName(name)
            self.vf.GUI.VIEWER.RemoveObject(geom)
            self.grid.geomContainer['OrthoSlice'].pop('Y')
            self.ifd.entryByName['YGroup']['widget'].collapse()
            self.grid._Y_Vis = False            
        self.vf.GUI.VIEWER.Redraw()

    def Y_ColorMap(self):
        if not self.Y_vis.get():
            return
        elif self.grid:
            colormap = self.grid.geomContainer['OrthoSlice']['Y'].colormap
            name = "Y Slice - " 
            name += self.vf.Grid3DCommands.get_grid_name()
            colormap.name = name
            self.Y_ColorMapGUI = ColorMapGUI(cmap=colormap, modifyMinMax=True)
            self.Y_ColorMapGUI.addCallback( self.Y_ColorMap_cb )
            self.ifd.entryByName['Y_ColorMap']['widget'].configure(state='disabled')
            
            def dismissYCmap():
                self.ifd.entryByName['Y_ColorMap']['widget'].configure(state='normal')
                if self.Y_ColorMapGUI.master.winfo_ismapped():
                    self.Y_ColorMapGUI.master.withdraw()

            self.Y_ColorMapGUI.dismiss.configure(command = dismissYCmap)
            self.Y_ColorMapGUI.master.protocol('WM_DELETE_WINDOW', dismissYCmap)
        else:
            parent = self.vf.Grid3DCommands.root
            tkMessageBox.showerror("Error: No grid selected", 
                                   "Please add and select grid first.", parent=parent)
            
    def Y_ColorMap_cb(self, colorMap):
        self.grid.geomContainer['OrthoSlice']['Y'].Set(colormap=colorMap)


    def Z_Slice(self, event):
        if not self.Z_vis.get():
            return
        elif self.grid:
            data, vertices = self.grid.get2DOrthoSlice('z', int(event))
            geom = self.grid.geomContainer['OrthoSlice']['Z']
            geom.Set(vertices=vertices, array=data)
            self.grid._Z_Slice = int(event)
            self.grid._Z_Vis = True
            self.vf.GUI.VIEWER.Redraw()
#        else:
#            parent = self.vf.Grid3DCommands.root
#            tkMessageBox.showerror("Error: No grid selected", 
#                                   "Please add and select grid first.", parent=parent)
           
    def createZ(self):
        if not self.grid:
            return        
        if self.Z_vis.get():
            geom = textured2DArray('OrthoSlice_Z',
                                   inheritLighting=False,
                                   lighting=False)
            self.vf.GUI.VIEWER.AddObject(geom, parent=self.grid.OrthoSlice)
            self.grid.geomContainer['OrthoSlice']['Z'] = geom
            slice_number = self.ifd.entryByName['Z_Slice']['widget'].get()
            data, vertices = self.grid.get2DOrthoSlice('z', slice_number)
            geom.Set(vertices=vertices, array=data)
            if hasattr(self.grid, 'path') and self.grid.path.endswith('.map'):
                if self.grid.mini < 0:
                    geom.Set(max=-self.grid.mini, min=self.grid.mini)
                else:
                    geom.Set(max=self.grid.maxi, min=self.grid.mini)
            else:
                geom.Set(max=self.grid.maxi, min=self.grid.mini)
            self.ifd.entryByName['ZGroup']['widget'].expand()
            self.grid._Z_Slice = slice_number
            self.grid._Z_Vis = True            
        else:
            name = '|' + self.grid.master_geom.name + '|' + 'OrthoSlice' + \
                                                      '|' + 'OrthoSlice_Z'
            geom = self.vf.GUI.VIEWER.FindObjectByName(name)
            self.vf.GUI.VIEWER.RemoveObject(geom)
            self.grid.geomContainer['OrthoSlice'].pop('Z')
            self.ifd.entryByName['ZGroup']['widget'].collapse()
            self.grid._Z_Vis = False
        self.vf.GUI.VIEWER.Redraw()

    def Z_ColorMap(self):       
        if not self.Z_vis.get():
            return
        elif self.grid:
            colormap = self.grid.geomContainer['OrthoSlice']['Z'].colormap
            name = "Z Slice - " 
            name += self.vf.Grid3DCommands.get_grid_name()
            colormap.name = name
            self.Z_ColorMapGUI = ColorMapGUI(cmap=colormap, modifyMinMax=True)
            self.Z_ColorMapGUI.addCallback( self.Z_ColorMap_cb )
            self.ifd.entryByName['Z_ColorMap']['widget'].configure(state='disabled')
            
            def dismissZCmap():
                self.ifd.entryByName['Z_ColorMap']['widget'].configure(state='normal')
                if self.Z_ColorMapGUI.master.winfo_ismapped():
                    self.Z_ColorMapGUI.master.withdraw()

            self.Z_ColorMapGUI.dismiss.configure(command = dismissZCmap)
            self.Z_ColorMapGUI.master.protocol('WM_DELETE_WINDOW', dismissZCmap)
        else:
            parent = self.vf.Grid3DCommands.root
            tkMessageBox.showerror("Error: No grid selected", 
                                   "Please add and select grid first.", parent=parent)
            
    def Z_ColorMap_cb(self, colorMap):
        self.grid.geomContainer['OrthoSlice']['Z'].Set(colormap=colorMap)
        
                
    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'grids3D'):
            self.vf.grids3D={}

    def __call__(self, grid3D, **kw):
        return apply(self.doitWrapper, (grid3D,), kw)

    def doit(self, grid3D, name = None, axis = 'x', sliceNumber = 0):
        if type(grid3D) in types.StringTypes:
            if self.vf.grids3D.has_key(grid3D):
                grid3D = self.vf.grids3D[grid3D]
            else:
                print "ERROR!!! "+ grid3D + "is not in the self.vf.grids3D"

        if not name:
            name = "Grid3D_Ortho_%s_%d"%(axis,sliceNumber)
            
        if name in  grid3D.geomContainer['OrthoSlice']:
            g = grid3D.geomContainer['OrthoSlice'][name]
        else:
            g = textured2DArray(name)
            self.vf.GUI.VIEWER.AddObject(g, parent = grid3D.OrthoSlice)
            grid3D.geomContainer['OrthoSlice'][name] = g

        data, vertices = grid.get2DOrthoSlice(axis, sliceNumber)
        g.Set(vertices=vertices, array=data)
        self.vf.GUI.VIEWER.OneRedraw()

        return g
    
    def select(self):
        grid_name = self.vf.Grid3DCommands.get_grid_name()
        if not grid_name:
            self.vf.Grid3DCommands.root.configure(cursor='')
            self.vf.Grid3DCommands.PanedWindow.config(cursor='')
            self.grid = None
            return
        
        self.grid = self.vf.grids3D[grid_name]
        self.ifd.entryByName['X_Slice']['widget'].config(to=self.grid.dimensions[0]-1)
        self.ifd.entryByName['Y_Slice']['widget'].config(to=self.grid.dimensions[1]-1)
        self.ifd.entryByName['Z_Slice']['widget'].config(to=self.grid.dimensions[2]-1)

        if hasattr(self.grid,'_X_Slice'):
            self.ifd.entryByName['X_Slice']['widget'].set(self.grid._X_Slice)
            self.X_vis.set(self.grid._X_Vis)
            if self.grid._X_Vis:
                self.ifd.entryByName['XGroup']['widget'].expand()
            else:
                self.ifd.entryByName['XGroup']['widget'].collapse()
        else:
            self.ifd.entryByName['X_Slice']['widget'].set(0)
            self.X_vis.set(1)
            self.createX()
            self.ifd.entryByName['XGroup']['widget'].expand()
                        
        if hasattr(self.grid,'_Y_Slice'):
            self.ifd.entryByName['Y_Slice']['widget'].set(self.grid._Y_Slice)
            self.Y_vis.set(self.grid._Y_Vis)
            if self.grid._Y_Vis:
                self.ifd.entryByName['YGroup']['widget'].expand()
            else:
                self.ifd.entryByName['YGroup']['widget'].collapse()
        else:
            self.ifd.entryByName['Y_Slice']['widget'].set(0)
            self.Y_vis.set(0)
            self.ifd.entryByName['YGroup']['widget'].collapse()
        if hasattr(self.grid,'_Z_Slice'):
            self.ifd.entryByName['Z_Slice']['widget'].set(self.grid._Z_Slice)
            self.Z_vis.set(self.grid._Z_Vis)
            if self.grid._Z_Vis:
                self.ifd.entryByName['ZGroup']['widget'].expand()
            else:
                self.ifd.entryByName['ZGroup']['widget'].collapse()    
        else:   
            self.ifd.entryByName['Z_Slice']['widget'].set(0)
            self.Z_vis.set(0)
            self.ifd.entryByName['ZGroup']['widget'].collapse()
            
        self.vf.Grid3DCommands.root.configure(cursor='')  
        self.vf.Grid3DCommands.PanedWindow.config(cursor='')   
           
OrthoSliceGUI = CommandGUI()
OrthoSliceGUI.addMenuCommand('menuRoot', 'Grid3D', 'OrthoSlice...')

from mglutil.gui.BasicWidgets.Tk.tablemaker import Colormap, TableManager, LUT
from Volume.Operators.MapData import MapGridData
globalFont = (ensureFontCase('helvetica'), 10)
from math import log10
class myLUT(LUT):
    """Extend mglutil.gui.BasicWidgets.Tk.tablemaker.LUT; removes label to top
    """
    def __init__(self, master=None, xminval=0,xmaxval=255, ymaxval=4095,
             width = width-20, height = height-50, grid_row=0,
             num_of_entries = 256, initdraw = 1):    
        self.callbacks = {'entries':None, 'rgbmap':None, 'setalpha':None,
                 'setcolor':None}
        self.master = master
        self.xmaxval = xmaxval
        self.xminval = xminval
        self.ymaxval = ymaxval
        self.num_of_entries = num_of_entries
        assert self.num_of_entries > 0
        self.font = globalFont
        
        self.canvas = Tkinter.Canvas(master,width = width, height=height,
                             relief = Tkinter.FLAT, highlightbackground='blue',
                             borderwidth = 2)
        self.width = width
        self.height = height
        
        c = self.canvas
        c.grid(row=grid_row, sticky=Tkinter.W)
        width = float(c.cget('width')) # 461.0
        height = float(c.cget('height'))#106.0
        diff = 15
        self.right = width-4
        self.top = diff
        self.left = 8
        self.bott = height-12

       # c.create_rectangle(3,3, width+3,height+3,
       #                    outline ='', width=4,
       #                    fill='', tags='outline')
        c.create_rectangle(self.left,self.top, self.right,self.bott,
                           outline ='black', width=1,
                           fill='white', tags='box')
        #c.create_text(self.right-15, self.bott+10, text=str(xmaxval),
        #              anchor=Tkinter.W, font=self.font)
        #c.create_text(self.left, self.bott+11, text=str(xminval), anchor=Tkinter.W,
        #              font=self.font)
        #c.create_text(self.left-3, self.top-7, text=str(ymaxval), anchor=Tkinter.W,
        #              font=self.font, tags = 'ytext')
        # scale x and y axes 
        self.sclx = (self.right-self.left)/(xmaxval-xminval)
        self.scly = (self.bott-self.top)/ymaxval
        self.delta = self.sclx+1e-6
        ##          c.create_line(self.left,self.bott,self.right,
        ##                        self.bott, width = 2, fill='black', tags=('line','line0'))
        ##          self.line_count = 1
        ##          self.dot_count = 0
        
        c.tag_bind('dot', '<Button-1>', self.mouse1Down)
        c.tag_bind('dot', '<ButtonRelease-1>', self.mouse1Up)
        c.tag_bind('isodot', '<Button-1>', self.pickIsoVal)
        c.tag_bind('isodot', '<B1-Motion>', self.moveIsoVal)
        #c.tag_bind('line', '<Button-1>', self.pick)
        self.bind_tags()
        arr_len = xmaxval-xminval+1
        self.color_arr = Numeric.zeros((arr_len,3),'f')
        self.alpha_arr = Numeric.zeros(arr_len).astype(Numeric.Int16)
        self.points = []
        self.values = []
        self.shapes = []
        self.isoVals = []
        self.dotrad = 5
        self.isodotrad = 5
        self.isoval_inrange = []
        if initdraw:
            self.draw_initshape()
        self.last_event = ''
        self.curr_ind = 1
        #self.continuous = 1
        
    def plot_histogram(self, event = None, data = None):  
        if data is not None:
            self.data = data
        elif not hasattr(self, 'data'):
            return
        self.canvas.delete("rect")
        x = data[1].tolist()
        y = data[0].tolist()
        
        for i in range(len(y)):
            if y[i] != 0:
                y[i] = math.log10(y[i])
            
        self.min_y = min(y)
        self.max_y = max(y)
        
        self.update_a_b()
        for i in range(len(x)):
            screen_x = self.a_x*x[i] + self.b_x
            screen_y = self.a_y*y[i] + self.b_y
            self.canvas.create_rectangle(screen_x, screen_y, 
                                 screen_x+2, self.bott , 
                                 outline="gray70", fill="gray70", tag = 'rect')
        tags = self.canvas.find_all()
        tags = list(tags)
        rect = self.canvas.find_withtag('rect')
        rect = list(rect) 
        box = self.canvas.find_withtag('box')
        box = list(box) 
        for i in rect:
            tags.remove(i)
        for i in box:
            tags.remove(i)
        for i in tags:
            self.canvas.tag_raise(i)
            
    def update_a_b(self):
        if self.max_x == self.min_x:
            print 'Error: min and max for the X axis are equal ', self.max_x
            self.a_x = 10000000000000000000000000000000000000000
        else:
            self.a_x = (self.right - self.left -1 )/(self.max_x - self.min_x)
        self.b_x = -self.a_x*self.min_x + self.left + 1
        bottom = self.bott 
        if self.max_y == self.min_y:
            print 'Error: min and max for the Y axis are equal ', self.max_y
            self.a_y = 10000000000000000000000000000000000000000
        else:
            self.a_y = (-bottom + self.top)/(self.max_y - self.min_y)
        self.b_y = bottom - self.a_y*self.min_y

from DejaVu.colorTool import RGBARamp        
class myTF(TableManager):
    """Extends mglutil.gui.BasicWidgets.Tk.tablemaker.TableManager and removes
    iso widget
    """
    def __init__(self, master, xminval=0, xmaxval=255,
                 ymaxval=255, alphaCallback = None, colorCallback = None):
        self.viewer = self.cmd.vf.GUI.VIEWER
        self.xminval = int(xminval)
        self.xmaxval = int(xmaxval)
        self.ymaxval = int(ymaxval)
        self.ymaxval_limit = int(ymaxval)
        self.master = master
        self.lutcallbacks = {}
        self.labelsBarFormat = '%4.2f'
        self.heightAdded = 0 #this keeps track the height added when splitting
        self.balloon = Pmw.Balloon(self.master)
        #place menu buttons
        #mbutton = Tkinter.Menubutton(self.master, text='VolRender - Menu')
        #mbutton.pack(side=Tkinter.LEFT)
        self.menu = Tkinter.Menu(self.master, title='VolRender - Menu')
                
        self.menu.add_command(label="Set Color", command=self.showColormap)
        self.menu.add_command(label="Reset", command=self.reset)
        self.menu.add_command(label="Hide", command=self.hideShow)
        self.menu.drawchoices= Tkinter.Menu(self.menu)
        self.menu.add_cascade(label="Draw Function...",
                                 menu=self.menu.drawchoices)
        self.menu.drawchoices.add_command(label ="Ramp",
                      command=(lambda self=self, num=0: self.draw_ramp(num)))
        self.menu.drawchoices.add_command(label ="Reversed Ramp",
                      command=(lambda self=self, num=1: self.draw_ramp(num)))
        self.menu.add_command(label="Flip Function",
                                 command = self.flip_function_cb)
        self.menu.sizechoices= Tkinter.Menu(self.menu)
        self.menu.add_command(label="Set Dots Size",
                                 command=(lambda self=self,
                                          st="dot": self.set_dotsize_cb(st)))
        self.menu.add_command(label="Delete Selected Dot",
                                 command=self.del_selected_dot)
        self.menu.add_separator()
        #self.editBtn = self # needed since split_cb calls self.editBtn.menu....
#        self.menu.add_command(label="Split Function",
#                                 command=self.show_splitDialog)
#        self.menu.add_command(label="Merge Function",
#                                 command=self.merge_function,
#                                 state="disabled")
#        
#        self.menu.add_separator()
        self.menu.add_command(label="Load LUT (.lut)",
                                 command=self.ask_open_file_cb)
        self.menu.add_command(label="Save LUT (.lut)",
                                 command=self.saveLUT)
        self.menu.add_command(label='Save TF (.clu)', command=self.saveTF)
        self.continVar = Tkinter.IntVar()
        self.continVar.set(1)
        font = self.font = globalFont
        self.set_font(self.menu, font)
        self.intervals_list = [(self.xminval, self.xmaxval),]
        self.parent_interval = (self.xminval, self.xmaxval)
        self.create_splitDialog()
        self.colormapWin = Tkinter.Toplevel()
        self.colormapWin.title('Color - VolRender')
        self.colormapWin.protocol('WM_DELETE_WINDOW', self.closeRGB)
        iconpath = 'mglutil.gui.BasicWidgets.Tk'    
        file = findFilePath('icons', iconpath)
        file = os.path.join(file,'colors.gif')
        self.colormap = Colormap(self.colormapWin, file=file)
        Tkinter.Button(self.colormapWin,text="Dismiss", 
                       command=self.closeRGB).grid(columnspan=2)
        self.colormapWin.withdraw()
        self.colormap.callbacks = [self.set_hsv]        
        #self.Label = Tkinter.Label(self.master, 
        #                           text="(0,0)")
        #self.Label.pack(anchor='w') 
        
        self.intervals_list = [(self.xminval, self.xmaxval),]
        self.parent_interval = (self.xminval, self.xmaxval)
        
        self.create_splitDialog()
        #place Lookup Table editor on the form
        self.f1 = Tkinter.Frame(self.master)
        self.f1.pack()
        self.log_var = Tkinter.IntVar()
        self.log_var.set(1)
        
        lut = myLUT(self.f1, xmaxval=self.xmaxval, xminval=xminval, grid_row=1,
                  num_of_entries = self.xmaxval+1, ymaxval=ymaxval)
        
        lut.canvas.bind('<Button-1>', self.selected)
        lut.canvas.bind('<Button-3>', self.button3)        
        self.canvas_list = [lut.canvas,]
        #lut.canvas.itemconfigure('outline', outline='blue')                    
        self.with_focus = lut
        self.lut_list = [lut,]

        #place entries for ISO value info
                
        #place color editor on the form
        
        self.lutcallbacks['entries'] = self.entries_update
        self.lutcallbacks['rgbmap'] = self.colormap.show_color
        if alphaCallback:
            self.lutcallbacks['setalpha'] = alphaCallback
        else:
            self.lutcallbacks['setalpha'] = self.lut_alpha_cb
        if colorCallback :
             self.lutcallbacks['setcolor'] = colorCallback
        else :
            self.lutcallbacks['setcolor'] = self.lut_color_cb
        lut.setCallbacks(self.lutcallbacks)
        self.data = [] #data saved to Undo splitting intervals
        lut.master.bind('<FocusOut>', self.cancelManu)
        #lut.canvas.bind("<Motion>", self.onMouseOver)

        self.minEntry = Pmw.ComboBox(self.master,label_text = 'min',labelpos = 'e',
                                dropdown=1, selectioncommand=self.setMin)
        self.minEntry.pack(side='left')
        self.minEntry._entryWidget.configure(width=8)
        
        self.maxEntry = Pmw.ComboBox(self.master,label_text = 'max',labelpos = 'w',
                                dropdown=1, selectioncommand=self.setMax)
        self.maxEntry.pack(side='right')
        self.maxEntry._entryWidget.configure(width=8)
        self.cVar = Tkinter.IntVar()
        radioS = Pmw.RadioSelect(self.master, command=self.colorGUI)
        
        radioS.pack(side="top", fill = 'x',)
        radioS.add(' Use This Widget ')
        radioS.add(' Use Colormap GUI ')
        radioS.setvalue(' Use This Widget ')
        self.radioS = radioS
        self.balloon.bind(self.lut_list[0].canvas, "Move the dots to change the transfer "+
                      "function. " + rightClick+" for options.")        

    def dismissCmap(self, toggle=True):
        if hasattr(self, 'ColorMapGUI') and self.ColorMapGUI.master.winfo_ismapped():
            self.ColorMapGUI.master.withdraw()
        self.radioS.setvalue(' Use This Widget ')
        self.balloon.bind(self.lut_list[0].canvas, "Move the dots to change the transfer "+
                      "function. " + rightClick+" for options.")        
        self.lut_list[0].canvas.configure(state='normal')
                
    def colorGUI(self, tag=None):
        name = self.cmd.vf.Grid3DCommands.get_grid_name()
        if not name:
            parent = self.cmd.vf.Grid3DCommands.root
            tkMessageBox.showerror("Error: No grid selected", 
                                   "Please add and select grid first.", parent=parent)
            return
        
        if tag == ' Use This Widget ':
            self.dismissCmap(toggle=False)
            return
        else:            
            self.lut_list[0].canvas.configure(state='disabled')
            self.balloon.bind(self.lut_list[0].canvas, "Click on 'Use This Widget' to enable this widget")            
            self.radioS.setvalue(' Use Colormap GUI ')
        if hasattr(self,'ColorMapGUI'):
            self.ColorMapGUI.master.deiconify()
            name += "-VolRender Colormap"
            self.ColorMapGUI.master.title(name)
        else:
            ramp = RGBARamp()
            ramp[:,3] = Numeric.arange(0,0.25,1./(4*256.),'f')
            name += "-VolRender Colormap"
            self.ColorMapGUI = ColorMapGUI(ramp=ramp,name=name )
            self.ColorMapGUI.numOfRampValues.pack_forget()
            self.ColorMapGUI.addCallback( self.ColorMap_cb )
        #self.colorMapB.configure(state='active')
            
        #for value in self.ColorMapGUI.buttonFrame.children.values():
        #    if not isinstance(value,Tkinter.Radiobutton):
        #        value.grid_forget()
            
        self.ColorMapGUI.dismiss.configure(command = self.dismissCmap)
        self.ColorMapGUI.master.protocol('WM_DELETE_WINDOW', self.dismissCmap)
        
    def ColorMap_cb(self, colorMap):
        ramp = Numeric.array(colorMap.ramp)
        self.cmd.alpha_cb([0,(240.*ramp[:,3]).astype('string')])
        self.cmd.vf.GUI.VIEWER.ReallyRedraw()
        self.cmd.color_cb([0,ramp[:,:3].astype(numpy.float)])
        
    
    def setMin(self, text):
        try:
            hMin = float(text)
        except ValueError:
            self.minEntry.setentry(str(self.min_x))
            return
        grid = self.cmd.grid
        bound = [hMin,self.cmd.grid.Vhist[1][-1]]
        datamap = {}
        datamap['src_min'] = hMin
        datamap['src_max'] = self.cmd.grid.Vhist[1][-1]
        datamap['dst_min'] = 0
        datamap['dst_max'] = 255
        datamap['map_type'] = 'linear'
        mapper = MapGridData()
        result = mapper(grid.data, datatype=Numeric.UInt8, datamap=datamap,
                        powerOf2=True)
        gtype = ArrayTypeToGrid[result.dtype.char]
        if grid.crystal:
            from mglutil.math.crystal import Crystal
            crystal = Crystal( grid.crystal.length, grid.crystal.angles)
        else:
            crystal = None
        newgrid = gtype(result, grid.origin, grid.stepSize, 
                        grid.header.copy(), crystal)
        newgrid.dataDims = grid.data.shape[:]
        grid.volRenGrid = newgrid
        geom = UTVolRenGeom('VolRender')
        grid.geomContainer['VolRender'] = geom
        self.cmd.vf.GUI.VIEWER.AddObject(geom, parent=grid.master_geom)
        geom.AddGrid3D(newgrid)        
        hist = numpy.histogram(self.cmd.grid.data.copy().flat, bins=self.lut_list[0].width+100, range=bound)
        self.cmd.grid.Vhist = hist
        self.data = hist
        self.plot_histogram()
        self.reset()
        self.cmd.vf.GUI.VIEWER.OneRedraw()
        
    def setMax(self, text):
        try:
            hMax = float(text)
        except ValueError:
            self.maxEntry.setentry(str(self.max_x))
            return
        grid = self.cmd.grid
        bound = [self.cmd.grid.Vhist[1][0],hMax]
        datamap = {}
        datamap['src_min'] = self.cmd.grid.Vhist[1][0]
        datamap['src_max'] = hMax
        datamap['dst_min'] = 0
        datamap['dst_max'] = 255
        datamap['map_type'] = 'linear'
        mapper = MapGridData()
        result = mapper(grid.data.copy(), datatype=Numeric.UInt8, datamap=datamap,
                        powerOf2=True)

        gtype = ArrayTypeToGrid[result.dtype.char]
        if grid.crystal:
            from mglutil.math.crystal import Crystal
            crystal = Crystal( grid.crystal.length, grid.crystal.angles)
        else:
            crystal = None
        newgrid = gtype(result, grid.origin, grid.stepSize, 
                        grid.header.copy(), crystal)
        newgrid.dataDims = grid.data.shape[:]
        grid.volRenGrid = newgrid
        geom = UTVolRenGeom('VolRender')
        grid.geomContainer['VolRender'] = geom
        self.cmd.vf.GUI.VIEWER.AddObject(geom, parent=grid.master_geom)
        geom.AddGrid3D(newgrid)
        hist = numpy.histogram(self.cmd.grid.data.copy().flat, bins=self.lut_list[0].width+100, range=bound)
        self.cmd.grid.Vhist = hist
        self.plot_histogram()
        self.reset()
        self.cmd.vf.GUI.VIEWER.OneRedraw()

    def plot_histogram(self, event=None):
        grid = self.cmd.grid            
        if not hasattr(grid,'Vhist'):
            hist = numpy.histogram(grid.data.copy().flat, bins=self.lut_list[0].width+100)
            grid.Vhist = hist                    

        self.lut_list[0].min_x = grid.Vhist[1][0]
        self.lut_list[0].max_x = grid.Vhist[1][-1]     
        self.maxEntry.setentry((self.labelsBarFormat)%grid.Vhist[1][-1])
        self.minEntry.setentry((self.labelsBarFormat)%grid.Vhist[1][0])

        self.lut_list[0].plot_histogram(data=grid.Vhist)            
        
    def hideShow(self):
        geom = self.cmd.grid.master_geom.children[-1]
        if geom.visible:
            geom.Set(visible=False)      
            self.cmd.vf.GUI.VIEWER.OneRedraw()      
            self.menu.entryconfig("Hide",label="Show")
        else:
            geom.Set(visible=True)
            self.cmd.vf.GUI.VIEWER.OneRedraw()
            self.menu.entryconfig("Show",label="Hide")

    def onMouseOver(self, event):
        x = str(event.x)
        y = str(event.y)
        self.Label.configure(text = "( " + x + " ,  " + y + " )")

    def showColormap(self):
        self.colormapWin.deiconify()
        self.colormapWin.tkraise()
        #self.menu.entryconfigure(self.menu.index('Set color'), state='disabled')
        
    def closeRGB(self):
        self.colormapWin.withdraw()
        #self.menu.entryconfigure(self.menu.index('Set color'), state='normal')
        
    def entries_update(self, **values):
        pass
    def entry_color_set(self):
        pass
    def entry_value_set(self):
        pass

    def selected(self, event):
        """Activates selected canvas widget."""
        curr_widget = event.widget
        if not isinstance(curr_widget,Tkinter.Frame):
            self.make_selected(curr_widget)
        self.menu.unpost()
        self.balloon.unbind(self.master)
        
    def button3(self, event):
        #the following 2 lines simulate right-click even which is needed for "Set Color" menu
        self.lut_list[0].canvas.event_generate('<Button-1>', x=event.x_root, y=event.y_root)
        self.lut_list[0].last_event = 'ButtonRelease-1'
        self.menu.post(event.x_root, event.y_root)

        if widgetsOnBackWindowsCanGrabFocus is False:
            lActiveWindow = self.menu.focus_get()
            if    lActiveWindow is not None \
              and ( lActiveWindow.winfo_toplevel() != self.menu.winfo_toplevel() ):
                return       
        self.balloon.bind(self.lut_list[0].canvas,"Double-click on the line connecting dots to add a dot")
        self.menu.focus_set() 

    def cancelManu(self, event=None):
        self.menu.unpost()
    
    def split_cb(self, entry_minval, entry_maxval, split=1):
        """Executing command of the 'Split Interval Dialog'.
        Determines new intervals of values. Destroys canvas widget
        representing the original interval. Calls a function creating
        canvas widgets for the new intervals."""
        
        parent_interval = self.parent_interval
        try:
            ind = self.intervals_list.index(parent_interval)
        except ValueError:
            print 'ValueError: interval',parent_interval,'is not in self.intervals_list'
            return
        if entry_minval == parent_interval[0]:
            intervals = [(entry_minval, entry_maxval),
                         (entry_maxval+1, parent_interval[1])]
            curr_interval = ind
        elif entry_maxval == parent_interval[1]:
            intervals = [(parent_interval[0], entry_minval-1),
                         (entry_minval, entry_maxval)]
            curr_interval = ind+1
        else:
            intervals = [(parent_interval[0], entry_minval-1),
                         (entry_minval, entry_maxval),
                         (entry_maxval+1, parent_interval[1])]
            curr_interval = ind+1 

        self.intervals_list.pop(ind)
        self.with_focus.canvas.configure(highlightbackground='gray')
        self.canvas_list[ind].destroy()
        self.canvas_list.pop(ind)
        old_lut = self.lut_list.pop(ind)
        #print "ind :", ind
        i = ind
        for interval in intervals:
            self.intervals_list.insert(i, interval)
            lut = myLUT(self.f1, xminval=interval[0],
                      xmaxval=interval[1], ymaxval=self.ymaxval,
                      grid_row=i+1,
                      num_of_entries=self.xmaxval+1, initdraw = 0)
            lut.canvas.bind('<Button-1>', self.selected)
            lut.canvas.bind('<Button-3>', self.button3)
            self.lut_list.insert(i, lut)
            self.canvas_list.insert(i, lut.canvas)
            i = i + 1
            lut.setCallbacks(self.lutcallbacks)
            lut.canvas.configure(highlightbackground='gray')
        no_intervals = len(self.intervals_list)
        if i < no_intervals:
            for n in range(i, no_intervals):
                self.canvas_list[n].grid(row=n, sticky=W)
        self.canvas_list[curr_interval].configure(highlightbackground='blue')
        self.with_focus = self.lut_list[curr_interval]
        i = 0
        for interval in intervals:
            self.split_function(old_lut, interval, ind+i)
            i = i + 1
        old_lut = None
        self.menu.entryconfigure("Merge Function", state='normal')
        self.master.update()
        reqHeight = self.master.winfo_reqheight()
        realHeight = self.master.winfo_height()
        if reqHeight > realHeight:            
            root = self.master.winfo_toplevel()        
            h = root.winfo_height()
            h += reqHeight - realHeight
            self.heightAdded += reqHeight - realHeight
            w = root.winfo_width()
            root.geometry('%dx%d' % (w,h))
        
    def make_selected(self, curr_widget):
        if curr_widget == self.with_focus.canvas:
            return
        curr_widget.configure(highlightbackground='blue')
        self.with_focus.canvas.configure(highlightbackground='gray')
        ind = self.canvas_list.index(curr_widget)
        i = 0
        for lut in self.lut_list:
            if i == ind:
                lut.bind_tags()
            else:
                lut.unbind_tags()
            i=i+1
        self.with_focus = self.lut_list[ind]    
        
    def merge_function(self):
        if len(self.intervals_list)<2:
            return
        interval = (self.xminval, self.xmaxval)
        #data ={'intervals':[interval,]}
        points = self.lut_list[0].points[1:-1]
        values = self.lut_list[0].values[1:-1]
        shapes = self.lut_list[0].shapes[1:-1]
        color_arr = self.lut_list[0].color_arr
        alpha_arr = self.lut_list[0].alpha_arr
        
        for lut in self.lut_list[1:]:
            points.extend(lut.points[1:-1])
            
            alpha_arr = Numeric.concatenate((alpha_arr, lut.alpha_arr))
            color_arr = Numeric.concatenate((color_arr, lut.color_arr))
            old_shapes =lut.shapes[1:-1]
            old_vals = lut.values[1:-1]
            val1 = values[-1]
            val2 = old_vals[0]
            if alpha_arr[val1] == 0 and alpha_arr[val2] == 0:
                d = shapes[-1]
                for s in old_shapes:
                    shapes.append(s+d)
            else:
                d = shapes[-1]
                shapes[-1] = d+old_shapes[1]
                if len(old_shapes) > 2:
                    for s in old_shapes[2:]:
                        shapes.append(s+d)
            values.extend(old_vals)    
        shapes.insert(0,0)
        shapes.append(shapes[-1]+1)
        ########
        for canvas in self.canvas_list:
            canvas.destroy()
        self.canvas_list = []
        self.lut_list = []
        self.intervals_list = [interval,]
        i=0
        lut = myLUT(self.f1, xminval=interval[0], ymaxval=self.ymaxval,
                  xmaxval=interval[1], grid_row=i,
                  num_of_entries=self.xmaxval+1, initdraw = 0)
        
        lut.canvas.bind('<Button-1>', self.selected)
        lut.canvas.bind('<Button-3>', self.button3)
        self.lut_list.append(lut)
        self.canvas_list.append(lut.canvas)
        right = lut.right
        left = lut.left
        bott = lut.bott
        sclx = lut.sclx
        new_points = [(left, bott),]
        for i in range(len(points)):
            new_points.append(((values[i]-self.xminval)*sclx+left,
                                  points[i][1]))
        new_points.append((right, bott))
        lut.points = new_points
        lut.shapes = shapes
        lut.color_arr = color_arr
        lut.alpha_arr = alpha_arr
        values.insert(0, self.xminval)
        values.append(self.xmaxval)
        lut.values = values
        lut.redraw()
        lut.setCallbacks(self.lutcallbacks)
        self.lut_list[0].canvas.configure(highlightbackground='blue')
        self.with_focus = self.lut_list[0]
        #######
        self.menu.entryconfigure("Merge Function", state='disabled')
        root = self.master.winfo_toplevel()
        h = root.winfo_height()
        h -= self.heightAdded
        self.heightAdded = 0
        w = root.winfo_width()
        root.geometry('%dx%d' % (w,h))

    def load_file(self, file):
        from string import split, atoi
        of = open(file, 'r')
        line = split(of.readline())
        warning = "Warning: wrong file format. Could not read file %s" %(file,)
        if len(line):
            if line[0] != "Transfer":
                of.close()
                if self.load_file_old(file):
                    return
                else:
                    print warning
                return
        else:
            of.close()
            print warning
            return
        ymaxval = 0
        while(1):
            line = of.readline()
            line = split(line)
            if len(line):
                if line[0] == "End": break
                else:
                    if line[0] == "NumIntervals":
                        nintervals = atoi(line[1])
                    elif line[0] == "Intervals":
                        intervals_str= line[1:]
                    elif line[0] == "DataSizes":
                        sizes_str = line[1:]
                    elif line[0] == "Maxalpha":
                        ymaxval = atoi(line[1])
        
        intervals = []
        sizes = []
        for n in range(nintervals):
            intervals.append( (atoi(intervals_str[n*2]),
                                    atoi(intervals_str[n*2+1]) ))
            sizes.append( (atoi(sizes_str[n*3]),
                           atoi(sizes_str[n*3+1]),
                           atoi(sizes_str[n*3+2])) )
        #print "nintervals: ", nintervals
        #print "intervals: ", intervals
        #print "sizes: ", sizes
        
        data = []
        xmaxval = intervals[nintervals-1][1]
        if xmaxval != self.xmaxval:
            if self.viewer.hasGui:
                text = "WARNING: number of LUT entries in\n%s\n is %d,\n current number of LUT entries is %d.\nLoad new LUT?" %(file,xmaxval+1,self.xmaxval+1)
                dialog = Pmw.MessageDialog(self.master,
                                           buttons=('OK','Cancel'),
                                           defaultbutton='OK',
                                           title='Load New LUT',
                                           message_text=text)
                result=dialog.activate()
                if result=='Cancel':
                    of.close()
                    return
                else:
                    self.xmaxval = xmaxval
            else:
                print "WARNING: number of LUT entries in %s is %d, current number of LUT entries is %d." % (file, xmaxval+1, self.xmaxval+1)

        shapes = []
        values = []
        alphas = []
        colors = []
        from struct import unpack, calcsize
        for n in range(nintervals):
            fmt_shapes = ">%di"%sizes[n][0]
            fmt_values = ">%di"%sizes[n][1]
            fmt_colors = ">%df"%sizes[n][2]
            l_shapes = of.read(calcsize(fmt_shapes))
            #values and alphas have the same format
            l_values= of.read(calcsize(fmt_values))
            l_alphas = of.read(calcsize(fmt_values))
            l_colors = of.read(calcsize(fmt_colors))
            shapes.append(list(unpack(fmt_shapes, l_shapes)))
            values.append(unpack(fmt_values, l_values))
            alphas.append(unpack(fmt_values, l_alphas))
            colors.append(unpack(fmt_colors, l_colors))
        #print 'shapes:', shapes    
        #print 'values: ', values
        #print 'alphas: ', alphas
        
        of.close()
        d = 1
        if ymaxval:
##              d = (ymaxval*1.0)/self.ymaxval
            self.ymaxval = ymaxval
        #print "ymaxval: ", ymaxval, "self.ymaxval: ", self.ymaxval
        self.xmaxval = xmaxval
        for canvas in self.canvas_list:
            canvas.destroy()
        self.canvas_list = []
        self.lut_list = []
        self.intervals_list = intervals
        i = 0
        for interval in intervals:
##              print 'in load_file: interval =', interval
            lut = myLUT(self.f1, xminval=interval[0],
                      xmaxval=interval[1], ymaxval = self.ymaxval,
                      grid_row=i,
                      num_of_entries=xmaxval+1, initdraw = 0)
            lut.canvas.bind('<Button-1>', self.selected)
            lut.canvas.bind('<Button-3>', self.button3)
            self.lut_list.append(lut)
            self.canvas_list.append(lut.canvas)
            if d != 1 :
                lut.calculate_points(values[i],
                                     map(lambda x: x/d, alphas[i]))
            else:
                lut.calculate_points(values[i], alphas[i])
            lut.shapes = shapes[i]
            colors_size = (len(colors[i])/3, 3)
            #print "colors_size: ", len(colors[i]), colors_size
            lut.color_arr = Numeric.reshape(Numeric.array(colors[i], 'f'),
                                            colors_size)
            lut.calculate_alphas()
            lut.redraw()
            lut.setCallbacks(self.lutcallbacks)
            lut.callbacks['setalpha']([interval[0], lut.alpha_arr])
            lut.callbacks['setcolor']([interval[0], lut.color_arr])
            i = i + 1
        #self.lut_list[0].canvas.configure(highlightbackground='blue')
        self.with_focus = self.lut_list[0]
        if len(intervals)>1:
            self.menu.entryconfigure("Merge Function", state='normal')
        root = self.master.winfo_toplevel()
        h = len(intervals)*(height-50) + height + 50
        w = root.winfo_width()
        root.geometry('%dx%d' % (w,h))
         
class LUT_data:
    "This class stores LUT data"
    intervals_list = None
    shapes = None
    values = None
    color_arr = None
    alpha_arr = None

class VolRenCommand(Command):
    "Volume Rendering command with Trasnfer Function editor GUI"
    def __init__(self, func=None):
        Command.__init__(self)
        self.grid = None
        self.ifd = InputFormDescr(title="VolRen")
        self.ifd.append({'name':'VolRen',
                    'widgetType':myTF,
                    'wcfg':{'alphaCallback':self.alpha_cb,
                            'colorCallback':self.color_cb,
                             },
                    'gridcfg':{'row':0, 'column':0, 'sticky':'wens'}
                    })
        
    def color_cb(self, values):
       if self.grid:
            #print "col",values[0],values[1] 
            self.grid.geomContainer['VolRender'].setVolRenColors(values)    
            
    def alpha_cb(self, values):
        if self.grid:          
            #print "alpha",values          
            self.grid.geomContainer['VolRender'].setVolRenAlpha(values)
            
    def saveLUT_Dict(self):
        if not self.grid:
            return   
        widget = self.ifd.entryByName['VolRen']['widget']
        self.grid.LUT_data.intervals_list = widget.intervals_list
        lut = widget.lut_list[0]
        self.grid.LUT_data.shapes = lut.shapes
        self.grid.LUT_data.values = lut.values
        self.grid.LUT_data.color_arr = lut.color_arr.copy()
        self.grid.LUT_data.alpha_arr = lut.alpha_arr.copy()  
        
    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'grids3D'):
            self.vf.grids3D={}
        self.ifd[0]['widgetType'].cmd = self
        
    def __call__(self, grid3D, **kw):
        return apply(self.doitWrapper, (grid3D,), kw)

    def doit(self, grid3D, name = None):
        if type(grid3D) in types.StringTypes:
            if self.vf.grids3D.has_key(grid3D):
                grid3D = self.vf.grids3D[grid3D]
            else:
                print "ERROR!!! "+ grid3D + "is not in the self.vf.grids3D"
        self.vf.GUI.VIEWER.OneRedraw()
    
    def select(self):
        grid_name = self.vf.Grid3DCommands.get_grid_name()
        if not grid_name:
            self.vf.Grid3DCommands.root.configure(cursor='')
            self.vf.Grid3DCommands.PanedWindow.config(cursor='')
            self.grid = None
            return
        grid = self.vf.grids3D[grid_name]
        widget = self.ifd.entryByName['VolRen']['widget']
        widget.merge_function()
            
        if not hasattr(grid,'volRenGrid'):
            datamap = {}
            datamap['src_min'] = grid.mini
            datamap['src_max'] = grid.maxi
            datamap['dst_min'] = 0
            datamap['dst_max'] = 255
            datamap['map_type'] = 'linear'
            mapper = MapGridData()
            result = mapper(grid.data, datatype=Numeric.UInt8, datamap=datamap,
                            powerOf2=True)

            gtype = ArrayTypeToGrid[result.dtype.char]
            if grid.crystal:
                from mglutil.math.crystal import Crystal
                crystal = Crystal(grid.crystal.length, grid.crystal.angles)
            else:
                crystal = None
            newgrid = gtype(result, grid.origin, grid.stepSize, 
                            grid.header.copy(), crystal)
            newgrid.dataDims = grid.data.shape[:]
            grid.volRenGrid = newgrid
            geom = UTVolRenGeom('VolRender')
            grid.geomContainer['VolRender'] = geom
            self.vf.GUI.VIEWER.AddObject(geom, parent=grid.master_geom)
            geom.AddGrid3D(newgrid)
            self.vf.GUI.VIEWER.OneRedraw()
            grid.LUT_data = LUT_data()
            self.grid = grid
            widget.lut_list[0].draw_initshape()
            widget.applylut_cb()                
        else:
            self.saveLUT_Dict()
            widget.intervals_list = grid.LUT_data.intervals_list
            widget.lut_list[0].shapes = grid.LUT_data.shapes
            widget.lut_list[0].values = values = grid.LUT_data.values
            widget.lut_list[0].color_arr = grid.LUT_data.color_arr
            widget.lut_list[0].alpha_arr = grid.LUT_data.alpha_arr
            self.grid = grid
            alphas = Numeric.take(grid.LUT_data.alpha_arr,values)
            widget.lut_list[0].calculate_points(values,alphas)
            #widget.lut_list[0].calculate_alphas()
            widget.lut_list[0].redraw(redrawIsoVals=False)
        if not hasattr(grid,'Vhist'):            
            bound = None #this is used to set the limits on the histogram
            if grid_name.endswith('.map'):
                if grid.mini < 0:
                    bound = [grid.mini,-grid.mini]
            Vhist = numpy.histogram(grid.data.copy().flat, bins=widget.lut_list[0].width+100)
            grid.Vhist = Vhist

        #widget.lut_list[0].min_x = grid.hist.min
        #widget.lut_list[0].max_x = grid.hist.max        
        widget.plot_histogram()            

        self.vf.Grid3DCommands.root.configure(cursor='')  
        self.vf.Grid3DCommands.PanedWindow.config(cursor='')   

commandList = [
    {'name':'Grid3DReadAny','cmd':readAnyGrid(),'gui':None},
    #{'name':'Grid3DAddRemove','cmd':AddRemove(),'gui':None},
    #{'name':'Grid3DCommands','cmd':Grid3DCommands(),'gui':None},    
    {'name':'addGrid','cmd':addGridCommand(),'gui':None},    
    {'name':'Grid3DIsocontour','cmd':IsocontourCommand(),'gui':None},    
    #{'name':'Grid3DOrthoSlice','cmd':OrthoSliceCommand(),'gui':None},    
    #{'name':'Grid3DVolRen','cmd':VolRenCommand(),'gui':None},    
    ]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'],dict['name'],dict['gui'])
        
"""
from Pmv.hostappInterface.lightGridCommands import *
mv =self
mv.addCommand(readAnyGrid(),'readAny',None)
mv.addCommand(addGridCommand(),'addGrid',None)
mv.addCommand(IsocontourCommand(),'isoC',None)
#self.readAny("/Library/MGLTools/1.5.6.csv/MGLToolsPckgs/mglutil/hostappliOld/data/2SOD.e.map")
self.readAny("ct_head.rawiv")
name = self.grids3D.keys()[0]
#isosurface Test OK!
self.isoC.select(grid_name=name)
self.isoC(self.grids3D[name])
self.isoC(self.grids3D[name],name="tesT",isovalue=1.0)

#so what about change the isovalue?
"""