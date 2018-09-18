"""Test project settings."""

SECRET_KEY = 'tes$t'
INSTALLED_APPS = [
    'tests.app'
    ]

DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': ':memory:',
  }
}
