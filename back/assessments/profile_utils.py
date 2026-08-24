from __future__ import annotations

from uuid import UUID


def parse_profile_id(profile_id: str | None) -> UUID:
    """Valida IDs vindos da URL antes de entregá-los ao ORM."""
    value = (profile_id or '').strip()
    if not value:
        raise ValueError('profile_id é obrigatório')
    try:
        return UUID(value)
    except (ValueError, AttributeError, TypeError) as error:
        raise ValueError('profile_id precisa ser um UUID válido') from error
