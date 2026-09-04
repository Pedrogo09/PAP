#Requires -Version 5.1
# Sincroniza o projeto com o GitHub e atualiza as percentagens de linguagens no README.
# Uso:  powershell -ExecutionPolicy Bypass -File .\up.ps1

# 'Continue': com 'Stop', qualquer texto que o git escreva no stderr (redirecionado) aborta o script.
$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Set-Location -Path $PSScriptRoot

$Repo = 'https://github.com/Pedrogo09/PAP.git'
$RepoSlug = 'Pedrogo09/PAP'

function Sair-ComErro([string]$Mensagem) {
    Write-Host "[ERRO] $Mensagem"
    Read-Host 'Prime Enter para sair'
    exit 1
}

Write-Host '==================================================='
Write-Host '  ATUALIZAR PROJETO NO GITHUB - BAR ESCOLAR PAP'
Write-Host '==================================================='
Write-Host ''

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Sair-ComErro 'Git nao esta instalado.'
}

if (-not (Test-Path '.git')) {
    git init
    git branch -M main
}

$remotes = @(git remote)
if ($remotes -notcontains 'origin') {
    git remote add origin $Repo
} else {
    git remote set-url origin $Repo
}

Write-Host '[INFO] A sincronizar com o GitHub...'
git pull origin main --allow-unrelated-histories -X ours --no-edit
if ($LASTEXITCODE -ne 0) { Sair-ComErro 'Falha no pull.' }

Write-Host ''
Write-Host '[INFO] A adicionar alteracoes...'
git add .

Write-Host ''
$commitMsg = Read-Host 'Mensagem do commit (Enter = Atualizacao automatica)'
if ([string]::IsNullOrWhiteSpace($commitMsg)) { $commitMsg = 'Atualizacao automatica' }

Write-Host ''
Write-Host '[INFO] A criar commit...'
git commit -m $commitMsg

Write-Host ''
Write-Host '[INFO] A enviar para o GitHub...'
git push -u origin main
if ($LASTEXITCODE -ne 0) { Sair-ComErro 'Falha no push.' }

Write-Host ''
Write-Host '[SUCESSO] Projeto enviado para o GitHub!'
Write-Host ''

$linguagens = $null
if (Get-Command gh -ErrorAction SilentlyContinue) {
    $json = gh api "repos/$RepoSlug/languages" 2>$null
    if ($LASTEXITCODE -eq 0 -and $json) { $linguagens = $json | ConvertFrom-Json }
}

if (-not $linguagens) {
    Write-Host '[INFO] GitHub CLI indisponivel. A obter linguagens pela API publica...'
    try {
        $linguagens = Invoke-RestMethod -Uri "https://api.github.com/repos/$RepoSlug/languages" `
            -Headers @{ 'User-Agent' = 'pap-up-script' } -UseBasicParsing
    } catch {
        Write-Host '[AVISO] Nao foi possivel obter as linguagens.'
    }
}

if ($linguagens) {
    $total = 0
    foreach ($p in $linguagens.PSObject.Properties) { $total += $p.Value }

    function Pct($valor) {
        if ($total -eq 0 -or -not $valor) { return 0 }
        return [math]::Round($valor / $total * 100, 1)
    }

    $html = Pct $linguagens.HTML
    $python = Pct $linguagens.Python
    $css = Pct $linguagens.CSS
    $typescript = Pct $linguagens.TypeScript
    $outros = [math]::Round(100 - $html - $python - $css - $typescript, 1)

    Write-Host ''
    Write-Host '==================================================='
    Write-Host '  PERCENTAGENS ATUAIS'
    Write-Host '==================================================='
    Write-Host ''
    Write-Host "  HTML:       $html%"
    Write-Host "  Python:     $python%"
    Write-Host "  CSS:        $css%"
    Write-Host "  TypeScript: $typescript%"
    Write-Host "  Outros:     $outros%"
    Write-Host ''

    $readme = 'README.md'
    $conteudo = Get-Content -Raw -Encoding UTF8 $readme
    $substituicoes = @(
        @{ Pattern = '(?m)^([-*]) 🟠 \*\*HTML:\*\*.*$';       Valor = '{0:0.0}' -f $html },
        @{ Pattern = '(?m)^([-*]) 🐍 \*\*Python:\*\*.*$';     Valor = '{0:0.0}' -f $python },
        @{ Pattern = '(?m)^([-*]) 🎨 \*\*CSS:\*\*.*$';        Valor = '{0:0.0}' -f $css },
        @{ Pattern = '(?m)^([-*]) 🔵 \*\*TypeScript:\*\*.*$'; Valor = '{0:0.0}' -f $typescript },
        @{ Pattern = '(?m)^([-*]) ⚪ \*\*Outros:\*\*.*$';     Valor = '{0:0.0}' -f $outros }
    )
    $etiquetas = @('🟠 **HTML:**', '🐍 **Python:**', '🎨 **CSS:**', '🔵 **TypeScript:**', '⚪ **Outros:**')

    for ($i = 0; $i -lt $substituicoes.Count; $i++) {
        $s = $substituicoes[$i]
        $conteudo = [regex]::Replace($conteudo, $s.Pattern, ('$1 ' + $etiquetas[$i] + ' ' + $s.Valor + '%'))
    }
    Set-Content -Encoding UTF8 -Path $readme -Value $conteudo

    git diff --quiet -- $readme
    if ($LASTEXITCODE -ne 0) {
        git add $readme
        git commit -m 'Atualizar percentagens das linguagens'
        git push
        Write-Host '[SUCESSO] README atualizado no GitHub!'
    }
}

Write-Host ''
Write-Host '==================================================='
Write-Host '[SUCESSO] PROCESSO TERMINADO!'
Write-Host '==================================================='
Read-Host 'Prime Enter para sair'
