#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

# $Header: /opt/cvs/python/packages/share1.5/ViewerFramework/picker.py,v 1.5 2004/06/01 22:03:54 sanner Exp $
#
# $Id: picker.py,v 1.5 2004/06/01 22:03:54 sanner Exp $
#

#
"""
implement classes for object pickers in viewer.

Pickers support, GUI and non-GUI versions. Picking can be done in the viewer's
camera. A picker can terminate automatically when a given number of objects
has been picked. Exact number of objects can be enforced.
Callback functions can be invoked after each picking operation or after the
picker finishes.
The picking level can be set to 'vertices' or 'parts'.
Duplicate checks is performed by default.

The base class Picker has to be sub-classed by speciliazed classes implementing
methods such as:
    getObjects(self, pick)
    def allChoices(self)
    def buildInputFormDescr(self)
    def updateGUI(self)

When a gui is present, each sub-class has to implement the updateGUI method
that will reflect the action of picking an object.
if the method "allChoices" returns a non-empty list, a list chooser from which 
objects can be picked is added. 
"""

##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
import Tkinter, time, types

class Picker:
    """Base class for picker objects"""

    def __init__(self, vf, numberOfObjects=None, gui=1, immediate=0,
                 callbacks=[], mode='exact',
                 checkDuplicates=1, disableOtherPickingFunctions=0):
        """picker constructor,
        numberOfObjects: None or positive integer. if None call stop() to end
        gui: 0/1 for display GUI
        immediate: 1/0. If 1 call callback function after each pick else call
                   after picker's termination
        callbacks: list of functions to be called with a list of objects as arg
        mode: 'exact' or 'atLeast'. If exact only pick operation that do not
               exceed the numberOfObject are considered
        checkDuplicates: 0/1. Remove duplicate entries form list of objects
        """
        
        self.vf = vf # viewer application
        self.numberOfObjects = numberOfObjects # required number of objects
        self.immediate = immediate
        self.gui = gui # show GUI
        self.mode = mode
        self.checkDuplicates = checkDuplicates
        l = len(callbacks)
        self.callbacks = callbacks
        self.disableOtherPickingFunctions = disableOtherPickingFunctions
	self.clear() #this set-up self.objects to be the right thing
        self.saveCallBackList = None
        if self.gui and self.vf.hasGui:
            self.ifd=self.buildInputFormDescr()
            self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)


    def go(self, modal=0, level='vertices'):
        """return only after the specified number of objects have been picked
  level: 'vertices' or 'parts', Picking level to be used
  """
        assert level in ['vertices', 'parts']
        self.pickLevel = level
        vi = self.vf.GUI.VIEWER
        vi.pickLevel = self.pickLevel
        self.modal = modal

        if self.disableOtherPickingFunctions:
            self.saveCallBackList = vi.SetPickingCallback(self.pickObject_cb)
        else:
            vi.AddPickingCallback(self.pickObject_cb)

        if modal:
            while len(self.objects) < self.numberOfObjects:
                self.vf.GUI.VIEWER.master.update()
                time.sleep(0.001)
            if self.disableOtherPickingFunctions:
                vi.SetPickingCallback(self.saveCallBackList)
            elif self.pickObject_cb in vi.pickingFunctions:
                vi.RemovePickingCallback(self.pickObject_cb)

            # FIXME
            # hack to go back to default mode. This raise the problem that we
            # cannot have a vertices picker and a part picker at the same time
            vi.pickLevel = 'vertices'
            return self.objects


    def stop(self, event=None):

        if not self.immediate:
            self.callCallback(self.objects)
            
        vi = self.vf.GUI.VIEWER
        if self.disableOtherPickingFunctions:
            vi.SetPickingCallback(self.saveCallBackList)
            self.saveCallBackList = None
        else:
            vi.RemovePickingCallback(self.pickObject_cb)
        if hasattr(self, 'form'):
            self.form.destroy()

        # FIXME see remark in go()
        vi.pickLevel = 'vertices'
        

    def clear(self):
        """clear list of selected objects"""
        self.objects = []


    def removeAlreadySelected(self, objects):
        """remove for objects the ones already in self.objects"""
        l = []
        for o in objects:
            if not o in self.objects:
                l.append(o)
        return l
        

    def pickObject_cb(self, pick): 
        """handle a picking operation"""

        #print 'in Picker pickObject_cb'
        objects = self.getObjects(pick)
        #print objects
        
        if objects:
            if self.gui: self.updateGUI(objects)

            # remove objects that are aleady in self.objects
            if self.checkDuplicates:
                objects = self.removeAlreadySelected(objects)

            # make sure we do not select too many objects
            if self.mode=='exact':
                l = len(objects)+len(self.objects)
                if self.numberOfObjects is not None and \
                   l > self.numberOfObjects:
                    print "WARNING: this operation would select %d objects while %d are needed\n" % (l,self.numberOfObjects)
                    return

            # add te new objects to already selected ones
            self.objects = self.objects + objects

            # call callbacks with new objects (only in immediate mode)
            if self.immediate:
                self.callCallback(objects)

            # check whether obect count has been reached
            if self.numberOfObjects is not None:
                if len(self.objects)>=self.numberOfObjects:
                    self.stop()


    def buildInputFormDescr(self):
        ifd = InputFormDescr()
        all = self.allChoices()
        if len(all)>0:
            ifd.append({'widgetType':'ListChooser',
                             'name':'AllObjects',
                             'entries':all,
                             'title':'All objects',
                             'wcfg':{'mode':'multiple'},
                             })
        if self.numberOfObjects==None:
            ifd.append({'widgetType':Tkinter.Button,
                             'wcfg':{'text':'Done'},
                             'command': self.stop})
        return ifd


    def getSelectedObjects(self):
        return self.objects


    def callCallback(self, objects):
        for f in self.callbacks:
            apply(f, ( (objects), ) )
        
            
    def addCallback(self, callback):
	"""Add a callback function"""

	assert callable(callback)
	# Here we should also check that callback has exactly 1 argument

        self.callbacks.append(callback)


    def removeCallback(self, func):
	"""Delete function func from the list of callbacks for eventType"""

        self.callbacks.remove(callback)


    def getObjects(self, pick):
        """to be implemented by sub-class"""
        # has to return a list (or equivalent) of unique objects
        pass


    def updateGUI(self):
        """to be implemented by sub-class"""
        pass
    

    def allChoices(self):
        return []


    
class GeomPicker(Picker):

    def getObjects(self, pick):
        return pick.hits.keys()

