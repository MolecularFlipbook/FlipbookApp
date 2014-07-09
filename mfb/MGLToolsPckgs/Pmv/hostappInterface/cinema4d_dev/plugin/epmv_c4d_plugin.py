"""
Name: 'Python Molecular Viewer GUI'
Cinema4D: 12
Py4D:1.11
"""

#this should be part of the adaptor?
__author__ = "Ludovic Autin, Graham Johnson"
__url__ = ["http://mgldev.scripps.edu/projects/ePMV/wiki/index.php/Main_Page",
           'http://mgldev.scripps.edu/projects/ePMV/update_notes.txt']
__version__="0.0.2a"
__doc__ = "ePMV v"+__version__
__doc__+"""\
Use cinema4d as a molecular viewer

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
#=======
import os,sys
import c4d
MGL_ROOT=""


prefpath=c4d.storage.GeGetC4DPath(1)
os.chdir(prefpath)
os.chdir(".."+os.sep)
softdir = os.path.abspath(os.curdir)
mgldirfile=softdir+os.sep+"plugins"+os.sep+"epmv"+os.sep+"mgltoolsdir"
if os.path.isfile(mgldirfile) :
    f=open(mgldirfile,'r')
    MGL_ROOT=f.readline()
    f.close()
else :
    if len(MGL_ROOT) == 0 :
        MGL_ROOT = c4d.storage.LoadDialog(title="what is the path to MGLToolsPckgs?",flags=2)
    f=open(mgldirfile,'w')
    f.write(MGL_ROOT)
    f.close()
print MGL_ROOT
#is MGLTools Pacthed ie windows
if sys.platform == 'win32':
    #need to patch MGLTools first
    #first patch MGLTools
    #check if we need to patch
    mgltoolsDir = MGL_ROOT+os.sep+"MGLToolsPckgs"
    patch=os.path.isfile(mgltoolsDir+os.sep+"patched")
    if not patch :
        import urllib
        import tarfile 
        c4d.gui.MessageDialog("Patching MGLToolsPckgs with python2.6 system dependant modules\nclick ok to Continue\nand be patient")
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
        c4d.gui.MessageDialog("MGLTools pacthed, click OK to continue")

#add to syspath
sys.path.append(MGL_ROOT+'/MGLToolsPckgs')
from Pmv.hostappInterface.install_plugin import Installer

epmvinstall = Installer(gui=False)

#is C4dpatched
if sys.platform == "darwin" :
	patchpath = c4d.storage.GeGetC4DPath(4)+os.sep+"python"+os.sep+"packages"+os.sep+"osx"+os.sep
elif sys.platform == "win32":
	patchpath = c4d.storage.GeGetC4DPath(2)+os.sep+"modules"+os.sep+"python"+os.sep+"res"+os.sep
epmvinstall.softdir[2] = softdir
print epmvinstall.softdir[2]
patched=os.path.isfile(patchpath+"patched")
if not patched :
    c4d.gui.MessageDialog("Cinema4D python library is going to be pacthed\nclick ok to Continue\nand be patient\n")
    epmvinstall.patchC4DR12(patchpath)
    c4d.gui.MessageDialog("Cinema4D python library have just beed patched you need to restart!\n")
    #c4d.CallCommand(12104)#quit

#check if we need to patch MGLTools / C4D
#TODO:
#make the pyrosetta extension
#loft did not work
#copy  libjpeg.62.dylib in /usr/lib ?
import c4d
from c4d import plugins
from c4d import utils
from c4d import bitmaps
from c4d import gui
#from c4d import symbols as sy

#setup the python Path
import sys
import os
from time import time
#if changePath :
#    sys.path.insert(1,sys.path[0]+"/lib-tk")
#    sys.path.insert(0,MGL_ROOT+'/lib/python2.5/site-packages')
#    sys.path.insert(0,MGL_ROOT+'/lib/python2.5/site-packages/PIL')

sys.path.append(MGL_ROOT+'/MGLToolsPckgs')
if sys.platform == "win32":
    sys.path.append(MGL_ROOT+'/MGLToolsPckgs/PIL')
else :
    sys.path.insert(1,sys.path[0]+"/lib-tk")
    sys.path.insert(0,MGL_ROOT+'/lib/python2.5/site-packages')
    sys.path.insert(0,MGL_ROOT+'/lib/python2.5/site-packages/PIL')

#sys.path.append('/Library/MGLTools/REL/python2.6/lib/python2.6/site-packages')
#sys.path.append('/Library/Python/2.6/site-packages/')
#sys.path.append('/Library/Python/2.6/site-packages/numpy-1.3.0-py2.6-macosx-10.6-universal.egg/')
#sys.path.append('/Library/Python/2.6/site-packages/PIL/')

#sys.path.insert(0,"/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/")
#sys.path.insert(0,"/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/lib-tk/")

#only need to do it once the sys path update....
    #pmv 1.6.0 seems to works perfect, no need to patch
    #even better if 64bits i guess

#be sure to use a unique ID obtained from www.plugincafe.com
PLUGIN_ID = 10234096

from MolKit.protein import ResidueSetSelector,Chain
from MolKit.molecule import Atom
from Pmv.pmvPalettes import AtomElements
from Pmv.pmvPalettes import RasmolAmino
from Pmv.hostappInterface.install_plugin import Installer
from Pmv.hostappInterface import comput_util as C
from Pmv.hostappInterface import epmvGui
#import Pmv.hostappInterface.cinema4d.helperC4D as self.epmv.helper

VERBOSE = 0

class ParameterARViewer(gui.SubDialog):
    #.epmv
    #Pattern managment ?
    
    def initWidgetId(self):
        #AR options
        #Video option
        #Patterns options
        #energie option
        id=1005
        self.NUMBERS = {"nrjrate":{"id":id,"name":"Energy compute rate",'width':150,"height":10,"action":self.setEnergieRate},
                        }
        id = id + 1
        self.BTN = {"initVideo":{"id":id,"name":"initVideo",'width':150,"height":10,"action":self.epmv.mv.art.init_video},
                    "startVideo":{"id":id+1,"name":"startVideo",'width':150,"height":10,"action":self.epmv.mv.art.start_video},
                    "stopVideo":{"id":id+2,"name":"stopVideo",'width':150,"height":10,"action":self.epmv.mv.art.stop_video},
                    "startAR":{"id":id+3,"name":"start ARtracking thread",'width':200,"height":10,"action":self.startTracking},
                    "setupGeom":{"id":id+4,"name":"bind geometries",'width':150,"height":10,"action":self.setUpgeoms},
                    "setupPatt":{"id":id+5,"name":"add patterns",'width':150,"height":10,"action":self.setUpPatterns},
                    }
        id = id + 6
        self.CHECKBOXS ={"avg1":{"id":id,"name":"average mode 1",'width':150,"height":10,"action":self.toggleAvg1},
                         "avg2":{"id":id+1,"name":"average mode 2",'width':150,"height":10,"action":self.toggleAvg2},
                         "conc":{"id":id+2,"name":"concatenate transformation",'width':150,"height":10,"action":self.toggleConcat},
                         "showV":{"id":id+3,"name":"show video",'width':150,"height":10,"action":self.showVideo},
                         "showDV":{"id":id+4,"name":"show debug video",'width':150,"height":10,"action":self.showVideo},
                         "flipV":{"id":id+5,"name":"flip video",'width':150,"height":10,"action":self.flipVideo}
                         }
        id = id + 6
        self.SLIDERS  = {"thr":{"id":id,"name":"Threshold",'width':150,"height":10,"action":self.setThreshold},
                        "his":{"id":id+1,"name":"History",'width':150,"height":10,"action":None},
                        "scale":{"id":id+2,"name":"Scale Device",'width':150,"height":10,"action":self.setScale},
                        "scaleO":{"id":id+3,"name":"Scale Object",'width':150,"height":10,"action":self.setScaleObject}
                        }
        id = id + 3
        return True


    def CreateLayout(self):
        ID=0
        self.SetTitle("Options")
        self.initWidgetId()
        #minimize otin/button
        self.GroupBegin(id=ID,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                           cols=1, rows=4)
        self.GroupBorderSpace(1, 1, 1, 1)
        ID = ID +1
        #store?
        self.AddStaticText(ID,flags=c4d.BFH_LEFT)
        self.SetString(ID,"AR options")                                    
        ID = ID +1
        self.AddCheckbox(id=self.CHECKBOXS["avg1"]["id"],flags=c4d.BFH_CENTER|c4d.BFH_SCALEFIT,
                                name=self.CHECKBOXS["avg1"]["name"],
                                initw=self.CHECKBOXS["avg1"]["width"],
                                inith=self.CHECKBOXS["avg1"]["height"])
        self.AddCheckbox(id=self.CHECKBOXS["avg2"]["id"],flags=c4d.BFH_CENTER|c4d.BFH_SCALEFIT,
                                name=self.CHECKBOXS["avg2"]["name"],
                                initw=self.CHECKBOXS["avg2"]["width"],
                                inith=self.CHECKBOXS["avg2"]["height"])
        self.AddCheckbox(id=self.CHECKBOXS["conc"]["id"],flags=c4d.BFH_CENTER|c4d.BFH_SCALEFIT,
                                name=self.CHECKBOXS["conc"]["name"],
                                initw=self.CHECKBOXS["conc"]["width"],
                                inith=self.CHECKBOXS["conc"]["height"])

        his=self.AddEditSlider(id=self.SLIDERS["his"]["id"],
                                            flags=c4d.BFH_LEFT|c4d.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["his"]["width"])
        self.SetLong(his,5,0,  20, 1)
        thr=self.AddEditSlider(id=self.SLIDERS["thr"]["id"],
                                            flags=c4d.BFH_LEFT|c4d.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["thr"]["width"])                                            
        self.SetLong(thr,100,0,  200, 1)
        sc=self.AddEditSlider(id=self.SLIDERS["scale"]["id"],
                                            flags=c4d.BFH_LEFT|c4d.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["scale"]["width"])
        self.SetReal(sc,1.,0.,  20., 0.1)
        sc=self.AddEditSlider(id=self.NUMBERS["nrjrate"]["id"],
                                            flags=c4d.BFH_LEFT|c4d.BFH_SCALEFIT, 
                                            initw=self.NUMBERS["nrjrate"]["width"])
        self.SetLong(sc,1,0,  50, 1)
        sco=self.AddEditSlider(id=self.SLIDERS["scaleO"]["id"],
                                            flags=c4d.BFH_LEFT|c4d.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["scaleO"]["width"])
        self.SetReal(sco,1.,0.,  20., 0.1)

        self.AddStaticText(ID,flags=c4d.BFH_LEFT)
        self.SetString(ID,"Video options")                                    
        ID = ID +1
        
        self.AddCheckbox(id=self.CHECKBOXS["showV"]["id"],flags=c4d.BFH_CENTER|c4d.BFH_SCALEFIT,
                                name=self.CHECKBOXS["showV"]["name"],
                                initw=self.CHECKBOXS["showV"]["width"],
                                inith=self.CHECKBOXS["showV"]["height"])
        self.SetBool(self.CHECKBOXS["showV"]["id"],True)
        self.AddCheckbox(id=self.CHECKBOXS["showDV"]["id"],flags=c4d.BFH_CENTER|c4d.BFH_SCALEFIT,
                                name=self.CHECKBOXS["showDV"]["name"],
                                initw=self.CHECKBOXS["showDV"]["width"],
                                inith=self.CHECKBOXS["showDV"]["height"])
        self.AddCheckbox(id=self.CHECKBOXS["flipV"]["id"],flags=c4d.BFH_CENTER|c4d.BFH_SCALEFIT,
                                name=self.CHECKBOXS["flipV"]["name"],
                                initw=self.CHECKBOXS["flipV"]["width"],
                                inith=self.CHECKBOXS["flipV"]["height"])
        self.GroupEnd()
        self.GroupBegin(id=ID,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                           cols=3, rows=4)
        self.GroupBorderSpace(1, 1, 1, 1)
        ID = ID +1

        self.AddButton(id=self.BTN["initVideo"]["id"], flags=c4d.BFH_CENTER | c4d.BFV_MASK,
                            initw=self.BTN["initVideo"]["width"],
                            inith=self.BTN["initVideo"]["height"],
                            name=self.BTN["initVideo"]["name"])
        self.AddButton(id=self.BTN["startVideo"]["id"], flags=c4d.BFH_CENTER | c4d.BFV_MASK,
                            initw=self.BTN["startVideo"]["width"],
                            inith=self.BTN["startVideo"]["height"],
                            name=self.BTN["startVideo"]["name"])
        self.AddButton(id=self.BTN["stopVideo"]["id"], flags=c4d.BFH_CENTER | c4d.BFV_MASK,
                            initw=self.BTN["stopVideo"]["width"],
                            inith=self.BTN["stopVideo"]["height"],
                            name=self.BTN["stopVideo"]["name"])
        self.GroupEnd()
        self.AddSeparatorH(200,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK)
        self.GroupBegin(id=ID,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                           cols=1, rows=4)
        self.GroupBorderSpace(1, 1, 1, 1)
        ID = ID +1
        self.AddButton(id=self.BTN["startAR"]["id"], flags=c4d.BFH_LEFT | c4d.BFV_MASK|c4d.BFH_SCALEFIT,
                            initw=self.BTN["startAR"]["width"],
                            inith=self.BTN["startAR"]["height"],
                            name=self.BTN["startAR"]["name"])         
        self.GroupEnd()
        return True

    def setScaleObject(self):
        self.epmv.mv.art.scaleObject = self.GetReal(self.SLIDERS["scaleO"]["id"])

    def setScale(self):
        self.epmv.mv.art.scaleDevice = self.GetReal(self.SLIDERS["scale"]["id"])
        
    def toggleAvg1(self):
        self.epmv.mv.art.set_average_mode(self.GetBool(self.CHECKBOXS["avg1"]["id"]))
        
    def toggleAvg2(self):
        self.epmv.mv.art.patternMgr.means=bool(self.GetBool(self.CHECKBOXS["avg2"]["id"]))

    def toggleConcat(self):
        self.epmv.mv.art.concat=bool(self.GetBool(self.CHECKBOXS["conc"]["id"]))
        
    def setThreshold(self):
        thr = self.GetLong(self.SLIDERS["thr"]["id"])
        self.epmv.mv.art.set_threshold_cmd(thr)

    def setEnergieRate(self):
        self.epmv.mv.art.nrg_calcul_rate = self.GetLong(self.NUMBERS['nrjrate']['id'])
        
    def showVideo(self):
        vid = self.GetBool(self.CHECKBOXS["showV"]["id"])
        dvid = self.GetBool(self.CHECKBOXS["showDV"]["id"])
        self.epmv.mv.art.AR.show_tex = bool(vid)
        #self.epmv.mv.art.AR.debug = bool(dvid)
        self.epmv.mv.art.set_debug_mode(bool(dvid))
        
    def flipVideo(self):
        self.epmv.mv.art.patternMgr.mirror = self.GetBool(self.CHECKBOXS["flipV"]["id"])
    
    def startTracking(self):
        import thread
        self.thread=thread.start_new_thread(self.epmv.helper.AR,(self.epmv.mv,))
        print "thread ",self.thread

    def setUpPatterns(self):
        patt5='patt17'#left
        patt6='patt35'#front
        patt7='patt36'#right
        patt8='patt39'#back   
        #why loadDevice didnt set the transfo_position correctly
        self.epmv.mv.art.patternMgr.loadDevice(name='head',type='cube4',width=40.,
        								trans=[0.,0.,-30.])
        self.epmv.mv.art.patternMgr.loadDevice(name='bott',type='cube4',
        							listPatt=[patt6,patt7,patt8,patt5],width=40.,
        							trans=[0.,0.,-30.])
        #offset ?
        self.epmv.mv.art.patternMgr.groups['head'].offset = [60.,0.,0.]
        self.epmv.mv.art.patternMgr.groups['bott'].offset = [60.,0.,0.]

    def setUpgeoms(self):
        geom = self.epmv.mv.Mols[0].geomContainer.masterGeom
        self.epmv.mv.setGeoms('head',[geom],log=0)#1oel
        geom1 = self.epmv.mv.Mols[1].geomContainer.masterGeom
        self.epmv.mv.setGeoms('bott',[geom1],log=0)#1oel
    

#######EVENT COMMAND######################################################
    def Command(self, id, msg):
        c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        for butn in self.BTN.keys():
            if id == self.BTN[butn]["id"]:
                self.BTN[butn]["action"]()
        for butn in self.CHECKBOXS.keys():
            if id == self.CHECKBOXS[butn]["id"]:
                action = self.CHECKBOXS[butn]["action"]
                if action is not None :
                    action()
        for butn in self.SLIDERS.keys():
            if id == self.SLIDERS[butn]["id"]:
                action = self.SLIDERS[butn]["action"]
                if action is not None :
                    action()
        c4d.gui.SetMousePointer(c4d.MOUSE_NORMAL)
        self.epmv.gui.updateViewer()
        return True
#        
### NRG calculation setup
#at1 = "hsg1:A::;"
#at2 = "ind:::;"
#atomset1 = self.expandNodes(at1)
#atomset2 = self.expandNodes(at2)
#helperC4D.cAD3Energies(self,self.Mols,atomset1,atomset2,add_Conf=True,debug=True)
class ParameterScoring(gui.SubDialog):
    _scorer = 'ad3Score'
    _display = False
    label = None
    
    def initWidgetId(self):
        #atomset1 Rc
        #atomset2 Lig
        #mols
        #add conf
        #score type default score_type='c_ad3Score'
        id=1005
        self.BTN = {"rec":{"id":id,"name":"Browse",'width':50,"height":10,
                           "action":self.setRec},
                    "lig":{"id":id+1,"name":"Browse",'width':50,"height":10,
                           "action":self.setLig},
                    "ok":{"id":id+2,"name":"Add Scorer",'width':50,"height":10,
                          "action":self.setup},
                    "gScore":{"id":id+3,"name":"Get Score",'width':50,"height":10,
                          "action":self.getScore}      
                    }
        id = id + len(self.BTN)
        self.TXT = {"rec":{"id":id,"name":"Receptor",'width':50,
                           "height":10,"action":None},
                    "lig":{"id":id+1,"name":"ligand",'width':50,
                           "height":10,"action":None}
                    }
        id = id + len(self.TXT)

        self.COMB_BOX = {"score":{"id":id,"name":"type of score","width":60,
                                  "height":10,"action":self.setScorer},
                         "scorer":{"id":id+1,"name":"available scorer","width":60,
                                   "height":10,"action":self.setCurrentScorer},
                         }
        id = id + len(self.COMB_BOX)
        self.scorertype = ['PyPairWise','ad3Score','ad4Score']
        if C.cAD : #cAutodock is available
            self.scorertype.append('c_ad3Score')
            self.scorertype.append('PairWise')
        self.getScorerAvailable()
        self.CHECKBOXS ={"store":{"id":id,"name":"store",'width':100,
                                  "height":10,"action":self.toggleStore},
                        "displayLabel":{"id":id+1,"name":"display Label",'width':100,
                                    "height":10,"action":self.toggleDisplay},
                        "colorRec":{"id":id+2,"name":"color Rec",'width':100,
                                    "height":10,"action":self.toggleColor},
                        "colorLig":{"id":id+3,"name":"color Lig",'width':100,
                                    "height":10,"action":self.toggleColor},
                        "realtime":{"id":id+4,"name":"real time",'width':100,
                                    "height":10,"action":self.setRealtime}
                                    }
        id = id + len(self.CHECKBOXS)
        return True

    def CreateLayout(self):
        ID=0
        self.SetTitle("PyAutoDock")
        self.initWidgetId()
        #minimize otin/button
        self.GroupBegin(id=ID,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                           cols=2, rows=4)
        self.GroupBorderSpace(1, 1, 1, 1)
        ID = ID +1

        self.AddStaticText(ID,flags=c4d.BFH_SCALEFIT)
        self.SetString(ID,"Receptor")
        ID = ID +1
        
        self.rec=self.AddEditText(id=self.TXT['rec']["id"],flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK)
#        self.AddButton(id=self.BTN["rec"]["id"], flags=c4d.BFH_LEFT | c4d.BFV_MASK,
#                            initw=self.BTN["rec"]["width"],
#                            inith=self.BTN["rec"]["height"],
#                            name=self.BTN["rec"]["name"])
        self.SetString(self.TXT['rec']["id"],"hsg1:::;")
        self.AddStaticText(ID,flags=c4d.BFH_SCALEFIT)
        self.SetString(ID,"Ligand")        
        ID = ID +1
        self.lig=self.AddEditText(id=self.TXT['lig']["id"],flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK)
        self.SetString(self.TXT['lig']["id"],"ind:::;")
#        self.AddButton(id=self.BTN["rec"]["id"], flags=c4d.BFH_LEFT | c4d.BFV_MASK,
#                            initw=self.BTN["rec"]["width"],
#                            inith=self.BTN["rec"]["height"],
#                            name=self.BTN["rec"]["name"])

        self.AddStaticText(ID,flags=c4d.BFH_SCALEFIT)
        self.SetString(ID,"Scorer")        
        ID = ID +1
        self._scorertype=self.AddComboBox(id=self.COMB_BOX["score"]["id"],flags=c4d.BFH_SCALEFIT,initw=60)
        map(lambda x,box=self._scorertype:self.AddChild(box,x[0],x[1]),enumerate(self.scorertype))
                                
        self.GroupEnd()
        self.GroupBegin(id=ID,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                           cols=1, rows=4)
        self.GroupBorderSpace(1, 1, 1, 1)
        ID = ID +1
                                

        self.AddButton(id=self.BTN["ok"]["id"], flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                            initw=self.BTN["ok"]["width"],
                            inith=self.BTN["ok"]["height"],
                            name=self.BTN["ok"]["name"])
        
        #should display here a menu of available scorer...
        self._currentscorer=self.AddComboBox(id=self.COMB_BOX["scorer"]["id"],
                                             flags=c4d.BFH_SCALEFIT,initw=60)
        map(lambda x,box=self._currentscorer:self.AddChild(box,x[0],x[1]),enumerate(self.scoreravailable))
        for butk in self.CHECKBOXS.keys():
            self.AddCheckbox(id=self.CHECKBOXS[butk]["id"],flags=c4d.BFH_SCALEFIT,
                                name=self.CHECKBOXS[butk]["name"],
                                initw=self.CHECKBOXS[butk]["width"],
                                inith=self.CHECKBOXS[butk]["height"])

        self.AddButton(id=self.BTN["gScore"]["id"], flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                            initw=self.BTN["gScore"]["width"],
                            inith=self.BTN["gScore"]["height"],
                            name=self.BTN["gScore"]["name"])                        

        return True

    def setRealtime(self):
        if hasattr(self.epmv.mv,'energy'):
            self.epmv.mv.energy.realTime = self.GetBool(self.CHECKBOXS['realtime']['id'])

    def toggleDisplay(self):
        if hasattr(self.epmv.mv,'energy') :
            display = self.GetBool(self.CHECKBOXS['displayLabel']['id'])
            if display and not self._display:
                self.initDisplay()
                self._display = True
            else :
                obj = self.label
                self.epmv._toggleDisplay(obj,display)

            if not hasattr(self.epmv.mv.energy,'label'):
                setattr(self.epmv.mv.energy, 'label', display)
            else :
                self.epmv.mv.energy.label = display

    def toggleStore(self):
        store = self.GetBool(self.CHECKBOXS['store']['id'])
        
        
    def toggleColor(self):
        if hasattr(self.epmv.mv,'energy') :
            r=self.GetBool(self.CHECKBOXS['colorRec']['id'])
            l=self.GetBool(self.CHECKBOXS['colorLig']['id'])
            if hasattr(self.epmv.mv,'energy') :
                if not hasattr(self.epmv.mv.energy,'color'):
                    setattr(self.epmv.mv.energy, 'color', [r,l])
                else :
                    self.epmv.mv.energy.color = [r,l]
                
    def getScore(self):
        if hasattr(self.epmv.mv,'energy'):
            self.epmv.helper.get_nrg_score(self.epmv.mv.energy)

    def setRec(self):
        pass
    def setLig(self):
        pass

    def getScorerAvailable(self):
        self.scoreravailable = []
        if hasattr(self.epmv.mv,'energy'):
            self.scoreravailable = self.epmv.mv.energy.data.keys()

    def setCurrentScorer(self):
        self.getScorerAvailable()
        name = self.scoreravailable[self.GetLong(self._currentscorer)]
        self.epmv.mv.energy.current_scorer = self.epmv.mv.energy.data[name]

    def setScorer(self):
        self._scorer = self.scorertype[self.GetLong(self._scorertype)]
        
    def setup(self):
        #get Rec
        rname = self.GetString(self.TXT['rec']['id'])
        #get Lig
        print rname
        lname = self.GetString(self.TXT['lig']['id'])
        print lname
        #is this can be selection ? yep
        #recSet=self.mv.select(rname,negate=False, only=True, xor=False, 
        #                           log=0, intersect=False)
        recSet=self.epmv.mv.expandNodes(rname)
        rec = recSet[0].top
        #=self.epmv.mv.getMolFromName(rname)
        ligSet=self.epmv.mv.expandNodes(lname)
        lig = ligSet[0].top
        #test lig and rec
        scorer_name =  rec.name+'-'+lig.name+'-'+self._scorer
        if rec is not None and lig is not None:
            if not hasattr(self.epmv.mv,'energy'):
                self.epmv.mv.energy = C.EnergyHandler(self.epmv.mv)
            self.getScorerAvailable()                
            self.epmv.mv.energy.add(recSet,ligSet,score_type=self._scorer)
            self.AddChild(self._currentscorer,len(self.scoreravailable),scorer_name)
            confNum = 1
            for mol in [rec,lig]:
                # check number of conformations available
                current_confNum = len(mol.allAtoms[0]._coords) -1
                mol.allAtoms.addConformation(mol.allAtoms.coords)
                mol.cconformationIndex = len(mol.allAtoms[0]._coords) -1
        self.toggleDisplay()
        self.toggleColor()
        self.setRealtime()    
            
    def initDisplay(self):
        scene =self.epmv.helper.getCurrentScene()
        s1=c4d.BaseObject(c4d.Osphere)
        s1.SetName("sphere_rec")
        s1[self.epmv.helper.PRIM_SPHERE_RAD]=2.
        s2=c4d.BaseObject(c4d.Osphere)
        s2.SetName("sphere_lig")
        s2[self.epmv.helper.PRIM_SPHERE_RAD]=2.
        self.epmv.helper.addObjectToScene(scene,s1)
        self.epmv.helper.addObjectToScene(scene,s2)        
        #label
        self.label=label = self.epmv.helper.newEmpty("label")
        label.MakeTag(self.epmv.helper.LOOKATCAM)
        self.epmv.helper.addObjectToScene(scene,label)
        TEXT = self.epmv.helper.TEXT
        text1 =  c4d.BaseObject(TEXT)
        text1.SetName("score")
        text1[2111] = "score : 0.00"
        text1[2115] = 5.
        text1[904,1000] = 3.14
        text1[903,1001] = 4.
        text2 =  c4d.BaseObject(TEXT)
        text2.SetName("el")
        text2[2111] = "el : 0.00"
        text2[2115] = 5.0
        text2[904,1000] = 3.14
        text3 =  c4d.BaseObject(TEXT)
        text3.SetName("hb")
        text3[2111] = "hb : 0.00"
        text3[2115] = 5.0
        text3[904,1000] = 3.14
        text3[903,1001] = -4.
        text4 =  c4d.BaseObject(TEXT)
        text4.SetName("vw")
        text4[2111] = "vw : 0.00"
        text4[2115] = 5.0
        text4[904,1000] = 3.14
        text4[903,1001] = -8.
        text5 =  c4d.BaseObject(TEXT)
        text5.SetName("so")
        text5[2111] = "so : 0.00"
        text5[2115] = 5.0
        text5[904,1000] = 3.14
        text5[903,1001] = -12.
        self.epmv.helper.addObjectToScene(scene,text1,parent=label)
        self.epmv.helper.addObjectToScene(scene,text2,parent=label)
        self.epmv.helper.addObjectToScene(scene,text3,parent=label)
        self.epmv.helper.addObjectToScene(scene,text4,parent=label)
        self.epmv.helper.addObjectToScene(scene,text5,parent=label)     


#######EVENT COMMAND######################################################
    def Command(self, id, msg):
        c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        for butn in self.BTN.keys():
            if id == self.BTN[butn]["id"]:
                self.BTN[butn]["action"]()
        for butn in self.COMB_BOX.keys():
            if id == self.COMB_BOX[butn]["id"]:
                self.COMB_BOX[butn]["action"]()
        for butn in self.CHECKBOXS.keys():
            if id == self.CHECKBOXS[butn]["id"]:
                if self.CHECKBOXS[butn]["action"] is not None :
                    self.CHECKBOXS[butn]["action"]()
        c4d.gui.SetMousePointer(c4d.MOUSE_NORMAL)
        self.epmv.gui.updateViewer()
        return True
    
class ParameterModeller(gui.SubDialog,epmvGui.ParameterModeller):
    #.epmv
    def initWidgetId(self):
        epmvGui.ParameterModeller.__init__(self,epmv=self.epmv)
        #need to update the action
        self.CHECKBOXS['real-time']["action"] = self.setRealTime
        self.CHECKBOXS['store']["action"] = self.setStoring
        self.NUMBERS['rtstep']["action"] = self.setRealTimeStep
        self.BTN['mini']["action"] = self.epmv.gui.modellerOptimize
        self.BTN['md']["action"] = self.epmv.gui.modellerMD
        self.COMB_BOX["sobject"]["action"] = self.setObjectSynchrone
        self.COMB_BOX["rtType"]["action"] = self.setRToptimzeType
        return True

    def CreateLayout(self):
        ID=0
        self.SetTitle("Modeller")
        self.initWidgetId()
        #minimize otin/button
        self.GroupBegin(id=ID,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                           cols=2, rows=4)
        self.GroupBorderSpace(1, 1, 1, 1)
        ID = ID +1
        #store?
        
#        for checkB in self.CHECKBOXS:
        self.AddCheckbox(id=self.CHECKBOXS["store"]["id"],flags=c4d.BFH_CENTER,
                                name=self.CHECKBOXS["store"]["name"],
                                initw=self.CHECKBOXS["store"]["width"],
                                inith=self.CHECKBOXS["store"]["height"])
        self.AddStaticText(ID,flags=c4d.BFH_LEFT)
        self.SetString(ID,"")                                    
        ID = ID +1
        self.AddCheckbox(id=self.CHECKBOXS["real-time"]["id"],flags=c4d.BFH_CENTER,
                                name=self.CHECKBOXS["real-time"]["name"],
                                initw=self.CHECKBOXS["real-time"]["width"],
                                inith=self.CHECKBOXS["real-time"]["height"])

        cb=self.AddComboBox(id=self.COMB_BOX["rtType"]["id"],flags=c4d.BFH_LEFT,initw=56)
        [self.AddChild(cb,x[0],x[1]) for x in enumerate(self.rtType) ]

        self.AddStaticText(ID,flags=c4d.BFH_LEFT)
        self.SetString(ID,"timestep realtime")   
        ID = ID +1        
        n = self.AddEditNumberArrows(id=self.NUMBERS["rtstep"]["id"],flags=c4d.BFH_CENTER,
                                initw=self.NUMBERS["rtstep"]["width"],
                                inith=self.NUMBERS["rtstep"]["height"])
        self.SetLong(n,2,0,  100000, 1)

        self.AddButton(id=self.BTN["update coordinate"]["id"], flags=c4d.BFH_LEFT | c4d.BFV_MASK,
                            initw=self.BTN["update coordinate"]["width"],
                            inith=self.BTN["update coordinate"]["height"],
                            name=self.BTN["update coordinate"]["name"])
#        self.AddStaticText(ID,flags=c4d.BFH_LEFT)
#        self.SetString(ID,"")                                    
#        ID = ID +1
        
        cb=self.AddComboBox(id=self.COMB_BOX["sobject"]["id"],flags=c4d.BFH_LEFT,initw=56)
        [self.AddChild(cb,x[0],x[1]) for x in enumerate(self.sObject) ]
#        map(lambda x,box=self.COMB_BOX["sobject"]["id"]:self.AddChild(box,x[0],x[1]),enumerate(self.sObject))

        #minimize
        self.AddStaticText(ID,flags=c4d.BFH_LEFT)
        self.SetString(ID,"max_iteration")   
        ID = ID +1        
        n = self.AddEditNumberArrows(id=self.NUMBERS["miniIterMax"]["id"],flags=c4d.BFH_CENTER,
                                initw=self.NUMBERS["miniIterMax"]["width"],
                                inith=self.NUMBERS["miniIterMax"]["height"])
        self.SetLong(n,1000,0,  100000, 10)
        self.AddButton(id=self.BTN["mini"]["id"], flags=c4d.BFH_LEFT | c4d.BFV_MASK,
                            initw=self.BTN["mini"]["width"],
                            inith=self.BTN["mini"]["height"],
                            name=self.BTN["mini"]["name"])
        self.AddStaticText(ID,flags=c4d.BFH_LEFT)
        self.SetString(ID,"")                                    
        ID = ID + 1
        #MD
        self.AddStaticText(ID,flags=c4d.BFH_LEFT)
        self.SetString(ID,"max_iteration")                                    
        ID = ID + 1
        n = self.AddEditNumberArrows(id=self.NUMBERS["mdIterMax"]["id"],flags=c4d.BFH_CENTER,
                                initw=self.NUMBERS["mdIterMax"]["width"],
                                inith=self.NUMBERS["mdIterMax"]["height"])
        self.SetLong(n,1000,0,  100000, 10)
        self.AddStaticText(ID,flags=c4d.BFH_LEFT)
        self.SetString(ID,"temperature")                                    
        ID = ID + 1
        n = self.AddEditNumberArrows(id=self.NUMBERS["mdTemp"]["id"],flags=c4d.BFH_CENTER,
                                initw=self.NUMBERS["mdTemp"]["width"],
                                inith=self.NUMBERS["mdTemp"]["height"])
        self.SetReal(n,300.,-100.,  1000., 1.)
        self.AddButton(id=self.BTN["md"]["id"], flags=c4d.BFH_LEFT | c4d.BFV_MASK,
                            initw=self.BTN["md"]["width"],
                            inith=self.BTN["md"]["height"],
                            name=self.BTN["md"]["name"])
        self.AddStaticText(ID,flags=c4d.BFH_LEFT)
        self.SetString(ID,"")                                    
        ID = ID + 1

        return True

    def setStoring(self):
        mol = self.epmv.gui.current_mol
        mol.pmvaction.store = self.GetBool(self.CHECKBOXS['store']['id'])
 
    def setObjectSynchrone(self):
        mol = self.epmv.gui.current_mol
        mol.pmvaction.sObject = self.sObject[self.GetLong(self.COMB_BOX["sobject"]['id'])]

    def setRToptimzeType(self):
        mol = self.epmv.gui.current_mol
        rtype= self.rtType[self.GetLong(self.COMB_BOX["rtType"]['id'])]
        if mol.pmvaction.rtType != rtype :
            mol.pmvaction.rtType = rtype
            #need to update the optimizer ie delete and create a new one
            mol.pmvaction.resetOptimizer()

    #overwrite RT checkbox action
    def setRealTime(self):
        mol = self.epmv.gui.current_mol
        mol.pmvaction.temp = self.GetLong(self.NUMBERS["mdTemp"]['id'])
        mol.pmvaction.realtime = self.GetBool(self.CHECKBOXS['real-time']['id'])
        
    def setRealTimeStep(self):
        mol = self.epmv.gui.current_mol
        mol.pmvaction.mdstep = self.GetLong(self.NUMBERS['rtstep']['id'])

#######EVENT COMMAND######################################################
    def Command(self, id, msg):
        c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        for butn in self.BTN.keys():
            if id == self.BTN[butn]["id"]:
                if self.BTN[butn]["action"] is not None :
                    self.BTN[butn]["action"]()
        for butn in self.NUMBERS.keys():
            if id == self.NUMBERS[butn]["id"]:
                if self.NUMBERS[butn]["action"] is not None :
                    self.NUMBERS[butn]["action"]()
        for butn in self.CHECKBOXS.keys():
            if id == self.CHECKBOXS[butn]["id"]:
                if self.CHECKBOXS[butn]["action"] is not None :
                    self.CHECKBOXS[butn]["action"]()                    
        for butn in self.COMB_BOX.keys():
            if id == self.COMB_BOX[butn]["id"]:
                if self.COMB_BOX[butn]["action"] is not None :
                    self.COMB_BOX[butn]["action"]()                    
        c4d.gui.SetMousePointer(c4d.MOUSE_NORMAL)
        self.epmv.gui.updateViewer()
        return True


class Parameter_ePMV(gui.SubDialog):
    #.epmv
    def initWidgetId(self):
        #minimize options
        #max_iterations=1000
        #md options
        #temperature=300, max_iterations=1000
        witdh=350
        id=1005
        #need to split in epmv options and gui options - >guiClass?
        self.OPTIONS = {'cam':{"id": id, "name":"PMV camera",'width':witdh,"height":10,"action":None},
                       'light':{"id": id+1, "name":"PMV lights",'width':witdh,"height":10,"action":None},
                       'clouds':{"id": id+2, "name":"Render points",'width':witdh,"height":10,"action":None},
                       'cyl':{"id": id+3, "name":"Split bonds",'width':witdh,"height":10,"action":None},
                       'log':{"id": id+4, "name":"Console log",'width':witdh,"height":10,"action":None},
                       'center':{"id": id+5, "name":"Center Molecule",'width':witdh,"height":10,"action":None},
                       'centerG':{"id": id+6, "name":"Center Grid",'width':witdh,"height":10,"action":None},
                       'fetch':{"id": id+7, "name":"Force Fetch instead of cache",'width':witdh,"height":10,"action":None},
                       'depthQ':{"id": id+8, "name":"Environment depth cueing",'width':witdh,"height":10,"action":None},
                       'stimeline':{"id": id+9, "name":"Synchronize data player to timeline",'width':witdh,"height":10,"action":None},
                       }
        id = id + len(self.OPTIONS)
        if self.epmv.gui._modeller :
            self.OPTIONS['modeller']={"id": id, "name":"Modeller",'width':witdh,"height":10,"action":None}
            id = id + 1
        self.INPUT ={'timeStep':{"id": id, "name":"steps every",'width':50,"height":10,"action":None},
                     'frameStep':{"id": id+1, "name":"frames",'width':50,"height":10,"action":None},
        }
        id = id + (len(self.INPUT))
        self.BTN = {"ok":{"id":id,"name":"OK",'width':50,"height":10,"action":self.SetPreferences}}
        id = id + 1
        return True

    def CreateLayout(self):
        ID=0
        self.SetTitle("Preferences")
        self.initWidgetId()
        #minimize otin/button
        self.GroupBegin(id=ID,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                           cols=1, rows=10)
        self.GroupBorderSpace(10, 10, 5, 10)
        ID = ID +1
        #store?
        for k in self.OPTIONS.keys():
            self.AddCheckbox(id=self.OPTIONS[k]["id"],flags=c4d.BFH_SCALEFIT,
                                name=self.OPTIONS[k]["name"],
                                initw=self.OPTIONS[k]["width"],
                                inith=self.OPTIONS[k]["height"])
            if k == "stimeline":
                self.GroupBegin(id=ID,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                        cols=4, rows=1)
                self.GroupBorderSpace(0, 5, 0, 5)
                ID = ID +1
                self.AddEditNumberArrows(self.INPUT["timeStep"]["id"], c4d.BFH_SCALEFIT, 
                                                    initw=self.INPUT["timeStep"]["width"], 
                                                    inith=self.INPUT["timeStep"]["height"])
                self.AddStaticText(ID,c4d.BFH_SCALEFIT)
                self.SetString(ID,self.INPUT["timeStep"]["name"])                                    
                self.AddEditNumberArrows(self.INPUT["frameStep"]["id"], c4d.BFH_SCALEFIT, 
                                                    initw=self.INPUT["frameStep"]["width"], 
                                                    inith=self.INPUT["frameStep"]["height"])
                ID = ID +1
                self.AddStaticText(ID,c4d.BFH_SCALEFIT)
                self.SetString(ID,self.INPUT["frameStep"]["name"])                                                    
                self.GroupEnd()
        self.AddButton(id=self.BTN["ok"]["id"], flags=c4d.BFH_CENTER | c4d.BFV_MASK,
                            initw=self.BTN["ok"]["width"],
                            inith=self.BTN["ok"]["height"],
                            name=self.BTN["ok"]["name"])
        self.restorePreferences()
        return True        

    def SetPreferences(self):
        self.epmv.doCamera = self.GetBool(self.OPTIONS['cam']["id"])
        self.epmv.doLight = self.GetBool(self.OPTIONS['light']["id"])
        self.epmv.doCloud = self.GetBool(self.OPTIONS['clouds']["id"])
        self.epmv.bicyl = self.GetBool(self.OPTIONS['cyl']["id"])
        self.epmv.center_mol = self.GetBool(self.OPTIONS['center']["id"])
        self.epmv.center_grid = self.GetBool(self.OPTIONS['centerG']["id"])
        self.epmv.gui._logConsole = self.GetBool(self.OPTIONS['log']["id"])
        self.epmv.gui._forceFetch = self.GetBool(self.OPTIONS['fetch']["id"])
        self.epmv.gui._depthQ = self.GetBool(self.OPTIONS['depthQ']["id"])
        self.epmv.synchro_timeline= self.GetBool(self.OPTIONS['stimeline']["id"])
        self.epmv.synchro_ratio[0] = self.GetLong(self.INPUT['timeStep']["id"])
        self.epmv.synchro_ratio[1] = self.GetLong(self.INPUT['frameStep']["id"])
        
        if self.epmv.gui._modeller :
            self.epmv.gui._useModeller = self.GetBool(self.OPTIONS['modeller']["id"])
            self.epmv.useModeller = self.epmv.gui._useModeller
            if self.epmv.gui._useModeller :
                self.epmv.center_mol = False
                self.epmv.center_grid = False
                if self.epmv.gui.env is None:
                    import modeller
                    from Pmv.hostappInterface.extension.Modeller.pmvAction import setupENV
                    #setup Modeller
                    self.epmv.gui.env = setupENV()
        #self.AskClose()
        if self.epmv.gui._depthQ :
            self.epmv.helper.create_environment('depthQ',distance = 30.)
        else :
            obj=self.epmv.helper.getObject('depthQ')
            if obj is not None :
                self.epmv.helper.toggleDisplay(obj,False)
        self.Close()
        
    def restorePreferences(self):
        self.SetBool(self.OPTIONS['cam']["id"],self.epmv.doCamera)
        self.SetBool(self.OPTIONS['light']["id"],self.epmv.doLight)
        self.SetBool(self.OPTIONS['clouds']["id"],self.epmv.doCloud)
        self.SetBool(self.OPTIONS['cyl']["id"],self.epmv.bicyl)
        self.SetBool(self.OPTIONS['log']["id"],self.epmv.gui._logConsole)
        self.SetBool(self.OPTIONS['center']["id"],self.epmv.center_mol)
        self.SetBool(self.OPTIONS['centerG']["id"],self.epmv.center_grid)
        self.SetBool(self.OPTIONS['fetch']["id"],self.epmv.gui._forceFetch)
        self.SetBool(self.OPTIONS['depthQ']["id"],self.epmv.gui._depthQ)
        self.SetBool(self.OPTIONS['stimeline']["id"],self.epmv.synchro_timeline)
        self.SetLong(self.INPUT['timeStep']["id"],self.epmv.synchro_ratio[0])
        self.SetLong(self.INPUT['frameStep']["id"],self.epmv.synchro_ratio[1])
        
        if self.epmv.gui._modeller :
            self.SetBool(self.OPTIONS['modeller']["id"],self.epmv.gui._useModeller)
        
#######EVENT COMMAND######################################################
    def Command(self, id, msg):
        c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        for butn in self.BTN.keys():
            if id == self.BTN[butn]["id"]:
                self.BTN[butn]["action"]()
        c4d.gui.SetMousePointer(c4d.MOUSE_NORMAL)
        self.epmv.gui.updateViewer()
        return True

class epmv_c4d(gui.GeDialog):
    restored=False
    status = 0
    link = 0
    __red_mat = None
    __current_doc = None
    _box = None
    _maingroup=None
    _color=None
    nF=1000
    _useModeller = False
    _modeller = False
    _AF = False
    _AR = False
    _logConsole = False
    _forceFetch = False
    inst = None
    _depthQ = False
    
    def setupEPMV(self):
        from Pmv.hostappInterface.cinema4d_dev.c4dAdaptor import c4dAdaptor
        doc = c4d.documents.GetActiveDocument()
        dname=doc.GetDocumentName()
        if dname not in c4d.mv.keys() :
            epmv = c4dAdaptor(debug=0)
            c4d.mv[dname]=epmv#self.epmv.helper.start(debug=1)
            #create the empty epmv object and add the epmv_synchro Tag
            root = epmv._newEmpty("ePMV")
            root.MakeTag(1023745)
            epmv._addObjectToScene(doc,root)
            self.updateViewer()
        self.mv=c4d.mv[dname].mv#self.epmv.helper.start(debug=1)
        self.epmv=c4d.mv[dname]                            
        
        self.epmv.gui = self.mv.GUI = self
        self.mv.GUI.VIEWER = self
        def t(val):
            print val
        self.TransformRootOnly = t
        
        self.funcColor = [self.mv.colorByAtomType,self.mv.colorAtomsUsingDG,
                            self.mv.colorByResidueType,self.mv.colorBySecondaryStructure,
                            self.mv.color,self.mv.colorByProperty,
                            self.mv.colorByChains]        
        self.set_up()
        self.epmv.timer = False
        self.env = None  
        
    def initWidgetId(self):

        if VERBOSE : print "__init__ values"
        id = 1005
        self.MENU_ID = {"File":
                      [{"id": id, "name":"Recent Files","action":None},
                      {"id": id+1, "name":"Open PDB","action":self.buttonLoad},
                       {"id": id+2, "name":"Open Data","action":self.buttonLoadData}],
                       "Edit" :
                      [{"id": id+3, "name":"Options","action":self.drawPreferences}],
#                      [{"id": id+3, "name":"Camera&c&","action":self.optionCam},
#                       {"id": id+4, "name":"Light&c&","action":self.optionLight},
#                       {"id": id+5, "name":"CloudsPoints&c&","action":self.optionPC},
#                       {"id": id+6, "name":"BiCylinders&c&","action":self.optionCyl}],
                       "Extensions" : [
                       {"id": id+4, "name":"PyAutoDock","action":self.drawPyAutoDock}
                       ],
                       "Help" : 
                      [{"id": id+5, "name":"About ePMV","action":self.drawAbout},
                       {"id": id+6, "name":"ePMV documentation","action":self.launchBrowser},
                       {"id": id+7, "name":"Check for Update","action":self.check_update},
                       {"id": id+8, "name":"Citation Informations","action":self.citationInformation},
                      ],
                       }
        id = id + 9
        if self._AF :
            self.MENU_ID["Extensions"].append({"id": id, "name":"AutoFill",
                                                "action":self.launchAFgui})
            id = id + 1 
        if self._AR :
            self.MENU_ID["Extensions"].append({"id": id, "name":"ARViewer",
                                                "action":self.launchARgui})
            id = id + 1 
        if self._modeller:            
            self.MENU_ID["Extensions"].append({"id": id, "name":"Modeller",
                                                "action":self.modellerGUI})
            id = id + 1
        self.MENU_ID["Extensions"].append({"id": id, "name":"Add an Extension",
                                                "action":self.addExtensionGUI})
        id = id + 1
        self.LABEL_ID = [{"id":id,"label":"to a PDB file OR enter a 4 digit ID (e.g. 1crn):"},
                         {"id":id+1,"label":""},
                         {"id":id+2,"label":"Current selection :"},
                         {"id":id+3,"label":"Add selection set using string or"},
                         {"id":id+4,"label":"Color scheme:"},
                         {"id":id+5,"label":"to load a Data file"},
                         {"id":id+6,"label":"to Current Selection and play below:"},
                         {"id":id+7,"label":"PMV-Python scripts/commands"},
                         {"id":id+8,"label":"Molecular Representations"},
                         {"id":id+9,"label":"Apply"},
                         {"id":id+10,"label":"a Selection Set"},
                         {"id":id+11,"label":"atoms in the Selection Set"},
                         {"id":id+12,"label":"or"},
                         {"id":id+13,"label":"or"},
                         {"id":id+14,"label":":"},
                         ]      
        id = id + len(self.LABEL_ID)#4?
        
        self.EDIT_TEXT = {"id":id,"name":"pdbId","action":None}
        id = id + 1
        
        self.DATA_TEXT = {"id":id,"name":"dataFile","action":None}
        id = id +1
        self.LOAD_BTN = {"id":id,"name":"Browse",'width':40,"height":10,
                         "action":self.buttonBrowse}
        id = id + 1
        self.FETCH_BTN = {"id":id,"name":"Fetch",'width':30,"height":10,
                         "action":self.buttonLoad}
        id = id + 1
        self.DATA_BTN = {"id":id,"name":"Browse",'width':50,"height":10,
                         "action":self.buttonLoadData}
        id = id + 1
        self.PMV_BTN = {"id":id,"name":"Submit/exec",'width':80,"height":10,
                         "action":self.execPmvComds}
        id = id + 1
        self.KEY_BTN= {"id":id,"name":"store key-frame",'width':80,"height":10,
                         "action":None}
        id = id + 1
        self.DEL_BTN= {"id":id,"name":"delete",'width':80,"height":10,
                         "action":self.deleteMol}
        id = id + 1

        self.COMB_BOX = {"mol":{"id":id,"width":60,"height":10,"action":self.update},
                         "col":{"id":id+1,"width":60,"height":10,"action":self.color},
                         "dat":{"id":id+2,"width":60,"height":10,"action":self.updateTraj},
                         "pdbtype":{"id":id+3,"width":50,"height":10,"action":None},
                         "datatype":{"id":id+4,"width":60,"height":10,"action":None},
                         "preset":{"id":id+5,"width":60,"height":10,"action":self.drawPreset},
                         "keyword":{"id":id+6,"width":60,"height":10,"action":self.setKeywordSel},
                         "scriptO":{"id":id+7,"width":60,"height":10,"action":self.set_ePMVScript},
                         "scriptS":{"id":id+8,"width":60,"height":10,"action":self.save_ePMVScript},
                         "selection":{"id":id+9,"width":60,"height":10,"action":self.edit_Selection},
                         }
        id = id + len(self.COMB_BOX)
        
        self.pdbtype=['PDB','TMPDB','OPM','CIF','PQS']
        self.datatype=['e.g.','Trajectories:','  .trj','  .xtc','VolumeGrids:']
        DataSupported = '\.mrc$|\.MRC$|\.cns$|\.xplo*r*$|\.ccp4*$|\.grd$|\.fld$|\.map$|\.omap$|\.brix$|\.dsn6$|\.dn6$|\.rawiv$|\.d*e*l*phi$|\.uhbd$|\.dx$|\.spi$'
        DataSupported=DataSupported.replace("\\","  ").replace("$","").split("|")
        self.datatype.extend(DataSupported)
        self.presettype=['available presets:','  Lines','  Liccorice','  SpaceFilling',
                         '  Ball+Sticks','  RibbonProtein+StickLigand',
                         '  RibbonProtein+CPKligand','  xray','  Custom',
                         '  Save Custom As...']
        self.keyword = ['keywords:','  backbone','  sidechain','  chain','  picked']
        kw=map(lambda x:"  "+x,ResidueSetSelector.residueList.keys())
        self.keyword.extend(kw)
        
        self.scriptliste = ['Open:',
                            'pymol_demo',
                            'interactive_docking',
                            'colorbyAPBS',
                            'demo1',
                            'user_script']
        self.scriptsave = ['Save','Save as']
        self.editselection = ['Save set','Rename set','Delete set']
        
        self.SELEDIT_TEXT = {"id":id,"name":"selection","action":None}
        id = id+1
        
        self.SEL_BTN ={"add":{"id":id,"name":"Save set",'width':45,"height":10,
                            "action":self.add_Selection},
                        "rename":{"id":id+1,"name":"Rename",'width':44,"height":10,
                            "action":self.rename_Selection},
                        "deleteS":{"id":id+2,"name":"Delete Set",'width':33,"height":10,
                            "action":self.delete_Selection},
                        "deleteA":{"id":id+3,"name":"Delete",'width':33,"height":10,
                            "action":self.delete_Atom_Selection}    
                        }
        id = id + len(self.SEL_BTN)
        self.CHECKBOXS ={"cpk":{"id":id,"name":"Atoms",'width':80,"height":10,"action":self.displayCPK},
                         "bs":{"id":id+1,"name":"Sticks",'width':80,"height":10,"action":self.displayBS},
                         "ss":{"id":id+2,"name":"Ribbons",'width':40,"height":10,"action":self.displaySS},
                         "loft":{"id":id+3,"name":"Loft",'width':40,"height":10,"action":self.createLoft},
                         "arm":{"id":id+4,"name":"Armature",'width':40,"height":10,"action":self.createArmature},
                         "spline":{"id":id+5,"name":"Spline",'width':40,"height":10,"action":self.createSpline},
                         "surf":{"id":id+6,"name":"MSMSurf",'width':80,"height":10,"action":self.displaySurf},
                         "cms":{"id":id+7,"name":"CoarseMolSurf",'width':80,"height":10,"action":self.displayCoarseMS},
                         "meta":{"id":id+8,"name":"MetaBalls",'width':40,"height":10,"action":self.displayMetaB}
                         }
        id = id + len(self.CHECKBOXS)            
        self.SLIDERS = {"cpk":{"id":id,"name":"cpk_scale",'width':35,"height":10,"action":self.displayCPK},
                        "bs_s":{"id":id+1,"name":"bs_scale",'width':35,"height":10,"action":self.displayBS},
                        "bs_r":{"id":id+2,"name":"bs_ratio",'width':35,"height":10,"action":self.displayBS},
                        #"ss":{"id":id+2,"name":"ss",'width':15,"height":10,"action":self.displaySS},
                        #"loft":{"id":id+3,"name":"loft",'width':15,"height":10,"action":self.createLoft},
                        #"arm":{"id":id+4,"name":"armature",'width':15,"height":10,"action":self.createArmature},
                        #"spline":{"id":id+5,"name":"spline",'width':15,"height":10,"action":self.createSpline},
                        "surf":{"id":id+3,"name":"probe",'width':45,"height":10,"action":self.updateSurf},
                        "cmsI":{"id":id+4,"name":"isovalue",'width':45,"height":10,"action":self.updateCoarseMS},
                        "cmsR":{"id":id+5,"name":"resolution",'width':45,"height":10,"action":self.updateCoarseMS},
                        #"meta":{"id":id+8,"name":"MBalls",'width':15,"height":10,"action":self.displayMetaB}
                        "datS":{"id":id+6,"name":"state",'width':50,"height":10,"action":self.applyState},
                        #"datV":{"id":id+7,"name":"value",'width':15,"height":10,"action":self.applyValue},                        
                        }
        id = id + len(self.SLIDERS)            
        self.COLFIELD = {"id":id,"name":"chooseCol","action":self.chooseCol}
        id = id + 1
        self.pd = ParameterModeller()
        self.argui = ParameterARViewer()
        self.ad=ParameterScoring()
        self.options = Parameter_ePMV()
        return True

    def InitValues(self):
        self.dash=False
        self.nF=10
        self.ResidueSelector=ResidueSetSelector()      
        self.nModels=0      
        self.im = 0#2071+4
        self.ic = 0#2039+3+4#4
        self.idata = 0#2053+13+4#4
        self.bc = c4d.BaseContainer() #basecontainer for the progressBar
        self.indice_mol=0
        self.indice=0
        self.indiceData=0
        #print self.dash
        return True

    def set_up(self):
        #print "set_up"   
        self.indice_mol=0
        self.indice=0
        self.indiceData=0
        if not hasattr(self.mv,'molDispl') : self.mv.molDispl={}
        if not hasattr(self.mv,'MolSelection') : self.mv.MolSelection={}
        if not hasattr(self.mv,'selections') : self.mv.selections={}
        if not hasattr(self.mv,'iMol') : self.mv.iMol={}
        if not hasattr(self.mv,'iSel') : self.mv.iSel={}
        if not hasattr(self.mv,'iTraj') : self.mv.iTraj={}
        if not hasattr(self.mv,'iMolData') : self.mv.iMolData={}
        self.current_traj=[None,""]
        self.current_mol = None
        self.firstmol=True
        self.firsttraj=True

    def checkExtension(self):
        if self.inst is None :
            self.inst = Installer(gui=False)
            self.inst.mgltoolsDir=MGL_ROOT
            self.inst.currDir=MGL_ROOT+os.sep+"MGLToolsPckgs"+os.sep+"Pmv"+os.sep+"hostappInterface"
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
            

    def CreateLayout(self):       
        self.checkExtension()
        self.setupEPMV()        
        self.initWidgetId()
        #set the title
        self.SetTitle("ePMV") #set the title
        #create the menu
        self.MenuFlushAll()
        #feed menu
        self.menuGadget={}
        ordered = ["File","Edit","Extensions","Help"]
        for menu in ordered:
            self.menuGadget[menu]=[]
            self.MenuSubBegin(menu)
            for item in self.MENU_ID[menu]:
                if item["name"] == "Recent Files":
                    self.MenuSubBegin(item["name"])
                    if self.mv.recentFiles.categories.has_key("Documents"):
                        for i,r in enumerate(self.mv.recentFiles.categories["Documents"]):
                            if r[1] == "readMolecule" :
                                self.MenuAddString(item["id"]*(i+2),r[0])
                    self.MenuSubEnd()
                else :
                    self.menuGadget[menu].append(self.MenuAddString(item["id"],item["name"]))#,self.buttonLoad)
            self.MenuSubEnd()
        self.MenuFinished()
        left, top, right, bottom =(10,10,10,1)#left, top, right, bottom
        #############################################################################
        #Hierarchy Options...TO DO
        #self.GroupBegin(id=0,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                         #                 cols=4, rows=1)
        #self.GroupBorderSpace(1, 1, 1, 1)
        #self.add_label(label="1. Make each atom a child of :",flags=c4d.BFH_LEFT)
        #self._defaultTree = self.AddCheckbox(flags=c4d.BFH_CENTER,label='Mol',width=60,default=True,event=self.setTree)
        #self._perResTree = self.AddCheckbox(flags=c4d.BFH_CENTER,label='Res',width=60,event=self.setTree)
        #self._perAtomTree = self.AddCheckbox(flags=c4d.BFH_CENTER,label='Atms',width=60,event=self.setTree)
        #self.GroupEnd()
        #############################################################################
        #Load Molecule
        self.GroupBegin(id=0,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                           cols=3, rows=1)
        self.GroupBorderSpace(left, top, right, bottom)
        self.AddButton(id=self.LOAD_BTN["id"], flags=c4d.BFH_LEFT | c4d.BFV_MASK,
                            initw=self.LOAD_BTN["width"],
                            inith=self.LOAD_BTN["height"],
                            name=self.LOAD_BTN["name"])
        self.add_label(self.LABEL_ID[0],flags=c4d.BFH_LEFT)
        self.add_label(self.LABEL_ID[1],flags=c4d.BFH_LEFT)
        self.GroupEnd()
        self.GroupBegin(id=1,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                           cols=3, rows=1)
        self.GroupBorderSpace(left, 1, right, bottom)

        self.file=self.AddEditText(id=self.EDIT_TEXT["id"],flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                            initw=120)
        self.SetString(self.file,'1crn')
        
        self._pdbtype=self.AddComboBox(id=self.COMB_BOX["pdbtype"]["id"],flags=c4d.BFH_LEFT,initw=56)
        map(lambda x,box=self._pdbtype:self.AddChild(box,x[0],x[1]),enumerate(self.pdbtype))
        self.AddButton(id=self.FETCH_BTN["id"], flags=c4d.BFH_LEFT | c4d.BFV_MASK,
                            initw=self.FETCH_BTN["width"],
                            inith=self.FETCH_BTN["height"],
                            name=self.FETCH_BTN["name"])
        self.GroupEnd()
        self.AddSeparatorH(200,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK)
        #############################################################################
        #DashBoard / Display Options
        self.GroupBegin(id=1,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                       cols=2, rows=1)
        self.GroupBorderSpace(left, top, right, bottom)                       
        #molecule menu
        self.add_label(self.LABEL_ID[2],flags=c4d.BFH_LEFT)
        self._box=self.AddComboBox(id=self.COMB_BOX["mol"]["id"],flags=c4d.BFH_SCALEFIT,initw=60)
        #self.add_label(self.LABEL_ID[1],flags=c4d.BFH_LEFT)
        
        #delete command
#        self.AddButton(id=self.DEL_BTN["id"], flags=c4d.BFH_SCALEFIT,
#                            initw=self.DEL_BTN["width"],
#                            inith=self.DEL_BTN["height"],
#                            name=self.DEL_BTN["name"])
        self.GroupEnd()
        self.GroupBegin(id=1,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                       cols=2, rows=1)
        self.GroupBorderSpace(left, top, right, bottom)                       
       
        #selection text area
        self.add_label(self.LABEL_ID[3],flags=c4d.BFH_LEFT)
        self._keywordtype=self.AddComboBox(id=self.COMB_BOX["keyword"]["id"],flags=c4d.BFH_LEFT,initw=80)
        map(lambda x,box=self._keywordtype:self.AddChild(box,x[0],x[1]),enumerate(self.keyword))
        #self.add_label(self.LABEL_ID[14],flags=c4d.BFH_LEFT)
        self.GroupEnd()
        self.GroupBegin(id=1,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                       cols=2, rows=1)
        self.GroupBorderSpace(left, 1, right, bottom)                       
        self.selection=self.AddEditText(id =self.SELEDIT_TEXT["id"],
                                        flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                                        initw=150)
        self.SetString(self.SELEDIT_TEXT["id"],
                       '(Mol:Ch:Rletter:Atom), eg "1CRN:A:ALA:CA", or keywords: BACKBONE, SIDECHAINS, etc...')
        
        self.AddComboBox(id=self.COMB_BOX["selection"]["id"],flags=c4d.BFH_LEFT,initw=80)
        map(lambda x,box=self.COMB_BOX["selection"]["id"]:self.AddChild(box,x[0],x[1]),
            enumerate(self.editselection))
        
        self.GroupEnd()
        self.GroupBegin(id=4,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                       cols=2, rows=1)
        self.GroupBorderSpace(left, 1, right, bottom)
        self.AddButton(id=self.SEL_BTN["deleteA"]["id"], flags=c4d.BFH_LEFT,
                        initw=self.SEL_BTN["deleteA"]["width"],
                        inith=self.SEL_BTN["deleteA"]["height"],
                        name=self.SEL_BTN["deleteA"]["name"]) 
        self.add_label(self.LABEL_ID[11],flags=c4d.BFH_SCALEFIT)
        self.GroupEnd()
        self.AddSeparatorH(200,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK)
        #############################################################################
        self.GroupBegin(id=2,flags=c4d.BFH_SCALEFIT,cols=2, rows=12)
        self.GroupBorderSpace(left, top, right, bottom)                       
        self.add_label(self.LABEL_ID[8],flags=c4d.BFH_LEFT)
        self._preset=self.AddComboBox(id=self.COMB_BOX["preset"]["id"],flags=c4d.BFH_SCALEFIT,initw=60)
        map(lambda x,box=self._preset:self.AddChild(box,x[0],x[1]),enumerate(self.presettype))
        self.GroupEnd()
        
        #the different representation and there options
        self.GroupBegin(id=2,flags=c4d.BFH_SCALEFIT,cols=3, rows=12)
        self.GroupBorderSpace(left, top, right, bottom)                       
       
        self.cpk=self.AddCheckbox(id=self.CHECKBOXS["cpk"]["id"],flags=c4d.BFH_SCALEFIT,
                                name=self.CHECKBOXS["cpk"]["name"],
                                initw=self.CHECKBOXS["cpk"]["width"],
                                inith=self.CHECKBOXS["cpk"]["height"])
        self.ss=self.AddCheckbox(id=self.CHECKBOXS["ss"]["id"],flags=c4d.BFH_SCALEFIT,
                                name=self.CHECKBOXS["ss"]["name"],
                                inith=self.CHECKBOXS["ss"]["height"],
                                initw=self.CHECKBOXS["ss"]["width"])
        self.surf=self.AddCheckbox(id=self.CHECKBOXS["surf"]["id"],flags=c4d.BFH_SCALEFIT,
                                name=self.CHECKBOXS["surf"]["name"],
                                inith=self.CHECKBOXS["surf"]["height"],
                                initw=self.CHECKBOXS["surf"]["width"])
      
        self.cpk_slider=self.AddEditSlider(id=self.SLIDERS["cpk"]["id"],
                                            flags=c4d.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["cpk"]["width"])
        self.SetReal(self.cpk_slider,1.00,0.,  10., 0.01)
        self.loft=self.AddCheckbox(id=self.CHECKBOXS["loft"]["id"],flags=c4d.BFH_SCALEFIT,
                                name=self.CHECKBOXS["loft"]["name"],
                                inith=self.CHECKBOXS["loft"]["height"],
                                initw=self.CHECKBOXS["loft"]["width"])
        self.msms_slider=self.AddEditSlider(id=self.SLIDERS["surf"]["id"],
                                            flags=c4d.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["surf"]["width"])
        self.SetReal(self.msms_slider,1.50,0.001,  19.99, 0.1)
        
        self.bs=self.AddCheckbox(id=self.CHECKBOXS["bs"]["id"],flags=c4d.BFH_SCALEFIT,
                                name=self.CHECKBOXS["bs"]["name"],
                                inith=self.CHECKBOXS["bs"]["height"],
                                initw=self.CHECKBOXS["bs"]["width"])
        self.armature=self.AddCheckbox(id=self.CHECKBOXS["arm"]["id"],flags=c4d.BFH_SCALEFIT,
                                name=self.CHECKBOXS["arm"]["name"],
                                inith=self.CHECKBOXS["arm"]["height"],
                                initw=self.CHECKBOXS["arm"]["width"])
        self.cms=self.AddCheckbox(id=self.CHECKBOXS["cms"]["id"],flags=c4d.BFH_SCALEFIT,
                                name=self.CHECKBOXS["cms"]["name"],
                                inith=self.CHECKBOXS["cms"]["height"],
                                initw=self.CHECKBOXS["cms"]["width"])
 
        self.bs_slider=self.AddEditSlider(id=self.SLIDERS["bs_s"]["id"],
                                            flags=c4d.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["bs_s"]["width"])
        self.SetReal(self.bs_slider,1.00,0.,  10., 0.01)
        self.spline=self.AddCheckbox(id=self.CHECKBOXS["spline"]["id"],flags=c4d.BFH_SCALEFIT,
                                name=self.CHECKBOXS["spline"]["name"],
                                inith=self.CHECKBOXS["spline"]["height"],
                                initw=self.CHECKBOXS["spline"]["width"])
        self.cms_slider=self.AddEditSlider(id=self.SLIDERS["cmsI"]["id"],
                                            flags=c4d.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["cmsI"]["width"])
        self.SetReal(self.cms_slider,7.10,0.001,  15., 0.1)
      
        self.bs_ratio=self.AddEditSlider(id=self.SLIDERS["bs_r"]["id"],
                                            flags=c4d.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["bs_r"]["width"])
        self.SetReal(self.bs_ratio,1.50,0.,  10., 0.01)
        self.meta=self.AddCheckbox(id=self.CHECKBOXS["meta"]["id"],flags=c4d.BFH_SCALEFIT,
                                name=self.CHECKBOXS["meta"]["name"],
                                inith=self.CHECKBOXS["meta"]["height"],
                                initw=self.CHECKBOXS["meta"]["width"])
        self.cms_res_slider=self.AddEditSlider(id=self.SLIDERS["cmsR"]["id"],
                                            flags=c4d.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["cmsR"]["width"])
        self.SetReal(self.cms_res_slider,-0.30,-20.,  -0.001, 0.01)
          
        self.GroupEnd()
        #color what is check as display        
        self.GroupBegin(id=3,flags=c4d.BFH_SCALEFIT,
                       cols=3, rows=12)
        self.GroupBorderSpace(left, top, right, bottom)                       
        self.add_label(self.LABEL_ID[4],flags=c4d.BFH_LEFT)
        self._color=self.AddComboBox(id=self.COMB_BOX["col"]["id"],flags=c4d.BFH_SCALEFIT,initw=206)
        self.AddChild(self._color,0,'Atoms using CPK')        #2018
        self.AddChild(self._color,1,'AtomsDG (polarity/charge)')        #2019
        self.AddChild(self._color,2,'Per residue')      #2020  
        self.AddChild(self._color,3,'Secondary Structure')      #2021?
        self.AddChild(self._color,4,'Custom color')      #2022?
        self.AddChild(self._color,5,'Rainbow from N to C')     #2022?
        self.AddChild(self._color,6,'Chains')     #2022?
        self.AddChild(self._color,7,'Temperature Factor')     #2022?
        self.AddChild(self._color,8,'sas area')
        self.unic_color=self.AddColorField(id=self.COLFIELD["id"],flags=c4d.BFH_LEFT, 
                                     initw=30,inith=15)

        self.GroupEnd()
        self.AddSeparatorH(200,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK)
        #############################################################################
        self.GroupBegin(id=4,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                       cols=3, rows=1)
        self.GroupBorderSpace(left, top, right, bottom)
        self.AddButton(id=self.DATA_BTN["id"], flags=c4d.BFH_LEFT | c4d.BFV_MASK,
                    initw=self.DATA_BTN["width"],
                    inith=self.DATA_BTN["height"],
                    name=self.DATA_BTN["name"])
        self.add_label(self.LABEL_ID[5],flags=c4d.BFH_LEFT)
        self._datatype=self.AddComboBox(id=self.COMB_BOX["datatype"]["id"],flags=c4d.BFH_LEFT,initw=80)
        map(lambda x,box=self._datatype:self.AddChild(box,x[0],x[1]),enumerate(self.datatype))
#        self.trajectoryfile=self.AddEditText(id=self.DATA_TEXT["id"],flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK)
#        self.AddButton(id=self.DATA_BTN["id"], flags=c4d.BFH_LEFT | c4d.BFV_MASK,
#                            initw=self.DATA_BTN["width"],
#                            inith=self.DATA_BTN["height"],
#                            name=self.DATA_BTN["name"])
        self.GroupEnd()
        #self.AddSeparatorH(200,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK)
        #############################################################################
        self.GroupBegin(id=4,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                       cols=3, rows=1)
        self.GroupBorderSpace(left, top, right, bottom)
        self.add_label(self.LABEL_ID[9],flags=c4d.BFH_LEFT)
        self.trajbox=self.AddComboBox(id=self.COMB_BOX["dat"]["id"],flags=c4d.BFH_LEFT,initw=60)
        self.add_label(self.LABEL_ID[6],flags=c4d.BFH_SCALEFIT)
        self.GroupEnd()
        self.GroupBegin(id=4,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK,
                       cols=1, rows=1)
        self.GroupBorderSpace(left, 1, right, bottom)        
        self.slider=self.AddEditSlider(id=self.SLIDERS["datS"]["id"],
                                            flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK, 
                                            initw=self.SLIDERS["datS"]["width"])
        #self.dataVal = self.AddEditNumberArrows(id=self.SLIDERS["datV"]["id"], 
        #                                        flags=c4d.BFH_LEFT, initw=100)
        #self.SetLong(self.slider,0,0,1000,1)                                        
        #self.SetReal(self.dataVal,0.,-300.,300.,0.01)
#        self.AddButton(id=self.KEY_BTN["id"], flags=c4d.BFH_LEFT | c4d.BFV_MASK,
#                            initw=self.KEY_BTN["width"],
#                            inith=self.KEY_BTN["height"],
#                            name=self.KEY_BTN["name"])
        self.GroupEnd()
        self.AddSeparatorH(200,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK)
        #############################################################################

        self.GroupBegin(id=5,flags=c4d.BFH_SCALEFIT,
                       cols=3, rows=10)
        self.GroupBorderSpace(left, top, right, bottom)                       
        self.add_label(self.LABEL_ID[7],flags=c4d.BFH_LEFT)
        
        self.AddComboBox(id=self.COMB_BOX["scriptO"]["id"],flags=c4d.BFH_LEFT,initw=56)
        map(lambda x,box=self.COMB_BOX["scriptO"]["id"]:self.AddChild(box,x[0],x[1]),enumerate(self.scriptliste))

        self.AddComboBox(id=self.COMB_BOX["scriptS"]["id"],flags=c4d.BFH_LEFT,initw=56)
        map(lambda x,box=self.COMB_BOX["scriptS"]["id"]:self.AddChild(box,x[0],x[1]),enumerate(self.scriptsave))

        self.GroupEnd()
        
        self.GroupBegin(id=5,flags=c4d.BFH_SCALEFIT|c4d.BFV_SCALEFIT,
                       cols=1, rows=10)
        self.GroupBorderSpace(left, 5, right, bottom)                
        
        #self.add_label(label="the molecular viewer is also available in the sandbox (import c4d;c4d.mv;)")
        self.pmvcmds=self.AddMultiLineEditText(id=6,flags=c4d.BFH_SCALEFIT|c4d.BFV_SCALEFIT, 
                                     initw=100, style=c4d.DR_MULTILINE_SYNTAXCOLOR)
        self.SetString(self.pmvcmds,
        """
        
print 'put your own commands here'
print 'with self = PMV instance, and epmv as ePMV'
        """)
        self.AddButton(self.PMV_BTN["id"],flags=c4d.BFH_SCALEFIT,
                       name=self.PMV_BTN["name"],initw=80)
        #no banner but we can put the label version
        self.AddStaticText(7,flags=c4d.BFH_LEFT)
        self.SetString(7,'welcome to ePMV '+__version__)
        self.GroupEnd()
        
        self.AddSeparatorH(200	,flags=c4d.BFH_SCALEFIT | c4d.BFV_MASK)
        #use instead StatusSetBar
        #banner
        self.bannerFile = MGL_ROOT+'/MGLToolsPckgs/Pmv/hostappInterface/banner.jpg'
        self.bannerBMP = bitmaps.BaseBitmap()
        self.bannerBMP.InitWith(self.bannerFile)
        self.bannerBC = c4d.BaseContainer()
        
#        #dont work
#        self.area = c4d.gui.GeUserArea()        
#        self.AddUserArea(10,flags=c4d.BFH_SCALEFIT,initw=100, inith=150)
#        self.AttachUserArea(self.area, id=10, userareaflags=c4d.USERAREA_COREMESSAGE)
#        self.area.DrawBitmap(self.bannerBMP, 0, 0, 396, 60, 0, 0, 396, 60, mode=c4d.BMP_NORMALSCALED)#396 × 60
#        self.area.DrawText('welcome to ePMV '+__version__, 0, 0, flags=c4d.DRAWTEXT_STD_ALIGN)
#        self.area.Init()
#        self.area.InitValues()
        
        #self.banner = self.AddImage(self.bannerBMP, flags=c4d.BFH_CENTER,  
        #                             width=self.bannerBMP.get_width(), 
        #                             height=self.bannerBMP.get_height())
        

        self.pd.epmv = self.epmv
        self.argui.epmv = self.epmv
        self.options.epmv = self.epmv
        self.ad.epmv = self.epmv
        if self.restored :
            #self.set_up()
            for mol in self.mv.Mols:
                print "restore ",mol.name
                self.buttonLoad(None,mname=mol.name)
                self.firstmol = False
                #need to restore the data
                for dataname in self.mv.iMolData[mol.name] :
                    print "dataname ",dataname               
                    self.buttonLoadData(None,trajname=dataname,molname=mol.name)              
                #need to restore the selection
                if mol.name in self.mv.MolSelection.keys():
                    self.add_Selection(n=mol.name)
                #for selname in self.mv.MolSelection[mol.name].keys() :
                #    self.addChildToMolMenu(selname)
            self.restored = False                                
        return True
        
    def add_label(self,label,flags=None):
        self.AddStaticText(label["id"],flags)
        self.SetString(label["id"],label["label"])

    def timeFunction(self,function):
        t1=time()
        function()
        print "time ", time()-t1
    
    def save_ePMVScript(self):
        commands=self.GetString(self.pmvcmds)
        from Pmv.hostappInterface import demo
        dir = demo.__path__[0]
        ids = self.GetLong(self.COMB_BOX['scriptS']['id'])
        #fix Me open dialog to save.
        if ids == 0 : #Save
            filename = dir+'/'+self.scriptliste[ids]+'.py'
        else : #save as
            filename = c4d.storage.SaveDialog(c4d.FSTYPE_ANYTHING, "Save python file as")
        f = open(filename,'w')
        f.write(commands)
        f.close()
        
    def set_ePMVScript(self):
        from Pmv.hostappInterface import demo
        dir = demo.__path__[0]
        ids = self.GetLong(self.COMB_BOX['scriptO']['id'])
        filename = None
        if ids == 0 : #Open..ask for broser
            filename = c4d.storage.LoadDialog(c4d.FSTYPE_ANYTHING, "Open python file")
        else :
            filename = dir+'/'+self.scriptliste[ids]+'.py'
        if filename :
            f = open(filename,'r')
            script = f.read()
            f.close()
            self.SetString(self.pmvcmds,script)
        
    def execPmvComds(self):
        cmds=self.GetString(self.pmvcmds)
        print len(cmds),cmds
        exec(cmds,{'self':self.mv,'epmv':self.epmv,'c4d':c4d})   
        self.updateViewer()
        return True

    def check_update(self):
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
                res = c4d.gui.QuestionDialog("A update is available did you want to proceed\ncurrent version:"+__version__+" new version:"+cv+"\n")
                if res : 
                    self.epmv_update(note=note)
        else :
            c4d.gui.MessageDialog("problem with Internet!")
        
    def epmv_update(self,note=None):
        #try to update ePMV
        if self.inst is None :
            self.inst=Installer(gui=False)
            self.inst.mgltoolsDir=MGL_ROOT
            self.inst.currDir=MGL_ROOT+os.sep+"MGLToolsPckgs"+os.sep+"Pmv"+os.sep+"hostappInterface"
        #first check if the file exist
        import os.path
        if not os.path.exists(self.inst.currDir+os.sep+'epmv_dir.txt'):
            c4d_dir = c4d.storage.GeGetStartupPath().replace(" ","\ ")
            f=open(self.inst.currDir+'/epmv_dir.txt','w')
            f.write("Cinema4DR12:"+c4d_dir)
            f.close()
        self.inst.getDirFromFile()
        self.inst.updateCVS()
        try:
            self.inst.installC4dr12(update=True)
            #need a popup to says to restart
            c4d.gui.MessageDialog("SUCCESS!\nYou need to restart now!")
            return True
        except:
            c4d.gui.MessageDialog("OUPS no update done!")
        
    def uncheckMenu(self,gadget,check,name):
        if check:
            self.SetString(gadget["id"],name + "&c&")
            gadget["name"] = name + "&c&"
        else :
            self.SetString(gadget["id"],name + "&c&")
            gadget["name"] = name

    def deleteChildrens(self,o):
        #print o.GetName()
        if hasattr(o,'GetChilds'):
            childs = o.GetChilds()
            if childs is not None:
                for ch in childs:
                    self.deleteChildrens(ch)
            else :
                self.epmv.helper.deleteObject(o)
        else :
            child = o.GetDown()
            if child is not None: 
                self.deleteChildrens(child)
            else :
                self.epmv.helper.deleteObject(o)
        self.epmv.helper.deleteObject(o)
                
    def delMolDic(self,molname):
        del self.mv.selections[molname]
        del self.mv.iMolData[molname]
        del self.mv.molDispl[molname]
        del self.mv.MolSelection[molname]
    
    def delGeomMol(self,mol):
        #put in the helper
        #scene.unlink
        #first go throught the geom and del all attribute / unlink all obj
        #get the master
        master = mol.geomContainer.masterGeom.obj
        self.deleteChildrens(master)
            
    def deleteMol(self,mol=None):
        val = self.GetLong(self._box)
        if mol is None :
            mname,mol=self.getMolName()
        else :
            mname = mol.name
        if mname in self.mv.Mols.name :
            #need to first delete the geom and the associates dictionary
            #note the mesh are still in the memory ....
            self.delMolDic(mname)
            self.delGeomMol(mol)
            #then delete the mol
            self.mv.deleteMol(mol, log=0)
            #delete the entry in the menuBox
            self.FreeChildren(self._box, val)


    def getData(self,molname,adt=False,restore=False):
        if not restore:
            if molname in self.mv.Mols.name : self.mv.hostApp.driver.duplicatemol=False
            self.mv.assignAtomsRadii(molname, united=0, log=0, overwrite=1)
            print "Load ",molname,(self.GetLong(self._box))
            self.dash=True
        if self.firstmol :
            self.mv.iMol[str(self.indice_mol)]=molname
            self.AddChild(self._box,self.indice_mol,molname)#self.mv.Mols[-1].name)
            self.SetLong(self._box, int(self.indice_mol))
            self.indice_mol +=1         
            self.firstmol=False
        else :
            print "new mol ",molname
            self.AddChild(self._box,int(self.indice_mol),molname)#self.mv.Mols[-1].name)
            self.mv.iMol[str(self.indice_mol)]=molname
            self.SetLong(self._box, int(self.indice_mol))
            self.indice_mol+=1
        self.epmv._addMolecule(molname)
        #test if multimodel
        if not restore:
            mol = self.mv.getMolFromName(molname)
            if len(mol.allAtoms[0]._coords) > 1 or self._useModeller : 
                #need a test about trajectories...
                doit=True           
                if len(self.mv.iMolData[mol.name]) != 0 : #ok data
                    for dataname in self.mv.iMolData[mol.name] : 
                        if dataname.find('xtc') != -1 : 
                            doit= False                             
                if doit : self.buttonLoadData(model=True,adt=adt)
      
    def buttonBrowse(self,file=None):
        adt=False
        if file is None :
            name = c4d.storage.LoadDialog(c4d.FSTYPE_ANYTHING, "choose a file")#, flags=0][, def_path])
        else :
            name = file
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
                name,mdl = setupMDL(self.env,name)
            if not adt :
                self.mv.readMolecule(name,log=1)
                if self._useModeller :
                    self.mv.Mols[-1].mdl=mdl
            molname = self.mv.Mols[-1].name
        else :
            #dialog ?
            return True
        self.getData(molname,adt=adt)
        self.updateViewer()
        self.current_mol = self.mv.Mols[-1]
        return True
        
    def buttonLoad(self,filename=None,mname=None):
        print "buttonLoad", mname
        if mname is None:
            name= self.GetString(self.EDIT_TEXT["id"])
            if len(name) == 0:
                self.buttonBrowse()
            else :    
                if len(name) == 4 or len(name.split(".")[0]) == 4 : #PDB CODE =>web download
                    molname=name.split(".")[0]
                    if molname in self.mv.Mols.name : self.mv.hostApp.driver.duplicatemol=True
                    #what is the selected pdbtype:
                    type = self.pdbtype[self.GetLong(self._pdbtype)]
                    self.mv.fetch.db = type
                    #print self.mv.fetch.db
                    mol = self.mv.fetch(name, f=self._forceFetch)
                    #I can probably set up modeller, by deleting/reloading the molecule..
                    if mol is None :
                        return True
                    self.getData(self.mv.Mols[-1].name)
                    self.updateViewer()
                    self.current_mol = mol
                    return True
                else :  
                    self.buttonBrowse(name)
                    self.current_mol = self.mv.Mols[-1]
                    return True
        else : #restore case
            self.getData(mname,restore=True)
        return True
        
    ##########################DATA COMMAND######################################
    def modelData(self,dataname=None,molname=None,adt=False):
        if molname == None :
            mname,mol=self.getMolName()
            trajname = mname+'.model'
            if adt:
                trajname = mname+'.dlg'
            self.mv.iMolData[mname].append(trajname)
        else :
            mname = molname
            trajname = dataname                         
        if self.firsttraj:
            self.AddChild(self.trajbox,0,trajname)
            self.SetLong(self.trajbox, 0)
            self.mv.iTraj[self.indiceData]=[trajname,"model"]
            #self.set(self.trajbox, int(self.idata))
            #self.mv.iTraj[self.idata]=self.mv.Trajectories[trajname]
            self.firsttraj=False
            self.current_traj=[trajname,"model"]
            self.indiceData += 1
            #self.nF=len(self.current_traj.coords)
        else :
            self.AddChild(self.trajbox,self.indiceData,trajname)
            self.SetLong(self.trajbox, self.indiceData)
            #nTraj=len(self.mv.Trajectories.keys())
            #self.mv.iTraj[self.idata+nTraj-1]=self.mv.Trajectories[trajname]
            self.mv.iTraj[self.indiceData]=[trajname,"model"]
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
        if self.firsttraj:
            self.AddChild(self.trajbox,0,trajname)#first traj is 2040
            self.SetLong(self.trajbox, 0)
            self.mv.iTraj[0]=[self.mv.Trajectories[trajname],"traj"]
            #self.set(self.trajbox, int(self.idata))
            #self.mv.iTraj[self.idata]=self.mv.Trajectories[trajname]
            self.firsttraj=False
            self.current_traj=[self.mv.Trajectories[trajname],"traj"]
            self.nF=len(self.current_traj[0].coords)
            self.indiceData += 1
        else :
            self.add_child(self.trajbox,self.indiceData,trajname)#first traj is 2040
            self.SetLong(self.trajbox,self.indiceData)
            nTraj=len(self.mv.Trajectories.keys())
            #self.mv.iTraj[self.idata+nTraj-1]=self.mv.Trajectories[trajname]
            self.mv.iTraj[self.indiceData]=[self.mv.Trajectories[trajname],"traj"]
            self.indiceData += 1
            
    def amberTraj(self,filename):
       pass
       """trajname=os.path.basename(filename)
       print trajname
       mname,mol=self.getMolName()   
       self.mv.setup_Amber94(mname+":",'traj_'+mname,filename=None)    
       self.mv.setmdOpts_Amber94('traj_'+mname, tautp=0.2, log=0, zerov=0, tempi=0.0, verbosemd=1, idum=-1, temp0=300.0, t=0.0, ntpr_md=10, dt=0.001, ntwx=300, vlimit=10.0)
       #self.mv.md_Amber94('traj_'+mname, 349, callback=1, filename=filename, log=0, callback_freq=10)
       self.mv.play_md_trj_Amber94('traj_'+mname, filename, log=0)

       if self.firsttraj:
           self.add_child(self.trajbox,trajname)#first traj is 2040
           self.set(self.trajbox, int(2045))
           self.iTraj[2045]=self.mv.Trajectories[trajname]
           self.firsttraj=False
           self.current_traj=self.mv.Trajectories[trajname]
           self.nF=len(self.current_traj.coords)
       else :
           self.add_child(self.trajbox,trajname)#first traj is 2040
           nTraj=len(self.mv.Trajectories.keys())
           self.iTraj[2045+nTraj-1]=self.mv.Trajectories[trajname]"""

    def gridData_2(self,file=None,dataname=None,molname=None):
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
        if self.firsttraj:
            self.AddChild(self.trajbox,0,os.path.basename(trajname))#first traj is 2040
            self.SetLong(self.trajbox,0)
            self.indiceData += 1
            self.mv.iTraj[0]=[self.mv.grids3D[trajname],"grid"]
            #self.set(self.trajbox, int(self.idata))
            #self.mv.iTraj[self.idata]=self.mv.grids[trajname]
            self.firsttraj=False
            self.current_traj=[self.mv.grids3D[trajname],"grid"]
            self.nF=self.current_traj[0].maxi
        else :
            self.AddChild(self.trajbox,self.indiceData,os.path.basename(trajname))
            self.SetLong(self.trajbox, int(self.indiceData))        
            nTraj=len(self.mv.grids3D.keys())
            self.mv.iTraj[self.indiceData]=[self.mv.grids3D[trajname],"grid"]
            self.indiceData += 1   
            #self.mv.iTraj[self.idata+nTraj-1]=self.mv.grids[trajname]

    def buttonLoadData(self,model=False,trajname=None,molname=None,adt=False):
        if trajname == None :
            if model : 
                self.modelData(adt=adt)
                return True
            #filename=self.GetString(self.trajectoryfile)
            #if len(filename) == 0 :
            filename = c4d.storage.LoadDialog(c4d.FSTYPE_ANYTHING, 
                                                  "choose a file (.xct,.mrc,...)")
            if filename is None :
                    return True
            #else :
            extension=os.path.splitext(os.path.basename(filename))[1] #.xtc,.trj,etc..
            if extension == '.xtc' or extension == '.dcd'  : self.gromacsTraj(file=filename)
            else : self.gridData_2(file=filename)
            #elif extension == '.map' : self.gridData_1(file=filename)
        else :
           print "restore ",trajname      
           if trajname.find(".model") != -1 or trajname.find(".dlg") != -1: #model conformation data
               self.modelData(dataname=trajname,molname=molname)          
           elif trajname.find("xtc") != -1 : #gromacs conformation data
               self.gromacsTraj(dataname=trajname,molname=molname)          
           else : #autodock map conformation data
               self.gridData_2(dataname=trajname,molname=molname)          
        #elif extension == '.trj' : self.amberTraj(filename)
        self.updateViewer()
        return True

    def updateTraj(self):
        traji=self.GetLong(self.trajbox)
        #print traji,self.mv.iTraj
        self.current_traj=self.mv.iTraj[traji]#[0]
        type = self.mv.iTraj[traji][1]
        print "type",type
        if type == "model":
            mname = self.current_traj[0].split(".")[0]
            type = self.current_traj[0].split(".")[1]
#            print mname,type
            mol = self.mv.getMolFromName(mname)
            if type == 'model':
                nmodels=len(mol.allAtoms[0]._coords)
            else :
                nmodels=len(mol.docking.ch.conformations)
            mini=0
            maxi=nmodels
            default=0
            step=1
            doit=self.SetLong
        elif type == "traj":
            mini=0
            maxi=len(self.current_traj[0].coords)
            default=0
            step=1
            doit=self.SetLong
        elif type == "grid":
            mini=self.current_traj[0].mini
            maxi=self.current_traj[0].maxi
            default=self.current_traj[0].mean
            step=0.01
            doit=self.SetReal
        print self.slider,default,mini,maxi,step
        doit(self.slider,default,mini,maxi,step)    
        self.updateViewer()
        return True

    def applyState(self):
        #frame=self.GetLong(self.slider)
        #print frame,self.current_traj
        traj = self.current_traj
        mname,mol=self.getMolName()
        if traj[0] is not None : 
            if traj[1] in ["model" ,"traj"]:
                conf = self.GetLong(self.slider)
                self.epmv.helper.updateData(self.epmv,traj,conf)
                if self.mv.molDispl[mname][3] : self.updateSurf()
                if self.mv.molDispl[mname][4] : self.updateCoarseMS()
            elif traj[1] == "grid":
                #grid3D
                iso=self.GetReal(self.slider)
                self.mv.isoC(traj[0],isovalue=iso,name=mname+"IsoSurface")       
            elif hasattr(traj[0],'GRID_DATA_FILE'):
                #grid
                iso=self.GetReal(self.slider)
                self.mv.setIsovalue(traj[0].name,iso, log = 1)          
        self.updateViewer()
        return True

    def updateViewer(self):
        c4d.EventAdd()
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW|c4d.DRAWFLAGS_NO_THREAD|c4d.DRAWFLAGS_NO_ANIMATION)          
        c4d.GeSyncMessage(c4d.EVMSG_TIMECHANGED)
        

    def drawPreset(self):
        mname,mol=self.getMolName(forupdate=True)
        sel=self.getSelectionLevel(mol)
        selection = self.mv.select(sel,negate=False, only=True, xor=False, 
                                   log=0, intersect=False)        
#        self.presettype=['available presets:','  Lines','  Liccorice','  SpaceFilling',
#                         '  Ball+Sticks','  RibbonProtein+StickLigand',
#                         '  RibbonProtein+CPKligand','  xray','  Custom',
#                         '  Save Custom As...']
        #load,edit save representation preset
        preset=self.presettype[self.GetLong(self._preset)]
        print preset
        if preset.strip() == 'Liccorice':
            #displayBS as licorice which is simply ratio == 1.0
                #set the ratio and do the command
            self.SetReal(self.bs_ratio,1.0)
            self.SetBool(self.bs,True)
            self.displayBS()
        elif preset.strip() == 'RibbonProtein+StickLigand':
            #need 1 or 2 molecules...like whats prot and whats ligand
            #lets ask for it ? with some proposition
            pass
        elif preset.strip() == 'xray':
            #??
            pass
        elif preset.strip() == 'Lines':
            self.mv.displayLines(selection)
        #should we use the styleCommand?

    def update(self):  
        mname,mol=self.getMolName(forupdate=True)
        if mol == None : return True    
        #print "update ",mname,self.mv.molDispl[mname]
        self.SetBool(self.cpk,self.mv.molDispl[mname][0])
        self.SetBool(self.bs,self.mv.molDispl[mname][1])
        self.SetBool(self.ss,self.mv.molDispl[mname][2])
        self.SetBool(self.surf,self.mv.molDispl[mname][3])
        self.SetBool(self.cms,self.mv.molDispl[mname][4])
        if self.mv.molDispl[mname][5] != None : 
           #indice of func col used 
           #print self.molDispl[mname][5],self.molDispl[mname][5]+2019
           self.SetLong(self._color,self.mv.molDispl[mname][5])
        if self.mv.molDispl[mname][6] != None :
           #the unic color 
           color=self.mv.molDispl[mname][6]      
           self.SetColorField(self.unic_color,color,1.0,1.0,0)
        if mname not in self.mv.Mols.name:
           #print mname,self.mv.MolSelection[mname.split("_")[0]][mname]
           self.SetString(self.selection,self.mv.MolSelection[mol.name][mname])
           if True in self.mv.molDispl[mname]: self.doDisplaySelection(self.mv.molDispl[mname])
        else : 
           self.SetString(self.selection,"")
           #if True in self.molDispl[mname]: self.doDisplaySelection(self.molDispl[mname],private)"""
        #print "update"
        #should apply the ds...or not ? lets try
        self.current_mol = mol
        self.updateViewer()
        return True

    def doDisplaySelection(self,disArray):
        if disArray[0] : self.displayCPK()  
        if disArray[1] : self.displayBS()
        if disArray[2] : self.displaySS()
        if disArray[3] : self.displaySurf()
        if disArray[4] : self.displayCoarseMS()
        if disArray[5] != None : self.color()       

    def edit_Selection(self):
        edit = self.GetLong(self.COMB_BOX['selection']['id'])
        if edit == 0 : #add selection
            self.add_Selection()
        elif edit == 1 : #rename
            self.rename_Selection()
        elif edit == 2 :
            self.delete_Selection()

    def delete_Atom_Selection(self):
        #self.mv.deleteAtomSet...
        mname,mol=self.getMolName()
        sel=self.getSelectionLevel(mol)
#        print sel,mname, mol
        if sel is mol.name :
            print sel,mname, mol , "del"
            res = c4d.gui.QuestionDialog("Are You sure you want to delete "+mol.name)
            if res : 
                self.deleteMol()
        else :
            selection = self.mv.select(sel,negate=False, only=True, xor=False, 
                                   log=0, intersect=False)
#            print len(selection),selection
            if not isinstance(selection,Atom) : 
               selection = selection.findType(Atom)
            res = c4d.gui.QuestionDialog("Are You sure you want to delete the atoms of the current selection "+sel)
            if res : 
                self.mv.deleteAtomSet(selection)

    def restoreMolMenu(self):
        #call this after flushing the combo box
        for ind in self.mv.iMol.keys():
            self.AddChild(self._box,int(ind),self.mv.iMol[ind])
            for selname in self.mv.selections[self.mv.iMol[ind]].keys():
                #find indice
                for inds in self.mv.iSel.keys():
                    if self.mv.iSel[inds] == selname :
                        self.AddChild(self._box,int(inds),self.mv.iSel[inds])
        
    def delete_Selection(self):
        val = self.GetLong(self._box)
        selname,mol=self.getMolName(forupdate=True)
        res = c4d.gui.QuestionDialog("Are You sure you want to delete the current selection "+selname)
        mname = mol.name
        if res :
            del self.mv.MolSelection[mname][selname]
            del self.mv.selections[mname][selname]
            del self.mv.molDispl[selname]
            self.FreeChildren(self._box)
            self.restoreMolMenu()
            
    def rename_Selection(self):
        #whats the new name
        newname=c4d.gui.InputDialog("Enter the new name for the current selection\n",
        "mySelection1")
        #get current selection name
        val = self.GetLong(self._box)
        selname,mol=self.getMolName(forupdate=True)
        mname = mol.name
        #change the name in dic of indice
        self.mv.iSel[str(val)] = newname
        #change the name in the mol dictionary of selection
        sel = self.mv.MolSelection[mname][selname]
        dsDic = self.mv.molDispl[selname]
        del self.mv.MolSelection[mname][selname]
        del self.mv.selections[mname][selname]
        del self.mv.molDispl[selname]
        
        
        self.mv.MolSelection[mname][newname]=sel
        self.mv.selections[mname][newname]=sel
        self.mv.molDispl[newname]=dsDic
        self.FreeChildren(self._box)      
        self.restoreMolMenu()

    def add_Selection(self,n=None):
        print "add_selection"
        if n is not None:
            for selname in self.mv.MolSelection[n].keys():
                self.AddChild(self._box,self.indice_mol,selname)
                self.mv.iSel[str(self.indice_mol)]=selname
                self.indice_mol+=1               
            return True
        mname,mol=self.getMolName()   
        sel=self.getSelectionLevel(mol)       
        print mname
        print sel       
        selname=mname+"_Selection"+str(len(self.mv.MolSelection[mname]))
        print selname
        self.mv.MolSelection[mname][selname]=sel
        self.mv.selections[mname][selname]=sel
        self.mv.molDispl[selname]=[self.GetBool(self.cpk),self.GetBool(self.bs),
                                   self.GetBool(self.ss),self.GetBool(self.surf),
                                   self.GetBool(self.cms),
                                   self.GetLong(self._color),
                                   self.GetColorField(self.unic_color)['color']]
        self.AddChild(self._box,self.indice_mol,selname)
        #print str(self.indice_mol+self.indice)       
        self.mv.iSel[str(self.indice_mol)]=selname
        self.indice_mol+=1
        return True       

    def getSelectionName(self,sel,mol):
        for selname in self.mv.MolSelection[mol.name].keys() : 
            if sel == self.mv.MolSelection[mol.name][selname] : return selname           
        return mol.name+"_Selection"+str(len(self.mv.MolSelection[mol.name]))
    
    def sortName(self,array):
        stringselection=""
        for element in array:
            if ":" in element :
                stringselection+=element+";"
            else : return element
        return stringselection 

    def setKeywordSel(self):
        key=self.keyword[self.GetLong(self._keywordtype)]
        if key == 'keywords' : key = ""
        self.SetString(self.selection,key.replace(" ",""))

    def getSelectionLevel(self,mol):
        #fix...problem if multiple chain...
        #R=mol.chains[0].residues
        if mol == None : sel = ''
        else : sel=mol.name
        selection=self.GetString(self.selection)
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
            #need to get the current object selected in the doc
            #and parse their name to recognize the atom selection...do we define a picking level ? and some phantom object to be picked?                  
            CurrSel=self.epmv.helper.getCurrentScene().GetSelection()
            astr=[]
            for o in CurrSel : 
                #print o.get_name()#,o.get_type()
                astr.append(self.epmv.helper.parseObjectName(o))
            sel=self.sortName(astr)
            print "parsed selection ",sel
            #sel=mol.name
        return sel

    def getMolName(self,forupdate=False):
        val = self.GetLong(self._box)
#        print "get ",val
        selname=""
        mname=""
        #print self.mv.iMol.keys()       
        if str(val) in self.mv.iMol.keys(): 
            selname=mname=self.mv.iMol[str(val)]
        elif str(val) in self.mv.iSel.keys() : #it is the selecetionname
            selname=self.mv.iSel[str(val)]
            mname=""
            for mname in self.mv.MolSelection.keys():
                for sname in self.mv.MolSelection[mname].keys():
                    if selname == sname :
                        break
            if mname=="":
                return selname,None
        else : return "",None   
        mol=self.mv.getMolFromName(mname)
#        print mol.name
        if forupdate: return selname,mol   
        return mname,mol


    #######DISPLAY COMMAND######################################################
    def displayMetaB(self):
        print "displayMetaB"
        #create metaballs from clouds /perchains or permolecule ?
        #_perMol option 
        _perMol = True 
        mname,mol=self.getMolName()
        sel=self.getSelectionLevel(mol)
        selection = self.mv.select(sel,negate=False, only=True, xor=False, 
                                   log=0, intersect=False)
        doc=c4d.documents.GetActiveDocument()
        display = self.GetBool(self.CHECKBOXS["meta"]["id"])
        if _perMol :
            parent  = mol.geomContainer.masterGeom.obj
            #find the metaball
            metab = self.epmv.helper.getObject(mol.name+"_metab")
            if metab is None :
                #create the metabll object
                self.epmv.helper.create_metaballs(mol.name,source="clouds",
                                                  parent=parent,
                                                    coords=mol.allAtoms.coords)
            #visibility
            self.epmv.helper.toggleDisplay(metab,display)   
        else : #perChains
            parents  = mol.geomContainer.masterGeom.chains_obj #one foreach chain
            for i,ch in enumerate(mol.chains):
                pass
        self.updateViewer()
        return True

    def displayCPK(self):
        #c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        mname,mol=self.getMolName()
        if VERBOSE : print "CPK", mname
        scale = self.GetReal(self.cpk_slider)   
        self.mv.hostApp.driver.use_instances=True
        sel=self.getSelectionLevel(mol)
        if VERBOSE : print "select ",sel
        selection = self.mv.select(sel,negate=False, only=True, xor=False, 
                                   log=0, intersect=False)
        if VERBOSE : print len(selection)
        if not isinstance(selection,Atom) : selection = selection.findType(Atom)
        maxi = len(selection)
        
        if maxi < 100 : 
            quality=5
        elif maxi < 500:
            quality=0
        elif maxi < 1000 :
            quality = 4
        else :
            quality =1
            
        self.mv.displayCPK(sel,log=1,negate=(not self.GetBool(self.cpk)),
                                             scaleFactor = float(scale))
        #self.bc[gui.BFM_STATUSBAR_PROGRESSON] = False
        self.updateViewer()
        self.mv.molDispl[mname][0]=self.GetBool(self.cpk)
        #c4d.gui.SetMousePointer(c4d.MOUSE_NORMAL)
        return True

    def displayBS(self):
        if VERBOSE : print "displayBS"
        #c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        mname,mol=self.getMolName()   
        sel=self.getSelectionLevel(mol) 
        scale = self.GetReal(self.bs_slider)
        ratio = self.GetReal(self.bs_ratio)
        cradius = 0.3/ratio
        self.mv.hostApp.driver.use_instances=True#self.get(self.instance)       
        #print "self.displaySticksAndBalls('"+sel+"',log=1,negate=",(not self.get(self.bs)),")" 
        #print cradius*scale,scale,ratio
        self.mv.displaySticksAndBalls(sel, log=1, cquality=0, sticksBallsLicorice='Sticks and Balls', 
									bquality=0, cradius=cradius*scale, only=False, bRad=0.3, 
									negate=(not self.GetBool(self.bs)), bScale=scale)
        #self.mv.colorByAtomType(sel, ['balls','sticks'], log=1)
        self.updateViewer()
        self.mv.molDispl[mname][1]=self.GetBool(self.bs)
        #c4d.gui.SetMousePointer(c4d.MOUSE_NORMAL)
        #c4d.draw_views(c4d.DA_ONLY_ACTIVE_VIEW|c4d.DA_NO_THREAD|c4d.DA_NO_ANIMATION)
        return True

    def displaySS(self):
        #pass
        #c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        mname,mol=self.getMolName()
        sel=self.getSelectionLevel(mol)      
        self.mv.displayExtrudedSS(sel, negate=(not self.GetBool(self.ss)), 
                                    only=False, log=1)
        self.updateViewer()
        self.mv.molDispl[mname][2]=self.GetBool(self.ss)
        #c4d.gui.SetMousePointer(c4d.MOUSE_NORMAL)
        return True
        
    def updateSurf(self):
        #pass
        #c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
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
        pRadius = self.GetReal(self.msms_slider)
        if name in mol.geomContainer.geoms :
            self.mv.computeMSMS(sel, log=1, display=self.GetBool(self.surf), 
                               pRadius=pRadius, perMol=permol,surfName=name)
            #need to MenuAddString the color function#should we update the color ?
            #self.color(None,[name,])                     
            self.updateViewer()
            self.mv.molDispl[mname][3]=self.GetBool(self.surf)
        #c4d.gui.SetMousePointer(c4d.MOUSE_NORMAL)
        return True
    
    def displaySurf(self):
        #c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        mname,mol=self.getMolName()
        name='MSMS-MOL'+str(mol.name)
        sel=self.getSelectionLevel(mol)
        selname=self.getSelectionName(sel,mol)
        if sel != mname :
            name='MSMS-MOL'+str(selname)       
            permol=0
        else : permol=1       
        if name in mol.geomContainer.geoms :
            self.mv.displayMSMS(sel, negate=(not self.GetBool(self.surf)), 
                                only=False, log=1, surfName=name, nbVert=1)
        else : 
            self.mv.computeMSMS(sel, log=1, display=self.GetBool(self.surf), 
                                perMol=permol,surfName=name)
            obj=mol.geomContainer.geoms[name].obj
            obj.SetName(name)
            self.mv.colorByAtomType(mname, [name], log=0)
        self.updateViewer()
        self.mv.molDispl[mname][3]=self.GetBool(self.surf)
        #c4d.gui.SetMousePointer(c4d.MOUSE_NORMAL)
        return True

    def updateCoarseMS(self):
        #c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        mname,mol=self.getMolName()   
        sel=self.getSelectionLevel(mol)       
        name='CoarseMS'+str(mol.name)
        selname=self.getSelectionName(sel,mol)
        select=self.mv.select(sel,negate=False, only=True, xor=False, log=0, 
                              intersect=False)
        parent=mol.geomContainer.masterGeom.obj       
        if sel != mname : 
            name='CoarseMS'+str(selname)
            chain=select.findParentsOfType(Chain)[0]
            parent=mol.geomContainer.masterGeom.chains_obj[chain.name]
        #print 'CoarseMS',name,sel,mname,parent
        option = self.GetReal(self.cms_slider)
        res = self.GetReal(self.cms_res_slider)
        if name in mol.geomContainer.geoms.keys():
            g = mol.geomContainer.geoms[name]
            proxy = None
            if hasattr(g,"color_obj"):
                proxy = g.color_obj			
            obj = g.obj
            #print proxy,obj
            g = self.epmv.coarseMolSurface(select,[32,32,32],
                                           isovalue=option,resolution=res,
                                           name=name,
                                           geom=g)    
            #mol.geomContainer.geoms[name]=g
            g.obj = obj
            g.color_obj=proxy		
            #print g.color_obj,g.obj
            self.epmv.helper.updateMesh(g,parent=parent, proxyCol=False,mol=mol)
            self.mv.molDispl[mname][4]=self.GetBool(self.cms)
            #need to call the color function
            #self.color(None,[name,])
        self.updateViewer()
        #c4d.gui.SetMousePointer(c4d.MOUSE_NORMAL)
        return True
    
    def displayCoarseMS(self):
        #c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        mname,mol=self.getMolName()   
        sel=self.getSelectionLevel(mol)       
        name='CoarseMS'+str(mol.name)
        selname=self.getSelectionName(sel,mol)
        select=self.mv.select(sel,negate=False, only=True, xor=False, log=0, 
                              intersect=False)
        parent=mol.geomContainer.masterGeom.obj       
        if sel != mname : 
            name='CoarseMS'+str(selname)
            chain=select.findParentsOfType(Chain)[0]
            parent=mol.geomContainer.masterGeom.chains_obj[chain.name]
        if name not in mol.geomContainer.geoms.keys():
            g=self.epmv.coarseMolSurface(select,[32,32,32],isovalue=7.1,
                                         resolution=-0.3,name=name)
            atoms = mol.findType(Atom)
            mol.geomContainer.geoms[name]=g
            c4dobj=self.epmv.helper.createsNmesh(name,g.getVertices(),None,g.getFaces(),
                                        smooth=True,proxyCol=True)
            self.epmv.helper.addObjToGeom(c4dobj,g)
            doc=c4d.documents.GetActiveDocument()           
            self.epmv.helper.addObjectToScene(doc,c4dobj[0],parent=parent)
            c4dobj = c4dobj[0]       
        else : 
            c4dobj=mol.geomContainer.geoms[name].obj
        self.epmv.helper.toggleDisplay(c4dobj,self.GetBool(self.cms))    
        #c4d.MultiMessage(c4d.MSG_UPDATE)
        self.mv.molDispl[mname][4]=self.GetBool(self.cms)
        self.updateViewer()
        #c4d.gui.SetMousePointer(c4d.MOUSE_NORMAL)
        return True

    def create2DShape(self):
        doc=c4d.documents.GetActiveDocument()
        shap=c4d.BaseObject(c4d.Onull)
        shap.SetName('BaseShape')
        self.epmv.helper.addObjectToScene(doc,shap)
        shape2d,array =self.epmv.helper.createShapes2D(doc=doc,parent=shap)
        self.updateViewer()
        return shape2d

    def createLoft(self):
        #Kill C4d when called????
        #c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        mname,mol=self.getMolName()   
        sel=self.getSelectionLevel(mol)       
        doit=self.GetBool(self.loft)
        doc=c4d.documents.GetActiveDocument()
        ret=False	   
        for ch in mol.chains :
            name='loft'+mol.name+'_'+ch.name
            loft=self.epmv.helper.getObject(name)
            #print "loft", loft
            if loft != None : 
                self.epmv.helper.toggleDisplay(loft,doit)
                #need to toggle the spline too
                name=mol.name+'_'+ch.name+'spline'
                sp=self.epmv.helper.getObject(name)
                if loft != None :
                    self.epmv.helper.toggleDisplay(sp,doit) 
                ret=True				   
        if ret : 
            self.updateViewer()
            #c4d.gui.SetMousePointer(c4d.MOUSE_NORMAL)
            return True
        shape2dDic=self.create2DShape()
        #self.mv.displayExtrudedSS(mol.name, negate=False, only=False, log=0)
        #print "ok extruded"
        #return True
        for ch in mol.chains :
            atoms=ch.getAtoms().get('backbone')
            loft=self.epmv.helper.loftnurbs('loft'+mol.name+'_'+ch.name)
            #print loft.GetName()
            ch.loft = loft       
            self.epmv.helper.addObjectToScene(doc,loft,parent=mol.geomContainer.masterGeom.chains_obj[ch.name])              
            sheet=ch.sheet2D['ssSheet2D']
            sheet.chords=1
            #print "before"       
            sheet.compute(sheet.coords, sheet.isHelix, nbrib=sheet.nrib, 
                          nbchords=sheet.chords, offset=sheet.offset)
            #print "sheet computed ok"
            #Segmentation Fault
            #
            #return True
            sh=self.epmv.helper.LoftOnSpline(mol.name+'_'+ch.name,ch,atoms,
                                             shapes2d=shape2dDic,instance=True)#bool(self.get(self.instance)))
            ch.sh = sh
            #sh=self.epmv.helper.c4dSecondaryLoftsSp('ssSheet2D',atoms,shapes2d=shape2dDic,instance=True)#bool(self.get(self.instance)))
            for k,o in enumerate(sh) :
                #print o,o.get_name(),loft.get_name()
                self.epmv.helper.addObjectToScene(doc,o,parent=loft)
        self.updateViewer()
        #c4d.gui.SetMousePointer(c4d.MOUSE_NORMAL)
        return True

    def createArmature(self):
        #should we use the selection ?
        #c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        if VERBOSE :print "create Armature"   
        mname,mol=self.getMolName()   
        sel=self.getSelectionLevel(mol)    
        if VERBOSE :print "for CA of ",mol.name
        doit=self.GetBool(self.armature)
        doc=c4d.documents.GetActiveDocument()
        name='armature'+mol.name
        sp=doc.SearchObject(name)
        if sp != None : 
            self.epmv.helper.toggleDisplay(sp,doit)
            self.updateViewer()
            return True
        atoms=mol.allAtoms.get("CA")
        if len(atoms) == 0 :
            atoms=mol.allAtoms.get("backbone")
        armature,joints=self.epmv.helper.armature('armature'+mol.name,atoms,scn=doc,
                                           root=mol.geomContainer.masterGeom.obj)
        mol.geomContainer.geoms["armature"]=[armature,joints]
        self.updateViewer()
        return True

    def createSpline(self):
        #c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        mname,mol=self.getMolName()   
        sel=self.getSelectionLevel(mol)
        selection = self.mv.select(sel,negate=False, only=True, xor=False, 
                                   log=0, intersect=False)       
        doit=self.GetBool(self.spline)
        doc=c4d.documents.GetActiveDocument()
        name='spline'+mol.name
        sp=doc.SearchObject(name)
        if VERBOSE :print "spline",sp
        if sp != None : 
            self.epmv.helper.toggleDisplay(sp,doit)
            self.updateViewer()
            return True	   	   	   	   
        atoms = selection.findType(Atom)
        atoms.sort()
        spline=self.epmv.helper.spline(name,atoms.coords,scene=doc,
                                       parent=mol.geomContainer.masterGeom.obj)
        self.updateViewer()
        return True


    #######COLORING COMMAND####################################################

    def getGeomActive(self):
        lgeomName=[]
        mname,mol=self.getMolName()   
        sel=self.getSelectionLevel(mol)
        selname=self.getSelectionName(sel,mol)           
        if self.GetBool(self.surf) : 
            sname='MSMS-MOL'+str(mname)
            if sel != mname :sname='MSMS-MOL'+str(selname)       
            lgeomName.append(sname)
        if self.GetBool(self.cpk) : lgeomName.append('cpk')
        if self.GetBool(self.ss) : lgeomName.append('secondarystructure')
        if self.GetBool(self.bs) : 
            lgeomName.append('balls')
            lgeomName.append('sticks')
        if self.GetBool(self.cms) : 
            sname='CoarseMS'+str(mname)
            if sel != str(mname) :sname='CoarseMS'+str(selname)       
            lgeomName.append(sname)        
        return lgeomName


    def chooseCol(self):
        #print self.get(self.unic_color)
        #print self.get(self._color)
        coli=int(self.GetLong(self._color))
        mname,mol=self.getMolName()   
        sel=self.getSelectionLevel(mol)       
        if coli == 4 :
            lGeom=self.getGeomActive()  
            colorU= self.GetColorField(self.unic_color)
            #print colorU[0]     
            self.funcColor[coli](sel,[(colorU['color'].x,colorU['color'].y,colorU['color'].z)] ,lGeom, log=1)
            self.mv.molDispl[mname][6]=colorU
        return True
                  
    def color(self,geoms=None):
        #c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        mname,mol=self.getMolName()   
        sel=self.getSelectionLevel(mol)       
        #what have to be colored : checkbox
        if geoms is not None : lGeom = geoms
        else : lGeom=self.getGeomActive()
        coli=int(self.GetLong(self._color))
        if coli == 4 :
            colorU= self.GetColorField(self.unic_color)
            self.funcColor[coli](sel,[(colorU['color'].x,colorU['color'].y,colorU['color'].z)] ,lGeom, log=1)
            self.mv.molDispl[mname][6]=colorU
        elif coli == 5 :
            self.mv.colorByProperty.level='Atom'
            selection = self.mv.select(sel,negate=False, only=True, xor=False, log=0, intersect=False)
            if not isinstance(selection,Atom) : selection = selection.findType(Atom)
            ma = len(selection)
            self.funcColor[coli](selection, lGeom, 'number',mini=1.0,maxi=float(ma),
                               propertyLevel='Atom', colormap='rgb256',log=1)
        elif coli == 7 :
            self.mv.colorByProperty.level='Atom'
            selection = self.mv.select(sel,negate=False, only=True, xor=False, log=0, intersect=False)
            if not isinstance(selection,Atom) : selection = selection.findType(Atom)
            ma = max(selection.temperatureFactor)
            mi = min(selection.temperatureFactor)
            self.funcColor[5](selection, lGeom, 'temperatureFactor',mini=float(mi),maxi=float(ma),
                               propertyLevel='Atom', colormap='rgb256',log=1)            
        elif coli == 8 :
            self.mv.colorByProperty.level='Atom'
            selection = self.mv.select(sel,negate=False, only=True, xor=False, log=0, intersect=False)
            if not isinstance(selection,Atom) : selection = selection.findType(Atom)
            #should I recompute ?
            self.mv.computeSESAndSASArea(mol, log=0)
            ma = max(selection.sas_area)
            mi = min(selection.sas_area)
            self.funcColor[5](selection, lGeom, 'sas_area',mini=float(mi),maxi=float(ma),
                               propertyLevel='Atom', colormap='rgb256',log=1)            
        else : self.funcColor[coli](sel, lGeom, log=1)
        self.mv.molDispl[mname][5]=coli
        self.updateViewer()
        return True       

    def drawPyAutoDock(self):
        self.ad.Open(c4d.DLG_TYPE_ASYNC, pluginid=2555553, defaultw=120, defaulth=200)

    def drawPreferences(self):
        self.options.Open(c4d.DLG_TYPE_ASYNC, pluginid=2555554, defaultw=250, defaulth=200)

    def modellerGUI(self):
        self.pd.Open(c4d.DLG_TYPE_ASYNC, pluginid=2555555,defaultw=120, defaulth=200)

    def modellerOptimize(self):
        import modeller
        mname,mol=self.getMolName()   
        sel=self.getSelectionLevel(mol)       
        mdl = mol.mdl
        print mname
        # Select all atoms:
        atmsel = modeller.selection(mdl)
        
        # Generate the restraints:
        mdl.restraints.make(atmsel, restraint_type='stereo', spline_on_site=False)
        #mdl.restraints.write(file=mpath+mname+'.rsr')
        mpdf = atmsel.energy()
        print "before optmimise"
        # Create optimizer objects and set defaults for all further optimizations
        cg = modeller.optimizers.conjugate_gradients(output='REPORT')
        mol.pmvaction.last = 10000
        print "optimise"
        maxit = self.pd.GetLong(self.pd.NUMBERS['miniIterMax']['id'])
        mol.pmvaction.store = self.pd.GetBool(self.pd.CHECKBOXS['store']['id'])
        mol.pmvaction.redraw = True
        cg.optimize(atmsel, max_iterations=maxit, actions=mol.pmvaction)#actions.trace(5, trcfil))
        del cg
        mol.pmvaction.redraw = False
        return True
        
    def modellerMD(self):
        import modeller
        mname,mol=self.getMolName()   
        sel=self.getSelectionLevel(mol)       
        mdl = mol.mdl
        print mname
        # Select all atoms:
        atmsel = modeller.selection(mdl)
        
        # Generate the restraints:
        mdl.restraints.make(atmsel, restraint_type='stereo', spline_on_site=False)
        #mdl.restraints.write(file=mpath+mname+'.rsr')
        mpdf = atmsel.energy()
        print "before optmimise"
        md = modeller.optimizers.molecular_dynamics(output='REPORT')
        mol.pmvaction.last = 10000
        mol.pmvaction.store = True
        print "optimise"
        maxit = self.pd.GetLong(self.pd.NUMBERS['mdIterMax']['id'])
        temp = self.pd.GetReal(self.pd.NUMBERS['mdTemp']['id'])
        mol.pmvaction.store = self.pd.GetBool(self.pd.CHECKBOXS['store']['id'])
        print maxit,temp,mol.pmvaction.store
        mol.pmvaction.redraw = True
        md.optimize(atmsel, temperature=temp, max_iterations=int(maxit),actions=mol.pmvaction)
        del md
        mol.pmvaction.redraw = False
        return True

    def citationInformation(self):
        txt=self.epmv.getCitations()
        c4d.gui.MessageDialog(txt)

    def drawAbout(self):
        #just Draw a litlle windows of some about ePMV, like how,who, etc...
        #and PMV citation
        c4d.gui.MessageDialog(__doc__)


    def addExtensionGUI(self):
        input=c4d.gui.InputDialog("Enter the extension name follow by the directory\nSupported extension are: Modeller, Pyrosetta\n",
        "modeller:/Library/modeller/modlib")
        self.inst.addExtension(input)

    def launchBrowser(self):
        #launch the default interenet browser and open the ePMV wiki page
        import webbrowser
        webbrowser.open(__url__[0])

    def launchAFgui(self):
        c4d.CallCommand(102380125)

    def launchARgui(self):
        if not hasattr(self.mv,'art'):
           self.mv.initARViewer(log=0)
           self.mv.art.patternMgr.useGUI = False
           self.mv.art.AR.Set(usePlus=False,useCfg=False,usePatCfg=False)
           self.mv.art.disable_magic_lenses()
           self.mv.art.useScenePattern=False
           self.mv.art.use_current_camera = False
           self.mv.art.dual_display = False
           self.mv.art.useAR = True
           self.mv.art.use_gesture = False
        #setupgeom?
        self.argui.Open(c4d.DLG_TYPE_ASYNC, pluginid=2555556, defaultw=120, defaulth=200)
        

    #######EVENT COMMAND######################################################
    def Command(self, id, msg):
        c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        #check the id/event
        #Menu id
        for menu in self.MENU_ID.keys():
            for item in self.MENU_ID[menu]:
                if item["name"] == "Recent Files" :
                    if self.mv.recentFiles.categories.has_key("Documents"):
                        for i,r in enumerate(self.mv.recentFiles.categories["Documents"]):
                            if id == item["id"]*(i+2) :
                                self.buttonBrowse(file=r[0])					   				   		   
                else :
                    if id==item["id"] :
                        if self.epmv.timer : self.timeFunction(item["action"])
                        else : item["action"]()
        #Label Id
        for label in self.LABEL_ID:
            if id == label["id"] :
                print "Label"
                #return True
        #Checkbox ID
        for cbut in self.CHECKBOXS.keys():
            if id == self.CHECKBOXS[cbut]["id"]:
                if self.epmv.timer : self.timeFunction(self.CHECKBOXS[cbut]["action"])
                else : self.CHECKBOXS[cbut]["action"]()
                #return True

        #Sliders ID
        for slide in self.SLIDERS.keys():
            if id == self.SLIDERS[slide]["id"]:
                if self.epmv.timer : self.timeFunction(self.SLIDERS[slide]["action"])
                else : self.SLIDERS[slide]["action"]()
                #return True

        #Combo Box ID
        for box in self.COMB_BOX.keys():
            if id == self.COMB_BOX[box]["id"]:
                if self.epmv.timer : self.timeFunction(self.COMB_BOX[box]["action"])
                else : self.COMB_BOX[box]["action"]()
                #return True
         #SEL_BTN ID
        for box in self.SEL_BTN.keys():
            if id == self.SEL_BTN[box]["id"]:
                if self.epmv.timer : self.timeFunction(self.SEL_BTN[box]["action"])
                else : self.SEL_BTN[box]["action"]()
                #return True
               
        #single element id
        if id == self.EDIT_TEXT["id"]:
            #while  typing in the edittext area do nothing
            pass
            #print "editText"
            #self.EDIT_TEXT["action"]()
        elif id == self.LOAD_BTN["id"]:
            if VERBOSE : print "load btn"
            if self.epmv.timer : self.timeFunction(self.LOAD_BTN["action"])
            else :self.LOAD_BTN["action"]()
        elif id == self.FETCH_BTN["id"]:
            if VERBOSE : print "load btn"
            if self.epmv.timer : self.timeFunction(self.FETCH_BTN["action"])
            else :self.FETCH_BTN["action"]()
        elif id == self.DATA_BTN["id"]:
            if VERBOSE : print "load data"
            if self.epmv.timer : self.timeFunction(self.DATA_BTN["action"])
            else :self.DATA_BTN["action"]()
        elif id == self.PMV_BTN["id"]:
            if VERBOSE : print "load btn"
            if self.epmv.timer : self.timeFunction(self.PMV_BTN["action"])
            else :self.PMV_BTN["action"]()
        elif id == self.KEY_BTN["id"]:
            if VERBOSE : print "load btn"
            if self.epmv.timer : self.timeFunction(self.KEY_BTN["action"])
            else :self.KEY_BTN["action"]()
        elif id == self.COLFIELD["id"]:
            if self.epmv.timer : self.timeFunction(self.COLFIELD["action"])
            else :self.COLFIELD["action"]()
        #else :
        #    if VERBOSE : print "nothing"
        c4d.gui.SetMousePointer(c4d.MOUSE_NORMAL)
        self.updateViewer()
        return True

class epmv_C4dDialog(plugins.CommandData):
   """Class to register the entry in the plugins menu.
   In the most cases a dialog only needs to be in the
   memory when its really needed. So just allocate the memory
   for the dialog when the user calls it or CINEMA 4D restores
   it for the startup GUI."""
   dialog = None
   def Execute(self, doc):
         # create the dialog
         print "execute"   
         dname=doc.GetDocumentName()
         #if dname not in c4d.mv.keys() :
         #3       epmv = c4dAdaptor(debug=1)
         #       c4d.mv[dname]=epmv#self.epmv.helper.start(debug=1)     
         #print doc,c4d.mv[dname]
         if self.dialog is None:
            self.dialog = epmv_c4d()
            #self.dialog.mv=c4d.mv[dname].mv#self.epmv.helper.start(debug=1)
            #self.dialog.epmv=c4d.mv[dname]                            
            #self.dialog.set_up()
         #else : 
         #   self.dialog.mv=c4d.mv[dname].mv
         #   self.dialog.epmv=c4d.mv[dname]
         #self.dialog.epmv.gui = self.dialog            
         return self.dialog.Open(c4d.DLG_TYPE_ASYNC, pluginid=PLUGIN_ID,
                              defaultw=270, defaulth=375)
    
   def RestoreLayout(self, sec_ref):
         print "restore",sec_ref    
         doc=c4d.documents.GetActiveDocument()
         dname=doc.GetDocumentName()
         #print doc,dname,c4d.mv
         if self.dialog is None:
            self.dialog = epmv_c4d()
            #if dname not in c4d.mv.keys() :
                 #print "start a new epmv" 
            #    epmv = c4dAdaptor(debug=1)           
            #    c4d.mv[dname]=epmv#self.epmv.helper.start(debug=1)                
            #else :                
                 #print "reset epmv"            
            #     self.epmv.helper.reset_ePMV(c4d.mv[dname],debug=1)
            #3#self.dialog.mv=c4d.mv[dname].mv#self.epmv.helper.start(debug=1)    
            #3self.dialog.epmv=c4d.mv[dname]            
            #3self.dialog.set_up()
#         else : 
#            if dname not in c4d.mv.keys() :
#                epmv = c4dAdaptor(debug=1)
#                c4d.mv[dname]=epmv#.mv#self.epmv.helper.start(debug=1)
#                self.dialog.set_up()
#            #else : self.epmv.helper.reset_ePMV(c4d.mv[dname],debug=1)
#            self.dialog.mv=c4d.mv[dname].mv  
#            self.dialog.epmv=c4d.mv[dname]                                     
         self.dialog.restored=True
#         self.dialog.epmv.gui = self.dialog         
         #self.dialog.firstmol=True
         #self.dialog.indice=0              
         return self.dialog.Restore(pluginid=PLUGIN_ID,secret=sec_ref)

if __name__ == "__main__":
    bmp = bitmaps.BaseBitmap()
    dir, file = os.path.split(__file__)
    fn = os.path.join(dir, "pmv.tif")
    bmp.InitWith(fn)
    #import mglutil.hostappli.pdb_c4d as self.epmv.helper
    #doc=c4d.documents.get_active_document()
    if not hasattr(c4d,'mv'):
        c4d.mv={}    
    #c4d.mv[doc.get_document_name()]=self.epmv.helper.start(debug=1)
    plugins.RegisterCommandPlugin(id=PLUGIN_ID, str="Py-ePMV",
                                     help="This is an embedded Molecular Viewer.",
                                     dat=epmv_C4dDialog(),info=0, icon=bmp)
    #plugins.RegisterCommandPlugin(id=PLUGIN_ID, str="Py-ePMV",
     #                                help="This is an embedded Molecular Viewer.",
     #3                                dat=epmv_C4dDialog(),info=0, icon=bmp)                                 
    """
import mglutil.hostappli.pdb_c4d as self.epmv.helper
import c4d
doc=c4d.documents.get_active_document()
mv=self.epmv.helper.start(debug=1)
doc[123456] = self.epmv.helper.start(debug=1)

mol=self.Mols[0]
import mglutil.hostappli.pdb_c4d as self.epmv.helper
#self.colorAtomsUsingDG("1CRN", ['MSMS-MOL1CRN'], log=0)
self.colorByResidueType("1CRN", ['MSMS-MOL1CRN'], log=0)
colors=mol.geomContainer.getGeomColor('MSMS-MOL1CRN')
print colors
obj=self.epmv.helper.PolygonColorsObject('MSMS-MOL1CRN',colors)
import c4d
doc=c4d.documents.get_active_document()
self.epmv.helper.addObjectToScene(c4d.documents.get_active_document(),obj,parent=mol.geomContainer.masterGeom.obj)
#mol=self.Mols[0]
obj=mol.geomContainer.geoms['MSMS-MOL1CRN'].obj
#obj.make_tag(1024681)
doc.set_active_object(obj)
c4d.call_command(1023892)

mol=self.Mols[0]
from MolKit.molecule import Atom
atoms = mol.findType(Atom)
print mol.geomContainer.geoms.keys()
g=mol.geomContainer.geoms["CoarseMS1CRN"]
self.bindGeomToMolecularFragment(g, self.Mols[0].allAtoms, log=0)
self.colorByAtomType(mol.name, ["CoarseMS1CRN"], log=0)
colors=mol.geomContainer.getGeomColor("CoarseMS1CRN")
print "color",colors

PYQTDESIGNERPATH
PYTHONPATH

    """
