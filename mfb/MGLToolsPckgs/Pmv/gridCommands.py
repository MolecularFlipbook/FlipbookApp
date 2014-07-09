## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Shanrong Zhao, Ruth HUEY, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/gridCommands.py,v 1.30 2010/05/14 05:38:21 autin Exp $
#
# $Id: gridCommands.py,v 1.30 2010/05/14 05:38:21 autin Exp $
#

"""
This Module implements commands 
    to read grid data, 
    to visualize isosurfaces,
    to manipulate orthoslices through the isosurfaces...
 
"""
from ViewerFramework.VFCommand import CommandGUI
##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr

from mglutil.util.callback import CallBackFunction

from Pmv.mvCommand import MVCommand
import types,string,Tkinter, math, os
import Pmw

from DejaVu import Texture
from DejaVu.extendedSlider import ExtendedSlider
import numpy.oldnumeric as Numeric
from DejaVu.colorTool import Map, RGBRamp, array2DToImage
from DejaVu.bitPatterns import patternList

from Pmv import Grid
from Pmv.moleculeViewer import DeleteGeomsEvent, AddGeomsEvent, EditGeomsEvent

class GridReader(MVCommand):
    """ Command to load grid data files, creating a 'Grid' object
   \nPackage : Pmv
   \nModule  : GridCommands
   \nClass   : GridReader
   \nCommand : readGRID
   \nSynopsis:\n
        None <--- readGRID(gridFile, **kw)
   \nRequired Arguments:\n
        gridFile --- path to the grid data file
    """


    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'grids'):
            self.vf.grids={}


    def __call__(self, gridFile, **kw):
        """None <--- readGRID(gridFile, **kw)
        \ngridFile --- path to the grid data file"""
        apply(self.doitWrapper, (gridFile,), kw)


    def doit(self, gridFile):
        grid = Grid.Grid(gridFile)
        #NB:a Grid knows its: 
        #    array    
        #    base    
        #    min    
        #    max    
        #    typecode    
        #    name...string.split(str(self.__class__))[0]    
        #    and MAYBE:
        #    SPACING=1.0
        #    CENTER= (0.,0.,0.)
        grid.name = gridFile 
        if self.vf.grids.has_key(gridFile):
            msg = "grid from " + gridFile + " already present in viewer"
            self.warningMsg(msg)
            return 'ERROR'
        self.vf.grids[gridFile] = grid
        #one grid, one surface...?
        grid.srf=None
        #FIX THIS: what about atType(?)


    def guiCallback(self):
        """called each time the 'read ->Grid' sequence is pressed"""
        gridFile = self.vf.askFileOpen(types=[('grid data files', '*.*')],
        title = 'Grid File:')
        if gridFile is not None and len(gridFile):
            self.doitWrapper(gridFile, redraw=0)


gridReaderGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
              'menuButtonName':'Grid', 'menuEntryLabel':'Grid',
              'menuCascadeName':'read'}


GridReaderGUI = CommandGUI()
GridReaderGUI.addMenuCommand('menuRoot', 'Grid', 'Grid', cascadeName='read')




class AutoGridReader(MVCommand):
    """ Command to load autogrid data files, creating an 'AutoGrid' object
   \nPackage : Pmv
   \nModule  : GridCommands
   \nClass   : AutoGridReader
   \nCommand : readAUTOGRID
   \nSynopsis:\n
        None <- readAUTOGRID(gridFile, **kw)
   \nRequired Arguments:\n 
        gridFile --- path to the autogrid data file    
    """


    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'grids'):
            self.vf.grids={}


    def __call__(self, gridFile, **kw):
        """None <- readAUTOGRID(gridFile, **kw)
        \ngridFile --- path to the autogrid data file"""
        apply(self.doitWrapper, (gridFile,), kw)


    def doit(self, gridFile):
        grid = Grid.AutoGrid(gridFile)
        curdir = os.getcwd()
        griddir = os.path.dirname(gridFile)
        if curdir==griddir:
            gridFile = os.path.basename(gridFile)
        grid.name = gridFile
        #NB:an AutoGrid knows  stuff Grid knows AND its: 
        #    GRID_PARAMETER_FILE
        #    GRID_DATA_FILE
        #    MACROMOLECULE
        #    SPACING
        #    NELEMENTS
        #    CENTER
        if self.vf.grids.has_key(gridFile):
            msg = "grid from " + gridFile + " already present in viewer"
            self.warningMsg(msg)
            return 'ERROR'
        self.vf.grids[gridFile] = grid
        fname = os.path.basename(gridFile)
        atType = string.split(fname, '.')[-2]
        grid.atType = atType
        #one grid, one surface...?
        grid.srf=None


    def guiCallback(self):
        """called each time the 'read ->AutoGrid' sequence is pressed"""
        gridFile = self.vf.askFileOpen(types=[('autogrid data files', '*.map')],
        title = 'AutoGrid File:')
        if gridFile is not None and len(gridFile):
            self.doitWrapper(gridFile, redraw=0)


autoGridReaderGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
              'menuButtonName':'Grid', 'menuEntryLabel':'AutoGrid',
              'menuCascadeName':'read'}


AutoGridReaderGUI = CommandGUI()
AutoGridReaderGUI.addMenuCommand('menuRoot', 'Grid', 'AutoGrid', cascadeName='read')

class DXReader(MVCommand):
    """ Command to load autogrid data files, creating an 'AutoGrid' object
   \nPackage : Pmv
   \nModule  : GridCommands
   \nClass   : AutoGridReader
   \nCommand : readAUTOGRID
   \nSynopsis:\n
        None <- readAUTOGRID(gridFile, **kw)
   \nRequired Arguments:\n 
        gridFile --- path to the autogrid data file    
    """
        
    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'grids'):
            self.vf.grids={}


    def __call__(self, gridFile, **kw):
        """None <- readAUTOGRID(gridFile, **kw)
        \ngridFile --- path to the autogrid data file"""
        apply(self.doitWrapper, (gridFile,), kw)


    def doit(self, gridFile):
        grid = Grid.DX(gridFile)
        curdir = os.getcwd()
        griddir = os.path.dirname(gridFile)
        if curdir==griddir:
            gridFile = os.path.basename(gridFile)
        grid.name = gridFile
        #NB:an AutoGrid knows  stuff Grid knows AND its: 
        #    GRID_PARAMETER_FILE
        #    GRID_DATA_FILE
        #    MACROMOLECULE
        #    SPACING
        #    NELEMENTS
        #    CENTER
        if self.vf.grids.has_key(gridFile):
            msg = "grid from " + gridFile + " already present in viewer"
            self.warningMsg(msg)
            return 'ERROR'
        self.vf.grids[gridFile] = grid
        fname = os.path.basename(gridFile)
        atType = string.split(fname, '.')[-2]
        grid.atType = atType
        #one grid, one surface...?
        grid.srf=None


    def guiCallback(self):
        """called each time the 'read ->AutoGrid' sequence is pressed"""
        gridFile = self.vf.askFileOpen(types=[('autogrid data files', '*.dx')],
        title = 'AutoGrid File:')
        if gridFile is not None and len(gridFile):
            self.doitWrapper(gridFile, redraw=0)


DXReaderGUI = CommandGUI()
DXReaderGUI.addMenuCommand('menuRoot', 'Grid', 'Open DX', cascadeName='read')


class DeleteAutoGrid(MVCommand):
    """ Command to remove an 'AutoGrid' object and its geometries, if any
   \nPackage : Pmv
   \nModule  : GridCommands
   \nClass   : DeleteAutoGrid
   \nCommand : deleteAUTOGRID
   \nSynopsis:\n
        None <--- deleteAUTOGRID(gridName, **kw)
   \nRequired Arguments:\n     
        gridName --- key for autogrid_to_delete in self.vf.grids
    """


    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'grids'):
            self.vf.grids={}


    def __call__(self, gridName, **kw):
        """None <- deleteAUTOGRID(gridName, **kw)
        \ngridName --- key for autogrid_to_delete in self.vf.grids"""
        if not self.vf.grids.has_key(gridName):
            msg = gridName + " not found in mv.grids "
            self.warningMsg(msg)
            return "ERROR"
        apply(self.doitWrapper, (gridName,), kw)


    def doit(self, gridName):
        grid = self.vf.grids.pop(gridName)
        if hasattr(grid, 'surfaceGUI'):
            #print "deleting ", gridName, ".surfaceGUI"
            #the box:
            #grid.box.Set(protected = False)
            grid.box.protected = False
            self.vf.GUI.VIEWER.RemoveObject(grid.box)
            delattr(grid, 'box')
            grid.surfaceGUI.delete_all_widgets()
            delattr(grid, 'surfaceGUI')
        #what about other guis which might be open?
        if hasattr(grid, 'sliceGUI'):
            #print "deleting ", gridName, ".slices"
            self.vf.getOrthoSlice.Close_cb()
            for k,v in grid.slices.items():
                print " in dimension: ", k
                for geom in v:
                    #geom.Set(protected = False)
                    geom.protected = False
                    self.vf.GUI.VIEWER.RemoveObject(geom)
            grid.sliceGUI.delete_all_widgets()
            delattr(grid, 'slices')
        #grid.srf.Set(protected = False)
        if hasattr(grid, 'srf'):
            #print "deleting ", gridName, ".srf"
            if grid.srf:
                grid.srf.protected = False
                self.vf.GUI.VIEWER.RemoveObject(grid.srf)

            delattr(grid, 'srf')
        del(grid)
        #possibly close the guis from cmds (?)
        self.vf.GUI.VIEWER.Redraw()


    def guiCallback(self):
        """called each time the 'read ->AutoGrid' sequence is pressed"""
        objList=[]
        if len(self.vf.grids.keys())==0:
            t='no grids currently in viewer'
            self.warningMsg(t)
            return
        for item in self.vf.grids.keys():
            if item not in objList:
                objList.append(item)
        if len(objList)==0:
            gridName = objList[0]
        else:
            #NEED TO PICK THE GRID....
            ifd2 = InputFormDescr(title='Choose Grid')
            ifd2.append({'widgetType':'ListChooser',
                'name':'gridObjs',
                'entries':objList,
                'wcfg':{'title':'Pick grid',
                        'mode':'single'},
                'lbwcfg':{'height':4},
                'gridcfg':{'sticky':'wens', 'column':100,
                         'rowspan':10}})
            val = self.vf.getUserInput(ifd2)
            if val is not None and len(val)>0 and len(val['gridObjs'])>0:
                gridName = val['gridObjs'][0]
            else:
                return
        return self.doitWrapper(gridName, redraw=0)


deleteAutoGridGUIDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
              'menuButtonName':'Grid', 'menuEntryLabel':'AutoGrid',
              'menuCascadeName':'delete'}


DeleteAutoGridGUI = CommandGUI()
DeleteAutoGridGUI.addMenuCommand('menuRoot', 'Grid', 'delete')



class AutoGridIsoSurface(MVCommand):
    """ Command to create:an isosurface for a 'Grid' object ,a bounding box of the grid,and a GUI to manipulate the srf and the visibility of the box . 
    \nPackage : Pmv
   \nModule  : GridCommands
   \nClass   : AutoGridIsoSurface
   \nCommand : getIsosurface
   \nSynopsis:\n
        None <- getIsosurface(grid, **kw)
   \nRequired Arguments:\n
        grid --- grid object
    """


    def onAddCmdToViewer(self):
        self.srfs = {}
        if not self.vf.commands.has_key('getOrthoSlice'):
            self.vf.loadCommand('gridCommands', 'getOrthoSlice', 'Pmv',
                                topCommand=0)
        if not self.vf.commands.has_key('setIsovalue'):
            self.vf.loadCommand('gridCommands', 'setIsovalue', 'Pmv',
                                topCommand=0)


    def buildForm(self):
        ifd = self.ifd = InputFormDescr(title = 'Visualize Grids')
        ifd.append({'widgetType': Tkinter.Label,
            'text':'Display Map',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':Tkinter.W}})
        ifd.append({'widgetType': Tkinter.Label,
            'text':'Sampling',
            'gridcfg':{'sticky':Tkinter.W, 'row':-1,'column':1}})
        ifd.append({'widgetType': Tkinter.Label,
            'text':'IsoValue',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
            'row':-1,'column':2,'columnspan':2}})
        ifd.append({'widgetType': Tkinter.Label,
            'text':'RenderMode',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':Tkinter.W, 'row':-1,'column':4}})
        ifd.append({'name': 'closeB',
            'widgetType': Tkinter.Button,
            'text':'Close',
            'wcfg':{'bd':4},
            'gridcfg':{'sticky':Tkinter.E+Tkinter.W, 'columnspan':6, 'row': 100, 'column':0},
            'command':self.Close_cb})
        self.form = self.vf.getUserInput(ifd, modal=0, blocking = 0)
        self.form.root.protocol('WM_DELETE_WINDOW',self.Close_cb)


    def guiCallback(self):
        objList=[]
        if len(self.vf.grids.keys())==0:
            t='no grids currently in viewer'
            self.warningMsg(t)
            return
        for item in self.vf.grids.keys():
            if item not in objList and not self.vf.grids[item].srf:
                objList.append(item)
        if not hasattr(self, 'ifd'):
            self.buildForm()
        else:
            self.form.deiconify()
        if len(objList)>0:
            #NEED TO PICK THE GRID....
            ifd2 = InputFormDescr(title='Choose Grid')
            ifd2.append({'widgetType':'ListChooser',
                'name':'gridObjs',
                'entries':objList,
                'wcfg':{'title':'Pick grid',
                        'mode':'single'},
                'lbwcfg':{'height':4},
                'gridcfg':{'sticky':'wens', 'column':100,
                         'rowspan':10}})
            val = self.vf.getUserInput(ifd2)
            if val is not None and len(val)>0 and len(val['gridObjs'])>0:
                filename = val['gridObjs'][0]
                grid = self.vf.grids[filename]
                return self.doitWrapper(filename, redraw=1)
                
    def Close_cb(self, event=None):
        self.form.withdraw()


    def __call__(self, grid, **kw):
        """None <- getIsosurface(grid, **kw)
           grid --- grid object
           """
        return apply(self.doitWrapper, (grid,), kw)


    def mouseUp(self, grid,  event=None):
        self.vf.setIsovalue(grid.name, grid.surfaceGUI.slider.get())

    def update(self, grid, value):
        self.vf.setIsovalue(grid.name, value)
		
    def doit(self, grid):
        if type(grid)==types.StringType:
            grid = self.vf.grids[grid]
        if grid.srf:
            msg= "this grid already has a surface"
            self.warningMsg(msg)
            return 'ERROR'
        if not hasattr(self, 'ifd') and self.vf.hasGui :
            #for the moment, set this grid's srf
            grid.srf = 1
            self.guiCallback()
            grid.srf = None
        Grid.AutoGridSurfaceGui(grid,self.vf)
        if self.vf.hasGui :
            grid.surfaceGUI.makeIfdEntry(self.ifd,['closeB'])
            value = grid.surfaceGUI.slider.get()
            grid.surfaceGUI.slider.draw.bind('<ButtonRelease-1>', CallBackFunction(self.mouseUp, grid), add='+')
            # grid.surfaceGUI.slider.AddCallback('<ButtonRelease-1>', CallBackFunction(self.mouseUp, grid))
            self.vf.GUI.VIEWER.Normalize_cb()
        else :
            print "make the srf"		
            grid.surfaceGUI.getMap()		
        #redraw = False
        #if kw.has_key("redraw") : redraw=True
        event = EditGeomsEvent('iso', [grid,[]])
        self.vf.dispatchEvent(event)
        return grid


autoGridIsoSurfaceguiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                     'menuButtonName':'Grid', 'menuEntryLabel':'get surface'}


AutoGridIsoSurfaceGUI = CommandGUI()
AutoGridIsoSurfaceGUI.addMenuCommand('menuRoot','Grid', 'get surface')



class SetIsovalue(MVCommand):
    """command called to log a change in isovalue for a isocontour
    \nPackage : Pmv
   \nModule  : GridCommands
   \nClass   : SetIsovalue
   \nCommand : setIsovalue
   \nSynopsis:\n
         None <--- setIsovalue(grid, value)
   \nRequired Arguments:\n  
        grid_name --- AutoGrid.name\n
        value --- float value of grid.surfaceGUI.slider     
    """

    def __call__(self, grid_name, value, **kw):
        """ None <--- setIsovalue(grid, value)
        \ngrid_name --- AutoGrid.name
        \nvalue --- float value of grid.surfaceGUI.slider
        """
        apply(self.doitWrapper, (grid_name, value), kw)


    def doit(self, grid_name, value):
        if self.vf.grids.has_key(grid_name):
            grid = self.vf.grids[grid_name]
            if not hasattr(grid, 'surfaceGUI'):
                #create it here...
                self.vf.getIsosurface(grid.name)
            if self.vf.hasGui :
                grid.surfaceGUI.slider.set(value)
            else :
                grid.surfaceGUI.updateIsoVal(value)	
                event = EditGeomsEvent('iso', [grid,[]])
                self.vf.dispatchEvent(event)
        else:
            t='grids %s not currently in viewer'%grid_name
            self.warningMsg(t)
            return 'ERROR'

class GetOrthoSlice(MVCommand):
    """Allows the user to see a slice through a set of volume data
    \nPackage : Pmv
   \nModule  : GridCommands
   \nClass   : GetOrthoSlice
   \nCommand : getOrthoSlice
   \nSynopsis:\n
        None <- getOrthoSlice(axis, **kw)
    """
        

    def onAddCmdToViewer(self):
        self.slices = {}
        self.axisVars = {}
        self.vvars = {}
        self.scales = {}


    def __call__(self, axis, **kw):
        """None <- getOrthoSlice(axis, **kw)
        """
        apply(self.doitWrapper, (axis,), kw)


    def doit(self, axis):
        if not hasattr(self, 'ifd'):
            self.guiCallback()
        self.addAxisSlice(axis)


    def forgetWidgets(self,grid):
        if not hasattr(grid, 'widgets'): return
        for item in grid.widgets:
            if hasattr(item, 'frame'): item.frame.grid_forget()
            else: item.grid_forget()


    def gridWidgets(self,grid):
        if not hasattr(grid, 'widgets'): return
        for i in range(len(grid.widgets)):
            if isinstance(grid.widgets[i], ExtendedSlider):
                grid.widgets[i].frame.grid(grid.gcfgs[i])
            else:
                grid.widgets[i].grid(grid.gcfgs[i])
        

    def changeGrid(self, event=None):
        lb=self.ifd.entryByName['gridObjs']['widget'].lb
        if len(lb.curselection()):
            gridentry=lb.get(lb.curselection()[0])
            newgrid = self.vf.grids[gridentry]
            for item in self.vf.grids.values():
                if hasattr(item, 'widgets'):
                    self.forgetWidgets(item)
            self.gridWidgets(newgrid)
            self.showAll.set(0)


    def addAxisSlice(self, axis):
        lb=self.ifd.entryByName['gridObjs']['widget'].lb
        if len(lb.curselection()):
            gridentry=lb.get(lb.curselection()[0])
            grid = self.vf.grids[gridentry]
            if not hasattr(grid, 'surfaceGUI'):
                if not hasattr(self.vf.getIsosurface, 'ifd'):
                    self.vf.getIsosurface.buildForm()
                self.vf.getIsosurface(grid)
                if self.vf.getIsosurface.form.root.winfo_ismapped():
                    self.vf.getIsosurface.Close_cb()
            if not hasattr(grid, 'sliceGUI'):
                Grid.AutoGridSliceGui(grid,self.vf)
            grid.sliceGUI.makeIfdEntry(axis,self.ifd,[['addX','addY','addZ'],['closeB']])
            #need this to make sure the line above finishes before the next
            print '  '
            grid.sliceGUI.addSlice(axis)
        else:
            self.warningMsg("Please select a grid,first!")
            

    def guiCallback(self):
        objList=[]
        if len(self.vf.grids.keys())==0:
            t='no grids currently in viewer'
            self.warningMsg(t)
            return
        for item in self.vf.grids.keys():
            if not self.vf.grids[item].srf:
                continue
            if item not in objList:
                objList.append(item)
        if len(objList)==0:
            t='no grids with surfaces currently in viewer'
            self.warningMsg(t)
            return
        if not hasattr(self, 'ifd'):
            self.axisType=Tkinter.StringVar()
            self.axisType.set('x')
            self.showAll=Tkinter.IntVar()
            self.showAll.set(1)
            ifd = self.ifd = InputFormDescr(title = 'Visualize OrthoSlices')
            ifd.append({'widgetType':'ListChooser',
                'name':'gridObjs',
                'title':"Current Grid:",
                'entries':objList,
                'wcfg':{'title':'Current grid',
                        'mode':'single'},
                'lbwcfg':{'height':4},
                'gridcfg':{'sticky':'w', 'columnspan': 10,'column':0,
                         'rowspan':10}})
            ifd.append({'name':'showAll',
                'widgetType':Tkinter.Checkbutton,
                'text':'Show all widgets',
                'variable':self.showAll,
                'gridcfg':{'sticky':'we', 'row':-1,
                            'column':2, 'columnspan':2},
                'command': self.gridAll})
            ifd.append({'widgetType': Tkinter.Label,
                'text':'Display Slice\n(Grid_Axis#)',
                'wcfg':{'bd':6},
                'gridcfg':{'sticky':'w' }})
            ifd.append({'widgetType': Tkinter.Label,
                'text':'Slice Number',
                'wcfg':{'bd':6},
                'gridcfg':{'sticky':'we', 'row':-1,
                            'column':2, 'columnspan':2}})
            ifd.append({'name': 'addX',
                'widgetType': Tkinter.Button,
                'text':'add x slice',
                'wcfg':{'bd':4},
                'gridcfg':{'sticky':'we', 'row': 99, 'column':0},
                'command':CallBackFunction(self.addAxisSlice,'x')})
            ifd.append({'name': 'addY',
                'widgetType': Tkinter.Button,
                'text':'add y slice',
                'wcfg':{'bd':4},
                'gridcfg':{'sticky':'we', 'row': -1, 'column':1},
                'command':CallBackFunction(self.addAxisSlice,'y')})
            ifd.append({'name': 'addZ',
                'widgetType': Tkinter.Button,
                'text':'add z slice',
                'wcfg':{'bd':4},
                'gridcfg':{'sticky':'we', 'row': -1, 'column':2},
                'command':CallBackFunction(self.addAxisSlice,'z')})
            ifd.append({'name': 'closeB',
                'widgetType': Tkinter.Button,
                'text':'Close',
                'wcfg':{'bd':4},
                'gridcfg':{'sticky':'we', 'columnspan':6, 'row': 100, 'column':0},
                'command':self.Close_cb})
            self.form = self.vf.getUserInput(ifd, modal=0, blocking = 0)
            self.form.root.protocol('WM_DELETE_WINDOW',self.Close_cb)
            self.lb = self.ifd.entryByName['gridObjs']['widget'].lb
            self.lb.bind('<Double-Button-1>',self.changeGrid)
        else:
            if hasattr(self, 'form'): 
                #first update lb here
                self.lb.delete(0, 'end')
                for item in objList:
                    self.lb.insert('end', item)
                self.form.deiconify()


    def gridAll(self):
        itemList = self.vf.grids.values()
        if self.showAll.get():
            #for item in self.vf.grids.values():
            for item in itemList:
                self.gridWidgets(item)
        else:
            for item in itemList:
                self.forgetWidgets(item)
                            

    def Close_cb(self, event=None):
        self.form.withdraw()


    def CallBack(self,scalekey,event=None):
        scale=self.scales[scalekey]
        val=scale.get()
        g = scale.grd
        axis = scale.axis
        num = int(scale.num[1:])
        self.moveSlice(g,axis,int(val), scale.num)
        self.vf.GUI.VIEWER.Redraw()


getOrthoSliceGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                 'menuButtonName':'Grid', 'menuEntryLabel':'get ortho slice'}

GetOrthoSliceGUI= CommandGUI()
GetOrthoSliceGUI.addMenuCommand('menuRoot','Grid', 'get ortho slice')


commandList = [
    {'name':'readAUTOGRID','cmd':AutoGridReader(),'gui':AutoGridReaderGUI},
    {'name':'readDX','cmd':DXReader(),'gui':DXReaderGUI},    
    #{'name':'readGRID','cmd':GridReader(),'gui':GridReaderGUI},
    {'name':'getIsosurface','cmd':AutoGridIsoSurface(),'gui':AutoGridIsoSurfaceGUI},
    {'name':'getOrthoSlice','cmd':GetOrthoSlice(),'gui':GetOrthoSliceGUI},
    {'name':'deleteAUTOGRID','cmd':DeleteAutoGrid(),'gui':DeleteAutoGridGUI},
    {'name':'setIsovalue','cmd':SetIsovalue(),'gui':None},
    ]



def initModule(vf):
    
    for dict in commandList:
        vf.addCommand(dict['cmd'],dict['name'],dict['gui'])


        
