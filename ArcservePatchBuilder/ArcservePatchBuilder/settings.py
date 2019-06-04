"""
Django settings for ArcservePatchBuilder project.

Generated by 'django-admin startproject' using Django 2.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '5===lpqfh@mbz9o2!e58f!6e+(@z$2a3(*kvq0e074gl-n*1!y'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost','10.57.10.31']
HOST_PORT = 8000

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ASBU',
    'channels',
    'werkzeug_debugger_runserver',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ArcservePatchBuilder.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'),],
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

WSGI_APPLICATION = 'ArcservePatchBuilder.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'

PATCH_SUPPORTED_VERSIONS = ['18.0', '17.5.1', '17.5', '17.0']
PATCH_SUPPORTED_EXTENSIONS = ['caz', 'zip']
PATCH_ROOT_URL = os.path.join(BASE_DIR, 'Patches')
PATCH_CA_APM = 'CA_APM'
ARCSERVE_SMTP_SERVER = 'smtp.live.com'
ARCSERVE_SMTP_PORT = 587

CELERY_BROKER_URL = 'redis://10.57.51.87:6379/0'
CELERY_RESULT_BACKEND = 'redis://10.57.51.87:6379/1'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']



ASGI_APPLICATION = 'ArcservePatchBuilder.routing.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('10.57.58.38', 6379)],
        }
    }
}

APM_VERSION_PATH = {
    '16.5.1' : r'APM\APMr16.5sp1\build7003',
    '17.0' : r'APM\APMr17\build7067',
    '17.5' : r'APM\APMr17.5\build7861',
    '17.5.1' : r'APM\APMr17.5SP1\build7903',
    '18.0': r'APM\APMr18\build8007',
}

SIGN_URL = 'http://rmdm-bldvm-l901:8000/sign4dev.aspx'
SIGN_ACCOUNT = 'qiang.liu@arcserve.com'
SIGN_PASSWORD ='<passwd>'

ZIP_FILE_THRESHOLD = 100*1024*1024  #zip file larger than 100MB, we will not try to load it to memery and unzip directly. 
                                    #so that we can have progress update in GUI.

