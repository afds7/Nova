from rest_framework import serializers
from .models import Assessment

class AssessmentSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Assessment
        fields = ['id', 'name', 'email', 'area', 'iep_score', 'iev_score', 'diagnostic', 'strongest_point', 'weakest_point', 'gap', 'action_plan', 'created_at', 'password']
        read_only_fields = ['id', 'created_at']


class DashboardCompetencySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    nome = serializers.CharField()
    nivel = serializers.IntegerField()


class DashboardMissionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    titulo = serializers.CharField()
    status = serializers.CharField()
    prazo = serializers.DateField(allow_null=True)


class DashboardMissionStatsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    concluidas = serializers.IntegerField()
    em_andamento = serializers.IntegerField()
    pendentes = serializers.IntegerField()


class DashboardFocusSerializer(serializers.Serializer):
    competencia = serializers.CharField(allow_null=True)
    nivel_atual = serializers.IntegerField(allow_null=True)
    area = serializers.CharField()
    mensagem = serializers.CharField()


class DashboardEvidenceDraftSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    titulo = serializers.CharField()
    descricao = serializers.CharField(allow_blank=True)
    tipo = serializers.CharField()
    missao_relacionada = serializers.UUIDField(allow_null=True)


class DashboardLastMissionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    titulo = serializers.CharField()
    concluida_em = serializers.DateTimeField(allow_null=True)


class DashboardSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    student_name = serializers.CharField()
    student_email = serializers.EmailField()
    objective_id = serializers.UUIDField(allow_null=True)
    objective_area = serializers.CharField(allow_null=True)
    iep_score = serializers.DecimalField(max_digits=5, decimal_places=2, coerce_to_string=False)
    iev_score = serializers.DecimalField(max_digits=5, decimal_places=2, coerce_to_string=False)
    iep_delta = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True, coerce_to_string=False)
    diagnostic = serializers.CharField()
    assessment_date = serializers.DateTimeField(allow_null=True)
    competency_scores = DashboardCompetencySerializer(many=True)
    priority_competency = DashboardCompetencySerializer(allow_null=True)
    mission_stats = DashboardMissionStatsSerializer()
    upcoming_missions = DashboardMissionSerializer(many=True)
    portfolio_count = serializers.IntegerField()
    experience_count = serializers.IntegerField()
    next_focus = DashboardFocusSerializer(allow_null=True)
    last_updated = serializers.DateTimeField()
    ultima_missao_concluida = DashboardLastMissionSerializer(allow_null=True)
    rascunho_evidencia_pendente = DashboardEvidenceDraftSerializer(allow_null=True)


class MissionSuggestionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    titulo = serializers.CharField()
    descricao = serializers.CharField(allow_blank=True)
    area_relacionada = serializers.CharField(allow_blank=True)
    competencias_desenvolvidas = serializers.ListField(child=serializers.CharField())
    dificuldade = serializers.CharField()
    duracao_estimada_minutos = serializers.IntegerField()
    prazo_dias = serializers.IntegerField()
    dias_uteis_estimados = serializers.IntegerField()
    prazo = serializers.DateField(allow_null=True)
    prioridade = serializers.IntegerField()
    motivo_recomendacao = serializers.CharField()
    competencia_alvo = serializers.CharField()
    origem_geracao = serializers.ChoiceField(choices=['regra', 'regra+ia'])
    gerada_por_ia = serializers.BooleanField()
