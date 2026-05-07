@echo off
setlocal

pushd "%~dp0" >nul

echo Running paid fal text-to-video smoke test.
echo Model: fal-ai/kandinsky5/text-to-video/distill
echo Output: Docs\MediaGeneration\outputs\text_to_video
echo.

call run_fal.bat --model fal-ai/kandinsky5/text-to-video/distill --args Docs\MediaGeneration\recipes\text_to_video\kandinsky5_smoke_test.json --out Docs\MediaGeneration\outputs\text_to_video
set EXIT_CODE=%ERRORLEVEL%

echo.
echo Finished with exit code %EXIT_CODE%.

popd >nul
exit /b %EXIT_CODE%
