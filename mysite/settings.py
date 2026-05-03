"""
Django settings for mysite project.
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ─────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*']

# ── Applications ─────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pages',
]

# ── Middleware ────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',        # ← must be 2nd
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',         # after Session, before Common
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

# ── Templates ─────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'pages.context_processors.lang_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'

# ── Database ──────────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ── Password Validators ───────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Internationalisation ──────────────────────────────────────────────────────
USE_I18N = True
USE_L10N = True
USE_TZ   = True

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'

LANGUAGES = [
    ('en',      'English'),
    ('ne',      'नेपाली'),
    ('hi',      'हिन्दी'),
    ('zh-hans', '简体中文'),
    ('ar',      'العربية'),
    ('fr',      'Français'),
    ('de',      'Deutsch'),
    ('es',      'Español'),
    ('ja',      '日本語'),
    ('ko',      '한국어'),
    ('pt',      'Português'),
    ('ru',      'Русский'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# ── Static Files ──────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Default Auto Field ────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Payment Gateway Settings ──────────────────────────────────────────────────
ESEWA_BASE_URL     = os.environ.get('ESEWA_BASE_URL', 'https://rc-epay.esewa.com.np')
ESEWA_PRODUCT_CODE = os.environ.get('ESEWA_PRODUCT_CODE', 'EPAYTEST')
ESEWA_SECRET_KEY   = os.environ.get('ESEWA_SECRET_KEY', '8gBm/:&EnhH.1/q')

KHALTI_BASE_URL    = os.environ.get('KHALTI_BASE_URL', 'https://a.khalti.com')
KHALTI_SECRET_KEY  = os.environ.get('KHALTI_SECRET_KEY', 'test_secret_key_dc74e0fd57cb46cd93832aee0a390234')

PAYMENT_RETURN_BASE = os.environ.get('PAYMENT_RETURN_BASE', 'https://shopping-eta-two.vercel.app')