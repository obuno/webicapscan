#!/bin/bash

# Stop and remove any older webicapscan container if it exists
CONTAINER_NAME="webicapscan"
OLD="$(docker ps --all --quiet --filter=name="$CONTAINER_NAME")"
if [ -n "$OLD" ]; then
  docker container stop $OLD && docker container rm $OLD
fi

# build and start a new webicapscan container
docker image build -t webicapscan .

#modifications needed below are in [ ] (brackets which shall be removed post updates for your environment)
docker container create \
  --name webicapscan \
  -p [docker-host-ip]:5000:5000 \
  --dns [dns-server-ip] \
  -v [/path/to/the/clamav/databases]:/var/lib/clamav \
  -it webicapscan:latest

docker container start webicapscan
docker save webicapscan:latest | gzip > webicapscan_latest.tar.gz

