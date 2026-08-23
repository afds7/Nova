from rest_framework import serializers

from .models import EvidenciaPortfolio


class MissionCompletionSerializer(serializers.Serializer):
    profile_id = serializers.UUIDField(required=False)


class EvidencePublishSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenciaPortfolio
        fields = ['titulo', 'descricao', 'tipo', 'arquivo_url', 'arquivo_chave']

    def validate(self, attrs):
        if not attrs.get('titulo', '').strip():
            raise serializers.ValidationError({'titulo': 'Dê um título para esta evidência.'})
        return attrs
