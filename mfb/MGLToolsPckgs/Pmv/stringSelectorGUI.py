## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Ruth HUEY, Michel SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

import numpy.oldnumeric as Numeric, Tkinter, types, string
from DejaVu.viewerFns import checkKeywords
from MolKit.molecule import MoleculeSet, Atom, AtomSetSelector
from MolKit.protein import Protein, ProteinSetSelector, Residue, \
                ResidueSetSelector, Chain, ChainSetSelector
import tkMessageBox, tkSimpleDialog

from MolKit.stringSelector import StringSelector



class StringSelectorGUI(Tkinter.Frame):
    """ molEntry, chainEntry, resEntry, atomEntry
        molMB, chainMB, resSetMB, atomSetMB, #setsMB
        showBut,
        clearBut, acceptBut,  closeBut
    """
    
    entryKeywords = [
        'molWids',
        'molLabel',
        'molEntry',
        'chainWids',
        'chainLabel',
        'chainEntry',
        'resWids',
        'resLabel',
        'resEntry',
        'atomWids',
        'atomLabel',
        'atomEntry',
       ]

    menuKeywords = [
        'molMB',
        'chainMB',
        'resSetMB',
        'atomSetMB',
        ]

    buttonKeywords = [
        'showBut',
        'clearBut',
        ]

    masterbuttonKeywords = [
        'acceptBut',
        'closeBut'
        ]


    def __init__(self, master, check=0, molSet=MoleculeSet([]),
            userPref = 'cS', vf = None, all=1,  crColor=(0.,1.,0), 
            clearButton=True, showButton=True, sets=None, **kw):

        if not kw.get('packCfg'):
            self.packCfg = {'side':'top', 'anchor':'w','fill':'x'}

        self.sets = sets
        #all is a shortcut to use all of default values
        if 'all' in kw.keys():
            all = 1
        elif __debug__:
            if check:
                apply( checkKeywords, ('stringSelector', self.entryKeywords), kw)

        Tkinter.Frame.__init__(self, master)
        ##????
        Tkinter.Pack.config(self, side='left', anchor='w')

        
        #to make a stringSelector need vf, moleculeSet, selString
        self.master = master
        self.molSet = molSet
        self.residueSelector = ResidueSetSelector()
        self.atomSelector = AtomSetSelector()
        self.userPref = userPref
        self.vf = vf
        if not self.vf is None:
            self.addGeom(crColor)
        else:
            self.showCross = None
        self.molCts = {}
        self.chainCts = {}
        
        # optsDict includes defaults for all possible widgets
        # in practice
        # user can specify which widgets to put into gui
        d = self.optsDict = {}

        #first check for menubuttons:

        llists = [self.entryKeywords, self.menuKeywords, self.buttonKeywords]
        if all:
            if not clearButton:
                self.buttonKeywords.remove("clearBut")
            if not showButton:
                self.buttonKeywords.remove("showBut")
            for l in llists:
                for key in l:
                    d[key] = 1

        else:
            for l in llists:
                for key in l:
                    d[key] = kw.get(key)
            
                

        self.flexChildren = {
            'mol': ['molLabel', 'molEntry'],
            'chain': ['chainLabel', 'chainEntry'],
            'res': ['resLabel', 'resEntry'],
            'atom': ['atomLabel', 'atomEntry'],
            }
       
        for w in ['molWids', 'chainWids','resWids','atomWids']:
            if kw.get(w):
                lab = w[:-4]
                s = lab+'Label'
                d[s] = 1
                s1 = lab+'Entry'
                d[s1] = 1


        # instantiate all Tkinter variables (?)
        #DON"T HAVE ANY???
        self.buildTkVars()
       
        # only build requested widgets(?)
        self.buildifdDict()

        # build commandDictionary
        self.buildCmdDict()

        self.buildGUI()



    def buildifdDict(self):
        #to prevent dependency on InputFormDescr: put all widgets in a frame
        #this dictionary has default values for each widget
        self.ifdDict = {}
        self.ifdDict['topFrame'] = {'name': 'topFrame',
            'widgetType':Tkinter.Frame,
            'wcfg':{'relief': 'flat', 'bd':2}, 
            'packCfg':{'side':'top', 'fill':'x'}
            }
        self.ifdDict['buttonFrame'] = {'name': 'buttonFrame',
            'widgetType':Tkinter.Frame,
            'wcfg':{'relief': 'flat', 'bd':2}, 
            'packCfg':{'side':'top', 'fill':'x'}
            }
        self.ifdDict['entryFrame'] = {'name': 'entryFrame',
            'widgetType':Tkinter.Frame,
            'wcfg':{'relief': 'flat', 'bd':2}, 
            'packCfg':{'side':'left'}
            }
        self.ifdDict['menuFrame'] = {'name': 'menuFrame',
            'widgetType':Tkinter.Frame,
            'wcfg':{'relief': 'flat', 'bd':2}, 
            'packCfg':{'side':'left', 'fill':'x'}
            }
        self.ifdDict['molWids'] = {'name': 'molWids',
            'widgetType': Tkinter.Frame,
            'wcfg':{'relief': 'flat'},
            'children': ['molLabel', 'molEntry'],
            'packCfg':{'side':'top'}
            } 
        self.ifdDict['molLabel'] = {'name': 'molLabel',
            'widgetType':Tkinter.Label,
            'wcfg':{'text': 'Molecule'}, 
            'packCfg':{'side':'left', 'anchor': 'w', 'fill':'x'}
            }
        self.ifdDict['molEntry'] = {'name': 'molEntry',
            'widgetType':Tkinter.Entry,
            'wcfg':{'bd': 3}, 
            'packCfg':{'side':'left', 'anchor':'e', 'fill':'x'}
            }
        self.ifdDict['chainWids'] = {'name': 'chainWids',
            'widgetType': Tkinter.Frame,
            'wcfg':{'relief': 'flat', 'bd':3},
            'children': ['chainLabel', 'chainEntry'],
            'packCfg':{'side':'top'}
            } 
        self.ifdDict['chainLabel'] = {'name': 'chainLabel',
            'widgetType':Tkinter.Label,
            'wcfg':{'text': 'Chain    '}, 
            'packCfg':{'anchor': 'w', 'side':'left'}
            }
        self.ifdDict['chainEntry'] = {'name': 'chainEntry',
            'widgetType':Tkinter.Entry,
            'wcfg':{'bd': 3}, 
            'packCfg':{'side':'left', 'anchor':'e', 'fill':'x'}
            }
        self.ifdDict['resWids'] = {'name': 'resWids',
            'widgetType': Tkinter.Frame,
            'wcfg':{'relief': 'flat'},
            'children': ['resLabel', 'resEntry'],
            'packCfg':{'side':'top'}
            } 
        self.ifdDict['resLabel'] = {'name': 'resLabel',
            'widgetType':Tkinter.Label,
            'wcfg':{'text': 'Residue'}, 
            'packCfg':{'anchor': 'w', 'side':'left'}
            }
        self.ifdDict['resEntry'] = {'name': 'resEntry',
            'widgetType':Tkinter.Entry,
            'wcfg':{'bd': 3}, 
            'packCfg':{'side':'left', 'anchor':'e', 'fill':'x'}
            }
        self.ifdDict['atomWids'] = {'name': 'atomWids',
            'widgetType': Tkinter.Frame,
            'wcfg':{'relief': 'flat'},
            'children': ['atomLabel', 'atomEntry'],
            'packCfg':{'side':'top'}
            } 
        self.ifdDict['atomLabel'] = {'name': 'atomLabel',
            'widgetType':Tkinter.Label,
            'wcfg':{'text': 'Atom    '}, 
            'packCfg':{'anchor': 'w', 'side':'left'}
            }
        self.ifdDict['atomEntry'] = {'name': 'atomEntry',
            'widgetType':Tkinter.Entry,
            'wcfg':{'bd': 3}, 
            'packCfg':{'side':'left', 'anchor':'e', 'fill':'x'}
            }
        #next the menus
        self.ifdDict['molMB'] = {'name': 'molMB',
            'widgetType':Tkinter.Menubutton,
            'buildMenuCmd': self.buildMolMenu,
            'wcfg':{
                    'text': 'Molecule List',
                    'relief': 'ridge'},
            'packCfg':{'side':'top', 'anchor':'w', 'fill':'x'}}
        self.ifdDict['chainMB'] = {'name': 'chainMB',
            'widgetType':Tkinter.Menubutton,
            'buildMenuCmd': self.buildChainMenu,
            'wcfg':{
                    'text': 'Chain List',
                    'relief': 'ridge'},
            'packCfg':{'side':'top', 'anchor':'w', 'fill':'x'}}
        self.ifdDict['resSetMB'] = {'name': 'resSetMB',
            'widgetType':Tkinter.Menubutton,
            'buildMenuCmd': self.buildResMenus,
            'wcfg':{
                    'text': 'ResidueSet List',
                    'relief': 'ridge'},
            'packCfg':{'side':'top', 'anchor':'w', 'fill':'x'}}
        self.ifdDict['atomSetMB'] = {'name': 'atomSetMB',
            'widgetType':Tkinter.Menubutton,
            'buildMenuCmd': self.buildAtomMenus,
            'wcfg':{
                    'text': 'AtomSet List',
                    'relief': 'ridge'},
            'packCfg':{'side':'top', 'anchor':'w', 'fill':'x'}}
        #some way to toggle visual aide
        self.ifdDict['showBut'] = {'name': 'showBut',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{
                    'command': self.Show_cb,
                    'variable': self.showCurrent,
                    # should there be a box?
                    #'indicatoron':0,
                    'text':'Show ',
                    'relief':'raised',
                    'bd': '1'},
            'packCfg':{'side':'left', 'anchor':'w', 'fill':'x'}}
        #last the buttons
        self.ifdDict['clearBut'] = {'name': 'clearBut',
            'widgetType':Tkinter.Button,
            'wcfg':{
                    'command': self.Clear_cb,
                    'text':'Clear Form',
                    'relief':'raised',
                    'bd': '1'},
            'packCfg':{'side':'left', 'anchor':'w', 'fill':'x'}}
        self.ifdDict['acceptBut'] = {'name': 'acceptBut',
            'widgetType':Tkinter.Button,
            'wcfg':{
                    'command': self.get,
                    'text':'Accept',
                    'relief':'raised',
                    'bd': '1'},
            'packCfg':{'side':'left', 'anchor':'w', 'fill':'x'}}
        self.ifdDict['closeBut'] = {'name': 'closeBut',
            'widgetType':Tkinter.Button,
            'wcfg':{
                    'command': self.Close_cb,
                    'text':'Close ',
                    'relief':'raised',
                    'bd': '1'},
            'packCfg':{'side':'left', 'anchor':'w', 'fill':'x'}}


    def buildTkVars(self):
        self.showCurrent = Tkinter.IntVar()
        self.showCurrent.set(0)
        #for n in ['showCurrent']:
        #    exec('self.'+ n + '= Tkinter.IntVar()')
        #    exec('self.'+ n + '.set(0)')


    def addGeom(self, crColor):
        from DejaVu.Points import CrossSet
        #need to have  a new name if there is already a 'strSelCrossSet'
        # in the viewer...
        name = 'strSelCrossSet'
        ctr = 0
        for c in self.vf.GUI.VIEWER.rootObject.children:
            if c.name[:14]==name[:14]:
                ctr = ctr + 1
        if ctr>0:
            name = name + str(ctr)
        self.showCross=CrossSet(name,
            inheritMaterial=0, materials=(crColor,), 
            offset=0.5, lineWidth=2)
        self.showCross.Set(visible=1, tagModified=False)
        self.showCross.pickable = 0
        self.vf.GUI.VIEWER.AddObject(self.showCross)


    def bindMenuButton(self, mB, command, event='<ButtonPress>', add='+'):
        mB.bind(event, command, add=add)
               

    def buildMenu(self, mB, nameList, varDict, oldvarDict, cmd):
        if nameList:
            #prune non-valid entries
            for i in varDict.keys():
                if i not in nameList:
                    del varDict[i]
                    del oldvarDict[i]
            #add anything new
            for i in nameList:
                if i not in varDict.keys():
                    varDict[i]=Tkinter.IntVar()
                    oldvarDict[i]=0
        else:
            varDict={}
            oldvarDict={}
        #start from scratch and build menu
        #4/24: only build and add 1 menu
        if hasattr(mB, 'menu'):
            mB.menu.delete(1,'end')
        else:
            mB.menu = Tkinter.Menu(mB)
            mB['menu']=mB.menu
        #PACK all the entries
        for i in varDict.keys():
            mB.menu.add_checkbutton(label=i, var=varDict[i], command=cmd)


    def buildMolMenu(self,event=None):
        if not hasattr(self,'molVar'): self.molVar={}
        if not hasattr(self,'oldmolVar'): self.oldmolVar={}
        molNames = self.molSet.name
        self.buildMenu(self.molMB,molNames,self.molVar,self.oldmolVar,self.getMolVal)


    def buildChainMenu(self,event=None):
        if not hasattr(self,'chainVar'): self.chainVar={}
        if not hasattr(self,'oldchainVar'): self.oldchainVar={}
        chMols = MoleculeSet([])
        if len(self.molSet):
            chMols=MoleculeSet(filter(lambda x: Chain in x.levels, self.molSet))
        chainIDList = []
        if len(chMols):
            chains=chMols.findType(Chain)
            if chains==None: return
            for i in chains:
                chainIDList.append(i.full_name())
        self.buildMenu(self.chainMB,chainIDList,self.chainVar,self.oldchainVar,self.getChainVal)


    def buildResMenus(self,event=None):
        if not hasattr(self,'ResSetsVar'): self.ResSetsVar={}
        if not hasattr(self,'oldResSetsVar'): self.oldResSetsVar={}
        ResSetsList = self.residueSelector.residueList.keys()
        self.residueList = self.residueSelector.residueList
        #ResSetsList = residueList_.keys()
        #self.residueList = residueList_
        self.buildMenu(self.resSetMB,ResSetsList,self.ResSetsVar,self.oldResSetsVar,self.getResSetsVal)


    def buildAtomMenus(self,event=None):
        if not hasattr(self,'AtomSetsVar'): self.AtomSetsVar={}
        if not hasattr(self,'oldAtomSetsVar'): self.oldAtomSetsVar={}
        AtomSetsList = self.atomSelector.atomList.keys()
        self.atomList = self.atomSelector.atomList
        #AtomSetsList = atomList_.keys()
        #self.atomList = atomList_
        self.buildMenu(self.atomSetMB,AtomSetsList,self.AtomSetsVar,self.oldAtomSetsVar,self.getAtomSetsVal)

    
    def increaseCts(self,dict, newStr):
        if dict.has_key(newStr):
            dict[newStr]=dict[newStr]+1
        else:
            dict[newStr]=1


    def decreaseCts(self,dict,newStr):
        if dict.has_key(newStr):
            currentVal=dict[newStr]
            if currentVal<=1: currentVal=1
            dict[newStr]=currentVal-1


    def getMolVal(self, event=None):
        molWidget = self.molEntry
        for molStr in self.molVar.keys():
            #figure out which check button was just changed
            newVal=self.molVar[molStr].get()
            if newVal==self.oldmolVar[molStr]: continue
            else:
                self.oldmolVar[molStr]=newVal
            molList=string.split(molWidget.get(),',')
            if newVal==1:
                self.increaseCts(self.molCts,molStr)
                if not molStr in molList:
                    if molWidget.index('end')==0:
                        molWidget.insert('end',molStr) 
                    else: 
                        molWidget.insert('end',','+molStr) 
            else:
                if molStr in molList:
                    self.molCts[molStr]=0
                    molList.remove(molStr)
                    molWidget.delete(0,'end')
                    molWidget.insert('end',string.join(molList,','))
                    #also turn off all of the chain checkbuttons:
                    chainWidget=self.chainEntry
                    chainList=string.split(chainWidget.get(),',')
                    # chain menu may not have been built yet:
                    if not hasattr(self, 'chainVar'):
                        self.buildChainMenu()
                    for ch in self.chainVar.keys():
                        chKeyList = string.split(ch,':')
                        thisMolStr=chKeyList[0]
                        thisChainStr=chKeyList[1]
                        #if the chain is in this molecule
                        if thisMolStr==molStr:
                            #turn off chain checkbutton
                            self.chainVar[ch].set(0)
                            self.oldchainVar[ch]=0
                            self.decreaseCts(self.chainCts,thisChainStr)
                            if len(chKeyList)>1 and thisChainStr in chainList:
                                chainList.remove(thisChainStr)
                    chainWidget.delete(0,'end')   
                    chainWidget.insert('end',string.join(chainList,','))


    def getChainVal(self, event=None):
        chains = self.molSet.findType(Chain)
        molWidget = self.molEntry
        chainWidget = self.chainEntry
        for item in self.chainVar.keys():
            molStr,chainStr = string.split(item,':')
            newVal=self.chainVar[item].get()
            if newVal ==self.oldchainVar[item]:
                continue
            else:
                self.oldchainVar[item]=newVal
                molList=string.split(molWidget.get(),',')
                chainList=string.split(chainWidget.get(),',')
            if newVal==1:
                self.increaseCts(self.molCts,molStr)
                self.increaseCts(self.chainCts,chainStr)
                if not molStr in molList:
                    if molWidget.index('end')==0:
                        molWidget.insert('end',molStr)
                    else:
                        molWidget.insert('end',','+molStr)
                ###11/17:#if chainStr!=' ' and not chainStr in chainList:
                if  not chainStr in chainList:
                    if chainWidget.index('end')==0:
                        chainWidget.insert('end',chainStr)
                    else:
                        chainWidget.insert('end',','+chainStr)
                if hasattr(self, 'molVar') and self.molVar.has_key(molStr):
                    self.molVar[molStr].set(1)
                else: 
                    self.buildMolMenu()
                    self.molVar[molStr].set(1)
                self.oldmolVar[molStr]=1
            else:
                if not self.molCts.has_key(molStr): continue
                if not self.chainCts.has_key(chainStr): continue
                self.decreaseCts(self.molCts,molStr)
                self.decreaseCts(self.chainCts,chainStr)
                chainList=string.split(chainWidget.get(),',')
                ###11/17:#if chainStr in chainList or chainStr==' ': 
                if chainStr in chainList: 
                    if chainStr in chainList and self.chainCts[chainStr]==0:
                        chainList.remove(chainStr)
                    if self.molCts[molStr]==0:
                        if hasattr(self, 'molVar') and self.molVar.has_key(molStr):
                            self.molVar[molStr].set(0)
                            self.oldmolVar[molStr]=0
                        #also remove it from Molecule entry
                        molList=string.split(molWidget.get(),',')
                        if molStr in molList:molList.remove(molStr)
                        newss1=string.join(molList,',')
                        molWidget.delete(0,'end')
                        molWidget.insert('end',newss1)
                    ##also have to fix the Chain entry:
                    chainWidget.delete(0,'end')
                    chainWidget.insert('end',string.join(chainList,','))


    def getResSetsVal(self, event=None):
        w = self.resEntry
        ssList = string.split(w.get(),',')
        for newStr in self.ResSetsVar.keys():
            if self.ResSetsVar[newStr].get()==1:
                if newStr not in ssList:
                    if w.index('end')==0:
                        w.insert('end',newStr) 
                    else:
                        w.insert('end',',') 
                        w.insert('end',newStr) 
            #method to remove here
            else: 
                if newStr in ssList: 
                    ssList.remove(newStr)
                    w.delete(0,'end')
                    w.insert(0,string.join(ssList,','))


    def getAtomSetsVal(self, event=None):
        w = self.atomEntry
        ssList = string.split(w.get(),',')
        for newStr in self.AtomSetsVar.keys():
            if self.AtomSetsVar[newStr].get()==1:
                if newStr not in ssList:
                    if w.index('end')==0:
                        w.insert('end',newStr) 
                    else:
                        w.insert('end',',') 
                        w.insert('end',newStr) 
            #method to remove here
            else: 
                if newStr in ssList: 
                    ssList.remove(newStr)
                    w.delete(0,'end')
                    w.insert(0,string.join(ssList,','))


    def getSetsVal(self, event=None):
        if len(self.sets):
            sets = self.sets.keys()
        for newStr in self.setsVar.keys():
            node0 = self.sets[newStr][0]
            ##this would work only w/ 4 levels(/)
            nodeLevel = node0.isBelow(Protein)
            l = [self.molEntry, self.chainEntry, self.resEntry, self.atomEntry]
            w = l[nodeLevel]
            ssList=string.split(w.get(),',')
            if self.setsVar[newStr].get()==1:
                if newStr==' ': continue
                if not newStr in ssList:
                    if w.index('end')==0:
                        w.insert('end',newStr) 
                    else:
                        w.insert('end',',') 
                        w.insert('end',newStr) 
            else: 
                if newStr in ssList:
                    ssList.remove(newStr)
                    w.delete(0,'end')
                    w.insert(0,string.join(ssList,','))


    def buildArgs(self, event=None):
        kw = {}
        kw['mols'] = self.molEntry.get()        
        kw['chains'] = self.chainEntry.get()        
        kw['res'] = self.resEntry.get()        
        kw['atoms'] = self.atomEntry.get()        
        return kw


    def get(self, event=None, withMsg=False):
        args = self.buildArgs()
        atArg = self.atomEntry.get()        
        #print "atArg=", atArg, "=='' is", atArg==""
        resArg = self.resEntry.get()        
        #print "resArg=", resArg, "=='' is", resArg==""
        chainArg = self.chainEntry.get()        
        #print "chainArg=", chainArg, "=='' is", chainArg==""
        molArg = self.molEntry.get()        
        #print "molArg=", molArg, "=='' is", molArg==""
        if atArg!="":
            args = molArg + ':' + chainArg + ':' + resArg + ':' + atArg
        elif resArg!="":
            args = molArg + ':' + chainArg + ':' + resArg
        elif chainArg!="":
            args = molArg + ':' + chainArg
        else:  
            args = molArg
        #print "calling StringSelector.select with args=", args
        selitem, msgStr = StringSelector().select(self.molSet, args, sets=self.sets, caseSensitive=self.userPref)
        #if StringSelector starts returning msgs fix here
        #selitem, msgStr = StringSelector().select(self.molSet, args, self.userPref)
        #return selitem, msgStr
        #if selitem and len(selitem):
        #    print "returning len(selitem)=", len(selitem)
        if withMsg:
            return selitem, msgStr
        else:
            return selitem
    
        
    def set(self, val):
        valList = string.split(val, ',')
        if not len(valList)==4:
            delta = 4-len(valList)
            for i in range(delta):
                valList.append('')
        if valList[0]!="''":
            self.molEntry.insert('end', valList[0])
        if valList[1]!="''":
            self.chainEntry.insert('end', valList[1])
        if valList[2]!="''":
            self.resEntry.insert('end', valList[2])
        if valList[3]!="''":
            self.atomEntry.insert('end', valList[3])


    def Show_cb(self, event=None):
        if self.showCurrent.get():
            current = self.get()
            #if stringSelector starts returning msgs fix here
            #current, msgStr = self.get()
            if not self.vf:
                print 'nowhere to show'
                return
            if not current:
                msg = 'nothing to show'
                self.vf.warningMsg(msg, title='String Selector GUI WARNING:')
                self.showCurrent.set(0)
                return
            allAt = current.findType(Atom)
            if allAt is None or len(allAt)==0:
                self.showCross.Set(vertices=[], tagModified=False)
            else:
                self.showCross.Set(vertices = allAt.coords, tagModified=False)
        else:
            self.showCross.Set(vertices=[], tagModified=False)
        self.vf.GUI.VIEWER.Redraw()


    def Clear_cb(self, event=None):
        for item in [self.molEntry, self.chainEntry, self.resEntry, \
                self.atomEntry]:
            item.delete(0, 'end')
        #also have to turn off all the vars and reset all Cts
        ss1 = ['molVar', 'chainVar', 'ResSetsVar', \
                    'AtomSetsVar']
        dTkList = []
        for item in ss1:
            if hasattr(self, item):
                #dTkList.append(eval('self.'+item))
                dTkList.append(getattr(self, item))
        #dTkList = [self.molVar, self.chainVar, self.ResSetsVar, \
                    #self.AtomSetsVar]
        for d in dTkList:
            for k in d.keys():
                d[k].set(0)
        ss2 = ['oldmolVar', 'oldchainVar', 'oldResSetsVar',\
                    'oldAtomSetsVar']
        dintList = [self.molCts, self.chainCts]
        for item in ss2:
            if hasattr(self, item):
                #dintList.append(eval('self.'+item))
                dintList.append(getattr(self, item))
        #dintList = [self.oldmolVar, self.oldchainVar, self.oldResSetsVar,\
                    #self.oldAtomSetsVar]
        for d in dintList:
            for k in d.keys():
                d[k]=0
        if self.showCurrent.get():
            self.showCurrent.set(0)
            if self.showCross:
                self.showCross.Set(vertices=[], tagModified=False)
                self.vf.GUI.VIEWER.Redraw()


    def Close_cb(self, event=None):
        if self.showCross:
            self.showCross.Set(vertices=[], tagModified=False)
            self.vf.GUI.VIEWER.Redraw()
        self.master.withdraw()


    #def buildFileMenu(self, event=None):
    #    cmdList = [self.Close_cb]
    #    #cmdList = [self.Accept_cb, self.Close_cb]
    #    #fileOpts = ['Accept', 'Close']
    #    fileOpts = ['Close']
    #    if not self.showFileMenu.get():
    #        if not hasattr(self.fileMB, 'menu'):
    #            self.buildMenu(fileOpts, self.fileMB, None, None,
    #                type = 'button', cmdList = cmdList)
    #        self.showFileMenu.set(1)
    #    else:
    #        self.fileMB.menu.unpost()
    #        self.showFileMenu.set(0)


    #def buildHelpMenu(self, event=None):
        #tkMessageBox.showwarning('Warning',self.helpMsg)


    def buildCmdDict(self):
        self.cmdDict = {}
        for key, value in self.optsDict.items():
            if value: 
                if type(value) == types.DictionaryType and \
                        value.has_key('command'):
                    self.cmdDict[key] = value['command']
                elif key in self.ifdDict.keys() and self.ifdDict[key].has_key('command'):
                    self.cmdDict[key] = self.ifdDict[key]['command']


    def updateChildren(self):
        d = self.optsDict
        for key, chList in self.flexChildren.items():
            val = d[key]
            if val: 
                #set alternate children list
                for ch in chList:
                    d[ch] = val


    def buildFrame(self, widName, parent = None):
        
        #print 'in buildFrame with ', widName
        if parent==None:
            parent = self
        widDict = self.ifdDict[widName]
        newWid = apply(Tkinter.Frame, (parent,), widDict['wcfg'])
        exec('self.'+widName+'=newWid')
        apply(newWid.pack, (), widDict['packCfg'])
        

    def buildGUI(self):
        #first build Frames
        #which set up Menubar and rest
        #self.MBFrame = Tkinter.Frame(self.master, relief='raised')
        #widStrings =  ['MBFrame', 'WidFrame']
        self.buildFrame('topFrame' ) 
        self.buildFrame('buttonFrame' )
        widStrings =  ['entryFrame', 'menuFrame']
        keyList = [self.entryKeywords, self.menuKeywords]
        for num in range(2):
            wid = widStrings[num]
            widDict = self.ifdDict[wid]
            if self.optsDict.get(wid):
                for k, v in self.optsDict.get(wid).items():
                    if type(v) == types.DictionaryType:
                        for subk, subv in v.items():
                            widDict[k][subk] = subv
                    else: widDict[k] = v
            newWid = apply(Tkinter.Frame, (self.topFrame,), widDict['wcfg'])
            exec('self.'+wid+'=newWid')
            apply(newWid.pack, (), widDict['packCfg'])
            #if num==1: self.updateChildren()
            self.buildWidgets(keyList[num], newWid)
        self.buildWidgets(self.buttonKeywords, self.buttonFrame)
        self.buildWidgets(self.masterbuttonKeywords, self.buttonFrame)


    def buildWidgets(self, keyList, master):
        for key in keyList:
            value = self.optsDict.get(key)
            if not value:
                #skip this widget
                #print 'skipping ', key
                continue
            else:
                #first check whether there is a cfg 
                widDict = self.ifdDict[key]
                if value!=1:
                    #check whether it's a dictionary
                    for k, v in value.items():
                        if type(v) == types.DictionaryType:
                            for subk, subv in v.items():
                                widDict[k][subk] = subv
                        else: widDict[k] = v
                #make the widget here
                w = widDict['widgetType']
                del widDict['widgetType']

                #save possible pack info + command to bind
                widCallback = widDict.get('callBack')
                if widCallback: del widDict['callBack']
                packCfg = widDict.get('packCfg')
                if packCfg: del widDict['packCfg']
                else: packCfg = self.packCfg

                #save possible menuBuild cmds
                buildMenuCmd = widDict.get('buildMenuCmd')
                if buildMenuCmd: del widDict['buildMenuCmd']

                #if w==Tkinter.Menubutton: master = self.MBFrame
                #else: master = self.WidFrame
                newW = apply(w, (master,), widDict['wcfg'])

                if buildMenuCmd:
                    newW.bind('<ButtonPress>', buildMenuCmd, add='+')

                #frames have children to build and pack
                if widDict.has_key('children'):
                    for ch in widDict['children']:
                        if not self.optsDict.get(ch): continue
                        else:
                            #first grab any passed info
                            wD =self.ifdDict[ch]
                            opD = self.optsDict[ch]
                            if type(opD)==types.DictionaryType:
                                for k, v in opD.items():
                                    wD[k] = v
                            # mark this ch as done
                            self.optsDict[ch] = 0
                        ch_w = wD['widgetType']
                        del wD['widgetType']
                        childCallback = wD.get('callBack')
                        if childCallback: del wD['callBack']
                        childPackCfg = wD.get('packCfg')
                        if childPackCfg: del wD['packCfg']
                        else: childPackCfg = self.packCfg
                        newChild = apply(ch_w, (newW,), wD['wcfg'])
                        newChild.pack(childPackCfg)
                        exec('self.'+ch+'= newChild')
                        if childCallback: 
                            self.bindCallback(newChild, childCallback)
                    
                #if key=='spacing':
                    #newW.pack = newW.frame.pack

                
                #if key in ['fileMB', 'cenMB', 'visiMB', 'helpMB']:
                    #newW.bind('<ButtonPress>', cmdDict[key], add='+')

                newW.pack(packCfg)

                exec('self.'+key+'= newW')

                #check for a command to bind to newW
                if key in self.cmdDict.keys(): 
                    ##binding depends on type of widget
                    if newW.__class__==Tkinter.Scale:
                        newW.bind('<ButtonRelease>', widDict['command'])

                if widCallback:
                    self.bindCallback(newW, widCallback)


    def bindCallback(self, wid, cmdDict):
        if type(cmdDict)!=types.DictionaryType:
            #this is a cheap way to set up defaults
            cmdDict = {}
        event = cmdDict.get('event')
        if not event: event = '<ButtonPress>'
        add = cmdDict.get('add')
        if not add: add = '+'
        command = cmdDict.get('command')
        if not command: command = self.updateBox
        wid.bind(event, command, add=add)


    def returnEntries(self):
        #build list of requested options to return
        returnList=[]
        for item in self.dict.keys():
            if self.dict[item]:
                returnList.append(self.ifdDict['item'])
        return returnList
               


if __name__=='__main__':
    #code to test it here
    print 'testing stringSelector'
    import pdb
    
    root = Tkinter.Tk()
    root.withdraw()
    top = Tkinter.Toplevel()
    top.title = 'StringSelectorGUI'

    strSel = StringSelectorGUI(top, all = 1, crColor=(1.,0.,0.))

