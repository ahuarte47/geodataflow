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
import logging
import unittest
from typing import Dict, Iterable

from geodataflow.core.settingsmanager import ApplicationSettings
from geodataflow.pipeline.pipelinecontext import PipelineContext
from geodataflow.pipeline.pipelinemanager import PipelineManager

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')


class TestGeodataFlowWithCore(unittest.TestCase):
    """
    Tests for `geodataflow.core` package.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    def setUp(self):
        """
        Set up test fixtures, if any.
        """
        custom_modules_path = os.path.join(DATA_FOLDER, 'modules')

        self.app_settings = \
            ApplicationSettings.load_from_dict({'GEODATAFLOW__CUSTOM__MODULES__PATH': custom_modules_path})

        pass

    def tearDown(self):
        """
        Tear down test fixtures, if any.
        """
        pass

    def create_context(self) -> PipelineContext:
        """
        Returns a PipelineContext for this unittest.
        """
        app_settings = self.app_settings

        # Custom modules path.
        custom_modules_path = app_settings.get('GEODATAFLOW__CUSTOM__MODULES__PATH', '')
        custom_modules_path = custom_modules_path.replace('${APP_PATH}', os.path.dirname(__file__))
        custom_modules_path = custom_modules_path.replace('${HOME}', os.path.expanduser('~'))

        # Returns basic Context.
        return PipelineContext(custom_modules={}, custom_modules_path=custom_modules_path)

    def process_pipeline(self, test_func: callable, pipeline_file: str, pipeline_args: Dict[str, str] = {}) -> Iterable:
        """
        Process the specified Pipeline file and returns the collection of Features.
        """
        features = list()

        def output_callback(pipeline_ob, processing_args, writer, feature, callback_args):
            """
            Append Feature/Dataset to results.
            """
            features.append(feature)

        with self.create_context() as context:
            #
            with context.processing_args() as processing_args:
                #
                pipeline_args['--pipeline.TEST_DATA_PATH'] = DATA_FOLDER
                pipeline_args['--pipeline.TEST_OUTPUT_PATH'] = processing_args.temp_data_path()

                # Load & Run workflow.
                pipeline = PipelineManager(context=context, config=self.app_settings)
                pipeline.load_from_file(pipeline_file, pipeline_args)
                pipeline.run(processing_args, output_callback, {})

                # Validate results.
                test_func(features)
                features.clear()

        pass

    def test_catalog(self):
        """
        Test Catalog.
        """
        with self.create_context() as context:
            catalog = context.catalog()
            self.assertGreater(len(catalog), 1)

        pass

    def test_reader_writer(self):
        """
        Test Workflow with basic graph of operations.
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_reader_writer.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 3)
            self.assertEqual(features[0]['properties'].get('id'), 0)
            self.assertEqual(features[1]['properties'].get('id'), 1)
            self.assertEqual(features[2]['properties'].get('id'), 2)

        self.process_pipeline(test_func, pipeline_file)
        pass


if __name__ == '__main__':
    """
    Run tests.
    """
    unittest.main()
