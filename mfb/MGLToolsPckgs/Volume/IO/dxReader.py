## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

import numpy.oldnumeric as Numeric
from string import split
from  Volume.Grid3D import Grid3DF, Grid3DSI, Grid3DUC

class ReadDX:

    def __init__(self):
        self.header = {}
        self.filename = None


    def read(self, filename, normalize):
        self.filename = filename
        data = self.readAllLines(filename)
        return self.parse(data, normalize)
    

    def readAllLines(self, filename):
        # open file to read
        f = open(filename, 'r')
        data = f.readlines()
        f.close()
        return data

        
    def parse(self, data, normalize):

        h = self.header = {}
   
        # read header (need some specs here)
        w = split(data[4])
        nx, ny, nz = int(w[5]), int(w[6]), int(w[7])
        h['nx']=nx; h['ny']=ny; h['nz']=nz

        w = split(data[5])
        ox, oy, oz = float(w[1]), float(w[2]), float(w[3])
        h['origin']= (ox, oy, oz)

        w = split(data[6])
        h['stepx'] = sx = float(w[1])

        w = split(data[7])
        h['stepy'] = sy = float(w[2])

        w = split(data[8])
        h['stepz'] = sz = float(w[3])

        self.data = array = Numeric.zeros( (nx,ny,nz), Numeric.Float32)
        values = map(split, data[11:-5])
        ind=0
        size = nx*ny*nz
        for line in values:
            if ind>=size:
                break
            l = len(line)
            array.flat[ind:ind+l] = map(float, line)
            ind = ind + l

        stepSize = [h['stepx'], h['stepy'], h['stepz']]
        volume = Grid3DF(self.data, h['origin'], stepSize, h)
        return volume


    def describe(self):
        print "DX file: ", self.filename
        print "nx= ", self.header['nx']
        print "ny= ", self.header['ny'] 
        print "nz= ", self.header['nz'] 
        #print "xlen= ", self.header['xlen'] 
        #print "ylen= ", self.header['ylen'] 
        #print "zlen= ", self.header['zlen']
        print "min= ", min(self.data.ravel())
        print "max= ", max(self.data.ravel())
        #print "mean= ", self.header['amean']
        print "origin= ", self.header['origin'] 


if __name__=='__main__':
    reader = ReadDX()
    header, vol = reader.read("pot-0mM.dx")
    reader.describe()

