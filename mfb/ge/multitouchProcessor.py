# import gamengine modules
from bge import logic
from bge import events
from bge import render
import mathutils

from .settings import *

# interpret touch events
def touchHandler(touches):
	if not touches:
		logic.multitouch = False
		return
	
	logic.multitouch = True
	if len(touches) == 1:
		# logic.tap = True
		...

	elif len(touches) == 2:
		# calculate some helpers vectors and coords
		dxVel = touches[0]["vel"][0] - touches[1]["vel"][0]
		dyVel = touches[0]["vel"][1] - touches[1]["vel"][1]
		sumxVel = touches[0]["vel"][0] + touches[1]["vel"][0]
		sumyVel = touches[0]["vel"][1] + touches[1]["vel"][1]
		meanPos = [(touches[0]["pos"][0] + touches[1]["pos"][0])/2.0, (touches[0]["pos"][1] + touches[1]["pos"][1])/2.0]
		
		# pan view
		if (abs(dxVel)+abs(dyVel)) < 0.5:		# magic number, consider this to be a 2-finger panning motion
			meanxVel = touches[0]["vel"][0] + touches[1]["vel"][0]
			meanyVel = touches[0]["vel"][1] + touches[1]["vel"][1]
			if meanyVel > 1:
				logic.mouseUp = True
			if meanyVel < -1:
				logic.mouseDown = True
			
		# rotate
		elif (sumxVel < 0.5) or (sumyVel < 0.5):	# magic number, consider this to be a 2 finger rotation
			if touches[0]["pos"][1] < touches[1]["pos"][1]:
				direction = -1
			else:
				direction = 1
			logic.viewRotTarget[2] += (dxVel + dyVel) * 0.02 * direction
		
		
	draw(touches)
	
def intersect(vec2,vecStart2, point2):
	a = mathutils.Vector(vecStart2)
	b = mathutils.Vector((vecStart2[0]*vec2[0]+vecStart2[0], vecStart2[1]*vec2[1]+vecStart2[1]))
	c = mathutils.Vector((point2))
	intersect = mathutils.geometry.intersect_line_sphere_2d(a,b, c, 1.0)
	return intersect

#draw touch points for debug
def draw(touches):
	logic.gui.MTpoint1.position = [-1,-1]
	logic.gui.MTpoint2.position = [-1,-1]
	logic.gui.MTpoint3.position = [-1,-1]
	logic.gui.MTpoint4.position = [-1,-1]
	logic.gui.MTpoint5.position = [-1,-1]
	logic.gui.MTpoint6.position = [-1,-1]
	logic.gui.MTpoint7.position = [-1,-1]
	logic.gui.MTpoint8.position = [-1,-1]
	logic.gui.MTpoint9.position = [-1,-1]
	logic.gui.MTpoint10.position = [-1,-1]
	
	try:
		logic.gui.MTpoint1.position = touches[0]["pos"]
		logic.gui.MTpoint1.size = [0.01*touches[0]["size"], 0.01*touches[0]["size"]]
		logic.gui.MTpoint2.position = touches[1]["pos"]
		logic.gui.MTpoint2.size = [0.01*touches[1]["size"], 0.01*touches[1]["size"]]
		logic.gui.MTpoint3.position = touches[2]["pos"]
		logic.gui.MTpoint3.size = [0.01*touches[2]["size"], 0.01*touches[2]["size"]]
		logic.gui.MTpoint4.position = touches[3]["pos"]
		logic.gui.MTpoint4.size = [0.01*touches[3]["size"], 0.01*touches[3]["size"]]
		logic.gui.MTpoint5.position = touches[4]["pos"]
		logic.gui.MTpoint5.size = [0.01*touches[4]["size"], 0.01*touches[4]["size"]]
		logic.gui.MTpoint6.position = touches[5]["pos"]
		logic.gui.MTpoint6.size = [0.01*touches[5]["size"], 0.01*touches[5]["size"]]
		logic.gui.MTpoint7.position = touches[6]["pos"]
		logic.gui.MTpoint7.size = [0.01*touches[6]["size"], 0.01*touches[6]["size"]]
		logic.gui.MTpoint8.position = touches[7]["pos"]
		logic.gui.MTpoint8.size = [0.01*touches[7]["size"], 0.01*touches[7]["size"]]
		logic.gui.MTpoint9.position = touches[8]["pos"]
		logic.gui.MTpoint9.size = [0.01*touches[8]["size"], 0.01*touches[8]["size"]]
		logic.gui.MTpoint10.position = touches[9]["pos"]
		logic.gui.MTpoint10.size = [0.01*touches[9]["size"], 0.01*touches[9]["size"]]
	except:
		pass