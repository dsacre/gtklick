#!/usr/bin/env python

from distutils.core import setup
import sys

if sys.hexversion < 0x02050000:
    sys.exit("sorry, python 2.5 or higher is required")

try:
    import pygtk
    pygtk.require('2.0')
    import gtk
    import gtk.glade
except:
    sys.exit("sorry, can't find pygtk")

try:
    import liblo
except:
    sys.exit("sorry, can't find pyliblo")


setup(
    name = 'gtklick',
    version = '0.1.0',
    author = 'Dominic Sacre',
    author_email = 'dominic.sacre@gmx.de',
    url = 'http://das.nasophon.de/gtklick/',
    description = '',
    license = "GPL",
    scripts = ['gtklick.py'],
    data_files = [('share/gtklick', ['gtklick.glade'])],
)
