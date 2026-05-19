@echo off
:: Configuracoes de codificacao para mostrar caracteres sem acento corretamente
chcp 65001 > nul

echo ===================================================
echo   ATUALIZAR PROJETO NO GITHUB - BAR ESCOLAR PAP
echo ===================================================
echo.

:: Verificar se o Git esta instalado
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] O Git nao esta instalado ou nao esta no PATH do Windows!
    echo Por favor, instala o Git para continuar.
    pause
    exit /b
)

:: Inicializar o repositorio se ainda nao estiver
if not exist .git (
    echo [INFO] Inicializando repositorio Git local...
    git init
    git branch -M main
)

:: Verificar e associar o repositorio remoto correto
git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] A adicionar o repositorio remoto origin...
    git remote add origin https://github.com/Pedrogo09/PAP.git
) else (
    echo [INFO] A atualizar o endereco do repositorio remoto origin...
    git remote set-url origin https://github.com/Pedrogo09/PAP.git
)

echo.
echo Adicionando alteracoes...
git add .

echo.
:: Pedir mensagem de commit ao utilizador
set "commit_msg="
set /p commit_msg="Escreve a mensagem do commit (ou Enter para 'Atualizacao automatica'): "

if "%commit_msg%"=="" (
    set commit_msg=Atualizacao automatica: %date% %time%
)

echo.
echo Efetuando commit...
git commit -m "%commit_msg%"

echo.
echo A enviar para o GitHub (ramo: main)...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ===================================================
    echo [SUCESSO] Projeto atualizado no GitHub com sucesso!
    echo ===================================================
) else (
    echo.
    echo ===================================================
    echo [ERRO] Falha ao enviar para o GitHub.
    echo Verifica a tua ligacao a Internet ou as tuas permissoes.
    echo ===================================================
)

echo.
pause
