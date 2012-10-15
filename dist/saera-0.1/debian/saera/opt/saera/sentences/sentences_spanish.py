#!/usr/bin/python
# -*- coding: utf-8 -*-

#Don't change this next line, it tells espeak how to pronounce this language
espeak_cmdline = "espeak -ves+f2"

tens = {'veinte':20, 'treinta':30, 'cuarenta':40, 'cincuenta':50, 'sesenta':60}
teens = {'diez':10, 'once':11, 'doce':12, 'trece':13, 'catorce':14, 'quince':15, 'dieciséis':16,'diecisiete':17, 'dieciocho':18, 'diecinueve':19}
ones = {'uno':1, 'dos':2, 'tres':3, 'cuatro':4, 'cinco':5, 'seis':6, 'siete':7, 'ocho':8, 'nueve':9}

life_universe_everything = ['41.99999999.',
			'Chocolate.',
			'Eso me llevará algún tiempo para responder. Alrededor de 7 millones y medio de años.',
			'El amor es el sentido de la vida. El resto del universo se resolverá solo.',
			'Software de código abierto.',
			'Yo soy.',
			'Tómate una vacaciones a los trópicos.',
			'Requiere dos personas.',
			['¿Cuál quieres que sea la respuesta?', 'store_answer'],
			'Cuarenta y dos.',
			# A Matrix quote too, why not.
			'Matrix es el mundo que ha sido puesto ante tus ojos para ocultarte la verdad.']

greeting = ['¡Hola!',
	'Buen día.',
	'Hola.',
	'Hey.',
	'¡Hola!',
	'¡Hola!',
	'¡Hola!',
	'¡Hola!',
	'¡Hola!',
	"Es un lindo día para inteligencia artificial.",
	'¡Hola, ¿qué tal?']
greeting_grumpy = "Vete."

test = ['Estoy trabajando.',
	 'Probando, probando, uno, dos, tres.',
	 'Reporte de estado: Saera funcionando.',
	 'Paso']

# Times
known_time = "En este momento, son las %I:%M %p."
unknown_time = "Lo siento, no sé qué hora es en "

# Phone
phone_number_error = "Los números de teléfono tienen diez u once caracteres."
contact_name_error = "No sé quién es."
successful_call = "Llamando "

N900_facts = ["El N900 es el rey de los teléfonos.",
	"¿Sabías que el N900 puede correr Mac OSX?",
	"Nokia hizo el teléfono, la comunidad hizo todo el trabajo.",
	"El N900 tuvo pantalla Retina antes que el iPhone.",
	"Hay buenos recursos para el N900 en maemo.org.",
	"Tomemos una computadora, una cámara, una radio y un teléfono"+
	" Y pongámoslos en un solo paquete. Ese dispositivo que ahora tienes en tu mano.",
	"El N900 fue hecho para correr al menos 8 sistemas operativos.",
	"Si no hay alguna aplicación para eso, ¡tú puedes hacerla!"]

# Pictures
took_picture = "Tomé una foto."
took_front_picture = "Ok. Tomé una foto tuya."

i_love_you = "Yo también te amo. Claramente, deberíamos leer XKCD."

# Reminders
what_reminder_time = '¿A qué hora quieres que te recuerde?'
reminding_you = 'Recordándote '

#Time
bells = {'quarto':15, 'media':30}
times = {'media dia':12, 'media noche':0, 'mañana':9, 'tarde':16, 'evening':19, 'noche':21}
weekdays = ['domingo','lunes','martes','miercoles', 'jueves','viernes','sabado']
