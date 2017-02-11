#!/usr/bin/python3
##################################################################################
# Show information about binary and source packages in multiple
# (independent) apt-repositories utilizing libapt / python-apt/
# apt_pkg without the need to change the local system and it's apt-setup.
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
"""
This python module provides methods and classes to retrieve information
about debian binary- and source-packages from independent apt-repositories
using python apt_pkg module. Analog to well the well known tool apt-cache
it downloads Packages files from the inspected repsitories to a local cache
and reads the information from there. One main advantage of this module
is, that the local apt-setup (/etc/apt/sources.list, ...) don't need to
be modified in order to retrieve package information via apt.
"""

