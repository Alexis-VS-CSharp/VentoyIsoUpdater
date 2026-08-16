@echo off
REM Crée un ZIP portable Windows — extrait et lance VentoyIsoUpdater.exe, sans installation.
REM Usage : package_zip_win.bat

setlocal

set APP_NAME=VentoyIsoUpdater
if not defined VERSION set VERSION=1.0.0
REM surchargeable : set VERSION=1.2.3 && package_zip_win.bat
set BINARY=dist\windows\%APP_NAME%.exe
set OUTPUT=dist\windows\%APP_NAME%-%VERSION%-windows-portable.zip
set WORK_DIR=build\portable_%APP_NAME%

if not exist "%BINARY%" (
    echo ERREUR : %BINARY% introuvable. Lancez build.bat d'abord.
    pause & exit /b 1
)

echo =^> Préparation du dossier portable...

if exist "%WORK_DIR%" rmdir /s /q "%WORK_DIR%"
mkdir "%WORK_DIR%"

copy "%BINARY%" "%WORK_DIR%\%APP_NAME%.exe" >nul

(
    echo @echo off
    echo start "" "%~dp0%APP_NAME%.exe"
) > "%WORK_DIR%\Lancer %APP_NAME%.bat"

(
    echo VentoyIsoUpdater %VERSION% — Version portable Windows
    echo ==================================================
    echo.
    echo Lancez VentoyIsoUpdater.exe directement.
    echo Aucune installation requise.
    echo.
    echo Vos préférences sont sauvegardées dans :
    echo   %%APPDATA%%\ventoyisoupdater\
    echo.
    echo https://github.com/celmax85
) > "%WORK_DIR%\LISEZMOI.txt"

echo =^> Création du ZIP...
powershell -NoProfile -Command ^
    "Compress-Archive -Path '%WORK_DIR%\*' -DestinationPath '%OUTPUT%' -Force"

if errorlevel 1 (
    echo ERREUR : création du ZIP échouée.
    pause & exit /b 1
)

rmdir /s /q "%WORK_DIR%"

echo.
echo =^> ZIP portable généré : %OUTPUT%
pause
