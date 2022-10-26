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

from geodataflow.pipeline.basictypes import AbstractFilter


class TablePack(AbstractFilter):
    """
    The Filter packs input Features into a GeoPandas DataFrame.
    """
    def __init__(self):
        AbstractFilter.__init__(self)

    def alias(self) -> str:
        """
        Returns the Human alias-name of this Module.
        """
        return 'Pack'

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Packs input Features into a GeoPandas DataFrame.'

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'Table'

    def run(self, feature_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        schema_def = self.pipeline_args.schema_def

        cols = ['geometry'] + [f.name for f in schema_def.fields]
        rows = []

        # Collect input Features for GeoPandas.
        for feature in feature_store:
            row = {'geometry': feature.geometry}
            row.update(feature.properties)
            rows.append(row)

        from geopandas import GeoDataFrame
        temp_df = GeoDataFrame(rows, crs=schema_def.crs, columns=cols)
        yield temp_df
