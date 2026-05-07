@echo off
setlocal

pushd "%~dp0" >nul

uv run python -c "from dotenv import load_dotenv; import os, requests, sys; load_dotenv('.env', override=False); key=os.environ.get('FAL_KEY'); assert key, 'FAL_KEY is missing or empty'; r=requests.get('https://api.fal.ai/v1/models?limit=1', headers={'Authorization':'Key '+key}, timeout=20); print('FAL_KEY auth test: OK' if r.ok else 'FAL_KEY auth test: FAILED ' + str(r.status_code)); sys.exit(0 if r.ok else 1)"
set EXIT_CODE=%ERRORLEVEL%

popd >nul
exit /b %EXIT_CODE%
