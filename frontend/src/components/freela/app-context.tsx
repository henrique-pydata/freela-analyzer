import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  API_URL_KEY,
  DEFAULT_API_URL,
  freelaApi,
  type Estatisticas,
  type Projeto,
  type SincronizacaoStatus,
} from "@/lib/freela-data";

const EMPTY_STATS: Estatisticas = {
  total_projetos: 0,
  projetos_analisados: 0,
  projetos_pendentes: 0,
  score_medio: 0,
  vale_a_pena: { SIM: 0, "NÃO": 0, TALVEZ: 0 },
  dificuldade: { BAIXA: 0, "MÉDIA": 0, ALTA: 0 },
  ultima_atualizacao: null,
};

const EMPTY_SYNC: SincronizacaoStatus = {
  status: "NUNCA_EXECUTADA",
  inicio: null,
  fim: null,
  erro: null,
  fase: "AGUARDANDO",
  progresso_atual: 0,
  progresso_total: 0,
  percentual: 0,
  sucessos: 0,
  falhas: 0,
  projeto_atual: null,
  mensagem: null,
  ultima_atualizacao: null,
};

type AppData = {
  apiUrl: string;
  setApiUrl: (url: string) => void;
  apiOnline: boolean;
  loading: boolean;
  projects: Projeto[];
  stats: Estatisticas;
  syncStatus: SincronizacaoStatus;
  refresh: () => void;
  iniciarSincronizacao: () => Promise<void>;
};

const DataContext = createContext<AppData | null>(null);

async function carregarTodosOsProjetos(
  apiUrl: string,
  signal: AbortSignal,
): Promise<Projeto[]> {
  const porPagina = 100;
  const primeiraPagina = await freelaApi.projects(
    apiUrl,
    { pagina: 1, por_pagina: porPagina, ordem: "score" },
    signal,
  );

  const totalPaginas = Math.ceil(primeiraPagina.total / porPagina);

  if (totalPaginas <= 1) return primeiraPagina.projetos;

  const paginasRestantes = await Promise.all(
    Array.from({ length: totalPaginas - 1 }, (_, index) =>
      freelaApi.projects(
        apiUrl,
        { pagina: index + 2, por_pagina: porPagina, ordem: "score" },
        signal,
      ),
    ),
  );

  const projetos = [
    primeiraPagina.projetos,
    ...paginasRestantes.map((resposta) => resposta.projetos),
  ].flat();

  return Array.from(
    new Map(projetos.map((projeto) => [projeto.id, projeto])).values(),
  );
}

export function FreelaDataProvider({ children }: { children: ReactNode }) {
  const [apiUrl, setApiUrlState] = useState(DEFAULT_API_URL);
  const [apiOnline, setApiOnline] = useState(false);
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState<Projeto[]>([]);
  const [stats, setStats] = useState<Estatisticas>(EMPTY_STATS);
  const [syncStatus, setSyncStatus] = useState<SincronizacaoStatus>(EMPTY_SYNC);
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    const saved = window.localStorage.getItem(API_URL_KEY);
    if (saved) setApiUrlState(saved);
  }, []);

  useEffect(() => {
    let cancel = false;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 30000);

    async function carregar() {
      setLoading(true);
      try {
        const [health, apiStats, projetos, sync] = await Promise.all([
          freelaApi.health(apiUrl, controller.signal),
          freelaApi.statistics(apiUrl, controller.signal),
          carregarTodosOsProjetos(apiUrl, controller.signal),
          freelaApi.synchronization(apiUrl, controller.signal),
        ]);

        if (cancel) return;
        setApiOnline(health.status === "online");
        setStats(apiStats);
        setProjects(projetos);
        setSyncStatus(sync);
      } catch (erro) {
        if (!cancel && !controller.signal.aborted) {
          console.error("Falha ao carregar o Freela Analyzer:", erro);
          setApiOnline(false);
          setProjects([]);
          setStats(EMPTY_STATS);
        }
      } finally {
        if (!cancel) {
          window.clearTimeout(timeout);
          setLoading(false);
        }
      }
    }

    carregar();
    return () => {
      cancel = true;
      controller.abort();
      window.clearTimeout(timeout);
    };
  }, [apiUrl, revision]);

  useEffect(() => {
    const jobAtivo = syncStatus.status === "PENDENTE" || syncStatus.status === "EXECUTANDO";
    if (!jobAtivo) return;

    const interval = window.setInterval(async () => {
      try {
        const atual = await freelaApi.synchronization(apiUrl);
        setSyncStatus(atual);
        if (atual.status === "CONCLUIDA" || atual.status === "FALHOU") {
          setRevision((value) => value + 1);
        }
      } catch (erro) {
        console.error("Falha ao consultar status da sincronização:", erro);
      }
    }, 2000);

    return () => window.clearInterval(interval);
  }, [apiUrl, syncStatus.status]);

  const setApiUrl = (url: string) => {
    const normalized = url.trim().replace(/\/$/, "") || DEFAULT_API_URL;
    window.localStorage.setItem(API_URL_KEY, normalized);
    setApiUrlState(normalized);
  };

  const iniciarSincronizacao = async () => {
    const resposta = await freelaApi.startSynchronization(apiUrl);
    setSyncStatus(resposta.sincronizacao);
  };

  const value = useMemo(
    () => ({
      apiUrl,
      setApiUrl,
      apiOnline,
      loading,
      projects,
      stats,
      syncStatus,
      refresh: () => setRevision((value) => value + 1),
      iniciarSincronizacao,
    }),
    [apiUrl, apiOnline, loading, projects, stats, syncStatus],
  );

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
}

export function useFreelaData() {
  const value = useContext(DataContext);
  if (!value) {
    throw new Error("useFreelaData precisa estar dentro de FreelaDataProvider");
  }
  return value;
}
