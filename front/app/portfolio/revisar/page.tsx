'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { useMissionFlowStore } from '../../../store/useMissionFlowStore';
import { useDashboardStore } from '../../../store/useDashboardStore';

export default function ReviewDraftPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const profileId = (session?.user as { id?: string } | undefined)?.id;
  const { draft, isSubmitting, error, message, publishDraft, loadDraft } = useMissionFlowStore();
  const fetchDashboard = useDashboardStore((state) => state.fetchDashboard);
  const [titulo, setTitulo] = useState('');
  const [descricao, setDescricao] = useState('');
  const [tipo, setTipo] = useState<'projeto' | 'certificado' | 'imagem' | 'outro'>('projeto');

  useEffect(() => {
    if (status === 'unauthenticated') router.replace('/');
  }, [status, router]);

  useEffect(() => {
    if (draft) {
      setTitulo(draft.titulo);
      setDescricao(draft.descricao);
      setTipo(draft.tipo);
    }
  }, [draft]);

  useEffect(() => {
    const evidenceId = new URLSearchParams(window.location.search).get('id');
    if (profileId && evidenceId && (!draft || draft.id !== evidenceId)) loadDraft(profileId, evidenceId);
  }, [profileId, draft, loadDraft]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!profileId || !draft) return;
    await publishDraft(profileId, draft.id, { titulo, descricao, tipo });
    await fetchDashboard(profileId);
    router.push('/menu');
  };

  if (status === 'loading') return <main className="min-h-screen bg-slate-50 p-6" />;

  return (
    <main className="min-h-screen bg-slate-50 px-5 py-8 md:px-8">
      <div className="mx-auto max-w-2xl">
        <button type="button" onClick={() => router.back()} className="mb-6 text-sm font-bold text-[#2c9be3]">← Voltar</button>
        <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm md:p-8">
          <p className="text-xs font-bold uppercase tracking-widest text-[#2c9be3]">Revisar evidência</p>
          <h1 className="mt-2 text-2xl font-black text-slate-800">Deixe este registro com a sua cara</h1>
          <p className="mt-2 text-sm leading-relaxed text-slate-500">A missão criou um rascunho para você revisar. Nada é publicado sem sua confirmação.</p>

          {!draft ? (
            <div className="mt-6 rounded-xl bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">Não há um rascunho selecionado para revisar.</div>
          ) : (
            <form onSubmit={submit} className="mt-6 space-y-4">
              <label className="block text-sm font-bold text-slate-700">Título<input value={titulo} onChange={(event) => setTitulo(event.target.value)} required className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-[#2c9be3]" /></label>
              <label className="block text-sm font-bold text-slate-700">O que você realizou?<textarea value={descricao} onChange={(event) => setDescricao(event.target.value)} rows={6} className="mt-2 w-full resize-none rounded-xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-[#2c9be3]" /></label>
              <label className="block text-sm font-bold text-slate-700">Tipo<select value={tipo} onChange={(event) => setTipo(event.target.value as typeof tipo)} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 font-normal outline-none focus:border-[#2c9be3]"><option value="projeto">Projeto</option><option value="certificado">Certificado</option><option value="imagem">Imagem</option><option value="outro">Outro</option></select></label>
              {error && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}
              {message && <p className="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p>}
              <button type="submit" disabled={isSubmitting} className="w-full rounded-xl bg-[#2c9be3] px-4 py-3.5 text-sm font-bold text-white hover:bg-[#2188ca] disabled:opacity-50">{isSubmitting ? 'Publicando...' : 'Publicar no portfólio'}</button>
            </form>
          )}
        </div>
      </div>
    </main>
  );
}
