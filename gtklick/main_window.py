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
import itertools

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
            'on_file_quit':                     self.on_file_quit,
            'on_edit_preferences':              self.on_edit_preferences,
            'on_view_markings_toggled':         self.on_view_markings_toggled,
            'on_view_speedtrainer_toggled':     self.on_view_speedtrainer_toggled,
            'on_view_meter_toggled':            self.on_view_meter_toggled,
            'on_view_pattern_toggled':          self.on_view_pattern_toggled,
            'on_view_profiles_toggled':         self.on_view_profiles_toggled,
            'on_help_shortcuts':                self.on_help_shortcuts,
            'on_help_about':                    self.on_help_about,
            # tempo
            'on_tempo_scale_changed':           self.on_tempo_changed,
            'on_tempo_spin_changed':            self.on_tempo_changed,
            'on_tap_tempo':                     self.on_tap_tempo,
            'on_tempo_format_value':            self.on_tempo_format_value,
            # speed trainer
            'on_speedtrainer_enable_toggled':   self.on_speedtrainer_enable_toggled,
            'on_tempo_increment_changed':       self.on_tempo_increment_changed,
            'on_tempo_limit_changed':           self.on_tempo_limit_changed,
            # meter
            'on_meter_even_toggled':            (self.on_meter_toggled, (0, 4)),
            'on_meter_24_toggled':              (self.on_meter_toggled, (2, 4)),
            'on_meter_34_toggled':              (self.on_meter_toggled, (3, 4)),
            'on_meter_44_toggled':              (self.on_meter_toggled, (4, 4)),
            'on_meter_other_toggled':           (self.on_meter_toggled, None),
            'on_meter_beats_changed':           self.on_meter_beats_changed,
            'on_meter_denom_changed':           self.on_meter_denom_changed,
            # pattern
            'on_pattern_reset':                 self.on_pattern_reset,
            # others
            'on_start_stop':                    self.on_start_stop,
            'on_volume_changed':                self.on_volume_changed,
            'on_window_main_delete_event':      self.on_delete_event,
        })

        accel = gtk.AccelGroup()

        for k in (gtk.keysyms.Left, gtk.keysyms.Right,
                  gtk.keysyms.Down, gtk.keysyms.Up,
                  gtk.keysyms.Page_Down, gtk.keysyms.Page_Up):
            accel.connect_group(k, gtk.gdk.CONTROL_MASK, 0, self.on_tempo_accel)

        for k in (gtk.keysyms.plus, gtk.keysyms.equal, gtk.keysyms.KP_Add,
                  gtk.keysyms.minus, gtk.keysyms.KP_Subtract):
            accel.connect_group(k, gtk.gdk.CONTROL_MASK, 0, self.on_volume_accel)

        self.widgets['window_main'].add_accel_group(accel)

        self.widgets['item_view_markings'].set_active(self.config.view_markings)
        self.widgets['item_view_meter'].set_active(self.config.view_meter)
        self.widgets['item_view_speedtrainer'].set_active(self.config.view_speedtrainer)
        self.widgets['item_view_pattern'].set_active(self.config.view_pattern)
        self.widgets['item_view_profiles'].set_active(self.config.view_profiles)

        self.pattern_buttons = []
        # create one button now to avoid window size changes later on
        self.readjust_pattern_table(1)

        self.state_changed = run_idle_once(lambda: self.state_changed_callback())
        self.state_changed_callback = None

        self.klick.register_methods(self)


    # GUI callbacks

    def on_delete_event(self, w, ev):
        self.klick.quit()
        gtk.main_quit()

    def on_file_quit(self, i):
        self.widgets['window_main'].destroy()
        self.klick.quit()
        gtk.main_quit()

    def on_edit_preferences(self, i):
        prefs = self.widgets['dialog_preferences']
        prefs.run()
        prefs.hide()

    def on_view_markings_toggled(self, i):
        self.widgets['scale_tempo'].set_draw_value(i.get_active())
        self.config.view_markings = i.get_active()

    def on_view_speedtrainer_toggled(self, i):
        b = i.get_active()
        self.widgets['frame_speedtrainer'].set_property('visible', b)
        self.config.view_speedtrainer = b

    def on_view_meter_toggled(self, i):
        b = i.get_active()
        self.widgets['frame_meter'].set_property('visible', b)
        self.config.view_meter = b
        if not b:
            self.set_meter(0, 4)

    def on_view_pattern_toggled(self, i):
        b = i.get_active()
        self.widgets['frame_pattern'].set_property('visible', b)
        self.config.view_pattern = b
        if not b:
            self.klick.send('/simple/set_pattern', '')

    def on_view_profiles_toggled(self, i):
        b = i.get_active()
        self.widgets['vbox_profiles'].set_property('visible', b)
        self.config.view_profiles = b

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
        self.state_changed.queue()

    @gui_callback
    def on_tap_tempo(self, b):
        self.klick.send('/simple/tap', ('d', time.time()))

    def on_tempo_format_value(self, scale, value):
        if value < 40:      return "Larghissimo"
        elif value < 56:    return "Largo"
        elif value < 66:    return "Larghetto"
        elif value < 76:    return "Adagio"
        elif value < 108:   return "Andante"
        elif value < 120:   return "Moderato"
        elif value < 168:   return "Allegro"
        elif value < 200:   return "Presto"
        else:               return "Prestissimo"

    @gui_callback
    def on_speedtrainer_enable_toggled(self, b):
        a = b.get_active()
        self.widgets['spin_tempo_increment'].set_sensitive(a)
        self.widgets['spin_tempo_limit'].set_sensitive(a)
        self.config.speedtrainer = a
        if a:
            self.klick.send('/simple/set_tempo_increment', self.widgets['spin_tempo_increment'].get_value())
            self.klick.send('/simple/set_tempo_limit', int(self.widgets['spin_tempo_limit'].get_value()))
        else:
            self.klick.send('/simple/set_tempo_increment', 0.0)
        self.state_changed.queue()

    @gui_callback
    def on_tempo_increment_changed(self, b):
        self.klick.send('/simple/set_tempo_increment', b.get_value())
        self.state_changed.queue()

    @gui_callback
    def on_tempo_limit_changed(self, b):
        self.klick.send('/simple/set_tempo_limit', int(b.get_value()))
        self.state_changed.queue()

    @gui_callback
    def on_meter_toggled(self, b, data):
        if b.get_active():
            if data != None:
                self.set_meter(data[0], data[1])
            else:
                self.set_meter(int(self.widgets['spin_meter_beats'].get_value()),
                               int(self.widgets['spin_meter_denom'].get_value()))
        self.state_changed.queue()

    @gui_callback
    def on_meter_beats_changed(self, b):
        self.set_meter(int(self.widgets['spin_meter_beats'].get_value()),
                       int(self.widgets['spin_meter_denom'].get_value()))
        self.state_changed.queue()

    @gui_callback
    def on_meter_denom_changed(self, b):
        v = b.get_value()

        # make sure value is a power of two
        if v == self.config.denom:
            return
        elif v == self.config.denom - 0.5:
            # down arrow (step_inc is 0.5)
            denom = 2 ** (math.log(self.config.denom, 2) - 1)
        elif v == self.config.denom + 0.5:
            # up arrow
            denom = 2 ** (math.log(self.config.denom, 2) + 1)
        else:
            # keyboard input: use next power of two
            denom = 1
            while denom < v:
                denom *= 2

        b.set_value(denom)
        self.config.denom = denom

        self.set_meter(int(self.widgets['spin_meter_beats'].get_value()),
                       int(self.widgets['spin_meter_denom'].get_value()))
        self.state_changed.queue()

    def set_meter(self, beats, denom):
        if len(self.pattern_buttons):
            # make "even" meter non-emphasized by default
            if beats == 0:
                self.pattern_buttons[0].set_state(1)
            elif beats != 0 and self.config.beats == 0:
                self.pattern_buttons[0].set_state(2)

        self.klick.send('/simple/set_meter', beats, denom)

        self.readjust_pattern_table(beats)
        pattern = self.get_pattern()
        self.klick.send('/simple/set_pattern', pattern)

    @gui_callback
    def on_pattern_button_toggled(self, b):
        pattern = self.get_pattern()
        self.klick.send('/simple/set_pattern', pattern)
        self.state_changed.queue()

    @gui_callback
    def on_pattern_reset(self, b):
        self.klick.send('/simple/set_pattern', '')
        self.state_changed.queue()

    @gui_callback
    def on_start_stop(self, b):
        if self.widgets['align_stop'].get_property('visible'):
            self.klick.send('/metro/stop')
        else:
            self.klick.send('/metro/start')

    @gui_callback
    def on_volume_changed(self, r):
        self.klick.send('/config/set_volume', r.get_value())

    @gui_callback
    def on_tempo_accel(self, group, accel, key, mod):
        tempo = int(self.widgets['spin_tempo'].get_value())
        if   key == gtk.keysyms.Left:       tempo -= 1
        elif key == gtk.keysyms.Right:      tempo += 1
        elif key == gtk.keysyms.Down:       tempo -= 10
        elif key == gtk.keysyms.Up:         tempo += 10
        elif key == gtk.keysyms.Page_Down:  tempo /= 2
        elif key == gtk.keysyms.Page_Up:    tempo *= 2
        tempo = min(max(tempo, 1), 999)
        self.klick.send('/simple/set_tempo', tempo)
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


    # OSC callbacks

    @make_method('/simple/tempo', 'f')
    @osc_callback
    def simple_tempo_cb(self, path, args):
        self.widgets['scale_tempo'].set_value(args[0])
        self.widgets['spin_tempo'].set_value(args[0])
        self.config.tempo = args[0]

    @make_method('/simple/tempo_increment', 'f')
    @osc_callback
    def simple_tempo_increment_cb(self, path, args):
        if args[0]:
            self.widgets['spin_tempo_increment'].set_value(args[0])
            self.config.tempo_increment = args[0]

    @make_method('/simple/tempo_limit', 'f')
    @osc_callback
    def simple_tempo_limit_cb(self, path, args):
        self.widgets['spin_tempo_limit'].set_value(args[0])
        self.config.tempo_limit = args[0]

    @make_method('/simple/current_tempo', 'f')
    @osc_callback
    def simple_current_tempo_cb(self, path, args):
        if args[0]:
            self.widgets['window_main'].set_title("gtklick - " + str(int(args[0])))
        else:
            self.widgets['window_main'].set_title("gtklick")

    @make_method('/simple/meter', 'ii')
    @osc_callback
    def simple_meter_cb(self, path, args):
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
            self.config.beats = beats
            self.config.denom = 0
        else:
            # custom meter
            self.widgets['radio_meter_other'].set_active(True)
            self.widgets['hbox_meter_spins'].set_sensitive(True)
            self.widgets['spin_meter_beats'].set_value(beats)
            self.widgets['spin_meter_denom'].set_value(denom)
            self.config.beats = beats
            self.config.denom = denom

        # set active radio button as mnemonic widget
        w = [x for x in self.widgets['radio_meter_other'].get_group() if x.get_active()][0]
        self.widgets['label_frame_meter'].set_mnemonic_widget(w)

        self.readjust_pattern_table(beats)

    @make_method('/simple/pattern', 's')
    @osc_callback
    def simple_pattern_cb(self, path, args):
        pattern = args[0]
        if len(pattern) != len(self.pattern_buttons) or not all(x in '.xX' for x in pattern):
            pattern = self.default_pattern()
        for p, b in itertools.izip(pattern, self.pattern_buttons):
            b.set_state('.xX'.index(p))
        self.config.pattern = pattern

    @make_method('/metro/active', 'i')
    @osc_callback
    def simple_active_cb(self, path, args):
        if args[0]:
            self.widgets['align_start'].hide()
            self.widgets['align_stop'].show()
        else:
            self.widgets['align_stop'].hide()
            self.widgets['align_start'].show()

    @make_method('/config/volume', 'f')
    @osc_callback
    def config_volume_cb(self, path, args):
        self.widgets['scale_volume'].set_value(args[0])
        self.config.volume = args[0]


    def readjust_pattern_table(self, beats):
        n = max(1, beats)
        table = self.widgets['table_pattern']

        if n < len(self.pattern_buttons):
            # reduce table size
            for b in self.pattern_buttons[n:]:
                self.pattern_buttons.remove(b)
                table.remove(b)
            table.resize(max((n-1)//6 + 1, 2), 6)

        elif n > len(self.pattern_buttons):
            # increase table size
            table.resize(max((n-1)//6 + 1, 2), 6)
            for x in range(len(self.pattern_buttons), n):
                b = TristateCheckButton(str(x+1))
                b.set_state(2 if x == 0 else 1)
                b.connect('toggled', self.on_pattern_button_toggled)
                row, col = x // 6, x % 6
                table.attach(b, col, col + 1, row, row + 1)
                self.pattern_buttons.append(b)
                if x == 0:
                    self.widgets['label_frame_pattern'].set_mnemonic_widget(b)
                b.show()

    def get_pattern(self):
        pattern = ''.join('.xX'[s] for s in (n.get_state() for n in self.pattern_buttons))
        return pattern if pattern != self.default_pattern() else ''

    def default_pattern(self):
        if (len(self.pattern_buttons) > 1):
            pattern = 'X' + 'x'*(len(self.pattern_buttons)-1)
        else:
            pattern = 'x'
        return pattern
