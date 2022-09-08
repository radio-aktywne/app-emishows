import os
import warnings
from pathlib import Path

from emishows.config import config

warnings.filterwarnings(
    "ignore", message="No directory at", module="whitenoise.base"
)

BASE_DIR = Path().resolve()

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "django_probes",
    "emishows.app",
]

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "emishows.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django_cockroachdb",
        "NAME": "database",
        "USER": "emishows",
        "HOST": config.db_host,
        "PORT": config.db_port,
        "OPTIONS": {
            "password": config.db_password,
            "sslmode": "verify-full",
            "sslrootcert": config.certs_dir / "ca.pem",
            "sslcert": config.certs_dir / "client.cert.pem",
            "sslkey": config.certs_dir / "client.key.pem",
        },
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True

STATIC_ROOT = BASE_DIR / "static"
STATIC_URL = "static/"
WHITENOISE_USE_FINDERS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend"
    ],
}
