## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

############################################################################
#
# Author: Ruth HUEY, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

# $Header: /opt/cvs/python/packages/share1.5/Pmv/amberCommands.py,v 1.45 2009/11/09 23:43:29 annao Exp $
#
# $Id: amberCommands.py,v 1.45 2009/11/09 23:43:29 annao Exp $
#

import Tkinter, numpy.oldnumeric as Numeric
import Pmw
import glob
from math import pi, sqrt, ceil
from string import split, strip
from os.path import basename, exists
from types import StringType

from sff.amber import Amber94, AmberParm
from sff.amber import prmlib
from sff.amber import BinTrajectory

from ViewerFramework.VFCommand import CommandGUI

from Pmv.mvCommand import MVCommand
from Pmv.stringSelectorGUI import StringSelectorGUI

from MolKit.molecule import Atom, AtomSet, Bond
from MolKit.protein import Chain,Residue
from MolKit.amberPrmTop import Parm
from MolKit import data

from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from mglutil.util.callback import CallBackFunction
from mglutil.util.misc import ensureFontCase

from DejaVu.Geom import Geom
from DejaVu.Spheres import Spheres
from DejaVu.IndexedPolylines import IndexedPolylines

from DejaVu.glfLabels import GlfLabels

Amber94Config = {}
CurrentAmber94 = {}



class SetupAmber94(MVCommand):
    """This command creates an instance of Amber94 class and enters it in Amber94Config dictionary with specified name as the key. The Amber94 instance requires a Parm instance, which can be built from scratch or readin from a file.
    \nPackage : Pmv
    \nModule  : amberCommands
    \nClass   : SetupAmber94
    \nCommand : setupAmber94
    \nSynopsis:\n
    None<-setup_Amber94(chains, key, filename=None, dataDict={}, **kw)\n
    \nArguments:\n
    chains --- atoms to be minimized\n
    key --- identifier to be key for this Amber94 instance in Amber94Config dictionary\n
    filename --- optional filename to read in for prmtop\n
    dataDict --- optional dictionary of parameter data to use for Parm instance\n
    """


    from Pmv.amberCommands import CurrentAmber94

    
    def __init__(self):
        MVCommand.__init__(self)
        self.file = None
        self.fileTypes = [('prm files:', '*.prm'), ('prmtop files:', '*.prmtop'), ('allfiles', '*')]
        self.fileBrowserTitle = "Read Amber PrmTop File"
        self.lastDir = "."


    def onAddCmdToViewer(self):
        if self.vf.hasGui:
            self.useFile = Tkinter.IntVar()
            self.useFile.set(0)
            self.specData = Tkinter.IntVar()
            self.specData.set(0)
            self.keyStr = Tkinter.StringVar()
        else:
            from mglutil.util.misc import IntVar, StringVar
            self.useFile = IntVar(0)
            self.specData = IntVar(0)
            self.keyStr = StringVar()

        
    def __call__(self, chains, key, filename=None, dataDict = {},**kw):
        """None<---setup_Amber94(chains, key, filename=None, dataDict={}, **kw)
         \nchains --- atoms to be minimized
         \nkey --- identifier to be key for this Amber94 instance in Amber94Config dictionary
         \nfilename --- optional filename to read in for prmtop
         \ndataDict --- optional dictionary of parameter data to use for Parm instance
        """
        chains = self.vf.expandNodes(chains)
        if not len(chains):
            return 'ERROR'
        chains = chains.findType(Chain)
        kw['dataDict'] = dataDict
        kw['filename'] = filename
        return apply(self.doitWrapper, (chains, key), kw)


    def doit(self, chains, key, **kw):
        atoms = chains.residues.atoms
        filename = kw['filename']
        if filename is not None:
            if not exists(filename):
                print filename, " does not exist"
                return "ERROR"
            amb_ins = Amber94(atoms, prmfile=filename)
            #this doesn't work!!!
            #parmtop.loadFromFile(filename)
        else:
            dataDict = kw.get('dataDict', {})
            print 'calling Amber94 init with dataDict=', dataDict
            amb_ins = Amber94(atoms, dataDict = dataDict)
        amb_ins.key = key
        Amber94Config[key] = [amb_ins]
        self.CurrentAmber94 = amb_ins
        print 'set CurrentAmber94 to', self.CurrentAmber94
        #Amber94Config values will be a list where instance is list[0] and 
        #sets of parms used for minimizations the rest....
        

    def getFile(self, event=None):
        if self.useFile.get():
            self.file = self.vf.askFileOpen(types=self.fileTypes,
                           idir = self.lastDir,
                           title=self.fileBrowserTitle)


    def guiCallback(self):
        # a molecule must present first
        if not len(self.vf.Mols):
            self.warningMsg('must load molecule first')
            return "ERROR"
        nodes = self.vf.getSelection()
        if not len(nodes):
            self.warningMsg('nothing in the selection')
            return "ERROR"
        #FIX THIS: need to process atoms in units of whole chains
        chains = nodes.findType(Chain).uniq()
        ifd = self.ifd = InputFormDescr(title = " Set Up Amber94 instance:")
        ifd.append({'name':'fileRB0',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'Read from file',
                'variable': self.useFile,
                'command': self.getFile,
                'value':1,
                },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'fileRB1',
            'widgetType':Tkinter.Radiobutton,
            'wcfg':{'text':'Build from atoms',
                'variable': self.useFile,
                'value':0,
                },
            'gridcfg':{'sticky':'w', 'row':-1, 'column':1}})
        ifd.append({'name':'parmDCB',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Specify parm data',
                'variable': self.specData,
                'command': self.setData,
                },
            'gridcfg':{'sticky':'w', 'row':-1, 'column':2}})
        ifd.append({'name': 'nameStr',
            'widgetType':Tkinter.Entry,
            'wcfg':{ 
                    'label': 'Enter identifier',
                    'textvariable': self.keyStr, 
                    },
            'gridcfg':{'sticky':'we', 'columnspan':3}})
        vals = self.vf.getUserInput(self.ifd, modal=0, blocking=1, okcancel=1)
        if len(vals)>0:
            if not self.useFile.get():
                file = None
            else:
                file = self.file
            key = vals['nameStr']      
            kw = {}
            if hasattr(self, 'dataDict'):
                kw['dataDict'] = self.dataDict
            kw['filename'] = file
            return apply(self.doitWrapper, (chains, key), kw)
        else:
            return 'ERROR'


    def setData(self, event=None):
        #print 'in setData'
        #self.ifd.entryByName['parmDCB']['widget'].toggle()
        if not self.specData.get():
            return

        #build lists of available data parameter files
        #which are in MolKit/data and end in [nt,ct,,]_dat.py
        #nt files end in nt_dat.py
        #ct files end in ct_dat.py
        #the rest _dat.py
        ntList = []
        for i in glob.glob(data.__path__[0] + '/*nt_dat.py'):
            ent = split(basename(i),'.')[0]
            ntList.append((ent, None))
            #ntList.append((basename(i), None))
        for i in glob.glob(data.__path__[0] + '/*nt94_dat.py'):
            ent = split(basename(i),'.')[0]
            ntList.append((ent, None))
            #ntList.append((basename(i), None))
        ctList = []
        for i in glob.glob(data.__path__[0] + '/*ct_dat.py'):
            ent = split(basename(i),'.')[0]
            ctList.append((ent, None))
            #ctList.append((basename(i), None))
        for i in glob.glob(data.__path__[0] + '/*ct94_dat.py'):
            ent = split(basename(i),'.')[0]
            ctList.append((ent, None))
            #ctList.append((basename(i), None))
        allList = []
        for i in glob.glob(data.__path__[0] + '/*_dat.py'):
            n = basename(i)
            ent = split(basename(i),'.')[0]
            t = (ent, None)
            if not (t in ntList) and not (t in ctList):
                allList.append(t)
                #allList.append((n, None))
        ifd2 = InputFormDescr(title = " Select Amber94 data dictionaries:")
        ifd2.append({'name':'allDictLB',
            'widgetType':ListChooser,
            'wcfg':{'entries':allList,
                'mode': 'multiple',
                'title': 'data files for\n\nnon-terminal residues:',
                #'command': 
                'lbwcfg':{'height':5, 
                        'selectforeground': 'red',
                        'exportselection': 0,
                        'width': 30},
                },
            'gridcfg':{'sticky':'we'}})
        ifd2.append({'name':'ntDictLB',
            'widgetType':ListChooser,
            'wcfg':{'entries':ntList,
                'mode': 'multiple',
                'title': 'n-terminus residues:',
                #'command': 
                'lbwcfg':{'height':5, 
                        'selectforeground': 'red',
                        'exportselection': 0,
                        'width': 30},
                        },
            'gridcfg':{'sticky':'we'}})
        ifd2.append({'name': 'ctDictLB',
            'widgetType':ListChooser,
            'wcfg':{'entries':ctList,
                'mode': 'multiple',
                'title': 'c-terminus residues:',
                #'command': 
                'lbwcfg':{'height':5, 
                        'selectforeground': 'red',
                        'exportselection': 0,
                        'width': 30},
                        },
            'gridcfg':{'sticky':'we'}})
        vals2 = self.vf.getUserInput(ifd2, modal=0, blocking=1, okcancel=1)
        if len(vals2)>0:
            dataDict = self.dataDict = {}
            dataDict['allDictList'] = vals2['allDictLB']
            dataDict['ntDictList'] = vals2['ntDictLB']
            dataDict['ctDictList'] = vals2['ctDictLB']



SetupAmber94CommandGUI = CommandGUI()
SetupAmber94CommandGUI.addMenuCommand('menuRoot', 'Amber', 'Setup Amber94')



class SetMinimOptsAmber94(MVCommand):
    """
    This class allows you to set minimization options of a Amber94 instance 
These options include cut, nsnb, dield and verbose. NB: this is written as 
a separate class in order to create a clear log.
     \nPackage : Pmv
    \nModule  : amberCommands
    \nClass   : SetMinimOptsAmber94
    \nCommand : setMinimOptsAmber94
    \nSynopsis:\n
    None<-setminimOpts_Amber94(key, **kw)
    \nArguments:\n
    key --- identifier to be key for this Amber94 instance in Amber94Config dictionary\n
    """

    from Pmv.amberCommands import CurrentAmber94

    
    def __call__(self, key, **kw):
        """
        None<-setminimOpts_Amber94(key, **kw)

        """
        return apply(self.doitWrapper, (key,), kw)


    def doit(self, key, **kw):
        if key not in Amber94Config.keys():
            print 'key: ', key, " is not in current Amber94Config "
            return 'ERROR'
        amber94instance = Amber94Config[key][0] 
        amb_ins = self.CurrentAmber94 = amber94instance
        for k in kw.keys():
            assert k in ['cut', 'nsnb', 'ntpr', 'scnb','scee',
                            'mme_init_first', 'dield', 'verbosemm']
        apply(amb_ins.setMinimizeOptions, (), kw)


    def Close_cb(self, ifd, event=None):
        form = ifd.form
        form.withdraw()


    def buildForm(self):
        ifd = self.ifd = InputFormDescr(title = "Set parameters for amber94 minimization:")
        self.verbose = Tkinter.StringVar()
        self.verbose.set('print summary')
        self.verbose_list = ['no print out', 'print summary', 'print summary w/energies']
        self.dield = Tkinter.IntVar()
        self.dield.set(1)
        self.id = Tkinter.StringVar()
        self.id.set(self.CurrentAmber94.key)
        #self.id.set(Amber94Config.keys()[0])
        ifd.append({'widgetType':Pmw.ComboBox,
            'name':'amberIds',
            'wcfg':{'label_text':'Amber94 ids',
                    'entryfield_value':self.id.get(),
                    'labelpos':'w',
                    'listheight':'80',
                    'scrolledlist_items': Amber94Config.keys(),
                    'selectioncommand': self.update,
                    },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'widgetType':Pmw.ComboBox,
            'name':'verbose_cb',
            'wcfg':{'label_text':'',
                    'entryfield_value':self.verbose.get(),
                    'labelpos':'w',
                    'listheight':'80',
                    'scrolledlist_items': self.verbose_list,
                    },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'dield_cb',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'dield -constant dielectric function',
                'variable': self.dield,
                },
            'gridcfg':{'sticky':'w', 'row':-1, 'column':1 }})
        ifd.append({'name':'cut_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                        'text': 'cut -cutoff distance non-bonded interactions',
                    },
                    'type':'float',
                    'min':1.0,'max':3000.0,
                    'precision':2,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'value':8.,
                    'oneTurn':50.,},
             'gridcfg':{'columnspan':2,'sticky':'e'}})
        ifd.append({'name':'nsnb_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                        'text': 'nsnb -number of steps between non-bonded pairlist updates',
                    },
                    'type':'int',
                    'min':1,'max':5000,
                    #'precision':2,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'value':25,
                    'oneTurn':50.,},
             'gridcfg':{'columnspan':2,'sticky':'e'}})
        ifd.append({'name':'ntpr_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                        'text': 'ntpr -number of steps between print out of energy information',
                    },
                    'type':'int',
                    'min':5,'max':5000,
                    #'precision':2,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'value':50,
                    'oneTurn':50.,},
             'gridcfg':{'columnspan':2,'sticky':'e'}})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Accept',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we'},
            'command':self.Accept_cb})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Cancel',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we', 'column':1,'row':-1},
            'command':CallBackFunction(self.Close_cb, ifd)})
        self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW', CallBackFunction(self.Close_cb,ifd))


    def Accept_cb(self, event=None):
        #FIX THIS!!
        self.form.withdraw()
        #get the setupAmber94instance
        key = self.ifd.entryByName['amberIds']['widget'].get()
        amb_ins = Amber94Config[key][0]
        #update minimization Options
        minOptD = {}
        for v in ['cut_tw', 'nsnb_tw','ntpr_tw']:
            val = self.ifd.entryByName[v]['widget'].get()
            s = split(v,'_')[0]
            minOptD[s] = val
            #ideally want to set amber.prmlib.cvar.nsnb etc...???
        w = self.ifd.entryByName['verbose_cb']['widget'].get()
        if w not in self.verbose_list:
            minOptD['verbosemm'] = 1
        else:
            minOptD['verbosemm'] = self.verbose_list.index(w)
        minOptD['dield'] = self.dield.get()
        apply(self.doitWrapper, (key,), minOptD )
        #apply(amb_ins.setMinimizeOptions,(),minOptD)


    def update(self, event=None):
        key = self.ifd.entryByName['amberIds']['widget'].get()
        amb_ins = Amber94Config[key]
        self.CurrentAmber94 = amb_ins
        #THIS SHOULD ADJUST THE DISPLAYED PARAMETERS....
        #for w in []:
            #FIX THIS!!!
            #newval = amber.prmlib.cvar.+ key


    def guiCallback(self):
        if not len(Amber94Config.keys()):
            self.warningMsg('no Amber94 objects present: SetupAmber94 first')
            return 'ERROR'

        if self.CurrentAmber94=={}:
            self.CurrentAmber94 = Amber94Config.values()[0][0]

        #ALLOW USER TO SET parameters here
        if not hasattr(self, 'ifd'):
            self.buildForm()
        else:
            lb =  self.ifd.entryByName['amberIds']['widget']._list
            #make sure to update the listbox:
            lb.delete(0, 'end')
            for k in Amber94Config.keys():
                lb.insert('end', k)
            self.form.deiconify()


SetMinimOptsAmber94CommandGUI = CommandGUI()
SetMinimOptsAmber94CommandGUI.addMenuCommand('menuRoot', 'Amber', 'Minimization',
                                             cascadeName = 'Set Options')



class MinimizeAmber94(MVCommand):
    """
    This class allows you to select an Amber94 instance from Amber94Config
whose keys are ids specified in setup_Amber94 for the Amber94 instances.
You can also set minimization options, freeze atoms, specify constrained 
atoms and anchor atoms and set maxIter, drms and dfpred. The minimization 
can be run repeatedly.
    \nPackage : Pmv
    \nModule  : amberCommands
    \nClass   : MinimizeAmber94
    \nCommand : minimizeAmber94
    \nSynopsis:\n
    return_code<-minimize_amber94(key, **kw)
    \nArguments:\n
    key --- key into Amber94Config dictionary\n
    """

    from Pmv.amberCommands import CurrentAmber94

    def onAddCmdToViewer(self):
        self.energyLabel = GlfLabels('minimize Energy', 
                                     inheritMaterial=0,
                                     shape=(0,3))
        if self.vf.hasGui:
            self.vf.GUI.VIEWER.AddObject(self.energyLabel)
            
        
    def __call__(self, key, **kw):
        """return_code<-minimize_amber94(key, **kw)

\npossible return codes:\n
        >0    converged, final iteration number\n
        -1    bad line search, probably an error in the relation
                of the funtion to its gradient (perhaps from
                round-off if you push too hard on the minimization).\n
        -2    search direction was uphill\n
        -3    exceeded the maximum number of iterations\n
        -4    could not further reduce function value\n
        -5    stopped via signal   (bsd)\n

key is key into Amber94Config dictionary\n
\nkw is dictionary with keys:\n
                    maxIter -maximum number of iterations\n
                    drms -convergence criterion for energy gradient\n
                    dfpred -predicted drop in conj grad func on 1st iteration\n
\nkeys removed before call to minimize:\n
                    callback\n
                    callback_freq\n
        """
        return apply(self.doitWrapper, (key,), kw)


    def doit(self, key, **kw):
        if key not in Amber94Config.keys():
            print 'key: ', key, " is not in current Amber94Config "
            return 'ERROR' 
        amber94instance = Amber94Config[key][0] 
        amb = self.CurrentAmber94 = amber94instance

        #FIX THIS:
        #HOW DO YOU TURN OFF THE CALLBACK???? by setting freq to 0?
        freq = int(kw.get('callback_freq', 0))
        callback = kw.get('callback')

        for k in ['callback_freq', 'callback']:
            if kw.has_key(k):
                del kw[k]
        #if kw.has_key('callback'):
            #del kw['callback']
        #del kw['callback']
        if callback:
            #add the coords here
            if not hasattr(amb, 'coord_index'):
                amb.atoms.addConformation(amb.atoms.coords[:])
                amb.coord_index = len(amb.atoms[0]._coords)-1
            #freq = int(self.callbackFreq.get())
            #print 'setting callback to updateCoords'
            amb.setCallback(self.updateCoords, freq)

        return_code = apply(amber94instance.minimize,(), kw)
        print 'return_code=', return_code
        return  return_code
        

    def updateCoords(self,  cbNum=0, nbat=300, coords=[], energies=[], step=[]):
        #FIX THIS
        #print 'in updateCoords'
        amb = self.CurrentAmber94
        mols = amb.atoms.top.uniq()
        allAtoms = mols.chains.residues.atoms
        newcoords = Numeric.array(amb.coords[:])
        newcoords.shape = (-1,3)
        allAtoms.updateCoords(newcoords.tolist(), amb.coord_index)
        self.vf.displayLines(allAtoms, topCommand=0)
        pos = Numeric.maximum.reduce(amb.atoms.coords).astype('f')
        self.energyLabel.Set(vertices=[pos],
                             labels=[str(amb.energies[8])], tagModified=False)
        if self.vf.hasGui:
            self.vf.GUI.VIEWER.currentCamera.update()
        

    def Close_cb(self, ifd, event=None):
        form = ifd.form
        form.withdraw()


    def buildForm(self):
        ifd = self.ifd = InputFormDescr(title = "Minimize amber94:")
        self.verbose = Tkinter.StringVar()
        self.verbose.set('print summary')
        self.dield = Tkinter.IntVar()
        self.dield.set(1)
        self.callback = Tkinter.IntVar()
        self.callbackFreq = Tkinter.StringVar()
        self.callbackFreq.set('10')
        self.id = Tkinter.StringVar()
        #self.id.set(Amber94Config.keys()[0])
        self.id.set(self.CurrentAmber94.key)
        frozNum = Numeric.add.reduce(self.CurrentAmber94.frozen)
        self.frozenLab = Tkinter.StringVar()
        fstr = 'Currently ' + str(frozNum) + ' frozen atoms'
        self.constrLab = Tkinter.StringVar()
        constrNum = Numeric.add.reduce(self.CurrentAmber94.constrained)
        cstr = 'Currently ' + str(constrNum) + ' constrained atoms'
        self.constrLab.set(cstr)
        ifd.append({'widgetType':Pmw.ComboBox,
            'name':'amberIds',
            'wcfg':{'label_text':'Amber94 ids',
                    'entryfield_value':self.id.get(),
                    'labelpos':'w',
                    'listheight':'80',
                    'scrolledlist_items': Amber94Config.keys(),
                    'selectioncommand': self.update,
                    },
            'gridcfg':{'sticky':'w'}})
            #'gridcfg':{'sticky':'nesw','row':-1, 'column':1}}),
        ifd.append({'name':'setminopts_cb',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'set minimization options',
                'command': self.setMinOpts,
                },
            'gridcfg':{'sticky':'w', 'row':-1,'column':1}})
        ifd.append({'name':'frozen_lab',
            'widgetType': Tkinter.Label,
            'textvariable':self.frozenLab,
            'wcfg':{'font':(ensureFontCase('helvetica'),12,'bold') },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'const_lab',
            'widgetType': Tkinter.Label,
            'textvariable':self.constrLab,
            'wcfg':{'font':(ensureFontCase('helvetica'),12,'bold') },
            'gridcfg':{'sticky':'w','row':-1,'column':1}})
        ifd.append({'name':'setfroz_cb',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'set frozen atoms',
                'command': self.setFrozenAtoms,
                },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'setcons_cb',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'set constrained atoms',
                'command': self.setConstrainedAtoms,
                },
            'gridcfg':{'sticky':'w', 'row':-1,'column':1}})
        #widgets for the run parameters:
        ifd.append({'name':'maxIter_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{
                    'labCfg':{
                    'text': 'maxIter -maximum number of iterations:',
                    },
                    'type':'int',
                    'min':100,
                    'max':20000 ,
                    'value':10000,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'oneTurn':1000,},
             'gridcfg':{'columnspan':2,'sticky':'e'}})
        ifd.append({'name':'drms_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{
                    'labCfg':{
                    'text': 'drms -convergence criterion for energy gradient',
                    },
                    'type':'float',
                    'min':0.0000001,'max':0.000002,
                    'value':0.000001,
                    'precision':6,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'oneTurn':.001,},
             'gridcfg':{'columnspan':2,'sticky':'e'}})
        ifd.append({'name':'dfpred_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{
                    'labCfg':{
                    'text': 'dfpred -predicted drop in conj grad func on 1st iteration',
                    },
                    'type':'float',
                    'min':0.1,'max':20.0,
                    'precision':4,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'value':10.,
                    'oneTurn':1.,},
             'gridcfg':{'columnspan':2,'sticky':'e'}})
        ifd.append({'name':'callback_cb',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'update geometries',
                'variable': self.callback,
                'command': self.disableCallbackFreq,
                },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name': 'callback_ent',
            'widgetType':Tkinter.Entry,
            'wcfg':{ 
                    'label': 'update frequency',
                    #'label': 'callback frequency',
                    'textvariable': self.callbackFreq, 
                    'width':7,
                    'fg':'grey',
                    'state':'disabled',
                    'selectbackground':'#d9d9d9', 
                    'selectforeground':'grey', 
                    },
            'gridcfg':{'sticky':'we', 'row':-1, 'column':1}})
        
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Minimize',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we'},
            'command':self.Accept_cb})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Cancel',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we', 'column':1,'row':-1},
            'command':CallBackFunction(self.Close_cb, ifd)})
        self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW', CallBackFunction(self.Close_cb,ifd))
        #self.ifd.entryByName['amberIds']['widget'].component('entryfield')._entryFieldEntry.config(width=10)


    def disableCallbackFreq(self, event=None):
        w = self.ifd.entryByName['callback_ent']['widget']
        if self.callback.get():
            w.config(state='normal', fg='black', selectbackground='#c3c3c3', 
                                selectforeground='black')
        else:
            w.config(state='disabled', fg='grey', selectbackground='#d9d9d9', 
                                selectforeground='grey')


    def Accept_cb(self, event=None):
        self.form.withdraw()
        #FIX THIS!!
        key = self.ifd.entryByName['amberIds']['widget'].get()
        #if self.callback.get():
            ##add the coords here
            #amb = Amber94Config[key][0]
            #if not hasattr(amb, 'coord_index'):
                #amb.atoms.addConformation(amb.atoms.coords)
                #amb.coord_index = len(amb.atoms[0]._coords)-1
                ##amb.atoms.setConformation(amb.coord_index) 
            #freq = int(self.callbackFreq.get())
            #print 'setting callback to updateCoords'
            #amb.setCallback(self.updateCoords, freq)
        #start minimization
        d = {}
        #for v in [ 'maxIter_esw','drms_esw','dfpred_esw']:
        for v in [ 'maxIter_tw','drms_tw','dfpred_tw']:
            s = split(v,'_')[0]
            val = self.ifd.entryByName[v]['widget'].get()
            #FIX THIS!!!
            ##amber.prmlib.cvar.+ key = v
            d[s] =  val
        d['callback'] = self.callback.get()
        d['callback_freq'] = self.callbackFreq.get()
        return apply(self.doitWrapper, (key,),  d)


    def setMinOpts(self, event=None):
        #turn off button
        self.ifd.entryByName['setminopts_cb']['widget'].toggle()
        self.vf.setminimOpts_Amber94.guiCallback()
 

    def setFrozenAtoms(self, event=None):
        #turn off button
        self.ifd.entryByName['setfroz_cb']['widget'].toggle()
        #print 'calling freezeAtoms'
        numFroz = self.vf.freezeAtoms_Amber94.guiCallback()
        #fstr = 'Currently ' + str(numFroz) + ' frozen atoms'
        #self.frozenLab.set(fstr)


    def setConstrainedAtoms(self, event=None):
        #turn off button
        self.ifd.entryByName['setcons_cb']['widget'].toggle()
        #print 'calling constrainAtoms'
        numConstr = self.vf.constrainAtoms_Amber94.guiCallback()
        cstr = 'Currently ' + str(numConstr) + ' constrained atoms'
        self.constrLab.set(cstr)


    def update(self, event=None):
        key = self.ifd.entryByName['amberIds']['widget'].get()
        amb_ins = Amber94Config[key]
        self.CurrentAmber94 = amb_ins
        #THIS SHOULD ADJUST THE DISPLAYED PARAMETERS....
        #for w in []:
            #FIX THIS!!!
            #newval = amber.prmlib.cvar.+ key


    def guiCallback(self):
        if not len(Amber94Config.keys()):
            self.warningMsg('no Amber94 objects present: SetupAmber94 first')
            return 'ERROR'

        if self.CurrentAmber94=={}:
            self.CurrentAmber94 = Amber94Config.values()[0][0]

        #ALLOW USER TO SET parameters here
        if not hasattr(self, 'ifd'):
            self.buildForm()
        else:
            lb =  self.ifd.entryByName['amberIds']['widget']._list
            #make sure to update the listbox:
            lb.delete(0, 'end')
            for k in Amber94Config.keys():
                lb.insert('end', k)
            self.form.deiconify()


MinimizeAmber94CommandGUI = CommandGUI()
MinimizeAmber94CommandGUI.addMenuCommand('menuRoot', 'Amber', 'Minimize')




class FreezeAtomsAmber94(MVCommand):
    """
    This class allows you to freeze atoms of an Amber94 instance
    \nPackage : Pmv
    \nModule  : amberCommands
    \nClass   : FreezeAtomsAmber94
    \nCommand : freezeAtomsAmber94
    \nSynopsis:\n
        len(frozenAtoms)<-freezeAtoms_amber94(key, atsToFreeze)\n
    \nArguments:\n
    key --- identifier to be key for this Amber94 instance in Amber94Config dictionary\n
    """

    from Pmv.amberCommands import CurrentAmber94


    def __call__(self, key, atsToFreeze, **kw):
        """
        len(frozenAtoms)<-freezeAtoms_amber94(key, atsToFreeze)
        """
        
        if key not in Amber94Config.keys():
            print 'key: ', key, " is not in current Amber94Config "
            return 'ERROR'

        atsToFreeze = self.vf.expandNodes(atsToFreeze)
        if not len(atsToFreeze):
            return 'ERROR'

        atsToFreeze = atsToFreeze.findType(Atom)
        return apply(self.doitWrapper, (key, atsToFreeze), kw)


    def doit(self, key,  atsToFreeze, **kw):
        amb_ins = Amber94Config[key][0]
        self.CurrentAmber94 = amb_ins

        #check that all the atsToFreeze are in amber instances' atoms
        chain_ids = {}
        for c in amb_ins.atoms.parent.uniq().parent.uniq():
            chain_ids[id(c)] = 0

        for c in atsToFreeze.parent.uniq().parent.uniq():
            assert chain_ids.has_key(id(c)), 'atoms to freeze not in Amber94 instance.atoms'

        atsToFreezeIDS = {}
        for at in atsToFreeze:
            atsToFreezeIDS[id(at)] = 0
        atomIndices = map(lambda x, d=atsToFreezeIDS: d.has_key(id(x)), amb_ins.atoms)
        #FIX THIS: it has to be put into the correct c-structure
        #print 'setting ', key, ' frozen to ', atomIndices
        #amb_ins.frozen = atomIndices
        apply(amb_ins.freezeAtoms, (atomIndices,), {})
        numFrozen = Numeric.add.reduce(Numeric.array(amb_ins.frozen))
        print 'numFrozen=', numFrozen
        return numFrozen
        

    def Close_cb(self, ifd, event=None):
        form = ifd.form
        form.withdraw()


    def buildForm(self, tstr, mols, amb_ins):
        ifd = self.ifd = InputFormDescr(title = tstr)
        self.id = Tkinter.StringVar()
        #self.id.set(self.CurrentAmber94.key)
        self.id.set(amb_ins.key)

        frozNum = Numeric.add.reduce(amb_ins.frozen)
        self.frozenLab = Tkinter.StringVar()
        fstr = 'Currently ' + str(frozNum) + ' frozen atoms'
        self.frozenLab.set(fstr)
        ##self.frozenLab.set('Currently 0 frozen atoms')
        #self.constrLab = Tkinter.StringVar()
        #constrNum = Numeric.add.reduce(self.CurrentAmber94.constrained)
        #cstr = 'Currently ' + str(constrNum) + ' constrained atoms'
        #self.constrLab.set(cstr)
        ifd.append({'widgetType':Pmw.ComboBox,
            'name':'amberIds',
            'wcfg':{'label_text':'Amber94 ids',
                    'entryfield_value':self.id.get(),
                    'labelpos':'w',
                    'listheight':'80',
                    'scrolledlist_items': Amber94Config.keys(),
                    'selectioncommand': self.update,
                    },
            'gridcfg':{'sticky':'w','columnspan':2}})
        ifd.append({'name':'frozen_lab',
            'widgetType': Tkinter.Label,
            'textvariable':self.frozenLab,
            'wcfg':{'font':(ensureFontCase('helvetica'),12,'bold') },
            'gridcfg':{'sticky':'w'}})
        #one string selector:
        ifd.append({'name':'frozAtsLab',
            'widgetType':Tkinter.Label,
            'text':'Specify Frozen Atoms:\n',
            'gridcfg':{'sticky':'w'}})
        ifd.append({ 'widgetType':StringSelectorGUI,
             'name':'frozAts','required':1,
             'wcfg':{ 'molSet': mols, 
                      'vf': self.vf,
                      'all':1,
                      'crColor':(0.4,.8,1.),
                      },
             'gridcfg':{'sticky':'we','columnspan':3 }})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Freeze',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we'},
            'command':self.Accept_cb})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Unfreeze all',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we','row':-1,'column':1},
            'command':self.Unfreeze_cb})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Cancel',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we', 'column':2,'row':-1},
            'command':CallBackFunction(self.Close_cb, ifd)})
        self.form = self.vf.getUserInput(ifd, modal=0, blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW', CallBackFunction(self.Close_cb,ifd))


    def updateLabels(self, numFroz):
        for c in [self, self.vf.minimize_Amber94, self.vf.md_Amber94]:
            if hasattr(c, 'frozenLab'):
                fstr = 'Currently ' + str(numFroz) + ' frozen Atoms'
                c.frozenLab.set(fstr)
        

    def Accept_cb(self, event=None):
        #FIX THIS!!
        self.form.withdraw()
        #get the setupAmber94instance
        key = self.ifd.entryByName['amberIds']['widget'].get()
        #amb_ins = Amber94Config[key][0]
        #set frozen atoms:
        frozAts = self.ifd.entryByName['frozAts']['widget'].get()
        if len(frozAts):
            frozAts = frozAts.findType(Atom)
            numFroz = self.doitWrapper(key, frozAts)
            #at this point update whatever you can
            self.updateLabels(numFroz)
        else:
            self.Unfreeze_cb()


    def Unfreeze_cb(self, event=None):
        key = self.ifd.entryByName['amberIds']['widget'].get()
        amb_ins = self.CurrentAmber94
        l = []
        for i in range(len(amb_ins.atoms)):
            l.append(0)
        apply(amb_ins.freezeAtoms, (l,), {})
        numFrozen = Numeric.add.reduce(Numeric.array(amb_ins.frozen))
        self.updateLabels(numFrozen)


    def update(self, event=None):
        key = self.ifd.entryByName['amberIds']['widget'].get()
        amb_ins= Amber94Config[key]
        self.CurrentAmber94 = amb_ins
        print 'set CurrentAmber94 to', self.CurrentAmber94
        #THIS SHOULD ADJUST THE DISPLAYED PARAMETERS....
        #for w in []:
            #FIX THIS!!!
            #newval = amber.prmlib.cvar.+ key


    def guiCallback(self):
        if not len(Amber94Config.keys()):
            self.warningMsg('no Amber94 objects present: SetupAmber94 first')
            return 'ERROR'
        #if not self.CurrentAmber94:
        #    self.warningMsg('no CurrentAmber94 object: SetupAmber94 first')
        #    return 'ERROR'
        #if not len(self.CurrentAmber94):
        #    self.CurrentAmber94 = Amber94Config.keys()[0][0]

        if self.CurrentAmber94=={}:
            self.CurrentAmber94 = Amber94Config.values()[0][0]

        #amb_ins = Amber94Config.values()[0][0]
        amb_ins = self.CurrentAmber94
        key = amb_ins.key
        mols = amb_ins.atoms.top.uniq()
        #ALLOW USER TO SET parameters here
        tstr = "Set atoms to be frozen for  " + key + ":"
        if not hasattr(self, 'ifd'):
            self.buildForm(tstr, mols, amb_ins)
        else:
            lb =  self.ifd.entryByName['amberIds']['widget']._list
            #make sure to update the listbox:
            lb.delete(0, 'end')
            for k in Amber94Config.keys():
                lb.insert('end', k)
            self.ifd.entryByName['frozAts']['widget'].molSet = mols
            self.ifd.title = tstr
            self.ifd.form.root.title(tstr)
            self.form.deiconify()


FreezeAtomsAmber94CommandGUI = CommandGUI()
FreezeAtomsAmber94CommandGUI.addMenuCommand('menuRoot', 'Amber', 'Freeze Atoms',
                                             cascadeName = 'Set Options')



class ConstrainAtomsAmber94(MVCommand):
    """
    This class allows you to constrain atoms of an Amber94 instance
    \nPackage : Pmv
    \nModule  : amberCommands
    \nClass   : ConstrainAtomsAmber94
    \nCommand : constrainAtomsAmber94
    \nSynopsis:\n
    NumConstr<---constrainAtoms_amber94(key, atsToConstrain, anchorPts)\n
    \nArguments:\n
    key --- identifier to be key for this Amber94 instance in Amber94Config dictionary\n
    atsToConstrain --- atomset for which 3D-constrain points are specified in\n
    anchorPts --- a list of 3-D points, one per atsToConstrain\n
    kw --- possible md options\n
    """


    from Pmv.amberCommands import CurrentAmber94
    

    def onAddCmdToViewer(self):
        self.masterGeom = Geom('constrAtsGeom',shape=(0,0), 
                               pickable=0, protected=True)
        self.masterGeom.isScalable = 0
        if self.vf.hasGui:
            self.vf.GUI.VIEWER.AddObject(self.masterGeom)

        self.lines = IndexedPolylines('constrAtsLines', materials = ((1,1,0),),
                                      inheritMaterial=0, lineWidth=3, 
                                      stippleLines=1, protected=True)
        self.spheres = Spheres(name='constrAtsSpheres', shape=(0,3),
                               inheritMaterial=0, radii=0.2, quality=15,
                               materials = ((1.,1.,0.),), protected=True) 
        if self.vf.hasGui:
            for item in [self.lines, self.spheres]:
                self.vf.GUI.VIEWER.AddObject(item, parent=self.masterGeom)
        #constrList will start with coords of ats to constrain, then
        #be adjusted by user to some other 3D points
        self.constrList = []


    def __call__(self, key, atsToConstrain, anchorPts, **kw):
        """NumConstr<-constrainAtoms_amber94(key, atsToConstrain, anchorPts)
        \nkey --- identifier to be key for this Amber94 instance in Amber94Config dictionary
        \natsToConstrain --- atomset for which 3D-constrain points are specified in
        \nanchorPts: a list of 3-D points, one per atsToConstrain
        \nkw: possible md options
        """
        atsToConstrain = self.vf.expandNodes(atsToConstrain)
        if not len(atsToConstrain):
            return 'ERROR'
        if key not in Amber94Config.keys():
            print 'key: ', key, " is not in current Amber94Config "
            return 'ERROR' 
        #assert key in Amber94Config.keys()
            
        return apply(self.doitWrapper, (key, atsToConstrain, anchorPts), kw)


    def doit(self, key,  atsToConstrain, anchorPts,**kw):

        amb_ins = Amber94Config[key][0]
        self.CurrentAmber94 = amb_ins 
        #check that all the atsToConstrain are in amber instances' atoms
        chain_ids = {}
        for c in amb_ins.atoms.parent.uniq().parent.uniq():
            chain_ids[id(c)] = 0

        for c in atsToConstrain.parent.uniq().parent.uniq():
            assert chain_ids.has_key(id(c)), 'atoms to constrain not in Amber94 instance.atoms'

        atsToConstrainIDS = {}
        for at in atsToConstrain:
            atsToConstrainIDS[id(at)] = 0
        atomIndices = map(lambda x, d=atsToConstrainIDS: d.has_key(id(x)), amb_ins.atoms)

        if len(kw):
            apply(amb_ins.setMinimizeOptions,(), kw)

        #warn if wcons is 0:
        #if getattr(prmlib.cvar, 'wcons')==0:
        if prmlib.SFFoptions_wcons_get(amb_ins.sff_opts) == 0:
            self.warningMsg(" currently 0 constraint weight!")
            
        #anchors have 3 correct values when atomIndex is 1, else garbage
        clist = []
        k = 0
        junkCoords = amb_ins.atoms.coords[:]
        for i in range(len(amb_ins.atoms)):
            if atomIndices[i]:
                clist.append(anchorPts[k])
                k = k + 1
            else:
                clist.append(junkCoords[i])
        anchors = Numeric.array(clist).ravel()
        apply(amb_ins.constrainAtoms, (atomIndices, anchors), {})
        numConstr = Numeric.add.reduce(Numeric.array(amb_ins.constrained))
        print 'returning numConstr=', numConstr
        return numConstr
        

    def Close_cb(self, ifd, event=None):
        form = ifd.form
        form.withdraw()


    def buildForm(self, tstr, mols):
        ifd = self.ifd = InputFormDescr(title = tstr)
        self.id = Tkinter.StringVar()
        #self.id.set(self.CurrentAmber94.key)
        #self.id.set(Amber94Config.keys()[0])
        self.id.set(self.CurrentAmber94.key)
        self.constrLab = Tkinter.StringVar()
        cnum = Numeric.add.reduce(self.CurrentAmber94.constrained)
        cstr = 'Currently ' + str(cnum) + ' constrained atoms'
        self.constrLab.set(cstr)
        self.adjustAnchor = Tkinter.StringVar()
        self.adjAnchors = Tkinter.IntVar()
        #self.constrLab.set('Currently 0 constrained atoms')
        ifd.append({'widgetType':Pmw.ComboBox,
            'name':'amberIds',
            'wcfg':{'label_text':'Amber94 ids',
                    'entryfield_value':self.id.get(),
                    'labelpos':'w',
                    'listheight':'80',
                    'scrolledlist_items': Amber94Config.keys(),
                    'selectioncommand': self.update,
                    },
            'gridcfg':{'sticky':'w','columnspan':3}})
        #one string selector:
        ifd.append({'name':'constr_lab',
            'widgetType': Tkinter.Label,
            'textvariable':self.constrLab,
            'wcfg':{'font':(ensureFontCase('helvetica'),12,'bold') },
            'gridcfg':{'sticky':'w','columnspan':3}})
        ifd.append({'name':'constrAtsLab',
            'widgetType':Tkinter.Label,
            'text':'Specify Constrained Atoms:\n',
            'gridcfg':{'sticky':'w','columnspan':3}})
        ifd.append({ 'widgetType':StringSelectorGUI,
             'name':'constrAts','required':1,
             'wcfg':{ 'molSet': mols, 
                      'vf': self.vf,
                      'all':1,
                      'crColor':(1.,0.,0.),
                      },
             'gridcfg':{'sticky':'we' ,'columnspan':3}})
        ifd.append({'name':'anchorCB',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'Adjust anchorPts ',
                'variable': self.adjAnchors,
                'command': self.setAnchors,
                },
            'gridcfg':{'sticky':'w' }})
            #'gridcfg':{'sticky':'w' ,'columnspan':3}})
        ##Should THIS go here?
        ifd.append({'name':'wcons_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                     'text':'wcons -restraint weight \nfor keeping atoms close\nto their position in xyz_ref',
                    },
                    'type':'float',
                    'min':0.0,'max':10.,
                    'value':0.0,
                    'precision':2,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'oneTurn':.5,},
             'gridcfg':{'columnspan':2,'sticky':'w','row':-1,'column':1}})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Ok',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we'},
            'command':self.Accept_cb})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Unconstrain all',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we','row':-1, 'column':1},
            'command':self.Unconstrain_cb})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Cancel',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we', 'column':2,'row':-1},
            'command':CallBackFunction(self.Close_cb, ifd)})
        self.form = self.vf.getUserInput(ifd, modal=0, blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW', CallBackFunction(self.Close_cb,ifd))
        #keep a handle to string selector
        self.ss = self.ifd.entryByName['constrAts']['widget']
        self.ss.bind('<ButtonPress>', self.updateForm2, add='+')
        self.ss.sets = self.vf.sets


    def update(self, event=None):
        key = self.ifd.entryByName['amberIds']['widget'].get()
        amb_ins = Amber94Config[key]
        self.CurrentAmber94 = amb_ins


    def Unconstrain_cb(self, event=None):
        amb_ins = self.CurrentAmber94
        ats = amb_ins.atoms
        atInd = map(lambda x:x==2, ats)
        anchors = Numeric.array(ats.coords).ravel()
        apply(amb_ins.constrainAtoms, (atInd, anchors,), {})
        numConstr = Numeric.add.reduce(amb_ins.constrained)
        self.updateLabels(numConstr)


    def updateLabels(self, numConstr):
        #print 'in updateLabels'
        if numConstr==None:
            print 'skipping update to None'
            raise 'abc'
            return
        cstr = 'Currently ' + str(numConstr) + ' constrained Atoms'
        for c in [self.vf.minimize_Amber94, self.vf.md_Amber94, self]:
            if hasattr(c, 'constrLab'):
                c.constrLab.set(cstr)
        #self.constrLab.set(cstr)


    def Accept_cb(self, event=None):
        #FIX THIS!!
        self.form.withdraw()
        #get the setupAmber94instance
        key = self.ifd.entryByName['amberIds']['widget'].get()
        amb_ins = Amber94Config[key][0]

        kw = {}
        #update wcons
        wcons = round(self.ifd.entryByName['wcons_tw']['widget'].get(),4)
        if wcons:
            kw['wcons'] = wcons
            #apply(amb_ins.setMinimizeOptions,(), mmOptD)

        constrAts = self.ifd.entryByName['constrAts']['widget'].get()
        constrAts = constrAts.findType(Atom)
        if hasattr(self, 'geomDict'):
            anchorPts = []
            for a in constrAts:
                anchorPts.append(self.geomDict[id(a)])
        else:
            anchorPts = constrAts.coords[:]
        #numConst = self.doitWrapper(key, constrAts, anchorPts)
        numConstr = apply(self.doitWrapper,(key, constrAts, anchorPts,), kw)
        #print 'updating labels with ', numConstr
        if numConstr!=None:
            self.updateLabels(numConstr)



    ##########################################################################
    ###ANCHOR COMMANDS:                                                 
    ###
    ###setAnchors                                                       
    ###
    ###initializes spheres + lines at ats.coords                
    ###
    ###initializes geomDict: keys=id(at), values=anchor xyz     
    ###
    ###initializes Form2                                        
    ##########################################################################
    def setAnchors(self, event=None):
        #print 'in setAnchors'
        if self.adjAnchors.get(): 
            self.ifd.entryByName['anchorCB']['widget'].toggle()
        self.ss.sets = self.vf.sets
        ats = self.atSET = self.ss.get().findType(Atom)
        ok = 0
        self.spheres.Set(visible=1, tagModified=False)
        if hasattr(self, 'form2') and hasattr(self, 'geomDict'):
            #check that every at is in current geomDict
            ok = 1
            for a in ats:
                if not self.geomDict.has_key(id(a)):
                    ok = 0
                    break
            for g in [self.spheres, self.lines]:
                g.Set(visible=1, tagModified=False)
                g.RedoDisplayList()
        if not ok:
            #have to rebuild here
            self.spheres.Set(vertices=ats.coords, visible=1, tagModified=False)
            numAts = 2*len(ats)
            fcs = []
            for i in range(0, numAts):
                if i%2==1:
                    fcs.append((i-1, i))
            #print 'fcs=', fcs
            linePts = []
            for a in ats:
                linePts.append(a.coords[:])
                linePts.append(a.coords[:])
            self.lines.Set(vertices=linePts, faces=fcs, visible=1,
                           tagModified=False)
            #self.lines.Set(vertices=ats.coords, faces=fcs, tagModified=False)
            self.geomDict = {}
            for a in ats:
                self.geomDict[id(a)] = a.coords[:]
        self.updateForm2()
        self.vf.GUI.VIEWER.Redraw()
        #else:
            #self.spheres.Set(vertices=[], tagModified=False)


    ##########################################################################
    ###ANCHOR: FORM2 COMMANDS:                                          
    ###                                                                        
    ###updateForm2                                                      
    ###
    ###checks that some anchors have been specified             
    ###
    ###IF NOT: return                                      
    ###
    ###calls buildForm2 if form2 hasn't been created            
    ###
    ###deiconifies form2 if it has been created                 
    ###
    ###updates entries in form2:                                
    ###
    ###in case specified anchors have changed           
    ##########################################################################
    def updateForm2(self, event=None):
        #if the string selector Show button is not on, do nothing
        if not self.ss.showCurrent.get():
            self.warningMsg("'Show' anchors before setting them")
            return
        if not hasattr(self, 'form2'):
            self.buildForm2()
        else:
            try:
                self.cur_at = self.ss.get().findType(Atom)[0]
            except:
                pass
            self.form2.deiconify()
        ##fix up entries in form2 + deiconify it
        self.updateForm2Entries()
    ######################################################################
    ###buildForm2                                                       
    ###
    ###builds framework of form2 : x,y,z thumbwheels and close button                  
    ###
    ###initializes :                                          
    ###
    ###currentAt - Tk variable for current rb choice        
    ###
    ###cur_at - Atom instance corresponding to currentAt    
    ###
    ###x,y,z_tw - coords of ats[ 0 ]                          
    #######################################################################
    def buildForm2(self):
        tstr = 'Adjust Anchor Positions'
        self.currentAt = Tkinter.IntVar()
        self.curAtLab = Tkinter.StringVar()
        self.cur_at = self.ss.get().findType(Atom)[0]
        lstr= 'current atom: '+ self.cur_at.full_name()
        self.curAtLab.set(lstr)
        coords = self.cur_at.coords[:]
        ifd2 = self.ifd2 = InputFormDescr(title = tstr)
        ifd2.append({'name':'curAtlab',
            'widgetType': Tkinter.Label,
            'textvariable':self.curAtLab,
            'wcfg':{'font':(ensureFontCase('helvetica'),12,'bold') },
            'gridcfg':{'sticky':'w','columnspan':2}})
        ifd2.append({'name':'x_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 'text':'x', },
                    'type':'float', 'value':coords[0],
                    'precision':3, 'width':100,
                    'continuous':1, 'wheelPad':2,
                    'callback':self.updateGeoms,
                    'height':20, 'oneTurn':4.,},
             'gridcfg':{'sticky':'w'}})
        ifd2.append({'name':'y_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 'text':'y', },
                    'type':'float', 'value':coords[1],
                    'precision':3, 'width':100,
                    'continuous':1, 'wheelPad':2,
                    'callback':self.updateGeoms,
                    'height':20, 'oneTurn':4.,},
             'gridcfg':{'sticky':'w', 'row':-1, 'column':1}})
        ifd2.append({'name':'z_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 'text':'z', },
                    'type':'float', 'value': coords[2],
                    'precision':3, 'width':100,
                    'continuous':1, 'wheelPad':2,
                    'callback':self.updateGeoms,
                    'height':20, 'oneTurn':4.,},
             'gridcfg':{'sticky':'w', 'row':-1, 'column':2}})
        ifd2.append({
            'name':'resetbut',
            'widgetType': Tkinter.Button,
            'text':'Reset All',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we','columnspan':2},
            'command':self.Reset_cb})
        ifd2.append({
            'name':'cancelbut',
            'widgetType': Tkinter.Button,
            'text':'Close',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we', 'row':-1, 'column':2},
            #'gridcfg':{'sticky':'we', 'column':2,'row':-1},
            'command':self.Accept_cb2})
            #'command':CallBackFunction(self.Close_cb, ifd2)})
        self.form2 = self.vf.getUserInput(ifd2, modal=0, width=400,
                            height=400, blocking=0, scrolledFrame=1)
        self.form2.root.protocol('WM_DELETE_WINDOW', CallBackFunction(self.Close_cb,ifd2))
        for tw in ['x_tw','y_tw','z_tw']:
            setattr(self, tw, self.ifd2.entryByName[tw]['widget'])


    ##########################################################################
    ###updateForm2Entries                                               
    ###
    ###ungrids framework of form2                              
    ###
    ###removes all previous rb                              
    ###
    ###builds new rb                                        
    ###
    ###regrids framework of form2                               
    ##########################################################################
    def updateForm2Entries(self, event=None):
        #first forget the bottom buttons:
        bButtons = ['resetbut','cancelbut']
        #bButtons = ['okbut','cancelbut']
        for b in bButtons:
            self.ifd2.entryByName[b]['widget'].grid_forget()
        #next remove former rb_* buttons:
        for k,v in self.ifd2.entryByName.items():
            if k[:3]=='rb_':
                v['widget'].grid_forget()
                del self.ifd2.entryByName[k]
        #build new radiobuttons
        rowctr = 1
        ats = self.ss.get().findType(Atom)
        nameLabs = []
        atCtr = 0
        for at in ats:
            entry = {'name':'rb_%s'%id(at),
                'widgetType':Tkinter.Radiobutton,
                'text':at.full_name(),
                'variable': self.currentAt,
                'value':atCtr,
                'gridcfg':{'sticky':'w','columnspan':3},
                'command':CallBackFunction(self.setCurrentAt, at)}
            self.ifd2.entryByName[entry['name']] = entry
            self.form2.addEntry(entry)
            rowctr = rowctr+1
            atCtr = atCtr + 1
        #repack the bottom buttons:
        for b in bButtons:
            item = self.ifd2.entryByName[b]
            gridcfg = item['gridcfg']
            gridcfg['row'] = gridcfg['row'] + rowctr + 2
            item['widget'].grid(gridcfg)


    ##########################################################################
    ###setCurrentAt :                                                    
    ###
    ###callback for rb in form2                                 
    ###
    ###sets cur_at                                          
    ###
    ###sets x,y,z_tw to cur_at coords                       
    ###
    ###calls updateGeoms                                        
    ##########################################################################
    def setCurrentAt(self, at, event=None):
        self.cur_at = at
        lstr= 'current atom: '+ self.cur_at.full_name()
        self.curAtLab.set(lstr)
        #get last specified anchor point for this atom
        coords = self.geomDict[id(at)]
        #coords = at.coords[:]
        self.x_tw.set(coords[0])
        self.y_tw.set(coords[1])
        self.z_tw.set(coords[2])
        self.updateGeoms()


    ##########################################################################
    ###updateGeoms                                                      
    ###called by:                                               
    ###
    ###setCurrentAt                                         
    ###
    ###resets spheres and lines to current vertices             
    ###
    ###calls Redraw                                             
    ##########################################################################
    def updateGeoms(self, event=None):
        key = id(self.cur_at)
        ind = self.currentAt.get()
        #ind = self.atSET.index(self.cur_at)
        currentPos = self.geomDict[key]
        newPos = ( self.x_tw.get(), self.y_tw.get(), self.z_tw.get()) 
        self.geomDict[key] = newPos
        self.spheres.vertexSet.vertices.array[ind] = newPos
        self.spheres.RedoDisplayList()
        #the moving pt is the odd one of face pair: (0,1), (2,3) etc
        lineInd = 2*ind + 1
        #print 'updating vertex ', lineInd
        self.lines.vertexSet.vertices.array[lineInd] = newPos
        self.lines.RedoDisplayList()
        #self.spheres.Set(vertices = (newPos,), tagModified=False)
        #self.lines.Set(vertices = (self.cur_at.coords, newPos,),
        #               faces=((0,1),), tagModified=False)
        self.vf.GUI.VIEWER.Redraw()


    ##########################################################################
    ###Reset_cb                                                         
    ###
    ###restores geomDict to original coords                     
    ###
    ###resets spheres and lines to original coords              
    ###
    ###calls Redraw                                             
    ##########################################################################
    def Reset_cb(self, event=None):
        ats = self.atSET = self.ss.get().findType(Atom)
        self.geomDict = {}
        for a in ats:
            self.geomDict[id(a)] = a.coords[:]
        self.spheres.Set(vertices=ats.coords, visible=1, tagModified=False)
        linePts = []
        for a in ats:
            linePts.append(a.coords[:])
            linePts.append(a.coords[:])
        self.lines.Set(vertices=linePts,visible=1, tagModified=False)
        self.vf.GUI.VIEWER.Redraw()


    def Accept_cb2(self, event=None):
        for g in [self.spheres, self.lines]:
            g.Set(visible=0, tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        self.form2.withdraw()



    def guiCallback(self):
        if not len(Amber94Config.keys()):
            self.warningMsg('no Amber94 objects present: SetupAmber94 first')
            return 'ERROR'
        #amb_ins = Amber94Config.values()[0][0]
        #key = amb_ins.key
        #mols = amb_ins.atoms.top.uniq()
        if self.CurrentAmber94=={}:
            self.CurrentAmber94 = Amber94Config.values()[0][0]
        key = self.CurrentAmber94.key
        mols = self.CurrentAmber94.atoms.top.uniq()
        tstr = "Set atoms to be constrained for  " + key + ":"
        if not hasattr(self, 'ifd'):
            self.buildForm(tstr, mols)
        else:
            lb =  self.ifd.entryByName['amberIds']['widget']._list
            #make sure to update the listbox:
            lb.delete(0, 'end')
            for k in Amber94Config.keys():
                lb.insert('end', k)
            self.ifd.entryByName['constrAts']['widget'].molSet = mols
            self.ifd.title = tstr
            self.ifd.form.root.title(tstr)
            self.form.deiconify()


ConstrainAtomsAmber94CommandGUI = CommandGUI()
ConstrainAtomsAmber94CommandGUI.addMenuCommand('menuRoot', 'Amber', 'Constrain Atoms',
                                             cascadeName = 'Set Options')



class SetMDOptsAmber94(MVCommand):
    """This class allows you to set md options of a Amber94 instance these options include t, dt, tautp, temp0, verbose, vlimit, ntpr_md, zerov,tempi and idum. NB: this is written as a separate class in order to create a straight-forward log.
    \nPackage : Pmv
    \nModule  : amberCommands
    \nClass   : SetMDOptsAmber94
    \nCommand : setMDOptsAmber94
    \nSynopsis:\n
    None<-setmdOpts_Amber94(key, **kw)\n
    \nArguments:\n
    key --- identifier to be key for this Amber94 instance in Amber94Config dictionary\n
    """

    from Pmv.amberCommands import CurrentAmber94

    
    def __call__(self, key, **kw):
        """None<-setmdOpts_Amber94(key, **kw)
        \nkey --- identifier to be key for this Amber94 instance in Amber94Config dictionary\n
        """
        return apply(self.doitWrapper, (key,), kw)


    def doit(self, key, **kw):
        if key not in Amber94Config.keys():
            print 'key: ', key, " is not in current Amber94Config "
            return 'ERROR'
        amber94instance = Amber94Config[key][0] 
        amb_ins = self.CurrentAmber94 = amber94instance
        for k in kw.keys():
            assert k in ['t','dt','tautp','temp0','verbosemd','ntwx',
                         'vlimit', 'ntpr_md', 
                         'zerov', 'tempi', 'idum']
        apply(amb_ins.setMdOptions, (), kw)


    def Close_cb(self, ifd, event=None):
        form = ifd.form
        form.withdraw()


    def buildForm(self):
        ifd = self.ifd = InputFormDescr(title = "Set parameters for amber94 molecular dynamics:")
        self.verbose = Tkinter.StringVar()
        self.verbose.set('print summary')
        self.verbose_list = ['no print out', 'print summary', 'print summary w/energies']
        self.zerov = Tkinter.IntVar()
        self.id = Tkinter.StringVar()
        self.id.set(self.CurrentAmber94.key)

        ifd.append({'widgetType':Pmw.ComboBox,
            'name':'amberIds',
            'wcfg':{'label_text':'Amber94 ids',
                    'entryfield_value':self.id.get(),
                    'labelpos':'w',
                    'listheight':'80',
                    'scrolledlist_items': Amber94Config.keys(),
                    'selectioncommand': self.update,
                    },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'widgetType':Pmw.ComboBox,
            'name':'verbose_cb',
            'wcfg':{'label_text':'',
                    'entryfield_value':self.verbose.get(),
                    'labelpos':'w',
                    'listheight':'80',
                    'scrolledlist_items': self.verbose_list,
                    },
            'gridcfg':{'sticky':'w'}})

        ifd.append({'name':'zerov_cb',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'zerov - use zero initial velocities',
                'variable': self.zerov,
                },
            'gridcfg':{'sticky':'w', 'row':-1, 'column':1 }})
        ifd.append({'name':'t_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                     'text': 't - initial time',
                    },
                    'type':'float',
                    'min':0.0,'max':30.0,
                    'lockmin':1,
                    'precision':2,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'value':0.0,
                    'oneTurn':10.,},
             'gridcfg':{'columnspan':2,'sticky':'e'}})
        ifd.append({'name':'dt_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                     'text': 'dt - time step, ps',
                    },
                    'type':'float',
                    'min':0.00001,'max':1.0,
                    'precision':6,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'value':0.001,
                    'oneTurn':.1,},
             'gridcfg':{'columnspan':2,'sticky':'e'}})
        ifd.append({'name':'tautp_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                     'text': 'tautp - temp. coupling parm., ps',
                    },
                    'type':'float',
                    'min':0.001,'max':5.0,
                    'precision':6,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'value':0.2,
                    'oneTurn':.1,},
             'gridcfg':{'columnspan':2,'sticky':'e'}})
        ifd.append({'name':'temp0_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                     'text': 'temp0 - target temperature, K',
                    },
                    'type':'float',
                    'min':0.0,'max':1000.0,
                    'precision':3,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'value':300.,
                    'oneTurn':100.,},
             'gridcfg':{'columnspan':2,'sticky':'e'}})
        ifd.append({'name':'vlimit_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                     'text': 'vlimit - maximum velocity component',
                    },
                    'type':'float',
                    'min':0.0,'max':100.0,
                    'precision':3,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'value':10.,
                    'oneTurn':10.,},
             'gridcfg':{'columnspan':2,'sticky':'e'}})
        ifd.append({'name':'ntpr_md_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                     'text': 'ntpr_md - print frequency',
                    },
                    'type':'int',
                    'min':0,'max':5000,
                    #'precision':3,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'value':10,
                    'oneTurn':500.,},
             'gridcfg':{'columnspan':2,'sticky':'e'}})
        ifd.append({'name':'ntwx_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                     'text': 'ntwx - trajectory snapshot frequency',
                    },
                    'type':'int',
                    'min':0,'max':5000,
                    'lockmin':1,
                    #'precision':3,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'value':0,
                    'oneTurn':500.,},
             'gridcfg':{'columnspan':2,'sticky':'e'}})
        ifd.append({'name':'tempi_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                     'text': 'tempi- initial temperature',
                    },
                    'type':'float',
                    'min':0.,'max':1000.,
                    'precision':3,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'value':0,
                    'oneTurn':500.,},
             'gridcfg':{'columnspan':2,'sticky':'e'}})
        ifd.append({'name':'idum_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                     'text': 'idum - random number seed',
                    },
                    'type':'int',
                    'min':-1,'max':1,
                    #'precision':3,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'value':-1,
                    'oneTurn':1,},
             'gridcfg':{'columnspan':2,'sticky':'e'}})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Accept',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we'},
            'command':self.Accept_cb})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Cancel',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we', 'column':1,'row':-1},
            'command':CallBackFunction(self.Close_cb, ifd)})
        self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW', CallBackFunction(self.Close_cb,ifd))


    def Accept_cb(self, event=None):
        #FIX THIS!!
        self.form.withdraw()
        #get the setupAmber94instance
        key = self.ifd.entryByName['amberIds']['widget'].get()
        #amb_ins = Amber94Config[key][0]
        #update minimization Options
        #SKIPPED: boltz2
        mdOptD = {}
        for v in ['t_tw','dt_tw', 'tautp_tw','temp0_tw','vlimit_tw',
                    'ntwx_tw', 'tempi_tw','idum_tw']:
            val = self.ifd.entryByName[v]['widget'].get()
            s = split(v,'_')[0]
            mdOptD[s] = val
        mdOptD['ntpr_md'] = self.ifd.entryByName['ntpr_md_tw']['widget'].get()
        w = self.ifd.entryByName['verbose_cb']['widget'].get()
        if w not in self.verbose_list:
            mdOptD['verbosemd'] = 1
        else:
            mdOptD['verbosemd'] = self.verbose_list.index(w)
        mdOptD['zerov'] = self.zerov.get()
        #apply(amb_ins.setMdOptions, (), mdOptD)
        apply(self.doitWrapper, (key,), mdOptD)


    def update(self, event=None):
        key = self.ifd.entryByName['amberIds']['widget'].get()
        amb_ins = Amber94Config[key]
        self.CurrentAmber94 = amb_ins
        #THIS SHOULD ADJUST THE DISPLAYED PARAMETERS....
        #for w in []:
            #FIX THIS!!!
            #newval = amber.prmlib.cvar.+ key



    def guiCallback(self):
        if not len(Amber94Config.keys()):
            self.warningMsg('no Amber94 objects present: SetupAmber94 first')
            return 'ERROR'

        if self.CurrentAmber94=={}:
            self.CurrentAmber94 = Amber94Config.values()[0][0]

        #ALLOW USER TO SET parameters here
        if not hasattr(self, 'ifd'):
            self.buildForm()
        else:
            lb =  self.ifd.entryByName['amberIds']['widget']._list
            #make sure to update the listbox:
            lb.delete(0, 'end')
            for k in Amber94Config.keys():
                lb.insert('end', k)
            self.form.deiconify()


SetMDOptsAmber94CommandGUI = CommandGUI()
SetMDOptsAmber94CommandGUI.addMenuCommand('menuRoot', 'Amber', 'Molecular Dynamics',
                                             cascadeName = 'Set Options')



class MolecularDynamicsAmber94(MVCommand):
    """
    This class allows you to select an Amber94 instance from Amber94Config whose keys are ids specified in setup_Amber94 for the Amber94 instances.You can also set md options, freeze atoms, specify constrained atoms and anchor atoms and set maxStep. The md 
can be run repeatedly.
    \nPackage : Pmv
    \nModule  : amberCommands
    \nClass   : MolecularDynamicsAmber94
    \nCommand : molecularDynamicsAmber94
    \nSynopsis:\n
    return_code<-md_Amber94(key, maxStep, **kw)\n
    \nArguments\n:
    key --- is key into Amber94Config dictionary\n
    """


    from Pmv.amberCommands import CurrentAmber94


    def __call__(self, key, maxStep, **kw):
        """return_code<-md_Amber94(key, maxStep, **kw)\n
\npossible return codes:\n
        >0    converged, final iteration number\n
        -1    bad line search, probably an error in the relation
                of the funtion to its gradient (perhaps from
                round-off if you push too hard on the minimization).\n
        -2    search direction was uphill\n
        -3    exceeded the maximum number of iterations\n
        -4    could not further reduce function value\n
        -5    stopped via signal   (bsd)\n
key is key into Amber94Config dictionary\n
        """
        #FIX THESE!

        return apply(self.doitWrapper, (key, maxStep,), kw)


    def doit(self, key, maxStep, **kw):
        if key not in Amber94Config.keys():
            print 'key: ', key, " is not in current Amber94Config "
            return 'ERROR'
        amb_ins = Amber94Config[key][0] 
        self.CurrentAmber94 = amb_ins
        ##do you need to retrieve a set of minimization parms, too?
        #if self.callback.get():
        #    mols = amb_ins.atoms.top.uniq()
        #    print 'calling updateCoords)'
        #    cbNum=0
        #    nbat=len(amb_ins.atoms)
        #    coords = amb_ins.atoms.coords
        #    energies = []
        #    step = 49
        #    self.updateCoords(cbNum, nbat, coords, energies, step)
        #    self.vf.displayLines(mols, negate=1, topCommand=0)
        #    self.vf.displayLines(mols, negate=0, topCommand=0)
        freq = kw.get('callback_freq', 0)
        del kw['callback_freq']
        callback = kw.get('callback')
        del kw['callback']
        wcons = kw.get('wcons')
        if wcons:
            del kw['wcons']
            #check here if anything has been constrained
            numConst = Numeric.add.reduce(amb_ins.constrained)
            if numConst:
                mdopt={}
                mdopt['wcons'] = wcons
                apply(amb_ins.setMinimizeOptions, (), mdopt)

        if callback:
            #add the coords here
            if not hasattr(amb_ins, 'coord_index'):
                amb_ins.atoms.addConformation(amb_ins.atoms.coords[:])
                amb_ins.coord_index = len(amb_ins.atoms[0]._coords)-1
            #freq = int(self.callbackFreq.get())
            #print 'setting callback to updateCoords'
            amb_ins.setCallback(self.updateCoords, freq)

        return_code = apply(amb_ins.md,(maxStep,), kw)
        print 'return_code=', return_code
        return  return_code


    def updateCoords(self,  cbNum=0, nbat=300, coords=[], energies=[], step=[]):
        #FIX THIS
        #print 'in updateCoords'
        amb = self.CurrentAmber94
        mols = amb.atoms.top.uniq()
        allAtoms = mols.chains.residues.atoms
        newcoords = Numeric.array(amb.coords[:])
        newcoords.shape = (-1,3)
        allAtoms.updateCoords(newcoords.tolist(), amb.coord_index)
        self.vf.displayLines(allAtoms, topCommand=0)
        if self.vf.hasGui:
            self.vf.GUI.VIEWER.currentCamera.update()


    def Close_cb(self, ifd, event=None):
        form = ifd.form
        form.withdraw()


    def buildForm(self):
        ifd = self.ifd = InputFormDescr(title = "Set parameters for amber94 md:")
        self.verbose = Tkinter.IntVar()
        self.verbose.set('print summary')
        self.dield = Tkinter.IntVar()
        self.dield.set(1)
        self.callback = Tkinter.IntVar()
        self.callbackFreq = Tkinter.StringVar()
        self.callbackFreq.set('10')
        self.TrjFilename = Tkinter.StringVar()
        self.TrjFilename.set('')
        self.id = Tkinter.StringVar()
        #self.id.set(Amber94Config.keys()[0])
        self.id.set(self.CurrentAmber94.key)
        frozNum = Numeric.add.reduce(self.CurrentAmber94.frozen)
        self.frozenLab = Tkinter.StringVar()
        fstr = 'Currently ' + str(frozNum) + ' frozen atoms'
        self.constrLab = Tkinter.StringVar()
        constrNum = Numeric.add.reduce(self.CurrentAmber94.constrained)
        cstr = 'Currently ' + str(constrNum) + ' constrained atoms'
        self.constrLab.set(cstr)
        ifd.append({'widgetType':Pmw.ComboBox,
            'name':'amberIds',
            'wcfg':{'label_text':'Amber94 ids',
                    'entryfield_value':self.id.get(),
                    'labelpos':'w',
                    'listheight':'80',
                    'scrolledlist_items': Amber94Config.keys(),
                    'selectioncommand': self.update,
                    },
            'gridcfg':{'sticky':'w'}})
            #'gridcfg':{'sticky':'nesw','row':-1, 'column':1}}),
        ifd.append({'name':'setmdopts_cb',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'set molecular dynamics options',
                'command': self.setMdOpts,
                },
            'gridcfg':{'sticky':'w', 'row':-1,'column':1}})
        ifd.append({'name':'frozen_lab',
            'widgetType': Tkinter.Label,
            'textvariable':self.frozenLab,
            'wcfg':{'font':(ensureFontCase('helvetica'),12,'bold') },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'const_lab',
            'widgetType': Tkinter.Label,
            'textvariable':self.constrLab,
            'wcfg':{'font':(ensureFontCase('helvetica'),12,'bold') },
            'gridcfg':{'sticky':'w','row':-1,'column':1}})
        ifd.append({'name':'setfroz_cb',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'set frozen atoms',
                'command': self.setFrozenAtoms,
                },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'setcons_cb',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'set constrained atoms',
                'command': self.setConstrainedAtoms,
                },
            'gridcfg':{'sticky':'w', 'row':-1,'column':1}})
        #widgets for the run parameters:
        ifd.append({'name':'maxStep_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                     'text': 'maxStep -maximum number of steps:',
                    },
                    'type':'int',
                    #'min':100,
                    'max':20000,
                    #'precision':2,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'value':100.0,
                    'oneTurn':1000,},
             'gridcfg':{'columnspan':2,'sticky':'e'}})
        #Should THIS go here?
        ifd.append({'name':'wcons_tw',
            'widgetType':ThumbWheel,
            'wType':ThumbWheel,
            'wcfg':{ 'labCfg':{ 
                     'text':'wcons -restraint weight \nfor keeping atoms close\nto their position in xyz_ref',
                    },
                    'type':'float',
                    'min':0.0,'max':10.,
                    'value':0.0,
                    'precision':2,
                    'width':100,
                    'continuous':1,
                    'wheelPad':2,
                    'height':20,
                    'oneTurn':.5,},
             'gridcfg':{'columnspan':2,'sticky':'e'}})
             #'gridcfg':{'columnspan':2,'sticky':'w','row':-1,'column':1}})
        ifd.append({'name':'trjCB',
            'widgetType': Tkinter.Checkbutton,
            'wcfg':{'text':'Specify trajectory filename',
                'variable': self.TrjFilename,
                'command': self.set_filename,
                },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'callback_cb',
            'widgetType':Tkinter.Checkbutton,
            'wcfg':{'text':'update geometries',
                'variable': self.callback,
                'command': self.disableCallbackFreq,
                },
            'gridcfg':{'sticky':'w'}})
        ifd.append({'name': 'callback_ent',
            'widgetType':Tkinter.Entry,
            'wcfg':{ 
                    'label': 'update frequency',
                    #'label': 'callback frequency',
                    'textvariable': self.callbackFreq, 
                    'width':7,
                    'fg':'grey',
                    'state':'disabled',
                    'selectbackground':'#d9d9d9', 
                    'selectforeground':'grey', 
                    },
            'gridcfg':{'sticky':'we', 'row':-1, 'column':1}})
        
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Run MD',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we'},
            'command':self.Accept_cb})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Cancel',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we', 'column':1,'row':-1},
            'command':CallBackFunction(self.Close_cb, ifd)})
        self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW', CallBackFunction(self.Close_cb,ifd))


    def disableCallbackFreq(self, event=None):
        w = self.ifd.entryByName['callback_ent']['widget']
        if self.callback.get():
            w.config(state='normal', fg='black', selectbackground='#c3c3c3', 
                                selectforeground='black')
        else:
            w.config(state='disabled', fg='grey', selectbackground='#d9d9d9', 
                                selectforeground='grey')


    def set_filename(self, event=None):
        self.ifd.entryByName['trjCB']['widget'].toggle()
        #if getattr(prmlib.cvar, 'ntwx')==0:
        if prmlib.SFFoptions_ntwx_get(self.CurrentAmber94.sff_opts) == 0:
            self.warningMsg("must set ntwx first!")
            return
        file = self.vf.askFileSave(types=[('trj files:', '*.trj'),('allfiles:','*.*')],
                           title='amber94 md trajectory file:')
        if file:
            self.TrjFilename.set(file) #this has the whole pathname etc
        else:
            self.TrjFilename.set('')


    def Accept_cb(self, event=None):
        self.form.withdraw()
        #FIX THIS!!
        key = self.ifd.entryByName['amberIds']['widget'].get()
        amb_ins = Amber94Config[key][0]
        if self.callback.get():
            #add the coords here
            amb_ins = Amber94Config[key][0]
            if not hasattr(amb_ins, 'coord_index'):
                amb_ins.atoms.addConformation(amb_ins.atoms.coords[:])
                amb_ins.coord_index = len(amb_ins.atoms[0]._coords)-1
            #newConfNum = len(allAtoms[0]._coords)-1
            #allAtoms.setConformation(newConfNum) 
            freq = int(self.callbackFreq.get())
            #print 'setting callback to updateCoords'
            amb_ins.setCallback(self.updateCoords, freq)
        else:
            amb_ins.coord_index = 1
        #start md
        d = {}
        d['callback'] = self.callback.get()
        d['callback_freq'] = int(self.callbackFreq.get())
        #put wcons into dictionary
        wcons = round(self.ifd.entryByName['wcons_tw']['widget'].get(),4)
        if wcons:
            d['wcons'] = wcons
        maxStep = self.ifd.entryByName['maxStep_tw']['widget'].get()
        if hasattr(self, 'TrjFilename'):
            filename = self.TrjFilename.get()
            if len(filename):
                d['filename'] = filename
        return apply(self.doitWrapper, (key, maxStep,),  d)


    def setMdOpts(self, event=None):
        #turn off button
        self.ifd.entryByName['setmdopts_cb']['widget'].toggle()
        self.vf.setmdOpts_Amber94.guiCallback()
        

    def setFrozenAtoms(self, event=None):
        #turn off button
        self.ifd.entryByName['setfroz_cb']['widget'].toggle()
        #print 'calling freezeAtoms'
        numFrozen = self.vf.freezeAtoms_Amber94.guiCallback()
        fstr = 'Currently ' + str(numFrozen) + ' frozen atoms'
        self.frozenLab.set(fstr)


    def setConstrainedAtoms(self, event=None):
        #turn off button
        self.ifd.entryByName['setcons_cb']['widget'].toggle()
        #print 'calling constrainAtoms'
        numConstr = self.vf.constrainAtoms_Amber94.guiCallback()
        cstr = 'Currently ' + str(numConstr) + ' constrained atoms'
        self.constrLab.set(cstr)


    def update(self, event=None):
        key = self.ifd.entryByName['amberIds']['widget'].get()
        amb_ins = Amber94Config[key]
        self.CurrentAmber94 = amb_ins
        #THIS SHOULD ADJUST THE DISPLAYED PARAMETERS....
        #for w in []:
            #FIX THIS!!!
            #newval = amber.prmlib.cvar.+ key


    def guiCallback(self):
        if not len(Amber94Config.keys()):
            self.warningMsg('no Amber94 objects present: SetupAmber94 first')
            return 'ERROR'

        if self.CurrentAmber94=={}:
            self.CurrentAmber94 = Amber94Config.values()[0][0]

        #ALLOW USER TO SET parameters here
        if not hasattr(self, 'ifd'):
            self.buildForm()
        else:
            lb =  self.ifd.entryByName['amberIds']['widget']._list
            #make sure to update the listbox:
            lb.delete(0, 'end')
            for k in Amber94Config.keys():
                lb.insert('end', k)
            self.form.deiconify()


MolecularDynamicsAmber94CommandGUI = CommandGUI()
MolecularDynamicsAmber94CommandGUI.addMenuCommand('menuRoot', 'Amber', 'MD')



class PlayMolecularDynamicsTrjAmber94(MVCommand):
    """
    This class allows you to select an Amber94 instance from Amber94Config
whose keys are ids specified in setup_Amber94 for the Amber94 instances, and
a molecular dynamics trajectory file and play the trajectory.
    \nPackage : Pmv
    \nModule  : amberCommands
    \nClass   : PlayMolecularDynamicsTrjAmber94
    \nCommand : playMolecularDynamicsTrjAmber94
    \nSynopsis:\n
    return_code<-play_md_trj_Amber94(key, filename, **kw)
    \nArguments:\n
    key --- key into Amber94Config dictionary\n
    filename --- is name of file containing md trajectory binary data\n
    """


    from Pmv.amberCommands import CurrentAmber94


    def __call__(self, key, filename, **kw):
        """
        return_code<--play_md_trj_Amber94(key, filename, **kw)
        \nkey --- is key into Amber94Config dictionary
        \nfilename --- is name of file containing md trajectory binary data
        """
        return apply(self.doitWrapper, (key, filename,), kw)


    def doit(self, key, filename, **kw):
        if key not in Amber94Config.keys():
            print 'key: ', key, " is not in current Amber94Config "
            return 'ERROR'
        if not exists(filename):
            print filename, " does not exist"
            return 'ERROR' 
        amb_ins = Amber94Config[key][0] 
        self.CurrentAmber94 = amb_ins
        amb_ins.bt = BinTrajectory(filename)
        self.stop = 0 
        self.Play_cb()


    def Play_cb(self, event=None):
        cam = self.vf.GUI.VIEWER.cameras[0]
        self.stop = 0
        #this command plays md trajectory in self.filename
        amb_ins = self.CurrentAmber94
        allAtoms = amb_ins.atoms
        while not self.stop:
            if self.stop: break
            newCoords = amb_ins.bt.getNextConFormation()
            if newCoords is None: break
            if not hasattr(amb_ins, 'coord_index'):
                allAtoms.addConformation(allAtoms.coords[:])
                amb_ins.coord_index = len(allAtoms[0]._coords)-1
            allAtoms.updateCoords(newCoords.tolist(), amb_ins.coord_index)
            #print 'allAtoms[0].coords=', allAtoms[0].coords
            self.vf.displayLines(allAtoms, topCommand=0)
            cam.update()
            

    def Stop_cb(self, event=None):
        self.stop = 1


    def Close_cb(self, ifd, event=None):
        form = ifd.form
        form.withdraw()


    def update(self, event=None):
        key = self.ifd.entryByName['amberIds']['widget'].get()
        amb_ins = Amber94Config[key]
        self.CurrentAmber94 = amb_ins
        #THIS SHOULD ADJUST THE DISPLAYED PARAMETERS....
        #for w in []:
            #FIX THIS!!!
            #newval = amber.prmlib.cvar.+ key


    def buildForm(self):
        ifd = self.ifd = InputFormDescr(title = "Play amber94 md trajectory file:")
        self.filename = Tkinter.StringVar()
        self.filename.set('')
        self.id = Tkinter.StringVar()
        #self.id.set(Amber94Config.keys()[0])
        self.id.set(self.CurrentAmber94.key)
        ifd.append({'widgetType':Pmw.ComboBox,
            'name':'amberIds',
            'wcfg':{'label_text':'Amber94 ids',
                    'entryfield_value':self.id.get(),
                    'labelpos':'n',
                    'listheight':'80',
                    'scrolledlist_items': Amber94Config.keys(),
                    'selectioncommand': self.update,
                    },
            'gridcfg':{'sticky':'w','columnspan':2}})
        ifd.append({'name':'trjCB',
            'widgetType': Tkinter.Checkbutton,
            'wcfg':{'text':'Select filename',
                'variable': self.filename,
                'command': self.getFile,
                },
            'gridcfg':{'sticky':'w','columnspan':2}})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Play',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we'},
            'command':self.Accept_cb})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Stop',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we','row':-1,'column':1},
            'command':self.Stop_cb})
        ifd.append({'widgetType': Tkinter.Button,
            'text':'Close',
            'wcfg':{'bd':6},
            'gridcfg':{'sticky':'we', 'columnspan':2},
            'command':CallBackFunction(self.Close_cb, ifd)})
        self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW', CallBackFunction(self.Close_cb,ifd))


    def getFile(self, event=None):
        file = self.vf.askFileOpen(types=[('trj files:','*.trj')],
                           title='Select Trajectory File')
        if file:
            self.filename.set(file)


    def Accept_cb(self, event=None):
        #self.form.withdraw()
        #FIX THIS!!
        key = self.ifd.entryByName['amberIds']['widget'].get()
        d = {}
        filename = self.filename.get()
        if not len(filename):
            self.warningMsg('no trajectory file selected!')
            return 'ERROR'
        return apply(self.doitWrapper, (key, filename,),  d)



    def guiCallback(self):
        if not len(Amber94Config.keys()):
            self.warningMsg('no Amber94 objects present: SetupAmber94 first')
            return 'ERROR'

        if self.CurrentAmber94=={}:
            self.CurrentAmber94 = Amber94Config.values()[0][0]

        #ALLOW USER TO SET parameters here
        if not hasattr(self, 'ifd'):
            self.buildForm()
        else:
            lb =  self.ifd.entryByName['amberIds']['widget']._list
            #make sure to update the listbox:
            lb.delete(0, 'end')
            for k in Amber94Config.keys():
                lb.insert('end', k)
            self.form.deiconify()


PlayMolecularDynamicsTrjAmber94CommandGUI = CommandGUI()
PlayMolecularDynamicsTrjAmber94CommandGUI.addMenuCommand('menuRoot', 'Amber', 'Play Trajectory File')



class FixAmberHAtomNamesCommand(MVCommand):
    """This class checks hydrogen atom names and modifies them to conform to
    \nPackage : Pmv
    \nModule  : amberCommands
    \nClass   : FixAmberHAtomNamesCommand
    \nCommand : fixAmberHAtomNamesCommand
    \nSynopsis:\n
    None <- fixAmberHNames(nodes, **kw)\n
    \nArguments:\n
    nodes --- TreeNodeSet holding the current selection\n
    \nAmber conventions:\n
        Single hydrogen atoms bonded to N are named 'H'.\n 
        Single hydrogen atoms bonded to atoms with 2 or 3 character names are named 'H'+ bonded-atom's name[ 1: ].  
    \neg: 
        \nhydrogen bonded to atom 'CA' is named 'HA'
        \nhydrogen bonded to atom 'OG1' of THR is named 'HG1'.
        \nPairs of hydrogens bonded to atoms append '2' or '3' to names formed as above.
    \neg: 
        \nhydrogens bonded to n-terminus 'N' of PRO are named 'H2' and 'H3'.
        \nhydrogens bonded to atom 'CA' of GLY are named 'HA2' and 'HA3'.
        \nhydrogens bonded to atom 'CG1' of ILE are named 'HG12' and 'HG13'.
        \nTrios of hydrogens bonded to atoms append '1', '2' or '3' to 
    names formed as above.
    \neg: 
        \nhydrogens bonded to n-terminus 'N' of ALA are named 'H1', 'H2' and 'H3'.
        \nhydrogens bonded to atom 'CB' of ALA are named 'HB1','HB2' and 'HB3'.
        \nhydrogens bonded to atom 'CB' of ALA are named 'HB1','HB2' and 'HB3'.
        \nhydrogens bonded to atom 'CD1' of ILE are named 'HD11','HD12' and 'HD13'.
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def doit(self, nodes):
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'

        all = nodes.findType(Atom)
        allHs = all.get('H.*')
        if not allHs: return 'ERROR'
        # use _ct to only process each hydrogen once
        allHs._ct = 0

        #this leaves out hydrogens whose bonded atom isn't in nodes
        #hasHAtoms = AtomSet(filter(lambda x, all=all: x.findHydrogens(), all))
        #for a in hasHAtoms:
        for h in allHs:
            if h._ct: continue
            if not len(h.bonds): continue
            b = h.bonds[0]
            a = b.atom1
            if a==h: a = b.atom2

            if len(a.name)==1:
                astem = ''
            else:
                astem = a.name[1:]

            hlist = AtomSet(a.findHydrogens())
            #try to preserve order of H's if there is any
            hlist.sort()
            hlen = len(hlist)

            #SPECIAL TREATMENT for CYSTEINES:
            parType = h.parent.type
            sibNames = a.parent.atoms.name
            #NB CYS with no HG is CYM
            if parType=='CYS' or parType=='CYM':
                #check for nterminus + for cterminus + for disulfide bond:
                isTerminus = 'OXT' in sibNames or hlen==3
                # must have BOND S-S  and no HG atom for treatment as CYX 
                sAt = h.parent.atoms.get(lambda x: x.name=='SG')[0]
                hasDisulfide = len(sAt.bonds)==2 
                #problem1: in non-terminal CYM, H bonded to N is 'HN'
                if a.name=='N' and 'HG' not in sibNames \
                    and not isTerminus and not hasDisulfide:
                    #distinguish between cystine + neg charged cys:
                    #CYX v. CYM
                    astem = 'N'
                #problem2: in n- or c-terminal CYS, H bonded to SG is 'HSG'
                elif isTerminus and a.name=='SG':
                    astem = 'SG'

            if hlen == 1:
                hlist[0].name = 'H' + astem
            elif hlen == 2:
                #N-terminus PRO has H2+H3
                if len(a.name)>1 and a.name[0]=='N':
                    rl = [1,2]
                else:
                    rl = [2,3]
                for i in rl:
                    hat = hlist[i-2]
                    hat.name = 'H' +  astem + str(i)
                    hat._ct = 1
            elif hlen == 3:
                for i in range(3):
                    hat = hlist[i]
                    hat.name = 'H' + astem + str(i+1)
                    hat._ct = 1
        delattr(allHs, '_ct')
                

    def __call__(self, nodes, **kw):
        """None <- fixAmberHNames(nodes, **kw)
        \nnodes --- TreeNodeSet holding the current selection"""
        if type(nodes) is StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes):
            return 'ERROR'
        apply ( self.doitWrapper, (nodes,), kw )
   


class FixAmberHAtomNamesGUICommand(MVCommand):
    """
This class provides Graphical User Interface to FixAmberHAtomsNameCommand which is invoked by it with the current selection, if there is one.
    \nPackage : Pmv
    \nModule  : amberCommands
    \nClass   : FixAmberHAtomNamesGUICommand
    \nCommand : FixAmberHAtomNamesGUICommand
    \nSynopsis:\n
    None <--- fixAmberHNamesGC(nodes, **kw)\n
    nodes --- TreeNodeSet holding the current selection\n
    """
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly
    

    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'fixAmberHNames'):
            self.vf.loadCommand('amberCommands', 'fixAmberHNames','Pmv',
                                topCommand=0)
    

    def doit(self, nodes):
        self.vf.fixAmberHNames(nodes)


    def __call__(self, nodes, **kw):
        """None <- fixAmberHNamesGC(nodes, **kw)
           \nnodes: TreeNodeSet holding the current selection"""
        if type(nodes) is StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes):
            return 'ERROR'
        apply( self.doitWrapper, (nodes,), kw )


    def guiCallback(self):
        sel=self.vf.getSelection()
        if len(sel):
            self.doitWrapper(sel, topCommand=0)
        

fixAmberHAtomNamesGUICommandGuiDescr = {'widgetType':'Menu',
                                          'menuBarName':'menuRoot',
                                          'menuButtonName':'Amber',
                                          'menuCascadeName':'Hydrogens',
                                          'menuEntryLabel':'Fix Amber Hydrogen Names'}


FixAmberHAtomNamesGUICommandGUI = CommandGUI()
FixAmberHAtomNamesGUICommandGUI.addMenuCommand('menuRoot', 'Amber',
                    'Fix Amber Names', cascadeName='Hydrogens')



class FixAmberResNamesAndOrderAtomsCommand(MVCommand):
    """This class reorders atoms to conform to Amber conventions. 
    \nPackage : Pmv
    \nModule  : amberCommands
    \nClass   : FixAmberResNamesAndOrderAtomsCommand
    \nCommand : fixAmberResNamesAndOrderAtomsCommand
    \nSynopsis:\n 
    \n  None<-fixAmberResNamesAndOrderAtomsCommand(nodes)
    \nfor residues with no cycles:
    \nN,[H*],_A,[HA*],_B,[HB*],_G,[HG*],_D,[HD*],_E,[HE*],_Z,[HZ*],_H,[HH*],C,O
    for HIS:\n
    HID: (has HD1)\n
    N,[H*],CA,HA,CB,HB2,HB3,CG,ND1,HD1,CE1,HE1,NE2,CD2,HD2,C,O\n
    HIE: (has HE2)\n
    N,[H*],CA,HA,CB,HB2,HB3,CG,ND1,CE1,HE1,NE2,HE2,CD2,HD2,C,O\n
    HIP: (has both)\n
    N,[H*],CA,HA,CB,HB2,HB3,CG,ND1,HD1,CE1,HE1,NE2,HE2,CD2,HD2,C,O\n
    for PHE:\n
    N,[H*],CA,HA,CB,HB2,HB3,CG,CD1,HD1,CE1,HE1,CZ,HZ,CE2,HE2,CD2,HD2,C,O\n
    for PRO:\n
    N,[H*], CD, HD2, HD3, CG, HG2, HG3, CB, HB2, HB3, CA, HA, C, O\n
    for TRP:\n
    N,[H*],CA,HA,CB,HB2,HB3,CG,CD1,HD1,NE1,HE1,CE2,CZ2,HZ2,CH2,HH2,CZ3,HZ3,CE3,HE3,CD2,C,O\n
    for TYR:\n
    N,[H*],CA,HA,CB,HB2,HB3,CG,CD1,HD1,CE1,HE1,CZ,OH,HH,CE2,HE2,CD2,HD2,C,O\n
    """
    def onAddCmdToViewer(self):
        self.atNames = {}
        self.atNames['ACE'] = ['HH31','CH3','HH32','HH33','C','O']
        self.atNames['NME'] = ['N','H','CH3','HH31','HH32','HH33']
        self.atNames['HOH'] = ['H2','O','H3']
        self.atNames['ALA'] = ['N','H','H1','H2','H3','CA','HA','CB','HB1',
                'HB2','HB3', 'C', 'O','OXT']
        self.atNames['ARG'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','CG','HG2','HG3','CD','HD2','HD3','NE','HE','CZ',
                'NH1','NH11','NH12', 'NH2', 'HH21','HH22', 'C', 'O','OXT']
        #ASH is neutral ASP
        self.atNames['ASH'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','CG','OD1','OD2','HD2','C', 'O','OXT']
        self.atNames['ASN'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','CG','OD1','ND2','HD21','HD22', 'C', 'O','OXT']
        self.atNames['ASP'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','CG','OD1','OD2','C', 'O','OXT']
        self.atNames['CIM'] = ['CL-']
        self.atNames['CIP'] = ['NA+']
        #CYM is CYS with negative charge
        self.atNames['CYM'] = ['N','HN','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','SG', 'C', 'O','OXT']
        self.atNames['CYS'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','SG','HG', 'C', 'O','OXT']
        #CYX is CYSTINE (S-S bridge)
        self.atNames['CYX'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','SG', 'C', 'O','OXT']
        #GLH is neutral GLU
        self.atNames['GLH'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','CG','HG2','HG3','CD','OE1','OE2','HE2',
                'C', 'O','OXT']
        self.atNames['GLN'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','CG','HG2','HG3','CD','OE1','NE2','HE21','HE22',
                'C', 'O','OXT']
        self.atNames['GLU'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','CG','HG2','HG3','CD','OE1','OE2','C', 'O','OXT']
        self.atNames['GLY'] = ['N','H','H1','H2','H3','CA','HA2','HA3',
                'C', 'O','OXT']
        #HID is HIS with delta H
        self.atNames['HID'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','CG',' ND1','HD1','CE1','HE1','NE2','CD2','HD2','C',
                'O','OXT']
        #HIE is HIS with epsilon H
        self.atNames['HIE'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','CG',' ND1','CE1','HE1','NE2','HE2','CD2','HD2','C',
                'O','OXT']
        #HIP is HIS with both (positive charge)
        self.atNames['HIP'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','CG',' ND1','HD1', 'CE1','HE1','NE2','HE2','CD2',
                'HD2','C', 'O','OXT']
        self.atNames['ILE'] = ['N','H','H1','H2','H3','CA','HA','CB','HB',
                'CG2','HG21','HG22','HG23','CG1','HG12','HG13', 'CD1',
                'HD11','HD12','HD13','C', 'O','OXT']
        self.atNames['LEU'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3', 'CG','HG', 'CD1','HD11','HD12','HD13','CD2',
                'HD21','HD22','HD23','C', 'O','OXT']
        #LYN is neutral LYS
        self.atNames['LYN'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','CG','HG2','HG3','CD','HD2','HD3','CE','HE2','HE3',
                'NZ','HZ2','HZ3','C', 'O','OXT']
        self.atNames['LYS'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','CG','HG2','HG3','CD','HD2','HD3','CE','HE2','HE3',
                'NZ','HZ1','HZ2','HZ3','C', 'O','OXT']
        self.atNames['MET'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','CG','HG2','HG3','SD','CE','HE1','HE2','HE3', 'C', 'O','OXT']
        self.atNames['PHE'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','CG','CD1','HD1','CE1','HE1', 'CZ','HZ','CE2',
                'HE2','CD2','HD2','C', 'O','OXT']
        self.atNames['PRO'] = ['N','H2','H3','CD', 'HD2', 'HD3',
                'CG', 'HG2', 'HG3', 'CB', 'HB2', 'HB3', 'CA', 'HA', 'C',
                'O','OXT']
        self.atNames['SER'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2','HB3',
                'OG', 'HG','C', 'O','OXT']
        self.atNames['THR'] = ['N','H','H1','H2','H3','CA','HA','CB','HB',
                'CG2','HG21', 'HG22','HG23','OG1','HG1','C', 'O','OXT']
        self.atNames['TRP'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','CG','CD1','HD1','NE1','HE1','CE2', 'CZ2','HZ2','CH2',
                'HH2','CZ3','HZ3','CE3','HE3','CD2', 'C', 'O','OXT']
        self.atNames['TYR'] = ['N','H','H1','H2','H3','CA','HA','CB','HB2',
                'HB3','CG','CD1','HD1','CE1','HE1', 'CZ','OH','HH',
                'CE2','HE2','CD2','HD2','C', 'O','OXT']
        self.atNames['VAL'] = ['N','H','H1','H2','H3','CA','HA','CB','HB',
                'CG1','HG11','HG12', 'HG13', 'CG2','HG21','HG22','HG23',
                'C', 'O','OXT']


    def reorderAtoms(self, res, atList):
        ats = []
        rlen = len(res.atoms)
        resNames = res.atoms.name
        #these lists have n-terminal H's and OXT
        #so relax this requirement
        s = 0
        #check for c-terminus
        if 'OXT' in atList and 'OXT' not in resNames: atList.remove('OXT')
        #check for n-terminus
        if 'H2' not in resNames: 
            atList.remove('H2')
        elif 'H' in atList:
            atList.remove('H')
        if 'H3' not in resNames: atList.remove('H3')
        if 'H1' in atList and 'H1' not in resNames: 
            atList.remove('H1')
        if rlen!= len(atList):
            print "atoms missing in residue", res
            print "expected:", atList
            print "got     :", res.atoms.name
        for i in range(len(atList)):
            a = atList[i]
            for j in range(rlen):
                b = res.atoms[j]
                if b.name==a:
                    ats.append(b)
                    break
        if len(ats)==len(res.atoms):
            res.children.data = ats
            res.atoms.data = ats
        elif len(ats)<len(res.atoms):
            for at in res.atoms:
                if at not in ats:
                    ats.append(at)
            res.children.data = ats
            res.atoms.data = ats
        else:
            msg = res.name + ' has extra atoms '
            #self.warningMsg(msg)
            raise msg


    def doit(self, nodes):
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'

        residues = nodes.findType(Residue)
        if not residues: return 'ERROR'
        residues.sort()

        for res in residues:
            chNames = res.atoms.name

            amberResType = res.type
            
            if amberResType=='CYS':
                print 'in CYS with ', res.name,
                sAt = res.atoms.get(lambda x: x.element=='S')[0]
                isDisulfide = len(sAt.bonds)==2
                print 'isDisulfide=', isDisulfide,
                if 'HG' in chNames or 'HSG' in chNames:
                    amberResType ='CYS'
                    print ' has HG',

                elif 'HN' in chNames:
                    print ' has HN',
                    amberResType ='CYM'
                    print 'using CYM'
                # require that disulfide bridge is built
                elif isDisulfide:
                    amberResType = 'CYX'
                    print ' is CYX',
                print '\n'
            elif amberResType=='LYS':
                if 'HZ1' not in chNames:
                    amberResType = 'LYN'
            elif amberResType=='ASP':
                # neutral ASH not possible at N-terminus
                if 'HD2' in chNames and 'H2' not in chNames:
                    amberResType = 'ASH'
            elif amberResType=='GLU':
                # neutral GLH not possible at either terminus
                if 'HE2' in chNames and ('OXT' not in chNames and \
                    'H2' not in chNames):
                        amberResType = 'GLH'
            elif amberResType=='HIS':
                returnVal = 'HIS'
                hasHD1 = 'HD1' in chNames
                hasHD2 = 'HD2' in chNames
                hasHE1 = 'HE1' in chNames
                hasHE2 = 'HE2' in chNames
                if hasHD1 and hasHE1:
                    if hasHD2 and not hasHE2:
                        amberResType = 'HID'
                    elif hasHD2 and hasHE2:
                        amberResType = 'HIP'
                elif (not hasHD1) and (hasHE1 and hasHD2 and hasHE2):
                    amberResType = 'HIE'
                else:
                    print 'unknown HISTIDINE config'
                    raise ValueError

            res.amber_type = amberResType
            listCopy = []
            for n in self.atNames[amberResType]:
                listCopy.append(n)
            self.reorderAtoms(res, listCopy)






commandList=[
    {'name':'setup_Amber94','cmd':SetupAmber94(),\
        'gui': SetupAmber94CommandGUI},
    {'name':'setminimOpts_Amber94','cmd':SetMinimOptsAmber94(),\
        'gui': SetMinimOptsAmber94CommandGUI},
    {'name':'setmdOpts_Amber94','cmd':SetMDOptsAmber94(),\
        'gui': SetMDOptsAmber94CommandGUI},
    {'name':'minimize_Amber94','cmd':MinimizeAmber94(), 
            'gui':MinimizeAmber94CommandGUI},
    {'name':'md_Amber94','cmd':MolecularDynamicsAmber94(), 
            'gui':MolecularDynamicsAmber94CommandGUI},
    {'name':'play_md_trj_Amber94','cmd':PlayMolecularDynamicsTrjAmber94(), 
            'gui':PlayMolecularDynamicsTrjAmber94CommandGUI},
    {'name':'freezeAtoms_Amber94','cmd':FreezeAtomsAmber94(), 
            'gui':FreezeAtomsAmber94CommandGUI},
    {'name':'constrainAtoms_Amber94','cmd':ConstrainAtomsAmber94(), 
            'gui':ConstrainAtomsAmber94CommandGUI},
    #moved from editCommands.py:
    {'name':'fixAmberHNames','cmd':FixAmberHAtomNamesCommand(), 'gui': None},
    {'name':'fixAmberHNamesGC','cmd':FixAmberHAtomNamesGUICommand(),
     'gui': FixAmberHAtomNamesGUICommandGUI},
    {'name':'fixAmberResNamesOrder','cmd':FixAmberResNamesAndOrderAtomsCommand(),
        'gui': None},
    ]



def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
