# import GE modules
from bge import logic
from bge import events
from bge import render

# import native python
import os, sys, traceback
import logging

from .settings import *


def getMol(filepath):
	'''Parse PDB file and return mol obj'''
	import MolKit
	mol = MolKit.Read(filepath)[-1]
	return mol


def getMolInfo(pdbFullPath, mol):

	'''Get general information of molecule'''
	title = ''				# TITLE, structure name
	chaininfo = {}			# COMPND MOLECULE chain's title
	chainDescTemp = ''		#
	chaininfoTemp = {}		#
	detmethod = ''			# EXPDTA, 
	resolution = ''			# REMARK 2 resolution angstroms
	authors = []			# list of authors
	articlename = ''		# name of article
	journal = ''			# name of journal
	issn = ''				# ISSN code
	doi = ''				# DOI code
	molIDFlag = False		# continuation of COMPND

	try:
		file = open(pdbFullPath, 'r')
		lines = file.readlines()
		file.close()
	except:
		logging.exception("pdbparser.geMolInfo error")

	# parse pdb for general info
	for line in lines:
		# get title
		if line[:5] == 'TITLE':
			nxtline = line[9:10]
			if nxtline == ' ':
				title = title + line[10:].strip().lower()
			else:
				title = title + ' ' + line[10:].strip().lower()

		# Journal Info: Authors, Article Title, Journal, Journal Volume, ISSN
		elif line[:4] == 'JRNL':

			if line[12:16] == 'AUTH':
				for author in line[19:79].strip().split(','):
					authors.append(author.title())

			elif line[12:16] == 'TITL':
				articlename = articlename + line[19:79].strip().title()

			elif line[12:16] == 'REF ':
				journal = (journal + line[19:47].strip() + ' ' + line[49:51].strip() + ' ' +  line[51:55].strip() + ' ' + line[56:66].strip()).title()

			elif line[12:16] == 'REFN':
				if line[35:39].strip() == 'ISSN':
					issn = issn + line[35:39].strip() + ' ' + line[40:65].strip()

			elif line[12:16] == 'DOI ':
				doi = line[19:79].strip()

				if not doi:
					doi = 'N/A'

		# experiment technique
		elif line[:6] == 'EXPDTA':
			detmethod = line[10:].strip()

		# resolution angstroms
		elif line[:10] == 'REMARK   2':
			if line[11:12] != '' and line[12:37] != 'RESOLUTION. NOT APPLICABLE':
				resolution = line[26:40]

		# chain info
		elif line[:6] == 'COMPND':
			if line[11:19] == 'MOLECULE':
				chainDescTemp = line[21:].strip()

			elif line[11:16] == 'CHAIN':
				chainList = line[17:].strip().split(',')
				for chain in chainList:
					label = chain.strip()[0]		# remove additional letter at the end
					chaininfoTemp[label.upper()] = chainDescTemp[:]


	for chain in mol.chains:
		try:
			desc = chaininfoTemp[str(chain.name).upper()]
			if desc[-1] == ';':
				desc = desc[:-1]
			chaininfo[str(chain.name)] = desc
		except Exception as E:
			chaininfo[str(chain.name)] = "N/A"


	return (title,chaininfo,detmethod, resolution, authors, articlename, journal, issn, doi)
