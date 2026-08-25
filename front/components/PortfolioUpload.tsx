'use client';

import { DragEvent, FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import { useSession } from 'next-auth/react';
import Link from 'next/link';
import { EvidenceType, usePortfolioStore } from '../store/usePortfolioStore';

const typeLabels: Record<EvidenceType, string> = {
  projeto: 'Projeto',
  certificado: 'Certificado',
  imagem: 'Imagem',
  outro: 'Outro',
};

const acceptedTypes = '.pdf,.png,.jpg,.jpeg,.mp4';

export default function PortfolioUpload() {
  const { data: session } = useSession();
  const profileId = (session?.user as { id?: string } | undefined)?.id;
  const inputRef = useRef<HTMLInputElement>(null);
  const { evidencias, isLoading, uploadProgress, error, fetchEvidencias, uploadEvidencia, inativarEvidencia, clearError } = usePortfolioStore();
  const [file, setFile] = useState<File | null>(null);
  const [titulo, setTitulo] = useState('');
  const [descricao, setDescricao] = useState('');
  const [tipo, setTipo] = useState<EvidenceType>('projeto');
  const [filtro, setFiltro] = useState<'todos' | EvidenceType>('todos');
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    if (profileId) fetchEvidencias(profileId);
  }, [profileId, fetchEvidencias]);

  const visibleEvidence = useMemo(
    () => filtro === 'todos' ? evidencias : evidencias.filter((item) => item.tipo === filtro),
    [evidencias, filtro]
  );
  const filterOptions: Array<'todos' | EvidenceType> = ['todos', ...(Object.keys(typeLabels) as EvidenceType[])];

  const chooseFile = (candidate: File | undefined) => {
    if (!candidate) return;
    clearError();
    setFile(candidate);
    if (!titulo) setTitulo(candidate.name.replace(/\.[^/.]+$/, '').slice(0, 255));
  };

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    chooseFile(event.dataTransfer.files[0]);
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!profileId || !file || !titulo.trim()) return;
    try {
      await uploadEvidencia(profileId, file, { titulo: titulo.trim(), descricao: descricao.trim(), tipo });
      setFile(null);
      setTitulo('');
      setDescricao('');
      if (inputRef.current) inputRef.current.value = '';
    } catch {
      // O erro já fica disponível no store para orientar a pessoa na tela.
    }
  };

  return (
    <section className="md:col-span-2 rounded-2xl border border-slate-100 bg-white p-5 shadow-sm md:p-7">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-widest text-[#2c9be3]">Seu portfólio</p>
          <h2 className="mt-1 text-lg font-bold text-slate-800">Mostre o que você já construiu</h2>
          <p className="mt-1 text-sm text-slate-500">Guarde projetos, certificados e outras evidências do seu caminho.</p>
        </div>
        <div className="flex items-center gap-3"><span className="text-sm font-semibold text-slate-400">{evidencias.length} {evidencias.length === 1 ? 'item' : 'itens'}</span><Link href="/portfolio" className="rounded-lg bg-slate-100 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-200">Ver portfólio completo</Link></div>
      </div>

      <form onSubmit={submit} className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(260px,0.8fr)]">
        <div
          onDragEnter={(event) => { event.preventDefault(); setIsDragging(true); }}
          onDragOver={(event) => event.preventDefault()}
          onDragLeave={() => setIsDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className={`flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-5 py-6 text-center transition-colors ${isDragging ? 'border-[#2c9be3] bg-blue-50' : 'border-slate-200 bg-slate-50 hover:border-blue-300 hover:bg-blue-50/50'}`}
        >
          <input ref={inputRef} type="file" accept={acceptedTypes} className="hidden" onChange={(event) => chooseFile(event.target.files?.[0])} />
          <span className="text-2xl" aria-hidden="true">↑</span>
          <span className="mt-2 text-sm font-bold text-slate-700">Arraste um arquivo ou toque para escolher</span>
          <span className="mt-1 text-xs text-slate-400">PDF, PNG, JPG ou MP4 · até 25 MB</span>
          {file && <span className="mt-3 max-w-full truncate rounded-full bg-white px-3 py-1 text-xs font-semibold text-[#2c9be3]">{file.name}</span>}
        </div>

        <div className="space-y-3">
          <input value={titulo} onChange={(event) => setTitulo(event.target.value)} required maxLength={255} placeholder="Título da evidência" className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-800 outline-none transition focus:border-[#2c9be3]" />
          <textarea value={descricao} onChange={(event) => setDescricao(event.target.value)} maxLength={2000} placeholder="Descrição rápida (opcional)" rows={3} className="w-full resize-none rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-800 outline-none transition focus:border-[#2c9be3]" />
          <div className="flex gap-3">
            <select value={tipo} onChange={(event) => setTipo(event.target.value as EvidenceType)} className="min-w-0 flex-1 rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm text-slate-700 outline-none focus:border-[#2c9be3]">
              {Object.entries(typeLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
            <button type="submit" disabled={!file || !titulo.trim() || uploadProgress !== null} className="rounded-xl bg-[#2c9be3] px-4 py-3 text-sm font-bold text-white transition hover:bg-[#2188ca] disabled:cursor-not-allowed disabled:opacity-50">
              {uploadProgress === null ? 'Adicionar' : `${uploadProgress}%`}
            </button>
          </div>
          {uploadProgress !== null && <div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-[#2c9be3] transition-all" style={{ width: `${uploadProgress}%` }} /></div>}
        </div>
      </form>

      {error && <div className="mt-4 flex items-center justify-between gap-3 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700"><span>{error}</span><button type="button" onClick={clearError} className="font-bold">Fechar</button></div>}

      <div className="mt-7 border-t border-slate-100 pt-5">
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {filterOptions.map((value) => (
            <button key={value} type="button" onClick={() => setFiltro(value)} className={`shrink-0 rounded-full px-3 py-1.5 text-xs font-bold transition ${filtro === value ? 'bg-[#2c9be3] text-white' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}>
              {value === 'todos' ? 'Todos' : typeLabels[value]}
            </button>
          ))}
        </div>

        {isLoading ? <p className="py-8 text-center text-sm text-slate-400">Carregando suas evidências...</p> : visibleEvidence.length === 0 ? <p className="rounded-xl bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">Ainda não há evidências aqui. Que tal começar pelo projeto que mais representa você?</p> : (
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {visibleEvidence.map((item) => (
              <article key={item.id} className="min-w-0 rounded-xl border border-slate-100 p-4">
                <div className="flex items-start justify-between gap-2"><span className="rounded-full bg-blue-50 px-2 py-1 text-[10px] font-bold text-[#2c9be3]">{typeLabels[item.tipo]}</span><button type="button" title="Arquivar evidência" onClick={() => profileId && inativarEvidencia(profileId, item.id)} className="text-xs font-semibold text-slate-400 hover:text-rose-500">Arquivar</button></div>
                {item.tipo === 'imagem' && item.arquivo_url && (
                  <a href={item.arquivo_url} target="_blank" rel="noreferrer" className="mt-3 block overflow-hidden rounded-lg bg-slate-50" aria-label={`Visualizar ${item.titulo}`}>
                    <img src={item.arquivo_url} alt={item.titulo} className="h-36 w-full object-cover transition hover:scale-[1.02]" />
                  </a>
                )}
                <h3 className="mt-3 truncate text-sm font-bold text-slate-800">{item.titulo}</h3>
                {item.descricao && <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-slate-500">{item.descricao}</p>}
                {item.arquivo_url && <a href={item.arquivo_url} target="_blank" rel="noreferrer" className="mt-3 inline-block text-xs font-bold text-[#2c9be3] hover:underline">Abrir arquivo ↗</a>}
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
