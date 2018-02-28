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
import logging
import apt_pkg
from enum import Enum

logger = logging.getLogger(__name__)


class Priority(Enum):
    '''
        This Enum describes the values defined for Priority-Fields.
    '''
    REQUIRED = apt_pkg.PRI_REQUIRED
    IMPORTANT = apt_pkg.PRI_IMPORTANT
    STANDARD = apt_pkg.PRI_STANDARD
    OPTIONAL = apt_pkg.PRI_OPTIONAL
    EXTRA = apt_pkg.PRI_EXTRA

    def __str__(self):
        return self.name.lower()

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return self.value == other.value

    def __ne__(self, other):
        return not(self == other)

    def __lt__(self, other):
        return self.value < other.value
    
    @staticmethod    
    def getByInt(intVal):
        for p in Priority:
            if intVal == p.value:
                return p
        return Priority.EXTRA

    @staticmethod
    def getByName(name):
        for p in Priority:
            if name.upper() == p.name:
                return p
        return Priority.EXTRA
