@echo off
if /i "%1"=="code" (
    echo ==========================================
    echo    Dang khoi dong Face Attendance - Code...
    echo ==========================================
) else if /i "%1"=="project" (
    echo ==========================================
    echo    Dang khoi dong Face Attendance - Project...
    echo ==========================================
) else (
    echo ==========================================
    echo    Dang khoi dong Face Attendance...
    echo ==========================================
)
call venv\Scripts\activate.bat
echo Dang kiem tra va cap nhat database (migrate)...
python manage.py migrate
echo.
python manage.py runserver
