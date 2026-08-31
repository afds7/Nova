import { act, render, screen, waitFor } from '@testing-library/react';
import { useSession } from 'next-auth/react';
import RecommendationsPage from './page';
import { useRecommendationsStore } from '../../store/useRecommendationsStore';

jest.mock('next-auth/react', () => ({
  useSession: jest.fn(),
  signOut: jest.fn(),
}));

const mockedUseSession = useSession as jest.MockedFunction<typeof useSession>;

describe('RecommendationsPage', () => {
  beforeEach(() => {
    mockedUseSession.mockReturnValue({
      data: {
        user: { id: 'current-profile' } as { id: string },
        expires: '2099-01-01T00:00:00.000Z',
      },
      status: 'authenticated',
      update: jest.fn(),
    } as ReturnType<typeof useSession>);
    act(() => {
      useRecommendationsStore.setState({ data: null, isLoading: false, error: null });
    });
    global.fetch = jest.fn(() => new Promise(() => undefined));
  });

  afterEach(() => {
    jest.restoreAllMocks();
    act(() => {
      useRecommendationsStore.setState({ data: null, isLoading: false, error: null });
    });
  });

  it('mostra loading enquanto gera recomendações para o perfil atual', async () => {
    render(<RecommendationsPage />);

    expect(await screen.findByText('Estamos gerando as suas sugestões')).toBeInTheDocument();
  });

  it('não exibe recomendações antigas enquanto busca recomendações novas', async () => {
    act(() => {
      useRecommendationsStore.setState({
        data: {
          perfil_id: 'old-profile',
          area: 'Área antiga',
          competencia_prioritaria: null,
          origem: 'fallback',
          resumo: 'Resumo antigo',
          itens: [{
            tipo: 'faculdade',
            titulo: 'Faculdade antiga',
            descricao: 'Descrição antiga',
            o_que_fazer: 'Fazer antigo',
            como_fazer: 'Como antigo',
            opcoes: [],
            por_que_pode_fazer_sentido: 'Motivo antigo',
            url: '',
            nivel: 'graduação',
            estimativa_tempo: '4 anos',
          }],
          proximos_passos: [],
          comunidades: [],
        },
        isLoading: false,
        error: null,
      });
    });

    render(<RecommendationsPage />);

    expect(await screen.findByText('Estamos gerando as suas sugestões')).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByText('Faculdade antiga')).not.toBeInTheDocument());
  });
});
