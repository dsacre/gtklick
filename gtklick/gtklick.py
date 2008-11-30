#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# gtklick
#
# Copyright (C) 2008  Dominic Sacré  <dominic.sacre@gmx.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.


import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import gobject

import getopt
import sys
import os.path

from klick_backend import *
from gtklick_config import *
from main_window import *
from profiles_pane import *
from preferences_dialog import *
from misc import *


help_string = """Usage:
  gtklick [ options ]

Options:
  -o port   OSC port to start klick with
  -q port   OSC port of running klick instance to connect to
  -h        show this help"""


class GTKlick:
    def __init__(self, args, share_dir):
        self.config =None

        # parse command line arguments
        port = None
        connect = False
        try:
            r = getopt.getopt(args, 'o:q:h');
            for opt in r[0]:
                if opt[0] == '-o':
                    port = opt[1]
                    connect = False
                elif opt[0] == '-q':
                    port = opt[1]
                    connect = True
                elif opt[0] == '-h':
                    print help_string
                    sys.exit(0)
        except getopt.GetoptError, e:
            sys.exit(e.msg)

        gtk.gdk.threads_init()

        try:
            self.wtree = gtk.glade.XML(os.path.join(share_dir, 'gtklick.glade'))
            # explicitly call base class method, because get_name() is overridden in AboutDialog. stupid GTK...
            widgets = dict([(gtk.Widget.get_name(w), w) for w in self.wtree.get_widget_prefix('')])

            self.config = GTKlickConfig()

            # load config from file
            self.config.read()

            # start klick process
            self.klick = KlickBackend('gtklick', port, connect)

            # the actual windows are created by glade, this basically just connects GUI and OSC callbacks
            win = MainWindow(self.wtree, widgets, self.klick, self.config)
            profiles = ProfilesPane(self.wtree, widgets, self.klick, self.config, win)
            prefs = PreferencesDialog(self.wtree, widgets, self.klick, self.config)

            #self.klick.add_method(None, None, self.fallback)

            if not connect:
                self.klick.send('/config/set_sound', self.config.prefs_sound)

                if len(self.config.prefs_connect_ports):
                    ports = self.config.prefs_connect_ports.split('\0')
                    for p in ports:
                        prefs.model_ports.append([p])

                if self.config.prefs_autoconnect:
                    widgets['radio_connect_auto'].set_active(True)
                    widgets['radio_connect_auto'].toggled()
                else:
                    widgets['radio_connect_manual'].set_active(True)

                # this can not be set in the OSC callback
                widgets['check_speedtrainer_enable'].set_active(self.config.speedtrainer)
                widgets['check_speedtrainer_enable'].toggled()
                widgets['spin_tempo_increment'].set_value(self.config.tempo_increment)
                widgets['radio_meter_other'].set_active(self.config.denom != 0)

                self.klick.send('/simple/set_tempo', self.config.tempo)
                self.klick.send('/simple/set_tempo_increment', self.config.tempo_increment if self.config.speedtrainer else 0.0)
                self.klick.send('/simple/set_tempo_limit', self.config.tempo_limit)
                self.klick.send('/simple/set_meter', self.config.beats, self.config.denom if self.config.denom else 4)
                self.klick.send('/simple/set_pattern', self.config.pattern)
                self.klick.send('/config/set_volume', self.config.volume)

            self.klick.send('/query')

            widgets['window_main'].show()

        except KlickBackendError, e:
            self.error_message(e.msg)
            sys.exit(1)

        # start timer to check if klick is still running
        if self.klick.process:
            self.timer = gobject.timeout_add(1000, weakref_method(self.check_klick))

    def __del__(self):
        if self.config:
            self.config.write()

    def run(self):
        gtk.main()

    def check_klick(self):
        if not self.klick.check_process():
            self.error_message("klick seems to have been killed, can't continue without it")
            sys.exit(1)
        return True

    def fallback(self, path, args, types, src):
        print "message not handled:", path, args, src.get_url()

    def error_message(self, msg):
        m = gtk.MessageDialog(self.wtree.get_widget('window_main'),
                              0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, msg)
        m.set_title("gtklick error")
        m.run()


if __name__ == '__main__':
    app = GTKlick(sys.argv[1:], 'share')
    app.run()
