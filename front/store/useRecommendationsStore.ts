import { create } from 'zustand';

export type RecommendationType = 'curso' | 'faculdade' | 'livro' | 'certificacao' | 'recurso';

export interface RecommendationItem {
  tipo: RecommendationType;
  titulo: string;
  descricao: string;
  por_que_pode_fazer_sentido: string;
  url: string;
  nivel: string;
  estimativa_tempo: string;
}

export interface RecommendationsData {
  perfil_id: string;
  area: string;
  competencia_prioritaria: string | null;
  origem: 'ia' | 'fallback';
  resumo: string;
  itens: RecommendationItem[];
  proximos_passos: string[];
}

interface RecommendationsState {
  data: RecommendationsData | null;
  isLoading: boolean;
  error: string | null;
  fetchRecommendations: (profileId: string) => Promise<void>;
}

const apiBase = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const useRecommendationsStore = create<RecommendationsState>((set) => ({
  data: null,
  isLoading: false,
  error: null,

  fetchRecommendations: async (profileId) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${apiBase()}/api/recomendacoes/?profile_id=${encodeURIComponent(profileId)}`);
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.error || `Erro ${response.status}`);
      set({ data: body as RecommendationsData, isLoading: false });
    } catch (error: unknown) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Não foi possível carregar suas sugestões.',
      });
    }
  },
}));
