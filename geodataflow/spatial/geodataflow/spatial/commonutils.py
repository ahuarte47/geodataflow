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
import logging
import re
from typing import Any, Callable, Dict, Iterable, List, Tuple, Union

import pyproj as pj
from shapely.geometry.polygon import Polygon
from shapely.geometry.base import BaseGeometry
from shapely.geos import lgeos
from shapely.ops import transform

from geodataflow.core.capabilities import StoreCapabilities


class DataUtils:
    """
    Provides generic Data/File utility functions.
    """
    @staticmethod
    def get_layer_name(connection_string: str) -> str:
        """
        Returns the FeatureClass name of the specified GDAL/OGR ConnectionString.
        """
        if DataUtils.represents_json_feature_collection(connection_string):
            return 'FeatureCollection'

        file_name, file_ext = os.path.splitext(connection_string)
        if file_name and file_ext:
            tmp_key = os.path.basename(file_name)
            tmp_pos = tmp_key.find('.')
            return tmp_key[:tmp_pos] if tmp_pos != -1 else tmp_key

        raise Exception('Unknown LayerName parsing of the ConnectionString="{}"'.format(connection_string))

    @staticmethod
    def replace_layer_name(connection_string: str, layer_name: str) -> str:
        """
        Replaces the LayerName of the specified GDAL/OGR ConnectionString.
        """
        if DataUtils.represents_json_feature_collection(connection_string):
            return layer_name

        file_name, file_ext = os.path.splitext(connection_string)
        if file_name and file_ext:
            tmp_key = os.path.basename(file_name)
            tmp_pos = tmp_key.find('.')
            tmp_ext = tmp_key[tmp_pos:] if tmp_pos != -1 else ''
            return os.path.join(os.path.dirname(connection_string), layer_name + tmp_ext + file_ext)

        raise Exception('Unknown LayerName parsing of the ConnectionString="{}"'.format(connection_string))

    @staticmethod
    def enumerate_single_connection_string(connection_string: Union[str, Iterable[str]]) -> Iterable[str]:
        """
        Enumerates the single connection string from the specified connection string.
        """
        if DataUtils.represents_json_feature_collection(connection_string):
            yield connection_string
            return

        if isinstance(connection_string, str):
            for connection_item in re.split(';|\n', connection_string):
                if '*' in connection_item:
                    import glob
                    for file_name in glob.glob(connection_item):
                        yield file_name
                else:
                    yield connection_item
            return

        for connection_item in connection_string:
            for temp_c in DataUtils.enumerate_single_connection_string(connection_item):
                yield temp_c

        pass

    @staticmethod
    def represents_json_feature_collection(connection_string: Union[str, List[str], Dict[str, Any]]) -> bool:
        """
        Returns if the specified connection string is a GeoJSON Feature collection.
        """
        if isinstance(connection_string, list) and connection_string:
            connection_string = connection_string[0]
        if isinstance(connection_string, dict) and connection_string.get('type', '') == 'FeatureCollection':
            return True
        if isinstance(connection_string, str) and len(connection_string) > 32:
            temp_text = connection_string.replace("\n", "").replace(" ", "")[0:32]

            if temp_text.startswith("{'type':'FeatureCollection'"):
                return True
            if temp_text.startswith('{"type":"FeatureCollection"'):
                return True

        return False


class GdalUtils:
    """
    Provides generic GDAL/OGR utility functions.
    """
    @staticmethod
    def get_gdal_driver(connection_string: str):
        """
        Return the GDAL Driver that supports the specified DataSource.
        """
        from geodataflow.spatial.gdalenv import GdalEnv
        gdal = GdalEnv.default().gdal()

        file_name, file_ext = os.path.splitext(connection_string)
        if file_name and file_ext:
            temp_key = os.path.basename(connection_string)
            temp_pos = temp_key.find('.')
            file_ext = temp_key[temp_pos:]

        file_ext = file_ext.lower()

        if file_ext in ['.tiff', '.tif']:
            return gdal.GetDriverByName('Gtiff')
        if file_ext in ['.jpeg', '.jpg']:
            return gdal.GetDriverByName('JPEG')
        if file_ext == '.png':
            return gdal.GetDriverByName('PNG')
        if file_ext == '.vrt':
            return gdal.GetDriverByName('VRT')
        if file_ext == '.gpkg':
            return gdal.GetDriverByName('GPKG')
        if file_ext == '.jp2':
            driver = gdal.GetDriverByName('JP2OpenJPEG')
            driver = driver if driver else gdal.GetDriverByName('JP2ECW')
            return driver

        raise Exception('Unknown GDAL Driver for the ConnectionString="{}"'.format(connection_string))

    @staticmethod
    def get_ogr_driver(connection_string: str):
        """
        Return the OGR Driver that supports the specified DataSource.
        """
        from geodataflow.spatial.gdalenv import GdalEnv
        ogr = GdalEnv.default().ogr()

        if DataUtils.represents_json_feature_collection(connection_string):
            return ogr.GetDriverByName('GeoJSON')
        if connection_string.startswith('PG:'):
            return ogr.GetDriverByName('PostgreSQL')

        file_name, file_ext = os.path.splitext(connection_string)
        if file_name and file_ext:
            temp_key = os.path.basename(connection_string)
            temp_pos = temp_key.find('.')
            file_ext = temp_key[temp_pos:]

        file_ext = file_ext.lower()

        if file_ext == '.gpkg':
            return ogr.GetDriverByName('GPKG')
        if file_ext in ['.shp', '.shz', '.shp.zip']:
            return ogr.GetDriverByName('ESRI Shapefile')
        if file_ext in ['.json', '.geojson']:
            return ogr.GetDriverByName('GeoJSON')
        if file_ext in ['.kml', '.kmz']:
            return ogr.GetDriverByName('KML')
        if file_ext in ['.csv']:
            return ogr.GetDriverByName('CSV')
        if file_ext in ['.fgb']:
            return ogr.GetDriverByName('FlatGeobuf')

        raise Exception('Unknown OGR Driver for the ConnectionString="{}"'.format(connection_string))

    @staticmethod
    def test_gdal_capability(connection_string: str, capability: StoreCapabilities) -> bool:
        """
        Returns if any GDAL Driver supports the specified named Capability.
        """
        try:
            driver = GdalUtils.get_gdal_driver(connection_string)
            if driver is None:
                return False

            from geodataflow.spatial.gdalenv import GdalEnv
            gdal = GdalEnv.default().gdal()

            if capability == StoreCapabilities.READ:
                metadata = driver.GetMetadata()
                is_ok = gdal.DCAP_OPEN in metadata and metadata[gdal.DCAP_OPEN] == 'YES'
                return is_ok
            if capability == StoreCapabilities.WRITE or capability == StoreCapabilities.CREATE:
                metadata = driver.GetMetadata()
                is_ok = (gdal.DCAP_CREATE in metadata and metadata[gdal.DCAP_CREATE] == 'YES') or \
                        (gdal.DCAP_CREATECOPY in metadata and metadata[gdal.DCAP_CREATECOPY] == 'YES')
                return is_ok

            return False
        except Exception as e:
            logging.warning(
                'Error getting the GDAL Driver of the ConnectionString "{}", Cause="{}".'
                .format(connection_string, str(e)))

            return False

    @staticmethod
    def test_ogr_capability(connection_string: str, capability: StoreCapabilities) -> bool:
        """
        Returns if any OGR Driver supports the specified named Capability.
        """
        try:
            driver = GdalUtils.get_ogr_driver(connection_string)
            if driver is None:
                return False

            from geodataflow.spatial.gdalenv import GdalEnv
            ogr = GdalEnv.default().ogr()

            if capability == StoreCapabilities.READ:
                return True
            if capability == StoreCapabilities.WRITE:
                is_ok = driver.TestCapability(ogr.ODrCCreateDataSource)
                return is_ok
            if capability == StoreCapabilities.CREATE:
                is_ok = driver.TestCapability(ogr.ODrCCreateDataSource)
                return is_ok

            return False
        except Exception as e:
            logging.warning(
                'Error getting the OGR Driver of the specified ConnectionString "{}", Cause="{}".'
                .format(connection_string, str(e)))

            return False

    @staticmethod
    def get_ogr_connection_string(connection_string: str) -> str:
        """
        Return the normalized OGR Connection String that supports the specified DataSource.
        """
        if os.path.exists(connection_string):
            file_ext = os.path.splitext(os.path.basename(connection_string))[1]
            file_ext = file_ext.lower()

            if file_ext in ['.kmz', '.zip']:
                from zipfile import ZipFile
                import fnmatch
                import re
                re_ob = re.compile('|'.join(
                    fnmatch.translate('*.' + f_ext) for f_ext in ['kml', 'shp', 'gpkg', 'geojson'])
                )

                with ZipFile(connection_string, mode='r') as zf:
                    for zc in zf.infolist():
                        if re_ob.match(zc.filename):
                            return '/vsizip/' + connection_string + '/' + zc.filename

        return connection_string

    @staticmethod
    def get_spatial_reference(crs_def):
        """
        Returns the OGR SpatialReference from the specified CRS/EPSG/WKT definition.
        """
        from osgeo import osr

        crs = osr.SpatialReference()
        if hasattr(crs, 'SetAxisMappingStrategy'):
            crs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        if isinstance(crs_def, int):
            crs.ImportFromEPSG(crs_def)
            return crs
        if isinstance(crs_def, str):
            if crs_def.isdigit():
                crs.ImportFromEPSG(int(crs_def))
            elif crs_def.startswith('EPSG:'):
                crs.ImportFromEPSG(int(crs_def[5:]))
            else:
                crs.ImportFromWkt(crs_def)

            return crs

        return crs

    @staticmethod
    def get_spatial_srid(spatial_ref) -> int:
        """
        Returns the EPSG SRID code of the specified SRS SpatialReference.
        """
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
            logging.debug('Error reading the SRID of the CRS="{}", Cause="{}"'.format(str(spatial_ref), e))

        return srid


class GeometryUtils:
    """
    Provides generic CRS/Geometry utility functions.
    """
    @staticmethod
    def get_spatial_crs(crs_def: Union[int, str, pj.CRS]) -> pj.CRS:
        """
        Returns the pyproj CRS from the specified CRS/EPSG/WKT definition.
        """
        if isinstance(crs_def, pj.CRS):
            return crs_def
        if isinstance(crs_def, int):
            return pj.CRS.from_epsg(crs_def)
        if isinstance(crs_def, str) and crs_def.isdigit():
            return pj.CRS.from_epsg(crs_def)

        return pj.CRS.from_string(crs_def)

    @staticmethod
    def create_transform_function(source_crs: Union[int, str, pj.CRS],
                                  target_crs: Union[int, str, pj.CRS]
                                  ) -> Callable[[BaseGeometry], BaseGeometry]:
        """
        Returns a function to transform Geometries between the specified Spatial Reference Systems.
        """
        if not isinstance(source_crs, pj.CRS):
            source_crs = GeometryUtils.get_spatial_crs(source_crs)
        if not isinstance(target_crs, pj.CRS):
            target_crs = GeometryUtils.get_spatial_crs(target_crs)

        if source_crs and target_crs and source_crs.to_epsg() != target_crs.to_epsg():
            transform_fn = pj.Transformer.from_crs(source_crs, target_crs, always_xy=True).transform
            target_srid = target_crs.to_epsg()
        else:
            transform_fn = None
            target_srid = 0

        def transform_fn_(geometry: BaseGeometry) -> BaseGeometry:
            if transform_fn:
                geometry = transform(transform_fn, geometry)
                geometry = geometry.with_srid(target_srid)

            return geometry

        return transform_fn_

    @staticmethod
    def get_srid(obj: Union[int, object, pj.CRS]) -> int:
        """
        Returns the SRID of this Geometry.
        """
        if isinstance(obj, int):
            return obj
        if isinstance(obj, BaseGeometry):
            return lgeos.GEOSGetSRID(obj._geom)
        if isinstance(obj, pj.CRS):
            return obj.to_epsg()
        if hasattr(obj, 'srid'):
            return getattr(obj, 'srid')

        return 0

    @staticmethod
    def set_srid(geometry, obj: Union[int, object, pj.CRS]):
        """
        Set the SRID to specified Geometry.
        """
        srid = GeometryUtils.get_srid(obj)
        if srid:
            if isinstance(geometry, BaseGeometry):
                lgeos.GEOSSetSRID(geometry._geom, srid)
            else:
                setattr(geometry, 'srid', srid)

        return geometry

    @staticmethod
    def create_geometry_from_bbox(x_min: float, y_min: float, x_max: float, y_max: float) -> Polygon:
        """
        Returns the Geometry from the specified BBOX.
        INFO:
            This function adds four mid-point vertices to the Geometry because the transform
            between EPSG:4326 and EPSG:3035 generates curvilinear borders.
        """
        coordinates = [
            (x_min, y_min),
            (x_min + 0.5 * (x_max - x_min), y_min),
            (x_max, y_min),
            (x_max, y_min + 0.5 * (y_max - y_min)),
            (x_max, y_max),
            (x_max - 0.5 * (x_max - x_min), y_max),
            (x_min, y_max),
            (x_min, y_max - 0.5 * (y_max - y_min)),
            (x_min, y_min)
        ]
        return Polygon(coordinates)

    @staticmethod
    def clamp_envelope(envelope: Tuple[float, float, float, float],
                       pixel_size_x: float,
                       pixel_size_y: float,
                       padding_val: int = 0,
                       minimum_ts: int = 0) -> Tuple[float, float, float, float]:
        """
        Clamp the specified Envelope aligned to current GRID.
        """
        x_min = int(envelope[0] / pixel_size_x) * pixel_size_x
        y_min = int(envelope[1] / pixel_size_y) * pixel_size_y
        x_max = int(envelope[2] / pixel_size_x) * pixel_size_x
        y_max = int(envelope[3] / pixel_size_y) * pixel_size_y

        if x_max < envelope[2]:
            x_max += pixel_size_x
        if y_max < envelope[3]:
            y_max += pixel_size_y

        # ... forcing the Envelope have a minimum size of tile/image.
        if minimum_ts:
            num_pixel_x = (x_max - x_min) / pixel_size_x
            num_pixel_y = (y_max - y_min) / pixel_size_y
            pad_pixel_x = num_pixel_x - minimum_ts
            pad_pixel_y = num_pixel_y - minimum_ts

            if pad_pixel_x < 0:
                pad_pixel_x = int(abs(pad_pixel_x) * 0.5)
                x_min = x_min - pixel_size_x * pad_pixel_x
                x_max = x_max + pixel_size_x * (1 + pad_pixel_x)
            if pad_pixel_y < 0:
                pad_pixel_y = int(abs(pad_pixel_y) * 0.5)
                y_min = y_min - pixel_size_y * pad_pixel_y
                y_max = y_max + pixel_size_y * (1 + pad_pixel_y)

        # ... applying a "little" padding ot border of the Envelope.
        if padding_val:
            x_min = x_min - padding_val * pixel_size_x
            y_min = y_min - padding_val * pixel_size_y
            x_max = x_max + padding_val * pixel_size_x
            y_max = y_max + padding_val * pixel_size_y

        return [x_min, y_min, x_max, y_max]


# Inject methods to manage SRID/CRS info in Geometry types.
BaseGeometry.with_srid = GeometryUtils.set_srid
BaseGeometry.get_srid = GeometryUtils.get_srid
