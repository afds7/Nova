from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from .models import Assessment, PerfilAluno, HistoricoIEP, Objetivo, Competencia
from .serializers import AssessmentSerializer
from .services import generate_action_plan
from django.core.cache import cache
from .cache_utils import assessment_cache_key, invalidate_profile_cache


class AssessmentCreateView(generics.CreateAPIView):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        # 1. Valida os dados que vieram do front
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2. Chama a IA (LGPD safe - só passamos scores)
        data = serializer.validated_data
        password = data.pop('password', '') # Extrai a senha antes de salvar no modelo Assessment
        action_plan = generate_action_plan(data)

        # 3. Salva no banco JÁ COM o plano de ação embutido
        assessment = serializer.save(action_plan=action_plan)

        # 4. Se existir um PerfilAluno vinculado a este e-mail, popula o histórico e competências.
        # Se recebemos a senha, criamos a conta antes.
        email = data.get('email', '').strip().lower()
        
        if email:
            from django.contrib.auth.models import User
            if password and not User.objects.filter(email=email).exists():
                name = data.get('name', '').strip() or 'Aluno'
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=name,
                )
                PerfilAluno.objects.create(user=user, nome=name)

            perfil = PerfilAluno.objects.filter(user__email=email).first()
            if perfil:
                invalidate_profile_cache(str(perfil.id))
                # Criar histórico do IEP
                HistoricoIEP.objects.create(
                    perfil=perfil,
                    iep_score=assessment.iep_score,
                    iev_score=assessment.iev_score,
                    diagnostic=assessment.diagnostic
                )
                
                # Criar ou atualizar objetivo com base na área de interesse
                Objetivo.objects.update_or_create(
                    perfil=perfil,
                    defaults={'area_curso': assessment.area}
                )
                
                # Criar/atualizar competências iniciais com base nos resultados do quiz
                pilares = [
                    'Base Acadêmica',
                    'Visão Estratégica',
                    'Foco Comportamental',
                    'Diferenciação',
                    'Projetos e Prova Real',
                    'Contato com Mundo Real',
                    'Posicionamento e Networking'
                ]
                
                for pilar in pilares:
                    nivel = 3  # Nível padrão intermediário
                    if pilar == assessment.strongest_point:
                        nivel = 4
                    elif pilar == assessment.weakest_point:
                        nivel = 2
                        
                    Competencia.objects.update_or_create(
                        perfil=perfil,
                        nome=pilar,
                        defaults={'nivel': nivel}
                    )
            cache.delete(assessment_cache_key(email))

        # 5. Devolve o plano de ação junto com a resposta para o frontend
        headers = self.get_success_headers(serializer.data)
        response_data = serializer.data
        response_data['action_plan'] = action_plan

        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)



class LastAssessmentView(APIView):
    """
    Retorna o diagnóstico mais recente de um usuário pelo e-mail.
    Usado na entrada do app para verificar se o aluno já fez o quiz.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        email = request.query_params.get('email', '').strip().lower()
        if not email:
            return Response({"error": "E-mail é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)

        cached = cache.get(assessment_cache_key(email))
        if cached:
            return Response(cached, status=status.HTTP_200_OK)

        assessment = Assessment.objects.filter(email=email).first()
        if not assessment:
            return Response(None, status=status.HTTP_404_NOT_FOUND)

        payload = {
            "id":              str(assessment.id),
            "name":            assessment.name,
            "email":           assessment.email,
            "iep_score":       assessment.iep_score,
            "iev_score":       assessment.iev_score,
            "diagnostic":      assessment.diagnostic,
            "area":            assessment.area,
            "strongest_point": assessment.strongest_point,
            "weakest_point":   assessment.weakest_point,
            "gap":             assessment.gap,
            "action_plan":     assessment.action_plan,
        }
        cache.set(assessment_cache_key(email), payload, 60)
        return Response(payload, status=status.HTTP_200_OK)
