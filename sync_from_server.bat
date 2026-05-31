@echo off
echo ========================================
echo   Sync DB from server to localhost
echo ========================================
echo.

echo [1/5] Creating dump on server...
ssh root@194.67.92.11 "cd /root/kameks && docker compose exec db pg_dump -U kameks_user --encoding=UTF8 kameks_db > backup.sql"
if %errorlevel% neq 0 (
    echo ERROR: cannot connect to server
    pause
    exit /b 1
)

echo [2/5] Downloading dump...
scp root@194.67.92.11:/root/kameks/backup.sql C:\Projects\kameks\backup.sql
if %errorlevel% neq 0 (
    echo ERROR: cannot download dump
    pause
    exit /b 1
)

echo [3/5] Resetting local DB...
docker compose -f C:\Projects\kameks\docker-compose.yml exec db psql -U kameks_user -d postgres -c "DROP DATABASE IF EXISTS kameks_db;"
docker compose -f C:\Projects\kameks\docker-compose.yml exec db psql -U kameks_user -d postgres -c "CREATE DATABASE kameks_db WITH ENCODING='UTF8';"

echo [4/5] Restoring data...
docker compose -f C:\Projects\kameks\docker-compose.yml cp C:\Projects\kameks\backup.sql db:/tmp/backup.sql
docker compose -f C:\Projects\kameks\docker-compose.yml exec db psql -U kameks_user -d kameks_db -f /tmp/backup.sql

echo [5/5] Restarting Docker...
docker compose -f C:\Projects\kameks\docker-compose.yml up --build -d

echo.
echo ========================================
echo   Done! Open http://localhost
echo ========================================
pause
