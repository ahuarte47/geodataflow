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

from typing import Dict
from geodataflow.pipeline.basictypes import AbstractFilter


class ConnectionJoin(AbstractFilter):
    """
    The Filter joins the streams of data of several input Modules in one unique output.
    """
    def __init__(self):
        AbstractFilter.__init__(self)
        self._is_heterogeneous = False
        self._inputs = None
        self.stages = []

    def alias(self) -> str:
        """
        Returns the Human alias-name of this Module.
        """
        return 'ConnectionJoin'

    def description(self) -> str:
        """
        Returns the Description text of this Module.
        """
        return 'Joins the streams of data of several input Modules in one unique output.'

    def category(self) -> str:
        """
        Returns the category or group to which this Module belongs.
        """
        return 'Graph'

    def params(self) -> Dict:
        """
        Returns the declaration of parameters supported by this Module.
        """
        return {
            'stages': {
                'description': 'Collection of Modules (Using the "StageId" attribute) to merge.',
                'dataType': 'array<string>'
            }
        }

    def starting_run(self, schema_def, pipeline, processing_args):
        """
        Starting a new Workflow on Geospatial data.
        """
        set_of_objects = pipeline.objects(recursive=True)
        schema_def = None
        inputs = []

        for stage_id in self.stages:
            object_array = [obj for obj in set_of_objects if obj.stageId == stage_id]

            # Join SchemaDef instances of all input Modules.
            for temp_object in object_array:
                temp_schema_def = temp_object.pipeline_args.schema_def

                schema_def = temp_schema_def.merge(schema_def)
                if len(schema_def.fields) != len(temp_schema_def.fields):
                    self._is_heterogeneous = True

                inputs.append(temp_object)

        self._inputs = inputs
        return schema_def

    def run(self, none_store, processing_args):
        """
        Transform input Geospatial data. It should return a new iterable set of Geospatial features.
        """
        fields = self.pipeline_args.schema_def.fields

        for data_store in self._inputs:
            for row in data_store:
                if self._is_heterogeneous:
                    row.properties = {fd.name: row.properties.get(fd.name, fd.defaultValue) for fd in fields}

                yield row

        pass

    def finished_run(self, pipeline, processing_args):
        """
        Finishing a Workflow on Geospatial data.
        """
        self._is_heterogeneous = False

        if self._inputs:
            self._inputs.clear()
            self._inputs = None

        return True
