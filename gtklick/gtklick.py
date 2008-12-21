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

import weakref

import klick_backend
import gtklick_config
import main_window
import profiles_pane
import preferences_dialog
import misc


help_string = """Usage:
  gtklick [ options ]

Options:
  -o port   OSC port to start klick with
  -q port   OSC port of running klick instance to connect to
  -r port   OSC port to be used for gtklick
  -h        show this help"""


class GTKlick:
    def __init__(self, args, share_dir):
        self.config = None

        # parse command line arguments
        port = None
        return_port = None
        connect = False
        verbose = False
        try:
            r = getopt.getopt(args, 'o:q:r:Lh');
            for opt, arg in r[0]:
                if opt == '-o':
                    port = arg
                    connect = False
                elif opt == '-q':
                    port = arg
                    connect = True
                elif opt == '-r':
                    return_port = arg
                elif opt == '-L':
                    verbose = True
                elif opt == '-h':
                    print help_string
                    sys.exit(0)
        except getopt.GetoptError, e:
            sys.exit(e.msg)

        gtk.gdk.threads_init()

        try:
            self.wtree = gtk.glade.XML(os.path.join(share_dir, 'gtklick.glade'))
            # explicitly call base class method, because get_name() is overridden in AboutDialog. stupid GTK...
            widgets = dict([(gtk.Widget.get_name(w), w) for w in self.wtree.get_widget_prefix('')])

            self.config = gtklick_config.GTKlickConfig()

            # load config from file
            self.config.read()

            # start klick process
            self.klick = klick_backend.KlickBackend('gtklick', port, return_port, connect, verbose)

            # make "globals" known in other modules
            for m in (main_window, profiles_pane, preferences_dialog):
                m.wtree = self.wtree
                m.widgets = widgets
                m.klick = weakref.proxy(self.klick)
                m.config = weakref.proxy(self.config)

            # the actual windows are created by glade, this basically just connects GUI and OSC callbacks
            self.win = main_window.MainWindow()
            self.profiles = profiles_pane.ProfilesPane(self.win)
            self.prefs = preferences_dialog.PreferencesDialog()

            #self.klick.add_method(None, None, self.fallback)

            if not connect:
                # restore settings from config file.
                # many settings are just sent to klick, and the OSC notifications will take care of the rest

                # port connections
                if len(self.config.prefs_connect_ports):
                    ports = self.config.prefs_connect_ports.split('\0')
                    for p in ports:
                        self.prefs.model_ports.append([p])

                if self.config.prefs_autoconnect:
                    misc.do_quietly(lambda: widgets['radio_connect_auto'].set_active(True))
                    self.klick.send('/config/autoconnect')
                else:
                    misc.do_quietly(lambda: widgets['radio_connect_manual'].set_active(True))
                    self.klick.send('/config/connect', *ports)

                # sound / volume
                if self.config.prefs_sound >= 0:
                    self.klick.send('/config/set_sound', self.config.prefs_sound)
                else:
                    self.klick.send('/config/set_sound', self.config.prefs_sound_accented, self.config.prefs_sound_normal)

                self.klick.send('/config/set_sound_pitch',
                    2 ** (self.config.prefs_pitch_accented / 12.0),
                    2 ** (self.config.prefs_pitch_normal / 12.0)
                )
                self.klick.send('/config/set_volume', self.config.volume)

                # metronome state
                misc.do_quietly(lambda: (
                    widgets['check_speedtrainer_enable'].set_active(self.config.speedtrainer),
                    widgets['spin_tempo_increment'].set_value(self.config.tempo_increment),
                    widgets['radio_meter_other'].set_active(self.config.denom != 0)
                ))
                widgets['spin_tempo_increment'].set_sensitive(self.config.speedtrainer)
                widgets['spin_tempo_start'].set_sensitive(self.config.speedtrainer)

                self.klick.send('/simple/set_tempo', self.config.tempo)
                self.klick.send('/simple/set_tempo_increment', self.config.tempo_increment if self.config.speedtrainer else 0.0)
                self.klick.send('/simple/set_tempo_start', self.config.tempo_start)
                self.klick.send('/simple/set_meter', self.config.beats, self.config.denom if self.config.denom else 4)
                self.klick.send('/simple/set_pattern', self.config.pattern)
            else:
                self.klick.send('/query')

            widgets['window_main'].show()

        except klick_backend.KlickBackendError, e:
            self.error_message(e.msg)
            sys.exit(1)

        # start timer to check if klick is still running
        if self.klick.process:
            self.timer = gobject.timeout_add(1000, misc.weakref_method(self.check_klick))

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
        m = gtk.MessageDialog(self.wtree.get_widget('window_main'), 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, msg)
        m.set_title("gtklick error")
        m.run()
        m.destroy()


if __name__ == '__main__':
    app = GTKlick(sys.argv[1:], 'share')
    app.run()
