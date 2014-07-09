## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#
#  collection of standard 4x4 rotation matrices
#  about the X, Y and Z axis of 10, 30, 45, 90, 180 degrees
#
rotations = {
}

import math, numpy.oldnumeric as Numeric
from mglutil.math.rotax import rotax

orig = Numeric.array( (0,0,0), 'f')
X = Numeric.array( (1,0,0), 'f')
Y = Numeric.array( (0,1,0), 'f')
Z = Numeric.array( (0,0,1), 'f')

for angle in [1, 5, 10, 30, 45, 90, 180]:
    rotations['X'+str(angle)] = rotax( orig, X, angle*math.pi/180.)
    rotations['X-'+str(angle)] = rotax( orig, X, -angle*math.pi/180.)

for angle in [1, 5, 10, 30, 45, 90, 180]:
    rotations['Y'+str(angle)] = rotax( orig, Y, angle*math.pi/180.)
    rotations['Y-'+str(angle)] = rotax( orig, Y, -angle*math.pi/180.)

for angle in [1, 5, 10, 30, 45, 90, 180]:
    rotations['Z'+str(angle)] = rotax( orig, Z, angle*math.pi/180.)
    rotations['Z-'+str(angle)] = rotax( orig, Z, -angle*math.pi/180.)
