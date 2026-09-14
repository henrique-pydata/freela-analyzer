import { Link } from "@tanstack/react-router";
import {
  BarChart3,
  CircleAlert,
  BriefcaseBusiness,
  Gauge,
  Menu,
  RefreshCw,
  Settings2,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

import { FreelaDataProvider, useFreelaData } from "./app-context";
import { cn } from "@/lib/utils";

const links = [
  { to: "/" as const, label: "Visão geral", icon: Gauge },
  { to: "/projetos" as const, label: "Projetos", icon: BriefcaseBusiness },
  { to: "/analises" as const, label: "Análises", icon: BarChart3 },
];

function formatarAtualizacao(
  valor: string | null,
  agora = Date.now(),
): string {
  if (!valor) {
    return "Sem sincronização";
  }

  const valorNormalizado = /(?:Z|[+-]\d{2}:?\d{2})$/.test(valor)
    ? valor
    : `${valor}Z`;
  const data = new Date(valorNormalizado);
  const diferencaMs = agora - data.getTime();

  if (Number.isNaN(diferencaMs) || diferencaMs < 0) {
    return "Atualizado agora";
  }

  const minutos = Math.floor(diferencaMs / 60000);

  if (minutos < 1) {
    return "Atualizado agora";
  }

  if (minutos < 60) {
    return `Atualizado há ${minutos} min`;
  }

  const horas = Math.floor(minutos / 60);

  if (horas < 24) {
    return `Atualizado há ${horas} h`;
  }

  const dias = Math.floor(horas / 24);

  return `Atualizado há ${dias} ${dias === 1 ? "dia" : "dias"}`;
}

function ApiStatus() {
  const {
    apiUrl,
    setApiUrl,
    apiOnline,
    refresh,
    loading,
  } = useFreelaData();

  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(apiUrl);

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => {
          setDraft(apiUrl);
          setOpen(true);
        }}
        className="gap-2"
      >
        <span
          className={cn(
            "size-2 rounded-full",
            apiOnline ? "bg-success" : "bg-danger",
          )}
        />

        <span className="hidden sm:inline">
          API {apiOnline ? "conectada" : "indisponível"}
        </span>

        <Settings2 className="size-4" />
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Conexão com a API</DialogTitle>

            <DialogDescription>
              Informe a URL base do backend FastAPI. Quando a API estiver
              indisponível, o dashboard não exibirá dados fictícios.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2">
            <label
              htmlFor="api-url"
              className="text-sm font-medium"
            >
              URL base
            </label>

            <Input
              id="api-url"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="http://127.0.0.1:8000"
            />
          </div>

          <div className="flex items-center gap-2 rounded-md bg-muted p-3 text-sm text-muted-foreground">
            {apiOnline ? (
              <Wifi className="text-success" />
            ) : (
              <WifiOff className="text-danger" />
            )}

            {apiOnline
              ? "Backend online e dados reais sincronizados."
              : "Backend indisponível."}
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={refresh}
              disabled={loading}
            >
              <RefreshCw
                className={cn(
                  "size-4",
                  loading && "animate-spin",
                )}
              />
              Testar
            </Button>

            <Button
              onClick={() => {
                setApiUrl(draft);
                setOpen(false);
              }}
            >
              Salvar URL
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function SincronizarButton() {
  const { apiOnline, syncStatus, iniciarSincronizacao } = useFreelaData();
  const jobAtivo =
    syncStatus.status === "PENDENTE" || syncStatus.status === "EXECUTANDO";

  async function handleClick() {
    if (!apiOnline || jobAtivo) return;
    try {
      await iniciarSincronizacao();
    } catch (erro) {
      console.error("Erro ao iniciar sincronização:", erro);
    }
  }

  const label = jobAtivo
    ? syncStatus.status === "PENDENTE"
      ? "Na fila..."
      : "Sincronizando..."
    : syncStatus.status === "FALHOU"
      ? "Tentar sincronizar"
      : "Sincronizar";

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleClick}
      disabled={!apiOnline || jobAtivo}
      className="gap-2"
      title={syncStatus.mensagem ?? undefined}
    >
      <RefreshCw className={cn("size-4", jobAtivo && "animate-spin")} />
      <span className="hidden sm:inline">{label}</span>
    </Button>
  );
}

function SyncProgress() {
  const { syncStatus } = useFreelaData();
  const jobAtivo =
    syncStatus.status === "PENDENTE" || syncStatus.status === "EXECUTANDO";

  if (!jobAtivo && syncStatus.status !== "FALHOU") return null;

  const faseLabel: Record<typeof syncStatus.fase, string> = {
    AGUARDANDO: "Aguardando worker",
    INICIALIZANDO: "Inicializando",
    VERIFICANDO: "Verificando projetos existentes",
    COLETANDO: "Coletando projetos",
    ANALISANDO: "Analisando projetos com IA",
    CONCLUIDA: "Concluída",
  };

  const percentual = Math.max(0, Math.min(100, syncStatus.percentual));
  const progressoDeterminado = syncStatus.progresso_total > 0;

  return (
    <section
      aria-live="polite"
      className={cn(
        "mb-6 rounded-lg border bg-card p-4 shadow-card",
        syncStatus.status === "FALHOU" && "border-danger/30",
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            {syncStatus.status === "FALHOU" ? (
              <CircleAlert className="size-4 text-danger" />
            ) : (
              <RefreshCw className="size-4 animate-spin text-primary" />
            )}
            <p className="text-sm font-semibold">{faseLabel[syncStatus.fase]}</p>
          </div>
          <p className="mt-1 truncate text-xs text-muted-foreground">
            {syncStatus.mensagem ?? "Processamento em segundo plano."}
          </p>
        </div>
        {progressoDeterminado && (
          <span className="shrink-0 text-sm font-semibold tabular-nums">
            {Math.round(percentual)}%
          </span>
        )}
      </div>

      {progressoDeterminado && (
        <div className="mt-3">
          <div className="h-2 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-[width] duration-500"
              style={{ width: `${percentual}%` }}
            />
          </div>
          <div className="mt-2 flex flex-wrap justify-between gap-2 text-xs text-muted-foreground">
            <span>
              {syncStatus.progresso_atual} de {syncStatus.progresso_total}
            </span>
            <span>
              {syncStatus.sucessos} sucesso(s) · {syncStatus.falhas} falha(s)
            </span>
          </div>
        </div>
      )}

      {syncStatus.status === "FALHOU" && syncStatus.erro && (
        <p className="mt-3 rounded-md bg-danger/5 p-2 text-xs text-danger">
          {syncStatus.erro}
        </p>
      )}
    </section>
  );
}

function Nav({ mobile = false }: { mobile?: boolean }) {
  return (
    <nav
      aria-label="Navegação principal"
      className={cn(
        "flex",
        mobile ? "flex-col gap-1 pt-6" : "items-center gap-1",
      )}
    >
      {links.map(({ to, label, icon: Icon }) => (
        <Link
          key={to}
          to={to}
          activeOptions={{ exact: to === "/" }}
          className={cn(
            "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground",
            mobile && "text-base",
          )}
          activeProps={{
            className: "bg-primary-soft text-primary",
          }}
        >
          <Icon className="size-4" />
          {label}
        </Link>
      ))}
    </nav>
  );
}

function ShellContent({
  children,
}: {
  children: ReactNode;
}) {
  const { stats } = useFreelaData();

  const [agora, setAgora] = useState(() =>
    Date.now(),
  );

  useEffect(() => {
    const interval = window.setInterval(() => {
      setAgora(Date.now());
    }, 60000);

    return () => window.clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 border-b bg-card/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1440px] items-center gap-3 px-4 sm:gap-6 sm:px-6 lg:px-8">
          <Link
            to="/"
            className="flex min-w-0 items-center gap-3"
          >
            <span className="grid size-9 shrink-0 place-items-center rounded-md bg-primary text-primary-foreground">
              <BarChart3 className="size-5" />
            </span>

            <span className="font-display text-base font-bold text-foreground sm:text-lg">
              FREELA ANALYZER
            </span>
          </Link>

          <span className="hidden rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground xl:inline">
            {formatarAtualizacao(
              stats.ultima_atualizacao,
              agora,
            )}
          </span>

          <div className="hidden flex-1 md:block">
            <Nav />
          </div>

          <div className="ml-auto flex items-center gap-2">
            <SincronizarButton />
            <ApiStatus />
          </div>

          <Sheet>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden"
                aria-label="Abrir menu"
              >
                <Menu />
              </Button>
            </SheetTrigger>

            <SheetContent side="right" className="w-72">
              <SheetTitle className="font-display">
                FREELA ANALYZER
              </SheetTitle>

              <Nav mobile />
            </SheetContent>
          </Sheet>
        </div>
      </header>

      <main className="mx-auto w-full max-w-[1440px] px-4 py-7 sm:px-6 lg:px-8 lg:py-9">
        <SyncProgress />
        {children}
      </main>
    </div>
  );
}

export function AppShell({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <FreelaDataProvider>
      <ShellContent>{children}</ShellContent>
    </FreelaDataProvider>
  );
}