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

from geodataflow.core.processing import ProcessingUtils
from geodataflow.core.relationships import SpatialRelationships
from geodataflow.spatial.modules.GeometrySpatialRelation import SpatialRelation as OSGeoSpatialRelation
from geodataflow.dataframes.geopandasmodule import GeoPandasMixinModule


class SpatialRelation(OSGeoSpatialRelation, GeoPandasMixinModule):
    """
    The Filter returns input Features that match a Spatial Relationship with one or more other Geometries.
    """
    def __init__(self):
        OSGeoSpatialRelation.__init__(self)

    def run(self, data_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        relationship = ProcessingUtils.cast_enum(self.relationship, SpatialRelationships)
        others = [
            obj.geometry for obj in self.enumerate_inputs(self.otherGeometries)
        ]

        # Set names of implemented Spatial Relationsips between geometries.
        rel_names = {
            SpatialRelationships.Equals: 'geom_equals',
            SpatialRelationships.Disjoint: 'disjoint',
            SpatialRelationships.Intersects: 'intersects',
            SpatialRelationships.Touches: 'touches',
            SpatialRelationships.Crosses: 'crosses',
            SpatialRelationships.Within: 'within',
            SpatialRelationships.Contains: 'contains',
            SpatialRelationships.Overlaps: 'overlaps'
        }
        rel_name = rel_names.get(relationship)
        if not rel_name:
            raise Exception('The Relationship "{}" is not supported!'.format(relationship))

        from geopandas.base import _binary_op

        # Perform spatial relation between Geometries.
        for data_frame in self.pack(data_store):
            geometries = data_frame.geometry
            masks = None

            for other in others:
                mask_ = _binary_op(op=rel_name, this=geometries, other=other, align=True)
                masks = mask_ if masks is None else masks | mask_

            if masks is not None:
                data_frame = data_frame.loc[masks]

            yield data_frame

        pass
