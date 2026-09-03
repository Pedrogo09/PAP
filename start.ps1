#Requires -Version 5.1
<#
.SYNOPSIS
    Prepara o ambiente e inicia o servidor Django do Bar Escolar (PAP).
.DESCRIPTION
    Equivalente ao start.bat, mas escrito em PowerShell para funcionar em
    maquinas onde o cmd.exe esta desativado por politica de grupo.
.EXAMPLE
    .\start.ps1
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\start.ps1
#>

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

function Write-Titulo {
    param([string]$Texto)
    Write-Host ''
    Write-Host '==============================================' -ForegroundColor Green
    Write-Host "       $Texto" -ForegroundColor Green
    Write-Host '==============================================' -ForegroundColor Green
}

function Get-ComandoPython {
    foreach ($candidato in @('python', 'python3', 'py')) {
        $comando = Get-Command $candidato -ErrorAction SilentlyContinue
        if ($comando) { return $comando.Source }
    }
    return $null
}

Write-Titulo 'A preparar ficheiro .env'
if (Test-Path '.env') {
    Write-Host '[OK] Ficheiro .env ja existe.'
} else {
    Write-Host '[INFO] Ficheiro .env nao encontrado. A criar a partir de .env.example...'
    Copy-Item '.env.example' '.env'
    Write-Host '[AVISO] Ficheiro .env criado! Nao te esquecas de o editar para colocar as tuas passwords/API Keys.' -ForegroundColor Yellow
}

Write-Titulo 'Verificando a instalacao do Python'
$python = Get-ComandoPython
if (-not $python) {
    Write-Host '[ERRO] Python nao foi encontrado no PATH.' -ForegroundColor Red
    Write-Host '[INFO] Instala o Python a partir de https://www.python.org/downloads/ e marca a opcao "Add python.exe to PATH".'
    Write-Host '[INFO] Depois fecha e volta a abrir o PowerShell e corre novamente este script.'
    exit 1
}
Write-Host "[OK] Python encontrado em: $python"

Write-Titulo 'A instalar dependencias (Python)'
& $python -m pip install --upgrade pip
& $python -m pip install --upgrade -r requirements.txt

Write-Titulo 'A realizar migracoes da Base de Dados'
& $python manage.py makemigrations
& $python manage.py migrate

Write-Titulo 'A iniciar o servidor Django'
Write-Host 'Aceda em: http://127.0.0.1:8000'
& $python manage.py runserver
