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

from geodataflow.core.capabilities import StoreCapabilities
from geodataflow.pipeline.basictypes import AbstractWriter


class RasterWriter(AbstractWriter):
    """
    Writes Datasets to a Geospatial RasterStore using GDAL providers.
    """
    def __init__(self):
        AbstractWriter.__init__(self)
        self.connectionString = ''
        self.formatOptions = []

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Writes Datasets to a Geospatial RasterStore using GDAL providers.'

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
                'description':
                    'Connection string of the Raster Store (Common GDAL extensions are supported).',
                'dataType': 'string',
                'default': 'output.tif',
                'extensions': ['.tif', '.ecw', '.jp2', '.png', '.jpg']
            },
            'formatOptions': {
                'description': 'GDAL format options of output Dataset (Optional).',
                'dataType': 'string',
                'default': '-of COG',
            }
        }

    def test_capability(self, connection_string: str, capability: StoreCapabilities) -> bool:
        """
        Returns this Module supports the specified ConnectionString and named StoreCapability.
        """
        from geodataflow.geoext.commonutils import GdalUtils
        return GdalUtils.test_gdal_capability(connection_string, capability)

    def starting_run(self, schema_def, pipeline, processing_args):
        """
        Starting a new Workflow on Geospatial data.
        """
        from geodataflow.geoext.commonutils import DataUtils

        for item_string in DataUtils.enumerate_single_connection_string(self.connectionString):
            #
            if not self.test_capability(item_string, StoreCapabilities.CREATE):
                raise Exception('The GDAL Driver of "{}" does not support Data creation!'.format(item_string))

            from geodataflow.core.schemadef import SchemaDef, GeometryType
            from geodataflow.geoext.dataset import DATASET_DEFAULT_SCHEMA_DEF

            schema_def = SchemaDef(type='RasterLayer',
                                   name=DataUtils.get_layer_name(item_string),
                                   srid=schema_def.crs.to_epsg(),
                                   crs=schema_def.crs,
                                   geometryType=GeometryType.Polygon,
                                   envelope=[1.e+20, 1.e+20, -1.e+20, -1.e+20],
                                   fields=DATASET_DEFAULT_SCHEMA_DEF.copy())

            return schema_def

        return None

    def run(self, dataset_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        dataset_count = 0

        from geodataflow.geoext.commonutils import DataUtils, GdalUtils
        from geodataflow.geoext.dataset import GdalDataset
        from geodataflow.geoext.gdalenv import GdalEnv

        gdal_env = GdalEnv.default()
        gdal = gdal_env.gdal()

        format_options = self.formatOptions or []
        format_options = format_options.split(' ') if isinstance(format_options, str) else format_options
        driver_options = [format_options[i + 1] for i, opt in enumerate(format_options) if opt == '-of']
        format_options = [format_options[i + 1] for i, opt in enumerate(format_options) if opt == '-co']

        connection_strings = list(DataUtils.enumerate_single_connection_string(self.connectionString))
        connection_index = 0

        for dataset in dataset_store:
            #
            if not isinstance(dataset, GdalDataset):
                raise Exception('RasterStore only accepts Datasets as input data.')

            connection_string = connection_strings[connection_index]
            connection_index += 1

            driver = GdalUtils.get_gdal_driver(connection_string) \
                if not driver_options else gdal.GetDriverByName(driver_options[0])
            metadata = driver.GetMetadata()

            # Write GDAL Datasets.
            if gdal.DCAP_CREATECOPY in metadata and metadata[gdal.DCAP_CREATECOPY] == 'YES':
                output = \
                    driver.CreateCopy(connection_string, dataset.dataset(), strict=0, options=format_options)

                output.FlushCache()
                output = None
            else:
                info = dataset.get_metadata()
                cols = info.get('rasterSizeX')
                rows = info.get('rasterSizeY')
                band_count = info.get('rasterCount')
                data_type = info.get('dataType')
                no_data = info.get('noData')
                spatial_ref = GdalUtils.get_spatial_reference(info.get('srid'))
                envelope = dataset.get_envelope()
                pixel_size_x = info.get('pixelSizeX')
                pixel_size_y = info.get('pixelSizeY')

                # Create output GDAL Dataset.
                output = \
                    driver.Create(connection_string, cols, rows, band_count, data_type, format_options)

                gdal_dataset = dataset.dataset()
                output.SetGeoTransform([envelope[0], pixel_size_x, 0.0, envelope[3], 0.0, -pixel_size_y])
                output.SetProjection(spatial_ref.ExportToWkt())
                metadata = gdal_dataset.GetMetadata()
                if metadata is not None:
                    output.SetMetadata(metadata)

                for band_index in range(0, band_count):
                    band_s = gdal_dataset.GetRasterBand(band_index + 1)
                    raster = band_s.ReadAsArray(xoff=0, yoff=0, win_xsize=cols, win_ysize=rows)
                    band_s = None

                    band_t = output.GetRasterBand(band_index + 1)
                    band_t.Fill(no_data)
                    band_t.SetNoDataValue(no_data)
                    band_t.WriteArray(raster)
                    band_t.FlushCache()
                    band_t = None

                output.FlushCache()
                output = None

            dataset_count += 1
            yield dataset

        logging.info('{:,} Datasets saved to "{}".'.format(dataset_count, connection_string))
        pass

    def finished_run(self, pipeline, processing_args) -> bool:
        """
        Finishing a Workflow on Geospatial data.
        """
        return True
