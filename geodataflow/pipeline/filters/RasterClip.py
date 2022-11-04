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


class RasterClip(AbstractFilter):
    """
    The Filter clips input Rasters by a Geometry.
    """
    def __init__(self):
        AbstractFilter.__init__(self)
        self.clipGeometries = ''

    def alias(self) -> str:
        """
        Returns the Human alias-name of this Module.
        """
        return 'Clip'

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Clips input Rasters by a Geometry.'

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
            'clipGeometries': {
                'description': 'Collection of Geometries that will clip input Features.',
                'dataType': 'input'
            }
        }

    def run(self, data_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        clipping_geoms = [
            obj.geometry for obj in self.enumerate_inputs(self.clipGeometries)
        ]

        if clipping_geoms:
            from geodataflow.geoext.commonutils import GeometryUtils

            schema_def = self.pipeline_args.schema_def
            if schema_def.srid:
                schema_crs = GeometryUtils.get_spatial_crs(schema_def.srid)

                for g_index, g in enumerate(clipping_geoms):
                    if g.get_srid():
                        clipping_crs = GeometryUtils.get_spatial_crs(g.get_srid())
                        transform_fn = GeometryUtils.create_transform_function(clipping_crs, schema_crs)
                        clipping_geoms[g_index] = transform_fn(g)

            for dataset in data_store:
                for g in clipping_geoms:
                    if g.intersects(dataset.geometry):
                        new_dataset = dataset.warp(output_crs=None, output_geom=g)
                        dataset.recycle()
                        dataset = new_dataset

                yield dataset
        else:
            for dataset in data_store:
                yield dataset

        pass
