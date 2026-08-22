import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import PerfilAluno
from .serializers import DashboardSerializer, MissionSuggestionSerializer
from .services import MotorDeMissoes

logger = logging.getLogger('assessments')

LEGACY_DIAGNOSTIC_LABELS = {
    'Bom Aluno Comum': 'Boa base, falta mostrar',
    'Talento Mal Direcionado': 'Potencial sem direção',
    'Alta Performance Real': 'Pronto para avançar',
    'Alto Risco': 'Hora de organizar a rota',
}


def friendly_diagnostic(label: str) -> str:
    """Atualiza rótulos antigos sem alterar o histórico salvo no banco."""
    return LEGACY_DIAGNOSTIC_LABELS.get(label, label)


class DashboardView(APIView):
    """
    Endpoint agregador do Dashboard de Evolução Contínua.
    Retorna todos os dados necessários para a visão principal do aluno em uma única requisição.

    Query Params:
        profile_id (str): fallback para a sessão do NextAuth no frontend.
        Quando o Django possui um usuário autenticado, request.user é a fonte de verdade.
    """

    def get(self, request):
        # ── Busca o perfil ──────────────────────────────────────────────
        try:
            perfil_query = (
                PerfilAluno.objects
                .select_related('user', 'objetivo')
                .prefetch_related('competencias', 'historicos_iep', 'missoes', 'portfolio')
            )
            if request.user.is_authenticated:
                perfil = perfil_query.get(user=request.user)
            else:
                profile_id = request.query_params.get('profile_id', '').strip()
                if not profile_id:
                    return Response(
                        {'error': 'profile_id é obrigatório quando não há usuário autenticado'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                perfil = perfil_query.get(id=profile_id)
        except PerfilAluno.DoesNotExist:
            return Response(
                {'error': 'Perfil não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # ── Objetivo ─────────────────────────────────────────────────────
        objetivo = getattr(perfil, 'objetivo', None)

        # ── Histórico IEP (ordenado por mais recente) ─────────────────────
        historicos = list(perfil.historicos_iep.order_by('-created_at')[:2])
        ultimo_iep = historicos[0] if historicos else None
        penultimo_iep = historicos[1] if len(historicos) > 1 else None

        iep_score = ultimo_iep.iep_score if ultimo_iep else 0
        iev_score = ultimo_iep.iev_score if ultimo_iep else 0
        diagnostic = friendly_diagnostic(
            ultimo_iep.diagnostic if ultimo_iep else 'Sem diagnóstico'
        )
        assessment_date = ultimo_iep.created_at if ultimo_iep else None

        iep_delta = None
        if ultimo_iep and penultimo_iep:
            iep_delta = ultimo_iep.iep_score - penultimo_iep.iep_score

        # ── Competências ──────────────────────────────────────────────────
        competencias = list(
            perfil.competencias.order_by('-nivel').values('id', 'nome', 'nivel')
        )
        # Converte UUIDs para string
        for c in competencias:
            c['id'] = str(c['id'])

        # Competência prioritária = a de menor nível (a que mais precisa evoluir)
        competencia_prioritaria = None
        if competencias:
            prioritaria = min(competencias, key=lambda c: c['nivel'])
            competencia_prioritaria = prioritaria

        # ── Missões ───────────────────────────────────────────────────────
        missoes = perfil.missoes.all()
        mission_stats = {
            'total': missoes.count(),
            'concluidas': missoes.filter(status='concluida').count(),
            'em_andamento': missoes.filter(status='em_andamento').count(),
            'pendentes': missoes.filter(status='pendente').count(),
        }

        # Próximas missões pendentes/em andamento para exibir no dashboard
        proximas_missoes = list(
            missoes.exclude(status='concluida')
            .order_by('prazo')[:3]
            .values('id', 'titulo', 'status', 'prazo')
        )
        for m in proximas_missoes:
            m['id'] = str(m['id'])
            if m['prazo']:
                m['prazo'] = m['prazo'].isoformat()

        # ── Portfólio ──────────────────────────────────────────────────────
        portfolio_count = perfil.portfolio.count()

        # ── Próximo Foco (recomendação) ────────────────────────────────────
        proximo_foco = None
        if competencia_prioritaria and objetivo:
            proximo_foco = {
                'competencia': competencia_prioritaria['nome'],
                'nivel_atual': competencia_prioritaria['nivel'],
                'area': objetivo.area_curso,
                'mensagem': (
                    f"Seu principal ponto de desenvolvimento em {objetivo.area_curso} "
                    f"é '{competencia_prioritaria['nome']}' (nível {competencia_prioritaria['nivel']}/5). "
                    "Fortalecer essa competência pode abrir seu próximo passo."
                )
            }
        elif objetivo:
            proximo_foco = {
                'competencia': None,
                'nivel_atual': None,
                'area': objetivo.area_curso,
                'mensagem': f"Comece mapeando suas competências em {objetivo.area_curso}."
            }

        logger.info(
            "Dashboard acessado | perfil=%s | iep=%s | delta=%s",
            str(perfil.id), iep_score, iep_delta
        )

        payload = {
            # Identificação
            'student_id': str(perfil.id),
            'student_name': perfil.nome,
            'student_email': perfil.user.email,

            # Objetivo
            'objective_id': str(objetivo.id) if objetivo else None,
            'objective_area': objetivo.area_curso if objetivo else None,

            # IEP atual
            'iep_score': iep_score,
            'iev_score': iev_score,
            'iep_delta': iep_delta,
            'diagnostic': diagnostic,
            'assessment_date': assessment_date,

            # Competências
            'competency_scores': competencias,
            'priority_competency': competencia_prioritaria,

            # Missões
            'mission_stats': mission_stats,
            'upcoming_missions': proximas_missoes,

            # Portfólio
            'portfolio_count': portfolio_count,

            # Experiências (placeholder para fase futura)
            'experience_count': 0,

            # Próximo foco
            'next_focus': proximo_foco,

            # Metadados
            'last_updated': perfil.updated_at,
        }
        return Response(DashboardSerializer(payload).data, status=status.HTTP_200_OK)


class MissionSuggestionsView(APIView):
    """Retorna as três missões mais relevantes para um perfil de aluno."""

    def get(self, request):
        profile_id = request.query_params.get('profile_id', '').strip()

        try:
            if request.user.is_authenticated:
                perfil = PerfilAluno.objects.get(user=request.user)
            elif profile_id:
                perfil = PerfilAluno.objects.get(pk=profile_id)
            else:
                return Response(
                    {'error': 'profile_id é obrigatório quando não há usuário autenticado'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (PerfilAluno.DoesNotExist, ValueError):
            return Response(
                {'error': 'Perfil não encontrado'},
                status=status.HTTP_404_NOT_FOUND,
            )

        assignments = MotorDeMissoes.recomendar(perfil.id)
        missions = [
            {
                'id': assignment.missao.id,
                'titulo': assignment.missao.titulo,
                'descricao': assignment.missao.descricao,
                'area_relacionada': assignment.missao.area_relacionada,
                'competencias_desenvolvidas': assignment.missao.competencias_desenvolvidas or [],
                'dificuldade': assignment.missao.dificuldade,
                'duracao_estimada_minutos': assignment.missao.duracao_estimada_minutos,
                'prazo_dias': assignment.missao.prazo_dias,
                'dias_uteis_estimados': assignment.missao.dias_uteis_estimados,
                'prazo': assignment.prazo,
                'prioridade': assignment.prioridade,
                'motivo_recomendacao': assignment.motivo_recomendacao,
            }
            for assignment in assignments
        ]
        return Response(
            MissionSuggestionSerializer(missions, many=True).data,
            status=status.HTTP_200_OK,
        )
