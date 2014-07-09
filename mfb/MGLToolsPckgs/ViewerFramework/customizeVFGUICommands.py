#############################################################################
#
# Author: Ruth HUEY, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/ViewerFramework/customizeVFGUICommands.py,v 1.30.2.1 2011/08/18 18:57:45 sanner Exp $
#
# $Id: customizeVFGUICommands.py,v 1.30.2.1 2011/08/18 18:57:45 sanner Exp $
#


"""
This Module implements commands 
    to change the appearance of the ViewerFrameworkGUI
 
"""
from ViewerFramework.VFCommand import CommandGUI, Command
##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.util.callback import CallBackFunction
from mglutil.util.misc import ensureFontCase
import types, string, Tkinter, Pmw, sys, os

class HideGUICommand(Command):
    """Allow to Hide the  ViewerFrameworkGUI at any time
    \nPackage : Pmv
    \nModule : customizeVFGUICommands
    \nClass : HideGUICommand
    \nCommand : ShowHideGUI
    \nSynopsis:\n
    None <- ShowHideGUI( **kw)
    """
    def __call__(self, **kw):
        """ None <- ShowHideGUI( **kw)
        """
        if not kw.has_key('redraw'):
            kw['redraw']=0
        apply(self.doitWrapper, (), kw)


    def doit(self):
        # don't do anything if the GUI is already not visible.
        if self.vf.hasGui and self.vf.guiVisible == 1:
            # widthdraw the ViewerFramework GUI
            self.vf.GUI.ROOT.withdraw()
            # set the guiVisile flag to 0
            self.vf.guiVisible=0
            if self.vf.withShell:
                self.vf.GUI.pyshell.top.deiconify()
            
##              # Save the pyShell stdout and redirect it to the main Python
##              # interpreter only works if the main interpreter has been
##              # started in a interactive mode.
##              self.vf.pyShellstdout = sys.stdout
##              sys.stdout = sys.__stdout__

##              # Save the pyShell stdin and redirect it to the main Python
##              # interpreter only works if the main interpreter has been
##              # started in a interactive mode.
##              self.vf.pyShellstdin = sys.stdin
##              sys.stdin = sys.__stdin__

##              # Save the pyShell stderr and redirect it to the main Python
##              # interpreter only works if the main interpreter has been
##              # started in a interactive mode.
##              self.vf.pyShellstderr = sys.stderr
##              sys.stderr = sys.__stderr__
            

# HideGUI command GUI.
HideGUI = CommandGUI()
HideGUI.addMenuCommand('menuRoot', 'File', 'Hide VF GUI...',
                       cascadeName='Preferences')

class ShowGUICommand(Command):
    """Allow to show the ViewerFrameworkGUI at any time
    \nPackage : Pmv
    \nModule : customizeVFGUICommands
    \nClass : ShowGUICommand
    \nCommand : ShowGUI
    \nSynopsis:\n 
    None <- ShowGUI(**kw)
    """

    def __call__(self,**kw):
        """ None <- ShowGUI(**kw)
        """
        if not kw.has_key('redraw'):
            kw['redraw']=1
        apply(self.doitWrapper, (), kw)

    def doit(self):
        if self.vf.hasGui and self.vf.guiVisible == 0 :
            if self.vf.withShell:
                # Hide the Pyshell
                self.vf.GUI.pyshell.top.withdraw()
            # Make the ViewerFramework GUI visible
            self.vf.GUI.ROOT.deiconify()
            # Set the guiVisible flag to 1
            self.vf.guiVisible=1
##              # redirect the stdout, stdin and stderr to the pyShell
##              sys.stdout = self.vf.pyShellstdout
##              sys.stdin = self.vf.pyShellstdin
##              sys.stderr = self.vf.pyShellstderr
##              #self.vf.GUI.ROOT.mainloop()
            
class BindActionToMouse(Command):


    def __init__(self, func=None):
        Command.__init__(self, func)
        self.forwhat = 'Object'


    def setupUndoBefore(self, action, buttonNum, modifier='None',
                        actionDict='Object'):
        cam = self.vf.GUI.VIEWER.currentCamera

        # bind action back to its current button and modifier
        value = cam.findButton(action, actionDict)
        if value[0]:
            self.addUndoCall((action, value[0], value[1], actionDict),
                             {}, self.name)

        # restore action that will be overwritten
        oldaction = cam.mouseButtonActions[actionDict][buttonNum][modifier]
        self.addUndoCall((oldaction, buttonNum, modifier, actionDict),
                         {}, self.name)


    def doit(self, action, buttonNum, modifier='None', actionDict='Object'):
        c = self.vf.GUI.VIEWER.currentCamera
        c.bindActionToMouseButton(action, buttonNum, modifier=modifier,
                                  actionDict=actionDict)


    def __call__(self, action, buttonNum, modifier='None', actionDict='Object',
                 **kw):
        """None <- bindAction(action, buttonNum, modifier='None', actionDict='Object')
        bind an action to a given mouse button for the current camera
        action can be any of ['None', 'picking', 'rotation', 'scale',
                    'XYtranslation', 'Ztranslation']
        modifier can be any of ['None', 'Shift', 'Control', 'Alt', 'Meta']
        actionDict can be anu of ['Object', 'Camera', 'Clip', 'Light',
                    'Texture', 'Scissor']
        'picking' action is always assigned for all modifiers"""

        assert buttonNum in (1,2,3)
        cam = self.vf.GUI.VIEWER.currentCamera
        assert modifier in cam.mouseButtonModifiers
        assert action in cam.actions[actionDict].keys()
        kw['modifier'] = modifier
        kw['actionDict'] = actionDict
        apply( self.doitWrapper, (action, buttonNum,), kw )
        self.forwhat = actionDict
        

    def guiCallback(self, event=None):
        self.ifd = InputFormDescr("Bind Actions to Mouse Buttons!")
        # create modifier dropDown combo box
        
        cam = self.vf.GUI.VIEWER.currentCamera
        self.ifd.append({
            'name':'forwhat',
            'widgetType': Pmw.ComboBox,
            'defaultValue': 'Object',
            'wcfg':{ 'labelpos':'nw', 'label_text':'bindings for:',
                     'selectioncommand': self.binding_cb,
                     'scrolledlist_items':['Object', 'Insert2d', 'Camera', 'Clip', 'Light',
                                           'Texture', 'Scissor']},
            'gridcfg':{'sticky':'ew', 'padx':2, 'pady':1}
            })
        self.ifd.append({
            'name':'buttonNum',
            'widgetType': Pmw.ComboBox,
            'defaultValue': '1',
            'wcfg':{ 'labelpos':'nw', 'label_text':'mouse Button Number:',
                     'scrolledlist_items':['1','2','3']},
            'gridcfg':{'sticky':'ew', 'padx':2, 'pady':1}
            })
        self.ifd.append({
            'name':'action',
            'widgetType': Pmw.ComboBox,
            'defaultValue': 'None',
            'wcfg':{ 'labelpos':'nw', 'label_text':'Action:',
                     'selectioncommand': self.actionSet_cb,
                     'scrolledlist_items':cam.actions[self.forwhat].keys()},
            'gridcfg':{'sticky':'ew', 'padx':2, 'pady':1}
            })
        self.ifd.append({
            'name':'modifier',
            'widgetType': Pmw.ComboBox,
            'defaultValue': 'None',
            'wcfg':{ 'labelpos':'nw', 'label_text':'keyboard modifier:',
                     'scrolledlist_items':cam.mouseButtonModifiers},
            'gridcfg':{'sticky':'ew', 'padx':2, 'pady':1}
            })
        self.ifd.append({
            'name':'set',
            'widgetType': Tkinter.Button,
            'wcfg':{'text':'Set', 'command':self.set_cb, },
            'gridcfg':{'sticky':'ew', 'padx':2, 'pady':1}
            })
        self.ifd.append({'widgetType':Tkinter.Button,
                         'name':'dismiss',
                         'wcfg':{'text':'dismiss',
                                 'command':self.dismiss_cb},
                         'gridcfg':{'sticky':'sew'}
                             })
        self.vf.getUserInput(self.ifd, modal=0, blocking=0)


    def binding_cb(self, event=None):
        self.forwhat = self.ifd.entryByName['forwhat']['widget'].get()
        c = self.vf.GUI.VIEWER.currentCamera
        w = self.ifd.entryByName['action']['widget']
        w.setlist(c.actions[self.forwhat].keys())


    def actionSet_cb(self, event=None):
        action = self.ifd.entryByName['action']['widget'].get()
        c = self.vf.GUI.VIEWER.currentCamera
        val = c.findButton(action, self.forwhat)
        if val[0]:
            w=self.ifd.entryByName['buttonNum']['widget']
            w.selectitem(str(val[0]), setentry=1)
        if val[1]:
            w=self.ifd.entryByName['modifier']['widget']
            w.selectitem(val[1], setentry=1)
            
    
    def set_cb(self, event=None):
        
        action = self.ifd.entryByName['action']['widget'].get()
        buttonNum = int(self.ifd.entryByName['buttonNum']['widget'].get())
        modifier = self.ifd.entryByName['modifier']['widget'].get()

        apply( self.doitWrapper, (action, buttonNum,),
               {'modifier':modifier, 'actionDict':self.forwhat} )

        
    def dismiss_cb(self, event=None):
        self.ifd.form.destroy()


BindActionToMouseGUI = CommandGUI()
BindActionToMouseGUI.addMenuCommand('menuRoot', 'File',
                                    'Bind Action to Mouse Button ...',
                                    cascadeName='Preferences')


class ChangeFont(Command):
    """ Command to change font of the VFGUI"""

    def getCurrentFont(self):
        currentfont = self.vf.GUI.ROOT.option_get('font', '*')
        # current font is '{family yyyy} size opt' if fontname contains
        # a spaces, else 'family size opt'
        if currentfont[0]=='{':
                family, rest = string.split(currentfont[1:], '}')
                rest = string.split(rest)
        else:
                split = string.split(currentfont)
                family = split[0]
                rest = split[1:]
        if len(rest)==0:
                size = 12
                opt = 'normal'
        elif len(rest)==1:
                size = int(rest[0])
                opt = 'normal'
        else:
                size = int(rest[0])
                opt = rest[1]
        return family, size, opt

    def callbackFunc(self, name, old, new):
        self.doit(new)
        
    def setupUndoBefore(self, newfont):
        font = self.getCurrentFont()
        self.addUndoCall( (font,), {}, self.name )


    def onAddCmdToViewer(self):
        if self.vf.hasGui:
            self.familyVar=Tkinter.StringVar()
            self.sizeVar=Tkinter.IntVar()
            self.styleVar=Tkinter.StringVar()
            self.fontVar=Tkinter.StringVar()
            self.vf.userpref.add( 'Fonts', self.getCurrentFont(),
                           callbackFunc = [self.callbackFunc],
                           validateFunc = self.validateFunc,
                           category="Viewer",
                           doc="""Fonts used for Graphical User Interface. Use File -> Preferences -> "Change Font" to select a new font.""")
            
    def validateFunc(self, font):
        root=self.vf.GUI.ROOT.tk
        familyNames=list(root.splitlist(root.call('font','families')))
        if not type(font) == tuple:
            font = font.split() 
        if len(font) < 3:
            return False
        font0 = ensureFontCase(font[0])
        if font0 in familyNames and font[2] in['normal','bold','bold italic','italic']:
            return True
        else:
            return False
    
    def makeChange(self,wid,newfont):
        try:
            wid.config(font=newfont)
        except :
            pass
        if len(wid.children)==0: return
        for item in wid.children.values():
            self.makeChange(item, newfont)    


    def doit(self, newfont):
        """Allow User to Change GUI's font"""
        self.makeChange(self.vf.GUI.ROOT, newfont)
        self.vf.GUI.ROOT.option_add('*font', newfont)
        #self.lastCmdLog.append(self.logString(newfont,log=0))
        #self.vf.GUI.naturalSize()

    def __call__(self, font, **kw):
        """None <- changeFont(font, **kw)
        font has to be a 3-tuple ('arial', 14, 'normal')
        """
        apply( self.doitWrapper, (font,), kw )

    
    def guiCallback(self):
        #familyNames=[ensureFontCase('times'),ensureFontCase('helvetica'),ensureFontCase('Courier'),'Symbol','Verdana']
        root=self.vf.GUI.ROOT.tk
        familyNames=list(root.splitlist(root.call('font','families')))
        familyNames.sort()
        familyNames.append('from entry')
        sizeNames=[6,8,10,12,14,16,18,20]
        styleNames=['normal','bold','bold italic','italic']
        if self.familyVar.get() not in familyNames: 
                self.familyVar.set(ensureFontCase('helvetica'))
        if int(self.sizeVar.get()) not in sizeNames: 
                self.sizeVar.set('10')
        if self.styleVar.get() not in styleNames: 
                self.styleVar.set(styleNames[0])

        ifd=InputFormDescr(title='Select New Font')
        ifd.append({'widgetType':Pmw.ComboBox,
                    'name':'family',
                    'defaultValue':self.familyVar.get(),
                    'wcfg':{'label_text':'Font Name',
                            'labelpos':'n',
                            'scrolledlist_items': familyNames,
                            'selectioncommand': self.changeSampleFont,
                            },
                    'gridcfg':{'sticky':'w'}})
        ifd.append({'widgetType':Tkinter.Radiobutton,
                'name':'size',
                'listtext':sizeNames,
                'defaultValue':self.sizeVar.get(),
                'command': self.changeSampleOpt,
                'wcfg':{'variable':self.sizeVar},
                'gridcfg':{'sticky':Tkinter.W,'row':0,'column':5}})
        ifd.append({'widgetType':Tkinter.Radiobutton,
                'name':'style',
                'listtext':styleNames,
                'command': self.changeSampleOpt,
                'defaultValue':self.styleVar.get(),
                'wcfg':{'variable':self.styleVar},
                'gridcfg':{'sticky':Tkinter.W,'row':0,'column':6}})
        ifd.append({'widgetType':Tkinter.Entry,
                'wcfg':{ 'textvariable':self.fontVar,
                        'width':60},
                'defaultValue':self.getCurrentFont(),
                'name':'ent',
                'gridcfg':{'sticky':Tkinter.W,'row':11,'column':0,'columnspan':16}})
        ifd.append({'widgetType':Tkinter.Label,
                'name':'sample',
                'wcfg':{ 'text':"""This is a sample of this font 0123456789_!@#$%^&*()\nABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz""",
                        'width':60, 'relief':'ridge',
                         'borderwidth': 3},
                'gridcfg':{'sticky':Tkinter.W,'row':11,'column':0,
                           'columnspan':16}})
        self.ifd = ifd
        val=self.vf.getUserInput(ifd)
        if not val: return
        self.val=val
        font = self.fontVar.get()
        if val['family'][0]=='from entry':
            newfont=val['ent']
            newfont=eval('%s'%val['ent']) # turn tuple repr into objs
            self.fontVar.set(newfont)
        else:
            newfont=(val['family'][0],int(val['size']),val['style'])
        self.doitWrapper(newfont, log=1, redraw=0)
        #self.vf.userpref.saveSingleSetting('Fonts', newfont)

    def changeSampleFont(self, font):
        if font=='from entry':
                return
        self.fontVar.set(font)
        self.changeSampleOpt()


    def changeSampleOpt(self, event=None):
        font = self.fontVar.get()
        newfont=(font ,int(self.sizeVar.get()), self.styleVar.get())
        lab = self.ifd.entryByName['sample']['widget']
        lab.configure(font=newfont)

        

ChangeFontGUI = CommandGUI()
ChangeFontGUI.addMenuCommand('menuRoot', 'File', 'Change Font',
                 cascadeName='Preferences',separatorAbove=1)

class showHideGUI(Command):
    """ Command to change which parts of the VFGUI are visible"""


    def __init__(self, func=None):
        Command.__init__(self, func=func)
        self.tkvarDict = {}
        self.ifd = None
        

    def setupUndoBefore(self, name, onOff):
        self.addUndoCall( (name, not onOff), {}, self.name )


    def getWidget(self, name):
        if hasattr(self.vf.GUI, name): return eval('self.vf.GUI.'+name)
        elif self.vf.GUI.menuBars.has_key(name): return self.vf.GUI.menuBars[name]
        else: return None


    def doit(self, name, onOff):
        w = self.getWidget(name)
        if w is None:
            return
        value = w.winfo_ismapped()
        if value==onOff: return
        # Need to repack the menubars properly
        if onOff==1:
            if name=='mBarFrame':
                w.pack(before=self.vf.GUI.vwrCanvasDocked,
                               fill='x')
            elif name == 'menuRoot':
                m2= self.getWidget("icomBar")
                if m2.winfo_ismapped():
                    w.pack(before=m2,fill='x')
                else:
                    m3 = self.getWidget("Toolbar")
                    if m3.winfo_ismapped():
                        w.pack(before=m3,fill='x')
                    else:
                        w.pack(fill='x')
            elif name == 'Toolbar':
                m2 = self.getWidget("icomBar")
                if m2.winfo_ismapped() :
                    w.pack(after=m2, fill='x')
                else:
                    m3 = self.getWidget("menuRoot")
                    if m3.winfo_ismapped():
                        w.pack(after=m3, fill='x')
                    else:
                        w.pack(fill='x')

            elif name == 'icomBar':
                m2 = self.getWidget("menuRoot")
                m3 = self.getWidget("Toolbar")
                if m2.winfo_ismapped():
                    if m3.winfo_ismapped():
                        w.pack(after=m2, before=m3,  fill='x')
                    else:
                        w.pack(after=m2, fill='x')
                else:
                    if m3.winfo_ismapped():
                        w.pack(before=m3, fill='x')
                    else:
                        w.pack(fill='x')

            elif name=='infoBar':
                w1 = self.getWidget('MESSAGE_BOX')
                if w1.winfo_ismapped():
                    w.pack(before=w1,fill='x')
                else:
                    if self.vf.GUI.vwrCanvasDocked.winfo_ismapped():
                        w1.clear()
                        w.pack(after=self.vf.GUI.vwrCanvasDocked, fill='x')
                    else:
                        w.pack(fill='x')
                        
            elif name=='MESSAGE_BOX':
                w1 = self.getWidget('infoBar')
                #print 'show MESSAGE_BOX'
                text = self.vf.getLog()
                w.clear()
                [w.append(line) for line in text]
                if self.vf.GUI.vwrCanvasDocked.winfo_ismapped():
                    # show MESSAGE BOX when camera is docked
                    
                    w.pack(after=self.vf.GUI.vwrCanvasDocked,fill='x')
                elif w1.winfo_ismapped():
                    w.pack(after=w1,fill='x')
                    self.vf.GUI.naturalSize()
                else:
                    w.pack(fill='x')
                self.vf.GUI.toolbarCheckbuttons['MESSAGE_BOX']['Variable'].set(1)
            else:
                w.pack(fill='x')
        else:
            w.forget()
            if name=='MESSAGE_BOX':
                self.vf.GUI.toolbarCheckbuttons['MESSAGE_BOX']['Variable'].set(0)

        self.vf.GUI.VIEWER.currentCamera.update_idletasks()
        if self.ifd:
            self.tkvarDict[name].set(onOff)


    def __call__(self, name, onOff, **kw):
        """None <- showHideGUI(name, onOff, **kw)
name: 'menuRoot', 'Toolbar', 'infoBar' 'MESSAGE_BOX', 'all', 'allAbove',
'allBelow' or bars that appear in self.GUI.menuBars"""

        if name=='all' or name=='allAbove':
                apply( self.doitWrapper, ('mBarFrame', onOff), kw )
        if name=='all' or name=='allBelow':
                apply( self.doitWrapper, ('MESSAGE_BOX', onOff), kw )
                apply( self.doitWrapper, ('infoBar', onOff), kw )
        else:
                apply( self.doitWrapper, (name, onOff), kw )


    def guiCallback(self):
        ifd=InputFormDescr(title='Show/Hide VFGUI components ')
        for name in ['infoBar', 'MESSAGE_BOX']:
            w = self.getWidget(name)
            var = Tkinter.IntVar()
            self.tkvarDict[name] = var
            cb = CallBackFunction( self.callback, name, var)
            ifd.append({'widgetType':Tkinter.Checkbutton,
                        'name':name,
                        'wcfg':{'text':name, 'command': cb, 'variable':var,},
                        'defaultValue': w.winfo_ismapped(),
                        'gridcfg':{'sticky':Tkinter.W}})

        posy = 0
        for name in self.vf.GUI.menuBars.keys():
            w = self.getWidget(name)
            var = Tkinter.IntVar()
            self.tkvarDict[name] = var
            cb = CallBackFunction( self.callback, name, var)
            ifd.append({'widgetType':Tkinter.Checkbutton,
                        'name':name,
                        'wcfg':{'text':name, 'command': cb, 'variable':var,},
                        'defaultValue':w.winfo_ismapped(),
                        'gridcfg':{'sticky':Tkinter.W,'column':1,'row':posy}})
            posy=posy+1

        ifd.append({'widgetType':Tkinter.Button,
                    'name':'dismiss',
                    'wcfg':{'text':'dismiss', 'command':self.dismiss_cb},
                    'gridcfg':{'columnspan':2},
                    })
        self.ifd = ifd
        val=self.vf.getUserInput(ifd, modal=0)


    def dismiss_cb(self, event=None):
        self.ifd.form.destroy()
        self.ifd = None


    def callback(self, name, var):
        self.doitWrapper(name, var.get())



ChangeVFGUIvisGUI = CommandGUI()
ChangeVFGUIvisGUI.addMenuCommand('menuRoot','File', 'Show/Hide GUI Sections',
                 cascadeName='Preferences')

commandList = [
    {'name':'changeFont','cmd':ChangeFont(),'gui':ChangeFontGUI},
    {'name':'showHideGUI','cmd':showHideGUI(),'gui':ChangeVFGUIvisGUI},
    {'name':'bindAction', 'cmd':BindActionToMouse(),
     'gui':BindActionToMouseGUI},
        {'name':'hideGUI', 'cmd':HideGUICommand(), 'gui':HideGUI},
        {'name':'showGUI', 'cmd':ShowGUICommand(), 'gui':None}
    ]

def initModule(vf):
    
    for dict in commandList:
        vf.addCommand(dict['cmd'],dict['name'],dict['gui'])


        
