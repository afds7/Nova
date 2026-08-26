'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSession } from 'next-auth/react';
import { EvidenceType, usePortfolioStore } from '../../store/usePortfolioStore';

const labels: Record<EvidenceType, string> = {
  projeto: 'Projeto',
  certificado: 'Certificado',
  imagem: 'Imagem',
  outro: 'Outro',
};

export default function PortfolioPage() {
  const { data: session, status } = useSession();
  const profileId = (session?.user as { id?: string } | undefined)?.id;
  const { evidencias, isLoading, error, fetchEvidencias } = usePortfolioStore();
  const [filter, setFilter] = useState<'todos' | EvidenceType>('todos');

  useEffect(() => {
    if (profileId) fetchEvidencias(profileId);
  }, [profileId, fetchEvidencias]);

  const visible = useMemo(
    () => filter === 'todos' ? evidencias : evidencias.filter((item) => item.tipo === filter),
    [evidencias, filter]
  );

  if (status === 'loading') return <main className="min-h-screen bg-slate-50" />;

  return (
    <main className="portfolio-page min-h-screen bg-[#f1f5f9] pb-12">
      <header className="border-b border-slate-100 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col items-start gap-4 px-4 py-4 sm:px-5 sm:py-5 md:flex-row md:items-center md:justify-between md:px-8">
          <div>
            <Link href="/menu" className="text-sm font-bold text-[#2c9be3]">← Voltar ao menu</Link>
            <p className="mt-5 text-xs font-bold uppercase tracking-[0.18em] text-[#2c9be3]">Portfólio</p>
            <h1 className="mt-1 text-3xl font-black text-slate-800 md:text-4xl">O que você já construiu</h1>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">Uma visão organizada das suas entregas, aprendizados e experiências que merecem ser lembrados.</p>
          </div>
          <button type="button" onClick={() => window.print()} className="print:hidden w-full rounded-xl bg-[#2c9be3] px-4 py-3 text-sm font-bold text-white shadow-sm hover:bg-[#2188ca] md:w-auto">Exportar PDF</button>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-4 pt-5 sm:px-5 sm:pt-6 md:px-8 md:pt-8">
        <div className="mb-6 flex flex-wrap items-center gap-2 print:hidden">
          {(['todos', ...Object.keys(labels)] as Array<'todos' | EvidenceType>).map((value) => (
            <button key={value} type="button" onClick={() => setFilter(value)} className={`rounded-full px-4 py-2 text-sm font-bold transition ${filter === value ? 'bg-[#2c9be3] text-white' : 'bg-white text-slate-500 hover:bg-slate-100'}`}>
              {value === 'todos' ? 'Todos' : labels[value]}
            </button>
          ))}
        </div>

        {error && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}
        {isLoading ? <p className="py-12 text-center text-sm text-slate-400">Organizando seu portfólio...</p> : visible.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-2xl text-[#2c9be3]">✦</div>
            <h2 className="mt-4 text-lg font-bold text-slate-800">Ainda não há itens nesta seleção</h2>
            <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-slate-500">Adicione uma entrega ao seu portfólio para começar a construir essa visão.</p>
            <Link href="/menu" className="mt-5 inline-flex rounded-xl bg-[#2c9be3] px-4 py-3 text-sm font-bold text-white print:hidden">Adicionar evidência</Link>
          </div>
        ) : (
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {visible.map((item) => (
              <article key={item.id} className="portfolio-item overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
                {item.arquivo_url && item.tipo === 'imagem' ? (
                  <img src={item.arquivo_url} alt={item.titulo} className="h-52 w-full object-cover" />
                ) : (
                  <div className="flex h-32 items-end bg-gradient-to-br from-blue-50 via-white to-slate-100 p-5"><span className="rounded-full bg-white px-3 py-1.5 text-xs font-bold text-[#2c9be3]">{labels[item.tipo]}</span></div>
                )}
                <div className="p-5">
                  <div className="flex items-start justify-between gap-3"><span className="text-xs font-bold uppercase tracking-wider text-[#2c9be3]">{labels[item.tipo]}</span><time className="text-xs text-slate-400">{new Date(item.criado_em).toLocaleDateString('pt-BR')}</time></div>
                  <h2 className="mt-3 text-lg font-bold leading-snug text-slate-800">{item.titulo}</h2>
                  {item.descricao && <p className="mt-2 line-clamp-4 text-sm leading-relaxed text-slate-500">{item.descricao}</p>}
                  {item.arquivo_url && <a href={item.arquivo_url} target="_blank" rel="noreferrer" className="mt-4 inline-block text-sm font-bold text-[#2c9be3] hover:underline print:hidden">Abrir arquivo ↗</a>}
                </div>
              </article>
            ))}
          </div>
        )}
      </div>

      <style jsx global>{`
        @media print {
          @page { margin: 16mm; }
          body { background: white !important; }
          .portfolio-page { background: white !important; padding-bottom: 0 !important; }
          .portfolio-item { break-inside: avoid; box-shadow: none !important; }
          .portfolio-page header { border-bottom: 1px solid #cbd5e1 !important; }
          .portfolio-page a { color: #1e293b !important; text-decoration: none !important; }
        }
      `}</style>
    </main>
  );
}
