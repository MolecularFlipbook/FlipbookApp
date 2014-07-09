#execfile("/Library/MGLTools/1.5.6.csv/MGLToolsPckgs/Pmv/hostappInterface/extension/testAF/vesicle.py")
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

## cyl test 1
cyl1Ingr = MultiCylindersIngr(MSca*.001, color=coral, pdb='1CYL',
                             name='SingleCylinder', radii=[[23]],
                              positions=[[[-35,0,0]]], positions2=[[[45,0,0]]],
                              packingPriority=1,
                              principalVector=(1,0,0)
                              )

rSurf1.addIngredient(cyl1Ingr)

cylCoord1 = [ (-35,0,0), (45,0,0),  (45,0,0),    (85, 40, 0),]
cylCoord2 = [ (45,0,0),  (85,40,0), (105, -40,0), (135, 40, 30)]
cylRadii = [25, 20, 16, 16]

cyl4Ingr = MultiCylindersIngr(MSca*.001, color=aquamarine, pdb='1CYL',
                             name='4Cylinders', radii=[cylRadii],
                              positions=[cylCoord1], positions2=[cylCoord2],
                              packingPriority=1,
                              principalVector=(1,0,0)
                              )

rSurf1.addIngredient(cyl4Ingr)

## # 1h6i
ingr1h6i = SingleSphereIngr( MSca*.001, color=aquamarine, pdb='1h6i',
                             name='AUQAPORINE',
                             sphereFile=wrkDir+'/recipes/membrane/1h6i.sph',
                             meshFile=wrkDir+'/recipes/membrane/1h6i',
                             packingPriority=10,
                             jitterMax=(1,1,0.2),
                             principalVector=(0,0,1))
rSurf1.addIngredient(ingr1h6i)

# 1zll
ingr1zll = SingleSphereIngr( MSca*.001, color=darkorchid, pdb='1zll',
                             name='PHOSPHOLAMBAN',
                             sphereFile=wrkDir+'/recipes/membrane/1zll.sph',
                             meshFile=wrkDir+'/recipes/membrane/1zll',
                             packingPriority=5,
                             jitterMax=(1,1,0.2),
                             principalVector=(0,0,-1))
rSurf1.addIngredient(ingr1zll)

# 2afl
ingr2afl = SingleSphereIngr( MSca*.001, color=lightcoral, pdb='2afl',
                             name='PROTON TRANSPORT',
                             sphereFile=wrkDir+'/recipes/membrane/2afl.sph',
                             meshFile=wrkDir+'/recipes/membrane/2afl',
                             packingPriority=10,
                             jitterMax=(1,1,0.2),
                             principalVector=(0,0,-1))
rSurf1.addIngredient(ingr2afl)

# 2uuh
ingr2uuh = MultiSphereIngr( MSca*.001, color=gold, name='C4 SYNTHASE',
                            sphereFile=wrkDir+'/recipes/membrane/2uuh.sph',
                            meshFile=wrkDir+'/recipes/membrane/2uuh', pdb='2uuh',
                            packingPriority=5,
                            jitterMax=(1,1,.2),
                            principalVector=(0,0,-1))
rSurf1.addIngredient(ingr2uuh)

# 1yg1
ingr1yg1 = MultiSphereIngr( MSca*.001, color=khaki, pdb='1yg1',
                             name='FACILITATIVE GLUCOSE',
                             sphereFile=wrkDir+'/recipes/membrane/1yg1.sph',
                             meshFile=wrkDir+'/recipes/membrane/1yg1',
                             packingPriority=5,
                             jitterMax=(1,1,0.2),
                             principalVector=(0,0,-1))
rSurf1.addIngredient(ingr1yg1)

# 1ojc
ingr1ojc = MultiSphereIngr( MSca*.001, color=blueviolet, pdb='1ojc',
                             name='OXIDOREDUCTASE',
                             sphereFile=wrkDir+'/recipes/membrane/1ojc.sph',
                             meshFile=wrkDir+'/recipes/membrane/1ojc',
                             packingPriority=10,
                             jitterMax=(1,1,0.2),
                             principalVector=(0,0,-1))
rSurf1.addIngredient(ingr1ojc)

# 1qo1
ingr1qo1 = MultiSphereIngr( MSca*.0005, color=limegreen, pdb='1qo1',
                             name='ATP SYNTHASE',
                             sphereFile=wrkDir+'/recipes/membrane/1qo1.sph',
                             meshFile=wrkDir+'/recipes/membrane/1qo1',
                             packingPriority=1,
                             jitterMax=(1,1,0.2),
                             principalVector=(0,0,-1))
rSurf1.addIngredient(ingr1qo1)

# 2abm
ingr2abm = MultiSphereIngr( MSca*.001, color=darkcyan, pdb='2abm',
                             name='AQUAPORIN TETRAMER',
                             sphereFile=wrkDir+'/recipes/membrane/2abm.sph',
                             meshFile=wrkDir+'/recipes/membrane/2abm',
                             packingPriority=2,
                             jitterMax=(1,1,0.2),
                             principalVector=(0,0,-1))
rSurf1.addIngredient(ingr2abm)

# 3g61
ingr3g61 = MultiSphereIngr( MSca*.001, color=darkcyan, pdb='3g61',
                             name='P-GLYCOPROTEIN',
                             sphereFile=wrkDir+'/recipes/membrane/3g61.sph',
                             meshFile=wrkDir+'/recipes/membrane/3g61',
                             packingPriority=2,
                             jitterMax=(1,1,0.2),
                             principalVector=(0,0,1))
rSurf1.addIngredient(ingr3g61)

# 2bg9 
ingr2bg9 = MultiSphereIngr( MSca*.001, color=deeppink, pdb='2bg9',
                             name='ION CHANNEL/RECEPTOR',
                             sphereFile=wrkDir+'/recipes/membrane/2bg9.sph',
                             meshFile=wrkDir+'/recipes/membrane/2bg9',
                             packingPriority=2,
                             jitterMax=(1,1,0.2),
                             principalVector=(0,0,-1))
rSurf1.addIngredient(ingr2bg9)

# 2a79
ingr2a79 = MultiSphereIngr( MSca*.001, color=gold, pdb='2a79',
                             name='POTASSIUM CHANNEL',
                             sphereFile=wrkDir+'/recipes/membrane/2a79.sph',
                             meshFile=wrkDir+'/recipes/membrane/2a79',
                             packingPriority=1,
                             jitterMax=(1,1,0.2),
                             principalVector=(0,0,1))
rSurf1.addIngredient(ingr2a79)

##
## Matrix
##
rMatrix1 = Recipe()
kinase0 = SingleSphereIngr( MSca*.075,  16., color=steelblue,
                            name='kinase0', nbJitter=20, pdb='0ABL',
                            meshFile=wrkDir+'/recipes/cyto/1ABL_centered',
                            packingMode='close')
rMatrix1.addIngredient( kinase0 )

##
## Cytoplasm:
##
rCyto = Recipe()

# 1ABL
from DejaVu.colors import brown, peru, saddlebrown, darkred
kinase1 = SingleSphereIngr( MSca*.08,  16., color=brown, name='kinase1',
                            meshFile=wrkDir+'/recipes/cyto/1ABL_centered', pdb='1ABL')
## kinase2 = SingleSphereIngr( MSca*.005,  16., color=peru, name='2ABL kinase2',
##                             meshFile='recipes/cyto/1ABL_centered')
## kinase3 = SingleSphereIngr( MSca*.005,  16., color=saddlebrown,
##                             name='3ABL kinase3',
##                             meshFile='recipes/cyto/1ABL_centered')
## kinase4 = SingleSphereIngr( MSca*.005,  16., color=darkred, name='4ABL kinase4',
##                             meshFile='recipes/cyto/1ABL_centered')

rCyto.addIngredient( kinase1 )
## #rCyto.addIngredient( kinase2 )
## #rCyto.addIngredient( kinase3 )
## #rCyto.addIngredient( kinase4 )
# 1AON
GroelIngr1 = MultiSphereIngr( MSca*.00004, name='Groel', pdb='1AON',
                              sphereFile=wrkDir+'/recipes/cyto/1AON_centered.sph',
                              meshFile=wrkDir+'/recipes/cyto/1AON_centered',
                              color=red, packingPriority=2)
rCyto.addIngredient( GroelIngr1 )

# 2CPK
ingr2CPK = MultiSphereIngr( MSca*.0004, name='PHOSPHOTRANSFERASE', pdb='2CPK',
                            sphereFile=wrkDir+'/recipes/cyto/2CPK_centered.sph',
                            meshFile=wrkDir+'/recipes/cyto/2CPK_centered',
                            color=limegreen, packingPriority=4)
rCyto.addIngredient( ingr2CPK )

# 1CZA
ingr1CZA = MultiSphereIngr( MSca*.0004, name='TRANSFERASE', pdb='1CZA',
                            sphereFile=wrkDir+'/recipes/cyto/1CZA_centered.sph',
                            meshFile=wrkDir+'/recipes/cyto/1CZA_centered',
                            color=darkorchid, packingPriority=3)
rCyto.addIngredient( ingr1CZA )

# 2OT8
ingr2OT8 = MultiSphereIngr( MSca*.0001, name='TRANSPORT PROTEIN', pdb='2OT8',
                            sphereFile=wrkDir+'/recipes/cyto/2OT8_centered.sph',
                            meshFile=wrkDir+'/recipes/cyto/2OT8_centered',
                            color=tomato, packingPriority=1)
rCyto.addIngredient( ingr2OT8 )

# 1TWT
ingr1TWT = MultiSphereIngr( MSca*.00005, name='30S RIBOSOME', pdb='1TWT',
                            sphereFile=wrkDir+'/recipes/cyto/1TWT_centered.sph',
                            meshFile=wrkDir+'/recipes/cyto/1TWT_centered',
                            color=khaki, packingPriority=1)
rCyto.addIngredient( ingr1TWT )

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
geomS = IndexedPolygonsFromFile(wrkDir+'/organelles/vesicle_r20nm', 'vesicle')
faces = geomS.getFaces()
vertices = geomS.getVertices()
vnormals = geomS.getVNormals()
o1 = Organelle(vertices, faces, vnormals)
h1.addOrganelle(o1)

# set recipes
h1.setExteriorRecipe(rCyto)

o1.setSurfaceRecipe(rSurf1)
#o1.setInnerRecipe(rMatrix1)

h1.setMinMaxProteinSize()
print 'Cyto', rCyto.getMinMaxProteinSize()
print 'Surf', rSurf1.getMinMaxProteinSize()
print 'Matrix', rMatrix1.getMinMaxProteinSize()
print 'o1', o1.getMinMaxProteinSize()
print 'smallest', h1.smallestProteinSize
print 'largest', h1.largestProteinSize
print 'Bounding box', h1.boundingBox
# add padding
bb = h1.boundingBox
pad = 200.
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
