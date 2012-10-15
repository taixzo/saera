#!/usr/bin/python

import saera_processing
import gtk
import pango
import cairo
import pangocairo
import sys
import os
import gobject
import math
import gobject
import pygst
pygst.require('0.10')
gobject.threads_init()
import gst

# Absolute path tweak - thanks MartinK!
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
	import hildon
	from portrait import FremantleRotation
	app_name = "Saera"
	app_version = "1.0"
	initial_mode = FremantleRotation.ALWAYS
except ImportError:
	pass

pulsing = False
rot_amount = 0
WIDTH = 0
HEIGHT = 0
photo = None
able_to_listen = True

class Saera:
	def __init__(self):
		self.lines = [['What can I help you with?',False]]
		try:
			program = hildon.Program.get_instance()
			self.win = hildon.StackableWindow()
			rotation_object = FremantleRotation(app_name, self.win, app_version, initial_mode)
			program.add_window(self.win)
		except:
			print "No hildon win"
			self.win = gtk.Window()
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

		gobject.timeout_add(500, self.check_proximity_sensor)

		self.win.connect('destroy', gtk.main_quit)

		self.init_gst()

	def expose_event(self, widget, event):
		global WIDTH, HEIGHT
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

	def button_press_event(self, widget, event):
		if WIDTH/2-64<event.x<WIDTH/2+64 and event.y>HEIGHT-128:
			# This looks nice, but redrawing while recording takes up
			# way too much CPU.
			#global pulsing, rot_amount
			#rot_amount = 0
			#pulsing = True
			#self.pulse()
			global able_to_listen
			able_to_listen = False
			os.system("aplay dingding.wav &")
			os.system("sleep 0.5")
			self.pipeline.set_state(gst.STATE_PLAYING)

	def check_proximity_sensor(self):
		global able_to_listen
		try:
			if able_to_listen:
				f = open("/sys/devices/platform/gpio-switch/proximity/state")
				state = f.read()
				f.close()
				if state=="closed\n":
					global able_to_listen
					able_to_listen = False
					os.system("aplay dingding.wav &")
					os.system("sleep 0.5")
					self.pipeline.set_state(gst.STATE_PLAYING)
				else:
					gobject.timeout_add(500, self.check_proximity_sensor)
		except:
			# we probably don't have a proximity sensor
			print "No proximity sensor."

	def open_settings(self):
		def set_lang(widget, langs):
			sel = [None]
			def selection_changed(selector, seltype):
				__import__("sentences.sentences_"+selector.get_current_text())
				saera_processing.sent = sys.modules["sentences.sentences_"+selector.get_current_text()]
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
		if event=="speech-event":
			text = data[0].upper()+data[1:].lower().replace(" and nine hundred", " N900")
		else:
			text = self.input.get_text()
		if text:
			self.lines.append([text, True])
			self.input.set_text("")
			self.darea.queue_draw()
			result, func = saera_processing.parse_input(text+" ")
			if func:
				eval(func)
			self.lines.append([result,False])
			self.lines = self.lines[-20:]
			global pulsing
			global able_to_listen
			pulsing = False
			able_to_listen = True
			self.darea.queue_draw()
			#Espeak makes a poor guess how to pronounce this, so we help it out.
			result = result.replace("maemo","maymo")
			result = result.replace("I am.","Ay am.")
			gobject.timeout_add(100, os.system, saera_processing.sent.espeak_cmdline+' "'+result+'"')
			gobject.timeout_add(500, self.check_proximity_sensor)

	def pulse(self):
		global rot_amount
		rot_amount+=0.3
		self.darea.queue_draw()
		if pulsing:
			gobject.timeout_add(100, self.pulse)

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

	def init_gst(self):
		"""Initialize the speech components"""
		self.pipeline = gst.parse_launch('pulsesrc ! audioconvert ! audioresample '
										 + '! vader name=vad auto-threshold=true '
										 + '! pocketsphinx name=asr ! fakesink')
		asr = self.pipeline.get_by_name('asr')
		asr.connect('partial_result', self.asr_partial_result)
		asr.connect('result', self.asr_result)
		asr.set_property('configured', True)
		print dir(asr)
		
		#Experimental. Custom model for higher accuracy.
		asr.set_property('lm', 'model/0893.lm')
		asr.set_property('dict', 'model/0893.dic')

		bus = self.pipeline.get_bus()
		bus.add_signal_watch()
		bus.connect('message::application', self.application_message)

		self.pipeline.set_state(gst.STATE_PAUSED)

	def asr_partial_result(self, asr, text, uttid):
		"""Forward partial result signals on the bus to the main thread."""
		struct = gst.Structure('partial_result')
		struct.set_value('hyp', text)
		struct.set_value('uttid', uttid)
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
		self.run_saera(None, "speech-event", hyp)

if __name__=='__main__':

	app = Saera()
	gtk.main()
