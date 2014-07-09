#$Header: /opt/cvs/python/packages/share1.5/Pmv/msmsClient.py,v 1.3 2008/12/23 00:29:19 sargis Exp $
#
#$Id: msmsClient.py,v 1.3 2008/12/23 00:29:19 sargis Exp $
#
# Authors: M. Sanner and S. Dallakyan

import socket
import subprocess
import numpy
import struct
from mglutil.util.packageFilePath import getBinary, which
try:
    msmsBinary = getBinary('msms','binaries')
except:
    msmsBinary = None

if not msmsBinary: #msms not found in binaries
    msmsBinary = which('msms')

msmsBinary = None #(un)comment this line to (not) use msmsClient instead of mslib 
class MSMSClient:    
    def __init__(self, coords=None, radii=None, **kw):
        
        self.coords = coords
        self.radii = radii        
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = 2000
        #find a free port
        result = soc.connect_ex(('', port))
        while not result:
            port += 1
            result = soc.connect_ex(('', port))
            soc.close()
        self.port = port
        proc = subprocess.Popen([msmsBinary, "-socketPort", str(port)], stdout=subprocess.PIPE)
        if proc.returncode:
            result = None
            while not result:
                port += 1
                result = soc.connect_ex(('', port))
                soc.close()
            self.port = port
            proc = subprocess.Popen([msmsBinary, "-socketPort", str(port)], stdout=subprocess.PIPE)
        #print "msms server started on port "+str(port)
        self.proc = proc
     
    def compute(self, probe_radius, density, **kw):
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connected = False
        for i in range(1000):#this is done to make sure msms is ready to accept a client.     
            try:
                soc.connect(('', self.port))
                connected = True
                #print "msms client connected on port "+str(self.port)
                break;
            except Exception, inst:
                pass
                #print inst
        print connected
        if not connected: 
            raise RuntimeError("Unable to connect to msms on port "+str(self.port))
        soc.settimeout(None) 
        lenCoord = len(self.coords)
        soc.send(struct.pack('ffiii', probe_radius, density, 0, 1, lenCoord))

        for i in range(lenCoord):
            x, y, z = self.coords[i]
            soc.send( struct.pack('ffffi', x, y, z, self.radii[i], 1))  
        msg = ''
        while 1:
            d = soc.recv(1)
            if d[0]=='\n':
                break
            msg += d
        print msg
        # e.g. "tahiti: MSMS SERVICE started on tahiti"
        cmd = ''
        while 1:
            d = soc.recv(1)
            if d and d[0]=='\n':
                break
            cmd += d        
        #cmd can be one of the following strings
        # MSMS END this tring should be received after the calculation ocmpleted
        #          successfuly and the data was sent back
        # MSMS RS  This string indicates that next the reduced surface will be sent
        # MSMS RCF This string indicates that nexttbhe triangulated surface will be sent
        print cmd        
        isize = struct.calcsize('i')
        fsize = struct.calcsize('f')
        
        d = soc.recv(isize)
        nbf = struct.unpack('i', d)[0]
        
        d = soc.recv(isize)
        nbv = struct.unpack('i', d)[0]
        
        soc.setblocking(1) # to avoid recv to return with partial data
        

        # get the faces
        d = soc.recv(nbf*5*isize)
        while len(d) != nbf*5*isize:
            d += soc.recv(nbf*5*isize-len(d))
            
        faces = struct.unpack('%di'%(nbf*5), d)
        faces = numpy.array(faces)
        faces.shape = (-1,5)
        
        # get the vertices
        d = soc.recv(nbv*6*fsize)
        while len(d) != nbv*6*isize:
            d += soc.recv(nbv*6*isize-len(d))
        vn = struct.unpack('%df'%(6*nbv), d)
        vf = numpy.array(vn)
        vf.shape = (-1,6)
        
        d = soc.recv(nbv*isize)
        indices = struct.unpack('%di'%nbv, d)     
        #self.vf = vf
        self.faces = faces
        self.indices = indices
        self.vfloat =  numpy.zeros((len(self.indices), 6), dtype=numpy.float)
        self.vint =  numpy.zeros((len(self.indices), 3), dtype=numpy.int)

        for index, atomIndex in enumerate(self.indices):
            self.vfloat[index] = [vf[index][3], vf[index][4], vf[index][5],
                                  vf[index][0], vf[index][1], vf[index][2]]
            self.vint[index] = [0, self.indices[index], 0]

        if hasatrr(self.proc, 'terminate'): #New in Python 2.6.
            self.proc.terminate()
            
    def getTriangles(self, atomindices, **kw):
        firstTime = True
        indices = range(len(self.faces))
        faces = self.faces.copy()
        for index, item in enumerate(self.indices):
            if item in atomindices: continue
            #else
            for i, face in enumerate(faces[indices]):
                if (face[0] == index) or (face[1] == index) or (face[2] == index):
                    if i in indices:
                        indices.remove(i)    
        return self.vfloat, self.vint, faces.take(indices, axis=0)
        