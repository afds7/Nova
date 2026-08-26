'use client';

import { useState, useEffect, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';
import { useSession, signIn } from 'next-auth/react';
import { useQuizStore } from '../store/useQuizStore';
import { QUESTIONS } from '../constants/questions';
import { calculateScores, getDiagnostics } from '../utils/math';
import { useRouter } from 'next/navigation';
import AuthModal from './AuthModal';
import type { RecommendationItem } from '../store/useRecommendationsStore';


// Mapeamento: pilar mais forte do aluno → sugestão de áreas abrangentes
const PILLAR_TO_AREA: Record<string, string> = {
  'Base Acadêmica':               'Ciências Exatas, Pesquisa ou Direito',
  'Visão Estratégica':            'Administração, Economia ou Relações Internacionais',
  'Foco Comportamental':          'Psicologia, Medicina/Saúde ou Recursos Humanos',
  'Diferenciação':                'Design, Arquitetura ou Artes',
  'Projetos e Prova Real':        'Engenharias, Tecnologia da Informação ou Biologia',
  'Contato com Mundo Real':       'Agronomia, Marketing ou Comércio Exterior',
  'Posicionamento e Networking':  'Comunicação Social, Jornalismo ou Relações Públicas',
};

// Mapa de cores para os botões do quiz no hover
const optionColors: Record<number, string> = {
  1: 'hover:border-red-500 hover:bg-red-50 hover:text-red-700',
  2: 'hover:border-orange-500 hover:bg-orange-50 hover:text-orange-700',
  3: 'hover:border-yellow-500 hover:bg-yellow-50 hover:text-yellow-700',
  4: 'hover:border-lime-500 hover:bg-lime-50 hover:text-lime-700',
  5: 'hover:border-green-500 hover:bg-green-50 hover:text-green-700',
};

// Mapa de cores para o estado selecionado
const activeColors: Record<number, string> = {
  1: 'border-red-500 bg-red-50 text-red-700 shadow-sm',
  2: 'border-orange-500 bg-orange-50 text-orange-700 shadow-sm',
  3: 'border-yellow-500 bg-yellow-50 text-yellow-700 shadow-sm',
  4: 'border-lime-500 bg-lime-50 text-lime-700 shadow-sm',
  5: 'border-green-500 bg-green-50 text-green-700 shadow-sm',
};

// Componente de score animado (conta até o número alvo)
function AnimatedScore({ target }: { target: number }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let start = 0;
    const duration = 1200;
    const step = 16;
    const increment = target / (duration / step);
    const timer = setInterval(() => {
      start += increment;
      if (start >= target) { setDisplay(target); clearInterval(timer); }
      else setDisplay(Math.floor(start));
    }, step);
    return () => clearInterval(timer);
  }, [target]);
  return <>{display}</>;
}

export default function Quiz() {
  const { data: session } = useSession();
  const router = useRouter();
  const {
    currentStep, answers, leadInfo,
    setAnswer, setLeadInfo, nextStep, prevStep,
    resetQuiz, actionPlan, recommendations, setActionPlan, setRecommendations,
  } = useQuizStore();

  const [localName, setLocalName]       = useState('');
  const [localEmail, setLocalEmail]     = useState('');
  const [localPassword, setLocalPassword] = useState('');
  const [localArea, setLocalArea]       = useState('');
  const [isAreaEdited, setIsAreaEdited] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [emailError, setEmailError]     = useState('');
  const [submitError, setSubmitError]   = useState('');
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [assessmentId, setAssessmentId] = useState<string | null>(null);
  const [isPlanUpdating, setIsPlanUpdating] = useState(false);

  const scores = useMemo(() => calculateScores(answers), [answers]);

  // Sugestão de área baseada no pilar mais forte
  const suggestedArea = answers && Object.keys(answers).length > 0
    ? PILLAR_TO_AREA[scores.strongest] ?? ''
    : '';

  // Preenche nome e email automaticamente após login (modal de autenticação)
  useEffect(() => {
    if (session?.user) {
      if (session.user.name && !localName) setLocalName(session.user.name);
      if (session.user.email && !localEmail) setLocalEmail(session.user.email);
    }
  }, [session]);


  useEffect(() => {
    if (suggestedArea && !isAreaEdited) setLocalArea(suggestedArea);
  }, [suggestedArea, isAreaEdited]);

  // O diagnóstico determinístico aparece primeiro. A IA enriquece o plano depois,
  // para que timeout/rate limit nunca impeça o aluno de ver seu resultado.
  useEffect(() => {
    if (currentStep !== QUESTIONS.length + 2 || !assessmentId) return;

    let cancelled = false;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    setIsPlanUpdating(true);
    fetch(`${apiUrl}/api/assessments/${assessmentId}/plan/`)
      .then(async (response) => {
        if (!response.ok) return null;
        return response.json() as Promise<{ action_plan?: string }>;
      })
      .then((data) => {
        if (!cancelled && data?.action_plan) setActionPlan(data.action_plan);
      })
      .catch(() => {
        // O plano determinístico já está visível; não interrompe o fluxo por falha externa.
      })
      .finally(() => {
        if (!cancelled) setIsPlanUpdating(false);
      });

    return () => { cancelled = true; };
  }, [currentStep, assessmentId, setActionPlan]);

  // Guard: se currentStep for 0 (estado inicial antes da LandingPage transicionar), não renderiza nada
  if (currentStep === 0) return null;

  // ─────────────────────────────────────────────
  // TELA DE CAPTURA DE LEAD
  // ─────────────────────────────────────────────
  if (currentStep === QUESTIONS.length + 1) {
    const handleLeadSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      if (!localName || !localEmail || !localArea || !localPassword) return;
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(localEmail)) { setEmailError('Confere seu e-mail e tenta de novo.'); return; }
      setEmailError('');
      setSubmitError('');
      setIsSubmitting(true);
      setLeadInfo({ name: localName, email: localEmail, area: localArea });

      const { iep, iev, strongest, weakest, gap } = scores;
      const { mainDiagnostic } = getDiagnostics(iep, iev);
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/api/assessments/submit/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: localName, email: localEmail, area: localArea, password: localPassword, strongest_point: strongest, weakest_point: weakest, gap, iep_score: iep, iev_score: iev, diagnostic: mainDiagnostic }),
        });
        if (response.ok) {
          const data = await response.json(); 
          setAssessmentId(data.id || null);
          setActionPlan(data.action_plan); 
          setRecommendations(data.recommendations || null);

          // O diagnóstico já foi salvo: mostre o resultado sem esperar a sessão.
          nextStep();
          
          if (!session?.user) {
            // Faz login automaticamente com a senha recém-criada
            const signInRes = await signIn('credentials', {
              email: localEmail,
              password: localPassword,
              redirect: false,
            });
            if (!signInRes?.ok) {
              setSubmitError('Seu diagnóstico foi salvo. Entre na sua conta para continuar.');
              setAuthModalOpen(true);
              return;
            }
          }
          return;
        }

        const errorText = await response.text();
        console.error('Erro ao guardar a lead:', errorText);
        let message = 'Não foi possível salvar seu diagnóstico. Tente novamente.';
        try {
          const errorData = JSON.parse(errorText) as { detail?: string; error?: string };
          if (errorData.detail || errorData.error) message = errorData.detail || errorData.error || message;
        } catch {
          // Mantém uma mensagem amigável quando o servidor não retorna JSON.
        }
        setSubmitError(message);
      } catch (err) {
        console.error('Erro de rede:', err);
        setSubmitError('Não foi possível conectar ao servidor. Verifique se o backend está rodando e tente novamente.');
      } finally {
        setIsSubmitting(false);
      }
    };


    const inputClass = "w-full min-w-0 pl-10 pr-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-[#2c9be3] focus:border-transparent outline-none transition-all text-sm bg-slate-50 focus:bg-white text-slate-800 placeholder-slate-400 disabled:opacity-60";

    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="w-full max-w-md mx-auto"
      >
        {/* Card */}
        <div className="bg-white border border-slate-200/80 rounded-3xl shadow-xl overflow-hidden">
          {/* Header colorido */}
          <div className="bg-gradient-to-br from-[#2c9be3] to-[#1d81c2] px-8 pt-8 pb-10 text-center text-white">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', delay: 0.1 }}
              className="w-14 h-14 rounded-full bg-white/20 border border-white/30 flex items-center justify-center mx-auto mb-4"
            >
              <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </motion.div>
            <h2 className="text-xl font-black">Seu perfil está pronto! 🎯</h2>
            <p className="text-blue-100 text-sm mt-1">Onde você quer receber seu diagnóstico?</p>
          </div>

          {/* Form — overlap com o header */}
          <div className="-mt-4 mx-4 bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6">
            {/* AuthModal de login/cadastro — ao entrar/cadastrar, fecha e mantém o resultado */}
            <AuthModal
              isOpen={authModalOpen}
              onClose={() => setAuthModalOpen(false)}
              onSuccess={() => {
                setAuthModalOpen(false);
                nextStep();
              }}
            />

            <form onSubmit={handleLeadSubmit} className="space-y-4">
              {/* Nome + Email: logado ou manual */}
              {session?.user ? (
                // Já logado: exibe card com dados do usuário
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="flex items-center gap-3 p-3 bg-[#2c9be3]/5 border border-[#2c9be3]/20 rounded-2xl"
                >
                  <div className="w-10 h-10 rounded-full bg-[#2c9be3] flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                    {session.user.name?.charAt(0)?.toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-slate-800 truncate">{session.user.name}</p>
                    <p className="text-xs text-slate-500 truncate">{session.user.email}</p>
                  </div>
                  <span className="text-[#2c9be3] flex-shrink-0">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </span>
                </motion.div>
              ) : (
                // Não logado: botão para abrir modal de login + campos manuais
                <>

                  {/* Nome */}
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                    </span>
                    <input type="text" required disabled={isSubmitting} className={inputClass} placeholder="Seu nome" value={localName} onChange={(e) => setLocalName(e.target.value)} />
                  </motion.div>
                  {/* Email */}
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.22 }} className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                    </span>
                    <input type="email" required disabled={isSubmitting}
                      className={`${inputClass} ${emailError ? '!border-red-400 !focus:ring-red-400' : ''}`}
                      placeholder="seu@email.com" value={localEmail}
                      onChange={(e) => { setLocalEmail(e.target.value); if (emailError) setEmailError(''); }}
                    />
                    <AnimatePresence>
                      {emailError && <motion.p initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="text-red-500 text-xs mt-1 font-medium">{emailError}</motion.p>}
                    </AnimatePresence>
                  </motion.div>
                  {/* Senha */}
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                    </span>
                    <input type="password" required minLength={6} disabled={isSubmitting}
                      className={inputClass}
                      placeholder="Crie uma senha (mínimo 6 caracteres)" value={localPassword}
                      onChange={(e) => setLocalPassword(e.target.value)}
                    />
                  </motion.div>
                </>
              )}

              {/* Área */}
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.29 }}>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Que área combina com você?</label>
                  {isAreaEdited && suggestedArea && (
                    <button type="button" onClick={() => { setLocalArea(suggestedArea); setIsAreaEdited(false); }}
                      className="text-xs text-[#2c9be3] hover:text-[#1d81c2] font-semibold transition-colors">
                      ↺ Usar sugestão de novo
                    </button>
                  )}
                </div>
                {suggestedArea && !isAreaEdited && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-wrap items-center gap-x-1.5 gap-y-1 mb-2 min-w-0">
                    <span className="inline-flex shrink-0 items-center gap-1 px-2 py-0.5 rounded-full bg-[#2c9be3]/10 border border-[#2c9be3]/20 text-xs font-semibold text-[#2c9be3]">
                      ✨ Sugestão automática
                    </span>
                    <span className="min-w-0 text-xs leading-snug text-slate-400">
                      pilar: <strong className="break-words text-slate-600">{scores.strongest}</strong>
                    </span>
                  </motion.div>
                )}
                <div className="relative">
                  <span className="absolute left-3 top-3.5 text-slate-400">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                  </span>
                  <textarea required disabled={isSubmitting} rows={2} className={`${inputClass} min-h-[56px] resize-none leading-relaxed`}
                    placeholder="Ex: TI, Medicina, Design..." value={localArea}
                    onChange={(e) => { setLocalArea(e.target.value); setIsAreaEdited(true); }}
                  />
                </div>
              </motion.div>

              {/* Submit */}
              <motion.button
                type="submit" disabled={isSubmitting}
                whileHover={{ scale: isSubmitting ? 1 : 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full mt-2 py-3.5 bg-[#2c9be3] text-white font-bold rounded-xl hover:bg-[#1d81c2] disabled:opacity-70 transition-colors shadow-md shadow-[#2c9be3]/20 flex justify-center items-center gap-2 text-sm cursor-pointer"
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Gerando Plano Estratégico...
                  </>
                ) : 'Ver meu resultado →'}
              </motion.button>

              {submitError && (
                <p role="alert" className="text-center text-xs font-medium text-red-500">
                  {submitError}
                </p>
              )}

              <p className="text-xs text-center text-slate-400">🔒 Seus dados protegidos · LGPD · Sem spam</p>
            </form>
          </div>
        </div>
      </motion.div>
    );
  }

  // ─────────────────────────────────────────────
  // TELA FINAL: Dashboard de Resultados
  // ─────────────────────────────────────────────
  if (currentStep > QUESTIONS.length + 1) {
    const { iep, iev } = scores;
    const { mainDiagnostic, copyMessage, themeClasses } = getDiagnostics(iep, iev);

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-4xl mx-auto space-y-6 pb-12 mt-4"
      >
        {/* Card principal de perfil */}
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className={`p-8 rounded-3xl border-2 text-center ${themeClasses.bg} ${themeClasses.border} shadow-lg`}
        >
          <div className="mb-2 text-xs font-bold tracking-widest uppercase text-slate-400">
            Diagnóstico de {leadInfo.name}
          </div>
          <motion.h2
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className={`text-4xl md:text-5xl font-black mb-4 ${themeClasses.text}`}
          >
            {mainDiagnostic}
          </motion.h2>
          <p className="text-slate-700 text-sm md:text-base font-medium leading-relaxed max-w-2xl mx-auto">
            {copyMessage}
          </p>

          {leadInfo.area && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35 }}
              className="mt-6 inline-flex items-center gap-2 px-5 py-2 bg-white/80 backdrop-blur border border-slate-200 rounded-full shadow-sm"
            >
              <svg className={`w-4 h-4 flex-shrink-0 ${themeClasses.text}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="text-sm font-semibold text-slate-700">
                Foco estratégico em{' '}
                <span className={`font-black ${themeClasses.text}`}>{leadInfo.area}</span>
              </span>
            </motion.div>
          )}
        </motion.div>

        {/* Métricas animadas */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { label: 'Preparo Estratégico', sub: 'Índice IEP', score: iep, delay: 0.2 },
            { label: 'Vantagem Competitiva', sub: 'Índice IEV', score: iev, delay: 0.3 },
          ].map((m) => (
            <motion.div
              key={m.label}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: m.delay }}
              className="p-6 bg-white border border-slate-200/80 rounded-2xl shadow-md flex justify-between items-center"
            >
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-0.5">{m.label}</h3>
                <p className="text-xs text-slate-400 font-medium">{m.sub}</p>
              </div>
              <div className="flex items-baseline gap-0.5">
                <span className="text-5xl font-black text-[#2c9be3] tabular-nums">
                  <AnimatedScore target={m.score} />
                </span>
                <span className="text-slate-300 text-sm font-medium mb-1">/100</span>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Plano de Ação */}
        {actionPlan ? (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-2xl shadow-lg border border-slate-200/80 overflow-hidden"
          >
            <div className="bg-gradient-to-r from-[#2c9be3] to-[#1d81c2] px-6 py-4 flex items-center gap-3">
              <svg className="w-5 h-5 text-white flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <h3 className="text-base font-bold text-white">Seu plano para evoluir</h3>
            </div>
            <div className="p-8 prose max-w-none prose-headings:font-bold prose-a:text-[#2c9be3] hover:prose-a:text-[#1d81c2]">
              <ReactMarkdown>{actionPlan}</ReactMarkdown>
              {isPlanUpdating && (
                <p className="not-prose mt-5 text-xs font-medium text-slate-400">
                  Ajustando este plano com referências personalizadas...
                </p>
              )}
            </div>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="p-10 text-center bg-white rounded-2xl border border-slate-200/80 shadow-sm"
          >
            <div className="flex justify-center gap-1.5 mb-3">
              {[0, 0.15, 0.3].map((d, i) => (
                <motion.div key={i} animate={{ y: [0, -6, 0] }} transition={{ repeat: Infinity, duration: 0.9, delay: d }}
                  className="w-2 h-2 rounded-full bg-[#2c9be3]" />
              ))}
            </div>
            <p className="text-sm text-slate-500 font-medium">Montando seus próximos passos com IA...</p>
          </motion.div>
        )}

        {recommendations && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.46 }}
            className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-md"
          >
            <div className="flex items-center justify-between gap-3 bg-slate-800 px-6 py-4 text-white">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-blue-200">Para explorar a partir daqui</p>
                <h3 className="mt-1 text-base font-bold">Cursos, faculdades e materiais que podem combinar com seu perfil</h3>
              </div>
              <span className="hidden text-xl sm:block" aria-hidden="true">✦</span>
            </div>
            <div className="p-5 md:p-6">
              <p className="text-sm leading-relaxed text-slate-600">{recommendations.resumo}</p>
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                {recommendations.itens.slice(0, 3).map((item: RecommendationItem) => (
                  <article key={`${item.tipo}-${item.titulo}`} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#2c9be3]">{item.tipo}</span>
                    <h4 className="mt-2 line-clamp-2 text-sm font-bold leading-snug text-slate-800">{item.titulo}</h4>
                    <p className="mt-2 line-clamp-3 text-xs leading-relaxed text-slate-500">{item.descricao}</p>
                    {item.url && <a href={item.url} target="_blank" rel="noreferrer" className="mt-3 inline-block text-xs font-bold text-[#2c9be3] hover:underline">Conhecer ↗</a>}
                  </article>
                ))}
              </div>
              <button type="button" onClick={() => router.push('/recomendacoes')} className="mt-5 w-full rounded-xl border-2 border-[#2c9be3] px-4 py-3 text-sm font-bold text-[#2c9be3] transition hover:bg-blue-50">
                Ver sugestões detalhadas
              </button>
              <p className="mt-2 text-center text-[11px] text-slate-400">São possibilidades para você investigar, não escolhas definitivas.</p>
            </div>
          </motion.div>
        )}

        {/* Botão acessar menu */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }} className="pt-2">
          <motion.button
            onClick={() => router.push('/menu')}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            className="w-full py-4 px-6 flex items-center justify-center gap-3 bg-[#2c9be3] text-white font-bold text-sm rounded-2xl hover:bg-[#1d81c2] transition-all duration-200 shadow-md group cursor-pointer"
          >
            Ir para meu painel
            <svg className="w-4 h-4 transition-transform duration-500 group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </motion.button>
          <p className="text-xs text-center text-slate-400 mt-2">Acompanhe sua evolução e suas próximas missões.</p>
        </motion.div>
      </motion.div>
    );
  }

  // ─────────────────────────────────────────────
  // TELAS 1–17: Questionário
  // ─────────────────────────────────────────────
  const questionIndex = currentStep - 1;
  const question = QUESTIONS[questionIndex];
  const progress = (currentStep / QUESTIONS.length) * 100;

  const handleSelect = (value: number) => {
    if (isTransitioning) return;
    setIsTransitioning(true);
    setAnswer(question.id, value);
    setTimeout(() => { nextStep(); setIsTransitioning(false); }, 350);
  };

  return (
    <div className="w-full max-w-xl mx-auto mt-6">

      {/* Header: categoria + contagem */}
      <div className="flex justify-between items-center mb-3">
        <motion.span
          key={question.category}
          initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
          className="text-xs font-bold text-[#2c9be3] uppercase tracking-widest"
        >
          {question.category}
        </motion.span>
        <span className="text-xs font-semibold text-slate-400">
          <span className="text-slate-800 font-black">{currentStep}</span> / {QUESTIONS.length}
        </span>
      </div>

      {/* Barra de progresso */}
      <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden mb-8">
        <motion.div
          className="h-full rounded-full"
          style={{ background: 'linear-gradient(90deg, #2c9be3, #1d81c2)' }}
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        />
      </div>

      {/* Pergunta */}
      <div className="min-h-[300px]">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
            className="space-y-8"
          >
            <h2 className="text-2xl md:text-3xl font-medium text-slate-900 leading-tight">
              {question.text}
            </h2>

            <div className="grid grid-cols-5 gap-2">
              {[1, 2, 3, 4, 5].map((value) => {
                const isSelected = answers[question.id] === value;
                return (
                  <button
                    key={value}
                    onClick={() => handleSelect(value)}
                    className={`h-16 flex flex-col items-center justify-center rounded-xl border-2 transition-all duration-200 outline-none cursor-pointer
                      ${isSelected
                        ? `${activeColors[value]} scale-95`
                        : `border-slate-200 text-slate-700 bg-white hover:border-slate-300 ${optionColors[value]}`
                      }`}
                  >
                    <span className="text-xl font-bold">{value}</span>
                  </button>
                );
              })}
            </div>

            <div className="flex justify-between text-xs font-medium">
              <span className="text-rose-500">Discordo Totalmente</span>
              <span className="text-emerald-600">Concordo Totalmente</span>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Rodapé: voltar */}
      <div className="mt-8 pt-6 border-t border-slate-200/80 flex justify-between">
        <button
          onClick={prevStep}
          disabled={currentStep === 1 || isTransitioning}
          className="px-4 py-2 text-sm font-medium text-slate-500 hover:text-slate-900 disabled:opacity-30 transition-colors cursor-pointer"
        >
          ← Voltar
        </button>
      </div>
    </div>
  );
}
