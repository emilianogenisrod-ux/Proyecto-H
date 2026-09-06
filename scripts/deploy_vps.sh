#!/bin/bash
set -euo pipefail

APP_DIR=/root/proyecto-h-app
STACK_NAME=proyecto-h
IMAGE=proyecto-h-api:latest
DOMAIN=proyecto-h.iagentek.com.mx
REPO=https://github.com/emilianogenisrod-ux/Proyecto-H.git

echo "==> Preparando directorio $APP_DIR"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch origin
  git -C "$APP_DIR" reset --hard origin/main
else
  rm -rf "$APP_DIR"
  git clone "$REPO" "$APP_DIR"
fi

cd "$APP_DIR"

echo "==> Extrayendo credenciales del VPS (sin imprimirlas)"
POSTGRES_PASSWORD=$(grep -m1 'POSTGRES_PASSWORD=' /root/supabase.yaml | sed 's/.*POSTGRES_PASSWORD=//' | tr -d '"' | tr -d "'" | tr -d ' ')
MINIO_ACCESS_KEY=$(grep -m1 'MINIO_ROOT_USER=' /root/minio.yaml | sed 's/.*MINIO_ROOT_USER=//' | tr -d '"' | tr -d "'" | tr -d ' ')
MINIO_SECRET_KEY=$(grep -m1 'MINIO_ROOT_PASSWORD=' /root/minio.yaml | sed 's/.*MINIO_ROOT_PASSWORD=//' | tr -d '"' | tr -d "'" | tr -d ' ')
SESSION_SECRET=$(openssl rand -hex 24)

if [ -z "$POSTGRES_PASSWORD" ] || [ -z "$MINIO_ACCESS_KEY" ] || [ -z "$MINIO_SECRET_KEY" ]; then
  echo "ERROR: no se pudieron leer credenciales"
  exit 1
fi

# Resolver hostname MinIO en la red swarm
MINIO_HOST=$(docker service inspect minio_minio --format '{{.Spec.Name}}' 2>/dev/null || echo minio_minio)

DATABASE_URL="postgresql+psycopg://postgres:${POSTGRES_PASSWORD}@supabase_db:5432/postgres"

echo "==> Generando stack yaml"
cat > /root/proyecto-h.yaml <<EOF
version: "3.8"

services:
  api:
    image: ${IMAGE}
    networks:
      - iagenteknet
      - supabase_internal
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SESSION_SECRET=${SESSION_SECRET}
      - APP_TITLE=Gestor de Citas Hospitalarias
      - MINIO_ENABLED=true
      - MINIO_ENDPOINT=http://${MINIO_HOST}:9000
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
      - MINIO_BUCKET=hospital
      - MINIO_SECURE=false
      - MINIO_PUBLIC_BASE_URL=https://iagentekminioback.iagentek.com.mx
      - SUPABASE_URL=https://iagenteksupabase.iagentek.com.mx
    volumes:
      - proyecto_h_media:/app/media
      - proyecto_h_data:/app/data
    deploy:
      replicas: 1
      restart_policy:
        condition: on-failure
      labels:
        - traefik.enable=true
        - traefik.docker.network=iagenteknet
        - traefik.http.routers.proyecto-h.entrypoints=websecure
        - traefik.http.routers.proyecto-h.rule=Host(\`${DOMAIN}\`)
        - traefik.http.routers.proyecto-h.service=proyecto-h
        - traefik.http.routers.proyecto-h.tls=true
        - traefik.http.routers.proyecto-h.tls.certresolver=letsencryptresolver
        - traefik.http.services.proyecto-h.loadbalancer.server.port=8000
        - traefik.http.routers.proyecto-h-http.entrypoints=web
        - traefik.http.routers.proyecto-h-http.rule=Host(\`${DOMAIN}\`)
        - traefik.http.routers.proyecto-h-http.middlewares=proyecto-h-redirect
        - traefik.http.middlewares.proyecto-h-redirect.redirectscheme.scheme=https
        - traefik.http.middlewares.proyecto-h-redirect.redirectscheme.permanent=true

networks:
  iagenteknet:
    external: true
  supabase_internal:
    external: true

volumes:
  proyecto_h_media:
  proyecto_h_data:
EOF

echo "==> Asegurar Dockerfile y requirements en repo"
if [ ! -f Dockerfile ]; then
  echo "ERROR: falta Dockerfile en el repo; se necesita push previo"
  ls -la
  exit 1
fi

echo "==> Build imagen ${IMAGE}"
docker build -t "${IMAGE}" .

echo "==> Crear bucket hospital en MinIO (si mc disponible)"
if command -v mc >/dev/null 2>&1; then
  mc alias set localminio http://127.0.0.1:9000 "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY" 2>/dev/null || true
  mc mb -p localminio/hospital 2>/dev/null || true
else
  # Intento vía contenedor temporal en la red del minio
  docker run --rm --network iagenteknet \
    -e MC_HOST_m="http://${MINIO_ACCESS_KEY}:${MINIO_SECRET_KEY}@${MINIO_HOST}:9000" \
    minio/mc mb -p m/hospital 2>/dev/null || \
  docker run --rm --network iagenteknet minio/mc \
    alias set m "http://${MINIO_HOST}:9000" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY" >/dev/null 2>&1 || true
  docker run --rm --network iagenteknet minio/mc mb -p m/hospital 2>/dev/null || echo "WARN: bucket hospital (se creará al primer upload)"
fi

echo "==> Deploy stack ${STACK_NAME}"
docker stack deploy -c /root/proyecto-h.yaml "${STACK_NAME}"

echo "==> Esperando servicio..."
for i in $(seq 1 30); do
  READY=$(docker service ls --filter name=${STACK_NAME}_api --format '{{.Replicas}}')
  echo "  replicas: $READY"
  echo "$READY" | grep -q '1/1' && break
  sleep 3
done

sleep 5
echo "==> HTTP check"
curl -sI -m 20 "https://${DOMAIN}/login" | head -15 || true
curl -sI -m 20 "http://${DOMAIN}/login" | head -10 || true

echo "==> Logs recientes"
docker service logs --tail 40 "${STACK_NAME}_api" 2>&1 | tail -50

echo "DONE"
