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
from geodataflow.pipeline.basictypes import AbstractFilter


class FeatureLimit(AbstractFilter):
    """
    The Filter validates that input Geometries do not be greater than a Limit.
    """
    def __init__(self):
        AbstractFilter.__init__(self)
        self.fullAreaLimit = None
        self.areaLimit = None
        self.countLimit = None

    def alias(self) -> str:
        """
        Returns the Human alias-name of this Module.
        """
        return 'Limits'

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Validates that input Geometries do not be greater than a Limit.'

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'Feature'

    def params(self) -> Dict:
        """
        Returns the declaration of parameters supported by this Module.
        """
        return {
            'fullAreaLimit': {
                'description': 'Maximum area covered by all input Geometries (Optional).',
                'dataType': 'float'
            },
            'areaLimit': {
                'description': 'Maximum area covered by each input Geometry (Optional).',
                'dataType': 'float'
            },
            'countLimit': {
                'description': 'Maximum number of input Geometries (Optional).',
                'dataType': 'int'
            }
        }

    def run(self, feature_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        schema_def = self.pipeline_args.schema_def
        crs = schema_def.crs

        # Input parameters.
        full_area_limit = self.fullAreaLimit if self.fullAreaLimit is not None else 0.0
        area_limit = self.areaLimit if self.areaLimit is not None else 0.0
        full_area = 0.0
        count_limit = self.countLimit if self.countLimit is not None else 0
        feature_count = 0

        logging.info(
            'Verifying limits of input data (Area={}, FullArea={}, Count={})...'
            .format(area_limit, full_area_limit, count_limit))

        from shapely.geometry.polygon import Polygon
        from shapely.geometry.multipolygon import MultiPolygon

        # Do we need to transform input Geometries to ellipsoid WGS84 to calculate Areas in m2?
        if crs and not crs.is_projected:
            import pyproj as pj
            from geodataflow.geoext.commonutils import GeometryUtils

            ellipsoid_ob = pj.Geod(ellps='WGS84')
            transform_fn = GeometryUtils.create_transform_function(crs, pj.CRS.from_epsg(4326))

            for feature in feature_store:
                geometry = feature.geometry

                if count_limit and feature_count >= count_limit:
                    raise Exception(
                        'The number of input Features is greater than maximum allowed ({}).'
                        .format(count_limit))

                if isinstance(geometry, (Polygon, MultiPolygon)):
                    geometry = transform_fn(geometry)

                    area, _ = ellipsoid_ob.geometry_area_perimeter(geometry)
                    area = abs(area)
                    full_area += area

                    if area_limit and area > area_limit:
                        raise Exception(
                            'Area of input Geometry ({}) is greater than maximum allowed ({}).'
                            .format(area_limit, area))

                    if full_area_limit and full_area > full_area_limit:
                        raise Exception(
                            'Area of input Layer ({}) is greater than maximum allowed ({}).'
                            .format(full_area_limit, full_area))

                feature_count += 1
                yield feature
            #
        else:
            for feature in feature_store:
                geometry = feature.geometry

                if count_limit and feature_count >= count_limit:
                    raise Exception(
                        'The number of input Features is greater than maximum allowed ({}).'
                        .format(count_limit))

                if isinstance(geometry, (Polygon, MultiPolygon)):
                    area = geometry.area
                    full_area += area

                    if area_limit and area > area_limit:
                        raise Exception(
                            'Area of input Geometry ({}) is greater than maximum allowed ({}).'
                            .format(area_limit, area))

                    if full_area_limit and full_area > full_area_limit:
                        raise Exception(
                            'Area of input Layer ({}) is greater than maximum allowed ({}).'
                            .format(full_area_limit, full_area))

                feature_count += 1
                yield feature
            #

        pass
