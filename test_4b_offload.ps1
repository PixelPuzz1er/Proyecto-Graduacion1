Clear-Host
Write-Host "TEST: Cargar 4b con offload KV->CPU" -ForegroundColor Cyan

$env:CUDA_VISIBLE_DEVICES = "0"
$env:OLLAMA_NUM_GPU = "1"
$env:OLLAMA_NUM_GPU_LAYERS = "18"   # pedir 18 de 33 capas
$env:OLLAMA_MAX_VRAM = "3700"      # dejar ~300MB buffer
$env:OLLAMA_KEEP_ALIVE = "24h"
$env:OLLAMA_NUM_PARALLEL = "1"
$env:OLLAMA_KV_CACHE_TYPE = "cpu"   # mantener KV en CPU para ahorrar VRAM

Write-Host "Variables colocadas:" -ForegroundColor Yellow
Write-Host "- OLLAMA_NUM_GPU_LAYERS=18" -ForegroundColor Green
Write-Host "- OLLAMA_MAX_VRAM=3700 MB" -ForegroundColor Green
Write-Host "- OLLAMA_KV_CACHE_TYPE=cpu" -ForegroundColor Green

# Detener Ollama si corre
Get-Process ollama -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Iniciar Ollama
Write-Host "Iniciando Ollama..." -ForegroundColor Yellow
Start-Process ollama -ArgumentList "serve" -NoNewWindow
Start-Sleep -Seconds 5

# Forzar carga del modelo 4b
Write-Host "Intentando cargar sorc/qwen3.5-claude-4.6-opus:4b en GPU (puede tardar)..." -ForegroundColor Yellow
# Ejecutar run para forzar carga y ver logs
& ollama run sorc/qwen3.5-claude-4.6-opus:4b "Prueba de carga" 2>$null | Out-Null

Write-Host "Fin de intento de carga. Estado GPU ahora:" -ForegroundColor Yellow
nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader

Write-Host "Comprueba los logs para ver cuántas capas fueron offloaded." -ForegroundColor Cyan
Write-Host "Si vemos que aún carga pocas capas, volveré a intentar con ajustes menores." -ForegroundColor Cyan

Write-Host "Presiona ENTER para terminar." -ForegroundColor Gray
Read-Host
