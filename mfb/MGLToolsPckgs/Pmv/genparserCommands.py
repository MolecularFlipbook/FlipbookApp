#############################################################################
#
# Author: Kevin Chan, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
#$Header: /opt/cvs/python/packages/share1.5/Pmv/genparserCommands.py,v 1.7 2004/03/22 19:29:39 sophiec Exp $
#
#$Id: genparserCommands.py,v 1.7 2004/03/22 19:29:39 sophiec Exp $
#
from ViewerFramework.VFCommand import CommandGUI
##  from ViewerFramework.gui import InputForm, InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputForm, InputFormDescr

from Pmv.mvCommand import MVCommand
from MolKit.protein import Protein
from MolKit.genPdbParser import GenPdbParser, IndexSpecs, ColumnSpecs
from MolKit.molecule import Atom
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import SaveButton, LoadButton
import types, os, string
import Pmw, Tkinter


from Pmv.fileCommands import PDBReader

class GenPDBReader(PDBReader):
    """ Command to load PDB files using parser with user defined
    specifications """


    def __init__(self):
        PDBReader.__init__(self)
        self.specfileTypes = [('all', '*')]
        self.specfileBrowserTitle = 'load specification file: '


    def _doit(self, filename, specs):
        """ does the parsing of the pdb file using specs object"""
        newparser = GenPdbParser(filename, specs)
        mols = newparser.parse()
        newmol = []
        for m in mols:
            mol = self.vf.addMolecule(m)
            if mol==None:
                del newparser
                return []
            if hasattr(self, "done"):
                self.done.release()
            newmol.append(mol)
        return newmol


    def doit(self, filename, specfile):
        """ takes a pdb file name and a specification file name """
#	self.log(filename, specfile)
        specs = self.extractSpecs(specfile)
        if specs:
            mols = self._doit(filename, specs)
            return mols
        else:
            import traceback,sys
            print "ERROR IN READING SPECIFICATIONS:%s"%specfile
            traceback.print_exc()
            print "---------- End of error message ----------"
            if self.vf.hasGui and self.vf.guiVisible \
               and self.vf.withShell:
                self.vf.GUI.pyshell.top.deiconify()
##          mesg = "error in reading specifications from " + specfile
##          self.warningMsg(mesg)

    def __call__(self, filename, specfile, **kw):
        """mol <- genreadPDB(filename, specfile, **kw)
           filename: path name of the PDB file
           specfile: a specification file name
           """
        return apply ( self.doitWrapper, (filename, specfile), kw )

    def guiCallback(self, event=None, *args, **kw):
	cmdmenuEntry = self.GUI.menu[4]['label']
        file = self.vf.askFileOpen(types=self.fileTypes,
                                   idir = self.lastDir,
                                   title=self.fileBrowserTitle)
	mol = None
	if file != None:
            self.lastDir = os.path.split(file)[0]
            #args = (file,)
            self.vf.GUI.configMenuEntry(self.GUI.menuButton, cmdmenuEntry,
                                        state = 'disabled')
            #mol = self.vf.tryto(self.doit, file)
            specfile = self.vf.askFileOpen(types=self.specfileTypes,
                                   idir = self.lastDir,
                                   title=self.specfileBrowserTitle)
            if specfile != None:
##                  RecSpec = self.extractSpecs(specfile)
##                  if RecSpec:
                try:
                    mol = self.doitWrapper(file, specfile, redraw=1)
                    self.vf.GUI.configMenuEntry(self.GUI.menuButton,
                                        cmdmenuEntry,state = 'normal')
                except:
                    import traceback,sys
                    print "ERROR IN LOADING FILE:%s"%file
                    traceback.print_exc()
                    print "---------- End of error message ----------"
                    if self.vf.hasGui and self.vf.guiVisible \
                       and self.vf.withShell:
                        self.vf.GUI.pyshell.top.deiconify()
##                          self.vf.GUI.configMenuEntry(self.GUI.menuButton,
##                                              cmdmenuEntry,state = 'normal')

##                      try:
##                          mol = self.doit(file, RecSpec)
##                      except:
##                          msg = "error in loading file: " + file
##                          self.warningMsg(msg)
            self.vf.GUI.configMenuEntry(self.GUI.menuButton,
                                        cmdmenuEntry,state = 'normal')
	return mol

    def extractSpecs(self, file):
        """ takes a specification file in proper format and creates a specs
        object """
        f = open(file, 'r')
        lines = f.readlines(30)
##          num = len(string.split(lines[0]))
##          if num==4:
        parts = string.split(lines[0])
        if len(parts)==4 and parts[0]=='FieldName' and parts[1]=='From' and \
           parts[2]=='To' and parts[3]=='Type':
            Specs = ColumnSpecs()
            for line in lines[1:]:
                vals = string.split(line)
                if len(vals)==4:
                    specEntry = {'field_name':vals[0],
                                 'from':int(vals[1]),
                                 'to':int(vals[2]),
                                 'var_type':vals[3]
                                 }
                    Specs.define_field(specEntry)
        elif len(parts)==3 and parts[0]=='FieldName' and parts[1]=='Index' \
             and parts[2]=='Type':
            Specs = IndexSpecs()
            for line in lines[1:]:
                vals = string.split(line)
                if len(vals)==3:
                    specEntry = {'field_name':vals[0],
                                 'index':int(vals[1]),
                                 'var_type':vals[2]
                                 }
                    Specs.define_field(specEntry)
        else: return None
        if not (Specs.DefFieldsDict.has_key('x') and
                Specs.DefFieldsDict.has_key('y') and
                Specs.DefFieldsDict.has_key('z')):
            msg = "specs for atom coordinates (x,y,z) are missing"
            self.warningMsg(msg)
            return None
        return Specs
       
genPDBReaderGuiDescr = {'widgetType':'menuRoot', 'menuBarName':'File',
                        'menuButtonName':'Read PDB with Gen Parser ...',
                        'index':0}

GenPDBReaderGUI = CommandGUI()
GenPDBReaderGUI.addMenuCommand('menuRoot', 'File',
                               'Read PDB with Gen Parser ...',index=0)


FieldNames = ('serial', 'name', 'altLoc', 'resName', 'chainID',
                      'resSeq', 'iCode', 'x', 'y', 'z', 'occupancy',
                      'tempFactor', 'segID', 'element', 'charge', 'other')
variableTypes = ('int', 'character', 'float', 'alphabetic', 'string')
specEntries = ('field_name', 'var_type', 'from', 'to', 'index')


class DefinePdbSpecifications(MVCommand):
    """ class to define some pdb specifications in a dictionary and save them
    in a file """
    
    def __init__(self):
        """ constructor """
        MVCommand.__init__(self)
        # iformStatus tells if these exist and if the widgets are visible
        self.iFormStatus = {'columnspecs':0, 'columnwidgets':0,
                            'cwidgetsshow':0,
                            'indexspecs':0, 'indexwidgets':0,
                            'iwidgetsshow':0}
        self.maxIndex = None
        self.active = 0
        self.ccurSpecFile = ''
        self.icurSpecFile = ''

    def extractSpecs(self, file):
        """ takes a specification file in proper format and creates a specs
        object """
        f = open(file, 'r')
        lines = f.readlines(30)
##          num = len(string.split(lines[0]))
##          if num==4:
        parts = string.split(lines[0])
        if len(parts)==4 and parts[0]=='FieldName' and parts[1]=='From' and \
           parts[2]=='To' and parts[3]=='Type':
            Specs = ColumnSpecs()
            for line in lines[1:]:
                vals = string.split(line)
                if len(vals)==4:
                    specEntry = {'field_name':vals[0],
                                 'from':int(vals[1]),
                                 'to':int(vals[2]),
                                 'var_type':vals[3]
                                 }
                    Specs.define_field(specEntry)
#        elif num==3:
        elif len(parts)==3 and parts[0]=='FieldName' and parts[1]=='Index' \
             and parts[2]=='Type':
            Specs = IndexSpecs()
            for line in lines[1:]:
                vals = string.split(line)
                if len(vals)==3:
                    specEntry = {'field_name':vals[0],
                                 'index':int(vals[1]),
                                 'var_type':vals[2]
                                 }
                    Specs.define_field(specEntry)
        else: return None
##          if not (Specs.DefFieldsDict.has_key('x') and
##                  Specs.DefFieldsDict.has_key('y') and
##                  Specs.DefFieldsDict.has_key('z')): return None
        return Specs


    def compareFrom(self, e1, e2):
        return cmp(e1['from'], e2['from'])

    def compareIndex(self, e1, e2):
        return cmp(e1['index'], e2['index'])

    def update_SpecBox(self):
        """ writes the specs in self.Specs to the ScrolledText box in gui. """
        entriesString = ''
        if self.Specs.specType=='c':
            entrylist = []
            for entryname in (self.Specs.DefFieldsDict.keys() +
                              self.Specs.UserFieldsDict.keys()):
                e = self.Specs.DefFieldsDict[entryname]
                entrylist.append(e)
            entrylist.sort(self.compareFrom)
            for entry in entrylist:
                entryname = entry['field_name']
                e = self.Specs.DefFieldsDict[entryname]
                entrystring  = string.ljust(entryname, 12) +\
                               string.ljust(str(e['from']), 4) +\
                               string.ljust(str(e['to']), 4) +\
                               e['var_type'] + '\n'
##                  for key in self.Specs.DefFieldsDict[entryname].keys():
##                      if key != 'field_name':
##                          val = self.Specs.DefFieldsDict[entryname][key]
##                          entrystring  = entrystring + '%s'%val
##                  entrystring = entrystring + '\n'
                entriesString = entriesString + entrystring
        elif self.Specs.specType=='i':
            entrylist = []
            for entryname in (self.Specs.DefFieldsDict.keys() +
                              self.Specs.UserFieldsDict.keys()):
                e = self.Specs.DefFieldsDict[entryname]
                entrylist.append(e)
            entrylist.sort(self.compareIndex)
            for entry in entrylist:
                entryname = entry['field_name']
                e = self.Specs.DefFieldsDict[entryname]
                entrystring  = string.ljust(entryname, 13) +\
                               string.ljust(str(e['index']), 6) +\
                               e['var_type'] + '\n'
                entriesString = entriesString + entrystring
        else: return
        specboxentry = self.idf.entryByName['%s_specBox'%self.Specs.specType]
        specboxentry['widget'].settext(entriesString)


    def clearSpecs_cb(self, event = None):
        """ clears the current specifications in the gui """
        if self.iFormStatus['cwidgetsshow']:
            self.Specs = ColumnSpecs()
            self.idf.entryByName['c_save']['ifile'] = None
            self.ccurSpecFile = ''
        elif self.iFormStatus['iwidgetsshow']:
            self.Specs = IndexSpecs()
            self.idf.entryByName['i_save']['ifile'] = None
            self.icurSpecFile = ''
        self.update_SpecBox()
        self.idf.entryByName['SpecFileName']['widget'].configure(text='')

    def loadSpecs_cb(self, filename, event = None):
        """ callback function to load specs from a file to the gui """
        Specs = self.extractSpecs(filename)
        bad = 0
        if Specs:
            fparts = os.path.split(filename)
            if isinstance(Specs, ColumnSpecs):
                self.column_cb()
                self.Specs = self.columnSpecs = Specs
                self.idf.entryByName['byColumn']['wcfg']['variable'].set('c')
                self.idf.entryByName['c_save']['idir'] = fparts[0]
                self.idf.entryByName['c_save']['ifile'] = fparts[1]
                self.ccurSpecFile = filename
            elif isinstance(Specs, IndexSpecs):
                self.index_cb()
                self.Specs = self.indexSpecs = Specs
                self.idf.entryByName['byIndex']['wcfg']['variable'].set('i')
                self.idf.entryByName['i_save']['idir'] = fparts[0]
                self.idf.entryByName['i_save']['ifile'] = fparts[1]
                self.icurSpecFile = filename
            else: bad = 1 
        else: bad = 1
        if bad:
            msg = "error: could not load specification file"
            self.vf.warningMsg(msg)
        else:
            self.update_SpecBox()
            self.idf.entryByName['SpecFileName']['widget'].configure(text=filename)


    def saveSpecs_cb(self, filename, event = None):
        """ callback function to save pdb specs to filename """
        if not (self.Specs.DefFieldsDict.has_key('x') and
                self.Specs.DefFieldsDict.has_key('y') and
                self.Specs.DefFieldsDict.has_key('z')):
            msg = "specs for atom coordinates (x,y,z) are required to parse a pdb file"
            self.warningMsg(msg)
            return

        fparts = os.path.split(filename)
        self.write_from_specBox(filename)
        self.idf.entryByName['SpecFileName']['widget'].configure(text=filename)
        if self.iFormStatus['cwidgetsshow']:
            self.idf.entryByName['c_save']['idir'] = fparts[0]
            self.idf.entryByName['c_save']['ifile'] = fparts[1]
            self.ccurSpecFile = filename
        elif self.iFormStatus['iwidgetsshow']:
            self.idf.entryByName['i_save']['idir'] = fparts[0]
            self.idf.entryByName['i_save']['ifile'] = fparts[1]
            self.icurSpecFile = filename
##          self.writeDicts(filename,
##                          (self.Specs.DefFieldsDict, self.Specs.UserFieldsDict),
##                          ('DefFieldsDict', 'UserFieldsDict'))

    def write_from_specBox(self, filename):
        """ takes text from specBox and writes it to a file """
        if self.Specs.specType=='c':
            text = 'FieldName  From To  Type      \n' + \
                   self.idf.entryByName['c_specBox']['widget'].get()
        elif self.Specs.specType=='i':
            text = 'FieldName   Index  Type       \n' + \
                   self.idf.entryByName['i_specBox']['widget'].get()

        if text:
            f = open(filename, 'w')
            f.write(text)
            f.close()

    # not implemented now
##      def writeDicts(self, filename, dicts, dictnames):
##          """ takes filename, dictionaries, and names of dictionaries.  Writes
##          the dictionaries in proper python format in the file. """
##          f = open(filename, 'w')
##          i = 0 
##          for dict in dicts:
##              dictstring = dictnames[0] + '= {'
##              for key in dict.keys():
##                  val = dict[key]
##                  if type(val)==types.StringType: val = "'%s'"%val
##                  dicstring = dictstring + " '%s'"%key +':' + '%s,'%str(val)
##              dictstring = dictstring[:-1] + '}\n'
##              f.write(dictstring)
##              i = i+1
##          f.close()                

    def addToSpecs_cb(self, event = None):
        """ callback function to add button.  Adds the specs in the entry
        fields to the self.Specs object. """
        fieldspec = {}
        for wName in self.smallidf.entryByName.keys():
            if wName in specEntries:
                # check that there is an entry
                widget = self.smallidf.entryByName[wName]['widget']
                if wName in ('index', 'from', 'to'):
                    fieldspec[wName] = int(widget.get())
                else: fieldspec[wName] = widget.get()  
        self.Specs.define_field(fieldspec)
        self.update_SpecBox()

    def removeFromSpecs_cb(self, event = None):
        """ callback to remove button.  Removes spec given by user from the
        self.Specs object. """
        # check that there is an entry
        widget = self.smallidf.entryByName['field_name']['widget']
        fieldspec = {'field_name':widget.get()}
        self.Specs.remove_field(fieldspec)
        self.update_SpecBox()

    def col_selectfield_cb(self, fieldname, event = None):
        """ callback to put current values of fieldname into the entryfield of
        the gui """
        ebn = self.smallidf.entryByName
        if self.Specs.DefFieldsDict.has_key(fieldname) or \
           self.Specs.UserFieldsDict.has_key(fieldname):
            ebn['from']['widget'].setentry(self.Specs.get(fieldname, 'from'))
            ebn['to']['widget'].setentry(self.Specs.get(fieldname, 'to'))
            ebn['var_type']['widget'].component('entryfield').setentry(self.Specs.get(fieldname, 'var_type'))
        else:
            ebn['from']['widget'].clear()
            ebn['to']['widget'].clear()

    def ind_selectfield_cb(self, fieldname, event = None):
        """ callback to put current values of fieldname into the entryfield of
        the gui """
        ebn = self.smallidf.entryByName
        if self.Specs.DefFieldsDict.has_key(fieldname) or \
           self.Specs.UserFieldsDict.has_key(fieldname):
            ebn['index']['widget'].setentry(self.Specs.get(fieldname, 'index'))
            ebn['var_type']['widget'].component('entryfield').setentry(self.Specs.get(fieldname, 'var_type'))
        else:
            ebn['index']['widget'].clear()

    def defineColSpecs_cb(self, event = None):
        """ callback that creates an input form with fields for the user to
        define the field specifications in column format.  callback of a
        define/modify button.
        """
        # if it exists, bring to front ?
        if not hasattr(self, 'smallform'):
            smallidf = self.smallidf = \
                       InputFormDescr(title = 'Define Column Specs:')
            smallidf.append({'widgetType':Pmw.ComboBox,
                             'name':'field_name',
                             'wcfg':{'label_text':'Field Name:',
                                     'labelpos':'w', 'label_width':25,
                                     'scrolledlist_items':FieldNames,
                                     'selectioncommand':self.col_selectfield_cb,
                                     'entryfield_validate':'alphabetic',
                                     'entry_width':12},
                             'gridcfg':{'row':0, 'column':0, 'sticky':'w',
                                        'columnspan':3}
                             })
            smallidf.append({'widgetType':Pmw.EntryField,
                             'name':'from',
                             'wcfg':{'labelpos':'w', 'label_width':25,
                                     'label_text':'from column (int 1-80):',
                                     'entry_width':2,
                                     'validate':{'validator':'numeric',
                                                 'min':1,
                                                 'max':80}},
                             'gridcfg':{'row':1, 'column':0, 'sticky':'w',
                                        'columnspan':3}
                             })
            smallidf.append({'widgetType':Pmw.EntryField,
                             'name':'to',
                             'wcfg':{'labelpos':'w', 'label_width':25,
                                     'label_text':'to column (int 1-80):',
                                     'entry_width':2,
                                     'validate':{'validator':'numeric',
                                                 'min':1,
                                                 'max':80}},
                             'gridcfg':{'row':2, 'column':0, 'sticky':'w',
                                        'columnspan':3}
                             })
            smallidf.append({'widgetType':Pmw.ComboBox,
                             'name':'var_type',
                             'defaultValue':'string',
                             'wcfg':{'label_text':'Field value type:',
                                     'labelpos':'w', 'label_width':25,
                                     'scrolledlist_items':variableTypes,
                                     'entry_width':12},
                             'gridcfg':{'row':3, 'column':0, 'sticky':'w',
                                        'columnspan':3}
                             })
            smallidf.append({'widgetType':Tkinter.Button,
                             'name':'Add',
                             'wcfg':{'text':'Add',
                                     'command':self.addToSpecs_cb},
                             'gridcfg':{'row':4, 'column':0, 'sticky':'ew'}
                             })
            smallidf.append({'widgetType':Tkinter.Button,
                             'name':'Remove',
                             'wcfg':{'text':'Remove',
                                     'command':self.removeFromSpecs_cb},
                             'gridcfg':{'row':4, 'column':1, 'sticky':'ew'}
                             })
            smallidf.append({'widgetType':Tkinter.Button,
                             'name':'dismiss',
                             'wcfg':{'text':'dismiss',
                                     'command':self.dismiss_smallform_cb},
                             'gridcfg':{'row':4, 'column':2, 'sticky':'ew'}
                             })
            self.smallform = self.vf.getUserInput(smallidf,
                                                  modal = 0, blocking = 0)

    def defineIndSpecs_cb(self, event = None):
        """ callback that creates an input form with fields for the user to
        define the field specifications in index format.  callback of a
        define/modify button.
        """
        # if it exists, bring to front ?
        if not hasattr(self, 'smallform'):
            smallidf = self.smallidf \
                       = InputFormDescr(title = 'Define Index Specs:')
            # show split records???
            smallidf.append({'widgetType':Pmw.ComboBox,
                             'name':'field_name',
                             'wcfg':{'label_text':'Field Name:',
                                     'labelpos':'w', 'label_width':25,
                                     'scrolledlist_items':FieldNames,
                                     'selectioncommand':self.ind_selectfield_cb,
                                     'entryfield_validate':'alphabetic',
                                     'entry_width':12},
                             'gridcfg':{'row':0, 'column':0, 'sticky':'w',
                                        'columnspan':3}
                             })
            smallidf.append({'widgetType':Pmw.EntryField,
                             'name':'index',
                             'wcfg':{'labelpos':'w', 'label_width':25,
                                     'label_text':'index(int):',
                                     'entry_width':2,
                                     'validate':{'validator':'numeric',
                                                 'min':1, 'max':self.maxIndex
                                                 }},
                             'gridcfg':{'row':1, 'column':0, 'sticky':'w',
                                        'columnspan':3}
                             })
            smallidf.append({'widgetType':Pmw.ComboBox,
                             'name':'var_type',
                             'defaultValue':'string',
                             'wcfg':{'label_text':'Field value type:',
                                     'labelpos':'w', 'label_width':25,
                                     'scrolledlist_items':variableTypes,
                                     'entry_width':12},
                             'gridcfg':{'row':2, 'column':0, 'sticky':'w',
                                        'columnspan':3}
                             })
            smallidf.append({'widgetType':Tkinter.Button,
                             'name':'Add',
                             'wcfg':{'text':'Add',
                                     'command':self.addToSpecs_cb},
                             'gridcfg':{'row':3, 'column':0, 'sticky':'ew'}
                             })
            smallidf.append({'widgetType':Tkinter.Button,
                             'name':'Remove',
                             'wcfg':{'text':'Remove',
                                     'command':self.removeFromSpecs_cb},
                             'gridcfg':{'row':3, 'column':1, 'sticky':'ew'}
                             })
            smallidf.append({'widgetType':Tkinter.Button,
                             'name':'dismiss',
                             'wcfg':{'text':'dismiss',
                                     'command':self.dismiss_smallform_cb},
                             'gridcfg':{'row':3, 'column':2, 'sticky':'ew'}
                             })
            self.smallform = self.vf.getUserInput(smallidf,
                                                  modal = 0, blocking = 0)

    def hide_widget_group(self, grouptype):
        """ hides widgets of grouptype (either 'i' or 'c').  called by either
        column_cb or index_cb """
        idfentries = self.idf.entryByName
        for name in idfentries.keys():
            if name[:2]==(grouptype+'_'):
                idfentries[name]['widget'].grid_forget()
        if hasattr(self, 'smallform'):
            self.smallform.destroy()
            del self.smallform, self.smallidf
        self.iFormStatus['%swidgetsshow'%grouptype] = 0

    def show_widget_group(self, grouptype):
        """ shows existing widgets of grouptype (either 'i' or 'c'). called by
        either column_cb or index_cb
        """
        idfentries = self.idf.entryByName
        for name in idfentries.keys():
            if name[:2]==(grouptype+'_'):
                apply(idfentries[name]['widget'].grid,(),idfentries[name]['gridcfg'])
        self.iFormStatus['%swidgetsshow'%grouptype] = 1
        if grouptype=='c':
            self.Specs = self.columnSpecs
            self.idf.entryByName['SpecFileName']['widget'].configure(text=self.ccurSpecFile)
        elif grouptype=='i':
            self.Specs = self.indexSpecs
            self.idf.entryByName['SpecFileName']['widget'].configure(text=self.icurSpecFile)

            
    def createColumnWidgets(self):
        """ adds widgets to self.idf and self.form useful for column
        specification format.  called bycolumn_cb """
        entries = []
        entries.append({'widgetType':Tkinter.Button, 'name':'c_define_modify_specs',
                       'wcfg':{'text':'Define/Modify...',
                               'command':self.defineColSpecs_cb,
                               'width':12},
                        'gridcfg':{'row':5, 'column':0, 'columnspan':2}
                                   #, 'sticky':'e'}
                        })
        entries.append({'widgetType':Pmw.ScrolledText, 'name':'c_specBox',
                        'wcfg':{'labelpos':'nw',
                                'label_text':'FieldName  From To  Type      ',
                                'text_width':30, 'text_height':5,
                                'text_font':('Courier New', 10),
                                'label_font':('Courier New', 10)},
                        'gridcfg':{'row':5, 'column':2, 'rowspan':3,
                                   'columnspan':2}
                                   #'sticky':'w'}
                        })
        if self.ccurSpecFile:
            fparts = os.path.split(self.ccurSpecFile)
        else: fparts = ['.', None]
##          entries.append({'widgetType':'SaveButton', 'name':'c_save',
##                          'wcfg':{'text':'Save',
##                                  'width':12},   
##                          'callback':self.saveSpecs_cb,
##                          'gridcfg':{'row':6, 'column':0, 'columnspan':2},#, 'sticky':'w'},
##                          'idir':fparts[0], 'ifile':fparts[1]
##                          })

        entries.append({'widgetType':SaveButton,
                        'name':'c_save',
                        'wcfg':{'buttonType':Tkinter.Button,
                                'title':'Save Specifications in File...',
                                'types':[('All Files','*')],
                                'idir':fparts[0],
                                'ifile':fparts[1],
                                'callback':self.saveSpecs_cb,
                                'widgetwcfg':{'text':'Save',
                                              'width':12}},   
                        'gridcfg':{'row':6, 'column':0, 'columnspan':2},#, 'sticky':'w'},
                        })
        entries.append({'widgetType':Tkinter.Button, 'name':'c_clear',
                        'wcfg':{'text':'Clear',
                                'command':self.clearSpecs_cb,
                                'width':12},
                        'gridcfg':{'row':7, 'column':0, 'columnspan':2}
                        })

        for entry in entries:
            self.form.addEntry(entry)
            self.idf.entryByName[entry['name']] = entry
        self.iFormStatus['columnwidgets'] = 1     
        self.iFormStatus['cwidgetsshow'] = 1
        self.idf.entryByName['SpecFileName']['widget'].configure(text = self.ccurSpecFile)
                                                                             

    def createIndexWidgets(self):
        """ adds widgets to self.idf and self.form useful to specify in index
        format.  called by index_cb """
        entries = []
        entries.append({'widgetType':Tkinter.Button, 'name':'i_define_modify_specs',
                       'wcfg':{'text':'Define/Modify...',
                               'command':self.defineIndSpecs_cb,
                               'width':12},
                        'gridcfg':{'row':5, 'column':0, 'columnspan':2}#, 'sticky':'e'}
                        })
        entries.append({'widgetType':Pmw.ScrolledText, 'name':'i_specBox',
                        'wcfg':{'labelpos':'nw',
                                'label_text':'FieldName   Index  Type       ',
                                'text_width':30, 'text_height':5,
                                'text_font':('Courier New', 10),
                                'label_font':('Courier New', 10)},
                        'gridcfg':{'row':5, 'column':2, 'rowspan':3,
                                   'columnspan':2}
                                   #'sticky':'w'}
                        })
        if self.icurSpecFile: fparts = os.path.split(self.icurSpecFile)
        else: fparts = ['.', None]
##          entries.append({'widgetType':'SaveButton', 'name':'i_save',
##                          'wcfg':{'text':'Save',
##                                  'width':12},
##                          'callback':self.saveSpecs_cb,
##                          'gridcfg':{'row':6, 'column':0, 'columnspan':2},#, 'sticky':'w'},
##                          'idir':fparts[0], 'ifile':fparts[1]
##                          })
        entries.append({'widgetType':SaveButton,
                        'name':'i_save',
                        'wcfg':{'buttonType':Tkinter.Button,
                                'title':'Save Specifications in File...',
                                'types':[('All Files','*')],
                                'idir':fparts[0],
                                'ifile':fparts[1],
                                'callback':self.saveSpecs_cb,
                                'widgetwcfg':{'text':'Save',
                                              'width':12}},   
                        'gridcfg':{'row':6, 'column':0, 'columnspan':2},
                        })

        entries.append({'widgetType':Tkinter.Button, 'name':'i_clear',
                        'wcfg':{'text':'Clear',
                                'command':self.clearSpecs_cb,
                                'width':12},
                        'gridcfg':{'row':7, 'column':0, 'columnspan':2}
                        })

        for entry in entries:
            self.form.addEntry(entry)
            self.idf.entryByName[entry['name']] = entry
        self.iFormStatus['indexwidgets'] = 1
        self.iFormStatus['iwidgetsshow'] = 1
        self.idf.entryByName['SpecFileName']['widget'].configure(text = self.icurSpecFile)

    def column_cb(self, event=None):
        """ callback of radiobutton to use column format pdb specifications
        """
        Status = self.iFormStatus
        if Status['indexwidgets'] and Status['iwidgetsshow']:
            self.hide_widget_group('i')
        if Status['columnwidgets']:
            if not Status['cwidgetsshow']: self.show_widget_group('c')
        else:
            self.Specs = self.columnSpecs = ColumnSpecs()
            self.iFormStatus['columnspecs'] = 1
            self.createColumnWidgets()
        w = self.idf.entryByName['index_label']['widget'].configure(text = '')

    def index_cb(self, event=None):
        """ callback of radiobutton to use index format pdb specifications
        """
        Status = self.iFormStatus
        if Status['columnwidgets'] and Status['cwidgetsshow']:
            self.hide_widget_group('c')
        if Status['indexwidgets']:
            if not Status['iwidgetsshow']: self.show_widget_group('i')
        else:
            self.Specs = self.indexSpecs = IndexSpecs()
            self.iFormStatus['indexspecs'] = 1
            self.createIndexWidgets()
        self.indexLabel()
        
    def guiCallback(self, event=None, *args, **kw):

        text = '         1         2         3         4         5         6         7         8\n12345678901234567890123456789012345678901234567890123456789012345678901234567890'
        if self.active: return
        self.active = 1
        idf = self.idf = InputFormDescr(title = 'Enter Pdb Specifications:')
##          idf.append({'widgetType':'OpenButton', 'name':'readFile',
##                      'callback':self.fileinScrolledText_cb,
##                      'wcfg':{'text':'load pdb file...'},
##                      'gridcfg':{'row':0, 'column':0, 'sticky':'w', 'pady':5},
##                      'types':[('pdb files', '*.pdb'), ('all', '*')]
##                      })
        idf.append({'widgetType':LoadButton,
                    'name':'readFile',
                    'wcfg':{'buttonType':Tkinter.Button,
                            'title':'Load PDB File.',
                            'types':[('pdb files', '*.pdb'), ('all', '*')],
                            'callback':self.fileinScrolledText_cb,
                            'widgetwcfg':{'text':'load pdb file...'}},
                    'gridcfg':{'row':0, 'column':0, 'sticky':'w', 'pady':5}
                    })

        idf.append({'widgetType':Tkinter.Label, 'name':'FileName',
                    'gridcfg':{'row':0, 'column':0, 'columnspan':4}
                    })
        idf.append({'widgetType':Pmw.ScrolledText, 'name':'fileView',
                    'wcfg':{'labelpos':'nw', 'label_text':text,
                            'text_height':10, 'text_width':80,
                            'text_font':('Courier New',10),
                            'label_font':('Courier New',10),
                            'vscrollmode':'static'
                            },
                    'gridcfg':{'row':1, 'column':0, 'columnspan':4}#,
                               #'pady':5}
                    })
        idf.append({'widgetType':Tkinter.Label, 'name':'index_label',
                    'wcfg':{'font':('Courier New', 10)},
                    'gridcfg':{'row':2, 'column':0, 'columnspan':4,
                               'sticky':'w', 'pady':5}
                    })
        spectype = Tkinter.StringVar()
        idf.append({'widgetType':Tkinter.Radiobutton, 'name':'byColumn',
                    'wcfg':{'text':'Specify by column',
                            'variable':spectype,
                            'value':'c',
                            'command':self.column_cb},
                    'gridcfg':{'row':3, 'column':0}#, 'columnspan':2}
                    })
        idf.append({'widgetType':Tkinter.Radiobutton, 'name':'byIndex',
                    'wcfg':{'text':'Specify by index',
                            'variable':spectype,
                            'value':'i',
                            'command':self.index_cb},
                    'gridcfg':{'row':3, 'column':1}#, 'columnspan':2}
                    })
##          idf.append({'widgetType':'OpenButton', 'name':'load',
##                      'wcfg':{'text':'Load spec file...'},   
##                      'callback':self.loadSpecs_cb,
##                      'gridcfg':{'row':3, 'column':2, 'sticky':'ew'
##                                 },
##                                 #'columnspan':2},
##                      'idir':'.',
##                      'types':[('all', '*')]
##                      })
        idf.append({'widgetType':LoadButton,
                    'name':'load',
                    'wcfg':{'buttonType':Tkinter.Button,
                            'title':'Load Specification File ',
                            'idir':'.',
                            'types':[('all', '*')],
                            'callback':self.loadSpecs_cb,
                            'widgetwcfg':{'text':'Load spec file...'}},
                    'gridcfg':{'row':3, 'column':2, 'sticky':'ew'}
                    })

        idf.append({'widgetType':Tkinter.Label, 'name':'SpecFileName',
                    'gridcfg':{'row':4, 'column':0, 'columnspan':4,
                               'pady':5}
                    })
        idf.append({'name':'dismiss',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Dismiss',
                            'command': self.dismiss_cb},
                    'gridcfg':{'row':3, 'column':3, 'sticky':'ew'}#,
                               #'columnspan':2}
                    })
        
        self.form = self.vf.getUserInput(idf, modal = 0, blocking = 0)
        for N in range(4):
            self.form.f.columnconfigure(N, minsize=168)


    def indexLabel(self):
        """ creates a label that indexes each space-separated field """
        text = self.idf.entryByName['fileView']['widget'].get()
        lines = string.split(text, '\n')
        w = self.idf.entryByName['index_label']['widget']
        for l in lines:
            if l[:4]=='ATOM':
                labeltext = l
                recs = string.split(l)
                self.maxIndex = len(recs)-1
                j = 1
                for rec in recs[1:]:
                    if j > 9 and len(rec)==1:
                        rec = ' ' + rec
                        num = str(j)
                    else:
                        num = string.center('%i'%j, len(rec))
                    ind = string.find(labeltext, '%i'%(j-1))
                    if j==1: ind = 0
                    labeltext = labeltext[:ind] + \
                                string.replace(labeltext[ind:],rec,num,1)
                    j = j + 1
                labeltext = 'Index' + labeltext[5:]
                w.configure(text = labeltext)
                if hasattr(self, 'smallidf'):
                    self.smallidf.entryByName['index']['widget'].configure(validate = {'validator':'numeric', 'min':1, 'max':self.maxIndex})
                return
        w.configure(text = '')
        self.maxIndex = None
        if hasattr(self, 'smallidf'):
            self.smallidf.entryByName['index']['widget'].configure(validate = {'validator':'numeric', 'min':1, 'max':self.maxIndex})

            
    def fileinScrolledText_cb(self, filename, event = None):
        """ take a file and puts its text into the scrolled text box """
        scrolledText = self.idf.entryByName['fileView']['widget']
        scrolledText.clear()
        scrolledText.importfile(filename)
        self.idf.entryByName['FileName']['widget'].configure(text=filename)
        if self.iFormStatus['iwidgetsshow']:
            self.indexLabel()

    def dismiss_cb(self, event = None):
        self.form.destroy()
        self.active = 0
        if hasattr(self, 'smallform'):
            self.smallform.destroy()
            del self.smallform, self.smallidf
        self.iFormStatus['columnwidgets'] = 0
        self.iFormStatus['cwidgetsshow'] = 0
        self.iFormStatus['indexwidgets'] = 0
        self.iFormStatus['iwidgetsshow'] = 0

    def dismiss_smallform_cb(self, event = None):
        self.smallform.destroy()
        del self.smallform, self.smallidf
                                                     
definePdbSpecificationsGuiDescr = {'widgetType':'menuRoot', 'menuBarName':'File',
                                   'menuButtonName':'Define Pdb Specifications...',
                                   'index':0}

DefinePdbSpecificationsGUI = CommandGUI()
DefinePdbSpecificationsGUI.addMenuCommand('menuRoot', 'File',
                                          'Define Pdb Specifications...',
                                          index = 0)

commandList = [
    {'name':'genreadPDB', 'cmd':GenPDBReader(), 'gui':GenPDBReaderGUI},
    {'name':'defPdbSpecs', 'cmd':DefinePdbSpecifications(),
     'gui':DefinePdbSpecificationsGUI}
    ]

def initModule(viewer):

    for dict in commandList:
        viewer.addCommand( dict['cmd'], dict['name'], dict['gui'])


# self.loadCommand('genparserCommands', 'defPdbSpecs', 'Pmv')
# self.loadCommand('genparserCommands', 'genreadPDB', 'Pmv')
##  import pdb
##  pdb.run('self.commands["genreadPDB"].guiCallback()')
