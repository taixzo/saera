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
			os.system("aplay dingding.wav &")
			os.system("sleep 1")
			self.pipeline.set_state(gst.STATE_PLAYING)

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
			pulsing = False
			self.darea.queue_draw()
			#Espeak makes a poor guess how to pronounce this, so we help it out.
			result = result.replace("maemo","maymo")
			gobject.timeout_add(100, os.system, 'espeak -v +f2 "'+result+'"')

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
