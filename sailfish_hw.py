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
from streetnames import get_street_names
import alsaaudio, audioop
import re
from ID3 import ID3
try:
	import urllib.parse as parse
except:
	import urllib as parse
import guessing

import ast # for safely parsing timed stuff

global app
app = None

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

mailconn = sqlite3.connect('/home/nemo/.qmf/database/qmailstore.db')
mailcur = mailconn.cursor()

f = __file__.split('sailfish_hw.py')[0]

# terminate any pre-existing julius processes
p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
out, err = p.communicate()
for line in out.decode('UTF-8').splitlines():
	if 'julius.arm' in line:
		pid = int(line.split(None, 1)[0])
		os.kill(pid, 9)

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
		l = line.decode('utf-8').split(", file://")
		file = l[-1]
		# tracker-sparql uses commas in results and doesn't escape them. As there
		# seems to be no workaround, we assume that all URLs are file:// urls and
		# no artists contain commas.
		index_of_last_comma = l[0].rindex(',')
		artist = l[0][index_of_last_comma+1:]
		title = l[0][:index_of_last_comma]
		if title.count(' - ')==1:
			name_artist, title = title.split(' - ')
		title = regex.sub('', title).strip()
		lst.append(title)
		print (title)
		song_title_map[title.lower()] = file

contacts = {}
firstnames = {}
streetnames = []

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
				print (fulls[-1])
			else:
				contacts[first] = {'hasPhoneNumber':hasPhoneNumber, 'contactId':contactId}
				firstnames[first] = first
				print (firsts[-1])
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
	espeak2julius.create_grammar(list(contacts), 'contacts', 'contacts')
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
jproc = subprocess.Popen([f+'julius/julius.arm','-module','-gram',f+'julius/saera', '-gram', '/home/nemo/.cache/saera/musictitles', '-gram', '/home/nemo/.cache/saera/contacts', '-gram', '/home/nemo/.cache/saera/addresses','-h',f+'julius/hmmdefs','-hlist',f+'julius/tiedlist','-input','mic','-tailmargin','800','-rejectshort','600'],stdout=subprocess.PIPE)
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

def pause_daemons():
	global daemons_running
	daemons_running = False

def resume_daemons():
	global daemons_running
	daemons_running = True
	e.set()

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

def watch_mic(e):
	inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NONBLOCK)
	inp.setchannels(1)
	inp.setrate(8000)
	inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
	inp.setperiodsize(160)
	while True:
		l,data = inp.read()
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
prox_thread = threading.Thread(target=watch_proximity, args=(e,))
mic_thread = threading.Thread(target=watch_mic, args=(e2,))
prox_thread.start()
mic_thread.start()

def listen():
	print ("Listening...")
	# purge message queue
	time.sleep(0.6)
	client.send("RESUME\n")
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
		except Queue.Empty:
			continue
	numbers = {'zero':'0','oh':'0','one':'1','two':'2','three':'3','four':'4','five':'5','six':'6','seven':'7','eight':'8','nine':'9'}
	words = [i.word.lower() for i in result.words]
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
	res = " ".join(words)
	res = res[0].upper()+res[1:]
	client.send("TERMINATE\n")
	return res

class timed:
	alarms = []

	def check():
		result = subprocess.Popen(["timedclient-qt5", "--info"], stdout=subprocess.PIPE).communicate()
		rawvals = result[0].decode("UTF-8").split("Cookie ")
		for val in rawvals:
			alm = {}
			for line in val.split('\n'):
				line = line.strip()
				# TODO: recurrence0 determines whether alarm is active if it comes from clock app
				if '=' in line:
					sections = [i.strip() for i in line.split('=')]
					alm[sections[0]] = ast.literal_eval(sections[-1])
				else:
					pass
			timed.alarms.append(alm)
	def set_alarm(time,message):
		result = subprocess.Popen(["timedclient-qt5 -r'hour="+str(time.hour)+";minute="+str(time.minute)+";everyDayOfWeek;everyDayOfMonth;everyMonth;' -e'APPLICATION=nemoalarms;TITLE=Alarm;createdDate="+str(int(datetime.now().timestamp()))+";timeOfDay="+str(time.hour*60+time.minute)+";type=clock;alarm;reminder;boot;keepAlive;singleShot;time="+time.strftime("%Y-%m-%d %H:%M")+";'"], shell=True, stdout=subprocess.PIPE).communicate()
		timed.check()

	def set_reminder(time,message,location=None):
		result = subprocess.Popen(["timedclient-qt5 -b'TITLE=button0' -e'APPLICATION=saera;TITLE="+message+(";location="+location if location else "")+";time="+time.strftime("%Y-%m-%d %H:%M")+";'"], shell=True, stdout=subprocess.PIPE).communicate()
		print (result)
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
	return "Playing" if "Playing" in result[0].decode("UTF-8") else "Paused" if "Paused" in result[0].decode("UTF-8") else "Off" if not result[0] else "Stopped"


def pause():
	result = subprocess.Popen(["gdbus",
								"call",
								"-e",
								"-d",
								"org.mpris.MediaPlayer2.jolla-mediaplayer",
								"-o",
								"/org/mpris/MediaPlayer2",
								"-m",
								"org.mpris.MediaPlayer2.Player.Pause"], stdout=subprocess.PIPE).communicate()
	print (result)

def play(song=None):
	if is_playing() in ("Playing", "Paused") and song is None:
		result = subprocess.Popen(["gdbus",
								"call",
								"-e",
								"-d",
								"org.mpris.MediaPlayer2.jolla-mediaplayer",
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
	mailconn.execute("VACUUM") # to move messages from the WAL into the main database
	mailcur.execute("SELECT * FROM mailmessages WHERE stamp>'"+(datetime.now()+timedelta(days=-1)).strftime("%Y-%m-%dT%H:%M:%S.000")+"'")
	rows = mailcur.fetchall()
	messages = []
	for row in rows:
		if bin(row[8])[2:][-8]=='0' and bin(row[8])[2:][-10]=='0': # one of those two bits is the read flag
			messages.append({'type':'email','to':row[9],'from':row[4].split(" <")[0].split(" (")[0].replace('"',''),'subject':row[6].split(' [')[0],'content':row[22]})
	return messages

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
		spoken_str = string
	else:
		spoken_str = '\n'.join([i[0] for i in string])
	if not os.path.exists("/tmp/espeak_lock"):
		os.system('touch /tmp/espeak_lock && espeak --stdout -v +f2 "' + spoken_str.replace(":00"," o'clock").replace("\n",". ") + '" | gst-launch-0.10 -q fdsrc ! wavparse ! audioconvert ! alsasink && rm /tmp/espeak_lock &')
	detected = False
	return string

def enablePTP():
	pyotherside.send('enablePTP')

def disablePTP():
	pyotherside.send('disablePTP')

def sayRich(spokenMessage, message, img, lat=0, lon=0):
	pyotherside.send('sayRich',message, img, lat, lon)
	speak(spokenMessage)

def quit():
	conn.close()
	client.stop()
	client.disconnect()
	client.join()
	jproc.terminate()
