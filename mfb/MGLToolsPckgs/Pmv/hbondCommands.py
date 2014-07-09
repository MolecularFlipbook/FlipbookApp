## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 


############################################################################
#
# Author: Ruth HUEY
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

# $Header
#
# $Id: hbondCommands.py,v 1.93.4.2 2011/08/19 22:19:35 rhuey Exp $
#


from ViewerFramework.VFCommand import CommandGUI
from Pmv.moleculeViewer import AddAtomsEvent
from mglutil.gui.BasicWidgets.Tk.colorWidgets import ColorChooser

from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.util.callback import CallBackFunction
from mglutil.gui.BasicWidgets.Tk.customizedWidgets \
    import ExtendedSliderWidget, ListChooser
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from mglutil.util.misc import ensureFontCase

from Pmv.mvCommand import MVCommand, MVAtomICOM, MVBondICOM
from Pmv.measureCommands import MeasureAtomCommand

from MolKit.molecule import Atom, AtomSet, Bond
from MolKit.molecule import BondSet, HydrogenBond, HydrogenBondSet
from MolKit.distanceSelector import DistanceSelector
from MolKit.hydrogenBondBuilder import HydrogenBondBuilder
from MolKit.pdbWriter import PdbWriter

from DejaVu.Geom import Geom
from DejaVu.Spheres import Spheres
from DejaVu.Points import CrossSet
from DejaVu.Cylinders import Cylinders
from DejaVu.spline import DialASpline, SplineObject
from DejaVu.GleObjects import GleExtrude, GleObject
from DejaVu.Shapes import Shape2D, Triangle2D, Circle2D, Rectangle2D,\
     Square2D, Ellipse2D

from Pmv.stringSelectorGUI import StringSelectorGUI
from PyBabel.util import vec3

import Tkinter, numpy.oldnumeric as Numeric, math, string, os
from string import strip, split
from types import StringType

from opengltk.OpenGL import GL

from DejaVu.glfLabels import GlfLabels


def check_hbond_geoms(VFGUI):
    hbond_geoms_list = VFGUI.VIEWER.findGeomsByName('hbond_geoms')
    if hbond_geoms_list==[]:
        hbond_geoms = Geom("hbond_geoms", shape=(0,0), protected=True)
        VFGUI.VIEWER.AddObject(hbond_geoms, parent=VFGUI.miscGeom)
        hbond_geoms_list = [hbond_geoms]
    return hbond_geoms_list[0]
 


# lists of babel_types for donor-acceptor 
#   derived from MacDonald + Thornton 
#   'Atlas of Side-Chain + Main-Chain Hydrogen Bonding'
# plus sp2Acceptor Nam

sp2Donors = ['Nam', 'Ng+', 'Npl']
sp3Donors = ['N3+', 'O3','S3']
allDonors = []
allDonors.extend(sp2Donors)
allDonors.extend(sp3Donors)
#added Nam because of bdna cytidine N3
#NB: Npl cannot be an acceptor if the sum of its bonds' bondOrder>2
sp2Acceptors = ['O2', 'O-', 'Npl', 'Nam']
sp3Acceptors = ['S3', 'O3']
allAcceptors = []
allAcceptors.extend(sp2Acceptors)
allAcceptors.extend(sp3Acceptors)
a_allAcceptors = []
for n in allAcceptors:
    a_allAcceptors.append('a'+n)


def dist(c1, c2):
    d = Numeric.array(c2) - Numeric.array(c1) 
    ans = math.sqrt(Numeric.sum(d*d))
    return round(ans, 3)


def getAngle(ac, hat, don ):
    acCoords = getTransformedCoords(ac)
    hCoords = getTransformedCoords(hat)
    dCoords = getTransformedCoords(don)
    pt1 = Numeric.array(acCoords, 'f')
    pt2 = Numeric.array(hCoords, 'f')
    pt3 = Numeric.array(dCoords, 'f')
    #pt1 = Numeric.array(ac.coords, 'f')
    #pt2 = Numeric.array(hat.coords, 'f')
    #pt3 = Numeric.array(don.coords, 'f')
    v1 = Numeric.array(pt1 - pt2)
    v2 = Numeric.array(pt3 - pt2)
    dist1 = math.sqrt(Numeric.sum(v1*v1))
    dist2 = math.sqrt(Numeric.sum(v2*v2))
    sca = Numeric.dot(v1, v2)/(dist1*dist2)
    if sca>1.0:
        sca = 1.0
    elif sca<-1.0:
        sca = -1.0
    ang =  math.acos(sca)*180./math.pi
    return round(ang, 5)


def applyTransformation(pt, mat):
    pth = [pt[0], pt[1], pt[2], 1.0]
    return Numeric.dot(mat, pth)[:3]


def getTransformedCoords(atom):
    # when there is no viewer, the geomContainer is None
    if atom.top.geomContainer is None:
        return atom.coords
    g = atom.top.geomContainer.geoms['master']
    c = applyTransformation(atom.coords, g.GetMatrix(g))
    return  c.astype('f')



class GetHydrogenBondDonors(MVCommand):
    """This class allows user to get AtomSets of sp2 hydridized and sp3 hybridized hydrogenBond Donors able.
   \nPackage : Pmv
   \nModule  : bondsCommands
   \nClass   : GetHydrogenBondDonors
   \nCommand :getHBDonors 
   \nSynopsis:\n
        sp2Donors, sp3Donors <- getHBDonors(nodes, donorList, **kw)
   \nRequired Arguments:\n    
   nodes ---
   donorList ---
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly
    
    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('typeAtoms'):
            self.vf.loadCommand('editCommands', 'typeAtoms', 'Pmv',
                                topCommand=0)


    def __call__(self, nodes, donorList=allDonors,**kw):
        """sp2Donors, sp3Donors <- getHBDonors(nodes, donorList, **kw) """ 
        if type(nodes) is StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        ats = nodes.findType(Atom)
        try:
            ats.babel_type
        except AttributeError:
            tops = ats.top.uniq()
            for t in tops:
                self.vf.typeAtoms(t.allAtoms, topCommand=0)
        return apply(self.doitWrapper, (ats, donorList), kw)


    def checkForPossibleH(self, ats, blen):
        #check that if at has all bonds, at least one is to a hydrogen
        # have to do this by element??
        probAts = AtomSet(ats.get(lambda x, blen=blen: len(x.bonds)==blen))
        #probOAts = ats.get(lambda x, blen=blen: len(x.bonds)==blen)
        #probSAts = ats.get(lambda x, blen=blen: len(x.bonds)==blen)
        if probAts:
            rAts = AtomSet([])
            for at in probAts:
                if not len(at.findHydrogens()):
                    rAts.append(at)
            if len(rAts):
                ats =  ats.subtract(rAts)
        return ats
    

    def doit(self, ats, donorList):
        #getHBDonors 
        sp2 = []
        sp3 = []
        for item in sp2Donors:
            if item in donorList: sp2.append(item)
        for item in sp3Donors:
            if item in donorList: sp3.append(item)
        
        dAts2 = ats.get(lambda x, l=sp2: x.babel_type in l)
        if not dAts2: dAts2=AtomSet([])
        else: 
            dAts2 = self.checkForPossibleH(dAts2, 3)
        
        dAts3 = ats.get(lambda x, l=sp3: x.babel_type in l)
        if not dAts3: dAts3=AtomSet([])
        else: dAts3 = self.checkForPossibleH(dAts3, 4)

        return dAts2, dAts3



class GetHydrogenBondAcceptors(MVCommand):
    """This class allows user to get AtomSets of sp2 hydridized and sp3 hybridized
hydrogenBond Acceptors.
   \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : GetHydrogenBondEnergies
   \nCommand : getHBondEnergies
   \nSynopsis:\n
        sp2Acceptors, sp3Acceptors <- getHBAcceptors(nodes, acceptorList, **kw)
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('typeAtoms'):
            self.vf.loadCommand('editCommands', 'typeAtoms', 'Pmv',
                                topCommand=0)


    def __call__(self, nodes, acceptorList=allAcceptors,**kw):
        """sp2Acceptors, sp3Acceptors <- getHBAcceptors(nodes, acceptorList, **kw) """
        if type(nodes) is StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        ats = nodes.findType(Atom)
        #no way to know if typeBonds has been called on each molecule!
        try:
            ats._bndtyped
        except:
            tops = ats.top.uniq()
            for t in tops:
                self.vf.typeBonds(t.allAtoms, topCommand=0)
        return apply(self.doitWrapper, (ats, acceptorList), kw)


    def filterAcceptors(self, accAts):
        ntypes = ['Npl', 'Nam']
        npls = accAts.get(lambda x, ntypes=ntypes: x.babel_type=='Npl')
        nams = accAts.get(lambda x, ntypes=ntypes: x.babel_type=='Nam')
        #nAts = accAts.get(lambda x, ntypes=ntypes: x.babel_type in ntypes)
        restAts = accAts.get(lambda x, ntypes=ntypes: x.babel_type not in ntypes)
        if not restAts: restAts = AtomSet([])
        #if nAts:
        if npls:
            #for at in nAts:
            for at in npls:
                s = 0
                for b in at.bonds:
                    if b.bondOrder=='aromatic':
                        s = s + 2
                    else: s = s + b.bondOrder
                #if s<3:
                #apparently this is wrong
                if s<4:
                    restAts.append(at)
        if nams:
            #for at in nAts:
            for at in nams:
                s = 0
                for b in at.bonds:
                    if b.bondOrder=='aromatic':
                        s = s + 2
                    else: s = s + b.bondOrder
                    #s = s + b.bondOrder
                if s<3:
                    restAts.append(at)
        return restAts
                
        

    def doit(self, ats, acceptorList):
        #getHBAcceptors 
        sp2 = []
        sp3 = []
        for item in sp2Acceptors:
            if item in acceptorList: sp2.append(item)
        for item in sp3Acceptors:
            if item in acceptorList: sp3.append(item)

        dAts2 = AtomSet(ats.get(lambda x, l=sp2: x.babel_type in l))
        if dAts2: 
            dAts2 = self.filterAcceptors(dAts2)
        dAts3 = AtomSet(ats.get(lambda x, l=sp3: x.babel_type in l))
        return dAts2, dAts3



class GetHydrogenBondEnergies(MVCommand):
    """This class allows user to get a list of energies of HydrogenBonds. For this calculation, the bond must have a hydrogen atom AND it must know its type.
Energy calculation based on "Protein Flexibility and dynamics using constraint
theory", J. Molecular Graphics and Modelling 19, 60-69, 2001. MF Thorpe, Ming
Lei, AJ Rader, Donald J.Jacobs and Leslie A. Kuhn.
   \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : GetHydrogenBondEnergies
   \nCommand : getHBondEnergies
   \nSynopsis:\n
        [energies] <- getHBondEnergies(nodes, **kw) 
   \nRequired Arguments:\n     
        nodes --- TreeNodeSet holding the current selection
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def onAddCmdToViewer(self):
        self.vf.loadModule('measureCommands', 'Pmv', log=0)
        if not self.vf.commands.has_key('typeAtoms'):
            self.vf.loadCommand('editCommands', 'typeAtoms', 'Pmv',
                                topCommand=0, log=0)
        

    def __call__(self, nodes, **kw):
        """[energies] <- getHBondEnergies(nodes, **kw) 
        \nnodes --- TreeNodeSet holding the current selection
        """
        if type(nodes) is StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        ats = nodes.findType(Atom)
        hats = AtomSet([])
        for at in ats:
            if hasattr(at, 'hbonds'): hats.append(at)
        if not len(hats):
            self.warningMsg('no hbonds in specified nodes')
            return 'ERROR'
        return apply(self.doitWrapper, (hats,), kw)


    def getEnergy(self, b):
        accAt = b.accAt
        b0 = accAt.bonds[0]
        acN = b0.atom1
        if id(acN)==id(accAt): acN = b0.atom2
        b.acN = acN
        #b.acN = b.accAt.bonds[0].neighborAtom(b.accAt)
        if b.dlen is None:
            b.dlen = dist(getTransformedCoords(b.donAt), 
                            getTransformedCoords(b.accAt))
            #b.dlen = dist(b.donAt.coords, b.accAt.coords)
        r = 2.8/b.dlen
        if b.phi is None: b.phi = self.vf.measureAngle(b.hAt, b.accAt, 
                acN, topCommand=0)
        if b.theta is None: b.theta = self.vf.measureAngle(b.donAt, b.hAt, 
                b.accAt, topCommand=0)
        b.gamma = self.vf.measureTorsion(b.donAt, b.hAt, b.accAt, 
                acN, topCommand=0)
        #make all angles into radians
        theta = b.theta * math.pi/180.
        newAngle = math.pi - theta
        gamma = b.gamma * math.pi/180.
        phi = b.phi * math.pi/180.
        n = 109.5*math.pi/180.

        if b.type is None:
            #get # of donAt+# of accAt
            try:
                b.donAt.babel_type
                b.accAt.babel_type
            except AttributeError:
                b_ats = AtomSet([b.donAt, b.accAt])
                tops = b_ats.top.uniq()
                for t in tops:
                    self.vf.typeAtoms(t.allAtoms, topCommand=0)
            if b.donAt.babel_type in sp2Donors:
                d1=20
            else:
                d1=30
            if b.accAt.babel_type in sp2Acceptors:
                d2=2
            else:
                d2=3
            b.type = d1+d2
                

        if b.type==33:
            f = (math.cos(theta)**2)*\
                (math.e**(-(newAngle)**6))*(math.cos(phi-n)**2)
        elif b.type==32:
            f = (math.cos(theta)**2)*\
                (math.e**(-(newAngle)**6))*(math.cos(phi)**2)
        elif b.type==23:
            f = ((math.cos(theta)**2)*\
                (math.e**(-(newAngle)**6)))**2
        else:
            f = (math.cos(theta)**2)*\
                (math.e**(-(newAngle)**6))*(math.cos(max(theta, gamma))**2)
        newVal =  8.*(5.*(r**12) - 6.*(r**10))*f
        b.energy =  round(newVal, 3)
        return b.energy


    def doit(self, hats):
        #getHBondEnergies
        energyList = []
        hbonds = hats.hbonds
        #SHOULD hbonds be checked for type??? HERE???????
        for b in hbonds:
            if b.energy:
                energyList.append(b.energy)
            elif b.hAt is None:
                energyList.append(None)
            else:
                energyList.append(self.getEnergy(b))
        #print 'returning ', len(energyList), ' hbond energies: ', energyList
        return energyList



class ShowHBDonorsAcceptors(MVCommand):
    """This class allows user to show AtomSets of HydrogenBond donors and acceptors.
   \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : ShowHBDonorsAcceptors
   \nCommand : showHBDA
   \nSynopsis:\n
        None <- showHBDA(dnodes, anodes, donorList, acceptorList, **kw)
    """


    def onAddCmdToViewer(self):
        self.vf.loadModule('editCommands', 'Pmv', log=0)
        self.vf.loadCommand('interactiveCommands','setICOM', 'Pmv', log=0)
        #setup geoms
        #miscGeom = self.vf.GUI.miscGeom

        self.masterGeom = Geom('hbondDonorAcceptorGeoms',shape=(0,0), 
                                pickable=0, protected=True)
        self.masterGeom.isScalable = 0
        if self.vf.hasGui:
            hbond_geoms = check_hbond_geoms(self.vf.GUI)
            self.vf.GUI.VIEWER.AddObject(self.masterGeom, parent=hbond_geoms)
        self.hbdonor2=CrossSet('hbSP2Donors', 
            materials=((0.,1.,1.),), offset=0.4, lineWidth=2,
            inheritMaterial=0, protected=True)
        self.hbdonor2.Set(visible=1, tagModified=False)
        self.hbdonor2.pickable = 0
        self.hbdonor3=CrossSet('hbSP3Donors', 
            materials=((0.,.3,1.),), offset=0.4, lineWidth=2,
            inheritMaterial=0, protected=True)
        self.hbacceptor2=Spheres('hbSP2Acceptors', shape=(0,3),
            radii=0.2, quality=15, materials=((1.,.8,0.),), inheritMaterial=0, protected=True)
        self.hbacceptor3=Spheres('hbSP3Acceptors', shape=(0,3),
            radii=0.2, quality=15, materials=((1.,.2,0.),), inheritMaterial=0, protected=True)
        for item in [self.hbdonor2, self.hbdonor3, self.hbacceptor2,\
                self.hbacceptor3]:
            item.Set(visible=1, tagModified=False)
            item.pickable = 0
            if self.vf.hasGui:
                self.vf.GUI.VIEWER.AddObject(item, parent=self.masterGeom)
        #setup Tkinter variables
        varNames = ['hideDSel', 'N3', 'O3','S3','Nam', 'Ng', 'Npl',\
                'hideASel',  'aS3', 'aO3', 'aO2', 'aO', 'aNpl',
                'aNam', 'sp2D', 'sp3D', 'sp2A', 'sp3A','useSelection']
                
        for n in varNames:
            exec('self.'+n+'=Tkinter.IntVar()')
            exec('self.'+n+'.set(1)')
        self.showDTypeSel = Tkinter.IntVar()
        self.showATypeSel = Tkinter.IntVar()


    def __call__(self, dnodes, anodes, donorList=allDonors,
            acceptorList=allAcceptors, **kw):
        """None <- showHBDA(dnodes, anodes, donorList, acceptorList, **kw) """
        
        dnodes = self.vf.expandNodes(dnodes)
        donats = dnodes.findType(Atom)
        anodes = self.vf.expandNodes(anodes)
        acats = anodes.findType(Atom)
        if not (len(donats) or len(acats)): return 'ERROR'
        apply(self.doitWrapper, (donats, acats, donorList, acceptorList), kw)


    def doit(self, donats, acats,  donorList, acceptorList):
        #showHBDA
        if len(donats):
            dAts2, dAts3 = self.vf.getHBDonors(donats, 
                    donorList=donorList, topCommand=0)
            msg = ''
            if dAts2:
                newVerts = []
                for at in dAts2:
                    newVerts.append(getTransformedCoords(at).tolist())
                self.hbdonor2.Set(vertices=newVerts, visible=1,
                                  tagModified=False)
                #self.hbdonor2.Set(vertices = dAts2.coords, visible=1,
                #                  tagModified=False)
            else:
                msg = msg + 'no sp2 donors found '
                dAts2 = AtomSet([])
                self.hbdonor2.Set(vertices=[], tagModified=False)
            if dAts3:
                newVerts = []
                for at in dAts3:
                    newVerts.append(getTransformedCoords(at).tolist())
                self.hbdonor3.Set(vertices=newVerts, visible=1,
                                  tagModified=False)
                #self.hbdonor3.Set(vertices = dAts3.coords, visible=1, tagModified=False
            else:
                if len(msg): msg = msg + ';'
                msg = msg + 'no sp3 donors found'
                dAts3 = AtomSet([])
                self.hbdonor3.Set(vertices=[], tagModified=False)
            if len(msg):
                self.warningMsg(msg)
        else:
            dAts2 = AtomSet([])
            dAts3 = AtomSet([])
            self.hbdonor2.Set(vertices=[], tagModified=False)
            self.hbdonor3.Set(vertices=[], tagModified=False)
        #NOW THE ACCEPTORS:
        if len(acats):
            acAts2, acAts3 = self.vf.getHBAcceptors(acats,
                    acceptorList=acceptorList, topCommand=0)
            msg = ''
            if acAts2:
                newVerts = []
                for at in acAts2:
                    newVerts.append(getTransformedCoords(at).tolist())
                self.hbacceptor2.Set(vertices = newVerts, visible=1,
                                     tagModified=False)
                #self.hbacceptor2.Set(vertices = acAts2.coords, visible=1, tagModified=False)
            else:
                msg = msg + 'no sp2 acceptors found '
                acAts2 = AtomSet([])
                self.hbacceptor2.Set(vertices=[], tagModified=False)
            if acAts3:
                newVerts = []
                for at in acAts3:
                    newVerts.append(getTransformedCoords(at).tolist())
                self.hbacceptor3.Set(vertices = newVerts, visible=1,
                                     tagModified=False)
                #self.hbacceptor3.Set(vertices = acAts3.coords, visible=1, tagModified=False)
            else:
                if len(msg): msg = msg + ';'
                msg = msg + 'no sp3 acceptors found'
                acAts3 = AtomSet([])
                self.hbacceptor3.Set(vertices=[], tagModified=False)
            if len(msg): self.warningMsg(msg)
        else:
            acAts2 = AtomSet([])
            acAts3 = AtomSet([])
            self.hbacceptor2.Set(vertices=[], tagModified=False)
            self.hbacceptor3.Set(vertices=[], tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        #PUT UP A FORM TO TOGGLE Visibility etc (?)
        # show/hide sp2/sp3
        # select, save
        if not len(dAts2) and not len(dAts3) and not len(acAts2)\
            and not len(acAts3):
            self.warningMsg('no donors or acceptors found')
            return
        ifd2 = self.ifd2 = InputFormDescr(title = "Show/Hide Donors and Acceptors")
        if len(dAts2):
            ifd2.append({'name':'donor2',
                'widgetType':Tkinter.Checkbutton,
                'wcfg':{'text':'sp2 donors ',
                    'variable': self.sp2D,
                    'command': CallBackFunction(self.showGeom, 
                                self.hbdonor2, self.sp2D),
                    },
                'gridcfg':{'sticky':'w'}})
        if len(dAts3):
            ifd2.append({'name':'donor3',
                'widgetType':Tkinter.Checkbutton,
                'wcfg':{'text':'sp3 donors ',
                    'variable': self.sp3D,
                    'command': CallBackFunction(self.showGeom, 
                                self.hbdonor3, self.sp3D),
                    },
                'gridcfg':{'sticky':'w'}})
               # 'gridcfg':{'sticky':'w', 'row':-1, 'column':1}})
        if len(acAts2):
            ifd2.append({'name':'accept2',
                'widgetType':Tkinter.Checkbutton,
                'wcfg':{'text':'sp2 acceptors ',
                    'variable': self.sp2A,
                    'command': CallBackFunction(self.showGeom, 
                                self.hbacceptor2, self.sp2A),
                    },
                'gridcfg':{'sticky':'w'}})
        if len(acAts3):
            ifd2.append({'name':'accept3',
                'widgetType':Tkinter.Checkbutton,
                'wcfg':{'text':'sp3 acceptors ',
                    'variable': self.sp3A,
                    'command': CallBackFunction(self.showGeom, 
                                self.hbacceptor3, self.sp3A),
                    },
                'gridcfg':{'sticky':'w'}})
                #'gridcfg':{'sticky':'w', 'row':-1, 'column':1}})
        ifd2.append({'widgetType': Tkinter.Button,
            'text':'Select',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'ew' },
            'command':CallBackFunction(self.select_cb,dAts2,dAts3,acAts2,acAts3)})
        ifd2.append({'widgetType': Tkinter.Button,
            'text':'Cancel',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'ew', 'column':1,'row':-1},
            'command':self.cancel_cb})
        self.form2 = self.vf.getUserInput(self.ifd2, modal=0, blocking=0)
        self.form2.root.protocol('WM_DELETE_WINDOW',self.cancel_cb)



    def showGeom(self, geom, var, event=None):
        geom.Set(visible=var.get(), tagModified=False)
        self.vf.GUI.VIEWER.Redraw()


    def select_cb(self, dAts2, dAts3, acAts2, acAts3):
        #NB need to set level to Atom
        self.vf.setIcomLevel(Atom)
        vars = [self.sp2D, self.sp2D, self.sp2A, self.sp3A]
        atL = [dAts2, dAts3, acAts2, acAts3]
        for i in range(4):
            if vars[i].get() and len(atL[i]):
                self.vf.select(atL[i])
                
    
    def cancel_cb(self, event=None):
        for g in [self.hbdonor2, self.hbdonor3, self.hbacceptor2,\
                self.hbacceptor3]:
            g.Set(vertices=[], tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        self.form2.destroy()


    def buildForm(self):
        ifd = self.ifd = InputFormDescr(title = "Select nodes + types of donor-acceptors:")
        ifd.append({'name':'DkeyLab',
                    'widgetType':Tkinter.Label,
                    'text':'For Hydrogen Bonds Donors:',
                    'gridcfg':{'sticky':'w','columnspan':3}})
        ifd.append({'name':'selDRB0',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'Use all atoms',
                'variable': self.hideDSel,
                'value':1,
                'command':self.hideDSelector
                },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'selDRB1',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'Set atoms to use',
                'variable': self.hideDSel,
                'value':0,
                'command':self.hideDSelector
                },
            'gridcfg':{'sticky':'w', 'row':-1, 'column':1}})
        ifd.append({'name': 'keyDSelector',
            'wtype':StringSelectorGUI,
            'widgetType':StringSelectorGUI,
            'wcfg':{ 'molSet': self.vf.Mols,
                    'vf': self.vf,
                    'all':1,
                    'crColor':(0.,1.,.2),
            },
            'gridcfg':{'sticky':'we', 'columnspan':2 }})
        ifd.append({'name':'limitDTypes',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Limit donor types ',
                'variable': self.showDTypeSel,
                'command':self.hideDTypes
                },
            'gridcfg':{'sticky':'w', 'columnspan':2}})
        ifd.append({'name':'N3+',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'N3+',
                'variable': self.N3, },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'O3',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'O3',
                'variable': self.O3, },
            'gridcfg':{'sticky':'w','row':-1, 'column':1}})
        ifd.append({'name':'S3',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'S3',
                'variable': self.S3, },
            'gridcfg':{'sticky':'w','row':-1, 'column':2}})
        ifd.append({'name':'Nam',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Nam',
                'variable': self.Nam, },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'Ng+',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Ng+',
                'variable': self.Ng, },
            'gridcfg':{'sticky':'w','row':-1, 'column':1}})
        ifd.append({'name':'Npl',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Npl',
                'variable': self.Npl, },
            'gridcfg':{'sticky':'w','row':-1, 'column':2}})
        #now the acceptors
        ifd.append({'name':'AkeyLab',
                    'widgetType':Tkinter.Label,
                    'text':'For Hydrogen Bonds Acceptors:',
                    'gridcfg':{'sticky':'w','columnspan':3}})
        ifd.append({'name':'selARB0',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'Use all atoms',
                'variable': self.hideASel,
                'value':1,
                'command':self.hideASelector
                },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'selARB1',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'Set atoms to use',
                'variable': self.hideASel,
                'value':0,
                'command':self.hideASelector
                },
            'gridcfg':{'sticky':'w', 'row':-1, 'column':1}})
        ifd.append({'name': 'keyASelector',
            'wtype':StringSelectorGUI,
            'widgetType':StringSelectorGUI,
            'wcfg':{ 'molSet': self.vf.Mols,
                    'vf': self.vf,
                    'all':1,
                    'crColor':(0.,1.,.2),
            },
            'gridcfg':{'sticky':'we', 'columnspan':2 }})
        ifd.append({'name':'limitTypes',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Limit acceptor types ',
                'variable': self.showATypeSel,
                'command':self.hideATypes
                },
            'gridcfg':{'sticky':'w', 'columnspan':2}})
        ifd.append({'name':'aO3',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'O3',
                'variable': self.aO3, },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'aS3',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'S3',
                'variable': self.aS3, },
            'gridcfg':{'sticky':'w','row':-1, 'column':1}})
        ifd.append({'name':'aO2',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'O2',
                'variable': self.aO2, },
            'gridcfg':{'sticky':'w','row':-1, 'column':2}})
        ifd.append({'name':'aO-',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'O-',
                'variable': self.aO,},
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'aNpl',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Npl',
                'variable': self.aNpl, },
            'gridcfg':{'sticky':'w', 'row':-1, 'column':1}})
        ifd.append({'name':'aNam',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Nam',
                'variable': self.aNam, },
            'gridcfg':{'sticky':'w','row':-1, 'column':2}})
        ifd.append({'name':'useSelCB',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'select from current selection',
                'variable': self.useSelection, },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Ok',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'ew', 'columnspan':2 },
            'command':self.Accept_cb})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Cancel',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'ew', 'column':2,'row':-1},
            'command':self.Close_cb})
        self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)
        self.hideDSelector()
        self.hideDTypes()
        self.hideASelector()
        self.hideATypes()


    def guiCallback(self):
        if not len(self.vf.Mols):
            self.warningMsg('no molecules in viewer')
            return 
        if not hasattr(self, 'ifd'):
            self.buildForm()


    def Close_cb(self, event=None):
        self.form.destroy()


    def Accept_cb(self, event=None):
        self.form.withdraw()
        dnodesToCheck = self.ifd.entryByName['keyDSelector']['widget'].get()
        if not len(dnodesToCheck):
            self.warningMsg('no donor atoms specified')
            dats = AtomSet([])
        else:
            dats = dnodesToCheck.findType(Atom)
            if self.useSelection.get():
                curSel = self.vf.getSelection()
                if len(curSel):
                    curAts = curSel.findType(Atom)
                    if curAts != self.vf.allAtoms:
                        dats = curAts.inter(dats)
                        if dats is None:
                            msg = 'no specified donor atoms in current selection'
                            self.warningMsg(msg)
                            dats = AtomSet([])
                else:
                    msg = 'no current selection'
                    self.warningMsg(msg)
                    dats = AtomSet([])
        donorList = []
        for n in allDonors:
            v = self.ifd.entryByName[n]['wcfg']['variable']
            if v.get():
                donorList.append(n)
        if not len(donorList):
            self.warningMsg('no donor types selected')
        ###FIX THIS!!!
        anodesToCheck = self.ifd.entryByName['keyASelector']['widget'].get()
        if not len(anodesToCheck):
            self.warningMsg('no acceptor atoms specified')
            acats = AtomSet([])
            #return
        else:
            acats = anodesToCheck.findType(Atom)
            if self.useSelection.get():
                curSel = self.vf.getSelection()
                if len(curSel):
                    curAts = curSel.findType(Atom)
                    if curAts != self.vf.allAtoms:
                        acats = curAts.inter(acats)
                        if not acats:  #NB inter returns empty set!
                            msg = 'no specified acceptor atoms in current selection'
                            self.warningMsg(msg)
                            acats = AtomSet([])
                else:
                    msg = 'no current selection'
                    self.warningMsg(msg)
                    acats = AtomSet([])
        acceptorList = []
        for n in allAcceptors: 
            name = 'a' + n 
            v = self.ifd.entryByName[name]['wcfg']['variable']
            if v.get():
                acceptorList.append(n)
        if not len(acceptorList):
            self.warningMsg('no acceptor types selected')
        if not (len(donorList) or len(acceptorList)):
            return
        self.Close_cb()
        return self.doitWrapper(dats, acats, donorList, acceptorList, topCommand=0)


    def hideDSelector(self, event=None):
        e = self.ifd.entryByName['keyDSelector']
        if self.hideDSel.get():
            e['widget'].grid_forget()
        else:
            e['widget'].grid(e['gridcfg'])
        self.form.autoSize() 


    def hideDTypes(self, event=None):
        for n in allDonors:
            e = self.ifd.entryByName[n]
            if not self.showDTypeSel.get():
                e['wcfg']['variable'].set(1)
                e['widget'].grid_forget()
            else:
                e['widget'].grid(e['gridcfg'])
        self.form.autoSize() 


    def hideASelector(self, event=None):
        e = self.ifd.entryByName['keyASelector']
        if self.hideASel.get():
            e['widget'].grid_forget()
        else:
            e['widget'].grid(e['gridcfg'])
        self.form.autoSize() 


    def hideATypes(self, event=None):
        for n in a_allAcceptors: 
            e = self.ifd.entryByName[n]
            if not self.showATypeSel.get():
                e['wcfg']['variable'].set(1)
                e['widget'].grid_forget()
            else:
                e['widget'].grid(e['gridcfg'])
        self.form.autoSize() 



ShowHBDonorsAcceptorsGuiDescr = {'widgetType':'Menu',
                                      'menuBarName':'menuRoot',
                                      'menuButtonName':'Hydrogen Bonds',
                                      'menuEntryLabel':'Show Donors + Acceptors',
                                      'menuCascadeName': 'Build'}


ShowHBDonorsAcceptorsGUI = CommandGUI()
ShowHBDonorsAcceptorsGUI.addMenuCommand('menuRoot','Hydrogen Bonds','Show Donors + Acceptors', cascadeName = 'Build')




class ShowHydrogenBonds(MVCommand):
    """This class allows user to visualize pre-existing HydrogenBonds between 
atoms in viewer
   \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : ShowHydrogenBonds
   \nCommand : showHBonds
   \nSynopsis:\n
    None <- showHBonds(nodes, **kw)
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly


    def onAddCmdToViewer(self):
        from DejaVu.IndexedPolylines import IndexedPolylines
        #from DejaVu.Labels import Labels
        miscGeom = self.vf.GUI.miscGeom
        hbond_geoms = check_hbond_geoms(self.vf.GUI)
        self.masterGeom = Geom('HbondsAsLinesGeoms',shape=(0,0), 
                                pickable=0, protected=True)
        self.masterGeom.isScalable = 0
        self.vf.GUI.VIEWER.AddObject(self.masterGeom, parent=hbond_geoms)
        self.lines = IndexedPolylines('showHbondLines', 
                    materials = ((0,1,0),), lineWidth=4, 
                    stippleLines=1, inheritMaterial=0, protected=True)
        self.labels = GlfLabels(name='showHbondLabs', shape=(0,3),
                            materials = ((0,1,1),), inheritMaterial=0,
                            billboard=True, fontStyle='solid',
                            fontScales=(.3,.3,.3,)) 
        self.labels.font = 'arial1.glf'
        self.thetaLabs = GlfLabels(name='hbondThetaLabs', shape=(0,3),
                            materials = ((1,1,0),), inheritMaterial=0,
                            billboard=True, fontStyle='solid',
                            fontScales=(.3,.3,.3,)) 
        self.thetaLabs.font = 'arial1.glf'
        self.phiLabs = GlfLabels(name='hbondPhiLabs', shape=(0,3),
                            materials = ((1,.2,0),), inheritMaterial=0,
                            billboard=True, fontStyle='solid',
                            fontScales=(.3,.3,.3,)) 
        self.phiLabs.font = 'arial1.glf'
        self.engLabs = GlfLabels(name='hbondELabs', shape=(0,3),
                            materials = ((1,1,1),), inheritMaterial=0,
                            billboard=True, fontStyle='solid',
                            fontScales=(.3,.3,.3,)) 
        self.engLabs.font = 'arial1.glf'

        geoms = [self.lines, self.labels, self.thetaLabs,
                        self.phiLabs, self.engLabs]
        for item in geoms:
            self.vf.GUI.VIEWER.AddObject(item, parent=self.masterGeom)

        self.vf.loadModule('labelCommands', 'Pmv', log=0)
        self.showAll = Tkinter.IntVar()
        self.showAll.set(1)
        self.showDistLabels = Tkinter.IntVar()
        self.showDistLabels.set(1)
        self.dispTheta = Tkinter.IntVar()
        self.dispTheta.set(0)
        self.dispPhi = Tkinter.IntVar()
        self.dispPhi.set(0)
        self.dispEnergy = Tkinter.IntVar()
        self.dispEnergy.set(0)
        self.dverts = []
        self.dlabs = []
        self.angVerts = []
        self.phi_labs = []
        self.theta_labs = []
        self.e_labs = []
        self.hasDist = 0
        self.hasAngles = 0
        self.hasEnergies = 0
        self.height = None
        self.width = None
        self.winfo_x = None
        self.winfo_y = None


    def __call__(self, nodes, **kw):
        """None <- showHBonds(nodes, **kw) """
        if type(nodes) is StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes =self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        ats = nodes.findType(Atom)
        apply(self.doitWrapper, (ats,), kw)


    def reset(self):
        self.hasAngles = 0
        self.hasEnergies = 0
        self.hasDist = 0
        self.lines.Set(vertices=[], tagModified=False)
        self.labels.Set(vertices=[], tagModified=False)
        self.engLabs.Set(vertices=[], tagModified=False)
        self.dverts = []
        self.dlabs = []
        self.angVerts = []
        self.phi_labs = []
        self.theta_labs = []
        self.e_labs = []


    def doit(self, ats):
        #asLines: ShowHBonds
        hbats = AtomSet(ats.get(lambda x: hasattr(x, 'hbonds')))
        self.reset()
        if not hbats:
            self.warningMsg('1:no hydrogen bonds found')
            return 'ERROR'
        hats = AtomSet(hbats.get(lambda x: x.element=='H'))
        atNames = []
        if hats:
            for h in hats:
                atNames.append((h.full_name(), None))
        else:
            hats = AtomSet([])
            bnds = []
            for at in hbats:
                bnds.extend(at.hbonds)
            bndD = {}
            for b in bnds:
                bndD[b] = 0
            hbnds2 = bndD.keys()
            hbnds2.sort()
            for b in hbnds2:
                atNames.append((b.donAt.full_name(), None))
                hats.append(b.donAt)
        self.showAllHBonds(hats)
        if not hasattr(self, 'ifd'):
            ifd = self.ifd=InputFormDescr(title = 'Hydrogen Bonds:')
            ifd.append({'name': 'hbondLabel',
                'widgetType': Tkinter.Label,
                'wcfg':{'text': str(len(atNames)) + ' Atoms in hbonds:'},
                'gridcfg':{'sticky': 'we', 'columnspan':2}})
            ifd.append({'name': 'atsLC',
                'widgetType':ListChooser,
                'wcfg':{
                    'entries': atNames,
                    'mode': 'single',
                    'title': '',
                    'command': CallBackFunction(self.showHBondLC, atNames),
                    'lbwcfg':{'height':5, 
                        'selectforeground': 'red',
                        'exportselection': 0,
                        'width': 30},
                },
                'gridcfg':{'sticky':'we', 'weight':2,'row':2,
                        'column':0, 'columnspan':2}})
            ifd.append({'name':'showAllBut',
                'widgetType':Tkinter.Checkbutton,
                'wcfg': { 'text':'Show All ',
                    'variable': self.showAll,
                    'command': CallBackFunction(self.showAllHBonds, \
                           hats)},
                'gridcfg':{'sticky':'we','weight':2}})
            ifd.append({'name':'showDistBut',
                'widgetType':Tkinter.Checkbutton,
                'wcfg': { 'text':'Show Distances ',
                    'variable': self.showDistLabels,
                    'command': self.showDistances},
                'gridcfg':{'sticky':'we', 'row':-1, 'column':1,'weight':2}})
            ifd.append({'name':'showThetaBut',
                'widgetType':Tkinter.Checkbutton,
                'wcfg': { 'text':'Show theta\n(don-h->acc)',
                    'variable': self.dispTheta,
                    'command': CallBackFunction(self.showAngles, hats)},
                'gridcfg':{'sticky':'we','weight':2}})
            ifd.append({'name':'showPhiBut',
                'widgetType':Tkinter.Checkbutton,
                'wcfg': { 'text':'Show phi\n(h->acc-accN)',
                    'variable': self.dispPhi,
                    'command': CallBackFunction(self.showAngles, hats)},
                'gridcfg':{'sticky':'we', 'row':-1, 'column':1,'weight':2}})
            ifd.append({'name':'showEnBut',
                'widgetType':Tkinter.Checkbutton,
                'wcfg': { 'text':'Show Energy',
                    'variable': self.dispEnergy,
                    'command': CallBackFunction(self.showEnergies, hats)},
                'gridcfg':{'sticky':'we','weight':2}})
            ifd.append({'name':'selAllBut',
                'widgetType':Tkinter.Button,
                'wcfg': { 'text':'Select All ',
                    'command': CallBackFunction(self.selAllHBonds, hats)},
                'gridcfg':{'sticky':'we','weight':2}})
            ifd.append({'name':'closeBut',
                'widgetType':Tkinter.Button,
                'wcfg': { 'text':'Dismiss',
                    'command': self.dismiss_cb},
                'gridcfg':{'sticky':'we', 'row':-1, 'column':1,'weight':2}})
            self.form  = self.vf.getUserInput(ifd, modal=0, blocking=0,
                     width=350, height=350)
            self.form.root.protocol('WM_DELETE_WINDOW',self.dismiss_cb)
            self.toplevel = self.form.f.master.master
            self.toplevel.positionfrom(who='user')
            if self.winfo_x is not None and self.winfo_y is not None:
                geom = self.width +'x'+ self.height +'+'
                geom += self.winfo_x + '+' + self.winfo_y
                self.toplevel.geometry(newGeometry=geom)

        else:
            self.ifd.entryByName['showAllBut']['widget'].config(command= \
                                     CallBackFunction(self.showAllHBonds, hats))
            self.ifd.entryByName['showThetaBut']['widget'].config(command= \
                                     CallBackFunction(self.showAngles, hats))
            self.ifd.entryByName['showPhiBut']['widget'].config(command= \
                                     CallBackFunction(self.showAngles, hats))
            self.ifd.entryByName['showEnBut']['widget'].config(command= \
                                     CallBackFunction(self.showEnergies, hats))
            self.ifd.entryByName['selAllBut']['widget'].config(command= \
                                     CallBackFunction(self.selAllHBonds, hats))
            if self.winfo_x is not None and self.winfo_y is not None:
                geom = self.width +'x'+ self.height +'+'
                geom += self.winfo_x + '+' + self.winfo_y
                self.toplevel.geometry(newGeometry=geom)


    def showHBondLC(self, hats, event=None):
        #this caused infinite loop:
        if not hasattr(self, 'ifd'):
            self.doit(hats)
        lb = self.ifd.entryByName['atsLC']['widget'].lb
        if lb.curselection() == (): return
        self.showAll.set(0)
        atName = lb.get(lb.curselection())
        ind = int(lb.curselection()[0])
        ats = self.vf.Mols.NodesFromName(atName)
        at = ats[0]
        #to deal with two atoms with the exact same name:
        if len(ats)>1:
            for a in ats:
                if hasattr(a, 'hbonds'):
                    at = a
                    break
        b = at.hbonds[0]
        faces = ((0,1),)
        if b.hAt is not None:
            lineVerts = (getTransformedCoords(b.hAt).tolist(), getTransformedCoords(b.accAt).tolist())
            #lineVerts = (b.hAt.coords, b.accAt.coords)
        else:
            lineVerts = (getTransformedCoords(b.donAt).tolist(), getTransformedCoords(b.accAt).tolist())
            #lineVerts = (b.donAt.coords, b.accAt.coords)
            faces = ((0,1),)
        if self.hasAngles:
            verts = [self.angVerts[ind]]
            labs = [self.theta_labs[ind]]
            self.thetaLabs.Set(vertices=verts, labels=labs, tagModified=False)
            labs = [self.phi_labs[ind]]
            self.phiLabs.Set(vertices=verts, labels=labs, tagModified=False)
        if self.hasEnergies:
            labs = [self.e_labs[ind]]
            verts = [self.dverts[ind]]
            self.engLabs.Set(vertices=verts,labels=labs,\
                    visible=self.dispEnergy.get(), tagModified=False)
        labelVerts = [self.dverts[ind]]
        labelStrs = [self.dlabs[ind]]
        self.labels.Set(vertices=labelVerts, labels=labelStrs,
                        tagModified=False)
        self.lines.Set(vertices=lineVerts, type=GL.GL_LINE_STRIP,
                           faces=faces, freshape=1, tagModified=False)
        self.vf.GUI.VIEWER.Redraw()


    def dismiss_cb(self, event=None, **kw):
        #showHBonds
        self.lines.Set(vertices=[], tagModified=False)
        self.labels.Set(vertices=[], tagModified=False)
        self.thetaLabs.Set(vertices=[], tagModified=False)
        self.phiLabs.Set(vertices=[], tagModified=False)
        self.engLabs.Set(vertices=[], tagModified=False)
        try:
            self.width = str(self.form.f.master.master.winfo_width())
            self.height = str(self.form.f.master.master.winfo_height())
            self.winfo_x = str(self.form.f.master.master.winfo_x())
            self.winfo_y = str(self.form.f.master.master.winfo_y())
        except:
            pass
        self.vf.GUI.VIEWER.Redraw()
        if hasattr(self, 'ifd'):
            delattr(self, 'ifd')
        if hasattr(self, 'form'):
            self.form.destroy()
        if hasattr(self, 'palette'):
            self.palette.hide()


    def showDistances(self, event=None):
        self.labels.Set(visible=self.showDistLabels.get(), tagModified=False)
        self.vf.GUI.VIEWER.Redraw()


    def showEnergies(self, hats):
        if not self.hasEnergies:
            self.buildEnergies(hats)
            self.hasEnergies = 1
        if not self.showAll.get():
            self.showHBondLC(hats)
        else:
            self.engLabs.Set(labels = self.e_labs, vertices = self.dverts,
                visible=self.dispEnergy.get(), tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        

    def buildEnergies(self, hats):
        #FIX THIS: for some reason, eList is disordered...???
        eList = self.vf.getHBondEnergies(hats, topCommand=0)
        for hat in hats:
            self.e_labs.append(str(hat.hbonds[0].energy))


    def showAngles(self, hats, event=None):
        if not self.hasAngles:
            self.buildAngles(hats)
            self.hasAngles = 1
        if not self.showAll.get():
            self.showHBondLC(hats)
        else:
            self.thetaLabs.Set(vertices=self.angVerts, labels=self.theta_labs,
                               tagModified=False)
            self.phiLabs.Set(vertices = self.angVerts, labels = self.phi_labs,
                             tagModified=False)
        self.thetaLabs.Set(visible=self.dispTheta.get(), tagModified=False)
        self.phiLabs.Set(visible=self.dispPhi.get(), tagModified=False)
        self.vf.GUI.VIEWER.Redraw()


    def buildAngles(self, hats):
        #NB: hats are either donAts or hAts
        # theta is don-h->acc, phi is h->acc-accN
        # calc 1 angle for each closeAt
        # hat is h, 
        if self.hasAngles: return
        tlabs = []
        plabs = []
        verts = []
        for hat in hats:
            b = hat.hbonds[0]
            accAt = b.accAt
            donAt = b.donAt
            if b.hAt is not None:
                ang = getAngle(donAt, hat, accAt)
                ang = round(ang, 3)
                b.theta = ang
                b0 = accAt.bonds[0]
                accN = b0.atom1
                if id(accN)==id(accAt): accN = b0.atom2
                #accN = b.accAt.bonds[0].neighborAtom(b.accAt)
                ang = getAngle(hat, accAt, accN)
                ang = round(ang, 3)
                b.phi = ang
            p1=Numeric.array(getTransformedCoords(hat))
            p2=Numeric.array(getTransformedCoords(accAt))
            #p1=Numeric.array(hat.coords)
            #p2=Numeric.array(accAt.coords)
            newVert = tuple((p1+p2)/2.0 + .2)
            tlabs.append(str(b.theta))
            verts.append(newVert)
            plabs.append(str(b.phi))
            self.thetaLabs.Set(vertices=verts, labels=tlabs, tagModified=False)
            self.angVerts = verts
            self.theta_labs = tlabs
            self.phi_labs = plabs
            self.phiLabs.Set(vertices=verts, labels=plabs, tagModified=False)
               

    def setupDisplay(self):
        #draw lines between hAts OR donAts and accAts
        self.labels.Set(vertices=self.dverts, labels=self.dlabs,
                        tagModified=False)
        self.lines.Set(vertices=self.lineVerts, type=GL.GL_LINE_STRIP,
                       faces=self.faces, freshape=1, tagModified=False)
        if self.hasAngles:
            self.thetaLabs.Set(vertices=self.angVerts, labels=self.theta_labs,
                               tagModified=False)
            self.phiLabs.Set(vertices=self.angVerts, labels=self.theta_labs,
                             tagModified=False)

        if self.hasEnergies:
            self.engLabs.Set(vertices=self.dverts, labels=self.e_labs,
                             tagModified=False)

        self.vf.GUI.VIEWER.Redraw()


    def showAllHBonds(self, hats, event=None):
        if not self.showAll.get() and hasattr(self, 'ifd'):
            self.showHBondLC(hats)
        elif not self.hasDist:
            lineVerts = []
            faces = []
            labelVerts = []
            labelStrs = []
            dlabelStrs = []
            atCtr = 0
            for at in hats:
                for b in at.hbonds:
                    dCoords = getTransformedCoords(b.donAt)
                    aCoords = getTransformedCoords(b.accAt)
                    if b.hAt is not None:
                        hCoords = getTransformedCoords(b.hAt)
                        lineVerts.append(hCoords)
                    else:
                        lineVerts.append(dCoords)
                    lineVerts.append(aCoords)
                    #lineVerts.append(b.accAt.coords)
                    faces.append((atCtr, atCtr+1))
                    #c1 = Numeric.array(at.coords, 'f')
                    c1 = getTransformedCoords(at)
                    c3 = aCoords
                    #c3 = Numeric.array(b.accAt.coords, 'f')
                    labelVerts.append(tuple((c1 + c3)/2.0))
                    if b.hAt is not None:
                        if b.hlen is not None:
                            labelStrs.append(str(b.hlen))
                        else:
                            #d = dist(hCoords,aCoords)
                            #d=self.vf.measureDistance(b.hAt,b.accAt, topCommand=0)
                            b.hlen=round(dist(hCoords, aCoords),3)
                            labelStrs.append(str(b.hlen))
                    if b.dlen is not None:
                        dlabelStrs.append(str(b.dlen))
                    else:
                        #d = dist(dCoords, aCoords)
                        ##d = dist(b.donAt.coords, b.accAt.coords)
                        #d=self.vf.measureDistance(b.donAt,b.accAt, topCommand=0)
                        #b.dlen=round(d,3)
                        b.dlen=round(dist(dCoords, aCoords) ,3)
                        dlabelStrs.append(str(b.dlen))
                    atCtr = atCtr + 2
            self.lineVerts = lineVerts
            self.faces = faces
            self.dverts = labelVerts
            if len(labelStrs):
                self.dlabs = labelStrs
            else:
                self.dlabs = dlabelStrs
            self.hasDist = 1
            self.setupDisplay()
        else:
            self.setupDisplay()


    def selAllHBonds(self, hats, event=None):
        self.vf.select(hats)
                

    def guiCallback(self):
        #showHbonds
        if not len(self.vf.Mols):
            self.warningMsg('no molecules in viewer')
            return 
        sel =  self.vf.getSelection()
        #put a selector here
        if len(sel):
            ats = sel.findType(Atom)
            apply(self.doitWrapper, (ats,), {})


ShowHydrogenBondsGuiDescr = {'widgetType':'Menu',
                                          'menuBarName':'menuRoot',
                                          'menuButtonName':'Hydrogen Bonds',
                                          'menuEntryLabel':'As Lines',
                                          'menuCascadeName': 'Display'}


ShowHydrogenBondsGUI = CommandGUI()
ShowHydrogenBondsGUI.addMenuCommand('menuRoot', 'Hydrogen Bonds',
        'As Lines', cascadeName='Display')



class BuildHydrogenBondsGUICommand(MVCommand):
    """This class provides Graphical User Interface to BuildHydrogenBonds which is invoked by it.
    \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : BuildHydrogenBondsGUICommand
   \nCommand : buildHydrogenBondsGC
   \nSynopsis:\n
        None<---buildHydrogenBondsGC(nodes1, nodes2, paramDict, reset=1)
    """
    

    def onAddCmdToViewer(self):
        self.showSel = Tkinter.IntVar()
        self.resetVar = Tkinter.IntVar()
        self.resetVar.set(1)
        self.showDef = Tkinter.IntVar()
        self.distOnly = Tkinter.IntVar()
        self.hideDTypeSel = Tkinter.IntVar()
        self.hideATypeSel = Tkinter.IntVar()
        self.showTypes = Tkinter.IntVar()
        varNames = ['hideDSel',  'N3', 'O3','S3','Nam', 'Ng', 'Npl',\
                'hideASel',  'aS3', 'aO3', 'aO2', 'aO', 'aNpl',
                'aNam']
        for n in varNames:
            exec('self.'+n+'=Tkinter.IntVar()')
            exec('self.'+n+'.set(1)')



    def doit(self, nodes1, nodes2, paramDict, reset=1):
        #buildHbondGC
        self.hasAngles = 0
        atDict = self.vf.buildHBonds(nodes1, nodes2, paramDict, reset)
        if not len(atDict.keys()):
            self.warningMsg('3:no hydrogen bonds found')
            return 'ERROR'
        else:
            msg = str(len(atDict.keys()))+' hydrogen bonds formed'
            self.warningMsg(msg)
            
        #ats = AtomSet(atDict.keys())
        #ats.parent.sort()
        #self.vf.showHBonds(ats)


    def guiCallback(self):
        if not len(self.vf.Mols):
            self.warningMsg('no molecules in viewer')
            return 
        if not hasattr(self, 'ifd'):
            self.buildForm()
        else:
            self.form.deiconify()


    def buildForm(self):
        ifd = self.ifd = InputFormDescr(title = "Select nodes + change parameters(optional):")
        ifd.append({'name':'keyLab',
                    'widgetType':Tkinter.Label,
                    'text':'For Hydrogen Bond detection:',
                    'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'selRB0',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'Use all atoms',
                'variable': self.showSel,
                'value':0,
                'command':self.hideSelector
                },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'selRB1',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'Specify two sets:',
                'variable': self.showSel,
                'value':1,
                'command':self.hideSelector
                },
            'gridcfg':{'sticky':'w', 'row':-1, 'column':1}})
        ifd.append({'name': 'group1',
            'wtype':StringSelectorGUI,
            'widgetType':StringSelectorGUI,
            'wcfg':{ 'molSet': self.vf.Mols,
                    'vf': self.vf,
                    'all':1,
                    'crColor':(0.,1.,.2),
            },
            'gridcfg':{'sticky':'we', 'columnspan':2 }})
        ifd.append({'name': 'group2',
            'wtype':StringSelectorGUI,
            'widgetType':StringSelectorGUI,
            'wcfg':{ 'molSet': self.vf.Mols,
                    'vf': self.vf,
                    'all':1,
                    'crColor':(1.,2.,0.),
            },
            'gridcfg':{'sticky':'we', 'columnspan':2}})

        ifd.append({'name':'typeRB0',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'Use all donor-acceptorTypes',
                'variable': self.showTypes,
                'value':0,
                'command':self.hideTypeCBs,
                },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'selRB1',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'Limit types:',
                'variable': self.showTypes,
                'value':1,
                'command':self.hideTypeCBs
                },
            'gridcfg':{'sticky':'w', 'row':-1, 'column':1}})
        ifd.append({'name':'limitDTypes',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Limit donor types ',
                'variable': self.hideDTypeSel,
                'command':self.hideDTypes
                },
            'gridcfg':{'sticky':'w', 'columnspan':2}})
        ifd.append({'name':'N3+',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'N3+',
                'variable': self.N3, },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'O3',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'O3',
                'variable': self.O3, },
            'gridcfg':{'sticky':'w','row':-1, 'column':1}})
        ifd.append({'name':'S3',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'S3',
                'variable': self.S3, },
            'gridcfg':{'sticky':'w','row':-1, 'column':2}})
        ifd.append({'name':'Nam',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Nam',
                'variable': self.Nam, },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'Ng+',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Ng+',
                'variable': self.Ng, },
            'gridcfg':{'sticky':'w','row':-1, 'column':1}})
        ifd.append({'name':'Npl',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Npl',
                'variable': self.Npl, },
            'gridcfg':{'sticky':'w','row':-1, 'column':2}})

        #now the acceptors
        ifd.append({'name':'limitATypes',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Limit acceptor types ',
                'variable': self.hideATypeSel,
                'command':self.hideATypes
                },
            'gridcfg':{'sticky':'w', 'columnspan':2}})
        ifd.append({'name':'aO3',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'O3',
                'variable': self.aO3, },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'aS3',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'S3',
                'variable': self.aS3, },
            'gridcfg':{'sticky':'w','row':-1, 'column':1}})
        ifd.append({'name':'aO2',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'O2',
                'variable': self.aO2, },
            'gridcfg':{'sticky':'w','row':-1, 'column':2}})
        ifd.append({'name':'aO-',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'O-',
                'variable': self.aO,},
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'aNpl',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Npl',
                'variable': self.aNpl, },
            'gridcfg':{'sticky':'w', 'row':-1, 'column':1}})
        ifd.append({'name':'aNam',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Nam',
                'variable': self.aNam, },
            'gridcfg':{'sticky':'w','row':-1, 'column':2}})

        ifd.append({'name':'distOnly',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Use distance as only criteria',
                'variable': self.distOnly,
                },
            'gridcfg':{'sticky':'w', 'columnspan':2}})

        ifd.append({'name':'defRB0',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Adjust default hydrogen bond parameters',
                'variable': self.showDef,
                'command':self.hideDefaults
                },
            'gridcfg':{'sticky':'w', 'columnspan':2}})
        ifd.append({'name':'distCutoff',
                    'widgetType':ExtendedSliderWidget,
                    'wcfg':{'label': 'H-Acc Distance Cutoff',
                            'minval':1.5,'maxval':3.0 ,
                            'init':2.25,
                            'labelsCursorFormat':'%1.2f',
                            'sliderType':'float',
                            'entrywcfg':{'width':4},
                            'entrypackcfg':{'side':'right'}},
                     'gridcfg':{'columnspan':2,'sticky':'we'}})
        ifd.append({'name':'distCutoff2',
                    'widgetType':ExtendedSliderWidget,
                    'wcfg':{'label': 'Donor-Acc Distance Cutoff',
                            'minval':1.5,'maxval':5.0 ,
                            'init':3.00,
                            'labelsCursorFormat':'%1.2f',
                            'sliderType':'float',
                            'entrywcfg':{'width':4},
                            'entrypackcfg':{'side':'right'}},
                     'gridcfg':{'columnspan':2,'sticky':'we'}})
        #min+max theta values for sp2 and for sp3 donors:
        ifd.append({ 'name':'d2lab',
            'widgetType':Tkinter.Label,
            'wcfg':{ 'text': 'sp2 donor-hydrogen-acceptor angle limits:',
                'font':(ensureFontCase('helvetica'),12,'bold')},
            'gridcfg':{'sticky':'w', 'columnspan':2}})
        ifd.append({'name':'d2min',
            'wtype':ThumbWheel,
            'widgetType':ThumbWheel,
            'wcfg':{ 'labCfg':{'text':'min', 
                        'font':(ensureFontCase('helvetica'),12,'bold')},
                'showLabel':2, 'width':100,
                'min':100, 'max':180, 'type':float, 'precision':3,
                'value':120,
                'showLabel':1,
                'continuous':1, 'oneTurn':2, 'wheelPad':2, 'height':20},
            'gridcfg':{'sticky':'we'}})
        #modified this 10/1 because of 1crn:ILE35NH to THR1:O hbond
        ifd.append({'name':'d2max',
            'wtype':ThumbWheel,
            'widgetType':ThumbWheel,
            'wcfg':{ 'labCfg':{'text':'max', 
                        'font':(ensureFontCase('helvetica'),12,'bold')},
                'showLabel':2, 'width':100,
                'min':100, 'max':190, 'type':float, 'precision':3,
                'value':180,
                'showLabel':1,
                'continuous':1, 'oneTurn':2, 'wheelPad':2, 'height':20},
            'gridcfg':{'sticky':'we', 'row':-1, 'column':1}})
        ifd.append({ 'name':'d3lab',
            'widgetType':Tkinter.Label,
           'wcfg':{ 'text': 'sp3 donor-hydrogen-acceptor angle limits:',
                'font':(ensureFontCase('helvetica'),12,'bold')},
            'gridcfg':{'sticky':'w', 'columnspan':2}})
        ifd.append({'name':'d3min',
            'wtype':ThumbWheel,
            'widgetType':ThumbWheel,
            'wcfg':{ 'labCfg':{'text':'min', 
                        'font':(ensureFontCase('helvetica'),12,'bold')},
                'showLabel':2, 'width':100,
                'min':100, 'max':180, 'type':float, 'precision':3,
                'value':120,
                'showLabel':1,
                'continuous':1, 'oneTurn':2, 'wheelPad':2, 'height':20},
            'gridcfg':{'sticky':'we'}})
        ifd.append({'name':'d3max',
            'wtype':ThumbWheel,
            'widgetType':ThumbWheel,
            'wcfg':{ 'labCfg':{'text':'max', 
                        'font':(ensureFontCase('helvetica'),12,'bold')},
                'showLabel':2, 'width':100,
                'min':100, 'max':180, 'type':float, 'precision':3,
                'value':180,
                'showLabel':1,
                'continuous':1, 'oneTurn':2, 'wheelPad':2, 'height':20},
            'gridcfg':{'sticky':'we', 'row':-1, 'column':1}})
        #min+max phi values for sp2 and for sp3 donors:
        ifd.append({ 'name':'a2lab',
            'widgetType':Tkinter.Label,
            'wcfg':{ 'text': 'sp2 donor-acceptor-acceptorN angle  limits:',
                'font':(ensureFontCase('helvetica'),12,'bold')},
            'gridcfg':{'sticky':'w', 'columnspan':2}})
        ifd.append({'name':'a2min',
            'wtype':ThumbWheel,
            'widgetType':ThumbWheel,
            'wcfg':{ 'labCfg':{'text':'min', 
                        'font':(ensureFontCase('helvetica'),12,'bold')},
                'showLabel':2, 'width':100,
                'min':90, 'max':180, 'type':float, 'precision':3,
                'value':110,
                'showLabel':1,
                'continuous':1, 'oneTurn':2, 'wheelPad':2, 'height':20},
            'gridcfg':{'sticky':'we'}})
        ifd.append({'name':'a2max',
            'wtype':ThumbWheel,
            'widgetType':ThumbWheel,
            'wcfg':{ 'labCfg':{'text':'max', 
                        'font':(ensureFontCase('helvetica'),12,'bold')},
                'showLabel':2, 'width':100,
                'min':100, 'max':180, 'type':float, 'precision':3,
                'value':150,
                'showLabel':1,
                'continuous':1, 'oneTurn':2, 'wheelPad':2, 'height':20},
            'gridcfg':{'sticky':'we', 'row':-1, 'column':1}})
        ifd.append({ 'name':'a3lab',
            'widgetType':Tkinter.Label,
            'wcfg':{ 'text': 'sp3 donor-acceptor-acceptorN angle limits:',
                'font':(ensureFontCase('helvetica'),12,'bold')},
            'gridcfg':{'sticky':'w', 'columnspan':2}})
        ifd.append({'name':'a3min',
            'wtype':ThumbWheel,
            'widgetType':ThumbWheel,
            'wcfg':{ 'labCfg':{'text':'min', 
                        'font':(ensureFontCase('helvetica'),12,'bold')},
                'showLabel':2, 'width':100,
                'min':90, 'max':180, 'type':float, 'precision':3,
                'value':100,
                'showLabel':1,
                'continuous':1, 'oneTurn':2, 'wheelPad':2, 'height':20},
            'gridcfg':{'sticky':'we'}})
        ifd.append({'name':'a3max',
            'wtype':ThumbWheel,
            'widgetType':ThumbWheel,
            'wcfg':{ 'labCfg':{'text':'max', 
                        'font':(ensureFontCase('helvetica'),12,'bold')},
                'showLabel':2, 'width':100,
                'min':100, 'max':180, 'type':float, 'precision':3,
                'value':150,
                'showLabel':1,
                'continuous':1, 'oneTurn':2, 'wheelPad':2, 'height':20},
            'gridcfg':{'sticky':'we', 'row':-1, 'column':1}})
        ifd.append({'name':'resetRB0',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'Remove all previous hbonds',
                'variable': self.resetVar,
                'value':1,
                },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'resetRB1',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'Add to previous hbonds',
                'variable': self.resetVar,
                'value':0,
                },
            'gridcfg':{'sticky':'w', 'row':-1, 'column':1}})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Ok',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we'},
            'command':self.Accept_cb})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Cancel',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we', 'column':1,'row':-1},
            'command':self.Close_cb})
        self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW',self.Close_cb)
        self.hideSelector()
        self.hideDefaults()
        self.hideDTypes()
        self.hideATypes()
        self.hideTypeCBs()
        self.form.autoSize()


    def cleanUpCrossSet(self):
        chL = []
        for item in self.vf.GUI.VIEWER.rootObject.children:
            if isinstance(item, CrossSet) and item.name[:8]=='strSelCr':
                chL.append(item)
        if len(chL):
            for item in chL: 
                item.Set(vertices=[], tagModified=False)
                self.vf.GUI.VIEWER.Redraw()
                self.vf.GUI.VIEWER.RemoveObject(item)


    def Close_cb(self, event=None):
        #self.cleanUpCrossSet()
        self.form.withdraw()
        #self.form.destroy()


    def hideTypeCBs(self, event=None):
        if not self.showTypes.get():
            for n in ['limitDTypes', 'limitATypes']:
                e = self.ifd.entryByName[n]
                e['widget'].grid_forget()
            self.hideDTypeSel.set(0)
            self.hideDTypes()
            self.hideATypeSel.set(0)
            self.hideATypes()
            #reset all variables to 1 here
            varNames = ['N3', 'O3','S3','Nam', 'Ng', 'Npl',\
                 'aS3', 'aO3', 'aO2', 'aO', 'aNpl', 'aNam']
            for n in varNames:
                exec('self.'+n+'.set(1)')
        else:
            for n in ['limitDTypes', 'limitATypes']:
                e = self.ifd.entryByName[n]
                e['widget'].grid(e['gridcfg'])
        self.form.autoSize()


    def hideDTypes(self, event=None):
        for n in allDonors:
            e = self.ifd.entryByName[n]
            if not self.hideDTypeSel.get():
                e['widget'].grid_forget()
            else:
                e['widget'].grid(e['gridcfg'])
        self.form.autoSize()


    def hideASelector(self, event=None):
        e = self.ifd.entryByName['keyASelector']
        if self.hideASel.get():
            e['widget'].grid_forget()
        else:
            e['widget'].grid(e['gridcfg'])
        self.form.autoSize()


    def hideATypes(self, event=None):
        for n in a_allAcceptors: 
            e = self.ifd.entryByName[n]
            if not self.hideATypeSel.get():
                e['widget'].grid_forget()
            else:
                e['widget'].grid(e['gridcfg'])
        self.form.autoSize()


    def Accept_cb(self, event=None):
        self.form.withdraw()
        if self.showSel.get():
            nodesToCheck1 = self.ifd.entryByName['group1']['widget'].get()
            nodesToCheck2 = self.ifd.entryByName['group2']['widget'].get()
        else:
            # user didn't choose to specify two sets:
            nodesToCheck1 = nodesToCheck2 = self.vf.getSelection()
            #nodesToCheck2 = self.vf.getSelection()
        if not len(nodesToCheck1):
            self.warningMsg('no atoms in first set')
            return
        if not len(nodesToCheck2):
            self.warningMsg('no atoms in second set')
            return
        distCutoff = self.ifd.entryByName['distCutoff']['widget'].get()
        distCutoff2 = self.ifd.entryByName['distCutoff2']['widget'].get()
        d2min = self.ifd.entryByName['d2min']['widget'].get()
        d2max = self.ifd.entryByName['d2max']['widget'].get()
        d3min = self.ifd.entryByName['d3min']['widget'].get()
        d3max = self.ifd.entryByName['d3max']['widget'].get()

        a2min = self.ifd.entryByName['a2min']['widget'].get()
        a2max = self.ifd.entryByName['a2max']['widget'].get()
        a3min = self.ifd.entryByName['a3min']['widget'].get()
        a3max = self.ifd.entryByName['a3max']['widget'].get()
        if nodesToCheck1[0].__class__!=Atom:
            ats1 = nodesToCheck1.findType(Atom)
            nodesToCheck1 = ats1
        if not self.showSel.get():
            nodesToCheck2 = nodesToCheck1
        elif nodesToCheck2[0].__class__!=Atom:
            ats2 = nodesToCheck2.findType(Atom)
            nodesToCheck2 = ats2
        donorList = []
        for w in allDonors:
            if self.ifd.entryByName[w]['wcfg']['variable'].get():
                donorList.append(w)
        acceptorList = []
        for w in a_allAcceptors:
            if self.ifd.entryByName[w]['wcfg']['variable'].get():
                acceptorList.append(w[1:])
        self.Close_cb()
        paramDict = {}
        paramDict['distCutoff'] = distCutoff
        paramDict['distCutoff2'] = distCutoff2
        paramDict['d2min'] = d2min
        paramDict['d2max'] = d2max
        paramDict['d3min'] = d3min
        paramDict['d3max'] = d3max
        paramDict['a2min'] = a2min
        paramDict['a2max'] = a2max
        paramDict['a3min'] = a3min
        paramDict['a3max'] = a3max
        paramDict['distOnly'] = self.distOnly.get()
        paramDict['donorTypes'] = donorList
        paramDict['acceptorTypes'] = acceptorList
        if  len(donorList)==0 and len(acceptorList)==0:
            self.warningMsg('no donors or acceptors possible')
            return 'ERROR'
        #print 'donorList=', donorList
        #print 'acceptorList=', acceptorList
        return self.doitWrapper(nodesToCheck1, nodesToCheck2, 
            paramDict, reset=self.resetVar.get(), topCommand=0)


    def hideSelector(self, event=None):
        e = self.ifd.entryByName['group1']
        e2 = self.ifd.entryByName['group2']
        if not self.showSel.get():
            e['widget'].grid_forget()
            e2['widget'].grid_forget()
        else:
            e['widget'].grid(e['gridcfg'])
            e2['widget'].grid(e2['gridcfg'])
        self.form.autoSize() 


    def hideDefaults(self, event=None):
        e = self.ifd.entryByName['distCutoff']
        e2 = self.ifd.entryByName['distCutoff2']
        if not self.showDef.get():
            e['widget'].frame.grid_forget()
            e2['widget'].frame.grid_forget()
        else:
            e['widget'].frame.grid(e['gridcfg'])
            e2['widget'].frame.grid(e2['gridcfg'])
        wids =  ['d2lab', 'd2min', 'd2max', 'd3lab', 'd3min', 'd3max',
            'a2lab', 'a2min', 'a2max', 'a3lab', 'a3min', 'a3max']
        for item in wids:
            e = self.ifd.entryByName[item]
            if not self.showDef.get():
                e['widget'].grid_forget()
            else:
                e = self.ifd.entryByName[item]
                e['widget'].grid(e['gridcfg'])
        self.form.autoSize() 



BuildHydrogenBondsGUICommandGuiDescr = {'widgetType':'Menu',
                                          'menuBarName':'menuRoot',
                                          'menuButtonName':'Hydrogen Bonds',
                                          'menuEntryLabel':'Set Params + Build',
                                          'menuCascadeName':'Build'}


BuildHydrogenBondsGUICommandGUI = CommandGUI()
BuildHydrogenBondsGUICommandGUI.addMenuCommand('menuRoot', 'Hydrogen Bonds', 'Set Parms + Build', cascadeName = 'Build')



class BuildHydrogenBonds(MVCommand):
    """This command finds hydrogen donor atoms within 2.4*percentCutoff angstrom distance of hydrogen acceptor atoms. It builds and returns a dictionary atDict whose keys are hydrogen atoms (or hydrogenbond donor atoms if there are no hydrogens) and whose values are potential h-bond acceptors and distances to these atoms, respectively
    \nPackage : Pmv
    \nModule  : hbondCommands
    \nClass   : BuildHydrogenBonds 
    \nCommand : buildHbonds
    \nSynopsis:\n
        atDict <- buildHbonds(group1, group2, paramDict, **kw)
    \nRequired Arguments:\n       
        group1 ---  atoms\n 
        group2 --- atoms\n 
        paramDict --- a dictionary with these keys and default values\n
        keywords --\n
            distCutoff: 2.25  hydrogen--acceptor distance\n
            distCutoff2: 3.00 donor... acceptor distance\n
            d2min: 120 <min theta for sp2 hybridized donors>\n
            d2max: 180 <max theta for sp2 hybridized donors>\n
            d3min: 120 <min theta for sp3 hybridized donors>\n
            d3max: 170 <max theta for sp3 hybridized donors>\n

            a2min: 120 <min phi for sp2 hybridized donors>\n
            a2max: 150 <max phi for sp2 hybridized donors>\n
            a3min: 100 <min phi for sp3 hybridized donors>\n
            a3max: 150 <max phi for sp3 hybridized donors>\n
            donorTypes = allDonors\n
            acceptorTypes = allAcceptors\n
            reset: remove all previous hbonds\n
    """


    def onAddCmdToViewer(self):
        self.distSelector = DistanceSelector(return_dist=0)
        if not self.vf.commands.has_key('typeAtoms'):
            self.vf.loadCommand('editCommands', 'typeAtoms', 'Pmv',
                                topCommand=0)


    def reset(self):
        ct = 0
        for at in self.vf.allAtoms:
            if hasattr(at, 'hbonds'):
                for item in at.hbonds:
                    del item
                    ct = ct +1
                delattr(at, 'hbonds')
        #print 'reset: deleted  hbonds from ' + str(ct)+ ' atoms '


    def doit(self, group1, group2, paramDict, reset):
        hb = HydrogenBondBuilder()
        atDict = hb.build(group1, group2,reset=reset, paramDict=paramDict)
        return atDict
#        #buildHbonds
#        # two steps:
#        # group1 donors v group2 acceptors and group1 acceptors vs group2 donors
#        if reset: 
#            #delattr(group1, 'hbonds')
#            #delattr(group2, 'hbonds')
#            self.reset()
#        atDict = {}

#        dict1 = self.buildD(group1, paramDict)

#        if group1==group2:
#            atD1 =self.process(dict1, dict1, paramDict)
#            #print 'len(atD1).keys()=', len(atD1.keys())
#        else:
#            dict2 = self.buildD(group2, paramDict)
#            atD1 = self.process(dict1, dict2, paramDict)
#            atD2 = self.process(dict2, dict1, paramDict)
#            #print 'len(atD1).keys()=', len(atD1.keys())
#            #print 'len(atD2).keys()=', len(atD2.keys())

#        #if called with 1 atom could get tuple of two empty dictionaries
#        if type(atD1)==type(atDict):
#            atDict.update(atD1)
#            if group1!=group2 and type(atD2)==type(atDict):
#                atDict.update(atD2)

#        return atDict


#    def buildD(self, ats, paramDict):
#        d = {}
#        donorTypes = paramDict['donorTypes']
#        donor2Ats, donor3Ats = self.vf.getHBDonors(ats,
#                donorTypes, topCommand=0)
#        d23 = donor2Ats+donor3Ats
#        #hAts = ats.get(lambda x, d23=d23: x.element=='H' \
#                    #and x.bonds[0].neighborAtom(x) in d23)
#        hAts = AtomSet(ats.get(lambda x, donorTypes=donorTypes: x.element=='H' \
#                    and (x.bonds[0].atom1.babel_type in donorTypes\
#                    or x.bonds[0].atom2.babel_type in donorTypes)))
#        d['hAts'] = hAts
#        d['donor2Ats'] = donor2Ats
#        d['donor3Ats'] = donor3Ats

#        acceptor2Ats, acceptor3Ats = self.vf.getHBAcceptors(ats, 
#                    paramDict['acceptorTypes'], topCommand=0)
#        d['acceptor2Ats'] = acceptor2Ats
#        d['acceptor3Ats'] = acceptor3Ats
#        if acceptor2Ats:
#            acceptorAts = acceptor2Ats
#            if acceptor3Ats:
#                acceptorAts = acceptorAts + acceptor3Ats
#        elif acceptor3Ats:
#            acceptorAts = acceptor3Ats
#        else:
#            #CHECK THIS: should it be None or AtomSet([])
#            acceptorAts = None
#        d['acceptorAts'] = acceptorAts
#        return d
#            

#    def getMat(self, ats):
#        tops = ats.top.uniq()
#        if len(tops)>1: 
#            self.warningMsg('transformation mat=None:>1 mol in atomset!')
#            return None
#        g = tops[0].geomContainer.geoms['master']
#        return g.GetMatrix(g)

#    def process(self, dict1, dict2, paramDict):
#        #hAts are keys, aceptorAts are checks
#        hAts = dict1['hAts']
#        tAts = hAts
#        dist = paramDict['distCutoff']
#        distOnly = paramDict['distOnly']

#        if not hAts:
#            #then use donors and a different distance
#            tAts = dict1['donor2Ats'] + dict1['donor3Ats']
#            dist = paramDict['distCutoff2']
#            
#        acceptorAts = dict2['acceptorAts']
#        if not acceptorAts or not tAts: #6/14/2004
#            return {}, {}

#        #call distanceSelector on two groups of atoms with dist
#        keyMat = self.getMat(tAts)
#        checkMat = self.getMat(acceptorAts)
#        atDict = self.distSelector.select(tAts, acceptorAts, dist,
#            keyMat=keyMat, checkMat=checkMat)
#        #atDict = self.distSelector.select(tAts, acceptorAts, dist)
#        #first remove bonded angles
#        atDict = self.removeNeighbors(atDict)

#        donor2Ats = dict1['donor2Ats']
#        donor3Ats = dict1['donor3Ats']
#        acceptor2Ats = dict2['acceptor2Ats']
#        acceptor3Ats = dict2['acceptor3Ats']

#        if distOnly: 
#            #need to build hbonds and return dictionary
#            self.makeBonds(atDict, donor2Ats, donor3Ats, \
#                    acceptor2Ats, acceptor3Ats, paramDict)
#            return atDict

#        badAtDict = self.filterBasedOnAngs(atDict, donor2Ats, donor3Ats, \
#                    acceptor2Ats, acceptor3Ats, paramDict)
#        atDict = self.removeBadAts(atDict, badAtDict)
#        if atDict is None:
#            atDict = {}
#        return atDict


#    def makeBonds(self, pD, d2Ats, d3Ats, a2Ats, a3ats, paramDict):
#        for k in pD.keys():
#            if k.element=='H':
#                if hasattr(k, 'hbonds') and len(k.hbonds):
#                    continue
#                d = k.bonds[0].atom1
#                if id(d)==id(k): d = k.bonds[0].atom2
#                #d = k.bonds[0].neighborAtom(k)
#                h = k
#            else: 
#                d = k
#                h = None
#            #pD[k] is a list of close-enough ats
#            for ac in pD[k]:
#                if ac==d: continue
#                dSp2 = d in d2Ats
#                aSp2 = ac in a2Ats
#                if dSp2:
#                    if aSp2: typ = 22
#                    else: typ = 23
#                elif aSp2: typ = 32
#                else: typ = 33
#                #THEY could be already bonded
#                alreadyBonded = 0
#                if hasattr(d, 'hbonds') and hasattr(ac,'hbonds'):
#                    for hb in d.hbonds:
#                        if hb.donAt==ac or hb.accAt==ac:
#                            alreadyBonded = 1
#                            
#                if not alreadyBonded:
#                    newHB = HydrogenBond(d, ac, h, typ=typ)
#                    if not hasattr(ac, 'hbonds'):
#                        ac.hbonds=[]
#                    if not hasattr(d, 'hbonds'):
#                        d.hbonds=[]
#                    ac.hbonds.append(newHB)
#                    d.hbonds.append(newHB)
#                    if h is not None:
#                        #hydrogens can have only 1 hbond
#                        h.hbonds = [newHB]


#    def filterBasedOnAngs(self, pD, d2Ats, d3Ats, a2Ats, a3ats, paramDict):
#        badAtDict = {}
#        d2max = paramDict['d2max']
#        d2min = paramDict['d2min']
#        d3max = paramDict['d3max']
#        d3min = paramDict['d3min']
#        #NEED these parameters
#        a2max = paramDict['a2max']
#        a2min = paramDict['a2min']
#        a3max = paramDict['a3max']
#        a3min = paramDict['a3min']
#        #NB now pD keys could be hydrogens OR donors
#        for k in pD.keys():
#            if k.element=='H':
#                d = k.bonds[0].atom1
#                if id(d)==id(k): d = k.bonds[0].atom2
#                #d = k.bonds[0].neighborAtom(k)
#                h = k
#            else: 
#                d = k
#                h = None
#            badAts = AtomSet([])
#            ct = 0
#            for ac in pD[k]:
#                if h is not None:
#                    ang = getAngle(ac, h, d)
#                else:
#                    acN = ac.bonds[0].atom1
#                    if id(acN) == id(ac): acN = ac.bonds[0].atom2
#                    #acN = ac.bonds[0].neighborAtom(ac)
#                    ang = getAngle(d, ac, acN)
#                #print 'ang=', ang
#                dSp2 = d in d2Ats
#                aSp2 = ac in a2Ats
#                #these limits could be adjustable
#                if h is not None:
#                    if dSp2:
#                        upperLim = d2max
#                        lowerLim = d2min
#                        #upperLim = 170
#                        #lowerLim = 130
#                    else:
#                        upperLim = d3max
#                        lowerLim = d3min
#                        #upperLim = 180
#                        #lowerLim = 120
#                else:
#                    #if there is no hydrogen use d-ac-acN angles
#                    if dSp2:
#                        upperLim = a2max
#                        lowerLim = a2min
#                        #upperLim = 150
#                        #lowerLim = 110
#                    else:
#                        upperLim = a3max
#                        lowerLim = a3min
#                        #upperLim = 150
#                        #lowerLim = 100
#                if ang>lowerLim and ang <upperLim:
#                    #AT THIS MOMENT BUILD HYDROGEN BOND:
#                    if dSp2:
#                        if aSp2: typ = 22
#                        else: typ = 23
#                    elif aSp2: typ = 32
#                    else: typ = 33
#                    #THEY could be already bonded
#                    alreadyBonded = 0
#                    if hasattr(d, 'hbonds') and hasattr(ac,'hbonds'):
#                        for hb in d.hbonds:
#                            if hb.donAt==ac or hb.accAt==ac:
#                                alreadyBonded = 1
#                    if not alreadyBonded:
#                        newHB = HydrogenBond(d, ac, h, theta=ang, typ=typ)
#                        if not hasattr(ac, 'hbonds'):
#                            ac.hbonds=[]
#                        if not hasattr(d, 'hbonds'):
#                            d.hbonds=[]
#                        ac.hbonds.append(newHB)
#                        d.hbonds.append(newHB)
#                        if h is not None:
#                            #hydrogens can have only 1 hbond
#                            h.hbonds = [newHB]
#                        #    newHB.hlen = dist
#                        #else:
#                        #    newHB.dlen = dist
#                else:
#                    badAts.append(ac)
#                ct = ct + 1
#            badAtDict[k] = badAts
#        return badAtDict


#    def removeBadAts(self, atDict, badAtDict):
#        #clean-up function called after filtering on angles
#        badKeys= badAtDict.keys()
#        for at in atDict.keys():
#            if at not in badKeys:
#                continue
#            if not len(badAtDict[at]):
#                continue
#            closeAts = atDict[at]
#            badAts = badAtDict[at]
#            goodAts = []
#            for i in range(len(closeAts)):
#                cAt = closeAts[i]
#                if cAt not in badAts:
#                    goodAts.append(cAt)
#            if len(goodAts):
#                atDict[at] = goodAts
#            else:
#                del atDict[at]
#        return atDict


#    def removeNeighbors(self, atDict):
#        #filter out at-itself and at-bondedat up to 1:4
#        #NB keys could be hydrogens OR donors
#        for at in atDict.keys():
#            closeAts = atDict[at]
#            bondedAts = AtomSet([])
#            for b in at.bonds:
#                ###at2 = b.neighborAtom(at)
#                at2 = b.atom1
#                if id(at2)==id(at): at2 = b.atom2
#                bondedAts.append(at2)
#                #9/13 remove this:
#                ##also remove 1-3
#                for b2 in at2.bonds:
#                    at3 = b2.atom1
#                    if id(at3)==id(at2): at3 = b.atom2
#                    #at3 = b2.neighborAtom(at2)
#                    if id(at3)!=id(at):
#                        bondedAts.append(at3)
#                    #for b3 in at3.bonds:
#                        #at4 = b2.neighborAtom(at3)
#                        #if at4!=at and at4!=at2:
#                            #bondedAts.append(at4)
#            bondedAts = bondedAts.uniq()
#            goodAts = []
#            for i in range(len(closeAts)):
#                cAt = closeAts[i]
#                if cAt not in bondedAts:
#                    goodAts.append(cAt)
#            if len(goodAts):
#                atDict[at] = goodAts
#            else:
#                del atDict[at]
#        return atDict
#                    

#    def getDonors(self, nodes, paramDict):
#        donorList = paramDict['donorTypes']
#        print 'donorList=', donorList
#        # currently this is a set of hydrogens
#        hats = AtomSet(nodes.get(lambda x: x.element=='H'))
#        #hats are optional: if none, process donors
#        # if there are hats: dAts are all atoms bonded to all hydrogens
#        if hats:
#            dAts = AtomSet([])
#            for at in hats:
#                for b in at.bonds:
#                    at2 = b.atom1
#                    if id(at2)==id(at): at2 = b.atom2
#                    dAts.append(at2)
#                    #dAts.append(b.neighborAtom(at))
#        else:
#            dAts = nodes
#        #get the sp2 hybridized possible donors which are all ns
#        sp2 = []
#        for t in ['Nam', 'Ng+', 'Npl']:
#            if t in donorList:
#                sp2.append(t)
#        #ntypes = ['Nam', 'Ng+', 'Npl']

#        sp2DAts = None
#        if len(sp2):
#            sp2DAts = AtomSet(dAts.get(lambda x, sp2=sp2: x.babel_type in sp2))

#        hsp2 = AtomSet([])
#        if sp2DAts:
#            if hats:
#                hsp2 = AtomSet(hats.get(lambda x, sp2DAts=sp2DAts:x.bonds[0].atom1 \
#                        in sp2DAts or x.bonds[0].atom2 in sp2DAts))
#        if sp2DAts:
#            #remove any sp2 N atoms which already have 3 bonds not to hydrogens
#            n2Dons = AtomSet(sp2DAts.get(lambda x: x.element=='N'))
#            if n2Dons:
#                n2Dons.bl=0
#                for at in n2Dons:
#                    for b in at.bonds:
#                        if type(b.bondOrder)==type(2):
#                            at.bl = at.bl + b.bondOrder
#                        else:
#                            at.bl = at.bl + 2
#                        #allow that there might already be a hydrogen
#                    nH = at.findHydrogens()
#                    at.bl = at.bl - len(nH)
#                badAts = AtomSet(n2Dons.get(lambda x: x.bl>2))
#                if badAts:
#                    sp2DAts = sp2DAts - badAts
#                delattr(n2Dons,'bl')
#        #get the sp3 hybridized possible donors
#        sp3 = []
#        for t in ['N3+', 'S3', 'O3']:
#            if t in donorList:
#                sp3.append(t)
#        n3DAts = None
#        if 'N3+' in sp3:
#            n3DAts = AtomSet(dAts.get(lambda x: x.babel_type=='N3+'))
#        o3DAts = None
#        if 'O3' in sp3:
#            o3DAts = AtomSet(dAts.get(lambda x: x.babel_type=='O3'))
#        if o3DAts:
#            #remove any O3 atoms which already have 2 bonds not to hydrogens
#            badO3s = AtomSet([])
#            for at in o3DAts:
#                if len(at.bonds)<2: continue
#                if len(at.findHydrogens()): continue
#                else:
#                    badO3s.append(at)
#            if len(badO3s):
#                o3DAts = o3DAts - badO3s
#        s3DAts = None
#        if 'S3' in sp3:
#            s3DAts = AtomSet(dAts.get(lambda x: x.babel_type=='S3'))
#        sp3DAts = AtomSet([])
#        for item in [n3DAts, o3DAts, s3DAts]:
#            if item:
#                sp3DAts = sp3DAts + item
#        hsp3 = AtomSet([])
#        if sp3DAts:
#            if hats:
#                hsp3 = AtomSet(hats.get(lambda x, sp3DAts=sp3DAts:x.bonds[0].atom1 \
#                    in sp3DAts or x.bonds[0].atom2 in sp3DAts))
#        hsp = hsp2 + hsp3
#        #print 'hsp=', hsp.name
#        #print 'sp2DAts=', sp2DAts.name
#        #print 'sp3DAts=', sp3DAts.name
#        return hsp, sp2DAts, sp3DAts


#    def getAcceptors(self, nodes, paramDict):
#        acceptorList = paramDict['acceptorTypes']
#        print 'acceptorList=', acceptorList

#        sp2 = []
#        for t in ['Npl', 'Nam']:
#            if t in acceptorList: sp2.append(t)
#        n2Accs = None
#        if 'Npl' in sp2:
#            n2Accs = AtomSet(nodes.get(lambda x: x.babel_type=='Npl'))
#        if 'Nam' in sp2:
#            n2Accs2 = AtomSet(nodes.get(lambda x: x.babel_type=='Nam'))
#            if n2Accs2:
#                if n2Accs:
#                    n2Accs = n2Accs+n2Accs2
#                else:
#                    n2Accs = n2Accs2
#        if n2Accs is None: 
#            n2Accs = AtomSet([])

#        o_sp2 = []
#        for t in ['O2', 'O-']:
#            if t in acceptorList: sp2.append(t)

#        o2Accs = None
#        if 'O2' in o_sp2:
#            o2Accs = AtomSet(nodes.get(lambda x: x.babel_type=='O2'))
#        if 'O-' in sp2:
#            o2Accs2 = AtomSet(nodes.get(lambda x: x.babel_type=='O-'))
#            if o2Accs2:
#                if o2Accs:
#                    o2Accs = o2Accs+o2Accs2
#                else:
#                    o2Accs = o2Accs2
#        if o2Accs is None: 
#            o2Accs = AtomSet([])

#        
#        o3Accs = None
#        if 'O3' in acceptorList:
#            o3Accs = AtomSet(nodes.get(lambda x: x.babel_type=='O3'))
#        if o3Accs is None: o3Accs = AtomSet([])

#        s3Accs = None
#        if 'S3' in acceptorList:
#            s3Accs = AtomSet(nodes.get(lambda x: x.babel_type=='S3'))
#        if s3Accs is None: s3Accs = AtomSet([])

#        ret2Ats = AtomSet([])
#        for item in [n2Accs, o2Accs]:
#            ret2Ats = ret2Ats + item

#        ret3Ats = AtomSet([])
#        for item in [s3Accs, o3Accs]:
#            ret3Ats = ret3Ats + item
#        if ret2Ats: print 'ret2Ats=', ret2Ats.name
#        else: print 'no ret2Ats'
#        if ret3Ats: print 'ret3Ats=', ret3Ats.name
#        else: print 'no ret3Ats'
#        return ret2Ats, ret3Ats



    def __call__(self, group1, group2=None, paramDict={}, reset=1,  **kw):
        """atDict <--- buildHbonds(group1, group2, paramDict, **kw)
           \ngroup1 ---  atoms 
           \ngroup2 --- atoms 
           \nparamDict --- a dictionary with these keys and default values
           \nkeywprds ---\n
           \ndistCutoff: 2.25  hydrogen--acceptor distance
           \ndistCutoff2: 3.00 donor... acceptor distance
           \nd2min: 120 <min theta for sp2 hybridized donors>
           \nd2max: 180 <max theta for sp2 hybridized donors>
           \nd3min: 120 <min theta for sp3 hybridized donors>
           \nd3max: 170 <max theta for sp3 hybridized donors>

           \na2min: 120 <min phi for sp2 hybridized donors>
           \na2max: 150 <max phi for sp2 hybridized donors>
           \na3min: 100 <min phi for sp3 hybridized donors>
           \na3max: 150 <max phi for sp3 hybridized donors>
           \ndonorTypes = allDonors
           \nacceptorTypes = allAcceptors
           \nreset: remove all previous hbonds
           """
        group1 = self.vf.expandNodes(group1)
        if group2 is None:
            group2 = group1
        else:
            group2 = self.vf.expandNodes(group2)
        if not (len(group1) and len(group2)):
            return 'ERROR'
        #for item in [group1, group2]:
        if group1.__class__!=Atom:
                group1 = group1.findType(Atom)
        try:
            group1.babel_type
        except:
            tops = group1.top.uniq()
            for t in tops:
                t.buildBondsByDistance()
                self.vf.typeAtoms(t.allAtoms, topCommand=0)

        if group2.__class__!=Atom:
                group2 = group2.findType(Atom)
        try:
            group2.babel_type
        except:
            tops = group2.top.uniq()
            for t in tops:
                self.vf.typeAtoms(t.allAtoms, topCommand=0)
        if not paramDict.has_key('distCutoff'):
            paramDict['distCutoff'] = 2.25
        if not paramDict.has_key('distCutoff2'):
            paramDict['distCutoff2'] = 3.00
        if not paramDict.has_key('d2min'):
            paramDict['d2min'] = 120.
        if not paramDict.has_key('d2max'):
            paramDict['d2max'] = 180.
        if not paramDict.has_key('d3min'):
            paramDict['d3min'] = 120.
        if not paramDict.has_key('d3max'):
            paramDict['d3max'] = 170.

        if not paramDict.has_key('a2min'):
            paramDict['a2min'] = 130.
        if not paramDict.has_key('a2max'):
            paramDict['a2max'] = 170.
        if not paramDict.has_key('a3min'):
            paramDict['a3min'] = 120.
        if not paramDict.has_key('a3max'):
            paramDict['a3max'] = 170.
        if not paramDict.has_key('distOnly'):
            paramDict['distOnly'] = 0
        if not paramDict.has_key('donorTypes'):
            paramDict['donorTypes'] = allDonors
        if not paramDict.has_key('acceptorTypes'):
            paramDict['acceptorTypes'] = allAcceptors
        return apply( self.doitWrapper, (group1, group2, paramDict, reset), kw)






class AddHBondHydrogensGUICommand(MVCommand):
    """This class provides Graphical User Interface to AddHBondHydrogens
which is invoked by it.
   \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : AddHBondHydrogensGUICommand
   \nCommand : addHBondHsGC
   \nSynopsis:\n
        None<---addHBondHsGC(nodes)
    """
    

    def onAddCmdToViewer(self):
        self.showSel = Tkinter.IntVar()
        self.showSel.set(0)


    def doit(self, nodes):
        #addhydrogens to hbonds GC
        self.hasAngles = 0
        newHs = self.vf.addHBondHs(nodes)
        #print 'newHs=', newHs
        if not len(newHs):
            self.warningMsg('no hbonds found missing hydrogens')
            return 'ERROR'
        else:
            msg = str(len(newHs)) + ' hydrogens added to hbonds'
            self.warningMsg(msg)


    def guiCallback(self):
        if not len(self.vf.Mols):
            self.warningMsg('no molecules in viewer')
            return 
        ifd = self.ifd = InputFormDescr(title = "Select nodes + change parameters(optional):")
        ifd.append({'name':'keyLab',
                    'widgetType':Tkinter.Label,
                    'text':'Add missing hydrogens to hbonds for:',
                    'gridcfg':{'sticky':Tkinter.W, 'columnspan':2}})
        ifd.append({'name':'selRB0',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'all atoms',
                'variable': self.showSel,
                'value':0,
                'command':self.hideSelector
                },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'selRB1',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'a subset of atoms ',
                'variable': self.showSel,
                'value':1,
                'command':self.hideSelector
                },
            'gridcfg':{'sticky':'w', 'row':-1, 'column':1}})
        ifd.append({'name': 'keySelector',
            'wtype':StringSelectorGUI,
            'widgetType':StringSelectorGUI,
            'wcfg':{ 'molSet': self.vf.Mols,
                    'vf': self.vf,
                    'all':1,
                    'crColor':(0.,1.,.2),
            },
            'gridcfg':{'sticky':'we', 'columnspan':2 }})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Ok',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':Tkinter.E+Tkinter.W},
            'command':self.Accept_cb})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Cancel',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':Tkinter.E+Tkinter.W, 'column':1,'row':-1},
            'command':self.Close_cb})
        self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW',self.Close_cb)
        self.hideSelector()


    def cleanUpCrossSet(self):
        chL = []
        for item in self.vf.GUI.VIEWER.rootObject.children:
            if isinstance(item, CrossSet) and item.name[:8]=='strSelCr':
                chL.append(item)
        if len(chL):
            for item in chL: 
                item.Set(vertices=[], tagModified=False)
                self.vf.GUI.VIEWER.Redraw()
                self.vf.GUI.VIEWER.RemoveObject(item)


    def Close_cb(self, event=None):
        self.cleanUpCrossSet()
        self.form.destroy()


    def Accept_cb(self, event=None):
        self.form.withdraw()
        nodesToCheck = self.ifd.entryByName['keySelector']['widget'].get()
        if not len(nodesToCheck):
            self.warningMsg('no atoms specified')
            return
        if nodesToCheck[0].__class__!='Atom':
            ats = nodesToCheck.findType(Atom)
            nodesToCheck = AtomSet(ats.get(lambda x: hasattr(x, 'hbonds')))
        self.Close_cb()
        if not nodesToCheck:
            self.warningMsg('no hbonds present in specified atoms')
            return
        else:
            return self.doitWrapper(ats, topCommand=0)


    def hideSelector(self, event=None):
        e = self.ifd.entryByName['keySelector']
        if not self.showSel.get():
            e['widget'].grid_forget()
        else:
            e['widget'].grid(e['gridcfg'])
        self.form.autoSize() 



AddHBondHydrogensGUICommandGuiDescr = {'widgetType':'Menu',
                                          'menuBarName':'menuRoot',
                                          'menuButtonName':'Hydrogen Bonds',
                                          'menuEntryLabel':'Add Hydrogens to Hbonds',
                                          'menuCascadeName':'Build'}


AddHBondHydrogensGUICommandGUI = CommandGUI()
AddHBondHydrogensGUICommandGUI.addMenuCommand('menuRoot', 'Hydrogen Bonds', 'Add Hydrogens to Hbonds', cascadeName='Build')



class AddHBondHydrogens(MVCommand):
    """This command adds hydrogen atoms to preexisting hydrogen bonds
    \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : AddHBondHydrogens
   \nCommand : addHBondHs
   \nSynopsis:\n
    newHs <- addHBondHs(nodes, **kw):
   \nRequired Arguments:\n        
            nodes --- atoms \n
            newHs are new atoms, added to hbond.donAt\n
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('typeAtoms'):
            self.vf.loadCommand('editCommands', 'typeAtoms', 'Pmv',
                                topCommand=0)


    def dist(self, c1, c2):
        c1 = Numeric.array(c1)
        c2 = Numeric.array(c2)
        d = c2 - c1
        return math.sqrt(Numeric.sum(d*d))


    def chooseH(self, at, accAt):
        #do this for sp2 nitrogens with 1 bond
        c2 = at.bonds[0].neighborAtom(at)
        c3 = None
        c4 = None
        for b in c2.bonds:
            if b.neighborAtom(c2)==at:
                continue
            elif c3 is None:
                c3 = b.neighborAtom(c2)
            elif c4 is None:
                c4 = b.neighborAtom(c2)
        accCoords = getTransformedCoords(accAt)
        c2Coords = getTransformedCoords(c2)
        c3Coords = getTransformedCoords(c3)
        c4Coords = getTransformedCoords(c4)
        v = vec3(c3Coords, c2Coords, 1.020)
        v1 = vec3(c4Coords, c2Coords, 1.020)
        #v = vec3(c3.coords, c2.coords, 1.020)
        #v1 = vec3(c4.coords, c2.coords, 1.020)
        #check angles of c3-at-b.accAt
        c = getTransformedCoords(at)
        #c = at.coords
        coords1 = [c[0]+v[0], c[1]+v[1], c[2]+v[2]]
        coords2 = [c[0]+v1[0], c[1]+v1[1], c[2]+v1[2]]
        dist1 =  dist(c3Coords, accCoords)
        dist2 =  dist(c4Coords, accCoords)
        #dist1 =  dist(c3.coords, accAt.coords)
        #dist2 =  dist(c4.coords, accAt.coords)
        if dist1 > dist2:
            coords = coords1
        else:
            coords = coords2
        name = 'H' + at.name 
        childIndex = at.parent.children.index(at)+1
        atom = Atom(name, at.parent, top=at.top, childIndex=childIndex,
                        assignUniqIndex=0)
        atom._coords = [coords]
        if hasattr(at, 'segID'): atom.setID = at.segID
        atom.hetatm = at.hetatm
        atom.alternate = []
        atom.element = 'H'
        atom.occupancy = 1.0
        atom.conformation = 0
        atom.temperatureFactor = 0.0
        atom.babel_atomic_number = 1
        atom.babel_type = 'H'
        atom.babel_organic = 1
        bond = Bond(at, atom)
        atom.colors = {}
        for key, value in at.colors.items():
            atom.colors[key] = (0.0, 1.0, 1.0)
            atom.opacities[key] = 1.0
        atom.number = len(at.parent.children)
        return atom


    def doit(self, ats, renumber=1):
        #addhydrogens to hbonds 
        withHBondAts = AtomSet(ats.get(lambda x: hasattr(x, 'hbonds')))
        if not withHBondAts:
            return 'ERROR'
        newHs = AtomSet([])
        for at in withHBondAts:
            for b in at.hbonds:
                if at!=b.donAt: 
                    continue
                if b.hAt is None:
                    if len(at.bonds)==1 and \
                        at.babel_type in ['Ng+', 'Nam','Npl']:
                        h = self.chooseH(at, b.accAt)
                    else:
                        self.vf.add_h(AtomSet([b.donAt]), 1,'noBondOrder',
                                      1,topCommand=0)
                        h = at.bonds[-1].neighborAtom(at)
                    h.hbonds = [b]
                    newHs.append(h)
                    b.hAt = h
        if renumber:
            for mol in ats.top.uniq():
                mol.allAtoms.sort()
                fst = mol.allAtoms[0].number
                mol.allAtoms.number = range(fst, len(mol.allAtoms)+fst)

        # MS
        #assert len(newHs)==len(newHs.uniq())
        # tester -V Pmv.Tests.test_hbondCommands.hbond_hbondTests.test_addhbonds_hsGC__log_checks_that_it_runs
        # creates
        #hbond_barrel: :GLY22:HN1
        #hbond_barrel: :THR23:HG1
        #hbond_barrel: :THR23:HG1
        #hbond_barrel: :ALA28:HN
        # ...
        #  THR32:HG1 is double !
        #print 'OKKKKKKKKKKKKKKKKKKKKKK', newHs
        #for a in newHs:
        #    print a.full_name()
        set = newHs.uniq()
        # (MS) seems like we do not add atom here, They have been added by the
        # self.vf.add_h above
        #event = AddAtomsEvent(objects=set)
        #self.vf.dispatchEvent(event)

        return set


    def __call__(self, nodes, **kw):
        """newHs <--- addHBondHs(nodes, **kw)
          \nnodes --- atoms 
          \nnewHs are new atoms, added to hbond.donAt
           """
        if type(nodes) is StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes =self.vf.expandNodes(nodes)
        if not len(nodes):
            return 'ERROR'
        if nodes.__class__!=Atom:
            ats = nodes.findType(Atom)
        else:
            ats = nodes
        try:
            ats.babel_type
        except AttributeError:
            tops = ats.top.uniq()
            for t in tops: 
                self.vf.typeAtoms(t.allAtoms, topCommand=0)
        return apply( self.doitWrapper, (ats,), kw)



class LimitHydrogenBonds(MVCommand):
    """This class allows user to detect pre-existing HydrogenBonds with energy values 
'lower' than a designated cutoff.  Optionally the user can remove these bonds.
   \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : LimitHydrogenBonds
   \nCommand : limitHBonds
   \nSynopsis:\n
        None <- limitHBonds(nodes, energy, **kw)
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def onRemoveObjectFromViewer(self, obj):
        if not len(self.hbonds):
            return
        removedAts = obj.findType(Atom)
        changed = 0
        bndsToRemove=[]
        for b in self.hbonds:
            ats = AtomSet([b.donAt,b.accAt])
            if b.hAt is not None:
                ats.append(b.hAt)
            if ats.inter(removedAts):
                bndsToRemove.append(b)
        for b in bndsToRemove:
            self.hbonds.remove(b)
            changed = 1
            ats = AtomSet([b.donAt,b.accAt])
            if b.hAt is not None:
                ats.append(b.hAt)
            for at in ats:
                at.hbonds.remove(b)
                if not len(at.hbonds):
                    delattr(at, 'hbonds')
        if changed:
            self.update()
                


    def onAddCmdToViewer(self):
        from DejaVu.IndexedPolylines import IndexedPolylines
        #from DejaVu.Labels import Labels
        miscGeom = self.vf.GUI.miscGeom
        hbond_geoms = check_hbond_geoms(self.vf.GUI)
        self.masterGeom = Geom('limitHbondGeoms',shape=(0,0), 
                                pickable=0, protected=True)
        self.masterGeom.isScalable = 0
        self.vf.GUI.VIEWER.AddObject(self.masterGeom, parent=hbond_geoms)
        self.lines = IndexedPolylines('limitHbondLines', 
                    materials = ((1,0,0),), lineWidth=8, 
                    stippleLines=1, inheritMaterial=0, protected=True)
        self.labels = GlfLabels(name='limitELabs', shape=(0,3),
                            materials=((1,1,0),), inheritMaterial=0,
                            billboard=True, fontStyle='solid',
                            fontScales=(.3,.3,.3,)) 
        self.labels.font = 'arial1.glf'
        geoms = [self.lines, self.labels]
        for item in geoms:
            self.vf.GUI.VIEWER.AddObject(item, parent=self.masterGeom)

        self.vf.loadModule('labelCommands', 'Pmv', log=0)
        self.showAll = Tkinter.IntVar()
        self.showAll.set(1)
        self.disp_energy = Tkinter.IntVar()
        self.disp_energy.set(0)
        self.everts = []
        self.e_labs = []
        self.hideSel = Tkinter.IntVar()
        self.hideSel.set(1)
        self.bondsToDelete = []
        #SHOULD THIS BE A HYDROGENBONDSET?
        self.hbonds = []


    def __call__(self, nodes, **kw):
        """None <- limitHBonds(nodes, energy, **kw) """
        if type(nodes) is StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes =self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        ats = nodes.findType(Atom)
        apply(self.doitWrapper, (ats,), kw)


    def doit(self, ats):
        #limit HBonds by energy
        self.hasEnergies = 0
        self.bondsToDelete = []
        self.hbonds = []
        self.everts = []
        self.e_labs = []
        self.resetDisplay()

        hbats = AtomSet(ats.get(lambda x: hasattr(x, 'hbonds')))
        if not hbats:
            self.warningMsg('no hydrogen bonds found')
            return 'ERROR'
        hats = AtomSet(hbats.get(lambda x: x.element=='H'))

        atNames = []
        if hats:
            for h in hats:
                atNames.append((h.full_name(), None))
                #self.hbonds.append(h.hbonds[0])
                for b in h.hbonds:
                    self.hbonds.append(b)
        else:
            hats = AtomSet([])
            bnds = []
            for at in hbats:
                bnds.extend(at.hbonds)
            bndD = {}
            for b in bnds:
                bndD[b] = 0
            hbnds2 = bndD.keys()
            hbnds2.sort()
            for b in hbnds2:
                atNames.append((b.donAt.full_name(), None))
                hats.append(b.donAt)
                self.hbonds.append(b)
        #self.vf.showHBonds.doit(hats)
        #self.vf.showHBonds.showAllHBonds(hats)
        #self.vf.showHBonds.buildEnergies(hats)
        self.vf.getHBondEnergies(hats, topCommand=0)
        #self.vf.showHBonds.showDistLabels.set(0)
        #self.vf.showHBonds.showDistances()
        #self.vf.showHBonds.dispEnergy.set(0)
        #self.vf.showHBonds.showEnergies(hats)
        self.origLabel = '0 hbonds to delete:'
        ifd = self.ifd=InputFormDescr(title = 'Hydrogen Bonds to Delete:')
        ifd.append({'name': 'hbondLabel',
            'widgetType': Tkinter.Label,
            'wcfg':{'text': self.origLabel},
            'gridcfg':{'sticky': 'wens', 'columnspan':2}})
        ifd.append({'name': 'atsLC',
            'widgetType':ListChooser,
            'wcfg':{
                'entries': atNames,
                'mode': 'multiple',
                'title': '',
                'command': CallBackFunction(self.showHBondLC, atNames),
                'lbwcfg':{'height':5, 
                    'selectforeground': 'red',
                    'exportselection': 0,
                    'width': 30},
            },
            'gridcfg':{'sticky':'wens', 'row':2,'column':0, 'columnspan':2}})
        ifd.append( {'name':'energy',
            'widgetType': ExtendedSliderWidget,
            'wcfg':{'label':'energy limit ',
                 'minval':-10, 'maxval':10,
                'immediate':1,
                'init':-2.0,
                'width':150,
                'command':self.update,
                'sliderType':'float',
                'entrypackcfg':{'side':'bottom'}},
            'gridcfg':{'sticky':'we', 'columnspan':2}})
        ifd.append({'name':'resetBut',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Reset',
                'command': self.reset},
            'gridcfg':{'sticky':'wens'}})
        ifd.append({'name':'showEnBut',
            'widgetType':Tkinter.Checkbutton,
            'wcfg': { 'text':'Show Energy',
                'variable': self.disp_energy,
                'command': CallBackFunction(self.showEnergies, hats)},
            'gridcfg':{'sticky':'wens', 'column':1, 'row':-1}})
        ifd.append({'name':'acceptBut',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Delete',
                'command': self.Delete_cb},
            'gridcfg':{'sticky':'wens'}})
        ifd.append({'name':'closeBut',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Dismiss',
                'command': self.dismiss_cb},
            'gridcfg':{'sticky':'wens', 'row':-1, 'column':1}})

        self.form2  = self.vf.getUserInput(ifd, modal=0, blocking=0,
                 width=350, height=330)
        self.form2.root.protocol('WM_DELETE_WINDOW',self.dismiss_cb)
        self.lb = self.ifd.entryByName['atsLC']['widget'].lb
        self.energyWid = self.ifd.entryByName['energy']['widget']
        self.hbondLabel = self.ifd.entryByName['hbondLabel']['widget']
        self.update()


    def Delete_cb(self, event=None):
        bl = []
        for b in self.bondsToDelete:
            for at in [b.donAt, b.hAt, b.accAt]:
                at.hbonds.remove(b)
                if not len(at.hbonds):
                    delattr(at, 'hbonds')
            bl.append(b)
        self.bondsToDelete = []
        for b in bl:
            del b
        #also reset self.hbondLabel, self.lb
        self.reset()
        #also need to reset showHBonds so it will recalc everything
        self.vf.showHBonds.reset()
        self.vf.showHBonds.lines.Set(vertices=[], tagModified=False)
        self.vf.showHBonds.labels.Set(vertices=[], tagModified=False)
        self.vf.showHBonds.engLabs.Set(vertices=[], tagModified=False)
        self.vf.showHBonds.dispEnergy.set(0)
        self.vf.GUI.VIEWER.Redraw()
        self.everts = []
        self.dismiss_cb()


    def resetDisplay(self, event=None):
        self.lines.Set(vertices=[], tagModified=False)
        self.labels.Set(vertices=[], labels=[], tagModified=False)


    def updateDisplay(self, event=None):
        #this draws red lines along bondToDelete
        lineVerts = []
        faces = []
        self.everts = []
        labs = []
        ctr = 0
        n = len(self.bondsToDelete)
        self.lb.delete(0, 'end')
        if n:
            for b in self.bondsToDelete:
                hAtCoords = getTransformedCoords(b.hAt)
                accAtCoords = getTransformedCoords(b.accAt)
                lineVerts.append(hAtCoords)
                lineVerts.append(accAtCoords)
                #lineVerts.append(b.hAt.coords)
                #lineVerts.append(b.accAt.coords)
                faces.append((ctr, ctr+1))
                pt = (Numeric.array(hAtCoords)+Numeric.array(accAtCoords))/2.0
                self.everts.append(pt.tolist())
                labs.append(str(b.energy))
                ctr = ctr + 2
                self.lb.insert('end', b.hAt.full_name())
            self.lines.Set(vertices = lineVerts, faces=faces,
                           tagModified=False)
            self.labels.Set(vertices = self.everts, labels = labs,
                            tagModified=False)
            msg = str(n) + ' hbonds to delete:'
            self.hbondLabel.config(text=msg)
        else:
            msg = '0 hbonds to delete:'
            self.hbondLabel.config(text=msg)
            self.resetDisplay()
        self.vf.GUI.VIEWER.Redraw()
                

    def reset(self):
        self.lb.select_clear(0, 'end')
        self.lb.delete(0, 'end')
        self.hbondLabel.config(text=self.origLabel)
        self.energyWid.set(-2.0)
        #also change bonds to delete
        self.bondsToDelete = []
        self.everts = []
        self.resetDisplay()
        self.update()


    def update(self, event=None):
        energy = self.energyWid.get()
        self.bondsToDelete = []
        for b in self.hbonds:
            if b.energy > energy and not b in self.bondsToDelete:
                self.bondsToDelete.append(b)
        self.updateDisplay()
            

    def showHBondLC(self, hats, event=None):
        if not hasattr(self, 'ifd'):
            self.doit(hats)
        if self.lb.curselection() == (): return
        self.showAll.set(0)
        #THIS COULD BE >1
        labs = []
        verts = []
        lineVerts = []
        faces = []
        ctr = 0
        for n in self.lb.curselection():
            #n in ('0','1','2')
            name = self.lb.get(n)
            at = self.vf.Mols.NodesFromName(name)[0]
            b = at.hbonds[0]
            #NB THESE MUST HAVE hydrogens
            hAtCoords = getTransformedCoords(b.hAt)
            accAtCoords = getTransformedCoords(b.accAt)
            lineVerts.append(hAtCoords) 
            lineVerts.append(accAtCoords) 
            #lineVerts.append(b.hAt.coords) 
            #lineVerts.append(b.accAt.coords) 
            faces = ((ctr,ctr+1),)
            if self.hasEnergies:
                labs.append(self.e_labs[ind])
                verts.append(self.everts[ind])
            ctr = ctr + 2
        self.labels.Set(vertices=verts,labels=labs,\
                        visible=self.disp_energy.get(), tagModified=False)
        self.lines.Set(vertices=lineVerts, type=GL.GL_LINE_STRIP,
                           faces=faces, freshape=1, tagModified=False)
        self.vf.GUI.VIEWER.Redraw()


    def dismiss_cb(self, event=None, **kw):
        #limitHbonds
        self.lines.Set(vertices=[], tagModified=False)
        self.labels.Set(vertices=[], tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        delattr(self, 'ifd')
        self.form2.destroy()
        self.hbonds = []
        self.everts = []
        self.vf.showHBonds.dismiss_cb()


    def showEnergies(self, hats):
        if not self.showAll.get():
            self.showHBondLC(hats)
        else:
            self.labels.Set(labels = self.e_labs, vertices = self.everts,
                visible=self.disp_energy.get(), tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        

    def buildEnergies(self, hats):
        #FIX THIS: for some reason, eList is disordered...???
        eList = self.vf.getHBondEnergies(hats, topCommand=0)
        for hat in hats:
            self.e_labs.append(str(hat.hbonds[0].energy))


    def hideSelector(self, event=None):
        e = self.ifd.entryByName['keySelector']
        if self.hideSel.get():
            e['widget'].grid_forget()
        else:
            e['widget'].grid(e['gridcfg'])
        self.form.autoSize() 


    def cleanUpCrossSet(self):
        chL = []
        for item in self.vf.GUI.VIEWER.rootObject.children:
            if isinstance(item, CrossSet) and item.name[:8]=='strSelCr':
                chL.append(item)
        if len(chL):
            for item in chL: 
                item.Set(vertices=[], tagModified=False)
                self.vf.GUI.VIEWER.Redraw()
                self.vf.GUI.VIEWER.RemoveObject(item)


    def Close_cb(self, event=None):
        self.cleanUpCrossSet()
        self.form.destroy()


    def Ok_cb(self, event=None):
        if self.hideSel.get():
            nodes = self.vf.getSelection()
        else:
            nodes = self.ifd.entryByName['keySelector']['widget'].get()
        if not len(nodes):
            self.warningMsg('no nodes specified')
            return
        ats = nodes.findType(Atom)
        self.form.withdraw()
        apply(self.doitWrapper, (ats,), {})


    def guiCallback(self):
        #limitHbonds
        if not len(self.vf.Mols):
            self.warningMsg('no molecules in viewer')
            return 
        sel =  self.vf.getSelection()
        ifd = self.ifd = InputFormDescr(title = "Select nodes + energy limit")
        ifd.append({'name':'DkeyLab',
                    'widgetType':Tkinter.Label,
                    'text':'For Hydrogen Bonds:',
                    'gridcfg':{'sticky':Tkinter.W,'columnspan':3}})
        ifd.append({'name':'selDRB0',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'Use all atoms',
                'variable': self.hideSel,
                'value':1,
                'command':self.hideSelector
                },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'selDRB1',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'Set atoms to use',
                'variable': self.hideSel,
                'value':0,
                'command':self.hideSelector
                },
            'gridcfg':{'sticky':'w', 'row':-1, 'column':1}})
        ifd.append({'name': 'keySelector',
            'wtype':StringSelectorGUI,
            'widgetType':StringSelectorGUI,
            'wcfg':{ 'molSet': self.vf.Mols,
                    'vf': self.vf,
                    'all':1,
                    'crColor':(0.,1.,.2),
            },
            'gridcfg':{'sticky':'we', 'columnspan':2 }})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Ok',
            'wcfg':{'bd':6,
                    'command':self.Ok_cb,
                    },
            'gridcfg':{'sticky':'ew', 'columnspan':2 }})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Cancel',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'ew', 'column':2,'row':-1},
            'command':self.Close_cb})
        self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW',self.Close_cb)
        self.hideSelector()


LimitHydrogenBondsGuiDescr = {'widgetType':'Menu',
                                          'menuBarName':'menuRoot',
                                          'menuButtonName':'Hydrogen Bonds',
                                          'menuEntryLabel':'Limit Existing Hbonds',
                                          'menuCascadeName': 'Edit'}


LimitHydrogenBondsGUI = CommandGUI()
LimitHydrogenBondsGUI.addMenuCommand('menuRoot', 'Hydrogen Bonds',
        'Limit Existing Hbonds by Energy', cascadeName='Edit')



class DisplayHBonds(MVCommand):
    """Base class to allow user to visualize pre-existing HydrogenBonds between 
atoms in viewer 
   \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : DisplayHBonds
   \nCommand : displayHBonds
   \nSynopsis:\n
        None <--- displayHBonds(ats)
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def initGeom(self):
        #initialize:
        #   self.geom
        #   self.hasGeom
        pass


    def onAddCmdToViewer(self):
        self.initGeom()
        #from DejaVu.Labels import Labels
        self.verts = []
        self.showAll = Tkinter.IntVar()
        self.showAll.set(1)
        self.vf.loadModule('labelCommands', 'Pmv', log=0)
        # Create a ColorChooser.
        self.palette = ColorChooser(commands=self.color_cb,
                    exitFunction = self.hidePalette_cb)
        # pack
        self.palette.pack(fill='both', expand=1)
        # hide it 
        self.palette.hide()
        self.width = 100
        self.height = 100
        self.winfo_x = None
        self.winfo_y = None


    def hidePalette_cb(self, event=None):
        self.palette.hide()


    def reset(self):
        self.geom.Set(vertices=[], tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        self.hasGeom = 0


    def update(self, event=None):
        self.radii = self.radii_esw.get()
        self.hasGeom =0
        self.showAllHBonds()
        

    def showHBondLC(self, atName, event=None):
        #perhaps toggle on and off displaying the hbond with this???
        #find the bond and change its visible field
        for n in self.lb.curselection():
            #n in ('0','1','2')
            entry = self.lb.get(n)
            name = entry[:-2]
            #at = self.vf.Mols.NodesFromName(name)[0]
            ats = self.vf.Mols.NodesFromName(name)
            at = ats[0]
            #to deal with two atoms with the exact same name:
            if len(ats)>1:
                for a in ats:
                    if hasattr(a, 'hbonds'):
                        at = a
                        break
            b = at.hbonds[0]
            #b.visible = not(b.visible)
            if b.visible==0: b.visible = 1
            else: b.visible = 0
            entry = name + ' ' + str(b.visible)
            self.lb.delete(n)
            self.lb.insert(n, entry)
        self.hasGeom = 0
        self.showAllHBonds()


    def color_cb(self, colors):
        from DejaVu import colorTool
        self.geom.Set(materials = (colors[:3],), tagModified=False)
        self.vf.GUI.VIEWER.Redraw()


    def changeColor(self, event=None):
        #col = self.palette.display(callback=self.color_cb, modal=1)
        #self.palette.pack(fill='both', expand=1)
        # Create a ColorChooser.
        if not hasattr(self, 'palette') or not self.palette.master.winfo_exists():
            self.palette = ColorChooser(commands=self.color_cb,
                        exitFunction = self.hidePalette_cb)
            # pack
            self.palette.pack(fill='both', expand=1)
            #??rh WHY hide it??
            #self.palette.hide()
        if not self.palette.master.winfo_ismapped():
            self.palette.master.deiconify()


    def getIfd(self, atNames):
        #base class
        pass

#        print 'in spheres getIfd'
#        if not hasattr(self, 'ifd'):
#            ifd = self.ifd = InputFormDescr(title = 'Show Hydrogen Bonds as Spheres')
#            ifd.append({'name': 'hbondLabel',
#                'widgetType': Tkinter.Label,
#                'wcfg':{'text': str(len(atNames)) + ' Atoms in hbonds:'},
#                'gridcfg':{'sticky': 'wens', 'columnspan':2}})
#            ifd.append({'name': 'atsLC',
#                'widgetType':ListChooser,
#                'wcfg':{
#                    'entries': atNames,
#                    'mode': 'multiple',
#                    'title': '',
#                    'command': CallBackFunction(self.showHBondLC, atNames),
#                    'lbwcfg':{'height':5, 
#                        'selectforeground': 'red',
#                        'exportselection': 0,
#                        'width': 30},
#                },
#                'gridcfg':{'sticky':'wens', 'row':2,'column':0, 'columnspan':2}})
#            ifd.append( {'name':'spacing',
#                'widgetType': ExtendedSliderWidget,
#                'wcfg':{'label':'spacing',
#                     'minval':.01, 'maxval':1.0,
#                    'immediate':1,
#                    'init':.4,
#                    'width':150,
#                    'command':self.update,
#                    'sliderType':'float',
#                    'entrypackcfg':{'side':'bottom'}},
#                'gridcfg':{'sticky':'wens'}})
#            ifd.append( {'name':'radii',
#                'widgetType': ExtendedSliderWidget,
#                'wcfg':{'label':'radii',
#                     'minval':.01, 'maxval':1.0,
#                    'immediate':1,
#                    'init':.1,
#                    'width':150,
#                    'command':self.update,
#                    'sliderType':'float',
#                    'entrypackcfg':{'side':'bottom'}},
#                'gridcfg':{'sticky':'wens','row':-1, 'column':1}})
#            ifd.append( {'name':'quality',
#                'widgetType': Tkinter.Scale,
#                'wcfg':{'label':'quality',
#                    'troughcolor':'green',
#                     'from_':2, 'to_':20,
#                    'orient':'horizontal',
#                    'length':'2i',
#                    'command':self.updateQuality },
#                'gridcfg':{'sticky':'wens'}})
#            ifd.append({'name':'changeColorBut',
#                'widgetType':Tkinter.Button,
#                'wcfg': { 'text':'Choose color',
#                    'relief':'flat',
#                    'command': self.changeColor},
#                'gridcfg':{'sticky':'wes', 'row':-1, 'column':1}})
#            ifd.append({'name':'changeVertsBut',
#                'widgetType':Tkinter.Button,
#                'wcfg': { 'text':'Set anchors',
#                    'command': self.changeDVerts},
#                'gridcfg':{'sticky':'wens'}})
#            ifd.append({'name':'closeBut',
#                'widgetType':Tkinter.Button,
#                'wcfg': { 'text':'Dismiss',
#                    'command': self.dismiss_cb},
#                'gridcfg':{'sticky':'wens', 'row':-1, 'column':1}})


    def setUpWidgets(self, atNames):
        if not hasattr(self, 'ifd'):
            self.getIfd(atNames)
        self.radii_esw = self.ifd.entryByName['radii']['widget']
        self.lb = self.ifd.entryByName['atsLC']['widget'].lb


    def doit(self, ats):
        #DisplayHBonds base class
        self.reset()
        hbats = AtomSet(ats.get(lambda x: hasattr(x, 'hbonds')))
        if not hbats:
            self.warningMsg('no hydrogen bonds found')
            return 'ERROR'
        hats = AtomSet(hbats.get(lambda x: x.element=='H'))
        atNames = []
        if hats:
            for h in hats:
                nStr = h.full_name() + ' 1'
                atNames.append((nStr, None))
                #h.hbonds[0].visible = 1
                for b in h.hbonds:
                    b.visible = 1
        else:
            hats = AtomSet([])
            bnds = []
            for at in hbats:
                bnds.extend(at.hbonds)
            bndD = {}
            for b in bnds:
                bndD[b] = 0
            hbnds2 = bndD.keys()
            hbnds2.sort()
            for b in hbnds2:
                b.visible = 1
                nStr = b.donAt.full_name() + ' 1'
                atNames.append((nStr, None))
                hats.append(b.donAt)
        self.hats = hats
        self.showAllHBonds()
        #print "hasattr(self, form)==", hasattr(self, 'form')
        self.getIfd(atNames)
        if not hasattr(self, 'form'):
            #print "building form"
            self.form  = self.vf.getUserInput(self.ifd, modal=0, blocking=0,
                 width=380, height=390)
            self.form.root.protocol('WM_DELETE_WINDOW',self.dismiss_cb)
            self.toplevel = self.form.f.master.master
            self.toplevel.positionfrom(who='user')
            if self.winfo_x is not None and self.winfo_y is not None:
                geom = self.width +'x'+ self.height +'+'
                geom += self.winfo_x + '+' + self.winfo_y
                self.toplevel.geometry(newGeometry=geom)
        #else:
            #print "already has form"
        self.setUpWidgets(atNames)


    def updateQuality(self, event=None):
        # asSpheres
        self.quality = self.quality_sl.get()
        self.geom.Set(quality=quality, tagModified=False)
        self.showAllHBonds()


    def dismiss_cb(self, event=None, **kw):
        # base class
        self.reset()
        try:
            self.width = str(self.toplevel.winfo_width())
            self.height = str(self.toplevel.winfo_height())
            self.winfo_x = str(self.toplevel.winfo_x())
            self.winfo_y = str(self.toplevel.winfo_y())
        except:
            pass
        self.vf.GUI.VIEWER.Redraw()
        if hasattr(self, 'ifd'):
            delattr(self, 'ifd')
        if hasattr(self, 'form2'):
            self.form2.destroy()
            delattr(self, 'form2')
        if hasattr(self, 'form'):
            self.form.destroy()
            delattr(self, 'form')
        if hasattr(self, 'palette'):
            #self.palette.exit()
            self.palette.hide()


    def setupDisplay(self):
        #draw geom between hAts OR donAts and accAts
        self.geom.Set(vertices = self.verts, radius = self.radius,
                      tagModified=False)
        self.vf.GUI.VIEWER.Redraw()


    def interpolate(self, pt1, pt2):
        # self.spacing = .4
        length = dist(pt1, pt2)
        c1 = Numeric.array(pt1)
        c2 = Numeric.array(pt2)
        n = length/self.spacing
        npts = int(math.floor(n))
        # use floor of npts to set distance between > spacing
        delta = (c2-c1)/(1.0*npts)
        ##spacing = length/floor(npts)
        vertList = []
        for i in range(npts):
            vertList.append((c1+i*delta).tolist())
        vertList.append(pt2.tolist())
        return vertList


    def setDVerts(self, entries, event=None):
        if not hasattr(self, 'ifd2'):
            self.changeDVerts()
        lb = self.ifd2.entryByName['datsLC']['widget'].lb
        if lb.curselection() == (): return
        atName = lb.get(lb.curselection())
        ind = int(lb.curselection()[0])
        for h in self.hats:
            for b in h.hbonds:
                ats = b.donAt.parent.atoms.get(lambda x, atName=atName: x.name==atName)
                if ats is None or len(ats) == 0:
                    if b.hAt is not None: at = b.hAt
                    else: at = b.donAt
                else:
                    at = ats[0]
                b.spVert1 = at
        self.hasGeom = 0
        self.showAllHBonds()
        

    def setAVerts(self, entries, event=None):
        if not hasattr(self, 'ifd2'):
            self.changeDVerts()
        lb = self.ifd2.entryByName['aatsLC']['widget'].lb
        if lb.curselection() == (): return
        atName = lb.get(lb.curselection())
        ind = int(lb.curselection()[0])
        for h in self.hats:
            for b in h.hbonds:
                ats = b.accAt.parent.atoms.get(lambda x, atName=atName: x.name==atName)
                if ats is None or len(ats) == 0:
                    at = b.accAt
                else:
                    at = ats[0]
                b.spVert2 = at
        self.hasGeom = 0
        self.showAllHBonds()


    def changeDVerts(self, event=None):
        #for all residues in hbonds, pick new donorAttachment
        # and new acceptorAttachment
        entries = []
        ns = ['N','C','O','CA','reset']
        for n in ns:
            entries.append((n, None))

        if hasattr(self, 'form2'):
            self.form2.root.tkraise()
            return
        ifd2 = self.ifd2=InputFormDescr(title = 'Set Anchor Atoms')
        ifd2.append({'name': 'datsLC',
            'widgetType':ListChooser,
            'wcfg':{
                'entries': entries,
                'mode': 'single',
                'title': 'Donor Anchor',
                'command': CallBackFunction(self.setDVerts, entries),
                'lbwcfg':{'height':5, 
                    'selectforeground': 'red',
                    'exportselection': 0,
                    #'lbpackcfg':{'fill':'both', 'expand':1},
                    'width': 30},
            },
            'gridcfg':{'sticky':'wens', 'columnspan':2}})
        ifd2.append({'name': 'aatsLC',
            'widgetType':ListChooser,
            'wcfg':{
                'entries': entries,
                'mode': 'single',
                'title': 'Acceptor Anchor',
                'command': CallBackFunction(self.setAVerts, entries),
                'lbwcfg':{'height':5, 
                    'selectforeground': 'red',
                    #'lbpackcfg':{'fill':'both', 'expand':1},
                    'exportselection': 0,
                    'width': 30},
            },
            'gridcfg':{'sticky':'wens', 'columnspan':2}})
        ifd2.append({'name':'doneBut',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Done',
                'command': self.closeChangeDVertLC},
            'gridcfg':{'sticky':'wens'}})
        self.form2 = self.vf.getUserInput(self.ifd2, modal=0, blocking=0)
        self.form2.root.protocol('WM_DELETE_WINDOW',self.closeChangeDVertLC)


    def closeChangeDVertLC(self, event=None):
        if hasattr(self, 'ifd2'):
            delattr(self, 'ifd2')
        if hasattr(self, 'form2'):
            self.form2.destroy()
            delattr(self, 'form2')


    def showAllHBonds(self, event=None):
        if not self.hasGeom:
            verts = []
            for at in self.hats:
                for b in at.hbonds:
                    if hasattr(b, 'visible') and not b.visible: continue
                    if hasattr(b, 'spVert1'):
                        pt1 = getTransformedCoords(b.spVert1)
                        #verts.append(getTransformedCoords(b.spVert1))
                        #verts.append(b.spVert1.coords)
                    elif b.hAt is not None:
                        pt1 = getTransformedCoords(b.hAt)
                        #verts.append(getTransformedCoords(b.hAt))
                        #verts.append(b.hAt.coords) 
                    else:
                        pt1 = getTransformedCoords(b.donAt)
                        #verts.append(getTransformedCoords(b.donAt))
                        #verts.append(b.donAt.coords)
                    if hasattr(b, 'spVert2'):
                        #verts.extend(self.interpolate(verts[-1],
                        verts.extend(self.interpolate(pt1,
                                getTransformedCoords(b.spVert2)))
                    else:
                        #verts.extend(self.interpolate(verts[-1],
                        verts.extend(self.interpolate(pt1,
                                getTransformedCoords(b.accAt)))
            self.verts = verts
            self.hasGeom = 1
        self.geom.Set(vertices = self.verts, radii = self.radii,
                      tagModified=False)
        self.vf.GUI.VIEWER.Redraw()


    def guiCallback(self):
        #showHbonds
        if not len(self.vf.Mols):
            self.warningMsg('no molecules in viewer')
            return 
        sel =  self.vf.getSelection()
        #put a selector here
        if len(sel):
            ats = sel.findType(Atom)
            apply(self.doitWrapper, (ats,), {})



class DisplayHBondsAsSpheres(DisplayHBonds):
    """This class allows user to visualize pre-existing HydrogenBonds between 
atoms in viewer as small spheres
    \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : DisplayHBondsAsSpheres
   \nCommand : displayHBSpheres
   \nSynopsis:\n
        None <--- displayHBSpheres(nodes, **kw)
    """

    def initGeom(self):
        from DejaVu.IndexedPolylines import IndexedPolylines
        #from DejaVu.Labels import Labels
        self.quality = 4
        self.spheres = self.geom = Spheres('hbondSpheres', 
                    materials=((0,1,0),), shape=(0,3),
                    radii=0.1, quality=4, pickable=0, inheritMaterial=0, protected=True)
        geoms = [self.spheres]
        self.masterGeom = Geom('HbondsAsSpheresGeoms',shape=(0,0), 
                                pickable=0, protected=True)
        self.masterGeom.isScalable = 0
        if self.vf.hasGui:
            miscGeom = self.vf.GUI.miscGeom
            hbond_geoms = check_hbond_geoms(self.vf.GUI)
        
            self.vf.GUI.VIEWER.AddObject(self.masterGeom, parent=hbond_geoms)
            for item in geoms:
                self.vf.GUI.VIEWER.AddObject(item, parent=self.masterGeom)
        self.hasGeom = 0
        self.spacing = .40
        self.radii = 0.1
        self.verts = []
        


    def __call__(self, nodes, **kw):
        """None <- displayHBSpheres(nodes, **kw) """
        if type(nodes) is StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        ats = nodes.findType(Atom)
        apply(self.doitWrapper, (ats,), kw)



    def update(self, event=None):
        #as spheres
        self.radii = self.radii_esw.get()
        self.spacing = self.spacing_esw.get()
        self.hasGeom = 0
        self.showAllHBonds()
        

    def color_cb(self, colors):
        from DejaVu import colorTool
        self.geom.Set(materials = (colors[:3],), tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        col = colorTool.TkColor(colors[:3])
        self.quality_sl.config(troughcolor = col)


    def getIfd(self, atNames):
        #print 'in spheres getIfd'
        if not hasattr(self, 'ifd'):
            ifd = self.ifd=InputFormDescr(title = 'Show Hydrogen Bonds as Spheres')
            ifd.append({'name': 'hbondLabel',
                'widgetType': Tkinter.Label,
                'wcfg':{'text': str(len(atNames)) + ' Atoms in hbonds:\n(1=visible, 0 not visible)'},
                'gridcfg':{'sticky': 'wens', 'columnspan':2}})
            ifd.append({'name': 'atsLC',
                'widgetType':ListChooser,
                'wcfg':{
                    'entries': atNames,
                    'mode': 'multiple',
                    'title': '',
                    'command': CallBackFunction(self.showHBondLC, atNames),
                    'lbwcfg':{'height':5, 
                        'selectforeground': 'red',
                        'exportselection': 0,
                        'width': 30},
                },
                'gridcfg':{'sticky':'wens', 'row':2,'column':0, 'columnspan':2}})
            ifd.append( {'name':'spacing',
                'widgetType': ExtendedSliderWidget,
                'wcfg':{'label':'spacing',
                     'minval':.01, 'maxval':1.0,
                    'immediate':1,
                    'init':.4,
                    'width':150,
                    'command':self.update,
                    'sliderType':'float',
                    'entrypackcfg':{'side':'bottom'}},
                'gridcfg':{'sticky':'wens'}})
            ifd.append( {'name':'radii',
                'widgetType': ExtendedSliderWidget,
                'wcfg':{'label':'radii',
                     'minval':.01, 'maxval':1.0,
                    'immediate':1,
                    'init':.1,
                    'width':150,
                    'command':self.update,
                    'sliderType':'float',
                    'entrypackcfg':{'side':'bottom'}},
                'gridcfg':{'sticky':'wens','row':-1, 'column':1}})
            ifd.append( {'name':'quality',
                'widgetType': Tkinter.Scale,
                'wcfg':{'label':'quality',
                    'troughcolor':'green',
                     'from_':2, 'to_':20,
                    'orient':'horizontal',
                    'length':'2i',
                    'command':self.updateQuality },
                'gridcfg':{'sticky':'wens'}})
            ifd.append({'name':'changeColorBut',
                'widgetType':Tkinter.Button,
                'wcfg': { 'text':'Choose color',
                    'relief':'flat',
                    'command': self.changeColor},
                'gridcfg':{'sticky':'wes', 'row':-1, 'column':1}})
            ifd.append({'name':'changeVertsBut',
                'widgetType':Tkinter.Button,
                'wcfg': { 'text':'Set anchors',
                    'command': self.changeDVerts},
                'gridcfg':{'sticky':'wens'}})
            ifd.append({'name':'closeBut',
                'widgetType':Tkinter.Button,
                'wcfg': { 'text':'Dismiss',
                    'command': self.dismiss_cb},
                'gridcfg':{'sticky':'wens', 'row':-1, 'column':1}})


    def setUpWidgets(self, atNames):
        if not hasattr(self, 'ifd'):
            self.getIfd(atNames)
        self.radii_esw = self.ifd.entryByName['radii']['widget']
        self.spacing_esw = self.ifd.entryByName['spacing']['widget']
        self.quality_sl= self.ifd.entryByName['quality']['widget']
        self.quality_sl.set(self.quality)
        self.lb = self.ifd.entryByName['atsLC']['widget'].lb


    def updateQuality(self, event=None):
        self.quality = self.quality_sl.get()
        self.geom.Set(quality=self.quality, tagModified=False)
        self.vf.GUI.VIEWER.Redraw()


DisplayHBondsAsSpheresGuiDescr = {'widgetType':'Menu',
                                          'menuBarName':'menuRoot',
                                          'menuButtonName':'Hydrogen Bonds',
                                          'menuEntryLabel':'As Spheres',
                                          'menuCascadeName': 'Display'}


DisplayHBondsAsSpheresGUI = CommandGUI()
DisplayHBondsAsSpheresGUI.addMenuCommand('menuRoot', 'Hydrogen Bonds',
        'As Spheres', cascadeName = 'Display')



class DisplayHBondsAsCylinders(DisplayHBonds):
    """This class allows user to visualize pre-existing HydrogenBonds between 
atoms in viewer as cylinders
   \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : DisplayHBondsAsCylinders
   \nCommand : displayHBCylinders
   \nSynopsis:\n
        None <- displayHBCylinders(nodes, **kw)
    """


    def initGeom(self):
        self.cylinders = self.geom = Cylinders('hbondCylinders', 
                    quality=40, culling=GL.GL_NONE, radii=(0.2),
                    materials=((0,1,0),), pickable=0, inheritMaterial=0)
        #DejaVu.Cylinders overwrites kw cull so have to reset it here
        self.cylinders.culling = GL.GL_NONE
        geoms = [self.cylinders]
        miscGeom = self.vf.GUI.miscGeom
        hbond_geoms = check_hbond_geoms(self.vf.GUI)
        self.masterGeom = Geom('HbondsAsCylindersGeoms',shape=(0,0), 
                                pickable=0, protected=True)
        self.vf.GUI.VIEWER.AddObject(self.masterGeom, parent=hbond_geoms)
        for item in geoms:
            self.vf.GUI.VIEWER.AddObject(item, parent=self.masterGeom)
        self.hasGeom = 0
        self.radii = 0.2
        self.length = 1.0
        self.oldlength = 1.0
        self.verts = []
        self.faces = []


    def __call__(self, nodes, **kw):
        """None <- displayHBCylinders(nodes, **kw) """
        if type(nodes) is StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes =self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        ats = nodes.findType(Atom)
        apply(self.doitWrapper, (ats,), kw)



    def getIfd(self, atNames):
        #cylinders
        if not hasattr(self, 'ifd'):
            ifd = self.ifd = InputFormDescr(title='Show Hydrogen Bonds as Cylinders')
            ifd.append({'name': 'hbondLabel',
                'widgetType': Tkinter.Label,
                'wcfg':{'text': str(len(atNames)) + ' Atoms in hbonds:\n(1=visible, 0 not visible)'},
                'gridcfg':{'sticky': 'wens', 'columnspan':2}})
            ifd.append({'name': 'atsLC',
                'widgetType':ListChooser,
                'wcfg':{
                    'entries': atNames,
                    'mode': 'multiple',
                    'title': '',
                    'command': CallBackFunction(self.showHBondLC, atNames),
                    'lbwcfg':{'height':5, 
                        'selectforeground': 'red',
                        'exportselection': 0,
                        'width': 30},
                },
                'gridcfg':{'sticky':'wens', 'row':2,'column':0, 'columnspan':2}})
            ifd.append( {'name':'radii',
                'widgetType': ExtendedSliderWidget,
                'wcfg':{'label':'radii',
                     'minval':.01, 'maxval':1.0,
                    'immediate':1,
                    'init':.2,
                    'width':250,
                    'command':self.update,
                    'sliderType':'float',
                    'entrypackcfg':{'side':'right'}},
                'gridcfg':{'sticky':'wens', 'columnspan':2}})
            ifd.append( {'name':'length',
                'widgetType': ExtendedSliderWidget,
                'wcfg':{'label':'length',
                     'minval':.01, 'maxval':5.0,
                    'immediate':1,
                    'init':1.0,
                    'width':250,
                    'command':self.update,
                    'sliderType':'float',
                    'entrypackcfg':{'side':'right'}},
                'gridcfg':{'sticky':'wens', 'columnspan':2}})
            ifd.append({'name':'changeVertsBut',
                'widgetType':Tkinter.Button,
                'wcfg': { 'text':'Set anchors',
                    'command': self.changeDVerts},
                'gridcfg':{'sticky':'wens'}})
            ifd.append({'name':'changeColorBut',
                'widgetType':Tkinter.Button,
                'wcfg': { 'text':'Change color',
                    'command': self.changeColor},
                'gridcfg':{'sticky':'wes', 'row':-1, 'column':1}})
            ifd.append({'name':'closeBut',
                'widgetType':Tkinter.Button,
                'wcfg': { 'text':'Dismiss',
                    'command': self.dismiss_cb},
                'gridcfg':{'sticky':'wens','columnspan':2 }})
            #ifd.append({'name':'changeVertsBut',
                #'widgetType':Tkinter.Button,
                #'wcfg': { 'text':'Set anchors',
                    #'command': self.changeDVerts},
                #'gridcfg':{'sticky':'wens'}})


    def setUpWidgets(self, atNames):
        if not hasattr(self, 'ifd'):
            self.getIfd(atNames)
        self.radii_esw = self.ifd.entryByName['radii']['widget']
        self.length_esw = self.ifd.entryByName['length']['widget']
        self.lb = self.ifd.entryByName['atsLC']['widget'].lb



    def update(self, event=None):
        #as cylinders
        self.radii = self.radii_esw.get()
        self.oldlength = self.length
        self.length = self.length_esw.get()
        self.hasGeom = 0
        self.showAllHBonds()
        

    def adjustVerts(self, v1, v2, length):
        #each end needs to be changed by length/2.
        #eg if length = 1.1, change each end by .05
        if length==self.oldlength:
            return (v1, v2)
        vec = Numeric.array(v2) - Numeric.array(v1)
        vec_len = math.sqrt(vec[0]**2 + vec[1]**2 + vec[2]**2) 
        alpha = (length-1.)/2.  #(.5-1)/2.-> -.25%  or (1.5 -1.)/2. ->+.25%
        #delta v1 is v1 - alpha*vec_len
        #delta v2 is v2 + alpha*vec_len
        delta = alpha*vec_len
        return Numeric.array(v1-delta*vec).astype('f'), Numeric.array(v2+delta*vec).astype('f')

        



    def showAllHBonds(self, event=None):
        if not self.hasGeom:
            verts = []
            faces = []
            ct = 0
            for at in self.hats:
                for b in at.hbonds:
                    if hasattr(b, 'visible') and not b.visible: continue
                    if hasattr(b, 'spVert1'):
                        pt1 = getTransformedCoords(b.spVert1)
                    elif b.hAt is not None:
                        pt1 = getTransformedCoords(b.hAt)
                    else:
                        pt1 = getTransformedCoords(b.donAt)
                    if hasattr(b, 'spVert2'):
                        #verts.extend(self.interpolate(verts[-1],
                        at2 = b.spVert2
                    else:
                        at2 = b.accAt
                    pt2 = getTransformedCoords(at2)
                    #verts.extend([pt1, pt2])
                    verts.extend(self.adjustVerts(pt1, pt2, self.length))
                    faces.append((ct, ct+1))
                    ct = ct + 2
            #reset oldlength here, after recalc all hbond verts
            self.oldlength = self.length
            self.verts = verts
            self.faces = faces
            self.hasGeom  = 1

        self.cylinders.Set(vertices=self.verts, radii=self.radii,
                           faces=self.faces, tagModified=False)
        self.vf.GUI.VIEWER.Redraw()


DisplayHBondsAsCylindersGuiDescr = {'widgetType':'Menu',
                                          'menuBarName':'menuRoot',
                                          'menuButtonName':'Hydrogen Bonds',
                                          'menuEntryLabel':'As Cylinders',
                                          'menuCascadeName': 'Display'}


DisplayHBondsAsCylindersGUI = CommandGUI()
DisplayHBondsAsCylindersGUI.addMenuCommand('menuRoot', 'Hydrogen Bonds',
        'As Cylinders', cascadeName = 'Display')



class ExtrudeHydrogenBonds(MVCommand):
    """This class allows user to visualize pre-existing HydrogenBonds between 
atoms in viewer using extruded geometries
   \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : ExtrudeHydrogenBonds
   \nCommand : extrudeHBonds
   \nSynopsis:\n
        None <- extrudeHBonds(nodes, shape2D=None, capsFlag=0, **kw)
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def onAddCmdToViewer(self):
        self.spacing = 0.4
        self.geoms = []
        self.color = (0,1,1)
        # Create a ColorChooser.
        self.palette = ColorChooser(commands=self.color_cb,
                    exitFunction = self.hidePalette_cb)
        # pack
        self.palette.pack(fill='both', expand=1)
        # hide it 
        self.palette.hide()
        #self.palette.exit()

    def hidePalette_cb(self, event=None):
        self.palette.hide()

    def __call__(self, nodes, shape2D=None, capsFlag=0,**kw):
        """
        None <- extrudeHBonds(nodes, shape2D=None, capsFlag=0, **kw)
        """
        if type(nodes) is StringType:
            self.nodeLogString = "'"+nodes+"'"
        if shape2D==None:
            shape2D = Circle2D(radius=0.1)
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        nodes = nodes.findType(Atom)
        kw['capsFlag'] = capsFlag
        apply(self.doitWrapper, (nodes, shape2D), kw)


    def interpolate(self, pt1, pt2):
        length = dist(pt1, pt2)
        c1 = Numeric.array(pt1)
        c2 = Numeric.array(pt2)
        delta = (c2-c1)/(3.0)
        vertList = []
        for i in range(3):
            vertList.append((c1+i*delta).tolist())
        vertList.append(pt2)
        return vertList


    def updateDisplay(self):
        self.geoms = []
        atNames = []
        for b in self.hbonds:
            accAtCoords = getTransformedCoords(b.accAt)
            dAtCoords = getTransformedCoords(b.donAt)
            if b.hAt is not None:
                hAtCoords = getTransformedCoords(b.hAt)
                name = b.hAt.full_name()
            else:
                name = b.donAt.full_name()
            if not hasattr(b, 'spline'):
                #make one
                if b.hAt is not None:
                    #name = b.hAt.full_name()
                    coords = self.interpolate(hAtCoords, accAtCoords)
                    #coords = self.interpolate(b.hAt.coords, b.accAt.coords)
                else:
                    #name = b.donAt.full_name()
                    coords = self.interpolate(dAtCoords, accAtCoords)
                    #coords = self.interpolate(b.donAt.coords, b.accAt.coords)
                nStr = name + ' 1'
                atNames.append((nStr,None))
                b.spline = SplineObject(coords, name = name,
                                    nbchords = 4, interp = 'interpolation',
                                    continuity= 2, closed=0)
                smooth = b.spline.smooth
            else:
                nStr = name + ' %d'%b.g.visible
                atNames.append((nStr,None))
            if hasattr(b,'exVert1'):
                name = b.exVert1.full_name()
                coords1= b.exVert1.coords
            elif b.hAt is not None:
                name = b.hAt.full_name()
                coords1= hAtCoords
            else:
                name = b.donAt.full_name()
                coords1= dAtCoords
            if hasattr(b,'exVert2'):
                coords2= b.exVert2.coords
            else:
                coords2= accAtCoords

            coords = self.interpolate(coords1, coords2)
            b.spline = SplineObject(coords, name = name,
                                nbchords = 4, interp = 'interpolation',
                                continuity= 2, closed=0)
            smooth = b.spline.smooth
            if hasattr(b, 'g'):
                self.vf.GUI.VIEWER.RemoveObject(b.g)
            name = b.spline.name[-8:]+'_hbond'
            b.g = GleExtrude(name=name, visible=1, 
                             inheritMaterial=0,
                             culling=GL.GL_NONE,
                             materials = (self.color,))
            self.vf.GUI.VIEWER.AddObject(b.g)
            b.g.culling = GL.GL_NONE
            self.geoms.append(b.g)
            ctlAtmsInSel = AtomSet([b.donAt, b.accAt])
            ctlAtms = AtomSet([b.donAt, b.accAt])
            b.g.spline = (b.spline, ctlAtmsInSel, ctlAtms)

            # need to get new contourPoints and new contourNormals
            b.g.shape2D = self.shape
            contpts = Numeric.array(b.g.shape2D.contpts)
            contourPoints = contpts[:,:2]
            contnorm = Numeric.array(b.g.shape2D.contnorm)
            contourNormals = contnorm[:,:2]
            b.g.Set(trace3D = Numeric.array((b.spline.smooth),'f'),
                    shape2D = self.shape,
                    contourUp = (0.,0.,1.),
                    inheritMaterial=0,
                    materials = (self.color,), visible=1,
                    capsFlag=self.capsFlag, tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        return atNames


    def doit(self, nodes, shape2D, capsFlag = 0):
        #extrude
        self.shape = shape2D
        self.capsFlag = capsFlag
        hats = AtomSet(nodes.get(lambda x: hasattr(x, 'hbonds')))
        hbonds = []
        for h in hats:
            for b in h.hbonds:
                if h == b.donAt:
                    b.visible = 1
                    hbonds.append(b)
        self.hbonds = hbonds
        atNames = self.updateDisplay()
        if not hasattr(self, 'ifd2'):
            ifd = self.ifd2=InputFormDescr(title = 'Show Extruded Hydrogen Bonds')
            ifd.append({'name': 'hbondLabel',
                'widgetType': Tkinter.Label,
                'wcfg':{'text': str(len(atNames)) + ' Atoms in hbonds:\n(1=visible, 0 not visible)'},
                'gridcfg':{'sticky': 'wens', 'columnspan':2}})

            ifd.append({'name': 'atsLC',
                'widgetType':ListChooser,
                'wcfg':{
                    'entries': atNames,
                    'mode': 'single',
                    'title': '',
                    'command': CallBackFunction(self.showHBondLC, atNames),
                    'lbwcfg':{'height':5, 
                        'selectforeground': 'red',
                        'exportselection': 0,
                        'width': 30},
                },
                'gridcfg':{'sticky':'wens', 'row':2,'column':0, 'columnspan':2}})
            ifd.append({'name':'changeColorBut',
                'widgetType':Tkinter.Button,
                'wcfg': { 'text':'Choose color',
                    'command': self.changeColor},
                'gridcfg':{'sticky':'wes'}})
            ifd.append({'name':'changeVertsBut',
                'widgetType':Tkinter.Button,
                'wcfg': { 'text':'Set anchors',
                    'command': self.changeDVerts},
                'gridcfg':{'sticky':'wens','row':-1,'column':1}})
            ifd.append({'name':'closeBut',
                'widgetType':Tkinter.Button,
                'wcfg': { 'text':'Dismiss',
                    'command': self.dismiss_cb},
                'gridcfg':{'sticky':'wens','columnspan':2}})
            self.form  = self.vf.getUserInput(ifd, modal=0, blocking=0,
                                              width=350, height=290)
            self.form.root.protocol('WM_DELETE_WINDOW',self.dismiss_cb)
            self.lb = self.ifd2.entryByName['atsLC']['widget'].lb


    def updateExtrusion_cb(self, event=1):
        #REDO DISPLAY HERE!!
        self.updateDisplay()


    def changeDVerts(self, event=None):
        #for all residues in hbonds, pick new donorAttachment
        # and new acceptorAttachment
        entries = []
        ns = ['N','C','O','CA','reset']
        for n in ns:
            entries.append((n, None))
        ifd3 = self.ifd3=InputFormDescr(title = 'Set Anchor Atoms')
        ifd3.append({'name': 'datsLC',
            'widgetType':ListChooser,
            'wcfg':{
                'entries': entries,
                'mode': 'single',
                'title': 'Donor Anchor',
                'command': CallBackFunction(self.setDVerts, entries),
                'lbwcfg':{'height':5, 
                    'selectforeground': 'red',
                    'exportselection': 0,
                    'width': 30},
            },
            'gridcfg':{'sticky':'wens', 'columnspan':2}})
        ifd3.append({'name': 'aatsLC',
            'widgetType':ListChooser,
            'wcfg':{
                'entries': entries,
                'mode': 'single',
                'title': 'Acceptor Anchor',
                'command': CallBackFunction(self.setAVerts, entries),
                'lbwcfg':{'height':5, 
                    'selectforeground': 'red',
                    'exportselection': 0,
                    'width': 30},
            },
            'gridcfg':{'sticky':'wens', 'columnspan':2}})
        ifd3.append({'name':'acceptBut',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Update extrusion',
                'command': self.updateExtrusion_cb},
            'gridcfg':{'sticky':'wens'}})
        ifd3.append({'name':'doneBut',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Done',
                'command': self.closeChangeDVertLC},
            'gridcfg':{'sticky':'wens'}})
        self.form3 = self.vf.getUserInput(self.ifd3, modal=0, blocking=0)
        self.form3.root.protocol('WM_DELETE_WINDOW',self.closeChangeDVertLC)


    def setDVerts(self, entries, event=None):
        if not hasattr(self, 'ifd3'):
            self.changeDVerts()
        lb = self.ifd3.entryByName['datsLC']['widget'].lb
        if lb.curselection() == (): return
        atName = lb.get(lb.curselection())
        ind = int(lb.curselection()[0])
        for b in self.hbonds:
            ats = b.donAt.parent.atoms.get(lambda x, atName=atName: x.name==atName)
            if ats is None:
                if b.hAt is not None: at = b.hAt
                else: at = b.donAt
            else:
                at = ats[0]
            b.exVert1 = at
        #REDO DISPLAY HERE!!
        #self.updateDisplay()
        

    def setAVerts(self, entries, event=None):
        if not hasattr(self, 'ifd3'):
            self.changeDVerts()
        lb = self.ifd3.entryByName['aatsLC']['widget'].lb
        if lb.curselection() == (): return
        atName = lb.get(lb.curselection())
        ind = int(lb.curselection()[0])
        for b in self.hbonds:
            ats = b.accAt.parent.atoms.get(lambda x, atName=atName: x.name==atName)
            if ats is None:
                at = b.accAt
            else:
                at = ats[0]
            b.exVert2 = at
        #REDO DISPLAY HERE!!
        #self.updateDisplay()


    def closeChangeDVertLC(self, event=None):
        if hasattr(self, 'ifd3'):
            delattr(self, 'ifd3')
        if hasattr(self, 'form3'):
            self.form3.destroy()


    def dismiss_cb(self, event=None, **kw):
        #extrudeHbonds
        for g in self.geoms:
            g.Set(visible=0, tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        if hasattr(self, 'ifd2'):
            delattr(self, 'ifd2')
        if hasattr(self, 'form3'):
            self.form3.destroy()
            delattr(self, 'form3')
        if hasattr(self, 'form'):
            self.form.destroy()
            delattr(self, 'form')
        if hasattr(self, 'palette'):
            self.palette.hide()
            #self.palette.exit()


    def color_cb(self, colors):
        self.color = colors[:3]
        for g in self.geoms:
            g.Set(materials = (self.color,), inheritMaterial=0,
                  tagModified=False)
        self.vf.GUI.VIEWER.Redraw()


    def changeColor(self, event=None):
        #col = self.palette.display(callback=self.color_cb, modal=1)
        if not hasattr(self, 'palette') or not self.palette.master.winfo_exists():
            self.palette = ColorChooser(commands=self.color_cb,
                        exitFunction = self.hidePalette_cb)
            # pack
            self.palette.pack(fill='both', expand=1)
            #??rh WHY hide it??
            #self.palette.hide()
        if not self.palette.master.winfo_ismapped():
            self.palette.master.deiconify()


    def showHBondLC(self, atName, event=None):
        #toggle on and off displaying the hbond
        #find the bond and Set its visible field
        #CHANGE ENTRY HERE!!!!
        for n in self.lb.curselection():
            #n in ('0','1','2')
            entry = self.lb.get(n)
            name = entry[:-2]
            #at = self.vf.Mols.NodesFromName(name)[0]
            #at = ats[0]
            ats = self.vf.Mols.NodesFromName(name)
            #to deal with two atoms with the exact same name:
            if len(ats)>1:
                for a in ats:
                    if hasattr(a, 'hbonds'):
                        at = a
                        break
            b = at.hbonds[0]
            b.g.Set(visible = not(b.g.visible), tagModified=False)
            if b.g.visible:
                entry = name + ' 1'
            else:
                entry = name + ' 0'
            self.lb.delete(n)
            self.lb.insert(n, entry)
            self.vf.GUI.VIEWER.Redraw()


    def guiCallback(self):
        # Write a shape chooser method that should be reused in
        # secondaryStructureCommands, CATrace commands, and splineCommands.
        if not len(self.vf.Mols):
            self.warningMsg('no molecules in viewer')
            return 
        idf = InputFormDescr(title='Extrude Spline')
        # List Chooser for the shape to extrude
        entries = [('rectangle',None),('circle',None),
                   ('ellipse',None),
                   ('square',None),('triangle',None)
                   ]

        idf.append({'name':'shape',
                    'widgetType':ListChooser,
                    'defaultValue':'circle',
                    'wcfg':{'entries': entries,
                            'lbwcfg':{'height':5,'exportselection':0},
                            'title':'Choose a shape to extrude'},
                    'gridcfg':{'sticky':'wens'}
                    })
        typeshape = self.vf.getUserInput(idf)
        if typeshape == {} or typeshape['shape'] == []: return
        
 
        ########################################################
        
        # Shape is a Rectangle
        if typeshape['shape'][0]=='rectangle':
            idf = InputFormDescr(title ="Rectangle size :")
            idf.append( {'name': 'width',
                         'widgetType':ExtendedSliderWidget,
                         'wcfg':{'label': 'Width',
                                 'minval':0.05,'maxval':3.0 ,
                                 'init':1.2,
                                 'labelsCursorFormat':'%1.2f',
                                 'sliderType':'float',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                     'gridcfg':{'columnspan':2,'sticky':'we'}
                     })

            idf.append( {'name': 'height',
                         'widgetType':ExtendedSliderWidget,
                         'wcfg':{'label': 'Height',
                                 'minval':0.05,'maxval':3.0 ,
                                 'init':0.4,
                                 'labelsCursorFormat':'%1.2f',
                                 'sliderType':'float',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                     'gridcfg':{'columnspan':2,'sticky':'we'}
                         })

            #idf.append({'name':'frontcap',
                        #'widgetType':Tkinter.Checkbutton,
                        #'defaultValue':1,'type':float,
                        #'wcfg':{'text':'front cap',
                                #'state': 'disabled',
                                #'variable': Tkinter.IntVar()},
                        #'gridcfg':{'sticky':'we'}})

            idf.append({'name':'caps',
                        'widgetType':Tkinter.Checkbutton,
                        'defaultValue':1,
                        'wcfg':{'text':'Caps',
                                'variable': Tkinter.IntVar()},
                        'gridcfg':{'sticky':'we','row':-1}})

            val = self.vf.getUserInput(idf)
            if val:
                shape = Rectangle2DDupRectangle2D(width = val['width'],
                                      height = val['height'],
                                      vertDup=1, firstDup=1)
                capsFlag = val['caps']

        # Shape is a Circle:
        elif typeshape['shape'][0]=='circle':
            idf = InputFormDescr(title="Circle size :")

            idf.append( {'name': 'radius',
                         'widgetType':ExtendedSliderWidget,
                         'wcfg':{'label': 'Radius',
                                 'minval':0.05,'maxval':3.0 ,
                                 'init':0.2,
                                 'labelsCursorFormat':'%1.2f',
                                 'sliderType':'float',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                     'gridcfg':{'columnspan':2,'sticky':'we'}
                     })

            idf.append({'name':'caps',
                        'widgetType':Tkinter.Checkbutton,
                        'defaultValue':1,
                        'wcfg':{'text':'Caps',
                                'variable': Tkinter.IntVar()},
                        'gridcfg':{'sticky':'we'}})

            val = self.vf.getUserInput(idf)
            if val:
                shape = Circle2D(radius=val['radius'], firstDup = 1)
                capsFlag = val['caps']

        # Shape is an Ellipse
        elif typeshape['shape'][0]=='ellipse':
            idf = InputFormDescr(title="Ellipse demi grand Axis and demi small axis :")

            idf.append( {'name': 'grand',
                         'widgetType':ExtendedSliderWidget,
                         'wcfg':{'label': 'demiGrandAxis',
                                 'minval':0.05,'maxval':3.0 ,
                                 'init':0.5,
                                 'labelsCursorFormat':'%1.2f',
                                 'sliderType':'float',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                     'gridcfg':{'columnspan':2,'sticky':'we'}
                     })
            idf.append( {'name': 'small',
                         'widgetType':ExtendedSliderWidget,
                         'wcfg':{'label': 'demiSmallAxis',
                                 'minval':0.05,'maxval':3.0 ,
                                 'init':0.2,
                                 'labelsCursorFormat':'%1.2f',
                                 'sliderType':'float',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                     'gridcfg':{'columnspan':2,'sticky':'we'}
                     })

            idf.append({'name':'caps',
                        'widgetType':Tkinter.Checkbutton,
                        'defaultValue':1,
                        'wcfg':{'text':'Caps ',
                                'variable': Tkinter.IntVar()},
                        'gridcfg':{'sticky':'we','row':-1}})

            val = self.vf.getUserInput(idf)
            if val:
                shape = Ellipse2D(demiGrandAxis= val['grand'],
                                  demiSmallAxis=val['small'], firstDup=1)
                capsFlag = val['caps']
                
        # Shape is a Square:
        elif typeshape['shape'][0]=='square':

            idf = InputFormDescr(title="Square size :")
            idf.append( {'name': 'sidelength',
                         'widgetType':ExtendedSliderWidget,
                         'wcfg':{'label': 'Length of side:',
                                 'minval':0.05,'maxval':3.0 ,
                                 'init':0.5,
                                 'labelsCursorFormat':'%1.2f',
                                 'sliderType':'float',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                     'gridcfg':{'columnspan':2,'sticky':'we'}
                     })

            idf.append({'name':'caps',
                        'widgetType':Tkinter.Checkbutton,
                        'defaultValue':1,
                         'wcfg':{'text':'Caps',
                                 'variable': Tkinter.IntVar()},
                        'gridcfg':{'sticky':'we'}})

            val = self.vf.getUserInput(idf)
            
            if val:
                shape = Square2D(side=val['sidelength'], firstDup=1, vertDup=1)
                capsFlag = val['caps']

        # Shape is a Triangle:
        elif typeshape['shape'][0]=='triangle':

            idf = InputFormDescr(title="Triangle size :")
            idf.append( {'name': 'sidelength',
                         'widgetType':ExtendedSliderWidget,
                         'wcfg':{'label': 'Length of side:    ',
                                 'minval':0.05,'maxval':3.0 ,
                                 'init':0.5,
                                 'labelsCursorFormat':'%1.2f',
                                 'sliderType':'float',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                     'gridcfg':{'columnspan':2,'sticky':'we'}
                     })

            idf.append({'name':'caps',
                        'widgetType':Tkinter.Checkbutton,
                        'defaultValue':1,
                        'wcfg':{'text':'Caps',
                                'variable': Tkinter.IntVar()},
                        'gridcfg':{'sticky':'we'}})


            val = self.vf.getUserInput(idf)
            if val:
                shape = Triangle2D(side=val['sidelength'], firstDup=1,
                                   vertDup=1)
                capsFlag = val['caps']

        else: return

        if val:
            nodes = self.vf.getSelection()
            if not len(nodes): return 'ERROR'
            nodes = nodes.findType(Atom)
            self.doitWrapper(nodes, shape, capsFlag = capsFlag)

ExtrudeHydrogenBondsGuiDescr = {'widgetType':'Menu',
                                'menuBarName':'menuRoot',
                                'menuButtonName':'Hydrogen Bonds',
                                'menuEntryLabel':'As Extruded Shapes',
                                'menuCascadeName': 'Display'}

ExtrudeHydrogenBondsGUI = CommandGUI()
ExtrudeHydrogenBondsGUI.addMenuCommand('menuRoot', 'Hydrogen Bonds',
        'As Extruded Shapes', cascadeName = 'Display')



class WriteAssemblyHBonds(MVCommand):
    """Command to write a file specifying >1 chain with hydrogen bonds. Chains which are hydrogen-bonded are written in one pdb file.  They may or may not be part of the same molecule.
    \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : WriteAssemblyHBonds
   \nCommand : writeAssemblyHB
   \nSynopsis:\n
        None <--- writeAssemblyHB(filename, nodes, **kw)
   \nRequired Arguments:\n     
        filename --- name of the hbond file\n
        nodes --- TreeNodeSet holding the current selection
    """


    def onAddCmdToViewer(self):
        self.PdbWriter = PdbWriter()


    def __call__(self, filename, nodes, **kw):
        """None <--- writeAssemblyHB(filename, nodes, **kw)
        \nfilename ---  name of the hbond file
        \nnodes --- TreeNodeSet holding the current selection """
        apply(self.doitWrapper, (filename, nodes,), kw)


    def fixIDS(self, chains):
        idList = chains.id
        ifd = self.ifd = InputFormDescr(title = "Set unique chain ids")
        ent_varDict = self.ent_varDict = {}
        cb_varDict = self.cb_varDict = {}
        self.nStrs = []
        self.entStrs = []
        self.chains = chains
        ifd.append({'name':'Lab1',
                    'widgetType':Tkinter.Label,
                    'text':'Current',
                    'gridcfg':{'sticky':'we'}})
        ifd.append({'name':'Lab2',
                    'widgetType':Tkinter.Label,
                    'text':'New',
                    'gridcfg':{'sticky':'we', 'row':-1, 'column':1}})
        for ch in chains:
            idList = chains.id
            ct = idList.count(ch.id)
            if ct!=1:
                for i in range(ct-1):
                    ind = idList.index(ch.id)
                    idList[ind] = ch.id+str(i)
        for i in range(len(chains)):
            chid = idList[i]
            ch = chains[i]
            nStr = chid+'_lab'
            self.nStrs.append(nStr)
            entStr = chid+'_ent'
            self.entStrs.append(entStr)
            newEntVar = ent_varDict[ch] = Tkinter.StringVar()
            newEntVar.set(ch.id)
            newCbVar = cb_varDict[ch] = Tkinter.IntVar()
            ifd.append({'name':nStr,
                    'widgetType':Tkinter.Label,
                    'text':ch.full_name(),
                    'gridcfg':{'sticky':'we'}})
            ifd.append({'name':entStr,
                'widgetType':Tkinter.Entry,
                'wcfg':{ 'textvariable': newEntVar, },
                'gridcfg':{'sticky':'we', 'row':-1, 'column':1}})
        vals = self.vf.getUserInput(self.ifd, modal=0, blocking=1, okcancel=1)
        if vals:
            for i in range(len(chains)):
                #CHECK for changes in id/name
                ch = chains[i]
                ll = ch.id
                wl = strip(vals[self.entStrs[i]])
                if ll!=wl:
                    print 'changed chain ', ch.full_name(), ' to ',  
                    ch.id = wl[0]
                    ch.name = wl[0]
                    print  ch.full_name()


    def writeHYDBNDRecords(self, atoms, fptr):
        for a in atoms:
            if not hasattr(a, 'hbonds'): continue 
            for b in a.hbonds:
                #only write a record if a is the donor 
                if b.donAt!=a: continue
                #columns 1-6 + spaces for columns 7-12
                s = 'HYDBND      '
                #columns 13-16 donor name
                #strip off altloc + save it
                nameStr, altLoc = self.PdbWriter.formatName(a)
                s = s + nameStr
                #column 17 donor altLoc indicator
                if altLoc: s = s + altLoc
                else: s = s + ' '
                #columns 18-20 donor parent name (residue type)
                #column 21 space + column 22 chain id
                s = s + a.parent.type + ' ' + a.parent.parent.id 
                #columns 23-27 donor parent number 
                #column 27 insertion code
                #column 28 space
                s = s + '%5d' %int(a.parent.number) + '  '

                # write the OPTIONAL hydrogen atom info
                hAt = b.hAt
                if hAt is None:
                    s = s + "              "
                else:
                    #columns 30-33 hydrogen atom name
                    nameStr, altLoc = self.PdbWriter.formatName(hAt)
                    s = s + nameStr
                    #column 34 hydrogen atom  altLoc indicator
                    if altLoc: s = s + altLoc
                    else: s = s + ' '
                    #column 35 space + column 36 chain id
                    s = s + ' ' + hAt.parent.parent.id
                    #columns 37-41 hydrogen atom parent number 
                    # nb: 42 would be insertion code then 43 a space
                    s = s + '%5d' %int(hAt.parent.number) + '  '

                # write the acceptor atom info
                acc = b.accAt 
                #columns 44-47 acceptor name
                nameStr, altLoc = self.PdbWriter.formatName(acc)
                s = s + nameStr
                #column 48 acceptor altLoc indicator
                if altLoc: s = s + altLoc
                else: s = s + ' '
                #columns 49-51 acceptor parent name (residue type)
                #column 52 space + column 53 chain id
                s = s + acc.parent.type + ' ' + acc.parent.parent.id
                #columns 54-58 acceptor parent number 
                # nb: 59 would be insertion code 
                # ???? non implemented->
                # 60-65 symmetry operator for 1st non-hyd. atom
                s = s + '%5d' %int(acc.parent.number) + '   \n'
                fptr.write(s)
        


    def doit(self, filename, nodes):
        #writeAssembly
        nodes = self.vf.expandNodes(nodes)
        if len(nodes)==0: return 'ERROR'
        nodes = nodes.findType(Atom)
        hbats = nodes.get(lambda x: hasattr(x, 'hbonds'))
        if hbats is None:
            self.warningMsg('no atoms with hbonds specified')
            return 'ERROR'
        #CHECK FOR presence and uniqueness of chain ids
        chains = nodes.parent.uniq().parent.uniq()
        fptr = open(filename, 'w')
        #to write:
        self.writeHYDBNDRecords(nodes, fptr)
        for ch in chains:
            for at in ch.residues.atoms:
                self.PdbWriter.write_atom(fptr, at)
            try:
                self.PdbWriter.write_TER(fptr, at)
            except:
                ostr =self.PdbWriter.defineTERRecord(at)
                fptr.write(ostr)
        fptr.close()

    
    def guiCallback(self):
        if not len(self.vf.Mols):
            self.warningMsg('no molecules in viewer')
            return 
        nodes = self.vf.getSelection()
        if not len(nodes): return None
        nodes = nodes.findType(Atom)
        hbats = AtomSet(nodes.get(lambda x: hasattr(x, 'hbonds')))
        if not hbats:
            self.warningMsg('no atoms with hbonds specified')
            return 'ERROR'
        chains = nodes.parent.uniq().parent.uniq()
        self.fixIDS(chains)
        file = self.vf.askFileSave(types=[('pdb files', '*.pdb'), 
                ('any', '*.*')], title="file to write hbonded chains\n(could be >1 molecule):")
        if file is None: return
        self.doitWrapper(file, nodes)


WriteAssemblyHBondsGuiDescr = {'widgetType':'Menu',
                                          'menuBarName':'menuRoot',
                                          'menuButtonName':'Hydrogen Bonds',
                                          'menuEntryLabel':'Write Assembly with Hbonds',
                                          'menuCascadeName': 'Assemblies'}

WriteAssemblyHBondsGUI = CommandGUI()
WriteAssemblyHBondsGUI.addMenuCommand('menuRoot', 'Hydrogen Bonds',
        'Write Hbonded Chains as 1 Mol', cascadeName='Assemblies')



class WriteIntermolHBonds(MVCommand):
    """Command to write files specifying intermolecular hydrogen bonds
   \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : WriteIntermolHBonds
   \nCommand : writeIntermolHB
   \nSynopsis:\n
        None <- writeIntermolHB(filename, nodes, **kw)
   \nRequired Arguments:\n       
        filename --- name of the hbond file\n
        nodes --- TreeNodeSet holding the current selection
    """


    def __call__(self, filename, nodes, **kw):
        """None <- writeIntermolHB(filename, nodes, **kw)
        \nfilename --- name of the hbond file
        \nnodes --- TreeNodeSet holding the current selection """
        apply(self.doitWrapper, (filename, nodes,), kw)


    def doit(self, filename, nodes):
        #writeIntermolHBonds
        nodes = self.vf.expandNodes(nodes)
        if len(nodes)==0: return 'ERROR'
        nodes = nodes.findType(Atom)
        hbats = AtomSet(nodes.get(lambda x: hasattr(x, 'hbonds')))
        if not hbats:
            self.warningMsg('no atoms with hbonds specified')
            return 'ERROR'
        bnds = []
        for at in hbats:
            for b in at.hbonds:
                if b.donAt.top!=b.accAt.top and b not in bnds:
                    bnds.append(b)
        if not len(bnds):
            self.warningMsg('no intermolecular hydrogen bonds in specified atoms')
            return 'ERROR'

        fptr = open(filename, 'w')
        for b in bnds:
            outstring = ''+b.donAt.full_name() + ',' + b.accAt.full_name()
            if b.hAt is not None:
                outstring = outstring + ',' + b.hAt.full_name()
            outstring = outstring + '\n'
            fptr.write(outstring)
        fptr.close()

    
    def guiCallback(self):
        if not len(self.vf.Mols):
            self.warningMsg('no molecules in viewer')
            return 
        file = self.vf.askFileSave(types=[('hbnd files', '*.hbnd'), 
                ('any', '*.*')], title="file to write intermolecular hbonds:")
        if file is None: return
        nodes = self.vf.getSelection()
        if not len(nodes): return None
        self.doitWrapper(file, nodes)

WriteIntermolHBondsGuiDescr = {'widgetType':'Menu',
                                          'menuBarName':'menuRoot',
                                          'menuButtonName':'Hydrogen Bonds',
                                          'menuEntryLabel':'Write Intermolecular Hbonds',
                                          'menuCascadeName': 'Assemblies'}

WriteIntermolHBondsGUI = CommandGUI()
WriteIntermolHBondsGUI.addMenuCommand('menuRoot', 'Hydrogen Bonds',
        'Write Intermolecular Hbonds', cascadeName='Assemblies')



class ReadIntermolHBonds(MVCommand):
    """Command to read files specifying intermolecular hydrogen bonds
   \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : ReadIntermolHBonds
   \nCommand : readIntermolHB
   \nSynopsis:\n
        None <--- readIntermolHB(filename, nodes, **kw)
   \nRequired Arguments:\n
        filename --- name of the hbond file
    """


    def __call__(self, filename, **kw):
        """None <--- readIntermolHB(filename, nodes, **kw)
        \nfilename --- name of the hbond file"""
        if not os.path.exists(filename):
            raise IOError
        apply(self.doitWrapper, (filename,), kw)


    def doit(self, filename):
        #read IntermolHBonds
        fptr = open(filename, 'r')
        allLines = fptr.readlines()
        fptr.close()
        ctr = 0
        for line in allLines:
            lList = split(line,',')
            donAt = self.vf.Mols.NodesFromName(lList[0])
            if donAt is None:
                msg = donAt + ' not in mv.allAtoms'
                self.warningMsg(msg)
                return 'ERROR'
            else:
                donAt = donAt[0]
            if len(lList)==2:
                accAt = self.vf.Mols.NodesFromName(lList[1][:-1])
            else:
                accAt = self.vf.Mols.NodesFromName(lList[1])
            if accAt is None:
                msg = accAt + ' not in mv.allAtoms'
                self.warningMsg(msg)
                return 'ERROR'
            else:
                accAt = accAt[0]
            if len(lList)==3:
                #there is a newlinecharacter
                hAt = self.vf.Mols.NodesFromName(lList[2][:-1])
                if hAt is None:
                    msg = hAt + ' not in mv.allAtoms'
                    self.warningMsg(msg)
                    return 'ERROR'
                else:
                    hAt = hAt[0]
            else: hAt = None

            #at this point build a hbond
            newHB = HydrogenBond(donAt, accAt, hAt)
            for at in [donAt, accAt]:
                if hasattr(at, 'hbonds'):
                    at.hbonds.append(newHB)
                else:
                    at.hbonds = [newHB]
            if hAt is not None:
                hAt.hbonds = [newHB]
            ctr = ctr + 1
        msg = 'built '+str(ctr) + ' intermolecular hydrogen bonds'
        self.warningMsg(msg)

    
    def guiCallback(self):
        if not len(self.vf.Mols):
            self.warningMsg('no molecules in viewer')
            return 
        file = self.vf.askFileOpen(types=[('hbnd files', '*.hbnd'), 
                ('any', '*.*')], title="intermolecular hbonds file:")
        if file is None: return
        apply(self.doitWrapper, (file,), {})


ReadIntermolHBondsGuiDescr = {'widgetType':'Menu',
                                          'menuBarName':'menuRoot',
                                          'menuButtonName':'Hydrogen Bonds',
                                          'menuEntryLabel':'Read Intermolecular Hbonds',
                                          'menuCascadeName': 'Assemblies'}

ReadIntermolHBondsGUI = CommandGUI()
ReadIntermolHBondsGUI.addMenuCommand('menuRoot', 'Hydrogen Bonds',
        'Read Intermolecular Hbonds', cascadeName='Assemblies')



class AddHBondCommandGUICommand(MVCommand, MVAtomICOM):
    """GUI command wrapper for AddHBondCommand which allows user to add hbonds between selected atoms. Hydrogen bonds are built assuming user picked hydrogen atom (or donor atom if there is no hydrogen atom) first followed by the acceptor atom.
   \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : AddHBondCommandGUICommand
   \nCommand : addHBondGC
   \nSynopsis:\n 
        None<---addHBondGC(atoms)
   \nRequired Arguments:\n     
        atoms ---  atom(s)
    """
    
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        MVAtomICOM.__init__(self)
        self.atomList = AtomSet([])
        self.undoAtList = AtomSet([])
        self.save = None


    def onRemoveObjectFromViewer(self, obj):
        removeAts = AtomSet([])
        for at in self.atomList:
            if at in obj.allAtoms:
                removeAts.append(at)
        self.atomList = self.atomList - removeAts
        removeAts = AtomSet([])
        for at in self.undoAtList:
            if at in obj.allAtoms:
                removeAts.append(at)
        self.undoAtList = self.undoAtList - removeAts
        self.update()


    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('setICOM'):
            self.vf.loadCommand('interactiveCommands', 'setICOM', 'Pmv',
                                topCommand=0) 
        miscGeom = self.vf.GUI.miscGeom
        hbond_geoms = check_hbond_geoms(self.vf.GUI)
        self.masterGeom = Geom('addHBondGeoms',shape=(0,0), 
                                pickable=0, protected=True)
        self.masterGeom.isScalable = 0
        self.vf.GUI.VIEWER.AddObject(self.masterGeom, parent=hbond_geoms)
        self.spheres = Spheres(name='addHBondSpheres', shape=(0,3),
                               inheritMaterial=0,
                               radii=0.2, quality=15,
                               materials = ((1.,1.,0.),), protected=True) 
        self.vf.GUI.VIEWER.AddObject(self.spheres, parent=self.masterGeom)


    def __call__(self, atoms, **kw):
        """None<-addHBondGC(atoms)
        \natoms  : atom(s)"""
        if type(atoms) is StringType:
            self.nodeLogString = "'"+atoms+"'"
        ats = self.vf.expandNodes(atoms)
        if not len(ats): return 'ERROR'
        return apply(self.doitWrapper, (ats,), kw)


    def doit(self, ats):
        #addHBondGC
        #can only do it on first two picked
        if len(ats)>2:
            ats = ats[:2]
        for at in ats:
            #check for repeats of same atom
            lenAts = len(self.atomList)
            if lenAts and at==self.atomList[-1]:
                continue
            self.atomList.append(at)
            self.undoAtList.append(at)
            lenAts = len(self.atomList)
        self.update()
        #if only have one atom, there is nothing else to do
        if lenAts<2: return
        #now build hbonds between pairs of atoms
        atSet = self.atomList
        if lenAts%2!=0:
            atSet = atSet[:-1]
            #all pairs of atoms will be bonded
            #so keep only the last one
            self.atomList = atSet[-1:]
            lenAts = lenAts -1
        else:
            self.atomList = AtomSet([])
        newHB = self.vf.addHBond(atSet[0], atSet[1])
        #to update display, need to call appropriate commands
        geomList = [self.vf.showHBonds.lines, self.vf.hbondsAsSpheres.spheres]
        cmdList = [self.vf.showHBonds, self.vf.hbondsAsSpheres]
        #FIX THIS: extrude geoms are too slow
        #if len(self.vf.extrudeHBonds.geoms):
            #geomList.append(self.vf.extrudeHBonds.geoms[0])
            #cmdList.append(self.vf.extrudeHBonds)
        for i in range(len(geomList)):
            geom = geomList[i]
            cmd = cmdList[i]
            hats = AtomSet(self.vf.allAtoms.get(lambda x: hasattr(x,'hbonds')))
            if len(geom.vertexSet):
                #first call dismiss_cb???
                apply(cmd.dismiss_cb,(),{})
                d = {}
                d['topCommand']=0
                #update a visible geometry here
                apply(cmd,(hats,), d)
        self.update()



    def setupUndoAfter(self, ats, **kw):
        lenUndoAts = len(self.undoAtList)
        lenAts = len(ats)
        if lenAts==1:
            #after adding 1 self.atomList would be 1 or 0
            if len(self.atomList)==1:
                s = '0'
                ustr='"c=self.addHBondGC;c.atomList=c.atomList[:'+s+'];c.undoAtList=c.undoAtList[:-1];c.update()"'
            else:
                ind = str(lenUndoAts - 2)
                ustr = '"c=self.addHBondGC;nodes=self.expandNodes('+'\''+self.undoAtList[-2:].full_name()+'\''+'); self.removeHBondGC(nodes, topCommand=0);c.atomList=nodes[:1];c.undoAtList=c.undoAtList[:'+ind+'];c.update()"'
        elif lenUndoAts>lenAts:
            ustr='"c=self.addHBondGC;nodes=self.expandNodes('+'\''+ats.full_name()+'\''+');self.removeHBondGC(nodes, topCommand=0);c.undoAtList=c.undoAtList[:'+str(lenAts)+']"'
        else:
            ustr='"c=self.addHBondGC;nodes=self.expandNodes('+'\''+ats.full_name()+'\''+');self.removeHBondGC(nodes, topCommand=0);c.undoAtList=c.undoAtList[:0]"'
        if len(self.atomList) and lenAts>1:
            atStr = self.atomList.full_name()
            estr = ';nodes=self.expandNodes('+'\''+self.atomList.full_name()+'\''+');c.atomList=nodes;c.update()"'
            ustr = ustr + estr
        self.undoCmds = "exec("+ustr+")"


    def update(self, event=None):
        if not len(self.atomList):
            self.spheres.Set(vertices=[], tagModified=False)
            self.vf.labelByExpression(self.atomList, negate=1, topCommand=0)
            self.vf.GUI.VIEWER.Redraw()
            return
        self.lineVertices=[]
        #each time have to recalculate lineVertices
        for at in self.atomList:
            c1 = getTransformedCoords(at)
            self.lineVertices.append(tuple(c1))
        self.spheres.Set(vertices=self.lineVertices, tagModified=False)
        self.vf.labelByExpression(self.atomList,
                                  function = 'lambda x: x.full_name()',
                                  lambdaFunc = 1,
                                  textcolor = 'yellow',
                                  format = '', negate = 0,
                                  location = 'Last', log = 0,
                                  font = 'arial1.glf', only = 1,
                                  topCommand=0)
        #setting spheres doesn't trigger redraw so do it explicitly
        self.vf.GUI.VIEWER.Redraw()


    def guiCallback(self, event=None):
        self.save = self.vf.ICmdCaller.commands.value["Shift_L"]
        self.vf.setICOM(self, modifier="Shift_L", topCommand=0)


    def startICOM(self):
        self.vf.setIcomLevel( Atom )




AddHBondGuiDescr = {'widgetType':'Menu',
                              'menuBarName':'menuRoot',
                              'menuButtonName':'Hydrogen Bonds',
                              'menuEntryLabel':'Add Hydrogen Bonds',
                              'menuCascadeName': 'Edit'}

AddHBondCommandGUICommandGUI=CommandGUI()
AddHBondCommandGUICommandGUI.addMenuCommand('menuRoot', 'Hydrogen Bonds', 'Add Hydrogen Bonds', cascadeName='Edit')



class AddHBondCommand(MVCommand):
    """AddHBondCommand allows user to add hydrogen bonds between pairs of atoms.
    \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : AddHBondCommand
   \nCommand : addHBond
   \nSynopsis:\n
        None<---addHBond(atom1, atom2)
   \nRequired Arguments:\n       
        atom1 --- first atom\n
        atom2 --- second atom
    """

    def setupUndoBefore(self, atom1, atom2):
        self.addUndoCall((atom1.full_name(),atom2.full_name()),{'topCommand':0}, 
                    self.vf.removeHBond.name)


    def undo(self, atom1, atom2, **kw):
        self.vf.removeHBond(atom1, atom2, topCommand=0)


    def __call__(self, atom1, atom2, **kw):
        """None<-addHBond(atom1, atom2)
        \natom1 --- first atom
        \natom2  --- second atom """
        ats = self.vf.expandNodes(atom1)
        if not len(ats): return 'ERROR'
        at1 = ats[0]
        ats = self.vf.expandNodes(atom2)
        if not len(ats): return 'ERROR'
        at2 = ats[0]
        #check that at1 and at2 are not already in an hbond
        if hasattr(at1, 'hbonds') and hasattr(at2, 'hbonds'):
            for b in at1.hbonds:
                if b.donAt==at2 or b.hAt==at2 or b.accAt==at2:
                    return 'ERROR'
            for b in at2.hbonds:
                if b.donAt==at2 or b.hAt==at2 or b.accAt==at2:
                    return 'ERROR'
        return apply(self.doitWrapper, (at1, at2), kw)


    def doit(self, at1, at2):
        #addHBond
        #this assumes atoms are picked in order
        #from donor to acceptor
        donAt = at1
        accAt = at1
        if at1.element=='H':
            hAt = at1
            accAt = at2
        elif at2.element=='H':
            hAt = at2
            accAt = at1
        else:
            hAt = None
        if hAt is not None :
            b = hAt.bonds[0]
            donAt = b.atom1
            if id(donAt)==id(hAt):
                donAt = b.atom2
        newHB = HydrogenBond( donAt, accAt, hAt=hAt)
        if not hasattr(accAt, 'hbonds'):
            accAt.hbonds=[]
        if not hasattr(donAt, 'hbonds'):
            donAt.hbonds=[]
        accAt.hbonds.append(newHB)
        donAt.hbonds.append(newHB)
        #hydrogens can have only 1 hbond
        if hAt is not None :
            hAt.hbonds = [newHB]
        return newHB



class RemoveHBondCommandGUICommand(MVCommand, MVBondICOM):
    """RemoveHBondCommandGUICommand allows user to remove hbonds between
    picked atoms.
   \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : RemoveHBondCommandGUICommand
   \nCommand : removeHBondGC
   \nSynopsis:\n
        None <- removeHBondGC(atoms, **kw)
   \nRequired Arguments:\n
        atoms: atoms to remove hbonds between
    """
       

    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('setICOM'):
            self.vf.loadCommand('interactiveCommands', 'setICOM', 'Pmv',
                                topCommand=0) 
        hbond_geoms = check_hbond_geoms(self.vf.GUI)
        self.masterGeom = Geom('removeBondGeoms',shape=(0,0), 
                                pickable=0, protected=True)
        self.masterGeom.isScalable = 0
        self.vf.GUI.VIEWER.AddObject(self.masterGeom, parent=hbond_geoms)
        self.spheres = Spheres(name='removeBondSpheres', shape=(0,3),
                               inheritMaterial=0,
                               radii=0.2, quality=15,
                               materials = ((1.,0.,0.),), protected=True) 
        self.vf.GUI.VIEWER.AddObject(self.spheres, parent=self.masterGeom)


    def __init__(self, func = None):
        MVCommand.__init__(self, func)
        MVBondICOM.__init__(self)
        self.pickLevel = 'parts'
        self.undoBondList = []
        self.save = None


    def guiCallback(self):
        self.save = self.vf.ICmdCaller.commands.value["Shift_L"]
        self.vf.setICOM(self, modifier="Shift_L", topCommand = 0)
        self.vf.setIcomLevel(Atom)

    def stop(self):
        self.done_cb()


    def getObjects(self, pick):
        for o, val in pick.hits.items(): ###loop over geometries
            primInd = map(lambda x: x[0], val)
            g = o.mol.geomContainer
            if g.geomPickToBonds.has_key(o.name):
                func = g.geomPickToBonds[o.name]
                if func: return func(o, primInd)
            else:
                l = []
                bonds = g.atoms[o.name].bonds[0]
                if not len(bonds): return BondSet()
                for i in range(len(primInd)):
                    l.append(bonds[int(primInd[i])])
                return BondSet(l)


    def dismiss(self):
        self.vf.setICOM(self.save, modifier="Shift_L", topCommand = 0)
        self.save = None
        self.done_cb()


    def done_cb(self):
        pass
        

    def __call__(self, atoms, **kw):
        """None <- removeHBondGC(atoms, **kw)
           atoms: atoms to remove hbonds between
           """
        if type(atoms) is StringType:
            self.nodeLogString = "'"+atoms+"'"
        ats = self.vf.expandNodes(atoms)
        if not len(ats): return 'ERROR'
        apply(self.doitWrapper, (ats,), kw)


    def doit(self, ats):
        #removeHBondGC
        hats = AtomSet(ats.get(lambda x: hasattr(x, 'hbonds')))
        if not len(hats): return 'ERROR'
        for at in hats:
            if not hasattr(at, 'hbonds'):
                continue
            if not len(at.hbonds):
                delattr(at, 'hbonds')
                continue
            for hbnd in at.hbonds:
                if at==hbnd.donAt:
                    if hbnd.accAt in hats:
                        self.vf.removeHBond(at, hbnd.accAt)
                elif at==hbnd.accAt:
                    if hbnd.donAt in hats:
                        self.vf.removeHBond(hbnd.donAt, at)
                    elif hbnd.hAt in hats:
                        self.vf.removeHBond(hbnd.hAt, at)
                else:
                    #in this case at is hydrogen atom of hbond
                    if hbnd.accAt in hats:
                        self.vf.removeHBond(at, hbnd.accAt)
        #FIX THIS: update the geoms as above in addHBonds
        #to update display, need to call appropriate commands
        geomList = [self.vf.showHBonds.lines, self.vf.hbondsAsSpheres.spheres]
        cmdList = [self.vf.showHBonds, self.vf.hbondsAsSpheres]
        #FIX THIS: extrude is too slow
        #if len(self.vf.extrudeHBonds.geoms):
            #geomList.append(self.vf.extrudeHBonds.geoms[0])
            #cmdList.append(self.vf.extrudeHBonds)
        for i in range(len(geomList)):
            geom = geomList[i]
            cmd = cmdList[i]
            hats = AtomSet(self.vf.allAtoms.get(lambda x: hasattr(x,'hbonds')))
            if len(geom.vertexSet):
                #first call dismiss_cb???
                apply(cmd.dismiss_cb,(),{})
                d = {}
                d['topCommand']=0
                #update visible geometry here
                apply(cmd,(hats,),d)


    def setupUndoAfter(self, ats, **kw):
        lenUndoAts = len(self.undoAtList)
        lenAts = len(ats)
        if lenAts==1:
            #after removing 1 self.atomList would be 1 or 0
            if len(self.atomList)==1:
                s = '0'
                ustr='"c=self.removeHBondGC;c.atomList=c.atomList[:'+s+'];c.undoAtList=c.undoAtList[:-1];c.update()"'
            else:
                ind = str(lenUndoAts - 2)
                ustr = '"c=self.removeHBondGC;nodes=self.expandNodes('+'\''+self.undoAtList[-2:].full_name()+'\''+'); self.addHBondGC(nodes, topCommand=0);c.atomList=nodes[:1];c.undoAtList=c.undoAtList[:'+ind+'];c.update()"'
        elif lenUndoAts>lenAts:
            ustr='"c=self.removeHBondGC;nodes=self.expandNodes('+'\''+ats.full_name()+'\''+');self.addHBondGC(nodes, topCommand=0);c.undoAtList=c.undoAtList[:'+str(lenAts)+']"'
        else:
            ustr='"c=self.removeHBondGC;nodes=self.expandNodes('+'\''+ats.full_name()+'\''+');self.addHBondGC(nodes, topCommand=0);c.undoAtList=c.undoAtList[:0]"'
        if len(self.atomList) and lenAts>1:
            atStr = self.atomList.full_name()
            estr = ';nodes=self.expandNodes('+'\''+self.atomList.full_name()+'\''+');c.atomList=nodes;c.update()"'
            ustr = ustr + estr
        self.undoCmds = "exec("+ustr+")"


RemoveHBondGuiDescr = {'widgetType':'Menu',
                              'menuBarName':'menuRoot',
                              'menuButtonName':'Hydrogen Bonds',
                              'menuEntryLabel':'Remove Hydrogen Bond',
                              'menuCascadeName': 'Edit'}


RemoveHBondCommandGUICommandGUI=CommandGUI()
RemoveHBondCommandGUICommandGUI.addMenuCommand('menuRoot', 'Hydrogen Bonds', 
        'Remove Hydrogen Bonds', cascadeName='Edit')



class RemoveHBondCommand(MVCommand):
    """RemoveHBondCommand allows user to remove hydrogen bonds between specified
    atoms.
   \nPackage : Pmv
   \nModule  : hbondCommands
   \nClass   : RemoveHBondCommand
   \nCommand : removeHBond
   \nSynopsis:\n
        None<-removeHBond(atom1, accAt)
   \nRequired Arguments:\n        
        atom1 --- donAt or hAt of bond\n
        accAt --- accAt of bond 
    """


    def setupUndoBefore(self, atom1, atom2):
        self.addUndoCall((atom1.full_name(),atom2.full_name()),{'topCommand':0}, 
                    self.vf.addHBond.name)


    def __call__(self, atom1, accAt, **kw):
        """None<-removeHBond(atom1, accAt)
        \natom1  --- donAt or hAt of bond
        \naccAt --- accAt of bond"""
        ats = self.vf.expandNodes(atom1)
        if not len(ats): return 'ERROR'
        at1 = ats[0]
        ats = self.vf.expandNodes(accAt)
        if not len(ats): return 'ERROR'
        accAt = ats[0]
        return apply(self.doitWrapper, (at1, accAt), kw)


    def doit(self, atom1, accAt):
        b = None
        for hb in atom1.hbonds:
            if hb.accAt == accAt:
                #found the bond to remove
                b = hb
        #if no bond exists between these atoms, return error
        if b is None:
            return 'ERROR'

        #only remove one bond here
        accAt.hbonds.remove(b)
        if not len(accAt.hbonds):
            delattr(accAt,'hbonds')
        hAt = b.hAt
        if hAt is not None:
            donAt = b.donAt
            hAt.hbonds.remove(b)
            delattr(hAt,'hbonds')
            donAt.hbonds.remove(b)
            if not len(donAt.hbonds):
                delattr(donAt,'hbonds')
        else:
            #in this case, atom1 was the donAt
            atom1.hbonds.remove(b)
            if not len(atom1.hbonds):
                delattr(atom1,'hbonds')
        del b
        return



commandList=[
    {'name':'getHBDonors','cmd':GetHydrogenBondDonors(), 'gui':None},
    {'name':'getHBAcceptors','cmd':GetHydrogenBondAcceptors(), 'gui':None},
    {'name':'getHBondEnergies','cmd':GetHydrogenBondEnergies(), 'gui': None},
    {'name':'showHBDA','cmd':ShowHBDonorsAcceptors(), 
            'gui':ShowHBDonorsAcceptorsGUI},
    {'name':'showHBonds','cmd':ShowHydrogenBonds(), 'gui':ShowHydrogenBondsGUI},
    {'name':'buildHBondsGC','cmd':BuildHydrogenBondsGUICommand(),
            'gui': BuildHydrogenBondsGUICommandGUI},
    {'name':'buildHBonds','cmd':BuildHydrogenBonds(), 'gui': None},
    {'name':'addHBondHsGC','cmd':AddHBondHydrogensGUICommand(),
            'gui': AddHBondHydrogensGUICommandGUI},
    {'name':'addHBondHs','cmd':AddHBondHydrogens(), 'gui': None},
    {'name':'hbondsAsSpheres','cmd':DisplayHBondsAsSpheres(),
            'gui':DisplayHBondsAsSpheresGUI},
    {'name':'hbondsAsCylinders','cmd':DisplayHBondsAsCylinders(),
            'gui':DisplayHBondsAsCylindersGUI},
    {'name':'extrudeHBonds','cmd':ExtrudeHydrogenBonds(), 'gui':ExtrudeHydrogenBondsGUI},
    {'name':'addHBondGC','cmd':AddHBondCommandGUICommand(),
     'gui': AddHBondCommandGUICommandGUI},
    {'name':'addHBond','cmd':AddHBondCommand(), 'gui': None},
    {'name':'removeHBondGC','cmd':RemoveHBondCommandGUICommand(),
     'gui': RemoveHBondCommandGUICommandGUI},
    {'name':'removeHBond','cmd':RemoveHBondCommand(), 'gui': None},
    {'name':'limitHBonds','cmd':LimitHydrogenBonds(), 'gui':LimitHydrogenBondsGUI},
    {'name':'readIntermolHBonds','cmd':ReadIntermolHBonds(), 
        'gui':ReadIntermolHBondsGUI},
    {'name':'writeIntermolHBonds','cmd':WriteIntermolHBonds(), 
        'gui':WriteIntermolHBondsGUI},
    {'name':'writeHBondAssembly','cmd':WriteAssemblyHBonds(), 
        'gui':WriteAssemblyHBondsGUI},

    ]



def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
