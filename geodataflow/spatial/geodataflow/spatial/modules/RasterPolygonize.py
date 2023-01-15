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
from geodataflow.pipeline.basictypes import AbstractFilter


class RasterPolygonize(AbstractFilter):
    """
    The Filter returns the Geometry containing all connected regions of nodata pixels in input Datasets.
    """
    def __init__(self):
        AbstractFilter.__init__(self)
        self.bandIndex = 0

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Returns the Geometry containing all connected regions of nodata pixels in input Datasets.'

    def alias(self) -> str:
        """
        Returns the Human alias-name of this Module.
        """
        return 'Polygonize'

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'Raster'

    def params(self) -> Dict:
        """
        Returns the declaration of parameters supported by this Module.
        """
        return {
            "bandIndex": {
                'description': 'Index of Band from which to create Geometries.',
                'dataType': 'int',
                'default': 0
            }
        }

    def starting_run(self, schema_def, pipeline, processing_args):
        """
        Starting a new Workflow on Geospatial data.
        """
        from geodataflow.core.schemadef import GeometryType

        schema_def = schema_def.clone()
        schema_def.type = 'FeatureLayer'
        schema_def.geometryType = GeometryType.Polygon
        return schema_def

    def run(self, data_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        from geodataflow.spatial.dataset import GdalDataset

        band_index = self.bandIndex
        feature_index = 0

        for dataset in data_store:
            if not isinstance(dataset, GdalDataset):
                raise Exception('RasterPolygonize only accepts Datasets as input data.')

            properties = dataset.properties.copy()
            geometry = dataset.polygonize(band_index=band_index)

            if geometry is None:
                logging.warning('Polygonize returns an empty Geometry, input Dataset is skipped.')
                continue

            feature = type('Feature', (object,), {
                'type': 'Feature',
                'fid': feature_index,
                'properties': properties,
                'geometry': geometry,
            })
            feature_index += 1
            yield feature

        pass
