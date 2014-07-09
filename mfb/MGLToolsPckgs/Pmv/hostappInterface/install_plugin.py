#!/usr/bin/python2.5
import os,sys,glob
import re
import time
import urllib
import tarfile
import shutil
COPY="cp"
geturl=None

def _reporthook(numblocks, blocksize, filesize, url=None, pb = None):
    #print "reporthook(%s, %s, %s)" % (numblocks, blocksize, filesize)
    base = os.path.basename(url)
    #XXX Should handle possible filesize=-1.
    try:
        percent = min((numblocks*blocksize*100)/filesize, 100)
    except:
        percent = 100
    if numblocks != 0:
        sys.stdout.write("\b"*70)
    sys.stdout.write("%-66s%3d%%" % (base, percent))
    if pb is not None:
        pb.set(percent)

def geturl(url, dst,pb=None):
    print "get url '%s' to '%s'" % (url, dst)
    doit = True
    try :
        doit = sys.stdout.isatty()
    except:
        doit = False
    if doit:
        urllib.urlretrieve(url, dst,
                           lambda nb, bs, fs, url=url: _reporthook(nb,bs,fs,url,pb))
        sys.stdout.write('\n')
    else:
       urllib.urlretrieve(url, dst)

if __name__ == '__main__':
    path = os.path.abspath(os.curdir)
    if path == os.getenv("HOME") or path == os.getenv("HOMEPATH"):
        #we are in the local user directory, how to get back to MGLRoot:
        #use the sys.argv
        epmvdir=os.path.split(sys.argv[0])
        path = os.path.abspath(epmvdir[0])
        os.chdir(path)
    if sys.platform == 'win32': 
        os.chdir('../../')
    else :
        os.chdir('../')
    mgltoolsDir=os.path.abspath(os.curdir)
    print mgltoolsDir
    sys.path.append(mgltoolsDir)
    sys.path.append(mgltoolsDir+os.sep+'PIL')
    #import comput_util as util
    os.chdir(path)
    
    if sys.platform == 'win32':
        #need to patch MGLTools first
        #first patch MGLTools
        #check if we need to patch
        patch=os.path.isfile(mgltoolsDir+os.sep+"patched")
        if not patch :
            print "Patching MGLToolsPckgs with python2.6 system dependant modules"
            print mgltoolsDir+os.sep
            patchpath = mgltoolsDir+os.sep
            URI="http://mgldev.scripps.edu/projects/ePMV/patchs/depdtPckgs.tar"
            tmpFileName = mgltoolsDir+os.sep+"depdtPckgs.tar"
            #urllib.urlretrieve(URI, tmpFileName)
            geturl(URI, tmpFileName)
            TF=tarfile.TarFile(tmpFileName)
            TF.extractall(patchpath)
            #create the pacthed file
            f=open(mgltoolsDir+os.sep+"patched","w")
            f.write("MGL patched!")
            f.close()
        COPY="xcopy /s"

try:
    from Tkinter import *
    import Image, ImageTk
    from tkFileDialog   import askdirectory
    from mglutil.gui.BasicWidgets.Tk.progressBar import ProgressBar
    from mglutil.gui.BasicWidgets.Tk.multiButton import MultiRadiobuttons
except:
    print "noTK"
#utility
from mglutil.util import packageFilePath

#note : do we ask for Modeller, PyRosetta,etc...?
#seems yes, so should have a extension frames where user defeine path to extension
#as AR and AF are part of MGLToolsPckgs no need to check them
class Installer:
    
    def __init__(self, master=None,color='white',gui=True):
        self.automaticSearch = False
        self.plateform = sys.platform
        self.rootDirectory="/"
        self.sharedDirectory=""
        self.userDirectory=""
        self.progDirectory=""
        self.SetDirectory()
        self.bgcolor=color
        import Pmv.hostappInterface as epmv
        self.currDir=epmv.__path__[0]
        os.chdir(self.currDir)
        os.chdir('../../../')
        self.mgltoolsDir=os.path.abspath(os.curdir)
        self.softdir=["","","",""]
        self.MODES = ["Blender","Cinema4D","Cinema4DR12","Maya"]
        self.extensions = ["modeller","pyrosetta","hollow"]
        self.extdir=["","",""]
        self.cb = [self.getBlenderDir,self.getC4dDir,self.getC4dr12Dir,self.getMayaDir]
        self.funcInstall=[self.installBlender,self.installC4d,self.installC4dr12,self.installMaya]    
        self.v = []
        self.dir = []
        self.log = ""
        self.msg = None
        self.chooseDir=None
        self.gui=gui
        self.curent =0
        self.choosenDir = None
        self.master = master
        if self.gui:
            self.choosenDir = StringVar()
            master.configure(bg=self.bgcolor)
            self.frame = Frame(master,bg=self.bgcolor)
            self.frame.pack()       
            self.imageFile = self.mgltoolsDir+'/MGLToolsPckgs/Pmv/hostappInterface/images/banner.jpg'
            self.bannerImage = Image.open(self.imageFile)
            self.bannerTk = ImageTk.PhotoImage(self.bannerImage)
            self.label_banner = Label(self.frame, image=self.bannerTk,bg=self.bgcolor)
            self.label_banner.place(x=0,y=0,width=self.bannerImage.size[0],height=self.bannerImage.size[1])
            self.label_banner.pack(side=TOP)

            for i,text in enumerate(self.MODES):
                frame = Frame(master,bg=self.bgcolor)
                frame.pack()
                self.v.append(IntVar())
                self.dir.append(StringVar())
                b = Checkbutton(frame, text=text,
                            variable=self.v[i],bg=self.bgcolor,command=self.cb[i])
                b.pack(side=LEFT,fill=X,anchor=E)#,anchor=W
                w = Label(frame,textvariable=self.dir[i],bg=self.bgcolor)
                self.dir[i].set(text+"_dir")
                w.pack(side=LEFT,fill=X,anchor=E)#,anchor=E
#
#            for i,text in enumerate(self.MODES):
#                self.v.append(IntVar())
#                self.dir.append(StringVar())
#                b = Checkbutton(self.frame, text=text,
#                            variable=self.v[i],bg=self.bgcolor,command=self.cb[i])
#                b.pack(side=BOTTOM,anchor=W)
#    
#            for i,text in enumerate(self.MODES):
#                w = Label(self.frame,textvariable=self.dir[i],bg=self.bgcolor)
#                self.dir[i].set(text+"_dir")
#                w.pack(side=TOP,anchor=E)
#                i=i+1
#            
            frame2 = Frame(master,bg=self.bgcolor)
            frame2.pack()
            self.buttonSEARCH = Button(frame2, text="SEARCH_DIR", fg="red",
                                    command=self.findDirectories,bg=self.bgcolor)
            self.buttonSEARCH.pack(side=LEFT)
            
            self.buttonDIR = Button(frame2, text="SET_DIR", fg="red",
                                    command=self.setDirectory,bg=self.bgcolor)
            self.buttonDIR.pack(side=LEFT)
     
            self.buttonOK = Button(frame2, text="INSTALL", fg="red", 
                                   command=self.install,bg=self.bgcolor)
            self.buttonOK.pack(side=LEFT)
    
            self.buttonQuit = Button(frame2, text="QUIT", fg="red", 
                                     command=self.quit,bg=self.bgcolor)
            self.buttonQuit.pack(side=LEFT)
            
            frame3 = Frame(master,bg=self.bgcolor)
            frame3.pack()
    
            self.progressbar = ProgressBar(master=frame3, labelside='left')
            self.progressbar.configure(height=20, width=200, init=1, mode='percent',
                           labeltext='')
            self.pbval = 0
            self.msg = StringVar()
            self.message=Label(frame3,textvariable=self.msg,bg=self.bgcolor,wraplength=350)
            self.message.pack(side=BOTTOM,fill=BOTH, expand=1)
            self.msg.set(self.currDir+"\n"+self.mgltoolsDir+'\n')
#            self.createDirChooser()
            
    def linuxwhich(self,program):
        #this function is also in mglutil.util.packageFilePath.py
        import os
        def is_exe(fpath):
            return os.path.exists(fpath) and os.access(fpath, os.X_OK)
    
        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file
    
        return None

    def SetDirectory(self):
        #according OS will set all the basic directory:
        #user/progam/root
        #in Win XP/2k/2k3 it is C:\Documents and Settings\%username%\
        #in Vista, it is C:\Users\%username%\
        #%HOMEPATH%.+
        self.userDirectory=os.getenv("HOME")
        if self.plateform == 'darwin':
            COPY="cp -r"
            self.progDirectory="/Applications/" #Mac
            self.preferencesDir=self.userDirectory+"/Library/Preferences/"
            self.sharedDirectory="/Users/Shared/"
        elif self.plateform == 'linux':
            COPY="cp -r"
            self.progDirectory=os.environ["PATH"].split(os.pathsep)
            self.preferencesDir=self.userDirectory
            self.sharedDirectory="/home/"
        elif self.plateform == 'win32':
            COPY="xcopy"
            self.userDirectory="C:"+os.getenv("HOMEPATH")
            self.progDirectory="C:"+os.sep+"Program Files"+os.sep
            self.preferencesDir=os.getenv("APPDATA")

            
    def say_hi(self):
        print "hi there, everyone!"

    def quit(self):
        self.frame.quit()
        
    def install(self):
        f=open(self.mgltoolsDir+os.sep+'MGLToolsPckgs'+os.sep+'Pmv'+os.sep+'hostappInterface'+os.sep+'epmv_dir.txt','a')
        for i,v in enumerate(self.v):
            val=v.get()
            if val : 
                print "install epmv plug for ",self.MODES[i]
                self.log+="\ninstall epmv plug for "+self.MODES[i]
                self.msg.set(self.log)                
                self.funcInstall[i]()
                #store directory
                f.write(self.MODES[i]+":"+self.softdir[i]+"\n")
        f.close()
        self.makeExtensionfile()
        self.log+="\nSUCCESS YOU CAN QUIT !"
        print self.log
        self.msg.set(self.log)

    def DirCallback(self,widget, event=None):
        values =  widget.get()
        print values
        
    def quitDir(self):
        dir = self.choosenDir.get()
        print "quitDir",dir
        if self.plateform == "darwin":
            dir = dir.replace(" ","\ ")
        self.dir[self.curent].set(dir)
        self.softdir[self.curent] = dir    
        self.chooseDir.destroy()

    def setChoosenDir(self):
        dir = self.choosenDir.get()
        self.dir[self.curent].set(dir)
#        print dir
    
    def chooseDirectory(self,soft,listeDir):
        #need a new windows ?
        self.curent = soft
        if self.chooseDir is None :
            self.chooseDir=Frame(self.master)
            
#            self.createDirChooser()
        else :
            self.chooseDir.destroy()
            self.chooseDir=Frame(self.master)
        self.chooseDir.pack()
#        frame = Frame(self.chooseDir)
#        frame.pack() 
#        mb3 = MultiRadiobuttons(self.chooseDir,valueList=listeDir, 
#                                callback=self.DirCallback)
#        self.choosenDir.set("") # initialize
        for i in range(len(listeDir)):
#            self.choosenDir.set(listeDir[i])
            b = Radiobutton(self.chooseDir, text=listeDir[i],
                    variable=self.choosenDir, value=listeDir[i],
                    command=self.setChoosenDir)
            b.pack(anchor=W)
        buttonQuit = Button(self.chooseDir, text="OK",
                                 command=self.quitDir)
        buttonQuit.pack(anchor=W)
#        else :
            

    def findDirectories(self):
        self.automaticSearch = True
        for i,v in enumerate(self.v):
            val=v.get()
            if val : 
                if self.MODES[i] == 'Blender':
                    self.getBlenderDir()
                elif self.MODES[i] == 'Cinema4D':
                    self.getC4dDir()
                elif self.MODES[i] == 'Cinema4DR12':
                    self.getC4dr12Dir()
                elif self.MODES[i] == 'Maya':
                    self.getMayaDir()
        self.automaticSearch = False
        
    def setDirectory(self):
      for i,v in enumerate(self.v):
          val=v.get()
          if val : 
                x = askdirectory(initialdir="", title="where is "+self.MODES[i]+" plugin/script directory")
                if sys.platform != 'win32':
                    x = x.replace(" ","\ ")
                print x 
                self.softdir[i] = x
                self.dir[i].set(x)
                
    def listDir(self,dir,sp="*"):
        return glob.glob(dir+os.sep+sp)

    def findDirectoryFrom(self,dirname,where,sp="*"):
        dirs=[]
        tocheck = self.listDir(where,sp=sp)
        for dir in tocheck:
            print dir,dirname
            if dir.find(dirname) != -1:
                dirs.append(dir)
        return dirs

    def findDirectory(self,dirname,where,pbval=0):
        result=None
        if where == None:
            return result
        #print "try finding "+dirname+" directory in "+where
        self.pbval +=pbval
        if self.pbval > 100 :
            self.pbval = 0
        self.progressbar.set(self.pbval)
        #print where
        if dirname in os.listdir(where):
            print "founded"
            self.progressbar.set(100)
            result=os.path.join(where,dirname)
        else :
            k=0
            #print where
            tocheck = self.listDir(where)
            if len(tocheck) > 100: return None
            for dir in tocheck:
                self.progressbar.set( (k/len(self.listDir(where)))*100 )
                if os.path.isdir(dir):
                    result = self.findDirectory(dirname,dir,k)
                    if result != None:
                        k=k+1
                        break
                k=k+1
        return result

    def getDirFromFile(self):
        #we get the soft dir from a file in Pmv/hostappinterface/epmv_dir.txt
        f=open(self.currDir+os.sep+'epmv_dir.txt','r')
        lines=f.readlines()
        f.close()
        #now parse it ie format : soft/extension dir
        for line in lines :
            elem = line.split(":")
            for i,soft in enumerate(self.MODES):
                if elem[0].lower() == self.MODES[i].lower():
                    self.softdir[i]=elem[1].strip()

    def getBlenderDir(self):
        if self.plateform.find("linux") != -1:
            dir=self.findDirectoryFrom(".blender",self.userDirectory+"/",sp=".*")
            if len(dir) == 0 :
                x = askdirectory(initialdir=self.userDirectory, title="where is blender script directory, ie .blender/script")
                dir = x#self.softdir[2]
            else :
                dir = dir[0]
            dir = dir.replace(" ","\ ")
            self.dir[0].set(dir)
            self.softdir[0] = dir
        elif self.plateform == 'darwin':
            dir=self.findDirectoryFrom("blender",self.progDirectory+"/")
            if len(dir) == 0 :
                x = askdirectory(initialdir=self.userDirectory, title="where is blender script directory, ie .blender/script")
                dir = x#self.softdir[2]
                self.dir[0].set(dir)
                self.softdir[0] = dir
            elif len(dir) == 1 :
                dir = dir[0]
                dir = dir.replace(" ","\ ")
                self.dir[0].set(dir)
                self.softdir[0] = dir
            else :
                self.chooseDirectory(0,dir)
        elif self.plateform == 'win32':
            #blender can be in Prgoram files or Application Data
            #dir=self.findDirectoryFrom("Blender Foundation",self.progDirectory)
            #if len(dir) == 0 :
            dir=self.findDirectoryFrom("Blender Foundation",self.preferencesDir)
            if len(dir) == 0 :
                x = askdirectory(initialdir=self.userDirectory, title="where is the Blender Foundation directory")
                dir = x
                self.dir[0].set(dir)
                self.softdir[0] = dir     
            elif len(dir) == 1 :
                dir = dir[0]
#                dir = dir+os.sep+"Blender"+os.sep+".blender"+os.sep
                self.dir[0].set(dir)
                self.softdir[0] = dir
            else :
                self.chooseDirectory(0,dir)
        if self.automaticSearch :
            t1=time.time()
            self.progressbar.setLabelText('searching '+".blender")
            #is blender define in path
            dir=packageFilePath.which('blender')
            if dir == None :
                dir=self.findDirectory(".blender",self.progDirectory)
                if dir is None :
                    dir=self.findDirectory(".blender",self.userDirectory)
                    if dir is None :
                    #dir=self.findDirectory(".blender",self.rootDirectory)
                    #if dir is None:
                        dir="not Found"
                        return 
            print "time to find", time.time()-t1
            print dir
            dir = dir.replace(" ","\ ")
            self.dir[0].set(dir)
            self.softdir[0] = dir
        
    def getC4dDir(self):
        dir = None
        if self.plateform == "darwin":
            dir=self.findDirectoryFrom("CINEMA 4D R11.5",self.progDirectory+"/MAXON/")
            if len(dir) == 0 :
                x = askdirectory(initialdir=self.progDirectory, title="where is CINEMA4D 4D R11.5 plugin directory")
                dir = x
                self.dir[1].set(dir)
                self.softdir[1] = dir                
            elif len(dir) == 1 :
                dir = dir.replace(" ","\ ")
                self.dir[1].set(dir)
                self.softdir[1] = dir
            else :
                self.chooseDirectory(1,dir)
#                dir = dir[0]
        if self.automaticSearch :
            t1=time.time()
            self.progressbar.setLabelText('searching '+"Py4D")
            dir=self.findDirectory("Py4D",self.progDirectory)
            #if dir is None :
            #    dir=self.findDirectory("Py4D",self.progDirectory)
            if dir is None:
                    dir="not Found"
                    return
            print "time to find", time.time()-t1
            dir = dir.replace(" ","\ ")
            self.dir[1].set(dir)
            self.softdir[1] = dir

    def getC4dr12Dir(self):
        dir = None
        if self.plateform == "darwin":
            dir=self.findDirectoryFrom("CINEMA 4D R12",self.preferencesDir+"/MAXON/")
            if len(dir) == 0 :
                x = askdirectory(initialdir=self.preferencesDir, title="where is CINEMA4D 4D R12 user preferences directory")
                dir = x
                self.dir[2].set(dir)
                self.softdir[2] = dir
            elif len(dir) == 1 :
                dir = dir[0]
                dir = dir.replace(" ","\ ")
                self.dir[2].set(dir)
                self.softdir[2] = dir
            else :
                self.chooseDirectory(2,dir)
        elif self.plateform == "win32":
            dir=self.findDirectoryFrom("CINEMA 4D R12",self.preferencesDir+os.sep+"MAXON"+os.sep)
            if len(dir) == 0 :
                x = askdirectory(initialdir=self.preferencesDir, title="where is CINEMA4D 4D R12 user preferences directory")
                dir = x
                self.dir[2].set(dir)
                self.softdir[2] = dir                
            elif len(dir) == 1 :
                dir = dir[0]
#            dir = dir + "/plugins/Py4D/"
                self.dir[2].set(dir)
                self.softdir[2] = dir
            else :
                self.chooseDirectory(2,dir)
        if self.automaticSearch and dir is None :
            t1=time.time()
            self.progressbar.setLabelText('searching '+"C4D R12")
            dir=self.findDirectory("CINEMA 4D R12",self.progDirectory)
            #if dir is None :
            #    dir=self.findDirectory("Py4D",self.progDirectory)
            if dir is None:
                    dir="not Found"
                    return
            print "time to find", time.time()-t1
            dir = dir.replace(" ","\ ")
            self.dir[2].set(dir)
            self.softdir[2] = dir
        
    def getMayaDir(self):
        if self.plateform == "darwin":
            dir=self.sharedDirectory+"/Autodesk/maya/2011/plug-ins/"
            if not os.path.exists(dir):
                x = askdirectory(initialdir=self.progDirectory, title="where is MAYA2011 plugin directory")
                dir = x                
            self.dir[3].set(dir)
            self.softdir[3] = dir
        elif self.plateform == "win32":
            dir=self.findDirectoryFrom("Maya2011",self.progDirectory+os.sep+"Autodesk"+os.sep)
            if len(dir) ==0 :
                x = askdirectory(initialdir=self.progDirectory, title="where is MAYA2011 bin/plugins directory")
                dir = x
                self.dir[3].set(dir)
                self.softdir[3] = dir                
            elif len(dir) == 1 :
                dir = dir[0]
                dir = dir +os.sep+"bin"+os.sep+"plug-ins"
                self.dir[3].set(dir)
                self.softdir[3] = dir
            else :
                self.chooseDirectory(3,dir)
        elif self.automaticSearch and dir is None:
            dir=self.findDirectory("maya2011",self.rootDirectory)
            dir = dir.replace(" ","\ ")
            self.dir[3].set(dir)
            self.softdir[3] = dir
        
    def installBlender(self):
        if self.plateform =="darwin":
            self.softdir[0] =self.softdir[0]+"/blender.app/Contents/MacOS/.blender/"
        elif self.plateform =="win32":    
            self.softdir[0] =self.softdir[0]+os.sep+"Blender"+os.sep+".blender"
        self.log+="\ninstall blender-epmv plug in "+self.softdir[0]
        self.msg.set(self.log)
        #copy the directory of plugin to the blender script directory selected 
        # by the user
        #change the head of the plugin-files
        indir = self.currDir+os.sep+"blender"+os.sep+"plugin"+os.sep
        outdir = self.softdir[0]+os.sep+"scripts"+os.sep
        files=[]
        files.append("blenderPmvScriptGUI.py")
        files.append("blenderPmvClientGUI.py") 
        files.append("epmv_blender_update.py")   
        for f in files : 
            shutil.copy (indir+f, outdir+f)
            self.changeHeaderFile(outdir+f)
        #no need to patch linux and mac as there is blender python2.5
        #What about windows, already patch MGL but do we need to patch blender?
        
    def installC4d(self,update=False):
        self.log+="\ninstall c4d-epmv plug in "+self.softdir[1]+os.sep+"plugins/Py4D"
        self.msg.set(self.log)
        dir = self.softdir[1] 
        if self.plateform == "darwin":
            dir = dir.replace("\ "," ")
        py4ddir=dir+os.sep+"plugins/Py4D"
        #copy the directory of plugin to c4d/plugins/Py4D/plugins/.
        #Py4D should be already patched
        if not update:
            if not os.path.exists(py4ddir):
                patchpath = dir
                self.progressbar.setLabelText("getting  Py4D")
                URI="http://mgldev.scripps.edu/projects/ePMV/py4d.tar" #or Tku.tar
                tmpFileName = dir+"/py4d.tar"
                geturl(URI, tmpFileName,pb=self.progressbar)
                TF=tarfile.TarFile(tmpFileName)
                TF.extractall(patchpath)
            dirname1=self.currDir+os.sep+"cinema4d"+os.sep+"plugin"
            dirname2=py4ddir+os.sep+"plugins"+os.sep+"epmv"
            if os.path.exists(dirname2):
                shutil.rmtree(dirname2,True)
            shutil.copytree (dirname1, dirname2)            
            #copy the color per vertex c++ plugin
            filename1=py4ddir+os.sep+"plugins"+os.sep+"epmv"+os.sep+"epmv_c4d_plugin.py"
            filename2=py4ddir+os.sep+"plugins"+os.sep+"epmv"+os.sep+"epmv.pyp"
            shutil.copy (filename1, filename2)
            filename1=py4ddir+os.sep+"plugins"+os.sep+"epmv"+os.sep+"epmv_update.py"
            filename2=py4ddir+os.sep+"plugins"+os.sep+"epmv"+os.sep+"epmv_synchro.pyp"
            shutil.copy (filename1, filename2)
            filename1=self.currDir+os.sep+"cinema4d"+os.sep+"VertexColor.dylib"
            filename2=dir+os.sep+"plugins/VertexColor.dylib"
            shutil.copy (filename1, filename2)
        else :
            cmd="cp "+self.currDir+os.sep+"cinema4d"+os.sep+"plugin"+os.sep+"*.py "+self.softdir[1]+os.sep+"plugins"+os.sep+"epmv"+os.sep+"."
            print cmd
            os.system(cmd)
        #update the header changing the MGLTOOLS value
        files=[]
        files.append(py4ddir+os.sep+"plugins"+os.sep+"epmv"+os.sep+"epmv_c4d_plugin.py")
        files.append(py4ddir+os.sep+"plugins"+os.sep+"epmv"+os.sep+"epmv.pyp")
        for f in files : 
            self.changeHeaderFile(f)

    def patchC4DR12(self,patchpath):
        dir = self.softdir[2]
        patch=os.path.isfile(patchpath+"patched")
        if self.plateform == "darwin":
#            dir=dir.replace("\ "," ")
#            patchpath = dir+"/library/python/packages/osx/"        
            if not patch :
#                self.progressbar.setLabelText("patching C4D python")
                URI="http://mgldev.scripps.edu/projects/ePMV/Tk.tar" #or Tku.tar
                tmpFileName = dir+"/library/python/packages/osx/Tk.tar"
                geturl(URI, tmpFileName)
                TF=tarfile.TarFile(tmpFileName)
                TF.extractall(patchpath)
                f=open(patchpath+"patched","w")
                f.write("C4D patched!")
                f.close()                    
        elif self.plateform == "win32":
            #then patch python framework but need the soft directory
            #C:Program Files / MAXON / CINEMA4D
            if not patch :
                 #resource\modules\python\res
                name1="Python.win32.framework"
                name2="Python.win32.framework.original"
                print patchpath+name1
                if not os.path.exists(patchpath+name2):
                    os.rename(patchpath+name1,patchpath+name2)
                #we simply Copy the C:\\Python26 directory....
                dirname1="C:\\Python26\\"
                dirname2=patchpath+name1
                shutil.copytree (dirname1, dirname2)         
                
#                URI="http://mgldev.scripps.edu/projects/ePMV/patchs/py26win.tar"
#                tmpFileName = patchpath+"py26win.tar"
                #self.progressbar.setLabelText("patching C4D python")
#                if not os.path.isfile(tmpFileName):
#                    geturl(URI, tmpFileName)
#                TF=tarfile.TarFile(tmpFileName)
#                if not os.path.exists(patchpath+name2):
#                    os.rename(patchpath+name1,patchpath+name2)
#                TF.extractall(patchpath)
                f=open(patchpath+"patched","w")
                f.write("C4D patched!")
                f.close()        

    def installC4dr12(self,update=False):
        dir = self.softdir[2]
        if self.plateform == "darwin":
           dir = dir.replace("\ "," ")
#        print "install c4dr12-epmv plug in ",self.softdir[0]       
        self.log+="\ninstall c4dr12-epmv plug in "+self.softdir[2] 
        if self.gui :
            self.msg.set(self.log)
        #same should we use the user directory and check on  windows
        #copy the directory of plugin to c4d/plugins/Py4D/plugins/.
        if not update:
            #copy the plugin directory
            #if self.plateform == "win32":
            import shutil
            dirname1=self.currDir+os.sep+"cinema4d_dev"+os.sep+"plugin"
            dirname2=dir+os.sep+"plugins"+os.sep+"epmv"
            if os.path.exists(dirname2):
                shutil.rmtree(dirname2,True)
            shutil.copytree (dirname1, dirname2)
            filename1=dir+os.sep+"plugins"+os.sep+"epmv"+os.sep+"epmv_c4d_plugin.py"
            filename2=dir+os.sep+"plugins"+os.sep+"epmv"+os.sep+"epmv.pyp"
            shutil.copy (filename1, filename2)
            filename1=dir+os.sep+"plugins"+os.sep+"epmv"+os.sep+"epmv_update.py"
            filename2=dir+os.sep+"plugins"+os.sep+"epmv"+os.sep+"epmv_synchro.pyp"
            shutil.copy (filename1, filename2)
            #patch using 32 or 64bits ? seems that both are working
            if self.plateform == "darwin":
                dir=dir.replace("\ "," ")
                patchpath = dir+"/library/python/packages/osx/"
                patch=os.path.isfile(patchpath+"patched")
                if not patch :
                    self.progressbar.setLabelText("patching C4D python")
                    URI="http://mgldev.scripps.edu/projects/ePMV/Tk.tar" #or Tku.tar
                    tmpFileName = dir+"/library/python/packages/osx/Tk.tar"
                    geturl(URI, tmpFileName,pb=self.progressbar)
                    TF=tarfile.TarFile(tmpFileName)
                    TF.extractall(patchpath)
                    f=open(patchpath+"patched","w")
                    f.write("C4D patched!")
                    f.close()                    
            elif self.plateform == "win32":
                #then patch python framework but need the soft directory C:Program Files / MAXON / CINEMA4D
                print self.progDirectory+"MAXON"+os.sep
                prog=self.findDirectoryFrom("CINEMA 4D R12",self.progDirectory+"MAXON"+os.sep)
                if len(prog) ==0 :
                    x = askdirectory(initialdir=self.progDirectory, 
                                     title="where is CINEMA4D 4D R12 application directory")
                    prog = [x,]
                    patchpath = prog[0]+os.sep+"resource"+os.sep+"modules"+os.sep+"python"+os.sep+"res"+os.sep
                    patch=os.path.isfile(patchpath+"patched")
                elif len(prog) ==1:
                    patchpath = prog[0]+os.sep+"resource"+os.sep+"modules"+os.sep+"python"+os.sep+"res"+os.sep
                    patch=os.path.isfile(patchpath+"patched")
                else : #take the first one....
                    patchpath = prog[0]+os.sep+"resource"+os.sep+"modules"+os.sep+"python"+os.sep+"res"+os.sep
                    patch=os.path.isfile(patchpath+"patched")
                if not patch :
                     #resource\modules\python\res
                    name1="Python.win32.framework"
                    name2="Python.win32.framework.original"
                    print patchpath+name1
                    if not os.path.exists(patchpath+name2):
                        os.rename(patchpath+name1,patchpath+name2)
                    #we simply Copy the C:\\Python26 directory....
                    dirname1="C:\\Python26\\"
                    dirname2=patchpath+name1
                    shutil.copytree (dirname1, dirname2)
#                    URI="http://mgldev.scripps.edu/projects/ePMV/patchs/py26win.tar"
#                    tmpFileName = patchpath+"py26win.tar"
#                    self.progressbar.setLabelText("patching C4D python")
#                    geturl(URI, tmpFileName,pb=self.progressbar)
#                    TF=tarfile.TarFile(tmpFileName)
#                    TF.extractall(patchpath)
                    f=open(patchpath+"patched","w")
                    f.write("C4D patched!")
                    f.close()
        else :
            cmd=COPY+" "+self.currDir+os.sep+"cinema4d_dev"+os.sep+"plugin"+os.sep+"*.py "+dir+os.sep+"plugins"+os.sep+"epmv"+os.sep+"."
            print cmd
            os.system(cmd)
        #update the header changing the MGLTOOLS value
        files=[]
        files.append(dir+os.sep+"plugins"+os.sep+"epmv"+os.sep+"epmv_c4d_plugin.py")
        files.append(dir+os.sep+"plugins"+os.sep+"epmv"+os.sep+"epmv.pyp")
        for f in files : 
            self.changeHeaderFile(f)
        
    def personalizeMaya(self,plugdir,prefDir):
        shelfMel="""
shelfButton
        -enableCommandRepeat 1
        -enable 1
        -width 35
        -height 35
        -manage 1
        -visible 1
        -preventOverride 0
        -annotation "import maya\\nmaya.cmds.ePMV()\\nepmv = maya.epmvui.epmv\\nself = epmv.mv\\n" 
        -enableBackground 0
        -align "center" 
        -label "ePMV" 
        -labelOffset 0
        -font "plainLabelFont" 
        -imageOverlayLabel "ePMV" 
        -overlayLabelColor 0.8 0.8 0.8 
        -overlayLabelBackColor 0 0 0 0.2
"""
        logo = plugdir+os.sep+"images"+os.sep+"pmv.tif"
        shelfMel+='        -image "%s"\n' % (logo.replace("\\","/"))
        shelfMel+='        -image1 "%s"\n' % (logo.replace("\\","/"))
        shelfMel+="""
        -style "iconOnly" 
        -marginWidth 1
        -marginHeight 1
        -command "import maya\\nmaya.cmds.ePMV()\\nepmv = maya.epmvui.epmv\\nself = epmv.mv\\n"
        -sourceType "python" 
        -commandRepeatable 1
    ;
"""
        windowsPref = "windowPref -topLeftCorner 413 640 -widthHeight 960 480 ePMV;"
        pluginPref = 'evalDeferred("autoLoadPlugin(\"\", \"ePMV.py\", \"ePMV\")");'
        
        filename = prefDir+os.sep+"shelves"+os.sep+"shelf_Custom.mel"
        #test if exist if not create.
        if os.path.isfile(filename):
            f=open(filename,'r')
            lines = f.readlines()
            f.close()
        else :
            f=open(filename,'w')
            lines="""global proc shelf_Custom () {
global string $gBuffStr;
global string $gBuffStr0;
global string $gBuffStr1;
}"""
            f.write(lines)
            f.close()
        f=open(prefDir+os.sep+"shelves"+os.sep+"shelf_Custom.mel",'w')
        lines = lines[:-1]
        for line in lines:
            f.write(line)
        f.write(shelfMel)
        f.write("}\n")
        f.close()
        #change the plugin preferences too
        f=open(prefDir+os.sep+"pluginPrefs.mel",'a')
        f.write('evalDeferred("autoLoadPlugin(\\"\\", \\"ePMV.py\\", \\"ePMV\\")");')
        f.close()
        
        
    def installMaya(self,update=False):
        self.log+="\ninstall maya-epmv plug in "+self.softdir[2] 
        self.msg.set(self.log)
        #what about windows
        #maya is in /Applications/Autodesk/maya2011/Maya.app/Contents/MacOS/plug-ins/ePMV.py
        #preferences are in /Users/ludo/Library/Preferences/Autodesk/maya/2011/prefs
        #and on windowsXP : C:\Documents and Settings\ludo\My Documents\maya\2011\prefs
        #and on windows7 vista : C:\Users\USERNAME\Documents\maya\2011\
        
        shelfMel="""
shelfButton
        -enableCommandRepeat 1
        -enable 1
        -width 35
        -height 35
        -manage 1
        -visible 1
        -preventOverride 0
        -annotation "import maya\\nmaya.cmds.ePMV()\\nepmv = maya.epmvui.epmv\\nself = epmv.mv\\n" 
        -enableBackground 0
        -align "center" 
        -label "ePMV" 
        -labelOffset 0
        -font "plainLabelFont" 
        -imageOverlayLabel "ePMV" 
        -overlayLabelColor 0.8 0.8 0.8 
        -overlayLabelBackColor 0 0 0 0.2
"""
        logo = self.currDir+os.sep+"images"+os.sep+"pmv.tif"
        shelfMel+='        -image "%s"\n' % (logo.replace("\\","/"))
        shelfMel+='        -image1 "%s"\n' % (logo.replace("\\","/"))
        shelfMel+="""
        -style "iconOnly" 
        -marginWidth 1
        -marginHeight 1
        -command "import maya\\nmaya.cmds.ePMV()\\nepmv = maya.epmvui.epmv\\nself = epmv.mv\\n"
        -sourceType "python" 
        -commandRepeatable 1
    ;
"""
        windowsPref = "windowPref -topLeftCorner 413 640 -widthHeight 960 480 ePMV;"
        pluginPref = 'evalDeferred("autoLoadPlugin(\"\", \"ePMV.py\", \"ePMV\")");'
        #1 link the plugin to plug-dir or copy? plugin is in maya.app folder
        #special case of /Users/shared/maya/plugin
#        cmd="cp "+self.currDir+"/autodeskmaya/plugin/mayaPMVui.py "+self.softdir[3]+"/ePMV.py"
        file1=self.currDir+os.sep+"autodeskmaya"+os.sep+"plugin"+os.sep+"mayaPMVui.py"
        if self.plateform == 'darwin':
            file2=self.sharedDirectory+"/Autodesk/maya/2011/plug-ins/ePMV.py"
        elif self.plateform == "win32":
            file2=self.softdir[3]+os.sep+"ePMV.py"
            print file2
        else :#linux
            file2=self.sharedDirectory+"/Autodesk/maya/2011/plug-ins/ePMV.py"
        try :
            shutil.copy (file1, file2)
        except IOError, e:
            print "Unable to copy file. %s" % e
        #cmd="cp "+self.currDir+"/autodeskmaya/plugin/mayaPMVui.py "+self.sharedDirectory+"/Autodesk/maya/2011/plug-ins/ePMV.py"
        #print cmd
        #os.system(cmd)
        prefDir=""
        dirname1=self.currDir+os.sep+"images"+os.sep+"icons"
        if self.plateform == 'darwin':
            prefDir=self.preferencesDir+os.sep+"Autodesk"+os.sep+"maya"+\
                  os.sep+"2011"+os.sep+"prefs"
        elif self.plateform == 'win32':
            mydocdir =self.userDirectory+os.sep+"My Documents"
            if not os.path.exists(mydocdir):
                mydocdir= self.userDirectory+os.sep+"Documents"
            prefDir=mydocdir+os.sep+"maya"+\
                  os.sep+"2011"+os.sep+"prefs"
        else :
            prefDir=self.preferencesDir+os.sep+"Autodesk"+os.sep+"maya"+\
                  os.sep+"2011"+os.sep+"prefs"
        dirname2=prefDir+os.sep+"icons"+os.sep
        if os.path.exists(dirname2):
            #os.remove(dirname2)
            shutil.rmtree(dirname2,True)
        shutil.copytree (dirname1, dirname2)
        
        #cmd="cp "+self.currDir+"/images/icons/* "+\
        #     self.preferencesDir+"/Autodesk/maya/2011/prefs/icons/."
        #What about the c++ plugin?
        #print cmd
        #os.system(cmd)        
        if not update:
            #2 setup the shelf, the preferences, and copy the icons
            filename = prefDir+os.sep+"shelves"+os.sep+"shelf_Custom.mel"
            #test if exist if not create.
            if os.path.isfile(filename):
                f=open(filename,'r')
                lines = f.readlines()
                f.close()
            else :
                f=open(filename,'w')
                lines="""global proc shelf_Custom () {
    global string $gBuffStr;
    global string $gBuffStr0;
    global string $gBuffStr1;
}"""
                f.write(lines)
                f.close()
            f=open(prefDir+os.sep+"shelves"+os.sep+"shelf_Custom.mel",'w')
            lines = lines[:-1]
            for line in lines:
                f.write(line)
            f.write(shelfMel)
            f.write("}\n")
            f.close()
            #change the plugin preferences too
            f=open(prefDir+os.sep+"pluginPrefs.mel",'a')
            f.write('evalDeferred("autoLoadPlugin(\\"\\", \\"ePMV.py\\", \\"ePMV\\")");')
            f.close()
        #update the header changing the MGLTOOLS value
        files=[]
#        files.append(self.softdir[3]+"/ePMV.py")
        files.append(file2)
        for f in files : 
            self.changeHeaderFile(f)

    def changeHeaderFile(self,file):
        if self.plateform != "win32":
            file=file.replace('\\','')
            self.mgltoolsDir = self.mgltoolsDir.replace("\n","\\n")
        data = open(file,'r').read()
        o = open(file,"w")
        o.write( re.sub('MGL_ROOT=""','MGL_ROOT="'+self.mgltoolsDir+'"',data) )
        o.close()       

    def updateCVS(self,full=False):
        if full:
            cmd="cd "+self.mgltoolsDir+"\n"
        else :
            cmd="cd "+self.currDir+"\n"
        cmd+="cvs -d:pserver:anonymous@mgl1.scripps.edu:/opt/cvs update\n"
        os.system(cmd)

    def addExtensionToFile(self,string):
        f=open(self.currDir+os.sep+'extension'+os.sep+'liste.txt','a')
        f.write(string+"\n")
        f.close()

    def addExtension(self,string):
        self.getExtensionDirFromFile()
        elem = string.split(":")
        print elem
        for i,soft in enumerate(self.extensions):
                if elem[0].lower() == self.extensions[i].lower():
                    if self.extdir[i] is "":
                        self.extdir[i]=elem[1].strip()
                        self.addExtensionToFile(string)

    def makeExtensionfile(self):
        f=open(self.currDir+os.sep+'extension'+os.sep+'liste.txt','w')
        f.write("#put your extension name and directory here\n")
        f.close()

    def getExtensionDirFromFile(self):
        #we get the soft dir from a file in Pmv/hostappinterface/epmv_dir.txt
        fname=self.currDir+os.sep+'extension'+os.sep+'liste.txt'
        if not os.path.isfile(fname):
            f=open(fname,'w')
            f.write("#extension dir\n")
            f.close()
        f=open(fname,'r')
        lines=f.readlines()
        f.close()
        #now parse it ie format : soft/extension dir
        for line in lines :
            elem = line.split(":")
            for i,soft in enumerate(self.extensions):
                if elem[0].lower() == self.extensions[i].lower():
                    self.extdir[i]=elem[1].strip()
           
if __name__ == '__main__':
    try :
        root = Tk()
        root.title("ePMV plugins installer")
        #root.geometry('+%d+%d' % (100,100))
        app = Installer(master=root)
        root.mainloop()
    except :
        print "problem"
        pass
