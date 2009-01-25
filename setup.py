#!/usr/bin/env python

from distutils.core import setup
from distutils.dep_util import newer
from distutils.log import info
from distutils.command.build import build
from distutils.command.install_data import install_data
from distutils.command.clean import clean
import sys
import subprocess
import glob
import os
import shutil


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

try:
    subprocess.Popen(['msgfmt'], stderr=subprocess.PIPE)
except OSError:
    sys.exit("couldn't run msgfmt, please make sure gettext is installed")


mo_files = []

class my_build(build):
    def run(self):
        self.compile_po_files()
        build.run(self)

    def compile_po_files(self):
        for po in glob.glob('po/*.po'):
            lang = os.path.basename(po)[:-3]
            mo_dir = os.path.join(self.build_base, 'locale', lang, 'LC_MESSAGES')
            mo = os.path.join(mo_dir, 'gtklick.mo')
            if not os.path.isdir(mo_dir):
                info("creating %s" % mo_dir)
                os.makedirs(mo_dir)
            if newer(po, mo):
                info("compiling %s to %s" % (po, mo))
                subprocess.Popen(['msgfmt', '-o', mo, po])
            lang_dir = os.path.join('share', 'locale', lang, 'LC_MESSAGES')
            mo_files.append((lang_dir, [mo]))

class my_install_data(install_data):
    def run(self):
        self.data_files.extend(mo_files)
        install_data.run(self)

class my_clean(clean):
    def run(self):
        clean.run(self)
        locale_dir = os.path.join(self.build_base, 'locale')
        if self.all and os.path.exists(locale_dir):
            info("removing %s (and everything under it)" % locale_dir)
            try:
                shutil.rmtree(locale_dir)
            except:
                pass


setup(
    name = 'gtklick',
    version = '0.6.0',
    author = 'Dominic Sacre',
    author_email = 'dominic.sacre@gmx.de',
    url = 'http://das.nasophon.de/gtklick/',
    description = 'a simple GTK metronome based on klick',
    license = 'GPL',
    scripts = ['bin/gtklick'],
    packages = ['gtklick'],
    data_files = [
        ('share/gtklick', ['share/gtklick.glade']),
        ('share/applications', ['share/gtklick.desktop']),
        ('share/pixmaps', ['share/gtklick.xpm', 'share/gtklick.png']),
    ],
    cmdclass = {
        'build': my_build,
        'install_data': my_install_data,
        'clean': my_clean,
    }
)
