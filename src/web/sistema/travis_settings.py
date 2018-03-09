"""Django settings for Travis builds"""

import os


DB = os.environ.get('DB', 'sqlite')

if DB == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'travis_db.sqlite3',
        }
    }

if DB == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'travis_db',
            'USER': 'travis',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': '3306',
            'OPTIONS': {
                'sql_mode': 'TRADITIONAL',
                'charset': 'utf8',
                'init_command':
                    'SET '
                    'character_set_connection=utf8,'
                    'collation_connection=utf8_bin;'
                    'SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED',
            }
        },
    }

if DB == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'travis_db',
            'USER': 'postgres',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': '',
        }
    }
