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
from typing import Dict

from geodataflow.core.capabilities import StoreCapabilities
from geodataflow.pipeline.basictypes import AbstractWriter


class FeatureWriter(AbstractWriter):
    """
    Writes Features with Geometries to a Geospatial DataStore using OGR providers.
    """
    def __init__(self):
        AbstractWriter.__init__(self)
        self._featureStore = None
        self.connectionString = ''
        self.formatOptions = []

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Writes Features with Geometries to a Geospatial DataStore using OGR providers.'

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'Output'

    def params(self) -> Dict:
        """
        Returns the declaration of parameters supported by this Module.
        """
        return {
            'connectionString': {
                'description':
                    "Connection string of the FeatureStore ('.geojson', '.gpkg', '.shp.zip' and '.csv' are supported).",
                'dataType': 'string',
                'default': 'output.gpkg',
                'extensions': ['.geojson', '.gpkg', '.shp.zip', '.csv']
            },
            'formatOptions': {
                'description': 'OGR format options of output Feature Layer (Optional).',
                'dataType': 'string'
            }
        }

    def test_capability(self, connection_string: str, capability: StoreCapabilities) -> bool:
        """
        Returns this Module supports the specified ConnectionString and named StoreCapability.
        """
        from geodataflow.geoext.commonutils import GdalUtils
        return GdalUtils.test_ogr_capability(connection_string, capability)

    def starting_run(self, schema_def, pipeline, processing_args):
        """
        Starting a new Workflow on Geospatial data.
        """
        from geodataflow.geoext.featurestore import OgrFeatureStore
        self._featureStore = OgrFeatureStore()

        format_options = self.formatOptions or []
        format_options = format_options.split(' ') if isinstance(format_options, str) else format_options

        # Create the FeatureStore.
        schema_def = self._featureStore.create(self.connectionString, schema_def, format_options)
        return schema_def

    def run(self, feature_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        if self._featureStore:
            feature_count = 0

            # Group n features per transaction (default 20000).
            # Increase the value for better performance when writing into DBMS drivers that have transaction
            # support.
            # n can be set to unlimited to load the data into a single transaction.
            # https://github.com/OSGeo/gdal/blob/release/3.2/gdal/swig/python/samples/ogr2ogr.py#L1540
            # https://gdal.org/programs/ogr2ogr.html#cmdoption-ogr2ogr-gt
            cache_size = self.cacheSize if hasattr(self, 'cacheSize') else 20000

            for feature in self._featureStore.write_features(features=feature_store, cache_size=cache_size):
                feature_count += 1
                yield feature

            logging.info('{:,} Features saved to "{}".'.format(feature_count, self.connectionString))
            return

        raise Exception('FeatureStore is not open!')

    def finished_run(self, pipeline, processing_args):
        """
        Finishing a Workflow on Geospatial data.
        """
        self._featureStore = None
        return True
