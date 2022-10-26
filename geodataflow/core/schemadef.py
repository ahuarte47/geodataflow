# -*- coding: utf-8 -*-
"""
===============================================================================

   GeodataFlow:
   Toolkit to run workflows on Geospatial & Earth Observation (EO) data.

   Copyright (c) 2022, Alvaro Huarte. All rights reserved.

   Redistribution and use of this code in source and binary forms, with
   or without modification, are permitted provided that the following
   conditions are met:
   * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.
   * Redistributions in binary form must reproduce the above copyright notice,
     this list of conditions and the following disclaimer in the documentation
     and/or other materials provided with the distribution.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
   TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
   PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
   EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
   OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
   WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
   OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SAMPLE CODE, EVEN IF
   ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

===============================================================================
"""

from datetime import date, datetime
from typing import Any, List


class DataType(object):
    """
    List of available Data Types of Attributes or Columns (Identifiers and types
    match the OGR/Fiona type specs).
    """
    """
    + OGR OFT enum: [
        ogr.OFTInteger,
        ogr.OFTIntegerList,
        ogr.OFTReal,
        ogr.OFTRealList,
        ogr.OFTString,
        ogr.OFTStringList,
        ogr.OFTWideString,
        ogr.OFTWideStringList,
        ogr.OFTBinary,
        ogr.OFTDate,
        ogr.OFTTime,
        ogr.OFTDateTime,
        ogr.OFTInteger64,
        ogr.OFTInteger64List
        ]
    + fiona.ogrext.FIELD_TYPES: [
        'int32', None, 'float', None, 'str', None, None, None, 'bytes',
        'date', 'time', 'datetime', 'int64', None
        ]
    + fiona.ogrext.FIELD_TYPES_MAP: {
        'int32': <class 'int'>,
        'float': <class 'float'>,
        'str': <class 'str'>,
        'bytes': <class 'bytes'>,
        'date': <class 'fiona.rfc3339.FionaDateType'>,
        'time': <class 'fiona.rfc3339.FionaTimeType'>,
        'datetime': <class 'fiona.rfc3339.FionaDateTimeType'>,
        'int64': <class 'int'>,
        'int': <class 'int'>
        }
    """
    Integer = 0
    Float = 2
    String = 4
    Binary = 8
    Date = 9
    Time = 10
    DateTime = 11
    Integer64 = 12

    @staticmethod
    def to_data_type(value: Any) -> "DataType":
        """
        Returns the DataType of the specified value.
        """
        if isinstance(value, int):
            return DataType.Integer
        if isinstance(value, float):
            return DataType.Float
        if isinstance(value, str):
            return DataType.String
        if isinstance(value, bytes):
            return DataType.Binary
        if isinstance(value, date):
            return DataType.Date
        if isinstance(value, datetime):
            return DataType.DateTime
        if isinstance(value, bool):
            return DataType.Integer

        return DataType.String


class GeometryType(object):
    """
    List of available Geometry Types (Identifiers and types match the OGR/Fiona WKB type specs).
    """
    """
    + OGR GT enum: [
        ogr.wkbUnknown,
        ogr.wkbPoint, ogr.wkbPointM (wkb+2000), ogr.wkbPointZM (wkb+3000),
        ogr.wkbLineString, ...
        ogr.wkbPolygon,
        ogr.wkbMultiPoint,
        ogr.wkbMultiLineString,
        ogr.wkbMultiPolygon,
        ogr.wkbGeometryCollection
        ]
    """
    Unknown = 0
    Point = 1
    LineString = 2
    Polygon = 3
    MultiPoint = 4
    MultiLineString = 5
    MultiPolygon = 6
    GeometryCollection = 7


class FieldDef:
    """
    Provides metadata information of a Geospatial Attribute or Column.
    """
    def __init__(self,
                 name: str,
                 data_type: DataType,
                 precision: int = 0,
                 width: int = 0,
                 is_nullable: bool = True,
                 default_value: Any = None,
                 **kwargs):
        self.name = name
        self.type = data_type
        self.precision = precision
        self.width = width
        self.nullable = is_nullable
        self.defaultValue = default_value
        for arg in kwargs:
            setattr(self, arg, kwargs[arg])

    def __str__(self) -> str:
        """
        Returns the String representation of this Object.
        """
        return 'Name = {}, DataType = {}, Precision = {}, Width = {}, Nullable = {}, Default = {}' \
               .format(self.name,
                       self.type,
                       self.precision,
                       self.width,
                       self.nullable,
                       self.defaultValue)

    def copy(self, field_def: "FieldDef") -> None:
        """
        Copy the metadata information of specified input FieldDef.
        """
        for k, v in field_def.__dict__.items():
            setattr(self, k, v)

    def clone(self) -> "FieldDef":
        """
        Clone this FieldDef object.
        """
        new_obj = FieldDef(name=self.name, data_type=self.type)
        new_obj.copy(self)
        return new_obj


class SchemaDef:
    """
    Provides metadata information of a Geospatial Dataset.
    """
    def __init__(self, **kwargs):
        self.name = ''
        self.type = ''
        self.srid = 0
        self.crs = None
        self.geometryType = None
        self.envelope = None
        self.fields = list()
        for arg in kwargs:
            setattr(self, arg, kwargs[arg])

    def copy(self, schema_def: "SchemaDef") -> None:
        """
        Copy the metadata information of specified input SchemaDef.
        """
        for k, v in schema_def.__dict__.items():
            setattr(self, k, v)

        self.fields = [fd.clone() for fd in schema_def.fields]

    def clone(self) -> "SchemaDef":
        """
        Clone this SchemaDef object.
        """
        new_obj = SchemaDef()
        new_obj.copy(self)
        return new_obj

    def merge(self, other: "SchemaDef") -> "SchemaDef":
        """
        Merge metadata of this Object and specified input SchemaDef.
        """
        if not other:
            return self

        a, b = self, other

        geometry_type_a = a.geometryType
        geometry_type_b = b.geometryType
        if geometry_type_a != geometry_type_b:
            raise Exception('Merging SchemaDefs of different GeometryType is not supported.')
        srid_a = a.srid
        srid_b = b.srid
        if srid_a != srid_b:
            raise Exception('Merging SchemaDefs of different CRS is not supported.')

        from geodataflow.core.common import CaseInsensitiveDict
        fields1 = b.fields
        fd_hash = CaseInsensitiveDict({field.name: field for field in a.fields})
        fields1 = [f.clone() for f in fields1 if fd_hash.get(f.name, None) is None]
        if not fields1:
            return a
        schema_def = a.clone()
        schema_def.fields = schema_def.fields + fields1
        return schema_def

    @staticmethod
    def merge_all(schemas: List["SchemaDef"]) -> "SchemaDef":
        """
        Merge metadata of specified stream of input SchemaDefs.
        """
        if not schemas:
            return None

        a = schemas[0]
        for b in schemas[1:]:
            a = a.merge(b)

        return a
