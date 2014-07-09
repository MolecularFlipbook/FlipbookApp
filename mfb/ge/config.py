from bge import logic

import pickle
import logging
import time

DEFAULT_CONFIG = {
	'useTutorial': True,
	'lastUpdate': None,
}

configPath = None

def set(param, value):
	''' allows one to write a config option'''
	logic.config[param] = value
	write()


def write(path = None):
	''' writes the config to file'''
	if not path:
		global configPath
		path = configPath

	try:
		fp = open(path, mode='wb')
		pickle.dump(logic.config, fp)
	except Exception as E:
		logging.error('Error opening config file for writing' + str(E))
	else:
		fp.close()


def load(path):
	''' load the config from file'''
	try:
		global configPath
		configPath = path
		fp = open(path, mode='rb')
		logic.config = pickle.load(fp)
	except Exception as E:
		logging.error('Error opening config file for reading' + str(E))
		logic.config = DEFAULT_CONFIG

