
# 🎯 Hub Estratégico NOVA

O **Hub Estratégico NOVA** é uma plataforma inovadora de mapeamento e direcionamento universitário. Através de um diagnóstico rápido, o sistema calcula o **Índice Estratégico de Preparação (IEP)** e o **Índice Estratégico de Vantagem (IEV)** do aluno, cruzando dados comportamentais e acadêmicos para entregar um perfil estratégico e captar leads qualificados.

## 🚀 Arquitetura e Stack Tecnológica

O projeto foi construído utilizando uma arquitetura moderna e escalável, focada em segurança de dados (LGPD) e integridade transacional, idealizada no formato Monorepo e orquestrada via Docker.

### Frontend
- **Framework:** Next.js 14+ (App Router, React, TypeScript)
- **Estilização:** Tailwind CSS
- **Gerenciamento de Estado:** Zustand (Estado volátil em memória para maior privacidade)

### Backend
- **Framework:** Django & Django Rest Framework (Python)
- **Gerenciador de Dependências:** Poetry (Garante determinismo de ambiente)
- **Banco de Dados:** PostgreSQL 16
- **Segurança:** CorsHeaders, dj-database-url, UUID como Primary Keys

### Infraestrutura
- **Containers:** Docker & Docker Compose
- **Imagens:** Otimizadas (Alpine/Slim) com usuários non-root para segurança.

---

## 📂 Estrutura de Pastas e Infraestrutura

O projeto segue um padrão de Monorepo, separando responsabilidades entre backend (API) e frontend (Interface), unidos por um orquestrador de containers na raiz.

```text
NOVA_HUB/
├── back/                       # Backend Django (API)
│   ├── assessments/            # App principal (Leads e Lógica de Negócio)
│   │   ├── migrations/         # Versionamento do Banco de Dados
│   │   ├── models.py           # Modelagem de dados (PostgreSQL)
│   │   ├── serializers.py      # Validação e serialização de dados (DRF)
│   │   ├── services.py         # Lógica e Integrações de IA (OpenAI / Tavily)
│   │   ├── urls.py             # Roteamento de endpoints do app
│   │   └── views.py            # Controladores da API
│   ├── Dockerfile              # Container do backend
│   ├── manage.py               # Utilitário administrativo do Django
│   ├── poetry.lock             # Trava de dependências do Python
│   └── pyproject.toml          # Lista de dependências (Poetry)
│
├── front/                      # Frontend Next.js
│   ├── app/                    # Next.js App Router (Páginas e CSS Global)
│   ├── components/             # Componentes React
│   │   └── Quiz.tsx            # Motor principal e UI do formulário
│   ├── constants/              # Dados estáticos
│   │   └── questions.ts        # Matriz das perguntas e categorias
│   ├── store/                  # Gerenciamento de estado (Zustand)
│   │   └── useQuizStore.ts     # Estado global de respostas e Lead
│   ├── utils/                  # Funções utilitárias
│   │   └── math.ts             # Motor de cálculo dos scores estratégicos
│   ├── Dockerfile              # Container do frontend
│   └── package.json            # Dependências e scripts do Node.js
│
├── .env                        # Variáveis de ambiente secretas (Chaves de API, DB)
├── .gitignore                  # Arquivos ignorados pelo Git
├── docker-compose.yml          # Orquestração da infraestrutura (db, back, front)
├── README.md                   # Documentação do projeto
└── tasks.md                    # Roadmap, controle de versão e backlog

```

----------

## 🛠️ Como rodar o projeto localmente

O ambiente de desenvolvimento foi totalmente automatizado com Docker. Você não precisa instalar Node, Python ou Postgres na sua máquina, apenas o Docker.

### 1. Clonar o repositório

Bash

```
git clone [https://github.com/Dejota-04/nova-hub.git](https://github.com/Dejota-04/nova-hub.git)
cd nova_hub

```

### 2. Subir os containers

Na raiz do projeto, execute:

Bash

```
docker compose up --build

```

O Docker Compose cuidará de:

1.  Subir o banco de dados PostgreSQL.

2.  Instalar as dependências do Python via Poetry e subir a API na porta `8000`.

3.  Instalar os pacotes NPM e subir o Next.js na porta `3000`.


### 3. Acessar a aplicação

-   **Frontend (Interface do Usuário):** [http://localhost:3000](https://www.google.com/search?q=http://localhost:3000&authuser=1)

-   **Backend (API):** O endpoint principal está em `http://localhost:8000/api/assessments/submit/`


### 4. Acessar o Banco de Dados (Opcional)

Para auditar os leads salvos localmente:

Bash

```
docker compose exec db psql -U postgres -d nova_db
# Dentro do console do psql:
# SELECT name, email, iep_score, iev_score, diagnostic FROM assessments_lead;

```

----------

## 🔒 Considerações de Segurança (Design)

-   **Proteção de Dados:** Coleta mínima de PII necessária para geração do lead. Sem uso de LocalStorage para dados sensíveis.

-   **Isolamento:** O frontend comunica-se exclusivamente via API, sem acesso direto ao banco.


----------

Desenvolvido com ☕ e 💻 por Dejota.