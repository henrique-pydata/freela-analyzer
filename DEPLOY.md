# Deploy do Freela Analyzer no Render

A arquitetura de produção é composta por três serviços:

- **Frontend:** TanStack Start/Node em um Web Service.
- **API:** FastAPI + Playwright + ODBC Driver 18 em um Web Service.
- **Worker:** mesmo container do backend, mas iniciado como Background Worker. Ele é o único processo que executa a sincronização pesada.
- **Banco:** SQL Server/Azure SQL gerenciado, acessível pela API e pelo worker.

O botão **Sincronizar** apenas cria uma execução persistente com status `PENDENTE` e responde `202 Accepted`. O worker pega o job, atualiza o progresso no banco e o frontend consulta `GET /sincronizacao` a cada 2 segundos. Assim, os ~3 minutos de trabalho nunca ficam presos dentro de uma requisição HTTP.

O Render documenta Background Workers justamente para retirar tarefas longas do caminho das requisições; o serviço de worker não recebe tráfego HTTP e normalmente consome uma fila/controle compartilhado. Este projeto usa o próprio SQL Server como fila persistente porque já é uma dependência obrigatória e não cria uma nova dependência em Redis.

## 1. Banco de dados do zero

Crie primeiro a base `FreelaAnalyzer` no SQL Server. Depois configure `FREELA_DB_CONNECTION_STRING` apontando para essa base.

### PowerShell local

```powershell
$env:PYTHONPATH="."
python -m pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
# Edite backend/.env e preencha FREELA_DB_CONNECTION_STRING e GEMINI_API_KEY
python backend/scripts/migrate.py
```

O bootstrap `backend/sql/000_bootstrap.sql` cria `dbo.projetos` e `dbo.analises_ia`. A migration `backend/sql/001_sincronizacao.sql` cria/atualiza o controle persistente da sincronização e é compatível com a base legada.

Para uma base existente, rode também `python backend/scripts/migrate.py`; as migrations são idempotentes.

## 2. Variáveis do backend

Use `backend/.env.example` como referência. Nunca publique `.env` no Git.

No Render, cadastre pelo menos:

```text
FREELA_DB_CONNECTION_STRING=...
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.6-flash
GEMINI_MAX_TENTATIVAS=4
GEMINI_BACKOFF_INICIAL=2
GEMINI_BACKOFF_MAXIMO=60
GEMINI_INTERVALO_MINIMO=2
PLAYWRIGHT_HEADLESS=true
FREELA_CORS_ORIGINS=https://SEU-FRONTEND.onrender.com
LOG_LEVEL=INFO
SYNC_WORKER_POLL_SECONDS=2
SYNC_STALE_MINUTES=10
```

O `render.yaml` marca os segredos com `sync: false`, seguindo a recomendação do Render para não gravar chaves e strings de conexão no repositório.

## 3. Deploy

Na raiz do repositório já existe `render.yaml`. Crie um Blueprint a partir dele.

O backend usa `0.0.0.0` e a variável `PORT` do Render. O health check é `/health`. O Render exige que aplicações HTTP escutem no `PORT` fornecido e recomenda health checks HTTP para verificar dependências críticas como banco de dados.

O worker usa o mesmo Dockerfile do backend e o comando:

```text
python backend/scripts/migrate.py && python -m backend.src.worker
```

O web service usa:

```text
python backend/scripts/migrate.py && uvicorn backend.src.api.app:app --host 0.0.0.0 --port ${PORT:-10000}
```

O Blueprint configura o encerramento gracioso do worker/API em até 300 segundos, dentro do limite documentado pelo Render, para reduzir interrupções durante deploy/restart.

### Custo

O Render atualmente lista Background Workers entre os tipos de serviço pagos e oferece `0.5c-512mb` como o menor plano pago de worker. O plano Free é oferecido para Web Services, Static Sites, Postgres e Key Value, mas não para Background Workers. Portanto, a arquitetura realmente autônoma com worker dedicado exige pelo menos um serviço de worker pago.

Para economizar, o frontend pode permanecer no `free` enquanto o worker usa `0.5c-512mb`.

## 4. Fluxo em produção

1. Usuário clica em **Sincronizar**.
2. API grava `PENDENTE` e responde em milissegundos.
3. Worker detecta o job e muda para `EXECUTANDO`.
4. Progresso é persistido após cada projeto.
5. Cada projeto possui tratamento de exceção individual; falhas não interrompem os demais.
6. O frontend consulta `/sincronizacao` a cada 2 segundos.
7. Ao finalizar, o worker grava `CONCLUIDA`; em erro fatal, grava `FALHOU`.
8. Se o worker morrer, um novo worker pode retomar uma execução cujo heartbeat esteja vencido após `SYNC_STALE_MINUTES`.

## 5. Teste pós-deploy

```text
GET https://SEU-BACKEND.onrender.com/health
GET https://SEU-BACKEND.onrender.com/sincronizacao
POST https://SEU-BACKEND.onrender.com/sincronizar
```

Depois abra o frontend e confirme que o card de progresso passa por **Verificando**, **Coletando** e **Analisando**, sem bloquear a interface.
