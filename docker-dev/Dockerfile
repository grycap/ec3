# Dockerfile to create a container with EC3 
FROM alpine:3.12
LABEL maintainer="Germán Moltó <gmolto@dsic.upv.es>"
LABEL version="2.1"
LABEL description="Elastic Cloud Computing Cluster (EC3) - http://www.grycap.upv.es/ec3"

RUN apk add --no-cache py3-pip py3-requests python3 sshpass git openssh-client && \
     cd /tmp && git clone https://github.com/grycap/ec3/ --branch=devel && \
     pip --no-cache-dir install /tmp/ec3 && \
     apk del py3-pip git

ENTRYPOINT ["/usr/bin/ec3"]
