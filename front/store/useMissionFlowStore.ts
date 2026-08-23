import { create } from 'zustand';

export interface EvidenceDraft {
  id: string;
  titulo: string;
  descricao: string;
  tipo: 'projeto' | 'certificado' | 'imagem' | 'outro';
  arquivo_url: string;
  arquivo_chave: string;
  origem: 'missao' | 'manual';
  missao_relacionada: string | null;
  ativo: boolean;
  criado_em: string;
}

interface MissionFlowState {
  draft: EvidenceDraft | null;
  isSubmitting: boolean;
  error: string | null;
  message: string | null;
  loadDraft: (profileId: string, evidenceId: string) => Promise<void>;
  concludeMission: (profileId: string, missionId: string) => Promise<EvidenceDraft>;
  publishDraft: (profileId: string, evidenceId: string, data: Partial<EvidenceDraft>) => Promise<void>;
  clear: () => void;
}

const apiBase = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function readResponse(response: Response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || `Erro ${response.status}`);
  return body;
}

export const useMissionFlowStore = create<MissionFlowState>((set) => ({
  draft: null,
  isSubmitting: false,
  error: null,
  message: null,

  concludeMission: async (profileId, missionId) => {
    set({ isSubmitting: true, error: null, message: null });
    try {
      const response = await fetch(`${apiBase()}/api/missoes/${missionId}/concluir/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_id: profileId }),
      });
      const body = await readResponse(response);
      const draft = body.evidence_draft as EvidenceDraft;
      set({ draft, isSubmitting: false, message: body.message });
      return draft;
    } catch (error: unknown) {
      set({ isSubmitting: false, error: error instanceof Error ? error.message : 'Não foi possível registrar essa ação.' });
      throw error;
    }
  },

  publishDraft: async (profileId, evidenceId, data) => {
    set({ isSubmitting: true, error: null });
    try {
      const response = await fetch(`${apiBase()}/api/portfolio/evidencias/${evidenceId}/publicar/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_id: profileId, ...data }),
      });
      const published = await readResponse(response) as EvidenceDraft;
      set({ draft: published, isSubmitting: false, message: 'Evidência publicada no seu portfólio.' });
    } catch (error: unknown) {
      set({ isSubmitting: false, error: error instanceof Error ? error.message : 'Não foi possível publicar a evidência.' });
      throw error;
    }
  },

  loadDraft: async (profileId, evidenceId) => {
    set({ isSubmitting: true, error: null });
    try {
      const response = await fetch(`${apiBase()}/api/portfolio/evidencias/${evidenceId}/?profile_id=${encodeURIComponent(profileId)}`);
      const draft = await readResponse(response) as EvidenceDraft;
      set({ draft, isSubmitting: false });
    } catch (error: unknown) {
      set({ isSubmitting: false, error: error instanceof Error ? error.message : 'Não foi possível carregar o rascunho.' });
    }
  },

  clear: () => set({ draft: null, isSubmitting: false, error: null, message: null }),
}));
