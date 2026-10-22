# BotManager one-command startup for Windows PowerShell.
# Opens two windows:
#   - Backend  (FastAPI)  -> http://127.0.0.1:8001
#   - Frontend (Laravel)  -> http://localhost:9999
# Open http://localhost:9999 in your browser when both windows are up.

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'

Write-Host 'Starting BotManager...' -ForegroundColor Cyan

# --- Load backend/.env into this process so uvicorn inherits the variables ---
$backendEnv = Join-Path $backend '.env'
if (Test-Path $backendEnv) {
    foreach ($line in Get-Content $backendEnv) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
            $name = $Matches[1]
            $value = $Matches[2].Trim().Trim('"')
            if ($value -ne '') { Set-Content -Path "Env:\$name" -Value $value }
        }
    }
}

# --- Make sure Laravel's storage / sqlite structure exists ---
foreach ($dir in @(
    'storage\framework\views',
    'storage\framework\cache\data',
    'storage\framework\sessions',
    'storage\logs',
    'bootstrap\cache'
)) {
    New-Item -ItemType Directory -Force -Path (Join-Path $frontend $dir) | Out-Null
}
if (!(Test-Path (Join-Path $frontend 'database\database.sqlite'))) {
    New-Item -ItemType File -Path (Join-Path $frontend 'database\database.sqlite') | Out-Null
}

# --- Backend window: venv + uvicorn on port 8001 ---
$backendCmd = "Set-Location '$backend'; " +
    "if (Test-Path '.\venv\Scripts\Activate.ps1') { . '.\venv\Scripts\Activate.ps1' } " +
    "else { Write-Host 'WARNING: backend\venv not found. Create it first: cd backend; python -m venv venv; .\venv\Scripts\pip install -r requirements.txt' -ForegroundColor Yellow }; " +
    "Write-Host 'Backend  : http://127.0.0.1:8001' -ForegroundColor Green; " +
    "uvicorn main:app --reload --port 8001"
Start-Process powershell.exe -ArgumentList '-NoExit', '-Command', $backendCmd -WorkingDirectory $backend

# --- Frontend window: migrations + php artisan serve on port 9999 ---
$frontendCmd = "Set-Location '$frontend'; " +
    "php artisan migrate --force; " +
    "php artisan config:clear; " +
    "Write-Host 'Frontend : http://localhost:9999' -ForegroundColor Green; " +
    "php artisan serve --port=9999"
Start-Process powershell.exe -ArgumentList '-NoExit', '-Command', $frontendCmd -WorkingDirectory $frontend

Write-Host ''
Write-Host 'Backend window  : FastAPI on http://127.0.0.1:8001 (docs at /docs)' -ForegroundColor Green
Write-Host 'Frontend window : Laravel on http://localhost:9999' -ForegroundColor Green
Write-Host 'Waiting for both to boot, then open http://localhost:9999 in your browser.' -ForegroundColor Cyan