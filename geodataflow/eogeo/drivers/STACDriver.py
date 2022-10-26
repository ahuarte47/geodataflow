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

import json
import datetime
from typing import Dict, Iterable

from geodataflow.eogeo.productcatalog import ProductDriverApi


class STACDriver(ProductDriverApi):
    """
    Implements an EO Products Provider Driver of EO/STAC imagery collections.
    """
    def __init__(self):
        ProductDriverApi.__init__(self)

    def name(self) -> str:
        """
        Returns the Name of the Driver.
        """
        return 'STAC'

    def search(self,
               provider: str,
               config: Dict,
               product_type: str,
               area=None,
               date=None,
               **keywords) -> Iterable[object]:
        """
        Search the available EO products with the coordinates of an area, a date interval
        and any other search keywords accepted by the OpenSearch API.
        See:
        https://scihub.copernicus.eu/twiki/do/view/SciHubUserGuide/FullTextSearch?redirectedfrom=SciHubUserGuide.3FullTextSearch
        """
        import requests

        if not provider:
            raise Exception('API Endpoint of Provider not specified!')

        from shapely.geometry import mapping as shapely_mapping, shape as shapely_shape
        geom_as_json = shapely_mapping(area)

        # Fix Date range: (date >= start && date <= end)!!!
        start_date, end_date = date
        start_date, end_date = \
            start_date.strftime('%Y-%m-%d'), (end_date+datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        # Send POST request.
        headers = {
            'Content-Type': 'application/json',
            'Accept-Encoding': 'gzip',
            'Accept': 'application/geo+json',
        }
        query = {
            'collections': [product_type],
            'datetime': '{}/{}'.format(start_date, end_date),
            'limit': keywords.get('limit', 200),
            'filter': keywords.get('filter', ''),
            'intersects': geom_as_json
        }
        response = requests.request('POST', provider, headers=headers, json=query)
        if response.status_code != 200:
            raise Exception(response.text)

        # Parse input EO Products.
        for index, product_ob in enumerate(json.loads(response.text).get('features', [])):
            geometry = product_ob.get('geometry')
            geometry = shapely_shape(geometry)

            feature = type('Feature', (object,), {
                'type': 'Feature',
                'fid': index,
                'properties': product_ob.get('properties'),
                'geometry': geometry,
                'assets': product_ob.get('assets')
            })
            yield feature

        pass
