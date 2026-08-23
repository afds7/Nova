import { create } from 'zustand';

// ── Tipos ──────────────────────────────────────────────────────────────────

export interface CompetencyScore {
  id: string;
  nome: string;
  nivel: number; // 1–5
}

export interface MissionStats {
  total: number;
  concluidas: number;
  em_andamento: number;
  pendentes: number;
}

export interface UpcomingMission {
  id: string;
  titulo: string;
  status: 'pendente' | 'em_andamento';
  prazo: string | null;
}

export interface MissionSuggestion {
  id: string;
  titulo: string;
  descricao: string;
  area_relacionada: string;
  competencias_desenvolvidas: string[];
  dificuldade: 'facil' | 'media' | 'dificil';
  duracao_estimada_minutos: number;
  prazo_dias: number;
  dias_uteis_estimados: number;
  prazo: string | null;
  prioridade: number;
  motivo_recomendacao: string;
  competencia_alvo: string;
  origem_geracao: 'regra' | 'regra+ia';
  gerada_por_ia: boolean;
}

export interface NextFocus {
  competencia: string | null;
  nivel_atual: number | null;
  area: string;
  mensagem: string;
}

export interface PendingEvidenceDraft {
  id: string;
  titulo: string;
  descricao: string;
  tipo: string;
  missao_relacionada: string | null;
}

export interface LastCompletedMission {
  id: string;
  titulo: string;
  concluida_em: string | null;
}

export interface DashboardData {
  // Identificação
  student_id: string;
  student_name: string;
  student_email: string;

  // Objetivo
  objective_id: string | null;
  objective_area: string | null;

  // IEP
  iep_score: number;
  iev_score: number;
  iep_delta: number | null; // null = primeiro registro
  diagnostic: string;
  assessment_date: string | null;

  // Competências
  competency_scores: CompetencyScore[];
  priority_competency: CompetencyScore | null;

  // Missões
  mission_stats: MissionStats;
  upcoming_missions: UpcomingMission[];

  // Portfólio & Experiências
  portfolio_count: number;
  experience_count: number;

  // Recomendação
  next_focus: NextFocus | null;

  // Meta
  last_updated: string;
  ultima_missao_concluida: LastCompletedMission | null;
  rascunho_evidencia_pendente: PendingEvidenceDraft | null;
}

// ── Store ──────────────────────────────────────────────────────────────────

interface DashboardState {
  data: DashboardData | null;
  suggestedMissions: MissionSuggestion[];
  isLoading: boolean;
  error: string | null;

  fetchDashboard: (profileId: string) => Promise<void>;
  setData: (data: DashboardData) => void;
  clearDashboard: () => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  data: null,
  suggestedMissions: [],
  isLoading: false,
  error: null,

  fetchDashboard: async (profileId: string) => {
    set({ isLoading: true, error: null });
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const [dashboardRes, suggestionsRes] = await Promise.all([
        fetch(`${apiUrl}/api/dashboard/resumo/?profile_id=${encodeURIComponent(profileId)}`),
        fetch(`${apiUrl}/api/missoes/sugeridas/?profile_id=${encodeURIComponent(profileId)}`),
      ]);

      if (!dashboardRes.ok) {
        const err = await dashboardRes.json().catch(() => ({}));
        throw new Error(err.error || `Erro ${dashboardRes.status}`);
      }

      const data: DashboardData = await dashboardRes.json();
      const suggestedMissions: MissionSuggestion[] = suggestionsRes.ok
        ? await suggestionsRes.json()
        : [];
      set({ data, suggestedMissions, isLoading: false });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Erro ao carregar dashboard';
      set({ error: message, isLoading: false });
    }
  },

  setData: (data) => set({ data }),

  clearDashboard: () => set({ data: null, suggestedMissions: [], isLoading: false, error: null }),
}));
