# GeodataFlow Workbench

GeodataFlow **Workbench** is a _javascript_ application for users easily draw and run their own Workflows in the Web Browser.

**GeodataFlow** is a Geoprocessing framework for fetching, translating and manipulating Geospatial data (*Raster*, *Vector*, *EO/STAC collections*) by using a *Pipeline* or sequence of operations on input data. It is very much like the [_GDAL_](https://gdal.org/) library which handles raster and vector data.

GeodataFlow **Workbench** is an independent component written in javascript to invoke a GeodataFlow [WebAPI](../api/) service to get metadata, query states and run Workflows.

![workbench](docs/workbench.png)

## How to use

GeodataFlow **Workbench** is a static web application that you can run directly in the Web Browser.

Drop [workbench.html](workbench.html) in your Web Browser, You will be able to draw & configure Workflows even with none WebAPI service started. By default, the application is loading a fake WebAPI with several modules included and ready to check the interface.

If you want to configure the **Workbench** application to use a running WebAPI instance, you will need to change the setting where that URL is defined. Please, check the file [env.js](js/env.js) and the template [env.template.js](js/env.template.js) used by [docker-compose.yml](../../docker-compose.yml) to deploy everything using environment variables.

The most easy way is just to load the [docker-compose.yml](../../docker-compose.yml) to run GeodataFlow WebAPI and Workbench components. Please, read related section in the root [README](../../README.md).

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

