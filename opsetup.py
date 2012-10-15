#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob, re

import sys
reload(sys).setdefaultencoding("UTF-8")
import os

try:
	from sdist_maemo import sdist_maemo as _sdist_maemo
	sdist_maemo = _sdist_maemo
except ImportError:
	sdist_maemo = None
	print 'sdist_maemo command not available'

from distutils.core import setup

def read(fname):
  return open(os.path.join(os.path.dirname(__file__), fname)).read()

print "SETUP.PY RUNNING"

APP_NAME="optify_pocketsphinx"
VERSION="0.1"
BUILD="0"

## load changelog from file
CHANGES = " " + read("optify_pocketsphinx.changelog").strip()

## TODO: an actual bugtracker ##
BUGTRACKER_URL = "http://talk.maemo.org/showthread.php?p=1222081"

def is_package(path):
	return (
		os.path.isdir(path) and
		os.path.isfile(os.path.join(path, '__init__.py'))
	)

listOfAllPaths = []

setup(
	name=APP_NAME,
	version=VERSION,
	description="Optify Pocketsphinx",
	long_description="Optify the Pocketsphinx packages to free up rootfs space.",
	author="taixzo",
	author_email="taixzo@gmail.com",
	maintainer="taixzo",
	maintainer_email="taixzo@gmail.com",
	license="GNU GPLv3",
	data_files=[],
	requires=[],
	cmdclass={
		'sdist_ubuntu': sdist_maemo,
		'sdist_diablo': sdist_maemo,
		'sdist_fremantle': sdist_maemo,
		'sdist_harmattan': sdist_maemo,
	},
	options={
		"sdist_ubuntu": {
			"debian_package": APP_NAME,
			"section": "utilities",
			"copyright": "gpl",
			"changelog": CHANGES,
			"buildversion": str(BUILD),
			"depends": "python, pocketsphinx-utils, pocketsphinx-hmm-en-hub4wsj, pocketsphinx-lm-en-hub4, gstreamer0.10-pocketsphinx, python-gst0.10, python-gtk2, python-gobject, python-cairo, espeak",
			"architecture": "all",
		},
		"sdist_fremantle": {
			"debian_package": APP_NAME,
			"Maemo_Bugtracker": BUGTRACKER_URL,
			"section": "user/system",
			"copyright": "gpl",
			"changelog": CHANGES,
			"buildversion": str(BUILD),
			"depends": "pocketsphinx-utils, pocketsphinx-hmm-en-hub4wsj, pocketsphinx-lm-en-hub4, gstreamer0.10-pocketsphinx",
			"architecture": "all",
      "postinst" : open("optify_pocketsphinx.sh").read()


		},
	},
)
