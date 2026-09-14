export type Verdict = "SIM" | "NÃO" | "TALVEZ";
export type Difficulty = "BAIXA" | "MÉDIA" | "ALTA";
export type ProjectStatus = "ATIVO" | "CANCELADO" | "ENCERRADO" | "REPROVADO";
export type ApiOrder = "score" | "recente" | "orcamento";
export type SyncStatus =
  | "NUNCA_EXECUTADA"
  | "PENDENTE"
  | "EXECUTANDO"
  | "CONCLUIDA"
  | "FALHOU";

export interface SincronizacaoStatus {
  status: SyncStatus;
  inicio: string | null;
  fim: string | null;
  erro: string | null;
  fase: "AGUARDANDO" | "INICIALIZANDO" | "VERIFICANDO" | "COLETANDO" | "ANALISANDO" | "CONCLUIDA";
  progresso_atual: number;
  progresso_total: number;
  percentual: number;
  sucessos: number;
  falhas: number;
  projeto_atual: string | null;
  mensagem: string | null;
  ultima_atualizacao: string | null;
}

export interface AnaliseProjeto {
  vale_a_pena: Verdict;
  score: number;
  dificuldade: Difficulty;
  tecnologias: string[];
  riscos: string[];
  prazo_estimado: string;
  orcamento_informado: string;
  orcamento_justo: string;
  faixa_preco: string;
  justificativa: string;
  pontos_esclarecer: string[];
  veredito: string;
  data_analise?: string;
}

export interface Projeto {
  id: string;
  titulo: string;
  url: string;
  projeto_exclusivo: boolean;
  descricao: string | null;
  data_publicacao?: string | null;
  data_coleta: string;
  ultima_verificacao?: string | null;
  status: ProjectStatus;
  categoria: string | null;
  subcategoria: string | null;
  orcamento: string | null;
  nivel_experiencia: string | null;
  visibilidade: string | null;
  propostas: string | null;
  interessados: string | null;
  analise?: AnaliseProjeto | null;
}

export interface Estatisticas {
  total_projetos: number;
  projetos_analisados: number;
  projetos_pendentes: number;
  score_medio: number;
  vale_a_pena: Record<Verdict, number>;
  dificuldade: Record<Difficulty, number>;
  ultima_atualizacao: string | null;
}

export interface ProjetosResponse {
  projetos: Projeto[];
  pagina: number;
  por_pagina: number;
  total: number;
}

export interface ProjectFilters {
  pagina?: number;
  por_pagina?: number;
  score_minimo?: number;
  vale_a_pena?: Verdict;
  dificuldade?: Difficulty;
  projeto_exclusivo?: boolean;
  categoria?: string;
  ordem?: ApiOrder;
}

export const DEFAULT_API_URL = import.meta.env.VITE_API_URL?.trim() || "http://127.0.0.1:8000";
export const API_URL_KEY = "freela-analyzer-api-url";

function queryString(filters: ProjectFilters) {
  const params = new URLSearchParams();

  Object.entries({ pagina: 1, por_pagina: 20, ...filters }).forEach(
    ([key, value]) => {
      if (value !== undefined && value !== "") {
        params.set(key, String(value));
      }
    },
  );

  return params.toString();
}

async function request<T>(
  baseUrl: string,
  path: string,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(
    `${baseUrl.replace(/\/$/, "")}${path}`,
    signal ? { signal } : {},
  );

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body?.detail;
    const message = typeof detail === "string" ? detail : "A API retornou um erro.";
    throw new Error(message);
  }

  return (await response.json()) as T;
}

export const freelaApi = {
  health: (
    baseUrl: string,
    signal?: AbortSignal,
  ) => request<{ status: "online" }>(baseUrl, "/health", signal),

  statistics: (
    baseUrl: string,
    signal?: AbortSignal,
  ) => request<Estatisticas>(baseUrl, "/estatisticas", signal),

  projects: (
    baseUrl: string,
    filters: ProjectFilters = {},
    signal?: AbortSignal,
  ) =>
    request<ProjetosResponse>(
      baseUrl,
      `/projetos?${queryString(filters)}`,
      signal,
    ),

  best: (
    baseUrl: string,
    scoreMinimo = 70,
    signal?: AbortSignal,
  ) =>
    request<ProjetosResponse>(
      baseUrl,
      `/projetos/melhores?pagina=1&por_pagina=20&score_minimo=${scoreMinimo}`,
      signal,
    ),

  project: (
    baseUrl: string,
    id: string,
    signal?: AbortSignal,
  ) => request<Projeto>(baseUrl, `/projetos/${id}`, signal),

  synchronization: (
    baseUrl: string,
    signal?: AbortSignal,
  ) => request<SincronizacaoStatus>(baseUrl, "/sincronizacao", signal),

  startSynchronization: async (baseUrl: string) => {
    const response = await fetch(`${baseUrl.replace(/\/$/, "")}/sincronizar`, {
      method: "POST",
      headers: { Accept: "application/json" },
    });

    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = body?.detail;
      if (detail && typeof detail === "object" && detail.status) {
        throw new Error(detail.mensagem || "Uma sincronização já está em andamento.");
      }
      throw new Error(
        typeof detail === "string"
          ? detail
          : `API respondeu com status ${response.status}`,
      );
    }

    return body as {
      status: "enfileirada";
      mensagem: string;
      sincronizacao: SincronizacaoStatus;
    };
  },

  analysis: (
    baseUrl: string,
    id: string,
    signal?: AbortSignal,
  ) => request<AnaliseProjeto>(baseUrl, `/projetos/${id}/analise`, signal),
};
