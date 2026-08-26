'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSession, signOut } from 'next-auth/react';
import { useRecommendationsStore, RecommendationType } from '../../store/useRecommendationsStore';

const labels: Record<RecommendationType, string> = {
  curso: 'Cursos',
  faculdade: 'Faculdades',
  livro: 'Livros',
  certificacao: 'Certificações',
  recurso: 'Recursos',
};

const colors: Record<RecommendationType, string> = {
  curso: 'bg-blue-50 text-blue-700',
  faculdade: 'bg-violet-50 text-violet-700',
  livro: 'bg-amber-50 text-amber-700',
  certificacao: 'bg-emerald-50 text-emerald-700',
  recurso: 'bg-slate-100 text-slate-700',
};

export default function RecommendationsPage() {
  const { data: session, status } = useSession();
  const { data, isLoading, error, fetchRecommendations } = useRecommendationsStore();
  const [filter, setFilter] = useState<'todos' | RecommendationType>('todos');
  const profileId = (session?.user as { id?: string } | undefined)?.id;

  useEffect(() => {
    if (status === 'authenticated' && profileId) fetchRecommendations(profileId);
  }, [status, profileId, fetchRecommendations]);

  const visibleItems = useMemo(
    () => data?.itens.filter((item) => filter === 'todos' || item.tipo === filter) || [],
    [data, filter]
  );

  if (status === 'loading' || (isLoading && !data)) {
    return <main className="min-h-screen bg-[#f1f5f9] p-5 md:p-10"><div className="mx-auto max-w-6xl space-y-5"><div className="h-20 animate-pulse rounded-2xl bg-white" /><div className="h-52 animate-pulse rounded-2xl bg-white" /><div className="h-64 animate-pulse rounded-2xl bg-white" /></div></main>;
  }

  if (status === 'unauthenticated') return null;

  return (
    <main className="min-h-screen bg-[#f1f5f9] pb-12">
      <header className="w-full border-b border-slate-100 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-5 sm:py-4 md:px-8">
          <Link href="/menu" className="relative h-24 w-56 overflow-hidden">
            <img src="/logo-nova.png" alt="NOVA Hub" width={650} height={366} className="absolute left-[-220px] top-[-145px] max-w-none" />
          </Link>
          <div className="flex w-full items-center justify-between gap-2 sm:w-auto sm:justify-end sm:gap-3">
            <Link href="/menu" className="rounded-lg bg-slate-100 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-200">Voltar ao menu</Link>
            <button type="button" onClick={() => signOut({ callbackUrl: '/' })} title="Sair" className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200">↪</button>
          </div>
        </div>
      </header>

      <div className="w-full min-w-0 mx-auto max-w-6xl space-y-5 px-4 pt-6 sm:px-5 md:px-8 md:pt-9">
        <section className="rounded-2xl bg-gradient-to-br from-[#2c9be3] to-[#1d81c2] p-6 text-white md:p-9">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-100">Explorar caminhos</p>
          <h1 className="mt-2 text-2xl font-black md:text-4xl">Possibilidades para o seu próximo passo</h1>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-blue-50 md:text-base">
            {data?.resumo || 'Estamos conectando seu perfil profissional a opções de formação, prática e aprofundamento.'}
          </p>
          {data?.area && <span className="mt-5 inline-flex rounded-full border border-white/30 bg-white/15 px-3 py-1.5 text-xs font-bold">Foco atual: {data.area}</span>}
        </section>

        {error && <div className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

        {data && (
          <>
            <section className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm md:p-7">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-xs font-bold uppercase tracking-widest text-[#2c9be3]">Curadoria do seu momento</p>
                  <h2 className="mt-1 text-lg font-bold text-slate-800">Escolha o que vale investigar agora</h2>
                </div>
                {data.competencia_prioritaria && <p className="text-xs text-slate-500">Ponto de atenção: <strong className="text-slate-700">{data.competencia_prioritaria}</strong></p>}
              </div>
              <div className="mt-5 flex gap-2 overflow-x-auto pb-1">
                {(['todos', ...Object.keys(labels)] as Array<'todos' | RecommendationType>).map((value) => (
                  <button key={value} type="button" onClick={() => setFilter(value)} className={`shrink-0 rounded-full px-3 py-2 text-xs font-bold ${filter === value ? 'bg-[#2c9be3] text-white' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}>
                    {value === 'todos' ? 'Tudo' : labels[value]}
                  </button>
                ))}
              </div>
            </section>

            <section className="grid gap-4 md:grid-cols-2">
              {visibleItems.map((item) => (
                <article key={`${item.tipo}-${item.titulo}`} className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm md:p-6">
                  <div className="flex items-start justify-between gap-3">
                    <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold ${colors[item.tipo]}`}>{labels[item.tipo]}</span>
                    {item.nivel && <span className="text-xs font-semibold text-slate-400">{item.nivel}</span>}
                  </div>
                  <h2 className="mt-4 text-lg font-bold leading-snug text-slate-800">{item.titulo}</h2>
                  <p className="mt-2 text-sm leading-relaxed text-slate-500">{item.descricao}</p>
                  <div className="mt-4 rounded-xl bg-slate-50 p-3 text-sm leading-relaxed text-slate-600"><strong className="text-slate-700">Por que pode fazer sentido:</strong> {item.por_que_pode_fazer_sentido}</div>
                  <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                    {item.estimativa_tempo && <span className="text-xs font-semibold text-slate-400">⏱ {item.estimativa_tempo}</span>}
                    {item.url ? <a href={item.url} target="_blank" rel="noreferrer" className="rounded-lg bg-[#2c9be3] px-3 py-2 text-xs font-bold text-white hover:bg-[#2188ca]">Conhecer opção ↗</a> : <span className="text-xs font-semibold text-[#2c9be3]">Ideia para experimentar</span>}
                  </div>
                </article>
              ))}
            </section>

            <section className="rounded-2xl border border-blue-100 bg-blue-50 p-5 md:p-7">
              <p className="text-xs font-bold uppercase tracking-widest text-[#2c9be3]">Para começar sem pressa</p>
              <div className="mt-3 grid gap-2 md:grid-cols-3">{data.proximos_passos.map((step, index) => <div key={step} className="rounded-xl bg-white/80 p-4 text-sm leading-relaxed text-slate-600"><span className="font-black text-[#2c9be3]">0{index + 1}</span><p className="mt-2">{step}</p></div>)}</div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
