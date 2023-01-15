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

import os
import datetime
import numpy as np
from typing import Dict, Iterable
from geodataflow.pipeline.basictypes import AbstractWriter
from geodataflow.core.capabilities import StoreCapabilities
from geodataflow.core.processing import ProcessingUtils


class TimeseriesPlot(AbstractWriter):
    """
    This module plots to image Time Series of values to visualize trends
    in counts or numerical values over time.
    """
    def __init__(self):
        AbstractWriter.__init__(self)
        self.connectionString = ''
        # Graph properties.
        self.title = 'Time series Plot'
        self.xLabel = 'Date'
        self.yLabel = 'Value'
        self.figureXSize = 800
        self.figureYSize = 600
        # Time Series properties.
        self.label = ''
        self.expressionValue = 'float(mean)'
        self.attributeDate = 'productDate'
        self.dateFormatter = '%Y-%m-%d'
        self.dateRange = 10

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'It plots to image Time Series of values to visualize trends in counts or numerical values over time.'

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'Output'

    def params(self) -> Dict:
        """
        Returns the declaration of parameters supported by this Module.
        """
        return {
            'connectionString': {
                'description': 'Connection string or Filename of the image to output.',
                'dataType': 'string',
                'default': 'plot.png',
                'extensions': ['.png', '.jpg']
            },
            'title': {
                'description': 'Title of the Graph.',
                'dataType': 'string',
                'default': 'Time series Plot'
            },
            'xLabel': {
                'description': 'Label for the x-axis.',
                'dataType': 'string',
                'default': 'Date'
            },
            'yLabel': {
                'description': 'Label for the y-axis.',
                'dataType': 'string',
                'default': 'Value'
            },
            'figureXSize': {
                'description': 'The number of pixels of the image in the X direction.',
                'dataType': 'int',
                'default': 800
            },
            'figureYSize': {
                'description': 'The number of pixels of the image in the Y direction.',
                'dataType': 'int',
                'default': 600
            },
            'expressionValue': {
                'description':
                    'Algebraic expression to calculate the values, or list of them separated by commas.',
                'dataType': 'calc'
            },
            'attributeDate': {
                'description': 'Attribute containing the Date in format "%Y-%m-%d".',
                'dataType': 'string'
            },
            'label': {
                'description':
                    'Optional label, or list of them separated by commas, for the Legend. None by default.',
                'dataType': 'string'
            },
            'dateFormatter': {
                'description': 'Format pattern of Dates for the x-axis.',
                'dataType': 'string',
                'default': '%Y-%m-%d'
            },
            'dateRange': {
                'description': 'The interval between each iteration for the x-axis ticker.',
                'dataType': 'int',
                'default': 10
            }
        }

    def test_capability(self, connection_string: str, capability: StoreCapabilities) -> bool:
        """
        Returns if this Module supports the specified ConnectionString and named StoreCapability.
        """
        file_name, file_ext = os.path.splitext(connection_string)
        return file_name and file_ext and file_ext in ['.png', '.jpg', '.jpeg']

    def starting_run(self, schema_def, pipeline, processing_args):
        """
        Starting a new Workflow on Geospatial data.
        """
        from geodataflow.spatial.commonutils import DataUtils

        for item_string in DataUtils.enumerate_single_connection_string(self.connectionString):
            #
            if not self.test_capability(item_string, StoreCapabilities.CREATE):
                raise Exception('Theimage  format "{}" is not supported!'.format(item_string))

            from geodataflow.core.schemadef import SchemaDef, GeometryType
            from geodataflow.spatial.dataset import DATASET_DEFAULT_SCHEMA_DEF

            schema_def = SchemaDef(type='RasterLayer',
                                   name=DataUtils.get_layer_name(item_string),
                                   srid=0,
                                   crs=None,
                                   geometryType=GeometryType.Polygon,
                                   envelope=[0, 0, self.figureXSize, self.figureYSize],
                                   fields=DATASET_DEFAULT_SCHEMA_DEF.copy())

            return schema_def

        return None

    def run(self, feature_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        timeseries = []

        expressions = \
            self.expressionValue.split(',') if isinstance(self.expressionValue, str) else self.expressionValue
        labels = \
            self.label.split(',') if isinstance(self.label, str) and self.label else self.label

        if isinstance(expressions, list) and isinstance(labels, list) and len(expressions) != len(labels):
            raise Exception(
                'TimeseriesPlot does not support "expressionValue" and "label" settings with different size.')

        # Extract stream of Dates and array of Values.
        for feature in feature_store:
            date_ = feature.properties[self.attributeDate] if self.attributeDate else None
            values = [
                ProcessingUtils.eval_function(xpr, feature.properties, False)
                for xpr in expressions
            ]
            timeseries.append({'date': date_, 'values': values})

        # Refactoring stream of Date/Values to numpy arrays.
        timeseries = TimeseriesPlot._timeseries_np(timeseries)

        # Draw plot!
        if len(timeseries) > 0:
            import matplotlib
            import matplotlib.dates as m_dates
            matplotlib.use('agg')
            import matplotlib.pyplot as plt

            from geodataflow.spatial.gdalenv import GdalEnv
            from geodataflow.spatial.dataset import GdalDataset

            file_ext = os.path.splitext(self.connectionString)[1]
            relative_date = '%Y' not in self.dateFormatter
            has_labels = False

            # Main attributes of Plot.
            inv_dpi_ = 0.01
            fig, ax_ = plt.subplots(figsize=(inv_dpi_*self.figureXSize, inv_dpi_*self.figureYSize))
            if self.title:
                ax_.set_title(self.title)
            if self.xLabel:
                ax_.set_xlabel(self.xLabel)
            if self.yLabel:
                ax_.set_ylabel(self.yLabel)

            # Drawing Time Series collection.
            # TODO: Allow customization of symbology of Lines.
            settings = {}
            date_min = timeseries[0].min().astype(datetime.datetime)
            date_max = timeseries[0].max().astype(datetime.datetime)
            #
            for index, values in enumerate(timeseries[1:]):
                x = timeseries[0]
                y = values
                l_label = labels[index] if isinstance(labels, list) else None
                l_style = settings.get('linestyle', '-')
                l_width = settings.get('linewidth', 1)
                l_color = settings.get('color', None)
                m_style = settings.get('marker', None)
                m_wsize = settings.get('markersize', 3)

                ax_.plot(x, y,
                         color=l_color,
                         linestyle=l_style,
                         linewidth=l_width,
                         marker=m_style,
                         markersize=m_wsize,
                         label=l_label)

                has_labels = has_labels or l_label

            if relative_date:
                day_range = (date_max - date_min).days
                while day_range > 365:
                    day_range = day_range - 365
            else:
                day_range = (date_max - date_min).days

            ax_font_size = max(1, int(8 * self.figureXSize / 800))
            day_interval = max(1, 2 * int(day_range / self.dateRange))
            ax_.xaxis.set_major_locator(m_dates.DayLocator(interval=day_interval))
            ax_.xaxis.set_major_formatter(m_dates.DateFormatter(self.dateFormatter))

            for tick in ax_.xaxis.get_major_ticks():
                tick.label1.set_fontsize(max(1, ax_font_size - 1))

            fig.autofmt_xdate()
            if has_labels:
                ax_.legend(loc='best', fontsize=ax_font_size)

            ax_.grid()
            fig.savefig(self.connectionString, format=file_ext[1:])
            plt.close()

            # Load GDAL dataset from the rasterized Graph.
            gdal_env = GdalEnv.default()
            gdal = gdal_env.gdal()
            dataset = gdal.Open(self.connectionString, gdal.GA_ReadOnly)
            yield GdalDataset(dataset, gdal_env)

        pass

    @staticmethod
    def _timeseries_np(timeseries: Iterable[Dict]):
        """
        Convert stream of Date/Values to numpy arrays.
        """
        today_date = datetime.date.today()
        result = []

        for date_index, ts in enumerate(timeseries):
            date_ = ts.get('date')
            values = ts.get('values')

            if not date_:
                date_ = today_date + datetime.timedelta(days=date_index)
                date_ = date_.strftime('%Y-%m-%d')

            result.append([np.datetime64(date_)] + values)

        result = sorted(result, key=lambda x: x[0], reverse=False)
        result = np.transpose(np.array(result))
        return result
