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


def setAptReposBaseDir(dir):
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
                break
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
                selected.add(RepoSuite(__baseDir, __cacheDir, suiteDesc, i))
                
    return selected
    

class RepoSuite:
    '''
        This class represents a Repository/Suite combination as defined in the current suites-file.
        The most important features of RepoSuites are: They are comparable/__lt__able and respect
        the order defined in the suites-file. They can be updated calling scan(True) against the configured
        apt-repositories/suites and it's possible to query for packages, returning QueryResults       
    
        Note: RepoSuite can be used single threaded only! This is because apt_pkg can only
              be configured to have one root-context at a time. This root-context is set by scan(...)
    '''

    def __init__(self, baseDir, cacheDir, suiteDesc, ordervalue):
        '''
            Initializes the suite and creates the caching structure. 
            Note: The apt-cache is not scanned and not updated there! 
                  Always call scan(...) before accessing package metadata!
        '''
        logger = logging.getLogger('RepoSuite.__init__')

        self.suite = suiteDesc['Suite']
        self.ordervalue = ordervalue        
        self.basedir = baseDir
        self.rootdir = os.path.realpath(cacheDir + '/' + self.suite.replace("/", "^"))
        self.sourcesListEntry = suiteDesc['SourcesList']
        self.printDebSrc = suiteDesc.get('DebSrc')
        self.architectures = suiteDesc['Architectures'] 
        self.trustedGPGFile = suiteDesc.get('TrustedGPG') 

        # create caching structure
        dirs = [ "/etc/apt", "/var/lib/dpkg", "/var/cache/apt/archives/partial", "/var/lib/apt/lists/partial" ]
        for dir in dirs:
            fullDir = self.rootdir + dir
            if not os.path.isdir(fullDir):
                logger.debug("Creating directory " + fullDir)
                os.makedirs(fullDir)

        # ensure our config files are properly configured
        self._ensureFileContent(self.rootdir + "/etc/apt/sources.list", self.getSourcesList())
        self._ensureFileContent(self.rootdir + "/etc/apt/apt.conf", self.getAptConf())
        self._ensureFileContent(self.rootdir + "/etc/apt/trusted.gpg", self.getTrustedGPG())
        self._ensureFileContent(self.rootdir + "/var/lib/dpkg/status", "")
        

    def _ensureFileContent(self, file, content):
        logger = logging.getLogger('RepoSuite.ensureFileContent')
        '''
            This method ensures that the file <file> contains <content> but
            modifies the file only if the file not yet exists or it exists
            with a different content. This is to fasten the apt-cache that seems
            to need longer (in method scan(...)) if the modify-timestamp has changed.
            If content == None, we do nothing here.
        '''
        if content == None:
            return
        binaryMode = "b" if isinstance(content, bytes) else ""
        if os.path.exists(file):
            with open(file, "r" + binaryMode) as fh:
                curContent = fh.read()
                if(content == curContent):
                    logger.debug("file {} needs no update".format(file))
                    return
        logger.debug("creating file " + file)
        with open(file, "w" + binaryMode) as fh:
            fh.write(content)
        

    def scan(self, update):
        '''
            This method sets the (global) apt-context to this suite and updates the repository
            metadata in the local cache from the remote apt-repository if update==True.
            Call this method before accessing packages data, e.g. like in queryPackages(...).
            If update==False, the already cached local metadata are used.
        '''  
        logger = logging.getLogger('RepoSuite.__setRootContext')
        logger.debug("scanning repository/suite {} {} update".format(self.suite, 'with' if update else 'without'))
        apt_pkg.read_config_file(apt_pkg.config, self.rootdir + "/etc/apt/apt.conf")                
        apt_pkg.config.set("Dir", self.rootdir)
        apt_pkg.config.set("Dir::State::status", self.rootdir + "/var/lib/dpkg/status")
        apt_pkg.init_system()
        self.cache = apt_pkg.Cache()
        if update:
            self.cache.update(self.__Progress(), self.__sources())
            self.cache = apt_pkg.Cache()
        self.records = apt_pkg.PackageRecords(self.cache)
        logger.debug("finished scan")
        
    
    def getSourcesList(self):
        '''
            Returns the sourcesList-Entry used for this repo/suite constellation
        '''
        logger = logging.getLogger('RepoSuite.getSourcesList')
        logger.debug("got self.sourcesListEntry=" + str(self.sourcesListEntry))
        debSrc = ""
        if self.printDebSrc:
            debSrc = "\n" + re.sub("^deb ", "deb-src ", self.sourcesListEntry)
        return self.sourcesListEntry + debSrc

    
    def getAptConf(self):
        '''
            Returns the apt.conf used for this repo/suite constellation
        '''
        return 'APT { Architectures { "' + '"; "'.join(sorted(self.architectures)) + '"; }; };'


    def getTrustedGPG(self):
        if self.trustedGPGFile:
            with open(self.basedir + "/" + self.trustedGPGFile, "rb") as fh:
                return fh.read()
        return None
        

    def getSuiteName(self):
        '''
            Returns the full suite name (consisting of <repository>:<suitename>) of this
            repo/suite constellation as named in the suites file - even if this repo/suite
            was not named in this form in the selector
        ''' 
        return self.suite

    def __len__(self):
        return len(self.suite)

    def __str__(self):
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


    def queryPackages(self, requestPackages, isRE, requestArchs, requestComponents, requestedFields):
        '''
            This method queries packages in this repository/suite by several criteria and returns a result set
            with elements of type QueryResult:

            requestPackages (list of string; mandatory): is a list of package names.
                            By default a package name is the name of a binary package.
                            Package names may be prefixed with "src:". In this case, a package
                            will match if the source-packages name matches.
           
            isRE (boolean) specifies if package names in requestPackages should be treated
                 as regular expressions. It is possible to search for parts of the package
                 name this way and much more...
                
            requestArch (list of string, optional): is a list of accepted architectures.
                        If requestArch is None, all architectures are accepted.
           
            requestComponent (list of string, optional): is a list of accepted components.
                             If requestComponent is None, all components are accepted.

            requestFields (list of string, mandatory): is a list of fields that should be copied
                          into the query result. QueryResults will automatically order fields in
                          this list order and will accumulate the (hashable) QueryResult-Objects
                          by these fields.
        '''
        logger = logging.getLogger('RepoSuite.queryPackages')
        res = set()
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
                        s = os.path.basename(os.path.dirname(self.records.filename))
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
    
                    res.add(QueryResult(requestedFields, pkg, v, self.records, self, source))
        return res


    class __Progress(apt.progress.base.AcquireProgress):
        '''
            Logging of network activity for RepoSuite.updateCache()
        '''
    
        logger = logging.getLogger('Progress')
    
        def start(self):
            self.logger.debug("[start]")
    
        def stop(self):
            self.logger.debug("[stop]")
    
        def fetch(self, i):
            self.logger.debug("[fetch {}]".format(i.description))
    
        def fail(self, i):
            self.logger.debug("[fail {}]".format(i.description))
    
        def done(self, i):
            self.logger.debug("[done {}]".format(i.description))
    
        def ims_hit(self, i):
            self.logger.debug("[hit {}]".format(i.description))
    
    @staticmethod
    def __sources():
        '''
            Settings to use standard directory layout
        '''
        src = apt_pkg.SourceList()
        src.read_main_list()
        return src

        
class PackageField(Enum):
    '''
        This Enum describes the Fields that can be returned as values in a QueryResult.
        Each PackageField is assigned a unique character that can be used to easily define
        a list of Fields we want to query for in form of a fieldsString.
    '''
    BINARY_PACKAGE_NAME = ('p', 'Package')
    VERSION = ('v', 'Version')
    SUITE = ('S', 'Suite')
    ARCHITECTURE = ('a', 'Arch')
    SECTION = ('s', 'Section')
    SOURCE_PACKAGE_NAME = ('C', 'Source')
    LONG_DESC = ('L', 'Long-Desc')
    RECORD = ('R', 'Full-Record')

    def __str__(self):
        return "<PackageField.{}>".format(self.name)
    
    
    def getHeader(self):
        char, header = self.value
        return header
    
    
    @staticmethod    
    def getByFieldsString(fieldsString):
        res = list()
        for c in fieldsString:
            found = None
            for f in PackageField:
                char, header = f.value
                if str(c) == str(char):
                    found = f
            if found:
                res.append(found)
            else:
                raise Exception("Unknown format-character '" + c + "'")
        return res


class QueryResult:
    '''
        A QueryResult is able to carry the requestedFields (and only the requestedFields)
        in the order they were requested. This order is also relevant for sorting.
        A QueryResult is hashable which makes it possible to accumulate QueryResults by
        the requestedFields.
    '''
    
    def __init__(self, requestedFields, pkg, version, curRecord, suite, source):
        '''
            This constructor creates a QueryResult for the requestedFields. The
            corresponding data are collected from the provided objects:
            
            pkg: Object of type apt_pkg.Package (see apt_pkg docs)
            
            version: Object of type apt_pkg.Version (see apt_pkg docs)
            
            curRecord: Object of type apt_pkg.PackageRecords (see apt_pkg docs)
            
            suite: The RepoSuite object
            
            source: source name (It seems that this information is already provided
                    in curRecord.source_pkg, but this is not quite true. If package
                    name and source name are equal, curRecord.source_pkg will be empty.
                    Since I'am not quite clear, if this is the only reason for
                    curRecord.source_pkg to be empty, we force the caller to provide
                    the exact source name directly).
        '''
        self.fields = requestedFields
        data = list()        
        for field in self.fields:
            if field == PackageField.BINARY_PACKAGE_NAME:
                data.append(pkg.name)
            elif field == PackageField.VERSION:
                data.append(version.ver_str)
            elif field == PackageField.ARCHITECTURE:
                data.append(version.arch)
            elif field == PackageField.SECTION:
                data.append(version.section)
            elif field == PackageField.SOURCE_PACKAGE_NAME:
                data.append(source)
            elif field == PackageField.SUITE:
                data.append(suite)        
            elif field == PackageField.LONG_DESC:
                data.append(curRecord.long_desc)        
            elif field == PackageField.RECORD:
                data.append(curRecord.record)        
        self.data = tuple(data)


    def getData(self):
        '''
            This method returns the field values as a tuple
        '''
        return self.data


    def __iter__(self):
        return iter(self.data)


    def __hash__(self):
        return hash((tuple(self.data), tuple(self.fields)))


    def __eq__(self, other):
        if other == None:
            return False
        return (self.data == other.data and self.fields == other.fields)


    def __ne__(self, other):
        return not(self == other)


    def __lt__(self, other):
        if self.fields != other.fields:
            raise Exception('We can only compare QueryResults with the same fields-order.')
        for field, a, b in zip(self.fields, self.data, other.data):
            if field == PackageField.VERSION and a != b:
                return True if apt_pkg.version_compare(a, b) < 0 else False
            elif a != b:
                return a < b
        return False
    
    
    def __str__(self):
        return "QueryResult(" + ", ".join(["{}:'{}'".format(field.name, data) for field, data in zip(self.fields, self.data)]) + ")"
    