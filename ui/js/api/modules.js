var modules = {"ConnectionJoin": {"name": "ConnectionJoin", "type": "filter", "alias": "ConnectionJoin", "category": "Graph", "description": "Joins the streams of data of several input Modules in one unique output.", "params": {"stages": {"description": "Collection of Modules (Using the \"StageId\" attribute) to merge.", "dataType": "array<string>"}}}, "TableEval": {"name": "TableEval", "type": "filter", "alias": "Eval", "category": "Table", "description": "Evaluates a string describing operations on GeoPandas DataFrame columns.", "params": {"expression": {"description": "The query to evaluate. Operates on columns only, not specific rows.", "dataType": "calc"}}}, "RasterWriter": {"name": "RasterWriter", "type": "writer", "alias": "RasterWriter", "category": "Output", "description": "Writes Datasets to a Geospatial RasterStore using GDAL providers.", "params": {"connectionString": {"description": "Connection string of the Raster Store (Common GDAL extensions are supported).", "dataType": "string", "default": "output.tif", "extensions": [".tif", ".ecw", ".jp2", ".png", ".jpg"]}, "formatOptions": {"description": "GDAL format options of output Dataset (Optional).", "dataType": "string", "default": "-of COG"}}}, "FeatureLimit": {"name": "FeatureLimit", "type": "filter", "alias": "Limits", "category": "Feature", "description": "Validates that input Geometries do not be greater than a Limit.", "params": {"fullAreaLimit": {"description": "Maximum area covered by all input Geometries (Optional).", "dataType": "float"}, "areaLimit": {"description": "Maximum area covered by each input Geometry (Optional).", "dataType": "float"}, "countLimit": {"description": "Maximum number of input Geometries (Optional).", "dataType": "int"}}}, "TableQuery": {"name": "TableQuery", "type": "filter", "alias": "Query", "category": "Table", "description": "Queries the columns of a GeoPandas DataFrame with a boolean expression.", "params": {"expression": {"description": "The query string to evaluate. You can refer to variables in the environment by prefixing them with an \u2018@\u2019 character like @a + @b.", "dataType": "filter"}}}, "SpatialRelation": {"name": "SpatialRelation", "type": "filter", "alias": "SpatialRelation", "category": "Geometry", "description": "Returns input Features that match a Spatial Relationship with one or more other Geometries.", "params": {"relationship": {"description": "Spatial Relationship to validate, 'Intersects' by default.", "dataType": "int", "default": 3, "options": [1, 2, 3, 4, 5, 6, 7, 8], "labels": ["Equals", "Disjoint", "Intersects", "Touches", "Crosses", "Within", "Contains", "Overlaps"]}, "otherGeometries": {"description": "Collection of Geometries with which input Features should validate a Spatial Relationship.", "dataType": "input"}}}, "EOProductDataset": {"name": "EOProductDataset", "type": "filter", "alias": "Dataset", "category": "EO STAC Imagery", "description": "Extracts Datasets from EO/STAC Collections via spatial & alphanumeric filters.", "params": {"driver": {"description": "Driver class name that implements EO Providers.", "dataType": "string", "default": "STAC", "options": ["STAC", "EODAG"], "labels": ["STAC", "EODAG"]}, "provider": {"description": "Provider name or API Endpoint that provides info about EO Products.", "dataType": "string", "default": "https://earth-search.aws.element84.com/v0/search"}, "product": {"description": "EO Product type or Collection from which to fetch data.", "dataType": "string", "default": "sentinel-s2-l2a-cogs"}, "startDate": {"description": "Start date of EO Products to fetch (Optional). \"$TODAY()\" is supported.", "dataType": "date"}, "endDate": {"description": "End date of EO Products to fetch (Optional). \"$TODAY()\" is supported.", "dataType": "date"}, "closestToDate": {"description": "Select only those EO Products which Date is the closest to the specified (Optional).", "dataType": "date"}, "windowDate": {"description": "Days around \"closestToDate\" when \"startDate\" and \"endDate\" are not specified.", "dataType": "int", "default": 5}, "filter": {"description": "Attribute filter string of EO Products to fetch (Optional).", "dataType": "filter"}, "preserveInputCrs": {"description": "Preserve input CRS, otherwise Geometries are transformed to \"EPSG:4326\".", "dataType": "bool", "default": true}, "configVars": {"description": "Environment variables separated by commas. Commonly used to configure credentials.", "dataType": "string", "default": "AWS_NO_SIGN_REQUEST=YES"}, "bands": {"description": "List of Bands to fetch, or a string separated by commas. Empty means fetch all.", "dataType": "string", "default": "B04,B03,B02,B08", "placeHolder": "B04,B03,B02,B08"}, "groupByDate": {"description": "Group EO Products by Date.", "dataType": "bool", "default": true}, "clipByAreaOfInterest": {"description": "Clip EO Products by geometry of input AOI.", "dataType": "bool", "default": true}}}, "RasterTransform": {"name": "RasterTransform", "type": "filter", "alias": "Transform", "category": "Raster", "description": "Transforms input Rasters between two Spatial Reference Systems (CRS).", "params": {"sourceCrs": {"description": "Source Spatial Reference System (CRS), SRID, WKT, PROJ formats are supported. It uses input CRS when this param is not specified.", "dataType": "crs", "placeHolder": "EPSG:XXXX or SRID..."}, "targetCrs": {"description": "Output Spatial Reference System (CRS), SRID, WKT, PROJ formats are supported.", "dataType": "crs", "placeHolder": "EPSG:XXXX or SRID..."}, "resampleAlg": {"description": "Resampling strategy.", "dataType": "int", "default": 1, "options": [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12], "labels": ["NearestNeighbour", "Bilinear", "Cubic", "CubicSpline", "Lanczos", "Average", "Mode", "Max", "Min", "Med", "Q1", "Q3"]}}}, "GeometryCentroid": {"name": "GeometryCentroid", "type": "filter", "alias": "Centroid", "category": "Geometry", "description": "Returns the Centroid of input Geometries.", "params": {}}, "RasterSplit": {"name": "RasterSplit", "type": "filter", "alias": "Split", "category": "Raster", "description": "Splits input Rasters to tiles.", "params": {"tileSizeX": {"description": "Size of output tiles in X-direction (Pixels).", "dataType": "int", "default": 512}, "tileSizeY": {"description": "Size of output tiles in Y-direction (Pixels).", "dataType": "int", "default": 512}, "paddingVal": {"description": "Extra padding to apply to output", "dataType": "int", "default": 0}}}, "EOProductCatalog": {"name": "EOProductCatalog", "type": "filter", "alias": "Catalog", "category": "EO STAC Imagery", "description": "Extracts Metadata from EO/STAC Collections via spatial & alphanumeric filters.", "params": {"driver": {"description": "Driver class name that implements EO Providers.", "dataType": "string", "default": "STAC", "options": ["STAC", "EODAG"], "labels": ["STAC", "EODAG"]}, "provider": {"description": "Provider name or API Endpoint that provides info about EO Products.", "dataType": "string", "default": "https://earth-search.aws.element84.com/v0/search"}, "product": {"description": "EO Product type or Collection from which to fetch data.", "dataType": "string", "default": "sentinel-s2-l2a-cogs"}, "startDate": {"description": "Start date of EO Products to fetch (Optional). \"$TODAY()\" is supported.", "dataType": "date"}, "endDate": {"description": "End date of EO Products to fetch (Optional). \"$TODAY()\" is supported.", "dataType": "date"}, "closestToDate": {"description": "Select only those EO Products which Date is the closest to the specified (Optional).", "dataType": "date"}, "windowDate": {"description": "Days around \"closestToDate\" when \"startDate\" and \"endDate\" are not specified.", "dataType": "int", "default": 5}, "filter": {"description": "Attribute filter string of EO Products to fetch (Optional).", "dataType": "filter"}, "preserveInputCrs": {"description": "Preserve input CRS, otherwise Geometries are transformed to \"EPSG:4326\".", "dataType": "bool", "default": true}}}, "RasterReader": {"name": "RasterReader", "type": "reader", "alias": "RasterReader", "category": "Input", "description": "Reads Datasets from a Geospatial RasterSource using GDAL providers.", "params": {"connectionString": {"description": "Connection string of the Raster Store.", "dataType": ["file", "url"], "extensions": [".tiff", ".tif", ".ecw", ".jp2"]}, "countLimit": {"description": "Maximum number of Datasets to fetch (Optional).", "dataType": "int"}}}, "FeatureWriter": {"name": "FeatureWriter", "type": "writer", "alias": "FeatureWriter", "category": "Output", "description": "Writes Features with Geometries to a Geospatial DataStore using OGR providers.", "params": {"connectionString": {"description": "Connection string of the FeatureStore ('.geojson', '.gpkg', '.shp.zip' are supported).", "dataType": "string", "default": "output.gpkg", "extensions": [".geojson", ".gpkg", ".shp.zip"]}}}, "GeometryTransform": {"name": "GeometryTransform", "type": "filter", "alias": "Transform", "category": "Geometry", "description": "Transforms input Geometries or Rasters between two Spatial Reference Systems (CRS).", "params": {"sourceCrs": {"description": "Source Spatial Reference System (CRS), SRID, WKT, PROJ formats are supported. It uses input CRS when this param is not specified.", "dataType": "crs", "placeHolder": "EPSG:XXXX or SRID..."}, "targetCrs": {"description": "Output Spatial Reference System (CRS), SRID, WKT, PROJ formats are supported.", "dataType": "crs", "placeHolder": "EPSG:XXXX or SRID..."}}}, "RasterCalc": {"name": "RasterCalc", "type": "filter", "alias": "Calc", "category": "Raster", "description": "Performs raster calc algebraical operations to input Rasters.", "params": {"bands": {"description": "List of Band names defined in Expression, or a string separated by commas.", "dataType": "string", "default": "", "placeHolder": "B04,B03,B02,B08"}, "expression": {"description": "Raster calculator expression with numpy syntax, e.g. (B08\u2013B04)/(B08+B04).", "dataType": "calc", "default": "", "placeHolder": "(B08 - B04) / (B08 + B04)"}, "noData": {"description": "NoData value of output Dataset.", "dataType": "float", "default": -9999.0}}}, "TablePack": {"name": "TablePack", "type": "filter", "alias": "Pack", "category": "Table", "description": "Packs input Features into a GeoPandas DataFrame.", "params": {}}, "FeatureReader": {"name": "FeatureReader", "type": "reader", "alias": "FeatureReader", "category": "Input", "description": "Reads Features with Geometries from a Geospatial DataSource using OGR providers.", "params": {"connectionString": {"description": "Connection string of the Feature Store.", "dataType": ["file", "url", "geojson"], "extensions": [".geojson", ".gpkg", ".shp.zip"]}, "where": {"description": "Attribute query string when fetching features (Optional).", "dataType": "filter"}, "spatialFilter": {"description": "Geometry to be used as spatial filter when fetching features (Optional).", "dataType": "geometry"}, "countLimit": {"description": "Maximum number of Features to fetch (Optional).", "dataType": "int"}}}, "InputParam": {"name": "InputParam", "type": "filter", "alias": "InputParam", "category": "Graph", "description": "Acts as Feature provider of a Module's parameter", "params": {}}, "FeatureCache": {"name": "FeatureCache", "type": "filter", "alias": "Cache", "category": "Feature", "description": "Caches data of inputs to speedup the management of repetitive invocations of Modules.", "params": {}}, "GeometryBuffer": {"name": "GeometryBuffer", "type": "filter", "alias": "Buffer", "category": "Geometry", "description": "Computes a buffer area around a geometry having the given width.", "params": {"distance": {"description": "Distance of buffer to apply to input Geometry.", "dataType": "float", "default": 1.0}, "capStyle": {"description": "Caps style.", "dataType": "int", "default": 1, "options": [1, 2, 3], "labels": ["round", "flat", "square"]}, "joinStyle": {"description": "Join style.", "dataType": "int", "default": 1, "options": [1, 2, 3], "labels": ["round", "mitre", "bevel"]}}}, "RasterMosaic": {"name": "RasterMosaic", "type": "filter", "alias": "Mosaic", "category": "Raster", "description": "Merges all input Rasters to one unique Output.", "params": {}}, "RasterClip": {"name": "RasterClip", "type": "filter", "alias": "Clip", "category": "Raster", "description": "Clips input Rasters by a Geometry.", "params": {"clipGeometries": {"description": "Collection of Geometries that will clip input Features.", "dataType": "input"}}}, "TableUnpack": {"name": "TableUnpack", "type": "filter", "alias": "Unpack", "category": "Table", "description": "Unpacks input GeoPandas DataFrames to a stream of Features.", "params": {}}};