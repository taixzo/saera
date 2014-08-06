#!/usr/bin/python

import saera_processing
#import gtk
#import pango
#import cairo
#import pangocairo

from PySide import QtGui, QtCore
import functools

import sys
import os
#import gobject
import math
# import gobject
import pygst
import urllib2
import email
import time
import commands
from subprocess import PIPE, Popen
from threading import Thread
from Queue import Queue, Empty

try:
	import json
except ImportError:
	import simplejson as json

QT = True

pygst.require('0.10')
if not QT:
	gobject.threads_init()
import gst

# Absolute path tweak - thanks MartinK!
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
	import hildon
	from portrait import FremantleRotation
	app_name = "Saera"
	app_version = "1.0"
	initial_mode = FremantleRotation.AUTOMATIC
except ImportError:
	pass

ON_POSIX = 'posix' in sys.builtin_module_names

def enqueue_output(out, queue):
	for line in iter(out.readline, ''):
		queue.put(line)
	out.close()

pulsing = False
rot_amount = 0
WIDTH = 0
HEIGHT = 0
photo = None
able_to_listen = True

# Possible values:
#	"always": always use Google Voice for speech recognition
#	"unrecognized": use Google Voice when pocketsphinx+saera_processing can't tell what you meant
#	"never": never use Google Voice for processing
settings = {}
settings['use_google_voice'] = "unrecognized"
settings['language'] = 'english'
settings['use_answers_com'] = 'yes'
lang = "en"
# Levels:
#	0: No accuracy. User is probably somewhere on Earth.
#	1: Very low accuracy, using geoip on cellular connection - accurate to within a thousand miles or so
#	2: Medium accuracy, using geoip with wifi connection - accurate to within 10 miles
#	3: High accuracy, using GPS - accurate to within 20 feet
POSITION_ACCURACY = 0
gv_api_url='http://www.google.com/speech-api/v1/recognize?lang='+lang+'-'+lang+'&client=chromium'
ipinfodb_api_key = '799619bbf0ddff5c7b3897e12a0289849103af68e7bf6e348db653dba1ced573'
SAMPLE_RATE = 16000
try:
	parsed_settings = json.loads(open(os.getenv('HOME')+'/.saera').read())
	for i in parsed_settings:
		settings[i] = parsed_settings[i]
	__import__("sentences.sentences_"+settings['language'])
	saera_processing.sent = sys.modules["sentences.sentences_"+settings['language']]
except IOError:
	open(os.getenv('HOME')+'/.saera', 'w').write(json.dumps(settings))


try:
	os.mkdir('/tmp/saera')
except OSError:
	pass

def get_ip_location():
	global POSITION_ACCURACY
	if POSITION_ACCURACY<3:
		try:
			response = urllib2.urlopen("http://api.ipinfodb.com/v3/ip-city/?key="+ipinfodb_api_key).read()
			status, huh, ip, cc, country, state, city, zip, lat, lon, tz = response.split(';')
			settings['state'] = state
			settings['city'] = city
			settings['zip'] = zip
			settings['lat'] = lat
			settings['lon'] = lon
			saera_processing.location = (lat, lon)
			POSITION_ACCURACY = 2
		except urllib2.URLError:
			# Probably not connected to internet
			pass

def get_geo_location():
	global POSITION_ACCURACY
	if POSITION_ACCURACY<3:
		try:
			import location
			control = location.GPSDControl.get_default()
			device = location.GPSDevice()
			control.set_properties(preferred_method=location.METHOD_ACWP)
			def on_changed(device, user_data):
				if not device:
					return
				if device.fix:
					if device.fix[1] & location.GPS_DEVICE_LATLONG_SET:
						settings['lat'], settings['lon'] = device.fix[4:6]
						saera_processing.location = (lat, lon)
					print "horizontal accuracy: %f meters" % (device.fix[6] / 100)
					POSITION_ACCURACY = 2
			device.connect("changed", on_changed)
			control.start()
		except ImportError:
			get_ip_location()

class MailFolder:
	def __init__(self, foldername, foldertype):
		self.foldername = foldername
		self.folders = []
		self.name = foldername.split("__")[0]
		self.domain = foldername.split("__")[1].replace("_", ":")
		self.messages = []
		self.foldertype = foldertype
	def check(self):
		try:
			messages = os.listdir('/home/user/.modest/cache/mail/'+self.foldertype+'/'+self.foldername+'/folders/INBOX/')
			unread = []
			for i in messages:
				if not i in self.messages:
					unread.append(email.message_from_file(open('/home/user/.modest/cache/mail/'+self.foldertype+'/'+self.foldername+'/folders/INBOX/'+i)))
			self.messages = messages
			return unread
		except OSError:
			return []
	def all(self):
		return [email.message_from_file(open('/home/user/.modest/cache/mail/'+self.foldertype+'/'+self.foldername+'/folders/INBOX/'+i)) for i in self.messages[:10]]

class Saera:
	def __init__(self):
		self.imap_mailfolders = []
		self.pop_mailfolders = []
		self.ims = []
		self.lines = [['What can I help you with?',False]]
		try:
			program = hildon.Program.get_instance()
			self.win = hildon.StackableWindow()
			rotation_object = FremantleRotation(app_name, self.win, app_version, initial_mode)
			program.add_window(self.win)
		except:
			try:
				self.win = gtk.Window()
				print "No hildon win"
			except:
				print "Using QT"
				self.app = QtGui.QApplication(sys.argv)
				self.win = QtGui.QWidget()
				self.win.setWindowTitle("Saera")
				# self.win.setWindowIcon(QtGui.QIcon('80x80/saera.png'))
				self.win.show()
				global QT
				QT = True
		if not QT:
			self.win.set_size_request(400, 550)
			self.win.set_title("Saera")
			self.vbox = gtk.VBox()
			self.win.add(self.vbox)
			self.input = gtk.Entry()
			self.darea = gtk.DrawingArea()
			self.vbox.pack_start(self.input, False, True, 0)
			self.vbox.pack_start(self.darea, True, True, 0)

			self.darea.add_events(gtk.gdk.EXPOSURE_MASK
										| gtk.gdk.BUTTON_PRESS_MASK
										| gtk.gdk.BUTTON_RELEASE_MASK
										| gtk.gdk.POINTER_MOTION_MASK
										| gtk.gdk.POINTER_MOTION_HINT_MASK)

			self.input.connect('activate', self.run_saera)
			self.darea.connect("expose-event", self.expose_event)
			self.darea.connect("button-press-event", self.button_press_event)

			try:
				self.bgimage = cairo.ImageSurface.create_from_png("saera_bg.png")
				self.micimage = cairo.ImageSurface.create_from_png("siri_mic.png")
				self.micpulse = cairo.ImageSurface.create_from_png("siri_mic_spinner.png")
				self.cbgimage = cairo.ImageSurface.create_from_png("saera_chat_bg.png")
			except Exception, e:
				print e.message
				sys.exit(1)

			self.win.show_all()
			#self.pixmap = gtk.gdk.Pixmap(self.darea.window, *self.darea.window.get_size(), depth=-1)

			if not QT:
				gobject.timeout_add(500, self.check_proximity_sensor)
				# gobject.timeout_add(10000, self.check_mail)
				gobject.timeout_add(60000, self.check_mail)
			else:
				t1 = QtCore.QTimer()
				t1.singleShot(500, self.check_proximity_sensor)
				t2 = QtCore.QTimer()
				t2.singleShot(60000, self.check_mail)

			self.win.connect('destroy', gtk.main_quit)
		else:
			self.vbox = QtGui.QVBoxLayout()
			self.win.setLayout(self.vbox)
			self.input = QtGui.QLineEdit()
			self.vbox.addWidget(self.input)
			class canvas(QtGui.QWidget):
				def __init__(self):
					super (canvas, self).__init__()
					self.initUI()
				def initUI(self):
					self.show()
				def paintEvent(self, event):
					self.expose_event(self, event)
			self.darea = canvas()
			self.darea.expose_event = self.expose_event
			self.vbox.addWidget(self.darea)

			self.input.returnPressed.connect(self.run_saera)

			try:
				self.bgimage = QtGui.QPixmap()
				self.micimage = QtGui.QPixmap()
				self.micpulse = QtGui.QPixmap()
				self.cbgimage = QtGui.QPixmap()
				self.bgimage.load("saera_bg.png")
				self.micimage.load("siri_mic.png")
				self.micpulse.load("siri_mic_spinner.png")
				self.cbgimage.load("saera_chat_bg.png")
			except Exception, e:
				print e.message
				sys.exit(1)
			pass

		self.init_gst()
		self.init_mail()

		get_ip_location()
		get_geo_location()
		
		# Commented out because there is a bug in the sqlite line that I can't find.
		# gobject.timeout_add(10000, self.check_texts)

		self.current_message = None

		self.mod = Popen(['python', '/opt/modrana/modrana.py', '--return-current-coordinates'], stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
		self.q = Queue()
		self.t = Thread(target=enqueue_output, args=(self.mod.stdout, self.q))
		self.t.daemon = True # thread dies with the program
		self.t.start()

	def expose_event(self, widget, event):
		global WIDTH, HEIGHT
		if not QT:
			cr = widget.window.cairo_create()

			cr.set_line_width(2)
			cr.set_source_rgb(0.7, 0.2, 0.0)

			w = widget.allocation.width
			h = widget.allocation.height
			WIDTH, HEIGHT = w, h

			pat = cairo.SurfacePattern(self.bgimage)
			pat.set_extend (cairo.EXTEND_REPEAT)
			cr.set_source(pat)
			cr.paint()

			surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w,h*4)
			cra = cairo.Context(surface)
			pat = cairo.SurfacePattern(self.cbgimage)
			pat.set_extend (cairo.EXTEND_REPEAT)
			y = 0
			for i in self.lines:
				cra.set_source(pat)

				pangocairo_context = pangocairo.CairoContext(cra)
				pangocairo_context.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
				layout = pangocairo_context.create_layout()
				fontname = "Arial"
				font = pango.FontDescription(fontname + " 15")
				layout.set_font_description(font)
				layout.set_width(pango.SCALE * (w-40))

				layout.set_text(i[0])
				height = layout.get_size()[1]/pango.SCALE


				cra.move_to(20,y)
				cra.line_to(w-20,y)
				cra.arc(w-20,y+10,10,3*math.pi/2,math.pi*2)
				cra.line_to(w-10,y+height)
				if i[1]:
					cra.line_to(w,y+height+10)
					cra.line_to(20,y+height+10)
					cra.arc(20,y+height,10,math.pi/2,math.pi)
				else:
					cra.arc(w-20,y+height,10,0,math.pi/2)
					cra.line_to(0,y+height+10)
					cra.line_to(10,y+height)
				cra.line_to(10,y+10)
				cra.arc(20,y+10,10,math.pi,3*math.pi/2)
				cra.fill_preserve()
				cra.set_source_rgb(0.8,0.8,0.8)
				cra.stroke()

				cra.set_source_rgb(1,1,1)
				cra.save()
				cra.translate(20,y+5)
				pangocairo_context.update_layout(layout)
				pangocairo_context.show_layout(layout)
				cra.restore()

				y += height+20
			cr.set_source_surface(surface, 0, -max(0, y-(h-128)))
			cr.paint()

			cr.set_source_surface(self.micimage,w/2-64,h-128)
			cr.save()
			cr.translate(w/2, h-64)
			cr.rectangle(-64,-64,128,128)
			cr.fill()
			if pulsing:
				cr.rotate(rot_amount)
				cr.set_source_surface(self.micpulse,-64,-64)
				cr.rectangle(-64,-64,128,128)
				cr.fill()
			cr.restore()
			
			if photo:
				cr.set_source_surface(photo,0,0)
				cr.rectangle(0,0,w,h)
				cr.fill()
		else:
			qp = QtGui.QPainter()
			qp.begin(widget)

			# Todo
			# cr.set_line_width(2)
			qp.setPen(QtGui.QColor(179, 51, 0))

			w = widget.size().width()
			h = widget.size().height()
			WIDTH, HEIGHT = w, h

			bw = self.bgimage.width()
			bh = self.bgimage.height()
			for i in range(0,int(w/bw)+1):
				for j in range(0,int(h/bh)+1):
					qp.drawPixmap(i*bw, j*bh, self.bgimage)

			font = QtGui.QFont('Decorative', 10)
			qp.setFont(font)
			fm = QtGui.QFontMetrics(font)
			y = 0
			for i in self.lines:
				qp.setPen(QtGui.QColor(255,255,255))
				height = fm.boundingRect(20, 5, w-40, h, QtCore.Qt.AlignLeft | QtCore.Qt.TextWordWrap, i[0]).height()


				'''
				# cra.move_to(20,y)
				qp.drawLine(20, y, w-20,y)
				qp.drawArc(w-30,y,20,20, 90*16, -90*16)
				# cra.arc(w-20,y+10,10,3*math.pi/2,math.pi*2)
				qp.drawLine(w-10,y+10,w-10,y+height)
				if i[1]:
					qp.drawLine(w-10,y+height,w,y+height+10)
				# 	qp.drawLine(w,y+height+10,20,y+height+10)
				# 	# cra.arc(20,y+height,10,math.pi/2,math.pi)
				else:
					# cra.arc(w-20,y+height,10,0,math.pi/2)
					qp.drawArc(w-10,y+height-10,-20,20,0,-90*16)
					qp.drawLine(w-20,y+height+10,20,y+height+10)
					qp.drawLine(20,y+height+10,0,y+height+20)
					qp.drawLine(0,y+height+20,10,y+height)
				qp.drawLine(10,y+height,10,y+10)
				qp.drawArc(10,y,20,20,180*16,-90*16)
				# cra.arc(20,y+10,10,math.pi,3*math.pi/2)
				# cra.fill_preserve()
				# cra.set_source_rgb(0.8,0.8,0.8)
				# cra.stroke()'''

				cra = QtGui.QPainterPath()
				cra.moveTo(20,y)
				cra.lineTo(w-20,y)
				cra.arcTo(w-30,y,20,20,90,-90)
				cra.lineTo(w-10,y+height)
				if i[1]:
					cra.lineTo(w,y+height+10)
					cra.lineTo(20,y+height+10)
					cra.arcTo(10,y+height-10,20,20,-90,-90)
				else:
					cra.arcTo(w-10,y+height-10,-20,20,180,90)
					cra.lineTo(0,y+height+10)
					cra.lineTo(10,y+height)
				cra.lineTo(10,y+10)
				cra.arcTo(10,y,20,20,180,-90)
				qp.fillPath(cra, QtGui.QColor(255,255,255,128))
				qp.drawPath(cra)
				# cra.set_source_rgb(0.8,0.8,0.8)
				# cra.stroke()


				qp.translate(0,y+5)
				qp.drawText(QtCore.QRectF(20, 5, w-40, h), QtCore.Qt.AlignLeft | QtCore.Qt.TextWordWrap, i[0])


				y += height+20

			qp.drawPixmap(w/2-64,h-128,self.micimage)
			if pulsing:
				qp.translate(w/2,h-64)
				qp.rotate(rot_amount)
				qp.drawPixmap(-64,-64,self.micpulse)

			# ...

			qp.end()

	def button_press_event(self, widget, event):
		if WIDTH/2-64<event.x<WIDTH/2+64 and event.y>HEIGHT-128:
			# This looks nice, but redrawing while recording takes up
			# way too much CPU.
			#global pulsing, rot_amount
			#rot_amount = 0
			#pulsing = True
			#self.pulse()
			global able_to_listen
			if able_to_listen:
				able_to_listen = False
				os.system("aplay dingding.wav &")
				time.sleep(0.5)
				self.pipeline.set_state(gst.STATE_PLAYING)
			else:
				self.pipeline.set_state(gst.STATE_PAUSED)
				try:
					self.run_saera(None, 'speech-event', ' ')
				finally:
					fsink = self.pipeline.get_by_name('fsink')
					if not fsink is None:
						fsink.set_state(gst.STATE_NULL)
						fsink.set_state(gst.STATE_READY)
					able_to_listen = True

	def check_proximity_sensor(self):
		global able_to_listen
		try:
			if able_to_listen:
				f = open("/sys/devices/platform/gpio-switch/proximity/state")
				state = f.read()
				f.close()
				if state=="closed\n":
					cmd = """dbus-send --system --type=method_call --dest="com.nokia.mce" --print-reply "/com/nokia/mce/request" com.nokia.mce.request.get_tklock_mode|awk -F "\"" '/g/ {print $2}'"""
					status, result = commands.getstatusoutput(cmd)
					if status:
						return # probably not on an N900
					else:
						if not "un" in result:
							# Screen is locked
							return
					global able_to_listen
					able_to_listen = False
					os.system("aplay dingding.wav &")
					time.sleep(0.5)
					self.pipeline.set_state(gst.STATE_PLAYING)
				else:
					if not QT:
						gobject.timeout_add(500, self.check_proximity_sensor)
					else:
						t1 = QtCore.QTimer()
						t1.singleShot(500, self.check_proximity_sensor)
		except:
			# we probably don't have a proximity sensor
			print "No proximity sensor."

	def check_mail(self):
		self.pipeline.set_state(gst.STATE_PAUSED)
		result = []
		for i in self.imap_mailfolders:
			result = result + i.check()
		for i in self.pop_mailfolders:
			result = result + i.check()
		if result:
			# for j in result:
			if len(result)==1:
				j = result[0]
				if '"' in j['From']:
					fro = j['From'].split('"')[1]
				else:
					fro = ''.join(''.join(j['From'].split('<')).split('>'))
				words = "You have a new email from "+fro+". Would you like me to read it to you?"
				self.current_message = j
			else:
				words = "You have "+str(len(result))+" new emails. Would you like me to read them to you?"
				self.current_message = result
				saera_processing.next_func = saera_processing.should_read_email
				self.lines.append([words, False])
				self.darea.queue_draw()
				self.lines = self.lines[-20:]
				# gobject.timeout_add(100, os.system, saera_processing.sent.espeak_cmdline+' "'+words+'" ; aplay dingding.wav & sleep 0.5')
				os.system(saera_processing.sent.espeak_cmdline+' "'+words+'" ; aplay dingding.wav & sleep 0.5')
				global able_to_listen
				able_to_listen = False
				self.pipeline.set_state(gst.STATE_PLAYING)
		# return False
		if not QT:
			gobject.timeout_add(45000, self.check_mail)
		else:
			t1 = QtCore.QTimer()
			t1.singleShot(45000, self.check_mail)

	def check_texts(self):
		self.pipeline.set_state(gst.STATE_PAUSED)
		# smsp = os.popen('sqlite3 /home/user/.rtcom-eventlogger/el-vl.db "Select remote_uid, free_text, outgoing, is_read, \
		# 				storage_time from Events where service_id=3 and event_type_id=11 and outgoing=0 and is_read=0 \
		# 				order by storage_time desc ; Update Events set is_read = 1 where service_id=3 and event_type_id=11 and outgoing=0"')
		smsp=os.popen('sqlite3 /home/user/.rtcom-eventlogger/el-v1.db "Select remote_uid, free_text from Events where service_id=3 and event_type_id=11 and outgoing=0 and is_read=0 order by storage_time desc ; Update Events set is_read = 1 where service_id=3 and event_type_id=11 and outgoing=0"')
		sms_texts = smsp.read()
		smsp.close()
		# imp = os.popen('sqlite3 /home/user/.rtcom-eventlogger/el-vl.db "Select remote_uid, free_text, outgoing, is_read, \
		# 				storage_time from Events where service_id=3 and event_type_id=4 and outgoing=0 and is_read=0 \
		# 				order by storage_time desc ; Update Events set is_read = 1 where service_id=3 and event_type_id=4 and outgoing=0"')
		imp=os.popen('sqlite3 /home/user/.rtcom-eventlogger/el-v1.db "Select remote_uid, free_text from Events where service_id=3 and event_type_id=4 and outgoing=0 and is_read=0 order by storage_time desc ; Update Events set is_read = 1 where service_id=3 and event_type_id=4 and outgoing=0"')
		im_texts = imp.read().strip()
		imp.close()
		smsp = sms_texts.split('\n')
		imp = im_texts.split('\n')
		imp = smsp+imp
		imp = [j for j in [[i.split("|")[0],"|".join(i.split("|")[1:])] for i in imp] if j]
		imp = [j for j in imp if j[0] and j[1]]
		self.ims = imp
		if not QT:
			gobject.timeout_add(10000, self.check_texts)
		else:
			QtCore.QTimer().singleShot(10000, self.check_texts)
		self.read_ims()

	def read_email(self):
		self.pipeline.set_state(gst.STATE_PAUSED)
		if self.current_message:
			if isinstance(self.current_message, basestring):
				if '"' in self.current_message['From']:
					fro = self.current_message['From'].split('"')[1]
				else:
					fro = ''.join(''.join(self.current_message['From'].split('<')).split('>'))
				words = "This email is from "+fro+".\nSubject: "+self.current_message['Subject']+'.\nMessage: '+self.current_message.get_payload()
				self.lines.append([words, False])
				self.lines = self.lines[-20:]
				self.darea.queue_draw()
				if not QT:
					gobject.timeout_add(100, os.system, saera_processing.sent.espeak_cmdline+' "'+words+'"')
				else:
					callback = functools.partial(os.system, saera_processing.sent.espeak_cmdline+' "'+words+'"')
					QtCore.QTimer().singleShot(100, callback)
			else:
				for i in self.current_message:
					if '"' in i['From']:
						fro = i['From'].split('"')[1]
					else:
						fro = ''.join(''.join(i['From'].split('<')).split('>'))
					if i==len(self.current_message)-1:
						words = "Last email is from "+fro+".\nSubject: "+i['Subject']+'.\nMessage: '+i.get_payload()
					elif i==0:
						words = "The first email is from "+fro+".\nSubject: "+i['Subject']+'.\nMessage: '+i.get_payload()
					else:
						words = "Email number "+str(self.current_message.index(i)+1)+" is from "+fro+".\nSubject: "+i['Subject']+'.\nMessage: '+i.get_payload()
					self.lines.append([words, False])
					self.lines = self.lines[-20:]
					self.darea.queue_draw()
					if not QT:
						gobject.timeout_add(100, os.system, saera_processing.sent.espeak_cmdline+' "'+words+'"')
					else:
						callback = functools.partial(os.system, saera_processing.sent.espeak_cmdline+' "'+words+'"')
						QtCore.QTimer().singleShot(100, callback)
	def read_all_emails(self):
		self.pipeline.set_state(gst.STATE_PAUSED)
		result = []
		for i in self.imap_mailfolders:
			result = result+i.all()
		for i in self.pop_mailfolders:
			result = result+i.all()
		for i in result:
			if '"' in i['From']:
				fro = i['From'].split('"')[1]
			else:
				fro = ''.join(''.join(i['From'].split('<')).split('>'))
			words = "Email from "+fro+".\nSubject: "+i['Subject']+'.\nMessage: '+i.get_payload().replace('"', '\\"')
			self.lines.append([words, False])
			self.lines = self.lines[-20:]
			self.darea.queue_draw()
			if not QT:
				gobject.timeout_add(100, os.system, saera_processing.sent.espeak_cmdline+' "'+words+'"')
			else:
				callback = functools.partial(os.system, saera_processing.sent.espeak_cmdline+' "'+words+'"')
				QtCore.QTimer().singleShot(100, callback)

	def read_ims(self):
		try:
			im = self.ims.pop()
			words = "New message from "+im[0]+": "+im[1]
			words1 = "New message from "+im[0].replace('1','one ').\
											   replace('2','two ').\
											   replace('3','three ').\
											   replace('4','four ').\
											   replace('5','five ').\
											   replace('6','six ').\
											   replace('7','seven ').\
											   replace('8','eight ').\
											   replace('9','nine ').\
											   replace('0','zero ')+": "+im[1]
			self.lines.append([words,False])
			self.lines = self.lines[-20:]
			self.darea.queue_draw()
			os.system(saera_processing.sent.espeak_cmdline+' "'+words1+'"')
			if not QT:
				gobject.timeout_add(5000, self.read_ims)
			else:
				QtCore.QTimer().singleShot(5000, self.read_ims)
		except IndexError:
			return


	def open_settings(self):
		def set_lang(widget, langs):
			sel = [None]
			def selection_changed(selector, seltype):
				global settings
				__import__("sentences.sentences_"+selector.get_current_text())
				saera_processing.sent = sys.modules["sentences.sentences_"+selector.get_current_text()]
				settings['language'] = selector.get_current_text()
				open(os.getenv('HOME')+'/.saera', 'w').write(json.dumps(settings))
				stack = hildon.WindowStack.get_default()
				stack.pop_1()
			lwin = hildon.StackableWindow()
			selector = hildon.TouchSelector(text = True)
			selector.connect("changed", selection_changed)
			for i in langs:
				selector.append_text(i)
			selector.set_column_selection_mode(hildon.TOUCH_SELECTOR_SELECTION_MODE_SINGLE)
			lwin.add(selector)
			lwin.show_all()
		try:
			win = hildon.StackableWindow()
		except NameError:
			win = gtk.Window()
			win.set_modal(True)
			win.set_transient_for(self.win)
		win.set_title("Settings")
		vbox = gtk.VBox()
		win.add(vbox)
		langs = [i.split("_")[1].split(".")[0] for i in os.listdir('sentences') if (i.endswith('.py') and not 'init' in i)]
		try:
			langbut = hildon.GtkButton(gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT)
			langbut.set_label("Language")
			langbut.connect("clicked", set_lang, langs)
			vbox.pack_start(langbut, True, False, 0)
		except NameError:
			cbox = gtk.combo_box_new_text()
			for i in langs:
				cbox.append_text(i)
			vbox.pack_start(cbox, True, False, 0)
		win.show_all()
	

	def run_saera(self, widget=None, event=None, data=None):
		try:
			coords = self.q.get_nowait()
		except Empty:
			pass
		else:
			saera_processing.location = coords
			print "Coords: ", coords

		if(event == "speech-event"):
			text = data[0].upper() + data[1:].lower().replace(" and nine hundred", " N900")
		else:
			if not QT:
				text = self.input.get_text()
			else:
				text = self.input.text()

		if text:
			print "Got input: " + text
			self.lines.append([text, True])
			if not QT:
				self.input.set_text("")
				self.darea.queue_draw()
			else:
				self.input.setText("")
			result, func = saera_processing.parse_input(text+" ")
		else:
			result = False
			func = False

		if event == "speech-event" \
			and ((settings['use_google_voice'] == 'unrecognized' and result.startswith("I don't understand ")) \
				 or settings['use_google_voice'] == 'always'):
			print "Sending to Google..."
			cmd = r'wget -q -U "Mozilla/5.0" --post-file /tmp/saera/output.flac -O- '\
				'--header="Content-Type: audio/x-flac; rate='+str(SAMPLE_RATE)+r'" "'\
				+gv_api_url+'"'
			print(cmd)
			status, result = commands.getstatusoutput(cmd)

			if status:
				print "Google voice recognition failed."
			else:
				print "Result from google: %s" % result
				text = json.loads(result)['hypotheses'][0]['utterance']

				print "Got back '"+text+"'"
				self.lines[-1][0] = text
				result, func = saera_processing.parse_input(text+" ")

		if func:
			eval(func)

		global pulsing
		global able_to_listen
		pulsing = False
		able_to_listen = True
		if result:
			self.lines.append([result,False])
			self.lines = self.lines[-20:]
			if not QT:
				self.darea.queue_draw()
			#Espeak makes a poor guess how to pronounce this, so we help it out.
			result = result.replace("maemo","maymo")
			result = result.replace("I am.","Ay am.")
			result = result.replace("sushi", "sooshi")
			result = result.replace("falafel", "fuh-laHfel")
			if not QT:
				gobject.timeout_add(100, os.system, saera_processing.sent.espeak_cmdline+' "'+result+'"')
			else:
				callback = functools.partial(os.system, saera_processing.sent.espeak_cmdline+' "'+result+'"')
				QtCore.QTimer.singleShot(100, callback)
			if not QT:
				gobject.timeout_add(500, self.check_proximity_sensor)
			else:
				QtCore.QTimer().singleShot(500, self.check_proximity_sensor)

	def pulse(self):
		global rot_amount
		rot_amount+=0.3
		self.darea.queue_draw()
		if pulsing:
			if not QT:
				gobject.timeout_add(100, self.pulse)
			else:
				QtCore.QTimer().singleShot(100, self.pulse)

	def display_picture(self, pic):
		global photo
		pixbuf = gtk.gdk.pixbuf_new_from_file(pic)
		x = pixbuf.get_width()
		y = pixbuf.get_height()
		photo = cairo.ImageSurface(0,x,y)
		ct = cairo.Context(surface)
		''' create a GDK formatted Cairo context to the new Cairo native context '''
		ct2 = gtk.gdk.CairoContext(ct)
		ct2.set_source_pixbuf(pixbuf,0,0)
		ct2.paint()
		self.darea.queue_draw()


	def init_mail(self):
		try:
			imap_mailfolder = '/home/user/.modest/cache/mail/imap/'
			accounts = os.listdir(imap_mailfolder)
			for i in accounts:
				folder = MailFolder(i, 'imap')
				folder.folders = os.listdir(imap_mailfolder+i+'/folders')
				if "INBOX" in folder.folders:
					folder.messages = os.listdir(imap_mailfolder+i+'/folders/INBOX/')
				self.imap_mailfolders.append(folder)
			pop_mailfolder = '/home/user/.modest/cache/mail/pop/'
			accounts = os.listdir(pop_mailfolder)
			for i in accounts:
				folder = MailFolder(i,'pop')
				folder.folders = os.listdir(pop_mailfolder+i+'/folders')
				if "INBOX" in folder.folders:
					folder.messages = os.listdir(pop_mailfolder+i+'/folders/INBOX/')
				self.pop_mailfolders.append(folder)
		except OSError:
			pass


	def init_gst(self):
		"""Initialize the speech components"""

		pipeline = 'pulsesrc ! audioconvert '
		print(settings)

		if(settings['use_google_voice'] != 'always'):
			pipeline += '! tee name = t ! audioresample '
			pipeline += '! vader name=vad auto-threshold=true '
			pipeline += '! pocketsphinx name=asr t. '

		if(settings['use_google_voice'] == 'never'):
			pipeline += '! fakesink '
		else:
			pipeline += '! audiorate ! audioresample ! audio/x-raw-int, rate='+str(SAMPLE_RATE)
			pipeline += '! flacenc ! filesink name=fsink location=/tmp/saera/output.flac'

		print "GStreamer pipeline: " + pipeline
		self.pipeline = gst.parse_launch(pipeline)

		if(settings['use_google_voice'] != 'always'):
			asr = self.pipeline.get_by_name('asr')
			asr.connect('partial_result', self.asr_partial_result)
			asr.connect('result', self.asr_result)
			asr.set_property('configured', True)
			print dir(asr)

			#Experimental. Custom model for higher accuracy.
			asr.set_property('lm', 'model/6577.lm')
			asr.set_property('dict', 'model/6577.dic')

		bus = self.pipeline.get_bus()
		bus.add_signal_watch()
		bus.connect('message::application', self.application_message)

		self.pipeline.set_state(gst.STATE_PAUSED)

	def asr_partial_result(self, asr, text, uttid):
		"""Forward partial result signals on the bus to the main thread."""
		struct = gst.Structure('partial_result')
		struct.set_value('hyp', text)
		struct.set_value('uttid', uttid)
		if text.lower()=="open":
			asr.set_property('lm', 'model_open/6521.lm')
			asr.set_property('dict', 'model_open/6521.dic')
		asr.post_message(gst.message_new_application(asr, struct))

	def asr_result(self, asr, text, uttid):
		"""Forward result signals on the bus to the main thread."""
		struct = gst.Structure('result')
		struct.set_value('hyp', text)
		struct.set_value('uttid', uttid)
		asr.post_message(gst.message_new_application(asr, struct))

	def application_message(self, bus, msg):
		"""Receive application messages from the bus."""
		msgtype = msg.structure.get_name()
		if msgtype == 'partial_result':
			self.partial_result(msg.structure['hyp'], msg.structure['uttid'])
		elif msgtype == 'result':
			self.final_result(msg.structure['hyp'], msg.structure['uttid'])
			self.pipeline.set_state(gst.STATE_PAUSED)
			
	def partial_result(self, hyp, uttid):
		"""Delete any previous selection, insert text and select it."""
		# All this stuff appears as one single action
		print "Partial Result:", hyp
		
	def final_result(self, hyp, uttid):
		"""Insert the final result."""
		# All this stuff appears as one single action
		print "Final Result:", hyp
		try:
			self.run_saera(None, "speech-event", hyp)
		finally:
			fsink = self.pipeline.get_by_name('fsink')
			if not fsink is None:
				fsink.set_state(gst.STATE_NULL)
				fsink.set_state(gst.STATE_READY)

if __name__=='__main__':

	app = Saera()
	if not QT:
		gtk.main()
	else:
		sys.exit(app.app.exec_())
