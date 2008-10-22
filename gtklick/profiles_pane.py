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
import gobject

from misc import weakref_method

from gtklick_config import Profile


class ProfilesPane:
    def __init__(self, wtree, widgets, klick, config, mainwin):
        self.widgets = widgets
        self.klick = klick
        self.config = config
        self.mainwin = mainwin

        wtree.signal_autoconnect({
            'on_profile_add':       self.on_profile_add,
            'on_profile_remove':    self.on_profile_remove,
            'on_profile_save':      self.on_profile_save,
            'on_profile_rename':    self.on_profile_rename,
        })

        # create treeview. doing this within glade somehow breaks dnd. weird...
        self.treeview = gtk.TreeView()
        self.treeview.set_headers_visible(False)
        self.treeview.set_enable_search(False)
        self.treeview.set_reorderable(True)

        self.widgets['scrolledwindow_profiles'].add(self.treeview)
        self.widgets['label_frame_profiles'].set_mnemonic_widget(self.treeview)
        self.treeview.show()

        # create model
        self.model = gtk.ListStore(str, Profile)
        self.treeview.set_model(self.model)

        # create renderer/column
        self.renderer = gtk.CellRendererText()
        self.column = gtk.TreeViewColumn(None, self.renderer, text=0)
        self.treeview.append_column(self.column)

        # connect signals
        self.treeview.get_selection().connect('changed', self.on_selection_changed)
        self.treeview.connect('row-activated', self.on_row_activated)
        # create a weak reference to the callback function, to prevent cyclic references.
        # sometimes PyGTK astounds me...
        self.renderer.connect('edited', weakref_method(self.on_cell_edited))

        self.model.connect('row-changed', self.on_row_changed)
        self.model.connect('row-deleted', self.on_row_deleted)
        self.enable_buttons(False)

        self.idle_pending = False

        # populate treeview with profiles from config file
        for p in self.config.get_profiles():
            self.model.append([p.name, p])


    def on_row_activated(self, w, path, view_column):
        i = self.model.get_iter(path)
        self.activate_profile(i)

    def on_selection_changed(self, selection):
        i = selection.get_selected()[1]
        if i:
            self.activate_profile(i)
            self.enable_buttons(True)

    def on_cell_edited(self, cell, path, new_text):
        self.model[path][0] = new_text
        self.model[path][1].name = new_text
        # renaming finished, make cell non-editable again
        self.renderer.set_property('editable', False)

    def on_row_changed(self, w, path, i):
        # enable/disable buttons and save profiles. doing this in an idle callback seems to be
        # the only way to avoid spurious calls while the treeview is in an intermediate state
        self.queue_idle()

    def on_row_deleted(self, w, path):
        self.queue_idle()

    def on_profile_add(self, b):
        i = self.model.append(["unnamed", self.current_profile("unnamed")])
        # temporarily make cells editable
        self.renderer.set_property('editable', True)
        self.treeview.set_cursor(self.model.get_path(i), self.column, start_editing=True)

    def on_profile_remove(self, b):
        selection = self.treeview.get_selection()
        i = selection.get_selected()[1]
        if i:
            path = self.model.get_path(i)
            self.model.remove(i)

            # select next item
            selection.select_path(path)
            if not selection.path_is_selected(path):
                row = path[0]-1
                if row >= 0:
                    selection.select_path(row)

    def on_profile_save(self, b):
        selection = self.treeview.get_selection()
        i = selection.get_selected()[1]
        if i:
            # replace selected profile
            self.model.set_value(i, 1, self.current_profile(self.model.get_value(i, 0)))

    def on_profile_rename(self, b):
        selection = self.treeview.get_selection()
        i = selection.get_selected()[1]
        if i:
            # temporarily make cell editable
            self.renderer.set_property('editable', True)
            self.treeview.set_cursor(self.model.get_path(i), self.column, start_editing=True)

    def activate_profile(self, i):
        v = self.model.get_value(i, 1)
        self.klick.send('/simple/set_tempo', v.tempo)
        self.widgets['spin_tempo_increment'].set_value(v.tempo_increment)
        self.widgets['check_speedtrainer_enable'].set_active(v.speedtrainer)
        self.klick.send('/simple/set_tempo_increment', v.tempo_increment if v.speedtrainer else 0.0)
        self.klick.send('/simple/set_tempo_limit', v.tempo_limit)
        self.klick.send('/simple/set_meter', v.beats, v.denom)
        self.klick.send('/simple/set_pattern', v.pattern)

    def current_profile(self, name):
        # create profile from the current state of the GUI
        if self.widgets['radio_meter_other'].get_active():
            beats = int(self.widgets['spin_meter_beats'].get_value())
            denom = int(self.widgets['spin_meter_denom'].get_value())
        else:
            beats = 1 if self.widgets['radio_meter_even'].get_active() else \
                    2 if self.widgets['radio_meter_24'].get_active() else \
                    3 if self.widgets['radio_meter_34'].get_active() else 4
            denom = 4

        return Profile(
            name,
            int(self.widgets['spin_tempo'].get_value()),
            self.widgets['check_speedtrainer_enable'].get_active(),
            self.widgets['spin_tempo_increment'].get_value(),
            int(self.widgets['spin_tempo_limit'].get_value()),
            beats,
            denom,
            self.mainwin.get_pattern()
        )

    def enable_buttons(self, enable):
        self.widgets['btn_profile_remove'].set_sensitive(enable)
        self.widgets['btn_profile_save'].set_sensitive(enable)
        self.widgets['btn_profile_rename'].set_sensitive(enable)

    def queue_idle(self):
        # avoid redundant calls of the idle handler
        if not self.idle_pending:
            gobject.idle_add(self.idle_handler)
            self.idle_pending = True

    def idle_handler(self):
        self.idle_pending = False
        # enable buttons only if a profile is selected
        i = self.treeview.get_selection().get_selected()[1]
        self.enable_buttons(bool(i))
        # save all profiles
        self.save_profiles()
        return False

    def save_profiles(self):
        # save all profiles, write config file
        self.config.set_profiles([i[1] for i in self.model])
        self.config.write()
