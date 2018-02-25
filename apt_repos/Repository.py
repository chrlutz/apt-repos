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


class Repository:
    '''
        TODO
        This class represents a Repository/Suite combination as defined in the current suites-file.
        The most important features of RepoSuites are: They are comparable/__lt__able and respect
        the order defined in the suites-file. They can be updated calling scan(True) against the configured
        apt-repositories/suites and it's possible to query for packages, returning QueryResults       
    
        Note: RepoSuite can be used single threaded only! This is because apt_pkg can only
              be configured to have one root-context at a time. This root-context is set by scan(...)
    '''

    def __init__(self, repoDesc):
        '''
            TODO
            Initializes the suite and creates the caching structure. 
            Note: The apt-cache is not scanned and not updated there! 
                  Always call scan(...) before accessing package metadata!
        '''
        self.desc = repoDesc.get('Repository')
        self.prefix = repoDesc['Prefix']
        self.url = repoDesc['Url']
        self.scan = repoDesc.get('Scan')
        self.suites = repoDesc["Suites"] if repoDesc.get("Suites") else []
        self.architectures = repoDesc.get('Architectures')
        self.trustedGPGFile = repoDesc.get('TrustedGPG')
        self.tags = repoDesc["Tags"] if repoDesc.get("Tags") else []        


    def querySuiteDescs(self, repo, suite):
        res = list()
        prefix = self.prefix if(":" in self.prefix) else "{}:".format(self.prefix)
        (r, s) = prefix.split(":", 1)
        repo = "{}:".format(r) if repo=="" else "{}:".format(repo)
        if not prefix.startswith(repo):
            return res
        selector = repo + suite

        for s in self.suites:
            sid = prefix + s
            if sid == selector or suite=="":
                found = scanRepository(self.url, [sid[len(prefix):]])
                res.extend(self.getSuiteDescs(prefix, found))
        
        if len(self.suites) == 0 and self.scan:
            if len(suite) > 0:
                sid = prefix + suite
                found = scanRepository(self.url, [sid[len(prefix):]])
                res.extend(self.getSuiteDescs(prefix, found))
            else:
                found = scanRepository(self.url)
                res.extend(self.getSuiteDescs(prefix, found))
                
        return res


    def getSuiteDescs(self, prefix, suites):
        res = list()
        for suite in suites:
            archs = list()
            if self.architectures:
                for arch in self.architectures:
                    if arch in suite['architectures']:
                        archs.append(arch)
            res.append({
                "Suite" : prefix + suite['suite'],
                "SourcesList" : "deb {} {} {}".format(self.url, suite['suite'], " ".join(suite['components'])),
                "DebSrc" : suite['hasSources'],
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
           TODO
        ''' 
        return self.desc


    #def getTags(self):
    #    '''
    #        Returns the tags that are assigned to the suite.
    #    '''
    #    return self.tags


    def __str__(self):
        return "Repository('{}', '{}')".format(self.prefix, self.url)
