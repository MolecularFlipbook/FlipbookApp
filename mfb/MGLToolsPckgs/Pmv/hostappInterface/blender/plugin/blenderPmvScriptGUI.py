#!BPY

"""
Name: 'ePMV'
Blender: 249b
Group: 'System'
Tooltip: 'Molecular Viewer'
"""

__url__ = ["http://mgldev.scripps.edu/projects/ePMV/wiki/index.php/Main_Page",
           'http://mgldev.scripps.edu/projects/ePMV/update_notes.txt',
           'http://mgldev.scripps.edu/projects/ePMV/wiki/index.php/Citation_Information',]
__version__="0.0.2a"
__bpydoc__ = "ePMV v"+__version__
__bpydoc__+="""\
Use Blender as a molecular viewer
ePMV by Ludovic Autin,Graham Jonhson,Michel Sanner.
Develloped in the Molecular Graphics Laboratory directed by Arthur Olson.
"""

# -------------------------------------------------------------------------- 
# ***** BEGIN GPL LICENSE BLOCK ***** 
# 
# This program is free software; you can redistribute it and/or 
# modify it under the terms of the GNU General Public License 
# as published by the Free Software Foundation; either version 2 
# of the License, or (at your option) any later version. 
# 
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
# GNU General Public License for more details. 
# 
# You should have received a copy of the GNU General Public License 
# along with this program; if not, write to the Free Software Foundation, 
# Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA. 
# 
# ***** END GPL LICENCE BLOCK ***** 
# -------------------------------------------------------------------------- 
#general import
import sys
import os
import re
import shutil
from time import time
import time as T
import Blender
global MGL_ROOT
MGL_ROOT=""
def getMGL(filename):
        MGL_ROOT=filename
        print "whats upone",MGL_ROOT
        f=open(mgldirfile,'w')
        f.write(MGL_ROOT)
        f.close()
        
softdir = Blender.Get("homedir")
prefdir = Blender.Get('uscriptsdir')
if prefdir is None:
    prefdir = Blender.Get('scriptsdir')
mgldirfile=prefdir+os.sep+"mgltoolsdir"
personalize = False
if os.path.isfile(mgldirfile) :
    f=open(mgldirfile,'r')
    MGL_ROOT=f.readline()
    f.close()
else :
    personalize = True
    if len(MGL_ROOT) == 0 :    
        MGL_ROOT=Blender.Draw.PupStrInput("what is the path to MGLToolsPckgs?:", "untitled", 100)
        if not os.path.exists(MGL_ROOT):
            MGL_ROOT=Blender.Draw.PupStrInput("MGLToolsPckgs path:", "untitled", 100)
    if os.path.exists(MGL_ROOT):
        f=open(mgldirfile,'w')
        f.write(MGL_ROOT)
        f.close()
    
if len(MGL_ROOT):
    if sys.platform == 'win32':
    #need to patch MGLTools first
    #first patch MGLTools
    #check if we need to patch
        mgltoolsDir = MGL_ROOT+os.sep+"MGLToolsPckgs"
        patch=os.path.isfile(mgltoolsDir+os.sep+"patched")
        if not patch :
            import urllib
            import tarfile 
            print mgltoolsDir+os.sep
            patchpath = mgltoolsDir+os.sep
            URI="http://mgldev.scripps.edu/projects/ePMV/patchs/depdtPckgs.tar"
            tmpFileName = mgltoolsDir+os.sep+"depdtPckgs.tar"
            if not os.path.isfile(tmpFileName):
                urllib.urlretrieve(URI, tmpFileName)
                #geturl(URI, tmpFileName)
            TF=tarfile.TarFile(tmpFileName)
            TF.extractall(patchpath)
            #create the pacthed file
            f=open(mgltoolsDir+os.sep+"patched","w")
            f.write("MGL patched!")
            f.close()
#do I need to copy the file
    plugfile = prefdir+os.sep+"blenderPmvScriptGUI.py"
    print plugfile
    if not os.path.isfile(plugfile) :
        indir = MGL_ROOT+os.sep+"MGLToolsPckgs"+os.sep+"Pmv"+os.sep+"hostappInterface"+os.sep+\
                "blender"+os.sep+"plugin"+os.sep
        outdir = prefdir+os.sep
        print outdir
        files=[]
        files.append("blenderPmvScriptGUI.py")
        files.append("blenderPmvClientGUI.py") 
        files.append("epmv_blender_update.py")   
        for f in files : 
            shutil.copy (indir+f, outdir+f)
        print "copy"
sys.path.append(MGL_ROOT+'/MGLToolsPckgs')
if sys.platform == "win32":
    sys.path.append(MGL_ROOT+'/MGLToolsPckgs/PIL')
else :
    sys.path.insert(0,MGL_ROOT+'/lib/python2.5/site-packages')
    sys.path.append(MGL_ROOT+'/lib/python2.5/site-packages/PIL')

from Pmv.hostappInterface.blender.blenderAdaptor import blenderAdaptor
from Pmv.hostappInterface.blender import blenderHelper
from Pmv.moleculeViewer import EditAtomsEvent
from Pmv.hostappInterface import lightGridCommands as lG

from Pmv.hostappInterface.install_plugin import Installer

from MolKit.molecule import Atom
from MolKit.protein import ResidueSet,ResidueSetSelector
from Pmv.pmvPalettes import AtomElements
#Blender import 
from Blender import Registry
from Blender import BGL
from Blender import Image
import bpy

#extension
_AR=False
_AF=False
_modeller=False
_useModeller=False
_logCommand=False
_forceFetch=False

env = None #modeller env

listExtension=[]
listOptionsMenu=["Recent Files","load PDB","load Data"]
listHelp=["About ePMV","ePMV documentation","check fo update","Citation Information"]
listSelection=["Save Set","Rename Set","Delete Set"]

_inst=Installer(gui=False)
_inst.mgltoolsDir=MGL_ROOT
_inst.currDir=MGL_ROOT+os.sep+"MGLToolsPckgs"+os.sep+"Pmv"+os.sep+"hostappInterface"+os.sep

class ParameterModeller():
    def __init__(self):
        #minimize options
        #max_iterations=1000
        #md options
        #temperature=300, max_iterations=1000
        id=0
        self.NUMBERS = {"miniIterMax":{"id":id,"name":"max_it mini",'width':50,"height":10,"action":None,"value":Blender.Draw.Create(100.0)},
                        "mdIterMax":{"id":id+1,"name":"max_it MD",'width':50,"height":10,"action":None,"value":Blender.Draw.Create(100.0)},
                        "mdTemp":{"id":id+2,"name":"temp MD",'width':50,"height":10,"action":None,"value":Blender.Draw.Create(300.)}
                        }
        id = id + 3
        self.BTN = {"mini":{"id":id,"name":"minimize",'width':50,"height":10,"action":None,"value":Blender.Draw.Create(0)},
                    "md":{"id":id+1,"name":"MD",'width':50,"height":10,"action":None,"value":Blender.Draw.Create(0)},
                    "store":{"id":id+2,"name":"store",'width':100,"height":10,"action":None,"value":Blender.Draw.Create(0)}
                    }
        self.block=[]
        self.CreateLayout()

    def CreateLayout(self):
        ID=0
        title = "Options"
        #minimize otin/button
        for numb in self.NUMBERS:
            self.block.append( (self.NUMBERS[numb]["name"],self.NUMBERS[numb]['value'],0.0,1000.)  )
        for numb in self.BTN:
            self.block.append( (self.BTN[numb]["name"],self.BTN[numb]['value'],numb)  )
    

def checkExtension():
    global _modeller,_useModeller,_AF,_AR,_inst
    global listExtension
    _inst.getExtensionDirFromFile()
    for i,ext in enumerate(_inst.extensions):
        if _inst.extdir[i] not in sys.path :
            sys.path.append(_inst.extdir[i])
            if ext.lower() == 'modeller' :
                sys.path.append(_inst.extdir[i]+"/python2.5")
    if not _useModeller:
        try :
            import modeller
            _modeller = True
            #_useModeller = True #depend on the user preference by default True
            listExtension.append('modeller')
        except:
            print "noModeller"
    if not _AF:
        try :
            import AutoFill
            _AF = True
            listExtension.append('AutoFill')
        except:
            print "noAutoFill"
    if not _AR:
        try :
            import ARViewer
            _AR = True
            listExtension.append('ARViewer')
        except:
            print "noARViewer"

LOG = 0
VERBOSE = 0
TIMER = 1

selections={}

self=None
epmv=None
listExtension.append('Add Extension')
print "BEFORE"

def update_Registry():
   d = {}
   d['self'] = self
   d['epmv'] = epmv
   #if self.Mols : 
   #    if hasattr(self.Mols[0].geomContainer.geoms['cpk'],'obj') : 
   #        d['obj'] = self.Mols[0].geomContainer.geoms['cpk'].obj
   Blender.Registry.SetKey('bmv', d, False)

sc=Blender.Scene.GetCurrent()

rdict = Registry.GetKey('bmv', False) # True to check on disk also
print rdict
if rdict and 'self' in rdict.keys() : 
    self = rdict['self']
    epmv = rdict['epmv']
    if VERBOSE : print "redo"
    #print self,self.Mols.name
    if self == None :
        if VERBOSE : print "self none"
        epmv = blenderAdaptor(debug=0)
        self = epmv.mv     
        self.armObj = None
        self.selections=selections
        update_Registry()
    else : 
        if VERBOSE : 
            print "ok in registry ",self,self.Mols.name
            print self.Mols[0].geomContainer.masterGeom.chains_obj
else :
    if VERBOSE : print "no registration"
    epmv = blenderAdaptor(debug=0)
    self = epmv.mv
    self.armObj = None
    self.selections=selections
    update_Registry()

#check available extension
checkExtension()
    
Banner = Image.Load(MGL_ROOT+'/MGLToolsPckgs/Pmv/hostappInterface/images/banner.jpg')

if not hasattr(self ,'molDispl') : self.molDispl={}
if not hasattr(self,'MolSelection') : self.MolSelection={}
if not hasattr(self,'iMolData') : self.iMolData={}
#define the default options
epmv.use_progressBar = True
epmv.bicyl = True
epmv.doLight = True
epmv.doCamera = True

self.hostApp.driver.bicyl = True

strDataSupported = lG.getSupportedFormat()

if VERBOSE :  print self,self.Mols
selections=self.selections
RS=ResidueSetSelector()
Draw=Blender.Draw

stringName = Draw.Create("")
dataName = Draw.Create("")
Menupreset = Draw.Create(1)
ColorPreset1= Draw.Create(1)
ColorPreset2= Draw.Create(1)
ExportPreset= Draw.Create(1)
Shapepreset = Draw.Create(1)
stringSelection = Draw.Create("")
ColorMol= Draw.Create(1)
molPreset= Draw.Create(1)
keyPreset= Draw.Create(1)
#pmvcmds = bpy.data.texts.new('pythonscript.py')#Draw.Create("put python script or PMV commmands here")
#pmvcmds.write("'put python script or PMV commmands here'")

molMenu = {}

baseIndice=[50,100,150,200,250,300,350,400,450,500]
baseISel=[600,700,800,900,1000,1100,1200,1300]
check=599

line = [None,None,None,None,None,None,None,None,None,None,None,None,None,
        None,None,None,None,None,None,None]
init=50
step=30
line[0]=init
for i in range(1,len(line)):
    line[i]=line[i-1]+30

EV_BT_OK = 1
EV_BT_CANCEL = 2
EV_ST_PDBNAME = 3

EV_TG_BKBONE = 4
EV_TG_ARMATURE = 5
EV_TG_SURF = 6
EV_TG_VDW = 7
EV_ME_MESH = 8
EV_TG_SS = 9
EV_TG_BSTICK = 10
EV_TG_TUBE = 11
EV_TG_CAT = 12
EV_TG_COL1 = 13
EV_ME_COL = 14
EV_TG_COL2 = 15
EV_TG_JOIN1 = 16
EV_TG_JOIN2 = 17
EV_TG_JOIN3 = 18
EV_BT_EX = 19
EV_ME_EXPOR = 20
EV_ME_BEZIER = 21
EV_BT_LOAD = 22
EV_TG_DEL = 23
EV_ST_SELECTION = 24
EV_BT_ADD = 25
EV_BT_MODIF = 26
EV_TG_ONLY = 27
EV_BT_CHOOSE = 28
EV_CPKRAD = 29
EV_CPKSCALE = 30
EV_CPKOPT = 31
EV_MSOPT = 32
EV_BSOPT = 33
EV_CMSOPT = 34

EV_ST_DATA = 35
EV_BT_DLOAD = 36
EV_BT_DCHOOSE = 37
EV_DOPT = 38
EV_BT_EXECUTE = 39
EV_ST_PMV = 40

EV_BT_MENU=41
EV_BT_EXT=42
EV_BT_OPT=43
EV_BT_ABOUT=44

ev_del=100
ev_vdw=101
ev_surf=102
ev_cms=103
ev_bs=104
ev_ss=105
ev_col=106
ev_sel=107
ev_pcol=108
ev_data=109
ev_mol=110
ev_2key = 111
ev_meta = 112
ev_spline = 113
ev_key = 114

ev_slider=120
ev_mod=121
selColorPreset=Draw.Create(1)
dataMenu = Draw.Create(1)
data_slider = Draw.Create(0.)
data_start = Draw.Create(1)
data_end = Draw.Create(1)
data_step = Draw.Create(1)


LSURF=Draw.Create(0)#(0)
LCMS=Draw.Create(0)#(0)
LMETA=Draw.Create(0)#(0)
LSPLINE=Draw.Create(0)
LVDW=Draw.Create(0)#(0)
LSS=Draw.Create(0)#(0)
LBSTICK=Draw.Create(0)#(0)
LRIB=Draw.Create(0)#(0)
LCOLOR=(0)
LKEY=(0)

cpkopt={}
for k,v in self.displayCPK.lastUsedValues['default'].items():
    if type(v) == type(None) : continue
    elif type(v) == bool : cpkopt[k]=Draw.Create(int(v))
    else : cpkopt[k]=Draw.Create(v)

bsopt={}
for k,v in self.displaySticksAndBalls.lastUsedValues['default'].items():
    if type(v) == type(None) : continue
    elif type(v) == bool : bsopt[k]=Draw.Create(int(v))
    else : bsopt[k]=Draw.Create(v)
bsopt["ratio"] = Draw.Create(1.5)
bsopt['bScale']= Draw.Create(1.)

msmsopt={}
for k,v in self.computeMSMS.lastUsedValues['default'].items():
    if type(v) == type(None) : continue
    elif type(v) == bool : msmsopt[k]=Draw.Create(int(v))
    else : msmsopt[k]=Draw.Create(v)

cmsopt={}
cmsopt["iso"] = Draw.Create(7.1)
cmsopt["res"] = Draw.Create(-0.3)

ColorMol=Draw.Create(0.,0.,0.)
ColorSel=Draw.Create(0.,0.,0.)

BKBONE = 0
ARMATURE = 0
COARSE = 0
SURF = 0
VDW = 0
SS = 0
BSTICK = 0
TUBE = 0
CAT = 0
COLOR1=0
COLOR2=0
JOIN1=0
JOIN2=0
JOIN3=0
EXPORT=0
DASH=0
DEL=0
ONLY=0


stringMesh = ["Sphere","Cube","Mb"]
funcColor = [self.colorByAtomType,
             self.colorAtomsUsingDG,
             self.colorByProperty,
             self.colorByResidueType,
             self.colorResiduesUsingShapely,
             self.colorBySecondaryStructure,
             self.color,
             self.colorByChains]
             
colorMenu = {1:['Atoms using CPK',0],
             2:['AtomsDG (polarity/charge)',1],
             3:['Per residue',3],
             4:['Per residue shapely',4],
             5:['Per chains',7],
             6:['Secondary Structure',5],
             7:['Rainbow from N to C',2,'number'],
             8:['Temperature Factor',2,'temperatureFactor'],
             9:['sas area',2,'sas_area'],
             10:['Custom color',6],
            }

keyword = ['Keywords','  backbone','  sidechain','  chain','  picked']
kw=map(lambda x:"  "+x,RS.residueList.keys())
keyword.extend(kw)

stringBezier = ["Circle","Square"]

mesh_objects = {}
indice_objects = {
'SURF':0,
'CMS':0,
'VDW':0,
'SS': 0,
'BSTICK' : 0,
'TUBE' : 0
}

#data player default option
slider_min = 0 
slider_max = 1000
typedata = "frame :"
#mol_data = self.iMolData

def getSelectionLevel(mol):
    #fix...problem if multiple chain...
    R=mol.chains[0].residues
    sel=mol.name
    if BKBONE == 1 :
            sel=ResidueSet(R.copy())
            for i in range(len(R)) :
                sel[i].atoms=sel[i].backbone()
                #remove O
                sel[i].atoms=sel[i].atoms.get("N,CA,C")
            #sel.atoms=sel.atoms.get("CA,C,N") #backbone()
    if CAT == 1 :
            sel=ResidueSet(R.copy())
            #sel.atoms=sel.atoms.get("CA")
            for i in range(len(R)) :
                sel[i].atoms=sel[i].atoms.get("CA")
            #sel=mol.name+':::CA'
    return sel

def Make():
    global pdb,radius,mesh_objects,sc
    #molname=os.path.splitext(os.path.basename(stringName.val))[0]
    if VERBOSE :print "the name ",stringName.val
    string=stringName.val
    P=self.getMolFromName(str(stringName.val).split(":")[0])
    
    if VERBOSE : print P
    armObj = None
    if ARMATURE == 1 : #always on CA-backbone
        #if CAT == 0 and BKBONE == 0 :
        state=string.split(":") # MOL : CH : AA : ATMS
        select=self.select(string,negate=False, only=True, xor=False, 
                           log=0, intersect=False)
        sel=select.findType(Atom)
        atoms=sel#.get(state[-1])
        if len(state) < 4 or state[3] == 'CA' : 
            atoms=sel.get("CA")
            armObj=blenderHelper.armature("Armature_obj",atoms,sc)
        elif len(state[3]) == 1 :
            atoms=sel.get(state[3])
            armObj=blenderHelper.armature("Armature_obj",atoms,sc)
        else : 
            #atoms=sel#.get(state[3])
            atoms.sort()            
            armObj=blenderHelper.armature("Armature_obj",atoms,sc)
            #armObj=bond_armature("Armature_obj",atoms,sc)
    Blender.Window.CameraView()
        #for keys in mesh_objects :
        #           print keys
        #           print mesh_objects[keys]

def get_children(ob):
    return [ob_child for ob_child in Blender.Object.Get() if ob_child.parent == ob]

def getAllRelatedGeom(molname):
    listO = Blender.Object.Get()
    liste = filter(lambda x: x.name.find(molname) != -1, listO)
    return liste
    
def delMolDic(molname):
    del self.selections[molname]
    del self.iMolData[molname]
    del self.molDispl[molname]
    del self.MolSelection[molname]

def delGeomMol(mol):
    #put in the helper
    #scene.unlink
    #first go throught the geom and del all attribute / unlink all obj
    #get the master
    liste = getAllRelatedGeom(mol.name)
    for ch in liste :
        sc.objects.unlink(ch)
    #need to delete the sticks as they do not show molname
    sticks = mol.geomContainer.geoms['sticks']
    if hasattr(sticks,'obj'):
        for o in sticks.obj:
            sc.objects.unlink(o)
    
def getMolName():
    global molMenu
    ind = molPreset.val - 1 #start at 1
    name = molMenu[ind]
    if name in self.Mols.name:
        mol = self.getMolFromName(name)
    else : #selection
        for mname in self.selections:
            if name in self.selections[mname].keys() : 
                mol = self.getMolFromName(mname)
                break
    return name,mol

def getGeomActive(name):
    lgeomName=[]
    mname,mol=getMolName()   
    #sel=getSelectionLevel(mol)
    #Sel = parseSelection(stringSelection.val,mol)
    #selname=getSelectionName(sel,mol)   
    if LSURF.val : 
        sname='MSMS-MOL'+str(mname)
        #if sel != str(mname) :sname='MSMS-MOL'+str(selname)
        lgeomName.append(sname)
    if LCMS.val :
        sname='CoarseMS_'+str(mname)
        #if sel != str(mname) :sname='CoarseMS_'+str(selname)       
        lgeomName.append(sname)
    if LVDW.val : lgeomName.append('cpk')
    if LSS.val : lgeomName.append('secondarystructure')
    if LBSTICK.val : 
        lgeomName.append('balls')
        lgeomName.append('sticks')
    return lgeomName

def sortName1(array):
    mols=[]
    chain={}
    res={}
    atoms={}
    for element in array:
        if ":" in element :
            levels=element.split(":")
            if levels[0] not in mols : 
                mols.append(levels[0])
                chain[levels[0]]=[]
            if levels[1] not in chain[levels[0]] : 
                chain[levels[0]].append(levels[1])
                res[levels[1]]=[]
            if levels[2] not in res[levels[1]] : 
                res[levels[1]].append(levels[2])
                atoms[levels[2]]=[]
            if levels[23] not in res[levels[2]] : 
                atoms[levels[2]].append(levels[1])
        else :  #only mol name present
            return element
    
def sortName(array):
    stringselection=""
    for element in array:
        if ":" in element :
            stringselection+=element+";"
        else : return element
    return stringselection            

def parseObjectName(o):
    name=o.name
    tmp=name.split("_")
    if len(tmp) == 1 : #no "_" so not cpk (S_) or ball (B_) stick (T_) or Mesh (Mesh_)
       return ""
    else :
       if "MSMS" in name : 
           return name.split("MSMS-MOL")[1][:-1]         #the mol name
       elif o.parent.name == "secondarystructur" : 
           return name.split("_")[1]    #the mol name
       else :
          if tmp[0] == "S" or tmp[0] == "B" : 
              return tmp[1]
          else : 
              return [tmp[1],tmp[2]]

def parseSelection(string,mol):
    strselection=""
    if string == "picked" : 
        if VERBOSE :print sc.objects.selected
        astr=[]
        for o in sc.objects.selected : 
            if VERBOSE : print o.name,o.type
            astr.append(parseObjectName(o))
        strselection=sortName(astr)
        if VERBOSE : print strselection
        return strselection
    elif string.upper() == "BACKBONE": return mol.name+":::CA,C,N;"
    elif string.upper() == "SIDECHAIN": return mol.name+":::sidechain;"
    elif string.upper()[0:5] == "CHAIN" : return mol.name+":"+string.upper()[5:].replace(" ","")+"::;"
    elif string.upper() in AtomElements.keys() : return mol.name+":::"+string.upper()
    elif string.upper() in RS.r_keyD.keys() : return mol.name+"::"+RS.r_keyD[string.upper()]
    elif string.lower() in ResidueSetSelector.residueList.keys() : return mol.name+'::'+string.lower()+':'
    else : return mol.name

def getSelectionName(sel,mol):
       for selname in self.selections[mol.name].keys() : 
           if sel == self.selections[mol.name][selname][0] : return selname           
       return mol.name+"_Selection"+str(len(self.MolSelection[mol.name]))

def editSelection(ind):
    #listSelection=["Save Set","Rename Set","Delete Set"]
    txt=listSelection[ind-1]
    if txt == "Save Set":
        saveSelection()
    elif txt == "Rename Set":
        renameSelection()
    elif txt == "Delete Set":
        deleteSelection()

def saveSelection():
    #store the current selection
    name,mol = getMolName()
    if VERBOSE :print "mol name ",name
    sel=stringSelection.val
    n=len(self.selections[name])
    selname=mol.name+"_sel_"+str(n)
    name = mol.name
    if VERBOSE :print "sel str ",sel,n,selname
    self.selections[name][selname]=[]#array of parameter : selection string / display mode / color mode
    self.selections[name][selname].append(sel)
    self.selections[name][selname].append([LVDW.val,LBSTICK.val,LSS.val,LSURF.val,LCMS.val,None,None]) #cpk,b&s,ribbon,surf
    self.selections[name][selname].append(str(selColorPreset.val-1))
    self.selections[name][selname].append(parseSelection(sel,mol))
    self.MolSelection[name][selname] = sel
    self.molDispl[selname]=[LVDW.val,LBSTICK.val,LSS.val,LSURF.val,LCMS.val,None,None]
    if ColorPreset1.val == 7 : 
        self.molDispl[selname][6]=ColorMol.val
        self.selections[name][selname][1][6]=ColorMol.val
    self.molDispl[selname][5] = ColorPreset1.val
    self.selections[name][selname][1][5]=ColorPreset1.val
    if VERBOSE :print self.selections[name][selname]
    self.iMolData[selname]=self.iMolData[mol.name]
    #operateSelection(selname,self.selections[name][selname],mol)
    resetDashBoard()
    Draw.Redraw()
    Draw.Redraw(1)

def deleteSelection():
    ind = molPreset.val - 1
    selname,mol=getMolName()
    res = drawQuestion("Are You sure you want to delete the current selection "+selname,"delete")
    mname = mol.name
    if res :
        del self.MolSelection[mname][selname]
        del self.selections[mname][selname]
        del self.molDispl[selname]
        del self.iMolData[selname]
        resetDashBoard()
        
def renameSelection():
    #whats the new name
    newname=Blender.Draw.PupStrInput("new Name:", "mySel", 25)
    #get current selection name
    ind = molPreset.val - 1
    selname,mol=getMolName()
    mname = mol.name
    #change the name in dic of indice
    #self.mv.iSel[str(val)] = newname
    #change the name in the mol dictionary of selection
    sel = self.MolSelection[mname][selname]
    dsDic = self.molDispl[selname]
    dicS = self.selections[mname][selname]
    #del self.mv.MolSelection[mname][selname]
    del self.selections[mname][selname]
    del self.molDispl[selname]
    del self.iMolData[selname]
    
    self.MolSelection[mname][newname]=sel
    self.selections[mname][newname]=dicS
    self.molDispl[newname]=dsDic
    self.iMolData[newname]=self.iMolData[mol.name]
    
    resetDashBoard()
    
def operateSelection(selname,selection,mol):
    #self.selections[name][selname] ie 'CA', [0, 1, 0, 0], 'byAtomType' string selection, display,color
    #need to add CMS
    dis=selection[1]
    print dis
    string=parseSelection(selection[0],mol)
    lGeom=getGeomActive(mol.name)
    self.select.clear()
    if VERBOSE :print "ok selection ",string
      #if dis[0] : #cpk
    if dis[0] : 
        self.displayCPK(string,log=LOG,negate=(not bool(LVDW.val)),
                        only=bool(ONLY))
    #if dis[1] : #b&s
    if dis[1] : 
        self.displaySticksAndBalls(string, log=1, cquality=0, 
                                   sticksBallsLicorice='Sticks and Balls', 
                                   bquality=0, cradius=0.2, bRad=0.3,
                                   negate=(not bool(LBSTICK.val)), 
                                   bScale=0.0,only=bool(ONLY))
    if dis[3] : 
        if selname in mol.geomContainer.geoms : 
            self.displayMSMS(string, negate=(not bool(LSURF.val)), 
            only=bool(ONLY), log=1, surfName='MSMS-MOL'+selname, nbVert=1)
        else : 
            self.computeMSMS(string, log=1, display=(bool(LSURF.val)), 
                             surfName='MSMS-MOL'+selname,perMol=0)
    if dis[2] : 
        self.displayExtrudedSS(string, negate=(not bool(LSS.val)), 
                               only=bool(ONLY), log=1)        
    if dis[5] != None :
        funcId = colorMenu[dis[5]][1]
        print funcId,funcColor[funcId]
        if int(dis[5]) == 7 : 
           #apply the color on the molecule geometry if no selection geometry displayed
           if len(lGeom) == 0 :
               lGeom=getGeomActive(mol.name)
           funcColor[int(dis[5])-1](string,[dis[6]], lGeom, log=1)
        elif funcId == 2 :
                self.colorByProperty.level='Atom'
                selection = self.select(string,negate=False, only=True, xor=False, 
                                           log=0, intersect=False)
                if not isinstance(selection,Atom) : 
                    selection = selection.findType(Atom)
                max = len(selection)         
                funcColor[2](selection, lGeom, colorMenu[dis[5]][2], propertyLevel='Atom', 
                                            colormap='rgb256',log=1)
        else : funcColor[funcId](string, lGeom, log=1)

def delMol():
    mname,mol = getMolName()
    if mname in self.Mols.name :
        #need to first delete the blender geom and the associates directory
        #note the mesh are still in the memory ....
        delMolDic(mname)
        delGeomMol(mol)
        #then delete the mol
        self.deleteMol(mol, log=0)

def delete_Atom_Selection():
    #self.mv.deleteAtomSet...
    mname,mol=getMolName()
    sel = parseSelection(stringSelection.val,mol)
    print "del ", sel,mname, mol
    if sel is mol.name :
        #print sel,mname, mol , "del"
        res = drawQuestion("Are You sure you want to delete:\n "+mol.name,"delete")
        if res : 
            delMol()
    else :
        selection = self.select(sel,negate=False, only=True, xor=False, 
                               log=0, intersect=False)
        if not isinstance(selection,Atom) : 
           selection = selection.findType(Atom)
        res = drawQuestion("Are You sure you want to\n delete the atoms\n of the current selection:\n "+sel,"delete")
        if res : 
            self.deleteAtomSet(selection)
            

def checkNumberOfLine(indl,k):
    if (indl+k) >= len(line) :
        line.append(line[-1]+30)        

def drawCPKoption(iline):
    minV=0.
    maxV=10.
    cpkopt['cpkRad']=Draw.Slider('cpkRad:', EV_CPKOPT, 5, line[iline], 200, 25,
                                cpkopt['cpkRad'].val, minV, maxV, 0, 
                                'the radii of the sphere is cpkRadii+vdwRadii*scale')
    cpkopt['scaleFactor']=Draw.Slider('scaleFactor:', EV_CPKOPT, 5, line[iline+1], 
                                    200, 25,cpkopt['scaleFactor'].val, minV, maxV, 
                                    0, 'the radii of the sphere is cpkRadii+vdwRadii*scale')
    BGL.glRasterPos2i(5,line[iline+2])
    Draw.Text("DisplayCPK options:")
    return iline+3

def drawBSoption(iline):
    #only, negate, bRad,
    #bScale, bquality, cradius, cquality,
    #sticksBallsLicorice,redraw
    minV=0.
    maxV=10.
    bsopt['bScale']=Draw.Slider('scale:', EV_BSOPT, 5, line[iline], 200, 25,
                                bsopt['bScale'].val, minV, maxV, 0, 'scale')
    bsopt["ratio"]=Draw.Slider('ratio B/S:', EV_BSOPT, 5, line[iline+1], 200, 
                                25,bsopt['ratio'].val, minV, maxV, 0, 
                                'the ratio ball size/stick size')
    BGL.glRasterPos2i(5,line[iline+2])
    Draw.Text("displaySticksAndBalls options:")
    return iline+3

def drawMSMSoption(iline):
    #msmsopt['perMol']=
    msmsopt['pRadius']=Draw.Slider('pRadius:', EV_MSOPT, 5, line[iline], 200, 
                                    25,msmsopt['pRadius'].val, 0., 10., 1, 
                                    'the probe radius')
    msmsopt['density']=Draw.Slider('density:', EV_MSOPT, 5, line[iline+1], 
                                    200, 25,msmsopt['density'].val, 0., 10., 1, 
                                    'the vertex density for triangulation')
    msmsopt['hdensity']=Draw.Slider('hdensity:', EV_MSOPT, 5, line[iline+2], 
                                    200, 25,msmsopt['hdensity'].val, 0., 10., 1, 
                                    'the vertex density for triangulation of high density surface')
    BGL.glRasterPos2i(5,line[iline+3])
    Draw.Text("DisplayMSMS options:")
    return iline+4
 
def drawCMSoption(iline):
    minV=0.
    maxV=10.
    cmsopt['iso']=Draw.Slider('iso:', EV_CMSOPT, 5, line[iline], 200, 25,
                                cmsopt['iso'].val, 0., 20., 0, 'isovalue')
    cmsopt["res"]=Draw.Slider('res:', EV_CMSOPT, 5, line[iline+1], 200, 
                                25,cmsopt['res'].val, -5.0, +5.0, 0, 
                                'resolution')
    BGL.glRasterPos2i(5,line[iline+2])
    Draw.Text("displayCoarseMolecularSurface options:")
    return iline+3

def resetDashBoard():
    LVDW.val = False
    LBSTICK.val = False
    LSS.val = False
    LSURF.val = False
    LCMS.val = False
    stringSelection.val = ""
    
def update(mname,mol):  
    LVDW.val = self.molDispl[mname][0]
    LBSTICK.val = self.molDispl[mname][1]
    LSS.val = self.molDispl[mname][2]
    LSURF.val = self.molDispl[mname][3]
    LCMS.val = self.molDispl[mname][4]
    if self.molDispl[mname][5] != None : 
        ColorPreset1.val = self.molDispl[mname][5]
    if self.molDispl[mname][6] != None :
        color=self.molDispl[mname][6]
        ColorMol=Draw.Create(color[0],color[1],color[2])
    if mname not in self.Mols.name:
        print mname+" is a selection"
        #dis=selection[1]
        operateSelection(mname,self.selections[mol.name][mname],mol)
        #should also modified the sel fields
        stringSelection.val = self.selections[mol.name][mname][0]
    else :
        operateSelection(mname,[mname,self.molDispl[mname]],mol)
    #print self.molDispl[mname]
    #should look at data only for mol, not data, or should point to the same data as the mol
    listData=self.iMolData[mname]
    if len(listData) == 0 : dataMenu.val = 0
    else : #take the first one ?
        iMol = self.Mols.name.index(mname)
        dataMenu.val = iMol+1
    
    #need to update the data player
    
        #   self.set(self.selection,self.mv.MolSelection[mname.split("_")[0]][mname])
        #   if True in self.mv.molDispl[mname]: self.doDisplaySelection(self.mv.molDispl[mname],private)
        #else : 
        #   self.set(self.selection,"")
        #if True in self.molDispl[mname]: self.doDisplaySelection(self.molDispl[mname],private)

def doModeller(res):
    dic = res[1]
    doMD = dic.BTN['md']['value'].val
    doMini = dic.BTN['mini']['value'].val
    import modeller
    mname,mol = getMolName()
    Sel = parseSelection(stringSelection.val,mol)    
    mdl = mol.mdl
    print mname
    # Select all atoms:
    atmsel = modeller.selection(mdl)
    # Generate the restraints:
    mdl.restraints.make(atmsel, restraint_type='stereo', spline_on_site=False)
    #mdl.restraints.write(file=mpath+mname+'.rsr')
    mpdf = atmsel.energy()
    mol.pmvaction.last = 10000
    mol.pmvaction.store = dic.BTN['store']['value'].val
    print "before optmimise"
    if doMini:
        cg = modeller.optimizers.conjugate_gradients(output='REPORT')
        maxit = int(dic.NUMBERS['miniIterMax']['value'].val)
        cg.optimize(atmsel, max_iterations=maxit, actions=mol.pmvaction)#actions.trace(5, trcfil))
        del cg
    if doMD:
        md = modeller.optimizers.molecular_dynamics(output='REPORT')
        maxit = int(dic.NUMBERS['mdIterMax']['value'].val)
        temp = dic.NUMBERS['mdTemp']['value'].val
        md.optimize(atmsel, temperature=temp, max_iterations=int(maxit),actions=mol.pmvaction)
        del md
        
def check_update():
    ask = False
    #get the update file
    import urllib
    URL=__url__[1]
    import WebServices
    test = WebServices.checkURL(URL)
    if test :
        fURL=urllib.urlopen(URL)
        note=fURL.read()
        fURL.close()
        fields=note.split()
        cv=fields[0].split("=")[1]
        if cv != __version__ :
            ask=True
        if ask :
            message= "A update is available did you want to proceed\ncurrent version:"+__version__+"\nnew version:"+cv+"\n"
            res=drawQuestion(message,'ePMV Update')
            if res == 1: 
                epmv_update(note=note)
    else :
        drawMessage('Error','Internet Problem')

def epmv_update(note=None):
    global _inst
    #try to update ePMV
    if _inst is None :
        _inst=Installer(gui=False)
        _inst.mgltoolsDir=MGL_ROOT
        _inst.currDir=MGL_ROOT+os.sep+"MGLToolsPckgs"+os.sep+"Pmv"+os.sep+"hostappInterface"+os.sep
    #first check if the file exist
#        import os.path
#        if not os.path.exists(self.inst.currDir+'/epmv_dir.txt'):
#            c4d_dir = c4d.storage.GeGetStartupPath().replace(" ","\ ")
#            f=open(self.inst.currDir+'/epmv_dir.txt','w')
#            f.write("Cinema4DR12:"+c4d_dir)
#            f.close()
    _inst.getDirFromFile()
    _inst.updateCVS()
    try:
        _inst.installBlender(update=True)
        #need a popup to says to restart
        msgs="SUCCESS!\nYou need to restart now!\n"
        if note != None:
            msgs += note
        drawMessage(msgs,'Update success')
        return True
    except:
        drawMessage('Error','Update Problem')

def drawMessage(message,title):
    block=[]
    #need to split the message, as windows length limited, 
    #31car
    for line in message.split('\n'):
        if len(line) > 30 :
            block.append(line[0:28]+"-")
            block.append("-"+line[28:])
        else :
            block.append(line)
    print block
    retval = Blender.Draw.PupBlock(title, block)
    return 
    
def drawError(message):
    drawMessage(message,"Problem")
    return 

def drawQuestion(question,title):
    block=[]
    for line in question.split('\n'):
        if len(line) > 30 :
            block.append(line[0:28]+"-")
            block.append("-"+line[28:])
        else :
            block.append(line)
    return Blender.Draw.PupBlock(title, block)

def drawModeller():
    guimodeller = ParameterModeller()
    retval = Blender.Draw.PupBlock("Modeller", guimodeller.block)
    return retval,guimodeller

def drawOptionMenu(choice):
    option=listOptionsMenu[choice-1]
    #if option == 'update':
    #    check_update()
    if option == 'load PDB':
        Blender.Window.FileSelector(choosePDB, 'load PDB')
    elif option == 'load DATA':
        Blender.Window.FileSelector(chooseDATA, 'load Data')
    elif option == 'Recent Files':
        drawRecentFiles()

def drawRecentFiles():
    global stringName
    listeFile=["Cancel"]
    for r in self.recentFiles.categories["Documents"]:
        listeFile.append(r[0])
    choice = Draw.PupMenu('|'.join(listeFile))
    if choice :
        if listeFile[choice-1] != "Cancel":
            stringName.val = listeFile[choice-1]
            loadPDB()

def drawExtension(choice):
    print choice
    print listExtension[choice-1]
    extension = listExtension[choice-1]
    if extension == "modeller":
        res=drawModeller()
        doModeller(res)
    elif extension == 'Add Extension':
        print "add extension"

def citationInformation():
    txt=epmv.getCitations()
    drawMessage(txt,'PMV citations')

def drawAbout(ind):
    txt=listHelp[ind-1]
    if txt == 'About ePMV':
        drawMessage(__bpydoc__,'About ePMV')
    elif txt == 'ePMV documentation':
        import webbrowser
        webbrowser.open(__url__[0])
    elif txt == 'check fo update':
        check_update()
    elif txt == 'Citation Information':
        import webbrowser
        webbrowser.open(__url__[2])
        
def setPreferences(res):
    global _useModeller,_modeller,_logCommand,_forceFetch
    global env
    r=res[0]
    prefs=res[1]
    epmv.doCamera = prefs['Camera'].val
    epmv.doLight = prefs['Light'].val
    epmv.doCloud = prefs['CloudsPoints'].val
    epmv.bicyl = prefs['BiCylinders'].val   
    _logCommand = prefs['LogCommands'].val
    epmv.center_mol = prefs['Center_mol'].val
    epmv.center_grid = prefs['Center_grid'].val
    _forceFetch = prefs['Force_fetch'].val
    if _modeller :
        _useModeller = prefs['modeller'].val
        epmv.useModeller = _useModeller
        if _useModeller :
            import modeller
            #setup Modeller
            if env is None :
                env = modeller.environ()
                MPATH=MGL_ROOT+'/MGLToolsPckgs/Pmv/hostappInterface/extension/Modeller/'
                env.io.atom_files_directory = [MPATH]
                env.edat.dynamic_sphere = True
                env.libs.topology.read(file='$(LIB)/top_heav.lib')
                env.libs.parameters.read(file='$(LIB)/par.lib')         
            epmv.center_mol = False
            epmv.center_grid = False
            
def drawPreferences():
    global _useModeller,_logCommand,_forceFetch
    preferences={"Camera":Blender.Draw.Create(0),
                 "Light":Blender.Draw.Create(0),
                 "CloudsPoints":Blender.Draw.Create(0),
                 "BiCylinders":Blender.Draw.Create(0),
                 "LogCommands":Blender.Draw.Create(0),
                 "Center_mol":Blender.Draw.Create(0),
                 "Center_grid":Blender.Draw.Create(0),
                 "Force_fetch":Blender.Draw.Create(0),
                 }
    if _modeller :
        preferences["modeller"] = Blender.Draw.Create(int(_useModeller))

    preferences['Camera'].val = int(epmv.doCamera)
    preferences['Light'].val = int(epmv.doLight)
    preferences['CloudsPoints'].val = int(epmv.doCloud )
    preferences['BiCylinders'].val = int(epmv.bicyl)
    preferences['LogCommands'].val = int(_logCommand)
    preferences['Center_mol'].val = int(epmv.center_mol)
    preferences['Center_grid'].val = int(epmv.center_grid)
    preferences['Force_fetch'].val = int(_forceFetch)
    options=[]
    for n in preferences.keys():
        options.append((n,preferences[n]))
    retval = Blender.Draw.PupBlock("ePMV preferences", options)
    return retval,preferences

def drawHeadLogo(line):
    #should be the first or last line ??
    Draw.Image(Banner, 0, 0)#, zoomx=1.0, zoomy=1.0, clipx=0, clipy=0, clipw=-1, cliph=-1)

def drawMenu(nline):
    #fileMenu: Load PDB, Load Data, Update ePMV
    Draw.PushButton("File", EV_BT_MENU, 5, line[nline], 75, 25, "ePMV menu")
    Draw.PushButton("Edit", EV_BT_OPT, 85, line[nline], 75, 25, "preferences")
    Draw.PushButton("Extensions", EV_BT_EXT, 165, line[nline], 75, 25, "extensions available")
    Draw.PushButton("Help", EV_BT_ABOUT, 245, line[nline], 75, 25, "help&update")
        
def drawAdvanceOptions(iline):
    listobj=sc.objects.selected
    #print listobj
    drawCpk=False
    drawMSM=False
    drawBs=False
    drawCms=False
    for o in sc.objects.selected : 
        if VERBOSE :print o.name,o.type
        if o.name.find('cpk') !=-1 or o.name.split("_")[0] == 'S': drawCpk=True#
        if o.name.find('ball') !=-1 or o.name.split("_")[0] == 'B' or o.name.split("_")[0] == 'T': drawBs=True#
        if o.name.find('MSMS') !=-1 : drawMSM=True#
        if o.name.find('CoarseMS') !=-1 : drawCms=True#
    if drawCpk : iline=drawCPKoption(iline)
    if drawBs  : iline=drawBSoption(iline)
    if drawMSM : iline=drawMSMSoption(iline)
    if drawCms : iline=drawCMSoption(iline)  
    BGL.glBegin(BGL.GL_LINES);
    BGL.glVertex3f(5., float(line[iline]), 0.0)
    BGL.glVertex3f(395., float(line[iline]), 0.0)
    BGL.glEnd( );
    return iline+1

def drawDataPlayer(lmol,iline):
    global slider_min, slider_max,dataMenu,data_slider,typedata
    global data_start,data_end,data_step
    #per molecule
    #menu of availabe data
    #checkNumberOfLine(iline,k)
    lineP=line[iline]
    menu="DATA : %t|None %x0"
    doit=True
    for i,mol in enumerate(lmol) :
        if VERBOSE :print "drawDataPlayer ", mol.name,self.iMolData
        listData=self.iMolData[mol.name]
        for  j,data in enumerate(listData) :
            menu+="|"+data+" %x"+str(i+j+1)
            doit=True
    if doit  :
        if typedata == "frame :" :
            Draw.PushButton("toKeys", ev_2key, 5, lineP, 100, 25, 
                            "bake to KeysFrame")
            data_start = Draw.Number("start:", 1000, 120, lineP, 60, 25, 
                                     data_start.val, slider_min, slider_max) 
            data_end = Draw.Number("end:", 1000, 200, lineP, 60, 25, 
                                   data_end.val, slider_min, slider_max)
            data_step = Draw.Number("step:", 1000, 280, lineP, 60, 25, 
                                    data_step.val, 1, 200)
                                    #tooltip=None, callback=None, clickstep=None, precision=None)
            iline = iline + 1 
            lineP = line[iline]
        dataMenu = Draw.Menu(menu,ev_data, 5, lineP, 100, 25, 
                                 dataMenu.val,'Data')
        data_slider = Draw.Slider(typedata, ev_slider, 120, lineP, 220, 25, 
                                      data_slider.val, slider_min, slider_max, 
                                      0, typedata)
        return iline + 1
    else :
        return iline

def drawDash(lmol,indl):
    global ev_del,ev_vdw,ev_surf,ev_bs,ev_ss,ev_col,ev_sel,ColorPreset1,ColorMol
    global keyPreset,ev_key
    global LVDW,LBSTICK,LSS,LSURF,LCMS,LMETA,LSPLINE,LRIB
    global stringSelection,molPreset,molMenu
    
    #the dash is now a menu selection for mol
    #the dash consist of Atom | Backbone | surface representation
    #from bottom to top line
    ##end with color
    #BGL.glRasterPos2i(5,line[indl])
    #Draw.Text("Color By")
    color=""
    for i in colorMenu.keys():
        color+=colorMenu[i][0]+" %x"+str(i)+"|"
    drawLabel(10,line[indl]+10,"Color scheme:")
    #color = "Atom %x1|DG %x2|NtoC %x3|Residues %x4|ResShapely %x5|SS %x6|Color %x7"
    ColorPreset1=Draw.Menu(color,ev_col, 100, line[indl], 160, 25, ColorPreset1.val,'Color')
    ColorMol=Draw.ColorPicker(ev_pcol, 270, line[indl], 30, 25, ColorMol.val)
    indl=indl+1
    #next line : bs ratio , metaballs, cmsres
    bsopt["ratio"]=Draw.Slider('', EV_BSOPT, 5, line[indl], 100, 
                                25,bsopt['ratio'].val, 0., 10., 0, 
                                'the ratio ball size/stick size')
    LMETA=Draw.Toggle("MetaBalls", ev_meta, 120, line[indl], 100, 25,LMETA.val, 
                      "display MetaBalls")
    cmsopt["res"]=Draw.Slider('', EV_CMSOPT, 230, line[indl], 100, 
                                25,cmsopt['res'].val, -5.0, +5.0, 0, 
                                'resolution')
    indl=indl+1
    #next line : bs sc , spline, cmsiso
    bsopt["bScale"]=Draw.Slider('', EV_BSOPT, 5, line[indl], 100, 
                                25,bsopt['bScale'].val, 0., 10., 0, 
                                'the scale')
    LSPLINE=Draw.Toggle("Spline", ev_spline, 120, line[indl], 100, 25,LSPLINE.val, 
                      "display Spline")
    cmsopt["iso"]=Draw.Slider('', EV_CMSOPT, 230, line[indl], 100, 
                                25,cmsopt['iso'].val, 0.1, 20.0, 0, 
                                'isovalue')
    
    indl=indl+1
    #next line : bs , armature, cms
    LBSTICK=Draw.Toggle("Sticks", ev_bs, 5, line[indl], 100, 25,LBSTICK.val, 
                        "display Ball and Stick")        
    Draw.Toggle("Armature", EV_TG_ARMATURE, 120, line[indl], 100, 25,ARMATURE, 
                        "create an Armature")
    LCMS=Draw.Toggle("CoarseMS", ev_cms,230, line[indl], 100, 25,LCMS.val, 
                     "display Coarse Molecular Surface")      

    indl=indl+1
    #next line : cpkslider, loft, msmsslider
    cpkopt['scaleFactor']=Draw.Slider('', EV_CPKOPT, 5, line[indl], 
                                    100, 25,cpkopt['scaleFactor'].val, 0, 10, 
                                    0, 'the radii of the sphere is cpkRadii+vdwRadii*scale')
    LRIB=Draw.Toggle("Loft", EV_TG_BKBONE, 120, line[indl], 100, 25,LRIB.val, 
                        "create a Loft")
    msmsopt['pRadius']=Draw.Slider('', EV_MSOPT, 230, line[indl], 100, 
                                    25,msmsopt['pRadius'].val, 0., 10., 1, 
                                    'the probe radius')
                                    
    indl=indl+1
    #next line : cpk, ss,msms
    LVDW=Draw.Toggle("Atoms", ev_vdw, 5, line[indl], 100, 25,LVDW.val, 
                     "display CPK")
    LSS=Draw.Toggle("Ribbons", ev_ss, 120, line[indl], 100, 25,LSS.val, 
                    "display Secondary Structure")
    LSURF=Draw.Toggle("MSMSurf", ev_surf, 230, line[indl], 100, 25,LSURF.val, 
                      "display Molecular Surface") 
                                    
    indl=indl+1
    drawLabel(10,line[indl]+10,"Molecular Representations:")
    indl=indl+1
    #the molecule and selection menu
    mol = "Molecules %t"
    i = 1
    for m in lmol :
        mol += "|"+m.name+"%x"+str(i)
        molMenu[i-1] = m.name
        i = i +1
        #check if the mol have selection
        if len(self.selections[m.name]) :
            for selname in self.selections[m.name]:
                mol += "|"+selname+"%x"+str(i)
                molMenu[i-1] = selname
                i = i +1
        
    molPreset=Draw.Menu(mol,ev_mol, 5, line[indl], 75, 25, molPreset.val,'Molecules')
    #the fields for selection
    stringSelection = Draw.String("Sel:", EV_ST_SELECTION, 80, line[indl], 140, 25,
                                  stringSelection.val, 50, "Selection string")
    #draw menu selection of keywords
    k = keyword[0]+' %t'
    for i,ky in enumerate(keyword[1:]):
        k+="|"+ky+"%x"+str(i+1)
    keyPreset=Draw.Menu(k,ev_key, 225, line[indl], 15, 25, keyPreset.val,'Selection')
    Draw.PushButton("Edit", ev_sel, 240, line[indl], 40, 25, "Save/Rename/Delete the current selection")
    #delete on/off
    Draw.PushButton("Del", ev_del, 280, line[indl], 40, 25,"Delete the current Atom set")
    indl = indl + 1
    return indl

def drawLabel(x,y,Text):
     BGL.glRasterPos2i(x,y)
     Draw.Text(Text)

def drawSeparator(nLine):
    BGL.glBegin(BGL.GL_LINES);
    BGL.glVertex3f(5., float(line[nLine]), 0.0)
    BGL.glVertex3f(335., float(line[nLine]), 0.0)
    BGL.glEnd( );

def draw_gui():
    global stringName,dataName, Shapepreset, Menupreset,ExportPreset,ColorPreset1
    global pmvcmds
    global ColorPreset2,sliderEdge, numberCentreX, numberCentreY, numberCentreZ
    global sliderG, sliderR, sliderB,selColorPreset,line
    
    nLine=0
    
    drawHeadLogo(nLine)
    nLine+=1

    #draw version nb
    drawLabel(5,line[nLine]-15,"ePMV "+__version__)
    #nLine+=1
    #execute pytyhon script button
    Draw.PushButton("execute script", EV_BT_EXECUTE, 5, line[nLine], 235, 25, "execute python script")
    nLine+=1
    drawSeparator(nLine)
    listmol=self.Mols
    #dataplayer
    nLine=drawDataPlayer(listmol,nLine)
    #dataName = Draw.String("data:", EV_ST_DATA, 5, line[nLine], 235, 25,dataName.val, 100,"Name of the data file")
    #nLine+=1
    Draw.PushButton("Browse", EV_BT_DCHOOSE, 5, line[nLine], 60, 25, "choose a data file")
    drawLabel(70,line[nLine]+10,"to load a Data file e.g.")
    #need the show popup of differnt type available
    datatype = ("Data Type%t|"+strDataSupported+"|\\.xtc|\\.trj").replace("$","")
    Draw.Menu(datatype,300, 200, line[nLine], 100, 25, 0,'supported data type')
    #Draw.PushButton("Load", EV_BT_DLOAD, 335, line[nLine], 60, 25, "Load the file")
    nLine+=1   
    drawSeparator(nLine)
    nLine=drawDash(listmol,nLine)
    drawSeparator(nLine)
    #Load PDB
    stringName = Draw.String("ID:", EV_ST_PDBNAME, 5, line[nLine], 235, 25,stringName.val, 100,"Name of the pdb file")
    Draw.PushButton("Fetch", EV_BT_LOAD, 260, line[nLine], 60, 25, "Load the file")
    nLine+=1
    Draw.PushButton("Browse", EV_BT_CHOOSE, 5, line[nLine], 60, 25, "choose a molecule file")
    drawLabel(70,line[nLine]+5,"to a PDB file OR enter a 4 digit ID (e.g. 1crn):")
    nLine+=1
    drawSeparator(nLine)
    #put here the file menu and the extension
    drawMenu(nLine)
    nLine+=1

    #menu
    
def event(event, val) :
    if event == Draw.ESCKEY or event == Draw.QKEY:
       stop = Draw.PupMenu("OK?%t|Stop the script %x1")
       if stop == 1:
              Draw.Exit()
    

def loadPDB():
    #todo, some part may probably be in the adaptor or helper instead of here
    if VERBOSE :print stringName.val
    if len(stringName.val) == 4 : #PDB CODE -> webdownload!
            molname=stringName.val
            if molname in self.Mols.name : 
                self.hostApp.driver.duplicatemol=True
            if VERBOSE :print self.hostApp.driver.duplicatemol
            #how support modeller here
            #will use fetch instead
            pdbtype=['PDB','TMPDB','OPM','CIF','PQS']
            indice = Draw.PupMenu('|'.join(pdbtype))
            self.fetch.db = pdbtype[indice-1]
            mol = self.fetch(stringName.val, f=_forceFetch)
            #self.readFromWeb(stringName.val.upper(), log=1)
    else :    
        molname=os.path.splitext(os.path.basename(stringName.val))[0]
        print molname
        #test the name lenght
        if len(molname) > 7 :
            drawError("Sorry, but the name of the given file is to long,\nand not suppported by Blender.\n Please rename it or load another file")
            return 0
        if VERBOSE :print molname, self.Mols.name, (molname in self.Mols.name)
        name=stringName.val
        adt=False
        ext = os.path.splitext(os.path.basename(name))[1]
        print ext
        if ext == '.dlg' :#Autodock
            epmv.center_mol = False
            self.readDLG(name,1,0) #addToPrevious,ask
            self.showDLGstates(self.Mols[-1])
            molname = self.Mols[-1].name
            adt=True
        if molname in self.Mols.name : 
            self.hostApp.driver.duplicatemol=True
            if VERBOSE :print self.hostApp.driver.duplicatemol
        if _useModeller and not adt :
            import modeller
            from modeller.scripts import complete_pdb
            mdl = complete_pdb(env, name)
            mdl.patch_ss()
            name = name.split(".pdb")[0]+"m.pdb"
            mdl.write(file=name)
        if not adt :
            self.readMolecule(name,log=1)
            if _useModeller :
                self.Mols[-1].mdl=mdl
        molname = self.Mols[-1].name
        molname=molname.replace(".","_")
        if VERBOSE :print "1",molname, self.Mols[-1].name
        self.Mols[-1].name=molname
        if VERBOSE :print "2", self.Mols.name
        #molname.replace(".","_")
        if molname in self.Mols.name : self.hostApp.driver.duplicatemol=False
        if len(molname) > 7 : 
            self.Mols[-1].name=molname[0:6]
            molname = self.Mols[-1].name
    self.selections[self.Mols[-1].name]={}
    stringName.val=self.Mols[-1].name
    self.iMolData[self.Mols[-1].name]=[]
    if len(self.Mols[-1].allAtoms[0]._coords) > 1 or _useModeller :
        #need a test about trajectories...
        doit=True           
        if len(self.iMolData[self.Mols[-1].name]) != 0 or _useModeller : #ok data
            for dataname in self.iMolData[self.Mols[-1].name] : 
                if dataname.find('xtc') != -1 : 
                    doit= False
        if doit : modelData(self.Mols[-1],adt=adt)
    if VERBOSE :print "self.iMolData ",self.iMolData
    if molname not in self.molDispl.keys() :
        self.molDispl[self.Mols[-1].name]=[False,False,False,False,False,None,None]
    if molname not in self.MolSelection.keys() :
        self.MolSelection[molname]={}
    if molname not in self.selections.keys() :       
        self.selections[molname]={}
    if molname not in self.iMolData.keys() :       
        self.iMolData[molname]=[]
    DASH=1
    #do we test the number of Atoms
    epmv.testNumberOfAtoms(self.Mols[-1])
 
def choosePDB(filename):
    global stringName
    stringName.val = filename
    loadPDB()

def loadData():
    if VERBOSE :print dataName.val
    dataname = dataName.val
    extension = os.path.splitext(os.path.basename(dataname))[1] #.xtc,.trj
    if VERBOSE :print dataname,extension
    if extension == '.xtc' : gromacsTraj(dataname)
    #elif extension == '.map' : gridData_1(dataname)
    else : gridData_2(dataname)    

def chooseDATA(filename):
    global dataName
    dataName.val = filename
    loadData()
    #print stringName.val

def convertFrame(frame,maxi):
       newframe= 3. - ((frame/maxi)*3.)
       return newframe * -1.0

def applyDataState(mol,value=None,redraw=True) :
    index=dataMenu.val
    if index == 0 : #first level == None
        return
    data=self.iMolData[mol.name][index-1]
    #assume data  = string
    extension = os.path.splitext(data)[1] #.xtc,.trj
    if value == None : value=data_slider.val
    #if LSS.val == 1: 
    #         if VERBOSE :print "cleanSS"
    #         cleanSS(sc,mol)
    #         self.computeSecondaryStructure.clean(mol)
    if extension == '.xtc':
        if value >= slider_max : value =  slider_max - 1
        self.Trajectories[data].player.applyState(int(value))
        updateCloud(mol)
        if self.molDispl[mol.name][3] : updateSurf()
        if self.molDispl[mol.name][4] : updateCoarseMS()
    elif (re.search(strDataSupported,extension,re.I)):
         if VERBOSE :print "value",value
         #value=convertFrame(value,1000)
         #print value
         #self.setIsovalue(data,value, log = 1)
         self.isoC(self.grids3D[data],name=mol.name+"IsoSurface",
                 isovalue=float(value))
    else :
        mname = data.split(".")[0]
        mol = self.getMolFromName(mname) 
        #nmodels=len(mol.allAtoms[0]._coords)
        conf = int(value)
        epmv.updateData([data,'model'],conf)
#        mol.allAtoms.setConformation(conf)
#        event = EditAtomsEvent('coords', mol.allAtoms)
#        self.dispatchEvent(event) 
#        updateCloud(mol)
        if self.molDispl[mol.name][3] : updateSurf()
        if self.molDispl[mol.name][4] : updateCoarseMS()
    #if LSS.val : 
    #    self.displayExtrudedSS(mol, negate=(not bool(LSS.val)), redraw=1 ,
    #                           only=False, log=1)
    #    self.colorBySecondaryStructure(mol, ['secondarystructure'], log=1)
    if redraw :
        sc.update()
        Draw.Redraw()
        Blender.Redraw()

def updateData(mol) :
    global slider_min, slider_max,typedata,data_slider
    #data player default option
    index=dataMenu.val
    print index
    if index == 0 : #first level == None
        return
    data=self.iMolData[mol.name][index-1]
    extension = os.path.splitext(data)[1] #.xtc,.trj
    if extension == '.xtc':
        data_slider = Draw.Create(0)
        slider_min = 0 
        slider_max = len(self.Trajectories[data].coords)
        typedata = "frame :"
    elif (re.search(strDataSupported,extension,re.I)):
        data_slider = Draw.Create(self.grids3D[data].mean)
        slider_min = self.grids3D[data].mini#-3.0#0 
        slider_max = self.grids3D[data].maxi#1000
        typedata = "isovalue :"
    else  :#pdb model or dlg model
        data_slider = Draw.Create(0)
        mol = self.getMolFromName(mol.name)
        mname = mol.name
        type = data.split(".")[1]
        if type == 'model':
            nmodels=len(mol.allAtoms[0]._coords)
        else :
            nmodels=len(mol.docking.ch.conformations)        
        slider_min = 0 
        slider_max = nmodels
        typedata = "model :"

def dataToKeyFrame(mol,start=0,end=100,step=1):
    global slider_min, slider_max,typedata,data_slider
    #data player default option
    index=dataMenu.val
    if index == 0 : #first level == None
        return   
    data=self.iMolData[mol.name][index-1]
    extension = os.path.splitext(data)[1] #.xtc,.trj
    if extension != '.xtc': 
        print "only for trajectories "
        return 
    lGeom=getGeomActive(mol.name)
    geoms = []
    for gname in lGeom:
        geoms.append(mol.geomContainer.geoms[gname])   
    epmv.use_progressBar = False
    i = start
    while i < end :
        applyDataState(mol,value=i,redraw=False)
        blenderHelper.insertKeys(geoms,step=2)
        Blender.Window.DrawProgressBar(i/float(end), 'back Traj')
        i = i + step
    epmv.use_progressBar = True
    
def modelData(mol,adt=False):
    trajname = mol.name+'.model'
    if adt:
        trajname = mol.name+'.dlg'
    self.iMolData[mol.name].append(trajname)
    data_slider = Draw.Create(0)
    dataMenu = Draw.Create(1)
    updateData(mol)
       
def gromacsTraj(filename):
    self.openTrajectory(filename, log=0)
    trajname=os.path.basename(filename)
    if VERBOSE :print filename,trajname,stringName.val
    string=stringName.val
    mol=self.getMolFromName(str(stringName.val).split(":")[0])
    #create the player
    self.playTrajectory(mol.name, trajname, log=0)
    #create the slider variable
    data_slider = Draw.Create(0.0)
    dataMenu = Draw.Create(1)
    self.iMolData[mol.name].append(trajname)
    updateData(mol)

def gridData_1(filename):
    self.browseCommands('gridCommands', commands=None, log=0, package='Pmv')
    self.readAUTOGRID(filename, log=0)
    self.getIsosurface(filename, log = 1)
    dataname=filename#os.path.basename(filename)
    if VERBOSE :print dataname
    #string=stringName.val
    mol=self.getMolFromName(str(stringName.val).split(":")[0])
    #create the slider variable
    data_slider = Draw.Create(0)
    dataMenu = Draw.Create(1)
    self.iMolData[mol.name].append(dataname)
    updateData(mol)

def gridData_2(filename):
    """read any type of grid Data from filename
    the isoSurface mesh can be associated to the current molecule
    or not, in that case parent = None
    """
    self.readAny(filename)
    name = self.grids3D.keys()[-1] #the last grid added
    grid = self.grids3D[name]#the grid
    #get the isoContour
    mname,mol = getMolName()
    print mname
    self.cmol = mol  		   		   
    self.isoC.select(grid_name=name)
    self.isoC(grid,name=mname+"IsoSurface",
                 isovalue=self.grids3D[name].mean)  
    dataname=name
    if VERBOSE :print dataname
    #string=stringName.val
    #create the slider variable
    data_slider = Draw.Create(0)
    dataMenu = Draw.Create(1)
    self.iMolData[mname].append(dataname)
    updateData(mol)

def dsLines():
    pass
    
def dsCPK():
    mname,mol = getMolName()
    #self.hostApp.driver.SetJoins(JOIN1)
    Sel = parseSelection(stringSelection.val,mol)
    #Sel=getSelectionLevel(mol)
    #print Sel
    if not mol.doCPK:
        mol.doCPK = drawQuestion("Are You sure you want \nto display the CPK ("+str(len(mol.allAtoms))+" atoms) ","CPK")
    if mol.doCPK:
        self.displayCPK(Sel,log=LOG,negate=(not bool(LVDW.val)),
                    scaleFactor=cpkopt['scaleFactor'].val, redraw =0 )
    #funcColor[ColorPreset2.val-1](molname, [name], log=1)
    if Sel == mname :
        self.molDispl[mname][0]= LVDW.val
    else :
        self.molDispl[mname][0] = False
    Blender.Draw.Redraw()

def updateCPK():
    for i,molname in enumerate(self.Mols.name):
        geoms=getGeomActive(molname)
        if VERBOSE :print geoms
        if 'cpk' in geoms : 
            self.displayCPK(molname, log=LOG, 
                            #cpkRad=cpkopt['cpkRad'].val, 
                            scaleFactor=cpkopt['scaleFactor'].val, 
                            only=False, negate=False, quality=0,
                            redraw =1)

def dsBS():
    mname,mol = getMolName() 
    #self.hostApp.driver.SetJoins(JOIN2)
    Sel = parseSelection(stringSelection.val,mol)
    ratio =  bsopt["ratio"].val #ball/stick
    scale =  bsopt["bScale"].val #ball/stick
    bRad = 0.3
    cradius = float(bRad/ratio)*scale
    #print bRad,cradius
    if not mol.doCPK:
        mol.doCPK = drawQuestion("Are You sure you want \nto display the BallSticks ("+str(len(mol.allAtoms))+" atoms)","Balls and Sticks")
    if mol.doCPK:
        self.displaySticksAndBalls(Sel, log=LOG, bRad=0.3*scale, 
                               cradius =cradius, bScale=0., 
                               negate=(not bool(LBSTICK.val)),
                               only=False, bquality=0, 
                               cquality=0,redraw = 0)
    if Sel == mname :
        self.molDispl[mname][1]= LBSTICK.val
    else :
        self.molDispl[mname][1] = False               

def updateBS():
    for i,molname in enumerate(self.Mols.name):
        geoms=getGeomActive(molname)
        if VERBOSE :print geoms
        if 'balls' in geoms or 'sticks' in geoms:
            ratio =  bsopt["ratio"].val #ball/stick
            scale =  bsopt["bScale"].val #ball/stick
            bRad = 0.3
            cradius = float(bRad/ratio)*scale
            #print bRad,cradius
            self.displaySticksAndBalls(molname, log=LOG, bRad=0.3*scale, 
                                       cradius =cradius, bScale=0., 
                                       only=False, negate=False, bquality=0, 
                                       cquality=0,redraw = 1)

def dsSS():
    mname,mol = getMolName()
    Sel = parseSelection(stringSelection.val,mol)
    self.displayExtrudedSS(Sel, negate=(not bool(LSS.val)), only=False, log=1)
    if Sel == mname :
        self.molDispl[mname][2]= LSS.val
    else :
        self.molDispl[mname][2] = False               
    
def dsCMS():
    mname,mol = getMolName()
    name='CoarseMS_'+mname
    Sel = parseSelection(stringSelection.val,mol)
    parent=mol.geomContainer.masterGeom.obj 
    if name not in mol.geomContainer.geoms :
        geom=epmv.coarseMolSurface(mol,[32,32,32],
                                    isovalue=7.1,resolution=-0.3,
                                    name=name)
        mol.geomContainer.geoms[name]=geom
        obj=blenderHelper.createsNmesh(name,geom.getVertices(),None,
                                      geom.getFaces(),smooth=True)
        blenderHelper.addObjToGeom(obj,geom)
        blenderHelper.addObjectToScene(blenderHelper.getCurrentScene(),
                                      obj[0],parent=parent)
        self.colorByAtomType(mname, [name], log=0)
        obj=obj[0]
    else :
        obj = mol.geomContainer.geoms[name].obj
    blenderHelper.toggleDisplay(obj,LCMS.val)
    if Sel == mname :
        self.molDispl[mname][4]= LCMS.val
    else :
        self.molDispl[mname][4] = False       

def dsMSMS():
    mname,mol = getMolName()
    name='MSMS-MOL'+mname
    Sel = parseSelection(stringSelection.val,mol)
    if name in mol.geomContainer.geoms :
        #print name
        self.displayMSMS(Sel, negate=(not bool(LSURF.val)), 
                        only=False, log=1, surfName=name, nbVert=1)
    else :
        self.computeMSMS(Sel, log=1, display=(bool(LSURF.val)), 
                         surfName=name,perMol=1)
    #funcColor[ColorPreset2.val-1](molname, [name], log=1)
    if Sel == mname :
        self.molDispl[mname][3]= LSURF.val
    else :
        self.molDispl[mname][3] = False       
    Draw.Redraw()

def dsRibon():
    global BKBONE
    mname,mol = getMolName()
    Sel = parseSelection(stringSelection.val,mol)
    name="ribbon"+mol.name
    ruban = blenderHelper.getObject(name)
    if ruban is None :
        atoms = mol.allAtoms.get("CA")
        atoms.sort()
        ruban = epmv._makeRibbon("ribbon"+mol.name,atoms.coords,
                                 parent=mol.geomContainer.masterGeom.obj)
    if LRIB.val :
        blenderHelper.toggleDisplay(ruban,display=True)
    else :
        blenderHelper.toggleDisplay(ruban,display=False)
        
def dsSpline():
    mname,mol = getMolName()
    Sel = parseSelection(stringSelection.val,mol)
    name='spline'+mol.name
    obSpline=blenderHelper.getObject(name)
    if obSpline is None:
        atoms = mol.allAtoms.get("CA")
        atoms.sort()
        obSpline,spline=blenderHelper.spline(name,atoms.coords,scene=sc,
                                         parent=mol.geomContainer.masterGeom.obj)
    if LSPLINE.val:
        blenderHelper.toggleDisplay(obSpline,display=True)
    else :
        blenderHelper.toggleDisplay(obSpline,display=False)

def dsMeta():
    mname,mol = getMolName()
    Sel = parseSelection(stringSelection.val,mol)
    #make the metaballs
    name='metaballs'+mol.name
    metaballs=blenderHelper.getObject(name)
    if metaballs is None :
        atoms = mol.allAtoms #or a subselection of surface atoms according sas
        metaballsModifyer,metaballs = blenderHelper.metaballs(name,atoms,scn=sc,
                                        root=mol.geomContainer.masterGeom.obj)
    if LMETA.val :
        blenderHelper.toggleDisplay(metaballs,display=True)
    else :
        blenderHelper.toggleDisplay(metaballs,display=False)
    
def dsBones():
    global ARMATURE
    mname,mol = getMolName()
    Sel = parseSelection(stringSelection.val,mol)
    name=mname+"_Armature"
    armObj = blenderHelper.getObject(name)
    if armObj is None :
        #sel=Sel.findType(Atom)
        atoms=mol.allAtoms.get("CA")
        atoms.sort()            
        armObj=blenderHelper.armature(name,atoms,sc)       
    if ARMATURE == 0 :
        ARMATURE = 1
        blenderHelper.toggleDisplay(armObj,display=True)
    else  :
        ARMATURE = 0
        blenderHelper.toggleDisplay(armObj,display=False)

def color():
    global LCOLOR
    if TIMER : t1 = time()
    mname,mol = getMolName() 
    #print ind,name
    LCOLOR = 1 - LCOLOR
    #self.displayExtrudedSS(self.Mols[ind].name, negate=(not bool(LSS[name]q)), only=False, log=1)
    #listofGeom to color : all activated
    Sel = parseSelection(stringSelection.val,mol)
    lGeom=getGeomActive(mname)
    funcId = colorMenu[ColorPreset1.val][1]
    #print "colorF ", funcColor[ColorPreset1.val-1], Sel, lGeom
    if ColorPreset1.val == 10 : 
        #custom color
        self.molDispl[mname][6]=ColorMol.val
        funcColor[funcId](Sel,[ColorMol.val], lGeom, log=1)
    elif funcId == 2 :
        #color by properties , ie NtoC, Bfactor, SAS
        self.colorByProperty.level='Atom'
        selection = self.select(Sel,negate=False, only=True, xor=False, 
                                   log=0, intersect=False)
        if not isinstance(selection,Atom) : 
            selection = selection.findType(Atom)
        if ColorPreset1.val == 7 :
            maxi = len(selection)
            mini = 1.0
            property = 'number'
        elif ColorPreset1.val == 8 :
            maxi = max(selection.temperatureFactor)
            mini = min(selection.temperatureFactor)
            property = 'temperatureFactor'
        elif ColorPreset1.val == 9 :     
            maxi = max(selection.sas_area)
            mini = min(selection.sas_area)
            property = 'sas_area'
        funcColor[2](selection, lGeom, property,mini=float(mini),
                                    maxi=float(maxi), propertyLevel='Atom', 
                                    colormap='rgb256',log=1)
    else : 
        funcColor[funcId](Sel, lGeom, log=1)
    self.molDispl[mname][5] = ColorPreset1.val
    if TIMER : print "time ", time()-t1

def updateCloud(mol):
    #should update cloud...and other mixed object type
    cloudmeshname = mol.name+'_cloud'
    blenderHelper.updateCloudObject(cloudmeshname,mol.allAtoms.coords)
    #what about chain cloud object?
    for ch in mol.chains :
        cloudmeshname =  ch.full_name()+"_cloud"
        blenderHelper.updateCloudObject(cloudmeshname,ch.residues.atoms.coords)

def updateSurf():
    mname,mol = getMolName()
    Sel = parseSelection(stringSelection.val,mol)
    name='MSMS-MOL'+str(mname)
    if bool(LSURF.val) and name in mol.geomContainer.geoms: 
        self.computeMSMS(Sel,hdensity=msmsopt['hdensity'].val, 
                                 hdset=None, log=1, 
                                 density=msmsopt['density'].val, 
                                 pRadius=msmsopt['pRadius'].val, 
                                 perMol=1, display=True, 
                                 surfName=name)
                                 
def updateCoarseMS():
    mname,mol = getMolName()
    Sel = parseSelection(stringSelection.val,mol)
    name='CoarseMS_'+mname
    parent=mol.geomContainer.masterGeom.obj
    #geoms=getGeomActive(mol.name)
    select=self.select(Sel,negate=False, only=True, xor=False, log=0, 
                           intersect=False)
    #chain=select.findParentsOfType(Chain)[0]
    #parent=mol.geomContainer.masterGeom.chains_obj[chain.name]
    #select=self.mv.select(sel,negate=False, only=True, xor=False, log=0, intersect=False)
    if bool(LCMS.val) and name in mol.geomContainer.geoms.keys():
        #isovalue=7.1#float(cmsopt['iso'].val),
        #resolution=-0.3#float(cmsopt['res'].val)
        g = epmv.coarseMolSurface(select,[32,32,32],
                                  isovalue=float(cmsopt['iso'].val),
                                  resolution=float(cmsopt['res'].val),
                                  name=name,
                                  geom = mol.geomContainer.geoms[name])
        blenderHelper.updateMesh(g,parent=parent,mol=mol)

def getSelectTxt():
    texts = list(bpy.data.texts)
    textNames = [tex.name for tex in texts]
    if textNames:
        choice = Draw.PupMenu('|'.join(textNames))
        if choice != -1:
        	text = texts[choice-1]
        	return text
    return None

def execPmvComds():
    #first select the text
    #cmds=pmvcmds.val
    text = getSelectTxt()
    if text is not None:
        scmds=text.asLines()
        cmds=""
        for l in scmds:
            cmds+=l+'\n'
            print len(cmds),cmds
        exec(cmds,{'self':self,'epmv':epmv})

def timeFunction(function,arg=None):
    t1=time()
    function()
    print "time ", time()-t1

def button_event(evt) :
    global SURF,VDW,BKBONE,ARMATURE,CAT,TUBE,BSTICK,SS,COLOR1,COLOR2,JOIN1
    global JOIN2,JOIN3,DASH,LSURF,LVDW,LSS,LCMS,LMETA,LSPLINE,LBSTICK,LCOLOR,ONLY,EV_CPKRAD
    global stringName,dataName,stringSelection,pmvcmds
    if VERBOSE :print "button evt", evt
    Blender.Window.WaitCursor(1)

    ###########PLUGIN EVENT#######################################
    if evt==EV_BT_OK:
        #print "DOIT"
        Make()
    elif evt==EV_BT_CANCEL:
        Draw.Exit()
    elif evt == EV_BT_CHOOSE :
        Blender.Window.FileSelector(choosePDB, 'load PDB')
    ###########PYTHON SCRIPT#######################################
    elif evt==EV_BT_EXECUTE:
        execPmvComds()
    ###########MOLECULE EVENT#######################################
    elif evt == EV_BT_LOAD :
        if TIMER : timeFunction(loadPDB)
        else :
            loadPDB()
    elif evt == EV_BT_DCHOOSE :
        Blender.Window.FileSelector (chooseDATA, 'load DATA')
    elif evt == ev_mol :
        mname,mol = getMolName()
        update(mname,mol)
    elif evt == ev_del :
        delete_Atom_Selection()
    ###########DISPLAY EVENT#######################################
    elif evt == ev_vdw :
        if TIMER : timeFunction(dsCPK)
        else :
            dsCPK()
    elif evt == EV_CPKOPT :
        if TIMER : timeFunction(updateCPK)
        else :
            updateCPK()
    elif evt == ev_surf :
        if TIMER : timeFunction(dsMSMS)
        else :
            dsMSMS()
    elif evt == EV_MSOPT :
        if TIMER : timeFunction(updateSurf)
        else :
            updateSurf()
    elif evt == ev_cms :
        if TIMER : timeFunction(dsCMS)
        else :
            dsCMS()
    elif evt == EV_CMSOPT :
        if TIMER : timeFunction(updateCoarseMS)
        else :
            updateCoarseMS()
    elif evt == ev_ss :
        if TIMER : timeFunction(dsSS)
        else :
            dsSS()
    elif evt == ev_meta :
        if TIMER : timeFunction(dsMeta)
        else :
            dsMeta()
    elif evt == ev_spline :
        if TIMER : timeFunction(dsSpline)
        else :
            dsSpline()
    elif evt == ev_bs :
        if TIMER : timeFunction(dsBS)
        else :
            dsBS()
    elif evt == EV_BSOPT : 
        if TIMER : timeFunction(updateBS)
        else :
            updateBS()
    elif evt == EV_TG_ARMATURE:
        if TIMER : timeFunction(dsBones)
        else :
            dsBones()
    ###########COLOR EVENT#######################################
    elif evt == ev_col :
        color()
    elif evt == ev_pcol :
        if TIMER : t1 = time()
        mname,mol = getMolName()
        if  ColorPreset1.val == 9 :
            lGeom=getGeomActive(mname)
            funcColor[colorMenu[ColorPreset1.val][1]](mname,[ColorMol.val], lGeom, log=1) 
            self.molDispl[mname][6]=ColorMol.val
        if TIMER :print "time ", time()-t1
    elif evt == ev_mod :
        mname,mol = getMolName()
        Sel = parseSelection(stringSelection.val,mol)
        #ind=int(str(evt/baseISel[6])[0])
        #mol=self.Mols[ind-1]
        #mname = mol.name
        #seli=(evt-(baseISel[6]*ind))
        #sel=mname+'_sel_'+str(seli)
        #self.selections[mname][sel][1]=[LVDW[sel],LBSTICK[sel],LSS[sel],LSURF[sel]] #cpk,b&s,ribbon,surf
        #self.selections[mname][sel][2]=str(selColorPreset[sel].val-1)
        #operateSelection(sel,self.selections[mname][sel],self.Mols[ind-1])
        #Draw.Redraw()
    ###########DATA EVENT#######################################
    elif evt == EV_BT_DLOAD :
        if TIMER : timeFunction(loadData)
        else :loadData()
    elif evt == ev_data :
        if TIMER : t1 = time()
        mname,mol = getMolName()
        updateData(mol)
        if TIMER :print "time ", time()-t1
    elif evt == ev_slider :
        if TIMER : t1 = time()
        mname,mol = getMolName()
        applyDataState(mol)
        if TIMER :print "time ", time()-t1
    elif evt == ev_2key:
        if TIMER : t1 = time()
        #need to get start / end / step
        name,mol = getMolName()
        dataToKeyFrame(mol)
        if TIMER :print "time ", time()-t1
    ###########SELECTION EVENT#######################################
    elif evt == EV_ST_SELECTION :
        #do nothing
        pass
        #name,mol = getMolName()
        #if VERBOSE :print "mol name ",name
        #sel=stringSelection.val
        #selname=name+"_sel_0"
        #print sel,selname
        #selection = []#array of parameter : selection string / display mode / color mode
        #selection.append(sel)
        #selection.append([LVDW,LBSTICK,LSS,LSURF]) #cpk,b&s,ribbon,surf
        #selection.append(str(selColorPreset.val-1))
        #selection.append(parseSelection(sel,mol))
        #operateSelection(selname,selections[name][selname],mol)
    elif evt == ev_key :
        #keywords choose-> put in the stringSelection
        kw=keyword[keyPreset.val]
        stringSelection.val = kw.replace(" ","")
    elif evt == ev_sel :
        if TIMER : t1 = time()
        name = "Editt%t|"  # if no %xN int is set, indices start from 1
        name+='|'.join(listSelection)
        result = Draw.PupMenu(name)
        editSelection(result)        
        if TIMER :print "time ", time()-t1
    ###########OPTIONAL EVENT#######################################
    elif evt==EV_TG_BKBONE:
        if TIMER : timeFunction(dsRibon)
        else :dsRibon()
    elif evt==EV_TG_CAT:
        CAT = 1 - CAT
        BKBONE = 0
        Draw.Redraw()
    elif evt==EV_TG_JOIN1:
        JOIN1 = 1 - JOIN1
    elif evt==EV_TG_ONLY:
        ONLY = 1 - ONLY
    elif evt==EV_BT_MENU:
        #draw popumenu with associated command: loadPDB,loadData,Update
        choice = Draw.PupMenu('|'.join(listOptionsMenu))
        drawOptionMenu(choice)
    elif evt==EV_BT_EXT:
        #draw popumenu with associated command
        choice = Draw.PupMenu('|'.join(listExtension))
        print choice
        drawExtension(choice)
    elif evt==EV_BT_OPT:
        res=drawPreferences()
        setPreferences(res)
    elif evt==EV_BT_ABOUT:
        name = "About%t|"  # if no %xN int is set, indices start from 1
        name+='|'.join(listHelp)
        result = Draw.PupMenu(name)
        drawAbout(result)
        
    sc.update()
    Blender.Draw.Redraw()
    Blender.Redraw()
    Blender.Window.RedrawAll()
    Blender.Window.DrawProgressBar(1.0, '')
    Blender.Window.WaitCursor(0)
    update_Registry()
Draw.Register(draw_gui, event, button_event)
print "registration"