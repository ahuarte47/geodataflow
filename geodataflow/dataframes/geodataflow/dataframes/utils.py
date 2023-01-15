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

from typing import Iterable, Union

from geodataflow.core.schemadef import SchemaDef
from geodataflow.spatial.commonutils import GeometryUtils
from geopandas.geodataframe import GeoDataFrame


class TableUtils:
    """
    Provides generic GeoPandas utility functions.
    """
    @staticmethod
    def from_features(schema_def: SchemaDef, features: Iterable[object]) -> GeoDataFrame:
        """
        Returns a GeoPandas DataFrame from the spcified Feature Collection.
        """
        cols = ['geometry'] + [f.name for f in schema_def.fields]
        rows = []

        # Collect input Features for GeoPandas.
        for feature in features:
            row = {'geometry': feature.geometry}
            row.update(feature.properties)
            rows.append(row)

        temp_df = GeoDataFrame(rows, crs=schema_def.crs, columns=cols)
        return temp_df

    @staticmethod
    def to_features(data_frame: GeoDataFrame) -> Iterable[object]:
        """
        Returns a Feature Collection from the specified GeoPandas DataFrame.
        """
        srid = GeometryUtils.get_srid(data_frame.crs)
        cols = [c for c in data_frame.columns if c != 'geometry']

        for index, row in data_frame.iterrows():
            geometry = row['geometry']
            geometry = geometry.with_srid(srid)

            feature = type('Feature', (object,), {
                'type': 'Feature',
                'fid': index,
                'properties': {c: row[c] for c in cols},
                'geometry': geometry
            })
            yield feature

        pass

    @staticmethod
    def unpack(data_store: Union[GeoDataFrame, Iterable[object]]) -> Iterable[object]:
        """
        Unpack specified Store into a collection of Features simples.
        """
        for row in data_store:
            if isinstance(row, GeoDataFrame):
                for feature in TableUtils.to_features(row):
                    yield feature
            else:
                yield row

        pass


GeoDataFrame.__iter__ = TableUtils.to_features
