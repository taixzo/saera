from geopy.distance import great_circle as distance
from geopy.point import Point
import math
import polyline

def dist_to_line(a, b, c):
	"""Return distance from point a to line (b, c)."""
	dab = distance(a, b).meters or 0.00000001
	dac = distance(a, c).meters or 0.00000001
	dbc = distance(b, c).meters or 0.00000001
	semiperim = (dab+dac+dbc)/2
	try:
		A = math.sqrt(semiperim*(semiperim-dab)*(semiperim-dac)*(semiperim-dbc))
	except ValueError as e:
		# Most likely one of the legs is 0 and that is screwing up the math
		# Points are therefore probably colinear, so return
		if dab>dbc:
			return dac
		elif dac>dbc:
			return dab
		else:
			return min(dab, dac)
	d = 2*A/dab
	if dac > math.sqrt(dab**2 + dbc**2):
		return dbc
	elif dbc > math.sqrt(dab**2 + dac**2):
		return dac
	else:
		return d

def distance_to_polyline(point, line):
	if isinstance(point, list) or isinstance(point, tuple):
		point = Point(*point)
	geline = [Point(i[0], i[1]) for i in line]
	# return [dist_to_line(line[i],line[i+1], point) for i in range(len(line)-1)]
	return min([dist_to_line(line[i],line[i+1], point) for i in range(len(line)-1)])

if __name__=="__main__":