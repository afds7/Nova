# Testes do Hub Estratégico NOVA

## Backend

Instalação:

```powershell
cd back
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Execução:

```powershell
.venv\Scripts\python.exe -m pytest diagnostico/tests -q
```

Os testes usam SQLite temporário do pytest-django, fixtures simples e mocks para OpenAI. Nenhuma chave real ou chamada externa é usada.

## Frontend

Instalação:

```powershell
cd front
npm install
```

Execução dos testes:

```powershell
npm test -- --runInBand
```

Validação de build:

```powershell
npm run build
```

## Arquivos

- `QA_CHECKLIST.md`: fluxo manual completo, incluindo casos de produção, fallback e permissões.
- `back/pytest.ini`: configuração do pytest-django.
- `back/requirements-dev.txt`: dependências de teste do backend.
- `back/diagnostico/tests/`: testes de modelos, endpoints, fallback de IA, PII e isolamento.
- `front/jest.config.ts`: configuração Jest integrada ao Next.js.
- `front/components/__tests__/Quiz.test.tsx`: testes de edição manual da sugestão e erro amigável de API.
