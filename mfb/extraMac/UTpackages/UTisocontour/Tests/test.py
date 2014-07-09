## Automatically adapted for numpy.oldnumeric Jul 30, 2007 by 

# test for isocontour Python extension . From ../ :
# tester Tests.test
import sys
import unittest
import numpy.oldnumeric as Numeric
from Pmv import Grid
from UTpackages import UTisocontour

class TestIsocontour(unittest.TestCase):
    auC = None
    def setUp(self):
        from UTpackages import UTisocontour
        print(UTisocontour.__file__)
        if not self.auC:
            self.auC = Grid.AutoGrid('1ak3.C.map')
        
    def test_loadDataset(self):
        the_data = UTisocontour.loadDataset(UTisocontour.CONTOUR_FLOAT,
                                      UTisocontour.CONTOUR_REG_3D, 3, 1,
                                      ["pot-2eti-glucose-3fields.raw"]);


        isovar   = 0
        timestep = 0
        isovalue = 0.23

        isoc = UTisocontour.getContour3d(the_data, isovar, timestep, isovalue,
                                       UTisocontour.NO_COLOR_VARIABLE)

        print("nvert:", isoc.nvert)
        print("ntri:", isoc.ntri)
        #assert isoc.nvert == 12816
        assert isoc.nvert == 3204
        assert isoc.ntri == 6392
        vert = Numeric.zeros((isoc.nvert,3)).astype('f')
        norm = Numeric.zeros((isoc.nvert,3)).astype('f')
        col = Numeric.zeros((isoc.nvert)).astype('f')
        tri = Numeric.zeros((isoc.ntri,3)).astype('i')
        UTisocontour.getContour3dData(isoc, vert, norm, col, tri, 0)

        # signature stuff
        nsig = UTisocontour.getNumberOfSignatures(the_data)
        sig0 = UTisocontour.getSignatureFunctions(the_data, 0, 0)
        sig1 = UTisocontour.getSignatureFunctions(the_data, 1, 0)
        sig2 = UTisocontour.getSignatureFunctions(the_data, 2, 0)
        print(sig0.name, sig0.nval)
        print(sig1.name, sig1.nval)
        print(sig2.name, sig2.nval)

        print("signatureValues:", UTisocontour.getSignatureValues(the_data, 0, 0, 0.23))

    def test_newDatasetRegFloat3D(self):

        # we have to swap axes because in a grid object z varies faster then y which
        # in turn varies faster then x
        sh = (1,3,self.auC.NELEMENTS[0],self.auC.NELEMENTS[1], self.auC.NELEMENTS[2])
        da = Numeric.zeros(sh).astype('f')
        da[0][0] = Numeric.array( Numeric.reshape( Numeric.swapaxes( self.auC.array, 0, 2), self.auC.NELEMENTS ) ).astype('f')
        center = Numeric.array(self.auC.CENTER).astype('f')
        dim = Numeric.array(self.auC.NELEMENTS).astype('f')
        span = Numeric.array(self.auC.SPACING).astype('f')
        print("span: ", span)
        orig = center - ((dim-1)/2)*span
        print("orig: ", orig)
        the_data = UTisocontour.newDatasetRegFloat3D(da, orig.astype('f'), (span,)*3 )
    ##      the_data = UTisocontour.newDatasetRegFloat3D(da)
    ##      UTisocontour.setOrig3D(the_data, orig.astype('f'))
    ##      UTisocontour.setSpan3D(the_data, (span,)*3)
        isovar   = 0
        timestep = 0
        isovalue = 0.23

        isoc = UTisocontour.getContour3d(the_data, isovar, timestep, isovalue,
                                       UTisocontour.NO_COLOR_VARIABLE)
        vert = Numeric.zeros((isoc.nvert,3)).astype('f')
        norm = Numeric.zeros((isoc.nvert,3)).astype('f')
        col = Numeric.zeros((isoc.nvert)).astype('f')
        tri = Numeric.zeros((isoc.ntri,3)).astype('i')
        print("nvert:", isoc.nvert)
        print("ntri:", isoc.ntri)
        #assert isoc.nvert == 28478
        assert isoc.nvert ==7394
        assert isoc.ntri == 14220
        UTisocontour.getContour3dData(isoc, vert, norm, col, tri, 1)
        nsig = UTisocontour.getNumberOfSignatures(the_data)
        sig0 = UTisocontour.getSignatureFunctions(the_data, 0, 0)
        sig1 = UTisocontour.getSignatureFunctions(the_data, 1, 0)
        sig2 = UTisocontour.getSignatureFunctions(the_data, 2, 0)
        print(sig0.name, sig0.nval)
        print(sig1.name, sig1.nval)
        print(sig2.name, sig2.nval)

        print("signatureValues:", UTisocontour.getSignatureValues(the_data, 0, 0, 0.23))
        datainfo = UTisocontour.getDatasetInfo(the_data)
        orig=datainfo._orig()
        span=datainfo._span()
        print("orig: ", orig)
        print("span: ", span)

    def test_getSliceArray(self):

        assert hasattr(UTisocontour, 'getSliceArray')
        isovar=0
        timestep=0
        axis='x'
        sliceNum=10
        step=1
        sh = (1,1, self.auC.NELEMENTS[0], self.auC.NELEMENTS[1], self.auC.NELEMENTS[2])
        da = Numeric.zeros(sh).astype('f')
        da[0][0] = Numeric.array( Numeric.reshape( Numeric.swapaxes( self.auC.array, 0, 2), self.auC.NELEMENTS ) ).astype('f')
        daSmall = Numeric.array(da[:,:,::step,::step,::step]).astype('f')
        center = Numeric.array(self.auC.CENTER).astype('f')
        dim = Numeric.array(self.auC.NELEMENTS).astype('f')
        span = Numeric.array(self.auC.SPACING).astype('f')
        print("span:", span)
        orig = center - ((dim-1)/2)*span
        print("orig: ", orig)
        the_data = UTisocontour.newDatasetRegFloat3D(daSmall,
                                        orig.astype('f'), (span*step,)*3 )
        #the_data = UTisocontour.newDatasetRegFloat3D(daSmall)

        sld = UTisocontour.getSliceArray(the_data, isovar,
                                       timestep, axis, sliceNum)
        print('sld.shape' ,sld.shape)
        assert sld.shape == (61, 41)

if __name__ == '__main__':
    unittest.main(argv=([__name__,]) )
        

