#!/usr/bin/env python
#
# 
#
# $Header: /opt/cvs/python/packages/share1.5/AutoDockTools/Utilities24/prepare_single_alt_loc_files.py,v 1.1.2.1 2012/04/13 21:30:24 rhuey Exp $
#

from MolKit import Read

def hasAt(name):
    if '@' in name: 
        return 1
    else: 
        return 0

def getAT_types(m):
    AT_SET = m.allAtoms.get(lambda x: hasAt(x.name))
    AT_SET_SET = set(AT_SET.name)
    alt_items = {}
    for ent in AT_SET_SET:
        alt_items[ent.split("@")[1]] = 1
    print "@@returning ", alt_items.keys(), " @@"
    return alt_items.keys()
    

if __name__ == '__main__':
    import sys
    import getopt


    def usage():
        "Print helpful, accurate usage statement to stdout."
        print "Usage: prepare_single_alt_loc_files.py -r filename.pdb"
        print
        print "    Description of command..."
        print "        -r   filename.pdb "
        print "        create separate pdb files for file with alt_loc coords"
        print "    Optional parameters:"
        print "        [-v]  verbose output (default is minimal output)"
        print "        [-o pdb_stem]  (default creates 'filename_A.pdb', 'filename_B.pdb' etc)"


    # process command arguments
    try:
        opt_list, args = getopt.getopt(sys.argv[1:], 'r:vo:h')

    except getopt.GetoptError, msg:
        print 'prepare_single_alt_loc_files.py: %s' %msg
        usage()
        sys.exit(2)

    # initialize required parameters
    #-r: filename 
    filename =  None

    # optional parameters
    #-v verbose
    verbose = None
    #-o pdb_stem
    pdb_stem = None

    #'r:vo:h'
    for o, a in opt_list:
        if o in ('-r', '--r'):
            filename = a
            if verbose: print 'set filename to ', a
        if o in ('-v', '--v'):
            verbose = True
            if verbose: print 'set verbose to ', True
        if o in ('-o', '--o'):
            pdb_stem = a
            if verbose: print 'set pdb_stem to ', a
        if o in ('-h', '--'):
            usage()
            sys.exit()


    if not filename:
        print 'prepare_single_alt_loc_files: filename must be specified.'
        usage()
        sys.exit()

    file_stem = filename.split('.')[0]
    if pdb_stem is not None:
        file_stem = pdb_stem


    mols = Read(filename)
    if verbose: print 'read ', filename
    mol = mols[0]
    if len(mols)>1:
        if verbose: print "more than one molecule in file using molecule with most atoms"
        #use the molecule with the most atoms
        ctr = 1
        for m in mols[1:]:
            ctr += 1
            if len(m.allAtoms)>len(mol.allAtoms):
                mol = m
                if verbose: print "mol set to ", ctr, "th molecule with", len(mol.allAtoms), "atoms"
    ats = mol.allAtoms.get("*@*")
    if not len(ats):
        print 'Nothing to do:no alt loc atoms found in ', filename
        sys.exit()
    list_to_write = getAT_types(mol)
    ATOMLINES = mol.parser.getAtomsLines(-2,0)
    
    for altT in list_to_write:
        fn = file_stem + '_' + altT + '.pdb'
        fptr = open(fn, 'w')
        ctr = 1
        for ll in ATOMLINES:
            if ll[16]==altT: #'B'
                newL = ll[:7] +"%4d" %(ctr) + ll[11:16]+" " + ll[17:] 
                #newL = ll[:6] +"%4d" %ctr 
                #newL = ll[:16] + " " + ll[17:]
                ctr = ctr + 1
            elif ll[16]==' ':
                #newL = ll
                newL = ll[:7] +"%4d" %(ctr) + ll[11:16]+" " + ll[17:] 
                ctr = ctr + 1
            else:
                newL = ""
            if len(newL): fptr.write(newL)
        fptr.close()


# To execute this command type:
# prepare_single_alt_loc_files.py -r pdb_file -o pdb_stem 

