@echo off
REM Build un exécutable standalone Windows avec PyInstaller
REM Usage : build.bat

setlocal

if exist ".venv\Scripts\pip.exe" (
    set PIP=.venv\Scripts\pip.exe
    set PYINSTALLER=.venv\Scripts\pyinstaller.exe
) else (
    set PIP=pip
    set PYINSTALLER=pyinstaller
)

echo =^> Installation des dépendances...
%PIP% install -q -r requirements.txt pyinstaller
if errorlevel 1 (
    echo ERREUR : installation des dépendances échouée.
    pause & exit /b 1
)

REM Génère icon.ico si absent
if not exist "assets\icon.ico" (
    echo =^> Génération de assets\icon.ico...
    python tools\generate_ico.py
)

REM Génère les --hidden-import pour tous les modules sources/
set HIDDEN=
for %%f in (sources\*.py) do (
    if not "%%~nf"=="__init__" (
        set HIDDEN=%HIDDEN% --hidden-import sources.%%~nf
    )
)

if not exist "dist\windows" mkdir "dist\windows"

echo =^> Build de l'exécutable Windows...
%PYINSTALLER% ^
    --onefile ^
    --windowed ^
    --name "VentoyIsoUpdater" ^
    --icon "assets\icon.ico" ^
    --add-data "data\distros.json;data" ^
    --add-data "assets;assets" ^
    --hidden-import customtkinter ^
    --hidden-import PIL ^
    --hidden-import PIL._tkinter_finder ^
    --hidden-import packaging ^
    --hidden-import packaging.version ^
    --collect-all customtkinter ^
    --distpath "dist\windows" ^
    --workpath "build" ^
    %HIDDEN% ^
    main.py

if errorlevel 1 (
    echo ERREUR : build échoué.
    pause & exit /b 1
)

echo.
echo =^> Exécutable généré : dist\windows\VentoyIsoUpdater.exe
echo.
echo     Packages disponibles :
echo     package_zip_win.bat          → dist\windows\*-portable.zip
echo     package_installer_win.bat    → dist\windows\*-setup.exe
pause
