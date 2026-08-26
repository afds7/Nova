import os
import logging
import hashlib
import json
import unicodedata
from datetime import timedelta
from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from openai import OpenAI
from tavily import TavilyClient
from django.core.cache import cache
from .models import Missao, MissaoAluno, PerfilAluno

# Recomendação de segurança para substituir o print()
logger = logging.getLogger(__name__)


class MotorDeMissoes:
    """Cria uma trilha persistente de missões específica para cada perfil."""

    LIMITE_SUGESTOES = 3
    NIVEIS_PRIORITARIOS = (1, 2)

    @classmethod
    def sugerir(cls, perfil_id: UUID | str) -> list[Missao]:
        """Compatibilidade: retorna as missões persistidas para o perfil."""
        return [atribuicao.missao for atribuicao in cls.recomendar(perfil_id)]

    @classmethod
    def recomendar(cls, perfil_id: UUID | str) -> list[MissaoAluno]:
        """Retorna até três recomendações persistidas e idempotentes por perfil."""
        perfil = (
            PerfilAluno.objects
            .select_related('objetivo')
            .prefetch_related('competencias', 'historicos_iep')
            .get(pk=perfil_id)
        )

        atuais = list(
            MissaoAluno.objects
            .filter(
                perfil=perfil,
                status__in=('pendente', 'em_andamento'),
                missao__perfil__isnull=True,
            )
            .select_related('missao')
            .order_by('-prioridade', 'created_at')[:cls.LIMITE_SUGESTOES]
        )
        hoje = timezone.localdate()
        for atribuicao in atuais:
            if atribuicao.prazo is None:
                atribuicao.prazo = hoje + timedelta(days=min(7, atribuicao.missao.prazo_dias))
                atribuicao.save(update_fields=['prazo', 'updated_at'])
        if len(atuais) >= cls.LIMITE_SUGESTOES:
            return atuais

        competencias_aluno = {
            cls._normalizar(competencia.nome): competencia.nivel
            for competencia in perfil.competencias.all()
        }
        area = cls._normalizar(getattr(getattr(perfil, 'objetivo', None), 'area_curso', ''))
        iep = max(perfil.historicos_iep.all(), key=lambda item: item.created_at, default=None)
        ja_atribuidas = MissaoAluno.objects.filter(perfil=perfil).values_list('missao_id', flat=True)
        catalogo: QuerySet[Missao] = (
            Missao.objects
            .filter(perfil__isnull=True)
            .exclude(id__in=ja_atribuidas)
        )

        ranqueadas = sorted(catalogo, key=lambda missao: cls._pontuar(missao, competencias_aluno, area, iep), reverse=True)
        faltantes = cls.LIMITE_SUGESTOES - len(atuais)
        with transaction.atomic():
            for missao in ranqueadas[:faltantes]:
                score, motivo = cls._pontuar(missao, competencias_aluno, area, iep, detalhar=True)
                MissaoAluno.objects.create(
                    missao=missao,
                    perfil=perfil,
                    prioridade=score,
                    motivo_recomendacao=motivo,
                    prazo=hoje + timedelta(days=min(7, missao.prazo_dias)),
                )

        return list(
            MissaoAluno.objects
            .filter(perfil=perfil, status__in=('pendente', 'em_andamento'), missao__perfil__isnull=True)
            .select_related('missao')
            .order_by('-prioridade', 'created_at')[:cls.LIMITE_SUGESTOES]
        )

    @staticmethod
    def _normalizar(valor: str) -> str:
        sem_acentos = unicodedata.normalize('NFKD', valor)
        return ''.join(
            caractere for caractere in sem_acentos
            if not unicodedata.combining(caractere)
        ).casefold().strip()

    @classmethod
    def _pontuar(
        cls,
        missao: Missao,
        competencias_aluno: dict[str, int],
        area: str,
        iep: object | None,
        detalhar: bool = False,
    ) -> tuple[int, str] | tuple[int, int, str]:
        competencias_catalogo = missao.competencias_desenvolvidas or []
        if isinstance(competencias_catalogo, dict):
            competencias_catalogo = competencias_catalogo.keys()

        competencias_missao = {
            cls._normalizar(str(competencia)) for competencia in competencias_catalogo
        }
        matches = competencias_missao & set(competencias_aluno)
        score = sum(max(1, 6 - competencias_aluno[nome]) * 100 for nome in matches)
        area_words = set(area.split()) - {'e', 'de', 'da', 'do', 'em'}
        mission_words = set(cls._normalizar(missao.area_relacionada).split())
        score += len(area_words & mission_words) * 35
        if iep is not None and iep.iep_score <= 60:
            score += 15 if missao.dificuldade == 'facil' else 0
        if not matches and not area_words:
            score += 1

        motivo = (
            f"Recomendada porque trabalha {', '.join(sorted(matches))}."
            if matches else
            f"Recomendada para criar experiência prática em {missao.area_relacionada or 'sua área de interesse'}."
        )
        if detalhar:
            return score, motivo
        return score, int(bool(matches)), missao.titulo.casefold()

def build_marketing_copy(iep, iev, area, fraqueza, forca, gap):
    """Constrói o texto determinístico baseado nas regras de Marketing"""

    if iep <= 40:
        iep_text = f"### 🔴 Preparo Estratégico: 0–40 (PRIMEIROS PASSOS)\nSua direção ainda está tomando forma.\nHoje, suas decisões ainda não estão totalmente conectadas a um objetivo em **{area}**, e isso pode tornar o caminho mais difícil.\nO ponto que mais merece atenção agora é **{fraqueza}**.\nCom pequenos passos e mais clareza, você já consegue começar a avançar."
    elif iep <= 60:
        iep_text = f"### 🟡 Preparo Estratégico: 41–60 (GANHANDO CLAREZA)\nVocê já começou a pensar no seu futuro e está organizando as próximas decisões.\nExiste uma intenção de seguir **{area}**, mas ainda dá para conectar melhor seus planos.\nSeu próximo ponto de evolução é **{fraqueza}**.\nCom alguns ajustes, seu caminho pode ficar muito mais consistente."
    elif iep <= 80:
        iep_text = f"### 🔵 Preparo Estratégico: 61–80 (EM EVOLUÇÃO)\nVocê já tem uma boa direção para **{area}**, e suas ações começam a se conectar.\nO próximo ponto para desenvolver é **{fraqueza}**.\nAo fortalecer isso, você amplia suas possibilidades e ganha mais segurança para escolher os próximos passos."
    else:
        iep_text = f"### 🟢 Preparo Estratégico: 81–100 (MOMENTO DE ACELERAR)\nVocê tem uma direção bem alinhada com seu objetivo em **{area}**.\nExiste consistência no que você está construindo, com destaque para **{forca}**.\nAgora, o foco é escolher boas oportunidades e ampliar o impacto do que você já começou."

    if iev <= 40:
        iev_text = f"### 🔴 Vantagem Competitiva: 0–40 (CONSTRUINDO VISIBILIDADE)\nVocê ainda está transformando preparo em sinais concretos dentro de **{area}**.\nO ponto de partida é criar evidências do que você sabe fazer.\nSeu principal foco agora é **{fraqueza}**, para que suas habilidades apareçam com mais clareza."
    elif iev <= 60:
        iev_text = f"### 🟡 Vantagem Competitiva: 41–60 (CRIANDO DIFERENCIAIS)\nVocê já começou a experimentar e construir sinais de diferenciação em **{area}**.\nAgora, vale transformar essas ações em resultados mais visíveis.\nSeu próximo foco é **{fraqueza}**, que pode fortalecer sua presença."
    elif iev <= 80:
        iev_text = f"### 🔵 Vantagem Competitiva: 61–80 (GANHANDO PRESENÇA)\nVocê já demonstra diferenciais reais em **{area}**.\nSua força aparece principalmente em **{forca}**.\nAo desenvolver **{fraqueza}**, você torna essa presença ainda mais consistente."
    else:
        iev_text = f"### 🟢 Vantagem Competitiva: 81–100 (DIFERENCIAL CONSOLIDADO)\nVocê já construiu uma presença relevante em **{area}**.\nSeu posicionamento e suas ações mostram diferenciação, especialmente em **{forca}**.\nAgora, o foco é consolidar e ampliar esse diferencial."

    if iep <= 60 and iev <= 60:
        combo_text = f"### 🧠 SEU MOMENTO: ORGANIZAR A BASE\nVocê está construindo direção e presença em **{area}**. O foco imediato é ganhar clareza, testar possibilidades e transformar esforço em aprendizados concretos."
    elif iep > 60 and iev <= 60:
        combo_text = f"### 🧠 SEU MOMENTO: TRANSFORMAR PREPARO EM PRÁTICA\nVocê já tem uma boa base, e o próximo passo em **{area}** é mostrar isso em projetos e experiências reais."
    elif iep <= 60 and iev > 60:
        combo_text = f"### 🧠 SEU MOMENTO: CONECTAR IDEIAS E DIREÇÃO\nVocê já tem iniciativa e diferenciais em **{area}**. Agora, o foco é alinhar suas ações a um objetivo claro para aproveitar melhor seu potencial."
    else:
        combo_text = f"### 🧠 SEU MOMENTO: AMPLIAR IMPACTO\nVocê combina preparo e diferenciais em **{area}**. Agora, o foco é escolher oportunidades alinhadas e ampliar o impacto do que você está construindo."

    direcao_text = f"### 🎯 PRÓXIMOS PASSOS\nPara evoluir em **{area}**, vale focar em:\n1. Desenvolver {fraqueza}\n2. Usar {forca} a seu favor\n3. Aproximar seu preparo da sua prática ({gap} pontos)"

    return f"{combo_text}\n\n{iep_text}\n\n{iev_text}\n\n{direcao_text}"


def generate_action_plan(data):
    cache_input = {
        key: data.get(key)
        for key in ('area', 'iep_score', 'iev_score', 'diagnostic', 'strongest_point', 'weakest_point', 'gap')
    }
    cache_digest = hashlib.sha256(
        json.dumps(cache_input, ensure_ascii=False, sort_keys=True, default=str).encode('utf-8')
    ).hexdigest()
    cache_key = f'nova:assessment:plan:v1:{cache_digest}'
    cached_plan = cache.get(cache_key)
    if cached_plan:
        logger.info('[CACHE] Plano de diagnóstico reutilizado | chave=%s', cache_digest[:12])
        return cached_plan

    raw_area = data.get('area', '').strip().lower()
    fraqueza = data.get('weakest_point', 'falta de estratégia')
    forca = data.get('strongest_point', 'vontade de aprender')

    # 1. INTERCEPTADOR DE INDECISÃO
    undecided_keywords = ['não sei', 'nao sei', 'indeciso', 'nenhuma', 'dúvida', 'qualquer', 'ainda não sei', 'indefinido']
    is_undecided = not raw_area or any(kw in raw_area for kw in undecided_keywords)

    area_for_copy = "sua futura área" if is_undecided else data.get('area')

    # 2. Gera a copy determinística do marketing
    marketing_copy = build_marketing_copy(
        iep=data['iep_score'], iev=data['iev_score'], area=area_for_copy,
        fraqueza=fraqueza, forca=forca, gap=data['gap']
    )

    # 3. Busca do Tavily Dinâmica (Agora buscando Faculdades e Cursos ativamente)
    search_context = ""
    try:
        if is_undecided:
            search_query = "melhores testes vocacionais profissionais, faculdades com grade flexível e cursos de mapeamento de carreira no Brasil 2026"
        else:
            search_query = f"melhores faculdades, cursos de elite, certificações e materiais avançados para profissionais de {area_for_copy} no Brasil 2026"

        tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        search_result = tavily_client.search(
            query=search_query, search_depth="basic", max_results=3
        )
        search_context = "\n".join([f"- {res['title']}: {res['url']}" for res in search_result['results']])
    except Exception:
        search_context = "Foque em pesquisar ativamente universidades de ponta e certificações reconhecidas na área."

    # Regras de ferro para a formatação do markdown
    anti_codeblock_rule = "\n\nIMPORTANTE: Retorne o texto DIRETAMENTE, sem envolver a resposta em blocos de código (não use ```markdown ou ```)."

    # NOVA REGRA MISTA: Autoridade + Nomes Reais de Instituições
    anti_cliche_rule = """
        - Se o gargalo for "Posicionamento e Networking", É PROIBIDO sugerir "participar de eventos/webinars". Traduza para "Autoridade Silenciosa": criar ativos de alto valor (artigos, portfólio técnico).
        - Ao recomendar educação, NUNCA diga genericamente "faça um curso". Você DEVE citar NOMES REAIS de faculdades referência, certificações internacionais ou livros específicos do setor.
    """

    # 4. Prompt Dinâmico
    if is_undecided:
        prompt = f"""
        O estudante está INDECISO.
        Sua maior Força atual: **{forca}**.
        Seu principal ponto de desenvolvimento: **{fraqueza}**.

        Contexto de mercado: {search_context}

        Crie um plano tático DIRETO E RETO. REGRAS OBRIGATÓRIAS:
        - PROIBIDO sugerir "fazer networking básico" ou "dar um Google".{anti_cliche_rule}

        Formato obrigatório em Markdown (### para títulos):

        ### ⚡ Ações Imediatas (Próximos 7 dias)
        (3 micro-experimentações práticas para descobrir afinidades).
        ### 🎯 Curto Prazo (3 meses)
        (3 metas focadas em testar habilidades generalistas, usando a força dele em {forca}).
        ### 🚀 Visão Estratégica (1 ano)
        (Como criar uma "T-shaped skill" e não ficar para trás enquanto decide).
        ### 🎓 Formação e Materiais
        (Indique links de faculdades com grades inovadoras, testes de perfil sérios ou livros de autoconhecimento. É OBRIGATÓRIO usar o formato: [Nome da Instituição/Material](https://www.link.com)).{anti_codeblock_rule}
        """
    else:
        prompt = f"""
        O estudante quer dominar a área de: **{area_for_copy}**.
        Sua maior Força atual: **{forca}**.
        Seu principal ponto de desenvolvimento: **{fraqueza}**.

        Contexto de mercado: {search_context}

        Crie um plano de ataque TÁTICO, DIRETO E ESPECÍFICO. REGRAS OBRIGATÓRIAS:
        - Entregue conselhos nível "Engenharia Reversa" de mercado.{anti_cliche_rule}

        Formato obrigatório em Markdown:

        ### ⚡ Ações Imediatas (Próximos 7 dias)
        (3 ações não-óbvias baseadas no contexto do mercado atual).
        ### 🎯 Curto Prazo (3 meses)
        (3 metas de projeto ou estudo avançado focadas no desenvolvimento de {fraqueza}).
        ### 🚀 Visão Estratégica (1 ano)
        (Como se blindar na área de {area_for_copy} criando vantagem competitiva usando a força dele em {forca}).
        ### 🎓 Formação e Materiais (Links Reais)
        (Indique pelo menos 1 Faculdade Referência, 1 Curso de Elite/Certificação e 1 Material/Livro obrigatório para a área de {area_for_copy}. É OBRIGATÓRIO usar o formato: [Nome da Instituição/Material](https://www.link.com)).{anti_codeblock_rule}
    """

    try:
        openai_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            # O diagnóstico é interativo; o fallback precisa chegar antes do timeout do proxy.
            timeout=float(os.getenv('OPENAI_ASSESSMENT_TIMEOUT_SECONDS', '3')),
            max_retries=0,
        )
        response = openai_client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-5.6-luna'),
            messages=[
                {
                    "role": "system",
                    "content": "Você é um Diretor Executivo focado em carreira. Você é direto, odeia conselhos motivacionais genéricos e foca apenas no que gera resultado real. Quando fala de estudo, indica as melhores faculdades e cursos nominais, sem enrolação."
                },
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=850
        )

        # 1. Tratamento da resposta da IA
        ai_plan = response.choices[0].message.content
        ai_plan = ai_plan.replace("```markdown", "").replace("```", "").strip()

        # 2. Extração de Tokens da API
        usage = response.usage
        prompt_tokens = getattr(usage, 'prompt_tokens', 0) if usage else 0
        completion_tokens = getattr(usage, 'completion_tokens', 0) if usage else 0
        total_tokens = getattr(usage, 'total_tokens', 0) if usage else 0

        # 3. Métricas de uso do modelo configurado
        cost_input = (prompt_tokens / 1_000_000) * 0.15
        cost_output = (completion_tokens / 1_000_000) * 0.60
        total_cost_usd = cost_input + cost_output

        # 4. Auditoria e Logging Estruturado
        lead_email = data.get('email', 'unknown_lead')
        logger.info(
            f"[OPENAI_METRICS] Lead: {lead_email} | "
            f"Tokens: {total_tokens} (In: {prompt_tokens}, Out: {completion_tokens}) | "
            f"Custo USD: ${total_cost_usd:.6f}"
        )

        final_plan = f"{marketing_copy}\n\n---\n\n{ai_plan}"
        cache.set(cache_key, final_plan, 15 * 60)
        return final_plan

    except Exception as e:
        logger.error(f"Erro na geração do plano de ação (OpenAI): {e}", exc_info=True)
        cache.set(cache_key, marketing_copy, 60)
        return marketing_copy
