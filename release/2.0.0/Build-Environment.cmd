@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (py -3 -m venv .nrb-env) else (python -m venv .nrb-env)
if errorlevel 1 goto failed
.nrb-env\Scripts\python.exe -m pip install -r requirements-evaluator.txt
if errorlevel 1 goto failed
docker build --platform=linux/amd64 -t nrb-v2:local -f environments/v2/Dockerfile .
if errorlevel 1 goto failed
docker build --platform=linux/amd64 -t nrb-v2-lean:local -f environments/v2/LeanDockerfile .
if errorlevel 1 goto failed
echo Environment ready. Place each task file in its submissions directory, then run Grade-Results.
echo.
pause
exit /b 0
:failed
echo Environment setup did not finish. Read the error above and try again.
pause
exit /b 1
