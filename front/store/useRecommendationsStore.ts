import { create } from 'zustand';

export type RecommendationType = 'curso' | 'faculdade' | 'livro' | 'certificacao' | 'recurso';

export interface RecommendationItem {
  tipo: RecommendationType;
  titulo: string;
  descricao: string;
  o_que_fazer: string;
  como_fazer: string;
  opcoes: string[];
  por_que_pode_fazer_sentido: string;
  url: string;
  nivel: string;
  estimativa_tempo: string;
  custo?: string;
  alcance?: string;
  modalidade?: string;
}

export interface RecommendationsData {
  perfil_id: string;
  area: string;
  competencia_prioritaria: string | null;
  origem: 'ia' | 'fallback';
  resumo: string;
  itens: RecommendationItem[];
  proximos_passos: string[];
  comunidades: string[];
}

interface RecommendationsState {
  data: RecommendationsData | null;
  isLoading: boolean;
  error: string | null;
  fetchRecommendations: (profileId: string) => Promise<void>;
}

const apiBase = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function normalizeRecommendations(body: Partial<RecommendationsData>): RecommendationsData {
  return {
    perfil_id: String(body.perfil_id || ''),
    area: String(body.area || ''),
    competencia_prioritaria: body.competencia_prioritaria || null,
    origem: body.origem === 'ia' ? 'ia' : 'fallback',
    resumo: String(body.resumo || ''),
    itens: Array.isArray(body.itens) ? body.itens.map((item) => ({
      tipo: item.tipo || 'recurso',
      titulo: String(item.titulo || 'Sugestão para explorar'),
      descricao: String(item.descricao || ''),
      o_que_fazer: String(item.o_que_fazer || item.descricao || ''),
      como_fazer: String(item.como_fazer || 'Compare esta opção com outras e faça um primeiro teste antes de decidir.'),
      opcoes: Array.isArray(item.opcoes) ? item.opcoes.map(String) : [],
      por_que_pode_fazer_sentido: String(item.por_que_pode_fazer_sentido || ''),
      url: String(item.url || ''),
      nivel: String(item.nivel || 'todos'),
      estimativa_tempo: String(item.estimativa_tempo || ''),
      custo: item.custo ? String(item.custo) : undefined,
      alcance: item.alcance ? String(item.alcance) : undefined,
      modalidade: item.modalidade ? String(item.modalidade) : undefined,
    })) : [],
    proximos_passos: Array.isArray(body.proximos_passos) ? body.proximos_passos.map(String) : [],
    comunidades: Array.isArray(body.comunidades) ? body.comunidades.map(String) : [],
  };
}

export const useRecommendationsStore = create<RecommendationsState>((set) => ({
  data: null,
  isLoading: false,
  error: null,

  fetchRecommendations: async (profileId) => {
    set({ data: null, isLoading: true, error: null });
    try {
      const response = await fetch(
        `${apiBase()}/api/recomendacoes/?profile_id=${encodeURIComponent(profileId)}&_=${Date.now()}`,
        { cache: 'no-store' }
      );
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.error || `Erro ${response.status}`);
      set({ data: normalizeRecommendations(body as Partial<RecommendationsData>), isLoading: false });
    } catch (error: unknown) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Não foi possível carregar suas sugestões.',
      });
    }
  },
}));
