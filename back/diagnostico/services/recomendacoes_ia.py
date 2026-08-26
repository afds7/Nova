"""Gera uma trilha de estudos personalizada sem enviar dados pessoais à IA."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any
from urllib.parse import quote_plus

from django.core.cache import cache
from openai import OpenAI

logger = logging.getLogger(__name__)

TIPOS = {'curso', 'faculdade', 'livro', 'certificacao', 'recurso'}


def _cache_key(context: dict[str, Any]) -> str:
    digest = hashlib.sha256(
        json.dumps(context, ensure_ascii=False, sort_keys=True).encode('utf-8')
    ).hexdigest()
    return f'nova:recommendations:v1:{digest}'


def _fallback(context: dict[str, Any]) -> dict[str, Any]:
    area = context['area'] or 'sua área de interesse'
    competencia = context['prioridade'] or 'a competência que você quer fortalecer'
    area_query = quote_plus(area)
    return {
        'origem': 'fallback',
        'resumo': (
            f'Alguns caminhos que podem ajudar a explorar {area}. '
            'Use esta lista como ponto de partida e escolha o que combina com seu momento.'
        ),
        'itens': [
            {
                'tipo': 'faculdade',
                'titulo': f'Graduações relacionadas a {area}',
                'descricao': 'Compare cursos, modalidades e instituições no cadastro oficial do MEC.',
                'por_que_pode_fazer_sentido': f'Pode ajudar a conectar seu interesse em {area} com uma formação estruturada.',
                'url': 'https://emec.mec.gov.br/',
                'nivel': 'exploracao',
                'estimativa_tempo': 'Compare 2 ou 3 opções',
            },
            {
                'tipo': 'curso',
                'titulo': f'Cursos introdutórios de {area}',
                'descricao': 'Explore aulas curtas antes de investir em uma formação mais longa.',
                'por_que_pode_fazer_sentido': f'Pode ser um teste prático para entender se {area} combina com seus próximos passos.',
                'url': f'https://www.coursera.org/search?query={area_query}',
                'nivel': 'inicial',
                'estimativa_tempo': '2 a 6 semanas',
            },
            {
                'tipo': 'livro',
                'titulo': 'Designing Your Life',
                'descricao': 'Livro sobre experimentação de caminhos profissionais e tomada de decisão.',
                'por_que_pode_fazer_sentido': f'Pode apoiar sua reflexão sobre como desenvolver {competencia} enquanto testa possibilidades.',
                'url': 'https://designingyour.life/',
                'nivel': 'todos',
                'estimativa_tempo': 'Leitura gradual',
            },
            {
                'tipo': 'recurso',
                'titulo': 'Plano de teste em 7 dias',
                'descricao': f'Escolha uma tarefa pequena ligada a {area} e registre o que aprendeu.',
                'por_que_pode_fazer_sentido': 'Uma experiência curta gera evidência antes de uma decisão maior.',
                'url': '',
                'nivel': 'pratica',
                'estimativa_tempo': 'Até 7 dias',
            },
        ],
        'proximos_passos': [
            f'Escolha um item de {area} para explorar nesta semana.',
            'Anote o que despertou interesse e o que não funcionou.',
            'Revise a lista depois de uma nova experiência prática.',
        ],
    }


def _normalizar_itens(raw: Any, fallback: dict[str, Any]) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return fallback['itens']
    itens: list[dict[str, str]] = []
    for item in raw[:8]:
        if not isinstance(item, dict):
            continue
        tipo = str(item.get('tipo', 'recurso')).lower().strip()
        if tipo not in TIPOS or not str(item.get('titulo', '')).strip():
            continue
        itens.append({
            'tipo': tipo,
            'titulo': str(item['titulo'])[:180],
            'descricao': str(item.get('descricao', ''))[:500],
            'por_que_pode_fazer_sentido': str(item.get('por_que_pode_fazer_sentido', ''))[:500],
            'url': str(item.get('url', ''))[:1000],
            'nivel': str(item.get('nivel', 'todos'))[:40],
            'estimativa_tempo': str(item.get('estimativa_tempo', ''))[:80],
        })
    return itens or fallback['itens']


def gerar_recomendacoes(context: dict[str, Any]) -> dict[str, Any]:
    """Retorna recomendações estruturadas; falha externa nunca bloqueia o diagnóstico."""
    safe_context = {
        'area': str(context.get('area', '')).strip()[:255],
        'prioridade': str(context.get('prioridade', '')).strip()[:120],
        'pontos_fortes': sorted(str(value)[:120] for value in context.get('pontos_fortes', [])),
        'nivel_iep': int(context.get('nivel_iep') or 0),
    }
    key = _cache_key(safe_context)
    cached = cache.get(key)
    if cached:
        return cached

    fallback = _fallback(safe_context)
    try:
        client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            timeout=float(os.getenv('OPENAI_RECOMMENDATIONS_TIMEOUT_SECONDS', '3')),
            max_retries=0,
        )
        response = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-5.6-luna'),
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'Você é um orientador de possibilidades de formação. '
                        'Responda somente JSON válido. Nunca trate uma sugestão como obrigação ou diagnóstico. '
                        'Indique cursos, faculdades, livros, certificações e recursos que possam ser explorados. '
                        'Priorize links oficiais ou páginas de busca confiáveis e não invente URLs específicas.'
                    ),
                },
                {
                    'role': 'user',
                    'content': json.dumps({
                        'area_de_interesse': safe_context['area'],
                        'competencia_prioritaria': safe_context['prioridade'],
                        'competencias_fortes': safe_context['pontos_fortes'],
                        'iep_atual': safe_context['nivel_iep'],
                        'formato_obrigatorio': {
                            'resumo': 'string',
                            'itens': 'array com 4 a 8 objetos',
                            'proximos_passos': 'array com 2 a 3 strings',
                            'item': ['tipo', 'titulo', 'descricao', 'por_que_pode_fazer_sentido', 'url', 'nivel', 'estimativa_tempo'],
                        },
                    }, ensure_ascii=False),
                },
            ],
            max_completion_tokens=1400,
        )
        parsed = json.loads(response.choices[0].message.content or '{}')
        raw_steps = parsed.get('proximos_passos', fallback['proximos_passos'])
        steps = raw_steps if isinstance(raw_steps, list) else fallback['proximos_passos']
        result = {
            'origem': 'ia',
            'resumo': str(parsed.get('resumo', fallback['resumo']))[:700],
            'itens': _normalizar_itens(parsed.get('itens'), fallback),
            'proximos_passos': [str(item)[:300] for item in steps[:3]],
        }
    except Exception as error:
        logger.warning('Recomendações indisponíveis; usando fallback: %s', error)
        result = fallback

    cache.set(key, result, 30 * 60)
    return result
