"""
Settings for the local environment. These definitions override ones from
settings.py file.
"""

# This is an example for your local SIStema settings.
#
# Copy this file to |local_settings.py|, fill in the values for your
# development or prod environment, and remove this comment.

# Uncomment in production, set the actual list of allowed hosts, and generate a
# new security key:
#DEBUG = False
#ALLOWED_HOSTS = ['*']
#SECRET_KEY = '<generate your private secret key and paste it here>'

# Uncomment and replace the example entry with your admin's information. This
# information will be used to send emails in case any exceptions occur.
#ADMINS = [('Admin name', 'admin-email@example.org')]

# The email address that error messages come from, such as those sent to ADMINS
# and MANAGERS
SERVER_EMAIL = 'admin@example.org'

POSTMARK_API_KEY = 'Not_empty_fake_key'
POSTMARK_TEST_MODE = True

ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'

# Access for polygon API to update wiki
POLYGON_API_URL = 'https://polygon.lksh.ru/api/'
POLYGON_API_KEY = ''
POLYGON_API_SECRET = ''
