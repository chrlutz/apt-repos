#!/usr/bin/python3 -Es
# -*- coding: utf-8 -*-
##################################################################################
"""Launcher for Test-Methods to test the python3-apt-repos library"""
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

import os
import sys
import argparse
import logging

sys.path.insert(0, "../")
import apt_repos
from apt_repos import PackageField, QueryResult
from apt_repos.Repository import Repository


def testPrintHelloWorld():
    print("HelloWorld")


def testSuiteSelectors():
    apt_repos.setAptReposBaseDir(".")
    selectors = [
        None, [":"], ["default:"], ["ubuntu:xenial"], ["xenial"],
        ["ub:trusty"], ["ubuntu:"], ["u:"], ["u:trusty"],
        ["ubuntu:trusty-security", "ubuntu:xenial-security"]
    ]
    for selector in selectors:
        dumpSelectedSuites(apt_repos.getSuites(selector), selector)


def testSuiteProperties():
    apt_repos.setAptReposBaseDir(".")
    for s in sorted(apt_repos.getSuites([":"])):
        print(s.getSuiteName())
        print(s.getAptSuite())
        print(s.getRepoUrl())
        print(s.getDistsUrl())
        print(s.getComponents())
        print(s.hasSources())
        print(s.getArchitectures())
        print(s.getSourcesList())
        print()


def dumpSelectedSuites(suites, selectors):
    print("\nSelected suites for selectors: " + (", ".join(selectors) if selectors else str(selectors)))
    for s in sorted(suites):
        print(s.getSuiteName())


def testGetPackageFields():
    for fieldsStr in [ '', 'pvsaSC', 'CSasvp', 'p', 'v', 's', 'a', 'S', 'C', 'X', 'XYZ' ]:
        print("FieldsStr '" + fieldsStr + "'")
        try:
            print("[" + (", ".join([str(f) for f in PackageField.getByFieldsString(fieldsStr)])) + "]")
        except Exception as x:
            print(x)


class PVRMock:
    def __init__(self, args):
        for k in args:
            self.__dict__[k] = args[k]


def testQueryResult():
    a1 = PVRMock({ "name" : "a-pkg", "ver_str" : "1.2~6deb2", "arch" : "i386", "section" : "main", "source_pkg" : "a" })
    a2 = PVRMock({ "name" : "a-pkg", "ver_str" : "1.2~55deb2", "arch" : "i386", "section" : "main", "source_pkg" : "a" })
    b1 = PVRMock({ "name" : "b-pkg", "ver_str" : "1.2~55deb2", "arch" : "i386", "section" : "main", "source_pkg" : "b" })
    b2 = PVRMock({ "name" : "b-pkg", "ver_str" : "1.2~55deb2", "arch" : "amd64", "section" : "main", "source_pkg" : "b" })
    b3 = PVRMock({ "name" : "b-pkg", "ver_str" : "1.2~55deb2", "arch" : "amd64", "section" : "universe", "source_pkg" : "b" })

    for fieldsStr in [ 'pv', 'saSC', 'pvsaSC', 'CSasvp', 'p', 'v', 's', 'a', 'S', 'C' ]:
        print()
        print("==========================")
        print("FieldsStr '" + fieldsStr + "'")
        print("==========================")
        fields = PackageField.getByFieldsString(fieldsStr)

        x = QueryResult.createByAptPkgStructures(fields, a1, a1, a1, "mySuite", "a")
        y = QueryResult.createByAptPkgStructures(fields, a1, a1, a1, "otherSuite", "a")
        compareAndPrintQueryResults(x, y)

        x = QueryResult.createByAptPkgStructures(fields, a1, a1, a1, "mySuite", "a")
        y = QueryResult.createByAptPkgStructures(fields, a2, a2, a2, "mySuite", "a")
        compareAndPrintQueryResults(x, y)

        x = QueryResult.createByAptPkgStructures(fields, a1, a1, a1, "mySuite", "a")
        y = QueryResult.createByAptPkgStructures(fields, b1, b1, b1, "mySuite", "b")
        compareAndPrintQueryResults(x, y)

        x = QueryResult.createByAptPkgStructures(fields, b1, b1, b1, "mySuite", "b")
        y = QueryResult.createByAptPkgStructures(fields, b2, b2, b2, "mySuite", "b")
        compareAndPrintQueryResults(x, y)

        x = QueryResult.createByAptPkgStructures(fields, b1, b1, b1, "mySuite", "b")
        y = QueryResult.createByAptPkgStructures(fields, b3, b3, b3, "mySuite", "b")
        compareAndPrintQueryResults(x, y)


def compareAndPrintQueryResults(x, y):
    print()
    print("x = " + str(x))
    print("y = " + str(y))
    print("x<y = " + str(x < y))
    print("y<x = " + str(y < x))
    print("x==y = " + str(x == y))
    print("sameHash = " + str(x.__hash__() == y.__hash__()))


def testQueryPackages():
    apt_repos.setAptReposBaseDir(".")
    fields = PackageField.getByFieldsString('pvsaSCFB')
    repoSuite = list(apt_repos.getSuites(["ubuntu:trusty"]))[0]
    repoSuite.scan(True)
    res = repoSuite.queryPackages(['git'], False, None, None, fields)
    for qr in sorted(res):
        print(qr)


def testQuerySources():
    apt_repos.setAptReposBaseDir(".")
    fields = PackageField.getByFieldsString('CvsaSFB')
    repoSuite = list(apt_repos.getSuites(["ubuntu:trusty"]))[0]
    repoSuite.scan(True)
    res = repoSuite.querySources(['git'], False, None, None, fields)
    for qr in sorted(res):
        print(qr)


def testGetSourcesFiles():
    apt_repos.setAptReposBaseDir(".")
    repoSuite = list(apt_repos.getSuites(["ubuntu:trusty"]))[0]
    repoSuite.scan(True)
    for file in repoSuite.getSourcesFiles():
        # we can't just print the absolute filename which is not diffable, so
        # we print the trailing 4 parts of the path.
        keep = ""
        for i in range(0, 7):
            keep = os.path.basename(file) + ("/" if len(keep) > 0 else "") + keep
            file = os.path.dirname(file)    
        print(("<testfolder>/" if len(file) > 0 else "") + keep)


def testRepository():
    basisRepoDesc = {
      "Repository" : "Main Ubuntu Repository",
      "Prefix" : "ubuntu",
      "Url" : "http://archive.ubuntu.com/ubuntu/",
      "Architectures" : [ "i386", "amd64" ],
      "TrustedGPG" : "./gpg/ubuntu.gpg"
    }

    repo = Repository(mergedict(basisRepoDesc, {
      "Repository" : "Testing Basics",
      "Suites" : [ "xenial", "bionic" ]
    }))
    print("\n" + str(repo))
    dumpQuerySuiteDescsResult(repo, "ubuntu", "bionic")
    dumpQuerySuiteDescsResult(repo, "u", "bionic")
    dumpQuerySuiteDescsResult(repo, "ubuntu", "noexist")
    dumpQuerySuiteDescsResult(repo, "", "noexist")
    dumpQuerySuiteDescsResult(repo, "", "bionic")
    dumpQuerySuiteDescsResult(repo, "ubuntu", "")
    dumpQuerySuiteDescsResult(repo, "ubuntu:test-", "bionic")
    dumpQuerySuiteDescsResult(repo, "another", "bionic")

    repo = Repository(mergedict(basisRepoDesc,{
      "Repository" : "Testing different Prefix",
      "Prefix" : "ubuntu:de-",
      "Url" : "http://de.archive.ubuntu.com/ubuntu/",
      "Suites" : [ "xenial", "bionic" ]
    }))
    print("\n" + str(repo))
    dumpQuerySuiteDescsResult(repo, "ubuntu", "de-bionic")
    dumpQuerySuiteDescsResult(repo, "u", "de-bionic")
    dumpQuerySuiteDescsResult(repo, "", "de-noexist")
    dumpQuerySuiteDescsResult(repo, "", "de-bionic")
    dumpQuerySuiteDescsResult(repo, "ubuntu", "")
    dumpQuerySuiteDescsResult(repo, "ubuntu:de-", "bionic")
    dumpQuerySuiteDescsResult(repo, "ubuntu:", "bionic")

    repo = Repository(mergedict(basisRepoDesc, {
      "Repository" : "Testing Option Scan==True",
      "Scan" : True
    }))
    print("\n" + str(repo))
    dumpQuerySuiteDescsResult(repo, "ubuntu", "bionic")
    dumpQuerySuiteDescsResult(repo, "", "bionic")
    dumpQuerySuiteDescsResult(repo, "", "noexist")
    dumpQuerySuiteDescsResult(repo, "ubuntu", "")
    dumpQuerySuiteDescsResult(repo, "ubuntu:de-", "bionic")
    dumpQuerySuiteDescsResult(repo, "ubuntu:", "bionic")

    # Better would be to test a repo whose Release-File states a different
    # suitename than it's .../dists/<dist>-path. ExtractSuiteFromReleaseUrl
    # should give precidence to <dist> in this case.
    repo = Repository(mergedict(basisRepoDesc, {
      "Repository" : "Testing Option ExtractSuiteFromReleaseUrl==True",
      "Suites" : [ "bionic" ],
      "ExtractSuiteFromReleaseUrl": True,
    }))
    print("\n" + str(repo))
    dumpQuerySuiteDescsResult(repo, "ubuntu", "bionic")

    repo = Repository(mergedict(basisRepoDesc, {
      "Repository" : "Testing Option Trusted==True",
      "Suites" : [ "bionic" ],
      "Trusted": True
    }))
    print("\n" + str(repo))
    dumpQuerySuiteDescsResult(repo, "ubuntu", "bionic")

    repo = Repository(mergedict(basisRepoDesc, {
      "Repository" : "Testing Option DebSrc==True",
      "Suites" : [ "bionic" ],
      "DebSrc" : False,
    }))
    print("\n" + str(repo))
    dumpQuerySuiteDescsResult(repo, "ubuntu", "bionic")


def mergedict(a, b):
    res = dict(a)
    for key, value in b.items():
        res[key] = value
    return res


def dumpQuerySuiteDescsResult(repo, prefix, suite):
    print("  Results for '{}', '{}':".format(prefix, suite))
    for suiteDesc in repo.querySuiteDescs(prefix, suite):
        for key, value in sorted(suiteDesc.items()):
            print("    {}: {}".format(key, value))


def dump(obj):
    for attr in sorted(dir(obj)):
        print("obj.%s = %s" % (attr, getattr(obj, attr)))


def main():
    logging.basicConfig(**{
        'format': '%(levelname)-8s %(message)s',
        'level': logging.INFO,
        'stream': sys.stdout
    })
    
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('method', nargs='+', help='Name of a test method to run')
    args = args.parse_args()
    
    for method in args.method:
        if str(method).startswith('test'):
            globals()[method]()
        else:
            print("Not a test method: " + test)


if __name__ == "__main__":
    main()
