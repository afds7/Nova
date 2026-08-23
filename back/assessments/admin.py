from django.contrib import admin
from .models import (
    Assessment, PerfilAluno, Objetivo,
    Competencia, HistoricoIEP, Missao, MissaoAluno, ItemPortfolio,
    Portfolio, Evidencia, EvidenciaPortfolio
)


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'diagnostic', 'iep_score', 'iev_score', 'created_at')
    list_filter = ('diagnostic',)
    search_fields = ('name', 'email')
    readonly_fields = ('id', 'created_at')


@admin.register(PerfilAluno)
class PerfilAlunoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'user', 'created_at')
    search_fields = ('nome', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Objetivo)
class ObjetivoAdmin(admin.ModelAdmin):
    list_display = ('perfil', 'area_curso', 'created_at')
    search_fields = ('perfil__nome', 'area_curso')


@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'perfil', 'nivel')
    list_filter = ('nivel',)
    search_fields = ('nome', 'perfil__nome')


@admin.register(HistoricoIEP)
class HistoricoIEPAdmin(admin.ModelAdmin):
    list_display = ('perfil', 'iep_score', 'iev_score', 'diagnostic', 'created_at')
    list_filter = ('diagnostic',)
    search_fields = ('perfil__nome',)
    readonly_fields = ('id', 'created_at')


@admin.register(Missao)
class MissaoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'area_relacionada', 'dificuldade', 'perfil', 'status')
    list_filter = ('status',)
    search_fields = ('titulo', 'area_relacionada', 'perfil__nome')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(MissaoAluno)
class MissaoAlunoAdmin(admin.ModelAdmin):
    list_display = ('missao', 'perfil', 'status', 'progresso', 'updated_at')
    list_filter = ('status',)
    search_fields = ('missao__titulo', 'perfil__nome')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(ItemPortfolio)
class ItemPortfolioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'perfil', 'tipo', 'data')
    list_filter = ('tipo',)
    search_fields = ('titulo', 'perfil__nome')
    readonly_fields = ('id', 'created_at')


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'perfil', 'area', 'updated_at')
    search_fields = ('titulo', 'perfil__nome', 'area')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Evidencia)
class EvidenciaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'portfolio', 'tipo_arquivo', 'missao_aluno', 'created_at')
    search_fields = ('titulo', 'portfolio__titulo', 'tipo_arquivo')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(EvidenciaPortfolio)
class EvidenciaPortfolioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'perfil', 'tipo', 'origem', 'ativo', 'criado_em')
    list_filter = ('tipo', 'origem', 'ativo')
    search_fields = ('titulo', 'perfil__nome', 'arquivo_chave')
    readonly_fields = ('id', 'criado_em')
