"""
Django settings for sistema project.

Generated by 'django-admin startproject' using Django 1.8.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import datetime

from sistema.local_settings import *

PROJECT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)



# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '&2_k-9xguisgilttn3^akg2v0@%8&d8_l)g_5_yha0yvxll^)%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

ADMINS = [('Андрей Гейн', 'andgein@yandex.ru')]

SERVER_EMAIL = 'admin@sistema.lksh.ru'

# Application definition

INSTALLED_APPS = (
    # https://github.com/yourlabs/django-autocomplete-light/blob/master/docs/install.rst
    # before django.contrib.admin and grappelli (if present)
    'dal',
    'dal_select2',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'reversion',
    'social_django',
    'markdown_deux',
    'hijack',
    'hijack_admin',
    'compat',
    'ipware',
    'polymorphic',
    'constance',
    'constance.backends.database',

    'sistema',

    'frontend',
    'generator',
    'home',
    'questionnaire',
    'schools',
    'users',

    'modules.ejudge',
    'modules.enrolled_scans',
    'modules.entrance',
    'modules.exam_scorer_2016',
    'modules.finance',
    'modules.poldnev',
    'modules.study_results',
    'modules.topics',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.vk',
    'allauth.socialaccount.providers.twitter',
)

SITE_ID = 1
LOGIN_REDIRECT_URL = '/'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_USER_DISPLAY = lambda user: user.get_full_name()

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',

    'schools.middleware.SchoolMiddleware',
    'users.middleware.UserProfileMiddleware',
)

ROOT_URLCONF = 'sistema.urls'

AUTH_USER_MODEL = 'users.User'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_DIR, 'sistema', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_settings_export.settings_export',

                'sistema.staff.staff_context_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'sistema.wsgi.application'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

LOGIN_URL = '/accounts/login/'
LOGOUT_URL = '/accounts/logout/'



# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, '..', 'db.sqlite3'),
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = False

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_ROOT = '../static/'
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, 'static')
]


DATE_INPUT_FORMATS = (
    '%d.%m.%Y', '%d.%m.%Y', '%d.%m.%y',  # '25.10.2006', '25.10.2006', '25.10.06'
    '%d-%m-%Y', '%d/%m/%Y', '%d/%m/%y',  # '25-10-2006', '25/10/2006', '25/10/06'
)

DATE_FORMAT = '%d.%m.%Y'

SISTEMA_UPLOAD_FILES_DIR = os.path.join(BASE_DIR, 'uploads')
if not os.path.exists(SISTEMA_UPLOAD_FILES_DIR):
    os.mkdir(SISTEMA_UPLOAD_FILES_DIR)
else:
    if not os.path.isdir(SISTEMA_UPLOAD_FILES_DIR):
        raise Exception('Upload directory (SISTEMA_UPLOAD_FILES_DIR) exists but is not a folder')


SISTEMA_EJUDGE_BACKEND_ADDRESS = 'https://ejudge.andgein.ru'
SISTEMA_ENTRANCE_CHECKING_TIMEOUT = datetime.timedelta(minutes=30)

SISTEMA_GENERATOR_FONTS_DIR = os.path.join(SISTEMA_UPLOAD_FILES_DIR, 'generator-fonts')
# I.e. for images used in generate documents
SISTEMA_GENERATOR_ASSETS_DIR = os.path.join(SISTEMA_UPLOAD_FILES_DIR, 'generator-assets')

SISTEMA_FINANCE_DOCUMENTS = os.path.join(SISTEMA_UPLOAD_FILES_DIR, 'finance-documents')

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_CONFIG = {
    'SISTEMA_CURRENT_SCHOOL_SHORT_NAME': ('2016', 'Короткое название текущей смены')
}

HIJACK_DISPLAY_ADMIN_BUTTON = False
HIJACK_LOGIN_REDIRECT_URL = '/'
HIJACK_LOGOUT_REDIRECT_URL = '/admin/users/user'
HIJACK_USE_BOOTSTRAP = True
HIJACK_REGISTER_ADMIN = False
HIJACK_ALLOW_GET_REQUESTS = True

EMAIL_BACKEND = 'postmark.django_backend.EmailBackend'
DEFAULT_FROM_EMAIL = 'admin@sistema.lksh.ru'
SISTEMA_CONTACT_US_EMAIL = 'lksh@lksh.ru'

ACCOUNT_ADAPTER = 'users.adapter.AccountAdapter'
ACCOUNT_SIGNUP_FORM_CLASS = 'users.forms.base.BaseSignupForm'
ACCOUNT_FORMS = {
    'login': 'users.forms.LoginForm',
    'signup': 'users.forms.SignupForm',
    'reset_password': 'users.forms.ResetPasswordForm',
    'reset_password_from_key': 'users.forms.ResetPasswordKeyForm',
    'change_password': 'users.forms.ChangePasswordForm',
}
SOCIALACCOUNT_FORMS = {
    'signup': 'users.forms.SocialSignupForm',
}

SETTINGS_EXPORT = [
    'DEBUG',
    'SISTEMA_CONTACT_US_EMAIL',
]


"""For migration: to create SocialApp model"""
SOCIAL_AUTH_VK_OAUTH2_KEY = '2888774'
SOCIAL_AUTH_VK_OAUTH2_SECRET = 'xO6ka9PBnhNunuUyfx5f'
SOCIAL_AUTH_TWITTER_KEY = 'a4XGu2XP4DZE7DAqphTZfdltj'
SOCIAL_AUTH_TWITTER_SECRET = 'DRakQj6dslpLSG2ceoZRrkHF8uh4dGnlMia55cHt9fuuRrNiYs'
