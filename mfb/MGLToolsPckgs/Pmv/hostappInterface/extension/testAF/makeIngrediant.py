#execfile("/Library/MGLTools/1.5.6.csv/MGLToolsPckgs/Pmv/hostappInterface/extension/testAF/makeIngrediant.py")
import numpy
from time import time

import sys


#AUTOFILL
from AutoFill.Ingredient import SingleSphereIngr, MultiSphereIngr
from AutoFill.Ingredient import MultiCylindersIngr
from AutoFill.Organelle import Organelle
from AutoFill.Recipe import Recipe
from AutoFill.HistoVol import HistoVol
from AutoFill.autofill_viewer import AFViewer

#Directory
import AutoFill
wrkDir = AutoFill.__path__[0]
from  Pmv import hostappInterface
plgDir = hostappInterface.__path__[0]

#DEJAVU COLORS
from DejaVu.colors import red, aliceblue, antiquewhite, aqua, \
     aquamarine, azure, beige, bisque, black, blanchedalmond, \
     blue, blueviolet, brown, burlywood, cadetblue, \
     chartreuse, chocolate, coral, cornflowerblue, cornsilk, \
     crimson, cyan, darkblue, darkcyan, darkgoldenrod, \
     orange, purple, deeppink, lightcoral, \
     blue, cyan, mediumslateblue, steelblue, darkcyan, \
     limegreen, darkorchid, tomato, khaki, gold, magenta, green


#define the viewer type dejavu,c4d,blender
ViewerType='c4d'

MSca = 1.0
## Surface:
rSurf1 = Recipe()
## cyl test 1
cyl1Ingr = MultiCylindersIngr(2, color=coral, pdb='1CYL',
                             name='SingleCylinder', radii=[[23]],
                              positions=[[[-35,0,0]]], positions2=[[[45,0,0]]],
                              packingPriority=1,
                              principalVector=(1,0,0)
                              )

rSurf1.addIngredient(cyl1Ingr)

cylCoord1 = [ (-35,0,0), (45,0,0),  (45,0,0),    (85, 40, 0),]
cylCoord2 = [ (45,0,0),  (85,40,0), (105, -40,0), (135, 40, 30)]
cylRadii = [25, 20, 16, 16]

cyl4Ingr = MultiCylindersIngr(3, color=aquamarine, pdb='1CYL',
                             name='4Cylinders', radii=[cylRadii],
                              positions=[cylCoord1], positions2=[cylCoord2],
                              packingPriority=1,
                              principalVector=(1,0,0)
                              )

rSurf1.addIngredient(cyl4Ingr)
##
## Matrix
##
rMatrix1 = Recipe()
##
## Cytoplasm:
##
rCyto = Recipe()
for i in [15,25]:
    sph = SingleSphereIngr( 1,  float(i), color=steelblue,
                            name='SPH'+str(i), nbJitter=20,
                            #packingMode='close'
                            packingPriority=1,
                            jitterMax=(0.,0.,0.),
                            )
    rCyto.addIngredient( sph )

# vesicle
from DejaVu.IndexedPolygons import IndexedPolygonsFromFile

# create HistoVol
h1 = HistoVol()
# set recipes
h1.setExteriorRecipe(rCyto)
#o1.setSurfaceRecipe(rSurf1)
#o1.setInnerRecipe(rMatrix1)

from Pmv.hostappInterface.cinema4d_dev import helperC4D as helper
#display the organel, the box, and prepare the hierachy...
doc = helper.getCurrentScene()
sel = doc.GetSelection()

c4dorganlle = sel[0]
helper.triangulate(c4dorganlle)
faces,vertices,vnormals = helper.DecomposeMesh(c4dorganlle,edit=True,copy=True,tri=True)

o1 = Organelle(vertices, faces, vnormals)
h1.addOrganelle(o1)
o1.setSurfaceRecipe(rSurf1)
#o1.setInnerRecipe(rCyto)

#define the viewer type dejavu,c4d,blender
ViewerType='c4d'
afviewer = AFViewer(ViewerType=ViewerType)
#make some option here 
afviewer.doPoints = False
afviewer.doSpheres = False

afviewer.quality = 1 #lowest quality for sphere and cylinder

h1.setMinMaxProteinSize()
print 'Cyto', rCyto.getMinMaxProteinSize()
print 'Surf', rSurf1.getMinMaxProteinSize()
print 'Matrix', rMatrix1.getMinMaxProteinSize()
#print 'o1', o1.getMinMaxProteinSize()
print 'smallest', h1.smallestProteinSize
print 'largest', h1.largestProteinSize

pad = 100.
afviewer.SetHistoVol(h1,pad,display=False)
afviewer.displayPreFill()


def FILL(h):
    doc =helper.getCurrentScene()
    box = doc.GetSelection()[0]
    bb=helper.getCornerPointCube(box)
    h.buildGrid(boundingBox=bb)
    #afviewer.displayFillBox(bb)
    t1 = time()
    h.fill3(seedNum=0)
    t2 = time()
    print 'time to fill', t2-t1
    afviewer.displayFill()
    print 'time to display', time()-t2
    
#FILL(h1)
#afviewer.displayOrganellesPoints()
#afviewer.displayFreePoints()