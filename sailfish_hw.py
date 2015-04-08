#! /usr/bin/end python

import pyotherside
import os
import email
import subprocess
import sqlite3

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

class timed:
	alarms = []

	def check():
		result = subprocess.Popen(["timedclient-qt5", "--info"], stdout=subprocess.PIPE).communicate()
		rawvals = result[0].decode("UTF-8").split("Cookie ")
		for val in rawvals:
			alm = {}
			for line in val.split('\n'):
				line = line.strip()
				if '=' in line:
					sections = [i.strip() for i in line.split('=')]
					alm[sections[0]] = ast.literal_eval(sections[-1])
				else:
					pass
			timed.alarms.append(alm)
	def set_alarm(time,message):
		# result = subprocess.Popen(["timedclient-qt5", "-b'TITLE=button0'", "-e'APPLICATION=saera;TITLE=Alarm;time="+time.strftime("%Y-%m-%d %H:%M")+"'"], stdout=subprocess.PIPE).communicate()
		# For some reason, subprocess.Popen returns an error for this (probably because of how timedclient-qt5 mangles argv), so we use os.system instead
		result = os.system("timedclient-qt5 -b'TITLE=button0' -e'APPLICATION=saera;TITLE=Alarm;time="+time.strftime("%Y-%m-%d %H:%M")+"'")
		# print ("timedclient-qt5", "-b'TITLE=button0'", "-e'APPLICATION=saera;TITLE=Alarm;time="+time.strftime("%Y-%m-%d %H:%M")+"'")
		timed.check()

def set_alarm(time, message = "alarm"):
	timed.set_alarm(time,message)
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
	os.system('espeak --stdout -v +f2 "' + string.replace(":00"," o'clock") + '" | gst-launch-0.10 -v fdsrc ! wavparse ! audioconvert ! alsasink &')
	return string