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

import ast # for safely parsing timed stuff

global app
app = None

memory_path = os.getenv('HOME')+'/.saera_memory.db'
if not os.path.exists(memory_path):
	conn = sqlite3.connect(memory_path)
	conn.row_factory = sqlite3.Row
	cur = conn.cursor()
	cur.execute('CREATE TABLE Variables (Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, VarName TEXT NOT NULL, Value TEXT NOT NULL, UpdateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
	cur.execute('CREATE TABLE Locations (Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, LocName TEXT NOT NULL COLLATE NOCASE, Zip TEXT, Latitude REAL, Longitude REAL, Timezone REAL, UpdateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
	cur.execute('CREATE TABLE People (Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, Name TEXT NOT NULL COLLATE NOCASE, Description TEXT, Born DATE, Died DATE, Gender TEXT, Profession TEXT)')

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

jproc = subprocess.Popen([f+'julius/julius.arm','-module','-gram',f+'julius/saera','-h',f+'julius/hmmdefs','-hlist',f+'julius/tiedlist','-input','mic','-tailmargin','800','-rejectshort','600'],stdout=subprocess.PIPE)
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

def listen():
	print ("Listening...")
	# purge message queue
	client.send("TERMINATE\n")
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
				result.words = ['*mumble*']
				break
		except Queue.Empty:
			continue
	res = " ".join([i.word.lower() for i in result.words])
	res = res[0].upper()+res[1:]
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
		result = subprocess.Popen(["timedclient-qt5 -r'hour="+str(time.hour)+";minute="+str(time.minute)+";everyDayOfWeek;everyDayOfMonth;everyMonth;' -e'APPLICATION=nemoalarms;TITLE=Alarm;createdDate="+str(int(datetime.now().timestamp()))+";timeOfDay="+str(time.hour*60+time.minute)+";type=clock;alarm;reminder;boot;keepAlive;time="+time.strftime("%Y-%m-%d %H:%M")+";'"], shell=True, stdout=subprocess.PIPE).communicate()
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
	return "Playing" if "Playing" in result[0].decode("UTF-8") else "Paused" if "Paused" in result[0].decode("UTF-8") else "Stopped"


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

def play():
	result = subprocess.Popen(["gdbus",
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
	try:
		is_string = isinstance(string,basestring)
	except NameError:
		is_string = isinstance(string,str)
	if is_string:
		spoken_str = string
	else:
		spoken_str = '\n'.join([i[0] for i in string])
	os.system('espeak --stdout -v +f2 "' + spoken_str.replace(":00"," o'clock").replace("\n",". ") + '" | gst-launch-0.10 -v fdsrc ! wavparse ! audioconvert ! alsasink &')
	return string

def quit():
	conn.close()
	client.stop()
	client.disconnect()
	client.join()
	jproc.terminate()