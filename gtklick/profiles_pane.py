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
from gi.repository import GObject

import cgi

import gtklick_config
import misc


class ProfilesPane:
    def __init__(self, mainwin):
        self.mainwin = mainwin

        wtree.signal_autoconnect({
            'on_profile_add':       self.on_profile_add,
            'on_profile_remove':    self.on_profile_remove,
            'on_profile_save':      self.on_profile_save,
            'on_profile_rename':    self.on_profile_rename,
        })

        # create treeview. doing this within glade somehow breaks dnd. weird...
        self.treeview = Gtk.TreeView()
        self.treeview.set_headers_visible(False)
        self.treeview.set_enable_search(False)
        self.treeview.set_reorderable(True)

        wtree.get_object('scrolledwindow_profiles').add(self.treeview)
        wtree.get_object('label_frame_profiles').set_mnemonic_widget(self.treeview)
        self.treeview.show()

        # create model
        self.model = Gtk.ListStore(str, gtklick_config.Profile)
        self.treeview.set_model(self.model)

        # create renderer/column
        self.renderer = Gtk.CellRendererText()
        self.column = Gtk.TreeViewColumn(None, self.renderer, markup=0)
        self.treeview.append_column(self.column)

        # connect signals
        self.treeview.get_selection().connect('changed', self.on_selection_changed)
        self.treeview.connect('row-activated', self.on_row_activated)
        # create a weak reference to the callback function, to prevent cyclic references.
        # sometimes PyGTK astounds me...
        self.renderer.connect('edited', misc.weakref_method(self.on_cell_edited))

        self.model.connect('row-changed', self.on_row_changed)
        self.model.connect('row-deleted', self.on_row_deleted)
        self.enable_buttons(False)

        self.idle = misc.run_idle_once(self.idle_handler)

        self.track_changes = False

        # populate treeview with profiles from config file
        for p in config.get_profiles():
            self.model.append([cgi.escape(p.name), p])

        self.mainwin.state_changed_callback = self.state_changed_callback


    def on_row_activated(self, w, path, view_column):
        # reset profile name
        self.model[path][0] = cgi.escape(self.model[path][1].name)

        i = self.model.get_iter(path)
        self.activate_profile(i)

    def on_selection_changed(self, selection):
        # reset all profile names, since we don't know which one was previously selected
        for p in self.model:
            p[0] = cgi.escape(p[1].name)

        i = selection.get_selected()[1]
        if i:
            self.activate_profile(i)
            self.enable_buttons(True)
        else:
            self.idle.queue()

    def on_cell_edited(self, cell, path, new_text):
        self.model[path][0] = cgi.escape(new_text)
        self.model[path][1].name = new_text
        # renaming finished, make cell non-editable again
        self.renderer.set_property('editable', False)

    def on_row_changed(self, w, path, i):
        # enable/disable buttons and save profiles. doing this in an idle callback seems to be
        # the only way to avoid spurious calls while the treeview is in an intermediate state
        self.idle.queue()

    def on_row_deleted(self, w, path):
        self.idle.queue()

    def on_profile_add(self, b):
        i = self.model.append(["unnamed", self.current_profile("unnamed")])
        # temporarily make cells editable
        self.renderer.set_property('editable', True)
        self.treeview.set_cursor(self.model.get_path(i), self.column, start_editing=True)

    def on_profile_remove(self, b):
        selection = self.treeview.get_selection()
        i = selection.get_selected()[1]
        if i:
            misc.treeview_remove(self.model, selection, i)

        # this is needed when removing a newly added profile before 'edited' has been sent
        self.renderer.set_property('editable', False)

    def on_profile_save(self, b):
        selection = self.treeview.get_selection()
        i = selection.get_selected()[1]
        if i:
            path = self.model.get_path(i)
            # replace selected profile
            self.model[path][0] = cgi.escape(self.model[path][1].name)
            self.model[path][1] = self.current_profile(self.model[path][1].name)

    def on_profile_rename(self, b):
        selection = self.treeview.get_selection()
        i = selection.get_selected()[1]
        if i:
            # temporarily make cell editable
            self.renderer.set_property('editable', True)
            self.treeview.set_cursor(self.model.get_path(i), self.column, start_editing=True)

    def activate_profile(self, i):
        v = self.model.get_value(i, 1)

        # ignore state changes while activating the profile
        self.track_changes = False
        # sending and receiving all OSC messages takes, uhm... so we need to wait at least... oh well...
        GObject.timeout_add(500, lambda: setattr(self, 'track_changes', True))

        klick.send('/simple/set_tempo', v.tempo)
        wtree.get_object('spin_tempo_increment').set_value(v.tempo_increment)
        wtree.get_object('check_speedtrainer_enable').set_active(v.speedtrainer)
        klick.send('/simple/set_tempo_increment', v.tempo_increment if v.speedtrainer else 0.0)
        klick.send('/simple/set_tempo_start', v.tempo_start)

        if v.denom:
            misc.do_quietly(lambda: wtree.get_object('radio_meter_other').set_active(True))
        else:
            # focus any radio button other than "other"
            misc.do_quietly(lambda: wtree.get_object('radio_meter_44').set_active(True))
        klick.send('/simple/set_meter', v.beats, v.denom if v.denom else 4)

        klick.send('/simple/set_pattern', v.pattern)

        # show all relevant frames
        if v.speedtrainer:
            wtree.get_object('item_view_speedtrainer').set_active(True)
        if (v.beats, v.denom) != (0, 4):
            wtree.get_object('item_view_meter').set_active(True)
        if v.pattern != '':
            wtree.get_object('item_view_pattern').set_active(True)

    def current_profile(self, name):
        # create profile from the current state of the GUI
        if wtree.get_object('radio_meter_other').get_active():
            beats = int(wtree.get_object('spin_meter_beats').get_value())
            denom = int(wtree.get_object('spin_meter_denom').get_value())
        else:
            beats = 0 if wtree.get_object('radio_meter_even').get_active() else \
                    2 if wtree.get_object('radio_meter_24').get_active() else \
                    3 if wtree.get_object('radio_meter_34').get_active() else 4
            denom = 0

        return gtklick_config.Profile(
            name,
            int(wtree.get_object('spin_tempo').get_value()),
            wtree.get_object('check_speedtrainer_enable').get_active(),
            wtree.get_object('spin_tempo_increment').get_value(),
            int(wtree.get_object('spin_tempo_start').get_value()),
            beats,
            denom,
            self.mainwin.get_pattern()
        )

    def enable_buttons(self, enable):
        wtree.get_object('btn_profile_remove').set_sensitive(enable)
        wtree.get_object('btn_profile_save').set_sensitive(enable)
        wtree.get_object('btn_profile_rename').set_sensitive(enable)

    def idle_handler(self):
        # enable buttons only if a profile is selected
        i = self.treeview.get_selection().get_selected()[1]
        self.enable_buttons(bool(i))
        # save all profiles
        self.save_profiles()

    def save_profiles(self):
        # save all profiles, write config file
        config.set_profiles([i[1] for i in self.model])
        config.write()

    def state_changed_callback(self):
        selection = self.treeview.get_selection()
        i = selection.get_selected()[1]
        if i and self.track_changes:
            path = self.model.get_path(i)
            self.model[path][0] = "<i>%s</i>" % cgi.escape(self.model[path][1].name)
