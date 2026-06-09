Clear-Host
Write-Host "OLLAMA GPU - CONFIGURACIÓN FINAL OPTIMIZADA" -ForegroundColor Cyan
Write-Host ""

# Variables de entorno
$env:CUDA_VISIBLE_DEVICES = "0"
$env:OLLAMA_NUM_GPU = "1"
$env:OLLAMA_NUM_GPU_LAYERS = "99"
$env:OLLAMA_MAX_VRAM = "3500"
$env:OLLAMA_KEEP_ALIVE = "24h"
$env:OLLAMA_NUM_PARALLEL = "1"

Write-Host "Configuracion:" -ForegroundColor Yellow
Write-Host "- CUDA_VISIBLE_DEVICES = 0 (GPU)" -ForegroundColor Green
Write-Host "- OLLAMA_NUM_GPU_LAYERS = 99 (TODO en GPU)" -ForegroundColor Green
Write-Host "- Modelo: Qwen 2b (2.7GB - CABE TODO en GPU)" -ForegroundColor Green
Write-Host ""

# Detener Ollama previo
Get-Process ollama -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Iniciar Ollama
Write-Host "Iniciando Ollama..." -ForegroundColor Yellow
Start-Process ollama -ArgumentList "serve" -NoNewWindow
Start-Sleep -Seconds 5

# Cargar modelo 2b en GPU
Write-Host "Cargando modelo 2b en GPU (esperar 20-30 segundos)..." -ForegroundColor Yellow
ollama pull sorc/qwen3.5-claude-4.6-opus:2b 2>$null | Out-Null
ollama run sorc/qwen3.5-claude-4.6-opus:2b "OK" 2>$null | Out-Null

Write-Host ""
Write-Host "Estado GPU:" -ForegroundColor Yellow
$gpuStatus = nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader
$mem = $gpuStatus -split ", "
Write-Host "VRAM: $($mem[0]) / $($mem[1])" -ForegroundColor Green
Write-Host "GPU Utilization: $($mem[2])" -ForegroundColor Green

Write-Host ""
Write-Host "LISTO PARA USAR!" -ForegroundColor Green
Write-Host "1. Cierra VS Code completamente" -ForegroundColor White
Write-Host "2. Reabre VS Code" -ForegroundColor White
Write-Host "3. Presiona Ctrl+Shift+L" -ForegroundColor White
Write-Host "4. El modelo se auto-seleccionara!" -ForegroundColor White
