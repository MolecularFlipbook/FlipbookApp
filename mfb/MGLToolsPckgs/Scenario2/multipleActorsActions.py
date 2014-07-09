import weakref
from time import time

from Scenario2.actions import Actions
from Scenario2.actor import Actor
from Scenario2 import MaxKF

from SimPy.Simulation import Process, initialize, activate, simulate, now, hold

class ActorProcess(Process):
    """
An ActorProcess is a SimPY Process object that gets created each time a
simulation is run.
"""
    def __init__(self, actor):
        """
Constructor of the ActorProcess object,

arguments:
    Actor:             An instance of an Action object
"""
        Process.__init__(self)
        self.actor = actor
        

    def execute(self):
        actor = self.actor
        if actor.playing:
            # FIXME we should wait for the first frame with values change
            yield hold, self, 0 # wait for the first frame
            director = actor._maa()
            while True:
                frame = now()
                if not director.moveForward:
                    # director.maxFrame is computed in director.run(), before activate()
                    frame = director.maxFrame - frame

                value = actor.actions.getValue(frame)
##                 value, inter, valGen = actor.getValueAt(frame)
##                 if valGen == None:
##                     if inter == -1: # this is the case when the first keyframe != 0 and
##                                     # the time cursor is over the interval before it -
##                                     # there is no interpolation
##                         value = None
##                 elif valGen != -1:
##                     if not valGen.active: value = None
                if value!='Nothing There':
                    # pre-step callback
                    try:
                        f, args, kw = actor.preStep_cb
                        f( *args, **kw)
                    except TypeError:
                        pass
                    #if actor.scenarioname == "DejaVuScenario":
                    director.needsRedraw = True
                    if actor.printValuesWhenSetting:
                        print "setting frame %d value of actor %s to " % (frame, actor.name), value
                    actor.setValue(value)

                    # post-step callback
                    try:
                        f, args, kw = actor.postStep_cb
                        f( *args, **kw)
                    except TypeError:
                        pass
                # Fixme we should wait for the next frame with values change
                yield hold, self, 1.


                
class RedrawActorProcess(ActorProcess):
    
    def execute(self):
        actor = self.actor
        # FIXME we should wait for the first frame with values change
        yield hold, self, 0 # wait for the first frame

        while True:
            frame = now()

            try:
                f, args, kw = actor.preStep_cb
                f( *args, **kw)
            except TypeError:
                pass
            maa = None
            if actor._maa:
                maa = actor._maa()
                if hasattr(maa, "_maaGroup") and maa._maaGroup is not None:
                    maa = maa._maaGroup()
            if maa and hasattr( maa, 'sortPoly'):
                if maa.sortPoly == 'Once' and frame==0:
                    #print "maa.name:", maa.name, "sortPoly once"
                    opacityGeoms, parents = maa.findOpacityGeoms()
                    for obj in opacityGeoms:
                        #print "opacity geom:", obj.name
                        order = {'+Zsort':1, '-Zsort':-1}.get(maa.sortOrder)
                        obj.sortPoly(order=order)
                    maa.reorderTransparentChildren(parents)

                elif maa.sortPoly == 'Always':
                    #print "maa.name:", maa.name, "sortPoly always"
                    opacityGeoms, parents = maa.findOpacityGeoms()
                    for obj in opacityGeoms:
                        order = {'+Zsort':1, '-Zsort':-1}.get(maa.sortOrder)
                        obj.sortPoly(order=order)
                    maa.reorderTransparentChildren(parents)
                
            if actor.printValuesWhenSetting:
                print "setting frame %d value of actor %s" % (frame, actor.name)
            actor.setValue()
            # post-step callback
            try:
                f, args, kw = actor.postStep_cb
                f( *args, **kw)
            except TypeError:
                pass
            # Fixme we should wait for the next frame with values change
            yield hold, self, 1.



class MultipleActorsActions:
    """
    Container for Actions objects for multiple actors.
    
    This object maintains a list of actors.

    attributes:
    .name: MAA name
    .actors: list of actors
    .currentFrame
    .endFrame:
    .firstPosition: First frame of the MAA relative to MAA start (i.e. 0)
    .lastPosition: last frame relative to MAA start (i.e. 0)

    Methods:
    bool <- AddActionsAt(actor, actions, position=0)
    Bool <- addMultipleActorsActionsAt(maa, position=None)
    names, posLabel, posStr, actStr, fullStr <-getStringRepr(pos1=0, pos2=None)
    None <- setValuesAt(self, frame, off=0, actor=None)
    """

    def __init__(self, name='MAactions', startFlag="after previous"):
        """
        MultiActorActions constructor

        MultiActorActions <- MultiActorActions(name='MAactions')
        """
        
        self.name = name
        self.actors = [] # list of actors

        self._director = None # becomes a weakref to MAADirector
        
        self.currentFrame = 0
        self.endFrame = 0
        self.firstPosition = 0
        self.lastPosition = 0

        self.gui = None # will be set when a gui is created
        self.recordingActors = []  # list of actors with recording flag on
           # i.e. actor.recording!='stopped'
        # FIXME should have a set and delete method to check type etc
        self.afterAnimation = [] # list of functions to be called after
                                 # play ends
        self.scenarios = {}
        self.autotrackDict = {}
        self.redrawActor = None
        self.moveForward = True
        self.maxFrame = 0
        self.needsRedraw = False
        # These are the attributes used by the sequence animator for computing
        # time position of this maa in the list of all maas.
        self.startFlag = startFlag
        self.startOffset = 0
        self.setOrient = False
        self.sortPoly = 'Once'
        self.sortOrder = "-Zsort"
        
        

    def AddActions(self, actor, actions, position=0):
        """
        adding actions for an actor at a given position

        bool <- AddActionsAt(actor, actions, position=0)

        arguments:
          actor: has to be an instance of an Actor Object
          actions: is an instance of an Actions object
          position: start frame for this action relative to begin of MAA
        
        return values
           
        if actor already exists in this MAA the actions are added to this actor
        else a new actor is created in this MAA tand the actions are added to
        this new actor
        
        """

        # FIXME
        # we should return the actor so we know when a new one is created
        # - actor is the actor in the MAA which can is a new actor if the
        #       incomming actor was not found in the MAA
        # - success is True if the actions were added successfully to the actor
        
        assert isinstance(actor, Actor)

        assert isinstance(actions, Actions)
        
        objAnim = self.findActor(actor)
        if objAnim is None:
            actor = self.addActor(actor)
        else:
            actor = objAnim

        success = actor.actions.addActionsAt(actions, position)
        if success:
            self.computeFirstAndLastPosition()

        return actor, success


    def findActor(self, actor):
        """
        find an actor if is exists in the director

        actor <- findActor(actor1)

        actor1 is an instance of an actor
        if there is an actor in the director withthe same name we return this actor
        else we return None
        """
        import types
        if type(actor) == types.StringType:
            name = actor
        else:
            name = actor.name
        for objAnim in self.actors:
            if objAnim.name == name:
                return objAnim
        return None


    def addActor(self, actor, redraw = True):
        """
        add an actor to the director.

        actor <- addActor(actor, redraw=True)
        
        if an actor with that name already exists this actor is return
        else a clone of the actor is added and returned
        """
        objAnim = self.findActor(actor)
        if objAnim is not None:
            return objAnim

        assert isinstance(actor, Actor)
        newActor = actor.clone()
        newActor._maa = weakref.ref(self)
        self.actors.append( newActor )
        lastFrame = newActor.getLastKeyFrame()
        if lastFrame is not None:
            lastFrame = lastFrame.pos
        else:
            lastFrame = 0
        if lastFrame >= self.endFrame:
            self.updateEndFrame(lastFrame)

        newActor.onAddToDirector()
        return newActor


    def addMultipleActorsActionsAt(self, maa, position=None):
        """
        add MultipleActorsActions object to a director at a given position

        Bool <- addMultipleActorsActionsAt(maa, position=None)

        if position is None the maa is added at its current position,
        else position can be an absolute frame at which the first keyframe
        of the maa will be placed.
        The boolean retrun True of the maa was successfully added
        """

        mini, maxi = maa.boundingFrames()

        # check if this MAA can be added
        # it can be added if no existing actor has anything between mini and maxi
        if position is None:
            position = mini
            
        for actor in maa.actors:
            objAnim = self.findActor(actor)
            if objAnim is None:
                continue # there will be no problem adding this actions
            if objAnim.actions.keyframeBetween(position, position + maxi - mini):
                return False

        for actor in maa.actors:
            actions = actor.actions
            actor = self.addActor(actor)
            poskf0 = actions.boundingFrames()[0]
            delta = poskf0 - mini
            val = actor.addActionsAt(actions, position+delta )
            if val is False:
                raise RuntimeError ("failed to add MAA")

        self.computeFirstAndLastPosition()
        return True


    def getStringRepr(self, pos1=0, pos2=None):
        """Return a string description of all actions.

        names, posLabel, posStr, actStr, fullStr <-getStringRepr(pos1=0, pos2=None)
        names is the list of actor names
        See Action.getStringRepr for the description of hte other returned values
        """

        allActionsStr = """"""
        names = []
        nokfnames = []
        nokfStr = """"""
        for actor in self.actors:
            actions = actor.actions

            posLab, posStr, actStr, fullStr = actions.getStringRepr(
                pos1, pos2, actor.name)
            if fullStr.find("No Keyframes")> 0:
                nokfnames.append(actor.name)
                nokfStr += fullStr+'\n'
            else:
                names.append(actor.name)
                if len(allActionsStr)==0:
                    allActionsStr += fullStr+'\n'
                else:
                    allActionsStr += actStr+'\n'
        if len(nokfStr):
            allActionsStr += nokfStr
            names.extend(nokfnames)
        return names, posLab, posStr, actStr, allActionsStr

  
    def afterAnimation_cb(self):
        # subclass this
        pass

    
    def computeFirstAndLastPosition(self):
        mini, maxi = self.boundingFrames()
        self.firstPosition = mini
        self.lastPosition = maxi


    def boundingFrames(self, position=0):
        """
        return first and last KF positions for the object
        """
        mini = MaxKF
        maxi = 0

        for actor in self.actors:
            action = actor.actions
            minia, maxia = action.boundingFrames(position)
            if maxia == MaxKF: continue  # for example , in  'redraw' actor case 
            if minia < mini:
                mini = minia
            if maxia > maxi and maxia < MaxKF:
                maxi = maxia
        #if maxi==0:
        #    maxi = MaxKF
        return mini, maxi


    def addScenario(self, name, scenario):
        self.scenarios[name] = scenario


    def start(self, setDirector = True, title = None):
        if self.gui is None:
            gui = DirectorGUI(self, title = title)
            gui.root.protocol('WM_DELETE_WINDOW', gui.root.withdraw)
            self.gui = gui
            if setDirector:
                for scenario in self.scenarios.values():
                    scenario.setDirector()
        else:
            if title:
                oldtitle = self.gui.root.title()
                if oldtitle != title:
                   self.gui.root.title(title) 
            self.gui.root.deiconify()

    def __repr__(self):
        return self.name


##     def deleteActor(self, actor):
##         # delete this actor and all its actions
##         name = actor.name
##         if self.gui:
##             self.gui.deleteActors()
##         if actor in self.actors:
##             self.actors.remove(actor)
##         if hasattr(actor, "guiVar"):
##             if actor.guiVar:
##                 actor.guiVar.set(0)
##         #if hasattr(actor.object, "animatedProperties"):
##         #    del actor.object.animatedProperties[name]
##         if hasattr(actor.scenario, "animatedProperties"):
##             del actor.scenario.animatedProperties[name]
##         if self.gui:
##             if self.gui.selectedFrames.has_key(name):
##                 self.gui.selectedFrames.pop(name)
##             if self.gui.autotracking:
##                 if self.autotrackDict.has_key(name):
##                     self.autotrackDict.pop(name)
##                     # this will update the dictioanary with a new "clean"
##                     # version of the deleted actor.
##                     self.autotrackDict.update(actor.scenario.getNewActors())
                
##             self.gui.drawActors()
##         ####################FIX THIS ###########
##         if len(actor.kfSetId):
##             for kf, setId in actor.kfSetId.items():
##                 kfset = self.gui.kfSets.get(setId)
##                 if kfset:
##                     kfset.removeKeyFrame(name, kf)
##                     if kfset.getNumberOfFrames() == 1:
##                         # remove the set
##                         self.gui.removeKFSet(kfset)

        

    def getLastFrame(self):
        # returns number of frames in the simulation
        return self.endFrame

    
    def getLastFrameWithChange(self, actors = None):
        # returns the last frame in which a value changes
        if not actors:
            actors = self.actors
        last = None
        for actor in actors:
            #if actor.isFullRange(): continue
            if actor.visible:
                lastFrame = actor.getLastKeyFrame()
                if last is None:
                    last = lastFrame
                else:
                    if lastFrame.pos > last.pos:
                        last = lastFrame
        return last


    def updateEndFrame(self, end, updateGUI=1):
        if not end:
            return
        
        if end > self.endFrame:
            self.endFrame = end
            if self.gui and updateGUI:
                self.gui.setDuration(end)

        else:
            last = self.getLastFrameWithChange()
            if last is not None:
                last = last.pos
            else:
                last = 0
            if end < last+10 : # when recording we want to make sure there are frame to the right
                self.endFrame = last +10
            else:
                self.endFrame = end
            if self.gui and updateGUI:
                self.gui.setDuration(self.endFrame)


    def run(self, forward=True):
        """
        used in DejaVu/scenarioInterface/animationPanels.py AnimationPanel.runMAA
        """
        if len(self.actors)==0:
            #print "no actors"
            return
        initialize()
        redraw = self.redrawActor
        start = 0
        #end = self.endFrame
        self.maxFrame = 0
        maxFrame = self.getLastFrameWithChange()
        if maxFrame is not None:
            self.maxFrame = maxFrame.pos

        end = self.maxFrame
        gui = self.gui
        if gui:
            if not (gui.startFrame == 0 and gui.stopFrame == 1):
                start = gui.startFrame
                end = gui.stopFrame
                self.maxFrame = end + start
        self.moveForward = forward
        if redraw:
            redraw.object.stopAutoRedraw()
            proc = RedrawActorProcess(redraw)
            activate(proc, proc.execute(), at=start, prior=True)
            #print 'activated redraw', 
        for actor in self.actors:
            if actor.name != "redraw":
                proc = ActorProcess(actor)
                activate(proc, proc.execute(), at=start, prior=True)
                #print 'activated ', actor.name, action
        #print 'simulate', self.endFrame
        simulate(until=end)
        #self.currentFrame = self.endFrame
        if forward:
            #self.currentFrame = self.endFrame
            self.currentFrame = end
        else:
           self.currentFrame = start
        # call callback after animation completes
        for f in self.afterAnimation:
            f()
        #self.afterAnimation_cb()
        if self.redrawActor:
            vi = self.redrawActor.object
            vi.startAutoRedraw()


    def _timedDraw(self, director, at):
        director.setValuesAt(at)
        director.viewerRedraw()
        dtime = time() - self._timeStart
        fraction = min(1.0, dtime/self._duration)
        frameT = int(fraction*self._nbFrames)
        self.frameCounter += 1
        at = max(frameT, self.frameCounter)
        #print 'AT', at, director.endFrame
        #print dtime, frameT, self.frameCounter, director.endFrame
        if at < self._nbFrames:
            self._afterFunc(1, self._timedDraw(director, at))
            
        
    def runIn(self, duration, afterFunc):
        """
        used in DejaVu/scenarioInterface/animationPanels.py AnimationPanel.runMAA
        """
        from Scenario2.director import MAADirector
        director = MAADirector()
        director.addMAAat(self, 0)

        self.needsRedraw = False

        director.stopViewersAutoRedraw()

        self._nbFrames = director.endFrame-1
        self._duration = float(duration)
        self._afterFunc = afterFunc
        self.frameCounter = 0
        
        self._timeStart = time()
        self._timedDraw(director, 0)

        del self._nbFrames
        del self._duration
        del self._timeStart
        del self._afterFunc
        
        director.startViewersAutoRedraw()

        
    def findOpacityGeoms(self):
        """a helper function used in setValuesAt(). Finds all opacity actors
        and returns a list of their objects(geometries) and  a dictionary of
        the parents of the 'opacity' geometries"""
        
        # find all opacity actors and the parents of the geometry
        opacityGeoms = []
        parents  = {}
        for a in self.actors:
            if a.name[-7:]=='opacity':
                obj = a.object
                opacityGeoms.append(obj)
                if parents.has_key(obj.parent):
                    parents[obj.parent].append(obj)
                else:
                    parents[obj.parent] = [obj]
        return opacityGeoms, parents


    def reorderTransparentChildren(self, parents):
        """a helper function used in setValuesAt().
        Reorder children of same parent from back to front"""
        
        import numpy
        for parent, objs in parents.items():
            allobjs = []
            for o in parent.children:
                if o.visible:
                    allobjs.append(o)
            zmin = []
            for obj in allobjs:
                mat = obj.GetMatrix()
                p1, p2 = obj.ComputeBB()
                p = [ (p1[0], p1[1], p1[2], 1.),
                      (p2[0], p2[1], p2[2], 1.)] 
                tp = numpy.dot(p, mat.transpose())
                # save closest Z value for this geom
                zmin.append( max(tp[0][2], tp[1][2]) )
                # remove child from parent's list
                parent.children.remove(obj)

            # sort by increasing z
            sortedl = numpy.argsort(zmin)

            # append the children to parent's children list
            # ordered from furthest z to closest
            for i in sortedl:#
                parent.children.append(allobjs[i])


    def setValuesAt(self, frame, off=0, actor=None):
        #print "setValuesAt:", frame, self.name
        firstFrame = False
        if frame == off + self.firstPosition: # first Frame
            firstFrame = True
               
        if actor:
            actors = [actor]
        else:
            actors = self.actors
        self.needsRedraw = False
        for actor in actors:
            actions = actor.actions
            if actor.playing:
                actor.setValueAt(frame, off)
        if hasattr( self, 'sortPoly'):
            if self.sortPoly == 'Once' and firstFrame:
                #print "maa.name:", self.name, "sortPoly once"
                opacityGeoms, parents = self.findOpacityGeoms()
                for obj in opacityGeoms:
                    #print "'Once, opacity geom:", obj.name
                    order = {'+Zsort':1, '-Zsort':-1}.get(self.sortOrder)
                    obj.sortPoly(order=order)
                self.reorderTransparentChildren(parents)

            elif self.sortPoly == 'Always':
                #print "maa.name:", self.name, "sortPoly always"
                opacityGeoms, parents = self.findOpacityGeoms()
                for obj in opacityGeoms:
                    #print "Always, opacity geom:", obj.name
                    order = {'+Zsort':1, '-Zsort':-1}.get(self.sortOrder)
                    obj.sortPoly(order=order)
                self.reorderTransparentChildren(parents)

    def getAllGeoms(self):
        """Returns a list of all geometries driven by maa's actors"""
        geoms = []
        from DejaVu.Geom import Geom
        from DejaVu.scenarioInterface.actor import DejaVuTransformationActor
        
        for actor in self.actors:
            if isinstance(actor, DejaVuTransformationActor):
                continue
            obj = actor.object
            if isinstance(obj, Geom) and obj not in geoms:
                geoms.append(obj)
        return geoms


    def gotoFrame(self, frame, set=True):
        if frame<0:
            frame = 0
        elif frame>self.endFrame:
            frame = self.endFrame
        if frame==self.currentFrame:
            return
        self.currentFrame = frame
        if set:
            self.setValuesAt(frame)
        if self.gui:
            self.gui.placeTimeCursor(frame)
            

##     def createActorFromData(self, obj, propname, scenarioInterface,filename, fields,
##                             data, start = 0, end=-1):
##         # Create a special actor whose valueGenerator returns values from a data 
##         # sequence such as list or numpy array, This data is read from a file (.adat)->
##         # see actor.py/adatFileParser

##         # obj - animatable object
##         # propname - the object's animated property name
##         # scenarioInterface - scenario interface that is n self.scenarios and "knows" how
##         # to create a regular actor for this object (i.e has createActor() method).
##         # start - first keyframe of the actor
##         # end - last keyframe of the actor ( if end == -1, then the number of frames between
##         # first and last keyframes is len(data)-1, or one data step per each keyframe).

##         if data is None:
##             print "createActorFromData: data is None"
##             return

##         assert scenarioInterface in self.scenarios.values()
##         actor = None
##         if data is not None:
##             assert type(data).__name__ in ('ndarray', 'list')
##             nsteps = len(data)
##             firstVal = data[0]
##             lastVal =  data[nsteps-1]
##             #print filename, len(data), data[0], propname
##             # create an actor with ReadDataInterpolator valuegenerator
##             #try:

##             # this will create file actor with two keyframes : "0" and "nsteps-1" 
##             actor = scenarioInterface.createActor(obj, propname, check=False,
##                                                   addToDirector=False,
##                                                   actorData = (filename, data))
##             actor.datafields = fields
##             #except:
##             #    warnings.warn("Failed to create file actor %s" % propname)
##             #    return None
##             if actor:
##                 self.addActor(actor)
##                 #print "start=", start, "end=", end, "nsteps=", nsteps
##                 if end == -1:
##                     end = start + nsteps - 1
##                 if end != nsteps-1:
##                     if self.gui:
##                         #this will move "nsteps-1" keyframe  to "end" keyframe 
##                         self.gui.selectKeyFrame_cb(actor, nsteps-1, newframe=end)
##                 if start != 0:
##                     if self.gui:
##                         # this will move "0" keyframe to "start" keyframe
##                         self.gui.selectKeyFrame_cb(actor,0,newframe=start) 
                    
##         return actor



class MAAGroup:


    def __init__(self, name='MAAGroup', maalist=[], startFlag="after previous"):
        """
        MAAGroup constructor

        MAAGroup <- MAAGroup(name='MAAGroup', maalist=[], startFlag='after previous')
        """
        self.maas = []
        self.actors = []
        self.firstPosition = 0
        self.lastPosition = 0
        self.currentFrame = 0
        self.redrawActor = None
        self.afterAnimation = []
        for maa in maalist:
            self.AddMaa(maa)
        self.name = name
        self._director = None # becomes a weakref to MAADirector
        
        self.gui = None # will be set when a gui is created
        self.scenarios = {}

        self.maxFrame = 0

        # These are the attributes used by the sequence animator for computing
        # time position of this maa in the list of all maas.
        self.startFlag = startFlag
        self.startOffset = 0
        self.editorClass = None
        self.setOrient = False
        self.needsRedraw = False
        self.sortPoly = 'Once'
        self.sortOrder = "-Zsort"

        

    def AddMaa(self, maa):
        mini, maxi = maa.boundingFrames()
        if mini < self.firstPosition:
            self.firstPosition=mini
        if maxi > self.lastPosition:
            self.lastPosition = maxi
        self.maas.append(maa)
        maa._maaGroup = weakref.ref(self)
        for actor in maa.actors:
            if actor.name.startswith('redraw'):
                if not self.redrawActor:
                    self.actors.insert(0, actor)
                    self.redrawActor = actor
            else:
                self.actors.append(actor)
            self.afterAnimation.extend(maa.afterAnimation) 
        

    def findActor(self, actor):
        """
        find an actor if is exists in the director

        actor <- findActor(actor1)

        actor1 is an instance of an actor
        if there is an actor in the director withthe same name we return this actor
        else we return None
        """
        for maa in self.maas:
            _actor = maa.findActor(actor)
            if _actor is not None:
                return _actor
        return None

    def makeActorList(self, maas = None, reverse = False):
        self.actors = []
        self.redrawActor = None
        if maas == None:
            maas = self.maas
        for maa in maas:
            actors = maa.actors
            if reverse: 
                # In the maa.run() method the actors are played (by simulate()) in the reversed order
                # from the one they had beed activated. So, if we want to play actors in
                # the original order , we need to reverse the list of actors before activating each actor.
                actors = maa.actors[:]
                actors.reverse()
            for actor in actors:
                if actor.name.startswith('redraw'):
                    if not self.redrawActor:
                        self.actors.insert(0, actor)
                        self.redrawActor = actor
                else:
                    self.actors.append(actor)


    def getAllGeoms(self):
        geoms = []
        for maa in self.maas:
            _geoms = maa.getAllGeoms()
            for obj in _geoms:
                if obj not in geoms:
                    geoms.append(obj)
        return geoms
                    

    def getStringRepr(self, pos1=0, pos2=None):
        """Return a string description of all actions.

        names, posLabel, posStr, actStr, fullStr <-getStringRepr(pos1=0, pos2=None)
        names is the list of actor names
        See Action.getStringRepr for the description of hte other returned values
        """

        allActionsStr = """"""
        names = []
        for maa in self.maas:
            _names, _posLab, _posStr, _actStr, _allActionsStr=maa.getStringRepr(pos1, pos2)
            names.extend(_names)
            allActionsStr += _allActionsStr 
        return names, allActionsStr

  
    def afterAnimation_cb(self):
        # subclass this
        pass

    
    def computeFirstAndLastPosition(self):
        self.firstPosition = 0
        self.lastPosition = 0
        for maa in self.maas:
            mini, maxi = maa.boundingFrames()
            if mini < self.firstPosition:
                self.firstPosition=mini
            if maxi > self.lastPosition:
                self.lastPosition = maxi


    def boundingFrames(self, position=0):
        """
        return first and last KF positions for the object
        """
        self.computeFirstAndLastPosition()
        return self.firstPosition+position, self.lastPosition+position


    def addScenario(self, name, scenario):
        self.scenarios[name] = scenario


    def run(self, forward=True):
        """
        used in DejaVu/scenarioInterface/animationGUI.py animClip.makeAndRunMAA
        """
        if len(self.maas)==0:
            #print "no actors"
            return
        initialize()
        redraw = self.redrawActor
        actors = self.actors
        afterAnimation = self.afterAnimation
        start = self.firstPosition
        end = self.lastPosition
        if redraw:
            redraw.object.stopAutoRedraw()
            proc = RedrawActorProcess(redraw)
            activate(proc, proc.execute(), at=start, prior=True)
            #print 'activated redraw', 
        for actor in actors:
            if actor == redraw:continue
            proc = ActorProcess(actor)
            activate(proc, proc.execute(), at=start, prior=True)
        simulate(until=end)
        #self.currentFrame = self.endFrame
        if forward:
            #self.currentFrame = self.endFrame
            self.currentFrame = end
        else:
           self.currentFrame = start
        # call callback after animation completes
        for f in afterAnimation:
            f()
        #self.afterAnimation_cb()
        if redraw:
            redraw.object.startAutoRedraw()


    def setValuesAt(self, frame, off=0, actor=None):
        for maa in self.maas:
            maa.setValuesAt(frame, off, actor)

    def getSourceCode(self, varname, indent = 0):
        tabs = " "*indent
        lines = tabs + """from Scenario2.multipleActorsActions import MAAGroup\n"""
        lines += tabs +"""%s = MAAGroup(name='%s', startFlag='%s')\n""" %(varname, self.name, self.startFlag)
        for i, maa in enumerate(self.maas):
            lines +=maa.getSourceCode("_maa%d"%i, indent=indent)
            lines += tabs + """%s.AddMaa(_maa%d)\n""" % (varname, i)
        return lines
        
            
