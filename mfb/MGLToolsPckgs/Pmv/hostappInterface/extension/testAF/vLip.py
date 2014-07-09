#execfile("/Library/MGLTools/1.5.6.csv/MGLToolsPckgs/Pmv/hostappInterface/extension/testAF/vLip.py")
import numpy
from time import time

import sys


#AUTOFILL
from AutoFill.Ingredient import SingleSphereIngr, MultiSphereIngr
from AutoFill.Ingredient import MultiCylindersIngr
from AutoFill.Organelle import Organelle
from AutoFill.Recipe import Recipe
from AutoFill.HistoVol import HistoVol

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
# Surface:
rSurf1 = Recipe()
ingr1qo1 = MultiSphereIngr( MSca*.0001/3., color=limegreen, pdb='1qo1',
                             name='ATP SYNTHASE',
                             sphereFile=wrkDir+'/recipes/membrane/1qo1.sph',
                             meshFile=wrkDir+'/recipes/membrane/1qo1',
                             packingPriority=1,
                             jitterMax=(1,1,0.2),
                             principalVector=(0,0,-1))#,
                             #packingMode='close')
#Surf1.addIngredient(ingr1qo1)

## cyl test 1
cyl1Ingr = MultiCylindersIngr(MSca*0.1, color=coral, pdb='1CYL',
                             name='SingleCylinder', radii=[[8.]],
                              positions=[[[0,0,0]]], positions2=[[[20,0,0]]],
                              packingPriority=1,
                              jitterMax=(1,1,0.2),
                              principalVector=(1,0,0),
                              meshFile=plgDir+'/extension/testAF/Lip',
                              #packingMode='close',
                              rejectionThreshold=30
                              )
rSurf1.addIngredient(cyl1Ingr)
# 1qo1


##
## Matrix
##
rMatrix1 = Recipe()

##
## Cytoplasm:
##
rCyto = Recipe()

# 1TWT
ingr1TWT = MultiSphereIngr( MSca*.000005, name='30S RIBOSOME', pdb='1TWT',
                            sphereFile=wrkDir+'/recipes/cyto/1TWT_centered.sph',
                            meshFile=wrkDir+'/recipes/cyto/1TWT_centered',
                            color=khaki, packingPriority=1)
#rCyto.addIngredient( ingr1TWT )

# 1TWV
#ingr1TWV = MultiSphereIngr( .0001, name='1TWV 50S RIBOSOME',
#                           sphereFile='recipes/cyto/1TWV_centered_16.sph',
#                           meshFile='recipes/cyto/1TWV_centered',
#                           color=cornflowerblue, packingPriority=1)
#rCyto.addIngredient( ingr1TWV )

# vesicle
from DejaVu.IndexedPolygons import IndexedPolygonsFromFile

# create HistoVol
h1 = HistoVol()

# create and add oganelles
#=> how to do it interactively?
#select a mesh, get Polygon information and create the Organelle,
#but then dont need to draw it...
#bb = helper.getCornerPointCube(selectedObject)
#what about the organell
#c4dorganlle = currentSelection
#faces = c4dorganlle.get_polygons()
#vertices = c4dorganlle.get_points()
#vnormals = None 

"""geomS = IndexedPolygonsFromFile(wrkDir+'/organelles/vesicle_r20nm', 'vesicle')
faces = geomS.getFaces()
vertices = geomS.getVertices()
vnormals = geomS.getVNormals()
o1 = Organelle(vertices, faces, vnormals)
h1.addOrganelle(o1)
"""

# set recipes
h1.setExteriorRecipe(rCyto)

#o1.setSurfaceRecipe(rSurf1)
#o1.setInnerRecipe(rMatrix1)

#again how interactively put ingrediants....
#maybe pred_displayFill can load everyavailable ingrediant....or at least create
#an empty for everyone of them

"""print 'Bounding box', h1.boundingBox
# add padding
bb = h1.boundingBox
pad = 100.
x,y,z = bb[0]
bb[0] = [x-pad, y-pad, z-pad]
x,y,z = bb[1]
bb[1] = [x+pad, y+pad, z+pad]
print 'Bounding box with padding', h1.boundingBox

(x,y,z), maxi = h1.boundingBox
bb = [[0, y, z], maxi]
#bb = [[0, 0, 0], maxi]
h1.buildGrid(boundingBox=bb)#, gridFileOut='1vesicle_new.grid' )
#h1.buildGrid(gridFileOut='1vesicle_new.grid' )

#display the organel, the box, and prepare the hierachy...
execfile(plgDir+'/extension/testAF/c_displayPreFill.py')

print 'gridSpacing', h1.gridSpacing
#h1.printFillInfo()

#raw_input('press enter to start')
t1 = time()
h1.fill3(seedNum=0)

print 'time to fill', time()-t1
#h1.printFillInfo()

t1 = time()
execfile(plgDir+'/extension/testAF/c_displayFill.py')
print 'time to display', time()-t1
"""
## for ingr, jitterList, collD1, collD2 in h1.successfullJitter:
##     print ingr.name[:4], len(ingr.positions), len(jitterList)

## len(h1.failedJitter)
## len(h1.successfullJitter)

## t1 = time()
## h1.fill3(seedNum=3.40)
## print 'time to fill', time()-t1
## h1.printFillInfo()
## execfile('displayFill.py')

## t1 = time()
## h1.fill3(seedNum=43420)
## print 'time to fill', time()-t1
## h1.printFillInfo()
## execfile('displayFill.py')
from Pmv.hostappInterface.cinema4d import helperC4D as helper
#display the organel, the box, and prepare the hierachy...
doc = helper.getCurrentScene()
sel = doc.get_selection()

c4dorganlle = sel[0]
helper.triangulate(c4dorganlle)

faces = c4dorganlle.get_polygons()
c4dvertices = c4dorganlle.get_points()
vertices = map(helper.vc4d,c4dvertices)
vnormals = helper.GetFaces(c4dorganlle)
o1 = Organelle(vertices, faces, vnormals)
h1.addOrganelle(o1)
o1.setSurfaceRecipe(rSurf1)

# add padding
bb = h1.boundingBox
pad = 100.
x,y,z = bb[0]
bb[0] = [x-pad, y-pad, z-pad]
x,y,z = bb[1]
bb[1] = [x+pad, y+pad, z+pad]
print 'Bounding box with padding', h1.boundingBox


h1.setMinMaxProteinSize()
print 'Cyto', rCyto.getMinMaxProteinSize()
print 'Surf', rSurf1.getMinMaxProteinSize()
print 'Matrix', rMatrix1.getMinMaxProteinSize()
#print 'o1', o1.getMinMaxProteinSize()
print 'smallest', h1.smallestProteinSize
print 'largest', h1.largestProteinSize

execfile(plgDir+'/extension/testAF/c_displayPreFill.py')
from Pmv.hostappInterface.cinema4d import helperC4D as helper



def FILL(h):
    doc =helper.getCurrentScene()
    box = doc.get_selection()[0]
    bb=helper.getCornerPointCube(box)
    h.buildGrid(boundingBox=bb)
    h.fill3(seedNum=0)
    execfile(plgDir+'/extension/testAF/c_displayFill.py')
    
    
#FILL(h1,box)
"""
sel = doc.get_selection()
bb=helper.getCornerPointCube(sel[0])
h1.buildGrid(boundingBox=bb)
"""
#h1.fill3(seedNum=0)

#print 'time to fill', time()-t1
#h1.printFillInfo()

#t1 = time()
#execfile(plgDir+'/extension/testAF/c_displayFill.py')
