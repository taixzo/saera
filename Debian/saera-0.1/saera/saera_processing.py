#!/usr/bin/python

import random
import datetime
import time
import gobject
import os, sys

next_func = None

def parse_input(input):
	input = input.lower()
	if next_func:
		return next_func(input)
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
		
	elif "nine hundred" in input or "n900" in input:
		return n900(input), None
	
	elif exists_in_order(['put','on','music'],input.split()) or exists_in_order(['play','music'],input.split()):
		return play_music(), None
	elif exists_in_order(['what', 'time'], input.split()):
		return current_time(input), None
	elif exists_in_order(['take','picture'], input.split()):
		return take_picture(input)
	elif exists_in_order(['answer','life','universe','everything'],input.split()) or exists_in_order(['meaning','life','universe','everything'],input.split()):
		return life_the_universe_and_everything(), None
		
	elif input in ("quit ", "go away "):
		gobject.timeout_add(3000,sys.exit,0)
		return "Goodbye.", None
		
	else:
		return ai(input), None
	
def store_answer(answer):
	pass
	global next_func
	next_func = None
	return 'Ok.', None
	
def play_music():
	#Todo.
	return 'Playing music.'

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
				

########### Common questions/functions ############
def ai(input):
	return "I don't understand you. Sorry."

def life_the_universe_and_everything():
	a = random.randint(0,10)
	b = ['41.99999999.',
			'Chocolate.',
			'That will take me some time to answer. About seven and a half million years.',
			'Love is the meaning of life. The rest of the universe will figure itself out.',
			'Open-source software.',
			'I am.',
			'Take a vacation to the tropics.',
			'It takes two people.',
			['What do you want the answer to be?', store_answer],
			'Forty-two.',
			# A Matrix quote too, why not.
			'The Matrix is the world that has been pulled over your eyes to blind you from the truth.'][a]
	if isinstance(b, basestring):
		return b
	else:
		global next_func
		next_func = b[1]
		return b[0]

def hello(input):
	a = random.randint(0,10)
	b = ['Hello!',
		 'Good day.',
		 'Hi.',
		 'Hey.',
		 'Aloha!',
		 'Hello!',
		 'Hello!',
		 'Hello!',
		 'Hello!',
		 "It's a nice day for artificial intelligence.",
		 'Hey there!'][a]
	if random.random()>0.999: b = "Go away." #Occasionally grumpy.
	return b
	
def testing(input):
	a = random.randint(0,3)
	b = ['I am working.',
		 'Testing, testing, one, two, three.',
		 'Status report: Saera running.',
		 'Pass'][a]
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
			return "Sorry, I don't know what time it is in "+loc
	return ltime.strftime("Right now, it is %I:%M %p"+loc+".").replace(" 0", " ")

def call(input):
	words, has_nums = parse_to_nums(input.lower().split())
	if has_nums:
		phone_number = "".join([str(i) for i in words if hasattr(i, '__int__')])
		if len(phone_number) in [7, 10, 11]:
			gobject.timeout_add(5000,os.system,'dbus-send --system --type=method_call'+
				' --print-reply --dest=com.nokia.csd.Call /com/nokia/csd/call'+
				' com.nokia.csd.Call.CreateWith string:"'+str(phone_number)+'" uint32:0')
			return "Calling "+" ".join(phone_number.split(""))
		else:
			return "Phone numbers have ten or eleven characters."
	else:
		# Todo: check for name of contact
		return "I don't know who that is."

def n900(input):
	a = random.randint(0,8)
	b = ["The N900 is the king of phones.",
		 "Did you know the N900 can run Mac OSX?",
		 "Nokia made the phone, the community did all the work.",
		 "The N900 had a Retina display before the iPhone.",
		 "There are good resources for the N900 on maemo.org.",
		 "Let's take a computer, a camera, a radio and a phone"+
		 " and put them in one package. That device you are now holding in your hand.",
		 "The N900 has been made to run at least 8 operating systems.",
		 "If there isn't an app for that, you can make it!"][a]
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
			return "Ok. I took a picture of you.", 'self.display_picture("/home/user/MyDocs/DCIM/'+photoname+'front.jpg")'
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
			return "I took a picture.", 'self.display_picture("/home/user/MyDocs/DCIM/'+photoname_num+'.jpg")'


def iloveyou(input):
	return "I love you too. Clearly, we should go read XKCD."

bells = {'quarter':15, 'half':30}
times = {'noon':12, 'midnight':0, 'morning':9, 'afternoon':16, 'evening':19, 'night':21}
weekdays = ['sunday','monday','tuesday','wednesday', 'thursday','friday','saturday']

def reminder (message):
	message = message.strip()
	if message.startswith('to '):
		message = message[len('to '):]
	if ' at ' in message:
		tiloc = message[message.index(' at ')+len(' at '):]
		tiloc, has_nums = parse_to_nums(tiloc.split())
		if has_nums:
			nums = [i for i in tiloc if hasattr(i, '__int__')]
		hour = 0
		minute = 0
		bell = False
		pmam = False
		for i in tiloc:
			if hasattr(i, '__int__'):
				if not hour:
					hour = i
				elif not minute:
					minute = i
			else:
				if i in bells:
					bell = True
					minute = bells[i]
				elif bell:
					if i in ['as', 'past', 'after']:
						pass
					elif i in ['to', 'told', 'til', 'till', 'of']:
						minute = -minute
					bell = False
				elif i in times:
					hour = times[i]
				elif pmam:
					if i=='m.':
						if pmam=='pm':
							hour = hour%12+12
						elif pmam=='am':
							hour = hour%12
					pmam = False
				elif i in ['p.', 'a.']:
					pmam = {'p.':'pm','a.':'am'}[i]
		if minute<0:
			hour=(hour-1)%24
			minute = 60+minute
		print tiloc, hour, minute
	else:
		global next_func
		next_func = reminder_time
		return 'What time would you like me to remind you?'
	return 'Reminding you '+message
	
def reminder_time(input):
	global next_func
	next_func = None
	time = datetime.datetime.today()
	words, has_nums = parse_to_nums(input.lower().split())
	day_identifier = [i for i in words if i in weekdays]
	if "after tomorrow" in input.lower():
		time = time+datetime.timedelta(days=2)
	elif 'tomorrow' in words:
		time = time+datetime.timedelta(days=1)
	elif day_identifier:
		day = weekdays.index(day_identifier[0])
		print day
		time = time+datetime.timedelta(days=(day-time.weekday())%7)
	
	hour = [i for i in words if i in times]
	if hour:
		time = time.replace(hour=times[hour[0]],minute=0,second=0,microsecond=0)
	hour = False
	minute = 0
	pmam = False
	bell = False
	for i in words:
		if hasattr(i, '__int__'):
			if type(hour)==bool and not hour:
				hour = i
			elif not minute:
				minute = i
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
			if i=='m.':
				if pmam=='pm':
					hour = hour%12+12
				elif pmam=='am':
					hour = hour%12
			pmam = False
		elif i in ['p.', 'a.']:
			pmam = {'p.':'pm','a.':'am'}[i]
	if minute<0:
		hour=(hour-1)%24
		minute = 60+minute
	if type(hour)==bool:
		hour = time.hour
	time = time.replace(hour=hour,minute=minute,second=0,microsecond=0)
	os.system('echo \'espeak "'+input+'" > at')
	return str(time), None

###################################################
	
if __name__=='__main__':
	while 1:
		print parse_input(raw_input())
