Release history
---------------

0.2.0 (2023-01-15)
++++++++++++++++++

- Splitting GeodataFlow into namespace packages

    * geodataflow.core
      The main subpackage of GeodataFlow which implements basic building blocks (Pipeline engine & Modules) and commonly used functionalities.

    * geodataflow.api
      WebAPI component using FastAPI which provides access to GeodataFlow backend via API REST calls.

    * workbench/ui
      GeodataFlow Workbench is a static javascript application for users easily draw and run their own Workflows in the Web Browser.

    Backends:

    * geodataflow/spatial
      Backend implementation for GeodataFlow using GDAL/OGR.

    * geodataflow/dataframes
      Backend implementation for GeodataFlow using Geopandas.

0.1.0 (2022-10-26)
++++++++++++++++++

- Starting to be stable for internal use
