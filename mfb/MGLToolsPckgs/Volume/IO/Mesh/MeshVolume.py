## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Anna Omelchenko
#
# Copyright: M. Sanner TSRI
#
#############################################################################

#
#$Header: /opt/cvs/Volume/IO/Mesh/MeshVolume.py,v 1.2 2007/07/24 17:30:45 vareille Exp $
#
#$Id: MeshVolume.py,v 1.2 2007/07/24 17:30:45 vareille Exp $
#
import numpy.oldnumeric as Numeric, struct
import sys

import mesh
#
# load low resolution volume
class MeshVolume:
    def __init__(self, filename, ps=512, mcs=400000):
        self.inputFile = filename
        self.ps = ps
        self.mcs = mcs
        self.decoder = mesh.FormatCatalog_createDecoder(self.inputFile)
        self.ca = mesh.CacheAttributes(self.mcs, self.ps)
        self.mesh = mesh.StructuredMesh(self.decoder, 0, self.ca)
        self.sma = self.mesh.getStructuredMeshAttributes()
        self.nGda = self.sma.getGridDimensionCount()
        self.gda = []
        for i in range(self.nGda):
            self.gda.append(self.sma.getGridDimensionAttributes(i))

        self.elementAttributes = self.sma.getElementAttributes()
        self.bounds = ( self.gda[0].getSize(), self.gda[1].getSize(),
                        self.gda[2].getSize() )
        print "***Mesh_info*****************"
        print "inputFile:" , self.inputFile
        print "MaximumCachePageCount:", self.ca.getMaximumCachePageCount()
        print " MaximumCacheSize:", self.ca.getMaximumCacheSize()
        print "MaximumPageSize:" , self.ca.getMaximumPageSize()
        print "*****************************"

    def getSubVolume(self, fieldName, x1, x2, y1, y2, z1, z2):
        fieldNameIndex = self.elementAttributes.getFieldIndex(fieldName)
        arrPtr = self.mesh.GetSubVolume( x1, x2, y1, y2, z1, z2,
                                         fieldNameIndex,
                                         self.elementAttributes )
        return arrPtr

    def getZeroPaddedSubVolume(self, fieldName, x1, x2, y1, y2, z1,z2):
        fieldNameIndex = self.elementAttributes.getFieldIndex(fieldName)
        outdata = self.mesh.GetZeroPaddedSubVolume( x1, x2, y1, y2, z1, z2,
                                         fieldNameIndex,
                                         self.elementAttributes )
        #outdata is a tuple of data pointer and three new array dimensions -
        #(arrptr, nx, ny, nz).
        return outdata
