#!/usr/bin/python

#Don't change this next line, it tells espeak how to pronounce this language
espeak_cmdline = "espeak -vde+f2"

tens = {'twenty':20, 'thirty':30, 'dirty':30, 'forty':40, 'fifty':50, 'sixty':60}
teens = {'ten':10, 'eleven':11, 'twelve':12, 'thirteen':13, 'fourteen':14, 'fifteen':15, 'sixteen':16,'seventeen':17, 'eighteen':18, 'nineteen':19}
ones = {'one':1, 'two':2, 'three':3, 'four':4, 'five':5, 'six':6, 'seven':7, 'eight':8, 'ate':8, 'nine':9}

life_universe_everything = ['41.99999999.',
			'Schokolade.',
			'That will take me some time to answer. About seven and a half million years.',
			'Love is the meaning of life. The rest of the universe will figure itself out.',
			'Open-source software.',
			'Ich.',
			'Take a vacation to the tropics.',
			'It takes two people.',
			['What do you want the answer to be?', 'store_answer'],
			'Zwei und fiertzig.',
			# A Matrix quote too, why not.
			'The Matrix is the world that has been pulled over your eyes to blind you from the truth.']

greeting = ['Hallo!',
	'Gruss dich.',
	'Hi.',
	'Hey.',
	'Aloha!',
	'Hallo!',
	'Hallo!',
	'Hallo!',
	'Hallo!',
	"Es ist ein guten Tag fur artificial intelligence.",
	'Hey there!']
greeting_grumpy = "Gehen weg."

test = ['Ich arbeite.',
	 'Testing, testing, eins, zwei, drei.',
	 'Status report: Saera running.',
	 'Jah']

# Times
known_time = "Jetzt es ist %I:%M %p."
unknown_time = "Es tut mir leid, ich weiss nicht der Zeit in "

# Phone
phone_number_error = "Telefonnumer haben zehn oder elf digits."
contact_name_error = "Ich weiss das Name nicht."
successful_call = "Calling "

N900_facts = ["Der N900 ist der konig des Handis.",
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

i_love_you = "Und ich liebe dich. Doch, wir sollen XKCD lesen."

# Reminders
what_reminder_time = 'What time would you like me to remind you?'
reminding_you = 'Reminding you '

