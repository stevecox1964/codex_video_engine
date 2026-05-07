@echo off
setlocal

pushd "%~dp0" >nul

if "%~1"=="" (
  echo Usage:
  echo   run_fal.bat --model fal-ai/flux/schnell --set prompt="a simple sunset over mountains" --set image_size="landscape_16_9"
  echo.
  echo Recipe example:
  echo   run_fal.bat --model fal-ai/flux/schnell --args Docs\MediaGeneration\recipes\text_to_image\brandbook_image.json
  echo.
  echo Note: generation calls may use fal credits.
  popd >nul
  exit /b 2
)

uv run python Python\scripts\media\fal_generate.py %*
set EXIT_CODE=%ERRORLEVEL%

popd >nul
exit /b %EXIT_CODE%
