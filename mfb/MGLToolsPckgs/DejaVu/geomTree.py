import Tkinter
from mglutil.gui.BasicWidgets.Tk.trees.tree import IconsManager
from mglutil.gui.BasicWidgets.Tk.trees.TreeWithButtons import \
     ColumnDescriptor ,TreeWithButtons, NodeWithButtons

from DejaVu.Geom import Geom
from DejaVu.IndexedPolygons import IndexedPolygons
from DejaVu.IndexedPolylines import IndexedPolylines
from DejaVu.Polylines import Polylines
from DejaVu.Spheres import Spheres
from DejaVu.Cylinders import Cylinders
from DejaVu.glfLabels import GlfLabels

class DejaVuGeomTreeWithButtons(TreeWithButtons):
    """
    Class to display a tree for DejaVu geoemtry.
    """

    def __init__(self, master, root, iconsManager=None,
                 idleRedraw=True, nodeHeight=18, headerHeight=30,
                 treeWidth=150, **kw):
        # add a compound selector entry
        kw['iconsManager'] = iconsManager
        kw['idleRedraw'] = idleRedraw
        kw['nodeHeight'] = nodeHeight
        kw['headerHeight'] = headerHeight
        kw['treeWidth'] = treeWidth
        TreeWithButtons.__init__( *(self, master, root), **kw )

        canvas = self.canvas


class DejaVuGeomNode(NodeWithButtons):
    """
    The first level of this tree is either a molecule or a container.
    The second level are geoemtry object. Columns are used to modify geoms
    """

    def getChildren(self):
        """
        return children for object associated with this node.
        By default we return object.children. Override this method to
        selectively show children
        """
        return self.children

    
    def getIcon(self):
        """
        return node's icons for DejaVu geometry objects 
        """
        iconsManager = self.tree().iconsManager
        object = self.object

        if isinstance(object, IndexedPolygons):
            icon = iconsManager.get("mesh16.png", self.tree().master)
        elif isinstance(object, IndexedPolylines) or \
                 isinstance(object, Polylines):
            icon = iconsManager.get("lines16.png", self.tree().master)
        elif isinstance(object, Spheres):
            icon = iconsManager.get("spheres16.png", self.tree().master)
        elif isinstance(object, Cylinders):
            icon = iconsManager.get("cyl16.png", self.tree().master)
        elif isinstance(object, GlfLabels):
            icon = iconsManager.get("labels16.png", self.tree().master)
        else: # isinstance(object, Geom):
            icon = iconsManager.get("geom16.png", self.tree().master)

        if icon:
            self.iconWidth = icon.width()
        else:
            self.iconWidth = 0
        return icon

if __name__ == '__main__':
    root = Tkinter.Toplevel()
    vi = self.GUI.VIEWER

    iconsManager = IconsManager(['Icons'], 'DejaVu')

    rootnode = DejaVuGeomNode(vi.rootObject, None)

    tree = DejaVuGeomTreeWithButtons(root, rootnode, self, nodeHeight=18,
                                     iconsManager=iconsManager, headerHeight=0,
                                     treeWidth=180, selectionMode='multiple')
    tree.pack(side='bottom', expand=1, fill='both')
    rootnode.expand()
