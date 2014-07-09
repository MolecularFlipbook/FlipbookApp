#########################################################################
#
# Date: Nov. 2001  Author: Michel Sanner
#
# Copyright: Michel Sanner and TSRI
#
#########################################################################

import threading, traceback, time

class ExecutionThread(threading.Thread, threading._Verbose):
    """ class used to schedule a list of nodes in a separate thread.
"""

    def __init__(self, net, nodes):
        threading.Thread.__init__(self, name='scheduler')
        threading._Verbose.__init__(self)
        self.net = net
        self.nodes = nodes
        

    def run(self):
        """run all nodes in the order they appear in the list"""
        net = self.net

        net.execStatusLock.acquire()
        net.execStatus = 'running'
        net.execStatusLock.release()
            
        net.RunLock.acquire()
        t1 = time.time()
        net.runNodes(self.nodes)
        t2 = time.time()

        net.execStatusLock.acquire()
        net.execStatus = 'waiting'
        net.execStatusLock.release()

        #print 'ran in:', t2-t1
        net.RunLock.release()


class AfterExecution(threading.Thread, threading._Verbose):
    """ class used to wait for the end of an execution and call a fucntion
"""

    def __init__(self, net, func=None):
        threading.Thread.__init__(self, name='scheduler')
        self.net = net
        if func is not None:
            assert callable(func)
        self.func = func

        
    def run(self):
        """run all nodes in the order they appear in the list"""
        net = self.net
        # get the lock
        net.RunLock.acquire()
        # release lock and go to sleep until notified
        net.RunLockCond.wait()
        # call the function
        self.func(net)
        net.RunLock.release()
        

        
##  class MTScheduler(threading.Thread, threading._Verbose):
##      """ class used to schedule the multi-threaded execution of the nodes
##      in the subtrees specified by a set of root nodes"""

##      # FIXME we might want to add a limit number of threads to be started
##      # simultaneousley
##      def __init__(self, roots):
##          threading.Thread.__init__(self, name='scheduler')
##          threading._Verbose.__init__(self)
##          self.mtstatelock = threading.RLock()
##          self.waitLock = threading.RLock()
##          self.waitCond = threading.Condition(self.waitLock)
##          self.threadObjects = []
##          ## USED TO FLASH NETWORK ONCE ONLY
##          ## self.allNodes = [] # list of nodes to be run
##          self.roots = roots
##          self.done = 0 # will be set to 1 after all nodes have run
        
##          for node in roots:
##              node.mtstate = 0

##          self.iterateNodes = [] # list to store iterate nodes in substrees
##                                 # with roots self.roots

##      def tagNodes(self, node, iterateSubTree):
##          """tag all nodes in subtree. mtstate will correspond to the number
##          of times a given node was seen in the set of all sub-trees,
##          iterateSubTree is used to tag all nodes below an iterate node"""

##          ## USED TO FLASH NETWORK ONCE ONLY
##  ##          if node.mtstate==0:
##  ##              self.allNodes.append(node)
##  ##              # if we flash the network turn node red
##  ##              if node.editor.flashNetworkWhenRun:
##  ##                  lock = node.editor.RunNodeLock
##  ##                  lock.acquire()
##  ##                  node._tmp_prevCol = node.setColor('red')
##  ##                  lock.release()

##          node.mtstate = node.mtstate + 1
        
##          # if the node has been seen before (from another root) do not
##          # overwrite the fact that it is a child of an iterate node (if it is)
##          if hasattr(node, '_tmp_childOfIterate'):
##              if node._tmp_childOfIterate < iterateSubTree:
##                  node._tmp_childOfIterate = iterateSubTree
##          else:
##              node._tmp_childOfIterate = iterateSubTree

##          #print 'TAG', node.name, node._tmp_childOfIterate
        
##          # has to be imported here because of cross imports with
##          # items and standardNodes
##          from StandardNodes import Iterate
##          if isinstance(node, Iterate):
##              self.iterateNodes.append(node)
##              node._tmp_isIterateNode = 1
##              iterateSubTree = 1

##          #print 'TAG', node.name, node.mtstate
##          if hasattr(node, 'temp_uniqueFloodIndex'):
##              if node.temp_uniqueFloodIndex == self.uniqueFloodIndex:
##                  return
##          node.temp_uniqueFloodIndex = self.uniqueFloodIndex

##          for child in node.children:
##              self.tagNodes(child, iterateSubTree)


##      def startChildren(self, node):
##          """recursively start threaded execution of all non-root nodes"""
##          # FIXME: we should builtin a limit number of threads to be started
##          #        at the same time

##          # children of iterate node need not be scheduled
##          if hasattr(node, '_tmp_isIterateNode'):
##              return
        
##          for child in node.children:
##              # if node not yet associated with a thread object
##              if child._tmp_childOfIterate==1:
##                  #print 'NOT starting node for _tmp_childOfIterate:', child.name
##                  continue
##              if child.mtstate > 0:
##                  #print 'starting node:', child.name
##                  child.thread = NodeThread(child, self, root=0)
##                  self.threadObjects.append(child.thread)
##                  # force mtstate to -1 to prevent creating more thread object
##                  # threadobject's run method checks mtstate==-1 to decide if
##                  # it has to wait for a parent's completion
##                  child.mtstate = -1
##              #else:
##                  #print 'NOT starting node for mtstate:', child.name
##              self.startChildren(child)


##      def deleteTmp(self, node):
##          del node.temp_uniqueFloodIndex
##          if hasattr(node, '_tmp_childOfIterate'):
##              del node._tmp_childOfIterate
##          for child in node.children:
##                  self.deleteTmp(child)


##      def run(self):
##          """ schedule MT execution of all nodes in trees for a given list
##          of root nodes"""

##          if len(self.roots)==0:
##              return
        
##          if self.roots[0].editor.networkRunning==0:
##              return
        
##          self.roots[0].network.RunNetLock.acquire()

##          self.mtstatelock.acquire()
##          # list of ThreadObjects for all children (i.e. non root) nodes
##          # node.mtstate is used to add each child node only once to the list
##          # It is also used in the ThreadNode object.run() method
##          # to decide if a child node has to wait for a given parent
##          self.threadObjects = []

##          # used to prevent endless loop in tagging of nodes involved in
##          # this run
##          self.uniqueFloodIndex = 0

##          # first tag all nodes involved in this run using mtstate
##          for root in self.roots:
##              self.tagNodes(root, 0)
##              self.uniqueFloodIndex = self.uniqueFloodIndex + 1
##              if root.mtstate > 1: # this root is also a child of another root
##                  #print 'REMOVING root', root.name
##                  self.roots.remove(root) # we remove from the list of roots
##              else:
##                  # force mtstate to -1 so all children will wait once started
##                  root.mtstate = -1

##          # walk the subtrees and add a ThreadNode object to the list for
##          # each child node and force mtstate to -1 on all of them
##          for root in self.roots:
##              self.startChildren(root)

##          for node in self.iterateNodes:
##              del node._tmp_isIterateNode
##          for node in self.roots:
##              self.deleteTmp(node)
            
##          # At this point, all nodes involved have mtstate == -1
##          # and self.threadObjects contains a NodeThread for each child node
        
##          # now start all children nodes
##          # they will sit waiting to grab the mtstatelock and then wait for
##          # their parent's condition
##          for to in self.threadObjects:
##              to.start()

##          self.mtstatelock.release()
        
##          # now execute all root nodes and trigger all the executions
##          for root in self.roots:
##              #print 'starting node:', root.name
##              # root=1 means this node will not wait for parents to start
##              # running
##              root.thread = NodeThread(root, self, root=1)
##              root.thread.start()

##          #self.mtstatelock.release()
        
##          # has to be imported here because of cross imports with
##          # items and standardNodes
##          from StandardNodes import Iterate

##          # lock run lock until this run is completed
##          self.waitLock.acquire()
##          while 1:
##              self.done = 1
##              # check if there is a thread started by an MTScheduler object
##              # (they can be recognized because their name starts with
##              # the '_&&_mtScheduler_&&_thread_' string).
##              # if we find a thread with such a name which does not
##              # correspond to an iterate node we have to wait.
##              # else, all children started have run and we can release the
##              # lock that was set for this run and give another MTscheduler
##              # (for instance started by an iterate node) to grab it and start
##              # running.
##              # 
##              for thread in threading.enumerate():
##                  # if this thread was started by an MTscheduler
##                  if thread.getName()[:26]=='_&&_mtScheduler_&&_thread_':
##                      # if it is not an iterate node  and it is not
##                      # a child of an iterate node that is scheduled
##                      # we have to wait.
##                      if not isinstance(thread.node, Iterate):
##                          self.done = 0
##                          break
##              if self.done==1:
##                  net = self.roots[0].network
##                  net.release()
##                  net.iterateLock.acquire()
##                  net.iterateCond.notifyAll() # wakeup all iterate nodes
##                  net.iterateLock.release()
##                  break
##              else:
##                  # self.waitCond is notified after completed of each thread
##                  # corresponding to a node.
##                  # We check every second but this wakes up every time a node
##                  # is done running anyways. We still need the timeout of
##                  # 1 second in case we miss a notifocation or an iterate node
##                  # is still an active thread but not done running. (not 100%
##                  # sure we need the timeout)
##                  self.waitCond.wait(1)

##          ## USED TO FLASH NETWORK ONCE ONLY
##          # if we flash the network only once go back to previous color
##  ##          if self.roots[0].editor.flashNetworkWhenRun:
##  ##              for node in self.allNodes: 
##  ##                  lock = node.editor.RunNodeLock
##  ##                  lock.acquire()
##  ##                  node._tmp_prevCol = node.setColor(node._tmp_prevCol)
##  ##                  del node._tmp_prevCol
##  ##                  lock.release()

##          self.waitLock.release()



##  class NodeThread(threading.Thread):

##      def __init__(self, node, scheduler, root=0):
##          threading.Thread.__init__(self, name='_&&_mtScheduler_&&_thread_'+node.name)#, verbose=1)
##          self.node = node
##          self.scheduler = scheduler
##          self.root = root
        

##      def run(self):
##          node = self.node
##          #self._note('running %s', node.name)

##          # acquire global lock (only one node can run at any time)
##          lock = node.network.RunNodeLock
##          lock.acquire()
##          #print 'start running', node.name

##          # has to be imported here because of cross imports with
##          # items and standardNodes
##          from StandardNodes import Iterate

##          try:
##              # make sure all parents are done
##              if self.root==0:
##                  for parentNode in node.parents:
##                      if isinstance(parentNode, Iterate):
##                          continue
##                      self.scheduler.mtstatelock.acquire()
##                      if parentNode.mtstate == -1:
##                          self.scheduler.mtstatelock.release()
##                          parentNode.condition.wait()
##                          #print node.name, 'wake up sent by', parentNode.name
##                      else:
##                          self.scheduler.mtstatelock.release()
                            
##              if node.editor.flashNodesWhenRun:
##                  col = node.setColor('red')
##                  #node.editor.update_idletasks()

##              # once all the parents are done we can run this node
##              #print 'running', node.name
##              status = node.computeFunction()
            
##              if node.editor.flashNodesWhenRun:
##                  if col=='#557700': # after successfull run of failed node
##                      col = node.colorBeforeFail
##                  node.setColor(col)
            
##          except:
##              print
##              print "***********************************************************"
##              print "*** ERROR while executing node: ", node.name
##              print "***********************************************************"
##              traceback.print_exc()
##              if node.editor.flashNodesWhenRun:
##                  if col != '#557700':
##                      node.colorBeforeFail = col
##                  node.setColor('#557700')

##          self.scheduler.mtstatelock.acquire()
##          node.mtstate = 0 # done
##          #print 'mtstate', node.name, node.mtstate
##          self.scheduler.mtstatelock.release()
                
##          # once this node has run we want to tell all threads of
##          # children nodes
##          #print 'notify from', node.name
##          node.condition.notifyAll()

##          #print 'Thread: acquireing waitLock by', node.name
##          self.scheduler.waitLock.acquire()
##          self.scheduler.waitCond.notify()
##          #print 'Thread: releasinging waitLock by', node.name
##          self.scheduler.waitLock.release()
        
##          # finally release the lock
##          #print 'release global lock', node.name
##          del node.thread
##          lock.release()


##  class Queue(threading._Verbose):

##      def __init__(self, limit):
##          threading._Verbose.__init__(self)
##          self.mon = threading.RLock()
##          self.rc = threading.Condition(self.mon)
##          self.wc = threading.Condition(self.mon)
##          self.limit = limit
##          self.queue = [] # list of nodes in trees except for root nodes
##          self.roots = [] # list of nodes at root of trees


##      def printQueue(self):
##          self.mon.acquire()
##          self._note('queue :************************')
##          for entry in self.queue:
##              self._note("%s", entry.name)
##          self.mon.release()


##      def put(self, item):
##          self.mon.acquire()
##          # we only add nodes to the queue if they are not queued or scheduled
##          # if a node is running, it needs to be added tot he queue in order to
##          # run again with the new input
##          if item.mtstate is not 0:
##              print '-------- already in queue or schedule', item.name
##              self.mon.release()
##              return
##          while len(self.queue) >= self.limit:
##              #self._note("put(%s): queue full", item)
##              self.wc.wait()
##          print 'queued ',item.name
##          #import traceback
##          #print traceback.print_stack()
##          self.queue.append(item)
##          item.mtstate = 3 # inQueue
##          #self._note("put(%s): appended, length now %d",
##          #           item, len(self.queue))
##          self.rc.notify()
##          self.mon.release()

##      def get(self):
##          self.mon.acquire()
##          while not self.queue:
##              #self._note("get(): queue empty")
##              print '************************ queue empty'
##              self.rc.wait()
##          item = self.queue[0]
##          print 'scheduled ',item.name
##          item.mtstate = 2 # scheduled
##          del self.queue[0]
##          #self._note("get(): got %s, %d left", item, len(self.queue))
##          self.wc.notify()
##          self.mon.release()
##          return item

        
##  # objects reading the queue
##  class QueueHandler(threading.Thread):

##      def __init__(self, queue, verbose=None):
##          threading.Thread.__init__(self, name="handler", verbose=verbose)
##          self.queue = queue
##          self.finish = 1

        
##      def stop(self):
##          self._Thread__started = 0
##          self.finish = 1

        
##      def run(self):
##          self.finish = 0
##          while not self.finish:
##              node = self.queue.get()
##              if node.frozen:
##                  continue
##              #if __debug__:
##              #    self._note('running %s', node.name)
##              node.thread = NodeThread(node, self.queue)
##              node.thread.start()

            
#def _test():
#    import time
#    _sleep = time.sleep
#
#    NP = 3
#    QL = 4
#    NI = 5
#
#    Q = Queue(QL)
#    P = []
#    C = ConsumerThread(Q, NI*NP)
#    C.start()
#    for i in range(NP):
#        t = ProducerThread(Q, NI)
#        t.setName("Producer-%d" % (i+1))
#        P.append(t)
#        t.start()
#        _sleep(1.)
#    #for t in P:
#    #    t.join()
#    #C.join()
#
#if __name__ == '__main__':
#    _test()
#       
