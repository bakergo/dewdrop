#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2011, Greg Baker.

""" No bullshit distributed dropbox clone """

import sys, os
import optparse
import lib.external as external
import lib.remote as remote
import lib.tree as tree

#import datetime
#import re
#import tempfile
#import sqlite3
# TODO Break out each command to a git like command structure
# TODO Handle configuration in ~/.yafs.d/config
# TODO Maintain a global list of yafs dirs in .yafs.d
# TODO Create a yafs-daemon to handle synchronizing each of the dirs.

class InvalidArguments(Exception):
    """ An exception that signifies an error with a command """
    pass

def init(env, opts, args):
    """ Generate a yafs directory """
    tree.init(opts.directory)

def increment(env, opts, args):
    """ Generate a new rdiff-backup incremental backup """
    external.backup(env)

def remote_cmd(env, opts, args):
    """
    Add or remove references to remote servers.
    """
    def usage():
        """ Print how to use this then raise an exception """
        print 'yafs remote add name rsync_path'
        print 'yafs remote remove name'
        print 'yafs remote list'
        raise InvalidArguments('remote')
    if args:
        command = args[0]
    else:
        usage()

    with open(env.remote) as remotefile:
        rconf = remote.RemoteConfig(remotefile)

    if command == 'add':
        if len(args) >= 3:
            rconf.add(remote.Remote(name=args[1], url=args[2]))
            with open(env.remote, 'w+') as remotefile:
                rconf.write(remotefile)
        else:
            usage()
    elif command == 'remove': 
        if len(args) >= 2:
            rconf.remove(args[1])
            with open(env.remote, 'w+') as remotefile:
                rconf.write(remotefile)
        else:
            usage()
    elif command == 'list':
        for entry in rconf.remotes:
            print "%s %s" % (entry.name, entry.url)
    else:
        usage()

def push(env, opts, args):
    """
    Push to each of the remote servers this directory.
    Remote folders are set with the .yafs command
    """
    remotes = remote.get_remotes(env)
    if args:
        filt = lambda rmt: rmt.name in args
    else:
        filt = lambda rmt: True
    for entry in filter(filt, remotes):
        external.rsync(env.directory, entry.url)

def pull(env, opts, args):
    """
    Pull from each of the remote servers of this directory.
    Remote folders are set with the .yafs command
    """
    remotes = remote.get_remotes(env)
    if args:
        filt = lambda rmt: rmt.name in args
    else:
        filt = lambda rmt: True
    for entry in filter(filt, remotes):
        external.rsync(entry.url, env.directory)

def sync(env, opts, args):
    """ 
    Synchronize this folder with each of the others.
    """
    increment(env, opts, args)
    push(env, opts, args)
    pull(env, opts, args)

def clone(env, opts, args):
    """
    Creates a new folder with contents cloned from the given path, referencing
    that path
    """
    pass
# TODO init
# TODO add remote
# TODO pull
# TODO increment

def get_options():
    """ Retrieve and parse command-line options into options and arguments """
    optparser = optparse.OptionParser(
        usage='%prog [Options]',
        version='%prog 0.0')
    optparser.add_option('--yafs-dir', type='string', default=os.getcwd(),
        help='Specify the working directory.')
    (options, args) = optparser.parse_args()
    if (len(args) == 0 or args[0] == 'help'):
        optparser.print_help()
        sys.exit(0)
    command = args[0]
    options.command = command
    return (options, args[1:])

def main():
    """Run through the arguments, then run through user input until we're out"""
    (opts, args) = get_options()
    commands = {
        'init' : init,
        'increment' : increment,
        'push' : push,
        'pull' : pull,
        'remote' : remote_cmd,
        'sync' : sync,
        #'list' : list_incr,
        #'checkout' : checkout,
        #'clone' : clone,
        #'daemon' : daemon,
        #'ping' : ping
    }

    env = None
    if opts.command == 'init':
        if len(args) == 2:
            opts.directory = args[1]
        else:
            opts.directory = os.getcwd()
    else:
        opts.directory = tree.get_root(opts.yafs_dir);
        env = tree.Environment(opts.directory)
    try:
        if opts.command in commands:
            commands[opts.command](env, opts, args)
        else:
            pass
            # Try a subprocess?
    except tree.BadWorkingTree as exc:
        print "bad working tree: ", exc
    except InvalidArguments as exc:
        print "Couldn't recognize your command: ", exc
        
# TODO catch the CalledProcessError from increment
# TODO catch the OSError
# TODO catch ValueError
# TODO catch InvalidArguments
# TODO catch BadWorkingTree

if(__name__ == "__main__"):
    sys.exit(main())

