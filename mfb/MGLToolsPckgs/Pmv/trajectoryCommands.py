## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/trajectoryCommands.py,v 1.18 2010/02/25 23:03:46 autin Exp $
#
# $Id: trajectoryCommands.py,v 1.18 2010/02/25 23:03:46 autin Exp $
#


# implements classes to read and play GROMACS trajectory files
import warnings
import os
from MolKit.trajParser import trrParser, xtcParser
import Pmw, Tkinter
import numpy.oldnumeric as Numeric
from opengltk.OpenGL import GL
import time

from mglutil.util.misc import ensureFontCase

class Trajectory:
    """class to store GROMACS trajectory file data"""
    
    def __init__ (self, file, mol = None):

        self.file = file
        self.parser = self.getParser(file)
        self.nbAtoms = None
        self.nbSteps = None
        self.coords = []
        self.velocities = {}
        self.nbFrames = None
        self.forces = {}
        self.energies = {}
        self.mol = mol
        self.player = None
        


    def getParser(self, file):
        """determine which parser to use"""
        
        fext = os.path.splitext(file)[-1]
        if fext == ".trr":
            return trrParser(file)
        elif fext == ".xtc":
            return xtcParser(file)
        else:
            print "ERROR: unsupported trajectory file format %s"%fext
            return None



    def readTrajectory(self):
        """parse trajectory file"""
        self.parser.read()
        self.coords = self.parser.coords
        self.nbAtoms = len(self.coords[0])
        self.nbFrames = len(self.coords)
        self.velocities = self.parser.velocities
        self.forces = self.parser.forces




from mglutil.gui.BasicWidgets.Tk.player import Player
from Pmv.moleculeViewer import EditAtomsEvent

from mglutil.util.callback import CallBackFunction
from mglutil.gui.InputForm.Tk.gui import InputFormDescr, InputForm, evalString
from mglutil.util.callback import CallbackManager
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from mglutil.util.packageFilePath import findFilePath
import tkMessageBox
from MolKit.pdbParser import PdbParser, PdbqParser, PdbqtParser
from MolKit.groParser import groParser

from string import find

class TrajPlayer(Player):
    """ a GUI to play a trajectory. The class constructor takes a Trajectory object and
        a correspoonding molecule as arguments."""
    
    def __init__(self, mol, traj, vf, titleStr=None, sequenceList=None,
                        idList = None, delta=0, form2=1,
                        ask=1, **kw):
        
        self.mol = mol
        self.traj = traj
        self.startFrame = 0
        self.ask = ask
        mol.allAtoms.addConformation(mol.allAtoms.coords[:])
        self.coordSlot = len(mol.allAtoms[0]._coords) - 1
        self.update(sequenceList, idList)
        kw['master'] = None
        if vf.hasGui :
            kw['master'] = vf.GUI.ROOT
        kw['endFrame'] = self.endFrame
        kw['maxFrame'] = self.endFrame
        kw['form2'] = form2
        kw['titleStr'] = titleStr
        self.vf = vf
        if self.vf.hasGui :
            apply(Player.__init__, (self,), kw)
        try:
            self.form.ifd.entryByName['setanimB']['widget'].grid_forget()
            #print 'withdrew SetAnim button'
            self.form.autoSize()
        except:
            pass

    def update(self, sequenceList=None, idList=None):
        if not sequenceList:
            self.sequenceList = range(len(self.traj.coords))
            #self.sequenceList = self.traj.coords.keys()
        else :
            self.sequenceList = sequenceList
        lenSeq = len(self.sequenceList)
        self.maxFrame = lenSeq
        self.endFrame = lenSeq
        if self.startFrame>lenSeq:
            self.startFrame = 0

        if hasattr(self, 'playModeForm'):
            e = self.playModeForm.descr.entryByName
            endTW = e['endFrameTW']['widget']
            #print 'setting endTW to ', self.endFrame
            endTW.max = self.endFrame
            endTW.set(self.endFrame)
            startTW = e['startFrameTW']['widget']
            startTW.set(self.startFrame)
        if not idList:
            #insert 0 for original state
            idL = range(0, len(self.sequenceList) + 1)
            self.idList = map(str, idL)
        else:
            self.idList = map(str, idList)
        #print "self.idList", self.idList
        
        if hasattr(self, 'form'):
            if hasattr(self.form, 'ent2'):
                newLen = max(map(len, self.idList))
                if newLen>3:
                    #print 'update:updating ent2 width'
                    self.form.ent2.config(width=newLen)
                self.form.ent2.delete(0,'end')
                #could use startFrame if it is valid here:
                if self.startFrame<=len(self.sequenceList) and self.startFrame>0:
                    next_val = str(self.idList[self.startFrame])
                    self.form.ent2.insert(0, next_val)
                    self.currentFrameIndex = self.startFrame
                    self.applyState(self.startFrame-1)
                else:
                    #print "restarting from frame =", self.idList[0]
                    #print self.startFrame, ": index out of range for ", sequenceList, "; resetting startFrame to  0"
                    self.form.ent2.insert(0, str(self.idList[0]))
                    #this calls applyState with reset flag
                    self.applyState(-1)


    def applyState(self, ind):
        """None<-applyState(ind)"""
        mol = self.mol
        # -1 is key for go back to original
        if int(ind)==-1:
            mol.allAtoms.setConformation(0)
            conf = None
        else:
            #in this case want to get new coords
            #coords = self.traj.coords["frame%d"%ind]
            coords = self.traj.coords[ind]
            coordsarr = (Numeric.array(coords)*10).astype("f")
            allAtoms = self.mol.allAtoms
            allAtoms.updateCoords(coordsarr[:], self.coordSlot)

        if not self.vf.hasGui: return
        event = EditAtomsEvent('coords', mol.allAtoms)
        self.vf.dispatchEvent(event)
        #modEvent = ModificationEvent('edit','coords', mol.allAtoms)
        #mol.geomContainer.updateGeoms(modEvent)
        self.vf.GUI.VIEWER.Redraw()
        #self.showStats()


   


    def SetMode_cb(self, event=None):
        #print 'SetMode'
        #playMode options:
        #   0   play once and stop
        #   1   play continuously in 1 direction
        #   2   play once in 2 directions
        #   3   play continuously in 2 directions
        #play framerate is frame/per second
        if not hasattr(self, 'playModeForm'):
            self.showPlayMode = Tkinter.IntVar()
            self.showFrameParmWidgets = Tkinter.IntVar()
            self.playModeVar = Tkinter.StringVar()
            self.playModeVar.set('once and stop')
            self.playModeList=[ 'once and stop', 
                                'continuously in 1 direction',
                                'once in 2 directions', 
                                'continuously in 2 directions']
            self.frameParmsList=[ 'framerateLabel','framerateTW','startFrameLabel', 
                                  'startFrameTW', 'endFrameLabel', 'endFrameTW', 
                                  'stepSizeLabel', 'stepSizeTW']

            #self.showListVar = Tkinter.IntVar()
            ifd2 = InputFormDescr(title='Set Play Options')    
            ## ifd2.append({'name':'selectCB',
##                 'widgetType': Tkinter.Checkbutton,
##                 'tooltip':'show ids of current ordered conformation list',
##                 'wcfg':{ 'text':'Show Conf List',
##                         #'command': self.showStatesList,
##                         #'variable': self.showListVar,
##                        },
##                 'gridcfg':{'sticky':'ew', 'row':-1, 'column':1}})
##                 #'gridcfg':{'sticky':'ew'}})
            ifd2.append({'name':'playModeMb',
                'widgetType': Tkinter.Menubutton,
                'tooltip':'set play mode choice',
                'wcfg':{ 'text':'Play Mode',
                       },
                'gridcfg':{'sticky':'we'}})
                #'gridcfg':{'sticky':'w', 'columnspan':2}})
            ifd2.append({'name':'adjustFrameParmsMb',
                'widgetType': Tkinter.Checkbutton,
                'tooltip':'opens panel to set play rate, start conf number, end conf number \nand step size for playing conf sequence',
                'wcfg':{ 'text':'Play Parameters',
                        'command': self.showFrameParms_cb,
                        'variable': self.showFrameParmWidgets,
                       },
                'gridcfg':{'sticky':'w', 'row':-1, 'column':1}})
            ifd2.append( {'name': 'framerateLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'frame rate:',
                        'font':(ensureFontCase('helvetica'),12,'bold')},
                    'gridcfg':{'sticky':'w'}})
            ifd2.append({'name': 'framerateTW',
                    'wtype':ThumbWheel,
                    'widgetType':ThumbWheel,
                    'tooltip':'set max num of confs to be displayed per second',
                    'wcfg':{'labCfg':{'fg':'black', 'side':'left', 'text':''},
                        'showLabel':1, 'width':100,
                        'min':0,
                        'max':100,
                        'lockBMin':1,
                        'lockBMax':0,
                        'lockBIncrement':1,
                        'value':self.framerate,
                        'oneTurn':100,
                        'type':'float',
                        'increment':.1,
                        'callback':self.setMode_cb,
                        'canvascfg':{'bg':'red'},
                        'wheelLabcfg1':{'font':(ensureFontCase('times'),14,'bold')},
                        'wheelLabcfg2':{'font':(ensureFontCase('times'),14,'bold')},
                        'continuous':0, 'wheelPad':1, 'height':20},
                    'gridcfg':{'sticky':'nesw', 'row':-1, 'column':1}})
            ifd2.append( {'name': 'startFrameLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'start frame:',
                        'font':(ensureFontCase('helvetica'),12,'bold')},
                    'gridcfg':{'sticky':'w'}})
            ifd2.append({'name': 'startFrameTW',
                    'wtype':ThumbWheel,
                    'widgetType':ThumbWheel,
                    'tooltip':'set number of first conf to be displayed',
                    'wcfg':{
                        'labCfg':{
                            'fg':'black',
                            'side':'left',
                            'text':''
                            },
                        'showLabel':1, 'width':100,
                        'min':0,
                        'max':self.endFrame,
                        'lockBMin':0,
                        'lockBMax':1,
                        'lockBIncrement':1,
                        'value':self.startFrame,
                        'oneTurn':10,
                        'type':'int',
                        'increment':1,
                        'callback':self.setMode_cb,
                        'canvascfg':{'bg':'green'},
                        'wheelLabcfg1':{'font':(ensureFontCase('times'),14,'bold')},
                        'wheelLabcfg2':{'font':(ensureFontCase('times'),14,'bold')},
                        'continuous':0, 'wheelPad':1, 'height':20},
                    'gridcfg':{'sticky':'ew', 'row':-1,  'column':1}})
            ifd2.append( {'name': 'endFrameLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'end frame:',
                        'font':(ensureFontCase('helvetica'),12,'bold')},
                    'gridcfg':{'sticky':'w'}})
            ifd2.append({'name': 'endFrameTW',
                    'wtype':ThumbWheel,
                    'widgetType':ThumbWheel,
                    'tooltip':'set number of last conf to be displayed',
                    'wcfg':{
                        'labCfg':{
                            'fg':'black',
                            'side':'left',
                            'text':''
                            },
                        'showLabel':1, 'width':100,
                        'min':self.startFrame,
                        'max':self.maxFrame,
                        'lockBMin':1,
                        'lockBMax':0,
                        'lockBIncrement':1,
                        'value':self.endFrame,
                        'oneTurn':10,
                        'type':'int',
                        'increment':1,
                        'callback':self.setMode_cb,
                        'canvascfg':{'bg':'green'},
                        'wheelLabcfg1':{'font':(ensureFontCase('times'),14,'bold')},
                        'wheelLabcfg2':{'font':(ensureFontCase('times'),14,'bold')},
                        'continuous':0, 'wheelPad':1, 'height':20},
                    'gridcfg':{'sticky':'nesw', 'row':-1, 'column':1}})
            ifd2.append( {'name': 'stepSizeLabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'step size:',
                        'font':(ensureFontCase('helvetica'),12,'bold')},
                    'gridcfg':{'sticky':'w'}})
            ifd2.append({'name': 'stepSizeTW',
                    'wtype':ThumbWheel,
                    'widgetType':ThumbWheel,
                    'tooltip':'set step before next conf number: default is 1',
                    'wcfg':{
                        'labCfg':{
                            'fg':'black',
                            'side':'left',
                            'text':''
                            },
                        'showLabel':1, 'width':100,
                        'min':1,
                        'max':1000,
                        'lockBMin':1,
                        'lockBMax':0,
                        'lockBIncrement':1,
                        'value':self.stepSize,
                        'oneTurn':10,
                        'type':'int',
                        'increment':1,
                        'callback':self.setMode_cb,
                        'canvascfg':{'bg':'blue'},
                        'wheelLabcfg1':{'font':(ensureFontCase('times'),14,'bold')},
                        'wheelLabcfg2':{'font':(ensureFontCase('times'),14,'bold')},
                        'continuous':0, 'wheelPad':1, 'height':20},
                    'gridcfg':{'sticky':'nesw', 'row':-1, 'column':1}})
            ifd2.append({'name':'buildB',
                'widgetType': Tkinter.Button,
                'tooltip':'build a new molecule with current conf coords\nand add it to viewer',
                'wcfg':{ 'text':'Build Current',
                        'command': self.Build_cb,
                       },
                'gridcfg':{'sticky':'we'}})
                #'gridcfg':{'sticky':'ew', 'row':-1, 'column':1}})

            ifd2.append({'name':'writeB',
                'widgetType': Tkinter.Button,
                'tooltip':'write a new file with current conf coords',
                'wcfg':{ 'text':'Write Current',
                        'command': self.Write_cb,
                       },
                #'gridcfg':{'sticky':'we'}})
                'gridcfg':{'sticky':'nesw', 'row':-1, 'column':1}})         

            ifd2.append({'name':'cancelB',
                        'widgetType': Tkinter.Button,
                        'wcfg':{
                            'text': 'Close',
                            'command': self.cancelPlayMode_cb,
                        },
                        #'gridcfg':{'sticky':'ew', 'row':-1, 'column':1}})
                        'gridcfg':{'sticky':'ew','columnspan':2}}),
            self.playModeForm = InputForm(self.master, self.root,
                        descr = ifd2,
                        modal = 0, blocking = 0)
            self.framerateWidget = ifd2.entryByName['framerateTW']['widget']
            self.startFrameWidget = ifd2.entryByName['startFrameTW']['widget']
            self.endFrameWidget = ifd2.entryByName['endFrameTW']['widget']
            self.stepSizeWidget = ifd2.entryByName['stepSizeTW']['widget']
            self.frameParmCfgs = []
            self.frameParmWidgets = []
            for i in self.frameParmsList:
                ent = ifd2.entryByName[i]
                self.frameParmCfgs.append(ent['gridcfg'])
                self.frameParmWidgets.append(ent['widget'])
            self.playModeMb = ifd2.entryByName['playModeMb']['widget']
            self.playModeMb.bind('<ButtonPress>', self.buildPlayModeMenu, add='+')
            self.showFrameParms_cb()
            #self.showList = ifd2.entryByName['selectCB']['widget']
        else:
            self.playModeVar.set(self.playModeList[self.playMode])
            self.framerateWidget.set(self.framerate)
            self.startFrameWidget.set(self.startFrame)
            self.endFrameWidget.set(self.endFrame)
            self.stepSizeWidget.set(self.stepSize)
            self.playModeForm.deiconify()
        self.playModeForm.autoSize()

    def buildPlayModeMenu(self, event=None):
        mB = self.playModeMb
        keyList = self.playModeList
        if not self.showPlayMode.get():
            #mB.config(bg='white')
            if not hasattr(mB, 'menu'):
                mB.menu = Tkinter.Menu(mB)
                mB['menu'] = mB.menu
            else:
                mB.menu.delete(1, 'end')
            for i in range(len(keyList)):
                mB.menu.add_radiobutton(label=keyList[i], var=self.playModeVar, 
                            value=keyList[i], command=self.setMode_cb)
            self.showPlayMode.set(1)
        else:
            mB.menu.unpost()
            self.showPlayMode.set(0)
            
    def showFrameParms_cb(self, event=None):
        if not self.showFrameParmWidgets.get():
            for w in self.frameParmWidgets:
                w.grid_forget()
        else:
            for i in range(len(self.frameParmWidgets)):
                w = self.frameParmWidgets[i]
                cfg = self.frameParmCfgs[i]
                w.grid(cfg)
        self.playModeForm.autoSize()

    def setMode_cb(self, event=None):
        curVal = self.playModeVar.get()
        #print 'setting playMode to ', curVal
        self.playMode = self.playModeList.index(curVal)
        #print 'setting playMode to ', curVal
        self.framerate = round(self.framerateWidget.get(),4)
        #print 'setting self.framerate ->', self.framerate
        self.timestamp= 1./self.framerate
        self.startFrame = self.startFrameWidget.get()
        self.endFrame = self.endFrameWidget.get()
        #print 'set endFrame to', self.endFrame
        self.stepSize = self.stepSizeWidget.get()
        self.playMode = self.playModeList.index(curVal)
        #i think this restarts the player's trip memory
        #that is, hasn't gone in any direction yet
        self.oneDirection = 0
        if not self.stop:
            self.stop = 1
            self.play(self.framerate)

            

    def setPlayMode_cb(self, event=None):
        self.setMode_cb()
        self.cancelPlayMode_cb()
        self.oneDirection = 0
        

    def SetRMSRef_cb(self, event=None):
        print 'in SetRMSRef_cb'
        return


    def Build_cb(self, event=None):
        #print building current
        """None<-Build_cb(mol, event=None)

        builds new molecule with current coordinates and adds it to the viewer
        """
        #FIRST CHECK THAT THIS HASN'T already been built
        #get the current counter content for name of new molecule
        #w = self.form.ifd.entryByName['statesCounter']['widget']
        numStr = self.form.counter.get()
        #numStr = w.get()
        #remember idList has '0' always added at the beginning for input conf
        confInd =  self.idList.index(numStr) - 1
        #CHECK THIS IS CORRECT!!!
        conf = self.sequenceList[confInd]
        self.buildConf(conf, numStr)


    def buildConf(self, conf, nameStr):
        newname = self.mol.name + '_conf_' + nameStr
        if newname in self.vf.Mols.name:
            msg = newname + ' already in viewer. Not building a second copy'
            self.vf.warningMsg(msg)
            return 'ERROR'
        allLines = self.mol.parser.allLines
        newLines = []
        coords = self.mol.allAtoms.coords
        natoms = len(coords)
        ctr = 0
        parser = self.mol.parser.__class__()
        if isinstance(parser, groParser):
            newLines.append(allLines[0])
            newLines.append(allLines[1])
            for l in allLines[2:natoms+2]:
                cc = coords[ctr]/10
                newLines.append(l[:20] +'%8.3f%8.3f%8.3f'%(cc[0],cc[1],cc[2])+ l[44:])
                ctr = ctr+1
            for l in allLines[natoms+2:]:
                newLines.append(l)
        else:
            for l in allLines:
                if find(l, 'ATOM')==0 or find(l, 'HETA')==0:
                    cc = coords[ctr]
                    newLines.append(l[:30] +'%8.3f%8.3f%8.3f'%(cc[0],cc[1],cc[2])+ l[54:])
                    ctr = ctr+1
                else:
                    newLines.append(l)
        
        parser.allLines = newLines
        filename = parser.filename = self.mol.parser.filename + '_conf_' + nameStr
        newMol = parser.parse()[0]          
        newMol.name = newname
        newMol = self.vf.addMolecule(newMol, ask=self.ask)


    def Write_cb(self, event=None):
        #print writing current
        """None<-Write_cb(mol, event=None)
        writes a new file with current coordinates
        """
        filename = self.vf.askFileSave(types=[('pdb files','*.pdb'),('pdbq files', '*.pdbq'),
                        ('pdbqt files', '*.pdbqt'), ('.gro. files', '*.gro'), ("all", "*")], 
                        title="write current conf:")
        if filename is not None:
            self.write_conf(filename)



    def write_conf(self, filename):       
            fptr = open(filename, 'w')
            ctr = 0
            liglines = self.mol.parser.allLines
            coords = self.mol.allAtoms.coords
            natoms = len(coords)
            if isinstance(self.mol.parser, groParser):
                fptr.write(liglines[0])
                fptr.write(liglines[1])
                for l in liglines[2:natoms+2]:
                    cc = coords[ctr]/10
                    fptr.write(l[:20] +'%8.3f%8.3f%8.3f'%(cc[0],cc[1],cc[2])+ l[44:])
                    ctr +=1
            for l in liglines[natoms+2:]:
                fptr.write(l)
            else:
                for l in liglines:
                    if l.find("ATOM")!=0 and l.find("HETATM")!=0:
                        l += "\n"
                        fptr.write(l)
                    else:
                        crds = coords[ctr] 
                        rec = "%s%8.3f%8.3f%8.3f%s\n"%(l[:30],crds[0], crds[1], crds[2],l[54:] ) 
                        fptr.write(rec)
                        ctr += 1
            fptr.close()
    
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import SliderWidget
import Tkinter


class TrajSliderWidget(SliderWidget):

    def __init__(self, master =None, **kw):

        apply(SliderWidget.__init__, (self, master), kw)
        self.draw.pack_forget()
        self.draw.pack(side="left")
        fnt='-*-helvetica-medium-r-narrow-*-*-120-*-*-*-*-*-*'
        label=Tkinter.Label(self.frame, text=str(self.max), font=fnt)
        label.pack(side='left', fill="both", expand="yes")


        
class TrajPlayerCached(TrajPlayer):
    """ This player saves display lists for each frame (when the frame is played for the first time)
        to be used  in consequent replays. """
    
    def __init__(self, mol, traj, vf, titleStr=None, sequenceList=None,
                        idList = None, delta=0, form2=1,
                        ask=1, **kw):
        kw['titleStr'] = titleStr
        kw['sequenceList'] = sequenceList
        kw['idList'] = idList
        kw['delta'] = delta
        kw['form2'] = form2
        kw['ask'] = ask
        TrajPlayer.__init__(self, mol, traj, vf, titleStr=titleStr, sequenceList=sequenceList,
                            idList = idList, delta=delta, form2=form2, ask=ask)
        if vf.hasGui :
            #add a button to clear cache
            # add a slider to the form
            sl = {'name': 'slider',
              'widgetType':TrajSliderWidget,
              'type':int,
              'wcfg':{'label': '0', 'width':120, 'minval':0,'maxval':self.maxFrame, 'incr': 1,
                      'labelsCursorFormat':'%4d', 'sliderType':'int', 'immediate': 1,
                      'command': self.nextFrame},
              'gridcfg':{'sticky':'w','column':2, 'columnspan':4, }
              }
            cb = {'name': 'clearCache',
             'widgetType': Tkinter.Button,
             'text':'Clear rendering cache',
             'tooltip':"Delete cached trajectory rendered frames to regenerate\nnew frames using currently displayed geometry",
             'wcfg':{'bd':4},
             'gridcfg':{'sticky':'w', 'column':6, 'columnspan':5, 'row':-1},
             'command':self.clearCache_cb}
        
            self.form.addEntry(sl)
            self.form.addEntry(cb)
            self.form.descr.entryByName[cb['name']] = cb
            self.form.descr.entryByName[sl['name']] = sl
            self.form.autoSize()
        self.dpyLists ={}

    def nextFrame(self, id):
        id = int(id)
        strID = self.idList[id]
        if self.hasCounter and self.gui:
            self.form.ent2.delete(0,'end')
            self.form.ent2.insert(0, str(strID))
            sl = self.form.descr.entryByName['slider']['widget']
            if int(sl.get()) != id:
                sl.set(id,  update = 0)
        self.currentFrameIndex = int(id)
        #self.currentFrameIndex = self.idList.index(str(id))
        
        self.applyState(self.currentFrameIndex-1) 
        
    def applyState(self, ind):
        """None<-applyState(ind)"""
        mol = self.mol
        viewer = None # self.vf.GUI.VIEWER
        if self.vf.hasGui:
            viewer = self.vf.GUI.VIEWER
        cache_list = False
        # check if we can cache the display list for this frame 
        if self.dpyLists.has_key(ind):
            if self.dpyLists[ind] is not None:
                cache_list = True
                viewer.currentCamera.dpyList = self.dpyLists[ind]
                #viewer.dpyList = self.dpyLists[ind]
                if self.vf.hasGui:
                    viewer.OneRedraw()
                #viewer.Redraw()
            else:
               self.dpyLists.pop(ind) 

        if not cache_list:
            if int(ind)==-1: # -1 is key for go back to original
                mol.allAtoms.setConformation(0)
            else:
                #in this case we want to get new coords
                coords = self.traj.coords[ind]
                coordsarr = (Numeric.array(coords)*10).astype("f")
                allAtoms = self.mol.allAtoms
                allAtoms.updateCoords(coordsarr[:], self.coordSlot)
            #if not self.vf.hasGui: return
            if self.vf.hasGui: 
                self.vf.GUI.VIEWER.singleDpyList = True
            event = EditAtomsEvent('coords', mol.allAtoms)
            self.vf.dispatchEvent(event)
            if self.vf.hasGui: 
                viewer.OneRedraw()
                #viewer.Redraw()
                self.dpyLists[ind] = viewer.currentCamera.dpyList #viewer.dpyList
                viewer.currentCamera.dpyList = None
                #viewer.dpyList = None
                self.vf.GUI.VIEWER.singleDpyList = False
                #print "dpyList: ", ind, self.dpyLists[ind]

                
    def clearCache_cb(self):
        #print "clearing cache: "
        vi = self.vf.GUI.VIEWER
        currentcontext = vi.currentCamera.tk.call(vi.currentCamera._w, 'contexttag')
        for dl in  self.dpyLists.keys():
            if self.dpyLists[dl]is not None:
                if currentcontext != self.dpyLists[dl][1]:
                    print "currentcontext != self.dpyLists[%d][1]" %(dl,), currentcontext, self.dpyLists[dl][1]
                    c = vi.currentCamera
                    c.tk.call(c._w, 'makecurrent')

                #import pdb; pdb.set_trace()
                #print "glDeleteLists TrajPlayerCached", self.dpyLists[dl][0]
                GL.glDeleteLists(self.dpyLists[dl][0], 1)
            self.dpyLists.pop(dl)
    


                    
from Pmv.mvCommand import MVCommand
from ViewerFramework.VFCommand import CommandGUI
from mglutil.gui.InputForm.Tk.gui import InputFormDescr


class OpenTrajectoryCommand(MVCommand):
    """ Command to open and read a trajectory file . Currently supporting Gromacs trajectories:
        .trr and .xtc """
    
    def __init__(self):
        MVCommand.__init__(self) 
        self.trajFile = None

    def onAddCmdToViewer(self):
        if self.vf.hasGui and not self.vf.commands.has_key("playTrajectory"):
            self.vf.loadCommand("trajectoryCommands", "playTrajectory", "Pmv", topCommand = 0)
                
        if not hasattr(self.vf, "Trajectories"):
            self.vf.Trajectories = {}

    def guiCallback(self):
        """opens a trajectory file (curenly .trr, .xtc)""" 
        
        trajFile = self.vf.askFileOpen(types=[('select trajectory filename:', '*.trr *.xtc'),
                                             ("Gromacs .trr", "*.trr"), ("Gromacs .xtc", "*.xtc"),
                                             ('all files','*')],
                                      title = 'Trajectory File:')

        if trajFile:
            self.trajFile = trajFile
            self.doitWrapper(trajFile)

    def doit(self, trajFile, ask=True):
        """creates a Trajectory object, uses its parser to read the trajectory file,
        adds created Trajectory object to self.vf.Trajectories dictionary"""
        
        name = os.path.split(trajFile)[1]
        trajnames = self.vf.Trajectories.keys()
        if name in trajnames:
            if ask:
                from mglutil.gui.InputForm.Tk.gui import InputFormDescr
                ifd = InputFormDescr(title = '')
                ifd.append({'widgetType':Pmw.EntryField,
                            'name':'newtraj',
                            'required':1,
                            'wcfg':{'labelpos':'w',
                                    'label_text': "Trajectory %s exists.\nEnter new name:"%(name,),
                                    'validate':None},
                            'gridcfg':{'sticky':'we'}
                            })

                vals = self.vf.getUserInput(ifd)
                if len(vals)>0:
                    assert not vals['newtraj'] in trajnames
                    name = vals['newtraj']
                else:
                    return None
            else:
                name = name+str(len(trajnames))
        trj = Trajectory(trajFile)
        if trj.parser:
            trj.readTrajectory()

            self.vf.Trajectories[name] = trj
            if self.vf.commands.has_key("playTrajectory"):
                if self.vf.playTrajectory.ifd:
                    cb = self.vf.playTrajectory.ifd.entryByName['trs']['widget']
                    sl = cb.component('scrolledlist')
                    trajnames = self.vf.Trajectories.keys()
                    sl.setlist(trajnames)
                    cb.selectitem(name)
            return name
        else: return None

    def __call__(self, trajFile, ask=False, **kw):
        """trajName<-openTrajectory(trajFile)
           open aand parse a trajectory file (.trr or .xtc)."""
        
        self.doitWrapper(trajFile, ask)

            
OpenTrajectoryGUI = CommandGUI()
OpenTrajectoryGUI.addMenuCommand('menuRoot', "Trajectory", "Read...")
#OpenTrajectoryGUI.addMenuCommand('menuRoot', 'File', 
#                         'Trajectory (Gromacs)', cascadeName='Read', index=3)      




class PlayTrajectoryCommand (MVCommand):
    """This class allows the user to select/read a trajectory and a corresponding molecule.
       It invokes TrajPlayer interface to play selected trajectory"""
    
    def __init__(self):
        MVCommand.__init__(self)
        self.trajectory = None
        self.player = None
        self.isDisplayed = 0
        self.ifd =None

    def onAddCmdToViewer(self):
        if self.vf.hasGui and not self.vf.commands.has_key("openTrajectory"):
            self.vf.loadCommand("trajectoryCommands", "openTrajectory", "Pmv", topCommand = 0)
        
        if not hasattr(self.vf, "trajectories"):
            self.vf.Trajectories = {}
        # add a menu entry for openTrajectory command to File->Read menu
        if self.vf.hasGui:
            bar = self.vf.GUI.menuBars['menuRoot']
            filemb = bar.menubuttons["File"]
            readmenu = filemb.menu.children["Read"]
            readmenu.add_command(label="Trajectory(Gromacs)", command=self.vf.openTrajectory.guiCallback)
        
    def onAddObjectToViewer(self, obj):
        if self.ifd:
            w = self.ifd.entryByName['mols']['widget']
            molecules = []
            for mol in self.vf.Mols:
                molecules.append(mol.name)
            w.setlist(molecules)
            
    def openTrajFile_cb(self):
        """opens a trajectory file (curenly .trr, .xtc)""" 
        
        self.vf.openTrajectory.guiCallback()
            

    def getTrajectory(self, trajFile, ask=True):
        """creates a Trajectory object, uses its parser to read the trajectory file,
           adds created Trajectory object to self.vf.Trajectories dictionary"""
        
        name = os.path.split(trajFile)[1]
        trajnames = self.vf.Trajectories.keys()
        if name in trajnames:
            if ask:
                from mglutil.gui.InputForm.Tk.gui import InputFormDescr
                ifd1 = InputFormDescr(title = '')
                ifd1.append({'widgetType':Pmw.EntryField,
                            'name':'newtraj',
                            'required':1,
                            'wcfg':{'labelpos':'w',
                                    'label_text': "Trajectory %s exists.\nEnter new name:"%(name,),
                                    'validate':None},
                            'gridcfg':{'sticky':'we'}
                            })

                vals = self.vf.getUserInput(ifd1)
                if len(vals)>0:
                    assert not vals['newtraj'] in trajnames
                    name = vals['newtraj']
                else:
                    return None
            else:
                name = name+str(len(trajnames))
        trj = Trajectory(trajFile)
        if trj.parser:
            trj.readTrajectory()

            self.vf.Trajectories[name] = trj
            if self.ifd:
                cb = self.ifd.entryByName['trs']['widget']
                sl = cb.component('scrolledlist')
                trajnames = self.vf.Trajectories.keys()
                sl.setlist(trajnames)
                cb.selectitem(name)
            return name
        else: return None

    def __call__(self, mol, trajName, **kw):
        """None<-GetTrajectory(mol, trajName)
        Looks for the trajectory  in self.vf.Trajectories and pops up the trajectory player GUI.
        """
        
        apply( self.doitWrapper, (mol, trajName), {})




    def buildFormDescr(self, formName):
        if formName == "showtraj":
            ifd = self.ifd = InputFormDescr(title = "Show trajectory")
            trajnames = self.vf.Trajectories.keys()
            molecules = []
            for i in range(len(self.vf.Mols)):
                mol = self.vf.Mols[i]
                molParser = mol.parser
                molStr = molParser.getMoleculeInformation()
                molecules.append(mol.name)

            ifd.append({'widgetType':Tkinter.Label,
                        'wcfg':{'text':'Read trajectory from file:'},
                        'gridcfg':{'sticky': 'e', 'column': 0}
                        })
            
            ifd.append({'name':'fileopen',
                        'widgetType':Tkinter.Button,
                        'wcfg':{'text':"...",#'Read trajectory from file',
                                #'variable': ,
                                'command': self.openTrajFile_cb,
                                'width': 0, 'height': 0,},
                        'gridcfg':{'sticky':'w', 'column':1, 'row':-1}
                        })
            
            ifd.append({'name': 'trs',
                        'widgetType':Pmw.ComboBox,
                        'wcfg':{'labelpos': 'n',
                                'label_text':'or select trajectory from list:',
                                'scrolledlist_items': trajnames,
                                'scrolledlist_listbox_width': 5,
                                'selectioncommand': self.getMol_cb
                                },
                        'gridcfg':{'sticky':'we', 'column': 0,
                                   'columnspan':2},
                        })
            ifd.append({'name': 'mols',
                        'widgetType':Pmw.ComboBox,
                        'wcfg':{'labelpos': 'n',
                                'label_text':'Select molecule',
                                'scrolledlist_items': molecules,
                                'scrolledlist_listbox_width': 5},
                        'gridcfg':{'sticky':'we', 'column': 2, 'row': -1,
                                   'columnspan':2},
                        })
            

            
            ifd.append({'widgetType':Tkinter.Button,
                        'wcfg': {'text': 'Play Trajectory',
                                 'relief' : Tkinter.RAISED,
                                 'borderwidth' : 3,
                                 'command':self.playTraj},
                        'gridcfg':{'sticky':'we', 'column':0, 'columnspan':2},
                        })
            
            ifd.append({'widgetType':Tkinter.Button,
                    'wcfg':{'text': 'Dismiss',
                            'relief' : Tkinter.RAISED,
                            'borderwidth' : 3,
                            'command':self.dismiss_cb},
                    'gridcfg':{'sticky':'we', 'row':-1, 'column':2, 'columnspan':2},
                    })
            
            return ifd

    
            
    def guiCallback(self):
        if not len(self.vf.Mols):
            msg = 'no molecules in viewer'
            self.vf.warningMsg(msg)
            return 'ERROR'
        val = self.showForm('showtraj', force = 1, modal = 0)
        
        #val = self.showForm("showtraj", force = 1, modal = 1)
        
    def getMol_cb(self, trajname):
        
        """callback of the Pmw.ComboBox (trajectory selection)"""
        if trajname:
            if not  self.ifd.entryByName["mols"]["widget"].get():
                mol = self.vf.Trajectories[trajname].mol
                if mol:
                    molwidget = self.ifd.entryByName['mols']['widget']
                    molwidget.selectitem(mol.name)

    def playTraj(self):
        val = self.ifd.form.checkValues()
        mol = None
        traj = None
        if len(val['mols']):
            mol = val['mols'][0]
        if len(val['trs']):
            traj = val['trs'][0]
        if not mol or not traj:
            return
        
        self.doitWrapper(mol, traj)

        
    def dismiss_cb(self):
          """Withdraws the GUI."""
          if self.cmdForms.has_key('showtraj'):
              self.cmdForms['showtraj'].destroy()
              self.ifd =None

    def doit (self, molname, tname):
        # if trajFile is specified - read the trajectory from the file first
        # if trajName specified - look for the trajectory  in self.vf.Trajectories 
        #if trajFile:
        #    tname = self.getTrajectory(trajFile)
        #elif trajName:

        if tname and molname:
            #play the trajectory
            #print "mol" ,mol , "traj",tname
            
            title = "Playing trajectory: %s  Molecule: %s"%(tname, molname)
            mol = self.vf.expandNodes(molname)[0]
            traj = self.vf.Trajectories[tname]
            if not len(traj.coords):
                msg = "Trajectory %s has 0 frames." %(tname,)
                if self.vf.hasGui:
                    self.vf.warningMsg(msg)
                else:
                    print "WARNING:", msg
                return
            
            if len(mol.allAtoms) != len(traj.coords[0]) :
                msg = "Number of atoms in %s molecule\nand length of coordinates in %s\n trajectory are not equal.\nChoose another molecule/trajectory."%(molname, tname)
                if self.vf.hasGui:
                    self.vf.warningMsg(msg)
                else:
                    print "WARNING:", msg
                return
            if traj.player:
                if traj.mol != mol:
                    traj.player.mol = mol
                    traj.player.update()
                    traj.player.form.root.title(title)
                traj.player.showGUI()
            else:
                #player = TrajPlayer(mol, traj, self.vf, form2=1, titleStr = title)
                player = TrajPlayerCached(mol, traj, self.vf, form2=1, titleStr = title)
                traj.player = player
                traj.mol = mol
            self.dismiss_cb()







PlayTrajectoryGUI = CommandGUI()
PlayTrajectoryGUI.addMenuCommand('menuRoot', 'Trajectory', "Play...")



commandList = [
    {'name':'openTrajectory', 'cmd':OpenTrajectoryCommand(), 'gui':OpenTrajectoryGUI},
    {'name':'playTrajectory', 'cmd':PlayTrajectoryCommand(), 'gui':PlayTrajectoryGUI},
    ]

def initModule(vf):
    for dict in commandList:
        vf.addCommand(dict['cmd'],dict['name'],dict['gui'])
