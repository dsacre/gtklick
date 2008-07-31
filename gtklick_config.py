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


class GtklickConfig:
    def __init__(self):
        self.cfgfile = os.path.expanduser('~/.gtklickrc')

        self.parser = ConfigParser.SafeConfigParser()

        # default values, overridden by read()
        self.parser.add_section('preferences')
        self.set_sound(0)
        self.set_autoconnect(False)

    def read(self):
        self.parser.read(self.cfgfile)

    def write(self):
        self.parser.write(open(self.cfgfile, 'w'))

    def set_sound(self, sound):
        self.parser.set('preferences', 'sound', str(sound))

    def get_sound(self):
        return self.parser.getint('preferences', 'sound')

    def set_autoconnect(self, autoconnect):
        self.parser.set('preferences', 'autoconnect', str(autoconnect))

    def get_autoconnect(self):
        return self.parser.getboolean('preferences', 'autoconnect')
