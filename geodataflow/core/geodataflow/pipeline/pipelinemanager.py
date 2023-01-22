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
import sys
import logging
import json
import uuid
import base64
import inspect
from collections import OrderedDict
from copy import deepcopy
from typing import Any, Callable, Dict, Iterable, List, Tuple, Union, Type

from geodataflow.core.jsoncomments import JsonComments
from geodataflow.core.capabilities import StoreCapabilities
from geodataflow.core.processing import ProcessingArgs, ProcessingUtils
from geodataflow.core.modulemanager import ModuleManager
from geodataflow.core.schemadef import SchemaDef

from geodataflow.pipeline.moduledef import AbstractModule
from geodataflow.pipeline.basictypes import AbstractReader, AbstractWriter
from geodataflow.pipeline.pipelinecontext import PipelineContext
from geodataflow.pipeline.datastagetypes import DataStageType


class PipelineManager:
    """
    Provides a framework to process Workflows of Geospatial data.

    Pipelines describe the processing of data within a Workflow,
    namely, how data is read, processed and written.
    """
    def __init__(self, context: PipelineContext, config: Dict = {}):
        self.config = config
        self._context = context
        self._pipeline_dir = None
        self._objects: List[AbstractModule] = list()

    @staticmethod
    def _recursive_function(parent_obj,
                            obj,
                            pre_call: bool,
                            function_def: Callable[[Any, Any], None],
                            function_args: Any) -> None:
        """
        Apply the specified function recursively.
        """
        if pre_call:
            function_def(parent_obj, obj, function_args)

        if hasattr(obj, 'ti_'):
            for child in obj.ti_.children:
                PipelineManager._recursive_function(obj, child, pre_call, function_def, function_args)

        if not pre_call:
            function_def(parent_obj, obj, function_args)

        pass

    def context(self) -> PipelineContext:
        """
        Returns the context of this Pipeline
        """
        return self._context

    def objects(self, recursive: bool = False) -> List[AbstractModule]:
        """
        Returns the collection of Operations of this Pipeline.
        """
        if recursive:
            temp_list = list()

            def my_collection_of_objects_function(parent_obj, obj, _):
                temp_list.append(obj)
            for item in self._objects:
                PipelineManager._recursive_function(None, item, True, my_collection_of_objects_function, None)

            return temp_list

        return self._objects

    @staticmethod
    def _get_layer_name(connection_string: Union[str, List[str], Dict[str, Any]]) -> str:
        """
        Returns the FeatureClass name of the specified ConnectionString.
        """
        if isinstance(connection_string, list) and connection_string:
            connection_string = connection_string[0]
        if isinstance(connection_string, dict) and connection_string.get('type', '') == 'FeatureCollection':
            return 'FeatureCollection'
        if isinstance(connection_string, str) and len(connection_string) > 32:
            temp_text = connection_string.replace("\n", "").replace(" ", "")[0:32]

            if temp_text.startswith("{'type':'FeatureCollection'"):
                return 'FeatureCollection'
            if temp_text.startswith('{"type":"FeatureCollection"'):
                return 'FeatureCollection'

        if isinstance(connection_string, dict) and connection_string.get('name', ''):
            connection_string = connection_string.get('name')

        file_name, file_ext = os.path.splitext(connection_string)
        if file_name and file_ext:
            tmp_key = os.path.basename(file_name)
            tmp_pos = tmp_key.find('.')
            return tmp_key[:tmp_pos] if tmp_pos != -1 else tmp_key

        raise Exception('Unknown LayerName parsing of the ConnectionString="{}"'.format(connection_string))

    @staticmethod
    def _convert_list_args_to_dict_args(
            pipeline_args: Union[Iterable[str], Dict[str, str]]) -> Dict[str, str]:
        """
        Converts if necessary the specified type-list pipeline_args to a type-dict object.
        """
        if isinstance(pipeline_args, dict):
            return pipeline_args

        temp_args = dict()
        skip_arg = False

        for arg_index, arg in enumerate(pipeline_args):
            arg_l = arg.lower()

            if skip_arg:
                skip_arg = False
                continue
            if arg_l in ['-source', '-i', '-input', '-target', '-o', '-output'] or arg_l.startswith('--'):
                temp_args[arg] = pipeline_args[arg_index + 1]
                skip_arg = True
                continue
            else:
                temp_item = pipeline_args[arg_index]
                temp_ipos = temp_item.find('=')

                if temp_ipos != -1:
                    temp_pair = [temp_item[0:temp_ipos], temp_item[temp_ipos+1:]]
                else:
                    temp_pair = [temp_item, temp_item]

                temp_args[temp_pair[0].strip()] = temp_pair[1].strip()

        return temp_args

    @staticmethod
    def _enumerate_environment_args(objects: List[AbstractModule],
                                    pipeline_args: Dict[str, str]) -> Iterable[Tuple[str, str]]:
        """
        Enumerate the Pipeline environment args.
        """
        feature_class_found = False

        for key, value in pipeline_args.items():
            #
            if key in ['-source', '-i', '-input']:
                feature_class_found = True
                yield 'FEATURE_CLASS', PipelineManager._get_layer_name(value)
            elif key.startswith('--'):
                key = key[2:].split('.')
                if len(key) != 2:
                    continue
                object_type, attribute_name = key
                if object_type.lower() == 'pipeline':
                    yield attribute_name, value

        if not feature_class_found and objects:
            obj = objects[0]
            if isinstance(obj, AbstractReader) and hasattr(obj, 'connectionString'):
                yield 'FEATURE_CLASS', PipelineManager._get_layer_name(obj.connectionString)

        pass

    @staticmethod
    def _replace_environment_args(objects: List[AbstractModule],
                                  pipeline_args: Dict[str, str],
                                  value: Union[str, List[str]]) -> Union[str, List[str]]:
        """
        Replace the Pipeline environment args in the specified value
        """
        if isinstance(value, str):
            for key, env_value in PipelineManager._enumerate_environment_args(objects, pipeline_args):
                if os.path.isdir(env_value) or os.path.isfile(env_value):
                    import pathlib
                    p = pathlib.Path(os.path.abspath(env_value))
                    env_value = p.as_posix()

                value = value.replace('${' + key + '}', env_value)
                value = value.replace('%' + key + '%', env_value)

        elif isinstance(value, list):
            for i in range(0, len(value)):
                temp_val = PipelineManager._replace_environment_args(objects, pipeline_args, value[i])
                value[i] = temp_val

        return value

    def _parse_pipeline(self,
                        pipeline: Iterable[Dict],
                        pipeline_args: Dict[str, str] = dict()) -> List[AbstractModule]:
        """
        Parse the specified operation settings of a deserialized Pipeline.
        """
        logging.debug('Starting the parsing of Pipeline...')

        # Get the available list of modules.
        context = self.context()
        modules = context.modules()

        logging.debug('Loading metadata of Modules...')

        objects = PipelineManager._parse_pipeline_objects(context, modules, pipeline, pipeline_args)
        logging.debug('Creation of Pipeline operations finished')

        return objects

    def _build_tree_pipeline(self) -> None:
        """
        Build tree of relations between Modules.
        """
        set_of_objects = {obj.stageId: obj for obj in self.objects(recursive=True)}

        def _connect_modules(a: AbstractModule, b: AbstractModule) -> None:
            """
            Connect the specified Modules.
            """
            a.ti_.outputs[b.stageId] = b
            b.ti_.inputs[a.stageId] = a

        def _build_tree_module(module_obj):
            """
            Returns the top of the specified Module.
            """
            if hasattr(module_obj, 'inputStageId'):
                obj = set_of_objects.get(module_obj.inputStageId)
                if not obj:
                    logging.warning(
                        'The StageId="{}" was not found in the tree of Objects.'
                        .format(module_obj.inputStageId))
                else:
                    _connect_modules(obj, module_obj)

            if hasattr(module_obj, 'outputStageId'):
                obj = set_of_objects.get(module_obj.outputStageId)
                if not obj:
                    logging.warning(
                        'The StageId="{}" was not found in the tree of Objects.'
                        .format(module_obj.outputStageId))
                else:
                    _connect_modules(module_obj, obj)

            if module_obj.className == 'ConnectionJoin':
                for stage_id in module_obj.stages:
                    obj = set_of_objects.get(stage_id)
                    if not obj:
                        logging.warning(
                            'The StageId="{}" was not found in the tree of Objects.'
                            .format(stage_id))
                    else:
                        _connect_modules(obj, module_obj)

                return module_obj

            a = module_obj
            children = module_obj.ti_.children

            for i in range(0, len(children)):
                b = _build_tree_module(children[i])

                if a.className != 'AbstractModule' and not isinstance(b, AbstractReader) and not b.ti_.inputs:
                    _connect_modules(a, b)

                a = b

            return a

        # Connect tree of available Modules.
        root_module = AbstractModule()
        root_module.ti_ = type('TreeMetadata', (object,), {
            'children': self._objects,
            'outputs': OrderedDict()
        })
        _build_tree_module(root_module)
        pass

    @staticmethod
    def _reassign_parameters_objects(
            context: PipelineContext,
            objects: List[AbstractModule],
            pipeline_args: Dict[str, str] = dict()) -> List[AbstractModule]:
        """
        Reassign parameters of operations.
        """
        for key, value in pipeline_args.items():
            #
            if key in ['-source', '-i', '-input']:
                data_source = value
                obj = context.find_module_by_data_source(data_source, AbstractReader, StoreCapabilities.READ)
                if obj is None:
                    raise Exception('Input DataSource "{}" not supported!'.format(data_source))

                obj.connectionString = data_source
                objects.insert(0, obj)
                continue
            if key in ['-target', '-o', '-output']:
                data_source = value
                obj = context.find_module_by_data_source(data_source, AbstractWriter, StoreCapabilities.CREATE)
                if obj is None:
                    raise Exception('Output DataSource "{}" not supported!'.format(data_source))

                obj.connectionString = data_source
                objects.append(obj)
                continue
            #
            elif key.startswith('--'):
                key = key[2:].split('.')
                if len(key) != 3:
                    continue
                object_type, stage_id, attribute_name = key
                if object_type.lower() != 'module':
                    continue

                logging.debug(
                    'Assigning parameter of "{}.{}" -> {}={}...'
                    .format(object_type, stage_id, attribute_name, value))

                for obj in objects:
                    if obj.stageId == stage_id:
                        if hasattr(obj, attribute_name):
                            new_value = ProcessingUtils.cast_value(value, type(getattr(obj, attribute_name)))
                            setattr(obj, attribute_name, new_value)
                        else:
                            setattr(obj, attribute_name, value)

        return objects

    @staticmethod
    def _parse_pipeline_objects(context: PipelineContext,
                                modules: Dict[str, Type],
                                pipeline: Iterable[Dict],
                                pipeline_args: Dict[str, str] = dict()) -> List[AbstractModule]:
        """
        Parse the specified operation settings of a deserialized Pipeline.
        """
        objects: List[AbstractModule] = list()
        temp_args = {k: v for k, v in pipeline_args.items() if k.startswith('--') or not k.startswith('-')}

        # Create the operation object collection of the pipeline.
        for settings in pipeline:
            type_name = settings['type']

            type_parts = type_name.split('.')
            class_name = type_parts[len(type_parts)-1]
            type_def = modules.get(type_name.lower()) or modules.get(class_name.lower())

            # ... does this object provide the Path where the Python file is located?
            if type_def is None and settings.get('moduleLocation'):
                script_file = settings.get('moduleLocation')

                if not os.path.exists(script_file):
                    script_file = os.path.join(os.path.dirname(__file__), script_file)

                type_def = ModuleManager.import_type_from_file(script_file, class_name, inspect.isclass)

            if type_def is None:
                raise Exception('The Module type "{}" is not supported!'.format(settings['type']))

            obj = type_def()
            obj.ti_ = type('TreeMetadata', (object,), {
                'parent': None, 'children': [], 'inputs': OrderedDict(), 'outputs': OrderedDict()
            })

            for key, value in settings.items():
                if key not in ['type', 'pipeline']:
                    setattr(obj, key, value)

            if settings.get('pipeline'):
                children_pipeline = settings.get('pipeline')
                children = \
                    PipelineManager._parse_pipeline_objects(context, modules, children_pipeline, temp_args)

                for child in children:
                    child.ti_.parent = obj

                obj.ti_.children = children

            objects.append(obj)

        # Reassign parameters of operations.
        objects = \
            PipelineManager._reassign_parameters_objects(context, objects, pipeline_args)

        # Fix some possible bad settings.
        for obj in objects:
            if isinstance(obj, (AbstractReader, AbstractWriter)) and hasattr(obj, 'connectionString'):
                obj.connectionString = \
                    PipelineManager._replace_environment_args(objects, pipeline_args, obj.connectionString)

        return objects

    def load_from_file(self,
                       file_name: str,
                       pipeline_args: Union[Iterable[str], Dict[str, str]] = dict()) -> List[AbstractModule]:
        """
        Load the pipeline from the specified JSON filename.
        """
        self._pipeline_dir = os.path.dirname(file_name)
        self._objects = list()
        pipeline_args = PipelineManager._convert_list_args_to_dict_args(pipeline_args)

        with open(file_name, 'r') as file:
            # remove JSON comments.
            standard_json = JsonComments.remove_comments(file, keep_ends=True)
            # Reassign environment pipeline content.
            standard_json = PipelineManager._replace_environment_args([], pipeline_args, standard_json)

            # Reassign pipeline content from current file.
            import pathlib
            p = pathlib.Path(os.path.abspath(file_name))
            model_path = p.as_posix()
            model_dirn = os.path.dirname(model_path)
            model_file = os.path.basename(model_path)

            file_args = {
                "PIPELINE_FOLDER": model_dirn,
                "PIPELINE_FILE": model_file,
                "PIPELINE_PATH": model_path
            }
            for k, v in pipeline_args.items():
                if not k.startswith('-'):
                    standard_json = standard_json.replace('$'+k, v)
            for k, v in file_args.items():
                standard_json = standard_json.replace('$'+k, v)

            pipeline = json.loads(standard_json)['pipeline']
            self._objects = self._parse_pipeline(pipeline, pipeline_args)
            self._build_tree_pipeline()

        return self._objects

    def load_from_json(self,
                       pipeline: Iterable[Dict],
                       pipeline_args: Union[Iterable[str], Dict[str, str]] = dict()) -> List[AbstractModule]:
        """
        Load the pipeline from the specified JSON pipeline.
        """
        self._pipeline_dir = None
        self._objects = list()
        pipeline_args = PipelineManager._convert_list_args_to_dict_args(pipeline_args)

        self._objects = self._parse_pipeline(pipeline, pipeline_args)
        self._build_tree_pipeline()
        return self._objects

    class _DataStageWriter(AbstractWriter):
        """
        Writer to capture data from a Pipeline Stage.
        """
        def __init__(self, data_type: DataStageType):
            AbstractWriter.__init__(self)
            self.data_type = data_type
            self.schema_def = None
            self.features = []

        def __del__(self):
            AbstractWriter.__del__(self)
            self.schema_def = None
            self.features = None

        def test_capability(self, connection_string: str, capability: StoreCapabilities) -> bool:
            """
            Returns always True for this DummyWriter.
            """
            return True

        def starting_run(self, schema_def, pipeline, processing_args):
            """
            Capture SchemaDef.
            """
            self.schema_def = schema_def.clone()
            return schema_def

        def run(self, data_store, processing_args):
            """
            Doing something.
            """
            if self.data_type == DataStageType.SCHEMA:
                return iter([])
            else:
                from shapely.geometry import mapping as shapely_mapping

                for index, row in enumerate(data_store):
                    feature = {
                        'type': row.type,
                        'fid': row.fid if hasattr(row, 'fid') else index,
                        'properties': row.properties,
                        'geometry': shapely_mapping(row.geometry)
                    }
                    self.features.append(feature)
                    yield row

                pass

        def result(self):
            """
            Returns the data collected.
            """
            if self.data_type == DataStageType.SCHEMA:
                return self.schema_def
            else:
                data = {
                    'type': 'FeatureCollection',
                    'crs': {
                        'type': 'name',
                        'properties': {'name': 'EPSG:' + str(self.schema_def.srid)}
                    },
                    'features': self.features
                }
                return data

    def data_of_stage(self, stage_id: str, data_type: DataStageType, processing_args: ProcessingArgs) -> bool:
        """
        Get data of a Stage in the specified pipeline of Geospatial data.
        """
        temp_list = [obj for obj in self.objects(recursive=True) if obj.stageId == stage_id]
        if not temp_list:
            raise Exception('Stage "{}" not found in current Pipeline'.format(stage_id))

        current_list = self._objects
        try:
            new_list = list()

            data_writer = PipelineManager._DataStageWriter(data_type)
            data_writer.ti_ = type('TreeMetadata', (object,), {
                'parent': None, 'children': [], 'inputs': OrderedDict(), 'outputs': OrderedDict()
            })

            def my_clone_of_object_function(obj) -> Iterable:
                #
                if obj.stageId == stage_id:
                    #
                    if isinstance(obj, AbstractWriter):
                        data_writer.ti_.inputs = obj.ti_.inputs.copy()
                        yield data_writer
                    else:
                        new_obj = deepcopy(obj)
                        new_obj.ti_.outputs.clear()
                        new_obj.ti_.outputs[data_writer.stageId] = data_writer
                        yield new_obj
                        data_writer.ti_.inputs.clear()
                        data_writer.ti_.inputs[new_obj.stageId] = new_obj
                        yield data_writer

                        new_obj.ti_.children.clear()
                        for child in obj.ti_.children:
                            for c in my_clone_of_object_function(child):
                                new_obj.ti_.children[c.stageId] = c

                    return

                if isinstance(obj, AbstractWriter):
                    return

                yield obj

            for item in self._objects:
                new_list.extend(my_clone_of_object_function(item))

            self._objects = new_list
            self.run(processing_args)

            data = data_writer.result()
            return data
        finally:
            self._objects = current_list

    def run(self, processing_args: ProcessingArgs, callback: Callable = None, callback_args: Any = None) -> bool:
        """
        Execute the pipeline of Geospatial data.
        """
        if len(self._objects) == 0:
            logging.warning('There is none Node, the Pipeline does nothing!')
            return False

        set_of_objects = [obj for obj in self.objects(recursive=True)]

        if self._pipeline_dir:
            os.environ['PIPELINE_FOLDER'] = self._pipeline_dir
            sys.path.append(self._pipeline_dir)

        try:
            readers = [
                obj for obj in set_of_objects if isinstance(obj, AbstractReader)
            ]
            writers = [
                obj for obj in set_of_objects if isinstance(obj, AbstractWriter) and not obj.ti_.outputs
            ]

            if not writers:
                logging.warning('There is none Output node, the Pipeline does nothing!')
                return False

            # Redefine 'connectionString' of Readers, when defining embebed fileData.
            for reader in readers:
                if hasattr(reader, 'connectionString'):
                    tempString = reader.connectionString

                    if isinstance(tempString, dict) and tempString.get('name') and tempString.get('fileData'):
                        file_data = tempString.get('fileData')
                        temp_ipos = file_data.find(';base64,')
                        file_data = file_data[temp_ipos+len(';base64,'):]
                        file_name = tempString.get('name')
                        temp_file = os.path.join(
                            processing_args.temp_data_path(), '{}_{}'.format(uuid.uuid1(), file_name))

                        with open(temp_file, mode='wb') as fp:
                            stream_fp = base64.b64decode(file_data)
                            fp.write(stream_fp)

                        reader.connectionString = temp_file

            # Run workflow, like one IEnumerable stream!
            for writer in writers:
                self._invoke_starting_run(writer, [None, None], processing_args)

                for feature in writer:
                    if callback:
                        callback(self, processing_args, writer, feature, callback_args)

                    feature = None

                self._invoke_finished_run(writer, processing_args)

            return True
        finally:
            for obj in set_of_objects:
                if hasattr(obj, 'pipeline_args'):
                    obj.finished_run(self, processing_args)
                    delattr(obj, 'pipeline_args')
                if hasattr(obj, 'clean') and callable(getattr(obj, 'clean')):
                    obj.clean()

            if self._pipeline_dir:
                os.environ['PIPELINE_FOLDER'] = ''
                sys.path.remove(self._pipeline_dir)

        return False

    def _invoke_starting_run(
            self,
            module_obj: AbstractModule,
            function_args: Any, processing_args: ProcessingArgs) -> Tuple[SchemaDef, AbstractModule]:
        """
        Prepare of task metadata of each Pipeline Operation.
        """
        input_function_args = function_args
        input_schemas = []

        # Calling before to the tree of inputs.
        for obj in module_obj.ti_.inputs.values():
            function_args = self._invoke_starting_run(obj, input_function_args, processing_args)
            input_schemas.append(function_args[0])

        if hasattr(module_obj, 'pipeline_args'):
            module_obj.pipeline_args.calling_count += 1
            return [module_obj.pipeline_args.schema_def, module_obj.pipeline_args.data_source]
        if len(input_schemas) > 1:
            function_args[0] = SchemaDef.merge_all(input_schemas)
        if module_obj.className == 'ConnectionJoin':
            function_args[1] = None

        # Assign metadata for using when the Pipeline runs.
        schema_def = function_args[0]
        parent_obj = function_args[1]
        schema_def = module_obj.starting_run(schema_def, self, processing_args)

        setattr(module_obj, 'pipeline_args', type('PipelineArgs', (object,), {
            'config': self.config,
            'pipeline': self,
            'data_source': parent_obj,
            'schema_def': schema_def,
            'processing_args': processing_args,
            'calling_count': 1
        })())
        return [schema_def, module_obj]

    def _invoke_finished_run(self, module_obj: AbstractModule, processing_args: ProcessingArgs) -> AbstractModule:
        """
        Finalization of task for each Pipeline operation.
        """
        if hasattr(module_obj, 'pipeline_args'):
            module_obj.pipeline_args.calling_count -= 1

            if module_obj.pipeline_args.calling_count == 0:
                module_obj.finished_run(self, processing_args)
                delattr(module_obj, 'pipeline_args')

        for obj in module_obj.ti_.inputs.values():
            self._invoke_finished_run(obj, processing_args)

        return module_obj
