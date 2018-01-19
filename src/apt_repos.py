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
import tempfile
import subprocess
import functools

from lib_apt_repos import setAptReposBaseDir, getSuites, RepoSuite, PackageField, QueryResult


def main():
    
    # fixup to get help-messages for subcommands that require positional argmuments
    # so that "apt-repos -h <subcommand>" prints a help-message and not an error
    if ("-h" in sys.argv or "--help" in sys.argv) and \
       ("ls" in sys.argv or "show" in sys.argv):
        sys.argv.append(".")
    
    parser = createArgparsers()[0]
    args = parser.parse_args()

    setupLogging(logging.DEBUG if args.debug else logging.WARN)
    logger = logging.getLogger('main')
    
    if "diff" in args.__dict__ and args.diff:
        diffField = args.diff.split("^")[0]
        if len(diffField) != 1:
            raise AnError("-di needs exactly one diffField character as argument. provided is: '{}'".format(diffField))
        elif not diffField in args.columns:
            raise AnError("The character -di needs to be also in -col. provided is: -col '{}' and -di '{}'".format(args.columns, diffField))

    if args.basedir:
        setAptReposBaseDir(args.basedir)
    
    if "sub_function" in args.__dict__:
        if args.help:
            args.sub_parser.print_help()
            sys.exit(0)
        else:
            args.sub_function(args)
            sys.exit(0)
    else:
        if args.help:
            parser.print_help()
            sys.exit(0)
        else:
            parser.print_usage()
            sys.exit(1)


def createArgparsers():
    fieldChars = ", ".join(["({})={}".format(f.getChar(), f.getHeader()) for f in PackageField])
    if sys.stdout.isatty():
        ttyWidth = os.popen('stty size', 'r').read().split()[1]
    else:
        ttyWidth = 80
    diffToolDefault = "diff,--side-by-side,--suppress-common-lines,--width={}"

    parser = argparse.ArgumentParser(description=__doc__, prog="apt-repos", add_help=False)
    parser.add_argument("-h", "--help", action="store_true", help="""
                        Show a (subcommand specific) help message""")
    parser.add_argument("-b", "--basedir", help="""Set a new/custom basedir for config-data and caching.
                        Please provide the basedir as an absolute path.
                        The default is $HOME/.apt-repos. 
                        The basedir must at least contain a file named 'suites'.
                        The cache will be created into a subfolder called '<basedir>/.apt-repos_cache'.""")
    subparsers = parser.add_subparsers(help='choose one of these subcommands')
    parser.set_defaults(debug=False)
    
    # args for subcommand list
    parse_ls = subparsers.add_parser('list', aliases=['ls'], help='search and list binary and source packages', description=ls.__doc__)
    parse_ls.add_argument("-d", "--debug", action="store_true", help="""
                          Switch on debugging message printed to stderr.""")
    parse_ls.add_argument("-s", "--suite", default='default:', help="""
                          Only show info for these SUITE(s). The list of SUITEs is specified comma-separated.
                          The default value is 'default:'.""")
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
    parse_ls.add_argument("-col", "--columns", type=str, required=False, default='pvsaSC', help="""
                          Specify the columns that should be printed. Default is 'pvsaSC'.
                          Possible characters are: """ + fieldChars)
    parse_ls.add_argument("-f", "--format", type=str, choices=['table', 'list'], required=False, default='table', help="""
                          Specifies the output-format of the package list. Default is 'table'.
                          Possible values: 'table' to pretty print a nice table; 'list' to print a
                          space separated list of columns that can easily be processed with bash tools.""")
    parse_ls.add_argument("-di", "--diff", type=str, required=False, help="""
                          Similar to -s switch, but expects in DIFF exactly two comma separated parts
                          ("suiteA,suiteB"), calculates the output for suiteA and suiteB separately 
                          and diff's this output with the diff tool specified in --diff-tool.""")
    parse_ls.add_argument("-dt", "--diff-tool", type=str, default=diffToolDefault.format(ttyWidth), required=False, help="""
                          Diff-Tool used to compare the separated results from --diff.
                          Default is '{}'.
                          Use , (instead of spaces) to provide arguments for the difftool.""".format(diffToolDefault.format("<ttyWidth>")))
    parse_ls.add_argument('package', nargs='+', help='Name of a binary PACKAGE or source-package name prefixed as src:SOURCENAME')
    parse_ls.set_defaults(sub_function=ls, sub_parser=parse_ls)

    # args for subcommand suites
    parse_suites = subparsers.add_parser('suites', help='list configured suites', description=suites.__doc__)
    parse_suites.add_argument("-d", "--debug", action="store_true", help="""
                              Switch on debugging message printed to stderr.""")
    parse_suites.add_argument("-s", "--suite", default=':', help="""
                              Only show info for these SUITE(s). The list of SUITEs is specified comma-separated.
                              The default value is ':' (all suites).""")
    parse_suites.add_argument("-v", "--verbose", action="store_true", help="""
                              also print corresponding sources.list-entries for each suite""")
    parse_suites.set_defaults(sub_function=suites, sub_parser=parse_suites)

    # args for subcommand show
    parse_show = subparsers.add_parser('show', help='show details about packages similar to apt-cache show', description=show.__doc__)
    parse_show.add_argument("-d", "--debug", action="store_true", help="""
                              Switch on debugging message printed to stderr.""")
    parse_show.add_argument("-s", "--suite", default='default:', help="""
                              Only show info for these SUITE(s). The list of SUITEs is specified comma-separated.
                              The default value is 'default:'.""")
    parse_show.add_argument("-a", "--architecture", help="""
                              Only show info for ARCH(s). The list of ARCHs is specified comma-separated.""")
    parse_show.add_argument("-c", "--component", help="""
                              Only show info for COMPONENT(s). The list of COMPONENTs is specified comma-separated.
                              Note: component and section fields are not exactly the same. A component is only the first part
                              of a section (everything before the '/'). There is also a special treatment for sections
                              in the component 'main', in which case 'main/' is typically not named in a section-field.
                              For this switch -c we have to specify 'main' to see packages from the component 'main'.""")
    parse_show.add_argument("-r", "--regex", action="store_true", help="""
                              Treat PACKAGE as a regex. Searches for binary package-names or
                              binary packages that were built from a source prefixed with 'src:'.
                              Examples:
                              Use regex '.' to show all packages.
                              Use regex '^pkg' to show all packages starting with 'pkg'.
                              Use regex '^src:source' to show packages that were built from a source starting with 'source'.""")
    parse_show.add_argument("-col", "--columns", type=str, required=False, default='sR', help="""
                              Specify the columns that should be printed. Default is 'sR'.
                              Possible characters are: """ + fieldChars)
    parse_show.add_argument("-di", "--diff", type=str, required=False, help="""
                              Similar to -s switch, but expects in DIFF exactly two comma separated parts
                              ("suiteA,suiteB"), calculates the output for suiteA and suiteB separately 
                              and diff's this output with the diff tool specified in --diff-tool.""")
    parse_show.add_argument("-dt", "--diff-tool", type=str, default=diffToolDefault.format(ttyWidth), required=False, help="""
                              Diff-Tool used to compare the separated results from --diff.
                              Default is '{}'.
                              Use _ instead of spaces if this command has arguments.""".format(diffToolDefault.format("<ttyWidth>")))
    parse_show.add_argument("-nu", "--no-update", action="store_true", default=False, help="Skip downloading of packages list.")
    parse_show.add_argument('package', nargs='+', help='Name of a binary PACKAGE or source-package name prefixed as src:SOURCENAME')
    parse_show.set_defaults(sub_function=show, sub_parser=parse_show)

    # args for subcommand dsc
    parse_dsc = subparsers.add_parser('dsc', help='list urls of dsc-files for particular source-packages.', description=dsc.__doc__)
    parse_dsc.add_argument("-d", "--debug", action="store_true", help="""
                              Switch on debugging message printed to stderr.""")
    parse_dsc.add_argument("-s", "--suite", default='default:', help="""
                              Only show info for these SUITE(s). The list of SUITEs is specified comma-separated.
                              The list of suites is read in the specified order (this is interesting together with --first).
                              The default value is 'default:'.""")
    parse_dsc.add_argument("-c", "--component", help="""
                              Only show info for COMPONENT(s). The list of COMPONENTs is specified comma-separated.
                              Note: component and section fields are not exactly the same. A component is only the first part
                              of a section (everything before the '/'). There is also a special treatment for sections
                              in the component 'main', in which case 'main/' is typically not named in a section-field.
                              For this switch -c we have to specify 'main' to see packages from the component 'main'.""")
    parse_dsc.add_argument("-1", "--first", action="store_true", default=False, help="Query only for the first matching dsc file, then skip the others.")
    parse_dsc.add_argument("-nu", "--no-update", action="store_true", default=False, help="Skip downloading of packages list.")
    parse_dsc.add_argument('package', nargs='+', help='Name of a source PACKAGE')
    parse_dsc.set_defaults(sub_function=dsc, sub_parser=parse_dsc)

    return (parser, parse_ls, parse_show, parse_suites, parse_dsc)


def setupLogging(loglevel):
    '''
       Initializing logging and set log-level
    '''
    kwargs = {
        'format': '%(asctime)s %(levelname)-8s %(message)s',
        'datefmt':'%Y-%m-%d,%H:%M:%S',
        'level': loglevel,
        'stream': sys.stderr
    }
    logging.basicConfig(**kwargs)


def suites(args):
    '''
       subcommand suites: print a list of registered suites
    '''
    logger = logging.getLogger('suites')
    suites = getSuites(args.suite.split(','))
    for s in sorted(suites):
        print("# {}{}".format(s.getSuiteName(), (" [" + (":, ".join(sorted(s.getTags())) + ":]")) if len(s.getTags()) > 0 else ""))
        if args.verbose:
            print(s.getSourcesList() + "\n")



def show(args):
    '''
       subcommand show: print details about packages similar to what apt-cache show does
    '''
    logger = logging.getLogger('show')

    (result, requestFields) = queryPackages(args)

    formatter = singleLines_formatter

    if args.diff:
        diff_formatter(result, requestFields, args.diff, args.diff_tool, False, formatter)            
    else:
        formatter(result, requestFields, False, sys.stdout)


def ls(args):
    '''
       subcommand ls: search and print a list of packages
    '''
    logger = logging.getLogger('ls')

    (result, requestFields) = queryPackages(args)
    
    if args.format == 'table':
        formatter = table_formatter
    elif args.format == 'list':
        formatter = list_formatter

    if args.diff:
        diff_formatter(result, requestFields, args.diff, args.diff_tool, args.no_header, list_formatter)            
    else:
        formatter(result, requestFields, args.no_header, sys.stdout)


def dsc(args):
    '''
       subcommand dsc: list urls of dsc-files available for source-packages.
    '''
    logger = logging.getLogger('dsc')

    suites = getSuites(args.suite.split(','))
    requestPackages = { p for p in args.package }
    requestComponents = { c for c in args.component.split(',') } if args.component else {}

    showProgress = True
    pp(showProgress, "{}querying sources lists for {} suites".format(
        "updating (use --no-update to skip) and " if not args.no_update else "", len(suites)))

    urls = list()
    for x, suite in enumerate(suites):
        pp(showProgress, ".{}".format(x+1))
        res = queryDscFiles(suite, requestPackages, requestComponents, logger, not args.no_update, args.first)
        if res:
            urls.extend(res)
        if args.first and len(urls) > 0:
            break
    pp(showProgress, '\n')

    for url in urls:
        print(url)


def queryDscFiles(suite, requestPackages, requestComponents, logger, update, first):
    '''
       queries for DSC-Files in sources lists provided by the apt_repos.Suite suite,
       - Matching all packages in requestPackages (yet, matching the exact name only) 
       - and from the requestedComponents (also exact match)
       - Printing debugging information to logger
       - Updating during scan if update==True
       - Returning immediately after the first match if first==True
       - Returning a list of urls to DSC-Files
    '''
    import apt_pkg
    result = list()
    logger.debug("querying sources from " + suite.getSuiteName())
    suite.scan(update)
    sourcesFiles = suite.getSourcesFiles()
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
        if len(requestComponents) > 0 and not component in requestComponents:
            logger.debug("skipping component {} as not requested in --component".format(component))
            continue

        logger.debug("parsing sources file {}".format(sourcesFile))
        with open(sourcesFile, 'r') as f:
            tagfile = apt_pkg.TagFile(f)
            for package in tagfile:
                name = package['Package']
                if not name in requestPackages:
                    continue
                dscFile = None
                for f in package['Files'].split("\n"):
                    (md5, size, fname) = f.strip().split(" ")
                    if fname.endswith(".dsc"):
                        dscFile = fname
                if not dscFile:
                    logger.warn("Did't find a dsc-file in Files-Attribute:\n{}".format(package['Files']))
                    continue
                path = os.path.join(package['Directory'], dscFile)
                url = os.path.join(suite.getRepoUrl(), path)
                result.append(url)
                if first:
                    return result
    return result


def table_formatter(result, requestFields, no_header, outfile):
    header = [f.getHeader() for f in requestFields]    
    resultList = sorted(result)

    # calculate max col_widths (witch must be at least 1)
    col_width = [max(len(str(x)) for x in col) for col in zip(*result)]
    col_width = [max(1, w) for w in (col_width + [1]*(len(header)-len(col_width)))]
    if not no_header:
        # recalculate col_width for header, too
        col_width = [max(len(h), w) for h, w in zip(header, col_width)]
        print (" | ".join("{!s:{}}".format(h, w) for h, w in zip(header, col_width)), file=outfile)
        print (" | ".join("{!s:{}}".format("="*w, w) for w in col_width), file=outfile)
    for r in resultList:
        print (" | ".join("{!s:{}}".format(d, w) for d, w in zip(r.getData(), col_width)), file=outfile)


def list_formatter(result, requestFields, no_header, outfile):
    header = [f.getHeader() for f in requestFields]    
    resultList = sorted(result)

    if not no_header:
        print (" ".join(header), file=outfile)
    for r in resultList:
        print (" ".join([str(d) for d in r.getData()]), file=outfile)


def singleLines_formatter(result, requestFields, no_header, outfile):
    header = [f.getHeader() for f in requestFields]    
    resultList = sorted(result)

    print(file=outfile)    
    for r in resultList:
        data = r.getData()
        for h, d in zip(header, data):
            if h == "Full-Record":
                print (d, file=outfile)
            else:
                print ("{}: {}".format(h, d), file=outfile)


def diff_formatter(result, requestFields, diffField, diffTool, no_header, subFormatter):
    logger = logging.getLogger('diff_formatter')
    
    # split result list at diffField into two different sets:
    dfParts = diffField.split("^")
    df = PackageField.getByFieldsString(dfParts[0])[0]
    dfIgnores = dfParts[1:]
    dropColumns = set() # implemented as a set because diffField could be in
                        # requestFields multiple times. So we want to drop this
                        # column multiple time - allways for the same diffField!
                        # (this doesn't make much sense, but it could happen)
    newFields = list()
    for x, field in enumerate(requestFields):
        if field == df:
            dropColumns.add(x)
        else:
            newFields.append(field)
    newResults = {} # example: a map of { 'i386' : resultSet1, 'amd64' : resultSet2 } if diffField='a'
    for r in result:
        newData = list()
        newResultSet = set()
        for x, d in enumerate(r.getData()):
            if x in dropColumns:
                if str(d) in dfIgnores:
                    continue
                aSet = newResults.get(str(d))
                if not aSet:
                    aSet = set()
                    newResults[str(d)] = aSet
                newResultSet = aSet                
            else:
                newData.append(d)
        newResultSet.add(QueryResult(newFields, tuple(newData)))        
                
    if len(newResults) != 2:
        raise AnError("We got not exactly 2 differentiators for Diff-Field '{}'. We found: '{}'. Use -di {}^... to ignore results for one of these values."
                        .format(df.getHeader(), 
                                "', '".join(sorted(newResults.keys())),
                                df.getChar()))
        
    tmpFiles = list()
    for part in sorted(newResults.keys()):            
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            logger.debug("Part {}, TmpFileName {}".format(part, tmp.name))
            tmpFiles.append(tmp.name)
            if not no_header:
                print("Results for {} '{}'".format(df.getHeader(), part), file=tmp)
                print("", file=tmp)
            subFormatter(newResults[part], newFields, no_header, tmp)

    cmd = diffTool.split(",")
    cmd.extend(tmpFiles)
    subprocess.call(cmd)
    for tmp in tmpFiles:
        os.remove(tmp)


def queryPackages(args):
    '''
       queries Packages by the args provided on the command line and returns a
       tuple of (queryResults, requestFields)
    '''
    logger = logging.getLogger('queryPackages')

    suites = getSuites(args.suite.split(','))
    requestPackages = { p for p in args.package }
    requestArchs = { a for a in args.architecture.split(',') } if args.architecture else {}
    requestComponents = { c for c in args.component.split(',') } if args.component else {}
    requestFields = PackageField.getByFieldsString(args.columns)

    result = set()
    showProgress = True
    pp(showProgress, "{}querying packages lists for {} suites".format(
        "updating (use --no-update to skip) and " if not args.no_update else "", len(suites)))
    for x, suite in enumerate(suites):
        pp(showProgress, '.')
        try:
            suite.scan(not args.no_update)
            pp(showProgress, x+1)
            result = result.union(suite.queryPackages(requestPackages, args.regex, requestArchs, requestComponents, requestFields))
        except SystemError as e:
            logger.warn("Could not retrieve packages for suite {}:\n{}".format(suite.getSuiteName(), e))
    pp(showProgress, '\n')
    return (result, requestFields)


def pp(show, message):
    '''
       prints and flushes a progress message <message> without newline to stderr if <show> is True.
    '''
    if show:
        print(message, end='', flush=True, file=sys.stderr)

    
class AnError (Exception):
    def __init__(self, message):
        super(AnError, self).__init__("ERROR: " + message)


if __name__ == "__main__":
    try:
        main()
    except (AnError) as e:
        print("\n" + str(e) + "\n",  file=sys.stderr)
        sys.exit(1)
