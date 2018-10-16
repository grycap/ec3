# Dockerfile to create a container with EC3 
FROM alpine:3.8
LABEL maintainer="Germán Moltó <gmolto@dsic.upv.es>"
LABEL version="2.0"
LABEL description="Elastic Cloud Computing Cluster (EC3) - http://www.grycap.upv.es/ec3"

RUN apk add --no-cache py-pip python && \
     pip --no-cache-dir install ec3-cli && \
     apk del py-pip

ENTRYPOINT ["/usr/bin/ec3"]
