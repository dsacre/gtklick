# -*- coding: utf-8 -*-
#
# gtklick
#
# Copyright (C) 2008-2010  Dominic Sacré  <dominic.sacre@gmx.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from gi.repository import Gtk

import time
import math
import itertools

from klick_backend import make_method
from misc import gui_callback, osc_callback
import misc


class MainWindow:
    def __init__(self):
        # why doesn't glade do this?
        widgets['spin_meter_beats'].set_value(4)
        widgets['spin_meter_denom'].set_value(4)

        #wtree.signal_autoconnect({
        wtree.connect_signals({
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
            'on_tempo_start_changed':           self.on_tempo_start_changed,
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
            'on_window_main_key_press_event':   self.on_key_press_event,
        })

        widgets['item_view_markings'].set_active(config.view_markings)
        widgets['item_view_meter'].set_active(config.view_meter)
        widgets['item_view_speedtrainer'].set_active(config.view_speedtrainer)
        widgets['item_view_pattern'].set_active(config.view_pattern)
        widgets['item_view_profiles'].set_active(config.view_profiles)

        self.pattern_buttons = []
        # create one button now to avoid window size changes later on
        self.readjust_pattern_table(1)

        self.state_changed = misc.run_idle_once(lambda: self.state_changed_callback())
        self.state_changed_callback = None

        klick.register_methods(self)


    # GUI callbacks

    def on_delete_event(self, w, ev):
        klick.quit()
        Gtk.main_quit()

    def on_file_quit(self, i):
        widgets['window_main'].destroy()
        klick.quit()
        Gtk.main_quit()

    def on_edit_preferences(self, i):
        widgets['dialog_preferences'].show()

    def on_view_markings_toggled(self, i):
        widgets['scale_tempo'].set_draw_value(i.get_active())
        config.view_markings = i.get_active()

    def on_view_speedtrainer_toggled(self, i):
        b = i.get_active()
        widgets['frame_speedtrainer'].set_property('visible', b)
        config.view_speedtrainer = b

    def on_view_meter_toggled(self, i):
        b = i.get_active()
        widgets['frame_meter'].set_property('visible', b)
        config.view_meter = b
        if not b:
            self.set_meter(0, 4)

    def on_view_pattern_toggled(self, i):
        b = i.get_active()
        widgets['frame_pattern'].set_property('visible', b)
        config.view_pattern = b
        if not b:
            klick.send('/simple/set_pattern', '')

    def on_view_profiles_toggled(self, i):
        b = i.get_active()
        widgets['vbox_profiles'].set_property('visible', b)
        config.view_profiles = b

    def on_help_shortcuts(self, i):
        shortcuts = widgets['dialog_shortcuts']
        shortcuts.run()
        shortcuts.hide()

    def on_help_about(self, i):
        about = widgets['dialog_about']
        try:
            # d'oh!
            about.set_program_name("gtklick")
        except AttributeError:
            pass
        about.run()
        about.hide()

    @gui_callback
    def on_tempo_changed(self, r):
        klick.send('/simple/set_tempo', int(r.get_value()))

    @gui_callback
    def on_tap_tempo(self, b):
        klick.send('/simple/tap', ('d', time.time()))

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
        widgets['spin_tempo_increment'].set_sensitive(a)
        widgets['spin_tempo_start'].set_sensitive(a)
        config.speedtrainer = a
        if a:
            klick.send('/simple/set_tempo_increment', widgets['spin_tempo_increment'].get_value())
            klick.send('/simple/set_tempo_start', int(widgets['spin_tempo_start'].get_value()))
        else:
            widgets['spin_tempo_increment'].select_region(0, 0)
            widgets['spin_tempo_start'].select_region(0, 0)
            klick.send('/simple/set_tempo_increment', 0.0)

    @gui_callback
    def on_tempo_increment_changed(self, b):
        klick.send('/simple/set_tempo_increment', b.get_value())

    @gui_callback
    def on_tempo_start_changed(self, b):
        klick.send('/simple/set_tempo_start', int(b.get_value()))

    @gui_callback
    def on_meter_toggled(self, b, data):
        if b.get_active():
            if data != None:
                self.set_meter(data[0], data[1])
            else:
                self.set_meter(int(widgets['spin_meter_beats'].get_value()), int(widgets['spin_meter_denom'].get_value()))

    @gui_callback
    def on_meter_beats_changed(self, b):
        self.set_meter(int(widgets['spin_meter_beats'].get_value()), int(widgets['spin_meter_denom'].get_value()))

    @gui_callback
    def on_meter_denom_changed(self, b):
        v = b.get_value()

        # make sure value is a power of two
        if v == config.denom:
            return
        elif v == config.denom - 0.5:
            # down arrow (step_inc is 0.5)
            denom = 2 ** (math.log(config.denom, 2) - 1)
        elif v == config.denom + 0.5:
            # up arrow
            denom = 2 ** (math.log(config.denom, 2) + 1)
        else:
            # keyboard input: use next power of two
            denom = 1
            while denom < v:
                denom *= 2

        b.set_value(denom)
        config.denom = denom

        self.set_meter(int(widgets['spin_meter_beats'].get_value()), int(widgets['spin_meter_denom'].get_value()))

    def set_meter(self, beats, denom):
        if len(self.pattern_buttons):
            # make "even" meter non-emphasized by default
            if beats == 0:
                self.pattern_buttons[0].set_state(1)
            elif beats != 0 and config.beats == 0:
                self.pattern_buttons[0].set_state(2)

        klick.send('/simple/set_meter', beats, denom)

        self.readjust_pattern_table(beats)
        klick.send('/simple/set_pattern', self.get_pattern(beats))

    @gui_callback
    def on_pattern_button_toggled(self, b):
        klick.send('/simple/set_pattern', self.get_pattern())

    @gui_callback
    def on_pattern_reset(self, b):
        klick.send('/simple/set_pattern', '')

    @gui_callback
    def on_start_stop(self, b):
        if widgets['align_stop'].get_property('visible'):
            klick.send('/metro/stop')
        else:
            klick.send('/metro/start')

    @gui_callback
    def on_volume_changed(self, r):
        klick.send('/config/set_volume', r.get_value())

    @gui_callback
    def on_key_press_event(self, widget, event):
        key = event.keyval
        focus = widgets['window_main'].get_focus()

        # make escape remove focus from spinbuttons
        if event.keyval == Gdk.KEY_Escape and isinstance(focus, Gtk.SpinButton):
            widgets['window_main'].set_focus(None)
            return True

        # don't allow shortcuts in spinbuttons and entrys
        if isinstance(focus, (Gtk.SpinButton, Gtk.Entry)):
            return False

        # use keys with ctrl modifier to get default GTK behaviour
        if event.get_state() & Gdk.ModifierType.CONTROL_MASK and \
            key in (Gdk.KEY_Left, Gdk.KEY_Right, Gdk.KEY_Down, Gdk.KEY_Up, Gdk.KEY_space, Gdk.KEY_Return):
            #event.get_state() &= ~Gdk.ModifierType.CONTROL_MASK
            thisState = event.state 
            thisState &= ~gtk.gdk.CONTROL_MASK
            event.state = thisState
            return False

        # tempo shortcuts
        if key in (Gdk.KEY_Left, Gdk.KEY_Right, Gdk.KEY_Down, Gdk.KEY_Up, Gdk.KEY_Page_Down, Gdk.KEY_Page_Up):
            tempo = int(widgets['spin_tempo'].get_value())
            if   key == Gdk.KEY_Left:       tempo -= 1
            elif key == Gdk.KEY_Right:      tempo += 1
            elif key == Gdk.KEY_Down:       tempo -= 10
            elif key == Gdk.KEY_Up:         tempo += 10
            elif key == Gdk.KEY_Page_Down:  tempo /= 2
            elif key == Gdk.KEY_Page_Up:    tempo *= 2
            tempo = min(max(tempo, 1), 999)
            klick.send('/simple/set_tempo', tempo)
            return True

        # volume shortcuts
        elif key in (Gdk.KEY_plus, Gdk.KEY_equal, Gdk.KEY_KP_Add, Gdk.KEY_minus, Gdk.KEY_KP_Subtract):
            volume = widgets['scale_volume'].get_value()
            if key in (Gdk.KEY_minus, Gdk.KEY_KP_Subtract):
                volume -= 0.1
            elif key in (Gdk.KEY_plus, Gdk.KEY_equal, Gdk.KEY_KP_Add):
                volume += 0.1
            volume = min(max(volume, 0.0), 1.0)
            klick.send('/config/set_volume', volume)
            return True

        # start/stop
        elif key == Gdk.KEY_space:
            if widgets['align_stop'].get_property('visible'):
                klick.send('/metro/stop')
            else:
                klick.send('/metro/start')
            return True

        # tap tempo
        elif key == Gdk.KEY_Return:
            klick.send('/simple/tap', ('d', time.time()))
            return True

        return False


    # OSC callbacks

    @make_method('/simple/tempo', 'f')
    @osc_callback
    def simple_tempo_cb(self, path, args):
        tempo = args[0]
        changed = tempo != config.tempo
        widgets['scale_tempo'].set_value(int(tempo))
        widgets['spin_tempo'].set_value(int(tempo))
        config.tempo = tempo
        if changed:
            self.state_changed.queue()

    @make_method('/simple/tempo_increment', 'f')
    @osc_callback
    def simple_tempo_increment_cb(self, path, args):
        tempo_increment = args[0]
        changed = tempo_increment != config.tempo_increment
        if tempo_increment:
            widgets['spin_tempo_increment'].set_value(tempo_increment)
            config.tempo_increment = tempo_increment
        if changed:
            self.state_changed.queue()

    @make_method('/simple/tempo_start', 'f')
    @osc_callback
    def simple_tempo_start_cb(self, path, args):
        tempo_start = args[0]
        changed = tempo_start != config.tempo_start
        widgets['spin_tempo_start'].set_value(int(tempo_start))
        config.tempo_start = tempo_start
        if changed:
            self.state_changed.queue()

    @make_method('/simple/current_tempo', 'f')
    @osc_callback
    def simple_current_tempo_cb(self, path, args):
        if args[0]:
            widgets['window_main'].set_title("gtklick - " + str(int(args[0])))
        else:
            widgets['window_main'].set_title("gtklick")

    @make_method('/simple/meter', 'ii')
    @osc_callback
    def simple_meter_cb(self, path, args):
        beats, denom = args
        changed = beats != config.beats or denom != config.denom

        if beats in (0, 2, 3, 4) and denom == 4 and not widgets['radio_meter_other'].get_active():
            # standard meter
            widgets['hbox_meter_spins'].set_sensitive(False)
            widgets['spin_meter_beats'].select_region(0, 0)
            widgets['spin_meter_denom'].select_region(0, 0)
            if beats == 0:
                widgets['radio_meter_even'].set_active(True)
            elif beats == 2:
                widgets['radio_meter_24'].set_active(True)
            elif beats == 3:
                widgets['radio_meter_34'].set_active(True)
            elif beats == 4:
                widgets['radio_meter_44'].set_active(True)
            config.beats = beats
            config.denom = 0
        else:
            # custom meter
            widgets['radio_meter_other'].set_active(True)
            widgets['hbox_meter_spins'].set_sensitive(True)
            widgets['spin_meter_beats'].set_value(beats)
            widgets['spin_meter_denom'].set_value(denom)
            config.beats = beats
            config.denom = denom

        # set active radio button as mnemonic widget
        w = [x for x in widgets['radio_meter_other'].get_group() if x.get_active()][0]
        widgets['label_frame_meter'].set_mnemonic_widget(w)

        self.readjust_pattern_table(beats)
        if changed:
            self.state_changed.queue()

    @make_method('/simple/pattern', 's')
    @osc_callback
    def simple_pattern_cb(self, path, args):
        pattern = args[0]
        if len(pattern) != len(self.pattern_buttons) or not all(x in '.xX' for x in pattern):
            # invalid pattern, use default
            pattern = self.default_pattern(config.beats)
        changed = pattern != config.pattern
        for p, b in zip(pattern, self.pattern_buttons):
            b.set_state('.xX'.index(p))
        config.pattern = pattern
        if changed:
            self.state_changed.queue()

    @make_method('/metro/active', 'i')
    @osc_callback
    def simple_active_cb(self, path, args):
        if args[0]:
            widgets['align_start'].hide()
            widgets['align_stop'].show()
        else:
            widgets['align_stop'].hide()
            widgets['align_start'].show()

    @make_method('/config/volume', 'f')
    @osc_callback
    def config_volume_cb(self, path, args):
        widgets['scale_volume'].set_value(args[0])
        config.volume = args[0]


    def readjust_pattern_table(self, beats):
        n = max(1, beats)
        table = widgets['table_pattern']

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
                b = misc.TristateCheckButton(str(x+1))
                b.set_state(2 if x == 0 else 1)
                b.connect('toggled', self.on_pattern_button_toggled)
                row, col = x // 6, x % 6
                table.attach(b, col, col + 1, row, row + 1)
                self.pattern_buttons.append(b)
                if x == 0:
                    widgets['label_frame_pattern'].set_mnemonic_widget(b)
                b.show()

    def get_pattern(self, beats=None):
        if beats == None:
            beats = config.beats
        pattern = ''.join('.xX'[s] for s in (n.get_state() for n in self.pattern_buttons))
        return pattern if pattern != self.default_pattern(beats) else ''

    def default_pattern(self, beats):
        return 'X' + 'x'*(beats-1) if beats > 0 else 'x'
