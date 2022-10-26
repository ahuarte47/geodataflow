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

from datetime import datetime
from typing import Dict, Optional, Union
from pydantic import BaseModel, Field


class WorkflowBase(BaseModel):
    """
    Basic pydantic model of a Workflow.
    """
    user_id: str = Field(description='UserId of the request')
    input: Union[str, Dict] = Field(
        description='Pipeline of operations on Geospatial datasources, Json or str-based inputs are supported'
        )
    input_args: Union[Dict, None] = Field(description='Extra parameters (Optional)', default=None)


class WorkflowCreate(WorkflowBase):
    """
    Pydantic model for the creation of a Workflow.
    """
    ...


class Workflow(WorkflowBase):
    """
    Pydantic model of a Workflow.
    """
    id: str = Field(description='UUID of the Workflow')
    created_at: datetime = Field(description='DateTime when the process started', default=datetime.now())
    terminated_at: Optional[datetime] = Field(description='DateTime when the process terminated')
    result: dict = Field(description='Metadata & results of the processing', default={})

    class Config:
        orm_mode = True


class Request(BaseModel):
    """
    Pydantic model of a Request.
    """
    workflow_id: str = Field(description='Id of the Request')
    user_id: str = Field(description='UserId of the Request')
    created_at: datetime = Field(description='DateTime when the process started', default=datetime.now())
    terminated_at: Optional[datetime] = Field(description='DateTime when the process terminated')
    status: str = Field(description='Status of the Request (WORKING, OK, ERROR)')
    message: Optional[str] = Field(description='Optional message/metadata of the Request')
    file_result: Optional[str] = Field(description='href to file result')

    class Config:
        orm_mode = True
