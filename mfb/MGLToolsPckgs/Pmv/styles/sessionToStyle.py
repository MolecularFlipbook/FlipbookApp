import os, sys

if len(sys.argv) < 3:
    print "Usage: python sessionToStyle sessionFile, molName"
    sys.exit(1)
    
filename = sys.argv[1]
molname = sys.argv[2]
f = open(filename)
lines = f.readlines()
f.close()

name, ext = os.path.splitext(filename)
f = open(name+'_style.py', 'w')
f.write("numberOfMolecules = 1\n\n")

f.write("__doc__ = """Style_01: Applies to X molecules. It displays ..
"""\n")

f.write("def applyStyle(mv, molName):\n")
f.write("    mode='both'\n")
for l in lines:
    # replace self by mv
    l = l.replace('self', 'mv')
    # look for "nolname in PMV commands
    try:
        start = l.index('"'+molname)
        end = l[start+1:].index('"')
        newline1 = l[:start+1]+'%s'+l[start+1+len(molname):start+end+2] +\
                   "%molName"+l[start+end+2:]
    except ValueError:
        newline1 = l

    # look for |molname| in DejaVu Geometry
    try:
        start = newline1.index("FindObjectByName('root|")+23
        end = newline1[start+1:].index('|')
        newline2 = newline1[:start]+"'+molName+'"+newline1[start+1+end:]
    except ValueError:
        newline2 = newline1

    f.write("    %s"%newline2)

f.close()
