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

import re
from typing import Iterable


class JsonComments:
    """
    A wrapper to JSON parsers allowing comments, multiline strings and trailing commas.
    See:
      https://bitbucket.org/Dando_Real_ITA/json-comment/src/default/jsoncomment/comments.py
    """
    COMMENT_PREFIX = ("#", ";", "//")
    MULTILINE_START = "/*"
    MULTILINE_END = "*/"
    LONG_STRING = '"""'
    TEMPLATE_RE = re.compile(r"\{\{(.*?)\}\}")

    @staticmethod
    def remove_comments(lines: Iterable[str], keep_ends: bool = True) -> str:
        """
        Returns the standard JSON version (Skipping comments) of the specified stream of JSON lines.
        """
        standard_json = ''
        is_multiline = False

        for line in lines:
            # 0 if there is no trailing space, 1 otherwise.
            keep_trail_space = int(line.endswith(' '))

            # Count leading spaces.
            leading_spaces = len(line) - len(line.lstrip())

            # Remove all whitespace on both sides.
            line = line.strip()

            # Skip blank lines or single line comments.
            if len(line) == 0 or line.startswith(JsonComments.COMMENT_PREFIX):
                continue

            # Mark the start of a multiline comment:
            # Not skipping, to identify single line comments using multiline comment tokens, like
            # /***** Comment *****/
            if line.startswith(JsonComments.MULTILINE_START):
                is_multiline = True

            # Skip a line of multiline comments
            if is_multiline:
                # Mark the end of a multiline comment
                if line.endswith(JsonComments.MULTILINE_END):
                    is_multiline = False

                continue

            # Replace the multiline data token to the JSON valid one.
            if JsonComments.LONG_STRING in line:
                line = line.replace(JsonComments.LONG_STRING, '"')

            standard_json += (leading_spaces * ' ') + line + ' ' * keep_trail_space
            if keep_ends:
                standard_json += '\n'

        # Removing non-standard trailing commas.
        standard_json = standard_json.replace(',]', ']')
        standard_json = standard_json.replace(',}', '}')

        return standard_json
