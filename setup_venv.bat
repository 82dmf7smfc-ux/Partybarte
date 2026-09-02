@echo off
REM ---------------------------------------------------------------------------
REM Build the virtual environment for this repository on this Windows machine.
REM Run it from the repository root. One environment serves every project here.
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

set WHEEL_DIR=%1

echo Creating virtual environment in .venv ...
python -m venv .venv
if errorlevel 1 goto :error

echo Upgrading pip inside the environment ...
call .venv\Scripts\python.exe -m pip install --upgrade pip

if "%WHEEL_DIR%"=="" (
  echo No wheel folder given. Installing from the default index (needs internet).
  call .venv\Scripts\python.exe -m pip install -r requirements.txt
) else (
  echo Installing packages from local wheels in %WHEEL_DIR% ...
  call .venv\Scripts\python.exe -m pip install --no-index --find-links "%WHEEL_DIR%" -r requirements.txt
)
if errorlevel 1 goto :error

echo.
echo Done. The environment is ready in the .venv folder.
echo To run all the tests, use:
echo   .venv\Scripts\python.exe -m pytest -q
echo To run the alarm pareto tool on its sample log, use:
echo   cd projects\alarm_pareto
echo   ..\..\.venv\Scripts\python.exe -m alarm_pareto.main --input tests\data\sample_alarm_log.csv --vendor amat
goto :eof

:error
echo.
echo Setup failed. Read the messages above. A common cause is a missing wheel
echo file for one of the packages in requirements.txt.
exit /b 1
