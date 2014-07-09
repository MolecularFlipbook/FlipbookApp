# -*- coding: utf-8 -*-
"""
Created on Mon Sep 13 08:38:56 2010

@author: -
"""

#define the general parameter and function for gui
from Pmv.hostappInterface import comput_util as C

class ParameterModeller:
    def __init__(self,epmv=None):
        self.epmv = epmv
        id=1005
        self.NUMBERS = {"miniIterMax":{"id":id,"name":"max_iteration",'width':50,"height":10,"action":None},
                        "mdIterMax":{"id":id+1,"name":"max_iteration",'width':50,"height":10,"action":None},
                        "mdTemp":{"id":id+2,"name":"temperature",'width':50,"height":10,"action":None},
                        "rtstep":{"id":id+2,"name":"rtstep",'width':100,"height":10,"action":None},  
                        }
        id = id + len(self.NUMBERS) 
        self.BTN = {"mini":{"id":id,"name":"minimize",'width':50,"height":10,"action":None},
                    "md":{"id":id+1,"name":"MD",'width':50,"height":10,"action":None},
                    "cancel":{"id":id+2,"name":"Cancel",'width':50,"height":10,"action":None},
                    "update coordinate":{"id":id+3,"name":"Update coordinates",'width':100,"height":10,"action":self.updateCoord}
                    }
        id = id + len(self.BTN) 
        self.CHECKBOXS ={"store":{"id":id,"name":"store",'width':100,"height":10,"action":None},
                         "real-time":{"id":id+1,"name":"real-time",'width':100,"height":10,"action":None},
                        }
        
        id = id + len(self.CHECKBOXS) 
        self.COMB_BOX = {"sobject":{"id":id,"width":60,"height":10,"action":None},
                         "rtType":{"id":id+1,"width":60,"height":10,"action":None}}
        id = id + len(self.COMB_BOX)
        self.sObject = ["cpk","lines","bones","spline"]
        self.rtType = ["mini","md"]
        return True

#    def setRealTime(self):
#        pass
#
#    def setRealTimeStep(self):
#        pass
#
#    def minimize(self):
#        pass
#
#    def md(self):
#        pass
        
    def updateCoord(self):
        if hasattr(self.epmv,'gui'):
            mol = self.epmv.gui.current_mol
            if hasattr(mol,'pmvaction'):
                self.epmv.helper.updateMolAtomCoord(mol,mol.pmvaction.idConf,types=mol.pmvaction.sObject)
                mol.pmvaction.updateModellerCoord(mol.pmvaction.idConf,mol.mdl)       
        
class ParameterScoringGui:
    def __init__(self,epmv=None):
        self.epmv = epmv
        id=1005
        self.BTN = {"rec":{"id":id,"name":"Browse",'width':50,"height":10,
                           "action":None},
                    "lig":{"id":id+1,"name":"Browse",'width':50,"height":10,
                           "action":None},
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
                                  "height":10,"action":None},
                        "displayLabel":{"id":id+1,"name":"display Label",'width':100,
                                    "height":10,"action":None},
                        "colorRec":{"id":id+2,"name":"color Rec",'width':100,
                                    "height":10,"action":None},
                        "colorLig":{"id":id+3,"name":"color Lig",'width':100,
                                    "height":10,"action":None},
                        "realtime":{"id":id+4,"name":"real time",'width':100,
                                    "height":10,"action":self.setRealtime}
                                    }
        id = id + len(self.CHECKBOXS)
        return True

    def getScorerAvailable(self):
        self.scoreravailable = []
        if hasattr(self.epmv.mv,'energy'):
            self.scoreravailable = self.epmv.mv.energy.data.keys()

    def getScore(self):
        if hasattr(self.epmv.mv,'energy'):
            self.epmv.helper.get_nrg_score(self.epmv.mv.energy)

          

class parameter_epmvGUI:
    def __init__(self,epmv):
        self.epmv = epmv
        witdh=350
        id=1005
        #need to split in epmv options and gui options - >guiClass?
        self.EPMVOPTIONS = {}
        for key in self.epmv.keywords.keys() : 
            self.EPMVOPTIONS[key] = {"id": id, "name":self.epmv.keywords[key],'width':witdh,"height":10,"action":None}
            id = id +1
        self.GUIOPTIONS = {}
        for key in self.epmv.gui.keywords.keys():
            self.GUIOPTIONS[key] = {"id": id, "name":self.epmv.gui.keywords[key],'width':witdh,"height":10,"action":None}
            id = id +1
            
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
        
class epmvGui:
    keywords = {
        "_logConsole":"Console log",
        "_forceFetch":"Force web Fetch instead of pdb cache"
        }
    def __init__(self):
        id=0
        self.MENU_ID = {"File":
                      [{"id": id, "name":"Open PDB","action":self.buttonLoad},
                       {"id": id+1, "name":"Open Data","action":self.buttonLoadData}],
                       "Edit" :
                      [{"id": id+3, "name":"Options","action":self.drawPreferences}],
                       "Extensions" : [
                       {"id": id+4, "name":"PyAutoDock","action":self.drawPyAutoDock}
                       ],
                       "Help" : 
                      [{"id": id+5, "name":"About ePMV","action":self.drawAbout},
                       {"id": id+6, "name":"ePMV documentation","action":self.launchBrowser},
                       {"id": id+2, "name":"Check for Update","action":self.check_update},
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
        self.presettype=['available presets:','  Lines','  Liccorice','  SpaceFilling',
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
         
    
