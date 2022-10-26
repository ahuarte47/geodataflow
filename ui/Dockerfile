# =============================================================================
# This Dockerfile implements a Docker container to GeodataFlow Workbench cli.
#
# @Build:
#  docker build -f ./ui/Dockerfile -t geodataflow/workbench:1.0.0 .
#  docker image rmi geodataflow/workbench:1.0.0
#
# @Usage:
#  docker run --rm -it -p 8090:9640 geodataflow/workbench:1.0.0 -> http://localhost:8090/
#
# =============================================================================

FROM nginx:alpine
LABEL maintainer="Alvaro Huarte <ahuarte47@gmail.com>"

RUN echo "INFO: Deploying GeodataFlow Workbench webapp!"

COPY ./ui/nginx.conf /etc/nginx/nginx.conf
COPY ./ui/css /usr/share/nginx/html/css
COPY ./ui/images /usr/share/nginx/html/images
COPY ./ui/gallery /usr/share/nginx/html/gallery
COPY ./ui/js /usr/share/nginx/html/js
COPY ./ui/workbench.html /usr/share/nginx/html
WORKDIR /usr/share/nginx/html

RUN echo "INFO: Everything done!"

# Set entrypoint.
EXPOSE 9640
CMD ["/bin/sh",  "-c",  "envsubst < /usr/share/nginx/html/js/env.template.js > /usr/share/nginx/html/js/env.js && exec nginx -g 'daemon off;'"]
