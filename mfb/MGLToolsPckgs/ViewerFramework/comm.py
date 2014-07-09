#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/ViewerFramework/comm.py,v 1.6 2009/03/24 18:11:18 sanner Exp $
#
# $Id: comm.py,v 1.6 2009/03/24 18:11:18 sanner Exp $
#


"""
COMM module

Author: Michel F. Sanner
Date: Oct 11 2000

This module implements the Comm class that provides bi-directional communication over sockets. The Comm object provides server functionality, accepting connections from multiple clients (each client is handled by a separate thread).  the comm object also provides client side functionality, allowing a Comm object to connect to an existing server.

A - Server side
After a Comm object has been created, the startServer method can be called to
create a socket (self.serverSocket) and find a free port to which this socket
will be bound. The port is stored in self.port

By calling the acceptClients(func, maxConnections) one can allow the server to accept connection from clients. 'func' will be called for each message sreceived from clients. FIXME: calling func should probably set a lock.
acceptClients works in its own thread. When a client connects, a new thread is started to handle input from this client (listenToClient()) and the client is added to the Comm's clients dictionary.

The client dictionary uses the client's name as a key and stores the socket and the address created by accept.

hangupClient(name, client) can be called to terminate a connection with a specific client.

sendToClients(message) can be used to send a string to all connected clients

B - Client side

A comm object can be used to connect to a running server using the connectToServer(self, host, port, func). host cane be a host name or an IP address (as string). If the connection is successful a new thread is started to listen to the server and 'func' will be called with all messages comming from that server.

disconnectFromServer(self, clientSocket) can be called to disconnect fropm a server. 'clientSocket' can be a socket or a 
"""
import sys, time
from socket import *
import thread, types

class Comm:

    def __init__(self):
        self.verbose = 1   # set to 0 to get rid of printing

        # server related members
        self.clients = {}  # dictionary of clients,
                           # key is the host name+address bound to the socket
                           # on the other end of the connection
                           # value is (conn, addr) tuple
        self.port = None   # port used by server to accept connections
        self.serverSocket = None  # socket used by server to accpet conenctions
        self.maxConnections = 5   # maximum number of conenctions allowed

        # client related members
        self.serverSockets = {}  # dictionary of servers, key is the server's
                                 #  name, value is the socket created for this
                                 # connection

    def getPort(self, socket, base=50000):
        """find the first free port above base"""
        port = base
        while(1):
            try:
                socket.bind( ( '', port))
                return port
            except:
                import traceback
                traceback.print_exc()
                port = port + 1
                print port
    ##
    ## server side
    def startServer(self, port=None):
        self.serverSocket = s = socket(AF_INET, SOCK_STREAM)
        if port is None:
            self.port = self.getPort(s)
        else:
            self.port = port

    def acceptClients(self, func, maxConnections=5):
        self.maxConnections = maxConnections
        self.serverSocket.listen(maxConnections)
        if self.verbose:
            print "server ready, listening to port ", self.port
        while 1:
            conn, addr = self.serverSocket.accept()
            name = gethostbyaddr(conn.getpeername()[0])[0] + str(addr[1])
            self.clients[name] = ( conn, addr )
            if self.verbose:
                print 'Connected by', name, '\n'
            thread.start_new(self.listenToClient, (name, conn, func))
            
    def listenToClient(self, name, client, func):
        while (1):
            data = client.recv(1024)
            if data=='':
                if self.verbose:
                    print 'Connection closed by client'
                self.hangupClient(client)
                return

            MSGLEN = int(data)
            #print 'FFFFF  client receving', MSGLEN
            msg = ''
            while len(msg) < MSGLEN:
                chunk = client.recv(MSGLEN-len(msg))
                if chunk == '':
                    if self.verbose:
                        print 'Connection closed by client'
                    self.hangupClient(client)
                    return
                msg = msg + chunk
            #print 'client received', len(msg)
            func(name, msg)

    def hangupClient(self, client):
        if type(client) == types.StringType:
            cl = self.clients[client][0]
        else:
            cl = client
            client = None
            for key, value in self.clients.items():
                if value[0]==cl:
                    client = key
                    break
            if client is None:
                raise ValueError, "client not found"
            
        cl.close()
        del self.clients[client]
        
    def sendToClients(self, message):
        """send a messaqe to all clients"""
        #print 'server sending to client', message
        for c in self.clients.values():
            print 'server sending', len(message), '%020d'%len(message)
            c[0].send('%020d'%len(message))
            c[0].send(message)
        

    def getClients(self):
        """send a messaqe to all clients"""
        return self.clients.keys()

    ##
    ## client side
    def connectToServer(self, host, port, func):
        """become a client of a server specified using host and port,
        func will be called to handle messages from server
        """
        host = gethostbyname(host)
        serverSocket = socket(AF_INET, SOCK_STREAM)
        serverSocket.connect( ( host, port))
        name = gethostbyaddr(serverSocket.getpeername()[0])[0]+str(port)
        self.serverSockets[name] = serverSocket
        thread.start_new(self.listenToServer, (name, serverSocket, func))

        
    def listenToServer(self, name, client, func):
        while (1):
            data = client.recv(20)
            print 'client receives', data
            MSGLEN = int(data)
            #print 'FFFFF  client receving', MSGLEN
            msg = ''
            while len(msg) < MSGLEN:
                chunk = client.recv(MSGLEN-len(msg))
                if chunk == '':
                    if self.verbose:
                        print 'Connection closed by server'
                        self.disconnectFromServer(client)
                        return
                msg = msg + chunk
            #print 'client received', len(msg)
            func(name, msg)


    def disconnectFromServer(self, server):
        if type(server) == types.StringType:
            cl = self.serverSockets[server]
        else:
            cl = server
            server = None
            for key, values in self.serverSockets.items():
                if values==cl:
                    server = key
                    break
            if server is None:
                raise ValueError, "server not found"
        cl.shutdown(2)
        cl.close()
        del self.serverSockets[server]

    def getServers(self):
        """send a messaqe to all servers"""
        return self.serverSockets.keys()


if __name__ == '__main__':
    com = Comm()
    com.startServer()
    #com.acceptClients()

    def foo1(client, data):
        print 'client %s sent> %s'%(client,data)

    thread.start_new(com.acceptClients, (foo1,))

    def foo(server, data):
        print 'server %s sent> %s'%(server,data)

    #com.connectToServer('', 50008, foo)
