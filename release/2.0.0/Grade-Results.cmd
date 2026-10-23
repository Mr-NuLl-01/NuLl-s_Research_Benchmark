@echo off
cd /d "%~dp0"
if exist .nrb-env\Scripts\python.exe (
  .nrb-env\Scripts\python.exe run-grader.py %*
  goto finished
)
where py >nul 2>nul
if %errorlevel% equ 0 (py -3 run-grader.py %*) else (python run-grader.py %*)
:finished
set RESULT=%errorlevel%
echo.
pause
exit /b %RESULT%
