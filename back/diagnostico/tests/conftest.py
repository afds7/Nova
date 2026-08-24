from __future__ import annotations

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache

from assessments.models import PerfilAluno


@pytest.fixture
def profile_factory(db):
    def create_profile(email: str = 'aluno@example.com', name: str = 'Aluno QA'):
        user = User.objects.create_user(username=email, email=email, password='senha-segura')
        return PerfilAluno.objects.create(user=user, nome=name)

    return create_profile


@pytest.fixture(autouse=True)
def allow_test_hosts(settings):
    settings.ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']


@pytest.fixture(autouse=True)
def clear_cache_between_tests():
    """Evita que um fallback/circuit breaker de um teste contamine outro."""
    cache.clear()
    yield
    cache.clear()
