#!/bin/sh
set -eu
cd "$(dirname "$0")"
docker info >/dev/null
docker network inspect m5d4-events >/dev/null 2>&1 || docker network create m5d4-events
docker volume inspect m5d4-classroom-logs >/dev/null 2>&1 || docker volume create m5d4-classroom-logs
docker compose -f compose-monitor.yaml up -d --build --wait --wait-timeout 180
docker compose -f compose-general.yaml up -d --build --wait --wait-timeout 180
printf '%s\n' 'General: http://localhost:8083/login | class-student' 'Monitor: http://localhost:8084 | class-operator' 'Classroom password: classroom1234!'
