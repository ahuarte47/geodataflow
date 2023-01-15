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

from geodataflow.core.capabilities import StoreCapabilities
from geodataflow.pipeline.moduledef import AbstractModule


class AbstractFilter(AbstractModule):
    """
    Abstract Filter that operates on items of Geospatial data.
    """
    def __init__(self):
        AbstractModule.__init__(self)
        self.classType = 'filter'


class AbstractReader(AbstractModule):
    """
    Abstract Module that reads items from a Geospatial DataSource.
    """
    def __init__(self):
        AbstractModule.__init__(self)
        self.classType = 'reader'

    def test_capability(self, connection_string: str, capability: StoreCapabilities) -> bool:
        """
        Returns if this Module supports the specified ConnectionString and named StoreCapability.
        """
        return False


class AbstractWriter(AbstractModule):
    """
    Abstract Module that writes items to a Geospatial DataStore.
    """
    def __init__(self):
        AbstractModule.__init__(self)
        self.classType = 'writer'

    def test_capability(self, connection_string: str, capability: StoreCapabilities) -> bool:
        """
        Returns if this Module supports the specified ConnectionString and named StoreCapability.
        """
        return False
