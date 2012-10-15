#!/usr/bin/python
# -*- coding:utf-8 -*-

#Don't change this next line, it tells espeak how to pronounce this language
espeak_cmdline = "espeak -vpt-pt+f2"

tens = {'vinte':20, 'trinta':30, 'dirty':30, 'quarenta':40, 'cinquenta':50, 'sessenta':60}
teens = {'des':10, 'dez':10, 'onze':11, 'douze':12, 'doze':12, 'treze':13, 'katorze':14, 'quaorze':14, 'quinze':15, 'kinze':15, 'dezasseis':16,'dezassete':17, 'dizoito':18, 'dezanove':19}
ones = {'um':1, 'dois':2, 'tres':3, 'quatro':4, 'cinco':5, 'seis':6, 'seys':6, 'sete':7, 'oito':8, 'nove':9}

life_universe_everything = ['41.99999999.',
			'Chocolate.',
			'Isso vai demurar um tempo a responder. Mais ou menos sete e meio milhoes de anos.',
			'O amor e u significado da vida. O resto do Universo pode-se deixar arranger sozinho.',
			'Software Livre.',
			'Eu Sou.',
			'Tira umas ferias num Pais Tropical.',
			'Precisa-ce de duas pessoas.',
			['O que e a resposta que queres?', 'store_answer'],
			'Quarenta e dois.',
			# A Matrix quote too, why not.
			'A Matrix e o mundo que foi escondido a frente dos teus olhos para te fazer cego a verdade.']

greeting = ['Olŕ!',
	'Bom Dia.',
	'Oy.',
	'Hey.',
	'Aloha!',
	'Como estas?',
	"E um dia bonito para Intelligencia Artificial."]
greeting_grumpy = "Vai-te Cagar."

test = ['Estou a trabalhar.',
	 'Test, test, Um, dois, tres.',
	 'Relatorio de Status: Saera a trabalhar.',
	 'Pass']

# Times
known_time = "Agora e %I:%M %p."
unknown_time = "Deculpa, nao sei que horas sao "

# Phone
phone_number_error = "Numeros de telephone tem dez o onze numeros."
contact_name_error = "Nao sem quem e essa pessoa."
successful_call = "Telefonando "

N900_facts = ["O N900 e o Rei dos telephones",
	"Sabes que o N900 pode usar o Mac OSX?",
	"Nokia fez o telephone, a communidade fez o trabalho.",
	"O N900 tinha uma Retina display antes de o iPhone.",
	"A muitos boms recursos para o N900 ao maemo.org.",
	"Vamos por um computador, uma camera, um radio, e um telefone"+
	" e vamos juntar todos em uma peca. Isso e que voce esta a segurar nas suas maos.",
	"O N900 foi feito para utilizar pelo menos 8 systemas de operacao.",
	"Se nao a uma App para isso, podes fazer a tua propria!"]

# Pictures
took_picture = "Tirem uma fotografia."
took_front_picture = "Ok. Tirem uma fotografia de ti."

i_love_you = "Eu tambem te amo. Obviamente nos deveriamos ir ler XKCD."

# Reminders
what_reminder_time = 'Que horas e que ue te deveria lembrar?'
reminding_you = 'Lembra '

