from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import PerfilAluno


class RegisterView(APIView):
    """
    Cadastro de novo usuário com email e senha.
    Cria User do Django (com senha hasheada) + PerfilAluno vinculado.
    Retorna os dados do perfil para o NextAuth criar a sessão.
    """
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')
        name = request.data.get('name', '').strip() or 'Aluno'

        if not email or not password:
            return Response(
                {"error": "E-mail e senha são obrigatórios"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(password) < 6:
            return Response(
                {"error": "A senha deve ter pelo menos 6 caracteres"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "Este e-mail já está cadastrado"},
                status=status.HTTP_409_CONFLICT
            )

        # Cria o usuário com senha hasheada via create_user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name,
        )

        perfil = PerfilAluno.objects.create(user=user, nome=name)

        return Response({
            "id": str(perfil.id),
            "email": user.email,
            "name": perfil.nome,
        }, status=status.HTTP_201_CREATED)


class EmailLoginView(APIView):
    """
    Login com email e senha.
    Valida as credenciais usando o sistema de autenticação do Django.
    Retorna os dados do perfil para o NextAuth criar a sessão.
    """
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')

        if not email or not password:
            return Response(
                {"error": "E-mail e senha são obrigatórios"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Django usa username para autenticar; como usamos email como username, funciona direto
        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response(
                {"error": "E-mail ou senha incorretos"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        perfil, _ = PerfilAluno.objects.get_or_create(
            user=user,
            defaults={'nome': user.first_name or email}
        )

        return Response({
            "id": str(perfil.id),
            "email": user.email,
            "name": perfil.nome,
        }, status=status.HTTP_200_OK)

