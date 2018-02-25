#!/usr/bin/python3
# -*- coding: utf-8 -*-
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
            res.append(scanReleaseFile(urljoin(url, os.path.join('dists', s, 'Release'))))
    else:
        res.extend(scanReleases(urljoin(url, "dists/")))
    return res


def scanReleases(url, recursive=True):
    '''
       return suites found at url and all it's relevant subfolders if recursive==True
    '''
    print("retrieving suites at url {}".format(url))
    suites = list()
    ignoreFolders = list(['by-hash'])
    index = HtmlIndexParser(url)

    if index.release or index.inRelease:
        releaseFileUrl = index.inRelease if index.inRelease else index.release
        suite = scanReleaseFile(releaseFileUrl)
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
    with tempfile.TemporaryFile() as fp:
        fp.write(req.data)
        fp.seek(0)
        with apt_pkg.TagFile(fp) as tagfile:
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
