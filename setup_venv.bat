@echo off
REM ---------------------------------------------------------------------------
REM Build the project-local virtual environment on this Windows machine.
REM
REM A virtual environment is a private copy of Python and its packages. Keeping
REM it inside the solution folder keeps these packages away from anything you
REM install later for instrument control. It also gives IT one folder to check.
REM
REM This script does NOT reach the internet. Point it at a folder of wheel
REM files that IT gave you. A wheel is a pre-built package file that ends in
REM .whl. Put them all in one folder and pass that folder as the first argument.
REM
REM Usage:
REM   setup_venv.bat C:\path\to\wheel_folder
REM
REM If you leave the folder out, pip will try the default index, which needs
REM internet. On an offline machine, always pass the wheel folder.
REM ---------------------------------------------------------------------------

setlocal

REM Work from the folder this script lives in, whatever folder it was called
REM from. Without this, double-clicking it from Explorer or running it from
REM C:\ creates the environment somewhere unexpected and then fails to find
REM requirements.txt.
cd /d "%~dp0"

set WHEEL_DIR=%1

REM Check the Python version before doing anything. numpy 1.26.4 and pandas
REM 2.2.2 have no wheels for 3.13 or newer, so on a newer Python the venv is
REM created happily and the install then fails with a resolver message that
REM says nothing about the real cause. Better to say it here.
python -c "import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,12) else 1)" 2>nul
if errorlevel 1 (
  echo.
  echo This project needs Python 3.11 or 3.12.
  python --version
  echo.
  echo The pinned numpy and pandas versions have no wheels for anything newer.
  echo Install 3.12 and run this again, or change the pins in requirements.txt
  echo and pyproject.toml together if IT gave you different wheels.
  exit /b 1
)

echo Creating virtual environment in .venv ...
python -m venv .venv
if errorlevel 1 goto :error

REM Only upgrade pip when there is an index to reach. On an offline machine
REM this line used to try the network, fail, print a confusing error, and carry
REM on regardless, because nothing checked its exit code.
if "%WHEEL_DIR%"=="" (
  echo Upgrading pip inside the environment ...
  call .venv\Scripts\python.exe -m pip install --upgrade pip
) else (
  echo Skipping the pip upgrade: installing offline from %WHEEL_DIR%.
)

if "%WHEEL_DIR%"=="" (
  echo No wheel folder given. Installing from the default index (needs internet).
  call .venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
) else (
  echo Installing packages from local wheels in %WHEEL_DIR% ...
  call .venv\Scripts\python.exe -m pip install --no-index --find-links "%WHEEL_DIR%" -r requirements.txt -r requirements-dev.txt
)
if errorlevel 1 goto :error

echo.
echo Done. The environment is ready in the .venv folder.
echo To run the tool, use:
echo   .venv\Scripts\python.exe -m alarm_pareto.main --input tests\data\sample_alarm_log.csv --vendor amat
goto :eof

:error
echo.
echo Setup failed. Read the messages above. A common cause is a missing wheel
echo file for one of the packages in requirements.txt.
exit /b 1
