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


class RasterReader(AbstractReader):
    """
    Reads Datasets from a Geospatial RasterSource using GDAL providers.
    """
    def __init__(self):
        AbstractReader.__init__(self)
        self._rasterStore = None
        self.connectionString = ''
        self.countLimit = -1

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Reads Datasets from a Geospatial RasterSource using GDAL providers.'

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
                'description': 'Connection string of the Raster Store.',
                'dataType': ['file', 'url'],
                'extensions': ['.tiff', '.tif', '.ecw', '.jp2']
            },
            'countLimit': {
                'description': 'Maximum number of Datasets to fetch (Optional).',
                'dataType': 'int'
            }
        }

    def test_capability(self, connection_string: str, capability: StoreCapabilities) -> bool:
        """
        Returns this Module supports the specified ConnectionString and named StoreCapability.
        """
        from geodataflow.spatial.commonutils import GdalUtils
        return GdalUtils.test_gdal_capability(connection_string, capability)

    def starting_run(self, schema_def, pipeline, processing_args):
        """
        Starting a new Workflow on Geospatial data.
        """
        from geodataflow.spatial.rasterstore import GdalRasterStore

        # Open the RasterStore.
        self._rasterStore = GdalRasterStore()
        schema_def = self._rasterStore.open(self.connectionString, self.countLimit)
        return schema_def

    def run(self, none_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        from geodataflow.core.progress import ProgressProcessingStore

        # Show UI percentage progress?
        ui_progress = ProgressProcessingStore(processing_args)

        datasets = self._rasterStore.datasets()
        dataset_count = 0

        # Enumerate Datasets...
        for dataset in datasets:
            #
            if ui_progress.enabled:
                if dataset_count == 0:
                    ui_progress.initialize(len(datasets))
                else:
                    ui_progress.update()

            # DEBUG: if feature_count == 100: break
            dataset_count += 1
            yield dataset

        if ui_progress.enabled and ui_progress.initialized():
            logging.info('')

        logging.info('{:,} Datasets read from "{}".'.format(dataset_count, self.connectionString))
        pass

    def finished_run(self, pipeline, processing_args):
        """
        Finishing a Workflow on Geospatial data.
        """
        self._rasterStore = None
        return True
