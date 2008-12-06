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

import math

from klick_backend import make_method
from misc import gui_callback, osc_callback


class PreferencesDialog:
    def __init__(self):
        wtree.signal_autoconnect({
            'on_sound_square_toggled':      (self.on_sound_toggled, 0),
            'on_sound_sine_toggled':        (self.on_sound_toggled, 1),
            'on_sound_noise_toggled':       (self.on_sound_toggled, 2),
            'on_sound_click_toggled':       (self.on_sound_toggled, 3),
            'on_sound_custom_toggled':      (self.on_sound_toggled, -1),

            'on_accented_selection_changed':self.on_sound_selection_changed,
            'on_normal_selection_changed':  self.on_sound_selection_changed,

            'on_sound_pitch_changed':       self.on_sound_pitch_changed,

            'on_connect_auto_toggled':      (self.on_connect_toggled, True),
            'on_connect_manual_toggled':    (self.on_connect_toggled, False),
            'on_connect_add':               self.on_connect_add,
            'on_connect_remove':            self.on_connect_remove,

            'on_preferences_delete_event':  self.on_delete_event,
            'on_preferences_close':         self.on_close,
        })

        widgets['vbox_filechoosers'].set_sensitive(config.prefs_sound == -1)

        # build JACK connection treeview
        self.treeview_ports = widgets['treeview_connect_ports']
        self.model_ports = gtk.ListStore(str)
        self.treeview_ports.set_model(self.model_ports)
        self.model_avail = gtk.ListStore(str)

        renderer = gtk.CellRendererCombo()
        renderer.set_property('model', self.model_avail)
        renderer.set_property('text-column', 0)
        renderer.set_property('editable', True)
        self.column = gtk.TreeViewColumn(None, renderer, text=0)
        self.treeview_ports.append_column(self.column)

        self.treeview_ports.get_selection().connect('changed', self.on_connect_selection_changed)
        renderer.connect('editing-started', self.on_connect_editing_started)
        renderer.connect('editing-canceled', self.on_connect_editing_canceled)
        renderer.connect('edited', self.on_connect_cell_edited)
        self.model_ports.connect('row-deleted', lambda w, p: self.update_connect_ports())

        widgets['btn_connect_remove'].set_sensitive(False)
        self.ports_avail = []

        klick.register_methods(self)


    # GUI callbacks

    def on_delete_event(self, w, ev):
        widgets['dialog_preferences'].hide()
        return 1

    def on_close(self, b):
        widgets['dialog_preferences'].hide()

    @gui_callback
    def on_sound_toggled(self, b, data):
        if b.get_active():
            widgets['vbox_filechoosers'].set_sensitive(data == -1)
            if data >= 0:
                klick.send('/config/set_sound', data)
            else:
                a = widgets['filechooser_accented'].get_filename()
                b = widgets['filechooser_normal'].get_filename()
                if a and b:
                    klick.send('/config/set_sound', a, b)
                else:
                    # set silent
                    klick.send('/config/set_sound', -2)

    @gui_callback
    def on_sound_selection_changed(self, chooser):
        a = widgets['filechooser_accented'].get_filename()
        b = widgets['filechooser_normal'].get_filename()
        if a and b:
            klick.send('/config/set_sound', a, b)
        else:
            # set silent
            klick.send('/config/set_sound', -2)

    @gui_callback
    def on_sound_pitch_changed(self, r):
        # convert octave to factor
        v = 2**r.get_value()
        klick.send('/config/set_sound_pitch', v, v)

    @gui_callback
    def on_connect_toggled(self, b, data):
        if b.get_active():
            widgets['hbox_connect_manual'].set_sensitive(data == False)
            if data:
                klick.send('/config/disconnect_all')
                klick.send('/config/autoconnect')
            else:
                self.update_connect_ports()
            config.prefs_autoconnect = data

    def on_connect_add(self, b):
        if klick.get_version() < (0, 10, 0):
            m = gtk.MessageDialog(widgets['dialog_preferences'], 0, gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
                                  "please upgrade to klick 0.10.0 or later for this to work.")
            m.run()
            m.destroy()
            return

        if not all(x[0] for x in self.model_ports):
            return
        i = self.model_ports.append([''])
        self.treeview_ports.set_cursor(self.model_ports.get_path(i), self.column, start_editing=True)

    def on_connect_remove(self, b):
        selection = self.treeview_ports.get_selection()
        i = selection.get_selected()[1]
        if i:
            treeview_remove(self.model_ports, selection, i)
        self.update_connect_ports()

    def on_connect_selection_changed(self, selection):
        i = selection.get_selected()[1]
        widgets['btn_connect_remove'].set_sensitive(bool(i))

    def on_connect_editing_started(self, cell, editable, path):
        klick.send('/config/get_available_ports')

    def on_connect_editing_canceled(self, cell):
        selection = self.treeview_ports.get_selection()
        i = selection.get_selected()[1]
        if i and not self.model_ports.get_value(i, 0):
            self.model_ports.remove(i)

    def on_connect_cell_edited(self, cell, path, new_text):
        if new_text:
            self.model_ports[path][0] = new_text
        else:
            self.model_ports.remove(self.model_ports.get_iter(path))
        self.update_connect_ports()

    def update_connect_ports(self):
        ports = [x[0] for x in self.model_ports]
        klick.send('/config/disconnect_all')
        klick.send('/config/connect', *ports)
        config.prefs_connect_ports = '\0'.join(ports)


    # OSC callbacks

    @make_method('/config/sound', 'i')
    @osc_callback
    def sound_cb(self, path, args):
        sound = args[0]
        if sound < 0 or sound > 3: return
        w = ('radio_sound_square', 'radio_sound_sine', 'radio_sound_noise', 'radio_sound_click')[sound]
        widgets[w].set_active(True)
        config.prefs_sound = sound

    @make_method('/config/sound', 'ss')
    @osc_callback
    def sound_custom_cb(self, path, args):
        widgets['radio_sound_custom'].set_active(True)

        if args[0] != widgets['filechooser_accented'].get_filename():
            widgets['filechooser_accented'].set_filename(args[0])
        if args[1] != widgets['filechooser_normal'].get_filename():
            widgets['filechooser_normal'].set_filename(args[1])

        config.prefs_sound = -1
        config.prefs_sound_accented = args[0]
        config.prefs_sound_normal = args[1]

    @make_method('/config/sound_pitch', 'ff')
    @osc_callback
    def sound_pitch_cb(self, path, args):
        # for now let's assume that args[0] == args[1]
        v = math.log(args[0], 2)
        widgets['scale_sound_pitch'].set_value(v)
        config.prefs_sound_pitch = v

    @make_method('/config/available_ports', None)
    @osc_callback
    def available_ports_cb(self, path, args):
        if args != self.ports_avail:
            self.ports_avail = args
            self.model_avail.clear()
            for x in self.ports_avail:
                self.model_avail.append([x])

    @make_method('/config/sound_loading_failed', 's')
    @osc_callback
    def sound_loading_failed_cb(self, path, args):
        klick.send('/config/set_sound', -2)
        m = gtk.MessageDialog(widgets['dialog_preferences'], 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, "couldn't load file '%s'." % args[0])
        m.run()
        m.destroy()
