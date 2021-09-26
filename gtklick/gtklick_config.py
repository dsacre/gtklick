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

import configparser
import os.path
from gi.repository import GObject
import re
import itertools


def make_property(section, option, type_):
    def getter(self):
        if type_ is int:
            try:
                return self.parser.getint(section, option)
            except ValueError:
                # this is only here because i fucked up
                return int(self.parser.getfloat(section, option))
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
    prefs_autoconnect       = make_property('preferences', 'autoconnect', bool)
    prefs_connect_ports     = make_property('preferences', 'connect_ports', str)
    prefs_sound             = make_property('preferences', 'sound', int)
    prefs_sound_accented    = make_property('preferences', 'sound_accented', str)
    prefs_sound_normal      = make_property('preferences', 'sound_normal', str)
    prefs_pitch_accented    = make_property('preferences', 'pitch_accented', float)
    prefs_pitch_normal      = make_property('preferences', 'pitch_normal', float)

    view_markings       = make_property('view', 'markings', bool)
    view_meter          = make_property('view', 'meter', bool)
    view_speedtrainer   = make_property('view', 'speedtrainer', bool)
    view_pattern        = make_property('view', 'pattern', bool)
    view_profiles       = make_property('view', 'profiles', bool)

    tempo               = make_property('state', 'tempo', int)
    speedtrainer        = make_property('state', 'speedtrainer', bool)
    tempo_increment     = make_property('state', 'tempo_increment', float)
    tempo_start         = make_property('state', 'tempo_start', int)
    beats               = make_property('state', 'beats', int)
    denom               = make_property('state', 'denom', int)
    pattern             = make_property('state', 'pattern', str)
    volume              = make_property('state', 'volume', float)


    def __init__(self):
        self.cfgfile = os.path.expanduser('~/.gtklickrc')

        self.parser = configparser.SafeConfigParser()

        self.parser.add_section('preferences')
        self.parser.add_section('view')
        self.parser.add_section('state')

        # default values, overridden by read()
        self.prefs_autoconnect = False
        self.prefs_connect_ports = ''
        self.prefs_sound = 0
        self.prefs_sound_accented = ""
        self.prefs_sound_normal = ""
        self.prefs_pitch_accented = 0.0
        self.prefs_pitch_normal = 0.0

        self.view_markings = False
        self.view_meter = True
        self.view_speedtrainer = False
        self.view_pattern = False
        self.view_profiles = False

        self.tempo = 120
        self.speedtrainer = False
        self.tempo_increment = 0.2
        self.tempo_start = 120
        self.beats = 4
        self.denom = 0
        self.pattern = ''
        self.volume = 1.0

        self.prof_re = re.compile('^profile_[0-9]+$')

    def read(self):
        self.parser.read(self.cfgfile)
        self.convert_older_format('state')

    def write(self):
        self.parser.write(open(self.cfgfile, 'w'))

    def get_profiles(self):
        sections = (x for x in self.parser.sections() if re.match(self.prof_re, x))
        numbers = sorted(int(x.split('_')[1]) for x in sections)

        profiles = []
        for n in numbers:
            try:
                s = 'profile_%d' % n
                self.convert_older_format(s)

                p = Profile(
                    self.parser.get(s, 'name'),
                    self.parser.getint(s, 'tempo'),
                    self.parser.getboolean(s, 'speedtrainer'),
                    self.parser.getfloat(s, 'tempo_increment'),
                    self.parser.getint(s, 'tempo_start'),
                    self.parser.getint(s, 'beats'),
                    self.parser.getint(s, 'denom'),
                    self.parser.get(s, 'pattern')
                )
                profiles.append(p)
            except:
                # silently ignore invalid profiles
                pass

        return profiles

    def set_profiles(self, profiles):
        # store all profiles in config parser
        for n, p in zip(itertools.count(), profiles):
            s = 'profile_%d' % n
            try:
                self.parser.add_section(s)
            except configparser.DuplicateSectionError:
                pass
            self.parser.set(s, 'name', p.name)
            self.parser.set(s, 'tempo', str(p.tempo))
            self.parser.set(s, 'speedtrainer', str(p.speedtrainer))
            self.parser.set(s, 'tempo_increment', str(p.tempo_increment))
            self.parser.set(s, 'tempo_start', str(p.tempo_start))
            self.parser.set(s, 'beats', str(p.beats))
            self.parser.set(s, 'denom', str(p.denom))
            self.parser.set(s, 'pattern', p.pattern)

        # remove unused profile sections
        for s in self.parser.sections():
            if re.match(self.prof_re, s) and int(s.split('_')[1]) >= len(profiles):
                self.parser.remove_section(s)

    def convert_older_format(self, section):
        # convert tempo_limit (pre 0.5) -> tempo_start
        if self.parser.has_option(section, 'tempo_limit'):
            self.parser.set(section, 'tempo_start', str(self.parser.getint(section, 'tempo')))
            if self.parser.getboolean(section, 'speedtrainer'):
                self.parser.set(section, 'tempo', str(self.parser.getint(section, 'tempo_limit')))
            self.parser.remove_option(section, 'tempo_limit')


class Profile(GObject.GObject):
    def __init__(self, name, tempo, speedtrainer, tempo_increment, tempo_start, beats, denom, pattern):
        GObject.GObject.__init__(self)
        self.name = name
        self.tempo = tempo
        self.speedtrainer = speedtrainer
        self.tempo_increment = tempo_increment
        self.tempo_start = tempo_start
        self.beats = beats
        self.denom = denom
        self.pattern = pattern
