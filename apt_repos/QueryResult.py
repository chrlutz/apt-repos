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
import os
import apt_pkg
from apt_repos.PackageField import PackageField
from apt_repos.Priority import Priority

logger = logging.getLogger(__name__)


class QueryResult:
    '''
        A QueryResult is able to carry the requestedFields (and only the requestedFields)
        in the order they were requested. This order is also relevant for sorting.
        A QueryResult is hashable which makes it possible to accumulate QueryResults by
        the requestedFields.
    '''
    
    def __init__(self, fields, data):
        '''
            This constructor creates a QueryResult for the list of PackageField fields
            and their corresponding field-data (as a tuple)
            
            fields: List of type PackageField that describes which fields
                             this QueryResult should carry.
                             
            data: tuple of values for each of the fields
        '''
        self.fields = fields
        self.data = data
        
        
    @staticmethod
    def createByAptPkgStructures(requestedFields, pkg, version, curRecord, suite, source):
        '''
            This factory-method creates a QueryResult for the requestedFields. The
            corresponding data are collected from the provided apt_pkg objects:
            
            requestedFields: List of type PackageField that describes which fields
                             this QueryResult should carry.
            
            pkg: Object of type apt_pkg.Package (see apt_pkg docs)
            
            version: Object of type apt_pkg.Version (see apt_pkg docs)
            
            curRecord: Object of type apt_pkg.PackageRecords (see apt_pkg docs)
            
            suite: The RepoSuite object
            
            source: source name (It seems that this information is already provided
                    in curRecord.source_pkg, but this is not quite true. If package
                    name and source name are equal, curRecord.source_pkg will be empty.
                    Since I'am not quite clear, if this is the only reason for
                    curRecord.source_pkg to be empty, we force the caller to provide
                    the exact source name directly).
        '''
        data = list()        
        if type(requestedFields) == str:
            requestedFields = PackageField.getByFieldsString(requestedFields)
        for field in requestedFields:
            if field == PackageField.BINARY_PACKAGE_NAME:
                data.append(pkg.name)
            elif field == PackageField.VERSION:
                data.append(version.ver_str)
            elif field == PackageField.ARCHITECTURE:
                data.append(version.arch)
            elif field == PackageField.SECTION:
                data.append(version.section)
            elif field == PackageField.PRIORITY:
                data.append(Priority.getByInt(version.priority))
            elif field == PackageField.SOURCE_PACKAGE_NAME:
                data.append(source)
            elif field == PackageField.SUITE:
                data.append(suite)        
            elif field == PackageField.LONG_DESC:
                data.append(curRecord.long_desc)        
            elif field == PackageField.RECORD:
                data.append(curRecord.record)        
            elif field == PackageField.BASE_URL:
                data.append(os.path.join(suite.getRepoUrl(), ""))
            elif field == PackageField.FILENAME:
                data.append(os.path.join(suite.getRepoUrl(), curRecord.filename))
        data = tuple(data)
        return QueryResult(requestedFields, data)


    @staticmethod
    def createBySourcesTagFileSection(requestedFields, source, suite):
        '''
            This factory-method creates a QueryResult for the requestedFields. The
            corresponding data are collected from the provided section of an
            apt_pkg.TagFile:

            requestedFields: List of type PackageField that describes which fields
                             this QueryResult should carry.

            source: Object of type apt_pkg.TagSection that can be retrieved e.g. by
                    apt_pkg.TagFile(<sourceFile>) for a particular sources control
                    file <sourceFile> (see apt_pkg docs).

            suite: The RepoSuite object
        '''
        data = list()
        if type(requestedFields) == str:
            requestedFields = PackageField.getByFieldsString(requestedFields)
        for field in requestedFields:
            if field == PackageField.SOURCE_PACKAGE_NAME:
                data.append(source['Package'])
            elif field == PackageField.VERSION:
                data.append(source['Version'])
            elif field == PackageField.SECTION:
                data.append(source['Section'])
            elif field == PackageField.PRIORITY:
                data.append(Priority.getByName(source['Priority']))
            elif field == PackageField.ARCHITECTURE: # not a final solution!
                data.append(",".join(sorted(source['Architecture'].split(" "))))
            elif field == PackageField.SUITE:
                data.append(suite)
            elif field == PackageField.RECORD:
                data.append(source)
            elif field == PackageField.BASE_URL:
                data.append(os.path.join(suite.getRepoUrl(), ""))
            elif field == PackageField.FILENAME:
                dscFile = None
                for f in source['Files'].split("\n"):
                    (md5, size, fname) = f.strip().split(" ")
                    if fname.endswith(".dsc"):
                        dscFile = fname
                        break
                if dscFile:
                    data.append(os.path.join(suite.getRepoUrl(), source['Directory'], dscFile))
                else:
                    data.append(None)
            else:
                raise Exception('Package Field \'{}\' (or column character \'{}\') is not supported for source packages'.format(field.name, field.getChar()))
        data = tuple(data)
        return QueryResult(requestedFields, data)


    def getData(self):
        '''
            This method returns the field values as a tuple
        '''
        return self.data


    def __iter__(self):
        return iter(self.data)


    def __hash__(self):
        return hash((tuple(self.data), tuple(self.fields)))


    def __eq__(self, other):
        if other == None:
            return False
        return (self.data == other.data and self.fields == other.fields)


    def __ne__(self, other):
        return not(self == other)


    def __lt__(self, other):
        if self.fields != other.fields:
            raise Exception('We can only compare QueryResults with the same fields-order.')
        for field, a, b in zip(self.fields, self.data, other.data):
            if field == PackageField.VERSION and a != b:
                return True if apt_pkg.version_compare(a, b) < 0 else False
            elif a != b:
                return a < b
        return False
    
    
    def __str__(self):
        return "QueryResult(" + ", ".join(["{}:'{}'".format(field.name, data) for field, data in zip(self.fields, self.data)]) + ")"
    
