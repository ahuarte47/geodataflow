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


class RasterCalc(AbstractFilter):
    """
    The Filter performs raster calc operations with numpy syntax to input Rasters.
    """
    def __init__(self):
        AbstractFilter.__init__(self)
        self.bands = []
        self.expression = ''
        self.noData = -9999.0

    def alias(self) -> str:
        """
        Returns the Human alias-name of this Module.
        """
        return 'Calc'

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Performs raster calc algebraical operations to input Rasters.'

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
            'bands': {
                'description': 'List of Band names defined in Expression, or a string separated by commas.',
                'dataType': 'string',
                'default': '',
                'placeHolder': 'B04,B03,B02,B08'
            },
            'expression': {
                'description': 'Raster calculator expression with numpy syntax, e.g. (B08–B04)/(B08+B04).',
                'dataType': 'calc',
                'default': '',
                'placeHolder': '(B08 - B04) / (B08 + B04)'
            },
            'noData': {
                'description': 'NoData value of output Dataset.',
                'dataType': 'float',
                'default': -9999.0
            }
        }

    def run(self, data_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        from geodataflow.geoext.dataset import GdalDataset

        bands = self.bands.replace(' ', '').split(',') if isinstance(self.bands, str) else self.bands
        no_data = float(self.noData)

        for dataset in data_store:
            if not isinstance(dataset, GdalDataset):
                raise Exception('RasterCalc only accepts Datasets as input data.')

            new_dataset = dataset.calc(band_names=bands, band_expression=self.expression, no_data=no_data)
            dataset.recycle()
            yield new_dataset

        pass
