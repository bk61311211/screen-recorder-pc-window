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

:: --- 2. DOWNLOAD AND INSTALL PYTHON IF NOT FOUND ---
echo Python not found.

:: Check if the installer exists and is a "full file" (roughly > 20MB)
set "RE_DOWNLOAD=0"
if exist "%TEMP_INSTALLER%" (
    for %%A in ("%TEMP_INSTALLER%") do set "FILESIZE=%%~zA"
    if !FILESIZE! LSS 20000000 (
        echo Existing installer seems too small (!FILESIZE! bytes). Will re-download.
        set "RE_DOWNLOAD=1"
    ) else (
        echo Python installer found in Temp.
    )
) else (
    set "RE_DOWNLOAD=1"
)

if "!RE_DOWNLOAD!"=="1" (
    echo Downloading Python 3.12.9...
    if exist "%TEMP_INSTALLER%" del "%TEMP_INSTALLER%"
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile '%TEMP_INSTALLER%'"
)

echo Installing Python for current user... (Please wait)
:: Use /passive instead of /quiet to see progress bar without needing input
start /wait "" "%TEMP_INSTALLER%" /passive InstallAllUsers=0 PrependPath=1 Include_test=0

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
echo Error: Python installation failed.
echo I will delete the installer so it downloads fresh next time.
if exist "%TEMP_INSTALLER%" del "%TEMP_INSTALLER%"
pause
exit

:check_reqs
:: --- 3. CHECK AND INSTALL REQUIREMENTS ---
echo.
echo Using Python: !PYTHON_EXE!
echo Checking libraries (mss, opencv, etc.)...
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
    start /wait "" "%TEMP_INSTALLER%" /passive /uninstall
    if exist "%TEMP_INSTALLER%" del "%TEMP_INSTALLER%"
    echo Cleanup complete.
    pause
    exit
)

if exist "%TEMP_INSTALLER%" del "%TEMP_INSTALLER%"
pause
