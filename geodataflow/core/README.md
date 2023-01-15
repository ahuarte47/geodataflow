# geodataflow.core

The main subpackage of **GeodataFlow** which implements basic building blocks (Pipeline engine & Modules) and commonly used functionalities.

**GeodataFlow** is a Geoprocessing framework for fetching, translating and manipulating Geospatial data (*Raster*, *Vector*, *EO/STAC collections*) by using a *Pipeline* or sequence of operations on input data. It is very much like the [_GDAL_](https://gdal.org/) library which handles raster and vector data.

The project is split up into several namespace packages. `geodataflow.core` implements core functionalities: the Pipeline engine and a CLI tool to run workflows.

### Workflow examples

Assuming you are using `geodataflow.spatial` (GDAL/OGR) as active backend implementation, **GeodataFlow** can run workflows as the following:

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

`geodataflow.core` just provides basic built-in modules, you need to install one of available backends in order to have a complete list of useful modules.

### Using pypi

To install the latest stable version from [_pypi_](https://pypi.org/), write this in the command-line:

```bash
> pip install geodataflow.core
```

To view all available CLI tool commands and options:
```bash
> geodataflow --help
```

Listing all available modules:
```bash
> geodataflow --modules
```

### Using docker

Building the container with:
```bash
> docker build -f ./Dockerfile.core -t geodataflow/cli:1.0.0 .
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
