"""Management command to create a demo user for Swagger testing."""

import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)
User = get_user_model()

DEMO_USERNAME = "demo"
DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo1234"


class Command(BaseCommand):
    help = "Create a demo user for Swagger API testing (idempotent)."

    def handle(self, *args, **options):
        if User.objects.filter(username=DEMO_USERNAME).exists():
            self.stdout.write(self.style.WARNING(f"Demo user '{DEMO_USERNAME}' already exists, skipping."))
            return

        User.objects.create_user(
            username=DEMO_USERNAME,
            email=DEMO_EMAIL,
            password=DEMO_PASSWORD,
            is_verified=True,  # Ensure they can bypass IsEmailVerified permission checks
        )
        self.stdout.write(self.style.SUCCESS(f"Demo user '{DEMO_USERNAME}' created successfully."))
        logger.info("Demo user '%s' created.", DEMO_USERNAME)
