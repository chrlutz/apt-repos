#!/usr/bin/python3

import os
import sys

sys.path.append("tools/")
from build_manpage import ManPageFormatter

sys.path.append("src/")
from apt_repos import createArgparser, __doc__


def main():	
    sections = {'authors': ("apt-repos is written and maintained by Christoph Lutz <chrlutz@gmail.com>\n "
                            "with contributions from the Landeshauptstadt München.\n "
                            "Other contributors are welcome."),
               'distribution': ("provided as debian-Packages created from the sources on github:\n "
                                "https://github.com/chrlutz/apt-repos")
    }
    parser = createArgparser()

    createManpage(parser, 'apt-repos', __doc__, sections)


def createManpage(parser, appname, desc, sections):
    filename="man/{}.1".format(appname)
    mpf = ManPageFormatter(appname, desc=desc, long_desc=desc, ext_sections=sections)
    m = mpf.format_man_page(parser)
    with open(filename, 'w') as f:
        f.write(m)


if __name__ == "__main__":
    main()
