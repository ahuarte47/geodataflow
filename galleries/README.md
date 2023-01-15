# Gallery of Templates

This folder contains collections of templates to deploy in the GeodataFlow Workbench Gallery panel.

Each backend implementation for GeodataFlow should provide its own list of templates because each of them implements its own collection of modules (Readers, Filters & Writers).

## OSGeo/Geopandas

[Gallery](osgeo/gallery/) of templates shared by the [geodataflow.spatial](../geodataflow/spatial/) (GDAL/OGR - OSGeo) & [geodataflow.dataframes](../geodataflow/dataframes/) (GeoPandas) backend implementations.

### Templates:

* _Featurelayer transform_

  Title: Changing the Coordinate System of a Feature Layer.

  Descripton: This example takes Geometries from a Layer and transforms them between two Spatial Reference Systems (_EPSG:4326_ to _EPSG:25830_).

* _S2L2A STAC items_

  Title: Getting items from a STAC Catalog.

  Description: This example queries the [Sentinel-2 L2A COG STAC Catalog](https://registry.opendata.aws/sentinel-2-l2a-cogs) to fetch metadata of available Products.

  [STAC](https://stacspec.org) is a standardized way to expose collections of spatial temporal data. At its core, the SpatioTemporal Asset Catalog (STAC) specification provides a common structure for describing and cataloging spatiotemporal assets. A spatiotemporal asset is any file that represents information about the earth captured in a certain space and time.

* _S2L2A STAC dataset_

  Title: Getting raster from a STAC Catalog.

  Description: This example queries the [Sentinel-2 L2A COG STAC Catalog](https://registry.opendata.aws/sentinel-2-l2a-cogs) to extract a raster (_NDVI_ index) that intersects an Area.

* _Timeseries plot_

  Title: Plotting a _NDVI_ Time Series Graph of a polygon.

  Description: This example plots a graph of the _NDVI_ Time Series that intersects a Polygon. It queries a set of dates of the [Sentinel-2 L2A COG STAC Catalog](https://registry.opendata.aws/sentinel-2-l2a-cogs), cuts inputs rasters with the Area de Interest, calculates for each dataset its _NDVI_ index, then the workflow aggregates the "mean" of all pixels to finally export all rasters as _Geotiffs_, the TimeSeries plot as png and the Area of Interest as _GeoJson_.
