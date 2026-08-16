@echo off
REM Compile setup.iss avec Inno Setup pour produire un installateur .exe Windows.
REM Prérequis : Inno Setup 6+ (https://jrsoftware.org/isinfo.php)
REM Usage : package_installer_win.bat

setlocal

set BINARY=dist\windows\VentoyIsoUpdater.exe
set ICON=assets\icon.ico

if not exist "%BINARY%" (
    echo ERREUR : %BINARY% introuvable. Lancez build.bat d'abord.
    pause & exit /b 1
)

if not exist "%ICON%" (
    echo ERREUR : %ICON% introuvable.
    echo Générez-le avec : python tools\generate_ico.py
    pause & exit /b 1
)

set ISCC=""
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
) else (
    where iscc >nul 2>&1 && set ISCC=iscc
)

if %ISCC%=="" (
    echo ERREUR : Inno Setup introuvable.
    echo Téléchargez : https://jrsoftware.org/isdl.php
    pause & exit /b 1
)

if not defined VERSION set VERSION=1.0.0
REM surchargeable : set VERSION=1.2.3 ^&^& package_installer_win.bat

echo =^> Compilation de l'installateur...
%ISCC% /DAppVersion=%VERSION% setup.iss

if errorlevel 1 (
    echo ERREUR : compilation échouée.
    pause & exit /b 1
)

echo.
echo =^> Installateur généré : dist\windows\VentoyIsoUpdater-%VERSION%-windows-setup.exe
pause
