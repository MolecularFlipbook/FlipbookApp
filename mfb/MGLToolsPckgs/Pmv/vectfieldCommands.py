## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Alexandre T. GILLET
#
# TSRI 2003
#
#############################################################################
#
#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/vectfieldCommands.py,v 1.13 2007/12/03 19:17:15 sargis Exp $
#
# $Id: vectfieldCommands.py,v 1.13 2007/12/03 19:17:15 sargis Exp $
#
#
#
#
from ViewerFramework.VFCommand import CommandGUI
from Pmv.mvCommand import MVCommand
from mglutil.gui.InputForm.Tk.gui import InputFormDescr,InputForm
from  mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser, ExtendedSliderWidget
from mglutil.util.callback import CallBackFunction
import Tkinter,Pmw
import os,sys,types,string,time,math
from DejaVu.Spheres import Spheres
from opengltk.OpenGL import GL
import numpy.oldnumeric as Numeric
from DejaVu.colorTool import RedWhiteBlueRamp, Map
from DejaVu.Arrows import Arrows

from ViewerFramework.VFGUI import dirChoose
class loadVect(MVCommand):
    """ Command to load a Vect field for a molecule."""

    def __init__(self):
        MVCommand.__init__(self)

    def onAddCmdToViewer(self):
        if not hasattr(self.vf,'vectfield'):
            self.vf.vectfield = {}

    def doit(self,name, folderPath):
        """name,file"""
        from glob import glob
        filelist = glob(folderPath+'/*.vu')  
            
        vi  = self.vf.GUI.VIEWER
        hasVect=0
        for i in vi.rootObject.AllObjects():
            if i.name == name:hasVect=1
        if hasVect:
            self.vf.loadVUFile(name,filelist, topCommand = 0) 
        else:
            self.createGeometries(name)
            self.vf.loadVUFile(name,filelist, topCommand = 0)

    def __call__(self, name,folderPath,**kw):
        """
        None <- loadVect(nodes, file,**kw)
        name: name of the vect obj
        folderPath   : Path to folder of *.vu
        """
        
        if not name: return
        if not folderPath: return
        apply(self.doitWrapper, (name,folderPath), kw)

    def onAddObjectToViewer(self, obj):
        # private flag to specify whether or not the geometries for the SS
        # have been created.
        obj.__hasVectField = 0

    def createGeometries(self, name):
        from DejaVu.Geom import Geom
        t = Geom(name,shape=(0,0), protected=True)
        self.vf.vectfield[name]=t
        t.replace = True
        self.vf.GUI.VIEWER.AddObject(t, redo=0)

    def buildFormDescr(self,formName):
        if formName == "enterName":
            ifd  =InputFormDescr(title = "Pick Vect Name")
            vectNames = self.vf.vectfield.keys()
            ifd.append({'widgetType':Pmw.ComboBox,
                        'name':'vectName',
                        'required':1,
                        'tooltip': "Please type-in a new name or chose one from the list below\n '_' are not accepted",
                        'wcfg':{'labelpos':'nw',
                                'label_text':'VectField Name: ',
                                'entryfield_validate':self.entryValidate,
                                'scrolledlist_items':vectNames,
                                },
                        'gridcfg':{'sticky':'we'}})
            return ifd

    def entryValidate(self, text):
        """
        Method to validate the name of the msms surface. This name
        will be used by other command to build Pmw widget so it can't
        contain an '_'.
        """
        if '_' in text:
            return Pmw.ERROR
        else:
            return Pmw.OK
    
    def guiCallback(self,**kw):
        val = self.showForm('entrerName')
        if not val:return
        vectName = val['vectName'][0]
        folderPath = dirChoose(self.vf.GUI.ROOT)
        if folderPath:
            #print folderPath,type(folderPath)
            ## get all the *.vu file from folderPath,
            ## create filelist
            folderPath =str(folderPath)
            apply(self.doitWrapper, (vectName,folderPath),kw)

##             from glob import glob
##             filelist = glob(str(folderPath)+'/*.vu')  
##             if filelist:
##                 apply(self.doitWrapper, (vectName,filelist),kw)
            

##     def guiCallback(self,**kw):
##         folderPath = dirChoose(self.vf.GUI.ROOT)
##         if folderPath:
##             print folderPath,type(folderPath)
##             ## get all the *.vu file from folderPath,
##             ## create filelist
##             from glob import glob
##             filelist = glob(str(folderPath)+'/*.vu')  
##             if filelist:
##                 if self.vf.userpref['expandNodeLogString']['value'] == 0:
##                     self.nodeLogString = "self.getSelection()"
##                 apply(self.doitWrapper, (self.vf.getSelection(),filelist),kw)
            


loadVectGUI = CommandGUI()
loadVectGUI.addMenuCommand('menuRoot', 'VectField', 'loadVect')

####### VU Field ###################
class loadVUFile(MVCommand):
    """ Command  to a load a VU file to display"""

    def __init__(self):
        MVCommand.__init__(self)
        self.fileTypes =[('VU file',"*.vu")]
        self.fileBrowserTitle = "Read VU File"
        self.lastDir = "."
        
        
    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('loadVect'):
            self.vf.loadCommand('vectfieldCommands', 'loadVect', 'Pmv',
                                topCommand = 0)
            
    def buildFormDescr(self,formName):
        if formName == "Vectfield":
           ifd  =InputFormDescr(title = "Choose Vect Field")
           vectList = []
           for key in self.vf.vectfield.keys():
               vectList.append((key,None))
           ifd.append({'widgetType':ListChooser,
                       'name':'vectObj',
                       'wcfg':{'title':'Pick grid',
                               'entries':vectList,
                               'mode':'single',
                               'lbwcfg':{'height':4},},
                       'gridcfg':{'sticky':'wens', 'column':100,
                                  'rowspan':10}})   
 
           return ifd

    def guiCallback(self,event=None, *args, **kw):

        if len(self.vf.vectfield.keys())==0:
            t='no vectfield currently loaded'
            self.warningMsg(t)
            return
 
        val = self.showForm('Vectfield')
        if len(val)>0 and len(val['vectObj'])>0:
            field = val['vectObj'][0]

        file = self.vf.askFileOpen(types=self.fileTypes,
                                       idir = self.lastDir,
                                       title=self.fileBrowserTitle)

        if file != None:
            self.lastDir = os.path.split(file)[0]
            file =[file]
            self.vf.tryto(self.doitWrapper,field, file)
        return

    def loadFile(self,filename):
        """ load the vector pts and color from a file .vu """
        file = open(filename,'r')
        val = file.readlines()
        file.close()
        # shtovu colroname     rgb
        # 120    bright red    1 .4 .4
        # 129    orange        1 .5 0
        # 150    yellow        1 1  0
        # 240    green         .3 1 .3
        # 300    cyan          0  1  1

        colormap = {120:(1,.4,.4,1),129:(1.,.5,0.,1),150:(1.,1.,0.,1),
                    240:(.3,1.,.3,1.),300:(0.,1.,1.,1.)}

        i = 0
        vertices =[]
        faces = []
        materials =[]
        
        for l in val:
            x1 = (float) (string.split(string.strip(l))[0])
            y1 = (float) (string.split(string.strip(l))[1])
            z1 = (float) (string.split(string.strip(l))[2])
            x2 = (float) (string.split(string.strip(l))[3])
            y2 = (float) (string.split(string.strip(l))[4])
            z2 = (float) (string.split(string.strip(l))[5])
            color = (int) (string.split(string.strip(l))[6])
            pts1 = (x1,y1,z1)
            pts2=(x2,y2,z2)

            vertices.append(pts1)
            vertices.append(pts2)
            faces.append((i,i+1))
            materials.append(colormap[color])
            i = i+2

        return (vertices,faces,materials)


    def doit(self,vectName,filelist):
        viewer = self.vf.GUI.VIEWER
        for file in filelist:
            f = os.path.split(file)[1]
            name = string.split(f,'.')[0]
            #field= VectField(name=filename)
            #field.loadVUfile(filelist)
            vertices,faces,materials= self.loadFile(file)
            #obj.Set(vertices=self.vertices,faces=self.faces,
            #        materials=self.materials, tagModified=False)
            obj = Arrows(name,vertices=vertices,faces=faces,
                         materials=materials,inheritMaterial=0,
                         inheritLineWidth=0, lineWidth=3)
            
            if self.vf.vectfield.has_key(vectName):
                vect = self.vf.vectfield[vectName]
            else:
                t = 'No vector field of Name,%s found'%vectName
                self.warningMsg(t)
                return
            obj.replace = True
            viewer.AddObject(obj, parent=vect)
            viewer.deleteOpenglList()
            viewer.Redraw()
            

    def __call__(self, vectName,filelist,**kw):
        """None <- loadVUFile(vectName, filelist,**kw)
        vectName: Name of the vectobj 
        filelist    :list of  file *.vu holding the coordinate
        a the vector to display
        """
        if not vectName: return
        if not filelist: return
        apply(self.doitWrapper, (vectName,filelist), kw)
        
loadVUFileGUI = CommandGUI()
loadVUFileGUI.addMenuCommand('menuRoot', 'VectField', 'loadVU')



commandList = [

    {'name':'loadVect','cmd':loadVect(),'gui':loadVectGUI},
    {'name':'loadVUFile','cmd':loadVUFile(),'gui':loadVUFileGUI},
 
    ]



def initModule(vf):
    
    for dict in commandList:
        vf.addCommand(dict['cmd'],dict['name'],dict['gui'])
































