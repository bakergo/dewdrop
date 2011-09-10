#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2011, Greg Baker.

''' Call external command wrappers '''

import subprocess
import lib.tree as tree
import os


def backup(wtree):
    ''' Generate a new incremental backup using the given working tree '''
    subprocess.check_call(['rdiff-backup',
        '--exclude', wtree.tree,
        wtree.directory,
        wtree.backup])

def rsync(src, dest):
    ''' Call rsync with the default parameters to sync the two folders '''
    subprocess.check_call(['rsync',
        '--delay-updates',
        #'--delete-delay',
        '--partial-dir=%s' % ('.yafsync'),
        '--exclude', tree.TREE_NAME,
        '-slurpt',
        os.path.join(src, ''),
        os.path.join(dest, '')])

