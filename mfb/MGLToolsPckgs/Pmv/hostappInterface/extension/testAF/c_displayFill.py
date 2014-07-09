# display organelle surface normals
for orga in h1.organelles:
    if ViewerType == 'dejavu':
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
                   visible=0,parent = orgaToMasterGeom[orga])
        if ViewerType == 'dejavu':
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
               visible=0,parent = orgaToMasterGeom[orga])
    if ViewerType == 'dejavu':
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
               visible=0,parent = orgaToMasterGeom[orga])
    if ViewerType == 'dejavu':
        vi.AddObject(s, parent=orgaToMasterGeom[orga])

        labDistg = GlfLabels('insidePtLab', vertices=verts, labels=labels,
                         visible=0)
        vi.AddObject(labDistg, parent=orgaToMasterGeom[orga])



# display cytoplasm spheres
verts = {}
radii = {}
r =  h1.exteriorRecipe
if r :
    for ingr in r.ingredients:
        verts[ingr] = []
        radii[ingr] = []

for pos, rot, ingr, ptInd in h1.molecules:
    level = ingr.maxLevel
    px = ingr.transformPoints(pos, rot, ingr.positions[level])
    for ii in range(len(ingr.radii[level])):
        verts[ingr].append( px[ii] )
        radii[ingr].append( ingr.radii[level][ii] )

if ViewerType != 'dejavu':
    psph=vi.newEmpty("base_shape")
    vi.AddObject(psph)            
    pesph=vi.newEmpty("base_sphere")
    vi.AddObject(pesph,parent=psph)                    
    bsph=vi.Sphere("sphere")
    vi.AddObject(bsph,parent=pesph)
    becyl=vi.newEmpty("base_cylinder")
    vi.AddObject(becyl,parent=psph)
    bcyl=vi.Cylinder("cylinder",res=4)
    vi.AddObject(bcyl,parent=becyl)                        


#if r :
#    for ingr in r.ingredients:
#        if len(verts[ingr]):
#            if ingr.modelType=='Spheres':
#                if ViewerType == 'dejavu':
#                    sph = Spheres('spheres', inheritMaterial=0,
#                              centers=verts[ingr], materials=[ingr.color],
#                              radii=radii[ingr], visible=1)
#                    vi.AddObject(sph, parent=orgaToMasterGeom[ingr])
#                    #print ingr.name, verts[ingr]                    
#                else :
#                    parent=vi.newEmpty("spheres")
#                    vi.AddObject(parent,parent=orgaToMasterGeom[ingr])                            
#                    sph=vi.instancesSphere("spheres",verts[ingr],radii[ingr],
#                                    pesph,[ingr.color],sc,parent=parent)
#                    #print ingr.name, verts[ingr]
# display cytoplasm meshes
r =  h1.exteriorRecipe
if r :
    meshGeoms = {}
    for pos, rot, ingr, ptInd in h1.molecules:
        if ingr.mesh: # display mesh
            geom = ingr.mesh
            mat = rot.copy()
            mat[:3, 3] = pos
            if not meshGeoms.has_key(geom):
                meshGeoms[geom] = [mat]
                geom.Set(materials=[ingr.color], inheritMaterial=0, visible=0)
                if ViewerType != 'dejavu':
                    polygon = vi.createsNmesh(geom.name,geom.getVertices(),None,geom.getFaces(),material=vi.retrieveColorMat(ingr.color))    
                    vi.AddObject(polygon[0], parent=orgaToMasterGeom[ingr])
                    #vi.toggleDisplay(polygon[0],False)
                    ingr.mesh_3d = polygon[0]
                    geom.mesh_3d = polygon[0]
                    geom.ingr = ingr                                                                        
                    vi.toggleDisplay(polygon[0],False)
                    #ingr.mesh_3d.set_pos(c4d.Vector(1000.,1000.,1000.))
            else:
                meshGeoms[geom].append(mat)
                if ViewerType == 'dejavu': vi.AddObject(geom, parent=orgaToMasterGeom[ingr])
    for geom, mats in meshGeoms.items():
        geom.Set(instanceMatrices=mats, visible=1)        
        if ViewerType != 'dejavu':
            #find the polygon and the ingr?#polygon = ingr.mesh_3d
            polygon = geom.mesh_3d
            parent=vi.newEmpty("Meshs")
            vi.AddObject(parent, parent=orgaToMasterGeom[geom.ingr])
            ipoly = vi.instancePolygon(geom.name,matrices=mats,mesh=polygon,parent = parent)            


# display organelle spheres
for orga in h1.organelles:
    verts = {}
    radii = {}
    rs =  orga.surfaceRecipe
    if rs :
        for ingr in rs.ingredients:
            verts[ingr] = []
            radii[ingr] = []
    ri =  orga.innerRecipe
    if ri:
        for ingr in ri.ingredients:
            verts[ingr] = []
            radii[ingr] = []

    for pos, rot, ingr, ptInd in orga.molecules:
        level = ingr.maxLevel
        px = ingr.transformPoints(pos, rot, ingr.positions[level])
        if ingr.modelType=='Spheres':
            for ii in range(len(ingr.radii[level])):
                verts[ingr].append( px[ii] )
                radii[ingr].append( ingr.radii[level][ii] )
        elif ingr.modelType=='Cylinders':
            px2 = ingr.transformPoints(pos, rot, ingr.positions2[level])
            for ii in range(len(ingr.radii[level])):
                verts[ingr].append( px[ii] )
                verts[ingr].append( px2[ii] )
                radii[ingr].append( ingr.radii[level][ii] )
                radii[ingr].append( ingr.radii[level][ii] )

    if rs :
        for ingr in rs.ingredients:
            if len(verts[ingr]):
                if ingr.modelType=='Spheres':
                    if ViewerType == 'dejavu':
                        sph = Spheres('spheres', inheritMaterial=False,
                                  centers=verts[ingr], radii=radii[ingr], 
                                  materials=[ingr.color], visible=0)
                        vi.AddObject(sph, parent=orgaToMasterGeom[ingr])
#                    else:
#                        parent=vi.newEmpty("spheres")
#                        vi.AddObject(parent,parent=orgaToMasterGeom[ingr])
#                        sph=vi.instancesSphere("spheres",verts[ingr],radii[ingr],pesph,[ingr.color,],sc,parent=parent)
                elif ingr.modelType=='Cylinders':
                    v = numpy.array(verts[ingr])
                    f = numpy.arange(len(v))
                    f.shape=(-1,2)
                    if ViewerType == 'dejavu':                
                        cyl = Cylinders('Cylinders', inheritMaterial=0,
                                        vertices=v, faces=f, materials=[ingr.color],
                                        radii=radii[ingr], visible=1,
                                        inheritCulling=0, culling='None',
                                        inheritFrontPolyMode=0, frontPolyMode='line')
                        vi.AddObject(cyl, parent=orgaToMasterGeom[ingr])
                    else :
                        parent=vi.newEmpty("Cylinders")
                        vi.AddObject(parent,parent=orgaToMasterGeom[ingr])                    
                        cyl=vi.instancesCylinder("Cylinders",verts[ingr],f,radii[ingr],
                                    becyl,[ingr.color],sc,parent=parent)

    if ri:
        for ingr in ri.ingredients:
            if len(verts[ingr]):
                if ingr.modelType=='Spheres':
                    if ViewerType == 'dejavu':                
                        sph = Spheres('spheres', inheritMaterial=False,
                                  centers=verts[ingr], radii=radii[ingr], 
                                  materials=[ingr.color], visible=0)
                        vi.AddObject(sph, parent=orgaToMasterGeom[ingr])
#                    elif ViewerType == 'c4d':
#                        parent=vi.newEmpty("spheres")
#                        vi.AddObject(parent,parent=orgaToMasterGeom[ingr])
#                        sph=vi.instancesSphere("spheres",verts[ingr],radii[ingr],
#                                    pesph,[ingr.color],sc,parent=parent)                        
                elif ingr.modelType=='Cylinders':
                    v = numpy.array(verts[ingr])
                    f = numpy.arange(len(v))
                    f.shape=(-1,2)
                    if ViewerType == 'dejavu':                    
                        cyl = Cylinders('Cylinders', inheritMaterial=0,
                                    vertices=v, faces=f, materials=[ingr.color],
                                    radii=radii[ingr], visible=1,
                                    inheritCulling=0, culling='None',
                                    inheritFrontPolyMode=0, frontPolyMode='line')
                        vi.AddObject(cyl, parent=orgaToMasterGeom[ingr])
                    elif ViewerType == 'c4d':
                        parent=vi.newEmpty("Cylinders")
                        vi.AddObject(parent,parent=orgaToMasterGeom[ingr])
                        cyl=vi.instancesCylinder("Cylinders",verts[ingr],f,radii[ingr],
                                    becyl,[ingr.color],sc,parent=parent)

# display organelle meshes
for orga in h1.organelles:
    matrices = {}
    rs =  orga.surfaceRecipe
    if rs :
        for ingr in rs.ingredients:
            if ingr.mesh: # display mesh
                matrices[ingr] = []
                ingr.mesh.Set(materials=[ingr.color], inheritMaterial=0)
                if ViewerType != 'dejavu':
                    geom = ingr.mesh                 
                    #g=vi.newEmpty(geom.name)
                    #vi.AddObject(g, parent=orgaToMasterGeom[ingr])
                    #print len(geom.getVertices()),geom.name
                    #create the polygon                    
                    polygon = vi.createsNmesh(geom.name,geom.getVertices(),None,geom.getFaces(),material=vi.retrieveColorMat(ingr.color))    
                    vi.AddObject(polygon[0], parent=orgaToMasterGeom[ingr])
                    vi.toggleDisplay(polygon[0],False)
                    ingr.mesh_3d = polygon[0]                                
                    ingr.mesh_3d.set_pos(c4d.Vector(1000.,1000.,1000.))
    ri =  orga.innerRecipe
    if ri :
        for ingr in ri.ingredients:
            if ingr.mesh: # display mesh
                matrices[ingr] = []
                ingr.mesh.Set(materials=[ingr.color], inheritMaterial=0)
                if ViewerType != 'dejavu':
                    geom = ingr.mesh                 
                    #g=vi.newEmpty(geom.name)
                    #vi.AddObject(g, parent=orgaToMasterGeom[ingr])
                    #print len(geom.getVertices()),geom.name
                    #create the polygon                    
                    polygon = vi.createsNmesh("Mesh_"+geom.name,geom.getVertices(),None,geom.getFaces(),material=vi.retrieveColorMat(ingr.color))    
                    vi.AddObject(polygon[0], parent=orgaToMasterGeom[ingr])
                    #vi.toggleDisplay(polygon[0],False)                    
                    ingr.mesh_3d = polygon[0]
                    ingr.mesh_3d.set_pos(c4d.Vector(1000.,1000.,1000.))
    for pos, rot, ingr, ptInd in orga.molecules:
        if ingr.mesh: # display mesh
            geom = ingr.mesh
            #print ingr,ingr.mesh.name
            #print pos                          
            mat = rot.copy()
            mat[:3, 3] = pos
            matrices[ingr].append(mat)
            if ViewerType == 'dejavu': 
                vi.AddObject(geom, parent=orgaToMasterGeom[ingr])
            else :
                if not hasattr(ingr,'mesh_3d') :
                    polygon = vi.createsNmesh(geom.name,geom.getVertices(),None,geom.getFaces(),material=vi.retrieveColorMat(ingr.color))    
                    vi.AddObject(polygon[0], parent=orgaToMasterGeom[ingr])
                    #vi.toggleDisplay(polygon[0],False)
                    ingr.mesh_3d = polygon[0]
                    ingr.mesh_3d.set_pos(c4d.Vector(1000.,1000.,1000.))                                                    
                #print "c4d",ingr.mesh_3d.get_name()

    for ingr, mats in matrices.items():
        geom = ingr.mesh
        geom.Set(instanceMatrices=mats, visible=1)
        #print ingr,ingr.mesh.name,orgaToMasterGeom[ingr]    
        if ViewerType == 'dejavu': 
            vi.AddObject(geom, parent=orgaToMasterGeom[ingr])
        else :
            #the mesh polygon
            polygon = ingr.mesh_3d
            parent=vi.newEmpty("Meshs")
            vi.AddObject(parent, parent=orgaToMasterGeom[ingr])
            ipoly = vi.instancePolygon(geom.name,matrices=mats,mesh=polygon,parent = parent)            
            #print "c4d",ingr.mesh_3d.get_name(),
            #vi.instancePolygon(name, matrices, mesh)    

if ViewerType == 'dejavu':
    from DejaVu.colorTool import RGBRamp, Map
    verts = []
    labels = []
    for i, value in enumerate(h1.distToClosestSurf):
        if h1.gridPtId[i]==1:
            verts.append( h1.masterGridPositions[i] )
            labels.append("%.2f"%value)
    lab = GlfLabels('distanceLab', vertices=verts, labels=labels, visible=0)
    vi.AddObject(lab)



# display grid points with positive distances left
verts = []
rads = []
for pt in h1.freePointsAfterFill[:h1.nbFreePointsAfterFill]:
    d = h1.distancesAfterFill[pt]
    if d>h1.smallestProteinSize-0.001:
        verts.append(h1.masterGridPositions[pt])
        rads.append(d)
if ViewerType == 'dejavu':
    if len(verts):
        sph1 = Spheres('unusedSph', centers=verts, radii=rads, inheritFrontPolyMode=0,
                       frontPolyMode='line', visible=0)
        vi.AddObject(sph1)

if len(verts):
    pts1 = Points('zeroPts', vertices=verts, inheritPointWidth=0,
                  pointWidth=4, inheritMaterial=0, materials=[(0,1,0)], visible=0,
                  parent=None)
    if ViewerType == 'dejavu':vi.AddObject(pts1)

    verts = []
    for pt in h1.freePointsAfterFill[:h1.nbFreePointsAfterFill]:
        verts.append(h1.masterGridPositions[pt])

    unpts = Points('unusedGridPoints', vertices=verts, inheritMaterial=0,
                  materials=[green], visible=0,parent=None)
    if ViewerType == 'dejavu' : vi.AddObject(unpts)

    verts = []
    for pt in h1.freePointsAfterFill[h1.nbFreePointsAfterFill:]:
        verts.append(h1.masterGridPositions[pt])

    uspts = Points('usedGridPoints', vertices=verts, inheritMaterial=0,
                  materials=[red], visible=0,parent=None)
    if ViewerType == 'dejavu':vi.AddObject(uspts)
    
if ViewerType == 'dejavu':
    if hasattr(h1, 'jitter vectors'):
        from DejaVu.Polylines import Polylines
        verts = []
        for p1, p2 in (h1.jitterVectors):
            verts.append( (p1, p2))

        jv = Polylines('jitter vectors', vertices=verts, visible=1,
                       inheritLineWidth=0, lineWidth=4)
        vi.AddObject(jv, parent=orgaToMasterGeom[h1])


def dspMesh(geom):
    if ViewerType != 'dejavu':
        for c in geom.get_childs():
            if c.get_name() == "Meshs":
                vi.toggleDisplay(c,True)                        
    else :
        for c in geom.children:
            if c.name=='mesh':
                c.Set(visible=1)
                
def undspMesh(geom):
    if ViewerType != 'dejavu':
        for c in geom.get_childs():
            if c.get_name() == "Meshs":
                vi.toggleDisplay(c,False)                        
    else :
        for c in geom.children:
            if c.name=='mesh':
                c.Set(visible=0)

def dspSph(geom):
    if ViewerType != 'dejavu':
        for c in geom.get_childs():
            if c.get_name() == "spheres":
                vi.toggleDisplay(c,True)                        
    else :
        for c in geom.children:
            if c.name=='spheres':
                c.Set(visible=1)

def undspSph(geom):
    if ViewerType!= 'dejavu':
        for c in geom.get_childs():
            if c.get_name() == "spheres":
                vi.toggleDisplay(c,False)                        
    else :
        for c in geom.children:
            if c.name=='spheres':
                c.Set(visible=0)

def showHide(func):
    r =  h1.exteriorRecipe
    if r :
        for ingr in r.ingredients:
            master = orgaToMasterGeom[ingr]
            func(master)
    for orga in h1.organelles:
        rs =  orga.surfaceRecipe
        if rs :
            for ingr in rs.ingredients:
                master = orgaToMasterGeom[ingr]
                func(master)
        ri =  orga.innerRecipe
        if ri:
            for ingr in ri.ingredients:
                master = orgaToMasterGeom[ingr]
                func(master)

#showHide(dspMesh)
#showHide(undspSph)
