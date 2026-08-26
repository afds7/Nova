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


def _bounded_timeout() -> float:
    try:
        configured = float(os.getenv('OPENAI_RECOMMENDATIONS_TIMEOUT_SECONDS', '2'))
    except (TypeError, ValueError):
        configured = 2.0
    return min(max(configured, 0.5), 2.0)

TIPOS = {'curso', 'faculdade', 'livro', 'certificacao', 'recurso'}


def _opcoes_por_area(area: str, tipo: str) -> list[str]:
    """Oferece pontos de partida concretos mesmo quando a IA está indisponível."""
    normalized = area.lower()
    if tipo == 'faculdade' and 'direito' in normalized:
        return ['USP', 'São Judas', 'Estácio']
    if tipo == 'faculdade' and any(term in normalized for term in ('tecnologia', 'informação', 'computação', 'software')):
        return ['USP', 'Mackenzie', 'FIAP']
    if tipo == 'faculdade' and any(term in normalized for term in ('engenharia', 'biologia', 'saúde')):
        return ['USP', 'UNESP', 'PUC']
    if tipo == 'faculdade':
        return ['Universidade pública da sua região', 'São Judas', 'Estácio']
    if tipo == 'curso':
        return ['Escola Virtual Fundação Bradesco', 'Coursera', 'edX']
    if tipo == 'livro':
        return ['Biblioteca pública ou universitária', 'e-book', 'livraria']
    return []


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
                'custo': 'gratuito',
                'alcance': 'nacional',
                'modalidade': 'online',
                'o_que_fazer': f'Liste graduações de {area} e compare a grade curricular antes de escolher.',
                'como_fazer': 'Separe duas opções públicas, duas privadas e confira duração, modalidade, bolsas e reconhecimento no e-MEC.',
                'opcoes': _opcoes_por_area(area, 'faculdade'),
            },
            {
                'tipo': 'curso',
                'titulo': f'Cursos introdutórios de {area}',
                'descricao': 'Explore aulas curtas antes de investir em uma formação mais longa.',
                'por_que_pode_fazer_sentido': f'Pode ser um teste prático para entender se {area} combina com seus próximos passos.',
                'url': f'https://www.coursera.org/search?query={area_query}',
                'nivel': 'inicial',
                'estimativa_tempo': '2 a 6 semanas',
                'custo': 'gratuito e pago',
                'alcance': 'internacional',
                'modalidade': 'online',
                'o_que_fazer': f'Teste os fundamentos de {area} em uma trilha curta.',
                'como_fazer': 'Faça a primeira aula, reserve dois blocos de estudo na semana e registre se a prática despertou interesse.',
                'opcoes': _opcoes_por_area(area, 'curso'),
            },
            {
                'tipo': 'livro',
                'titulo': 'Designing Your Life',
                'descricao': 'Livro sobre experimentação de caminhos profissionais e tomada de decisão.',
                'por_que_pode_fazer_sentido': f'Pode apoiar sua reflexão sobre como desenvolver {competencia} enquanto testa possibilidades.',
                'url': 'https://designingyour.life/',
                'nivel': 'todos',
                'estimativa_tempo': 'Leitura gradual',
                'custo': 'pago',
                'alcance': 'internacional',
                'modalidade': 'livro',
                'o_que_fazer': 'Use a leitura para organizar perguntas sobre sua escolha profissional.',
                'como_fazer': 'Leia um capítulo por semana e anote uma ideia que pode ser testada em uma experiência prática.',
                'opcoes': _opcoes_por_area(area, 'livro'),
            },
            {
                'tipo': 'curso',
                'titulo': f'Escolas e cursos técnicos públicos em {area}',
                'descricao': 'Consulte opções gratuitas de institutos federais, escolas técnicas e programas de extensão.',
                'por_que_pode_fazer_sentido': 'Pode oferecer uma entrada acessível e prática na área antes de um investimento maior.',
                'url': 'https://www.gov.br/mec/pt-br',
                'nivel': 'inicial',
                'estimativa_tempo': 'Compare inscrições e editais',
                'custo': 'gratuito',
                'alcance': 'nacional',
                'modalidade': 'presencial ou online',
                'o_que_fazer': f'Procure uma porta de entrada gratuita em {area}.',
                'como_fazer': 'Pesquise editais, pré-requisitos e datas de inscrição em institutos federais e escolas técnicas da sua região.',
                'opcoes': ['Institutos Federais', 'Escolas Técnicas Estaduais', 'Fundação Bradesco'],
            },
            {
                'tipo': 'faculdade',
                'titulo': f'Universidades e bolsas para {area}',
                'descricao': 'Pesquise bolsas, financiamentos e universidades públicas ou privadas reconhecidas.',
                'por_que_pode_fazer_sentido': 'Amplia as opções de formação sem presumir um único orçamento ou modalidade.',
                'url': 'https://acessounico.mec.gov.br/',
                'nivel': 'formacao',
                'estimativa_tempo': 'Pesquisa de médio prazo',
                'custo': 'gratuito, bolsa ou pago',
                'alcance': 'nacional',
                'modalidade': 'presencial ou online',
                'o_que_fazer': 'Compare caminhos de graduação que cabem no seu momento e orçamento.',
                'como_fazer': 'Monte uma tabela com mensalidade, bolsas, financiamento, nota do curso, turno e distância.',
                'opcoes': _opcoes_por_area(area, 'faculdade'),
            },
            {
                'tipo': 'curso',
                'titulo': f'Escola Virtual da Fundação Bradesco: trilhas de {area}',
                'descricao': 'Cursos online gratuitos para testar fundamentos e criar uma rotina de estudos.',
                'por_que_pode_fazer_sentido': 'É uma forma acessível de experimentar a área antes de investir em uma formação paga.',
                'url': 'https://www.ev.org.br/areas-de-interesse',
                'nivel': 'inicial',
                'estimativa_tempo': 'Algumas horas por curso',
                'custo': 'gratuito',
                'alcance': 'nacional',
                'modalidade': 'online',
                'o_que_fazer': f'Faça uma trilha gratuita de fundamentos em {area}.',
                'como_fazer': 'Conclua um curso curto e guarde o certificado ou o projeto final como evidência.',
                'opcoes': ['Escola Virtual Fundação Bradesco', 'Khan Academy', 'SENAI'],
            },
            {
                'tipo': 'curso',
                'titulo': f'Coursera e edX: especializações em {area}',
                'descricao': 'Catálogos internacionais com cursos gratuitos para assistir e trilhas pagas com certificado.',
                'por_que_pode_fazer_sentido': 'Permite comparar professores, ementas e certificados em uma plataforma internacional.',
                'url': f'https://www.edx.org/search?q={area_query}',
                'nivel': 'inicial a avancado',
                'estimativa_tempo': '4 a 12 semanas',
                'custo': 'gratuito ou pago',
                'alcance': 'internacional',
                'modalidade': 'online',
                'o_que_fazer': f'Compare uma formação internacional em {area}.',
                'como_fazer': 'Assista ao conteúdo aberto, verifique idioma e certificado e só depois avalie pagar pela trilha completa.',
                'opcoes': ['Coursera', 'edX', 'FutureLearn'],
            },
            {
                'tipo': 'livro',
                'titulo': 'So Good They Can\'t Ignore You, de Cal Newport',
                'descricao': 'Livro sobre construção de habilidades e escolhas profissionais com mais critério.',
                'por_que_pode_fazer_sentido': f'Pode ajudar a transformar {competencia} em uma habilidade demonstrável.',
                'url': 'https://calnewport.com/books/so-good-they-cant-ignore-you/',
                'nivel': 'todos',
                'estimativa_tempo': 'Leitura gradual',
                'custo': 'pago',
                'alcance': 'internacional',
                'modalidade': 'livro',
                'o_que_fazer': 'Leia sobre construção de habilidades antes de decidir por uma especialização.',
                'como_fazer': 'Escolha uma ideia do livro e transforme-a em um pequeno teste de carreira nesta semana.',
                'opcoes': ['Biblioteca pública ou universitária', 'e-book', 'livraria'],
            },
            {
                'tipo': 'certificacao',
                'titulo': f'Certificações introdutórias para {area}',
                'descricao': 'Compare certificações de empresas e associações reconhecidas antes de escolher uma prova.',
                'por_que_pode_fazer_sentido': 'Pode criar um sinal objetivo de estudo, desde que acompanhado de projeto ou prática real.',
                'url': f'https://www.coursera.org/search?query={area_query}',
                'nivel': 'intermediario',
                'estimativa_tempo': '1 a 4 meses',
                'custo': 'gratuito ou pago',
                'alcance': 'nacional e internacional',
                'modalidade': 'online',
                'o_que_fazer': f'Identifique uma certificação inicial útil para {area}.',
                'como_fazer': 'Compare o conteúdo da prova, o custo total e a aceitação no mercado; combine a certificação com um projeto.',
                'opcoes': ['Certificações de empresas da área', 'Coursera', 'Escolas profissionais nacionais'],
            },
            {
                'tipo': 'recurso',
                'titulo': 'Plano de teste em 7 dias',
                'descricao': f'Escolha uma tarefa pequena ligada a {area} e registre o que aprendeu.',
                'por_que_pode_fazer_sentido': 'Uma experiência curta gera evidência antes de uma decisão maior.',
                'url': '',
                'nivel': 'pratica',
                'estimativa_tempo': 'Até 7 dias',
                'custo': 'gratuito',
                'alcance': 'qualquer',
                'modalidade': 'autoguiado',
                'o_que_fazer': f'Teste uma atividade pequena ligada a {area}.',
                'como_fazer': 'Defina uma entrega simples, reserve até cinco dias úteis e registre o que aprendeu para comparar com outras opções.',
                'opcoes': ['Projeto autoral', 'Conversa com alguém da área', 'Observação de uma aula aberta'],
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
    for item in raw[:12]:
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
            'custo': str(item.get('custo', 'não informado'))[:60],
            'alcance': str(item.get('alcance', 'não informado'))[:40],
            'modalidade': str(item.get('modalidade', 'não informado'))[:80],
            'o_que_fazer': str(item.get('o_que_fazer', item.get('descricao', ''))).strip()[:500],
            'como_fazer': str(item.get('como_fazer', 'Pesquise a opção, compare alternativas e faça um primeiro teste antes de decidir.')).strip()[:500],
            'opcoes': [str(option)[:160] for option in item.get('opcoes', []) if str(option).strip()][:5] if isinstance(item.get('opcoes', []), list) else [],
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
            timeout=_bounded_timeout(),
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
                        'Monte uma lista equilibrada: inclua alternativas gratuitas, de baixo custo e pagas; '
                        'opções nacionais e internacionais; modalidades online e presenciais quando fizer sentido. '
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
                            'itens': 'array com 8 a 12 objetos variados',
                            'proximos_passos': 'array com 2 a 3 strings',
                            'item': ['tipo', 'titulo', 'descricao', 'o_que_fazer', 'como_fazer', 'opcoes', 'por_que_pode_fazer_sentido', 'url', 'nivel', 'estimativa_tempo', 'custo', 'alcance', 'modalidade'],
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
