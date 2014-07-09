## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

from geomutils.surface import findComponents, meshVolume, triangleArea
try:
    from UTpackages.UTisocontour import isocontour
except:
    pass
try:
    from UTpackages.UTblur import blur
except:
    pass

try:
    from mslib import MSMS
except:
    pass

try:
   from QSlimLib import qslimlib
except:
   pass

from math import fabs
from MolKit.molecule import Atom

import numpy.oldnumeric as Numeric
from math import sqrt

def computeIsovalue(nodes, blobbyness, densityList=3.0, gridResolution=0.5, criteria="Volume", radiiSet="united", msmsProbeRadius=1.4, computeWeightOption=0, resolutionLevel=None, gridDims=None, padding=0.0):
    	"""This function is based on shapefit/surfdock.py blurSurface() by Qing Zhang.

INPUT:
	nodes 		
	blobbyness: 		blobbyness
	densityList:		A list of vertex densities (or just a single density value) for blur surfaces
			   		e.g. [1.0, 2.0, 3.0] or 1.0 or [1.0]
	gridResolution:		Resolution of grid used for blurring
			    		0.5  gives surface vertex density >  5 dots/Angstrom^2
			    		0.25 gives surface vertex density > 20 dots/Angstrom^2
			    		0.2  gives surface vertex density > 40 dots/Angstrom^2
	radiiSet: 		Radii set for computing both MSMS and blur surfaces
	msmsProbeRadius:	Probe radius for computing MSMS
	resolutionLevel:	Level of surface resolution
		= None:			using the given blobbyness value
		= 1 or 'very low'       blobbyness = -0.1
		= 2 or 'low'		blobbyness = -0.3
		= 3 or 'medium'		blobbyness = -0.5
		= 4 or 'high'		blobbyness = -0.9
		= 5 or 'very high'	blobbyness = -3.0

        padding : size of the padding around the molecule

                
"""
	# 0. Initialization

	blurSurfList = []

    	isoGridResolution = 0.5   	# grid resolution for finding isovalue
    	isoDensity = 5.0		# density of blur surface vertices for finding isovalue
    	msmsDensity = 20.0		# density of MSMS surface vertices for compute MSMS volume
        #msmsFilePrefix=molName		# prefix of MSMS surface filenames


        # ... 1.1. Blur
        print "... 1.1. Blur ......"
        
        atoms = nodes.findType(Atom)
        coords = atoms.coords
        radii = atoms.radius
        arrayf, origin, stepsize = blurCoordsRadii(coords, radii, blobbyness,
						   isoGridResolution, gridDims, padding)
        data = isocontour.newDatasetRegFloat3D(arrayf, origin, stepsize)
        print "##### data : ", type(data),  "#######"
        # ... 1.2. Compute area and volume of MSMS surface at msmsDensity
        print "... 1.2. Compute MSMS volume ......"
        msmsVolume = computeMSMSvolume(coords, radii, msmsProbeRadius, msmsDensity)
        #msmsArea, msmsVolume = computeMSMSAreaVolumeViaCommand(molFile, radiiSet, msmsProbeRadius, dens=msmsDensity, outFilePrefix=msmsFilePrefix)
        #os.system( "rm -rf %s.vert %s.face %s.xyzr" % ( msmsFilePrefix, msmsFilePrefix, msmsFilePrefix ) ) # remove MSMS surface files
        # ... 1.3. Find isovalue based on either MSMS area or volume at blur isoDensity
        print "... 1.3. Find isovalue ......"
        res = findIsoValueMol(radii, coords, blobbyness, data, isoDensity, msmsVolume, "Volume")
        
	target, targetValue, value, isovalue, v1, t1, n1 = res    
        #isocontour.clearDataset(data)	# free memory of data
        isocontour.delDatasetReg(data)
        if isovalue == 0.0:		# isovalue can not be found
            print "blurSurface(): isovalue can not be found"
            return None
        return isovalue

def blurCoordsRadii(coords, radii, blobbyness=-0.1, res=0.5,
                    weights=None, dims=None, padding = 0.0):
    """blur a set of coordinates with radii
"""
    # Setup grid
    resX = resY = resZ = res
    if not dims:
        minb, maxb = blur.getBoundingBox(coords, radii, blobbyness, padding)
        Xdim = int(round( (maxb[0] - minb[0])/resX + 1))
        Ydim = int(round( (maxb[1] - minb[1])/resY + 1))
        Zdim = int(round( (maxb[2] - minb[2])/resZ + 1))
    else:
        Xdim, Ydim, Zdim = dims
    print "Xdim = %d, Ydim =%d, Zdim = %d"%(Xdim, Ydim, Zdim)
    # Generate blur map
    volarr, origin, span = blur.generateBlurmap(
        coords, radii, [Xdim, Ydim, Zdim], blobbyness, weights=weights, padding=padding)
    # Take data from blur map 
    volarr.shape = [Zdim, Ydim, Xdim]
    volarr = Numeric.transpose(volarr).astype('f')
    origin = Numeric.array(origin).astype('f')
    stepsize = Numeric.array(span).astype('f')
    arrayf = Numeric.reshape( Numeric.transpose(volarr),
                              (1, 1)+tuple(volarr.shape) )
    # Return data
    return arrayf, origin, stepsize

def computeMSMSvolume(atmCoords, atmRadii, pRadius, dens ):
    srf = MSMS(coords=atmCoords, radii=atmRadii)
    srf.compute(probe_radius=pRadius, density=dens)
    vf, vi, f = srf.getTriangles()
    
    vertices=vf[:,:3]
    normals=vf[:,3:6]
    triangles=f[:,:3]
    return meshVolume(vertices, normals, triangles)



def meshArea(verts, tri):
    """Compute the surface area of a surface as the sum of the area of its
triangles.  The surface is specified by vertices, indices of triangular faces
"""
    areaSum = 0.0
    for t in tri:
        s1 = verts[t[0]]
        s2 = verts[t[1]]
        s3 = verts[t[2]]
        area = triangleArea(s1,s2,s3)
        areaSum += area

    return areaSum

def normalCorrection(norms, faces):
    """Replace any normal, which is equal to zero, with the average
of its triangle neighbors' non-zero normals (triangle neighbors, as
the edge partners, can be derived from the faces)
"""
    # Convert one-based faces temporarily to zero-based
    newFaces = []
    if faces[0][0] == 1:
        for v1, v2, v3 in faces:   # vertex indices v1, v2, v3
	    newFaces.append( ( v1-1, v2-1, v3-1 ) )
    else:
        newFaces = faces
    
    # Build a neighborhood dictionary for easy neighbor search
    neighborDict = {}
    for v1, v2, v3 in newFaces:   # vertex indices v1, v2, v3
        # v1
	if v1 not in neighborDict:
	    neighborDict[v1] = []
	if v2 not in neighborDict[v1]:
	    neighborDict[v1].append(v2)
	if v3 not in neighborDict[v1]:
	    neighborDict[v1].append(v3)
	# v2
	if v2 not in neighborDict:
	    neighborDict[v2] = []
	if v3 not in neighborDict[v2]:
	    neighborDict[v2].append(v3)
	if v1 not in neighborDict[v2]:
	    neighborDict[v2].append(v1)
	# v3
	if v3 not in neighborDict:
	    neighborDict[v3] = []
	if v1 not in neighborDict[v3]:
	    neighborDict[v3].append(v1)
	if v2 not in neighborDict[v3]:
	    neighborDict[v3].append(v2)

    # Find any zero-value normal and replace it
    newNorms = []
    for i, eachnorm in enumerate(norms):
        # non-zero normal
        if not ( eachnorm[0]==0.0 and eachnorm[1]==0.0 and eachnorm[2]==0.0 ):
	    newNorms.append( [ eachnorm[0], eachnorm[1], eachnorm[2] ] )
	    continue
	# zero normal
	print "normalCorrection(): zero normal at vertex %d", i
	neighbors = neighborDict[i]
	neighborNorms = [0.0, 0.0, 0.0]
	Nneighbors = 0
	for eachneighbor in neighbors:			# sum up non-zero neighbors
	    eachneighborNorm = norms[eachneighbor]
	    if eachneighborNorm[0]==0.0 and eachneighborNorm[1]==0.0 and eachneighborNorm[2]==0.0:
	        continue   				# skip zero-normal neighbor
	    Nneighbors += 1
	    neighborNorms[0] += eachneighborNorm[0]
	    neighborNorms[1] += eachneighborNorm[1]
	    neighborNorms[2] += eachneighborNorm[2]
	if Nneighbors == 0:				# non-zero neighbors can not be found
	    print "Can not find non-zero neighbor normals for normal %d " % i
	    newNorms.append(neighborNorms)
	    continue
        neighborNorms[0] /= Nneighbors 			# average
        neighborNorms[1] /= Nneighbors
        neighborNorms[2] /= Nneighbors
	newNorms.append(neighborNorms)    
	
    # Return
    return newNorms

def findIsoValueMol(radii, coords, blobbyness, data, isoDensity, targetValue, target):
    """Find the best isocontour value (isovalue) for a molecule
at one specific blobbyness by reproducing the targetValue
for a target (area or volume)
INPUT:
	mol:		molecule recognizable by MolKit
	blobbyness:	blobbyness
	data: 		blurred data
	isoDensity: 	density of surface vertices for finding isovalue only
	targetValue: 	value of the target, to be reproduced
	target: 	Area or Volume
OUTPUT:
	target:		(as input)
	targetValue:	(as input)
	value:		reproduced value of target
	isovalue:	the best isocontour value
	v1d:		vertices of generated blur surface
	t1d:		faces of generated blur surface
	n1d:		normals of the vertices
"""
    

    # Initialization
    isovalue = 1.0  		# guess starting value
    mini = 0.
    maxi = 99.
    cutoff = targetValue*0.01	# 99% reproduction of targetValue
    accuracy = 0.0001		# accuracy of isovalue
    stepsize = 0.5		# step size of increase/decrease of isovalue
    value_adjust = 1.0		# adjustment of value
    value = 0.0
    
    # Optimize isovalue
    while True:
        print "------- isovalue = %f -------" % isovalue

        # 1. Isocontour
	print "... ... 1. Isocontour ......"
        v1, t1, n1 = computeIsocontour(isovalue, data)
        if len(v1)==0 or len(t1)==0:
            value    = 0.0
            maxi     = isovalue
            isovalue = maxi - (maxi-mini)*stepsize
	    print "***** isocontoured surface has no vertices *****", len(v1), ", ", len(t1)
            continue
	
	# 2. Remove small components (before decimate)
	print "... ... 2. Remove small components ......"
        v1, t1, n1 = findComponents(v1, t1, n1, 1)
	
	# 3. Decimate
	print "... ... 3. Decimate ......"
        v1d, t1d, n1d = decimate(v1, t1, n1, isoDensity)
        if len(v1d)==0 or len(t1d)==0:
            value    = 0.0
            maxi     = isovalue
            isovalue = maxi - (maxi-mini)*stepsize
            continue
	#################### Analytical normals for decimated vertices #####################
        normals = computeBlurCurvature(radii, coords, blobbyness, v1d)   # Analytical Blur curvatures
	n1d = normals.tolist()
	####################################################################################
	
        # 4. Compute value
	print "... ... 4. Compute value ......"
	if target == "Area":
	    value = meshArea(v1d, t1d)
	else:
            n1d = normalCorrection(n1d, t1d) 	# replace zero normals
	    print "calling meshVolume after normalCorrection"
	    value  = meshVolume(v1d, n1d, t1d)

	# 5. Adjust value
	print "... ... 5. Adjust value ......"
	value *= value_adjust
	
	# TEST
        print "target=%6s, targetValue=%10.3f, value=%10.3f, isovalue=%7.3f, maxi=%7.3f, mini=%7.3f"%(
            	target, targetValue, value, isovalue, maxi, mini)
		
	# 6. Evaluate isocontour value
	print "... ... 6. Evaluate isovalue ......"
        if fabs(value - targetValue) < cutoff:	# Satisfy condition!
            print "Found: target=%6s, targetValue=%10.3f, value=%10.3f, isovalue=%7.3f, maxi=%7.3f, mini=%7.3f"%(
           	   target, targetValue, value, isovalue, maxi, mini)
            break

        if maxi-mini < accuracy:		# can not find good isovalue
            print "Not found: target=%6s, targetValue=%10.3f, value=%10.3f, isovalue=%7.3f, maxi=%7.3f, mini=%7.3f"%(
            	   target, targetValue, value, isovalue, maxi, mini)
            return target, targetValue, value, 0.0, v1, t1, n1

        if value > targetValue: 		# value too big, increase isovalue
            mini = isovalue
            isovalue = mini + (maxi-mini)*stepsize
        else: 					# value too small, decrease isovalue
            maxi = isovalue
            isovalue = maxi - (maxi-mini)*stepsize

    # Return
    return target, targetValue, value, isovalue, v1, t1, n1

def computeIsocontour(isovalue, data):
    isoc = isocontour.getContour3d(data, 0, 0, isovalue,
                                   isocontour.NO_COLOR_VARIABLE)

    if isoc.nvert==0 or isoc.ntri==0:
        return [], [], []
    vert = Numeric.zeros((isoc.nvert,3)).astype('f')
    norm = Numeric.zeros((isoc.nvert,3)).astype('f')
    col = Numeric.zeros((isoc.nvert)).astype('f')
    tri = Numeric.zeros((isoc.ntri,3)).astype('i')
    isocontour.getContour3dData(isoc, vert, norm, col, tri, 0)
    if len(vert) == 0 or len(tri) == 0:
         return [], [], []
    return vert, tri, norm

def decimate(vert, tri, normals, density=1.0):
    # decimate a mesh to vertex density close to 1.0
    if len(vert)==0 or len(tri)==0:
        return [], [], []

    #print "before decimate: ", len(vert), " vertices, ", len(tri), " faces"
    model = qslimlib.QSlimModel(vert, tri, bindtoface=False,
                                colors=None, norms=normals)
    nverts = model.get_vert_count()
    nfaces = model.get_face_count()
    # allocate array to read decimated surface back

    newverts = Numeric.zeros((nverts, 3)).astype('f')
    newfaces = Numeric.zeros((nfaces, 3)).astype('i')
    newnorms = Numeric.zeros((nverts, 3)).astype('f')

    # print len(vert), area, len(tri), int(len(tri)*len(vert)/area)
    area = meshArea(vert, tri)
    tface = int(min(len(tri), int(len(tri)*area/len(vert)))*density)

    model.slim_to_target(tface)
    numFaces = model.num_valid_faces()

    # print 'decimated to %d triangles from (%d)'%(numFaces, len(tri))
    model.outmodel(newverts, newfaces, outnorms=newnorms)

    numVertices = max(newfaces.ravel())+1
    # build lookup table of vertices used in faces
    d = {}
    for t in newfaces[:numFaces]:
        d[t[0]] = 1
        d[t[1]] = 1
        d[t[2]] = 1
    vl = {}
    decimVerts = Numeric.zeros((numVertices, 3)).astype('f')
    decimFaces = Numeric.zeros((numFaces, 3)).astype('i')
    decimNormals = Numeric.zeros((numVertices, 3)).astype('f')

    nvert = 0
    nvert = 0
    for j, t in enumerate(newfaces[:numFaces]):
        for i in (0,1,2):
            n = t[i]
            if not vl.has_key(n):
                vl[n] = nvert
                decimVerts[nvert] = newverts[n,:]
                decimNormals[nvert] = newnorms[n,:] 
                nvert += 1
        decimFaces[j] = (vl[t[0]], vl[t[1]], vl[t[2]]) 
##     vertices=newverts[:numVertices]
##     for t in newfaces[:numFaces]:
##         for i in (0,1,2):
##                 if not vl.has_key(t[i]):
##                     vl[t[i]] = nvert
##                     decimVerts.append(vertices[t[i]])
##                     nvert += 1
##         decimFaces.append( (vl[t[0]], vl[t[1]], vl[t[2]] ) ) 

    #print 'density after decimation', len(decimVerts)/meshArea(decimVerts, decimFaces)
##     norms1 = glTriangleNormals( decimVerts, decimFaces, 'PER_VERTEX')
    #print "after decimate: ", nvert, " vertices, ", numFaces, " faces"
    return decimVerts[:nvert], decimFaces, decimNormals[:nvert]

def computeBlurCurvature(radii, coords, blobbiness, points):
# Compute Blur curvatures analytically by UTmolderivatives (since Novemeber 2005)
    from UTpackages.UTmolderivatives import molderivatives
    import numpy.oldnumeric as Numeric
    # Read input
    npoints  = len(points)
    numberOfGaussians = len(coords)
    gaussianCenters = Numeric.zeros((numberOfGaussians,4)).astype('d')
    for i in range(numberOfGaussians):
        gaussianCenters[i,0:3] = coords[i]
	gaussianCenters[i,3]   = radii[i]
    numberOfGridDivisions = 10	# as in Readme.htm of UTmolderivatives
    maxFunctionError = 0.001	# as in Readme.htm of UTmolderivatives
    
    # Compute HandK, normals, k1Vector, k2Vector
    HandK, normals, k1Vector, k2Vector = molderivatives.getGaussianCurvature(gaussianCenters,
                               numberOfGridDivisions, maxFunctionError,
                               blobbiness, points)
    
    k1Vector = Numeric.reshape(k1Vector, (npoints, 3))
    k2Vector = Numeric.reshape(k2Vector, (npoints, 3))
    HandK    = Numeric.reshape(HandK, (npoints, 2))
    normals  = Numeric.reshape(normals, (npoints, 3)) * (-1)	# change normal directions to outwards
    return normals
