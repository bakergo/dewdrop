#!/usr/bin/python
from distutils.core import setup
import dewdrop

setup(name='dewdrop',
        version='%d.%d.%d' % dewdrop.VERSION,
        description='A completely bullshit distributed dropbox clone',
        author='Greg Baker',
        author_email='bakergo@gmail.com',
        url='https://github.com/bakergo/dewdrop',
        license=open('LICENSE').read(),
        scripts=['bin/ddr'],
        packages=['dewdrop'])

