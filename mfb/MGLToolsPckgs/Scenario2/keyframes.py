##
##  Author Michel F. Sanner Jan 2009
##
class ValueObject:
    """Object holding a value associated with a keyframe
    """

    def __init__(self, value=None, cmp=None):
        """Constructor of ValueObject
        None <- ValueObject(value=None, cmp=None)
        arguments: value  -  a value associated with a keyframe
                   cmp - a function used to compare the value of this ValueObject with
                         the value of another ValueObject.
        """
        self.value = value
        self.cmp = cmp
        
    def getValue(self):
        """
        value <- getValue()
        returns self.value
        """
        return self.value

    def setValue(self, value):
        """
        None <- setValue(value)
        Set the value atttribute
        """
        self.value = value

    def equal(self, valueObject):
        """ 
        bool <- equal(valueObject)
        compare the value stored in self.value with
        the value of specified ValueObject.
        Returns True or False
        """
        if self.cmp:
            return self.cmp(self.value, valueObject.value)
        else:
            return self.value == valueObject.value


class AutoCurrentValueObject(ValueObject):
    """
    ValueObject class that will get and set it's value autoamtically to the
    current value of the actor's animated object when it plays.
    The actor has to be able to retrieve the
    current value from the object it is driving.
    """
    def __init__(self, actor):
        """
        None <- AutoCurrentValueObject(actor)
        argument:
          actor - an Actor instance, has to have getValueFromObject method 
        """
        ValueObject.__init__(self)
        assert actor.getFuncTuple
        self.actor = actor

    def getValue(self):
        """
        value <- getValue()
        Returns the current value of the actor's object associated with this ValueObject
        """
        return self.actor.getValueFromObject()


class ValueFromFunctionObject(ValueObject):
    """
    ValueObject object that will get a value from a specified function
    when it plays.
    """

    def __init__(self, function, *args, **kw):
        ValueObject.__init__(self)
        assert callable(function)
        self.function = function
        self.args = args
        self.kw = kw
        
    def getValue(self):
        return self.function(*self.args, **self.kw)
    

class ValueGenerator:
    """
    Object producing interpolating values over an interval.
    The generator has to be callable and has to return a value for a given
    input value. This input value is usually a fraction of an interval ranging
    from 0. at the begining of the interval to 1. at the end of the interval. 
    """
    def __init__(self, generator=None):
        self.generator = None
        if generator is not None:
            self.setGenerator(generator)

    def setGenerator(self, generator):
        assert callable(generator)
        self.generator = generator
        
    def getValue(self, percentage, interval, **kw):
        if self.generator is None:
            raise ValueError("ValueGenerator has no generator set yet")
        else:
            return self.generator( *(percentage, interval), **kw)

    def clone(self):
        """
        This method returns a copy of the ValueGenerator object.
        If the generator has a .clone() method this method will be used to clone
        this ValueGenerator. Else the cloned ValueGenerator will be crated by
        pointing to the same callable as the ValueGenerator beign cloned.
        """
        try:
            generator = self.generator.clone()
        except AttributeError:
            generator = self.generator

        nvg = self.__class__(generator)
        return nvg


class LinkedList:
    """This mixin class adds 2 attributes nxtLinked and prvLinked and proviceds support for adding a linked copy using linkedCopy() and retrieving all linked copies 
"""

    def __init__(self):
        self.nxtLinked = None # next linked keyframe
        self.prvLinked = None # previous linked keyframe


    def linkedCopy(self, newLinkedObject):
        """update links to add the linkedObject
"""
        #find last linked keyframe
        lastkf = self
        while lastkf.nxtLinked is not None:
            lastkf = lastkf.nxtLinked

        # build links between last and linkedObject
        newLinkedObject.prvLinked = lastkf
        lastkf.nxtLinked = newLinkedObject


    def getAllLinked(self):
        """
        return all linked keyframes, self is always first in the returned list
        """

        kf = self
        linked = [kf,]
        while kf.nxtLinked is not None:
            kf = kf.nxtLinked
            linked.append( kf )

        kf = self.prvLinked
        if kf is None:
            return linked

        linked.append( kf )
        while kf.prvLinked is not None:
            kf = kf.prvLinked
            linked.append( kf )
        return linked
        

    def isLinked(self):
        return self.nxtLinked is not None or self.prvLinked is not None
   

class KF(LinkedList):
    """Keyframe object. This object associates a frame (i.e. time) with a value
stored in a ValueObject object.
"""
    def __init__(self, position, value):

        LinkedList.__init__(self)

        self.pos = position
        if isinstance(value, ValueObject):
            self.valueObject = value
        else:
            self.valueObject = ValueObject(value)

        self.leftInterval = None # interval object before KF
        self.rightInterval = None # interval object after KF


    def getValue(self, frame=None, interval=None):
        return self.valueObject.getValue()

        
    def setValue(self, value):
        self.valueObject.setValue(value)

        # for this keyframe and all linked ones update valGens
        for k in self.getAllLinked():
            # update value generators for left interval
            inter = k.leftInterval
            if inter:
                if inter.valGen.generator:
                    inter.valGen.generator.configure(lastVal=value)

            # update value generators for right interval
            inter = k.rightInterval
            if inter:
                if inter.valGen.generator:
                    inter.valGen.generator.configure(firstVal=value)
                    
        
    def linkedCopy(self, position):
        """update links to add the linkedObject
"""
        newkf = KF(position, self.valueObject)
        LinkedList.linkedCopy(self, newkf)
        return newkf


    def copy(self, position):
        """
        create a deep copy of a keyframe
        """
        return self.__class__(position, self.getValue())


    def equal(self, kf):
        """
        return True if kf and self have same position and same value
        """
        return self.pos==kf.pos and \
               ( (self.valueObject==kf.valueObject) or (self.valueObject.equal(kf.valueObject)) )
    

class KFAutoCurrentValue(KF):
    """Keyframe object. This object associates a frame (i.e. time) with a value
    returned or generated by AutoCurrentValueObject object.
"""
    def __init__(self, position, value):
        """
        Constructor of KFAutoCurrentValue obejct

        obj <- KFAutoCurrentValue(position, value)

        position is an integer describing the time for this keyframe
        value can be a AutoCurrentValueObject instance or an object for which
        a AutoCurrentValueObject can be created
        """
        LinkedList.__init__(self)

        self.pos = position
        if isinstance(value, AutoCurrentValueObject):
            self.valueObject = value
        else:
            self.valueObject = AutoCurrentValueObject(value)

        self.leftInterval = None # interval object before KF
        self.rightInterval = None # interval object after KF


    def getValue(self, value=None):
        if value is None:
            value = self.valueObject.getValue()
        #print "kf: ", self, self.pos, value
        inter = self.rightInterval
        if inter:
            gen = inter.valGen.generator
            if gen:
                if hasattr(gen, 'configure'):
                    try:
                        gen.configure(firstVal=value, active = True)
                        inter.active = True
                    except:
                        gen.configure(active = False)
                        inter.active = False
        inter = self.leftInterval
        if inter:
            gen = inter.valGen.generator
            if gen:
                if hasattr(gen, 'configure'):
                    try:
                        gen.configure(lastVal=value, active = True)
                        inter.active = True
                    except:
                        gen.configure(active = False)
                        inter.active = False
        return value

    def copy(self, position):
        """
        create a deep copy of a keyframe
        """
        return KFAutoCurrentValue(position, self.valueObject.actor)


class KFValueFromFunction(KF):
    """Keyframe object. This object associates a frame (i.e. time) with a value
    returned or generated by ValueFromFunctionObject object.
"""
    def __init__(self, position, function):
        """
        Constructor of KFAutoCurrentValue obejct

        obj <- KFValueFromFunction(position, function)

        position - an integer describing the time for this keyframe
        function - either a ValueFromFunctionObject instance or a callable function  for which
        a ValueFromFunctionObject can be created
        """
        KF.__init__(self, position, None)

        if isinstance(function, ValueFromFunctionObject):
            self.valueObject = function
        else:
            self.valueObject = ValueFromFunctionObject(function)


    def getValue(self):
        value = self.valueObject.getValue()
        inter = self.rightInterval
        if inter:
            gen = inter.valGen.generator
            if gen:
                if hasattr(gen, 'configure'):
                    gen.configure(firstVal=value)
        inter = self.leftInterval
        if inter:
            gen = inter.valGen.generator
            if gen:
                if hasattr(gen, 'configure'):
                    gen.configure(lastVal=value)

        return value



    def copy(self, position):
        """
        create a deep copy of a keyframe
        """
        return self.__class__(position, self.valueObject.function)

            
class Interval(LinkedList):
    """Class representing an interval to the right of the keyframe k1
"""
    def __init__(self, k1=None, k2=None, valGen=None, generator=None, **kw):
        """
        Interval constructor

        interval <- Interval(k1=None, k2=None, valGen=None, generator=None)

        If k1 and k2 are specified that has to be instances of KF objects
        If valGen is specified it has to be an instance of ValueGenerator
        if valGen is NOT specified and generator is specified, a ValueGenerator
        object is built and generator is set as the generator for this
        ValueGenerator
        """
        LinkedList.__init__(self)

        self.kf1 = None
        self.kf2 = None
        self.getValue = self._getValue0KF

        if valGen is None:
            self.valGen = ValueGenerator(generator)
        else:
            assert isinstance(valGen, ValueGenerator)
            self.valGen = valGen


        #self.setKF1(k1)
        #self.setKF2(k2)
        self.setKeyFrames(k1, k2)

        self.active = True # when false this interval deos not set values

        self.data = kw.copy() # used to propagate data such as rotation angle


    def setActive(self, value):
        assert value in [True, False, 0, 1]
        self.active = bool(value)


    def setGetValueMethod(self):
        """
        select getValue method depending on the keyframes that are defined
        """
        if self.kf2 is None and self.kf1 is None:
            self.getValue = self._getValue0KF

        elif self.kf1 is not None and self.kf2 is None:
            self.getValue = self._getValue1KF
            
        elif self.kf1 is not None and self.kf2 is not None:
            self.getValue = self._getValue2KF
        else:
            self.getValue = self._getValue0KF


    def setKF1(self, k1):
        """
        set first keyframe
        """
        assert k1 is None or isinstance(k1, KF)
        self.kf1 = k1
        if k1 is not None:
            k1.rightInterval = self

            val  = k1.getValue()
            if val is not None:
                if self.valGen.generator:
                    gen = self.valGen.generator
                    if hasattr(gen, 'configure'):
                        gen.configure(firstVal=val)

        self.setGetValueMethod()


    def setKF2(self, k2):
        """
        set second keyframe
        """
        assert k2 is None or isinstance(k2, KF)
        self.kf2 = k2
        if k2 is not None:
            k2.leftInterval = self

            val  = k2.getValue()
            if val is not None:
                if self.valGen.generator:
                    gen = self.valGen.generator
                    if hasattr(gen, 'configure'):
                        gen.configure(lastVal=val)

        self.setGetValueMethod()


    def setKeyFrames(self, k1, k2):
        """set both keyframes """
        assert k1 is None or isinstance(k1, KF)
        assert k2 is None or isinstance(k2, KF)
        self.kf1 = k1
        self.kf2 = k2
        if k1 is not None and k2 is not None:
            k1.rightInterval = self
            k2.leftInterval = self
            if self.valGen.generator:
                gen = self.valGen.generator
                if hasattr(gen, 'configure'):
                    val1  = k1.getValue()
                    val2 =  k2.getValue()
                    if val1 is not None and val2 is not None:
                        gen.configure(firstVal=val1, lastVal=val2)
                    elif val1 is not None:
                        gen.configure(firstVal=val1)
                    elif val2 is not None:
                        gen.configure(lastVal=val2)
            self.setGetValueMethod()
        elif k1 is not None:
            self.setKF1(k1)
        elif k2 is not None:
            self.setKF2(k2)
        

    def setValGen(self, valGen):
        """
        set the interval's value generator
        """

        assert valGen is None or isinstance(valGen, ValueGenerator)
        self.valGen = valGen


    def setValGenGenerator(self, generator):
        """
        set the value generator function in the interval's value generator object
        """

        self.valGen.setGenerator(generator)
        
        # set the keyframes to for the generator to be configured
        if self.kf1:
            generator.configure(firstVal=self.kf1.getValue())
        if self.kf2:
            generator.configure(lastVal=self.kf2.getValue())


    def linkedCopy(self, position):
        """Returns a linked interval with linked keyframes and pointing to the same calue generator than the original interval.
"""
        oldpos1 = self.kf1.pos
        k1l = self.kf1.linkedCopy(position)
        if self.kf2 is not None:
            k2l = self.kf2.linkedCopy(self.kf2.pos + (position-oldpos1))
        else:
            k2l = None
        newInt = Interval( k1l, k2l, self.valGen )

        LinkedList.linkedCopy(self, newInt)

        return newInt


    def _getValue2KF(self, frame):
        """intervals with 2 keyframes return a value generated by the interval value generator"""
        if self.active:
            first = self.kf1.pos
            nbFrames = float(self.kf2.pos - first) + 1
            #print 'AAA', frame, nbFrames
            if frame==self.kf2.pos:
                fraction = 1.0
            else:
                fraction = (frame-first)/(nbFrames-1)

            #try:
            #    return self.valGen.getValue(fraction, h, dy)
            #except:
            return self.valGen.getValue( fraction, self )
        else:
            return None

    
    def _getValue1KF(self, frame):
        """open ended intervals return value of starting keyfram"""
        if self.active:
            return self.kf1.getValue()
        else:
            return None

            
    def _getValue0KF(self, frame):
        """intervals with no keyframes return None"""
        return None

    
    def getValue(self, frame):
        """
        Retuns the value for the given frame.
        The value is only returned if the interval is active.
        This frame has to be withing the 2 keyframes of the interval,
        else we raise a ValueError.
        If the interval has no second keyframe, we return the value of the
        first keyframe.
        """
        # this method is overriden when keyframes are set
        pass
    
