# create a Viewer
from DejaVu import Viewer

from DejaVu.Geom import Geom
from DejaVu.Spheres import Spheres
from DejaVu.Box import Box
from DejaVu.Points import Points
from DejaVu.glfLabels import GlfLabels
from DejaVu.IndexedPolygons import IndexedPolygons
from DejaVu.Polylines import Polylines

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

bb=[[0, -400.0, -400.0], [400.0, 400.0, 400.0]]

sc = bl.getCurrentScene()
#display fill box
fbb = bl.box('fillpBB',cornerPoints=bb) #maybe /10.
bl.addObjectToScene(sc,fbb)
#fbb = Box('fillpBB', cornerPoints=bb, visible=1)
#vi.AddObject(fbb)

# create master for extra cellular compartment
# 
bg = bl.newEmpty('extra cellular')
orgaToMasterGeom = {}
g = Geom('extra cellular', visible=0)
orgaToMasterGeom[0] = g
orgaToMasterGeom[h1] = g
bl.addObjectToScene(sc,bg)

# display organelle mesh
for orga in h1.organelles:
    # create master for organelle
    bg = bl.newEmpty('organelle_%d'%orga.number)
    g = Geom('organelle_%d'%orga.number)
    bl.addObjectToScene(sc,bg)
    gs = Geom('surface')
    bgs = bl.newEmpty('surface')
    bl.addObjectToScene(sc,bgs, parent=bg)
    gc = Geom('cytoplasm')
    bgc = bl.newEmpty('cytoplasm')
    bl.addObjectToScene(sc,bgc, parent=bg)
    orgaToMasterGeom[orga] = g
    orgaToMasterGeom[orga.number] = gs
    orgaToMasterGeom[-orga.number] = gc
    
    tetobj,tetmesh = bl.createsNmesh('surfaceMesh',orga.vertices,orga.vnormals,orga.faces)
    tetobj.setMaterials([Material.Get("wire")])
    tetobj.colbits = 1<<0 #objMAt
    tetobj.setDrawMode(32)#drawwire
    tetobj.setDrawType(2)#wire
    #tet = IndexedPolygons('surfaceMesh', vertices=orga.vertices,
    #                      faces=orga.faces, normals=orga.vnormals,
    #                      inheritFrontPolyMode=False,
    #                      frontPolyMode='line',
    #                      inheritCulling=0, culling='none',
    #                      inheritShading=0, shading='flat')
    #vi.AddObject(tet, parent=g)
    bl.addObjectToScene(sc,tetobj, parent=bg)

#cp = vi.clipP[0]
#vi.GUI.clipvar[0][0].set(1)
#tet.AddClipPlane( cp, 1, False)

# display histo BB 
#hbb = Box('histoVolBB', cornerPoints=h1.boundingBox)
#vi.AddObject(hbb)
hbb = bl.box('histoVolBB',cornerPoints=h1.boundingBox) #maybe /10.
bl.addObjectToScene(sc,hbb)

"""
# display organelle surface normals
for orga in h1.organelles:
    verts = []
    for i, p in enumerate(o1.surfacePoints):
        pt = h1.masterGridPositions[p]
        norm = o1.surfacePointsNormals[p]
        verts.append( (pt, (pt[0]+norm[0]*10, pt[1]+norm[1]*10, pt[2]+norm[2]*10) ) )

    n = Polylines('normals', vertices=verts, visible=0)
    vi.AddObject(n, parent=orgaToMasterGeom[orga])

    if hasattr(o1, 'ogsurfacePoints'):
        # display off grid surface grid points
        verts = []
        labels = []
        for i,pt in enumerate(orga.ogsurfacePoints):
            verts.append( pt )
            labels.append("%d"%i)

        s = Points('OGsurfacePts', vertices=verts, materials=[[1,1,0]],
                   inheritMaterial=0, pointWidth=3, inheritPointWidth=0,
                   visible=0)
        vi.AddObject(s, parent=orgaToMasterGeom[orga])
        labDistg = GlfLabels('OGsurfacePtLab', vertices=verts, labels=labels,
                             visible=0)
        vi.AddObject(labDistg, parent=orgaToMasterGeom[orga])


    # display surface grid points
    verts = []
    colors = [(1,0,0)]
    labels = []
    for ptInd in orga.surfacePoints:
        verts.append( h1.masterGridPositions[ptInd])
        labels.append("%d"%ptInd)
    s = Points('surfacePts', vertices=verts, materials=colors,
               inheritMaterial=0, pointWidth=4, inheritPointWidth=0,
               visible=0)
    vi.AddObject(s, parent=orgaToMasterGeom[orga])
    labDistg = GlfLabels('surfacePtLab', vertices=verts, labels=labels,
                         visible=0)
    vi.AddObject(labDistg, parent=orgaToMasterGeom[orga])

    # display interior grid points
    verts = []
    labels = []
    for ptInd in orga.insidePoints:
        verts.append( h1.masterGridPositions[ptInd])
        labels.append("%d"%ptInd)

    s = Points('insidePts', vertices=verts, materials=[[0,1,0]],
               inheritMaterial=0, pointWidth=4, inheritPointWidth=0,
               visible=0)
    vi.AddObject(s, parent=orgaToMasterGeom[orga])

    labDistg = GlfLabels('insidePtLab', vertices=verts, labels=labels,
                         visible=0)
    vi.AddObject(labDistg, parent=orgaToMasterGeom[orga])


vi.Reset_cb()
vi.Normalize_cb()
vi.Center_cb()
cam = vi.currentCamera
cam.master.master.geometry('%dx%d+%d+%d'%(400,400, 92, 73))
vi.update()
cam.fog.Set(enabled=1)

sph = Spheres('debugSph', inheritMaterial=False)
vi.AddObject(sph)
"""
center = hbb.getLocation()
cam = Blender.Camera.New('persp','AFcam')
#cam.setScale(focal*2.)
cam.clipEnd=4000.	
obc = sc.objects.new(cam) # make a new object in this scene using the camera data\n'
obc.setLocation (center[0],center[1],1600)
#obc.RotZ=2*math.pi
#obc.restrictSelect=True
sc.objects.camera = obc
#Window.CameraView()

bl.addLampToScene('AFsun','Sun',(1.,1.,1.),15.,0.8,1.5,False,center,sc)
