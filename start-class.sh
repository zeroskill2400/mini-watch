#!/bin/sh
set -eu
cd "$(dirname "$0")"
docker network inspect m5d1-events >/dev/null 2>&1 || docker network create m5d1-events
docker compose -f compose-monitor.yaml up -d --build
docker compose -f compose-general.yaml up -d --build
docker compose -f compose-general.yaml exec -T general-api python collect_classroom.py
printf '%s\n' 'General: http://localhost:8081/login | class-student' 'Monitor: http://localhost:8082 | class-operator' 'Classroom password: classroom1234!'
