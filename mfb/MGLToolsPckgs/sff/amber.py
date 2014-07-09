## Automatically adapted for numpy.oldnumeric Jul 30, 2007 by 

#
# Copyright_notice
#

import _prmlib as prmlib
import re
import os
import numpy.oldnumeric as Numeric
from types import StringType


realType = Numeric.Float
intType = Numeric.Int
pyArrayInt = prmlib.PyArray_INT
pyArrayDouble = prmlib.PyArray_DOUBLE

getpat = re.compile( 'parmstruct_(\w+)_get')
parmattrs = {}


for x in dir( prmlib):
    match = getpat.match( x)
    if match:
        parmattrs[ match.group( 1) ] = None
            
parmbuffers = {
    'AtomNames': (StringType, lambda x: x.Natom * 4 + 81, None),
    'Charges': (realType, lambda x: x.Natom, pyArrayDouble ),
    'Masses': (realType, lambda x: x.Natom, pyArrayDouble),
    'Iac': (intType, lambda x: x.Natom, pyArrayInt),
    'Iblo': (intType, lambda x: x.Natom, pyArrayInt),
    'Cno': (intType, lambda x: x.Ntype2d, pyArrayInt),
    'ResNames': (StringType, lambda x: x.Nres * 4 + 81, None),
    'Ipres': (intType, lambda x: x.Nres + 1, pyArrayInt),
    'Rk': (realType, lambda x: x.Numbnd, pyArrayDouble),
    'Req': (realType, lambda x: x.Numbnd, pyArrayDouble),
    'Tk': (realType, lambda x: x.Numang, pyArrayDouble),
    'Teq': (realType, lambda x: x.Numang, pyArrayDouble),
    'Pk': (realType, lambda x: x.Nptra, pyArrayDouble),
    'Pn': (realType, lambda x: x.Nptra, pyArrayDouble),
    'Phase': (realType, lambda x: x.Nptra, pyArrayDouble),
    'Solty': (realType, lambda x: x.Natyp, pyArrayDouble),
    'Cn1': (realType, lambda x: x.Nttyp, pyArrayDouble),
    'Cn2': (realType, lambda x: x.Nttyp, pyArrayDouble),
    'Boundary': (intType, lambda x: x.Nspm, pyArrayInt),
    'BondHAt1': (intType, lambda x: x.Nbonh, pyArrayInt),
    'BondHAt2': (intType, lambda x: x.Nbonh, pyArrayInt),
    'BondHNum': (intType, lambda x: x.Nbonh, pyArrayInt),
    'BondAt1': (intType, lambda x: x.Nbona, pyArrayInt),
    'BondAt2': (intType, lambda x: x.Nbona, pyArrayInt),
    'BondNum': (intType, lambda x: x.Nbona, pyArrayInt),
    'AngleHAt1': (intType, lambda x: x.Ntheth, pyArrayInt),
    'AngleHAt2': (intType, lambda x: x.Ntheth, pyArrayInt),
    'AngleHAt3': (intType, lambda x: x.Ntheth, pyArrayInt),
    'AngleHNum': (intType, lambda x: x.Ntheth, pyArrayInt),
    'AngleAt1': (intType, lambda x: x.Ntheta, pyArrayInt),
    'AngleAt2': (intType, lambda x: x.Ntheta, pyArrayInt),
    'AngleAt3': (intType, lambda x: x.Ntheta, pyArrayInt),
    'AngleNum': (intType, lambda x: x.Ntheta, pyArrayInt),
    'DihHAt1': (intType, lambda x: x.Nphih, pyArrayInt),
    'DihHAt2': (intType, lambda x: x.Nphih, pyArrayInt),
    'DihHAt3': (intType, lambda x: x.Nphih, pyArrayInt),
    'DihHAt4': (intType, lambda x: x.Nphih, pyArrayInt),
    'DihHNum': (intType, lambda x: x.Nphih, pyArrayInt),
    'DihAt1': (intType, lambda x: x.Nphia, pyArrayInt),
    'DihAt2': (intType, lambda x: x.Nphia, pyArrayInt),
    'DihAt3': (intType, lambda x: x.Nphia, pyArrayInt),
    'DihAt4': (intType, lambda x: x.Nphia, pyArrayInt),
    'DihNum': (intType, lambda x: x.Nphia, pyArrayInt),
    'ExclAt': (intType, lambda x: x.Nnb, pyArrayInt),
    'HB12': (realType, lambda x: x.Nphb, pyArrayDouble),
    'HB10': (realType, lambda x: x.Nphb, pyArrayDouble),
    'Box': (realType, lambda x: 3, pyArrayDouble),
    'AtomSym': (StringType, lambda x: x.Natom * 4 + 81, None),
    'AtomTree': (StringType, lambda x: x.Natom * 4 + 81, None),
    'TreeJoin': (intType, lambda x: x.Natom, pyArrayInt),
    'AtomRes': (intType, lambda x: x.Natom, pyArrayInt),
    'N14pairs': (intType, lambda x: x.Natom, pyArrayInt),
    'N14pairlist': (intType, lambda x: 10*x.Natom, pyArrayInt),
   }
    
def checkbuffersize( parmobj, attr, value):
    attrlen = parmbuffers[ attr][ 1]( parmobj)
    if attr in ['AtomNames', 'AtomSym', 'AtomTree']:
        attrlen = parmobj.Natom * 4
    elif attr == 'ResNames':
        attrlen = parmobj.Nres * 4
    elif attr == 'Ipres':
        attrlen = parmobj.Nres
    elif attr == 'N14pairlist':
        from operator import add
        sum = reduce( add, parmobj.N14pairs )
        attrlen = sum
        if sum!=len(value):
            print 'WARNING: N14pairlist length'
            attrlen = len(value)
            
    if len( value) < attrlen:
        raise ValueError( attr, attrlen, len( value))

class AmberParm:
    def __init__( self, name, parmdict=None):
        """
        name - string
        parmdict - map
        """
        import types

        self.name  = name
        if parmdict:
            parmptr = self._parmptr_ = prmlib.parmcalloc()
            for name in parmattrs.keys():
                value = parmdict[ name]
                try:
                    bufdesc = parmbuffers[ name]
                except KeyError:
                    pass
                else:
                    if bufdesc[ 0] != StringType\
                       and not isinstance( value, StringType):
                        value = Numeric.array( value).astype(bufdesc[ 0])
                self.__dict__[ name] = value
                if name == 'Box':
                    self.Box[:] = value
                else:
                    getattr( prmlib, 'parmstruct_%s_set' % name)( parmptr, value)

        else:
            assert os.path.exists( name )
            self._parmptr_ = parmptr = prmlib.readparm( name)
            for attr in filter( lambda x: not parmbuffers.has_key( x),
                                parmattrs.keys()):
                value = getattr( prmlib, 'parmstruct_%s_get' % attr)( parmptr)
                self.__dict__[ attr] = value
               
            for attr in filter( lambda x: parmbuffers.has_key( x),
                                parmattrs.keys()):
                # these _get() functions  must not be called from anywhere else
                #print "attr:", attr,
                value = getattr( prmlib, 'parmstruct_%s_get' % attr)( parmptr)
                #print "value: ", value
                if value is None:
                    value = ()
                else:
                    bufdesc = parmbuffers[ attr]
                    if bufdesc[ 0] != StringType:
                        value = prmlib.createNumArr(value,  bufdesc[ 1]( self), bufdesc[2])

                self.__dict__[ attr] = value
        if __debug__:
            for attr in parmbuffers.keys():
                val = getattr(self, attr)
                if isinstance(val, Numeric.ArrayType) or isinstance(val, StringType):
                    checkbuffersize(self, attr, val)
            
    def __setattr__( self, name, value):
        if parmattrs.has_key( name):
            raise AttributeError( 'constant parm attribute')
        self.__dict__[ name] = value

    def __del__( self):
        prmlib.parmfree( self._parmptr_)
        delattr( self, '_parmptr_')
        

    def asDict(self):
        # return the content of the parm structure as a python dict
        d = {}
        for k in self.__dict__.keys():
            if k[0]=='_': continue
            if parmbuffers.has_key(k):
                value = list(getattr(self, k))
            else:
                value = getattr(self, k)
            d[k] = value
        return d


import threading
amberlock = threading.RLock()

import struct

class BinTrajectory:
    
    ## WARNING nothing is done about byte order
    def __init__(self, filename):
        import os
        assert os.path.isfile(filename)
        self.filename = filename
        self.typecode = 'f'
        if prmlib.UseDouble:
            self.typecode = 'd'
        self.coordSize = struct.calcsize(self.typecode)
        self.intSize = struct.calcsize('i')
        self.fileHandle = None
        

    def getNumberOfAtoms(self, filename):
        f = open(filename, 'rb')
        lenstr = f.read(struct.calcsize('i'))
        f.close()
        return struct.unpack('i', lenstr)[0]
    

    def closeFile(self):
        self.fileHandle.close()
        self.fileHandle = None

        
    def getNextConFormation(self):
        # open file if necessary
        if self.fileHandle is None:
            self.fileHandle = open(self.filename)

        # read the number of atoms as an integer
        lenstr = self.fileHandle.read(self.intSize)
        if len(lenstr) < self.intSize: #EOF reached
            self.closeFile()
            return None
        nba = struct.unpack('i', lenstr)[0]
        size = 3 * nba * self.coordSize

        # read the coordinates for nba atoms
        crdstr = self.fileHandle.read( size )
        if len(crdstr) != size: #EOF reached
            self.closeFile()
            return None
        c = Numeric.array( struct.unpack( '%dd'%3*nba, crdstr),
                           self.typecode )
        c.shape = (-1, 3)
        return c

        

class Amber94:

    from MolKit import parm94_dat

    def __init__(self, atoms, parmtop=None, prmfile=None, dataDict={}):

        from MolKit.amberPrmTop import Parm

        self.atoms = atoms
        self.parmtop = parmtop
        if prmfile:
            self.oprm = AmberParm( prmfile )
        else:
            if self.parmtop is None:
                # create parmtop info
                if not len(dataDict):
                    self.parmtop = Parm()
                else:
                    #dataDict is a dictionary with possible keys:
                    #allDictList, ntDictList, ctDictList
                    #whose values are lists of python files such as
                    #found in MolKit/data...which end in dat.py
                    #dataDict['allDictList']=[all_amino94_dat]
                    #if len(list)>1, the first is updated by the rest
                    self.parmtop = apply(Parm, (), dataDict)
                self.parmtop.processAtoms(atoms, self.parm94_dat)
                #this read is broken
                #self.parmtop.loadFromFile(prmfile)
            else:
                assert isinstance(parmtop, Parm)

            # create the C-data structure
            self.oprm = AmberParm( 'test', self.parmtop.prmDict )

        from operator import add
        coords = self.atoms.coords[:]
        lcoords = reduce( add, coords)
        self.coords = Numeric.array( lcoords).astype(realType )
        
        # create Numeric array for frozen
        self.frozen = Numeric.zeros( self.oprm.Natom).astype(intType)

        # create Numeric array for constrained
        self.constrained = Numeric.zeros( self.oprm.Natom). astype(intType)

        # create Numeric array for anchor
        self.anchor = Numeric.zeros( 3*self.oprm.Natom).astype(realType) 

        # create Numeric array for minv (md)
        self.minv = Numeric.zeros( 3*self.oprm.Natom).astype(realType )
        
        # create Numeric array for v (md)
        self.mdv = Numeric.zeros( 3*self.oprm.Natom).astype(realType)
        
        # create Numeric array for f (md)
        self.mdf = Numeric.zeros( 3*self.oprm.Natom).astype( realType )

        # is the number of variables
        self.nbVar = Numeric.array([3*self.oprm.Natom]).astype(intType)

        # will contain the value of the objective function at the end
        self.objFunc = Numeric.zeros( 1).astype(realType )

        # return when sum of squares of gradient is less than dgrad
        drms = 0.1
        self.dgrad = Numeric.array([drms*3*self.oprm.Natom]).astype(realType)

        # expected decrease in the function on the first iteration
        self.dfpred = Numeric.array( [10.0,]).astype( realType )

        # 
        self.maxIter = Numeric.array([500,]).astype(intType)

        #
        self.energies = Numeric.zeros(20).astype(realType )

        # filename used to save trajectory
        self.filename = None
        self.sff_opts = prmlib.init_sff_options()

    def setMinimizeOptions(self, **kw):
        # WARNING when cut it set mme_init needs to be called to allocate a
        # list of non-bonded paires of the proper size
        for k,v in kw.items():
            assert k in ['cut', 'nsnb', 'ntpr', 'scnb', 'scee',
                         'mme_init_first', 'dield', 'verbosemm',
                         'wcons']
            #prmlib.mm_options(k, v)
            #setattr(prmlib.cvar, k, v)
            prmlib.mm_options(k, v, self.sff_opts)
        

    def setMdOptions(self, **kw):
        #nb: for the moment set verbosemm for verbosemd
        for k,v in kw.items():
            assert k in ['t', 'dt', 'tautp', 'temp0', 'boltz2', 'verbosemd',
                          'ntwx','vlimit', 'ntpr_md', 'zerov', 'tempi', 'idum' ]
            #prmlib.md_options(k, v)
            #setattr(prmlib.cvar, k, v)
            prmlib.md_options(k, v, self.sff_opts)


    def setCallback(self, func, frequency):
        assert callable(func)
        prmlib.set_callback(func, frequency, 0)

        
    def freezeAtoms(self, atomIndices):
        assert len(atomIndices)==len(self.atoms), 'atomIndices wrong length'
        self.frozen = Numeric.array(atomIndices).astype(intType)


    def constrainAtoms(self, atomIndices, anchor):
        atlen = len(self.atoms)
        assert len(atomIndices)==atlen, 'atomIndices wrong length'
        #this is not right:
        #constNum = Numeric.add.reduce(atomIndices)
        #anchors have garbage for non-constrained atoms
        assert len(anchor)==atlen*3, 'anchor wrong length'
        self.constrained = Numeric.array(atomIndices).astype(intType)
        self.anchor = Numeric.array(anchor).astype(realType)
    
    def minimize(self, drms=None, maxIter=None, dfpred=None):

        if drms is not None: self.dgrad[0] = drms*3*self.oprm.Natom
        if maxIter is not None: self.maxIter[0] = maxIter
        if dfpred is not None: self.dfpred[0] = dfpred
            
        prmlib.mme_init(self.frozen, self.constrained, self.anchor,
                        None, self.oprm._parmptr_, self.sff_opts)

        amberlock.acquire()
        result_code = -6
        try:
            # add new thread here
            result_code = prmlib.conjgrad( self.coords, self.nbVar, self.objFunc,
                   prmlib.mme_fun, self.dgrad, self.dfpred, self.maxIter,
                   self.oprm._parmptr_, self.energies, self.sff_opts )
        finally:
            amberlock.release()

        return result_code

    
    def md(self, maxStep, filename=None):

        self.filename = filename
        if filename is not None:
            f = open(filename, 'w')
        else:
            f = None

        prmlib.mme_init(self.frozen, self.constrained, self.anchor,
                        f, self.oprm._parmptr_, self.sff_opts)

        amberlock.acquire()
        result_code = -6
        try:
            # add new thread here
            result_code = prmlib.md( 3*self.oprm.Natom, maxStep, self.coords,
                                     self.minv, self.mdv, self.mdf,
                                     prmlib.mme_fun, self.energies,
                                     self.oprm._parmptr_ , self.sff_opts)
        finally:
            amberlock.release()

        if filename is not None:
            f.close()

        return result_code
