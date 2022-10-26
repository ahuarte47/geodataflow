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

from geodataflow.pipeline.basictypes import AbstractFilter


class FeatureCache(AbstractFilter):
    """
    The Filter caches data of inputs to speedup the management of repetitive invocations of Modules.
    """
    def __init__(self):
        AbstractFilter.__init__(self)
        self._dataCache = None

    def alias(self) -> str:
        """
        Returns the Human alias-name of this Module.
        """
        return 'Cache'

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Caches data of inputs to speedup the management of repetitive invocations of Modules.'

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'Feature'

    def run(self, data_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        if self._dataCache:
            for feature in self._dataCache:
                yield feature
        else:
            data_cache = []

            for feature in data_store:
                data_cache.append(feature)
                yield feature

            self._dataCache = data_cache

        pass

    def finished_run(self, pipeline, processing_args):
        """
        Finishing a Workflow on Geospatial data.
        """
        return True

    def clean(self):
        """
        Clean cache of inputs.
        """
        if self._dataCache:
            self._dataCache.clear()
            self._dataCache = None

        return True
