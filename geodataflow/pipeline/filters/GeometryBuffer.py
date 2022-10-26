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


class GeometryBuffer(AbstractFilter):
    """
    The Filter computes a buffer area around a geometry having the given width.
    """
    def __init__(self):
        AbstractFilter.__init__(self)
        self.distance = 1.0
        self.capStyle = 1
        self.joinStyle = 1

    def alias(self) -> str:
        """
        Returns the Human alias-name of this Module.
        """
        return 'Buffer'

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Computes a buffer area around a geometry having the given width.'

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
            'distance': {
                'description': 'Distance of buffer to apply to input Geometry.',
                'dataType': 'float',
                'default': 1.0
            },
            'capStyle': {
                'description': 'Caps style.',
                'dataType': 'int',
                'default': 1,
                'options': [1, 2, 3],
                'labels': ['round', 'flat', 'square']
            },
            'joinStyle': {
                'description': 'Join style.',
                'dataType': 'int',
                'default': 1,
                'options': [1, 2, 3],
                'labels': ['round', 'mitre', 'bevel']
            }
        }

    def starting_run(self, schema_def, pipeline, processing_args):
        """
        Starting a new Workflow on Geospatial data.
        """
        from geodataflow.core.schemadef import GeometryType

        schema_def = schema_def.clone()
        schema_def.geometryType = GeometryType.Polygon
        return schema_def

    def run(self, feature_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        from shapely.geometry.base import CAP_STYLE, JOIN_STYLE
        from geodataflow.core.processingargs import ProcessingUtils

        cap_style = ProcessingUtils.cast_enum(self.capStyle, CAP_STYLE)
        join_style = ProcessingUtils.cast_enum(self.joinStyle, JOIN_STYLE)

        for feature in feature_store:
            geometry = feature.geometry
            feature.geometry = geometry.buffer(
                distance=self.distance, cap_style=cap_style, join_style=join_style).with_srid(geometry)
            yield feature

        pass
