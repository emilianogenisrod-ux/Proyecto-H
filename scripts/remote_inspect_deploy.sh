#!/bin/bash
set -e
echo "=== /root/proyecto-H ==="
ls -la /root/proyecto-H 2>/dev/null | head -40 || true
echo "=== find stack yaml ==="
find /root /opt -maxdepth 3 -iname '*proyecto*' 2>/dev/null
echo "=== proyectoh services ==="
docker service ls | grep -i proyecto || true
echo "=== traefik rules proyectoh ==="
for svc in proyectoh_api proyectoh_frontend; do
  echo "-- $svc"
  docker service inspect "$svc" --format '{{range $k,$v := .Spec.Labels}}{{println $k $v}}{{end}}' 2>/dev/null | grep -iE 'rule|image|port' || true
done
echo "=== networks ==="
docker network ls | grep -E 'iagentek|supabase|internal' || true
echo "=== DNS ==="
getent hosts proyecto-h.iagentek.com.mx || true
dig +short proyecto-h.iagentek.com.mx A 2>/dev/null || host proyecto-h.iagentek.com.mx 2>/dev/null || true
echo "=== secret keys present (names only) ==="
grep -E '^([[:space:]]*-[[:space:]]*)?(POSTGRES_PASSWORD|MINIO_ROOT_USER|MINIO_ROOT_PASSWORD)=' /root/supabase.yaml /root/minio.yaml 2>/dev/null | sed 's/=.*/=***PRESENT***/'
