# -*- coding: utf-8 -*-

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

    def setter(self, value):
        self.parser.set(section, option, str(type_(value)))

    return property(getter, setter)


class GtklickConfig(object):
    def __init__(self):
        self.cfgfile = os.path.expanduser('~/.gtklickrc')

        self.parser = ConfigParser.SafeConfigParser()

        self.parser.add_section('preferences')
        self.parser.add_section('state')

        # default values, overridden by read()
        self.sound = 0
        self.autoconnect = False

        self.tempo = 120
        self.meter_beats = 4
        self.meter_denom = 4
        self.volume = 1.0

    def read(self):
        self.parser.read(self.cfgfile)

    def write(self):
        self.parser.write(open(self.cfgfile, 'w'))


    sound       = make_property('preferences', 'sound', int)
    autoconnect = make_property('preferences', 'autoconnect', bool)

    tempo       = make_property('state', 'tempo', int)
    meter_beats = make_property('state', 'meter_beats', int)
    meter_denom = make_property('state', 'meter_denom', int)
    volume      = make_property('state', 'volume', float)
