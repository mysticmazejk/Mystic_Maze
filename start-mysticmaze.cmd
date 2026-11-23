@echo off
setlocal

cd /d "%~dp0"

echo Mystic Maze - Einrichtung
echo.

py -3 --version >nul 2>&1

if errorlevel 1 (
    echo FEHLER: Python wurde nicht gefunden.
    echo.
    echo Bitte Python 3 installieren und danach erneut starten.
    echo Bei der Installation "Add Python to PATH" aktivieren.
    echo.
    pause
    exit /b 1
)

REM Virtuelle Umgebung nur beim ersten Start erstellen
if not exist ".venv\Scripts\python.exe" (
    echo Erstelle virtuelle Umgebung...
    echo.

    py -3 -m venv .venv

    if errorlevel 1 (
        echo.
        echo FEHLER: Die virtuelle Umgebung konnte nicht erstellt werden.
        echo.
        echo Python-Version:
        py -3 --version
        echo.
        pause
        exit /b 1
    )
) else (
    echo Virtuelle Umgebung bereits vorhanden.
)

echo.
echo Installiere bzw. aktualisiere Abhaengigkeiten...
".venv\Scripts\python.exe" -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo FEHLER: Requirements konnten nicht installiert werden.
    pause
    exit /b 1
)

echo.
echo Starte Mystic Maze...
echo.

set "PORT=8000"

for /f "tokens=2 delims=:" %%I in ('ipconfig ^| findstr /c:"IPv4-Adresse"') do (
    for /f "tokens=*" %%J in ("%%I") do set "IP=%%J"
)

if not defined IP (
    echo Keine aktive IPv4-Adresse gefunden.
    set "IP=localhost"
)

echo Mystic Maze
echo.
echo Lokal:
echo http://localhost:%PORT%
echo.
echo Im WLAN:
echo http://%IP%:%PORT%
echo.
echo Zum Beenden STRG+C druecken.
echo.

".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port %PORT%

echo.
echo Server wurde beendet.
pause