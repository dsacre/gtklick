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

import gtk
import gtk.keysyms

import time
import math

from klick_backend import *
from misc import *


class MainWindow:
    def __init__(self, wtree, widgets, klick, config):
        self.widgets = widgets
        self.klick = klick
        self.config = config

        # why doesn't glade do this?
        self.widgets['spin_meter_beats'].set_value(4)
        self.widgets['spin_meter_denom'].set_value(4)

        wtree.signal_autoconnect({
            # main menu
            'on_file_quit':             self.on_file_quit,
            'on_edit_preferences':      self.on_edit_preferences,
            'on_help_shortcuts':        self.on_help_shortcuts,
            'on_help_about':            self.on_help_about,
            # tempo
            'on_tempo_scale_changed':   self.on_tempo_changed,
            'on_tempo_spin_changed':    self.on_tempo_changed,
            'on_tap_tempo':             self.on_tap_tempo,
            # meter
            'on_meter_even_toggled':    (self.on_meter_toggled, (0, 4)),
            'on_meter_24_toggled':      (self.on_meter_toggled, (2, 4)),
            'on_meter_34_toggled':      (self.on_meter_toggled, (3, 4)),
            'on_meter_44_toggled':      (self.on_meter_toggled, (4, 4)),
            'on_meter_other_toggled':   (self.on_meter_toggled, None),
            'on_meter_beats_changed':   self.on_meter_beats_changed,
            'on_meter_denom_changed':   self.on_meter_denom_changed,
            # others
            'on_start_stop':            self.on_start_stop,
            'on_volume_changed':        self.on_volume_changed,
            'on_window_main_destroy':   gtk.main_quit,
        })

        accel = gtk.AccelGroup()

        for k in (gtk.keysyms.Left, gtk.keysyms.Right,
                  gtk.keysyms.Down, gtk.keysyms.Up,
                  gtk.keysyms.Page_Down, gtk.keysyms.Page_Up):
            accel.connect_group(k, gtk.gdk.CONTROL_MASK, 0, self.on_tempo_accel)

        for k in (gtk.keysyms.plus, gtk.keysyms.equal, gtk.keysyms.KP_Add,
                  gtk.keysyms.minus, gtk.keysyms.KP_Subtract):
            accel.connect_group(k, gtk.gdk.CONTROL_MASK, 0, self.on_volume_accel)

        accel.connect_group(gtk.keysyms.space, gtk.gdk.CONTROL_MASK, 0, self.on_start_stop_accel)
        accel.connect_group(gtk.keysyms.Return, gtk.gdk.CONTROL_MASK, 0, self.on_tap_tempo_accel)

        self.widgets['window_main'].add_accel_group(accel)

        self.klick.register_methods(self)

        self.klick.send('/simple/set_tempo', self.config.tempo)
        self.klick.send('/simple/set_meter', self.config.beats, self.config.denom)
        self.klick.send('/config/set_volume', self.config.volume)


    # GUI callbacks

    def on_file_quit(self, i):
        self.widgets['window_main'].destroy()

    def on_edit_preferences(self, i):
        prefs = self.widgets['dialog_preferences']
        prefs.run()
        prefs.hide()

    def on_help_shortcuts(self, i):
        shortcuts = self.widgets['dialog_shortcuts']
        shortcuts.run()
        shortcuts.hide()

    def on_help_about(self, i):
        about = self.widgets['dialog_about']
        about.run()
        about.hide()

    @gui_callback
    def on_tempo_changed(self, r):
        self.klick.send('/simple/set_tempo', int(r.get_value()))

    @gui_callback
    def on_tap_tempo(self, b):
        self.klick.send('/simple/tap', ('d', time.time()))

    @gui_callback
    def on_meter_toggled(self, b, data):
        if b.get_active():
            if data != None:
                self.klick.send('/simple/set_meter', data[0], data[1])
            else:
                self.klick.send('/simple/set_meter',
                                self.widgets['spin_meter_beats'].get_value(),
                                self.widgets['spin_meter_denom'].get_value())

    @gui_callback
    def on_meter_beats_changed(self, b):
        self.klick.send('/simple/set_meter',
                        self.widgets['spin_meter_beats'].get_value(),
                        self.widgets['spin_meter_denom'].get_value())

    @gui_callback
    def on_meter_denom_changed(self, b):
        v = b.get_value()

        # make sure value is a power of two
        if v == self.prev_denom:
            return
        elif v == self.prev_denom - 0.5:
            # down arrow (step_inc is 0.5)
            denom = 2 ** (math.log(self.prev_denom, 2) - 1)
        elif v == self.prev_denom + 0.5:
            # up arrow
            denom = 2 ** (math.log(self.prev_denom, 2) + 1)
        else:
            # keyboard input: use next power of two
            denom = 1
            while denom < v:
                denom *= 2

        b.set_value(denom)
        self.prev_denom = denom

        self.klick.send('/simple/set_meter',
                        self.widgets['spin_meter_beats'].get_value(),
                        self.widgets['spin_meter_denom'].get_value())

    @gui_callback
    def on_start_stop(self, b):
        if self.active:
            self.klick.send('/metro/stop')
        else:
            self.klick.send('/metro/start')

    @gui_callback
    def on_volume_changed(self, r):
        self.klick.send('/config/set_volume', r.get_value())

    @gui_callback
    def on_tempo_accel(self, group, accel, key, mod):
        tempo = self.widgets['spin_tempo'].get_value()
        if   key == gtk.keysyms.Left:       tempo -= 1
        elif key == gtk.keysyms.Right:      tempo += 1
        elif key == gtk.keysyms.Down:       tempo -= 10
        elif key == gtk.keysyms.Up:         tempo += 10
        elif key == gtk.keysyms.Page_Down:  tempo /= 2
        elif key == gtk.keysyms.Page_Up:    tempo *= 2
        tempo = min(max(tempo, 1), 999)
        self.klick.send('/simple/set_tempo', int(tempo))
        return True

    @gui_callback
    def on_volume_accel(self, group, accel, key, mod):
        volume = self.widgets['scale_volume'].get_value()
        if key in (gtk.keysyms.minus, gtk.keysyms.KP_Subtract):
            volume -= 0.1
        elif key in (gtk.keysyms.plus, gtk.keysyms.equal, gtk.keysyms.KP_Add):
            volume += 0.1
        volume = min(max(volume, 0.0), 1.0)
        self.klick.send('/config/set_volume', volume)
        return True

    @gui_callback
    def on_start_stop_accel(self, group, accel, key, mod):
        if self.active:
            self.klick.send('/metro/stop')
        else:
            self.klick.send('/metro/start')
        return True

    @gui_callback
    def on_tap_tempo_accel(self, group, accel, key, mod):
        self.klick.send('/simple/tap', ('d', time.time()))
        return True


    # OSC callbacks

    @make_method('/simple/tempo', 'f')
    @osc_callback
    def metro_tempo_cb(self, path, args):
        self.widgets['scale_tempo'].set_value(args[0])
        self.widgets['spin_tempo'].set_value(args[0])
        self.config.tempo = args[0]

    @make_method('/simple/meter', 'ii')
    @osc_callback
    def metro_meter_cb(self, path, args):
        beats, denom = args
        if beats in (0, 2, 3, 4) and denom == 4 and \
                not self.widgets['radio_meter_other'].get_active():
            # standard meter
            self.widgets['hbox_meter_spins'].set_sensitive(False)
            self.widgets['spin_meter_beats'].select_region(0, 0)
            self.widgets['spin_meter_denom'].select_region(0, 0)
            if beats == 0:
                self.widgets['radio_meter_even'].set_active(True)
            elif beats == 2:
                self.widgets['radio_meter_24'].set_active(True)
            elif beats == 3:
                self.widgets['radio_meter_34'].set_active(True)
            elif beats == 4:
                self.widgets['radio_meter_44'].set_active(True)
        else:
            # custom meter
            self.widgets['radio_meter_other'].set_active(True)
            self.widgets['hbox_meter_spins'].set_sensitive(True)
            self.widgets['spin_meter_beats'].set_value(beats)
            self.widgets['spin_meter_denom'].set_value(denom)

        # set active radio button as mnemonic widget
        w = [x for x in self.widgets['radio_meter_other'].get_group() if x.get_active()][0]
        self.widgets['label_frame_meter'].set_mnemonic_widget(w)

        self.prev_denom = denom

        self.config.beats = beats
        self.config.denom = denom

    @make_method('/metro/active', 'i')
    @osc_callback
    def metro_active_cb(self, path, args):
        if args[0]:
            self.widgets['align_start'].hide()
            self.widgets['align_stop'].show()
        else:
            self.widgets['align_stop'].hide()
            self.widgets['align_start'].show()

        self.active = bool(args[0])

    @make_method('/config/volume', 'f')
    @osc_callback
    def volume_cb(self, path, args):
        self.widgets['scale_volume'].set_value(args[0])
        self.config.volume = args[0]
