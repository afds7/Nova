export type QuestionBlock = 'IEP' | 'IEV';

export interface Question {
  id: number;
  block: QuestionBlock;
  category: string;
  text: string;
}

export const QUESTIONS: Question[] = [
  // BLOCO 1 - IEP (Acadêmico: 1-3)
  { id: 1, block: 'IEP', category: 'Acadêmico', text: 'Você tem clareza sobre quais matérias são mais importantes para o seu objetivo?' },
  { id: 2, block: 'IEP', category: 'Acadêmico', text: 'Seu desempenho atual reflete seu real potencial?' },
  { id: 3, block: 'IEP', category: 'Acadêmico', text: 'Você tem um plano de estudos estruturado?' },
  // BLOCO 1 - IEP (Estratégico/Carreira: 4-6)
  { id: 4, block: 'IEP', category: 'Estratégico / Carreira', text: 'Você sabe qual carreira quer seguir?' },
  { id: 5, block: 'IEP', category: 'Estratégico / Carreira', text: 'Você entende o que o mercado exige para essa carreira?' },
  { id: 6, block: 'IEP', category: 'Estratégico / Carreira', text: 'Você está construindo diferenciais (projetos, cursos, experiências)?' },
  // BLOCO 1 - IEP (Comportamental: 7-9)
  { id: 7, block: 'IEP', category: 'Comportamental', text: 'Você consegue manter consistência nos seus estudos?' },
  { id: 8, block: 'IEP', category: 'Comportamental', text: 'Eu tomo decisões de forma calculada e estratégica, em vez de agir por impulso.' },
  { id: 9, block: 'IEP', category: 'Comportamental', text: 'Você revisa e ajusta suas decisões com frequência?' },

  // BLOCO 2 - IEV (Diferenciação: 10-11)
  { id: 10, block: 'IEV', category: 'Diferenciação', text: 'Você está fazendo algo além do que a maioria dos alunos faz?' },
  { id: 11, block: 'IEV', category: 'Diferenciação', text: 'Você tem habilidades que te destacam?' },
  // BLOCO 2 - IEV (Prova Real: 12-13)
  { id: 12, block: 'IEV', category: 'Prova Real', text: 'Você já construiu algo concreto? (projetos, portfólio, etc.)' },
  { id: 13, block: 'IEV', category: 'Prova Real', text: 'Você consegue provar sua capacidade?' },
  // BLOCO 2 - IEV (Mundo Real: 14-15)
  { id: 14, block: 'IEV', category: 'Mundo Real', text: 'Você já teve contato com o mercado real?' },
  { id: 15, block: 'IEV', category: 'Mundo Real', text: 'Você já aplicou o que aprende na prática?' },
  // BLOCO 2 - IEV (Posicionamento: 16-17)
  { id: 16, block: 'IEV', category: 'Posicionamento', text: 'Você sabe se comunicar sobre o que você faz?' },
  { id: 17, block: 'IEV', category: 'Posicionamento', text: 'Você já construiu alguma presença (LinkedIn, portfólio, etc.)?' },
];