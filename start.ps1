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

function Update-PathFromRegistry {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = (@($machine, $user) | Where-Object { $_ }) -join ';'
}

function Test-PythonExe([string]$Caminho) {
    if (-not $Caminho) { return $false }
    # Os stubs da Microsoft Store (WindowsApps) abrem a loja em vez de correr o Python.
    if ($Caminho -like '*\WindowsApps\*') { return $false }
    try {
        $versao = & $Caminho --version 2>&1
        return ($LASTEXITCODE -eq 0 -and "$versao" -match 'Python 3\.')
    } catch {
        return $false
    }
}

function Get-PythonCmd {
    Update-PathFromRegistry

    foreach ($candidato in @('python', 'python3')) {
        foreach ($exe in @(Get-Command $candidato -All -ErrorAction SilentlyContinue)) {
            if (Test-PythonExe $exe.Source) { return $exe.Source }
        }
    }

    $pastas = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python'),
        (Join-Path $env:ProgramFiles 'Python*'),
        'C:\Python*'
    )
    foreach ($pasta in $pastas) {
        $encontrados = Get-ChildItem -Path $pasta -Filter 'python.exe' -Recurse -Depth 2 `
            -ErrorAction SilentlyContinue | Sort-Object FullName -Descending
        foreach ($exe in $encontrados) {
            if (Test-PythonExe $exe.FullName) { return $exe.FullName }
        }
    }

    $py = Get-Command 'py' -ErrorAction SilentlyContinue
    if ($py) {
        try {
            $alvo = (& $py.Source -3 -c 'import sys; print(sys.executable)' 2>$null | Select-Object -First 1)
            if (Test-PythonExe $alvo) { return $alvo }
        } catch { }
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

    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id Python.Python.3.12 --scope user `
            --accept-package-agreements --accept-source-agreements
        $python = Get-PythonCmd
    }

    if (-not $python) {
        Write-Host '[INFO] A descarregar o instalador oficial do Python...'
        $installer = Join-Path $env:TEMP 'python_installer.exe'
        Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe' `
            -OutFile $installer -UseBasicParsing
        Write-Host '[INFO] A instalar o Python... Isto pode demorar alguns minutos. Aguarda...'
        Start-Process -FilePath $installer -Wait -ArgumentList `
            '/quiet', 'InstallAllUsers=0', 'PrependPath=1', 'Include_test=0'
        Remove-Item $installer -ErrorAction SilentlyContinue
        $python = Get-PythonCmd
    }

    if (-not $python) {
        Write-Host '[ERRO] Nao foi possivel encontrar o Python depois da instalacao.'
        Write-Host '[INFO] Instala manualmente a partir de https://www.python.org/downloads/'
        Write-Host '       com a opcao "Add python.exe to PATH" activada e corre o script outra vez.'
        Read-Host 'Prime Enter para sair'
        exit 1
    }

    Write-Host '[SUCESSO] Python instalado!'
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
