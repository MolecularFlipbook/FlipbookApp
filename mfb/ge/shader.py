# import gamengine modules
from bge import logic
from bge import events
from bge import render

# import mvb's own modules
from .settings import *
from .helpers import *

import os, time

def initMarker(obj, shaderName, color = [0,1,0]):
	"""Initializes or update a GLSL FP/VP shader and apply it to object's material slots """
	mesh = obj.meshes[0]

	for mat in mesh.materials:
		shader = mat.getShader()
		if shader != None:
			if not shader.isValid():
				fragPath = os.path.join(logic.basePath, "shaders", shaderName+".fp")
				frag = open(fragPath).read()
				vertPath = os.path.join(logic.basePath, "shaders", shaderName+".vp")
				vert = open(vertPath).read()
				if shader: shader.delSource()
				shader.setSource(vert, frag, 1)
		# set updated col
		shader.setUniform3f('color', *color)



def initSky(obj, shaderName, color = [1,1,1,1], stretch = False, update = False):
	"""Initializes or update a GLSL FP/VP shader and apply it to sky's material slots """
	mesh = obj.meshes[0]

	for mat in mesh.materials:
		shader = mat.getShader()
		if shader != None:
			if not shader.isValid() or update:
				fragPath = os.path.join(logic.basePath, "shaders", shaderName+".fp")
				frag = open(fragPath).read()
				vertPath = os.path.join(logic.basePath, "shaders", shaderName+".vp")
				vert = open(vertPath).read()
				if shader: shader.delSource()
				shader.setSource(vert, frag, 1)
		# set updated col
		shader.setUniform4f('color', *color)
		shader.setUniform2f('dimension', render.getWindowWidth(), render.getWindowHeight())
		shader.setUniform1f('stretch', stretch)
		shader.setSampler('texmap', 0)



def updateSky(obj):
	"""Update the shader every frame"""
	mesh = obj.meshes[0]
	for mat in mesh.materials:
		shader = mat.getShader()

		if shader != None:
			# set updated col
			col = logic.mvb.bgColor[:]
			col.append(logic.mvb.bgColorFactor)
			shader.setUniform4f('color', *col)
			
			shader.setUniform2f('dimension', render.getWindowWidth(), render.getWindowHeight())
			
			shader.setUniform1f('stretch', logic.mvb.bgImageStretch)
			
			shader.setSampler('texmap', 0)
		else:
			print('no shader?')



def initProtein(obj, shaderName, update = False, setUniformsFunc=None):
	"""Initializes or update a GLSL FP/VP shader and apply it to object's material slots """
	mesh = obj.meshes[0]

	for mat in mesh.materials:
		shader = mat.getShader()
		if shader != None:
			if not shader.isValid() or update:
				fragPath = os.path.join(logic.basePath, "shaders", shaderName+".fp")
				frag = open(fragPath).read()
				vertPath = os.path.join(logic.basePath, "shaders", shaderName+".vp")
				vert = open(vertPath).read()
				if shader: shader.delSource()
				shader.setSource(vert, frag, 1)
		# set updated col
		shader.setUniform3f('color', 1,1,1)
		shader.setUniform1f('time', time.time()%10000.0)
		shader.setUniform1f('gray', 0.0)
		# shader.setUniform1f('select', 0.0)

		if setUniformsFunc:
			setUniformsFunc(shader)


def updateProtein(obj, color=[1,1,1], setUniformsFunc=None):
	"""Update the shader every frame"""
	mesh = obj.meshes[0]
	assert mesh
	for mat in mesh.materials:
		shader = mat.getShader()

		if shader != None:
			if logic.mvb.preActiveObj and obj in logic.mvb.preActiveObj:
				shader.setUniform3f('highlight', *highlightColor)
			else:
				shader.setUniform3f('highlight', 0.0, 0.0, 0.0)

			# if obj in logic.mvb._activeObjs:
			# 	shader.setUniform1f('select', 1.0)
			# else:
			# 	shader.setUniform1f('select', 0.0)

			if not logic.mvb._activeObjs:
				shader.setUniform1f('gray', 0.0)
			elif obj in logic.mvb._activeObjs:
				shader.setUniform1f('gray', 0.0)
			else:
				shader.setUniform1f('gray', 1.0)

			# set updated col
			shader.setUniform3f('color', *color)
			shader.setUniform1f('time', time.time()%10000.0)

			if setUniformsFunc:
				setUniformsFunc(shader)
		else:
			print('no shader?')


def initWidget(obj, shaderName):
	"""Initializes a GLSL FP/VP shader and apply it to object's material slots """
	mesh = obj.meshes[0]

	for mat in mesh.materials:
		shader = mat.getShader()
		if shader != None:
			if not shader.isValid():
				fragPath = os.path.join(logic.basePath, "shaders", shaderName+".fp")
				frag = open(fragPath).read()
				vertPath = os.path.join(logic.basePath, "shaders", shaderName+".vp")
				vert = open(vertPath).read()
				shader.setSource(vert, frag, 1)

			shader.setSampler('texture', 0)
			shader.setUniform1f('opacity', 0)


def updateWidget(obj, opacity = None):
	"""Update the shader every frame"""
	mesh = obj.meshes[0]

	for mat in mesh.materials:
		shader = mat.getShader()
		shader.setUniform1f('opacity', opacity)

