#!/usr/bin/python

import random
import datetime
import time
try:
	import gobject
	QT = False
except:
	from PySide import QtCore
	QT = True
import os, sys
import functools
import tempfile
import urllib2
import saera

try:
	import json
except ImportError:
	import simplejson as json


#Let's try to use some Google cards
import gsearch

#Maemo-specific alarm functionality
try:
	import alarm
except:
	class alarm:
		class Event:
			pass
		ACTION_WHEN_RESPONDED = 123
		ACTION_TYPE_NOP = 0
		ACTION_TYPE_SNOOZE = 540023
		ALARM_EVENT_BOOT = 8007

# Strings
# import sentences.sentences_english as sent

next_func = None
location = None

def overlap(a, b):
	result = [i for i in a  if i in b]
	return bool(result)

def parse_input(input):
	global next_func
	input = input.lower()

	if next_func:
		# Reset next_func before calling it, to allow currently installed
		# next_func to set another one.
		cur_call_func = next_func
		next_func = None
		return cur_call_func(input)

	elif input.startswith('hello') or input.startswith('hi ') or input.startswith('hey'):
		return hello(input), None
	elif input.startswith('test'):
		return testing(input), None
	elif input.startswith('remind me '):
		return reminder(input[len('remind me '):]), None
	elif input.startswith('we mind me '):
		# Pocketsphinx isn't perfect after all
		return reminder(input[len('we mind me '):]), None
	elif input.startswith('i love you'):
		return iloveyou(input), None
	elif input.startswith("call "):
		return call(input), None
	elif input.startswith("where am i"):
		return where_am_i(input)
		
	elif "nine hundred" in input or "n900" in input:
		return n900(input), None
	elif "settings" in input or "language" in input:
		return settings(input), "self.open_settings()"
	
	elif exists_in_order(['put','on','music'],input.split()) or exists_in_order(['play','music'],input.split()):
		return play_music(), None
	elif exists_in_order(['pause', 'music'],input.split()) or exists_in_order(['be','quiet'],input.split()):
		return pause_music(), None
	elif exists_in_order(['what', 'time'], input.split()):
		return current_time(input), None
	elif exists_in_order(['what', 'day'], input.split()):
		return current_day(input), None
	elif exists_in_order(['take','picture'], input.split()):
		return take_picture(input)
	elif exists_in_order(['answer','life','universe','everything'],input.split()) or exists_in_order(['meaning','life','universe','everything'],input.split()):
		return life_the_universe_and_everything(), None

	elif "weather" in input or "rain" in input or 'sun ' in input\
		or "sunny" in input or "umbrella" in input or "hot" in input or "cold" in input or "wind" in input:
		return get_weather(input)

	elif exists_in_order(['chuck', 'norris'], input.split()):
		return chuck_norris(input), None

	elif exists_in_order(['read', 'email'], input.split()) or exists_in_order(['read', 'emails'], input.split()) or exists_in_order(['what', 'emails'], input.split()):
		return read_emails(input)

	elif 'wake' in input:
		return new_alarm(input)

	elif 'hungry' in input or set(sent.food).intersection(set(input.split())):
		return food(input)

	elif 'gas' in input:
		return gas(input)
		
	elif exists_in_order(['my','location'],input.split()) or exists_in_order(['where', 'i'],input.split()):
		return where_am_i(input)

	#Rather last-ditch: if we can't parse, ask Google
	#elif input.startswith("what") or input.startswith("who") or input.startswith("where") or input.startswith("how") or input.startswith("where"):
	#	return search_google(input)
		
	elif input in ("quit ", "go away "):
		if not QT:
			gobject.timeout_add(3000,sys.exit,0)
		else:
			QtCore.QTimer.singleShot(3000,sys.exit)
		return "Goodbye.", None
		
	else:
		return ai(input), None
	
def play_music():
	#Todo.
	os.system("dbus-send --dest=com.nokia.mafw.renderer.Mafw-Gst-Renderer-Plugin.gstrenderer /com/nokia/mafw/renderer/gstrenderer com.nokia.mafw.renderer.resume")
	return 'Playing music.'

def pause_music():
	#Todo.
	os.system("dbus-send --dest=com.nokia.mafw.renderer.Mafw-Gst-Renderer-Plugin.gstrenderer /com/nokia/mafw/renderer/gstrenderer com.nokia.mafw.renderer.pause")
	return 'Okay.'

def exists_in_order(a, b):
	index = 0
	for i in a:
		if i in b:
			if b.index(i)>=index:
				index=b.index(i)
			else:
				return False
		else:
			return False
	return True

def parse_to_nums(input):
	tens = {'twenty':20, 'thirty':30, 'dirty':30, 'forty':40, 'fifty':50, 'sixty':60}
	teens = {'ten':10, 'eleven':11, 'twelve':12, 'thirteen':13, 'fourteen':14, 'fifteen':15, 'sixteen':16,
			'seventeen':17, 'eighteen':18, 'nineteen':19}
	ones = {'one':1, 'two':2, 'three':3, 'four':4, 'five':5, 'six':6, 'seven':7, 'eight':8, 'ate':8, 'nine':9}
	nlist = []
	ten = False
	has_nums =False
	for i in input:
		if ten:
			if i in ones:
				nlist.append(ten+ones[i])
			else:
				nlist.append(ten)
			ten = False
		else:
			if i in tens:
				has_nums = True
				ten = tens[i]
			elif i in teens:
				has_nums = True
				nlist.append(teens[i])
			elif i in ones:
				has_nums = True
				nlist.append(ones[i])
			else:
				nlist.append(i)
	return nlist, has_nums
				
########### Callback functions ####################
def should_read_email(input):
	if overlap(input.split(), sent.affirmative) and not overlap(input.split(), sent.negative):
		return '', 'self.read_email()'
	else:
		return 'Okay.', None


########### Common questions/functions ############
def ai(input):
	if saera.settings["use_answers_com"] != "no":
		query = input.replace(" ", "_")
		request_url = "http://%s.answers.com/Q/%s" % ("wiki", query)
		print "Sending request to answers.com: %s" % request_url
		os.system('wget "'+request_url+'" -O /tmp/saera/answer.html')
		answer = open('/tmp/saera/answer.html').read()
		if 'description' in answer:
			result = [i for i in answer.split('\n') if 'description' in i][0]
			if "content" in result:
				return "".join([i for i in result.split('content="')[1].strip('"\'<>') if not i in '"<>*'])

	return "I don't understand "+input+". Sorry."

def life_the_universe_and_everything():
	a = random.randint(0,11)
	b = sent.life_universe_everything[a]
	if isinstance(b, basestring):
		return b
	else:
		global next_func
		next_func = eval(b[1])
		return b[0]

def hello(input):
	a = random.randint(0,10)
	b = sent.greeting[a]
	if random.random()>0.999: b = "Go away." #Occasionally grumpy.
	return b
	
def testing(input):
	a = random.randint(0,3)
	b = sent.test[a]
	return b

tz_cities = {"honolulu":-10,"seattle":-8,"portland":-8,"san francisco":-8,"los angeles":-8," las vegas":-8,
			 "vancouver":-8,"tijuana":-8,"denver":-7,"phoenix":-7,"belize":-6,"chicago":-6,
			 "dallas":-6,"houston":-6,"minneapolis":-6,"new orleans":-6,"boston":-5," new york":-5,
			 "philadelphia":-5,"washington":-5,"atlanta":-5, "miami":-5, "cleveland":-5, 
			 "cincinnati":-5, "detroit":-5, "lima":-5, "ottawa":-5, "montreal":-5,
			 "quebec":-5, "toronto":-5, "havana":-5, "london":0, "lisbon":0, "dublin":0,
			 "amsterdam":1, "berlin":1, "vienna":1, "paris":1, "stockholm":1, "rome":1, 
			 "brussels":1, "athens":2, "cairo":2, "istanbul":2, "jerusalem":2, "baghdad":3,
			 "moscow":4, "dubai":4, "jakarta":7, "bangkok":7, "beijing":8, "singapore":8,
			 "tokyo":9, "sydney":10, "melbourne":10}

def current_time(input):
	ltime = datetime.datetime.today()
	loc = ""
	for i in tz_cities:
		if i in input:
			myoffset = datetime.timedelta(seconds=time.timezone)
			ltime = ltime+myoffset
			theiroffset = datetime.timedelta(hours=tz_cities[i])
			ltime = ltime+theiroffset
			loc = " in "+i
			break
	else:
		if " in " in input:
			loc = input[input.index(" in ")+len(" in "):]
			return sent.unknown_time+loc
	return ltime.strftime(sent.known_time+loc+".").replace(" 0", " ")
	
def current_day(input):
	ltime = datetime.datetime.today()
	if "tomorrow" in input:
		return "Tomorrow is "+sent.weekdays[ltime.weekday()+1]
	else:
		return sent.weekdays[ltime.weekday()]

def call(input):
	words, has_nums = parse_to_nums(input.lower().split())
	if has_nums:
		phone_number = "".join([str(i) for i in words if hasattr(i, '__int__')])
		if len(phone_number) in [7, 10, 11]:
			callback = functools.partial(os.system,'dbus-send --system --type=method_call'+
				' --print-reply --dest=com.nokia.csd.Call /com/nokia/csd/call'+
				' com.nokia.csd.Call.CreateWith string:"'+str(phone_number)+'" uint32:0')
			if not QT:
				gobject.timeout_add(5000,os.system,'dbus-send --system --type=method_call'+
					' --print-reply --dest=com.nokia.csd.Call /com/nokia/csd/call'+
					' com.nokia.csd.Call.CreateWith string:"'+str(phone_number)+'" uint32:0')
			else:
				QtCore.QTimer.singleShot(5000,callback)
			return "Calling "+" ".join(phone_number.split(""))
		else:
			return sent.phone_number_error
	else:
		# Todo: check for name of contact
		return sent.contact_name_error

def n900(input):
	a = random.randint(0,8)
	b = sent.N900_facts[a]
	return b

def take_picture(input):
	if not "bless" in input:
		if "me" in input:
			now = datetime.datetime.now()
			photoname = str(now.year)+str(now.month)+str(now.day)+"_"
			os.system(r"gst-launch v4l2src device=/dev/video1 num-buffers=1"+
					  r" ! ffmpegcolorspace ! jpegenc ! filesink"+
					  r" location=/home/user/MyDocs/DCIM/"+photoname+"front.jpg")
			'''if os.path.exists("/usr/bin/display"):
				gobject.timeout_add(5000,os.system,"display /home/user/MyDocs/DCIM/"+
									photoname+"front.jpg")
			else:
				gobject.timeout_add(5000,os.system,"/usr/bin/dbus-send --print-reply"+
									" --dest=com.nokia.image_viewer /com/nokia/image_viewer"+
									" com.nokia.image_viewer.mime_open "+
									"string:file:///home/user/MyDocs/DCIM/"+
									photoname+"front.jpg")'''
			return sent.took_front_picture, 'self.display_picture("/home/user/MyDocs/DCIM/'+photoname+'front.jpg")'
		else:
			now = datetime.datetime.now()
			photoname = str(now.year)+str(now.month)+str(now.day)+"_"
			phots = [i for i in os.listdir("/home/user/MyDocs/DCIM/") if photoname in i]
			phots.sort()
			try:
				num = str(int(phots[-1].split('.')[0].split('_'))+1)
			except IndexError:
				num = "00"
			os.system(r"/usr/bin/gst-launch v4l2camsrc device=/dev/video0 "+
					  r"num-buffers=1 \! video/x-raw-yuv,width=2592,height=1968 "+
					  r" \! ffmpegcolorspace \! jpegenc \! filesink "+
					  r"location=/home/user/MyDocs/DCIM/"+photoname+num+".jpg")
			'''if os.path.exists("/usr/bin/display"):
				gobject.timeout_add(5000,os.system,"display /home/user/MyDocs/DCIM/"+
									photoname+num+".jpg")
			else:
				gobject.timeout_add(5000,os.system,"/usr/bin/dbus-send --print-reply"+
									" --dest=com.nokia.image_viewer /com/nokia/image_viewer"+
									" com.nokia.image_viewer.mime_open "+
									"string:file:///home/user/MyDocs/DCIM/"+
									photoname+num+".jpg")'''
			return sent.took_picture, 'self.display_picture("/home/user/MyDocs/DCIM/'+photoname+num+'.jpg")'

def where_am_i(input):
	return sent.heres_where_you_are, "gobject.timeout_add(500, os.system,'python /opt/modrana/modrana.py --focus-on-coordinates geo:"+ \
		str(location[0])+","+str(location[1])+"')"

def food(input):
	food = list(set(sent.food).intersection(set(input.split())))
	food = food[0] if food else 'food'
	#TODO - cmdline
	return 'Let me search for '+food, "gobject.timeout_add(500, os.system, 'python /opt/modrana/modrana.py --local-search-location geo:" + \
		str(location[0])+","+str(location[1])+" --local-search "+food+"')"

def gas(input):
	return 'Let me search for gas stations.', "gobject.timeout_add(500, os.system, 'python /opt/modrana/modrana.py --local-search-location geo:" + \
		str(location[0])+","+str(location[1])+" --local-search gas')"

def get_weather(input):
	try:
		if location:
			loc = ','.join(location.split(',')[:2])
		else:
			loc = 'NY/New_York'
		# f = urllib2.urlopen('http://api.wunderground.com/api/0a02b434d9bf118f/geolookup/conditions/q/NY/New_York.json')
		f = urllib2.urlopen('http://api.wunderground.com/api/0a02b434d9bf118f/geolookup/conditions/q/'+loc+'.json')
	except urllib2.URLError:
		return "I need an internet connection to look up the weather, sorry."
	json_string = f.read()
	parsed_json = json.loads(json_string)
	location = parsed_json['location']['city']
	temp_f = parsed_json['current_observation']['temp_f']
	feelslike_f = parsed_json['current_observation']['feelslike_f']
	wind_string = parsed_json['current_observation']['wind_string'].replace("NNW","north-northwest")\
																	.replace("NNE", "north-northeast")\
																	.replace("NE", "northeast")\
																	.replace("ENE", "east-northeast")\
																	.replace("ESE", "east-southeast")\
																	.replace("SE", "southeast")\
																	.replace("SSE", "south-southeast")\
																	.replace("SSW", "south-southwest")\
																	.replace("SW", "southwest")\
																	.replace("WSW", "west-southwest")\
																	.replace("WNW", "west-northwest")\
																	.replace("NW", "northwest")\
																	.replace("MPH", "miles per hour")
	precip = float(parsed_json['current_observation']['precip_1hr_in'])
	weather = parsed_json['current_observation']['weather'].lower()
	f.close()
	if overlap(['rain', 'rainy', 'raining'], input):
		if precip>0.2 or 'rain' in weather.lower() or ('storm' in weather.lower() and not 'snow' in weather.lower()):
			return 'Yes.', None
		else:
			return 'No, the current weather in %s is %s.' % (location, weather), None
	elif overlap(['sun', 'sunny'], input):
		if precip<0.2 and ('sun' in weather.lower() or 'clear' in weather.lower()):
			return 'Yes.', None
		else:
			return 'No, the current weather in %s is %s.' % (location, weather), None
	elif overlap(['hot', 'cold'], input):
		if abs(float(temp_f)-float(feelslike_f))>2:
			return "In %s it is %s degrees Fahrenheit, but it feels like %s." % (location, temp_f, feelslike_f), None
		else:
			return "It is %s degrees in %s." % (temp_f, location), None
	elif "umbrella" in input:
		if 'rain' in weather.lower() or ('storm' in weather.lower() and not 'snow' in weather.lower()):
			return 'Yes, the weather is %s in %s.' % (weather, location), None
		elif overlap(['snow', 'flurries', 'blizzard'], weather.lower()):
			return 'That depends; the weather in %s is %s. Do you use an umbrella in the snow?' % (location, weather), None
		elif precip>0.2:
			return 'Maybe; there should be rain but the weather is %s.' % (weather), None
		else:
			return "I don't think you need an umbrella; the weather in %s is %s." % (location, weather), None
	elif "wind" in input:
		return "The wind in %s is %s." % (location, wind_string.lower()), None
	else:
		if "tornado" in weather:
			return "Tornado. Get down to the cellar.", None
	return "The weather in %s is %s degrees and %s." % (location, temp_f, weather), None

def settings(input):
	return "Ok."

def iloveyou(input):
	return sent.i_love_you

bells = {'quarter':15, 'half':30}
times = {'noon':12, 'midnight':0, 'morning':9, 'afternoon':16, 'evening':19, 'night':21}
weekdays = ['sunday','monday','tuesday','wednesday', 'thursday','friday','saturday']

def input_to_datetime (input):
	time = datetime.datetime.today()
	words, has_nums = parse_to_nums(input.lower().split())
	day_identifier = [i for i in words if i in weekdays]

	if "after tomorrow" in input.lower():
		time = time + datetime.timedelta(days = 2)
	elif 'tomorrow' in words:
		time = time + datetime.timedelta(days = 1)
	elif day_identifier:
		day = weekdays.index(day_identifier[0])
		print day
		time = time + datetime.timedelta(days = (day - time.weekday()) % 7)

	hour = [i for i in words if i in times]
	if hour:
		time = time.replace(hour = times[hour[0]], minute = 0, second = 0, microsecond = 0)
	hour = False
	minute = 0
	pmam = False
	bell = False
	for i in words:
		try:
			# try casting to integer, fails for non-numbers
			int(i)

			if type(hour) == bool and not hour:
				hour = int(i)
			elif not minute:
				minute = int(i)
		except ValueError:
			pass

		if i in bells:
			bell = True
			minute = bells[i]
		elif bell:
			if i in ['as', 'past', 'after']:
				pass
			elif i in ['to', 'told', 'til', 'till', 'of']:
					minute = -minute
			bell = False
		elif pmam:
			if i == 'm.':
				if pmam == 'pm':
					hour = hour % 12 + 12
				elif pmam == 'am':
					hour = hour%12
			pmam = False
		elif i in ['p.', 'a.']:
			pmam = {'p.':'pm','a.':'am'}[i]

	if minute < 0:
		hour = (hour - 1) % 24
		minute = 60 + minute

	if type(hour) == bool:
		hour = time.hour

	return time.replace(hour = hour, minute = minute, second = 0, microsecond = 0)

def reminder (message):
	message = message.strip()
	if message.startswith('to '):
		message = message[len('to '):]

	if ' at ' in message:
		tiloc_ptr = message.index(' at ')
		time = input_to_datetime(message[tiloc_ptr + 4:])
		message = message[:tiloc_ptr - 1]

		set_alarm(message, time, True)
		return "Okay, at %s I will remind you to %s" % \
			(time.strftime("%I:%M %P"), message)

	else:
		global next_func
		next_func = lambda x: (reminder_time(x, message), None)
		return sent.what_reminder_time

def reminder_time(input, message):
	time = input_to_datetime(input)
	set_alarm(message, time, True)

	return "Okay, at %s I will remind you to %s" % \
		(time.strftime("%I:%M %P"), message)

def set_alarm(message, time, use_espeak = False):
	event = alarm.Event()
	event.appid = 'Saera'
	event.alarm_time = float(time.strftime("%s"))

	if use_espeak:
		fd, name = tempfile.mkstemp()
		fh = os.fdopen(fd, 'w+')
		fh.write(r"""#! /bin/sh
		espeak '%s'
		rm -f '%s'
		""" % (message, name))
		fh.close()

		actions = event.add_actions(1)
		actions[0].flags |= alarm.ACTION_WHEN_TRIGGERED | alarm.ACTION_TYPE_EXEC
		actions[0].command = "/bin/sh '%s'" % name

	else:
		event.message = message

		action_stop, action_snooze = event.add_actions(2)
		action_stop.label = 'Stop'
		action_stop.flags |= alarm.ACTION_WHEN_RESPONDED | alarm.ACTION_TYPE_NOP

		action_snooze.label = 'Snooze'
		action_snooze.flags |= alarm.ACTION_WHEN_RESPONDED | alarm.ACTION_TYPE_SNOOZE

	return alarm.add_event(event)

def new_alarm(input):
	time = input_to_datetime (input)
	if time < datetime.datetime.now():
		return "The alarm time is in the past, can't help.  Sorry.", None

	set_alarm('Wake Up', time)
	return "Okay, I set your alarm for "+time.strftime("%I:%M %P"), None

def search_google(input):
	a, b, loc = gsearch.search(input)
	if a and b:
		return a + ' is '+b+'.', None
	elif loc:
		return 'Let me search for '+food, "gobject.timeout_add(500, os.system, 'python /opt/modrana/modrana.py --address-search "+food+"')"

def chuck_norris(input):
	return sent.chuck_norris[random.randint(0,len(sent.chuck_norris))]

def read_emails(input):
	return "Here are your emails.", 'self.read_all_emails()'

###################################################
	
if __name__=='__main__':
	while 1:
		print parse_input(raw_input())
