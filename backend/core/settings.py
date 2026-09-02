import os
from pathlib import Path
from datetime import timedelta
from celery.schedules import crontab
import environ

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)

BASE_DIR = Path(__file__).resolve().parent.parent

# Ler .env se existir
environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env'))

SECRET_KEY = env('SECRET_KEY', default='django-insecure-default')
DEBUG = env('DEBUG', default=True)
ALLOWED_HOSTS = ['*']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CORS
CORS_ALLOW_ALL_ORIGINS = True # Para rede interna, isso facilita o acesso de qualquer IP

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Bibliotecas
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    
    # Apps locais
    'tickets',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'api.middleware.UpdateLastActivityMiddleware',
    'api.middleware.ClearSerializerCacheMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL', default=f"postgres://{env('DB_USER', default='postgres')}:{env('DB_PASSWORD', default='postgres')}@{env('DB_HOST', default='db')}:{env('DB_PORT', default='5432')}/{env('DB_NAME', default='whatsapp_saas')}")
}
DATABASES['default']['CONN_MAX_AGE'] = 0

# Cache Redis nativo do Django
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://redis:6379/1'),
        'TIMEOUT': 300,
    }
}

AUTH_USER_MODEL = 'tickets.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

CELERY_BROKER_URL = env('REDIS_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://redis:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = True # Ajustar em produção

# Evolution API Settings
EVOLUTION_API_URL = env('EVOLUTION_API_URL', default='http://evolution-go:8080')
EVOLUTION_API_KEY = env('EVOLUTION_API_TOKEN', default='your-token-here')

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'process-daily-notifications': {
        'task': 'tickets.tasks.process_daily_notifications_task',
        'schedule': crontab(minute='*/5'), # Checa a cada 5 minutos os horários configurados de cada usuário
    },
    'check-unattended-queue': {
        'task': 'tickets.tasks.check_unattended_queue_task',
        'schedule': crontab(minute='*'), # Checa a cada 1 minuto se há mensagens paradas na fila
    },
}
