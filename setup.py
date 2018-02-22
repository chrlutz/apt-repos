import sys

import apt_repos
import re

from distutils.core import setup

from debian.changelog import Changelog

with open('debian/changelog', 'rb') as reader:
    chlog = Changelog(reader, max_blocks = 1)
version = chlog.get_version().full_version

long_description = re.sub(' +', ' ', apt_repos.__doc__.strip())
long_description = re.sub('\n ', '\n', long_description)

description = '''Python3 API to show information about binary and source packages in multiple (system) independent apt-repositories.'''

settings = dict(

    name = 'apt_repos',
    version = version,

    packages = ['apt_repos'],

    author = 'Christoph Lutz',
    author_email = 'christoph.lutz@interface-ag.de',
    description = description,
    long_description = long_description,

    license = 'GPL 2.1',
    url = 'https://github.com/chrlutz/apt-repos'

)

setup(**settings)
