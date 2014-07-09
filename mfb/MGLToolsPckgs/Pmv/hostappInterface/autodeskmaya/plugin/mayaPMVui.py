"""
Name: 'Python Molecular Viewer GUI'
AutoDesk Maya: 2011
"""

__author__ = "Ludovic Autin"
__url__ = ["http://mgldev.scripps.edu/projects/ePMV/wiki/index.php/Main_Page",
           'http://mgldev.scripps.edu/projects/ePMV/update_notes.txt']
__version__="0.0.2a"
__doc__ = "ePMV v"+__version__
__doc__+"""\
Use maya as a molecular viewer

Provide gui interface to load and display Molecule Object (from pdb file for instance)
-load .pdb,.pdbqt,.pqr,.mol2,.cif
-display as CPK,Ball&Stick,Ribbon, MSMS and Coarse Molecular Surface
-color by: color,atom type, david goodsell atom type, resiude type, secondary structure type
-selection : any molecule levele MOL:CHAIN:RESIDUE:ATOM using keyword and picking functionality
-option available for : CPK, BS, CMS, MSMS under object selection...

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
#import pdb
#MAYA import
import maya
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx

import sys,os
#cmds.confirmDialog( title='About ePMV', message=about, button=['OK'], 
#                           defaultButton='OK')
                           
MGL_ROOT=""

prefpath=cmds.internalVar(userPrefDir=True)
os.chdir(prefpath)
os.chdir(".."+os.sep)
softdir = os.path.abspath(os.curdir)
mgldirfile=softdir+os.sep+"mgltoolsdir"
personalize = False
if os.path.isfile(mgldirfile) :
    f=open(mgldirfile,'r')
    MGL_ROOT=f.readline()
    f.close()
else :
    if len(MGL_ROOT) == 0 :
        MGL_ROOT = cmds.fileDialog2(fileMode=3, dialogStyle=1,
                                    cap="what is the path to MGLToolsPckgs?")
        MGL_ROOT = str(MGL_ROOT[0])
        personalize = True
    f=open(mgldirfile,'w')
    f.write(MGL_ROOT)
    f.close()

print MGL_ROOT
ICONSDIR=MGL_ROOT+os.sep+"MGLToolsPckgs"+os.sep+"Pmv"+os.sep+"hostappInterface"+os.sep+\
            "images"+os.sep+"icons"+os.sep
print ICONSDIR
#register plugin dir
#this is handle by the user
#plugpath=os.environ["MAYA_PLUG_IN_PATH"].split(":")
#uidir =MGL_ROOT+os.sep+"MGLToolsPckgs"+os.sep+"Pmv"+os.sep+"hostappInterface"+os.sep+"autodeskmaya"+os.sep+"plugin"
#if uidir not in plugpath:
#    os.environ["MAYA_PLUG_IN_PATH"] = os.environ["MAYA_PLUG_IN_PATH"]+":"+uidir

#how to personalize it...

def _reporthook(numblocks, blocksize, filesize, url=None, pb = None):
    #print "reporthook(%s, %s, %s)" % (numblocks, blocksize, filesize)
    base = os.path.basename(url)
    #XXX Should handle possible filesize=-1.
    try:
        percent = min((numblocks*blocksize*100)/filesize, 100)
    except:
        percent = 100
    if numblocks != 0:
        sys.stdout.write("\b"*70)
    sys.stdout.write("%-66s%3d%%" % (base, percent))
    if pb is not None:
        cmds.progressWindow( edit=True, 
                            progress=percent, 
                            status=('Downloading: ' + `amount` + '%' ) )

#is MGLTools Pacthed ie windows
if sys.platform == 'win32':
    #need to patch MGLTools first
    #first patch MGLTools
    #check if we need to patch
    mgltoolsDir = MGL_ROOT+os.sep+"MGLToolsPckgs"
    patch=os.path.isfile(mgltoolsDir+os.sep+"patched")
    if not patch :
        amount=0
        #need to test deeper. as it look like its slowing down the download...
        #cmds.progressWindow(    title='Patching MGLToolsPckgs with python2.6 system dependant modules',
        #                                progress=amount,
        #                                status='Sleeping: 0%',
        #                                isInterruptable=True )

        import urllib
        import tarfile 
#        c4d.gui.MessageDialog("Patching MGLToolsPckgs with python2.6 system dependant modules")
        print mgltoolsDir+os.sep
        patchpath = mgltoolsDir+os.sep
        URI="http://mgldev.scripps.edu/projects/ePMV/patchs/depdtPckgs.tar"
        tmpFileName = mgltoolsDir+os.sep+"depdtPckgs.tar"
        if not os.path.isfile(tmpFileName):
#            urllib.urlretrieve(URI, tmpFileName)
            urllib.urlretrieve(URI, tmpFileName,
                           lambda nb, bs, fs, url=URI: _reporthook(nb,bs,fs,url,pb=False))
            #geturl(URI, tmpFileName)
        TF=tarfile.TarFile(tmpFileName)
        TF.extractall(patchpath)
        #create the pacthed file
        f=open(mgltoolsDir+os.sep+"patched","w")
        f.write("MGL patched!")
        f.close()
#        c4d.gui.MessageDialog("MGLTools pacthed, click OK to continue")
        #cmds.progressWindow(endProgress=1)

#add to syspath
sys.path.append(MGL_ROOT+'/MGLToolsPckgs')

#ok now need to modify the shelf/preferences
#creating a shelf on the fly, but remember it...like first time runing
if personalize:
    from Pmv.hostappInterface.install_plugin import Installer
    epmvinstall = Installer(gui=False)
    plugdir = MGL_ROOT+os.sep+"MGLToolsPckgs"+os.sep+"Pmv"+os.sep+"hostappInterface"
    epmvinstall.personalizeMaya(plugdir,prefpath)
    #in that case we should restart...not sure will work
    cmds.confirmDialog( title='ePMV', message="You need to restart maya to see ePMV button", button=['OK'], 
                           defaultButton='OK')
if sys.platform == "win32":
    sys.path.append(MGL_ROOT+os.sep+'MGLToolsPckgs'+os.sep+'PIL')
else :
    sys.path[0]=(MGL_ROOT+'/lib/python2.5/site-packages')
    sys.path.insert(0,MGL_ROOT+'/lib/python2.5/site-packages/PIL')
    sys.path.append('/Library/Python/2.5/site-packages/')


from functools import partial

#pmv import
from Pmv.moleculeViewer import EditAtomsEvent
from MolKit.protein import ResidueSetSelector,Chain
from MolKit.molecule import Atom
from Pmv.pmvPalettes import AtomElements
from Pmv.pmvPalettes import RasmolAmino

#epmv import
from Pmv.hostappInterface.autodeskmaya.mayaAdaptor import mayaAdaptor
import Pmv.hostappInterface.autodeskmaya.helperMaya as hmaya
from Pmv.hostappInterface.install_plugin import Installer
from Pmv.hostappInterface import epmvGui
from Pmv.hostappInterface import comput_util as C

kPluginCmdName = "ePMV"
print kPluginCmdName
#pdb.set_trace()

#TODO
#1-restore
#2-dna color per residue
#3-test imd , pyrosetta, ARViewer etc..
#5-depthQ : fogShader for rendering...not realtime
# add option for MSMS and CMS (res,..)
#test session reading from PMV

def myfunc(inst=None, thing=None, arg=None):
    print 'arg: ', arg
    print 'inst: ', inst
    print 'thing: ', thing
    data = cmds.button(inst.btnA, query=True, label=True)
    print data


class ePMVsynchro:
    
    def __init__(self,epmv,period=0.1):
        self.period = period
        self.callback = None
        self.epmv = epmv
        self.mv = self.epmv.mv

    def change_period(self,newP):
        self.period = newP
        self.remove_callback()
        self.set_callback()
        
    def set_callback(self):
        self.callback = OpenMaya.MTimerMessage.addTimerCallback(self.period,self.doit)

    def remove_callback(self):
        OpenMaya.MMessage.removeCallback(self.callback)
        
    def doit(self,period,time,userData=None):
        #need to get the current selection
        # Create a selection list iterator
        #
        slist = OpenMaya.MSelectionList()
        OpenMaya.MGlobal.getActiveSelectionList(slist)
        sIter = OpenMaya.MItSelectionList(slist)

#        if hasattr(self.mv,'art'):
#            vp = doc.GetActiveBaseDraw() 
#            self.epmv.helper.updateImage(self.mv,viewport = vp)
        self.epmv.helper.updateCoordFromObj(self.mv,sIter,debug=True)

class ParameterModeller(epmvGui.ParameterModeller):

    def __init__(self,epmv=None):
        epmvGui.ParameterModeller.__init__(self,epmv=epmv)
        self.gui = None

    def CreateLayout(self):
        self.gui = cmds.window(title="Modeller", iconName='Modeller', widthHeight=(200, 100))
        cmds.frameLayout(label='Modeller optimizer',borderStyle='out')
        cmds.gridLayout(numberOfColumns=1,cellWidthHeight=(200, 20),columnsResizable=False)        
        self.CHECKBOXS["store"]["id"] = cmds.checkBox(label=self.CHECKBOXS["store"]['name'])
        self.NUMBERS["miniIterMax"]["id"] = cmds.intField(minValue=0, maxValue=10000, value=1000 )#max_iteration
        self.BTN["mini"]["id"] = cmds.button(l=self.BTN["mini"]['name'], c=partial(self.epmv.gui.do_modeller,"Minimize"))
        self.NUMBERS["mdIterMax"]["id"] = cmds.intField(minValue=0, maxValue=10000, value=1000 )#max_iteration
        self.NUMBERS["mdTemp"]["id"] = cmds.intField(minValue=0, maxValue=10000, value=300 )#temperature
        self.BTN["md"]["id"] = cmds.button(l=self.BTN["md"]['name'], c=partial(self.epmv.gui.do_modeller,"MD" ) )
        self.BTN["cancel"]["id"] = cmds.button(l=self.BTN["cancel"]['name'], c=partial(self.epmv.gui.do_modeller,"Cancel" ))
        cmds.setParent('..')
        cmds.setParent('..')
#        cmds.showWindow( self.MODGUI["ui"]  )
  

class ParameterScoring(epmvGui.ParameterScoringGui):

    def __init__(self,epmv=None):
        epmvGui.ParameterScoringGui.__init__(self,epmv=epmv)
        self.gui = None

    def CreateLayout(self):
        self.gui = cmds.window(title="AutoDock Scoring", iconName='ADscoring', 
                               widthHeight=(200, 100))
        cmds.frameLayout(label='Set up',borderStyle='out')
        cmds.gridLayout(numberOfColumns=2,cellWidthHeight=(100, 20),columnsResizable=False)
        
        cmds.text( label=self.TXT['rec']['name'] )
        self.TXT['rec']['id']=self.rec = cmds.textField(aie=True)#,enterCommand=self.fetchPDB
        cmds.textField(self.rec,e=True,tx="hsg1:::;")
        
        cmds.text( label=self.TXT['lig']['name'] )
        self.TXT['lig']['id']=self.lig = cmds.textField(aie=True)#,enterCommand=self.fetchPDB)
        cmds.textField(self.lig,e=True,tx="ind:::;")
        
        cmds.text( label='Scorer:' ) #scorer type choice
        self._scorertype=self.COMB_BOX["score"]["id"]=cmds.text( label='choose' )
        self.pscoretype=cmds.popupMenu( button=1 )
        for i,item in enumerate(self.scorertype) :
            cmds.menuItem(item,c=partial(self.COMB_BOX["score"]["action"],i))

        #checkbox option
        self.CHECKBOXS["store"]["id"] = cmds.checkBox(label=self.CHECKBOXS["store"]["name"])
        self.CHECKBOXS["displayLabel"]["id"] = cmds.checkBox(label=self.CHECKBOXS["displayLabel"]["name"])
        self.CHECKBOXS["realtime"]["id"] = cmds.checkBox(label=self.CHECKBOXS["realtime"]["name"],
                                                    cc=self.CHECKBOXS["realtime"]["action"])
        self.BTN['gScore']['id'] = cmds.button(label=self.BTN['gScore']['name'],c=self.BTN['gScore']['action'])
        cmds.setParent('..')
        cmds.setParent('..')
            
        cmds.frameLayout(label='Init/Doit',borderStyle='out')        
        cmds.gridLayout(numberOfColumns=1,cellWidthHeight=(200, 20),
                        columnsResizable=False)        
        
        self.BTN['ok']['id'] = cmds.button(label=self.BTN['ok']['name'],c=self.BTN['ok']['action'])
        
        self._currentscorer=self.COMB_BOX["scorer"]["id"]=cmds.text( label='scorer' )
        self.pcurrentscorer=cmds.popupMenu( button=1 )
        for i,item in enumerate(self.scoreravailable) :
            cmds.menuItem(item,c=partial(self.COMB_BOX["scorer"]["action"],item))
        cmds.setParent('..')
        cmds.setParent('..')
        
    def setRealtime(self,val):
        #this should be overwrite by the subclass as 
        if hasattr(self.epmv.mv,'energy'):
            self.epmv.mv.energy.realTime = val = cmds.checkBox(self.CHECKBOXS["realtime"]["id"],q=1,v=1)
#            self._setRealtime(val)
            self.epmv.mv.energy.display = bool(cmds.checkBox(self.CHECKBOXS["display"]["id"],q=1,v=1))
            
    def setCurrentScorer(self,val,arg):
        self.getScorerAvailable()
        #name = self.scoreravailable[val]
        sc = self.epmv.mv.energy.data[val]
        self._setCurrentScorer(sc)
        cmds.text( self._currentscorer,e=1,l=val)
    
    def setScorer(self,val,arg):
        self._scorer = self.scorertype[val]
        cmds.text( self._scorertype,e=1,l=self._scorer)

    def getScorerAvailable(self):
        self.scoreravailable = []
        if hasattr(self.epmv.mv,'energy'):
            self.scoreravailable = self.epmv.mv.energy.data.keys()
            
    def setup(self,val):
        rname = cmds.textField(self.TXT['rec']['id'],q=1,tx=1)
        #get Lig
        print rname
        lname = cmds.textField(self.TXT['lig']['id'],q=1,tx=1)
        print lname
        recSet=self.epmv.mv.expandNodes(str(rname))
        rec = recSet[0].top
        #=self.epmv.mv.getMolFromName(rname)
        ligSet=self.epmv.mv.expandNodes(str(lname))
        lig = ligSet[0].top
#        scorer_name = self._setup(str(rname),str(lname))
        scorer_name =  rec.name+'-'+lig.name+'-'+self._scorer
        if rec is not None and lig is not None:
            if not hasattr(self.epmv.mv,'energy'):
                self.epmv.mv.energy = C.EnergyHandler(self.epmv.mv)
            self.getScorerAvailable()                
            self.epmv.mv.energy.add(recSet,ligSet,score_type=self._scorer)
#            self.AddChild(self._currentscorer,len(self.scoreravailable),scorer_name)
            confNum = 1
            for mol in [rec,lig]:
                # check number of conformations available
                current_confNum = len(mol.allAtoms[0]._coords) -1
                mol.allAtoms.addConformation(mol.allAtoms.coords)
                mol.cconformationIndex = len(mol.allAtoms[0]._coords) -1
#            if scorer_name is not None :
            cmds.menuItem(p=self.pcurrentscorer,l=scorer_name,
                          c=partial(self.COMB_BOX["scorer"]["action"],scorer_name))
            cmds.text( self._currentscorer,e=1,l=scorer_name)
            self.setRealtime(None)
            val = cmds.checkBox(self.CHECKBOXS["display"]["id"],q=1,v=1)
            if val : self.initDisplay()
            else :
                self.epmv.mv.energy.labels = None
                self.epmv.mv.energy.display = False
            self.epmv.mv.energy.color = [0,1]
            
    def getScore(self,val):
        if hasattr(self.epmv.mv,'energy'):
            self.epmv.helper.get_nrg_score(self.epmv.mv.energy)
            
    def initDisplay(self):
        #label
        label = self.epmv.helper.newEmpty("label")
        #label.MakeTag(self.epmv.helper.LOOKATCAM)
        listeName=["score","el","hb","vw","so"]
        y=0.0
        self.listeO=[]
        for i,name in enumerate(listeName):
            o=cmds.textCurves( n= name, f='Courier', t=name+" : 0.00" )
            cmds.move(0.,y,0., o, absolute=True )
            cmds.parent( o, label)
            self.listeO.append(o)
            y+=5.0
        self.epmv.mv.energy.labels = self.listeO
        #constraint the label to be oriented toward the persp camera
        cmds.orientConstraint( 'persp', label )
        self.epmv.mv.energy.display = True

class epmvUI():
    def __init__(self, winName="ePMV",mv=None):
        self.winTitle = "ePMVgui"
        self.winName = winName
        #create epmv cession
        if mv == None:        
            epmv = mayaAdaptor(debug=0)
            self.mv = epmv.mv
            self.epmv = epmv
        else : self.mv = mv
        if not hasattr(self.mv,'molDispl') : self.mv.molDispl={}
        if not hasattr(self.mv,'selections') : self.mv.selections={}
        if not hasattr(self.mv,'iTraj') : self.mv.iTraj={}
        
        self.use_log = 1
        self.epmv.use_progressBar=False
        self.epmv.bicyl = True
        self.epmv.doCloud = False
        self.epmv.doCamera = False
        self.epmv.doLight = False
        self.epmv.center_mol = True
        self.epmv.center_grid = False
        
        #how put mv in the scope                    
        self.funcColor = [self.mv.colorByAtomType,self.mv.colorAtomsUsingDG,
                          self.mv.colorByProperty,self.mv.colorByResidueType,
                          self.mv.colorResiduesUsingShapely,
                          self.mv.colorBySecondaryStructure,
                          self.mv.color,
                          self.mv.colorByChains
                          ]
        self._forceFetch = False
        self._logConsole = False
        self._useModeller = self.epmv.useModeller = False
        self._modeller = False
        self._AF = False
        self._AR = False
        self._depthQ = False
        self._synchro = False #do we synchromize with model data, base on timer function
        self.epmv_synchro = None
        
        self.pdbtype = ['PDB', 'PDBTM', 'OMP', 'CIF','PQS']
        self.firsttraj = True
        self.current_traj = None
        self.indiceData = 0
        self.inst = None
        self.current_script=None
        self.current_mol=None
        self._pd = None   #autodock scoring gui
        self._mod = None #modeller gui
        self.icons = {}
        self.epmv.gui = self
        
    def initWidget(self):
        witdh = 100
        id =1 
        self.OPTIONS = {'cam':{"id": None, "name":"PMV camera",'width':witdh,
                               "height":10,"action":self.SetPreferences,"var":self.epmv.doCamera},
                       'light':{"id": None, "name":"PMV lights",'width':witdh,
                                "height":10,"action":self.SetPreferences,"var":self.epmv.doLight},
                       'clouds':{"id": None, "name":"Render points",'width':witdh,
                                 "height":10,"action":self.SetPreferences,"var":self.epmv.doCloud},
                       'cyl':{"id": None, "name":"Split bonds",'width':witdh,
                              "height":10,"action":self.SetPreferences,"var":self.epmv.bicyl},
                       'log':{"id": None, "name":"Console log",'width':witdh,
                              "height":10,"action":self.SetPreferences,"var":self._logConsole},
                       'center':{"id": None, "name":"Center Molecule",'width':witdh,
                                 "height":10,"action":self.SetPreferences,"var":self.epmv.center_mol},
                       'centerG':{"id": None, "name":"Center Grid",'width':witdh,
                                  "height":10,"action":self.SetPreferences,"var":self.epmv.center_grid},
                       'fetch':{"id": None, "name":"Force Fetch instead of cache",'width':witdh,
                                "height":10,"action":self.SetPreferences,'var':self._forceFetch},
#                       'depthQ':{"id": None, "name":"Environment depth cueing",
#                                 'width':witdh,"height":10,"action":self.SetPreferences,'var':self._depthQ}
                       'synchro':{"id": None, "name":"Model data synchro",'width':witdh,
                                "height":10,"action":self.SetPreferences,'var':self._synchro}
                       }
        if self._modeller :
            self.OPTIONS["modeller"] = {"id": None, "name":"Modeller",'width':witdh,
                                        "height":10,"action":self.SetPreferences,
                                        'var':self._useModeller}
        self.MENU_ID = [
            ["File",
                [{"id": id, "name":"Open PDB","action":self.browseFile},
                  {"id": id+1, "name":"Open Data","action":self.buttonLoadData},
                ],
            ],
            ["Edit" ,
                [{"id": id+2, "name":"Options","action":None,"sub":self.OPTIONS},],
            ],
            ["Extensions" , 
                [{"id": id+3, "name":"PyAutoDock","action":self.do_AutoDock},],
            ],
            ["Help" , 
                [{"id": id+4, "name":"About ePMV","action":self.drawAbout},
                {"id": id+5, "name":"ePMV documentation","action":self.launchBrowser},
                {"id": id+6, "name":"Check for Update","action":self.check_update},
                {"id": id+7, "name":"Citation Information","action":self.citationInformation},
                ],
            ]
        ]
        
        if self._AF :
            self.MENU_ID[2][1].append({"id": None, "name":"AutoFill",
                                                "action":None})
        if self._AR :
            self.MENU_ID[2][1].append({"id": None, "name":"ARViewer",
                                                "action":None})
        if self._modeller:            
            self.MENU_ID[2][1].append({"id": None, "name":"Modeller",
                                                "action":self.modellerGUI})
        self.MENU_ID[2][1].append({"id": None, "name":"Add an Extension",
                                                "action":self.addExtension})
        
        self.PMV_BTN = {"id":None,"name":"Submit/exec",'width':80,"height":10,
                         "action":self.execPmvComds}
        
        self.keywords = ['keywords:','  backbone','  sidechain','  chain','  picked']
        kw=map(lambda x:"  "+x,ResidueSetSelector.residueList.keys())
        self.keywords.extend(kw)

        self.scriptliste = ['Load','pymol_demo','interactive_docking','colorbyAPBS','demo1','user_script']
        self.scriptsave = ['Save','Save as']
        
        
    def create(self):
        self.checkExtension()
        if cmds.window(self.winName, exists=True):
            cmds.deleteUI(self.winName)
        self.initWidget()
        cmds.window(self.winName, menuBar=True,title=self.winTitle)
        #self.mainCol = cmds.columnLayout( adjustableColumn=True )
        for menu in self.MENU_ID:
            cmds.menu( label=menu[0], tearOff=True , parent = self.winName)
            for elem in menu[1]:
                if elem["name"] == "Options" : checkBox=True
                else : checkBox=False
                if elem.has_key("sub"):
                    elem['id']=cmds.menuItem(subMenu=True, label=elem["name"])
                    for sub in elem['sub'].keys():
                        if elem['sub'][sub]["action"] is not None :
                            elem['sub'][sub]['id']=cmds.menuItem( label=elem['sub'][sub]["name"],
                                                            checkBox=checkBox,
                                                            c=elem['sub'][sub]["action"])
                        else :
                            elem['sub'][sub]['id']=cmds.menuItem( label=elem['sub'][sub]["name"],
                                                            checkBox=checkBox,)
                        if checkBox and elem['sub'][sub].has_key("var"):
                            cmds.menuItem(elem['sub'][sub]['id'],e=1,checkBox=bool(elem['sub'][sub]['var']))
                    cmds.setParent( '..', menu=True )
                else:
                    if elem["action"] is not None :
                        elem['id']=cmds.menuItem( label=elem["name"],c=elem["action"])
                    else :
                        elem['id']=cmds.menuItem( label=elem["name"])
        cmds.scrollLayout()
        cmds.columnLayout(adjustableColumn=True)

        #layout = cmds.gridLayout(numberOfColumns=2,cellWidthHeight=(200, 20),columnsResizable=False)
        cmds.frameLayout(label='Molecule Input',borderStyle='out')
        cmds.gridLayout(numberOfColumns=2,cellWidthHeight=(200, 20),columnsResizable=False)        
        
        self.btnBrowse = cmds.button( label='Browse', c=partial(self.browseFile,))
        cmds.text( label=' to a PDB file or enter a 4 digit ID (e.g. 1crn)' )
        #cmds.text( label='or enter a 4 digit ID code (e.g. 1crn)' )
        
        
        #self._pdbtype = cmds.textScrollList( numberOfRows=len(self.pdbtype), allowMultiSelection=False,
        #                append=self.pdbtype,
        #                selectItem='PDB', showIndexedItem=1 )
        self.pdbid = cmds.textField(aie=True,enterCommand=self.fetchPDB)
        cmds.textField(self.pdbid,e=True,tx="1crn")
        self.btnA = cmds.button( label='Fetch', c=partial(self.fetchPDB,))
        cmds.popupMenu( button=1 )
        for item in self.pdbtype :
            cmds.menuItem(item,c=partial(self.fetchPDB,item))
        cmds.setParent('..')
        cmds.setParent('..')
        
        layout = cmds.frameLayout(label='Current selection',borderStyle='out')
        cmds.rowLayout(numberOfColumns=2, columnWidth2=(200, 200), adjustableColumn=2, 
                       columnAlign=(1, 'right'), 
                       columnAttach=[(1, 'left', 0), (2, 'both', 0)] )
        
        cmds.text( label='Current Selection:' )
        self.mol=cmds.text( label='e.g. 1crn' )
        self.pmol=cmds.popupMenu( button=1 )
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=2, columnWidth2=(200, 200), adjustableColumn=2, 
                       columnAlign=(1, 'right'), 
                       columnAttach=[(1, 'left', 0), (2, 'both', 0)] )    
        #self.mol = cmds.iconTextScrollList(allowMultiSelection=False)
        cmds.text( label='Add selection set using string or' )
        cmds.text( label='keywords' )
        self._keywords=cmds.popupMenu( button=1 )
        for item in self.keywords :
            cmds.menuItem(item,c=partial(self.setKeywordSel,item))
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=2, columnWidth2=(200, 200), adjustableColumn=2, 
                       columnAlign=(1, 'right'), 
                       columnAttach=[(1, 'left', 0), (2, 'both', 0)] )    
        
        self.selection = cmds.textField(aie=True,w=200)
        cmds.text( label='edit Selection:' )
        cmds.popupMenu( button=1 )
        cmds.menuItem( label='Save set',c=partial(self.add_selection,))
        cmds.menuItem( label='Rename set',c=partial(self.rename_selection,) )
        cmds.menuItem( label='Delete set',c=partial(self.delete_selection,) )
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=2, columnWidth2=(200, 200), adjustableColumn=2, 
                       columnAlign=(1, 'right'), 
                       columnAttach=[(1, 'left', 0), (2, 'both', 0)] )    

        self.delmol = cmds.button( label='Delete', c=self._deleteMol)
        cmds.text( label='Atoms in the Selection Set' )
        #self.savesel = cmds.button( label='Save selection', c=partial(self._saveSelection,))
        #self.create_dashboard(layout)
        cmds.setParent('..')
        cmds.setParent('..')
        
        #cmds.frameLayout(label='Dashboard/Tree',labelAlign='top',borderStyle='out')        
        #layout = cmds.gridLayout(cellWidthHeight=(400, 100),columnsResizable=False)

        #self.dash = cmds.treeView(numberOfButtons = 5, abr = False )
        #self.create_dashboard()
        #cmds.formLayout(layout,e=True, attachForm=(self.dash,'top', 2))
        #cmds.formLayout(layout,e=True, attachForm=(self.dash,'left', 2))
        #cmds.formLayout(layout,e=True, attachForm=(self.dash,'bottom', 2))
        #cmds.formLayout(layout,e=True, attachForm=(self.dash,'right', 2))
        #cmds.setParent('..')
        #cmds.setParent('..')
            
        cmds.frameLayout(label='Molecular Representations',borderStyle='out')        
        cmds.gridLayout(numberOfColumns=1,cellWidthHeight=(400, 20),
                        columnsResizable=False)
        #self.cpk = cmds.checkBox( label='CPK', cc=self._displayCPK )

        self.cpk = cmds.iconTextCheckBox( label='Atoms', style='iconAndTextHorizontal', 
                                       image1=ICONSDIR+'waterIcon_26.xpm', cc=self._displayCPK )
        #self.cpk_slider = cmds.floatSlider( min=0., max=10., value=1., step=0.01 ,dc=self._displayCPK)
        self.cpk_slider = cmds.floatSliderGrp( label='cpk radii scale', field=True, minValue=0.0, 
                                              maxValue=5.0, fieldMinValue=0.0, 
                                              fieldMaxValue=5.0, value=1. , step=0.01,
                                              dc=self._displayCPK,
                                              cc=self._displayCPK,
                                              cal=[1,"left"])

        self.bs = cmds.iconTextCheckBox( label='Sticks',style='iconAndTextHorizontal', 
                                       image1=ICONSDIR+'bs.xpm', cc=self._displayBS )
        #cmds.gridLayout(numberOfColumns=2,cellWidthHeight=(100, 20),
        #                columnsResizable=True)
        self.bs_slider = cmds.floatSliderGrp( label='b&s radii scale', field=True, minValue=0.0, 
                                              maxValue=5.0, fieldMinValue=0.0, 
                                              fieldMaxValue=5.0, value=1. , step=0.01,
                                              dc=self._displayBS,
                                              cc=self._displayBS,
                                              cal=[1,"left"])
        self.bs_ratio = cmds.floatSliderGrp( label='B/S ration', field=True, minValue=0.0, 
                                              maxValue=10.0, fieldMinValue=0.0, 
                                              fieldMaxValue=10.0, value=1.5 , step=0.01,
                                              dc=self._displayBS,
                                              cc=self._displayBS,
                                              cal=[1,"left"]) 
        #cmds.setParent('..')
        #cmds.setParent('..')
        
        #cmds.frameLayout(label='Molecule Display',labelAlign='top',borderStyle='out')
        #cmds.gridLayout(numberOfColumns=2,cellWidthHeight=(200, 20),
        #                columnsResizable=False)
        self.ss = cmds.iconTextCheckBox( label='Ribbons',style='iconAndTextHorizontal', 
                                       image1=ICONSDIR+'ss.xpm', cc=self._displaySS )
        #self.bs_slider = cmds.floatSlider( min=0., max=10., value=1., step=0.01 ,dc=self._displayBS)
        #cmds.text( label='ss options?' )
        
        self.msms = cmds.iconTextCheckBox( label='MSMSurf', style='iconAndTextHorizontal', 
                                       image1=ICONSDIR+'ms.xpm',cc=self._displaySurf )
        self.msms_slider = cmds.floatSliderGrp( label='Probe radius', field=True,
                                               minValue=0.01, maxValue=20., 
                                               fieldMinValue=0.01, fieldMaxValue=20.0,
                                               value=1., step=0.1 ,
                                               dc=self._updateSurf,
                                               cc=self._updateSurf,
                                               cal=[1,"left"]) #cc or dc
        self.cms = cmds.iconTextCheckBox( label='CoarseMolSurf',style='iconAndTextHorizontal', 
                                       image1=ICONSDIR+'ms.xpm', cc=self._displayCoarse )
        self.cms_slider = cmds.floatSliderGrp( label='Iso value', field=True,
                                            minValue=0.01, maxValue=20., 
                                            fieldMinValue=0.01, fieldMaxValue=20.0,
                                            value=7.1, step=0.1 ,
                                            dc=self._updateCoarse,
                                            cc=self._updateCoarse,
                                            cal=[1,"left"])
        cmds.setParent('..')
        cmds.setParent('..')
        
        cmds.frameLayout(label='Specials Representations',borderStyle='out')
        cmds.gridLayout(numberOfColumns=2,cellWidthHeight=(200, 20),
                        columnsResizable=False)
        self.loft = cmds.iconTextCheckBox( label='Loft',style='iconAndTextHorizontal', 
                                       image1=ICONSDIR+'loft_icon.jpg', cc=self._displayLoft )

        self.spline = cmds.iconTextCheckBox( label='Spline',style='iconAndTextHorizontal', 
                                       image1=ICONSDIR+'loft_icon.jpg', cc=self._displaySpline )

        self.armature = cmds.iconTextCheckBox( label='Armature',style='iconAndTextHorizontal', 
                                       image1=ICONSDIR+'armature_icon.jpg', cc=self._displayArmature )

        self.meta = cmds.iconTextCheckBox( label='Metaballs (particles)',style='iconAndTextHorizontal', 
                                       image1=ICONSDIR+'metaball_icon.jpg', cc=self._displayMeta )
        cmds.setParent('..')
        cmds.setParent('..')
        
        cmds.frameLayout(label='Color scehem',borderStyle='out')
        cmds.gridLayout(numberOfColumns=3,cellWidthHeight=(133, 20),
                        columnsResizable=False)
        #fix me, not the best way to do it
        self.color_collection = cmds.radioCollection()
        self.col=[]
        self.col.append(cmds.radioButton( label='Atoms using CPK' ,cc=self._color).split("|")[-1])
        self.col.append(cmds.radioButton( label='AtomsDG (polarity/charge)' ,cc=self._color).split("|")[-1])
        self.col.append(cmds.radioButton( label='Rainbow from N to C' ,cc=self._color).split("|")[-1])
        self.col.append(cmds.radioButton( label='Per residue' ,cc=self._color).split("|")[-1])
        self.col.append(cmds.radioButton( label='Per residue Shapely' ,cc=self._color).split("|")[-1])
        self.col.append(cmds.radioButton( label='Secondary Structure' ,cc=self._color).split("|")[-1])
        self.col.append(cmds.radioButton( label='Custom color',cc=self._color ).split("|")[-1])
        self.col.append(cmds.radioButton( label='Chains' ,cc=self._color).split("|")[-1])
        self.col.append(cmds.radioButton( label='Temperature Factor' ,cc=self._color).split("|")[-1])
        self.col.append(cmds.radioButton( label='sas area' ,cc=self._color).split("|")[-1])
        #had the color chooser

        cmds.setParent('..')
        cmds.setParent('..')
        self.unic_col = cmds.colorSliderButtonGrp(label='Choose a color to apply ',rgb=(1, 0, 0), 
                                                  symbolButtonDisplay=False,
                                                  bl = 'color',
                                                  bc = self._color,
                                                  cc = self._color)

        #Data Player
        cmds.frameLayout(label='Datas Area',borderStyle='out')
        cmds.gridLayout(numberOfColumns=1,cellWidthHeight=(400, 20),
                        columnsResizable=True)
        self.btnBrowseData = cmds.button( label='Browse to load a Data file', c=partial(self.buttonLoadData,))
        #cmds.text( label=' to load a Data file' )

        cmds.text( label='Apply ... to current selection and play below:' )
        self.trajbox=cmds.popupMenu( button=1 )
        #for item in self.pdbtype :
        #    cmds.menuItem(item,c=partial(self.fetchPDB,item))

        #cmds.text( label='to current selection and play below:' )

        self.dataSlider = cmds.floatSliderGrp( label='Apply state', field=True,
                                               minValue=0.01, maxValue=20., 
                                               fieldMinValue=0.01, fieldMaxValue=20.0,
                                               value=1., step=0.1 ,dc=self._applyState,
                                               cal=[1,"left"],cc=self._applyState) #cc or dc
        cmds.setParent('..')
        cmds.setParent('..')

        #cmds.gridLayout(numberOfColumns=3,cellWidthHeight=(133, 20),
        #                columnsResizable=True)
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(200, 100, 100), adjustableColumn=2, 
                       columnAlign=(1, 'right'), 
                       columnAttach=[(1, 'left', 0), (2, 'both', 0), (3, 'both', 0)] )
        cmds.text( label="PMV-python script commands:")
        cmds.button( label="Open")
        cmds.popupMenu( button=1 )
        for item in self.scriptliste :
            cmds.menuItem(item,c=partial(self.set_ePMVScript,item))        
        cmds.button( label="Save")
        cmds.popupMenu( button=1 )
        for item in self.scriptsave :
            cmds.menuItem(item,c=partial(self.save_ePMVScript,item))  
        cmds.setParent('..')
        cmds.setParent('..')
        #python PMV commands script
        cmds.frameLayout(label='Scripts Area',borderStyle='out')
        #cmds.gridLayout(numberOfColumns=1,cellWidthHeight=(200, 20),
        #                columnsResizable=False)
        self.pmvcmds=cmds.cmdScrollFieldExecuter(width=400, height=100, sourceType="python")
        exple = """
print 'put your own commands here'
print 'with self = PMV instance, and epmv as ePMV'
"""
        cmds.cmdScrollFieldExecuter(self.pmvcmds,e=1,t=exple)
        self.PMV_BTN['id'] = cmds.button( label=self.PMV_BTN['name'], c=partial(self.PMV_BTN['action'],))
        #cmds.setParent('..')
        cmds.setParent('..')

#        cmds.frameLayout(label='ProgessBar',labelAlign='top',borderStyle='in')        
#        cmds.columnLayout()        
#        #self.btnC = cmds.button( label='Press Me - Internal Func No Args', c=self.b)
#        #self.btnB = cmds.button( label='Press Me - Internal Func', c=partial(self.a, 'something...') )
#        #self.btnC = cmds.button( label='Press Me - Internal Func No Args', c=self.b)
#        self.progressControl = cmds.progressBar(maxValue=100, width=400)
#        #cmds.button( label='Make Progress!', command='cmds.progressBar(self.progressControl, edit=True, step=1)' )
#        #cmds.progressBar(self.progressControl, edit=True, step=1)
#        #hmaya.PROGRESS_BAR = self.progressControl
#        maya.pb = self.progressControl
#        cmds.setParent('..')
#        cmds.setParent('..')
        cmds.text( label='ePMV '+__version__ )
        cmds.picture( image=ICONSDIR+'banner.jpg')#''ePMV_banner.xpm' )
        allowedAreas = ['right', 'left']
        cmds.dockControl( l="ePMV",area='left', content=self.winName, allowedArea=allowedAreas )
       
        #cmds.showWindow( self.winName )
        #cmds.window(self.winName, edit=True, t="ePMV",widthHeight=[420,820])
        #return self        

    def create_dashboard(self,layout):
        self.dash = cmds.treeView( numberOfButtons = 5, abr = False )
        #cmds.treeView( self.dash, e=True, pressCommand=[1,self._displayCPK])
        #cmds.treeView( self.dash, e=True, pressCommand=[2,self._displayBS])
        #cmds.treeView( self.dash, e=True, pressCommand=[3,self._displaySS])
        #cmds.treeView( self.dash, e=True, pressCommand=[4,self._displaySurf])
        #cmds.treeView( self.dash, e=True, pressCommand=[5,self._displayCoarse])
        
        #cmds.treeView(self.dash,e=True,bs=    [string, int, string],i=    [string, int, string]
        #cmds.formLayout(layout,e=True, attachForm=(self.dash,'top', 2))
        #cmds.formLayout(layout,e=True, attachForm=(self.dash,'left', 2))
        #cmds.formLayout(layout,e=True, attachForm=(self.dash,'bottom', 2))
        #cmds.formLayout(layout,e=True, attachForm=(self.dash,'right', 2))
    
    def addItemDash(self,item,parent=None):
        if parent == None : parent = ""
        cmds.treeView( self.dash, e=True, addItem = (item, parent))
        icons = ["waterIcon_26.xpm","bs.xpm","ss.xpm","ms.xpm","ms.xpm"]
        for i in range(1,6):
            cmds.treeView(self.dash,e=True, bs=    [item, i, "2StateButton"],
                      i=[item, i, icons[i-1]])
                      
    def addMolToDash(self,mol):
        self.addItemDash(mol.name)
        #cmds.treeView( self.dash, e=True, pressCommand=[mol.name,1,"maya.epmvui._displayCPK"])
        #cmds.treeView( self.dash, e=True, pressCommand=[mol.name,2,self._displayBS])
        #cmds.treeView( self.dash, e=True, pressCommand=[mol.name,3,self._displaySS])
        #cmds.treeView( self.dash, e=True, pressCommand=[mol.name,4,self._displaySurf])
        #cmds.treeView( self.dash, e=True, pressCommand=[mol.name,5,self._displayCoarse])

        for c in mol.chains:
            self.addItemDash(c.name,mol.name)
            for r in c.residues:
                self.addItemDash(r.name,c.name)
                for at in r.atoms:
                    self.addItemDash(at.full_name(),r.name)
                    
    #def update_dashboard(self):

    def checkExtension(self):
        if self.inst is None :
            self.inst = Installer(gui=False)
            self.inst.mgltoolsDir=MGL_ROOT
            self.inst.currDir=MGL_ROOT+os.sep+"MGLToolsPckgs"+os.sep+"Pmv"+os.sep+"hostappInterface"+os.sep
        self.inst.getExtensionDirFromFile()
        for i,ext in enumerate(self.inst.extensions):
            if self.inst.extdir[i] not in sys.path :
                sys.path.append(self.inst.extdir[i])
                if ext.lower() == 'modeller' :
                    sys.path.append(self.inst.extdir[i]+"/python2.5")
        if not self._modeller:
            try :
                import modeller
                self._modeller = True
                #self._useModeller = True
            except:
                print "noModeller"
        if not self._AF:
            try :
                import AutoFill
                self._AF = True
            except:
                print "noModeller"
        if not self._AR:
            try :
                import ARViewer
                self._AR = True
            except:
                print "noModeller"


    def getMolName(self,forupdate=False):
        selname = cmds.text(self.mol,q=1,l=1)
        if selname in self.mv.molDispl.keys(): 
            mname = selname
        else :
            mname=""
            for mname in self.mv.selections.keys():
                for sname in self.mv.selections[mname].keys():
                    if selname == sname :
                        break
            if mname=="":
                return selname,None
        #name = cmds.iconTextScrollList(self.mol,q=1,si=1)    
        mol = self.mv.getMolFromName(str(mname))
        if forupdate : return selname, mol
        return mol.name,mol

    def getGeomActive(self):
        lgeomName=[]
        mname,mol=self.getMolName()
        self.mv.molDispl[str(mol.name)]
        #sel=self.getSelectionLevel(mol)
        #selname=self.getSelectionName(sel,mol)         
        if cmds.iconTextCheckBox(self.msms,q=1,v=1) :
            sname='MSMS-MOL'+str(mol.name)
            #if sel != mname :sname='MSMS-MOL'+str(selname)       
            lgeomName.append(sname)
        if cmds.iconTextCheckBox(self.cpk,q=1,v=1) : lgeomName.append('cpk')
        if cmds.iconTextCheckBox(self.ss,q=1,v=1) : lgeomName.append('secondarystructure')
        if cmds.iconTextCheckBox(self.bs,q=1,v=1) : 
            lgeomName.append('balls')
            lgeomName.append('sticks')
        if cmds.iconTextCheckBox(self.cms,q=1,v=1) : 
            sname='CoarseMS'+str(mol.name)
            #if sel != str(mname) :sname='CoarseMS'+str(selname)       
            lgeomName.append(sname)
        #add loft and metaball
        return lgeomName

    def modelData(self,dataname=None,molname=None,adt=False):
        if molname == None :
            mname,mol=self.getMolName()   
            trajname = mname+'.model'
            if adt:
                trajname = mname+'.dlg'
            #self.mv.iMolData[mname].append(trajname)
        else :
            mname = molname
            if dataname == None :
                trajname = mname+'.model'
                if adt:
                    trajname = mname+'.dlg'
            else :
                trajname = dataname
        self.mv.iMolData[mname].append(trajname)
        self.current_traj=[trajname,"model"]
        dataname=trajname#
        cmds.menuItem(label=dataname,parent=self.trajbox,
                      c=partial(self.updateTraj,dataname))
        self.mv.iTraj[dataname]=[trajname,"model"]
        self.firsttraj=False
        self.current_traj=[trajname,"model"]
        self.indiceData += 1

    def gromacsTraj(self,file=None,dataname=None,molname=None):
        if molname == None :
            self.mv.openTrajectory(file, log=0)
            trajname=os.path.basename(file)
            #print trajname
            mname,mol=self.getMolName()   
            self.mv.iMolData[mname].append(trajname)
            self.mv.playTrajectory(mname, trajname, log=0)
        else :
            mname = molname
            trajname = dataname
        dataname=trajname#
        cmds.menuItem(label=dataname,parent=self.trajbox,
                      c=partial(self.updateTraj,dataname))
        self.indiceData += 1
        self.mv.iTraj[dataname]=[self.mv.Trajectories[trajname],"traj"]
        self.firsttraj=False
        self.current_traj=[self.mv.Trajectories[trajname],"traj"]
        self.nF=self.current_traj[0].maxi

    def gridData(self,file=None,dataname=None,molname=None):
        if molname == None :
            self.mv.readAny(file)
            sys.stderr.write('DObe')
            name = self.mv.grids3D.keys()[-1] #the last read data
            mname,mol=self.getMolName()
            self.mv.cmol = mol
            sys.stderr.write('before Select and isoContour')            
            self.mv.isoC.select(grid_name=name)           
            self.mv.isoC(self.mv.grids3D[name],name=mname+"IsoSurface",
                        isovalue=25.)#self.mv.grids3D[name].mean)  
            trajname=name#os.path.basename(filename)
            #print trajname
            if mname == "" and "IsoSurface" not in self.mv.iMolData.keys():
                self.mv.iMolData["IsoSurface"]=[]
                mname = "IsoSurface"
            self.mv.iMolData[mname].append(file)
        else :
            mname = molname
            trajname = dataname
        #self.mv.playTrajectory(mname, trajname, log=0)
        dataname=os.path.basename(trajname)
        cmds.menuItem(label=dataname,parent=self.trajbox,
                      c=partial(self.updateTraj,dataname))
        self.indiceData += 1
        self.mv.iTraj[dataname]=[self.mv.grids3D[trajname],"grid"]
        self.firsttraj=False
        self.current_traj=[self.mv.grids3D[trajname],"grid"]
        self.nF=self.current_traj[0].maxi

    def buttonLoadData(self,txt,model=False,trajname=None,molname=None,adt=False):
        if trajname == None :
            if model : 
                self.modelData(molname=molname,adt=adt)
                return True
            filename = cmds.fileDialog()
            print filename
            if filename is None or len(filename) == 0:
                return
            #else :
            extension=os.path.splitext(os.path.basename(filename))[1] #.xtc,.trj,etc..
            if extension == '.xtc' : self.gromacsTraj(file=filename)
            else : self.gridData(file=filename)
            #elif extension == '.map' : self.gridData_1(file=filename)

    def updateTraj(self,val,arg):
        print val,arg
        self.current_traj=self.mv.iTraj[val]
        mini,maxi,default,step = self.epmv.updateTraj(self.current_traj)
        cmds.floatSliderGrp(self.dataSlider,e=1,minValue=float(mini), maxValue=float(maxi), 
                                               fieldMinValue=float(mini), fieldMaxValue=float(maxi),
                                               value=float(default),step=float(step))

    def _applyState(self,val):
        #frame=self.GetLong(self.slider)
        mname,mol=self.getMolName()
        print self.current_traj
        traj = self.current_traj
        if traj is not None : 
            if traj[1] in ["model" ,"traj"]:
                conf = cmds.floatSliderGrp(self.dataSlider,q=1,v=1)
                self.epmv.updateData(traj,int(conf))
                if self.mv.molDispl[mname][3] : self._updateSurf(None)
                if self.mv.molDispl[mname][4] : self._updateCoarse(None)                
            elif self.current_traj[1] == "grid":
                iso=cmds.floatSliderGrp(self.dataSlider,q=1,v=1)#isovalue
                self.mv.isoC(self.current_traj[0],isovalue=iso,name=mname+"IsoSurface")       
            elif hasattr(self.current_traj,'GRID_DATA_FILE'):
                #grid
                iso=cmds.floatSliderGrp(self.dataSlider,q=1,v=1)#isoself.GetReal(self.slider)
                self.mv.setIsovalue(self.current_traj[0].name,iso, log = 1)          
        self.updateViewer()
        #return True

    def getData(self,molname,adt=False):
        if molname in self.mv.Mols.name : self.mv.hostApp.driver.duplicatemol=False
        self.mv.assignAtomsRadii(str(molname), united=0, log=0, overwrite=1)
        self.epmv._addMolecule(molname)
        #add a child to mol pop up menu
        cmds.menuItem(p=self.pmol,l=str(molname),c=partial(self.setCurMol,str(molname)))
        cmds.text(self.mol,e=1,l=str(molname))
        #cmds.iconTextScrollList(self.mol,edit=True, append=(str(molname)),selectItem=str(molname))
        mol = self.mv.getMolFromName(molname)
        if len(mol.allAtoms[0]._coords) > 1 or self._useModeller : 
            #need a test about trajectories...
            doit=True           
            if len(self.mv.iMolData[mol.name]) != 0 : #ok data
                for dataname in self.mv.iMolData[mol.name] : 
                    if dataname.find('xtc') != -1 : 
                        doit= False                             
            if doit : self.buttonLoadData(None,model=True,molname=molname,adt=adt)
        self.current_mol = mol
        
    def browseFile(self,txt):
        #get the text area  
        adt=False
        name = cmds.fileDialog()
        if name is None or len(name) == 0:
            return
        if name is not None:
            molname=os.path.splitext(os.path.basename(name))[0]  
            ext = os.path.splitext(os.path.basename(name))[1]
            if ext == '.dlg' :#Autodock
                self.mv.readDLG(name,1,0) #addToPrevious,ask
                self.mv.showDLGstates(self.mv.Mols[-1])
                molname = self.mv.Mols[-1].name
                adt=True
            if molname in self.mv.Mols.name : self.mv.hostApp.driver.duplicatemol=True 
            #modeller ?
            #load in Modeller
            if self._useModeller :
                from Pmv.hostappInterface.extension.Modeller.pmvAction import setupMDL
                name,mdl = setupMDL(self.env,str(name))
            if not adt :
                self.mv.readMolecule(str(name),log=1)
                if self._useModeller :
                    self.mv.Mols[-1].mdl=mdl
            molname = self.mv.Mols[-1].name
        else :
            #dialog ?
            return True
        self.getData(molname,adt=adt)
        self.updateViewer()
        
    def fetchPDB(self,txt,arg2=None):
        #get the text area    
        name = cmds.textField(self.pdbid,q=1,tx=1)
        name = str(name)
        if txt in self.pdbtype : 
            type = txt
        else :
            type = "PDB"
        if len(name) == 4 or len(name.split(".")[0]) == 4 :
            print "PDB id, webdownload"
            molname=name.upper()
            if molname in self.mv.Mols.name : self.mv.hostApp.driver.duplicatemol=True
            self.mv.fetch.db = type
            mol = self.mv.fetch(molname, log=self.use_log,f=self._forceFetch)           
            if mol is None :
                return True
            self.getData(self.mv.Mols[-1].name)
            self.updateViewer()
        
    def _displayCPK(self,val=None):
        #print val,val2
        #print cmds.treeView(self.dash,q=1,si=1)
        #return
        mname,mol=self.getMolName()
        sel=self.getSelectionLevel(mol)
        selection = self.mv.select(str(sel),negate=False, only=True, xor=False, 
                                   log=0, intersect=False)

        scale = cmds.floatSliderGrp(self.cpk_slider,q=1,v=1)
        display = cmds.iconTextCheckBox(self.cpk,q=1,v=1)        
        self.mv.hostApp.driver.use_instances=True
        if not isinstance(selection,Atom) : selection = selection.findType(Atom)
        max = len(selection)
        self.mv.displayCPK(sel,log=self.use_log,negate=not bool(display),scaleFactor = float(scale))
        self.mv.molDispl[str(mname)][0]=bool(display)

    def _displayBS(self,val):
        mname,mol=self.getMolName()
        print "BS", mname
        scale = cmds.floatSliderGrp(self.bs_slider,q=1,v=1)
        ratio = cmds.floatSliderGrp(self.bs_ratio,q=1,v=1)
        #val = self.get(self._box)
        #ind=int(val-self.indice_mol)
        #mname = self.mv.Mols[ind].name
        display = cmds.iconTextCheckBox(self.bs,q=1,v=1)        
        self.mv.hostApp.driver.use_instances=True#bool(self.get(self.instance))
        sel=self.getSelectionLevel(mol)
        selection = self.mv.select(str(sel),negate=False, only=True, xor=False, log=0, intersect=False)
        #print selection
        if not isinstance(selection,Atom) : selection = selection.findType(Atom)
        #max = len(selection)
        cradius = 0.3/ratio
        self.mv.displaySticksAndBalls(sel,log=self.use_log,negate=not display,
                    sticksBallsLicorice='Sticks and Balls', bquality=0, 
                    cradius=cradius*scale, only=False, bRad=0.3*scale, bScale=0.0)
        self.mv.molDispl[str(mname)][1]=bool(display)

    def _displaySS(self,val):
        #c4d.set_mouse_pointer(c4d.MOUSE_BUSY)
        mname,mol=self.getMolName()
        display = cmds.iconTextCheckBox(self.ss,q=1,v=1)        
        sel=self.getSelectionLevel(mol)       
        self.mv.displayExtrudedSS(sel, negate=(not bool(display)), only=False, log=1)        
        #self.mv.colorByAtomType(str(mname), ['secondarystructure'], log=1)
        self.mv.molDispl[str(mname)][2]=bool(display)

    def _updateSurf(self,val):
       #c4d.set_mouse_pointer(c4d.MOUSE_BUSY)
       mname,mol=self.getMolName()
       #print "SURF", mname 
       name='MSMS-MOL'+str(mol.name)
       sel=self.getSelectionLevel(mol)
       selname=self.getSelectionName(sel,mol)
       if sel != mname :
           name='MSMS-MOL'+str(selname)       
           permol=0
       else : permol=1       
       #print "msms surf name ",name,permol
       #permol=1       
       display = cmds.iconTextCheckBox(self.msms,q=1,v=1)               
       pRadius = cmds.floatSliderGrp(self.msms_slider,q=1,v=1)
       if name in mol.geomContainer.geoms :
           if pRadius == 0.0 : pRadius = 0.01
           self.mv.computeMSMS(sel, log=1, display=display, pRadius=pRadius, perMol=permol,surfName=name)
           self.mv.molDispl[mname][3]=bool(display)

    def _displaySurf(self,private):
       #c4d.set_mouse_pointer(c4d.MOUSE_BUSY)
       mname,mol=self.getMolName()
       print "SURF", mname 
       name='MSMS-MOL'+str(mol.name)
       sel=self.getSelectionLevel(mol)
       selname=self.getSelectionName(sel,mol)
       if sel != mname :
           name='MSMS-MOL'+str(selname)       
           permol=0
       else : permol=1       
       #print "msms surf name ",name,permol
       #permol=1       
       display = cmds.iconTextCheckBox(self.msms,q=1,v=1)               
       pRadius = cmds.floatSliderGrp(self.msms_slider,q=1,v=1)
       if name in mol.geomContainer.geoms :
            print name           
            self.mv.displayMSMS(mol, negate=(not display), only=False, log=1, 
                                surfName=name, nbVert=1)
       else : 
            #print "self.computeMSMS('"+sel+"', log=1, display=",(self.get(self.surf)),",perMol=",permol,",surfName='"+name+"')"
            if pRadius == 0.0 : pRadius = 0.01
            self.mv.computeMSMS(mol, log=1, display=display, 
                                perMol=permol,surfName=name)
            print name        
            #obj=mol.geomContainer.geoms[name].obj
            #obj.set_name(name)
            self.mv.colorByAtomType(mol, [name], log=1)
       self.mv.molDispl[mname][3]=display


    def _updateCoarse(self,value):
       #c4d.set_mouse_pointer(c4d.MOUSE_BUSY)
       mname,mol=self.getMolName()   
       sel=self.getSelectionLevel(mol)       
       name='CoarseMS'+str(mol.name)
       selname=self.getSelectionName(sel,mol)
       select=self.mv.select(str(sel),negate=False, only=True, xor=False, log=0, intersect=False)
       parent=mol.geomContainer.masterGeom.obj       
       if sel != mname : 
           name='CoarseMS'+str(selname)
           chain=select.findParentsOfType(Chain)[0]
           parent=mol.geomContainer.masterGeom.chains_obj[chain.name]
       #print 'CoarseMS',name,sel,mname,parent
       display = cmds.iconTextCheckBox(self.cms,q=1,v=1)
       option = cmds.floatSliderGrp(self.cms_slider,q=1,v=1)
       if option == 0.0 : option = 0.001
       if name in mol.geomContainer.geoms.keys():
            g = mol.geomContainer.geoms[name]
            obj = g.obj
            mesh = g.mesh
            #newg = hmaya.coarseMolSurface(self.mv,mol,[32,32,32],isovalue=option,resolution=-0.3,name=name)    
            newg = self.epmv.coarseMolSurface(select,[32,32,32],isovalue=option,
                                         resolution=-0.3,name=name,geom=g)
            mol.geomContainer.geoms[name]=newg
            newg.obj = obj
            newg.mesh=mesh
            hmaya.updateMesh(newg,parent=parent, proxyCol=True,mol=mol)
            self.mv.molDispl[mname][4]=bool(display)
            #c4dutil.getCurrentScene().message(c4d.MULTIMSG_UP)       
            #c4d.draw_views(c4d.DA_ONLY_ACTIVE_VIEW|c4d.DA_NO_THREAD|c4d.DA_NO_ANIMATION)
            #c4d.set_mouse_pointer(c4d.MOUSE_NORMAL)
       #return True

    def _displayCoarse(self,private):
        #c4d.set_mouse_pointer(c4d.MOUSE_BUSY)
        mname,mol=self.getMolName()   
        sel=self.getSelectionLevel(mol)       
        name='CoarseMS'+str(mol.name)
        selname=self.getSelectionName(sel,mol)
        select=self.mv.select(str(sel),negate=False, only=True, xor=False, log=0, intersect=False)
        parent=mol.geomContainer.masterGeom.obj       
        if sel != mname : 
            name='CoarseMS'+str(selname)
            chain=select.findParentsOfType(Chain)[0]
            parent=mol.geomContainer.masterGeom.chains_obj[chain.name]
        #print 'CoarseMS',name,sel,mname,parent
        display = cmds.iconTextCheckBox(self.cms,q=1,v=1)
        option = cmds.floatSliderGrp(self.cms_slider,q=1,v=1)
        if option == 0.0 : option = 0.001
        if name not in mol.geomContainer.geoms.keys():
            #self.mv.coarseMolSurface(bindGeom=True, gridSize=32, surfName='CoarseMolSurface', isovalue='fast approximation', immediate=False, padding=0.0, perMol=True, nodes="1CRN", resolution=-0.3, log=0)
            #print "self.displayExtrudedSS('"+mname+"',log=1,negate=",(not self.get(self.ss)),")" 
            #g=hmaya.coarseMolSurface(self.mv,mol,[32,32,32],isovalue=option,resolution=-0.3,name=name)
            g=self.epmv.coarseMolSurface(select,[32,32,32],isovalue=option,
                                         resolution=-0.3,name=name)
            atoms = mol.findType(Atom)
            mol.geomContainer.geoms[str(name)]=g
            obj=hmaya.createsNmesh(name,g.getVertices(),None,g.getFaces(),smooth=True,proxyCol=True)
            hmaya.addObjToGeom(obj,mol.geomContainer.geoms[str(name)])
            doc=hmaya.getCurrentScene()
            hmaya.addObjectToScene(doc,obj[0],parent=parent)
            #self.mv.colorByAtomType(str(mname), [str(name)], log=1)
            #colors=mol.geomContainer.getGeomColor(name)
        else : 
            obj=[None,None]       
            try :
                obj[0]=mol.geomContainer.geoms[str(name)].obj
            except:
                obj[0]=cmds.ls(str(name))                  
        hmaya.toggleDisplay(obj[0],display)    
        self.mv.molDispl[mname][4]=bool(display)

    def _displayLoft(self,val):
        mname,mol = self.getMolName()
        sel=self.getSelectionLevel(mol)
        select=self.mv.select(str(sel),negate=False, only=True, xor=False, log=0, intersect=False)
        if not isinstance(select,Atom) : select = select.findType(Atom)
        name="ribbon"+mol.name
        display = cmds.iconTextCheckBox(self.loft,q=1,v=1)
        spline = self.epmv._getObject(name,doit=True)
        ruban = self.epmv._getObject(name+"_extruded",doit=True)
        if ruban is None :
            atoms = select.get("CA")
            atoms.sort()
            spline,ruban = self.epmv._makeRibbon(name,atoms.coords,
                                     parent=mol.geomContainer.masterGeom.obj)
        self.epmv._toggleDisplay(ruban,display=display)
        self.epmv._toggleDisplay(spline,display=display)
        self.updateViewer()
        
    def _displayMeta(self,val):
        print "displayMetaB"
        #change particle render Type to Blobby surface
        #setAttr metaballs1TIMtrShape.particleRenderType 7;
        #setAttr "metaballs1TIMtrShape.radius" 1.437909;
        #setAttr "metaballs1TIMtrShape.threshold" 0.784314;
        #then assign radius and threshold
        #create metaballs from clouds /perchains or permolecule ?
        #_perMol option 
        _perMol = True 
        mname,mol=self.getMolName()
        sel=self.getSelectionLevel(mol)
        selection = self.mv.select(str(sel),negate=False, only=True, xor=False, 
                                   log=0, intersect=False)
        if not isinstance(selection,Atom) : select = selection.findType(Atom)
        doc=self.epmv._getCurrentScene()
        display = cmds.iconTextCheckBox(self.meta,q=1,v=1)
        if _perMol :
            name = 'metaballs'+mol.name
            parent  = mol.geomContainer.masterGeom.obj
            #find the metaball
            metab = self.epmv._getObject(name,doit=True)
            if metab is None :
                #create the metabll object
                self.epmv.helper.metaballs(name,selection,scn=doc)
            #visibility
            self.epmv.helper.toggleDisplay(metab,display)   
        else : #perChains
            parents  = mol.geomContainer.masterGeom.chains_obj #one foreach chain
            for i,ch in enumerate(mol.chains):
                pass
        self.updateViewer()

    def _displaySpline(self,val):
        mname,mol = self.getMolName()
        #Sel = parseSelection(stringSelection.val,mol)
        name="spline"+mol.name
        display = cmds.iconTextCheckBox(self.spline,q=1,v=1)
        spline = self.epmv._getObject(name,doit=True)
        if spline is None :
            atoms = mol.allAtoms.get("CA")
            atoms.sort()
            spline = self.epmv.helper.spline(name,atoms.coords)
        self.epmv._toggleDisplay(spline,display=display)
        self.updateViewer()
         
    def _displayArmature(self,val):
        #should we use the selection ?
        #an IK handler can be then add:ikHandle
        #and a skin can be bound:SmoothBindSkin
        #c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        mname,mol=self.getMolName()   
        #sel=self.getSelectionLevel(mol)    
        doit = cmds.iconTextCheckBox(self.armature,q=1,v=1)
        #doit=self.GetBool(self.armature)
        doc=self.epmv._getCurrentScene()
        name=mol.name+'_armature'
        sp=self.epmv._getObject(name,doit=True)
        print sp
        if sp != None : 
            self.epmv.helper.toggleDisplay(sp,doit)
            self.updateViewer()
            return True
        atoms=mol.allAtoms.get("CA")
        if len(atoms) == 0 :
            atoms=mol.allAtoms.get("backbone")
        armature=self.epmv.helper.armature(name,atoms,scn=doc,
                                           root=mol.geomContainer.masterGeom.obj)
        self.updateViewer()

    def _color(self,val=None):
        #print val
        #Note unic color should work on every geometry even the grid data...
        mname,mol=self.getMolName()
        sel = self.getSelectionLevel(mol)
        radio = cmds.radioCollection( self.color_collection, q=1, select=1 )
        #print radio
        index = self.col.index(radio)
        #print index
        #need to get the active geom
        lGeoms = self.getGeomActive()
        #then apply the color function
        if index == 6 : 
            #get the color from the color choose
            color= [0.,0.,0.]
            color = cmds.colorSliderButtonGrp(self.unic_col,q=1,rgb=1)
            print color
            self.funcColor[index](mol,[color], lGeoms)
        elif index == 2 :
            self.mv.colorByProperty.level='Atom'
            selection = self.mv.select(str(sel),negate=False, only=True, xor=False, log=0, intersect=False)
            if not isinstance(selection,Atom) : selection = selection.findType(Atom)
            ma = len(selection)
            self.funcColor[2](selection, lGeoms, 'number',mini=1.0,maxi=float(ma),
                               propertyLevel='Atom', colormap='rgb256',log=1)
        elif index == 8 :
            self.mv.colorByProperty.level='Atom'
            selection = self.mv.select(str(sel),negate=False, only=True, xor=False, log=0, intersect=False)
            if not isinstance(selection,Atom) : selection = selection.findType(Atom)
            ma = max(selection.temperatureFactor)
            mi = min(selection.temperatureFactor)
            self.funcColor[2](selection, lGeoms, 'temperatureFactor',mini=float(mi),maxi=float(ma),
                               propertyLevel='Atom', colormap='rgb256',log=1)            
        elif index == 9 :
            self.mv.colorByProperty.level='Atom'
            selection = self.mv.select(str(sel),negate=False, only=True, xor=False, log=0, intersect=False)
            if not isinstance(selection,Atom) : selection = selection.findType(Atom)
            ma = max(selection.sas_area)
            mi = min(selection.sas_area)
            self.funcColor[2](selection, lGeoms, 'sas_area',mini=float(mi),maxi=float(ma),
                               propertyLevel='Atom', colormap='rgb256',log=1)            
        else : self.funcColor[index](mol, lGeoms)
        cmds.colorSliderButtonGrp(self.unic_col,e=True,cal=[1,'left'])

    def restoreMolMenu(self):
        #call this after flushing the pop up menu
        for mname in self.mv.MolSelection.keys():
            cmds.menuItem(p=self.pmol,l=mname,c=partial(self.setCurMol,str(mname)))
            for selname in self.mv.MolSelection[mname].keys():
                cmds.menuItem(p=self.pmol,l=selname,c=partial(self.setCurMol,str(selname)))
                
    def setCurMol(self,var,args):
        mname = var
        cmds.text(self.mol,e=1,l=str(mname))
        #apply save selection from molDisplay dictionary
    
    def getSelectionName(self,sel,mol):
        for selname in self.mv.MolSelection[mol.name].keys() : 
            if sel == self.mv.MolSelection[mol.name][selname] : return selname         
        return mol.name+"_Selection"+str(len(self.mv.MolSelection[mol.name]))

    def getSelectionLevel(self,mol):
        if mol == None : sel = ''
        else : sel=mol.name
        selection=str(cmds.textField(self.selection,q=1,tx=1))
#        print "selection ",selection
#        print "sel ",sel
        if selection.upper() == 'BACKBONE':              
            sel=mol.name+":::N,CA,C"
        elif selection.upper() == 'SIDECHAIN':              
            sel=mol.name+":::sidechain"
        elif selection.upper() in AtomElements.keys(): sel=mol.name+':::'+selection
        elif selection.upper() in RasmolAmino.keys(): sel=mol.name+'::'+self.ResidueSelector.r_keyD[selection]+':'
        elif selection.lower() in ResidueSetSelector.residueList.keys() : sel=mol.name+'::'+selection+':'
        elif selection.split(':')[0] == mol.name : sel = selection
        elif selection.split(' ')[0].lower() == "chain" : sel = mol.name+':'+selection.split(' ')[1]+'::'
        elif selection == 'picked' :
            pass
            #need to get the current object selected in the doc
            #and parse their name to recognize the atom selection...do we define a picking level ? and some phantom object to be picked?                  
            #CurrSel=self.epmv.helper.getCurrentScene().GetSelection()
            #astr=[]
            #for o in CurrSel : 
                #print o.get_name()#,o.get_type()
            #    astr.append(self.epmv.helper.parseObjectName(o))
            #sel=self.sortName(astr)
            #print "parsed selection ",sel
            #sel=mol.name
#        print sel
        return str(sel)        

    def setKeywordSel(self,val,arg):
        print val,arg
        cmds.textField(self.selection,e=1,tx=str(val).strip())

    def delete_selection(self,var):
        selname,mol=self.getMolName(forupdate=True)
        mname = mol.name
        res = cmds.confirmDialog(title='delete set',
                                            message="Are You sure you want to delete the current selection "+selname+" ?",
                                            button=['Yes','No'],
                                            defaultButton='Yes',
                                            cancelButton='No', dismissString='No')
        if res == 'Yes': 
            del self.mv.MolSelection[mname][selname]
            del self.mv.selections[mname][selname]
            del self.mv.molDispl[selname]
            cmds.menu(self.pmol,e=1,dai=1)
            self.restoreMolMenu()
            
    def rename_selection(self,var):
        #whats the new name
        newname = None
        result = cmds.promptDialog(title='Change selection set name',
                message='"Enter the new name for the current selection\n"',
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')
        if result == "OK" : 
            newname = cmds.promptDialog(query=True, text=True)
        if newname is None : return
        #get current selection name
        selname,mol=self.getMolName(forupdate=True)
        mname = mol.name
        #change the name in the mol dictionary of selection
        sel = self.mv.MolSelection[mname][selname]
        dsDic = self.mv.molDispl[selname]
        del self.mv.MolSelection[mname][selname]
        del self.mv.selections[mname][selname]
        del self.mv.molDispl[selname]        
        
        self.mv.MolSelection[mname][newname]=sel
        self.mv.selections[mname][newname]=sel
        self.mv.molDispl[newname]=dsDic
        
        cmds.menu(self.pmol,e=1,dai=1)
        self.restoreMolMenu()

    def add_selection(self,val,n=None):
        print "add_selection"
        if n is not None:
            for selname in self.mv.selections[n].keys():
                #add a new menuItem to the main menu
                cmds.menuItem(p=self.pmol,label=selname,c=partial(self.setCurMol,str(selname)))
                #self.AddChild(self._box,self.indice_mol,selname)
                #self.mv.iSel[str(self.indice_mol)]=selname
                #self.indice_mol+=1               
            return True
        mname,mol=self.getMolName()   
        sel=self.getSelectionLevel(mol)       
        print mname
        print sel
        selname=mname+"_Selection"+str(len(self.mv.selections[mname]))
        print selname
        self.mv.MolSelection[mname][selname]=sel
        self.mv.selections[mname][selname]=sel
        self.mv.molDispl[selname]=[cmds.iconTextCheckBox(self.cpk,q=1,v=1),
                                   cmds.iconTextCheckBox(self.bs,q=1,v=1),
                                   cmds.iconTextCheckBox(self.ss,q=1,v=1),
                                   cmds.iconTextCheckBox(self.surf,q=1,v=1),
                                   cmds.iconTextCheckBox(self.cms,q=1,v=1),
                                   cmds.radioCollection( self.color_collection, q=1, select=1 ),
                                   cmds.colorSliderButtonGrp(self.unic_col,q=1,rgb=1)]
        #add a menu
        cmds.menuItem(p=self.pmol,label=selname,c=partial(self.setCurMol,str(selname)))
        cmds.text(self.mol,e=1,l=str(selname))
        #self.AddChild(self._box,self.indice_mol,selname)
        #print str(self.indice_mol+self.indice)       
        #self.mv.iSel[str(self.indice_mol)]=selname
        #self.indice_mol+=1
        #return True       

    def _deleteMol(self,val):
        mname,mol=self.getMolName()
        #first delete all geom associated
        for g in mol.geomContainer.geoms:
            if hasattr(g,'obj'):
                print "delete"
                del g.obj 
            if hasattr(g,'mesh'):
                print "delete"
                del g.mesh
        #then delete the molecule this ensure the dejavugeom to be deleted too
        self.mv.deleteMol(mname)

    def save_ePMVScript(self,val,arg):
        commands=cmds.cmdScrollFieldExecuter(self.pmvcmds,q=1,t=1)
        from Pmv.hostappInterface import demo
        dir = demo.__path__[0]
        if val == 'Save':
            filename = self.current_script+'.py'
        else :
            filename = cmds.fileDialog()
        f = open(filename,'w')
        f.write(commands)
        f.close()
        
    def set_ePMVScript(self,val,arg):
        from Pmv.hostappInterface import demo
        dir = demo.__path__[0]        
        if val == 'Load' : #Open..ask for broser
            filename = cmds.fileDialog()
        else :
            filename = dir+'/'+val+'.py'
        f = open(filename,'r')
        script = f.read()
        f.close()
        cmds.cmdScrollFieldExecuter(self.pmvcmds,e=1,t=script)
        self.current_script = filename
        
    def execPmvComds(self,val):
        pmvcmds=cmds.cmdScrollFieldExecuter(self.pmvcmds,q=1,t=1)
        print len(pmvcmds),pmvcmds
        exec(pmvcmds,{'self':self.mv,'epmv':self.epmv})   

    def SetPreferences(self,val):
        #print val
        #for options in self.OPTIONS.keys():
        #    self.OPTIONS[options]["id"]["val"] = cmds.menuItem(self.OPTIONS[options]["id"],q=1,checkBox=1)
        self.epmv.doCamera = cmds.menuItem(self.OPTIONS['cam']["id"],q=1,checkBox=1)
        self.epmv.doLight = cmds.menuItem(self.OPTIONS['light']["id"],q=1,checkBox=1)
        self.epmv.doCloud = cmds.menuItem(self.OPTIONS['clouds']["id"],q=1,checkBox=1)
        self.epmv.bicyl = cmds.menuItem(self.OPTIONS['cyl']["id"],q=1,checkBox=1)
        self.epmv.center_mol = cmds.menuItem(self.OPTIONS['center']["id"],q=1,checkBox=1)
        self.epmv.center_grid = cmds.menuItem(self.OPTIONS['centerG']["id"],q=1,checkBox=1)
        self._logConsole = cmds.menuItem(self.OPTIONS['log']["id"],q=1,checkBox=1)
        self._forceFetch = cmds.menuItem(self.OPTIONS['fetch']["id"],q=1,checkBox=1)
        self._synchro = cmds.menuItem(self.OPTIONS['synchro']["id"],q=1,checkBox=1)
#        self._depthQ = cmds.menuItem(self.OPTIONS['depthQ']["id"],q=1,checkBox=1)
        if self._modeller :
            from Pmv.hostappInterface.extension.Modeller.pmvAction import setupENV
            self._useModeller = cmds.menuItem(self.OPTIONS['modeller']["id"],q=1,checkBox=1)
            self.epmv.useModeller = self._useModeller
            if self._useModeller :
                self.epmv.center_mol = False
                self.epmv.center_grid = False
                cmds.menuItem(self.OPTIONS['center']["id"],e=1,checkBox=0)
                cmds.menuItem(self.OPTIONS['centerG']["id"],e=1,checkBox=0)
                if self.epmv.env is None:
                    self.env = self.epmv.env = setupENV()
                if self._mod is None :
                    self._mod = ParameterModeller(epmv = self.epmv)
#        #self.AskClose()
#        if self.epmv.gui._depthQ :
#            self.epmv.helper.create_environment('depthQ',distance = 30.)
#        else :
#            obj=self.epmv.helper.getObject('depthQ')
#            self.epmv.helper.toggleDisplay(obj,False)
        if self._synchro :
            if self.epmv_synchro is None :
                self.epmv_synchro = ePMVsynchro(self.epmv,period=0.1)
            self.epmv_synchro.set_callback()
        else :
            if self.epmv_synchro is not None :
                self.epmv_synchro.remove_callback()

    def citationInformation(self,val):
        txt=self.epmv.getCitations()
        cmds.confirmDialog(title='PMV citations', message=txt, button=['OK'], 
                           defaultButton='OK')
        
    def drawAbout(self,val):
        #just Draw a litlle windows of some about ePMV, like how,who, etc...
        #and PMV citation
        about="""ePMV designed by Ludovic Autin and Graham Jonhson.
Based on PMV created by Michel Sanner.
Develloped in the Molecular Graphics Laboratory directed by Arthur Olson.
        """
        cmds.confirmDialog( title='About ePMV', message=about, button=['OK'], 
                           defaultButton='OK')

    def addExtension(self,val):
        result = cmds.promptDialog(title='Add Extension',
                message='"Enter the extension name follow by the directory\nSupported extension are: Modeller, Pyrosetta\n"',
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')
        if result == 'OK':
            text = cmds.promptDialog(query=True, text=True)
            self.inst.addExtension(text)
            #how to redo the gui?

    def launchBrowser(self,val):
        #launch the default interenet browser and open the ePMV wiki page
        import webbrowser
        webbrowser.open(__url__[0])

    def check_update(self,val):
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
                res = cmds.confirmDialog(title='ePMV Update',
                                            message=message,
                                            button=['Yes','No'],
                                            defaultButton='Yes',
                                            cancelButton='No', dismissString='No')
                if res == 'Yes': 
                    self.epmv_update(None,note=note)
        else :
            c4d.gui.MessageDialog("problem with Internet!")

    def epmv_update(self,val,note=None):
        #try to update ePMV
        if self.inst is None :
            self.inst=Installer(gui=False)
            self.inst.mgltoolsDir=MGL_ROOT
            self.inst.currDir=MGL_ROOT+os.sep+"MGLToolsPckgs"+os.sep+"Pmv"+os.sep+"hostappInterface"+os.sep
        #first check if the file exist
#        import os.path
#        if not os.path.exists(self.inst.currDir+'/epmv_dir.txt'):
#            c4d_dir = c4d.storage.GeGetStartupPath().replace(" ","\ ")
#            f=open(self.inst.currDir+'/epmv_dir.txt','w')
#            f.write("Cinema4DR12:"+c4d_dir)
#            f.close()
        self.inst.getDirFromFile()
        self.inst.updateCVS()
        try:
            self.inst.installMaya(update=True)
            #need a popup to says to restart
            msgs="SUCCESS!\nYou need to restart now!\n"
            if note != None:
                msgs += note
            result = cmds.confirmDialog(title='Update',
                message=msgs,
                button=['OK'],
                defaultButton='OK')
            return True
        except:
            result = cmds.confirmDialog(title='Update',
                message="OUPS no update done!",
                button=['OK'],
                defaultButton='OK')

    def modellerGUI(self,arg):
        #if self._mod is None :
            self._mod=ParameterModeller(epmv=self.epmv)
        #if self._mod.epmv is None :
            self._mod.epmv = self.epmv
        #if self._mod.gui is None :
            self._mod.CreateLayout()
            cmds.showWindow(self._mod.gui)
        #else :
        #    cmds.window(self._mod.gui,e=1,vis=True)
        
    def do_modeller(self,arg,val):
        print arg,val
        res=arg
        #res=cmds.layoutDialog(t="Modeller",ui=self.modellerGUI)
        if res != 'Cancel':
            from Pmv.hostappInterface.extension.Modeller.pmvAction import minimizeMDL 
            from Pmv.hostappInterface.extension.Modeller.pmvAction import dynamicMDL 
            mname,mol=self.getMolName()
            #sel=self.getSelectionLevel(mol)
            store = cmds.checkBox(self._mod.CHECKBOXS["store"]["id"],q=1,v=1)
            if res == "Minimize":
                maxit = cmds.intField(self._mod.NUMBERS["miniIterMax"]["id"],q=1,v=1)
                minimizeMDL(mol,maxit=maxit,store=store)                       
            elif res == "MD":
                maxit = cmds.intField(self._mod.NUMBERS['mdIterMax']['id'],q=1,v=1)
                temp = cmds.intField(self._mod.NUMBERS['mdTemp']['id'],q=1,v=1)
                dynamicMDL(mol,temp=temp,maxit=maxit,store=store)
        else :
            cmds.window(self._mod.gui,e=1,vis=False)

    def do_AutoDock(self,arg):
#        if self._pd is None :
            self._pd=ParameterScoring(epmv=self.epmv)
#        if self._pd.epmv is None :
            self._pd.epmv = self.epmv
#        if self._pd.gui is None :
            self._pd.CreateLayout()
            cmds.showWindow(self._pd.gui)
#        else :
#            cmds.window(self._pd.gui,e=1,vis=True)

    def updateViewer(self):
        self.epmv.helper.update()
        
# command
class scriptedCommand(OpenMayaMPx.MPxCommand):
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)
    def doIt(self,argList):
        epmvui = epmvUI()
        epmvui.create()
        maya.epmvui = epmvui

# Creator
def cmdCreator():
    return OpenMayaMPx.asMPxPtr( scriptedCommand() )

def createShelf():
    shelfTopLevel = maya.mel.eval("global string $gShelfTopLevel;$temp = $gShelfTopLevel")
    shelf = "%s|Custom|Start_ePMV" % shelfTopLevel
    res=cmds.shelfButton(shelf,ex=1)
    print res,shelf
    if not res and not hasattr(maya,'epmvshelf'):
        #assume ePMV already loaded
        com = 'import maya\nmaya.cmds.ePMV()\nepmv = maya.epmvui.epmv\nself = epmv.mv\n'
        im = "/Library/MGLTools/1.5.6.csv/MGLToolsPckgs/Pmv/hostappInterface/images/pmv.tif" 
        par="General"
        shelf=cmds.shelfButton('Start_ePMV',p='General',l='ePMV', annotation='start ePMV', image1=im, command=com )
    #to delete maya.cmds.deleteUI(shelf)
    
# Initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerCommand( kPluginCmdName, cmdCreator )
#        createShelf()
    except:
        sys.stderr.write( "Failed to register command: %s\n" % kPluginCmdName )
        raise

# Uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand( kPluginCmdName )
    except:
        sys.stderr.write( "Failed to unregister command: %s\n" % kPluginCmdName )
        raise

#add in the shelf:
# import maya
# maya.cmds.ePMV()
# epmv = maya.epmvui.epmv

# epmvui = epmvUI()
# epmvui.create()
