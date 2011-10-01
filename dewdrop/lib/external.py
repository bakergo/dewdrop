#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2011, Greg Baker.

''' Call external command wrappers '''

import subprocess
import datetime
import lib.tree as tree
import os

def rsync(src, dest, backup_dir=None):
    ''' Call rsync with the default parameters to sync the two folders '''
    cmd = ['rsync', '--delay-updates', 
        '--partial-dir=%s' % ('.ddrsync'),
        '--exclude', tree.TREE_NAME,
        '-slurpt']
    if backup_dir:
        suffix = datetime.datetime.now().strftime('.%Y%m%d-%H%M%S')
        cmd.extend(['-b', '--suffix', suffix, '--backup-dir', backup_dir])
    cmd.extend([os.path.join(src, ''), os.path.join(dest, '')])
    subprocess.check_call(cmd)

