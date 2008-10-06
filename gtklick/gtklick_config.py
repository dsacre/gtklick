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

import ConfigParser
import os.path


def make_property(section, option, type_):
    def getter(self):
        if type_ is int:
            return self.parser.getint(section, option)
        elif type_ is float:
            return self.parser.getfloat(section, option)
        elif type_ is bool:
            return self.parser.getboolean(section, option)
        elif type_ is str:
            return self.parser.get(section, option)

    def setter(self, value):
        self.parser.set(section, option, str(type_(value)))

    return property(getter, setter)


class GTKlickConfig(object):
    def __init__(self):
        self.cfgfile = os.path.expanduser('~/.gtklickrc')

        self.parser = ConfigParser.SafeConfigParser()

        self.parser.add_section('preferences')
        self.parser.add_section('view')
        self.parser.add_section('state')

        # default values, overridden by read()
        self.prefs_sound = 0
        self.prefs_autoconnect = False

        self.view_markings = False
        self.view_meter = True
        self.view_speedtrainer = False
        self.view_pattern = False

        self.state_tempo = 120
        self.state_beats = 4
        self.state_denom = 4
        self.state_volume = 1.0
        self.state_speedtrainer = False
        self.state_pattern = ''

    def read(self):
        self.parser.read(self.cfgfile)

    def write(self):
        self.parser.write(open(self.cfgfile, 'w'))


    prefs_sound         = make_property('preferences', 'sound', int)
    prefs_autoconnect   = make_property('preferences', 'autoconnect', bool)

    view_markings       = make_property('view', 'markings', bool)
    view_meter          = make_property('view', 'meter', bool)
    view_speedtrainer   = make_property('view', 'speedtrainer', bool)
    view_pattern        = make_property('view', 'pattern', bool)

    state_tempo         = make_property('state', 'tempo', int)
    state_beats         = make_property('state', 'beats', int)
    state_denom         = make_property('state', 'denom', int)
    state_volume        = make_property('state', 'volume', float)
    state_speedtrainer  = make_property('state', 'speedtrainer', bool)
    state_pattern       = make_property('state', 'pattern', str)
