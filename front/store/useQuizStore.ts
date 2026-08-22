import { create } from 'zustand';
import { QUESTIONS } from '../constants/questions';

interface LeadInfo {
  name: string;
  email: string;
  area: string;
}

interface FullResult {
  name: string;
  email: string;
  area: string;
  iep_score: number;
  iev_score: number;
  diagnostic: string;
  action_plan: string;
}

interface QuizState {
  currentStep: number;
  answers: Record<number, number>;
  leadInfo: LeadInfo;
  actionPlan: string;
  setAnswer: (questionId: number, value: number) => void;
  setLeadInfo: (info: LeadInfo) => void;
  nextStep: () => void;
  prevStep: () => void;
  resetQuiz: () => void;
  startQuiz: () => void;
  setActionPlan: (plan: string) => void;
  setFullResult: (result: FullResult) => void;
}

export const useQuizStore = create<QuizState>((set) => ({
  currentStep: 0,
  answers: {},
  leadInfo: { name: '', email: '', area: '' },

  setAnswer: (questionId, value) => set((state) => ({
    answers: { ...state.answers, [questionId]: value }
  })),

  setLeadInfo: (info) => set({ leadInfo: info }),

  // Agora temos as 17 perguntas + 1 tela de Lead + 1 tela de Resultado
  nextStep: () => set((state) => ({
    currentStep: Math.min(state.currentStep + 1, QUESTIONS.length + 2)
  })),

  prevStep: () => set((state) => ({
    currentStep: Math.max(state.currentStep - 1, 1)
  })),

  // Inicia o quiz a partir da pergunta 1
  startQuiz: () => set({ currentStep: 1, answers: {}, leadInfo: { name: '', email: '', area: '' }, actionPlan: '' }),

  actionPlan: '',
  setActionPlan: (plan) => set({ actionPlan: plan }),

  resetQuiz: () => set({ currentStep: 0, answers: {}, leadInfo: { name: '', email: '', area: '' }, actionPlan: '' }),

  // Carrega resultado anterior do backend e vai direto para a tela de resultados
  setFullResult: (result) => set({
    leadInfo: { name: result.name, email: result.email, area: result.area },
    actionPlan: result.action_plan || '',
    currentStep: QUESTIONS.length + 2, // pula direto para a tela final
  }),
}));