#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import pyotherside

from time import timezone, sleep
from datetime import datetime, time, timedelta
import calendar
import logging
import pygoogle
import wikikit
import duckduckgo
import re
import math
import random
# import urllib2
try:
	import urllib.request as urllib2
except:
	import urllib2
try:
	import json
except ImportError:
	import simplejson as json

import sys
import platform as pfm
import subprocess

from guessing import Guesser

if sys.version_info[0]<3:
	if sys.version_info[1]<7:
		try:
			import fremantle_hw as platform
		except ImportError:
			try:
				import harmattan_hw as platform
			except ImportError:
				import cmd_hw as platform
	else:
		if pfm.linux_distribution()[0].lower()=='ubuntu':
			import ubuntu_hw as platform
		elif sys.platform == 'darwin':
			import osx_hw as platform
		else:
			import cmd_hw as platform
else:
	#import harmattan_hw as platform
	# import x86_hw as platform
	try:
		import sailfish_hw as platform
	except ImportError:
		if pfm.linux_distribution()[0].lower()=='ubuntu':
			import ubuntu_hw as platform
		else:
			import cmd_hw as platform

# if not os.path.exists(platform.memory_path):

# 	data = {'username':None}

log_level = logging.INFO

config = platform.config

if sys.version < '3':
	import codecs
	def u(x):
		# return codecs.unicode_escape_decode(x)[0]
		try:
			return str(x)
		except:
			return codecs.unicode_escape_decode(x)[0]
else:
	def u(x):
		return x

class ForgottenException(Exception):
	pass

class Memory:
	def __init__(self, forgettable=True):
		self.items = {}
		self.forgettable = forgettable
	def set(self,item,value,duration=10):
		self.items[item] = [value,duration]
	def get(self,item):
		try:
			return self.items[item][0]
		except KeyError:
			raise ForgottenException
	def get_more_recent(self, *items):
		lst = [self.items[item]+[item] for item in items if item in self.items]
		lst.sort(key=lambda x: x[1])
		try:
			return (lst[-1][0], lst[-1][2])
		except IndexError:
			raise ForgottenException
	def tick(self):
		if self.forgettable:
			for i in list(self.items):
				self.items[i][1]-=1
				if self.items[i][1]<0:
					del self.items[i]


import math, sys

def packageTrackingNumber(num):
	
	if re.match(r"\b(1Z ?[0-9A-Z]{3} ?[0-9A-Z]{3} ?[0-9A-Z]{2} ?[0-9A-Z]{4} ?[0-9A-Z]{3} ?[0-9A-Z]|[\dT]\d\d\d ?\d\d\d\d ?\d\d\d)\b", num) is not None:
		return "UPS"
	elif re.match(r"\b(1Z ?[0-9A-Z]{3} ?[0-9A-Z]{3} ?[0-9A-Z]{2} ?[0-9A-Z]{4} ?[0-9A-Z]{3} ?[0-9A-Z]|[\dT]\d\d\d ?\d\d\d\d ?\d\d\d|\d{22})\b", num) is not None:
		return "UPS"
	elif re.match(r"(\b96\d{20}\b)|(\b\d{15}\b)|(\b\d{12}\b)", num) is not None:
		return "FEDEX"
	elif re.match(r"\b((98\d\d\d\d\d?\d\d\d\d|98\d\d) ?\d\d\d\d ?\d\d\d\d( ?\d\d\d)?)\b", num) is not None:
		return "FEDEX"
	elif re.match(r"^[0-9]{15}$", num) is not None:
		return "FEDEX"
	elif re.match(r"(\b\d{30}\b)|(\b91\d+\b)|(\b\d{20}\b)", num) is not None:
		return "USPS"
	elif re.match(r"^E\D{1}\d{9}\D{2}$|^9\d{15,21}$", num) is not None:
		return "USPS"
	elif re.match(r"^91[0-9]+$", num) is not None:
		return "USPS"
	elif re.match(r"^[A-Za-z]{2}[0-9]+US$", num) is not None:
		return "USPS"
	else:
		return None

def is_day(lon,dt=None):
	sin,cos,pi = math.sin,math.cos,math.pi
	if dt is None:
		dt = datetime.now()
	longit = float(lon)

	gamma = 2 * pi / 365 * (dt.timetuple().tm_yday - 1 + float(dt.hour - 12) / 24)
	eqtime = 229.18 * (0.000075 + 0.001868 * cos(gamma) - 0.032077 * sin(gamma) \
			 - 0.014615 * cos(2 * gamma) - 0.040849 * sin(2 * gamma))
	decl = 0.006918 - 0.399912 * cos(gamma) + 0.070257 * sin(gamma) \
		   - 0.006758 * cos(2 * gamma) + 0.000907 * sin(2 * gamma) \
		   - 0.002697 * cos(3 * gamma) + 0.00148 * sin(3 * gamma)
	time_offset = eqtime + 4 * longit
	tst = dt.hour * 60 + dt.minute + dt.second / 60 + time_offset
	solar_time = datetime.combine(dt.date(), time(0)) + timedelta(minutes=tst)
	return solar_time.hour<12

def decodePath (encoded, is3D):
	length = len(encoded)
	index = 0
	array = []
	lat = 0
	lng = 0
	ele = 0

	while index < length:
		shift = 0
		result = 0
		while True:
			b = ord(encoded[index]) - 63
			result |= (b & 0x1f) << shift
			shift += 5
			index += 1
			if b<0x20: break
		deltaLat = ~(result >> 1) if (result & 1) else (result >> 1)
		lat += deltaLat

		shift = 0;
		result = 0;

		while True:
			b = ord(encoded[index]) - 63;
			result |= (b & 0x1f) << shift;
			shift += 5;
			index +=1
			if b<0x20: break
		deltaLon = ~(result >> 1) if (result & 1) else (result >> 1)
		lng += deltaLon;

		if is3D:
			# elevation
			shift = 0;
			result = 0;
			while True:
				b = ord(encoded[index]) - 63
				result |= (b & 0x1f) << shift
				shift += 5
				index += 1
				if b >= 0x20: break
			deltaEle = ~(result >> 1) if (result & 1) else (result >> 1)
			ele += deltaEle;
			array.append([lng * 1e-5, lat * 1e-5, ele / 100])
		else:
			array.append([lng * 1e-5, lat * 1e-5])

	# // end = new Date().getTime();
	# // print ("decoded " + length + " coordinates in " + ((end - start) / 1000) + "s");
	return array

global direction_list
direction_list = []

def toRadians(x):
	return x*0.0174532925

def geo_distance (lat1, lon1, lat2, lon2):
	R = 6371000; # metres
	phi1 = toRadians(lat1)
	phi2 = toRadians(lat2)
	deltaphi = toRadians(lat2-lat1)
	deltalambda = toRadians(lon2-lon1)

	a = math.sin(deltaphi/2) * math.sin(deltaphi/2) + math.cos(phi1) * math.cos(phi2) * math.sin(deltalambda/2) * math.sin(deltalambda/2)
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

	d = R * c
	return d

def formatTime(seconds):
	if seconds<60:
		return str(int(round(seconds)))+" second"+("s" if round(seconds)!=1 else "")
	elif seconds<300:
		return str(int(round(seconds/60)))+" minute"+("s " if round(seconds/60)!=1 else " ")+str(int(round(seconds))%60)+" second"+("s" if round(seconds)%60!=1 else "")
	elif seconds<3600:
		return str(int(round(seconds/60)))+" minute"+("s" if round(seconds/60)!=1 else "")
	elif seconds<36000:
		return str(int(round(seconds/3600)))+" hour"+("s " if round(seconds/3600)!=1 else " ")+str(int(round(seconds/60))%60)+" minute"+("s" if round(seconds/60)%60!=1 else "")
	else:
		return str(int(round(seconds/3600)))+" hour"+("s" if round(seconds/3600)!=1 else "")

def formatDistance(meters):
	if config.imperial:
		feet = 3.28084*meters
		if feet>26400: # 5 miles
			miles = int(round(feet/5280))
			return str(miles)+" miles"
		elif feet>=5280:
			miles = feet/5280
			return "{0:.1f}".format(round(miles,1)) + " mile"+("s" if round(miles,1) != 1 else "")
		elif feet>100:
			return str(int(round(feet/50)*50))+" feet"
		elif feet>25:
			return str(int(round(feet/10)*10))+" feet"
		else:
			return str(int(round(feet)))+(" feet" if round(feet) != 1 else " foot")
	else:
		if meters>5000:
			return str(int(round(meters/1000)))+" kilometers"
		elif meters>1000:
			return "{0:.1f}".format(round(meters/1000,1)) + " kilometers"+("s" if round(meters/1000,1) != 1 else "")
		elif meters>100:
			return str(int(round(meters/50)*50))+" meters"
		elif feet>25:
			return str(int(round(meters/10)*10))+" meters"
		else:
			return str(int(round(meters)))+(" meters" if round(feet) != 1 else " meter")

class Saera:
	def __init__(self):
		self.short_term_memory = Memory()
		self.long_term_memory = Memory(forgettable=False)
		self.guesser = Guesser()
		# pass
	def execute_text(self, string):
		# try:
			# result = {
			# 			'outcome': {
			# 				'intent':'alarm',
			# 				'entities':{
			# 					'datetime':datetime(2015,2,20,9),
			# 				}
			# 			}
			# 		}
		string = string.replace('.','').replace(',','').replace('!','').replace('?','')
		result = self.guesser.guess(string)
			# result = self.w.get_message(string, context={"timezone":"America/New_York"})
		# except:
		# 	'''# Hack. Hacky hack hack. Python stdlib on Sailfish was compiled without SSL for some reason.
		# 	# So rather than installing an extra version of Python, we use curl.
		# 	# ...
		# 	# ...
		# 	# WTF, CURL HAS HTTPS DISABLED TOO
		# 	raw_result = subprocess.Popen(["curl",
		# 								   "-XGET",
		# 								   "'https://api.wit.ai/message?q="+string.replace(" ","%20")+"'",
		# 								   "-H",
		# 								   "'Authorization: Bearer CH4ZMQO2X7VGXBCLERMDJFFO4RYQWFCK'"], stdout=subprocess.PIPE).communicate()
		# 	int_result = raw_result[0].decode('utf-8')
		# 	print(int_result)
		# 	result = json.loads(int_result)'''
		# 	pass
		return self.process(result)
	def hello(self, result):
		try:
			# return "Hello, "+self.long_term_memory.get("nickname")
			platform.cur.execute("SELECT * FROM Variables WHERE VarName='name'")
			row = platform.cur.fetchone()
			if row:
				return "Hello, "+row['Value']+"!"
			else:
				return "Hello!"
		except ForgottenException:
			return "Hello!"
	def set_alarm(self,result):
		self.short_term_memory.set('intent','alarm',2)
		if 'time' in result['outcome']['entities']:
			# alarm_time = datetime.strptime(result['outcome']['entities']['time']['value']['from'][:-6], "%Y-%m-%dT%H:%M:%S.%f")
			alarm_time = result['outcome']['entities']['time']
			# platform.set_alarm(calendar.timegm(alarm_time.utctimetuple()))
			platform.set_alarm(alarm_time)
			self.short_term_memory.set('time',alarm_time)
			return "Setting alarm for "+str(alarm_time.hour)+":"+alarm_time.strftime("%M.")
		elif 'location' in result['outcome']['entities']:
			location = result['outcome']['entities']['location']['value']
			# TODO: location alarms
			return "Ok, I'll wake you when you get to "+location+"."
		else:
			try:
				alarm_time = self.short_term_memory.get('time')
				platform.set_alarm(calendar.timegm(alarm_time.utctimetuple()))
				return "Setting alarm for "+str(alarm_time.hour)+":"+alarm_time.strftime("%M.")
			except ForgottenException:
				return "What time do you want the alarm set for?"
	def weather(self,result):
		print (result)
		self.short_term_memory.set('intent','weather')
		here = False
		if 'location' in result['outcome']['entities']:
			location = result['outcome']['entities']['location']
			platform.cur.execute("SELECT * FROM Locations WHERE LocName='"+location+"'")
			loc = platform.cur.fetchone()
			if not loc:
				# How to convert a generalized location to a city??
				try:
					req = urllib2.urlopen('http://api.geonames.org/searchJSON?q='+location.replace(" ","+")+'&username=taixzo').read().decode("utf-8")
				except:
					return "I need an internet connection to look up the weather, sorry."
				locdic = json.loads(req)
				loc = (0,locdic['geonames'][0]["toponymName"],"",locdic['geonames'][0]["lat"],locdic['geonames'][0]["lng"])
				try:
					tz = json.loads(urllib2.urlopen('http://api.geonames.org/timezoneJSON?lat='+locdic['geonames'][0]["lat"]+'&lng='+locdic['geonames'][0]["lng"]+'&username=taixzo').read().decode("utf-8"))['rawOffset']
				except:
					return "I need an internet connection to look up the weather, sorry."
				platform.cur.execute('INSERT INTO Locations (LocName, Zip, Latitude, Longitude, Timezone) VALUES ("'+loc[1]+'", "", '+loc[3]+', '+loc[4]+', '+str(tz)+')')
				platform.conn.commit()
		else:
			platform.cur.execute("SELECT * FROM Variables WHERE VarName='here'")
			loc = platform.cur.fetchone()
			if loc:
				platform.cur.execute("SELECT * FROM Locations WHERE Id="+str(loc[2]))
				loc = platform.cur.fetchone()
				here = True
			else:
				platform.cur.execute("SELECT * FROM Variables WHERE VarName='home'")
				loc = platform.cur.fetchone()
				if loc:
					platform.cur.execute("SELECT * FROM Locations WHERE Id="+str(loc[2]))
					loc = platform.cur.fetchone()
					here = True
				else:
					return "Where do you live?"
			# location = 'New York'
		try:
			# self.short_term_memory.set('location',location)
			if 'time' in result['outcome']['entities']:
				is_time = True
				f = urllib2.urlopen('http://api.wunderground.com/api/0a02b434d9bf118f/hourly/geolookup/conditions/q/'+str(loc[3])+','+str(loc[4])+'.json').read()
			else:
				is_time = False
				f = urllib2.urlopen('http://api.wunderground.com/api/0a02b434d9bf118f/geolookup/conditions/q/'+str(loc[3])+','+str(loc[4])+'.json').read()
		except urllib2.URLError:
			return "I need an internet connection to look up the weather, sorry."
		json_string = f.decode("utf-8")
		parsed_json = json.loads(json_string)
		location = parsed_json['location']['city']
		if is_time:
			fcst = [i for i in parsed_json['hourly_forecast'] if int(i['FCTTIME']['hour'])==result['outcome']['entities']['time'].hour][0]
			temp_f = int(fcst['temp']['english'])
			temp_c = int(fcst['temp']['metric'])
			feelslike_f = float(fcst['feelslike']['english'])
			feelslike_c = float(fcst['feelslike']['metric'])
			wind_speed = int(fcst['wspd']['english'])
			wind_string = "calm" if wind_speed<3 else str(wind_speed)+" mph "+fcst['wdir']['dir']
			weather = fcst['condition'].lower()
			pop = int(fcst['pop'])
			hour = str(result['outcome']['entities']['time'].hour)
		else:
			temp_f = int(parsed_json['current_observation']['temp_f'])
			temp_c = int(parsed_json['current_observation']['temp_c'])
			feelslike_f = float(parsed_json['current_observation']['feelslike_f'])
			feelslike_c = float(parsed_json['current_observation']['feelslike_c'])
			wind_string = parsed_json['current_observation']['wind_string']
			weather = parsed_json['current_observation']['weather'].lower()
			try:
				precip = float(parsed_json['current_observation']['precip_1hr_in'])
			except ValueError:
				precip = 0

		# if 'location' in result['outcome']['entities']:
			# TODO: store weather for locations every so often
		# else:
			# TODO: ditto

		# if 'weather' in result['outcome']['entities']:
			# if result['outcome']['entities']['weather']['value'] == "rain":
		loc_str = "in "+loc[1] if loc[1] != "here" else "here"
		if "rain" in result['text']:
			if is_time:
				if pop>60:
					return "Yes, it will definitely be raining at "+hour+"."
				elif pop>40:
					return "Yes, it will probably rain."
				elif pop>15:
					return "It might rain; there's a "+str(pop)+"% chance of rain at "+hour+"."
				else:
					return "No, it will be "+weather+" at "+hour+"."
			else:
				if precip>0.3:
					return "Yes, it's really pouring."
				elif precip>0.1:
					return "Yes, it's raining."
				elif precip>0 or "rain" in weather:
					return "Maybe it's drizzling a little."
				else:
					return "No, it's "+weather+"."
		# elif result['outcome']['entities']['weather']['value'] == 'sun':
		elif 'sun' in result['text']:
			if is_time:
				if "sun" in weather or "clear" in weather:
					if is_day(float(loc[4]),time):
						return "Yes, it will be sunny"+(" "+loc_str+" at "+hour+"." if not here else " at "+hour+".")
					else:
						now = datetime.now()
						return "No, the sun will be down at "+str((now.hour-1)%12+1 if True else now.hour)+":"+str(now.minute).zfill(2)+(" "+loc_str+"." if not here else ".")
				elif "scattered clouds" in weather:
					if is_day(float(loc[4]),time):
						return "Yes, with scattered clouds."
					else:
						return "There will be a few clouds, and it will be night "+loc_str+" at "+hour+"."
				else:
					return "No, the weather "+loc_str+" will be "+weather+" at "+hour+"."
			else:
				if "sun" in weather or "clear" in weather:
					if is_day(float(loc[4])):
						return "Yes, it's sunny "+loc_str+"!"
					else:
						now = datetime.now()
						return "It would be sunny if the sun were still up. It is "+str((now.hour-1)%12+1 if True else now.hour)+":"+str(now.minute).zfill(2)+(" "+loc_str+"." if not here else ".")
				elif "scattered clouds" in weather:
					if is_day(float(loc[4])):
						return "Yes, with scattered clouds."
					else:
						return "There's a few clouds, and it's night "+loc_str+"."
				else:
					return "No, the weather "+loc_str+" is "+weather+"."
		temp = temp_f if config.imperial else temp_c
		feelslike = feelslike_f if config.imperial else feelslike_c
		if 'temperature' in result['outcome']['entities']:
			if result['outcome']['entities']['temperature']['value'] == "cold":
				if is_time:
					if abs(temp_f-feelslike_f)<5:
						if temp_f<40:
							return "Yes, it will be "+str(int(round(temp)))+u("° ")+loc_str+"."
						elif temp_f<60:
							return "It will be sort of cold; the temperature "+loc_str+" is supposed to be "+str(int(round(temp)))+u("°.")
						else:
							return "No, it will be "+str(int(round(temp)))+u("° ")+loc_str+"."
					else:
						if feelslike_f<40:
							return "Yes, it will be "+str(int(round(temp)))+u("° ")+loc_str+" but with the wind chill it will feel like "+str(int(round(feelslike)))+u("°.")
						elif feelslike_f<60:
							return "It will be sort of cold; the temperature "+loc_str+" will be "+str(int(round(temp)))+u("° but it will feel like ")+str(int(round(feelslike)))+u("°.")
						else:
							return "No, it will be "+str(int(round(temp)))+u("° ")+loc_str+" but it will feel like "+str(int(round(feelslike)))+u("°.")
				else:
					if abs(temp_f-feelslike_f)<5:
						if temp_f<40:
							return "Yes, it's "+str(int(round(temp)))+u("° ")+loc_str+"."
						elif temp_f<60:
							return "It's sort of cold; the temperature "+loc_str+" is "+str(int(round(temp)))+u("°.")
						else:
							return "No, it's "+str(int(round(temp)))+u("° ")+loc_str+"."
					else:
						if feelslike_f<40:
							return "Yes, it's "+str(int(round(temp)))+u("° ")+loc_str+" but it feels like "+str(int(round(feelslike)))+u("°.")
						elif feelslike_f<60:
							return "It's sort of cold; the temperature "+loc_str+" is "+str(int(round(temp)))+u("° but it feels like ")+str(int(round(feelslike)))+u("°.")
						else:
							return "No, it's "+str(int(round(temp)))+u("° ")+loc_str+" but it feels like "+str(int(round(feelslike)))+u("°.")
		if is_time:
			return "The weather "+loc_str+" will be "+weather+" and "+str(int(round(temp)))+u("°. at ")+hour+"."
		else:
			return "The weather "+loc_str+" is "+weather+", and "+str(int(round(temp)))+u("°.")
	def call_phone(self, result):
		self.short_term_memory.set('intent','call_phone')
		if 'phone_number' in result['outcome']['entities']:
			num = result['outcome']['entities']['phone_number']['value']
			platform.call_phone(num)
			return "Calling "+num
		elif 'digits' in result['outcome']['entities']:
			num = ''.join([{'zero':'0','oh':'0','naught':'0','one':'1','two':'2','three':'3','four':'4','five':'5','six':'6','seven':'7',
							'eight':'8','nine':'9','ten':'10','eleven':'11','twelve':'12','thirteen':'13','fourteen':'14','fifteen':'15',
							'sixteen':'16','seventeen':'17','eighteen':'18','nineteen':'19','hundred':'00'}[i] for i in result['outcome']['entities']['digits'].split()])
			self.short_term_memory.set('phone_number', num)
			return "Would you like me to call "+num+"?"
		elif 'contact' in result['outcome']['entities']:
			try:
				# platform.call_contact(result['outcome']['entities']['contact'])
				res = platform.check_contact(result['outcome']['entities']['contact'])
				if res:
					self.short_term_memory.set('contact',result['outcome']['entities']['contact'])
			except NameError:
				return "I don't know who "+result['outcome']['entities']['contact']+" is."
			except AttributeError:
				return result['outcome']['entities']['contact']+" doesn't have a phone number."
			return 'Would you like me to call '+result['outcome']['entities']['contact']+"?"
		else:
			return "What number should I call?"
	def yesno(self,result):
		response_is_yes = result['outcome']['entities']['yes_no'] if 'yes_no' in result['outcome']['entities'] else True
		try:
			intent = self.short_term_memory.get('intent')
			if intent=="alarm":
				return "What?"
			elif intent=="call_phone":
				if response_is_yes:
					try:
						call_dest, dest_type = self.short_term_memory.get_more_recent('phone_number','contact')
						if dest_type=='phone_number':
							platform.call_phone(call_dest)
							return "Calling "+call_dest+"."
						elif dest_type=='contact':
							platform.call_contact(call_dest)
							return "Calling "+call_dest+"."
					except:
						return "Sorry, could you repeat that?"
			elif intent=="weather":
				return "Good."
		except ForgottenException:
			return "What are you referring to?"
	def feeling_query(self,result):
		#TODO: feelings?
		return "I am feeling well."
	def time(self, result):
		now = datetime.now()
		if 'location' in result['outcome']['entities']:
			platform.cur.execute("SELECT * FROM Variables WHERE VarName='here'")
			loc = platform.cur.fetchone()
			if loc:
				platform.cur.execute("SELECT * FROM Locations WHERE Id="+str(loc[2]))
				loc = platform.cur.fetchone()
				localOffset = loc[5]
			else:
				platform.cur.execute("SELECT * FROM Variables WHERE VarName='home'")
				loc = platform.cur.fetchone()
				if loc:
					platform.cur.execute("SELECT * FROM Locations WHERE Id="+str(loc[2]))
					loc = platform.cur.fetchone()
					localOffset = loc[5]
				else:
					localOffset = timezone / 60 / 60 * (-1) # time.timezone is measured in seconds West of UTC, whereas everything else uses East of UTC, hence the -1
			location = result['outcome']['entities']['location']
			platform.cur.execute("SELECT * FROM Locations WHERE LocName='"+location+"'")
			loc = platform.cur.fetchone()
			if not loc:
				try:
					req = urllib2.urlopen('http://api.geonames.org/searchJSON?q='+location.replace(" ","+")+'&username=taixzo').read().decode("utf-8")
					locdic = json.loads(req)

					tz = json.loads(urllib2.urlopen('http://api.geonames.org/timezoneJSON?lat='+locdic['geonames'][0]["lat"]+'&lng='+locdic['geonames'][0]["lng"]+'&username=taixzo').read().decode("utf-8"))['rawOffset']
				except:
					return "I don't know where "+location+" is."
				loc = (0,locdic['geonames'][0]["toponymName"],"",locdic['geonames'][0]["lat"],locdic['geonames'][0]["lng"],tz)
			now = now + timedelta(hours=loc[5]-localOffset)
			return "It is "+str((now.hour-1)%12+1 if True else now.hour)+":"+str(now.minute).zfill(2)+" in "+loc[1]+"."
		return "It is "+str((now.hour-1)%12+1 if True else now.hour)+":"+str(now.minute).zfill(2)+"."
	def set_user_name(self, result):
		platform.cur.execute('INSERT OR REPLACE INTO Variables (ID, VarName, Value) VALUES ((SELECT ID FROM Variables WHERE VarName = "userName"), "userName", "'+result['outcome']['entities']['name']+'");')
		platform.conn.commit()
		self.short_term_memory.set('you',{'name':result['outcome']['entities']['name'].capitalize()})
		return "Ok, from now on I'll refer to you as "+result['outcome']['entities']['name']+"."
	def set_sys_name(self, result):
		platform.cur.execute('INSERT OR REPLACE INTO Variables (ID, VarName, Value) VALUES ((SELECT ID FROM Variables WHERE VarName = "sysName"), "sysName", "'+result['outcome']['entities']['name']+'");')
		platform.conn.commit()
		self.short_term_memory.set('I',{'name':result['outcome']['entities']['name'].capitalize()})
		return "Ok, now my name is "+result['outcome']['entities']['name']+"."
	def set_home(self, result):
		# platform.cur.execute('INSERT OR REPLACE INTO Variables (ID, VarName, Value) VALUES ((SELECT ID FROM Variables WHERE VarName = "name"), "name", "'+result['outcome']['entities']['name']+'");')
		# platform.conn.commit()
		# return "Ok, from now on I'll refer to you as "+result['outcome']['entities']['name']
		# loc =
		platform.cur.execute("SELECT * FROM Locations WHERE LocName='"+result['outcome']['entities']['location']+"'")
		locs = platform.cur.fetchall()
		if locs:
			platform.cur.execute('INSERT OR REPLACE INTO Variables (ID, VarName, Value) VALUES ((SELECT ID FROM Variables WHERE VarName = "home"), "home", "'+str(locs[0]['Id'])+'");')
			# return "Ok, you live in "+locs[0]['name']
			platform.conn.commit()
			return "Ok, you live in "+locs[0][1]+"."
		else:
			try:
				req = urllib2.urlopen('http://api.geonames.org/searchJSON?q='+result['outcome']['entities']['location'].replace(" ","+")+'&username=taixzo').read().decode("utf-8")
				# req  = subprocess.Popen(["curl",
										   # 'http://api.geonames.org/searchJSON?q='+location.replace(" ","+")+'&username=taixzo'], stdout=subprocess.PIPE).communicate()[0].decode("utf-8")
				locdic = json.loads(req)
				loc = {'lat':locdic['geonames'][0]["lat"],'lon':locdic['geonames'][0]["lng"],'name':locdic['geonames'][0]["name"],"region":locdic['geonames'][0]["adminName1"]}
				tz = json.loads(urllib2.urlopen('http://api.geonames.org/timezoneJSON?lat='+loc['lat']+'&lng='+loc['lon']+'&username=taixzo').read().decode("utf-8"))['rawOffset']
				try:
					zip = json.loads(urllib2.urlopen('http://api.geonames.org/findNearbyPostalCodesJSON?lat='+loc['lat']+'&lng='+loc['lon']+'&radius=10&username=taixzo').read().decode("utf-8"))["postalCodes"][0]["postalCode"]
				except IndexError:
					zip = ''
				platform.cur.execute('INSERT INTO Locations (LocName, Zip, Latitude, Longitude, Timezone) VALUES ("'+loc['name']+'", "'+zip+'", '+loc['lat']+', '+loc['lon']+', '+str(tz)+')')
				platform.cur.execute('INSERT OR REPLACE INTO Variables (ID, VarName, Value) VALUES ((SELECT ID FROM Variables WHERE VarName = "home"), "home", "'+str(platform.cur.lastrowid)+'");')
				platform.conn.commit()
				return "Ok, you live in "+loc['name']+", "+loc["region"]+"."
			except urllib2.URLError:
				return "I don't know where"+result['outcome']['entities']['location']+" is, sorry."
		return "Where is "+result['outcome']['entities']['location']
	def who_is(self,result):
		conjugations = {'I':'am','you':'are','he':'is','she':'is','it':'is','we':'are','they':'are'}
		if 'posessive_preposition' in result['outcome']['entities']:
			result['outcome']['entities']['preposition'] = {"my":"i","your":"you","his":"he","her":"she","our":"we","their":"they"}[result['outcome']['entities']['posessive_preposition']]
		if 'preposition' in result['outcome']['entities']:
			who = result['outcome']['entities']['preposition']
			who = 'you' if who=='i' else 'I' if who=='you' else who
			if who in self.short_term_memory.items:
				return who.capitalize()+" "+conjugations[who]+" "+' '.join([i.capitalize() for i in self.short_term_memory.get(who)['name'].split(' ')])+"."
			else:
				if who is "you":
					platform.cur.execute("SELECT * FROM Variables WHERE VarName='userName'")
					name = platform.cur.fetchone()
					if name:
						return who.capitalize()+" "+conjugations[who]+" "+' '.join([i.capitalize() for i in name[2].split(' ')])+"."
					else:
						return "I don't know. What is your name?"
				elif who is "I":
					platform.cur.execute("SELECT * FROM Variables WHERE VarName='sysName'")
					name = platform.cur.fetchone()
					if name:
						return who.capitalize()+" "+conjugations[who]+" "+' '.join([i.capitalize() for i in name[2].split(' ')])+"."
					else:
						return "I am Saera."
			return who+" is whoever "+who+" is."
		elif 'name' in result['outcome']['entities']:
			who = result['outcome']['entities']['name']
			try:
				person = self.short_term_memory.get(who)
			except ForgottenException:
				platform.cur.execute("SELECT * FROM People WHERE Name='"+who+"'")
				res = platform.cur.fetchone()
				if res:
					person = {'name':res[1],'description':res[2],'born':res[3],'died':res[4],'gender':res[5],'profession':res[6]}
				else:
					try:
						req = json.loads(urllib2.urlopen("https://www.wikidata.org/w/api.php?action=wbsearchentities&search="+who.replace(" ","%20")+"&language=en&format=json").read().decode("utf-8"))
						if req['search']:
							genders = {6581097:'male',6581072:'female'}
							wikidataid = req['search'][0]['id']
							req = json.loads(urllib2.urlopen("https://www.wikidata.org/wiki/Special:EntityData/"+wikidataid+".json").read().decode("utf-8"))
							person = {	'name':req['entities'][wikidataid]['labels']['en']['value'],
										'description':req['entities'][wikidataid]['descriptions']['en']['value'],
										'born':req['entities'][wikidataid]['claims']['P569'][0]['mainsnak']['datavalue']['value']['time'] if 'P569' in req['entities'][wikidataid]['claims'] else None,
										'died':None,
										'profession':None,
										'gender':genders[req['entities'][wikidataid]['claims']['P21'][0]['mainsnak']['datavalue']['value']['numeric-id']] if req['entities'][wikidataid]['claims']['P21'][0]['mainsnak']['datavalue']['value']['numeric-id'] in genders else 'other'
										}
							platform.cur.execute('INSERT OR REPLACE INTO People (ID, Name, Description, Born, Died, Gender, Profession) VALUES ((SELECT ID FROM People WHERE Name = "'+person['name']+'"), "'+person['name']+'", "'+person['description']+'", "'+(person['born'] or 'NULL')+'","'+(person['died'] or 'NULL')+'","'+person['gender']+'",NULL);')
							platform.conn.commit()
						else:
							return "I don't know who "+who+" is."
					except:
						return "I don't know who "+who+" is, and I can't look it up without an internet connection."
			pronoun = 'he' if person["gender"] == "male" else 'she' if person["gender"] == "female" else 'it'
			self.short_term_memory.set(pronoun,person)
			return pronoun.capitalize() + " " + conjugations[pronoun] + " " + ("a " if not (person['description'].lower().startswith("the ") or person['description'].lower().startswith("a ") or person['description'].lower().startswith("an ")) else "") + person["description"][0].upper()+person["description"][1:]+'.'
		else:
			return "What?"
	def email(self,result):
		messages = platform.get_unread_email()
		if not messages:
			return "You have no new mail."
		elif len(messages) == 1:
			self.short_term_memory.set('object',messages[0])
			if "read " in result['text'].lower():
				return "From "+messages[0]['from']+". "+messages[0]['subject']+". Message: "+messages[0]['message']
			return "You have a new email from "+messages[0]['from']
		else:
			print (result['text'])
			self.short_term_memory.set('plural_object',messages)
			if "read " in result['text'].lower():
				retstr = ''
				for message in messages:
					retstr += "From "+message['from']+".\n"+message['subject']+".\n\n"
				return retstr
			return "You have "+str(len(messages))+" new email messages."
	def reminder(self,result):
		print (result)
		if 'do_action' in result['outcome']['entities']:
			reminder = (" "+result['outcome']['entities']['do_action']+" ").replace(" my "," your^ ").replace(" me "," you^ ").replace(" you "," me^ ").replace(" your "," my ").replace("^","").strip()
			if 'time' in result['outcome']['entities']:
				platform.set_reminder(result['outcome']['entities']['time'],reminder)
				return 'I will remind you to '+reminder+' at '+result['outcome']['entities']['time'].strftime("%H:%M.")
			else:
				return "When should I remind you to "+reminder+"?"
		else:
			return 'No idea what to remind you of'
	def read_out(self,result):
		if "them" in result['text'].split():
			try:
				thingsToRead = self.short_term_memory.get('plural_object')
				if thingsToRead[0]['type']=='email':
					retstr = ''
					for message in thingsToRead:
						retstr += "From "+message['from']+".\n"+message['subject']+"."+message['content']+"\n\n"
					return retstr
			except ForgottenException:
				return (" "+result['text']+" ").replace(" them "," what ").strip()+"?"
		elif "it" in result['text'].split():
			try:
				thingToRead = self.short_term_memory.get('object')
				if thingToRead['type']=='email':
					return "From "+messages[0]['from']+". "+messages[0]['subject']+". Message: "+messages[0]['message']
			except ForgottenException:
				return (" "+result.text+" ").replace(" it "," what ").strip()+"?"
	def search (self,result):
		try:
			if 'search_engine' in result['outcome']['entities']:
				search_engine = result['outcome']['entities']['search_engine']
			else:
				search_engine = "google"
			if search_engine=="google":
				search = pygoogle.pygoogle( log_level=log_level, query=result['outcome']['entities']['query'], pages=1, hl='en')
				return [("I found these results:",)]+list(search.search().items())
			elif search_engine=="wikipedia":
				try:
					return [wikikit.summary(result['outcome']['entities']['query'],sentences=1)]
				except KeyError:
					return "Wikipedia doesn't have an entry for "+result['outcome']['entities']['query']+"."
			elif search_engine=="duckduckgo" or search_engine=="duck duck go" or search_engine=="duck go":
				# r = duckduckgo.query(result['outcome']['entities']['query'])
				return duckduckgo.get_zci(result['outcome']['entities']['query'])
			return "I don't know how to search  "+search_engine+"."
		except:
			return "I need an internet connection to search "+search_engine+" for "+result['outcome']['entities']['query']+"."
	def traffic(self, result):
		if 'location' in result['outcome']['entities']:
			location = result['outcome']['entities']['location']
			platform.cur.execute("SELECT * FROM Locations WHERE LocName='"+location+"'")
			loc = platform.cur.fetchone()
			if not loc:
				try:
					req = urllib2.urlopen('http://api.geonames.org/searchJSON?q='+location.replace(" ","+")+'&username=taixzo').read().decode("utf-8")
					locdic = json.loads(req)
					loc = (0,locdic['geonames'][0]["toponymName"],"",locdic['geonames'][0]["lat"],locdic['geonames'][0]["lng"])
					tz = json.loads(urllib2.urlopen('http://api.geonames.org/timezoneJSON?lat='+locdic['geonames'][0]["lat"]+'&lng='+locdic['geonames'][0]["lng"]+'&username=taixzo').read().decode("utf-8"))['rawOffset']
				except:
					return "I need an internet connection to check the traffic, sorry."
				platform.cur.execute('INSERT INTO Locations (LocName, Zip, Latitude, Longitude, Timezone) VALUES ("'+loc[1]+'", "", '+loc[3]+', '+loc[4]+', '+str(tz)+')')
				platform.conn.commit()
			if 'on the way' in result['text']:
				platform.cur.execute("SELECT * FROM Variables WHERE VarName='here'")
				here = platform.cur.fetchone()
				if here:
					platform.cur.execute("SELECT * FROM Locations WHERE Id="+str(here[2]))
					here = platform.cur.fetchone()
				else:
					platform.cur.execute("SELECT * FROM Variables WHERE VarName='home'")
					here = platform.cur.fetchone()
					if here:
						platform.cur.execute("SELECT * FROM Locations WHERE Id="+str(here[2]))
						here = platform.cur.fetchone()
					else:
						return "Where do you live?"
				try:
					routeinfo = json.loads(urllib2.urlopen("http://dev.virtualearth.net/REST/V1/Routes/Driving?wp.0="+str(here[4])+","+str(here[3])+"%2Cwa&wp.1="+loc[1].replace(" ","%20")+"&avoid=minimizeTolls&key=AltIdRJ4KAV9d1U-rE3T0E-OFN66cwd3D1USLS28oVl2lbIRbFcqMZHJZd5DwTTP").read().decode("utf-8"))
				except:
					return "I need an internet connection to check the traffic, sorry."
				travelDuration = routeinfo['resourceSets'][0]['resources'][0]['travelDuration']
				travelDurationTraffic = routeinfo['resourceSets'][0]['resources'][0]['travelDurationTraffic']
				trafficCongestion = routeinfo['resourceSets'][0]['resources'][0]['trafficCongestion']
				if float(travelDuration)/travelDurationTraffic>0.9:
					return "There isn't much traffic between here and "+loc[1]+"."
				elif float(travelDuration)/travelDurationTraffic>0.7:
					return "There's some traffic between here and "+loc[1]+"; expect to be delayed about "+str(int((travelDurationTraffic-travelDuration)/60))+" minutes."
					return "There isn't much traffic between here and "+loc[1]+"."
				elif float(travelDuration)/travelDurationTraffic>0.5:
					return "There's quite a bit of traffic between here and "+loc[1]+"; expect to be delayed about "+str(int((travelDurationTraffic-travelDuration)/60))+" minutes."
				else:
					return "There is heavy congestion. It will take about "+(str(travelDurationTraffic/3600)+" hours" if travelDurationTraffic>5400 else str(travelDurationTraffic/60) + " minutes") + " to reach "+loc[1]+"."
		else:
			platform.cur.execute("SELECT * FROM Variables WHERE VarName='here'")
			loc = platform.cur.fetchone()
			if loc:
				platform.cur.execute("SELECT * FROM Locations WHERE Id="+str(loc[2]))
				loc = platform.cur.fetchone()
				here = True
			else:
				platform.cur.execute("SELECT * FROM Variables WHERE VarName='home'")
				loc = platform.cur.fetchone()
				if loc:
					platform.cur.execute("SELECT * FROM Locations WHERE Id="+str(loc[2]))
					loc = platform.cur.fetchone()
					here = True
				else:
					return "Where do you live?"
		bb = (float(loc[3])-.25,float(loc[4])-.25,float(loc[3])+.25,float(loc[4])+.25)
		try:
			trafficdata = json.loads(urllib2.urlopen("http://dev.virtualearth.net/REST/v1/Traffic/Incidents/"+str(bb[0])+","+str(bb[1])+","+str(bb[2])+","+str(bb[3])+"?key=AltIdRJ4KAV9d1U-rE3T0E-OFN66cwd3D1USLS28oVl2lbIRbFcqMZHJZd5DwTTP").read().decode("utf-8"))
		except:
			return "I need an internet connection to check the traffic." # Would you like me to check next time I have a connection?"
		print (trafficdata['resourceSets'][0])
		retmsg = "There "+(('are '+str(trafficdata['resourceSets'][0]['estimatedTotal'])+' ').replace(' 0 ',' no ')+'traffic incidents ').replace('are 1 traffic incidents ','is 1 traffic incident ')+("in the "+loc[1]+" area." if loc[1] != "here" else "around here.")
		if trafficdata['resourceSets'][0]['estimatedTotal']<10:
			lists = []
			for i in trafficdata['resourceSets'][0]['resources']:
				if ' between ' in i['description'].lower() and ' and ' in i['description']:
					endpoints = (i['description'].lower().split(' - ')[0].split(' between ')[1].split(' and '))
					if tuple(reversed(endpoints)) in lists:
						continue
					else:
						lists.append(endpoints)
				retmsg+="\n"+i['description']
		return retmsg
	def directions(self, result):
		global direction_list
		print (result)
		platform.cur.execute("SELECT * FROM Variables WHERE VarName='here'")
		here = platform.cur.fetchone()
		if here:
			platform.cur.execute("SELECT * FROM Locations WHERE Id="+str(here[2]))
			here = platform.cur.fetchone()
		else:
			platform.cur.execute("SELECT * FROM Variables WHERE VarName='home'")
			here = platform.cur.fetchone()
			if here:
				platform.cur.execute("SELECT * FROM Locations WHERE Id="+str(here[2]))
				here = platform.cur.fetchone()
			else:
				return "Where do you live?"
		if 'location' in result['outcome']['entities']:
			platform.sayRich("", "One moment...","")
			location = result['outcome']['entities']['location']
			platform.cur.execute("SELECT * FROM Locations WHERE LocName='"+location+"'")
			loc = platform.cur.fetchone()
			if not loc:
				# req = urllib2.urlopen('https://graphhopper.com/api/1/geocode?q='+location.replace(' ','%20')+'&point='+str(here[3])+','+str(here[4])+'&key=d5365874-1efe-4f12-92ee-5757f82041fe').read().decode("utf-8")
				# locdic = json.loads(req)
				# loc = (0,locdic['hits'][0]["name"],"",locdic['hits'][0]["point"]["lat"],locdic['hits'][0]["point"]["lng"])
				try:
					req = urllib2.urlopen('https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyBUI3LwzSUmm3cI8-nEMGrQYAzs6VWFIfg&address='+location.replace(' ','+')+'&bounds='+str(float(here[3])-0.1)+','+str(float(here[4])-0.1)+'|'+str(float(here[3])+0.1)+','+str(float(here[4])+0.1)+'').read().decode("utf-8")
				except:
					return "I can't look up directions without an internet connection, sorry."
				locdic = json.loads(req)
				loc = (0,' '.join([i["long_name"] for i in locdic['results'][0]['address_components'] if i['types'][0] not in ('country','postal','postal_code_suffix','administrative_area_level_2','neighborhood')]),"",locdic['results'][0]["geometry"]["location"]["lat"],locdic['results'][0]["geometry"]["location"]["lng"])

				print (loc)
			try:
				req = urllib2.urlopen("https://graphhopper.com/api/1/route?point="+str(here[3])+","+str(here[4])+"&point="+str(loc[3])+","+str(loc[4])+"&vehicle=car&points_encoded=true&calc_points=true&key=d5365874-1efe-4f12-92ee-5757f82041fe").read().decode("utf-8")
			except:
				return "I can't look up directions without an internet connection, sorry."
			pathdic = json.loads(req)
			path = decodePath(pathdic['paths'][0]['points'], False)
			print (path)
			instructions = pathdic['paths'][0]['instructions']
			for index, instruction in enumerate(instructions):
				# point = path[int((instruction['interval'][0]+instruction['interval'][1])/2)]
				point = path[instruction['interval'][0]]
				instruction['point'] = point
				print (instruction['text'], 'at', point)
			instructions = [{'text':'Start','point':instructions[0]['point'],'distance':0}] + instructions
			platform.enablePTP()
			direction_list = instructions
			total_distance = int(round(pathdic['paths'][0]['distance']*0.000621371))
			return "Ok, "+loc[1]+" is "+(str(total_distance)+" mile"+("s" if total_distance != 1 else "") if total_distance >= 1 else "less than a mile") + " away. It will take about "+formatTime(pathdic['paths'][0]['time']/1000)+"."
		return "No."
	def coin_flip(self,result):
		if 'number' in result['outcome']['entities'] and result['outcome']['entities']['number']>1:
			coins = []
			for i in range(result['outcome']['entities']['number']):
				coins.append(round(random.random()))
			heads = sum(coins)
			if heads==len(coins):
				return "I flipped "+str(result['outcome']['entities']['number'])+" coins. They're all heads."
			elif heads==0:
				return "I flipped "+str(result['outcome']['entities']['number'])+" coins. They're all tails."
			else:
				return "I flipped "+str(result['outcome']['entities']['number'])+" coins. "+str(int(heads))+" were heads and "+str(int(len(coins)-heads))+" were tails."
		else:
			if random.random()>0.5:
				return "It's heads."
			else:
				return "It's tails."
	def roll_dice(self,result):
		if 'dice' in result['outcome']['entities'] and result['outcome']['entities']['dice']>1:
			if 'number' in result['outcome']['entities'] and result['outcome']['entities']['number']>1:
				rolls = [random.randint(1,result['outcome']['entities']['dice']) for i in range(result['outcome']['entities']['number'])]
				return "I rolled a "+", a ".join([str(i) for i in rolls[:-1]])+", and a "+str(rolls[-1])+", for a total of "+str(sum(rolls))+"."
			else:
				roll = random.randint(1,result['outcome']['entities']['dice'])
				return "I rolled a "+str(result['outcome']['entities']['dice'])+"-sided die, which came up "+str(roll)+"."
		elif 'number' in result['outcome']['entities'] and result['outcome']['entities']['number']>1:
			roll = random.randint(1,result['outcome']['entities']['number'])
			return "I rolled a "+str(result['outcome']['entities']['number'])+"-sided die, which came up "+str(roll)+"."
		else:
			if " pair " in result['text']:
				rolls = [random.randint(1,6) for i in range(2)]
				return "I rolled a pair of dice. They came up "+str(rolls[0])+" and "+str(rolls[1])+" for a total of "+str(sum(rolls))+"."
			roll = random.randint(1,6)
			return "I rolled a six-sided die, which came up "+str(roll)+"."
	def play(self, result):
		print(result)
		if 'song' in result['outcome']['entities']:
			platform.play(result['outcome']['entities']['song'].lower())
			return "Ok!"
		else:
			p = platform.is_playing()
			if p=="Paused" or p=="Stopped" or p=="Off":
				platform.play()
				return "Done!"
			elif p=="Playing":
				return "Already playing!"
			else:
				return "Play what?"
	def search_local_business(self, result):
		if result['outcome']['intent']=="food":
			keyword = "food"
		if 'location' in result['outcome']['entities']:
			location = result['outcome']['entities']['location']
			platform.cur.execute("SELECT * FROM Locations WHERE LocName='"+location+"'")
			loc = platform.cur.fetchone()
			if not loc:
				try:
					req = urllib2.urlopen('http://api.geonames.org/searchJSON?q='+location.replace(" ","+")+'&username=taixzo').read().decode("utf-8")
				except:
					return "I don't know where "+location+" is, sorry."
				locdic = json.loads(req)
				loc = (0,locdic['geonames'][0]["toponymName"],"",locdic['geonames'][0]["lat"],locdic['geonames'][0]["lng"])
				try:
					tz = json.loads(urllib2.urlopen('http://api.geonames.org/timezoneJSON?lat='+locdic['geonames'][0]["lat"]+'&lng='+locdic['geonames'][0]["lng"]+'&username=taixzo').read().decode("utf-8"))['rawOffset']
				except:
					return "I don't know where "+location+" is, sorry."
				platform.cur.execute('INSERT INTO Locations (LocName, Zip, Latitude, Longitude, Timezone) VALUES ("'+loc[1]+'", "", '+loc[3]+', '+loc[4]+', '+str(tz)+')')
				platform.conn.commit()
		else:
			platform.cur.execute("SELECT * FROM Variables WHERE VarName='here'")
			loc = platform.cur.fetchone()
			if loc:
				platform.cur.execute("SELECT * FROM Locations WHERE Id="+str(loc[2]))
				loc = platform.cur.fetchone()
				here = True
			else:
				platform.cur.execute("SELECT * FROM Variables WHERE VarName='home'")
				loc = platform.cur.fetchone()
				if loc:
					platform.cur.execute("SELECT * FROM Locations WHERE Id="+str(loc[2]))
					loc = platform.cur.fetchone()
					here = True
				else:
					return "Where do you live?"
		req = urllib2.urlopen('https://maps.googleapis.com/maps/api/place/nearbysearch/json?key=AIzaSyBUI3LwzSUmm3cI8-nEMGrQYAzs6VWFIfg&location='+str(loc[3])+','+str(loc[4])+'&rankby=distance&keyword='+keyword).read().decode('utf-8')
		places = json.loads(req)
		if len(places['results'])==1:
			return places['results'][0]['name']+" is "+formatDistance(geo_distance(loc[3],loc[4],places['results'][0]['geometry']['location']['lat'],places['results'][0]['geometry']['location']['lng']))+" away."
		retstr = "I found these results. The closest one is "+places['results'][0]['name']+", which is "+formatDistance(geo_distance(loc[3],loc[4],places['results'][0]['geometry']['location']['lat'],places['results'][0]['geometry']['location']['lng']))+" away."
		retstr += "|destinations"
		for destination in places['results'][:5]:
			retstr+="|"+destination['name']+'^'+str(destination['geometry']['location']['lat'])+','+str(destination['geometry']['location']['lng'])+'^'+str(destination['opening_hours']['open_now'] if 'opening_hours' in destination else None)
		return retstr
	def help(self):
		return """Here are some things you could ask me:
	What is the time in Tokyo?
	Will it rain this afternoon?
	What song is this?
	Play music.
	Call John Smith.
	Wake me at eight.
	Directions to 123 Main Street."""
	def process(self,result):
		print (result['outcome']['intent'])
		self.short_term_memory.tick()
		if result['outcome']['intent']=='hello' or result['outcome']['intent']=='greetings':
			return self.hello(result)
		elif result['outcome']['intent']=='alarm':
			return self.set_alarm(result)
		elif result['outcome']['intent']=='reminder':
			return self.reminder(result)
		elif result['outcome']['intent']=="weather":
			return self.weather(result)
		elif result['outcome']['intent']=="time":
			return self.time(result)
		elif result['outcome']['intent']=="test":
			return "Test successful."
		elif result['outcome']['intent']=="pause":
			p = platform.is_playing()
			if p=="Playing":
				platform.pause()
				return "Done!"
			elif p=="Paused":
				return "It's already paused."
			else:
				return "Nothing is playing."
		elif result['outcome']['intent']=="play":
			return self.play(result)

		elif result['outcome']['intent']=="email":
			return self.email(result)
		elif result['outcome']['intent']=="call":
			return self.call_phone(result)
		elif result['outcome']['intent']=="how_about":
			print (result)
			try:
				if self.short_term_memory.get('intent')=='alarm':
					return self.set_alarm(result)
				elif self.short_term_memory.get('intent')=='weather':
					return self.weather(result)
				else:
					return "I'm sorry, what were we talking about?"
			except ForgottenException:
				return "I'm sorry, what were we talking about?"

		elif result['outcome']['intent']=="yes_no":
			return self.yesno(result)
		elif result['outcome']['intent']=="feeling_query":
			return self.feeling_query(result)
		elif result['outcome']['intent']=='read_out':
			return self.read_out(result)
		elif result['outcome']['intent']=="set_user_name":
			return self.set_user_name(result)
		elif result['outcome']['intent']=="set_sys_name":
			return self.set_sys_name(result)
		elif result['outcome']['intent']=="set_home":
			return self.set_home(result)
		elif result['outcome']['intent']=="who_is":
			return self.who_is(result)
		elif result['outcome']['intent']=="search":
			return self.search(result)
		elif result['outcome']['intent']=="traffic":
			return self.traffic(result)
		elif result['outcome']['intent']=="directions":
			return self.directions(result)
		elif result['outcome']['intent']=="coin_flip":
			return self.coin_flip(result)
		elif result['outcome']['intent']=="roll_dice":
			return self.roll_dice(result)
		elif result['outcome']['intent']=="get_song":
			return platform.identify_song()
		elif result['outcome']['intent']=="food":
			return self.search_local_business(result)
		elif result['outcome']['intent']=="cancel":
			global direction_list
			if direction_list != []:
				direction_list = []
				platform.disablePTP()
				return "Canceled navigation."
			else:
				return "Cancel what?"
		elif result['outcome']['intent']=="mumble":
			return "Sorry, I didn't understand that."
		elif result['outcome']['intent']=="quit" or result['outcome']['intent']=="good_bye":
			# sys.exit(0)
			platform.quit()
		elif result['outcome']['intent']=="restart":
			platform.restart()
		elif result['outcome']['intent']=="help":
			return self.help()
		else:
			print (result)

def initialize():
	s = Saera()
	platform.run_app(s)

def quit():
	platform.quit()

def run_text(t):
	return platform.speak(platform.app.execute_text(t))

def run_voice():
	return platform.listen()

def run_processed_text(t):
	return platform.app.process(json.loads(t))

def pause_daemons():
	if not platform.app:
		return ""
	return platform.pause_daemons()

def resume_daemons():
	if not platform.app:
		return ""
	return platform.resume_daemons()

def set_position(lat, lon):
	global direction_list
	# platform.cur.execute('INSERT INTO Locations (LocName, Zip, Latitude, Longitude, Timezone) VALUES ("here", "", '+str(lat)+', '+str(lon)+', 0)')
	platform.cur.execute('INSERT OR REPLACE INTO Locations (ID, LocName, Zip, Latitude, Longitude, Timezone) VALUES ((SELECT ID FROM Locations WHERE LocName = "here"), "here", "", '+str(lat)+', '+str(lon)+', 0)')
	platform.cur.execute('INSERT OR REPLACE INTO Variables (ID, VarName, Value) VALUES ((SELECT ID FROM Variables WHERE VarName = "here"), "here", "'+str(platform.cur.lastrowid)+'");')
	platform.cur.execute('INSERT INTO LocationLogs (Latitude, Longitude) VALUES ('+str(lat)+','+str(lon)+')')
	platform.conn.commit()

	if direction_list != []:
		# if abs(lat-direction_list[0]['point'][1])<0.001 and abs(lon-direction_list[0]['point'][0])<0.013:
		print (geo_distance(lat, lon, direction_list[0]['point'][1], direction_list[0]['point'][0]))
		if geo_distance(lat, lon, direction_list[0]['point'][1], direction_list[0]['point'][0])<75:
		# if True:
			print (direction_list[0])
			platform.speak(direction_list[0]['text'])
			sleep(10)
			if len(direction_list)>1:
				if direction_list[0]['text'] == "Start":
					if direction_list[1]['point'][1]>lat:
						if direction_list[1]['point'][1]-lat>abs(direction_list[1]['point'][0]-lon):
							compass_dir = "north"
						elif direction_list[1]['point'][0]>lon:
							compass_dir = "east"
						else:
							compass_dir = "west"
					else:
						if lat-direction_list[1]['point'][1]>abs(direction_list[1]['point'][0]-lon):
							compass_dir = "south"
						elif direction_list[1]['point'][0]>lon:
							compass_dir = "east"
						else:
							compass_dir = "west"
					tex = "Head "+compass_dir+(" on " + direction_list[1]['text'].split(" onto ")[-1]+"." if " onto " in direction_list[1]['text'] else ".")
					platform.sayRich(tex, tex, 4)
				else:
					platform.sayRich("In "+formatDistance(direction_list[0]['distance'])+", "+direction_list[1]['text'], direction_list[1]['text'],direction_list[1]['sign'], direction_list[1]['point'][1], direction_list[1]['point'][0])
				direction_list = direction_list[1:]
			else:
				direction_list = []
				platform.disablePTP()

def activate():
	if not platform.app:
		return ""
	if datetime.now().hour<5:
		return ""
	platform.cur.execute("SELECT * FROM Variables WHERE VarName='last_activated'")
	row = platform.cur.fetchone()
	platform.cur.execute('INSERT OR REPLACE INTO Variables (ID, VarName, Value) VALUES ((SELECT ID FROM Variables WHERE VarName = "last_activated"), "last_activated", "'+datetime.now().isoformat()+'");')
	platform.conn.commit()
	if row and datetime.strptime( row["Value"], "%Y-%m-%dT%H:%M:%S.%f" ).date()>=datetime.now().date():
		return ""
	else:
		return platform.speak("Good morning! "+platform.app.weather({'outcome':{'entities':{}},'text':''}) )

def check_can_listen():
	return platform.check_can_listen()

def cancel_listening():
	return platform.cancel_listening()

def play_url(url):
	return platform.play_url(url)

if __name__=="__main__":
	initialize()
