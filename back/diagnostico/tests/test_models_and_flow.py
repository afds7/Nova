from __future__ import annotations

from uuid import UUID
import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from assessments.models import (
    Competencia,
    EvidenciaPortfolio,
    HistoricoIEP,
    Missao,
    MissaoAluno,
    Objetivo,
)


@pytest.mark.django_db
def test_new_records_use_uuid_primary_keys(profile_factory):
    profile = profile_factory()
    objective = Objetivo.objects.create(perfil=profile, area_curso='Design')
    mission = Missao.objects.create(
        titulo='Criar uma entrega', competencias_desenvolvidas=['Design']
    )
    assignment = MissaoAluno.objects.create(perfil=profile, missao=mission)
    history = HistoricoIEP.objects.create(perfil=profile, iep_score=60, diagnostic='Em evolução')
    evidence = EvidenciaPortfolio.objects.create(
        perfil=profile, titulo='Entrega', tipo='projeto', arquivo_url='', arquivo_chave=''
    )

    for record in (profile, objective, mission, assignment, history, evidence):
        assert isinstance(record.pk, UUID)


@pytest.mark.django_db
def test_history_is_append_only(profile_factory):
    profile = profile_factory()
    first = HistoricoIEP.objects.create(perfil=profile, iep_score=60, diagnostic='Primeiro registro')
    second = HistoricoIEP.objects.create(perfil=profile, iep_score=60.5, diagnostic='Nova ação registrada')

    assert first.pk != second.pk
    assert HistoricoIEP.objects.filter(perfil=profile).count() == 2
    assert first.iep_score == 60
    assert second.iep_score == 60.5


@pytest.mark.django_db
def test_complete_mission_creates_draft_and_new_history(profile_factory):
    profile = profile_factory()
    Competencia.objects.create(perfil=profile, nome='Comunicação Social', nivel=2)
    old_history = HistoricoIEP.objects.create(perfil=profile, iep_score=60, diagnostic='Base')
    mission = Missao.objects.create(
        titulo='Praticar comunicação',
        dificuldade='media',
        competencias_desenvolvidas=['Comunicação Social'],
    )
    assignment = MissaoAluno.objects.create(perfil=profile, missao=mission)

    response = APIClient().post(
        f'/api/missoes/{mission.id}/concluir/', {'profile_id': str(profile.id)}, format='json'
    )

    assert response.status_code == 200
    assert assignment.__class__.objects.get(pk=assignment.pk).status == 'concluida'
    assert EvidenciaPortfolio.objects.filter(
        perfil=profile, missao_relacionada=assignment, ativo=False
    ).exists()
    assert HistoricoIEP.objects.filter(perfil=profile).count() == 2
    assert HistoricoIEP.objects.get(pk=old_history.pk).iep_score == 60


@pytest.mark.django_db
def test_publish_draft_is_explicit_and_soft_delete_preserves_record(profile_factory):
    profile = profile_factory()
    draft = EvidenciaPortfolio.objects.create(
        perfil=profile, titulo='Rascunho', tipo='projeto', origem='missao', ativo=False,
        arquivo_url='', arquivo_chave=''
    )
    client = APIClient()
    response = client.post(
        f'/api/portfolio/evidencias/{draft.id}/publicar/',
        {'profile_id': str(profile.id), 'titulo': 'Entrega revisada', 'descricao': 'Detalhes'},
        format='json',
    )

    assert response.status_code == 200
    draft.refresh_from_db()
    assert draft.ativo is True
    assert draft.titulo == 'Entrega revisada'

    draft.ativo = False
    draft.save(update_fields=['ativo'])
    assert EvidenciaPortfolio.objects.filter(pk=draft.pk).exists()


@pytest.mark.django_db
def test_mission_engine_does_not_replace_completed_weekly_cycle(profile_factory):
    """Após três conclusões no ciclo, nenhuma quarta missão é criada antes de 7 dias."""
    from assessments.services import MotorDeMissoes

    profile = profile_factory()
    missions = [
        Missao.objects.create(
            titulo=f'Missão {index}',
            competencias_desenvolvidas=['Comunicação Social'],
        )
        for index in range(3)
    ]
    for mission in missions:
        MissaoAluno.objects.create(
            perfil=profile,
            missao=mission,
            status='concluida',
            concluida_em=timezone.now(),
        )

    assert MotorDeMissoes.recomendar(profile.id) == []
    assert MissaoAluno.objects.filter(perfil=profile).count() == 3
