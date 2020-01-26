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

import apt_repos
from apt_repos import PackageField, QueryResult

logger = logging.getLogger(__name__)


def main():
    
    # fixup to get help-messages for subcommands that require positional argmuments
    # so that "apt-repos -h <subcommand>" prints a help-message and not an error
    for subcmd in ['ls', 'list', 'src', 'source', 'sources', 'dsc', 'show']:
        if ("-h" in sys.argv or "--help" in sys.argv) and subcmd in sys.argv:
            sys.argv.append(".")
    
    parser = createArgparsers()[0]
    args = parser.parse_args()

    setupLogging(logging.DEBUG if args.debug else logging.INFO)
    
    if "diff" in args.__dict__ and args.diff:
        diffField = args.diff.split("^")[0]
        if len(diffField) != 1:
            raise AnError("-di needs exactly one diffField character as argument. provided is: '{}'".format(diffField))
        elif not diffField in args.columns:
            raise AnError("The character -di needs to be also in -col. provided is: -col '{}' and -di '{}'".format(args.columns, diffField))

    if args.basedir:
        apt_repos.setAptReposBaseDir(args.basedir)
    
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

    # main parser
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
    
    # subcommand parsers
    parse_ls = subparsers.add_parser('list', aliases=['ls'], help='query and list binary packages and their properties', description=ls.__doc__)
    parse_src = subparsers.add_parser('sources', aliases=['src', 'source'], help='query and list source packages and their properties', description=src.__doc__)
    parse_suites = subparsers.add_parser('suites', help='list configured suites', description=suites.__doc__)
    parse_show = subparsers.add_parser('show', help='show details about packages similar to apt-cache show', description=show.__doc__)
    parse_dsc = subparsers.add_parser('dsc', help='list urls of dsc-files for particular source-packages.', description=dsc.__doc__)

    parse_ls.set_defaults(sub_function=ls, sub_parser=parse_ls)
    parse_src.set_defaults(sub_function=src, sub_parser=parse_src)
    parse_suites.set_defaults(sub_function=suites, sub_parser=parse_suites)
    parse_show.set_defaults(sub_function=show, sub_parser=parse_show)
    parse_dsc.set_defaults(sub_function=dsc, sub_parser=parse_dsc)

    # mapping of common arguments:
    ___x = ____x = _____x = _______x = 0 # undefined for this subcommand
    __SS = __SSSS = 1                    # argument exists in a special variant
    commonArguments = {
        parse_ls:     [ '-d', '-s', '-a', '-c', '-r', '-O', '-nu', '-nh', '-col', '-f', '-di', '-dt', 'package', ___x, ___x ],
        parse_src:    [ '-d', '-s', ___x, '-c', '-r', '-O', '-nu', '-nh', __SSSS, '-f', '-di', '-dt', 'source' , ___x, ___x ],
        parse_suites: [ '-d', __SS, ___x, ___x, ___x, ___x, ____x, ____x, _____x, ___x, ____x, ____x,  _______x, '-v', ___x ],
        parse_show:   [ '-d', '-s', '-a', '-c', '-r', ___x, '-nu', ____x, __SSSS, ___x, '-di', '-dt', 'package', ___x, ___x ],
        parse_dsc:    [ '-d', __SS, ___x, '-c', ___x, ___x, '-nu', ____x, _____x, ___x, ____x, ____x, 'source' , ___x, '-1' ],
    }

    # add common arguments (if argument is defined in the above map)
    for pars, o in commonArguments.items():
        addArg(pars, o, "-d", "--debug", action="store_true", help="""
                        Switch on debugging message printed to stderr.""")
        addArg(pars, o, "-s", "--suite", default='default:', help="""
                        Only show info for these SUITE(s). The list of SUITEs is specified comma-separated.
                        The default value is 'default:'.""")
        addArg(pars, o, "-a", "--architecture", help="""
                        Only show info for ARCH(s). The list of ARCHs is specified comma-separated.""")
        addArg(pars, o, "-c", "--component", help="""
                        Only show info for COMPONENT(s). The list of COMPONENTs is specified comma-separated.
                        Note: component and section fields are not exactly the same. A component is only the first part
                        of a section (everything before the '/'). There is also a special treatment for sections
                        in the component 'main', in which case 'main/' is typically not named in a section-field.
                        For this switch -c we have to specify 'main' to see packages from the component 'main'.""")
        addArg(pars, o, "-r", "--regex", action="store_true", help="""
                        Treat PACKAGE as a regex. Searches for binary package-names or
                        binary packages that were built from a source prefixed with 'src:'.
                        Examples:
                        Use regex '.' to show all packages.
                        Use regex '^pkg' to show all packages starting with 'pkg'.
                        Use regex '^src:source' to show packages that were built from a source starting with 'source'.""")
        addArg(pars, o, "-O", "--no-old-versions", action="store_true", help="""
                        Ignore old package versions found in a suite.""")
        addArg(pars, o, "-nu", "--no-update", action="store_true", default=False, help="Skip downloading of packages list.")
        addArg(pars, o, "-nh", "--no-header", action="store_true", default=False, help="Don't print the column header.")
        addArg(pars, o, "-col", "--columns", type=str, required=False, default='pvsaSC', help="""
                        Specify the columns that should be printed. Default is 'pvsaSC'.
                        Possible characters are: """ + fieldChars)
        addArg(pars, o, "-f", "--format", type=str, choices=['table', 'list', 'grouped_list'], required=False, default='table', help="""
                        Specifies the output-format of the package list. Default is 'table'.
                        Possible values: 'table' to pretty print a nice table; 'list' to print a
                        space separated list of columns that can easily be processed with bash tools;
                        Use 'grouped_list' to do nearly the same as 'list' but add a newline for each
                        new value in the first column (which means we group over identical values in the
                        first column).""")
        addArg(pars, o, "-di", "--diff", type=str, required=False, help="""
                        Specify the character of a colunm over which we should compare two different results.
                        The character needs to be one of the characters described for the --columns switch.
                        Typical useful comparisons are e.g. comparing the results for two different 
                        architectures i386/amd64 (a) or comparing two different suites (s).
                        Since we can just compare two different results, please ensure that the result set of your
                        query returns exactly two different values for the specified column. It could be
                        necessary to ignore some results. E.g if '--diff a' is specified and our query returns 3 results
                        for the architectures 'amd64', 'i386' and 'all', we might want to ignore architecture 'all'
                        packages. This can be done using the argument '--diff a^all' which would ignore the 
                        architecture 'all' packages and just compare 'amd64' and 'i386' packages.""")
        addArg(pars, o, "-dt", "--diff-tool", type=str, default=diffToolDefault.format(ttyWidth), required=False, help="""
                        Diff-Tool used to compare the separated results from --diff.
                        Default is '{}'.
                        Use , (instead of spaces) to provide arguments for the difftool.""".format(diffToolDefault.format("<ttyWidth>")))
        addArg(pars, o, "-v", "--verbose", action="store_true", help="""
                        also print corresponding sources.list-entries for each suite""")
        addArg(pars, o, "-1", "--first", action="store_true", default=False, help="""
                        Query only for the first matching dsc file for a source package, then skip the others sources
                        for this package.""")

    # special variant for subcommand suites
    parse_suites.add_argument("-s", "--suite", default=':', help="""
                        Only show info for these SUITE(s). The list of SUITEs is specified comma-separated.
                        The default value is ':' (all suites).""")

    # special variant for subcommand source
    parse_src.add_argument("-col", "--columns", type=str, required=False, default='CvsaS', help="""
                        Specify the columns that should be printed. Default is 'sR'.
                        Possible characters are: """ + fieldChars)

    # special variant for subcommand show
    parse_show.add_argument("-col", "--columns", type=str, required=False, default='sR', help="""
                        Specify the columns that should be printed. Default is 'sR'.
                        Possible characters are: """ + fieldChars)

    # special variant for subcommand dsc
    parse_dsc.add_argument("-s", "--suite", default='default:', help="""
                        Only show info for these SUITE(s). The list of SUITEs is specified comma-separated.
                        The list of suites is scanned in the specified order. If the list contains a tag
                        or a selector that matches multiple suites (e.g. default:), these suites are scanned
                        in reverse order as specified in the corresponding *.suites-file.
                        This specific ordering is in particular interesting together with --first.
                        The default value is 'default:'.""")

    for pars, o in commonArguments.items():
        addArg(pars, o, 'package', nargs='+', help='Name of a binary PACKAGE or source-package name prefixed as src:SOURCENAME')
        addArg(pars, o, 'source', nargs='+', help='Name of a source package')

    return (parser, parse_ls, parse_src, parse_show, parse_suites, parse_dsc)


def addArg(parser, options, *args, **kwargs):
    if args[0] in options:
            parser.add_argument(*args, **kwargs)


def setupLogging(loglevel):
    '''
       Initializing logging and set log-level
    '''
    kwargs = {
        'format': '%(levelname)s[%(name)s]: %(message)s',
        'level': loglevel,
        'stream': sys.stderr
    }
    logging.basicConfig(**kwargs)
    logging.getLogger("urllib3").setLevel(logging.ERROR)



def suites(args):
    '''
       subcommand suites: print a list of registered suites
    '''
    suites = apt_repos.getSuites(args.suite.split(','))
    for s in sorted(suites):
        print("# {}{}".format(s.getSuiteName(), (" [" + (":, ".join(sorted(s.getTags())) + ":]")) if len(s.getTags()) > 0 else ""))
        if args.verbose:
            print(s.getSourcesList() + "\n")



def show(args):
    '''
       subcommand show: print details about packages similar to what apt-cache show does
    '''
    (result, requestFields) = queryPackages(args.suite, args.package, args.regex, args.architecture, args.component, args.columns, args.no_update)

    formatter = singleLines_formatter

    if args.diff:
        diff_formatter(result, requestFields, args.diff, args.diff_tool, False, formatter)            
    else:
        formatter(result, requestFields, False, sys.stdout)


def ls(args, querySources = False):
    '''
       subcommand list: search and print a list of binary packages
    '''
    (result, requestFields) = queryPackages(args.suite, args.package, args.regex, args.architecture, args.component, args.columns, noUpdate=args.no_update, latestOnly=args.no_old_versions)
    formatListResult(args, result, requestFields)


def src(args):
    '''
       subcommand source: search and print a list of source packages
    '''
    (result, requestFields) = queryPackages(args.suite, args.source, args.regex, None, args.component, args.columns, noUpdate=args.no_update, querySources=True, latestOnly=args.no_old_versions)
    formatListResult(args, result, requestFields)


def dsc(args):
    '''
       subcommand dsc: list urls of dsc-files available for source-packages.
    '''
    # parse --suite and determine the specific suite scan-order
    suites = list()
    for selector in args.suite.split(','):
        suites.extend(sorted(apt_repos.getSuites([selector]), reverse=True))
    
    requestPackages = { p for p in args.source }
    requestComponents = { c for c in args.component.split(',') } if args.component else {}

    showProgress = True
    pp(showProgress, "{}querying sources lists for {} suites".format(
        "updating (use --no-update to skip) and " if not args.no_update else "", len(suites)))

    results = {}
    for package in requestPackages: # pre-seed results
        results[package] = list()

    for x, suite in enumerate(suites):
        pp(showProgress, ".{}".format(x+1))
        queryDscFiles(results, suite, requestComponents, logger, not args.no_update, args.first)
        if args.first and gotAllFirsts(results):
           break

    pp(showProgress, '\n')

    for package, urls in sorted(results.items()):
        for url in urls[: 1 if (args.first and len(urls) > 0) else len(urls)]:
            print(url)


def queryDscFiles(results, suite, requestComponents, logger, update, first):
    '''
       queries for DSC-Files in sources lists provided by the apt_repos.Suite suite,
       - Find a source package for each key in results (yet, matching the exact package name only) 
       - Printing debugging information to logger
       - Updating ReposSuite during scan if update==True
       - Don't neccissarily collect more than one URL for a package if first==True
       - adds all found dsc-files to results
       - results is a hash map with key ("package name") to a "list of urls" mapping
    '''
    import apt_pkg
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
                urls = results.get(name) # results is pre-seeded with the requested packages
                if urls == None:
                    continue
                dscFile = None
                for f in package['Files'].split("\n"):
                    (unused_md5, unused_size, fname) = f.strip().split(" ")
                    if fname.endswith(".dsc"):
                        dscFile = fname
                if not dscFile:
                    logger.warn("Did't find a dsc-file in Files-Attribute:\n{}".format(package['Files']))
                    continue
                path = os.path.join(package['Directory'], dscFile)
                url = os.path.join(suite.getRepoUrl(), path)
                urls.append(url)
                if first and gotAllFirsts(results):
                    return
    return


def gotAllFirsts(results):
    if not results:
        return True
    for unused_package, urls in results.items():
        if len(urls) == 0:
            return False
    return True


def formatListResult(args, result, requestFields):
    if args.format == 'table':
        formatter = table_formatter
    elif args.format == 'list':
        formatter = list_formatter
    elif args.format == 'grouped_list':
        formatter = grouped_list_formatter

    if args.diff:
        diff_formatter(result, requestFields, args.diff, args.diff_tool, args.no_header, list_formatter)
    else:
        formatter(result, requestFields, args.no_header, sys.stdout)


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


def list_formatter(result, requestFields, no_header, outfile, separateGroups=False):
    header = [f.getHeader() for f in requestFields]    
    resultList = sorted(result)

    k = None
    if not no_header:
        print (" ".join(header), file=outfile)
        k = "__header__"

    for r in resultList:
        # separate Blocks with newlines
        nk = r.getData()[0] if len(r.getData()) > 0 else None
        if separateGroups and k and k != nk:
            print(file=outfile)
        k = nk

        print (" ".join([str(d) for d in r.getData()]), file=outfile)


def grouped_list_formatter(result, requestFields, no_header, outfile):
    list_formatter(result, requestFields, no_header, outfile, True)


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
    subprocess.call(cmd, stdout=sys.stdout)
    for tmp in tmpFiles:
        os.remove(tmp)


def queryPackages(suiteStr, requestPackages, regexStr, archStr, componentStr, fieldStr, noUpdate=False, querySources=False, latestOnly=False):
    '''
       queries Packages by the args provided on the command line and returns a
       tuple of (queryResults, requestFields)
    '''
    suites = apt_repos.getSuites(suiteStr.split(','))
    requestArchs = { a for a in archStr.split(',') } if archStr else {}
    requestComponents = { c for c in componentStr.split(',') } if componentStr else {}
    requestFields = PackageField.getByFieldsString(fieldStr)

    result = set()
    showProgress = True
    pp(showProgress, "{}querying packages lists for {} suites".format(
        "updating (use --no-update to skip) and " if not noUpdate else "", len(suites)))
    for x, suite in enumerate(suites):
        pp(showProgress, '.')
        try:
            suite.scan(not noUpdate)
            pp(showProgress, x+1)
            if not querySources:
                result = result.union(suite.queryPackages(requestPackages, regexStr, requestArchs, requestComponents, requestFields, latestOnly=latestOnly))
            else:
                result = result.union(suite.querySources(requestPackages, regexStr, requestArchs, requestComponents, requestFields, latestOnly=latestOnly))
        except SystemError as e:
            logger.warn("Could not retrieve {} for suite {}:\n{}".format("sources" if querySources else "packages", suite.getSuiteName(), e))
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
    with apt_repos.suppress_unwanted_apt_pkg_messages() as forked:
        if forked:
            try:
                main()
            except (AnError) as e:
                print("\n" + str(e) + "\n",  file=sys.stderr)
                sys.exit(1)
