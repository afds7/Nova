'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { signIn } from 'next-auth/react';
import Image from 'next/image';

type Mode = 'login' | 'register';

export default function LoginPage() {
  const [mode, setMode]           = useState<Mode>('login');
  const [name, setName]           = useState('');
  const [email, setEmail]         = useState('');
  const [password, setPassword]   = useState('');
  const [error, setError]         = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const reset = () => { setName(''); setEmail(''); setPassword(''); setError(''); };

  const switchMode = (next: Mode) => { reset(); setMode(next); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (mode === 'register' && name.trim().length < 2) {
      setError('Coloca seu nome completo para continuar.'); return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Confere seu e-mail e tenta de novo.'); return;
    }
    if (password.length < 6) {
      setError('Sua senha precisa ter pelo menos 6 caracteres.'); return;
    }

    setIsLoading(true);
    try {
      const result = await signIn('credentials', {
        redirect: false,
        name,
        email,
        password,
        mode,
      });

      if (result?.error) {
        const msg = decodeURIComponent(result.error);
        setError(
          msg.includes('E-mail') || msg.includes('senha') || msg.includes('cadastrado')
            ? msg
            : mode === 'login'
              ? 'E-mail ou senha incorretos.'
              : 'Erro ao criar conta. Tente novamente.'
        );
      }
      // Se login OK, o useSession no page.tsx vai detectar a nova sessão automaticamente
    } finally {
      setIsLoading(false);
    }
  };

  const inputBase =
    'w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 text-sm ' +
    'placeholder-slate-400 outline-none transition-all ' +
    'focus:bg-white focus:border-[#2c9be3] focus:ring-2 focus:ring-[#2c9be3]/20 ' +
    'disabled:opacity-60';

  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-[#f1f5f9] p-4 sm:p-6">

      {/* Logo */}
      <motion.div
        initial={{ opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="mb-8 text-center"
      >
        <h1 className="text-4xl md:text-5xl tracking-tight text-slate-900 font-normal">
          NOVA<span className="font-bold text-[#2c9be3]">Hub</span>
        </h1>
        <p className="text-slate-500 text-sm mt-2">
          Diagnóstico Estratégico de Carreira
        </p>
      </motion.div>

      {/* Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ type: 'spring', stiffness: 320, damping: 28, delay: 0.1 }}
        className="w-full max-w-md bg-white rounded-3xl shadow-2xl overflow-hidden"
      >
        {/* Header degradê */}
        <div className="bg-gradient-to-br from-[#2c9be3] to-[#1d81c2] px-5 pt-7 pb-10 sm:px-8 sm:pt-8 sm:pb-12 text-white">
          <div className="w-12 h-12 rounded-2xl bg-white/20 border border-white/30 flex items-center justify-center mb-4">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <h2 className="text-xl font-black">
            {mode === 'login' ? 'Que bom te ver por aqui!' : 'Crie sua conta'}
          </h2>
          <p className="text-blue-100 text-sm mt-1">
            {mode === 'login'
              ? 'Entre para acessar seu diagnóstico e seu painel.'
              : 'Cadastre-se e descubra seu próximo passo.'}
          </p>
        </div>

        {/* Form — overlap */}
        <div className="-mt-6 mx-2 sm:mx-4 bg-white rounded-2xl border border-slate-200/80 shadow-sm p-4 sm:p-6 mb-4">
          {/* Abas */}
          <div className="flex bg-slate-100 rounded-xl p-1 mb-5">
            {(['login', 'register'] as Mode[]).map((m) => (
              <button
                key={m}
                id={`login-tab-${m}`}
                type="button"
                onClick={() => switchMode(m)}
                className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all cursor-pointer ${
                  mode === m
                    ? 'bg-white text-[#2c9be3] shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                {m === 'login' ? 'Entrar' : 'Criar conta'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-3">
            {/* Campo nome — só no cadastro */}
            <AnimatePresence initial={false}>
              {mode === 'register' && (
                <motion.div
                  key="name-field"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <input
                    id="login-input-name"
                    type="text"
                    placeholder="Seu nome completo"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    disabled={isLoading}
                    className={inputBase}
                    autoComplete="name"
                  />
                </motion.div>
              )}
            </AnimatePresence>

            <input
              id="login-input-email"
              type="email"
              placeholder="seu@email.com"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setError(''); }}
              disabled={isLoading}
              className={inputBase}
              autoComplete="email"
            />

            <input
              id="login-input-password"
              type="password"
              placeholder={mode === 'register' ? 'Criar senha (mín. 6 caracteres)' : 'Sua senha'}
              value={password}
              onChange={(e) => { setPassword(e.target.value); setError(''); }}
              disabled={isLoading}
              className={inputBase}
              autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
            />

            {/* Erro */}
            <AnimatePresence>
              {error && (
                <motion.p
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="text-red-500 text-xs font-medium flex items-center gap-1.5"
                >
                  <svg className="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  {error}
                </motion.p>
              )}
            </AnimatePresence>

            <motion.button
              id="login-submit-btn"
              type="submit"
              disabled={isLoading}
              whileHover={{ scale: isLoading ? 1 : 1.01 }}
              whileTap={{ scale: 0.98 }}
              className="w-full py-3 bg-[#2c9be3] hover:bg-[#1d81c2] text-white font-bold text-sm rounded-xl transition-colors disabled:opacity-70 flex items-center justify-center gap-2 shadow-md shadow-[#2c9be3]/20 cursor-pointer mt-1"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  {mode === 'login' ? 'Entrando...' : 'Criando conta...'}
                </>
              ) : mode === 'login' ? 'Entrar' : 'Criar conta grátis'}
            </motion.button>
          </form>

          <p className="text-xs text-center text-slate-400 mt-4">
            🔒 100% seguro · LGPD · Sem spam
          </p>
        </div>
      </motion.div>
    </main>
  );
}
