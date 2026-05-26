@echo off
title He Thong Backup Database - EduFace
color 0A


echo   Backup Database
echo ==================================================

:: 1. Thong so Database
set DB_NAME=face_attendance
set DB_USER=root
set DB_PASSWORD=
set DB_HOST=127.0.0.1
set DB_PORT=3306

:: 2. Tao thu muc backups (neu chua co) nam cung cap voi thu muc scripts
set BACKUP_DIR=..\backups
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

:: 3. Lay thoi gian hien tai de dat ten file (Tranh trung lap)
set THOIGIAN=%DATE:/=-%_%TIME::=-%
set THOIGIAN=%THOIGIAN: =0%
set THOIGIAN=%THOIGIAN:,=-%
set THOIGIAN=%THOIGIAN:.=-%

set BACKUP_FILE=%BACKUP_DIR%\%DB_NAME%_backup_%THOIGIAN%.sql

:: 4. Thuc thi lenh mysqldump
echo.
echo [*] Dang tao ban sao luu cho database: %DB_NAME%...

:: chinh lai duong dan den file mysqldump.exe theo cai dat tren may
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe" -h %DB_HOST% -P %DB_PORT% -u %DB_USER% %DB_NAME% > "%BACKUP_FILE%"

echo.
echo [V] HOAN THANH!
echo File backup da duoc luu tai: %BACKUP_FILE%
echo ==================================================
pause