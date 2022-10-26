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
import datetime
from typing import Dict, Iterable

from geodataflow.eogeo.productcatalog import ProductDriverApi


class EODAGDriver(ProductDriverApi):
    """
    Implements an EO Products Provider Driver using the EODAG module (https://eodag.readthedocs.io/).
    """
    def __init__(self):
        ProductDriverApi.__init__(self)

    def name(self) -> str:
        """
        Returns the Name of the Driver.
        """
        return 'EODAG'

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
        if not provider:
            raise Exception('Provider not specified!')
        if not config:
            config = dict()

        provider = provider.lower()

        for k in config.keys():
            if k.startswith('EODAG__'):
                os.environ[k] = config.get(k)

        from eodag.api.core import EODataAccessGateway
        dag = EODataAccessGateway()
        dag.set_preferred_provider(provider)

        # Fix Date range: (date >= start && date <= end)!!!
        start_date, end_date = date
        start_date, end_date = \
            start_date.strftime('%Y-%m-%d'), (end_date+datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        products = dag.search_all(
            productType=product_type,
            start=start_date,
            end=end_date,
            geom=area,
            items_per_page=None,
            **keywords
        )
        for index, product_ob in enumerate(products):
            #
            feature = type('Feature', (object,), {
                'type': 'Feature',
                'fid': index,
                'properties': product_ob.properties,
                'geometry': product_ob.geometry,
                'assets': product_ob.assets
            })
            yield feature

        pass
