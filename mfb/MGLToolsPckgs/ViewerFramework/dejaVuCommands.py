## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

"""
This module implements classes relative to DejaVu.
"""
# $Header: /opt/cvs/python/packages/share1.5/ViewerFramework/dejaVuCommands.py,v 1.141.2.1 2011/04/08 21:21:21 sargis Exp $
#
# $Id: dejaVuCommands.py,v 1.141.2.1 2011/04/08 21:21:21 sargis Exp $
#


import numpy.oldnumeric as Numeric
import types
import os
import string
import Tkinter, Pmw
from math import pi, pow
from time import time, sleep
import tkMessageBox

from mglutil.util.callback import CallbackManager, CallBackFunction
from mglutil.math.rotax import rotax
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser, SaveButton
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from mglutil.util.misc import ensureFontCase
from DejaVu.colorMap import ColorMap
from DejaVu.ColormapGui import ColorMapGUI
from DejaVu.colorTool import RGBRamp, RedWhiteBlueRamp,RedWhiteRamp, \
        WhiteBlueRamp,GreyscaleRamp 
from DejaVu.colorTool import RGBARamp, RedWhiteBlueARamp,RedWhiteARamp, \
        WhiteBlueARamp
from DejaVu.Geom import Geom
from DejaVu.Spheres import Spheres

from ViewerFramework.VFCommand import Command, ICOM, CommandGUI
from ViewerFramework.VF import ViewerFramework
from mglutil.gui.BasicWidgets.Tk.colorWidgets import ColorChooser, BackgroundColorChooser
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser, \
     kbScrolledListBox
from opengltk.OpenGL import GL
from mglutil.util.packageFilePath import getResourceFolder

class ResetView(Command):

    def doit(self):
        vi = self.vf.GUI.VIEWER
        vi.Reset_cb()
        vi.Normalize_cb()
        vi.Center_cb()
        
    def guiCallback(self, event=None):
        self.doitWrapper()

    def __call__(self, **kw):
        """None <- ResetView( self, **kw)
        resets transformation on root object, translates and scales the scene
        to fit in viewport and sets the center of rotation to be the center of
        the scene
        """
        apply( self.doitWrapper, (), kw )

ResetViewGUI = CommandGUI()
ResetViewGUI.addToolBar('Reset View', icon1='icon-focus.gif', 
                        balloonhelp='Reset view, normalize and center',
                        type='ToolBarButton', index=9)

class ToggleNpr(Command):
    def doit(self, npr=1):
        if npr == 1:
            self.vf.GUI.VIEWER.GUI.contourTk.set(True)
            self.vf.GUI.VIEWER.cameras[0].Set(contours=True,
                                              tagModified=False)
            GL.glFinish()
            self.vf.GUI.VIEWER.GUI.showCurveTool() 
            self.vf.GUI.VIEWER.GUI.continuousRamp()
                        
        else:
            self.vf.GUI.VIEWER.GUI.contourTk.set(False)
            self.vf.GUI.VIEWER.cameras[0].Set(contours=False,
                                              tagModified=False)
            self.vf.GUI.VIEWER.GUI.GraphToolpanel.withdraw()                                  
            
    def guiCallback(self):
        val = self.GUI.menuCheckbuttonVar.get()
        self.doitWrapper( *(val,), **{'redraw':1})


    def __call__(self, npr=1, **kw):
        """None <- toggleNpr( self, npr=1, **kw)
        npr : flag when set to 1 toggle npr mode on when set to 0 turns
                 npr mode off
        """
        self.GUI.menuCheckbuttonVar.set(npr)

        self.doitWrapper( *(npr,), **kw )

toggleNprGuiDescr = {'widgetType':'Button', 'barName':'Toolbar',
                        'buttonName':'photo/cartoon'}
        
ToggleNprGUI = CommandGUI()
ToggleNprGUI.addToolBar('photo_cartoon', icon1 = 'npr.png', 
                         balloonhelp = 'Toggle photo/cartoon modes', index = 9)

ToggleNprMenuGUI = CommandGUI()
ToggleNprMenuGUI.addMenuCommand('menuRoot', 'Display', 'Cartoon',
                                menuEntryType='checkbutton')


class ToggleStereo(Command):
    def doit(self, stereo='MONO'):

        if self.vf.GUI.VIEWER.currentCamera.stereoMode == stereo:
            return

        if self.vf.GUI.VIEWER.activeStereoSupport is True:
            if stereo == 'STEREO_BUFFERS':
                self.vf.GUI.rebuildCamera(stereo='native')
                self.vf.GUI.VIEWER.currentCamera.Set( stereoMode=stereo,
                                                      tagModified=False )
            elif self.vf.GUI.VIEWER.currentCamera.stereoMode == 'STEREO_BUFFERS':
                self.vf.GUI.VIEWER.currentCamera.Set( stereoMode=stereo,
                                                      tagModified=False )
                self.vf.GUI.rebuildCamera(stereo='none')
            else:
                self.vf.GUI.VIEWER.currentCamera.Set( stereoMode=stereo,
                                                      tagModified=False )
        else:
            if stereo == 'STEREO_BUFFERS':
                # that way when we select STEREO_BUFFERS the camera is always rebuilt
                # it is a way to obtain a screen refresh
                self.vf.GUI.rebuildCamera(stereo='none')
                
                msg = """Stereo buffers are not present
or not enabled on this system.

enableStereo must be set to True in:
~/.mgltools/(ver_number)/DejaVu/_dejavurc
"""
                #self.warningMsg(msg)
                tkMessageBox.showerror('Stereo Buffers Error', msg)
                stereo = 'MONO'
                self.vf.GUI.toolbarCheckbuttons['mono_stereo']['Variable'].set(stereo)
            self.vf.GUI.VIEWER.currentCamera.Set( stereoMode=stereo,
                                                  tagModified=False )


    def guiCallback(self):
        val = {}
        val['stereo'] = self.vf.GUI.toolbarCheckbuttons['mono_stereo']['Variable'].get()
        val['redraw'] = 1
        apply( self.doitWrapper, (), val )


    def __call__(self, stereo=1, **kw):
        """None <- toggleStereo( self, stereo=1, **kw)
stereo : flag when set to 1 toggle stereo mode on when set to 0 turns
mono mode on
"""
        self.vf.GUI.toolbarCheckbuttons['mono_stereo']['Variable'].set(stereo)
        if stereo:
            kw['stereo'] = 'STEREO_BUFFERS' # was 'native'
        else:
            kw['stereo'] = 'MONO' # was 'none'
        apply( self.doitWrapper, (), kw )

stereoRadioLabels = [
                'mono (disabled)', 
                'SHUTTER GLASSES (on enabled systems)',
                'side by side cross',
                'side by side straight',
                'RED ****** CYAN',
                'red       green',
                'red        blue',
                'yellow     blue',
                'cyan        red',
                'green       red',
                'blue        red',
                'blue     yellow',
              ]

stereoRadioValues = [
                'MONO', 
                'STEREO_BUFFERS',
                'SIDE_BY_SIDE_CROSS',
                'SIDE_BY_SIDE_STRAIGHT',
                'COLOR_SEPARATION_RED_GREENBLUE',
                'COLOR_SEPARATION_RED_GREEN',
                'COLOR_SEPARATION_RED_BLUE',
                'COLOR_SEPARATION_REDGREEN_BLUE',
                'COLOR_SEPARATION_GREENBLUE_RED',
                'COLOR_SEPARATION_GREEN_RED',
                'COLOR_SEPARATION_BLUE_RED',
                'COLOR_SEPARATION_BLUE_REDGREEN',
              ]

toggleStereoGuiDescr = {'widgetType':'Menu', 'barName':'Toolbar',
                        'buttonName':'mono/stereo'}

ToggleStereoGUI = CommandGUI()
ToggleStereoGUI.addToolBar('mono_stereo', icon1='stereo.gif', 
                           type ='MenuRadiobutton', 
                           radioLabels=stereoRadioLabels,
                           radioValues=stereoRadioValues,
                           radioInitialValue=stereoRadioValues[0],
                           balloonhelp='Toggle mono/stereo', index = 6)



class TransformObject(Command):

    def doit(self, transformation, geomName, matrix):
        # should be
        # geomName, rot = None, trans = None, scale = None, mat = None, set = 1
        if not self.vf.hasGui:
            return
        vi = self.vf.GUI.VIEWER
        geometry = vi.FindObjectByName(geomName)
        
        if not geometry:
            print 'WARNING: geometry name  %s not found'%geomName
            return

        # set the vi.currentObject to be the object to transform
        oldCurrent = vi.currentObject
        vi.SetCurrentObject(geometry)

        # transform only the given geometry.
        if vi.redirectTransformToRoot == 1:
            old = vi.redirectTransformToRoot
            vi.TransformRootOnly(0)
        else:
            old = 0
        
        if transformation[:3]=='rot':
            mat = Numeric.reshape(Numeric.array(matrix, 'f'), (16,))
            geometry.SetRotation(mat)

        elif transformation[:3]=='tra':
            mat = Numeric.reshape(Numeric.array(matrix, 'f'), (3,))
            geometry.SetTranslation(mat)

        elif transformation[:3]=='sca':
            mat = Numeric.reshape(Numeric.array(matrix, 'f'), (3,))
            geometry.SetScale(mat)

        elif transformation[:3]=='piv':
            mat = Numeric.reshape(Numeric.array(matrix, 'f'), (3,))
            geometry.SetPivot(mat)

        # do not understand those two lines ?????
        if self != vi.rootObject:
            vi.deleteOpenglList()

        # Put everything back like it was before.
        if old == 1:
            vi.TransformRootOnly(1)
        vi.SetCurrentObject(oldCurrent)

    def __call__( self, transformation, object, matrix, **kw):
        """ None <- tranformObject( transformation, object, matrix, **kw)
        transformation   : type of transformation
                           rotation      : 'rot'
                           translation   : 'tra'
                           scaling       : 'sca'
                           pivot         : 'piv'
        object           : the geometry to be transformed
        matrix           : transformation matrix to be applied to the object
        """
        if not kw.has_key('redraw'):
            kw['redraw']=1
        apply(self.doitWrapper, (transformation, object, matrix), kw)


class TransformCamera(Command):

    def doit(self, transformation, matrix, camIndex):
        # should be
        # geomName, rot = None, trans = None, scale = None, mat = None, set = 1
        if not self.vf.hasGui:
            return
        vi = self.vf.GUI.VIEWER
        cam = vi.cameras[camIndex]
        
        if transformation=='fov':
            cam.Set(fov=matrix)
            
        elif transformation[:3]=='rot':
            mat = Numeric.reshape(Numeric.array(matrix, 'f'), (16,))
            cam.SetRotation(mat)

        elif transformation[:3]=='tra':
            mat = Numeric.reshape(Numeric.array(matrix, 'f'), (3,))
            cam.SetTranslation(mat)

        elif transformation[:3]=='sca':
            mat = Numeric.reshape(Numeric.array(matrix, 'f'), (3,))
            cam.SetScale(mat)

        elif transformation[:3]=='piv':
            mat = Numeric.reshape(Numeric.array(matrix, 'f'), (3,))
            cam.SetPivot(mat)


    def __call__( self, transformation, matrix, camIndex=0, **kw):
        """ None <- tranformCamera( transformation, matrix, camIndex=0, **kw)
        transformation   : type of transformation
                           rotation      : 'rot'
                           translation   : 'tra'
                           scaling       : 'sca'
                           pivot         : 'piv'
                           field of view : 'fov'
        matrix           : transformation matrix to be applied to the object
        camIndex         : index of camera (defaults to 0)
        """
        if not kw.has_key('redraw'):
            kw['redraw']=1
        apply(self.doitWrapper, (transformation, matrix, camIndex), kw)


class SetObject(Command):

    def doit(self, object, **kw):
        if not self.vf.hasGui:
            return
        vi = self.vf.GUI.VIEWER
        viewerObj = vi.FindObjectByName(object)
        if not viewerObj:
            print 'WARNING: object %s not found'%object
            return
        kw['tagModified']=False
        apply( viewerObj.Set, (), kw)


        
class SetCamera(Command):

    def doit(self, camera, **kw):
        if not self.vf.hasGui:
            return
        vi = self.vf.GUI.VIEWER
        viewerCameras = filter(lambda x, name=camera: x.name==name, vi.cameras)
        if len(viewerCameras)==1:
            viewerCamera = viewerCameras[0]
        elif len(viewerCameras)>1:
            print 'WARNING: more than one camera found for the name: %s'%camera
            return
        else:
            print 'WARNING: camera %s not found'%camera
            return
        #print kw
        kw['tagModified']=False
        apply( viewerCamera.Set, (), kw)



class SetLight(Command):

    def doit(self, light, **kw):
        if not self.vf.hasGui:
            return
        vi = self.vf.GUI.VIEWER
        viewerLights = filter(lambda x, name=light: x.name==name, vi.lights)
        if len(viewerLights)==1:
            viewerLight = viewerLights[0]
        elif len(viewerLights)>1:
            print 'WARNING: more than one light found for the num: %d'%lightnum
            return
        else:
            print 'WARNING: light nb: %d not found'%lightnum
            return

        kw['tagModified']=False
        apply( viewerLight.Set, (), kw)



class AddClipPlane(Command):
    def doit(self, object, clip, side=-1, inh=0):
        if not self.vf.hasGui:
            return
        vi = self.vf.GUI.VIEWER
        viewerObj = vi.FindObjectByName(object)
        if not viewerObj:
            print 'WARNING: object %s not found'%object
            return

        viewerClips = filter(lambda x, name=clip: x.name==name, vi.clipP)
        if len(viewerClips)==1:
            viewerClip = viewerClips[0]
        elif len(viewerClips)>1:
            print 'WARNING: more than one clipping plane found for the name: %s'%clip
            return
        else:
            print 'WARNING: camera %s not found'%clip
            return

        viewerObj.AddClipPlane( viewerClip, side, inh )


        
class SetClip(Command):

    def doit(self, clip, **kw):
        if not self.vf.hasGui:
            return
        vi = self.vf.GUI.VIEWER
        viewerClips = filter(lambda x, name=clip: x.name==name, vi.clipP)
        if len(viewerClips)==1:
            viewerClip = viewerClips[0]
        elif len(viewerClips)>1:
            print 'WARNING: more than one clipping plane found for the name: %s'%clip
            return
        else:
            print 'WARNING: camera %s not found'%clip
            return

        kw['tagModified']=False
        apply( viewerClip.Set, (), kw)



class ViewPoints(Command):
    """None <- view(name, mode='save' or 'restore')
    Command to save current transformation of root node
    """

    def __init__(self):
        Command.__init__(self)
        self.views = []
        self.names = []
        self.current = -1


    def doit(self, name=None, index=None, mode='add'):
        if not self.vf: return
        root = self.vf.GUI.VIEWER.rootObject
        if name is None:
            name = 'View'+str(len(self.views))
        if mode=='set':
            self.names = [ name ]
            self.views = [ (root.translation, root.rotation, root.scale,
                            root.pivot) ]
            self.current = 1
            
        elif mode=='add':
            self.names.append( name )
            self.views.append( (root.translation, root.rotation, root.scale,
                                root.pivot) )
            self.current = len(self.views)
            
        elif mode=='previous':
            self.names.append( name )
            self.views.append( (root.translation, root.rotation, root.scale,
                                root.pivot) )
            index = max(self.current-1, 0)
            self.go(index)
                
        elif mode=='next':
            index = min(self.current+1, len(self.views))
            self.go(index)

        elif mode=='go':
            if index>-1 and index<len(self.views):
                self.go(index)

    def go(self, index):
        #print 'going to ',self.names[index]
        tr = self.views[index]
        root = self.vf.GUI.VIEWER.rootObject
        root.translation = tr[0]
        root.rotation = tr[1]
        root.scale = tr[2]
        root.pivot = tr[3]
        self.current=index
        self.vf.GUI.VIEWER.Redraw()

    def __call__(self, name=None, mode='add', **kw):
        """None <- viewerPoint(name=None, mode='add', **kw)
        mode in 'set', 'add', 'go', 'next', previous'
        """
        kw['name'] = name
        kw['mode'] = mode
        apply( self.doitWrapper, (), kw)



class RotateScene(Command):
    """None <- rotateScene(axis=(0,1,0), stepSize=0.0, nbSteps=0, pause=0.0, object=None)
Command to rotate 'object' about an arbitrary 'axis' 'nbSteps' times
object defaults to the root object (i.e. the complete scene)
by default the rotation will be a full turn in increments of 5 degrees.
Specifying a nSteps of -1 will create an endless loop.
The commands stop() method has to be called to break out of the loop
    """

    def __init__(self):
        Command.__init__(self)
        self._redraw = True


    def doit(self, axis=(0,1,0), stepSize=0.0, nbSteps=0, pause=0.0,
             object=None):
        if stepSize is None or stepSize==0.0:
            stepSize = 5*pi/180.
        else:
            stepSize = stepSize*pi/180.

        if nbSteps is None or nbSteps==0:
            nbSteps = pi*2/stepSize
 
        viewer = self.vf.GUI.VIEWER
        if object is None:
            object = viewer.rootObject
            
        self.stopFlag = 0
        step = 0
        matrix = rotax(Numeric.zeros(3), Numeric.array( axis ), stepSize)
        t1 = time()
        while not self.stopFlag:
            object.ConcatRotation(matrix.ravel())
            if self._redraw:
                viewer.Redraw()
                viewer.cameras[0].update()
            if pause > 0.0:
                sleep(pause)
            step = step+1
            if nbSteps > 0.0 and step >= nbSteps:
                break
        t2 = time()
        #print 'FrameRate = %4.1f'%(step/(t2-t1),), step
        

    def stop(self):
        self.stopFlag = 1

        
    def __call__(self, axis=(0,1,0), stepSize=0.0, nbSteps=0,
                 pause=0.0, object=None, **kw):
        """None <- rotateScene(axis=(0,1,0), stepSize=0.0, nbSteps=0, pause=0.0, object=None)
"""
        self._redraw = kw.get('redraw', True)
        kw['redraw'] = False
        apply( self.doitWrapper, (axis, stepSize, nbSteps, pause), kw )



class CenterScene(Command):
    """None <- centerScene()
    Command to scale and translate the scene to make it fit in the view frustum
    """

    def onAddCmdToViewer(self):
        self.vf.userpref.add('Center Scene','firstObjectOnly',
               validValues=['firstObjectOnly','always', 'never', 'ask'],
               callbackFunc=[self.doit_cb],
               category="DejaVu",
               doc="""the value of this preference defines whether\
the sceen is centered and tranformed to fit into the field\
of view when a new object is loaded""")
        


    def doit_cb(self, name, old_value, new_value):
        if self.vf.hasGui: 
            pass

        
    def doit(self, mode=None):
        choices = self.vf.userpref['Center Scene']['validValues']
        if mode is None: mode=self.vf.userpref['Center Scene']['value']
        else: assert mode in choices
        if mode=='never': return
        if mode==choices[0] and len(self.vf.objects)>1:
            return
        if mode=='ask':
            from SimpleDialog import SimpleDialog
            t= 'Do you want to center scene?'
            d=SimpleDialog(self.vf.GUI.ROOT, text=t,
                buttons=['yes','no'], default=0,
                title='Center Scene?')
            ok=d.go()
            if ok==1: return
        if self.vf.hasGui:
            self.vf.GUI.VIEWER.NormalizeCurrentObject()
            self.vf.GUI.VIEWER.CenterCurrentObject()



class CenterGeom(Command):

    def setupUndoBefore(self, object, point):
        piv = tuple(object.pivot)
        self.addUndoCall( (object, piv), {}, self.vf.centerGeom.name )

    def doit(self, object, point):
        object.SetPivot( point )

    def __call__(self, object, point, **kw):
        """None <- centerGeom(geom, point3D) set the center of rotation
Geom can be either a tring or an instance of a DejaVu.Geom.Geom
The point3D is given in the global coodinates system.
"""
        if type(object)==types.StringType:
            vi = self.vf.GUI.VIEWER
            object = vi.FindObjectByName(object)
        apply( self.doitWrapper, (object, point), kw)
        

class CenterSceneOnPickedPixel(Command, ICOM):
    """This command allows a user to set the center of rotation of the entire
scene to the picked pixel.
"""
    
##     def onAddCmdToViewer(self):
##         if self.vf.hasGui:
##             sph = Spheres('flashSphere', vertices=((0,0,0),), radii=(0.3,),
##                           visible=0, materials=((0,1,1),))
##             self.vf.GUI.VIEWER.AddObject(sph, parent=self.vf.GUI.miscGeom)
##             self.flashSphere = sph
            
    def __init__(self, func=None):
        Command.__init__(self, func)
        ICOM.__init__(self)


    def getObjects(self, pick):
        # we override this else we get pick.hits but we need pick.even
        return pick


    def setupUndoBefore(self, obj):
        root = self.vf.GUI.VIEWER.rootObject
        piv = tuple(root.pivot)
        self.addUndoCall( (root, piv), {}, self.vf.centerGeom.name )

        
    def doit(self, object):
        g, background = self.vf.GUI.VIEWER.get3DPointFromPick(object)
        #print 'CenterSceneOnPickedVertices', g, background
        if not background:
            self.vf.centerGeom( 'root', g, topCommand=0, log=1, setupUndo=1)
            self.vf.flashSphere.Set(vertices=(g,))
            self.vf.flashSphere.flashT()


    def __call__(self, pick, **kw):
        """This command allows a user to set the center of rotation of the entire
scene to the a vertex specified by a picking operation.
This command is an interactive picking command and is aware of instance
matrices.
"""
        # we do not want this command to log or undo itself
        kw['topCommand'] = 0
        kw['busyIdle'] = 1
        apply( self.doitWrapper, (pick,), kw )


class CenterSceneOnVertices(Command, ICOM):
    """This command allows a user to set the center of rotation of the entire
scene to the a vertex specified by a picking operation.
This command is an interactive picking command and is aware of instance
matrices.
"""
    
    def __init__(self, func=None):
        Command.__init__(self, func)
        ICOM.__init__(self)


    def setupUndoBefore(self, obj):
        root = self.vf.GUI.VIEWER.rootObject
        piv = tuple(root.pivot)
        self.addUndoCall( (root, piv), {}, self.vf.centerGeom.name )

        
    def doit(self, objects):
        # objects is pick.hist = {geom: [(vertexInd, intance),...]}
        vt = ViewerFramework.transformedCoordinatesWithInstances(self.vf,
                                                                 objects)
        g = [0,0,0]
        i = 0
        for v in vt:
            g[0] += v[0]
            g[1] += v[1]
            g[2] += v[2]
            i+=1
        g[0] = g[0]/i
        g[1] = g[1]/i
        g[2] = g[2]/i

        self.vf.centerGeom( 'root', g, topCommand=0, log=1, setupUndo=1)


    def __call__(self, nodes, **kw):
        """This command allows a user to set the center of rotation of the entire
scene to the a vertex specified by a picking operation.
This command is an interactive picking command and is aware of instance
matrices.
"""
        # we do not want this command to log or undo itself
        kw['topCommand']=0
        kw['busyIdle']=1
        apply( self.doitWrapper, (nodes,), kw )



class AlignGeoms(Command):

    # this is the non-interactive command (see AlignGeomsPCOM) which
    # does log itself
    
        # FIXME: A UNDO METHOD SHOULD BE IMPLEMENTED HERE
        
##      def setupUndoBefore(self, object):
##          geom1 = object[0]
##          t = geom1.translation
##          self.addUndoCall( (geom1.getName(),root, piv), {}, self.vf.centerGeom.name )

    def doit(self, geom1, vertInd1, geom2, vertInd2):
        vi = self.vf.GUI.VIEWER

        # "compute" translation vector
        vert1 = self.getVertex(geom1, vertInd1)
        vert2 = self.getVertex(geom2, vertInd2)
        v = []
        v.append(vert2[0] - vert1[0])
        v.append(vert2[1] - vert1[1])
        v.append(vert2[2] - vert1[2])
        v = Numeric.array(v)

        # make sure geom1.Ri is up-to-date by calling FrameTransform()
        # oldCurrent = vi.currentObject
        geom1.FrameTransform()
        if vi.redirectTransformToRoot == 1:
            old = vi.redirectTransformToRoot
            vi.TransformRootOnly(0)
        else:
            old = 0

        # Note: adding the new translation is the
        # same as matrixmultiply Ri & v and then ConcatTranslation
        geom1.translation = geom1.translation + v

##  	d = Numeric.array( v )
##  	d = Numeric.concatenate( (d, [1.0]) )  # go to homogenous coords
##          rot = Numeric.reshape( geom1.Ri, (4,4) )
##          trans =  Numeric.dot( rot, d )[:3]

##          # Note to self: if you use SetTranslation instead it only works
##          # the first time!
##          geom1.ConcatTranslation(trans)

        if old == 1:
            vi.TransformRootOnly(1)


    def getVertex(self, geom, index):
        verts = geom.TransformedCoords(geom.LastParentBeforeRoot() )
        pickedVerts = Numeric.take(verts, index)
        vertex = Numeric.sum(pickedVerts)/len(pickedVerts)
        return list(vertex)


    def __call__(self, geom1, vertInd1, geom2, vertInd2, **kw):
        """describe this command for a programmer"""
        if type(geom1) is types.StringType :
            geom1 = self.vf.GUI.VIEWER.FindObjectByName(geom1)
        if type(geom2) is types.StringType :
            geom2 = self.vf.GUI.VIEWER.FindObjectByName(geom2)
        apply( self.doitWrapper, (geom1, vertInd1, geom2, vertInd2), kw )



class AlignGeomsPCOM(Command, ICOM):
    """Pick one or more vertices on geom1 and one or more vertices on geom2.
If more than one vertex is selected, the middle point (point1 and 2) of these
vertices is computed. A translation vector point2-point1 is computed and
applied to geom1. Point1 and point2 are displayed as spheres during this
operation and deleted when finished."""

    # This is the interactive picking command, which does not log itself and
    # will call AlignGeoms, which logs
    
    def __init__(self, func=None):
        Command.__init__(self, func)
        ICOM.__init__(self)
        self.vertInd1 = None # vertex index list of picked geom1
        self.vertInd2 = None # vertex index list of picked geom2
        self.geom1 = None # picked geom1
        self.geom2 = None # picked geom2


#    def onAddCmdToViewer(self):
#        if self.vf.hasGui:
#            if not self.vf.commands.has_key('setICOM'):
                ## FIXME makes ViewerFrameworj depend on PMV ... BAD !
#                self.vf.loadCommand('interactiveCommands', 'setICOM', 'Pmv',
#                                topCommand=0)
#            miscGeom = self.vf.GUI.miscGeom
#            self.masterGeom = Geom('pickSpheresGeom',shape=(0,0),
#                                   pickable=0, protected=True)
#            self.masterGeom.isScalable = 0
#            self.vf.GUI.VIEWER.AddObject(self.masterGeom, parent=miscGeom)
#            self.spheres = Spheres(name='pickSpheres', shape=(0,3),
#                               inheritMaterial=0, radii=0.3, quality=15,
#                               materials = ((0.,1.,0.),), protected=True) 
#
#            self.vf.GUI.VIEWER.AddObject(self.spheres, parent=self.masterGeom)


    def stopICOM(self):
        # Reset everything if ICOM is stopped
        self.vertInd1 = None 
        self.vertInd2 = None
        self.geom1 = None
        self.geom2 = None
#        self.spheres.Set(vertices=[], tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        
        
    def doit(self, object):
        if len(object)==0:
            return 'ERROR' # prevent logging if nothing picked

        vi = self.vf.GUI.VIEWER
        # first pick event
        if self.vertInd1 is None:
            self.geom1 = object[0]
            self.vertInd1 = self.getVertexIndex()
            vertex = self.getSphereVertex(self.geom1, self.vertInd1)
            self.spheres.Add(vertices=[vertex,])
            vi.Redraw()
        # second pick event
        elif self.vertInd1 is not None:
            self.vertInd2 = self.getVertexIndex()
            self.geom2 = object[0]
            vertex = self.getSphereVertex(self.geom1, self.vertInd1)
            self.spheres.Add(vertices=[vertex,])
            vi.Redraw()
            # reset to first picked  if vertices in same geom were picked
            if self.geom1 == self.geom2:
                self.geom2 = None
                self.vertInd2 = None
                oldspheres = self.spheres.vertexSet.vertices.array
                self.spheres.Set(vertices=oldspheres[:1], tagModified=False)
                vi.Redraw()
                return
                
            # call the non-interactive, logable command
            self.vf.alignGeomsnogui(self.geom1, self.vertInd1,
                                     self.geom2, self.vertInd2,
                                     topCommand=0, log=1, setupUndo=1)
            # now we are done and can reset everything 
            self.spheres.Set(vertices=[], tagModified=False)
            vi.Redraw()
            self.vertInd1 = None
            self.vertInd2 = None
            self.geom1 = None
            self.geom2 = None


    def getSphereVertex(self, geom, index):
        verts = geom.TransformedCoords( geom.LastParentBeforeRoot() )
        pickedVerts = Numeric.take(verts, index)
        vertex = Numeric.sum(pickedVerts)/len(pickedVerts)
        return list(vertex)
    

    def getVertexIndex(self):
        vi = self.vf.GUI.VIEWER
        pick = vi.lastPick
        geom, vertIndList = pick.hits.items()[0]
        return vertIndList[1]


    def __call__(self, nodes, **kw):
        """describe this command for a programmer"""
        # we do not want this command to log or undo itself
        kw['topCommand']=0
        kw['busyIdle']=1
        apply( self.doitWrapper, (nodes,), kw )



class PrintGeometryName(Command, ICOM):

    def __init__(self, func=None):
        Command.__init__(self, func)
        ICOM.__init__(self)

        
    def doit(self, objects):
        # object is a list of geometries
        for o in objects:
            self.vf.message(o.name)
            

    def __call__(self, objects, topCommand=0, **kw):
        # we do not want this command to log or undo itself
        if not kw.has_key('topCommand'): kw['topCommand'] = topCommand
        apply( self.doitWrapper, (objects,), kw )



class StopContinuousPicking(Command):
    def start(self):	
        #self.vf.GUI.ehm.RemoveCallback("<Motion>", 'motion_cb')
        self.vf.GUI.removeCameraCallback("<Motion>", 'motion_cb')

    def __call__(self, *args):
        self.start()

        
    def guiCallback(self):
        self.start()



class StartContinuousPicking(Command):
    """Start the contiguous selection mode"""

    def __init__(self, delay=100):
        Command.__init__(self)
        self.delay=delay
        self.alarmID = None
        self.cbManager = CallbackManager()

    def onAddCmdToViewer(self):
        self.cbManager.AddCallback(CallBackFunction( self.vf.unsolicitedPick))

    def start(self):	
        self.vf.GUI.addCameraCallback("<Motion>", self.motion_cb)


    def __call__(self, *args):
        self.start()

    def guiCallback(self):
        self.start()

    def _pick(self, event):
        # has to be first transformed in a DejaVu Camera Pick object
        pick = self.vf.DoPick( event.x, event.y, event=event )
        if pick:
            self.cbManager.CallCallbacks(pick)
        
    def motion_cb(self, event=None):
        if (self.alarmID):
            self.vf.GUI.ROOT.after_cancel(self.alarmID)
        self.alarmID = self.vf.GUI.ROOT.after(self.delay, self._pick, event)



class LoadColorMap(Command):
    """
    Command to Load a Color Map 
    """
    def onAddCmdToViewer(self):
        # load the rgb256_map  by default
        import ViewerFramework
        vfpath = ViewerFramework.__path__[0]
        idir = os.path.join(vfpath, 'ColorMaps/')
        cmap = os.path.join(idir, "rgb256_map.py")
        self.vf.loadColorMap(cmap, log=0)

    def guiCallback(self):
        # Update the level if the form exists already.
        import ViewerFramework
        vfpath = ViewerFramework.__path__[0]
        idir = os.path.join(vfpath, 'ColorMaps/')
        filename = self.vf.askFileOpen(idir=idir,
            types=[('color map files:', '*_map.py'),\
                   ('all files:', '*')],\
                title = 'Color Map File:')
        if not filename: return
        apply(self.doitWrapper, (filename,), {})


    def doit(self, filename):
        #colormap can be built from a filename
        name = os.path.splitext(os.path.basename(filename))[0]
        l = {}
        g = {}
        execfile(filename, g, l)
        newColorMap = None
        for name, object in l.items():
            if isinstance(object, ColorMap):
                newColorMap = object
                break
            
        #newColorMap = ColorMap(name, filename=filename)
        if newColorMap:
            #name should be uniq already
            for k in self.vf.colorMaps.keys():
                if k==name:
                    newColorMap.name = name + '_' + str(self.vf.colorMapCt)
                    self.vf.colorMapCt = self.vf.colorMapCt + 1
            self.vf.addColorMap(newColorMap)
            
        return newColorMap

    def __call__(self, filename, **kw):
        """
        None <- loadColorMap(filename)
        filename: file containing colorMap *_map.py
        """
        return apply( self.doitWrapper, (filename,), kw)



LoadColorMapGUIDescr =  {'widgetType':'Menu', 'menuBarName':'menuRoot',
                         'menuButtonName':'File',
                         'menuEntryLabel':'ColorMap'}               
 
LoadColorMapGUI = CommandGUI()
LoadColorMapGUI.addMenuCommand('menuRoot', 'File', 'Color Map', cascadeName='Import')



class SaveColorMap(Command):
    """
    Command to Save a Color Map 
    """

    def logString(self, *args, **kw):
        """return None as log string as we don't want to log this
"""
        pass



    def buildFormDescr(self, formName):
        if formName == 'saveCM':
            ifd = InputFormDescr(title = 'Save Color Map')
            cmNames = map(lambda x: (x, None), self.vf.colorMaps.keys())
            ifd.append({'name':'colorMapName',
                            'widgetType':ListChooser,
                            'wcfg':{'entries': cmNames,
                                    'title':'Choose a color map to save:',
                                    'lbwcfg':{'exportselection':0},
                                    'mode':'single','withComment':0, },
                            'gridcfg':{'sticky':'we', 'rowspan':4, 'padx':5}})
            return ifd



    def guiCallback(self):
        #force a redraw of form
        keys = self.vf.colorMaps.keys()
        if not len(keys):
            self.vf.warningMsg('currently no color maps in viewer')
            return
                
        if self.cmdForms.has_key('saveCM'):
            descr = self.cmdForms['saveCM']

        val = self.showForm('saveCM', force=1)
        if val=={}: return
        if not val: return
        if not len(val['colorMapName']):
            return 
        colorMapName = val['colorMapName'][0]
        import ViewerFramework
        vfpath = ViewerFramework.__path__[0]
        idir = os.path.join(vfpath, 'ColorMaps/')
        filename = self.vf.askFileSave(idir=idir,
            types=[('color map files:', '*_map.py'),\
                   ('all files:', '*')],\
            title = 'Color Map File:')
        if not filename: return
        apply(self.doitWrapper, (colorMapName, filename,), {})


    def doit(self, colorMapName, filename):
        assert colorMapName in self.vf.colorMaps.keys(), 'no colorMap of that name'
        colorMap = self.vf.colorMaps[colorMapName]
        colorMap.write(filename)
            

    def __call__(self, colorMapName, filename, **kw):
        """
        None <- saveColorMap(filename)
        colorMapName: name of colorMap to be written
        filename: file containing colorMap
        """
        apply( self.doitWrapper, (colorMapName, filename,), kw)



SaveColorMapGUIDescr =  {'widgetType':'Menu', 'menuBarName':'menuRoot',
                              'menuButtonName':'File',
                              'menuEntryLabel':'Color map'}               
 
SaveColorMapGUI = CommandGUI()
SaveColorMapGUI.addMenuCommand('menuRoot', 'File', 'Color Map', cascadeName='Save')



class CreateColorMap(Command):
    """
    Command to Create a Color Map 
    NB: colormaps are created from files by LoadColorMap
    """

    def guiCallback(self):
        apply(self.doitWrapper, (), {'viewer':self.vf.GUI.VIEWER, 'log':0})


    def accept_cb(self, event=None):
        #print "accept_cb"
        self.cmg.apply_cb()
        if self.colorMaps.has_key('self.cmg.name') is False:
            self.vf.addColorMap(self.cmg)
            self.cmg.apply.configure(command=self.cmg.apply_cb)


    def doit(self, name='colormap', ramp=None, geoms={},
             legend=None,  mini='not passed', maxi='not passed', viewer=None, log=0):

        if not viewer:
            viewer = self.vf.GUI.VIEWER

        if ramp and type(ramp) is types.StringType:
            #ramp can only be a string
            ramp = eval(ramp + '()')

        if name != 'colormap' and self.vf.colorMaps.has_key(name):
            self.cmg = self.vf.colorMaps[name]
            self.cmg.showColormapSettings_cb()
        else:
            i = 1
            while self.vf.colorMaps.has_key(name):
                name = 'colormap' + str(i)
                i += 1

            self.cmg = ColorMapGUI(name=name, ramp=ramp, viewer=viewer,
                                   mini=mini, maxi=maxi,
                                   allowRename=True, modifyMinMax=True)

        self.cmg.apply.configure(command=self.accept_cb)
        #self.cmg.apply.configure(text='Accept', command=self.accept_cb)
        ##FIX THIS TO BUILD LOG STRING FROM GUI ...???...


    def __call__(self, name='colormap', ramp='RGBARamp', filename=None, **kw):
        """
        None <- createColorMap(name, ramp='RGBARamp', filename=None, **kw)
        name:         identifier 
        ramp:         color ramp string ('RGBARamp', 'RedWhiteARamp',
                      'WhiteBlueARamp' or 'RedWhiteBlueARamp'
        """
        if not kw.has_key('redraw'): kw['redraw'] = 1
        if not kw.has_key('viewer'): kw['viewer'] = self.vf.GUI.VIEWER
        kw['ramp'] = ramp
        kw['name'] = name
        kw['log'] = 0
        apply( self.doitWrapper, (), kw)



CreateColorMapGUIDescr =  {'widgetType':'Menu', 'menuBarName':'menuRoot',
                              'menuButtonName':'Color',
                              'menuEntryLabel':'ColorMap'}               
 
CreateColorMapGUI = CommandGUI()
CreateColorMapGUI.addMenuCommand('menuRoot', 'Color', 'Create', cascadeName='Color Map')



class ColorMapEditor(Command):
    """
    Create a GUI to edit a color map object
    """
        
    def buildFormDescr(self, formName):
        if formName == 'editCM':
            self.interpOn = Tkinter.IntVar()
            #self.id = Tkinter.StringVar()
            self.showLabels = Tkinter.IntVar()
            self.showLabels.set(1)
            ifd = InputFormDescr(title = 'Select Color Map To Edit')
            #cmNames = self.vf.colorMaps.keys()
            cmNames = map(lambda x: (x, None), self.vf.colorMaps.keys())
            #could use this to build a new one
            #self.id.set(cmNames[0])
#            ifd.append({'widgetType':Pmw.ComboBox,
#            'name':'cmap',
#            'wcfg':{'label_text':'Color Maps',
#                    'entryfield_value':self.id.get(),
#                    'labelpos':'w',
#                    'listheight':'80',
#                    'scrolledlist_items': cmNames,
#                    #'selectioncommand': self.update,
#                    },
#            'gridcfg':{'sticky':'w'}})
            ifd.append({'name':'colorMapName',
                            'widgetType':ListChooser,
                            'wcfg':{'entries': cmNames,
                                    'title':'Choose a color map to edit:',
                                    'lbwcfg':{'exportselection':0},
                                    'mode':'single','withComment':0, },
                            'gridcfg':{'sticky':'we', 'rowspan':4, 'padx':5}})
            return ifd



    def guiCallback(self):
        # Update the level if the form exists already.
        if not len(self.vf.colorMaps.keys()):
            print 'no color maps in viewer'
            return
        if self.cmdForms.has_key('editCM'):
            descr = self.cmdForms['editCM'].descr
        val = self.showForm('editCM',force=1)
        if val=={}: return
        if not val: return
        cmap = val['colorMapName'][0]
        vi = self.vf.GUI.VIEWER
        apply(self.doitWrapper, (cmap,), {'viewer':vi, 'log':0})


    def doit(self, cmap, viewer=None):
        
        if type(cmap) is types.StringType:
            if self.vf.colorMaps.has_key(cmap):
                cmap=self.vf.colorMaps[cmap]
            else:
                print 'no such color map'

        assert isinstance(cmap, ColorMap)

        if isinstance(cmap, ColorMapGUI):
            if not cmap.master.winfo_ismapped():
                cmap.showColormapSettings_cb()
                self.cmg = cmap
        else:
            if viewer is None: 
                viewer = self.vf.GUI.VIEWER

            self.cmg = ColorMapGUI(cmap, viewer=viewer, allowRename=False, modifyMinMax=True)
            self.vf.colorMaps[self.cmg.name] = self.cmg


    def __call__(self, cmap, viewer=None, **kw):
        """
        None <- showCMGUI(cmap='cmap', **kw)
        cmap:         ColorMap or its name
        """
        if type(cmap) is types.StringType:
            if cmap not in self.vf.colorMaps.keys():
                print 'unknown color map name: ', cmap
                return 'ERROR'
            else:
                cmap = self.vf.colorMaps[cmap]
        elif not isinstance(cmap, ColorMap):
            print 'specified colormap not a ColorMap instance'
            return 'ERROR'
        if not viewer:
            viewer = self.vf.GUI.VIEWER
        kw['log'] = 0
        kw['viewer'] = viewer

        apply( self.doitWrapper, (cmap,), kw)



ColorMapEditorGUIDescr =  {'widgetType':'Menu', 'menuBarName':'menuRoot',
                           'menuButtonName':'Edit',
                           'menuEntryLabel':'ColorMap'}               
 
ColorMapEditorGUI = CommandGUI()
#EditColorMapGUI.addMenuCommand('menuRoot', 'Edit', 'ColorMap')
ColorMapEditorGUI.addMenuCommand('menuRoot', 'Color', 'Edit', cascadeName='Color Map')



class EditColorMap(Command):
    """
    Command to modify a color map object
    """

    def doit(self, cmap, ramp=None, mini=None, maxi=None):
        cfg = {}
        if ramp:
            cfg['ramp']=ramp
        if mini:
            cfg['mini']=mini
        if maxi:
            cfg['maxi']=maxi 
        apply( cmap.configure, (), cfg)
        
    def __call__(self, cmap, ramp=None, mini=None, maxi=None, **kw):
        """
        None <- editCM(cmap, ramp=None, mini=None,
                 maxi=None, name=None, **kw)
        """
        if type(cmap) is types.StringType:
            if cmap not in self.vf.colorMaps.keys():
                print 'unknown color map name: ', cmap
                return 'ERROR'
            cmap = self.vf.colorMaps[cmap]
        elif not isinstance(cmap, ColorMap):
            print 'specified colormap not a ColorMap instance'
            return 'ERROR'
        kw['ramp']=ramp
        kw['mini']=mini
        kw['maxi']=maxi
        apply( self.doitWrapper, (cmap,), kw)



class RenderLargeImageCommand(Command):
    """
Package : ViewerFramework
Module  : dejaVuCommands
Class   : RenderLargeImageCommand
Command : renderLargeImage

Description:
This command allows the user to enable the rendering of images
larger than the screen.

Synopsis:
None <- renderLargeImage(width=None, height=None, border=0,
                          outputFile='test.jpg', backbuffer=True)
width, height   : to specify either the width or the height.
border          : (default 0) specify the size of a border can be any
                  any small integer between 1 and 20.
outputFile      : path to a output file. Use .tif to avoid compression
backBuffer      : default True, Boolean flag turn to False to see
                  the tiles render.
checkeredBackground: (False)

Keywords : large, image, tile rendering
"""


    def logString(self, *args, **kw):
        """return None as log string as we don't want to log this
"""
        pass


    def doit(self,
             width=None,
             height=None,
             border=0,
             outputFile='test.tif',
             backBuffer=True,
             checkeredBackground=False):
        #print "RenderLargeImageCommand.doit"

        if width is None and height is None:
            self.warningMsg(
                "Please either specify the width or the height of the camera."
            )

        vfgui = self.vf.GUI

#        cam = vfgui.VIEWER.cameras[0]
#        camHeight = cam.height
#        camWidth = cam.width
#        camrootX = cam.master.master.master.winfo_rootx()
#        camrootY = cam.master.master.master.winfo_rooty()
#
#        # We set the camera to the biggest possible size to avoid multiple drawing
#        lLargestWidth = vfgui.screenWidth
#        lLargestHeight = lLargestWidth * float(height)/width
#        if lLargestHeight > vfgui.screenHeight:
#            lLargestHeight = vfgui.screenHeight
#            lLargestWidth = lLargestHeight * float(width)/height
#        status = self.vf.setCameraSize(lLargestWidth,
#                                       lLargestHeight,
#                                       xoffset=0,
#                                       yoffset=0,
#                                       topCommand=0)
#        if status=='ERROR':
#            return 'ERROR'

        vi = vfgui.VIEWER
        vi.stopAutoRedraw()
        vi.update()

        vi.startTileRendering(width=width,
                              height=height,
                              border=border,
                              outputFile=outputFile,
                              backBuffer=backBuffer,
                              checkeredBackground=checkeredBackground)
        vi.OneRedraw()

#        # set camera to its previous size and position
#        self.vf.setCameraSize(camWidth, 
#                              camHeight, 
#                              xoffset=camrootX,
#                              yoffset=camrootY, 
#                              topCommand=0)


    def __call__(self, width=None, height=None, border=0,
                 outputFile='test.jpg', backBuffer=True,
                 checkeredBackground=False, **kw):
        #print "RenderLargeImageCommand.__call__"
        kw['width'] = width
        kw['height'] = height
        kw['border'] = border
        kw['outputFile'] = outputFile
        kw['backBuffer'] = backBuffer
        kw['checkeredBackground'] = checkeredBackground
        kw['redraw'] = True
        apply(self.doitWrapper, (), kw)
        
        
    def guiCallback(self):
        #print "RenderLargeImageCommand.guiCallback"

        # in case we arrive here after a cancel and a resizing
        if self.cmdForms.has_key('tileRendering'):
            self.fixHeight_cb()
        
        val = self.showForm('tileRendering', 
                            okCfg={'text':'Render Image'},
                            cancelCfg={'text':'Cancel', 'command':self.cancel_cb} )
            
        if not val=={}:
            del val['constraint']
            if val.has_key('filebrowse'):
                del val['filebrowse']
            if val.has_key('outputFile') and not val['outputFile']:
                val['outputFile'] = './test.tif'
            val['redraw'] = False
            apply(self.doitWrapper, (), val)


    def getConstrainedWidth(self, mode, height, width):
        #print "RenderLargeImageCommand.getConstrainedWidth"
        # compute val2 as a function of val1
        if mode == 'square':
            return height
        elif mode == 'keep aspect ratio':
            cam = self.vf.GUI.VIEWER.currentCamera
            return round( height * cam.width/float(cam.height) )
        else:
            return width


    def getConstrainedHeight(self, mode, width, height):
        #print "RenderLargeImageCommand.getConstrainedHeight"
        # compute val2 as a function of val1
        if mode == 'square':
            return width
        elif mode == 'keep aspect ratio':
            cam = self.vf.GUI.VIEWER.currentCamera
            return round( width * cam.height/float(cam.width) )
        else:
            return height


    def fixHeight_cb (self, event=None):
        #print "RenderLargeImageCommand.fixHeight_cb"
        # called when width thumbwheel changes
        f = self.cmdForms['tileRendering']
        mode = f.descr.entryByName['constraint']['widget'].get()
        width = f.descr.entryByName['width']['widget'].value
        height = f.descr.entryByName['height']['widget'].value
        cam = self.vf.GUI.VIEWER.currentCamera
        if mode != 'None':
            nheight = self.getConstrainedHeight(mode, width, height)
            f.descr.entryByName['height']['widget'].set(nheight, update=0)
            if (mode == 'square') and (cam.width != cam.height):
                if cam.width < cam.height:
                    tileSize = cam.width
                else:
                    tileSize = cam.height
                self.vf.setCameraSize(tileSize, tileSize, topCommand=0)
        else:
            camWidth = int( cam.height * width/float(height) )
            self.vf.setCameraSize(width=camWidth, height=cam.height, 
                                  topCommand=0)


    def fixWidth_cb (self, event=None):
        #print "RenderLargeImageCommand.fixWidth_cb"
        # called when height thumbwheel changes
        f = self.cmdForms['tileRendering']
        mode = f.descr.entryByName['constraint']['widget'].get()
        width = f.descr.entryByName['width']['widget'].value
        height = f.descr.entryByName['height']['widget'].value
        cam = self.vf.GUI.VIEWER.currentCamera
        if mode != 'None':
            nwidth = self.getConstrainedWidth(mode, height, width)
            f.descr.entryByName['width']['widget'].set(nwidth, update=0)
            if (mode == 'square') and (cam.width != cam.height):
                if cam.width < cam.height:
                    tileSize = cam.width
                else:
                    tileSize = cam.height
                self.vf.setCameraSize(tileSize, tileSize, topCommand=0)
        else:
            camHeight = int( cam.width * height/float(width) )
            self.vf.setCameraSize(width=cam.width, height=camHeight,
                                  topCommand=0)

        
    def buildFormDescr(self, formName):
        #print "RenderLargeImageCommand.buildFormDescr"
        if formName == 'tileRendering':
            idf = InputFormDescr(title="Tile Rendering parameters")
            cam = self.vf.GUI.VIEWER.cameras[0]
            idf.append({'name':'width',
                        'widgetType':ThumbWheel,
                        'wcfg':{ 'labCfg':{'text':'Requested Width: ', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0, 
                                 'callback':self.fixHeight_cb,
                                 'type':int, 'precision':1,
                                 'value':cam.width,'continuous':1,
                                 'oneTurn':500, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})
                        
            idf.append({'name':'height',
                        'widgetType':ThumbWheel,
                        'wcfg':{ 'labCfg':{'text':'Requested Height: ', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0, 
                                 'callback':self.fixWidth_cb,
                                 'type':int, 'precision':1,
                                 'value':cam.height,'continuous':1,
                                 'oneTurn':500, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})

            idf.append({'name':'constrLab',
                        'widgetType':Tkinter.Label,
                        'wcfg':{ 'text':'Constraints: '},
                        'gridcfg':{'sticky':'wens', 'row':0, 'column':1}})
            
            modes = ['None', 'square', 'keep aspect ratio']
            idf.append({'name':'constraint',
                        'widgetType':Pmw.ComboBox,
                        'wcfg':{ 'scrolledlist_items':modes, 'dropdown':1,
                                 'selectioncommand':self.fixHeight_cb,
                                 'entryfield_entry_width':8},
                        'defaultValue':'keep aspect ratio',
                        'gridcfg':{'sticky':'wens', 'row':1, 'column':1},
                        })

            idf.append({'name':'border',
                        'widgetType':ThumbWheel,
                        'wcfg':{ 'labCfg':{'text':'Border: ', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0, 'max':20, 'type':int,
                                 'precision':1,
                                 'value':0,'continuous':1,
                                 'oneTurn':2, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})

            idf.append({'name':'backBuffer',
                        'widgetType':Tkinter.Checkbutton,
                        'defaultValue':1,
                        'wcfg':{'text':'Back Buffer',
                                'variable':Tkinter.IntVar()},
                        'gridcfg':{'sticky':'w', 'columnspan':2}
                        })

            idf.append({'name':'checkeredBackground',
                        'widgetType':Tkinter.Checkbutton,
                        'defaultValue':0,
                        'wcfg':{'text':'Checkered Background',
                                'variable':Tkinter.IntVar()},
                        'gridcfg':{'sticky':'w', 'columnspan':2}
                        })

            # File to create
            idf.append({'name':'outputFile',
                        'widgetType':Pmw.EntryField,
                        'tooltip':'Enter the outputFile',
                        'wcfg':{'label_text':'Output File:',
                                'labelpos':'w',
                                'value':'test.tif'},
                        'gridcfg':{'sticky':'w'},
                        })

            idf.append({'widgetType':SaveButton,
                        'name':'filebrowse',
                        'wcfg':{'buttonType':Tkinter.Button,
                                'title':'Save In File ...',
                                'types':[('TIFF', '*.tif'),
                                         ('JPEG','*.jpg'),
                                         ('All','*.*')],
                                'callback':self.setEntry_cb,
                                'widgetwcfg':{'text':'BROWSE'}},
                        'gridcfg':{'row':-1, 'sticky':'we'}})

            return idf

    ### ##################################################################
    ### CALLBACK FUNCTIONS
    ### ##################################################################
        
    def setEntry_cb(self, filename):
        #print "RenderLargeImageCommand.setEntry_cb"
        ebn = self.cmdForms['tileRendering'].descr.entryByName
        entry = ebn['outputFile']['widget']
        entry.setentry(filename)


    def cancel_cb(self):
        #print "RenderLargeImageCommand.cancel_cb"
        pass
        #cam = self.vf.GUI.VIEWER.cameras[0]
        #self.camHeight = cam.height
        #self.camWidth = cam.width
        #self.camrootX = cam.rootx
        #self.camrootY = cam.rooty
        ##self.vf.showHideGUI('all', 1, topCommand=0)
        #self.vf.setCameraSize(self.camWidth, self.camHeight,
        #                      xoffset=self.camrootX, yoffset=self.camrootY, 
        #                      topCommand=0)
        


RenderLargeImageGUI = CommandGUI()
RenderLargeImageGUI.addMenuCommand('menuRoot', '3D Graphics', 'Render Large Image')


class SpinCommand(Command):
    """
Package : ViewerFramework
Module  : dejaVuCommands
Class   : SpinCommand
Command : spin

Description:
Open the spin gui

Synopsis:

Keywords :
"""

    def logString(self, *args, **kw):
        """return None as log string as we don't want to log this
"""
        pass


    def doit(self):
        self.vf.GUI.VIEWER.currentCamera.trackball.showSpinGui()


spinGUI = CommandGUI()
spinGUI.addMenuCommand('menuRoot', '3D Graphics', 'Spin - Bounce - Oscillate')



class SetCameraSizeCommand(Command):
    """
    Package : ViewerFramework
    Module  : dejaVuCommands
    Class   : SetCameraSizeCommand
    Command : setCameraSize

    Description    
    Command allowing the user to resize the camera to the given width, height, xoffset and yoffset

    Synopsis:
    width, height <- setCameraSize(width, height, xoffset=None, yoffset=None)

    width    : int to specify camera width in pixels
    height   : int to specify camera height in pixels
    xoffset  : int to specify the x position of the left corner of the camera
               relative to the left corner of the camera
    yoffset  : int to specify the y position of the left corner of the camera
               relative to the left corner of the camera
    """

    def doit(self, width, height, xoffset=0, yoffset=0):
        """
width    : int to specify camera width in pixels
height   : int to specify camera height in pixels
xoffset  : int to specify the x position of the left corner of the camera
           relative to the left corner of the camera
yoffset  : int to specify the y position of the left corner of the camera
           relative to the left corner of the camera
"""
        vfgui =self.vf.GUI 
        vi = vfgui.VIEWER
        if not vfgui.isCameraFloating():
            # Camera is docked

            # I was unable to find out how to resize the master such that
            # the camera ends up with the right size, because the message_box
            # expands along with the camera.  So I disable expansion of the
            # message box when the camera size is set for a docked camera

            # disable message box expansion
            mb = vfgui.MESSAGE_BOX
            try:
                opts = mb.pack_info()
                mb.pack_forget()
                opts['expand'] = 0
                apply( mb.pack, (), opts)
                MESSAGE_BOX_reqheight = vfgui.MESSAGE_BOX.winfo_reqheight()
            except: #mb.pack_info() hrows exception
                MESSAGE_BOX_reqheight = 0
            # first set the width as this might add scroll bars under menus and
            # hence add the thir height
            c = vi.cameras[0]
            off = 2*c.frameBorderWidth
            vfgui.setGeom(xoffset, yoffset, width+off, c.height)
            #vi.update()

            # now compute height needed
            #print 'MENU', vfgui.mBarFrame.winfo_reqheight()
            #print 'Info', vfgui.infoBar.winfo_reqheight()
            #print 'MESSAGE', vfgui.MESSAGE_BOX.winfo_reqheight()
            #print 'camera', height+off
            h = vfgui.mBarFrame.winfo_reqheight() + \
                height + off +\
                vfgui.infoBar.winfo_reqheight() + \
                MESSAGE_BOX_reqheight
            #print 'TOTAL', h, width+off, h+off

            # resize the top widget.  At this point only thw camera should
            # expand, and reach the desired size
            vfgui.setGeom(xoffset, yoffset, width+off, h)
            vi.update()

            # now restore the message_box's packing options so that it scales
            # again when the user resizes the app
            
        else:
            # Camera is floating
            toplevel = self.vf.GUI.vwrCanvasFloating
            #geom = '%dx%d+%d+%d' % (width, height, xoffset, yoffset)
            #toplevel.geometry(geom)

            # Need to reposition the camera and the menu
            vi.currentCamera.Set(rootx=xoffset, rooty=yoffset, width=width, height=height)
            #menux, menuy, menuw, menuh = self.vf.GUI.getGeom()
            # give Tk a chance to handle the event
            self.vf.GUI.VIEWER.update()
            
            #nwidth = toplevel.cget('width')
            #nheight = toplevel.cget('height')

            # FIXME not sure why she sets the geometry of the menu window here
            #self.vf.GUI.setGeom(xoffset, yoffset+height+30, width,  menuh)

        #return nwidth, nheight
        if self.vf.GUI.VIEWER.suspendRedraw is False:
            self.vf.GUI.VIEWER.OneRedraw()


    def buildFormDescr(self, formName):
        if formName == 'setCameraSize':
            idf = InputFormDescr(title="Set Camera Size:")
            cam = self.vf.GUI.VIEWER.cameras[0]
            idf.append({'name':'width',
                        'widgetType':ThumbWheel,
                        'wcfg':{ 'labCfg':{'text':'Camera Width: ', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0, 'max':self.vf.GUI.screenWidth,
                                 'type':int, 'precision':1,
                                 'value':cam.width,'continuous':1,
                                 'oneTurn':200, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})
                        
            idf.append({'name':'height',
                        'widgetType':ThumbWheel,
                        'wcfg':{ 'labCfg':{'text':'Camera Height: ', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0, 'max':self.vf.GUI.screenHeight,
                                 'type':int, 'precision':1,
                                 'value':cam.height,'continuous':1,
                                 'oneTurn':200, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})
            if self.vf.GUI.floatCamVariable.get():
                defRootx = self.vf.GUI.VIEWER.currentCamera.rootx
                defRooty = self.vf.GUI.VIEWER.currentCamera.rooty
            else:
                defRootx = self.vf.GUI.ROOT.winfo_rootx()
                defRooty = self.vf.GUI.ROOT.winfo_rooty()

            idf.append({'name':'xoffset',
                        'widgetType':ThumbWheel,
                        'wcfg':{ 'labCfg':{'text':'Camera X Offset: ', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0, 
                                 'type':int, 'precision':1,
                                 'value':defRootx,'continuous':1,
                                 'oneTurn':50, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})

            idf.append({'name':'yoffset',
                        'widgetType':ThumbWheel,
                        'wcfg':{ 'labCfg':{'text':'Camera Y Offset: ', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0, 'max':self.vf.GUI.screenHeight,
                                 'type':int, 'precision':1,
                                 'value':defRooty,'continuous':1,
                                 'oneTurn':50, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})
            
            return idf

    def guiCallback(self):
        val = self.showForm('setCameraSize')
        if val:
            width = val['width']
            del val['width']
            height = val['height']
            del val['height']
            apply(self.doitWrapper, (width, height), val)
        
    

    def __call__(self, width, height, xoffset=0, yoffset=0, **kw):
        """
        width, height <-self.setCameraSize(width, height, xoffset=None, yoffset=None, **kw)
        width    : int to specify camera width in pixels
        height   : int to specify camera height in pixels
        xoffset  : int to specify the x position of the left corner of the camera
                   relative to the left corner of the camera
        yoffset  : int to specify the y position of the left corner of the camera
                   relative to the left corner of the camera
       
        """
        kw['xoffset']=xoffset
        kw['yoffset']=yoffset
        kw['redraw']=True
        return apply(self.doitWrapper, (width, height), kw)



SetCamSizeGUI = CommandGUI()
SetCamSizeGUI.addMenuCommand('menuRoot', '3D Graphics', 'Set Camera Size')



class SaveImage(Command):
    """This command allows to save the content of the current frambuffer as
an image into a file. The file format will be defined by the extension used
in the filename. Currently de follwoing foramt are supported:
BMP, EPS, GIF, IM, JPEG, PNG, PPM, TIFF or TIF, PDF.
    \nPackage : ViewerFramework
    \nModule  : dejaVuCommands
    \nClass   : SaveImage
    \nCommand : saveImage
    \nSynopsis:\n
        None <- saveImage(self,filename, **kw)
    \nfilename --- name of the file
    \nDependencies: require the Python Imaging Library
    \nregression test: testdir/testSaveImage.py
"""

#    def logString(self, *args, **kw):
#        """return None as log string as we don't want to log this
#"""
#        pass


    def checkDependencies(self, vf):
        import Image

  
    def doit(self, filename, transparentbg):
        # lift
        self.vf.GUI.ROOT.lift()
        vi = self.vf.GUI.VIEWER
        vi.OneRedraw()
        cam = self.vf.GUI.VIEWER.currentCamera
        if transparentbg:    
            cam.SaveImage(filename, transparentBackground=True)
        else:
            cam.SaveImage(filename)
   

    def buildFormDescr(self, formName):
        
        idf = InputFormDescr(title="SaveImage")
        idf.append({'name':"TB",
                        'widgetType':Tkinter.Checkbutton,
                        'wcfg':{'text':'Transparent Background', 'variable':Tkinter.IntVar()},
                        'command':self.switch_type_cb,
                        'gridcfg':{'sticky':'nw'}})
        
        idf.append({'name':'File',
                        'widgetType':Pmw.EntryField,
                        'tooltip':'Enter the outputFile',
                        'wcfg':{'label_text':'Output File:',
                                'labelpos':'wnse',
                                },
                        'gridcfg':{'sticky':'wnse'},
                        })
    
        idf.append({'widgetType':SaveButton,
                        'name':'filesave',
                        'wcfg':{'buttonType':Tkinter.Button,
                                'title':'Save as File',
                                'types':[('PNG files', '*.png'),
                                         ('TIFF files', '*.tif'),
                                         ('JPEG files', '*.jpg'),
                                         ('GIF files', '*.gif'),
                                         ('PPM files', '*.ppm'),
                                         ('EPS files', '*.eps'),
                                         ('IM files', '*.im'),
                                         ('PDF files', '*.pdf'),
                                         ('all files', '*.*')],
                                'callback':self.setEntry_cb,
                                'widgetwcfg':{'text':'Choose'}},
                        'gridcfg':{'sticky':'we','row':-1}})
        
        
        idf.append({'name':'cite',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Cite',
                            'command':self.cite_cb,
                           },
                    'gridcfg':{'sticky':'wnse','column':1}})
        idf.append({'name':'Citelab',
                        'widgetType':Tkinter.Label,
                        'wcfg':{ 'text':'If you are going to publish this image'},
                        'gridcfg':{'sticky':'wnse','row':-1,'column':0}})
        idf.append({'name':'ok',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'OK',
                            'command':self.ok_cb,
                           },
                    'gridcfg':{'sticky':'wnse'}})            
        
        idf.append({'name':'dismiss',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'DISMISS',
                            'command':self.dismiss_cb,
                           },
                    'gridcfg':{'sticky':'wnse','row':-1,'column':1}})
        
        return idf     
        
    def cite_cb(self):
        urlcite = "http://www.scripps.edu/~sanner/software/documentation/citationsinfo.html"     
        import webbrowser
        webbrowser.open_new(urlcite)

    def switch_type_cb(self):
        # callback function for transparent background checkbutton
        # when checked configure file browser to show *.png file only
        ebn = self.cmdForms['SaveImage'].descr.entryByName
        if  ebn['TB']['wcfg']['variable'].get()==0:
            saveb = ebn['filesave']['widget']
            wcfg = ebn['filesave']['wcfg']
            from mglutil.util.callback import CallBackFunction
            ftypes = [('PNG files', '*.png'), ('TIFF files', '*.tif'), ('JPEG files', '*.jpg'), ('GIF files', '*.gif'),
                       ('PPM files', '*.ppm'), ('EPS files', '*.eps'),
                      ('IM files', '*.im'), ('PDF files', '*.pdf'), ('all files', '*.*')]
            saveb.configure(title=wcfg['title'], idir=None, ifile=None, types=ftypes, callback=wcfg['callback'])
        else:
            saveb = self.cmdForms['SaveImage'].descr.entryByName['filesave']['widget']
            wcfg = self.cmdForms['SaveImage'].descr.entryByName['filesave']['wcfg']
            ftypes = [('PNG files', '*.png')]
            saveb.configure(idir=None, ifile=None, types=ftypes, title=wcfg['title'], callback=wcfg['callback'])

    
    def setEntry_cb(self, filename):
        ebn = self.cmdForms['SaveImage'].descr.entryByName
        entry = ebn['File']['widget']
        entry.setentry(filename)
        
        
    def ok_cb(self):
        ebn = self.cmdForms['SaveImage'].descr.entryByName
        file = ebn['File']['widget'].get()                
        if file == None or file =='': return
        transparentbg = ebn['TB']['wcfg']['variable'].get()
        if not self.cmdForms.has_key('SaveImage'): return
        f = self.cmdForms['SaveImage']
        if f.root.winfo_ismapped():
            f.root.withdraw()
            f.releaseFocus()

        apply(self.doitWrapper, (file,transparentbg), {})
    
    def dismiss_cb(self):
        if not self.cmdForms.has_key('SaveImage'): return
        f = self.cmdForms['SaveImage']
        if f.root.winfo_ismapped():
            f.root.withdraw()
            f.releaseFocus()


    def guiCallback(self):
        f = self.vf.GUI.VIEWER.currentCamera.frame
        if f.winfo_height() + f.winfo_rooty() < f.winfo_screenheight() - 100:
            posy =  f.winfo_height() + f.winfo_rooty()
            posx = int(f.winfo_width()/2) + f.winfo_rootx() -100
        else:
            posx = None
            posy = None
        val = self.showForm('SaveImage', force=1, blocking=0, modal=0, 
                            master=self.vf.GUI.VIEWER.currentCamera.frame, posx=posx, posy=posy)
                    
 
    def __call__(self, filename, transparentbg=False, **kw):
        """ None <- saveImage(self,filename, **kw)
    \nfilename : name of the file
    transparentbg: true to get a transparent background, works only with .png files"""
        if filename==None: return
        kw['transparentbg'] = transparentbg
        apply(self.doitWrapper, (filename,), kw)



SaveImageGUI = CommandGUI()
SaveImageGUI.addMenuCommand('menuRoot', 'File', 'Save Image As',
                            cascadeName='Save')


class ColorGeomsByName(Command):
    """
    Command to choose color for geometries selected by name 
    """

    def onAddCmdToViewer(self):
        if self.vf.hasGui:
            self.patVar = Tkinter.StringVar()
            self.patVar.set("")

    def hidePalette_cb(self, event=None):
        self.palette.hide()

    def color_cb(self, colors, event=None):
        self.doitWrapper(pat = self.patVar.get(), material = colors)


    def doit(self, pat, material):
        print 'in doit with pat=', pat 
        print 'and material=', material 
        geomsToColor = self.vf.GUI.VIEWER.findGeomsByName(pat)
        print "geomsToColor=", 
        for g in geomsToColor:
            print g.name
        if len(geomsToColor)==0:
            return
        for geom in geomsToColor:
            geom.Set(inheritMaterial=False, materials = [material,])
            if geom.children!=[]:
                for childGeom in geom.children:
                    childGeom.Set(inheritMaterial=False, materials = [material,])
        self.vf.GUI.VIEWER.Redraw()


    def dismiss_cb(self, event=None):
        if hasattr(self, 'form'):
            self.form.withdraw()
        

    def buildForm(self):
        if hasattr(self, 'ifd'):
            return
        from mglutil.gui.BasicWidgets.Tk.colorWidgets import ColorChooser
        self.palette = ColorChooser(commands=self.color_cb,
                            exitFunction = self.hidePalette_cb)
        top = self.palette.ccFrame
        menuBar = self.palette.ccFrame
        ifd = self.ifd = InputFormDescr(title="Color Geometries by Name")
        ifd.append({'name':'patternLab',
                    'widgetType':Tkinter.Label,
                    'parent':top,
                    'text':"pattern:",
                    'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'patternEnt',
                'widgetType':Tkinter.Entry,
                'parent':top,
                'wcfg':{ 'textvariable': self.patVar, },
                'gridcfg':{'sticky':'wens', 'row':-1, 'column':1}})
        self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)
        self.label = self.ifd.entryByName['patternLab']['widget']
        self.entry = self.ifd.entryByName['patternEnt']['widget']
        top = self.label.master.master.master
        self.palette.pack(fill='both', expand=True)
        self.form.root.portocol("WM_DELETE_WINDOW", self.dismiss_cb)


    def guiCallback(self):
        if hasattr(self, 'ifd'):
            self.form.deiconify()
        else:
            self.buildForm()


    def __call__(self, pat, material, **kw):
        """
        None <- colorGeomsByName(filename)
        pat: string to match to geometry names
        material: new color 
        """
        apply( self.doitWrapper, (pat, material,), kw)



ColorGeomsByNameGUI = CommandGUI()
ColorGeomsByNameGUI.addMenuCommand('menuRoot', 'Color', 'ColorGeomsByName')



class setAntialiasingCommand(Command):
    """
    Package : ViewerFramework
    \nModule  : dejaVuCommands
    \nClass   : setbackgroundcolorCommand
    \nCommand : SetBackGroundColor

    \nDescription    
    \nCommand allowing the user to set color of the camera 

    \nSynopsis:
    \ncolor : Required color of background
    """
      
    def doit(self,value):
        vfgui = self.vf.GUI
        vi = vfgui.VIEWER
        vi.GUI.nbJitter.set(value)
        camera = vi.currentCamera 
        camera.Set(antialiased = value)
        vi.Redraw()
          
    def buildFormDescr(self, formName):
        if formName == 'setAntialiasing':
            idf = InputFormDescr(title="SetAntialiasing")
            self.vallist = [0,2,3,4,8,15,24,66]
            idf.append({'name':'value',
                'widgetType':kbScrolledListBox,
                'wcfg':{'items':self.vallist,
                            #'defaultValue': 0,
                            'listbox_exportselection':0,
                            'labelpos':'nw',
                            'label_text':'Antialiasing Values',
                            'selectioncommand':self.setJitter_cb,
                            
                            },
                    'gridcfg':{'sticky':'wesn','columnspan':1}})
                
            
            
            
            idf.append({'widgetType':Tkinter.Button,
                        'name':'dismiss',
                        'wcfg':{'text':'DISMISS', 'command':self.dismiss_cb},
                        'gridcfg':{'sticky':'we', 'columnspan':3}})
            
            return idf
    
    def dismiss_cb(self):
        if self.cmdForms.has_key('setAntialiasing'):
            self.cmdForms['setAntialiasing'].withdraw()
    
    def guiCallback(self):
        form = self.showForm('setAntialiasing', modal=0, blocking=0)
        
    def setJitter_cb(self):
        
        self.curselval = self.cmdForms['setAntialiasing'].descr.entryByName['value']['widget'].getcurselection()
        if self.curselval == ():
            self.curselv = 0
        else:
            self.curselv = self.curselval[0]
        
        apply( self.doitWrapper, (self.curselv,),{})
        
    def __call__(self,value, **kw):
        """None <-----setAntialiasing(value)
        \ncolor : background color
        """
        if isinstance(value, types.IntType) is False:
            return
        
        apply( self.doitWrapper, (value,), kw)



setAntialiasingGUI = CommandGUI()
setAntialiasingGUI.addMenuCommand('menuRoot', '3D Graphics','SetAntialiasing')    



class setbackgroundcolorCommand(Command):
    """
    Package : ViewerFramework
    \nModule  : dejaVuCommands
    \nClass   : setbackgroundcolorCommand
    \nCommand : SetBackGroundColor

    \nDescription    
    \nCommand allowing the user to set color of the camera 

    \nSynopsis:
    \ncolor : Required color of background
    """
   
    def hidePalette_cb(self, event=None):
        self.palette.hide()

    def color_cb(self, colors, event=None):
        self.doitWrapper(colors)
        
    def onAddCmdToViewer(self):
        if self.vf.hasGui:
            self.patVar = Tkinter.StringVar()
            self.patVar.set("")
            path = os.path.join(getResourceFolder(),'backgroundColor')
            if os.path.exists(path):
                hcol = open(path).read()
            else:
                return
            rgb = int(hcol[1:3], 16), int(hcol[3:5], 16), int(hcol[5:7], 16)
            col = [x/255. for x in rgb]
            self.vf.GUI.VIEWER.CurrentCameraBackgroundColor(col)
            
    def doit(self,color, **kw):
        vfgui = self.vf.GUI
        vi = vfgui.VIEWER
        vi.CurrentCameraBackgroundColor(color)
        #vi.GUI.CameraColorButton_cb()

        #cam = vi.currentCamera 
        #cc = vi.GUI.colorChooser
        #cc.Set( cam.backgroundColor[:3], 'RGB' )
        
    
    
    def buildFormDescr(self, formName):
        if formName == 'setbackgroundcolor':
            idf = InputFormDescr(title="SetBackGroundColor")
            cam = self.vf.GUI.VIEWER.cameras[0]      
            idf.append({'widgetType':ColorChooser,
                        'name':'colors',
                        'wcfg':{'title':'SetBackGroundColor',
                                'commands':self.color_cb,
                                'immediate':0, 'exitFunction':self.dismiss_cb},
                        'gridcfg':{'sticky':'wens', 'columnspan':3}
                        })
            idf.append({'widgetType':Tkinter.Button,
                        'name':'dismiss',
                        'wcfg':{'text':'DISMISS', 'command':self.dismiss_cb},
                        'gridcfg':{'sticky':'we', 'columnspan':3}})
            
            return idf
    

    def dismiss_cb(self, **kw):
        if self.cmdForms.has_key('setbackgroundcolor'):
            self.cmdForms['setbackgroundcolor'].withdraw()


    def guiCallback(self):
        form = self.showForm('setbackgroundcolor', modal=0, blocking=0)
    

    def __call__(self, color, **kw):
        """
None <-----setbackgroundcolorCommand(color)
\ncolor : background color
"""
        if type(color) == types.StringType:
            return "Error: color type can't be string"
        elif hasattr(color, '__len__') is False:
            return "Error: color should have length"
        elif len(color) != 3:
            return "Error: color length should be 3"
        
        apply( self.doitWrapper, (color,), kw)


setbackgroundcolorGUI = CommandGUI()
setbackgroundcolorGUI.addMenuCommand('menuRoot', '3D Graphics','SetBackGroundColor')



class setNPROutlinesCommand(ToggleNpr,Command):
    
    """
    Package : ViewerFramework
    \nModule  : dejaVuCommands
    \nClass   : setNPROutlinesCommand
    \nCommand : SetNPROutlines

    \nDescription    
    \nCommand allowing the user to set NPR outlines 

    \nSynopsis:
    \ncolor : Required color of background
    """
        
    def doit(self,control_points,sensitivity):
        self.vf.toggleNpr(npr=1)
        vi.GUI.curvetool.setControlPoints(control_points)
        vi.GUI.curvetool.d1scalewheel.set(sensitivity)
        
        #vi.GUI.CameraColorButton_cb()

        #cam = vi.currentCamera 
        #cc = vi.GUI.colorChooser
        #cc.Set( cam.backgroundColor[:3], 'RGB' )
        
    def onAddCmdToViewer(self):
        if self.vf.hasGui:
            self.sensitivityVar = Tkinter.StringVar()
            self.sensitivityVar.set("")
            self.cpVar = Tkinter.StringVar()
            self.cpVar.set("")

    def buildFormDescr(self, formName):
       if formName=="setNprparams":                
        ifd = InputFormDescr(title="Set NPR Params")
        ifd.append({'name':'cpLab',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':"Control Points"},
                    
                    'gridcfg':{"row":0,'column':0,'sticky':'w'}})
        ifd.append({'name':'cpEnt',
                'widgetType':Tkinter.Entry,
                'tooltip':'controlpoints must be  a list of tuples with x  value ranging from [50,305] and y from [20,275].',
                'wcfg':{'textvariable':self.cpVar},
                'gridcfg':{'sticky':'wens', 'row':0, 'column':1}})
        ifd.append({'name':'sensitivityLab',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':"Sensitivity"},
                    
                    'gridcfg':{"row":1,"column":0,'sticky':'w'}})
        ifd.append({'name':'sensitivityEnt',
                'widgetType':Tkinter.Entry,
                'tooltip':'sensitivity should be in range of 0.0 to 1.0',
                'wcfg':{'textvariable':self.sensitivityVar},
                'gridcfg':{'sticky':'wens', 'row':1, 'column':1}})
       
        ifd.append({'widgetType':Tkinter.Button,
                        'name':'OK',
                        'wcfg':{'text':'OK', 'command':self.ok_cb},
                        'gridcfg':{'sticky':'we', 'row':2,'column':0}})
        ifd.append({'widgetType':Tkinter.Button,
                        'name':'dismiss',
                        'wcfg':{'text':'DISMISS', 'command':self.dismiss_cb},
                        'gridcfg':{'sticky':'we', 'row':2,'column':1}})
        

        return ifd

        
    
    def dismiss_cb(self):
        if self.cmdForms.has_key('setNprparams'):
            self.cmdForms['setNprparams'].withdraw()
    def guiCallback(self):
        form = self.showForm('setNprparams', modal=0, blocking=0)
        
        
    
    def ok_cb(self):
        vfgui = self.vf.GUI
        vi = vfgui.VIEWER
        self.vf.toggleNpr(npr=1)
        if self.cpVar.get() != '':
            vi.GUI.curvetool.setControlPoints(eval(self.cpVar.get()))
        if self.sensitivityVar.get() != '':
            vi.GUI.curvetool.d1scalewheel.set(eval(self.sensitivityVar.get()))
        self.dismiss_cb()
              
        

    def __call__(self,control_points,sensitivity):
        """None <-----setNPROutlines(points,sensitivity)
        points:list of points
        snesitivity:floatvalue(ranging from 0.0 to 1.0)
        \ncolor : background color
        """
        if type(control_points) != types.ListType:
            print "Illegal type for points"
            return
        if type(sensitivity)!=types.FloatType:
            print "Illegal type for sensitivity"
            return
                    
        apply( self.doitWrapper, (control_points,sensitivity),{})


   
setNPROutlinesGUI = CommandGUI()
setNPROutlinesGUI.addMenuCommand('menuRoot', '3D Graphics','SetCartoonOutlines')    


commandList = [
    {'name':'setNPROutlines', 'cmd':setNPROutlinesCommand(),
     'gui':setNPROutlinesGUI},
    {'name':'setAntialiasing', 'cmd':setAntialiasingCommand(),
     'gui':setAntialiasingGUI},
    {'name':'setbackgroundcolor', 'cmd':setbackgroundcolorCommand(),
     'gui':setbackgroundcolorGUI},
    {'name':'setCameraSize', 'cmd':SetCameraSizeCommand(),
     'gui':SetCamSizeGUI},
    {'name':'renderLargeImage', 'cmd':RenderLargeImageCommand(),
     'gui':RenderLargeImageGUI},
    {'name':'spin', 'cmd':SpinCommand(), 'gui':spinGUI},
    {'name':'transformObject', 'cmd':TransformObject(),
     'gui':None},
    {'name':'transformCamera', 'cmd':TransformCamera(),
     'gui':None},
    {'name':'setObject', 'cmd': SetObject(),
     'gui':None},
    {'name':'setCamera', 'cmd':SetCamera(),
     'gui': None},
    {'name':'setLight', 'cmd':SetLight(), 'gui':None},
    {'name':'setClip', 'cmd':SetClip(),'gui':None},
    {'name':'addClipPlane', 'cmd':AddClipPlane(),'gui':None},
    {'name':'centerGeom','cmd':CenterGeom(),'gui':None},
    {'name':'viewPoints', 'cmd': ViewPoints(),'gui':None},
    {'name': 'centerScene', 'cmd':CenterScene(), 'gui':None},
    {'name': 'centerSceneOnVertices', 'cmd':CenterSceneOnVertices(),
     'gui':None},
    {'name':'centerSceneOnPickedPixel','cmd':CenterSceneOnPickedPixel(),
     'gui':None},
    {'name': 'alignGeomsnogui', 'cmd':AlignGeoms(),
     'gui':None},
    {'name': 'alignGeoms', 'cmd':AlignGeomsPCOM(),
     'gui':None},
    {'name': 'rotateScene', 'cmd':RotateScene(), 'gui':None},
    {'name':'printGeometryName', 'cmd':PrintGeometryName(), 'gui':None},
    {'name':'startContinuousPicking', 'cmd':StartContinuousPicking(),
     'gui':None},
    {'name':'stopContinuousPicking', 'cmd':StopContinuousPicking(),
     'gui':None},
#    {'name':'toggleStereo', 'cmd':ToggleStereo(), 'gui':ToggleStereoGUI},
#    {'name':'toggleNpr', 'cmd':ToggleNpr(), 'gui':ToggleNprGUI},
    {'name':'toggleStereo', 'cmd':ToggleStereo(), 'gui':ToggleStereoGUI},
    {'name':'toggleNpr', 'cmd':ToggleNpr(), 'gui':ToggleNprMenuGUI},

    {'name':'ResetView', 'cmd':ResetView(), 'gui':ResetViewGUI},
     
    {'name':'loadColorMap', 'cmd':LoadColorMap(), 'gui':LoadColorMapGUI},
    {'name':'saveColorMap', 'cmd':SaveColorMap(), 'gui':SaveColorMapGUI},
    {'name':'createColorMap', 'cmd':CreateColorMap(), 'gui':CreateColorMapGUI},
    {'name':'showCMGUI', 'cmd':ColorMapEditor(),
     'gui':ColorMapEditorGUI},
    {'name':'editColorMap', 'cmd':EditColorMap(), 'gui':None},
    {'name':'saveImage', 'cmd':SaveImage(), 'gui':SaveImageGUI },
    #{'name':'colorGeomsByName', 'cmd':ColorGeomsByName(), 'gui':ColorGeomsByNameGUI},
    ]



def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
