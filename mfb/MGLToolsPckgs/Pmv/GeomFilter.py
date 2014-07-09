class GeomFilter:

    def __init__(self, pmv):
        self.pmv = pmv
        
    def filter(self, viewer):
        geoms = [ ('All', [viewer.rootObject]) ]

        for mol in self.pmv.Mols:
            gc = mol.geomContainer
            geoms.append( ("  "+mol.name, [gc.masterGeom])) # put the molecule

            # build a dict of all geoms that do display something
            gd = {}
            for gname, g in gc.geoms.items():
                if len(g.getVertices())>0:
                    gd[gname] = g

            # lines
            if gd.has_key('bonded'):
                geoms.append( ("    "+'lines', [gc.geoms['lines']]))
                #del gd['lines']
                #del gd['bonded']
                #del gd['nobnds']
                #del gd['bondorder']

            # surface
            for gname, x in gc.msms.items():
                if gd.has_key(gname):
                    geoms.append( ("    "+gname, [gd[gname]]))
                    #del gd[gname]

            # cpk
            if gd.has_key('cpk'):
                geoms.append( ("    "+'cpk', [gd['cpk']]))
                #del gd['cpk']
            
            # sticks and balls
            if gd.has_key('sticks') and gd.has_key('balls'):
                g = gd['sticks']
                if len(g.getFaces()):
                    geoms.append( ("    "+'ball & stick',
                                   [gd['sticks'], gd['balls']]))
                #del gd['sticks']
                #del gd['balls']

            # CA trace
            if gd.has_key('CAsticks') and gd.has_key('CAballs'):                
                geoms.append( ("    "+'CA trace',
                               [gd['CAsticks'], gd['CAballs']]))
                #del gd['CAsticks']
                #del gd['CAballs']

            # secondary structure
            if gc.geoms.has_key('secondarystructure'):
                # check if any of it is displayed
                # only add it if there is at least 1 triangle
                found = False
                for g in gc.geoms['secondarystructure'].children:
                    if len(g.faceSet):
                        found = True
                        break
                if found:
                    geoms.append( ("    secondary struct",
                                   [gc.geoms['secondarystructure']]))

            # labels
            if gd.has_key('AtomLabels'):
                geoms.append( ("    Atom labels", [gd['AtomLabels']]))
                #del gd['AtomLabels']
            
            if gd.has_key('ResidueLabels'):
                geoms.append( ("    Residue labels", [gd['ResidueLabels']]))
                #del gd['ResidueLabels']
            
            if gd.has_key('ChainLabels'):
                geoms.append( ("    Chain labels", [gd['ChainLabels']]))
                #del gd['ChainLabels']
            
            if gd.has_key('ProteinLabels'):
                geoms.append( ("    Protein labels", [gd['ProteinLabels']]))
                #del gd['ProteinLabels']

            # coarse molecular surface
            if gd.has_key('CoarseMolSurface'):
                geoms.append( ("    Coarse surface", [gd['CoarseMolSurface']]))
                #del gd['CoarseMolSurface']

        return geoms
