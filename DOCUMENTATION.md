# 🎯 Documentação do Projeto: Hub Estratégico NOVA

Esta documentação fornece uma visão geral completa do **Hub Estratégico NOVA**, detalhando sua arquitetura, funcionamento de negócio (cálculos e algoritmos), estrutura de dados, integradores de inteligência artificial, manual de execução local e especificações técnicas gerais.

---

## 📌 1. Visão Geral da Solução

O **Hub Estratégico NOVA** é uma plataforma que atua no mapeamento de direcionamento de carreira acadêmica e profissional de estudantes. Através de um questionário interativo, o sistema calcula dois índices chave para o estudante:
1. **IEP (Índice Estratégico de Preparação)**: Avalia a clareza de metas, organização acadêmica e foco comportamental.
2. **IEV (Índice Estratégico de Vantagem)**: Avalia diferenciação prática, portfólio, contato com o mercado real e networking.

Baseando-se no cruzamento desses índices, o sistema define um perfil de diagnóstico do estudante (ex: *Bom Aluno Comum*, *Talento Mal Direcionado*, *Alta Performance Real*, ou *Alto Risco*) e aciona um serviço de inteligência artificial (com OpenAI GPT-4o-Mini e buscas dinâmicas com Tavily) para gerar um **Plano de Ação Tático Personalizado** altamente focado no mercado, enquanto capta leads qualificados de forma segura em conformidade com as diretrizes de privacidade.

---

## 🛠️ 2. Arquitetura e Stack Tecnológica

O projeto adota um padrão de **Monorepo** orquestrado em containers Docker, separando rigidamente o cliente (Frontend) da API de negócio (Backend).

### 🖥️ Frontend (Interface do Usuário)
- **Framework:** [Next.js 14+](https://nextjs.org) utilizando o modelo de diretórios **App Router** com **TypeScript**.
- **Estilização:** [Tailwind CSS](https://tailwindcss.com) para um design fluído, responsivo e baseado em classes utilitárias.
- **Gerenciamento de Estado:** [Zustand](https://github.com/pmndrs/zustand) para controle de estado do questionário e leads de forma volátil (evitando persistência desnecessária no navegador por segurança e privacidade).

### ⚙️ Backend (API de Negócio)
- **Framework:** [Django](https://djangoproject.com) & [Django Rest Framework (DRF)](https://django-rest-framework.org) em Python 3.12.
- **Gerenciador de Dependências:** [Poetry](https://python-poetry.org) para ambiente determinista e empacotamento.
- **Banco de Dados:** [PostgreSQL 16](https://www.postgresql.org) para persistência transacional segura.
- **Segurança:** Utilização de UUID como Primary Keys nas tabelas, além de isolamento de variáveis sensíveis via `.env`.

---

## 📂 3. Estrutura de Pastas

A estrutura organizacional do repositório é configurada da seguinte forma:

```text
nova-hub/
├── docker-compose.yml          # Definição e orquestração de containers (db, back, front)
├── .env                        # Variáveis de ambiente secretas (chaves de API, banco)
├── .gitignore                  # Regras de exclusão do versionamento Git
├── README.md                   # Documentação resumida
├── DOCUMENTATION.md            # [Esta Documentação Completa]
│
├── back/                       # Pasta raíz do backend Django
│   ├── core/                   # Módulo de configuração global do Django (settings, urls, wsgi)
│   ├── assessments/            # Aplicativo de leads e diagnósticos
│   │   ├── migrations/         # Histórico de alterações e estruturação da base de dados
│   │   ├── admin.py            # Configurações do painel administrativo Django Admin
│   │   ├── apps.py             # Registro e inicialização do app
│   │   ├── models.py           # Modelos de dados do banco (PostgreSQL)
│   │   ├── serializers.py      # Serialização e validação das submissões da API
│   │   ├── services.py         # Lógica de integração com OpenAI, Tavily e Marketing Copy
│   │   ├── urls.py             # Declaração das rotas de endpoint do app
│   │   └── views.py            # Controlador e regras de requisição e resposta
│   ├── Dockerfile              # Imagem Docker para o Backend
│   ├── pyproject.toml          # Configuração do Poetry e dependências Python
│   └── poetry.lock             # Registro travado de versões exatas do Poetry
│
└── front/                      # Pasta raíz do frontend Next.js
    ├── app/                    # Arquivos globais do App Router (layout, globals.css, homepage)
    ├── components/             # Componentes modulares React (ex: Quiz.tsx)
    ├── constants/              # Constantes e matriz de dados estáticos (perguntas)
    ├── store/                  # Configurações de estado global do Zustand
    ├── utils/                  # Utilitários, funções auxiliares e lógica matemática de pontuação
    ├── Dockerfile              # Imagem Docker do Frontend
    ├── package.json            # Script executável e dependências Node.js
    └── tsconfig.json           # Configuração de tipagem do TypeScript
```

---

## 📊 4. Especificações de Negócio e Lógica Matemática

### 📋 As Perguntas do Diagnóstico
O questionário é estruturado em **17 perguntas** avaliadas em uma escala Likert de **1 a 5** (onde 1 é o menor nível e 5 é o maior). As perguntas estão separadas em dois grandes blocos de avaliação:

#### Bloco 1: IEP (Índice Estratégico de Preparação)
Mapeia a fundação de estudos e clareza do aluno. Possui três subcategorias:
*   **Acadêmico (Questões 1, 2, 3):** Foco nas matérias prioritárias, rendimento escolar e estrutura de estudo.
*   **Estratégico / Carreira (Questões 4, 5, 6):** Conhecimento das demandas de mercado e planejamento profissional.
*   **Comportamental (Questões 7, 8, 9):** Consistência, tomada de decisão estratégica e autoavaliação.

#### Bloco 2: IEV (Índice Estratégico de Vantagem)
Mapeia a execução prática e a competitividade. Dividido em quatro subcategorias:
*   **Diferenciação (Questões 10, 11):** Nível de habilidades excepcionais e ações fora do padrão dos estudantes.
*   **Prova Real (Questões 12, 13):** Existência de projetos reais entregues e capacidade comprovada.
*   **Mundo Real (Questões 14, 15):** Vivência prévia no mercado profissional e aplicação prática.
*   **Posicionamento (Questões 16, 17):** Comunicação, portfólios visíveis e presença no LinkedIn.

### 📐 Lógica de Cálculo dos Scores
No arquivo `front/utils/math.ts`, a pontuação é apurada da seguinte maneira:

1.  **Cálculo da Média dos Pilares:**
    Calcula-se a média simples das respostas (1 a 5) associadas aos identificadores de questões de cada pilar:
    *   $A$ (Acadêmico) = Média das questões $[1, 2, 3]$
    *   $E$ (Estratégico) = Média das questões $[4, 5, 6]$
    *   $C$ (Comportamental) = Média das questões $[7, 8, 9]$
    *   $D$ (Diferenciação) = Média das questões $[10, 11]$
    *   $P$ (Prova Real) = Média das questões $[12, 13]$
    *   $M$ (Mundo Real) = Média das questões $[14, 15]$
    *   $S$ (Posicionamento) = Média das questões $[16, 17]$

2.  **Cálculo das Notas Finais (Escala 0 a 100):**
    *   **IEP (Preparo):** A pontuação pondera os pilares Acadêmico ($30\%$), Estratégico ($40\%$) e Comportamental ($30\%$), multiplicando por 20 para normalizar na escala centesimal:
        $$\text{IEP} = \text{Round}\left((A \times 0.3 + E \times 0.4 + C \times 0.3) \times 20\right)$$
    *   **IEV (Vantagem):** A pontuação pondera Diferenciação ($25\%$), Prova Real ($30\%$), Mundo Real ($25\%$) e Posicionamento ($20\%$), multiplicando por 20:
        $$\text{IEV} = \text{Round}\left((D \times 0.25 + P \times 0.30 + M \times 0.25 + S \times 0.20) \times 20\right)$$

3.  **Determinação de Força, Fraqueza e Gap:**
    *   **Ponto Forte / Ponto Fraco:** Os 7 pilares são ordenados com base nas médias calculadas. Caso haja empates exatos de pontuação, o algoritmo utiliza uma ordenação dinâmica aleatória para evitar viés posicional na entrega do relatório. O pilar com maior média é o Ponto Forte (`strongest_point`), e o de menor média é o Ponto Fraco (`weakest_point`).
    *   **Gap:** Diferença absoluta entre o preparo e a vantagem competitiva:
        $$\text{Gap} = |\text{IEP} - \text{IEV}|$$

### 🩺 Diagnósticos de Categoria
A partir do resultado final do IEP e do IEV, o estudante é classificado em um dos quadrantes de desempenho:
*   **Alta Performance Real** ($\text{IEP} > 60$ e $\text{IEV} > 60$)
*   **Bom Aluno Comum** ($\text{IEP} > 60$ e $\text{IEV} \le 60$)
*   **Talento Mal Direcionado** ($\text{IEP} \le 60$ e $\text{IEV} > 60$)
*   **Alto Risco** ($\text{IEP} \le 60$ e $\text{IEV} \le 60$)

---

## 🤖 5. Integração com Inteligência Artificial e Copys de Marketing

Ao enviar a submissão dos dados do diagnóstico, a API Django executa um fluxo híbrido para compor o relatório final:

1.  **Criação de Copy Determinística (Regras de Marketing):**
    Uma estrutura estática é resolvida no backend interpretando o IEP e o IEV, escrevendo uma narrativa crua dos riscos e potenciais das notas em que o lead se enquadra.
2.  **Busca de Mercado Externa (Tavily AI):**
    O backend detecta se o estudante possui uma área de interesse definida ou se está indeciso. É feita uma busca web via **Tavily API** buscando as faculdades de maior destaque, livros influentes e certificações atualizadas da área escolhida em 2026.
3.  **Geração do Plano Tático (OpenAI API):**
    O backend monta um prompt enviando os scores (IEP, IEV, Ponto Forte, Gargalo) e o contexto retornado pelo Tavily para o modelo **gpt-4o-mini**.
    *   *Diretiva Anti-Clichê:* O prompt proíbe respostas vagas como "faça networking" ou "busque no Google". Ele exige nomes reais de universidades renomadas, livros chave e ações imediatas detalhadas.
    *   *LGPD/Privacidade:* Dados pessoais como e-mail ou nome não são passados ao prompt da OpenAI para assegurar total privacidade de dados sensíveis.

---

## 💾 6. Especificações de Banco de Dados

Os dados são armazenados na tabela `assessments_lead` gerenciada pelo Django e mapeada para o banco PostgreSQL:

| Campo | Tipo no Banco | Descrição |
| :--- | :--- | :--- |
| `id` | `UUID` (Primary Key) | Identificador único universal gerado de forma aleatória e segura. |
| `name` | `VARCHAR(255)` | Nome fornecido pelo Lead. |
| `email` | `VARCHAR(254)` (Indexed) | Endereço de e-mail do Lead, indexado para consultas ágeis de auditoria. |
| `iep_score` | `INTEGER` | Pontuação final calculada de Preparação ($0$ a $100$). |
| `iev_score` | `INTEGER` | Pontuação final calculada de Vantagem Competitiva ($0$ a $100$). |
| `diagnostic` | `VARCHAR(100)` | Diagnóstico textual correspondente ao quadrante de desempenho. |
| `area` | `VARCHAR(100)` | Área acadêmica/profissional desejada informada pelo usuário. |
| `strongest_point` | `VARCHAR(100)` | Pilar com melhor desempenho geral do estudante. |
| `weakest_point` | `VARCHAR(100)` | Pilar com maior necessidade de melhoria (Gargalo). |
| `gap` | `INTEGER` | A diferença absoluta ($|\text{IEP} - \text{IEV}|$). |
| `action_plan` | `TEXT` | O plano de ação em formato Markdown completo retornado pela OpenAI. |
| `created_at` | `TIMESTAMP` | Data e hora em que a avaliação foi realizada. |

---

## ⚡ 7. Configuração e Variáveis de Ambiente

Para o funcionamento completo da aplicação, crie um arquivo `.env` na raiz do projeto contendo as chaves de acesso:

```env
# Banco de Dados PostgreSQL
DB_NAME=nova_db
DB_USER=postgres
DB_PASSWORD=postgres

# Integrações de Inteligência Artificial
OPENAI_API_KEY=sua_chave_da_openai_aqui
TAVILY_API_KEY=sua_chave_do_tavily_aqui
```

---

## 🚀 8. Como Rodar o Projeto Localmente

O ecossistema é totalmente dockerizado, eliminando a necessidade de instalar localmente Python, PostgreSQL ou Node.js.

### Requisitos Prévios
-   [Docker](https://www.docker.com/products/docker-desktop/) instalado e rodando.
-   [Docker Compose](https://docs.docker.com/compose/) habilitado.

### Executando Passo a Passo

1.  **Clonar e Configurar:**
    Navegue até a raiz do projeto e crie o seu arquivo `.env` conforme instruído na seção 7.

2.  **Iniciar os Containers:**
    Execute o comando abaixo para compilar as imagens e iniciar os serviços:
    ```bash
    docker compose up --build
    ```
    Este comando inicializa os três containers integrados:
    *   **`nova_db`** (Porta interna `5432` com PostgreSQL).
    *   **`nova_backend`** (Porta `8000` executando as migrações automáticas de banco de dados e inicializando a API Django).
    *   **`nova_frontend`** (Porta `3000` servindo a interface do Next.js em modo de desenvolvimento).

3.  **Urls de Acesso:**
    *   **Interface Web:** `http://localhost:3000`
    *   **Endpoint Principal da API:** `http://localhost:8000/api/assessments/submit/`

4.  **Auditoria e Acesso ao Banco de Dados (Via CLI):**
    Caso precise verificar os Leads cadastrados diretamente no PostgreSQL, utilize:
    ```bash
    docker compose exec db psql -U postgres -d nova_db
    ```
    No prompt SQL, você pode buscar os dados executando:
    ```sql
    SELECT name, email, iep_score, iev_score, diagnostic, area FROM assessments_lead;
    ```
    Para sair do prompt do banco de dados, digite `\q`.
