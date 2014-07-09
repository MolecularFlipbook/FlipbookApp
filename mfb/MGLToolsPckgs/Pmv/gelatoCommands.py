#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/gelatoCommands.py,v 1.2 2009/08/25 22:12:40 autin Exp $
#
# $Id: gelatoCommands.py,v 1.2 2009/08/25 22:12:40 autin Exp $
#

import Tkinter, os
from Pmv.mvCommand import MVCommand
from ViewerFramework.VFCommand import CommandGUI
##  from ViewerFramework.gui import InputFormDescr, InputForm
from mglutil.gui.InputForm.Tk.gui import InputFormDescr, InputForm

from mglutil.util.callback import CallBackFunction

from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser
from DejaVu.gelato import Shader

import Pmw

class Gelato(MVCommand): 
    def onAddCmdToViewer(self):
        self.form = None
	self.formS = None
        self.fileWritten = 0
	self.shader_edited = False
        self.g=None
	self.shadDic=Shader.ShaderDic

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
        w1 = self.form.descr.entryByName['pigment']['widget']
        w2 = self.form.descr.entryByName['finish']['widget']
        self.g = self.form.descr.entryByName['selectedGeometries']['widget']

    def applyShader(self,event=None):
        g = self.form.descr.entryByName['selectedGeometries']['widget']
        geoms = g.get()
        sh = self.form.descr.entryByName['pigment']['widget'].get()
	for g in geoms :
		self.properties[g]['pigment']=sh

    def runGelato(self, event=None):
        if not self.fileWritten:
            self.writeFile()

        fn = self.filename
        c = self.vf.GUI.VIEWER.cameras[0]
        bin = self.form.descr.entryByName['gelatoBin']['widget'].get()
        args = self.form.descr.entryByName['gelatoArgs']['widget'].get()
        s = float(self.form.descr.entryByName['scaleImage']['widget'].get())
        outf = self.form.descr.entryByName['imageFile']['widget'].get()
        cmd = '%s %s %s' % (bin, args,self.filename)
        if outf!='':
            cmd = '%s -o %s'%(cmd, outf)
        print cmd

        import thread
        def renderIt(c, cmd):
            os.system(cmd)
            
        thread.start_new_thread( renderIt, (c,cmd) )


    def writeFile(self, event=None):
        from DejaVu.gelato import Gelato
        G = Gelato(shaderD=self.shadDic)
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
	sh = self.form.descr.entryByName['pigment']['widget'].get()
        G.addCamera(vi.cameras[0], sl)
	G.addBackground(vi.cameras[0])
	if sh == "occlusion" : G.addShader(sh)
	#G.addLight()

        if wbg==1: vi.cameras[0].Set(color=col, tagModified=False)

	self.updateProps()
        geoms = self.g.get()
        print 'aaaaaaaa', geoms
        print 'aaaaaaaa', self.properties
        #geoms = vi.getVisibleGeoms()

	#'catmull-clark'#'linear'
	interpolate = 'linear'
	if self.form.descr.entryByName['inter']['wcfg']['variable'].get() == 1 : interpolate = 'catmull-clark'
        for ge in geoms:
            print 
            G.addGeom(self.geomList[ge], self.properties[ge], br,interpolate)
	#add the last line : Render()
	G.addRender()
        # get the file namer and write file
##          fw = self.form.descr.entryByName['fileName']['textvariable']
        fw = self.form.descr.entryByName['fileName']['widget']
        fn = fw.get()
        if fn =='':
            fn = self.vf.askFileSave(idir='.', ifile=None,
                           types=[('Gelato', '*.pyg'), ('all files', '*.*')],
                           title='Save Gelato scene')
##              fw.set(fn)
            fw.setentry(fn)

        if fn:
            self.filename=fn
            G.write(fn)
            self.fileWritten = 1

    def helpShader(self):
		name=self.formS.descr.title
		import webbrowser
		dirG = os.environ.get('GELATOHOME')
		#url = dirG+"/doc/shaders/index.html"
		#webbrowser.open_new_tab(url)
		if name == "soapbubble" : name = "glass"
		url = dirG+"/doc/shaders/"+name+".html"
		webbrowser.open_new_tab(url)		

    def helpGelato(self):
		import webbrowser
		dirG = os.environ.get('GELATOHOME')
		url = dirG+"/doc/index.html"
		webbrowser.open_new_tab(url)

    def editShader(self):
		self.shader_edited= True
		shname = self.form.descr.entryByName['pigment']['widget'].get()	
		shaderP = self.shadDic[shname]
		idf = InputFormDescr(title =shname)
		k=0
		for i in shaderP : 
			W=4
			tmp=i.replace("\"","").split(",")
			P=tmp[0].split(" ")
			V=tmp[1]
			if P[0] == "string" : 
				P[0]="str"
				W=16
			else :	V=eval(V)	
			idf.append({	'name':P[1],
                    			'widgetType':Pmw.EntryField,
                    			'type':eval(P[0]),
                    			'wcfg':{'labelpos':'w',
                        		'label_text':tmp[0],
                            		'validate':'real',
                            		'value':V,
                            		'entry_width':W},
                    			'gridcfg':{'column':0, 'row':k, 'sticky':'w'}})
			k=k+1
      		idf.append({'name':'Set',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'ApplyChange','command': self.SetShader},
                    'gridcfg':{'column':0,
                               'row':k,'sticky':'ew'}})
	        idf.append({'name':'help',
                    'widgetType':Tkinter.Button,
                    'defaultValue':0,
                    'wcfg':{'text':'Help','command': self.helpShader},
                    'gridcfg':{'column':1, 'row':k,'sticky':'ew'}})

		self.formS = self.vf.getUserInput(idf, modal = 0, blocking = 0)
		
    def SetShader(self):
	name=self.formS.descr.title
	shaderDesc = self.shadDic[name]
	k=0
	for i in shaderDesc :
		tmp=i.replace("\"","").split(",")
		P=tmp[0].split(" ")
		V=tmp[1]
		pname=P[1]
		value=self.formS.descr.entryByName[P[1]]['widget'].get()
		if P[0] == "string" : self.shadDic[name][k]="\""+P[0]+" "+P[1]+"\",\""+value+"\""
		else : self.shadDic[name][k]="\""+P[0]+" "+P[1]+"\","+str(value)
		print self.shadDic[name][k]
		k=k+1

    def guiCallback(self):

        if self.form: return
        self.fileWritten = 0
        
        # get a list of geometries
        self.geomList = {}
        self.properties = {}
        for m in self.vf.Mols:
            for g in m.geomContainer.geoms.values():
                if g.visible and g.__class__.__name__ != 'Geom':
                    name = '%s_%s'%(m.name,g.name)
                    self.geomList[name] = g
                    self.properties[name] = {'pigment':'',
                                             'finish':''}

        for g in self.vf.GUI.VIEWER.rootObject.children:
            if g.visible and g.__class__.__name__ != 'Geom':
                name = g.name
                self.geomList[name] = g
                self.properties[name] = {'pigment':'',
                                         'finish':''}
            
        idf = InputFormDescr(title ="Gelato")

        geomsEntries = map(lambda x: (x,None),self.geomList.keys())
        idf.append({'name':'selectedGeometries',
                    'widgetType':ListChooser,
                    'wcfg':{'title':'Selected geometries',
                            'entries': geomsEntries,
                            'mode':'multiple',
                            'lbwcfg':{'height':5,'exportselection':0}},
                    'gridcfg':{'rowspan':4, 'column':0, 'row':0}})
	from DejaVu.gelato import Shader
	#shaderD = Shader.ShaderDic
	#shaderEntries = map(lambda x: (x,None),Shader.ShaderDic.keys())
	shaderEntries = Shader.ShaderDic.keys()

        idf.append({'widgetType':Pmw.ComboBox,
                    'name':'pigment',
                    'wcfg':{'labelpos':'w',
                            'label_text':'Shader',
                            'scrolledlist_items' : shaderEntries,
			    'scrolledlist_listbox_width':7,
			    #'width':40
                            },
                    'gridcfg':{'columnspan':2, 'column':0,
                               'row':4, 'sticky':'w'}})
        idf.append({'name':'Apply',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'ApplyToSelection','command': self.applyShader},
                    'gridcfg':{'column':1,
                               'row':4,'sticky':'w'}})

        idf.append({'name':'edit',
                    'widgetType':Tkinter.Button,
                    'defaultValue':0,
                    'wcfg':{'text':'Edit','command': self.editShader},
                    'gridcfg':{'column':2, 'row':4,'sticky':'w'}})

        idf.append({'widgetType':Pmw.EntryField,
                    'name':'finish',
                    'wcfg':{'labelpos':'w',
                            'label_text':'Finish      ',
                            'validate':None,
                            'entry_width':40},
                    'gridcfg':{'columnspan':2, 'column':0,
                               'row':5, 'sticky':'w'}})

        idf.append({'name':'scaleLight',
                    'widgetType':Pmw.EntryField,
                    'type':float,
                    'wcfg':{'labelpos':'w',
                            'label_text':'Light scale factor',
                            'validate':'real',
                            'value':2.0,
                            'entry_width':5},
                    'gridcfg':{'column':3, 'row':4, 'sticky':'e'}})

        idf.append({'name':'scaleImage',
                    'widgetType':Pmw.EntryField,
                    'type':float,
                    'wcfg':{'labelpos':'w',
                            'label_text':'scale Image', 
                            'entry_width':5,
                            'validate':'real',
                            'value':1.0},
                    'gridcfg':{'column':3, 'row':5, 'sticky':'e'}})

        idf.append({'name':'bondRadius',
                    'widgetType':Pmw.EntryField,
                    'type':float,
                    'wcfg':{'labelpos':'w',
                            'label_text':'bond Radius', 
                            'entry_width':5,
                            'validate':'real',
                            'value': 0.15},
                    'gridcfg':{'column':3, 'row':6, 'sticky':'e'}})

        idf.append({'name':'fileName',
                    'widgetType':Pmw.EntryField,
                    'wcfg':{'labelpos':'w',
                            'label_text':'File Name',
                            'entry_width':40,
                            'value':'test.pyg',},
                    'gridcfg':{'columnspan':2,'column':0,'row':6,'sticky':'w'}})

        idf.append({'name':'gelatoBin',
                    'widgetType':Pmw.EntryField,
                    'wcfg':{'labelpos':'w',
                            'label_text':'Gelato binary',
                            'value':'gelato',
                            'entry_width':40},
                    'gridcfg':{'columnspan':2,'column':0,
                               'row':7,'sticky':'w'}})

        idf.append({'name':'wbg',
                    'widgetType':Tkinter.Checkbutton,
                    'defaultValue':1,
                    'wcfg':{'text':'White Background',
                            'variable': Tkinter.IntVar()},
                    'gridcfg':{'column':3, 'row':7,'sticky':'e'}})

        idf.append({'name':'inter',
                    'widgetType':Tkinter.Checkbutton,
                    'defaultValue':0,
                    'wcfg':{'text':'catmull-clark',
                            'variable': Tkinter.IntVar()},
                    'gridcfg':{'column':3, 'row':8,'sticky':'e'}})


        idf.append({'name':'gelatoArgs',
                    'widgetType':Pmw.EntryField,
                    'wcfg':{'labelpos':'w',
                            'label_text':'cmdline arguments',
                            'value':'-iv',# +P +X -V +FN +QR',
                            'entry_width':40},
                    'gridcfg':{'columnspan':2,'column':0,
                               'row':8,'sticky':'w'}})

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
                    'gridcfg':{'column':0,
                               'row':10,'sticky':'ew'}})

        idf.append({'name':'Render',
                    'widgetType':Tkinter.Button,
                    'wcfg':{'text':'Render',
                            'command': CallBackFunction( self.runGelato,
                                                         (idf))},
                    'gridcfg':{'column':1,
                               'row':10,'sticky':'ew'}})
	idf.append({'name':'help',
                    'widgetType':Tkinter.Button,
                    'defaultValue':0,
                    'wcfg':{'text':'Help','command': self.helpGelato},
                    'gridcfg':{'column':2, 'row':10,'sticky':'ew'}})

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
        
GelatoGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                  'menuButtonName':'File',
                  'menuEntryLabel':'Gelato', 'index':0}

GelatoGUI = CommandGUI()
GelatoGUI.addMenuCommand('menuRoot', 'File', 'Gelato', index = 0)

commandList = [
    {'name':'gelato','cmd': Gelato(), 'gui': GelatoGUI},
    ]


def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
