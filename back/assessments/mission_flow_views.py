from __future__ import annotations

from uuid import UUID

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .mission_flow import conclude_mission
from .mission_flow_serializers import EvidencePublishSerializer, MissionCompletionSerializer
from .models import EvidenciaPortfolio, MissaoAluno, PerfilAluno
from .portfolio_serializers import EvidenciaPortfolioSerializer
from .cache_utils import invalidate_profile_cache


def _profile(request, profile_id: str | None = None) -> PerfilAluno:
    if request.user.is_authenticated:
        return get_object_or_404(PerfilAluno, user=request.user)
    if not profile_id:
        raise ValueError('profile_id é obrigatório')
    return get_object_or_404(PerfilAluno, id=profile_id)


class MissionCompleteView(APIView):
    def post(self, request, mission_id: UUID):
        serializer = MissionCompletionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            profile = _profile(request, serializer.validated_data.get('profile_id'))
            assignment, draft, history, already_completed = conclude_mission(
                profile=profile, mission_id=str(mission_id)
            )
        except ValueError as error:
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        except MissaoAluno.DoesNotExist:
            return Response({'error': 'Missão não encontrada para este perfil.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'message': 'Missão concluída e evolução registrada com base na ação realizada.',
            'already_completed': already_completed,
            'mission_id': str(assignment.missao_id),
            'mission_status': assignment.status,
            'evidence_draft': EvidenciaPortfolioSerializer(draft).data,
            'iep_history_id': str(history.id),
            'iep_score': history.iep_score,
        }, status=status.HTTP_200_OK)


class EvidencePublishView(APIView):
    def post(self, request, evidence_id: UUID):
        try:
            profile = _profile(request, request.data.get('profile_id'))
        except ValueError as error:
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)

        evidence = get_object_or_404(
            EvidenciaPortfolio,
            id=evidence_id,
            perfil=profile,
            origem='missao',
        )
        if evidence.ativo:
            return Response(EvidenciaPortfolioSerializer(evidence).data, status=status.HTTP_200_OK)
        requested_key = request.data.get('arquivo_chave', evidence.arquivo_chave)
        if requested_key and not str(requested_key).startswith(f'evidencias/{profile.id}/'):
            return Response({'error': 'arquivo não pertence ao perfil atual'}, status=status.HTTP_403_FORBIDDEN)
        serializer = EvidencePublishSerializer(evidence, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        published = serializer.save(ativo=True)
        invalidate_profile_cache(str(profile.id))
        return Response(EvidenciaPortfolioSerializer(published).data, status=status.HTTP_200_OK)
