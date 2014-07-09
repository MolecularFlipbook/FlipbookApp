## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Authors: Michel F. SANNER, Ruth Huey, Daniel Stoffler
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################
# $Id:

"""
This Module implements commands to load molecules from files in the following
formats:
    PDB: Brookhaven Data Bank format
    PQR: Don Bashford's modified PDB format used by MEAD
    PDBQ: Autodock file format
    PDBQS: Autodock file format
    PDBQT: Autodock file format
    MMCIF: Macromolecular Crystallographic Information File
The module implements commands to save molecules in additional formats:    
    STL: Stereolithography file format
"""

from ViewerFramework.VFCommand import CommandGUI
from Pmv.mvCommand import MVCommand
from MolKit.protein import Protein
from MolKit.pdbParser import PdbParser, PdbqParser, PdbqsParser, PdbqtParser, PQRParser, F2DParser
from MolKit.pdbWriter import PdbWriter, PdbqWriter, PdbqsWriter, PdbqtWriter
from MolKit.pqrWriter import PqrWriter
from MolKit.groParser import groParser
from MolKit.molecule import Atom, AtomSet, MoleculeSet
from MolKit.mol2Parser import Mol2Parser
from MolKit.mmcifParser import MMCIFParser
from MolKit.mmcifWriter import MMCIFWriter

import types, os, sys, string, glob
import numpy
import numpy.oldnumeric as Numeric
import Tkinter, Pmw
##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import SaveButton
from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Atom
from tkMessageBox import *

from Pmv.moleculeViewer import EditAtomsEvent

pdbDescr = """
By default the PDB writer will create the following records:
- ATOM and TER records
- CONECT records when bond information is available (bonds have been built by distance,
  the user defined bond information or the original file contained connectivity information.
- HELIX, SHEET, TURN when secondary structure information is available (either from the original
  file or computed).

Other records can be created from the molecular data structure such as :
- HYDBND when hydrogne bonds information is available.

The information below can be found at http://www.rcsb.org/pdb/docs/format/pdbguide2.2/guide2.2_frame.html

The PDBQ format is similar to the PDB format but has charges information in the field adjacent to the
temperature factor.
The PDBQS format is the PDBQS format with some solvation information at the end of the ATOM/HETATM records.
The PDBQT format is the PDBQ format with autodock element information at the end of the ATOM/HETATM records.

1- TITLE SECTION

HEADER 
----------------------------------
The HEADER record uniquely identifies a PDB entry through the idCode field.
This record also provides a classification for the entry. Finally, it contains
the date the coordinates were deposited at the PDB.

OBSLTE 
----------------------------------
OBSLTE appears in entries which have been withdrawn from distribution.
This record acts as a flag in an entry which has been withdrawn from the PDB's
full release. It indicates which, if any, new entries have replaced the withdrawn entry.
The format allows for the case of multiple new entries replacing one existing entry.   

TITLE 
----------------------------------
The TITLE record contains a title for the experiment or analysis that is represented
in the entry. It should identify an entry in the PDB in the same way that a title
identifies a paper.

CAVEAT 
----------------------------------
CAVEAT warns of severe errors in an entry. Use caution when using an entry containing
this record. 

COMPND 
----------------------------------
The COMPND record describes the macromolecular contents of an entry. Each macromolecule
found in the entry is described by a set of token: value pairs, and is referred to as a
COMPND record component. Since the concept of a molecule is difficult to specify exactly,
PDB staff may exercise editorial judgment in consultation with depositors in assigning
these names.
For each macromolecular component, the molecule name, synonyms, number assigned
by the Enzyme Commission (EC), and other relevant details are specified.   

SOURCE 
----------------------------------
The SOURCE record specifies the biological and/or chemical source of each biological
molecule in the entry. Sources are described by both the common name and the scientific
name, e.g., genus and species. Strain and/or cell-line for immortalized cells are given
when they help to uniquely identify the biological entity studied.

KEYWDS 
----------------------------------
The KEYWDS record contains a set of terms relevant to the entry. Terms in the KEYWDS
record provide a simple means of categorizing entries and may be used to generate
index files. This record addresses some of the limitations found in the classification
field of the HEADER record. It provides the opportunity to add further annotation to
the entry in a concise and computer-searchable fashion.

EXPDTA 
----------------------------------
The EXPDTA record presents information about the experiment.
The EXPDTA record identifies the experimental technique used. This may refer to the
type of radiation and sample, or include the spectroscopic or modeling technique.
Permitted values include:
   ELECTRON DIFFRACTION
   FIBER DIFFRACTION
   FLUORESCENCE TRANSFER
   NEUTRON DIFFRACTION
   NMR
   THEORETICAL MODEL
   X-RAY DIFFRACTION  

AUTHOR 
----------------------------------
The AUTHOR record contains the names of the people responsible for the contents of
the entry. 

REVDAT 
----------------------------------
REVDAT records contain a history of the modifications made to an entry since its release.

SPRSDE 
----------------------------------
The SPRSDE records contain a list of the ID codes of entries that were made obsolete
by the given coordinate entry and withdrawn from the PDB release set. One entry may
replace many. It is PDB policy that only the principal investigator of a structure has
the authority to withdraw it.

JRNL 
----------------------------------
The JRNL record contains the primary literature citation that describes the experiment
which resulted in the deposited coordinate set. There is at most one JRNL reference per
entry. If there is no primary reference, then there is no JRNL reference. Other references
are given in REMARK 1.
PDB is in the process of linking and/or adding all references to CitDB, the literature
database used by the Genome Data Base (available at URL
http://gdbwww.gdb.org/gdb-bin/genera/genera/citation/Citation).

REMARK 
----------------------------------
REMARK records present experimental details, annotations, comments, and information not
included in other records. In a number of cases, REMARKs are used to expand the contents
of other record types. A new level of structure is being used for some REMARK records.
This is expected to facilitate searching and will assist in the conversion to a relational
database.

REMARK 1
----------------------------------
REMARK 1 lists important publications related to the structure presented in the entry.
These citations are chosen by the depositor. They are listed in reverse-chronological
order. Citations are not repeated from the JRNL records. After the first blank record
and the REFERENCE sub-record, the sub-record types for REMARK 1 are the same as in the
JRNL sub-record types. For details, see the JRNL section.

PDB is in the process of linking and/or adding references to CitDB, the literature
database of the Genome Data Base (available at URL
http://gdbwww.gdb.org/gdb-bin/genera/genera/citation/Citation).

REMARK 2 
----------------------------------
REMARK 2 states the highest resolution, in Angstroms, that was used in building the model.
As with all the remarks, the first REMARK 2 record is empty and is used as a spacer.

REMARK 3 
----------------------------------
REMARK 3 presents information on refinement program(s) used and the related statistics.
For non-diffraction studies, REMARK 3 is used to describe any refinement done, but its
format in those cases is mostly free text.

If more than one refinement package was used, they may be named in
'OTHER REFINEMENT REMARKS'. However, Remark 3 statistics are given for the final
refinement run.

Refinement packages are being enhanced to output PDB REMARK 3. A token: value
template style facilitates parsing. Spacer REMARK 3 lines are interspersed for
visually organizing the information.

The templates below have been adopted in consultation with program authors. PDB is
continuing this dialogue with program authors, and expects the library of PDB records
output by the programs to greatly increase in the near future.

Instead of providing aRecord Formattable, each template is given as it appears in
PDB entries. 

REMARK N  
----------------------------------
REMARKs following the refinement remark consist of free text annotation, predefined
boilerplate remarks, and token: value pair styled templates. PDB is beginning to organize
the most often used remarks, and assign numbers and topics to them.

Presented here is the scheme being followed in the remark section of PDB files.
The PDB expects to continue to adopt standard text or tables for certain remarks,
as details are worked out. 

2- PRIMARY STRUCTURE SECTION:

DBREF 
----------------------------------
The DBREF record provides cross-reference links between PDB sequences and the
corresponding database entry or entries. A cross reference to the sequence database
is mandatory for each peptide chain with a length greater than ten (10) residues.
For nucleic acid entries a DBREF record pointing to the Nucleic Acid Database (NDB)
is mandatory when the corresponding entry exists in NDB.

SEQADV 
----------------------------------
The SEQADV record identifies conflicts between sequence information in the ATOM records
of the PDB entry and the sequence database entry given on DBREF. Please note that these
records were designed to identify differences and not errors. No assumption is made as
to which database contains the correct data. PDB may include REMARK records in the entry
that reflect the depositor's view of which database has the correct sequence.

SEQRES 
----------------------------------
SEQRES records contain the amino acid or nucleic acid sequence of residues in each
chain of the macromolecule that was studied.

MODRES 
----------------------------------
The MODRES record provides descriptions of modifications (e.g., chemical or
post-translational) to protein and nucleic acid residues. Included are a mapping
between residue names given in a PDB entry and standard residues.

3- HETEROGEN SECTION

HET 
----------------------------------
HET records are used to describe non-standard residues, such as prosthetic groups,
inhibitors, solvent molecules, and ions for which coordinates are supplied. Groups
are considered HET if they are:
  - not one of the standard amino acids, and 
  - not one of the nucleic acids (C, G, A, T, U, and I), and 
  - not one of the modified versions of nucleic acids (+C, +G, +A, +T, +U, and +I), and 
  - not an unknown amino acid or nucleic acid where UNK is used to indicate the
unknown residue name. 
Het records also describe heterogens for which the chemical identity is unknown,
in which case the group is assigned the hetID UNK. 

HETNAM 
----------------------------------
This record gives the chemical name of the compound with the given hetID.

HETSYN 
----------------------------------
This record provides synonyms, if any, for the compound in the corresponding
(i.e., same hetID) HETNAM record. This is to allow greater flexibility in searching
for HET groups.

FORMUL 
----------------------------------
The FORMUL record presents the chemical formula and charge of a non-standard group.
(The formulas for the standard residues are given in Appendix 5.)

4- SECONDARY STRUCTURE SECTION

HELIX 
----------------------------------
HELIX records are used to identify the position of helices in the molecule.
Helices are both named and numbered. The residues where the helix begins and ends are
noted, as well as the total length.

SHEET 
----------------------------------
SHEET records are used to identify the position of sheets in the molecule.
Sheets are both named and numbered. The residues where the sheet begins and ends are
noted.

TURN 
----------------------------------
The TURN records identify turns and other short loop turns which normally connect other
secondary structure segments.

5- CONNECTIVITY ANNOTATION SECTION:

SSBOND 
----------------------------------
The SSBOND record identifies each disulfide bond in protein and polypeptide structures
by identifying the two residues involved in the bond.

LINK :
----------------------------------
The LINK records specify connectivity between residues that is not implied by the
primary structure. Connectivity is expressed in terms of the atom names.
This record supplements information given in CONECT records and is provided here
for convenience in searching.

HYDBND 
----------------------------------
The HYDBND records specify hydrogen bonds in the entry.

SLTBRG 
----------------------------------
The SLTBRG records specify salt bridges in the entry.

CISPEP 
----------------------------------
CISPEP records specify the prolines and other peptides found to be in the cis
conformation. This record replaces the use of footnote records to list cis peptides.

6- MISCELLANEOUS FEATURES SECTION:

SITE 
----------------------------------
The SITE records supply the identification of groups comprising important sites
in the macromolecule.

7- CRYSTALLOGRAPHIC COORDINATE TRANSFORMATION SECTION

CRYST1 
----------------------------------
The CRYST1 record presents the unit cell parameters, space group, and Z value.
If the structure was not determined by crystallographic means, CRYST1 simply defines
a unit cube.

ORIGX 1,2,3
----------------------------------
The ORIGXn (n = 1, 2, or 3) records present the transformation from the orthogonal
coordinates contained in the entry to the submitted coordinates.

SCALE 1,2,3
----------------------------------
The SCALEn (n = 1, 2, or 3) records present the transformation from the orthogonal
coordinates as contained in the entry to fractional crystallographic coordinates.
Non-standard coordinate systems should be explained in the remarks.

MTRIX 1,2,3
----------------------------------
The MTRIXn (n = 1, 2, or 3) records present transformations expressing
non-crystallographic symmetry.

TVECT 
----------------------------------
The TVECT records present the translation vector for infinite covalently
connected structures.

8- COORDINATE SECTION
======================================================

MODEL 
----------------------------------
The MODEL record specifies the model serial number when multiple structures are
presented in a single coordinate entry, as is often the case with structures determined
by NMR.
                                       
ATOM 
----------------------------------
The ATOM records present the atomic coordinates for standard residues.
They also present the occupancy and temperature factor for each atom. Heterogen
coordinates use the HETATM record type. The element symbol is always present on each
ATOM record; segment identifier and charge are optional.

SIGATM 
----------------------------------
The SIGATM records present the standard deviation of atomic parameters as they appear
in ATOM and HETATM records.

ANISOU 
----------------------------------
The ANISOU records present the anisotropic temperature factors.

SIGUIJ 
----------------------------------
The SIGUIJ records present the standard deviations of anisotropic temperature factors
scaled by a factor of 10**4 (Angstroms**2).

TER 
----------------------------------
The TER record indicates the end of a list of ATOM/HETATM records for a chain.

HETATM 
----------------------------------
The HETATM records present the atomic coordinate records for atoms within
'non-standard' groups. These records are used for water molecules and atoms presented
in HET groups.

ENDMDL 
----------------------------------
The ENDMDL records are paired with MODEL records to group individual structures
found in a coordinate entry.

9- CONNECTIVITY SECTION

CONECT 
----------------------------------
The CONECT records specify connectivity between atoms for which coordinates are
supplied. The connectivity is described using the atom serial number as found in
the entry. CONECT records are mandatory for HET groups (excluding water) and for
other bonds not specified in the standard residue connectivity table which involve
atoms in standard residues (see Appendix 4 for the list of standard residues).
These records are generated by the PDB.

10- BOOKKEEPING SECTION:

MASTER 
----------------------------------
The MASTER record is a control record for bookkeeping. It lists the number of lines
in the coordinate entry or file for selected record types.

END
----------------------------------
The END record marks the end of the PDB file
"""


class MoleculeLoader(MVCommand):
    """Base class for all the classes in this module
   \nPackage : Pmv
   \nModule  : bondsCommands
   \nClass   : MoleculeLoader
   """
    def __init__(self):
        MVCommand.__init__(self)
        self.fileTypes = [('all', '*')]
        self.fileBrowserTitle = "Read File"
        self.lastDir = "."


    def onRemoveObjectFromViewer(self, obj):
        """ Function to remove the sets able to reference a TreeNode created
        in this command : Here remove the alternate location list created
        when a pdb File is read."""
        if self.vf.undoableDelete__: return
        try:
            atms = obj.findType(Atom)
            for a in atms:
                if hasattr(a, 'alternate'):
                    delattr(a, 'alternate')
        except:
            print "exception in MolecularLoader.onRemoveObjectFromViewer", obj.name
        #del atms

    def guiCallback(self, event=None, *args, **kw):
        cmdmenuEntry = self.GUI.menu[4]['label']
        files = self.vf.askFileOpen(types=self.fileTypes,
                                    idir=self.lastDir,
                                    title=self.fileBrowserTitle,
                                    multiple=True)
        mols = MoleculeSet([])
        for file in files:
            mol = None
            self.lastDir = os.path.split(file)[0]
            self.vf.GUI.configMenuEntry(self.GUI.menuButton, cmdmenuEntry,
                                        state='disabled')
            mol = self.vf.tryto(self.doitWrapper, file)
            self.vf.GUI.configMenuEntry(self.GUI.menuButton,
                                        cmdmenuEntry,state='normal')
            mols.extend(mol.data)
            self.vf.recentFiles.add(file, self.name)

        if len(mols): return mols
        else: return None
        

class MoleculeReader(MoleculeLoader):
    """Command to read molecule
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : MoleculeReader
    \nCommand :readMolecule
    \nSynopsis:\n
        mols <- readMolecule(filename,parser=None, **kw)
    \nRequired Arguments:\n
    filename --- path to a file describing a molecule\n
    parser  --- you can specify the parser to use to parse the file has to be one of 'PDB', 'PDBQ', 'PDBQS','PDBQT', 'PQR', 'MOL2'.This is useful when your file doesn't have the correct extension.
    """
    lastDir = None
    
    def __init__(self):
        MoleculeLoader.__init__(self)
        self.fileTypes =[(
            'All supported files',
            '*.cif *.mol2 *.pdb *.pqr *.pdbq *.pdbqs *.pdbqt *.f2d *.gro')]
        self.fileTypes += [('PDB files', '*.pdb'),
                           ('MEAD files', '*.pqr'),('MOL2 files', '*.mol2'),
                           ('AutoDock files (pdbq)', '*.pdbq'),
                           ('AutoDock files (pdbqs)', '*.pdbqs'),
                           ('AutoDock files (pdbqt)', '*.pdbqt'),
                           ('Gromacs files (gro)', '*.gro'),
                           ('F2Dock input molecule files (f2d)', '*.fd2'),
                           ]

        self.parserToExt = {'PDB':'.pdb', 'PDBQ':'.pdbq',
                            'PDBQS':'.pdbqs', 'PDBQT':'.pdbqt',
                            'MOL2':'.mol2',
                            'PQR':'.pqr',
                            'GRO':'.gro',
                            'F2D':'.f2d',
                            }
        self.fileTypes += [('MMCIF files', '*.cif'),]
        self.parserToExt['CIF'] = '.cif'
        self.fileTypes += [('All files', '*')]
        self.fileBrowserTitle ="Read Molecule:"


    def onAddCmdToViewer(self):
        # Do  that better
        self.vf.loadCommand("fileCommands", ["readPDBQ",
                                             "readPDBQS", 
                                             "readPDBQT", 
                                             "readPQR",
                                             "readF2D",
                                             "readMOL2",
                                             "readPDB",
                                             "readGRO",
                                             ], "Pmv",
                            topCommand=0)
        self.vf.loadCommand("fileCommands", ["readMMCIF"], "Pmv",
                                topCommand=0)
        if self.vf.hasGui:
            self.modelsAsMols = Tkinter.IntVar()
            self.modelsAsMols.set(1)
            self.doModelUpdates = Tkinter.IntVar()
            self.doModelUpdates.set(0)
        self.setModelUpdates = None


    def processArrowEvent(self, event):
        #detect molecules with conformations and vina_results
        mols = self.vf.Mols.get(lambda x: len(x.allAtoms[0]._coords)>1)
        if not len(mols):
            return
        if hasattr(event, 'keysym') and event.keysym=='Right':
            #print "Right"
            for m in mols:
                geom = m.geomContainer.geoms['ProteinLabels']
                ind = m.allAtoms[0].conformation
                nconf = len(m.allAtoms[0]._coords)
                if ind+1 < nconf:
                    m.allAtoms.setConformation(ind+1)
                    event = EditAtomsEvent('coords', m.allAtoms)
                    self.vf.dispatchEvent(event)
                else:
                    print 'last conformation of ', m.name
        if hasattr(event, 'keysym') and event.keysym=='Left':
            #print "Left"
            for m in mols:
                geom = m.geomContainer.geoms['ProteinLabels']
                ind = m.allAtoms[0].conformation
                if ind > 0:
                    ind = ind - 1
                    m.allAtoms.setConformation(ind)
                    event = EditAtomsEvent('coords', m.allAtoms)
                    self.vf.dispatchEvent(event)
                else:
                    print 'first conformation of ', m.name


    def buildFormDescr(self, formName):
        if formName == 'parser':
            idf =  InputFormDescr(title=self.name)
            label = self.fileExt + " has not been recognized\n please choose a parser:"
            l = ['PDB','PDBQ', 'PDBQS', 'PDBQT','MOL2','PQR', 'F2D']
            l.append('MMCIF')
            idf.append({'name':'parser',
                        'widgetType':Pmw.RadioSelect,
                        'listtext':l,
                        'defaultValue':'PDB',
                        'wcfg':{'labelpos':'nw', 'label_text':label,
                                'orient':'horizontal',
                                'buttontype':'radiobutton'},
                        'gridcfg':{'sticky': 'we'}})
            return idf
            

    def guiCallback(self, event=None, *args, **kw):
        cmdmenuEntry = self.GUI.menu[4]['label']
        files = self.vf.askFileOpen(types=self.fileTypes,
                                    idir=self.lastDir,
                                    title=self.fileBrowserTitle,
                                    multiple=True)
        if files is None:
            return None
        
        mols = MoleculeSet([])
        for file in files:
            mol = None
            self.lastDir = os.path.split(file)[0]
            self.fileExt = os.path.splitext(file)[1]
            if not self.fileExt in [".pdb",".pdbq", ".pdbqs", ".pdbqt", 
                                    ".mol2", ".pqr", ".f2d", ".cif",".gro"]:
                # popup a pannel to allow the user to choose the parser
                val = self.showForm('parser')
                if not val == {}:
                    self.fileExt = self.parserToExt[val['parser']]
            self.vf.GUI.configMenuEntry(self.GUI.menuButton,
                                        cmdmenuEntry,
                                        state='disabled')

            mol = self.vf.tryto(self.doitWrapper, file, kw={})
            self.vf.GUI.configMenuEntry(self.GUI.menuButton,
                                        cmdmenuEntry,state='normal')
            if mol is not None:
                mols.data.extend(mol.data)

        if len(mols): return mols
        else: return None


    def __call__(self, filename, parser=None, **kw):
        """mols <- readMolecule(filename,parser=None, **kw)
           \nfilename --- path to a file describing a molecule
           \nparser --- you can specify the parser to use to parse the file
                     has to be one of 'PDB', 'PDBQ', 'PDBQS','PDBQT', 'PQR', 'MOL2'.
                     This is useful when your file doesn't have the correct
                     extension.
           """
        self.fileExt = os.path.splitext(filename)[1]
        kw['parser'] = parser
        kw['ask']=0
        return apply ( self.doitWrapper, (filename,), kw)


    def doit(self, filename, parser=None, ask=True, addToRecent=True, **kw):
        import os
        if not os.path.exists(filename):
            self.warningMsg("ERROR: %s doesn't exists"%filename)
            return None

        if not parser is None and self.parserToExt.has_key(parser):
            self.fileExt = self.parserToExt[parser]
        # Call the right parser
        if self.fileExt == ".pdb" or self.fileExt == ".ent":
            # Call readPDB
            mols = self.vf.readPDB(filename, ask=ask, topCommand=0)
        elif self.fileExt == ".pdbq":
            # Call readPDBQ
            mols = self.vf.readPDBQ(filename, ask=ask,topCommand=0)
        elif self.fileExt == ".pdbqs":
            # Call readPDBQS
            mols = self.vf.readPDBQS(filename,ask=ask, topCommand=0)
        elif self.fileExt == ".pdbqt":
            foundModelsAs = kw.has_key("modelsAs")
            #print "readMolecule: foundModelsAs=", foundModelsAs
            setupUpdates = kw.get("setupUpdates", 0)
            #print "readMolecule: setupUpdates=", setupUpdates
            #set default in any case
            modelsAs = kw.get('modelsAs', 'molecules')
            #check for multimodel file
            fptr = open(filename)
            lines = fptr.readlines()
            fptr.close()
            found = 0
            for l in lines:
                if l.find("MODEL")==0:
                    found = found + 1
                    if found>1:
                        break
            if found > 0:
                if not foundModelsAs:
                    ifd = InputFormDescr(title="Load MODELS as: ")
                    ifd.append({'name': 'ModelsAsMols',
                        'text': 'separate molecules',
                        'widgetType':Tkinter.Radiobutton,
                        'tooltip':'Check this button to add a separate molecule for each model.',
                        'variable': self.modelsAsMols,
                        'value': '1',
                        'text': 'Molecules           ',
                        'gridcfg': {'sticky':'w','columnspan':2}})
                    ifd.append({'name': 'ModelsAsConfs',
                        'widgetType':Tkinter.Radiobutton,
                        'tooltip':'Check this button to add a single molecule\n with a separate conformation for each model',
                        'variable': self.modelsAsMols,
                        'value': '0',
                        'text': 'Conformations       ',
                        'gridcfg': {'sticky':'w'}}) 
                    ifd.append({'name': 'updates label',
                        'widgetType':Tkinter.Label,
                        'tooltip':'On sets changing models with arrow keys',
                        'text': 'If conformations, change models using arrow keys',
                        'gridcfg': {'sticky':'w', 'column':0, 'columnspan':2}}) 
                    ifd.append({'name': 'updates',
                        'widgetType':Tkinter.Radiobutton,
                        'tooltip':'Yes sets changing models with arrow keys',
                        'variable': self.doModelUpdates,
                        'value': '1',
                        'text': 'Yes',
                        'gridcfg': {'sticky':'w', 'column':0}}) 
                    ifd.append({'name': 'no_updates',
                        'widgetType':Tkinter.Radiobutton,
                        'tooltip':'No do not change models with arrow keys',
                        'variable': self.doModelUpdates,
                        'value': '0',
                        'text': 'No',
                        'gridcfg': {'sticky':'w', 'row':-1, 'column':1}}) 
                    d = self.vf.getUserInput(ifd)
                    # if cancel, stop
                    if not len(d): return
                    ans = d['ModelsAsMols']
                    if not ans: 
                        modelsAs = 'conformations'
                if modelsAs=='conformations' and (self.doModelUpdates.get() or setupUpdates):
                    e = self.vf.GUI.VIEWER.currentCamera.eventManager
                    if "<Right>" in e.eventHandlers.keys():
                        l = e.eventHandlers["<Right>"]
                        if self.processArrowEvent not in l:
                            self.vf.GUI.addCameraCallback("<Right>", self.processArrowEvent)
                    else:
                        self.vf.GUI.addCameraCallback("<Right>", self.processArrowEvent)

                    if "<Left>" in e.eventHandlers.keys():
                        l = e.eventHandlers["<Left>"]
                        if self.processArrowEvent not in l:
                            self.vf.GUI.addCameraCallback("<Left>", self.processArrowEvent)
                    else:
                        self.vf.GUI.addCameraCallback("<Left>", self.processArrowEvent)
                    #self.warningMsg("added arrow keys to camera callbacks!")

            # Call readPDBQT
            mols = self.vf.readPDBQT(filename, ask=ask, modelsAs=modelsAs, 
                                    setupUpdates=setupUpdates, topCommand=0)
        elif self.fileExt == ".pqr":
            # Call readPQR
            mols = self.vf.readPQR(filename,ask=ask, topCommand=0)
        elif self.fileExt == ".mol2":
            # Call readMOL2
            mols = self.vf.readMOL2(filename,ask=ask, topCommand=0)
        elif self.fileExt == ".cif":
            # Call readMMCIF
            mols = self.vf.readMMCIF(filename, ask=ask, topCommand=0)
        elif self.fileExt == ".gro":
            # Call readGRO
            mols = self.vf.readGRO(filename, ask=ask, topCommand=0)
        elif self.fileExt == ".f2d":
            # Call readGRO
            mols = self.vf.readF2D(filename, ask=ask, topCommand=0)
        else:
            self.warningMsg("ERROR: Extension %s not recognized"%self.fileExt)
            return None
        if mols is None:
            self.warningMsg("ERROR: Could not read %s"%filename)
        if addToRecent and hasattr(self.vf,'recentFiles'):
            self.vf.recentFiles.add(filename, self.name)
        return mols
    
from Pmv.fileCommandsGUI import MoleculeReaderGUI
                                 
class PDBReader(MoleculeLoader):
    """Command to load PDB files using a PDB spec compliant parser
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : MoleculeReader
    \nCommand : readMolecule 
    \nSynopsis:\n
        mols <--- readPDB(filename, **kw)
    \nRequired Arguments:\n
        filename --- path to the PDB file
    """

    lastDir = None

    def onAddCmdToViewer(self):
        if not hasattr(self.vf,'readMolecule'):
            self.vf.loadCommand('fileCommands', ['readMolecule'], 'Pmv',
                                topCommand=0)
        

    def onRemoveObjectFromViewer(self, obj):
        """ Function to remove the sets able to reference a TreeNode created
        in this command : Here remove the alternate location list created
        when a pdb File is read."""
        if self.vf.undoableDelete__: return
        if not hasattr(obj, 'parser') or \
           not isinstance(obj.parser, PdbParser): return
        MoleculeLoader.onRemoveObjectFromViewer(self, obj)
        # Free the parser too !
        # this dictionary contains referneces to itself through function.
        if hasattr(obj.parser, 'pdbRecordParser'):
            del obj.parser.pdbRecordParser
        if hasattr(obj.parser, 'mol'):
            del obj.parser.mol
        del obj.parser
        

    def doit(self, filename, ask=True):
        modelsAs = self.vf.userpref['Read molecules as']['value']
        newparser = PdbParser(filename,modelsAs=modelsAs)

        # overwrite progress bar methods
        if self.vf.hasGui:
            newparser.updateProgressBar = self.vf.GUI.updateProgressBar
            newparser.configureProgressBar = self.vf.GUI.configureProgressBar

        mols = newparser.parse()
        if mols is None: return
        newmol = []
        for m in mols:
            mol = self.vf.addMolecule(m, ask)
            if mol is None:
                del newparser
                return mols.__class__([])
            newmol.append(mol)
                
        return mols.__class__(newmol)
    
    
    def __call__(self, filename, **kw):
        """mols <- readPDB(filename, **kw)
        \nfilename --- path to the PDB file"""

        kw['ask']=0
        return apply ( self.doitWrapper, (filename,), kw)
        
pdbReaderGuiDescr = {'widgetType':'Menu', 'menyBarName':'menuRoot',
                     'menuButtonName':'File',
                     'menyEntryLabel':'Read PDB ...',
                     'index':0}

#PDBReaderGUI = CommandGUI()
#PDBReaderGUI.addMenuCommand('menuRoot', 'File', 'Read PDB ...',index=0)

class MMCIFReader(MoleculeLoader):
    """This command reads macromolecular Crystallographic Information File (mmCIF)
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : MMCIFReader
    \nCommand :readMMCIF
    \nSynopsis:\n
        mols <- readMMCIF(filename, **kw)
    \nRequired Arguments:\n
        filename --- path to the MMCIF file
    """
    lastDir = None

    def onAddCmdToViewer(self):
        if not hasattr(self.vf,'readMolecule'):
            self.vf.loadCommand('fileCommands', ['readMolecule'], 'Pmv',
                                topCommand=0)

    def onRemoveObjectFromViewer(self, obj):
        """ Function to remove the sets able to reference a TreeNode created
        in this command : Here remove the alternate location list created
        when a pdb File is read."""
        if self.vf.undoableDelete__: return
        if not hasattr(obj, 'parser') or \
           not isinstance(obj.parser, PdbParser): return
        MoleculeLoader.onRemoveObjectFromViewer(self, obj)
        # Free the parser too !
        # this dictionary contains referneces to itself through function.
        if hasattr(obj.parser, 'pdbRecordParser'):
            del obj.parser.pdbRecordParser
        if hasattr(obj.parser, 'mol'):
            del obj.parser.mol
        del obj.parser


    def doit(self, filename, ask=True):
        newparser = MMCIFParser(filename)

        # overwrite progress bar methods
        if self.vf.hasGui:
            newparser.updateProgressBar = self.vf.GUI.updateProgressBar
            newparser.configureProgressBar = self.vf.GUI.configureProgressBar

        mols = newparser.parse()
        if mols is None: return
        newmol = []
        for m in mols:
            mol = self.vf.addMolecule(m, ask)
            if mol is None:
                del newparser
                return mols.__class__([])
            newmol.append(mol)
                
        return mols.__class__(newmol)
    
    
    def __call__(self, filename, **kw):
        """mols <- readMMCIF(filename, **kw)
        \nfilename --- path to the PDB file"""

        kw['ask']=0
        return apply ( self.doitWrapper, (filename,), kw)
        
    
class GROReader(MoleculeLoader):
    """This command reads macromolecular Crystallographic Information File (mmCIF)
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : MMCIFReader
    \nCommand :readMMCIF
    \nSynopsis:\n
        mols <- readMMCIF(filename, **kw)
    \nRequired Arguments:\n
        filename --- path to the MMCIF file
    """
    lastDir = None

    def onAddCmdToViewer(self):
        if not hasattr(self.vf,'readMolecule'):
            self.vf.loadCommand('fileCommands', ['readMolecule'], 'Pmv',
                                topCommand=0)


    def onRemoveObjectFromViewer(self, obj):
        """ Function to remove the sets able to reference a TreeNode created
        in this command : Here remove the alternate location list created
        when a pdb File is read."""
        if self.vf.undoableDelete__: return
        if not hasattr(obj, 'parser') or \
           not isinstance(obj.parser, PdbParser): return
        MoleculeLoader.onRemoveObjectFromViewer(self, obj)
        # Free the parser too !
        # this dictionary contains referneces to itself through function.
        if hasattr(obj.parser, 'pdbRecordParser'):
            del obj.parser.pdbRecordParser
        if hasattr(obj.parser, 'mol'):
            del obj.parser.mol
        del obj.parser


    def doit(self, filename, ask=True):
        newparser = groParser(filename)

        # overwrite progress bar methods
        if self.vf.hasGui:
            newparser.updateProgressBar = self.vf.GUI.updateProgressBar
            newparser.configureProgressBar = self.vf.GUI.configureProgressBar

        mols = newparser.parse()
        if mols is None: return
        newmol = []
        for m in mols:
            mol = self.vf.addMolecule(m, ask)
            if mol is None:
                del newparser
                return mols.__class__([])
            newmol.append(mol)
                
        return mols.__class__(newmol)
    
    
    def __call__(self, filename, **kw):
        """mols <- readGRO(filename, **kw)
        \nfilename --- path to the PDB file"""

        kw['ask']=0
        return apply ( self.doitWrapper, (filename,), kw)


class PDBQReader(MoleculeLoader):
    """Command to load AutoDock PDBQ files.
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : PDBQReader
    \nCommand : readPDBQ
    \nSynopsis:\n
    mols <--- readPDBQ(filename, **kw)
    \nRequired Arguments:\n
    filename --- path to the PDBQ file
    """
    

    def onAddCmdToViewer(self):
        if not hasattr(self.vf,'readMolecule'):
            self.vf.loadCommand('fileCommands', ['readMolecule'], 'Pmv',
                                topCommand=0)

    def onRemoveObjectFromViewer(self, obj):
        """ Function to remove the sets able to reference a TreeNode created
        in this command : Here remove the alternate location list created
        when a pdb File is read."""
        if self.vf.undoableDelete__: return
        if not hasattr(obj, 'parser') or \
           not isinstance(obj.parser, PdbqParser): return
        MoleculeLoader.onRemoveObjectFromViewer(self, obj)
        # Free the parser too !
        # this dictionary contains referneces to itself through function.
        if hasattr(obj.parser, 'pdbRecordParser'):
            del obj.parser.pdbRecordParser
        if hasattr(obj.parser, 'mol'):
            del obj.parser.mol
        if hasattr(obj, 'ROOT'):
            delattr(obj, 'ROOT')
        if hasattr(obj, 'torTree') and hasattr(obj.torTree, 'parser'):
            delattr(obj.torTree, 'parser')
        del obj.parser


    def doit(self, filename, ask=True ):
        newparser = PdbqParser(filename )
        mols = newparser.parse()
        if mols is None: return
        newmol = []
        for m in mols:
            mol = self.vf.addMolecule(m, ask)
            if mol is None:
                del newparser
                return mols.__class__([])
            newmol.append(mol)
        return mols.__class__(newmol)

    def __call__(self, filename, **kw):
        """mols <- readPDBQ(filename, **kw)
        \nfilename --- path to the PDBQ file"""

        kw['ask']=0
        return apply ( self.doitWrapper, (filename,), kw)
        
pdbqReaderGuiDescr = {'widgetType':'Menu', 'menyBarName':'menuRoot',
                      'menuButtonName':'File',
                      'menyEntryLabel':'Read PDBQ ...',
                      'index':0}

#PDBQReaderGUI = CommandGUI()
#PDBQReaderGUI.addMenuCommand('menuRoot', 'File', 'Read PDBQ ...', index=0)



class PDBQSReader(MoleculeLoader):
    """Command to load AutoDock PDBQS files
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : PDBQSReader
    \nCommand : readPDBQS
    \nSynopsis:\n
        mols <--- readPDBQS(filename, **kw)
    \nRequired Arguments:\n    
        filename --- path to the PDBQS file
    """
    

    def onAddCmdToViewer(self):
        if not hasattr(self.vf,'readMolecule'):
            self.vf.loadCommand('fileCommands', ['readMolecule'], 'Pmv',
                                topCommand=0)

    def onRemoveObjectFromViewer(self, obj):
        """ Function to remove the sets able to reference a TreeNode created
        in this command : Here remove the alternate location list created
        when a pdb File is read."""
        if self.vf.undoableDelete__: return
        if not hasattr(obj, 'parser') or \
        not isinstance(obj.parser, PdbqsParser): return
        MoleculeLoader.onRemoveObjectFromViewer(self, obj)
        # Free the parser too !
        # this dictionary contains referneces to itself through function.
        if hasattr(obj.parser, 'pdbRecordParser'):
            del obj.parser.pdbRecordParser
        if hasattr(obj.parser, 'mol'):
            del obj.parser.mol
        if hasattr(obj, 'ROOT'):
            delattr(obj, 'ROOT')
        if hasattr(obj, 'torTree') and hasattr(obj.torTree, 'parser'):
            delattr(obj.torTree, 'parser')
        del obj.parser


    def doit(self, filename, ask=True):
        newparser = PdbqsParser(filename)
        mols = newparser.parse()
        if mols is None: return
        newmol = []
        for m in mols:
            mol = self.vf.addMolecule(m, ask)
            if mol is None:
                del newparser
                return mols.__class__([])
            newmol.append(mol)
        return mols.__class__(newmol)


    def __call__(self, filename, **kw):
        """mols <--- readPDBQS(filename, **kw)
        \nfilename --- path to the PDBQS file"""

        kw['ask']=0
        return apply ( self.doitWrapper, (filename,), kw)
        
pdbqsReaderGuiDescr = {'widgetType':'Menu', 'menyBarName':'menuRoot',
                       'menuButtonName':'File',
                       'menyEntryLabel':'Read PDBQS ...',
                       'index':0}

#PDBQSReaderGUI = CommandGUI()
#PDBQSReaderGUI.addMenuCommand('menuRoot', 'File', 'Read PDBQS ...', index=0)


class PDBQTReader(MoleculeLoader):
    """Command to load AutoDock PDBQT files
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : PDBQTReader
    \nCommand :readPDBQT
    \nSynopsis:\n
        mols <--- readPDBQT(filename, **kw)
    \nRequired Arguments:\n      
        filename --- path to the PDBQT file
    """
    

    def onAddCmdToViewer(self):
        if not hasattr(self.vf,'readMolecule'):
            self.vf.loadCommand('fileCommands', ['readMolecule'], 'Pmv',
                                topCommand=0)


    def onRemoveObjectFromViewer(self, obj):
        """ Function to remove the sets able to reference a TreeNode created
        in this command : Here remove the alternate location list created
        when a pdb File is read."""
        if self.vf.undoableDelete__: return
        if not hasattr(obj, 'parser') or \
        not isinstance(obj.parser, PdbqtParser): return
        MoleculeLoader.onRemoveObjectFromViewer(self, obj)
        # Free the parser too !
        # this dictionary contains referneces to itself through function.
        if hasattr(obj.parser, 'pdbRecordParser'):
            del obj.parser.pdbRecordParser
        if hasattr(obj.parser, 'mol'):
            del obj.parser.mol
        if hasattr(obj, 'ROOT'):
            delattr(obj, 'ROOT')
        if hasattr(obj, 'torTree') and hasattr(obj.torTree, 'parser'):
            delattr(obj.torTree, 'parser')
        del obj.parser


    def processArrowEvent(self, event):
        #detect molecules with conformations and vina_results
        mols = self.vf.Mols.get(len(x.allAtoms[0]._coords)>1)
        print "readPDBQT:  mols=", mols
        if not len(mols):
            return
        if hasattr(event, 'keysym') and event.keysym=='Right':
            #print "Right"
            for m in mols:
                print m.name
                geom = m.geomContainer.geoms['ProteinLabels']
                ind = m.allAtoms[0].conformation
                nconf = len(m.allAtoms[0]._coords)
                if ind+1 < nconf:
                    m.allAtoms.setConformation(ind+1)
                    event = EditAtomsEvent('coords', m.allAtoms)
                    self.vf.dispatchEvent(event)
                else:
                    print 'last MODEL of ', m.name
        if hasattr(event, 'keysym') and event.keysym=='Left':
            #print "Left"
            for m in mols:
                print m.name,
                geom = m.geomContainer.geoms['ProteinLabels']
                ind = m.allAtoms[0].conformation
                if ind > 0:
                    ind = ind - 1
                    m.allAtoms.setConformation(ind)
                    event = EditAtomsEvent('coords', m.allAtoms)
                    self.vf.dispatchEvent(event)
                else:
                    print 'first MODEL of ', m.name


    def doit(self, filename, ask=True, modelsAs='molecules', **kw):
        #msg ="readPDBQT: modelsAs=" + modelsAs
        #self.vf.warningMsg(msg)
        newparser = PdbqtParser(filename, modelsAs=modelsAs)
        mols = newparser.parse()
        if mols is None: return
        newmol = []
        for m in mols:
            mol = self.vf.addMolecule(m, ask)
            if mol is None:
                del newparser
                return mols.__class__([])
            newmol.append(mol)
        return mols.__class__(newmol)


    def __call__(self, filename, **kw):
        """mols <--- readPDBQT(filename, **kw)
        \nfilename --- path to the PDBQT file"""

        kw['ask']=0
        return apply ( self.doitWrapper, (filename,), kw)
        

pdbqtReaderGuiDescr = {'widgetType':'Menu', 'menyBarName':'menuRoot',
                       'menuButtonName':'File',
                       'menyEntryLabel':'Read PDBQT ...',
                       'index':0}


#PDBQTReaderGUI = CommandGUI()
#PDBQTReaderGUI.addMenuCommand('menuRoot', 'File', 'Read PDBQT ...', index=0)


class PQRReader(MoleculeLoader):
    """Command to load MEAD PQR files
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : PQRReader
    \nCommand : readpqr
    \nSynopsis:\n 
        mols <- readPQR(filename, **kw)
    \nRequired Arguments:\n   
        filename --- path to the PQR file
    """
    

    def onAddCmdToViewer(self):
        if not hasattr(self.vf,'readMolecule'):
            self.vf.loadCommand('fileCommands', ['readMolecule'], 'Pmv',
                                topCommand=0)


    def onRemoveObjectFromViewer(self, obj):
        """ Function to remove the sets able to reference a TreeNode created
        in this command : Here remove the alternate location list created
        when a pdb File is read."""
        if self.vf.undoableDelete__: return
        if not hasattr(obj, 'parser') or \
           not isinstance(obj.parser, PQRParser): return
        MoleculeLoader.onRemoveObjectFromViewer(self, obj)
        # Free the parser too !
        # this dictionary contains referneces to itself through function.
        if hasattr(obj.parser, 'pdbRecordParser'):
            del obj.parser.pdbRecordParser
        if hasattr(obj.parser, 'mol'):
            del obj.parser.mol
        del obj.parser


    def doit(self, filename, ask=True):
        newparser = PQRParser(filename)
        mols = newparser.parse()
        if mols is None : return
        newmol = []
        for m in mols:
            mol = self.vf.addMolecule(m, ask)
            if mol is None:
                del newparser
                return mols.__class__([])
            newmol.append(mol)
        return mols.__class__(newmol)


    def __call__(self, filename, **kw):
        """mols <--- readPQR(filename, **kw)
        \nfilename --- path to the PQR file"""

        kw['ask']=0
        return apply ( self.doitWrapper, (filename,), kw)

pqrReaderGuiDescr = {'widgetType':'Menu', 'menyBarName':'menuRoot',
                     'menuButtonName':'File',
                     'menyEntryLabel':'Read PQR ...',
                     'index':0}

#PQRReaderGUI = CommandGUI()
#PQRReaderGUI.addMenuCommand('menuRoot', 'File', 'Read PQR ...',index=0)

class F2DReader(MoleculeLoader):
    """Command to load F2Dock .f2d files
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : F2DReader
    \nCommand : readF2D
    \nSynopsis:\n 
        mols <- readF2D(filename, **kw)
    \nRequired Arguments:\n   
        filename --- path to the F2D file
    """
    

    def onRemoveObjectFromViewer(self, obj):
        """ Function to remove the sets able to reference a TreeNode created
        in this command : Here remove the alternate location list created
        when a pdb File is read."""
        if self.vf.undoableDelete__: return
        if not hasattr(obj, 'parser') or \
           not isinstance(obj.parser, Mol2Parser): return
        MoleculeLoader.onRemoveObjectFromViewer(self, obj)
        if hasattr(obj.parser, 'mol2RecordParser'):
            del obj.parser.mol2RecordParser
        if hasattr(obj.parser, 'mol'):
            del obj.parser.mol
        del obj.parser


    def doit(self, filename, ask=True):
        newparser = F2DParser(filename)
        mols = newparser.parse()
        if mols is None : return
        newmol = []
        for m in mols:
            mol = self.vf.addMolecule(m, ask)
            if mol is None:
                del newparser
                return mols.__class__([])
            newmol.append(mol)
        return mols.__class__(newmol)


    def __call__(self, filename, **kw):
        """mols <--- readF2D(filename, **kw)
        \nfilename --- path to the F2D file"""

        kw['ask']=0
        return apply ( self.doitWrapper, (filename,), kw)

f2dReaderGuiDescr = {'widgetType':'Menu', 'menyBarName':'menuRoot',
                     'menuButtonName':'File',
                     'menyEntryLabel':'Read F2D ...',
                     'index':0}


class MOL2Reader(MoleculeLoader):
    """Command to load MOL2 files
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : MOL2Reader
    \nCommand : readMOL2
    \nSynopsis:\n
        mols <- readMOL2(filename, **kw)
    \nRequired Arguments:\n       
        filename --- path to the MOL2 file
    """
    from MolKit.mol2Parser import Mol2Parser


    def onAddCmdToViewer(self):
        if not hasattr(self.vf,'readMolecule'):
            self.vf.loadCommand('fileCommands', ['readMolecule'], 'Pmv',
                                topCommand=0)

    def onRemoveObjectFromViewer(self, obj):
        """ Function to remove the sets able to reference a TreeNode created
        in this command : Here remove the alternate location list created
        when a pdb File is read."""
        if self.vf.undoableDelete__: return
        if not hasattr(obj, 'parser') or \
           not isinstance(obj.parser, Mol2Parser): return
        MoleculeLoader.onRemoveObjectFromViewer(self, obj)
        if hasattr(obj.parser, 'mol2RecordParser'):
            del obj.parser.mol2RecordParser
        if hasattr(obj.parser, 'mol'):
            del obj.parser.mol
        del obj.parser


    def doit(self, filename, ask=True):
        newparser = Mol2Parser(filename)
        mols = newparser.parse()
        newmol = []
        if mols is None: return
        for m in mols:
            mol = self.vf.addMolecule(m, ask)
            if mol is None:
                del newparser
                return mols.__class__([])
            newmol.append(mol)
        return mols.__class__(newmol)

    
    def __call__(self, filename, **kw):
        """mols <- readMOL2(filename, **kw)
        \nfilename --- path to the MOL2 file"""
        kw['ask']=0
        return apply ( self.doitWrapper, (filename,), kw )

mol2ReaderGuiDescr = {'widgetType':'Menu', 'menyBarName':'menuRoot',
                      'menuButtonName':'File',
                      'menyEntryLabel':'Read MOL2 ...',
                      'index':0}

#MOL2ReaderGUI = CommandGUI()
#MOL2ReaderGUI.addMenuCommand('menuRoot', 'File', 'Read MOL2',index=0)

class PDBWriter(MVCommand):
    """
    Command to write the given molecule or the given subset of atoms
    of one molecule as PDB file.
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : PDBWriter 
    \nCommand : writePDB
    \nSynopsis:\n
        None <- writePDB( nodes, filename=None, sort=True,
                          pdbRec=['ATOM', 'HETATM', 'MODRES', 'CONECT'],
                          bondOrigin=('File', 'UserDefined'), ssOrigin=None, **kw)
    \nRequired Arguments:\n    
        nodes --- TreeNodeSet holding the current selection
    \nOptional Arguments:\n
        filename --- name of the PDB file (default=None). If None is given
                  The name of the molecule plus the .pdb extension will be used\n
        sort --- Boolean flag to either sort or not the nodes before writing
                  the PDB file (default=True)\n
        pdbRec --- List of the PDB Record to save in the PDB file.
                  (default: ['ATOM', 'HETATM', 'MODRES', 'CONECT']\n
        bondOrigin --- string or list specifying the origin of the bonds to save
                    as CONECT records in the PDB file. Can be 'all' or a tuple\n

        ssOrigin --- Flag to specify the origin of the secondary structure
                    information to be saved in the HELIX, SHEET and TURN
                    record. Can either be None, File, PROSS or Stride.\n
    """


#    def logString(self, *args, **kw):
#        """return None as log string as we don't want to log this
#"""
#        pass



    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

        
    def doit(self, nodes, filename=None, sort=True, transformed=False,
             pdbRec=['ATOM', 'HETATM', 'MODRES', 'CONECT'],
             bondOrigin=('File', 'UserDefined'), ssOrigin=None):
        
        if bondOrigin == 0:
            bondOrigin = ('File', 'UserDefined')
        elif bondOrigin == 1:
            bondOrigin = 'all'
            
        nodes = self.vf.expandNodes(nodes)
        molecules = nodes.top.uniq()
        if len(molecules)==0: return 'ERROR'
        if len(molecules)>1:
            self.warningMsg("ERROR: Cannot create the PDB file, the current selection contains more than one molecule")
            return 'ERROR'

        mol = molecules[0]
        if filename is None:
            filename = './%s.pdb'%mol.name

        if transformed:
            oldConf = mol.allAtoms[0].conformation                
            self.setNewCoords(mol)

        writer = PdbWriter()
        writer.write(filename, nodes, sort=sort, records=pdbRec,
                     bondOrigin=bondOrigin, ssOrigin=ssOrigin)

        if transformed:
            mol.allAtoms.setConformation(oldConf)


    def setNewCoords(self, mol):
        """ set the current conformation to be 1"""
        allAtoms = mol.allAtoms
        # get a handle on the master geometry
        mg = mol.geomContainer.masterGeom

        # get the transformation matrix of the root
        matrix = mg.GetMatrix(mg) # followed the code in DejaVu/ViewerGUI.py
                                  #def saveTransformation(self, filename, geom)
                                  
        # Transpose the transformation matrix.
        trMatrix = Numeric.transpose(matrix)
        # Get the coords of the atoms of your molecule.
        allAtoms.setConformation(0)
        coords = allAtoms.coords
        # Transform them into homogeneous coords.
        hCoords = Numeric.concatenate((coords,Numeric.ones( (len(coords), 1), 'd')), 1)
        # tranform the coords
        #tCoords = Numeric.matrixmultiply(hCoords, matrix)
        #tCoords = Numeric.matrixmultiply(hCoords, trMatrix)
        tCoords = numpy.dot(hCoords, trMatrix)
        # number of conformations available
        confNum = len(allAtoms[0]._coords)
        if hasattr(mol, 'transformedCoordsIndex'):
            # uses the same conformation to store the transformed data
            allAtoms.updateCoords(tCoords[:,:3].tolist(), \
                                  mol.transformedCoordsIndex)
        else:
            # add new conformation to be written to file
            allAtoms.addConformation(tCoords[:,:3].tolist())
            mol.transformedCoordsIndex = confNum
        allAtoms.setConformation( mol.transformedCoordsIndex )



    def __call__(self, nodes, filename=None, sort=True, transformed=False,
                 pdbRec=['ATOM', 'HETATM', 'MODRES', 'CONECT'],
                 bondOrigin=('File','UserDefined'), ssOrigin=None, **kw):
        """None <- writePDB( nodes, filename=None, sort=True,
                          pdbRec=['ATOM', 'HETATM', 'MODRES', 'CONECT'],
                          bondOrigin=('File', 'UserDefined')', ssOrigin=None, **kw)
        \nRequired Argument:\n
        nodes --- TreeNodeSet holding the current selection
        \nOptional Arguments:\n
        filename --- name of the PDB file (default=None). If None is given
                  The name of the molecule plus the .pdb extension will be used\n
        sort --- Boolean flag to either sort or not the nodes before writing
                  the PDB file (default=True)\n
        pdbRec --- List of the PDB Record to save in the PDB file.
                  (default: ['ATOM', 'HETATM', 'MODRES', 'CONECT']\n
        bondOrigin --- string or list specifying the origin of the bonds to save
                    as CONECT records in the PDB file. Can be 'all' or a tuple\n

        ssOrigin --- Flag to specify the origin of the secondary structure
                    information to be saved in the HELIX, SHEET and TURN
                    record. Can either be None, File, PROSS or Stride.\n
        """
        kw['sort'] = sort        
        kw['bondOrigin'] = bondOrigin
        kw['pdbRec'] = pdbRec
        kw['ssOrigin'] = ssOrigin
        kw['filename'] = filename
        kw['transformed'] = transformed        
        return apply(self.doitWrapper, (nodes,), kw)


    def dismiss_cb(self):
        if not self.cmdForms.has_key('PDBHelp'): return
        f = self.cmdForms['PDBHelp']
        if f.root.winfo_ismapped():
            f.root.withdraw()
            f.releaseFocus()
            

    def showPDBHelp(self):
        f = self.cmdForms['saveOptions']
        f.releaseFocus()
        nf = self.showForm("PDBHelp", modal=0, blocking=0)
        

    def add_cb(self):
        from mglutil.util.misc import uniq
        ebn = self.cmdForms['saveOptions'].descr.entryByName
        lb1 = ebn['avRec']['widget']
        lb2 = ebn['pdbRec']['widget']
        newlist = uniq(list(lb2.get()) + list(lb1.getcurselection()))
        lb2.setlist(newlist)
        if 'CONECT' in newlist:
            self.idf.entryByName['bondOrigin']['widget'].grid(sticky='w')
        

    def remove_cb(self):
        ebn = self.cmdForms['saveOptions'].descr.entryByName
        lb2 = ebn['pdbRec']['widget']
        sel = lb2.getcurselection()
        all = lb2.get()
        if sel:
            remaining = filter(lambda x: not x in sel, all)
            lb2.setlist(remaining)
            if 'CONECT' in sel:
                self.idf.entryByName['bondOrigin']['widget'].grid_forget()
                


    def setEntry_cb(self, filename ):
        ebn = self.cmdForms['saveOptions'].descr.entryByName
        entry = ebn['filename']['widget']
        entry.setentry(filename)
    

    def buildFormDescr(self, formName):
        from mglutil.util.misc import uniq
        if formName=='saveOptions':
            idf = InputFormDescr(title='Write Options')
            self.idf =idf            
            idf.append({'name':'fileGroup',
                        'widgetType':Pmw.Group,
                        'container':{'fileGroup':"w.interior()"},
                        'wcfg':{},
                        'gridcfg':{'sticky':'wnse', 'columnspan':4}})

            idf.append({'name':'filename',
                        'widgetType':Pmw.EntryField,
                        'parent':'fileGroup',
                        'tooltip':'Enter a filename',
                        'wcfg':{'label_text':'Filename:',
                                'labelpos':'w', 'value':self.defaultFilename},
                        'gridcfg':{'sticky':'we'},
                        })
            
            idf.append({'widgetType':SaveButton,
                        'name':'filebrowse',
                        'parent':'fileGroup',
                        'wcfg':{'buttonType':Tkinter.Button,
                                'title':self.title,
                                'types':self.fileType,
                                'callback':self.setEntry_cb,
                                'widgetwcfg':{'text':'BROWSE'}},
                        'gridcfg':{'row':-1, 'sticky':'we'}})

            # Find the available records and the avalaibe options
            # bond origin and secondary structure origin)
            # default records
            defRec = ['ATOM', 'HETATM', 'MODRES', 'CONECT']
            if isinstance(self.mol.parser, PdbParser):
                defRec = ['ATOM', 'HETATM', 'MODRES', 'CONECT', 'SHEET', 'TURN', 'HELIX']
                avRec = uniq(self.mol.parser.keys)
                #sargis added the following line to make sure that only 
                #PdbParser.PDBtags are displayed
                avRec = filter(lambda x: x in avRec, PdbParser.PDBtags)
                defRec = filter(lambda x: x in avRec, defRec)

            else:
                avRec = ['ATOM', 'HETATM', 'MODRES', 'CONECT']

            # Source of the secondary structure information
            ssRec = filter(lambda x: x in avRec, ['HELIX', 'SHEET', 'TURN'])
            if self.mol.hasSS != []:
                avRec = avRec + ['HELIX', 'SHEET', 'TURN']
                ssOrigin = [self.mol.hasSS[0].split('From ')[1],]
                if len(ssRec) !=0 and self.mol.hasSS != ['From File']:
                    ssOrigin.append('File')
            elif len(ssRec) != 0:
                ssOrigin=['File',]
            else:
                ssOrigin = None
            # Source of the CONECT information
            atms = self.nodes.findType(Atom)
            bonds = atms.bonds[0]
            bondOrigin = uniq(bonds.origin)
            if len(bondOrigin)>0 and not 'CONECT' in avRec: avRec.append('CONECT')

            # HYBND is also a record that can be created from
            # the molecular data structure.
            hydbnd = atms.get(lambda x: hasattr(x, 'hbonds'))
            if hydbnd is not None and len(hydbnd) and not "HYDBND" in avRec:
                avRec.append("HYDBND")

            avRec.sort()
            # Available records to write out
            idf.append({'name':'recGroup',
                        'widgetType':Pmw.Group,
                        'container':{'recGroup':"w.interior()"},
                        'wcfg':{'tag_text':"PDB Records:"},
                        'gridcfg':{'sticky':'wnse', 'columnspan':2}})
                        
            idf.append({'name':'avRec',
                        'widgetType':Pmw.ScrolledListBox,
                        'parent':'recGroup',
                        'tooltip':'The available PDB records are the records present in the original PDB \n\
file when relevant and the PDB records that can be created from the MolKit data structure \n\
(such as ATOM, HETATM, CONECT, TER, HELIX, SHEET, TURN, HYDBND). The TER record will be automatically \n\
created with the ATOM records.',
                        'wcfg':{'label_text':'Available PDB Records: ',
                                'labelpos':'nw',
                                'items':avRec,
                                'listbox_selectmode':'extended',
                                'listbox_exportselection':0,
                                'listbox_height':5,'listbox_width':10,
                                },
                        'gridcfg':{'sticky': 'wesn','row':1, 'column':0,'rowspan':2}})

            idf.append({'name':'pdbinfo',
                        'parent':'recGroup',
                        'widgetType':Tkinter.Button,
                        'tooltip':'Show PDB record description',
                        'wcfg':{'text':'Records \nInfo',
                                'command':self.showPDBHelp},
                        'gridcfg':{'sticky':'we', 'row':1, 'column':1}})

            idf.append({'name':'add',
                        'parent':'recGroup',
                        'widgetType':Tkinter.Button,
                        'tooltip':""" Add the selected PDB record to the list
of saved in the file""",
                        'wcfg':{'text':'Add','command':self.add_cb},
                        'gridcfg':{'sticky':'we','row':2, 'column':1}})


            idf.append({'name':'pdbRec',
                        'parent':'recGroup',
                        'widgetType':Pmw.ScrolledListBox,
                        'wcfg':{'label_text':'PDB Records to be saved: ',
                                'labelpos':'nw',
                                'items':defRec,
                                'listbox_selectmode':'extended',
                                'listbox_exportselection':0,
                                'listbox_height':5,'listbox_width':10,
                                },
                        'gridcfg':{'sticky': 'wesn', 'row':1, 'column':2, 'rowspan':2}})


            idf.append({'name':'remove',
                        'parent':'recGroup',
                        'widgetType':Tkinter.Button,
                        'tooltip':""" Remove the selected records from the list of records to be saved in the file.""",
                        'wcfg':{'text':'REMOVE','width':10,
                               'command':self.remove_cb},
                        'gridcfg':{'sticky':'we', 'row':1, 'column':3}})

            
            # OTHER OPTIONS
            idf.append({'name':'optionGroup',
                        'widgetType':Pmw.Group,
                        'container':{'optionGroup':"w.interior()"},
                        'wcfg':{'tag_text':"Other write options:"},
                        'gridcfg':{'sticky':'wnse', 'columnspan':3}})

            # sort the nodes
            idf.append({'name':'sort',
                        'parent':'optionGroup',
                        'widgetType':Tkinter.Checkbutton,
                        'tooltip':'Choose whether or not to sort the nodes before writing in the PDB files',
                        'wcfg':{'text':'Sort Nodes', 'variable':Tkinter.IntVar()},
                        'gridcfg':{'sticky':'w'}})
            
            # save transformed coords
            idf.append({'name':'transformed',
                        'parent':'optionGroup',
                        'widgetType':Tkinter.Checkbutton,
                        'tooltip':'Choose to save original coordinates or the transformed coordinates in Viewer.',
                        'wcfg':{'text':'Save Transformed Coords', 'variable':Tkinter.IntVar()},
                        'gridcfg':{'sticky':'w'}})


            if 'CONECT' in avRec:  # bond origin
                idf.append({'name':'bondOrigin',
                            'parent':'optionGroup',
                            'widgetType':Tkinter.Checkbutton,
                            'tooltip':'When this button is not checked, only bonds created from original CONECT records and\nbonds added by the user (i.e. addBond command) will generate CONECT records in the output file.',
                            'wcfg':{'text':'Write All Bonds as CONECT Records ', 'variable':Tkinter.IntVar()},
                            'gridcfg':{'sticky':'w'}})
            
            # secondary structure origin
            if not ssOrigin is None and len(ssOrigin)>1:
                idf.append({'name':'ssOrigin',
                            'widgetType':Pmw.RadioSelect,
                            'listtext':ssOrigin,'defaultValue':ssOrigin[0],
                            'parent':'optionGroup',
                            'tooltip':"",
                            'wcfg':{'label_text': 'Secondary structure information source:',
                                    'labelpos':'w','buttontype':'radiobutton', 'selectmode':'single',
                                    },
                            'gridcfg':{'sticky':'w'}})
            return idf


        elif formName == 'PDBHelp':
            idf = InputFormDescr(title='PDB FORMAT HELP')
            idf.append({'name':'pdbHelp',
                        'widgetType':Pmw.ScrolledText,
                        'defaultValue':pdbDescr,
                        'wcfg':{ 'labelpos':'nw',
                                 'label_text':'PDB Format description:',
                                 'text_width':50,
                                 'text_height':20},
                        'gridcfg':{'sticky':'we'}})
            idf.append({'name':'dismiss',
                        'widgetType':Tkinter.Button,
                        'wcfg':{'text':'DISMISS',
                                'command':self.dismiss_cb},
                        'gridcfg':{'sticky':'we'}})

            return idf
            

    def guiCallback(self):
        # Get the current selection
        nodes = self.vf.getSelection()
        if not len(nodes): return None
        molecules, nodes = self.vf.getNodesByMolecule(nodes)
        # Make sure that the current selection only belong to 1 molecule
        if len(molecules)>1:
            self.warningMsg("ERROR: Cannot create the PDB file.\n\
The current selection contains more than one molecule.")
            return
        self.mol = molecules[0]
        self.nodes = nodes[0]
        self.title = "Write PDB file"
        self.fileType = [('PDB file', '*.pdb')]
        currentPath = os.getcwd()
        self.defaultFilename = os.path.join(currentPath,self.mol.name) + '.pdb'
        val = self.showForm('saveOptions', force=1,
                            cancelCfg={'text':'Cancel',
                                       'command':self.dismiss_cb},
                            okCfg={'text':'OK',
                                   'command':self.dismiss_cb})
        if val:
            fileName = val['filename']
            if os.path.exists(fileName):
                if not askyesno("Overwrite", "File " +fileName+ " exists. Overwrite?"):
                    return
            if val.has_key('filebrowse'):
                del val['filebrowse']
            del val['avRec']
            ebn = self.cmdForms['saveOptions'].descr.entryByName
            w = ebn['pdbRec']['widget']
            val['pdbRec'] = w.get()
            if len(val['pdbRec'])==0: return
            apply(self.doitWrapper, (self.nodes,), val)


pdbWriterDescr = {'widgetType':'Menu', 'menyBarName':'menuRoot',
                  'menuButtonName':'File',
                  'menyEntryLabel':'Write PDB ...',
                  'index':0}

from Pmv.fileCommandsGUI import PDBWriterGUI

class PQRWriter(PDBWriter):
    """Command to write PQR files using a PQR spec compliant writer
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : PQRWriter
    \nCommand : writePQR
    \nSynopsis:\n
    None <- writePQR(filename, nodes, sort=True, **kw)
    \nRequired Arguments:\n      
           filename --- name of the PQR file
           nodes --- TreeNodeSet holding the current selection\n
    \nOptional Arguments:\n        
           sort --- default is 1    
    """
    from MolKit.pqrWriter import PqrWriter


#    def logString(self, *args, **kw):
#        """return None as log string as we don't want to log this
#"""
#        pass


    def doit(self, filename, nodes, sort):
        nodes = self.vf.expandNodes(nodes)
        if len(nodes)==0: return 'ERROR'

        mol = nodes.top.uniq()
        assert len(mol)==1

        if sort:
            #print 'nodes are sorted'
            nodes.sort()
        writer = self.PqrWriter()
        writer.write(filename, nodes)


    def __call__(self, filename, nodes, sort=True, recType='all', **kw):
        """None <--- writePQR(filename, nodes, sort=True, **kw)
           \nfilename --- name of the PQR file
           \nnodes --- TreeNodeSet holding the current selection
           \nsort --- default is 1
           """
        kw['sort'] = sort        
        apply(self.doitWrapper, (filename, nodes,), kw)

        

    def guiCallback(self):
        file = self.vf.askFileSave(types=[('prq files', '*.pqr')],
                                   title="write PQR file:")
        if file == None: return
        nodes = self.vf.getSelection()
        if not len(nodes): return None
        if len(nodes.top.uniq())>1:
            self.warningMsg("more than one molecule in selection")
            return
        elif len(nodes)!=len(nodes.top.uniq().findType(nodes[0].__class__)):
            msg = 'writing only selected portion of '+ nodes[0].top.name
            self.warningMsg(msg)
        ans = Tkinter.IntVar()
        ans.set(1)

        ifd = InputFormDescr(title='Write Options')
        ifd.append({'name':'sortLab',
                    'widgetType': Tkinter.Label,
                    'wcfg':{'text':'Sort Nodes:'},
                    'gridcfg': {'sticky':Tkinter.W}})
        ifd.append({'name': 'yesWid',
                   'widgetType':Tkinter.Radiobutton,
                   'value': '1',
                   'variable': ans,
                   'text': 'Yes',
                   'gridcfg': {'sticky':Tkinter.W}}) 
        ifd.append({'name': 'noWid',
                   'widgetType':Tkinter.Radiobutton,
                   'value': '0',
                   'text': 'No',
                   'variable': ans,
                   'gridcfg': {'sticky':Tkinter.W, 'row':-1,'column':1}}) 

        val = self.vf.getUserInput(ifd)
        if val:
            sort = ans.get()
            if sort == 1: 
                nodes.sort()

            self.doitWrapper(file, nodes, sort)


pqrWriterDescr = {'widgetType':'Menu', 'menyBarName':'menuRoot',
                  'menuButtonName':'File',
                  'menyEntryLabel':'Write PQR ...',
                  'index':0}
from Pmv.fileCommandsGUI import PQRWriterGUI

class PDBQWriter(PDBWriter):
    """Command to write PDBQ files using a PDBQ spec compliant writer
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : PDBQWriter
    \nCommand : writePDBQ
    \nSynopsis:\n
        None <- writePDBQ( nodes, filename=None, sort=True,
                          pdbRec=['ATOM', 'HETATM', 'CONECT'],
                          bondOrigin=('File', 'UserDefined'), ssOrigin=None, **kw)
     \nRequired Argument:\n
        nodes --- TreeNodeSet holding the current selection
        
     \nOptional arguments:\n
        filename --- name of the PDB file (default=None). If None is given
                  The name of the molecule plus the .pdb extension will be used
        sort --- Boolean flag to either sort or not the nodes before writing
                  the PDB file (default=True)\n
        pdbRec --- List of the PDB Record to save in the PDB file.
                  (default: ['ATOM', 'HETATM', 'CONECT']\n
        bondOrigin --- string or list specifying the origin of the bonds to save
                    as CONECT records in the PDB file. Can be 'all' or a tuple\n

        ssOrigin --- Flag to specify the origin of the secondary structure
                    information to be saved in the HELIX, SHEET and TURN
                    record. Can either be None, File, PROSS or Stride.\n
    """


#    def logString(self, *args, **kw):
#        """return None as log string as we don't want to log this
#"""
#        pass


    def doit(self, nodes, filename=None, sort=True, pdbRec = ['ATOM', 'HETATM', 'CONECT'],
             bondOrigin=('File', 'UserDefined'), ssOrigin=None, transformed=False):
        if bondOrigin == 0:
            bondOrigin = ('File', 'UserDefined')
        elif bondOrigin == 1:
            bondOrigin = 'all'        
        nodes = self.vf.expandNodes(nodes)
        molecules = nodes.top.uniq()
        if len(molecules)==0: return 'ERROR'
        # Cannot save multiple molecules in one PDB file. They need to be merged into one molecule
        # first
        if len(molecules)>1:
            self.warningMsg("ERROR: Cannot create the PDBQ file, the current selection contains more than one molecule")
            return 'ERROR'
        mol = molecules[0]
        # Cannot save a PDBQ file if all the atoms donnot have a charge assigned.
        allAtoms = nodes.findType(Atom)
        try:
            allAtoms.charge
        except:
            try:
                allAtoms.charge=allAtoms.gast_charge
            except:
                self.warningMsg('ERROR: Cannot create the PDBQ file, all atoms in the current selection do not have a charge field. Use the commands in the editCommands module to either assign Kollman charges or compute Gasteiger charges')
                return 'ERROR'
        
        if filename is None:
            filename = './%s.pdbq'%mol.name

        if transformed:
            oldConf = mol.allAtoms[0].conformation
            self.setNewCoords(mol)

        writer = PdbqWriter()
        writer.write(filename, nodes, sort=sort, records=pdbRec,
                     bondOrigin=bondOrigin, ssOrigin=ssOrigin)

        if transformed:
            mol.allAtoms.setConformation(oldConf)
            

    def __call__(self, nodes, filename=None, sort=True, pdbRec = ['ATOM', 'HETATM', 'CONECT'],
                 bondOrigin=('File', 'UserDefined'), ssOrigin=None, transformed=False, **kw):
        """None <- writePDBQ( nodes, filename=None, sort=True,
                          pdbRec=['ATOM', 'HETATM', 'CONECT'],
                          bondOrigin=('File', 'UserDefined'), ssOrigin=None, **kw)
        \nRequired Argument:\n
        nodes: TreeNodeSet holding the current selection
        
        \nOptional Arguments:\n
        filename --- name of the PDB file (default=None). If None is given
                  The name of the molecule plus the .pdb extension will be used\n
        sort --- Boolean flag to either sort or not the nodes before writing
                  the PDB file (default=True)\n
        pdbRec --- List of the PDB Record to save in the PDB file.
                  (default: ['ATOM', 'HETATM', 'CONECT']\n
        bondOrigin --- string or list specifying the origin of the bonds to save
                    as CONECT records in the PDB file. Can be 'all' or a tuple\n

        ssOrigin --- Flag to specify the origin of the secondary structure
                    information to be saved in the HELIX, SHEET and TURN
                    record. Can either be None, File, PROSS or Stride.\n
        """

        kw['sort'] = sort        
        kw['bondOrigin'] = bondOrigin
        kw['ssOrigin'] = ssOrigin
        kw['filename'] = filename
        kw['transformed'] = transformed
        apply(self.doitWrapper, (nodes,), kw)


    def guiCallback(self):
        # Get the current selection
        nodes = self.vf.getSelection()
        if not len(nodes): return None
        molecules, nodes = self.vf.getNodesByMolecule(nodes)
        # Make sure that the current selection only belong to 1 molecule
        if len(molecules)>1:
            self.warningMsg("ERROR: Cannot create the PDBQ file.\n\
The current selection contains more than one molecule.")
            return
        self.mol = molecules[0]
        self.nodes = nodes[0]
        self.title = "Write PDBQ file"
        self.fileType = [('PDBQ file', '*.pdbq')]
        currentPath = os.getcwd()
        self.defaultFilename = os.path.join(currentPath,self.mol.name) + '.pdbq'
        val = self.showForm('saveOptions', force=1,cancelCfg={'text':'Cancel', 'command':self.dismiss_cb},
                            okCfg={'text':'OK', 'command':self.dismiss_cb})
        if val:
            del val['avRec']
            if val.has_key('filebrowse'): del val['filebrowse']
            ebn = self.cmdForms['saveOptions'].descr.entryByName
            w = ebn['pdbRec']['widget']
            val['pdbRec'] = w.get()
            if len(val['pdbRec'])==0: return
            apply(self.doitWrapper, (self.nodes,), val)



pdbqWriterGuiDescr = {'widgetType':'Menu', 'menyBarName':'menuRoot',
                      'menuButtonName':'File',
                      'menyEntryLabel':'Write PDBQ ...',
                      'index':0}

from Pmv.fileCommandsGUI import PDBQWriterGUI

class PDBQSWriter(PDBWriter):
    """Command to write PDBQS files using a PDBQS spec compliant writer
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : PDBQSWriter
    \nCommand : writePDBQS
    \nSynopsis:\n
        None <- writePDBQS( nodes, filename=None, sort=True,
                          pdbRec=['ATOM', 'HETATM', 'CONECT'],
                          bondOrigin=('File', 'UserDefined'), ssOrigin=None, **kw)
    \nRequired Argument:\n
        nodes --- TreeNodeSet holding the current selection
    \nOptional Arguments:\n
        filename --- name of the PDB file (default=None). If None is given
                  The name of the molecule plus the .pdb extension will be used\n
        sort --- Boolean flag to either sort or not the nodes before writing
                  the PDB file (default=True)\n
        pdbRec --- List of the PDB Record to save in the PDB file.
                  (default: ['ATOM', 'HETATM', 'CONECT']\n
        bondOrigin --- string or list specifying the origin of the bonds to save
                    as CONECT records in the PDB file. Can be 'all' or a tuple\n

        ssOrigin --- Flag to specify the origin of the secondary structure
                    information to be saved in the HELIX, SHEET and TURN
                    record. Can either be None, File, PROSS or Stride.\n
    """


#    def logString(self, *args, **kw):
#        """return None as log string as we don't want to log this
#"""
#        pass


    def doit(self, nodes, filename=None, sort=True, pdbRec = ['ATOM', 'HETATM', 'CONECT'],
             bondOrigin=('File', 'UserDefined'), ssOrigin=None, transformed=False):
        if bondOrigin == 0:
            bondOrigin = ('File', 'UserDefined')
        elif bondOrigin == 1:
            bondOrigin = 'all'        
        nodes = self.vf.expandNodes(nodes)
        molecules = nodes.top.uniq()
        if len(molecules)==0: return 'ERROR'
        # Cannot save multiple molecules in one PDB file. They need to be merged into one molecule
        # first
        if len(molecules)>1:
            self.warningMsg("ERROR: Cannot create the PDBQS file, the current selection contains more than one molecule")
            return 'ERROR'
        mol = molecules[0]
        # Cannot save a PDBQ file if all the atoms donnot have a charge assigned.
        allAtoms = nodes.findType(Atom)
        try:
            allAtoms.charge
        except:
            try:
                allAtoms.charge=allAtoms.gast_charge
            except:
                self.warningMsg('ERROR: Cannot create the PDBQS file, all atoms in the current selection do not have a charge field. Use the commands in the editCommands module to either assign Kollman charges or compute Gasteiger charges')
                return 'ERROR'
        
        try:
            allAtoms.AtSolPar
            allAtoms.AtVol
        except:
            self.warningMsg('ERROR: Cannot create the PDBQS file, all atoms do not have a solvation fields')
            return 'ERROR'

        if filename is None:
            filename = './%s.pdbqs'%mol.name
        if transformed:
            oldConf = mol.allAtoms[0].conformation
            self.setNewCoords(mol)

        writer = PdbqsWriter()
        writer.write(filename, nodes, sort=sort, records=pdbRec,
                     bondOrigin=bondOrigin, ssOrigin=ssOrigin)

        if transformed:
            mol.allAtoms.setConformation(oldConf)


    def __call__(self, nodes, filename=None, sort=True, pdbRec = ['ATOM', 'HETATM', 'CONECT'],
                 bondOrigin=('File', 'UserDefined'), ssOrigin=None, transformed=False, **kw):
        """None <- writePDBQS( nodes, filename=None, sort=True,
                          pdbRec=['ATOM', 'HETATM', 'CONECT'],
                          bondOrigin=('File', 'UserDefined'), ssOrigin=None, **kw)
        \nRequired Argument:\n
        nodes --- TreeNodeSet holding the current selection
        
        \nOptional Arguments:\n
        filename --- name of the PDB file (default=None). If None is given
                  The name of the molecule plus the .pdb extension will be used\n
        sort --- Boolean flag to either sort or not the nodes before writing
                  the PDB file (default=True)\n
        pdbRec --- List of the PDB Record to save in the PDB file.
                  (default: ['ATOM', 'HETATM', 'CONECT']\n
        bondOrigin --- string or list specifying the origin of the bonds to save
                    as CONECT records in the PDB file. Can be 'all' or a tuple\n

        ssOrigin --- Flag to specify the origin of the secondary structure
                    information to be saved in the HELIX, SHEET and TURN
                    record. Can either be None, File, PROSS or From Stride.
        """
 
        kw['sort'] = sort        
        kw['bondOrigin'] = bondOrigin
        kw['ssOrigin'] = ssOrigin
        kw['filename'] = filename
        kw['transformed'] = transformed
        apply(self.doitWrapper, (nodes,), kw)


    def guiCallback(self):
        # Get the current selection
        nodes = self.vf.getSelection()
        if not len(nodes): return None
        molecules, nodes = self.vf.getNodesByMolecule(nodes)
        # Make sure that the current selection only belong to 1 molecule
        if len(molecules)>1:
            self.warningMsg("ERROR: Cannot create the PDBQS file.\n\
The current selection contains more than one molecule.")
            return
        self.mol = molecules[0]
        self.nodes = nodes[0]
        self.title = "Write PDBQS file"
        self.fileType = [('PDBQS file', '*.pdbqs')]
        currentPath = os.getcwd()
        self.defaultFilename = self.defaultFilename = os.path.join(currentPath,self.mol.name) + '.pdbqs'
        val = self.showForm('saveOptions', force=1,cancelCfg={'text':'Cancel', 'command':self.dismiss_cb},
                            okCfg={'text':'OK', 'command':self.dismiss_cb})
        if val:
            del val['avRec']
            if val.has_key('filebrowse'): del val['filebrowse']
            ebn = self.cmdForms['saveOptions'].descr.entryByName
            w = ebn['pdbRec']['widget']
            val['pdbRec'] = w.get()
            if len(val['pdbRec'])==0: return
            apply(self.doitWrapper, (self.nodes,), val)


pdbqsWriterGuiDescr = {'widgetType':'Menu', 'menyBarName':'menuRoot',
                       'menuButtonName':'File',
                       'menyEntryLabel':'Write PDBS ...',
                       'index':0}

from Pmv.fileCommandsGUI import PDBQSWriterGUI

class PDBQTWriter(PDBWriter):
    """Command to write PDBQT files using a PDBQT spec compliant writer
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : PDBQTWriter
    \nCommand : write PDBQT
    \nSynopsis:\n
        None <--- writePDBQT( nodes, filename=None, sort=True,
                          pdbRec=['ATOM', 'HETATM', 'CONECT'],
                          bondOrigin=('File', 'UserDefined'), ssOrigin=None, **kw)\n
    \nRequired argument:\n
        nodes --- TreeNodeSet holding the current selection
        
    \nOptional arguments:\n
        filename --- name of the PDB file (default=None). If None is given
                  The name of the molecule plus the .pdb extension will be used\n
        sort --- Boolean flag to either sort or not the nodes before writing
                  the PDB file (default=True)\n
        pdbRec --- List of the PDB Record to save in the PDB file.
                  (default: ['ATOM', 'HETATM', 'CONECT']\n
        bondOrigin --- string or list specifying the origin of the bonds to save
                    as CONECT records in the PDB file. Can be 'all' or a tuple\n

        ssOrigin --- Flag to specify the origin of the secondary structure
                    information to be saved in the HELIX, SHEET and TURN
                    record. Can either be None, File, PROSS or Stride.
    
    """


#    def logString(self, *args, **kw):
#        """return None as log string as we don't want to log this
#"""
#        pass


    def doit(self, nodes, filename=None, sort=True, pdbRec = ['ATOM', 'HETATM', 'CONECT'],
             bondOrigin=('File', 'UserDefined'), ssOrigin=None, transformed=False):
        if bondOrigin == 0:
            bondOrigin = ('File', 'UserDefined')
        elif bondOrigin == 1:
            bondOrigin = 'all'        
        nodes = self.vf.expandNodes(nodes)
        molecules = nodes.top.uniq()
        if len(molecules)==0: return 'ERROR'
        # Cannot save multiple molecules in one PDB file. They need to be merged into one molecule
        # first
        if len(molecules)>1:
            self.warningMsg("ERROR: Cannot create the PDBQT file, the current selection contains more than one molecule")
            return 'ERROR'
        mol = molecules[0]
        # Cannot save a PDBQ file if all the atoms donnot have a charge assigned.
        allAtoms = nodes.findType(Atom)
        try:
            allAtoms.charge
        except:
            try:
                allAtoms.charge=allAtoms.gast_charge
            except:
                self.warningMsg('ERROR: Cannot create the PDBQT file, all atoms in the current selection do not have a charge field. Use the commands in the editCommands module to either assign Kollman charges or compute Gasteiger charges')
                return 'ERROR'
        
        try:
            allAtoms.autodock_element
        except:
            self.warningMsg('ERROR: Cannot create the PDBQT file, all atoms do not have an autodock_element field')
            return 'ERROR'

        if filename is None:
            filename = './%s.pdbqt'%mol.name
        if transformed:
            oldConf = mol.allAtoms[0].conformation
            self.setNewCoords(mol)

        writer = PdbqtWriter()
        writer.write(filename, nodes, sort=sort, records=pdbRec,
                     bondOrigin=bondOrigin, ssOrigin=ssOrigin)

        if transformed:
            mol.allAtoms.setConformation(oldConf)


    def __call__(self, nodes, filename=None, sort=True, pdbRec = ['ATOM', 'HETATM', 'CONECT'],
                 bondOrigin=('File', 'UserDefined'), ssOrigin=None, transformed=False, **kw):
        """None <- writePDBQT( nodes, filename=None, sort=True,
                          pdbRec=['ATOM', 'HETATM', 'CONECT'],
                          bondOrigin=('File', 'UserDefined'), ssOrigin=None, **kw)\n
        \nRequired Argument:\n
        nodes --- TreeNodeSet holding the current selection
        
        \nOptional Arguments:\n
        filename --- name of the PDB file (default=None). If None is given
                  The name of the molecule plus the .pdb extension will be used\n
        sort --- Boolean flag to either sort or not the nodes before writing
                  the PDB file (default=True)\n
        pdbRec --- List of the PDB Record to save in the PDB file.
                  (default: ['ATOM', 'HETATM', 'CONECT']\n
        bondOrigin --- string or list specifying the origin of the bonds to save
                    as CONECT records in the PDB file. Can be 'all' or a tuple\n

        ssOrigin --- Flag to specify the origin of the secondary structure
                    information to be saved in the HELIX, SHEET and TURN
                    record. Can either be None, File, PROSS or Stride.
        """
 
        kw['sort'] = sort        
        kw['bondOrigin'] = bondOrigin
        kw['ssOrigin'] = ssOrigin
        kw['filename'] = filename
        kw['transformed'] = transformed
        apply(self.doitWrapper, (nodes,), kw)


    def guiCallback(self):
        # Get the current selection
        nodes = self.vf.getSelection()
        if not len(nodes): return None
        molecules, nodes = self.vf.getNodesByMolecule(nodes)
        # Make sure that the current selection only belong to 1 molecule
        if len(molecules)>1:
            self.warningMsg("ERROR: Cannot create the PDBQT file.\n\
The current selection contains more than one molecule.")
            return
        self.mol = molecules[0]
        self.nodes = nodes[0]
        self.title = "Write PDBQT file"
        self.fileType = [('PDBQT file', '*.pdbqt')]
        currentPath = os.getcwd()
        self.defaultFilename = self.defaultFilename = os.path.join(currentPath,self.mol.name) + '.pdbqt'
        val = self.showForm('saveOptions', force=1,cancelCfg={'text':'Cancel', 'command':self.dismiss_cb},
                            okCfg={'text':'OK', 'command':self.dismiss_cb})
        if val:
            del val['avRec']
            if val.has_key('filebrowse'): del val['filebrowse']
            ebn = self.cmdForms['saveOptions'].descr.entryByName
            w = ebn['pdbRec']['widget']
            val['pdbRec'] = w.get()
            if len(val['pdbRec'])==0: return
            apply(self.doitWrapper, (self.nodes,), val)


pdbqtWriterGuiDescr = {'widgetType':'Menu', 'menyBarName':'menuRoot',
                       'menuButtonName':'File',
                       'menyEntryLabel':'Write PDBQT ...',
                       'index':0}

from Pmv.fileCommandsGUI import PDBQTWriterGUI


class SaveMMCIF(MVCommand):
    """This command writes macromolecular Crystallographic Information File (mmCIF).
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : SaveMMCIF
    \nCommand : saveMMCIF
    \nSynopsis:\n
        None<---saveMMCIF(filename, nodes)
    \nRequired Arguments:\n
        filename --- name of the mmcif file (default=None). If None is given
                  The name of the molecule plus the .cif extension will be used\n   
        nodes ---  TreeNodeSet holding the current selection
    """
    
#    def logString(self, *args, **kw):
#        """return None as log string as we don't want to log this
#"""
#        pass


    def doit(self, filename, nodes):
        nodes = self.vf.expandNodes(nodes)
        writer = MMCIFWriter()
        writer.write(filename, nodes)


    def __call__(self, filename, nodes,**kw):
        """None<---saveMMCIF(filename,nodes)
        \nfilename --- name of the mmcif file (default=None). If None is given
                  The name of the molecule plus the .cif extension will be used\n   
        \nnodes ---  TreeNodeSet holding the current selection
        """
        nodes = self.vf.expandNodes(nodes)
        apply(self.doitWrapper, (filename, nodes), kw)

    def guiCallback(self):
        filename = self.vf.askFileSave(types=[('MMCIF files', '*.cif')],
                                   title="Write MMCIF File:")
        if not filename: return
            
        nodes = self.vf.getSelection()
        if not len(nodes) : return None

        if len(nodes.top.uniq())>1:
            self.warningMsg("more than one molecule in selection")
            return

        self.doitWrapper(filename, nodes)
        
from Pmv.fileCommandsGUI import SaveMMCIFGUI

class STLWriter(MVCommand):
    """Command to write coords&normals of currently displayed geometries as
    ASCII STL files (STL = stereolithography, don't confuse with standard
    template library)
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : STLWriter
    \nCommand : writeSTL
    \nSynopsis:\n
        None<---Write STL ( filename, sphereQuality=2,
cylinderQuality=10 )
    """
       
#    def logString(self, *args, **kw):
#        """return None as log string as we don't want to log this
#"""
#        pass


    def doit(self, filename, sphereQuality=0,
             cylinderQuality=0):
        """Write all displayed geoms of all displayed molecules in
        the STL format"""
        from DejaVu.DataOutput import OutputSTL
        STL = OutputSTL()
        stl = STL.getSTL(self.vf.GUI.VIEWER.rootObject, filename,
                         sphereQuality=sphereQuality,
                         cylinderQuality=cylinderQuality)
        
        if stl is not None and len(stl) != 0:
            f = open(filename, 'w')
            map( lambda x,f=f: f.write(x), stl)
            f.close()


    def __call__(self, filename, **kw):
	"""None <--- Write STL ( filename, sphereQuality=0,
cylinderQuality=0 )"""
        apply( self.doitWrapper, (filename,), kw )


    def guiCallback(self):
        newfile = self.vf.askFileSave(types=[('STL files', '*.stl'),],
                                 title='Select STL files:')
        
        if not newfile or newfile == '':
            return
        
        from DejaVu.DataOutput import STLGUI
        opPanel = STLGUI(master=None, title='STL Options')
        opPanel.displayPanel(create=1)
        
        if not opPanel.readyToRun:
            return

        # get values from options panel
        di = opPanel.getValues()
        sq = di['sphereQuality']
        cq = di['cylinderQuality']

        self.doitWrapper(newfile, sq, cq)
            

stlWriterGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                     'menuButtonName':'File',
                     'menuEntryLabel':'Write STL',
                     }
from Pmv.fileCommandsGUI import STLWriterGUI

class VRML2Writer(MVCommand):
    """Command to save currently displayed geometries in VRML 2.0 format
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : VRML2Writer
    \nCommand : writeVRML2.0file
    \nSynopsis:\n
    None<---Write VRML 2.0 file (filename, saveNormals=0,
colorPerVertex=True, useProto=0, sphereQuality=2, cylinderQuality=10 )
    """


#    def logString(self, *args, **kw):
#        """return None as log string as we don't want to log this
#"""
#        pass


    def onAddCmdToViewer(self):
        if self.vf.hasGui:
            from DejaVu.DataOutput import VRML2GUI
            self.opPanel = VRML2GUI(master=None, title='VRML2 Options')

        
    def __init__(self):
        MVCommand.__init__(self)

        
    def doit(self, filename, saveNormals=0,
             colorPerVertex=True, useProto=0,
             sphereQuality=2, cylinderQuality=10):

        from DejaVu.DataOutput import OutputVRML2
        
        V = OutputVRML2()

        # add hook to progress bar
        if self.vf.hasGui:
            V.updateProgressBar = self.vf.GUI.updateProgressBar
            V.configureProgressBar = self.vf.GUI.configureProgressBar
        

        vrml2 = V.getVRML2(self.vf.GUI.VIEWER.rootObject, complete=1,
                           normals=saveNormals,
                           colorPerVertex=colorPerVertex, usePROTO=useProto,
                           sphereQuality=sphereQuality,
                           cylinderQuality=cylinderQuality)

        if vrml2 is not None and len(vrml2) != 0:
            f = open(filename, 'w')
            map( lambda x,f=f: f.write(x), vrml2)
            f.close()
            del vrml2


    def __call__(self, filename, saveNormals=0,
                 colorPerVertex=True, useProto=0,
                 sphereQuality=2, cylinderQuality=10, **kw):
	"""Write VRML 2.0 file (filename, saveNormals=0,
colorPerVertex=True, useProto=0, sphereQuality=2, cylinderQuality=10 )"""
        kw['saveNormals'] = saveNormals
        kw['colorPerVertex'] = colorPerVertex
        kw['useProto'] = useProto
        kw['sphereQuality'] = sphereQuality
        kw['cylinderQuality'] = cylinderQuality
        apply( self.doitWrapper, (filename,), kw)


    def guiCallback(self):
        newfile = self.vf.askFileSave(types=[('VRML 2.0 files', '*.wrl'),],
                                 title='Select VRML 2.0 files:')

        if newfile is None or newfile == '':
            return


#        if not self.opPanel.readyToRun:
#            self.opPanel.displayPanel(create=1)
#        else:
#            self.opPanel.displayPanel(create=0)

        # get values from options panel
        di = self.opPanel.getValues()
        sn = di['saveNormals']
        co = di['colorPerVertex']
        if co == 1:
            co = True
        else:
            co = False
        up = di['usePROTO']
        sq = di['sphereQuality']
        cq = di['cylinderQuality']
        kw = {'saveNormals':di['saveNormals'],
              'colorPerVertex':di['colorPerVertex'],
              'useProto':di['usePROTO'], 'sphereQuality':di['sphereQuality'],
              'cylinderQuality':di['cylinderQuality'], 'redraw':0}
        apply(self.doitWrapper, (newfile,), kw)
        #self.doitWrapper(newfile, sn, ni, co, up, sq, cq)


vrml2WriterGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                     'menuButtonName':'File',
                     'menuEntryLabel':'Write VRML 2.0',
                     }

from Pmv.fileCommandsGUI import VRML2WriterGUI


import urllib                   

class fetch(MVCommand):
    """This command read a molecule from the web.
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : readFromWebCommand
    \nCommand : readFromWeb
    \nSynopsis:\n
        mols <- readFromWeb(pdbID=None, URL="Default")
    \nguiCallback: 
Opens InputForm with 3 EntryFields
        PDB ID: 4-character code (e.g. 1crn).
        Keyword: searched using RCSB.ORG search engine
        URL: should point to an existing molecule (e.g http://mgltools.scripps.edu/documentation/tutorial/molecular-electrostatics/HIS.pdb)
If Keyword contains a text it is searched first. When URL field is not empty this URL is used instead of PDB ID to retrieve molecule.

Mouse over PDB Cache Directory label to see the path, or click Clear button to remove all files from there.
    """        
    baseURI = "http://www.rcsb.org/pdb/download/downloadFile.do?fileFormat=pdb&compression=NO&structureId="
    searchURI = "http://www.rcsb.org/pdb/search/navbarsearch.do?inputQuickSearch="
    resultURI = 'http://www.rcsb.org/pdb/results/results.do'
    from mglutil.util.packageFilePath import getResourceFolderWithVersion
    rcFolder = getResourceFolderWithVersion()
    width = 440    #width of the GUI
    height = 200   #height of the GUI
    forceIt = False #do we force the fect even if in the pdbcache dir


    def  onAddCmdToViewer(self):
        
        self.vf.userpref.add( 'PDB Cache Storage (MB)', 100, 
                           validateFunc = self.validateUserPref,
                           callbackFunc = [self.userPref_cb],
                           doc="""Maximum space allowed for File -> Read -> fetch From Web.""")        
        
    def message_box(self):
        txt =  "The file you requested does not exist\n"
        txt+=  "Do you want to search again?"
        if askyesno(title = 'Invalid Input',message=txt):
            self.guiCallback()

    def find_list(self,keyword):
        """This function is to find out number of pages  molecules are
        listed and get all molecule and information. """
        if  keyword:
            keyword = keyword.replace(' ','%20')
            uri = self.searchURI+keyword
            try:
                fURL = urllib.urlopen(uri)
            except Exception, inst:
                print inst
                return        
#            if 'content-type' not in fURL.headers.keys():
#                self.message_box()
#                return
#            if fURL.headers['content-type'] == 'text/html;charset=ISO-8859-1' or fURL.headers['content-type'] =="text/html; charset=iso-8859-1":
            m=[]
            self.listmols=[]
            self.information=[] 
            newurl = fURL.geturl()
            #shows first hundred files
            cur_url = newurl.split(";")[-1]
            st = "startAt=0&resultsperpage=100"
            cURL = self.resultURI+";"+cur_url+"?"+st
            fURL = urllib.urlopen(cURL)
            fp = open("dataf" ,"w")
            fp.write(fURL.read())
            fp.close()
            fp = open("dataf")
            lines =fp.readlines()
            fp.close()
            os.remove("dataf")
            ## file names              
            for i in lines:
                if '<input type="checkbox" name=' in i:
                        m.append(i)
            for j in m:
                h = eval(str(j.split(" ")[-1][:-2]).split("=")[-1])
                self.listmols.append(h)        
            
            if len(self.listmols)==0:
               return
            ##information
            z=[]
            c=[]
            for i in lines:
                 if 'href="/pdb/explore.do?structureId=' in i:
                        z.append(i)
            for i in z:
                 c.append(i.split(">"))
            for i in c:
                 if len(i[-1])>6:
                     self.information.append(i[-1][:-2])


    def __call__(self, pdbID=None, URL="Default", **kw):
         if kw.has_key('f'):
            self.forceIt = kw['f']
         else :
            self.forceIt = False
         return apply(self.doitWrapper, (pdbID,URL))


    def doit(self, pdbID=None, URL="Default"):
        gz=False
        #forceIt = True
        ext = ".pdb"
        URI = URL
        if not hasattr(self,'db'):
            self.db=""
        if pdbID == None and URL !="Default":
                URI = URL
                txt  = URL.split("/")[-1]
                pdbID = txt[:-4]
                ext =  txt[-4:]
        elif pdbID != None:
            if len(pdbID) > 4 or self.db != "":
                if pdbID[4:] == '.trpdb' or self.db == "Protein Data Bank of Transmembrane Proteins (TMPDB)":
                    #most are xml format just look if the 1t5t.trpdb.gz exist
                    URI = 'http://pdbtm.enzim.hu/data/database/'+pdbID[1:3]+'/'+pdbID[:4]+'.trpdb.gz'
                    pdbID = pdbID[:4]
                    gz=True
                    #print URI,pdbID
                elif pdbID[4:] == '.pdb' or self.db == "Protein Data Bank (PDB)" :
                    pdbID = pdbID[:4]
                    URI = self.baseURI + pdbID
                elif pdbID[4:] == '.opm' or self.db == "Orientations of Proteins in Membranes (OPM)" :
                    pdbID = pdbID[:4]
                    URI = 'http://opm.phar.umich.edu/pdb/'+pdbID[:4]+'.pdb'
                elif pdbID[4:] == '.cif' or self.db == "Crystallographic Information Framework (CIF)":
                    pdbID = pdbID[:4]
                    URI = 'http://www.rcsb.org/pdb/files/'+pdbID[:4]+'.cif'
                    ext = ".cif"
                elif pdbID[4:] == '.pqs' or self.db == "PQS":
                    pdbID = pdbID[:4]
                    URI ='ftp://ftp.ebi.ac.uk/pub/databases/msd/pqs/macmol/'+pdbID[:4]+'.mmol'   
                    ext = '.mmol'
            else : #==4 ?    
                URI = self.baseURI + pdbID
        if pdbID:
            #pdbID
            if self.rcFolder is not None:
                dirnames = os.listdir(self.rcFolder)
            else:
                dirnames = []
            #checks in pdb cache before searching in rcsb.org.
            if "pdbcache" in dirnames:
                #forceit : even if in pdbcache use the web pdb file
                filenames = os.listdir(self.rcFolder+os.sep+'pdbcache')
                if pdbID+ext in filenames and not self.forceIt:
                    tmpFileName = self.rcFolder + os.sep +"pdbcache"+os.sep+pdbID+ext
                    mols = self.vf.readMolecule(tmpFileName, log=0)
                    if hasattr(self.vf, 'recentFiles'):
                        self.vf.recentFiles.add(os.path.abspath(tmpFileName), 'readMolecule')
                    return mols
            try:
                #print "ok try urllib open", URI
                #but first check it ...
                import WebServices
                test = WebServices.checkURL(URI)
                if test :
                    fURL = urllib.urlopen(URI)
                else :
                    print "didn't exist try another ID"
                    return None
            except Exception, inst:
                print inst
                return None
            #if URL != "Default" or fURL.headers['content-type'] =='application/download':
            if self.rcFolder is not None:
                    if "pdbcache" not in dirnames:
                        curdir = os.getcwd()
                        os.mkdir(self.rcFolder + os.sep +"pdbcache")
                    #check if gzipped file...
                    tmpFileName = self.rcFolder + os.sep +"pdbcache"+os.sep+pdbID+ext
                    if gz :
                        tmpFileName = self.rcFolder + os.sep +"pdbcache"+os.sep+pdbID+ext+'.gz'
                    tmpFile = open(tmpFileName,'w')
                    tmpFile.write(fURL.read())
                    tmpFile.close()
                    if gz :
                        print "ok gunzip"
                        out = self.rcFolder + os.sep +"pdbcache"+os.sep+pdbID+ext
                        gunzip(tmpFileName, out)
                        tmpFileName = out
                    mols = self.vf.readMolecule(tmpFileName, log=0)
                    if hasattr(self.vf, 'recentFiles'):
                        self.vf.recentFiles.add(os.path.abspath(tmpFileName), 'readMolecule')
                    return mols
            #else:
            #    self.message_box()
                           
            
    def hide(self, event=None):
        if self.root:
            self.root.withdraw()

    def chooseDB(self,value):
        self.db = value#self.fetchmenu.getcurselection()
    
    def buildFormDescr(self, formName):
      self.db=""
      self.fetchmenu = None
      if formName == "Fetch":  
        self.ifd = ifd = InputFormDescr(title="Fetch PDB")
        ifd.append({'name': 'fetch',
                        'label_text': 'Fetch',
                        'widgetType':Pmw.OptionMenu,
                        'variable': self.fetchmenu,
                        'wcfg':{'labelpos':'w','label_text':"choose:",
                                #'menubutton_width':10,
                                'items': ['Protein Data Bank (PDB)','Crystallographic Information Framework (CIF)','Orientations of Proteins in Membranes (OPM)','Protein Data Bank of Transmembrane Proteins (TMPDB)'],
                                'command': self.chooseDB},
                        'gridcfg': {'sticky':'w','columnspan':2}})


        ifd.append({'name':"pdbID",
                    'widgetType':Pmw.EntryField,
                    'tooltip':'PDB ID is 4-character code (e.g. 1crn)',
                    'wcfg':{'labelpos':'w','label_text':"  ID:",
                            'entry_width':1,
                            'validate':{'validator':'alphanumeric',
                                        'min':4, 'max':4, 'minstrict':False
                                        },
                            'command':self.onEnter,
                            },
                    'gridcfg':{'columnspan':2}
                    })
        
#        ifd.append({'name':"keyword",
#                    'widgetType':Pmw.EntryField,
#                    'tooltip':'Keyword are Searched Using RCSB.ORG Search Engine',
#                    'wcfg':{'labelpos':'w','label_text':"Keyword:",
#                            'entry_width':1,
#                            
#                            },
#                    'gridcfg':{'columnspan':2}
#                    })

        ifd.append({'name':"URL",
                    'widgetType':Pmw.EntryField,
                    'wcfg':{'labelpos':'w','label_text':"       URL:",
                            'entry_width':1,
                            
                            },
                    'gridcfg':{'columnspan':2}
                    })
        

            
        ifd.append({'name':'PDBCachedir',
                        'widgetType':Tkinter.Button,
                        'wcfg':{'text':'Clear Cache Directory',
                                'command':self.clearPDBCache},
                        'gridcfg':{'sticky':'we', 'row':4, 'column':0,  'columnspan':2}})
        return ifd  

    def initFunc(self, foo):
        if self.vf.hasGui:
            self.vf.GUI.ROOT.after(1, self.focus)

    def focus(self):
        self.ifd.entryByName['pdbID']['widget'].component('entry').focus_set()
        
    def onEnter(self):
        self.ifd.form.OK_cb()
        self.dismiss_cb()
        
    def guiCallback(self, **kw):
        if hasattr(self,"root"):
            if self.root!=None:
                self.root.withdraw()
        if not self.getPDBCachedir() \
          and self.rcFolder is not None:
            os.mkdir(self.rcFolder+os.sep+'pdbcache')
        val = self.showForm('Fetch', force=1, initFunc=self.initFunc,
                            cancelCfg={'text':'Cancel',
                                       'command':self.dismiss_cb},
                            okCfg={'text':'OK',
                                   'command':self.dismiss_cb})
         
        if val:
            self.vf.GUI.ROOT.config(cursor='watch')
#            if val[ "keyword"]:
#                from mglutil.gui.BasicWidgets.Tk.multiListbox import MultiListbox
#                self.root = Tkinter.Toplevel()
#                self.root.title("Select PDB file")
#                self.root.protocol("WM_DELETE_WINDOW", self.hide)
#                self.PanedWindow = Tkinter.PanedWindow(self.root, handlepad=0,
#                             handlesize=0,
#                             orient=Tkinter.VERTICAL,
#                             bd=1,height=2*self.height,width=self.width
#                             )
#                
#                self.PanedWindow.pack(fill=Tkinter.BOTH, expand=1)
#                self.mlb = MultiListbox(self.PanedWindow, ((' PDB ID', 9),  
#                                             ('Information   ', 20)),
#                                              
#                                             hull_height = 2*self.height,
#                                             usehullsize = 1,
#                                             hull_width = self.width)
#
#                self.mlb.pack(expand=Tkinter.NO, fill=Tkinter.X)             
#                self.find_list(val["keyword"])
#                if len(self.listmols)==0:
#                    self.hide()
#                    self.message_box()
#                    return
#                for m,info in zip(self.listmols,self.information):
#                    mol_name = m
#                    self.mlb.insert(Tkinter.END, (m,info))
#                self.PanedWindow.add(self.mlb)
#                self.ok_b =    Tkinter.Button(self.root, text="Load", 
#                                      command=self.ok,width=20)   
#                self.ok_b.pack(fill=Tkinter.X,side = "left")
#                self.close_b = Tkinter.Button(self.root, text="  Dismiss  ", 
#                                      command=self.hide,width=20)  
#                self.close_b.pack(fill=Tkinter.X,side = "left")

            if val['pdbID']:
             if len(val['pdbID']) != 4:
                txt = val['pdbID'] + 'is not a valid PDB ID\n'
                txt += "Please enter 4-character code"
                showinfo(message = txt)
                self.guiCallback()
                return
            
            if val['URL']:
                self.vf.GUI.ROOT.config(cursor= '')    
                self.doitWrapper(URL=val['URL'])
            else:
                self.vf.GUI.ROOT.config(cursor= '')    
                self.doitWrapper(val['pdbID'], **kw)

    
    def getPDBCachedir(self):
        from mglutil.util.packageFilePath import getResourceFolderWithVersion 
        rcFolder = getResourceFolderWithVersion()
        if rcFolder is not None \
          and os.path.exists(self.rcFolder+os.sep+'pdbcache'):
            dirname = self.rcFolder+os.sep+'pdbcache'
            return    dirname     
        else:
            return None

    def clearPDBCache(self):
        dirname =  self.getPDBCachedir()
        if dirname and os.path.exists(dirname):
                filenames = os.listdir(dirname)
                for f in filenames:
                    os.remove(dirname+os.sep+f)

    def dismiss_cb(self):
        if not self.cmdForms.has_key('FetchPDB'): return
        f = self.cmdForms['FetchPDB']
        if f.root.winfo_ismapped():
            f.root.withdraw()
            f.releaseFocus()
             

    def ok(self):
        selection = self.mlb.curselection() 
        self.doitWrapper(self.listmols[eval(selection[0])])

    def validateUserPref(self, value):
        try:
            val = int(value)
            if val >-1:
                return 1
            else:
                return 0
        except:
            return 0 

    def userPref_cb(self, name, old, new):
        if self.vf.hasGui:
            self.vf.GUI.ROOT.after_idle(self.checkCache)

    def checkCache(self, threshold = 1024*1024):
        size = self.getCacheSize()
        maxSize = self.vf.userpref['PDB Cache Storage (MB)']['value']
        if size > maxSize:
            folder = self.getPDBCachedir()
            if not folder: return
            folder_size = 0
            for (path, dirs, files) in os.walk(folder):
              for file in files:
                filename = os.path.join(path, file)
                fileSize = os.path.getsize(filename)
                if fileSize > threshold:
                    os.remove(filename)
                else:
                    folder_size += os.path.getsize(filename)
            if (folder_size/(1024*1024.0)) > maxSize:
                self.checkCache(threshold = threshold/2.)
                
    def getCacheSize(self):
        # pick a folder you have ...
        folder = self.getPDBCachedir()
        if not folder: return
        folder_size = 0
        for (path, dirs, files) in os.walk(folder):
          for file in files:
            filename = os.path.join(path, file)
            folder_size += os.path.getsize(filename)
        
        return (folder_size/(1024*1024.0))
                       
from Pmv.fileCommandsGUI import fetchGUI

class ReadPmvSession(MVCommand):
    """Reads Full Pmv Session
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : ReadPmvSession
    \nCommand : readPmvSession
    \nSynopsis:\n
        mols <- readPmvSession(path)
    """        
    def guiCallback(self,  **kw):        
        self.fileBrowserTitle ="Read Session:"
        files = self.vf.askFileOpen([
            ('Pmv Session files', '*.psf'),
            ('All Files', '*.*')],  title="Read Pmv Session:",
            multiple=True)
        if files is None:
            return None
        for file in files:        
            self.doitWrapper(file, **kw)

    def doit(self, file):
        self.vf.readFullSession(file)

ReadPmvSessionGUI = CommandGUI()
ReadPmvSessionGUI.addMenuCommand('menuRoot', 'File', 'Read Session', after = "Read Molecule")

class ReadSourceMolecule(MVCommand):
    """Reads Molecule or Python script
    \nPackage : Pmv
    \nModule  : fileCommands
    \nClass   : ReadSourceMolecule
    \nCommand : readSourceMolecule
    \nSynopsis:\n
        mols <- readSourceMolecule(path)
    """        


    def guiCallback(self, event, **kw):
        self.fileTypes =[(
            'All supported formats',
         '*.psf *.cif *.mol2 *.pdb *.pqr *.pdbq *.pdbqs *.pdbqt *.gro *.py', )]
        self.fileTypes += [
            ('Pmv Session files', '*.psf'),
            ('PDB files', '*.pdb'),
            ('MEAD files', '*.pqr'),('MOL2 files', '*.mol2'),
            ('AutoDock files (pdbq)', '*.pdbq'),
            ('AutoDock files (pdbqs)', '*.pdbqs'),
            ('AutoDock files (pdbqt)', '*.pdbqt'),
            ('Gromacs files (gro)', '*.gro'),
            ]

        self.parserToExt = {'PDB':'.pdb', 'PDBQ':'.pdbq',
                            'PDBQS':'.pdbqs', 'PDBQT':'.pdbqt',
                            'MOL2':'.mol2',
                            'PQR':'.pqr',
                            'GRO':'.gro',
                            }
        self.fileTypes += [('MMCIF files', '*.cif'),]
        self.parserToExt['CIF'] = '.cif'
            
        #self.fileTypes += [('All files', '*')]
        
        self.fileBrowserTitle ="Read Molecule:"

        files = self.vf.askFileOpen(types=self.fileTypes+[
            ('Python scripts', '*.py'),
            ('Resource file','*.rc'),
            ('All Files', '*.*')],  title="Read Molecule or Python Script:",
            multiple=True)
        if files is None:
            return None
        
        for file in files:        
            self.doitWrapper(file, **kw)

            
    def doit(self, file):
        ext = os.path.splitext(file)[1].lower()
        if ext in ['.py','.rc']:
            self.vf.source(file, log=0)
        elif ext == ".psf":
            # Load Pmv session file
            self.vf.readFullSession(file)
        else:
            self.vf.readMolecule(file, log=0)

from Pmv.fileCommandsGUI  import ReadSourceMoleculeGUI

commandList = [
    {'name':'writePDB', 'cmd':PDBWriter(), 'gui':PDBWriterGUI },
    {'name':'writePDBQ', 'cmd':PDBQWriter(), 'gui':PDBQWriterGUI },
    {'name':'writePDBQT', 'cmd':PDBQTWriter(), 'gui':PDBQTWriterGUI },
    {'name':'writePDBQS', 'cmd':PDBQSWriter(), 'gui':PDBQSWriterGUI },
    {'name':'writeMMCIF', 'cmd':SaveMMCIF(), 'gui':SaveMMCIFGUI },    
    {'name':'writePQR', 'cmd':PQRWriter(), 'gui':PQRWriterGUI },
    {'name':'readPDB', 'cmd':PDBReader(), 'gui':None },
    {'name':'readGRO', 'cmd':GROReader(), 'gui':None },
    {'name':'readMolecule', 'cmd':MoleculeReader(), 'gui':MoleculeReaderGUI},
    {'name':'readPmvSession', 'cmd':ReadPmvSession(), 'gui':ReadPmvSessionGUI},    
    {'name':'fetch', 'cmd': fetch(), 'gui': fetchGUI},    
    {'name':'readPDBQ', 'cmd':PDBQReader(), 'gui':None },
    {'name':'readPDBQS', 'cmd':PDBQSReader(), 'gui':None },
    {'name':'readPDBQT', 'cmd':PDBQTReader(), 'gui':None },
    {'name':'readPQR', 'cmd':PQRReader(), 'gui':None },
    {'name':'readF2D', 'cmd':F2DReader(), 'gui':None },
    {'name':'readMOL2', 'cmd': MOL2Reader(), 'gui': None },
    {'name':'readMMCIF', 'cmd':MMCIFReader(), 'gui':None},
    {'name':'writeVRML2', 'cmd':VRML2Writer(), 'gui': VRML2WriterGUI},
    {'name':'writeSTL', 'cmd':STLWriter(), 'gui': STLWriterGUI},
    {'name':'readSourceMolecule', 'cmd':ReadSourceMolecule(), 'gui': ReadSourceMoleculeGUI}    
    ]

def gunzip(gzpath, path):
	import gzip
	gzf = gzip.open(gzpath)
	f = open(path, 'wb')
	f.write(gzf.read())
	f.close()
	gzf.close()


def initModule(viewer):

    for dict in commandList:
        viewer.addCommand( dict['cmd'], dict['name'], dict['gui'])

