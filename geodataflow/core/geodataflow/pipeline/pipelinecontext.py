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
import importlib.util
import inspect
import logging
from typing import Any, Dict, Type, Union

from geodataflow.core.__meta__ import __name__ as CORE_CONTEXT_NAME
from geodataflow.core.capabilities import StoreCapabilities
from geodataflow.core.modulemanager import ModuleManager
from geodataflow.core.processing import ProcessingArgs
from geodataflow.pipeline.moduledef import AbstractModule
from geodataflow.pipeline.basictypes import AbstractReader, AbstractFilter, AbstractWriter


class PipelineContext:
    """
    Provides basic context to a Processing Task.
    """
    def __init__(self, custom_modules: Dict[str, Type] = None, custom_modules_path: str = None):
        self._custom_modules = custom_modules
        self._custom_modules_path = custom_modules_path
        self._modules = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        self.dispose()

    def __del__(self):
        self.dispose()

    def dispose(self) -> None:
        """
        Dispose all resources created by this Context.
        """
        self._custom_modules = None
        self._custom_modules_path = None
        self._modules = None

    @staticmethod
    def contexts() -> Dict:
        """
        Set of registered PipelineContexts in current dist of GeodataFlow.
        """
        return RESGISTERED_CONTEXTS

    @staticmethod
    def register_context(package_with_context: str) -> "PipelineContext":
        """
        Register the PipelineContext provided by the specified Package.
        """
        if package_with_context != CORE_CONTEXT_NAME:
            try:
                root_path = os.path.dirname(__file__)
                is_windows = sys.platform.startswith('win')
                dev_mode = root_path.endswith(os.path.join(CORE_CONTEXT_NAME, __package__).replace('.', os.sep))

                package_names = \
                    ['{}.{}'.format(package_with_context, package_with_context), package_with_context] \
                    if not is_windows and dev_mode else [package_with_context]

                for name in package_names:
                    spec = importlib.util.find_spec(name)
                    if spec:
                        module_def = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module_def)
                        break

            except Exception as e:
                logging.warning('Package "{}" not loaded, error={}.'.format(package_with_context, str(e)))

        # Check existence of PipelineContext.
        return RESGISTERED_CONTEXTS.get(package_with_context)

    @staticmethod
    def concat_modules_path(class_of_context: Type, modules_path: Union[str, None]) -> str:
        """
        Concat specific Modules path with the default for this Context.
        """
        if class_of_context == PipelineContext:
            return modules_path
        else:
            default_path = os.path.join(os.path.dirname(inspect.getabsfile(class_of_context)), 'modules')
            return default_path + ',' + modules_path if modules_path else default_path

    def find_module_by_data_source(
            self,
            data_source: str,
            module_type: Type, capability: StoreCapabilities) -> AbstractModule:
        """
        Finds the first Module that supports the specified DataSource.
        """
        for module_def in self.modules().values():
            #
            if issubclass(module_def, module_type):
                module_obj = module_def()
                if module_obj.test_capability(data_source, capability):
                    return module_obj

        return None

    def modules(self) -> Dict:
        """
        Returns the collection of Modules managed by this Context.
        """
        if self._modules is None:
            modules_folders = \
                [os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core', 'modules')]

            if self._custom_modules_path:
                modules_folders += self._custom_modules_path.split(',')

            # Get available list of modules.
            manager = ModuleManager((AbstractReader, AbstractFilter, AbstractWriter))
            modules = manager.load_modules(modules_folders)
            #
            if self._custom_modules:
                modules.update(self._custom_modules)
            #
            self._modules = modules

        return self._modules

    def catalog(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns the Catalog of metadata of Modules managed by this Context.
        """
        modules_ = {}

        for module_def in self.modules().values():
            module_obj = module_def()

            modules_[module_obj.className] = {
                'name': module_obj.className,
                'type': module_obj.classType,
                'alias': module_obj.alias(),
                'category': module_obj.category(),
                'description': module_obj.description(),
                'params': module_obj.params()
            }

        return modules_

    def processing_args(self, temp_path: str = None) -> ProcessingArgs:
        """
        Returns a new Environment for a new Processing Task.
        """
        return ProcessingArgs(temp_path=temp_path)


# Set of registered contexts in current dist of GeodataFlow.
RESGISTERED_CONTEXTS = {CORE_CONTEXT_NAME: PipelineContext}
