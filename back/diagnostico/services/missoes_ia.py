from __future__ import annotations

import json
import hashlib
import logging
import os
import re
import time
from typing import Any

from django.core.cache import cache

logger = logging.getLogger(__name__)

AI_CACHE_SECONDS = 15 * 60
AI_FALLBACK_CACHE_SECONDS = 60
AI_TIMEOUT_SECONDS = float(os.getenv('OPENAI_MISSIONS_TIMEOUT_SECONDS', '3'))
AI_CIRCUIT_SECONDS = 60
EMAIL_PATTERN = re.compile(r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b')


def _without_pii(value: str) -> str:
    """Remove identificadores óbvios antes de qualquer texto chegar ao prompt."""
    return EMAIL_PATTERN.sub('[informação removida]', value or '')[:500]


def _fallback_payload(base: dict[str, Any], competency: str) -> dict[str, Any]:
    return {
        'titulo': base['titulo'],
        'descricao': f"Uma proposta que pode ajudar em {competency}: {base['descricao']}",
        'estimativa_tempo': base['duracao_estimada_minutos'],
        'competencia_alvo': competency,
        'origem_geracao': 'regra',
    }


def personalizar_missao(
    *,
    profile_id: str,
    base_mission: dict[str, Any],
    competency_gap: str,
    objective_area: str,
    strong_competencies: list[str],
    completed_mission_types: list[str],
) -> dict[str, Any]:
    """Serializa chamadas concorrentes da mesma sugestão para evitar estampede."""
    raw_cache_key = f"{profile_id}:{base_mission['id']}:{competency_gap}"
    cache_key = f"mission-ai:v1:{hashlib.sha256(raw_cache_key.encode('utf-8')).hexdigest()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    lock_key = f'{cache_key}:lock'
    owns_lock = cache.add(lock_key, '1', 15)
    if not owns_lock:
        for _ in range(60):
            time.sleep(0.05)
            cached = cache.get(cache_key)
            if cached:
                return cached
        owns_lock = cache.add(lock_key, '1', 15)

    try:
        cached = cache.get(cache_key)
        if cached:
            return cached
        return _personalizar_missao_uncached(
            profile_id=profile_id,
            base_mission=base_mission,
            competency_gap=competency_gap,
            objective_area=objective_area,
            strong_competencies=strong_competencies,
            completed_mission_types=completed_mission_types,
        )
    finally:
        if owns_lock:
            cache.delete(lock_key)


def _personalizar_missao_uncached(
    *,
    profile_id: str,
    base_mission: dict[str, Any],
    competency_gap: str,
    objective_area: str,
    strong_competencies: list[str],
    completed_mission_types: list[str],
) -> dict[str, Any]:
    """Personaliza apenas a apresentação; a lacuna vem exclusivamente das regras."""
    raw_cache_key = f"{profile_id}:{base_mission['id']}:{competency_gap}"
    cache_key = f"mission-ai:v1:{hashlib.sha256(raw_cache_key.encode('utf-8')).hexdigest()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    fallback = _fallback_payload(base_mission, competency_gap)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return fallback
    if cache.get('mission-ai:circuit:open'):
        return fallback

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            timeout=AI_TIMEOUT_SECONDS,
            max_retries=0,
        )
        context = {
            'objetivo_area': _without_pii(objective_area),
            'lacuna_definida_pelas_regras': competency_gap,
            'competencias_fortes': strong_competencies[:5],
            'tipos_de_missoes_ja_concluidas': completed_mission_types[:10],
            'missao_base': {
                'titulo': base_mission['titulo'],
                'descricao': base_mission['descricao'],
                'area': base_mission['area_relacionada'],
                'dificuldade': base_mission['dificuldade'],
                'duracao_minutos': base_mission['duracao_estimada_minutos'],
            },
        }
        response = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-5.6-luna'),
            response_format={'type': 'json_object'},
            max_completion_tokens=300,
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'Você personaliza missões educacionais. Responda somente JSON válido com as chaves '
                        'titulo, descricao, estimativa_tempo, competencia_alvo. '
                        'A competência alvo deve ser exatamente a lacuna fornecida. '
                        'Use linguagem de convite, como "uma proposta que pode ajudar". '
                        'Nunca use obrigação, diagnóstico definitivo, nome, e-mail ou dado pessoal.'
                    ),
                },
                {'role': 'user', 'content': json.dumps(context, ensure_ascii=False)},
            ],
        )
        content = response.choices[0].message.content or '{}'
        result = json.loads(content)
        if result.get('competencia_alvo') != competency_gap:
            result['competencia_alvo'] = competency_gap
        result['titulo'] = str(result.get('titulo') or fallback['titulo'])[:255]
        result['descricao'] = str(result.get('descricao') or fallback['descricao'])[:2000]
        result['estimativa_tempo'] = max(20, min(240, int(result.get('estimativa_tempo') or fallback['estimativa_tempo'])))
        result['origem_geracao'] = 'regra+ia'
        cache.set(cache_key, result, AI_CACHE_SECONDS)
        return result
    except Exception:
        logger.warning('Personalização de missão indisponível; usando catálogo de regras.', exc_info=True)
        cache.set('mission-ai:circuit:open', '1', AI_CIRCUIT_SECONDS)
        cache.set(cache_key, fallback, AI_FALLBACK_CACHE_SECONDS)
        return fallback
