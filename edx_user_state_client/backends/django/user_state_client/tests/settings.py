"""
Settings for testing the DjangoXBlockUserStateClient.
"""

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test',
    }
}

SECRET_KEY = 'for tests only'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'user_state_client',
    'django_nose'
]

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

USE_TZ = True
