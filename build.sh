image=mereith/open-webui:v0.1.0

docker build -t $image .
docker push $image
