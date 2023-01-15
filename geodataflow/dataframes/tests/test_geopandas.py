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
import importlib
import unittest
from typing import Dict, Iterable

from geodataflow.core.settingsmanager import ApplicationSettings
from geodataflow.pipeline.pipelinecontext import PipelineContext
from geodataflow.pipeline.pipelinemanager import PipelineManager
from geodataflow.spatial.commonutils import GeometryUtils
from geodataflow.dataframes.geopandascontext import GeoPandasPipelineContext

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')


class TestGeodataFlowWithGeoPandas(unittest.TestCase):
    """
    Tests for `geodataflow.dataframes` package.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    def setUp(self):
        """
        Set up test fixtures, if any.
        """
        self.app_settings = \
            ApplicationSettings.load_from_dict({'GEODATAFLOW__CUSTOM__MODULES__PATH': ''})

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
        return GeoPandasPipelineContext(custom_modules={}, custom_modules_path=custom_modules_path)

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

    def schema_of_stage(self, pipeline_file: str, stageId: str, pipeline_args: Dict[str, str] = {}) -> Dict:
        """
        Get the Schema of a Stage in the specified Pipeline file.
        """
        with self.create_context() as context:
            #
            with context.processing_args() as processing_args:
                #
                pipeline_args['--pipeline.TEST_DATA_PATH'] = DATA_FOLDER

                # Load workflow & Get Schema.
                pipeline = PipelineManager(context=context, config=self.app_settings)
                pipeline.load_from_file(pipeline_file, pipeline_args)
                schema_def = pipeline.get_schema(processing_args, stageId)

                return schema_def

    def test_catalog(self):
        """
        Test Catalog.
        """
        with self.create_context() as context:
            catalog = context.catalog()
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

    def test_feature_query(self):
        """
        Test Query module (GeoPandas).
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_feature_query.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 1)
            feature = features[0]
            self.assertEqual(feature.type, 'Feature')
            self.assertEqual(feature.geometry.geom_type, 'Polygon')
            self.assertEqual(GeometryUtils.get_srid(feature.geometry), 4326)
            self.assertEqual(feature.properties['tileId'], '30TXM')

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_feature_eval(self):
        """
        Test Eval module (GeoPandas).
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_feature_eval.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 1)
            feature = features[0]
            self.assertEqual(feature.type, 'Feature')
            self.assertEqual(feature.geometry.geom_type, 'Polygon')
            self.assertEqual(GeometryUtils.get_srid(feature.geometry), 4326)
            self.assertEqual(feature.properties['tileId'], '30TXM')
            self.assertEqual(feature.properties['lowerTileId'], '30txm')

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_feature_buffer(self):
        """
        Test GeometryBuffer module.
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

    def test_feature_to_csv(self):
        """
        Test GeometryTransform module.
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_feature_to_csv.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 1)
            feature = features[0]
            self.assertEqual(feature.type, 'Feature')
            self.assertEqual(feature.geometry.geom_type, 'MultiPolygon')

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

    def test_gee_collection_catalog(self):
        """
        Test GEEProductCatalog module (Google Earth Engine).
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_gee_collection_catalog.json')

        ee_api_spec = importlib.util.find_spec('ee')
        if ee_api_spec is None:
            self.logger.warning('Package "earthengine-api" is not installed, skipping test.')
            return

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 2)
            feature = features[0]
            self.assertEqual(feature.type, 'Feature')
            self.assertEqual(feature.geometry.geom_type, 'Polygon')
            self.assertEqual(GeometryUtils.get_srid(feature.geometry), 4326)

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_gee_collection_dataset(self):
        """
        Test GEEProductDataset module (Google Earth Engine).
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_gee_collection_dataset.json')

        ee_api_spec = importlib.util.find_spec('ee')
        if ee_api_spec is None:
            self.logger.warning('Package "earthengine-api" is not installed, skipping test.')
            return

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 1)
            feature = features[0]
            self.assertEqual(feature.type, 'Raster')
            self.assertEqual(feature.geometry.geom_type, 'Polygon')
            self.assertEqual(GeometryUtils.get_srid(feature.geometry), 25830)
            dataset = feature.dataset()
            self.assertEqual(dataset.RasterCount, 3)
            self.assertEqual(dataset.RasterXSize, 1555)
            self.assertEqual(dataset.RasterYSize, 999)

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
            self.assertEqual(feature.type, 'Feature')
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

    def test_raster_stats(self):
        """
        Test RasterStats module.
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_raster_stats.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 1)
            feature = features[0]
            self.assertEqual(feature.type, 'Feature')
            self.assertEqual(feature.geometry.geom_type, 'Polygon')
            self.assertAlmostEqual(feature.properties['min'], 0.17168459296226501, places=8)
            self.assertAlmostEqual(feature.properties['max'], 0.38235294818878174, places=8)
            self.assertAlmostEqual(feature.properties['mean'], 0.2934800447537696, places=8)
            self.assertEqual(feature.properties['size'], 1178)

        self.process_pipeline(test_func, pipeline_file)
        pass

    def test_raster_plot_timeseries(self):
        """
        Test RasterStats module.
        """
        pipeline_file = os.path.join(DATA_FOLDER, 'test_raster_plot_timeseries.json')

        def test_func(features):
            """ Test results """
            self.assertEqual(len(features), 1)
            feature = features[0]
            self.assertEqual(feature.type, 'Raster')
            self.assertEqual(feature.geometry.geom_type, 'Polygon')
            dataset = feature.dataset()
            self.assertEqual(dataset.RasterCount, 4)
            self.assertEqual(dataset.RasterXSize, 800)
            self.assertEqual(dataset.RasterYSize, 600)

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
