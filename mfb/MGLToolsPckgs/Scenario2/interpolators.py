## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

##
##  Authors:  Michel Sanner, Anna Omelchenko May 2007
##
"""
This module implements a variety of interpolator objects.

An interpolator object has values for the first and last positions (firstVal , lastVal).
This object implements the getValue(fraction) which will return
the value corresponding to the the position (a fraction of the range 0.0 ... 1.0)
"""
import numpy.oldnumeric as Numeric
from math import acos, sqrt, sin, cos, pi
from copy import copy
import weakref
import types
import warnings

class BehaviorList:
    """Class containing a list of behavior objects applied sequentially"""
    nbvar = None
    def __init__(self, firstVal, lastVal, actor=None, active=True):
        self.firstVal = None 
        self.lastVal = None 
        self.behaviors = []
        self.configure(firstVal = firstVal, lastVal = lastVal, active = active)
        self.actor= None
        if actor:
            self.actor = weakref.ref(actor)
        self.valueFormat = None
        self.active = active
        self.easeIn = False
        self.easeOut = False
        self.constant = False


    def clone(self):
        instance = self.__class__(self.firstVal, self.lastVal, active = self.active)
        instance.easeIn = self.easeIn
        instance.easeOut = self.easeOut        
        instance.constant = self.constant
        for b in self.behaviors:
            instance.addBehavior(b.clone())
        return instance

    
    def addBehavior(self, behavior = None, behaviorClass = None):
        if behavior:
            assert isinstance(behavior, Interpolator)
            nbvar = behavior.nbvar
        else:
            assert issubclass(behaviorClass, Interpolator)
            nbvar = behaviorClass.nbvar
            behavior =  behaviorClass(self.firstVal, self.lastVal)
        if behavior:
            if self.nbvar is not None:
                if nbvar is not None:
                    if self.nbvar != nbvar:
                        warnings.warn("Cannot add behavior - expected %d number of variables, got %d"%(self.nbvar, nbvar))
                        return False
            self.behaviors.append(behavior)
            if behavior.valueFormat is not None:
                self.valueFormat = behavior.valueFormat
            behavior.behaviorList = weakref.ref(self)
        return True


    def removeBehavior(self, behavior):
        try:
            self.behaviors.remove(behavior)
            del behavior.behaviorList
        except ValueError:
            pass


    def getValue(self, fraction, interval, **kw):

        #print "behaviorList,easeIn-Out",  self.easeIn , self.easeOut 
        if len(self.behaviors)==0:
            return None
        else:
            value = self.behaviors[0].getValue(fraction, interval)
            for b in self.behaviors[1:]:
                value = b.getValue(fraction, interval, value=value)
            return value


##         if len(self.behaviors)==0:
##             return None
##         else:
##             # alter fraction based on easeIn easeOut
##             if not self.constant and (self.easeIn or self.easeOut):
##                 #print 'EASE 1 ', fraction, 
##                 if self.easeIn and self.easeOut :
##                     #print "easeIn and easeOut"
##                     fraction = (sin(pi*.5*(fraction*2-1))+1)*.5
##                 elif self.easeIn:
##                     #print "easeIn"
##                     fraction = 1.0 - cos(pi*.5 * fraction)
##                 elif self.easeOut:
##                     #print "easeOut"
##                     fraction = sin(pi*.5 * fraction)
##                 #print fraction

##             value = self.behaviors[0].getValue(fraction, interval)
##             for b in self.behaviors[1:]:
##                 value = b.getValue(fraction, interval, value=value)
##             if not (self.constant and (self.easeIn or self.easeOut)):
##                 print 'noeaseinout', fraction, value
##             #print 'in behavior', fraction, value, len(self.behaviors)

##             # for constant interpolation alter value based on easeIn easeOut

##             # constant is used for rotation because each time we get here]
##             # the value get incremented by the same amount (self.firstVal)

##             # the multiplicative factors (2 and 4/3) are comouted so that
##             # the integral remians the same (i.e.) if no ease in or out
##             # we get self.firstVal * nbFrames to reach the desired rotation
##             # if we have ease in we have to accelerate linearly up to the
##             # middle of the interval and then stay constant in such a way
##             # that the sum of all increments is equal to self.firstVal*nbFrames

##             # for some reason we are always short by 0.5*(4/3) on ease in only
##             # and long by 0.5*(4/3) on ease out only. So we special case and
##             # add .5 to ease in on the last frame and start with .5 on ease out
##             if self.constant and (self.easeIn or self.easeOut):
##                 fv = self.firstVal
##                 valtype = type(fv)
##                 if valtype == types.ListType or valtype == types.TupleType:
##                     fv = Numeric.array(fv)

##                 if self.easeIn and self.easeOut :
##                     if fraction<0.5:
##                         value = 2*fv*2*fraction
##                     else:
##                         value = 2*fv*2*(1.-fraction)
##                     print "easeInOut", fraction, value, fv
##                 elif self.easeIn:
##                     #if fraction==1.0:
##                     #    value = 1.5*(4./3.)*fv
##                     #else:
##                     if fraction<=0.5:
##                         #value = 2*(4./3.)*fv*fraction
##                         value = dy*fraction
##                     else:
##                         value = h*fraction
##                         #value = (4./3.)*fv
##                     print "easeIn", fraction, value, fv
##                 elif self.easeOut:
##                     #if fraction==0.0:
##                     #    value = .5*(4./3.)*fv*(1.- fraction)
##                     #else:
##                     if fraction>0.5:
##                         value = 2*(4./3.)*fv*(1.- fraction)
##                     else:
##                         value = (4./3.)*fv
##                     print "easeOut", fraction, value, fv
                    
##             return value


    def testKW(self, **kw):
        options = ["firstVal", "lastVal", "active"]
        for k in kw.keys():
            assert k in options
            
    def configure(self, **kw):
        self.testKW(**kw)
        firstVal = kw.get("firstVal")
        lastVal = kw.get("lastVal")
        if firstVal is not None and lastVal is not None:
           self.firstVal = firstVal
           self.lastVal = lastVal
           for b in self.behaviors:
                if b is not None:
                    b.configure(firstVal=firstVal, lastVal=lastVal)
        elif firstVal is not None:
            self.firstVal = firstVal
            for b in self.behaviors:
                if b is not None:
                    b.configure(firstVal=firstVal)

        elif lastVal is not None:
            self.lastVal = lastVal
            for b in self.behaviors:
                if b is not None:
                    b.configure(lastVal=lastVal)
        try:
            nbvar1 = len(self.firstVal)
        except:
            nbvar1 = 1
        try:
            nbvar2 = len(self.lastVal)
        except:
            nbvar2 = 1
        self.nbvar = max(nbvar1, nbvar2)
        active = kw.get("active")
        if active is not None:
            self.active = active
            for b in self.behaviors:
                if b is not None:
                    b.configure(active=active)

        
    def formatValue(self, value):
        if self.valueFormat:
            if type(self.valueFormat) == types.MethodType:
                return self.valueFormat(value)
            else:
                return self.valueFormat%value
        else:
            return str(value)

    def __call__(self, fraction, interval, **kw):
        return self.getValue( *(fraction, interval), **kw)
    

class Interpolator:
    """
Base class for all interpolators.

The getValue method has to be implemented to compute the appropriate value
"""
    nbvar = 1
    varnames = ['variable 1']
    valueFormat = None
    
    def __init__(self, firstVal, lastVal, interpolation = 'linear', active = True):
        self.action = None # will be a weakref to the action this interpolator
                           # is associated with
        self.firstVal = None
        self.lastVal = None
        self.interpolation = interpolation
        self.behaviorList = None
        self.configure(firstVal = firstVal, lastVal = lastVal,
                       interpolation = interpolation, active = active)
        

    def clone(self):
        return self.__class__(self.firstVal, self.lastVal,
                              self.interpolation, active = self.active )

    def testKW(self, **kw):
        options = ["firstVal", "lastVal", "active", "interpolation", "interpolators"]
        for k in kw.keys():
            assert k in options
    
    def configure(self, **kw):

        #print "Interpolator, configure", kw
        self.testKW(**kw)
        firstVal = kw.get("firstVal")
        updateVR = False
        if firstVal is not None:
            self.firstVal = self.cast(firstVal)
            updateVR = True
        lastVal = kw.get("lastVal")
        if lastVal is not None:
            self.lastVal = self.cast(lastVal)
            updateVR = True
        interp = kw.get("interpolation")
        if interp is not None:
            self.interpolation = interp
        if updateVR:
            if self.firstVal is not None and self.lastVal is not None:
                self.valueRange = self.getValueRange()
        try:
            nbvar1 = len(self.firstVal)
        except:
            nbvar1 = 1
        try:
            nbvar2 = len(self.lastVal)
        except:
            nbvar2 = 1
        self.nbvar = max(nbvar1, nbvar2)
        active = kw.get("active")
        if active is not None:
            self.active = active


    def getValueRange(self):
        #print "getValueRange of Interp."
        #return self.lastVal - self.firstVal
        return None


    def getValue(self, fraction, interval, **kw):
        """This method has to return the right value for a fraction ranging
        between 0.0 and 1.0.
        For fraction 0.0 or less it should return self.startValue
        For fraction 1.0 or more it should return self.startValue
        """
        return fraction
        

    def cast(self, value):
        # function used by getValue to return the proper type
        return value


    def ease(self, fraction, interval):
        # computes new fraction for easeIn/easeOut.

        easeIn = False
        easeOut = False
        if self.behaviorList is not None:
            bl = self.behaviorList()
            easeIn = bl.easeIn
            easeOut = bl.easeOut
        if not easeIn and not easeOut:
            return fraction

        # a and b - times to control easeIn and easeOut (in range 0...1)
        # easeIn occurs from time 0 to time a.
        # easeOut occurs from time b to time 1.

        if not interval.data.has_key('easeInEnd'):
            easeInEnd = interval.data['easeInEnd'] = 0.3
        else:
            easeInEnd =  interval.data['easeInEnd']

        if not interval.data.has_key('easeOutStart'):
            easeOutStart = interval.data['easeOutStart'] = 0.7
        else:
            easeOutStart = interval.data['easeOutStart']
        if easeIn and easeOut:            
            a = easeInEnd
            b  = easeOutStart
            #print "easeIn-Out"
        elif easeIn:
            a = easeInEnd 
            b = 1.0
            #print "easeIn"
        else : #easeOut
            #print "easeOut"
            a = 0.0
            b = easeOutStart
            
        v0 = 2/(1+b-a)          # constant velocity attained
        if fraction<=a:
            if a==0:
                return 0
            else:
                d = v0*fraction*fraction/(2*a);
        else:
            d = v0*a/2
            if fraction<=b:
                d += (fraction-a)*v0
            else:
                d += (b-a)*v0
                d += (fraction-fraction*fraction/2-b+b*b/2)*v0/(1-b)

        return d # distance from 0 in range(0, 1)




    def __call__(self, fraction, interval, **kw):
        return self.getValue( *(fraction, interval), **kw)

##     def formatValue(self, value):
##         if self.valueFormat:
##             return self.valueFormat%value
##         else:
##             return str(value)


class noise3F(Interpolator):
    nbvar = 3
    def getValue(self, fraction, interval, value=None, **kw):
        if value is not None:
            if fraction <= 0.0 or fraction >= 1.0:
                return value
            else:
                from random import random as r
                return [value[0]+r(), value[1]+r(), value[2]+r()]


    
class speedUp3F(Interpolator):
    nbvar = 3
    def getValue(self, fraction, interval, value=None, **kw):
        bl = self.behaviorList()
        v1 = bl.firstVal
        v2 = bl.lastVal
        v = [v2[0]-v1[0],v2[1]-v1[1],v2[2]-v1[2]]
        #print fraction, v1, v2, v
        return [v1[0]+fraction*v[0], v1[1]+fraction*v[1], v1[2]+fraction*v[2]]



class noise(Interpolator):
    nbvar = None
    def getValue(self, fraction, interval, value=None, **kw):
        if value is not None:
            if fraction <= 0.0 or fraction >= 1.0:
                return value
            else:
                from random import random as r
                return  map(lambda x: x+r(), value)

            

            

class ScalarInterpolator(Interpolator):
    """ class for performing linear interpolations on scalar values """
    nbvar = None
    
    def __init__(self, firstVal, lastVal, interpolation='linear', active=True):
        
        Interpolator.__init__(self, firstVal, lastVal,
                              interpolation = interpolation, active=active)


    def getValueRange(self):
        #print "getValueRange of Interp."
        if self.lastVal is not None and self.firstVal is not None:
            return self.lastVal - self.firstVal
        else:
            return None

    def getValue(self, fraction, interval, **kw):
        """return the value for a fraction of the range"""
        if self.firstVal == None or self.lastVal == None:
            return None
        if fraction <= 0.0:
            return self.cast(self.firstVal)
        elif fraction >= 1.0:
            return self.cast(self.lastVal)
        else:
            if self.interpolation=='linear':
                fraction = self.ease(fraction, interval)
                return self.cast(self.firstVal +
                                 self.valueRange*fraction)
            else:
                print 'spline interpolation not yet implemented'


class IntScalarInterpolator(ScalarInterpolator):

    def cast(self, value):
        return int(round(value))



class FloatScalarInterpolator(ScalarInterpolator):
    valueFormat = "%.2f"
    
    def cast(self, value):
        return float(value)



class VarScalarInterpolator(Interpolator):
    """
    This class can handle interpolating between a scalar value and a sequence
    of values .
    Example : firstVal = v1, lastVal = [ v21, v22, ..., v2n]

    getValue(fraction) method returns a list containing either 1 or n values for
    specified fraction.
"""
    nbvar = None
    
    def __init__(self, firstVal, lastVal, interpolation='linear', active=True):
        
        Interpolator.__init__(self, firstVal, lastVal,
                              interpolation = interpolation, active=active)

        
    def getValueRange(self):
        # compute value range
        valueRange = []
        try:
            len(self.firstVal)
        except:
            self.firstVal = [self.firstVal]
            if self.behaviorList is not None:
                self.behaviorList().firstVal = [self.firstVal]
        try:
            len(self.lastVal)
        except:
            self.lastVal = [self.lastVal]
            if self.behaviorList is not None:
                self.behaviorList().lastVal = [self.lastVal]
        val1 = self.firstVal
        val2 = self.lastVal
        if len(val1) == 1 and len(val2) > 1:
            val1 = list(val1)*len(val2)
        elif len(val2) == 1 and len(val1) > 1:
            val2 = list(val2)*len(val1)
        vlist = []
        for v1,v2 in zip(val1, val2):
            vlist.append( v2 - v1 )
        return vlist
        
    def getValue(self, fraction, interval, **kw):
        """return the value for a fraction of the range"""
        if self.firstVal == None or self.lastVal == None:
            return None
        if fraction <= 0.0:
            return self.cast(self.firstVal)
        elif fraction >= 1.0:
            return self.cast(self.lastVal)
        else:
            if self.interpolation=='linear':
                fraction = self.ease(fraction, interval)
                if len(self.firstVal) == 1 and len(self.valueRange) > 1:
                    firstVal = list(self.firstVal)*len(self.valueRange)
                else:
                    firstVal = self.firstVal
                return self.cast(map(lambda v1, v2, s=fraction:\
                        v2+s*v1, self.valueRange, firstVal))
            else:
                print 'spline interpolation not yet implemented'



class  IntVarScalarInterpolator(VarScalarInterpolator):
    
    def cast(self, value):
        newval = []
        try:
            len(value)
        except:
            value = [value]
        for v in value:
            newval.append( int(round(v)))
        return newval


        
class  FloatVarScalarInterpolator(VarScalarInterpolator):
    valueFormat = "%.2f"    
    def cast(self, value):
        newval = []
        try:
            len(value)
        except:
            value = [value]
        for v in value:
            newval.append( float(v) )
        return newval


class VectorInterpolator(Interpolator):
    """
    class for performing linear interpolations on vectors of arbitrary length
    Example: firstVal = [v1, v2,....vn], lastVal=[v1, v2,....vn]
    """
    nbvar = None
    
    def __init__(self, firstVal, lastVal, interpolation='linear', active=True):
        
        Interpolator.__init__(self, firstVal, lastVal,
                              interpolation = interpolation, active=active)

        
    def getValueRange(self):
        # compute value range
        #print "getValueRange of vector Interp."
        valueRange = []
        for v1,v2 in zip(self.firstVal, self.lastVal):
            valueRange.append( v2 - v1 )
        return valueRange


        
    def getValue(self, fraction, interval, **kw):
        """return the value for a fraction of the range"""
        if self.firstVal == None or self.lastVal == None:
            return None
        if fraction <= 0.0:
            return self.cast(self.firstVal)
        elif fraction >= 1.0:
            return self.cast(self.lastVal)
        else:
            if self.interpolation=='linear':
                fraction = self.ease(fraction, interval)
                return self.cast(map(lambda x, off, s=fraction:\
                        off+s*x, self.valueRange, self.firstVal))
            else:
                print 'spline interpolation not yet implemented'



class IntVectorInterpolator(VectorInterpolator):
    """Handles interpolation of vectors of integer type"""

    def cast(self, value):
        if isinstance(value, Numeric.ArrayType):
            newvalue = value.astype('i')
        else:
            newvalue = []
            for val in value:
                newvalue.append(int(round(val)))
        return newvalue



class FloatVectorInterpolator(VectorInterpolator):
    """Handles interpolation of vectors of float type"""
    
    valueFormat = "%.2f"    
    def cast(self, value):
        if isinstance(value, Numeric.ArrayType):
            newvalue = value.astype('f')
        else:
            newvalue = []
            for val in value:
                newvalue.append(float(val))
        return newvalue

    
class VarVectorInterpolator(Interpolator):
    """
    class for performing linear interpolations on vector sequences of arbitrary length. 
    This can handle interpoalting between an array with shape (1, n) and an array with
    shape (N, n). 
    Example : firstVal = [ [v1, v2,..,vn] ],  lastVal = [ [v11, v12,..,v1n],...,[vN1, vN2,..,vNn] ] 
    """
    nbvar = None
    valueFormat = "%.2f"
    
    def __init__(self, firstVal, lastVal, interpolation='linear', active=True):
        
        Interpolator.__init__(self, firstVal, lastVal, interpolation = interpolation,
                              active=active)

    
    def getValueRange(self):
        # compute value range
        self.firstVal= Numeric.array(self.firstVal, 'f')
        self.lastVal= Numeric.array(self.lastVal, 'f')
        return self.lastVal - self.firstVal     

            
    def getValue(self, fraction, interval, **kw):
        """return the value for a fraction of the range"""
        if self.firstVal == None or self.lastVal == None:
            return None
        if fraction <= 0.0:
            return self.cast(self.firstVal)
        elif fraction >= 1.0:
            return self.cast(self.lastVal)
        else:
            if len(self.firstVal)==1 and len(self.valueRange)>1:
                # one color at begin and N colors at the end
                firstVal = Numeric.array( list(self.firstVal)*len(self.valueRange), "f" )
            else:
                firstVal = self.firstVal
            if self.interpolation=='linear':
                fraction = self.ease(fraction, interval)
                return self.cast(firstVal + self.valueRange*fraction)
            else:
                print 'spline interpolation not yet implemented'

    def cast(self, value):
        if type(value) != Numeric.ArrayType:
            return Numeric.array(value, "f")
        return value.astype("f")


class BooleanInterpolator(Interpolator):
    """class for interpolating values between 0 and 1 to boolean values True or False"""
    
    valueFormat = lambda self, x: str(x == True)
    
    def __init__(self, firstVal, lastVal, interpolation='linear', active=True):
        
        Interpolator.__init__(self, firstVal, lastVal,
                              interpolation = interpolation, active=active)
                            
        
    def getValueRange(self):
        if self.firstVal == True:
            self.firstVal = 1.0
        elif  self.firstVal == False:
            self.firstVal = 0.0
        if self.lastVal == True:
            self.lastVal = 1.0
        elif  self.lastVal == False:
            self.lastVal = 0.0
        return self.lastVal-self.firstVal

   
    def getValue(self, fraction, interval, **kw):
        if self.firstVal == None or self.lastVal == None:
            return None
        if self.firstVal:
            firstVal = 1.0
        else: firstVal = 0.0

        if self.lastVal:
            lastVal = 1.0
        else: lastVal = 0.0
        if fraction <= 0.0:
            if round(firstVal):
                return True
            else:
                return False
        elif fraction >= 1.0:
            if round(lastVal):
                return True
            else:
                return False
          
        else:
            if self.interpolation=='linear':
                if fraction < 1:
                    return {0: False, 1:True}.get(firstVal)
                else:
                    return {0: False, 1:True}.get(lastVal)
            else:
                print 'spline interpolation not yet implemented'




from mglutil.math.rotax import mat_to_quat
from mglutil.math.transformation import Transformation

class RotationInterpolator(Interpolator):
    """
    class for performing quaternion-based interpolations between rotation matrices
    described by 4x4 matrices.
    """
    nbvar = 4
    varnames = ['q1', 'q2', 'q3', 'q4'] # unit quaternion
    valueFormat = "%.2f"    

    def __init__(self, firstVal, lastVal, interpolation='linear', active=True):
        Interpolator.__init__(self, firstVal, lastVal, interpolation = interpolation,
                              active=active)
        self.invertVal = False
        

##     def cast(self, value):
##         t = Transformation(quaternion=value)
##         return t.getRotMatrix(shape=(16,), transpose=1)

        
##     def getValueRange(self):
##         # compute value ranges over all intervals
##         if len(self.firstVal)==16:
##             self.firstVal = mat_to_quat( self.firstVal ) 
##         if len(self.lastVal)==16:
##             self.lastVal = mat_to_quat( self.lastVal ) 
##         v0 = self.firstVal
##         v1 = self.lastVal
##         return (v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2], v1[3]-v0[3])
       


##     def getValue(self, fraction, interval):
##         """return the value for a fraction of the range"""
##         if fraction <= 0.0:
##             return self.cast(self.firstVal)
##         elif fraction >= 1.0:
##             return self.cast(self.lastVal)
##         x,y,z,q = self.firstVal
##         rx,ry,rz,rq = self.valueRange
##         return self.cast( (float(x + fraction*rx), float(y + fraction*ry),
##                            float(z + fraction*rz), float(q + fraction*rq)) )

    def configure(self, **kw):
        self.testKW(**kw)
        firstVal = kw.get("firstVal")
        if firstVal is not None:
            assert len(firstVal) == 4
            self.firstVal = firstVal
        lastVal = kw.get("lastVal")
        if lastVal is not None:
            assert len(lastVal) == 4
            self.lastVal = lastVal
        interp = kw.get("interpolation")
        if interp is not None:
            self.interpolation = interp
        if self.behaviorList:
            self.behaviorList().alterFunction = False
        active = kw.get("active")
        if active is not None:
            self.active = active


    def getValue(self, fraction, interval, **kw):
        # quaternion interpolation
        # http://www.euclideanspace.com/maths/algebra/realNormedAlgebra/quaternions/slerp/index.htm
        if self.firstVal == None or self.lastVal == None:
            return None
        qa = self.firstVal
        qb = copy(self.lastVal)
        #qb = self.lastVal
        self.invertVal = False
        if self.behaviorList:
            self.behaviorList().invertVal = False
            
        t = self.ease(fraction, interval)
        cosHalfTheta =  qa[0] * qb[0] + qa[1] * qb[1] + qa[2] * qb[2] + qa[3] * qb[3]
        #print "fraction:", fraction, "cosHalfTheta: ", cosHalfTheta
        #we need cosHalfTheta to be positive - invert the quaternion
        if cosHalfTheta < 0:  # ????
            qb[0] = -qb[0]; qb[1] = -qb[1]; qb[2] = -qb[2]; qb[3] = -qb[3] 
            cosHalfTheata = -cosHalfTheta
            self.invertVal = True
            if self.behaviorList:
                self.behaviorList().invertVal = True

        if abs(cosHalfTheta) >= 1.0:
            qm = [qa[0], qa[1], qa[2], qa[3]]
            return qm
        #Calculate temporary values.
        from math import acos, sqrt, fabs, sin, pi
	halfTheta = acos(cosHalfTheta)
        
	sinHalfTheta = sqrt(1.0 - cosHalfTheta*cosHalfTheta)
	# we could rotate around any axis normal to qa or qb
        if fabs(sinHalfTheta) < 0.001: #fabs is floating point absolute
            qm = [(qa[0] * 0.5 + qb[0] * 0.5), (qa[1] * 0.5 + qb[1] * 0.5),
                  (qa[2] * 0.5 + qb[2] * 0.5), (qa[3]* 0.5 + qb[3] * 0.5)]
            return qm
	ratioA = sin((1 - t) * halfTheta) / sinHalfTheta
	ratioB = sin(t * halfTheta) / sinHalfTheta
	#calculate Quaternion.
	qm = [(qa[0] * ratioA + qb[0] * ratioB), (qa[1] * ratioA + qb[1] * ratioB),
              (qa[2] * ratioA + qb[2] * ratioB), (qa[3] * ratioA + qb[3] * ratioB)]
	return qm


class CompositeInterpolator(Interpolator, object):
    """
    class for aggregating multiple interpolators
    
    the position vector is the same for all interpolators and stored in the
    CompositeInterpolator.
    The values are stored in each interpolator.
    CompositeInterpolator.values is overwriten by a property object collecting
    the values form the interpolators.
    """
    nbvar = None
    varnames = None
    
    def getFirstVal(self):
        val = []  # build list of values
        for inter in self.interpolators:
            val.append(inter.firstVal)
        return val

    
    def getLastVal(self):
        val = []  # build list of values
        for inter in self.interpolators:
            val.append(inter.lastVal)
        return val

    
    def setLastVal(self, val):
        #self.configure(values=values)
        pass


    def setFirstVal(self, val):
        pass

        
    firstVal = property(getFirstVal, setFirstVal)
    lastVal = property(getLastVal, setLastVal)

    
    def __init__(self, firstVal, lastVal, interpolation='linear', interpolators=None,
                 active=True):
        # firstVal - list of values for the first position  of each interpolator
        # lastVal -  lists of values for the last position of each interpolator
        self.interpolators = []
        self.interpolation = interpolation
        self.configure(firstVal = firstVal, lastVal = lastVal, interpolators=interpolators,
                       interpolation = interpolation, active=active)

    def configure(self, **kw):
        self.testKW(**kw)
        interpolators = kw.get("interpolators")
        firstVal = kw.get("firstVal")
        lastVal = kw.get("lastVal")
        if interpolators:
            ninterp = len(interpolators)
            if firstVal == None:
                if not len(self.firstVal):
                    firstVal = []
                    for i in range(ninterp):
                        firstVal.append(None)
                else:
                    firstVal = self.firstVal
            if lastVal == None:
                if not len(self.lastVal):
                    lastVal = []
                    for i in range(ninterp):
                        lastVal.append(None)
                else:
                    lastVal = self.lastVal
            assert len(firstVal)==len(lastVal)==len(interpolators)
            self.interpolators = []
            self.interpConfig = []
            for interpKlass, v1, v2 in zip(interpolators, firstVal, lastVal):
                interpolation = kw.get("interpolation", self.interpolation)
                interp = interpKlass(v1,v2,interpolation = interpolation)
                # replace .configure method with _configure to prevent a user
                # from accessing the interp and modifying a single one
                self.interpolators.append(interp)
                self.interpConfig.append(interp.configure)
                interp.configure = None
        else:
            if lastVal != None and firstVal != None:
                assert len(firstVal)==len(lastVal)==len(self.interpolators)
                for i in range(len(self.interpolators)):
                    self.interpConfig[i](firstVal = firstVal[i], lastVal = lastVal[i])
            elif firstVal is not None:
                assert len(firstVal) == len(self.interpolators)
                for i in range(len(self.interpolators)):
                    self.interpConfig[i](firstVal = firstVal[i])
            elif lastVal is not None:
                assert len(lastVal) == len(self.interpolators)
                for i in range(len(self.interpolators)):
                    self.interpConfig[i](lastVal = lastVal[i])
        interpolation = kw.get("interpolation")
        if interpolation is not None:
             for i in range(len(self.interpolators)):
                    self.interpConfig[i](interpolation = interpolation)
             self.interpolation = interpolation
        active = kw.get("active")
        if active is not None:
            self.active = active
        

    def getValue(self, fraction, interval, **kw):
        result = []
        for interp in self.interpolators:
            result.append(interp.getValue(fraction, interval))
        return result


class FunctionInterpolator(Interpolator):
    """
    class for performing interpolations using functions
    """
    def __init__(self, firstVal=None, lastVal=None, function=None,interpolation='linear',
                 active=True):
        """
        Constructor for an interpolator object using a function.  This object has to
        implement a getValue(fraction) method which returns a value corresponding
        to the given fraction.
        
        arguments:
        function:          function or method to called at each time step.
                           The function can be a function or a 3-tuple
                           (func, *args, **kw). It will be called using
                           func(*(value,)+args, **kw)
        firstVal, lastVal: range of x values to be mapped to the range of frames of
                           the action this interpolator is associated with.

        """
        self.valueRange = None
        Interpolator.__init__(self, firstVal, lastVal, interpolation = interpolation,
                              active=active)
        self.configure(function = function)


    def getValueRange(self):
        #print "getValueRange of Interp."
        return self.lastVal - self.firstVal
        
        
    def configure(self, **kw):
        firstVal = kw.get("firstVal")
        updateVR = False
        if firstVal is not None:
            self.firstVal = firstVal
            updateVR = True
        lastVal = kw.get("lastVal")
        if lastVal is not None:
            self.lastVal = lastVal
            updateVR = True
        function = kw.get("function")
        if function:
            self.funcTuple = self.checkFunction(function)
        interp = kw.get("interpolation")
        if interp is not None:
            self.interpolation = interp
        if updateVR:
            if self.firstVal != None and self.lastVal != None:
                self.valueRange = self.getValueRange()
        active = kw.get("active")
        if active is not None:
            self.active = active

        
    def checkFunction(self, function):
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


    def getX(self, fraction):
        if self.valueRange:
            return self.valueRange*fraction
        else:
            return None

    
    def getValue(self, fraction, interval, **kw):
        if self.valueRange:
            fraction = self.firstVal+self.valueRange*fraction
        f, args, kw = self.funcTuple
        return self.cast(f( *(fraction,)+args, **kw))



class ReadDataInterpolator(Interpolator):
    
    def __init__(self, firstVal=None, lastVal=None, function=None, nsteps=0,
                 interpolation='linear', active=True):
        self.valueRange = None
        self.function = None
        
        Interpolator.__init__(self,  firstVal, lastVal, interpolation = interpolation,
                              active=active)
        self.nsteps = nsteps
        self.configure(function = function)
        
        

    def getValueRange(self):
        return None

    def clone(self):
        return self.__class__(self.firstVal, self.lastVal, self.function,
                              nsteps = self.nsteps,
                              interpolation=self.interpolation,
                              active = self.active )


    def configure(self, **kw):
        # if firstVal or lastVal get reconfigured - we will add those values to the
        # range of values returned by function(step)
        #print "ReadDataInterpolator, configure", kw
        
        nsteps = kw.get("nsteps")
        if nsteps is not None:
            if nsteps != self.nsteps:
                self.nsteps = nsteps
        function =  kw.get("function")
        if function is not None:
            if type(function).__name__ in ('ndarray', 'list'):
                self.function = function
                self.firstVal = copy(function[0])
                self.lastVal = copy(function[-1])
                self.configure(nsteps = len(function))
            else:
                assert callable(function)
                self.function = function
                self.firstVal = function(0)
                self.lastVal = function(self.nsteps-1)

        firstVal = kw.get("firstVal")
        if firstVal is not None:
            self.firstVal = firstVal
            
        lastVal = kw.get("lastVal")
        if lastVal is not None:
            self.lastVal = lastVal

        try:
            nbvar1 = len(self.firstVal)
        except:
            nbvar1 = 1
        try:
            nbvar2 = len(self.lastVal)
        except:
            nbvar2 = 1
        nbvar = max(nbvar1, nbvar2)
        if self.nbvar != nbvar: self.nbvar = nbvar 
            
        interp = kw.get("interpolation")
        if interp is not None:
            self.interpolation = interp
        active = kw.get("active")
        if active is not None:
            self.active = active

            

    def getValue(self, fraction, interval, **kw):
        if self.function is None: return None
        
        nsteps = self.nsteps
        if fraction == 0:
            if self.firstVal is not None:
                #print "fraction:", fraction, "firstVal"
                return self.firstVal
            else:
                step = 0
        elif fraction == 1:
            if self.lastVal is not None:
                #print "fraction:", fraction, "lastVal"
                return self.lastVal
            else:
                step = nsteps -1
        else:
            step = round((nsteps-1)*fraction)
        #print "fraction:", fraction, "step:", step
        if type(self.function).__name__ in ('ndarray', 'list'):
            return self.function[int(step)]
        else:
            return self.function(int(step))


from math import sqrt, cos, sin, acos
import numpy

def matToQuaternion(mat):
    # converts rotation matrix to quaternion
    # http://www.euclideanspace.com/maths/geometry/rotations/conversions/matrixToQuaternion/index.htm
    trace = 1 + mat[0] + mat[5] + mat[10]
    if trace > 0.00000001:
      S = sqrt(trace) * 2
      X = ( mat[9] - mat[6] ) / S
      Y = ( mat[2] - mat[8] ) / S
      Z = ( mat[4] - mat[1] ) / S
      W = 0.25 * S
    else:
        if  mat[0] > mat[5] and mat[0] > mat[10]:      
            S  = sqrt( 1.0 + mat[0] - mat[5] - mat[10] ) * 2
            X = 0.25 * S
            Y = (mat[4] + mat[1] ) / S
            Z = (mat[2] + mat[8] ) / S
            W = (mat[9] - mat[6] ) / S
        elif mat[5] > mat[10] : 
            S  = sqrt( 1.0 + mat[5] - mat[0] - mat[10] ) * 2
            X = (mat[4] + mat[1] ) / S
            Y = 0.25 * S
            Z = (mat[9] + mat[6] ) / S
            W = (mat[2] - mat[8] ) / S
        else:		       
            S  = sqrt( 1.0 + mat[10] - mat[0] - mat[5] ) * 2
            X = (mat[2] + mat[8] ) / S
            Y = (mat[9] + mat[6] ) / S
            Z = 0.25 * S
            W = (mat[4] - mat[1] ) / S
    

      #The quaternion is then defined as:
      #Q = | X Y Z W |
##    #normalize:
##    n = sqrt(X*X + Y*Y + Y*Y + W*W);
##    X /= n
##    Y /= n
##    Z /= n
##    W /= n
    return [X, Y, Z, W]



def quatToMatrix(q):
    # converts quaternion to matrix
    # http://www.euclideanspace.com/maths/geometry/rotations/conversions/quaternionToMatrix/index.htm
    x, y,z, w = q
    sqw = w*w
    sqx = x*x
    sqy = y*y
    sqz = z*z

    #invs (inverse square length) is only required if quaternion is not already normalised
    invs = 1 / (sqx + sqy + sqz + sqw)
    m = numpy.zeros((4,4), 'f')
    m[0][0] = ( sqx - sqy - sqz + sqw)*invs  #since sqw + sqx + sqy + sqz =1/invs*invs
    m[1][1] = (-sqx + sqy - sqz + sqw)*invs 
    m[2][2] = (-sqx - sqy + sqz + sqw)*invs 
    
    tmp1 = x*y
    tmp2 = z*w
    m[1][0] = 2.0 * (tmp1 + tmp2)*invs 
    m[0][1] = 2.0 * (tmp1 - tmp2)*invs 
    
    tmp1 = x*z
    tmp2 = y*w
    m[2][0] = 2.0 * (tmp1 - tmp2)*invs 
    m[0][2] = 2.0 * (tmp1 + tmp2)*invs 
    tmp1 = y*z
    tmp2 = x*w
    m[2][1] = 2.0 * (tmp1 + tmp2)*invs 
    m[1][2] = 2.0 * (tmp1 - tmp2)*invs
    mat = m.flatten()
    mat[-1] = 1.
    return mat




if __name__=='__main__':
    ip = IntScalarInterpolator(0,10)

    print ip.getValue(0.3, None)
    print ip.getValue(0.34, None)
    print ip.getValue(0.35, None)
    print ip.getValue(0.36, None)
    print "---------------"
    
    ip1 = FloatScalarInterpolator(7., 10.)
    print ip1.getValue(0.3, None)
    print ip1.getValue(0.34, None)
    print ip1.getValue(0.35, None)
    print ip1.getValue(0.36, None) 
    print "---------------"
    
    ip2 = FloatVectorInterpolator( [1,1,1], [10,10,10])
    print ip2.getValue(0.5, None)
    print ip2.getValue(0.6, None)
    print ip2.getValue(0.67, None)
    print "---------------"

    ip3 = IntVectorInterpolator( [1,1,1], [10,10,10])
    print ip3.getValue(0.5, None)
    print ip3.getValue(0.6, None)
    print ip3.getValue(0.67, None)
    print "---------------"
    
    ip4 = VarScalarInterpolator (2, [2,4,6])
    print ip4.getValue(0.5, None)
    print ip4.getValue(0.6, None)
    print ip4.getValue(0.67, None)
    print "---------------"
    
    #ip5 = VarVectorInterpolator([[1,1,1], ], [[6,6,6], [8,8,8], [10,10,10]] )
    ip5 = VarVectorInterpolator( [[6,6,6], [8,8,8], [10,10,10]], [[1,1,1], ] )
    print ip5.getValue(0.5, None)
    print ip5.getValue(0.6, None)
    print ip5.getValue(0.67, None)
    
    print "---------------"
    #firstVal = Numeric.identity(4).astype('f')
    #from mglutil.math.rotax import rotax
    #import math
    #rot = rotax((0,0,0), (0,1,0), math.pi)
    #lastVal = Numeric.dot(firstVal, rot)
    #ip6 = RotationInterpolator(firstVal.ravel(), lastVal.ravel())
    #print ip6.getValue(0, None)
    #print ip6.getValue(0.3, None )
    #print ip6.getValue(0.5, None)
    #print "---------------"
    
    ip7 = CompositeInterpolator(interpolators = (FloatVectorInterpolator, FloatScalarInterpolator),
                                firstVal =([1,1,1], 1,), lastVal = ([10,10,10], 10))
    
                               
    print ip7.getValue(0.5, None)
    print ip7.getValue(0.6, None)
    print ip7.getValue(0.67, None)
