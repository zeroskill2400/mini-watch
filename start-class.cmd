@echo off
chcp 65001 >nul
setlocal DisableDelayedExpansion
cd /d "%~dp0"
docker compose up -d --build
if errorlevel 1 exit /b 1
echo General: http://localhost:8081/login ^| class-student
echo Monitor: http://localhost:8082 ^| class-operator
echo Classroom password: classroom1234!
