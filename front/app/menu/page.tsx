'use client';

import { useEffect } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useDashboardStore, CompetencyScore } from '../../store/useDashboardStore';
import PortfolioUpload from '../../components/PortfolioUpload';
import NovaLogo from '../../components/NovaLogo';
import { useMissionFlowStore } from '../../store/useMissionFlowStore';

// ── Helpers ────────────────────────────────────────────────────────────────

function getDiagnosticStyle(diagnostic: string) {
  if (diagnostic.includes('Alto Risco') || diagnostic.includes('Hora de organizar') || diagnostic.includes('Crítico'))
    return { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-600', dot: 'bg-red-500' };
  if (diagnostic.includes('Atenção') || diagnostic.includes('Alerta') || diagnostic.includes('Potencial sem direção'))
    return { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-600', dot: 'bg-amber-500' };
  if (diagnostic.includes('Desenvolvimento') || diagnostic.includes('Potencial') || diagnostic.includes('Boa base'))
    return { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-600', dot: 'bg-blue-500' };
  return { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-600', dot: 'bg-emerald-500' };
}

function CompetencyBar({ competency, isPriority }: { competency: CompetencyScore; isPriority: boolean }) {
  const pct = (competency.nivel / 5) * 100;
  const color = isPriority
    ? 'bg-orange-400'
    : competency.nivel >= 4
    ? 'bg-emerald-400'
    : competency.nivel >= 3
    ? 'bg-blue-400'
    : 'bg-slate-300';

  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-center">
        <span className="text-sm font-medium text-slate-700 flex items-center gap-1.5">
          {isPriority && <span className="text-orange-500 text-xs">⚡</span>}
          {competency.nome}
        </span>
        <span className="text-xs font-bold text-slate-500">{competency.nivel}/5</span>
      </div>
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className={`h-full rounded-full ${color}`}
        />
      </div>
    </div>
  );
}

function IEPDelta({ delta }: { delta: number | null }) {
  if (delta === null) return <span className="text-xs text-slate-400">Primeiro check-in</span>;
  const wholePointDelta = Math.floor(Number(delta));

  // Pequenas evoluções ficam no cálculo interno, mas só ganham destaque ao completar 1 ponto.
  if (wholePointDelta < 1) return null;

  return (
    <span className="text-xs font-bold flex items-center gap-0.5 text-emerald-600">
      ↑ {wholePointDelta} {wholePointDelta === 1 ? 'ponto' : 'pontos'} desde o último check-in
    </span>
  );
}

// ── Skeleton ───────────────────────────────────────────────────────────────

function SkeletonCard({ h = 'h-28' }: { h?: string }) {
  return (
    <div className={`${h} bg-white rounded-2xl border border-slate-100 animate-pulse`} />
  );
}

// ── Page ───────────────────────────────────────────────────────────────────

export function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const { concludeMission, isSubmitting: isCompletingMission, error: missionError } = useMissionFlowStore();
  const { data, suggestedMissions, isLoading, error, fetchDashboard } = useDashboardStore();
  const userId = (session?.user as { id?: string } | undefined)?.id;

  // Proteção de rota
  useEffect(() => {
    if (status === 'unauthenticated') router.replace('/');
  }, [status, router]);

  // Carrega dados ao montar
  useEffect(() => {
    if (status === 'authenticated' && userId && !data) {
      fetchDashboard(userId);
    }
  }, [status, userId, data, fetchDashboard]);

  if (status === 'loading' || (isLoading && !data)) {
    return (
      <main className="min-h-screen bg-[#f1f5f9] p-5 md:p-8 max-w-6xl mx-auto space-y-4 md:space-y-6">
        <div className="h-14 bg-white rounded-2xl animate-pulse" />
        <SkeletonCard h="h-36" />
        <SkeletonCard h="h-48" />
        <SkeletonCard />
        <SkeletonCard />
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-[#f1f5f9] flex items-center justify-center p-5">
        <div className="text-center space-y-4">
          <div className="text-4xl">⚠️</div>
          <p className="text-slate-600 font-medium">{error}</p>
          <button
            onClick={() => userId && fetchDashboard(userId)}
            className="px-6 py-2.5 bg-[#2c9be3] text-white font-bold rounded-xl text-sm"
          >
            Tentar novamente
          </button>
        </div>
      </main>
    );
  }

  if (!data) return null;

  const diagStyle = getDiagnosticStyle(data.diagnostic);
  const firstName = data.student_name.split(' ')[0];
  const missionPct = data.mission_stats.total > 0
    ? Math.round((data.mission_stats.concluidas / data.mission_stats.total) * 100)
    : 0;

  const completeMission = async (missionId: string) => {
    if (!userId || isCompletingMission) return;
    try {
      const draft = await concludeMission(userId, missionId);
      await fetchDashboard(userId);
      router.push(`/portfolio/revisar?id=${draft.id}`);
    } catch {
      // O estado de erro do store permanece visível no bloco de missões.
    }
  };

  return (
    <main className="w-full min-w-0 min-h-screen overflow-x-hidden bg-[#f1f5f9] pb-10">

      {/* ── Header ──────────────────────────────────────────────────── */}
      <header className="w-full bg-white border-b border-slate-100 sticky top-0 z-20">
        <div className="w-full min-w-0 max-w-6xl mx-auto px-4 sm:px-5 md:px-8 lg:px-10 py-3 sm:py-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <NovaLogo />
          <div className="flex w-full items-center justify-end gap-2 sm:w-auto sm:gap-3">
            <button type="button" onClick={() => router.push('/recomendacoes')} className="rounded-lg bg-blue-50 px-2.5 py-2 text-[11px] font-bold text-[#2c9be3] hover:bg-blue-100 sm:px-3 sm:text-xs">
              Ver sugestões
            </button>
            <div className="text-right">
              <p className="text-sm font-bold text-slate-800 leading-none">{firstName}</p>
              <p className="text-xs text-slate-400 mt-0.5">{data.objective_area || 'Objetivo ainda não definido'}</p>
            </div>
            <button
              onClick={() => signOut({ callbackUrl: '/' })}
              title="Sair"
              className="w-9 h-9 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center transition-colors cursor-pointer"
            >
              <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto w-full px-4 sm:px-5 md:px-8 lg:px-10 pt-5 md:pt-8 grid md:grid-cols-2 gap-5 md:gap-6 items-start">

        {/* ── Card IEP ──────────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className={`rounded-2xl border-2 p-5 md:p-7 md:col-span-1 ${diagStyle.bg} ${diagStyle.border}`}
        >
          <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
            <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Seu preparo</p>
              <div className="flex items-baseline gap-1.5">
                <span className={`text-5xl font-black ${diagStyle.text}`}>{Math.round(Number(data.iep_score))}</span>
                <span className="text-slate-400 text-sm">/100</span>
              </div>
              <div className="mt-1.5">
                <IEPDelta delta={data.iep_delta} />
              </div>
              <p className="mt-2 max-w-[15rem] text-[11px] leading-relaxed text-slate-500">Leitura atual com base nas últimas ações registradas.</p>
            </div>
            <div className="text-left sm:text-right">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Seu diferencial</p>
              <div className="flex items-baseline gap-1 justify-end">
                <span className="text-3xl font-black text-slate-700">{data.iev_score}</span>
                <span className="text-slate-400 text-xs">/100</span>
              </div>
              <div className={`inline-flex items-center gap-1.5 mt-2 px-3 py-1 rounded-full text-xs font-bold ${diagStyle.bg} border ${diagStyle.border} ${diagStyle.text}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${diagStyle.dot}`} />
                {data.diagnostic}
              </div>
            </div>
          </div>
        </motion.div>

        {/* ── Próximo Foco ──────────────────────────────────────────── */}
        {data.next_focus && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.08 }}
            className="bg-gradient-to-br from-[#2c9be3] to-[#1d81c2] rounded-2xl p-5 md:p-7 text-white md:col-span-1"
          >
            <div className="flex items-center gap-2 mb-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span className="text-xs font-bold uppercase tracking-widest text-blue-100">Seu próximo passo</span>
            </div>
            <p className="text-sm font-medium text-blue-50 leading-relaxed">{data.next_focus.mensagem}</p>
            {data.next_focus.competencia && (
              <div className="mt-3 inline-flex items-center gap-2 bg-white/20 border border-white/30 rounded-xl px-3 py-1.5">
                <span className="text-white text-xs font-bold">{data.next_focus.competencia}</span>
                <span className="text-blue-200 text-xs">nível {data.next_focus.nivel_atual}/5</span>
              </div>
            )}
          </motion.div>
        )}

        {/* ── Competências ──────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.14 }}
          className="bg-white rounded-2xl border border-slate-100 p-5 md:p-7 shadow-sm md:col-span-1"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-slate-800">Suas competências</h2>
            <span className="text-xs text-slate-400">{data.competency_scores.length} no radar</span>
          </div>

          {data.competency_scores.length === 0 ? (
            <p className="text-sm text-slate-400 text-center py-4">
              Ainda não temos competências no seu radar.
            </p>
          ) : (
            <div className="space-y-4">
              {data.competency_scores.map((c) => (
                <CompetencyBar
                  key={c.id}
                  competency={c}
                  isPriority={data.priority_competency?.id === c.id}
                />
              ))}
            </div>
          )}

          {data.priority_competency && (
            <div className="mt-4 pt-4 border-t border-slate-100 flex items-center gap-2">
              <span className="text-orange-500 text-sm">⚡</span>
              <span className="text-xs text-slate-500">
                Vale focar agora em: <strong className="text-slate-700">{data.priority_competency.nome}</strong>
              </span>
            </div>
          )}
        </motion.div>

        {/* ── Missões ───────────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="bg-white rounded-2xl border border-slate-100 p-5 md:p-7 shadow-sm md:col-span-1"
        >
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-bold text-slate-800">Em ação</h2>
            <span className="text-xs font-bold text-[#2c9be3]">
              {data.mission_stats.concluidas}/{data.mission_stats.total}
            </span>
          </div>

          {data.mission_stats.total === 0 ? (
            <p className="text-sm text-slate-400 text-center py-3">Você ainda não começou nenhuma missão.</p>
          ) : (
            <>
              {/* Barra de progresso */}
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden mb-3">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${missionPct}%` }}
                  transition={{ duration: 0.9, ease: 'easeOut', delay: 0.3 }}
                  className="h-full rounded-full bg-[#2c9be3]"
                />
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-2 mb-4">
                {[
                  { label: 'Pendentes', value: data.mission_stats.pendentes, color: 'text-slate-500' },
                  { label: 'Em andamento', value: data.mission_stats.em_andamento, color: 'text-amber-500' },
                  { label: 'Concluídas', value: data.mission_stats.concluidas, color: 'text-emerald-500' },
                ].map((s) => (
                  <div key={s.label} className="text-center bg-slate-50 rounded-xl p-2">
                    <div className={`text-xl font-black ${s.color}`}>{s.value}</div>
                    <div className="text-[10px] text-slate-400 font-medium">{s.label}</div>
                  </div>
                ))}
              </div>

              {/* Lista de próximas */}
              {data.upcoming_missions.length > 0 && (
                <div className="space-y-2">
                  {data.upcoming_missions.map((m) => (
                    <div key={m.id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl">
                      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                        m.status === 'em_andamento' ? 'bg-amber-400' : 'bg-slate-300'
                      }`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-700 truncate">{m.titulo}</p>
                        {m.prazo && (
                          <p className="text-xs text-slate-400">Prazo: {new Date(m.prazo).toLocaleDateString('pt-BR')}</p>
                        )}
                      </div>
                      <button type="button" onClick={() => completeMission(m.id)} disabled={isCompletingMission} className="shrink-0 rounded-lg bg-blue-50 px-2.5 py-1.5 text-[10px] font-bold text-[#2c9be3] hover:bg-blue-100 disabled:opacity-50">
                        Concluir
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </motion.div>

        {/* ── Missões recomendadas ──────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.24 }}
          className="bg-white rounded-2xl border border-slate-100 p-5 md:p-7 shadow-sm md:col-span-2"
        >
          <div className="flex items-start justify-between gap-3 mb-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-[#2c9be3]">Motor de Missões</p>
              <h2 className="text-base font-bold text-slate-800 mt-1">Desafios que fazem sentido para você</h2>
            </div>
            <span className="shrink-0 rounded-full bg-blue-50 px-2.5 py-1 text-xs font-bold text-[#2c9be3]">
              {suggestedMissions.length} sugestões
            </span>
          </div>

          {suggestedMissions.length === 0 ? (
            <p className="rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-500">
              Estamos preparando desafios que combinam com seu momento.
            </p>
          ) : (
            <div className="space-y-3">
              {suggestedMissions.map((mission) => (
                <article key={mission.id} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="min-w-0 text-sm font-bold leading-snug text-slate-800">{mission.titulo}</h3>
                    <span className="shrink-0 text-[10px] font-bold uppercase tracking-wide text-slate-400">
                      {mission.dificuldade === 'facil' ? 'Fácil' : mission.dificuldade === 'dificil' ? 'Difícil' : 'Média'}
                    </span>
                  </div>
                  {mission.descricao && (
                    <p className="mt-2 text-xs leading-relaxed text-slate-500">{mission.descricao}</p>
                  )}
                  <p className="mt-2 text-xs font-medium leading-relaxed text-[#2c9be3]">
                    Uma missão que pode ajudar por aqui: {mission.motivo_recomendacao}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2 text-[10px] font-semibold text-slate-500">
                    <span className="rounded-full bg-white px-2 py-1">
                      ⏱ {mission.duracao_estimada_minutos} min
                    </span>
                    <span className="rounded-full bg-white px-2 py-1">
                      Prazo: até {mission.prazo_dias} dias
                    </span>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    <span className="rounded-full bg-blue-50 px-2 py-1 text-[10px] font-semibold text-[#2c9be3]">
                      Foco: {mission.competencia_alvo}
                    </span>
                    {mission.area_relacionada && (
                      <span className="rounded-full bg-white px-2 py-1 text-[10px] font-semibold text-[#2c9be3]">
                        {mission.area_relacionada}
                      </span>
                    )}
                    {mission.competencias_desenvolvidas.slice(0, 3).map((competencia) => (
                      <span key={competencia} className="rounded-full bg-white px-2 py-1 text-[10px] font-medium text-slate-500">
                        {competencia}
                      </span>
                    ))}
                  </div>
                  <button type="button" onClick={() => completeMission(mission.id)} disabled={isCompletingMission} className="mt-4 w-full rounded-lg bg-[#2c9be3] px-3 py-2 text-xs font-bold text-white hover:bg-[#2188ca] disabled:opacity-50">
                    {isCompletingMission ? 'Registrando...' : 'Marcar como concluída'}
                  </button>
                </article>
              ))}
            </div>
          )}
        </motion.div>

        {/* ── Portfólio & Experiências ───────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.26 }}
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:gap-6 md:col-span-2"
        >
          {[
            {
              label: 'Portfólio',
              value: data.portfolio_count,
              unit: 'itens',
              icon: (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              ),
              color: 'text-purple-500 bg-purple-50',
            },
            {
              label: 'Experiências',
              value: data.experience_count,
              unit: 'registradas',
              icon: (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              ),
              color: 'text-teal-500 bg-teal-50',
            },
          ].map((card) => (
            <div key={card.label} className="bg-white rounded-2xl border border-slate-100 p-4 shadow-sm">
              <div className={`w-9 h-9 rounded-xl ${card.color} flex items-center justify-center mb-3`}>
                {card.icon}
              </div>
              <div className="text-3xl font-black text-slate-800">{card.value}</div>
              <div className="text-xs text-slate-400 font-medium mt-0.5">{card.unit}</div>
              <div className="text-xs font-bold text-slate-600 mt-1">{card.label}</div>
            </div>
          ))}
        </motion.div>

        {missionError && <div className="md:col-span-2 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{missionError}</div>}

        {data.rascunho_evidencia_pendente && (
          <div className="md:col-span-2 flex flex-col gap-3 rounded-xl border border-blue-100 bg-blue-50 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-[#2c9be3]">Próximo registro</p>
              <p className="mt-1 text-sm text-slate-700">Seu rascunho <strong>{data.rascunho_evidencia_pendente.titulo}</strong> está esperando sua revisão.</p>
            </div>
            <button type="button" onClick={() => router.push(`/portfolio/revisar?id=${data.rascunho_evidencia_pendente?.id}`)} className="shrink-0 rounded-lg bg-[#2c9be3] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#2188ca]">Revisar rascunho</button>
          </div>
        )}

        <PortfolioUpload />

      </div>
    </main>
  );
}

export default DashboardPage;
