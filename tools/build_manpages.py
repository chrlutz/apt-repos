#!/usr/bin/python3

import os
import sys

sys.path.append("tools/")
from build_manpage import ManPageFormatter

sys.path.append("src/")
from apt_repos import createArgparsers, __doc__, ls, show, suites, dsc


def main():	
    sections = {'authors': ("apt-repos is written and maintained by Christoph Lutz <chrlutz@gmail.com>\n "
                            "with contributions from the Landeshauptstadt München.\n "
                            "Other contributors are welcome."),
               'distribution': ("provided as debian-Packages created from the sources on github:\n "
                                "https://github.com/chrlutz/apt-repos")
    }

    (parser, parser_ls, parser_show, parser_suites, parser_dsc) = createArgparsers()

    createManpage(parser, 'apt-repos', __doc__.strip(), sections)
    createManpage(parser_ls, 'apt-repos ls', ls.__doc__.strip(), sections)
    createManpage(parser_dsc, 'apt-repos dsc', dsc.__doc__.strip(), sections)
    createManpage(parser_show, 'apt-repos show', show.__doc__.strip(), sections)
    createManpage(parser_suites, 'apt-repos suites', suites.__doc__.strip(), sections)


def createManpage(parser, appname, desc, sections):
    filename="man/{}.1".format(appname.replace(" ", "-"))
    mpf = ManPageFormatter(appname, desc=desc, long_desc=desc, ext_sections=sections)
    m = mpf.format_man_page(parser)
    with open(filename, 'w') as f:
        f.write(m)


if __name__ == "__main__":
    main()
