#! /usr/bin/env python

try:
	import json
except ImportError:
	import simplejson as json
import os

import timeparser2

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

# lists have no .rindex() method
def listRightIndex(alist, value):
	return len(alist) - alist[-1::-1].index(value) -1

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
		splitstring_oc = string.split()
		splitstring = string.lower().split()
		outvars = {}
		for i in best_guess_intent.vars:
			first = -1
			last = -1
			for j in splitstring:
				if j in variables[i].keywords or variables[i].keyfunc(j):
					first = min(first,splitstring.index(j)) if first >= 0 else splitstring.index(j)
			if first >= 0:
				for j in variables[i].assistantkeywords:
					if j in splitstring:
						for k in variables[i].keywords:
							kindices = [l for l, x in enumerate(splitstring) if x == k]
							indices = [l for l, x in enumerate(splitstring) if x == j]
							matches = [l for l in indices if l+1 in kindices]
							if matches:
								first = min(first,min(matches))
				for j in splitstring:
					if j in variables[i].keywords or variables[i].keyfunc(j):
						last = max(last,splitstring.index(j)+1)
			else:
				for j in splitstring:
					if j in variables[i].prewords:
						first = min(first,splitstring.index(j)+1) if first >= 0 else splitstring.index(j)+1
				if first >= 0:
					for j in variables[i].postwords:
						if j in splitstring and splitstring.index(j)>first:
							if variables[i].greedy:
								last = max(last,listRightIndex(splitstring,j))
							else:
								last = max(last,splitstring.index(j))
					if last==-1:
						last = len(splitstring)
			if last >= 0:
				outvars[i] = variables[i].parse(splitstring_oc[first:last])
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
		self.keyfunc = lambda x: False
		self.assistantkeywords = []
		self.prewords = []
		self.postwords = []
		self.sensitivity = 1.1
		self.greedy = False
	def parse(self,words):
		return ' '.join(words)

class vTime(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.assistantkeywords = ['a','an']
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
						 'afternoon',
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
		self.keywords += [str(i) for i in range(60)]
		self.keywords += ['one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen','twenty','thirty','forty','fifty']
		self.keywords += ['first','second','third','fourth','fifth','sixth','seventh','eighth','ninth','tenth','eleventh','twelfth','thirteenth','fourteenth','fifteenth','sixteenth','seventeenth','eighteenth','nineteenth','twentieth','thirtieth']
		self.keywords += ['january','march','april','may','june','july','august','september','october','november','december']
	def parse(self, words):
		return timeparser2.parse(words)

class  vDigits(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.keywords = ['one','two','three','four','five','six','seven','eight','nine','zero','oh','nought']

class  vNumber(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.keywords = ['zero','oh','one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen','twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety','hundred','thousand']
		self.keyfunc = lambda x: x.isdigit()
	def parse(self,words):
		units = [
			"zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
			"nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
			"sixteen", "seventeen", "eighteen", "nineteen",
		]

		tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

		scales = ["hundred", "thousand", "million", "billion", "trillion"]

		numwords = {}
		numwords["and"] = (1, 0)
		for idx, word in enumerate(units):    numwords[word] = (1, idx)
		for idx, word in enumerate(tens):     numwords[word] = (1, idx * 10)
		for idx, word in enumerate(scales):   numwords[word] = (10 ** (idx * 3 or 2), 0)

		current = result = 0
		for word in words:
			if word.isdigit():
				result = int(word)
				break
			if word not in numwords:
			  raise Exception("Illegal word: " + word)

			scale, increment = numwords[word]
			current = current * scale + increment
			if scale > 100:
				result += current
				current = 0

		return result + current

class vDice(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.keyfunc = lambda x: x.startswith('d') and x[1:].isdigit()
	def parse(self,words):
		return int(words[0][1:])

class vContact(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.keywords = []

class vLocation(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.keywords = []
		self.prewords = ['in','at','from','about', 'to']
		self.postwords = ['at','after','when','if','in']

#################################
class vName(Variable):			#
	def __init__(self):
		Variable.__init__(self)		#
		self.keywords = []		#
		self.prewords = ['am','me','is','named']		#
class vThing(Variable):			#
	def __init__(self):
		Variable.__init__(self)		#
		self.keywords = []		#
		self.prewords = ['is','are']		#
class vHome(Variable):			#
	def __init__(self):
		Variable.__init__(self)		#
		self.keywords = []		#
#################################

class vSong(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.prewords = 'play'

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

class vDoAction(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.prewords = ['to','should']
		self.postwords = ['in','at']
		self.greedy = True

class vDistance(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.keywords = ['one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen','twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety','hundred']
		self.keywords += ['foot','feet','yard','yards','mile','miles','meter','meters','kilometer','kilometers']

class vDirection(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.keywords = ['north','east','south','west']

class vPreposition(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.keywords = ['i','you','he','she','it','we','they']

class vPosessive_Preposition(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.keywords = ['my','your','his','her','its','our','their']

class vSearchEngine(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.keywords = ['google','bing','yahoo','duck','go','wikipedia']

class vQuery(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.prewords = ['for'] #+ vSearchEngine().keywords

class vYesNo(Variable):
	def __init__(self):
		Variable.__init__(self)
		self.affirmatives = ['yes','yep','yeah', 'certainly']
		self.negatives = ['no', 'nope','dont','don\'t','not']
		self.keywords = self.affirmatives+self.negatives
	def parse(self, words):
		for word in self.negatives:
			if word in words:
				return False
		for word in self.affirmatives:
			if word in words:
				return True
		# Assume we answer in the positive if it isn't one of these?
		return True

class vStore(Variable):
	def __init__(self):
		Variable.__init__(self)
		# TODO
		pass


variables = {'time':vTime(),
			 'digits':vDigits(),
			 'dice':vDice(),
			 'number':vNumber(),
			 'contact':vContact(),
			 'name':vName(),
			 'thing':vThing(),
			 'home':vHome(),	#  Do we need these?
			 'location':vLocation(),
			 'food':vFood(),
			 'distance':vDistance(),
			 'direction':vDirection(),
			 'preposition':vPreposition(),
			 'posessive_preposition':vPosessive_Preposition(),
			 'do_action':vDoAction(),
			 'search_engine':vSearchEngine(),
			 'query':vQuery(),
			 'song':vSong(),
			 'yes_no':vYesNo(),
			 'store':vStore()}

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
