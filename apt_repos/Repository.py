#!/usr/bin/python3 -Es
# -*- coding: utf-8 -*-
##################################################################################
# Access information about binary and source packages in multiple
# (independent) apt-repositories utilizing libapt / python-apt/
# apt_pkg without the need to change the local system and it's apt-setup.
#
# Copyright (C) 2018  Christoph Lutz
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
import os
import sys
import logging
import re
import json

import apt_pkg
import apt.progress
import functools

from apt_repos.RepositoryScanner import scanRepository
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class Repository:
    '''
        This class represents a Repository as descibed by an element of a .repos config file.
        A repository is able to scan the apt-repository automatically for it's suites and to
        dynamically create corresponding .suites-configuration for existing suites.
    '''

    def __init__(self, repoDesc):
        '''
            Creates a new Repository Object for the provided Repo Desciption repoDesc
            which is one entry of a .repos file.
        '''
        self.desc = repoDesc.get('Repository')
        self.prefix = repoDesc['Prefix']
        self.prefix = self.prefix + ('' if ':' in self.prefix else ':')
        self.commonTags = repoDesc.get('Tags', list())
        self.url = repoDesc['Url']
        self.scan = repoDesc.get('Scan')
        self.extractSuiteFromReleaseUrl = repoDesc.get('ExtractSuiteFromReleaseUrl')
        self.suites = repoDesc.get("Suites", dict())
        if type(self.suites) == list: # convert to dict
            suites = dict()
            for s in self.suites:
                suites[s] = dict()
            self.suites = suites
        self.architectures = repoDesc.get('Architectures')
        self.trustedGPGFile = repoDesc.get('TrustedGPG')
        self.debSrc = repoDesc.get('DebSrc')
        self.trusted = repoDesc.get('Trusted')


    def querySuiteDescs(self, selRepo, selSuite):
        res = list()
        (ownRepo, ownSuitePrefix) = self.prefix.split(":", 1)
        selRepo = ownRepo if selRepo=='' else selRepo
        selSuite = ownSuitePrefix if selSuite=='' else selSuite
        selector = "{}:{}".format(selRepo, selSuite)
        if not selector.startswith(self.prefix):
            return res
        suite = selector[len(self.prefix):]

        for ownSuite in sorted(self.suites.keys()):
            if suite == ownSuite or suite=='':
                found = scanRepository(self.url, [ownSuite])
                res.extend(self.getSuiteDescs(self.prefix, found))
        
        if self.scan:
            if len(suite) > 0:
                found = scanRepository(self.url, [suite])
                res.extend(self.getSuiteDescs(self.prefix, found))
            else:
                found = scanRepository(self.url)
                res.extend(self.getSuiteDescs(self.prefix, found))
                
        return res


    def getSuiteDescs(self, prefix, suites):
        res = list()
        for suite in suites:
            archs = list()
            if self.architectures:
                for arch in self.architectures:
                    if arch in suite['architectures']:
                        archs.append(arch)
            suitename = suite['suite']
            if self.extractSuiteFromReleaseUrl:
                suitename = re.sub(r".*/dists/", "", os.path.dirname(urlparse(suite['url']).path))
            option = '' if not self.trusted else '[trusted=yes] '
            debSrc = suite['hasSources'] if self.debSrc == None else self.debSrc
            tags = sorted(self.getTags(suitename))
            res.append({
                "Suite" : prefix + suitename,
                "Tags" : tags,
                "SourcesList" : "deb {}{} {} {}".format(option, self.url, suitename, " ".join(suite['components'])),
                "DebSrc" : debSrc,
                "Architectures" : archs if self.architectures else suite['architectures'],
                "TrustedGPG" : self.trustedGPGFile
            })
        return res


    def getArchitectures(self):
        '''
            Returns the architectures, the suite is configured for
        '''
        return self.architectures


    def getDescription(self):
        '''
            Returns the description of the Repository which is the content
            of the "Repository" key in the .repos description.
        ''' 
        return self.desc


    def getTags(self, suite):
        '''
            Returns a set of tags assigned to the suite `suite`.
            This is a union of commonTags (from the "Tags" keyword in
            the repos description) and suite specific Tags (from the
            "Tags" keyword assigned to a single suite).
        '''
        tags = set(self.commonTags)
        suiteAttrib = self.suites.get(suite, dict())
        tags = tags.union(set(suiteAttrib.get('Tags', list())))
        return tags


    def __str__(self):
        return "Repository: {} ({})".format(self.desc, self.url)
