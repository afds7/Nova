from __future__ import annotations

import hashlib

from django.core.cache import cache


def _profile_key(profile_id: str, suffix: str) -> str:
    return f'nova:{suffix}:profile:{profile_id}'


def dashboard_cache_key(profile_id: str) -> str:
    return _profile_key(str(profile_id), 'dashboard:v1')


def missions_cache_key(profile_id: str) -> str:
    return _profile_key(str(profile_id), 'missions:v1')


def assessment_cache_key(email: str) -> str:
    digest = hashlib.sha256(email.strip().lower().encode('utf-8')).hexdigest()
    # v2 invalida diagnósticos em cache que ainda continham recomendações genéricas.
    return f'nova:assessment:last:v2:{digest}'


def invalidate_profile_cache(profile_id: str) -> None:
    cache.delete(dashboard_cache_key(profile_id))
    cache.delete(missions_cache_key(profile_id))


def invalidate_assessment_cache(email: str) -> None:
    cache.delete(assessment_cache_key(email))
