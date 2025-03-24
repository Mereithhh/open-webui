#!/bin/bash
set -e

image=mereith/open-webui:v0.1.4

docker build -t $image .
docker push $image
