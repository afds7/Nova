from rest_framework import serializers

from .models import EvidenciaPortfolio


class UploadStartSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=100)
    file_size = serializers.IntegerField(min_value=1)


class EvidenciaPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenciaPortfolio
        fields = [
            'id', 'titulo', 'descricao', 'tipo', 'arquivo_url', 'arquivo_chave',
            'origem', 'missao_relacionada', 'ativo', 'criado_em',
        ]
        read_only_fields = ['id', 'ativo', 'criado_em']


class EvidenceConfirmSerializer(serializers.Serializer):
    titulo = serializers.CharField(max_length=255)
    descricao = serializers.CharField(required=False, allow_blank=True)
    tipo = serializers.ChoiceField(choices=EvidenciaPortfolio.TIPO_CHOICES)
    arquivo_url = serializers.URLField(max_length=2048, required=False, allow_blank=True)
    arquivo_chave = serializers.CharField(max_length=512)
    origem = serializers.ChoiceField(
        choices=EvidenciaPortfolio.ORIGEM_CHOICES, default='manual'
    )
    missao_relacionada = serializers.UUIDField(required=False, allow_null=True)
