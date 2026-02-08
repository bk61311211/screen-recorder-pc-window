@echo off
setlocal enabledelayedexpansion

:: Define the temp installer path
set "TEMP_INSTALLER=%TEMP%\python_312_installer.exe"

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
echo Python not found.

:: Check if the installer is already in Temp
if exist "%TEMP_INSTALLER%" (
    echo Python installer already found in Temp. Skipping download.
) else (
    echo Downloading Python 3.12.9 to Temp...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile '%TEMP_INSTALLER%'"
)

echo Installing Python... (This will take a minute)
:: /quiet: no UI, PrependPath=1: Add to PATH
start /wait "" "%TEMP_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

:: Check if installation was successful by trying to find python.exe again
if not exist "!APP_DATA_PYTHON!" (
    :: Some installations go to AllUsers path
    set "ALL_USERS_PYTHON=%ProgramFiles%\Python312\python.exe"
    if not exist "!ALL_USERS_PYTHON!" (
        echo.
        echo Error: Python installation failed or path not recognized.
        pause
        exit
    )
)

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
    echo Searching for Python installer in Temp to perform uninstall...
    if not exist "%TEMP_INSTALLER%" (
        echo Downloading installer for uninstallation...
        powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile '%TEMP_INSTALLER%'"
    )

    echo Uninstalling Python... (Please wait)
    start /wait "" "%TEMP_INSTALLER%" /quiet /uninstall

    if exist "%TEMP_INSTALLER%" del "%TEMP_INSTALLER%"

    echo.
    echo Cleanup complete. Python and libraries have been removed.
    pause
    exit
)

:: Even if we don't uninstall, let's clean up the temp installer file
if exist "%TEMP_INSTALLER%" del "%TEMP_INSTALLER%"

echo.
echo Keeping Python and libraries.
pause
