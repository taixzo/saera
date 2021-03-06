#! /usr/bin/env python

import os, sys
import email
import subprocess
import sqlite3
import rumps
from pync import Notifier

global app
app = None

if sys.version_info[0]==3:
	raw_input = input

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

def set_alarm(time, message = "alarm"):
	# TODO
	pass

def set_reminder(time, message, location=None):
	os.system("echo 'echo \""+message.replace('"','\\"').replace("'","\\'")+"\" | wall' | at "+time.strftime("%H:%M"))

def run_text(t):
	return app.execute_text(t)

class AwesomeStatusBarApp(rumps.App):
    def __init__(self,name,icon):
        super(AwesomeStatusBarApp, self).__init__("Saera",icon=icon)
        self.menu = ["Speak", "Enter text"]

    inp = rumps.Window(message="Hi",title="Saera",default_text="DEFAULT", dimensions=(250,50))
    inp.icon ="resources/saera.png"

    @rumps.clicked("Speak")
    def speak(self, _):
        pass

    @rumps.clicked("Enter text")
    def inputtext(self, sender):
        inp_text = unicode(self.inp.run().text)
        print inp_text
        result = run_text(inp_text)
        print result
        Notifier.notify(result, title="Saera", appIcon="resources/saera.png")
        os.system('say -v Victoria '+result)
        # rumps.notification("Hello", "btitle", result, sound=True)

def run_app(s):
	global app
	app = s
	AwesomeStatusBarApp("Saera",icon="resources/saera.png").run()
	while True:
		# try:
			inp = raw_input("> ")
			result = run_text(inp)
			try:
				is_string = isinstance(result,basestring)
			except NameError:
				is_string = isinstance(result,str)
			if is_string:
				print (result)
			else:
				for i in result:
					print (i[0])
			# print (result)
		# except Exception as e:
		# 	print "Error: ", e.message
		# 	quit()

def is_playing():
	return False


def pause():
	pass

def play(song=None):
	pass

def call_phone(num):
	pass

def check_contact(contact):
	return True # How to get contacts on OSX?

def call_contact(contact):
	pass

def get_unread_email():
	return []

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
	print ("Bye!")
	conn.close()
	sys.exit(0)
