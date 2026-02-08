@echo off
set "PYTHON_EXE=C:\Users\New User\AppData\Local\Programs\Python\Python312\python.exe"
set "SCRIPT_PATH=%~dp0recorder.py"

echo Starting Active Window Recorder...
"%PYTHON_EXE%" "%SCRIPT_PATH%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] The recorder stopped unexpectedly.
) else (
    echo.
    echo Recording finished successfully.
)

pause
