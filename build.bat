@echo off
REM ════════════════════════════════════════════════════════════════
REM  Moon Predictions — Build Nuitka --onedir (Windows)
REM ════════════════════════════════════════════════════════════════
REM  Compile main.py + moon_calc.py en binaire natif Windows
REM  Sortie : build/main.dist/main.exe (standalone, pas besoin de Python)
REM ════════════════════════════════════════════════════════════════

setlocal

REM Chemin vers Python 3.12 (seule version avec PyQt6 installé)
set PYTHON=C:\Python312\python.exe

REM Vérifier que Python 3.12 existe
if not exist "%PYTHON%" (
    echo [ERREUR] Python 3.12 introuvable : %PYTHON%
    echo Installez Python 3.12 avec PyQt6, skyfield, numpy, nuitka
    exit /b 1
)

REM Se placer dans le répertoire du script
cd /d "%~dp0"

echo ================================================================
echo  Moon Predictions - Build Nuitka --onedir
echo ================================================================
echo.
echo  Python    : %PYTHON%
echo  Source    : main.py + moon_calc.py
echo  Output    : build\main.dist\
echo.
echo  Compilation en cours (5-15 minutes)...
echo ================================================================
echo.

REM Nettoyer l'ancien build
if exist "build" (
    echo [CLEAN] Suppression de l'ancien build...
    rmdir /S /Q "build"
)

REM Build Nuitka
"%PYTHON%" -m nuitka ^
    --standalone ^
    --enable-plugin=pyqt6 ^
    --include-data-dir=data=data ^
    --include-package=skyfield ^
    --include-package-data=skyfield ^
    --include-package=numpy ^
    --windows-console-mode=disable ^
    --output-dir=build ^
    --output-filename=MoonPredictions.exe ^
    --product-name="Moon Predictions" ^
    --product-version=1.0.0 ^
    --file-version=1.0.0 ^
    --file-description="EME Moon Pass Predictions" ^
    --copyright="ON7KGK" ^
    --assume-yes-for-downloads ^
    main.py

if errorlevel 1 (
    echo.
    echo ================================================================
    echo  [ECHEC] Le build a echoue. Voir le log ci-dessus.
    echo ================================================================
    exit /b 1
)

echo.
echo ================================================================
echo  [SUCCES] Build termine !
echo ================================================================
echo.
echo  Executable : build\main.dist\MoonPredictions.exe
echo.
echo  Pour tester : build\main.dist\MoonPredictions.exe
echo.
echo  Pour creer l'installeur : lancer build_installer.bat
echo ================================================================

endlocal
