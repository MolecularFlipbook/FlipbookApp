## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

############################################################################
#
# Author: Ruth HUEY, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

# $Header: /opt/cvs/python/packages/share1.5/Pmv/repairCommands.py,v 1.79.4.2 2011/04/06 18:05:20 rhuey Exp $
#
# $Id: repairCommands.py,v 1.79.4.2 2011/04/06 18:05:20 rhuey Exp $
#


from ViewerFramework.VFCommand import CommandGUI
from Pmv.moleculeViewer import AddAtomsEvent, DeleteAtomsEvent
##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.util.callback import CallBackFunction
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import \
                ExtendedSliderWidget, ListChooser
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel

from PyBabel.addh import AddHydrogens
from PyBabel.util import vec3

from Pmv.mvCommand import MVCommand, MVAtomICOM, MVBondICOM
from Pmv.qkollua import q

from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Atom, AtomSet, Bond, Molecule, MoleculeSet
from MolKit.molecule import BondSet
from MolKit.protein import Protein, ProteinSet, Chain, Residue, ResidueSet
from MolKit.pdbParser import PdbParser, PdbqParser, PdbqsParser
from MolKit.distanceSelector import CloserThanVDWSelector, DistanceSelector 
from MolKit.distanceSelector import CloserThanVDWPlusConstantSelector
from MolKit.pdbWriter import PdbWriter

from DejaVu.Geom import Geom
from DejaVu.Spheres import Spheres
from DejaVu.Points import CrossSet

from SimpleDialog import SimpleDialog
from Pmv.stringSelectorGUI import StringSelectorGUI

import Tkinter, numpy.oldnumeric as Numeric, math, types, Pmw

from DejaVu.glfLabels import GlfLabels


def check_repair_geoms(VFGUI):
    repair_geoms_list = VFGUI.VIEWER.findGeomsByName('repair_geoms')
    if repair_geoms_list==[]:
        repair_geoms = Geom("repair_geoms", shape=(0,0), protected=True)
        VFGUI.VIEWER.AddObject(repair_geoms, parent=VFGUI.miscGeom)
        repair_geoms_list = [repair_geoms]
    return repair_geoms_list[0]


class CheckForMissingAtomsGUICommand(MVCommand):
    """This class provides Graphical User Interface to CheckForMissingAtomsCommand which is invoked by it with the current selection, if there is one.
   \nPackage : Pmv
   \nModule  : repairCommands
   \nClass   : CheckForMissingAtomsGUICommand
   \nCommand : checkForMissingAtomsGC
   \nSynopsis:\n
        dictOfMissingAts <--- checkForMissingAtomsGC(nodes, **kw)
   \nRequired Arguments:\n     
        nodes --- TreeNodeSet holding the current selection
    """
    
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def onRemoveObjFromViewer(self, obj):
        if self.oldNode==obj:
            del self.oldNode


    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('labelByProperty'):
            self.vf.loadCommand('labelCommands', 'labelByProperty','Pmv',
                                topCommand=0)
        #self.vf.loadModule('labelCommands', 'Pmv')
        self.oldNode = None


    def __call__(self, nodes, **kw):
        """dictOfMissingAts <--- checkForMissingAtomsGC(nodes, **kw)
        \nnodes --- TreeNodeSet holding the current selection"""
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        resSet = nodes.findType(Residue).uniq()
        return apply( self.doitWrapper, (resSet,), kw )


    def doit(self, nodes):
        dict = self.vf.checkForMissingAtoms(nodes)
        resNames = []
        resSet = ResidueSet(dict.keys())
        for item in resSet:
            resNames.append(item.full_name())
            item.missing = str(dict[item])[1:-1]
        #put up a form here with button
        ifd = self.ifd=InputFormDescr(title = 'Check for MissingAtoms Results:')
        ifd.append({'name': 'numResErrsLabel',
            'widgetType': Tkinter.Label,
            'wcfg':{'text': str(len(resSet)) + ' Residues with missing atoms:'},
            'gridcfg':{'sticky': Tkinter.W+Tkinter.E}})
        ifd.append({'name': 'resLC',
            'widgetType':'ListChooser',
            'entries': resNames,
            #'defaultValue':resSet[0],
            'mode': 'single',
            #'mode': 'multiple',
            'gridcfg':{'row':2,'column':0},
            'title': '',
            #'command': CallBackFunction(self.showMissingRes, dict),
            'lbwcfg':{'height':5, 
                    'selectforeground': 'red',
                    'exportselection': 0,
                    'width': 30}})
        ifd.append({'name':'selAllBut',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Select All Residues',
                'command': self.selectAllRes},
            'gridcfg':{'sticky':Tkinter.W+Tkinter.E}})
        ifd.append({'name':'selCurrBut',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Select Current Residue',
                'command': CallBackFunction(self.selectCurRes, dict)
                    },
            'gridcfg':{'sticky':Tkinter.W+Tkinter.E}})
        ifd.append({'name':'closeBut',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Dismiss',
                'command': self.dismiss_cb},
            'gridcfg':{'sticky':Tkinter.W+Tkinter.E}})
        self.form  = self.vf.getUserInput(ifd, modal=0, blocking=0,
                scrolledFrame=1, width=337, height=305)
        self.form.root.protocol('WM_DELETE_WINDOW',self.dismiss_cb)



    def dismiss_cb(self, event=None):
        res = self.vf.Mols.chains.residues.get(lambda x: hasattr(x,'missing'))
        if res is not None:
            self.vf.labelByProperty(res, negate=1, topCommand=0)
        self.form.destroy()


    def selectAllRes(self, event=None):
        try:
            resSet = self.vf.Mols.chains.residues
        except AttributeError:
            self.warningMsg('no residues in viewer')
            return
        missingResSet = resSet.get(lambda x: hasattr(x, 'missing'))
        if not missingResSet:
            self.warningMsg('no residues missing atoms')
            return
        self.vf.select(missingResSet, topCommand=0)


    #def selectCurRes(self, dict, event=None):
    #    resSet = ResidueSet(dict.keys())
    #    lb = self.ifd.entryByName['resLC']['widget'].lb
    #    if lb.curselection() == (): return
    #    resName = lb.get(lb.curselection())
    #    resNode = self.vf.Mols.NodesFromName(resName)[0]
    #    self.vf.select(resNode, topCommand=0)


    #def showMissingRes(self, dict, event=None):
        #pass


    def selectCurRes(self, dict, event=None):
        resSet = ResidueSet(dict.keys())
        lb = self.ifd.entryByName['resLC']['widget'].lb
        #unlabel anything from the previous time
        if self.oldNode is not None:
            self.vf.labelByProperty(self.oldNode, properties = ("missing",), textcolor = "yellow", location = "Last", log = 0, font = "arial1.glf", negate=1)
            self.vf.select(self.oldNode.atoms, negate=1, topCommand=0)
        #if nothing new is selected, remember that via oldNode + return
        if lb.curselection() == (): 
            self.oldNode = None
            return
        #get new nodes to label
        resNodes = ResidueSet()
        for ind in lb.curselection():
            resName = lb.get(ind)
            resNodes.append( self.vf.Mols.NodesFromName(resName)[0])
        self.vf.clearSelection(topCommand=0)
        self.vf.setIcomLevel(Residue, topCommand=0)
        self.vf.setICOM(self.vf.select, modifier="Shift_L", topCommand=0)
        self.vf.labelByProperty(resNodes, properties = ("missing",), textcolor = "yellow", location = "Last", log = 0, font = "arial1.glf", only=1)
        self.vf.select(resNodes, topCommand=0)
        self.oldNode = resNodes


    def guiCallback(self):
        if self.vf.userpref['Expand Node Log String']['value'] == 0:
            self.vf.checkForMissingAtoms.nodeLogString = "self.getSelection()"
        sel=self.vf.getSelection()
        if len(sel):
            return self.doitWrapper(sel, topCommand=0)
        

checkForMissingAtomsGUICommandGuiDescr = {'widgetType':'Menu',
                                          'menuBarName':'menuRoot',
                                          'menuButtonName':'Edit',
                                          'menuCascadeName':'Misc',
                                          'menuEntryLabel':'Check For Missing Atoms '}


CheckForMissingAtomsGUICommandGUI = CommandGUI()
CheckForMissingAtomsGUICommandGUI.addMenuCommand('menuRoot', 'Edit',
                    'Check for Missing Atoms ', cascadeName='Misc')



class CheckForMissingAtoms(MVCommand):
    """This command compares atoms present in residues with those expected by the dictionary used to assign Kollman charges, qkollua. It returns a dictionary of whose keys are residues missing atoms and whose values are the names of the missing atoms.  The keys are strings built from the residue name + its chain id.
   \nPackage : Pmv
   \nModule  : repairCommands
   \nClass   : CheckForMissingAtomsCommand
   \nCommand : checkForMissingAtoms
   \nSynopsis:\n
        dictOfMissingAts <--- checkForMissingAtoms(nodes, **kw)
   \nRequired Arguments:\n        
        nodes --- TreeNodeSet holding the current selection
   """
    
    def onRemoveObjFromViewer(self, obj):
        if obj in self.resAts.keys():
            del self.resAts[obj]


    def onAddCmdToViewer(self):
        self.resAtomNum = {}
        self.resAts = {}
        self.resKeys = q.keys()
        for item in self.resKeys:
            self.resAtomNum[item] = len(q[item].keys())
            self.resAts[item] = q[item].keys()


    def doit(self, resSet):
        d = {}
        for res in resSet:
            resType = res.type
            if resType in self.resKeys and \
                len(res.atoms)<self.resAtomNum[resType]:
                ats = []
                for atName in self.resAts[resType]:
                    if atName not in res.atoms.name:
                        ats.append(atName)
                #nameStr = res.name + res.parent.id
                #d[nameStr] = ats
                d[res] = ats
        return d
        


    def __call__(self, nodes, **kw):
        """dictOfMissingAts <--- checkForMissingAtoms(nodes, **kw)
        \nnodes --- TreeNodeSet holding the current selection"""
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        resSet = nodes.findType(Residue).uniq()
        return apply( self.doitWrapper, (resSet,), kw )



from opengltk.OpenGL import GL


class CheckForCloseContactsGUICommand(MVCommand):
    """This class provides Graphical User Interface to CheckForCloseContactsCommand which is invoked by it
   \nPackage : Pmv
   \nModule  : repairCommands
   \nClass   : CheckForCloseContactsGUICommand
   \nCommand : checkForCloseContactsGC
   \nSynopsis:\n
        None <--- checkForCloseContactsGC(keynodes,checkNodes, percentCutoff,distanceCutoff, distSelectorString,**kw)
   \nRequired Arguments:\n
        keyNodes --- atoms to use as reference points
        \ncheckNodes --- atoms to check to see if close to keyNodes
   \nOptional Arguments:\n        
        percentCutoff --- vdw scaling factor
        \ndistanceCutoff --- distance for DistanceSelector
        \ndistSelectorString --- name of class of selector to use
        \nconstant --- possible constant value to be added into selection
\nclose is defined as interatomic distance< percentCutoff*(key_radius+check_radius) where the radii depend on atom element .
    """

    def onRemoveObjFromViewer(self, obj):
        if self.oldNode==obj:
            del self.oldNode


    def onAddCmdToViewer(self):
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('checkForCloseContacts'):
            self.vf.loadCommand('repairCommands', ['checkForCloseContacts'],
                                package='Pmv', topCommand=0)
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('saveSet'):
            self.vf.loadCommand('selectionCommands', ['saveSet'],
                                package='Pmv', topCommand=0)
    
        from DejaVu.IndexedPolylines import IndexedPolylines
        #from DejaVu.Labels import Labels

        self.masterGeom = Geom('closeContactGeoms',shape=(0,0), 
                                pickable=0, protected=True)
        self.masterGeom.isScalable = 0
        if self.vf.hasGui:
            repair_geoms = check_repair_geoms(self.vf.GUI)
            self.vf.GUI.VIEWER.AddObject(self.masterGeom, parent = repair_geoms)
        self.lines = IndexedPolylines('closeContLines', 
                    inheritMaterial=0,
                    materials=((1,0,0),), lineWidth=3, 
                    stippleLines=1, protected=True)
        self.labels = GlfLabels(name='closeContLabels', shape=(0,3),
                    inheritMaterial=0, materials=((1,.2,0),), 
                    billboard=True, fontStyle='solid', fontScales=(.3,.3,.3,))
        self.labels.font = 'arial1.glf'
        if self.vf.hasGui:
            self.vf.GUI.VIEWER.AddObject(self.lines, parent=self.masterGeom)
            self.vf.GUI.VIEWER.AddObject(self.labels, parent=self.masterGeom)
        self.vf.loadModule('labelCommands', 'Pmv')
        self.oldNode = None
        self.keyss_oldvalue = 0
        self.checkss_oldvalue = 0
        #initialize self.selector to 
        self.distSelectorDict = {'DistanceSelector':DistanceSelector,
                      'CloserThanVDWSelector': CloserThanVDWSelector,
                      'CloserThanVDWPlusConstant':CloserThanVDWPlusConstantSelector}
        self.distSelectorString = 'CloserThanVDWSelector'


    def __call__(self, keyNodes, checkNodes, percentCutoff=1.0, 
                        distanceCutoff=3.0, 
                        distSelectorString='CloserThanVDWSelector',
                        constant=0., showGUI=True, **kw):
        """None <--- checkForCloseContactsGC(keynodes,checkNodes, percentCutoff,distanceCutoff, distSelectorString,**kw)
        \nRequired Arguments:\n
            keyNodes --- atoms to use as reference points
            \ncheckNodes --- atoms to check to see if close to keyNodes
        \nOptional Arguments:\n
            percentCutoff --- vdw scaling factor
            \ndistanceCutoff --- distance for DistanceSelector
            \ndistSelectorString --- name of class of selector to use
            \nconstant --- possible constant value to be added into selection
            \nfor vdw selectors ,close is defined as interatomic distance< percentCutoff*(key_radius+check_radius) where the radii depend on atom element.
"""
        if type(keyNodes) is types.StringType:
            self.nodeLogString = "'"+keyNodes+"'"
        keyNodes = self.vf.expandNodes(keyNodes)
        if not len(keyNodes): return 'ERROR'
        if type(checkNodes) is types.StringType:
            self.nodeLogString = "'"+checkNodes+"'"
        checkNodes = self.vf.expandNodes(checkNodes)
        if not len(checkNodes): return 'ERROR'
        return apply( self.doitWrapper, (keyNodes, checkNodes, percentCutoff,
                                distanceCutoff, distSelectorString,
                                constant, showGUI), kw )


    def doit(self, keyNodes, checkNodes, percentCutoff, 
                distanceCutoff, distSelectorString,
                constant, showGUI=True):
        import time
        t1 = time.time()
        distSelectorClass = self.distSelectorDict[distSelectorString]
        kw = {'constant':constant}
        self.atDict, self.distDict = apply(self.vf.checkForCloseContacts,( keyNodes, 
                                checkNodes, percentCutoff, distanceCutoff,
                                distSelectorClass), kw)
        t2 = time.time()
        print 'Found them in ', t2-t1
        atDict = self.atDict
        distDict = self.distDict
        if not showGUI:
            return self.atDict, self.distDict
        #MUST GET RID of previous results window, else create a zombie...
        if hasattr(self, 'ifd_results'):
            #cleanup previous results here!?!
            self.dismiss_cb()
        if not len(atDict.keys()):
            self.warningMsg('no atoms with close contacts')
            return 
        atNames = []
        # to sort keys:
        ats = AtomSet(atDict.keys())
        ats.sort()
        atNames = []
        for a in ats:
            atNames.append((a.full_name(), None))
        #figure out what the height of the listbox should be
        result_height = len(ats)
        if result_height>10: 
            result_height = 10
        ifd = self.ifd_results=InputFormDescr(title = 'Check for CloseContacts Results:')
        ifd.append({'name': 'closeContactLabel',
            'widgetType': Tkinter.Label,
            'wcfg':{'text': str(len(atNames)) + ' Atom(s) with Close Contacts:\nred:dist<criteria; green:dist<VDWsum*factor'},
            'gridcfg':{'sticky': Tkinter.W+Tkinter.E,'columnspan':2}})
        ifd.append({'name': 'atsLC',
            #'widgetType':'ListChooser',
            'widgetType':ListChooser,
            'wcfg':{ 'entries': atNames,
                    'mode': 'single',
                    'withComment':0,
                    'title': '',
                    'command': CallBackFunction(self.showCloseContacts, atDict, distDict),
                    'lbwcfg':{'height':result_height, 
                              'selectforeground': 'red',
                              'exportselection': 0,
                              #'lbpackcfg':{'fill':'both','expand':1},
                              'width': 30}},
                    'gridcfg':{'row':2,'column':0, 
                                'columnspan':2, 'sticky':'ew'}})
                        #'sticky':Tkinter.W+Tkinter.E+Tkinter.N+Tkinter.S},
        ifd.append({'name':'showAllBut',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Show All ',
                'command': CallBackFunction(self.showAllCloseContacts, \
                        atDict ,distDict)},
            'gridcfg':{'sticky':'wens'}})
        ifd.append({'name':'saveSetsBut',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Save as 2 sets',
                'command': self.save_sets,},
            'gridcfg':{'sticky':'nesw',
                        'row':-1, 'column':1 }})
        ifd.append({'name':'closeBut',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Dismiss',
                'command': self.dismiss_cb},
            'gridcfg':{'sticky':'nesw', 'columnspan':2}})
        self.result_form  = self.vf.getUserInput(ifd, modal=0, blocking=0,
                scrolledFrame=1)#, width=340, height=240)
        self.result_form.root.protocol('WM_DELETE_WINDOW',self.dismiss_cb)
        #1/27: show all results
        self.showAllCloseContacts(atDict, distDict)
        t3 = time.time()
        print 'displayed them in ', t3-t2


    def cleanupDicts(self, atDict, distDict):
        for at in atDict.keys():
            closeAts = atDict[at]
            dists = distDict[at]
            bondedAts = AtomSet([])
            for b in at.bonds:
                at2 = b.atom1
                if at2==at: at2 = b.atom2
                bondedAts.append(at2)
            goodAts = []
            goodDists = []
            for i in range(len(closeAts)):
                cAt = closeAts[i]
                if cAt not in bondedAts:
                    goodAts.append(cAt)
                    goodDists.append(dists[i])
            if len(goodAts):
                atDict[at] = goodAts
                distDict[at] = goodDists
            else:
                del atDict[at]
                del distDict[at]
        return atDict, distDict
                    

    def dismiss_cb(self, event=None):
        self.lines.Set(faces=[], vertices=[], tagModified=False)
        self.labels.Set(vertices=[], tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        self.result_form.destroy()


    def setupDisplay(self, lineVerts, faces, labelVerts, labelStrs, colors):
        #draw lines between at(s) and closeAts
        self.labels.Set(vertices=labelVerts, labels=labelStrs,
                        materials=colors, tagModified=False)
        self.lines.Set(vertices=lineVerts, type=GL.GL_LINE_STRIP,
                       materials=colors,
                       faces=faces, freshape=1, tagModified=False)
        self.vf.GUI.VIEWER.Redraw()


    def save_sets(self, event=None):
        keyAts = AtomSet(self.atDict.keys())
        #build an AtomSet of atoms close to any key
        closeAts = AtomSet([])
        for v in self.atDict.values():
            closeAts.extend(AtomSet(v))
        #there could be duplication here...
        #NOTE: THIS DISORDERS the atoms
        closeAts = closeAts.uniq()
        self.vf.saveSet(keyAts, 'closeContact_keys',comments="keys for checkForCloseContact")
        self.vf.saveSet(closeAts, 'closeContact_values', comments="results of checkForCloseContact")


    def showAllCloseContacts(self, atDict, distDict, event=None):
        lineVerts = []
        faces = []
        labelVerts = []
        labelStrs = []
        faces = []
        ctr = 1
        atCtr = 0
        colors = []
        colorCutOff = 1.0 # FIXME should be user setable
        for at in atDict.keys():
            lineVerts.append(at.coords)
            c1 = Numeric.array(at.coords, 'f')
            r1 = at.vdwRadius
            closeAts = atDict[at]
            thisAtCtr = 1
            for cAt in closeAts:
                lineVerts.append(cAt.coords)
                faces.append((atCtr, ctr))
                #build labelVert and labelStr
                c2 = Numeric.array(cAt.coords, 'f')
                #newCenter = tuple((c1 + c2)/2.0)
                labelVerts.append(tuple((c1 + c2)/2.0))
                j = thisAtCtr/2
                labelStrs.append(str(round(distDict[at][j],3)))
                r2 = cAt.vdwRadius
                if distDict[at][j]<(r1+r2)*colorCutOff:
                    colors.append( (1,0,0) )
                else:
                    colors.append( (0,1,0) )
                thisAtCtr = thisAtCtr + 1
                ctr = ctr+1
            atCtr = ctr
            ctr = ctr+1
        self.resultCtr = atCtr
        #print "set resultCtr to ", atCtr
        self.setupDisplay(lineVerts, faces, labelVerts, labelStrs, colors)
                

    def showCloseContacts(self, atDict, distDict, event=None):
        print "#############in SHOWCLOSECONTACTS#############"
        lb = self.ifd_results.entryByName['atsLC']['widget'].lb
        if lb.curselection() == (): return
        atName = lb.get(lb.curselection())
        at = self.vf.Mols.NodesFromName(atName)[0]
        closeAts =  atDict[at]
        lineVerts = []
        faces = []
        labelVerts = []
        labelStrs = []
        ctr = 1
        lineVerts.append(at.coords)
        c1 = Numeric.array(at.coords, 'f')
        j = 0
        r1 = at.vdwRadius
        colors = []
        colorCutOff = 1.0 # FIXME should be user setable
        for cAt in closeAts:
            lineVerts.append(cAt.coords)
            faces.append((0, ctr))
            #build labelVert and labelStr
            c2 = Numeric.array(cAt.coords, 'f')
            labelVerts.append(tuple((c1 + c2)/2.0))
            labelStrs.append(str(round(distDict[at][j],3)))
            ctr = ctr+1
            r2 = cAt.vdwRadius
            if distDict[at][j]<(r1+r2)*colorCutOff:
                colors.append( (1,0,0) )
            else:
                colors.append( (0,1,0) )
            j = j + 1
        self.setupDisplay(lineVerts, faces, labelVerts, labelStrs, colors)


    def buildForm(self):
        if hasattr(self, 'ifd0'):
            return
        self.selType = Tkinter.StringVar()
        self.selType.set("CloserThanVDW")
        ifd = self.ifd0 = InputFormDescr(title = "Select Two Sets:")
        ifd.append({'name':'keyLab',
                    'widgetType':Tkinter.Label,
                    'text':'Select Key Atoms:',
                    'gridcfg':{'sticky':Tkinter.W, 'columnspan':4}})
        ifd.append({'name': 'keySelector',
            'wtype':StringSelectorGUI,
            'widgetType':StringSelectorGUI,
            'wcfg':{ 'molSet': self.vf.Mols,
                    'vf': self.vf,
                    'all':1,
                    'crColor':(0.,1.,0.),
            },
            'gridcfg':{'sticky':'we' , 'columnspan':4}})
        ifd.append({'name':'interSelLab',
                    'widgetType':Tkinter.Label,
                    'text':'_____________________________________________',
                    'gridcfg':{'sticky':Tkinter.W, 'columnspan':4}})
        ifd.append({'name':'checkLab',
                    'widgetType':Tkinter.Label,
                    'text':'Select Atoms to check vs Keys:',
                    'gridcfg':{'sticky':Tkinter.W, 'columnspan':4}})
        ifd.append({'name': 'checkSelector',
            'wtype':StringSelectorGUI,
            'widgetType':StringSelectorGUI,
            'wcfg':{ 'molSet': self.vf.Mols,
                    'vf': self.vf,
                    'all':1,
                    'crColor':(0.,0.,1.),
            },
            'gridcfg':{'sticky':'we', 'columnspan':4 }})
        ifd.append({'name':'noteLab',
                    'widgetType':Tkinter.Label,
                    'text':'(empty form uses all atoms in viewer)',
                    'gridcfg':{'sticky':'we', 'columnspan':4}})
        ifd.append({'name':'interSelLab2',
                    'widgetType':Tkinter.Label,
                    'text':'_____________________________________________',
                    'gridcfg':{'sticky':Tkinter.W, 'columnspan':4}})
        ifd.append({'name':'selectorLab',
                    'widgetType':Tkinter.Label,
                    'text':'Select Selection Algorithm:',
                    'gridcfg':{'sticky':Tkinter.W, 'columnspan':4}})
        #ifd.append({'name':'interSelLab3',
                    #'widgetType':Tkinter.Label,
                    #'text':'_____________________________________________',
                    #'gridcfg':{'sticky':Tkinter.W, 'columnspan':4}})
        ifd.append({'name':'VDWsel',
                    'widgetType':Tkinter.Radiobutton,
                    'wcfg':{'text':"CloserThanVDW",
                            'variable':self.selType,
                            'value':"CloserThanVDWSelector",
                            'command':self.setDistSelector_cb,
                            },
                    'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'vdwPercentCutoff',
                    'widgetType':ThumbWheel,
                    #'The critical distance will be multiplied by this factor',
                    'tooltip': 'VDW Scaling Factor:\n(cutoff=Sum of vdwRadii*scale)',
                    'wcfg':{'labCfg':{'text': ' scale:'},
                             'showLabel':1, 'width':150,
                             'min':0.1, 'type':float, 'precision':2,
                             'value':1.0, 'continuous':1, 'oneTurn':2,
                             'wheelPad':2, 'height':20},
                     'gridcfg':{'row':-1,'column':1, 'columnspan':3,'sticky':'we'}})
        ifd.append({'name':'VDWPlussel',
                    'widgetType':Tkinter.Radiobutton,
                    'wcfg':{'text':"CloserThanVDWPlusConstant",
                            'variable':self.selType,
                            'value':"CloserThanVDWPlusConstant",
                            'command':self.setDistSelector_cb,
                            },
                    'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'vdwPlusConstant',
                    'widgetType':ThumbWheel,
                    #'The critical distance will be multiplied by this factor',
                    'tooltip': 'VDW Plus Constant Factor:\n(cutoff=Sum of vdwRadii+constant)',
                    'wcfg':{'labCfg':{'text': 'const:'},
                             'showLabel':1, 'width':150,
                             'type':float, 'precision':2,
                             'value':0.0, 'continuous':1, 'oneTurn':2,
                             'wheelPad':2, 'height':20},
                     'gridcfg':{'row':-1,'column':1, 'columnspan':3,'sticky':'we'}})
        ifd.append({'name':'Distsel',
                    'widgetType':Tkinter.Radiobutton,
                    'wcfg':{'text':"Distance",
                            'variable':self.selType,
                            'value':"DistanceSelector",
                            'command':self.setDistSelector_cb,
                            },
                    'gridcfg':{'sticky':'w'}})

        ifd.append({'name':'distanceCutoff',
                    'widgetType':ThumbWheel,
                    'tooltip':'angstrom distance cutoff',
                    'wcfg':{'labCfg':{'text': 'cutoff:'},
                             'showLabel':1, 'width':150,
                             'min':0.1, 'type':float, 'precision':2,
                             'value':3.0, 'continuous':1, 'oneTurn':2,
                             'wheelPad':2, 'height':20},
                     'gridcfg':{'row':-1,'column':1, 'columnspan':3,'sticky':'we'}})
        ifd.append({'name': 'ok',
                    'widgetType': Tkinter.Button,
                    'wcfg':{ 'text': 'OK',
                        'command': self.ok_cb,},
                    'gridcfg': {'sticky':'we'}}),
        ifd.append({'name': 'cancel',
                    'widgetType': Tkinter.Button,
                    'wcfg':{ 'text': 'Cancel',
                        'command': self.cancel_cb,},
                    'gridcfg': {'sticky':'we', 'row':-1, 'column':1,
                                    'columnspan':3}}),
        self.form  = self.vf.getUserInput(ifd, modal=0, blocking=0,
                scrolledFrame=1)#, width=440, height=540)
        self.key_ss = self.ifd0.entryByName['keySelector']['widget']
        self.check_ss = self.ifd0.entryByName['checkSelector']['widget']
        #make the default distance selector CloserThanVDWSelector
        self.ifd0.entryByName['VDWsel']['widget'].invoke() 


    def setDistSelector_cb(self, event=None):
        #value is a string: eg 'vdwSum'
        self.selector = self.selType.get()
        #print "set self.selector to ", self.selector


    def update_old_values(self):
        if hasattr(self, 'key_ss'):
            self.keyss_oldvalue = self.key_ss.showCurrent.get()
        if hasattr(self, 'check_ss'):
            self.checkss_oldvalue = self.check_ss.showCurrent.get()


    def ok_cb(self, event=None):
        keys = self.key_ss.get()
        if not len(keys):
            keyAts = self.vf.allAtoms
        else:
            cl = keys[0].setClass
            keySet = cl(keys)
            keyAts = keySet
            if cl!=Atom:
                keyAts = keySet.findType(Atom)
        checks = self.check_ss.get()
        if not len(checks):
            checkAts = self.vf.allAtoms
        else:
            cl = checks[0].setClass
            checkSet = cl(checks)
            checkAts = checkSet
            if cl!=Atom:
                checkAts = checkSet.findType(Atom)
        percentCutoff = self.ifd0.entryByName['vdwPercentCutoff']['widget'].get()
        #print 'using ', percentCutoff,' for percentCutoff'
        distanceCutoff = self.ifd0.entryByName['distanceCutoff']['widget'].get()
        #print 'using ', distanceCutoff,' for distanceCutoff'
        constant = self.ifd0.entryByName['vdwPlusConstant']['widget'].get()
        self.update_old_values()
        
        #this part is needed to fix bug 950
        mol1 = keyAts.getParentsNoStringRepr().top[0]
        master = mol1.geomContainer.geoms['master']
        matrix = master.GetMatrix(master)
        if (matrix != Numeric.eye(4,4)).all():
            self.vf.writePDB.setNewCoords(mol1)
        mol2 = checkAts.getParentsNoStringRepr().top[0]
        if mol2 != mol1:
            master = mol2.geomContainer.geoms['master']
            matrix = master.GetMatrix(master)
            if not (matrix == Numeric.eye(4,4)).all():
                self.vf.writePDB.setNewCoords(mol2)

            
        
        return self.doitWrapper(keyAts, checkAts, percentCutoff, distanceCutoff, self.selector, constant=constant, topCommand=0)


    def cancel_cb(self, event=None):
        #force the CrossSets to undisplay, but remember the old values
        self.update_old_values()
        if hasattr(self, 'key_ss'):
            self.key_ss.showCurrent.set(0)
            self.key_ss.Show_cb()
        if hasattr(self, 'check_ss'):
            self.check_ss.showCurrent.set(0)
            self.check_ss.Show_cb()
        self.form.withdraw()
        return


    def guiCallback(self):
        if not len(self.vf.Mols):
            self.warningMsg('no molecules in viewer')
            return 
        if hasattr(self, 'ifd0'):
            self.form.deiconify()
            #force the CrossSets to display
            self.key_ss.showCurrent.set(self.keyss_oldvalue)
            self.key_ss.Show_cb()
            self.check_ss.showCurrent.set(self.checkss_oldvalue)
            self.check_ss.Show_cb()
        else:
            self.buildForm()
        

checkForCloseContactsGUICommandGuiDescr = {'widgetType':'Menu',
                                          'menuBarName':'menuRoot',
                                          'menuButtonName':'Edit',
                                          'menuEntryLabel':'Check For Close Contacts'}


CheckForCloseContactsGUICommandGUI = CommandGUI()
CheckForCloseContactsGUICommandGUI.addMenuCommand('menuRoot', 'Edit',
                    'Check for Close Contacts', cascadeName='Misc', index=0)




class CheckForCloseContacts(MVCommand):
    """This command detects atoms which are selected as "close" by a MolKit.distanceSelector.  These selectors use criteria such as closer than combined atomic radii distance of nodes or closer than a specific distance.
   \nPackage : Pmv
   \nModule  : repairCommands
   \nClass   : CheckForCloseContacts
   \nCommand : checkForCloseContacts
   \nSynopsis:\n   
        closeAts <--- checkForCloseContacts(keyNodes, nodesToCheck, percentCutoff, **kw)
   \nRequired Arguments:\n
        keyNodes --- nodes to use as centers for selectInSphere of distance keyNode.radius + radius nodes in nodesToCheck
        \nnodesToCheck --- nodes to test to see if within sumRadii distance of keyNodes. 
   \nOptional Arguments:\n     
        percentCutoff ---  each sum of radii * this number is used to pick close contacts
        \ndistSelectorClass=None --- optional distanceSelector Class.default class is CloserThanVDWSelector
    """

    def onAddCmdToViewer(self):
        self.distSelector = CloserThanVDWSelector()

    def doit(self, keyAts, checkAts, percentCutoff, distanceCutoff, **kw):
        distSelectorClass = kw.get('distSelectorClass')
        if distSelectorClass is None:
            print "using self.distSelector"
            distSelector = self.distSelector
        else:
            dict = {}
            if kw.has_key("constant"):
                dict['constant'] = kw.get('constant')
            distSelector = apply(distSelectorClass,(), dict)

        pairDict, distDict = distSelector.select(keyAts, checkAts,
                        percentCutoff=percentCutoff, cutoff=distanceCutoff)
        pairDict, distDict = self.cleanupDicts(pairDict, distDict)
        return pairDict, distDict


    def cleanupDicts(self, atDict, distDict):
        for at in atDict.keys():
            closeAts = atDict[at]
            dists = distDict[at]
            bondedAts = AtomSet([])
            #CA-N-H
            for b in at.bonds:
                at2 = b.atom1
                if at2==at: at2 = b.atom2
                bondedAts.append(at2)
                # need to exclude 1:3 bonds here
                for bd in at2.bonds:
                    at3 = bd.atom1
                    if at3==at2: at3 = bd.atom2
                    if at3!=at:
                        bondedAts.append(at3)
                        # need to exclude 1:4 bonds here
                        for bnd in at3.bonds:
                            at4 = bnd.atom1
                            if at4 == at3:
                                at4 = bnd.atom2
                            if at4!=at and at4!=at2:
                                bondedAts.append(at4)
            goodAts = []
            goodDists = []
            for i in range(len(closeAts)):
                cAt = closeAts[i]
                if cAt not in bondedAts:
                    goodAts.append(cAt)
                    goodDists.append(dists[i])
            if len(goodAts):
                atDict[at] = goodAts
                distDict[at] = goodDists
            else:
                del atDict[at]
                del distDict[at]
        return atDict, distDict
                    

    def __call__(self, keyNodes, nodesToCheck, percentCutoff=1.0, distanceCutoff=3.0, 
                            distSelectorClass=None,**kw):
        """closeAts <- checkForCloseContacts(keyNodes, nodesToCheck, percentCutoff, **kw)
        \nRequired Arguments:\n
        keyNodes --- nodes to use as centers for selectInSphere of distance keyNode.radius + radius nodes in nodesToCheck\n
        nodesToCheck --- nodes to test to see if within sumRadii distance of keyNodes.\n 
        \nOptional Arguments:\n
        percentCutoff --- each sum of radii * this number is used to pick close contacts\n
        distSelectorClass=None --- optional distanceSelector Class\n
        """
        # be sure that all ats have radius
        # WHAT ABOUT UNITED ATOM v. plain???
        #tops1 = keyNodes.top.uniq()
        #tops2 = nodesToCheck.top.uniq()
        #tops = tops1+tops2
        #tops = tops.uniq()
        #for top in tops:
        #top.defaultRadii(united=0)
##         if type(keyNodes) is types.StringType:
##             self.nodeLogString = "'"+keyNodes+"'"
        keyNodes = self.vf.expandNodes(keyNodes)
        
        if not len(keyNodes): return 'ERROR'
        keyAts = keyNodes.findType(Atom)
        nodesToCheck = self.vf.expandNodes(nodesToCheck)
        if not len(nodesToCheck): return 'ERROR'
        checkAts = nodesToCheck.findType(Atom)
        kw['distSelectorClass'] = distSelectorClass
        return apply( self.doitWrapper, (keyAts, checkAts, percentCutoff, distanceCutoff), kw )


class RepairMissingAtomsGUICommand(MVCommand):
    """This class provides Graphical User Interface to RepairMissingAtomsCommand which is invoked by it with the current selection, if there is one.
    \nPackage : Pmv
   \nModule  : repairCommands
   \nClass   : RepairMissingAtomsGUICommand
   \nCommand : repairMissingAtomsGC
   \nSynopsis:\n
        closeContactDict<---repairMissingAtomsGC(nodes) 
   \nRequired Arguments:\n      
        nodes --- molecule(s) to check for missing atoms
    """
    
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def onRemoveObjFromViewer(self, obj):
        if self.oldNode==obj:
            del self.oldNode


    def onAddCmdToViewer(self):
        self.oldNode = None


    def __call__(self, nodes, **kw):
        """closeContactDict<---repairMissingAtomsGC(nodes) 
        \nnodes --- molecule(s) to check for missing atoms
        """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        return apply(self.doitWrapper,(nodes,), kw)


    def doit(self, nodes):
        dict = self.vf.checkForMissingAtoms(nodes)
        if not len(dict.keys()): 
            self.warningMsg('no residues to repair')
            return 'ERROR'
        resNames = []
        resSet = ResidueSet(dict.keys())
        newAts = self.vf.repairMissingAtoms(resSet)
        mol = resSet[0].top
        self.vf.GUI.VIEWER.Redraw()
        #check for closeContacts of newAts vs self.vf.allAtoms
        return self.vf.checkForCloseContactsGC(newAts, self.vf.allAtoms, 0.9,
            topCommand=0)


    def guiCallback(self):
        sel = self.vf.getSelection()
        if len(sel):
            if self.vf.userpref['Expand Node Log String']['value'] == 0:
                self.vf.repairMissingAtoms.nodeLogString = "self.getSelection()"
            mol = sel.top.uniq()[0]
            #FIX THIS: why not just use sel.top.uniq()????
            return self.doitWrapper(mol, topCommand=0)
        

repairMissingAtomsGUICommandGuiDescr = {'widgetType':'Menu',
                                        'menuBarName':'menuRoot',
                                        'menuButtonName':'Edit',
                                        'menuEntryLabel':'Repair Missing Atoms '}


RepairMissingAtomsGUICommandGUI = CommandGUI()
RepairMissingAtomsGUICommandGUI.addMenuCommand('menuRoot', 'Edit',
                    'Repair Missing Atoms ', cascadeName='Misc')



class RepairMissingAtoms(MVCommand):
    """This command compares atoms present in residues with those expected by the dictionary used to assign Kollman charges, qkollua. It builds the missing atoms.
    \nPackage : Pmv
   \nModule  : repairCommands
   \nClass   : RepairMissingAtoms
   \nCommand : repairMissingAtoms
   \nSynopsis:\n
        dictOfMissingAts <--- repairMissingAtoms(nodes, **kw)
   \nRequired Arguments:\n        
        nodes --- TreeNodeSet holding the current selection
    """
    
    def onRemoveObjFromViewer(self, obj):
        if obj in self.resAts.keys():
            del self.resAts[obj]


    def onAddCmdToViewer(self):
        #from Pmv.gmmRes import resDict
        from Pmv.qkollRes import resDict
        self.vf.loadModule('superImposeCommands', 'Pmv')
        self.vf.loadModule('deleteCommands', 'Pmv')
        self.resDict = resDict


    def getRefMol(self, resType, ptype = PdbParser):
        newparser = ptype(None)
        atLines = self.resDict[resType]
        refmol = newparser.buildMolFromAtomLines(atLines, resType)
        self.vf.addMolecule(refmol)
        return refmol
        
        
    def doit(self, resSet):
        newAts = AtomSet([])
        for res in resSet:
            #print 'repairing ', res.name
            if res.type not in self.resDict.keys():
                #print 'skipping ', res
                continue
            mol = res.top
            resType = res.type
            resAts = res.atoms
            #oxt = resAts.get(lambda x: x.name=='OXT')
            #if oxt:
                #resAts = resAts - oxt[0]
                
            resAtNames = resAts.name
            refmol = self.getRefMol(resType)
            #refmol = self.getRefMol(resType, ptype)
            ats2 = refmol.allAtoms
            # inAts are atoms in refmol which are also in mol
            inAts = ats2.get(lambda x,resAtNames=resAtNames:x.name in resAtNames)
            inAtsname = inAts.name
            # resATS2 are atoms in mol which are also in refmol
            resAts2 = resAts.get(lambda x,inAtsname=inAtsname:x.name in inAtsname)
            #move new refmol ontop of res
            self.vf.superimposeCoords(resAts2, inAts, refmol.allAtoms, topCommand=0)
            #the diff between refmol's shared ats and all atoms is atsToBuild
            atsToBuild = ats2 - inAts
            builtAts = AtomSet([])
            for at in atsToBuild:
                #print 'building copy of ', at.full_name()
                newAt = Atom(name=at.name, parent=res, 
                            elementType = at.elementType, top=mol)
                for k in at.colors.keys():
                    newAt.colors[k] = at.colors[k]
                #for k in at._charges.keys():
                #    newAt._charges[k] = at._charges[k]
                newAt.chargeSet = at.chargeSet
                newAt.element = at.element
                newAt.hetatm = at.hetatm
                newAt._coords = []
                newAt._coords.append(at.coords)
                #redo number at end
                newAt.number = at.number
                #after redoing numbers set up mol.atmNum[newAt.number] = newAt
                newAt.occupancy = at.occupancy
                newAt.temperatureFactor = at.temperatureFactor
                #need to build bonds to all Atoms which at has bonds(?)
                for b in at.bonds:
                    at2 = b.atom1
                    if at2==at: at2 = b.atom2
                    #see if other atom has been built yet
                    if at2.name in res.atoms.name:
                        atom2 = res.atoms.get(lambda x, at2=at2: x.name == at2.name)[0]
                        bond = Bond(newAt, atom2, origin = 'UserDefined')
                for k in atom2._charges.keys():
                    #can't use at_charges
                    newAt._charges[k] = 0.00
                newAt.chargeSet = atom2.chargeSet
                #after adding allAtoms and removing mol2, call buildBondsByDist.
                builtAts.append(newAt)
                newAts.append(newAt)
            mol.allAtoms = mol.allAtoms + builtAts

            #after building all atsToBuild for this residue, delete mol2 +bbByD
            self.vf.deleteMol(refmol, topCommand=0)
        if len(newAts):
            #don't forget to rebuild mv.allAtoms
            self.vf.allAtoms = self.vf.Mols.chains.residues.atoms
            event = AddAtomsEvent(objects=newAts)
            self.vf.dispatchEvent(event)

        return newAts
            

    def __call__(self, nodes, **kw):
        """dictOfMissingAts <--- checkForMissingAtoms(nodes, **kw)
        \nnodes --- TreeNodeSet holding the current selection"""
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        resSet = nodes.findType(Residue).uniq()
        return apply( self.doitWrapper, (resSet,), kw )



class EditHistHydrogensGUICommand(MVCommand):
    """Allows user to call editHistHydrogens on each histidine residue in selection.
   \nPackage : Pmv
   \nModule  : repairCommands
   \nClass   : EditHistHydrogensGUICommand
   \nCommand : editHist_hGC
   \nSynopsis:\n
        newHydrogens <--- editHist_hGC(nodes, resSet, **kw)
   \nRequired Arguments:\n    
        nodes --- TreeNodeSet holding the current selection
        \nresSet --- residueSet 
    """


    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def guiCallback(self):
        if self.vf.userpref['Expand Node Log String']['value'] == 0:
            self.vf.editHist_h.nodeLogString = "self.getSelection()"
        sel = self.vf.getSelection()
        if len(sel):
            res = sel.findType(Residue, uniq=1)
            resSet = res.get(lambda x: x.type == 'HIS')
            if resSet is None or not len(resSet): 
                self.warningMsg('No Histidines in selection')
                return 'ERROR'
            self.doitWrapper(resSet, topCommand=0)
        else:
            self.warningMsg('Nothing to select!')


    def __call__(self, nodes, resSet, **kw):
        """newHydrogens <--- editHist_hGC(nodes, resSet, **kw)
        \nnodes --- TreeNodeSet holding the current selection
        \nresSet --- residueSet
           """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        kw['topCommand'] = 0
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        res = nodes.findType(Residue, uniq=1)
        resSet = res.get(lambda x: x.type == 'HIS')
        if not resSet: 
            self.warningMsg('No Histidines in selection')
            return 'ERROR'
        apply(self.doitWrapper,(resSet,), kw)


    def doit(self, resSet):
        resNames = []
        for r in resSet:
            resNames.append(r.full_name())
        #put up a form here with buttons
        ifd = self.ifd=InputFormDescr(title = 'Edit Histidine Hydrogens :')
        ifd.append({'name': 'histLabel1',
            'widgetType': Tkinter.Label,
            'wcfg':{'text': 'Histidine'},
            'gridcfg':{'sticky': 'nesw'}})
        ifd.append({'name': 'histLabel2',
            'widgetType': Tkinter.Label,
            'wcfg':{'text': ' 0, HD1 '},
            'gridcfg':{'sticky': 'nesw', 'row':-1, 'column':1}})
        ifd.append({'name': 'histLabel3',
            'widgetType': Tkinter.Label,
            'wcfg':{'text': ' 0, HE2 '},
            'gridcfg':{'sticky': 'nesw', 'row':-1, 'column':2}})
        ifd.append({'name': 'histLabel3',
            'widgetType': Tkinter.Label,
            'wcfg':{'text': '+1     '},
            'gridcfg':{'sticky': 'nesw', 'row':-1, 'column':3}})
        ifd.append({'name': 'histLabel4',
            'widgetType': Tkinter.Label,
            'wcfg':{'text': '_______________________________________________'},
            'gridcfg':{'sticky': 'nesw', 'columnspan':5}})
        #build the rest of it here
        self.cbDict = {}
        cbFuncs = [None, 'HD1', 'HE2', 'HD1HE2']
        nameLabs = []
        for n in range(len(resNames)):
            name = resNames[n]
            r = resSet[n]
            nameLab = name + 'lab'
            nameLabs.append(nameLab)
            cbNames = []
            self.cbDict[name] = newvar = Tkinter.StringVar()
            ratomnames = r.atoms.name
            hasHD1 = 'HD1' in ratomnames
            hasHE2 = 'HE2' in ratomnames
            if hasHD1 and hasHE2:
                newvar.set('HD1HE2')
            elif hasHD1 and not hasHE2:
                newvar.set('HD1')
            elif hasHE2 and not hasHD1:
                newvar.set('HE2')
            ifd.append({'name': nameLab,
                'widgetType': Tkinter.Label,
                'wcfg':{'text': name},
                'gridcfg':{'sticky': Tkinter.W+Tkinter.E}})
            for i in range(1,4):
                newname = name + str(i)
                cbNames.append(newname)
                ifd.append({'name': newname,
                    'widgetType': Tkinter.Radiobutton,
                    'variable': newvar,
                    'value': cbFuncs[i],
                    'gridcfg':{'sticky': 'we', 'row':-1, 'column':i}})
        ifd.append({'name':'applyBut',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Apply',
                'command': self.apply_cb},
            'gridcfg':{'sticky':Tkinter.W+Tkinter.E, 'columnspan':2}})
        ifd.append({'name':'closeBut',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Dismiss',
                'command': self.dismiss_cb},
            'gridcfg':{'sticky':'we',  'columnspan':3,
                        'row':-1, 'column':2}})
        self.form = self.vf.getUserInput(ifd, modal=0, blocking=0,
                scrolledFrame=1, width=500)
        self.form.root.protocol('WM_DELETE_WINDOW',self.dismiss_cb)
        for name in nameLabs:
            ifd.entryByName[name]['widget'].bind('<Button-1>', CallBackFunction(self.highLight, name) )


    def highLight(self, name, event=None):
        self.vf.clearSelection()
        self.vf.setIcomLevel(Residue, topCommand=0)
        self.vf.select(name[:-3])


    def apply_cb(self, event=None):
        #FIX THIS: may not need any changes
        nodeDict = {}
        for k, v in self.cbDict.items():
            nodeDict[k] = v.get()
        #print 'nodeDict=', nodeDict

        newHydrogens = self.vf.editHist_h(nodeDict)

        self.vf.GUI.VIEWER.Redraw()


    def dismiss_cb(self, event=None):
        self.form.root.destroy()


EditHistHydrogensGUICommandGUI=CommandGUI()
EditHistHydrogensGUICommandGUI.addMenuCommand('menuRoot', 'Edit', 
        'Edit Histidine Hydrogens', cascadeName='Hydrogens')



class EditHistHydrogens(MVCommand):
    """Allows user to edit hydrogens in histidine residues
     \nPackage : Pmv
   \nModule  : repairCommands
   \nClass   : EditHistHydrogens
   \nCommand : editHist_h
   \nSynopsis:\n
            newHydrogens <--- editHist_h(nodeDict, **kw)
   \nRequired Arguments:\n        
            nodeDict --- a dictionary of a TreeNodeSet holding the current selection
    """


    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('typeAtoms'):
            self.vf.loadCommand('editCommands', 'typeAtoms','Pmv',
                                topCommand=0)
        if not self.vf.commands.has_key('deleteAtomSet'):
            self.vf.loadCommand('deleteCommands', 'deleteAtomSet','Pmv',
                                topCommand=0)
        if not self.vf.commands.has_key('computeGasteiger'):
            self.vf.loadCommand('editCommands', 'computeGasteiger','Pmv',
                                topCommand=0)
        from PyBabel.addh import AddHydrogens, SP2_N_H_DIST
        self.addh = AddHydrogens()
        self.SP2_N_H_DIST = SP2_N_H_DIST


    def __call__(self, nodeDict, **kw):
        """newHydrogens <--- editHist_h(nodeDict, **kw)
        \nnodeDict --- a dictionary of a TreeNodeSet holding the current selection"""
        #nodeDict keys had better be full_names
        #values can be the name of the function to do it
        theseNodes = ResidueSet([])
        for name in nodeDict.keys():
            newNodes = self.vf.expandNodes(name)
            if len(newNodes):
                theseNodes = theseNodes + self.vf.expandNodes(name)
        if len(theseNodes): 
            #if there are nodes, there have to be Residues
            mols = theseNodes.top.uniq()
            for mol in mols:
                self.vf.typeAtoms(mol, topCommand=0)
            return apply(self.doitWrapper,(nodeDict,), kw)
        else: return 'ERROR'


    def doit(self, nodeDict):
        #for each node set its type
        #have to call typeAtoms on the mols involved
        atmsToDelete = AtomSet([])
        newHydrogens = AtomSet([])
        self.hasKollman = 0
        self.hasgasteiger = 0
        for node, value in nodeDict.items():
            res = self.vf.expandNodes(node)[0]
            badHs, newHs = self.editHIS(res, value)
            if badHs: 
                atmsToDelete = atmsToDelete + badHs
            if newHs:
                newHydrogens = newHydrogens + newHs
        #check the userpref here
        if len(atmsToDelete):
            self.vf.allAtoms = self.vf.allAtoms - atmsToDelete
            for mol in atmsToDelete.top.uniq():
                mol.allAtoms = mol.allAtoms - atmsToDelete
            for at in atmsToDelete:
                for b in at.bonds:
                    at2 = b.atom1
                    if at2==at: at2=b.atom2
                    at2.bonds.remove(b)
                at.parent.remove(at, cleanup=1)
        # add the new atoms and make an effort to add the correct charges...
        if len(newHydrogens):
            self.vf.allAtoms = self.vf.allAtoms + newHydrogens
            mols, atms = self.vf.getNodesByMolecule(newHydrogens, Atom)
            for m, ats in map(None, mols, atms):
                m.allAtoms = m.allAtoms + ats
            if self.hasKollman:
                self.vf.addKollmanCharges(newHydrogens, topCommand=0)
            if self.hasgasteiger:
                self.vf.computeGasteiger(newHydrogens, topCommand=0)

        if len(atmsToDelete):
            event = DeleteAtomsEvent(objects=atmsToDelete)
            self.vf.dispatchEvent(event)

        if len(newHydrogens):
            event = AddAtomsEvent(objects=newHydrogens)
            self.vf.dispatchEvent(event)
                
        return newHydrogens
            

    def editHIS(self, res, key):
        resatomnames = res.atoms.name
        hasHD1 = 'HD1' in resatomnames
        hasHE2 = 'HE2' in resatomnames
        if key is None:
            return
        if len(key)>3:
            return self.HD1HE2(res, hasHD1, hasHE2)
        elif key=='HD1':
            return self.HD1(res, hasHD1, hasHE2)
        else:
            return self.HE2(res, hasHD1, hasHE2)


    def fixCharges(self, h, a, kollCh, gastCh):
        if a._charges.get('Kollman', None):
            self.hasKollman = 1
            h._charges['Kollman'] = kollCh
        if a._charges.get('pdbqs', None):
            if a.charge in [-0.613, -0.686, -0.444, -0.527]:
                self.hasKollman = 1
            h._charges['pdbqs'] = kollCh
        if a._charges.get('pdbq', None):
            if a.charge in [-0.613, -0.686, -0.444, -0.527]:
                self.hasKollman = 1
            h._charges['pdbq'] = kollCh
        if a._charges.get('gasteiger', None):
            self.hasgasteiger = 1
            h._charges['gasteiger'] = gastCh
        h.chargeSet = a.chargeSet


    def HD1(self, res, hasHD1, hasHE2):
        newH = AtomSet([])
        badH = AtomSet([])
        if 'ND1' not in res.atoms.name:
            return badH, newH
        if not hasHD1:
            a = res.atoms.get(lambda x: x.name=='ND1')[0]
            newH.append(self.addNewH(a, 'HD1'))
            self.fixCharges(newH[-1], a, .32, .1672)
        if hasHE2: 
            badH.append(res.atoms.get(lambda x: x.name=='HE2')[0])
        return badH, newH


    def HE2(self, res, hasHD1, hasHE2):
        newH = AtomSet([])
        badH = AtomSet([])
        if 'NE2' not in res.atoms.name:
            return badH, newH
        if not hasHE2:
            a = res.atoms.get(lambda x: x.name=='NE2')[0]
            newH.append(self.addNewH(a, 'HE2'))
            self.fixCharges(newH[-1], a, .32, .1675)
        if hasHD1: 
            badH.append(res.atoms.get(lambda x: x.name=='HD1')[0])
        return badH, newH


    def HD1HE2(self, res, hasHD1, hasHE2):
        newH = AtomSet([])
        badH = AtomSet([])
        if 'ND1' not in res.atoms.name:
            return badH, newH
        if 'NE2' not in res.atoms.name:
            return badH, newH
        if not hasHD1:
            a = res.atoms.get(lambda x: x.name=='ND1')[0]
            newH.append(self.addNewH(a, 'HD1'))
            self.fixCharges(newH[-1], a, .4780, .1671)
        if not hasHE2:
            a = res.atoms.get(lambda x: x.name=='NE2')[0]
            newH.append(self.addNewH(a, 'HE2'))
            self.fixCharges(newH[-1], a, .4860, .1675)
        return badH, newH


    def addNewH(self, a, name):
        hat = self.addh.add_sp2_hydrogen(a, self.SP2_N_H_DIST)
        a = hat[0][1]
        atom = Atom(name, a.parent, top=a.top)
        atom._coords = [ hat[0][0] ]
        atom.hetatm = 0
        atom.alternate = []
        atom.element = 'H'
        atom.number = -1
        atom.occupancy = 1.0
        atom.radius = 1.2
        atom.conformation = 0
        atom.temperatureFactor = 0.0
        atom.babel_atomic_number = hat[0][2]
        atom.babel_type = hat[0][3]
        atom.babel_organic = 1
        bond = Bond( a, atom )
        for key, value in a.colors.items():
            atom.colors[key] = (1.0, 1.0, 1.0)
            atom.opacities[key] = 1.0
        #also add whatever kinds of charges a._charges has
        chargeKeys = a._charges.keys()
        if 'Kollman' in chargeKeys:
            self.hasKollman = 1
        if 'gasteiger' in chargeKeys:
            self.hasgasteiger = 1
        return atom



class AddOXTGUICommand(MVCommand, MVAtomICOM):
    """This class provides GUICommand for AddOXT which adds oxygen atom to
terminal carbon atom.
    \nPackage : Pmv
   \nModule  : repairCommands
   \nClass   : AddOXTGUICommand
   \nCommand : add_oxtGC
   \nSynopsis:\n
        AtomSet([oxt]) <--- add_oxtGC(atoms)
   \nRequired Arguments:\n        
        atoms --- atom(s)
        \noxt --- the new oxt atom
    """


    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        MVAtomICOM.__init__(self)
        self.save = None


    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('add_oxt'):
            self.vf.loadCommand('repairCommands', 'add_oxt','Pmv',
                                topCommand=0)
        if self.vf.hasGui and not hasattr(self.vf, 'setICOM'):
            self.vf.loadCommand('interactiveCommands', 'setICOM', 'Pmv') 


    def __call__(self, atoms, **kw):
        """AtomSet([oxt]) <--- add_oxtGC(atoms)
        \natoms  --- atom(s)
        \noxt --- the new oxt atom
        """
        if type(atoms) is types.StringType:
            self.nodeLogString = "'"+atoms+"'"
        ats = self.vf.expandNodes(atoms)
        if not len(ats): return 'ERROR'
        return apply(self.doitWrapper, (ats,), kw)


    def doit(self, ats):
        """ats[0] must be a carbon with two bonds, one of which is to an
        oxygen
        """
        at = ats[0]
        if at.element!='C':
            t = 'can only add oxt to carbon atom, not ' + at.element
            self.warningMsg(t)
            return 'ERROR'
        elif at.name!='C':
            t = 'can only add oxt to C carbon atom, not ' + at.name
            self.warningMsg(t)
            return 'ERROR'
        if len(at.bonds)>=3:
            t = 'can only add oxt to carbon atom with two bonds'
            self.warningMsg(t)
            return 'ERROR'
        elif len(at.bonds)==1:
            t = 'can only add oxt to carbon atom with two bonds'
            self.warningMsg(t)
            return 'ERROR'
        #must only have two bonds:
        hasO = 0
        at2 = at.bonds[0].atom1
        if at2==at:
            at2 = at.bonds[0].atom2
        if at2.element=='O':
            hasO = 1
        else:
            at2 = at.bonds[1].atom1
            if at2==at:
                at2 = at.bonds[1].atom2
            if at2.element=='O':
                hasO = 1
        if not hasO:
            t = 'can only add oxt to carbon atom with bond to 1 oxygen'
            self.warningMsg(t)
            return 'ERROR'
        #if you get to this point: add the oxygen
        #newOXT is an AtomSet containing the new oxt
        newOXT = self.vf.add_oxt(at, topCommand=0)

        if self.save:
            self.vf.setICOM(self.save, modifier="Shift_L", topCommand=0)
            self.save = None
        return newOXT


    def guiCallback(self, event=None):
        if not len(self.vf.Mols):
            self.warningMsg('no molecules in viewer')
            return
        self.vf.setICOM(self, modifier="Shift_L", topCommand=0)


    def startICOM(self):
        self.vf.setIcomLevel( Atom )



AddOXTGUICommandGUI=CommandGUI()
AddOXTGUICommandGUI.addMenuCommand('menuRoot', 'Edit', 
        'Add OXT', cascadeName='Misc')



class AddOXT(MVCommand):
    """This class uses add_sp2_hydrogen method of the AddHydrogens class from the PyBabel package to compute coordinates of oxygen to be added to carbon atom.The carbon atom is bonded to another oxygen and a CA. If it is bonded to a hydrogen, the hydrogen is removed and replaced by the new OXT atom.
   \nPackage : Pmv
   \nModule  : repairCommands
   \nClass   : AddOXT
   \nCommand : add_oxt
   \nSynopsis:\n 
        oxt<--- add_oxt(catom,**kw)
   \nRequired Arguments:\n     
        catom --- carbon atom to get new oxt oxygen atom.
        oxt ---  the new oxygen atom
    """
    
    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('typeAtoms'):
            self.vf.loadCommand('editCommands', 'typeAtoms','Pmv',
                                topCommand=0)
        if not self.vf.commands.has_key('typeBonds'):
            self.vf.loadCommand('editCommands', 'typeBonds','Pmv',
                                topCommand=0)
        if not self.vf.commands.has_key('deleteAtomSet'):
            self.vf.loadCommand('deleteCommands', 'deleteAtomSet','Pmv',
                                topCommand=0)
        #self.addh = AddHydrogens()
        from MolKit.oxtBuilder import OxtBuilder
        self.oxtBuilder = OxtBuilder()
            

    def __call__(self, catom, polarOnly=0,method='noBondOrder',renumber=1,**kw):
        """oxt<- add_oxt(catom,**kw)
        \ncatom --- carbon atom to get new oxt oxygen atom.
        \noxt --- the new oxygen atom
        """
        return apply(self.doitWrapper,(catom,), kw)


    def doit(self, catom):
        """ oxt <- add_oxt(catom)"""
        nodes = self.vf.expandNodes(catom)
        if len(nodes)==0: return 'ERROR'

        catom = nodes[0]
        if catom.element!='C':
            return 'ERROR'

        atom = self.oxtBuilder.add_oxt(catom)
        mol = catom.top

#        #check whether catom has a hydrogen to delete
#        hatoms = catom.parent.atoms.get(lambda x: x.name=='HC')
#        if hatoms is not None:
#            self.vf.deleteAtomSet(hatoms)

#        #have to type atoms before call to add_sp2_hydrogen:
#        if not hasattr(catom,'babel_type'):
#            msg = 'catom has no babel_type: calling typeAtoms'
#            print msg
#            #self.warningMsg(msg)
#            #typeAtoms does whole molecule
#            self.vf.typeAtoms(catom, topCommand=0)
#    
#        #NB: bond_length 1.28 measured from OXT-C bond in 1crn
#        tup1 = self.addh.add_sp2_hydrogen(catom, 1.28)

        res = catom.parent

#        # find where to insert H atom
#        childIndex = res.children.index(catom)+1
#        name = 'OXT'

#        # create the OXT atom object
#        atom = Atom(name, res, top=mol,
#                    childIndex=childIndex, assignUniqIndex=0)

#        # set atoms attributes
#        atom._coords = [ tup1[0][0] ]
#        if hasattr(catom, 'segID'): atom.segID = catom.segID
#        atom.hetatm = 0
#        atom.alternate = []
#        atom.element = 'O'
#        atom.occupancy = 1.0
#        atom.conformation = 0
#        atom.temperatureFactor = 0.0
#        atom.babel_atomic_number = 8
#        atom.babel_type = 'O-'
#        atom.babel_organic = 1

#        # create the Bond object bonding Hatom to heavyAtom
#        bond = Bond( catom, atom, bondOrder=2)

        # create the color entries for all geometries
        # available for the other oxygen atom attached to 'C'
        oatom = res.atoms.get(lambda x: x.name=='O')[0]
        if oatom is not None:
            for key, value in oatom.colors.items():
                atom.colors[key] = value
                #atom.opacities[key] = oatom.opacities[key]
                
                # update the allAtoms set in the molecule
        mol.allAtoms = mol.chains.residues.atoms

        fst = mol.allAtoms[0].number
        mol.allAtoms.number = range(fst, len(mol.allAtoms)+fst)

        res.assignUniqIndex()

        # update self.vf.Mols.allAtoms
        self.vf.allAtoms = self.vf.Mols.allAtoms

        #update the display
        newOXT = AtomSet([atom])
        event = AddAtomsEvent(objects=newOXT)
        self.vf.dispatchEvent(event)
        if self.vf.hasGui:
            self.vf.GUI.VIEWER.Redraw()

        return newOXT



class ModifyCTerminus(MVCommand):
    """This command removes hydrogens from C-atom of internal c-termini residues.
An internal c-terminus occurs when residues are missing from a chain.
   \nPackage : Pmv
   \nModule  : repairCommands
   \nClass   : ModifyCTerminus 
   \nCommand : modifyCTerminus
   \nSynopsis:\n
        None<---modifyCTerminus(resSet,**kw)
   \nRequired Arguments:\n     
        resSet --- residues which are inside a chain and not bonded to a next residue in chain
    """
    
    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('typeAtoms'):
            self.vf.loadCommand('editCommands', 'typeAtoms','Pmv',
                                topCommand=0)
        if not self.vf.commands.has_key('typeBonds'):
            self.vf.loadCommand('editCommands', 'typeBonds','Pmv',
                                topCommand=0)
        if not self.vf.commands.has_key('deleteAtomSet'):
            self.vf.loadCommand('deleteCommands', 'deleteAtomSet','Pmv',
                                topCommand=0)
        self.addh = AddHydrogens()
            

    def __call__(self, resSet,**kw):
        """None<---modifyCTerminus(resSet,**kw)
        \nresSet --- residues which are inside a chain and not bonded to a next residue in chain
        """
        return apply(self.doitWrapper,(resSet,), kw)


    def doit(self, resSet):
        """ None<---modifyCTerminus(resSet)"""
        nodes = self.vf.expandNodes(resSet)
        if len(nodes)==0: return 'ERROR'

        catoms = resSet.atoms.get(lambda x: x.name=='C')
        if not catoms:
            msg = resSet.full_name() + ' missing C atoms'
            self.warningMsg(msg)
            return 'ERROR'
        #catom = catoms[0]
        #hs = catom.findHydrogens()
        hs = catoms.top.uniq().allAtoms.get(lambda x: x.element=='H')
        if not hs:
            return "ERROR"
        #possibly could just look for atoms with name 'HC'
        hcs = hs.get(lambda x: x.bonds[0].atom1.name=='C' or \
                        x.bonds[0].atom2.name=='C')
        if not hcs:
            #there is nothing to delete here
            return 'ERROR'
        self.vf.deleteAtomSet(hcs)



class ModifyNTerminus(MVCommand):
    """This command is used to modify residues which become internal n-termini
because some residues are missing within a chain in a crystal structure. 
Hydrogens are added or subtracted from nitrogen atom of the internal 
n-terminus so that the natom ends up with one sp2-hydrogen which is what it
would have in an intact chain.
   \nPackage : Pmv
   \nModule  : repairCommands
   \nClass   : ModifyNTerminus
   \nCommand : modifyNTerminus
   \nSynopsis:\n
        None<--- modifyNTerminus(res,**kw)
   \nRequired Arguments:\n    
        resSet --- set of residues which are inside a chain and not bonded to a previous residue
    """
    
    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('typeAtoms'):
            self.vf.loadCommand('editCommands', 'typeAtoms','Pmv',
                                topCommand=0)
        if not self.vf.commands.has_key('typeBonds'):
            self.vf.loadCommand('editCommands', 'typeBonds','Pmv',
                                topCommand=0)
        if not self.vf.commands.has_key('deleteAtomSet'):
            self.vf.loadCommand('deleteCommands', 'deleteAtomSet','Pmv',
                                topCommand=0)
        self.addh = AddHydrogens()
            

    def __call__(self, resSet, renumber=1, **kw):
        """None<---modifyNTerminus(res,**kw)        
        \nresSet --- set of residues which are inside a chain and not bonded to a previous residue
        """
        return apply(self.doitWrapper,(resSet, renumber,), kw)


    def doit(self, resSet, renumber):
        """ None <--- modifyNTerminus(resSet)"""
        resSet = self.vf.expandNodes(resSet)
        if len(resSet)==0: return 'ERROR'

        resATS = resSet.atoms
        #make sure natom has 1 sp2 hydrogen 'HN', only
        #if it's already there, return
        natoms = resATS.get(lambda x: x.name=='N')
        #print 'natoms=', natoms
        if not natoms:
            msg = resSet.name + ' missing N atom'
            self.warningMsg(msg)
            return 'ERROR'
        self.vf.fixHNames(self.vf.allAtoms)
        #remove any residues which already have atom 'HN'
        #print 'before subtract resSet.name=', resSet.name
        #resSet = resSet - resSet.get(lambda x:'HN' in x.children.name)
        #print 'after subtract resSet.name=', resSet.name

        mols = resATS.top.uniq()
        hs = resATS.get(lambda x: x.element=='H')
        if hs is not None:
            NHs = hs.get(lambda x:(x.bonds[0].atom1.name=='N' or \
                                    x.bonds[0].atom2.name=='N') and \
                                    x.name!='HN')
            print 'NHs==None', NHs==None
            if NHs:
                print 'deleting ', NHs
                self.vf.deleteAtomSet(NHs)

        for at in resATS:
            if not hasattr(at,'babel_type'):
                msg = 'atom has no babel_type: calling typeAtoms'
                self.warningMsg(msg)
                #typeAtoms does whole molecule
                self.vf.typeAtoms(at, topCommand=0)
                break
        resBONDS = resATS.bonds[0]
        untypedBonds = filter(lambda x:x.bondOrder==None, resBONDS)
        #don't do this if it is not necessary
        if len(untypedBonds):
            for m in mols:
                self.vf.typeBonds(m, withRings=0, topCommand=0)

        natoms.babel_type = 'Npl'
        for n in natoms:
            print 'processing n=', n.full_name()
            if n.parent.type!='PRO':
                hat = self.addh.add_vinyl_hydrogens(n, 1.02)
            else:
                continue
                #this adds a bogus hydrogen along what would be the N_C bond
                #hat = self.addh.add_sp2_hydrogen(n, 1.02)
            #always just add one hydrogen
            h = hat[0]
            #for h in hat:
            childIndex = n.parent.children.index(n) + 1
            name = 'HN'
            # create the HN atom object
            atom = Atom(name, n.parent, top=n.top,
                        childIndex=childIndex, assignUniqIndex=0)
            atom._coords = [ h[0] ]

            if hasattr(n, 'segID'): 
                atom.segID = n.segID
            atom.hetatm = 0
            atom.alternate = []
            atom.element = 'H'
            atom.occupancy = 1.0
            atom.conformation = 0
            atom.temperatureFactor = 0.0
            atom.babel_atomic_number = 1
            atom.babel_type = 'H'
            atom.babel_organic = 1

            # create the Bond object bonding Hatom to heavyAtom
            bond = Bond( n, atom, bondOrder=1)

            # create the color entries for all geoemtries
            # available for the heavyAtom
            for key, value in n.colors.items():
                atom.colors[key]=(0.0, 1.0, 1.0)
                atom.opacities[key]=1.0
            if hasattr(n, 'chargeSet') and n.chargeSet=='Kollman':
                #FIX THIS
                atom._charges['Kollman'] = n.charge/2.0 
                atom.chargeSet = 'Kollman'
            
        # update the allAtoms set in the molecules
        for mol in mols:
            mol.allAtoms = mol.chains.residues.atoms
            if renumber:
                fst = mol.allAtoms[0].number
                mol.allAtoms.number = range(fst, len(mol.allAtoms)+fst)
        self.vf.allAtoms = self.vf.Mols.chains.residues.atoms


    def buildCoords(self, atom):
        # c2 is neigbour of atom
        c2 = atom.bonds[0].atom1
        if c2==atom:
            c2= atom.bonds[0].atom2
        #print 'c2.name=', c2.name

        # c3 is neigbour of c2 different from c1
        c3 = c2.bonds[0].atom1
        if c3==c2: c3 = c2.bonds[0].atom2

        if c3==atom:
            c3 = c2.bonds[1].atom1
            if c3 == c2:
                c3 = c2.bonds[1].atom2
        # c4 is neighbor of c2 different from c1 and c3
        c4 = c2.bonds[0].atom1
        if c4==c2:
            c4 = c2.bonds[0].atom2
        if c4 == atom or c4 == c3:
            c4 = c2.bonds[1].atom1
            if c4 == c2:
                c4 = c2.bonds[1].atom2
            if c4==atom or c4 == c3:
                if len(c2.bonds)>2:
                    c4 = c2.bonds[2].atom1
                    if c4==c2:
                        c4 = c2.bonds[2].atom2
                else:
                    c4 = None

        c = atom.coords
        b_length = 1.02
        v = vec3(c3.coords, c2.coords, b_length)
        cH1 = [ c[0]+v[0], c[1]+v[1], c[2]+v[2] ]


        print 'c4==None', c4==None
        if c4 is not None:
            print 'c4=', c4.full_name()
            v = Numeric.array(vec3(c3.coords, c2.coords, b_length))
            #v1 = Numeric.array(vec3(cH1, c, b_length ))
            v1 = Numeric.array(vec3(c4.coords, c2.coords, b_length))
            u = v + v1
            u = u/math.sqrt(u[0]*u[0] + u[1]*u[1] + u[2]*u[2])
            #this is normalising u,
            #maybe vec3 has a method to do this?
            #c is atom.coords
            w = vec3(c2.coords, c, 1)
            dotproduct = (u[0]*w[0] + u[1]*w[1] + u[2]*w[2])
            dp = dotproduct
            w_perp = u - Numeric.array([dp*w[0],dp*w[1],dp*w[2]])
            #print 'w_perp=', w_perp
            cF = 0.5        #math.cos(60.*math.pi/180.)
            sF = 0.866      #math.cos(60.*math.pi/180.)
            cH1 = Numeric.array(c) + Numeric.array([cF*w[0],cF*w[1],cF*w[2]])+ \
                   Numeric.array([sF*w[0] +sF*w[1] + sF*w[2]])
            cH2 = Numeric.array(c) + Numeric.array([cF*w[0],cF*w[1],cF*w[2]])- \
                   Numeric.array([sF*w[0] +sF*w[1] + sF*w[2]])
            #ch1 = [round(cH1[0],4), round(cH1[1],4), round(cH1[2],4)]
            #ch2 = [round(cH2[0],4), round(cH2[1],4), round(cH2[2],4)]
        else:
            # we build second H like a sp2_hydrogen using c2, c, H
            v = vec3(c2.coords, c)
            v1 = vec3(cH1, c, b_length )
            s = [ v[0]+v1[0], v[1]+v1[1], v[2]+v1[2] ]
            mag = b_length / math.sqrt( s[0]*s[0] + s[1]*s[1] + s[2]*s[2])
            cH2 = [c[0] + (s[0]*mag), c[1] + (s[1]*mag), c[2] + (s[2]*mag)]

        ch1 = [round(cH1[0],4), round(cH1[1],4), round(cH1[2],4)]
        ch2 = [round(cH2[0],4), round(cH2[1],4), round(cH2[2],4)]
        print 'returning :', [[ch1], [ch2]]
        return [[ch1], [ch2]]
        



class ModifyTermini(MVCommand):
    """This class detects residues within a chain which are not bonded to a previous
residue in the chain and those not bonded to a subsequent residue in the
chain.  It calls ModifyNTerminus to edit hydrogens bonded to the nitrogen
atom of the first kind of residue  and ModifyCTerminus to edit hydrogens bonded terminal carbon in the second kind of intra-chain breaks.
   \nPackage : Pmv
   \nModule  : repairCommands
   \nClass   : ModifyTermini 
   \nCommand : modifyTermini
   \nSynopsis:\n
        None<- modifyTermini(res, check, **kw)
   \nRequired Arguments:\n 
        \nnodes to be checked for intrachain deletions. 
        \ncheck --- if check, each molecule in nodes.top is checked to be sure that each of its residues is a standard type. If not, looking for peptide connection breaks doesn't make sense so command exits with an error.If the user's molecule has non-standard residues, he can call this with check=0... 
    """


    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('modifyCTerminus'):
            self.vf.loadCommand('editCommands', 'modifyCTerminus','Pmv',
                                topCommand=0)
        if not self.vf.commands.has_key('modifyNTerminus'):
            self.vf.loadCommand('editCommands', 'modifyNTerminus','Pmv',
                                topCommand=0)
        self.resKeys = q.keys()


    def __call__(self, nodes, check=1, **kw):
        """None<- modifyTermini(res, check, **kw)
        \nnodes to be checked for intrachain deletions. 
        \ncheck --- if check, each molecule in nodes.top is checked to be sure that each of its residues is a standard type. If not, looking for peptide connection breaks doesn't make sense so command exits with an error.If the user's molecule has non-standard residues, he can call this with check=0... 
        """
        return apply(self.doitWrapper,(nodes,check,), kw)


    def doit(self, nodes, check):
        nodes = self.vf.expandNodes(nodes)
        mols = nodes.top.uniq()
        if len(nodes)==0: return 'ERROR'
        resSet = nodes.findType(Residue).uniq()
        changed = 0
        if check:
            dict = {}
            #check whether this is a resSet of peptide residues
            for m in resSet.top:
                for r in m.chains.residues:
                    dict[r.type] = 0
                for t in dict.keys():
                    if t not in self.resKeys:
                        print res.top.name, ' has non-standard residue types'
                        return 'ERROR'
                        
        defectiveCs = ResidueSet()
        defectiveNs = ResidueSet()
        for res in resSet:
            #check whether this is a resSet of peptide residues
            if res!=res.parent.children[-1]:
                catoms = res.atoms.get(lambda x: x.name=='C')
                if not catoms:
                    print res.name, ' missing C atom'
                    continue
                catom = catoms[0]
                needToFix = 1
                for b in catom.bonds:
                    at2 = b.atom1
                    if at2==catom:
                        at2 = b.atom2
                    if at2.name=='N':
                        needToFix = 0
                        break
                if needToFix:
                    #print 'calling modifyCTerminus on ', res.name
                    defectiveCs.append(res)
                    #self.vf.modifyCTerminus(res, log=0)
                    #changed = 1
            if res!=res.parent.children[0]:
                natoms = res.atoms.get(lambda x: x.name=='N')
                if not natoms:
                    print res.name, ' missing N atom'
                    continue
                natom = natoms[0]
                needToFix = 1
                for b in natom.bonds:
                    at2 = b.atom1
                    if at2==natom:
                        at2 = b.atom2
                    if at2.name=='C':
                        needToFix = 0
                        break
                if needToFix:
                    #print 'calling modifyNTerminus on ', res.name
                    defectiveNs.append(res)
                    #self.vf.modifyNTerminus(res, log=0)
                    #changed = 1
        if len(defectiveCs):
            self.vf.modifyCTerminus(defectiveCs)
            changed = 1
        if len(defectiveNs):
            self.vf.modifyNTerminus(defectiveNs)
            changed = 1
        if changed:
            self.vf.displayLines(mols, negate=1, log=0)
            self.vf.displayLines(mols, negate=0, log=0)
                

    def guiCallback(self):
        sel = self.vf.getSelection()
        if len(sel):
            if self.vf.userpref['Expand Node Log String']['value'] == 0:
                self.nodeLogString = "self.getSelection()"
            #add simple dialog to get whether to check or not
            t = "This command requires selection to be peptide based. Do you want to check whether the residues are standard?"
            d = SimpleDialog(self.vf.GUI.ROOT, text = t,
                                buttons=['No', 'Yes', 'Cancel'],
                                default=0, title='Check selection?')
            check = d.go()
            if check==2:
                return 'ERROR'
            self.doitWrapper(sel, check=check, log=1, redraw=0)

        

ModifyTerminiCommandGUI = CommandGUI()
ModifyTerminiCommandGUI.addMenuCommand('menuRoot', 'Edit',
                    'Modify Termini', cascadeName='Misc')



#class AttachNonBondedFragments(MVCommand):
#    """
#This class detects fragments in a molecule which  are not bonded and builds
#bonds between closest atoms.  It also bonds 'orphan' atoms to the closest atom

#    """

#    def __call__(self, nodes, **kw):
#        """None<- attach_nonbonded_fragments(nodes, check, **kw)
#nodes to be checked for non_bonded_fragments
#"""
#        nodes = self.vf.expandNodes(nodes)
#        if not len(nodes):
#            return "ERROR"
#        return apply(self.doitWrapper,(nodes,), kw)


#    def doit(self, nodes, **kw):
#        nodes = self.vf.expandNodes(nodes)
#        mols = nodes.top.uniq()
#        if len(nodes)==0: return 'ERROR'
#        changed = 0
#        for m in mols:
#            changed = changed + m.attach_nonbonded_fragments()
#        if changed:
#            self.vf.displayLines(mols, negate=1, log=0)
#            self.vf.displayLines(mols, negate=0, log=0)
#        return changed
#                

#        
#    def guiCallback(self):
#        sel = self.vf.getSelection()
#        if len(sel):
#            kw = {}
#            kw['log'] = 1
#            kw['redraw'] = 1
#            return apply(self.doitWrapper, (sel,), kw)


#AttachNonBondedFragmentsGUI = CommandGUI()
#AttachNonBondedFragmentsGUI.addMenuCommand('menuRoot', 'Edit',
#                    'Attach Non-bonded Fragments', cascadeName='Misc')


commandList=[
    {'name':'editHist_hGC','cmd':EditHistHydrogensGUICommand(),
     'gui': EditHistHydrogensGUICommandGUI},
    {'name':'editHist_h','cmd':EditHistHydrogens(), 'gui': None},
    {'name':'checkForMissingAtomsGC','cmd':CheckForMissingAtomsGUICommand(),
     'gui': CheckForMissingAtomsGUICommandGUI},
    {'name':'checkForMissingAtoms','cmd':CheckForMissingAtoms(), 'gui': None},
    {'name':'checkForCloseContactsGC','cmd':CheckForCloseContactsGUICommand(),
     'gui': CheckForCloseContactsGUICommandGUI},
    {'name':'checkForCloseContacts','cmd':CheckForCloseContacts(), 'gui': None},
    {'name':'repairMissingAtomsGC','cmd':RepairMissingAtomsGUICommand(),
     'gui': RepairMissingAtomsGUICommandGUI},
    {'name':'repairMissingAtoms','cmd':RepairMissingAtoms(), 'gui': None},

    {'name':'add_oxtGC','cmd':AddOXTGUICommand(), 'gui': AddOXTGUICommandGUI},
    {'name':'add_oxt','cmd':AddOXT(), 'gui': None},
    {'name':'modifyCTerminus','cmd':ModifyCTerminus(), 'gui': None},
    {'name':'modifyNTerminus','cmd':ModifyNTerminus(), 'gui': None},
    {'name':'modifyTermini','cmd':ModifyTermini(), 
            'gui': ModifyTerminiCommandGUI},
    #{'name':'attach_nonbonded_fragments','cmd':AttachNonBondedFragments(), 'gui': AttachNonBondedFragmentsGUI},
#    {'name':'addBondGC','cmd':AddBondCommandGUICommand(),
#     'gui': AddBondCommandGUICommandGUI},
#    {'name':'addBond','cmd':AddBondCommand(), 'gui': None},
#    {'name':'removeBondGC','cmd':RemoveBondCommandGUICommand(),
#     'gui': RemoveBondCommandGUICommandGUI},
#    {'name':'removeBond','cmd':RemoveBondCommand(), 'gui': None},
    ]



def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
