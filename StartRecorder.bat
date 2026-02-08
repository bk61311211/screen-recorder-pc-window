@echo off
setlocal

:: Define installer path at the top so it's accessible for cleanup
set "TEMP_INSTALLER=%TEMP%\python_312_installer.exe"

echo Checking for Python...

set "PYTHON_EXE="

REM --- 1. CHECK DIRECT PATHS FIRST (Bypass ghost shortcuts) ---
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
)

if not defined PYTHON_EXE if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
)

REM --- 2. CHECK COMMANDS ---
if not defined PYTHON_EXE (
    py -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PYTHON_EXE=py"
)

if not defined PYTHON_EXE (
    python -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PYTHON_EXE=python"
)

REM --- 3. DECIDE: RUN OR INSTALL ---
if not defined PYTHON_EXE goto :install_python

echo Found working Python: %PYTHON_EXE%
goto :check_reqs

:install_python
echo No working Python found.
echo Downloading and installing Python 3.12.9 in the background...

REM Download if not exists or small
if exist "%TEMP_INSTALLER%" (
    for %%A in ("%TEMP_INSTALLER%") do if %%~zA LSS 20000000 del "%TEMP_INSTALLER%"
)

if not exist "%TEMP_INSTALLER%" (
    echo Downloading from python.org...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile '%TEMP_INSTALLER%'"
)

if not exist "%TEMP_INSTALLER%" (
    echo ERROR: Download failed.
    pause
    exit /b 1
)

echo Starting background installation...
start /wait "" "%TEMP_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

echo.
echo Verifying installation...
timeout /t 5 >nul

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    echo Installation successful!
    echo Restarting script...
    timeout /t 2 >nul
    start "" "%~f0"
    exit /b 0
)

echo ERROR: Installation finished but python.exe still couldn't be located.
pause
exit /b 1

:check_reqs
echo.
echo Using: %PYTHON_EXE%
echo Checking/Installing libraries...
"%PYTHON_EXE%" -m pip install --no-warn-script-location --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo ERROR: Library installation failed.
    pause
    exit /b 1
)

echo.
echo Starting recorder...
if exist "recorder.py" (
    "%PYTHON_EXE%" "recorder.py"
) else (
    echo ERROR: recorder.py not found.
)

echo.
echo --------------------------------------------------
echo Recording session ended.
set "CLEANUP=N"
set /p CLEANUP="Do you want to uninstall Python and cleanup? (Y/N) [Default: N]: "

if /i "%CLEANUP%"=="Y" (
    echo.
    echo Cleaning up libraries...
    "%PYTHON_EXE%" -m pip uninstall -y -r requirements.txt >nul 2>&1

    if exist "%TEMP_INSTALLER%" (
        echo Uninstalling Python in the background...
        start /wait "" "%TEMP_INSTALLER%" /quiet /uninstall
        del "%TEMP_INSTALLER%"
        echo Python has been uninstalled.
    ) else (
        echo Could not find the installer to perform uninstallation.
    )
    echo Cleanup complete.
) else (
    :: Even if not uninstalling Python, clean up the installer file to save space
    if exist "%TEMP_INSTALLER%" del "%TEMP_INSTALLER%"
)

echo.
pause
