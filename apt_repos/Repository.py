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
from urllib.parse import urlparse, urljoin

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
        if isinstance(self.url, str):
            self.url = [ self.url ]
        self.scan = repoDesc.get('Scan')
        self.extractSuiteFromReleaseUrl = repoDesc.get('ExtractSuiteFromReleaseUrl')
        self.suites = repoDesc.get("Suites", list())
        # convert self.suite string entries into dicts
        for x in range(len(self.suites)):
            s = self.suites[x]
            if isinstance(s, str):
                d = dict()
                d["Suite"] = s
                self.suites[x] = d
        self.architectures = repoDesc.get('Architectures')
        self.trustedGPGFile = repoDesc.get('TrustedGPG')
        self.debSrc = repoDesc.get('DebSrc')
        self.trusted = repoDesc.get('Trusted')


    def querySuiteDescs(self, selRepo, selSuite):
        res = list()
        (unused_ownRepo, ownSuitePrefix) = self.prefix.split(":", 1)

        selSuite = ownSuitePrefix if selSuite=='' else selSuite
        if not selSuite.startswith(ownSuitePrefix):
            return res
        suite = selSuite[len(ownSuitePrefix):]

        first = True
        for suiteDict in self.suites:
            ownSuite = suiteDict["Suite"]
            for commonUrl in self.url:
                url = urljoin(commonUrl, suiteDict.get("Url", ''))
                if not self._isRepositorySelected(selRepo, suiteDict):
                    continue
                if suite == ownSuite or suite=='':
                    if first:
                        logger.info("Scanning {}".format(self))
                        first = False
                    found = scanRepository(url, [ownSuite])
                    res.extend(self.getSuiteDescs(self.prefix, found, suiteDict))
        
        if self.scan and self._isRepositorySelected(selRepo):
            for commonUrl in self.url:
                logger.info("Scanning {}".format(self))
                if len(suite) > 0:
                    found = scanRepository(commonUrl, [suite])
                    res.extend(self.getSuiteDescs(self.prefix, found))
                else:
                    found = scanRepository(commonUrl)
                    res.extend(self.getSuiteDescs(self.prefix, found))
                
        return res


    def _isRepositorySelected(self, selRepo, suiteDict=dict()):
        '''
            Returns true if the repository is selected by the repository selector
            selRepo (which ist the part of the selector before ":", without ":").
            This method also respects Tags defined in the two levels "repository-
            common tags" and "suite specific tags" (see self.getTags(suite)).
        '''
        (ownRepo, _) = self.prefix.split(":", 1)
        validRepos = ['', ownRepo]
        validRepos.extend(sorted(self.__getTags(suiteDict)))
        return selRepo in validRepos


    def getSuiteDescs(self, prefix, suites, suiteDict=dict()):
        res = list()
        for suite in suites:
            archs = list()
            if self.architectures:
                for arch in self.architectures:
                    if arch in suite['architectures']:
                        archs.append(arch)
            suitename = suite['suite']
            suitenameFromReleaseUrl = re.sub(r".*/dists/", "", os.path.dirname(urlparse(suite['releaseUrl']).path))
            if self.extractSuiteFromReleaseUrl:
                suitename = suitenameFromReleaseUrl
            option = '' if not self.trusted else '[trusted=yes] '
            debSrc = suite['hasSources'] if self.debSrc == None else self.debSrc
            tags = sorted(self.__getTags(suiteDict))
            res.append({
                "Suite" : prefix + suitename,
                "Tags" : tags,
                "SourcesList" : "deb {}{} {} {}".format(option, suite['repoUrl'], suitenameFromReleaseUrl, " ".join(suite['components'])),
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


    def __getTags(self, suiteDict=dict()):
        '''
            Returns a set of tags assigned to the suite described by 
            `suiteDict`. This is a union of commonTags (from the "Tags"
            keyword in the repos description) and suite specific Tags
            (from the "Tags" keyword in suiteDict). If suiteDict is not
            given this method just returns the commonTags.
        '''
        tags = set(self.commonTags)
        tags = tags.union(set(suiteDict.get('Tags', list())))
        return tags


    def __str__(self):
        if self.desc:
            return "Repository '{}' ({})".format(self.desc, self.url)
        else:
            return "Repository {}".format(self.url)
