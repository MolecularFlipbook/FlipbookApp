# This modules implements Help-->About for PMV
#
# $Author: vareille $
# $Header: /opt/cvs/python/packages/share1.5/Pmv/aboutCommands.py,v 1.5 2008/07/14 21:58:26 vareille Exp $
# $Date: 2008/07/14 21:58:26 $
# $Id: aboutCommands.py,v 1.5 2008/07/14 21:58:26 vareille Exp $

from Pmv.mvCommand import MVCommand
from ViewerFramework.VFCommand import CommandGUI
import Tkinter, os, sys, Pmw
from mglutil.util.packageFilePath import findFilePath, getResourceFolderWithVersion

import fnmatch
import random
from PIL import Image, ImageTk


class About(MVCommand):
    """Implements Help-->About menu"""

    def __init__(self):
        """Constructor for class About"""
        MVCommand.__init__(self)
        self.master = None


    def getImage(self, image_dir):
        files = os.listdir(image_dir)
        files = fnmatch.filter(files,'*.jpg') + fnmatch.filter(files,'*.png')

        rand = random.randint(0,len(files)-1)
        image_file = os.path.join(os.path.join(image_dir ,files[rand]))

        self.image = Image.open(image_file)
        self.image1 = ImageTk.PhotoImage(self.image, master=self.master)


    def nextImage(self, event=None):
        self.getImage(self.vf.help_about.image_dir)
        self.vf.help_about.imageTk.configure(image=self.image1)
        

    def guiCallback(self):
        if self.master == None:
            self.master = Tkinter.Toplevel()
            self.master.protocol('WM_DELETE_WINDOW',self.destroy)
                        
            self.vf.help_about.gui(master=self.master)
            self.vf.help_about.imageTk.bind('<1>', self.nextImage)


            notebook = Pmw.NoteBook(self.master)
            notebook.pack(expand='yes', fill='both')

            page = notebook.add('Authors')
            #notebook.tab('Authors').focus_set()
            # Authors
            from PIL import Image, ImageTk
            image = Image.open(self.vf.help_about.icon)
            self.icon_image = ImageTk.PhotoImage(master=page, image=image)
            self.image2 = Tkinter.Label(page, image=self.icon_image)
            self.image2.pack(side='left')

            Tkinter.Label(page, text=self.vf.help_about.authors, fg='#662626', 
                          justify='left', anchor='w', 
                          ).pack(side='left')

            # 3rd party
            if len(self.vf.help_about.third_party):
                page = notebook.add('Third party software components')
                
                Tkinter.Label(page, text=self.vf.help_about.third_party, fg='#0A3A75',
                              justify='left',  anchor='w',
                              ).pack(side='left')

    
            # app info group
            if len(self.vf.help_about.path_data):
                page = notebook.add('Path information')
                Tkinter.Label(page, text=self.vf.help_about.path_data, 
                              fg='#3A9E23', justify='left', anchor='w',
                              ).pack(side='left')

            Tkinter.Label(self.master,text = '              ').pack(side='left')
            l = Tkinter.Label(self.master, fg='Blue', cursor='hand1',
                          text='http://mgltools.scripps.edu')
            l.pack(side='left')
            l.bind(sequence="<Button-1>", func=self.openurl)
            Tkinter.Label(self.master,text = '              ').pack(side='left')

            registration = getResourceFolderWithVersion() + os.sep + '.registration'
            if not os.path.exists(registration):
                reg = Tkinter.Button(self.master,text='   Register   ',
                                     command=self.register)
                reg.pack(side = 'left')
            b = Tkinter.Button(self.master,text='   Close   ',
                               command=self.destroy)
            b.pack(side = 'left')
            notebook.setnaturalsize()
        else:
            self.master.deiconify()
            self.master.lift()
            
    def destroy(self):
        self.master.destroy()
        self.master = None
            
    def openurl(self, evt=None):
        import webbrowser
        webbrowser.open('http://mgltools.scripps.edu')
        
    def register(self):
        self.master.withdraw()
        from mglutil.splashregister.register import Register_User
        Register_User(self.vf.help_about.version)
        
AboutGUI = CommandGUI()
AboutGUI.addMenuCommand('menuRoot', 'Help', 'About',separatorAbove = 1)

commandList  = [{'name':'about','cmd':About(),'gui':AboutGUI}]
def initModule(viewer):
    for _dict in commandList:
        viewer.addCommand(_dict['cmd'],_dict['name'],_dict['gui'])
