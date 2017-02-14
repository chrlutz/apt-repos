#!/usr/bin/python3 -Es
# -*- coding: utf-8 -*-
##################################################################################
# Show information about binary and source packages in multiple
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
This python module provides methods and classes to retrieve information
about debian binary- and source-packages from independent apt-repositories
using python apt_pkg module. Analog to well the well known tool apt-cache
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


__baseDir = expanduser('~') + '/.apt-repos'
__cacheDir = __baseDir + '/.apt-repos_cache'
__suiteFiles = [ __baseDir + "/suites", '/etc/apt-repos/suites'  ]


def setAptRepoBaseDir(dir):
    logger = logging.getLogger('getSuites')
    global __baseDir
    global __cacheDir
    global __suiteFiles
    if(os.path.isdir(dir)):
        logger.info("Setting new BaseDir: " + dir)
        __baseDir = os.path.realpath(dir)
        __cacheDir = __baseDir + '/.apt-repos_cache'
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
    '''This class represents a Repository/Suite combination as defined in the current suites-file.
       The most important features of RepoSuites are: They are comparable/__lt__able and respect
       the order defined in the suites-file. They can be updated (updateCache) against the configured
       apt-repositories/suites and it's possible to query for packages, returning QueryResults       
    
       Note: RepoSuite can be used single threaded only! This is because apt_pkg can only
             be configured to have one root-context at a time'''

    def __init__(self, cacheDir, suiteDesc, ordervalue):
        '''initializes the suite and creates the caching structure. The apt-cache is not updated there'''
        logger = logging.getLogger('RepoSuite.__init__')

        self.suite = suiteDesc['Suite']
        self.ordervalue = ordervalue        
        self.rootdir = os.path.realpath(cacheDir + '/' + self.suite.replace("/", "^"))
        self.sourcesListEntry = suiteDesc['SourcesList']
        self.printDebSrc = suiteDesc.get('DebSrc')
        self.architectures = suiteDesc['Architectures'] 

        # create caching structure
        dirs = [ "/etc/apt", "/var/lib/dpkg", "/var/cache/apt/archives/partial", "/var/lib/apt/lists/partial" ]
        for dir in dirs:
            fullDir = self.rootdir + dir
            if not os.path.isdir(fullDir):
                logger.debug("Creating directory " + fullDir)
                os.makedirs(fullDir)

        # create required files
        with open(self.rootdir + "/etc/apt/sources.list", "w") as fh:
            fh.write(self.getSourcesList())
        with open(self.rootdir + "/etc/apt/apt.conf", "w") as fh:
            fh.write(self.getAptConf())
        with open(self.rootdir + "/var/lib/dpkg/status", "w") as fh:
            fh.write("")            

        self.__setRootContext()
        

    def __setRootContext(self):
        '''All methods that work on the objects self.cache or self.records
           should call this method before using these objects'''  
        apt_pkg.read_config_file(apt_pkg.config, self.rootdir + "/etc/apt/apt.conf")                
        apt_pkg.config.set("Dir", self.rootdir)
        apt_pkg.config.set("Dir::State::status", self.rootdir + "/var/lib/dpkg/status")
        apt_pkg.init_system()
        self.cache = apt_pkg.Cache()
        self.records = apt_pkg.PackageRecords(self.cache)

    
    def updateCache(self):
        '''Updates the apt-cache for the suite in the cache directory'''
        __setRootContext()
        # Sadly the underlying apt-lib prints something on stdout we cannot suppress here:
        #    Reading package lists...Done
        #    Building dependency tree...Done
        self.cache.update(Progress(), sources())
        self.cache = apt_pkg.Cache()
        self.records = apt_pkg.PackageRecords(cache)

    
    def getSourcesList(self):
        '''Returns the sourcesList-Entry used for this repo/suite constellation'''
        debSrc = ""
        if self.printDebSrc:
            debSrc = "\n" + re.sub("^deb ", "deb-src ", self.sourcesListEntry)
        return self.sourcesListEntry + debSrc

    
    def getAptConf(self):
        '''Returns the apt.conf used for this repo/suite constellation'''
        return 'APT { Architectures { "' + '"; "'.join(sorted(self.architectures)) + '"; }; };'


    def getSuiteName(self):
        '''Returns the full suite name (consisting of <repository>:<suitename>) of this
           repo/suite constellation as named in the suites file - even if this repo/suite
           was not named in this form in the selector''' 
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


    def queryPackages(self, requestPackages, isRE, requestArgs, requestComponents, requestedFields):
        self.__setRootContext()
        res = list()
        for pkg in self.cache.packages:
            for v in pkg.version_list:
                for req in requestPackages:
                    # Get source name that could be empty in some cases, i.e. if the 
                    # binary package name is equal to the source name. I'm not sure,
                    # if this the only reason for an empty source name, so we check
                    # that before we set source = pkg.name
                    self.records.lookup(v.file_list[0])
                    source = self.records.source_pkg
                    if source == "":
                        # last directory part of the deb-filename is the source name
                        s = os.path.basename(os.path.dirname(records.filename))
                        if pkg.name == s:
                            source = pkg.name
        
                    if isRE:
                        m = re.search(req, pkg.name)
                        if not m:
                            m = re.search(req, "src:" + source)
                            if not m:
                                continue
                    else:
                        if not (pkg.name == req or ("src:" + source) == req):
                            continue
        
                    logger.debug("Found package {}".format(pkg.name))
        
                    if (requestArchs) and (not v.arch in requestArchs):
                        continue
        
                    parts = v.section.split("/")
                    if len(parts) == 1:
                        component, section = "main", parts[0]
                    else:
                        component, section = parts
                    if (requestComponents) and (not component in requestComponents):
                        continue
    
                    res.append(QueryResult(requestedFields, pkg, v, self.records, self))
        return res

        
class PackageField(Enum):
    '''This Enum describes the Fields that can be returned as values in a QueryResult.
       Each PackageField is assigned a unique character that can be used to easily define
       a list of Fields we want to query for in form of a fieldsString.'''
    BINARY_PACKAGE_NAME = 'p'
    VERSION = 'v'
    SUITE = 'S'
    ARCHITECTURE = 'a'
    SECTION = 's'
    SOURCE_PACKAGE_NAME = 'C'
    
    @staticmethod    
    def getByFieldsString(fieldsString):
        res = list()
        for c in fieldsString:
            found = None
            for f in PackageField:
                if str(c) == str(f.value):
                    found = f
            if found:
                res.append(found)
            else:
                raise Exception("Unknown format-character '" + c + "'")
        return res


class QueryResult:
    '''A QueryResult is able carry the requestedFields (and only the requestedFields)
       in the order they were requested. This order is also relevant for sorting.'''
    
    def __init__(self, requestedFields, pkg, version, curRecord, suite):
        self.BINARY_PACKAGE_NAME = None
        self.VERSION = None
        self.ARCHITECTURE = None
        self.SECTION = None
        self.SOURCE_PACKAGE_NAME = None
        self.SUITE = None
        self.fields = requestedFields
        
        for field in self.fields:
            if field == PackageField.BINARY_PACKAGE_NAME:
                self.BINARY_PACKAGE_NAME = pkg.name
            elif field == PackageField.VERSION:
                self.VERSION = version.ver_str
            elif field == PackageField.ARCHITECTURE:
                self.ARCHITECTURE = version.arch
            elif field == PackageField.SECTION:
                self.SECTION = version.section
            elif field == PackageField.SOURCE_PACKAGE_NAME:
                self.SOURCE_PACKAGE_NAME = curRecord.source_pkg
            elif field == PackageField.SUITE:
                self.SUITE = suite


    def __hash__(self):
        return hash((self.BINARY_PACKAGE_NAME,
                     self.VERSION,
                     self.ARCHITECTURE,
                     self.SECTION,
                     self.SOURCE_PACKAGE_NAME,
                     self.SUITE,
                     tuple(self.fields)))


    def __eq__(self, other):
        if other == None:
            return False
        return (self.BINARY_PACKAGE_NAME == other.BINARY_PACKAGE_NAME and
                 self.VERSION == other.VERSION and
                 self.ARCHITECTURE == other.ARCHITECTURE and
                 self.SECTION == other.SECTION and
                 self.SOURCE_PACKAGE_NAME == other.SOURCE_PACKAGE_NAME and
                 self.SUITE == other.SUITE and
                 self.fields == other.fields)


    def __ne__(self, other):
        return not(self == other)


    def __lt__(self, other):
        if self.fields != other.fields:
            raise Exception('We can only compare QueryResults with the same fields-order.')
        for field in self.fields:
            if field == PackageField.BINARY_PACKAGE_NAME and self.BINARY_PACKAGE_NAME != other.BINARY_PACKAGE_NAME:
                return self.BINARY_PACKAGE_NAME < other.BINARY_PACKAGE_NAME
            elif field == PackageField.VERSION and self.VERSION != other.VERSION:
                return True if apt_pkg.version_compare(self.VERSION, other.VERSION) < 0 else False
            elif field == PackageField.ARCHITECTURE and self.ARCHITECTURE != other.ARCHITECTURE:
                return self.ARCHITECTURE < other.ARCHITECTURE
            elif field == PackageField.SECTION and self.SECTION != other.SECTION:
                return self.SECTION < other.SECTION
            elif field == PackageField.SOURCE_PACKAGE_NAME and self.SOURCE_PACKAGE_NAME != other.SOURCE_PACKAGE_NAME:
                return self.SOURCE_PACKAGE_NAME < other.SOURCE_PACKAGE_NAME
            elif field == PackageField.SUITE and self.SUITE != other.SUITE:
                return self.SUITE < other.SUITE
        return False
    
    
    def __str__(self):
        return "QueryResult(" + ", ".join(["{}:'{}'".format(f.name, self.__dict__[f.name]) for f in self.fields]) + ")"
    