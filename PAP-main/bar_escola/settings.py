"""
Configurações do Django para o projeto bar_escola Order System
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-bar-escola-dev-key-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '0.0.0.0:8000','testserver']

# Para facilitar testes com telemóvel/PC na rede local, habilitar coringa
# quando estamos em DEBUG. Não usar isto em produção.
if DEBUG:
    ALLOWED_HOSTS = ['*']

# URL do site para links em emails (ex: para ativação de conta)
import socket
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

SITE_URL = os.getenv('SITE_URL')
if not SITE_URL:
    SITE_URL = f"http://{get_local_ip()}:8000"


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',  
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bar_app',  # Nossa aplicação principal
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'bar_app.middleware.AdminAccessMiddleware',
]

ROOT_URLCONF = 'bar_escola.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bar_escola.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'pt-pt'
TIME_ZONE = 'Europe/Lisbon'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuração de email
# - `EMAIL_USE_DEVELOPMENT` pode ser forçado com a variável de ambiente
#   (true/1/yes). Quando não está definida, usa o valor de DEBUG.
# - Em desenvolvimento o backend é o `console.EmailBackend`, que **não
#   envia** nada mas imprime o conteúdo no terminal.
# - Em produção deve usar SMTP (Gmail por defeito) e definir as credenciais
#   em `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD`.
import os

EMAIL_USE_DEVELOPMENT = os.getenv('EMAIL_USE_DEVELOPMENT')
if EMAIL_USE_DEVELOPMENT is None:
    # não há override: assumir DEBUG
    EMAIL_USE_DEVELOPMENT = DEBUG
else:
    EMAIL_USE_DEVELOPMENT = EMAIL_USE_DEVELOPMENT.lower() in ('true', '1', 'yes')

if EMAIL_USE_DEVELOPMENT:
    # Desenvolvimento: saída para consola
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'no-reply@barescola.local'
else:
    # Produção: Gmail SMTP (ou outro servidor configurado via env vars)
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER', 'no-reply@barescola.local')

# Custom User Model
AUTH_USER_MODEL = 'bar_app.User'

# Login URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# NOTE: Historic reference removed to avoid misconfiguration