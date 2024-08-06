@echo off

set "venv_name=TAN_env"
set "APP_DIR=%~dp0"

REM Activate the conda environment
call %UserProfile%\miniconda3\Scripts\activate %venv_name%

REM Navigate to the application directory
cd %APP_DIR%

REM Run the application
echo Running the application...
python main.py

REM Deactivate the environment after running the application
call conda deactivate

echo Application execution completed.
pause
