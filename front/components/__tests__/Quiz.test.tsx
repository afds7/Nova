import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { useSession, signIn } from 'next-auth/react';
import { useQuizStore } from '../../store/useQuizStore';
import { QUESTIONS } from '../../constants/questions';
import Quiz from '../Quiz';

jest.mock('next-auth/react', () => ({
  useSession: jest.fn(),
  signIn: jest.fn(),
}));

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
}));

// O teste valida o fluxo do formulário; o parser Markdown não faz parte do contrato testado.
jest.mock('react-markdown', () => ({ children }: { children: string }) => <div>{children}</div>);

const mockedUseSession = useSession as jest.MockedFunction<typeof useSession>;
const mockedSignIn = signIn as jest.MockedFunction<typeof signIn>;

describe('captura de objetivo e diagnóstico', () => {
  beforeEach(() => {
    jest.spyOn(console, 'error').mockImplementation(() => undefined);
    mockedUseSession.mockReturnValue({ data: null, status: 'unauthenticated', update: jest.fn() });
    mockedSignIn.mockResolvedValue({ ok: true, error: null, status: 200, url: null });
    useQuizStore.setState({
      currentStep: QUESTIONS.length + 1,
      answers: Object.fromEntries(QUESTIONS.map((question) => [question.id, 3])),
      leadInfo: { name: '', email: '', area: '' },
      actionPlan: '',
    });
    global.fetch = jest.fn();
  });

  afterEach(() => jest.restoreAllMocks());

  it('permite editar manualmente uma área sugerida pela regra', async () => {
    render(<Quiz />);

    const area = await screen.findByPlaceholderText('Ex: TI, Medicina, Design...');
    expect(area).not.toHaveValue('');
    fireEvent.change(area, { target: { value: 'Cinema e audiovisual' } });
    expect(area).toHaveValue('Cinema e audiovisual');

    // Um re-render externo, como o fundo reativo ao mouse, não sobrescreve a edição.
    fireEvent.change(area, { target: { value: 'Cinema e audiovisual' } });
    expect(area).toHaveValue('Cinema e audiovisual');
  });

  it('mostra erro amigável quando o submit da API falha', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 503,
      text: async () => JSON.stringify({ error: 'API temporariamente indisponível' }),
    });
    render(<Quiz />);

    fireEvent.change(screen.getByPlaceholderText('Seu nome'), { target: { value: 'Pessoa QA' } });
    fireEvent.change(screen.getByPlaceholderText('seu@email.com'), { target: { value: 'qa@example.com' } });
    fireEvent.change(screen.getByPlaceholderText('Crie uma senha (mínimo 6 caracteres)'), { target: { value: 'senha-segura' } });
    fireEvent.click(screen.getByRole('button', { name: /ver meu resultado/i }));

    await waitFor(() => expect(screen.getByText('API temporariamente indisponível')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: /ver meu resultado/i })).toBeEnabled();
  });
});
