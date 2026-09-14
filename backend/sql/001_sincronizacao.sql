/*
   Migration incremental para bancos existentes.
   Em uma base nova, 000_bootstrap.sql já cria tudo isso; as cláusulas abaixo
   continuam sendo executáveis de forma idempotente.
*/

IF COL_LENGTH('dbo.projetos', 'status') IS NULL
BEGIN
    ALTER TABLE dbo.projetos ADD status VARCHAR(20) NOT NULL
        CONSTRAINT DF_projetos_status DEFAULT 'ATIVO' WITH VALUES;
END
GO

IF COL_LENGTH('dbo.projetos', 'ultima_verificacao') IS NULL
BEGIN
    ALTER TABLE dbo.projetos ADD ultima_verificacao DATETIME2 NULL;
END
GO

UPDATE dbo.projetos
SET ultima_verificacao = data_coleta
WHERE ultima_verificacao IS NULL;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name='IX_projetos_status'
      AND object_id=OBJECT_ID('dbo.projetos')
)
BEGIN
    CREATE INDEX IX_projetos_status ON dbo.projetos(status);
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name='IX_projetos_ultima_verificacao'
      AND object_id=OBJECT_ID('dbo.projetos')
)
BEGIN
    CREATE INDEX IX_projetos_ultima_verificacao ON dbo.projetos(ultima_verificacao);
END
GO

IF OBJECT_ID('dbo.sincronizacao_status','U') IS NULL
BEGIN
    CREATE TABLE dbo.sincronizacao_status (
        id TINYINT NOT NULL CONSTRAINT PK_sincronizacao_status PRIMARY KEY,
        status VARCHAR(20) NOT NULL,
        inicio DATETIME2 NULL,
        fim DATETIME2 NULL,
        erro NVARCHAR(2000) NULL,
        fase VARCHAR(30) NOT NULL CONSTRAINT DF_sinc_fase DEFAULT 'AGUARDANDO',
        progresso_atual INT NOT NULL CONSTRAINT DF_sinc_atual DEFAULT 0,
        progresso_total INT NOT NULL CONSTRAINT DF_sinc_total DEFAULT 0,
        sucessos INT NOT NULL CONSTRAINT DF_sinc_sucessos DEFAULT 0,
        falhas INT NOT NULL CONSTRAINT DF_sinc_falhas DEFAULT 0,
        projeto_atual NVARCHAR(500) NULL,
        mensagem NVARCHAR(1000) NULL,
        atualizado_em DATETIME2 NULL
    );
END
GO

IF COL_LENGTH('dbo.sincronizacao_status', 'fase') IS NULL
    ALTER TABLE dbo.sincronizacao_status ADD fase VARCHAR(30) NOT NULL CONSTRAINT DF_sinc_fase_legacy DEFAULT 'AGUARDANDO' WITH VALUES;
GO
IF COL_LENGTH('dbo.sincronizacao_status', 'progresso_atual') IS NULL
    ALTER TABLE dbo.sincronizacao_status ADD progresso_atual INT NOT NULL CONSTRAINT DF_sinc_atual_legacy DEFAULT 0 WITH VALUES;
GO
IF COL_LENGTH('dbo.sincronizacao_status', 'progresso_total') IS NULL
    ALTER TABLE dbo.sincronizacao_status ADD progresso_total INT NOT NULL CONSTRAINT DF_sinc_total_legacy DEFAULT 0 WITH VALUES;
GO
IF COL_LENGTH('dbo.sincronizacao_status', 'sucessos') IS NULL
    ALTER TABLE dbo.sincronizacao_status ADD sucessos INT NOT NULL CONSTRAINT DF_sinc_sucessos_legacy DEFAULT 0 WITH VALUES;
GO
IF COL_LENGTH('dbo.sincronizacao_status', 'falhas') IS NULL
    ALTER TABLE dbo.sincronizacao_status ADD falhas INT NOT NULL CONSTRAINT DF_sinc_falhas_legacy DEFAULT 0 WITH VALUES;
GO
IF COL_LENGTH('dbo.sincronizacao_status', 'projeto_atual') IS NULL
    ALTER TABLE dbo.sincronizacao_status ADD projeto_atual NVARCHAR(500) NULL;
GO
IF COL_LENGTH('dbo.sincronizacao_status', 'mensagem') IS NULL
    ALTER TABLE dbo.sincronizacao_status ADD mensagem NVARCHAR(1000) NULL;
GO
IF COL_LENGTH('dbo.sincronizacao_status', 'atualizado_em') IS NULL
    ALTER TABLE dbo.sincronizacao_status ADD atualizado_em DATETIME2 NULL;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.sincronizacao_status WHERE id = 1)
BEGIN
    INSERT INTO dbo.sincronizacao_status (
        id, status, fase, progresso_atual, progresso_total,
        sucessos, falhas, mensagem
    )
    VALUES (
        1, 'NUNCA_EXECUTADA', 'AGUARDANDO', 0, 0,
        0, 0, 'Nenhuma sincronização executada ainda.'
    );
END
GO

UPDATE dbo.sincronizacao_status
SET status = CASE WHEN status = 'EXECUTANDO' THEN status ELSE status END,
    atualizado_em = COALESCE(atualizado_em, fim, inicio)
WHERE id = 1;
GO
