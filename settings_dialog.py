#!/usr/bin/python

import gtk
import os
import sys
import saera
import saera_processing

try:
	import hildon
except ImportError:
	pass

try:
	import json
except ImportError:
	import simplejson as json

class SaeraSettingsDialog():
	def __init__(self, _settings):
		self.settings = _settings

	def touch_selector_change(self, selector, seltype, data):
		button, key = data

		self.settings[key] = selector.get_current_text()
		label = button.get_label().split(":")[0]
		button.set_label("%s: %s" % (label, self.settings[key]))

		stack = hildon.WindowStack.get_default()
		stack.pop_1()

	def check_box_change(self, widget, key):
		if widget.get_active():
			self.settings[key] = "yes"
		else:
			self.settings[key] = "no"

	def show_touch_selector(self, widget, data):
		label, key, options = data

		lwin = hildon.StackableWindow()
		lwin.set_title("Settings")

		selector = hildon.TouchSelector(text = True)
		selector.connect("changed", self.touch_selector_change, (widget, key))
		for i in options:
			selector.append_text(i)
		selector.set_column_selection_mode(hildon.TOUCH_SELECTOR_SELECTION_MODE_SINGLE)
		lwin.add(selector)
		lwin.show_all()

	def get_available_languages(self):
		return [i.split("_")[1].split(".")[0] for i in os.listdir('sentences') if (i.endswith('.py') and not 'init' in i)]

	def add_chooser(self, vbox, label, key, options):
		try:
			el = hildon.GtkButton(gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT)
			el.set_label("%s: %s" % (label, self.settings[key]))
			el.connect("clicked", self.show_touch_selector, (label, key, options))
		except NameError:
			el = gtk.combo_box_new_text()
			for i in options:
				el.append_text(i)

		vbox.pack_start(el, True, False, 0)

	def add_check_button(self, vbox, label, key):
		try:
			el = hildon.CheckButton(gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT)
		except NameError:
			el = gtk.CheckButton()

		el.set_label(label)
		el.set_active(self.settings[key] == "yes")
		el.connect("toggled", self.check_box_change, key)
		vbox.pack_start(el, True, False, 0)


	def destroy_handler(self, win):
		open(os.getenv('HOME') + '/.saera', 'w').write(json.dumps(self.settings))

		modname = "sentences.sentences_" + self.settings["language"]
		__import__(modname)
		saera_processing.sent = sys.modules[modname]


	def show(self, parent_window):
		try:
			win = hildon.StackableWindow()
		except NameError:
			win = gtk.Window()
			win.set_modal(True)
			win.set_transient_for(parent_window)

		vbox = gtk.VBox()
		win.set_title("Settings")
		win.add(vbox)
		win.connect("destroy", self.destroy_handler)

		langs = self.get_available_languages()
		self.add_chooser(vbox, "Language", "language", langs)

		opts = [ "always", "unrecognized", "never" ]
		self.add_chooser(vbox, "Use Google Voice", "use_google_voice", opts)

		self.add_check_button(vbox, "Pass to answers.com", "use_answers_com")

		win.show_all()
