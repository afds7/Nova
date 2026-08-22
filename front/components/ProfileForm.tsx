"use client";

import React, { useState, useEffect } from "react";

// Definição da interface para os dados mockados de diagnóstico
interface StudentDiagnostic {
  name: string;
  strongestSkill: string;
}

// Dado "mockado" de diagnóstico do aluno
const mockDiagnostic: StudentDiagnostic = {
  name: "Alex Souza",
  strongestSkill: "Lógica",
};

// Mapeamento de competências/habilidades para sugestões de áreas ou cursos
const SKILL_SUGGESTIONS: Record<string, string> = {
  "Lógica": "TI",
  "Criatividade": "Design Gráfico",
  "Cuidado": "Medicina",
  "Comunicação": "Relações Públicas",
  "Organização": "Administração de Empresas",
};

export default function ProfileForm() {
  // 1. Carrega a sugestão baseada na habilidade mais forte
  const initialSuggestion = SKILL_SUGGESTIONS[mockDiagnostic.strongestSkill] || "";

  // 2. Estados do formulário
  const [area, setArea] = useState<string>("");
  const [isEdited, setIsEdited] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [success, setSuccess] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  // Inicializa o input com o valor sugerido
  useEffect(() => {
    setArea(initialSuggestion);
  }, [initialSuggestion]);

  // Manipulador de mudança do input
  const handleAreaChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setArea(e.target.value);
    setIsEdited(true);
    setError("");
  };

  // Restaura a sugestão original recomendada pelo sistema
  const handleRestoreSuggestion = () => {
    setArea(initialSuggestion);
    setIsEdited(false);
    setError("");
  };

  // Envio do formulário
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!area.trim()) {
      setError("Por favor, preencha a sua área ou curso de interesse.");
      return;
    }

    setIsSubmitting(true);
    setError("");

    // Simulando chamada de API de persistência de dados
    setTimeout(() => {
      setIsSubmitting(false);
      setSuccess(true);
    }, 1200);
  };

  // Reset do formulário para demonstração
  const handleResetForm = () => {
    setArea(initialSuggestion);
    setIsEdited(false);
    setSuccess(false);
    setError("");
  };

  return (
    <div className="w-full max-w-md mx-auto px-4 py-8 sm:px-6">
      {/* Container Principal com visual Premium (Glassmorphism + Sombra suave) */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 shadow-2xl backdrop-blur-md transition-all duration-300 hover:shadow-cyan-900/20">
        
        {/* Cabeçalho */}
        <div className="mb-6">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#2c9be3]/10 border border-[#2c9be3]/30 text-xs font-semibold text-[#2c9be3] mb-3">
            <span className="w-1.5 h-1.5 rounded-full bg-[#2c9be3] animate-pulse"></span>
            Fase 1: Definição de Objetivo
          </div>
          <h2 className="text-2xl font-bold text-slate-50 tracking-tight">
            Olá, <span className="text-[#2c9be3]">{mockDiagnostic.name}</span>!
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Seu diagnóstico aponta que sua principal força é <strong className="text-[#2c9be3] font-semibold">{mockDiagnostic.strongestSkill}</strong>.
          </p>
        </div>

        {success ? (
          /* Estado de Sucesso */
          <div className="text-center py-8 animate-fade-in">
            <div className="w-16 h-16 bg-cyan-950/80 border border-cyan-500/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
              </svg>
            </div>
            <h3 className="text-lg font-bold text-slate-50 mb-1">Objetivo Definido!</h3>
            <p className="text-sm text-slate-400 mb-6 px-4">
              Seu foco estratégico foi definido para <span className="text-cyan-300 font-medium font-mono">"{area}"</span>.
            </p>
            <button
              onClick={handleResetForm}
              className="px-5 py-2.5 text-xs font-semibold text-slate-400 hover:text-slate-100 bg-slate-800/50 hover:bg-slate-800 border border-slate-700/60 rounded-xl transition-all"
            >
              Alterar Objetivo
            </button>
          </div>
        ) : (
          /* Formulário */
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              {/* Texto de Apoio Não-Determinístico (Regra Crucial de UX) */}
              <div className="p-3 mb-4 rounded-2xl bg-[#2c9be3]/5 border border-[#2c9be3]/20 text-xs text-slate-300 leading-relaxed">
                💡 <span className="font-semibold text-[#2c9be3]">Sugestão não definitiva:</span> Com base no seu perfil de <span className="font-semibold text-[#2c9be3]">{mockDiagnostic.strongestSkill}</span>, preenchemos o campo abaixo com uma sugestão. Sinta-se totalmente livre para apagar ou alterar para o curso ou área que preferir!
              </div>

              <div className="flex justify-between items-center mb-2">
                <label htmlFor="area-interesse" className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Qual área/curso você quer seguir?
                </label>
                {isEdited && (
                  <button
                    type="button"
                    onClick={handleRestoreSuggestion}
                    className="text-xs font-medium text-cyan-400 hover:text-cyan-300 transition-colors flex items-center gap-1"
                    title="Restaurar recomendação do diagnóstico"
                  >
                    ↺ Usar sugestão
                  </button>
                )}
              </div>

              <div className="relative">
                <input
                  type="text"
                  id="area-interesse"
                  value={area}
                  onChange={handleAreaChange}
                  placeholder="ex: TI"
                  className="w-full bg-slate-950/70 border border-slate-800 focus:border-[#2c9be3] focus:ring-1 focus:ring-[#2c9be3]/40 rounded-2xl px-4 py-3.5 text-slate-200 text-sm placeholder-slate-600 transition-all outline-none"
                  disabled={isSubmitting}
                />
              </div>

              {error && <p className="text-xs font-medium text-rose-500 mt-2 ml-1">{error}</p>}
            </div>

            {/* Botão de Submissão com micro-animação */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3.5 rounded-2xl font-semibold text-sm transition-all duration-300 bg-[#2c9be3] hover:bg-[#1d81c2] text-slate-50 hover:shadow-lg hover:shadow-[#2c9be3]/20 disabled:opacity-50 active:scale-[0.98] cursor-pointer"
            >
              {isSubmitting ? (
                <div className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5 text-slate-950" fill="none" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Salvando Objetivo...</span>
                </div>
              ) : (
                "Confirmar Meu Objetivo"
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
