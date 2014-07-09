from DejaVu.GeomChooser import GeomChooser
from Pmv.GeomFilter import GeomFilter
from Pmv.moleculeViewer import MoleculeViewer
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser
import Tkinter


class PmvSetChooser(ListChooser):

    def __init__(self, root, mv, title="select a set:",
                 command=None, mode="single", cwcfg=None):
        self.mv = mv
        pmvsets = self.getPmvSets()
        ListChooser.__init__(self, root, mode=mode, title=title, entries=pmvsets,
                    command=command, cwcfg=cwcfg)
        self.widget.configure(exportselection = False)


    def getPmvSets(self):
        """Return a list containing the names of pmv sets"""
        pmvsets = []
        for key, value in self.mv.sets.items():
            pmvsets.append( (key, value.comments) )
##         if len(pmvsets):
##             pmvsets.insert(0, ("None", " "))
        return pmvsets


    def updateList(self):
        """Update the entries of the pmvset chooser""" 
        pmvsets = self.getPmvSets()
        self.setlist(pmvsets)


    def getSets(self):
        items = []
        setNames = self.get()
        for name in setNames:
            if self.mv.sets.has_key(name):
                items.append( (name, self.mv.sets[name]))

        return items

    def getNodes(self):
        nodes = None
        sets = self.getSets()
        if len(sets):
            nodes = [] 
            for set in  sets:
                nodes = nodes + set[1]
        return nodes


class PmvGeomChooser(GeomChooser):
    """
    The PmvGeomChooser object has two ListBox widgets :
      - first displays  a list of geometries present in the DejaVu.Viewer object.
      - second displays a list of Pmv sets
    """

    def __init__(self, mv, root=None, showAll=True, filterFunction=None,
                 
                 command=None, pmvsetCommand=None, refreshButton=True, showAllButton=True):
        """
        PmvGeomChooser constructor

        PmvGeomChooserObject <- PmvGeomChooser(vf, showAll=True, filterFunction=None, root=None,
                 command=None)

        - mv is an instance of MoleculeViewer 
        - showAll is a boolean. When True all objects present in the Viewer are shown
        - filterFunction is an optional function that will be called when
          showAll is False. I takes one argument (a Viewer object) and returns a
          list of (name, [geoms]) pairs. The names will be displayed in the GUI
          for representing the corresponding list of geometry objects.
        - root is the master in which the chooser will be created.
        - command is the fucntion call upon selection in the geometry list
        - pmvsetCommand - fucntion call upon selection in the pmv sets list
        """
        assert isinstance(mv, MoleculeViewer)
        self.mv = mv
        if filterFunction is None:
            self.gf = GeomFilter(mv)
            filterFunction = self.gf.filter
        GeomChooser.__init__(self, self.mv.GUI.VIEWER, showAll=showAll,
                             filterFunction=filterFunction, root=root, #self.frame,
                             command=command, refreshButton=refreshButton,
                             showAllButton=showAllButton)
        self.chooserW.mode = 'single'
        self.chooserW.widget.configure(exportselection = False) # this is done to prevent disappearing
        #of the ListBox selection  when a text is selected in another widget or window. 
        self.chooserW.widget.configure(height=15)
        self.setChooser=PmvSetChooser(self.frame, mv, title = "select a set:",
                                      command=pmvsetCommand, mode="multiple" )
        self.setChooser.widget.configure(height=5)
        self.setChooser.pack(side='top', fill='both', expand=1)
        

    def updateList(self):
        """Update the entries of geometry and pmvset choosers""" 
        GeomChooser.updateList(self)
        self.setChooser.updateList()

    def getSets(self):
        return self.setChooser.getSets()

    def getNodes(self):
        return self.setChooser.getNodes()


    def showAll_cb(self, even=None):
        val = self.showAllVar.get()
        self.showAll = val
        self.updateList()



