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
import unittest
from typing import Dict, Iterable

from geodataflow.core.settingsmanager import Singleton
from geodataflow.pipeline.pipelinemanager import PipelineManager
from geodataflow.geoext.gdalenv import GdalEnv
from geodataflow.geoext.commonutils import GeometryUtils

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')


class TestGeodataFlow(unittest.TestCase):
    """
    Tests for `geodataflow` package.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    def setUp(self):
        """
        Set up test fixtures, if any.
        """
        self.app_settings = Singleton.load_from_dict({'GEODATAFLOW__CUSTOM__MODULES__PATH': ''})
        pass

    def tearDown(self):
        """
        Tear down test fixtures, if any.
        """
        pass

    def schema_of_stage(self, pipeline_file: str, stageId: str, pipeline_args: Dict[str, str] = {}) -> Dict:
        """
        Get the Schema of a Stage in the specified Pipeline file.
        """
        with GdalEnv(config_options=GdalEnv.default_options(), temp_path=None) as processing_args:
            #
            app_settings = self.app_settings
            pipeline_args['--pipeline.TEST_DATA_PATH'] = DATA_FOLDER

            # Custom modules path.
            custom_modules_path = app_settings.get('GEODATAFLOW__CUSTOM__MODULES__PATH', '')
            custom_modules_path = custom_modules_path.replace('${APP_PATH}', os.path.dirname(__file__))
            custom_modules_path = custom_modules_path.replace('${HOME}', os.path.expanduser('~'))

            # Load workflow & Get Schema.
            pipeline = PipelineManager(config=app_settings, custom_modules_path=custom_modules_path)
            pipeline.load_from_file(pipeline_file, pipeline_args)
            schema_def = pipeline.get_schema(processing_args, stageId)

            return schema_def

    def process_pipeline(self, test_func: callable, pipeline_file: str, pipeline_args: Dict[str, str] = {}) -> Iterable:
        """
        Process the specified Pipeline file and returns the collection of Features.
        """
        features = list()

        def output_callback(pipeline_ob, processing_args, writer, feature, callback_args):
            """
            Append Feature/Dataset to buffer.
            """
            features.append(feature)

        with GdalEnv(config_options=GdalEnv.default_options(), temp_path=None) as processing_args:
            #
            app_settings = self.app_settings
            pipeline_args['--pipeline.TEST_DATA_PATH'] = DATA_FOLDER
            pipeline_args['--pipeline.TEST_OUTPUT_PATH'] = processing_args.temp_data_path()

            # Custom modules path.
            custom_modules_path = app_settings.get('GEODATAFLOW__CUSTOM__MODULES__PATH', '')
            custom_modules_path = custom_modules_path.replace('${APP_PATH}', os.path.dirname(__file__))
            custom_modules_path = custom_modules_path.replace('${HOME}', os.path.expanduser('~'))

            # Load & Run workflow.
            pipeline = PipelineManager(config=app_settings, custom_modules_path=custom_modules_path)
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
        catalog = PipelineManager.catalog()
        self.assertGreater(len(catalog), 1)
        pass

    def test_input_from_feature_collection(self):
        """
        Test Workflow reading features from an embebbed GeoJson FeatureCollection.
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_input_from_feature_collection.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 1)
            feature = features[0]
            self.assertEqual(feature.type, 'Feature')
            self.assertEqual(feature.geometry.geom_type, 'Polygon')
            self.assertAlmostEqual(feature.geometry.area, 0.0164884, places=6)

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_input_from_file_data(self):
        """
        Test Workflow reading features from an embebbed FileData (Base64).
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_input_from_file_data.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 1)
            feature = features[0]
            self.assertEqual(feature.type, 'Feature')
            self.assertEqual(feature.geometry.geom_type, 'MultiPolygon')
            self.assertEqual(len(feature.geometry.geoms), 1)
            self.assertAlmostEqual(feature.geometry.area, 1.0896490, places=6)

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_feature_centroid(self):
        """
        Test GeometryCentroid module.
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_feature_centroid.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 1)
            feature = features[0]
            self.assertEqual(feature.type, 'Feature')
            self.assertEqual(feature.geometry.geom_type, 'Point')
            self.assertAlmostEqual(feature.geometry.x, -1.6527555, places=6)
            self.assertAlmostEqual(feature.geometry.y, 42.8170465, places=6)

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_feature_buffer(self):
        """
        Test GeometryCentroid module.
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_feature_buffer.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 1)
            feature = features[0]
            self.assertEqual(feature.type, 'Feature')
            self.assertEqual(feature.geometry.geom_type, 'Polygon')
            self.assertAlmostEqual(feature.geometry.area, 0.0223177, places=6)

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_geopandas(self):
        """
        Test Geopandas integration.
        """
        try:
            import geopandas  # noqa: F401

            pipeline_file = os.path.join(DATA_FOLDER, 'test_geopandas.json')

            def test_func(features):
                """ Test results """
                self.assertEqual(len(features), 1)
                feature = features[0]
                self.assertEqual(feature.type, 'Feature')
                self.assertEqual(feature.geometry.geom_type, 'Polygon')
                self.assertEqual(GeometryUtils.get_srid(feature.geometry), 4326)
                self.assertEqual(feature.properties['tileId'], '30TXM')

            self.process_pipeline(test_func, pipeline_file)
        except ModuleNotFoundError as e:
            self.logger.warning('Ignoring "test_geopandas" test. {}'.format(str(e)))

        pass

    def test_feature_transform(self):
        """
        Test GeometryTransform module.
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_feature_transform.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 1)
            feature = features[0]
            self.assertEqual(feature.type, 'Feature')
            self.assertEqual(feature.geometry.geom_type, 'Polygon')
            self.assertEqual(GeometryUtils.get_srid(feature.geometry), 25830)
            self.assertAlmostEqual(feature.geometry.area, 149725216.7391, places=3)

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_eo_stac_catalog(self):
        """
        Test EOProductCatalog module (STAC provider).
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_eo_stac_catalog.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 2)
            feature = features[0]
            self.assertEqual(feature.type, 'Feature')
            self.assertEqual(feature.geometry.geom_type, 'Polygon')
            self.assertEqual(GeometryUtils.get_srid(feature.geometry), 4326)
            self.assertTrue(any('WN' in feature.properties['sentinel:grid_square'] for feature in features))
            self.assertTrue(any('XN' in feature.properties['sentinel:grid_square'] for feature in features))

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_eo_stac_dataset(self):
        """
        Test EOProductDataset module (STAC provider).
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_eo_stac_dataset.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 1)
            feature = features[0]
            self.assertEqual(feature.type, 'Raster')
            self.assertEqual(feature.geometry.geom_type, 'Polygon')
            self.assertEqual(GeometryUtils.get_srid(feature.geometry), 4326)
            metadata = feature.get_metadata()
            self.assertEqual(metadata['rasterCount'], 2)
            self.assertAlmostEqual(metadata['pixelSizeX'], 0.000106, places=5)
            self.assertAlmostEqual(metadata['pixelSizeY'], 0.000106, places=5)

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_raster_to_vector(self):
        """
        Test Workflow converting raster to vector.
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_raster_to_vector.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 1)
            feature = features[0]
            self.assertEqual(feature.type, 'Raster')
            self.assertEqual(feature.geometry.geom_type, 'Polygon')

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_raster_calc(self):
        """
        Test Workflow applying a band expression to a raster.
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_raster_calc.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 1)
            feature = features[0]
            self.assertEqual(feature.type, 'Raster')
            self.assertEqual(feature.geometry.geom_type, 'Polygon')
            dataset = feature.dataset()
            self.assertEqual(dataset.RasterCount, 1)
            self.assertEqual(dataset.RasterXSize, 201)
            self.assertEqual(dataset.RasterYSize, 201)

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_raster_clip(self):
        """
        Test Workflow applying a clipping operation to a raster.
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_raster_clip.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 1)
            feature = features[0]
            self.assertEqual(feature.type, 'Raster')
            self.assertEqual(feature.geometry.geom_type, 'Polygon')
            dataset = feature.dataset()
            self.assertEqual(dataset.RasterCount, 4)
            self.assertEqual(dataset.RasterXSize, 38)
            self.assertEqual(dataset.RasterYSize, 31)

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_raster_transform(self):
        """
        Test RasterTransform module.
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_raster_transform.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 1)
            feature = features[0]
            self.assertEqual(feature.type, 'Raster')
            self.assertEqual(feature.geometry.geom_type, 'Polygon')
            self.assertEqual(GeometryUtils.get_srid(feature.geometry), 25830)
            metadata = feature.get_metadata()
            self.assertEqual(metadata['srid'], 25830)

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_schema_of_stage(self):
        """
        Test reading the Schema of a Stage.
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_eo_stac_catalog.json')

        schema_def = self.schema_of_stage(pipeline_file, 'my-stage-0')
        self.assertIsNotNone(schema_def)
        schema_def = self.schema_of_stage(pipeline_file, 'my-stage-1')
        self.assertIsNotNone(schema_def)
        schema_def = self.schema_of_stage(pipeline_file, 'my-stage-2')
        self.assertIsNotNone(schema_def)
        pass

    def test_spatial_intersects(self):
        """
        Test reading the Schema of a Stage.
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_spatial_intersects.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 2)

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_spatial_contains(self):
        """
        Test reading the Schema of a Stage.
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_spatial_contains.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 1)

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_spatial_disjoint(self):
        """
        Test reading the Schema of a Stage.
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_spatial_disjoint.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 2)

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_spatial_within(self):
        """
        Test reading the Schema of a Stage.
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_spatial_within.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 0)

        self.process_pipeline(test_func, pipeline_file)
        pass


if __name__ == '__main__':
    """
    Run tests.
    """
    unittest.main()
