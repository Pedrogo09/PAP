"""
Configurações do Django para o projeto bar_escola Order System
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-bar-escola-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

allowed_hosts_env = os.getenv('ALLOWED_HOSTS')
if allowed_hosts_env:
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',')]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Para facilitar testes com telemóvel/PC na rede local, habilitar coringa
# quando estamos em DEBUG. Não usar isto em produção.
if DEBUG:
    ALLOWED_HOSTS = ['*']
    CSRF_TRUSTED_ORIGINS = [
        'https://*.ngrok-free.app',
        'https://*.ngrok-free.dev',
    ]
else:
    # --- CONFIGURAÇÕES DE SEGURANÇA PARA PRODUÇÃO (DEBUG=False) ---
    
    # 1. Cookies Seguros (Cookies Inseguros / Sensitive Data Exposure)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'
    
    # 2. Segurança de Cabeçalhos HTTP (XSS, Sniffing, Clickjacking)
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    
    # 3. HTTP Strict Transport Security (HSTS)
    SECURE_HSTS_SECONDS = 31536000  # 1 ano
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# Application definition
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',  
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'axes',
    'captcha',
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
    'axes.middleware.AxesMiddleware',
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

# JAZZMIN SETTINGS
JAZZMIN_SETTINGS = {
    "site_title": "Bar Escolar Admin",
    "site_header": "Bar Escolar",
    "site_brand": "Bar Escolar",
    "site_logo": "images/logo.png",
    "login_logo": "images/logo.png",
    "site_icon": "images/logo.png",
    "welcome_sign": "Bem-vindo ao Bar Escolar",
    "copyright": "Bar Escolar. Todos os direitos reservados",
    "search_model": ["bar_app.Product", "bar_app.User"],
    "user_avatar": "logo_avatar",
    "topmenu_links": [
        {"name": "Início", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"model": "bar_app.User", "label": "Utilizadores"},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": ["bar_app.Student", "bar_app.Teacher", "bar_app.Staff", "auth.Group"],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "bar_app.User": "fas fa-user-graduate",
        "bar_app.Category": "fas fa-folder",
        "bar_app.Product": "fas fa-hamburger",
        "bar_app.Order": "fas fa-shopping-cart",
        "bar_app.Transaction": "fas fa-exchange-alt",
        "bar_app.StockMovement": "fas fa-boxes",
        "bar_app.BarSchedule": "fas fa-clock",
        "bar_app.WeekdayAvailability": "fas fa-calendar-alt",
        "bar_app.SchoolAccount": "fas fa-university",
        "bar_app.SchoolTransaction": "fas fa-money-bill-wave",
    },
    "order_with_respect_to": ["bar_app.Order", "bar_app.Product", "bar_app.User"],
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    "custom_css": "css/custom_admin_v3.css",
}

JAZZMIN_UI_CONFIG = {
    "navbar_small_text": False,
    "footer_small_text": True,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_fixed": True,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "theme": "slate",
    "dark_mode_theme": "slate",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    },
    "show_ui_builder": False,
}

# NOTE: Historic reference removed to avoid misconfiguration

# Axes Settings
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 15  # minutes
AXES_LOCKOUT_TEMPLATE = 'bar_app/lockout.html'

# Configuração da IA (Barista AI)
# Obtém a tua chave em: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = 'AIzaSyCaLVPrj2sqQ6E0bIJEdX0rXimhnDDE73w'
