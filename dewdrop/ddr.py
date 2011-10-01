#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2011, Greg Baker.

""" No bullshit distributed dropbox clone """

import sys, os
import shutil
import optparse
import lib.external as external
import lib.remote as remote
import lib.tree as tree
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

def init(env, opts, args):
    """ Generate a ddr directory """
    return tree.init(opts.directory)

def remote_cmd(env, opts, args):
    """
    Add or remove references to remote servers.
    """
    def usage():
        """ Print how to use this then raise an exception """
        print 'usage: ddr remote add <name> <url>'
        print '       ddr remote remove <name> ...'
        print '       ddr remote list <name> ...'
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
    Remote folders are set with the .ddr command
    """
    remotes = remote.get_remotes(env)
    if args:
        filt = lambda rmt: rmt.name in args
    else:
        filt = lambda rmt: True
    for entry in filter(filt, remotes):
        external.rsync(env.directory, entry.url, backup_dir=env.backup)

def pull(env, opts, args):
    """
    Pull from each of the remote servers of this directory.
    Remote folders are set with the .ddr command
    """
    remotes = remote.get_remotes(env)
    if args:
        filt = lambda rmt: rmt.name in args
    else:
        filt = lambda rmt: True
    for entry in filter(filt, remotes):
        external.rsync(entry.url, env.directory, backup_dir=env.backup)

def sync(env, opts, args):
    """ 
    Synchronize this folder with each of the others.
    """
    push(env, opts, args)
    pull(env, opts, args)

def clone(env, opts, args):
    """
    Creates a new folder with contents cloned from the given path, referencing
    that path
    """
    def usage():
        print 'usage: ddr clone <url> ... [dir]'
        print 'Init, add a remote and pull'
        raise  InvalidArguments('clone')
    if len(args) == 1:
        remotes = args[0]
        #opts.directory = opts.ddr_dir
    elif len(args) >1:
        opts.directory = args[-1]
        remotes = args[0:-1]
    else:
        usage()
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

def history(env, opts, args):
    """ Retrieve & list all known versions of a given file """
    def usage():
        ''' Print usage '''
        print 'usage: ddr history <file> ...'
        print 'List all known versions of a given file'
        InvalidArguments('history')

    def showfile(fileid, path, modified):
        ''' Formatter for file '''
        print '{0: <8s} {1:s} {2:s}'.format(str(fileid), modified.ctime(),
                os.path.relpath(path))

    if args:
        for filename in [os.path.abspath(x) for x in args]:
            print 'looking for %s' % filename
            # Find the path relative to directory()
            fileid = 0
            basepath = os.path.commonprefix([os.path.abspath(filename),
                    env.directory])
            relpath = filename[len(env.directory):len(filename)]
            abspath = env.directory + relpath
            basename = os.path.basename(filename)
            histpath = os.path.dirname(env.backup + relpath)
            if basepath != env.directory:
                raise tree.BadWorkingTree("Filename %s isn't in %s"
                        % (filename, directory))
            if os.path.exists(abspath):
                showfile('current', abspath,
                        datetime.datetime.fromtimestamp(
                                os.stat(abspath).st_mtime))
            if os.path.isdir(histpath):
                for (fileid, modified, fname) in listhist(basename, histpath):
                    showfile(fileid, os.path.join(histpath, fname), modified)
    else:
        usage()

def restore(env, opts, args):
    ''' Retrieve a file given by history '''
    def usage():
        ''' Print usage '''
        print 'usage: ddr restore <file> <version num>'
        print 'List all known versions of a given file'
        InvalidArguments('history')
    if len(args) == 2:
        (filename, version) = tuple(args)
        if version == 'current':
            # We're done.
            return
        # Find the path relative to directory()
        abspath = os.path.abspath(filename)
        basepath = os.path.commonprefix([os.path.abspath(filename),
                env.directory])
        relpath = abspath[len(env.directory):len(abspath)]
        basename = os.path.basename(filename)
        histpath = os.path.dirname(env.backup + relpath)

        print 'histpath %s ' % histpath
        if basepath != env.directory:
            #TODO Replace with an OSError
            raise tree.BadWorkingTree("Filename %s isn't in %s"
                    % (filename, env.directory))
        if not os.path.isdir(histpath):
            raise tree.BadWorkingTree("No backups of %s exist" % (filename))
        for (fileid, restmtime, restname) in listhist(basename, histpath):
            if str(fileid) == version:
                bupmtime = datetime.datetime.fromtimestamp(
                        os.stat(abspath).st_mtime)
                bupname = '%s.%s' % (basename,
                                     bupmtime.strftime('%Y%m%d-%H%M%S'))
                buppath  = os.path.join(histpath, bupname)
                restpath = os.path.join(histpath, restname)
                print "Moving newer file %s to %s" % (
                        os.path.relpath(abspath),
                        os.path.relpath(buppath))
                shutil.copy2(abspath, buppath)
                print "Restoring file %s to %s" % (
                        os.path.relpath(restpath),
                        os.path.relpath(abspath))
                shutil.copy2(restpath, abspath)
                return
        raise tree.BadWorkingTree("Filename %s version %s isn't in %s"
            % (filename, version, env.directory))
    else:
        usage()

def get_options():
    """ Retrieve and parse command-line options into options and arguments """
    optparser = optparse.OptionParser(
        usage='%prog [Options]',
        version='%prog 0.0')
    optparser.add_option('--ddr-dir', type='string', default=os.getcwd(),
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
        'push' : push,
        'pull' : pull,
        'remote' : remote_cmd,
        'sync' : sync,
        'clone' : clone,
        'history' : history,
        'restore' : restore,
        #'daemon' : daemon,
        #'ping' : ping
    }

    env = None
    create_commands = set(['init', 'clone'])
    if opts.command in create_commands:
        if len(args) >1:
            opts.directory = args[-1]
        else:
            opts.directory = opts.ddr_dir
    else:
        opts.directory = tree.get_root(opts.ddr_dir)
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

