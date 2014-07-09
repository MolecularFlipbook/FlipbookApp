## Automatically adapted for numpy.oldnumeric Jul 30, 2007 by 

#from UTpackages.UTsdf import utsdf
from string import split
import struct, os
import unittest

def write_file(data, dim, packType = 'f', file = "outfile.rawiv"):
    """Writes data in .rawiv file."""
    nx = ny = nz = dim
    print(("writing to file: %s, data size: %d, %d, %d" % (file, nx,ny,nz)))
    size = nx*ny*nz
    size1 = (nx-1)*(ny-1)*(nz-1)
    of = open(file,"wb")
    #Header: FIXME - not sure if this is right
    st=(0.0, 0.0, 0.0, float(nx), float(ny),float(nz),
	size, size1, nx, ny, nz, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
    of.write(struct.pack(*('>6f5I6f',)+st))
    #fmt = ">%dB"%size
    fmt = ">%d%s"%(size, packType)
    of.write( struct.pack(*(fmt,)+tuple(data.ravel())))
    
def readData (file):
    f= open(file)
    l1 = f.readline()
    str = split(l1)
    nverts = int(str[0])
    ntris = int(str[1])
    print(("nverts = %d, ntris = %d"%(nverts, ntris)))
    verts = []
    tris = []
    for i in range(nverts):
        l = f.readline()
        str = split(l)
        if len(str) != 3:
            print(("reading verts: i = %d, str = %s"%(i, str)))
            f.close()
            return 0,0
        v = [float(str[0]), float(str[1]), float(str[2])]
        
        verts.append(v)
    for i in range(ntris):
        l = f.readline()
        str = split(l)
        if len(str) != 3:
            print(("reading tris: i = %d, str = %s"%(i, str)))
            f.close()
            return 0,0
        tri = [int(str[0]), int(str[1]), int(str[2])]
        tris.append(tri)
    f.close()
    return verts, tris

def test_0import():
    print("test_0import()")
    from UTpackages.UTsdf import utsdf
    
def test_1lib():
    print("test_1lib()")   	
    from UTpackages.UTsdf import utsdf
    verts, tris = readData("eight.raw")
    dim = 64
    utsdf.setParameters(dim, 0, 1, [0,0,0,0,0,0])
    datap = utsdf.computeSDF(verts, tris)
    dim1 = dim+1
    size = dim1*dim1*dim1
    data = utsdf.createNumArr(datap, dim1*dim1*dim1)
    print(("len(data) = ", len(data)))
    assert len(data) == size
    outfile =  "outsdf.rawiv"
    write_file(data, dim1,file = outfile)
    assert os.path.isfile( outfile)


if __name__ == '__main__':
    unittest.main(argv=([__name__,]) )
