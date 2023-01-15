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

from geodataflow.spatial.modules.GeometryBuffer import GeometryBuffer as OSGeoGeometryBuffer
from geodataflow.dataframes.geopandasmodule import GeoPandasMixinModule


class GeometryBuffer(OSGeoGeometryBuffer, GeoPandasMixinModule):
    """
    The Filter computes a buffer area around a geometry having the given width.
    """
    def __init__(self):
        OSGeoGeometryBuffer.__init__(self)

    def run(self, data_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        from shapely.geometry.base import CAP_STYLE, JOIN_STYLE
        from geodataflow.core.processing import ProcessingUtils

        cap_style = ProcessingUtils.cast_enum(self.capStyle, CAP_STYLE)
        join_style = ProcessingUtils.cast_enum(self.joinStyle, JOIN_STYLE)

        for data_frame in self.pack(data_store):
            geometries = data_frame.buffer(distance=self.distance, cap_style=cap_style, join_style=join_style)
            data_frame = data_frame.set_geometry(geometries, inplace=False)
            yield data_frame

        pass
