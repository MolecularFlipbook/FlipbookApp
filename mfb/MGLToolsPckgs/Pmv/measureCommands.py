## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Michel F. SANNER, Ruth HUEY
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/measureCommands.py,v 1.52 2010/11/15 23:32:03 sanner Exp $
#
# $Id: measureCommands.py,v 1.52 2010/11/15 23:32:03 sanner Exp $
#
import numpy.oldnumeric as Numeric, math, types
from Pmv.mvCommand import MVCommand, MVAtomICOM
from DejaVu.Geom import Geom
from DejaVu.Spheres import Spheres
from DejaVu.IndexedPolylines import IndexedPolylines
#from DejaVu.Labels import Labels
from DejaVu.glfLabels import GlfLabels
from ViewerFramework.VFCommand import CommandGUI
from MolKit.molecule import Atom, AtomSet

"""
    MeasureCommands contains commands to measure distances, angles and 
    torsions between atoms:
      measureDistance-> returns distance between 2 atoms in Angstrom
      measureAngle->    returns angle defined by 3 atoms in Degrees
      measureTorsion->  returns torsion angle defined by 4 atoms in Degrees.

    This module also contains GuiCommands which provide the user-interfaces
    to the measure commands listed above.  Atoms picked for measurements 
    are marked with spheres: yellow for distance, orange for angle and 
    cyan for torsion.  In addition, these Gui Commands mark the property 
    measured as follows (with the same color scheme):
      measureDistanceGC->   stippled lines labelled with distance
      measureAngleGC ->     2D fan, stipple line and angle label
      measureTorsionGC->    polygon-fill on torsion and angle label

"""


def check_measure_geoms(VFGUI):
    measure_geoms_list = VFGUI.VIEWER.findGeomsByName('measure_geoms')
    if measure_geoms_list==[]:
        measure_geoms = Geom("measure_geoms", shape=(0,0), protected=True)
        VFGUI.VIEWER.AddObject(measure_geoms, parent=VFGUI.miscGeom)
        measure_geoms_list = [measure_geoms]
    return measure_geoms_list[0]


class MeasureAtomCommand(MVCommand):
    """Base class for commands which measure between atoms.Implements applyTransformation, getTransformedCoords and vvmult.
   \nPackage : Pmv
   \nModule  : measureCommands
   \nClass   : MeasureAtomCommand
   """

    def getTransformedCoords(self, atom):
        # when there is no viewer, the geomContainer is None
        if not atom.top.geomContainer:
            return atom.coords
        g = atom.top.geomContainer.geoms['master']
        c = self.vf.transformedCoordinatesWithInstances(AtomSet([atom]))
        return  Numeric.array(c[0], 'f')


    def vvmult(self, a, b):
        """
        Compute a vector product for 3D vectors
        """
        import numpy.oldnumeric as Numeric
        res = Numeric.zeros(3, 'f')
        res[0] = a[1]*b[2] - a[2]*b[1]
        res[1] = a[2]*b[0] - a[0]*b[2]
        res[2] = a[0]*b[1] - a[1]*b[0]
        return res


class MeasureDistance(MeasureAtomCommand):
    """Computes the distance between atom1, atom2, atom3.All coordinates are Cartesian; result is in Angstrom.
   \nPackage : Pmv
   \nModule  : measureCommands
   \nClass   : MeasureDistance
   \nCommand : measureDistance
   \nSynopsis:\n
        float <--- measureDistance(atom1, atom2, **kw)
   \nRequired Argument:\n       
        atom1 --- first atom
        \natom2 --- second atom
    """


    def doit(self, atom1, atom2):
        c1 = self.getTransformedCoords(atom1)
        c2 = self.getTransformedCoords(atom2)
        d = c2 - c1
        return math.sqrt(Numeric.sum(d*d))


    def __call__(self, atom1, atom2, **kw):
        """float <--- measureDistance(atom1, atom2, **kw)
        \natom1 --- first atom
        \natom2 --- second atom
        """
        ats = self.vf.expandNodes(atom1)
        if not len(ats): return 'ERROR'
        atom1 = ats[0]
        ats = self.vf.expandNodes(atom2)
        if not len(ats): return 'ERROR'
        atom2 = ats[0]
        return apply(self.doitWrapper, (atom1, atom2), kw)


    
class MeasureAngle(MeasureAtomCommand):
    """Compute the angle between atom1, atom2, atom3.All coordinates are Cartesian; result is in degrees.
   \nPackage : Pmv
   \nModule  : measureCommands
   \nClass   : MeasureAngle
   \nCommand : measureAngle
   \nSynopsis:\n
        float <--- measureAngle(atom1, atom2, atom3 **kw)
   \nRequired Argument:\n        
       atom1  ---  first atom
       \natom2  --- second atom
       \natom3  --- third atom
    """


    def angle(self, c1, c2, c3):
        v1 = Numeric.array(c1) - Numeric.array(c2)
        distance1 = math.sqrt(Numeric.sum(v1*v1))
        v2 = Numeric.array(c3) - Numeric.array(c2)
        distance2 = math.sqrt(Numeric.sum(v2*v2))
        sca = Numeric.dot(v1, v2)/(distance1*distance2)
        if sca<-1.0: 
            sca = -1.0
        elif sca>1.0: 
            sca = 1.0
        return math.acos(sca)*180/math.pi

    
    def doit(self, atom1, atom2, atom3):
        c1 = self.getTransformedCoords(atom1)
        c2 = self.getTransformedCoords(atom2)
        c3 = self.getTransformedCoords(atom3)
        return self.angle(c1, c2, c3)
    

    def __call__(self, atom1, atom2, atom3, **kw):
        """float <- measureAngle(atom1, atom2, atom3 **kw)
        \natom1 --- first atom
        \natom2 --- second atom
        \natom3 --- third atom"""
        ats = self.vf.expandNodes(atom1)
        if not len(ats): return 'ERROR'
        atom1 = ats[0]
        ats = self.vf.expandNodes(atom2)
        if not len(ats): return 'ERROR'
        atom2 = ats[0]
        ats = self.vf.expandNodes(atom3)
        if not len(ats): return 'ERROR'
        atom3 = ats[0]
        return apply(self.doitWrapper, (atom1, atom2, atom3), kw)

    
    
class MeasureTorsion(MeasureAtomCommand):
    """Compute the torsion between atom1, atom2, atom3, atom4.All coordinates are Cartesian; result is in degrees.
   \nPackage : Pmv
   \nModule  : measureCommands
   \nClass   : MeasureTorsion
   \nCommand : measureTorsion
   \nSynopsis:\n
        float <- measureTorsion(atom1, atom2, atom3, atom4, **kw)
   \nRequired Argument:\n        
        atom1 --- first atom
        \natom2 --- second atom
        \natom3 --- third atom
        \natom4 --- fourth atom
    """


    def torsion(self, x1, x2, x3, x4):
        """
        Compute the torsion angle between x1, x2, x3, x4.
        All coordinates are cartesian; result is in degrees.
        Raises a ValueError if angle is not defined.
        """
        from math import sqrt, acos
        import numpy.oldnumeric as Numeric

        tang=0.0
        assert x1.shape == (3, )
        assert x2.shape == (3, )
        assert x3.shape == (3, )
        assert x4.shape == (3, )

        a = x1-x2
        b = x3-x2
        c = self.vvmult(a, b)

        a = x2-x3
        b = x4-x3
        d = self.vvmult(a, b)

        dd=sqrt(Numeric.sum(c*c))
        de=sqrt(Numeric.sum(d*d))

        if dd<0.001 or de<0.001:
            raise ValueError ( 'Torsion angle undefined, degenerate points')

        vv = Numeric.dot(c, d) / (dd*de);
        if vv<1.0: tang=vv
        else: tang= 1.0
        if tang<-1.0: tang=-1.0
        tang = acos(tang)
        tang = tang*57.296

        b = self.vvmult(c, d)
        if Numeric.dot(a, b) > 0.0: tang = -tang
        return tang

    
    def doit(self, atom1, atom2, atom3, atom4):
        c1 = self.getTransformedCoords(atom1)
        c2 = self.getTransformedCoords(atom2)
        c3 = self.getTransformedCoords(atom3)
        c4 = self.getTransformedCoords(atom4)
        return self.torsion(c1, c2, c3, c4)
    

    def __call__(self, atom1, atom2, atom3, atom4, **kw):
        """float <--- measureTorsion(atom1, atom2, atom3, atom4, **kw)
        \natom1  --- first atom
        \natom2  --- second atom
        \natom3  --- third atom
        \natom4  --- fourth atom"""
        ats = self.vf.expandNodes(atom1)
        if not len(ats): return 'ERROR'
        atom1 = ats[0]
        ats = self.vf.expandNodes(atom2)
        if not len(ats): return 'ERROR'
        atom2 = ats[0]
        ats = self.vf.expandNodes(atom3)
        if not len(ats): return 'ERROR'
        atom3 = ats[0]
        ats = self.vf.expandNodes(atom4)
        if not len(ats): return 'ERROR'
        atom4 = ats[0]
        return apply(self.doitWrapper, (atom1, atom2, atom3, atom4), kw)


from opengltk.OpenGL import GL

class MeasureGUICommand(MeasureAtomCommand, MVAtomICOM):
    """
    Base class for commands which provide measureCommands user-interface.
    Implements setLength_cb, userpref callback, setLength, guiCallback and
    stopICOM
    \nPackage : Pmv
    \nModule  : measureCommands
    \nClass   : MeasureGUICommand
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        MVAtomICOM.__init__(self)
        self.atomList = []
        self.atomCenters = []
        self.labelStrs = []
        self.labelCenters = []
        self.lineVertices = []
        self.snakeLength = 4
        self.continuousUpdate = 0

        
    def setLength_cb(self, name, oldval, newLength):
        self.setLength(newLength)


    def continuousUpdate_cb(self, name, oldval, newval):
        if not self.vf.hasGui: return
##         ehm = self.vf.GUI.ehm
        if newval == 'yes':
            self.continuousUpdate = 1
            for event in ['<B2-Motion>', '<B3-Motion>', '<Shift-B3-Motion>']:
                self.vf.GUI.addCameraCallback(event, self.update_cb)
##                 if self.update_cb not in ehm.eventHandlers[event]:
##                     ehm.AddCallback(event, self.update_cb)
        else:
            self.continuousUpdate = 0
            for event in ['<B2-Motion>', '<B3-Motion>', '<Shift-B3-Motion>']:
                self.vf.GUI.removeCameraCallback(event, self.update_cb)
##                 if self.update_cb in ehm.eventHandlers[event]:
##                     ehm.RemoveCallback(event, self.update_cb)
                

    def update_cb(self, event=None):
        if not self.vf.hasGui: return
        if not len(self.atomList):
            return
        vi = self.vf.GUI.VIEWER
        if vi.redirectTransformToRoot:
            return
        if vi.currentObject==vi.rootObject:
            return 
        self.update()


    def setLength(self, newLength):
        assert newLength>0, 'can only set to values > 0'
        self.snakeLength = newLength

        
    def guiCallback(self, event=None):
        self.vf.setICOM(self, modifier='Shift_L', mode='pick',
                        topCommand=0)


    def setupUndoBefore(self,ats):
        self.addUndoCall((),{},self.name)


    def undo(self,*args, **kw):
        if len(self.lineVertices):
            self.atomList = self.atomList[:-1]
            self.update(forward=0)


    def onRemoveObjectFromViewer(self, mol):
        lenAts = len(self.atomList)
        #if cmd has no atoms on its list, nothing to do
        if not lenAts:
            return
        #remove any atoms which are being deleted from viewer
        self.atomList = AtomSet(self.atomList)-mol.allAtoms
        #if some have been removed, do an update
        if lenAts!=len(self.atomList):
            self.update()
            

    def startICOM(self):
        self.vf.setIcomLevel( Atom )


    def initICOM(self, modifier):
        #when cmd becomes icom and user pref is set, register callback
        if self.continuousUpdate:
#            ehm = self.vf.GUI.ehm
            for event in ['<B2-Motion>', '<B3-Motion>', '<Shift-B3-Motion>']:
                self.vf.GUI.addCameraCallback(event, self.update_cb)
##                 if ehm.eventHandlers.has_key(event) and self.update_cb not in \
##                     ehm.eventHandlers[event]:
##                     ehm.AddCallback(event, self.update_cb)


    def removeIcomGeometry(self):
        self.atomList = []
        self.atomCenters = []
        self.labelStrs = []
        self.labelCenters = []
        self.lineVertices = []
        self.spheres.Set(vertices=[])
        #self.spheres.Set(vertices=[], tagModified=False)
        self.lines.Set(vertices=[], faces=[])
        #self.lines.Set(vertices=[], faces=[], tagModified=False)
        self.labels.Set(vertices=[])
        #self.labels.Set(vertices=[], tagModified=False)
        if hasattr(self, 'fan'):
            self.arcNormals = []
            self.arcVectors = []
            self.arcCenters = []
            self.fan.Set(vertices=[], vnormals=[])
            #self.fan.Set(vertices=[], vnormals=[], tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        

    def stopICOM(self):
        #when cmd stops being icom, remove callback
##         ehm = self.vf.GUI.ehm
        for event in ['<B2-Motion>', '<B3-Motion>', '<Shift-B3-Motion>']:
            self.vf.GUI.removeCameraCallback(event, self.update_cb)
##             if ehm.eventHandlers.has_key(event) and self.update_cb in \
##                     ehm.eventHandlers[event]:
##                 ehm.RemoveCallback(event, self.update_cb)

##
## MS this version was usng the snake length to measure between n consecutive
## points (i.e. snake=0 means click 1, 2, 3, 4 will show distance 1-2 2-3 and
## 3-4, Next click will remove 1-2 and add 4-5
## This is not as usedul at showign distance 1-2 3-4 5-6 etc
##
## class MeasureDistanceGUICommand(MeasureGUICommand):
##     """
##     This command measures distance between atoms.
##     Lines are drawn between consecutively picked atoms and labels are display
##     showing the distance between atoms.
##     The userpref 'Number of Measure Distances' sets the 'snakeLength' which is
##     how many distance measures can be displayed at the same time.
##     When more than that number are measured, the first distance measured is
##     no longer labeled.
##    \nPackage : Pmv
##    \nModule  : measureCommands
##    \nClass   : MeasureDistanceGUICommand
##    \nCommand : measureDistanceGC
##    \nSynopsis:\n
##         distance/None<---measureDistanceGC(atoms)
##    \nRequired Argument:\n        
##            atoms --- atom(s)
##     """
##     def __init__(self, func=None):
##         MeasureGUICommand.__init__(self, func=func)
##         self.flag = self.flag | self.objArgOnly

##     def guiCallback(self, event=None):
##         MeasureGUICommand.guiCallback(self, event)
##         self.vf.setICOM(self.vf.measureDistance2, modifier='Control_L',
##                         topCommand=0)

## #    def stopICOM(self):
## #        MeasureGUICommand.stopICOM(self)
## #        self.vf.measureDistance2.spheres.Set(vertices=[])
## #        self.measureDistance2.lines.Set(vertices=[], faces=[])
## #        self.measureDistance2.labels.Set(vertices=[])
        
##     def onAddCmdToViewer(self):
##         if not self.vf.commands.has_key('setICOM'):
##             self.vf.loadCommand('interactiveCommands', 'setICOM', 'Pmv',
##                                 topCommand=0)
##         if not self.vf.commands.has_key('measureDistance'):
##             self.vf.loadCommand('measureCommands', 'measureDistance',
##                                 'Pmv', topCommand=0) 
##         if not self.vf.commands.has_key('measureDistanceCntr'):
##             self.vf.loadCommand('measureCommands', 'measureDistance2',
##                                 'Pmv', topCommand=0) 

##         self.masterGeom = Geom('measureDistGeom', shape=(0,0), 
##                                 pickable=0, protected=True)
##         self.masterGeom.isScalable = 0

##         if self.vf.hasGui:
##             measure_geoms = check_measure_geoms(self.vf.GUI)
##             self.vf.GUI.VIEWER.AddObject(self.masterGeom, parent = measure_geoms)

##         self.lines = IndexedPolylines('distLine', materials = ((1,1,0),),
##                                       inheritMaterial=0, lineWidth=3, 
##                                       stippleLines=1, protected=True)
##         self.labels = GlfLabels(name='distLabel', shape=(0,3),
##                              inheritMaterial=0, materials = ((1,1,0),)) 
##         self.spheres = Spheres(name='distSpheres', shape=(0,3),
##                                inheritMaterial=0, radii=0.2, quality=15,
##                                materials = ((1.,1.,0.),), protected=True) 
##         if self.vf.hasGui:
##             for item in [self.lines, self.labels, self.spheres]:
##                 self.vf.GUI.VIEWER.AddObject(item, parent=self.masterGeom)
        
##         doc = """Number of labeled distances displayed simultaneousely.
## Valid values are integers>0"""
##         self.vf.userpref.add('Number of Measure Distances', 2,
##                              callbackFunc = [self.setLength_cb],
##                              category="Molecules",
##                              validateFunc = lambda x: x>0, doc=doc )
##         #used after startICOM is invoked
##         doc = """Continuous update of distances if 'transformRoot only' is
## turned off  and viewer's current object is not Root."""
##         choices = ['yes','no']
##         self.vf.userpref.add('Continuous Update Distance', 'yes', choices,
##                              callbackFunc = [self.continuousUpdate_cb],
##                              category="Molecules",
##                              doc=doc )
##         self.snakeLength = 4


##     def __call__(self, atoms, **kw):
##         """distance/None<---measureDistanceGC(atoms)
##         \natoms --- atom(s)"""
##         if type(atoms) is types.StringType:
##             self.nodeLogString = "'"+atoms+"'"
##         ats = self.vf.expandNodes(atoms)
##         if not len(ats): return 'ERROR'
##         return apply(self.doitWrapper, (ats,), kw)


##     def doit(self, ats):
##         for at in ats:
##             lenAts = len(self.atomList)
##             if lenAts and lenAts%2!=0 and at==self.atomList[-1]:
##                 continue
##             self.atomList.append(at)
##             if len(self.atomList)>self.snakeLength+1:
##                 self.atomList = self.atomList[-self.snakeLength-1:]
##             self.update()
##         if len(self.labelStrs):
##             return float(self.labelStrs[-1])


##     def update(self, forward=1, event=None):
##         if not len(self.atomList):
##             self.spheres.Set(vertices=[])
##             #self.spheres.Set(vertices=[], tagModified=False)
##             self.labels.Set(vertices=[])
##             #self.labels.Set(vertices=[], tagModified=False)
##             self.lines.Set(vertices=[])
##             #self.lines.Set(vertices=[], tagModified=False)
##             return
##         self.lineVertices=[]
##         #each time have to recalculate lineVertices
##         for at in self.atomList:
##             c1 = self.getTransformedCoords(at)
##             self.lineVertices.append(tuple(c1))
##         self.spheres.Set(vertices=self.lineVertices)
##         #self.spheres.Set(vertices=self.lineVertices, tagModified=False)
##         #setting spheres doesn't trigger redraw so do it explicitly
##         self.vf.GUI.VIEWER.Redraw()
##         #each time have to recalculate labelCenters and labelStrs
##         if len(self.lineVertices)>1:
##             self.labelCenters = []
##             self.labelStrs = []
##             numLabels = len(self.lineVertices)-1
##             for i in range(numLabels):
##                 c0 = Numeric.array(self.lineVertices[i])
##                 c1 = Numeric.array(self.lineVertices[i+1])
##                 newCenter = tuple((c1 + c0)/2.0)
##                 self.labelCenters.append(newCenter)
##                 at1 = self.atomList[i]
##                 at2 = self.atomList[i+1]
##                 d = self.vf.measureDistance(at1, at2, topCommand=0)
##                 dLabel = '%.3f' %d
##                 self.labelStrs.append(dLabel)
##             labLimit = self.snakeLength
##             #correct length of labels here
##             if len(self.labelStrs)>labLimit:
##                 self.labelCenters = self.labelCenters[-labLimit:]
##                 self.labelStrs = self.labelStrs[-labLimit:]
##                 self.lineVertices = self.lineVertices[-(labLimit+1):]
##             self.labels.Set(vertices=self.labelCenters,labels=self.labelStrs)
##                             #tagModified=False)
##             self.lines.Set(vertices=self.lineVertices, type=GL.GL_LINE_STRIP,
##                            faces=[ range(len(self.lineVertices)) ], freshape=1)
##                            #tagModified=False)
        
##         elif len(self.lineVertices)==1 and len(self.labelCenters)==1:
##             #this fixes case of stepping back over 1st label
##             self.labels.Set(vertices=[])
##             #self.labels.Set(vertices=[], tagModified=False)
##             self.lines.Set(vertices=[])
##             #self.lines.Set(vertices=[], tagModified=False)
            

## MeasureDistanceGUICommandGUI = CommandGUI()
## MeasureDistanceGUICommandGUI.addMenuCommand(
##     'menuRoot', 'Display', 'Distance (Shift Pick)', cascadeName = 'Measure')


class MeasureDistanceGUICommand(MeasureGUICommand):
    """
    This command measures distance between atoms.
    Lines are drawn between pairs of consecutively picked atoms and labels
    are display showing the distance.

   \nPackage : Pmv
   \nModule  : measureCommands
   \nClass   : MeasureDistanceGUICommand
   \nCommand : measureDistanceGC
   \nSynopsis:\n
        distance/None<---measureDistanceGC(atoms)
   \nRequired Argument:\n        
           atoms --- atom(s)
    """
    def __init__(self, func=None):
        MeasureGUICommand.__init__(self, func=func)
        self.flag = self.flag | self.objArgOnly

    def guiCallback(self, event=None):
        MeasureGUICommand.guiCallback(self, event)
        self.vf.setICOM(self.vf.measureDistGUI, modifier='Control_L',
                        topCommand=0)

    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('setICOM'):
            self.vf.loadCommand('interactiveCommands', 'setICOM', 'Pmv',
                                topCommand=0)
        if not self.vf.commands.has_key('measureDistance'):
            self.vf.loadCommand('measureCommands', 'measureDistance',
                                'Pmv', topCommand=0) 

        self.masterGeom = Geom('measureDistGeom', shape=(0,0), pickable=0 )
        self.masterGeom.isScalable = 0

        if self.vf.hasGui:
            measure_geoms = check_measure_geoms(self.vf.GUI)
            self.vf.GUI.VIEWER.AddObject(self.masterGeom, parent=measure_geoms)

        self.lines = IndexedPolylines('distLine', materials = ((1,1,0),),
                                      inheritMaterial=0, lineWidth=3., 
                                      stippleLines=1, pickable=0)
        self.labels = GlfLabels(
            name='distLabel', shape=(0,3), font='arial1.glf',
            fontStyle='solid3d', fontScales=(.5, .5, .3),
            inheritMaterial=0, materials = ((1,1,0),)) 
        self.spheres = Spheres(name='distSpheres', shape=(0,3),
                               inheritMaterial=0, radii=0.2, quality=15,
                               materials = ((1.,1.,0.),)) 
        if self.vf.hasGui:
            for item in [self.lines, self.labels, self.spheres]:
                self.vf.GUI.VIEWER.AddObject(item, parent=self.masterGeom)
        

    def __call__(self, atoms, **kw):
        """distance/None<---measureDistanceGC(atoms)
        \natoms --- atom(s)"""
        if type(atoms) is types.StringType:
            self.nodeLogString = "'"+atoms+"'"
        ats = self.vf.expandNodes(atoms)
        if not len(ats): return 'ERROR'
        return self.doitWrapper(*(ats,), **kw)


    def doit(self, ats):
        for at in ats:
            lenAts = len(self.atomList)
            if lenAts and at==self.atomList[-1]:
                continue
            self.atomList.append(at)
            self.update()
        if len(self.labelStrs):
            return float(self.labelStrs[-1])


    def update(self, forward=1, event=None):
        if not len(self.atomList):
            self.spheres.Set(vertices=[])
            #self.spheres.Set(vertices=[], tagModified=False)
            self.labels.Set(vertices=[])
            #self.labels.Set(vertices=[], tagModified=False)
            self.lines.Set(vertices=[])
            #self.lines.Set(vertices=[], tagModified=False)
            return
        self.lineVertices=[]
        #each time have to recalculate lineVertices
        for at in self.atomList:
            c1 = self.getTransformedCoords(at)
            self.lineVertices.append(tuple(c1))

        if len(self.lineVertices)%2:
            self.spheres.Set(vertices=[self.lineVertices[-1]])
        else:
            self.spheres.Set(vertices=[])

        #self.spheres.Set(vertices=self.lineVertices, tagModified=False)
        #setting spheres doesn't trigger redraw so do it explicitly
        self.vf.GUI.VIEWER.Redraw()
        #each time have to recalculate labelCenters and labelStrs
        if len(self.lineVertices)>1:
            self.labelCenters = []
            self.labelStrs = []
            self.faces = []
            numLabels = len(self.lineVertices)-1
            for i in range(0,numLabels,2):
                c0 = Numeric.array(self.lineVertices[i])
                c1 = Numeric.array(self.lineVertices[i+1])
                newCenter = tuple((c1 + c0)/2.0)
                self.labelCenters.append(newCenter)
                at1 = self.atomList[i]
                at2 = self.atomList[i+1]
                d = self.vf.measureDistance(at1, at2, topCommand=0)
                dLabel = '%.3f' %d
                self.labelStrs.append(dLabel)
                self.faces.append([i,i+1])
            #correct length of labels here
            self.labels.Set(vertices=self.labelCenters,labels=self.labelStrs)
                            #tagModified=False)
            self.lines.Set(vertices=self.lineVertices, type=GL.GL_LINE_STRIP,
                           faces=self.faces, freshape=1)
                           #tagModified=False)
        
        elif len(self.lineVertices)==1 and len(self.labelCenters)==1:
            #this fixes case of stepping back over 1st label
            self.labels.Set(vertices=[])
            #self.labels.Set(vertices=[], tagModified=False)
            self.lines.Set(vertices=[])
            #self.lines.Set(vertices=[], tagModified=False)
            
MeasureDistanceGUICommandGUI = CommandGUI()
MeasureDistanceGUICommandGUI.addMenuCommand(
    'menuRoot', 'Display', 'Distance (Shift Pick)', cascadeName = 'Measure')


class MeasureAngleGUICommand(MeasureGUICommand):
    """Accumulates picked atoms.Draws fans, lines and labels labelling the angle between trios of selected atoms (color-coded orange).Userpref 'measureAngleSL' sets the 'snakeLength' which is how many angle measureDisplays can be seen at the same time.When more than that number are measured, the first angle measured is no longer labeled.
   \nPackage : Pmv
   \nModule  : measureCommands
   \nClass   : MeasureAngleGUICommand
   \nCommand : measureAngleGC
   \nSynopsis:\n
        angle/None<---measureAngleGC(atoms)
   \nRequired Argument:\n        
        atoms --- atom(s)
        \nangle --- returned when the number of atoms is a multiple of 3
    """
    
    def __init__(self, func=None):
        MeasureGUICommand.__init__(self, func=func)
        self.flag = self.flag | self.objArgOnly

    def onAddCmdToViewer(self):
        from DejaVu.Arcs3D import Fan3D
        from DejaVu.bitPatterns import pat3
        self.arcNormals = []
        self.arcVectors = []
        self.arcCenters = []
        if not self.vf.commands.has_key('setICOM'):
            self.vf.loadCommand('interactiveCommands', 'setICOM', 'Pmv',
                                topCommand=0)
        if not self.vf.commands.has_key('measureAngle'):
            self.vf.loadCommand('measureCommands', 'measureAngle', 'Pmv',
                                topCommand=0)

        self.masterGeom = Geom('measureAngleGeom',shape=(0,0), 
                                pickable=0, protected=True)
        self.masterGeom.isScalable = 0

        if self.vf.hasGui:
            measure_geoms = check_measure_geoms(self.vf.GUI)
            self.vf.GUI.VIEWER.AddObject(self.masterGeom, parent = measure_geoms)

        self.lines = IndexedPolylines('angleLine', materials = ((1,.5,0),),
                                      inheritMaterial=0, lineWidth=3,
                                      stippleLines=1, protected=True,
                                      pickable=0)
        self.fan = Fan3D('angles', materials = ((1,.5,0),), culling=GL.GL_NONE,
                         inheritMaterial=0, stipplePolygons=1, radii=(1.,),
                         inheritStipplePolygons=0, backPolyMode=GL.GL_FILL,
                         pickable=0)
        self.fan.polygonstipple.Set(pattern=pat3)
        #self.fan.polygonstipple.Set(pattern=pat3, tagModified=False)
        #self.fan.RenderMode(GL.GL_FILL)
        #self.fan.RenderMode(GL.GL_FILL, face=GL.GL_BACK)
        self.labels = GlfLabels(
            name='angleLabel', shape=(0,3), font='arial1.glf',
            fontStyle='solid3d', fontScales=(.5, .5, .3),
            inheritMaterial=0,  materials = ((1.,.5,0.),))
        self.spheres = Spheres(name='angleSpheres',  shape=(0,3),
                               inheritMaterial=0, radii=0.2, quality=15,
                               materials = ((1.,.5,0.),), protected=True) 
        if self.vf.hasGui:
            for item in [self.lines,self.labels, self.spheres, self.fan]:
                self.vf.GUI.VIEWER.AddObject(item, parent=self.masterGeom)
        doc = """Number of labeled angles displayed.
Valid values are integers>0"""
        self.vf.userpref.add('Number of Measure Angles', 4,
                             callbackFunc = [self.setLength_cb],
                             category="Molecules",
                             validateFunc = lambda x: x>0, doc=doc)
        #used after startICOM is invoked
        doc = """Continuous update of angles if 'transformRoot only' is
turned off  and viewer's current object is not Root."""
        choices = ['yes','no']
        self.vf.userpref.add('Continuous Update Angle', 'yes', choices,
                             callbackFunc = [self.continuousUpdate_cb],
                             category="Molecules",
                             doc=doc )
        self.snakeLength = 4

        

    def __call__(self, atoms, **kw):
        """angle/None<---measureAngleGC(atoms)
           \natoms --- atom(s)
           \nangle --- returned when the number of atoms is a multiple of 3"""
        if type(atoms) is types.StringType:
            self.nodeLogString = "'"+atoms+"'"
        ats = self.vf.expandNodes(atoms)
        if not len(ats): return 'ERROR'
        return apply(self.doitWrapper, (ats,), kw)


    def doit(self, ats):
        for at in ats:
            lenAts = len(self.atomList)
            if lenAts and lenAts%3!=0 and at==self.atomList[-1]:
                continue
            self.atomList.append(at)
            l = len(self.atomList)
            #for this command, reset after every 3
            #wrap when len(atoms)=3*self.snakeLength+1
            if l>3*self.snakeLength:
                self.atomList = self.atomList[3:]
            self.update()
        if len(self.labelStrs) and len(self.atomList)%3==0:
            return float(self.labelStrs[-1])


    def update(self,forward=1, event=None):
        if not len(self.atomList):
            self.spheres.Set(vertices=[])
            #self.spheres.Set(vertices=[], tagModified=False)
            self.labels.Set(vertices=[])
            #self.labels.Set(vertices=[], tagModified=False)
            self.lines.Set(vertices=[])
            #self.lines.Set(vertices=[], tagModified=False)
            self.vf.GUI.VIEWER.Redraw()
            return
        limit = self.snakeLength
        #each time have to recalculate lineVertices
        self.lineVertices=[]
        for at in self.atomList:
            c1 = self.getTransformedCoords(at)
            self.lineVertices.append(tuple(c1))

        #display spheres:
        if len(self.lineVertices)%3:
            self.spheres.Set(
                vertices=self.lineVertices[-(len(self.lineVertices)%3):])
        else:
            self.spheres.Set(vertices=[])

        #self.spheres.Set(vertices=self.lineVertices, tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        #label with angle
        #lines between spheres are only drawn when angle completed
        #that is, len(ats)%3=0
        if len(self.lineVertices)<3:
            self.labels.Set(vertices=[])
            #self.labels.Set(vertices=[], tagModified=False)
            self.fan.Set(vertices=[])
            #self.fan.Set(vertices=[], tagModified=False)
            self.lines.Set(vertices=[])
            #self.lines.Set(vertices=[], tagModified=False)
        else:
            #should all of these be reset?
            self.arcNormals=[]
            self.arcVectors=[]
            self.arcCenters=[]
            self.labelCenters=[]
            self.labelStrs=[]
            #rebuild arcNormals, arcVectors, arcCenters
            #labelCenters, labelStrs, 
            #this gets done lenATs/3 times
            numItems = len(self.atomList)/3
            for i in range(numItems):
                at0 = self.atomList[i*3]
                at1 = self.atomList[i*3+1]
                at2 = self.atomList[i*3+2]
                ang = self.vf.measureAngle(at0, at1, at2, topCommand=0)
                v, n = self.normal(at0, at1, at2)
                self.arcNormals.append(n)
                #self.arcNormals = self.arcNormals[-limit:]
                self.arcVectors.append(v)
                #self.arcVectors = self.arcVectors[-limit:]
                self.arcCenters.append(self.getTransformedCoords(at1))
                #self.arcCenters = self.arcCenters[-limit:]
                angLabel = '%.3f' %ang
                self.labelStrs.append(angLabel)
                c0 = self.getTransformedCoords(at0)
                c1 = self.getTransformedCoords(at2)
                newcenter = tuple((c0+c1)/2.0)
                self.labelCenters.append(newcenter)
            #to reset labels, lines and fan, EACH TIME
            self.labels.Set(vertices=self.labelCenters,labels=self.labelStrs)
                            #tagModified=False)
            faces = range(numItems*3)
            faces = Numeric.reshape(faces, (-1,3))
            self.lines.Set(vertices=self.lineVertices, type=GL.GL_LINE_STRIP,
                           faces=faces, freshape=1)
                           #faces=faces, freshape=1, tagModified=False)
            self.fan.angles=map(float, self.labelStrs)
            self.fan.vectors=self.arcVectors
            self.fan.Set(vertices=self.arcCenters, vnormals=self.arcNormals)
                         #tagModified=False)
    

    def normal(self, at0, at1, at2):
        c0 = self.getTransformedCoords(at0)
        c1 = self.getTransformedCoords(at1)
        c2 = self.getTransformedCoords(at2)
        v1 = c1-c0
        v2 = c1-c2
        l1 = math.sqrt(Numeric.sum(v1*v1))
        l2 = math.sqrt(Numeric.sum(v2*v2))
        #FIXME
        #protect against divide by 0
        n = self.vvmult(v1/l1,v2/l2)
        n = n/math.sqrt(Numeric.sum(n*n))
        return -v2/l2, n.astype('f')

        

MeasureAngleGUICommandGUI = CommandGUI()
MeasureAngleGUICommandGUI.addMenuCommand(
    'menuRoot', 'Display', 'Angle (Shift Pick)', cascadeName = 'Measure')



class MeasureTorsionGUICommand(MeasureGUICommand):
    """Label torsion between four atoms (color coded cyan) Accumulates picked atoms.Draws polygons and labels showing the torsion angle between groups of 4 selected atoms (color-coded cyan).Userpref 'measureTorsionSL' sets the 'snakeLength' which is how many torsion measureDisplays can be seen at the same time.When more than that number are measured, the first torsion measured is no longer labeled.
   \nPackage : Pmv
   \nModule  : measureCommands
   \nClass   : MeasureTorsionGUICommand
   \nCommand : measureTorsionGC
   \nSynopsis:\n
        torsion/None<---measureTorsionGC(atoms)
   \nRequired Argument:\n        
           atoms  --- the atom(s)
           \ntorsion --- returned when the number of atoms is a multiple of 4 
    """
    
    def __init__(self, func=None):
        MeasureGUICommand.__init__(self, func=func)
        self.flag = self.flag | self.objArgOnly

    def onAddCmdToViewer(self):
        from DejaVu.bitPatterns import pat3
        from DejaVu.IndexedPolygons import IndexedPolygons
        if not self.vf.commands.has_key('setICOM'):
            self.vf.loadCommand('interactiveCommands', 'setICOM', 'Pmv',
                                topCommand=0)
        if not self.vf.commands.has_key('measureAngle'):
            self.vf.loadCommand('measureCommands', 'measureAngle', 'Pmv',
                                topCommand=0)
            
        self.masterGeom = Geom('measureTorsionGeom',shape=(0,0),
                                pickable=0, protected=True)
        self.masterGeom.isScalable = 0

        if self.vf.hasGui:
            measure_geoms = check_measure_geoms(self.vf.GUI)
            self.vf.GUI.VIEWER.AddObject(self.masterGeom, parent = measure_geoms)
        self.lines = IndexedPolygons(
            'torsionLine', materials = ((0,1,1),), culling=GL.GL_NONE,
            inheritStipplePolygons=0, inheritMaterial=0, stipplePolygons=1,
            backPolyMode=GL.GL_FILL, frontPolyMode=GL.GL_FILL, protected=True,
            pickable=0)
        if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
            self.lines.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False,)
        self.lines.polygonstipple.Set(pattern=pat3)
        #self.lines.polygonstipple.Set(pattern=pat3, tagModified=False)
        #self.lines.RenderMode(GL.GL_FILL)
        #self.lines.RenderMode(GL.GL_FILL, face=GL.GL_BACK)
        self.labels = GlfLabels(
            name='torsionLabel', shape=(0,3), font='arial1.glf',
            fontStyle='solid3d', fontScales=(.5, .5, .3),
            inheritMaterial=0, materials = ((0,1,1),))
        self.spheres = Spheres(name='torsionSpheres', shape=(0,3),
                               inheritMaterial=0, radii=0.2, quality=15,
                               materials = ((0.,1.,1.),), protected=True) 
        if self.vf.hasGui:
            for item in [self.lines, self.labels, self.spheres]:
                self.vf.GUI.VIEWER.AddObject(item, parent=self.masterGeom)
        doc = """Number of labeled torsions displayed.
Valid values are integers>0"""
        self.vf.userpref.add('Measured Torsions', 4,
                             callbackFunc=[self.setLength_cb],
                             category="Molecules",
                             validateFunc = lambda x: x>0, doc=doc)
        #used after startICOM is invoked
        doc = """Continuous update of torsions if 'transformRoot only' is
turned off  and viewer's current object is not Root."""
        choices = ['yes','no']
        self.vf.userpref.add('Continuous Update Torsion', 'yes', choices,
                             callbackFunc = [self.continuousUpdate_cb],
                             category="Molecules",
                             doc=doc )
        self.snakeLength = 4


    def __call__(self, atoms, **kw):
        """torsion/None<-measureTorsionGC(atoms)
        \natoms  --- the atom(s)
        \ntorsion --- returned when the number of atoms is a multiple of 4"""
        if type(atoms) is types.StringType:
            self.nodeLogString = "'"+atoms+"'"
        ats = self.vf.expandNodes(atoms)
        if not len(ats): return 'ERROR'
        return apply(self.doitWrapper, (ats,), kw)


    def doit(self, ats):
        for at in ats:
            lenAts = len(self.atomList)
            if lenAts and lenAts%4!=0 and at==self.atomList[-1]:
                continue
            self.atomList.append(at)
            if len(self.atomList)>4*self.snakeLength:
                self.atomList = self.atomList[4:]
            self.update()
        if len(self.labelStrs) and len(self.atomList)%4==0:
            return float(self.labelStrs[-1])


    def update(self, forward=1, event=None):
        if not len(self.atomList):
            self.spheres.Set(vertices=[])
            #self.spheres.Set(vertices=[], tagModified=False)
            self.labels.Set(vertices=[])
            #self.labels.Set(vertices=[], tagModified=False)
            self.lines.Set(vertices=[])
            #self.lines.Set(vertices=[], tagModified=False)
            self.vf.GUI.VIEWER.Redraw()
            return
        limit = self.snakeLength
        #each time have to recalculate lineVertices
        self.lineVertices=[]
        for at in self.atomList:
            c1 = self.getTransformedCoords(at)
            self.lineVertices.append(tuple(c1))
        #display spheres:
        if len(self.lineVertices)%4:
            self.spheres.Set(
                vertices=self.lineVertices[-(len(self.lineVertices)%4):])
        else:
            self.spheres.Set(vertices=[])

        #self.spheres.Set(vertices=self.lineVertices, tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        #label with torsion
        #lines between spheres are only drawn when angle completed
        #that is, len(ats)%4=0
        if len(self.lineVertices)<4:
            self.labels.Set(vertices=[])
            #self.labels.Set(vertices=[], tagModified=False)
            self.lines.Set(vertices=[])
            #self.lines.Set(vertices=[], tagModified=False)
        else:
            #rebuild labels and polygons each time
            self.labelCenters=[]
            self.labelStrs=[]
            #labelCenters, labelStrs, 
            #this gets done lenATs/4 times
            numItems = len(self.atomList)/4
            for i in range(numItems):
                at0 = self.atomList[i*4]
                at1 = self.atomList[i*4+1]
                at2 = self.atomList[i*4+2]
                at3 = self.atomList[i*4+3]
                torsion = self.vf.measureTorsion(at0, at1, at2, at3, topCommand=0)
                torsionLabel = '%.3f' %torsion
                self.labelStrs.append(torsionLabel)
                c0 = self.getTransformedCoords(at0)
                c1 = self.getTransformedCoords(at3)
                newcenter = tuple((c0+c1)/2.0)
                self.labelCenters.append(newcenter)
            #to reset labels, lines and fan, EACH TIME
            self.labels.Set(vertices=self.labelCenters,labels=self.labelStrs)
                            #tagModified=False)
            #if len(self.lineVertices)%4!=0:
                #self.lineVertices = self.lineVertices[:numItems*4]
            #only draw lines in groups of 4
            #numItems*4
            if len(self.atomList)%4==0:
                faces = range(numItems*4)
                faces = Numeric.reshape(faces, (-1,4))
                ###FIX THIS
                ###on undo: if you have just wrapped, undoing the next pt
                ###breaks because trying to set the vertices uses the old
                ###faces
                if not forward:
                    self.lines.Set(vertices=[], faces=[])
                    #self.lines.Set(vertices=[], faces=[], tagModified=False)
                self.lines.Set(vertices=self.lineVertices, faces=faces,
                               freshape=1)
                               #freshape=1, tagModified=False)
                self.vf.GUI.VIEWER.Redraw()
            else:
                #this only works going forward: undo breaks here
                if len(self.lines.faceSet.faces.array)>numItems:
                    faces = range((numItems+1)*4)
                    faces = Numeric.reshape(faces, (-1,4))
                    if forward:
                        faces = faces[1:]
                    else:
                        faces = faces[:-1]
                    self.lines.Set(faces=faces)
                    self.vf.GUI.VIEWER.Redraw()
                     


MeasureTorsionGUICommandGUI = CommandGUI()
MeasureTorsionGUICommandGUI.addMenuCommand(
    'menuRoot', 'Display', 'Torsion (Shift Pick)', cascadeName = 'Measure')


commandList = [
        {'name':'measureDistance', 'cmd':MeasureDistance(), 'gui':None}, 
        {'name':'measureAngle', 'cmd':MeasureAngle(), 'gui':None}, 
        {'name':'measureTorsion', 'cmd':MeasureTorsion(), 'gui':None}, 
## version with snake not logner used (MS Oct 2010)
##         {'name':'measureDistanceGC', 'cmd':MeasureDistanceGUICommand(),
##                 'gui':MeasureDistanceGUICommandGUI}, 
        {'name':'measureDistGUI', 'cmd':MeasureDistanceGUICommand(),
                'gui':MeasureDistanceGUICommandGUI}, 
        {'name':'measureAngleGC', 'cmd':MeasureAngleGUICommand(),
                'gui':MeasureAngleGUICommandGUI}, 
        {'name':'measureTorsionGC', 'cmd':MeasureTorsionGUICommand(),
                'gui':MeasureTorsionGUICommandGUI}, 
]


def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])

