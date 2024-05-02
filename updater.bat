@echo off
setlocal enabledelayedexpansion

set "my_repo=https://github.com/VincentL01/F3LA"
@REM set my_dir at parent directory/temp_update
set "parent_dir=%~dp0.."
set "my_dir=%parent_dir%\temp_update"

@REM Make my_dir if not existed
if not exist "%my_dir%" mkdir "%my_dir%"

echo "Finding conda path..."

if "%OS%"=="Windows_NT" (
  set "bat_found=0"

  echo "OS is Windows"

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
)

if !bat_found!==0 (
    echo "No conda installation found. Please install conda and try again."
    exit /b 1
) else (
    echo "Conda installation found at %conda_path%"
)

echo "Updating program..."

if "%OS%"=="Windows_NT" (
        set "get_git=call %conda_path%\Scripts\conda install -c anaconda git -y"
) else (
        set "get_git=call $conda_path/bin/conda install -c anaconda git -y"
)

@REM Check if Git is installed
where git >nul 2>nul
if errorlevel 1 (
  echo Downloading and installing Git...
  %get_git%
) else (
  echo Git is already installed. Skipping installation.
  FOR /F "tokens=*" %%F IN ('where git') DO SET git_path=%%F
  echo git path is !git_path!
)

if "%OS%"=="Windows_NT" (
        set clone_cmd=call "!git_path!" clone %my_repo% %my_dir%
) else (
        set clone_cmd=call "!git_path!" clone %my_repo% %my_dir%
)

@REM Clone the repo
echo Cloning the repo...
%clone_cmd%

@REM copy repo/Libs and repo/main.py to replace current Libs and main.py
echo Copying Libs/*.* ...
xcopy /y /q /e "%my_dir%\Libs" "%cd%\Libs"
echo Copying main.py ...
xcopy /y /q /e "%my_dir%\main.py" "%cd%\main.py"
echo Copying updater.bat ...
xcopy /y /q /e "%my_dir%\updater.bat" "%cd%\updater.bat"
echo Copying requirements.txt ...
xcopy /y /q /e "%my_dir%\requirements.txt" "%cd%\requirements.txt"

@REM Remove temp_update folder
echo Removing temp_update folder...
rmdir /s /q "%my_dir%"

echo =================================================================================================
echo                                    UPDATE COMPLETED !
echo =================================================================================================
echo .
pause