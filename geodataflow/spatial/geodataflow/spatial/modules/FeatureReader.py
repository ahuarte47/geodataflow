# -*- coding: utf-8 -*-
"""
===============================================================================

   GeodataFlow:
   Geoprocessing framework for geographical & Earth Observation (EO) data.

   Copyright (c) 2022-2023, Alvaro Huarte. All rights reserved.

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
from geodataflow.pipeline.basictypes import AbstractReader


class FeatureReader(AbstractReader):
    """
    Reads Features with Geometries from a Geospatial DataSource using OGR providers.
    """
    def __init__(self):
        AbstractReader.__init__(self)
        self._featureStore = None
        self.connectionString = ''
        self.where = ''
        self.spatialFilter = ''
        self.countLimit = -1

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Reads Features with Geometries from a Geospatial DataSource using OGR providers.'

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'Input'

    def params(self) -> Dict:
        """
        Returns the declaration of parameters supported by this Module.
        """
        return {
            'connectionString': {
                'description': 'Connection string of the Feature Store.',
                'dataType': ['file', 'url', 'geojson'],
                'extensions': ['.fgb', '.geojson', '.gpkg', '.shp.zip']
            },
            'where': {
                'description': 'Attribute query string when fetching features (Optional).',
                'dataType': 'filter'
            },
            'spatialFilter': {
                'description': 'Geometry to be used as spatial filter when fetching features (Optional).',
                'dataType': 'geometry'
            },
            'countLimit': {
                'description': 'Maximum number of Features to fetch (Optional).',
                'dataType': 'int'
            }
        }

    def test_capability(self, connection_string: str, capability: StoreCapabilities) -> bool:
        """
        Returns of this Module supports the specified ConnectionString and named StoreCapability.
        """
        from geodataflow.spatial.commonutils import GdalUtils
        return GdalUtils.test_ogr_capability(connection_string, capability)

    def starting_run(self, schema_def, pipeline, processing_args):
        """
        Starting a new Workflow on Geospatial data.
        """
        from geodataflow.spatial.featurestore import OgrFeatureStore

        # Open the FeatureStore.
        self._featureStore = OgrFeatureStore()
        schema_def = self._featureStore.open(self.connectionString, 'r', self.spatialFilter, self.where)
        return schema_def

    def run(self, none_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        from geodataflow.spatial.commonutils import DataUtils
        from geodataflow.core.progress import ProgressProcessingStore

        # Show UI percentage progress?
        ui_progress = ProgressProcessingStore(processing_args)

        connection_string = list(DataUtils.enumerate_single_connection_string(self.connectionString))[0]
        is_geojson = DataUtils.represents_json_feature_collection(connection_string)
        if is_geojson:
            connection_string = 'GeoJSON FeatureCollection'

        logging.info('Reading Features from "{}"...'.format(connection_string))

        feature_layers = self._featureStore.layers()
        feature_count = 0
        count_limit = self.countLimit if self.countLimit is not None else -1

        # Enumerate Features...
        for feature in self._featureStore.features():
            #
            if ui_progress.enabled:
                if feature_count == 0:
                    total_count = 0
                    for feature_layer in feature_layers:
                        total_count += feature_layer.layer().GetFeatureCount()

                    ui_progress.initialize(total_count)
                else:
                    ui_progress.update()

            if count_limit > feature_count:
                logging.warning(
                    'Early processing break! The "countLimit" flag was specified (Value={}).'
                    .format(self.countLimit))

                break

            # DEBUG: if feature_count == 100: break
            feature_count += 1
            yield feature

        if ui_progress.enabled and ui_progress.initialized():
            logging.info('')

        logging.info('{:,} Features read from "{}".'.format(feature_count, connection_string))
        pass

    def finished_run(self, pipeline, processing_args):
        """
        Finishing a Workflow on Geospatial data.
        """
        self._featureStore = None
        return True
