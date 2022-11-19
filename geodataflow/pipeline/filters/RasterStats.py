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

import numpy as np
import logging
from typing import Dict, List
from geodataflow.pipeline.basictypes import AbstractFilter

# List of supported raster statistics.
ZONAL_STATS = [
    'min',
    'max',
    'mean',
    'count',
    'sum',
    'std',
    'median',
    'majority',
    'minority',
    'unique',
    'range',
    'nodataCount',
    'percentile_10',
    'percentile_25',
    'percentile_75',
    'percentile_90',
    'size'
]


def key_assoc_val(d, func, exclude=None):
    """
    Return the key associated with the value returned by func.
    """
    vs = list(d.values())
    ks = list(d.keys())
    key = ks[vs.index(func(vs))]
    return key


def get_percentile(stat):
    if not stat.startswith('percentile_'):
        raise ValueError("must start with 'percentile_'")

    qstr = stat.replace("percentile_", '')
    q = float(qstr)

    if q > 100.0:
        raise ValueError('percentiles must be <= 100')
    if q < 0.0:
        raise ValueError('percentiles must be >= 0')

    return q


class RasterStats(AbstractFilter):
    """
    The Filter summarizes geospatial raster datasets and transform them to vector geometries.
    """
    def __init__(self):
        AbstractFilter.__init__(self)
        self.stats = ['median']
        self.bandIndex = 0
        self.polygonize = False

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Summarizes geospatial raster datasets and transform them to vector geometries.'

    def alias(self) -> str:
        """
        Returns the Human alias-name of this Module.
        """
        return 'Stats'

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'Raster'

    def params(self) -> Dict:
        """
        Returns the declaration of parameters supported by this Module.
        """
        zonal_stats = sorted(ZONAL_STATS)

        return {
            'stats': {
                'description':
                    'Method, or list of methods separated by commas, ' +
                    'of summarizing and aggregating the raster values of input Datasets--.',
                'dataType': 'string',
                'default': 'median',
                'options': zonal_stats,
                'labels': zonal_stats
            },
            "bandIndex": {
                'description': 'Index of Band from which to calculate Raster statistics.',
                'dataType': 'int',
                'default': 0
            },
            "polygonize": {
                'description':
                    'Creates vector polygons for all connected regions of no-data pixels in the raster.',
                'dataType': 'bool',
                'default': False
            }
        }

    def starting_run(self, schema_def, pipeline, processing_args):
        """
        Starting a new Workflow on Geospatial data.
        """
        from geodataflow.core.schemadef import GeometryType, DataType, FieldDef

        stat_names = self.stats if isinstance(self.stats, list) else str(self.stats).split(',')
        for stat_name in stat_names:
            if stat_name not in ZONAL_STATS:
                raise Exception('The raster statistic "{}" is not supported by RasterStats.'.format(stat_name))

        schema_def = schema_def.clone()
        schema_def.type = 'FeatureLayer'
        schema_def.geometryType = GeometryType.Polygon
        schema_def.fields += [
            FieldDef(name=stat_name, data_type=DataType.Float) for stat_name in stat_names
        ]
        return schema_def

    def run(self, data_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        from geodataflow.geoext.dataset import GdalDataset

        stat_names = self.stats if isinstance(self.stats, list) else str(self.stats).split(',')
        band_index = self.bandIndex
        feature_index = 0

        for dataset in data_store:
            if not isinstance(dataset, GdalDataset):
                raise Exception('RasterStats only accepts Datasets as input data.')

            gdal_dataset = dataset.dataset()
            raster_size_x = gdal_dataset.RasterXSize
            raster_size_y = gdal_dataset.RasterYSize
            properties = dataset.properties.copy()

            # Extract or Polygonize Geometry.
            geometry = dataset.polygonize(band_index) if self.polygonize else dataset.geometry
            if geometry is None:
                logging.warning('Polygonize returns an empty Geometry, input Dataset is skipped.')
                continue

            # Calculate Zonal statistics.
            rs_band = gdal_dataset.GetRasterBand(band_index + 1)
            raster = rs_band.ReadAsArray(xoff=0, yoff=0, win_xsize=raster_size_x, win_ysize=raster_size_y)
            nodata = rs_band.GetNoDataValue()
            properties.update(RasterStats.zonal_statistics(raster, nodata, stat_names))
            raster = None
            rs_band = None

            feature = type('Feature', (object,), {
                'type': 'Feature',
                'fid': feature_index,
                'properties': properties,
                'geometry': geometry,
            })
            feature_index += 1
            yield feature

        pass

    @staticmethod  # noqa: C901
    def zonal_statistics(raster, no_data: float, stats: List[str]):  # noqa: C901
        """
        Zonal statistics of raster values aggregated to vector geometries.
        """
        raster = raster.astype(float)
        no_data = float(no_data)
        feature_stats = {}

        # Run the counter once, only if needed.
        run_count = 'majority' in stats or 'minority' in stats or 'unique' in stats

        # Set nodata mask.
        is_no_data = (raster == no_data) | np.isnan(raster)
        # Mask the source data array.
        masked = np.ma.MaskedArray(raster, mask=is_no_data)

        # Fill stats.
        if masked.compressed().size == 0:
            # nothing here, fill with None and move on.
            feature_stats = dict([(stat, None) for stat in stats])
            # special case, zero makes sense here.
            if 'count' in stats:
                feature_stats['count'] = 0
        else:
            if run_count:
                keys, counts = np.unique(masked.compressed(), return_counts=True)
                try:
                    pixel_count = dict(zip([k.item() for k in keys], [c.item() for c in counts]))
                except AttributeError:
                    pixel_count = dict(zip([np.asscalar(k) for k in keys], [np.asscalar(c) for c in counts]))
            else:
                pixel_count = {}

            if 'min' in stats:
                feature_stats['min'] = float(masked.min())
            if 'max' in stats:
                feature_stats['max'] = float(masked.max())
            if 'mean' in stats:
                feature_stats['mean'] = float(masked.mean())
            if 'count' in stats:
                feature_stats['count'] = int(masked.count())
            if 'sum' in stats:
                feature_stats['sum'] = float(masked.sum())
            if 'std' in stats:
                feature_stats['std'] = float(masked.std())
            if 'median' in stats:
                feature_stats['median'] = float(np.median(masked.compressed()))
            if 'majority' in stats:
                feature_stats['majority'] = float(key_assoc_val(pixel_count, max))
            if 'minority' in stats:
                feature_stats['minority'] = float(key_assoc_val(pixel_count, min))
            if 'unique' in stats:
                feature_stats['unique'] = len(list(pixel_count.keys()))
            if 'range' in stats:
                rmin = float(masked.min())
                rmax = float(masked.max())
                feature_stats['range'] = rmax - rmin

            for pctile in [s for s in stats if s.startswith('percentile_')]:
                q = get_percentile(pctile)
                pctarr = masked.compressed()
                feature_stats[pctile] = np.percentile(pctarr, q)

        if 'nodataCount' in stats:
            feature_stats['nodataCount'] = int(is_no_data.sum())
        if 'size' in stats:
            feature_stats['size'] = raster.size

        return feature_stats
