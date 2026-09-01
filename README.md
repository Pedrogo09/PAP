@echo off
setlocal EnableDelayedExpansion

:: ===================================================
:: CONFIGURACOES
:: ===================================================
chcp 65001 > nul

set "REPO=https://github.com/Pedrogo09/PAP.git"
set "API=https://api.github.com/repos/Pedrogo09/PAP/languages"
set "TEMP_JSON=%TEMP%\pap_languages.json"

echo ===================================================
echo   ATUALIZAR PROJETO NO GITHUB - BAR ESCOLAR PAP
echo ===================================================
echo.

:: ===================================================
:: VERIFICAR GIT
:: ===================================================
git --version >nul 2>&1
if %errorlevel% neq 0 (
echo [ERRO] O Git nao esta instalado ou nao esta no PATH do Windows!
echo Por favor, instala o Git para continuar.
pause
exit /b
)

:: ===================================================
:: INICIALIZAR REPOSITORIO
:: ===================================================
if not exist .git (
echo [INFO] Inicializando repositorio Git local...
git init
git branch -M main
)

:: ===================================================
:: CONFIGURAR REMOTE
:: ===================================================
git remote get-url origin >nul 2>&1

if %errorlevel% neq 0 (
echo [INFO] A adicionar o repositorio remoto origin...
git remote add origin %REPO%
) else (
echo [INFO] A atualizar o endereco do repositorio remoto origin...
git remote set-url origin %REPO%
)

echo.

:: ===================================================
:: ADICIONAR ALTERACOES
:: ===================================================
echo Adicionando alteracoes...
git add .

echo.

:: ===================================================
:: MENSAGEM DO COMMIT
:: ===================================================
set "commit_msg="
set /p commit_msg="Escreve a mensagem do commit (ou Enter para 'Atualizacao automatica'): "

if "%commit_msg%"=="" (
set "commit_msg=Atualizacao automatica: %date% %time%"
)

echo.

:: ===================================================
:: COMMIT
:: ===================================================
echo Efetuando commit...
git commit -m "%commit_msg%"

echo.

:: ===================================================
:: PULL
:: ===================================================
echo A sincronizar alteracoes do GitHub...

git pull origin main --allow-unrelated-histories -X ours --no-edit

if %errorlevel% neq 0 (
echo.
echo [ERRO] Falha ao sincronizar com o GitHub.
echo.
pause
exit /b
)

echo.

:: ===================================================
:: PRIMEIRO PUSH
:: ===================================================
echo A enviar para o GitHub...

git push -u origin main

if %errorlevel% neq 0 (
echo.
echo ===================================================
echo [ERRO] Falha ao enviar para o GitHub.
echo ===================================================
echo.
pause
exit /b
)

echo.
echo [SUCESSO] Projeto enviado para o GitHub!
echo.

:: ===================================================
:: OBTER NOVAS LINGUAGENS DO GITHUB
:: ===================================================
echo ===================================================
echo   A ATUALIZAR PERCENTAGENS DAS LINGUAGENS
echo ===================================================
echo.

echo [INFO] A consultar o GitHub...

curl -L -s -o "%TEMP_JSON%" ^
-H "Accept: application/vnd.github+json" ^
"%API%"

if not exist "%TEMP_JSON%" (
echo [AVISO] Nao foi possivel consultar a API do GitHub.
goto FINAL
)

:: ===================================================
:: CALCULAR PERCENTAGENS
:: ===================================================
for /f "tokens=1,2 delims==" %%A in ('powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$json = Get-Content -Raw '%TEMP_JSON%' | ConvertFrom-Json; ^
$total = 0; ^
$json.PSObject.Properties | ForEach-Object { $total += [double]$_.Value }; ^
if ($total -eq 0) { exit 1 }; ^
$html = if ($json.HTML) { [math]::Round(($json.HTML / $total) * 100, 1) } else { 0 }; ^
$python = if ($json.Python) { [math]::Round(($json.Python / $total) * 100, 1) } else { 0 }; ^
$css = if ($json.CSS) { [math]::Round(($json.CSS / $total) * 100, 1) } else { 0 }; ^
$typescript = if ($json.TypeScript) { [math]::Round(($json.TypeScript / $total) * 100, 1) } else { 0 }; ^
$other = [math]::Round(100 - $html - $python - $css - $typescript, 1); ^
Write-Output ('HTML=' + $html); ^
Write-Output ('Python=' + $python); ^
Write-Output ('CSS=' + $css); ^
Write-Output ('TypeScript=' + $typescript); ^
Write-Output ('Other=' + $other)"') do (
set "%%A=%%B"
)

if not defined HTML (
echo [AVISO] Nao foi possivel calcular as percentagens.
goto FINAL
)

echo.
echo Percentagens encontradas:
echo.
echo   🟠 HTML:       !HTML!%%
echo   🐍 Python:     !Python!%%
echo   🎨 CSS:        !CSS!%%
echo   🔵 TypeScript: !TypeScript!%%
echo   ⚪ Outros:     !Other!%%
echo.

:: ===================================================
:: ATUALIZAR README
:: ===================================================
echo [INFO] A atualizar README.md...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$path = 'README.md'; ^
$content = Get-Content -Raw -Encoding UTF8 $path; ^
$content = [regex]::Replace($content, '(?m)^- 🟠 **HTML:**.*$', '- 🟠 **HTML:** !HTML!%%'); ^
$content = [regex]::Replace($content, '(?m)^- 🐍 **Python:**.*$', '- 🐍 **Python:** !Python!%%'); ^
$content = [regex]::Replace($content, '(?m)^- 🎨 **CSS:**.*$', '- 🎨 **CSS:** !CSS!%%'); ^
$content = [regex]::Replace($content, '(?m)^- 🔵 **TypeScript:**.*$', '- 🔵 **TypeScript:** !TypeScript!%%'); ^
$content = [regex]::Replace($content, '(?m)^- ⚪ **Outros:**.*$', '- ⚪ **Outros:** !Other!%%'); ^
Set-Content -Path $path -Value $content -Encoding UTF8"

:: ===================================================
:: VERIFICAR SE README FOI ALTERADO
:: ===================================================
git diff --quiet README.md

if %errorlevel% equ 0 (
echo [INFO] As percentagens ja estavam atualizadas.
goto FINAL
)

echo [INFO] README.md foi atualizado.
echo.

:: ===================================================
:: SEGUNDO COMMIT
:: ===================================================
git add README.md

git commit -m "Atualizar percentagens das linguagens"

echo.

:: ===================================================
:: SEGUNDO PUSH
:: ===================================================
echo [INFO] A enviar README atualizado para o GitHub...

git push

if %errorlevel% neq 0 (
echo.
echo ===================================================
echo [ERRO] O README foi atualizado localmente,
echo mas nao foi possivel enviar a alteracao.
echo ===================================================
echo.
pause
exit /b
)

echo.
echo [SUCESSO] README atualizado e enviado para o GitHub!

:FINAL

echo.
echo ===================================================
echo [SUCESSO] PROJETO ATUALIZADO COM SUCESSO!
echo ===================================================
echo.
pause

del "%TEMP_JSON%" >nul 2>&1

endlocal
:: ===================================================
:: FIM
:: ===================================================
