# display extra cellular spheres
from mglutil.hostappli import pdb_blender as bl
import Blender
import bpy
from Blender import *
from Blender.Mathutils import *
from Blender import Mesh
from Blender import Object
from Blender import Material
from Blender import Mathutils
from Blender import Window, Scene, Draw


scn = bl.getCurrentScene()

verts1 = []
radii1 = []
colors1 =[]
master = orgaToMasterGeom[h1]
print master

for pos, rot, ingr, ptInd in h1.molecules:
    level = ingr.maxLevel
    px = ingr.transformPoints(pos, rot, ingr.positions[level])
    for ii in range(len(ingr.radii[level])):
        verts1.append( px[level][ii] )
        radii1.append( ingr.radii[level][ii] *2.)
        colors1.append( ingr.color)

print len(verts1)
bg = bl.newEmpty('spheres')
bl.addObjectToScene(scn,bg)
meshsphere=Mesh.Primitives.UVsphere(int(10),int(10),1)
meshsphere.name="basesphere"
for face in meshsphere.faces: face.smooth=1
basesphere=bl.getCurrentScene().objects.new(meshsphere,"basesphere")
basesphere.restrictSelect=True

if len(verts1):
    sphs = bl.instancesSphere('spheres',verts1,radii1,meshsphere,colors1,scn,parent=bg)
    #need create all the sphere..
    #sph = Spheres('spheres', inheritMaterial=False, centers=verts1,
     #             materials=colors1, radii=radii1, visible=1)
    #vi.AddObject(sph, parent=master)

# display extra cellular meshes
meshGeoms = {}
for pos, rot, ingr, ptInd in h1.molecules:
    if ingr.mesh: # display mesh
        geom = ingr.mesh
        mat = rot.copy()
        mat[:3, 3] = pos
        if not meshGeoms.has_key(geom):
            meshGeoms[geom] = [mat]
            geom.Set(materials = [ingr.color], inheritMaterial=0)
            #create the mesh
            geom.ob,geom.mesh = bl.createsNmesh(geom.name,geom.getVertices(),None,geom.getFaces(),
				color=[ingr.color],smooth=False,proxyCol=False)	
        else:
            meshGeoms[geom].append(mat)


for geom, mats in meshGeoms.items():
    instancesExtra = []
    for i,mat in enumerate(mats):
        instancesExtra.append(bl.setInstance(geom.name+str(i),geom.ob, mat))
        bl.addObjectToScene(sc,instancesExtra[-1], parent=bg)

# display organelle spheres
for orga in h1.organelles:
    vertsIn = []
    radiiIn = []
    colorsIn =[]
    vertsSurf = []
    radiiSurf = []
    colorsSurf =[]
    for pos, rot, ingr, ptInd in orga.molecules:
        level = ingr.maxLevel
        px = ingr.transformPoints(pos, rot, ingr.positions[level])
        for ii in range(len(ingr.radii[level])):
            if ingr.compNum > 0:
                vertsSurf.append( px[ii] )
                radiiSurf.append( ingr.radii[level][ii]*2. )
                colorsSurf.append( ingr.color)
            else:
                vertsIn.append( px[ii] )
                radiiIn.append( ingr.radii[level][ii]*2. )
                colorsIn.append( ingr.color)

    if len(vertsSurf):
        g = orgaToMasterGeom[orga.number]
        parent = bl.getObject(g.name)
        sphs = bl.instancesSphere('spheres',vertsSurf,radiiSurf,meshsphere,colorsSurf,scn,parent=parent)
        #sph = Spheres('spheres', inheritMaterial=False, centers=vertsSurf,
        #              materials=colorsSurf, radii=radiiSurf, visible=1)
        #vi.AddObject(sph, parent=g)
    if len(vertsIn):
        g = orgaToMasterGeom[-orga.number]
        parent = bl.getObject(g.name)
        sphs = bl.instancesSphere('spheres',vertsIn,radiiIn,meshsphere,colorsIn,scn,parent=parent)
	for sp in sphs:
	    bl.toggleDisplay(sp,display=False)
        #sph = Spheres('spheres', inheritMaterial=False, centers=vertsIn,
        #              materials=colorsIn, radii=radiiIn, visible=0)
        #vi.AddObject(sph, parent=g)


# display organelle meshes
for orga in h1.organelles:
    meshGeomsSurf = {}
    meshGeomsInt = {}
    for pos, rot, ingr, ptInd in orga.molecules:
        if ingr.mesh: # display mesh
            geom = ingr.mesh
            mat = rot.copy()
            mat[:3, 3] = pos

            if ingr.compNum > 0:
                gdict = meshGeomsSurf
            else:
                gdict = meshGeomsInt

            if not gdict.has_key(geom):
                gdict[geom] = [mat]
                geom.Set(materials=[ingr.color], inheritMaterial=0)
                #create the mesh
                geom.ob,geom.mesh = bl.createsNmesh(geom.name,geom.getVertices(),None,geom.getFaces(),
				color=[ingr.color],smooth=False,proxyCol=False)	
            else:
                gdict[geom].append(mat)

    g = orgaToMasterGeom[orga.number]
    bg = bl.getObject(g.name)
    for geom, mats in meshGeomsSurf.items():
        #create the instance according the matrices
        instancesSurf = []
        for i,mat in enumerate(mats):
            instancesSurf.append(bl.setInstance(geom.name+str(i),geom.ob, mat))
	    bl.addObjectToScene(sc,instancesSurf[-1], parent=bg)
        geom.Set(instanceMatrices=mats)
        #vi.AddObject(geom, parent=g)

    g = orgaToMasterGeom[-orga.number]
    bg = bl.getObject(g.name)
    for geom, mats in meshGeomsInt.items():
        #create the instance according the matrices
        instancesInt = []
        for i,mat in enumerate(mats):
            instancesInt.append(bl.setInstance(geom.name+str(i),geom.ob, mat))
	    bl.addObjectToScene(sc,instancesInt[-1], parent=bg)
        #geom.Set(instanceMatrices=mats)
        #vi.AddObject(geom, parent=g)

"""
from DejaVu.colorTool import RGBRamp, Map
verts = []
labels = []
for i, value in enumerate(h1.distToClosestSurf):
    if h1.gridPtId[i]==1:
        verts.append( h1.masterGridPositions[i] )
        labels.append("%.2f"%value)
lab = GlfLabels('distanceLab', vertices=verts, labels=labels, visible=0)
#vi.AddObject(lab)

# display grid points with positive distances left
verts = []
rads = []
for pt in h1.freePointsAfterFill:
    d = h1.distancesAfterFill[pt]
    if d>15.999:
        verts.append(h1.masterGridPositions[pt])
        rads.append(d)

sph1 = Spheres('unusedSph', centers=verts, radii=rads, inheritFrontPolyMode=0,
               frontPolyMode='line', visible=0)
#vi.AddObject(sph1)

pts1 = Points('unusedPts', vertices=verts, inheritPointWidth=0,
              pointWidth=4, inheritMaterial=0, materials=[(0,1,0)], visible=0)
#vi.AddObject(pts1)

if hasattr(h1, 'jitter vectors'):
    from DejaVu.Polylines import Polylines
    verts = []
    for p1, p2 in (h1.jitterVectors):
        verts.append( (p1, p2))

    jv = Polylines('jitter vectors', vertices=verts, visible=1,
                   inheritLineWidth=0, lineWidth=4)
    #vi.AddObject(jv, parent=orgaToMasterGeom[h1])
"""
