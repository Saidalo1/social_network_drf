from .base import *

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

# In production/docker environments, resolve db and redis hosts to container names
POSTGRES_HOST = env("POSTGRES_HOST", default="db")

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"psql://{env('POSTGRES_USER', default='postgres')}:{env('POSTGRES_PASSWORD', default='postgres')}@{POSTGRES_HOST}:{env('POSTGRES_PORT', default=5432)}/{env('POSTGRES_DB', default='social_db')}",
    )
}

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://redis:6379/0")

REDIS_HOST = env("REDIS_HOST", default="redis")

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

# Production security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)
X_FRAME_OPTIONS = "DENY"
