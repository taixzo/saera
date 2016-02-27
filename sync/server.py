#!/usr/bin/env python
from flask import Flask, request
from Crypto.PublicKey import RSA
import sqlite3
import os
import random
import string
import json
import base64

folder = os.path.dirname(os.path.realpath(__file__))
db_path = folder+"/saera_mappings.db"
if not os.path.exists(db_path):
	print "File %s does not exist, creating it..." % db_path

ephemeral_groups = {}
groups = {}

app = Flask(__name__)

@app.route("/")
def hello():
	return "Hi Workd", 200

@app.route("/key", methods=["POST"])
def get_key():
	content = request.get_json()
	uid = content["uuid"]
	public_key = content["public_key"]
	# Don't use possibly-ambigous characters (such as O and 0 or l, 1 and I)
	allowed_chars = '23456789abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
	while True:
		key = ''.join([random.choice(allowed_chars) for i in range(4)])
		if key not in ephemeral_groups:
			ephemeral_groups[key] = {"uuid": uid, "public_key": public_key}
			groups[uid] = { "public_key": public_key,
					"enc_key": RSA.importKey(public_key).publickey(),
					"group":set(),
					"messages": []}
			print key, '\n'
			return key, 200

@app.route("/connect", methods=["POST"])
def connect():
	content = request.get_json()
	uid = content["uuid"]
	token = content["token"]
	if token not in ephemeral_groups:
		return "Invalid token", 500
	else:
		target = ephemeral_groups[token]
		group = groups[target["uuid"]]
		own_group = groups[uid]
		own_group["group"].add(target["uuid"])
		for other_uid in group["group"]:
			own_group["group"].add(other_uid)
		group["group"].add(uid)
		group["messages"].append(base64.b64encode(group["enc_key"].encrypt("Connected", 32)[0]))
		connections = {}
		for other_uid in own_group["group"]:
			connections[other_uid] = groups[other_uid]["public_key"]
		return json.dumps(connections), 200

@app.route("/get_data", methods=["POST"])
def get_data():
	try:
		content = request.get_json()
		uid = content["uuid"]
		if uid not in groups:
			print "Invalid UUID: %s" % uid
			return "Invalid UUID", 500
		group = groups[uid]
		msg_json = json.dumps(group["messages"])
		chunk_size = 256
		chunks = [msg_json[i:i+chunk_size] for i in range(0, len(msg_json), chunk_size)]
		messages = [base64.b64encode(group["enc_key"].encrypt(chunk, 32)[0]) for chunk in chunks]
		group["messages"] = []
		return json.dumps(messages), 200
	except Exception as e:
		print e

@app.route("/send", methods=["POST"])
def send():
	content = request.get_json()
	uid = content["uuid"]
	message = content["message"]
	if uid not in groups:
		print "Invalid UUID: %s" % uid
		return "Invalid UUID", 500
	print groups
	group = groups[uid]
	for other_uid in message:
		if other_uid in group["group"]:
			print other_uid
			groups[other_uid]["messages"].append(message[other_uid])
	return "Success!", 200

if __name__ == "__main__":
	app.run(host='0.0.0.0')
