#!/usr/bin/python

#Don't change this next line, it tells espeak how to pronounce this language
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
known_time = "Right now, it is %I:%M %p."
unknown_time = "Sorry, I don't know what time it is in "

# Phone
phone_number_error = "Phone numbers have ten or eleven characters."
contact_name_error = "I don't know who that is."
successful_call = "Calling "

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

#Time
bells = {'quarter':15, 'half':30}
times = {'noon':12, 'midnight':0, 'morning':9, 'afternoon':16, 'evening':19, 'night':21}
weekdays = ['sunday','monday','tuesday','wednesday', 'thursday','friday','saturday']
