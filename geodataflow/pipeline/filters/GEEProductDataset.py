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

import os
import uuid
import requests
import importlib
from zipfile import ZipFile
from typing import Dict, Iterable
from geodataflow.pipeline.filters.GEEProductCatalog import GEEProductCatalog


class GEEProductDataset(GEEProductCatalog):
    """
    The Filter extracts Datasets from GEE Collections via spatial & alphanumeric filters.
    """
    def __init__(self):
        GEEProductCatalog.__init__(self)
        self.configVars = ''
        self.bands = []
        self.groupByDate = True
        self.clipByAreaOfInterest = True

    @staticmethod
    def is_available() -> bool:
        """
        Indicates that this Module is available for use, some modules may depend
        on the availability of other third-party packages.
        """
        ee_api_spec = importlib.util.find_spec('ee')
        return ee_api_spec is not None

    def alias(self) -> str:
        """
        Returns the Human alias-name of this Module.
        """
        return 'EarthEngine Dataset'

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Extracts Datasets from GEE Collections via spatial & alphanumeric filters.'

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'EO STAC Imagery'

    def params(self) -> Dict:
        """
        Returns the declaration of parameters supported by this Module.
        """
        the_params = GEEProductCatalog.params(self)
        the_params['configVars'] = {
            'description':
                'Environment variables separated by commas. Commonly used to configure credentials.',
            'dataType': 'string',
            'default': ''
        }
        the_params['bands'] = {
            'description': 'List of Bands to fetch, or a string separated by commas. Empty means fetch all.',
            'dataType': 'string',
            'default': 'B4,B3,B2,B8',
            'placeHolder': 'B4,B3,B2,B8'
        }
        the_params['groupByDate'] = {
            'description': 'Group EO Products by Date.',
            'dataType': 'bool',
            'default': True
        }
        the_params['clipByAreaOfInterest'] = {
            'description': 'Clip EO Products by geometry of input AOI.',
            'dataType': 'bool',
            'default': True
        }
        return the_params

    def starting_run(self, schema_def, pipeline, processing_args):
        """
        Starting a new Workflow on Geospatial data.
        """
        from geodataflow.core.schemadef import GeometryType, DataType, FieldDef
        from geodataflow.geoext.dataset import DATASET_DEFAULT_SCHEMA_DEF

        new_fields = [
            FieldDef("productType", DataType.String),
            FieldDef("productDate", DataType.String)
        ]

        schema_def = GEEProductCatalog.starting_run(self, schema_def, pipeline, processing_args, False)
        schema_def = schema_def.clone()
        schema_def.geometryType = GeometryType.Polygon
        schema_def.fields = FieldDef.concat(DATASET_DEFAULT_SCHEMA_DEF, new_fields)
        return schema_def

    def run(self, feature_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        schema_def = self.pipeline_args.schema_def

        from geodataflow.geoext.gdalenv import GdalEnv
        from geodataflow.geoext.dataset import GdalDataset

        ee_config_options = GdalEnv.default_options()
        if self.configVars:
            for item in self.configVars.split(','):
                pair = item.split('=')
                ee_config_options[pair[0].strip()] = pair[1].strip() if len(pair) > 1 else ''

        # Query & fetch GEE imagery from Google Earth Engine...
        with GdalEnv(config_options=ee_config_options, temp_path=processing_args.temp_data_path()) as ee_env:
            #
            for feature in feature_store:
                geometry = feature.geometry

                ee_dataset = self.ee_fetch_dataset(geometry, self.clipByAreaOfInterest)
                ee_dataset_props = self.ee_object_props(ee_dataset)
                ee_first_image = ee_dataset.first()
                ee_image_props = self.ee_object_props(ee_first_image)

                image_props = ee_image_props.getInfo()
                band_scales = image_props['system:band_scales']

                # For each Date, get the mosaic the subset of GEE images.
                for product_date, ee_subset in self.ee_enumerate_subsets(ee_dataset, ee_dataset_props, ee_image_props):
                    if self.bands:
                        bands = self.bands.replace(' ', '').split(',') if isinstance(self.bands, str) else self.bands
                        ee_subset = ee_subset.select(bands)
                        factor_scale = band_scales[bands[0]]
                    else:
                        bands = list(band_scales.keys())
                        factor_scale = band_scales[bands[0]]

                    # Query mosaic trying several scales upto it fits Google Erath Engine requirements.
                    temp_name = 'temp_GEE_' + str(uuid.uuid4()).replace('-', '')
                    factor_count = 10
                    url = None
                    while factor_count > 0:
                        try:
                            params = {
                                'name': temp_name,
                                'filePerBand': False,
                                'scale': factor_scale,
                                'region': ee_subset.geometry(),
                                'crs': 'EPSG:' + str(schema_def.srid),
                                'fileFormat': 'GEO_TIFF',
                                'formatOptions': 'TILED=YES'
                            }
                            factor_count -= 1
                            url = ee_subset.getDownloadURL(params)
                            break
                        except Exception:
                            factor_scale *= 2
                            url = None

                    if not url:
                        raise Exception('Request does not fit GEE requirements, query smaller areas.')

                    # Fetch & save request to Geotiff (GEE outputs ZIP files).
                    response = requests.get(url, stream=True)
                    if response.status_code != 200:
                        raise Exception('An error occurred while downloading a GEE image.')

                    output_file = os.path.join(ee_env.temp_data_path(), temp_name + '.zip')
                    raster_file = os.path.join(ee_env.temp_data_path(), temp_name + '.tif')

                    with open(output_file, 'wb') as fp:
                        for chunk in response.iter_content(chunk_size=1024*1024):
                            if chunk:
                                fp.write(chunk)

                    with ZipFile(output_file, mode='r') as zf:
                        zf.extractall(ee_env.temp_data_path())

                    os.remove(output_file)

                    user_data = {
                        'productType': self.dataset,
                        'productDate': product_date
                    }
                    yield GdalDataset(raster_file, ee_env, user_data, False)
                #

        pass

    def ee_enumerate_subsets(self, ee_dataset, ee_dataset_props, ee_image_props) -> Iterable:
        """
        Enumerate the GEE Image set of the ImageCollection.
        """
        ee = self.ee_initialize()
        dataset_props = ee_dataset_props.getInfo()

        if self.groupByDate:
            for product_date in dataset_props['dates']:
                y, m, d = \
                    int(product_date[0:4]), int(product_date[5:7]), int(product_date[8:10])

                ee_subset = ee_dataset \
                    .filter(ee.Filter.calendarRange(y, y, 'year')) \
                    .filter(ee.Filter.calendarRange(m, m, 'month')) \
                    .filter(ee.Filter.calendarRange(d, d, 'day_of_month'))

                ee_mosaic = ee_subset.mosaic()
                ee_mosaic = ee_mosaic.set(ee_image_props)

                yield product_date, ee_mosaic
        else:
            count = dataset_props['count']

            for i in range(0, count):
                ee_image = ee.Image(ee_dataset.toList(count).get(i))
                ee_product_date = ee.Date(ee_image.get('system:time_start')).format('yyyy-MM-dd')
                yield ee_product_date.getInfo(), ee_image

        pass
