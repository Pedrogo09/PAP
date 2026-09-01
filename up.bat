@'
@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

set "REPO=https://github.com/Pedrogo09/PAP.git"

echo ===================================================
echo   ATUALIZAR PROJETO NO GITHUB - BAR ESCOLAR PAP
echo ===================================================
echo.

git --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Git nao esta instalado.
    pause
    exit /b 1
)

if not exist ".git" (
    git init
    git branch -M main
)

git remote get-url origin >nul 2>&1
if errorlevel 1 (
    git remote add origin "%REPO%"
) else (
    git remote set-url origin "%REPO%"
)

echo [INFO] A sincronizar com o GitHub...
git pull origin main --allow-unrelated-histories -X ours --no-edit

if errorlevel 1 (
    echo [ERRO] Falha no pull.
    pause
    exit /b 1
)

echo.
echo [INFO] A adicionar alteracoes...
git add .

echo.
set "commit_msg="
set /p "commit_msg=Mensagem do commit (Enter = Atualizacao automatica): "

if "!commit_msg!"=="" set "commit_msg=Atualizacao automatica"

echo.
echo [INFO] A criar commit...
git commit -m "!commit_msg!"

echo.
echo [INFO] A enviar para o GitHub...
git push -u origin main

if errorlevel 1 (
    echo [ERRO] Falha no push.
    pause
    exit /b 1
)

echo.
echo [SUCESSO] Projeto enviado para o GitHub!
echo.

gh --version >nul 2>&1

if errorlevel 1 (
    echo [AVISO] GitHub CLI nao esta instalado.
    goto FIM
)

set "JSON=%TEMP%\pap_languages.json"

gh api repos/Pedrogo09/PAP/languages > "%JSON%"

if errorlevel 1 (
    echo [AVISO] Nao foi possivel obter as linguagens.
    goto FIM
)

powershell -NoProfile -Command "$j=Get-Content -Raw '%JSON%'|ConvertFrom-Json;$t=0;foreach($x in $j.PSObject.Properties){$t+=$x.Value};$h=if($j.HTML){[math]::Round($j.HTML/$t*100,1)}else{0};$p=if($j.Python){[math]::Round($j.Python/$t*100,1)}else{0};$c=if($j.CSS){[math]::Round($j.CSS/$t*100,1)}else{0};$ts=if($j.TypeScript){[math]::Round($j.TypeScript/$t*100,1)}else{0};$o=[math]::Round(100-$h-$p-$c-$ts,1);Set-Content '%TEMP%\h.txt' $h;Set-Content '%TEMP%\p.txt' $p;Set-Content '%TEMP%\c.txt' $c;Set-Content '%TEMP%\ts.txt' $ts;Set-Content '%TEMP%\o.txt' $o"

set /p HTML=<"%TEMP%\h.txt"
set /p PYTHON=<"%TEMP%\p.txt"
set /p CSS=<"%TEMP%\c.txt"
set /p TYPESCRIPT=<"%TEMP%\ts.txt"
set /p OTHER=<"%TEMP%\o.txt"

echo.
echo ===================================================
echo   PERCENTAGENS ATUAIS
echo ===================================================
echo.
echo   HTML:       !HTML!%%
echo   Python:     !PYTHON!%%
echo   CSS:        !CSS!%%
echo   TypeScript: !TYPESCRIPT!%%
echo   Outros:     !OTHER!%%
echo.

powershell -NoProfile -Command "$p='README.md';$c=Get-Content -Raw -Encoding UTF8 $p;$c=[regex]::Replace($c,'(?m)^- 🟠 \*\*HTML:\*\*.*$','- 🟠 **HTML:** !HTML!%%');$c=[regex]::Replace($c,'(?m)^- 🐍 \*\*Python:\*\*.*$','- 🐍 **Python:** !PYTHON!%%');$c=[regex]::Replace($c,'(?m)^- 🎨 \*\*CSS:\*\*.*$','- 🎨 **CSS:** !CSS!%%');$c=[regex]::Replace($c,'(?m)^- 🔵 \*\*TypeScript:\*\*.*$','- 🔵 **TypeScript:** !TYPESCRIPT!%%');$c=[regex]::Replace($c,'(?m)^- ⚪ \*\*Outros:\*\*.*$','- ⚪ **Outros:** !OTHER!%%');Set-Content -Encoding UTF8 $p $c"

git diff --quiet -- README.md

if not errorlevel 1 goto FIM

git add README.md
git commit -m "Atualizar percentagens das linguagens"
git push

echo [SUCESSO] README atualizado no GitHub!

:FIM

del "%JSON%" >nul 2>&1
del "%TEMP%\h.txt" >nul 2>&1
del "%TEMP%\p.txt" >nul 2>&1
del "%TEMP%\c.txt" >nul 2>&1
del "%TEMP%\ts.txt" >nul 2>&1
del "%TEMP%\o.txt" >nul 2>&1

echo.
echo ===================================================
echo [SUCESSO] PROCESSO TERMINADO!
echo ===================================================
pause
endlocal
'@ | Set-Content -Encoding UTF8 up.bat