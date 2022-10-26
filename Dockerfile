# =============================================================================
# This Dockerfile implements a Docker container to run GeodataFlow.
#
# @Build:
#  docker build -f ./Dockerfile -t geodataflow/pipelineapp:1.0.0 .
#  docker image rmi geodataflow/pipelineapp:1.0.0
#
# @Usage:
#  docker run --rm --name gdf geodataflow/pipelineapp:1.0.0 --help
#  docker run --rm --name gdf geodataflow/pipelineapp:1.0.0 --modules
# To run workflows in Linux:
#  docker run --rm --name gdf -v "$PWD/tests/data:/tests/data" geodataflow/pipelineapp:1.0.0 --pipeline_file "/tests/data/test_eo_stac_catalog.json" --pipeline.TEST_DATA_PATH "/tests/data" --pipeline.TEST_OUTPUT_PATH "/tests/data"
# To run workflows in Windows:
#  docker run --rm --name gdf -v "%cd%/tests/data:/tests/data" geodataflow/pipelineapp:1.0.0 --pipeline_file "/tests/data/test_eo_stac_catalog.json" --pipeline.TEST_DATA_PATH "/tests/data" --pipeline.TEST_OUTPUT_PATH "/tests/data"
# For interactive process:
#  docker run --rm -it --entrypoint "bash" geodataflow/pipelineapp:1.0.0
#
# =============================================================================

FROM osgeo/gdal:ubuntu-small-3.5.1
LABEL maintainer="Alvaro Huarte <ahuarte47@gmail.com>"

RUN echo "INFO: This Docker container provides the GeodataFlow app!"

RUN set -x && \
    apt-get update && \
    apt-get install -y python3-pip wget --no-install-recommends && \
    apt-get autoclean && \
    apt-get autoremove && \
    rm -rf /var/lib/{apt,dpkg,cache,log}

COPY ./geodataflow /app/geodataflow
COPY ./requirements.txt /app
WORKDIR /app

# Clean existing "__pycache__" directories.
RUN find . -name "__pycache__" -type d -prune -exec rm -rf '{}' +

# Install python dependencies.
RUN pip3 install --no-cache-dir --requirement requirements.txt

RUN echo "INFO: Everything installed!"
RUN echo "INFO: You can run Geospatial workflows type '--help'."

# Set entrypoint.
ENTRYPOINT ["python", "geodataflow/pipelineapp.py"]
