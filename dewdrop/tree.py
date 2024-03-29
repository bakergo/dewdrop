#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2011, Greg Baker.

""" Working tree information """

import os

TREE_NAME = '.ddr'
BACKUP_NAME = '.ddr/backup'

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

    def relpath(self, path):
        ''' Return path relative to the current tree '''
        basepath = os.path.commonprefix([os.path.abspath(filename), env.directory])
        if basepath != self.directory:
            raise tree.BadWorkingTree("Filename %s isn't in %s"
                    % (filename, directory))
        return filename[len(env.directory):len(filename)]

def is_tree(directory):
    """ Determine if we're in a working tree. """
    if not os.path.exists(directory):
        return False
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
    directory = os.path.abspath(directory)
    while not os.path.ismount(directory):
        for subdir in os.listdir(directory):
            if TREE_NAME == os.path.basename(subdir):
                return os.path.abspath(os.path.join(directory, subdir))
        directory = os.path.dirname(directory)
    for subdir in os.listdir(directory):
        if TREE_NAME == os.path.basename(subdir):
            return os.path.abspath(os.path.join(directory, subdir))
    raise BadWorkingTree('This directory is not a valid working tree')

def init(directory):
    ''' Create a new working tree '''
    if is_tree(directory):
        raise BadWorkingTree('%s is already a working tree! bailing out.' % 
                directory)
    if not os.path.exists(directory):
        os.makedirs(directory)
    os.mkdir(os.path.join(directory, TREE_NAME))
    os.mkdir(os.path.join(directory, TREE_NAME, 'backup'))
    os.mkdir(os.path.join(directory, TREE_NAME, 'sync'))
    rconf = open(os.path.join(directory, TREE_NAME, 'remotes'), 'w+')
    rconf.close()
    return Environment(directory)

