@echo off
setlocal EnabledDelayedExpansion
title GuardianAI -- Fraud Detection System Launcher
cls

echo.
echo  ============================================================
echo   Next-Generation AI Payment Protection
echo  ============================================================
echo.

:: ─── STEP 1: CHECK DOCKER ──────────────────────────────────────────────────────
echo  [CHECK] Verifying Docker is running...

:: Use 'docker version' as it is faster and more reliable for a 'liveness' check
docker version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ============================================================
    echo   ERROR: Docker Desktop is NOT running!
    echo.
    echo   Please:
    echo     1. Open Docker Desktop from your taskbar
    echo     2. Wait for it to fully start -- check green icon in tray
    echo     3. Run this script again: .\start.bat
    echo  ============================================================
    echo.
    pause
    exit /b 1
)

echo  [OK]    Docker is running.
echo.

:: ─── STEP 2: LAUNCH SERVICES ───────────────────────────────────────────────────
echo  [1/3] Building and starting AI + Kafka infrastructure...
echo        (First run may take a few minutes while images download)
echo.
docker-compose up --build -d
if errorlevel 1 (
    echo.
    echo  [ERROR] docker-compose failed. Check docker-compose.yml or Docker logs.
    pause
    exit /b 1
)
echo.
echo  [OK]    All services started in the background.
echo.

:: ─── STEP 3: WAIT FOR DASHBOARD ────────────────────────────────────────────────
echo  [2/3] Waiting for GuardianAI dashboard to become live...
echo        Polling http://localhost:8501 ...
powershell -ExecutionPolicy Bypass -Command "$ready = $false; while (-not $ready) { try { $r = Invoke-WebRequest -Uri 'http://localhost:8501' -TimeoutSec 2 -UseBasicParsing; if ($r.StatusCode -eq 200) { $ready = $true } } catch {} if (-not $ready) { Write-Host '.' -NoNewline; Start-Sleep -Seconds 2 } }; Write-Host ''"
echo.
echo  [OK]    Dashboard is live!
echo.

:: ─── STEP 4: OPEN BROWSER ──────────────────────────────────────────────────────
echo  [3/3] Opening GuardianAI in your default browser...
start http://localhost:8501
echo.
echo  ============================================================
echo   GuardianAI is RUNNING at:  http://localhost:8501
echo.
echo   To STOP everything, run:   docker-compose down
echo   Logs are streaming below  (Ctrl+C to stop log following)
echo  ============================================================
echo.
docker-compose logs -f
