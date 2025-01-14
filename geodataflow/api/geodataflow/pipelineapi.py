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
import time
import datetime
import logging
import json
import pathlib
import uuid
import zipfile
from typing import Any, Dict
from copy import deepcopy

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from geodataflow.api.__meta__ import __description__, __version__
from geodataflow.api.models import (
    Workflow as WorkflowModel, WorkflowCreate as WorkflowCreateModel, Request as RequestModel
)
from geodataflow.api.schema import (
    Request as RequestSchema, Status as RequestStatus, RequestType
)
from geodataflow.api.database import get_db, init_db


package_path = os.path.dirname(os.path.dirname(__file__))
if package_path not in sys.path:
    sys.path.insert(0, package_path)

try:
    from geodataflow.core.jsoncomments import JsonComments
    from geodataflow.core.processing import ProcessingUtils
    from geodataflow.core.settingsmanager import ApplicationSettings
    from geodataflow.pipeline.pipelinemanager import PipelineManager, PipelineContext
    from geodataflow.pipeline.basictypes import AbstractWriter
    from geodataflow.pipeline.datastagetypes import DataStageType
except Exception as e:
    raise e


# GeodataFlow FastAPI Service.
app = FastAPI(
    title='GeodataFlow WebAPI',
    description=__description__,
    version=__version__
)
origins = os.environ.get('GEODATAFLOW_API_ORIGINS')
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins.split(';'),
        allow_credentials=True,
        allow_methods=['GET', 'POST'],
        allow_headers=['*']
    )
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s]: %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.info('========================================================================')
logging.info('GeodataFlow:')
logging.info('Geoprocessing framework for geographical & Earth Observation (EO) data.')
logging.info('========================================================================')
logging.info('')

# Settings of service.
settings_file = os.path.splitext(os.path.abspath(__file__))[0] + '.default.settings'
app_settings = ApplicationSettings.load_from_file(settings_file)

# Package name with the PipelineContext to initialize.
PACKAGE_WITH_PIPELINE_CONTEXT: str = \
    os.environ.get('PACKAGE_WITH_GEODATAFLOW_PIPELINE_CONTEXT') or \
    app_settings.get('PACKAGE_WITH_GEODATAFLOW_PIPELINE_CONTEXT') or 'geodataflow.spatial'
PACKAGE_WITH_PIPELINE_CONTEXT = \
    PACKAGE_WITH_PIPELINE_CONTEXT.strip('"\'')

if PipelineContext.register_context(PACKAGE_WITH_PIPELINE_CONTEXT) is None:
    raise Exception('PipelineContext in package "{}" not found!'.format(PACKAGE_WITH_PIPELINE_CONTEXT))

logging.info(f'Active PipelineContext: "{PACKAGE_WITH_PIPELINE_CONTEXT}"')
logging.info('Waiting requests...')


def create_context(app_settings: dict, package_with_context: str) -> PipelineContext:
    """
    Creates a PipelineContext of specified Package.
    """
    pipeline_contexts = PipelineContext.contexts()

    # Custom modules path.
    custom_modules_path = app_settings.get('GEODATAFLOW__CUSTOM__MODULES__PATH', '')
    custom_modules_path = custom_modules_path.replace('${APP_PATH}', os.path.dirname(__file__))
    custom_modules_path = custom_modules_path.replace('${HOME}', os.path.expanduser('~'))

    # Find & return preferred PipelineContext.
    context_ty = pipeline_contexts.get(package_with_context)
    if context_ty:
        return context_ty(custom_modules={}, custom_modules_path=custom_modules_path)

    raise Exception('PipelineContext in package "{}" not registered!'.format(package_with_context))


@app.on_event('startup')
async def db_setup():
    """
    Init backend datatase.
    """
    await init_db()


@app.get('/api/metadata', response_model=Dict[str, str])
async def get_context():
    """
    Returns metadata describing this API.
    """
    return {
        "ActiveContext": PACKAGE_WITH_PIPELINE_CONTEXT.split('.')[-1],
        "ActivePackage": PACKAGE_WITH_PIPELINE_CONTEXT,
    }


@app.get('/api/workflows', response_model=Dict[str, RequestModel])
async def get_workflows(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns the collection of Workflows requested by one User.

    Args:
        user_id: The User identifier.
    """
    data: Dict[str, RequestModel] = {}

    if not user_id:
        raise HTTPException(status_code=400, detail="The 'user_id' parameter is not optional.")

    rows = await db.execute(select(RequestSchema).where(RequestSchema.user_id == user_id))
    rows = rows.scalars()

    for row in rows:
        request_id = row.workflow_id

        if row.type != RequestType.WORKFLOW:
            continue

        request_ob = RequestModel(
            workflow_id=row.workflow_id,
            user_id=row.user_id,
            created_at=row.created_at,
            terminated_at=row.terminated_at,
            status=row.status.value,
            message=row.message,
            file_result=row.file_result
        )
        data[request_id] = request_ob

    return data


@app.post('/api/workflows', response_model=WorkflowModel)
async def new_workflow(
        payload: WorkflowCreateModel, stageId: str = None, dataType: DataStageType = None, db: AsyncSession = Depends(get_db)):
    """
    Create and run new GeodataFlow pipeline.

    Args:
        payload: The data of the request.
    """
    start_time = time.time()

    workflow_id = str(uuid.uuid1())
    workflow = WorkflowModel(id=workflow_id, **payload.dict())

    # Input parameters of request.
    request_args = \
        json.loads(JsonComments.remove_comments(payload.input.splitlines(), keep_ends=True)) \
        if isinstance(payload.input, str) else \
        payload.input

    pipeline = request_args.get('pipeline', None)
    pipeline_args = \
        payload.input_args if payload.input_args else request_args.get('pipeline_args', {})

    if not workflow.user_id:
        raise HTTPException(status_code=400, detail='UserId not specified.')
    if not pipeline:
        raise HTTPException(status_code=400, detail='Pipeline not specified.')

    if not isinstance(pipeline, str):
        pipeline_trimmed = replace_item(deepcopy(pipeline), 'fileData', '')
        workflow.input = {'pipeline': pipeline_trimmed}

    output_prefix = os.environ.get('GEODATAFLOW_OUTPUT_FOLDER_PREFIX', os.path.curdir)
    output_folder = os.path.join(output_prefix, workflow_id)
    pipeline_args['outputFolder'] = output_folder
    pipeline_args['workflowId'] = workflow_id

    # Report context where any module can append its own metadata of results.
    report_context = type('ReportContext', (object,), {})
    report_context.info = {
        'workflowId': workflow_id,
        'startTime': datetime.datetime.now().isoformat(),
        'start': time.time(),
        'status': 'WORKING',
        'message': '',
        'endTime': None,
        'end': None,
        'elapsedTime': None
    }
    if stageId and dataType:
        report_context.info['dataOfStage'] = {}

    # Create PipelineContext for this request.
    with create_context(app_settings, PACKAGE_WITH_PIPELINE_CONTEXT) as context:
        #
        logging.debug('New request: "{}"'.format(json.dumps(request_args)))

        # Execute the Workflow.
        with context.processing_args() as processing_args:
            #
            try:
                # Register new Request.
                db_request = RequestSchema(
                    workflow_id=workflow_id,
                    type=RequestType.PROPERTY if stageId and dataType else RequestType.WORKFLOW,
                    user_id=workflow.user_id,
                    created_at=datetime.datetime.now(),
                    status=RequestStatus.WORKING
                )
                db.add(db_request)
                await db.commit()

                os.makedirs(output_folder, exist_ok=True)

                # Inject a Dict() as Report context where any module can append its own metadata of results.
                setattr(processing_args, 'reportContext', report_context)

                # Load workflow.
                pipeline_ob = PipelineManager(context=context, config=app_settings)
                pipeline_ob.load_from_json(pipeline, pipeline_args)

                # Redefine 'connectionString' of Writers, writing results into current 'OuputFolder'.
                writers = [obj for obj in pipeline_ob.objects(recursive=True) if isinstance(obj, AbstractWriter)]
                for writer in writers:
                    if hasattr(writer, 'connectionString'):
                        tempString = writer.connectionString
                        writer.connectionString = os.path.join(output_folder, os.path.basename(tempString))

                # Run!
                if stageId and dataType:
                    data = pipeline_ob.data_of_stage(stageId, dataType, processing_args)
                    report_context.info['dataOfStage'] = data
                else:
                    pipeline_ob.run(processing_args)

                # Packing results to ZIP?
                if pipeline_args.get('packOutputs', False):
                    zip_file = os.path.join(output_folder, 'output.zip')
                    zip_file = os.fspath(pathlib.Path(zip_file))

                    with zipfile.ZipFile(zip_file, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
                        dir = pathlib.Path(output_folder)

                        for entry in dir.rglob('*'):
                            fn = os.fspath(entry)
                            if fn != zip_file:
                                zf.write(entry, entry.relative_to(dir))

                    report_context.info['fileResult'] = zip_file

                report_context.info['status'] = 'OK'
                report_context.info['message'] = 'SUCCESS'
            except Exception as e:
                report_context.info['status'] = 'ERROR'
                report_context.info['message'] = str(e)
                logging.error(e)
            finally:
                elapsed_time = time.time() - start_time
                elapsed_time = datetime.datetime.utcfromtimestamp(elapsed_time)
                elapsed_text = str(elapsed_time)
                elapsed_text = elapsed_text[elapsed_text.index(' ') + 1:]

                report_context.info['endTime'] = datetime.datetime.now().isoformat()
                report_context.info['end'] = time.time()
                report_context.info['elapsedTime'] = elapsed_text

                # Update metadata of Request.
                db_request = await db.execute(
                    select(RequestSchema).where(RequestSchema.workflow_id == workflow_id)
                )
                db_request = db_request.scalars().first()
                db_request.terminated_at = datetime.datetime.now()
                db_request.status = \
                    RequestStatus.OK if report_context.info['status'] == 'OK' else RequestStatus.ERROR

                db_request.message = report_context.info['message']
                db_request.file_result = report_context.info.get('fileResult')
                db.add(db_request)
                await db.commit()

                logging.info('--- OK: Process successfully finalized! Elapsed=[{0}]'.format(elapsed_text))

            pass

    # Send results.
    workflow.terminated_at = datetime.datetime.now()
    workflow.result = ProcessingUtils.object_as_dict(report_context)
    return workflow


@app.post('/api/objects', response_model=Dict)
async def data_of_stage(
        payload: WorkflowCreateModel, stageId: str, dataType: DataStageType, db: AsyncSession = Depends(get_db)):
    """
    Get data of a Stage in a GeodataFlow pipeline.

    Args:
        payload: The data of the request.
        stageId: The StageId from which data is obtained.
        dataType: The data tyoe to ftech from a Stage.
    """
    if not stageId:
        raise HTTPException(status_code=400, detail='stageId not specified.')
    if not dataType:
        raise HTTPException(status_code=400, detail='dataType not specified.')

    workflow = await new_workflow(payload=payload, stageId=stageId, dataType=dataType, db=db)
    return workflow


@app.get('/api/modules', response_model=Dict)
async def get_modules():
    """
    Returns the collection of available Modules of GeodataFlow.
    """
    with create_context(app_settings, PACKAGE_WITH_PIPELINE_CONTEXT) as context:
        catalog = context.catalog()

    return catalog


def replace_item(obj: Any, key: str, replace_value: str):
    """
    Recursively replace dictionary values with a matching key.
    """
    if isinstance(obj, list):
        for item in obj:
            replace_item(item, key, replace_value)
    else:
        for k, v in obj.items():
            if isinstance(v, dict):
                obj[k] = replace_item(v, key, replace_value)

        if key in obj:
            obj[key] = replace_value

    return obj
