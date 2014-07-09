#############################################################################
#
# Author: Michel F. SANNER
# 
# Copyright: M. Sanner TSRI 2000
#
#############################################################################
"""
Module implementing classes to provide documentation on the application
"""


# $Header: /opt/cvs/python/packages/share1.5/ViewerFramework/helpCommands.py,v 1.19 2010/09/30 18:17:32 sargis Exp $
#
# $Id: helpCommands.py,v 1.19 2010/09/30 18:17:32 sargis Exp $
#

from ViewerFramework.basicCommand import loadCommandCommand
import Tkinter, Pmw, tkFileDialog
##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser, \
     kbScrolledListBox
from ViewerFramework.VFCommand import Command,CommandGUI
from mglutil.util.packageFilePath import findFilePath, findAllPackages, \
     findModulesInPackage
import os
from string import join
global commandslist
import webbrowser
# This should open a particular web page.


class CitationCommand(Command):
    """Command that shows citation information
    \nPackage : Pmv
    \nModule : helpCommands
    \nClass : CitationCommand
    """
    
    def onAddCmdToViewer(self):
        self.citations = {'Pmv':"""
Please acknowledge the use of the PMV software that results
in any published work, including scientific papers, films
and videotapes, by citing the following reference:
Michel F. Sanner. Python: A Programming Language for Software
Integration and Development. J. Mol. Graphics Mod., 1999,
Vol 17, February. pp57-61
""",
                         'ADT':"""
Please acknowledge the use of the ADT software that results
in any published work, including scientific papers, films
and videotapes, by citing the following reference:
Michel F. Sanner. Python: A Programming Language for
Software Integration and Development. J. Mol. Graphics
Mod., 1999, Vol 17, February. pp57-61
""",
                         'msms':"""
The MSMS library is used by the Pmv module msmsCommands.
Please acknowledge the use of the MSMS library that results
in any published work, including scientific papers, films
and videotapes, by citing the following reference:
Sanner, M.F., Spehner, J.-C., and Olson, A.J. (1996) Reduced
surface: an efficient way to compute molecular surfaces.
Biopolymers, Vol. 38, (3),305-320.
""",
                         'isocontour':"""
The isocontour library is used by the Pmv module ....
Please acknowledge the use of the isocontour library that results
in any published work, including scientific papers, films and
videotapes, by citing the following reference:
Bajaj, C, Pascucci, V., Schikore, D., (1996), Fast IsoContouring
for Improved Interactivity, Proceedings of  ACM Siggraph/IEEE
Symposium on Volume Visualization, ACM Press, 1996, pages 39 - 46,
San Francisco, CA
""",
                         'Vision':"""
Please acknowledge the use of the Vision software that results
in any published work, including scientific papers, films and
videotapes, by citing the following reference:
Michel F. Sanner, Daniel Stoffler and Arthur J. Olson. ViPEr
a Visual Programming Environment for Python. 10th International
Python Conference, February 2002.
""",
                          'PCVolRen':"""
The PCVolRen library is used in the PMV module ....
Please acknowledge the use of the FAST VOLUME RENDERING library
that results in any published work, including scientific papers,
films and videotapes, by citing the following reference:
Bajaj, C, Park, S., Thane, A., (2002), A Parallel Multi-PC
Volume Rendering System, ICES and CS Technical Report, University
of Texas, 2002.
""",
                        'APBS':"""
APBS is used in the Pmv Module.... 
Please acknowledge the use of APBS that results in any published work,
including scientific papers,films and videotapes, by citing the 
following reference:
Baker NA, Sept D, Joseph S, Holst MJ, McCammon JA. Electrostatics 
of nanosystems: application to microtubules and the ribosome. 
/Proc. Natl. Acad. Sci. USA/ *98*, 10037-10041 2001
""",
                        'stride':"""
stride is used in Pmv Module......
Please acknowledge the use of stride that results in any published work,
including scientific papers,films and videotapes, by citing the 
following reference:
Frishman,D & Argos,P. (1995) Knowledge-based secondary structure
assignment. Proteins: structure, function and genetics, 23,
566-579.""",

                        'PROSS':"""
PROSS is used in Pmv for Secondary Structure prediction.
Please acknowledge the use of PROSS that results in any 
published work, including scientific papers,films and 
videotapes, by citing the  following reference:
Srinivasan R, Rose GD. (1999) A physical basis for protein 
secondary structure. Proc. Natl. Acad. Sci. USA  96, 14258-63.
"""

}

    def buildFormDescr(self, formName):
        
        if formName=='chooseCitation':
            idf = InputFormDescr(title="Choose Package")
            pname = self.citations.keys()
            #pname.sort()
            idf.append({'name':'packList',
                        'widgetType':Pmw.ScrolledListBox,
                        'wcfg':{'items':pname,
                                'listbox_exportselection':0,
                                'labelpos':'nw','usehullsize': 1,
                                'hull_width':100,'hull_height':150,
                                'listbox_height':5,
                                 'listbox_width':150,
                                'label_text':'Select a package:',
                                'selectioncommand':self.displayCitation_cb,
                                },
                        'gridcfg':{'sticky':'wesn'}})
            
            idf.append({'name':'citation',
                        'widgetType':Pmw.ScrolledText,
                        'wcfg':{'labelpos':'nw',
                                'text_width':60,
                                'text_height':10},
                        'gridcfg':{'sticky':'wens'}
                        })
            idf.append({'name':'dismiss',
                        'widgetType':Tkinter.Button,
                        'wcfg':{'text':'DISMISS','command':self.dismiss_cb,
                                },
                        'gridcfg':{'sticky':'wens'}})
            return idf
    def dismiss_cb(self):
        if self.cmdForms.has_key('chooseCitation'):
            self.cmdForms['chooseCitation'].withdraw()
        
    def displayCitation_cb(self, event=None):
        ebn = self.cmdForms['chooseCitation'].descr.entryByName
        packW = ebn['packList']['widget']
        packs = packW.getcurselection()
        # Nothing selected
        if len(packs) == 0:
            return
        packName = packs[0]
        if not self.citations.has_key(packName): return
        citation = self.citations[packName]
        citWidget = ebn['citation']['widget']
        citWidget.setvalue(citation)
        
    def guiCallback(self):
        form = self.showForm('chooseCitation', modal=0,blocking=0)
        
citationCommandGUI = CommandGUI()
citationCommandGUI.addMenuCommand('menuRoot', 'Help',
                                  'Citation Information')

class CiteThisSceneCommand(Command):
    """Command that helps to cite references used in a given scene
    \nPackage : Pmv
    \nModule : helpCommands
    \nClass : CiteThisSceneCommand
    """
    
    def buildFormDescr(self, formName):
        if formName=='citationHelp':
            idf = InputFormDescr(title="Choose Package")
            citeKeys = self.vf.showCitation.citations.keys()

            txt = """
 This widget helps you cite the use of appropriate packages in your publication. 
 Based on the information we collected, please cite the following publications:   """ 

            idf.append({'name':'help',
                        'widgetType':Tkinter.Label,
                        'wcfg':{'text':txt,
                                    'justify':Tkinter.LEFT
                                },
                        'gridcfg':{'sticky':'wens', 'columnspan':2}})

            txt = """ADT/PMV/ViewerFramework:
    Michel F. Sanner. Python: A Programming Language for
    Software Integration and Development. J. Mol. Graphics
    Mod., 1999, Vol 17, February. pp57-61
"""
            #this is the part where we find out which packages are used
            MSMS = False
            isocontour = False
            volRen = False
            APBS = False
            PROSS = False
            if hasattr(self.vf, 'Mols'):
                for mol in self.vf.Mols:
                    if 'secondarystructure' in mol.geomContainer.geoms.keys():
                        PROSS = True
                    if 'MSMS-MOL' in mol.geomContainer.geoms.keys():
                        MSMS = True
            for gridName in self.vf.grids3D:
                 if '.potential.dx' in gridName:
                     APBS = True
                 grid = self.vf.grids3D[gridName]
                 if hasattr(grid, 'isoBarNumber') and grid.isoBarNumber > 0:
                     isocontour = True
                 if hasattr(grid, 'volRenGrid'):
                     volRen = True          
            if MSMS:
                txt += """
MSMS:                
    Sanner, M.F., Spehner, J.-C., and Olson, A.J. (1996) Reduced
    surface: an efficient way to compute molecular surfaces.
    Biopolymers, Vol. 38, (3),305-320.               
"""      
            if APBS:
                txt += """
APBS:           
    Baker NA, Sept D, Joseph S, Holst MJ, McCammon JA. Electrostatics 
    of nanosystems: application to microtubules and the ribosome. 
    /Proc. Natl. Acad. Sci. USA/ *98*, 10037-10041 2001 
"""      
            if isocontour:
                txt += """
IsoContour:                
    Bajaj, C, Pascucci, V., Schikore, D., (1996), Fast IsoContouring
    for Improved Interactivity, Proceedings of  ACM Siggraph/IEEE
    Symposium on Volume Visualization, ACM Press, 1996, pages 39 - 46,
    San Francisco, CA      
"""      
            if volRen:
                txt += """
Volume Rendering:           
    Bajaj, C, Park, S., Thane, A., (2002), A Parallel Multi-PC
    Volume Rendering System, ICES and CS Technical Report, University
    of Texas, 2002. 
"""      
            if PROSS:
                txt += """
Secondary Structure:           
    Srinivasan R, Rose GD. (1999) A physical basis for protein 
    secondary structure. Proc. Natl. Acad. Sci. USA  96, 14258-63.
"""      
            idf.append({'name':'citation',
                        'widgetType':Pmw.ScrolledText,
                        'defaultValue':txt,

                        'gridcfg':{'sticky':'wens', 'columnspan':2}
                        })
            
            idf.append({'name':'save',
                        'widgetType':Tkinter.Button,
                        'wcfg':{'text':'Save As','command':self.save,
                                },
                        'gridcfg':{'sticky':'we', 'row':2, 'column':0}})
                        
            idf.append({'name':'dismiss',
                        'widgetType':Tkinter.Button,
                        'wcfg':{'text':'DISMISS','command':self.dismiss_cb,
                                },
                        'gridcfg':{'sticky':'we', 'row':2, 'column':1}})
            return idf
        

    def save(self):
        file = tkFileDialog.asksaveasfilename(parent=self.cmdForms['citationHelp'].f,
                                              filetypes=[('Text files', '.txt'), ('BibTeX files', '.bib'), ],
                                               initialfile="cite.txt",
                                               title="Save file")
        if file:
            if file.endswith('.bib'):
                MSMS = False
                isocontour = False
                volRen = False
                APBS = False
                PROSS = False
                if hasattr(self.vf, 'Mols'):
                    for mol in self.vf.Mols:
                        if 'secondarystructure' in mol.geomContainer.geoms.keys():
                            PROSS = True
                        if 'MSMS-MOL' in mol.geomContainer.geoms.keys():
                            MSMS = True
                        if 'CoarseMolSurface' in mol.geomContainer.geoms.keys():
                            isocontour = True      
                for gridName in self.vf.grids3D:
                     if '.potential.dx' in gridName:
                         APBS = True
                     grid = self.vf.grids3D[gridName]
                     if hasattr(grid, 'isoBarNumber') and grid.isoBarNumber > 0:
                         isocontour = True
                     if hasattr(grid, 'volRenGrid'):
                         volRen = True   
                txt = """
@article{mgltools,
author = {Sanner MF},
title = {Python: A Programming Language for Software Integration and Development},
journal = {J. Mol. Graphics Mod.},
year = {1999},
volume = {17},
pages = {57-61}    
}
"""                                
                if MSMS:
                    txt += """
@article{msms,                    
author = {Sanner MF, Olson AJ, Spehner JC},   
title = {Reduced surface: an efficient way to compute molecular surfaces},
journal = {Biopolymers},
year = {1996},
volume = {38},
pages = {305-320}   
"""
                if APBS:
                    txt += """
@article{apbs,                    
author = {Baker NA, Sept D, Joseph S, Holst MJ, McCammon JA},
title = {Electrostatics of nanosystems: application to microtubules and the ribosome},
journal = {Proc. Natl. Acad. Sci. USA},
year = {2001},
volume = {98},
pages = {10037-10041} 
"""      
                if isocontour:
                    txt += """
@proceedings{isocontour,                    
author = {Bajaj C, Pascucci V, Schikore D},
title = {Fast IsoContouring for Improved Interactivity},
booktitle = {Proceedings of  ACM Siggraph/IEEE Symposium on Volume Visualization},
publisher = {ACM Press},
year = {1996},
pages = {39-46}
"""      

                if volRen:
                    txt += """
@techreport{volren,                
author = {Bajaj C, Park S, Thane A},
title = {A Parallel Multi-PC Volume Rendering System},
institution = {CS & ICES Technical Report, University of Texas},
year = {2002}
"""      
                if PROSS:
                    txt += """
@article{pross,
author = {Srinivasan R, Rose GD},
title = {A physical basis for protein secondary structure},               
journal = {Proc. Natl. Acad. Sci. USA},
year = {1999},
volume = {96},
pages = {14258-14263}
"""                      
                open(file,'w').write(txt)
            else:
                txt = self.cmdForms['citationHelp'].descr.entryByName['citation']['widget'].getvalue()
                open(file,'w').write(txt)
     
        
    def dismiss_cb(self):
        if self.cmdForms.has_key('citationHelp'):
            self.cmdForms['citationHelp'].destroy()
                            
    def guiCallback(self):
        form = self.showForm('citationHelp', okcancel=False, help=False, force=1)
            
CiteThisSceneCommandGUI = CommandGUI()
CiteThisSceneCommandGUI.addMenuCommand('menuRoot', 'Help',
                                  'Cite This Scene')

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
        if type(page) or type(pack) is not StringType:
            return "ERROR: pack or page are string type"
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
                              'MailingList')

class helpCommand(Command):
    """Command to show dynamically either modules or individual commands in the viewer.
    \nPackage : Pmv
    \nModule : helpCommands
    \nClass : helpCommand
    \nCommand : helpCommand
    \nSynopsis:\n
        None <--- helpCommand(module, commands=None, package=None, **kw)
    \nRequired Arguements\n:
        module --- name of the module (filename)
    \nOptional Arguements:\n
        commands --- list of cammnds in that module
        \nPackage --- package name to which module belongs
    """
    def __init__(self, func=None):
        Command.__init__(self, func)
        self.var=0
        self.allPack = {}
        self.packMod = {}
        self.allPackFlag = False

    def doit(self, module, commands=None, package=None):
        
        # If the package is not specified the default is the first library
        
        if package is None: package = self.vf.libraries[0]
        d=[] 
        importName = package + '.' + module
        try:
            mod = __import__(importName, globals(), locals(),
                            [module])
        except:
            self.vf.warningMsg("ERROR: Could not show module %s"%module)
            #traceback.print_exc()
            return 'ERROR'
        if commands is None:
            if hasattr(mod,"initModule"):
                mod.initModule(self.vf)
            else:
                self.vf.warningMsg("ERROR: Could not show module  %s"%module) 
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
                self.vf.addCommand(d['cmd'], d['name'], d['gui'])
                    
                
    def __call__(self, module, commands=None, package=None, **kw):
        """None <--- helpCommand(module, commands=None, package=None, **kw)
        \nRequired Arguements\n:
        module --- name of the module (filename)
        \nOptional Arguements:\n
        commands --- list of cammnds in that module
        \nPackage --- package name to which module belongs
        """
        kw['commands'] = commands
        kw['package'] = package
        apply(self.doitWrapper, (module,), kw )
    

    def buildFormDescr(self, formName):
        
        if not formName == 'showCmds': return
        idf = InputFormDescr(title='Show Commands and Documentation')
        from ViewerFramework.basicCommand import commandslist
        cname = commandslist
        cname.sort()
        
        

        idf.append({'name':'cmdList',
                    'widgetType':kbScrolledListBox,
                    'wcfg':{'items':cname,
                            'listbox_exportselection':0,
                            'labelpos':'nw',
                            'label_text':'Loaded commands:',
                            'selectioncommand':self.displayCmds_cb,
                            
                            },
                    'gridcfg':{'sticky':'wesn','columnspan':1, 'weight':20}})

        
        idf.append({'name':'doclist',
                    'widgetType':kbScrolledListBox,
                    'wcfg':{'items':[],
                            'listbox_exportselection':0,
                            #'listbox_selectmode':'extended',
                            'labelpos':'nw',
                            'labelmargin':0,
                            'label_text':'DOCUMENTATION',
                            'listbox_width':30                                                        
                            },
                    'gridcfg':{'sticky':'wesn','row':-1,'columnspan':1,  'weight':20}})
        
        idf.append({'name':'dismiss',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'DISMISS',
                            'command':self.dismiss_cb,
                            },
                    'gridcfg':{'sticky':'ew','columnspan':3}})
        
        

        return idf

    def guiCallback(self):
        
        if self.allPack == {}:
            self.allPack = findAllPackages()
        val = self.showForm('showCmds', force=1,modal=0,blocking=0)
        
    def dismiss_cb(self, event=None):
        self.cmdForms['showCmds'].withdraw()
        
    def displayCmds_cb(self, event=None):
        """This function 
        """
        packname=0
        cmdnames=[]
        c = self.cmdForms['showCmds'].mf.cget('cursor')
        self.cmdForms['showCmds'].mf.update_idletasks()
        ebn = self.cmdForms['showCmds'].descr.entryByName
        cmdW = ebn['cmdList']['widget']
        from ViewerFramework.basicCommand import cmd_docslist
        CmdName=cmdW.getcurselection()
        if len(CmdName)!=0:
          name= CmdName[0] 
          #finding documentation for command from cmd_docslist imported from
          #basicCommand
          if name in cmd_docslist.keys():
            docstring = cmd_docslist[name]
            cmdW.selection_clear()
            d =[]
            import string 
            if docstring!=None:
              if '\n' in docstring:
                x = string.split(docstring,"\n")
                for i in x:
                    if i !='':
                        d.append(i)
              else:
                   d.append(docstring)
            docw = ebn['doclist']['widget']
            docw.clear()
            docw.setlist(d)
                

helpCommandGUI = CommandGUI()
helpCommandGUI.addMenuCommand('menuRoot', 'Help',
                              'Commands Documentation')

class SearchCommand(Command):
    """Command to allow the user to search for commands using a given 'search string'. This search string can be matched against either the modules name, the commands name and or the command's documentation string.This will be done to either the default packages or all the packages found on the disk.The user will then be able to show the documentation on the command and load the commands in the application.
    \nPackage : Pmv
    \nModule : helpCommands
    \nClass : SearchCommand
    \nCommand : searchFor
    \nSynopsis:\n
        cmdsFound <- self.searchFor(self, searchString,
                                    matchCmdName=True, matchModName=True,
                                    matchDocString=True, caseSensitive=True,
                                    allPack=False, **kw)
        \ncmdsFound ---  list of string describing the command matching the
                      search string. The format is either
                      Package.module.command or package.module
    \nRequired Arguements:\n
        searchString --- string that will be used to search for the commands.
    \nOptional Arguements:\n    
        matchCmdName --- Boolean to specify whether or not to match the search
                        string agains the command name.
        \nmatchModName --- Boolean to specify whether or not to match the search
                        string agains the name of the modules.
        \nmatchDocString --- Boolean to specify whether or not to match the search
                       string agains the documentation string of the command.
        \ncaseSensitive --- Boolean to specify whether or not the search should be
                        case sensitive.
        \nallPack  --- Boolean to specify whether or not the search should
                        be done in the default packages contained in
                        self.vf.libraries or in all packages on the disk.
    """
    def __init__(self, func=None):
        Command.__init__(self, func)
        self.allPack = findAllPackages()
        self.packModCmd = {}

    def buildInformation(self, packName, package ):
        if not self.packModCmd.has_key(packName):
            modules = findModulesInPackage(package,"def initModule")
            if modules.values():
                modNames = map(lambda x: os.path.splitext(x)[0],
                               modules.values()[0])
            else:
                modNames = {}
            self.packModCmd[packName]={}
            packDict = self.packModCmd[packName]
            for modName in modNames:
                importName = packName + '.' + modName
                try:
                    m = __import__(importName, globals(), locals(),
                                   ['commandList'])
                    if not hasattr(m, 'commandList'):
                        packDict[modName]={}
                    else:
                        packDict[modName]={}
                        keys = map(lambda x: x['name'], m.commandList)
                        values = map(lambda x: x['cmd'].__doc__, m.commandList)
                        for k, v in map(None, keys, values):
                            packDict[modName][k] = v
                except:
                    continue
                        
    def guiCallback(self):
        form = self.showForm('searchForm', modal=0, blocking=0)

    def __call__(self, searchString, matchCmdName=True, matchModName=True,
                 matchDocString=True, caseSensitive=True,
                 allPack=False, **kw ):
        """cmdsFound <- self.searchFor(self, searchString,
                                    matchCmdName=True, matchModName=True,
                                    matchDocString=True, caseSensitive=True,
                                    allPack=False, **kw)
        \ncmdsFound --- list of string describing the command matching the
                      search string. The format is either
                      Package.module.command or package.module

        \nsearchString --- string that will be used to search for the commands.
        \nmatchCmdName --- Boolean to specify whether or not to match the search
                        string agains the command name.
        \nmatchModName --- Boolean to specify whether or not to match the search
                        string agains the name of the modules.
        \nmatchDocString --- Boolean to specify whether or not to match the search
                       string agains the documentation string of the command.
        \ncaseSensitive --- Boolean to specify whether or not the search should be
                        case sensitive.
        \nallPack --- Boolean to specify whether or not the search should
                        be done in the default packages contained in
                        self.vf.libraries or in all packages on the disk.
                       
        """
        kw['matchCmdName']=matchCmdName
        kw['matchDocString']=matchDocString
        kw['caseSensitive']=caseSensitive
        kw['allPack']=allPack
        results = apply(self.doitWrapper, (searchString,), kw)
        return results
    
    def doit(self, searchString, matchCmdName=True, matchModName=True,
                 matchDocString=True, caseSensitive=True, allPack=False):
        if not caseSensitive:
            searchString = searchString.lower()
        import re
        pat = re.compile(searchString)
        
        if not allPack:
            # only look in the default package
            packages = self.vf.libraries
        else:
            packages = self.allPack
        # populate the packModCmd
        cmdsFound = []
        for pName in packages:
            if not self.packModCmd.has_key(pName): 
                self.buildInformation(pName, self.allPack[pName])
                # look for the search string at the right place.
            
            modCmd = self.packModCmd[pName]
            for modName, cmds in modCmd.items():
                # match command Name
                foundMod = False
                if matchModName:
                    if not caseSensitive:
                        mName = modName.lower()
                    else: mName = modName
                    res = pat.search(mName)
                    if res:
                        cmdsFound.append("%s.%s"%(pName, modName))
                        foundMod = True
                if foundMod or \
                   (not matchCmdName and not matchDocString): continue
                for cmd, descr in cmds.items():
                    if matchCmdName:
                        if not caseSensitive:
                            cmdName = cmd.lower()
                        else:
                            cmdName=cmd
                        res = pat.search(cmdName)
                        if res:
                            cmdsFound.append('%s.%s.%s'%(pName,modName,cmd))
                            continue
                    if matchDocString and descr:
                        if not caseSensitive:
                            cmdDescr = descr.lower()
                        else:
                            cmdDescr = descr
                        res = pat.search(cmdDescr)
                        if res:
                            cmdsFound.append('%s.%s.%s'%(pName,modName,cmd))
        if cmdsFound:
            ebn = self.cmdForms['searchForm'].descr.entryByName
            ebn['cmdFound']['widget'].setlist(cmdsFound)
        return cmdsFound
                
        
        
    def buildFormDescr(self, formName):
        if formName == 'infoForm':
            idf = InputFormDescr(title='Command Description')
            idf = InputFormDescr('Documentation')
            idf.append({'name':'cmdDoc',
                        'widgetType':Pmw.ScrolledText,
                         'wcfg':{ 'labelpos':'nw',
                                  'label_text':'command documentation:',
                                  'text_width':50,
                                  'text_height':5},
                         'gridcfg':{'sticky':'we'}})
            
            idf.append({'widgetType':Tkinter.Button,
                        'wcfg':{'text':'Dismiss',
                                'command':self.dismissDoc_cb},
                        'gridcfg':{'sticky':'we'}})
            return idf
        elif formName == 'searchForm': 
            idf = InputFormDescr(title='Search For Commands')

            idf.append({'name':'searchGroup',
                        'widgetType':Pmw.Group,
                        'container':{'searchGroup':"w.interior()"},
                        'wcfg':{'tag_text':'Search Options'},
                        'gridcfg':{'sticky':'wnse', 'columnspan':2}})

            idf.append({'name':'searchString',
                        'widgetType':Pmw.EntryField,
                        'parent':'searchGroup',
                        'wcfg':{'label_text':'Search String',
                                'labelpos':'w',
                                },
                        'gridcfg':{'sticky':'wnse', 'columnspan':2}})

            idf.append({'name':'caseSensitive',
                        'widgetType':Tkinter.Checkbutton,
                        'parent':'searchGroup',
                        'wcfg':{'text':'Case sensitive',
                                'variable':Tkinter.IntVar(),},
                        'gridcfg':{'sticky':'w'},
                        })

            idf.append({'name':'matchGroup',
                        'widgetType':Pmw.Group,
                        'parent':'searchGroup',
                        'container':{'matchGroup':"w.interior()"},
                        'wcfg':{'tag_text':'Match search string to'},
                        'gridcfg':{'sticky':'wnse', 'columnspan':2}})

            idf.append({'name':'matchModName',
                        'widgetType':Tkinter.Checkbutton,
                        'parent':'matchGroup',
                        'defaultValue':1,
                        'tooltip':"The Search String will be matched against the modules name",
                        'wcfg':{'text':'Module Name',
                                'variable':Tkinter.IntVar()},
                        'gridcfg':{'sticky':'w'},
                        })

            idf.append({'name':'matchCmdName',
                        'widgetType':Tkinter.Checkbutton,
                        'parent':'matchGroup',
                        'defaultValue':1,
                        'tooltip':"The Search String will be matched against the commands name",
                        'wcfg':{'text':'Command Name',
                                'variable':Tkinter.IntVar()},
                        'gridcfg':{'sticky':'w'},
                        })

            idf.append({'name':'matchDocString',
                        'widgetType':Tkinter.Checkbutton,
                        'parent':'matchGroup',
                        'defaultValue':1,
                        'tooltip':"The Search String will be matched against the content of the documentation string",
                        'wcfg':{'text':'Documentation String',
                                'variable':Tkinter.IntVar()},
                        'gridcfg':{'sticky':'w'},
                        })

            idf.append({'name':'choices',
                        'widgetType':Pmw.RadioSelect,
                        'parent':'searchGroup',
                        'defaultValue':'Default Packages',
                        'listtext':['Default Packages', 'All Packages'],
                        'tooltip':"Choose where to look for a command: \n- Default packages  \n-All packages on disk which is slower",
                        'wcfg':{'labelpos':'nw',
                                'label_text':'Search in:',
                                'buttontype':'radiobutton'},
                        'gridcfg':{'sticky':'w'}})

            idf.append({'name':'search',
                        'widgetType':Tkinter.Button,
                        'wcfg':{'text':'SEARCH',
                                'command':self.searchCmd_cb},
                        'gridcfg':{'columnspan':2}})

            idf.append({'name':'resultGroup',
                        'widgetType':Pmw.Group,
                        'container':{'resultGroup':"w.interior()"},
                        'wcfg':{'tag_text':'Search Result'},
                        'gridcfg':{'sticky':'wnse', 'columnspan':2}})

            idf.append({'name':'cmdFound',
                        'widgetType':kbScrolledListBox,
                        'parent':'resultGroup',
                        'tooltip':"This widget will list all the commands found with the search string.",
                        'wcfg':{'items':[],
                                'listbox_exportselection':0,
                                'labelpos':'nw',
                                'label_text':'Found Commands:',
                                'dblclickcommand':self.loadCmd_cb
                                },
                        'gridcfg':{'sticky':'wesn','columnspan':2 }})

            idf.append({'name':'info',
                        'widgetType':Tkinter.Button,
                        'parent':'resultGroup',
                        'tooltip':"Display the documentation string of the selected command.",
                        'wcfg':{'text':'INFO','height':1,
                                'command':self.info_cb},
                        'gridcfg':{'sticky':'wesn' }})

            idf.append({'name':'load',
                        'widgetType':Tkinter.Button,
                        'parent':'resultGroup',
                        'tooltip':"Show the selected commands in the application",
                        'wcfg':{'text':'LOAD','height':1,
                                'command':self.loadCmd_cb},
                        'gridcfg':{'sticky':'wesn','row':-1}})

    ##         idf.append({'name':'cmdLoaded',
    ##                     'widgetType':kbScrolledListBox,
    ##                     'parent':'resultGroup',
    ##                     'tooltip':"This widget will list all the commands found with the search \nstring that have already been loaded in the application",
    ##                     'wcfg':{'items':[],
    ##                             'listbox_exportselection':0,
    ##                             'labelpos':'nw',
    ##                             'label_text':'Loaded Commands:',
    ##                             },
    ##                     'gridcfg':{'sticky':'wesn', 'rowspan':2,
    ##                                'column':2, 'row':0}})



            idf.append({'name':'search',
                        'widgetType':Tkinter.Button,
                        'wcfg':{'text':'DISMISS',
                                'command':self.dismiss_cb},
                        'gridcfg':{'columnspan':2}})
            return idf

    def info_cb(self):
        ebn = self.cmdForms['searchForm'].descr.entryByName
        sel = ebn['cmdFound']['widget'].getvalue()
        # get teh description:
        if not len(sel): return
        entry = sel[0].split('.')
        if len(entry) == 3:
            cmdDescr = self.packModCmd[entry[0]][entry[1]][entry[2]]
        elif len(entry) == 2:
            # need to get the module descr.
            importName = sel[0]
            m = __import__(importName, globals(), locals())
            cmdDescr = eval('m.%s.__doc__'%entry[1])
        if cmdDescr is None: cmdDescr=""
        val = self.showForm('infoForm', modal=0, blocking=0)
        ebn = self.cmdForms['infoForm'].descr.entryByName
        
        ebn['cmdDoc']['widget'].setvalue(cmdDescr)

    def searchCmd_cb(self):
        val = self.cmdForms['searchForm'].checkValues()
        if not val: self.vf.warningMsg("Please Enter a search string")
        searchString = val['searchString']
        self.cmdForms['searchForm'].descr.entryByName['cmdFound']['widget'].clear()
        del val['searchString']
        kw = {}
        if val.has_key('choice'):
            choice = val['choice']
            if choice == 'All Packages':
                kw['allPack'] = True
            elif choice == 'Default Packages':
                kw['allPack'] = False

        if val.has_key('matchCmdName'):
            kw['matchCmdName'] = val['matchCmdName']
        if val.has_key('matchDocString'):
            kw['matchDocString'] = val['matchDocString']
        if val.has_key('caseSensitive'):
            kw['caseSensitive'] = val['caseSensitive']
        if val.has_key('matchModName'):
            kw['matchModName'] = val['matchModName']

        results = apply(self.doitWrapper, (searchString,), kw)

    def dismiss_cb(self):
        self.cmdForms['searchForm'].withdraw()
        if self.cmdForms.has_key('infoForm') and \
           self.cmdForms['infoForm'].root.winfo_ismapped():
            self.dismissDoc_cb

    def dismissDoc_cb(self):
        self.cmdForms['infoForm'].withdraw()

    def loadCmd_cb(self):
        # need to call the split the name and call the
        # browse commands
        ebn = self.cmdForms['searchForm'].descr.entryByName
        rlb = ebn['cmdFound']['widget']
        sel = rlb.getvalue()
        entry = sel[0].split('.')
        if len(entry) == 3:
            self.vf.browseCommands(entry[1], commands=[entry[2]],
                                   package=entry[0])
        elif len(entry)==2:
            self.vf.browseCommands(entry[1], package=entry[0])
            
       

    
SearchCommandGUI = CommandGUI()
SearchCommandGUI.addMenuCommand('menuRoot', 'Help',
                                'Search For Commands')

class ReportBugCommand(Command):
    """This command will open a browser allowing the user to enter a bug in MGL
    Bugzilla.
    """
    pass
##  class Helpwin:
##      def __init__(self, master, contents, title='Help'):
##          self.__root = root = Tkinter.Toplevel(master, class_='Pynche')
##          root.protocol('WM_DELETE_WINDOW', self.__withdraw)
##          root.title(title)
##          root.iconname(title)
##          self.text = Tkinter.Text(root, relief=Tkinter.SUNKEN,
##                                   width=80, height=24)
##          self.text.insert(0.0, contents)
##          scrollbar = Tkinter.Scrollbar(root)
##          scrollbar.pack(fill=Tkinter.Y, side=Tkinter.RIGHT)
##          self.text.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)
##          self.text.configure(yscrollcommand=(scrollbar, 'set'))
##          scrollbar.configure(command=(self.text, 'yview'))

##          okay = Tkinter.Button(root, text='Ok', command=self.__withdraw)
##          okay.pack(side=Tkinter.BOTTOM, expand=1)
##          okay.focus_set()

##      def __withdraw(self, event=None):
##          self.__root.withdraw()

##      def deiconify(self):
##          self.__root.deiconify()


##  class helpModuleCommand(Command):
##      """Command to acces documentation of modules"""
    

##      def buildMenus(self, button, menuName):

##          # remove first entry which is an empty line
##          mmenu = button.menu.children[menuName]
##          mmenu.delete(1)
##          mmenu.bind("<ButtonRelease-1>", self.guiCallback)

##          if len(self.vf.libraries)==0: return

##          # here we would have to loop over all libraries
##  ##          modu = __import__(self.vf.package+'.modlib', globals(),
##  ##                           locals(), ['modlib'])
##  ##          mod = ''
##  ##          # dictionary of files keys=widget, values = filename
##  ##          self.entries = modu.modlist
##  ##          for entry in modu.modlist:
##  ##              # add command as last entry cascade entry
##  ##              mmenu.add_command(label=entry[1])


##      def doit(self, package, filename):
##          if package is None: _package = filename
##          else: _package = "%s.%s"%(package, filename)
##          self.log(_package, filename)

##          module = __import__( _package, globals(), locals(), [filename])
##          if module.__doc__:
##              Helpwin(self.vf.GUI.ROOT,  doc = module.__doc__,
##                      title = '%s.%s help'% (package, filename) )
##          else:
##              msg = 'Sorry no documentation available for module %s.%s !' % (package, filename)
##              tkMessageBox.showwarning('No documentation', msg)
##  ##        self.vf.message(module.__doc__)


##      def customizeGUI(self):
##          """create the cascade menu for selecting modules to be loaded"""

##          # ugly hack ! when menu is torn off guiCallback get's called twice
##          self.isFirstTearOffCallback = 1

##          barName = self.GUI.menuDict['menuBarName']
##          bar = self.vf.GUI.menuBars[barName]
##          buttonName = self.GUI.menuDict['menuButtonName']
##          button = bar.menubuttons[buttonName]
##          self.buildMenus(button, 'Module documentation')


##      def __call__(self, filename, package=None):

##          if package==None: package=self.vf.package
##          self.doit(filename, package)


##      def guiCallback(self, event=None):
##          if type(event.widget) is types.StringType: #when menu is torn off
##              if not self.isFirstTearOffCallback:
##                  self.isFirstTearOffCallback = 1
##                  return
##              self.isFirstTearOffCallback = 0
##              index = int(self.vf.GUI.ROOT.tk.call(event.widget, 'index',
##                                                   'active'))-1
##          else:
##              index = event.widget.index("active")-1
##              if index==-1: # when tear-off bar is used we come here
##                  return
        
##          entry = self.entries[index]
        
##          self.doit(entry[0], entry[1])



commandList = [
    {'name':'mailingListsCommand','cmd':mailingListsCommand(),'gui':mailingListsCommandGUI},
    {'name': 'helpCommand', 'cmd':helpCommand(), 'gui':helpCommandGUI},
    {'name': 'showCitation', 'cmd':CitationCommand(),  'gui':citationCommandGUI},
    {'name': 'citeThisScene', 'cmd':CiteThisSceneCommand(),  'gui':CiteThisSceneCommandGUI},    
    {'name':'searchForCmd','cmd':SearchCommand(),'gui':SearchCommandGUI},
    
    ]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
