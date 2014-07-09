"""
Name: 'Python Molecular Viewer GUI'
Cinema4D: 11.5
Py4D:0.9.9986
"""

__author__ = "Ludovic Autin, Graham Johnson"
__url__ = [""]
__doc__ = """\
ePMV v0.1.1a
Use c4d as a molecular viewer

Provide gui interface to load and display Molecule Object (from pdb file for instance)
-load .pdb,.pdbqt,.pqr,.mol2,.cif
-display as CPK,Ball&Stick,Ribbon, MSMS and Coarse Molecular Surface
-color by: color,atom type, david goodsell atom type, resiude type, secondary structure type
-selection : any molecule levele MOL:CHAIN:RESIDUE:ATOM using keyword and picking functionality
-option available for : CPK, BS, CMS, MSMS under object selection...
"""
__version__="v0.1.1a"
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
    
MGL_ROOT=

#TODO:
#make the pyrosetta extension
#make the pyautodock extension
#add progress bar
#add restoring test
#test the selection
#NtoC did not work
#loft did not work
#copy  libjpeg.62.dylib in /usr/lib
import c4d
from c4d import plugins
from c4d import utils
from c4d import bitmaps
from c4d import gui
from c4d import symbols as sy

#setup the python Path
import sys
import os
from time import time
sys.path[0]=(MGL_ROOT+'/lib/python2.5/site-packages')
sys.path.insert(0,MGL_ROOT+'/lib/python2.5/site-packages/PIL')
sys.path.append(MGL_ROOT+'/MGLToolsPckgs')

#be sure to use a unique ID obtained from www.plugincafe.com
PLUGIN_ID = 10234096

from MolKit.protein import ResidueSetSelector,Chain
from MolKit.molecule import Atom
from Pmv.pmvPalettes import AtomElements
from Pmv.pmvPalettes import RasmolAmino
from Pmv.hostappInterface.install_plugin import Installer
from Pmv.hostappInterface import comput_util as C
#import Pmv.hostappInterface.cinema4d.helperC4D as self.epmv.helper

VERBOSE = 0
#from Pmv.hostappInterface.cinema4d_dev.c4dAdaptor import c4dAdaptor
#epmv = c4dAdaptor(debug=1)
#epmv.mv.readMolecule("/Users/ludo/blenderKTF/1CRN.pdb")
#epmv.mv.computeMSMS("1CRN")
#epmv.mv.computeMSMS("1CRN", log=1, display=True, perMol=1,surfName="MSMS-MOL1CRN")
#epmv.mv.displayCPK("1CRN",log=1,negate=False,scaleFactor = 1.0)

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
                        "scale":{"id":id+2,"name":"Scale Device",'width':150,"height":10,"action":self.setScale}
                        }
        id = id + 3
        return True


    def CreateLayout(self):
        ID=0
        self.SetTitle("Options")
        self.initWidgetId()
        #minimize otin/button
        self.GroupBegin(id=ID,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                           cols=1, rows=4)
        self.GroupBorderSpace(1, 1, 1, 1)
        ID = ID +1
        #store?
        self.AddStaticText(ID,flags=gui.BFH_LEFT)
        self.SetString(ID,"AR options")                                    
        ID = ID +1
        self.AddCheckbox(id=self.CHECKBOXS["avg1"]["id"],flags=gui.BFH_CENTER|gui.BFH_SCALEFIT,
                                name=self.CHECKBOXS["avg1"]["name"],
                                initw=self.CHECKBOXS["avg1"]["width"],
                                inith=self.CHECKBOXS["avg1"]["height"])
        self.AddCheckbox(id=self.CHECKBOXS["avg2"]["id"],flags=gui.BFH_CENTER|gui.BFH_SCALEFIT,
                                name=self.CHECKBOXS["avg2"]["name"],
                                initw=self.CHECKBOXS["avg2"]["width"],
                                inith=self.CHECKBOXS["avg2"]["height"])
        self.AddCheckbox(id=self.CHECKBOXS["conc"]["id"],flags=gui.BFH_CENTER|gui.BFH_SCALEFIT,
                                name=self.CHECKBOXS["conc"]["name"],
                                initw=self.CHECKBOXS["conc"]["width"],
                                inith=self.CHECKBOXS["conc"]["height"])

        his=self.AddEditSlider(id=self.SLIDERS["his"]["id"],
                                            flags=gui.BFH_LEFT|gui.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["his"]["width"])
        self.SetInt(his,5,0,  20, 1)
        thr=self.AddEditSlider(id=self.SLIDERS["thr"]["id"],
                                            flags=gui.BFH_LEFT|gui.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["thr"]["width"])                                            
        self.SetInt(thr,100,0,  200, 1)
        sc=self.AddEditSlider(id=self.SLIDERS["scale"]["id"],
                                            flags=gui.BFH_LEFT|gui.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["scale"]["width"])
        self.SetFloat(sc,1.,0.,  20., 0.1)
        sc=self.AddEditSlider(id=self.NUMBERS["nrjrate"]["id"],
                                            flags=gui.BFH_LEFT|gui.BFH_SCALEFIT, 
                                            initw=self.NUMBERS["nrjrate"]["width"])
        self.SetInt(sc,1,0,  50, 1)

        self.AddStaticText(ID,flags=gui.BFH_LEFT)
        self.SetString(ID,"Video options")                                    
        ID = ID +1
        
        self.AddCheckbox(id=self.CHECKBOXS["showV"]["id"],flags=gui.BFH_CENTER|gui.BFH_SCALEFIT,
                                name=self.CHECKBOXS["showV"]["name"],
                                initw=self.CHECKBOXS["showV"]["width"],
                                inith=self.CHECKBOXS["showV"]["height"])
        self.SetBool(self.CHECKBOXS["showV"]["id"],True)
        self.AddCheckbox(id=self.CHECKBOXS["showDV"]["id"],flags=gui.BFH_CENTER|gui.BFH_SCALEFIT,
                                name=self.CHECKBOXS["showDV"]["name"],
                                initw=self.CHECKBOXS["showDV"]["width"],
                                inith=self.CHECKBOXS["showDV"]["height"])
        self.AddCheckbox(id=self.CHECKBOXS["flipV"]["id"],flags=gui.BFH_CENTER|gui.BFH_SCALEFIT,
                                name=self.CHECKBOXS["flipV"]["name"],
                                initw=self.CHECKBOXS["flipV"]["width"],
                                inith=self.CHECKBOXS["flipV"]["height"])
        self.GroupEnd()
        self.GroupBegin(id=ID,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                           cols=3, rows=4)
        self.GroupBorderSpace(1, 1, 1, 1)
        ID = ID +1

        self.AddButton(id=self.BTN["initVideo"]["id"], flags=gui.BFH_CENTER | gui.BFV_MASK,
                            initw=self.BTN["initVideo"]["width"],
                            inith=self.BTN["initVideo"]["height"],
                            name=self.BTN["initVideo"]["name"])
        self.AddButton(id=self.BTN["startVideo"]["id"], flags=gui.BFH_CENTER | gui.BFV_MASK,
                            initw=self.BTN["startVideo"]["width"],
                            inith=self.BTN["startVideo"]["height"],
                            name=self.BTN["startVideo"]["name"])
        self.AddButton(id=self.BTN["stopVideo"]["id"], flags=gui.BFH_CENTER | gui.BFV_MASK,
                            initw=self.BTN["stopVideo"]["width"],
                            inith=self.BTN["stopVideo"]["height"],
                            name=self.BTN["stopVideo"]["name"])
        self.GroupEnd()
        self.AddSeparatorH(200,flags=gui.BFH_SCALEFIT | gui.BFV_MASK)
        self.GroupBegin(id=ID,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                           cols=1, rows=4)
        self.GroupBorderSpace(1, 1, 1, 1)
        ID = ID +1
        self.AddButton(id=self.BTN["startAR"]["id"], flags=gui.BFH_LEFT | gui.BFV_MASK|gui.BFH_SCALEFIT,
                            initw=self.BTN["startAR"]["width"],
                            inith=self.BTN["startAR"]["height"],
                            name=self.BTN["startAR"]["name"])         
        self.GroupEnd()
        return True

    def setScale(self):
        self.epmv.mv.art.scaleDevice = self.GetFloat(self.SLIDERS["scale"]["id"])
        
    def toggleAvg1(self):
        self.epmv.mv.art.set_average_mode(self.GetBool(self.CHECKBOXS["avg1"]["id"]))
        
    def toggleAvg2(self):
        self.epmv.mv.art.patternMgr.means=bool(self.GetBool(self.CHECKBOXS["avg2"]["id"]))

    def toggleConcat(self):
        self.epmv.mv.art.concat=bool(self.GetBool(self.CHECKBOXS["conc"]["id"]))
        
    def setThreshold(self):
        thr = self.GetInt(self.SLIDERS["thr"]["id"])
        self.epmv.mv.art.set_threshold_cmd(thr)

    def setEnergieRate(self):
        self.epmv.mv.art.nrg_calcul_rate = self.GetInt(self.NUMBERS['nrjrate']['id'])
        
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
                          "action":self.setup}
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
                                  "height":10,"action":None},
                         "display":{"id":id+1,"name":"display",'width':100,
                                    "height":10,"action":None}}
        id = id + 2
        return True

    def CreateLayout(self):
        ID=0
        self.SetTitle("PyAutoDock")
        self.initWidgetId()
        #minimize otin/button
        self.GroupBegin(id=ID,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                           cols=2, rows=4)
        self.GroupBorderSpace(1, 1, 1, 1)
        ID = ID +1

        self.AddStaticText(ID,flags=gui.BFH_SCALEFIT)
        self.SetString(ID,"Receptor")
        ID = ID +1
        
        self.rec=self.AddEditText(id=self.TXT['rec']["id"],flags=gui.BFH_SCALEFIT | gui.BFV_MASK)
#        self.AddButton(id=self.BTN["rec"]["id"], flags=gui.BFH_LEFT | gui.BFV_MASK,
#                            initw=self.BTN["rec"]["width"],
#                            inith=self.BTN["rec"]["height"],
#                            name=self.BTN["rec"]["name"])
        self.SetString(self.TXT['rec']["id"],"hsg1:::;")
        self.AddStaticText(ID,flags=gui.BFH_SCALEFIT)
        self.SetString(ID,"Ligand")        
        ID = ID +1
        self.lig=self.AddEditText(id=self.TXT['lig']["id"],flags=gui.BFH_SCALEFIT | gui.BFV_MASK)
        self.SetString(self.TXT['lig']["id"],"ind:::;")
#        self.AddButton(id=self.BTN["rec"]["id"], flags=gui.BFH_LEFT | gui.BFV_MASK,
#                            initw=self.BTN["rec"]["width"],
#                            inith=self.BTN["rec"]["height"],
#                            name=self.BTN["rec"]["name"])

        self.AddStaticText(ID,flags=gui.BFH_SCALEFIT)
        self.SetString(ID,"Scorer")        
        ID = ID +1
        self._scorertype=self.AddComboBox(id=self.COMB_BOX["score"]["id"],flags=gui.BFH_SCALEFIT,initw=60)
        map(lambda x,box=self._scorertype:self.AddChild(box,x[0],x[1]),enumerate(self.scorertype))

        self.AddCheckbox(id=self.CHECKBOXS["store"]["id"],flags=gui.BFH_SCALEFIT,
                                name=self.CHECKBOXS["store"]["name"],
                                initw=self.CHECKBOXS["store"]["width"],
                                inith=self.CHECKBOXS["store"]["height"])
        self.AddCheckbox(id=self.CHECKBOXS["display"]["id"],flags=gui.BFH_SCALEFIT,
                                name=self.CHECKBOXS["display"]["name"],
                                initw=self.CHECKBOXS["display"]["width"],
                                inith=self.CHECKBOXS["display"]["height"])
        self.GroupEnd()
        self.GroupBegin(id=ID,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                           cols=1, rows=4)
        self.GroupBorderSpace(1, 1, 1, 1)
        ID = ID +1
                                

        self.AddButton(id=self.BTN["ok"]["id"], flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                            initw=self.BTN["ok"]["width"],
                            inith=self.BTN["ok"]["height"],
                            name=self.BTN["ok"]["name"])
        
        #should display here a menu of available scorer...
        self._currentscorer=self.AddComboBox(id=self.COMB_BOX["scorer"]["id"],
                                             flags=gui.BFH_SCALEFIT,initw=60)
        map(lambda x,box=self._currentscorer:self.AddChild(box,x[0],x[1]),enumerate(self.scoreravailable))
        return True

    def setRec(self):
        pass
    def setLig(self):
        pass

    def getScorerAvailable(self):
        self.scoreravailable = []
        if hasattr(self.epmv.mv,'energy'):
            self.scoreravailable = self.epmv.mv.energy.data.keys()

    def setCurrentScorer(self):
        name = self.scoreravailable[self.GetInt(self._currentscorer)]
        self.epmv.mv.energy.current_scorer = self.epmv.mv.energy.data[name]

    def setScorer(self):
        self._scorer = self.scorertype[self.GetInt(self._scorertype)]
        
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
        if self.GetBool(self.CHECKBOXS['display']['id']) and not self._display:
            self.initDisplay()
            self._display = True
            
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
        label = self.epmv.helper.newEmpty("label")
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
                self.CHECKBOXS[butn]["action"]()
        c4d.gui.SetMousePointer(c4d.MOUSE_NORMAL)
        self.epmv.gui.updateViewer()
        return True
    
class ParameterModeller(gui.SubDialog):
    #.epmv
    def initWidgetId(self):
        #minimize options
        #max_iterations=1000
        #md options
        #temperature=300, max_iterations=1000
        id=1005
        self.NUMBERS = {"miniIterMax":{"id":id,"name":"max_iteration",'width':50,"height":10,"action":None},
                        "mdIterMax":{"id":id+1,"name":"max_iteration",'width':50,"height":10,"action":None},
                        "mdTemp":{"id":id+2,"name":"temperature",'width':50,"height":10,"action":None}
                        }
        id = id + 3
        self.BTN = {"mini":{"id":id,"name":"minimize",'width':50,"height":10,"action":self.epmv.gui.modellerOptimize},
                    "md":{"id":id+1,"name":"MD",'width':50,"height":10,"action":self.epmv.gui.modellerMD}
                    }
        id = id + 2
        self.CHECKBOXS ={"store":{"id":id,"name":"store",'width':100,"height":10,"action":None}}
        id = id + 1 
        return True

    def CreateLayout(self):
        ID=0
        self.SetTitle("Options")
        self.initWidgetId()
        #minimize otin/button
        self.GroupBegin(id=ID,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                           cols=2, rows=4)
        self.GroupBorderSpace(1, 1, 1, 1)
        ID = ID +1
        #store?
        
        self.AddCheckbox(id=self.CHECKBOXS["store"]["id"],flags=gui.BFH_CENTER,
                                name=self.CHECKBOXS["store"]["name"],
                                initw=self.CHECKBOXS["store"]["width"],
                                inith=self.CHECKBOXS["store"]["height"])
        
        self.AddStaticText(ID,flags=gui.BFH_LEFT)
        self.SetString(ID,"")                                    
        ID = ID +1
        #minimize
        self.AddStaticText(ID,flags=gui.BFH_LEFT)
        self.SetString(ID,"max_iteration")   
        ID = ID +1        
        n = self.AddEditNumberArrows(id=self.NUMBERS["miniIterMax"]["id"],flags=gui.BFH_CENTER,
                                initw=self.NUMBERS["miniIterMax"]["width"],
                                inith=self.NUMBERS["miniIterMax"]["height"])
        self.SetInt(n,1000,0,  100000, 10)
        self.AddButton(id=self.BTN["mini"]["id"], flags=gui.BFH_LEFT | gui.BFV_MASK,
                            initw=self.BTN["mini"]["width"],
                            inith=self.BTN["mini"]["height"],
                            name=self.BTN["mini"]["name"])
        self.AddStaticText(ID,flags=gui.BFH_LEFT)
        self.SetString(ID,"")                                    
        ID = ID + 1
        #MD
        self.AddStaticText(ID,flags=gui.BFH_LEFT)
        self.SetString(ID,"max_iteration")                                    
        ID = ID + 1
        n = self.AddEditNumberArrows(id=self.NUMBERS["mdIterMax"]["id"],flags=gui.BFH_CENTER,
                                initw=self.NUMBERS["mdIterMax"]["width"],
                                inith=self.NUMBERS["mdIterMax"]["height"])
        self.SetInt(n,1000,0,  100000, 10)
        self.AddStaticText(ID,flags=gui.BFH_LEFT)
        self.SetString(ID,"temperature")                                    
        ID = ID + 1
        n = self.AddEditNumberArrows(id=self.NUMBERS["mdTemp"]["id"],flags=gui.BFH_CENTER,
                                initw=self.NUMBERS["mdTemp"]["width"],
                                inith=self.NUMBERS["mdTemp"]["height"])
        self.SetFloat(n,300.,-100.,  1000., 1.)
        self.AddButton(id=self.BTN["md"]["id"], flags=gui.BFH_LEFT | gui.BFV_MASK,
                            initw=self.BTN["md"]["width"],
                            inith=self.BTN["md"]["height"],
                            name=self.BTN["md"]["name"])
        self.AddStaticText(ID,flags=gui.BFH_LEFT)
        self.SetString(ID,"")                                    
        ID = ID + 1

        return True

#######EVENT COMMAND######################################################
    def Command(self, id, msg):
        c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        for butn in self.BTN.keys():
            if id == self.BTN[butn]["id"]:
                self.BTN[butn]["action"]()
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
        witdh=200
        id=1005
        self.OPTIONS = {'cam':{"id": id, "name":"PMV camera",'width':witdh,"height":10,"action":None},
                       'light':{"id": id+1, "name":"PMV lights",'width':witdh,"height":10,"action":None},
                       'clouds':{"id": id+2, "name":"Render points",'width':witdh,"height":10,"action":None},
                       'cyl':{"id": id+3, "name":"Split bonds",'width':witdh,"height":10,"action":None},
                       'log':{"id": id+4, "name":"Console log",'width':witdh,"height":10,"action":None},
                       'center':{"id": id+5, "name":"Center Molecule",'width':witdh,"height":10,"action":None},
                       'centerG':{"id": id+6, "name":"Center Grid",'width':witdh,"height":10,"action":None},
                       'fetch':{"id": id+7, "name":"Force Fetch instead of cache",'width':witdh,"height":10,"action":None}
                       }
        id = id + len(self.OPTIONS)
        if self.epmv.gui._modeller :
            self.OPTIONS['modeller']={"id": id, "name":"Modeller",'width':witdh,"height":10,"action":None}
            id = id + 1 
        self.BTN = {"ok":{"id":id,"name":"OK",'width':50,"height":10,"action":self.SetPreferences}}
        id = id + 1
        return True

    def CreateLayout(self):
        ID=0
        self.SetTitle("Preferences")
        self.initWidgetId()
        #minimize otin/button
        self.GroupBegin(id=ID,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                           cols=1, rows=10)
        self.GroupBorderSpace(10, 10, 5, 10)
        ID = ID +1
        #store?
        for k in self.OPTIONS.keys():
            self.AddCheckbox(id=self.OPTIONS[k]["id"],flags=gui.BFH_CENTER,
                                name=self.OPTIONS[k]["name"],
                                initw=self.OPTIONS[k]["width"],
                                inith=self.OPTIONS[k]["height"])
        
        self.AddButton(id=self.BTN["ok"]["id"], flags=gui.BFH_CENTER | gui.BFV_MASK,
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
        
        if self.epmv.gui._modeller :
            self.epmv.gui._useModeller = self.GetBool(self.OPTIONS['modeller']["id"])
            self.epmv.useModeller = self.epmv.gui._useModeller
            if self.epmv.gui._useModeller :
                self.epmv.center_mol = False
                self.epmv.center_grid = False
                if self.epmv.gui.env is None:
                    import modeller
                    #setup Modeller
                    self.epmv.gui.env = modeller.environ()
                    MPATH=MGL_ROOT+'/MGLToolsPckgs/Pmv/hostappInterface/extension/Modeller/'
                    self.epmv.gui.env.io.atom_files_directory = [MPATH]
                    self.epmv.gui.env.edat.dynamic_sphere = True
                    self.epmv.gui.env.libs.topology.read(file='$(LIB)/top_heav.lib')
                    self.epmv.gui.env.libs.parameters.read(file='$(LIB)/par.lib')
        #self.AskClose()
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
    
    def setupEPMV(self):
        from Pmv.hostappInterface.cinema4d.c4dAdaptor import c4dAdaptor
        doc = c4d.documents.GetActiveDocument()
        dname=doc.GetDocumentName()
        if dname not in c4d.mv.keys() :
            epmv = c4dAdaptor(debug=1)
            c4d.mv[dname]=epmv#self.epmv.helper.start(debug=1)     
        self.mv=c4d.mv[dname].mv#self.epmv.helper.start(debug=1)
        self.epmv=c4d.mv[dname]                            
        self.epmv.gui = self  
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
        self.MENU_ID = {"ePMV":
                      [{"id": id, "name":"Load PDB","action":self.buttonLoad},
                       {"id": id+1, "name":"Load Data","action":self.buttonLoadData},
                       {"id": id+2, "name":"Update","action":self.epmv_update}],
                       "Preferences" :
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
                      ],
                       }
        id = id + 7
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
        self.presettype=['available presets:','  Lines','  Sticks','  SpaceFilling',
                         '  Ball+Sticks','  RibbonProtein+StickLigand',
                         '  RibbonProtein+CPKligand','  xray','  Custom',
                         '  Save Custom As...']
        self.keyword = ['keywords:','  backbone','  sidechain','  chain','  picked']
        kw=map(lambda x:"  "+x,ResidueSetSelector.residueList.keys())
        self.keyword.extend(kw)
        
        self.scriptliste = ['Open:','pymol_demo','interactive_docking','demo1','user_script']
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
        self.current_traj=None
        self.firstmol=True
        self.firsttraj=True

    def checkExtension(self):
        if self.inst is None :
            self.inst = Installer(gui=False)
            self.inst.mgltoolsDir=MGL_ROOT
            self.inst.currDir=MGL_ROOT+"/MGLToolsPckgs/Pmv/hostappInterface/"
        self.inst.getExtensionDirFromFile()
        for i,ext in enumerate(self.inst.extensions):
            if self.inst.extdir[i] not in sys.path :
                sys.path.append(self.inst.extdir[i])
                if ext.lower() == 'modeller' :
                    sys.path.append(self.inst.extdir[i]+"/python2.5")
        if not self._useModeller:
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
        self.initWidgetId()
        #set the title
        self.SetTitle("ePMV") #set the title
        #create the menu
        self.MenuFlushAll()
        #feed menu
        self.menuGadget={}
        for menu in self.MENU_ID.keys():
            self.menuGadget[menu]=[]
            self.MenuSubBegin(menu)
            for item in self.MENU_ID[menu]:
                self.menuGadget[menu].append(self.MenuAddString(item["id"],item["name"]))#,self.buttonLoad)
            self.MenuSubEnd()
        self.MenuFinished()
        left, top, right, bottom =(10,10,10,1)#left, top, right, bottom
        #############################################################################
        #Hierarchy Options...TO DO
        #self.GroupBegin(id=0,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                         #                 cols=4, rows=1)
        #self.GroupBorderSpace(1, 1, 1, 1)
        #self.add_label(label="1. Make each atom a child of :",flags=gui.BFH_LEFT)
        #self._defaultTree = self.AddCheckbox(flags=gui.BFH_CENTER,label='Mol',width=60,default=True,event=self.setTree)
        #self._perResTree = self.AddCheckbox(flags=gui.BFH_CENTER,label='Res',width=60,event=self.setTree)
        #self._perAtomTree = self.AddCheckbox(flags=gui.BFH_CENTER,label='Atms',width=60,event=self.setTree)
        #self.GroupEnd()
        #############################################################################
        #Load Molecule
        self.GroupBegin(id=0,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                           cols=3, rows=1)
        self.GroupBorderSpace(left, top, right, bottom)
        self.AddButton(id=self.LOAD_BTN["id"], flags=gui.BFH_LEFT | gui.BFV_MASK,
                            initw=self.LOAD_BTN["width"],
                            inith=self.LOAD_BTN["height"],
                            name=self.LOAD_BTN["name"])
        self.add_label(self.LABEL_ID[0],flags=gui.BFH_LEFT)
        self.add_label(self.LABEL_ID[1],flags=gui.BFH_LEFT)
        self.GroupEnd()
        self.GroupBegin(id=1,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                           cols=3, rows=1)
        self.GroupBorderSpace(left, 1, right, bottom)

        self.file=self.AddEditText(id=self.EDIT_TEXT["id"],flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                            initw=120)
        #self.SetString(self.file,'1CRN')
        
        self._pdbtype=self.AddComboBox(id=self.COMB_BOX["pdbtype"]["id"],flags=gui.BFH_LEFT,initw=56)
        map(lambda x,box=self._pdbtype:self.AddChild(box,x[0],x[1]),enumerate(self.pdbtype))
        self.AddButton(id=self.FETCH_BTN["id"], flags=gui.BFH_LEFT | gui.BFV_MASK,
                            initw=self.FETCH_BTN["width"],
                            inith=self.FETCH_BTN["height"],
                            name=self.FETCH_BTN["name"])
        self.GroupEnd()
        self.AddSeparatorH(200,flags=gui.BFH_SCALEFIT | gui.BFV_MASK)
        #############################################################################
        #DashBoard / Display Options
        self.GroupBegin(id=1,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                       cols=2, rows=1)
        self.GroupBorderSpace(left, top, right, bottom)                       
        #molecule menu
        self.add_label(self.LABEL_ID[2],flags=gui.BFH_LEFT)
        self._box=self.AddComboBox(id=self.COMB_BOX["mol"]["id"],flags=gui.BFH_SCALEFIT,initw=60)
        #self.add_label(self.LABEL_ID[1],flags=gui.BFH_LEFT)
        
        #delete command
#        self.AddButton(id=self.DEL_BTN["id"], flags=gui.BFH_SCALEFIT,
#                            initw=self.DEL_BTN["width"],
#                            inith=self.DEL_BTN["height"],
#                            name=self.DEL_BTN["name"])
        self.GroupEnd()
        self.GroupBegin(id=1,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                       cols=2, rows=1)
        self.GroupBorderSpace(left, top, right, bottom)                       
       
        #selection text area
        self.add_label(self.LABEL_ID[3],flags=gui.BFH_LEFT)
        self._keywordtype=self.AddComboBox(id=self.COMB_BOX["keyword"]["id"],flags=gui.BFH_LEFT,initw=80)
        map(lambda x,box=self._keywordtype:self.AddChild(box,x[0],x[1]),enumerate(self.keyword))
        #self.add_label(self.LABEL_ID[14],flags=gui.BFH_LEFT)
        self.GroupEnd()
        self.GroupBegin(id=1,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                       cols=2, rows=1)
        self.GroupBorderSpace(left, 1, right, bottom)                       
        self.selection=self.AddEditText(id =self.SELEDIT_TEXT["id"],
                                        flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                                        initw=150)
        self.SetString(self.SELEDIT_TEXT["id"],
                       '(Mol:Ch:Rletter:Atom), eg "1CRN:A:ALA:CA", or keywords: BACKBONE, SIDECHAINS, etc...')
        
        self.AddComboBox(id=self.COMB_BOX["selection"]["id"],flags=gui.BFH_LEFT,initw=80)
        map(lambda x,box=self.COMB_BOX["selection"]["id"]:self.AddChild(box,x[0],x[1]),
            enumerate(self.editselection))
        
        self.GroupEnd()
        self.GroupBegin(id=4,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                       cols=2, rows=1)
        self.GroupBorderSpace(left, 1, right, bottom)
        self.AddButton(id=self.SEL_BTN["deleteA"]["id"], flags=gui.BFH_LEFT,
                        initw=self.SEL_BTN["deleteA"]["width"],
                        inith=self.SEL_BTN["deleteA"]["height"],
                        name=self.SEL_BTN["deleteA"]["name"]) 
        self.add_label(self.LABEL_ID[11],flags=gui.BFH_SCALEFIT)
        self.GroupEnd()
        self.AddSeparatorH(200,flags=gui.BFH_SCALEFIT | gui.BFV_MASK)
        #############################################################################
        self.GroupBegin(id=2,flags=gui.BFH_SCALEFIT,cols=2, rows=12)
        self.GroupBorderSpace(left, top, right, bottom)                       
        self.add_label(self.LABEL_ID[8],flags=gui.BFH_LEFT)
        self._preset=self.AddComboBox(id=self.COMB_BOX["preset"]["id"],flags=gui.BFH_SCALEFIT,initw=60)
        map(lambda x,box=self._preset:self.AddChild(box,x[0],x[1]),enumerate(self.presettype))
        self.GroupEnd()
        
        #the different representation and there options
        self.GroupBegin(id=2,flags=gui.BFH_SCALEFIT,cols=3, rows=12)
        self.GroupBorderSpace(left, top, right, bottom)                       
       
        self.cpk=self.AddCheckbox(id=self.CHECKBOXS["cpk"]["id"],flags=gui.BFH_SCALEFIT,
                                name=self.CHECKBOXS["cpk"]["name"],
                                initw=self.CHECKBOXS["cpk"]["width"],
                                inith=self.CHECKBOXS["cpk"]["height"])
        self.ss=self.AddCheckbox(id=self.CHECKBOXS["ss"]["id"],flags=gui.BFH_SCALEFIT,
                                name=self.CHECKBOXS["ss"]["name"],
                                inith=self.CHECKBOXS["ss"]["height"],
                                initw=self.CHECKBOXS["ss"]["width"])
        self.surf=self.AddCheckbox(id=self.CHECKBOXS["surf"]["id"],flags=gui.BFH_SCALEFIT,
                                name=self.CHECKBOXS["surf"]["name"],
                                inith=self.CHECKBOXS["surf"]["height"],
                                initw=self.CHECKBOXS["surf"]["width"])
      
        self.cpk_slider=self.AddEditSlider(id=self.SLIDERS["cpk"]["id"],
                                            flags=gui.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["cpk"]["width"])
        self.SetFloat(self.cpk_slider,1.00,0.,  10., 0.01)
        self.loft=self.AddCheckbox(id=self.CHECKBOXS["loft"]["id"],flags=gui.BFH_SCALEFIT,
                                name=self.CHECKBOXS["loft"]["name"],
                                inith=self.CHECKBOXS["loft"]["height"],
                                initw=self.CHECKBOXS["loft"]["width"])
        self.msms_slider=self.AddEditSlider(id=self.SLIDERS["surf"]["id"],
                                            flags=gui.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["surf"]["width"])
        self.SetFloat(self.msms_slider,1.50,0.001,  19.99, 0.1)
        
        self.bs=self.AddCheckbox(id=self.CHECKBOXS["bs"]["id"],flags=gui.BFH_SCALEFIT,
                                name=self.CHECKBOXS["bs"]["name"],
                                inith=self.CHECKBOXS["bs"]["height"],
                                initw=self.CHECKBOXS["bs"]["width"])
        self.armature=self.AddCheckbox(id=self.CHECKBOXS["arm"]["id"],flags=gui.BFH_SCALEFIT,
                                name=self.CHECKBOXS["arm"]["name"],
                                inith=self.CHECKBOXS["arm"]["height"],
                                initw=self.CHECKBOXS["arm"]["width"])
        self.cms=self.AddCheckbox(id=self.CHECKBOXS["cms"]["id"],flags=gui.BFH_SCALEFIT,
                                name=self.CHECKBOXS["cms"]["name"],
                                inith=self.CHECKBOXS["cms"]["height"],
                                initw=self.CHECKBOXS["cms"]["width"])
 
        self.bs_slider=self.AddEditSlider(id=self.SLIDERS["bs_s"]["id"],
                                            flags=gui.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["bs_s"]["width"])
        self.SetFloat(self.bs_slider,1.00,0.,  10., 0.01)
        self.spline=self.AddCheckbox(id=self.CHECKBOXS["spline"]["id"],flags=gui.BFH_SCALEFIT,
                                name=self.CHECKBOXS["spline"]["name"],
                                inith=self.CHECKBOXS["spline"]["height"],
                                initw=self.CHECKBOXS["spline"]["width"])
        self.cms_slider=self.AddEditSlider(id=self.SLIDERS["cmsI"]["id"],
                                            flags=gui.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["cmsI"]["width"])
        self.SetFloat(self.cms_slider,7.10,0.001,  15., 0.1)
      
        self.bs_ratio=self.AddEditSlider(id=self.SLIDERS["bs_r"]["id"],
                                            flags=gui.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["bs_r"]["width"])
        self.SetFloat(self.bs_ratio,1.50,0.,  10., 0.01)
        self.meta=self.AddCheckbox(id=self.CHECKBOXS["meta"]["id"],flags=gui.BFH_SCALEFIT,
                                name=self.CHECKBOXS["meta"]["name"],
                                inith=self.CHECKBOXS["meta"]["height"],
                                initw=self.CHECKBOXS["meta"]["width"])
        self.cms_res_slider=self.AddEditSlider(id=self.SLIDERS["cmsR"]["id"],
                                            flags=gui.BFH_SCALEFIT, 
                                            initw=self.SLIDERS["cmsR"]["width"])
        self.SetFloat(self.cms_res_slider,-0.30,-20.,  -0.001, 0.01)
          
        self.GroupEnd()
        #color what is check as display        
        self.GroupBegin(id=3,flags=gui.BFH_SCALEFIT,
                       cols=3, rows=12)
        self.GroupBorderSpace(left, top, right, bottom)                       
        self.add_label(self.LABEL_ID[4],flags=gui.BFH_LEFT)
        self._color=self.AddComboBox(id=self.COMB_BOX["col"]["id"],flags=gui.BFH_SCALEFIT,initw=206)
        self.AddChild(self._color,0,'Atoms using CPK')        #2018
        self.AddChild(self._color,1,'AtomsDG (polarity/charge)')        #2019
        self.AddChild(self._color,2,'Per residue')      #2020  
        self.AddChild(self._color,3,'Secondary Structure')      #2021?
        self.AddChild(self._color,4,'Custom color')      #2022?
        self.AddChild(self._color,5,'Rainbow from N to C')     #2022?
        self.AddChild(self._color,6,'Chains')     #2022?
        self.AddChild(self._color,7,'Temperature Factor')     #2022?
        self.AddChild(self._color,8,'sas area')
        self.unic_color=self.AddColorField(id=self.COLFIELD["id"],flags=gui.BFH_LEFT, 
                                     initw=30,inith=15)

        self.GroupEnd()
        self.AddSeparatorH(200,flags=gui.BFH_SCALEFIT | gui.BFV_MASK)
        #############################################################################
        self.GroupBegin(id=4,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                       cols=3, rows=1)
        self.GroupBorderSpace(left, top, right, bottom)
        self.AddButton(id=self.DATA_BTN["id"], flags=gui.BFH_LEFT | gui.BFV_MASK,
                    initw=self.DATA_BTN["width"],
                    inith=self.DATA_BTN["height"],
                    name=self.DATA_BTN["name"])
        self.add_label(self.LABEL_ID[5],flags=gui.BFH_LEFT)
        self._datatype=self.AddComboBox(id=self.COMB_BOX["datatype"]["id"],flags=gui.BFH_LEFT,initw=80)
        map(lambda x,box=self._datatype:self.AddChild(box,x[0],x[1]),enumerate(self.datatype))
#        self.trajectoryfile=self.AddEditText(id=self.DATA_TEXT["id"],flags=gui.BFH_SCALEFIT | gui.BFV_MASK)
#        self.AddButton(id=self.DATA_BTN["id"], flags=gui.BFH_LEFT | gui.BFV_MASK,
#                            initw=self.DATA_BTN["width"],
#                            inith=self.DATA_BTN["height"],
#                            name=self.DATA_BTN["name"])
        self.GroupEnd()
        #self.AddSeparatorH(200,flags=gui.BFH_SCALEFIT | gui.BFV_MASK)
        #############################################################################
        self.GroupBegin(id=4,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                       cols=3, rows=1)
        self.GroupBorderSpace(left, top, right, bottom)
        self.add_label(self.LABEL_ID[9],flags=gui.BFH_LEFT)
        self.trajbox=self.AddComboBox(id=self.COMB_BOX["dat"]["id"],flags=gui.BFH_LEFT,initw=60)
        self.add_label(self.LABEL_ID[6],flags=gui.BFH_SCALEFIT)
        self.GroupEnd()
        self.GroupBegin(id=4,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                       cols=1, rows=1)
        self.GroupBorderSpace(left, 1, right, bottom)        
        self.slider=self.AddEditSlider(id=self.SLIDERS["datS"]["id"],
                                            flags=gui.BFH_SCALEFIT | gui.BFV_MASK, 
                                            initw=self.SLIDERS["datS"]["width"])
        #self.dataVal = self.AddEditNumberArrows(id=self.SLIDERS["datV"]["id"], 
        #                                        flags=gui.BFH_LEFT, initw=100)
        #self.SetInt(self.slider,0,0,1000,1)                                        
        #self.SetFloat(self.dataVal,0.,-300.,300.,0.01)
#        self.AddButton(id=self.KEY_BTN["id"], flags=gui.BFH_LEFT | gui.BFV_MASK,
#                            initw=self.KEY_BTN["width"],
#                            inith=self.KEY_BTN["height"],
#                            name=self.KEY_BTN["name"])
        self.GroupEnd()
        self.AddSeparatorH(200,flags=gui.BFH_SCALEFIT | gui.BFV_MASK)
        #############################################################################

        self.GroupBegin(id=5,flags=gui.BFH_SCALEFIT,
                       cols=3, rows=10)
        self.GroupBorderSpace(left, top, right, bottom)                       
        self.add_label(self.LABEL_ID[7],flags=gui.BFH_LEFT)
        
        self.AddComboBox(id=self.COMB_BOX["scriptO"]["id"],flags=gui.BFH_LEFT,initw=56)
        map(lambda x,box=self.COMB_BOX["scriptO"]["id"]:self.AddChild(box,x[0],x[1]),enumerate(self.scriptliste))

        self.AddComboBox(id=self.COMB_BOX["scriptS"]["id"],flags=gui.BFH_LEFT,initw=56)
        map(lambda x,box=self.COMB_BOX["scriptS"]["id"]:self.AddChild(box,x[0],x[1]),enumerate(self.scriptsave))

        self.GroupEnd()
        
        self.GroupBegin(id=5,flags=gui.BFH_SCALEFIT,
                       cols=1, rows=10)
        self.GroupBorderSpace(left, 5, right, bottom)                
        
        #self.add_label(label="the molecular viewer is also available in the sandbox (import c4d;c4d.mv;)")
        self.pmvcmds=self.AddMultiLineEditText(id=6,flags=gui.BFH_SCALEFIT|gui.BFV_SCALEFIT, 
                                     initw=100, inith=150, style=gui.DR_MULTILINE_SYNTAXCOLOR)
        self.SetString(self.pmvcmds,
        """
        
print 'put your own commands here'
print 'with self = PMV instance, and epmv as ePMV'
        """)
        self.AddButton(self.PMV_BTN["id"],flags=gui.BFH_SCALEFIT,
                       name=self.PMV_BTN["name"],initw=80)
        #no banner but we can put the label version
        self.AddStaticText(7,flags=gui.BFH_LEFT)
        self.SetString(7,'welcome to ePMV '+__version__)
        self.GroupEnd()
        
        self.AddSeparatorH(200	,flags=gui.BFH_SCALEFIT | gui.BFV_MASK)
        #use instead StatusSetBar
        #banner
        self.bannerFile = MGL_ROOT+'/MGLToolsPckgs/Pmv/hostappInterface/banner.jpg'
        self.bannerBMP = bitmaps.BaseBitmap()
        self.bannerBMP.InitWith(self.bannerFile)
        self.bannerBC = c4d.BaseContainer()
        #self.banner = self.AddImage(self.bannerBMP, flags=gui.BFH_CENTER,  
        #                             width=self.bannerBMP.get_width(), 
        #                             height=self.bannerBMP.get_height())
        
        self.setupEPMV()
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
        ids = self.GetInt(self.COMB_BOX['scriptS']['id'])
        if ids == 0 : #Save
            filename = dir+'/'+self.scriptliste[self.GetInt(self.COMB_BOX['scriptO']['id'])]+'.py'
        else :
            filename = dir+'/user_script.py'
        f = open(filename,'w')
        f.write(commands)
        f.close()
        
    def set_ePMVScript(self):
        from Pmv.hostappInterface import demo
        dir = demo.__path__[0]
        ids = self.GetInt(self.COMB_BOX['scriptO']['id'])
        if ids == 0 : #Open..ask for broser
            filename = c4d.storage.LoadDialog(c4d.FSTYPE_ANYTHING, "choose a python file")
        else :
            filename = dir+'/'+self.scriptliste[self.GetInt(self.COMB_BOX['scriptO']['id'])]+'.py'
        f = open(filename,'r')
        script = f.read()
        f.close()
        self.SetString(self.pmvcmds,script)
        
    def execPmvComds(self):
        cmds=self.GetString(self.pmvcmds)
        print len(cmds),cmds
        exec(cmds,{'self':self.mv,'epmv':self.epmv})   
        self.updateViewer()
        return True

    def epmv_update(self):
        #try to update ePMV
        if self.inst is None :
            self.inst=Installer(gui=False)
            self.inst.mgltoolsDir=MGL_ROOT
            self.inst.currDir=MGL_ROOT+"/MGLToolsPckgs/Pmv/hostappInterface/"
        import os.path
        if not os.path.exists(self.inst.currDir+'/epmv_dir.txt'):
            py4d_dir = c4d.storage.GeGetPythonPath()
            f=open(self.inst.currDir+'/epmv_dir.txt','w')
            f.write("Cinema4D:"+py4d_dir)
            f.close()
        self.inst.getDirFromFile()
        self.inst.updateCVS()
        self.inst.installC4d(update=True)
        #need a popup to says to restart
        
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
            
    def buttonBrowse(self):
        name = c4d.storage.LoadDialog(c4d.FSTYPE_ANYTHING, "choose a file")#, flags=0][, def_path])
        if name is not None:
            molname=os.path.splitext(os.path.basename(name))[0]       
            if molname in self.mv.Mols.name : self.mv.hostApp.driver.duplicatemol=True 
            #modeller ?
            #load in Modeller
            if self._useModeller :
                import modeller
                from modeller.scripts import complete_pdb
                mdl = complete_pdb(self.env, name)
                mdl.patch_ss()
                name = name.split(".pdb")[0]+"m.pdb"
                mdl.write(file=name)
            self.mv.readMolecule(name,log=1)
            if self._useModeller :
                self.mv.Mols[-1].mdl=mdl
            molname = self.mv.Mols[-1].name
        else :
            #dialog ?
            return True
        if molname in self.mv.Mols.name : self.mv.hostApp.driver.duplicatemol=False
        self.mv.assignAtomsRadii(molname, united=0, log=0, overwrite=1)
        print "Load ",molname,(self.GetInt(self._box))
        self.dash=True
        if self.firstmol :
            #self.set_up()#self.mv.iMol = {}
            #self.indice_mol=self.im
            self.mv.iMol[str(self.indice_mol)]=molname
            self.AddChild(self._box,self.indice_mol,molname)#self.mv.Mols[-1].name)
            #i=self.im
            #if self.restored : self.indice_mol=0
            self.SetInt(self._box, int(self.indice_mol))
            print (self.GetInt(self._box))
            self.indice_mol +=1         
            #self.indice_mol=int(self.get(self._box))
            self.firstmol=False
        else :
            print "new mol ",molname
            #self.addChildToMolMenu(molname)
            self.AddChild(self._box,int(self.indice_mol),molname)#self.mv.Mols[-1].name)
            self.mv.iMol[str(self.indice_mol)]=molname
            self.SetInt(self._box, int(self.indice_mol))
            self.indice_mol+=1
        if molname not in self.mv.molDispl.keys() :
            self.mv.molDispl[molname]=[False,False,False,False,False,None,None]
        if molname not in self.mv.MolSelection.keys() :
            self.mv.MolSelection[molname]={}
        if molname not in self.mv.selections.keys() :       
            self.mv.selections[molname]={}
        if molname not in self.mv.iMolData.keys() :       
            self.mv.iMolData[molname]=[]
        #test if multimodel
        mol = self.mv.getMolFromName(molname)
        if len(mol.allAtoms[0]._coords) > 1 or self._useModeller : 
            #need a test about trajectories...
            doit=True           
            if len(self.mv.iMolData[mol.name]) != 0 : #ok data
                for dataname in self.mv.iMolData[mol.name] : 
                    if dataname.find('xtc') != -1 : 
                        doit= False                             
            if doit : self.buttonLoadData(model=True)
        #make an attention message about CPK and B&S
        c4d.documents.GetActiveDocument().Message(c4d.MULTIMSG_UP)
        c4d.DrawViews(c4d.DA_ONLY_ACTIVE_VIEW|c4d.DA_NO_THREAD|c4d.DA_NO_ANIMATION)          
        return True
        
    def buttonLoad(self,filename=None,mname=None):
        #text = self.GetString(self.EDIT_TEXT["id"])
        print "buttonLoad", mname
        if mname is None:
            name= self.GetString(self.EDIT_TEXT["id"])
            if len(name) == 0:
                name = c4d.storage.LoadDialog(c4d.FSTYPE_ANYTHING, "choose a PDB file")#, flags=0][, def_path])
                if name is not None:
                    molname=os.path.splitext(os.path.basename(name))[0]       
                    if molname in self.mv.Mols.name : self.mv.hostApp.driver.duplicatemol=True 
                    #modeller ?
                    #load in Modeller
                    if self._useModeller :
                        import modeller
                        mdl = modeller.scripts.complete_pdb(self.env, name)
                        mdl.patch_ss()
                        name = name.split(".pdb")[0]+"m.pdb"
                        mdl.write(file=name)
                    self.mv.readMolecule(name,log=1)  
                    if self._useModeller :
                        self.mv.Mols[-1].mdl=mdl
                        molname = self.mv.Mols[-1].name
                else :
                    #dialog ?
                    return True
            else :    
                if len(name) == 4 or len(name.split(".")[0]) == 4 : #PDB CODE =>web download
                    molname=name.split(".")[0]
                    if molname in self.mv.Mols.name : self.mv.hostApp.driver.duplicatemol=True
                    #what is the selected pdbtype:
                    type = self.pdbtype[self.GetInt(self._pdbtype)]
                    self.mv.fetch.db = type
                    #print self.mv.fetch.db
                    mol = self.mv.fetch(name, f=self._forceFetch)
                    if mol is None :
                        return True
                else :                         
                    molname=os.path.splitext(os.path.basename(name))[0]       
                    if molname in self.mv.Mols.name : self.mv.hostApp.driver.duplicatemol=True       
                    if self._useModeller :
                        import modeller
                        mdl = modeller.scripts.complete_pdb(self.env, name)
                        mdl.patch_ss()
                        name = name.split(".pdb")[0]+"m.pdb"
                        mdl.write(file=name)
                    self.mv.readMolecule(name,log=1)  
                    if self._useModeller :
                        self.mv.Mols[-1].mdl=mdl
                        molname = self.mv.Mols[-1].name
                molname = self.mv.Mols[-1].name
            if molname in self.mv.Mols.name : self.mv.hostApp.driver.duplicatemol=False
            self.mv.assignAtomsRadii(molname, united=0, log=0, overwrite=1)
        else :
            molname=mname                
        print "Load ",molname,(self.GetInt(self._box))#should be 0
        self.dash=True
        if self.firstmol :
            #self.set_up()#self.mv.iMol = {}
            #self.indice_mol=self.im
            self.mv.iMol[str(self.indice_mol)]=molname
            self.AddChild(self._box,self.indice_mol,molname)#self.mv.Mols[-1].name)
            #i=self.im
            #if self.restored : self.indice_mol=0
            self.SetInt(self._box, int(self.indice_mol))
            print (self.GetInt(self._box))
            self.indice_mol +=1         
            #self.indice_mol=int(self.get(self._box))
            self.firstmol=False
        else :
            print "new mol ",molname
            #self.addChildToMolMenu(molname)
            self.AddChild(self._box,int(self.indice_mol),molname)#self.mv.Mols[-1].name)
            self.mv.iMol[str(self.indice_mol)]=molname
            self.SetInt(self._box, int(self.indice_mol))
            self.indice_mol+=1
        if molname not in self.mv.molDispl.keys() :
            self.mv.molDispl[molname]=[False,False,False,False,False,None,None]
        if molname not in self.mv.MolSelection.keys() :
            self.mv.MolSelection[molname]={}
        if molname not in self.mv.selections.keys() :       
            self.mv.selections[molname]={}
        if molname not in self.mv.iMolData.keys() :       
            self.mv.iMolData[molname]=[]
        #test if multimodel
        mol = self.mv.getMolFromName(molname)
        if len(mol.allAtoms[0]._coords) > 1 or self._useModeller : 
            #need a test about trajectories...
            doit=True           
            if len(self.mv.iMolData[mol.name]) != 0 : #ok data
                for dataname in self.mv.iMolData[mol.name] : 
                    if dataname.find('xtc') != -1 : 
                        doit= False                             
            if doit : self.buttonLoadData(model=True)
        #make an attention message about CPK and B&S
        c4d.documents.GetActiveDocument().Message(c4d.MULTIMSG_UP)
        c4d.DrawViews(c4d.DA_ONLY_ACTIVE_VIEW|c4d.DA_NO_THREAD|c4d.DA_NO_ANIMATION)          
        return True
        
    ##########################DATA COMMAND######################################
    def modelData(self,dataname=None,molname=None):
        if molname == None :
            mname,mol=self.getMolName()   
            trajname = mname+'_model'
            self.mv.iMolData[mname].append(trajname)
        else :
            mname = molname
            trajname = dataname                         
        if self.firsttraj:
            self.AddChild(self.trajbox,0,trajname)
            self.SetInt(self.trajbox, 0)
            self.mv.iTraj[self.indiceData]=[trajname,"model"]
            #self.set(self.trajbox, int(self.idata))
            #self.mv.iTraj[self.idata]=self.mv.Trajectories[trajname]
            self.firsttraj=False
            self.current_traj=[trajname,"model"]
            self.indiceData += 1
            #self.nF=len(self.current_traj.coords)
        else :
            self.AddChild(self.trajbox,self.indiceData,trajname)
            self.SetInt(self.trajbox, self.indiceData)
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
            self.SetInt(self.trajbox, 0)
            self.mv.iTraj[0]=[self.mv.Trajectories[trajname],"traj"]
            #self.set(self.trajbox, int(self.idata))
            #self.mv.iTraj[self.idata]=self.mv.Trajectories[trajname]
            self.firsttraj=False
            self.current_traj=[self.mv.Trajectories[trajname],"traj"]
            self.nF=len(self.current_traj[0].coords)
            self.indiceData += 1
        else :
            self.add_child(self.trajbox,self.indiceData,trajname)#first traj is 2040
            self.SetInt(self.trajbox,self.indiceData)
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
            self.SetInt(self.trajbox,0)
            self.indiceData += 1
            self.mv.iTraj[0]=[self.mv.grids3D[trajname],"grid"]
            #self.set(self.trajbox, int(self.idata))
            #self.mv.iTraj[self.idata]=self.mv.grids[trajname]
            self.firsttraj=False
            self.current_traj=[self.mv.grids3D[trajname],"grid"]
            self.nF=self.current_traj[0].maxi
        else :
            self.AddChild(self.trajbox,self.indiceData,os.path.basename(trajname))
            self.SetInt(self.trajbox, int(self.indiceData))        
            nTraj=len(self.mv.grids3D.keys())
            self.mv.iTraj[self.indiceData]=[self.mv.grids3D[trajname],"grid"]
            self.indiceData += 1   
            #self.mv.iTraj[self.idata+nTraj-1]=self.mv.grids[trajname]

    def buttonLoadData(self,model=False,trajname=None,molname=None):
        if trajname == None :
            if model : 
                self.modelData()
                return True
            #filename=self.GetString(self.trajectoryfile)
            #if len(filename) == 0 :
            filename = c4d.storage.LoadDialog(c4d.FSTYPE_ANYTHING, 
                                                  "choose a file (.xct,.mrc,...)")
            if filename is None :
                    return True
            #else :
            extension=os.path.splitext(os.path.basename(filename))[1] #.xtc,.trj,etc..
            if extension == '.xtc' : self.gromacsTraj(file=filename)
            else : self.gridData_2(file=filename)
            #elif extension == '.map' : self.gridData_1(file=filename)
        else :
           print "restore ",trajname, trajname.find("_model")       
           if trajname.find("_model") != -1 : #model conformation data
               self.modelData(dataname=trajname,molname=molname)          
           elif trajname.find("xtc") != -1 : #gromacs conformation data
               self.gromacsTraj(dataname=trajname,molname=molname)          
           else : #autodock map conformation data
               self.gridData_2(dataname=trajname,molname=molname)          
        #elif extension == '.trj' : self.amberTraj(filename)
        self.updateViewer()
        return True

    def updateTraj(self):
        traji=self.GetInt(self.trajbox)
        #print traji,self.mv.iTraj
        self.current_traj=self.mv.iTraj[traji]#[0]
        type = self.mv.iTraj[traji][1]
        print "type",type
        if type == "model":
            mname = self.current_traj[0].split("_")[0]
            mol = self.mv.getMolFromName(mname)
            nmodels=len(mol.allAtoms[0]._coords)
            mini=0
            maxi=nmodels
            default=0
            step=1
            doit=self.SetInt
        elif type == "traj":
            mini=0
            maxi=len(self.current_traj[0].coords)
            default=0
            step=1
            doit=self.SetInt
        elif type == "grid":
            mini=self.current_traj[0].mini
            maxi=self.current_traj[0].maxi
            default=self.current_traj[0].mean
            step=0.01
            doit=self.SetFloat
        doit(self.slider,default,mini,maxi,step)    
        self.updateViewer()
        return True

    def applyState(self):
        #frame=self.GetInt(self.slider)
        #print frame,self.current_traj
        if self.current_traj is not None : 
            if self.current_traj[1] == "model":
                #NRM or PDB multiModel
                mname = self.current_traj[0].split("_")[0]
                mol = self.mv.getMolFromName(mname) 
                nmodels=len(mol.allAtoms[0]._coords)
                conf = self.GetInt(self.slider)
                #self.SetFloat(self.dataVal,conf)
                mol.allAtoms.setConformation(conf)
                #self.mv.computeSecondaryStructure(mol.name,molModes={mol.name:'From Pross'})
                from Pmv.moleculeViewer import EditAtomsEvent                       
                event = EditAtomsEvent('coords', mol.allAtoms)
                #manually update Surf and SS
                #create mol.builder with sst / ss by residues!               
                for c in mol.chains :
                    #    tt=mol.builder.rc_ss(c)
                    #print mol.builder.sst[c.id]
                    self.epmv.helper.update_spline(mol.name+"_"+c.name+"spline",c.residues.atoms.get("CA").coords)
                    self.epmv.helper.updatePoly(mol.name+":"+c.name+"_cloud",vertices=c.residues.atoms.coords)
                    if self.mv.molDispl[mname][3] : self.updateSurf()
                    if self.mv.molDispl[mname][4] : self.updateCoarseMS()
                    #c4dutil.updateLines(mol.name+":"+c.name+"_line",chains=c)
                    #what about msms and coarseMS?
                    #need to recompute ss
                    #    c4dutil.update_2dsheet(c.sh,mol.builder.sst[c.id],c.loft)                                
                    #    print "surf ",self.mv.molDispl[mol.name][3]                   
                    #if self.mv.molDispl[mname][3]:
                    #    print "ss ",self.mv.molDispl[mol.name][2]
                self.mv.dispatchEvent(event)			   
            elif self.current_traj[1] == "grid":
                #grid3D
                mname,mol=self.getMolName()
                iso=self.GetFloat(self.slider)
                self.mv.isoC(self.current_traj[0],isovalue=iso,name=mname+"IsoSurface")       
            elif hasattr(self.current_traj,'GRID_DATA_FILE'):
                #grid
                iso=self.GetFloat(self.slider)
                self.mv.setIsovalue(self.current_traj[0].name,iso, log = 1)          
            else :
                mname,mol=self.getMolName()
                frame = self.GetInt(self.slider)
                self.current_traj[0].player.applyState(int(frame))
                for c in mol.chains :
                    #    tt=mol.builder.rc_ss(c)
                    #print mol.builder.sst[c.id]
                    self.epmv.helper.update_spline(mol.name+"_"+c.name+"spline",c.residues.atoms.get("CA").coords)
                    self.epmv.helper.updatePoly(mol.name+":"+c.name+"_cloud",vertices=c.residues.atoms.coords)
                    if self.mv.molDispl[mname][3] : self.updateSurf()
                    if self.mv.molDispl[mname][4] : self.updateCoarseMS()
        self.updateViewer()
        return True

    def updateViewer(self):
        c4d.documents.GetActiveDocument().Message(c4d.MULTIMSG_UP)       
        c4d.DrawViews(c4d.DA_ONLY_ACTIVE_VIEW|c4d.DA_NO_THREAD|c4d.DA_NO_ANIMATION)

    def drawPreset(self):
        #load,edit save representation preset
        pass

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
           self.SetInt(self._color,self.mv.molDispl[mname][5])
        if self.mv.molDispl[mname][6] != None :
           #the unic color 
           color=self.mv.molDispl[mname][6]      
           self.SetColorField(self.unic_color,color,1.0,1.0,0)
        if mname not in self.mv.Mols.name:
           #print mname,self.mv.MolSelection[mname.split("_")[0]][mname]
           self.SetString(self.selection,self.mv.MolSelection[mname.split("_")[0]][mname])
           if True in self.mv.molDispl[mname]: self.doDisplaySelection(self.mv.molDispl[mname])
        else : 
           self.SetString(self.selection,"")
           #if True in self.molDispl[mname]: self.doDisplaySelection(self.molDispl[mname],private)"""
        #print "update"
        #should apply the ds...or not ? lets try
        
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
        edit = self.GetInt(self.COMB_BOX['selection']['id'])
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
        print sel,mname, mol
        if sel is mol.name :
            #print sel,mname, mol , "del"
            res = c4d.gui.QuestionDialog("Are You sure you want to delete "+mol.name)
            if res : 
                self.deleteMol()
        else :
            selection = self.mv.select(sel,negate=False, only=True, xor=False, 
                                   log=0, intersect=False)
            if not isinstance(selection,Atom) : 
               selection = selection.findType(Atom)
            res = c4d.gui.QuestionDialog("Are You sure you want to delete the current selection "+sel)
            if res : 
                self.mv.deleteAtomSet(selection)
    
    def delete_Selection(self):
        #delete the dictionary relative to this selection
        pass

    def rename_Selection(self):
        pass

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
                                   self.GetInt(self._color),
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
        key=self.keyword[self.GetInt(self._keywordtype)]
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
            sel=mol.name+"::sidechain"
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
        val = self.GetInt(self._box)
        print "get ",val
        selname=""
        mname=""
        #print self.mv.iMol.keys()       
        if str(val) in self.mv.iMol.keys(): 
            selname=mname=self.mv.iMol[str(val)]
        elif str(val) in self.mv.iSel.keys() : #it is the selecetionname
            selname=self.mv.iSel[str(val)]                  
            mname=selname.split("_")[0]
        else : return "",None   
        mol=self.mv.getMolFromName(mname)
        print mol.name
        if forupdate: return selname,mol   
        return mname,mol


    #######DISPLAY COMMAND######################################################
    def displayMetaB(self):
        print "displayMetaB"
        return True

    def displayCPK(self):
        #c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        mname,mol=self.getMolName()
        if VERBOSE : print "CPK", mname
        scale = self.GetFloat(self.cpk_slider)   
        self.mv.hostApp.driver.use_instances=True
        sel=self.getSelectionLevel(mol)
        if VERBOSE : print "select ",sel
        selection = self.mv.select(sel,negate=False, only=True, xor=False, 
                                   log=0, intersect=False)
        if VERBOSE : print len(selection)
        if not isinstance(selection,Atom) : selection = selection.findType(Atom)
        maxi = len(selection)
        #print max
        #print "self.displayCPK('"+sel+"',log=1,negate=",(not self.get(self.cpk)),")" 
#        if max > 1000000000000. :
#           #need to fix this command LATER
#           #self.bc[gui.BFM_STATUSBAR_PROGRESSON] = True
#           self.epmv.helper.display_CPK(mol,selection,self.GetBool(self.cpk),needRedraw=False,
#                                quality=1,cpkRad=0.0,scaleFactor=float(scale),
#                                useTree=self.mv.hostApp.driver.useTree,dialog=None)
#        else :
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
        scale = self.GetFloat(self.bs_slider)
        ratio = self.GetFloat(self.bs_ratio)
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
        pRadius = self.GetFloat(self.msms_slider)
        if name in mol.geomContainer.geoms :
            self.mv.computeMSMS(sel, log=1, display=self.GetBool(self.surf), 
                               pRadius=pRadius, perMol=permol,surfName=name)
            #need to MenuAddString the color function
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
        option = self.GetFloat(self.cms_slider)
        res = self.GetFloat(self.cms_res_slider)
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
            self.epmv.helper.updateMesh(g,parent=parent, proxyCol=True,mol=mol)
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
        armature=self.epmv.helper.armature('armature'+mol.name,atoms,scn=doc,
                                           root=mol.geomContainer.masterGeom.obj)
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
        coli=int(self.GetInt(self._color))
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
        coli=int(self.GetInt(self._color))
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
            ma = max(selection.sas_area)
            mi = min(selection.sas_area)
            self.funcColor[5](selection, lGeom, 'sas_area',mini=float(mi),maxi=float(ma),
                               propertyLevel='Atom', colormap='rgb256',log=1)            
        else : self.funcColor[coli](sel, lGeom, log=1)
        self.mv.molDispl[mname][5]=coli
        self.updateViewer()
        return True       

    def drawPyAutoDock(self):
        self.ad.Open(async=True, pluginid=2555553, width=120, height=200)

    def drawPreferences(self):
        self.options.Open(async=True, pluginid=2555554, width=210, height=200)

    def modellerGUI(self):
        self.pd.Open(async=True, pluginid=2555555, width=120, height=200)

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
        maxit = self.pd.GetInt(self.pd.NUMBERS['miniIterMax']['id'])
        mol.pmvaction.store = self.pd.GetBool(self.pd.CHECKBOXS['store']['id'])
        cg.optimize(atmsel, max_iterations=maxit, actions=mol.pmvaction)#actions.trace(5, trcfil))
        del cg
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
        maxit = self.pd.GetInt(self.pd.NUMBERS['mdIterMax']['id'])
        temp = self.pd.GetFloat(self.pd.NUMBERS['mdTemp']['id'])
        mol.pmvaction.store = self.pd.GetBool(self.pd.CHECKBOXS['store']['id'])
        print maxit,temp,mol.pmvaction.store
        md.optimize(atmsel, temperature=temp, max_iterations=int(maxit),actions=mol.pmvaction)
        del md
        return True

    def drawAbout(self):
        #just Draw a litlle windows of some about ePMV, like how,who, etc...
        #and PMV citation
        about="""ePMV designed by Ludovic Autin and Graham Jonhson.
Based on PMV created by Michel Sanner.
Develloped in the Molecular Graphics Laboratory directed by Arthur Olson.
        """
        c4d.gui.MessageDialog(about)


    def addExtensionGUI(self):
        input=c4d.gui.InputDialog("Enter the extension name follow by the directory\nSupported extension are: Modeller, Pyrosetta\n",
        "modeller:/Library/modeller/modlib")
        self.inst.addExtension(input)

    def launchBrowser(self):
        #launch the default interenet browser and open the ePMV wiki page
        import webbrowser
        webbrowser.open("http://mgldev.scripps.edu/projects/wiki/index.php/Main_Page")
        
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
        self.argui.Open(async=True, pluginid=2555556, width=120, height=200)
        

    #######EVENT COMMAND######################################################
    def Command(self, id, msg):
        c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        #check the id/event
        #Menu id
        for menu in self.MENU_ID.keys():
            for item in self.MENU_ID[menu]:
               if id==item["id"] :
                   if self.epmv.timer : self.timeFunction(item["action"])
                   else : item["action"]()
                   #return True
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
         return self.dialog.Open(async=True, pluginid=PLUGIN_ID,
                              width=270, height=375)
    
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
