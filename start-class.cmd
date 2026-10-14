@echo off
chcp 65001 >nul
setlocal DisableDelayedExpansion
cd /d "%~dp0"
docker info >nul 2>&1
if errorlevel 1 exit /b 1
docker network inspect m5d4-events >nul 2>&1
if errorlevel 1 docker network create m5d4-events
if errorlevel 1 exit /b 1
docker volume inspect m5d4-classroom-logs >nul 2>&1
if errorlevel 1 docker volume create m5d4-classroom-logs
if errorlevel 1 exit /b 1
docker compose -f compose-monitor.yaml up -d --build --wait --wait-timeout 180
if errorlevel 1 exit /b 1
docker compose -f compose-general.yaml up -d --build --wait --wait-timeout 180
if errorlevel 1 exit /b 1
echo General: http://localhost:8083/login ^| class-student
echo Monitor: http://localhost:8084 ^| class-operator
echo Classroom password: classroom1234!
