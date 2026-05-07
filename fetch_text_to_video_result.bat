@echo off
setlocal

pushd "%~dp0" >nul

if "%~1"=="" (
  echo Usage:
  echo   fetch_text_to_video_result.bat REQUEST_ID
  echo.
  echo Example:
  echo   fetch_text_to_video_result.bat 019dfffa-2074-7c02-aad8-b717304dcbde
  popd >nul
  exit /b 2
)

uv run python Python\scripts\media\fetch_fal_result.py --model fal-ai/kandinsky5/text-to-video/distill --request-id %1 --out Docs\MediaGeneration\outputs\text_to_video
set EXIT_CODE=%ERRORLEVEL%

echo.
echo Finished with exit code %EXIT_CODE%.
pause

popd >nul
exit /b %EXIT_CODE%
