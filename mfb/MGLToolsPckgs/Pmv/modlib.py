modlist = [
("Pmv","SLCommands","""None"""),
("Pmv","amberCommands","""None"""),
("Pmv","artCommands","""None"""),
("Pmv","bondsCommands","""None"""),
("Pmv","colorCommands","""
This Module implements commands to color the current selection different ways.
for example:
    by atoms.
    by residues.
    by chains.
    etc ...
    
"""),
("Pmv","deleteCommands","""
This Module implements commands to delete items from the MoleculeViewer:
for examples:
    Delete Molecule
"""),
("Pmv","displayCommands","""None"""),
("Pmv","editCommands","""None"""),
("Pmv","extrusionCommands","""None"""),
("Pmv","fileCommands","""
This Module implements commands to load molecules from files in the following
formats:
    PDB: Brookhaven Data Bank format
    PQR: Don Bashford's modified PDB format used by MEAD
    PDBQ: Autodock file format
    PDBQS: Autodock file format
The module implements commands to save molecules in additional formats:    
    STL: Stereolithography file format
"""),
("Pmv","genparserCommands","""None"""),
("Pmv","gridCommands","""
This Module implements commands 
    to read grid data, 
    to visualize isosurfaces,
    to manipulate orthoslices through the isosurfaces...
 
"""),
("Pmv","hbondCommands","""None"""),
("Pmv","interactiveCommands","""None"""),
("Pmv","labelCommands","""
This Module implements commands to label the current selection different ways.
For example:
    by properties  of the current selection
"""),
("Pmv","measureCommands","""None"""),
("Pmv","msmsCommands","""None"""),
("Pmv","povrayCommands","""None"""),
("Pmv","repairCommands","""None"""),
("Pmv","sdCommands","""None"""),
("Pmv","secondaryStructureCommands","""None"""),
("Pmv","selectionCommands","""None"""),
("Pmv","setangleCommands","""None"""),
("Pmv","splineCommands","""None"""),
("Pmv","superimposeCommandsNew","""None"""),
("Pmv","traceCommands","""
Package: Pmv
Module : TraceCommands
This module provides a set of commands:
- ComputeTraceCommand (computeTrace) to compute a trace and the corresponding
  sheet2D using the given control atoms and torsion atoms. Typically used to
  compute a CA trace for a protein
- ExtrudeTraceCommand (extrudeTrace) to extrude a 2D geometry along the 3D
  path to represent the given trace.
- DisplayTraceCommand (displayTrace) to display, undisplay or display only
  parts of the molecule using the geometry created to represent the given
  trace.
  Keywords:
  Trace, CA 
  
"""),
("Pmv","vectfieldCommands","""None"""),
("Pmv","visionCommands","""None"""),
("Pmv","writeMsmsAsCommands","""None"""),
]
