from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = ['*'] if DEBUG else config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    # Project apps
    'accounts',
    'billing',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'grocery_billing.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # project-level base.html lives here
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

WSGI_APPLICATION = 'grocery_billing.wsgi.application'

DB_ENGINE = config('DB_ENGINE', default='sqlite')

if DB_ENGINE == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='grocery_billing'),
            'USER': config('DB_USER', default='grocery_user'),
            'PASSWORD': config('DB_PASSWORD', default='grocery_pass'),
            'HOST': config('DB_HOST', default='db'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JS)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
WHITENOISE_MANIFEST_STRICT = False
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (uploaded images)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth redirects
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/billing/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Vision / CNN model service
MODEL_SERVICE_URL = config('MODEL_SERVICE_URL', default='http://model_service:8001')

# Store Configuration
STORE_NAME = config('STORE_NAME', default='Central Grocery Store')
STORE_UPI_ID = config('STORE_UPI_ID', default='grocerystore@upi')
