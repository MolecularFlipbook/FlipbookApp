##
##  Author Michel F. Sanner Jan 2009
##
import types, weakref
from Scenario2.actions import Actions
from Scenario2.keyframes import KF, Interval
from Scenario2.datatypes import DataType
from Scenario2.interpolators import Interpolator, BehaviorList

class Actor:
    """
    An Actor is an object that will modify an attribute of a Python Object
    over the course of time.

    Actions performed by the actor are represented by keyframes (representing a
    value at a given time), and intervals that can interpolate values between
    keyframes.
    
    Actors are stored in MultipleActorActions objects.

    An Actor is created with:
    - a name
    - a given Python object
    optionally:
    - an initial value
    - a datatype used to validate value for keyframes
    - default value generator function which defined how the value will modified
     by default in Intervals

     When an actor is created its Actions object is empty.

     Actors can be made active/inactive for playback.

     Actors that know how to retrieve the value from the Python object
     can be made active/inactive for recording keyframes.
     """

    _easeInOutDict = {'none':(0,0),
                      'ease in':(1,0),
                      'ease out':(0,1),
                      'ease in and out':(1,1)}


    def __init__(self, name, object, initialValue=None, datatype=None,
                 interp=None):

        self.printValuesWhenSetting = False # set to True to debug
        self.object = object
        self.name = name # actor name, has to be unique in Director.actors
        self.interp = interp
        self.initialValue = initialValue
        self.hasGetFunction = False # set to true is actor knows how to get the
                                    # value from the object
        self.recording = False # true if this actor will record keyframes
        self.playing = True  #true if the actor will set the values
        
        self._maa = None # becomes a weakref to MAA when added to MAA

        self.easeIn = False
        self.easeOut = False

        if datatype is not None:
            assert issubclass(datatype, DataType)
            self.datatype = datatype()
        else:
            self.datatype = None

        self.actions = Actions()
        self.actions.actor = weakref.ref(self)
        
        self.nbvar = None    # number of variable that are interpolated
        self.varnames = []
        self.activeVars = [] # list of booleans allowing to turn particular
                             # variables on or off
        self.interpClass = None
        args = (initialValue, initialValue)
        kw = {}
        interpolator = None
        if interp is not None:
            try:
                interpClass, args, kw = interp
                assert issubclass(interpClass, Interpolator)
                assert isinstance(args, tuple)
                assert isinstance(kw, dict)
            except TypeError:
                interpClass = interp
                assert issubclass(interpClass, Interpolator)

            interpolator = interpClass( *args, **kw) 
            self.interpClass = interpClass
            
            self.nbvar = interpClass.nbvar
            self.varnames = interpClass.varnames
            if self.nbvar:
                self.activeVars = [1]*self.nbvar

        self.behaviorList = bl = BehaviorList( *args, **{'actor':self})
        if interpolator:
            bl.addBehavior(interpolator)
            bl.configure(active = False)

        if initialValue is not None:
            kf0 = KF(0, initialValue)
            self.actions.addKeyframe(kf0)

        # FIXME .. check variable below to see if needed
        self.preStep_cb = None
        self.postStep_cb = None

        # GUI variable
        self.visible = True
        self.displayFunction = False
        self.graphHeight = 40
        self.valueFormat = None
        self.scenarioname = None

        
    def addIntervals(self, intervals, generator=None, check=True):
        """
        add a list of intervals to the actions. Intervals can be Interval
        Objects or pairs of KFs that can be specified as KF objects or
        (position, value) pairs
        """
        maxPos = 0
        actions = self.actions
        for inter in intervals:
            if isinstance(inter, Interval):
                if inter.valGen.generator is None:
                    inter.setValGenGenerator(self.behaviorList.clone())

                if inter.kf2.pos > maxPos:
                    maxPos = inter.kf2.pos
            else:
                kf1, kf2 = inter
                if not isinstance(kf1, KF):
                    kf1 = KF( *kf1 )
                if not isinstance(kf2, KF):
                    kf2 = KF( *kf2 )

                if kf2.pos > maxPos:
                    maxPos = kf2.pos

                if generator is None:
                    generator = self.behaviorList.clone()

                inter = Interval(kf1, kf2, generator=generator)

            val = actions.addInterval( inter )
            if val is False:
                return False
        
        if self._maa:
            if self._maa().getLastFrame() <= maxPos:
                self._maa().updateEndFrame( maxPos )

        return True
    

    def addKeyframe(self, kf):
        """
        None <- addKeyframe(kf)
        Adds the keyframe 'kf' to the actor's actions object
        """
        self.actions.addKeyframe(kf)
        if self._maa:
            if self._maa().getLastFrame() <= fk.pos:
                self._maa().updateEndFrame( frame )


    def addActionsAt(self, srcActions, position, check=True):
        """
        Add the actions srcActions at the given position to the actor's
        actions object. This method will add the Actor'; default value
        generator to any interval that does not have one.

        None <- actor.addActionsAt(actions, position, check=True)

        Input:
            arcAction: Actions object
            position: an integer specifying at which frame the srcAction will
                      be added
            Check: boolean

        Method used to add actions to to an actor. For every interval
        that has no value generator, this method will set it to the actor's
        default VG, and then call self.actions.addActions(actions, check) to
        add the keyframes and intervals in actions to the actor's actions.
        """
        for i in srcActions.intervals:
            if i.valGen.generator is None:
                i.setValGenGenerator(self.behaviorList.clone())
            else:
                pass # FIXME check is valgen is ok for this actor

        self.actions.addActionsAt(srcActions, position, check=check)

        
    def getLastKeyFrame(self):
        """
        KF <- actor.getLastKeyFrame()
        
        Return the last keyframe ni the actor's actions object
        """
        if len(self.actions.keyframes):
            return self.actions.keyframes[-1]
        else:
            return None

    def onAddToDirector(self):
        pass


    def setValueAt(self, frame, off=0):
        """
        None <- setValueAt(frame, off)
        argumets: frame - position in time;
                  off - offset value.
        Set the value at specified frame to the object's animated attribute.
        """
        # is called at each time step if the actor's readMode is active
        from SimPy.Simulation import now
        print 'setting ', self.name, 'for', self.name, 'at:', frame


    def setValue(self, value):
        """
        None <- setValue(value)
        set the value on the object
        """
        # is called at each time step if the actor's readMode is active
        from SimPy.Simulation import now
        print 'setting ', self.name, 'for', self.name, 'at:', now(), 'to', value


    def setEaseIn(self, val):
        """
        None <- setEaseIn(val)
        Set easeIn atribute of all value generators in the actions 
        object to the specified value (val).
        val can be 0, 1, True of False
        """ 
        assert val in [0, 1, True, False]
        self.behaviorList.easeIn = val
        for inter in self.actions.intervals:
            inter.valGen.generator.easeIn = val


    def setEaseOut(self, val):
        """
        None <- setEaseOut(val)
        Set easeOut atribute of all value generators in the actions 
        object to the specified value (val).
        val can be 0, 1, True of False
        """ 
        assert val in [0, 1, True, False]
        self.behaviorList.easeOut = val
        for inter in self.actions.intervals:
            inter.valGen.generator.easeOut = val


    def setEaseInOut(self, val):
        """
        None <- setEaseInOut(val)
        Set easeIn and easeOut atributes of all value generators in the actions 
        object.
        val can be :
           'none'             set easeIn and easeOut to 0,
           'ease in'          easeIn = True, easeOut = False,
           'ease out'         easeIn = False, easeOut = True,
           'ease in and out'  easeIn = True , easeOut = True
        """ 
        easeIn, easeOut = self._easeInOutDict[val]
        #print 'setting ease for actor', self.name, easeIn, easeOut
        self.setEaseIn(easeIn)
        self.setEaseOut(easeOut)


    def clone(self):
        """newActor <- clone()
        Return a copy of the actor (self).
        The method calls self.__class__ method. It then clones self.behaviorList and
        assignes the cloned copy to newActor.behaviorList.
        """
        if self.datatype is not None:
            dt = self.datatype.__class__
        else:
            dt = None
        newActor = self.__class__(self.name, self.object, initialValue=self.initialValue,
                                  datatype=dt, interp=self.interp)
        newActor.behaviorList = self.behaviorList.clone()
        return newActor



class CustomActor(Actor):
    """
    Custom actors are actors for which a setMethod or setFunction and a
    getFunction allowing set and get the value of the atrribute in the
    Python object that is driven by the actor can be set and gotten
    """
    def __init__(self, name, object, initialValue=None, datatype=None,
                 interp=None, setFunction=None, setMethod=None,
                 getFunction=None):
        """
Constructor of the Actor object,

arguments:
    object:            Python object on which to operate
    name:              Name of this Actor,  This name has to be unique
                       among the list of ActorDescriptor in an Director
    setFunction:       function to called at each time step.
                       The function will be called using  func(*(actor,value))
    setMethod:         method of the obect to be called at each time step.
                       The function will be called using  obj.method(value)
    getFunction=None:  [optional] function that can be called to get the
                       current value of the attribute managed by this actor
                       The function and its arguments have to be specified as a
                       3-tuple (func, *args, **kw). It will be called using
                       func(*(object,)+args), **kw) if it is a function
                       or func(*args, **kw) if it is a method
   interp              interpreter class
   initialValue        initial value of the attribute
   dataType            type of the attribute value 
   """
        
        self.getFuncTuple = None
        self.hasGetFunction = False
        if setFunction:
            assert callable(setFunction)
        self.setFunction = setFunction

        if setMethod:
            method = getattr(object, setMethod)
            assert callable(method)
        else:
            method = None
        self.setMethod = method

        if getFunction:
            self.getFuncTuple = self.checkFunction(getFunction)
            
        self.object = object
        if initialValue is None:
            if self.getFuncTuple:
                initialValue = self.getValueFromObject()

        Actor.__init__(self, name, object, datatype=datatype,
                       initialValue=initialValue, interp=interp)

        if self.getFuncTuple:
            self.hasGetFunction = True


    def clone(self):
        """newActor <- clone()
        Return a copy of the actor (self).
        The method calls self.__class__ method. It then clones self.behaviorList and
        assignes the cloned copy to newActor.behaviorList.
        """
        
        if self.setMethod is not None:
            setMethod = self.setMethod.__name__
        else:
            setMethod = None

        newActor = self.__class__(self.name, self.object, initialValue=self.initialValue,
                                  datatype=self.datatype.__class__, interp=self.interp,
                                  setFunction=self.setFunction, setMethod=setMethod,
                                  getFunction=None)
        newActor.getFuncTuple = self.getFuncTuple
        if self.getFuncTuple:
            newActor.hasGetFunction = True

        newActor.behaviorList = self.behaviorList.clone()
        return newActor


    def checkFunction(self, function):
        """
        Check if the specified 'function' is eather:
        1.callable function.
          Returned value will be a tuple: (function, (), {}).
             
        2.tuple: (function, (args), {kw}),
          where args is the function's arguments (tuple) ,
          kw - keywords dictionary.
          Returned value : (function, (args), {kw}).
        """
        # check that functionTuple is of form (func, (), {})
        try:
            f, args, kw = function
            assert callable(f)
            assert isinstance(args, tuple)
            assert isinstance(kw, dict)
        except TypeError:
            assert callable(function)
            f, args, kw = function, (), {}
        return f, args, kw

   
    def getValueFromObject(self):
        """
        value <- getValueFromObject()
        Get the current value of the animated attribute from the object
        and return it.
        """
        if not self.getFuncTuple:
            return None
        f, args, kw = self.getFuncTuple
        if type(f) == types.FunctionType or type(f) == types.BuiltinFunctionType:
            # add object as first argument to functions
            return f(*(self.object,)+args, **kw)
        elif type(f) == types.MethodType:
            return f(*args, **kw)


    def setValue(self, value):
        """
        None <- setValue(value)
        Call the self.setFunction() to set the value on the object.
        If set.selfFunction is None, this method will call self.setMethod() instead
        (if it is not None).
        """
        if self.setFunction:
            self.setFunction( *(self, value) )
        elif self.setMethod:
            self.setMethod(value)


    def setValueAt(self, frame, off):
        """
        None <- setValueAt(frame, off)
        argumets: frame - position in time;
                  off - offset value.
        The method first gets a value (at specified frame and offset) from the actions object.
        It then sets the value on the object with self.setValue() call. 
        """
        # call the function to set the value on the object
        value = self.actions.getValue(frame-off)

        if value != 'Nothing There':
            self.setValue(value)
