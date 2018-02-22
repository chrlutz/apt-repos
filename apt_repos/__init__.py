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


__baseDirs = [ expanduser('~') + '/.config/apt-repos', expanduser('~') + '/.apt-repos', '/etc/apt-repos' ]
__cacheDir = __baseDirs[0] + '/.apt-repos_cache'


def setAptReposBaseDir(dir):
    logger = logging.getLogger('getSuites')
    global __baseDirs
    global __cacheDir
    if(os.path.isdir(dir)):
        logger.info("Setting new BaseDir: " + dir)
        __baseDirs = [ os.path.realpath(dir) ]
        __cacheDir = __baseDirs[0] + '/.apt-repos_cache'
    else:
        raise Exception("base-directory doesn't exist: " + dir)


def getSuites(selectors=None):
    logger = logging.getLogger('getSuites')
    
    suitesData = dict() # map of filename --> (jsonData, basedir)
    suitesCount = 0
    for basedir in __baseDirs:
        if not os.path.isdir(basedir):
            if len(suitesData) == 0:
                logger.debug("Skipping BaseDir {} which doesn't exist".format(basedir))
            continue
        for f in sorted(os.listdir(basedir)):
            if f in suitesData:
                continue
            filename = basedir + "/" + f
            if os.path.isfile(filename) and str(filename).endswith(".suites"):
                logger.debug("reading suites file " + filename)
                with open(filename, 'r') as file:
                    jsonData = json.load(file)
                    suitesData[f] = (jsonData, basedir)
                    suitesCount += len(jsonData)
                    
    if suitesCount == 0:
        logger.warning("No *.suites-files or no suites-data found in the directories '" + "', '".join(__baseDirs) + "'")
        
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
        for key, (suiteDescs, basedir) in suitesData.items():
            for suiteDesc in suiteDescs:
                count+=1
                tags = suiteDesc.get("Tags") if suiteDesc.get("Tags") else []

                parts = suiteDesc["Suite"].split(":", 1)
                if len(parts) == 1:
                    repo, suiteName = ("", parts[0])
                else:
                    repo, suiteName = parts
                
                if (repo.startswith(srepo) or srepo in tags) and \
                   (suiteName == ssuiteName or ssuiteName == ""):
                    selected.add(RepoSuite(basedir, __cacheDir, suiteDesc, count))
                
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
        self.hasDebSrc = suiteDesc.get('DebSrc')
        self.architectures = suiteDesc['Architectures'] 
        self.trustedGPGFile = suiteDesc.get('TrustedGPG')
        self.tags = suiteDesc["Tags"] if suiteDesc.get("Tags") else []


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
        if self.hasDebSrc:
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
        

    def hasSources(self):
        '''
            Returns if this suite is configured to contain sources
        '''
        return self.hasDebSrc


    def getRepoUrl(self):
        '''
            Returns the Repository-Url
        '''
        (mod, url, suite, components) = self._parsedSourceListEntry()
        return url


    def getDistsUrl(self):
        '''
            Returns an Url to the dists-folder for the suite in the form <REPO_URL>/dists/<SUITENAME>
        '''
        (mod, url, suite, components) = self._parsedSourceListEntry()
        return "{}/dists/{}".format(url.rstrip('/'), suite)


    def getAptSuite(self):
        '''
            Returns the suite set in the apt.conf line
        '''
        (mod, url, suite, components) = self._parsedSourceListEntry()
        return suite


    def getComponents(self):
        '''
            Returns the suite set in the apt.conf line
        '''
        (mod, url, suite, components) = self._parsedSourceListEntry()
        return components


    def _parsedSourceListEntry(self):
        '''
           Returns (modifier, url, suite, components)
           from the sourcesListEntry
        '''
        parts = str(self.sourcesListEntry).split(" ")
        if "[" in parts[1] and "]" in parts[1]:
            mod = parts[1]
            parts = parts[2:]
        else:
            mod = None
            parts = parts[1:]
        return (mod, parts[0], parts[1], parts[2:])


    def getArchitectures(self):
        '''
            Returns the architectures, the suite is configured for
        '''
        return self.architectures


    def getSuiteName(self):
        '''
            Returns the full suite name (consisting of <repository>:<suitename>) of this
            repo/suite constellation as named in the suites file - even if this repo/suite
            was not named in this form in the selector
        ''' 
        return self.suite


    def getTags(self):
        '''
            Returns the tags that are assigned to the suite.
        '''
        return self.tags


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
        
                    parts = v.section.split("/", 1)
                    if len(parts) == 1:
                        component, section = "main", parts[0]
                    else:
                        component, section = parts
                    if (requestComponents) and (not component in requestComponents):
                        continue
    
                    res.add(QueryResult.createByAptPkgStructures(requestedFields, pkg, v, self.records, self, source))
        return res


    def querySources(self, requestPackages, isRE, requestArchs, requestComponents, requestedFields):
        '''
            This method queries source packages in this repository/suite by several criteria and returns a
            result set with elements of type QueryResult:

            requestPackages (list of string; mandatory): is a list of package names.
                            A package name is the name of a source package.

            isRE (boolean) specifies if package names in requestPackages should be treated
                 as regular expressions. It is possible to search for parts of the package
                 name this way and much more...

            #TODO:clarify what to do with arch
            #requestArch (list of string, optional): is a list of accepted architectures.
            #            If requestArch is None, all architectures are accepted.

            requestComponent (list of string, optional): is a list of accepted components.
                             If requestComponent is None, all components are accepted.

            requestFields (list of string, mandatory): is a list of fields that should be copied
                          into the query result. QueryResults will automatically order fields in
                          this list order and will accumulate the (hashable) QueryResult-Objects
                          by these fields.
        '''
        logger = logging.getLogger('RepoSuite.queryPackages')
        res = set()

        sourcesFiles = self.getSourcesFiles()
        if not sourcesFiles:
            logger.debug("no sources files for suite {}".format(suite.getSuiteName()))
            return

        for sourcesFile in sourcesFiles: # there's one sourcesFile per component
            # skip unrequested components:
            # TODO: this is too much implementation specific to the apt_pkg lib... improve if possible
            m = re.search("^.*_([^_]+)_source_Sources$", sourcesFile)
            if not m:
                raise AnError("Sorry, I can't extract a component name from the sources file name {}".format(sourcesFile))
            component = m.group(1)
            if requestComponents and len(requestComponents) > 0 and not component in requestComponents:
                logger.debug("skipping component {} as not requested in --component".format(component))
                continue

            logger.debug("parsing sources file {}".format(sourcesFile))
            with open(sourcesFile, 'r') as f:
                tagfile = apt_pkg.TagFile(f)
                for source in tagfile:
                    name = source['Package']

                    for req in requestPackages:
                        if isRE:
                            m = re.search(req, name)
                            if not m:
                                continue
                        else:
                            if not (name == req):
                                continue

                        logger.debug("Found package {}".format(name))

                        #if (requestArchs) and (not v.arch in requestArchs):
                        #    continue

                        parts = source['Section'].split("/", 1)
                        if len(parts) == 1:
                            component, section = "main", parts[0]
                        else:
                            component, section = parts
                        if (requestComponents) and (not component in requestComponents):
                            continue

                        res.add(QueryResult.createBySourcesTagFileSection(requestedFields, source, self))
        return res


    def getSourcesFiles(self):
        '''
            If this RepoSuite is configured to support Sources (Key "DebSrc" in suites-file is True)
            this method will return a list of all *_Sources-Files that have been downloaded by apt.
            We can use these Sources-Files to manually parse them (e.g. using apt_pkg.tagFile).
            Unfortunately apt_pkg seems to provide no other way to iterate through the list of all
            source packages in this suite. If this RepoSuite has no sources, this method returns None.
        '''
        if not self.hasDebSrc:
            return None
        res = list()
        for sourcesFile in sorted(os.listdir(self.rootdir + "/var/lib/apt/lists/")):
            if not sourcesFile.endswith("_Sources"):
                continue
            res.append(self.rootdir + "/var/lib/apt/lists/" + sourcesFile)
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
    SUITE = ('s', 'Suite')
    ARCHITECTURE = ('a', 'Arch')
    SECTION = ('S', 'Section')
    PRIORITY = ('P', 'Priority')
    SOURCE_PACKAGE_NAME = ('C', 'Source')
    LONG_DESC = ('L', 'Long-Desc')
    RECORD = ('R', 'Full-Record')
    BASE_URL = ('B', 'Base-Url')
    FILENAME = ('F', 'File-Url')

    def __str__(self):
        return "<PackageField.{}>".format(self.name)
    
    
    def getHeader(self):
        char, header = self.value
        return header
    
    
    def getChar(self):
        char, header = self.value
        return char
    
    
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


class Priority(Enum):
    '''
        This Enum describes the values defined for Priority-Fields.
    '''
    REQUIRED = apt_pkg.PRI_REQUIRED
    IMPORTANT = apt_pkg.PRI_IMPORTANT
    STANDARD = apt_pkg.PRI_STANDARD
    OPTIONAL = apt_pkg.PRI_OPTIONAL
    EXTRA = apt_pkg.PRI_EXTRA

    def __str__(self):
        return self.name.lower()

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return self.value == other.value

    def __ne__(self, other):
        return not(self == other)

    def __lt__(self, other):
        return self.value < other.value
    
    @staticmethod    
    def getByInt(intVal):
        for p in Priority:
            if intVal == p.value:
                return p
        return Priority.EXTRA

    @staticmethod
    def getByName(name):
        for p in Priority:
            if name.upper() == p.name:
                return p
        return Priority.EXTRA


class QueryResult:
    '''
        A QueryResult is able to carry the requestedFields (and only the requestedFields)
        in the order they were requested. This order is also relevant for sorting.
        A QueryResult is hashable which makes it possible to accumulate QueryResults by
        the requestedFields.
    '''
    
    def __init__(self, fields, data):
        '''
            This constructor creates a QueryResult for the list of PackageField fields
            and their corresponding field-data (as a tuple)
            
            fields: List of type PackageField that describes which fields
                             this QueryResult should carry.
                             
            data: tuple of values for each of the fields
        '''
        self.fields = fields
        self.data = data
        
        
    @staticmethod
    def createByAptPkgStructures(requestedFields, pkg, version, curRecord, suite, source):
        '''
            This factory-method creates a QueryResult for the requestedFields. The
            corresponding data are collected from the provided apt_pkg objects:
            
            requestedFields: List of type PackageField that describes which fields
                             this QueryResult should carry.
            
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
        data = list()        
        for field in requestedFields:
            if field == PackageField.BINARY_PACKAGE_NAME:
                data.append(pkg.name)
            elif field == PackageField.VERSION:
                data.append(version.ver_str)
            elif field == PackageField.ARCHITECTURE:
                data.append(version.arch)
            elif field == PackageField.SECTION:
                data.append(version.section)
            elif field == PackageField.PRIORITY:
                data.append(Priority.getByInt(version.priority))
            elif field == PackageField.SOURCE_PACKAGE_NAME:
                data.append(source)
            elif field == PackageField.SUITE:
                data.append(suite)        
            elif field == PackageField.LONG_DESC:
                data.append(curRecord.long_desc)        
            elif field == PackageField.RECORD:
                data.append(curRecord.record)        
            elif field == PackageField.BASE_URL:
                data.append(os.path.join(suite.getRepoUrl(), ""))
            elif field == PackageField.FILENAME:
                data.append(os.path.join(suite.getRepoUrl(), curRecord.filename))
        data = tuple(data)
        return QueryResult(requestedFields, data)


    @staticmethod
    def createBySourcesTagFileSection(requestedFields, source, suite):
        '''
            This factory-method creates a QueryResult for the requestedFields. The
            corresponding data are collected from the provided section of an
            apt_pkg.TagFile:

            requestedFields: List of type PackageField that describes which fields
                             this QueryResult should carry.

            source: Object of type apt_pkg.TagSection that can be retrieved e.g. by
                    apt_pkg.TagFile(<sourceFile>) for a particular sources control
                    file <sourceFile> (see apt_pkg docs).

            suite: The RepoSuite object
        '''
        data = list()
        for field in requestedFields:
            if field == PackageField.SOURCE_PACKAGE_NAME:
                data.append(source['Package'])
            elif field == PackageField.VERSION:
                data.append(source['Version'])
            elif field == PackageField.SECTION:
                data.append(source['Section'])
            elif field == PackageField.PRIORITY:
                data.append(Priority.getByName(source['Priority']))
            elif field == PackageField.ARCHITECTURE: # not a final solution!
                data.append(source['Architecture'])
            elif field == PackageField.SUITE:
                data.append(suite)
            elif field == PackageField.RECORD:
                data.append(source)
            elif field == PackageField.BASE_URL:
                data.append(os.path.join(suite.getRepoUrl(), ""))
            elif field == PackageField.FILENAME:
                dscFile = None
                for f in source['Files'].split("\n"):
                    (md5, size, fname) = f.strip().split(" ")
                    if fname.endswith(".dsc"):
                        dscFile = fname
                        break
                if dscFile:
                    data.append(os.path.join(suite.getRepoUrl(), source['Directory'], dscFile))
                else:
                    data.append(None)
            else:
                raise Exception('Package Field \'{}\' (or column character \'{}\') is not supported for source packages'.format(field.name, field.getChar()))
        data = tuple(data)
        return QueryResult(requestedFields, data)


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
    
