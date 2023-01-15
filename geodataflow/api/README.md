# geodataflow.api

GeodataFlow WebAPI component using [_FastAPI_](https://fastapi.tiangolo.com/) which provides access to GeodataFlow backend via API REST calls.

**GeodataFlow** is a Geoprocessing framework for fetching, translating and manipulating Geospatial data (*Raster*, *Vector*, *EO/STAC collections*) by using a *Pipeline* or sequence of operations on input data. It is very much like the [_GDAL_](https://gdal.org/) library which handles raster and vector data.

The project is split up into several namespace packages. `geodataflow.api` implements a WEB API endpoint conforming to [_OpenAPI_](https://www.openapis.org/) specification with methods to get metadata, query states and run workflows. This package includes the `geodataflow.core` subpackage.

![api](docs/api.png)

## Installation

`geodataflow.api` just provides the _FastAPI_ app, you need to install one of available backends in order to have a complete list of useful modules.

### Using pypi

To install the latest stable version from [_pypi_](https://pypi.org/), write this in the command-line:

```bash
> pip install geodataflow.api[spatial,dataframes,eodag,gee]
```

Optional backends:

* [spatial](../spatial/)

  Installs the `geodataflow.spatial` backend implementation for GeodataFlow using _GDAL/OGR_.

* [dataframes](../dataframes/)

  Installs the `geodataflow.dataframes` backend implementation for GeodataFlow using _Geopandas_.

Optional extras:

* eodag

  EODAG - [Earth Observation Data Access Gateway](https://eodag.readthedocs.io/en/stable/) is a Python package for searching and downloading remotely sensed images while offering an unified API for data access regardless of the data provider.

  Installing this extra _EODAG_ adds access to more EO Products from different providers to `EOProductCatalog` and `EOProductDataset` modules.

* gee

  GEE - [Google Earth Engine API](https://developers.google.com/earth-engine) is a geospatial processing service. With _Earth Engine_, you can perform geospatial processing at scale, powered by Google Cloud Platform. _GEE_ requires authentication, please, read available documentation [here](https://developers.google.com/earth-engine/guides/python_install#authentication).

  Installing this extra _GEE_ makes possible the access to Google Cloud Platform to `GEEProductCatalog` and `GEEProductDataset` modules.

### Using docker-compose

[docker-compose.yml](../../docker-compose.yml) builds images and starts  GeodataFlow API and Workbench components to easily run Workflows with **GeodataFlow**.

`PACKAGE_WITH_GEODATAFLOW_PIPELINE_CONTEXT` in the yml file indicates the backend implementation to load. The default value is `geodataflow.spatial`. If you prefer to use another backend, please, change it before starting.

Write in the command-line from the root folder of the project:
```bash
> docker-compose up
```

Then, type in your favorite Web Browser:
* http://localhost:9630/docs to check the interface of the REST WebAPI service.
* http://localhost:9640/workbench.html to access to the Workbench UI designer and where you can design and run Workflows!

To remove all resources:
```bash
> docker-compose down --rmi all -v --remove-orphans
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
