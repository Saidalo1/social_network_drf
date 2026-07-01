from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

# In development/local runs, resolve db and redis hosts to localhost
POSTGRES_HOST = env("POSTGRES_HOST", default="localhost")
if POSTGRES_HOST == "db":
    POSTGRES_HOST = "localhost"

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"psql://{env('POSTGRES_USER', default='postgres')}:{env('POSTGRES_PASSWORD', default='postgres')}@{POSTGRES_HOST}:{env('POSTGRES_PORT', default=5432)}/{env('POSTGRES_DB', default='social_db')}",
    )
}

# Override celery broker and backend to localhost
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")

REDIS_HOST = env("REDIS_HOST", default="localhost")
if REDIS_HOST == "redis":
    REDIS_HOST = "localhost"

CACHEOPS_REDIS = {
    "host": REDIS_HOST,
    "port": env.int("REDIS_PORT", 6379),
    "db": 1,
}

CACHEOPS_DEFAULTS = {
    "timeout": 60 * 15,
}

CACHEOPS = {
    "app.post": {"ops": ("get", "fetch"), "timeout": 60 * 15, "cache_on_save": True},
    "app.comment": {"ops": ("get", "fetch"), "timeout": 60 * 15, "cache_on_save": True},
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}
