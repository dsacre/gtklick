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
            'on_connect_auto_toggled':  (self.on_connect_toggled, True),
            'on_connect_manual_toggled':(self.on_connect_toggled, False),
            'on_connect_add':           self.on_connect_add,
            'on_connect_remove':        self.on_connect_remove,
        })

        self.treeview_ports = self.widgets['treeview_connect_ports']

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

        self.widgets['btn_connect_remove'].set_sensitive(False)
        self.ports_avail = []

        self.klick.register_methods(self)

    @gui_callback
    def on_sound_toggled(self, b, data):
        if b.get_active():
            self.klick.send('/config/set_sound', data)

    @gui_callback
    def on_connect_toggled(self, b, data):
        if b.get_active():
            self.widgets['hbox_connect_manual'].set_sensitive(data == False)
            if data:
                self.klick.send('/config/disconnect_all')
                self.klick.send('/config/autoconnect')
            else:
                self.update_connect_ports()
            self.config.prefs_autoconnect = data

    def on_connect_add(self, b):
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
        self.widgets['btn_connect_remove'].set_sensitive(bool(i))

    def on_connect_editing_started(self, cell, editable, path):
        self.klick.send('/config/get_available_ports')

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
        self.klick.send('/config/disconnect_all')
        self.klick.send('/config/connect', *ports)
        self.config.prefs_connect_ports = '\0'.join(ports)

    @make_method('/config/sound', 'i')
    @osc_callback
    def sound_cb(self, path, args):
        sound = args[0]
        if sound < 0 or sound > 3: return
        w = ('radio_sound_square', 'radio_sound_sine', 'radio_sound_noise', 'radio_sound_click')[sound]
        self.widgets[w].set_active(True)
        self.config.prefs_sound = sound

    @make_method('/config/available_ports', None)
    def available_ports_cb(self, path, args):
        if args != self.ports_avail:
            self.ports_avail = args
            self.model_avail.clear()
            for x in self.ports_avail:
                self.model_avail.append([x])
