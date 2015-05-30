
try:
	import urllib.request as urllib2
except:
	import urllib2
import json

def get_street_names(loc):
    # req = urllib2.urlopen('http://overpass.osm.rambler.ru/cgi/interpreter?data=[out:json];way[%22addr:city%22%3D%22'+loc[1].capitalize()+'%22]%3Bout%3B').read().decode('utf-8')
    # req = urllib2.urlopen('http://overpass.osm.rambler.ru/cgi/interpreter?data=[out:csv(::"id","tiger:name_base","tiger:name_type")];way["highway"]["tiger:name_base"]["tiger:name_type"]('+str(loc[3]-0.1)+","+str(loc[4]+0.15)+","+str(loc[3]+0.1)+","+str(loc[4]-0.15)+')%3Bout%3B').read().decode('utf-8')
    # req = urllib2.urlopen('http://overpass.osm.rambler.ru/cgi/interpreter?data=[out:csv%28::%22id%22,%22tiger:name_base%22,%22tiger:name_type%22%29];way[%22highway%22][%22tiger:name_base%22][%22tiger:name_type%22]%28' +str(loc[3]-0.1)+","+str(loc[4]-0.15)+","+str(loc[3]+0.1)+","+str(loc[4]+0.15)+ '%29%3Bout%201000%3B').read().decode('utf-8')
    req = urllib2.urlopen('http://overpass.osm.rambler.ru/cgi/interpreter?data=[out:csv%28::%22id%22,%22tiger:name_base%22,%22tiger:name_type%22%29];way[%22highway%22][%22tiger:name_base%22][%22tiger:name_type%22]%28' +str(loc[3]-0.03)+","+str(loc[4]-0.05)+","+str(loc[3]+0.03)+","+str(loc[4]+0.05)+ '%29%3Bout%3B').read().decode('utf-8')
    result = [i.split('\t') for i in req.splitlines()[1:]]
    streets = {}
    for i in result:
        if i[2] not in streets:
            if i[2].isalpha():
                streets[i[2]] = []
            else:
                continue
        if i[1] not in streets[i[2]]:
            if i[1].isalpha():
                streets[i[2]].append(i[1])
    newstreets = {}
    for i in streets:
        if streets[i]:
            newstreets[i] = streets[i]

    return newstreets



if __name__=="__main__":
    get_street_names([0,"Philadelphia", "", 39.95, -75.1667])
