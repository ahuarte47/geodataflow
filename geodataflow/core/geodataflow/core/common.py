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

import json
import datetime
from typing import Tuple


class CaseInsensitiveDict(dict):
    """
    Basic case in-sensitive dict with strings only keys.
    Copy of "CaseInsensitiveDict" class at "oauthlib.common" module.
    """
    proxy = {}

    def __init__(self, data):
        self.proxy = dict((k.lower(), k) for k in data)
        for k in data:
            self[k] = data[k]

    def __contains__(self, k):
        return k.lower() in self.proxy

    def __delitem__(self, k):
        key = self.proxy[k.lower()]
        super(CaseInsensitiveDict, self).__delitem__(key)
        del self.proxy[k.lower()]

    def __getitem__(self, k):
        key = self.proxy[k.lower()]
        return super(CaseInsensitiveDict, self).__getitem__(key)

    def get(self, k, default=None):
        return self[k] if k in self else default

    def __setitem__(self, k, v):
        super(CaseInsensitiveDict, self).__setitem__(k, v)
        self.proxy[k.lower()] = k

    def update(self, *args, **kwargs):
        super(CaseInsensitiveDict, self).update(*args, **kwargs)
        for k in dict(*args, **kwargs):
            self.proxy[k.lower()] = k


class JSONDateTimeEncoder(json.JSONEncoder):
    """
    Fixes serialization error of Dates in default JSON encoding Class.
    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%dT%H:%M:%S')
        if isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')

        return json.JSONEncoder.default(self, obj)


class DateUtils:
    """
    Provides useful methods to manage Datetimes.
    """
    @staticmethod
    def parse_date_range(startDate: str = None,
                         endDate: str = None,
                         closestToDate: str = None,
                         windowDate: int = 10) -> Tuple[datetime.datetime, datetime.datetime]:
        """
        Returns a Date range according to the specified criteria.
        """
        today_date = datetime.date.today()

        if isinstance(startDate, str):
            start_date = today_date \
                if startDate.upper() == '$TODAY()' \
                else datetime.datetime.strptime(startDate, '%Y-%m-%d')

        elif startDate is None and closestToDate:
            temps_time = datetime.datetime.strptime(closestToDate, '%Y-%m-%d')
            start_date = closestToDate \
                if not windowDate \
                else (temps_time - datetime.timedelta(days=windowDate)).strftime('%Y-%m-%d')

            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_date = startDate if startDate else today_date

        if isinstance(endDate, str):
            final_date = today_date \
                if endDate.upper() == '$TODAY()' \
                else datetime.datetime.strptime(endDate, '%Y-%m-%d')

        elif startDate is None and closestToDate:
            temps_time = datetime.datetime.strptime(closestToDate, '%Y-%m-%d')
            final_date = closestToDate \
                if not windowDate \
                else (temps_time + datetime.timedelta(days=windowDate)).strftime('%Y-%m-%d')

            final_date = datetime.datetime.strptime(final_date, '%Y-%m-%d')
        else:
            final_date = endDate if endDate else today_date

        return start_date, final_date
