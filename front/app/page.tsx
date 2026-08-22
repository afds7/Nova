'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import Quiz from '../components/Quiz';
import LandingPage from '../components/LandingPage';
import { useQuizStore } from '../store/useQuizStore';

type AppState = 'loading' | 'landing' | 'quiz';

export default function Home() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const { setFullResult, currentStep, startQuiz } = useQuizStore();
  const [appState, setAppState] = useState<AppState>('loading');
  const [mousePos, setMousePos] = useState({ x: 400, y: 300 });

  // Fundo reativo ao mouse
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => setMousePos({ x: e.clientX, y: e.clientY });
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  useEffect(() => {
    if (status === 'loading') return;

    // Se o quiz já está em andamento, vai direto para o quiz
    if (currentStep > 0) {
      setAppState('quiz');
      return;
    }

    // Se o usuário já está logado, verifica diagnóstico anterior
    if (session?.user?.email) {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      fetch(`${apiUrl}/api/assessments/last/?email=${encodeURIComponent(session.user.email)}`)
        .then(async (res) => {
          if (res.ok) {
            const data = await res.json();
            if (data) {
              router.replace('/menu');
              return;
            }
          }
          setAppState('landing');
        })
        .catch(() => setAppState('landing'));
    } else {
      setAppState('landing');
    }
  }, [session, status, router]);


  // Quando o usuário clica em "Refazer Diagnóstico", currentStep volta a 0
  // → detectamos aqui e redirecionamos para a landing page
  useEffect(() => {
    if (appState === 'quiz' && currentStep === 0) {
      setAppState('landing');
    }
  }, [currentStep, appState]);


  // Tela de carregamento
  if (appState === 'loading') {
    return (
      <main className="min-h-screen flex items-center justify-center bg-[#f1f5f9]">
        <motion.div
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ repeat: Infinity, duration: 1.5, ease: 'easeInOut' }}
          className="flex flex-col items-center gap-4"
        >
          <div className="flex gap-1.5">
            {[0, 0.15, 0.3].map((d, i) => (
              <motion.div
                key={i}
                animate={{ y: [0, -8, 0] }}
                transition={{ repeat: Infinity, duration: 0.9, delay: d }}
                className="w-2.5 h-2.5 rounded-full bg-[#2c9be3]"
              />
            ))}
          </div>
          <p className="text-sm text-slate-400 font-medium">Carregando...</p>
        </motion.div>
      </main>
    );
  }

  // Landing page
  if (appState === 'landing') {
    return <LandingPage onStart={() => { startQuiz(); setAppState('quiz'); }} />;
  }

  // Quiz (para todos — logados ou não)
  return (
    <main className="relative min-h-screen flex flex-col bg-[#f1f5f9] text-slate-900 p-6 md:p-12 overflow-x-hidden selection:bg-[#2c9be3]/20">
      {/* Fundo reativo */}
      <div
        className="fixed inset-0 pointer-events-none -z-10 transition-opacity duration-500"
        style={{
          background: `
            radial-gradient(650px circle at ${mousePos.x}px ${mousePos.y}px, rgba(44, 155, 227, 0.16), transparent 80%),
            radial-gradient(at 0% 0%, rgba(224, 242, 254, 0.7) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(219, 234, 254, 0.6) 0px, transparent 50%)
          `,
        }}
      />

      {/* Header com logo */}
      <header className="absolute top-0 left-0 p-6 z-10">
        <img
          src="/logo-nova.png"
          alt="Logo NOVA Hub"
          width={180}
          height={58}
          className="object-contain"
        />
      </header>

      {/* Quiz */}
      <div className="max-w-5xl mx-auto w-full flex-1 flex flex-col justify-center pt-12 md:pt-16">
        <Quiz />
      </div>
    </main>
  );
}