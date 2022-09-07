import os
import sys

DIRNAME = os.path.dirname(__file__)

DEBUG = True
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "mydatabase"}}

AUTH_USER_MODEL = 'myapp.User'


INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "telegram_django_bot",
    "django_json_widget",
    "tests.myapp",
)

STATIC_URL = "/static/"
SECRET_KEY = "abc123"
MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

LANGUAGE_CODE = 'ru-RU'

TELEGRAM_TOKEN = '604076170:AAEOy1JQCZ0n-d3LT7DJGjbMaHCla0N4Vag'
TELEGRAM_ROOT_UTRLCONF = 'tests.myapp.utrls'

ROOT_URLCONF = 'tests.urls'

