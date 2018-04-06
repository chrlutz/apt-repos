#!/usr/bin/python3 -Es
# -*- coding: utf-8 -*-
##################################################################################
# Access information about binary and source packages in multiple
# (independent) apt-repositories utilizing libapt / python-apt/
# apt_pkg without the need to change the local system and it's apt-setup.
#
# Copyright (C) 2017  Christoph Lutz
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
##################################################################################
"""
    This python3 module provides an API to retrieve information about debian
    binary- and source-packages from (system) independent apt-repositories
    using python's 'apt_pkg' module. Analog to the well known tool apt-cache
    it downloads Packages files from the inspected repsitories to a local cache
    and reads the information from there. One main advantage of this module
    is, that the local apt-setup (/etc/apt/sources.list, ...) doesn't need to
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
from enum import Enum

from apt_repos.RepoSuite import RepoSuite
from apt_repos.PackageField import PackageField
from apt_repos.QueryResult import QueryResult
from apt_repos.Repository import Repository

logger = logging.getLogger(__name__)

__baseDirs = [ expanduser('~') + '/.config/apt-repos', expanduser('~') + '/.apt-repos', '/etc/apt-repos' ]
__cacheDir = __baseDirs[0] + '/.apt-repos_cache'


def setAptReposBaseDir(dir):
    '''
       Use the specified dir as a sole directory for reading *.suites and *.repos
       files and for the apt-repos cache that will be created in this directory
       named <dir>/.apt-repos_cache.
    '''
    global __baseDirs
    global __cacheDir
    if(os.path.isdir(dir)):
        logger.info("Using basedir '{}'".format(os.path.relpath(dir)))
        __baseDirs = [ os.path.realpath(dir) ]
        __cacheDir = __baseDirs[0] + '/.apt-repos_cache'
    else:
        raise Exception("base-directory doesn't exist: " + dir)


def getSuites(selectors=None):
    '''
       This method returns a set of suites matched by selectors, where
       selectors is an array of selector-Strings.
    '''
    suitesData = dict() # map of filename --> (jsonData, basedir)
    reposData = dict() # map of filename --> (jsonData, basedir)
    configSectionsCount = 0
    for basedir in __baseDirs:
        if not os.path.isdir(basedir):
            if len(suitesData) == 0:
                logger.debug("Skipping BaseDir {} which doesn't exist".format(basedir))
            continue
        for f in sorted(os.listdir(basedir)):
            if f in suitesData:
                continue
            filename = basedir + "/" + f
            if os.path.isfile(filename):
                try:
                    if str(filename).endswith(".suites"):
                        logger.debug("reading suites file " + filename)
                        with open(filename, 'r') as file:
                            jsonData = json.load(file)
                            suitesData[f] = (jsonData, basedir)
                            configSectionsCount += len(jsonData)
                    elif str(filename).endswith(".repos"):
                        with open(filename, 'r') as file:
                            jsonData = json.load(file)
                            reposData[f] = (jsonData, basedir)
                            configSectionsCount += len(jsonData)
                except json.decoder.JSONDecodeError as ex:
                    logger.warning("Skipping unreadable json file {}: {}".format(filename, ex))
                    
    if configSectionsCount == 0:
        logger.warning("No *.suites- or *.repos-files found in the directories '" + "', '".join(__baseDirs) + "'")
        
    if not selectors:
        selectors = ["default:"]
    
    selected = set()
    for selector in selectors:
        
        parts = selector.split(":", 1)
        if len(parts) == 1:
            srepo, ssuiteName = ("", parts[0])
        else:
            srepo, ssuiteName = parts
        
        count = 0
        for unused_key, (suiteDescs, basedir) in suitesData.items():
            for suiteDesc in suiteDescs:
                count+=1
                tags = suiteDesc.get("Tags", [])

                parts = suiteDesc["Suite"].split(":", 1)
                if len(parts) == 1:
                    repo, suiteName = ("", parts[0])
                else:
                    repo, suiteName = parts
                
                if (repo == srepo or srepo == "" or srepo in tags) and \
                   (suiteName == ssuiteName or ssuiteName == ""):
                    selected.add(RepoSuite(basedir, __cacheDir, suiteDesc, count))

        for unused_key, (repoDescs, basedir) in reposData.items():
            for repoDesc in repoDescs:                
                if not type(repoDesc) is dict:
                    continue
                for suiteDesc in Repository(repoDesc).querySuiteDescs(srepo, ssuiteName):
                    count+=1
                    selected.add(RepoSuite(basedir, __cacheDir, suiteDesc, count))
                
    return selected
