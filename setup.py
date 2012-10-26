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

APP_NAME="saera"
PRETTY_APP_NAME="Saera"
VERSION="0.2"
BUILD="4"
DESKTOP_FILE_PATH="/usr/share/applications/hildon"
INPUT_DESKTOP_FILE="saera.desktop"
ICON_CATEGORY="apps"
ICON_SIZES=[80]

## load changelog from file
CHANGES = " " + read("saera.changelog").strip()

## TODO: an actual bugtracker ##
BUGTRACKER_URL = "http://talk.maemo.org/showthread.php?p=1222081"

def is_package(path):
	return (
		os.path.isdir(path) and
		os.path.isfile(os.path.join(path, '__init__.py'))
	)

def find_packages(path, base="", includeRoot=False):
	""" Find all packages in path """
	if includeRoot:
		assert not base, "Base not supported with includeRoot: %r" % base
		rootPath, module_name = os.path.split(path)
		yield module_name
		base = module_name
	for item in os.listdir(path):
		dir = os.path.join(path, item)
		if is_package( dir ):
			if base:
				module_name = "%(base)s.%(item)s" % vars()
			else:
				module_name = item
			yield module_name
			for mname in find_packages(dir, module_name):
				yield mname

## list all Mieru files
'''listOfAllPaths = []
for (dirpath, dirnames, filenames) in os.walk('src'):
  for filename in filenames:
    listOfAllPaths.append(os.sep.join([dirpath, filename]))'''
listOfAllPaths = ['saera_processing.py', 'saera.py', 'gsearch.py', 'dingding.wav', 'portrait.py',
		'saera_bg.png', 'saera_chat_bg.png', 'saera_mic.png', 'siri_mic.png',
		'siri_mic_spinner.png']
for (dirpath, dirnames, filenames) in os.walk('model'):
  for filename in filenames:
    listOfAllPaths.append(os.sep.join([dirpath, filename]))
for (dirpath, dirnames, filenames) in os.walk('sentences'):
  for filename in filenames:
    listOfAllPaths.append(os.sep.join([dirpath, filename]))
    

## drop the root folder path for the second ittem in the tupple

## NOTE: this might not be fully OS agnostic
## How it works
## * the x is substituted for one item in the list
## * we split the path using the path separator to a list of strings
## * then we drop the first string from the list
## * using * ve "unroll" the list and supply it as a list of arguments to os.path.join
## * os.path.join should reconstruct the path back together including the new path root folder
## * os.path.dirname drops the filenames (or else we would get for example /opt/mieru/mieru.py/mieru.py
dataFiles = map( lambda x: (os.path.dirname( os.path.join('/opt/saera/', *x.split(os.path.sep)[1:]) ), [x] ), listOfAllPaths ) 

for j in  xrange(len(dataFiles)):
	i = dataFiles[j]
	if os.sep in i[1][0]:
		print i
		dataFiles[j] = (i[0]+os.sep+i[1][0][:i[1][0].index(os.sep)],[i[1][0]])

print dataFiles


#dataFiles.extend(
#            [('/usr/share/applications',['saera.desktop']),
#             ('/usr/share/icons/hicolor/80x80/apps', ['80x80/saera.png']),
#             ('/usr/bin', ['saera'])]
#                )

## add desktop file
dataFiles.extend([ (DESKTOP_FILE_PATH, [INPUT_DESKTOP_FILE]) ])

## add icons
dataFiles.extend( [ (
                    # "/usr/share/icons/hicolor/%sx%s/%s" % (size, size, ICON_CATEGORY),
                    "/usr/share/icons/hicolor/scalable/%s" % (ICON_CATEGORY),
                    ["%sx%s/%s.png" % (size, size, APP_NAME)]
                    ) for size in ICON_SIZES ] )

setup(
	name=APP_NAME,
	version=VERSION,
	description="Voice Control and AI",
	long_description="Saera is designed as a Siri clone, using Pocketsphinx for voice recognition. Right now it is highly in development and doesn't work very well.",
	author="taixzo",
	author_email="taixzo@gmail.com",
	maintainer="taixzo",
	maintainer_email="taixzo@gmail.com",
	license="GNU GPLv3",
	data_files=dataFiles,
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
			"depends": "python, pocketsphinx-utils, pocketsphinx-hmm-en-hub4wsj, pocketsphinx-lm-en-hub4, gstreamer0.10-pocketsphinx, gstreamer0.10-flac, python-gst0.10, python-gtk2, python-gobject, python-cairo, espeak, python-beautifulsoup, python-simplejson",
			"architecture": "all",
		},
		"sdist_fremantle": {
			"debian_package": APP_NAME,
			"Maemo_Display_Name": PRETTY_APP_NAME,
			#"Maemo_Upgrade_Description": CHANGES,
			"Maemo_Bugtracker": BUGTRACKER_URL,
			#"Maemo_Icon_26": "icons/64x64/%s.png" % APP_NAME,
			"section": "user/utilities",
			"copyright": "gpl",
			"changelog": CHANGES,
			"buildversion": str(BUILD),
			#"depends": "python2.5, python2.5-qt4-core, python2.5-qt4-gui, python2.5-qt4-maemo5, python-xdg, python-simplejson",
			"depends": "python, pocketsphinx-utils, pocketsphinx-hmm-en-hub4wsj, pocketsphinx-lm-en-hub4, gstreamer0.10-pocketsphinx, gstreamer0.10-flac, python-gst0.10, python-gtk2, python-gobject, python-cairo, espeak, python-beautifulsoup, python-simplejson",
			"architecture": "all",
      "postinst" : """#!/bin/sh
#DEBHELPER#

echo "generating *.pyc files"
# generate *.pyc files to speed up startup
# also, after changing the permissions user ran python cant create them
python -m compileall /opt/saera

exit 0
""",
		},
		'''"sdist_harmattan": {
			"debian_package": APP_NAME,
			"Maemo_Display_Name": PRETTY_APP_NAME,
			#"Maemo_Upgrade_Description": CHANGES,
			"Maemo_Bugtracker": BUGTRACKER_URL,
			"Maemo_Icon_26": "icons/64x64/%s.png" % APP_NAME,
			"MeeGo_Desktop_Entry_Filename": APP_NAME,
			#"MeeGo_Desktop_Entry": "",
			"section": "user/utilities",
			"copyright": "gpl",
			"changelog": CHANGES,
			"buildversion": str(BUILD),
			"depends": "libzip1, python-pyside.qtgui, python-pyside.qtdeclarative, python",
			"architecture": "all",
      "postinst" : """#!/bin/sh
#DEBHELPER#
echo "removing old *.pyc files"
rm `find /opt/mieru -name '*.pyc'`

echo "generating *.pyc files"
# generate *.pyc files to speed up startup
# also, after changing the permissions user ran python cant create them
python -m compileall -f /opt/mieru

# if the installation is running on Fremantle,
# modify desktop files and add a startup script
CPUINFO=`cat /proc/cpuinfo | grep Hardware`
CPUINFO=`echo "$CPUINFO" | sed 's/Hardware//g'`
CPUINFO=`echo "$CPUINFO" | sed 's/://g'`
CPUINFO=`echo "$CPUINFO" | sed 's/ //g'`

if [[ "NokiaRX-51board" = $CPUINFO ]]
then
  echo "adding startup script for Fremantle"
  chmod +x /opt/mieru/mieru_fremantle
  rm -f /usr/bin/mieru
  ln -s /opt/mieru/mieru_fremantle /usr/bin/mieru
  echo "modifying Desktop file for Fremantle"
  cp /opt/mieru/data/desktop_files/mieru_fremantle.desktop /usr/share/applications/hildon/mieru.desktop
  echo "Fremantle modifications done"
fi
exit 0
""",
		},'''
		"bdist_rpm": {
			"requires": "REPLACEME",
			"icon": "data/icons/64/%s.png" % APP_NAME,
			"group": "REPLACEME",
		},
	},
)
