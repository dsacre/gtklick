# -*- coding: utf-8 -*-

# gtklick
#
# Copyright (C) 2008  Dominic Sacré  <dominic.sacre@gmx.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

import gtk
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
