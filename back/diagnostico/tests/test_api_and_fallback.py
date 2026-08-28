from __future__ import annotations

from types import SimpleNamespace

import pytest
from rest_framework.test import APIClient

from assessments.models import Competencia, Missao


@pytest.mark.django_db
def test_submit_diagnostic_creates_profile_objective_and_history(profile_factory, monkeypatch):
    from assessments import views

    monkeypatch.setattr(views, 'generate_action_plan', lambda data: 'Plano determinístico de fallback')
    response = APIClient().post('/api/assessments/submit/', {
        'name': 'Nova Pessoa', 'email': 'submit@example.com', 'password': 'senha-segura',
        'area': 'Tecnologia', 'iep_score': 60, 'iev_score': 55,
        'diagnostic': 'Em evolução', 'strongest_point': 'Base Acadêmica',
        'weakest_point': 'Comunicação Social', 'gap': 5,
    }, format='json')

    assert response.status_code == 201
    assert response.data['action_plan']


@pytest.mark.django_db
def test_new_diagnostic_recommendations_use_created_assessment(profile_factory, monkeypatch):
    """O primeiro resultado usa o ID recém-criado, nunca o primeiro diagnóstico do e-mail."""
    from assessments import views

    monkeypatch.setattr(views, 'generate_action_plan', lambda data: 'Plano determinístico')
    create = APIClient().post('/api/assessments/submit/', {
        'name': 'Pessoa Nova', 'email': 'new-recommendations@example.com', 'password': 'senha-segura',
        'area': 'Direito', 'iep_score': 70, 'iev_score': 60,
        'diagnostic': 'Em evolução', 'strongest_point': 'Base Acadêmica',
        'weakest_point': 'Visão Estratégica', 'gap': 4,
    }, format='json')
    assert create.status_code == 201

    expected = {
        'origem': 'fallback', 'resumo': 'Recomendação detalhada por área',
        'itens': [{'tipo': 'faculdade', 'titulo': 'Direito — USP', 'descricao': 'x',
                   'o_que_fazer': 'Compare a grade', 'como_fazer': 'Confira o ingresso',
                   'por_que_pode_fazer_sentido': 'x', 'url': '', 'nivel': 'graduação',
                   'estimativa_tempo': '5 anos', 'custo': 'pública', 'alcance': 'nacional',
                   'modalidade': 'presencial', 'opcoes': ['USP']}],
        'proximos_passos': ['Compare opções'], 'comunidades': [],
    }
    monkeypatch.setattr(views, 'gerar_recomendacoes', lambda context: expected)
    recommendation = APIClient().get(
        f"/api/assessments/{create.data['id']}/recommendations/"
    )

    assert recommendation.status_code == 200
    assert recommendation.data['itens'][0]['titulo'] == 'Direito — USP'


@pytest.mark.django_db
def test_mission_suggestions_fallback_when_openai_fails(profile_factory, monkeypatch):
    profile = profile_factory()
    Competencia.objects.create(perfil=profile, nome='Comunicação Social', nivel=1)
    Missao.objects.create(
        titulo='Escrever uma análise', dificuldade='facil',
        competencias_desenvolvidas=['Comunicação Social'], descricao='Texto-base'
    )
    monkeypatch.setenv('OPENAI_API_KEY', 'fake-key-for-test')

    class FailingClient:
        def __init__(self, *args, **kwargs):
            pass

        class chat:
            class completions:
                @staticmethod
                def create(*args, **kwargs):
                    raise RuntimeError('RateLimitError simulado')

    monkeypatch.setattr('openai.OpenAI', FailingClient)
    response = APIClient().get('/api/missoes/sugeridas/', {'profile_id': str(profile.id)})

    assert response.status_code == 200
    assert response.data
    assert response.data[0]['origem_geracao'] == 'regra'
    assert response.data[0]['gerada_por_ia'] is False


@pytest.mark.django_db
def test_mission_prompt_contains_no_personal_identifiers(profile_factory, monkeypatch):
    from diagnostico.services.missoes_ia import personalizar_missao

    captured = {}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    captured['messages'] = kwargs['messages']
                    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                        content='{"titulo":"Uma proposta","descricao":"Uma missão que pode ajudar","estimativa_tempo":40,"competencia_alvo":"Comunicação"}'
                    ))])

    monkeypatch.setenv('OPENAI_API_KEY', 'fake-key-for-test')
    monkeypatch.setattr('openai.OpenAI', FakeClient)
    personalizar_missao(
        profile_id='profile-id',
        base_mission={'id': 'mission-id', 'titulo': 'Base', 'descricao': 'Descrição', 'area_relacionada': 'Área', 'dificuldade': 'facil', 'duracao_estimada_minutos': 40},
        competency_gap='Comunicação', objective_area='Tecnologia',
        strong_competencies=['Organização'], completed_mission_types=['facil'],
    )
    prompt_text = str(captured['messages'])
    assert 'Nova Pessoa' not in prompt_text
    assert 'submit@example.com' not in prompt_text


@pytest.mark.django_db
def test_profile_cannot_read_another_profile_evidence(profile_factory):
    owner = profile_factory('owner@example.com', 'Owner')
    other = profile_factory('other@example.com', 'Other')
    evidence = __import__('assessments.models', fromlist=['EvidenciaPortfolio']).EvidenciaPortfolio.objects.create(
        perfil=owner, titulo='Privada', tipo='projeto', arquivo_url='', arquivo_chave=''
    )

    response = APIClient().get(
        f'/api/portfolio/evidencias/{evidence.id}/?profile_id={other.id}'
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_invalid_profile_id_is_client_error_not_server_error():
    """Carga mal configurada deve retornar 400, sem traceback 500 no backend."""
    client = APIClient()

    for url in (
        '/api/dashboard/resumo/?profile_id=UUID-DE-UM-PERFIL-SINTETICO',
        '/api/missoes/sugeridas/?profile_id=UUID-DE-UM-PERFIL-SINTETICO',
        '/api/portfolio/evidencias/?profile_id=UUID-DE-UM-PERFIL-SINTETICO',
    ):
        response = client.get(url)
        assert response.status_code == 400
        assert 'UUID válido' in response.json()['error']


def test_openai_and_tavily_failure_returns_deterministic_plan(monkeypatch):
    from assessments import services

    class FailingOpenAI:
        def __init__(self, *args, **kwargs):
            pass

        class chat:
            class completions:
                @staticmethod
                def create(*args, **kwargs):
                    raise RuntimeError('OpenAI indisponível')

    class FailingTavily:
        def __init__(self, *args, **kwargs):
            pass

        def search(self, *args, **kwargs):
            raise RuntimeError('Tavily indisponível')

    monkeypatch.setattr(services, 'OpenAI', FailingOpenAI)
    monkeypatch.setattr(services, 'TavilyClient', FailingTavily)
    result = services.generate_action_plan({
        'area': 'Tecnologia', 'iep_score': 60, 'iev_score': 50,
        'weakest_point': 'Comunicação Social', 'strongest_point': 'Organização', 'gap': 10,
    })

    assert 'PRÓXIMOS PASSOS' in result


def test_recommendations_fallback_is_named_and_actionable(monkeypatch):
    """Mesmo sem APIs externas, contas novas não recebem o cartão genérico legado."""
    from diagnostico.services.recomendacoes_ia import gerar_recomendacoes

    monkeypatch.delenv('TAVILY_API_KEY', raising=False)
    result = gerar_recomendacoes({
        'perfil_id': 'fallback-regression-unique',
        'area': 'Ciências Exatas',
        'prioridade': 'Base Acadêmica',
        'perfil_hint': 'interesse em matemática aplicada',
        'pontos_fortes': ['Raciocínio lógico'],
        'nivel_iep': 60,
    })

    assert result['origem'] == 'fallback'
    assert result['itens']
    assert all('Faculdades para estudar' not in item['titulo'] for item in result['itens'])
    assert all(item['o_que_fazer'] and item['como_fazer'] for item in result['itens'])
