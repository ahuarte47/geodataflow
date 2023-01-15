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
from typing import Iterable, List, Union

from geodataflow.core.capabilities import StoreCapabilities
from geodataflow.core.schemadef import SchemaDef, GeometryType
from geodataflow.spatial.commonutils import DataUtils, GdalUtils, GeometryUtils
from geodataflow.spatial.dataset import GdalDataset, DATASET_DEFAULT_SCHEMA_DEF
from geodataflow.spatial.gdalenv import GdalEnv


class GdalRasterStore:
    """
    Store that reads & writes Datasets in a GDAL RasterStore.
    """
    def __init__(self):
        self._datasets: List[GdalDataset] = list()

    def __enter__(self):
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        self.close()

    def __del__(self):
        """
        Releases resources of this GDAL RasterStore.
        """
        self.close()

    def open(self, connection_string: Union[str, Iterable[str]], count_limit: int = None) -> SchemaDef:
        """
        Opens one GDAL RasterStore for the specified ConnectionString.
        """
        dataset_count = 0
        count_limit = int(count_limit) if count_limit is not None else -1
        schema_def = None

        gdal_env = GdalEnv.default()
        gdal = gdal_env.gdal()

        for item_string in DataUtils.enumerate_single_connection_string(connection_string):
            #
            if not GdalUtils.test_gdal_capability(item_string, StoreCapabilities.READ):
                raise Exception(
                    'The GDAL Driver of "{}" does not support the Access mode "READ".'.format(item_string))

            if count_limit > dataset_count:
                logging.warning(
                    'Early processing break! The "rasterCountLimit" flag was specified (Value={}).'
                    .format(count_limit))

                break

            dataset = gdal.Open(item_string, gdal.GA_ReadOnly)
            dataset = GdalDataset(dataset, gdal_env)

            if schema_def is None:
                crs = GeometryUtils.get_spatial_crs(dataset.get_spatial_srid())

                schema_def = SchemaDef(type='RasterLayer',
                                       name=DataUtils.get_layer_name(item_string),
                                       srid=crs.to_epsg(),
                                       crs=crs,
                                       geometryType=GeometryType.Polygon,
                                       envelope=dataset.get_envelope(),
                                       fields=DATASET_DEFAULT_SCHEMA_DEF.copy())

            self._datasets.append(dataset)
            dataset_count += 1

        return schema_def

    def close(self) -> bool:
        """
        Releases the OGR FeatureLayer set managed by this GDAL RasterStore.
        """
        for i in range(0, len(self._datasets)):
            self._datasets[i] = None

        self._datasets = list()
        return True

    def datasets(self) -> Iterable[GdalDataset]:
        """
        Returns the Datasets set managed by this GDAL RasterStore.
        """
        return self._datasets
