# -*- coding: utf-8 -*-

# gtklick
#
# Copyright (C) 2008  Dominic Sacré  <dominic.sacre@gmx.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

import klick_backend
import misc


class PreferencesDialog:
    def __init__(self, wtree, klick, config):
        self.wtree = wtree
        self.klick = klick
        self.config = config

        self.wtree.signal_autoconnect({
            'on_sound_square_toggled':  (self.on_sound_toggled, 0),
            'on_sound_sine_toggled':    (self.on_sound_toggled, 1),
            'on_sound_noise_toggled':   (self.on_sound_toggled, 2),
            'on_sound_click_toggled':   (self.on_sound_toggled, 3),
            'on_connect_auto_toggled':  (self.on_autoconnect_toggled, True),
            'on_connect_manual_toggled':(self.on_autoconnect_toggled, False),
        })

        self.klick.register_methods(self)

        self.klick.send('/set_sound', self.config.get_sound())
        if self.config.get_autoconnect():
            self.wtree.get_widget('radio_connect_auto').set_active(True)
            self.klick.send('/autoconnect')
        else:
            self.wtree.get_widget('radio_connect_manual').set_active(True)

    @misc.gui_callback
    def on_sound_toggled(self, b, data):
        if b.get_active():
            self.klick.send('/set_sound', data)
            self.config.set_sound(data)

    @misc.gui_callback
    def on_autoconnect_toggled(self, b, data):
        if b.get_active():
            if data == True:
                self.klick.send('/autoconnect')
            self.config.set_autoconnect(data)

    @klick_backend.make_method('/sound', 'i')
    @misc.osc_callback
    def sound_cb(self, path, args):
        sound = args[0]
        if sound < 0 or sound > 3: return
        w = ('radio_sound_square', 'radio_sound_sine', 'radio_sound_noise', 'radio_sound_click')[sound]
        self.wtree.get_widget(w).set_active(True)

        self.config.set_sound(sound)
