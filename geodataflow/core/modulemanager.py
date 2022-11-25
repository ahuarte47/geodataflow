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

import os
import logging
import importlib
import inspect
from typing import Dict, Iterable, Type


class ModuleManager:
    """
    Module manager of dynamic modules deployed in the 'Factories' folder application.
    """
    def __init__(self, abstract_types=()):
        self.abstract_types = abstract_types
        self.modules: Dict[str, Type] = dict()

    def load_modules(self, modules_folders: Iterable[str] = []) -> Dict[str, Type]:
        """
        Load the modules deployed in the specified 'factories' folder application.
        """
        self.modules.clear()
        return self.append_modules(modules_folders)

    def append_modules(self, modules_folders: Iterable[str] = []) -> Dict[str, Type]:
        """
        Adds the modules deployed in the specified 'factories' folder application.
        """
        base_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        for modules_folder in modules_folders:
            modules_folder = os.path.abspath(modules_folder)

            if not os.path.exists(modules_folder):
                logging.error('The specified modules folder "{}" does not exist!'.format(modules_folder))
                continue

            modules_prefix = os.path.commonprefix([base_folder, modules_folder])
            modules_prefix = modules_folder[len(modules_prefix):]
            modules_prefix = modules_prefix.replace('\\', '.')
            modules_prefix = modules_prefix.replace('/', '.')
            if modules_prefix.startswith('.'):
                modules_prefix = os.path.basename(base_folder) + modules_prefix

            # Recursively reading of the factory sub-folder.
            module_file_list = os.listdir(modules_folder)
            module_list = []
            for module_file in module_file_list:
                file_name = os.path.join(modules_folder, module_file)

                if file_name.endswith('__init__.py') or file_name.endswith('__pycache__'):
                    continue
                if file_name.endswith('.py'):
                    module_name = module_file.split('.')[0]
                    module_list.append(module_name)

            # Load the modules of a sub-folder.
            for module_name in module_list:
                try:
                    module_def = importlib.import_module(modules_prefix + '.' + module_name)

                    for type_name, type_def in inspect.getmembers(module_def, inspect.isclass):
                        if type_def in self.abstract_types or not issubclass(type_def, self.abstract_types):
                            continue

                        if hasattr(type_def, '__abstractmethods__') and type_def.__abstractmethods__:
                            continue

                        if hasattr(type_def, 'is_available') and not type_def.is_available():
                            continue

                        type_name = type_name.lower()
                        self.modules[type_name] = type_def

                except Exception as e:
                    logging.error('Fail loading the dynamic module "{}". {}'.format(module_name, str(e)))

        return self.modules

    @staticmethod
    def import_type_from_file(script_file: str, type_name: str, predicate=None) -> Type:
        """
        Returns the Type declaration from the specified script file.
        """
        module_name = os.path.splitext(os.path.basename(script_file))[0]

        import importlib.util
        spec = importlib.util.spec_from_file_location(module_name, script_file)
        module_def = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module_def)
        n, t = None, None

        for type_name_i, type_def_i in inspect.getmembers(module_def, predicate):
            n = type_name_i
            t = type_def_i
            if type_name and type_name == n:
                return t

        return t
