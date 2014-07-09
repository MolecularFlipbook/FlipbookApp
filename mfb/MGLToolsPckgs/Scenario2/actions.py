##
##  Author Michel F. Sanner Jan 2009
##
import weakref
from Scenario2.keyframes import KF, Interval
from Scenario2 import MaxKF
from Scenario2.keyframes import AutoCurrentValueObject, KFValueFromFunction

class Actions:
    """
    container for a list of keyframes and intervals

    attributes:
    .keyframes: list of chronologically sorted Scenario2.keyframes.KF objects
    .intervals: list of chronologically sorted Scenario2.keyframes.Interval obj

    methods:
    KF <- addKeyframe(self, kf)
    None <- deleteKeyframe(self, kf)

    Bool <- actions.addActionsAt(srcActions, position, check=True)

    Bool <- addInterval(self, interval):

    Interval <- getInterval(self, position)

    value <- getValue(self, frame)

    Actions <- copyAt(self, position)
    
    firstFrame, lastFrame <- boundingFrames(self, position=0)
    """

    def __init__(self, actor=None):
        if actor:
            self.actor = weakref.ref(actor)
        else:
            self.actor = None
        self.keyframes = [] # sorted chronologically
        self.intervals = [] #these have to be sorted chronologically


    def getStringRepr(self, pos1=0, pos2=None, actorName='ACTOR______NAME'):
        """Return a string description of action. The description contains
        a list of position labels, containing all the mutiple of 10 positions,
        a string representing the time line and a string representing the
        actions. The full string is a multi line strign that will display all
        the information. If provided, the name will appear in front of the
        actStr and use 15 charaters

        posLabel, posStr, actStr, fullStr <-getStringRepr(pos1=0, pos2=None)

        if pos2 is None pos2 will be the position of the last keyframe

        posLabel is a list of all multiple of 10 positions (i.e. 'I' in poStr)
        
        The posStr has an '|' at all multiples of 10 and a ":" the multiple of 5
        that are not multiple of 10 (e.g. "   |    :    |     : ")

        The actStr string contains:
          ' ': a blank space for each position where no value
          'x': where there is a keyframe
          '-': where there is an active interval
          '.': where there is an inactive interval
          '|' every position that is a multiple of 10

          e.g. 'x---------x    x    x---------x'

        FullString example:
        
                             1         2         3
                             0         0         0         0
                             |    :    |    :    |    :    |
             ACTOR______NAME x.........x    x    x---------x

             interval (0,10) is inactive, there is an isolated keyframe at 15
             and an active interval from 20 to 30
        """

        nameLength = 30
        posStr = " "*(nameLength+1)
        sformat = "%0"+"%ds"%nameLength
        actStr = sformat%actorName[:nameLength]
        posLabels = []

        if len(self.keyframes)==0:
            return [], posStr, actStr, actStr+"No Keyframes"

        if pos2 is None:
            pos2 = self.keyframes[-1].pos

        nblines = len(str(pos2)) # how many lines we need for labels
        labelLines = []
        for i in range(nblines):
            labelLines.append( " "*(nameLength+1) )

        for i, pos in enumerate(xrange(pos1,pos2+1)):
            obj = self.getInterval(pos)

            # build posStr
            rpos = i+pos1
            if rpos%10==0 or i==0:
                if (rpos%10==0):
                    posStr += '|'
                else:
                    posStr += ' '
                posLabels.append(rpos)
            elif rpos%5==0:
                posStr += ':'
            else:
                posStr += ' '

            # build label lines 
            if (rpos)%10==0 or i==0:
                lab = str(rpos)
                nbl = len(lab)
                for j in range(0,nblines-nbl):
                    labelLines[j] += ' '
                for j,k in enumerate(range(nblines-nbl,nblines)):
                     labelLines[k] += lab[j]
            else:
                for j in range(nblines):
                    labelLines[j] += ' '

            # build actStr
            if obj is None:
                actStr += ' '

            elif isinstance(obj, KF):
                actStr += 'x'

            elif obj.active: # we are on an active interval
##                 if (rpos%10==0):
##                     actStr += '+'
##                 elif rpos%5==0:
##                     actStr += ':'
##                 else:
##                     actStr += '-'
                actStr += '-'
                
            else: # we are on an inactive interval
                actStr += '.'

        # build fullStr
        fullStr = """"""
        for i in range( nblines):
            fullStr += labelLines[i]+'\n'
        fullStr += posStr+'\n'
        fullStr += actStr
        
        return posLabels, posStr, actStr, fullStr

    
    def addKeyframe(self, kf):
        """
        add a  keyframe kf.
        Kf can be a KF object or a (position, value) pair.
        this method returns and existing KF or the one we sent into the method
        """
        if not isinstance(kf, KF):
            kf = KF( *kf )
        
        # find what is on
        obj = self.getInterval(kf.pos)
        if obj is None: # there is nothing at this position
                        # we simply add a copy of this keyframe
            self._insertKeyframe(kf)
            return kf
        
        elif isinstance(obj, KF):
            if kf.isLinked():
                return  None# a linked keyframe cannot be added on top of a keyframe

            elif kf.__class__ != obj.__class__: # we replace the keyframe
                kf.leftInterval = obj.leftInterval
                if kf.leftInterval is not None:
                    kf.leftInterval.kf2 = kf
                kf.rightInterval = obj.rightInterval
                if kf.rightInterval is not None:
                    kf.rightInterval.kf1 = kf
                self.keyframes.remove(obj)
                self._insertKeyframe(kf)
                return kf

            elif kf.valueObject.__class__ == obj.valueObject.__class__:
                # we over write the value
                obj.setValue(kf.getValue())
                return obj

            else:
                # we need to overwrite KF's value object
                obj.valueObject = kf.valueObject
                return obj

        elif isinstance(obj, Interval):
            # put kf in list of keyframes
            self._insertKeyframe(kf)

            if obj.isLinked(): # this is a linked interval
                off = kf.pos - obj.k1.pos
                self.splitIntervalWithKF(obj, kf)
                newInter = kf.rightInterval


                for inter in linkedInter[1:]:
                    il = newInter.linkedCopy(inter.k1.pos+off)
                    il.setKF2( inter.k2 )
                    kf1 = il.kf1
                    self._insertKeyframe(kf1)
                    inter.setKf2( kf1 )

            else: # not linked
                self.splitIntervalWithKF(obj, kf)

            return kf

    def deleteKeyframe(self, kf):
        """
        Delete keyframe kf if kf in not in any interval
        """
        try:
            for i in self.intervals:
                assert i.kf1!=kf
                assert i.kf2!=kf
        except AssertionError:
            print "could not remove kf, belongs to interval", kf, kf.pos
            return
        self.keyframes.remove(kf)


        
    def splitIntervalWithKF(self, inter, kf):
        """
        Split the interval inter using keyframe kf.
        kf is known to be in the interval. 
        """
        newInter = Interval(kf, inter.kf2)

        if inter.valGen.generator:
            gen = inter.valGen.generator
            generator = gen.clone()
            newInter.setValGenGenerator(generator)

        # set left and right for kf
        kf.leftInterval = inter
        kf.rightInterval = newInter

        # set kf as last of old interval
        inter.setKF2(kf)

        self._insertInterval(newInter)

##         for i,inter in enumerate(self.intervals):
##             if inter==obj:
##                 break
##         self.intervals.insert(i+1, newInter)

     
    def _insertInterval(self, inter):
        """
        insert the interval inter into self.intervals respecting the chronolgy. 
        The method does not perform any checks. It is assumed that inter.kf1 and
        inter.kf2 are in self.keyframes
        """
        
        p1 = inter.kf1.pos
        n=0 # needed when len(self.intervals)==0
        for n,i in enumerate(self.intervals):
            if i.kf1.pos > p1:
                break
        if len(self.intervals):
            if p1 > i.kf1.pos: # this happens when we split last interval or add a new interval after the last one
                n = n+1
        self.intervals.insert(n, inter)
        return


    def _insertKeyframe(self, kf):
        """
        insert the keyframe fk into self.keyframes respecting the chronolgy
        """
        if len(self.keyframes)==0:
            self.keyframes.append(kf)
            return
        
        for i,k in enumerate(self.keyframes):
            if k.pos==kf.pos:
                raise ValueError("position %d already has a keyframe"%k.pos)
            if k.pos > kf.pos:
                self.keyframes.insert(i, kf)
                return
        self.keyframes.append(kf)


    def boundingFrames(self, position=0):
        """
        return first and last frame of an action object
        """
        first = 0
        last = MaxKF
        if len(self.keyframes)>0:
            first = self.keyframes[0].pos+position
            last = self.keyframes[-1].pos+position
        return first, last


    def isLinked(self):
        """
        Return True if any object in the action is linked
        """
        for k in self.keyframes:
            if k.isLinked():
                return True

        for i in self.intervals:
            if i.isLinked():
                return True

        return False


    def keyframeBetween(self, pos1, pos2):
        """
        return true if there is a keyframe between the 2 positions
        """
        for k in self.keyframes:
            if k.pos >= pos1:
                if k.pos <= pos2:
                    return True
                else:
                    return False
                

    def checkAddLinkedActionsAt(self, action, position):
        """
        Determine whether a linked copy of the action can be added
        to this action object at the specified position.
        The addition of the action is allowed only if it does not overlap any
        KF or interval in current action (self) when placed at the specified position.
        """

        if len(actions.keyframes)==0:
            return False
        
        firstPos = actions.keyFrames[0].pos
        #delta = position - firstPos
        delta = position

        # get first and last frame for the action to be added 
        mini, maxi = action.boundingFrames()
        mini += delta
        maxi += delta

        # check that no keyframe of self is withing mini and maxi
        for k in self.keyframes:
            if k.pos >= mini and k.pos <= maxi:
                return False

        # now we know that no KF is within mini and maxi
        # we need to check that no interval of self spans the whole action object
        # this can only happen if there is an interval i in self for which the first
        # KF is BEFORE mini and the last KF is AFTER maxi
        for i in self.intervals:
            k1 = i.kf1
            k2 = i.kf2
            if k1.pos < mini and k.pos > maxi:
                return False

        return True

    
    def checkAddActionsAt(self, actions, position):
        """
        Determine whether the physical copy of the keyframes and intervals in action
        can be added to this action object at the specified position.
        The following rules are enforced:
           1. no KF to be added (at the position) falls onto an interval
           2. no inside of an interval to be added overlaps with either a KF or an Interval
        """
        if len(actions.keyframes)==0:
            return
        
        firstPos = actions.keyframes[0].pos
        #delta = position - firstPos
        delta = position

        # no KF to be added falls onto an interval
        for k in actions.keyframes: # loop over KFs kf to be added
            # check what is in self at position kf.pos
            obj = self.getInterval(k.pos+delta)
            # if it is an Interval we cannot paste actions
            if isinstance(obj, Interval):
                return False

        # no KF from actions to be added is inside of an interval
        # hence the each KF to be added either falls on nothing or a KF
        # in self

        # added overlaps with either a KF or an Interval
        for i in actions.intervals: # loop over interals to be added

            # check that self has no KF within interval to be added i
            if self.keyframeBetween(i.kf1.pos+1+delta, i.kf2.pos-1+delta):
                return False
                
        return True

            
    def addLinkedActionsAt(self, actions, position, check=True):
        """
        Creates a linked copy of the actions at specified position
        and adds it to this actions object.
        If check is True, the method first checks if linked actions can be added
        at the position.
        """
        if check:
            if not self.checkAddLinkedActionsAt(actions, position):
                return

        actions1 = actions.linkedCopyAt(position)

        for sourcekf in actions1.keyframes:
            destkf = self._insertKeyframe( sourcekf )
            
        # insert interval
        for inter in actions1.intervals:
            self._insertInterval(inter)


    def addActionsAt(self, srcActions, position, check=True):
        """
        Add srcActions at a given position to this actions object

        Bool <- actions.addActionsAt(srcActions, position, check=True)
        
        Creates a physical copy of the actions at specified position
        and adds it to this actions object.
        
        If check is True, the method first checks if actions can be added
        at the position adn returns False if it can;t be added. If the
        action is added successfully True is returned.
        """
        if srcActions==self:
            if position==None:
                return True
            if len(self.keyframes)>0 and position==self.keyframes[0].pos:
                return True
            
        if check:
            if not self.checkAddActionsAt(srcActions, position):
                return False

        actions1 = srcActions.copyAt(position)
        # insert keyframes (after the interval was added, else getInterval()
        # finds these keywords)
        lookup = {}
        for sourcekf in actions1.keyframes:
            destkf = self.addKeyframe(sourcekf)
            lookup[sourcekf] = destkf
            if destkf != sourcekf:
                li = sourcekf.leftInterval
                
                if li:
                    li.kf2 = destkf
                ri = sourcekf.rightInterval
                if ri:
                    ri.kf1 = destkf
        for i, inter in enumerate(actions1.intervals):
            kf1 = actions1.keyframes[i]
            kf2 = actions1.keyframes[i+1]
            if lookup[kf1] != kf1 and lookup[kf2] != kf2:
                # both keyframes overwrote existing keyframes ==> interval needs to be overwritten
                # i.e. we copy the valueGenerator of the srcInterval to the existing interval
                lookup[kf1].rightInterval.valGen = inter.valGen.clone()
            else:
                self._insertInterval(inter)
                inter.kf1.rightInterval = inter
                inter.kf2.leftInterval = inter
        return True


    def addInterval(self, interval):
        """
        add an interval to this Actions objet.
        The interval can be added if:
            1 - both keyframes fall on keyframes AND
              a - these 2 keyframes belong to the same existing interval
                  in this case, the generator of the destination interval is
                  overwritten with the generator from the source interval
              b - or these 2 keyframes belong 2 succesive intervals (i.e fill gap between intervals)

            2 - if both keyframes fall onto nothing, the interval is addded if there is no existing
                 keyframe inside the interval to be added.

            3 - kf1 falls on nothing and kf2 falls on an existing KF
                 we add if there is no existing KF between kf1.pos+1 and kf2.pos-1
                 
            4 - kf2 falls on nothing and kf1 falls on an existing KF
                 we add if there is no existing KF between kf1.pos+1 and kf2.pos-1

            5 - either kf1 or kf2 fall on an existing Interval
               the interval cannot be added
               
        return True if interval was added and False else
        """
        kf1 = interval.kf1
        kf2 = interval.kf2
        
        obj1 = self.getInterval(kf1.pos)
        obj2 = self.getInterval(kf2.pos)

        if isinstance(obj1, Interval) or isinstance(obj2, Interval):
            return False # case 5

        # at this point kf1 and kf2 can either fall on nothing or a KF 

        if self.keyframeBetween(kf1.pos+1, kf2.pos-1):
            return False

        kf1 = self.addKeyframe(kf1)
        kf2 = self.addKeyframe(kf2)

        if obj1 is not None and obj2 is not None: # both fall in KFs
            ri = obj1.rightInterval
            li = obj2.leftInterval
            if ri and ri==li: # case 1.a
                ri.valGen.generator = interval.valGen.generator
                return True

        kf1.rightInterval = interval
        kf2.leftInterval = interval
        interval.kf1 = kf1
        interval.kf2 = kf2
        self._insertInterval(interval)
        return True


    def getInterval(self, position):
        """
        return what is at the position passed as an argument. This can be a keyframe, and interval, or None if there is nothing there
        """
        result = None

        # check if there is a keyframe at this position
        # cannot be done using intervals because of isolated keyframes
        for k in self.keyframes:
            if position == k.pos:
                return k

        # check is position falls within an interval
        for i, inter in enumerate(self.intervals):
            p1 = None
            p2 = None
            kf1 = inter.kf1
            if kf1:
                p1 = kf1.pos 
            else:
                p1 = 0
                
            kf2 = inter.kf2
            if kf2:
                p2 = kf2.pos 
            else:
                p2 = MaxKF
                
            if p1<position and p2>position:
                return inter

        return None

        
    def getValue(self, frame):
        """
        return a value for a given frame, If not KF or Interval exists at this
        position, we return the string 'Nothing There'
        """
        obj = self.getInterval(frame)

        if obj is None:
            return 'Nothing There'

        elif isinstance(obj, KF):
            ri = obj.rightInterval
            li = obj.leftInterval

            # KF--------------AKF
            # ^
            # obj
            # when playing from left to right we need to configure ri.lastValue
            if ri:
                if obj==ri.kf1: # first KF of interval ri
                    ri._lastSetValue = None
                if isinstance(ri.kf2.valueObject, AutoCurrentValueObject):
                    if frame==0:
                        # update interval generators with a value
                        ri.kf2.getValue(value=self.actor().initialValue)
                    else:
                        ri.kf2.getValue() # getting the value forces generator to update lastVal
                    #print 'Akf2 is set to', ri.valGen.generator.firstVal, self.actor().initialValue
                
                elif isinstance(ri.kf2, KFValueFromFunction):
                    ri.kf2.getValue()

                if ri.valGen.generator is not None:
                    if hasattr(ri.valGen.generator, "constant") and  ri.valGen.generator.constant:
                        return ri.getValue(frame)                   
                    
            # KF--------------AKF
            #                  ^
            #                 obj
            # when playing from left to right we need to return the value at this AKF
            # without setting it from the object's current value
            if li:
                if isinstance(obj.valueObject, AutoCurrentValueObject):
                    return li.valGen.generator.lastVal
                
                if  li.valGen.generator is not None:
                    if hasattr(li.valGen.generator, "constant") and  li.valGen.generator.constant:
                        return li.getValue(frame)                

            return obj.getValue()

        else: # we are on an interval
            if obj.active:
                #print 'get frame:', frame, obj.getValue(frame)
                return obj.getValue(frame)

            
       
    def copyAt(self, position):

        if len(self.keyframes)==0:
            return None

        #delta = position - self.keyframes[0].pos
        delta = position
        
        # create Actions object
        na = self.__class__()
        lookup = {}

        # create copies of KFs
        for k in self.keyframes:
            nkf = k.copy(k.pos+delta)
            na.keyframes.append(nkf)
            lookup[k] = nkf

        # create copies of intervals
        for i in self.intervals:
            ni = i.__class__(lookup[i.kf1], lookup[i.kf2], i.valGen.clone())
            if hasattr(i, 'data'):
                ni.data = i.data.copy()
            na.intervals.append(ni)

        return na


    def linkedCopyAt(self, position):

        if len(self.keyframes)==0:
            return None

        #delta = position - self.keyframes[0].pos
        delta = position
        
        # create Actions object
        na = self.__class__()
        lookup = {}

        # create linked copies of all KFs
        for k in self.keyframes:
            nkf = k.linkedCopy(k.pos+delta)
            na.keyframes.append(nkf)
            lookup[k] = nkf

        # create copies of intervals
        pos = self.keyframes[0].pos
        for i in self.intervals:
            ni = i.getLinkedCopy(position)
            ni.kf1 = lookup[i.kf1]
            ni.kf2 = lookup[i.kf2]
            na.intervals.append(ni)

        return na
