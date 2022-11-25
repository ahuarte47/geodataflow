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
import datetime
from typing import Dict, Iterable

from geodataflow.core.common import CaseInsensitiveDict
from geodataflow.pipeline.basictypes import AbstractFilter
from geodataflow.eogeo.productcatalog import ProductCatalog


class EOProductCatalog(AbstractFilter):
    """
    The Filter extracts Metadata from EO/STAC Collections via spatial & alphanumeric filters.
    """
    def __init__(self):
        AbstractFilter.__init__(self)
        self.driver = 'STAC'
        self.provider = 'https://earth-search.aws.element84.com/v0/search'
        self.product = 'sentinel-s2-l2a-cogs'
        self.startDate = None
        self.endDate = None
        self.closestToDate = None
        self.windowDate = None
        self.filter = None
        self.preserveInputCrs = True

    def alias(self) -> str:
        """
        Returns the Human alias-name of this Module.
        """
        return 'Catalog'

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Extracts Metadata from EO/STAC Collections via spatial & alphanumeric filters.'

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'EO STAC Imagery'

    def params(self) -> Dict:
        """
        Returns the declaration of parameters supported by this Module.
        """
        eo_catalog = ProductCatalog()
        drivers = [driver.name().upper() for driver in eo_catalog.available_drivers()]

        return {
            'driver': {
                'description': 'Driver class name that implements EO Providers.',
                'dataType': 'string',
                'default': 'STAC',
                'options': drivers,
                'labels': drivers
            },
            'provider': {
                'description': 'Provider name or API Endpoint that provides info about EO Products.',
                'dataType': 'string',
                'default': 'https://earth-search.aws.element84.com/v0/search'
            },
            'product': {
                'description': 'EO Product type or Collection from which to fetch data.',
                'dataType': 'string',
                'default': 'sentinel-s2-l2a-cogs'
            },
            'startDate': {
                'description': 'Start date of EO Products to fetch (Optional). "$TODAY()" is supported.',
                'dataType': 'date'
            },
            'endDate': {
                'description': 'End date of EO Products to fetch (Optional). "$TODAY()" is supported.',
                'dataType': 'date'
            },
            'closestToDate': {
                'description':
                    'Select only those EO Products which Date is the closest to the specified (Optional).',
                'dataType': 'date'
            },
            'windowDate': {
                'description':
                    'Days around "closestToDate" when "startDate" and "endDate" are not specified.',
                'dataType': 'int',
                'default': 5
            },
            'filter': {
                'description': 'Attribute filter string of EO Products to fetch (Optional).',
                'dataType': 'filter'
            },
            'preserveInputCrs': {
                'description': 'Preserve input CRS, otherwise Geometries are transformed to "EPSG:4326".',
                'dataType': 'bool',
                'default': True
            }
        }

    def fetch_products(self, geometry, input_crs, app_config: Dict, limit: int = 1000) -> Iterable:
        """
        Ferch EO Products using current settings.
        """
        today_date = datetime.date.today()

        if isinstance(self.startDate, str):
            start_date = today_date \
                if self.startDate.upper() == '$TODAY()' \
                else datetime.datetime.strptime(self.startDate, '%Y-%m-%d')

        elif self.startDate is None and self.closestToDate:
            temps_time = datetime.datetime.strptime(self.closestToDate, '%Y-%m-%d')
            start_date = self.closestToDate \
                if not self.windowDate \
                else (temps_time - datetime.timedelta(days=self.windowDate)).strftime('%Y-%m-%d')

            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_date = self.startDate if self.startDate else today_date

        if isinstance(self.endDate, str):
            final_date = today_date \
                if self.endDate.upper() == '$TODAY()' \
                else datetime.datetime.strptime(self.endDate, '%Y-%m-%d')

        elif self.startDate is None and self.closestToDate:
            temps_time = datetime.datetime.strptime(self.closestToDate, '%Y-%m-%d')
            final_date = self.closestToDate \
                if not self.windowDate \
                else (temps_time + datetime.timedelta(days=self.windowDate)).strftime('%Y-%m-%d')

            final_date = datetime.datetime.strptime(final_date, '%Y-%m-%d')
        else:
            final_date = self.endDate if self.endDate else today_date

        product_filter = dict()
        if self.filter:
            for item in self.filter.replace('==', '=').split(';'):
                pair = item.split('=')
                product_filter[pair[0].strip()] = pair[1].strip()

        # Search available EO products according the current AOI-TimeRange criteria.
        eo_catalog = ProductCatalog()

        # Transform Geometries to EPSG:4326 for searching EO Products?
        from geodataflow.geoext.commonutils import GeometryUtils
        transform_fn = GeometryUtils.create_transform_function(input_crs, 4326)
        geometry = transform_fn(geometry)

        params = dict(
            driver=self.driver,
            provider=self.provider,
            config=app_config,
            product_type=self.product,
            area=geometry,
            date=(start_date, final_date),
            limit=limit
        )
        if len(product_filter) > 0:
            params.update(product_filter)

        # Search EO Products!
        for product in eo_catalog.search(**params):
            yield product

        pass

    def starting_run(self, schema_def, pipeline, processing_args):
        """
        Starting a new Workflow on Geospatial data.
        """
        from geodataflow.core.schemadef import DataType, GeometryType, FieldDef
        from geodataflow.geoext.commonutils import GeometryUtils

        envelope = schema_def.envelope if schema_def.envelope else [0, -90, 360, 90]
        geometry = GeometryUtils.create_geometry_from_bbox(envelope[0], envelope[1], envelope[2], envelope[3])

        # Fetch schema from first EO Product.
        app_config = pipeline.config
        field_dict = {f.name: f for f in schema_def.fields}
        new_fields = [
            FieldDef(name='gdf:product_date', data_type=DataType.String)
        ]
        for product in self.fetch_products(geometry, schema_def.crs, app_config, limit=1):
            properties = product.properties

            for name, value in properties.items():
                if not field_dict.get(name):
                    new_fields.append(FieldDef(name=name, data_type=DataType.to_data_type(value)))

        schema_def = schema_def.clone()
        schema_def.geometryType = GeometryType.Polygon
        schema_def.input_srid = schema_def.srid
        schema_def.input_crs = schema_def.crs
        schema_def.fields += new_fields

        # Redefine CRS when distinct of EPSG:4326?
        if not self.preserveInputCrs and schema_def.srid != 4326 and schema_def.envelope:
            from pyproj import CRS
            from geodataflow.geoext.commonutils import GeometryUtils

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
        app_config = self.pipeline_args.config

        report_info = {
            'driver': self.driver,
            'provider': self.provider,
            'productType': self.product,
            'bounds': '',
            'startDate': self.startDate,
            'endDate': self.endDate,
            'closestToDate': self.closestToDate if self.closestToDate else '',
            'filter': self.filter if self.filter else '',
            'availableDates': [],
            'selectedDate': ''
        }

        # Transform Geometries to EPSG:4326 for searching EO Products?
        from geodataflow.geoext.commonutils import GeometryUtils
        inv_transform_fn = \
            GeometryUtils.create_transform_function(4326, schema_def.input_crs) \
            if self.preserveInputCrs else None

        for feature in feature_store:
            geometry = feature.geometry
            report_info['bounds'] = 'BBOX{}'.format(geometry.bounds)

            # Search EO Products!
            eo_products = [
                self.normalize_product(product, feature)
                for product in self.fetch_products(geometry, schema_def.input_crs, app_config, limit=1000)
            ]
            logging.info("Available {} EO Products for type '{}'.".format(len(eo_products), self.product))

            available_dates = set([product.properties.get('gdf:product_date') for product in eo_products])
            report_info['availableDates'] = list(available_dates)

            # Return results.
            for product in self.pass_products(eo_products):
                report_info['selectedDate'] = product.properties.get('gdf:product_date')
                if inv_transform_fn:
                    product.geometry = inv_transform_fn(product.geometry)

                yield product
            #

        report_context = \
            processing_args.reportContext if hasattr(processing_args, 'reportContext') else None
        if report_context:
            setattr(report_context, self.className, report_info)

        pass

    def pass_products(self, products: Iterable[object]) -> Iterable[object]:
        """
        Returns only those EO Products that match custom criteria (e.g. "closestToDate").
        """
        if self.closestToDate:
            closest_time = datetime.datetime.strptime(self.closestToDate, '%Y-%m-%d')
            temp_dict = dict()
            temp_list = list()

            for product in products:
                product_date = product.properties.get('gdf:product_date')
                product_time = datetime.datetime.strptime(product_date, '%Y-%m-%d')
                product_diff = abs(product_time - closest_time).days
                temp_list.append((product_date, product_time, product_diff))
                curr_list = temp_dict.get(product_date, [])
                curr_list.append(product)
                temp_dict[product_date] = curr_list

            for best_item in sorted(temp_list, key=lambda tup: tup[2], reverse=False):
                best_date = best_item[0]
                best_list = temp_dict[best_date]
                return best_list

        return products

    def normalize_product(self, product: object, feature: object) -> object:
        """
        Normalize properties of specified EOProduct.
        """
        case_props = CaseInsensitiveDict(product.properties)
        attributes = feature.properties.copy()

        product_date = \
            case_props.get('startTimeFromAscendingNode') or \
            case_props.get('beginPosition') or \
            case_props.get('ingestionDate') or \
            case_props.get('publicationDate') or \
            case_props.get('datetime')

        attributes['gdf:product_date'] = product_date[0:10]

        for name, value in product.properties.items():
            attributes[name] = value if not isinstance(value, list) else ','.join([str(v) for v in value])

        product.areaOfInterest = feature
        product.properties = attributes

        return product
