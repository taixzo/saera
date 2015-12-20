#! /usr/bin/env python

import pyotherside
import os, sys
import email
import subprocess
import sqlite3
from datetime import datetime, timedelta
import pyjulius
import queue as Queue
import time
import random
import threading
import espeak2julius
import json
from streetnames import get_street_names
import alsaaudio, audioop
import re
from ID3 import ID3
try:
	import urllib.parse as parse
except:
	import urllib as parse
import guessing
import base64
import hmac
import hashlib
import http.client as httplib
import urllib.request as urllib2
from collections import namedtuple
import shutil

Message = namedtuple("Message", ("id", "sender", "sender_id", "message", "account", "date"))

import ast # for safely parsing timed stuff

global app
app = None

settings_path = os.getenv('HOME')+'/.config/saera/setting.json'

class Struct:
    def __init__(self, **entries): 
        self.__dict__.update(entries)

def load_config():
	settings = {
		"use_gps":True,
		"imperial":True,
		"read_texts":False,
		"internet_voice":False,
		"internet_voice_engine":"Wit", # Options: Wit, Google, Houndify
	}
	if os.path.exists(settings_path):
		with open(settings_path) as settings_file:
			settings.update(json.load(settings_file))
	else:
		os.makedirs(settings_path[:settings_path.rindex('/')], exist_ok=True)
		with open(settings_path, 'w') as settings_file:
			json.dump(settings, settings_file)
	return Struct(**settings)

config = load_config()

class MicroMock(object):
	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)

memory_path = os.getenv('HOME')+'/.saera_memory.db'
if not os.path.exists(memory_path):
	conn = sqlite3.connect(memory_path)
	conn.row_factory = sqlite3.Row
	cur = conn.cursor()
	cur.execute('CREATE TABLE Variables (Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, VarName TEXT NOT NULL, Value TEXT NOT NULL, UpdateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
	cur.execute('CREATE TABLE Locations (Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, LocName TEXT NOT NULL COLLATE NOCASE, Zip TEXT, Latitude REAL, Longitude REAL, Timezone REAL, UpdateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
	cur.execute('CREATE TABLE People (Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, Name TEXT NOT NULL COLLATE NOCASE, Description TEXT, Born DATE, Died DATE, Gender TEXT, Profession TEXT)')
	cur.execute('CREATE TABLE LocationLogs (Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, Latitude REAL, Longitude REAL, UpdateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')

	cur.execute('INSERT INTO Locations (LocName, Zip, Latitude, Longitude, Timezone) VALUES ("Tokyo", "", 35.6833, 139.6833, 9)')
	cur.execute('INSERT INTO Locations (LocName, Zip, Latitude, Longitude, Timezone) VALUES ("Shanghai", "", 31.2, 121.5, 8)')
	cur.execute('INSERT INTO Locations (LocName, Zip, Latitude, Longitude, Timezone) VALUES ("New York", "10001", 40.7127, -74.0059, -5)')
	cur.execute('INSERT INTO Locations (LocName, Zip, Latitude, Longitude, Timezone) VALUES ("Mexico City", "08619", 19.433, -99.133, -6)')
	cur.execute('INSERT INTO Locations (LocName, Zip, Latitude, Longitude, Timezone) VALUES ("Moscow", "101", 55.75, 37.6167, 3)')
	cur.execute('INSERT INTO Locations (LocName, Zip, Latitude, Longitude, Timezone) VALUES ("Los Angeles", "90001", 34.05, -118.25, -8)')

	conn.commit()
else:
	conn = sqlite3.connect(memory_path)
	conn.row_factory = sqlite3.Row
	cur = conn.cursor()

try:
	mailconn = sqlite3.connect('/home/nemo/.qmf/database/qmailstore.db')
	mailcur = mailconn.cursor()
	has_mail = True
except sqlite3.OperationalError:
	has_mail = False

f = __file__.split('sailfish_hw.py')[0]

# terminate any pre-existing julius processes
p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
out, err = p.communicate()
for line in out.decode('UTF-8').splitlines():
	if 'julius.arm' in line:
		pid = int(line.split(None, 1)[0])
		os.kill(pid, 9)

activeMediaPlayer = "jolla-mediaplayer"
song_title_map = {}
lst = []
def regen_music():
	regex = re.compile('[^a-zA-Z ]')
	# files = subprocess.Popen("find /home/nemo/Music/ -type f -name \*.mp3", shell=True, stdout=subprocess.PIPE).communicate()[0].splitlines()[:40]
	# for file in files:
	# 	id3info = ID3(file)
	# 	if id3info.has_tag:
	# 		lst.append(id3info.title.decode('utf-8'))
	# 		song_title_map[id3info.title.decode('utf-8').lower()] = file
	# 	else:
	# 		name = os.path.split(file)[1].decode('utf-8').split('.')[0]
	# 		if name.count(' - ')==1:
	# 			artist, name = name.split(' - ')
	# 		name = regex.sub('', name).strip()
	# 		if name:
	# 			lst.append(name)
	# 			song_title_map[name.lower()] = file
	# 		continue
	tlist = subprocess.Popen('tracker-sparql -q "SELECT ?title ?artist ?url \
	WHERE { ?song a nmm:MusicPiece . ?song nie:title ?title . ?song nmm:performer ?aName . ?aName nmm:artistName ?artist . \
	?song nie:url ?url . }"', shell=True, stdout=subprocess.PIPE).communicate()[0].splitlines()[1:]
	for line in tlist:
		if not line: continue
		try:
			l = line.decode('utf-8').split(", file://")
			file = l[-1]
			# tracker-sparql uses commas in results and doesn't escape them. As there
			# seems to be no workaround, we assume that all URLs are file:// urls and
			# no artists contain commas.
			index_of_last_comma = l[0].rindex(',')
		except: # If there are no songs on device, tracker-sparql will return 'None' which does not contain commas
			lst.append('music')
			break
		artist = l[0][index_of_last_comma+1:]
		title = l[0][:index_of_last_comma]
		if title.count(' - ')==1:
			name_artist, title = title.split(' - ')
		title = regex.sub('', title).strip()
		lst.append(title)
		# print (title)
		song_title_map[title.lower()] = file

contacts = {}
firstnames = {}
streetnames = []
volume = 65536

def regen_contacts():
	firsts = []
	fulls = []
	ccon = sqlite3.connect('/home/nemo/.local/share/system/Contacts/qtcontacts-sqlite/contacts.db')
	cur = ccon.cursor()
	cur.execute('SELECT lowerFirstName, lowerLastName, hasPhoneNumber, contactId from Contacts')
	rows = cur.fetchall()
	for first, last, hasPhoneNumber, contactId in rows:
		if first is not None and first.isalpha():
			firsts.append(first)
			guessing.variables['contact'].keywords.append(first)
			if last is not None and last.isalpha():
				fulls.append(first+' '+last)
				contacts[first+' '+last] = {'hasPhoneNumber':hasPhoneNumber, 'contactId':contactId}
				firstnames[first] = first+' '+last
				guessing.variables['contact'].keywords.append(last)
				# try:
				# 	print (fulls[-1])
				# except UnicodeEncodeError:
				# 	print ("Name contains Unicode string")
			else:
				contacts[first] = {'hasPhoneNumber':hasPhoneNumber, 'contactId':contactId}
				firstnames[first] = first
				# try:
				# 	print (firsts[-1])
				# except UnicodeEncodeError:
				# 	print ("Name contains Unicode string")
	cur.execute('SELECT Contacts.contactId, PhoneNumbers.phoneNumber from Contacts, PhoneNumbers where Contacts.contactId = PhoneNumbers.contactId')
	rows = cur.fetchall()
	for contactId, phoneNumber in rows:
		if contactId in [contacts[i]['contactId'] for i in contacts]:
			for i in contacts:
				if contacts[i]['contactId'] == contactId:
					contacts[i]['phoneNumber'] = phoneNumber
					break

def regen_streetnames():
	global streetnames
	cur.execute("SELECT * FROM Variables WHERE VarName='here'")
	here = cur.fetchone()
	if here:
		cur.execute("SELECT * FROM Locations WHERE Id="+str(here[2]))
		here = cur.fetchone()
	else:
		cur.execute("SELECT * FROM Variables WHERE VarName='home'")
		here = cur.fetchone()
		if here:
			cur.execute("SELECT * FROM Locations WHERE Id="+str(here[2]))
			here = cur.fetchone()
		else:
			streetnames = [("main","st"),
						   ("first","ave"),
						   ("washington","blvd")]
			return
	stn = get_street_names(here)
	for streettype in stn:
		for streetname in stn[streettype]:
			streetnames.append((streetname,streettype.lower()))
	print (streetnames)
	# espeak2julius.create_grammar(streetnames, 'addresses', 'addresses')

pyotherside.send('load_msg','Loading music titles...')
if not os.path.exists('/home/nemo/.cache/saera/musictitles.dfa'):
	if not os.path.exists('/home/nemo/.cache/saera'):
		os.mkdir('/home/nemo/.cache/saera')
	regen_music()
	espeak2julius.create_grammar(lst, 'musictitles', 'songtitles')
else:
	regen_music()

pyotherside.send('load_msg','Loading contacts...')
if not os.path.exists('/home/nemo/.cache/saera/contacts.dfa'):
	if not os.path.exists('/home/nemo/.cache/saera'):
		os.mkdir('/home/nemo/.cache/saera')
	regen_contacts()
	espeak2julius.create_grammar(list(contacts) if contacts else ['John Smith'], 'contacts', 'contacts')
else:
	regen_contacts()

pyotherside.send('load_msg','Loading street names...')
if not os.path.exists('/home/nemo/.cache/saera/addresses.dfa'):
	if not os.path.exists('/home/nemo/.cache/saera'):
		os.mkdir('/home/nemo/.cache/saera')
	regen_streetnames()
	pyotherside.send('load_msg','Loading street names\n(this may take a while)...')
	espeak2julius.create_grammar(streetnames, 'addresses', 'addresses')
else:
	pass # We don't do anything with streetnames here so no point to load them

pyotherside.send('load_msg','Initializing speech recognition...')
if not os.path.exists('/tmp/saera'):
	os.mkdir('/tmp/saera')
jproc = subprocess.Popen([f+'julius/julius.jolla','-module', '-record', '/tmp/saera/', '-gram',f+'julius/saera', '-gram', '/home/nemo/.cache/saera/musictitles', '-gram', '/home/nemo/.cache/saera/contacts', '-gram', '/home/nemo/.cache/saera/addresses','-h',f+'julius/hmmdefs','-hlist',f+'julius/tiedlist','-input','mic','-tailmargin','800','-rejectshort','600'],stdout=subprocess.PIPE)
# jproc = subprocess.Popen([f+'julius/julius.arm','-module','-gram','/tmp/saera/musictitles','-h',f+'julius/hmmdefs','-hlist',f+'julius/tiedlist','-input','mic','-tailmargin','800','-rejectshort','600'],stdout=subprocess.PIPE)
client = pyjulius.Client('localhost',10500)
print ('Connecting to pyjulius server')
while True:
	try:
		client.connect()
		break
	except pyjulius.ConnectionError:
		sys.stdout.write('.')
		time.sleep(2)
sys.stdout.write('..Connected\n')
client.start()
client.send("TERMINATE\n")

detected = False
daemons_running = True
listening = False
active_listening = False

# These should really go in a utilities file
def post_multipart(host, selector, fields, files):
	content_type, body = encode_multipart_formdata(fields, files)
	while True:
		try:
			h = httplib.HTTPConnection(host)
			h.putrequest('POST', selector)
			h.putheader('content-type', content_type)
			h.putheader('content-length', str(len(body)))
			h.endheaders()
			h.send(body)
			break
		except InterruptedError:
			continue
	# errcode, errmsg, headers = h.getreply()
	response = h.getresponse()
	# return h.file.read()
	return response.read().decode('utf-8')

def encode_multipart_formdata(fields, files):
    boundary = b"fhajlhafjdhjkfadsjhkfhajsfdhjfdhajkhjsfdakl"
    CRLF = b'\r\n'
    L = []
    for (key, value) in fields.items():
        L.append(b'--' + boundary)
        L.append(('Content-Disposition: form-data; name="%s"' % key).encode('utf-8'))
        L.append(b'')
        L.append(value)
    for (key, value) in files.items():
        L.append(b'--' + boundary)
        L.append(('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, key)).encode('utf-8'))
        L.append(b'Content-Type: application/octet-stream')
        L.append(b'')
        L.append(value)
    L.append(b'--' + boundary + b'--')
    L.append(b'')
    body = CRLF.join(L)
    content_type = ('multipart/form-data; boundary=%s' % boundary.decode('utf-8')).encode('utf-8')
    return content_type, body

access_key = "e46ce64507373c1d4e18a5e927efe7e0"
access_secret = "XGjCnOU0U4Dysum3kGmPDG0YH8gKvoMQUZY1hzox"

def pause_daemons():
	global daemons_running
	daemons_running = False
	stop_active_listening()

def resume_daemons():
	global daemons_running
	daemons_running = True
	e.set()
	e2.set()
	start_active_listening()

def watch_proximity(e):
	global detected
	while True:
		prox_detect = open("/sys/devices/virtual/input/input10/prx_detect").read()
		if bool(int(prox_detect)) and not detected:
			detected = True
			print ("Detected proximity input")
			pyotherside.send('start')
		if not daemons_running:
			print ('Application unfocused.')
			e.wait()
			e.clear()
			print ('Application focused.')
		time.sleep(1)

def watch_headset_btn():
	dbproc = subprocess.Popen(["dbus-monitor --system \"type='signal',sender='org.bluez',interface='org.bluez.Headset',member='AnswerRequested'\""],shell=True,stdout=subprocess.PIPE)
	while True:
		res = dbproc.stdout.readline()
		if res.endswith(b'AnswerRequested\n'):
			pyotherside.send('start')


def watch_mic(e):
	inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NONBLOCK)
	inp.setchannels(1)
	inp.setrate(8000)
	inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
	inp.setperiodsize(160)
	while True:
		l,data = inp.read()
		if not daemons_running:
			inp.pause()
			e.wait()
			e.clear()
			inp.pause(False)
		while True:
			tl,tdata = inp.read()
			if tl:
				l,data = tl, tdata
			else:
				break
		if l:
			# Return the maximum of the absolute value of all samples in a fragment.
			# print (audioop.max(data, 2))
			pyotherside.send('set_vol',audioop.max(data,2))
		time.sleep(.04)

e = threading.Event()
e2 = threading.Event()
e3 = threading.Event()
prox_thread = threading.Thread(target=watch_proximity, args=(e,))
mic_thread = threading.Thread(target=watch_mic, args=(e2,))
headset_thread = threading.Thread(target=watch_headset_btn)
prox_thread.start()
mic_thread.start()
headset_thread.start()

qgvdial_msgs = []

def load_qgvdial_messages():
	qconn = sqlite3.connect('/home/nemo/.qgvdial/qgvdial.sqlite.db')
	qcur = qconn.cursor()
	rows = qcur.execute('SELECT * from gvinbox where flags & 1 != 0 and type=5')
	for row in rows:
		qgvdial_msgs.append([row[4],row[6]])

def check_qgvdial_messages():
	qconn = sqlite3.connect('/home/nemo/.qgvdial/qgvdial.sqlite.db')
	qcur = qconn.cursor()
	qcur.execute('SELECT * from gvinbox where flags & 1 != 0 and type=5')
	rows = qcur.fetchall()
	new_msgs = []
	for row in rows:
		conversation = row[6].split('<br>')
		for message in conversation:
			if not message: continue
			sender, msg = message.split(':</b> ')
			sender = sender.split('<b>')[-1]
			msg, msg_time = msg.split(' <i>')
			msg_time = msg_time.split('</i>')[0]
			msg_date = datetime.fromtimestamp(row[2])
			hour, minute = msg_time.split(':')
			minute, am_pm = minute.split(' ')
			hour, minute = int(hour), int(minute)
			if 'p' in am_pm.lower():
				hour += 12
				hour %= 24
			msg_date = msg_date.replace(hour=hour, minute=minute)
			msg_id = row[0]+hashlib.md5(message.encode('utf-8')).hexdigest()

			msg = Message(id=msg_id, sender=sender, sender_id=row[4], message=msg, account='qgvdial', date=time.mktime(msg_date.timetuple()))
			if msg not in qgvdial_msgs and sender!='Me':
				new_msgs.append(msg)
				qgvdial_msgs.append(msg)
	return new_msgs

def check_messages():
	def parse_txt_date(date):
		return time.mktime(datetime.strptime(date.split(" GMT")[0], '%a %b %d %H:%M:%S %Y').timetuple())


	rproc = subprocess.Popen(["commhistory-tool", "listgroups"],stdout=subprocess.PIPE)
	res = rproc.communicate()[0]
	
	new_msgs = []
	groups = []
	for i in res.splitlines():
		i = i.decode('utf-8')
		if i.startswith("Group"):
			groups.append([])
			v = i[i.index('('):i.index(')')]
			if not v.startswith('0'):
				# Yay! New messages!
				pass
		else:
			msg = i.split('|')
			if len(msg)<13:
				continue
			if msg[6]=='0':
				# new_msgs.append([msg[10],msg[12]])
				new_msgs.append(Message(id=msg[0], sender=msg[10], sender_id=msg[10], message=msg[12], account=msg[9], date=parse_txt_date(msg[2])))
	return new_msgs

print ("Messages:")
for i in check_messages():
	print ("%s: %s" % (i.sender, i.message))
print ("QGVDial:")
for i in check_qgvdial_messages():
	print ("%s: %s" % (i.sender, i.message))
	# pass
	
def watch_texts():
	global detected
	while True:
		unread_msgs = check_qgvdial_messages()
		if unread_msgs:
			pyotherside.send('sayRich', '%s says: %s' % (unread_msgs[0].sender, unread_msgs[0].message), None, None, None)
		if not daemons_running:
			e.wait()
			e.clear()
		time.sleep(20)

text_thread = threading.Thread(target=watch_headset_btn)

#julius/julius.jolla -module -gram /usr/share/harbour-saera/qml/pages/julius/saera -gram /home/nemo/.cache/saera/musictitles -gram /home/nemo/.cache/saera/contacts -gram /home/nemo/.cache/saera/addresses -h /usr/share/harbour-saera/qml/pages/julius/hmmdefs -hlist /usr/share/harbour-saera/qml/pages/julius/tiedlist -input mic -tailmargin 800 -rejectshort 600
def listen():
	l = threading.Thread(target=listen_thread)
	l.start()

def listen_thread():
	print ("Listening...")
	global volume
	volume_getter = subprocess.Popen(["pactl list sinks | grep \"Volume: front-left\" | awk '{print $3}'"], shell=True, stdout=subprocess.PIPE)
	result, err = volume_getter.communicate()
	# if config.internet_voice:
	# 	if os.path.exists('/tmp/saera/outfile.ogg'):
			# os.remove('/tmp/saera/outfile.ogg')
		# audiorecorder = subprocess.Popen(["gst-launch-0.10 alsasrc ! audioconvert ! audioresample ! vorbisenc ! oggmux ! filesink location=/tmp/saera/outfile.ogg"], shell=True)
	volume = int(result.split(b'\n')[1])
	target_volume = int(volume/4)
	subprocess.Popen(['pactl', 'set-sink-volume', '1', str(target_volume)])

	# purge message queue
	time.sleep(0.7)
	client.send("RESUME\n")
	global listening
	listening = True
	while 1:
		try:
			client.results.get(False)
		except Queue.Empty:
			break
	print ("Message queue Empty")
	while 1:
		try:
			result = client.results.get(False)
			if isinstance(result,pyjulius.Sentence):
				print ("SENTENCE")
				print (dir(result), " ".join([i.word for i in result.words]), result.score)
				break
			elif result.tag=="RECOGFAIL":
				# result.words = ['*mumble*']
				result = MicroMock(words=[MicroMock(word='*mumble*')])
				break
			elif not listening:
				return
		except Queue.Empty:
			continue
	numbers = {'zero':'0','oh':'0','one':'1','two':'2','three':'3','four':'4','five':'5','six':'6','seven':'7','eight':'8','nine':'9'}
	words = [i.word for i in result.words]
	num_str = ''
	for i, word in enumerate(words):
		if len(words)>i-1:
			if word in numbers:
				num_str += numbers[word]
			else:
				if len(num_str)>1:
					words[i-(len(num_str))] = num_str
					words[i-(len(num_str))+1:i] = ['']*(len(num_str)-1)
				num_str = ''
	words = [i for i in words if i]
	if words[0] in ['what','where','when','why','how','who','is','will','are','do','should','can','would','does']:
		punct = '?'
	else:
		punct = '.'
	res = " ".join(words)+punct
	res = res[0].upper()+res[1:]
	client.send("TERMINATE\n")
	if config.internet_voice:
		ifconfig_proc = subprocess.Popen(['/sbin/ifconfig'], stdout=subprocess.PIPE)
		output, err = ifconfig_proc.communicate()
		# Only send voice to server if we are on wifi
		if b'wlan0' in output:
			pyotherside.send('goBusy')
			tmpfile = max(os.listdir('/tmp/saera'))
			data = open('/tmp/saera/%s' % tmpfile, 'rb').read()
			if config.internet_voice_engine=='Wit':
				req = urllib2.Request('https://api.wit.ai/speech?v=20141022', data)
				req.add_header('Content-Length', '%d' % len(data))
				req.add_header('Authorization', "Bearer CH4ZMQO2X7VGXBCLERMDJFFO4RYQWFCK")
				req.add_header('Content-Type', 'audio/wav')
				rem_res = urllib2.urlopen(req)
				out = rem_res.read()
				j = json.loads(out.decode('utf-8'))
				print (j)
				if '_text' in j and j['_text']:
					res = j['_text'][0].upper() + j['_text'][1:]
	pyotherside.send('process_spoken_text',res)

def getTrigger():
	while active_listening:
		try:
			print(".", end="")
			result = client.results.get(True, 0.5)
			if isinstance(result,pyjulius.Sentence) and len(result.words)==1 and result.words[0].word=="Saera" and result.words[0].confidence>0.7:
				# getSpeech()
				print ("Got trigger!")
				pyotherside.send('trigger')
				return
		except Queue.Empty:
			time.sleep(0.2)
			continue

def start_active_listening():
	global active_listening
	if not active_listening:
		active_listening = True
		l = threading.Thread(target=getTrigger)
		l.start()

def stop_active_listening():
	global active_listening
	active_listening = False
	subprocess.Popen(['pactl', 'set-sink-volume', '1', str(volume)])

def cancel_listening():
	client.send("TERMINATE\n")
	global listening
	global active_listening
	listening = False
	active_listening = False
	subprocess.Popen(['pactl', 'set-sink-volume', '1', str(volume)])

class timed:
	alarms = []

	def check():
		if os.path.exists(os.getenv('HOME')+'/.config/saera/alarms'):
			alarm_list = open(os.getenv('HOME')+'/.config/saera/alarms').read().splitlines()
		else:
			if not os.path.exists(os.getenv('HOME')+'/.config/saera'):
				os.mkdir(os.getenv('HOME')+'/.config/saera')
			alarm_list = []
		result = subprocess.Popen(["timedclient-qt5", "--info"], stdout=subprocess.PIPE).communicate()
		rawvals = result[0].decode("UTF-8").split("Cookie ")
		cookie = None
		for val in rawvals:
			alm = {}
			for line in val.split('\n'):
				line = line.strip()
				# TODO: recurrence0 determines whether alarm is active if it comes from clock app
				if '=' in line:
					sections = [i.strip() for i in line.split('=')]
					alm[sections[0]] = ast.literal_eval(sections[-1])
				else:
					# TODO: add alarm to list of alarms if set by us
					# First, remove any alarms whose time has passed
					try:
						cookie = str(int(line))
					except ValueError:
						pass
			if cookie in alarm_list:
				hour = int(alm['timeOfDay']) // 60
				minute = int(alm['timeOfDay']) % 60
				now = datetime.now()
				created_date = datetime.fromtimestamp(int(alm['createdDate']))
				alarm_past = False
				if (now-created_date).days > 1:
					alarm_past = True
				elif now.date()>created_date.date():
					if now.hour>hour or (now.hour == hour and now.minute > minute):
						alarm_past = True
				elif hour>created_date.hour or (hour == created_date.hour and minute>created_date.minute):
					if now.hour>hour or (now.hour == hour and now.minute > minute):
						alarm_past = True
				if alarm_past:
					result = subprocess.Popen(["timedclient-qt5 --cancel-event=%s" % cookie], shell=True, stdout=subprocess.PIPE).communicate()
					alarm_list.remove(cookie)
				cookie = None
			timed.alarms.append(alm)
		with open(os.getenv('HOME')+'/.config/saera/alarms', 'w') as alarm_list_file:
			alarm_list_file.write('\n'.join(alarm_list))
	def set_alarm(time,message):
		result = subprocess.Popen(["timedclient-qt5 -r'hour="+str(time.hour)+";minute="+str(time.minute)+";everyDayOfWeek;everyDayOfMonth;everyMonth;' -e'APPLICATION=nemoalarms;TITLE=Alarm;createdDate="+str(int(datetime.now().timestamp()))+";timeOfDay="+str(time.hour*60+time.minute)+";type=clock;alarm;reminder;boot;keepAlive;singleShot;time="+time.strftime("%Y-%m-%d %H:%M")+";'"], shell=True, stdout=subprocess.PIPE).communicate()
		res_str = result[0].splitlines()
		print (res_str)
		cookie = res_str[-1].decode('utf-8').split('cookie is')[-1].strip()
		with open(os.getenv('HOME')+'/.config/saera/alarms', 'a') as alarm_list_file:
			alarm_list_file.write('\n'+cookie)
		# timed.check()

	def set_reminder(time,message,location=None):
		result = subprocess.Popen(["timedclient-qt5 -b'TITLE=button0' -e'APPLICATION=saera;TITLE="+message+(";location="+location if location else "")+";time="+time.strftime("%Y-%m-%d %H:%M")+";'"], shell=True, stdout=subprocess.PIPE).communicate()
		print (result)
		timed.check()

timed.check()

def set_alarm(time, message = "alarm"):
	timed.set_alarm(time,message)

def set_reminder(time,message,location=None):
	return timed.set_reminder(time,message,location)

def run_text(t):
	return app.execute_text(t)

def run_app(s):
	global app
	app = s

def is_playing():
	global activeMediaPlayer
	result = subprocess.Popen(["gdbus",
								"call",
								"-e",
								"-d",
								"org.mpris.MediaPlayer2.jolla-mediaplayer",
								"-o",
								"/org/mpris/MediaPlayer2",
								"-m",
								"org.freedesktop.DBus.Properties.Get",
								"org.mpris.MediaPlayer2.Player",
								"PlaybackStatus"], stdout=subprocess.PIPE).communicate()
	spotresult = subprocess.Popen(["gdbus",
								"call",
								"-e",
								"-d",
								"org.mpris.MediaPlayer2.CuteSpot",
								"-o",
								"/org/mpris/MediaPlayer2",
								"-m",
								"org.freedesktop.DBus.Properties.Get",
								"org.mpris.MediaPlayer2.Player",
								"PlaybackStatus"], stdout=subprocess.PIPE).communicate()
	if not result[0]:
		activeMediaPlayer = "CuteSpot"
		return "Playing" if "Playing" in spotresult[0].decode("UTF-8") else "Paused" if "Paused" in spotresult[0].decode("UTF-8") else "Off" if not spotresult[0] else "Stopped"
	else:
		activeMediaPlayer = "jolla-mediaplayer"
		return "Playing" if "Playing" in result[0].decode("UTF-8") else "Paused" if "Paused" in result[0].decode("UTF-8") else "Stopped"


def pause():
	result = subprocess.Popen(["gdbus",
								"call",
								"-e",
								"-d",
								"org.mpris.MediaPlayer2."+activeMediaPlayer,
								"-o",
								"/org/mpris/MediaPlayer2",
								"-m",
								"org.mpris.MediaPlayer2.Player.Pause"], stdout=subprocess.PIPE).communicate()
	print (result)

def play(song=None):
	if is_playing() in ("Playing", "Paused") and not song:
		result = subprocess.Popen(["gdbus",
								"call",
								"-e",
								"-d",
								"org.mpris.MediaPlayer2."+activeMediaPlayer,
								"-o",
								"/org/mpris/MediaPlayer2",
								"-m",
								"org.mpris.MediaPlayer2.Player.Play"], stdout=subprocess.PIPE).communicate()

	else:
		if is_playing() == "Off":
			os.system("jolla-mediaplayer &")
			time.sleep(8) # for the media player to finish launching
		print(song)
		if song is not None and song in song_title_map:
			f = song_title_map[song]
		else:
			files = subprocess.Popen("find /home/nemo/Music/ -type f -name \*.mp3", shell=True, stdout=subprocess.PIPE).communicate()[0].splitlines()
			f = parse.quote(random.choice(files).decode('utf-8'))
		print ("Playing file://"+f)
		result = subprocess.Popen(["gdbus",
									"call",
									"-e",
									"-d",
									"org.mpris.MediaPlayer2.jolla-mediaplayer",
									"-o",
									"/org/mpris/MediaPlayer2",
									"-m",
									"org.mpris.MediaPlayer2.Player.OpenUri",
									"file://"+f], stdout=subprocess.PIPE).communicate()
		subprocess.Popen(["gdbus",
								"call",
								"-e",
								"-d",
								"org.mpris.MediaPlayer2.jolla-mediaplayer",
								"-o",
								"/org/mpris/MediaPlayer2",
								"-m",
								"org.mpris.MediaPlayer2.Player.Play"], stdout=subprocess.PIPE).communicate()
	print (result)

def identify_song():
	if os.path.exists('/tmp/rec.ogg'):
		os.remove('/tmp/rec.ogg')
	gproc = subprocess.Popen(['gst-launch-0.10 autoaudiosrc ! vorbisenc ! oggmux ! filesink location=/tmp/rec.ogg'], shell=True)
	time.sleep(11)
	gproc.terminate()

	f = open('/tmp/rec.ogg', "rb")
	sample_bytes = os.path.getsize('/tmp/rec.ogg')
	content = f.read()
	f.close()

	http_method = "POST"
	http_uri = "/v1/identify"
	data_type = "audio"
	signature_version = "1"
	timestamp = time.time()

	string_to_sign = http_method+"\n"+http_uri+"\n"+access_key+"\n"+data_type+"\n"+signature_version+"\n"+str(timestamp)
	sign = base64.b64encode(hmac.new(access_secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha1).digest())

	fields = {'access_key':access_key.encode('utf-8'),
	          'sample_bytes':str(sample_bytes).encode('utf-8'),
	          'timestamp':str(timestamp).encode('utf-8'),
	          'signature':sign,
	          'data_type':data_type.encode('utf-8'),
	          "signature_version":signature_version.encode('utf-8')}

	res = post_multipart("ap-southeast-1.api.acrcloud.com", "/v1/identify", fields, {"sample":content})
	print (res)
	result = json.loads(res)
	if result['status']['code']==0: # Success!
		title = result['metadata']['music'][0]['title']
		artists = [i['name'] for i in result['metadata']['music'][0]['artists']]
		if len(artists) == 1:
			artists_string = artists[0]
		else:
			artists = ", ".join(artists[:-1])+" and "+artists[-1]
		if "spotify" in result['metadata']['music'][0]['external_metadata']:
			pv_url = json.loads(urllib2.urlopen("https://api.spotify.com/v1/tracks/"+result['metadata']['music'][0]['external_metadata']['spotify']['track']['id']).read().decode("utf-8"))["preview_url"]
			return "It sounds like "+title+", by "+artists_string+".|"+"spot_preview|"+pv_url
		elif "itunes" in result['metadata']['music'][0]['external_metadata']:
			pv_url = json.loads(urllib2.urlopen("https://itunes.apple.com/lookup?id="+result['metadata']['music'][0]['external_metadata']['itunes']['track']['id']).read().decode("utf-8"))["results"][0]["previewUrl"]
		else:
			return "It sounds like "+title+", by "+artists_string+"."

	elif result['status']['code']==1001:
		return "I don't recognize it."
	else:
		return "I can't find out, the server gave me a "+str(result['status']['code'])+" error."

def play_url(url):
	g = subprocess.Popen(['gst-launch-0.10 playbin2 uri='+url], shell=True)
	g.wait()
	return

def call_phone(num):
	result = subprocess.Popen(["gdbus",
								"call",
								"-e",
								"-d",
								"com.jolla.voicecall.ui",
								"-o",
								"/",
								"-m",
								"com.jolla.voicecall.ui.dial",
								"'"+num+"'"], stdout=subprocess.PIPE).communicate()
	return "true" in result[0].decode("UTF-8")

def check_contact(contact):
	if contact.lower() in contacts:
		c = contacts[contact.lower()]
	elif contact.lower() in firstnames:
		c = contacts[firstnames[contact.lower()]]
	else:
		raise NameError
	if c['hasPhoneNumber']:
		return True
	else:
		raise AttributeError

def call_contact(contact):
	if contact.lower() in contacts:
		c = contacts[contact.lower()]
	elif contact.lower() in firstnames:
		c = contacts[firstnames[contact.lower()]]
	else:
		raise NameError
	if c['hasPhoneNumber']:
		print ("Calling "+c['phoneNumber'])
		result = subprocess.Popen(["gdbus",
									"call",
									"-e",
									"-d",
									"com.jolla.voicecall.ui",
									"-o",
									"/",
									"-m",
									"com.jolla.voicecall.ui.dial",
									"'"+c['phoneNumber']+"'"], stdout=subprocess.PIPE).communicate()
		return "true" in result[0].decode("UTF-8")
	else:
		raise AttributeError

def get_unread_email():
	if has_mail:
		mailconn.execute("VACUUM") # to move messages from the WAL into the main database
		mailcur.execute("SELECT * FROM mailmessages WHERE stamp>'"+(datetime.now()+timedelta(days=-1)).strftime("%Y-%m-%dT%H:%M:%S.000")+"'")
		rows = mailcur.fetchall()
		messages = []
		for row in rows:
			if bin(row[8])[2:][-8]=='0' and bin(row[8])[2:][-10]=='0': # one of those two bits is the read flag
				messages.append({'type':'email','to':row[9],'from':row[4].split(" <")[0].split(" (")[0].replace('"',''),'subject':row[6].split(' [')[0],'content':row[22]})
		return messages
	else:
		return []

class MailFolder:
	def __init__(self):
		self.messages = {}
	def check(self):
		for i in os.listdir(os.getenv("HOME")+"/.qmf/mail/"):
			if not i in self.messages and not "part" in i:
				self.messages[i] = email.message_from_file(open(os.getenv("HOME")+"/.qmf/mail/"+i))

def speak(string):
	global detected
	try:
		is_string = isinstance(string,basestring)
	except NameError:
		is_string = isinstance(string,str)
	if is_string:
		spoken_str = string.split('|')[0]
	else:
		spoken_str = '\n'.join([i[0] for i in string])
	if not os.path.exists("/tmp/espeak_lock"):
		os.system('pactl set-sink-volume 1 %i' % (volume/2))
		os.system('touch /tmp/espeak_lock && espeak --stdout -v +f2 "' + spoken_str.replace(":00"," o'clock").replace("\n",". ").replace(":", " ") + '" |'
				' gst-launch-0.10 -q fdsrc ! wavparse ! audioconvert ! volume volume=4.0 ! alsasink && rm /tmp/espeak_lock && pactl set-sink-volume 1 %i &' % volume)
	detected = False
	return string

def enablePTP():
	pyotherside.send('enablePTP')

def disablePTP():
	pyotherside.send('disablePTP')

def sayRich(spokenMessage, message, img, lat=0, lon=0):
	pyotherside.send('sayRich',message, img, lat, lon)
	speak(spokenMessage)

def check_can_listen():
	return not os.path.exists("/tmp/espeak_lock")

def quit():
	conn.close()
	client.stop()
	client.disconnect()
	client.join()
	jproc.terminate()
	if os.path.exists('/tmp/saera'):
		shutil.rmtree('/tmp/saera')
