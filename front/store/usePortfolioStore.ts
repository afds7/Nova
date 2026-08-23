import { create } from 'zustand';

export type EvidenceType = 'projeto' | 'certificado' | 'imagem' | 'outro';

export interface PortfolioEvidence {
  id: string;
  titulo: string;
  descricao: string;
  tipo: EvidenceType;
  arquivo_url: string;
  arquivo_chave: string;
  origem: 'missao' | 'manual';
  missao_relacionada: string | null;
  ativo: boolean;
  criado_em: string;
}

interface EvidenceDraft {
  titulo: string;
  descricao: string;
  tipo: EvidenceType;
  origem?: 'missao' | 'manual';
  missao_relacionada?: string | null;
}

interface PortfolioState {
  evidencias: PortfolioEvidence[];
  isLoading: boolean;
  uploadProgress: number | null;
  error: string | null;
  fetchEvidencias: (profileId: string) => Promise<void>;
  uploadEvidencia: (profileId: string, file: File, draft: EvidenceDraft) => Promise<void>;
  inativarEvidencia: (profileId: string, evidenceId: string) => Promise<void>;
  clearError: () => void;
}

const apiBase = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const jsonOrError = async (response: Response) => {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || `Erro ${response.status}`);
  return body;
};

export const usePortfolioStore = create<PortfolioState>((set) => ({
  evidencias: [],
  isLoading: false,
  uploadProgress: null,
  error: null,

  fetchEvidencias: async (profileId) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(
        `${apiBase()}/api/portfolio/evidencias/?profile_id=${encodeURIComponent(profileId)}`
      );
      const evidencias = await jsonOrError(response) as PortfolioEvidence[];
      set({ evidencias, isLoading: false });
    } catch (error: unknown) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Não foi possível carregar seu portfólio.',
      });
    }
  },

  uploadEvidencia: async (profileId, file, draft) => {
    set({ uploadProgress: 0, error: null });
    try {
      const startResponse = await fetch(`${apiBase()}/api/portfolio/upload/iniciar/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profile_id: profileId,
          filename: file.name,
          content_type: file.type,
          file_size: file.size,
        }),
      });
      const upload = await jsonOrError(startResponse) as {
        upload_url: string;
        arquivo_chave: string;
        arquivo_url: string;
      };

      await new Promise<void>((resolve, reject) => {
        const request = new XMLHttpRequest();
        request.open('PUT', upload.upload_url);
        request.setRequestHeader('Content-Type', file.type);
        request.upload.onprogress = (event) => {
          if (event.lengthComputable) set({ uploadProgress: Math.round((event.loaded / event.total) * 100) });
        };
        request.onload = () => request.status >= 200 && request.status < 300
          ? resolve()
          : reject(new Error('O arquivo não conseguiu chegar ao storage.'));
        request.onerror = () => reject(new Error('A conexão com o storage foi interrompida.'));
        request.send(file);
      });

      const confirmResponse = await fetch(`${apiBase()}/api/portfolio/evidencias/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profile_id: profileId,
          ...draft,
          arquivo_chave: upload.arquivo_chave,
          arquivo_url: upload.arquivo_url,
        }),
      });
      const evidence = await jsonOrError(confirmResponse) as PortfolioEvidence;
      set((state) => ({
        evidencias: [evidence, ...state.evidencias],
        uploadProgress: null,
      }));
    } catch (error: unknown) {
      set({
        uploadProgress: null,
        error: error instanceof Error ? error.message : 'Não foi possível concluir o upload.',
      });
      throw error;
    }
  },

  inativarEvidencia: async (profileId, evidenceId) => {
    try {
      const response = await fetch(`${apiBase()}/api/portfolio/evidencias/${evidenceId}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_id: profileId, ativo: false }),
      });
      await jsonOrError(response);
      set((state) => ({ evidencias: state.evidencias.filter((item) => item.id !== evidenceId) }));
    } catch (error: unknown) {
      set({ error: error instanceof Error ? error.message : 'Não foi possível arquivar esta evidência.' });
    }
  },

  clearError: () => set({ error: null }),
}));
