@echo off
chcp 65001 >nul
color 0B
echo.
echo   =========================================================
echo          ___   ___    _   _   ___    _     ___   ___ 
echo         ^| __^| ^|   \  ^| ^| ^| ^| ^| __^|  /_\   / __^| ^| __^|
echo         ^| _^|  ^| ^|^) ^| ^| ^|_^| ^| ^| _^|  / _ \ ^| ^(__  ^| _^| 
echo         ^|___^| ^|___/   \___/  ^|_^|  /_/ \_\ \___^| ^|___^|
echo   =========================================================
echo                        Hoang Dep Trai
echo   =========================================================
echo.
if /i "%1"=="code" (
    echo   [+] Che do: Developer ^(Code^)
    goto :continue
)
if /i "%1"=="project" (
    echo   [+] Che do: Developer ^(Project^)
    goto :continue
)
echo   [+] Che do: Mac Dinh

:continue
echo.
echo   [1/4] Kich hoat moi truong ao (venv)...
call venv\Scripts\activate.bat

echo   [2/4] Kiem tra Database (Migrate)...
python manage.py migrate

echo   [3/4] Mo trinh duyet web...
start /b powershell -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:8000'"

echo   [4/4] Khoi dong Server...
echo   ====================================================
echo.
color 0A
python manage.py runserver
