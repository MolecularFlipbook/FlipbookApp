#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/povrayCommands.py,v 1.5 2008/09/16 17:27:18 sanner Exp $
#
# $Id: povrayCommands.py,v 1.5 2008/09/16 17:27:18 sanner Exp $
#

import Tkinter, os
from Pmv.mvCommand import MVCommand
from ViewerFramework.VFCommand import CommandGUI
##  from ViewerFramework.gui import InputFormDescr, InputForm
from mglutil.gui.InputForm.Tk.gui import InputFormDescr, InputForm

from mglutil.util.callback import CallBackFunction

from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser

import Pmw

class Povray(MVCommand):
    
    PovrayIncDir = '/usr/local/share/povray-3.7/include'
    
    def onAddCmdToViewer(self):
        self.form = None
        self.fileWritten = 0
        
##      def addInclude(self, value):
##          lb1 = value.entryByName['includes']['widget']
##          #print lb1.get()
##          self.fileWritten = 0
##          lb2 = value.entryByName['selectedIncludes']['widget']
##          lb2.insert('end', lb1.get()[0])

##      def removeInclude(self, value):
##          self.fileWritten = 0
##          lb2 = value.entryByName['selectedIncludes']['widget']
##          if lb2.get():
##              lb2.remove(lb2.get()[0])

##      def addGeometry(self, value):
##          self.fileWritten = 0
##          #print "value", value
##          lb1 = value.entryByName['geometries']['widget']
##          lb2 = value.entryByName['selectedGeometries']['widget']
##          lb2.insert('end', (lb1.get()[0],None))

##      def removeGeometry(self, value):
##          self.fileWritten = 0
##          #print "value", value
##          lb2 = value.entryByName['selectedGeometries']['widget']
##          if lb2.get():
##              lb2.remove(lb2.get()[0])

    def dismissCB(self):
        self.form.destroy()
        self.form = None


    def bindPigment(self, event=None):
##          e1 = self.form.descr.entryByName['pigment']['variable']
        e1 = self.form.descr.entryByName['pigment']['widget']
        prop = e1.get()
        g = self.form.descr.entryByName['selectedGeometries']['widget']
        geom = g.getAll(0)
        if len(geom) and len(prop):
##              self.properties[geom[0]]['pigment'] = prop
            self.properties[geom[0][0]]['pigment'] = prop


    def bindFinish(self, event=None):
        e1 = self.form.descr.entryByName['finish']['widget']
##          e1 = self.form.descr.entryByName['finish']['variable']
        prop = e1.get()
        g = self.form.descr.entryByName['selectedGeometries']['widget']
        geom = g.getAll(0)
        if len(geom) and len(prop):
##              self.properties[geom[0]]['finish'] = prop
            self.properties[geom[0][0]]['finish'] = prop

       
    def updateProps(self,event=None):
        self.fileWritten = 0
##          e1 = self.form.descr.entryByName['pigment']['variable']
##          e2 = self.form.descr.entryByName['finish']['variable']
##          g = self.form.descr.entryByName['selectedGeometries']['widget']
##          e1.set(self.properties[g.get()[0]]['pigment'])
##          e2.set(self.properties[g.get()[0]]['finish'])
        w1 = self.form.descr.entryByName['pigment']['widget']
        w2 = self.form.descr.entryByName['finish']['widget']
        g = self.form.descr.entryByName['selectedGeometries']['widget']
        w1.setentry(self.properties[g.get()[0]]['pigment'])
        w2.setentry(self.properties[g.get()[0]]['finish'])


    def runPovray(self, event=None):
        if not self.fileWritten:
            self.writeFile()

        fn = self.filename
        c = self.vf.GUI.VIEWER.cameras[0]
##          bin = self.form.descr.entryByName['povrayBin']['variable'].get()
##          args = self.form.descr.entryByName['povrayArgs']['variable'].get()
##          s = float(self.form.descr.entryByName['scaleImage']['variable'].get())
##          outf = self.form.descr.entryByName['imageFile']['variable'].get()
        bin = self.form.descr.entryByName['povrayBin']['widget'].get()
        args = self.form.descr.entryByName['povrayArgs']['widget'].get()
        s = float(self.form.descr.entryByName['scaleImage']['widget'].get())
        outf = self.form.descr.entryByName['imageFile']['widget'].get()
        cmd = '%s +L%s +W%d +H%d %s -I%s' % (bin, self.PovrayIncDir,
                                             int(s*c.width),
                                             int(s*c.height), args,
                                             self.filename)
        if outf!='':
            cmd = '%s +O%s'%(cmd, outf)
        print cmd

        import thread
        def renderIt(c, cmd):
            os.system(cmd)
            
        thread.start_new_thread( renderIt, (c,cmd) )


    def writeFile(self, event=None):
        from DejaVu.povray3 import PovRay
        p = PovRay()
        vi = self.vf.GUI.VIEWER

        # handle camera and background checkbutton
        wbg = self.form.descr.entryByName['wbg']['wcfg']['variable'].get()
        if wbg==1:
            col = vi.cameras[0].backgroundColor
            vi.cameras[0].Set(color=(1.,1.,1.,1.), tagModified=False)
##          sl = float(self.form.descr.entryByName['scaleLight']['variable'].get())
##          br = float(self.form.descr.entryByName['bondRadius']['variable'].get())
        sl = float(self.form.descr.entryByName['scaleLight']['widget'].get())
        br = float(self.form.descr.entryByName['bondRadius']['widget'].get())
        p.addCamera(vi.cameras[0], sl)
        if wbg==1: vi.cameras[0].Set(color=col, tagModified=False)

        # get list of selected geometries and add them
        g = self.form.descr.entryByName['selectedGeometries']['widget']
##          geoms = g.lb.get(0,'end')
        geoms = g.getAll(0)
        print 'aaaaaaaa', geoms
        #geoms = vi.getVisibleGeoms()

        for ge in geoms:
            p.addGeom(self.geomList[ge], self.properties[ge], br)

        # get the file namer and write file
##          fw = self.form.descr.entryByName['fileName']['textvariable']
        fw = self.form.descr.entryByName['fileName']['widget']
        fn = fw.get()
        if fn =='':
            fn = self.vf.askFileSave(idir='.', ifile=None,
                           types=[('Povray', '*.pov'), ('all files', '*.*')],
                           title='Save Povray scene')
##              fw.set(fn)
            fw.setentry(fn)

        if fn:
            self.filename=fn
            p.write(fn)
            self.fileWritten = 1

        
    def guiCallback(self):

        if self.form: return
        self.fileWritten = 0
        # get a list of povray include files
        inclist = os.listdir(self.PovrayIncDir)
        inclist.sort()
        
        # get a list of geometries
        self.geomList = {}
        self.properties = {}
        for m in self.vf.Mols:
            for g in m.geomContainer.geoms.values():
                if g.visible and g.__class__.__name__ != 'Geom':
                    name = '%s_%s'%(m.name,g.name)
                    self.geomList[name] = g
                    self.properties[name] = {'pigment':'',
                                             'finish':'specular 1 roughness 0.001 ambient 0.3'}

        for g in self.vf.GUI.VIEWER.rootObject.children:
            if g.visible and g.__class__.__name__ != 'Geom':
                name = g.name
                self.geomList[name] = g
                self.properties[name] = {'pigment':'',
                                         'finish':'specular 1 roughness 0.001 ambient 0.3'}
            
        idf = InputFormDescr(title ="PovRay")
        incEntries = map(lambda x: (x,None),inclist)
        idf.append({'name':'includes',
                    'widgetType':ListChooser,
                    'wcfg':{'entries': incEntries,
                            'title':'Select include files',
                            'mode':'extended',
                            'lbwcfg':{'height':5,'exportselection':0}},
                    'gridcfg':{'rowspan':4,'column':0,'row':0},
                    } )

##          idf.append({'name':'includes','title':'Select include files',
##                      'widgetType':'ListChooser',
##                      'entries': inclist,
##                      'mode':'extended',
##                      'gridcfg':{'rowspan':4,'column':0,'row':0},
##                      'lbwcfg':{'height':5}} )

        geomsEntries = map(lambda x: (x,None),self.geomList.keys())
##          idf.append({'name':'geometries',
##                      'widgetType':ListChooser,
##                      'wcfg':{'title':'Select geometries',
##                              'entries': geomsEntries,
##                              'lbwcfg':{'height':5}},
##                      'gridcfg':{'rowspan':4,'column':1,'row':0}}
##                       )
##          idf.append({'name':'geometries','title':'Select geometries',
##                      'widgetType':'ListChooser',
##                      'entries': self.geomList.keys(),
##                      'gridcfg':{'rowspan':4,'column':1,'row':0},
##                      'lbwcfg':{'height':5}} )

##          idf.append({'name':'AddIncButton',
##                      'widgetType':Tkinter.Button,
##                      'wcfg':{'text':'->',
##                              'command': CallBackFunction( self.addGeometry,
##                                                           (idf))},
##                      'gridcfg':{'column':2,'row':1}})

##          idf.append({'name':'RemoveIncButton',
##                      'widgetType':Tkinter.Button,
##                      'wcfg':{'text':'<-',
##                              'command': CallBackFunction( self.removeGeometry,
##                                                           (idf))},
##                      'gridcfg':{'column':2,'row':2}})

##          idf.append({'name':'selectedGeometries','title':'Selected geometries',
##                      'widgetType':'ListChooser',
##                      'entries': self.geomList.keys(),
##                      'lbwcfg':{'height':5},
##                      'gridcfg':{'rowspan':4, 'column':3, 'row':0}})
        idf.append({'name':'selectedGeometries',
                    'widgetType':ListChooser,
                    'wcfg':{'title':'Selected geometries',
                            'entries': geomsEntries,
                            'mode':'single',
                            'lbwcfg':{'height':5,'exportselection':0}},
                    'gridcfg':{'rowspan':4, 'column':3, 'row':0}})

##          idf.append({'name':'pigment','label':'Pigment   ',
##                      'widgetType':Tkinter.Entry, 'wcfg':{'width':40},
##                      'gridcfg':{'columnspan':2, 'column':0,
##                                 'row':4, 'sticky':'w'}})
        idf.append({'widgetType':Pmw.EntryField,
                    'name':'pigment',
                    'wcfg':{'labelpos':'w',
                            'label_text':'Pigment   ',
                            'validate':None,
                            'entry_width':40},
                    'gridcfg':{'columnspan':2, 'column':0,
                               'row':4, 'sticky':'w'}})
                    
##          idf.append({'name':'finish','label':'Finish      ',
##                      'widgetType':Tkinter.Entry, 'wcfg':{'width':40},
##                      'gridcfg':{'columnspan':2, 'column':0,
##                                 'row':5, 'sticky':'w'}})
        idf.append({'widgetType':Pmw.EntryField,
                    'name':'finish',
                    'wcfg':{'labelpos':'w',
                            'label_text':'Finish      ',
                            'validate':None,
                            'entry_width':40},
                    'gridcfg':{'columnspan':2, 'column':0,
                               'row':5, 'sticky':'w'}})

##          idf.append({'name':'scaleLight',
##                      'label':'Light scale factor', 'type':float,
##                      'widgetType':Tkinter.Entry, 'wcfg':{'width':5},
##                      'defaultValue': '2.0',
##                      'gridcfg':{'column':3, 'row':4, 'sticky':'e'}})
        idf.append({'name':'scaleLight',
                    'widgetType':Pmw.EntryField,
                    'type':float,
                    'wcfg':{'labelpos':'w',
                            'label_text':'Light scale factor',
                            'validate':'real',
                            'value':2.0,
                            'entry_width':5},
                    'gridcfg':{'column':3, 'row':4, 'sticky':'e'}})

##          idf.append({'name':'scaleImage',
##                      'label':'scale Image', 'type':float,
##                      'widgetType':Tkinter.Entry, 'wcfg':{'width':5},
##                      'defaultValue': '1.0',
##                      'gridcfg':{'column':3, 'row':5, 'sticky':'e'}})
        idf.append({'name':'scaleImage',
                    'widgetType':Pmw.EntryField,
                    'type':float,
                    'wcfg':{'labelpos':'w',
                            'label_text':'scale Image', 
                            'entry_width':5,
                            'validate':'real',
                            'value':1.0},
                    'gridcfg':{'column':3, 'row':5, 'sticky':'e'}})

##          idf.append({'name':'bondRadius','label':'bond Radius', 'type':float,
##                      'widgetType':Tkinter.Entry, 'wcfg':{'width':5},
##                      'defaultValue': '0.15',
##                      'gridcfg':{'column':3, 'row':6, 'sticky':'e'}})
        idf.append({'name':'bondRadius',
                    'widgetType':Pmw.EntryField,
                    'type':float,
                    'wcfg':{'labelpos':'w',
                            'label_text':'bond Radius', 
                            'entry_width':5,
                            'validate':'real',
                            'value': 0.15},
                    'gridcfg':{'column':3, 'row':6, 'sticky':'e'}})

##          idf.append({'name':'fileName','label':'File Name',
##                      'widgetType':Tkinter.Entry,
##                      'defaultValue':'test.pov',
##                      'wcfg':{'width':40},
##                      'gridcfg':{'columnspan':2,'column':0,'row':6,'sticky':'w'}})
        idf.append({'name':'fileName',
                    'widgetType':Pmw.EntryField,
                    'wcfg':{'labelpos':'w',
                            'label_text':'File Name',
                            'entry_width':40,
                            'value':'test.pov',},
                    'gridcfg':{'columnspan':2,'column':0,'row':6,'sticky':'w'}})

##          idf.append({'name':'povrayBin','label':'Povray binary',
##                      'widgetType':Tkinter.Entry,
##                      'defaultValue':'povray',
##                      'wcfg':{'width':40},
##                      'gridcfg':{'columnspan':2,'column':0,'row':7,'sticky':'w'}})
        idf.append({'name':'povrayBin',
                    'widgetType':Pmw.EntryField,
                    'wcfg':{'labelpos':'w',
                            'label_text':'Povray binary',
                            'value':'povray',
                            'entry_width':40},
                    'gridcfg':{'columnspan':2,'column':0,
                               'row':7,'sticky':'w'}})

        idf.append({'name':'wbg',
                    'widgetType':Tkinter.Checkbutton,
                    'defaultValue':1,
                    'wcfg':{'text':'White Background',
                            'variable': Tkinter.IntVar()},
                    'gridcfg':{'column':3, 'row':7,'sticky':'e'}})

##          idf.append({'name':'povrayArgs','label':'cmdline arguments',
##                      'widgetType':Tkinter.Entry,
##                      'defaultValue':'+D0 +P +X -V +FN +QR',
##                      'wcfg':{'width':40},
##                      'gridcfg':{'columnspan':2,'column':0,'row':8,'sticky':'w'}})
        idf.append({'name':'povrayArgs',
                    'widgetType':Pmw.EntryField,
                    'wcfg':{'labelpos':'w',
                            'label_text':'cmdline arguments',
                            'value':'+D0',# +P +X -V +FN +QR',
                            'entry_width':40},
                    'gridcfg':{'columnspan':2,'column':0,
                               'row':8,'sticky':'w'}})

##          idf.append({'name':'imageFile','label':'image file',
##                      'widgetType':Tkinter.Entry,
##                      'wcfg':{'width':40},
##                      'gridcfg':{'columnspan':2,'column':0,'row':9,'sticky':'w'}})
        idf.append({'name':'imageFile',
                    'widgetType':Pmw.EntryField,
                    'wcfg':{'labelpos':'w',
                            'label_text':'image file',
                            'entry_width':40},
                    'gridcfg':{'columnspan':2,'column':0,
                               'row':9,'sticky':'w'}})

        idf.append({'name':'WriteFile',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'WriteFile','command': self.writeFile},
                    'gridcfg':{'columnspan':1,'column':0,
                               'row':10,'sticky':'ew'}})

        idf.append({'name':'Render',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Render',
                            'command': CallBackFunction( self.runPovray,
                                                         (idf))},
                    'gridcfg':{'columnspan':2,'column':1,
                               'row':10,'sticky':'ew'}})

        idf.append({'name':'Dismiss',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Dismiss',
                            'command':self.dismissCB},
                    'gridcfg':{'column':3, 'row':10,'sticky':'ew'}})

        self.form = self.vf.getUserInput(idf, modal = 0, blocking = 0)
        lb = idf.entryByName['selectedGeometries']['widget'].lb
        lb.bind("<ButtonRelease-1>", self.updateProps, '+')

        e1 = idf.entryByName['pigment']['widget']
        e1.bind("<Return>", self.bindPigment)
        
        e2 = idf.entryByName['finish']['widget']
        e2.bind("<Return>", self.bindFinish)
        
povrayGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                  'menuButtonName':'File',
                  'menuEntryLabel':'Povray', 'index':0}

PovrayGUI = CommandGUI()
PovrayGUI.addMenuCommand('menuRoot', 'File', 'Povray', index = 0)

commandList = [
    {'name':'povray','cmd': Povray(), 'gui': PovrayGUI},
    ]


def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
