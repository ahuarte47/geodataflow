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
import uuid
from typing import Any, Callable, List, Union

from geodataflow.spatial.dataset import GdalDataset
from geodataflow.spatial.gdalenv import GdalEnv

# Some predefined Satellite band names and indexes.
EO_BAND_NAMES = dict([
    ('S2_MSI_L2A', ['B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B09', 'B11', 'B12',
                    'AOT', 'WVP', 'SCL'])
])


class EOGdalDataset(GdalDataset):
    """
    Wrapper of a GDAL Dataset reading EO/STAC Products (Raster Datasets).
    """
    @staticmethod
    def calculate_gdal_path(dataset_path: str, gdal_env: GdalEnv) -> str:
        """
        Returns the GDAL FileSystem path to access to the specified resource.
        """
        if dataset_path.startswith('s3://'):
            return '/vsis3/' + dataset_path[5:]
        if dataset_path.startswith('gs://'):
            return '/vsigs/' + dataset_path[5:]

        if dataset_path.startswith('https://'):
            #
            if all(f in dataset_path for f in ['.s3.', '.amazonaws.com/']):
                temp_ = dataset_path[8:].split('/')
                temp_ = '/'.join([temp_[0].split('.')[0]] + temp_[1:])
                return '/vsis3/' + temp_

            gdal = gdal_env.gdal()
            signed_url = gdal.GetSignedURL(dataset_path)
            return '/vsicurl/' + signed_url if signed_url else dataset_path

        return dataset_path

    @staticmethod
    def open(assets_collection: Union[str, List[str]],
             bands: List[str],
             gdal_env: GdalEnv,
             custom_dataset_func: Callable[[GdalDataset, Any], GdalDataset] = None,
             custom_args: Any = None) -> GdalDataset:
        """
        Open the specified EO Product path, it can be a mosaic-list of paths.
        """
        assets_collection = \
            assets_collection if isinstance(assets_collection, list) else [assets_collection]

        if gdal_env is None:
            gdal_env = GdalEnv.default()

        if not bands:
            bands = EO_BAND_NAMES.get('S2_MSI_L2A')

        # Read each EO Product as mosaic of GDAL Datasets.
        datasets = list()
        gdal_config = gdal_env.gdal_config()

        for assets in assets_collection:
            raster_files = [
                EOGdalDataset.calculate_gdal_path(assets[band]["href"], gdal_env) for band in bands
            ]
            virtual_name = str(uuid.uuid1()).replace('-', '')
            virtual_file = os.path.join(gdal_env.temp_data_path(), 'temp_S3_{}.vrt'.format(virtual_name))

            command_line = \
                'gdalbuildvrt {} -separate "{}" {}' \
                .format(gdal_config, virtual_file, ' '.join(raster_files))

            gdal_env.run(command_line)
            datasets.append(GdalDataset(virtual_file, gdal_env))

        # Apply custom transform to input Datasets?
        if custom_dataset_func:
            custom_args = custom_args.copy()
            custom_args['datasets'] = datasets
            custom_args['gdal_env'] = gdal_env
            datasets = [custom_dataset_func(dataset, custom_args) for dataset in datasets]

        # Create output, a mosaic of GDAL datasets.
        dataset = GdalDataset.mosaic_of_datasets(datasets)
        return dataset
