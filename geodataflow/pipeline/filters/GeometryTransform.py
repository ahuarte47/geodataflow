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

from typing import Dict
from geodataflow.pipeline.basictypes import AbstractFilter


class GeometryTransform(AbstractFilter):
    """
    The Filter transforms input Geometries between two Spatial Reference Systems (CRS).
    """
    def __init__(self):
        AbstractFilter.__init__(self)
        self.sourceCrs = None
        self.targetCrs = None

    def alias(self) -> str:
        """
        Returns the Human alias-name of this Module.
        """
        return 'Transform'

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Transforms input Geometries or Rasters between two Spatial Reference Systems (CRS).'

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'Geometry'

    def params(self) -> Dict:
        """
        Returns the declaration of parameters supported by this Module.
        """
        return {
            'sourceCrs': {
                'description':
                    'Source Spatial Reference System (CRS), SRID, WKT, PROJ formats are supported. ' +
                    'It uses input CRS when this param is not specified.',
                'dataType': 'crs',
                'placeHolder': 'EPSG:XXXX or SRID...'
            },
            'targetCrs': {
                'description':
                    'Output Spatial Reference System (CRS), SRID, WKT, PROJ formats are supported.',
                'dataType': 'crs',
                'placeHolder': 'EPSG:XXXX or SRID...'
            }
        }

    def starting_run(self, schema_def, pipeline, processing_args):
        """
        Starting a new Workflow on Geospatial data.
        """
        from geodataflow.geoext.commonutils import GeometryUtils

        if self.targetCrs:
            source_crs = GeometryUtils.get_spatial_crs(self.sourceCrs if self.sourceCrs else schema_def.crs)
            target_crs = GeometryUtils.get_spatial_crs(self.targetCrs)

            schema_def = schema_def.clone()
            schema_def.input_srid = source_crs.to_epsg()
            schema_def.input_crs = source_crs
            schema_def.srid = target_crs.to_epsg()
            schema_def.crs = target_crs

            if schema_def.envelope:
                transform_fn = GeometryUtils.create_transform_function(source_crs, target_crs)
                geometry = GeometryUtils.create_geometry_from_bbox(*schema_def.envelope)
                geometry = transform_fn(geometry)
                schema_def.envelope = list(geometry.bounds)
        else:
            schema_def = schema_def.clone()
            schema_def.input_srid = schema_def.crs.to_epsg()
            schema_def.input_crs = schema_def.crs

        return schema_def

    def run(self, feature_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        from geodataflow.geoext.commonutils import GeometryUtils
        from geodataflow.geoext.dataset import GdalDataset

        schema_def = self.pipeline_args.schema_def
        source_crs = GeometryUtils.get_spatial_crs(
            self.sourceCrs if self.sourceCrs else schema_def.input_srid
        )
        target_crs = GeometryUtils.get_spatial_crs(
            self.targetCrs
        )

        if source_crs and target_crs and source_crs.to_epsg() != target_crs.to_epsg():
            transform_fn = GeometryUtils.create_transform_function(source_crs, target_crs)

            for feature in feature_store:
                if isinstance(feature, GdalDataset):
                    dataset = feature.warp(output_crs=target_crs, output_geom=None)
                    yield dataset
                else:
                    feature.geometry = transform_fn(feature.geometry)
                    yield feature
            #
        else:
            for feature in feature_store:
                yield feature

        pass
