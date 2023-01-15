# geodataflow.dataframes

GeodataFlow backend implementation with [GeoPandas](https://geopandas.org/) (GeoDataFrames).

**GeodataFlow** is a Geoprocessing framework for fetching, translating and manipulating Geospatial data (*Raster*, *Vector*, *EO/STAC collections*) by using a *Pipeline* or sequence of operations on input data. It is very much like the [_GDAL_](https://gdal.org/) library which handles raster and vector data.

The project is split up into several namespace packages. `geodataflow.dataframes` implements a backend for GeodataFlow using the GeoPandas library and other common OSGeo python packages. This package includes the `geodataflow.core` and `geodataflow.spatial` subpackages.

Although `geodataflow.dataframes` provides a list of useful modules, since Backend implementations for **GeodataFlow** load them using the paradigm of plugins, developers can easily write new operations and the list may grow up in the future.

### Workflow examples

Assuming you are using `geodataflow.dataframes` (GeoPandas) as active backend implementation, **GeodataFlow** can run workflows as the following:

+ Converting a Shapefile to GeoPackage:
  ```bash
  # ==============================================================
  # Pipeline sample to convert a Shapefile to GeoPackage.
  # ==============================================================
  {
    "pipeline": [
      {
        "type": "FeatureReader",
        "connectionString": "input.shp"
      },
      # Extract the Centroid of input geometries.
      {
        "type": "GeometryCentroid"
      },
      # Transform CRS of geometries.
      {
        "type": "GeometryTransform",
        "sourceCrs": 4326,
        "targetCrs": 32630
      },
      # Save features to Geopackage.
      {
        "type": "FeatureWriter",
        "connectionString": "output.gpkg"
      }
    ]
  }
  ```

+ Fetching metadata of a S2L2A Product (STAC):
  ```bash
  # ==============================================================
  # Pipeline sample to fetch metadata of a S2L2A Product (STAC).
  # ==============================================================
  {
    "pipeline": [
      {
        "type": "FeatureReader",

        # Define the input AOI in an embedded GeoJson.
        "connectionString": {
          "type": "FeatureCollection",
          "crs": {
            "type": "name",
            "properties": { "name": "EPSG:4326" }
          },
          "features": [
            {
              "type": "Feature",
              "properties": { "id": 0, "name": "My AOI for testing" },
              "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-1.746826,42.773227],
                    [-1.746826,42.860866],
                    [-1.558685,42.860866],
                    [-1.558685,42.773227],
                    [-1.746826,42.773227]
                ]]
              }
            }
          ]
        }
      },
      # Transform CRS of geometries.
      {
        "type": "GeometryTransform",
        "sourceCrs": 4326,
        "targetCrs": 32630
      },
      # Fetch metadata of EO Products that match one SpatioTemporial criteria.
      {
        "type": "EOProductCatalog",

        "driver": "STAC",
        "provider": "https://earth-search.aws.element84.com/v0/search",
        "product": "sentinel-s2-l2a-cogs",

        "startDate": "2021-09-25",
        "endDate": "2021-10-05",
        "closestToDate": "2021-09-30",
        "filter": "",

        "preserveInputCrs": true
      },
      # Save features to Geopackage.
      {
        "type": "FeatureWriter",
        "connectionString": "output.gpkg"
      }
    ]
  }
  ```

## Installation

In order to read and write Cloud Optimized Geotiffs (COG), GDAL version 3.1 or greater is required. If your system GDAL is older than version 3.1, consider using Docker or Conda to get a modern GDAL.

### Using pypi

To install the latest stable version from [_pypi_](https://pypi.org/), write this in the command-line:

```bash
> pip install geodataflow.dataframes[eodag,gee]
```

Optional extras:

* eodag

  EODAG - [Earth Observation Data Access Gateway](https://eodag.readthedocs.io/en/stable/) is a Python package for searching and downloading remotely sensed images while offering an unified API for data access regardless of the data provider.

  Installing this extra _EODAG_ adds access to more EO Products from different providers to `EOProductCatalog` and `EOProductDataset` modules.

* gee

  GEE - [Google Earth Engine API](https://developers.google.com/earth-engine) is a geospatial processing service. With _Earth Engine_, you can perform geospatial processing at scale, powered by Google Cloud Platform. _GEE_ requires authentication, please, read available documentation [here](https://developers.google.com/earth-engine/guides/python_install#authentication).

  Installing this extra _GEE_ makes possible the access to Google Cloud Platform to `GEEProductCatalog` and `GEEProductDataset` modules.

To view all available CLI tool commands and options:
```bash
> geodataflow --help
```

Listing all available modules:
```bash
> geodataflow --modules
```

Run a workflow in the command-line interface:
```bash
> geodataflow --pipeline_file "/geodataflow/dataframes/tests/data/test_eo_stac_catalog.json"
```

### Using docker

Building the container with:
```bash
> docker build -f ./Dockerfile.dataframes -t geodataflow/cli:1.0.0 .
```

Getting start:
```bash
> docker run --rm --name gdf geodataflow/cli:1.0.0 --help
> docker run --rm --name gdf geodataflow/cli:1.0.0 --modules
```

Creating an interactive bash shell:
```bash
> docker run --rm -it --entrypoint "bash" geodataflow/cli:1.0.0
```

To run workflows in Linux:
```bash
> docker run \
    --rm --name gdf -v "$PWD/geodataflow/dataframes/tests/data:/tests/data" geodataflow/cli:1.0.0 \
    --pipeline_file "/tests/data/test_eo_stac_catalog.json"
```

To run workflows in Windows:
```bash
> docker run ^
    --rm --name gdf -v "%cd%/geodataflow/dataframes/tests/data:/tests/data" geodataflow/cli:1.0.0 ^
    --pipeline_file "/tests/data/test_eo_stac_catalog.json"
```

## Contribute

Have you spotted a typo in our documentation? Have you observed a bug while running **GeodataFlow**? Do you have a suggestion for a new feature?

Don't hesitate and open an issue or submit a pull request, contributions are most welcome!

## License

**GeodataFlow** is licensed under Apache License v2.0.
See [LICENSE](LICENSE) file for details.

## Credits

**GeodataFlow** is built on top of amazingly useful open source projects. See [NOTICE](../../NOTICE) file for details about those projects
and their licenses.

Thank you to all the authors of these projects!
