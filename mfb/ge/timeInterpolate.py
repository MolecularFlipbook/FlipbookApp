from .helpers import *

def interpolate(self, time):
	# loop through object first
	for objName, mvbObj in self.objects.items():
		# find slide A and B that has keyframe given 'time'
		
		# get all the slides that have keyframe data for this particular object
		slides = [slide for slide in self.slides if objName in slide.animeData]
		# print(slides)

		# find A and B with keyframe
		A = None
		B = None
		for slide in slides:
			if slide.time <= time:
				A = slide
			elif slide.time > time and not B:
				B = slide

		# use mock slides when interpolation data is not available
		if A and B:
			pass
		elif A:
			B = A
		elif B:
			A = B

		if A and B:
				
			AData = A.animeData[objName]
			BData = B.animeData[objName]

			if A == B:
				# extrapolate data
				mvbObj.loc = AData["loc"]
				mvbObj.rot = AData["rot"]
				mvbObj.color = AData["col"]
				mvbObj.shader = AData["shader"]
				mvbObj.drawMode = AData["drawMode"]
				mvbObj.updateMarkers(AData["markers"])
			
			else:
				# interpolate
				# compute new viewtime based on new A and B
				timeIntervalA = time - A.time 			# always positive, time from last slide
				timeIntervalB = B.time - time 			# always positive, time til next slide

				assert(timeIntervalA >= 0)
				assert(timeIntervalB >= 0)

				# normalized viewTime, and fancy interpolation
				viewTime = timeIntervalB / (timeIntervalA + timeIntervalB)
				# viewTime = smoothstep(viewTime)

				# interpolate
				mvbObj.loc = mix(AData["loc"], BData["loc"], viewTime)
				mvbObj.rot = mix(AData["rot"], BData["rot"], viewTime)
				mvbObj.color = mix(AData["col"], BData["col"], viewTime)

				if viewTime > 0.5:
					mvbObj.shader = AData["shader"]
				else:
					mvbObj.shader = BData["shader"]

				if viewTime >  0.5:
					mvbObj.drawMode = AData["drawMode"]
				else:
					mvbObj.drawMode = BData["drawMode"]

				if viewTime > 0.5:
					mvbObj.updateMarkers(AData["markers"])
				else:
					mvbObj.updateMarkers(BData["markers"])
