// front/utils/math.ts

export const calculateAverages = (answers: Record<number, number>, ids: number[]) => {
  const validAnswers = ids.map(id => answers[id]).filter(answer => answer >= 1 && answer <= 5);
  if (validAnswers.length === 0) return 0;
  const sum = validAnswers.reduce((acc, val) => acc + val, 0);
  return sum / validAnswers.length;
};

export const calculateScores = (answers: Record<number, number>) => {
  const A = calculateAverages(answers, [1, 2, 3]);
  const E = calculateAverages(answers, [4, 5, 6]);
  const C = calculateAverages(answers, [7, 8, 9]);
  const D = calculateAverages(answers, [10, 11]);
  const P = calculateAverages(answers, [12, 13]);
  const M = calculateAverages(answers, [14, 15]);
  const S = calculateAverages(answers, [16, 17]);

  const iepScore = Math.round((A * 0.3 + E * 0.4 + C * 0.3) * 20);
  const ievScore = Math.round((D * 0.25 + P * 0.30 + M * 0.25 + S * 0.20) * 20);

  const pillars = [
    { name: 'Base Acadêmica', score: A },
    { name: 'Visão Estratégica', score: E },
    { name: 'Foco Comportamental', score: C },
    { name: 'Diferenciação', score: D },
    { name: 'Projetos e Prova Real', score: P },
    { name: 'Contato com Mundo Real', score: M },
    { name: 'Posicionamento e Networking', score: S },
  ];

  // Ordenação com tratamento de edge case (notas perfeitamente iguais)
  pillars.sort((a, b) => {
    // Se houver diferença na nota, ordena normalmente (maior para o menor)
    if (b.score !== a.score) {
      return b.score - a.score;
    }
    // Em caso de EMPATE exato, embaralha aleatoriamente (retorna -0.5 ou 0.5).
    // Evita o viés de leitura do array onde o último item (Networking) era sempre selecionado como fraqueza.
    return Math.random() - 0.5;
  });

  return {
    iep: iepScore,
    iev: ievScore,
    strongest: pillars[0].name,
    weakest: pillars[pillars.length - 1].name,
    gap: Math.abs(iepScore - ievScore)
  };
};

export const getDiagnostics = (iep: number, iev: number) => {
  let iepClass = '';
  if (iep <= 40) iepClass = 'Sem direção';
  else if (iep <= 60) iepClass = 'Em construção';
  else if (iep <= 80) iepClass = 'Ganhando forma';
  else iepClass = 'Pronto para acelerar';

  let ievClass = '';
  if (iev <= 40) ievClass = 'Ainda sem destaque';
  else if (iev <= 60) ievClass = 'Quase lá';
  else if (iev <= 80) ievClass = 'No caminho';
  else ievClass = 'Com diferencial';

  let mainDiagnostic = '';
  let copyMessage = '';
  let themeClasses = { bg: '', border: '', text: '' };

  if (iep > 60 && iev <= 60) {
    mainDiagnostic = 'Boa base, falta mostrar';
    copyMessage = 'Você já tem uma base legal. Agora é hora de transformar conhecimento em projetos, experiências e sinais claros do que você sabe fazer.';
    themeClasses = { bg: 'bg-orange-50', border: 'border-orange-500', text: 'text-orange-700' };
  }
  else if (iep <= 60 && iev > 60) {
    mainDiagnostic = 'Potencial sem direção';
    copyMessage = 'Você tem iniciativa e vontade de fazer acontecer. Com mais clareza e uma base melhor organizada, seus projetos podem ganhar muito mais força.';
    themeClasses = { bg: 'bg-[#2c9be3]/10', border: 'border-[#2c9be3]', text: 'text-[#2c9be3]' };
  }
  else if (iep > 60 && iev > 60) {
    mainDiagnostic = 'Pronto para avançar';
    copyMessage = 'Você combina preparo com atitude e já está construindo diferenciais. O próximo passo é escolher onde quer chegar e acelerar com intenção.';
    themeClasses = { bg: 'bg-emerald-50', border: 'border-emerald-500', text: 'text-emerald-700' };
  }
  else {
    mainDiagnostic = 'Hora de organizar a rota';
    copyMessage = 'Tudo bem ainda não ter tudo definido. O mais importante agora é organizar sua direção, testar possibilidades e dar passos pequenos, mas consistentes.';
    themeClasses = { bg: 'bg-red-50', border: 'border-red-500', text: 'text-red-700' };
  }

  return { iepClass, ievClass, mainDiagnostic, copyMessage, themeClasses };
};
