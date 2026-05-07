@echo off
setlocal

pushd "%~dp0" >nul

echo Starting FAL Video Studio at http://127.0.0.1:8765
echo.

uv run uvicorn Python.scripts.studio.server:app --host 127.0.0.1 --port 8765 --reload
set EXIT_CODE=%ERRORLEVEL%

popd >nul
exit /b %EXIT_CODE%
