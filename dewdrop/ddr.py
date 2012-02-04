#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2011, Greg Baker.

""" No bullshit distributed dropbox clone """

import sys
import os
import shutil
import optparse
import external
import remote
import tree
import datetime
import re

#import tempfile
#import sqlite3
# TODO Break out each command to a git like command structure
# TODO Handle configuration in ~/.ddr.d/config
# TODO Maintain a global list of ddr dirs in .ddr.d
# TODO Create a ddr-daemon to handle synchronizing each of the dirs.

class InvalidArguments(Exception):
    """ An exception that signifies an error with a command """
    pass

COMMANDS = {}
def subcommand(cmd):
    def wrapper(func):
        COMMANDS[cmd] = func
        docs = func.__doc__.split('\n')
        func.help = docs[1].strip()
        func.cmd = cmd
        func.usage = [line.strip() for line in docs[2:-1]]
        return func;
    return wrapper

def usage(func):
    prefix = 'usage:'
    for line in func.usage:
        print '%s %s' % (prefix, line)
        prefix = '      '
    raise InvalidArguments(func.cmd)

@subcommand('init')
def init(env, opts, args):
    """ 
    Generate a new ddr directory
    init
    """
    return tree.init(opts.directory)

@subcommand('remote')
def remote_cmd(env, opts, args):
    """
    Add or remove references to remote servers.
    remote add <name> <url>
    remote remove <name> ...
    remote list [<name> ...]
    """
    if args:
        command = args[0]
    else:
        usage(remote_cmd)

    with open(env.remote) as remotefile:
        rconf = remote.RemoteConfig(remotefile)

    if command == 'add':
        if len(args) >= 3:
            rconf.add(remote.Remote(name=args[1], url=args[2]))
            with open(env.remote, 'w+') as remotefile:
                rconf.write(remotefile)
        else:
            usage(remote_cmd)
    elif command == 'remove': 
        if len(args) >= 2:
            rconf.remove(args[1])
            with open(env.remote, 'w+') as remotefile:
                rconf.write(remotefile)
        else:
            usage(remote_cmd)
    elif command == 'list':
        for entry in rconf.remotes:
            print "%s %s" % (entry.name, entry.url)
    else:
        usage(remote_cmd)

@subcommand('push')
def push(env, opts, args):
    """
    Push to each of the remote servers this directory.
    push [<name> ...]
    """
    remotes = remote.get_remotes(env)
    if args:
        filt = lambda rmt: rmt.name in args
    else:
        filt = lambda rmt: True
    for entry in filter(filt, remotes):
        external.rsync(env.directory, entry.url, backup_dir=env.backup)

@subcommand('pull')
def pull(env, opts, args):
    """
    Pull from each of the remote servers of this directory.
    pull [<name> ...]
    """
    remotes = remote.get_remotes(env)
    if args:
        filt = lambda rmt: rmt.name in args
    else:
        filt = lambda rmt: True
    for entry in filter(filt, remotes):
        external.rsync(entry.url, env.directory, backup_dir=env.backup)

@subcommand('sync')
def sync(env, opts, args):
    """ 
    Synchronize this folder with each of the others. Alias for push & pull
    sync
    """
    push(env, opts, args)
    pull(env, opts, args)

@subcommand('clone')
def clone(env, opts, args):
    """
    Creates a new folder with contents cloned from the given path
    clone <url> ... [<dir>]
    """
    if len(args) == 1:
        remotes = args[0]
        #opts.directory = opts.ddr_dir
    elif len(args) >1:
        opts.directory = args[-1]
        remotes = args[0:-1]
    else:
        usage(clone)
    env = init(env, opts, args)
    with open(env.remote) as remotefile:
        rconf = remote.RemoteConfig(remotefile)
    for entry in remotes:
        rconf.add(remote.Remote(name=entry, url=entry))
    with open(env.remote, 'w+') as remotefile:
        rconf.write(remotefile)
    pull(env, opts, remotes)

def listhist(basename, dirpath):
    ''' List files in the histtree '''
    #suffix = datetime.datetime.now().strftime('.%Y%m%d-%H%M%S')
    fpat = re.compile('^%s.%s%s-%s$' %(basename, '(\d{4})', '(\d{2})'*2,
        '(\d{2})'*3))
    fileid = 0
    for histfile in os.listdir(dirpath):
        fmatch = fpat.match(os.path.basename(histfile))
        if fmatch and os.path.isfile(os.path.join(dirpath, histfile)):
            fileid += 1
            (year, month, day, hour, minute, second) = map(int, fmatch.groups())
            modified = datetime.datetime(year, month, day, hour, minute,
                    second)
            yield (fileid, modified, histfile)

@subcommand('history')
def history(env, opts, args):
    """
    Retrieve & list all known versions of a given file
    history <file> ...
    """
    def showfile(fileid, path, modified):
        ''' Formatter for file '''
        print '{0: <8s} {1:s} {2:s}'.format(str(fileid), modified.ctime(),
                os.path.relpath(path))

    if args:
        for filename in [os.path.abspath(x) for x in args]:
            print 'looking for %s' % filename
            # Find the path relative to directory()
            fileid = 0
            relpath = env.relpath(filename)
            basename = os.path.basename(filename)
            histpath = os.path.dirname(env.backup + relpath)
            if os.path.exists(filename):
                showfile('current', filename,
                        datetime.datetime.fromtimestamp(
                                os.stat(filename).st_mtime))
            if os.path.isdir(histpath):
                for (fileid, modified, fname) in listhist(basename, histpath):
                    showfile(fileid, os.path.join(histpath, fname), modified)
    else:
        usage(history)

@subcommand('restore')
def restore(env, opts, args):
    '''
    Retrieve a file given by history
    restore <file> <version num>
    '''
    def copy(source, dest):
        ''' Copy a source file to the destination no matter what. '''
        if os.path.isfile(source):
            print "Moving file from %s to %s" % (
                    os.path.relpath(source),
                    os.path.relpath(dest))
            if not os.path.isdir(os.path.dirname(dest)):
                os.makedirs(os.path.dirname(dest))
            shutil.copy2(source, dest)

    if len(args) == 2:
        (filename, version) = tuple(args)
        if version == 'current':
            # We're done.
            return
        # Find the path relative to directory()
        abspath = os.path.abspath(filename)
        basename = os.path.basename(filename)
        relpath = env.relpath(abspath)
        histpath = os.path.dirname(env.backup + relpath)

        if not os.path.isdir(histpath):
            raise tree.BadWorkingTree("No backups of %s exist" % (filename))
        for (fileid, restmtime, restname) in listhist(basename, histpath):
            if str(fileid) == version:
                # File.txt.20110102-133026
                bupname = '%s.%s' % (basename,
                        datetime.datetime.fromtimestamp(
                            os.stat(abspath).st_mtime
                            .strftime('%Y%m%d-%H%M%S')))
                buppath  = os.path.join(histpath, bupname)
                restpath = os.path.join(histpath, restname)
                copy(abspath, buppath)
                copy(restpath, abspath)
                return
        raise tree.BadWorkingTree("Filename %s version %s isn't in %s"
            % (filename, version, env.directory))
    else:
        usage(restore)

def get_options():
    """ 
    Retrieve and parse command-line options into options and arguments 
    """
    optparser = optparse.OptionParser(
        usage='%prog [Options]',
        version='%prog 0.0')
    optparser.add_option('--ddr-dir', type='string', default=os.getcwd(),
        help='Specify the working directory.')
    subcommands = optparse.OptionGroup(optparser, "Subcommands",
            "These arguments dictate the possible different actions that "
            "you can perform when using dewdrop")
    optparser.add_option_group(subcommands)

    (options, args) = optparser.parse_args()
    if (len(args) == 0 or args[0] == 'help'):
        optparser.print_help()
        print
        for command in COMMANDS:
                print "  %-10s %s" % (COMMANDS[command].cmd, 
                        COMMANDS[command].help)
        sys.exit(0)
    command = args[0]
    options.command = command
    return (options, args[1:])

def main():
    """
    Run through the arguments, then run through user input until we're out
    """
    (opts, args) = get_options()
    env = None
    create_commands = set(('init', 'clone'))
    if opts.command in create_commands:
        if len(args) >1:
            opts.directory = args[-1]
        else:
            opts.directory = opts.ddr_dir
    else:
        opts.directory = tree.get_root(opts.ddr_dir)
        env = tree.Environment(opts.directory)
    try:
        if opts.command in COMMANDS:
            COMMANDS[opts.command](env, opts, args)
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

