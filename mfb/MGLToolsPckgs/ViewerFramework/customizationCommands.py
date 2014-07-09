## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Michel F. SANNER, Sophie Coon
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################
"""
This module implements a set of class to customize a ViewerFramework
application:
    SetUserPreference
    SetOnAddObjectCmds
"""    
    
# $Header: /opt/cvs/python/packages/share1.5/ViewerFramework/customizationCommands.py,v 1.57.2.1 2011/04/08 21:21:21 sargis Exp $
#
#  $Id: customizationCommands.py,v 1.57.2.1 2011/04/08 21:21:21 sargis Exp $
#


from ViewerFramework.VFCommand import Command, CommandGUI
##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.util.packageFilePath import findResourceFile
from mglutil.util.callback import CallBackFunction
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser
import Pmw, Tkinter, types, os
import sys
import warnings
import tkMessageBox

## class SetCmdParam(Command):
##     """ Command providing an GUI for the user to set the parameter to use
##     as default when using the command as interactive commands or
##     setOnAddCmdObj...."""


##     def buildFormDescr(self, formName):
##         if formName=='setParam':
##             cmdNames = filter(lambda x, self = self:
##                              self.vf.commands[x].flag & self.objArgOnly,
##                              self.vf.commands.keys())
##             cmdNames.sort()
##             cmdEntries = map(lambda x: (x, None), cmdNames)
##             idf = InputFormDescr(title='Set default parameters')
##             idf.append({'name':'cmdlist',
##                         'widgetType':ListChooser,
##                         'tooltip':"""list of the commands loaded so far in the
## application which can be applied to the object
## when loaded in the application""",
##                         'wcfg':{'entries':cmdEntries,
##                                 'mode':'single',
##                                 'command':self.showDocString,
##                                 'lbwcfg':{'exportselection':0},
##                                 'title':'Available commands'},
##                         'gridcfg':{'sticky':'wens', 'row':0, 'column':0
##                                    ,'rowspan':3}})
## ##             idf.append({'name':'cmdstring',
## ##                         'widgetType':Pmw.EntryField,
## ##             idf.append({'name':'label',
## ##                         'widgetType'
##             return idf
                        
##     def showDocString(self, event=None):
##         ebn = self.cmdForms['setParam'].descr.entryByName
##         lb = ebn['cmdlist']['widget']
##         cmdName=lb.get()[0]
##         cmdString = self.vf.commands[cmdName].__call__.__doc__
        
##         print 'here', cmdString

##     def guiCallback(self):
##         self.showForm('setParam', modal=0, scrolledFrame=0, blocking=0)

class SetUserPreference(Command):
    """ Command providing a GUI to allow the user to set available userPreference.
    \nPackage : Pmv
    \nModule : customizationCommands.py
    \nClass : SetUserPreference
    \nCommand : setUserPreference
    \nSynopsis:\n
        None <--- setUserPreference(item, kw**)
    """
    def set_cb(self,key):
        """
        Method to set the userPreference to the given new value for the
        current session.
        """
        descr = self.form.descr
        result = filter(lambda x, k  = key: x.has_key('name') \
                        and x['name']== k, descr)
        assert len(result)==1
        value = result[0]['widget'].get()
        self.doitWrapper((key,value), redraw=0)


    def testType(self,value,key):
        """ Method testing the type of the userpreference. the combobox
        returns a string"""
        
        if type(value) is types.TupleType:
            value = value[0]
        if isinstance(self.vf.userpref[key]['value'], types.IntType):
            try:
                value = int(value)
            except:
                value = None
        elif isinstance(self.vf.userpref[key]['value'], types.FloatType):
            try:
                value = float(value)
            except:
                value = None
        return value


    def doit(self, item):
        """ Method taking the tuple (key,value) and set the corresponding
        preference to the given value."""

        if item[0] == 'trapExceptions':
            warnings.warn('trapExceptions user preference is deprecated',
                          DeprecationWarning, stacklevel=2)
            return
        #add other transformation where
        if item[0] == 'warningMsgFormat':
            item = ('Warning Message Format', item[1])

        if not item[0] in self.vf.userpref:
            warnings.warn(item[0]+' user preference is deprecated. Please update your resource files.',
                          DeprecationWarning)
            return
        assert type(item) is types.TupleType and len(item)==2
        logItems = []
        key ,value= item
        value = self.testType(value,key)
        if value is None:
            return
        if self.vf.userpref[key]['value']==value:
            return
        self.vf.userpref.set(key,value)
        #apply(self.log,(item,))

    def __call__(self, item, **kw):
        """None <--- setUserPreference(item, kw**)
        """
        assert type(item) is types.TupleType and len(item)==2
        apply(self.doitWrapper, (item,), kw)

    def dismissForm(self):
        self.form.destroy()

    def dismissSmallForm(self):
        self.smallForm.destroy()


    def info_cb(self, doc):
        """Method providing a gui to display the documentation describing the
        userpreference."""
        tkMessageBox.showinfo("Documentation", doc, parent=self.form.root)

            
    def default_cb(self, key):
        """
        Method that will make the userpref a default meaning it writes a
        log in the .pmvrc if existing and creates one if not, in that case a
        file browser opens and sets it to the given value for the current
        session.."""
        # here should pop up a file browser to allow the user to save 
        self.set_cb(key)
        descr = self.form.descr
        result = filter(lambda x, k  = key: x.has_key('name') \
                        and x['name']== k, descr)
        assert len(result)==1
        value = result[0]['widget'].get()
        value = self.testType(value,key)
        self.vf.userpref.saveSingleSetting(key, value)
        
    def updateGUI(self, name,oldvalue, newvalue):
        """ Callback added to all the userpref so the Gui is updated when
        userpref is modified."""
        if str(self.vf.userpref[name]['value']) != str(oldvalue):
            w = self.form.descr.entryByName[name]['widget']
            #val = str(newvalue)
            if isinstance(w, Pmw.ComboBox):
                w.selectitem(newvalue)
            elif isinstance(w,Pmw.EntryField):
                w.setentry(str(newvalue))


    def guiCallback(self):
        idf = InputFormDescr(title ="Set User Preferences")

        categoryList = ['General']
        for value in self.vf.userpref.values():
            if not value['category'] in categoryList:
                categoryList.append(value['category'])
        
        widgetType = {'widgetType':Pmw.NoteBook,
                                'name':'prefNotebook',
                                'container':{},
                                'wcfg':{'borderwidth':2},
                                'componentcfg':[],
                                'gridcfg':{'sticky':'we'},
                                }
        for item in  categoryList:
            widgetType['container'][item] = "w.page('"+item+"')"
            widgetType['componentcfg'].append({'name':item, 'cfg':{}})
            
        idf.append(widgetType)
        for item in  categoryList:            
            idf.append({'name':item+"Group",
                        'widgetType':Pmw.Group,
                        'parent':item,
                        'container':{item+'Group':'w.interior()'},
                        'wcfg':{'tag_text':item},
                        'gridcfg':{'sticky':'wne'}
                        })        
        for key, value in self.vf.userpref.items():
            if not self.updateGUI in self.vf.userpref[key]['callbackFunc']:
                self.vf.userpref.addCallback(key,self.updateGUI)
            # put a label to have more space between the widget Maybe
            # could replace it by using the options padx and pady.
            group =  value['category']+"Group"
            idf.append({'widgetType':Tkinter.Label,
                        'parent':group,
                        'wcfg':{'text':''},
                        'gridcfg':{'sticky':'we','columnspan':3}})

            if value.has_key('validValues') and value['validValues']:
                idf.append({'widgetType':Pmw.ComboBox,
                            'parent':group,
                            'name':key,
                            'defaultValue':value['value'],
                            'wcfg':{'label_text':key,
                                    'labelpos':'n',
                                    'scrolledlist_items': value['validValues']
                                    },
                            'gridcfg':{'sticky':'wens'}})
            else:
                             
                if value.has_key('validateFunc') and value['validateFunc']:
                    def valid(value, func=value['validateFunc']):
                        test = func(value)
                        if test == 1:
                            return Pmw.OK
                        else:
                            return Pmw.PARTIAL
                    idf.append({'widgetType':Pmw.EntryField,
                                'parent':group,
                                'name':key,
                                'wcfg':{'label_text':key,
                                        'labelpos':'n',
                                        'value': value['value'],
                                        'validate':{'validator':
                                                    valid}},
                                'gridcfg':{'sticky':'wens'}})
                else:
                    idf.append({'widgetType':Pmw.EntryField,
                                'parent':group,
                                'name':key,
                                'wcfg':{'label_text':key,
                                        'labelpos':'n'},
                                'gridcfg':{'sticky':'wens'}})
                    
                    

            idf.append({'widgetType':Tkinter.Button,
                        'parent':group,
                        'wcfg':{'bitmap':'info',
                                'width':50,
                                'height':40,
                                'padx':10,
                                'command':CallBackFunction(self.info_cb,
                                                         value['doc'])},
                        'gridcfg':{'row':-1,'sticky':'wens'}})

            idf.append({'widgetType':Tkinter.Button,
                        'parent':group,
                        'wcfg':{'text':'Make \nDefault',
                                'padx':10,
                                'command':CallBackFunction(self.default_cb,
                                                           key)},
                        'gridcfg':{'row':-1,'sticky':'wens'}})
             
            idf.append({'widgetType':Tkinter.Button,
                        'parent':group,
                        'wcfg':{'text':'Set',
                                'padx':10,
                                'height':2,
                                'width':5,
                                'command':CallBackFunction(self.set_cb,
                                                           key)},
                        'gridcfg':{'row':-1,'sticky':'wens'}})
       
        idf.append({'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Dismiss',
                            'command':self.dismissForm},
                    'gridcfg':{'sticky':'we','columnspan':4}})

        self.form = self.vf.getUserInput(idf, modal=0, blocking=0)


class SetOnAddObjectCmds(Command):
    """Command to specify commands that have to be carried out when an object
    is added to the application. Only the commands that have been loaded so
    far in the application will appear in the GUI. Commands are applied in
    the order they have been selected.
    \nPackage : Pmv
    \nModule : customizationCommands.py
    \nClass : SetOnAddObjectCmds
    """
    def dismissForm(self):
        self.form.destroy()


    def doit(self, cmds):
        """Method that add/remove the command from the onAddObjectCmds list"""
        oldCmds = map(lambda x: x[0], self.vf.onAddObjectCmds)
        newCmds = map(lambda x, vfcommands = self.vf.commands: vfcommands[x],
                      cmds)
        
        map(self.vf.removeOnAddObjectCmd, oldCmds)
        map(self.vf.addOnAddObjectCmd, newCmds)


    def buildFormDescr(self,formName):
        if formName == 'choosecmd':
            cmdNames = filter(lambda x, self = self:
                             self.vf.commands[x].flag & self.objArgOnly,
                             self.vf.commands.keys())
            cmdNames.sort()
            cmdEntries = map(lambda x: (x, None), cmdNames)

            onAddCmds = map(lambda x: x[0], self.vf.onAddObjectCmds)
            cmdToApplyNames = []
            cmdToApplyNames = filter(lambda x, vf=self.vf, onAddCmds=onAddCmds:
                                     vf.commands[x] in onAddCmds,
                                     cmdNames)

            cmdtoapply = map(lambda x: (x, None), cmdToApplyNames)
            idf = InputFormDescr(title ="Cmds called after adding an object")
            idf.append({'name':'cmdlist',
                        'widgetType':ListChooser,
                        'tooltip':"""list of the commands loaded so far in the
application which can be applied to the object
when loaded in the application""",
                        'wcfg':{'entries':cmdEntries,
                                'mode':'extended',
                                'lbwcfg':{'exportselection':0},
                                'title':'Available commands'},
                        'gridcfg':{'sticky':'wens', 'row':0, 'column':0
                                   ,'rowspan':3}})

            idf.append({'name':'add',
                        'widgetType':Tkinter.Button,
                        'tooltip':""" Add the selected command from to the list
of commands to be applied to the object when loaded in the application""",
                        'wcfg':{'text':'>>','command':self.add_cb},
                        'gridcfg':{'row':0,'column':1,'rowspan':3 }})

            idf.append({'name':'cmdtoapply',
                        'widgetType':ListChooser,
                        'tooltip':"""list of the commands the user chose to
apply to the object when loaded in the application""",
                        'wcfg':{'entries':cmdtoapply,
                                'mode':'single',
                                'lbwcfg':{'exportselection':0},
                                'title':'Commands to be applied'},
                        'gridcfg':{'sticky':'we', 
                                   'row':0, 'column':2,'rowspan':3}})

            idf.append({'name':'remove',
                        'widgetType':Tkinter.Button,
                        'tooltip':""" Remove the selected entry from the
commands to be applied to the object when loaded in the application""",
                        'wcfg':{'text':'REMOVE','width':10,
                               'command':self.remove_cb},
                        'gridcfg':{'sticky':'we','row':0, 'column':3}})

            idf.append({'name':'oneup',
                        'widgetType':Tkinter.Button,
                        'tooltip':"""Move the selected entry up one entry""",
                        'wcfg':{'text':'Move up','width':10,
                                'command':self.moveup_cb},
                        'gridcfg':{'sticky':'we','row':1,'column':3}})

            idf.append({'name':'onedown',
                        'widgetType':Tkinter.Button,
                        'tooltip':"""Move the selected entry down one entry""",
                        'wcfg':{'text':'Move down','width':10,
                                'command':self.movedown_cb},
                        'gridcfg':{'sticky':'we','row':2,'column':3}})

            return idf
                       
    def movedown_cb(self):
        ebn = self.cmdForms['choosecmd'].descr.entryByName
        lb2 = ebn['cmdtoapply']['widget']
        sel = lb2.get()
        if not sel: return
        sel = sel[0]
        selIndex = lb2.entries.index((sel,None))
        if selIndex == len(lb2.entries)-1: return
        lb2.remove(sel)
        lb2.insert(selIndex+1, sel)
        lb2.select(sel)

    def moveup_cb(self):
        ebn = self.cmdForms['choosecmd'].descr.entryByName
        lb2 = ebn['cmdtoapply']['widget']
        sel = lb2.get()
        if not sel: return
        sel = sel[0]
        selIndex = lb2.entries.index((sel,None))
        if selIndex == 0: return
        lb2.remove(sel)
        lb2.insert(selIndex-1, sel)
        lb2.select(sel)
        
    def add_cb(self):
        ebn = self.cmdForms['choosecmd'].descr.entryByName
        lb1 = ebn['cmdlist']['widget']
        lb2 = ebn['cmdtoapply']['widget']
        for name in lb1.get():
            if (name,None) in lb2.entries: continue
            lb2.add((name,None))

    def remove_cb(self):
        ebn = self.cmdForms['choosecmd'].descr.entryByName
        lb2 = ebn['cmdtoapply']['widget']
        sel = lb2.get()
        if sel:
            lb2.remove(sel[0])
    
    def guiCallback(self):
        # Need to check if some new commands have been added...
        if self.cmdForms.has_key('choosecmd'):
            cmdNames = filter(lambda x, self = self:
                             self.vf.commands[x].flag & self.objArgOnly,
                             self.vf.commands.keys())
            cmdNames.sort()
            ebn = self.cmdForms['choosecmd'].descr.entryByName
            w = ebn['cmdlist']['widget']
            w.clear()
            w.setlist(map(lambda x: (x, None), cmdNames))

        val = self.showForm('choosecmd', force=0)
        ebn = self.cmdForms['choosecmd'].descr.entryByName
        cmds = map(lambda x: x[0], ebn['cmdtoapply']['widget'].entries)
        self.doitWrapper(cmds)

##class SaveSessionCommand(Command):
##    """Command to allow the user to save the session as it is in a file.
##    It copies the .pmvrc in that file and also log all the transformation.
##    \nPackage : Pmv
##    \nModule : customizationCommands.py
##    \nClass : SaveSessionCommand
##    """
##    def guiCallback(self):
##        ### FIXME all the logs should be in a stack and not in a file.
##        if self.vf.logMode == 'no':
##            self.vf.warningMsg("No log information because logMode was set to no.")
##            return
##        newfile = self.vf.askFileSave(types = [('all files','*.*')],
##                                      title = 'Save Session in File:')
##        if not newfile is None:
##            self.doitWrapper(newfile, redraw=0)

##    def doit(self, filename):
##        import shutil
##        # get the current log.
##        logFileName = self.vf.logAllFile.name
##        self.vf.logAllFile.close()
##        if filename!=logFileName:
##            shutil.copy(logFileName, filename)
##        self.vf.logAllFile = open(logFileName,'a')
##        # Add to it the transformation log.
##        logFile = open(filename,'a')
##        vi = self.vf.GUI.VIEWER
##        code = vi.getViewerStateDefinitionCode('self.GUI.VIEWER')
##        code.extend( vi.getObjectsStateDefinitionCode('self.GUI.VIEWER') )
##        if code:
##            for line in code:
##                logFile.write(line)
##        #sceneLog = self.vf.Exit.logScene()
##        #for l in sceneLog:
##        #    l1 = l+'\n'
##        #    logFile.write(l1)
##        logFile.close()        


class SourceCommand(Command):
    """Command to source a command file
    \nPackage : Pmv
    \nModule : customizationCommands.py
    \nClass : SourceCommand
    \nCommand : source
    \nSynopsis:\n
        None<---source(filename)
    """

    def __init__(self, func=None):
        Command.__init__(self, func)
        self.currentlySourcedFiles = []


    def logString(self, *args, **kw):
        """build and return the log string
"""
        argString, before = self.buildLogArgList(args, kw)
        log = ''
        for l in before:
            log = log + l + '\n'
        f = open(args[0])
        lines = f.readlines()
        f.close()
        for line in lines:
            if line.startswith("if mode=='viewer' or mode=='both'"):
                # we don't want to log the viewer and object state,
                # it will be added at the end of the log anyway
                break
            log += line
        return log


    def doit(self, filename, globalNames=1):
        # if globalNames==1 the objects defined in the file will be
        # visible in the main interpreter

        if filename in self.currentlySourcedFiles:
            print 'WARNING: %s is already being sourced'%filename
            print '         skipping to avoid endless loop'
            return

        if filename.endswith('_pmvrc'):
            llogMode = self.vf.logMode
            self.vf.logMode = 'no'

        self.currentlySourcedFiles.append(filename)

##        # check that this files does not source itself (endless loops)
##        f = open(filename)
##        lines = f.readlines()
##        f.close()
##         import re
##         pat = re.compile('.*source.*'+filename+'.*')
##         for l in lines:
##             if pat.search(l):
##                 self.vf.warningMsg('file %s is sourcing itself. This would lead to an endless loop'%filename)
##                 return 'ERROR'

        # make self know while executing filename
        glob = {'self':self.vf, 'mode':'both'}
        # if we pass loaclDict Vision macros defined explicitely in alog file
        # do not build .. strang scope problem

        try:
            execfile( filename, glob)#, localDict)
        except Exception, e:
            self.currentlySourcedFiles = self.currentlySourcedFiles[:-1]
            import warnings, traceback
            # print the exception
            traceback.print_exc()
            # print a warning
            warnings.warn('the exception reported above occured while sourcing ****  '+filename+'  ****')
            
        self.currentlySourcedFiles = self.currentlySourcedFiles[:-1]
        
        if globalNames:
            # all global objects created in filename are now in glob
            # we remove self and update the interpreter's main dict
            del glob['self']
            sys.modules['__main__'].__dict__.update(glob)

        if filename.endswith('_pmvrc'):
            self.vf.logMode = llogMode


    def __call__(self, filename, **kw):
        """None<---source(filename,**kw)
        """
        apply(self.doitWrapper, (filename,), kw)


    def guiCallback(self, event=None,):
        name = self.vf.__class__.__name__
        file = self.vf.askFileOpen(types=[('%s scripts'%name, '*.py'),
                                          ('Resource file','*.rc'),
                                           ('All Files', '*.*')],
                                          title="read %s script file:"%name)
        if file:
            self.doitWrapper(file, redraw=0)
            if hasattr(self.vf, 'recentFiles'):
                self.vf.recentFiles.add(file, self.name)

# Source Command GUI
SourceGUI = CommandGUI()
SourceGUI.addMenuCommand('menuRoot', 'File', 'Python Scripts',
                         cascadeName='Import', cascadeIndex=1)

## SaveSessionCommand Command GUI
#SaveSessionCommandGUI = CommandGUI()
#SaveSessionCommandGUI.addMenuCommand('menuRoot', 'File',
                                     #'Current Session', cascadeName='Save', index=1)

# SetUserPreference Command GUI
SetUserPreferenceGUI = CommandGUI()
SetUserPreferenceGUI.addMenuCommand('menuRoot', 'File', 'Set...',
                                    cascadeName='Preferences'
                                    )
## # SetCmdParam Command GUI
## SetCmdParamGUI = CommandGUI()
## SetCmdParamGUI.addMenuCommand('menuRoot', 'File', 'Set command parameters',
##                                     cascadeName='Preferences'
##                                     )
# SetOnAddObjectCmds Command GUI
setOnAddObjectCmdsGUI= CommandGUI()
setOnAddObjectCmdsGUI.addMenuCommand('menuRoot', 'File',
                                     "Set Commands to be Applied on Objects",
                                     cascadeName="Preferences")




commandList = [
##     {'name':'setDefaultParam', 'cmd':SetCmdParam(),
##      'gui': SetCmdParamGUI},
    {'name':'setUserPreference', 'cmd':SetUserPreference(),
     'gui': SetUserPreferenceGUI},
    {'name':'setOnAddObjectCommands', 'cmd':SetOnAddObjectCmds(), 
     'gui':setOnAddObjectCmdsGUI},
##    {'name':'saveSession','cmd': SaveSessionCommand(),
##     'gui':SaveSessionCommandGUI},
    {'name':'source', 'cmd':SourceCommand(), 'gui':SourceGUI}
 
    ]

def initModule(viewer):
    for dict in commandList:
        #print 'dict',dict
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
