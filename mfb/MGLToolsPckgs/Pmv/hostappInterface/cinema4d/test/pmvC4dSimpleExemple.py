#execfile("/Library/MGLTools/1.5.6/MGLToolsPckgs/mglutil/hostappli/pmvC4dSimpleExemple.py")
import mglutil.hostappli.pdb_c4d as epmv
self=epmv.start()
self.readMolecule('/Users/ludo/blenderKTF/1CRN.pdb',log=1)

#self.displayCPK("1CRN", log=1, cpkRad=0., quality=0, only=False, negate=False, scaleFactor=1.0)
#self.displayCPK("1CRN", log=1, cpkRad=0.5, quality=0, only=False, negate=False, scaleFactor=1.0)

self.computeMSMS("1CRN",surfName='MSMS-MOL',hdensity=6.3, hdset=None, log=1, density=3.0, pRadius=1.0, perMol=0, display=True)
self.computeMSMS("1CRN",surfName='MSMS-MOL',hdensity=6.3, hdset=None, log=1, density=3.0, pRadius=0.5, perMol=0, display=True)




