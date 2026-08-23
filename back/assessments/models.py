import uuid
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

class Assessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(db_index=True)
    iep_score = models.IntegerField()
    iev_score = models.IntegerField()
    diagnostic = models.CharField(max_length=100)
    area = models.CharField(max_length=100, default="Não informada")
    strongest_point = models.CharField(max_length=100, default="-")
    weakest_point = models.CharField(max_length=100, default="-")
    gap = models.IntegerField(default=0)

    action_plan = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'assessments_lead'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email}) - {self.diagnostic}"


from django.contrib.auth.models import User

class PerfilAluno(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_aluno')
    nome = models.CharField(max_length=255, verbose_name="Nome Completo")
    data_nascimento = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'perfis_alunos'
        verbose_name = 'Perfil do Aluno'
        verbose_name_plural = 'Perfis dos Alunos'

    def __str__(self):
        return f"{self.nome} ({self.user.email})"


class Objetivo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil = models.OneToOneField(PerfilAluno, on_delete=models.CASCADE, related_name='objetivo')
    area_curso = models.CharField(max_length=255, verbose_name="Área ou Curso (Foco Estratégico)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'objetivos'

    def __str__(self):
        return f"Objetivo de {self.perfil.nome}: {self.area_curso}"


class Competencia(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil = models.ForeignKey(PerfilAluno, on_delete=models.CASCADE, related_name='competencias')
    nome = models.CharField(max_length=100)
    nivel = models.IntegerField(default=1)  # ex: 1 a 5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'competencias'

    def __str__(self):
        return f"{self.nome} ({self.perfil.nome})"


class HistoricoIEP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil = models.ForeignKey(PerfilAluno, on_delete=models.CASCADE, related_name='historicos_iep')
    iep_score = models.DecimalField(max_digits=5, decimal_places=2)
    iev_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    diagnostic = models.CharField(max_length=255)
    detalhamento = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False) # Editable False guarantees append-only intent on UI/Admin

    class Meta:
        db_table = 'historicos_iep'
        ordering = ['-created_at']

    def __str__(self):
        return f"IEP: {self.iep_score}% - {self.perfil.nome} em {self.created_at.strftime('%Y-%m-%d')}"


class Missao(models.Model):
    DIFICULDADE_CHOICES = [
        ('facil', 'Fácil'),
        ('media', 'Média'),
        ('dificil', 'Difícil'),
    ]
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluida', 'Concluída'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Mantido como nullable para preservar missões atribuídas na Fase 2.
    # Novas missões de catálogo devem usar MissaoAluno para a atribuição.
    perfil = models.ForeignKey(
        PerfilAluno, on_delete=models.CASCADE, related_name='missoes',
        null=True, blank=True,
    )
    titulo = models.CharField(max_length=255, verbose_name='Título')
    descricao = models.TextField(blank=True, verbose_name='Descrição curta')
    area_relacionada = models.CharField(max_length=255, blank=True, default='')
    competencias_desenvolvidas = models.JSONField(default=list, blank=True)
    dificuldade = models.CharField(
        max_length=10, choices=DIFICULDADE_CHOICES, default='media'
    )
    duracao_estimada_minutos = models.PositiveSmallIntegerField(
        default=60,
        validators=[MinValueValidator(20), MaxValueValidator(240)],
        verbose_name='Duração estimada (minutos)',
    )
    prazo_dias = models.PositiveSmallIntegerField(
        default=7,
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        verbose_name='Prazo (dias)',
    )
    dias_uteis_estimados = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Dias úteis estimados',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    prazo = models.DateField(null=True, blank=True, verbose_name='Prazo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'missoes'
        ordering = ['status', 'prazo']
        verbose_name = 'Missão'
        verbose_name_plural = 'Missões'

    def __str__(self):
        destino = self.perfil.nome if self.perfil else 'Catálogo'
        return f"{self.titulo} ({destino}) — {self.dificuldade}"


class MissaoAluno(models.Model):
    STATUS_CHOICES = Missao.STATUS_CHOICES
    ORIGEM_GERACAO_CHOICES = [
        ('regra', 'Regra'),
        ('regra+ia', 'Regra + IA'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    missao = models.ForeignKey(
        Missao, on_delete=models.CASCADE, related_name='atribuicoes'
    )
    perfil = models.ForeignKey(
        PerfilAluno, on_delete=models.CASCADE, related_name='missoes_aluno'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    progresso = models.PositiveSmallIntegerField(default=0)
    prioridade = models.PositiveSmallIntegerField(default=0)
    motivo_recomendacao = models.TextField(blank=True)
    origem_geracao = models.CharField(
        max_length=10, choices=ORIGEM_GERACAO_CHOICES, default='regra'
    )
    prazo = models.DateField(null=True, blank=True)
    iniciada_em = models.DateTimeField(null=True, blank=True)
    concluida_em = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'missoes_aluno'
        constraints = [
            models.UniqueConstraint(
                fields=['missao', 'perfil'], name='unique_missao_por_perfil'
            )
        ]
        ordering = ['status', 'created_at']

    def __str__(self):
        return f"{self.perfil.nome} — {self.missao.titulo} ({self.status})"


class ItemPortfolio(models.Model):
    TIPO_CHOICES = [
        ('projeto', 'Projeto'),
        ('certificado', 'Certificado'),
        ('artigo', 'Artigo'),
        ('video', 'Vídeo'),
        ('outro', 'Outro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil = models.ForeignKey(PerfilAluno, on_delete=models.CASCADE, related_name='portfolio')
    titulo = models.CharField(max_length=255, verbose_name='Título')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='projeto')
    url = models.URLField(blank=True, verbose_name='URL')
    descricao = models.TextField(blank=True)
    data = models.DateField(null=True, blank=True, verbose_name='Data de conclusão')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'portfolio_itens'
        ordering = ['-created_at']
        verbose_name = 'Item de Portfólio'
        verbose_name_plural = 'Itens de Portfólio'

    def __str__(self):
        return f"{self.titulo} ({self.tipo}) — {self.perfil.nome}"


class Portfolio(models.Model):
    """Projeto ou coleção de evidências construído por um aluno."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil = models.ForeignKey(
        PerfilAluno, on_delete=models.CASCADE, related_name='portfolios'
    )
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    area = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'portfolios'
        ordering = ['-updated_at']
        indexes = [models.Index(fields=['perfil', '-updated_at'])]

    def __str__(self):
        return f"{self.titulo} ({self.perfil.nome})"


class Evidencia(models.Model):
    """Arquivo ou link que comprova uma entrega do portfólio."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name='evidencias'
    )
    missao_aluno = models.ForeignKey(
        MissaoAluno, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='evidencias'
    )
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    tipo_arquivo = models.CharField(max_length=100)
    arquivo_url = models.URLField(max_length=2048)
    storage_key = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'evidencias'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['portfolio', '-created_at'])]

    def __str__(self):
        return f"{self.titulo} — {self.tipo_arquivo}"


class EvidenciaPortfolio(models.Model):
    """Metadados de um arquivo enviado diretamente para S3/R2."""

    TIPO_CHOICES = [
        ('projeto', 'Projeto'),
        ('certificado', 'Certificado'),
        ('imagem', 'Imagem'),
        ('outro', 'Outro'),
    ]
    ORIGEM_CHOICES = [
        ('missao', 'Missão'),
        ('manual', 'Manual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil = models.ForeignKey(
        PerfilAluno, on_delete=models.CASCADE, related_name='evidencias_portfolio'
    )
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    arquivo_url = models.URLField(max_length=2048, blank=True)
    arquivo_chave = models.CharField(max_length=512, blank=True)
    origem = models.CharField(max_length=10, choices=ORIGEM_CHOICES, default='manual')
    missao_relacionada = models.ForeignKey(
        MissaoAluno, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='evidencias_portfolio'
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'evidencias_portfolio'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['perfil', 'ativo', '-criado_em']),
            models.Index(fields=['arquivo_chave']),
        ]

    def __str__(self):
        return f"{self.titulo} ({self.perfil.nome})"
