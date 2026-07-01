"""Pytest global test fixtures configuration."""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client() -> APIClient:
    """
    Returns a fresh Django REST Framework APIClient instance.
    """
    return APIClient()
