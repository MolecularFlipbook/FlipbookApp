#############################################################################
#
# Author: Sowjanya Karnati , Michel F Sanner
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################
"""
Module implementing classes to provide documentation on the application
"""


# 
#
# $Id: helpCommands.py,v 1.32.2.3 2011/06/16 19:16:55 sargis Exp $
#


import Tkinter, Pmw,re, os
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser, \
     kbScrolledListBox
from ViewerFramework.VFCommand import Command,CommandGUI
from string import join
global commandslist
import webbrowser,os,sys
from Tkinter import *
from types import StringType
import pickle
from mglutil.util.packageFilePath import getResourceFolder
#from htmlDoc import *
try:
    os.remove('Pmv/BugReport.html')
except OSError:
    pass
VarDict = { }
class mailingListsCommand(Command):
    """Command to show mailing lists of Pmv and Vision.
    \nPackage : Pmv
    \nModule : helpCommands
    \nClass : mailingListsCommand
    \nCommand : mailingListsCommand
    \nSynopsis:\n
        None <--- mailingListsCommand(module, commands=None, package=None, **kw)
    \nRequired Arguements\n:
        module --- name of the module (filename)
    \nOptional Arguements:\n
        commands --- list of cammnds in that module
        \nPackage --- package name to which module belongs
    """
    
        
    def __init__(self, func=None):
        Command.__init__(self, func)
    
    def doit(self, pack, page):
        
        if page == None or pack == None:
            return
        if pack == "Pmv":
            
            if page == "Login Page":
                webbrowser.open_new('http://mgldev.scripps.edu/mailman/listinfo/pmv')
        
            if page == "Archive Page":
                webbrowser.open_new('http://mgldev.scripps.edu/pipermail/pmv')
        if pack == "Vision":
            if page == "Login Page":
                webbrowser.open_new('http://mgldev.scripps.edu/mailman/listinfo/vision')
        
            if page == "Archive Page":
                webbrowser.open_new('http://mgldev.scripps.edu/pipermail/vision')    
        
    
    def __call__(self,pack,page):
        """None <--- mailingListsCommand(pack,page)
        \nRequired Arguements\n:
        pack --- name of the package(Pmv, or Vision)
        \npage ---name of the page(Login or Archive)
        
        """
        if page == None: 
            return
        if type(page) is not StringType or type(pack) is not StringType:
            return "ERROR: pack or page are not string type"
        if  page not in ["Login Page", "Archive Page"]: 
            return "ERROR: Invalid page name"
        if pack not in ["Pmv","Vision"]: 
            return "ERROR: Invalid pack name"
        apply(self.doitWrapper,(pack,page,),{})
        
    def buildFormDescr(self, formName):
        
        if not formName == 'Show MailingLists': 
            return
        idf = InputFormDescr(title='Show MailingLists')
        self.mailinglists_pages=["Login Page","Archive Page"] 
        idf.append({'name':'pmvlist',
                    'widgetType':kbScrolledListBox,
                    'wcfg':{'items':self.mailinglists_pages,
                            'listbox_exportselection':0,
                            'labelpos':'nw',
                            'label_text':'Pmv Mailing List',
                            'selectioncommand':self.mailCmds_cb,
                            'listbox_height':3 ,
                            #'hscrollmode':'dynamic',
                            },
                    'gridcfg':{'sticky':'wesn','columnspan':1}})
        
        idf.append({'name':'visionlist',
                    'widgetType':kbScrolledListBox,
                    'wcfg':{'items':self.mailinglists_pages,
                            'listbox_exportselection':0,
                            'labelpos':'nw',
                            'label_text':'Vision Mailing List',
                            'selectioncommand':self.mailCmds_cb,
                            'listbox_height':3,
                            #'hscrollmode':'dynamic',
                            },
                    'gridcfg':{'sticky':'wesn','columnspan':1}})
        idf.append({'name':'dismiss',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'DISMISS',
                            'command':self.dismiss_cb,
                            },
                    'gridcfg':{'sticky':'ew','columnspan':3}})
        return idf

    def guiCallback(self):
        val = self.showForm('Show MailingLists',force = 1,modal =0,blocking = 0)
        ebn = val.descr.entryByName
            
    
    def dismiss_cb(self, event=None):
        self.cmdForms['Show MailingLists'].withdraw()    
    
    def mailCmds_cb(self):
        ebn = self.cmdForms['Show MailingLists'].descr.entryByName
        c = self.cmdForms['Show MailingLists'].mf.cget('cursor') 
        cmdW1 = ebn['pmvlist']['widget']
        cmdW2 = ebn['visionlist']['widget']
        
        CmdName1 = cmdW1.getcurselection()
        cmdW1.select_clear(0,last=1)
        
        CmdName2 = cmdW2.getcurselection()
        cmdW2.select_clear(0,last=1)
         
        if  len(CmdName1) != 0:
            
            if CmdName1[0] == 'Login Page':
                page = "Login Page"
                pack ="Pmv"
                apply( self.doitWrapper,(pack, page,),{})
        
            if CmdName1[0] == 'Archive Page':
         
                page = "Archive Page"
                pack ="Pmv"
                apply( self.doitWrapper,(pack, page,),{})
            CmdName1 =() 
            
        if  len(CmdName2) != 0:
            
            if CmdName2[0] == 'Login Page':
                page = "Login Page"
                pack = "Vision"
                apply( self.doitWrapper,(pack, page,),{})
         
            if CmdName2[0] == 'Archive Page':
                page = "Archive Page"
                pack = "Vision"
                apply( self.doitWrapper,(pack, page,),{})
            CmdName2 =()
mailingListsCommandGUI = CommandGUI()
mailingListsCommandGUI.addMenuCommand('menuRoot', 'Help',
                              'Mailing List')


class orderModelsCommand(Command):
    """Opens 'http://models.scripps.edu/?source=Pmv' with webbrowser
    \nPackage : Pmv
    \nModule : helpCommands
    \nClass : orderModelsCommand
    \nCommand : orderModelsCommand
    \nSynopsis:\n
        None <--- orderModelsCommand()
    """
    def guiCallback(self, evt=None):
        webbrowser.open_new('http://models.scripps.edu/?source=Pmv')
            
    
orderModelsGUI = CommandGUI()
msg = 'Opens http://models.scripps.edu\n 3D Molecular Model Printing Service.'
from moleculeViewer import ICONPATH
orderModelsGUI.addToolBar('orderModels', icon1='handmolecule.gif',
                          balloonhelp=msg, index=14.,
                          type = 'ToolBarButton', icon_dir=ICONPATH)
                              
orderModelsCommandGUI = CommandGUI()
orderModelsCommandGUI.addMenuCommand(
    'menuRoot', 'File', 'Order Physical Models', after='Save')
#    image=ICONPATH+'/32x32/handmoleculeMenu.gif')
                              
class BugReportCommand(Command):
    
    def __init__(self, func=None):
        Command.__init__(self, func)
        
    def doit(self):
        self.show_upload_page()    
            
    def __call__(self):
        apply(self.doitWrapper,(),{})
    
    
    def buildFormDescr(self, formName):
        
        if not formName == 'BugReport': 
            return
        
        email = Tkinter.StringVar()
        try:#get email from .registration
            old_rc = getResourceFolder()
            regfile = os.path.join(old_rc, ".registration")
            if os.path.exists(regfile):
                form_dict =  pickle.load(open(regfile, 'rb'))
                if form_dict.has_key("Email"):
                    email.set(form_dict['Email'])                
        except:
            pass
        
        idf = InputFormDescr(title='Bug Report')
         
        
    
        
       
        idf.append({'name':'shortdesclabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Summary (one line description)',
                               },
                        'gridcfg':{'sticky':'nw','columnspan':3}})
        
        
        idf.append({'name':'shortdescadd',
                    'widgetType':Pmw.ScrolledText,
                    #'parent':'SHORTDESCGROUP',
                    
                    'label_text':'Summary',
                    'labelpos':'n',
                    'text_padx':20,
                    'text_pady':2,
                    'wcfg':{},
                    'gridcfg':{'sticky':'wesn', 'columnspan':3}})
        idf.append({'name':'desclabel',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':'Description',
                               },
                        'gridcfg':{'sticky':'nw','columnspan':3}})
        
        
        
        idf.append({'name':'descadd',
                    'widgetType':Pmw.ScrolledText,
                    #'parent':'DESCGROUP',
                    'labelpos':'n',
                    'label_text':'Description',
                    'defaultValue':"""Please provide steps to reproduce the bug and any 
other information that would help us in fixing this bug.""",
                    'wcfg':{},
                    'gridcfg':{'sticky':'wesn', 'columnspan':3}})
        
        
        idf.append({'name':'PMVLOGGROUP',
                        'widgetType':Pmw.Group,
                        
                       # 'labelpos':'n',
                        'container':{'PMVLOGGROUP':"w.interior()"},
                        'wcfg':{'tag_text':'Check to attach Pmv Log','tag_pyclass':Tkinter.Checkbutton,'tag_variable':Tkinter.IntVar(),'tag_command':self.showpmvlog_cb},
                        'collapsedsize':0,
                        'gridcfg':{'sticky':'wnse', 'columnspan':3}})
        idf.append({'name':'pmvlogtext',
                    'widgetType':Pmw.ScrolledText,
                    'tag_text':"PmvLog", 
                    'parent':'PMVLOGGROUP',
                    'wcfg':{},
                    'gridcfg':{'sticky':'wesn', 'columnspan':3}})
        
        idf.append({'name':'PDBFILEGROUP',
                        'widgetType':Pmw.Group,
                        'container':{'PDBFILEGROUP':"w.interior()"},
                        'wcfg':{'tag_text':'Attach Files'},
                        'collapsedsize':0,
                        'gridcfg':{'sticky':'wnse', 'columnspan':3}})
       
        
        idf.append({'name':'pdbfileadd',
                    'widgetType':Pmw.ScrolledListBox,
                    'parent':'PDBFILEGROUP',
                    'wcfg':{},
                    'listbox_height':1,
                    'gridcfg':{'sticky':'wesn','columnspan':3,'row':1,'column':0}
                    })
        
        idf.append({'name':'DeleteSelected',
                    'widgetType':Tkinter.Button,
                    'defaultValue':0,
                    'parent':'PDBFILEGROUP',
                    'wcfg':{'text':'Delete Selected Files',
                             'width':38,
                                'state':'disabled', 
                               'command':self.delete_selected_cb,
                               },
                        'gridcfg':{'sticky':'nw','row':2,'column':0,'columnspan':2}})
        idf.append({'name':'AttachMore',
                    'widgetType':Tkinter.Button,
                    'defaultValue':0,
                    'parent':'PDBFILEGROUP',
                    'wcfg':{'text':'Attach File ..',
                             'width':37,  
                               'command':self.attachmore_cb,
                               },
                        'gridcfg':{'sticky':'ne','row':2,'column':1,'columnspan':2,}})
        idf.append({'name':'emailentrylab',
                    'widgetType':Tkinter.Label,
                    
                    'wcfg':{'text':"Email Address (optional). Used to notify important updates about this bug.\n"+
                            "Please register your email at http://mgldev.scripps.edu/bugs before using this form."
                            },
                    'gridcfg':{'sticky':'nw', 'columnspan':3}})
        idf.append({'name':'emailentry',
                    'widgetType':Tkinter.Entry,
                    
                    'wcfg':{'textvariable':email
                            },
                    'gridcfg':{'sticky':'wesn', 'columnspan':3}})
        idf.append({'name':'uploadbutton',
                    'widgetType':Tkinter.Button,
                    'defaultValue':0,
                    'wcfg':{'text':'Submit Bug Report',
                              'width':37, 
                               'command':self.show_upload_page,
                               },
                        'gridcfg':{'sticky':'nw','columnspan':2,'row':9,'column':0,}})
        idf.append({'name':'dismiss',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'DISMISS',
                            'width':38,
                            'command':self.dismiss_cb,
                            },
                    'gridcfg':{'sticky':'ne','columnspan':2,'row':9,'column':1,}})
        
        return idf

    def guiCallback(self):
        val = self.showForm('BugReport',force = 1,modal =0,blocking = 0)
        ebn = val.descr.entryByName
        pdb_group=ebn['PDBFILEGROUP']['widget']
        pdb_group.expand()
        pmvlog_group=ebn['PMVLOGGROUP']['widget']
        pmvlog_group.collapse()
        shortdesc_tx=ebn['shortdescadd']['widget']
        shortdesc_tx.configure(text_height=2)
        desc_tx=ebn['descadd']['widget']
        desc_tx.configure(text_height=8)        
        pdb_addw=ebn['pdbfileadd']['widget']
        pdb_addw.configure(listbox_height=1)
           
        
    def dismiss_cb(self, event=None):
        self.cmdForms['BugReport'].withdraw()
    
    
    def attachmore_cb(self):
        """for attching files"""
        ebn = self.cmdForms['BugReport'].descr.entryByName 
        pdb_group=ebn['PDBFILEGROUP']['widget']
        pdb_addw=ebn['pdbfileadd']['widget']
        pdb_att=ebn['AttachMore']['widget']
        pdb_delw=ebn['DeleteSelected']['widget']
        Filename = self.vf.askFileOpen(parent=pdb_att.winfo_toplevel(), types=[('all files','*')],
                        title="ADDFile")
        if Filename:
            inputfilename = os.path.abspath(Filename)
            files=pdb_addw.get()
            files=list(files)
            files.append(inputfilename)
            pdb_addw.setlist(files)
            pdb_addw.configure(listbox_height=len(files))
            pdb_delw.configure(state="active")
            
        else:
            if len(pdb_addw.get())==0:
                 pdb_delw.configure(state="disabled")    
            pdb_addw.setlist(pdb_addw.get())
            
    
    def delete_selected_cb(self):
        """deletes selected files"""
        ebn = self.cmdForms['BugReport'].descr.entryByName 
        pdb_group=ebn['PDBFILEGROUP']['widget']
        pdb_addw=ebn['pdbfileadd']['widget']
        pdb_delw=ebn['DeleteSelected']['widget']
        files=pdb_addw.get()
        lfiles=list(files)
        selected_files=pdb_addw.getcurselection()
        for s in list(selected_files):
            if s in lfiles:
                lfiles.remove(s)
        pdb_addw.setlist(lfiles)        
        pdb_addw.configure(listbox_height=len(lfiles))        
        if len(pdb_addw.get())==0:
            pdb_delw.configure(state="disabled")
       
    def showpmvlog_cb(self):
        
        ebn = self.cmdForms['BugReport'].descr.entryByName 
        var=ebn['PMVLOGGROUP']['wcfg']['tag_variable'].get()
        pmvlog_group=ebn['PMVLOGGROUP']['widget']
        pmvlog_txtw=ebn['pmvlogtext']['widget']
        if var==0:
            pmvlog_group.collapse()
            message_list = ""
            
        if var==1 :
                pmvlog_group.expand()   
                message_list = self.vf.getLog() 
                pmvlog_txtw.configure(text_height=3) 
                    
        mes =""
        for m in message_list:
            mes=mes+m
        pmvlog_txtw.settext(mes)    
        
        

    def get_description(self):
        ebn = self.cmdForms['BugReport'].descr.entryByName 
        desc_w =ebn['descadd']['widget']
        desc_text = desc_w.get()
        shortdesc_w = ebn['shortdescadd']['widget']

        shortdesc_text =shortdesc_w.get()
        
        VarDict['desc_text'] = desc_text
        VarDict['shortdesc_text'] = shortdesc_text
        email_ent =  ebn['emailentry']['widget'].get()
        VarDict['email_recipient'] = email_ent
        pmvlog_txtw=ebn['pmvlogtext']['widget']
        VarDict['pmvlog'] =  pmvlog_txtw.get()
        pdb_addw=ebn['pdbfileadd']['widget']
        VarDict['attachfile'] = pdb_addw.get() 

    #checking validity of email address
    def validateEmail(self,email):

            if len(email) > 7:
                if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
                    return 1
            return 0
    def show_upload_page(self):
        self.get_description()
         
        sumcont = VarDict['shortdesc_text']
        
        if VarDict.has_key('pmvlog') and len(VarDict['pmvlog'])>0:
            
            fulldesc = VarDict['desc_text']+"\n"+"PMV LOG:"+"\n"+VarDict['pmvlog']
        else:
            fulldesc = VarDict['desc_text']
        
        if len(VarDict['email_recipient'])>1:
            desccont = fulldesc+"\n"+"-by"+" "+VarDict['email_recipient']
        else:
            desccont = fulldesc
        if len(sumcont)<=1 or len(desccont)<=1:
            import tkMessageBox
            ok = tkMessageBox.askokcancel("Input","Please enter summary and description")
            return
        from mglutil.TestUtil import BugReport
        if VarDict.has_key('attachfile'):
            upfile = VarDict['attachfile']
        else:
            upfile=""
        BR=BugReport.BugReportCommand("PMV")
        from Support.version import __version__
        if self.validateEmail(VarDict['email_recipient']):
            idnum = BR.showuploadpage_cb(sumcont,desccont,upfile,
                                         email_ent=VarDict['email_recipient'],
                                         product="MGL Applications",
                                         version=__version__)
        else:
            
            idnum = BR.showuploadpage_cb(sumcont,desccont,upfile,
                                         email_ent="",
                                         product="MGL Applications",
                                         version=__version__)
        
        
        self.dismiss_cb() 
        ####################################
        #Tk message Box
        ####################################
         
        root = Tk()
        t  = Text(root)
        t.pack()
        
        
        def openHLink(event):
            start, end = t.tag_prevrange("hlink",
                               t.index("@%s,%s" % (event.x, event.y)))
            webbrowser.open_new('%s' %t.get(start, end))
            #print "Going to %s..." % t.get(start, end)
            
        def show_hand_cursor(event):
            t.config(cursor="hand2")
            
        def show_arrow_cursor(event):
            t.config(cursor="arrow")
            
        t.tag_configure("hlink", foreground='blue', underline=1)
        t.tag_bind("hlink", "<Button-1>", openHLink)
        t.tag_bind("hlink", "<Enter>", show_hand_cursor)
        t.tag_bind("hlink", "<Leave>", show_arrow_cursor)
                
        t.tag_configure("hlink", )

        try:
            int(idnum)
        except:
            t.insert(END, "Failed to submit bug report\n")
            t.insert(END, "Visit ")
            t.insert(END,"http://mgldev.scripps.edu/bugs","hlink")
            t.insert(END, " to submit this bug report. Thank you.")    
            t.insert(END,"\nControl-click on the link to visit this page\n")
            return
        t.insert(END, "BugReport has been Submitted Successfully\n")
        t.insert(END, "BugId is %s" %idnum)
        t.insert(END,"\nYou can visit Bug at\n")
        t.insert(END,"http://mgldev.scripps.edu/bugs/show_bug.cgi?id=%i" %int(idnum),"hlink")
        t.insert(END,"\nClick on the link to visit this page\n")
        t.insert(END,"\n")
        
        

BugReportCommandGUI = CommandGUI()
BugReportCommandGUI.addMenuCommand('menuRoot', 'Help',
                                   'Report a Bug')

commandList = [
    {'name':'orderModelsCommand','cmd':orderModelsCommand(),'gui':orderModelsCommandGUI},
#    {'name':'orderModelsToolbarCommand','cmd':orderModelsCommand(),'gui':orderModelsGUI},        
    {'name':'mailingListsCommand','cmd':mailingListsCommand(),'gui':mailingListsCommandGUI},
    {'name':'BugReportCommand','cmd':BugReportCommand(),'gui':BugReportCommandGUI},
    ]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])    
