## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

############################################################################
#
# Authors: William Lindstrom, Ruth Huey , Alex Gillet
#
# Copyright: A. Olson TSRI 2004
#
#############################################################################

#
# $Id: AutoDockScorer.py,v 1.24.4.1 2012/04/16 20:26:17 rhuey Exp $
#

import math
import numpy.oldnumeric as Numeric

from PyAutoDock.scorer import WeightedMultiTerm, DistDepPairwiseScorer
from PyAutoDock.scorer import PairwiseScorer

from vanDerWaals import VanDerWaals, HydrogenBonding
from vanDerWaals import  NewHydrogenBonding, NewVanDerWaals
from desolvation import Desolvation
from desolvation import NewDesolvation, NewDesolvationLigOnly, NewDesolvationAtomMap
from electrostatics import Electrostatics



class AutoDockTermWeights305:
    def __init__(self):
        self.name = 'asdf'

    estat_weight = 0.1146 # Autogrid3 weight
    dsolv_weight = 0.1711 # Autogrid3 weight
    hbond_weight = 0.0656 # Autogrid3 weight
    vdw_weight = 0.1485 # Autogrid3 weight
# AutoDockTermWeights305


class AutoDockTermWeights4_1:
    def __init__(self):
      self.name = '9_28_2004'

    estat_weight = 0.1408 # .1146*1.229 
    dsolv_weight = 0.122 # 9/28/04 weight
    hbond_weight = 0.1267 #.0656*1.931
    vdw_weight   = 0.1488 #.1485*1.002
# AutoDockTermWeights4_1


class AutoDockTermWeights4_2:
    def __init__(self):
      self.name = '5_5_2005'

    vdw_weight   = 0.1570 # .1485*1.057
    hbond_weight = 0.1344 # .0656*2.048
    estat_weight = 0.1319 # .1146*1.151 
    dsolv_weight = 0.1350 # 5/5/05 weight
# AutoDockTermWeights4_2


class AutoDockTermWeights4:
    def __init__(self):
      self.name = '8_2005'

    vdw_weight   = 0.1560 # .1485*1.05037
    hbond_weight = 0.0974 # .0656*1.48452
    estat_weight = 0.1465 # .1146*1.27907 
    dsolv_weight = 0.1159 # 8/05 weight
    tors_weight  = 0.2744 #
# AutoDockTermWeights4


class AutoDockTermWeights41:
    def __init__(self):
      self.name = '9_2007'

    vdw_weight   = 0.1662 #
    hbond_weight = 0.1209 #
    estat_weight = 0.1406 #
    dsolv_weight = 0.1322 #
    tors_weight  = 0.2983 #
# AutoDockTermWeights41


class AutoDockVinaTermWeights:
    def __init__(self):
      self.name = '8_2011'

    gauss1      =-0.035579 #
    gauss2      =-0.005156 #
    repulsion   = 0.840245 #
    hydrogen    =-0.587439 #
    hydrophobic =-0.035069 #
    rot         = 0.05846 #
# AutoDockVinaTermWeights


class Gauss(DistDepPairwiseScorer):
    xs_vdw_radii = {  
        'C': 1.9, # C_H 1.9,  C_P
        'A': 1.9, # C_H 1.9,  C_P
        'N': 1.8, # N_P, N_D, N_A, N_DA
       'NA': 1.8, # N_P, N_D, N_A, N_DA
       'OA': 1.7, # O_P, O_D,O_A, O_DA
       'SA': 2.0, # S_P
        'P': 2.1, #P_P
        'F': 1.5, #F_H
       'Cl': 1.8, #Cl_H
       'Br': 2.0, #Br_H
        'I': 2.2, #I_H
       'Fe': 1.2, # Metals...
       'Ca': 1.2} # Met_D } #from vina atom_constants.h

    def __init__(self, offset=0., width=0.5, cutoff=8.0, ms=None):
        DistDepPairwiseScorer.__init__(self)
        self.required_attr_dictA.setdefault('autodock_element', False)
        self.required_attr_dictB.setdefault('autodock_element', False)
        if ms is not None:
            self.set_molecular_system(ms)
        self.offset = offset
        self.width = width
        self.cutoff = cutoff


    def _f(self, at_a, at_b, dist, verbose=False):
        """ gauss pairwise dist dep function 
        @@USE rddist@@: dist - (xs_radius(a)+ xs_radius(b)) ??offset??
        """
        if dist>self.cutoff:
            return 0
        if at_a.element=='H' or at_b.element=='H':
            return 0
        try:
            rddist = dist - \
                    (self.xs_vdw_radii.get(at_a.autodock_element,2.0) + \
                     self.xs_vdw_radii.get(at_b.autodock_element,2.0) + \
                     self.offset)
            if verbose:
                print "rddist=", rddist, " a,b are:", at_a.full_name(), " ", at_b.full_name()
                print "autodock_elements = ", at_a.autodock_element," ",  at_b.autodock_element
                print "xs_vdw_radii = ", self.xs_vdw_radii.get(at_a.autodock_element, 2.0), " ", self.xs_vdw_radii.get(at_b.autodock_element, 2.0),
            #if verbose:
                print "self.offset=", self.offset,
                print "self.width=", self.width
            #energy = math.exp(-1*(((dist - (self.get_xs_radius_sum(at_a,at_b)+self.offset))/self.width)**2))
            energy = math.exp(-1*(rddist/self.width)**2)
            #print '%s-%s: rddist=%f, energy=%f'%(at_a.full_name(), at_b.full_name(), rddist, energy)
        except ZeroDivisionError:
            return 99999.9
        #@@NON-triangular adjustment:@@
        energy = energy/2.
        return energy


class Repulsion(DistDepPairwiseScorer):
    xs_vdw_radii = {  
        'C': 1.9, # C_H 1.9,  C_P
        'A': 1.9, # C_H 1.9,  C_P
        'N': 1.8, # N_P, N_D, N_A, N_DA
       'NA': 1.8, # N_P, N_D, N_A, N_DA
       'OA': 1.7, # O_P, O_D,O_A, O_DA
       'SA': 2.0, # S_P
        'P': 2.1, #P_P
        'F': 1.5, #F_H
       'Cl': 1.8, #Cl_H
       'Br': 2.0, #Br_H
        'I': 2.2, #I_H
       'Fe': 1.2, # Metals...
       'Ca': 1.2} # Met_D } #from vina atom_constants.h
#from everything.cpp:
#struct repulsion : public usable {
#	fl offset; // added to vdw
#	repulsion(fl offset_, fl cutoff_) : usable(cutoff_), offset(offset_) {
#		name = std::string("repulsion(o=") + to_string(offset) + ")";
#	}
#	fl eval(sz t1, sz t2, fl r) const {
#		fl d = r - (optimal_distance(t1, t2) + offset);
#		if(d > 0) 
#			return 0;
#		return d*d;
#	}
#};

    def __init__(self, offset=0., cutoff=8.0, ms=None):
        DistDepPairwiseScorer.__init__(self)
        self.required_attr_dictA.setdefault('autodock_element', False)
        self.required_attr_dictB.setdefault('autodock_element', False)
        if ms is not None:
            self.set_molecular_system(ms)
        self.offset = offset
        self.cutoff = cutoff


    def _f(self, at_a, at_b, dist, verbose=False):
        """ vina repulsion pairwise dist dep function 
        @@USE rddist@@: dist - (xs_radius(a)+ xs_radius(b)) ??offset??
        """
        if dist>self.cutoff:
            return 0
        if at_a.element=='H' or at_b.element=='H':
            return 0
        try:
            rddist = dist - \
                    (self.xs_vdw_radii.get(at_a.autodock_element,2.0) + \
                     self.xs_vdw_radii.get(at_b.autodock_element,2.0) + \
                     self.offset)
            if verbose:
                print "rddist=", rddist, " a,b are:", at_a.full_name(), " ", at_b.full_name()
                print "autodock_elements = ", at_a.autodock_element," ",  at_b.autodock_element
                print "xs_vdw_radii = ", self.xs_vdw_radii.get(at_a.autodock_element, 2.0), " ", self.xs_vdw_radii.get(at_b.autodock_element, 2.0),
                print "self.offset=", self.offset 
            energy = 0
            if rddist < 0: 
                energy = rddist*rddist
        except ZeroDivisionError:
            print "returning 99999.9"
            return 99999.9
        if verbose: print "returning ",energy 
        #@@NON-triangular adjustment:@@
        energy = energy/2.
        return energy

#------------------------------------------------------------------
# Hydrophobic
#------------------------------------------------------------------

#inline bool xs_is_hydrophobic(sz xs) {
#	return xs == XS_TYPE_C_H || 
#		   xs == XS_TYPE_F_H ||
#		   xs == XS_TYPE_Cl_H ||
#		   xs == XS_TYPE_Br_H || 
#		   xs == XS_TYPE_I_H;
#}
#void model::assign_types() {
#	VINA_FOR(i, grid_atoms.size() + atoms.size()) {
#		const atom_index ai = sz_to_atom_index(i);
#		atom& a = get_atom(ai);
#		a.assign_el();
#		sz& x = a.xs;
#		bool acceptor   = (a.ad == AD_TYPE_OA || a.ad == AD_TYPE_NA); // X-Score forumaltion apparently ignores SA
#		bool donor_NorO = (a.el == EL_TYPE_Met || bonded_to_HD(a));

#		switch(a.el) {
#			case EL_TYPE_H    : break;
#			case EL_TYPE_C    : x = bonded_to_heteroatom(a) ? XS_TYPE_C_P : XS_TYPE_C_H; break;
#			case EL_TYPE_N    : x = (acceptor && donor_NorO) ? XS_TYPE_N_DA : (acceptor ? XS_TYPE_N_A : (donor_NorO ? XS_TYPE_N_D : XS_TYPE_N_P)); break;
#			case EL_TYPE_O    : x = (acceptor && donor_NorO) ? XS_TYPE_O_DA : (acceptor ? XS_TYPE_O_A : (donor_NorO ? XS_TYPE_O_D : XS_TYPE_O_P)); break;
#			case EL_TYPE_S    : x = XS_TYPE_S_P; break;
#			case EL_TYPE_P    : x = XS_TYPE_P_P; break;
#			case EL_TYPE_F    : x = XS_TYPE_F_H; break;
#			case EL_TYPE_Cl   : x = XS_TYPE_Cl_H; break;
#			case EL_TYPE_Br   : x = XS_TYPE_Br_H; break;
#			case EL_TYPE_I    : x = XS_TYPE_I_H; break;
#			case EL_TYPE_Met  : x = XS_TYPE_Met_D; break;
#			case EL_TYPE_SIZE : break;
#			default: VINA_CHECK(false);
#		}
#	}
#}

#------------------------------------------------------------------
#// hydrophobic: check using index 'i' compared with 'carbon',
#//8/2011: hydrophobic from vina: everything.cpp l 134-145
#//struct hydrophobic : public usable {
#//fl good;
#//fl bad;
#//hydrophobic(fl good_, fl bad_, fl cutoff_) : usable(cutoff_), good(good_), bad(bad_) {
#//    name = "hydrophobic(g=" + to_string(good) + ", b=" + to_string(bad) + ", c=" + to_string(cutoff) + ")";
#//}
#//fl eval(sz t1, sz t2, fl r) const {
#//    if(xs_is_hydrophobic(t1) && xs_is_hydrophobic(t2))
#//        return slope_step(bad, good, r - optimal_distance(t1, t2));
#//    else return 0;
#//}
#//};

#//	add(1, new hydrophobic(0.5, 1.5, cutoff)); // good, bad, cutoff // WEIGHT:  -0.035069
#// carbon/aromatic_carbon       to non-hbonder
#//@@TODO: add support for these other hydrophobic interactions:
#//if (((i==carbon)||(i==arom_carbon)||(i==fluorine)||(i==chlorine)||(i==bromine)||(i==iodine))
#//&& ((ia==carbon)||(ia==arom_carbon)||(ia==fluorine)||(ia==chlorine)||(ia==bromine)||(ia==iodine))) 
#//wt_hydrophobic=-0.035069
#if (((i==carbon)||(i==arom_carbon)) && ((ia==carbon)||(ia==arom_carbon)))
# {
#    delta_e = 0.;
#    if (rddist<0.5) {
#       delta_e = 1*wt_hydrophobic;
#    } else if (rddist<1.5){
#       delta_e = (0.5-rddist)*wt_hydrophobic;
#    }
#    p_et->e_vdW_Hb[i][indx_r][ia] += delta_e;


class Hydrophobic(DistDepPairwiseScorer):
    xs_vdw_radii = {  
        'C': 1.9, # C_H 1.9,  C_P
        'A': 1.9, # C_H 1.9,  C_P
        'N': 1.8, # N_P, N_D, N_A, N_DA
       'NA': 1.8, # N_P, N_D, N_A, N_DA
       'OA': 1.7, # O_P, O_D,O_A, O_DA
       'SA': 2.0, # S_P
        'P': 2.1, #P_P
        'F': 1.5, #F_H
       'Cl': 1.8, #Cl_H
       'Br': 2.0, #Br_H
        'I': 2.2, #I_H
       'Fe': 1.2, # Metals...
       'Ca': 1.2} # Met_D } #from vina atom_constants.h

#//struct hydrophobic : public usable {
#//fl good;
#//fl bad;
#//hydrophobic(fl good_, fl bad_, fl cutoff_) : usable(cutoff_), good(good_), bad(bad_) {
#//    name = "hydrophobic(g=" + to_string(good) + ", b=" + to_string(bad) + ", c=" + to_string(cutoff) + ")";
#//}
#//fl eval(sz t1, sz t2, fl r) const {
#//    if(xs_is_hydrophobic(t1) && xs_is_hydrophobic(t2))
#//        return slope_step(bad, good, r - optimal_distance(t1, t2));
#//    else return 0;
#//}
#//};

    def slope_step(self, x_bad, x_good,  x, verbose=False):
        if x_bad < x_good:
            if verbose: print "bad is smaller"
            if x <= x_bad: 
                if verbose: print "x<= x_bad"
                return 0
            if x >= x_good: 
                if verbose: print "x>= x_good"
                return 1
        else:
            if verbose: print "bad is equal or larger"
            if x >= x_bad: 
                if verbose: print "2:x>= x_bad"
                return 0
            if x <= x_good: 
                if verbose: print "2:x<= x_good"
                return 1
        if verbose: print "returning fraction:"
        return (x - x_bad) / (x_good - x_bad)


    def __init__(self, good=0.5, bad=1.5, cutoff=8.0, ms=None, 
                  hydrophobic_types= ['C_H','Cu', 'Fe', 'Na', 'K', 'Hg', 'Co', 'U', 'Cd', 'Ni']):
        self.hp_types = set(hydrophobic_types).union(['C','A'])
        DistDepPairwiseScorer.__init__(self)
        self.required_attr_dictA.setdefault('autodock_element', False)
        self.required_attr_dictB.setdefault('autodock_element', False)
        if ms is not None:
            self.set_molecular_system(ms)
            self.set_vina_types(ms.get_entities(0)) #receptor
            self.set_vina_types(ms.get_entities(1)) #ligand
        self.good = good
        self.bad = bad
        self.cutoff = cutoff
        #TODO: distinguish C_P from C_H


    def set_vina_types(self, ats, verbose=False):
        for a in ats:
            a.is_hydrophobic = 0
            if verbose: print a.name, ' svt:'
            if a.element in self.hp_types:
                a.is_hydrophobic = 1
                if verbose: print "is_hydrophobic"
            elif a.element in ['C','A']:
                a.is_hydrophobic = 1
                for b in a.bonds:  #a-c
                    if verbose: print "bond ", b.atom1.name, b.atom1.is_hydrophobic, '-', b.atom2.name, b.atom2.is_hydrophobic
                    nAt = b.neighborAtom(a)
                    if verbose: print 'checking nAt ', nAt.name, ':', nAt.element
                    if nAt.element not in self.hp_types:
                        a.is_hydrophobic = 0
                        if verbose: print 'unset ', a.name, a.number, ' is_hydrophobic'


    def _f(self, at_a, at_b, dist, verbose=False):
        """ vina repulsion pairwise dist dep function 
        @@USE rddist@@: dist - (xs_radius(a)+ xs_radius(b)) 
#//    if(xs_is_hydrophobic(t1) && xs_is_hydrophobic(t2))
#//        return slope_step(bad, good, r - optimal_distance(t1, t2));
        """
        if dist>self.cutoff:
            return 0
        if at_a.element=='H' or at_b.element=='H':
            return 0
        if not hasattr(at_a,'is_hydrophobic'):
            self.set_vina_types(self.ms.get_entities(0)) #receptor
        if not at_a.is_hydrophobic:
            return 0
        if not hasattr(at_b,'is_hydrophobic'):
            self.set_vina_types(self.ms.get_entities(1)) #ligand
        if not at_b.is_hydrophobic:
            return 0
        try:
            rddist = dist - \
                    (self.xs_vdw_radii.get(at_a.autodock_element,2.0) + \
                     self.xs_vdw_radii.get(at_b.autodock_element,2.0))
            if verbose:
                print "rddist=", rddist, " a,b are:", at_a.full_name(), " ", at_b.full_name()
                print "autodock_elements = ", at_a.autodock_element," ",  at_b.autodock_element
                print "xs_vdw_radii = ", self.xs_vdw_radii.get(at_a.autodock_element, 2.0), " ", self.xs_vdw_radii.get(at_b.autodock_element, 2.0),
            energy = self.slope_step(self.bad, self.good, rddist)
        except ZeroDivisionError:
            print "returning 99999.9"
            return 99999.9
        #@@NON-triangular adjustment:@@
        energy = energy/2.
        if verbose: print "returning ",energy 
        return energy


#------------------------------------------------------------------
# Hydrogen
#------------------------------------------------------------------
#inline bool xs_is_acceptor(sz xs) {
#	return xs == XS_TYPE_N_A ||
#		   xs == XS_TYPE_N_DA ||
#		   xs == XS_TYPE_O_A ||
#		   xs == XS_TYPE_O_DA;
#}

#inline bool xs_is_donor(sz xs) {
#	return xs == XS_TYPE_N_D ||
#		   xs == XS_TYPE_N_DA ||
#		   xs == XS_TYPE_O_D ||
#		   xs == XS_TYPE_O_DA ||
#		   xs == XS_TYPE_Met_D;
#}

#inline bool xs_donor_acceptor(sz t1, sz t2) {
#	return xs_is_donor(t1) && xs_is_acceptor(t2);
#}

#inline bool xs_h_bond_possible(sz t1, sz t2) {
#	return xs_donor_acceptor(t1, t2) || xs_donor_acceptor(t2, t1);
#}
#------------------------------------------------------------------
#inline fl slope_step(fl x_bad, fl x_good, fl x) {
#	if(x_bad < x_good) {
#		if(x <= x_bad) return 0;
#		if(x >= x_good) return 1;
#	}
#	else {
#		if(x >= x_bad) return 0;
#		if(x <= x_good) return 1;
#	}
#	return (x - x_bad) / (x_good - x_bad);
#}
#------------------------------------------------------------------
#struct non_dir_h_bond : public usable {
#	fl good;
#	fl bad;
#	non_dir_h_bond(fl good_, fl bad_, fl cutoff_) : usable(cutoff_), good(good_), bad(bad_) {
#		name = std::string("non_dir_h_bond(g=") + to_string(good) + ", b=" + to_string(bad) + ")";
#	}
#	fl eval(sz t1, sz t2, fl r) const {
#		if(xs_h_bond_possible(t1, t2))
#			return slope_step(bad, good, r - optimal_distance(t1, t2));
#		return 0;
#	}
#};

class Non_dir_h_bond(DistDepPairwiseScorer):
    xs_vdw_radii = {  
        'C': 1.9, # C_H 1.9,  C_P
        'A': 1.9, # C_H 1.9,  C_P
        'N': 1.8, # N_P, N_D, N_A, N_DA
       'NA': 1.8, # N_P, N_D, N_A, N_DA
       'OA': 1.7, # O_P, O_D,O_A, O_DA
       'SA': 2.0, # S_P
        'P': 2.1, #P_P
        'F': 1.5, #F_H
       'Cl': 1.8, #Cl_H
       'Br': 2.0, #Br_H
        'I': 2.2, #I_H
       'Fe': 1.2, # Metals...
       'Ca': 1.2} # Met_D } #from vina atom_constants.h
#from everything.cpp:

    def slope_step(self, x_bad, x_good,  x, verbose=False):
        if x_bad < x_good:
            if verbose: print "bad is smaller"
            if x <= x_bad: 
                if verbose: print "x<= x_bad"
                return 0
            if x >= x_good: 
                if verbose: print "x>= x_good"
                return 1
        else:
            if verbose: print "bad is equal or larger"
            if x >= x_bad: 
                if verbose: print "2:x>= x_bad"
                return 0
            if x <= x_good: 
                if verbose: print "2:x<= x_good"
                return 1
        if verbose: print "returning fraction:"
        return (x - x_bad) / (x_good - x_bad)


    def __init__(self, good=-0.7, bad=0.0, cutoff=8.0, ms=None):
        #Non_dir_h_bond
        DistDepPairwiseScorer.__init__(self)
        self.required_attr_dictA.setdefault('autodock_element', False)
        self.required_attr_dictB.setdefault('autodock_element', False)
        #self.required_attr_dictB.setdefault('hb_type', False)
        if ms is not None:
            self.set_molecular_system(ms)
        self.good = good
        self.bad = bad
        self.cutoff = cutoff

#inline bool xs_is_acceptor(sz xs) {
#	return xs == XS_TYPE_N_A ||
#		   xs == XS_TYPE_N_DA ||
#		   xs == XS_TYPE_O_A ||
#		   xs == XS_TYPE_O_DA;
#}

#inline bool xs_is_donor(sz xs) {
#	return xs == XS_TYPE_N_D ||
#		   xs == XS_TYPE_N_DA ||
#		   xs == XS_TYPE_O_D ||
#		   xs == XS_TYPE_O_DA ||
#		   xs == XS_TYPE_Met_D;
#}

#inline bool xs_donor_acceptor(sz t1, sz t2) {
#	return xs_is_donor(t1) && xs_is_acceptor(t2);
#}

#inline bool xs_h_bond_possible(sz t1, sz t2) {
#	return xs_donor_acceptor(t1, t2) || xs_donor_acceptor(t2, t1);
#}

#	fl eval(sz t1, sz t2, fl r) const {
#		if(xs_h_bond_possible(t1, t2))
#			return slope_step(bad, good, r - optimal_distance(t1, t2));
#		return 0;
#	}
#};

#------------------------------------------------------------------
# from model.cpp line 402
#------------------------------------------------------------------
#		switch(a.el) {
#			case EL_TYPE_H    : break;
#			case EL_TYPE_C    : x = bonded_to_heteroatom(a) ? XS_TYPE_C_P : XS_TYPE_C_H; break;
#			case EL_TYPE_N    : x = (acceptor && donor_NorO) ? XS_TYPE_N_DA : (acceptor ? XS_TYPE_N_A : (donor_NorO ? XS_TYPE_N_D : XS_TYPE_N_P)); break;
#			case EL_TYPE_O    : x = (acceptor && donor_NorO) ? XS_TYPE_O_DA : (acceptor ? XS_TYPE_O_A : (donor_NorO ? XS_TYPE_O_D : XS_TYPE_O_P)); break;
#			case EL_TYPE_S    : x = XS_TYPE_S_P; break;
#			case EL_TYPE_P    : x = XS_TYPE_P_P; break;
#			case EL_TYPE_F    : x = XS_TYPE_F_H; break;
#			case EL_TYPE_Cl   : x = XS_TYPE_Cl_H; break;
#			case EL_TYPE_Br   : x = XS_TYPE_Br_H; break;
#			case EL_TYPE_I    : x = XS_TYPE_I_H; break;
#			case EL_TYPE_Met  : x = XS_TYPE_Met_D; break;
#			case EL_TYPE_SIZE : break;
#			default: VINA_CHECK(false);


    def h_bond_possible(self, a_ae, b_ae):
        metals = ['Cu', 'Zn', 'Co']
        hbonders = ['NA', 'OA']
        if (a_ae in metals and b_ae in metals):
            return 1
        if (a_ae in hbonders and b_ae in hbonders):
            return 1
        if (a_ae in hbonders and b_ae in metals):
            return 1
        if (a_ae in metals and b_ae in hbonders):
            return 1
        return 0


    def _f(self, at_a, at_b, dist, verbose=False):
        """ vina non_dir_hbond pairwise dist dep function 
        @@USE rddist@@: dist - (xs_radius(a)+ xs_radius(b)) ??offset??
        """
        if dist>self.cutoff:
            return 0
        if at_a.element=='H' or at_b.element=='H':
            return 0
        rddist = dist - \
                (self.xs_vdw_radii.get(at_a.autodock_element,2.0) + \
                 self.xs_vdw_radii.get(at_b.autodock_element,2.0))
        retval = 0.
        if self.h_bond_possible(at_a.autodock_element, at_b.autodock_element):
            if verbose: 
                print "hbond_possible! ", at_a.autodock_element,'-',at_b.autodock_element
            retval= self.slope_step(self.bad, self.good, rddist)
        #@@NON-triangular adjustment:@@??
        retval = retval/2.
        #if verbose: print "returning ", retval
        return retval
       


class Repulsion(DistDepPairwiseScorer):
    xs_vdw_radii = {  
        'C': 1.9, # C_H 1.9,  C_P
        'A': 1.9, # C_H 1.9,  C_P
        'N': 1.8, # N_P, N_D, N_A, N_DA
       'NA': 1.8, # N_P, N_D, N_A, N_DA
       'OA': 1.7, # O_P, O_D,O_A, O_DA
       'SA': 2.0, # S_P
        'P': 2.1, #P_P
        'F': 1.5, #F_H
       'Cl': 1.8, #Cl_H
       'Br': 2.0, #Br_H
        'I': 2.2, #I_H
       'Fe': 1.2, # Metals...
       'Ca': 1.2} # Met_D } #from vina atom_constants.h
#from everything.cpp:
#struct repulsion : public usable {
#	fl offset; // added to vdw
#	repulsion(fl offset_, fl cutoff_) : usable(cutoff_), offset(offset_) {
#		name = std::string("repulsion(o=") + to_string(offset) + ")";
#	}
#	fl eval(sz t1, sz t2, fl r) const {
#		fl d = r - (optimal_distance(t1, t2) + offset);
#		if(d > 0) 
#			return 0;
#		return d*d;
#	}
#};

    def __init__(self, offset=0., cutoff=8.0, ms=None):
        DistDepPairwiseScorer.__init__(self)
        self.required_attr_dictA.setdefault('autodock_element', False)
        self.required_attr_dictB.setdefault('autodock_element', False)
        if ms is not None:
            self.set_molecular_system(ms)
        self.offset = offset
        self.cutoff = cutoff


    def _f(self, at_a, at_b, dist, verbose=False):
        """ vina repulsion pairwise dist dep function 
        @@USE rddist@@: dist - (xs_radius(a)+ xs_radius(b)) ??offset??
        """
        if dist>self.cutoff:
            return 0
        if at_a.element=='H' or at_b.element=='H':
            return 0
        try:
            rddist = dist - \
                    (self.xs_vdw_radii.get(at_a.autodock_element,2.0) + \
                     self.xs_vdw_radii.get(at_b.autodock_element,2.0) + \
                     self.offset)
            if verbose:
                print "rddist=", rddist, " a,b are:", at_a.full_name(), " ", at_b.full_name()
                print "autodock_elements = ", at_a.autodock_element," ",  at_b.autodock_element
                print "xs_vdw_radii = ", self.xs_vdw_radii.get(at_a.autodock_element, 2.0), " ", self.xs_vdw_radii.get(at_b.autodock_element, 2.0),
                print "self.offset=", self.offset 
            if rddist > 0:
                energy = 0 #line 117 everything.cpp
            else:
                energy = rddist*rddist
        except ZeroDivisionError:
            print "ZeroDivisionError: returning 99999.9"
            energy = 99999.9
        if verbose: print "returning ",energy 
        #@@NON-triangular adjustment:@@??
        energy = energy/2.
        return energy

#------------------------------------------------------------------
# from autogrid/main.cpp:
# if ((rec_hbond>2&& (lig_hbond==1||lig_hbond==2))|| ((rec_hbond==1||rec_hbond==2)&&lig_hbond>2))
# { //check that types ia-i hbond
#       if (rddist<=0.7) { //what about EXACTLY 0.7?
#          delta_e = 1*wt_hydrogen;
#          p_et->e_vdW_Hb[i][indx_r][ia] += delta_e;
#          //energy_lookup[i][indx_r][ia] += delta_e;
#       }
#       if ((-0.7<rddist) && (rddist<=0.)){
#          delta_e =(rddist/0.7)*wt_hydrogen;
#          p_et->e_vdW_Hb[i][indx_r][ia] += delta_e;
#          //energy_lookup[i][indx_r][ia] -= delta_e;
#       }
#}
#------------------------------------------------------------------
# Num_tors_div
# main.cpp line 569:
#  self.add_term(Rotation(), weights.rot)  # 5*weight_rot/ 0.1 -1)
# everything.cpp line 379:
#  self.add_term(Num_tors_div(), weights.rot)  # 5*weight_rot/ 0.1 -1)
#------------------------------------------------------------------
# Python version doesn't have a separate scorer for this. Instead
#              it uses a post processing step 


class AutoDockVinaScorer(WeightedMultiTerm, AutoDockVinaTermWeights):
    """
 new class
"""
    def __init__(self, weights=AutoDockVinaTermWeights(), cutoff=8.0,
                       exclude_one_four=False, weed_bonds=False, verbose=False):
        self.prop = 'vina_energy'
        self.cutoff = cutoff
        WeightedMultiTerm.__init__(self)
        self.add_term(Gauss(0,0.5,cutoff), weights.gauss1)    
        self.add_term(Gauss(3.0,2.0,cutoff), weights.gauss2)    
        self.add_term(Repulsion(0., cutoff), weights.repulsion)    
        self.add_term(Non_dir_h_bond(-0.7, 0., cutoff), weights.hydrogen)    
        self.add_term(Hydrophobic(0.5, 1.5, cutoff), weights.hydrophobic)    
        self.num_tors_div_wt = weights.rot  #weight_rot=0.05846;((5*weight_rot/ 0.1) - 1)line618 main.cpp v.1.1.2
        self.verbose=verbose


    def post_process(self):
        # ligand (by convention)
        retVal = 0.0
        atoms_bx = self.ms.configuration[1]
        atoms_b = self.ms.get_entities(atoms_bx)
        try:
            at_b = atoms_b[0]
        except:
            at_b = atoms_b.next()
        atoms_ax = self.ms.configuration[0]
        atoms_a = self.ms.get_entities(atoms_ax)
        try:
            at_a = atoms_a[0]
        except:
            at_a = atoms_a.next()
        ndihe = 0
        if hasattr(at_b.top, 'ndihe'):
            ndihe = at_b.top.ndihe
        elif hasattr(at_a.top, 'ndihe'):
            ndihe = at_a.top.ndihe
        #from vina1.1.2/src/lib/everything.cpp line 253:
        #  return smooth_div(x, 1 + w * in.num_tors/5.0);
        retVal = 5.0/(1+self.num_tors_div_wt*ndihe) 
        self.array = Numeric.array(self.array)*retVal
        
# AutoDockVina Scorer

        
class AutoGrid305Scorer(WeightedMultiTerm, AutoDockTermWeights305):
    """
A handy scorer for AutoGrid305 atom maps.

Note that the Electrostatics term does not contribute to the atom
maps but is in a map of its own (the .e.map).
"""
    def __init__(self):
        WeightedMultiTerm.__init__(self)
        AutoDockTermWeights305.__init__(self)
        self.add_term(HydrogenBonding(), self.hbond_weight)
        self.add_term(VanDerWaals(), self.vdw_weight)
        self.add_term(Desolvation(), self.dsolv_weight)
# AutoGrid305Scorer



class AutoDock305Scorer(WeightedMultiTerm, AutoDockTermWeights305):
    def __init__(self):
      self.prop = 'ad305_energy'
      WeightedMultiTerm.__init__(self)
      AutoDockTermWeights305.__init__(self)
      self.add_term(Electrostatics(), self.estat_weight)
      self.add_term(HydrogenBonding(), self.hbond_weight)
      self.add_term(VanDerWaals(), self.vdw_weight)
      self.add_term(Desolvation(), self.dsolv_weight)
        

    def get_score_array(self):
      """ return a list of score for each terms per atoms"""
      # add up vdw, estat and hbond
      t = self.terms[0]
      # do you really want the list of arrays ? or a list of number for each
      # scoring object?
      array = t[0].get_score_array() * t[1]
      for term, weight in self.terms[1:]:
        array = array + weight*term.get_score_array()

      self.array = array
      return self.array
    

    def labels_atoms_w_nrg(self,score_array):
      """ will label each atoms with a nrg score """
      # label each first atom by sum of its ad3 interaction energies 
      firstAts = self.ms.get_entities(0)
      
      for i in range(len(firstAts)):
        a = firstAts[i]
        vdw_hb_estat_ds =Numeric.add.reduce(score_array[i])
        setattr(a, self.prop, vdw_hb_estat_ds)
        ## NOT sure we need the following anymore... ASK Ruth
##         vdw_hb_estat = Numeric.add.reduce(score_array[i])
##         if a.element=='O':
##           setattr(a, self.prop, .236+vdw_hb_estat)   #check this
##         elif a.element=='H':
##           setattr(a, self.prop, .118+vdw_hb_estat)   #check this
##         else:
##           setattr(a, self.prop, Numeric.add.reduce(self.dsolv_array[i])+vdw_hb_estat)

      # label each second atom by sum of its vdw interaction energies
      secondAts = self.ms.get_entities(1)
      swap_result = Numeric.swapaxes(score_array,0,1)
      for i in range(len(swap_result)):
          a = secondAts[i]
          vdw_hb_estat_ds =Numeric.add.reduce(swap_result[i])
          setattr(a, self.prop, vdw_hb_estat_ds)
                
##         vdw_hb_estat = Numeric.add.reduce(swap_result[i])
##         if a.element=='O':
##           setattr(a, self.prop, .236+vdw_hb_estat)   #check this
##         elif a.element=='H':
##           setattr(a, self.prop, .118+vdw_hb_estat)   #check this
##         else:
##           setattr(a, self.prop, Numeric.add.reduce(swap_dsolv[i])+vdw_hb_estat)

# AutoDock305Scorer


class AutoDock4Scorer(WeightedMultiTerm, AutoDockTermWeights4):
    def __init__(self):
        self.prop = 'ad4_energy'
        WeightedMultiTerm.__init__(self)
        AutoDockTermWeights4.__init__(self)
        self.add_term(Electrostatics(), self.estat_weight)    
        self.add_term(NewHydrogenBonding(), self.hbond_weight) 
        self.add_term(NewVanDerWaals(), self.vdw_weight)      #.1485*1.002
        self.add_term(NewDesolvation(), self.dsolv_weight) 


    def get_score_array(self):
        """ return a list of score for each terms per atoms"""
        # NEED TO CORRECT hbond
        # result = self.scorer.get_score_array()
        sal = score_array_list = []
        for t, w in self.terms:
            sal.append(t.get_score_array()*w)
        self.hbond_array = sal[1]
        result = Numeric.add(sal[0], sal[2])
        result = Numeric.add(result, sal[3])
        self.array = result
        return self.array


    def labels_atoms_w_nrg(self,score_array):
        """ will label each atoms with a nrg score """

        # label each first atom by sum of its vdw interaction energies 
        firstAts  = self.ms.get_entities(0)
        for i in range(len(firstAts)):
            # firstAts[i].vdw_energy = Numeric.add.reduce(score_array[i])
            hbond_val =  min(self.hbond_array[i])+max(self.hbond_array[i])
            setattr(firstAts[i], self.prop, Numeric.add.reduce(score_array[i])+hbond_val)
        # label each second atom by sum of its vdw interaction energies
        secondAts = self.ms.get_entities(1)
        swap_result = Numeric.swapaxes(score_array, 0,1)
        swap_hbond_array = Numeric.swapaxes(self.hbond_array, 0, 1)
        for i in range(len(swap_result)):
            #secondAts[i].vdw_energy = Numeric.add.reduce(swap_result[i])
            hbond_val =  min(swap_hbond_array[i])+max(swap_hbond_array[i])
            setattr(secondAts[i], self.prop, Numeric.add.reduce(swap_result[i])+hbond_val)      

# AutoDock4Scorer


class AutoDock4ScorerLigOnly(WeightedMultiTerm, AutoDockTermWeights4):
    def __init__(self):
        WeightedMultiTerm.__init__(self)
        self.add_term(Electrostatics(), self.estat_weight)    
        self.add_term(NewHydrogenBonding(), self.hbond_weight) 
        self.add_term(NewVanDerWaals(), self.vdw_weight)      #.1485*1.002
        self.add_term(NewDesolvationLigOnly(), self.dsolv_weight) 

# AutoDock4Scorer


class AutoDock4Scorer2(WeightedMultiTerm):
    #weights in the scorer for NewVanDerWaalsHybridWeights
    def __init__(self):
        WeightedMultiTerm.__init__(self)
        self.add_term(Electrostatics(), 0.1146)
        self.add_term(NewHydrogenBonding(), 0.1852)  #.0656*2.82292 = 0.1851836
        self.add_term(NewVanDerWaalsHybridWeights(), 1.0)   #varying weights in scorer
        self.add_term(NewDesolvation(), 1.0)         #.1711*0.10188 = 0.0174317
# AutoDock4Scorer2


class AutoDock41Scorer(WeightedMultiTerm, AutoDockTermWeights41):
    def __init__(self, exclude_torsFreeEnergy=False, verbose=False):
        self.verbose = verbose
        if verbose: print "initialized exclude_torsFreeEnergy=", exclude_torsFreeEnergy
        self.prop = 'ad41_energy'
        self.exclude_torsFreeEnergy=exclude_torsFreeEnergy
        WeightedMultiTerm.__init__(self)
        AutoDockTermWeights41.__init__(self)
        self.add_term(Electrostatics(), self.estat_weight)    
        self.add_term(NewHydrogenBonding(), self.hbond_weight) 
        self.add_term(NewVanDerWaals(), self.vdw_weight)   
        self.add_term(NewDesolvation(), self.dsolv_weight) 
        self.supported_types = self.get_supported_types()


    def get_supported_types(self):
        double_types = self.terms[2][0].epsij.keys()
        supported_types = []
        odd_length = []
        for t in double_types:
            if len(t)==4:
                supported_types.append(t[:2])
            elif len(t)==2:
                supported_types.append(t[0])
            elif len(t)==3:
                odd_length.append(t)
            else:
                raise "get_supported_types found badly formed autodock_element", t
        #check the 3-length autodock_elements [where did this come from??]
        for t in odd_length:
            t1 = t[:2]
            t2 = t[1:]
            ok = 0
            if t1 in supported_types and t[2] in supported_types:
                ok = 1
            if t2 in supported_types and t[0] in supported_types:
                ok = 1
            if not ok:
                raise "get_supported_types found badly formed autodock_element", t
        return supported_types


    def set_supported_types(self, type_list):
        self.supported_types = type_list


    def read_parameter_file(self, param_file):
        optr = open(param_file)
        lines = optr.readlines()
        #parse and set values
        Rij = {}
        epsij = {}
        vol = {}
        solpar = {}
        Rij_hb = {}
        epsij_hb = {}
        hbond = {}
        all_types = {}
        for l in lines:
            if l.find("FE_coeff_vdW")==0:
                self.vdw_weight = float(l.split()[1])
            if l.find("FE_coeff_hbond")==0:
                self.hbond_weight = float(l.split()[1])
            if l.find("FE_coeff_estat")==0:
                self.estat_weight = float(l.split()[1])
            if l.find("FE_coeff_desolv")==0:
                self.dsolv_weight = float(l.split()[1])
            if l.find("FE_coeff_tors")==0:
                self.tors_weight = float(l.split()[1])
            if l.find("atom_par")==0:
                ll = l.split()
                atomT = ll[1]
                all_types[atomT] = 1
                r,eps, v, sp, Rhb, ehb = map( float, ll[2:8])
                hb = int(ll[8])
                t = atomT+atomT
                Rij[t] = r
                epsij[t] = eps
                vol[atomT] = v
                solpar[atomT] = sp 
                Rij_hb[t] = Rhb 
                epsij_hb[t] = ehb 
                hbond[atomT] = hb
        #parcel out this new information to the various scorers:               
        #electrostatics:
        #newhb
        #keys are OAHD HDOA NAHD HDNA SAHD HDSA
        #Rij_hb and epsij_hb
        hbondT = self.terms[1][0]
        vdwT = self.terms[2][0]
        don_keys = []
        acc_keys = []
        for k,v in hbond.items():
            if v in [1,2]:
                don_keys.append(k)
            if v >2:
                acc_keys.append(k)
        old_hb_Rij = hbondT.Rij
        old_hb_epsij = hbondT.epsij
        old_vdw_Rij = vdwT.Rij
        old_vdw_epsij = vdwT.epsij
        hbondT.Rij = {}
        hbondT.epsij = {}
        vdwT.Rij = {}
        vdwT.epsij = {}
        #newvdw
        for t, val in Rij.items():
            vdwT.Rij[t] = val
            hbondT.Rij[t] = 0
        for t,val in epsij.items():
            vdwT.epsij[t] = val
            hbondT.epsij[t] = 0
        #then override the hbonders
        for t1 in acc_keys:
            for t2 in don_keys:
                hbondT.Rij[t1+t2] = Rij_hb[t1+t1]  #the value is in the donor entry only
                hbondT.Rij[t2+t1] = Rij_hb[t1+t1]  #the value is in the donor entry only
                hbondT.epsij[t1+t2] = epsij_hb[t1+t1]
                hbondT.epsij[t2+t1] = epsij_hb[t1+t1]
                vdwT.Rij[t1+t2] = 0 
                vdwT.Rij[t2+t1] = 0 
        #newdsolv
        self.terms[3][0].Solpars.update(solpar)
        self.terms[3][0].Vols.update(vol)
        self.supported_types = self.get_supported_types()


    def get_score(self):
        if self.ms is None:
            raise RuntimeError("no molecular system available in scorer")
        #replaced use of get_score_array because don't understand hbond_array
        #special handling
        score = 0.0
        for term, weight in self.terms:
            score = score + weight*term.get_score()
        #array = self.get_score_array()
        torsEnrg = 0
        if self.exclude_torsFreeEnergy==False:
            lig = self.ms.get_entities(self.ms.configuration[1])[0].top
            torsEnrg = lig.TORSDOF*self.tors_weight
        if self.verbose: print "torsEnrg=", torsEnrg
        if self.verbose: print "score=", score
        return score + torsEnrg


    def get_score_array(self):
        """ return a list of score for each terms per atoms"""
        # NEED TO CORRECT hbond
        # result = self.scorer.get_score_array()
        sal = score_array_list = []
        for t, w in self.terms:
            sal.append(t.get_score_array()*w)
        self.hbond_array = sal[1]
        result = Numeric.add(sal[0], sal[2])
        result = Numeric.add(result, sal[3])
        self.array = result
        return self.array


    def labels_atoms_w_nrg(self,score_array):
        """ will label each atoms with a nrg score """

        # label each first atom by sum of its vdw interaction energies 
        firstAts  = self.ms.get_entities(0)
        for i in range(len(firstAts)):
            # firstAts[i].vdw_energy = Numeric.add.reduce(score_array[i])
            hbond_val =  min(self.hbond_array[i])+max(self.hbond_array[i])
            setattr(firstAts[i], self.prop, Numeric.add.reduce(score_array[i])+hbond_val)
        # label each second atom by sum of its vdw interaction energies
        secondAts = self.ms.get_entities(1)
        swap_result = Numeric.swapaxes(score_array, 0,1)
        swap_hbond_array = Numeric.swapaxes(self.hbond_array, 0, 1)
        for i in range(len(swap_result)):
            hbond_val =  min(swap_hbond_array[i])+max(swap_hbond_array[i])
            setattr(secondAts[i], self.prop, Numeric.add.reduce(swap_result[i])+hbond_val)      

# AutoDock41.Scorer

        
class AutoGrid4Scorer(WeightedMultiTerm, AutoDockTermWeights4):
    """
A handy scorer for AutoGrid4 atom maps.

Note that the Electrostatics term does not contribute to the atom
maps but is in a map of its own (the .e.map).
ALSO Desolvation term energies are split 
the ligand_charge independent portion is in the atom map:
lig.solpar*rec.vol*sol_fn[dist]+(rec.solpar+solpar_q*rec.charge)*lig.vol*sol_fn[dist]

where as the ligand_charge dependent portion is in a map of its own (the 'd' map):
solpar_q*lig.charge*rec.vol*sol_fn[dist]
"""
    def __init__(self):
        WeightedMultiTerm.__init__(self)
        AutoDockTermWeights4.__init__(self)
        self.add_term(NewHydrogenBonding(), self.hbond_weight)
        self.add_term(NewVanDerWaals(), self.vdw_weight)
        self.add_term(NewDesolvationAtomMap(), self.dsolv_weight)
# AutoGrid4Scorer



if __name__ == '__main__':
    print "Test are in Tests/test_AutoDockScorer.py @@ WRITE ME!!"
    # test_scorer.run_test()


