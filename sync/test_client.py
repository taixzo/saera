import requests
import uuid
from Crypto.PublicKey import RSA
import json
import base64

SERVER = 'taixzo.com'
PORT = '5000'

class Client:
	def __init__(self):
		self.headers = {'Content-type': 'application/json'}
		self.connected = False
		self.peers = {}

	def generate_key(self):
		self.key = RSA.generate(2048)
		self.public_key = self.key.publickey().exportKey('PEM')
		self.private_key = self.key.exportKey('PEM')

	def initial_setup(self):
		data = json.dumps({'uuid': self.uid, 'public_key': self.public_key})
		result = requests.post('http://%s:%s/key' % (SERVER, PORT), data=data, headers=self.headers)
		if result.status_code == 200:
			return result.text
		else:
			return result

	def create_connection(self, token):
		data = json.dumps({'uuid': self.uid, 'public_key': self.public_key, 'token':token})
		result = requests.post('http://%s:%s/connect' % (SERVER, PORT), data=data, headers=self.headers)
		result_json = result.json()
		for peer in result_json:
			self.peers[peer] = RSA.importKey(result_json[peer]).publickey()
		print result, result_json

	def check_data(self):
		data = json.dumps({'uuid': self.uid})
		result = requests.post('http://%s:%s/get_data' % (SERVER, PORT), data=data, headers=self.headers)
		plaintext = ''.join([self.key.decrypt(base64.b64decode(chunk)) for chunk in json.loads(result.text)])
		messages = [self.key.decrypt(base64.b64decode(msg)) for msg in json.loads(plaintext)]
		#print plaintext
		print messages

	def send_data(self, message, peers):
		msg_dict = {}
		for peer in peers:
			# Encrypt the message to each peer with that peer's public key
			msg_dict[peer] = base64.b64encode(self.peers[peer].encrypt(message, 32)[0])
		data = json.dumps({'uuid': self.uid, 'message': msg_dict})
		result = requests.post('http://%s:%s/send' % (SERVER, PORT), data=data, headers=self.headers)

	def run(self):
		self.generate_key()
		self.uid = str(uuid.uuid4())
		print str(self.uid)
		token = self.initial_setup()
		print "Token: %s" % token
		while True:
			if self.connected:
				i = raw_input("Message to send: ")
				self.send_data(i, self.peers.keys())
			else:
				i = raw_input("Enter token: ")
				if i:
					self.create_connection(i)
					self.connected = True
					#break
			result = self.check_data()

if __name__=="__main__":
	client = Client()
	client.run()
