# =============================================================================
# This Dockerfile implements a Docker container to run GeodataFlow as WEB API.
#
# @Build:
#  docker build -f ./api/Dockerfile -t geodataflow/pipelineapi:1.0.0 .
#  docker image rmi geodataflow/pipelineapi:1.0.0
#
# @Usage:
# To start in Linux:
#  docker run --rm -it -p 9630:9630 -v "$PWD/tests/data:/tests/data" geodataflow/pipelineapi:1.0.0
# To start in Windows:
#  docker run --rm -it -p 9630:9630 -v "%cd%/tests/data:/tests/data" geodataflow/pipelineapi:1.0.0
#
# =============================================================================

FROM osgeo/gdal:ubuntu-small-3.5.1
LABEL maintainer="Alvaro Huarte <ahuarte47@gmail.com>"

RUN echo "INFO: This Docker container provides the GeodataFlow API!"

RUN set -x && \
    apt-get update && \
    apt-get install -y python3-pip wget --no-install-recommends && \
    apt-get autoclean && \
    apt-get autoremove && \
    rm -rf /var/lib/{apt,dpkg,cache,log}

COPY ./geodataflow /app/geodataflow
COPY ./api/__meta__.py /app
COPY ./api/models.py /app
COPY ./api/schema.py /app
COPY ./api/database.py /app
COPY ./api/pipelineapi.py /app
COPY ./api/pipelineapi.default.settings /app
COPY ./requirements.txt /app
WORKDIR /app

# Clean existing "__pycache__" directories.
RUN find . -name "__pycache__" -type d -prune -exec rm -rf '{}' +

# Install python dependencies.
RUN pip3 install --no-cache-dir --requirement requirements.txt
RUN pip3 install --no-cache-dir pydantic
RUN pip3 install --no-cache-dir SQLAlchemy
RUN pip3 install --no-cache-dir aiosqlite
RUN pip3 install --no-cache-dir fastapi
RUN pip3 install --no-cache-dir uvicorn

RUN echo "INFO: Everything installed!"
RUN echo "INFO: You can run Geospatial workflows as a Service."

# Set entrypoint.
EXPOSE 9630
ENTRYPOINT ["uvicorn", "--port=9630", "pipelineapi:app"]
