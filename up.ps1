#Requires -Version 5.1

# ============================================================
# ATUALIZAR PROJETO NO GITHUB - BAR ESCOLAR PAP
# ============================================================

$ErrorActionPreference = 'Stop'

Set-Location -Path $PSScriptRoot

# ============================================================
# CONFIGURACAO
# ============================================================

$Repo = 'https://github.com/Pedrogo09/PAP.git'
$RepoSlug = 'Pedrogo09/PAP'
$Branch = 'main'

# ============================================================
# FUNCOES
# ============================================================

function Sair-ComErro {
    param(
        [string]$Mensagem
    )

    Write-Host ''
    Write-Host '==================================================='
    Write-Host '[ERRO] ' -NoNewline
    Write-Host $Mensagem
    Write-Host '==================================================='
    Write-Host ''

    Read-Host 'Prime Enter para sair'
    exit 1
}

function Executar-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Argumentos
    )

    & git @Argumentos

    if ($LASTEXITCODE -ne 0) {
        throw "Comando Git falhou: git $($Argumentos -join ' ')"
    }
}

# ============================================================
# CABECALHO
# ============================================================

Clear-Host

Write-Host '==================================================='
Write-Host '  ATUALIZAR PROJETO NO GITHUB - BAR ESCOLAR PAP'
Write-Host '==================================================='
Write-Host ''

# ============================================================
# VERIFICAR GIT
# ============================================================

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Sair-ComErro 'Git nao esta instalado ou nao esta disponivel no PATH.'
}

$gitVersion = git --version 2>$null

if (-not $gitVersion) {
    Sair-ComErro 'Nao foi possivel executar o Git.'
}

Write-Host "[OK] $gitVersion"
Write-Host ''

# ============================================================
# VERIFICAR REPOSITORIO LOCAL
# ============================================================

if (-not (Test-Path '.git')) {

    Write-Host '[INFO] Repositorio Git local nao encontrado.'
    Write-Host '[INFO] A inicializar repositorio...'
    Write-Host ''

    try {
        Executar-Git @('init')
        Executar-Git @('branch', '-M', $Branch)
    }
    catch {
        Sair-ComErro $_.Exception.Message
    }

    Write-Host '[OK] Repositorio inicializado.'
}
else {
    Write-Host '[OK] Repositorio Git local encontrado.'
}

Write-Host ''

# ============================================================
# GARANTIR BRANCH MAIN
# ============================================================

try {

    $currentBranch = git branch --show-current 2>$null

    if ([string]::IsNullOrWhiteSpace($currentBranch)) {
        Executar-Git @('branch', '-M', $Branch)
    }
    elseif ($currentBranch -ne $Branch) {
        Write-Host "[INFO] Branch atual: $currentBranch"
        Write-Host "[INFO] A mudar para $Branch..."
        Executar-Git @('branch', '-M', $Branch)
    }

}
catch {
    Sair-ComErro $_.Exception.Message
}

Write-Host ''

# ============================================================
# CONFIGURAR ORIGIN
# ============================================================

try {

    $remotes = @(git remote 2>$null)

    if ($remotes -contains 'origin') {

        Write-Host '[INFO] Remote origin encontrado.'

        $currentRepo = git remote get-url origin 2>$null

        if ($currentRepo -ne $Repo) {

            Write-Host '[INFO] Remote origin incorreto.'
            Write-Host '[INFO] A atualizar...'

            Executar-Git @(
                'remote',
                'set-url',
                'origin',
                $Repo
            )

            Write-Host '[OK] Remote origin atualizado.'
        }
        else {
            Write-Host '[OK] Remote origin configurado corretamente.'
        }

    }
    else {

        Write-Host '[INFO] Remote origin nao encontrado.'
        Write-Host '[INFO] A adicionar...'

        Executar-Git @(
            'remote',
            'add',
            'origin',
            $Repo
        )

        Write-Host '[OK] Remote origin adicionado.'
    }

}
catch {
    Sair-ComErro "Nao foi possivel configurar o remote origin. $($_.Exception.Message)"
}

Write-Host ''

# ============================================================
# MOSTRAR REMOTE
# ============================================================

Write-Host '==================================================='
Write-Host '  REMOTE'
Write-Host '==================================================='
Write-Host ''

git remote -v

Write-Host ''

# ============================================================
# VERIFICAR GITHUB
# ============================================================

Write-Host '[INFO] A verificar o repositorio remoto...'
Write-Host ''

$remoteHasMain = $false

try {

    git ls-remote --exit-code --heads origin $Branch 2>$null

    if ($LASTEXITCODE -eq 0) {
        $remoteHasMain = $true
        Write-Host '[OK] A branch main existe no GitHub.'
    }
    else {
        Write-Host '[INFO] A branch main ainda nao existe no GitHub.'
    }

}
catch {
    Write-Host '[AVISO] Nao foi possivel verificar a branch remota.'
}

Write-Host ''

# ============================================================
# VERIFICAR HISTORICO LOCAL
# ============================================================

$hasCommits = $false

try {

    git rev-parse --verify HEAD 2>$null

    if ($LASTEXITCODE -eq 0) {
        $hasCommits = $true
    }

}
catch {
    $hasCommits = $false
}

# ============================================================
# PRIMEIRO COMMIT
# ============================================================

if (-not $hasCommits) {

    Write-Host '[INFO] Nao existem commits locais.'
    Write-Host '[INFO] A criar commit inicial...'
    Write-Host ''

    try {

        Executar-Git @('add', '.')

        Executar-Git @(
            'commit',
            '-m',
            'Sincronizacao inicial do projeto'
        )

    }
    catch {
        Sair-ComErro "Nao foi possivel criar o commit inicial. $($_.Exception.Message)"
    }

    Write-Host ''
    Write-Host '[OK] Commit inicial criado.'
    Write-Host ''
}

# ============================================================
# ESTADO ATUAL
# ============================================================

Write-Host '==================================================='
Write-Host '  ESTADO DO REPOSITORIO'
Write-Host '==================================================='
Write-Host ''

git status --short

Write-Host ''

# ============================================================
# ADICIONAR ALTERACOES
# ============================================================

Write-Host '[INFO] A adicionar alteracoes...'
Write-Host ''

try {
    Executar-Git @('add', '.')
}
catch {
    Sair-ComErro "Falha ao adicionar os ficheiros. $($_.Exception.Message)"
}

Write-Host '[OK] Ficheiros adicionados.'
Write-Host ''

# ============================================================
# VERIFICAR ALTERACOES
# ============================================================

$stagedChanges = @(git diff --cached --name-only)

if ($stagedChanges.Count -gt 0) {

    Write-Host '[INFO] Alteracoes encontradas:'
    Write-Host ''

    foreach ($file in $stagedChanges) {
        Write-Host "  + $file"
    }

    Write-Host ''

    $commitMsg = Read-Host 'Mensagem do commit (Enter = Atualizacao do projeto)'

    if ([string]::IsNullOrWhiteSpace($commitMsg)) {
        $commitMsg = 'Atualizacao do projeto'
    }

    Write-Host ''
    Write-Host '[INFO] A criar commit...'

    try {

        Executar-Git @(
            'commit',
            '-m',
            $commitMsg
        )

    }
    catch {
        Sair-ComErro "Falha ao criar o commit. $($_.Exception.Message)"
    }

    Write-Host ''
    Write-Host '[OK] Commit criado.'
    Write-Host ''

}
else {

    Write-Host '[INFO] Nao existem alteracoes novas.'
    Write-Host ''
}

# ============================================================
# PUSH
# ============================================================

Write-Host '==================================================='
Write-Host '  ENVIAR PARA O GITHUB'
Write-Host '==================================================='
Write-Host ''

try {

    if ($remoteHasMain) {

        Write-Host '[INFO] A verificar o estado atual do GitHub...'
        Write-Host ''

        & git fetch origin $Branch

        if ($LASTEXITCODE -ne 0) {
            throw 'Falha ao obter o estado do GitHub.'
        }

        $localHead = git rev-parse HEAD
        $remoteHead = git rev-parse "origin/$Branch"

        if ($localHead -eq $remoteHead) {

            Write-Host '[OK] Local e GitHub ja estao sincronizados.'

        }
        else {

            Write-Host '[INFO] A versao local e a versao do GitHub sao diferentes.'
            Write-Host '[INFO] A enviar a versao local...'
            Write-Host ''

            & git push --force-with-lease -u origin $Branch

            if ($LASTEXITCODE -ne 0) {
                throw 'O GitHub recusou o push.'
            }

            Write-Host ''
            Write-Host '[OK] Projeto enviado para o GitHub.'
        }

    }
    else {

        Write-Host '[INFO] A criar a branch main no GitHub...'
        Write-Host ''

        Executar-Git @(
            'push',
            '-u',
            'origin',
            $Branch
        )

        Write-Host '[OK] Projeto enviado para o GitHub.'
    }

}
catch {
    Sair-ComErro "Falha no push. $($_.Exception.Message)"
}

Write-Host ''

# ============================================================
# OBTER PERCENTAGENS DAS LINGUAGENS
# ============================================================

Write-Host '==================================================='
Write-Host '  PERCENTAGENS DAS LINGUAGENS'
Write-Host '==================================================='
Write-Host ''

$linguagens = $null

# ============================================================
# GITHUB CLI
# ============================================================

if (Get-Command gh -ErrorAction SilentlyContinue) {

    Write-Host '[INFO] GitHub CLI encontrado.'
    Write-Host '[INFO] A obter linguagens...'

    try {

        $json = gh api "repos/$RepoSlug/languages" 2>$null

        if ($LASTEXITCODE -eq 0 -and $json) {
            $linguagens = $json | ConvertFrom-Json
        }

    }
    catch {
        $linguagens = $null
    }
}

# ============================================================
# API PUBLICA
# ============================================================

if (-not $linguagens) {

    Write-Host '[INFO] A utilizar a API publica do GitHub...'

    try {

        $linguagens = Invoke-RestMethod `
            -Uri "https://api.github.com/repos/$RepoSlug/languages" `
            -Headers @{
                'User-Agent' = 'PAP-Up-Script'
            } `
            -UseBasicParsing

    }
    catch {

        Write-Host '[AVISO] Nao foi possivel obter as linguagens.'
        Write-Host "[AVISO] $($_.Exception.Message)"
    }
}

# ============================================================
# CALCULAR PERCENTAGENS
# ============================================================

if ($linguagens) {

    $total = 0.0

    foreach ($propriedade in $linguagens.PSObject.Properties) {
        $total += [double]$propriedade.Value
    }

    function Calcular-Porcentagem {
        param(
            [double]$Valor
        )

        if ($total -eq 0) {
            return 0
        }

        return [math]::Round(
            ($Valor / $total) * 100,
            1
        )
    }

    $html = Calcular-Porcentagem ([double]$linguagens.HTML)
    $python = Calcular-Porcentagem ([double]$linguagens.Python)
    $css = Calcular-Porcentagem ([double]$linguagens.CSS)
    $typescript = Calcular-Porcentagem ([double]$linguagens.TypeScript)

    $outros = [math]::Round(
        100 - $html - $python - $css - $typescript,
        1
    )

    if ($outros -lt 0) {
        $outros = 0
    }

    Write-Host "HTML:       ${html}%"
    Write-Host "Python:     ${python}%"
    Write-Host "CSS:        ${css}%"
    Write-Host "TypeScript: ${typescript}%"
    Write-Host "Outros:     ${outros}%"
    Write-Host ''

    # ========================================================
    # ATUALIZAR README
    # ========================================================

    $readme = 'README.md'

    if (Test-Path $readme) {

        try {

            $conteudo = Get-Content `
                -Raw `
                -Encoding UTF8 `
                -Path $readme

            $conteudoNovo = $conteudo

            # HTML
            $conteudoNovo = $conteudoNovo -replace `
                '(?im)^.*\*\*HTML:\*\*.*$',
                "**HTML:** ${html}%"

            # Python
            $conteudoNovo = $conteudoNovo -replace `
                '(?im)^.*\*\*Python:\*\*.*$',
                "**Python:** ${python}%"

            # CSS
            $conteudoNovo = $conteudoNovo -replace `
                '(?im)^.*\*\*CSS:\*\*.*$',
                "**CSS:** ${css}%"

            # TypeScript
            $conteudoNovo = $conteudoNovo -replace `
                '(?im)^.*\*\*TypeScript:\*\*.*$',
                "**TypeScript:** ${typescript}%"

            # Outros
            $conteudoNovo = $conteudoNovo -replace `
                '(?im)^.*\*\*Outros:\*\*.*$',
                "**Outros:** ${outros}%"

            if ($conteudoNovo -ne $conteudo) {

                Set-Content `
                    -Path $readme `
                    -Value $conteudoNovo `
                    -Encoding UTF8

                Write-Host '[OK] README atualizado.'
                Write-Host ''

                git add $readme

                if ($LASTEXITCODE -ne 0) {
                    throw 'Falha ao adicionar README.'
                }

                git commit `
                    -m 'Atualizar percentagens das linguagens'

                if ($LASTEXITCODE -ne 0) {
                    throw 'Falha ao criar commit do README.'
                }

                git push

                if ($LASTEXITCODE -ne 0) {
                    throw 'Falha ao enviar README.'
                }

                Write-Host '[OK] README enviado para o GitHub.'

            }
            else {

                Write-Host '[INFO] README ja esta atualizado.'
            }

        }
        catch {

            Write-Host '[AVISO] Nao foi possivel atualizar o README.'
            Write-Host "[AVISO] $($_.Exception.Message)"
        }

    }
    else {

        Write-Host '[AVISO] README.md nao encontrado.'
    }

}
else {

    Write-Host '[AVISO] Nao foi possivel obter as linguagens.'
    Write-Host '[AVISO] O README nao foi alterado.'
}

# ============================================================
# ESTADO FINAL
# ============================================================

Write-Host ''
Write-Host '==================================================='
Write-Host '  ESTADO FINAL'
Write-Host '==================================================='
Write-Host ''

git status --short

Write-Host ''
Write-Host '==================================================='
Write-Host '[SUCESSO] PROCESSO TERMINADO!'
Write-Host '==================================================='
Write-Host ''

Read-Host 'Prime Enter para sair'