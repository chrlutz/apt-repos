#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys

sys.path.append("tools/")
sys.path.append("bin/")
sys.path.append(".")

from build_manpage import ManPageFormatter

from apt_repos_cli import createArgparsers, __doc__, ls, show, suites, dsc, src


def main():	
    sections = {'authors': ("apt-repos is written and maintained by Christoph Lutz <chrlutz@gmail.com>\n "
                            "with contributions from the Landeshauptstadt München.\n "
                            "Other contributors are welcome."),
               'distribution': ("provided as debian-Packages created from the sources on github:\n "
                                "https://github.com/chrlutz/apt-repos")
    }

    (parser, parser_ls, parser_src, parser_show, parser_suites, parser_dsc) = createArgparsers()

    createManpage(parser, 'apt-repos', __doc__.strip(), sections)
    createManpage(parser_ls, 'apt-repos ls', ls.__doc__.strip(), sections)
    createManpage(parser_src, 'apt-repos src', src.__doc__.strip(), sections)
    createManpage(parser_dsc, 'apt-repos dsc', dsc.__doc__.strip(), sections)
    createManpage(parser_show, 'apt-repos show', show.__doc__.strip(), sections)
    createManpage(parser_suites, 'apt-repos suites', suites.__doc__.strip(), sections)


def createManpage(parser, appname, desc, sections):
    filename="man/{}.1".format(appname.replace(" ", "-"))
    mpf = ManPageFormatter(appname, desc=desc, long_desc=desc, ext_sections=sections)
    m = mpf.format_man_page(parser)
    with open(filename, 'wb') as f:
        f.write(m.encode('utf8'))


if __name__ == "__main__":
    main()
