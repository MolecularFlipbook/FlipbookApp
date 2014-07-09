#############################################################################
#
# Author: Ludovic Autin
#
# Copyright: L. Autin TSRI 2010
#
#############################################################################

# $Header: /opt/cvs/python/packages/share1.5/ViewerFramework/imdCommands.py,v 1.6 2010/08/17 20:03:47 autin Exp $
#
# $Id: imdCommands.py,v 1.6 2010/08/17 20:03:47 autin Exp $
#

"""
This module implements classes to start a server and to connect to a server.
"""
#import psyco
#psyco.full()

from ViewerFramework.VFCommand import Command
from Pmv.moleculeViewer import EditAtomsEvent
import struct
import numpy
from numpy import matrix
import sys, os
from socket import *
if os.name == 'nt': #sys.platform=='win32':
    mswin = True
else:
    mswin = False

HEADERSIZE=8
IMDVERSION=2
IMD_DISCONNECT=0   #//!< close IMD connection, leaving sim running    0
IMD_ENERGIES=1   #//!< energy data block                1
IMD_FCOORDS=2   #//!< atom coordinates                2
IMD_GO=3   #//!< start the simulation                3
IMD_HANDSHAKE=4   #//!< endianism and version check message        4
IMD_KILL=5   #//!< kill the simulation job, shutdown IMD        5
IMD_MDCOMM=6   #//!< MDComm style force data            6
IMD_PAUSE=7   #//!< pause the running simulation            7
IMD_TRATE=8   #//!< set IMD update transmission rate        8
IMD_IOERROR=9   #//!< indicate an I/O error                9

class vmdsocket:
    def __init__(self):
        self.addr=None   #!< address of socket provided by bind()
        self.port=None
        self.addrlen=None           #!< size of the addr struct
        self.sd=None                #< socket descriptor

class File2Send:
    def __init__(self):
        self.data=None
        self.length=None
        self.buffer=None
    
    #Convert a 32-bit integer from host to network byte order.
    def imd_htonl(self,h) :
        return htonl(h)

    #Convert a 32-bit integer from network to host byte order.
    def imd_ntohl(self,n) :
        return ntohl(n)

    def fill(self, data):
        self.data = data
        self.length = len(data)#self.imd_htonl(len(data))

    def swap_header(self) :
        #pass
        #self.imdtype = self.imd_ntohl(self.imdtype)
        self.length = self.imd_ntohl(self.length )

    def getBinary(self):
        """Returns the binary message (so far) with typetags."""
        length  = struct.pack(">i", int(self.length))
        if len(self.data) == 0 : 
            return length
        for l in self.data:
            length += struct.pack(">i", len(l))
            for i in l :
                length += struct.pack(">c", i)
        self.buffer = length
        return length

class Bonds2Send(File2Send):
    def getBinary(self):
        """Returns the binary message (so far) with typetags."""
        length  = struct.pack(">i", int(self.length))
        if len(self.data) == 0 : 
            return length
        for l in self.data:
            print l
            for j in range(len(l)):
                length += struct.pack(">i", int(l[j]))
        self.buffer = length
        return length

class IMDheader:
    def __init__(self):
        self.imdtype=None
        self.length=None
        self.buffer=None
    #Convert a 32-bit integer from host to network byte order.
    def imd_htonl(self,h) :
        return htonl(h)

    #Convert a 32-bit integer from network to host byte order.
    def imd_ntohl(self,n) :
        return ntohl(n)

    def fill_header(self, IMDType, length):
        self.imdtype = IMDType#self.imd_htonl(IMDType)
        self.length = length# self.imd_htonl(length)

    def swap_header(self) :
        self.imdtype = self.imd_ntohl(self.imdtype)
        self.length = self.imd_ntohl(self.length )

    def getBinary(self):
        """Returns the binary message (so far) with typetags."""
        types  = struct.pack(">i", int(self.imdtype))
        length  = struct.pack(">i", int(self.length))
        return types + length

class IMDEnergies:
    def __init__(self):
        self.buffer = None
        self.tstep = None      #//!< integer timestep index
        self.T = None      #//!< Temperature in degrees Kelvin
        self.Etot = None      #//!< Total energy, in Kcal/mol
        self.Epot = None      #//!< Potential energy, in Kcal/mol
        self.Evdw = None      #//!< Van der Waals energy, in Kcal/mol
        self.Eelec = None      #//!< Electrostatic energy, in Kcal/mol
        self.Ebond = None      #//!< Bond energy, Kcal/mol
        self.Eangle = None      #//!< Angle energy, Kcal/mol
        self.Edihe = None      #//!< Dihedral energy, Kcal/mol
        self.Eimpr = None      #//!< Improper energy, Kcal/mol
        self.len = 9*12+1*4    #number of element->9 float (12bit) 1 int (4bit)
        
class IMD(Command):
    """ This class implements method to connect to a server."""
    def checkDependencies(self, vf):
        import thread

    def init(self,hostname,
              mode,
              IMDwait_, 
              IMDport_, 
              IMDmsg_, 
              IMDlogname_,
              length
              ):
        self.current_buffer = None
        self.current_send_buffer = None
        self.mol = None
        self.slot = None
        self.imd_coords = numpy.zeros((length,3),'f')
        self.pause = False
        self.gui = False
        self.ffreq = 30
        self.rates = 1
        blen = 1024
        hname=""
        str=""
        IMDport=IMDport_
        if ( IMDlogname_ == 0 ) :
            IMDlog = sys.stderr
        else :
            IMDlog = open ( IMDlogname_, "w")
            if ( IMDlog == 0 ) :
                IMDlog.write("MDDriver >      Bad filename, using stderr\n")

        IMDmsg = IMDmsg_

        #IMDmsg < 0 force to display to stderr (IMDlog=stderr) 
        if( IMDmsg < 0) :
           IMDmsg = -IMDmsg
           IMDlog = sys.stderr
           IMDlog.write("MDDriver >      Negative IMDmsg - Setting IMDlog=stderr \n")

        if (IMDmsg > 1) :
           IMDlog.write("MDDriver > ---- Entering in %s\n"%sys._getframe().f_code.co_name)

        IMDwait   = IMDwait_  #  IMDwait = 1 -> blocking  
        IMDignore = 0

        #if ( self.vmdsock_init() ):
        #   IMDlog.write("MDDriver >      Unable to initialize socket interface for IMD.\n")
        IMDignore =  1;
        self.sock = self.vmdsock_create();
         
        self.vmdsock_connect(self.sock , hostname, IMDport)
        #before handshacking do we need to send the files
        if self.mindy:
            self.sendFiles()
        print "fileSend"
        IMDswap = self.imd_recv_handshake(self.sock);
        print "IMDswap",IMDswap
        """
      if ( IMDswap == 0 ){
    fprintf(IMDlog, "MDDriver >      Same endian machines\n");
      }
      else if ( IMDswap == 1 ) {
    fprintf(IMDlog, "MDDriver >      Different endian machines\n");
      }
      else {
    fprintf(IMDlog, 
        "MDDriver >      Unknown endian machine - disconnecting\n");
    if (sock) {
      imd_disconnect(sock);
      vmdsock_shutdown(sock);
      vmdsock_destroy(sock);
      sock = 0;
        if (IMDmsg > 1) 
            fprintf( IMDlog, "MDDriver > ---- Leaving     %s\n", __FUNCTION__); 

        """

        imd_event = -1;
        #return ( IMDlog )

    def vmdsock_create(self) :
        s=vmdsocket()
        #open socket using TCP/IP protocol family, using a streaming type and the
        #default protocol. This is connection-oriented, sequenced, error-controlled
        #and full-duplex
        #ref Wall p.380
        s.sd = socket(AF_INET, SOCK_STREAM) #no PF_INET in python
        if s.sd is None : 
            print "Failed to open socket."
            # TODO: provide error detail using errno
            return None
        return s

    def vmdsock_connect(self, vmdsocket, host, port) :
        #vmdsock_connect(sock, hostname, IMDport)
        s = vmdsocket
        host = gethostbyname(host)
        s.port = port
        s.addr = host
        s.sd.connect( ( host, port))

    def vmdsock_write(self,s, header, size) :#s, header, HEADERSIZE
        header.swap_header()
        buf = header.getBinary()
        s.sd.send(buf)
        #return len(buf)

    def vmdsock_read(self,s, ptr, size) :#socket, header, HEADERSIZE=8
        buf = s.sd.recv(size)
        if isinstance(ptr,IMDheader):
            ptr.buffer=buf
            ptr.imdtype=struct.unpack(">i", buf[0:4])[0]
            ptr.length =struct.unpack(">i", buf[4:])[0]
        elif isinstance(ptr,IMDEnergies): 
            ptr.buffer= buf
            ptr.tstep = ntohl(struct.unpack(">i", buf[0:4])[0]) #//!< integer timestep index
            rest=buf[4:]
            ptr.T = struct.unpack("f", rest[0:4])[0]      #//!< Temperature in degrees Kelvin
            rest=rest[4:]            
            ptr.Etot = struct.unpack("f", rest[0:4])[0]      #//!< Total energy, in Kcal/mol
            rest=rest[4:]            
            ptr.Epot = struct.unpack("f", rest[0:4])[0]      #//!< Potential energy, in Kcal/mol
            rest=rest[4:]            
            ptr.Evdw = struct.unpack("f",rest[0:4])[0]      #//!< Van der Waals energy, in Kcal/mol
            rest=rest[4:]            
            ptr.Eelec = struct.unpack("f", rest[0:4])[0]      #//!< Electrostatic energy, in Kcal/mol
            rest=rest[4:]            
            ptr.Ebond = struct.unpack("f", rest[0:4])[0]      #//!< Bond energy, Kcal/mol
            rest=rest[4:]            
            ptr.Eangle = struct.unpack("f", rest[0:4])[0]      #//!< Angle energy, Kcal/mol
            rest=rest[4:]            
            ptr.Edihe = struct.unpack("f", rest[0:4])[0]      #//!< Dihedral energy, Kcal/mol
            rest=rest[4:]    
            ptr.Eimpr = struct.unpack("f", rest[0:4])[0]      #//!< Improper energy, Kcal/mol
        elif isinstance(ptr,numpy.ndarray): 
            self.current_buffer = buf[:]
            rest=buf[:]
            #print "len",int(ptr.shape[0])
            for i in range(int(ptr.shape[0])):
                for j in range(3):
                    #print i,j,struct.unpack("f", rest[0:4])
                    try :
                       ptr[i][j]=float(struct.unpack("f", rest[0:4])[0])
                       rest=rest[4:]
                    except :
                       pass#print i,j, rest[0:4]
            #print "ok"
        #return len(buf)

    def vmdsock_selread(self,vmdsocket, sec):
        pass
        #s = vmdsocket
        #fd_set rfd;
        #struct timeval tv;
        #int rc;
    # 
        #FD_ZERO(&rfd);
        #FD_SET(s->sd, &rfd);
        #memset((void *)&tv, 0, sizeof(struct timeval));
        #tv.tv_sec = sec;
        #do {
        #   rc = select(s->sd+1, &rfd, NULL, NULL, &tv);
        #while (rc < 0 && errno == EINTR);
        #return rc;

    def sendOne(self,data,sender):
        sender.fill(data)
        buf=sender.getBinary()
        res=self.sock.sd.send(buf)
        print "res",res

    def sendFiles(self):
        #first get the pdb/psf
        try :
            from MDTools.md_AtomGroup import Molecule
        except :
            print "no MDTools package, cancel action"
            return
        m = self.m =Molecule(self.pdbFile,self.psfFile)
        s2Send = File2Send()
        b2Send = Bonds2Send()
        #need to send pdb
        print "pdb"
        self.sendOne(m.pdbLines,s2Send)
        #need to send the parmaFile
        o = open(self.paraFile,'r')
        data = o.readlines()
        o.close()
        print "param"
        self.sendOne(data,s2Send)
        #need to send psf file
        print "psf"
        self.sendOne(m.psfAtomsLines,s2Send)
        self.sendOne(m._bonds,b2Send)
        self.sendOne(m._angles,b2Send)
        self.sendOne(m._dihedrals,b2Send)   
        self.sendOne(m._impropers,b2Send)           
        self.sendOne([],s2Send)
        #need then to send fixed atoms
        print "atomsF"
        self.sendOne([],s2Send)
        
    def imd_pause(self):
        header=IMDheader()
        header.fill_header(IMD_PAUSE, 0)
        self.pause = not self.pause
        return (self.imd_writen(self.sock, header, HEADERSIZE) != HEADERSIZE)

    def imd_go(self):
        #swap ?
        header=IMDheader()
        header.fill_header(IMD_GO, 0)
        #print "type", header.imdtype
        header.swap_header()
        print "type", header.imdtype
        return (self.imd_writen(self.sock, header, HEADERSIZE) != HEADERSIZE)

    def imd_send_fcoords(self,n,coords):
        size = HEADERSIZE+12*n
        header=IMDheader()
        header.fill_header(IMD_FCOORDS, n)
        #header.swap_header()
        buf = header.getBinary()
        #need to pack coords (float*3)
        self.current_send_buffer = buf + self.packFloatVectorList(coords)
        self.sock.sd.send(self.current_send_buffer)

    def imd_send_mdcomm(self,n,indices,forces):
        """
        send n forces to apply to n atoms of indices indices
        """
        #rc=0
        size = HEADERSIZE+16*n
        header=IMDheader()
        header.fill_header(IMD_MDCOMM, n)
        header.swap_header()
        buf = header.getBinary()
        #need to pack indices (int) and forces (float*3)
        indiceBuff = self.packIntegerList(indices)
        forcesBuff = self.packFloatVectorList(forces)
        buffer = buf + indiceBuff + forcesBuff
        self.current_send_buffer = buffer
        self.sock.sd.send(buffer)
        #return rc

    def imd_readn(self,s,ptr,n) : #socket, header, HEADERSIZE=8
        #print "readN"#nread=None
        nleft = n
        self.vmdsock_read(s, ptr, nleft)
        return n
        """
        while (nleft > 0) :
            if ((nread = self.vmdsock_read(s, ptr, nleft)) < 0) {
                if (errno == EINTR)
                    nread = 0;         # and call read() again */
                else
                    return -1;
            else if (nread == 0)
                break;               /* EOF */
            nleft -= nread;
            ptr += nread;
        return n-nleft     
        """
  
    def imd_writen(self,s,ptr,n) :
        nleft = n
        nwritten=None
        self.vmdsock_write(s, ptr, nleft)
        del ptr		
        return 0
        """
        while (nleft > 0):
            if ((nwritten = self.vmdsock_write(s, ptr, nleft)) <= 0) :
                if (errno == EINTR):
                    nwritten = 0;
                else
                    return -1
            nleft -= nwritten;
            ptr += nwritten;
        return n
        """

    def imd_recv_handshake(self,s) :
        buf=None
        IMDType=None
        #print "handscheck"
        # Wait up to 5 seconds for the handshake to come
        #if (self.vmdsock_selread(s, 5) != 1) return -1;
        #import time
        #time.sleep(5.)
        # Check to see that a valid handshake was received */
        header = self.imd_recv_header_nolengthswap(s);
        #print "handscheck rcv"
        #print header.imdtype,   IMD_HANDSHAKE  
        if (header.imdtype != IMD_HANDSHAKE) : return -1
        #ok send imd_go
        #print "imd_go"
        self.imd_go()
        #if header.length == IMDVERSION :
        #    if (not self.imd_go(s)) : return 0
        #header.swap_header()
        #if header.length == IMDVERSION :
        #    if (not self.imd_go(s)) : return 0
        return -1;
        """
        # Check its endianness, as well as the IMD version. */
        if (buf == IMDVERSION) {
            if (!imd_go(s)) return 0;
        return -1;
        }
        imd_swap4((char *)&buf, 4);
        if (buf == IMDVERSION) {
           if (!imd_go(s)) return 1;
        }
  
        #/* We failed to determine endianness. */
        return -1; 
        """

   #/* The IMD receive functions */
    def imd_recv_header_nolengthswap(self,socket) :
        header=IMDheader()
        if (self.imd_readn(socket, header, HEADERSIZE) != HEADERSIZE):
            return IMD_IOERROR;
        #header.swap_header()
        return header; 

    def imd_recv_header(self,socket) :
        header=IMDheader()
        if (self.imd_readn(socket, header, HEADERSIZE) != HEADERSIZE):
            return IMD_IOERROR;
        #header.swap_header()
        return header;

    def imd_recv_mdcomm(self, n, indices, forces) :
        if (self.imd_readn(self.sock, indices, 4*n) != 4*n) : return 1
        if (self.imd_readn(self.sock, forces, 12*n) != 12*n) : return 1
        return 0;

    def imd_recv_energies(self, imdEnergies) :
        return (self.imd_readn(self.sock, imdEnergies, 1024)
          != imdEnergies.len);

    def imd_recv_fcoords(self, n, coords) :
        return (self.imd_readn(self.sock, coords, 12*n) != 12*n);

    def getType(self,bytes):
       types="" 
       for i in range(len(bytes)):
           types=types+str(ord(bytes[i]))
       return types
 
    def readInt(self,data):
        if(len(data)<4):
           print "Error: too few bytes for int", data, len(data)
           rest = data
           integer = 0
        else:
           integer = struct.unpack(">i", data[0:4])[0]
           rest    = data[4:]
        return (integer, rest)

    def packIntegerList(self,listeI):
        buffer = ''
        for i in listeI:
            buffer += struct.pack("i", i)
        return buffer

    def packFloatVectorList(self,listeV):
        buffer = ''
        for vector in listeV:
            for j in vector :
                buffer += struct.pack("f", j)
        return buffer

    def start(self,func=None):
        import thread
        self.lock = thread.allocate_lock()
        if self.pause : self.imd_pause()
        thread.start_new(self.listenToImdServer, (func,))

    def mindySend(self):
        from ARViewer import util
        import numpy.oldnumeric as Numeric       
        coords=[]
        for m in self.mol:
            if hasattr(self.vf,'art'):
                M = m.pat.mat_transfo
                vt = []
                vt=util.ApplyMatrix(Numeric.array(m.allAtoms.coords),M,transpose=False)
            else :
                vt = m.allAtoms.coords[:]
            coords.extend(vt)
        self.imd_send_fcoords(len(coords),coords)

    def mindyGet(self):
        from ARViewer import util
        import numpy.oldnumeric as Numeric
        imdheader = self.imd_recv_header(self.sock)
        vmd_length = imdheader.length
        imdtype = imdheader.imdtype
        if imdtype == IMD_FCOORDS:
            #print "recv fcoords ",vmd_length
            test=self.imd_recv_fcoords(vmd_length,self.imd_coords)
            #print self.imd_coords[0]           
            b=0
            n1 = 0
            for i,m in enumerate(self.mol) :
                n1 += len(m.allAtoms.coords)
                try :
                    #should apply the inverse matrix? to get back to the origin 
                    #before going on the marker..
                    #but problem of scaleFactor
                    if hasattr(self.vf,'art'):
                        M = matrix(m.pat.mat_transfo.reshape(4,4))
                        vt=util.ApplyMatrix(Numeric.array(self.imd_coords[b:n1]),
                                            Numeric.array(M.I),transpose=False)
                        #print "update coords but back in CS"
                        #print vt[0]
                        if True in numpy.isnan(vt[0]):
                            vt = map(lambda x: x[0], m.allAtoms._coords)
                        m.allAtoms.updateCoords(vt, self.slot[i])
                        #print m.allAtoms.coords[0]
                    else :
                        m.allAtoms.updateCoords(self.imd_coords[b:n1], self.slot[i])
                except:
                    print "coord update failed"
                b=n1
            from Pmv.moleculeViewer import EditAtomsEvent
            for i,m in enumerate(self.mol) :
                event = EditAtomsEvent('coords', m.allAtoms)
                try :
                    self.vf.dispatchEvent(event)
                except:
                    print "event failed"

    def updateMindy(self):
        from ARViewer import util
        import numpy.oldnumeric as Numeric
        imdheader = self.imd_recv_header(self.sock)
        vmd_length = imdheader.length
        imdtype = imdheader.imdtype
        if imdtype == IMD_FCOORDS:
            print "recv fcoords ",vmd_length
            test=self.imd_recv_fcoords(vmd_length,self.imd_coords)
            print self.imd_coords[0]           
            b=0
            n1 = 0
            for i,m in enumerate(self.mol) :
                n1 += len(m.allAtoms.coords)
                try :
                    #should apply the inverse matrix? to get back to the origin before going on the marker..
                    if hasattr(self.vf,'art'):
                        M = matrix(m.pat.mat_transfo.reshape(4,4))
                        vt=util.ApplyMatrix(Numeric.array(self.imd_coords[b:n1]),numpy.array(M.I))
                        print "update coords but back in CS"
                        print vt[0]
                        m.allAtoms.updateCoords(vt, self.slot[i])
                        print m.allAtoms.coords[0]
                    else :
                        m.allAtoms.updateCoords(self.imd_coords[b:n1], self.slot[i])
                except:
                    print "coord update failed"
                b=n1
            #print m.allAtoms._coords[0]
            #print "ipdate coords events"
            from Pmv.moleculeViewer import EditAtomsEvent
            for i,m in enumerate(self.mol) :
                event = EditAtomsEvent('coords', m.allAtoms)
                try :
                    self.vf.dispatchEvent(event)
                except:
                    print "event failed"
            #here we should update from AR....which is apply the marker transformation
            #one marker per mol...should have some mol.mat_transfo attributes
            #get the maker position transfo
            
            coords=[]
            for m in self.mol:
                if hasattr(self.vf,'art'):
                    M = m.pat.mat_transfo
                    vt = []
                    vt=util.ApplyMatrix(Numeric.array(m.allAtoms.coords),M)
                else :
                    vt = m.allAtoms.coords[:]
                coords.extend(vt)
            self.imd_send_fcoords(self.N,coords)

    def treatProtocol(self,i):
            #import Pmv.hostappInterface.pdb_blender as epmv
            if not self.pause:
                imdheader = self.imd_recv_header(self.sock)
                vmd_length = imdheader.length
                imdtype = imdheader.imdtype
                #print "TYPE ",imdtype
                if imdtype == IMD_ENERGIES:
                    #print "energie"
                    ene=IMDEnergies()
                    test=self.imd_recv_energies(ene)
                    #print ene.tstep,ene.Etot,ene.Epot,ene.Evdw,ene.Epot,ene.Eelec,ene.Eangle
                if imdtype == IMD_MDCOMM:
                    #receive Force and Atom listes
                    #print "mdcom",vmd_length
                    vmd_atoms=numpy.zeros(vmd_length,'i')
                    vmd_forces=numpy.zeros(vmd_length*3,'f')
                    test=self.imd_recv_mdcomm(vmd_length,vmd_atoms,vmd_forces)
                if imdtype == IMD_FCOORDS: #get the coord
                    #vmd_coords=numpy.zeros((vmd_length,3),'f')
                    self.lock.acquire()
                    test=self.imd_recv_fcoords(vmd_length,self.imd_coords)
                    #self.imd_coords[:]=vmd_coords[:]#.copy()
                    self.lock.release()
                    #self.vf.updateIMD
                    #epmv.updateCloudObject("1hvr_cloud",self.imd_coords)
                    #epmv.insertKeys(self.mol.geomContainer.geoms['cpk'],1)
                if self.vf.handler.isinited:
                    if (i % self.ffreq) == 0 :
                        if self.vf.handler.forceType == "move" : 
                            self.imd_send_fcoords(self.vf.handler.N_forces,self.vf.handler.forces_list)
                            print "ok",self.vf.handler.N_forces
                        else : 
                            self.imd_send_mdcomm(self.vf.handler.N_forces, self.vf.handler.atoms_list, self.vf.handler.forces_list)
                if self.mindy:
                    coords=[]
                    for m in self.mol:
                        coords.extend(m.allAtoms.coords)
                    self.imd_send_fcoords(self.N,coords)
        
    def listenToImdServer(self,func):
        i=0
        while (1):
                self.treatProtocol(i)
                i = i + 1

commandList = [
    {'name':'imd', 'cmd':IMD(),
     'gui': None},
    ]

def initModule(viewer):
    for dict in commandList:
#        print 'dict',dict
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
