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

from typing import Dict, Iterable, List, Union
from geodataflow.pipeline.basictypes import AbstractFilter


class InputParam(AbstractFilter):
    """
    The Filter acts as Feature provider of a Module's parameter.
    """
    def __init__(self):
        AbstractFilter.__init__(self)

    def alias(self) -> str:
        """
        Returns the Human alias-name of this Module.
        """
        return 'InputParam'

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return "Acts as Feature provider of a Module's parameter"

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'Graph'

    @staticmethod
    def enumerate_inputs(stages: Union[str, List[str]], pipeline_args: Dict) -> Iterable:
        """
        Returns an iterable collection of Features of the specified Stage.
        """
        pipeline_manager = pipeline_args.pipeline
        processing_args = pipeline_args.processing_args

        stages = stages.split(',') if isinstance(stages, str) else stages
        inputs = [
            obj for obj in pipeline_manager.objects(recursive=True) if obj.stageId in stages
        ]
        if not inputs:
            raise Exception('StageIds {} not found in current Pipeline.'.format(stages))

        try:
            for input in inputs:
                pipeline_manager._invoke_starting_run(input, [None, None], processing_args)

                for row in input:
                    yield row
        finally:
            for input in inputs:
                pipeline_manager._invoke_finished_run(input, processing_args)

        pass
