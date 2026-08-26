from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from diagnostico.services.recomendacoes_ia import gerar_recomendacoes

from .models import Competencia, HistoricoIEP, PerfilAluno
from .profile_utils import parse_profile_id


class RecommendationsView(APIView):
    """Entrega recomendações específicas do perfil sem expor dados pessoais à IA."""

    def get(self, request):
        try:
            profile_id = parse_profile_id(request.query_params.get('profile_id'))
            perfil = PerfilAluno.objects.select_related('objetivo').get(id=profile_id)
        except ValueError as error:
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        except PerfilAluno.DoesNotExist:
            return Response({'error': 'Perfil não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        competencias = list(perfil.competencias.all())
        historico = perfil.historicos_iep.order_by('-created_at').first()
        ordenadas = sorted(competencias, key=lambda item: item.nivel, reverse=True)
        prioridade = min(competencias, key=lambda item: item.nivel, default=None)
        result = gerar_recomendacoes({
            'perfil_id': str(perfil.id),
            'area': getattr(getattr(perfil, 'objetivo', None), 'area_curso', ''),
            'prioridade': prioridade.nome if prioridade else '',
            'pontos_fortes': [item.nome for item in ordenadas[:3]],
            'nivel_iep': float(historico.iep_score) if historico else 0,
        })
        return Response({
            'perfil_id': str(perfil.id),
            'area': getattr(getattr(perfil, 'objetivo', None), 'area_curso', ''),
            'competencia_prioritaria': prioridade.nome if prioridade else None,
            'origem': result['origem'],
            'resumo': result['resumo'],
            'itens': result['itens'],
            'proximos_passos': result['proximos_passos'],
            'comunidades': result.get('comunidades', []),
        })
