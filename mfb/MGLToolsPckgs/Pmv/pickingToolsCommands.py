#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2010
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/pickingToolsCommands.py,v 1.28.2.7 2012/03/14 19:41:39 sanner Exp $
# 
# $Id: pickingToolsCommands.py,v 1.28.2.7 2012/03/14 19:41:39 sanner Exp $
#
import Pmw, ImageTk, Tkinter, os

from Pmv.mvCommand import MVCommand, MVCommandGUI, MVAtomICOM
from Pmv.moleculeViewer import ICONPATH

from mglutil.util.callback import CallbackFunction
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel

from opengltk.OpenGL import GL

from MolKit.molecule import Atom, Molecule
from MolKit.protein import Protein, Residue, Chain

from DejaVu import jitter

class PickingToolsCommand(MVCommand):
    """
    The PickingToolsCommand adds the tools page to the Tools Notbook
    of the GUI
    \nPackage : Pmv
    \nModule  : pickingToolsCommands
    \nClass   : PickingToolsCommand
    \nName    : loadPickingTools
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.currentCmdButton = None
        

    def startTool(self, cmd, bnum):
        # uncheck current tool
        if self.currentCmdButton is not None:
            self.buttons[self.currentCmdButton].deselect()

        # remember new current tool
        self.currentCmdButton = bnum

        # set the command
        self.vf.setICOM(cmd, modifier='Shift_L', mode='pick')


    def onAddCmdToViewer(self):
        if self.vf.hasGui:

            # add a page for tools
            p = self.pToolsPage = self.vf.GUI.toolsNoteBook.add("Tools")
            button = self.vf.GUI.toolsNoteBook.tab(2)
            button.configure(command=self.adjustWidth)
            
            from ViewerFramework.VFGUI import RaiseToolPageEvent
            self.vf.registerListener(RaiseToolPageEvent, self.updatePage)

            # add comment about picking
            lab = Tkinter.Label(p, text='Use Shift-Left Click for picking',
                                font=('Arial', 12, 'bold'))
            lab.pack(side='top', anchor='nw')

            p = Pmw.ScrolledFrame(p, horizflex='expand',vertflex='expand',
                                  vscrollmode='dynamic', hscrollmode='dynamic')
            p.pack(side='top', anchor='nw', expand=1, fill='both')
            self.scrolledFrame = p
            self.pToolsMaster = p.interior()

    def adjustWidth(self):
        self.vf.GUI.toolsNoteBook.selectpage(2)
        self.vf.GUI.workspace.configurepane('ToolsNoteBook',size=self.pToolsMaster.winfo_reqwidth()+20)            

    def updatePage(self, event):
        if event.arg=='Tools':
            cam = self.vf.GUI.VIEWER.currentCamera
            cmd = self.vf.loadCameraTools
            cmd.nearTW.set(cam.near)
            cmd.farTW.set(cam.far)
            cmd.fogStartTW.set(cam.fog.start)
            cmd.fogEndTW.set(cam.fog.end)

        
    def setCmd_cb(self, cmd, bnum):
        val = self.cmdVar.get()
        if val=='stop':
            # remove geometry
            self.vf.measureDistGUI.removeIcomGeometry()
            self.vf.measureAngleGC.removeIcomGeometry()
            self.vf.measureTorsionGC.removeIcomGeometry()
            # restore original picking command
            self.vf.setICOM(self.originalIcom, modifier='Shift_L', mode='pick',
                            topCommand=0)
            self.originalIcom = None
            self.cmdVar.set('')
            self.stopw.grid_forget()
            return

        elif self.originalIcom == None:
            # save picking command at this point
            self.originalIcom = self.vf.ICmdCaller.commands.value['Shift_L']

        if cmd: # cmd is None for 'stop' button
            # set the command
            self.stopw.grid(**self.stopwGridOpt)
            self.vf.setICOM(cmd, modifier='Shift_L', mode='pick', topCommand=0)


class MeasureToolsCommand(PickingToolsCommand, MVAtomICOM):
    """
    """
    
    def __init__(self, func=None):
        MVAtomICOM.__init__(self)
        PickingToolsCommand.__init__(self, func)
        self.currentCmdButton = None
        self.originalIcom = None


    def onAddCmdToViewer(self):
        self.tools = [
            { 'name':'distance',
              'cmd': self.vf.measureDistGUI,
              'icon': 'measD24.png',
              'tooltip': 'measure distance between atom',
              'cursor': 'hand',
            },
            { 'name':'angle',
              'cmd': self.vf.measureAngleGC,
              'icon': 'measA24.png',
              'tooltip': 'measure angle between atom',
              'cursor': 'hand',
            },
            { 'name':'torsion',
              'cmd': self.vf.measureTorsionGC,
              'icon': 'measT24.png',
              'tooltip': 'measure torsion between atom',
              'cursor': 'hand',
            },
            { 'name':'stop',
              'cmd': None,
              'icon': 'cancel24.png',
              'tooltip': 'stop measuring',
              'cursor': 'hand',
            },
            ]

        if self.vf.hasGui:
            self.balloon = Pmw.Balloon(self.vf.GUI.ROOT)

            page = self.vf.loadPickingTools.pToolsMaster

            # create a group for each set of commands
            self.groupw = w = Pmw.Group(page, tag_text='Measure Tools')
            parent = w.interior()
            w.pack(side='top', anchor='nw')

            self.buttons = []
            bnum = 0
            row = col = 0
            v = self.cmdVar = Tkinter.StringVar()

            for cmdDict in self.tools:
                photo = ImageTk.PhotoImage(
                    file=os.path.join(ICONPATH, cmdDict['icon']))

                cb = CallbackFunction(self.setCmd_cb, cmdDict['cmd'], bnum)
                b = Tkinter.Radiobutton(
                    parent, compound='left', image=photo, variable=v,
                    command=cb, indicatoron=0, value=cmdDict['name'])
                b.photo = photo

                b.grid(row=row, column=col, sticky='ne')
                self.buttons.append(b)
                bnum += 1

                if col == 10:
                    col = 0
                    row += 1
                else:
                    col += 1

                self.balloon.bind(b, cmdDict['tooltip'])

            self.stopw = b
            self.stopwGridOpt = {'row':row, 'column':col, 'sticky':'ne'}
            b.grid_forget()
            

class CameraToolsCommand(MVCommand):
        
    def onAddCmdToViewer(self):

        if self.vf.hasGui:
            self.balloon = Pmw.Balloon(self.vf.GUI.ROOT)

            # create a group for each set of commands
            page = self.vf.loadPickingTools.pToolsMaster
            self.groupw = w = Pmw.Group(page, tag_text='Camera Tools')
            parent = w.interior()
            w.pack(side='top', anchor='nw', padx=2, pady=2)

            ##
            ## back ground color
            ##
            row = col = 0
            photo = ImageTk.PhotoImage(
                file=os.path.join(ICONPATH, 'colorChooser24.png'))
            b = Tkinter.Button(parent, command=self.setCamColor, image=photo)
            b.photo = photo
            b.grid(row=row, column=col, sticky='ne')
            self.balloon.bind(b, 'Set camera background color')

            ##
            ## chain fog and camera color
            ##
            col += 1
            photo = ImageTk.PhotoImage(
                file=os.path.join(ICONPATH, 'linkOpenedH.png'))
            self.photoOpened = photo
            photo = ImageTk.PhotoImage(
                file=os.path.join(ICONPATH, 'linkClosedH.png'))
            self.photoClosed = photo
            photo = ImageTk.PhotoImage(
                file=os.path.join(ICONPATH, 'linkOpenedV.png'))
            self.photoOpenedV = photo
            photo = ImageTk.PhotoImage(
                file=os.path.join(ICONPATH, 'linkClosedV.png'))
            self.photoClosedV = photo
            self.chainVar = Tkinter.IntVar()
            self.chainVar.set(1)
            b = Tkinter.Checkbutton(parent, command=self.linkCamFogColor,
                                    image=self.photoClosed, indicatoron=0,
                                    var=self.chainVar)
            b.grid(row=row, column=col, sticky='nesw')
            self.linkw = b
            self.balloon.bind(b, 'Link camera background color with fog color')
            
            ##
            ## fog ground color
            ##
            col += 1
            photo = ImageTk.PhotoImage(
                file=os.path.join(ICONPATH, 'colorChooser24.png'))
            b = Tkinter.Button(parent, command=self.setFogColor, image=photo,
                               state='disable')
            b.photo = photo
            b.grid(row=row, column=col, sticky='ne')
            self.balloon.bind(b, 'Set camera fog color')
            self.fogColw = b
            
            ##
            ## AA
            ##
            col += 1
            val = self.vf.GUI.VIEWER.currentCamera.antiAliased
            self.AAlevel = Pmw.OptionMenu(
                parent, label_text = 'AA:',
                labelpos = 'w', initialitem = val,
                command = self.setAALevel,
                items = jitter.jitterList, menubutton_pady=0,
                )
            self.balloon.bind(self.AAlevel, 'Set antialiasing level')
            self.AAlevel.grid(row=row, column=col, sticky='ne')

            ##
            ## near
            ##
            row += 1
            col = 0
            v = self.vf.GUI.VIEWER.currentCamera.near
            self.nearTW = ThumbWheel(
                parent, showLabel=1, width=60, height=16, type=float, value=v,
                callback=self.setNear, continuous=True, oneTurn=10.,min=0.0,
                wheelPad=2, labCfg = {'text':'clipZ:', 'side':'left'})
            self.nearTW.grid(row=row, column=col, columnspan=3, sticky='ne')
            self.balloon.bind(self.nearTW, 'Set near clipping plane Z value')
            ##
            ## far
            ##
            col = 3
            v = self.vf.GUI.VIEWER.currentCamera.far
            self.farTW = ThumbWheel(
                parent, showLabel=1, width=60, height=16, type=float, value=v,
                callback=self.setFar, continuous=True, oneTurn=10.,min=0.0,
                wheelPad=2, #labCfg = {'text':'far:', 'side':'left'}
                )
            self.farTW.grid(row=row, column=col, columnspan=4, sticky='ne')
            self.balloon.bind(self.farTW, 'Set far clipping plane Z value')

            ##
            ## link fog and near far planes
            ##
            #row += 1
            col = 7
            self.fogChainVar = Tkinter.IntVar()
            #self.fogChainVar.set(1)
            b = Tkinter.Checkbutton(parent, command=self.linkFogNearFar,
                                    image=self.photoOpenedV, indicatoron=0,
                                    var=self.fogChainVar)
            b.grid(row=row, column=col, rowspan=2, sticky='ns')
            self.balloon.bind(b, 'Link fog start to near clipping plane and\nfog end to far clipping plane')
            self.linkFogw = b

            ##
            ## Fog start
            ##
            row += 1
            col = 0
            v = self.vf.GUI.VIEWER.currentCamera.fog.start
            self.fogStartTW = ThumbWheel(
                parent, showLabel=1, width=60, height=16, type=float, value=v,
                callback=self.setFogStart, continuous=True, oneTurn=10.,min=0.0,
                wheelPad=2, labCfg = {'text':'fog:', 'side':'left'})
            self.fogStartTW.grid(row=row, column=col, columnspan=3, sticky='ne')
            self.balloon.bind(self.fogStartTW, 'Set fog starting Z value')

            ##
            ## Fog end
            ##
            col = 3
            v = self.vf.GUI.VIEWER.currentCamera.fog.end
            self.fogEndTW = ThumbWheel(
                parent, showLabel=1, width=60, height=16, type=float, value=v,
                callback=self.setFogEnd, continuous=True, oneTurn=10.,min=0.0,
                wheelPad=2, #labCfg = {'text':'fog end:', 'side':'left'}
                )
            self.fogEndTW.grid(row=row, column=col, columnspan=4, sticky='ne')
            self.balloon.bind(self.fogEndTW, 'Set fog ending Z value')


    def setAALevel(self, val):
        vi = self.vf.GUI.VIEWER
        cam = vi.currentCamera
        cam.Set(antialiased=val)
        vi.Redraw()

        
    def linkCamFogColor(self, event=None):
        if self.chainVar.get():
            self.fogColw.configure(state='disable')
            vi = self.vf.GUI.VIEWER
            cam = vi.currentCamera
            cam.fog.Set(color=cam.backgroundColor)
            vi.Redraw()
            self.linkw.configure(image=self.photoClosed)
        else:
            self.fogColw.configure(state='normal')
            self.linkw.configure(image=self.photoOpened)


    def setNear(self, val):
        vi = self.vf.GUI.VIEWER
        cam = vi.currentCamera
        if val < self.farTW.get():
            cam.Set(near=val)
            if self.fogChainVar.get():
                zlength = cam.far-cam.near
                value = cam.near+zlength*self.nearRatio
                self.fogStartTW.set(value)
                cam.fog.Set(start=value)
            vi.Redraw()

        
    def setFar(self, val):
        vi = self.vf.GUI.VIEWER
        cam = vi.currentCamera
        if val > self.nearTW.get():
            cam.Set(far=val)
            if self.fogChainVar.get():
                zlength = cam.far-cam.near
                value = cam.far-zlength*self.farRatio
                self.fogEndTW.set(value)
                cam.fog.Set(end=value)
            vi.Redraw()


    def linkFogNearFar(self, event=None):
        if self.fogChainVar.get():
            #self.fogColw.configure(state='disable')
            vi = self.vf.GUI.VIEWER
            cam = vi.currentCamera
            vi.Redraw()
            self.linkFogw.configure(image=self.photoClosedV)
            fogLength = cam.fog.end-cam.fog.start
            zlength = cam.far-cam.near
            self.nearRatio = (cam.fog.start-cam.near)/float(zlength)
            self.farRatio = (cam.far-cam.fog.end)/float(zlength)
        else:
            #self.fogColw.configure(state='normal')
            self.linkFogw.configure(image=self.photoOpenedV)


    def setFogStart(self, val):
        vi = self.vf.GUI.VIEWER
        cam = vi.currentCamera
        if val < self.farTW.get():
            cam.fog.Set(start=val)
            vi.Redraw()

        
    def setFogEnd(self, val):
        vi = self.vf.GUI.VIEWER
        cam = vi.currentCamera
        if val > self.nearTW.get():
            cam.fog.Set(end=val)
            vi.Redraw()

        
    def setCamColor(self):
        from mglutil.gui.BasicWidgets.Tk.colorWidgets import BackgroundColorChooser
        def cb(color):
            cam = self.vf.GUI.VIEWER.currentCamera
            cam.Set(color=color)
            if self.chainVar.get():
                cam.fog.Set(color=color)
            self.vf.GUI.VIEWER.Redraw()
                
        cc = BackgroundColorChooser(immediate=1, commands=cb,
                          title='Camera Background Color')
        cc.pack(expand=1, fill='both')

        
    def setFogColor(self):
        from mglutil.gui.BasicWidgets.Tk.colorWidgets import ColorChooser

        def cb(color):
            cam = self.vf.GUI.VIEWER.currentCamera
            cam.fog.Set(color=color)
            self.vf.GUI.VIEWER.Redraw()
            
        cc = ColorChooser(immediate=1, commands=cb,
                          title='Camera Fog Color')
        cc.pack(expand=1, fill='both')



## class RedirectCmd(MVAtomICOM):

##     def __init__(self, func):
##         MVAtomICOM.__init__(self)
##         self.func = func

##     def getObjects(self, pick):
##         return [pick]


##     def __call__(self, object):
##         self.func( object[0] )



class GeomToolsCommand(PickingToolsCommand):
    """
    Base class for tools that work on the last picked geometry
    """

    # class variables
    ggroupw = None
    applyToLabel = None
    
    def __init__(self, func=None):
        PickingToolsCommand.__init__(self, func)
        self.currentCmdButton = None
        self.originalIcom = None
        self.allw = [] # list of all widget to enable after picking


    def enable(self):
        for w in self.allw:
            w.configure(state='normal')

    def disable(self):
        for w in self.allw:
            w.configure(state='disable')

            
    def expandParents(self, object):
        """Expand all parents of the node"""
        p = object.parent
        tree = self.geomTree
        if not tree.objectToNode.has_key(p):
            self.expandParents(p)
            
        tree.objectToNode[p].expand()


    def handlePickEvent(self, event):
        geoms = event.arg.hits.keys()
        tree = self.geomTree
        tree.clearSelection()

        for obj in geoms:
            try:
                node = tree.objectToNode[obj]
            except KeyError:
                self.expandParents(obj)
                try:
                    node = tree.objectToNode[obj]
                except KeyError:
                    return
            node.select(only=False)
            tree.showNode(node)
            
##         GeomToolsCommand.applyToLabel.configure(
##             text='Apply to:\n %s'%name)
##         self.vf.loadAppearanceTools.enable()
##         self.vf.loadClipPTools.enable()

        
##     def callCmd_cb(self, cmd, bnum):
##         if self.vf.GUI.VIEWER.lastPick:
##             cmd.func(bnum, self.vf.GUI.VIEWER.lastPick)


##     def pickParent(self, event=None):
##         vi = self.vf.GUI.VIEWER
##         geom = vi.lastPick.hits.keys()[0]
##         parent = geom.parent
##         if geom.parent is None:
##             self.upw.configure(state='disable')
##         else:
##             vi.lastPick.hits = {parent:[(0, [0])]}
##         from Pmv.moleculeViewer import PickingEvent
##         self.handlePickEvent(PickingEvent(vi.lastPick))


    def onExitFromViewer(self):
        self.ggroupw = None
        self.allw = []
        
            
    def onAddCmdToViewer(self):

        if self.vf.hasGui:
            self.balloon = Pmw.Balloon(self.vf.GUI.ROOT)
            
            from Pmv.moleculeViewer import PickingEvent
            self.vf.registerListener(PickingEvent, self.handlePickEvent)

            page = self.vf.loadPickingTools.pToolsMaster

            # create a group for each geom tools
            if self.ggroupw == None:
                GeomToolsCommand.ggroupw = w = Pmw.Group(
                    page, tag_text='Geometry Tools')
                
                parent = GeomToolsCommand.ggroupw.interior()
                w.pack(side='top', anchor='nw', expand=1, fill='y')

                vi = self.vf.GUI.VIEWER

                # create a frame for up button and apply to label
##                 f = Tkinter.Frame(parent)
##                 # add up button to go to parent geometry
##                 photo = ImageTk.PhotoImage(
##                     file=os.path.join(ICONPATH, 'arrowup.gif'))
##                 self.upw = Tkinter.Button(
##                         f, compound='left', image=photo, 
##                         command=self.pickParent)
##                 self.upw.pack(side='left', anchor='nw')
##                 self.upw.photo = photo
                
##                 # create a label showing the currently selected geometry
##                 name = ''
##                 if self.vf.GUI.VIEWER.lastPick and \
##                        self.vf.GUI.VIEWER.lastPick.mode=='pick':
##                     name = self.GUI.VIEWER.lastPick.hits.keys()[0].fullName
##                 else:
##                     name='Pick geom in 3D viewer'
                
##                     GeomToolsCommand.applyToLabel = Tkinter.Label(
##                         f,  compound='left',
##                         text='Apply to:\n %s'%name, justify='left')

##                 GeomToolsCommand.applyToLabel.pack(side='left', anchor='nw')
                
                # create a geometry selection tree
                from Pmv.geomTree import PmvGeomNode, PmvGeomTreeWithButtons
                from DejaVu.geomTree import DejaVuGeomTreeWithButtons
                from mglutil.gui.BasicWidgets.Tk.trees.tree import \
                     IconsManager, SelectEvent, DeselectEvent

                rootnode = PmvGeomNode(vi.rootObject, None)
                self.rootNode = rootnode

                iconsManager = IconsManager(['Icons'], 'DejaVu')

                tree = PmvGeomTreeWithButtons(
                    parent, rootnode, nodeHeight=18,
                    iconsManager=iconsManager, headerHeight=5,
                    treeWidth=180, hull_width=190, hull_height=150,
                    selectionMode='single')
                tree.pack(side='top', expand=1, fill='both')
                self.balloon.bind(tree, 'Select geometry to edit')
                
                rootnode.expand()
                rootnode.select()
                self.geomTree = tree

                from DejaVu.Viewer import AddObjectEvent, RemoveObjectEvent, \
                     ReparentObjectEvent

                vi.registerListener(AddObjectEvent,
                                    self.geomAddedToViewer)
                vi.registerListener(RemoveObjectEvent,
                                    self.geomAddedToViewer)
                vi.registerListener(ReparentObjectEvent,
                                    self.geomAddedToViewer)

                tree.registerListener(SelectEvent, self.selectNode)
                tree.registerListener(DeselectEvent, self.selectNode)


    def selectNode(self, event):
        tree = self.vf.loadGeomTools.geomTree
        if len(tree.selectedNodes):
            self.vf.loadAppearanceTools.enable()
            self.vf.loadClipPTools.enable()
        else:
            self.vf.loadAppearanceTools.disable()
            self.vf.loadClipPTools.disable()

        
    def geomAddedToViewer(self, event):
        if self.geomTree.objectToNode.has_key(event.object.parent):
            node = self.geomTree.objectToNode[event.object.parent]
            if node.isExpanded:
                node.collapse()
            node.expand()
            node.refreshChildren()

        # HACK to get geometries added below visible wndow to show up
        # when we scroll down
        self.geomTree.root.collapse()
        self.geomTree.root.expand()

            
class AppearanceToolsCommand(GeomToolsCommand):
    """
    """
    
    def doit(self, mode, face='front'):
        geom = self.vf.loadGeomTools.geomTree.selectedNodes
        if len(geom)==0: return
        else: geoms = [x.object for x in geom]
        for geom in geoms:
            if mode=='points':
                if face=='front':
                    geom.Set(inheritFrontPolyMode=False,
                             frontPolyMode='point', outline=False)
                else:
                    geom.Set(inheritBackPolyMode=False,
                             backPolyMode='point', outline=False)
            elif mode=='wire':
                if face=='front':
                    geom.Set(inheritFrontPolyMode=False, frontPolyMode='line',
                             outline=False, polyFace=face)
                else:
                    geom.Set(inheritBackPolyMode=False, backPolyMode='line',
                             outline=False)

            elif mode=='gouraud':
                if face=='front':
                    geom.Set(inheritFrontPolyMode=False, frontPolyMode='fill',
                             inheritShading=False, shading='smooth',
                             outline=False)
                else:
                    geom.Set(inheritBackPolyMode=False, backPolyMode='fill',
                             inheritShading=False, shading='smooth',
                             outline=False)
                    
            elif mode=='outlined':
                if face=='front':
                    geom.Set(inheritFrontPolyMode=False, frontPolyMode='fill',
                             inheritShading=False, shading='smooth',
                             outline=True)
                else:
                    geom.Set(inheritBackPolyMode=False, backPolyMode='fill',
                             inheritShading=False, shading='smooth',
                             outline=True)
                    
##            elif mode=='flat':
##                geom.Set(inheritFrontPolyMode=False, frontPolyMode='fill',
##                          inheritShading=False, shading='flat', outline=False)
##             elif mode=='flat Outlined':
##                 geom.Set(inheritFrontPolyMode=False, frontPolyMode='fill',
##                          inheritShading=False, shading='flat', outline=True)

    def onAddCmdToViewer(self):

        self.tools = [
            { 'name':'points',
              'icon': 'point24.png',
              'tooltip': 'Draw points for %s polygons',
              'cursor': 'hand',
            },
            { 'name':'wire',
              'icon': 'wire24.png',
              'tooltip': 'Draw wires for %s polygons',
              'cursor': 'hand',
            },
            { 'name':'gouraud',
              'icon': 'smooth24.png',
              'tooltip': 'Draw Gouraud shaded polygons for %s polygons',
              'cursor': 'hand',
            },
            { 'name':'outlined',
              'icon': 'outline24.png',
              'tooltip': 'Draw Gouraud shaded polygons with outline for %s polygons',
              'cursor': 'hand',
            },
##             { 'name':'flat',
##               'cmd': CallbackFunction(self.doit, 'flat'),
##               'icon': 'flat24.png',
##               'tooltip': 'Draw flat shaded representation for %s polygons',
##               'cursor': 'hand',
##             },
##             { 'name':'flat outlined',
##               'cmd': RedirectCmd(CallbackFunction(self.doit, 'flat')),
##               'icon': 'flat24.png',
##               'tooltip': 'Apply flat shaded representation for %s polygons',
##               'cursor': 'hand',
##             },
##             { 'name':'stop',
##               'cmd': None,
##               'icon': 'cancel24.png',
##               'tooltip': 'stop measuring',
##               'cursor': 'hand',
##             },
            ]

        if self.vf.hasGui:
            self.balloon = Pmw.Balloon(self.vf.GUI.ROOT)

            # create a group for each set of commands
            self.groupw = w = Pmw.Group(GeomToolsCommand.ggroupw.interior(),
                                        tag_text='Appearance Tools')
            parent = w.interior()
            w.pack(side='top', anchor='nw', padx=2, pady=2)

            ##
            ## rendering buttons
            ##
            self.buttons = []
            bnum = 0
            row = col = 0

            ##
            ## add check button to show/hide FRONT polygons
            var = self.frontPolv = Tkinter.IntVar()
            var.set(1)
            b = Tkinter.Checkbutton(
                parent, compound='left', text='F', variable=var,
                command=self.cull_cb, indicatoron=0,
                state='disable')
            b.grid(row=row, column=col, sticky='ne')
            self.balloon.bind(b, 'Check to show front facing polygons')
            self.allw.append(b)

            col += 1
            for cmdDict in self.tools:
                photo = ImageTk.PhotoImage(
                    file=os.path.join(ICONPATH, cmdDict['icon']))

                cmd = CallbackFunction(self.doit, cmdDict['name'])
                b = Tkinter.Button(
                    parent, compound='left', image=photo,
                    command=cmd, state='disable')
                b.photo = photo
                b.grid(row=row, column=col, sticky='ne')
                self.allw.append(b)
                self.buttons.append(b)
                self.balloon.bind(b, cmdDict['tooltip']%'front')

                # add line width control on right click
                if cmdDict['name']=='points':
                    b.bind('<ButtonPress-3>', self.postPWCounter)

                # add line width control on right click
                if cmdDict['name']=='wire':
                    b.bind('<ButtonPress-3>', self.postLWCounter)
                    
                # add outline parameter panel on right click
                if cmdDict['name']=='outlined':
                    b.bind('<ButtonPress-3>', self.postOutlineParamPanel)
                    
                bnum += 1
                col += 1

            ##
            ## Front color
            ##
            photo = ImageTk.PhotoImage(
                file=os.path.join(ICONPATH, 'colorChooser24.png'))
            b = Tkinter.Button(parent, command=self.setColor, image=photo,
                               state='disable')
            b.photo = photo
            b.grid(row=row, column=col, sticky='ne')
            self.allw.append(b)
            self.balloon.bind(b, 'Choose color for front polygons')

            ##
            ## add check button to show/hide BACK polygons
            row += 1
            col = 0
            var = self.backPolv = Tkinter.IntVar()
            var.set(0)
            b = Tkinter.Checkbutton(
                parent, compound='left', text='B', variable=var,
                command=self.cull_cb, indicatoron=0,
                state='disable')
            b.grid(row=row, column=col, sticky='ne')
            self.balloon.bind(b, 'Check to show back facing polygons')
            self.allw.append(b)

            col += 1
            for cmdDict in self.tools:
                photo = ImageTk.PhotoImage(
                    file=os.path.join(ICONPATH, cmdDict['icon']))

                cmd = CallbackFunction(self.doit, cmdDict['name'], 'back')
                b = Tkinter.Button(
                    parent, compound='left', image=photo, 
                    command=cmd, state='disable')
                b.photo = photo
                b.grid(row=row, column=col, sticky='ne')
                self.allw.append(b)
                self.buttons.append(b)
                self.balloon.bind(b, cmdDict['tooltip']%'back')

                # add line width control on right click
                if cmdDict['name']=='points':
                    b.bind('<ButtonPress-3>', self.postPWCounter)

                # add line width control on right click
                if cmdDict['name']=='wire':
                    b.bind('<ButtonPress-3>', self.postLWCounter)
                    
                bnum += 1
                col += 1

            ##
            ## Back color
            ##
            photo = ImageTk.PhotoImage(
                file=os.path.join(ICONPATH, 'colorChooser24.png'))
            b = Tkinter.Button(parent, command=self.setColorB, image=photo,
                               state='disable')
            b.photo = photo
            b.grid(row=row, column=col, sticky='ne')
            self.allw.append(b)
            self.balloon.bind(b, 'Choose color for back polygons')

            ##
            ## opacity
            ##
            row += 1
            col = 0
            
            self.opcaTW = ThumbWheel(
                parent, showLabel=1, width=70, height=16, type=float, value=1.,
                callback=self.setOpacity, continuous=True, oneTurn=1.,min=0.0,
                max=1.0, wheelPad=2, labCfg = {'text':'opac:', 'side':'left'})
            self.opcaTW.grid(row=row, column=col, columnspan=4, sticky='ne')
            self.balloon.bind(self.opcaTW, 'Set geometry opacity')


            self.enable()

            tree = self.vf.loadGeomTools.geomTree
            from mglutil.gui.BasicWidgets.Tk.trees.tree import SelectEvent
            tree.registerListener(SelectEvent, self.configureButtons)


    def configureButtons(self, event):
        # configure appearance buttons for picked geometry
        geom = self.vf.loadGeomTools.geomTree.selectedNodes[0].object
        vi = geom.viewer
        val = geom.culling in [GL.GL_NONE, GL.GL_BACK]
        self.frontPolv.set(val)
        val = geom.culling in [GL.GL_NONE, GL.GL_FRONT]
        self.backPolv.set(val)


    def cull_cb(self):
        cf = not self.frontPolv.get()
        cb = not self.backPolv.get()
        geom = self.vf.loadGeomTools.geomTree.selectedNodes[0].object
        if cf and cb:
            geom.Set(culling='front_and_back')
        elif cf:
            geom.Set(culling='front')
        elif cb:
            geom.Set(culling='back')
        else:
            geom.Set(culling='none')
        geom.viewer.deleteOpenglList()
        geom.viewer.Redraw()
        
    ##
    ## outline paarameter panel popup
    ##
    def postOutlineParamPanel(self, event):
        vi = self.vf.GUI.VIEWER
        geom = self.vf.loadGeomTools.geomTree.selectedNodes[0].object
        vi.GUI.outlineMeshProp_cb(geometry=geom)
        
    ##
    ## Line width popup
    ##
    def postLWCounter(self, event):
        self._tmproot = root = Tkinter.Toplevel()
        vi = self.vf.GUI.VIEWER
        #pick = vi.lastPick
        #if pick is None: return
        #geom = pick.hits.keys()[0]
        geom = self.vf.loadGeomTools.geomTree.selectedNodes[0].object
        
        self._oldValue = geom.lineWidth
        root.transient()
        root.geometry("+%d+%d"%root.winfo_pointerxy())
        root.overrideredirect(True)
        c = self._int = Pmw.Counter(
            root,
            labelpos = 'w', label_text = 'line Width',
            orient = 'horizontal', entry_width = 2,
            entryfield_value = geom.lineWidth,
            #entryfield_validate = {'validator' : 'integer',
            #                       'min' : 1, 'max' : 10},
            entryfield_validate = self._custom_validate,
            entryfield_command = self.returnCB,
            )
        c.grid(row=0, column=0)
        self._counter = c

        im = ImageTk.PhotoImage(file=os.path.join(ICONPATH,'ok20.png'))
        b = Tkinter.Button(root, image=im, command=self.returnCB)
        b.im = im
        b.grid(row=0, column=1)

        im = ImageTk.PhotoImage(file=os.path.join(ICONPATH,'cancel20.png'))
        b = Tkinter.Button(root, image=im, command=self.cancelCB)
        b.im = im
        b.grid(row=0, column=2)

    def _custom_validate(self, text):
        try:
            val = float(text)
            if val > 0.0:
                ok = True
            else:
                ok = False
        except:
            ok = False
        if ok:
            self.setLW(val)
            return 1
        else:
            return -1

    def cancelCB(self, event=None, ok=False):
        if ok is False:
            self.setLW(self._oldValue)
        if hasattr(self, '_tmproot'):
            self._tmproot.destroy()
            del self._tmproot
            del self._oldValue


    def returnCB(self, event=None):
        value = self._counter.get()
        self.setLW(value)
        self.cancelCB(event, ok=True)

        
    def setLW(self, val):
        geom = self.vf.loadGeomTools.geomTree.selectedNodes[0].object
        geom.Set(inheritLineWidth=False, lineWidth=int(val))

    ##
    ## Point width popup
    ##
    def postPWCounter(self, event):
        self._tmproot = root = Tkinter.Toplevel()
        vi = self.vf.GUI.VIEWER

        geom = self.vf.loadGeomTools.geomTree.selectedNodes[0].object
        
        self._oldValue = geom.lineWidth
        root.transient()
        root.geometry("+%d+%d"%root.winfo_pointerxy())
        root.overrideredirect(True)
        c = self._int = Pmw.Counter(
            root,
            labelpos = 'w', label_text = 'Point Width',
            orient = 'horizontal', entry_width=2,
            entryfield_value = geom.pointWidth,
            entryfield_validate = self._custom_validate1,
            entryfield_command = self.returnCB1,
            )
        c.grid(row=0, column=0)
        self._counter = c

        im = ImageTk.PhotoImage(file=os.path.join(ICONPATH,'ok20.png'))
        b = Tkinter.Button(root, image=im, command=self.returnCB1)
        b.im = im
        b.grid(row=0, column=1)

        im = ImageTk.PhotoImage(file=os.path.join(ICONPATH,'cancel20.png'))
        b = Tkinter.Button(root, image=im, command=self.cancelCB1)
        b.im = im
        b.grid(row=0, column=2)

    def _custom_validate1(self, text):
        try:
            val = float(text)
            if val > 0.0:
                ok = True
            else:
                ok = False
        except:
            ok = False
        if ok:
            self.setPW(val)
            return 1
        else:
            return -1

    def cancelCB1(self, event=None, ok=False):
        if ok is False:
            self.setPW(self._oldValue)
        if hasattr(self, '_tmproot'):
            self._tmproot.destroy()
            del self._tmproot
            del self._oldValue


    def returnCB1(self, event=None):
        value = self._counter.get()
        self.setPW(value)
        self.cancelCB1(event, ok=True)

        
    def setPW(self, val):
        geom = self.vf.loadGeomTools.geomTree.selectedNodes[0].object
        # setting outline to False forces the change
        geom.Set(inheritPointWidth=False, pointWidth=int(val), outline=False)


    def setColor(self):
        from mglutil.gui.BasicWidgets.Tk.colorWidgets import ColorChooser
        #vi = self.vf.GUI.VIEWER
        #pick = vi.lastPick
        #if pick is None: return
        #geom = pick.hits.keys()[0]
        geom = self.vf.loadGeomTools.geomTree.selectedNodes[0].object

        def cb(color, geom=geom):
            geom.Set(inheritMaterial=False, materials=[color])
            self.setOpacity(self.opcaTW.get())
            
        cc = ColorChooser(title="Front Color Chooser", immediate=1, commands=cb)
        cc.pack(expand=1, fill='both')


    def setOpacity(self, val):
        geom = self.vf.loadGeomTools.geomTree.selectedNodes[0].object
        geom.Set(opacity=val, inheritMaterial=False, transparent=True)


    def setColorB(self):
        from mglutil.gui.BasicWidgets.Tk.colorWidgets import ColorChooser
        geom = self.vf.loadGeomTools.geomTree.selectedNodes[0].object

        def cb(color, geom=geom):
            geom.Set(inheritMaterial=False, materials=[color], polyFace='back')
            self.setOpacity(self.opcaTW.get())
            
        cc = ColorChooser(title="Back Color Chooser", immediate=1, commands=cb)
        cc.pack(expand=1, fill='both')


    def setOpacityB(self, val):
        geom = self.vf.loadGeomTools.geomTree.selectedNodes[0].object
        geom.Set(opacity=val, inheritMaterial=False, transparent=True,
                 polyFace='back')



class ClipPToolsCommand(GeomToolsCommand):
    """
    """
    
#    def __init__(self, func=None):
#        AppearanceToolsCommand.__init__(self)

    def onAddCmdToViewer(self):

        self.cliptools = [
            { 'name':'enable1',
              'cmd': CallbackFunction(self.doit, 0),
              'icon': 'clipOn24.png',
              'tooltip': 'enbale/Disable clipping plane 1',
              'cursor': 'hand',
            },
            { 'name':'enable2',
              'cmd': CallbackFunction(self.doit, 1),
              'icon': 'clipOn24.png',
              'tooltip': 'enbale/Disable clipping plane 2',
              'cursor': 'hand',
            },
            { 'name':'enable3',
              'cmd': CallbackFunction(self.doit, 2),
              'icon': 'clipOn24.png',
              'tooltip': 'enbale/Disable clipping plane 3',
              'cursor': 'hand',
            },
            { 'name':'enable4',
              'cmd': CallbackFunction(self.doit, 3),
              'icon': 'clipOn24.png',
              'tooltip': 'enbale/Disable clipping plane 4',
              'cursor': 'hand',
            },
            { 'name':'enable2',
              'cmd': CallbackFunction(self.doit, 4),
              'icon': 'clipOn24.png',
              'tooltip': 'enbale/Disable clipping plane 5',
              'cursor': 'hand',
            },
            { 'name':'enable6',
              'cmd': CallbackFunction(self.doit, 5),
              'icon': 'clipOn24.png',
              'tooltip': 'enbale/Disable clipping plane 6',
              'cursor': 'hand',
            },
            ]
        if self.vf.hasGui:
            self.balloon = Pmw.Balloon(self.vf.GUI.ROOT)

            # create a group for each set of commands
            self.groupw = w = Pmw.Group(GeomToolsCommand.ggroupw.interior(),
                                        tag_text='Clipping Planes')
            parent = w.interior()
            w.pack(side='top', anchor='nw', padx=2, pady=2)

            #self.cpbuttons = []
            row = 0
            col = 0

            ##
            ## transform clipping plane radio buttons
            ##
            var = self.cclip = Tkinter.IntVar()
            var.set(-1)
            for cpnum, cmdDict in enumerate(self.cliptools):
                #photo = ImageTk.PhotoImage(
                #    file=os.path.join(ICONPATH, cmdDict['icon']))
                cb = CallbackFunction(self.setCurrent, cpnum+1)
                #b = Tkinter.Radiobutton(
                #    parent, compound='left', image=photo,
                #    command=cb, indicatoron=0, variable=var, value=cpnum+1)
                b = Tkinter.Radiobutton(
                    parent, compound='left', text='T%d'%cpnum, state='disable',
                    command=cb, indicatoron=0, variable=var, value=cpnum+1)
                #b.photo = photo

                b.grid(row=row, column=col, sticky='ne')
                self.allw.append(b)
                helpstr = "assign mouse transformation to clipping plane %d"%cpnum
                self.balloon.bind(b, helpstr)
                col += 1

            photo = ImageTk.PhotoImage(
                file=os.path.join(ICONPATH, 'cancel24.png'))

            cb = CallbackFunction(self.setCurrent, 0)
            b = Tkinter.Radiobutton(
                parent, compound='left', image=photo, 
                command=cb, indicatoron=0, variable=var, value=0)
            b.photo = photo
            helpstr = "assign mouse transformation to root object"
            self.balloon.bind(b, helpstr)

            self.stopw = b
            self.stopwGridOpt = {'row':row, 'column':col, 'sticky':'ne'}

            ##
            ## enable/disable clipping plane on last picked geom
            ##
            row += 1
            col = 0
            bnum = 0
##             # add on off buttons
##             for cpnum, cmdDict in enumerate(self.cliptools):
##                 photo = ImageTk.PhotoImage(
##                     file=os.path.join(ICONPATH, cmdDict['icon']))

##                 var = self.vf.GUI.VIEWER.GUI.clipvar[cpnum][0]
##                 b = Tkinter.Checkbutton(
##                     parent, compound='left', image=photo, state='disable',
##                     command=cmdDict['cmd'], indicatoron=0, variable=var)
##                 b.photo = photo

##                 b.grid(row=row, column=col, sticky='ne')
##                 bnum += 1
##                 col += 1
##                 self.allw.append(b)

            ##
            ## enable/disable recursive clipping of children
            ##
            row += 1
            col = 0
            # add on off buttons
            for cpnum, cmdDict in enumerate(self.cliptools):
                photo = ImageTk.PhotoImage(
                    file=os.path.join(ICONPATH, cmdDict['icon']))

                cb = CallbackFunction(self.clipChildren, cpnum)
                var = self.vf.GUI.VIEWER.GUI.clipvar[cpnum][2]
                b = Tkinter.Checkbutton(
                    parent, compound='left', image=photo,
                    command=cb, indicatoron=0, variable=var)
                b.photo = photo

                b.grid(row=row, column=col, sticky='ne')
                col += 1
                self.allw.append(b)
                helpstr = "enable/diable clipping plane %d on current geometry"%cpnum
                self.balloon.bind(b, helpstr)

            ##
            ## enable/disable capping
            ##
            row += 1
            col = 0
            # add on off buttons
            for cpnum, cmdDict in enumerate(self.cliptools):
                #photo = ImageTk.PhotoImage(
                #    file=os.path.join(ICONPATH, cmdDict['icon']))

                cb = CallbackFunction(self.capOnOff, cpnum)
                var = self.vf.GUI.VIEWER.GUI.clipvar[cpnum][5]
                b = Tkinter.Checkbutton(
                    parent, compound='left', text='Cap', state='disable',
                    command=cb, indicatoron=0, variable=var)
                #b = Tkinter.Checkbutton(
                #    parent, compound='left', image=photo,
                #    command=cb, indicatoron=0, variable=var)
                #b.photo = photo

                b.grid(row=row, column=col, sticky='ne')
                col += 1
                self.allw.append(b)
                helpstr = "enable/diable capping on clipping plane %d on current geometry"%cpnum
                self.balloon.bind(b, helpstr)
            
            self.enable()

            tree = self.vf.loadGeomTools.geomTree
            from mglutil.gui.BasicWidgets.Tk.trees.tree import SelectEvent
            tree.registerListener(SelectEvent, self.configureButtons)


    def configureButtons(self, event):
        # configure clipping plane buttons for picked geometry
        geom = self.vf.loadGeomTools.geomTree.selectedNodes[0].object
        vi = geom.viewer
        vars = vi.GUI.clipvar
        for i in range(6):
            vars[i][0].set(0) # on/off
            vars[i][2].set(0) # inherit
            vars[i][5].set(0) # cap

        #for cp in geom.clipP:
        #    vars[cp.num][0].set(1)

        for cp in geom.clipPI:
            cpn = cp.num
            vars[cp.num][2].set(1)

        for child in geom.children:
            name = child.name
            if name[:3]=='cap' and len(name)==4:
                num = int(name[3])
                vars[num][5].set( 1 ) # capped Mesh

    def capOnOff(self, cpnum):
        # enable/disable capping, cpnum is 0-based clipping plane number
        vi = self.vf.GUI.VIEWER
        #pick = vi.lastPick
        #if pick is None: return
        #geom = pick.hits.keys()[0]
        geom = self.vf.loadGeomTools.geomTree.selectedNodes[0].object
        cp = vi.clipP[cpnum]
        onOff = vi.GUI.clipvar[cpnum][5].get()
        cp.ClipCapMesh(geom, onOff)


    def clipChildren(self, cpnum):
        # enable recursive clipping, cpnum is 0-based clipping plane number
        vi = self.vf.GUI.VIEWER
        #pick = vi.lastPick
        #if pick is None: return
        #geom = pick.hits.keys()[0]
        geom = self.vf.loadGeomTools.geomTree.selectedNodes[0].object
        cp = vi.clipP[cpnum]
        vars = vi.GUI.clipvar[cpnum]

        if cp in geom.clipP or cp in geom.clipPI:
            geom.RemoveClipPlane( cp )

        else:
            vars[0].set(1) # turn clipping on
            if vars[1].get(): side=1
            else: side=-1
            vars[2].set(1) # turn inherit on
            cp.visible = 0 # make plane not visible
            geom.AddClipPlane( cp, side, True)
            vi.GUI.centerClipPlane(geom, cp, True)
            

    def setCurrent(self, num):
        # bind mouse transformation to current clipping plane
        # numis clipping plane num+1. 0 is binding trackball to object
        vi = self.vf.GUI.VIEWER
        if num==0:
            self.stopw.grid_forget()
            self.currrentTransformedPlane.visible = 0
            vi.BindTrackballToObject(vi.currentObject)
            tree = self.vf.loadGeomTools.geomTree
            try:
                node = tree.objectToNode[vi.currentObject]
                node.select()
            except KeyError:
                tree.clearSelection()
                self.vf.loadAppearanceTools.disable()
                self.vf.loadClipPTools.disable()
                
        else:
            self.stopw.grid(**self.stopwGridOpt)
            cp = vi.clipP[num-1]
            cp.visible = 1
            self.currrentTransformedPlane = cp
            # we have to temporarly make the geoemtry in geomTree the viewer's
            # current object for vi.SetCurrentClip called in
            # vi.BindTrackballToClipto work properly
            curObj = vi.currentObject
            geom = self.vf.loadGeomTools.geomTree.selectedNodes[0].object
            vi.currentObject = geom

            vi.BindTrackballToClip(cp)

            # restore vi.currentObject
            vi.currentObject = curObj
        vi.deleteOpenglList()
        vi.Redraw()
        

    def doit(self, cpnum):
        # turn clipping plane on/off for last icked geometry
        #geom = pick.hits.keys()[0]
        geom = self.vf.loadGeomTools.geomTree.selectedNodes[0].object
        
        vi = self.vf.GUI.VIEWER
        cp = vi.clipP[cpnum]
        vars = vi.GUI.clipvar[cpnum]
        if cp in geom.clipP:
            geom.RemoveClipPlane( cp )
            vars[0].set(0)
        else:
            vars[0].set(1)            
            if vars[1].get(): side=1
            else: side=-1
            vars[2].set(1)
            inh = True
            cp.visible = 1
            geom.AddClipPlane( cp, side, inh)
            vi.GUI.centerClipPlane(geom, cp, inh)

        if geom != vi.rootObject:
            vi.objectsNeedingRedo[geom] = None

        vi.Redraw()


        
                   
class DisplayToolsCommand(PickingToolsCommand):
    """
    """
    
    def __init__(self, func=None):
        PickingToolsCommand.__init__(self, func)
        self.currentCmdButton = None
        self.currentTool= None


        self.tools = [
            { 'name':'cpk',
              'cmd': self.vf.displayCPK,
              'icon': 'measD24.png',
              'tooltip': 'Display Van der waals spheres',
              'cursor': 'hand',
            },
            { 'name':'S&B',
              'cmd': self.vf.displaySticksAndBalls,
              'icon': 'measD24.png',
              'tooltip': 'Display sticks and balls',
              'cursor': 'hand',
            },
            { 'name':'SS',
              'cmd': self.vf.displayExtrudedSS,
              'icon': 'measD24.png',
              'tooltip': 'Display ribbon',
              'cursor': 'hand',
            },
            { 'name':'MSMS',
              'cmd': self.vf.displayMSMS,
              'icon': 'measD24.png',
              'tooltip': 'Display molecular surface',
              'cursor': 'hand',
            },
            ]

        if self.vf.hasGui:
            gui = self.vf.GUI

            self.styleRow = self.styleCol = 0

            #self.balloon = Pmw.Balloon(gui.ROOT)

            # add a page for tools
            page = self.pToolsMaster = gui.toolsNoteBook.add("Tools")

            # create level radio buttons
            options = ['Atom', 'Residue', 'Chain', 'Molecule' ]
            col = self.vf.ICmdCaller.levelColors
            self.LevelOption = Pmw.OptionMenu(
                page, label_text = 'Level:',
                labelpos = 'w', initialitem = options[0],
                command = self.setLevel_cb,
                items = options, menubutton_pady=0,
                )
            self.LevelOption.pack(side='top', anchor='nw',
                                  expand=0, padx=2, pady=1)
##             self.LevelOption.grid(row=self.styleRow, column=self.styleCol,
##                                   sticky='ne')

            # create a group for each set of commands
            self.groups = {}
            for name in ['measure', 'display']:
                w = Pmw.Group(page, tag_text=name)
                parent = w.interior()
                w.pack(side='top', anchor='nw')
                
                self.groups[name] = w

                self.styleRow += 1
                self.buttons = []
                bnum = 0
            
                for cmdDict in getattr(self, name+'Tools'):
                    photo = ImageTk.PhotoImage(
                        file=os.path.join(ICONPATH, cmdDict['icon']))

                    cb = CallbackFunction(self.startTool, cmdDict['cmd'], bnum)
                    b = Tkinter.Checkbutton(parent, compound='left',
                                            image=photo,
                                            command=cb, indicatoron=0)
                    b.photo = photo

                    b.grid(row=self.styleRow, column=self.styleCol, sticky='ne')
                    self.buttons.append(b)
                    bnum += 1

                    if self.styleCol == 10:
                        self.styleCol = 0
                        self.styleRow += 1
                    else:
                        self.styleCol += 1


    def setLevel_cb(self, level):
        if level=='Atom':
            self.vf.setIcomLevel(Atom)
        elif level=='Residue':
            self.vf.setIcomLevel(Residue)
        elif level=='Chain':
            self.vf.setIcomLevel(Chain)
        elif level=='Molecule':
            self.vf.setIcomLevel(Molecule)


commandList = [
    {'name':'loadPickingTools', 'cmd':PickingToolsCommand(), 'gui':None},
    {'name':'loadMeasureTools', 'cmd':MeasureToolsCommand(), 'gui':None},
    {'name':'loadGeomTools', 'cmd':GeomToolsCommand(), 'gui':None},
    {'name':'loadCameraTools', 'cmd':CameraToolsCommand(), 'gui':None},
    {'name':'loadAppearanceTools', 'cmd':AppearanceToolsCommand(), 'gui':None},
    {'name':'loadClipPTools', 'cmd':ClipPToolsCommand(), 'gui':None},
]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
