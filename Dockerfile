# Dockerfile to create a container with EC3 
FROM ubuntu:14.04
MAINTAINER Germán Moltó <gmolto@dsic.upv.es>
LABEL version="1.0"
LABEL description="Elastic Cloud Computing Cluster (EC3) - http://www.grycap.upv.es/ec3"
RUN apt-get update && apt-get install -y \
    git \
    python-ply \
    python-dev \
    python-yaml

ENV EC3_HOME /opt/ec3
RUN mkdir -p "$EC3_HOME"
WORKDIR $EC3_HOME
RUN git clone https://github.com/grycap/ec3.git $EC3_HOME
ENTRYPOINT ["/opt/ec3/ec3"]
