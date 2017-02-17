#!/usr/bin/python3 -Es
# -*- coding: utf-8 -*-
##################################################################################
"""Launcher for Test-Methods to test lib_apt_repos"""
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

sys.path.append("../src/")
from lib_apt_repos import getSuites, setAptReposBaseDir, QueryResult, PackageField 


def testPrintHelloWorld():
    print("HelloWorld")


def testSuiteSelectors():
    setAptReposBaseDir(".")
    selectors = [
        None, [":"], ["default:"], ["ubuntu:xenial"], ["xenial"],
        ["ub:trusty"], ["ubuntu:"], ["u:"], ["u:trusty"],
        ["ubuntu:trusty-security", "ubuntu:xenial-security"]
    ]
    for selector in selectors:
        dumpSelectedSuites(getSuites(selector), selector)


def dumpSelectedSuites(suites, selectors):
    print("\nSelected suites for selectors: " + (", ".join(selectors) if selectors else str(selectors)))
    for s in sorted(suites):
        print(s.getSuiteName())


def testGetPackageFields():
    for fieldsStr in [ '', 'pvSasC', 'CsaSvp', 'p', 'v', 'S', 'a', 's', 'C', 'X', 'XYZ' ]:
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

    for fieldsStr in [ 'pv', 'SasC', 'pvSasC', 'CsaSvp', 'p', 'v', 'S', 'a', 's', 'C' ]:
        print()
        print("==========================")
        print("FieldsStr '" + fieldsStr + "'")
        print("==========================")
        fields = PackageField.getByFieldsString(fieldsStr)

        x = QueryResult(fields, a1, a1, a1, "mySuite", "a")
        y = QueryResult(fields, a1, a1, a1, "otherSuite", "a")
        compareAndPrintQueryResults(x, y)

        x = QueryResult(fields, a1, a1, a1, "mySuite", "a")
        y = QueryResult(fields, a2, a2, a2, "mySuite", "a")
        compareAndPrintQueryResults(x, y)

        x = QueryResult(fields, a1, a1, a1, "mySuite", "a")
        y = QueryResult(fields, b1, b1, b1, "mySuite", "b")
        compareAndPrintQueryResults(x, y)

        x = QueryResult(fields, b1, b1, b1, "mySuite", "b")
        y = QueryResult(fields, b2, b2, b2, "mySuite", "b")
        compareAndPrintQueryResults(x, y)

        x = QueryResult(fields, b1, b1, b1, "mySuite", "b")
        y = QueryResult(fields, b3, b3, b3, "mySuite", "b")
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
    setAptReposBaseDir(".")
    fields = PackageField.getByFieldsString('pvSasC')
    repoSuite = list(getSuites(["ubuntu:trusty"]))[0]
    repoSuite.scan(True)
    res = repoSuite.queryPackages(['git'], False, None, None, fields)
    for qr in sorted(res):
        print(qr)


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
