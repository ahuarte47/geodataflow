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

import enum
from sqlalchemy import Column, String, DateTime, Enum
from geodataflow.api.database import Base


class Status(str, enum.Enum):
    """
    Status of a Request.
    """
    OK = 'OK'
    ERROR = 'ERROR'
    WORKING = 'WORKING'


class RequestType(str, enum.Enum):
    """
    Type of a Request.
    """
    WORKFLOW = 'WORKFLOW'
    SCHEMA = 'SCHEMA'


class Request(Base):
    """
    Database schema of a Request.
    """
    __tablename__ = 'requests'

    workflow_id = Column(String, primary_key=True, index=True)
    type = Column(Enum(RequestType), nullable=False, default=RequestType.WORKFLOW)
    user_id = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    terminated_at = Column(DateTime, nullable=True)
    status = Column(Enum(Status), nullable=False)
    message = Column(String, nullable=True)
    file_result = Column(String, nullable=True)
