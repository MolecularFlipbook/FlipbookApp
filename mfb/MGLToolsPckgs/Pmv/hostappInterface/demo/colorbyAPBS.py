# -*- coding: utf-8 -*-
"""
Created on Fri Oct  1 08:13:38 2010

@author: Ludovic Autin

color a MSMS surface or any geometry according an APBS electrostatic grid (.dx)

"""
#1-get the grid or use the current grid ?
grid = epmv.gui.current_traj[0]# self.grids3D.values()[0]
#2-get the surface from the current mol ?
mol = epmv.gui.current_mol
if mol.geomContainer.geoms.has_key('MSMS-MOL'+mol.name):
    surf = mol.geomContainer.geoms['MSMS-MOL'+mol.name]# self.Mols[0].geomContainer.geoms['MSMS-MOL1TIMtr']
else :
    epmv.gui.displaySurf()
    surf = mol.geomContainer.geoms['MSMS-MOL'+mol.name]
#3-color,offset apply on vertex normal for the volume projection, stddev scale factor apply on the 
#standar deviation value
epmv.APBS2MSMS(grid,surf=surf,offset=1.0,stddevM=5.0)
