#!/usr/bin/env python
#
# 
#
# $Header: /opt/cvs/python/packages/share1.5/AutoDockTools/Utilities24/write_conformations_from_dlg.py,v 1.4.6.1 2012/01/16 23:20:39 rhuey Exp $
#
# $Id: write_conformations_from_dlg.py,v 1.4.6.1 2012/01/16 23:20:39 rhuey Exp $
#
import os

from AutoDockTools.Docking import Docking


if __name__ == '__main__':
    import sys
    import getopt


    def usage():
        "Print helpful, accurate usage statement to stdout."
        print "Usage: write_conformations_from_dlg.py -d directory"
        print
        print "    Description of command..."
        print "         -d     docking filename"
        print "    Optional parameters:"
        print "        [-o]    output file stem"
        print "        [-e]    include energy in output file stem"
        print "        (default is ligandname. Outputfiles are named 'stem' plus '_num.pdbq[t]')"
        print "        [-v]    verbose output"


    # process command arguments
    try:
        opt_list, args = getopt.getopt(sys.argv[1:], 'd:o:evh')
    except getopt.GetoptError, msg:
        print 'write_conformations_from_dlg.py: %s' %msg
        usage()
        sys.exit(2)

    # initialize required parameters
    #-d: docking log filename
    docking_filename =  None

    # initialize optional parameter
    #-o output_stem
    output_stem = None
    #-e include energy in filename 
    include_energy = False
    #-v verbose best only
    verbose = False

    #'d:bvh'
    for o, a in opt_list:
        #print "o=", o, " a=", a
        if o in ('-d', '--d'):
            docking_filename = a
            if verbose: print 'set docking_filename to ', a
        if o in ('-o', '--o'):
            output_stem = a
            if verbose: print 'set output_stem to ', a
        if o in ('-e', '--e'):
            include_energy = True
            if verbose: print 'set output_stem to ', a
        if o in ('-v', '--v'):
            verbose = True
            if verbose: print 'set verbose to ', True
        if o in ('-h', '--'):
            usage()
            sys.exit()

    if not docking_filename:
        print 'write_conformations_from_dlg: docking_filename must be specified.'
        usage()
        sys.exit()


    d = Docking()
    d.readDlg(docking_filename)
    lines = d.ligMol.parser.allLines
    for i in range(len(lines)):
        line = lines[i] 
        if line.find("\n")==-1:
            d.ligMol.parser.allLines[i] = line + "\n"
    ext = '.pdbqt'
    if d.version<4.0:
        ext = '.pdbq'
        
    if output_stem is None:
        output_stem = d.ligMol.name

    for ix, conf in enumerate(d.ch.conformations):
        outfile= output_stem + '_' + str(ix+1) + ext
        if include_energy:
            print "ix=", ix
            print "conf.energy=", conf.energy
            energy_str = str(round(conf.energy,3))
            if energy_str[0]=='-':
                energy_str = energy_str[1:] 
            outfile= output_stem + '_'+energy_str + ext
        conf = d.ch.conformations[ix]
        d.ligMol.parser.write_with_new_coords(conf.getCoords(),outfile)
        if verbose: print "wrote ", outfile


# To execute this command type:
# write_conformations_from_dlg.py -d docking_filename 
# optional arguments
# -o outputfile_stem (default is ligandname)
# -e include_energy in filename (default is not to do this)
