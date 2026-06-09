@echo off
REM ========================================
REM SCRIPT BATCH - INICIO OLLAMA GPU
REM Configuración automática completa
REM ========================================

cls
color 0B
echo.
echo ╔════════════════════════════════════════════════╗
echo ║  OLLAMA GPU OPTIMIZADO - Inicio Automático   ║
echo ╚════════════════════════════════════════════════╝
echo.

REM ========== CONFIGURACIÓN DE VARIABLES ==========
echo 1. Configurando variables de entorno...
echo.

set CUDA_VISIBLE_DEVICES=0
set OLLAMA_NUM_GPU=1
set OLLAMA_MAX_VRAM=3700
set OLLAMA_KEEP_ALIVE=24h
set OLLAMA_NUM_PARALLEL=1
set OLLAMA_LOAD_TIMEOUT=5m

echo    - CUDA_VISIBLE_DEVICES = 0
echo    - OLLAMA_MAX_VRAM = 3700 MB
echo    - OLLAMA_KEEP_ALIVE = 24h
echo.

REM ========== VERIFICAR GPU ==========
echo 2. Verificando GPU disponible...
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo.

echo 3. Iniciando Ollama en background...
taskkill /f /im "ollama app.exe" >nul 2>&1
taskkill /f /im "ollama.exe" >nul 2>&1
timeout /t 2 /nobreak >nul
start /B ollama serve

REM Esperar a que Ollama inicie
timeout /t 5 /nobreak

echo 4. Precargando modelo en GPU/CPU...
echo    (esto puede tardar 30-60 segundos)
echo.

ollama run sorc/qwen3.5-claude-4.6-opus:4b-gpu "OK" 2>nul

echo.
echo 5. Estado final de GPU:
nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader
echo.

echo ╔════════════════════════════════════════════════╗
echo ║  CONFIGURACIÓN COMPLETADA                    ║
echo ╚════════════════════════════════════════════════╝
echo.
echo INSTRUCCIONES:
echo   1. Abre VS Code
echo   2. Presiona: Ctrl+Shift+L
echo   3. Selecciona modelo: Qwen 3.5 Claude 4b (GPU-Optimizado)
echo   4. Comienza a usar!
echo.
echo Ollama seguira corriendo en background.
echo.
pause
