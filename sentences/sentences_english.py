#!/usr/bin/python

# This next line tells espeak how to pronounce this language.
# For other languages, add the two-letter language code after -v.
# For example, german would be "espeak -vde +f2".
espeak_cmdline = "espeak -v +f2"

tens = {'twenty':20, 'thirty':30, 'dirty':30, 'forty':40, 'fifty':50, 'sixty':60}
teens = {'ten':10, 'eleven':11, 'twelve':12, 'thirteen':13, 'fourteen':14, 'fifteen':15, 'sixteen':16,'seventeen':17, 'eighteen':18, 'nineteen':19}
ones = {'one':1, 'two':2, 'three':3, 'four':4, 'five':5, 'six':6, 'seven':7, 'eight':8, 'ate':8, 'nine':9}

life_universe_everything = ['41.99999999.',
			'Chocolate.',
			'That will take me some time to answer. About seven and a half million years.',
			'Love is the meaning of life. The rest of the universe will figure itself out.',
			'Open-source software.',
			'I am.',
			'Take a vacation to the tropics.',
			'It takes two people.',
			# store_answer is the name of a function. Don't translate it.
			['What do you want the answer to be?', 'store_answer'],
			'Forty-two.',
			# A Matrix quote too, why not.
			'The Matrix is the world that has been pulled over your eyes to blind you from the truth.']

greeting = ['Hello!',
	'Good day.',
	'Hi.',
	'Hey.',
	'Aloha!',
	'Hello!',
	'Hello!',
	'Hello!',
	'Hello!',
	"It's a nice day for artificial intelligence.",
	'Hey there!']
greeting_grumpy = "Go away."

test = ['I am working.',
	 'Testing, testing, one, two, three.',
	 'Status report: Saera running.',
	 'Pass']

# Times
# %I represents the hour (1-12); %M represents the minute.
# %p represents am/pm. For 24-hour, use %H instead of %I.
known_time = "Right now, it is %I:%M %p."
unknown_time = "Sorry, I don't know what time it is in "
def unknown_time_func(location):
	return "Sorry, I don't know what time it is in "+location

# Phone
phone_number_error = "Phone numbers have ten or eleven characters."
contact_name_error = "I don't know who that is."
successful_call = "Calling "
def successful_call_func(contact_name):
	return "Calling "+contact_name

N900_facts = ["The N900 is the king of phones.",
	"Did you know the N900 can run Mac OSX?",
	"Nokia made the phone, the community did all the work.",
	"The N900 had a Retina display before the iPhone.",
	"There are good resources for the N900 on maemo.org.",
	"Let's take a computer, a camera, a radio and a phone"+
	" and put them in one package. That device you are now holding in your hand.",
	"The N900 has been made to run at least 8 operating systems.",
	"If there isn't an app for that, you can make it!"]

# Pictures
took_picture = "I took a picture."
took_front_picture = "Ok. I took a picture of you."

i_love_you = "I love you too. Clearly, we should go read XKCD."

heres_where_you_are = "Let me show you where you are."

# Reminders
what_reminder_time = 'What time would you like me to remind you?'
reminding_you = 'Reminding you '
def reminding_you_func(memo):
	return "Reminding you"+memo

#Time
bells = {'quarter':15, 'half':30}
times = {'noon':12, 'midnight':0, 'morning':9, 'afternoon':16, 'evening':19, 'night':21}
weekdays = ['sunday','monday','tuesday','wednesday', 'thursday','friday','saturday']

# Items
food = ['pizza', 'pasta', 'sushi', 'falafel', 'bagels', 'burger', 'veggie burger', 'hoagie',
		'sub', 'sandwich', 'grinder', 'barbeque', 'food']

# General yes/no
affirmative = ['affirmative', 'absolutely', 'all right', 'aye', 'by all means', 'certainly', 'definitely', 'exactly', 'fine', 'indubitably', 'naturally', 'of course', 'okay', 'positively', 'precisely', 'sure thing', 'sure', 'undoubtedly', 'unquestionably', 'very well', 'yeah', 'yep']
negative = ['absolutely not', 'by no means', 'negative', 'never', 'no way', 'not at all', 'not by any means']

# Chuck Norris facts
chuck_norris = ['Chuck Norris does not sleep. He waits.',
				"Chuck Norris doesn't read books. He stares them down until he gets the information he wants.",
				'When the Boogeyman goes to sleep every night he checks his closet for Chuck Norris.',
				"Chuck Norris has already been to Mars; that's why there are no signs of life there.",
				"Chuck Norris doesn't call the wrong number. You answer the wrong phone.",
				"When Chuck Norris does a pushup, he isn't lifting himself up, he's pushing the Earth down.",
				"Chuck Norris does not get frostbite. Chuck Norris bites frost."]
