@echo off
cd /d "%~dp0"
docker build -t nrb-v2-python:local -f environments/v2/Dockerfile .
set RESULT=%errorlevel%
if %RESULT% equ 0 echo Environment ready. Place solution.py in submissions/P01 ... P08, then run Grade-Results.
echo.
pause
exit /b %RESULT%
