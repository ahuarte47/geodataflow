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

from typing import Dict, Type

from geodataflow.pipeline.pipelinecontext import PipelineContext
from geodataflow.core.processing import ProcessingArgs


class GdalPipelineContext(PipelineContext):
    """
    Provides context to a Processing Task using the GDAL/OGR toolkit.
    """
    def __init__(self, custom_modules: Dict[str, Type] = None, custom_modules_path: str = None):
        custom_modules_path = PipelineContext.concat_modules_path(GdalPipelineContext, custom_modules_path)
        PipelineContext.__init__(self, custom_modules, custom_modules_path)
        pass

    def modules(self) -> Dict:
        """
        Returns the collection of Modules managed by this Context.
        """
        return PipelineContext.modules(self)

    def processing_args(self, temp_path: str = None) -> ProcessingArgs:
        """
        Returns a new Environment for a new Processing Task.
        """
        from geodataflow.spatial.gdalenv import GdalEnv
        return GdalEnv(config_options=GdalEnv.default_options(), temp_path=temp_path)