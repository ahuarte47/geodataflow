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

from typing import Dict


class SettingsManager(dict):
    """
    Provides generic settings to configure an Application.
    """
    def __init__(self):
        dict.__init__(self)

    def load_from_file(self, settings_file_name: str) -> "SettingsManager":
        """
        Load settings from the specified file.
        """
        with open(settings_file_name, 'r') as fp:
            for line in fp:
                line = line.strip()
                if len(line) == 0 or line.startswith('#') or line.startswith('//'):
                    continue

                pair = line.strip().split('=')
                name = pair[0].strip()
                self[name] = pair[1].strip().replace("'", "") if len(pair) > 1 else None

        return self

    def load_from_dict(self, settings_dict: Dict) -> "SettingsManager":
        """
        Load settings from the specified Dictionary.
        """
        self.clear()
        self.update(settings_dict)
        return self


global ApplicationSettings
"""
Singleton for Application Configuration.
"""
ApplicationSettings = SettingsManager()
