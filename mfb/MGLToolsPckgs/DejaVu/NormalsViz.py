## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

from DejaVu.Polylines import Polylines
import numpy.oldnumeric as Numeric

class NormalsViewer:
    """Object that take a DejaVu geometry and a viewer and displays the
    geometry's normals in the viewer"""

    def __init__(self, geom, viewer):
        self.geom = geom
        self.normalsGeom = Polylines('normals_for_'+geom.name)
        self.viewer = viewer
        viewer.AddObject(self.normalsGeom, parent=geom)
        self.update()
        
    def update(self):
        vertices = self.geom.getVertices()
        normals = self.geom.getVNormals()
        pts = Numeric.concatenate( (vertices, vertices+normals), 1)
        pts = Numeric.reshape( pts, (len(vertices),2,-1) ).astype('f')
        self.normalsGeom.Set(vertices = pts) 
        self.viewer.Redraw()
       
