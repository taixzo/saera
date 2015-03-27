#! /usr/bin/env python

import json
import os

import timeparser

intentscfg = json.load(open(os.path.dirname(os.path.abspath(__file__))+"/intents.cfg"))

OPTIONAL = 0
REQUIRED = 1
VARIABLE = 2

def levenshtein(seq1, seq2):
    oneago = None
    thisrow = list(range(1, len(seq2) + 1)) + [0]
    for x in range(len(seq1)):
        twoago, oneago, thisrow = oneago, thisrow, [0] * len(seq2) + [x + 1]
        for y in range(len(seq2)):
            # delcost = oneago[y] + 1
            # delcost = oneago[y] + (1 if seq2[y][1]==REQUIRED else 0.5)
            delcost = oneago[y] + (0.5 if seq2[y][1]==REQUIRED else 0.25)
            # addcost = thisrow[y - 1] + 1
            addcost = thisrow[y - 1] + (1 if seq2[y][1]==REQUIRED else 0.5)
            if seq2[y][1]==REQUIRED:
            	subcost = oneago[y - 1] + (seq1[x] != seq2[y][0])
            else:
            	if seq2[y][1]==VARIABLE and seq1[x] in variables[seq2[y][0]].keywords:
            		subcost = oneago[y - 1]
            	elif seq2[y][1]==VARIABLE:
            		subcost = oneago[y - 1] + variables[seq2[y][0]].sensitivity
            	else:
            		subcost = oneago[y - 1] + (seq1[x] != seq2[y][0]) * 0.5
            # subcost = oneago[y - 1] + (seq1[x] != seq2[y][0])*(1 if seq2[y][1]==REQUIRED else 0.5)
            thisrow[y] = min(delcost, addcost, subcost)
    return thisrow[len(seq2) - 1]

class Intent:
	def __init__(self,name):
		self.name = name
		self.paths = []
		self.vars = []
	def add_path(self,pth):
		path = []
		requires = []
		in_required = False
		in_var = False
		for i in pth:
			if in_required:
				if i==']':
					in_required = False
					requires.append(path[-1][0])
					path.append(['', OPTIONAL])
				else:
					if i==' ':
						if path[-1][0]:
							path.append(['',REQUIRED])
					else:
						path[-1][0] += i
			else:
				if in_var:
					if i=='>':
						in_var=False
						if not path[-1][0] in self.vars:
							self.vars.append(path[-1][0])
						path.append(['',OPTIONAL])
					else:
						if i==' ':
							if path[-1][0]:
								path.append('',VARIABLE)
						else:
							path[-1][0] += i
				else:
					if i=='[':
						in_required = True
						path.append(['',REQUIRED])
					elif i=='<':
						in_var = True
						path.append(['',VARIABLE])
					elif i == ' ':
						if path[-1][0]:
							path.append(['',OPTIONAL])
					else:
						if len(path)==0:
							path.append(['',OPTIONAL])
						path[-1][0] += i
		for i in range(len(path)-1,-1,-1):
			if path[i][0] == '':
				del path[i]
		self.paths.append(path)
		print (path)
	def match(self,string):
		scores = []
		for path in self.paths:
			scores.append(levenshtein(string.lower().split(),path))
		# return self.paths[scores.index(min(scores))]
		return min(scores)

class Guesser:
	def __init__(self):
		self.intents = []
		# i = Intent("alarm")
		# i.add_path("[set alarm] for <time>")
		# i.add_path("[wake me] at <time>")

		# j = Intent("call")
		# j.add_path("[call] <digits>")
		# j.add_path("[call] <contact>")

		# k = Intent("email")
		# k.add_path("what [emails] do i have")
		# k.add_path("[read] me my [emails]")
		# k.add_path("do i have [unread] [emails]")
		# k.add_path("do i have any new [emails]")

		# self.intents.append(i)
		# self.intents.append(j)
		# self.intents.append(k)
		for intentname in intentscfg:
			intent = Intent(intentname)
			for expression in intentscfg[intentname]:
				intent.add_path(expression)
			self.intents.append(intent)
	def guess (self, string):
		guesses = []
		for intent in self.intents:
			guesses.append([intent.match(string),intent])
		best_guess = float("inf")
		best_guess_intent = None
		for i in range(len(guesses)):
			if guesses[i][0]<best_guess:
				best_guess = guesses[i][0]
				best_guess_intent = guesses[i][1]
		splitstring = string.split()
		outvars = {}
		for i in best_guess_intent.vars:
			first = -1
			last = -1
			for j in variables[i].keywords:
				if j in splitstring:
					print "In string: ", j
					first = min(first,splitstring.index(j)) if first >= 0 else splitstring.index(j)
			if first >= 0:
				print 'j', i, first
				for j in variables[i].keywords:
					if j in splitstring:
						print "In string: ", j
						last = max(last,splitstring.index(j)+1)
			else:
				for j in variables[i].prewords:
					print j, splitstring
					if j in splitstring:
						print "In string: ", j
						first = min(first,splitstring.index(j)+1) if first >= 0 else splitstring.index(j)+1
				if first >= 0:
					for j in variables[i].postwords:
						if j in splitstring:
							print "In string: ", j
							last = max(last,splitstring.index(j)+1)
					else:
						last = len(splitstring)
			if last >= 0:
				print "Var:",variables[i].parse(splitstring[first:last])
				outvars[i] = variables[i].parse(splitstring[first:last])
		# return (best_guess, best_guess_intent.name, string)
		return {
				'text':string,
				'outcome':{
					'intent':best_guess_intent.name,
					'entities':outvars
				}
			}

class Variable:
	def __init__(self):
		self.keywords = []
		self.prewords = []
		self.postwords = []
		self.sensitivity = 1.1
	def parse(self,words):
		return ' '.join(words)

class vTime(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.keywords = ['year',
						 'years',
						 'month',
						 'months',
						 'week',
						 'weeks',
						 'day',
						 'days',
						 'hour',
						 'hours',
						 'minute',
						 'minutes',
						 'second',
						 'seconds',
						 'tomorrow',
						 'yesterday',
						 'morning',
						 'noon',
						 'afternoon'
						 'evening',
						 'night',
						 'midnight',
						 'half',
						 'quarter',
						 'past',
						 'till',
						 'til',
						 'after',
						 'am',
						 'pm']
		self.keywords += ['one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen','twenty','thirty','forty','fifty']
		self.keywords += ['first','second','third','fourth','fifth','sixth','seventh','eighth','ninth','tenth','eleventh','twelfth','thirteenth','fourteenth','fifteenth','sixteenth','seventeenth','eighteenth','nineteenth','twentieth','thirtieth']
		self.keywords += ['january','march','april','may','june','july','august','september','october','november','december']
	def parse(self, words):
		return timeparser.parse(' '.join(words)).calculatedTime

class  vDigits(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.keywords = ['one','two','three','four','five','six','seven','eight','nine','zero','oh','nought']

class vContact(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.keywords = []

class vLocation(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.keywords = []
		self.prewords = ['in','at','from']

#################################
class vName(Variable):			#
	def __init__(self):	
		Variable.__init__(self)		#
		self.keywords = []		#
		self.prewords = ['am','me','is','named']		#
class vHome(Variable):			#
	def __init__(self):	
		Variable.__init__(self)		#
		self.keywords = []		#
#################################

class vFood(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.keywords = ['burger',
						 'veggie',
						 'pasta',
						 'sushi',
						 'pizza',
						 'falafel',
						 'sandwich']

class vDistance(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.keywords = ['one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen','twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety','hundred']
		self.keywords += ['foot','feet','yard','yards','mile','miles','meter','meters','kilometer','kilometers']

class vDirection(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.keywords = ['north','east','south','west']
			
	

variables = {'time':vTime(),
			 'digits':vDigits(),
			 'contact':vContact(),
			 'name':vName(),	#
			 'home':vHome(),	#  Do we need these?
			 'location':vLocation(),
			 'food':vFood(),
			 'distance':vDistance(),
			 'direction':vDirection()}

if __name__=="__main__":
	# i = Intent()
	# i.add_path("[set alarm] for <time>")
	# i.add_path("[wake me] at <time>")

	# j = Intent()
	# j.add_path("[call] <digits>")
	# j.add_path("[call] <contact>")

	g = Guesser()

	print (g.guess("Set alarm for time"))
	print (g.guess("Set alarm time"))
	print (g.guess("Set for time"))
	print ('*'*20)
	print (g.guess("Set alarm for seven"))
	print (g.guess("Set me an alarm for seven"))
	print (g.guess("Wake me up at half-past six"))
	print (g.guess("Wake me before noon tomorrow please"))
	print ('*'*20)
	print (g.guess("Call sarah"))
	print (g.guess("Call three four five one seven two six four five one"))
	print (g.guess("Make me tea seven"))
	print ('*'*20)
	print (g.guess("Do I have new emails"))
	print (g.guess("Check my email"))
	print (g.guess("What's my email status"))
	print (g.guess("What emails do I have"))
	print ('*'*20)
	print (g.guess("I want a veggie burger"))
	print (g.guess("I want pasta"))
	print (g.guess("Where is the nearest pizza place"))
	print ('*'*20)
	print (g.guess("My car ran out of gas"))
	print (g.guess("Gas around here"))

	while True:
		print (g.guess(raw_input("> ")))

