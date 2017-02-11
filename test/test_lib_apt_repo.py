#!/usr/bin/python3 -Es
# -*- coding: utf-8 -*-
##################################################################################
"""Launcher for Test-Methods to test lib_apt_repo"""
#
# Copyright (C) 2017  Christoph Lutz
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
##################################################################################

import os
import sys
import argparse
import logging

sys.path.append("../src/")
from lib_apt_repo import getSuites, setAptRepoBaseDir


def printHelloWorld():
    print("HelloWorld")


def testSuiteSelectors():
    setAptRepoBaseDir(".")
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


def dump(obj):
    for attr in sorted(dir(obj)):
        print("obj.%s = %s" % (attr, getattr(obj, attr)))


def main():
    logging.basicConfig(**{
        'format': '%(levelname)-8s %(message)s',
        'level': logging.DEBUG,
        'stream': sys.stdout
    })
    
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('method', nargs='+', help='Name of a test method to run')
    args = args.parse_args()
    
    for method in args.method:
        globals()[method]()


if __name__ == "__main__":
    main()
