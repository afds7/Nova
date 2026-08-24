
# 🎯 Hub Estratégico NOVA

O **Hub Estratégico NOVA** é uma plataforma inovadora de mapeamento e direcionamento universitário. Através de um diagnóstico rápido, o sistema calcula o **Índice Estratégico de Preparação (IEP)** e o **Índice Estratégico de Vantagem (IEV)** do aluno, cruzando dados comportamentais e acadêmicos para entregar um perfil estratégico e captar leads qualificados.

O produto também fecha o ciclo de evolução do aluno: **Diagnóstico -> Missão -> Evidência -> Dashboard**. As missões são priorizadas por regras de competência e podem receber personalização textual da IA, sempre com fallback determinístico e linguagem sugestiva.

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
- **Storage de arquivos:** Upload direto para Cloudflare R2/AWS S3 via presigned URL; nenhum arquivo de usuário é persistido no disco do Railway.
- **Cache:** Redis em produção via `REDIS_URL`, com cache local em memória para desenvolvimento.

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
├── QA_CHECKLIST.md             # Checklist manual ponta a ponta
├── TESTING.md                  # Testes automatizados e comandos
└── LOAD_TESTING.md             # Testes de carga com Locust

```

----------

## 🛠️ Como rodar o projeto localmente

O ambiente de desenvolvimento foi totalmente automatizado com Docker. Você não precisa instalar Node, Python ou Postgres na sua máquina, apenas o Docker.

### Opção A: Docker Compose

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

### Opção B: executar frontend e backend separadamente

Backend:

```powershell
cd back
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Frontend, em outro terminal:

```powershell
cd front
npm install
npm run dev
```


### 3. Acessar a aplicação

-   **Frontend (Interface do Usuário):** [http://localhost:3000](https://www.google.com/search?q=http://localhost:3000&authuser=1)

-   **Backend (API):** O endpoint principal está em `http://localhost:8000/api/assessments/submit/`

### Variáveis de ambiente

Copie `.env.example` para `.env` localmente e preencha apenas os valores necessários. Nunca envie `.env` para o GitHub.

Frontend:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXTAUTH_SECRET=um-segredo-longo-gerado-localmente
```

Backend em produção:

```env
SECRET_KEY=...
DATABASE_URL=...
OPENAI_API_KEY=...
TAVILY_API_KEY=...
REDIS_URL=redis://...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=...
AWS_S3_ENDPOINT_URL=...
AWS_S3_PUBLIC_BASE_URL=...
```

As chaves reais devem ser configuradas no provedor de deploy, como Railway e Vercel, por variáveis protegidas.


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

-   **Histórico:** Evoluções do IEP são adicionadas como novos registros. Evidências são arquivadas por soft delete, sem remoção silenciosa.

-   **IA:** Nome e e-mail não são enviados à OpenAI ou Tavily. Falhas, rate limits e indisponibilidade externa usam fallback e não interrompem o fluxo principal.

-   **Cache:** O cache reduz chamadas repetidas sem impedir o salvamento de novos diagnósticos ou a atualização do histórico. Após mudanças relevantes, o cache do perfil é invalidado.

## 🧪 Testes

Backend:

```powershell
cd back
.venv\Scripts\python.exe -m pytest diagnostico/tests -q
```

Frontend:

```powershell
cd front
npm test -- --runInBand
npm run build
```

Teste de carga local, usando um perfil sintético:

```powershell
cd back
$env:NOVA_PROFILE_ID="UUID-DE-UM-PERFIL-SINTETICO"
.venv\Scripts\python.exe -m locust -f load_tests\locustfile.py `
  --host http://127.0.0.1:8000 --headless -u 5 -r 1 -t 30s
```

O teste de carga deve ser executado em ambiente local ou staging. Consulte [TESTING.md](TESTING.md), [QA_CHECKLIST.md](QA_CHECKLIST.md) e [LOAD_TESTING.md](LOAD_TESTING.md) para detalhes.


----------

Desenvolvido com ☕ e 💻 por Dejota.
