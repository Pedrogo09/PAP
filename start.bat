@echo off
chcp 65001 > nul

echo ===================================================
echo   INICIALIZADOR DO PROJETO - BAR ESCOLAR PAP
echo ===================================================
echo.

:: Definir variaveis do instalador do Python
set "pythonVersion=3.12.3"
set "pythonUrl=https://www.python.org/ftp/python/%pythonVersion%/python-%pythonVersion%-amd64.exe"
set "pythonFolder=Python312"

if "%PROCESSOR_ARCHITECTURE%"=="x86" (
    if not defined PROCESSOR_ARCHITEW6432 (
        set "pythonUrl=https://www.python.org/ftp/python/%pythonVersion%/python-%pythonVersion%.exe"
        set "pythonFolder=Python312-32"
    )
)

:: Verificar se o Python esta instalado e funcional
set PYTHON_CMD=
py -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
) else (
    python -c "import sys" >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=python
    )
)

:: Se o Python nao foi encontrado, fazer a instalacao silenciosa
if "%PYTHON_CMD%"=="" (
    echo [INFO] Python nao foi detetado no sistema.
    echo [INFO] A iniciar o descarregamento e instalacao automatica do Python %pythonVersion%...
    echo.
    
    :: Descarregar o instalador usando o PowerShell
    echo [INFO] A descarregamento o instalador do Python...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%pythonUrl%' -OutFile '%TEMP%\python_installer.exe'"
    
    if not exist "%TEMP%\python_installer.exe" (
        echo [ERRO] Falha ao descarregar o instalador do Python.
        echo Por favor, instala o Python manualmente a partir de: https://www.python.org/
        pause
        exit /b
    )
    
    echo [INFO] A instalar o Python silenciosamente para o utilizador atual...
    echo (Por favor, aguarda. Isto pode demorar um minuto...)
    start /wait "" "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
    
    :: Apagar o instalador temporario
    del "%TEMP%\python_installer.exe"
    
    :: Tentar localizar o Python recem-instalado
    if exist "%LocalAppData%\Programs\Python\%pythonFolder%\python.exe" (
        set PYTHON_CMD="%LocalAppData%\Programs\Python\%pythonFolder%\python.exe"
        echo [SUCESSO] Python instalado com sucesso!
    ) else if exist "%USERPROFILE%\AppData\Local\Programs\Python\%pythonFolder%\python.exe" (
        set PYTHON_CMD="%USERPROFILE%\AppData\Local\Programs\Python\%pythonFolder%\python.exe"
        echo [SUCESSO] Python instalado com sucesso!
    ) else (
        echo [ERRO] Nao foi possivel localizar o Python apos a instalacao automatica.
        echo Por favor, fecha esta janela, reinicia o computador se necessario, ou instala o Python manualmente.
        pause
        exit /b
    )
) else (
    echo [INFO] Python ja esta instalado no sistema.
)

echo.
:: Criar e ativar o ambiente virtual (venv)
if not exist venv (
    echo [INFO] A criar o ambiente virtual (venv) na pasta do projeto...
    %PYTHON_CMD% -m venv venv
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao criar o ambiente virtual.
        echo A tentar prosseguir utilizando o Python global...
        set VENV_ACTIVE=0
    ) else (
        set VENV_ACTIVE=1
    )
) else (
    echo [INFO] Ambiente virtual (venv) ja existe.
    set VENV_ACTIVE=1
)

if "%VENV_ACTIVE%"=="1" (
    echo [INFO] A ativar o ambiente virtual...
    call venv\Scripts\activate.bat
)

echo.
echo [INFO] A instalar/atualizar as dependencias do projeto (pip)...
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar as dependencias.
    pause
    exit /b
)

echo.
echo [INFO] A aplicar as migracoes na base de dados...
python manage.py migrate
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao aplicar as migracoes.
    pause
    exit /b
)

echo.
echo ===================================================
echo   [SUCESSO] Configuracao inicial concluida!
echo   A iniciar o servidor do Bar Escolar...
echo   Aceda ao site em: http://127.0.0.1:8000/
echo   Para desligar o servidor: prima Ctrl + C nesta janela
echo ===================================================
echo.

python manage.py runserver

pause
