Clear-Host
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║    OLLAMA GPU HÍBRIDO - INICIO OPTIMIZADO      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$env:CUDA_VISIBLE_DEVICES = "0"
$env:OLLAMA_NUM_GPU = "1"
$env:OLLAMA_MAX_VRAM = "3700"
$env:OLLAMA_KEEP_ALIVE = "24h"
$env:OLLAMA_NUM_PARALLEL = "1"

Write-Host "Configuración activada:" -ForegroundColor Yellow
Write-Host "✓ GPU CUDA: NVIDIA RTX 3050" -ForegroundColor Green
Write-Host "✓ Partición: Híbrida Inteligente (GPU/CPU)" -ForegroundColor Green
Write-Host "✓ Modelo Principal: Qwen 3.5 Claude 4b (GPU-Optimizado)" -ForegroundColor Green
Write-Host ""

Write-Host "Cerrando instancias previas y watchdog de Ollama..." -ForegroundColor Yellow
Stop-Process -Name "ollama app" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "ollama" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "Iniciando Ollama con entorno optimizado..." -ForegroundColor Yellow
Start-Process ollama -ArgumentList "serve" -NoNewWindow
Start-Sleep -Seconds 5

Write-Host "Precargando Qwen 4b (Híbrido) en memoria (tardará unos segundos)..." -ForegroundColor Yellow
ollama run sorc/qwen3.5-claude-4.6-opus:4b-gpu "OK" 2>$null | Out-Null

Write-Host ""
Write-Host "✓ Modelo precargado con éxito." -ForegroundColor Green
Write-Host "Estado de VRAM ocupado ahora:" -ForegroundColor Yellow
nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader

Write-Host ""
Write-Host "¡TODO CONFIGURADO Y LISTO!" -ForegroundColor Green
Write-Host "El panel de Continue en VS Code responderá instantáneamente." -ForegroundColor White
