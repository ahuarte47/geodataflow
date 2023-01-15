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

import sys
import threading
from typing import Dict

from geodataflow.core.processing import ProcessingArgs


# Set of registered GDAL/OGR environments.
_DEFAULT_GDAL_LOCK = threading.RLock()
_DEFAULT_GDAL_ENVS: Dict[int, "GdalEnv"] = dict()


class GdalEnv(ProcessingArgs):
    """
    Provides a very simple GDAL/OGR environment for a Processing Task.

    NOTE:
        Fiona provides better abstraction but this is enough for now.
    Args:
        config_options: GDAL/OGR config options.
        temp_path: Path where temporary files are saved.
    """
    def __init__(self, config_options: Dict[str, str] = None, temp_path: str = None):
        ProcessingArgs.__init__(self, temp_path=temp_path)
        self._config_options = config_options or {}
        self._gdal = None
        self._ogr = None

    def dispose(self) -> None:
        """
        Dispose all resources including temporary data folder.
        """
        global _DEFAULT_GDAL_LOCK
        global _DEFAULT_GDAL_ENVS

        with _DEFAULT_GDAL_LOCK:
            thread_id = threading.get_ident()
            gdal_env = _DEFAULT_GDAL_ENVS.get(thread_id)

            if gdal_env is not None:
                del _DEFAULT_GDAL_ENVS[thread_id]
                gdal_env.dispose()

        ProcessingArgs.dispose(self)

    @staticmethod
    def default() -> "GdalEnv":
        """
        Default GDAL/OGR environment.
        """
        global _DEFAULT_GDAL_LOCK
        global _DEFAULT_GDAL_ENVS

        with _DEFAULT_GDAL_LOCK:
            thread_id = threading.get_ident()
            gdal_env = _DEFAULT_GDAL_ENVS.get(thread_id)

            if gdal_env is None:
                gdal_env = GdalEnv(config_options=GdalEnv.default_options(), temp_path='')
                _DEFAULT_GDAL_ENVS[thread_id] = gdal_env

            return gdal_env

    @staticmethod
    def default_options() -> Dict[str, str]:
        """
        Default GDAL/OGR options for GdalEnv instances.
        """
        return {
            'CPL_VSIL_CURL_ALLOWED_EXTENSIONS': '.tif,.tiff,.vrt,.ovr',
            'CPL_CURL_VERBOSE': 'NO',
            'CPL_DEBUG': 'NO',
            'CPL_VSIL_CURL_USE_CACHE': 'TRUE',
            'CPL_VSIL_CURL_CACHE_SIZE': '64000000',
            'GDAL_DISABLE_READDIR_ON_OPEN': 'FALSE',
            'GDAL_NUM_THREADS': 'ALL_CPUS',
            'GDAL_CACHEMAX': '128',
            'GDAL_TIFF_INTERNAL_MASK': 'YES',
            'VSI_CACHE': 'TRUE',
            'VSI_CACHE_SIZE': '32000000'
        }

    @staticmethod
    def gdal_scripts_path() -> str:
        """
        Returns the root folder where GDAL utility scripts (e.g. gdal_calc.py) are installed.
        """
        is_windows = sys.platform.startswith('win')
        return sys.prefix + '/scripts' if is_windows else '/usr/bin'

    def config_options(self) -> Dict[str, str]:
        """
        Returns configured GDAL/OGR options of this GdalEnv.
        """
        return self._config_options

    def gdal_config(self) -> str:
        """
        Returns configured GDAL/OGR options as a String.
        """
        text_config = ''

        for k, v in self._config_options.items():
            text_config += ' --config {} {}'.format(k, v)

        return text_config

    def gdal(self):
        """
        Returns the GDAL module managed by this GdalEnv.
        """
        if self._gdal is None:
            from osgeo import gdal
            gdal.UseExceptions()

            for k, v in self._config_options.items():
                gdal.SetConfigOption(k, v)

            self._gdal = gdal

        return self._gdal

    def ogr(self):
        """
        Returns the OGR module managed by this GdalEnv.
        """
        if self._ogr is None:
            from osgeo import ogr
            ogr.UseExceptions()
            self._ogr = ogr

        return self._ogr
