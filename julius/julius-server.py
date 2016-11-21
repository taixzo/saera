#!/usr/bin/env python
# -*- coding: utf-8 -*-

import queue as Queue
import subprocess
import os
import pyjulius
import time
import logging
import threading
from bottle import Bottle, route, run, template

logging.basicConfig(filename='/home/nemo/.saera/julius-server.log',
                    level=logging.DEBUG)

p = subprocess.Popen['pgrep julius.jolla'], shell=True, stdout=subprocess.PIPE)
out, err = p.communicate()
for line in out.decode('UTF-8').splitlines():
	pid = int(line.split(None, 1)[0])
	os.kill(pid, 9)

f = __file__.split('julius-server.py')[0]+'../'
jproc = subprocess.Popen([f+'julius/julius.jolla',
                          '-module',
                          '-record',
                          '/tmp/saera/',
                          '-gram',
                          '/home/nemo/.cache/saera/contacts',
                          '-gram',
                          '/home/nemo/.cache/saera/addresses',
                          '-h',
                          f + 'julius/hmmdefs',
                          '-hlist',
                          f + 'julius/tiedlist',
                          '-input',
                          'mic',
                          '-tailmargin',
                          '800',
                          '-rejectshort',
                          '600'],
                         stdout=subprocess.PIPE)

client = pyjulius.Client('localhost', 10500)
logging.debug('Connecting to julius module')
while True:
	try:
		client.connect()
		break
	except pyjulius.ConnectionError:
		logging.debug('Connecting...')
		time.sleep(0.5)
logging.debug('...Connected!')
client.start()

app = Bottle()

def listen_sync():
	client.send("RESUME\n")
	while True:
		try:
			client.results.get(False)
		except Queue.Empty:
			break
	logging.debug("Emptied message queue")
	while True:
		try:
			result = client.results.get(False)
			if isinstance(result, pyjulius.Sentence):
				break
			elif result.tag == "RECOGFAIL":
				result = MicroMock(words=[MicroMock(word='*mumble*')])
				break
			else:
				continue
		except Queue.Empty:
			continue
	numbers = {'zero':'0','oh':'0','one':'1','two':'2','three':'3','four':'4','five':'5','six':'6','seven':'7','eight':'8','nine':'9'}
	words = [i.word for i in result.words]
	num_str = ''
	for i, word in enumerate(words):
		if len(words) > i-1:
			if word in numbers:
				num_str += numbers[word]
			else:
				if len(num_str) > 1:
					words[i-(len(num_str))] = num_str
					words[i-(len(num_str))+1:i] = ['']*(len(num_str) - 1)
				num_str = ''
	words = [i for i in words if i]
	if words[0] in 'what,where,when,why,how,who,is,will,are,do,should,can,would,does'.split(','):
		punct = '?'
	else:
		punct = '.'
	res = " ".join(words) + punct
	res = res[0].upper() + res[1:]
	client.send("TERMINATE")
	return res


@app.route('/get_next')
def get_next():
	return listen_sync()

@app.route('/sleep')
def sleep():
	jproc.send_signal(20)

@app.route('/awake')
def awake():
	jproc.send_signal(18)

run(app, host='localhost', port=12885)
