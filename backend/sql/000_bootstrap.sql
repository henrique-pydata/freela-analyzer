/*
   Schema base do Freela Analyzer.
   Pode ser executado em uma base vazia e também é seguro em conjunto com a
   migration incremental 001_sincronizacao.sql.
*/

IF OBJECT_ID('dbo.projetos', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.projetos (
        id NVARCHAR(50) NOT NULL CONSTRAINT PK_projetos PRIMARY KEY,
        titulo NVARCHAR(500) NOT NULL,
        descricao NVARCHAR(MAX) NULL,
        url NVARCHAR(1000) NOT NULL,
        data_coleta DATETIME2 NOT NULL CONSTRAINT DF_projetos_data_coleta DEFAULT SYSUTCDATETIME(),
        ultima_verificacao DATETIME2 NULL,
        status VARCHAR(20) NOT NULL CONSTRAINT DF_projetos_status DEFAULT 'ATIVO',
        categoria NVARCHAR(200) NULL,
        subcategoria NVARCHAR(200) NULL,
        orcamento NVARCHAR(200) NULL,
        nivel_experiencia NVARCHAR(100) NULL,
        visibilidade NVARCHAR(100) NULL,
        propostas NVARCHAR(100) NULL,
        interessados NVARCHAR(100) NULL,
        projeto_exclusivo BIT NOT NULL CONSTRAINT DF_projetos_exclusivo DEFAULT 0
    );
END
GO

IF OBJECT_ID('dbo.analises_ia', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.analises_ia (
        projeto_id NVARCHAR(50) NOT NULL CONSTRAINT PK_analises_ia PRIMARY KEY,
        vale_a_pena VARCHAR(10) NOT NULL,
        score INT NOT NULL,
        dificuldade VARCHAR(20) NOT NULL,
        tecnologias NVARCHAR(MAX) NULL,
        riscos NVARCHAR(MAX) NULL,
        prazo_estimado NVARCHAR(200) NULL,
        orcamento_informado NVARCHAR(200) NULL,
        orcamento_justo NVARCHAR(200) NULL,
        faixa_preco NVARCHAR(200) NULL,
        justificativa NVARCHAR(MAX) NULL,
        pontos_esclarecer NVARCHAR(MAX) NULL,
        veredito NVARCHAR(MAX) NULL,
        data_analise DATETIME2 NOT NULL CONSTRAINT DF_analises_ia_data DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_analises_ia_projeto
            FOREIGN KEY (projeto_id) REFERENCES dbo.projetos(id) ON DELETE CASCADE,
        CONSTRAINT CK_analises_ia_score CHECK (score BETWEEN 0 AND 100)
    );
END
GO

IF COL_LENGTH('dbo.projetos', 'ultima_verificacao') IS NOT NULL
BEGIN
    UPDATE dbo.projetos
    SET ultima_verificacao = data_coleta
    WHERE ultima_verificacao IS NULL;
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_projetos_status'
      AND object_id = OBJECT_ID('dbo.projetos')
)
BEGIN
    CREATE INDEX IX_projetos_status ON dbo.projetos(status);
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_projetos_ultima_verificacao'
      AND object_id = OBJECT_ID('dbo.projetos')
)
BEGIN
    CREATE INDEX IX_projetos_ultima_verificacao
        ON dbo.projetos(ultima_verificacao);
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_analises_ia_score'
      AND object_id = OBJECT_ID('dbo.analises_ia')
)
BEGIN
    CREATE INDEX IX_analises_ia_score ON dbo.analises_ia(score DESC);
END
GO
