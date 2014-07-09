## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################
"""
Module implementing the basic commands that are present when instanciating
a ViewerFramework class or ViewerFramework derived class.
   - loadCommandCommand
   - loadModuleCommand
   - loadMacroCommand
   - ExitCommand
   - ShellCommand
   - UndoCommand
   - ResetUndoCommand.
"""

# $Header: /opt/cvs/python/packages/share1.5/ViewerFramework/basicCommand.py,v 1.139.2.3 2011/09/30 19:55:31 sargis Exp $
#
# $Id: basicCommand.py,v 1.139.2.3 2011/09/30 19:55:31 sargis Exp $
#
import os, sys, subprocess

from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.util.callback import CallBackFunction
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser, \
     LoadButton, kbScrolledListBox
from mglutil.util.packageFilePath import findFilePath, \
     findModulesInPackage, getResourceFolderWithVersion

import types, Tkinter, Pmw, os, sys, traceback
from string import join
import tkMessageBox
from ViewerFramework.VFCommand import Command, CommandGUI
import warnings
import string
commandslist=[]
cmd_docslist={}

def findAllVFPackages():
    """Returns a list of package names found in sys.path"""
    packages = {}
    for p in ['.']+sys.path:
        flagline = []
        if not os.path.exists(p) or not os.path.isdir(p):
            continue
        files = os.listdir(p)
        for f in files:
            pdir = os.path.join(p, f)
            if not os.path.isdir(pdir):
                continue
            if os.path.exists( os.path.join( pdir, '__init__.py')) :
            
                fptr =open("%s/__init__.py" %pdir)
                Lines = fptr.readlines()
                flagline =filter(lambda x:x.startswith("packageContainsVFCommands"),Lines)
                if not flagline ==[]:
                    if not packages.has_key(f):
                        packages[f] = pdir
    return packages

class  UndoCommand(Command):
    """pops undo string from the stack and executes it in the ViewerFrameworks
    scope
    \nPackage : ViewerFramework
    \nModule : basicCommand.py
    \nClass : UndoCommand
    \nCommand : Undo
    \nSynopsis:\n
        None <- Undo()
    """

    def __init__(self, func=None):
        Command.__init__(self, func)
        self.ctr = 1         # used to assure unique keys for _undoArgs
        self._undoArgs = {}  # this dict is used to save large Python objects
                             # that we do not want to turn into strings

    def get_ctr(self):
        #used to build unique '_undoArg_#'  strings
        #cannot simply use len(self_undoArgs)+1
        #because some entries may have been removed
        # for instance, using len(self_undoArgs)+1 only
        #   add 1: _undoArg_1, add another: _undoArg_2
        #   remove _undoArg_1
        #   next addition would replicate _undoArg_2 
        if not len(self._undoArgs):
            self.ctr = 1
        else:
            self.ctr += 1
        return self.ctr 
            

    def saveUndoArg(self, arg):
        """Add arg to self._undoArgs under a unique name and returns this name
"""
        name = '_undoArg_%d'%len(self._undoArgs)
        i = 1
        while self._undoArgs.has_key(name):
            name = '_undoArg_%d'%(self.get_ctr())
            i += 1
        self._undoArgs[name] = arg
        return name
    
        
    def validateUserPref(self, value):
        try:
            val = int(value)
            if val >-1:
                return 1
            else:
                return 0
        except:
            return 0
        
        
        
    def onAddCmdToViewer(self):
        doc = """Number of commands that can be undone"""
        if self.vf.hasGui:         
            TButton = self.vf.GUI.menuBars['Toolbar']._frame.toolbarButtonDict['Undo']
            self.balloon = Pmw.Balloon(self.vf.GUI.ROOT)
            self.balloon.bind(TButton, 'Undo')
            self.setLabel()
        self.vf.userpref.add( 'Number of Undo', 100,
                              validateFunc=self.validateUserPref,
                              doc=doc)
        
    def doit(self):
        if len(self.vf.undoCmdStack):
            command = self.vf.undoCmdStack.pop()[0]
            localDict = {'self':self.vf}
            localDict.update( self._undoArgs ) # add undoArgs to local dict
            exec( command, sys.modules['__main__'].__dict__, localDict)
            # remove _undoArg_%d used by this command from self._undoArgs dict
            ind = command.find('_undoArg_')
            while ind != -1 and ind < len(command)-10:
                name = command[ind: ind+9]
                end = ind+9
                # add digits following string
                while command[end].isdigit():
                    name += command[end]
                    end +=1
                nodes = self._undoArgs[name]
                del self._undoArgs[name]
                new_start = ind + len(name)
                ind = command[new_start:].find('_undoArg_') 
                if ind!=-1:
                    ind = ind + new_start
                
            #exec( command, self.vf.__dict__ )
            self.setLabel()
            

    def guiCallback(self, event=None):
        self.doitWrapper(topCommand=0, log=0, busyIdle=1)
        

    def __call__(self, **kw):
        """None<---Undo()
        """
        self.doitWrapper(topCommand=0, log=0, busyIdle=1)


    def addEntry(self, undoString, menuString):
        self.vf.undoCmdStack.append( (undoString, menuString) )
        maxLen = self.vf.userpref['Number of Undo']['value']
        if maxLen>0 and len(self.vf.undoCmdStack)>maxLen:
            self.vf.undoCmdStack = self.vf.undoCmdStack[-maxLen:]
        self.vf.undo.setLabel()


    def setLabel(self):
        """change menu entry label to show command name"""
        
        if not self.vf.hasGui: return
        cmdmenuEntry = self.GUI.menu[4]['label']
        if len(self.vf.undoCmdStack)==0:
            state = 'disabled'
            label = 'Undo '
            if self.vf.GUI.menuBars.has_key('Toolbar'):
                TButton = self.vf.GUI.menuBars['Toolbar']._frame.toolbarButtonDict['Undo']
                TButton.disable()
                #if hasattr(self,'balloon'):
                #     self.balloon.destroy()

                #self.balloon = Pmw.Balloon(self.vf.GUI.ROOT)
                #self.balloon.bind(TButton, 'Undo')
                #rebind other functions from toolbarbutton
                TButton.bind("<Enter>", TButton.buttonEnter, '+')
                TButton.bind("<Leave>", TButton.buttonLeave, '+')
                TButton.bind("<ButtonPress-1>",   TButton.buttonDown)
                TButton.bind("<ButtonRelease-1>", TButton.buttonUp)

        else:
            state='normal'
            label = 'Undo ' + self.vf.undoCmdStack[-1][1]
            if self.vf.GUI.menuBars.has_key('Toolbar'):
                TButton = self.vf.GUI.menuBars['Toolbar']._frame.toolbarButtonDict['Undo']
                TButton.enable()
                #if hasattr(self,'balloon'):
                #     self.balloon.destroy()
                #self.balloon = Pmw.Balloon(self.vf.GUI.ROOT)
                self.balloon.bind(TButton, label)
                #rebind other functions from toolbarbutton
                TButton.bind("<Enter>", TButton.buttonEnter, '+')
                TButton.bind("<Leave>", TButton.buttonLeave, '+')
                TButton.bind("<ButtonPress-1>",   TButton.buttonDown)
                TButton.bind("<ButtonRelease-1>", TButton.buttonUp)

        self.vf.GUI.configMenuEntry(self.GUI.menuButton, cmdmenuEntry,
                                    label=label, state=state)
        self.GUI.menu[4]['label']=label

class RemoveCommand(Command):
    def loadCommands(self):
        for key in self.vf.removableCommands.settings:
            try:
                self.vf.browseCommands.doit(key, self.vf.removableCommands.settings[key][0],
                                   self.vf.removableCommands.settings[key][1])
            except Exception, inst:
                print __file__, inst 
            
            
    def guiCallback(self):
        idf = InputFormDescr(title='Remove Command')
        idf.append({'name':'cmd',
            'widgetType':kbScrolledListBox,
            'wcfg':{'items':self.vf.removableCommands.settings.keys(),
                    'listbox_exportselection':0,
                    'listbox_selectmode':'extended',
                    'labelpos':'nw',
                    'label_text':'Available commands:',
                    #'dblclickcommand':self.loadCmd_cb,
                    #'selectioncommand':self.displayCmd_cb,
                    },
            'gridcfg':{'sticky':'wesn', 'row':-1}})
    
        val = self.vf.getUserInput(idf, modal=1, blocking=1)
        if val:
            self.vf.removableCommands.settings.pop(val['cmd'][0])
            self.vf.removableCommands.saveAllSettings()
            
            txt = "You need to restart for the changes to take effect."
            
            tkMessageBox.showinfo("Restart is Needed", txt)                
                        
class  ResetUndoCommand(Command):
    """ Class to reset Undo()
    \nPackage : ViewerFramework
    \nModule : basicCommand.py
    \nClass : ResetUndoCommand
    \nCommand : resetUndo
    \nSynopsis:\n
        None<---resetUndo()
    """

    def doit(self):
        self.vf.undoCmdStack = []
        self.vf.undo._undoArgs = {}  # reset dict used to save large Python objects
        self.vf.undo.setLabel()
        for command in self.vf.commands:
            if hasattr(command, 'command'): # added to handle 'computeSheet2D' case
                command.undoStack = [] 
        
    def __call__(self, **kw):
        """None<---resetUndo()
        """
        apply( self.doitWrapper, (), kw )


class BrowseCommandsCommand(Command):
    """Command to load dynamically either modules or individual commands
    in the viewer.
    \nPackage : ViewerFramework
    \nModule : basicCommand.py
    \nClass : BrowseCommandsCommand
    \nCommand : browseCommands
    \nSynopsis:\n
        None <-- browseCommands(module, commands=None, package=None, **kw)
    \nRequired Arguements:\n
        module --- name of the module(eg:colorCommands)
    \nOptional Arguements:\n
        commnads --- one list of commands to load
        \npackage --- name of the package to which module belongs(eg:Pmv,Vision)
    """
    def __init__(self, func=None):
        Command.__init__(self, func)
        self.allPack = {}
        self.packMod = {}
        self.allPackFlag = False
        self.txtGUI = ""


    def doit(self, module, commands=None, package=None, removable=False):
#        if removable:
#            self.vf.removableCommands.settings[module] = [commands, package]
#            self.vf.removableCommands.saveAllSettings()
        # If the package is not specified the default is the first library
        global commandslist,cmd_docslist
        if package is None: package = self.vf.libraries[0]
        
        importName = package + '.' + module
        try:
            mod = __import__(importName, globals(), locals(),
                            [module])
        except:
            if self.cmdForms.has_key('loadCmds') and \
                self.cmdForms['loadCmds'].f.winfo_toplevel().wm_state() == \
                                                                       'normal':
                   self.vf.warningMsg("ERROR: Could not load module %s"%module,
                                        parent = self.cmdForms['loadCmds'].root)
            elif self.vf.loadModule.cmdForms.has_key('loadModule') and \
                self.vf.loadModule.cmdForms['loadModule'].f.winfo_toplevel().wm_state() == \
                                                                       'normal':
                   self.vf.warningMsg("ERROR: Could not load module %s"%module,
                        parent = self.vf.loadModule.cmdForms['loadModule'].root)
            else:
                self.vf.warningMsg("ERROR: Could not load module %s"%module)
            traceback.print_exc()
            return 'ERROR'

        if commands is None:
            if hasattr(mod,"initModule"):
                if self.vf.hasGui : 
                    mod.initModule(self.vf)
                else :
                    #if there is noGUI and if we want to have multiple session of mv
                    #need to instanciate new commands, and not use the global dictionay commandList
                    if  hasattr(mod, 'commandList'):
                        for d in mod.commandList:
                            d['cmd'] = d['cmd'].__class__()
                            #print "load all comands ", d['cmd'], d['name'], d['gui']
                            self.vf.addCommand( d['cmd'], d['name'], d['gui'])
                    else : print mod
                if  hasattr(mod, 'commandList'):
                    for x in mod.commandList:
                        cmd=x['name']
                        c=x['cmd']
                        #print 'CCCCCCC', cmd
                        if cmd not in cmd_docslist:
                            if hasattr(c,'__doc__'):
                                cmd_docslist[cmd]=c.__doc__
                        if x['gui']:
                            if x['gui'].menuDict:
                                if len(self.txtGUI) < 800:
                                    self.txtGUI += "\n"+x['gui'].menuDict['menuButtonName']
                                    if x['gui'].menuDict['menuCascadeName']:
                                        self.txtGUI += "->"+ x['gui'].menuDict['menuCascadeName']
                                    self.txtGUI  += "->"+x['gui'].menuDict['menuEntryLabel']

                        if cmd not in commandslist: 
                            commandslist.append(cmd)   

                #print 'ZZZZZZZZZZZZ', mod
                        
            else:
                if self.cmdForms.has_key('loadCmds') and \
                    self.cmdForms['loadCmds'].f.winfo_toplevel().wm_state() == \
                                                                           'normal':
                       self.vf.warningMsg("ERROR: Could not load module %s"%module,
                                            parent = self.cmdForms['loadCmds'].root)
                elif self.vf.loadModule.cmdForms.has_key('loadModule') and \
                    self.vf.loadModule.cmdForms['loadModule'].f.winfo_toplevel().wm_state() == \
                                                                           'normal':
                       self.vf.warningMsg("ERROR: Could not load module %s"%module,
                            parent = self.vf.loadModule.cmdForms['loadModule'].root)                
                else:
                    self.vf.warningMsg("ERROR: Could not load module  %s"%module) 
                return "ERROR"
        else:
            if not type(commands) in [types.ListType, types.TupleType]:
                commands = [commands,]
            if not hasattr(mod, 'commandList'): 
                return
            for cmd in commands:
                d = filter(lambda x: x['name'] == cmd, mod.commandList)
                if len(d) == 0:
                    self.vf.warningMsg("Command %s not found in module %s.%s"%
                                       (cmd, package, module))
                    continue
                d = d[0]
                if cmd not in cmd_docslist:
                    if hasattr(d['cmd'],'__doc__'):
                        cmd_docslist[cmd]=d['cmd'].__doc__
                if cmd not in commandslist:
                    commandslist.append(cmd)
                if not self.vf.hasGui :
                    #if there is noGUI and if we want to have multiple session of mv
                    #need to instanciate new commands, and not use the global dictionay commandList
                    #print "load specific comands ", d['cmd'], d['name'], d['gui']
                    d['cmd'] = d['cmd'].__class__()
                self.vf.addCommand(d['cmd'], d['name'], d['gui'])
                
    def __call__(self, module, commands=None, package=None, **kw):
        """None<---browseCommands(module, commands=None, package=None, **kw)
        \nmodule --- name of the module(eg:colorCommands)
        \ncommnads --- one list of commands to load
        \npackage --- name of the package to which module belongs(eg:Pmv,Vision)
        """
        kw['commands'] = commands
        kw['package'] = package
        apply(self.doitWrapper, (module,), kw )
    

    def buildFormDescr(self, formName):
        import Tkinter
        if not formName == 'loadCmds': return
        idf = InputFormDescr(title='Load Modules and Commands')
        pname = self.vf.libraries
        #when Pvv.startpvvCommnads is loaded some how Volume.Pvv is considered
        #as seperate package and is added to packages list in the widget
        #To avoid this packages having '.' are removed
        for p in pname:
            if '.' in p:
                ind = pname.index(p)
                del pname[ind]
        
        idf.append({'name':'packList',
                    'widgetType':kbScrolledListBox,
                    'wcfg':{'items':pname,
                            #'defaultValue':pname[0],
                            'listbox_exportselection':0,
                            'labelpos':'nw',
                            'label_text':'Select a package:',
                            #'dblclickcommand':self.loadMod_cb,
                            'selectioncommand':self.displayMod_cb
                            },
                    'gridcfg':{'sticky':'wesn'}})
        
        
        idf.append({'name':'modList',
                    'widgetType':kbScrolledListBox,
                    'wcfg':{'items':[],
                            'listbox_exportselection':0,
                            'labelpos':'nw',
                            'label_text':'Select a module:',
                            #'dblclickcommand':self.loadMod_cb,
                            'selectioncommand':self.displayCmds_cb,
                            },
                    'gridcfg':{'sticky':'wesn', 'row':-1}})

        idf.append({'name':'cmdList',
                    'widgetType':kbScrolledListBox,
                    'wcfg':{'items':[],
                            'listbox_exportselection':0,
                            'listbox_selectmode':'extended',
                            'labelpos':'nw',
                            'label_text':'Available commands:',
                            #'dblclickcommand':self.loadCmd_cb,
                            'selectioncommand':self.displayCmd_cb,
                            },
                    'gridcfg':{'sticky':'wesn', 'row':-1}})

#        idf.append({'name':'docbutton',
#                    'widgetType':Tkinter.Checkbutton,
#                    #'parent':'DOCGROUP',
#                    'defaultValue':0,
#                    'wcfg':{'text':'Show documentation',
#                               'onvalue':1,
#                               'offvalue':0,
#                               'command':self.showdoc_cb,
#                               'variable':Tkinter.IntVar()},
#                        'gridcfg':{'sticky':'nw','columnspan':3}})
                    
        idf.append({'name':'DOCGROUP',
                        'widgetType':Pmw.Group,
                        'container':{'DOCGROUP':"w.interior()"},
                        'collapsedsize':0,
                        'wcfg':{'tag_text':'Description'},
                        'gridcfg':{'sticky':'wnse', 'columnspan':3}})

        idf.append({'name':'doclist',
                    'widgetType':kbScrolledListBox,
                    'parent':'DOCGROUP',
                    'wcfg':{'items':[],
                            'listbox_exportselection':0,
                            'listbox_selectmode':'extended',
                            },
                    'gridcfg':{'sticky':'wesn', 'columnspan':3}})
        
        idf.append({'name':'allPacks',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Show all packages',
                            'command':self.allPacks_cb},
                    'gridcfg':{'sticky':'ew'}})

        idf.append({'name':'loadMod',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Load selected module',
                            'command':self.loadMod_cb},
                    'gridcfg':{'sticky':'ew', 'row':-1}})

#        idf.append({'name':'loadCmd',
#                    'widgetType':Tkinter.Button,
#                    'wcfg':{'text':'Load Command',
#                            'command':self.loadCmd_cb},
#                    'gridcfg':{'sticky':'ew', 'row':-1}})

        idf.append({'name':'dismiss',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Dismiss',
                            'command':self.dismiss_cb},
                    'gridcfg':{'sticky':'ew', 'row':-1}})

#        idf.append({'name':'dismiss',
#                    'widgetType':Tkinter.Button,
#                    'wcfg':{'text':'DISMISS',
#                            'command':self.dismiss_cb,
#                           },
#                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W,'columnspan':3}})

        return idf

    def guiCallback(self):
        self.vf.GUI.ROOT.config(cursor='watch')
        self.vf.GUI.ROOT.update()
        if self.allPack == {}:
            self.allPack = findAllVFPackages()
        val = self.showForm('loadCmds', force=1,modal=0,blocking=0)
        ebn = self.cmdForms['loadCmds'].descr.entryByName
#        docb=ebn['docbutton']['widget']
#        var=ebn['docbutton']['wcfg']['variable'].get()
#        if var==0:
#            dg=ebn['DOCGROUP']['widget']
#            dg.collapse()
        self.vf.GUI.ROOT.config(cursor='')
        
    def dismiss_cb(self, event=None):
        self.cmdForms['loadCmds'].withdraw()
        
    def allPacks_cb(self, event=None):
        ebn = self.cmdForms['loadCmds'].descr.entryByName
        packW = ebn['packList']['widget']
        if not self.allPackFlag:
            packName = self.allPack.keys()
            packW.setlist(packName)
            ebn['allPacks']['widget'].configure(text='Show default packages')
            self.allPackFlag = True
        else:
            packName = self.vf.libraries
            packW.setlist(packName)
            ebn['allPacks']['widget'].configure(text='Show all packages')
            self.allPackFlag = False
            
        ebn['modList']['widget'].clear()
        ebn['cmdList']['widget'].clear()
    

#    def showdoc_cb(self,event=None):
#        #when a show documentation is on and a module is selected then 
#        #expands dg else dg is collapsed
#        ebn = self.cmdForms['loadCmds'].descr.entryByName
#        docb=ebn['docbutton']['widget']
#        var=ebn['docbutton']['wcfg']['variable'].get()
#        dg=ebn['DOCGROUP']['widget']
#        docw=ebn['doclist']['widget']
#        packW = ebn['packList']['widget']
#        psel=packW.getcurselection()
#        if var==0:
#            dg.collapse()
#        if var==1 and psel:
#            if docw.size()>0:
#                dg.expand()
            
        
    def displayMod_cb(self, event=None):
        #print "displayMod_cb"

#        c = self.cmdForms['loadCmds'].mf.cget('cursor')
        
#        self.cmdForms['loadCmds'].mf.configure(cursor='watch')
#        self.cmdForms['loadCmds'].mf.update_idletasks()
        ebn = self.cmdForms['loadCmds'].descr.entryByName
#        docb=ebn['docbutton']['widget']
#        var=ebn['docbutton']['wcfg']['variable'].get()
#        dg = ebn['DOCGROUP']['widget']
#        dg.collapse()
        packW = ebn['packList']['widget']
        packs = packW.getcurselection()
        if len(packs) == 0:
            return
        packName = packs[0]
        if not self.packMod.has_key(packName):
            package = self.allPack[packName]
            self.packMod[packName] = findModulesInPackage(package,"^def initModule",fileNameFilters=['Command'])
        self.currentPack = packName
        modNames = []
        for key, value in self.packMod[packName].items():
            pathPack = key.split(os.path.sep)
            if pathPack[-1] == packName:
                newModName = map(lambda x: x[:-3], value)
                #for mname in newModName:
                   #if "Command" not in mname :
                       #ind = newModName.index(mname)
                       #del  newModName[ind]
                modNames = modNames+newModName       
            else:
                pIndex = pathPack.index(packName)
                prefix = join(pathPack[pIndex+1:], '.')
                newModName = map(lambda x: "%s.%s"%(prefix, x[:-3]), value)
                #for mname in newModName:
                    #if "Command" not in mname :
                        #ind = newModName.index(mname)
                        #del  newModName[ind]
                modNames = modNames+newModName       
        modNames.sort()
        modW = ebn['modList']['widget']
        modW.setlist(modNames)
        # and clear contents in self.libraryGUI
        cmdW = ebn['cmdList']['widget']
        cmdW.clear()
        m = __import__(packName, globals(), locals(),[])
        d = []
        docstring=m.__doc__
        #d.append(m.__doc__)
        docw = ebn['doclist']['widget']
        docw.clear()
        #formatting documentation. 
        if docstring!=None :
            if '\n' in docstring:
                x = string.split(docstring,"\n")
                for i in x:
                    if i !='':
                        d.append(i)
                    if len(d)>8:
                        docw.configure(listbox_height=8)        
                    else:
                        docw.configure(listbox_height=len(d))
            else:
                x = string.split(docstring," ")
                #formatting documenation
                if len(x)>10:
                    docw.configure(listbox_height=len(x)/10)
                else:
                    docw.configure(listbox_height=1)
            
        
        
        docw.setlist(d)
        
 #       self.cmdForms['loadCmds'].mf.configure(cursor=c)
        #when show documentation on after selcting a package
        #dg is expanded to show documenttation
        #if var==1 and docw.size()>0:
        if docw.size()>0:
            dg.expand()


    def displayCmds_cb(self, event=None):
        #print "displayCmds_cb"

        global cmd_docslist
        self.cmdForms['loadCmds'].mf.update_idletasks()

        ebn = self.cmdForms['loadCmds'].descr.entryByName
        dg = ebn['DOCGROUP']['widget'] 
        dg.collapse()
        cmdW = ebn['cmdList']['widget']
        cmdW.clear()

#        docb=ebn['docbutton']['widget']
#        var=ebn['docbutton']['wcfg']['variable'].get()
        modName = ebn['modList']['widget'].getcurselection()
        if modName == (0 or ()): return
        else: 
            modName = modName[0]
        importName = self.currentPack + '.' + modName
        try:
            m = __import__(importName, globals(), locals(),['commandList'])
        except:
            return

        if not hasattr(m, 'commandList'):
            return
        cmdNames = map(lambda x: x['name'], m.commandList)
        cmdNames.sort()
        if modName:
            self.var=1
            d =[]
            docstring =m.__doc__
            import string
            docw = ebn['doclist']['widget']
            docw.clear()
            if docstring!=None :
                    if '\n' in docstring:
                        x = string.split(docstring,"\n")
                        for i in x:
                            if i !='':
                                d.append(i)
                        #formatting documenation
                        if len(d)>8:
                            docw.configure(listbox_height=8)        
                        else:
                            docw.configure(listbox_height=len(d))
                    else:
                         d.append(docstring)
                         x = string.split(docstring," ")
                         #formatting documenation
                         if len(x)>10:
                            docw.configure(listbox_height=len(x)/10)
                         else:
                            docw.configure(listbox_height=1)
                    
            docw.setlist(d)
        CmdName=ebn['cmdList']['widget'].getcurselection()
        cmdW.setlist(cmdNames)

        #when show documentation is on after selcting a module or a command
        #dg is expanded to show documenttation 
        #if var==1 and docw.size()>0:
        if docw.size()>0:
             dg.expand()


    def displayCmd_cb(self, event=None):
        #print "displayCmd_cb"
        
        global cmd_docslist
        self.cmdForms['loadCmds'].mf.update_idletasks()

        ebn = self.cmdForms['loadCmds'].descr.entryByName
        dg = ebn['DOCGROUP']['widget'] 
        dg.collapse()
#        docb=ebn['docbutton']['widget']
#        var=ebn['docbutton']['wcfg']['variable'].get()
        modName = ebn['modList']['widget'].getcurselection()
        if modName == (0 or ()): return
        else: 
            modName = modName[0]
        importName = self.currentPack + '.' + modName
        try:
            m = __import__(importName, globals(), locals(),['commandList'])
        except:
            self.warningMsg("ERROR: Cannot find commands for %s"%modName)
            return

        if not hasattr(m, 'commandList'):
            return
        cmdNames = map(lambda x: x['name'], m.commandList)
        cmdNames.sort()
        if modName:
            self.var=1
            d =[]
            docstring =m.__doc__
            import string
            docw = ebn['doclist']['widget']
            docw.clear()
            if docstring!=None :
                    if '\n' in docstring:
                        x = string.split(docstring,"\n")
                        for i in x:
                            if i !='':
                                d.append(i)
                        #formatting documenation
                        if len(d)>8:
                            docw.configure(listbox_height=8)        
                        else:
                            docw.configure(listbox_height=len(d))
                    else:
                         d.append(docstring)
                         x = string.split(docstring," ")
                         #formatting documenation
                         if len(x)>10:
                            docw.configure(listbox_height=len(x)/10)
                         else:
                            docw.configure(listbox_height=1)
                    
            docw.setlist(d)
        cmdW = ebn['cmdList']['widget']
        CmdName=ebn['cmdList']['widget'].getcurselection()
        cmdW.setlist(cmdNames)
        if len(CmdName)!=0:
            for i in m.commandList:
                if i['name']==CmdName[0]:
                    c = i['cmd']
            if CmdName[0] in cmdNames:
                ind= cmdNames.index(CmdName[0])
                cmdW.selection_clear()
                cmdW.selection_set(ind)
                d =[]
                docstring=c.__doc__
                docw = ebn['doclist']['widget']
                docw.clear()
                if CmdName[0] not in cmd_docslist.keys():
                    cmd_docslist[CmdName[0]]=d
                import string
                if docstring!=None :
                    if '\n' in docstring:
                        x = string.split(docstring,"\n")
                        for i in x:
                            if i !='':
                                d.append(i)
                        if len(d)>8:
                            docw.configure(listbox_height=8)
                        else:
                            docw.configure(listbox_height=len(d))
                    else:
                        d.append(docstring)
                        x = string.split(docstring," ")
                        if len(x)>10:
                            docw.configure(listbox_height=len(x)/10)
                        else:
                            docw.configure(listbox_height=1)
                               
                docw.setlist(d)    
        #when show documentation is on after selcting a module or a command
        #dg is expanded to show documenttation 
        #if var==1 and docw.size()>0:
        if docw.size()>0:
             dg.expand()


    def loadMod_cb(self, event=None):
        ebn = self.cmdForms['loadCmds'].descr.entryByName
        selMod = ebn['modList']['widget'].getcurselection()
        if len(selMod)==0: return
        else:
            self.txtGUI = ""
            apply(self.doitWrapper, ( selMod[0],),
                  {'commands':None, 'package':self.currentPack, 'removable':True})
            self.dismiss_cb(None)
            if self.txtGUI:
                self.txtGUI = "\n Access this command via:\n"+self.txtGUI
            tkMessageBox.showinfo("Load Module", selMod[0]+" loaded successfully!\n"+self.txtGUI)

#    def loadCmd_cb(self, event=None):
#        ebn = self.cmdForms['loadCmds'].descr.entryByName
#        selCmds = ebn['cmdList']['widget'].getcurselection()
#        selMod = ebn['modList']['widget'].getcurselection()
#        if len(selCmds)==0: return
#        else:
#            apply(self.doitWrapper, (selMod[0],), {'commands':selCmds,
#                                                  'package':self.currentPack})


class loadModuleCommand(Command):
    """Command to load dynamically modules to the Viewer import the file called name.py and execute the function initModule defined in that file Raises a ValueError exception if initModule is not defined
    \nPackage : ViewerFramework
    \nModule : basicCommand.py
    \nClass : loadModuleCommand
    \nCommand : loadModule
    \nSynopsis:\n
        None<--loadModule(filename, package=None, **kw)
    \nRequired Arguements:\n
        filename --- name of the module
    \nOptional Arguements:\n   
        package --- name of the package to which filename belongs
    """

    active = 0
    
    def doit(self, filename, package):
        # This is NOT called because we call browseCommand()"
        if package is None:
            _package = filename
        else:
            _package = "%s.%s"%(package, filename)
        try:
            mod = __import__( _package, globals(), locals(), ['initModule'])
            if hasattr(mod, 'initModule') or not callable(mod.initModule):
                mod.initModule(self.vf)
            else:
                self.vf.warningMsg('module %s has not initModule function')     
        except ImportError:
            self.vf.warningMsg('module %s could not be imported'%_package)
        
            
##         if package is None:
##             _package = filename
##         else:
##             _package = "%s.%s"%(package, filename)
##         module = self.vf.tryto( __import__ , _package, globals(), locals(),
##                                [filename])
##         if module=='ERROR':
##             print '\nWARNING: Could not load module %s' % filename
##             return
        

    def __call__(self, filename, package=None, **kw):
        """None<---loadModule(filename, package=None, **kw)
        \nRequired Arguements:\n
            filename --- name of the module
        \nOptional Arguements:\n   
            package --- name of the package to which filename belongs
        """
        if package==None:
            package=self.vf.libraries[0]
        if not kw.has_key('redraw'):
            kw['redraw'] = 0
        kw['package'] = package
        apply(self.vf.browseCommands, (filename,), kw)
        #apply( self.doitWrapper, (filename, package), kw )


    def loadModule_cb(self, event=None):
        
#        c = self.cmdForms['loadModule'].mf.cget('cursor')
#        self.cmdForms['loadModule'].mf.configure(cursor='watch')
#        self.cmdForms['loadModule'].mf.update_idletasks()
        ebn = self.cmdForms['loadModule'].descr.entryByName
        moduleName = ebn['Module List']['widget'].get()
        package = ebn['package']['widget'].get()
        if moduleName:
            self.vf.browseCommands(moduleName[0], package=package, redraw=0)        
#        self.cmdForms['loadModule'].mf.configure(cursor=c)
    def loadModules(self, package, library=None):
        modNames = []
        doc = []
        self.filenames={}
        self.allPack={}
        self.allPack=findAllVFPackages()
        if package is None: return [], []
        if not self.filenames.has_key(package):
            pack=self.allPack[package]
            #finding modules in a package
            self.filenames[pack] =findModulesInPackage(pack,"^def initModule",fileNameFilters=['Command'])
        # dictionary of files keys=widget, values = filename
        for key, value in self.filenames[pack].items():
            pathPack = key.split(os.path.sep)
            if pathPack[-1] == package:
                newModName = map(lambda x: x[:-3], value)
                #for mname in newModName:
                   #if not modulename has Command in it delete from the
                   #modules list  
                   #if "Command" not in mname :
                       #ind = newModName.index(mname)
                       #del  newModName[ind]
                   #if "Command"  in mname :
                if hasattr(newModName,"__doc__"):
                    doc.append(newModName.__doc__)
                else:
                    doc.append(None)
                modNames = modNames + newModName
                
            else:
                pIndex = pathPack.index(package)
                prefix = join(pathPack[pIndex+1:], '.')
                newModName = map(lambda x: "%s.%s"%(prefix, x[:-3]), value)
                #for mname in newModName:
                   #if not modulename has Command in it delete from the
                   #modules list
                   #if "Command" not in mname :
                       #ind = newModName.index(mname)
                       #del  newModName[ind]
                if hasattr(newModName,"__doc__"):
                    doc.append(newModName.__doc__)
                else:
                    doc.append(None)      
                modNames = modNames + newModName
            modNames.sort()
            return modNames, doc     
        
    
    def package_cb(self, event=None):
        ebn = self.cmdForms['loadModule'].descr.entryByName
        pack = ebn['package']['widget'].get()
        names, docs = self.loadModules(pack)
        w = ebn['Module List']['widget']
        w.clear()
        for n,d in map(None, names, docs):
            w.insert('end', n, d)

    def buildFormDescr(self, formName):
        """create the cascade menu for selecting modules to be loaded"""
        if not formName == 'loadModule':return
        ifd = InputFormDescr(title='Load command Modules')
        names, docs = self.loadModules(self.vf.libraries[0])
        entries = map(lambda x: (x, None), names)
        pname=self.vf.libraries
        for p in pname:
            if '.' in p:
                ind = pname.index(p)
                del pname[ind]
        ifd.append({
            'name':'package',
            'widgetType': Pmw.ComboBox,
            'defaultValue': pname[0],
            'wcfg':{ 'labelpos':'nw', 'label_text':'Package:',
                     'selectioncommand': self.package_cb,
                     'scrolledlist_items':pname
                     },
            'gridcfg':{'sticky':'ew', 'padx':2, 'pady':1}
            })
        
        ifd.append({'name': 'Module List',
                    'widgetType':ListChooser,
                    'wcfg':{
                        'title':'Choose a module',
                        'entries': entries,
                        'lbwcfg':{'width':27,'height':10},
                        'command':self.loadModule_cb,
                        'commandEvent':"<Double-Button-1>"
                        },
                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W}
                    })

        ifd.append({'name': 'Load Module',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Load Module',
                            'command': self.loadModule_cb,
                            'bd':6},
                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W},
                    })

        ifd.append({'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Dismiss',
                            'command': self.Dismiss_cb},
                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W}})
        return ifd

    def Dismiss_cb(self):
        self.cmdForms['loadModule'].withdraw()
        self.active = 0
        

    def guiCallback(self, event=None):
        if self.active: return
        self.active = 1
        form = self.showForm('loadModule', force=1,modal=0,blocking=0)
        form.root.protocol('WM_DELETE_WINDOW',self.Dismiss_cb)
        


class loadCommandCommand(loadModuleCommand):
    """Command to load dynamically individual commands in the Viewer.
    \nPackage : ViewerFramework
    \nModule : basicCommand.py
    \nClass : loadCommandCommand
    \nCommand : loadCommand
    \nSynopsis:\n
        None <- loadCommand(moduleName, commandsName, package=None,
        gui=None)
    \nRequired Arguements:\n
        moduleName --- name of the module to be loaded
        commandsName --- name of the Command or list of Commands
    \nOptional Arguements:\n
        package --- name of the package to which filename belongs
    """
    active = 0

    def doit(self, module, commands, package=None, gui=None):
        """Load a command instance with the given alias and gui"""
        if package is None:
            package = self.vf.libraries[0]
            
        if not type(commands)!=types.ListType:
            commands = [commands,]
        
        for command in commands:
            cmd, name, gui = self.getDefaults(package, module, command)
            if cmd is  None:
                print 'Could not add %s.%s.%s'%(package, module, command)
                continue
            self.vf.addCommand( cmd, name, gui )

    def guiCallback(self, event=None):
        if self.active: return
        self.active = 1 
        form = self.showForm('loadCommand', force=1,modal=0,blocking=0)
        form.root.protocol('WM_DELETE_WINDOW',self.Dismiss_cb)

    def package_cb(self, event=None):
        # Get Package.
        ebn = self.cmdForms['loadCommand'].descr.entryByName
        pack = ebn['package']['widget'].get()
        # Get Modules for the new package and update the listChooser.
        names, docs = self.loadModules(pack)
        mw = ebn['Module List']['widget']
        mw.clear()
        for n in names:
            mw.insert('end',n)
        mw.set(names[0])
           
        # Get Commands for the first module and update the listChooser
        cw =  ebn['Command List']['widget']
        cw.clear()
        cmds = self.getModuleCmds(modName=names[0],
                                  package=pack)
        if cmds==None:
           return
        for cmd in map(lambda x: x[0],cmds):
            cw.insert('end', cmd)
        

    def Dismiss_cb(self):
        self.cmdForms['loadCommand'].withdraw()
        self.active = 0


    def __call__(self, moduleName, commandsName,
                 package=None, gui=None, **kw):
        """None <- loadCommand(moduleName, commandsName, package=None,
        gui=None)
        \nRequired Arguements:\n
        moduleName --- name of the module to be loaded
        commandsName --- name of the Command or list of Commands
    \nOptional Arguements:\n
        package --- name of the package to which filename belongs
        """
        kw['package'] = package
        #kw['gui'] = gui
        #apply(self.doitWrapper, (moduleName, commandsName), kw)
        kw['commands']=commandsName
        apply(self.vf.browseCommands, (moduleName,), kw)


    def getDefaults(self, package, filename, commandName):
        if package is None: _package = filename
        else: _package = "%s.%s"%(package, filename)

        mod = self.vf.tryto(__import__,_package, globals(), locals(),
                            [filename])
        if mod=='ERROR':
            print '\nERROR: Could not load module %s.%s' % (_package,
                                                            filename)
            return None,None,None
        
        for d in mod.commandList:
            if d['name']==commandName:
                break
        if d['name']!=commandName:
            print '\nERROR: command %s not found in module %s.%s\n' % \
                  (commandName, package, filename)
            return None,None,None
            
        return d['cmd'], d['name'], d['gui']


    def loadCmd_cb(self, event=None):
#        c = self.cmdForms['loadCommand'].mf.cget('cursor')
#        self.cmdForms['loadCommand'].mf.configure(cursor='watch')
#        self.cmdForms['loadCommand'].mf.update_idletasks()
        ebn = self.cmdForms['loadCommand'].descr.entryByName
        module = ebn['Module List']['widget'].get()
        commands = ebn['Command List']['widget'].get()
        package = ebn['package']['widget'].get()
        if commands:
            kw = {'package': package}
            #apply(self.doitWrapper, (module, commands), kw)
            kw['commands'] = commands
            apply(self.vf.browseCommands, (module[0],), kw)
            
#        self.cmdForms['loadCommand'].mf.configure(cursor=c)
    def getModuleCmds(self, modName=None, package=None):
        """ Callback method of the module chooser to get the corresponding
        commands: 
        """
        filename = modName
        if package is None: _package = filename
        else: _package = "%s.%s"%(package, filename)
        try:
             mod = __import__(_package,globals(),locals(),['commandList'])   
        except:
            
            self.vf.warningMsg("ERROR: Could not load module %s "%filename)
            return "ERROR"
        if hasattr(mod,"initModule"):
                mod.initModule(self.vf)
        else:
                self.vf.warningMsg("ERROR: Could not load module  %s"%filename) 
                return 
        if not hasattr(mod, 'commandList'):
            cmdEntries = []
        else:    
            cmdsName = map(lambda x: x['name'], mod.commandList)
            cmdsName.sort()
            cmdEntries = map(lambda x: (x,None), cmdsName)
        return cmdEntries


    def modChooser_cb(self, event=None):
        """CallBack method that gets called when clicking on an entry
        of the mocule cjooser."""
        
        ebn = self.cmdForms['loadCommand'].descr.entryByName
        modChooser = ebn['Module List']['widget']
        filename = modChooser.get()[0]
        package = ebn['package']['widget'].get()
        cmdEntries = self.getModuleCmds(modName=filename, package=package)
        cmdChooser = ebn['Command List']['widget']
        cmdChooser.clear()
        #cmdEntries should be a list if there are no commands for a module then getModuleCmds returns None or Error  in that case  cmdEntries is made equal to emptylist 
        if cmdEntries=="ERROR" or cmdEntries==None:
            cmdEntries=[]    
        map(cmdChooser.add, cmdEntries)
        

    def buildFormDescr(self, formName):
        """Create the pulldown menu and Listchooser to let for the
        selection of commands."""
        if not formName == 'loadCommand': return
        ifd = InputFormDescr(title='Load Individual Commands')
        moduleNames, docs = self.loadModules(self.vf.libraries[0])
        moduleNames.sort()
        moduleEntries = map(lambda x: (x, None), moduleNames)
        pname = self.vf.libraries
        for p in pname:
            if '.' in p:
                ind = pname.index(p)
                del pname[ind]
        ifd.append({
            'name':'package',
            'widgetType': Pmw.ComboBox,
            'defaultValue': pname[0],
            'wcfg':{ 'labelpos':'nw', 'label_text':'Package:',
                     'selectioncommand': self.package_cb,
                     'scrolledlist_items':pname
                     },
            'gridcfg':{'columnspan':2,'sticky':'ew', 'padx':2, 'pady':1}
            })
        
     
        ifd.append({'name': 'Module List',
                    'widgetType':ListChooser,
                    'wcfg':{'title':'Choose a module',
                            'entries': moduleEntries,
                            'lbwcfg':{ 'width':25,
                                       'height':10,
                                       'exportselection':0},
                            'command':self.modChooser_cb,
                            },
                    'gridcfg':{'sticky':'ew'}
                    } )

        CmdEntries = []
        ifd.append({'name': 'Command List',
                    'widgetType':ListChooser,
                    'wcfg':{'title':'Choose a command',
                            'mode':'multiple',
                            'entries': CmdEntries,
                            'command':self.loadCmd_cb,
                            'commandEvent':"<Double-Button-1>",
                            'lbwcfg':{'width':25,'height':10,
                                      'exportselection':0}
                           },
                    'gridcfg':{'row':-1,'sticky':'we'}
                    } ) 
                            
        ifd.append({'name': 'Load Command',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Load Command',
                            'bd':6, 'command': self.loadCmd_cb},
                    'gridcfg':{'columnspan':2,'sticky':'ew'},
                    })

        ifd.append({'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Dismiss',
                            'command': self.Dismiss_cb},
                    'gridcfg':{'columnspan':2,'sticky':'ew'}})
        return ifd


class loadMacroCommand(Command):
    """Command to load dynamically macro commands.
    \nPackage : ViewerFramework
    \nModule : basicCommand.py
    \nClass : loadMacroCommand
    \nCommand : loadMacro
    \nSynopsis:\n
        None<---loadMacro(macroName, macroFile,  menuBar='menuRoot',
                 menuButton='Macros', menuEntry=None, cascade=None, **kw)
    """
    active = 0

    def getMacros(self, file):
        """load all macro functions from a given file"""
        names = []
        macros = []
        doc = []
        #if not os.path.exists(file) : return names, macros, doc
        _dir, file = os.path.split(file)
        if file[-3:]=='.py': file = file[:-3]
        import sys
        sys.path.insert(0, _dir)
        m = __import__(file, globals(), locals(), [])
        sys.path = sys.path[1:]
        #m.__dict__['self'] = self.vf
        setattr(m, 'self', self.vf)
        import types
        for key, value in m.__dict__.items():
            if type(value) == types.FunctionType:
                names.append(key)
                macros.append(value)
                doc.append(value.__doc__)
        return names, macros, doc


    def loadMacLib_cb(self, filename):
        """Call back function for 'Open Macro library' button"""
        ebn = self.cmdForms['loadMacro'].descr.entryByName
        ebn['openMacLib']['widget'].button.configure(relief='sunken')
        names, macros, docs = self.getMacros(filename)
        self.macroFile = filename
        self.macNames = names
        self.macMacros = macros
        self.macDoc = docs

        # Get a handle to the listchooser widget
        lc = ebn['macros']['widget']
        lc.clear()
        if len(names) == len(docs):
            entries = map(lambda x, y: (x, y), names, docs)
        else:
            entries = map(lambda x: (x, None), names)
        map(lc.add, entries)
        ebn['openMacLib']['widget'].button.configure(relief='raised')

        # set cascade name to libary Name - "mac"
        w = ebn['cascade']['widget']
        w.delete(0, 'end')
        w.insert(0, os.path.split(filename)[1][:-3])


    def setDefaultEntryName(self, event=None):
        """Call back function for the listchooser showing macros.
        gets the name of the currently selected macro and puts it in the entry
        type in"""
        # enable add button
        ebn = self.cmdForms['loadMacro'].descr.entryByName
        ebn['loadMacro']['widget'].configure(state='normal')

        # put default name into name entry
        val = ebn['macros']['widget'].get()
        w = ebn['menuentry']['widget']
        w.delete(0, 'end')
        w.insert(0, val[0])
        #self.selectedMac = val[0]


    def loadMacro_cb(self, event=None):
        ebn = self.cmdForms['loadMacro'].descr.entryByName
        bar = ebn['menubar']['widget'].get()
        
        menub = ebn['menubutton']['widget'].get()
        name = ebn['menuentry']['widget'].get()
        cascade = ebn['cascade']['widget'].get()
        if cascade=='': cascade=None
        lc = ebn['macros']['widget']
        macNames = lc.get()
        if len(macNames) != 0: macName = macNames[0]
        #macIndex = self.macNames.index(self.selectedMac)
        #macFunc = self.macMacros[macIndex]
        self.doitWrapper(macName, self.macroFile, menuBar=bar,
                         menuButton=menub,
                         menuEntry=name, cascade=cascade)
        
        ###self.addMacro(macFunc, bar, menub, name, cascade)
        ebn['openMacLib']['widget'].button.configure(relief='raised')
    
    def dismiss_cb(self):
        self.cmdForms['loadMacro'].withdraw()
        self.active = 0

    def buildFormDescr(self, formName):
        if not formName=='loadMacro': return None

        ifd = InputFormDescr(title='Load Macros')
        if len(self.vf.libraries) is None:
            modu = __import__('ViewerFramework')
        else:
            modu = __import__(self.vf.libraries[0])

        idir = os.path.split(modu.__file__)[0] + '/Macros'
        if not os.path.exists(idir):
            idir = None
        # 0
        ifd.append({'widgetType':LoadButton,
                    'name':'openMacLib',
                    'wcfg':{'buttonType':Tkinter.Button,
                            'title':'Open Macro Library...',
                            'types':[('Macro Module Library', '*Mac.py'),
                                     ('Any Python Function', '*.py')],
                            'callback':self.loadMacLib_cb,
                            'idir':idir,
                            'widgetwcfg':{'text':'Open Macro Library'}},

                    'gridcfg':{'sticky':'we'}})

        # 1
        ifd.append({'name':'macros',
                    'widgetType':ListChooser,
                    'wcfg':{'title':'Choose a macro',
                            'command':self.setDefaultEntryName,
                            'title':'Choose a macro'},
                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W}} )
        # 2
        ifd.append({'widgetType':Tkinter.Entry,
                    'name':'menubar',
                    'defaultValue':'menuRoot',
                    'wcfg':{'label':'menu bar'}, 
                    'gridcfg':{'sticky':Tkinter.E}
                    })
        # 3
        ifd.append({'widgetType':Tkinter.Entry,
                    'name':'menubutton',
                    'defaultValue':'Macros',
                    'wcfg':{'label':'menu button'}, 
                    'gridcfg':{'sticky':Tkinter.E}
                   })

        # 4
        ifd.append({'widgetType':Tkinter.Entry,
                    'name':'menuentry',
                    'defaultValue':'',
                    'wcfg':{'label':'menu entry'}, 
                    'gridcfg':{'sticky':Tkinter.E}
                    })

        # 5
        ifd.append({'widgetType':Tkinter.Entry,
                    'name':'cascade',
                    'defaultValue':'',
                    'wcfg':{'label':'cascade'}, 
                    'gridcfg':{'sticky':Tkinter.E}
                    })

        # 6
        ifd.append({'name': 'loadMacro',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Load Macro',
                            'bd':6,'command': self.loadMacro_cb},
                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W},
                    })

        # 7
        ifd.append({'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Dismiss',
                            'command': self.dismiss_cb}})

        return ifd
    
    def guiCallback(self, event=None):
        if self.active: return
        self.active = 1
        val = self.showForm("loadMacro", force=1,modal=0,blocking=0)
        ebn = self.cmdForms['loadMacro'].descr.entryByName
        ebn['loadMacro']['widget'].configure(state='disabled')

    def __call__(self, macroName, macroFile,  menuBar='menuRoot',
                 menuButton='Macros', menuEntry=None, cascade=None, **kw):
        """None<---loadMacro(macroName, macroFile,  menuBar='menuRoot',
                 menuButton='Macros', menuEntry=None, cascade=None, **kw)
        """         
        self.doitWrapper(macroName, macroFile, menuBar=menuBar,
                         menuButton=menuButton, menuEntry=menuEntry,
                         cascade=cascade)

    def doit(self, macroName, macroFile, menuBar='menuRoot',
             menuButton='Macros', menuEntry=None, cascade=None):

        if not hasattr(self, 'macroFile') or macroFile != self.macroFile:
            names, macros, docs = self.getMacros(macroFile)
        else:
            names =  self.macNames
            macros = self.macMacros
            docs = self.macDoc
        if len(names) == 0 or len(macros)==0 or len(docs)==0: return
        macIndex = names.index(macroName)
        macro = macros[macIndex]
        
        from VFCommand import Command, CommandGUI
        c = Command(func=macro)
        g = CommandGUI()
        if cascade:
            g.addMenuCommand(menuBar, menuButton, menuEntry,
                             cascadeName=cascade)
        else:
            g.addMenuCommand(menuBar, menuButton, menuEntry)
        self.vf.addCommand(c, macro.__name__, g)

    
    
## class loadMacroCommand(Command):
##     """
##     Command to load dynamically macro commands.
##     Using the Gui the user can open a macro file. The macros available in
##     that file are then displayed in a list chooser. When a macro is selected
##     in the listchooser, its documentation string is deisplayed and a default
##     name for the macro in the viewer is suggested. The user can also specify
##     a menuBar, a menuButton as well as an optional cascade name.
##     """

##     active = 0
##     def getMacros(self, file):
##         """load all macro functions from file"""
##         self.file = file
##         _dir, file = os.path.split(file)
##         if file[-3:]=='.py': file = file[:-3]
##         import sys
##         sys.path.insert(0, _dir)
##         m = __import__(file, globals(), locals(), [])
##         sys.path = sys.path[1:]
##         m.__dict__['self'] = self.vf
##         import types
##         names = []
##         macros = []
##         doc = []
##         for key,value in m.__dict__.items():
##             if type(value)==types.FunctionType:
##                 names.append(key)
##                 macros.append(value)
##                 doc.append(value.__doc__)
##         return names, macros, doc


##     def loadMacLib_cb(self, filename):
##         """Call back function for 'Open Macro library' button"""
##         # self.ifd[0]['widget'] is the 'Open Macro Library' button
##         self.ifd[0]['widget'].configure(relief='sunken')

##         #file = os.path.split(filename)[1][:-3]
##         names, macros, docs = self.getMacros(filename)
##         self.macNames = names
##         self.macMacros = macros
##         self.macDoc = docs
##         # Get a handle to the listchooser widget
##         lc = self.ifd[1]['widget']
##         lc.clear()
##         if len(names) == len(docs):
##             entries = map(lambda x, y: (x, y), names, docs)
##         else:
##             entries = map(lambda x: (x, None), names)
##         map(lc.add, entries)
##         self.ifd[0]['widget'].configure(relief='raised')
##         # set cascade name to libary Name - "mac"
##         w = self.ifd[5]['widget']
##         w.delete(0, 'end')
##         w.insert(0, os.path.split(filename)[1][:-3])


##     def setDefaultEntryName(self, event=None):
##         """Call back function for the listchooser showing macros.
##         gets the name of the currently selected macro and puts it in the entry
##         type in"""
##         # enable add button
##         self.ifd.entryByName['Load Macro']['widget'].configure(state='normal')
##         # put default name into name entry
##         val = self.ifd[1]['widget'].get()
##         w = self.ifd[4]['widget']
##         w.delete(0, 'end')
##         w.insert(0, val[0])
##         self.selectedMac = val[0]
        
##     def addMacro(self, macro, menuBar, menuButton, name, cascade=None):
##         from VFCommand import Command, CommandGUI

##         c = Command(func=macro)
##         g = CommandGUI()
##         if cascade:
##             g.addMenuCommand(menuBar, menuButton, name, cascadeName=cascade)
##         else:
##             g.addMenuCommand(menuBar, menuButton, name)
##         self.vf.addCommand(c, macro.__name__, g)
## ##        g.register(self.vf)
##         self.log(file=self.file, macroName=macro.__name__, menuBar=menuBar,
##                  menuButton=menuButton, name=name, cascade=cascade)


##     def loadMacro_cb(self, event=None):
##         bar = self.ifd[2]['widget'].get()
##         menub = self.ifd[3]['widget'].get()
##         name = self.ifd[4]['widget'].get()
##         cascade = self.ifd[5]['widget'].get()
##         if cascade=='': cascade=None
##         macIndex = self.macNames.index(self.selectedMac)
##         macFunc = self.macMacros[macIndex]
##         self.addMacro(macFunc, bar, menub, name, cascade)
##         self.ifd[0]['widget'].configure(relief='raised')

        
##     def customizeGUI(self):
##         """create the cascade menu for selecting modules to be loaded"""

##         self.selectedMac = ''
##          # create the for descriptor
##         ifd = self.ifd = InputFormDescr(title='Load macro commands')
##         if len(self.vf.libraries) is None:
##             modu = __import__('ViewerFramework')
##         else:
##             modu = __import__(self.vf.libraries[0])
##         idir = os.path.split(modu.__file__)[0] + '/Macros'
##         if not os.path.exists(idir):
##             idir = None

##         ifd.append( {'widgetType':'OpenButton', 'text':'Open Macro library ...',
##                      'types':[('Macro Module Library', '*Mac.py'),
##                               ('Any Python Function', '*.py')],
##                      'idir':idir,
##                      'title':'Open Macro File',
##                      'callback': self.loadMacLib_cb } )
##         ifd.append({'title':'Choose a macro',
##                     'widgetType':ListChooser,
##                     'wcfg':{
##                             'command':self.setDefaultEntryName,
##                             'title':'Choose a macro'},
##                     'gridcfg':{'sticky':Tkinter.E+Tkinter.W}} )

##         ifd.append({'widgetType':Tkinter.Entry,
##                     'defaultValue':'menuRoot',
##                     'wcfg':{'label':'menu bar'}, 
##                     'gridcfg':{'sticky':Tkinter.E}
##                     })
##         ifd.append({'widgetType':Tkinter.Entry,
##                     'defaultValue':'Macros',
##                     'wcfg':{'label':'menu button'}, 
##                     'gridcfg':{'sticky':Tkinter.E}
##                    })
##         ifd.append({'widgetType':Tkinter.Entry,
##                     'defaultValue':'',
##                     'wcfg':{'label':'menu entry'}, 
##                     'gridcfg':{'sticky':Tkinter.E}
##                     })
##         ifd.append({'widgetType':Tkinter.Entry,
##                     'defaultValue':'',
##                     'wcfg':{'label':'cascade'}, 
##                     'gridcfg':{'sticky':Tkinter.E}
##                     })
##         ifd.append({'name': 'Load Macro',
##                     'widgetType':Tkinter.Button,
##                     'text':'Load Macro',
##                     'wcfg':{'bd':6},
##                     'gridcfg':{'sticky':Tkinter.E+Tkinter.W},
##                     'command': self.loadMacro_cb})
##         ifd.append({'widgetType':Tkinter.Button,
##                     'text':'Dismiss',
##                     'command': self.Dismiss_cb})


##     def Dismiss_cb(self):
##         #self.cmdForms['loadMacro'].withdraw()
##         self.ifd.form.destroy()
##         self.active = 0

##     def guiCallback(self, event=None, file=None):
##         if self.active: return
##         self.active = 1
        
        
##         self.customizeGUI()
##         self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)
##         self.ifd.entryByName['Load Macro']['widget'].configure(state='disabled')
##         if file: self.loadMacLib_cb(file)


##     def __call__(self, file=None, macroName=None, menuBar='menuRoot',
##                  menuButton='Macros', name=None, cascade=None):
##         """file=None, macroName=None, menuBar='menuRoot', menuButton='Macros',
## name=None, cascade=None"""
##         if not macroName: self.guiCallback(file=file)
##         else:
##             if file[-3:]=='.py': file = file[:-3]
##             names, macros, docs = self.getMacros(file)
##             i = names.index(macroName)
##             if name==None: name=macroName
##             self.addMacro(macros[i], menuBar, menuButton, name, cascade)



class ShellCommand(Command):
    """Command to show/Hide the Python shell.
    \nPackage : ViewerFramework
    \nModule : basicCommand.py
    \nClass : ShellCommand
    \nCommand : Shell 
    \nSynopsis:\n
        None<---Shell()
    """
    
    def onAddCmdToViewer(self):
        if self.vf.hasGui:
            self.vf.GUI.pyshell.top.protocol('WM_DELETE_WINDOW',
                                             self.vf.Shell.onDestroy)
    
    def show(self):
        self.vf.GUI.pyshell.top.deiconify()

    def hide(self):
        self.vf.GUI.pyshell.top.withdraw()

    def __call__(self, *args):
        """None<---Shell()
        """
        if args[0]:
            self.show()
            self.vf.GUI.toolbarCheckbuttons['Shell']['Variable'].set(1)
        else:
            self.hide()
            self.vf.GUI.toolbarCheckbuttons['Shell']['Variable'].set(0)
            
    def guiCallback(self):
        on = self.vf.GUI.toolbarCheckbuttons['Shell']['Variable'].get()
        if on: self.show()
        else: self.hide()

    def onDestroy(self):
        self.vf.GUI.toolbarCheckbuttons['Shell']['Variable'].set(0)
        self.hide()

ShellCommandGUI = CommandGUI()
ShellCommandGUI.addToolBar('Shell', icon1='PyShell.gif', 
                             balloonhelp='Python IDLE Shell', index=1)
        
        
class SaveSessionCommand(Command):
    """Command to allow the user to save the session as it is in a file.
    It logs all the transformation.
    \nPackage : Pmv
    \nModule : customizationCommands.py
    \nClass : SaveSessionCommand
    """


    def logString(self, *args, **kw):
        """return None as log string as we don't want to log this
"""
        pass


    def guiCallback(self, event=None):
        ### FIXME all the logs should be in a stack and not in a file.
        if self.vf.logMode == 'no':
            self.vf.warningMsg("No log information because logMode was set to no.")
            return
        newfile = self.vf.askFileSave(types = [
            ('Pmv sesion files', '*.psf'),
            ('all files', '*.py')],
                                      title = 'Save Session in File:')
        if not newfile is None:
            self.doitWrapper(newfile, redraw=0)


    def doit(self, filename):
        #print "SaveSessionCommand.doit"
        ext = os.path.splitext(filename)[1].lower()
        if ext=='.psf':
            self.vf.saveFullSession(filename)
        else:
            import shutil
            # get the current log.
            if hasattr(self.vf, 'logAllFile'):
                logFileName = self.vf.logAllFile.name
                self.vf.logAllFile.close()
                if filename!=logFileName:
                    shutil.copy(logFileName, filename)
                self.vf.logAllFile = open(logFileName,'a')
            # Add to it the transformation log.
            logFile = open(filename,'a')
            vi = self.vf.GUI.VIEWER
            code = vi.getViewerStateDefinitionCode('self.GUI.VIEWER')
            code.extend( vi.getObjectsStateDefinitionCode('self.GUI.VIEWER') )

            if code:
                for line in code:
                    logFile.write(line)
            if vi.GUI.contourTk.get():
                controlpoints=vi.GUI.curvetool.getControlPoints()
                sensitivity=vi.GUI.d1scalewheel.get()
                logFile.write("self.GUI.VIEWER.GUI.curvetool.setControlPoints(%s)" %controlpoints)
                logFile.write("\n")
                logFile.write("self.GUI.VIEWER.GUI.curvetool.setSensitivity(%s)" %sensitivity)

            #sceneLog = self.vf.Exit.logScene()
            #for l in sceneLog:
            #    l1 = l+'\n'
            #    logFile.write(l1)
            logFile.close()
        if hasattr(self.vf, 'recentFiles'):
            self.vf.recentFiles.add(filename, 'readSourceMolecule')
        

# SaveSessionCommand Command GUI
SaveSessionCommandGUI = CommandGUI()
SaveSessionCommandGUI.addMenuCommand(
    'menuRoot', 'File', 'Current Session', index=2,
    cascadeName='Save', cascadeIndex=2, separatorAboveCascade=1)

SaveSessionCommandGUI.addToolBar('Save', icon1='filesave.gif', 
                             type='ToolBarButton', 
                             balloonhelp='Save Session', index=1)

class ExitCommand(Command):
    """Command to destroy application
    \nPackage : ViewerFramework
    \nModule : basicCommand.py
    \nClass : ExitCommand
    \nCommand : Exit
     \nSynopsis:\n   
        None<---Exit(ask)
        \nask = Flag when set to 1 a form asking you if you really want to quit
              will popup, it will quit directly if set to 0
    """

    def onAddCmdToViewer(self):
        #print "ExitComand.onAddCmdToViewer"
        import warnings
        if self.vf.hasGui:
            self.vf.GUI.ROOT.protocol('WM_DELETE_WINDOW',self.askquit)
            
        
    def logObjectTransformations(self, object):
        warnings.warn( "logObjectTransformations is deprecated",
                        DeprecationWarning, stacklevel=2)
        log = []
        # FIXME won't work with instance matrices
        mat = object.GetMatrix(object)
        import numpy.oldnumeric as Numeric
        log.append("self.transformObject('rotation', '%s', matrix=%s,log=0)"%(object.fullName,tuple(object.rotation)))
        log.append("self.transformObject('translation', '%s', matrix=%s, log=0 )"%(object.fullName, tuple(object.translation)))
        log.append("self.transformObject('scale', '%s', matrix=%s, log=0 )"%(object.fullName,tuple(object.scale)))
        log.append("self.transformObject('pivot', '%s', matrix=%s, log=0 )"%(object.fullName,tuple(object.pivot)))
        return log

    def logObjectMaterial(self, object):
        warnings.warn("logObjectMaterial is deprecated",
                        DeprecationWarning, stacklevel=2)
        log = []
        from opengltk.OpenGL import GL
        log.append("from opengltk.OpenGL import GL")
        mat = object.materials[GL.GL_FRONT]
        log.append("self.setObject('%s', materials=%s, propName='ambi', matBind=%d)" % (object.fullName, repr(mat.prop[0])[6:-5],mat.binding[0]))
        log.append("self.setObject('%s', materials=%s, propName='diff', matBind=%d)" % (object.fullName, repr(mat.prop[1])[6:-5],mat.binding[1]))
        log.append("self.setObject('%s', materials=%s, propName='emis', matBind=%d)" % (object.fullName, repr(mat.prop[2])[6:-5],mat.binding[2]))
        log.append("self.setObject('%s', materials=%s, propName='spec', matBind=%d)" % (object.fullName, repr(mat.prop[3])[6:-5],mat.binding[3]))
        log.append("self.setObject('%s', materials=%s, propName='shini', matBind=%d)" % (object.fullName, repr(mat.prop[4])[6:-5],mat.binding[4]))
        mat = object.materials[GL.GL_BACK]
        log.append("self.setObject('%s', materials=%s, polyFace=GL.GL_BACK,propName='ambi', matBind=%d)" % (object.fullName, repr(mat.prop[0])[6:-5],mat.binding[0]))
        log.append("self.setObject('%s', materials=%s, polyFace=GL.GL_BACK,propName='diff', matBind=%d)" % (object.fullName, repr(mat.prop[1])[6:-5],mat.binding[1]))
        log.append("self.setObject('%s', materials=%s, polyFace=GL.GL_BACK,propName='spec', matBind=%d)" % (object.fullName, repr(mat.prop[2])[6:-5],mat.binding[2]))
        log.append("self.setObject('%s', materials=%s, polyFace=GL.GL_BACK,propName='emis', matBind=%d)" % (object.fullName, repr(mat.prop[3])[6:-5],mat.binding[3]))
        log.append("self.setObject('%s', materials=%s, polyFace=GL.GL_BACK,propName='shini', matBind=%d)" % (object.fullName, repr(mat.prop[4])[6:-5],mat.binding[4]))
        return log

        
    def logCameraTransformations(self, camera):
        warnings.warn("logCameraTransformations is deprecated",
                        DeprecationWarning, stacklevel=2)
        logStr = "self.setCamera('%s', \n"%camera.name
        logStr = logStr + "rotation=(%9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f),\n"%tuple(camera.rotation)
        logStr=logStr + "translation=(%9.3f, %9.3f, %9.3f),\n"%tuple(camera.translation)
        logStr = logStr + "scale=(%9.3f, %9.3f, %9.3f),\n"%tuple(camera.scale)
        logStr = logStr + "pivot=(%9.3f, %9.3f, %9.3f),\n"%tuple(camera.pivot)
        logStr = logStr + "lookAt=(%9.3f, %9.3f, %9.3f),\n"%tuple(camera.lookAt)
        logStr = logStr + "lookFrom=(%9.3f, %9.3f, %9.3f),\n"%tuple(camera.lookFrom)
        logStr = logStr + "direction=(%9.3f, %9.3f, %9.3f))"%tuple(camera.direction)
        return logStr+'\n'

    def logCameraProp(self, camera):
        warnings.warn("logCameraProp is deprecated",
                        DeprecationWarning, stacklevel=2)
        logStr = "self.setCamera('%s', \n"%camera.name
        logStr = logStr + "width=%d, height=%d, rootx=%d, rooty=%d,"%\
                 (camera.width, camera.height, camera.rootx, camera.rooty)
        logStr = logStr + "fov=%f, near=%f, far=%f,"%\
                 (camera.fovy, camera.near, camera.far)
        logStr = logStr + "color=(%6.3f,%6.3f,%6.3f,%6.3f))"%\
                 tuple(camera.backgroundColor)
        return logStr+'\n'
    

    def logLightTransformations(self, light):
        warnings.warn("logLightTransformations is deprecated",
                        DeprecationWarning, stacklevel=2)
        logStr = "self.setLight('%s', \n"%light.name
        logStr = logStr + "rotation=(%9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f),\n"%tuple(light.rotation)
        logStr = logStr + "translation=(%9.3f, %9.3f, %9.3f),\n"%tuple(light.translation)
        logStr = logStr + "scale=(%9.3f, %9.3f, %9.3f),\n"%tuple(light.scale)
        logStr = logStr + "pivot=(%9.3f, %9.3f, %9.3f),\n"%tuple(light.pivot)
        logStr = logStr + "direction=(%9.3f,%9.3f,%9.3f,%9.3f))"%tuple(light.direction)
        return logStr+'\n'


    def logLightProp(self, light):
        warnings.warn("logLightProp is deprecated",
                        DeprecationWarning, stacklevel=2)
        logStr = "self.setLight('%s', \n"%light.name
        logStr = logStr + "enable=%d, visible=%d, length=%f,\n"%\
                 (light.enabled, light.visible, light.length)
        logStr = logStr + "ambient=(%6.3f,%6.3f,%6.3f,%6.3f),\n"%\
                 tuple(light.ambient)
        logStr = logStr + "specular=(%6.3f,%6.3f,%6.3f,%6.3f),\n"%\
                 tuple(light.specular)
        logStr = logStr + "diffuse=(%6.3f,%6.3f,%6.3f,%6.3f))\n"%\
                 tuple(light.diffuse)
        return logStr+'\n'
    

    def logClipTransformations(self, clip):
        warnings.warn("logClipTransformations is deprecated",
                        DeprecationWarning, stacklevel=2)
        logStr = "self.setClip('%s', \n"%clip.name
        logStr = logStr + "rotation=(%9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f, %9.3f),\n"%tuple(clip.rotation)
        logStr = logStr + "translation=(%9.3f, %9.3f, %9.3f),\n"%tuple(clip.translation)
        logStr = logStr + "scale=(%9.3f, %9.3f, %9.3f),\n"%tuple(clip.scale)
        logStr = logStr + "pivot=(%9.3f, %9.3f, %9.3f))\n"%tuple(clip.pivot)
        return logStr+'\n'


    def logClipProp(self, clip):
        warnings.warn("logClipProp is deprecated",
                        DeprecationWarning, stacklevel=2)
        logStr = "self.setClip('%s', \n"%clip.name
        logStr = logStr + "visible=%d, lineWidth=%f,\n"%\
                 (clip.visible, clip.lineWidth)
        logStr = logStr + "color=(%6.3f,%6.3f,%6.3f,%6.3f))\n"%\
                 tuple(clip.color)
        return logStr+'\n'


    def logAddClipPlanes(self, object):
        warnings.warn("logAddClipPlanes is deprecated",
                        DeprecationWarning, stacklevel=2)
        log = []
        for c in object.clipP:
            log.append("self.addClipPlane('%s','%s', %d, %d)\n"%\
                       (object.fullName, c.name, object.clipSide[c.num], 0))
        for c in object.clipPI:
            log.append("self.addClipPlane('%s','%s', %d, %d)\n"%\
                       (object.fullName, c.name, object.clipSide[c.num], 1))
        return log
    
               
    def logScene(self):
        warnings.warn("logScene is deprecated",
                        DeprecationWarning, stacklevel=2)
        log = []
        vi = self.vf.GUI.VIEWER
        for c in vi.cameras:
            if c._modified:
                log.append(self.logCameraTransformations(c))
                log.append(self.logCameraProp(c))
            
        for l in vi.lights:
            if l._modified:
                log.append(self.logLightTransformations(l))
                log.append(self.logLightProp(l))
            
        for c in vi.clipP:
            if c._modified:
                log.append(self.logClipTransformations(c))
                log.append(self.logClipProp(c))
                
        root = self.vf.GUI.VIEWER.rootObject
        for o in root.AllObjects():
            if not o.transformIsIdentity():
                log.extend(self.logObjectTransformations(o))
            if o._modified:
                log.extend(self.logAddClipPlanes(o))
                log.extend(self.logObjectMaterial(o))
        # Trigger a Viewer Redraw at the end.
        log.append("self.GUI.VIEWER.Redraw()")
        return log

    def savePerspective(self):
        if self.vf.resourceFile:
            rcFile = os.path.join(os.path.split(self.vf.resourceFile)[0], "perspective")
        else:
            rcFolder = getResourceFolderWithVersion()
            rcFile = os.path.join(rcFolder, "ViewerFramework", "perspective")
        try:
            rcFile = open(rcFile, 'w')
        except Exception, inst: #to avoid "IOError: [Errno 116] Stale NFS file handle" error message when running the tests 
            return
        
        if self.vf.GUI.floatCamVariable.get():
            rcFile.write("self.GUI.floatCamera()\n")
            geom = self.vf.GUI.vwrCanvasFloating.geometry()
            dum,x0,y0 = geom.split('+')
            w,h = [int(x) for x in dum.split('x')]            
            rcFile.write("self.setCameraSize(%s, %s,  xoffset=%s, yoffset=%s)\n"%(w,h,x0,y0))
        xywh = self.vf.GUI.getGeom()
        #make sure that xywh are within screen coordinates
        if xywh[0]+xywh[2] > self.vf.GUI.ROOT.winfo_screenwidth() or\
            xywh[1]+xywh[3] > self.vf.GUI.ROOT.winfo_screenheight():
            rcFile.write("#"+str(xywh)+"\n")
        else:
            rcFile.write("self.GUI.setGeom"+str(xywh)+"\n") 
#        txt = self.vf.GUI.MESSAGE_BOX.tx.get().split("\n")
#        if len(txt) > 5:
#            txt = txt[5:]
#        linesToWrite = []
#        for line in txt:
#            if line.startswith("self.browseCommands"):
#                linesToWrite.append(line)
#        linesToWrite = set(linesToWrite)
#        for line in linesToWrite:
#            line = line.replace('log=0','log=1')
#            rcFile.write(line)
#            rcFile.write("\n") 
        rcFile.close()


    def __call__(self, ask, **kw):
        """None <- Exit(ask, **kw)
        \nask = Flag when set to 1 a form asking you if you really want to quit
              will popup, it will quit directly if set to 0.
        """
        kw['redraw'] = 0
        kw['log'] = 0
        kw['busyIdle'] = 0
        kw['setupUndo'] = 0
        
        apply(self.doitWrapper, (ask,),kw)

    
    def doit(self, ask):
        #print "ExitComand.quit_cb"
        logPref = self.vf.userpref['Transformation Logging']['value']
        if logPref == 'continuous':
            if hasattr(self.vf.GUI,'pendingLog') and self.vf.GUI.pendingLog:
                self.vf.log(self.vf.GUI.pendingLog[-1])

        if self.vf.userpref.has_key('Save Perspective on Exit'):
            logPerspective = self.vf.userpref['Save Perspective on Exit']['value']
            if logPerspective == 'yes':
                self.savePerspective()
        elif logPref == 'final':
            #changed 10/24/2005-RH
            ##code = self.logScene()
            #vi = self.vf.GUI.VIEWER
            #code = vi.getViewerStateDefinitionCode('self.GUI.VIEWER')
            #code.extend( vi.getObjectsStateDefinitionCode('self.GUI.VIEWER') )
            #if code:
            #    for line in code:
            #        self.vf.log(line)
            if hasattr(self.vf, 'logAllFile'):
                self.vf.saveSession(self.vf.logAllFile.name)

        if ask:
            ##  from ViewerFramework.gui import InputFormDescr
#            from mglutil.gui.InputForm.Tk.gui import InputFormDescr
#            self.idf = InputFormDescr(title='Do you wish to Quit?')
#            self.idf.append({'widgetType':Tkinter.Button,
#                        'wcfg':{'text':'QUIT',
#                                'width':10,
#                                'command':self.quit_cb},
#                        'gridcfg':{'sticky':'we'}})
#            
#            self.idf.append({'widgetType':Tkinter.Button,
#                        'wcfg':{'text':'CANCEL',
#                                'width':10,
#                                'command':self.cancel_cb},
#                        'gridcfg':{'sticky':'we', 'row':-1}})
#            val = self.vf.getUserInput(self.idf, modal=1, blocking=0,
#                                       okcancel=0)
            self.vf.GUI.ROOT.after(10,self.askquit) 
        else:
            self.quit_cb()


    def quit_cb(self):
        #print "ExitComand.quit_cb"
        self.vf.GUI.softquit_cb()


    def cancel_cb(self):
        form = self.idf.form
        form.root.destroy()
        return
        
    def guiCallback(self):
        #print "ExitComand.guiCallback"
        self.doitWrapper(1, redraw=0, log=0)

    def askquit(self):
        #print "ExitComand.askquit"
            import tkMessageBox
            ok = tkMessageBox.askokcancel("Quit?","Do you Wish to Quit?")
            if ok:
                if hasattr(self.vf, 'openedSessions'):
                    import shutil
                    for folder in self.vf.openedSessions:
                        print 'removing session directory', folder
                        shutil.rmtree(folder)
                self.afterDoit = None
                self.vf.GUI.ROOT.after(10,self.vf.GUI.quit_cb)



class customAnimationCommand(Command):
    """Command to start Custom Animation notebook widget
    """

    def __init__(self, func=None):
        Command.__init__(self, func)
        self.root = None
        self.animNB = None
        
    def guiCallback(self):
        self.startCustomAnim_cb()


    def __call__(self, **kw):
        """None <- customAnimation"""
        add = kw.get('add', None)
        if add is None:
            add = 1
        else: assert add in (0, 1)
        if self.vf.GUI.toolbarCheckbuttons.has_key('customAnimation'):
            self.vf.GUI.toolbarCheckbuttons['customAnimation']['Variable'].set(add)
        self.startCustomAnim_cb()


    def startCustomAnim_cb(self):
        on = self.vf.GUI.toolbarCheckbuttons['customAnimation']['Variable'].get()
        if on:
            if not self.animNB:
                from Pmv.scenarioInterface.animationGUI import AnimationNotebook
                self.root = Tkinter.Toplevel()
                self.root.title('Custom Animation')
                self.root.protocol("WM_DELETE_WINDOW", self.hide_cb)
                vi = self.vf.GUI.VIEWER
                self.animNB = AnimationNotebook(self.vf, self.root)
            else:
                self.show_cb()
        else:
            self.hide_cb()

    def hide_cb(self):
        if self.root:
            self.root.withdraw()
            self.vf.GUI.toolbarCheckbuttons['customAnimation']['Variable'].set(0) 

    def show_cb(self, event=None):
        if self.root:
            self.root.deiconify()
            self.vf.GUI.toolbarCheckbuttons['customAnimation']['Variable'].set(1)


    def onAddCmdToViewer(self):
        if self.vf.hasGui:

            # add a page for scenario
            page = self.scenarioMaster = self.vf.GUI.toolsNoteBook.add("AniMol")

            from Pmv.scenarioInterface.animationGUI import AnimationNotebook
            self.animNB = AnimationNotebook(self.vf, page)

            button = self.vf.GUI.toolsNoteBook.tab(1)
            button.configure(command=self.adjustWidth)
            
    def adjustWidth(self):
        self.vf.GUI.toolsNoteBook.selectpage(1)
        self.vf.GUI.workspace.configurepane('ToolsNoteBook',size=self.animNB.master.winfo_width())    

