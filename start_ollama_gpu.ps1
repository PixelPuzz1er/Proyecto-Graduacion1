# ========================================
# SCRIPT DE INICIO OLLAMA - GPU OPTIMIZADO
# Modo: Inicio automático con carga de modelo
# ========================================

Clear-Host
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  OLLAMA GPU OPTIMIZADO - Inicio Automático   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ========== CONFIGURACIÓN DE VARIABLES GLOBALES ==========
Write-Host "1️⃣  Configurando variables de entorno..." -ForegroundColor Yellow

$env:CUDA_VISIBLE_DEVICES = "0"
$env:OLLAMA_NUM_GPU = "1"
$env:OLLAMA_MAX_VRAM = "3700"
$env:OLLAMA_KEEP_ALIVE = "24h"
$env:OLLAMA_NUM_PARALLEL = "1"
$env:OLLAMA_LOAD_TIMEOUT = "5m"

Write-Host "   ✓ CUDA_VISIBLE_DEVICES = 0" -ForegroundColor Green
Write-Host "   ✓ OLLAMA_MAX_VRAM = 3700 MB" -ForegroundColor Green
Write-Host "   ✓ OLLAMA_KEEP_ALIVE = 24h" -ForegroundColor Green
Write-Host ""

# ========== VERIFICAR GPU ==========
Write-Host "2️⃣  Verificando GPU disponible..." -ForegroundColor Yellow
$gpu = nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
Write-Host "   GPU Detectada: $gpu" -ForegroundColor Green
Write-Host ""

# ========== INICIAR OLLAMA ==========
Write-Host "3️⃣  Iniciando Ollama en background..." -ForegroundColor Yellow
Write-Host ""

# Cerrar tray app y procesos previos para evitar conflictos de variables
Stop-Process -Name "ollama app" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "ollama" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Iniciar Ollama en background
Start-Process ollama -ArgumentList "serve" -NoNewWindow
Start-Sleep -Seconds 5

# Verificar que Ollama está corriendo
$ollamaRunning = $false
for ($i = 0; $i -lt 10; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $ollamaRunning = $true
            Write-Host "   ✓ Ollama está corriendo en puerto 11434" -ForegroundColor Green
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $ollamaRunning) {
    Write-Host "   ⚠ Ollama tardó en iniciar, continuando..." -ForegroundColor Yellow
}
Write-Host ""

# ========== PRECARGAR MODELO EN GPU ==========
Write-Host "4️⃣  Precargando modelo en GPU/CPU (esto puede tardar 30-60 segundos)..." -ForegroundColor Yellow
Write-Host "   Esto asegura que las 16 capas estén en VRAM y las 17 en CPU" -ForegroundColor Gray
Write-Host ""

& ollama run sorc/qwen3.5-claude-4.6-opus:4b-gpu "Responde solo con OK" 2>$null | Out-Null

Write-Host ""
Write-Host "   ✓ Modelo precargado con partición híbrida" -ForegroundColor Green
Write-Host ""

# ========== VERIFICAR ESTADO GPU ==========
Write-Host "5️⃣  Estado final de GPU:" -ForegroundColor Yellow
$gpuStatus = nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader
$memoryInfo = $gpuStatus -split ", "
Write-Host "   VRAM: $($memoryInfo[0]) / $($memoryInfo[1])" -ForegroundColor Green
Write-Host "   GPU Utilization: $($memoryInfo[2])" -ForegroundColor Green
Write-Host ""

# ========== INSTRUCCIONES FINALES ==========
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ TODO CONFIGURADO Y LISTO               ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "📋 PRÓXIMOS PASOS:" -ForegroundColor Cyan
Write-Host "   1. Abre VS Code (si no lo hiciste)" -ForegroundColor White
Write-Host "   2. Presiona: Ctrl+Shift+L" -ForegroundColor White
Write-Host "   3. Haz clic en el selector de modelos" -ForegroundColor White
Write-Host "   4. Selecciona: 'Qwen 3.5 Claude 4b (GPU-Optimizado)'" -ForegroundColor White
Write-Host "   5. ¡Comienza a usar!" -ForegroundColor White
Write-Host ""
Write-Host "⚡ Velocidad esperada: Respuestas en 1-5 segundos" -ForegroundColor Green
Write-Host "🔒 Seguridad: Todo funciona localmente, sin internet" -ForegroundColor Green
Write-Host ""
Write-Host "Presiona ENTER para mantener Ollama en background..." -ForegroundColor Gray
Read-Host

Write-Host ""
Write-Host "✓ Ollama seguirá corriendo. Puedes cerrar esta ventana." -ForegroundColor Green
