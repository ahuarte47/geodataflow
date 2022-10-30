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
from geodataflow.core.processingargs import ProcessingUtils
from geodataflow.geoext.relationships import SpatialRelationships
from geodataflow.pipeline.basictypes import AbstractFilter
from geodataflow.pipeline.filters.InputParam import InputParam


class SpatialRelation(AbstractFilter):
    """
    The Filter returns input Features that match a Spatial Relationship with one or more other Geometries.
    """
    def __init__(self):
        AbstractFilter.__init__(self)
        self.relationship = SpatialRelationships.Intersects
        self.otherGeometries = ''

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Returns input Features that match a Spatial Relationship with one or more other Geometries.'

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'Geometry'

    def params(self) -> Dict:
        """
        Returns the declaration of parameters supported by this Module.
        """
        temp_dict = ProcessingUtils.object_as_dict(SpatialRelationships)

        return {
            'relationship': {
                'description': "Spatial Relationship to validate, 'Intersects' by default.",
                'dataType': 'int',
                'default': SpatialRelationships.Intersects,
                'options': [v for _, v in temp_dict.items()],
                'labels': [k for k, _ in temp_dict.items()]
            },
            'otherGeometries': {
                'description': 'Collection of Geometries with which input Features should validate a Spatial Relationship.',
                'dataType': 'input'
            }
        }

    def run(self, feature_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        relationship = ProcessingUtils.cast_enum(self.relationship, SpatialRelationships)
        others = [
            obj.geometry for obj in InputParam.enumerate_inputs(self.otherGeometries, self.pipeline_args)
        ]

        # Set names of implemented Spatial Relationsips between geometries.
        rel_names = {
            SpatialRelationships.Equals: 'equals',
            SpatialRelationships.Disjoint: 'disjoint',
            SpatialRelationships.Intersects: 'intersects',
            SpatialRelationships.Touches: 'touches',
            SpatialRelationships.Crosses: 'crosses',
            SpatialRelationships.Within: 'within',
            SpatialRelationships.Contains: 'contains',
            SpatialRelationships.Overlaps: 'ovelaps'
        }
        rel_name = rel_names.get(relationship)
        if not rel_name:
            raise Exception('The Relationship "{}" is not supported!'.format(relationship))

        # Perform spatial relation between Geometries.
        for feature in feature_store:
            geometry = feature.geometry

            for other in others:
                if bool(geometry.impl[rel_name](geometry, other)):
                    yield feature
                    break

        pass
