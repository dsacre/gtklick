#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import sys
import getopt

import liblo

import klick_backend
import gtklick_config
import main_window
import preferences_dialog
import misc


help_string = """Usage:
  gtklick [ options ]

Options:
  -o port   specify OSC port of klick instance to connect to
  -h        show this help"""


class GTKlick:
    def __init__(self, args):
        # parse command line arguments
        port = None
        try:
            r = getopt.getopt(args, 'o:h');
            for opt in r[0]:
                if opt[0] == '-o':
                    port = opt[1]
                elif opt[0] == '-h':
                    print help_string
                    sys.exit(0)
        except getopt.GetoptError, e:
            sys.exit(e.msg)

        gtk.gdk.threads_init()

        try:
            self.wtree = gtk.glade.XML('gtklick.glade')

            # load config from file
            self.config = gtklick_config.GtklickConfig()
            self.config.read()

            # start klick process
            self.klick = klick_backend.KlickBackend(port, 'gtklick')

            # the actual windows are created by glade, this basically just connects GUI and OSC callbacks
            self.win = main_window.MainWindow(self.wtree, self.klick)
            self.prefs = preferences_dialog.PreferencesDialog(self.wtree, self.klick, self.config)

            self.klick.add_method(None, None, self.fallback)

            # wassup?
            self.klick.send('/query_all')

        except klick_backend.KlickBackendError, e:
            self.error_message(e.msg)
            sys.exit(1)

        # start timer to check if klick is still running
        if self.klick.process:
            self.timer = gobject.timeout_add(1000, misc.weakref_method(self.check_klick))

    def __del__(self):
        self.config.write()

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
    gtklick = GTKlick(sys.argv[1:])
    gtk.main()
