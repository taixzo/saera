#! /usr/bin/end python

import pyotherside
import os
import email
import subprocess

global app
app = None

memory_path = os.getenv('HOME')+'/.saera_memory.db'
memory_path = os.getenv('HOME')+'/.saera_memory.db'
if not os.path.exists(memory_path):
	conn = sqlite3.connect(memory_path)
	conn.row_factory = sqlite3.Row
	cur = conn.cursor()
	cur.execute('CREATE TABLE Variables (Id INT NOT NULL PRIMARY KEY AUTOINCREMENT, VarName TEXT NOT NULL, Value TEXT NOT NULL, UpdateTime DATETIME DEFAULT CURRENT_TIMESTAMP')
	cur.execute('CREATE TABLE Locations (Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, LocName TEXT NOT NULL, Zip TEXT, Latitude REAL, Longitude REAL, UpdateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
	cur.execute('CREATE TABLE People (Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, Name TEXT NOT NULL COLLATE NOCASE, Description TEXT, Born DATE, Died DATE, Profession TEXT')
else:
	conn = sqlite3.connect(memory_path)
	conn.row_factory = sqlite3.Row
	cur = conn.cursor()

def set_alarm(time, message = "alarm"):
	# TODO
	pass

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

class MailFolder:
	def __init__(self):
		self.messages = {}
	def check(self):
		for i in os.listdir(os.getenv("HOME")+"/.qmf/mail/"):
			if not i in self.messages and not "part" in i:
				self.messages[i] = email.message_from_file(open(os.getenv("HOME")+"/.qmf/mail/"+i))

def speak(string):
	os.system('espeak --stdout -v +f2 "' + string + '" | gst-launch-0.10 -v fdsrc ! wavparse ! audioconvert ! alsasink &')
	return string