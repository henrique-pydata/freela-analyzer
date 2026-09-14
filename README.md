# Freela Analyzer

Sistema para coletar projetos do 99Freelas, manter apenas projetos ativos, analisar oportunidades com Gemini e exibir os resultados em um dashboard web responsivo.

## Arquitetura de produção

```text
                    ┌──────────────┐
Usuário ───────────► │   Frontend   │
                    └──────┬───────┘
                           │ HTTPS / JSON
                    ┌──────▼───────┐
                    │  FastAPI API │──────► SQL Server / Azure SQL
                    └──────┬───────┘              ▲
                           │ POST /sincronizar    │
                           ▼                       │
                    ┌──────────────┐               │
                    │ PENDENTE /   │───────────────┘
                    │ EXECUTANDO   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ Background   │
                    │ Worker       │
                    └──────┬───────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
           Playwright              Gemini
```

O endpoint `POST /sincronizar` não executa a sincronização. Ele apenas cria um job persistente e responde `202 Accepted`. Um Background Worker dedicado executa o Playwright e o Gemini fora do processo web. O frontend consulta `GET /sincronizacao` a cada 2 segundos para mostrar fase, progresso, projeto atual, sucessos e falhas.

O SQL Server foi usado como controle persistente do job porque já é uma dependência obrigatória da aplicação. Isso evita adicionar Redis apenas para uma fila de execução única e permite que o worker recupere jobs cujo heartbeat esteja vencido.

## Regras de negócio

- Projetos ativos permanecem no banco.
- Projetos confirmados como cancelados, encerrados, reprovados ou concluídos são removidos junto com a análise.
- Falhas de rede/navegação não removem projetos.
- Cada projeto mantém sua URL original do 99Freelas.
- A IA é apenas auxiliar; não há geração automática de propostas.
- Projetos existentes sem análise continuam elegíveis para análise nas próximas sincronizações.

## Desenvolvimento local

### Backend API

```powershell
python -m pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
$env:PYTHONPATH="."
python backend/scripts/migrate.py
uvicorn backend.src.api.app:app --reload --port 8000
```

### Worker

Em outro terminal:

```powershell
$env:PYTHONPATH="."
python -m backend.src.worker
```

### Frontend

```powershell
cd frontend
npm install
$env:VITE_API_URL="http://127.0.0.1:8000"
npm run dev
```

## Banco

Para uma base nova, crie a base `FreelaAnalyzer` no SQL Server e execute `python backend/scripts/migrate.py`. O runner aplica `backend/sql/000_bootstrap.sql` e `backend/sql/001_sincronizacao.sql` em ordem.

O bootstrap cria `dbo.projetos`, `dbo.analises_ia` e seus índices básicos. A migration incremental é idempotente e atualiza bases legadas com as colunas necessárias para status e progresso do worker.

## Deploy

O repositório inclui `render.yaml` com três serviços: frontend, API e Background Worker. A API e o worker usam a mesma imagem Docker, porém comandos de inicialização diferentes.

O projeto está preparado para Render e usa `PORT` em `0.0.0.0`. As configurações detalhadas, variáveis de ambiente e o procedimento de banco estão em `DEPLOY.md`.
