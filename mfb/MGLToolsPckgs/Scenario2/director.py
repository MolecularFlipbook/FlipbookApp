##
##  Author Michel F. Sanner May 2007
##

from time import sleep
import warnings, weakref, numpy

from actor import Actor
from Scenario2 import MaxKF

try:
    from DejaVu.scenarioInterface.animations import RedrawActor
    foundDejaVu = True
except ImportError:
    foundDejaVu = False
    
## from SimPy.Simulation import Process, initialize, activate, simulate, now, hold
from Scenario2.multipleActorsActions import MultipleActorsActions, MAAGroup, ActorProcess


## class Director(MultipleActorsActions):
##     """
## """
##     def __init__(self):

##         MultipleActorsActions.__init__(self)

##         self.currentFrame = 0
##         self.endFrame = 0

##         self.gui = None # will be set when a gui is created
##         self.recordingActors = []  # list of actors with recording flag on
##            # i.e. actor.recording!='stopped'
##         # FIXME should have a set and delete method to check type etc
##         self.afterAnimation = [] # list of functions to be called after
##                                  # play ends
##         self.scenarios = {}
##         self.autotrackDict = {}
##         self.redrawActor = None
##         self.moveForward = True
##         self.maxFrame = 0
##         self.needsRedraw = False
        

##     def addScenario(self, name, scenario):
##         self.scenarios[name] = scenario


##     def start(self, setDirector = True, title = None):
##         if self.gui is None:
##             gui = DirectorGUI(self, title = title)
##             gui.root.protocol('WM_DELETE_WINDOW', gui.root.withdraw)
##             self.gui = gui
##             if setDirector:
##                 for scenario in self.scenarios.values():
##                     scenario.setDirector()
##         else:
##             if title:
##                 oldtitle = self.gui.root.title()
##                 if oldtitle != title:
##                    self.gui.root.title(title) 
##             self.gui.root.deiconify()


## ##     def deleteActor(self, actor):
## ##         # delete this actor and all its actions
## ##         name = actor.name
## ##         if self.gui:
## ##             self.gui.deleteActors()
## ##         if actor in self.actors:
## ##             self.actors.remove(actor)
## ##         if hasattr(actor, "guiVar"):
## ##             if actor.guiVar:
## ##                 actor.guiVar.set(0)
## ##         #if hasattr(actor.object, "animatedProperties"):
## ##         #    del actor.object.animatedProperties[name]
## ##         if hasattr(actor.scenario, "animatedProperties"):
## ##             del actor.scenario.animatedProperties[name]
## ##         if self.gui:
## ##             if self.gui.selectedFrames.has_key(name):
## ##                 self.gui.selectedFrames.pop(name)
## ##             if self.gui.autotracking:
## ##                 if self.autotrackDict.has_key(name):
## ##                     self.autotrackDict.pop(name)
## ##                     # this will update the dictioanary with a new "clean"
## ##                     # version of the deleted actor.
## ##                     self.autotrackDict.update(actor.scenario.getNewActors())
                
## ##             self.gui.drawActors()
## ##         ####################FIX THIS ###########
## ##         if len(actor.kfSetId):
## ##             for kf, setId in actor.kfSetId.items():
## ##                 kfset = self.gui.kfSets.get(setId)
## ##                 if kfset:
## ##                     kfset.removeKeyFrame(name, kf)
## ##                     if kfset.getNumberOfFrames() == 1:
## ##                         # remove the set
## ##                         self.gui.removeKFSet(kfset)

        

##     def getLastFrame(self):
##         # returns number of frames in the simulation
##         return self.endFrame

    
##     def getLastFrameWithChange(self, actors = None):
##         # returns the last frame in which a value changes
##         if not actors:
##             actors = self.actors
##         last = None
##         for actor in actors:
##             #if actor.isFullRange(): continue
##             if actor.visible:
##                 lastFrame = actor.getLastKeyFrame()
##                 if last is None:
##                     last = lastFrame
##                 else:
##                     if lastFrame.pos > last.pos:
##                         last = lastFrame
##         return last


##     def updateEndFrame(self, end, updateGUI=1):
##         if not end:
##             return
        
##         if end > self.endFrame:
##             self.endFrame = end
##             if self.gui and updateGUI:
##                 self.gui.setDuration(end)

##         else:
##             last = self.getLastFrameWithChange()
##             if last is not None:
##                 last = last.pos
##             else:
##                 last = 0
##             if end < last+10 : # when recording we want to make sure there are frame to the right
##                 self.endFrame = last +10
##             else:
##                 self.endFrame = end
##             if self.gui and updateGUI:
##                 self.gui.setDuration(self.endFrame)


##     def run(self, forward=True):
##         if len(self.actors)==0:
##             #print "no actors"
##             return
##         initialize()
##         redraw = self.redrawActor
##         start = 0
##         #end = self.endFrame
##         self.maxFrame = 0
##         maxFrame = self.getLastFrameWithChange()
##         if maxFrame is not None:
##             self.maxFrame = maxFrame.pos

##         end = self.maxFrame
##         gui = self.gui
##         if gui:
##             if not (gui.startFrame == 0 and gui.stopFrame == 1):
##                 start = gui.startFrame
##                 end = gui.stopFrame
##                 self.maxFrame = end + start
##         self.moveForward = forward
##         if redraw:
##             redraw.object.stopAutoRedraw()
##             proc = RedrawActorProcess(redraw)
##             activate(proc, proc.execute(), at=start, prior=True)
##             #print 'activated redraw', 
##         for actor in self.actors:
##             if actor.name != "redraw":
##                 proc = ActorProcess(actor)
##                 activate(proc, proc.execute(), at=start, prior=True)
##                 #print 'activated ', actor.name, action
##         #print 'simulate', self.endFrame
##         simulate(until=end)
##         #self.currentFrame = self.endFrame
##         if forward:
##             #self.currentFrame = self.endFrame
##             self.currentFrame = end
##         else:
##            self.currentFrame = start
##         # call callback after animation completes
##         for f in self.afterAnimation:
##             f()
##         if self.redrawActor:
##             vi = self.redrawActor.object
##             vi.startAutoRedraw()


##     def setValuesAt(self, frame, actor = None):

##         if actor:
##             actors = [actor]
##         else:
##             actors = self.actors

##         for actor in actors:
##             actions = actor.actions
##             if actor.name != "redraw" and  actor.playing:
##                 if len(actor.valueGenerators):
##                     value = actions.getValueAt(frame)

##                     if value != 'Nothing There':
## #                        if redraw:
## #                            self.needsRedraw = True
##                         actor.setValue(value)
                                
## #        if redraw:
## #            redraw.setValue()

##     def gotoFrame(self, frame, set=True):
##         if frame<0:
##             frame = 0
##         elif frame>self.endFrame:
##             frame = self.endFrame
##         if frame==self.currentFrame:
##             return
##         self.currentFrame = frame
##         if set:
##             self.setValuesAt(frame)
##         if self.gui:
##             self.gui.placeTimeCursor(frame)
            

## ##     def createActorFromData(self, obj, propname, scenarioInterface,filename, fields,
## ##                             data, start = 0, end=-1):
## ##         # Create a special actor whose valueGenerator returns values from a data 
## ##         # sequence such as list ar numpy array, This data is read from a file (.adat)->
## ##         # see actor.py/adatFileParser

## ##         # obj - animatable object
## ##         # propname - the object's animated property name
## ##         # scenarioInterface - scenario interface that is n self.scenarios and "knows" how
## ##         # to create a regular actor for this object (i.e has createActor() method).
## ##         # start - first keyframe of the actor
## ##         # end - last keyframe of the actor ( if end == -1, then the number of frames between
## ##         # first and last keyframes is len(data)-1, or one data step per each keyframe).

## ##         if data is None:
## ##             print "createActorFromData: data is None"
## ##             return

## ##         assert scenarioInterface in self.scenarios.values()
## ##         actor = None
## ##         if data is not None:
## ##             assert type(data).__name__ in ('ndarray', 'list')
## ##             nsteps = len(data)
## ##             firstVal = data[0]
## ##             lastVal =  data[nsteps-1]
## ##             #print filename, len(data), data[0], propname
## ##             # create an actor with ReadDataInterpolator valuegenerator
## ##             #try:

## ##             # this will create file actor with two keyframes : "0" and "nsteps-1" 
## ##             actor = scenarioInterface.createActor(obj, propname, check=False,
## ##                                                   addToDirector=False,
## ##                                                   actorData = (filename, data))
## ##             actor.datafields = fields
## ##             #except:
## ##             #    warnings.warn("Failed to create file actor %s" % propname)
## ##             #    return None
## ##             if actor:
## ##                 self.addActor(actor)
## ##                 #print "start=", start, "end=", end, "nsteps=", nsteps
## ##                 if end == -1:
## ##                     end = start + nsteps - 1
## ##                 if end != nsteps-1:
## ##                     if self.gui:
## ##                         #this will move "nsteps-1" keyframe  to "end" keyframe 
## ##                         self.gui.selectKeyFrame_cb(actor, nsteps-1, newframe=end)
## ##                 if start != 0:
## ##                     if self.gui:
## ##                         # this will move "0" keyframe to "start" keyframe
## ##                         self.gui.selectKeyFrame_cb(actor,0,newframe=start) 
                    
## ##         return actor
            

from mglutil.events import EventHandler
from Scenario2.events import AddMAAEvent, RemoveMAAEvent, CurrentFrameEvent,\
     PlayerStartEvent, PlayerStopEvent

from DejaVu.states import setRendering, setOrientation

class MAADirector(EventHandler):
    """
    an MAADirector object contains a list of MultipleActorsActions (MAA) objects
    and their corresponding positions, i.e. absolute frame number in the
    animation.

    the (maas, position) tuples are stored in the .maas attribute

    attributes:

    .currentFrame: current frame in the animation
    .maxFrame:
    .endFrame: frame after the last frame for which there is a value
    
    Methods:

    bool <- addMAAat(self, maa, position)
    maa, index <- removeMAA(maa, position)
    None <- play(self, fromPos=0, toPos=None, forward=True, callback=None)
    None <- def setValuesAt(self, frame)
    string <- getMAASourceCode(self, variable, indent=0, showwarning=True)
    """

    def __init__(self):

        EventHandler.__init__(self)
        self.maas = [] # will hold the list of [MAA, position] pairs
        self.currentFrame = 0
        self.endFrame = 0  # frame after the last frame for which there is a value
        self.maxFrame = 0

        # these are used internally
        self.moveForward = True # truwe when palying forward
        self.needsRedraw = False
        self.redrawActors = {} # {Viewer Object: RedrawActor}


    def addMAAat(self, maa, position, check=True):
        """
        adds an MAA object to be played at a given position.

        bool <- addMAAat(maa, position)
        
        the MAA can only be added if none of its actors overlaps with the same
        actor in an existing MAA. Returns True is maa was added.

        Event:
            generates a AddMAA event
        """
        if not isinstance(maa, MultipleActorsActions) and not isinstance(maa, MAAGroup):
            raise TypeError, "in addMaaat() maa must be an instance of MultipleActorsActions or MAAGroup"
        #assert isinstance(maa, MultipleActorsActions)
        assert isinstance(position, int)

        maxiAll = 0
        # check that no actor in maa overlaps with the same actor
        redrawInd = []
        for i, actor in enumerate(maa.actors):

            actions = actor.actions
            mini, maxi = actions.boundingFrames(position)
            if maxi < MaxKF and maxi > maxiAll:
                maxiAll = maxi
            if check:
                for maa1, pos1 in self.maas:
                    #if actor.name[:6]=='redraw':
                    #    self.redrawActors[actor.object] = actor
                    #    continue
                    # does actor exist in maa1?
                    actor1 = maa1.findActor(actor)
                    if actor1 is None: # actor not in maa1
                        continue
                    if foundDejaVu and isinstance(actor1, RedrawActor):
                        continue
                    # does actions at position overlap with actor1 at pos1
                    mini1, maxi1 = actor1.actions.boundingFrames(pos1)
                    if maxi<mini1: continue
                    elif mini>maxi1: continue
                    else: return False
                    if mini>maxi1: continue
                    if maxi<mini1: continue
                    else: return False

            # if the maa contains a redraw actor add it to self.redrawActors
            # and remove it from the maa (after the "for" loop)
            if foundDejaVu and isinstance(actor, RedrawActor):
                if not self.redrawActors.has_key(actor.object):
                    self.redrawActors[actor.object] = actor
                    redrawInd.append(i)
                    
        for i in redrawInd:            
            maa.actors.pop(i)
                    
        # update self.endFrame
        if maxiAll > self.endFrame:
            self.endFrame = maxiAll + 1

        #add maa
        self.maas.append( [maa, position] )
        if not hasattr(maa, "startFlag"):
            maa.startFlag = "after previous"
        maa.startOffset = 0
        maa._director = weakref.ref(self)
        if isinstance(maa, MAAGroup):
            for m in maa.maas:
                m._director = weakref.ref(self)
        # create and dispatch event
        self.dispatchEvent(AddMAAEvent(maa))
        
        return True


    def stopViewersAutoRedraw(self):
        """
        Stop autoRedraw in all Viewer associates with RedrawActors
        """
        for actor in self.redrawActors.values():
            #print "stopped autoredraw"
            actor.object.stopAutoRedraw()
            
    def startViewersAutoRedraw(self):
        """
        Start autoRedraw in all Viewer associates with RedrawActors
        """
        for actor in self.redrawActors.values():
            #print "start autoredraw"
            actor.object.startAutoRedraw()

    def viewerRedraw(self):
        """
        make sure all Viewers will redraw
        """
        #print 'Viewer Redraw'
        for actor in self.redrawActors.values():
            if self.needsRedraw and actor.playing:
                actor.setValue()
                self.needsRedraw = False
                actor._maa().needsRedraw = False

        
    def setOrientation(self, orient):
        """
        make sure all Viewers will redraw
        """
        
        for actor in self.redrawActors.values():
            if actor.playing:
                vi = actor.object
                root = vi.rootObject
                if orient.has_key(root.fullName): # snapshot orient 
                    allkeys = orient.keys()
                    ort = {}
                    ort.update(orient[root.fullName])
                    allkeys.remove(root.fullName)
                    if orient.has_key('fieldOfView'):
                        ort['fieldOfView'] = orient['fieldOfView']
                        allkeys.remove('fieldOfView')
                    if orient.has_key('lookFrom'):
                        ort['lookFrom'] = orient['lookFrom']
                        allkeys.remove('lookFrom')                                  
                    setOrientation(root, ort)
                    for name in allkeys:
                        obj = vi.FindObjectByName(name)
                        if obj.fullName == name:
                           setOrientation(obj, orient[name])
                else:
                    setOrientation(actor.object.rootObject, orient)

        
    def setRendering(self, rendering):
        """
        make sure all Viewers will redraw
        """
        for actor in self.redrawActors.values():
            if actor.playing:
                setRendering( actor.object, rendering )

        
    def play(self, fromPos=0, toPos=None, forward=True, callback=None):
        """
        play through the list of MAAs

        None <- play(self, fromPos=0, toPos=None, forward=True, callback=None)

        fromPos: starting frame for play back
        toPos: ending frame for play back
        forward: True when playing direction is forward,
                 False when playing direction is backward
        
        """
        ## SEEMS NOT USED
        self.dispatchEvent(PlayerStartEvent(fromPos))

        if toPos is None:
            toPos = self.endFrame-1

        if len(self.maas)==0:
            return

        self.needsRedraw = False

        self.stopViewersAutoRedraw()
        
        for i in xrange(fromPos, toPos+1):
            self.setValuesAt(i)
            if callback:
                callback(i)
            self.viewerRedraw()
            
        self.startViewersAutoRedraw()

        #self.afterAnimationCb()

        self.dispatchEvent(PlayerStopEvent(i))


    def afterAnimationCb(self):
        """
        Call callback for each MAA to restore the state of objects drive by MAAs
        """
        for maa, off in self.maas:
            maa.afterAnimation_cb()
            

    def setValuesAt(self, frame):
        """
        Goto to a specified frame and issues values for all MAAs

        None <- def setValuesAt(self, frame):

        # FIXME this should also issue ending values of MAAs that ended before
        """

        # create and dispatch event for current frame change
        self.dispatchEvent(CurrentFrameEvent(frame))
        #stopAutoRedraw = False
        needsRedraw = False
        for maa, pos in self.maas:
            #print 'setting frame:', frame, maa.name, pos + maa.firstPosition
            if frame == pos + maa.firstPosition: # first Frame
                firstFrame = True
                if hasattr( maa, 'orient') and maa.forceOrient:
                    if not maa.setOrient:
                        self.setOrientation(maa.orient)
                        
                if hasattr(maa, "geomOrients") and maa.setOrient:
                        #self.stopViewersAutoRedraw()
                        #stopAutoRedraw = True
                        for o, val in maa.geomOrients.items():
                            setOrientation(o, val)
                
                if hasattr( maa, 'rendering') and maa.forceRendering:
                    self.setRendering(maa.rendering)
            else:
                firstFrame = False

            if frame >= pos+ maa.firstPosition and \
                   frame <= pos + maa.lastPosition:
                #print "setting values at frame %d , pos: %d for maa " % (
                #        frame,pos), maa.name

                maa.setValuesAt(frame, pos)
##                 if stopAutoRedraw:
##                     self.startViewersAutoRedraw()
##                     stopAutoRedraw = False
                if maa.needsRedraw: needsRedraw = True
        self.needsRedraw = needsRedraw
        

            #elif frame > maa.lastPosition+off:
            #    maa.setValuesAt(maa.lastPosition+off, off)



    def removeMAA(self, maa, position):
        """
        remove maa from MAADirector.

        maa, index <- removeMAA(maa, position)
        
        arguments:
           maa: instance of MAA;
           position: the specified MAA starting position in the MAADirector

        return value:
           returns the removed maa and its index in the director's MAA list

        Event:
            generates a RemoveMAA event

        Exceptions:
            raises a RuntimeError if MAA is not found in self.maas
        """

        # get index if it was not specified
        index = 0
        _maa = None
        for maa1, pos in self.maas:
            if maa==maa1 and pos==position:
                _maa = maa1
                break
            index += 1

        if _maa is None:
            raise RuntimeError("MAA not found")

        # remove maa
        rmaa = self.maas.pop(index)
        
        # check if self.redrawActors.values() contains a redraw actor from the removed maa:
        for obj,redrawactor in self.redrawActors.items():
            if redrawactor._maa()==maa:
                del self.redrawActors[redrawactor.object]
##         redrawactor = None 
##         for actor in rmaa[0].actors:
##             if foundDejaVu and isinstance(actor, RedrawActor):
##                 redrawactor = actor
##                 break
##         if redrawactor in self.redrawActors.values():
##             # remove the redraw actor from self.redrawActors dict, check if the rest of maas
##             # contain a redraw for the same object:
##             del (self.redrawActors[redrawactor.object])
##             obj = redrawactor.object
##             for maa in self.maas:
##                 if self.redrawActors.get(obj):
##                     break
##                 for actor in maa:
##                     if foundDejaVu and isinstance(actor, RedrawActor):
##                         if actor.object == obj:
##                             self.redrawActors[actor.object] = actor
##                             break
                    
        # create and dispatch event
        self.dispatchEvent(RemoveMAAEvent(rmaa[0]))

        # update director's endFrame
        self.updateEndFrame()

        return maa1, index


    def updateEndFrame(self):
        # update director's endFrame
        maxi = 0
        if len(self.maas)==0:
            self.endFrame = maxi
            return
        
        for maa, position in self.maas:
            end = position + maa.lastPosition
            if end > maxi:
                maxi = end

        self.endFrame = maxi + 1


    def computePosition(self, maa, startFlag=None, startOffset=None):
        """
        Compute the absolute starting frame of the specified maa
        
        position, index <- computePosition(maa, startFlag=None, startOffset=None)
        arguments:
           maa      - compute new position for this maa
           startFlag - can be 'with previous' or 'after previous'
           startOffset - start offset from the position specified by startFlag

        return values:
           position - absolute starting frame in animation
           index    - index of the specified maa in the self.maas list.
        """
        index = 0
        _maa = None
        _pos = None
        for maa1, pos in self.maas:
            if maa==maa1:
                _maa = maa1
                _pos = pos
                break
            index += 1

        if _maa is None:
            raise RuntimeError("MAA not found")

        if startFlag is None:
            startFlag = maa.startFlag
        if startOffset is None:
            startOffset = maa.startOffset

        if index == 0:
            position = startOffset
        else:
            # find previous maa in the list of self.maas
            prevMaa, prevPos = self.maas[index-1]
            # compute new position
            mini, maxi = prevMaa.boundingFrames(position = prevPos)
            if startFlag == "after previous":
                position = maxi+ 1 + startOffset
                #if startOffset == 0 :
                #    position = position + 1
            elif startFlag == "with previous":
                position = mini + startOffset
            else:
                raise RuntimeError("Wrong starting position: %s" % startFlag)
        return (position, index)


    def getMAASourceCode(self, variable, indent = 0, showwarning = True):
        """
        Return python code creating the list of maas

        string <- getMAASourceCode(self, variable, indent=0, showwarning=True)

        """

        tabs = " "*indent
        newtabs = tabs + 4*" "
        # define the showwarning variable that is used in the source code returned by
        # maa.getSourceCode()
        lines = tabs + """showwarning = %s\n""" % showwarning
        if not len (self.maas): return ""
        i = 0
        for maa in self.maas:
            if hasattr(maa[0], "getSourceCode"):
                maasrc = maa[0].getSourceCode("maa%d"%i)
                if len(maasrc):
                    lines += tabs + """maa%d = None\n"""%i
                    lines += tabs + maasrc + """\n"""
                    lines += tabs + """if maa%d is not None and len(maa%d.actors)> 0: \n""" % (i, i)
                    lines += newtabs + """%s.addMAAat(maa%d, offset+%d, check=False)\n""" % (variable, i,maa[1])
                    i = i+1
        return lines
            

##     def checkPosition(self, maa, position):
##         """check that no actor in the maa (placed at the specified position)
##         will overlap with the same actor of the maas in the list """
##         for maa1, pos1 in self.maas:
##             if maa1 == maa: continue
##             for actor in maa.actors:
##                 if actor.name[:6] == 'redraw':
##                     continue
##                 actor1 = maa1.findActor(actor)
##                 if actor1 is None: # actor not in maa1
##                     continue
##                 #same actor found
##                 mini, maxi = actor.actions.boundingFrames(position = position)
##                 mini1, maxi1 = actor1.actions.boundingFrames(pos1)
##                 if maxi<mini1: continue
##                 elif mini>maxi1: continue
##                 else:
##                     position = self.checkPosition(maa, maxi1 + 1)
##         return position
                    
                        
if __name__=='__main__':
    from datatypes import FloatType
    from interpolators import FloatScalarInterpolator

    class foo:

        def __init__(self):
            self.a= 2.0

    f = foo()

##     # create an actor
##     actor = Actor('test', f, 0.5, FloatType, FloatScalarInterpolator)
##     assert len(actor.keyframes.values) == 1
##     assert actor.keyframes.values[0] == 0.5

##     # create a director
##     d = Director()
##     d.addActor(actor)
    
##     # run the animation
##     print "Run keyframe 0"
##     d.run()

##     # add a keyframe
##     actor.setKeyframe( 10, 10.5)
##     print "Run keyframe 0 and 1"
##     d.run()

##     # add a keyframe at 15
##     actor.setKeyframe( 20, 10.5)
##     actor.setKeyframe( 25, 5.5)
##     assert len(actor.valueGenerators)==4
##     assert len(actor.keyframes.kfs)==4
##     print "Run keyframe 0,1,2,3"
##     d.run()

##     # stop interpolation between keyframe 1 and 2 (i.e interval 1)
##     actor.valueGenerators[1].configure(active = False)
##     #actor.setValueGenerator( None, segment=1)
##     print "Run keyframe 0,1 and 2,3"
##     d.run()
    
