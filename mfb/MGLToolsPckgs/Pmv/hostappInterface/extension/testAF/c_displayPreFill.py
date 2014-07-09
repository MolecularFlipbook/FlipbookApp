# create a Viewer
from DejaVu import Viewer
if ViewerType == 'dejavu':
    vi = Viewer()
    from DejaVu.Box import Box
    from DejaVu.Spheres import Spheres
    from DejaVu.Cylinders import Cylinders
    from DejaVu.Geom import Geom
    from DejaVu.IndexedPolygons import IndexedPolygons
    from DejaVu.Points import Points
    from DejaVu.glfLabels import GlfLabels
    from DejaVu.Polylines import Polylines
elif ViewerType == 'c4d':
    import c4d
    #from Pmv.hostappInterface import pdb_c4d
    import Pmv.hostappInterface.cinema4d.helperC4D as pdb_c4d
    vi = pdb_c4d    
    Box = pdb_c4d.box
    Geom = pdb_c4d.newEmpty
    IndexedPolygons = pdb_c4d.polygons
    Points = pdb_c4d.PointCloudObject
    sc=pdb_c4d.getCurrentScene()
    dejavumat = vi.createDejaVuColorMat()
    helper = pdb_c4d
elif ViewerType == 'blender':
    import Blender
    from Pmv.hostappInterface import pdb_blender
    vi = pdb_blender
    Box = pdb_blender.box
    Geom = pdb_blender.newEmpty
    IndexedPolygons = pdb_blender.polygons
    sc=pdb_blender.getCurrentScene()
    Points =None
#display fill box
#fbb = Box('fillpBB',cornerPoints=bb,visible=1) #maybe /10.
#vi.AddObject(fbb)

# create master for cytoplasm compartment
# 

orgaToMasterGeom = {}
g = Geom('cytoplasm', visible=0)
orgaToMasterGeom[0] = g
orgaToMasterGeom[h1] = g
vi.AddObject(g)

# create masters for ingredients
r =  h1.exteriorRecipe
if r :
    for ingr in r.ingredients:
        gi = Geom('%s %s'%(ingr.pdb, ingr.name))
        vi.AddObject(gi, parent=g)
        orgaToMasterGeom[ingr] = gi

# display organelle mesh
for orga in h1.organelles:
    # create master for organelle
    g = Geom('organelle_%d'%orga.number)
    vi.AddObject(g)
    gs = Geom('surface')
    vi.AddObject(gs, parent=g)
    gc = Geom('Matrix')
    vi.AddObject(gc, parent=g)
    orgaToMasterGeom[orga] = g
    orgaToMasterGeom[orga.number] = gs
    orgaToMasterGeom[-orga.number] = gc

    # create masters for ingredients
    r =  orga.surfaceRecipe
    if r :
        for ingr in r.ingredients:
            gi = Geom('%s %s'%(ingr.pdb, ingr.name))
            vi.AddObject(gi, parent=gs)
            orgaToMasterGeom[ingr] = gi
    r =  orga.innerRecipe
    if r :
        for ingr in r.ingredients:
            gi = Geom('%s %s'%(ingr.pdb, ingr.name))
            vi.AddObject(gi, parent=gc)
            orgaToMasterGeom[ingr] = gi

    tet = IndexedPolygons('surfaceMesh', vertices=orga.vertices,
                          faces=orga.faces, normals=orga.vnormals,
                          inheritFrontPolyMode=False,
                          frontPolyMode='line',
                          inheritCulling=0, culling='none',
                          inheritShading=0, shading='flat')
    vi.AddObject(tet, parent=g)
# display histo BB 
hbb = Box('histoVolBB', cornerPoints=h1.boundingBox)
vi.AddObject(hbb)

   
if ViewerType == 'dejavu':
    cp = vi.clipP[0]
    vi.GUI.clipvar[0][0].set(1)
    tet.AddClipPlane( cp, 1, False)
    fpg = Points('notFreePoints')
    vi.AddObject(fpg)
else :
    fpg = Geom('notFreePoints')
    vi.AddObject(fpg)

if ViewerType == 'dejavu':
    vi.Reset_cb()
    vi.Normalize_cb()
    vi.Center_cb()
    cam = vi.currentCamera
    cam.master.master.geometry('%dx%d+%d+%d'%(400,400, 92, 73))
    vi.update()
    cam.fog.Set(enabled=1)
    
    sph = Spheres('debugSph', inheritMaterial=False)
    vi.AddObject(sph)
