## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/DejaVu/viewerFns.py,v 1.7 2007/07/24 17:30:41 vareille Exp $
#
# $Id: viewerFns.py,v 1.7 2007/07/24 17:30:41 vareille Exp $
#

import numpy.oldnumeric as Numeric
import viewerConst
import types

def checkKeywords(_name, keywords, **kw):
    """test is all kyes in **kw are in list keywords"""

    for key in kw.keys():
        if key not in keywords:
            print 'WARNING: Keyword %s not recognized for %s' % (key,_name)
            #import traceback;traceback.print_stack()
            

def getkw(kw, name):
    """get a dictionary entry and remove it from the dictionary"""

    v = kw.get(name)
    if name in kw.keys(): del kw[name]
    return v


def GetArray(vector, shape=None, precision=viewerConst.FPRECISION ):
    """get a vector and return it in a Numeric array"""

    if type(vector).__name__ == 'array':
	if vector.dtype.char==precision:
	    if shape:
		if vector.shape == shape: return vector
		else: return Numeric.reshape(vector, shape)
	    else: return vector
	else:
	    vector = Numeric.array( vector, precision )
	    if shape:
		if vector.shape == shape: return vector
		else: return Numeric.reshape(vector, shape)
	    else: return vector
    else:
	vector = Numeric.array( vector, precision )
	if shape:
	    if vector.shape == shape: return vector
	    else: return Numeric.reshape(vector, shape)
	else: return vector

    
def read_data(filename, function):
    """Read data from an ASCII file."""

    import string
    result = []
    assert type(filename) == types.StringType
    assert function in (None, float, int)
    print "reading", filename
    f = open(filename, "r")
    while 1:
	line = f.readline();
	if not len(line):
	    break
	if function:
	    datum = map(function, string.split(line))
	    result.append(list(datum))
	else:
	    result.append(line)
    f.close()
    if function == float:
	ar = Numeric.array(result).astype(viewerConst.FPRECISION)
    elif function == int:
	ar = Numeric.array(result).astype(viewerConst.IPRECISION)
    else:
	ar = result

    return ar


def write_data(filename,data):
    """Write data to an ASCII file."""

    assert type(filename) == types.StringType
    import string
    f = open(filename, "w")
    def writedatum1(datum, f=f):
	line = str(datum)
	line = line[1:-1] + "\n" # slice off the [ , ] characters
	f.write(line)
    def writedatum(datum, f=f):
	import string, numpy.oldnumeric as Numeric
	line = string.join(map(str,Numeric.array(datum))," ") + "\n"
	f.write(line)
    map(writedatum,data)
    f.close()

