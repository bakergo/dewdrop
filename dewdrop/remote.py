#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2011, Greg Baker.

''' Lib for reading shit from a given tree '''
import ConfigParser
import collections

class Remote(collections.namedtuple('Remote', 'name url')):
    ''' Struct for holding name & url of a remote directory '''
    pass

class RemoteConfig(ConfigParser.RawConfigParser):
    ''' Class representing the file on disk for remotes '''
    def __init__(self, pfile):
        ''' Read Remote entries from the open file pointer given '''
        ConfigParser.RawConfigParser.__init__(self)
        self.readfp(pfile)
        self.remotes = []
        for section in self.sections():
            if self.has_option(section, 'url'):
                name = section
                url = self.get(section, 'url')
                self.remotes.append(Remote(name=name, url=url))

    def add(self, remote):
        ''' Add a new file to this RemoteConfig structure '''
        if not self.has_section(remote.name):
            self.add_section(remote.name)
        self.set(remote.name, 'url', remote.url)

    def remove(self, name):
        ''' Remove all Remote entries by the given name '''
        if self.has_section(name):
            self.remove_section(name)

def get_remotes(tree):
    """
    Retrieve a list of remote servers from internal storage.
    """
    with open(tree.remote) as remotefile:
        return RemoteConfig(remotefile).remotes[:]
