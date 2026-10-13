# Verificar elevación de Administrador
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-Not $isAdmin) {
    Write-Host "Solicitando permisos de Administrador..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    Exit
}

Set-Location $PSScriptRoot

# Regla de Firewall para puerto 8000
netsh advfirewall firewall add rule name="Sistema Recursos Hidricos (Puerto 8000)" dir=in action=allow protocol=TCP localport=8000 profile=any | Out-Null

if (-Not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "Creando venv e instalando dependencias..." -ForegroundColor Yellow
    python -m venv venv
    .\venv\Scripts\python -m pip install -r requirements.txt
} else {
    $hasFastapi = & .\venv\Scripts\python.exe -c "import fastapi" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Instalando dependencias faltantes en venv..." -ForegroundColor Yellow
        .\venv\Scripts\python.exe -m pip install -r requirements.txt
    }
}

# Configurar hosts si es necesario
$hostsPath = "$env:WINDIR\System32\drivers\etc\hosts"
if (Test-Path $hostsPath) {
    $hostsContent = Get-Content $hostsPath -Raw
    if ($hostsContent -notmatch "recursoshidricos\.local") {
        Add-Content -Path $hostsPath -Value "`n127.0.0.1 recursoshidricos.local`n192.168.100.38 recursoshidricos.local"
    }
}

Write-Host "Iniciando Servidor Seguro (HTTPS) y Panel de Control..." -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " Acceso Seguro en Red Local (LAN):" -ForegroundColor Yellow
Write-Host "  - Dominio Oficial (LAN): https://recursoshidricos.local:8000" -ForegroundColor White
Write-Host "  - Local (esta PC):       https://localhost:8000" -ForegroundColor White
Write-Host "================================================================" -ForegroundColor Cyan
& .\venv\Scripts\python.exe backend\gui_launcher.py $args
