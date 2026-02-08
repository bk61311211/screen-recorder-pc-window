@echo off
setlocal enabledelayedexpansion

:: Define installer path and URL
set "TEMP_INSTALLER=%TEMP%\python_312_installer.exe"
set "INSTALLER_NAME=python_312_installer.exe"
set "PYTHON_URL=https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe"

echo Checking for Python...

set "PYTHON_EXE="

REM --- 1. CHECK DIRECT PATHS FIRST ---
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
echo Downloading Python 3.12.9...

REM Download if not exists or small
if exist "%TEMP_INSTALLER%" (
    for %%A in ("%TEMP_INSTALLER%") do if %%~zA LSS 20000000 del "%TEMP_INSTALLER%"
)

if not exist "%TEMP_INSTALLER%" (
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%TEMP_INSTALLER%'"
)

if not exist "%TEMP_INSTALLER%" (
    echo ERROR: Download failed.
    pause
    exit /b 1
)

echo.
echo|set /p="Installing Python in background... "
start "" "%TEMP_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

:wait_install
timeout /t 2 >nul
echo|set /p="."
tasklist /fi "ImageName eq %INSTALLER_NAME%" | find /i "%INSTALLER_NAME%" >nul
if not errorlevel 1 goto :wait_install

echo.
echo Verifying installation...
timeout /t 3 >nul

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

    REM If uninstaller is missing, download it.
    if not exist "%TEMP_INSTALLER%" (
        echo Downloading uninstaller...
        powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%TEMP_INSTALLER%'"
    )

    REM Verify installer exists before trying to use it.
    if not exist "%TEMP_INSTALLER%" (
        echo.
        echo ERROR: Could not find or download the uninstaller.
        echo You may need to uninstall Python manually from Windows Settings.
        goto :cleanup_done
    )

    echo|set /p="Uninstalling Python in background... "
    start "" "%TEMP_INSTALLER%" /quiet /uninstall

    :wait_uninstall
    timeout /t 2 >nul
    echo|set /p="."
    tasklist /fi "ImageName eq %INSTALLER_NAME%" | find /i "%INSTALLER_NAME%" >nul
    if not errorlevel 1 goto :wait_uninstall

    del "%TEMP_INSTALLER%"
    echo.
    echo Python has been removed.

    :cleanup_done
    echo Cleanup complete.
) else (
    if exist "%TEMP_INSTALLER%" del "%TEMP_INSTALLER%"
)

echo.
pause
