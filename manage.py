#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def main():
    """Run administrative tasks."""
    # Auto-copy .env.example to .env if not present
    import shutil
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_dir, ".env")
    env_example_path = os.path.join(base_dir, ".env.example")
    if not os.path.exists(env_path) and os.path.exists(env_example_path):
        shutil.copy(env_example_path, env_path)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
