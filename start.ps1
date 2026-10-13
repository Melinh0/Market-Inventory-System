#Requires -Version 5.1
<#
.SYNOPSIS
  Inicializa o Market Inventory System localmente no Windows (sem Docker).

.DESCRIPTION
  Este script faz tudo que é necessário na primeira ou nas próximas execuções:
    1. Carrega o arquivo .env, se existir (senão usa valores padrão).
    2. Cria/atualiza o ambiente Python (.venv) com uv ou pip.
    3. Verifica se o PostgreSQL está no ar (serviço do Windows ou Docker);
       se não estiver, tenta iniciar sozinho.
    4. Cria o banco de dados, se ainda não existir.
    5. Roda as migrações e popula dados de demonstração (idempotente).
    6. Gera o build do frontend (npm), se necessário.
    7. Sobe o servidor Django em http://localhost:<porta>.

.EXAMPLE
  .\start.ps1
  .\start.ps1 -Port 8080
  .\start.ps1 -RebuildFrontend
  .\start.ps1 -NoSeed
#>
param(
    [int]$Port = 8000,
    [switch]$RebuildFrontend,
    [switch]$SkipFrontend,
    [switch]$NoSeed
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "    $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "    $msg" -ForegroundColor Yellow }

function Invoke-Native {
    param([scriptblock]$Action, [string]$Descricao)
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao executar: $Descricao (código $LASTEXITCODE)"
    }
}

function Get-EnvOrDefault {
    param([string]$Name, [string]$Default)
    $value = [Environment]::GetEnvironmentVariable($Name)
    if ([string]::IsNullOrWhiteSpace($value)) { return $Default }
    return $value
}

# ---------------------------------------------------------------------------
# 1) Variáveis de ambiente (.env opcional)
# ---------------------------------------------------------------------------
$envFile = Join-Path $Root ".env"
if (Test-Path $envFile) {
    Write-Step "Carregando variáveis de $envFile"
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#")) {
            $idx = $line.IndexOf("=")
            if ($idx -gt 0) {
                $key = $line.Substring(0, $idx).Trim()
                $value = $line.Substring($idx + 1).Trim().Trim('"').Trim("'")
                Set-Item -Path "Env:$key" -Value $value
            }
        }
    }
    Write-Ok ".env carregado"
}

$DbName = Get-EnvOrDefault "POSTGRES_DB" "market_inventory"
$DbUser = Get-EnvOrDefault "POSTGRES_USER" "postgres"
$DbPass = Get-EnvOrDefault "POSTGRES_PASSWORD" "postgres"
$DbHost = Get-EnvOrDefault "POSTGRES_HOST" "127.0.0.1"
$DbPort = Get-EnvOrDefault "POSTGRES_PORT" "5432"

$env:POSTGRES_DB = $DbName
$env:POSTGRES_USER = $DbUser
$env:POSTGRES_PASSWORD = $DbPass
$env:POSTGRES_HOST = $DbHost
$env:POSTGRES_PORT = $DbPort
if (-not $env:DJANGO_ALLOWED_HOSTS) {
    $env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1"
}

# ---------------------------------------------------------------------------
# 2) Ambiente Python
# ---------------------------------------------------------------------------
Write-Step "Preparando ambiente Python"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$uv = Get-Command uv -ErrorAction SilentlyContinue

if ($uv) {
    Invoke-Native { uv sync } "uv sync"
    Write-Ok "Dependências instaladas com uv"
} else {
    if (-not (Test-Path $VenvPython)) {
        $py = Get-Command py -ErrorAction SilentlyContinue
        if ($py) {
            Invoke-Native { py -3 -m venv (Join-Path $Root ".venv") } "criar .venv com py"
        } else {
            Invoke-Native { python -m venv (Join-Path $Root ".venv") } "criar .venv com python"
        }
        Write-Ok "Ambiente virtual criado"
    }
    Invoke-Native { & $VenvPython -m pip install --upgrade pip --quiet } "atualizar pip"
    Invoke-Native { & $VenvPython -m pip install (Join-Path $Root ".") --quiet } "instalar projeto"
    Write-Ok "Dependências instaladas com pip"
}

# ---------------------------------------------------------------------------
# 3) PostgreSQL no ar
# ---------------------------------------------------------------------------
function Test-DbPort {
    param([string]$HostName, [int]$PortNumber)
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $client.Connect($HostName, $PortNumber)
        return $true
    } catch {
        return $false
    } finally {
        $client.Dispose()
    }
}

function Wait-DbPort {
    param([string]$HostName, [int]$PortNumber, [int]$TimeoutSeconds = 60)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-DbPort -HostName $HostName -PortNumber $PortNumber) { return $true }
        Start-Sleep -Seconds 2
    }
    return $false
}

Write-Step "Verificando PostgreSQL em ${DbHost}:${DbPort}"
if (-not (Test-DbPort -HostName $DbHost -PortNumber $DbPort)) {
    Write-Warn "PostgreSQL não respondeu; procurando serviço do Windows..."
    $svc = Get-Service -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "*postgres*" } |
        Select-Object -First 1
    if ($svc) {
        Write-Step "Iniciando serviço '$($svc.Name)'"
        if ($svc.Status -ne "Running") { Start-Service $svc.Name }
        [void](Wait-DbPort -HostName $DbHost -PortNumber $DbPort -TimeoutSeconds 60)
    }

    if (-not (Test-DbPort -HostName $DbHost -PortNumber $DbPort)) {
        $docker = Get-Command docker -ErrorAction SilentlyContinue
        if ($docker) {
            Write-Step "Tentando subir PostgreSQL via Docker Compose"
            Invoke-Native { docker compose up -d db } "docker compose up -d db"
            [void](Wait-DbPort -HostName $DbHost -PortNumber $DbPort -TimeoutSeconds 90)
        }
    }

    if (-not (Test-DbPort -HostName $DbHost -PortNumber $DbPort)) {
        Write-Host ""
        Write-Host "Não consegui acessar o PostgreSQL em ${DbHost}:${DbPort}." -ForegroundColor Red
        Write-Host "Opções:" -ForegroundColor Yellow
        Write-Host "  1. Instale o PostgreSQL (https://www.postgresql.org/download/windows/)"
        Write-Host "     e use usuário '$DbUser' / senha '$DbPass', ou ajuste o arquivo .env."
        Write-Host "  2. Instale o Docker Desktop e rode: docker compose up -d db"
        Write-Host "  3. Suba um PostgreSQL em outro endereço e ajuste POSTGRES_* no .env."
        exit 1
    }
}
Write-Ok "PostgreSQL acessível"

# ---------------------------------------------------------------------------
# 4) Criar banco se não existir
# ---------------------------------------------------------------------------
Write-Step "Garantindo que o banco '$DbName' existe"
$createDbScript = @'
import os
import sys

import psycopg

dbname = os.environ["POSTGRES_DB"]
dsn = (
    f"host={os.environ['POSTGRES_HOST']} port={os.environ['POSTGRES_PORT']} "
    f"dbname=postgres user={os.environ['POSTGRES_USER']} "
    f"password={os.environ['POSTGRES_PASSWORD']}"
)
with psycopg.connect(dsn, connect_timeout=10) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        if cur.fetchone() is None:
            cur.execute(f'CREATE DATABASE "{dbname}"')
            print(f"Banco '{dbname}' criado.")
        else:
            print(f"Banco '{dbname}' já existe.")
'@
Invoke-Native { & $VenvPython -c $createDbScript } "criar banco de dados"
Write-Ok "Banco pronto"

# ---------------------------------------------------------------------------
# 5) Migrações e dados de demonstração
# ---------------------------------------------------------------------------
Write-Step "Aplicando migrações"
Invoke-Native { & $VenvPython (Join-Path $Root "manage.py") migrate --noinput } "migrate"

if (-not $NoSeed) {
    Write-Step "Populando dados de demonstração (idempotente)"
    Invoke-Native { & $VenvPython (Join-Path $Root "manage.py") seed_demo } "seed_demo"
}

# ---------------------------------------------------------------------------
# 6) Frontend
# ---------------------------------------------------------------------------
if (-not $SkipFrontend) {
    $distIndex = Join-Path $Root "frontend\dist\index.html"
    if ($RebuildFrontend -or -not (Test-Path $distIndex)) {
        $npm = Get-Command npm -ErrorAction SilentlyContinue
        if (-not $npm) {
            Write-Warn "npm não encontrado — a interface não será servida pelo Django."
            Write-Warn "Instale o Node.js (https://nodejs.org) e rode: cd frontend && npm install && npm run build"
        } else {
            Write-Step "Build do frontend"
            $frontendDir = Join-Path $Root "frontend"
            if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
                Invoke-Native { npm install --prefix $frontendDir } "npm install"
            }
            Invoke-Native { npm run build --prefix $frontendDir } "npm run build"
            Write-Ok "frontend/dist gerado"
        }
    } else {
        Write-Ok "frontend/dist já existe (use -RebuildFrontend para reconstruir)"
    }
}

# ---------------------------------------------------------------------------
# 7) Servidor
# ---------------------------------------------------------------------------
Write-Step "Iniciando servidor em http://localhost:$Port (Ctrl+C para parar)"
Invoke-Native {
    & $VenvPython (Join-Path $Root "manage.py") runserver "127.0.0.1:$Port"
} "runserver"
