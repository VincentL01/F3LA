@echo off
setlocal enabledelayedexpansion

set "python_version=3.9.13"
set "venv_name=TAN_env"

REM Set APP_DIR to current directory
set "APP_DIR=%~dp0"

if "%OS%"=="Windows_NT" (
    set "miniconda_url=https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
    set "miniconda_installer=%~dp0Miniconda3-latest-Windows-x86_64.exe"
) else (
    set "miniconda_url=https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
    set "miniconda_installer=%~dp0Miniconda3-latest-MacOSX-x86_64.sh"
)

REM If Miniconda is not installed, download and install it
if "%OS%"=="Windows_NT" (
    set "bat_found=0"

    for %%p in (
        "C:\ProgramData\miniconda3"
        "C:\ProgramData\Anaconda3"
        "C:\ProgramData\.conda"
        "%UserProfile%\miniconda3"
        "%UserProfile%\.conda"
        "%UserProfile%\Anaconda3"
    ) do (
        if exist "%%~p\Scripts\activate.bat" (
            set "conda_path=%%~p"
            set "bat_found=1"
        )
    )

    if !bat_found!==0 (
        echo Downloading Miniconda...
        powershell.exe -Command "(New-Object System.Net.WebClient).DownloadFile('%miniconda_url%', '%miniconda_installer%')"

        echo Installing Miniconda...
        start /wait "" "%miniconda_installer%" /InstallationType=JustMe /AddToPath=0 /RegisterPython=0 /S /D=%UserProfile%\miniconda3

        set "conda_path=%UserProfile%\miniconda3"
    ) else (
        echo Anaconda or Miniconda already installed
    )
) else (
    if not exist "$HOME/miniconda3" (
        if not exist "$HOME/anaconda3" (
            echo Downloading Miniconda...
            curl -o %miniconda_installer% %miniconda_url%

            echo Installing Miniconda...
            chmod +x %miniconda_installer%
            bash %miniconda_installer% -b -p $HOME/miniconda3

            set "conda_path=$HOME/miniconda3"
        ) else (
            set "conda_path=$HOME/anaconda3"
        )
    ) else (
        echo Miniconda already installed
        set "conda_path=$HOME/miniconda3"
    )
)

REM Check if the virtual environment already exists
if exist "%conda_path%\envs\%venv_name%" (
    echo %venv_name% already exists
) else (
    echo %venv_name% not found
    echo Creating virtual environment with Python %python_version%...
    if "%OS%"=="Windows_NT" (
        call %conda_path%\Scripts\conda create -n %venv_name% python==%python_version% -y
    ) else (
        $conda_path/bin/conda create -n %venv_name% python=%python_version% -y
    )
)

REM Define activation and installation commands based on the OS
if "%OS%"=="Windows_NT" (
    set "activate_cmd=call %conda_path%\Scripts\activate.bat %venv_name%"
    set "install_cmd=call %conda_path%\envs\%venv_name%\Scripts\pip install -r requirements.txt"
) else (
    set "activate_cmd=source $conda_path/bin/activate %venv_name%"
    set "install_cmd=call $conda_path/bin/pip install -r requirements.txt"
)

echo "Current conda path is : %conda_path%"

REM Activate the virtual environment
echo Activating virtual environment... at %conda_path%\envs\%venv_name%
%activate_cmd%

REM Navigate to the application directory
echo Go into directory of APP
cd %APP_DIR%

echo =================================================================================================
echo         Virtual environment setup complete. Installing requirements for this environment
echo =================================================================================================

REM Install the application requirements
echo Installing TAN requirements
%install_cmd%

echo =================================================================================================
echo                                    INSTALLATION COMPLETED !
echo =================================================================================================
echo .
echo          PLEASE RUN THE SpiderID_APP from run.bat file located in the same folder.
echo .
pause
