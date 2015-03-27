#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import pyotherside

from datetime import datetime, time, timedelta
import calendar
import re
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
import subprocess

from guessing import Guesser

#import fremantle_hw as platform
#import harmattan_hw as platform
# import x86_hw as platform
# import sailfish_hw as platform
import cmd_hw as platform

# if not os.path.exists(platform.memory_path):

# 	data = {'username':None}

if sys.version < '3':
	import codecs
	def u(x):
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
	def tick(self):
		if self.forgettable:
			for i in list(self.items):
				self.items[i][1]-=1
				if self.items[i][1]<0:
					del self.items[i]


import math, sys

def is_day(lon):
	sin,cos,pi = math.sin,math.cos,math.pi
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
	print solar_time
	return solar_time.hour<12

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
		result = self.guesser.guess(string)
		print result
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
			return "Hello, "+row['Value']
		except ForgottenException:
			return "Hello!"
	def set_alarm(self,result):
		self.short_term_memory.set('intent','alarm',2)
		if 'time' in result['outcome']['entities']:
			# alarm_time = datetime.strptime(result['outcome']['entities']['time']['value']['from'][:-6], "%Y-%m-%dT%H:%M:%S.%f")
			alarm_time = result['outcome']['entities']['time']
			platform.set_alarm(calendar.timegm(alarm_time.utctimetuple()))
			self.short_term_memory.set('time',alarm_time)
			return "Setting alarm for "+str(alarm_time.hour)+":"+'{0:02d}'.format(alarm_time.minute)+"."
		elif 'location' in result['outcome']['entities']:
			location = result['outcome']['entities']['location']['value']
			# TODO: location alarms
			return "Ok, I'll wake you when you get to "+location+"."
		else:
			try:
				alarm_time = self.short_term_memory.get('time')
				platform.set_alarm(calendar.timegm(alarm_time.utctimetuple()))
				return "Setting alarm for "+str(alarm_time.hour)+":"+'{0:02d}'.format(alarm_time.minute)
			except ForgottenException:
				return "What time do you want the alarm set for?"
	def weather(self,result):
		self.short_term_memory.set('intent','weather')
		here = False
		if 'location' in result['outcome']['entities']:
			location = result['outcome']['entities']['location']
			platform.cur.execute("SELECT * FROM Locations WHERE LocName='"+location+"'")
			loc = platform.cur.fetchone()
			if not loc:
				# How to convert a generalized location to a city??
				# For some idiotic reson, this segfaults under SailfishOS. Return of the cUrl!
				req = urllib2.urlopen('http://api.geonames.org/searchJSON?q='+location.replace(" ","+")+'&username=taixzo').read().decode("utf-8")
				# req  = subprocess.Popen(["curl",
										   # 'http://api.geonames.org/searchJSON?q='+location.replace(" ","+")+'&username=taixzo'], stdout=subprocess.PIPE).communicate()[0].decode("utf-8")
				locdic = json.loads(req)
				loc = (0,locdic['geonames'][0]["toponymName"],"",locdic['geonames'][0]["lat"],locdic['geonames'][0]["lng"])
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
			print loc
			f = urllib2.urlopen('http://api.wunderground.com/api/0a02b434d9bf118f/geolookup/conditions/q/'+str(loc[3])+','+str(loc[4])+'.json').read()
			# DAMMIT SAILFISH WHY DO YOU HATE THE INTERNET
			# req  = subprocess.Popen(["curl",
									   # 'http://api.wunderground.com/api/0a02b434d9bf118f/geolookup/conditions/q/'+loc[0]+','+loc[1]+'.json'], stdout=subprocess.PIPE).communicate()[0]
		except urllib2.URLError:
			return "I need an internet connection to look up the weather, sorry."
		json_string = f.decode("utf-8")
		parsed_json = json.loads(json_string)
		location = parsed_json['location']['city']
		temp_f = parsed_json['current_observation']['temp_f']
		feelslike_f = float(parsed_json['current_observation']['feelslike_f'])
		wind_string = parsed_json['current_observation']['wind_string']
		try:
			precip = float(parsed_json['current_observation']['precip_1hr_in'])
		except ValueError:
			precip = 0
		weather = parsed_json['current_observation']['weather'].lower()
		# if 'weather' in result['outcome']['entities']:
			# if result['outcome']['entities']['weather']['value'] == "rain":
		if "rain" in result['text']:
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
			if "sun" in weather or "clear" in weather:
				print loc[4]
				if is_day(float(loc[4])):
					return "Yes, it's sunny in "+loc[1]+"!"
				else:
					now = datetime.now()
					return "It would be sunny if the sun were still up. It is "+str((now.hour-1)%12+1 if True else now.hour)+":"+str(now.minute).zfill(2)+(" in "+loc[1]+"." if not here else ".")
			elif "scattered clouds" in weather:
				if is_day(float(loc[1])):
					return "Yes, with scattered clouds."
				else:
					return "There's a few clouds, and it's night in "+loc[1]+"."
			else:
				return "No, the weather in "+loc[1]+" is "+weather+"."
		if 'temperature' in result['outcome']['entities']:
			if result['outcome']['entities']['temperature']['value'] == "cold":
				if abs(temp_f-feelslike_f)<5:
					if temp_f<40:
						return "Yes, it's "+str(int(round(temp_f)))+u("° in ")+loc[1]+"."
					elif temp_f<60:
						return "It's sort of cold; the temperature in "+loc[1]+" is "+str(int(round(temp_f)))+u("°.")
					else:
						return "No, it's "+str(int(round(temp_f)))+u("° in ")+loc[1]+"."
				else:
					if feelslike_f<40:
						return "Yes, it's "+str(int(round(temp_f)))+u("° in ")+loc[1]+" but it feels like "+str(int(round(feelslike_f)))+u("°.")
					elif feelslike_f<60:
						return "It's sort of cold; the temperature in "+loc[1]+" is "+str(int(round(temp_f)))+u("° but it feels like ")+str(int(round(feelslike_f)))+u("°.")
					else:
						return "No, it's "+str(int(round(temp_f)))+u("° in ")+loc[1]+" but it feels like "+str(int(round(feelslike_f)))+u("°.")
		return "The weather in "+loc[1]+" is "+weather+", and "+str(int(round(temp_f)))+u("°.")
	def call_phone(self, result):
		if 'phone_number' in result['outcome']['entities']:
			num = result['outcome']['entities']['phone_number']['value']
			platform.call_phone(num)
			return "Calling "+num
		elif 'digit' in result['outcome']['entities']:
			num = ''.join([{'zero':'0','oh':'0','naught':'0','one':'1','two':'2','three':'3','four':'4','five':'5','six':'6','seven':'7',
							'eight':'8','nine':'9','ten':'10','eleven':'11','twelve':'12','thirteen':'13','fourteen':'14','fifteen':'15',
							'sixteen':'16','seventeen':'17','eighteen':'18','nineteen':'19','hundred':'00'}[i['value']] for i in result['outcome']['entities']['digit']])
			platform.call_phone(num)
			return "Calling "+num
		else:
			return "What number should I call?"
	def yesno(self,result):
		try:
			intent = self.short_term_memory.get('intent')
			if intent=="alarm":
				return "What?"
			elif intent=="weather":
				return "Good."
		except ForgottenException:
			return "What are you referring to?"
	def time(self, result):
		now = datetime.now()
		return "It is "+str((now.hour-1)%12+1 if True else now.hour)+":"+str(now.minute).zfill(2)
	def set_name(self, result):
		platform.cur.execute('INSERT OR REPLACE INTO Variables (ID, VarName, Value) VALUES ((SELECT ID FROM Variables WHERE VarName = "name"), "name", "'+result['outcome']['entities']['name']+'");')
		platform.conn.commit()
		return "Ok, from now on I'll refer to you as "+result['outcome']['entities']['name']
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
				zip = json.loads(urllib2.urlopen('http://api.geonames.org/findNearbyPostalCodesJSON?lat='+loc['lat']+'&lng='+loc['lon']+'&radius=10&username=taixzo').read().decode("utf-8"))["postalCodes"][0]["postalCode"]
				platform.cur.execute('INSERT INTO Locations (LocName, Zip, Latitude, Longitude, Timezone) VALUES ("'+loc['name']+'", "'+zip+'", '+loc['lat']+', '+loc['lon']+', '+str(tz)+')')
				platform.cur.execute('INSERT OR REPLACE INTO Variables (ID, VarName, Value) VALUES ((SELECT ID FROM Variables WHERE VarName = "home"), "home", "'+str(platform.cur.lastrowid)+'");')
				platform.conn.commit()
				return "Ok, you live in "+loc['name']+", "+loc["region"]+"."
			except urllib2.URLError:
				return "I need an internet connection to look up the weather, sorry."
		return "Where is "+result['outcome']['entities']['location']
	def process(self,result):
		print (result['outcome']['intent'])
		self.short_term_memory.tick()
		if result['outcome']['intent']=='hello' or result['outcome']['intent']=='greetings':
			return self.hello(result)
		elif result['outcome']['intent']=='alarm':
			return self.set_alarm(result)
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
			p = platform.is_playing()
			if p=="Paused":
				platform.play()
				return "Done!"
			elif p=="Playing":
				return "Already playing!"
			else:
				return "Play what?"
		elif result['outcome']['intent']=="email":
			pass
		elif result['outcome']['intent']=="call":
			return self.call_phone(result)
		elif result['outcome']['intent']=="how_about":
			if self.short_term_memory.get('intent')=='alarm':
				return self.set_alarm(result)
			elif self.short_term_memory.get('intent')=='weather':
				return self.weather(result)
			else:
				return "I'm sorry, what were we talking about?"
		elif result['outcome']['intent']=="yes_no":
			return self.yesno(result)
		elif result['outcome']['intent']=="set_name":
			return self.set_name(result)
		elif result['outcome']['intent']=="set_home":
			return self.set_home(result)
		elif result['outcome']['intent']=="quit" or result['outcome']['intent']=="good_bye":
			# sys.exit(0)
			platform.quit()
		else:
			print (result)

def initialize():
	s = Saera()
	platform.run_app(s)

def run_text(t):
	return platform.speak(platform.app.execute_text(t))

def run_processed_text(t):
	return platform.app.process(json.loads(t))
	
if __name__=="__main__":
	initialize()

