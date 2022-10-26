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

import logging
from typing import Dict
from geodataflow.pipeline.filters.EOProductCatalog import EOProductCatalog


class EOProductDataset(EOProductCatalog):
    """
    The Filter extracts Datasets from EO/STAC Collections via spatial & alphanumeric filters.
    """
    def __init__(self):
        EOProductCatalog.__init__(self)
        self.configVars = 'AWS_NO_SIGN_REQUEST=YES'
        self.bands = []
        self.groupByDate = True
        self.clipByAreaOfInterest = True

    def alias(self) -> str:
        """
        Returns the Human alias-name of this Module.
        """
        return 'Dataset'

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Extracts Datasets from EO/STAC Collections via spatial & alphanumeric filters.'

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'EO STAC Imagery'

    def params(self) -> Dict:
        """
        Returns the declaration of parameters supported by this Module.
        """
        the_params = EOProductCatalog.params(self)
        the_params['configVars'] = {
            'description':
                'Environment variables separated by commas. Commonly used to configure credentials.',
            'dataType': 'string',
            'default': 'AWS_NO_SIGN_REQUEST=YES'
        }
        the_params['bands'] = {
            'description': 'List of Bands to fetch, or a string separated by commas. Empty means fetch all.',
            'dataType': 'string',
            'default': 'B04,B03,B02,B08',
            'placeHolder': 'B04,B03,B02,B08'
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
        from geodataflow.core.schemadef import GeometryType
        from geodataflow.geoext.dataset import DATASET_DEFAULT_SCHEMA_DEF

        schema_def = EOProductCatalog.starting_run(self, schema_def, pipeline, processing_args)
        schema_def = schema_def.clone()
        schema_def.geometryType = GeometryType.Polygon
        schema_def.fields = DATASET_DEFAULT_SCHEMA_DEF.copy()
        return schema_def

    def run(self, feature_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        schema_def = self.pipeline_args.schema_def

        from collections import OrderedDict
        from geodataflow.eogeo.dataset import EOGdalDataset
        from geodataflow.geoext.gdalenv import GdalEnv

        eo_config_options = {
            'GDAL_DISABLE_READDIR_ON_OPEN': 'FALSE',
            'CPL_CURL_VERBOSE': 'NO',
            'CPL_DEBUG': 'NO',
            'CPL_VSIL_CURL_ALLOWED_EXTENSIONS': '.tif,.tiff,.vrt,.ovr'
        }
        for item in self.configVars.split(','):
            pair = item.split('=')
            eo_config_options[pair[0].strip()] = pair[1].strip()

        with GdalEnv(config_options=eo_config_options, temp_path=processing_args.temp_data_path()) as eo_env:
            #
            product_groups = OrderedDict()
            bands = list(filter(None, self.bands.replace(' ', '').split(','))) \
                if isinstance(self.bands, str) else self.bands

            # Group EO Products by Date.
            for product in EOProductCatalog.run(self, feature_store, processing_args):
                product_date = product.properties.get('gdf:product_date')

                curr_list = product_groups.get(product_date, [])
                curr_list.append(product)
                product_groups[product_date] = curr_list

            def custom_dataset_op(dataset_ob, operation_args):
                """
                Apply to input GDAL Datasets a custom operation.
                """
                output_crs = operation_args.get('crs')
                clip_geometry = operation_args.get('clippingGeom', None)

                # Figure out the best PixelSize of output Dataset.
                best_datasets = [
                    d for d in operation_args.get('datasets', [])
                    if d.get_spatial_srid() == output_crs.to_epsg()
                ]
                if best_datasets:
                    best_dataset = best_datasets[0]
                    best_info = best_dataset.get_metadata()
                    output_res_x = best_info.get('pixelSizeX')
                    output_res_y = best_info.get('pixelSizeY')

                    # Clamping Geometry to output PixelSize.
                    clip_geometry = best_dataset.clamp_geometry(clip_geometry)
                else:
                    output_res_x = None
                    output_res_y = None

                # Warp & Clip Dataset.
                return dataset_ob.warp(output_crs, output_res_x, output_res_y, clip_geometry)

            logging.info('Fetching EO Products as GDAL Datasets...')

            # Fetch EO Products as GDAL Datasets.
            for product_date, products in product_groups.items():
                logging.info('Starting conversion of EO Product, Date: {}...'.format(product_date))

                clipping_geom = products[0].areaOfInterest.geometry \
                    if self.clipByAreaOfInterest and products[0].areaOfInterest else None

                custom_args = {
                    'crs': schema_def.crs,
                    'clippingGeom': clipping_geom
                }

                # Convert to a mosaic of GDAL Datasets.
                if self.groupByDate:
                    datasets = [EOGdalDataset.open([product.assets for product in products],
                                                   bands,
                                                   eo_env,
                                                   custom_dataset_op,
                                                   custom_args)]
                else:
                    datasets = [EOGdalDataset.open(product.assets,
                                                   bands,
                                                   eo_env,
                                                   custom_dataset_op,
                                                   custom_args) for product in products]

                logging.info('Done!')

                for dataset in datasets:
                    dataset.user_data['areaOfInterest'] = products[0].areaOfInterest
                    dataset.user_data['product_type'] = self.product
                    dataset.user_data['product_date'] = product_date
                    yield dataset
            #
        pass
