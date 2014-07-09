## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Ruth HUEY, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/setangleCommands.py,v 1.43.4.1 2010/12/29 21:56:32 rhuey Exp $ 
#
# $Id: setangleCommands.py,v 1.43.4.1 2010/12/29 21:56:32 rhuey Exp $ 
#
#

from ViewerFramework.VFCommand import CommandGUI
from Pmv.moleculeViewer import EditAtomsEvent 
from mglutil.gui.InputForm.Tk.gui import InputFormDescr

from mglutil.gui.BasicWidgets.Tk.Dial import Dial
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ExtendedSliderWidget, ListChooser

from DejaVu import viewerConst
from DejaVu.Geom import Geom
#from DejaVu.Labels import Labels
from DejaVu.Spheres import Spheres
from DejaVu.IndexedPolylines import IndexedPolylines
from opengltk.OpenGL import GL
from Pmv.mvCommand import MVCommand, MVAtomICOM
from Pmv.measureCommands import MeasureDistance, MeasureTorsion, MeasureTorsionGUICommand
from MolKit.protein import Protein
from MolKit.molecule import Atom, AtomSet
import string, types
import Tkinter, numpy.oldnumeric as Numeric
import math

from mglutil.math.rotax import rotax

from DejaVu.glfLabels import GlfLabels


def vvmult(a,b):
    """
    Compute a vector product for 3D vectors
    """
    import numpy.oldnumeric as Numeric
    res = Numeric.zeros(3, 'f')
    res[0] = a[1]*b[2] - a[2]*b[1]
    res[1] = a[2]*b[0] - a[0]*b[2]
    res[2] = a[0]*b[1] - a[1]*b[0]
    return res


def torsionAngle(x1, x2, x3, x4):
    """
    Compute the torsion angle between x1,x2,x3,x4.
    All coordinates are cartesian, result is in degrees.
    Raises a ValueError if angle is not defined.
    """
    from math import sqrt, acos
    import numpy.oldnumeric as Numeric

    tang=0.0
    assert x1.shape == (3,)
    assert x2.shape == (3,)
    assert x3.shape == (3,)
    assert x4.shape == (3,)

    a = x1-x2
    b = x3-x2
    c = vvmult(a,b)

    a = x2-x3
    b = x4-x3
    d = vvmult(a,b)

    dd=sqrt(Numeric.add.reduce(c*c))
    de=sqrt(Numeric.add.reduce(d*d))

    if dd<0.001 or de<0.001:
        raise ValueError ( 'Torsion angle undefined, degenerate points')

    vv = Numeric.dot(c,d) / (dd*de);
    if vv<1.0: tang=vv
    else: tang= 1.0
    if tang<-1.0: tang=-1.0
    tang = acos(tang)
    tang = tang*57.296

    b = vvmult(c,d)
    if Numeric.dot(a,b) > 0.0: tang = -tang
    return tang



class SetRelativeTorsion(MeasureTorsion):
    """
        Transform the coords of atoms in subTree defined by atom1-atom2
        Set the coords of these atoms to the new values and return new coords
    """


    def __call__(self, atom1, atom2, angle, mov_atoms=None, returnVal=0,**kw):
        """movedAtomsCoords<-setRelativeTorsion(atom1, atom2, angle, returnVal)"""
        ats = self.vf.expandNodes(atom1)
        if not len(ats): return 'ERROR'
        atom1 = ats[0]
        ats = self.vf.expandNodes(atom2)
        if not len(ats): return 'ERROR'
        atom2 = ats[0]
        assert atom1.top == atom2.top
        return apply(self.doitWrapper,(atom1,atom2,angle,mov_atoms,returnVal),kw)


    def doit(self, atom1, atom2, angle, mov_atoms, returnVal=0):
        mol = atom1.top
        if mov_atoms is None:
            mov_atoms = mol.subTree(atom1, atom2, mol.allAtoms)
        assert len(mov_atoms)
        mov_coords = Numeric.array(mov_atoms.coords)
        lenCoords = len(mov_coords)
        x = Numeric.array(atom1.coords)
        y = Numeric.array(atom2.coords)
        rot = (angle * 3.14159/180.)%(2 * Numeric.pi)
        matrix = rotax(x, y, rot)
        _ones = Numeric.ones(lenCoords, 'f')
        _ones.shape = (lenCoords,1)
        mov_coords = Numeric.concatenate((mov_coords, _ones),1)
        newcoords = Numeric.dot(mov_coords, matrix)
        nc = newcoords[:,:3].astype('f')
        for i in range(lenCoords):
            at = mov_atoms[i]
            at._coords[at.conformation] = nc[i].tolist()

        event = EditAtomsEvent('coords', mov_atoms)
        self.vf.dispatchEvent(event)

        #have to return nc for setTorsionGC
        if returnVal:
            return nc



class SetTranslation(MeasureDistance):
    """
        Transform the coords by array
        Set the coords of these atoms to the new values and return new coords
    """


    def __call__(self, ats, trans, **kw):
        """newCoords<-setTranslation(ats,trans)"""
        ats = self.vf.expandNodes(ats)
        if not len(ats): return 'ERROR'
        allAtoms = ats.findType(Atom)
        #check that trans is tuple with length 3
        assert len(trans)==3
        return apply(self.doitWrapper, (allAtoms, trans), kw)


    def doit(self, ats, trans):
        for at in ats:
            at._coords[at.conformation] = (at.coords[0]+trans[0], 
                    at.coords[1]+trans[1], at.coords[2]+trans[2])



class SetQuaternion(MeasureDistance):
    """
        Transform the coords by quaternion
        Set the coords of these atoms to the new values and return new coords
    """


    def __call__(self, ats, quat, origin= (0., 0., 0.), trans=(0.,0.,0.), **kw):
        """newCoords<-setTranslation(ats,quat, trans)
        quat in form (x,y,z,w)
        origin is (x,y,z) default is (0., 0., 0.)
        trans is (x,y,z) default is (0., 0., 0.)
        doesnot assume quat is already normalized
        """

        ats = self.vf.expandNodes(ats)
        if not len(ats): return 'ERROR'
        allAtoms = ats.findType(Atom)
        #check that trans is tuple with length 3
        assert len(quat)==4
        return apply(self.doitWrapper, (allAtoms, quat, origin, trans), kw)


    def hypotenuse(self, x,y,z):
        return math.sqrt(x*x + y*y + z*z)


    def mkUnitQuat(self, quat):
        #from qmultiply.cc
        x = quat[0]
        y = quat[1]
        z = quat[2]
        w = quat[3]
        #print 'x,y,z,w=',x,y,z,w
        inv_nmag = 1./self.hypotenuse(x,y,z)
        #print 'inv_nmag=', inv_nmag
        x = x*inv_nmag
        y = y*inv_nmag
        z = z*inv_nmag
        #WHAT IS THIS???
        hqang = 0.5 * w
        s = math.sin(hqang)
        w = math.cos(hqang)
        x = s*x
        y = s*y
        z = s*z
        return x,y,z,w


    def doit(self, ats, quat, origin, trans):
        x,y,z,w = self.mkUnitQuat(quat)

        tx = x+x
        ty = y+y
        tz = z+z

        twx = w*tx
        omtxx = 1. - x*tx
        txy = y*tx
        txz = z*tx


        twy = w*ty
        tyy = y*ty
        tyz = z*ty

        twz = w*tz
        tzz = z*tz

        r11 = 1. - tyy - tzz
        r12 =      txy + twz
        r13 =      txz - twy
        r21 =      txy - twz
        r22 = omtxx    - tzz
        r23 =      tyz + twx
        r31 =      txz + twy
        r32 =      tyz - twx
        r33 = omtxx    - tyy

        newcoords = []
        transx = trans[0]
        transy = trans[1]
        transz = trans[2]
        originx = origin[0]
        originy = origin[1]
        originz = origin[2]
        for i in range(len(ats)):
            coords = ats[i].coords 
            coordx = coords[0] - originx
            coordy = coords[1] - originy
            coordz = coords[2] - originz
            #NB: it seems these would also set Translation 'T'
            tmpx = coordx*r11 + coordy*r21 + coordz*r31 + transx
            tmpy = coordx*r12 + coordy*r22 + coordz*r32 + transy
            tmpz = coordx*r13 + coordy*r23 + coordz*r33 + transz
            newentry = (tmpx, tmpy, tmpz)
            newcoords.append(newentry)
            at = ats[i]
            at._coords[at.conformation] = newentry

        #return newcoords



class SetTorsion(MeasureTorsion):
    """
        Transform the coords of atoms in subTree defined by atom1-atom2
        by angle less initial torsion defined by atom0, atom1, atom2, atom3
        Set the coords of these atoms to the new values and return new coords
    """


    def __call__(self, atom0, atom1, atom2, atom3, angle, returnVal=0, **kw):
        """movedAtomsCoords<-setTorsion(atom0, atom1, atom2, atom3,
        angle,returnVal)"""
        ats = self.vf.expandNodes(atom0)
        if not len(ats): return 'ERROR'
        atom0 = ats[0]
        ats = self.vf.expandNodes(atom1)
        if not len(ats): return 'ERROR'
        atom1 = ats[0]
        ats = self.vf.expandNodes(atom2)
        if not len(ats): return 'ERROR'
        atom2 = ats[0]
        ats = self.vf.expandNodes(atom3)
        if not len(ats): return 'ERROR'
        atom3 = ats[0]
        assert atom0.top == atom1.top == atom2.top == atom3.top
        #check that angle is between -360 and +360
        #why?
        #assert angle >= -360 and angle <= 360
        return apply(self.doitWrapper, (atom0, atom1, atom2, atom3, angle,returnVal), kw)


    def doit(self, atom0, atom1, atom2, atom3, angle, returnVal):
        init_angle=self.vf.measureTorsion.doit(atom0, atom1, atom2, atom3)
        angle = angle - init_angle
        return  self.vf.setRelativeTorsion.doit(atom1, atom2, angle, None,
                returnVal=returnVal)



class SetTorsionGUICommand(MeasureTorsionGUICommand):


    def guiCallback(self):
        self.save = self.vf.ICmdCaller.commands.value["Shift_L"]
        self.vf.setICOM(self, modifier="Shift_L", topCommand=0)
        if not hasattr(self, 'form'):
            self.buildForm()
        else:
            self.form.deiconify()


    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'GUI'):
            return
        self.undoNow = 0
        self.save = None
        from DejaVu.bitPatterns import pat3
        from DejaVu.IndexedPolygons import IndexedPolygons
        if not self.vf.commands.has_key('setICOM'):
            self.vf.loadCommand('interactiveCommands', 'setICOM', 'Pmv',
                                topCommand=0)
        if not self.vf.commands.has_key('measureTorsion'):
            self.vf.loadCommand('measureCommands', 'measureTorsion', 'Pmv',
                                topCommand=0) 

        self.masterGeom = Geom('setTorsionGeom',shape=(0,0), 
                                pickable=0, protected=True)
        self.masterGeom.isScalable = 0
        self.vf.GUI.VIEWER.AddObject(self.masterGeom,
                                parent=self.vf.GUI.miscGeom)
        self.lines = IndexedPolygons('settorsionLine', materials = ((0,1,1),),
                                     inheritMaterial=0,
                                     stipplePolygons=1, protected=True,)
        if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':                
            self.lines.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False,)
        self.lines.polygonstipple.Set(pattern=pat3)#, tagModified=False)
        #self.lines.RenderMode(GL.GL_FILL, face=GL.GL_BACK)
        self.lines.Set(backPolyMode=GL.GL_FILL)
        self.labels = GlfLabels(name='settorsionLabel', shape=(0,3),
                                    inheritMaterial=0,
                   materials = ((0,1,1),))
        self.spheres = Spheres(name='settorsionSpheres', shape=(0,3),
                               radii=0.2, quality=15,
                                    inheritMaterial=0,
                               materials = ((0.,1.,1.),), protected=True) 
        for item in [self.lines, self.labels, self.spheres]:
            self.vf.GUI.VIEWER.AddObject(item, parent=self.masterGeom)
        self.snakeLength = 1
        self.oldValue = None
        self.torsionType = Tkinter.StringVar()
        self.torsionType.set('1')
        self.newAngList = Tkinter.StringVar()
        self.TAHdata = None
        self.molecule = None
        #self.bondString = Tkinter.StringVar()
        self.callbackDict = {}
        self.callbackDict['measureDistanceGC'] = 'update'
        self.callbackDict['measureAngleGC'] = 'update'
        self.callbackDict['measureTorsionGC'] = 'update'


    def onRemoveObjectFromViewer(self, mol):
        lenAts = len(self.atomList)
        #if cmd has no atoms on its list, nothing to do
        if not lenAts:
            return
        #remove any atoms which are being deleted from viewer
        self.atomList = AtomSet(self.atomList) - mol.allAtoms
        #if some have been removed, do an update
        if lenAts!=len(self.atomList):
            self.update()
            self.extslider.set(0)



    def __call__(self, atoms, angle=None,**kw):
        """torsion/None<-setTorsionGC(atoms, angle=None)
        the torsion is returned when the number of atoms is a multiple of 4"""
        ats = self.vf.expandNodes(atoms)
        if not len(ats): return 'ERROR'
        return apply(self.doitWrapper, (ats, angle,), kw)


    def doit(self, ats, angle):
        for at in ats:
            lenAts = len(self.atomList)
            if lenAts and lenAts%4!=0 and at==self.atomList[-1]:
                continue
            if len(self.atomList)==0:
                self.molecule = at.top
            if at.top == self.molecule:
                self.atomList.append(at)
            else:
                #all atoms in torsion must be in same molecule ...(?)
                s = at.full_name()+ " not in " + self.molecule.full_name()
                self.warningMsg(s)
                return 'ERROR'
            if len(self.atomList)>4*self.snakeLength:
                self.atomList = self.atomList[4:]
            self.update()
        if  len(self.atomList)==4:
            mol = self.atomList[0].top
            at0,at1,at2,at3 = self.atomList
            self.mov_atoms = mol.subTree(at1, at2, mol.allAtoms)
            self.oldValue = self.vf.measureTorsion.doit(at0,at1,at2,at3)
            self.origValue = self.oldValue
            self.origCoords = self.mov_atoms.coords
            if hasattr(self, 'extslider'):
                self.extslider.set(self.oldValue, update=0)
            if angle: 
                #angle is what you want to end up with
                deltaAngle = angle - self.oldValue
                #print 'deltaAngle=', deltaAngle, 'angle=', angle
                self.transformCoords(deltaAngle)
                if hasattr(self, 'extslider'):
                    self.extslider.set(angle, update=0)
                #s = self.atomList[2].full_name()+'--'+self.atomList[3].full_name()
                #self.bondString.set(s)
            self.updateHistory()
            ##if self.undoNow: raise 'abc'
            #return float(self.labelStrs[-1])
            return


    def update(self, forward=1, event=None):
        if not len(self.atomList):
            self.spheres.Set(vertices=[], tagModified=False)
            self.labels.Set(vertices=[], tagModified=False)
            self.lines.Set(vertices=[], tagModified=False)
            self.vf.GUI.VIEWER.Redraw()
            return
        limit = self.snakeLength
        #each time have to recalculate lineVertices
        self.lineVertices=[]
        for at in self.atomList:
            c1 = self.getTransformedCoords(at)
            self.lineVertices.append(tuple(c1))
        #display spheres:
        self.spheres.Set(vertices=self.lineVertices, tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        #label with torsion
        #lines between spheres are only drawn when angle completed
        #that is, len(ats)%4=0
        if len(self.lineVertices)<4:
            self.labels.Set(vertices=[], tagModified=False)
            self.lines.Set(vertices=[], tagModified=False)
        else:
            #rebuild labels and polygons each time
            self.labelCenters=[]
            self.labelStrs=[]
            #labelCenters, labelStrs, 
            #this gets done lenATs/4 times
            numItems = len(self.atomList)/4
            for i in range(numItems):
                at0,at1,at2,at3 = self.atomList[i*4:i*4+4]
                torsion = self.vf.measureTorsion.doit(at0, at1, at2, at3)
                torsionLabel = '%.3f' %torsion
                self.labelStrs.append(torsionLabel)
                c0 = self.getTransformedCoords(at0)
                c1 = self.getTransformedCoords(at3)
                newcenter = tuple((c0+c1)/2.0)
                self.labelCenters.append(newcenter)
        self.vf.GUI.VIEWER.Redraw()
        items = self.callbackDict.keys()
        #items = ['measureDistanceGC','measureAngleGC','measureTorsionGC']
        #checkout whether measure update needs to be called
        icomVals = self.vf.ICmdCaller.commands.value.values()
        for item in items: 
            if not len(icomVals): break
            if not hasattr(self.vf, item):
                continue
            exec('cmd = self.vf.'+item)
            if cmd in icomVals:
                #cmd.update()
                s = self.callbackDict[item]
                exec('self.vf.' + item + '.'+ s + '()')



    def transformCoords(self, deltaAngle):
        """ deltaAngle is NOW not final angle wanted but relative"""
        #mov_coords is the array of the coords of the atoms to be moved,
        #x2 and x3 are atoms which define the axis of the transformation
        #by deltaAngle. NB: effect is that mov_atoms.coords 
        #are transformed...
        if not hasattr(self, 'mov_atoms'): return
        if not len(self.mov_atoms): return
        x1, x2, x3, x4 = self.atomList
        nc = self.vf.setRelativeTorsion.doit(x2, x3, deltaAngle, 
                self.mov_atoms, returnVal=1)
        mol = x2.top
        #mov_atoms = mol.subTree(x2, x3, mol.allAtoms)
        for i in range(len(nc)):
            at = self.mov_atoms[i]
            at._coords[at.conformation] = nc[i].tolist()
        event = EditAtomsEvent('coords', self.mov_atoms)
        self.vf.dispatchEvent(event)
        self.update()


#####Callback Functions for the Dial:
#####slideCallback 
    def slideCallback(self, eventval):
        #print 'in slideCallback'
        if len(self.atomList)!=4: return
        if not hasattr(self, 'oldValue'): return
        if self.oldValue==None:
            return
        #self.setupUndoBefore(self.atomList, self.oldValue)
        try:
            newAngle = self.extslider.get()
            tT = self.torsionType.get()
            at0, at1, at2, at3 = self.atomList
            #torsion = self.vf.measureTorsion.doit(at0, at1, at2, at3)
            torsion = self.oldValue
            if tT == '1':
                #NEWdeltaAngle = newAngle
                deltaAngle = newAngle - torsion
            else:
                #NEWdeltaAngle = newAngle + torsion
                deltaAngle = newAngle
            self.transformCoords(deltaAngle)
            #print 'deltaAngle=', deltaAngle
            self.oldValue = newAngle
            #self.oldValue = newAngle
        except ValueError:
            self.vf.GUI.message("error in slideCallback\n")


    def rdSet(self, event=None):
        #"""radiobutton selection of torsionType:
        #Absolute: initial angle to be displayed in slider/entry
        #Relative: 0 is displayed """
        if self.torsionType.get()=='1':
            aL = self.atomList
            if len(aL)==4:
                torsion = self.vf.measureTorsion.doit(aL[0],aL[1],aL[2],aL[3])
                self.extslider.set(torsion)
        else:
            self.extslider.set(0)

            

    def setupUndoBefore(self, ats, angle):
        pass


    #def setupUndoBefore(self, ats, angle):
        ##no atoms, <4 atoms, 
        #aSet = AtomSet(self.atomList)
        #self.undoMenuString = self.name
        #if len(self.atomList)==0:
            #undoCmd = 'self.setTorsionGC.atomList=[]; self.setTorsionGC.update()'
        #elif len(self.atomList)<4:
            ##need to step back here
            #undoCmd = 'self.setTorsionGC.atomList=self.setTorsionGC.atomList[:-1]; self.setTorsionGC.update()'
        #else:
            ##print 'self.oldValue=', self.oldValue
            #undoCmd = 'self.setTorsionGC(\''+ aSet.full_name()+ '\',' + str(self.oldValue) + ', topCommand=0)'
            ##self.oldValue = str(self.extslider.get())
        #self.vf.undo.addEntry((undoCmd), (self.name))
            

    def setupUndoAfter(self, ats, angle,**kw):
        #no atoms, <4 atoms, 
        aSet = AtomSet(self.atomList)
        self.undoMenuString = self.name
        if len(self.atomList)==0:
            undoCmd = 'self.setTorsionGC.atomList=[]; self.setTorsionGC.update()'
        elif len(self.atomList)<4:
            #need to step back here
            undoCmd = 'self.setTorsionGC.atomList=self.setTorsionGC.atomList[:-1]; self.setTorsionGC.update()'
        elif self.origValue==self.oldValue:
            return
        else:
            restoreAngle = self.origValue
            self.undoNow = 1
            undoCmd = 'self.setTorsionGC(\''+ aSet.full_name()+ '\',' + str(restoreAngle) + ', topCommand=0)'
        self.vf.undo.addEntry((undoCmd), (self.name))


    def Accept_cb(self):
        apply(self.setupUndoAfter,(self.atomList, self.oldValue),{})
        self.origValue = self.oldValue


    def Done_cb(self):
        self.vf.setICOM(self.save, modifier="Shift_L", mode='pick',topCommand = 0)
        self.stopICOM()



    def startICOM(self):
        self.vf.setIcomLevel( Atom )
        if not hasattr(self, 'form'):
            self.buildForm()
        else:
            self.form.deiconify()


    def stopICOM(self):
        if hasattr(self, 'form'):
            self.form.withdraw()
        self.atomList = []
        self.atomCenters = []
        self.labelStrs = []
        self.labelCenters = []
        self.lineVertices = []
        self.spheres.Set(vertices=[], tagModified=False)
        self.lines.Set(vertices=[], faces=[], tagModified=False)
        self.labels.Set(vertices=[], tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        #when cmd stops being icom, remove callback
##         ehm = self.vf.GUI.ehm
##         for event in ['<B2-Motion>', '<B3-Motion>']:
##             if ehm.eventHandlers.has_key(event) and self.update_cb in \
##                     ehm.eventHandlers[event]:
##                 ehm.RemoveCallback(event, self.update_cb)
        for event in ['<B2-Motion>', '<B3-Motion>']:
            self.vf.GUI.removeCameraCallback(event, self.update_cb)


    def repeat_transTors(self, event=None):
        deltaAngle = self.extslider.get()
        if self.torsionType.get() != '1':
            self.transformCoords(deltaAngle)
        #this is here in order to create a log message
        nc = self.vf.setRelativeTorsion(self.atomList[1], self.atomList[2], deltaAngle, 
                self.mov_atoms, returnVal=1)
        event = EditAtomsEvent('coords', self.mov_atoms)
        self.vf.dispatchEvent(event)


    def new_Tors(self, event = 0):
        self.atomList = []
        self.update()


    #when called, most recent 4 atoms are in self.atomList
    def updateHistory(self):
        """1: call TorsionHistory.getTorsion:
        make a new TorsionAngle or add current angle to angleList
        2: put TA.name_string into ListBox
        3: best if insert a tuple (string to be displayed, item itself)
        4: adjust size with self.historyList.configure(height=self.[].size)
        5: limit overall size to 4"""
        #print 'in updateHistory'
        molecule = self.atomList[-1].top
        if self.TAHdata is None:
            self.TAHdata = TorsionHistory(molecule)
        a1,a2,a3,a4 = self.atomList
        newone=self.TAHdata.getTorsion(a1,a2,a3,a4 )
        #first check to see if it is in there already??? 
        #need to get info back from getTorsion....(???)
        if hasattr(self, 'historyList'):
            if newone.new:
                self.historyList.insert('end',newone.name_string)
                if int(self.historyList.cget('height'))<4:
                    self.historyList.configure(height=self.historyList.size())
            if self.historyList.curselection():
                    self.historyList.select_clear(self.historyList.curselection())
            newindex=self.TAHdata.getIndex(newone)
            self.historyList.select_set(newindex)
            self.historyList.see(newindex)
        #set entry to a string ==current TA's angleList
        newstring= ""
        for item in newone.angleList:
            newstring=newstring +" " + "%5.3f" %item
        self.newAngList.set(newstring)



    def HLCommand(self, event=None):
        """double-clicking selection in listbox causes curselection to be picked...
        1:self.atomList set to atoms of curselection
        2:self.mov_atoms set to atoms of curselection
        3:self.selAtom[1-4].Set(vertices=atoms.coords)
        4:reset entry +slider and init_bondAngle etc
        5.add current angle to selection's.angleList"""
        #get TA:
        if self.historyList.get(0)=='': return
        items=self.historyList.curselection()
        if type(items)==types.TupleType:
            items = items[0]
        try:
            items=map(int, items)
        except ValueError:pass
        thisTA=self.TAHdata.torslist[items[0]]
        #get currentAngle
        current= thisTA.getCurrentAngle()
        if not thisTA.inList(current):
            thisTA.angleList.append(current)
        newAts = AtomSet([thisTA.atom1,thisTA.atom2, thisTA.atom3,\
                    thisTA.atom4])
        #reset self.molecule
        self.atomList = []
        self.molecule = newAts[0].top
        self.doit(newAts, current)
        #self.setTorsionAngle(thisTA.atom1, thisTA.atom2, thisTA.atom3, thisTA.atom4, current, 'A')
        #self.drawTransformedAngle()
        #self.updatespheres(items[0])
        #self.update()
        self.extslider.set(current,0)
        newstring= ""
        for item in thisTA.angleList:
            newstring=newstring +" " + "%5.3f" %item
        self.newAngList.set(newstring)


    def getAngList(self, event=None):
        items=self.historyList.curselection()
        try:
            items=map(int, items)
        except ValueError:pass
        thisTA=self.TAHdata.torslist[items[0]]
        thisTA.angleList=map(float, split(self.newAngList.get()))
        last=thisTA.angleList[-1]
        newAts = AtomSet([thisTA.atom1,thisTA.atom2, thisTA.atom3,\
                    thisTA.atom4])
        #reset self.molecule
        self.atomList = []
        self.molecule = newAts[0].top
        self.doit(newAts, last)
        #self.doit(thisTA.atom1, thisTA.atom2, thisTA.atom3, thisTA.atom4,last,'A')
        #self.setTorsionAngle(thisTA.atom1, thisTA.atom2, thisTA.atom3, thisTA.atom4,last,'A')
        #self.drawTransformedAngle()
        #self.updatespheres(items[0])
        self.extslider.set(last,0)
       

    def stepBack(self, event=None):
        items=self.historyList.curselection()
        if len(items)==0: return
        try:
            items=map(int, items)
        except ValueError:
            pass
        thisTA=self.TAHdata.torslist[items[0]]
        ####last angle is thisTA.angleList[-1]
        if len(thisTA.angleList)>1:
            last=thisTA.angleList[-1]
            lastIndex=thisTA.angleList.index(last)
            thisTA.angleList=thisTA.angleList[:lastIndex]
            last=thisTA.angleList[-1]
        else:
            last=thisTA.angleList[0]
        newAts = AtomSet([thisTA.atom1,thisTA.atom2, thisTA.atom3,\
                    thisTA.atom4])
        #reset self.molecule
        self.atomList = []
        self.molecule = newAts[0].top
        self.doit(newAts, last)
        #self.doit(thisTA.atom1, thisTA.atom2, thisTA.atom3, thisTA.atom4,last,'A')
        #self.setTorsionAngle(thisTA.atom1, thisTA.atom2, thisTA.atom3, thisTA.atom4,last,'A')
        #self.drawTransformedAngle()
        #self.updatespheres(items[0])
        newstring= ""
        for item in thisTA.angleList:
            newstring=newstring +" " + "%5.3f" %item
        self.newAngList.set(newstring)
        self.extslider.set(last, 0)
        #IS THIS ENOUGH in order to create correct log?
        self.mouseUp()
       

    def startOver(self, event=None):
        items=self.historyList.curselection()
        if len(items)==0: return
        try:
            items=map(int, items)
        except ValueError:pass
        thisTA=self.TAHdata.torslist[items[0]]
        self.resetAngle(thisTA)


    def resetAngle(self, thisTA, event=None):
        #first angle is thisTA.angleList[0]
        ang=thisTA.angleList[0]
        newAts = AtomSet([thisTA.atom1,thisTA.atom2, thisTA.atom3,\
                    thisTA.atom4])
        #reset self.molecule
        self.atomList = []
        self.molecule = newAts[0].top
        self.doit(newAts, ang)
        #self.doit(thisTA.atom1, thisTA.atom2, thisTA.atom3, thisTA.atom4,ang,'A')
        #self.setTorsionAngle(thisTA.atom1, thisTA.atom2, thisTA.atom3, thisTA.atom4,ang,'A')
        if len(thisTA.angleList)>1:
            thisTA.angleList=thisTA.angleList[:1]
        #self.drawTransformedAngle()
        self.extslider.set(ang,0)
        self.mouseUp()
        self.newAngList.set("%5.3f" %ang)
    

    def resetAll(self, event=None):
        if self.TAHdata==None: return
        for item in self.TAHdata.torslist:
            self.resetAngle(item)
        self.spheres.Set(vertices=[], tagModified=False)
        self.vf.GUI.VIEWER.Redraw()


    def buildForm(self):
        if hasattr(self, 'ifd'):
            return
        self.torsionType = Tkinter.StringVar()
        self.torsionType.set('1')
        self.ifd = ifd = InputFormDescr(title = 'Set Torsion Angle')
        ifd.append({'name':'extLabel',
                    'widgetType': Tkinter.Label,
                    'wcfg':{'text':'Set Angle:\n(180=trans)'},
                    'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                                'columnspan':2}})
        ifd.append( {'name':'extslider',
            'widgetType': ExtendedSliderWidget,
            'wcfg':{'label':'torsion',
                'minval':-360., 'maxval':360.,
                'width':150,
                'immediate':1,
                'command':self.slideCallback,
                'sliderType':'float',
                'entrypackcfg':{'side':'bottom'}},
            'gridcfg':{'sticky':'we', 'columnspan':2}})
        ifd.append({'name':'typeLabel',
                    'widgetType': Tkinter.Label,
                    'wcfg':{'text':'Torsion Type'},
                    'gridcfg':{'sticky':'we', 'columnspan':2}})
        ifd.append({'name':'rdbut1',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'Absolute',
                'variable': self.torsionType,
                'value':1,
                'command':self.rdSet
                },
            'gridcfg':{'sticky':'we'}})
        ifd.append({'name':'rdbut2',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'Relative ',
                'variable': self.torsionType,
                'value':0,
                'command':self.rdSet
                },
            'gridcfg':{'sticky':'we', 'row':-1, 'column':1}})
        ifd.append({'name':'historyList',
            'widgetType':ListChooser,
            'wcfg':{
                'title':'TorsionAngle\nTranformation History',
                'mode': 'single',
                'command': self.HLCommand,
                'lbwcfg':{'height':5, 
                    'selectforeground': 'yellow',
                    'exportselection': 0,
                    'width': 30},
            },
            'gridcfg':{'sticky':'we', 'columnspan':2}})
        ifd.append({'name':'hbut1',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Step Back ',
                'command': self.stepBack},
            'gridcfg':{'sticky':'we','columnspan':2}})
        ifd.append({'name':'hbut2',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Start Over ',
                'command': self.startOver},
            'gridcfg':{'sticky':'we','columnspan':2}})
        ifd.append({'name':'hbut3',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Reset All ',
                'command': self.resetAll},
            'gridcfg':{'sticky':'we','columnspan':2}})
        ifd.append({'name':'angListEnt',
           'widgetType':Tkinter.Entry, 
           'wcfg':{'width':5,
                'command':self.getAngList,
                'textvariable':self.newAngList},
           'gridcfg':{'sticky':'we','columnspan':2}})
        ifd.append({'name':'hbut4',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Move',
                'command': self.repeat_transTors},
            'gridcfg':{'sticky':'we','columnspan':2}})
        ifd.append({'name':'hbut5',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'New Torsion',
                'command': self.new_Tors},
            'gridcfg':{'sticky':'we','columnspan':2}})
        #ifd.append({'name':'accept',
                    #'widgetType': Tkinter.Button,
                    #'wcfg':{'text' : 'Accept',
                            #'command': self.Accept_cb},
                    #'gridcfg':{'sticky':'we'}})
        ifd.append({'name':'done',
                    'widgetType': Tkinter.Button,
                    'wcfg':{'text' : 'Done',
                            'command': self.Done_cb},
                    'gridcfg':{'sticky':'we','columnspan':2}})
                    #'gridcfg':{'sticky':'we','column':1, 'row':-1}})
        self.form = self.vf.getUserInput(ifd, modal=0, blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW',self.Done_cb)
        self.extslider = self.ifd.entryByName['extslider']['widget']
        self.extslider.draw.bind('<ButtonRelease-1>', self.mouseUp, add='+')
        self.extslider.entry.bind('<Return>', self.mouseUp, add='+')
        self.historyList = self.ifd.entryByName['historyList']['widget'].lb
        #self.historyList.bind("<Double-Button-1>",self.HLCommand)
        self.hbut1 = self.ifd.entryByName['hbut1']['widget']
        self.hbut2 = self.ifd.entryByName['hbut2']['widget']
        self.hbut3 = self.ifd.entryByName['hbut3']['widget']
        self.angListEnt = self.ifd.entryByName['angListEnt']['widget']
            

    def mouseUp(self, event=None):
        #print "in mouseUp"
        #fix this: atomList length dependent
        if len(self.atomList)==4:
            at0,at1,at2,at3 = self.atomList
            angle = self.extslider.get()
            if self.torsionType.get()=='1':
                self.vf.setTorsion(at0, at1, at2, at3, angle)
            else:
                self.vf.setRelativeTorsion(at1, at2, angle)



setTorsionGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
              'menuButtonName':'Set Torsion Angle',
              'menuEntryLabel':'Show Set Torsion Panel',
              'index':0}

SetTorsionGUI = CommandGUI()
SetTorsionGUI.addMenuCommand('menuRoot', 'Edit', 'Set Torsion',
                             cascadeName='Torsion Angles')




class TorsionAngle:
    def __init__(self,  atom1, atom2, atom3, atom4):
        self.molecule=atom1.top
        self.name_string=atom1.name +"-"+ atom2.name +"-"+ atom3.name +"-"+ atom4.name
        self.atom1=atom1
        self.atom2=atom2
        self.atom3=atom3
        self.atom4=atom4
        self.mov_atoms = self.molecule.subTree(atom2, atom3, self.molecule.allAtoms)
        self.currentAngle = self.measureAngle(self.atom1, self.atom2, self.atom3, self.atom4)
        self.angleList=[]
        self.addAngle(self.currentAngle)
        self.new=1

    def __cmp__(self,tA2):
        if self.atom1==tA2.atom1 and self.atom2==tA2.atom2 and self.atom3==tA2.atom3 and self.atom4 == tA2.atom4:
            return 1
        else:
            return 0

    def addAngle(self, angle):
        if not self.inList(angle):
            self.angleList.append(angle)


    def inList(self, angle):
        for ent in self.angleList:
            d = angle-ent
            if d<.05  and d >-.05:
                return 1
        return 0


    def measureAngle(self, atom1,atom2,atom3,atom4):
        w=Numeric.array(atom1.coords)
        x=Numeric.array(atom2.coords)
        y=Numeric.array(atom3.coords)
        z=Numeric.array(atom4.coords)
        thisAngle = torsionAngle(w,x,y,z)
        return thisAngle

    def getCurrentAngle(self):
        self.currentAngle=self.measureAngle(self.atom1,self.atom2,self.atom3,self.atom4)
        return self.currentAngle




class  TorsionHistory:
    def __init__(self, mol):
        self.torslist=[]
        self.molecule=mol

    def addTorsion(self, newtangle):
        previous=filter(newtangle.__cmp__,self.torslist)
        #if this angle is already on the list, add its current angle
        #to its angleList
        if len(previous)>0:
            previous[0].addAngle(newtangle.currentAngle)
            newtangle=previous[0]
            previous[0].new=0
        #if newtangle is new, just append it to the torslist
        else:
            self.torslist.append(newtangle)
        return newtangle

    def getTorsion(self, a1, a2, a3, a4):
        newone=TorsionAngle(a1,a2,a3,a4)
        return self.addTorsion(newone)

    def getIndex(self, newtangle):
        result=map(newtangle.__cmp__, self.torslist)
        #at this point result is a list such as [1,0,0,0,0]
        return result.index(1)



commandList = [
    {'name':'setTorsionGC','cmd': SetTorsionGUICommand(),'gui':SetTorsionGUI},
    {'name':'setRelativeTorsion','cmd': SetRelativeTorsion(),'gui':None},
    {'name':'setTorsion','cmd': SetTorsion(),'gui':None},
    {'name':'setTranslation','cmd': SetTranslation(),'gui':None},
    {'name':'setQuaternion','cmd': SetQuaternion(),'gui':None},
    ]


def initModule(viewer):

    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])

