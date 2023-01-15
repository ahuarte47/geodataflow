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

from typing import Dict, List, Union
from uuid import uuid4
from collections.abc import Iterable


class ModuleIt(Iterable):
    """
    Wrapper of a Module to run it as Iterator.
    """
    def __init__(self, object_it, module, pipeline_args, processing_args):
        Iterable.__init__(self)
        self._object_it = object_it
        self.module = module
        self.pipeline_args = pipeline_args
        self.processing_args = processing_args

    def __del__(self):
        self._object_it = None
        self.module = None
        self.pipeline_args = None
        self.processing_args = None

    def __next__(self):
        return next(self._object_it)

    def __iter__(self):
        return self


class AbstractModule(Iterable):
    """
    Generic Module that operates on Workflows of Geospatial data.
    """
    def __init__(self):
        Iterable.__init__(self)
        self.className = str(self.__class__.__name__)
        self.classType = 'module'
        self.stageId = str(uuid4())
        # logging.debug('-> New object {} created!'.format(self.className))

    def __del__(self):
        # logging.debug('<- {} destroyed!'.format(self.className))
        pass

    def __iter__(self) -> ModuleIt:
        """
        Returns the iterable set of Geospatial features of current Workflow.
        """
        if self.pipeline_args is None:
            return iter([])

        pipeline_args = self.pipeline_args
        processing_args = pipeline_args.processing_args
        return ModuleIt(
            self.run(pipeline_args.data_source, processing_args), self, pipeline_args, processing_args
        )

    @staticmethod
    def is_available() -> bool:
        """
        Indicates that this Module is available for use, some modules may depend
        on the availability of other third-party packages.
        """
        return True

    def alias(self) -> str:
        """
        Returns the Human alias-name of this Module.
        """
        return self.className

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'Modules'

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Generic module'

    def params(self) -> Dict:
        """
        Returns the declaration of parameters supported by this Module.
        """
        return {}

    def starting_run(self, schema_def, pipeline, processing_args):
        """
        Starting a new Workflow on Geospatial data.
        """
        return schema_def

    def run(self, data_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        if data_store is not None:
            for row in data_store:
                yield row

    def finished_run(self, pipeline, processing_args):
        """
        Finishing a Workflow on Geospatial data.
        """
        return False

    def enumerate_inputs(self, stages: Union[str, List[str]]) -> Iterable:
        """
        Returns an iterable collection of Features of the specified Stage[s].
        """
        from geodataflow.core.modules.InputParam import InputParam

        pipeline_args = self.pipeline_args
        if not pipeline_args:
            raise Exception('Invoking "enumerate_inputs()" outside of a running Context')

        processing_args = pipeline_args.processing_args
        if not processing_args:
            raise Exception('Invoking "enumerate_inputs()" outside of a running Context')

        for row in processing_args.unpack(InputParam.enumerate_inputs(stages, pipeline_args)):
            yield row

        pass
