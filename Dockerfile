FROM docker.io/debian:bullseye

LABEL name="pyhg612-exporter"
LABEL url="https://gitub.com/thomasdstewart/pyhg612-exporter"
LABEL maintainer="thomas@stewarts.org.uk"

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends install python3 python3-prometheus-client

COPY /pyhg612-exporter.py /usr/local/bin
CMD ["/usr/local/bin/pyhg612-exporter.py"]