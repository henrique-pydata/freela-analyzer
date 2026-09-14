# Freela Analyzer — Backend

FastAPI + Playwright + SQL Server/Azure SQL + Gemini.

## Configuração

Copie `.env.example` para `.env` e preencha as variáveis. Em produção, use as variáveis do Render.

`PLAYWRIGHT_HEADLESS=true` deve permanecer ativo no servidor.

## Execução local

API:

```powershell
$env:PYTHONPATH="."
uvicorn backend.src.api.app:app --reload --port 8000
```

Worker:

```powershell
$env:PYTHONPATH="."
python -m backend.src.worker
```

Migration:

```powershell
python backend/scripts/migrate.py
```

## Endpoints principais

- `GET /health` — saúde da API e conectividade com o banco.
- `GET /estatisticas` — estatísticas do dashboard.
- `GET /sincronizacao` — estado e progresso do job atual.
- `POST /sincronizar` — enfileira uma sincronização e retorna imediatamente.
- `GET /projetos` — lista paginada de projetos ativos.
- `GET /projetos/melhores` — melhores oportunidades.
- `GET /projetos/{id}` — detalhe do projeto.
- `GET /projetos/{id}/analise` — análise de IA.

## Job assíncrono

O endpoint de sincronização não usa `BackgroundTasks` do FastAPI. O servidor web grava `PENDENTE` em `dbo.sincronizacao_status`; um Background Worker separado adquire o job e executa o Playwright/Gemini.

O estado persistido contém:

- status (`PENDENTE`, `EXECUTANDO`, `CONCLUIDA`, `FALHOU`);
- fase atual;
- progresso atual/total;
- quantidade de sucessos e falhas;
- projeto em processamento;
- mensagem e erro;
- timestamp de heartbeat.

Cada projeto é processado dentro de `try/except` próprio. Uma falha de scraper, banco ou Gemini afeta somente aquele projeto; o worker continua nos demais.
