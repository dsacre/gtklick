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

from klick_backend import *
from misc import *


class PreferencesDialog:
    def __init__(self, wtree, widgets, klick, config):
        self.widgets = widgets
        self.klick = klick
        self.config = config

        wtree.signal_autoconnect({
            'on_sound_square_toggled':  (self.on_sound_toggled, 0),
            'on_sound_sine_toggled':    (self.on_sound_toggled, 1),
            'on_sound_noise_toggled':   (self.on_sound_toggled, 2),
            'on_sound_click_toggled':   (self.on_sound_toggled, 3),
            'on_connect_auto_toggled':  (self.on_autoconnect_toggled, True),
            'on_connect_manual_toggled':(self.on_autoconnect_toggled, False),
        })

        self.klick.register_methods(self)

    @gui_callback
    def on_sound_toggled(self, b, data):
        if b.get_active():
            self.klick.send('/config/set_sound', data)

    @gui_callback
    def on_autoconnect_toggled(self, b, data):
        if b.get_active():
            if data == True:
                self.klick.send('/config/autoconnect')
            self.config.prefs_autoconnect = data

    @make_method('/config/sound', 'i')
    @osc_callback
    def sound_cb(self, path, args):
        sound = args[0]
        if sound < 0 or sound > 3: return
        w = ('radio_sound_square', 'radio_sound_sine', 'radio_sound_noise', 'radio_sound_click')[sound]
        self.widgets[w].set_active(True)
        self.config.prefs_sound = sound
