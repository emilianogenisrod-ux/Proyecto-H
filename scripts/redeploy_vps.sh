#!/bin/bash
set -euo pipefail
APP_DIR=/root/proyecto-h-app
IMAGE=proyecto-h-api:latest
STACK=proyecto-h

git -C "$APP_DIR" fetch origin
git -C "$APP_DIR" reset --hard origin/main
cd "$APP_DIR"
docker build -t "$IMAGE" .
docker service update --force --image "$IMAGE" "${STACK}_api"

for i in $(seq 1 20); do
  R=$(docker service ls --filter name=${STACK}_api --format '{{.Replicas}}')
  echo "replicas=$R"
  echo "$R" | grep -q '1/1' && break
  sleep 3
done

curl -s -o /dev/null -w 'login:%{http_code}\n' https://proyecto-h.iagentek.com.mx/login
curl -s https://proyecto-h.iagentek.com.mx/login | grep -E 'emilio@farma|ejemplo@correo|placeholder' | head -10
curl -s -o /dev/null -w 'master:%{http_code}\n' https://proyecto-h.iagentek.com.mx/static/css/master.css
echo DONE
