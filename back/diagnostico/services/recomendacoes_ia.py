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
from tavily import TavilyClient

logger = logging.getLogger(__name__)


def _bounded_timeout() -> float:
    try:
        configured = float(os.getenv('OPENAI_RECOMMENDATIONS_TIMEOUT_SECONDS', '8'))
    except (TypeError, ValueError):
        configured = 8.0
    return min(max(configured, 1.0), 8.0)

TIPOS = {'curso', 'faculdade', 'livro', 'certificacao', 'recurso'}

# Instituições prioritárias para as recomendações de graduação. A IA deve
# validar a oferta do curso nas fontes consultadas antes de sugerir uma opção.
FACULDADES_PRIORITARIAS = [
    {'nome': 'USP', 'categoria': 'pública estadual', 'local': 'São Paulo/SP', 'url': 'https://www5.usp.br'},
    {'nome': 'Unicamp', 'categoria': 'pública estadual', 'local': 'Campinas/SP', 'url': 'https://www.unicamp.br'},
    {'nome': 'Unesp', 'categoria': 'pública estadual', 'local': 'São Paulo e interior/SP', 'url': 'https://www2.unesp.br'},
    {'nome': 'Fatec', 'categoria': 'pública estadual', 'local': 'São Paulo e interior/SP', 'url': 'https://www.fatecsp.br'},
    {'nome': 'Univesp', 'categoria': 'pública estadual', 'local': 'São Paulo/SP', 'url': 'https://www.univesp.br'},
    {'nome': 'UFSCar', 'categoria': 'pública federal', 'local': 'São Carlos/SP', 'url': 'https://www.ufscar.br'},
    {'nome': 'Unifesp', 'categoria': 'pública federal', 'local': 'São Paulo/SP', 'url': 'https://www.unifesp.br'},
    {'nome': 'UFABC', 'categoria': 'pública federal', 'local': 'Santo André/Diadema/SP', 'url': 'https://www.ufabc.edu.br'},
    {'nome': 'UNIFESSPA', 'categoria': 'pública federal', 'local': 'Marabá/PA', 'url': 'https://www.unifesspa.edu.br'},
    {'nome': 'FEMA', 'categoria': 'privada', 'local': 'Assis/SP', 'url': 'https://www.fema.edu.br'},
    {'nome': 'PUC-SP', 'categoria': 'privada', 'local': 'São Paulo/SP', 'url': 'https://www.pucsp.br'},
    {'nome': 'PUC-Campinas', 'categoria': 'privada', 'local': 'Campinas/SP', 'url': 'https://www.puc-campinas.edu.br'},
    {'nome': 'Mackenzie', 'categoria': 'privada', 'local': 'São Paulo/SP', 'url': 'https://www.mackenzie.br'},
    {'nome': 'FGV-SP', 'categoria': 'privada', 'local': 'São Paulo/SP', 'url': 'https://www.fgv.br'},
    {'nome': 'Insper', 'categoria': 'privada', 'local': 'São Paulo/SP', 'url': 'https://www.insper.edu.br'},
    {'nome': 'FIAP', 'categoria': 'privada', 'local': 'São Paulo/SP', 'url': 'https://www.fiap.com.br'},
    {'nome': 'Anhembi Morumbi', 'categoria': 'privada', 'local': 'São Paulo/SP', 'url': 'https://portal.anhembi.br'},
    {'nome': 'UNIP', 'categoria': 'privada', 'local': 'Brasil', 'url': 'https://www.unip.br'},
    {'nome': 'Cruzeiro do Sul', 'categoria': 'privada', 'local': 'São Paulo/SP', 'url': 'https://www.cruzeirodosul.edu.br'},
    {'nome': 'UMC', 'categoria': 'privada', 'local': 'Mogi das Cruzes/SP', 'url': 'https://www.umc.br'},
    {'nome': 'São Judas', 'categoria': 'privada', 'local': 'São Paulo/SP', 'url': 'https://www.saojudas.br'},
    {'nome': 'Uninove', 'categoria': 'privada', 'local': 'São Paulo/SP', 'url': 'https://www.uninove.br'},
    {'nome': 'Belas Artes', 'categoria': 'privada', 'local': 'São Paulo/SP', 'url': 'https://www.belasartes.br'},
    {'nome': 'ESPM', 'categoria': 'privada', 'local': 'São Paulo/SP', 'url': 'https://www.espm.br'},
    {'nome': 'Ibmec SP', 'categoria': 'privada', 'local': 'São Paulo/SP', 'url': 'https://www.ibmec.br'},
    {'nome': 'MIT', 'categoria': 'internacional privada', 'local': 'Massachusetts/EUA', 'url': 'https://www.mit.edu'},
    {'nome': 'Harvard', 'categoria': 'internacional privada', 'local': 'Massachusetts/EUA', 'url': 'https://www.harvard.edu'},
    {'nome': 'Stanford', 'categoria': 'internacional privada', 'local': 'Califórnia/EUA', 'url': 'https://www.stanford.edu'},
    {'nome': 'UC Berkeley', 'categoria': 'internacional pública', 'local': 'Califórnia/EUA', 'url': 'https://www.berkeley.edu'},
    {'nome': 'Oxford', 'categoria': 'internacional pública', 'local': 'Oxford/Reino Unido', 'url': 'https://www.ox.ac.uk'},
    {'nome': 'Cambridge', 'categoria': 'internacional pública', 'local': 'Cambridge/Reino Unido', 'url': 'https://www.cam.ac.uk'},
    {'nome': 'ETH Zürich', 'categoria': 'internacional pública', 'local': 'Zurique/Suíça', 'url': 'https://ethz.ch'},
    {'nome': 'Universidade de Toronto', 'categoria': 'internacional pública', 'local': 'Toronto/Canadá', 'url': 'https://www.utoronto.ca'},
    {'nome': 'Universidade de Melbourne', 'categoria': 'internacional pública', 'local': 'Melbourne/Austrália', 'url': 'https://www.unimelb.edu.au'},
    {'nome': 'Sorbonne', 'categoria': 'internacional pública', 'local': 'Paris/França', 'url': 'https://www.sorbonne-universite.fr'},
    {'nome': 'Universidad de Buenos Aires', 'categoria': 'internacional pública', 'local': 'Buenos Aires/Argentina', 'url': 'https://www.uba.ar'},
    {'nome': 'UNAM', 'categoria': 'internacional pública', 'local': 'Cidade do México/México', 'url': 'https://www.unam.mx'},
    {'nome': 'Universidade de Lisboa', 'categoria': 'internacional pública', 'local': 'Lisboa/Portugal', 'url': 'https://www.ulisboa.pt'},
    {'nome': 'Universidade do Porto', 'categoria': 'internacional pública', 'local': 'Porto/Portugal', 'url': 'https://www.up.pt'},
    {'nome': 'Yale', 'categoria': 'internacional privada', 'local': 'Connecticut/EUA', 'url': 'https://www.yale.edu'},
    {'nome': 'Princeton', 'categoria': 'internacional privada', 'local': 'Nova Jersey/EUA', 'url': 'https://www.princeton.edu'},
    {'nome': 'Columbia', 'categoria': 'internacional privada', 'local': 'Nova York/EUA', 'url': 'https://www.columbia.edu'},
    {'nome': 'NYU', 'categoria': 'internacional privada', 'local': 'Nova York/EUA', 'url': 'https://www.nyu.edu'},
    {'nome': 'Caltech', 'categoria': 'internacional privada', 'local': 'Califórnia/EUA', 'url': 'https://www.caltech.edu'},
    {'nome': 'Imperial College London', 'categoria': 'internacional privada', 'local': 'Londres/Reino Unido', 'url': 'https://www.imperial.ac.uk'},
]

CURSOS_PRIORITARIOS = [
    {'nome': 'Coursera', 'perfil': 'internacional, cursos gratuitos e pagos', 'url': 'https://www.coursera.org'},
    {'nome': 'edX', 'perfil': 'internacional, cursos gratuitos e pagos', 'url': 'https://www.edx.org'},
    {'nome': 'Khan Academy', 'perfil': 'gratuito', 'url': 'https://www.khanacademy.org'},
    {'nome': 'FGV Online', 'perfil': 'gratuito', 'url': 'https://educacao-executiva.fgv.br/cursos-online-gratuitos'},
    {'nome': 'Fundação Bradesco', 'perfil': 'gratuito e com certificado', 'url': 'https://www.ev.org.br'},
    {'nome': 'SENAI', 'perfil': 'nacional, cursos gratuitos e pagos', 'url': 'https://www.senai.br'},
    {'nome': 'Sebrae', 'perfil': 'gratuito e voltado a negócios', 'url': 'https://sebrae.com.br/sites/PortalSebrae/cursosonline'},
    {'nome': 'Google Actívate / Grow with Google', 'perfil': 'gratuito', 'url': 'https://learndigital.withgoogle.com/digitalgarage'},
    {'nome': 'Alura', 'perfil': 'pago, com trilhas gratuitas', 'url': 'https://www.alura.com.br'},
    {'nome': 'freeCodeCamp', 'perfil': 'gratuito', 'url': 'https://www.freecodecamp.org'},
    {'nome': 'Udemy', 'perfil': 'cursos gratuitos e pagos', 'url': 'https://www.udemy.com/courses/free'},
    {'nome': 'Class Central', 'perfil': 'busca cursos gratuitos de universidades', 'url': 'https://www.classcentral.com'},
    {'nome': 'Fundação Estudar', 'perfil': 'gratuito', 'url': 'https://fundacaoestudar.org.br'},
    {'nome': 'Politize!', 'perfil': 'gratuito', 'url': 'https://www.politize.com.br'},
    {'nome': 'Escola Virtual FGV', 'perfil': 'gratuito e com certificado', 'url': 'https://educacao-executiva.fgv.br'},
    {'nome': 'Microsoft Learn', 'perfil': 'gratuito', 'url': 'https://learn.microsoft.com'},
    {'nome': 'AWS Skill Builder', 'perfil': 'trilhas gratuitas e pagas', 'url': 'https://explore.skillbuilder.aws'},
    {'nome': 'Univesp', 'perfil': 'nacional, cursos livres gratuitos', 'url': 'https://www.univesp.br'},
    {'nome': 'USP for the world', 'perfil': 'cursos em português na Coursera', 'url': 'https://www.coursera.org/usp'},
    {'nome': 'MIT OpenCourseWare', 'perfil': 'internacional e gratuito', 'url': 'https://ocw.mit.edu'},
    {'nome': 'Harvard Online', 'perfil': 'internacional, opções gratuitas e pagas', 'url': 'https://pll.harvard.edu'},
    {'nome': 'Stanford Online', 'perfil': 'internacional, opções gratuitas e pagas', 'url': 'https://online.stanford.edu'},
    {'nome': 'Open Yale Courses', 'perfil': 'internacional e gratuito', 'url': 'https://oyc.yale.edu'},
    {'nome': 'FutureLearn', 'perfil': 'internacional, opções gratuitas e pagas', 'url': 'https://www.futurelearn.com'},
    {'nome': 'Alison', 'perfil': 'internacional, cursos gratuitos e pagos', 'url': 'https://alison.com'},
    {'nome': 'OpenLearn', 'perfil': 'internacional e gratuito', 'url': 'https://www.open.edu/openlearn'},
    {'nome': 'Codecademy', 'perfil': 'internacional, parte gratuita', 'url': 'https://www.codecademy.com'},
    {'nome': 'Udacity', 'perfil': 'internacional, cursos livres e pagos', 'url': 'https://www.udacity.com'},
    {'nome': 'Duolingo', 'perfil': 'internacional, idiomas com opção gratuita', 'url': 'https://www.duolingo.com'},
    {'nome': 'IBM SkillsBuild', 'perfil': 'internacional e gratuito', 'url': 'https://skillsbuild.org'},
    {'nome': 'Cisco Networking Academy', 'perfil': 'internacional, opções gratuitas e pagas', 'url': 'https://www.netacad.com'},
]


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
        return ['USP', 'Unicamp', 'Unesp', 'São Judas', 'PUC-SP', 'UNIP']
    if tipo == 'curso':
        return ['Coursera', 'edX', 'Fundação Bradesco', 'FGV Online', 'SENAI', 'Sebrae']
    if tipo == 'livro':
        return ['Biblioteca pública ou universitária', 'e-book', 'livraria']
    return []


def _cache_key(context: dict[str, Any]) -> str:
    digest = hashlib.sha256(
        json.dumps(context, ensure_ascii=False, sort_keys=True).encode('utf-8')
    ).hexdigest()
    # v2 invalida respostas genéricas que foram guardadas antes da curadoria específica.
    # v6 invalida respostas anteriores ao catálogo prioritário de faculdades.
    return f'nova:recommendations:v9:{digest}'


def _buscar_fontes(context: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    """Busca fontes antes da IA; não envia nome, e-mail ou identificadores pessoais."""
    api_key = os.getenv('TAVILY_API_KEY', '').strip()
    if not api_key:
        raise RuntimeError('TAVILY_API_KEY não configurada')

    area = context['area'] or 'a área escolhida'
    perfil_hint = context['perfil_hint'] or context['prioridade'] or 'interesses profissionais'
    queries = {
        'faculdades': [
            f'{area} faculdade universidade pública privada presencial EAD {perfil_hint}',
            f'{area} faculdade nota de corte 2026 bolsas financiamento fora de São Paulo e Rio de Janeiro',
        ],
        'livros': [
            f'melhores livros introdutórios e avançados para começar em {area}',
            f'livros {area} recomendados por profissionais {perfil_hint}',
            f'livros de {area} fundamentos prática carreira biografia leitura acessível recomendados',
        ],
        'cursos': [
            f'curso gratuito {area} certificado 2026',
            f'curso online {perfil_hint} relacionado a {area} gratuito pago',
        ],
        'comunidades': [
            f'comunidade {area} Brasil fórum discord associação profissional',
            f'eventos estudantes profissionais {area} Brasil 2026',
        ],
    }
    client = TavilyClient(api_key=api_key)
    sources: dict[str, list[dict[str, str]]] = {}
    for category, category_queries in queries.items():
        category_results: list[dict[str, str]] = []
        for query in category_queries:
            response = client.search(query=query, search_depth='basic', max_results=4)
            for result in response.get('results', []):
                if result.get('url') and result.get('title'):
                    category_results.append({
                        'titulo': str(result['title'])[:220],
                        'url': str(result['url'])[:1000],
                        'trecho': str(result.get('content', ''))[:500],
                    })
        sources[category] = category_results
    return sources


def _itens_especificos(area: str, competencia: str) -> list[dict[str, Any]]:
    """Fallback editorial com nomes reais para áreas frequentes do diagnóstico."""
    normalized = area.lower()
    if 'psicologia' in normalized:
        return [
            {'tipo': 'faculdade', 'titulo': 'Psicologia — Universidade de São Paulo (USP)', 'descricao': 'Graduação presencial com formação em pesquisa, avaliação psicológica e diferentes campos de atuação.', 'o_que_fazer': 'Compare a matriz curricular e as formas de ingresso da USP para Psicologia.', 'como_fazer': 'Acesse a FUVEST e o SiSU, confira calendário, nota de corte e os documentos exigidos.', 'opcoes': ['USP', 'FUVEST', 'SiSU'], 'por_que_pode_fazer_sentido': 'Pode fazer sentido se você busca uma formação acadêmica forte e contato com pesquisa.', 'url': 'https://www.fuvest.br/', 'nivel': 'graduação', 'estimativa_tempo': '5 anos', 'custo': 'pública', 'alcance': 'nacional', 'modalidade': 'presencial'},
            {'tipo': 'faculdade', 'titulo': 'Psicologia — Pontifícia Universidade Católica de São Paulo (PUC-SP)', 'descricao': 'Graduação privada com tradição em Psicologia e possibilidades de atuação clínica, social e organizacional.', 'o_que_fazer': 'Avalie a grade da PUC-SP e as condições de bolsa ou financiamento.', 'como_fazer': 'Consulte o vestibular, compare mensalidade, turno, estágios e linhas de formação.', 'opcoes': ['PUC-SP', 'ProUni', 'FIES'], 'por_que_pode_fazer_sentido': 'É uma alternativa privada para quem quer comparar percursos formativos e oportunidades de estágio.', 'url': 'https://www.pucsp.br/graduacao/psicologia', 'nivel': 'graduação', 'estimativa_tempo': '5 anos', 'custo': 'paga, com bolsas', 'alcance': 'nacional', 'modalidade': 'presencial'},
            {'tipo': 'faculdade', 'titulo': 'Psicologia — Universidade Federal da Bahia (UFBA)', 'descricao': 'Opção pública fora do eixo Rio-São Paulo, com formação universitária e acesso a projetos de extensão.', 'o_que_fazer': 'Verifique o curso de Psicologia da UFBA e as formas de ingresso pelo ENEM.', 'como_fazer': 'Acompanhe o portal de ingresso da UFBA e o SiSU; depois procure projetos e estágios da faculdade.', 'opcoes': ['UFBA', 'ENEM', 'SiSU'], 'por_que_pode_fazer_sentido': 'Amplia as opções para quem está no Nordeste ou quer estudar fora do eixo Sudeste.', 'url': 'https://www.ufba.br/', 'nivel': 'graduação', 'estimativa_tempo': '5 anos', 'custo': 'pública', 'alcance': 'nacional', 'modalidade': 'presencial'},
            {'tipo': 'faculdade', 'titulo': 'Psicologia — Universidade Paulista (UNIP)', 'descricao': 'Alternativa privada com campi em diferentes cidades e possibilidade de comparar turnos e unidades.', 'o_que_fazer': 'Compare unidades, turnos e matriz curricular da Psicologia na UNIP.', 'como_fazer': 'Consulte o vestibular, confirme a unidade mais acessível e verifique bolsas disponíveis.', 'opcoes': ['UNIP', 'Vestibular UNIP', 'ProUni'], 'por_que_pode_fazer_sentido': 'Pode ser uma opção para comparar disponibilidade de campus, horário e investimento.', 'url': 'https://www.unip.br/', 'nivel': 'graduação', 'estimativa_tempo': '5 anos', 'custo': 'paga, com bolsas', 'alcance': 'nacional', 'modalidade': 'presencial'},
            {'tipo': 'faculdade', 'titulo': 'Psicologia — Centro Universitário Internacional UNINTER', 'descricao': 'Alternativa privada com oferta de graduação e estrutura voltada a quem precisa de mais flexibilidade.', 'o_que_fazer': 'Confira se a modalidade e o polo da UNINTER atendem à sua rotina.', 'como_fazer': 'Leia a matriz curricular, valide o reconhecimento do curso e compare mensalidade e encontros presenciais.', 'opcoes': ['UNINTER', 'Polo regional', 'ProUni'], 'por_que_pode_fazer_sentido': 'Pode ajudar quem precisa conciliar trabalho, deslocamento e formação.', 'url': 'https://www.uninter.com/graduacao/', 'nivel': 'graduação', 'estimativa_tempo': '5 anos', 'custo': 'paga, com bolsas', 'alcance': 'nacional', 'modalidade': 'flexível'},
            {'tipo': 'livro', 'titulo': 'Introdução à Psicologia — Charles G. Morris e Albert A. Maisto', 'descricao': 'Panorama didático de processos psicológicos, comportamento e principais campos da Psicologia.', 'o_que_fazer': 'Use o livro para identificar quais áreas da Psicologia despertam mais interesse.', 'como_fazer': 'Leia um capítulo por semana e relacione cada conceito a uma situação observável, sem tentar diagnosticar pessoas.', 'opcoes': ['Biblioteca universitária', 'e-book', 'livraria'], 'por_que_pode_fazer_sentido': f'Constrói uma base inicial para explorar {competencia or "as competências do curso"}.', 'url': '', 'nivel': 'introdutório', 'estimativa_tempo': '8 a 12 semanas', 'custo': 'pago ou biblioteca', 'alcance': 'internacional', 'modalidade': 'livro'},
            {'tipo': 'livro', 'titulo': 'Psicologia: Uma Introdução — Linda L. Davidoff', 'descricao': 'Referência introdutória para compreender pesquisa, cognição, desenvolvimento e comportamento.', 'o_que_fazer': 'Monte um mapa dos temas que você gostaria de aprofundar na graduação.', 'como_fazer': 'Escolha três capítulos, faça um resumo de uma página e transforme uma dúvida em pergunta de pesquisa.', 'opcoes': ['Biblioteca pública', 'Biblioteca universitária', 'livraria'], 'por_que_pode_fazer_sentido': 'Ajuda a testar o interesse pela linguagem acadêmica antes da matrícula.', 'url': '', 'nivel': 'didático', 'estimativa_tempo': '6 a 10 semanas', 'custo': 'pago ou biblioteca', 'alcance': 'internacional', 'modalidade': 'livro'},
            {'tipo': 'livro', 'titulo': 'O Homem e Seus Símbolos — Carl G. Jung', 'descricao': 'Leitura mais acessível sobre símbolos, narrativas e interpretação na tradição junguiana.', 'o_que_fazer': 'Leia como uma porta de entrada para conhecer uma abordagem, sem tratá-la como explicação única da Psicologia.', 'como_fazer': 'Anote quais ideias você gostaria de discutir em uma aula introdutória ou grupo de estudos.', 'opcoes': ['Biblioteca', 'e-book', 'livraria'], 'por_que_pode_fazer_sentido': 'Oferece uma leitura menos técnica para experimentar o tipo de reflexão presente na área.', 'url': '', 'nivel': 'leitura leve', 'estimativa_tempo': '4 a 6 semanas', 'custo': 'pago ou biblioteca', 'alcance': 'internacional', 'modalidade': 'livro'},
            {'tipo': 'curso', 'titulo': 'The Science of Well-Being — Yale University', 'descricao': 'Curso aberto na Coursera sobre hábitos, bem-estar e avaliação crítica de evidências.', 'o_que_fazer': 'Faça a trilha para praticar leitura crítica de pesquisas relacionadas a comportamento.', 'como_fazer': 'Assista ao conteúdo gratuito, complete as atividades e avalie o certificado pago apenas se ele for útil para você.', 'opcoes': ['Coursera', 'Yale University', 'Auditar gratuitamente'], 'por_que_pode_fazer_sentido': 'Ajuda a desenvolver uma base de pensamento científico antes da graduação.', 'url': 'https://www.coursera.org/learn/the-science-of-well-being', 'nivel': 'inicial', 'estimativa_tempo': '4 semanas', 'custo': 'gratuito ou certificado pago', 'alcance': 'internacional', 'modalidade': 'online'},
            {'tipo': 'curso', 'titulo': 'Psicologia do Desenvolvimento — Instituto Federal do Rio Grande do Sul', 'descricao': 'Curso aberto para explorar desenvolvimento humano e conceitos usados em Psicologia e Educação.', 'o_que_fazer': 'Use a trilha para experimentar um tema central da formação em Psicologia.', 'como_fazer': 'Inscreva-se, complete as atividades e registre três conceitos que você gostaria de estudar na faculdade.', 'opcoes': ['IFRS', 'Moodle', 'Curso aberto'], 'por_que_pode_fazer_sentido': 'É uma alternativa gratuita e nacional para começar com conteúdo relacionado ao curso.', 'url': 'https://mundi.ifsul.edu.br/portal/', 'nivel': 'inicial', 'estimativa_tempo': '20 horas', 'custo': 'gratuito', 'alcance': 'nacional', 'modalidade': 'online'},
            {'tipo': 'curso', 'titulo': 'Psychological First Aid — Johns Hopkins University', 'descricao': 'Curso da Coursera sobre apoio inicial em situações de crise, sem substituir formação profissional.', 'o_que_fazer': 'Conheça princípios de acolhimento e limites éticos antes de pensar em atuação na área.', 'como_fazer': 'Estude o conteúdo, faça as atividades e não ofereça atendimento psicológico com base apenas no curso.', 'opcoes': ['Coursera', 'Johns Hopkins', 'Auditar gratuitamente'], 'por_que_pode_fazer_sentido': 'Apresenta uma aplicação concreta da Psicologia e reforça a importância da ética e dos limites profissionais.', 'url': 'https://www.coursera.org/learn/psychological-first-aid', 'nivel': 'inicial', 'estimativa_tempo': '5 semanas', 'custo': 'gratuito ou certificado pago', 'alcance': 'internacional', 'modalidade': 'online'},
        ]
    if any(term in normalized for term in ('comunicação social', 'comunicacao social', 'jornalismo', 'publicidade', 'relações públicas', 'relacoes publicas')):
        return [
            {'tipo': 'faculdade', 'titulo': 'Comunicação Social — Escola de Comunicações e Artes da USP (ECA-USP)', 'descricao': 'Formação pública presencial com habilitações e projetos ligados a jornalismo, publicidade, audiovisual e comunicação.', 'o_que_fazer': 'Compare as habilitações da ECA-USP e escolha a que mais se aproxima do tipo de comunicação que você quer praticar.', 'como_fazer': 'Leia a matriz curricular, acompanhe a FUVEST e o SiSU e monte um calendário para estudar e reunir os documentos.', 'opcoes': ['ECA-USP', 'FUVEST', 'SiSU'], 'por_que_pode_fazer_sentido': 'Pode ser uma opção para quem busca formação acadêmica, pesquisa e produção de projetos em comunicação.', 'url': 'https://www.eca.usp.br/', 'nivel': 'graduação', 'estimativa_tempo': '4 anos', 'custo': 'pública', 'alcance': 'nacional', 'modalidade': 'presencial'},
            {'tipo': 'faculdade', 'titulo': 'Comunicação e Multimeios — PUC-SP', 'descricao': 'Graduação privada presencial voltada a produção, linguagem e planejamento de comunicação em diferentes mídias.', 'o_que_fazer': 'Veja a grade de Comunicação e Multimeios e compare os laboratórios, turnos e projetos práticos.', 'como_fazer': 'Consulte o vestibular da PUC-SP, peça informações sobre mensalidade e verifique bolsas, ProUni e condições de matrícula.', 'opcoes': ['PUC-SP', 'Vestibular PUC-SP', 'ProUni'], 'por_que_pode_fazer_sentido': 'É uma alternativa privada para experimentar comunicação digital, audiovisual e projetos multimídia.', 'url': 'https://www.pucsp.br/graduacao', 'nivel': 'graduação', 'estimativa_tempo': '4 anos', 'custo': 'paga, com bolsas', 'alcance': 'nacional', 'modalidade': 'presencial'},
            {'tipo': 'faculdade', 'titulo': 'Comunicação Social — Universidade Federal do Rio Grande do Sul (UFRGS)', 'descricao': 'Opção pública no Sul do país, fora do eixo Rio-São Paulo, com graduação e ambiente de pesquisa em comunicação.', 'o_que_fazer': 'Confira as habilitações e disciplinas da UFRGS que combinam com seu interesse em comunicação.', 'como_fazer': 'Acompanhe o ingresso pelo vestibular e pelo SiSU, confira a nota de corte e compare o custo de morar em Porto Alegre.', 'opcoes': ['UFRGS', 'Vestibular UFRGS', 'SiSU'], 'por_que_pode_fazer_sentido': 'Amplia suas alternativas geográficas e permite comparar uma universidade pública reconhecida fora do Sudeste.', 'url': 'https://www.ufrgs.br/', 'nivel': 'graduação', 'estimativa_tempo': '4 anos', 'custo': 'pública', 'alcance': 'nacional', 'modalidade': 'presencial'},
            {'tipo': 'faculdade', 'titulo': 'Comunicação Social — Universidade Federal de Pernambuco (UFPE)', 'descricao': 'Universidade pública no Nordeste com formação em comunicação e possibilidade de participação em extensão e pesquisa.', 'o_que_fazer': 'Explore a graduação da UFPE e identifique se seu interesse está mais próximo de jornalismo, publicidade ou audiovisual.', 'como_fazer': 'Use o portal de ingresso da UFPE e o SiSU para acompanhar vagas, documentos e chamadas.', 'opcoes': ['UFPE', 'ENEM', 'SiSU'], 'por_que_pode_fazer_sentido': 'É uma opção pública fora do eixo Sudeste para quem quer estudar comunicação no Nordeste.', 'url': 'https://www.ufpe.br/', 'nivel': 'graduação', 'estimativa_tempo': '4 anos', 'custo': 'pública', 'alcance': 'nacional', 'modalidade': 'presencial'},
            {'tipo': 'faculdade', 'titulo': 'Comunicação Social — Estácio', 'descricao': 'Alternativa privada com unidades presenciais e opções digitais, permitindo comparar horários, polos e investimento.', 'o_que_fazer': 'Compare a modalidade, a unidade e a matriz curricular de Comunicação Social antes de escolher.', 'como_fazer': 'Consulte o processo seletivo, confirme o reconhecimento do curso, simule mensalidade e verifique bolsas e descontos.', 'opcoes': ['Estácio', 'Vestibular', 'ProUni'], 'por_que_pode_fazer_sentido': 'Pode atender quem precisa conciliar trabalho, localização e uma modalidade mais flexível.', 'url': 'https://www.estacio.br/', 'nivel': 'graduação', 'estimativa_tempo': '4 anos', 'custo': 'paga, com bolsas', 'alcance': 'nacional', 'modalidade': 'presencial ou EAD'},
            {'tipo': 'livro', 'titulo': 'Teorias da Comunicação de Massa — Mauro Wolf', 'descricao': 'Referência para entender como as teorias analisam mídia, públicos, efeitos e circulação de mensagens.', 'o_que_fazer': 'Use a leitura para montar um mapa das principais teorias que aparecem na graduação.', 'como_fazer': 'Leia um capítulo por semana e aplique cada conceito à análise de uma notícia, campanha ou postagem.', 'opcoes': ['Biblioteca universitária', 'Biblioteca pública', 'livraria'], 'por_que_pode_fazer_sentido': 'Ajuda a construir a base crítica necessária para jornalismo, publicidade e comunicação institucional.', 'url': '', 'nivel': 'referência', 'estimativa_tempo': '8 a 12 semanas', 'custo': 'pago ou biblioteca', 'alcance': 'internacional', 'modalidade': 'livro'},
            {'tipo': 'livro', 'titulo': 'A Reportagem — Nilson Lage', 'descricao': 'Livro didático sobre apuração, construção e linguagem da reportagem jornalística.', 'o_que_fazer': 'Faça uma pequena reportagem local para testar se a apuração jornalística combina com você.', 'como_fazer': 'Escolha um tema, converse com duas fontes, confira os fatos e escreva um texto curto identificando fontes e contexto.', 'opcoes': ['Biblioteca', 'e-book', 'livraria'], 'por_que_pode_fazer_sentido': 'Transforma o interesse em Comunicação Social em uma prática concreta e analisável.', 'url': '', 'nivel': 'didático', 'estimativa_tempo': '4 a 6 semanas', 'custo': 'pago ou biblioteca', 'alcance': 'nacional', 'modalidade': 'livro'},
            {'tipo': 'livro', 'titulo': 'Assessoria de Imprensa e Relacionamento com a Mídia — Jorge Duarte (org.)', 'descricao': 'Obra brasileira sobre planejamento, relacionamento com jornalistas e comunicação institucional.', 'o_que_fazer': 'Compare o trabalho de assessoria com jornalismo e produção de conteúdo para descobrir qual rotina interessa mais.', 'como_fazer': 'Leia os capítulos sobre planejamento e analise a comunicação de uma organização real.', 'opcoes': ['Biblioteca universitária', 'livraria', 'e-book'], 'por_que_pode_fazer_sentido': 'Apresenta uma frente profissional específica para quem se interessa por comunicação organizacional.', 'url': '', 'nivel': 'intermediário', 'estimativa_tempo': '5 a 8 semanas', 'custo': 'pago ou biblioteca', 'alcance': 'nacional', 'modalidade': 'livro'},
            {'tipo': 'curso', 'titulo': 'Fundamentos do Marketing Digital — Google Ateliê Digital', 'descricao': 'Curso online com fundamentos de presença digital, conteúdo, métricas e divulgação.', 'o_que_fazer': 'Complete os módulos e aplique o aprendizado em uma campanha simples para um projeto real ou autoral.', 'como_fazer': 'Faça a trilha gratuita, crie um briefing, publique uma peça e registre o resultado em seu portfólio.', 'opcoes': ['Google Ateliê Digital', 'Curso gratuito', 'Certificado'], 'por_que_pode_fazer_sentido': 'Conecta Comunicação Social a uma prática digital valorizada em publicidade e comunicação institucional.', 'url': 'https://learndigital.withgoogle.com/ateliedigital', 'nivel': 'inicial', 'estimativa_tempo': '40 horas', 'custo': 'gratuito', 'alcance': 'internacional', 'modalidade': 'online'},
            {'tipo': 'curso', 'titulo': 'Introduction to Public Speaking — Coursera, University of Washington', 'descricao': 'Curso internacional sobre estrutura, clareza e apresentação de mensagens para diferentes públicos.', 'o_que_fazer': 'Prepare e grave uma apresentação de três minutos sobre um tema de Comunicação Social.', 'como_fazer': 'Assista às aulas, escreva um roteiro, grave duas versões e compare clareza, tempo e adequação ao público.', 'opcoes': ['Coursera', 'University of Washington', 'Auditar gratuitamente'], 'por_que_pode_fazer_sentido': 'Desenvolve uma habilidade prática para jornalismo, apresentações, relações públicas e produção de conteúdo.', 'url': 'https://www.coursera.org/learn/public-speaking', 'nivel': 'inicial', 'estimativa_tempo': '4 semanas', 'custo': 'gratuito ou certificado pago', 'alcance': 'internacional', 'modalidade': 'online'},
            {'tipo': 'curso', 'titulo': 'Produção de Conteúdo para Mídias Digitais — Escola Virtual Fundação Bradesco', 'descricao': 'Curso nacional online para praticar planejamento, linguagem e produção de conteúdo digital.', 'o_que_fazer': 'Crie um calendário de conteúdo de uma semana para uma organização, projeto ou causa que você conheça.', 'como_fazer': 'Conclua as aulas, planeje três publicações e explique a escolha do público, formato e objetivo de cada uma.', 'opcoes': ['Escola Virtual Fundação Bradesco', 'Curso gratuito', 'Certificado'], 'por_que_pode_fazer_sentido': 'Oferece uma porta de entrada gratuita para praticar comunicação digital no contexto brasileiro.', 'url': 'https://www.ev.org.br/areas-de-interesse', 'nivel': 'inicial', 'estimativa_tempo': '10 a 20 horas', 'custo': 'gratuito', 'alcance': 'nacional', 'modalidade': 'online'},
        ]
    return []


def _fallback(context: dict[str, Any]) -> dict[str, Any]:
    area = context['area'] or 'sua área de interesse'
    competencia = context['prioridade'] or 'a competência que você quer fortalecer'
    area_query = quote_plus(area)
    specific_items = _itens_especificos(area, competencia)
    return {
        'origem': 'fallback',
        'resumo': (
            f'Alguns caminhos que podem ajudar a explorar {area}. '
            'Use esta lista como ponto de partida e escolha o que combina com seu momento.'
        ),
        'itens': specific_items or [
            {
                'tipo': 'faculdade',
                'titulo': f'Faculdades para estudar {area}',
                'descricao': f'Compare a oferta de {area} nas instituições prioritárias do NOVA e confirme a modalidade disponível.',
                'por_que_pode_fazer_sentido': f'Pode ajudar a conectar seu interesse em {area} com uma formação estruturada.',
                'url': 'https://www5.usp.br',
                'nivel': 'exploracao',
                'estimativa_tempo': 'Compare 2 ou 3 opções',
                'custo': 'gratuito',
                'alcance': 'nacional',
                'modalidade': 'online',
                'o_que_fazer': f'Liste graduações de {area} e compare a grade curricular antes de escolher.',
                'como_fazer': f'Abra os sites institucionais, confirme se oferecem {area}, compare duração, modalidade, bolsas e processo seletivo.',
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
                'url': 'https://www.univesp.br',
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
            f'Confirme se {area} é o curso que você quer seguir e anote suas dúvidas principais.',
            f'Compare a grade curricular de três instituições que oferecem {area}.',
            'Verifique formas de ingresso, bolsas, mensalidades e datas no site oficial de cada instituição.',
            'Faça uma experiência introdutória ligada ao curso antes de escolher a instituição.',
            'Separe documentos, faça a inscrição no processo seletivo escolhido e acompanhe o resultado.',
            'Após a aprovação, confirme a matrícula e consulte o calendário de início das aulas.',
        ],
        'comunidades': [
            f'Procure o diretório ou associação profissional relacionada a {area}.',
            'Participe de uma aula aberta, evento ou grupo de estudantes da área.',
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
            # Livros são exibidos apenas com nome e resumo, sem links externos.
            'url': '' if tipo == 'livro' else str(item.get('url', ''))[:1000],
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


def _resposta_ia_esta_detalhada(raw: Any) -> bool:
    """Impede que uma resposta curta/genérica seja exibida como recomendação final."""
    if not isinstance(raw, list):
        return False
    valid = [item for item in raw if isinstance(item, dict) and str(item.get('titulo', '')).strip()]
    types = {str(item.get('tipo', '')).lower().strip() for item in valid}
    required = {'faculdade', 'livro', 'curso'}
    if not required.issubset(types) or len(valid) < 8:
        return False
    return all(
        str(item.get('o_que_fazer', '')).strip()
        and str(item.get('como_fazer', '')).strip()
        and str(item.get('por_que_pode_fazer_sentido', '')).strip()
        for item in valid
    )


def gerar_recomendacoes(context: dict[str, Any]) -> dict[str, Any]:
    """Retorna recomendações estruturadas; falha externa nunca bloqueia o diagnóstico."""
    safe_context = {
        # Usado apenas para isolar o cache entre alunos; nunca entra no prompt.
        'perfil_id': str(context.get('perfil_id', '')).strip()[:80],
        'area': str(context.get('area', '')).strip()[:255],
        'prioridade': str(context.get('prioridade', '')).strip()[:120],
        'perfil_hint': str(context.get('perfil_hint', '')).strip()[:255],
        'pontos_fortes': sorted(str(value)[:120] for value in context.get('pontos_fortes', [])),
        'nivel_iep': int(context.get('nivel_iep') or 0),
    }
    key = _cache_key(safe_context)
    cached = cache.get(key)
    if cached:
        return cached

    fallback = _fallback(safe_context)
    # Mantém a regra de produto também no fallback: livro não possui link.
    fallback['itens'] = [
        {**item, 'url': ''} if item.get('tipo') == 'livro' else item
        for item in fallback['itens']
    ]
    faculdades_prioritarias = [
        f"{item['nome']} — {item['categoria']} — {item['local']} — {item['url']}"
        for item in FACULDADES_PRIORITARIAS
    ]
    cursos_prioritarios = [
        f"{item['nome']} — {item['perfil']} — {item['url']}"
        for item in CURSOS_PRIORITARIOS
    ]
    try:
        fontes = _buscar_fontes(safe_context)
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
                        'Você é Luna, orientadora vocacional. Responda somente JSON válido, sem markdown. '
                        'A pessoa já decidiu seguir a área informada. Use exclusivamente as fontes do Tavily '
                        'fornecidas abaixo para selecionar instituições, livros, cursos e comunidades. '
                        'Não responda com itens de memória nem invente nomes, links ou dados. '
                        'Releia todo o contexto anonimizado do perfil e conecte cada justificativa a um dado específico dele. '
                        'Misture faculdades públicas e privadas, presenciais e EAD, com pelo menos uma fora do eixo Rio-São Paulo. '
                        'Priorize as instituições do catálogo oficial fornecido no contexto quando elas oferecerem o curso escolhido; '
                        'não substitua esse catálogo por e-MEC, gov.br ou um agregador como recomendação principal. '
                        'Misture livro introdutório, técnico/avançado e leitura ligada ao interesse do perfil. '
                        'Para livros, varie autores, níveis e estilos (didático, técnico, prático, biográfico ou acessível), '
                        'evite repetir títulos padrão e retorne somente título e resumo; o campo url de livros deve ser vazio. '
                        'Inclua curso gratuito, pago e ligado ao interesse específico. '
                        'Toda sugestão é uma possibilidade, nunca uma obrigação ou diagnóstico. '
                        'Se uma fonte não comprovar um detalhe, escreva que ele precisa ser confirmado na instituição.'
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
                            'resumo': 'string específico para o curso escolhido',
                            'itens': 'array com 5 a 8 faculdades, 3 a 5 livros e 3 a 5 cursos/certificações',
                            'proximos_passos': 'array com 6 a 10 ações em ordem cronológica, até matrícula e início das aulas',
                            'comunidades': 'array com 2 a 5 fóruns, associações, eventos ou grupos específicos da área',
                            'item': ['tipo', 'titulo', 'descricao', 'o_que_fazer', 'como_fazer', 'opcoes', 'por_que_pode_fazer_sentido', 'url (vazio para livros)', 'nivel', 'estimativa_tempo', 'custo', 'alcance', 'modalidade'],
                        },
                        'fontes_tavily': fontes,
                        'instituicoes_prioritarias_do_produto': faculdades_prioritarias,
                        'plataformas_prioritarias_de_cursos_do_produto': cursos_prioritarios,
                    }, ensure_ascii=False),
                },
            ],
            max_completion_tokens=1400,
        )
        parsed = json.loads(response.choices[0].message.content or '{}')
        raw_steps = parsed.get('proximos_passos', fallback['proximos_passos'])
        steps = raw_steps if isinstance(raw_steps, list) else fallback['proximos_passos']
        # Uma resposta com poucos detalhes volta para a curadoria local. Assim,
        # nenhum perfil recebe cartões genéricos só porque a IA respondeu incompleto.
        if not _resposta_ia_esta_detalhada(parsed.get('itens')):
            raise ValueError('resposta da IA sem detalhamento mínimo por área')
        result = {
            'origem': 'ia',
            'resumo': str(parsed.get('resumo', fallback['resumo']))[:700],
            'itens': _normalizar_itens(parsed.get('itens'), fallback),
            'proximos_passos': [str(item)[:300] for item in steps[:10]],
            'comunidades': [str(item)[:300] for item in parsed.get('comunidades', fallback['comunidades'])[:5]] if isinstance(parsed.get('comunidades', fallback['comunidades']), list) else fallback['comunidades'],
        }
    except Exception as error:
        logger.warning('Recomendações indisponíveis; usando fallback: %s', error)
        result = fallback

    cache.set(key, result, 30 * 60)
    return result
