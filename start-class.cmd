@echo off
setlocal DisableDelayedExpansion
cd /d "%~dp0"
docker network inspect m5d1-events >nul 2>&1
if errorlevel 1 docker network create m5d1-events
if errorlevel 1 exit /b 1
docker compose -f compose-monitor.yaml up -d --build
if errorlevel 1 exit /b 1
docker compose -f compose-general.yaml up -d --build
if errorlevel 1 exit /b 1
docker compose -f compose-general.yaml exec -T general-api python collect_classroom.py
if errorlevel 1 exit /b 1
echo General: http://localhost:8081/login ^| class-student
echo Monitor: http://localhost:8082 ^| class-operator
echo Classroom password: classroom1234!
