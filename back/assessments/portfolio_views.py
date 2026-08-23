from __future__ import annotations

from uuid import UUID

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EvidenciaPortfolio, MissaoAluno, PerfilAluno
from .portfolio_serializers import (
    EvidenceConfirmSerializer,
    EvidenciaPortfolioSerializer,
    UploadStartSerializer,
)
from .storage_utils import create_presigned_upload


def profile_for_request(request, profile_id: str | None = None) -> PerfilAluno:
    if request.user.is_authenticated:
        return get_object_or_404(PerfilAluno, user=request.user)
    if not profile_id:
        raise ValueError('profile_id é obrigatório')
    return get_object_or_404(PerfilAluno, id=profile_id)


class PortfolioUploadStartView(APIView):
    """Valida metadados e assina um PUT direto para S3/R2."""

    def post(self, request):
        serializer = UploadStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            perfil = profile_for_request(request, request.data.get('profile_id'))
            upload = create_presigned_upload(
                filename=serializer.validated_data['filename'],
                content_type=serializer.validated_data['content_type'],
                file_size=serializer.validated_data['file_size'],
                profile_id=str(perfil.id),
            )
        except ValueError as error:
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)

        public_base = getattr(settings, 'AWS_S3_PUBLIC_BASE_URL', '')
        arquivo_url = f"{public_base}/{upload['object_key']}" if public_base else ''
        return Response(
            {
                'upload_url': upload['url'],
                'arquivo_chave': upload['object_key'],
                'arquivo_url': arquivo_url,
                'expires_in': upload['expires_in'],
                'max_bytes': 25 * 1024 * 1024,
            },
            status=status.HTTP_201_CREATED,
        )


class EvidenciaPortfolioListCreateView(APIView):
    def get(self, request):
        try:
            perfil = profile_for_request(request, request.query_params.get('profile_id'))
        except ValueError as error:
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        evidencias = EvidenciaPortfolio.objects.filter(perfil=perfil, ativo=True)
        return Response(EvidenciaPortfolioSerializer(evidencias, many=True).data)

    def post(self, request):
        serializer = EvidenceConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            perfil = profile_for_request(request, request.data.get('profile_id'))
            evidence_key = serializer.validated_data['arquivo_chave']
            owner_prefix = f'evidencias/{perfil.id}/'
            if not evidence_key.startswith(owner_prefix):
                return Response(
                    {'error': 'arquivo não pertence ao perfil atual'},
                    status=status.HTTP_403_FORBIDDEN,
                )

            mission_id = serializer.validated_data.get('missao_relacionada')
            mission = None
            if mission_id:
                mission = get_object_or_404(MissaoAluno, id=mission_id, perfil=perfil)

            public_base = getattr(settings, 'AWS_S3_PUBLIC_BASE_URL', '')
            arquivo_url = serializer.validated_data.get('arquivo_url', '')
            if public_base:
                arquivo_url = f"{public_base}/{evidence_key}"

            evidence = EvidenciaPortfolio.objects.create(
                perfil=perfil,
                titulo=serializer.validated_data['titulo'],
                descricao=serializer.validated_data.get('descricao', ''),
                tipo=serializer.validated_data['tipo'],
                arquivo_url=arquivo_url,
                arquivo_chave=evidence_key,
                origem=serializer.validated_data.get('origem', 'manual'),
                missao_relacionada=mission,
            )
        except ValueError as error:
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            EvidenciaPortfolioSerializer(evidence).data,
            status=status.HTTP_201_CREATED,
        )


class EvidenciaPortfolioDetailView(APIView):
    def get(self, request, evidence_id: UUID):
        try:
            perfil = profile_for_request(request, request.query_params.get('profile_id'))
        except ValueError as error:
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        evidence = get_object_or_404(EvidenciaPortfolio, id=evidence_id, perfil=perfil)
        return Response(EvidenciaPortfolioSerializer(evidence).data)

    def patch(self, request, evidence_id: UUID):
        try:
            perfil = profile_for_request(request, request.data.get('profile_id'))
        except ValueError as error:
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        evidence = get_object_or_404(
            EvidenciaPortfolio, id=evidence_id, perfil=perfil, ativo=True
        )
        # Exclusão é sempre lógica: o registro e o objeto na nuvem permanecem auditáveis.
        if request.data.get('ativo') is not False:
            return Response(
                {'error': 'uma evidência só pode ser marcada como inativa'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        evidence.ativo = False
        evidence.save(update_fields=['ativo'])
        return Response(EvidenciaPortfolioSerializer(evidence).data)
