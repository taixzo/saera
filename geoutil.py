from geopy.distance import great_circle as distance
from geopy.point import Point
import math
import polyline

def dist_to_line(a, b, c):
	dab = distance(a, b).meters
	dac = distance(a, c).meters
	dbc = distance(b, c).meters
	perim = (dab+dac+dbc)/2
	A = math.sqrt(perim*(perim-dab)*(perim-dac)*(perim-dbc))
	d = 2*A/dab
	if dac > math.sqrt(dab**2 + dbc**2):
		return dbc
	elif dbc > math.sqrt(dab**2 + dac**2):
		return dac
	else:
		return d

def distance_to_polyline(point, line):
	geline = [Point(i[0], i[1]) for i in line]
	# return [dist_to_line(line[i],line[i+1], point) for i in range(len(line)-1)]
	return min([dist_to_line(line[i],line[i+1], point) for i in range(len(line)-1)])

if __name__=="__main__":