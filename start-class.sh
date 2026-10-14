#!/bin/sh
set -eu
cd "$(dirname "$0")"
docker compose up -d --build
printf '%s\n' 'General: http://localhost:8081/login | class-student' 'Monitor: http://localhost:8082 | class-operator' 'Classroom password: classroom1234!'
