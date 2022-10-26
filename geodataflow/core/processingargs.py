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

import sys
import os
import tempfile
import logging
import subprocess
import shlex
import shutil
import math
from math import *  # noqa: F401,F403
from typing import Any, Callable, Dict, List, Iterable, Union


# =============================================================================
# XPR Eval helper functions.

def register_eval_function_stack() -> Dict[str, Callable]:
    """
    Returns the basic stack of evaluable Functions.
    """
    globals_ = globals()

    function_dict = dict([
        (f_name, globals_.get(f_name, None)) for f_name in dir(math) if not f_name.startswith('_')
    ])
    function_dict['str'] = str
    function_dict['len'] = len

    def _switch_func(value, options, default_val=None):
        """
        Select one of many codes to return it related value.
        """
        result = list(filter(lambda option: option[0] == value, options))
        return result[0][1] if len(result) > 0 else default_val

    function_dict['switch'] = _switch_func
    function_dict['select'] = _switch_func

    def _iif_func(condition, true_value, false_value):
        """
        Return true/false value according condition.
        """
        return true_value if condition else false_value

    function_dict['iif'] = _iif_func

    return function_dict


# Stack of callable math functions to include in an eval() execution, only MATH functions for safety.
BASIC_EVAL_FUNCTION_STACK = None

# =============================================================================


class ProcessingUtils:
    """
    Provides generic utility functions for Processing tasks.
    """
    @staticmethod
    def cast_value(value, value_type):
        """
        Cast a value to the specified type.
        """
        if value_type == float:
            return float(value)
        if value_type == int:
            return int(value)
        if value_type == list:
            return list(value)

        return value

    @staticmethod
    def cast_enum(value, class_enum_type):
        """
        Cast a value to the specified Enum-like type.
        """
        return value if isinstance(value, int) else class_enum_type().__getattribute__(value)

    @staticmethod
    def object_as_dict(obj: object) -> Dict[str, Any]:
        """
        Converts the specified Object to Dict.
        """
        new_dict = dict((k, v) for k, v in obj.__dict__.items() if not callable(v) and not k.startswith('__'))
        return new_dict

    @staticmethod
    def strtobool(value) -> bool:
        """
        Converts to bool type the specified string value.
        """
        if type(value) == str:
            value = value.lower()

            if value == 'false' or value == '0' or value == 'no':
                return False
            if value == 'true' or value == '1' or value == 'yes':
                return True

        return value

    @staticmethod
    def eval_function(expression, attributes: Union[List, Dict] = {}, normalize_attribs: bool = True):
        """
        Evaluate the specified expression and arguments.
        """
        if isinstance(expression, str) and \
           expression.find('$') == -1 and (os.path.isdir(expression) or os.path.isfile(expression)):
            return expression

        if normalize_attribs:
            attribute_dict = dict()

            if type(attributes) is list:
                for temp_dict in attributes:
                    attribute_dict.update(('_attr__'+str(k), v) for k, v in temp_dict.items())
            else:
                attribute_dict.update(('_attr__'+str(k), v) for k, v in attributes.items())
        else:
            if type(attributes) is list:
                attribute_dict = dict()
                for temp_dict in attributes:
                    attribute_dict.update(temp_dict)
            else:
                attribute_dict = attributes

        global BASIC_EVAL_FUNCTION_STACK

        if BASIC_EVAL_FUNCTION_STACK is None:
            BASIC_EVAL_FUNCTION_STACK = register_eval_function_stack()

        if isinstance(expression, str):
            xpr = expression
            arr = ['_attr__' if c == '$' and xpr[i+1].isalpha() else c for i, c in enumerate(xpr)]
            xpr = ''.join(arr)
            xpr = xpr.replace("\\", "^^")
            # r = expression.replace('$', '_attr__')
            res = eval(xpr, BASIC_EVAL_FUNCTION_STACK, attribute_dict)
            if isinstance(res, str):
                res = res.replace("^^", "\\")

            return res
        else:
            return eval(expression, BASIC_EVAL_FUNCTION_STACK, attribute_dict)


class ProcessingArgs:
    """
    Provides utilities for a Processing task.

    Args:
        temp_path: Path where temporary files are saved.
    """
    def __init__(self, temp_path: str = None):
        self._is_windows = sys.platform.startswith('win')
        self._temp_path = temp_path
        self._temp_data_path = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        self.dispose()

    def __del__(self):
        self.dispose()

    @staticmethod
    def _normalize_path(path: str) -> str:
        """
        Returns the normalized version of the specified path.
        """
        if ' ' in path and '"' not in path:
            path = '"' + path + '"'
        if '*' in path and '"' not in path:
            path = '"' + path + '"'
        return path

    @staticmethod
    def _get_command_line_args(command_args: Iterable[str]) -> str:
        """
        Returns the command-line string of the specified command_args
        """
        command_line = ''

        if not command_args:
            return command_line
        for command_arg in command_args:
            command_line += ' ' + ProcessingArgs._normalize_path(command_arg)

        return command_line

    @staticmethod
    def _read_subprocess_stdout(p) -> Iterable[str]:
        """
        Prompt the stdout pipeline as real-time style
        """
        while p.poll() is None:
            for line in iter(lambda: p.stdout.readline() if p.poll() is None else '', ''):
                line = line.decode('utf-8', errors='ignore').rstrip()
                if line:
                    yield line

    def temp_data_path(self) -> str:
        """
        Returns an unique temporal data path for this processing task.
        """
        if self._temp_data_path:
            return self._temp_data_path
        elif not self._temp_path:
            self._temp_data_path = tempfile.mkdtemp(prefix='pyproc-task_')
            return self._temp_data_path
        else:
            self._temp_data_path = self._temp_path

            # 'temp_path' is only created and removed when disposing if that folder does not exist.
            if not os.path.exists(self._temp_path):
                self._temp_path = None

            os.makedirs(self._temp_data_path, exist_ok=True)
            return self._temp_data_path

    def dispose(self) -> None:
        """
        Dispose all resources including temporary data folder.
        """
        if self._temp_data_path and not self._temp_path:
            shutil.rmtree(self._temp_data_path, ignore_errors=True)

    def run(self, command_line: Union[str, Iterable[str]], environment_args: Dict[str, str] = None) -> int:
        """
        Runs the specified command.
        """
        if not type(command_line) is str:
            command_line = ProcessingArgs._get_command_line_args(command_line)

        env_args = os.environ.copy()
        if environment_args:
            env_args.update(environment_args)

        logging.debug('command_line=' + command_line)
        logging.debug('command_args=' + str(shlex.split(command_line, posix="win" not in sys.platform)))

        try:
            with subprocess.Popen(command_line,
                                  shell=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env_args) as p:
                if p.stderr:
                    message = ''

                    for line in p.stderr.readlines():
                        message += line.decode('utf-8').rstrip() + '\n'

                    message = message.rstrip()
                    logging.error(message)
                    raise RuntimeError(message)

                if p.stdout:
                    for message in ProcessingArgs._read_subprocess_stdout(p):
                        logging.info(message)

                return p.returncode

        except subprocess.CalledProcessError as e:
            raise e
