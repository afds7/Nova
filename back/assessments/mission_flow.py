from __future__ import annotations

import unicodedata
from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from .models import Competencia, EvidenciaPortfolio, HistoricoIEP, MissaoAluno, PerfilAluno

MAX_IEP_SCORE = Decimal('96')
SLOW_PROGRESSION_FROM = Decimal('83')
WEEKLY_SLOW_LIMIT = Decimal('0.5')
NORMAL_MISSION_POINTS = {
    'dificil': Decimal('0.5'),
    'media': Decimal('0.3'),
    'facil': Decimal('0.2'),
}
SLOW_MISSION_POINTS = {
    'dificil': Decimal('0.3'),
    'media': Decimal('0.15'),
    'facil': Decimal('0.05'),
}


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize('NFKD', value)
    return ''.join(char for char in decomposed if not unicodedata.combining(char)).casefold().strip()


def _mission_competencies(missao: Any) -> list[str]:
    values = missao.competencias_desenvolvidas or []
    if isinstance(values, dict):
        values = values.keys()
    return [str(value) for value in values]


@transaction.atomic
def conclude_mission(*, profile: PerfilAluno, mission_id: str) -> tuple[MissaoAluno, EvidenciaPortfolio, HistoricoIEP, bool]:
    assignment = (
        MissaoAluno.objects.select_for_update()
        .select_related('missao', 'perfil')
        .get(missao_id=mission_id, perfil=profile)
    )
    already_completed = assignment.status == 'concluida'

    if not already_completed:
        assignment.status = 'concluida'
        assignment.progresso = 100
        assignment.concluida_em = timezone.now()
        assignment.save(update_fields=['status', 'progresso', 'concluida_em', 'updated_at'])

        competency_names = _mission_competencies(assignment.missao)
        normalized_names = {_normalize(name) for name in competency_names}
        competencies = list(Competencia.objects.select_for_update().filter(perfil=profile))
        impacted = []
        for competency in competencies:
            if _normalize(competency.nome) in normalized_names:
                before = competency.nivel
                competency.nivel = min(5, competency.nivel + 1)
                competency.save(update_fields=['nivel'])
                impacted.append({'nome': competency.nome, 'nivel_anterior': before, 'nivel_atual': competency.nivel})

        latest = profile.historicos_iep.order_by('-created_at').first()
        average_level = sum(item.nivel for item in competencies) / len(competencies) if competencies else 0
        calculated_score = Decimal(str(round(average_level * 20))) if competencies else (latest.iep_score if latest else Decimal('0'))
        mission_difficulty = assignment.missao.dificuldade
        if latest and latest.iep_score >= SLOW_PROGRESSION_FROM:
            week_start = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
            weekly_points = Decimal('0')
            for record in profile.historicos_iep.filter(created_at__date__gte=week_start):
                if record.detalhamento.get('origem') == 'missao_concluida':
                    weekly_points += Decimal(str(record.detalhamento.get('impacto_iep', '0')))
            mission_points = min(
                SLOW_MISSION_POINTS.get(mission_difficulty, Decimal('0.05')),
                max(Decimal('0'), WEEKLY_SLOW_LIMIT - weekly_points),
            )
        else:
            mission_points = NORMAL_MISSION_POINTS.get(mission_difficulty, Decimal('0.2'))
        applied_points = mission_points if impacted else Decimal('0')
        if latest:
            new_score = min(MAX_IEP_SCORE, latest.iep_score + applied_points)
        else:
            new_score = min(MAX_IEP_SCORE, calculated_score + applied_points)
        history = HistoricoIEP.objects.create(
            perfil=profile,
            iep_score=new_score,
            iev_score=latest.iev_score if latest else 0,
            diagnostic='Evolução registrada com base em uma missão concluída',
            detalhamento={
                'origem': 'missao_concluida',
                'missao_id': str(assignment.missao_id),
                'missao_titulo': assignment.missao.titulo,
                'competencias_impactadas': impacted,
                'impacto_iep': str(applied_points),
                'observacao': 'Este registro reflete uma ação concluída e não é um diagnóstico definitivo.',
            },
        )
    else:
        history = profile.historicos_iep.order_by('-created_at').first()
        if history is None:
            raise ValueError('Histórico do IEP não encontrado para a missão concluída.')

    draft, _ = EvidenciaPortfolio.objects.get_or_create(
        perfil=profile,
        missao_relacionada=assignment,
        origem='missao',
        defaults={
            'titulo': f'Entrega: {assignment.missao.titulo}',
            'descricao': 'Rascunho criado a partir da missão concluída. Revise e complemente antes de publicar.',
            'tipo': 'projeto',
            'arquivo_url': '',
            'arquivo_chave': '',
            'ativo': False,
        },
    )
    return assignment, draft, history, already_completed
