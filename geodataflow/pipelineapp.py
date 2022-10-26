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
import sys
import time
import datetime
import logging
import traceback
import argparse
import json
from typing import List

package_path = os.path.dirname(os.path.dirname(__file__))
if package_path not in sys.path:
    sys.path.insert(0, package_path)

try:
    from geodataflow.core.common import JSONDateTimeEncoder
    from geodataflow.core.processingargs import ProcessingUtils
    from geodataflow.geoext.gdalenv import GdalEnv
    from geodataflow.pipeline.basictypes import AbstractReader, AbstractFilter, AbstractWriter
    from geodataflow.pipeline.pipelinemanager import PipelineManager
except Exception as e:
    raise e


def pipeline_app(command_args: List[str] = None):
    """
    GeodataFlow console application.
    """
    start_time = time.time()

    if not command_args:
        command_args = sys.argv

    # Define the command parameters of the application.
    parser = argparse.ArgumentParser()
    parser.add_argument('--pipeline_file', dest='pipeline_file', required=False, action='store',
                        help='Pipeline file to process.', default='')
    parser.add_argument('--settings_file', dest='settings_file', required=False, action='store',
                        help='Settings file to load (Optional).', default='')
    parser.add_argument('--modules', dest='modules', required=False, action='store_true',
                        help='Show metadata of available Modules and exit without executing the Pipeline.',
                        default='')
    parser.add_argument('--ui_mode', dest='ui_mode', required=False, action='store_true',
                        help='UI mode, the processing task shows a progress bar.')
    #
    parser.add_argument('--temp_path', action='store', required=False,
                        help='Directory to use as temporal folder (Optional).', dest='temp_path', default='')
    parser.add_argument('--log_level', action='store', required=False,
                        help='LOG level to notify application messages (Optional).', dest='log_level',
                        default='INFO')
    parser.add_argument('--log_file', action='store', required=False, help='LOG output file (Optional).',
                        dest='log_file', default='')
    #
    args, pipeline_args = parser.parse_known_args(command_args)

    # Logging application initialization.
    logging_file = None
    if args.pipeline_file:
        logging_file = os.path.splitext(args.pipeline_file)[0] + '.log'
    if args.log_file:
        logging_file = args.log_file
    #
    logging.basicConfig(level=args.log_level, format="[%(levelname)s]: %(message)s")
    #
    if logging_file:
        logging_root = logging.getLogger()
        logging_file_handler = logging.FileHandler(logging_file, mode='w')
        logging_file_handler.setLevel(logging_root.level)
        logging_file_handler.setFormatter(logging_root.handlers[0].formatter)
        logging_root.addHandler(logging_file_handler)

    logging.info('========================================================================')
    logging.info('GeodataFlow:')
    logging.info('Toolkit to run workflows on Geospatial & Earth Observation (EO) data.')
    logging.info('========================================================================')
    logging.info('')

    # Show metadata of available modules and exit?
    if args.modules:
        logging.info('Available Modules...')

        objects = [module_def() for module_def in PipelineManager.modules()]
        objects = sorted(objects, key=lambda obj: obj.className, reverse=False)
        modules_txt = '\n'

        def info_of_module(module):
            """
            Returns info of specified module.
            """
            params_info = ''.join(
                ['\n\t  {}: {}'.format(k, v.get('description')) for k, v in module.params().items()]
            )
            if not params_info:
                params_info = '\n\t  NONE'

            return '  > {}: {}\n\tParams: {}\n'.format(module.className, module.description(), params_info)

        modules_txt += '+ DataSources:\n'

        for obj in [o for o in objects if isinstance(o, (AbstractReader, AbstractWriter))]:
            modules_txt += info_of_module(obj)

        modules_txt += '+ Filters:\n'

        for obj in [o for o in objects if isinstance(o, (AbstractFilter))]:
            modules_txt += info_of_module(obj)

        logging.info(modules_txt)
        logging.warning('The "--modules" flag is present, so exiting...')
        return

    # Initialize the default Settings Manager.
    if not args.settings_file:
        args.settings_file = os.path.splitext(os.path.abspath(__file__))[0] + '.default.settings'

    from geodataflow.core.settingsmanager import Singleton
    app_settings = Singleton.load_from_file(args.settings_file)

    logging.info('Processing file "{}"...'.format(args.pipeline_file))

    # Report context where any module can append its own metadata of results.
    report_context = type('ReportContext', (object,), {})
    report_context.info = {
        'pipelineFile': os.path.basename(args.pipeline_file),
        'startTime': datetime.datetime.now().isoformat(),
        'start': time.time(),
        'status': 'WORKING',
        'message': '',
        'endTime': None,
        'end': None,
        'elapsedTime': None
    }

    # Execute the Workflow.
    with GdalEnv(config_options=GdalEnv.default_options(), temp_path=args.temp_path) as processing_args:
        #
        try:
            if not args.pipeline_file or not os.path.exists(args.pipeline_file):
                raise Exception('Pipeline file not specified!')

            setattr(processing_args, 'ui_mode', ProcessingUtils.strtobool(args.ui_mode))

            # Inject a Dict() as Report context where any module can append its own metadata of results.
            setattr(processing_args, 'reportContext', report_context)

            # Custom modules path.
            custom_modules_path = app_settings.get('GEODATAFLOW__CUSTOM__MODULES__PATH', '')
            custom_modules_path = custom_modules_path.replace('${APP_PATH}', os.path.dirname(__file__))
            custom_modules_path = custom_modules_path.replace('${HOME}', os.path.expanduser('~'))

            # Load & Run workflow.
            pipeline = PipelineManager(config=app_settings, custom_modules_path=custom_modules_path)
            pipeline.load_from_file(args.pipeline_file, pipeline_args)
            pipeline.run(processing_args)

            report_context.info['status'] = 'SUCCESS'
            report_context.info['message'] = 'OK'
        except Exception as e:
            report_context.info['status'] = 'ERROR'
            report_context.info['message'] = str(e)
            logging.error(e)
            traceback.print_exc(file=sys.stdout)
        finally:
            elapsed_time = time.time() - start_time
            elapsed_time = datetime.datetime.utcfromtimestamp(elapsed_time)
            elapsed_text = str(elapsed_time)
            elapsed_text = elapsed_text[elapsed_text.index(' ') + 1:]

            report_context.info['endTime'] = datetime.datetime.now().isoformat()
            report_context.info['end'] = time.time()
            report_context.info['elapsedTime'] = elapsed_text

            if logging_file:
                report_file = os.path.splitext(logging_file)[0] + '.report.json'
                obj = ProcessingUtils.object_as_dict(report_context)
                with open(report_file, mode='w') as fp:
                    json.dump(obj, fp, indent=2, cls=JSONDateTimeEncoder)

            logging.info('--- OK: Process successfully finalized! Elapsed=[{0}]'.format(elapsed_text))
            logging_root = logging.getLogger()
            logging_root.handlers.clear()

    pass


if __name__ == '__main__':
    pipeline_app(command_args=sys.argv[1:])
