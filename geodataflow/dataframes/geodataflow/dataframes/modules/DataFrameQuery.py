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

from typing import Dict
from geodataflow.pipeline.basictypes import AbstractFilter
from geodataflow.dataframes.geopandasmodule import GeoPandasMixinModule


class FeatureQuery(AbstractFilter, GeoPandasMixinModule):
    """
    The Filter queries the columns of input Features with a boolean expression.
    """
    def __init__(self):
        AbstractFilter.__init__(self)
        self.expression = ''

    def alias(self) -> str:
        """
        Returns the Human alias-name of this Module.
        """
        return 'Query'

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Queries the columns of input Features with a boolean expression.'

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
            'expression': {
                'description':
                    'The query string to evaluate. You can refer to variables in the environment ' +
                    'by prefixing them with an ‘@’ character like @a + @b.',
                'dataType': 'filter'
            }
        }

    def run(self, data_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        if self.expression:
            for data_frame in self.pack(data_store):
                yield data_frame.query(expr=self.expression, inplace=False)
        else:
            for data_frame in self.pack(data_store):
                yield data_frame

        pass