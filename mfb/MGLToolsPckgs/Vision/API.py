#########################################################################
#
# Date: May 2004  Authors: Daniel Stoffler, Michel Sanner
#
#       stoffler@scripps.edu
#       sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Daniel Stoffler, Michel Sanner, and TSRI
#
#########################################################################

import warnings

class VisionInterface:
    """This class provides a mechanism to interface between Vision and
    another application (for example, it allows Pmv to add nodes to Vision)
    Objects created in the application (e.g. in Pmv) are stored in the
    self.objects list. Here we store the object, a name to be used for the
    Vision node, and optional keywords if the Vision node needs them. For
    example the kw 'constrkw' is used in Vision for saving/restoring properly.
    In addition, there is a lookup table to describe the connection between
    an object in the application (such as a molecule) and the corresponding
    Vision node.

    Adding an object to this interface using the add() method will
    automatically add the node to Vision -- if Vision is running at this
    moment. If Vision is not running, we still add the object to our list and
    in the command that starts Vision inside the application (e.g. in Pmv this
    would be 'visionCommands') a mechanism has to be implemented to loop over
    the objects in our list and add them to Vision -- that's 2 lines of code:
    see visionCommands!"""


    def __init__(self, ed=None, lib=None):
        self.ed = ed           # handle to Vision
        self.lib = lib         # handle to the Vision library
        self.objects = []      # list of objects to be added as nodes to Vision
                               # this contains tuples of (object, name, kw)

        self.lookup = {}       # lookup table that defines what node class,
                               # which category. Will be used to assign a
                               # Vision node to the object
                               # key: the object
                               # value: a tuple with the node class and
                               # category name

    def add(self, obj, name, kw=None):
        """Add an object to this API. This will automatically add a node
        to a Vision library if Vision is running.
        - obj: the appliaction object (such as a molecule)
        - name: name to be used for the Vision node
        - kw: optional Vision node constructor keywords.
        """
        if kw is None:
            kw = {}

        # find out which Vision node corresponds to this object, based on our
        # lookup table
        if obj.__class__ in self.lookup.keys():
            # add to our list of objects
            self.objects.append( (obj, name, kw) )
            
            # add node to Visual Programming Environment library if this exists
            if self.ed is not None and self.lib is not None:
                self.addNodeToLibrary(obj, name, kw)
            return
        else: # the class was not found, try to see if a base class is there
            for k in self.lookup.keys():
                if isinstance(obj, k):
                    # add to our list of objects
                    self.objects.append( (obj, name, kw) )
            
                    # add node to Visual Programming Environment library if this exists
                    if self.ed is not None and self.lib is not None:
                        self.addNodeToLibrary(obj, name, kw)
                    return
        import traceback
        traceback.print_exc()
        warnings.warn(
            "ERROR: Object not found in lookup. Cannot create node")


    def remove(self, obj):
        """Delete an object from the list of objects. This also deletes the
        node proxy in the category and all node instances in all networks."""
        
        # is the object in our list of objects?
        found = None
        for i in range(len(self.objects)):
            if self.objects[i][0] == obj:
                found = self.objects[i][0]
                # delete from our list of objects
                del self.objects[i]
                break

        if found is None:
            return

        node = self.lookup[found.__class__]['node']
        cat = self.lookup[found.__class__]['category']

        # if Vision was not started yet, return here
        if self.ed is None:
            return

        ## STEP 1) Delete node proxy in category

        # note: here, the 'node' is not a node instance, but a class,
        # therefore we can just pass the object
        self.lib.deleteNodeFromCategoryFrame(cat, node, found.name)

        ## STEP 2) Delete all instances of this node in all networks
        for net in self.ed.networks.values():
            for n in net.nodes:
                if n.__class__ == node:
                    net.deleteNodes([n])
        

    def setEditor(self, ed):
        """helper method to get a handle to Vision"""
        from Vision.VPE import VisualProgramingEnvironment
        assert isinstance(ed, VisualProgramingEnvironment)
        self.ed = ed


    def setLibrary(self, lib):
        """helper method to get a handle to a Vision library"""
        from Vision.VPE import NodeLibrary
        assert isinstance(lib, NodeLibrary)
        self.lib = lib


    def addToLookup(self, obj, node, cat):
        """Add a class instance of a Vision node to this list"""
        self.lookup[obj] = {'node':node, 'category':cat}



    def addNodeToLibrary(self, obj, name, kw=None):
        """add node to Visual Programming Environment library"""

        if kw is None:
            kw = {}

        if obj.__class__ in self.lookup.keys():
            o = self.lookup[obj.__class__]
        else:
            for k in self.lookup.keys():
                if isinstance(obj, k):
                    o = self.lookup[k]
                    break
        node     = o['node']
        cat      = o['category']

        self.lib.addNode(node, name, cat, (), kw)

        # if a node is added to an empty category, we resize all
        if len(self.lib.libraryDescr[cat]['nodes']) == 1:
            self.lib.resizeCategories()
        

 
