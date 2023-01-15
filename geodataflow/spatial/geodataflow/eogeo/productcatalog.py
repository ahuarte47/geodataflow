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
from typing import Dict, Iterable, Type
from geodataflow.core.modulemanager import ModuleManager


class ProductDriverApi:
    """
    Defines an interface to implement EO Products Providers.
    """
    def __init__(self):
        pass

    @staticmethod
    def is_available() -> bool:
        """
        Indicates that this Module is available for use, some modules may depend
        on the availability of other third-party packages.
        """
        return True

    def name(self) -> str:
        """
        Returns the Name of the Driver.
        """
        raise NotImplementedError('Interface Class has not to implement any method.')

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
        raise NotImplementedError('Interface Class has not to implement any method.')


class ProductCatalog:
    """
    Provides methods to search and download EO products (Copernicus Open Access Hub, DIAS, AWS, ...).
    """
    def __init__(self):
        self._modules: Dict[str, Type] = None
        self._drivers: Dict[str, Type] = None

    def available_drivers(self):
        """
        Returns the available list of EO Products Provider drivers.
        """
        if self._drivers:
            return self._drivers

        modules_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules')

        manager = ModuleManager(abstract_types=(ProductDriverApi,))
        self._modules = manager.load_modules(modules_folders=[modules_folder])

        self._drivers = dict()
        for ty in self._modules.values():
            driver_ob = ty()
            self._drivers[driver_ob.name().lower()] = driver_ob

        return self._drivers.values()

    def get_driver(self, driver_name: str):
        """
        Returns the EO Products Provider driver of specified name.
        """
        if not self._drivers:
            _ = self.available_drivers()

        return self._drivers.get(driver_name.lower())

    def search(self,
               driver: str,
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
        driver_ob = self.get_driver(driver_name=driver)

        for product_ob in driver_ob.search(
                provider=provider, config=config, product_type=product_type, area=area, date=date, **keywords
                ):
            product_ob = ProductCatalog._normalize_product(product_type, product_ob)
            yield product_ob

        pass

    @staticmethod
    def _normalize_product(product_type: str, product: object) -> object:
        """
        Normalize properties of specified EOProduct from different EO Providers.
        """
        product.geometry = product.geometry.with_srid(4326)
        return product
