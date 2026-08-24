# Teste de carga do Hub NOVA

O teste usa Locust para simular acessos concorrentes às telas de Dashboard, Missões sugeridas e Portfólio. Ele é somente leitura: não cria missões, não publica evidências e não dispara diagnóstico ou chamadas reais à OpenAI/Tavily.

## Preparar um ambiente seguro

Use local ou staging com um perfil sintético. Não execute contra produção sem autorização explícita e sem limites definidos no provedor.

```powershell
cd back
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:NOVA_PROFILE_ID = "UUID-DE-UM-PERFIL-SINTETICO"
```

## Execução web

Com o backend disponível em `http://127.0.0.1:8000`:

```powershell
cd back
.venv\Scripts\python.exe -m locust -f load_tests\locustfile.py --host http://127.0.0.1:8000
```

Abra `http://localhost:8089`, informe a quantidade de usuários e a taxa de criação. O formato sem interface também pode ser usado para CI:

```powershell
.venv\Scripts\python.exe -m locust -f load_tests\locustfile.py `
  --host https://URL-DE-STAGING `
  --headless -u 100 -r 10 -t 5m `
  --csv=artifacts\nova-load
```

Para um smoke test local de 5 segundos:

```powershell
$env:NOVA_PROFILE_ID = "UUID-DE-UM-PERFIL-SINTETICO"
.venv\Scripts\python.exe -m locust -f load_tests\locustfile.py `
  --host http://127.0.0.1:8000 --headless -u 1 -r 1 -t 5s --only-summary
```

Quando `-u/-r/-t` não forem informados, a rampa automática do arquivo executa 10, 50 e 100 usuários.

## O que observar

- taxa de falhas: objetivo inicial abaixo de 1% em staging;
- respostas `200` acima do limite de latência também são marcadas como falha;
- p95 e p99 de latência por endpoint;
- requests por segundo;
- respostas 5xx, timeouts e conexões recusadas;
- CPU, memória, workers Gunicorn, conexões do PostgreSQL e limites do provedor;
- crescimento de memória ao longo do teste, indicando vazamento;
- comportamento após reduzir a carga: o serviço deve recuperar sem reinício manual.

O arquivo `back/load_tests/locustfile.py` falha imediatamente se `NOVA_PROFILE_ID` não for informado ou não for UUID. Isso evita executar uma carga inválida ou atingir dados pessoais por engano.

Os limites padrão são `1000ms` para Dashboard/Portfólio e `3000ms` para Missões. Eles podem ser ajustados explicitamente com `NOVA_MAX_DASHBOARD_MS`, `NOVA_MAX_MISSIONS_MS` e `NOVA_MAX_PORTFOLIO_MS`; não devem ser aumentados apenas para esconder uma regressão.

## Cenário compatível com o produto

O produto prevê aproximadamente 150 usuários por mês. Esse número representa usuários ativos no mês, não 150 pessoas simultâneas. Para uma validação realista, use:

- carga nominal: 5 usuários concorrentes;
- pico conservador: 15 a 20 usuários concorrentes;
- estresse com margem: 50 e 100 usuários concorrentes.

Cada usuário faz várias requisições durante uma sessão, então o volume mensal não deve ser convertido diretamente em 150 usuários simultâneos. O cenário de 100 usuários continua útil como teste de margem, mas não é uma previsão de uso normal.

Considere o ambiente aprovado quando a carga nominal e o pico permanecerem estáveis, sem crash, sem aumento contínuo de memória, sem 5xx recorrente e com p95 dentro da meta definida para o produto. Registre separadamente a capacidade nominal, o pico suportado e o ponto em que o sistema começa a degradar.
