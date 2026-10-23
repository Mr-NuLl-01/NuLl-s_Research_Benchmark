@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (py -3 run-grader.py %*) else (python run-grader.py %*)
set RESULT=%errorlevel%
echo.
pause
exit /b %RESULT%
