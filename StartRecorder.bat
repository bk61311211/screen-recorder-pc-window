@echo off
setlocal enabledelayedexpansion

:: --- 1. CHECK IF PYTHON IS INSTALLED ---
echo Checking for Python...

:: Try to find python in PATH first
python --version >nul 2>&1
if %errorlevel% == 0 (
    set "PYTHON_EXE=python"
    goto :check_reqs
)

:: Try the Python Launcher (py)
py --version >nul 2>&1
if %errorlevel% == 0 (
    set "PYTHON_EXE=py"
    goto :check_reqs
)

:: Try common install paths
set "APP_DATA_PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if exist "!APP_DATA_PYTHON!" (
    set "PYTHON_EXE=!APP_DATA_PYTHON!"
    goto :check_reqs
)

:: --- 2. DOWNLOAD AND INSTALL PYTHON IF NOT FOUND ---
echo Python not found. Downloading Python 3.12.9...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile 'python_installer.exe'"

echo Installing Python... (This will take a minute)
:: /quiet: no UI, PrependPath=1: Add to PATH
start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
:: Keep the installer for possible uninstall later
:: del python_installer.exe

echo.
echo Python has been installed successfully.
echo Restarting script in a new window to refresh settings...
timeout /t 3
start "" "%~f0"
exit

:check_reqs
:: --- 3. CHECK AND INSTALL REQUIREMENTS ---
echo.
echo Checking for required libraries (mss, opencv, etc.)...
if not exist "requirements.txt" (
    echo Error: requirements.txt not found in this folder.
    pause
    exit
)

"!PYTHON_EXE!" -m pip install -r requirements.txt

:: --- 4. RUN THE RECORDER ---
echo.
echo Everything is ready. Starting the recorder...
if exist "recorder.py" (
    "!PYTHON_EXE!" "recorder.py"
) else (
    echo Error: recorder.py not found in this folder.
)

:: --- 5. CLEANUP PROMPT ---
echo.
echo --------------------------------------------------
set /p CLEANUP="Recording finished. Do you want to uninstall Python and clean up all libraries? (Y/N): "

if /i "%CLEANUP%"=="Y" (
    echo.
    echo Cleaning up...

    echo Uninstalling Python libraries...
    "!PYTHON_EXE!" -m pip uninstall -y -r requirements.txt

    echo.
    echo Searching for Python installer to perform uninstall...
    if not exist "python_installer.exe" (
        echo Downloading installer for uninstallation...
        powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile 'python_installer.exe'"
    )

    echo Uninstalling Python... (Please wait)
    start /wait python_installer.exe /quiet /uninstall

    if exist "python_installer.exe" del "python_installer.exe"

    echo.
    echo Cleanup complete. Python and libraries have been removed.
    pause
    exit
)

echo.
echo Keeping Python and libraries.
pause
