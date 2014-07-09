########################################################################
#
# Date:Sept 2009 Authors: Michel Sanner
#
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI
#
#########################################################################


def saveInstancesMatsToFile(filename, matrices):
    """
    save a list of instance matrices to a file

    status = saveInstancesMatsToFile(filename, matrices)

    status will be 1 if it worked
    """

    f = open(filename, 'w')
    if not f:
        return 0
    for mat in matrices:
        for v in mat.flatten():
            f.write("%f "%v)
        f.write("\n")
    f.close()
    return 1


import numpy

def readInstancesMatsFromFile(filename):
    """
    read a list of instance matrices from a file

    matrices = readInstancesMatsFromFile(filename)

    """

    f = open(filename)
    if not f:
        return None
    data = f.readlines()
    f.close()

    mats = []
    for line in data:
        mats.append( map(float, line.split()) )

    mats = numpy.array(mats)
    mats.shape = (-1,4,4)
    return mats
        
