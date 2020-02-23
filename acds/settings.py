import logging
import os
import platform
import socket
import warnings

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VERSION = '1.1-dev'

# Hostname
HOSTNAME = platform.node()

# Validate Python version
if platform.python_version_tuple() < ('3', '5'):
	raise RuntimeError(
		"ACDS requires Python 3.5 or higher (current: Python {})".format(
			platform.python_version())
	)
elif platform.python_version_tuple() < ('3', '6'):
	warnings.warn(
		"Python 3.6 or higher will be required starting with ACDS v1.1 (current: Python {})".format(
			platform.python_version()
		)
	)

#
# Configuration import
#

# Import configuration parameters
try:
	from acds import configuration
except ImportError:
	raise ImproperlyConfigured(
		"Configuration file is not present."
	)

# Enforce required configuration parameters
for parameter in ['ALLOWED_HOSTS', 'DATABASE', 'SECRET_KEY', 'CHANNEL_LAYERS']:
	if not hasattr(configuration, parameter):
		raise ImproperlyConfigured(
			"Required parameter {} is missing from configuration.py.".format(
				parameter)
		)

# Set required parameters
ALLOWED_HOSTS = getattr(configuration, 'ALLOWED_HOSTS')
DATABASE = getattr(configuration, 'DATABASE')
SECRET_KEY = getattr(configuration, 'SECRET_KEY')
CHANNEL_LAYERS = getattr(configuration, 'CHANNEL_LAYERS')
BASE_PATH = getattr(configuration, 'BASE_PATH', '')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = getattr(configuration, 'DEBUG', False)

ADMINS = getattr(configuration, 'ADMINS', [])

EMAIL = getattr(configuration, 'EMAIL', {})

DATABASE.update({
	'ENGINE': 'django.db.backends.postgresql'
})

DATABASES = {
    'default': DATABASE,
}

# Application definition

INSTALLED_APPS = [
    'devicelist',
    'activator',
    'channels',
    'chat',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
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

ROOT_URLCONF = 'acds.urls'

ASGI_APPLICATION = 'acds.routing.application'

TEMPLATES_DIR = BASE_DIR + '/templates'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            TEMPLATES_DIR,
        ],
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

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_REDIRECT_URL = '/devicelist'
LOGIN_URL = '/accounts/login/'


ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_LOGOUT_REDIRECT_URL ="/accounts/login"

# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = '10.184.86.104'
# EMAIL_PORT = 25
# EMAIL_HOST_USER = 'acds@ural.rt.ru'
# DEFAULT_FROM_EMAIL = 'acds@ural.rt.ru'
# SERVER_EMAIL = 'acds@ural.rt.ru'

EMAIL_HOST = EMAIL.get('SERVER')
EMAIL_PORT = EMAIL.get('PORT', 25)
EMAIL_HOST_USER = EMAIL.get('USERNAME')
EMAIL_HOST_PASSWORD = EMAIL.get('PASSWORD')
EMAIL_TIMEOUT = EMAIL.get('TIMEOUT', 10)
SERVER_EMAIL = EMAIL.get('FROM_EMAIL')
EMAIL_SUBJECT_PREFIX = '[ACDS] '

WSGI_APPLICATION = 'acds.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = getattr(configuration, 'LANGUAGE_CODE', 'en-us')

TIME_ZONE = getattr(configuration, 'TIME_ZONE', 'Asia/Yekaterinburg')

USE_I18N = True

USE_L10N = True

USE_TZ = True

SITE_ID = 3

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR + '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'acds', 'project_static'),
]
