@echo off
chcp 65001 >nul
title AntiPiracy Defense Lab - Iniciador
echo ============================================
echo   AntiPiracy Defense Lab
echo   Sobe o DEFENSE-CORE (8484) + Painel (5050)
echo ============================================
echo.

cd /d "%~dp0"

echo [1/2] Iniciando DEFENSE-CORE (servidor fake)...
start "DEFENSE-CORE (8484)" cmd /k "python core_server.py"

timeout /t 3 /nobreak >nul

echo [2/2] Iniciando Painel (5050)...
start "AntiPiracy Painel (5050)" cmd /k "python app.py"

timeout /t 3 /nobreak >nul

echo.
echo Pronto! Abrindo o painel no navegador...
start "" "http://localhost:5050"

echo.
echo --------------------------------------------
echo  Painel:   http://localhost:5050
echo  Fake:     http://localhost:8484
echo --------------------------------------------
echo  Para parar, feche as duas janelas abertas.
echo.
pause
