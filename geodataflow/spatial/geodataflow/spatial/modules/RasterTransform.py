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

from typing import Dict
from geodataflow.spatial.modules.GeometryTransform import GeometryTransform


class RasterTransform(GeometryTransform):
    """
    The Filter transforms input Rasters between two Spatial Reference Systems (CRS).
    """
    def __init__(self):
        GeometryTransform.__init__(self)
        self.resampleAlg = 1  # Bilinear

    def alias(self) -> str:
        """
        Returns the Human alias-name of this Module.
        """
        return 'Transform'

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Transforms input Rasters between two Spatial Reference Systems (CRS).'

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'Raster'

    def params(self) -> Dict:
        """
        Returns the declaration of parameters supported by this Module.
        """
        the_params = GeometryTransform.params(self)
        the_params['resampleAlg'] = {
            'description': 'Resampling strategy.',
            'dataType': 'int',
            'default': 1,
            'options': [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12],
            'labels': [
                'NearestNeighbour', 'Bilinear', 'Cubic', 'CubicSpline', 'Lanczos',
                'Average', 'Mode', 'Max', 'Min', 'Med', 'Q1', 'Q3'
            ]
        }
        return the_params

    def run(self, data_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        from geodataflow.spatial.commonutils import GeometryUtils

        schema_def = self.pipeline_args.schema_def
        source_crs = GeometryUtils.get_spatial_crs(
            self.sourceCrs if self.sourceCrs else schema_def.input_srid
        )
        target_crs = GeometryUtils.get_spatial_crs(
            self.targetCrs
        )

        if isinstance(self.resampleAlg, str):
            _RESAMPLE_ALG_NAMES_MAP = {
                'NearestNeighbour': 0,
                'Bilinear': 1,
                'Cubic': 2,
                'CubicSpline': 3,
                'Lanczos': 4, 'Average': 5, 'Mode': 6, 'Max': 8, 'Min': 9, 'Med': 10, 'Q1': 11, 'Q3': 12
            }
            resample_alg = _RESAMPLE_ALG_NAMES_MAP.get(self.resampleAlg, 1)
        else:
            resample_alg = self.resampleAlg

        if source_crs and target_crs and source_crs.to_epsg() != target_crs.to_epsg():
            for dataset in data_store:
                dataset = dataset.warp(output_crs=target_crs, output_geom=None, resample_arg=resample_alg)
                yield dataset
        else:
            for dataset in data_store:
                yield dataset

        pass
