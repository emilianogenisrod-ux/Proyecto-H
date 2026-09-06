#!/bin/bash
set -euo pipefail

DOMAIN=proyecto-h.iagentek.com.mx
IMAGE=proyecto-h-api:latest
STACK_NAME=proyecto-h
MINIO_HOST=minio

# Extraer password: toma el valor tras = de la primera línea útil
POSTGRES_PASSWORD=$(grep -E 'POSTGRES_PASSWORD=' /root/supabase.yaml | head -1 | sed -E 's/.*POSTGRES_PASSWORD=//' | tr -d '\"'\''\r ' )
MINIO_ACCESS_KEY=$(grep -E 'MINIO_ROOT_USER=' /root/minio.yaml | head -1 | sed -E 's/.*MINIO_ROOT_USER=//' | tr -d '\"'\''\r ' )
MINIO_SECRET_KEY=$(grep -E 'MINIO_ROOT_PASSWORD=' /root/minio.yaml | head -1 | sed -E 's/.*MINIO_ROOT_PASSWORD=//' | tr -d '\"'\''\r ' )
SESSION_SECRET=$(openssl rand -hex 24)

echo "cred_lens pg=${#POSTGRES_PASSWORD} ak=${#MINIO_ACCESS_KEY} sk=${#MINIO_SECRET_KEY}"

POSTGRES_PASSWORD_ENC=$(PGPASS="$POSTGRES_PASSWORD" python3 -c 'import os,urllib.parse; print(urllib.parse.quote(os.environ["PGPASS"], safe=""))')
DATABASE_URL="postgresql+psycopg://postgres:${POSTGRES_PASSWORD_ENC}@supabase_db:5432/postgres"

export DOMAIN IMAGE DATABASE_URL SESSION_SECRET MINIO_HOST MINIO_ACCESS_KEY MINIO_SECRET_KEY

python3 - <<'PY'
import os
from pathlib import Path

try:
    import yaml
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "-q", "pyyaml"])
    import yaml

data = {
    "version": "3.8",
    "services": {
        "api": {
            "image": os.environ["IMAGE"],
            "networks": ["iagenteknet", "supabase_internal"],
            "environment": {
                "DATABASE_URL": os.environ["DATABASE_URL"],
                "SESSION_SECRET": os.environ["SESSION_SECRET"],
                "APP_TITLE": "Gestor de Citas Hospitalarias",
                "MINIO_ENABLED": "true",
                "MINIO_ENDPOINT": f"http://{os.environ['MINIO_HOST']}:9000",
                "MINIO_ACCESS_KEY": os.environ["MINIO_ACCESS_KEY"],
                "MINIO_SECRET_KEY": os.environ["MINIO_SECRET_KEY"],
                "MINIO_BUCKET": "hospital",
                "MINIO_SECURE": "false",
                "MINIO_PUBLIC_BASE_URL": "https://iagentekminioback.iagentek.com.mx",
                "SUPABASE_URL": "https://iagenteksupabase.iagentek.com.mx",
            },
            "volumes": ["proyecto_h_media:/app/media", "proyecto_h_data:/app/data"],
            "deploy": {
                "replicas": 1,
                "restart_policy": {"condition": "on-failure"},
                "labels": [
                    "traefik.enable=true",
                    "traefik.docker.network=iagenteknet",
                    "traefik.http.routers.proyecto-h.entrypoints=websecure",
                    f"traefik.http.routers.proyecto-h.rule=Host(`{os.environ['DOMAIN']}`)",
                    "traefik.http.routers.proyecto-h.service=proyecto-h",
                    "traefik.http.routers.proyecto-h.tls=true",
                    "traefik.http.routers.proyecto-h.tls.certresolver=letsencryptresolver",
                    "traefik.http.services.proyecto-h.loadbalancer.server.port=8000",
                    "traefik.http.routers.proyecto-h-http.entrypoints=web",
                    f"traefik.http.routers.proyecto-h-http.rule=Host(`{os.environ['DOMAIN']}`)",
                    "traefik.http.routers.proyecto-h-http.middlewares=proyecto-h-redirect",
                    "traefik.http.middlewares.proyecto-h-redirect.redirectscheme.scheme=https",
                    "traefik.http.middlewares.proyecto-h-redirect.redirectscheme.permanent=true",
                ],
            },
        }
    },
    "networks": {
        "iagenteknet": {"external": True},
        "supabase_internal": {"external": True},
    },
    "volumes": {
        "proyecto_h_media": {},
        "proyecto_h_data": {},
    },
}

# Validar forma de la URL (sin secretos)
url = os.environ["DATABASE_URL"]
assert url.startswith("postgresql+psycopg://"), url[:30]
assert "@supabase_db:5432/postgres" in url
print("url_shape_ok")

Path("/root/proyecto-h.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
print("yaml written")
PY

docker stack deploy -c /root/proyecto-h.yaml "$STACK_NAME"

for i in $(seq 1 25); do
  READY=$(docker service ls --filter name=${STACK_NAME}_api --format '{{.Replicas}}' || true)
  echo "replicas=$READY"
  if echo "$READY" | grep -q '1/1'; then
    break
  fi
  # mostrar error reciente
  docker service ps ${STACK_NAME}_api --format '{{.CurrentState}} {{.Error}}' | head -3
  sleep 4
done

sleep 6
echo "==> HTTPS"
curl -sI -m 25 "https://${DOMAIN}/login" | head -20 || true
echo "==> logs"
docker service logs --tail 50 ${STACK_NAME}_api 2>&1 | tail -60
