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

import os
import logging
from typing import Iterable, List

from geodataflow.core.schemadef import FieldDef, SchemaDef
from geodataflow.geoext.commonutils import GdalUtils

from pyproj.crs import CRS
from osgeo import ogr
from osgeo import osr
ogr.UseExceptions()
osr.UseExceptions()


class OgrFeatureLayer(object):
    """
    Wrapper class of the OGR FeatureLayer object.
    """
    def __init__(self, data_source, feature_layer):
        self._data_source = data_source
        self._layer = feature_layer

    def __del__(self):
        self._data_source = None
        self._layer = None

    def data_source(self):
        """
        Returns the OGR DataSource related to this Feature Layer.
        """
        return self._data_source

    def layer(self):
        """
        Returns the OGR Layer managed.
        """
        return self._layer

    def features(self) -> Iterable:
        """
        Enumerate Features of this Feature Layer.
        """
        feature_layer = self._layer
        feature = feature_layer.GetNextFeature()
        #
        # NOTE:
        # We can't use "for feature in feature_layer:" -> https://github.com/nextgis/pygdal/issues/31
        #
        while feature is not None:
            yield feature
            feature = feature_layer.GetNextFeature()

        pass

    @staticmethod
    def create_spatial_reference(schema_def: SchemaDef) -> "osr.SpatialReference":
        """
        Creates an `osr.SpatialReference` from the specified SchemaDef.
        """
        spatial_ref = osr.SpatialReference()

        if hasattr(spatial_ref, 'SetAxisMappingStrategy'):
            spatial_ref.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        if schema_def.srid > 0:
            spatial_ref.ImportFromEPSG(schema_def.srid)
        elif schema_def.crs:
            crs = schema_def.crs

            spatial_ref.ImportFromEPSG(crs.to_epsg()) \
                if crs.to_epsg() else spatial_ref.ImportFromWkt(crs.to_wkt())
        else:
            spatial_ref.ImportFromEPSG(4326)

        return spatial_ref

    @staticmethod
    def create_layer(connection_string: str,
                     layer_name: str,
                     schema_def: SchemaDef,
                     format_options: List[str] = []) -> "OgrFeatureLayer":
        """
        Creates a new OGR FeatureLayer from the specified SchemaDef.
        """
        driver = GdalUtils.get_ogr_driver(connection_string)
        geometry_type = schema_def.geometryType
        spatial_ref = OgrFeatureLayer.create_spatial_reference(schema_def)

        # Remove old existing FeatureStore.
        try:
            if os.path.exists(connection_string):
                driver.DeleteDataSource(connection_string)

        except Exception as e:
            logging.warning(
                'Fail deleting old FeatureStore of "{}", Cause: "{}".'.format(connection_string, e))

        # Create FeatureLayer.
        driver_name = driver.GetName()
        feature_store = driver.CreateDataSource(connection_string, options=format_options)
        feature_layer = feature_store.CreateLayer(layer_name, srs=spatial_ref, geom_type=geometry_type)

        for field_def in schema_def.fields:
            field = ogr.FieldDefn(field_def.name, field_def.type)
            if field_def.width:
                field.SetWidth(field_def.width)
            if field_def.precision:
                field.SetPrecision(field_def.precision)
            if field_def.nullable:
                field.SetNullable(1 if field_def.nullable else 0)
            if field_def.defaultValue:
                field.SetDefault(field_def.defaultValue)

            feature_layer.CreateField(field)

        # Fix current saved PRJ file, the 'ESRI Shapefile' driver saves an invalid WKT spec.
        if driver_name == 'ESRI Shapefile':
            shp_file = connection_string
            prj_file = os.path.join(os.path.dirname(shp_file),
                                    os.path.splitext(os.path.basename(shp_file))[0]+'.prj')

            feature_layer.SyncToDisk()
            feature_store.SyncToDisk()
            feature_layer = None
            feature_store = None

            if spatial_ref is not None:
                with open(prj_file, 'w') as file:
                    file.write(spatial_ref.ExportToWkt())

            feature_store = driver.CreateDataSource(os.path.dirname(shp_file))
            layer_name = GdalUtils.get_layer_name(shp_file)
            feature_layer = feature_store.GetLayerByName(layer_name)

        return OgrFeatureLayer(feature_store, feature_layer)

    def get_schema_def(self) -> SchemaDef:
        """
        Returns the schema definition of this FeatureLayer.
        """
        feature_layer = self._layer
        spatial_ref = feature_layer.GetSpatialRef()
        table_def = feature_layer.schema

        if spatial_ref:
            srid = GdalUtils.get_spatial_srid(spatial_ref)
            crs = CRS.from_epsg(srid) if srid else CRS.from_wkt(spatial_ref.ExportToWkt())
        else:
            srid = 0
            crs = None

        envelope = feature_layer.GetExtent()
        envelope = [envelope[0], envelope[2], envelope[1], envelope[3]]

        fields_def = [
            FieldDef(name=fd.GetName(), data_type=fd.GetType(),
                     precision=fd.GetPrecision(), width=fd.GetWidth(),
                     is_nullable=True if fd.IsNullable() else False, default_value=fd.GetDefault(),
                     typeName=fd.GetTypeName())

            for fd in table_def
        ]
        return SchemaDef(type='FeatureLayer',
                         name=feature_layer.GetName(),
                         srid=srid,
                         crs=crs,
                         geometryType=feature_layer.GetGeomType(),
                         envelope=envelope,
                         fields=fields_def)
