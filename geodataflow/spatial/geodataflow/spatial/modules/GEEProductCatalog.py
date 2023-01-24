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

import datetime
import importlib
import requests
from typing import Dict, List, Iterable
from shapely.geometry import mapping as shapely_mapping, shape as shapely_shape
from shapely.geometry.polygon import Polygon
from geodataflow.core.common import DateUtils
from geodataflow.pipeline.basictypes import AbstractFilter

# List of available GEE Datasets.
GEE_CATALOG_URL = \
    'https://raw.githubusercontent.com/samapriya/Earth-Engine-Datasets-List/master/gee_catalog.json'


def search_gee_datasets() -> List[Dict]:
    """
    Discover list of available GEE Datasets.
    """
    try:
        response = requests.get(GEE_CATALOG_URL)
        catalog_list = response.json()
        datasets = [dataset for dataset in catalog_list if dataset['type'] == 'image_collection']
        datasets = sorted(datasets, key=lambda obj: obj['title'], reverse=False)
        return datasets
    except Exception:
        return []


class GEEProductCatalog(AbstractFilter):
    """
    The Filter extracts Metadata from GEE Collections via spatial & alphanumeric filters.
    """
    GEE_CATALOG_DATASET = search_gee_datasets() if importlib.util.find_spec('ee') else []

    def __init__(self):
        AbstractFilter.__init__(self)
        self._ee_api = None
        self.dataset = 'COPERNICUS/S2_SR_HARMONIZED'
        self.startDate = None
        self.endDate = None
        self.closestToDate = None
        self.windowDate = None
        self.filter = None
        self.preserveInputCrs = True

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
        return 'EarthEngine Catalog'

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'EO STAC Imagery'

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Extracts Metadata from GEE Collections via spatial & alphanumeric filters.'

    def params(self) -> Dict:
        """
        Returns the declaration of parameters supported by this Module.
        """
        dataset_labels = []
        dataset_keys = []

        for dataset in GEEProductCatalog.GEE_CATALOG_DATASET:
            dataset_keys.append(dataset['id'])
            dataset_labels.append(dataset['title'])

        return {
            'dataset': {
                'description': 'Earth Engine Dataset from which to fetch data.',
                'dataType': 'string',
                'default': 'COPERNICUS/S2_SR_HARMONIZED',
                'options': dataset_keys,
                'labels': dataset_labels
            },
            'startDate': {
                'description': 'Start date of images to fetch (Optional). "$TODAY()" is supported.',
                'dataType': 'date'
            },
            'endDate': {
                'description': 'End date of images to fetch (Optional). "$TODAY()" is supported.',
                'dataType': 'date'
            },
            'closestToDate': {
                'description':
                    'Select only those images which Date is the closest to the specified (Optional).',
                'dataType': 'date'
            },
            'windowDate': {
                'description':
                    'Days around "closestToDate" when "startDate" and "endDate" are not specified.',
                'dataType': 'int',
                'default': 5
            },
            'filter': {
                'description': 'Attribute filter string of images to fetch (Optional).',
                'dataType': 'filter'
            },
            'preserveInputCrs': {
                'description': 'Preserve input CRS, otherwise Geometries are transformed to "EPSG:4326".',
                'dataType': 'bool',
                'default': True
            }
        }

    def starting_run(self, schema_def, pipeline, processing_args, fetch_fields: bool = True):
        """
        Starting a new Workflow on Geospatial data.
        """
        from geodataflow.core.schemadef import DataType, GeometryType, FieldDef
        from geodataflow.spatial.commonutils import GeometryUtils

        envelope = schema_def.envelope if schema_def.envelope else [0, -90, 360, 90]
        geometry = GeometryUtils.create_geometry_from_bbox(envelope[0], envelope[1], envelope[2], envelope[3])

        # Fetch schema from first GEE Image.
        field_dict = {f.name: f for f in schema_def.fields}
        new_fields = [
            FieldDef(name='productType', data_type=DataType.String),
            FieldDef(name='productDate', data_type=DataType.String)
        ]
        if fetch_fields:
            ee = self.ee_initialize()

            ee_dataset = ee.ImageCollection(self.dataset)
            ee_image = ee_dataset.first()
            ee_properties = self.ee_object_props(ee_image)
            properties = ee_properties.getInfo()
            #
            for name, value in properties.items():
                if not field_dict.get(name) and \
                   not name.startswith('system:') and \
                   not isinstance(value, list) and \
                   not isinstance(value, dict):
                    new_fields.append(FieldDef(name=name, data_type=DataType.to_data_type(value)))

        schema_def = schema_def.clone()
        schema_def.geometryType = GeometryType.Polygon
        schema_def.input_srid = schema_def.srid
        schema_def.input_crs = schema_def.crs
        schema_def.fields += new_fields

        # Redefine CRS when distinct of EPSG:4326?
        if not self.preserveInputCrs and schema_def.srid != 4326 and schema_def.envelope:
            from pyproj import CRS
            from geodataflow.spatial.commonutils import GeometryUtils

            schema_def.srid = 4326
            schema_def.crs = CRS.from_epsg(4326)

            transform_fn = GeometryUtils.create_transform_function(schema_def.input_crs, schema_def.crs)
            geometry = GeometryUtils.create_geometry_from_bbox(*schema_def.envelope)
            geometry = transform_fn(geometry)
            schema_def.envelope = list(geometry.bounds)

        return schema_def

    def run(self, feature_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        schema_def = self.pipeline_args.schema_def

        # Transform output Geometries to input CRS?
        from geodataflow.spatial.commonutils import GeometryUtils
        inv_transform_fn = \
            GeometryUtils.create_transform_function(4326, schema_def.input_crs) \
            if self.preserveInputCrs else None

        ee = self.ee_initialize()

        def ee_iter_function(ee_image, new_list):
            """
            Iterating ee.Image's of one ee.ImageCollection().
            """
            new_list = ee.List(new_list)
            ee_image_props = self.ee_object_props(ee_image)
            return ee.List(new_list.add(ee_image_props))

        # Query & fetch GEE imagery from Google Earth Engine...
        index = 0
        for feature in feature_store:
            geometry = feature.geometry

            ee_dataset = self.ee_fetch_dataset(geometry, False)
            ee_images = ee_dataset.iterate(ee_iter_function, ee.List([]))

            for image_props in self.pass_images(ee_images.getInfo()):
                properties = feature.properties.copy()

                properties['productType'] = self.dataset
                properties['productDate'] = image_props['IMAGE_DATE']

                for name, value in image_props.items():
                    if not name.startswith('system:') and \
                       not isinstance(value, list) and not isinstance(value, dict):
                        properties[name] = value

                g = image_props.get('system:footprint')
                if g:
                    g = shapely_shape(g)
                    g = Polygon(g) if g.geom_type == 'LinearRing' else g
                    g = g.with_srid(4326)
                    g = inv_transform_fn(g) if inv_transform_fn else g
                else:
                    g = geometry

                product = type('Feature', (object,), {
                    'type': 'Feature',
                    'fid': index,
                    'properties': properties,
                    'geometry': g
                })
                yield product
                index += 1

        pass

    def pass_images(self, images: Iterable[object]) -> Iterable[object]:
        """
        Returns only those GEE Images that match custom criteria (e.g. "closestToDate").
        """
        if self.closestToDate:
            closest_time = datetime.datetime.strptime(self.closestToDate, '%Y-%m-%d')
            temp_dict = dict()
            temp_list = list()

            for image in images:
                product_date = image.get('IMAGE_DATE')
                product_time = datetime.datetime.strptime(product_date, '%Y-%m-%d')
                product_diff = abs(product_time - closest_time).days
                temp_list.append((product_date, product_time, product_diff))
                curr_list = temp_dict.get(product_date, [])
                curr_list.append(image)
                temp_dict[product_date] = curr_list

            for best_item in sorted(temp_list, key=lambda tup: tup[2], reverse=False):
                best_date = best_item[0]
                best_list = temp_dict[best_date]
                return best_list

        return images

    def ee_initialize(self):
        """
        Returns a GEE environemt.
        """
        if self._ee_api is None:
            import ee

            # Authenticates and initializes Earth Engine.
            try:
                ee.Initialize()
            except Exception:
                # Get credentials:
                # https://developers.google.com/earth-engine/guides/python_install-conda#get_credentials
                ee.Authenticate()
                ee.Initialize()

            self._ee_api = ee
            #
        return self._ee_api

    def ee_object_props(self, ee_object):
        """
        Get the properties of the specified GEE object.
        """
        ee = self.ee_initialize()

        if isinstance(ee_object, ee.Image):
            image = ee_object

            prop_names = image.propertyNames()
            values = prop_names.map(lambda prop_name: image.get(prop_name))
            dictionary = ee.Dictionary.fromLists(prop_names, values)

            image_date = ee.Date(image.get('system:time_start')).format('yyyy-MM-dd')
            dictionary = dictionary.set('IMAGE_DATE', image_date)

            band_names = image.bandNames()
            scales = band_names.map(lambda b: image.select([b]).projection().nominalScale())
            scale = ee.Algorithms.If(scales.distinct().size().gt(1),
                                     ee.Dictionary.fromLists(ee.List(band_names), scales),
                                     scales.get(0))

            dictionary = dictionary.set('system:band_scales', scale)
            return dictionary

        if isinstance(ee_object, ee.Feature):
            feature = ee_object

            prop_names = feature.propertyNames()
            values = prop_names.map(lambda prop_name: feature.get(prop_name))

            return ee.Dictionary.fromLists(prop_names, values)

        if isinstance(ee_object, ee.ImageCollection):
            dataset = ee_object

            geometry = dataset.geometry()
            count = dataset.size()
            keys = dataset.aggregate_array('system:id')

            # Get list of dates of current Collection.
            dates = dataset \
                .map(lambda img: ee.Feature(None, {'date': img.date().format('yyyy-MM-dd')})) \
                .distinct('date') \
                .aggregate_array('date')

            prop_names = ee.List(['geometry', 'dates', 'keys', 'count'])
            values = ee.List([geometry, dates, keys, count])

            return ee.Dictionary.fromLists(prop_names, values)

        return ee.Dictionary({})

    def ee_fetch_dataset(self, geometry, clip_images: bool = True):
        """
        Fetch the GEE ImageCollection according to current settings.
        """
        ee = self.ee_initialize()

        start_date, final_date = \
            DateUtils.parse_date_range(self.startDate, self.endDate, self.closestToDate, self.windowDate)

        start_date = start_date.strftime('%Y-%m-%d')
        final_date = final_date.strftime('%Y-%m-%d')

        from geodataflow.spatial.commonutils import GeometryUtils
        transform_fn = GeometryUtils.create_transform_function(geometry.get_srid(), 4326)
        geometry = transform_fn(geometry)
        geo_json = shapely_mapping(geometry)

        # Define settings for querying...
        ee_dataset = ee.ImageCollection(self.dataset)
        ee_dataset = ee_dataset.filterBounds(geo_json).filterDate(start_date, final_date)

        if self.filter:
            ee_dataset = ee_dataset.filter(self.filter)

        if clip_images:
            ee_dataset = ee_dataset.map(lambda image: image.clip(geo_json))

        ee_dataset = ee_dataset.sort('system:time_start')
        return ee_dataset
