#!/bin/bash
set -e
echo "=== service ls ==="
docker service ls | grep proyecto-h || true
echo "=== service ps ==="
docker service ps proyecto-h_api --no-trunc 2>&1 | head -30
echo "=== inspect error ==="
docker service ps proyecto-h_api --format '{{.CurrentState}} | {{.Error}}' 2>&1 | head -20
echo "=== task logs ==="
docker service logs --tail 100 proyecto-h_api 2>&1 | tail -120
echo "=== images ==="
docker images | grep proyecto-h || true
echo "=== networks attachable? ==="
docker network inspect supabase_internal --format '{{.Attachable}} {{.Driver}} {{.Scope}}' 2>&1
docker network inspect iagenteknet --format '{{.Attachable}} {{.Driver}} {{.Scope}}' 2>&1
