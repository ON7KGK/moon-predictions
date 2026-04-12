@echo off
REM ════════════════════════════════════════════════════════════════
REM  Moon Predictions — Construction de l'installeur NSIS
REM ════════════════════════════════════════════════════════════════
REM  Prérequis : NSIS installé (https://nsis.sourceforge.io/)
REM  Le dossier build\main.dist doit exister (lancer build.bat avant)
REM ════════════════════════════════════════════════════════════════

setlocal

cd /d "%~dp0"

REM Chercher makensis dans les chemins courants
set MAKENSIS=
if exist "C:\Program Files (x86)\NSIS\makensis.exe" set MAKENSIS=C:\Program Files (x86)\NSIS\makensis.exe
if exist "C:\Program Files\NSIS\makensis.exe"       set MAKENSIS=C:\Program Files\NSIS\makensis.exe

if "%MAKENSIS%"=="" (
    echo [ERREUR] NSIS non installe.
    echo.
    echo Telechargez et installez NSIS depuis :
    echo   https://nsis.sourceforge.io/Download
    echo.
    exit /b 1
)

REM Vérifier que le build Nuitka existe
if not exist "build\main.dist\MoonPredictions.exe" (
    echo [ERREUR] Build Nuitka introuvable.
    echo.
    echo Lancez d'abord : build.bat
    echo.
    exit /b 1
)

echo ================================================================
echo  Moon Predictions - Construction de l'installeur NSIS
echo ================================================================
echo.
echo  makensis : %MAKENSIS%
echo  Script   : installer.nsi
echo  Source   : build\main.dist\
echo.
echo  Construction en cours...
echo ================================================================
echo.

"%MAKENSIS%" installer.nsi

if errorlevel 1 (
    echo.
    echo ================================================================
    echo  [ECHEC] Construction echouee
    echo ================================================================
    exit /b 1
)

echo.
echo ================================================================
echo  [SUCCES] Installeur cree !
echo ================================================================
echo.
echo  Fichier : MoonPredictions-Setup-1.0.0.exe
echo ================================================================

endlocal
