#! /usr/bin/end python

import os, sys
import email
import subprocess
import sqlite3

global app
app = None

memory_path = os.getenv('HOME')+'/.saera_memory.db'
if not os.path.exists(memory_path):
	conn = sqlite3.connect(memory_path)
	conn.row_factory = sqlite3.Row
	cur = conn.cursor()
	cur.execute('CREATE TABLE Variables (Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, VarName TEXT NOT NULL, Value TEXT NOT NULL, UpdateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
	cur.execute('CREATE TABLE Locations (Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, LocName TEXT NOT NULL COLLATE NOCASE, Zip TEXT, Latitude REAL, Longitude REAL, Timezone REAL, UpdateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')

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

def set_alarm(time, message = "alarm"):
	# TODO
	pass

def run_text(t):
	return app.execute_text(t)

def run_app(s):
	global app
	app = s
	while True:
		# try:
			inp = raw_input("> ")
			result = run_text(inp)
			print result
		# except Exception as e:
		# 	print "Error: ", e.message
		# 	quit()

def is_playing():
	return False


def pause():
	pass

def play():
	pass

def call_phone(num):
	pass

class MailFolder:
	def __init__(self):
		self.messages = {}
	def check(self):
		for i in os.listdir(os.getenv("HOME")+"/.qmf/mail/"):
			if not i in self.messages and not "part" in i:
				self.messages[i] = email.message_from_file(open(os.getenv("HOME")+"/.qmf/mail/"+i))

def speak(string):
	os.system('say -v Vicki "' + string + '"')
	return string

def quit():
	print "Bye!"
	conn.close()
	sys.exit(0)