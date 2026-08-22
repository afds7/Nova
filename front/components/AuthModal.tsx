'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { signIn } from 'next-auth/react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** Chamado após login/cadastro bem-sucedido. Se não fornecido, apenas fecha o modal. */
  onSuccess?: () => void;
}

type Mode = 'login' | 'register';

export default function AuthModal({ isOpen, onClose, onSuccess }: AuthModalProps) {
  const [mode, setMode]           = useState<Mode>('login');
  const [name, setName]           = useState('');
  const [email, setEmail]         = useState('');
  const [password, setPassword]   = useState('');
  const [error, setError]         = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const reset = () => {
    setName(''); setEmail(''); setPassword(''); setError('');
  };

  const switchMode = (next: Mode) => {
    reset();
    setMode(next);
  };

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
        // NextAuth encoda a mensagem de erro na URL; tentamos decodificar
        const msg = decodeURIComponent(result.error);
        setError(
          msg.includes('E-mail') || msg.includes('senha') || msg.includes('cadastrado')
            ? msg
            : mode === 'login'
              ? 'E-mail ou senha incorretos.'
              : 'Erro ao criar conta. Tente novamente.'
        );
      } else {
        if (onSuccess) {
          onSuccess();
        } else {
          onClose();
        }
      }
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
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm"
          />

          {/* Modal */}
          <motion.div
            key="modal"
            initial={{ opacity: 0, scale: 0.94, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.94, y: 16 }}
            transition={{ type: 'spring', stiffness: 340, damping: 28 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="w-full max-w-md bg-white rounded-3xl shadow-2xl overflow-hidden">

              {/* Header degradê */}
              <div className="bg-gradient-to-br from-[#2c9be3] to-[#1d81c2] px-8 pt-8 pb-12 text-white relative">
                <button
                  onClick={onClose}
                  id="auth-modal-close"
                  className="absolute top-4 right-4 w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 transition-colors flex items-center justify-center text-white cursor-pointer"
                  aria-label="Fechar"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>

                <div className="w-12 h-12 rounded-2xl bg-white/20 border border-white/30 flex items-center justify-center mb-4">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <h2 className="text-xl font-black">
                  Que bom te ver por aqui!
                </h2>
                <p className="text-blue-100 text-sm mt-1">
                  Entre para acompanhar seu progresso e suas missões.
                </p>
              </div>

              {/* Card form — overlap */}
              <div className="-mt-6 mx-4 bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 mb-4">

                <form onSubmit={handleSubmit} className="space-y-3 mt-4">

                  <input
                    id="auth-input-email"
                    type="email"
                    placeholder="seu@email.com"
                    value={email}
                    onChange={(e) => { setEmail(e.target.value); setError(''); }}
                    disabled={isLoading}
                    className={inputBase}
                    autoComplete="email"
                  />

                  <input
                    id="auth-input-password"
                    type="password"
                    placeholder="Sua senha"
                    value={password}
                    onChange={(e) => { setPassword(e.target.value); setError(''); }}
                    disabled={isLoading}
                    className={inputBase}
                    autoComplete="current-password"
                  />

                  {/* Mensagem de erro */}
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

                  {/* Botão principal */}
                  <motion.button
                    id="auth-submit-btn"
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
                        Entrando...
                      </>
                    ) : 'Entrar'}
                  </motion.button>
                </form>

                <p className="text-xs text-center text-slate-400 mt-4">
                  🔒 Seus dados protegidos · LGPD · Sem spam
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
