@echo off
setlocal

pushd "%~dp0" >nul

echo This will run a paid fal text-to-video smoke test.
echo.
echo Model: fal-ai/kandinsky5/text-to-video/distill
echo Mode: text-to-video
echo Count: 1
echo Aspect ratio: 16:9
echo Duration: 5 seconds
echo Recipe: Docs\MediaGeneration\recipes\text_to_video\kandinsky5_smoke_test.json
echo Output: Docs\MediaGeneration\outputs\text_to_video
echo Estimated cost/risk: fal currently lists this endpoint at about $0.05 for a 5-second video; pricing can change.
echo.
choice /C YN /M "Proceed"
if errorlevel 2 (
  echo Cancelled.
  popd >nul
  exit /b 0
)

call run_fal.bat --model fal-ai/kandinsky5/text-to-video/distill --args Docs\MediaGeneration\recipes\text_to_video\kandinsky5_smoke_test.json --out Docs\MediaGeneration\outputs\text_to_video
set EXIT_CODE=%ERRORLEVEL%

popd >nul
exit /b %EXIT_CODE%
