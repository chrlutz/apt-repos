#!/usr/bin/python3
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

import sys
import configparser
import urllib3
import io
import codecs
import re
import subprocess
import os
import apt_pkg
import tempfile
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse


def scanRepository(url, suites=None):
    res = list()
    if suites:
        for s in suites:
            try:
                res.append(scanReleaseFile(urljoin(url, os.path.join('dists', s, 'Release'))))
            except Exception as ex:
                '''TODO: add debug message'''
    else:
        res.extend(scanReleases(urljoin(url, "dists/")))
    return res


def scanReleases(url, recursive=True):
    '''
       return suites found at url and all it's relevant subfolders if recursive==True
    '''
    suites = list()
    ignoreFolders = list(['by-hash'])
    index = HtmlIndexParser(url)

    if index.release:
        suite = scanReleaseFile(index.release)
        if suite:
          suites.append(suite)
          ignoreFolders.extend(suite['components'])

    if recursive:
        for subfolder, suburl in sorted(index.getSubfolders().items()):
            if not subfolder in ignoreFolders:
                suites.extend(scanReleases(suburl))

    return suites


def scanReleaseFile(url):
    http = urllib3.PoolManager()
    req = http.request('GET', url)
    if req.status != 200:
        raise Exception("http-request to url {} failed with status code {}".format(url, req.status))

    with tempfile.TemporaryFile() as fp:
        fp.write(req.data)
        fp.seek(0)
        with apt_pkg.TagFile(fp) as tagfile:
            try:
                for section in tagfile:
                    components = section.get('Components').split(" ") if section.get('Components') else list()
                    architectures = section.get('Architectures').split(" ") if section.get('Architectures') else list()
                    md5sum = section.get('MD5Sum').split("\n") if section.get('Md5Sum') else list()
                    files=[re.sub(" +", " ", s.strip()).split(" ")[2] for s in md5sum]
                    hasSources=suiteHasSources(files)

                    suite = section.get('Suite')
                    if suite:
                        return { 
                            'suite':suite,
                            'components':components,
                            'architectures':architectures,
                            'hasSources':hasSources,
                            #'files':files
                        }
            except SystemError as s:
                raise Exception("invalid release file or no suite found at {}".format(url))


def suiteHasSources(files):
    for f in files:
        if ( f.endswith('/source/Sources') or 
             f.endswith('/source/Sources.xz') or
             f.endswith('/source/Sources.gz')):
            return True
    return False


class HtmlIndexParser(HTMLParser):
    def __init__(self, baseurl):
        HTMLParser.__init__(self)
        self.baseurl = urljoin(baseurl, "./")
        self.release = None
        self.inRelease = None
        self.subfolders = dict()
        http = urllib3.PoolManager()
        req = http.request('GET', self.baseurl)
        if req.status != 200:
            raise Exception("http-request to url {} failed with status code {}".format(url, req.status))
        self.feed(req.data.decode('utf8'))
        
    def handle_starttag(self, tag, attrs):
        if tag.upper() == 'A':
            for attr, value in attrs:
                if attr.lower() == 'href':
                    href = urljoin(self.baseurl, value)
                    if href.startswith(self.baseurl):
                        self.handle_suburl(href)

    def handle_suburl(self, url):
        path = os.path.relpath(urlparse(url).path, urlparse(self.baseurl).path)
        if path == 'Release':
            self.release = url
        if path == 'InRelease':
            self.inRelease = url 
        if url.endswith('/'):
            self.subfolders[path] = url

    def getSubfolders(self):
        return self.subfolders


if __name__ == "__main__":
    main()
