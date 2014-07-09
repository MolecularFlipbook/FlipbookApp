import sys,os, time, random, pickle, pdb
import bpy

def main(args):

	# parses argument from command
	cachePath, pdbid, chains, method = args[-4:]

	# sanitize input
	pdbid = pdbid.lower()

	# get MolKit per-chain centers
	fp = open(os.path.join(cachePath, pdbid, "centers"), mode='rb')
	chainsCenter = pickle.load(fp)

	for chain in chains.split():

		if method == 'simple':
			# create blender data
			name = pdbid+"_"+chain+"_bb"

			# blender calls
			curveData = bpy.data.curves.new(name, type='CURVE')
			curveData.dimensions = '3D'
			curveData.fill_mode = 'FULL'
			curveData.bevel_depth = 1
			curveData.bevel_resolution = 0

			# open geom file containing CA info
			verts = os.path.join(cachePath, pdbid, str(ord(chain))+".backbone")
			fileVerts = open(verts, mode='rb')

			alphaCarbons = pickle.load(fileVerts)

			if alphaCarbons:

				polyline = curveData.splines.new('NURBS')
				polyline.points.add(len(alphaCarbons)+1)  	# double vertex at both end

				# duplicate first index
				coord = alphaCarbons[0]
				polyline.points[0].co = (coord[0], coord[1], coord[2], 1)

				# loop through body
				for i, coord in enumerate(alphaCarbons):
					x, y, z = coord
					polyline.points[i+1].co = (x, y, z, 1)

				# duplicate last index
				coord = alphaCarbons[-1]
				polyline.points[-1].co = (coord[0], coord[1], coord[2], 1)


				curveData.resolution_u = 2
				curveOB = bpy.data.objects.new(name, curveData)

				# add mat
				mat = bpy.data.materials.new(name)
				color3d = (random.random(), random.random(), random.random())
				mat.diffuse_color = (color3d)
				mat.specular_intensity = 0.0
				mat.diffuse_intensity = 1.0
				curveData.materials.append(mat)

				# attach to scene and validate context
				scn = bpy.context.scene
				scn.objects.link(curveOB)
				scn.objects.active = curveOB
				curveOB.select = True

				# origin
				bpy.context.scene.cursor_location = chainsCenter[chain]
				bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")

				bpy.ops.object.convert(target='MESH', keep_original=False)

				curveOB.data.name = name
				curveOB.select = False

	bpy.ops.wm.save_mainfile(filepath = os.path.join(cachePath, pdbid, "geometry.blend"))


if __name__ == '__main__':

	start = time.time()
	main(sys.argv)
	end = time.time()
	print ("Bone Importing time: ", end-start)
