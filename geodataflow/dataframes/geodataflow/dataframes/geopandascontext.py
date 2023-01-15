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

from typing import Dict, Type, Iterable

from geodataflow.core.processing import ProcessingArgs
from geodataflow.pipeline.pipelinecontext import PipelineContext
from geodataflow.spatial.gdalcontext import GdalPipelineContext


class GeoPandasPipelineContext(GdalPipelineContext):
    """
    Provides context to a Processing Task using GeoPandas DataFrames.
    """
    def __init__(self, custom_modules: Dict[str, Type] = None, custom_modules_path: str = None):
        custom_modules_path = PipelineContext.concat_modules_path(GeoPandasPipelineContext, custom_modules_path)
        GdalPipelineContext.__init__(self, custom_modules, custom_modules_path)
        pass

    def modules(self) -> Dict:
        """
        Returns the collection of Modules managed by this Context.
        """
        modules_ = {}

        for key, module_def in GdalPipelineContext.modules(self).items():
            #
            if key.startswith("osgeo"):
                continue

            modules_[key] = module_def

        return modules_

    def processing_args(self, temp_path: str = None) -> ProcessingArgs:
        """
        Returns a new Environment for a new Processing Task.
        """
        from geodataflow.spatial.gdalenv import GdalEnv

        class GeoPandasEnv(GdalEnv):
            """
            Overrides the GDAL/OGR environment for a Processing Task using GeoPandas.
            """
            def __init__(self_):
                GdalEnv.__init__(self=self_, config_options=GdalEnv.default_options(), temp_path=temp_path)

            def unpack(self, data_store) -> Iterable[object]:
                """
                Unpack input Store into a collection of Features simples.
                """
                from geodataflow.dataframes.utils import TableUtils

                for row in TableUtils.unpack(data_store):
                    yield row

        return GeoPandasEnv()
