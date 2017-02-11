#!/usr/bin/python3
# -*- coding: utf-8 -*-
##################################################################################
# Show information about binary and source packages in multiple
# (independent) apt-repositories utilizing libapt / python-apt/
# apt_pkg without the need to change the local system and it's apt-setup.
#
# Copyright (C) 2017  Christoph Lutz
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
##################################################################################

"""
This python module provides methods and classes to retrieve information
about debian binary- and source-packages from independent apt-repositories
using python apt_pkg module. Analog to well the well known tool apt-cache
it downloads Packages files from the inspected repsitories to a local cache
and reads the information from there. One main advantage of this module
is, that the local apt-setup (/etc/apt/sources.list, ...) don't need to
be modified in order to retrieve package information via apt.
"""

import os
import sys
import argparse
import logging
import re
import json

import apt_pkg
import apt.progress
import functools

from os.path import expanduser


__baseDir = expanduser('~') + '/.apt-repo'
__cacheDir = __baseDir + '/.apt-repo_cache'
__suiteFiles = [ __baseDir + "/suites", '/etc/apt-repo/suites'  ]


def setAptRepoBaseDir(dir):
    logger = logging.getLogger('getSuites')
    global __baseDir
    global __cacheDir
    global __suiteFiles
    if(os.path.isdir(dir)):
        logger.info("Setting new BaseDir: " + dir)
        __baseDir = os.path.realpath(dir)
        __cacheDir = __baseDir + '/.apt-repo_cache'
        __suiteFiles = [ __baseDir + "/suites" ]
    else:
        raise Exception("base-directory doesn't exist: " + dir)


def getSuites(selectors=None):
    logger = logging.getLogger('getSuites')
    
    suitesData = []
    for suitesFile in __suiteFiles:
        if os.path.isfile(suitesFile):
            with open(suitesFile, 'r') as f:
                suitesData = json.load(f)
        else:
            logger.warning("No suites-file found at " + suitesFile)
        
    if not selectors:
        selectors = ["default:"]
    
    selected = set()
    for selector in selectors:
        
        parts = selector.split(":", 1)
        if len(parts) == 1:
            srepo, ssuiteName = ("", parts[0])
        else:
            srepo, ssuiteName = parts
        
        for i, suiteDesc in enumerate(suitesData):
            tags = suiteDesc.get("Tags") if suiteDesc.get("Tags") else []

            parts = suiteDesc["Suite"].split(":", 1)
            if len(parts) == 1:
                repo, suiteName = ("", parts[0])
            else:
                repo, suiteName = parts
                
            if (repo.startswith(srepo) or srepo in tags) and \
               (suiteName == ssuiteName or ssuiteName == ""):
                selected.add(RepoSuite(__cacheDir, suiteDesc, i))
                
    return selected
    

class RepoSuite:

    def __init__(self, cacheDir, suiteDesc, ordervalue):
        logger = logging.getLogger('RepoSuite.__init__')
        self.suite = suiteDesc['Suite']
        self.rootdir = os.path.realpath(cacheDir + '/' + self.suite.replace("/", "^"))
        if not os.path.isdir(self.rootdir):
            logger.info("Creating suite cache directory " + self.rootdir)
            os.makedirs(self.rootdir)
        self.ordervalue = ordervalue

    def getSuiteName(self):
        return self.suite

    def __hash__(self):
        return hash((self.suite))

    def __eq__(self, other):
        if other == None:
            return False
        return self.suite == other.suite

    def __ne__(self, other):
        return not(self == other)

    def __lt__(self, other):
        if self.ordervalue != other.ordervalue:
            return self.ordervalue < other.ordervalue
        return self.suite < other.suite

