import subprocess
import os
import urllib2
import json
import threading
import time

global to_return
to_return = []

p = subprocess.Popen(['ps c | grep "[s]aera2.py" | grep S'], shell=True, stdout=subprocess.PIPE)
out, err = p.communicate()
for line in out.decode('UTF-8').splitlines():
	if 'saera2.py' in line:
		break
else:
	server = subprocess.Popen(['python', '/opt/Saera/qml/Saera/saera2.py'])

def call_func_async(func, args):
	request = urllib2.Request('http://localhost:12834', json.dumps((func,) + args))
	response = urllib2.urlopen(request).read().split('\r\n')[-1]
	to_return.append(response)

def call_func(func, *args):
	ext = threading.Thread(target=call_func_async, args=(func, args))
	ext.start()

def get_latest():
	time.sleep(0.01)
	try:
		return to_return.pop()
	except IndexError:
		return ""

def try_to_connect():
	try:
		request = urllib2.Request('http://localhost:12834', "test")
		response = urllib2.urlopen(request).read().split('\r\n')[-1]
		return True
	except:
		return False