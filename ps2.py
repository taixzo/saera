#!/usr/bin/python

import os
import pocketsphinx as ps
decoder = ps.Decoder(hmm='/usr/share/pocketsphinx/model/hmm/wsj1/',
					 dict='/usr/share/pocketsphinx/model/lm/en_US/cmu07a.dic',
					 jsgf='/home/skyler/Dropbox/saera/grammar.jsgf',
					 adcin='yes',
					 samprate='8000')

#decoder.add_word("Saera", "S EH R AH", True)

for i in os.listdir('.'):
	if '.wav' in i:
		fh = open("Putonsomemusic.wav", "rb")
		nsamp = decoder.decode_raw(fh)

		hyp, uttid, score = decoder.get_hyp()
		print "%s: Got result %s %d" % (i, hyp, score)

