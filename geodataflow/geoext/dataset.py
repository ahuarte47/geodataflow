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
import logging
from typing import Any, Dict, Iterable, List, Tuple, Union

from geodataflow.geoext.commonutils import GeometryUtils
from geodataflow.geoext.gdalenv import GdalEnv
from geodataflow.core.schemadef import DataType, FieldDef

from osgeo import gdalconst as gdal_const
from osgeo import gdal_array
from osgeo import osr
from shapely.wkb import dumps as shapely_wkb_dumps
osr.UseExceptions()

# Default schema of a GDAL Dataset.
DATASET_DEFAULT_SCHEMA_DEF = [
    FieldDef(name='srid', data_type=DataType.Integer),
    FieldDef(name='dataType', data_type=DataType.Integer),
    FieldDef(name='rasterSizeX', data_type=DataType.Integer),
    FieldDef(name='rasterSizeY', data_type=DataType.Integer),
    FieldDef(name='rasterCount', data_type=DataType.Integer),
    FieldDef(name='pixelSizeX', data_type=DataType.Float),
    FieldDef(name='pixelSizeY', data_type=DataType.Float),
    FieldDef(name='noData', data_type=DataType.Float)
]


class GdalDataset:
    """
    Wrapper class of the GDAL Dataset object.
    """
    def __init__(self,
                 dataset_or_path: Union["GdalDataset", str],
                 gdal_env: GdalEnv = None,
                 user_data: Dict = {},
                 recyclable: bool = False):

        self.type = 'Raster'
        self.user_data = user_data or {}
        self._gdal_env = gdal_env
        self._dataset_path = None
        self._recyclable = recyclable
        self._init_object(dataset_or_path)

    def __del__(self):
        self.recycle()
        self._gdal_env = None
        self._dataset_path = None
        self._recyclable = False
        self._dataset = None

    def _init_object(self, dataset_ref: Union["GdalDataset", str]) -> None:
        """
        Helper method to initialize some GDAL attributes.
        """
        if isinstance(dataset_ref, GdalDataset):
            self._gdal_env = dataset_ref._gdal_env
            self._dataset_path = dataset_ref._dataset_path
            self._dataset = dataset_ref._dataset
        elif isinstance(dataset_ref, str):
            gdal = self.env().gdal()
            self._dataset_path = dataset_ref
            self._dataset = gdal.Open(dataset_ref, gdal.GA_ReadOnly)
        else:
            self._dataset_path = None
            self._dataset = dataset_ref

        rs_band = self._dataset.GetRasterBand(1)
        self.gdal_type = rs_band.DataType
        self.data_type = gdal_array.GDALTypeCodeToNumericTypeCode(self.gdal_type)
        rs_band = None

    @property
    def geometry(self):
        """
        Returns the Geometry of this Dataset.
        """
        envelope = self.get_envelope()
        geometry = GeometryUtils.create_geometry_from_bbox(*envelope)
        geometry = geometry.with_srid(self.get_spatial_srid())
        return geometry

    @property
    def properties(self) -> Dict[str, Any]:
        """
        Returns the Properties of this Dataset.
        """
        info = self.get_metadata()
        return {field_def.name: info.get(field_def.name) for field_def in DATASET_DEFAULT_SCHEMA_DEF}

    def env(self) -> GdalEnv:
        """
        Returns the related GdalEnv instance of this Dataset.
        """
        return self._gdal_env if self._gdal_env else GdalEnv.default()

    def dataset(self):
        """
        Returns the GDAL Dataset managed.
        """
        return self._dataset

    def dataset_path(self, force_exists: bool = False) -> str:
        """
        Returns the path of this Dataset.
        """
        if not self._dataset_path and force_exists:
            gdal_env = self.env()
            gdal = gdal_env.gdal()
            temp_file = os.path.join(gdal_env.temp_data_path(), str(uuid.uuid4()).replace('-', '') + '.tif')

            gdal.Translate(temp_file,
                           self._dataset,
                           creationOptions=['TILED=YES', 'COMPRESS=DEFLATE', 'PREDICTOR=2'])

            self._dataset_path = temp_file
            self._recyclable = True

        return self._dataset_path

    def recycle(self) -> bool:
        """
        Recycle temporary file resources created by this Dataset.
        """
        if self._recyclable and self._dataset_path and os.path.exists(self._dataset_path):
            self._dataset = None
            os.remove(self._dataset_path)
            self._dataset_path = None
            self._recyclable = False
            return True

        return False

    def get_metadata(self) -> Dict[str, Any]:
        """
        Returns the main geospatial metadata of this Dataset.
        """
        rs_band = self._dataset.GetRasterBand(1)
        no_data = rs_band.GetNoDataValue() if rs_band.GetNoDataValue() is not None else 0.0
        rs_band = None

        envelope = self.get_envelope()
        pixel_size_x = (envelope[2] - envelope[0]) / float(self._dataset.RasterXSize)
        pixel_size_y = (envelope[3] - envelope[1]) / float(self._dataset.RasterYSize)

        info = {
            'srid': self.get_spatial_srid(),
            'envelope': envelope,
            'dataType': self.gdal_type,
            'rasterSizeX': self._dataset.RasterXSize,
            'rasterSizeY': self._dataset.RasterYSize,
            'rasterCount': self._dataset.RasterCount,
            'pixelSizeX': pixel_size_x,
            'pixelSizeY': pixel_size_y,
            'noData': no_data
        }
        return info

    def get_envelope(self) -> Tuple[float, float, float, float]:
        """
        Returns the spatial envelope of this Dataset.
        """
        geo_transform = self._dataset.GetGeoTransform()
        c = geo_transform[0]
        a = geo_transform[1]
        b = geo_transform[2]
        f = geo_transform[3]
        d = geo_transform[4]
        e = geo_transform[5]
        t = 0  # Texel offset, by default the texel is centered to CENTER-CENTER pixel.
        col = 0
        row = 0
        env_a = [a * (col + t) + b * (row + t) + c, d * (col + t) + e * (row + t) + f]
        col = self._dataset.RasterXSize
        row = self._dataset.RasterYSize
        env_b = [a * (col + t) + b * (row + t) + c, d * (col + t) + e * (row + t) + f]
        min_x = min(env_a[0], env_b[0])
        min_y = min(env_a[1], env_b[1])
        max_x = max(env_a[0], env_b[0])
        max_y = max(env_a[1], env_b[1])
        return min_x, min_y, max_x, max_y

    def get_spatial_srid(self) -> int:
        """
        Returns the EPSG SRID code of the this Dataset.
        """
        spatial_wkt = self._dataset.GetProjection()
        spatial_ref = osr.SpatialReference()
        spatial_ref.ImportFromWkt(spatial_wkt)

        if spatial_ref is None:
            return 0

        srid = 0
        try:
            srid = spatial_ref.GetAuthorityCode(None)

            if srid is None or srid == 0 or srid == '':
                temp = spatial_ref.AutoIdentifyEPSG()
                if temp is not None and temp != 0 and temp != '':
                    srid = int(temp)
            else:
                srid = int(srid)

        except Exception as e:
            logging.warning('Error reading the SRID of the CRS="{}" Cause="{}"'.format(str(spatial_ref), e))

        return srid

    def clamp_geometry(self, geometry, padding_val: int = 0, minimum_ts: int = 0):
        """
        Clamp the specified Envelope/Geometry aligned to current GRID of this Dataset.
        """
        if not geometry:
            return geometry

        info = self.get_metadata()
        is_envelope = False

        if isinstance(geometry, list):
            geometry = GeometryUtils.create_geometry_from_bbox(*geometry)
            is_envelope = True
        else:
            transform_fn = GeometryUtils.create_transform_function(geometry.get_srid(), info.get('srid'))
            geometry = transform_fn(geometry)

        pixel_size_x = info.get('pixelSizeX')
        pixel_size_y = info.get('pixelSizeY')

        envelope = GeometryUtils.clamp_envelope(
            envelope=list(geometry.bounds),
            pixel_size_x=pixel_size_x,
            pixel_size_y=pixel_size_y,
            padding_val=padding_val,
            minimum_ts=minimum_ts
        )
        if is_envelope:
            return envelope

        geometry = GeometryUtils.create_geometry_from_bbox(*envelope)
        geometry = geometry.with_srid(info.get('srid'))
        return geometry

    def _geometry_to_layer(self, geometry) -> str:
        """
        Create a FeatureLayer from the specified Geometry.
        """
        gdal_env = self.env()
        ogr = gdal_env.ogr()

        attribute_name = 'my_id'
        layer_name = str(uuid.uuid4()).replace('-', '')
        layer_file = os.path.join(gdal_env.temp_data_path(), '{}.shp'.format(layer_name))

        spatial_ref = osr.SpatialReference()
        spatial_ref.ImportFromEPSG(geometry.get_srid())
        if hasattr(spatial_ref, 'SetAxisMappingStrategy'): spatial_ref.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        driver = ogr.GetDriverByName('ESRI Shapefile')
        feature_store = driver.CreateDataSource(layer_file, options=[])
        feature_layer = feature_store.CreateLayer(layer_name, srs=spatial_ref, geom_type=ogr.wkbMultiPolygon)
        feature_field = ogr.FieldDefn(attribute_name, ogr.OFTInteger)
        feature_layer.CreateField(feature_field)
        layer_schema = feature_layer.GetLayerDefn()

        geometry_wkb = shapely_wkb_dumps(geometry)
        geometry_ogr = ogr.CreateGeometryFromWkb(geometry_wkb)

        # Saving the geometries of interest to a temporary Feature Layer to rasterize.
        feature = ogr.Feature(layer_schema)
        feature.SetField(attribute_name, 1)
        feature.SetGeometry(geometry_ogr)
        feature_layer.CreateFeature(feature)
        feature = None

        layer_schema = None
        feature_field = None
        feature_layer = None
        feature_store = None
        return layer_file

    def warp(self,
             output_crs=None, output_res_x: float = None, output_res_y: float = None, output_geom=None,
             resample_arg: int = gdal_const.GRA_Bilinear,
             cutline: bool = False) -> "GdalDataset":
        """
        Warp this Dataset by specified parameters.
        """
        gdal_env = self.env()
        gdal = gdal_env.gdal()
        info = self.get_metadata()

        if isinstance(output_geom, list):
            output_geom = GeometryUtils.create_geometry_from_bbox(*output_geom)
            output_geom = output_geom.with_srid(GeometryUtils.get_srid(output_crs) if output_crs else info.get('srid'))

        if output_geom:
            source_crs = GeometryUtils.get_spatial_crs(info.get('srid'))
            output_crs = GeometryUtils.get_spatial_crs(output_crs) if output_crs else source_crs
            window_crs = GeometryUtils.get_spatial_crs(GeometryUtils.get_srid(output_geom))

            # Calculate intersection of two Envelopes.
            if source_crs and output_crs:
                transform_fn = GeometryUtils.create_transform_function(source_crs, output_crs)
                geometry_a = GeometryUtils.create_geometry_from_bbox(*self.get_envelope())
                geometry_a = transform_fn(geometry_a)
            else:
                geometry_a = GeometryUtils.create_geometry_from_bbox(*self.get_envelope())

            if window_crs and output_crs:
                transform_fn = GeometryUtils.create_transform_function(window_crs, output_crs)
                geometry_b = transform_fn(output_geom)
            else:
                geometry_b = output_geom

            # Run intersection!
            geometry = geometry_a.intersection(geometry_b).with_srid(output_crs.to_epsg())

            if output_res_x and output_res_y:
                envelope = GeometryUtils.clamp_envelope(list(geometry.bounds), output_res_x, output_res_y)
                geometry = GeometryUtils.create_geometry_from_bbox(*envelope)
            else:
                envelope = list(geometry.bounds)

            layer_file = \
                self._geometry_to_layer(geometry) if cutline else None

            # Define the Warping options for resampling and reprojection.
            options = gdal.WarpOptions(format='Gtiff',
                                       outputBounds=envelope,
                                       cutlineDSName=layer_file,
                                       resampleAlg=resample_arg,
                                       xRes=output_res_x,
                                       yRes=output_res_y,
                                       srcSRS='EPSG:' + str(source_crs.to_epsg()),
                                       srcNodata=info.get('noData'),
                                       dstSRS='EPSG:' + str(output_crs.to_epsg()),
                                       dstNodata=info.get('noData'),
                                       copyMetadata=True,
                                       creationOptions=['TILED=YES', 'COMPRESS=DEFLATE', 'PREDICTOR=2'])
        else:
            source_srid = info.get('srid')
            output_srid = GeometryUtils.get_srid(output_crs) if output_crs else source_srid

            # Define the Warping options for resampling and reprojection.
            options = gdal.WarpOptions(format='Gtiff',
                                       resampleAlg=resample_arg,
                                       xRes=output_res_x,
                                       yRes=output_res_y,
                                       srcSRS='EPSG:' + str(source_srid),
                                       srcNodata=info.get('noData'),
                                       dstSRS='EPSG:' + str(output_srid),
                                       dstNodata=info.get('noData'),
                                       copyMetadata=True,
                                       creationOptions=['TILED=YES', 'COMPRESS=DEFLATE', 'PREDICTOR=2'])

        warp_name = str(uuid.uuid1()).replace('-', '')
        warp_file = os.path.join(gdal_env.temp_data_path(), 'temp_WARP_{}.tif'.format(warp_name))
        dataset = gdal.Warp(warp_file, self._dataset, options=options)
        if dataset:
            dataset.FlushCache()
            dataset = None

        return GdalDataset(warp_file, gdal_env, self.user_data.copy(), True)

    def calc(self,
             band_names: Iterable[str], band_expression: str, no_data: float = -9999.0) -> "GdalDataset":
        """
        Apply the specified Raster Calc expression (numpy syntax) to this Dataset.
        """
        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
                   'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'Y', 'Z']

        band_names = band_names or self.user_data.get('bands')
        if not band_names:
            raise Exception('BandNames of GdalDataset::apply_calc() method can not be empty!')

        dataset_file = self.dataset_path(force_exists=True)
        gdal_env = self.env()
        no_data = no_data if no_data is not None else -9999.0

        calc_name = str(uuid.uuid1()).replace('-', '')
        calc_file = os.path.join(gdal_env.temp_data_path(), 'temp_CALC_{}.tif'.format(calc_name))
        calc_args = ''
        calc_expr = band_expression

        for i, band_name in enumerate(band_names):
            if band_name in calc_expr:
                calc_args += ' -{} "{}" --{}_band={}'.format(letters[i], dataset_file, letters[i], i + 1)
                calc_expr = calc_expr.replace(band_name, letters[i] + '.astype(numpy.float32)')

        for calc_item in calc_expr.split(','):
            calc_args += ' --calc="{}"'.format(calc_item)

        # Perform GdalCalc to this GDAL Dataset.
        scripts_path = GdalEnv.gdal_scripts_path()
        command_line = 'python "' + os.path.join(scripts_path, 'gdal_calc.py') + '"'
        command_line += ' --overwrite --type=Float32 --NoDataValue={} --quiet'.format(no_data)
        command_line += calc_args
        command_line += ' --outfile="' + calc_file + '"'
        command_line += ' --format Gtiff --co "TILED=YES" --co "COMPRESS=DEFLATE" --co "PREDICTOR=2"'
        gdal_env.run(command_line)
        #
        return GdalDataset(calc_file, gdal_env, self.user_data.copy(), True)

    def split(self, tile_size_x: int, tile_size_y: int, padding: int = 0) -> Iterable["GdalDataset"]:
        """
        Split this Dataset into tiles.
        """
        gdal_env = self.env()
        driver = gdal_env.gdal().GetDriverByName('Gtiff')
        format_options = ['TILED=YES', 'COMPRESS=DEFLATE', 'PREDICTOR=2']

        geo_transform = self._dataset.GetGeoTransform()
        raster_size_x = self._dataset.RasterXSize
        raster_size_y = self._dataset.RasterYSize
        raster_count = self._dataset.RasterCount
        spatial_wkt = self._dataset.GetProjection()

        x, y, w, h = 0, 0, 0, 0
        item_count = len(range(0, raster_size_x, tile_size_x)) * len(range(0, raster_size_y, tile_size_y))
        item_index = 0

        for i in range(0, raster_size_x, tile_size_x):
            y = 0
            for j in range(0, raster_size_y, tile_size_y):
                w = min(i + tile_size_x, raster_size_x) - i
                h = min(j + tile_size_y, raster_size_y) - j

                if padding:
                    l_ = max(0, x - padding)
                    t_ = max(0, y - padding)
                    r_ = min(x + w + padding, raster_size_x)
                    b_ = min(y + h + padding, raster_size_y)
                else:
                    l_, t_, r_, b_ = x, y, x + w, y + h

                x_pos = geo_transform[0] + (l_ * geo_transform[1])
                y_pos = geo_transform[3] + (t_ * geo_transform[5])
                w = r_ - l_
                h = b_ - t_

                logging.info(
                    'Splitting Dataset, XY=({} {}), RECT=({} {} {} {}), Step=({} of {})...'
                    .format(x_pos, y_pos, l_, t_, r_, b_, item_index+1, item_count))

                # Create child GDAL Dataset if current Tile.
                split_name = str(uuid.uuid1()).replace('-', '')
                split_file = os.path.join(gdal_env.temp_data_path(), 'temp_SPLIT_C_{}.tif'.format(split_name))
                output = driver.Create(split_file, w, h, raster_count, self.gdal_type, options=format_options)
                output.SetGeoTransform([x_pos, geo_transform[1], 0.0, y_pos, 0.0, geo_transform[5]])
                output.SetProjection(spatial_wkt)
                metadata = self._dataset.GetMetadata()
                if metadata is not None:
                    output.SetMetadata(metadata)

                # Fill data of Bands.
                for band_index in range(0, raster_count):
                    band_s = self._dataset.GetRasterBand(band_index + 1)
                    raster = band_s.ReadAsArray(xoff=l_, yoff=t_, win_xsize=w, win_ysize=h)
                    nodata = band_s.GetNoDataValue()
                    band_s = None

                    band_t = output.GetRasterBand(band_index + 1)
                    band_t.Fill(nodata)
                    band_t.SetNoDataValue(nodata)
                    band_t.WriteArray(raster)
                    band_t.FlushCache()
                    band_t = None

                output.FlushCache()
                item_index += 1

                # print('{} -> {}'.format([x, y, w, h], [l, t, r, b]))
                yield GdalDataset(output, gdal_env, self.user_data.copy(), True)
                y += tile_size_y

            x += tile_size_x

        pass

    @staticmethod
    def mosaic_of_datasets(datasets: List["GdalDataset"],
                           resample_arg: int = gdal_const.GRA_Bilinear) -> "GdalDataset":
        """
        Returns a mosaic of the specified Dataset collection.
        """
        if len(datasets) == 0:
            return None
        if len(datasets) == 1:
            return datasets[0]

        first_info = datasets[0].get_metadata()
        user_data = {}
        mosaic_of_files = list()

        gdal_env = datasets[0].env()
        gdal = gdal_env.gdal()
        gdal_config = gdal_env.gdal_config()

        # Do we need transform input GDAL Datasets, otherwise "gdalbuildvrt" will fail.
        for dataset in datasets:
            info = dataset.get_metadata()
            user_data.update(dataset.user_data)

            if info.get('srid') == first_info.get('srid'):
                mosaic_of_files.append(dataset.dataset_path(force_exists=True))
            else:
                transform_fn = GeometryUtils.create_transform_function(
                    info.get('srid'), first_info.get('srid')
                )

                geometry = GeometryUtils.create_geometry_from_bbox(*dataset.get_envelope())
                geometry = transform_fn(geometry)
                envelope = list(geometry.bounds)
                envelope = GeometryUtils.clamp_envelope(
                    envelope,
                    first_info.get('pixelSizeX'),
                    first_info.get('pixelSizeY')
                )

                # Define the Warping options for resampling and reprojection.
                options = gdal.WarpOptions(format='Gtiff',
                                           outputBounds=envelope,
                                           resampleAlg=resample_arg,
                                           xRes=first_info.get('pixelSizeX'),
                                           yRes=first_info.get('pixelSizeY'),
                                           srcSRS='EPSG:' + str(info.get('srid')),
                                           srcNodata=info.get('noData'),
                                           dstSRS='EPSG:' + str(first_info.get('srid')),
                                           dstNodata=first_info.get('noData'),
                                           copyMetadata=True,
                                           creationOptions=['TILED=YES', 'COMPRESS=DEFLATE', 'PREDICTOR=2'])

                warp_name = str(uuid.uuid1()).replace('-', '')
                warp_file = os.path.join(gdal_env.temp_data_path(), 'temp_WARP_C_{}.tiff'.format(warp_name))
                dataset = gdal.Warp(warp_file, dataset.dataset(), options=options)
                if dataset:
                    dataset.FlushCache()
                    dataset = None

                mosaic_of_files.append(warp_file)
            #

        # Merging all files to one unique one.
        mosaic_name = str(uuid.uuid1()).replace('-', '')
        mosaic_file = os.path.join(gdal_env.temp_data_path(), 'temp_MOSAIC_{}.vrt'.format(mosaic_name))
        command_line = 'gdalbuildvrt {} "{}" {}'.format(gdal_config, mosaic_file, ' '.join(mosaic_of_files))
        gdal_env.run(command_line)
        #
        return GdalDataset(mosaic_file, gdal_env, user_data)
