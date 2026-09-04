#Requires -Version 5.1
# Inicia o servidor de desenvolvimento do PAP (Windows PowerShell / PowerShell 7).
# Uso:  powershell -ExecutionPolicy Bypass -File .\start.ps1

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Set-Location -Path $PSScriptRoot
$Host.UI.RawUI.WindowTitle = 'Iniciar Servidor PAP'

function Write-Titulo([string]$Texto) {
    Write-Host ''
    Write-Host '=============================================='
    Write-Host "       $Texto"
    Write-Host '=============================================='
}

function Get-PythonCmd {
    foreach ($candidato in @('python', 'python3', 'py')) {
        $exe = Get-Command $candidato -ErrorAction SilentlyContinue
        if ($exe) {
            try {
                & $exe.Source --version *> $null
                if ($LASTEXITCODE -eq 0) { return $exe.Source }
            } catch { }
        }
    }
    return $null
}

Write-Titulo 'A preparar ficheiro .env'
if (-not (Test-Path '.env')) {
    Write-Host '[INFO] Ficheiro .env nao encontrado. A criar a partir de .env.example...'
    Copy-Item '.env.example' '.env'
    Write-Host '[AVISO] Ficheiro .env criado! Edita-o para colocar as tuas passwords/API Keys.'
} else {
    Write-Host '[OK] Ficheiro .env ja existe.'
}

Write-Titulo 'Verificar a instalacao do Python'
$python = Get-PythonCmd

if (-not $python) {
    Write-Host '[AVISO] Python nao esta instalado no sistema.'
    Write-Host '[INFO] A tentar instalar o Python (apenas para o utilizador atual)...'

    $instalado = $false
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id Python.Python.3.12 --scope user `
            --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -eq 0) { $instalado = $true }
    }

    if (-not $instalado) {
        Write-Host '[INFO] Winget indisponivel. A descarregar o instalador manualmente...'
        $installer = Join-Path $env:TEMP 'python_installer.exe'
        Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe' `
            -OutFile $installer -UseBasicParsing
        Write-Host '[INFO] A instalar o Python... Isto pode demorar alguns minutos. Aguarda...'
        Start-Process -FilePath $installer -Wait -ArgumentList `
            '/quiet', 'InstallAllUsers=0', 'PrependPath=1', 'Include_test=0'
        Remove-Item $installer -ErrorAction SilentlyContinue
    }

    Write-Host '[SUCESSO] Python instalado!'
    Write-Host '[IMPORTANTE] Fecha esta janela e volta a correr o start.ps1 para o PATH ser reconhecido.'
    Read-Host 'Prime Enter para sair'
    exit 0
}

Write-Host "[OK] Python encontrado em: $python"

$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (Test-Path $venvPython) {
    Write-Host '[OK] A usar o ambiente virtual .venv'
    $python = $venvPython
}

Write-Titulo 'A instalar dependencias (Python)'
& $python -m pip install --upgrade pip
Write-Host '[INFO] A verificar e instalar as versoes mais recentes das dependencias...'
& $python -m pip install --upgrade -r requirements.txt

Write-Titulo 'A realizar migracoes da Base de Dados'
& $python manage.py makemigrations
& $python manage.py migrate

Write-Titulo 'A iniciar o servidor Django'
& $python manage.py runserver

Read-Host 'Prime Enter para sair'
