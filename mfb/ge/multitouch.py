from bge import logic

from . import multitouchProcessor

import ctypes


CFArrayRef = ctypes.c_void_p
CFMutableArrayRef = ctypes.c_void_p
CFIndex = ctypes.c_long

MultitouchSupport = ctypes.CDLL("/System/Library/PrivateFrameworks/MultitouchSupport.framework/MultitouchSupport")

CFArrayGetCount = MultitouchSupport.CFArrayGetCount
CFArrayGetCount.argtypes = [CFArrayRef]
CFArrayGetCount.restype = CFIndex

CFArrayGetValueAtIndex = MultitouchSupport.CFArrayGetValueAtIndex
CFArrayGetValueAtIndex.argtypes = [CFArrayRef, CFIndex]
CFArrayGetValueAtIndex.restype = ctypes.c_void_p

MTDeviceCreateList = MultitouchSupport.MTDeviceCreateList
MTDeviceCreateList.argtypes = []
MTDeviceCreateList.restype = CFMutableArrayRef

class MTPoint(ctypes.Structure):
	_fields_ = [("x", ctypes.c_float),
				("y", ctypes.c_float)]

class MTVector(ctypes.Structure):
	_fields_ = [("position", MTPoint),
				("velocity", MTPoint)]

class MTData(ctypes.Structure):
	_fields_ = [
	  ("frame", ctypes.c_int),
	  ("timestamp", ctypes.c_double),
	  ("identifier", ctypes.c_int),
	  ("state", ctypes.c_int),	# Current state (of unknown meaning).
	  ("unknown1", ctypes.c_int),
	  ("unknown2", ctypes.c_int),
	  ("normalized", MTVector),	 # Normalized position and vector of
								 # the touch (0 to 1).
	  ("size", ctypes.c_float),	 # The area of the touch.
	  ("unknown3", ctypes.c_int),
	  # The following three define the ellipsoid of a finger.
	  ("angle", ctypes.c_float),
	  ("major_axis", ctypes.c_float),
	  ("minor_axis", ctypes.c_float),
	  ("unknown4", MTVector),
	  ("unknown5_1", ctypes.c_int),
	  ("unknown5_2", ctypes.c_int),
	  ("unknown6", ctypes.c_float),
	]

MTDataRef = ctypes.POINTER(MTData)

MTContactCallbackFunction = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, MTDataRef,
	ctypes.c_int, ctypes.c_double, ctypes.c_int)

MTDeviceRef = ctypes.c_void_p

MTRegisterContactFrameCallback = MultitouchSupport.MTRegisterContactFrameCallback
MTRegisterContactFrameCallback.argtypes = [MTDeviceRef, MTContactCallbackFunction]
MTUnregisterContactFrameCallback = MultitouchSupport.MTUnregisterContactFrameCallback
MTUnregisterContactFrameCallback.argtypes = [MTDeviceRef, MTContactCallbackFunction]

MTDeviceStart = MultitouchSupport.MTDeviceStart
MTDeviceStart.argtypes = [MTDeviceRef, ctypes.c_int]

MTDeviceStop = MultitouchSupport.MTDeviceStop
MTDeviceStop.argtypes = [MTDeviceRef]
MTDeviceRelease = MultitouchSupport.MTDeviceRelease
MTDeviceRelease.argtypes = [MTDeviceRef]

###

@MTContactCallbackFunction
def callback(device, data_ptr, n_fingers, timestamp, frame):
	touches = []
	for i in range(n_fingers):
		data = data_ptr[i]
		touch = {}
		touch["pos"] = [data.normalized.position.x, data.normalized.position.y]
		touch["vel"] = [data.normalized.velocity.x, data.normalized.velocity.y]
		touch["size"] = data.size*2.0
		touches.append(touch)
		
	multitouchProcessor.touchHandler(touches)			# send touch data to multitouchProcessor for processing
	return 0

devices = MultitouchSupport.MTDeviceCreateList()
num_devices = CFArrayGetCount(devices)
print ("Number of Multitouch Devices:", num_devices)
logic.MTdevices = []
for i in range(num_devices):
	device = CFArrayGetValueAtIndex(devices, i)
	MTRegisterContactFrameCallback(device, callback)
	MTDeviceStart(device, 0)

	logic.MTdevices.append(devices)

# stop device and deregister callback function
def stopDevices():
	devices = logic.MTdevices
	for device in devices:
		MTUnregisterContactFrameCallback(device, callback)
		MTDeviceStop(device)
		MTDeviceRelease(device)
	