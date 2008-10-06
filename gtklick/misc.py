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

import inspect
import weakref, new


# decorator: don't call function while gtk signals are blocked
def gui_callback(f):
    def g(self, *args):
        if not hasattr(self, '__block') or not self.__block:
            return f(self, *args)
    return g

# decorator: enclose the function in threads_enter() / threads_leave() to safely call
# gtk functions, and block gtk signals while the function is running
def osc_callback(f):
    def g(self, *args):
        try:
            gtk.gdk.threads_enter()
            self.__block = True

            #print args[0], args[1]

            # call function with the correct number of arguments, to allow osc callbacks to omit
            # some of pyliblo's callback arguments
            if inspect.getargspec(f)[1] == None:
                n = len(inspect.getargspec(f)[0]) - 1
                r = f(self, *args[0:n])
            else:
                r = f(self, *args)

            self.__block = False
            gtk.gdk.threads_leave()
            return r
        finally:
            gtk.gdk.threads_leave()
    return g


class weakref_method:
    def __init__(self, f):
        self.inst = weakref.ref(f.im_self)
        self.func = f.im_func
    def __call__(self, *args, **kwargs):
        f = new.instancemethod(self.func, self.inst(), self.inst().__class__)
        return f(*args, **kwargs)


class TristateCheckButton(gtk.CheckButton):
    def __init__(self, label):
        gtk.CheckButton.__init__(self, label)
        self.connect('button-release-event', self.on_button_released)
        self.connect('key-press-event', self.on_key_pressed)

    def get_state(self):
        if self.get_inconsistent():
            return 1
        elif self.get_active():
            return 2
        else:
            return 0

    def set_state(self, state):
        toggle = self.get_inconsistent() != (state == 1) and self.get_active() == (state != 0)
        self.set_inconsistent(state == 1)
        self.set_active(state != 0)
        if toggle:
            # emit "toggled" manually if "active" didn't change, but "inconsistent" did
            self.toggled()

    def on_button_released(self, b, ev):
        s = ev.get_state()
        if s & gtk.gdk.CONTROL_MASK:
            if s & gtk.gdk.BUTTON1_MASK:
                self.set_state(2)
            elif s & gtk.gdk.BUTTON2_MASK:
                self.set_state(1)
            elif s & gtk.gdk.BUTTON3_MASK:
                self.set_state(0)
        else:
            if s & gtk.gdk.BUTTON1_MASK:
                self.set_state((self.get_state() - 1) % 3)
            elif s & gtk.gdk.BUTTON2_MASK:
                self.set_state(1 if self.get_state() == 2 else 2)
            elif s & gtk.gdk.BUTTON3_MASK:
                self.set_state(1 if self.get_state() == 0 else 0)
        self.queue_draw()
        return True

    def on_key_pressed(self, b, ev):
        if ev.keyval == gtk.keysyms.space:
            self.set_state((self.get_state() - 1) % 3)
            self.queue_draw()
            return True
        else:
            return False
