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

:: Search common installation folders for Python 3.12
for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python312*") do (
    if exist "%%d\python.exe" (
        set "PYTHON_EXE=%%d\python.exe"
        goto :check_reqs
    )
)

for /d %%d in ("%ProgramFiles%\Python312*") do (
    if exist "%%d\python.exe" (
        set "PYTHON_EXE=%%d\python.exe"
        goto :check_reqs
    )
)

:: --- 2. DOWNLOAD AND INSTALL PYTHON IF NOT FOUND ---
echo Python not found.

if exist "%TEMP_INSTALLER%" (
    echo Python installer already found in Temp. Skipping download.
) else (
    echo Downloading Python 3.12.9...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile '%TEMP_INSTALLER%'"
)

echo Installing Python for current user... (Please wait)
:: InstallAllUsers=0: Installs to AppData (No Admin needed)
:: PrependPath=1: Adds to user PATH
start /wait "" "%TEMP_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

:: Re-check after installation
timeout /t 5 >nul
for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python312*") do (
    if exist "%%d\python.exe" (
        echo Python installed successfully.
        echo Restarting script to refresh settings...
        timeout /t 2 >nul
        start "" "%~f0"
        exit
    )
)

echo.
echo Error: Python installation failed or could not be found.
echo Try running this script as Administrator if it continues to fail.
pause
exit

:check_reqs
:: --- 3. CHECK AND INSTALL REQUIREMENTS ---
echo.
echo Using Python: !PYTHON_EXE!
echo Checking libraries (mss, opencv, etc.)...
if not exist "requirements.txt" (
    echo Error: requirements.txt not found.
    pause
    exit
)

"!PYTHON_EXE!" -m pip install -r requirements.txt

:: --- 4. RUN THE RECORDER ---
echo Starting recorder...
if exist "recorder.py" (
    "!PYTHON_EXE!" "recorder.py"
) else (
    echo Error: recorder.py not found.
)

:: --- 5. CLEANUP PROMPT ---
echo.
echo --------------------------------------------------
set /p CLEANUP="Recording finished. Uninstall Python and libraries? (Y/N): "

if /i "%CLEANUP%"=="Y" (
    echo Cleaning up...
    "!PYTHON_EXE!" -m pip uninstall -y -r requirements.txt

    if not exist "%TEMP_INSTALLER%" (
        powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile '%TEMP_INSTALLER%'"
    )

    echo Uninstalling Python...
    start /wait "" "%TEMP_INSTALLER%" /quiet /uninstall
    if exist "%TEMP_INSTALLER%" del "%TEMP_INSTALLER%"
    echo Cleanup complete.
    pause
    exit
)

if exist "%TEMP_INSTALLER%" del "%TEMP_INSTALLER%"
pause
