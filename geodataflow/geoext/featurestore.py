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

import logging
import json
from typing import Iterable, List, Union

from shapely.wkb import loads as shapely_wkb_loads, dumps as shapely_wkb_dumps
from osgeo import ogr
from geodataflow.core.capabilities import StoreCapabilities
from geodataflow.core.schemadef import SchemaDef
from geodataflow.geoext.commonutils import DataUtils, GdalUtils
from geodataflow.geoext.gdalenv import GdalEnv
from geodataflow.geoext.featurelayer import OgrFeatureLayer
ogr.UseExceptions()


class OgrFeatureStore:
    """
    Store that reads & writes Features with Geometries in one OGR FeatureSource.
    """
    def __init__(self):
        self._layers: List[OgrFeatureLayer] = list()

    def __enter__(self):
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        self.close()

    def __del__(self):
        """
        Releases resources of this OGR FeatureStore.
        """
        self.close()

    def open(self,
             connection_string: Union[str, Iterable[str]],
             access_mode: str = 'r',
             spatial_filter: str = '',
             attribute_filter: str = '') -> SchemaDef:
        """
        Opens one OGR FeatureStore for the specified ConnectionString.
        """
        mode = 0 if access_mode == 'r' else 1

        for item_string in DataUtils.enumerate_single_connection_string(connection_string):
            is_geojson = \
                DataUtils.represents_json_feature_collection(item_string)

            if is_geojson:
                from uuid import uuid4
                feature_class = 'FeatureCollection-{}'.format(uuid4().hex)

                if isinstance(item_string, dict):
                    item_string = json.dumps(item_string)

                item_string = item_string.replace('\'', '"')  # or OGR library fails!
                mmap_name = '/vsimem/{}.json'.format(feature_class)

                gdal_env = GdalEnv.default()
                gdal = gdal_env.gdal()

                logging.debug('Opening "GeoJSON" from memory string...')

                gdal.FileFromMemBuffer(mmap_name, item_string)
                store = ogr.Open(mmap_name, mode)  # 0 means read-only. 1 means writeable.
                layer = store.GetLayerByName(feature_class)
                gdal.Unlink(mmap_name)

                logging.debug('Ok!')
            else:
                feature_class = DataUtils.get_layer_name(item_string)
                connect_store = GdalUtils.get_ogr_connection_string(item_string)

                logging.debug('Opening "{}"...'.format(item_string))

                store = ogr.Open(connect_store, mode)  # 0 means read-only. 1 means writeable.
                layer = store.GetLayerByName(feature_class)
                if layer is None:
                    layer = store.GetLayerByIndex(0)

                logging.debug('Ok!')

            do_spatial_filter = spatial_filter is not None and len(spatial_filter) > 0

            # Set the spatial and/or alphanumeric filters.
            if attribute_filter:
                layer.SetAttributeFilter(attribute_filter)

            if do_spatial_filter:
                for geom_key in ['RECT(', 'EXTENT(', 'BOUNDS(', 'BBOX(', 'ENV(', 'ENVELOPE(']:
                    if spatial_filter.startswith(geom_key):
                        bbox = [float(val.strip()) for val in spatial_filter[len(geom_key):-1].split(',')]
                        layer.SetSpatialFilterRect(bbox[0], bbox[1], bbox[2], bbox[3])
                        do_spatial_filter = False
                        break
            if do_spatial_filter:
                layer.SetSpatialFilter(spatial_filter)

            self._layers.append(OgrFeatureLayer(store, layer))
        #
        return self._layers[0].get_schema_def()

    def create(self, connection_string: str, schema_def: SchemaDef, format_options: List[str] = []) -> SchemaDef:
        """
        Creates a new OGR FeatureStore for the specified ConnectionString and SchemaDef.
        """
        for item_string in DataUtils.enumerate_single_connection_string(connection_string):
            #
            if not GdalUtils.test_ogr_capability(item_string, StoreCapabilities.CREATE):
                raise Exception('The OGR Driver of "{}" does not support Data creation!'.format(item_string))

            layer_obj = \
                OgrFeatureLayer.create_layer(item_string, DataUtils.get_layer_name(item_string), schema_def, format_options)

            self._layers.append(layer_obj)
            break

        return self._layers[0].get_schema_def()

    def close(self) -> bool:
        """
        Releases the OGR FeatureLayer set managed by this OGR FeatureStore.
        """
        for i in range(0, len(self._layers)):
            self._layers[i] = None

        self._layers = list()
        return True

    def features(self) -> Iterable:
        """
        Enumerates the whole collection of Features managed by this OGR FeatureStore.
        """
        for feature_layer in self._layers:
            schema_def = feature_layer.get_schema_def()
            fields = schema_def.fields

            for feature in feature_layer.features():
                geometry = feature.GetGeometryRef()
                geometry = shapely_wkb_loads(bytes(geometry.ExportToWkb()))
                geometry = geometry.with_srid(schema_def.srid)

                feature = type('Feature', (object,), {
                    'type': 'Feature',
                    'fid': feature.GetFID(),
                    'properties': {
                        fields[i].name: feature.GetField(i) for i in range(feature.GetFieldCount())
                    },
                    'geometry': geometry
                })
                yield feature
            #
        pass

    def write_features(self, features: Iterable, cache_size: int = None) -> Iterable:
        """
        Write the specified collection of Features to this OGR FeatureStore.
        """
        feature_transaction_count = 0
        feature_count = 0
        feature_layer = self._layers[0]

        # Group n features per transaction (default 20000).
        # Increase the value for better performance when writing into DBMS drivers that have transaction
        # support. n can be set to unlimited to load the data into a single transaction.
        # https://github.com/OSGeo/gdal/blob/release/3.2/gdal/swig/python/samples/ogr2ogr.py#L1540
        # https://gdal.org/programs/ogr2ogr.html#cmdoption-ogr2ogr-gt
        n = int(cache_size) if cache_size is not None else 20000

        ogr_layer = feature_layer.layer()
        ogr_schema_def = ogr_layer.GetLayerDefn()
        write_geoms = ogr_schema_def.GetGeomFieldCount() > 0
        ogr_layer.StartTransaction()

        for feature in features:
            geometry = shapely_wkb_dumps(feature.geometry)
            geometry = ogr.CreateGeometryFromWkb(geometry)

            fid = feature.fid if hasattr(feature, 'fid') else feature_count
            ogr_feature = ogr.Feature(ogr_schema_def)
            if fid is not None:
                ogr_feature.SetFID(fid)

            if write_geoms:
                ogr_feature.SetGeometry(geometry)

            for k, v in feature.properties.items():
                i = ogr_feature.GetFieldIndex(k)
                if i != -1:
                    ogr_feature.SetField(i, v)

            ogr_layer.CreateFeature(ogr_feature)

            # Group n features per transaction, therefore divide full transaction in parts.
            if feature_transaction_count > n:
                ogr_layer.CommitTransaction()
                ogr_layer.StartTransaction()
                feature_transaction_count = 0

            feature_transaction_count += 1
            feature_count += 1
            yield feature

        ogr_layer.CommitTransaction()

    def layers(self) -> Iterable[OgrFeatureLayer]:
        """
        Returns the OGR FeatureLayer set managed by this OGR FeatureStore.
        """
        return self._layers
