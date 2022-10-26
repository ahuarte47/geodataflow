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
        self.borderSizeX = 0
        self.borderSizeY = 0
        self.srid = 0
        self.geometry = None

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
            'borderSizeX': {
                'description':
                    'Size of border to remove in X-direction (Pixels). ' +
                    'Mutually exclusive with "geometry" param.',
                'dataType': 'int',
                'default': 0
            },
            'borderSizeY': {
                'description':
                    'Size of border to remove in Y-direction (Pixels). ' +
                    'Mutually exclusive with "geometry" param.',
                'dataType': 'int',
                'default': 0
            },
            'geometry': {
                'description': 'Clipping Geometry, Formats WKT or JSON are accepted.',
                'dataType': 'geometry'
            },
            'srid': {
                'description': 'SRID of clipping Geometry (Optional).',
                'dataType': 'int',
                'default': 0
            }
        }

    def run(self, data_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        if self.borderSizeX and self.borderSizeY:
            from geodataflow.geoext.commonutils import GeometryUtils

            # Clip input Dataset removing current defined border.
            for dataset in data_store:
                info = dataset.get_metadata()
                envelope = info.get('envelope')
                pixel_size_x = info.get('pixelSizeX')
                pixel_size_y = info.get('pixelSizeY')

                envelope = [
                    envelope[0] + self.borderSizeX * pixel_size_x,
                    envelope[1] + self.borderSizeY * pixel_size_y,
                    envelope[2] - self.borderSizeX * pixel_size_x,
                    envelope[3] - self.borderSizeY * pixel_size_y
                ]
                clipping_geom = GeometryUtils.create_geometry_from_bbox(*envelope)
                setattr(clipping_geom, 'srid', info.get('srid'))

                new_dataset = dataset.warp(output_crs=None, output_geom=clipping_geom)
                dataset.recycle()
                yield new_dataset

        elif self.geometry:
            from shapely.wkt import loads as shapely_wkt_loads
            from shapely.geometry import shape as shapely_shape
            from geodataflow.geoext.commonutils import GeometryUtils

            schema_def = self.pipeline_args.schema_def

            # Build clipping Geometry.
            clipping_geom = shapely_wkt_loads(self.geometry) \
                if isinstance(self.geometry, str) else shapely_shape(self.geometry)

            if self.srid:
                source_crs = GeometryUtils.get_spatial_crs(self.srid)
                target_crs = GeometryUtils.get_spatial_crs(schema_def.srid)
                transform_fn = GeometryUtils.create_transform_function(source_crs, target_crs)
                clipping_geom = transform_fn(clipping_geom)
            else:
                setattr(clipping_geom, 'srid', schema_def.srid)

            for dataset in data_store:
                new_dataset = dataset.warp(output_crs=None, output_geom=clipping_geom)
                dataset.recycle()
                yield new_dataset
        else:
            for dataset in data_store:
                yield dataset

        pass
