import os
import sys

from build_manpage import ManPageFormatter

sys.path.append("../src/")
from apt_repos import createArgumentParser

mpf = ManPageFormatter("apt-repos",
                       desc=apt_repos.__doc__,
                       long_desc=apt_repos.__doc__,
                       ext_sections=sections)

parser = createArgumentParser()
m = mpf.format_man_page(parser)

with open("man/apt-repos.1", 'w') as f:
    f.write(m)
