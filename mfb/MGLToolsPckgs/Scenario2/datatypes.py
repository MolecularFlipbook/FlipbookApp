## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

##
##  Author Michel F. Sanner May 2007
##

import numpy
class DataType:

    def valide(self, value):
        return True

    def cast(self, data):
        return False, None

    def isEqual(self, val1, val2):
        if val1 == val2:
            return True
        else:
            return False



class FloatType(DataType):

    def valide(self, value):
        return isinstance(value, float)

    def cast(self, data):
        try:
            return True, float(value)
        except:
            return False, None

    def isEqual(self, val1, val2):
        if abs(val1-val2) < 1.e-5:
            return True
        else: return False
        



class IntType(DataType):

    def valide(self, value):
        return isinstance(value, int)

    def cast(self, data):
        try:
            return True, int(value)
        except:
            return False, None



class BoolType(DataType):

    def valide(self, value):
        if isinstance(value, bool):
            return True
        else:
            if value == 1 or value == 0:
                return True
            else:
                return False

    def cast(self, data):
        try:
            return True, bool(value)
        except:
            return False, None


import numpy.oldnumeric as Numeric

class IntVectorType(DataType):
    
    def valide(self, value):
        try:
            len(value)
        except:
            return False
        for v in value:
            if not isinstance(v, int):
                return False
        return True

    
    def cast(self, data):
        try:
            if isinstance(data, Numeric.ArrayType):
                newdata = data.astype('i')
            else:
                newdata = []
                for val in data:
                    newdata.append(int(val))
            return True, newdata
        except:
            return False, None

    def isEqual(self, val1, val2):
        val1 = Numeric.array(val1, 'i')
        val2 = Numeric.array(val2, 'i')
        return Numeric.alltrue(val1, val2)

        
class FloatVectorType(DataType):
    
    def valide(self, value):
        try:
            len(value)
        except:
            return False
        for v in value:
            if not isinstance(v, float):
                return False
        return True


    def cast(self, data):
        try:
            if isinstance(data, Numeric.ArrayType):
                newdata = data.astype('f')
            else:
                newdata = []
                for val in data:
                    newdata.append(float(val))
            return True, newdata
        except:
            return False, None

    def isEqual(self, val1, val2):
        val1 = Numeric.array(val1, 'f')
        val2 = Numeric.array(val2, 'f') 
        d = abs(val1-val2)
        for i, v in enumerate(d):
           if  v > 1.e-5:
               #print "value arrays differ: ", i, val1[i], val2[i]
               return False
        return True



class IntVarType(DataType):
    
    def valide(self, value):
        # valid value can be either a single integer or a sequence of integers 
        try:
            len(value)
        except:
            value = [value]
        if isinstance(value, Numeric.ArrayType):
            dt = value.dtype.char  
            if dt not in ('i', Numeric.Int):
                return False
        else:
            for v in value:
                if not isinstance(v, int):
                    return False
        return True

    def cast(self, data):
        try:
            len(data)
        except:
            data = [data]
        try:
            if isinstance(data, Numeric.ArrayType):
                newdata = data.astype('i')
            else:
                newdata = []
                for val in data:
                    newdata.append(int(val))
            return True, newdata
        except:
            return False, None

    def isEqual(self, val1, val2):
        try:
            len(val1)
        except:
            val1 = [val1]
        try:
            len(val2)
        except:
            val2 = [val2]
        val1 = Numeric.array(val1, 'i')
        val2 = Numeric.array(val2, 'i')
        if val1.shape != val2.shape:
            return False
        return Numeric.alltrue(val1, val2)


class FloatVarType(DataType):
    
    def valide(self, value):
        # valid value can be either a single float or a sequence of floats 
        try:
            len(value)
        except:
            value = [value]
        if isinstance(value, Numeric.ArrayType):
            dt = value.dtype.char  
            if dt not in ('f', Numeric.Float):
                return False
        else:
            for v in value:
                if not isinstance(v, float):
                    return False
        return True

    def cast(self, data):
        try:
            len(data)
        except:
            data = [data]
        try:
            if isinstance(data, Numeric.ArrayType):
                newdata = data.astype('f')
            else:
                newdata = []
                for val in data:
                    newdata.append(float(val))
            return True, newdata
        except:
            return False, None


    def isEqual(self, val1, val2):
        try:
            len(val1)
        except:
            val1 = [val1]
        try:
            len(val2)
        except:
            val2 = [val2]
        val1 = Numeric.array(val1, 'f')
        val2 = Numeric.array(val2, 'f')
        if val1.shape != val2.shape:
            return False
        d = abs(val1-val2)
        for i, v in enumerate(d):
           if  v > 1.e-5:
               #print "value arrays differ: ", i, val1[i], val2[i]
               return False
        return True



class VarVectorType(DataType):

    def valide(self, value):
        #valid value is a 2D sequence
        if isinstance(value, Numeric.ArrayType):
            if len(value.shape) != 2:
                return False
        else:
            try:
                len(value)
            except:
                return False
            
            try:
                nelem = len(value[0])
            except:
                return False
            if len(value) > 1:
                for v in value[1:]:
                    try:
                        n = len(v)
                    except:
                        return False
                    if n != nelem:
                        return False
        return True

    def isEqual(self, val1, val2):
        val1 = Numeric.array(val1, 'f')
        val2 = Numeric.array(val2, 'f')
        if val1.shape != val2.shape:
            return False
        d = abs(val1-val2)
        shape = d.shape
        for i in range(shape[0]):
            for j in range(shape[1]):
                if  d[i][j] > 1.e-5:
                    #print "value arrays differ: val1[%d][%d] = %f, val2[%d][%d] = %f"% (i,j, val1[i][j], i, j, val2[i][j])
                    return False
        return True
            

if __name__=='__main__':
    t = IntVectorType()
    v1 = 3
    assert t.valide(v1)==False
    v2 = [1., 2., 3.]
    assert t.valide(v2) == False
    v3 = [1,2,3]
    assert t.valide(v3) == True
    assert t.cast(v2)[1] == v3
    assert t.cast(v1)[0] == False

    t = FloatVectorType()
    v4 = 3.4
    assert t.valide(v4)==False
    assert t.valide(v3) == False
    assert t.valide(v2) == True
    assert t.cast(v3)[1] == v2
    assert t.cast(v4)[0] == False

    t = IntVarType()
    assert t.valide(v4)==False
    assert t.valide(v1)==True
    assert t.valide(v3) == True
    assert t.valide(v2) == False
    v5 = Numeric.array([1,2,3], 'f')
    assert t.valide(v5) == False
    cv = t.cast(v5)
    assert t.valide(cv[1]) == True
    assert t.cast(v4)[0] == True
    v6 = [[1.,2.,3.],[4.,5.,6.]]
    assert t.cast(v6)[0] == False

    t = FloatVarType()
    assert t.valide(v1)==False
    assert t.valide(v4)==True
    assert t.valide(v2) == True
    assert t.valide(v3) == False
    v7 = Numeric.array([1,2,3], 'i')
    assert t.valide(v7) == False
    cv = t.cast(v7)
    assert t.valide(cv[1]) == True
    assert t.cast(v1)[0] == True
    v8 = [[1,2,3],[4,5,6]]
    assert t.cast(v8)[0] == False

    t = VarVectorType()
    assert t.valide(v1) == False
    assert t.valide(v2) == False
    assert t.valide (v5) == False
    assert t.valide(v6) == True
    assert t.valide([[1,2,3], [1]]) == False
    assert t.valide([[1,2,3]]) ==True
    assert t.valide(Numeric.array([[1,2,3],[4,5,6]]) ) == True
