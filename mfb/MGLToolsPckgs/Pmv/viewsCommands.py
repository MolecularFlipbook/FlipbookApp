#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/viewsCommands.py,v 1.4 2009/10/16 23:18:01 annao Exp $
# 
# $Id: viewsCommands.py,v 1.4 2009/10/16 23:18:01 annao Exp $
#

import os, sys
from Pmv.mvCommand import MVCommand
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from ViewerFramework.VFCommand import CommandGUI
from mglutil.util.callback import CallBackFunction
import Tkinter, Pmw
from opengltk.OpenGL import GL
import math
import types, numpy.oldnumeric as Numeric
import warnings


class ViewsCommand(MVCommand):
    """Command opens a panel that allows the user create bookmarks (icon buttons) representing
       current view state (the orientation and state of the objects currently displayed in
       the Viewer). Left-clicking on an icon button will bring on the saved view. Right click on the icon
       displays the menu(Edit, Remove, Rename). Scenario actors are used to interpolate the orientation
       parameters(rotation, scale, translation, ets) between two views."""


    def __init__(self):
        MVCommand.__init__(self)
        self.views = {}
        self.viewsDirectors = {}
        self.representations = {}
        self.allViews = 0
        self.form = None
        self.idf = None

    def checkDependencies(self, vf):
        from scenario.director import Director


    def onAddCmdToViewer(self):
        if self.vf.GUI:
            root = self.vf.GUI.ROOT
            self.viewMenu = Tkinter.Menu(root, title = "View")
            self.viewMenu.add_command(label="Edit")
            self.viewMenu.add_command(label="Rename")
            self.viewMenu.add_command(label="Remove")
            self.viewMenu.add_command(label="Update icon")
            self.viewMenu.add_command(label="Dismiss")
            self.viewsBalloon = Pmw.Balloon(root)


    def guiCallback(self):
        if not self.form:
            idf = self.idf = InputFormDescr(title="Views")
            idf.append({'name':'viewsContainer',
                        'widgetType':Pmw.Group,
                        'container':{'viewsContainer':"w.interior()"},
                        'wcfg':{'ring_borderwidth':2,
                                'tag_pyclass': None, #Tkinter.Button,
                                #'tag_text':'Save view',
                                #'tag_command': self.saveView
                                },
                        'gridcfg':{'sticky':'we', 'columnspan':1}})
            idf.append({'widgetType':Tkinter.Button,
                    'wcfg':{'text':"Save View", #'Close',
                            "width": 40,
                            'command': self.saveView  #self.dismissForm
                            }})
            self.form = self.vf.getUserInput(self.idf, modal=0, blocking=0)
        else:
            self.form.deiconify()
        # place the form below the viewer (so that the form does not get into a saved image if
        # the user decides to save the view).
        x = self.form.master.winfo_x()
        y = self.form.master.winfo_y()
        w = self.form.master.winfo_width()
        h = self.form.master.winfo_height()
        self.form.root.geometry("+%d+%d" % (x+w/2, y+h))

                                
    def saveView(self):
        """ Saves the current view parameters and adds an image button to the command's GUI."""
        
        name = 'view%d'% self.allViews
        vi = self.vf.GUI.VIEWER
        c = vi.currentCamera
        mini, maxi = vi.rootObject.ComputeBB()
        lBox = maxi - mini
        lHalfObject = max(lBox)/2.
        if lHalfObject == 0.:
            lHalfObject = 1.
        from scenario.interpolators import matToQuaternion, quatToMatrix
        dist = lHalfObject / math.tan(c.fovyNeutral/2*math.pi/180.0)
        lookFrom = c.nearDefault+dist+lHalfObject
        
        view = self.views[name] = {
            'quat' : matToQuaternion(vi.rootObject.rotation),
            'trans' : vi.rootObject.translation[:],
            'scale' : vi.rootObject.scale[:],
            'pivot' : vi.rootObject.pivot,
            'fovy' : c.fovy,
            'lfrom' : lookFrom,
            'near': c.near,
            'far': c.far,
            'start':c.fog.start,
            'end': c.fog.end
            }
        #positionNames = positions.keys()
        #positionNames.sort()
        #positionList.setlist(positionNames)

        director = vi.GUI.createOrientScenario(name, view)
        self.viewsDirectors[name] = director
        self.representations[name] = vi.GUI.saveRepr()
        self.addViewButton(name)
        

    def addViewButton(self, name, icon = True):
        """ Creates an image button ."""
        viewsContainer = self.idf.entryByName['viewsContainer']['widget']
        if self.allViews == 0:
            self.viewsBalloon.bind(viewsContainer._ring, "Right click on view's image\nto display its menu")
        if icon == True:
            self.form.master.lift()
            photo = self.vf.GUI.VIEWER.GUI.getButtonIcon()
            b = Tkinter.Button(master=viewsContainer.interior() ,compound='left', image=photo,
                               command=CallBackFunction( self.activateView, name))
            b.photo = photo
        else:
             b = Tkinter.Button(master=viewsContainer.interior() , text=name,
                                width = 4, height = 3, wraplength=50)
             b.configure(command = CallBackFunction(self.activateView, name, b))
        self.viewsBalloon.bind(b, name)
        b.name = name
        #print "row=", 1+(len(self.views)-1)/5, "column=", (len(self.views)-1)%5
        b.grid(row=1+(len(self.views)-1)/5, column=(len(self.views)-1)%5, sticky='w')
        self.form.autoSize()
        b.bind('<Button-3>', CallBackFunction( self.showViewMenu_cb, name))
        self.allViews = self.allViews + 1
        

    def activateView(self, name, button = None):
        """Callback of the mouse press on an image button. Goes to the   """
        vi = self.vf.GUI.VIEWER
        c = vi.currentCamera
        root = vi.rootObject
        director = self.viewsDirectors[name]
        from scenario.interpolators import matToQuaternion
        qt = matToQuaternion(root.rotation)
        trans = root.translation[:]
        scale= root.scale[:]
        fov = c.fovy
        lfrom = c.lookFrom
        pivot = self.views[name]['pivot']
        for actor in director.actors:
            prop = actor.name.split(".")[-1]
            if prop == 'rotation':
                actor.setKeyframe(0, value = qt)
            elif prop == 'translation':
                actor.setKeyframe(0, value = trans)
            elif prop == 'scale':
                actor.setKeyframe(0, value = scale)
            elif prop == 'pivot':
                actor.setKeyframe(0, value = pivot)
            elif prop == 'fieldOfView':
                actor.setKeyframe(0, value = fov)
            elif prop == 'lookFrom':
                actor.setKeyframe(0, value = lfrom)
            #elif prop == 'fog':
                #actor.setKeyframe(0, value = Numeric.array([c.fog.start, c.fog.end], "f"))
        if director.gui != None:
            director.gui.playTK.set(1)
        director.run()
        # bring on the saved representaion
        self.restoreRepesentation(name)
        if button: 
            if not hasattr(button, "photo"):
                #print "updating image for button %s" % name
                vi.master.master.lift()
                vi.OneRedraw()
                photo = vi.GUI.getButtonIcon()
                button.configure(compound='left', image = photo, text = "",
                                 width=photo.width(), height = photo.height())
                button.photo = photo


    def restoreRepesentation(self, name):
        repr = self.representations[name]
        vi = self.vf.GUI.VIEWER
        for g in vi.rootObject.AllObjects():
            if not repr.has_key(g.fullName):
                g.visible = 0
            else:
                #print g.fullName
                tmp = repr[g.fullName].copy()
                mat = tmp.pop('rawMaterialF', None)
                if mat: g.materials[GL.GL_FRONT].Set(**mat)
                mat = tmp.pop('rawMaterialB', None)
                if mat: g.materials[GL.GL_BACK].Set(**mat)
                g.Set( **tmp )
        
    
    def showViewMenu_cb(self, name, event = None):
        edit = self.viewMenu.index("Edit")
        rn = self.viewMenu.index("Rename")
        rm = self.viewMenu.index("Remove")
        update = self.viewMenu.index("Update icon")
        self.viewMenu.entryconfigure(
            edit, command = CallBackFunction(self.editView, name))
        self.viewMenu.entryconfigure(
            rn, command = CallBackFunction(self.renameView, name))
        self.viewMenu.entryconfigure(
            rm, command = CallBackFunction(self.removeView, name))
        self.viewMenu.entryconfigure(
            update, command = CallBackFunction(self.updateViewIcon, name))
        self.viewMenu.post(event.x_root, event.y_root)


    def editView(self, name):
        """Callback of the edit menu button.Pops up the scenario director gui."""
        director = self.viewsDirectors[name]
        if director:
            director.start(setDirector=False, title = "Director:  %s" % name)
            if director.gui:
                director.gui.disableAutoTrack()


    def gotoView(self, name):
        # go directly into the selected view without interpolation
        director = self.viewsDirectors.get(name)
        if director:
            lastFrame = director.getLastFrameWithChange()
            director.currentFrame = 0
            director.gotoFrame(lastFrame)

            
    def renameView(self, name):
        """Give a new name to the selected view. """
        from tkSimpleDialog import askstring
        viewsContainer = self.idf.entryByName['viewsContainer']['widget'].interior()
        newname = askstring("Rename %s"%name, "Enter new name:", initialvalue = name,
                            parent = viewsContainer)
        if newname != None and newname != name:
            if self.views.has_key(newname):
                from tkMessageBox import showwarning
                showwarning("Warning", "View name %s already exists"%newname,
                            parent = viewsContainer)
                return
            #find cooresponding button, rename it and update the bindings:
            for b in viewsContainer.grid_slaves():
                if hasattr(b, "name"):
                    if b.name == name:
                       b.name = newname
                       b.configure(command = CallBackFunction( self.activateView, newname))
                       b.bind('<Button-3>', CallBackFunction( self.showViewMenu_cb, newname))
                       self.viewsBalloon.bind(b, newname)
                       view = self.views.pop(name)
                       self.views[newname] = view
                       dr = self.viewsDirectors.pop(name)
                       self.viewsDirectors[newname] = dr
                       if dr.gui != None:
                           dr.gui.root.title(newname)
                       repr = self.representations.pop(name)
                       self.representations[newname] = repr
                       break 


    def removeView(self, name):
        """Remove selected view button from the gui.Delete saved orientation and representation corresponding to the view."""
        viewsContainer = self.idf.entryByName['viewsContainer']['widget'].interior()
        for b in viewsContainer.grid_slaves():
            if hasattr(b, "name"):
                if b.name == name:
                    b.destroy()
                    # regrid the buttons to fill the space freed by the removed button :
                    buttons = viewsContainer.grid_slaves() # the widgets in this list
                    # seem to be stored in "last created, first in the list" order
                    buttons.reverse()
                    for i, b in enumerate(buttons):
                        b.grid(row=1+ i/5, column= i%5, sticky='w')
                    self.form.autoSize()
                    # remove the view entry from self.views and self.viewsDirectors:
                    self.views.pop(name)
                    d= self.viewsDirectors.pop(name)
                    if d.gui:
                        d.gui.root.destroy()
                    self.representations.pop(name)
                    break


    def updateViewIcon(self, name):
        """Activates the selected view, takes picture of it and updates button image with it ."""
        self.form.master.lift()
        self.gotoView(name)
        self.restoreRepesentation(name)
        vi = self.vf.GUI.VIEWER
        vi.OneRedraw()

        container = self.idf.entryByName['viewsContainer']['widget'].interior()
        for b in container.grid_slaves():
            if hasattr(b, "name"):
                if b.name == name:
                    photo = vi.GUI.getButtonIcon()
                    b.configure(image = photo)
                    b.photo = photo
                    break


    def dismissForm(self):
        self.form.withdraw()

    def deleteViews(self):
        """ Remove all existing views. """
        for b in self.viewsContainer.interior().grid_slaves():
            b.destroy()
        self.views = {}
        self.allViews = 0
        for d in self.viewsDirectors.values():
            if d.gui:
                d.gui.root.destroy()
                d.gui = None
            d = None
        self.viewsDirectors={}
        self.representations = {}
    


ViewsCommandGUI = CommandGUI()
ViewsCommandGUI.addMenuCommand('menuRoot', '3D Graphics','Show Views Panel',
                                   index = 10)

from mglutil.gui.BasicWidgets.Tk.customizedWidgets import SaveButton, LoadButton

class SaveViewsToFile(MVCommand):
    """This command allows the user to save created views to two files:
    *_views.py ( orientation) and *_repr.db(representation). These files are used to
    restore the saved views (ReadViews Command). The saved orientations and representations
    could also be loaded (separately) whith the DejaVu Viewer GUI."""

    def buildFormDescr(self, formName):
        if formName=='saveViewsToFile':
            if self.vf.commands.has_key("viewsPanel"):
                if len(self.vf.viewsPanel.views) == 0:
                    return
            else:
                return
            idf = InputFormDescr(title="Save Views to file")
            idf.append({'name':'filename',
                        'widgetType':Pmw.EntryField,
                   'tooltip':"Enter the filename, a 'filename_oprient.py' (saves orientation)\nand 'filename_repr.db'(saves representation) will be created.",
                        'wcfg':{'label_text':'Filename:',
                                'labelpos':'w'},
                        'gridcfg':{'sticky':'we'},
                        })

            idf.append({'widgetType':SaveButton,
                        'name':'filebrowse',
                        'wcfg':{'buttonType':Tkinter.Button,
                                'title':'Save In File ...',
                                'types':[('Views orientation','*_orient.py'),
                                         ('Views representation', '*_repr.db'),
                                         ("", '*')],
                                'callback':self.setEntry_cb,
                                'widgetwcfg':{'text':'BROWSE'}},
                        'gridcfg':{'row':-1, 'sticky':'we'}})

            return idf


    def guiCallback(self):
        val = self.showForm('saveViewsToFile', force=1, modal=1)
        if not val: return

        if val.has_key('filename'):
            filename = val['filename']
            if file is not None:
                apply(self.doitWrapper, (filename,), {})


    def doit(self, filename, **kw):
        #save orientations
        filename, ext = os.path.splitext(filename)
        f=open(filename + "_orient.py", 'w')
        f.write("from numpy import array\n")
        # write the orients dictionary to the file:
        lines = "orients = {\n"
        for pname, pos in self.vf.viewsPanel.views.items():
            lines = lines + "'%s': {\n" % pname
            indent = "        "
            for prop, val in pos.items():
                if type(val) == Numeric.ndarray:
                    # create a string for numeric array:
                    valstr = "array(" + Numeric.array2string(val, precision =3, separator =",") + ", '%s')"%val.dtype.char
                else:
                    valstr = str(val)
                lines = lines + indent + "'%s': %s ,\n" % (prop, valstr)
            lines = lines + "},\n"
        lines = lines + "}\n"

        f.write(lines)
        f.close()
        # save representations
        import shelve
        f = shelve.open(filename + "_repr.db")
        if len(f.keys()):
            f.clear()
        for name, val in self.vf.viewsPanel.representations.items():
            f[name] = val
        f.close()
       
       
    def __call__(self, filename, **kw):
        if self.vf.commands.has_key("viewsPanel"):
            if len(self.vf.viewsPanel.views) == 0:
                return
        else:
            return
        name = os.path.splitext(filename)[0]
        if name.count("_repr") > 0:
            name = name.split("_repr")[0]
        elif name.count("_orient") > 0:
            name = name.split("_orient")[0]
        apply(self.doitWrapper, (name,), {})


    def setEntry_cb(self, filename):
        name = os.path.splitext(filename)[0]
        if name.count("_repr") > 0:
            name = name.split("_repr")[0]
        elif name.count("_orient") > 0:
            name = name.split("_orient")[0]
        ebn = self.cmdForms['saveViewsToFile'].descr.entryByName
        entry = ebn['filename']['widget']
        entry.setentry(name)

   
SaveViewsToFileGUI = CommandGUI()
SaveViewsToFileGUI.addMenuCommand('menuRoot', 'File','Views',
                                  cascadeName='Save', index = 14)


class ReadViews(MVCommand):

    """Command reads 'name_orient.py' and 'name_repr.db' files and adds/replaces the saved views
    in the SaveViews Command GUI"""

    def __init__(self):
        MVCommand.__init__(self)


    def buildFormDescr(self, formName):
        if formName == 'readViews':
            idf = InputFormDescr(title="Read Views")
            idf.append({'name':'orientfile',
                        'required':1,
                        'widgetType':Pmw.EntryField,
                        'tooltip':"Please type in the path to the _orient.py file \nor click on the BROWSE button to open a file browser",
                        'wcfg':{'labelpos':'w',
                                'label_text':"Orientations Filename",
                                },
                        'gridcfg':{'sticky':'w'}})

            idf.append({'widgetType':LoadButton,
                        'name':'browseOrient',
                        'wcfg':{'buttonType':Tkinter.Button,
                                'title':'Open views orientation file',
                                'types':[('Views orient','*_orient.py')],
                                'callback':self.setOrientEntry_cb,
                                'widgetwcfg':{'text':'BROWSE'}},
                        'gridcfg':{'row':-1, 'sticky':'we'}})
            idf.append({'name':'reprfile',
                        'required':1,
                        'tooltip':"Please type in the path to the _repr.db file\nor click on the BROWSE button to open a file browser",
                        'widgetType':Pmw.EntryField,
                        'wcfg':{'labelpos':'w',
                                'label_text':"Representations Filename",
                                },
                        'gridcfg':{'sticky':'w'}})

            idf.append({'widgetType':LoadButton,
                        'name':'browseRepr',
                        'wcfg':{'buttonType':Tkinter.Button,
                                'title': 'Open views representation file',
                                'types':[('Views orient','*_repr.db')],
                                'callback':self.setReprEntry_cb,
                                'widgetwcfg':{'text':'BROWSE'}},
                        'gridcfg':{'row':-1, 'sticky':'we'}})

            return idf



    def setOrientEntry_cb(self, filename):
        ebn = self.cmdForms['readViews'].descr.entryByName
        ebn['orientfile']['widget'].setentry(filename)
        if filename.count("_orient.py"):
            filename = filename.split("_orient.py")[0]
            rfilename = "%s_repr.db"%filename
            if os.path.exists(rfilename):
                ebn['reprfile']['widget'].setentry(rfilename)


    def setReprEntry_cb(self, filename):
        ebn = self.cmdForms['readViews'].descr.entryByName
        ebn['reprfile']['widget'].setentry(filename)
        if filename.count("_repr.db"):
            filename = filename.split("_repr.db")[0]
            ofilename = "%s_orient.py"%filename
            if os.path.exists(ofilename):
                ebn['orientfile']['widget'].setentry(ofilename)


    def guiCallback(self):
        val = self.showForm('readViews')
        if not val: return
        orientFilename = val['orientfile']
        reprFilename = val['reprfile']
        apply(self.doitWrapper, (orientFilename, reprFilename), {})


    def doit(self, orientFilename, reprFilename, **kw):
        if not os.path.exists(orientFilename):
            if os.path.exists("%s_orient.py"%orientFilename):
                orientFilename = "%s_orient.py"%orientFilename 
            else:
                warnings.warn("Warning: view orientation file %s does not exist" % orientFilename )
                return
        if not os.path.exists(reprFilename):
            if os.path.exists("%s_repr.db"%reprFilename):
                reprFilename = "%s_repr.db"%reprFilename
            else:
                warnings.warn("Warning: view representation file %s does not exist" % reprFilename)
                return
        #load orientations
        mydict = {}
        execfile(orientFilename,  globals(), mydict)
        if mydict.has_key("orients"):
            neworients = mydict['orients']
        else:
            warnings.warn("Warning: unknown file format (%s)"% orientFilename)
            return
        import shelve
        newrepr = shelve.open(reprFilename)
        if not self.vf.commands.has_key("viewsPanel"):
            self.browseCommands("viewsCommands", package="Pmv")
        cmd = self.vf.commands["viewsPanel"]
        if not cmd:
            return
        cmd.guiCallback()
        if len(cmd.views):
            # ask the user if he wants to add or replace the views:
            dialog = Pmw.Dialog( self.vf.master, title = "Load Views",
                                buttons = ('ADD', 'REPLACE', 'Cancel'),
                                defaultbutton = 'ADD')
            dialog.withdraw()
            label = Tkinter.Label(dialog.interior(),
                                  text = "Would you like to ADD new views\nor REPLACE existing ones?", pady = 10) 
            label.pack(expand = 1, fill = 'both', padx = 4, pady = 4)
            action = dialog.activate(geometry = '+%d+%d' % (self.vf.master.winfo_x()+200, self.vf.master.winfo_y()+200))
            if action == "Cancel": return
            elif action == "REPLACE":
                cmd.deleteViews()
        nviews = cmd.allViews
        self.vf.GUI.VIEWER.master.master.lift()
        #add new viewes
        for i, name in enumerate(neworients.keys()):
            if not newrepr.has_key(name):
                continue
            newname = name
            # if saved view  has "custom" name,
            # check if a orient with that name already exists in Bookmarks:
            if not name.startswith("view"):
                if cmd.views.has_key(name):
                    # name exists -> create newname by adding an
                    # integer to the name 
                    count = 0
                    for k in cmd.views.keys():
                        if k.startswith(name):
                            count = count +1
                    newname = name+"_"+str(count)
            else:
                newname = 'view%d'% (nviews + i)
            cmd.views[newname] = neworients[name]
            cmd.representations[newname] = newrepr[name]
            director = self.vf.GUI.VIEWER.GUI.createOrientScenario(newname, cmd.views[newname])
            cmd.viewsDirectors[newname] = director
            cmd.addViewButton(newname, icon = False)
        newrepr.close()


    def __call__(self, orientFilename, reprFilename, **kw):
        """None--->mv.readViews(orientFilename, reprFilename)
        """
        apply(self.doitWrapper, (orientFilename, reprFilename), kw)


ReadViewsCommandGUI = CommandGUI()
ReadViewsCommandGUI.addMenuCommand('menuRoot', 'File','Views',
                                  cascadeName='Read', index = 4)



commandList = [{'name':'viewsPanel','cmd':ViewsCommand(), 'gui':ViewsCommandGUI},
               {'name':'saveViewsToFile','cmd':SaveViewsToFile(), 'gui':SaveViewsToFileGUI},
               {'name': 'readViews', 'cmd':ReadViews(), 'gui':ReadViewsCommandGUI}]


## def initModule(viewer):
##     # load the commands if the scenario and SimPy can be imported
##     scenario_import = True
##     try:
##         from scenario.director import Director
##     except ImportError:
##         scenario_import = False
##     if scenario_import:
##         for dict in commandList:
##             viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
