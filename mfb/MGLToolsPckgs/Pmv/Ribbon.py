## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Sophie Coon, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/Ribbon.py,v 1.14 2008/10/03 19:28:29 sargis Exp $
#
# $Id: Ribbon.py,v 1.14 2008/10/03 19:28:29 sargis Exp $
#

import numpy.oldnumeric as Numeric

def cross( b, c):
    a = [0.,0.,0.]
    a[0]=b[1]*c[2]-c[1]*b[2]
    a[1]=b[2]*c[0]-c[2]*b[0]
    a[2]=b[0]*c[1]-c[0]*b[1]
    return a

def normalize(v):
    import math
    norm = 1.0 / math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
    v[0] = v[0]*norm
    v[1] = v[1]*norm
    v[2] = v[2]*norm
    return v

def bspline( v1, v2, v3, t ):
    v4 = [0.,0.,0.,0.]
    frac3 = 0.5 * t*t
    frac1 = 0.5 * (1.-t) * (1.-t)
    frac2 = 1. - (frac1 + frac3)
    for i in (0,1,2,3):
        v4[i] = frac1 * v1[i] + frac2 * v2[i] + frac3 * v3[i]
    return v4

def interpPoints( ctrl, nchord):

    assert ctrl.shape[1]==4
    tinc = 1./float(nchord-1)
    
    smooth = Numeric.zeros( (((ctrl.shape[0]-2)*nchord+2),4), 'f')
    if smooth is None: return None
    
    # calculate spline segments
    # first point in rib
    smooth[0] = ctrl[0]
    
    # splines go midpoint-to-midpoint
    nb = 1
    for pt in range(1,ctrl.shape[0]-1):
        t=0.0
        for i in range(nchord):
            smooth[nb] = bspline( ctrl[pt-1], ctrl[pt], ctrl[pt+1], t)
            nb = nb+1
            t = t + tinc
    # last point in rib
    smooth[nb] = ctrl[-1]
    
    return smooth


"""
ctrl: ctrl points 4D
nchord: how many interpolations per ctrl pt

splining from Larry Andrews 7-Nov-1988
"""
def ribdrw( ctrl, nrib, nchord ):

    tinc = 1./nchord
    smooth = Numeric.zeros( (nrib, ((ctrl.shape[0]-2)*nchord+2), 4 ), 'd')
    
    # calculate spline segments
    for irib in range(nrib):

        # first point in rib
        smooth[irib][0] = ctrl[0][irib]

        # splines go midpoint-to-midpoint
        nb = 1
        for pt in range(1,ctrl.shape[0]-1):
            t = 0.0
            for i in range(nchord):
                smooth[irib][nb] = bspline( ctrl[pt-1][irib], ctrl[pt][irib],
                                            ctrl[pt+1][irib], t )
                t = t + tinc
                nb = nb+1

        # last point in rib
        smooth[irib][nb] = ctrl[-1][irib];

    return smooth


def ribbon2D( nrib, ribwid, nchords, offset, natoms, coords, isHelix, 
                                                                   off_c = 0.5):
    """
    Generate ctrl points for protein ribbon, based on ideas on
    Carson & Bugg, J.Molec.Graphics 4,121-122 (1986)
    
    Ctrl points for Bspline are generated along a line passing
    through each CA and along the average of the two peptide planes
    
    nrib     number of strands in ribbon
    ribwid   total ribbon width
    nchord   number of chords/residue
    offset   amount to offset ctrl points away from CA positions
    natom    number of atoms stored in arrays
    coords   coordinates of CA and O atoms of all residues in strand
    isHelix  set to 1 for residues in alpha helices
    off_c   this parameter has been added to account for DNA/RNA in the coil
    """

    coords = Numeric.array(coords)
    
    # C Strand separation and half
    nres = natoms/2;

##     ctrl = Numeric.zeros( (nres, nrib, 4), 'd')
    # MS changes
    ctrl = Numeric.zeros( (nres+1, nrib, 4), 'd')

    E = Numeric.zeros( (3,), 'd')
    F = Numeric.zeros( (3,), 'd')
    G = Numeric.zeros( (3,), 'd')
    H = Numeric.zeros( (3,), 'd')

    if natoms<=0: return None
    if nrib > 1: drib = ribwid / (nrib-1)
    rib2 = (nrib+1)*0.5

    for nr in range(nres):
        i=2*nr
        if nr<nres-1:
            # A is vector CAi to CAi+1
            A = coords[i+2] - coords[i]
   
            # B is vector CAi to Oi
            B = coords[i+1] - coords[i]

            # C = A x B;  D = C x A
            C = Numeric.array(cross(A,B))
            D = Numeric.array(cross(C,A))
            D = normalize(D)

            if i==0:
                E[:] = D[:] # First peptide, no previous one to average with
                P = Numeric.zeros( (3,), 'd') # No offset for first CA
            else:
              # Not first, ribbon cross vector is average of peptide plane
              # with previous one
              if Numeric.dot(D,G)<0.0: B = -D
              else: B = D
              E = G+B
              # Offset is along bisector of CA-CA-CA vectors A (H is Ai-1)
              P = H-A
              P = normalize(P)
        else:
            E[:] = G[:] # Last one, just use last plane
            P = Numeric.zeros( (3,), 'd') # No offset for last CA

        E = normalize(E) # Normalise vector E

        # MS oct 11 2001. add a first ctrl point per rib the is before the
        # first CA atom. Use -0.5*A as the offset along the chain
        if i==0:
            # Generate ctrl points
            if not isHelix[nr]:
                P = coords[i] - 0.5*A
                for j in range(nrib):
                    fr=(float(j+1)-rib2)*drib
                    F = fr*E
                    ctrl[0][j][:3] = P+F
                    ctrl[0][j][3] = i+2;

            else:
                # is secondary structure starts with an Helix
                # The first point in an helix is particular ...
                for j in range(nrib):
                    fr=(float(j+1)-rib2)*drib
                    F = fr*E
                    ctrl[0][j][:3] = coords[i]-0.1 *A +F
                    ctrl[0][j][3] = i+2;

        # Generate ctrl points
        if not isHelix[nr]: # control points for none helical parts
            P = coords[i] + off_c*A
        else: # control point for helices
              # increasing the offset increases the radius of the helix
              # increasing the factor multiplying A shifts the per/residue
              # point down the helix
            P = (2*offset) * P + 0.75*A
            P = coords[i]+P

        for j in range(nrib):
            fr=(float(j+1)-rib2)*drib
            F = fr*E
            # MS changed.
            ctrl[nr+1][j][:3] = P+F
            ctrl[nr+1][j][3] = i+2;

        # Store things for next residue
        G[:] = E[:]
        H[:] = A[:]
    # end loop over residues

    smooth = ribdrw(ctrl, nrib, nchords)
    return smooth#, ctrl

if __name__=='__main__':
  
    cao = Numeric.array(
     (( 16.966999, 12.784000, 4.338000 ), (15.268000, 13.825000, 5.594000),
     ( 13.856000, 11.469000, 6.066000 ), (14.993000, 9.862000, 7.443000),
     ( 13.660000, 10.707000, 9.787000 ), (11.393000, 11.308000, 10.185000),
     ( 10.646000, 8.991000, 11.408000 ), (11.659000, 8.296000, 13.491000),
     ( 9.448000, 9.034000, 15.012000 ), (9.490000, 7.519000, 16.819000),
     ( 8.673000, 5.314000, 15.279000 ), (8.726000, 4.858000, 12.923000),
     ( 8.912000, 2.083000, 13.258000 ), (7.670000, 2.031000, 11.245000),
     ( 5.145000, 2.209000, 12.453000 ), (4.664000, 3.268000, 10.343000),
     ( 5.598000, 5.767000, 11.082000 ), (6.052000, 5.933000, 8.744000),
     ( 8.496000, 4.609000, 8.837000 ), (7.878000, 3.778000, 6.651000),
     ( 6.500000, 1.584000, 7.565000 ), (5.213000, 2.016000, 5.557000),
     ( 3.545000, 3.935000, 6.751000 ), (3.536000, 5.001000, 4.617000),
     ( 5.929000, 6.358000, 5.055000 ), (6.136000, 6.072000, 2.653000),
     ( 7.331000, 3.607000, 2.791000 ), (6.240000, 3.144000, 0.684000),
     ( 3.782000, 2.599000, 1.742000 ), (2.947000, 3.817000, -0.189000),
     ( 2.890000, 6.285000, 1.126000 ), (3.200000, 7.147000, -1.103000),
     ( 5.895000, 6.489000, -1.213000 ), (6.228000, 5.901000, -3.507000),
     ( 4.933000, 3.431000, -3.326000 ), (4.988000, 3.755000, -5.687000),
     ( 2.792000, 5.376000, -5.797000 ), (3.260000, 7.045000, -7.422000),
     ( 5.366000, 8.191000, -6.018000 ), (5.535000, 10.510000, -5.730000),
     ( 3.767000, 10.609000, -3.513000 ), (5.947000, 10.757000, -2.523000),
     ( 6.143000, 13.513000, -2.696000 ), (5.485000, 13.061000, -0.382000),
     ( 8.114000, 13.103000, 0.500000 ), (7.036000, 13.682000, 2.540000),
     ( 6.614000, 16.316999, 1.913000 ), (4.782000, 16.166000, 3.495000),
     ( 3.074000, 14.894000, 1.756000 ), (2.315000, 13.523000, 3.578000),
     ( 4.180000, 11.549000, 3.187000 ), (4.227000, 11.252000, 5.547000),
     ( 5.879000, 13.502000, 6.026000 ), (4.528000, 13.422000, 8.025000),
     ( 2.691000, 15.221000, 7.194000 ), (0.947000, 14.112000, 8.468000),
     ( 0.715000, 12.045000, 6.657000 ), (0.286000, 10.632000, 8.545000),
     ( 2.986000, 9.994000, 8.950000 ), (3.766000, 9.715000, 11.186000),
     ( 4.769000, 12.336000, 11.360000 ), (7.037000, 12.750000, 11.954000),
     ( 8.140000, 11.694000, 9.635000 ), (7.581000, 13.949000, 8.944000),
     ( 10.280000, 14.760000, 8.823000 ), (11.971000, 13.583000, 7.552000),
     ( 12.552000, 15.877000, 6.036000 ), (13.168000, 18.006001, 6.945000),
     ( 15.930000, 17.454000, 6.941000 ), (17.097000, 16.660000, 4.970000),
     ( 18.635000, 18.861000, 4.738000 ), (20.593000, 17.742001, 3.945000),
     ( 21.452000, 16.969000, 6.513000 ), (20.138000, 15.023000, 5.878000),
     ( 22.018999, 13.242000, 7.020000 ), (21.868999, 11.387000, 8.435000),
     ( 21.936001, 12.911000, 10.809000 ), (20.357000, 14.317000, 11.948000),
     ( 18.504000, 12.312000, 12.298000 ), (19.533001, 11.718000, 14.362000),
     ( 17.924000, 13.421000, 15.877000 ), (16.652000, 11.368000, 16.033001),
     ( 17.334000, 10.956000, 18.691000 ), (15.434000, 9.550000, 19.166000),
     ( 13.564000, 11.573000, 18.836000 ), (11.720000, 11.040000, 17.427999),
     ( 13.257000, 10.745000, 15.081000 ), (14.930000, 9.862000, 13.568000),
     ( 15.445000, 7.667000, 15.246000 ), (16.093000, 5.705000, 14.039000),
     ( 13.512000, 5.395000, 12.878000 ), (13.733000, 6.929000, 11.026000)))

    nchords=10
    nrib=2
    nres=46
    natoms=2*nres
    offset=1.2
    width=1.5

    import profile
#    profile.run("smooth, ctrl = ribbon2D( nrib, width, nchords, offset, natoms, cao, [0]*46 );")
    profile.run("smooth = ribbon2D( nrib, width, nchords, offset, natoms, cao, [0]*46 );")
    
    from DejaVu import Viewer
    vi = Viewer()
    from DejaVu.IndexedPolygons import IndexedPolygons
    f = []
    n = smooth.shape[1]
    f = map( lambda x: (x, x+1, x+n+1, x+n), range(smooth.shape[1]-1))
    v = Numeric.array(Numeric.reshape(smooth, (-1,4))[:,:3])
    p = IndexedPolygons('sheet2D', vertices = v, faces = f, protected=True,)
    if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
        p.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False,)
    p.replace = False
    vi.AddObject(p)

    from DejaVu.Spheres import Spheres
    ctrl.shape = (-1,4)
    p = Spheres('ctrl', centers = ctrl[:, :3], radii = 0.6, protected=True)
    p.replace = False
    vi.AddObject(p)

    from DejaVu.Spheres import Spheres
    s = Spheres('sph', vertices = v, quality=5, protected=True)
    s.radius = 0.2
    vi.AddObject(s)

    from MolKit import Read
    mol = Read('../1crn.pdb')
    allatoms = mol.chains.residues.atoms
    caat = allatoms.get('CA')
    coords = caat.coords
    from DejaVu.Spheres import Spheres
    p = Spheres('CA', centers = coords, radii = 0.6, protected=True)
    p.replace = False
    vi.AddObject(p)
    
##      from BioChem.protein import Protein
##      from BioChem.pdbParser import PdbParser
##      mol = Protein()
##      mol.read('/tsri/pdb/struct/1b1g.pdb', PdbParser())
##      l = lambda x:x.name=='CA' or x.name=='O'
##      cao1 = mol.chains.residues.atoms.get(l).coords
##      natoms = len(cao1)/2
##      profile.run("smooth1 = ribbon2D( nrib, width, nchords, offset, natoms, cao1 );")
##      f1 = []
##      n1 = smooth1.shape[1]
##      f1 = map( lambda x: (x, x+1, x+n+1, x+n), range(smooth1.shape[1]-1))
##      v1 = Numeric.array(Numeric.reshape(smooth1, (-1,4))[:,:3])
##      p1 = IndexedPolygons('sheet2D', vertices = v1, faces = f1)
##      vi.AddObject(p1)
