#!/usr/bin/python3 -Es
# -*- coding: utf-8 -*-
"""
   Display information about binary PACKAGE(s) in diverse apt-repositories and suites.
   This tool uses apt-mechanisms to scan for repositories/suites that are registered in
   a suites-file. For each repository/suite combination a local caching folder
   is created in which downloaded Packages files are stored, similar to the cache
   known from apt-cache which lives in /var/lib/apt/lists.
"""

import os
import sys
import argparse
import logging
import re

import apt_pkg
import apt.progress
import functools

# sys.path.append("./tqdm-4.11.2-py2.7.egg")
# from tqdm import tqdm

from lib_apt_repos import getSuites, RepoSuite, PackageField, QueryResult


def main():
    parser = argparse.ArgumentParser(description=__doc__, prog="apt-repos", add_help=False)
    parser.add_argument("-h", "--help", action="store_true", help="""
                        Show a (subcommand specific) help message""")
    subparsers = parser.add_subparsers(dest='func', help='choose one of these subcommands')
    parser.set_defaults(debug=False)
    
    # args for subcommand ls
    parse_ls = subparsers.add_parser('ls', help='search and list binary and source packages', description=ls.__doc__)
    parse_ls.add_argument("-s", "--suite", default='default:', help="""
                          Only show info for these SUITE(s). The list of SUITEs is specified comma-separated.
                          The default value is 'default:'.""")
    parse_ls.add_argument("-d", "--debug", action="store_true", help="""
                          Switch on debugging message printed to stderr.""")
    parse_ls.add_argument("-a", "--architecture", help="""
                          Only show info for ARCH(s). The list of ARCHs is specified comma-separated.""")
    parse_ls.add_argument("-c", "--component", help="""
                          Only show info for COMPONENT(s). The list of COMPONENTs is specified comma-separated.
                          Note: component and section fields are not exactly the same. A component is only the first part
                          of a section (everything before the '/'). There is also a special treatment for sections
                          in the component 'main', in which case 'main/' is typically not named in a section-field.
                          For this switch -c we have to specify 'main' to see packages from the component 'main'.""")
    parse_ls.add_argument("-r", "--regex", action="store_true", help="""
                          Treat PACKAGE as a regex. Searches for binary package-names or
                          binary packages that were built from a source prefixed with 'src:'.
                          Examples:
                          Use regex '.' to show all packages.
                          Use regex '^pkg' to show all packages starting with 'pkg'.
                          Use regex '^src:source' to show packages that were built from a source starting with 'source'.""")
    parse_ls.add_argument("-nu", "--no-update", action="store_true", default=False, help="Skip downloading of packages list.")
    parse_ls.add_argument("-nh", "--no-header", action="store_true", default=False, help="Don't print the column header.")
    parse_ls.add_argument("-col", "--columns", type=str, required=False, default='pvSasC', help="""
                          Specify the columns that should be printed. Default is 'pvSasC'. Possible characters are:
                          (p)=Package, (v)=Version, (S)=Suite, (a)=Architecture, (s)=Section, (C)=SourCe.""")
    parse_ls.add_argument("-f", "--format", type=str, choices=['table', 'list'], required=False, default='table', help="""
                          Specifies the output-format of the package list. Default is 'table'.
                          Possible values: 'table' to pretty print a nice table; 'list' to print a
                          space separated list of columns that can easily be processed with bash tools.""")
    parse_ls.add_argument('package', nargs='+', help='Name of a binary PACKAGE or source-package name prefixed as src:SOURCENAME')
    parse_ls.set_defaults(func=ls, sub_parser=parse_ls)

    # args for subcommand suites
    parse_suites = subparsers.add_parser('suites', help='list configured suites', description=suites.__doc__)
    parse_suites.add_argument("-d", "--debug", action="store_true", help="""
                              Switch on debugging message printed to stderr.""")
    parse_suites.add_argument("-s", "--suite", default=':', help="""
                              Only show info for these SUITE(s). The list of SUITEs is specified comma-separated.
                              The default value is ':' (all suites).""")
    parse_suites.set_defaults(func=suites, sub_parser=parse_suites)

    args = parser.parse_args()

    setupLogging(logging.DEBUG if args.debug else logging.WARN)
    logger = logging.getLogger('main')
    
    if args.func:
        if args.help:
            args.sub_parser.print_help()
            sys.exit(0)
        else:
            args.func(args)
    else:
        if args.help:
            parser.print_help()
            sys.exit(0)
        else:
            parser.print_usage()
            sys.exit(1)


def setupLogging(loglevel):
    '''Initializing logging and set log-level'''
    kwargs = {
        'format': '%(asctime)s %(levelname)-8s %(message)s',
        'datefmt':'%Y-%m-%d,%H:%M:%S',
        'level': loglevel,
        'stream': sys.stderr
    }
    logging.basicConfig(**kwargs)


def suites(args):
    '''subcommand suites: print a list of registered suites'''
    logger = logging.getLogger('suites')
    suites = getSuites(args.suite.split(','))
    for s in sorted(suites):
        print(s.getSuiteName())


def ls(args):
    '''subcommand ls: search and print a list of packages'''
    logger = logging.getLogger('ls')

    suites = getSuites(args.suite.split(','))
    requestPackages = { p for p in args.package }
    requestArchs = { a for a in args.architecture.split(',') } if args.architecture else {}
    requestComponents = { c for c in args.component.split(',') } if args.component else {}
    requestFields = PackageField.getByFieldsString(args.col)

    result = set()
    for suite in suites:
        if not args.no_update: 
            suite.updateCache()
        result.extend(suite.queryPackages(self, requestPackages, args.regex, requestArchs, requestComponents, requestFields))

    # calculate max col_widths
    col_width = [max(len(x) for x in col) for col in zip(*result)]

    if args.format == 'table':
        if not args.no_header:
            col_width = [max(len(h), col_width[i]) for i, h in enumerate(header)]
            result = (header, ["="*w for w in col_width], result)
        for r in result:
            print (" | ".join("{:{}}".format(x, col_width[i]) for i, x in enumerate(r)))

    elif args.format == 'list':
        if not args.no_header:
            result = (header, result)
        for r in result:
            print (" ".join(r))


if __name__ == "__main__":
    main()
