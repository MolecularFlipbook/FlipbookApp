from DejaVu.geomTree import DejaVuGeomNode
from DejaVu.geomTree import DejaVuGeomTreeWithButtons

from DejaVu.Geom import Geom
from DejaVu.IndexedPolygons import IndexedPolygons
from DejaVu.IndexedPolylines import IndexedPolylines
from DejaVu.Polylines import Polylines
from DejaVu.Spheres import Spheres
from DejaVu.Cylinders import Cylinders
from DejaVu.glfLabels import GlfLabels

class PmvGeomTreeWithButtons(DejaVuGeomTreeWithButtons):
    """
    Class to display a tree for PMV geometry.
    """
    pass
##     def __init__(self, master, root, iconsManager=None, vf=None,
##                  idleRedraw=True, nodeHeight=18, headerHeight=30,
##                  treeWidth=150, **kw):
##         # add a compound selector entry
##         DejaVuGeomTreeWithButtons.__init__(
##             self, master, root, iconsManager=iconsManager, 
##             idleRedraw=idleRedraw, nodeHeight=nodeHeight,
##             headerHeight=headerHeight, treeWidth=treeWidth, **kw)


class PmvGeomNode(DejaVuGeomNode):
    """
    The first level of this tree is either a molecule or a container.
    The second level are geometry object. Columns are used to modify geoms
    """

    def getChildren(self):
        """
        return children for object associated with this node.
        By default we return object.children. Override this method to
        selectively show children
        """
        children = []
        for child in self.object.children:
            #if not child.visible:
            #    continue
            if child.parent.name=='lines':
                continue
            if child.LastParentBeforeRoot().name=='misc':
                continue
            if child.name[:4] in ['Heli', 'Turn', 'Coil', 'Stra', 'chai']:
                continue
            if child.name[:9]=='selection':
                continue
            if child.name[-7:]=='APBSbox':
                continue
            children.append(child)

        return children



## if __name__ == '__main__':
## import Tkinter
## root = Tkinter.Toplevel()
## vi = self.GUI.VIEWER

## from Pmv.geomTree import PmvGeomNode, PmvGeomTreeWithButtons
## from DejaVu.geomTree import DejaVuGeomTreeWithButtons
## from mglutil.gui.BasicWidgets.Tk.trees.tree import IconsManager

## iconsManager = IconsManager(['Icons'], 'DejaVu')

## rootnode = PmvGeomNode(vi.rootObject, None)

## tree = PmvGeomTreeWithButtons(root, rootnode, nodeHeight=18,
##                               iconsManager=iconsManager, headerHeight=0,
##                               treeWidth=180, selectionMode='single')
## tree.pack(side='bottom', expand=1, fill='both')
## rootnode.expand()

#execfile('pmvGeomPicker.py')

