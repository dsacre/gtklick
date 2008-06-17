# -*- coding: utf-8 -*-

# gtklick
#
# Copyright (C) 2008  Dominic Sacré  <dominic.sacre@gmx.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

import klick
import misc


class PreferencesDialog:
    def __init__(self, wtree, klick):
        self.wtree = wtree
        self.klick = klick

        self.wtree.signal_autoconnect({
            'on_sound_square_toggled':  (self.on_sound_toggled, 0),
            'on_sound_sine_toggled':    (self.on_sound_toggled, 1),
            'on_sound_noise_toggled':   (self.on_sound_toggled, 2),
            'on_sound_click_toggled':   (self.on_sound_toggled, 3),
            'on_connect_auto_toggled':  (self.on_autoconnect_toggled, 0),
            'on_connect_manual_toggled':(self.on_autoconnect_toggled, 1),
        })

        self.klick.register_methods(self)

    @misc.gui_callback
    def on_sound_toggled(self, b, data):
        if b.get_active():
            self.klick.send('/set_sound', data)

    @misc.gui_callback
    def on_autoconnect_toggled(self, b, data):
        if b.get_active():
            self.klick.send('/set_autoconnect', data)

    @klick.make_method('/sound', 'i')
    @misc.osc_callback
    def sound_cb(self, path, args):
        if args[0] < 0 or args[0] > 3: return
        n = ('radio_sound_square', 'radio_sound_sine', 'radio_sound_noise', 'radio_sound_click')[args[0]]
        self.wtree.get_widget(n).set_active(True)

#    @klick.make_method('/autoconnect', 'i')
#    @misc.osc_callback
#    def autoconnect_cb(self, path, args):
#        if args[0] < 0 or args[0] > 1: return
#        n = ('radio_connect_auto', 'radio_connect_manual')[args[0]]
#        self.wtree.get_widget(n).set_active(True)

