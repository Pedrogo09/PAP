@echo off
title Iniciar Servidor PAP
color 0a

echo ==============================================
echo        A preparar ficheiro .env
echo ==============================================
IF NOT EXIST ".env" (
    echo [INFO] Ficheiro .env nao encontrado. A criar a partir de .env.example...
    copy .env.example .env
    echo [AVISO] Ficheiro .env criado! Nao te esquecas de o editar depois para colocar as tuas passwords/API Keys.
) ELSE (
    echo [OK] Ficheiro .env ja existe.
)

echo.
echo ==============================================
echo        Verificando a instalacao do Python
echo ==============================================

python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [AVISO] Python nao esta instalado no sistema.
    echo [INFO] A tentar instalar a versao mais recente do Python usando winget...
    winget install --id Python.Python.3 --accept-package-agreements --accept-source-agreements >nul 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        echo [INFO] Winget nao disponivel. A iniciar o download manual...
        curl -o python_installer.exe https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe
        echo [INFO] A instalar o Python... Isto pode demorar alguns minutos. Aguarda...
        start /wait python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
        del python_installer.exe
    )
    echo [SUCESSO] Python instalado!
    echo [IMPORTANTE] Por favor, fecha esta janela e volta a abrir o start.bat para que o sistema reconheca o Python.
    pause
    exit /b 0
) ELSE (
    echo [OK] Python esta instalado.
)

echo.
echo ==============================================
echo        A instalar dependencias (Python)
echo ==============================================
python -m pip install --upgrade pip
echo [INFO] A verificar e instalar as versoes mais recentes das dependencias...
python -m pip install --upgrade -r requirements.txt

echo.
echo ==============================================
echo        A realizar migracoes da Base de Dados
echo ==============================================
python manage.py makemigrations
python manage.py migrate

echo.
echo ==============================================
echo        A iniciar o servidor Django
echo ==============================================
python manage.py runserver

pause
