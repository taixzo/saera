#! /usr/bin/env python

import os, sys
import email
import subprocess
import sqlite3
import pyjulius
import time

import gtk
from gtk import Window, Button, Widget, VBox, Label
import gobject

import hildon
from portrait import FremantleRotation
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

app_name = "Saera"
app_version = "2.0"
initial_mode = FremantleRotation.AUTOMATIC

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

f = __file__.split('fremantle_hw.py')[0]

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
client.send("TERMINATE\n")

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
	run_text(text=res)
	return res

def set_alarm(time, message = "alarm"):
	# TODO
	event = alarm.Event()
	event.appid = 'saera'
	event.message = message
	event.alarm_time = float(time.strftime("%s"))

	action_stop, action_snooze = event.add_actions(2)
	action_stop.label = 'Stop'
	action_stop.flags |= alarm.ACTION_WHEN_RESPONDED | alarm.ACTION_TYPE_NOP

	action_snooze.label = 'Snooze'
	action_snooze.flags |= alarm.ACTION_WHEN_RESPONDED | alarm.ACTION_TYPE_SNOOZE

	cookie = alarm.add_event(event)

def set_reminder(time, message, location=None):
	event = alarm.Event()
	event.appid = 'saera'
	event.message = message
	event.alarm_time = float(time.strftime("%s"))

	action_stop, action_snooze = event.add_actions(2)
	action_stop.label = 'Stop'
	action_stop.flags |= alarm.ACTION_WHEN_RESPONDED | alarm.ACTION_TYPE_NOP

	action_snooze.label = 'Snooze'
	action_snooze.flags |= alarm.ACTION_WHEN_RESPONDED | alarm.ACTION_TYPE_SNOOZE

	cookie = alarm.add_event(event)

def open_url(widget,url):
	os.system('dbus-send --system --type=method_call --dest=com.nokia.osso_browser /com/nokia/osso_browser/request com.nokia.osso_browser.load_url string:"'+url+'"')

def run_text(widget=None,event=None,data=None, text=None):
	if text is None:
		text = widget.get_text()
		widget.set_text("")
	if text.strip()=="":
		return

	lab = Label(text)
	lab.set_alignment(xalign=0.95,yalign=0.5)
	app.vbox.pack_start(lab,False,True,30)
	lab.show()

	res = app.execute_text(text)
	if isinstance(res,basestring):
		reslab = Label("<b>"+res+"</b>")
		reslab.set_use_markup(True)
		reslab.set_alignment(xalign=0.05, yalign=0.5)
		app.vbox.pack_start(reslab,False,True,30)
		reslab.show()
	else:
		reslab = None
		for i in res:
			if len(i)==1:
				rlab = Label("<b>"+i[0]+"</b>")
				rlab.set_use_markup(True)
				app.vbox.pack_start(rlab,False,True,30)
			else:
				rlab = hildon.GtkButton(gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT)
				rlab.set_label("<b>"+i[0]+"</b>")
				label = rlab.child
				label.props.wrap = True
				label.props.width_chars = 40
				label.set_use_markup(True)
				rlab.connect("clicked",open_url,i[1])
				app.vbox.pack_start(rlab,False,True,0)
			if not reslab:
				reslab = rlab
			rlab.set_alignment(xalign=0.05, yalign=0.5)
			rlab.show()
		res = '\n'.join([i[0] for i in res])
	os.system('espeak -v +f2 "' + res.replace(":00"," o'clock").replace("\n",". ") + '" &')

	gobject.timeout_add(500, app.pannable_area.scroll_to_child,reslab)

def run_app(s):
	global app
	app = s

	program = hildon.Program.get_instance()
	window = hildon.StackableWindow()
	rotation_object = FremantleRotation(app_name, window, app_version, initial_mode)
	program.add_window(window)
	window.set_title("Saera")

	window.connect("destroy", gtk.main_quit)
	bigvbox = VBox()
	vbox = VBox()
	button = Button("Listen")
	button.connect("clicked", listen)

	pannable_area = hildon.PannableArea()

	input = gtk.Entry()
	welcome_message = Label("<b>How may I help you?</b>")
	welcome_message.set_use_markup(True)
	welcome_message.set_alignment(xalign=0.05, yalign=0.5)

	input.connect('activate', run_text)

	app.vbox = vbox
	app.pannable_area = pannable_area

	# buttona.connect_object("clicked", Widget.destroy, window)
	# welcome_message.connect_object("clicked", Widget.destroy, window)
	pannable_area.add_with_viewport(vbox)
	bigvbox.pack_start(pannable_area,True,True,0)
	bigvbox.pack_start(button,False,True,5)
	bigvbox.pack_start(input,False,True,5)

	vbox.pack_start(welcome_message,False,True,30)
	window.add(bigvbox)
	window.show_all()
	gtk.main()

	while False:
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

def is_playing():
	return False


def pause():
	os.system('dbus-send --dest=com.nokia.mafw.renderer.Mafw-Gst-Renderer-Plugin.gstrenderer /com/nokia/mafw/renderer/gstrenderer com.nokia.mafw.renderer.pause')

def play():
	os.system('dbus-send --dest=com.nokia.mafw.renderer.Mafw-Gst-Renderer-Plugin.gstrenderer /com/nokia/mafw/renderer/gstrenderer com.nokia.mafw.renderer.play')

def call_phone(num):
	os.system('dbus-send --system --type=method_call --print-reply --dest=com.nokia.csd.Call /com/nokia/csd/call com.nokia.csd.Call.CreateWith string:"'+num+'" uint32:0')

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
