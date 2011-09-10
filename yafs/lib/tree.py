#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2011, Greg Baker.

""" Working tree information """

import os

TREE_NAME = '.yafs'

class BadWorkingTree(Exception):
    """ An exception that involves a working tree somehow. """
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value
    def __str__(self):
        return repr(self.value)

class Environment:
    ''' Contains various locations within the current directory structure. '''
    def __init__(self, directory):
        self.tree = get_root(directory)
        self.directory = os.path.dirname(self.tree)
        self.backup = os.path.join(self.tree, 'backup')
        self.remote = os.path.join(self.tree, 'remotes')

def is_tree(directory):
    """ Determine if we're in a working tree. """
    while not os.path.ismount(directory):
        for subdir in os.listdir(directory):
            if TREE_NAME == os.path.basename(subdir):
                return True
        directory = os.path.dirname(directory)
    for subdir in os.listdir(directory):
        if TREE_NAME == os.path.basename(subdir):
            return True
    return False

def get_root(directory):
    """ return the root directory (our working tree) """
    while not os.path.ismount(directory):
        for subdir in os.listdir(directory):
            if TREE_NAME == os.path.basename(subdir):
                return os.path.abspath(subdir)
        directory = os.path.dirname(directory)
    for subdir in os.listdir(directory):
        if TREE_NAME == os.path.basename(subdir):
            return os.path.abspath(subdir)
    raise BadWorkingTree('This directory is not a valid working tree')

def init(directory):
    ''' Create a new working tree '''
    if is_tree(directory):
        raise BadWorkingTree('%s is already a working tree! bailing out.' % 
                directory)
    os.mkdir(os.path.join(directory, TREE_NAME))
    os.mkdir(os.path.join(directory, TREE_NAME, 'backup'))
    os.mkdir(os.path.join(directory, TREE_NAME, 'sync'))
    rconf = open(os.path.join(directory, TREE_NAME, 'remotes'), 'w+')
    rconf.close()
    return Environment(directory)

