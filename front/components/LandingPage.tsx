'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import AuthModal from './AuthModal';

interface LandingPageProps {
  onStart: () => void;
}

export default function LandingPage({ onStart }: LandingPageProps) {
  const [authOpen, setAuthOpen] = useState(false);

  const stats = [
    { value: '7', label: 'Pontos do seu perfil' },
    { value: '17', label: 'Perguntas rápidas' },
    { value: '2min', label: 'Até o resultado' },
  ];

  const features = [
    {
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      title: 'Entenda seu momento',
      desc: 'Veja como estão seu preparo, sua direção e o que pode te destacar.',
    },
    {
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      title: 'Plano com IA',
      desc: 'Receba próximos passos personalizados para sair da intenção e entrar em ação.',
    },
    {
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      title: 'É grátis de verdade',
      desc: 'Sem mensalidade e sem cartão. Você faz o diagnóstico e já começa a se organizar.',
    },
  ];

  return (
    <main className="min-h-screen flex flex-col bg-[#f1f5f9] overflow-x-hidden">

      {/* AuthModal para quem já tem conta */}
      <AuthModal isOpen={authOpen} onClose={() => setAuthOpen(false)} />

      {/* Header */}
      <header className="w-full px-6 md:px-12 py-5 flex items-center justify-between">
        <motion.div
          initial={{ opacity: 0, x: -12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
        >
          <div className="relative h-14 w-44 overflow-hidden md:h-16 md:w-48">
            <img src="/logo-nova.png" alt="NOVA Hub" width={650} height={366} className="absolute left-[-167px] top-[-105px] max-w-none origin-top-left scale-[0.8]" />
          </div>
        </motion.div>

        <motion.button
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
          onClick={() => setAuthOpen(true)}
          className="px-5 py-2.5 text-sm font-semibold text-[#2c9be3] border-2 border-[#2c9be3] rounded-xl hover:bg-[#2c9be3] hover:text-white transition-all duration-200 cursor-pointer"
        >
          Entrar
        </motion.button>
      </header>

      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center px-6 py-16 text-center max-w-3xl mx-auto w-full">

        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.05 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 bg-[#2c9be3]/10 border border-[#2c9be3]/30 rounded-full mb-6"
        >
          <span className="w-2 h-2 rounded-full bg-[#2c9be3] animate-pulse" />
          <span className="text-[#2c9be3] text-sm font-semibold">Seu próximo passo profissional</span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-4xl md:text-6xl font-black text-slate-900 leading-tight tracking-tight mb-4"
        >
          Descubra onde você está{' '}
          <span className="text-[#2c9be3]">na sua jornada</span>{' '}
          profissional
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.18 }}
          className="text-slate-500 text-lg md:text-xl leading-relaxed max-w-xl mb-10"
        >
          Responda 17 perguntas rápidas e descubra o que já está funcionando, o que falta e qual pode ser seu próximo movimento.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.25 }}
          className="flex flex-col sm:flex-row gap-3 items-center"
        >
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={onStart}
            className="px-10 py-4 bg-[#2c9be3] hover:bg-[#1d81c2] text-white font-black text-base rounded-2xl transition-all shadow-xl shadow-[#2c9be3]/30 cursor-pointer"
          >
            Começar agora →
          </motion.button>

          <button
            onClick={() => setAuthOpen(true)}
            className="text-sm text-slate-500 hover:text-slate-800 font-medium transition-colors cursor-pointer underline underline-offset-2"
          >
            Já tenho conta
          </button>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="flex items-center gap-8 mt-12"
        >
          {stats.map((s, i) => (
            <div key={i} className="text-center">
              <div className="text-2xl font-black text-[#2c9be3]">{s.value}</div>
              <div className="text-xs text-slate-400 font-medium mt-0.5">{s.label}</div>
            </div>
          ))}
        </motion.div>
      </section>

      {/* Features */}
      <section className="w-full max-w-4xl mx-auto px-6 pb-16 grid grid-cols-1 md:grid-cols-3 gap-4">
        {features.map((f, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.35 + i * 0.08 }}
            className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="w-10 h-10 rounded-xl bg-[#2c9be3]/10 text-[#2c9be3] flex items-center justify-center mb-3">
              {f.icon}
            </div>
            <h3 className="font-bold text-slate-800 text-sm mb-1">{f.title}</h3>
            <p className="text-slate-500 text-xs leading-relaxed">{f.desc}</p>
          </motion.div>
        ))}
      </section>

      {/* Footer */}
      <footer className="text-center pb-8 text-xs text-slate-400">
        🔒 Seus dados protegidos · LGPD · Sem spam
      </footer>
    </main>
  );
}
