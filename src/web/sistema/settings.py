"""
Django settings for sistema project.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os


PROJECT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)

# SECURITY WARNING: keep the secret key used in production secret! Override its
#                   value in local_settings.py.
SECRET_KEY = 'dummy secret key for the dev environment'

# SECURITY WARNING: don't run with debug turned on in production! Override it
#                   in local_settings.py.
DEBUG = True

# TODO: remove after sorl-thumbnail>12.4a1 is released on pip.
# This setting is removed from django but still referenced by sorl-thumbnail
# which is the dependency of wiki.plugins.images. The issue is already fixed,
# but not released on pip. See
# https://github.com/jazzband/sorl-thumbnail/issues/476 for more details.
TEMPLATE_DEBUG = DEBUG


# Application definition

INSTALLED_APPS = (
    # https://github.com/yourlabs/django-autocomplete-light/blob/master/docs/install.rst
    # It should be before django.contrib.admin and grappelli (if present)
    'dal',
    'dal_select2',

    # Django modules
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    # External django modules
    'reversion',
    # 'social_django',
    'markdown_deux',
    'hijack',
    'hijack_admin',
    'compat',
    'ipware',
    'polymorphic',
    'constance',
    'constance.backends.database',
    'django_tables2',
    'django_nyt',
    'mptt',
    'sekizai',
    'sorl.thumbnail',
    'wiki',
    'wiki.plugins.attachments',
    'wiki.plugins.globalhistory',
    'wiki.plugins.help',
    'wiki.plugins.images',
    'wiki.plugins.links',
    'wiki.plugins.macros',
    'wiki.plugins.notifications',
    'wiki_extensions',

    # Sistema core
    'sistema.apps.SistemaConfig',

    # Sistema core modules
    'dates',
    'frontend',
    'generator',
    'home',
    'questionnaire',
    'schools',
    'users',
    'groups.apps.GroupsConfig',

    # Allauth should be after importing 'users'
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.vk',
    'allauth.socialaccount.providers.twitter',

    # Sistema modules (all should be modules.*)
    'modules.ejudge',
    'modules.enrolled_scans',
    'modules.entrance.apps.EntranceConfig',
    'modules.exam_scorer_2016',
    'modules.finance',
    'modules.poldnev',
    'modules.smartq',
    'modules.study_results.apps.StudyResultsConfig',
    'modules.topics',
)

MIDDLEWARE = (
    'htmlmin.middleware.HtmlMinifyMiddleware',
    'htmlmin.middleware.MarkRequestMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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

                'sekizai.context_processors.sekizai',

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

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, '..', 'db.sqlite3'),
    }
}


# Cache

if DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_ROOT = '../static/'
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, 'static')
]


# Wiki
MEDIA_URL = '/media/'
WIKI_ACCOUNT_HANDLING = False
WIKI_ANONYMOUS = False

def WIKI_CAN_READ(article, user):
    return user.is_staff

# Disable check on page creation whether it's address already used by non-wiki
# urls. It needs to be disabled because any address conflicts with
# /<school_short_name>/... pattern as school_short_name can be equal to "wiki".
WIKI_CHECK_SLUG_URL_AVAILABLE = False

WIKI_EDITOR = 'wiki_extensions.editors.simple_mde.SimpleMDE'


DATE_INPUT_FORMATS = (
    '%d.%m.%Y', '%d.%m.%Y', '%d.%m.%y',  # '25.10.2006', '25.10.2006', '25.10.06'
    '%d-%m-%Y', '%d/%m/%Y', '%d/%m/%y',  # '25-10-2006', '25/10/2006', '25/10/06'
)

DATE_FORMAT = 'd.m.Y'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
    '--rednose',
    '--with-coverage',
    '--cover-package=sistema,dates,frontend,generator,groups,home,modules,'
    + 'questionnaire,schools,users',
]

SISTEMA_QUESTIONNAIRE_STORING_DATE_FORMAT = '%d.%m.%Y'

SISTEMA_UPLOAD_FILES_DIR = os.path.join(BASE_DIR, 'uploads')
if not os.path.exists(SISTEMA_UPLOAD_FILES_DIR):
    os.mkdir(SISTEMA_UPLOAD_FILES_DIR)
else:
    if not os.path.isdir(SISTEMA_UPLOAD_FILES_DIR):
        raise Exception('Upload directory (SISTEMA_UPLOAD_FILES_DIR) exists but is not a folder')

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
if not os.path.exists(MEDIA_ROOT):
    os.mkdir(MEDIA_ROOT)
else:
    if not os.path.isdir(MEDIA_ROOT):
        raise Exception('Upload directory (MEDIA_ROOT) exists but is not a folder')


SISTEMA_GENERATOR_FONTS_DIR = os.path.join(SISTEMA_UPLOAD_FILES_DIR, 'generator-fonts')
# I.e. for images used in generate documents
SISTEMA_GENERATOR_ASSETS_DIR = os.path.join(SISTEMA_UPLOAD_FILES_DIR, 'generator-assets')

SISTEMA_FINANCE_DOCUMENTS = os.path.join(SISTEMA_UPLOAD_FILES_DIR, 'finance-documents')

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_CONFIG = {
    'SISTEMA_CURRENT_SCHOOL_SHORT_NAME': ('2016',
                                          'Короткое название текущей смены'),

    'SISTEMA_EJUDGE_BACKEND_ADDRESS': ('https://ejudge.andgein.ru',
                                       'Адрес еджадж-сервера'),

    'SISTEMA_EJUDGE_USER': ('', 'Имя пользователя на еджадж-сервере'),

    'SISTEMA_EJUDGE_PASSWORD': ('', 'Пароль пользователя на еджадж-сервере'),

    'SISTEMA_ENTRANCE_CHECKING_TIMEOUT': (
        30,
        'Время для проверки одного решения вступительной работы (в минутах)'
    ),

    'SMARTQ_MODULE_EXECUTION_TIMEOUT': (
        1.0,
        'Ограничение по времени на компиляцию и выполнение модуля вопроса '
        '(в секундах)'),
    'SMARTQ_CHECKER_INSTANTIATION_TIMEOUT': (
        1.0,
        'Ограничение по времени на создание объекта чекера для вопроса '
        '(в секундах)'),
    'SMARTQ_GENERATOR_INSTANTIATION_TIMEOUT': (
        1.0,
        'Ограничение по времени на создание объекта генератора для вопроса '
        '(в секундах)'),
    'SMARTQ_CHECKER_TIMEOUT': (
        1.0,
        'Ограничение по времени на проверку вопроса (в секундах)'),
    'SMARTQ_GENERATOR_TIMEOUT': (
        1.0,
        'Ограничение по времени на генерацию вопроса (в секундах)'),
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


# Override settings defined above with the settings from local_settings.py
try:
    from sistema.local_settings import *
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(
        'WARNING: No local sistema settings (local_settings.py) found. Using '
        'default values from settings.py.')
