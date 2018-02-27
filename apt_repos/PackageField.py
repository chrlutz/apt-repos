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
from enum import Enum

logger = logging.getLogger(__name__)


class PackageField(Enum):
    '''
        This Enum describes the Fields that can be returned as values in a QueryResult.
        Each PackageField is assigned a unique character that can be used to easily define
        a list of Fields we want to query for in form of a fieldsString.
    '''
    BINARY_PACKAGE_NAME = ('p', 'Package')
    VERSION = ('v', 'Version')
    SUITE = ('s', 'Suite')
    ARCHITECTURE = ('a', 'Arch')
    SECTION = ('S', 'Section')
    PRIORITY = ('P', 'Priority')
    SOURCE_PACKAGE_NAME = ('C', 'Source')
    LONG_DESC = ('L', 'Long-Desc')
    RECORD = ('R', 'Full-Record')
    BASE_URL = ('B', 'Base-Url')
    FILENAME = ('F', 'File-Url')

    def __str__(self):
        return "<PackageField.{}>".format(self.name)
    
    
    def getHeader(self):
        char, header = self.value
        return header
    
    
    def getChar(self):
        char, header = self.value
        return char
    
    
    @staticmethod    
    def getByFieldsString(fieldsString):
        res = list()
        for c in fieldsString:
            found = None
            for f in PackageField:
                char, header = f.value
                if str(c) == str(char):
                    found = f
            if found:
                res.append(found)
            else:
                raise Exception("Unknown format-character '" + c + "'")
        return res
