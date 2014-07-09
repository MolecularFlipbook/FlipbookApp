def coarseMolSurface(molFrag,XYZd,isovalue=5.0,resolution=-0.4,padding=0.0, name='CoarseMolSurface',geom=None):
	"""
	Function adapted from the Vision network which compute a coarse molecular
	surface in PMV

	@type  molFrag: MolKit.AtomSet
	@param molFrag: the atoms selection
	@type  XYZd: array
	@param XYZd: shape of the volume
	@type  isovalue: float
	@param isovalue: isovalue for the isosurface computation
	@type  resolution: float
	@param resolution: resolution of the final mesh
	@type  padding: float
	@param padding: the padding
	@type  name: string
	@param name: the name of the resultante geometry
	@type  geom: DejaVu.Geom
	@param geom: update geom instead of creating a new one

	@rtype:   DejaVu.Geom
	@return:  the created or updated DejaVu.Geom
	"""
	import pdb
	from MolKit.molecule import Atom
	atoms = molFrag.findType(Atom)
	coords = atoms.coords
	radii = atoms.vdwRadius
	from UTpackages.UTblur import blur
	import numpy.core as Numeric

	volarr, origin, span = blur.generateBlurmap(coords, radii, XYZd,resolution, padding = 0.0)
	volarr.shape = (XYZd[0],XYZd[1],XYZd[2])
	volarr = Numeric.ascontiguousarray(Numeric.transpose(volarr), 'f')

	weights =  Numeric.ones(len(radii), 'f')
	h = {}
	from Volume.Grid3D import Grid3DF
	maskGrid = Grid3DF( volarr, origin, span , h)
	h['amin'], h['amax'],h['amean'],h['arms']= maskGrid.stats()

	from UTpackages.UTisocontour import isocontour
	isocontour.setVerboseLevel(0)

	data = maskGrid.data

	origin = Numeric.array(maskGrid.origin).astype('f')
	stepsize = Numeric.array(maskGrid.stepSize).astype('f')

	if data.dtype.char!=Numeric.float32:
		data = data.astype('f')#Numeric.Float32)

	newgrid3D = Numeric.ascontiguousarray(Numeric.reshape( Numeric.transpose(data),
										  (1, 1)+tuple(data.shape) ), data.dtype.char)

	ndata = isocontour.newDatasetRegFloat3D(newgrid3D, origin, stepsize)

	isoc = isocontour.getContour3d(ndata, 0, 0, isovalue,
									   isocontour.NO_COLOR_VARIABLE)
	vert = Numeric.zeros((isoc.nvert,3)).astype('f')
	norm = Numeric.zeros((isoc.nvert,3)).astype('f')
	col = Numeric.zeros((isoc.nvert)).astype('f')
	tri = Numeric.zeros((isoc.ntri,3)).astype('i')

	isocontour.getContour3dData(isoc, vert, norm, col, tri, 0)

	if maskGrid.crystal:
		vert = maskGrid.crystal.toCartesian(vert)

	return (vert, tri)
