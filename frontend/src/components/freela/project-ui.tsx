import { useState } from "react";
import {
  ArrowUpRight,
  ChevronDown,
  CircleAlert,
  Clock3,
  Code2,
  Crown,
  DollarSign,
  ExternalLink,
  FileText,
  Lightbulb,
  MessageSquareText,
  ShieldAlert,
  Sparkles,
  Target,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import type { AnaliseProjeto, Projeto } from "@/lib/freela-data";

export function Score({
  score,
  compact = false,
}: {
  score: number;
  compact?: boolean;
}) {
  const tone =
    score >= 80
      ? "text-success"
      : score >= 60
        ? "text-warning-foreground"
        : "text-danger";

  return (
    <div className={cn("shrink-0 text-center", tone)}>
      <span
        className={cn(
          "font-display font-bold",
          compact ? "text-2xl" : "text-4xl",
        )}
      >
        {score}
      </span>
      <span className="text-xs font-semibold">/100</span>
    </div>
  );
}

export function VerdictBadge({ analysis }: { analysis: AnaliseProjeto }) {
  const style =
    analysis.vale_a_pena === "SIM"
      ? "bg-success-soft text-success"
      : analysis.vale_a_pena === "TALVEZ"
        ? "bg-warning-soft text-warning-foreground"
        : "bg-danger-soft text-danger";

  return (
    <Badge className={cn("border-0 shadow-none", style)}>
      {analysis.vale_a_pena === "SIM" ? "VALE A PENA" : analysis.vale_a_pena}
    </Badge>
  );
}

export function OpportunityCard({
  project,
  onOpen,
}: {
  project: Projeto;
  onOpen: () => void;
}) {
  const analysis = project.analise;
  if (!analysis) return null;

  return (
    <article className="group flex h-full flex-col rounded-lg border bg-card p-5 shadow-card transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-card-hover">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="mb-2 flex flex-wrap gap-2">
            <VerdictBadge analysis={analysis} />
            {project.projeto_exclusivo && (
              <Badge variant="outline" className="gap-1 text-primary">
                <Crown className="size-3" />
                Exclusivo
              </Badge>
            )}
          </div>
          <h3 className="line-clamp-2 font-display text-base font-semibold leading-snug">
            {project.titulo}
          </h3>
        </div>
        <Score score={analysis.score} compact />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Badge variant="secondary">{analysis.dificuldade}</Badge>
        <Badge variant="outline">{analysis.faixa_preco}</Badge>
      </div>

      <div className="mt-4 flex flex-wrap gap-1.5">
        {analysis.tecnologias.map((technology) => (
          <span
            key={technology}
            className="rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground"
          >
            {technology}
          </span>
        ))}
      </div>

      <div className="mt-auto flex items-center justify-between gap-3 border-t pt-4">
        <span className="text-xs text-muted-foreground">
          {project.propostas ?? "Sem propostas"}
        </span>
        <Button size="sm" variant="outline" onClick={onOpen}>
          Ver análise
          <ArrowUpRight />
        </Button>
      </div>
    </article>
  );
}

export function AnalysisDialog({
  project,
  open,
  onOpenChange,
}: {
  project: Projeto | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const analysis = project?.analise;

  if (!project || !analysis) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] max-w-5xl overflow-y-auto p-0">
        <div className="border-b bg-surface-subtle p-5 sm:p-7">
          <DialogHeader>
            <div className="flex flex-col gap-5 pr-8 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <div className="mb-3 flex flex-wrap gap-2">
                  <VerdictBadge analysis={analysis} />
                  <Badge variant="outline">
                    {analysis.dificuldade} DIFICULDADE
                  </Badge>
                  {project.projeto_exclusivo && (
                    <Badge className="gap-1">
                      <Crown />
                      EXCLUSIVO
                    </Badge>
                  )}
                </div>
                <DialogTitle className="font-display text-xl leading-tight sm:text-2xl">
                  {project.titulo}
                </DialogTitle>
                <DialogDescription className="mt-2">
                  {project.categoria} · {project.subcategoria}
                </DialogDescription>
              </div>
              <Score score={analysis.score} />
            </div>
          </DialogHeader>
        </div>

        <div className="space-y-7 p-5 sm:p-7">
          <section className="rounded-lg border-l-4 border-l-primary bg-primary-soft p-5">
            <div className="mb-2 flex items-center gap-2 font-semibold text-primary">
              <Sparkles className="size-4" />
              Resumo da oportunidade
            </div>
            <p className="leading-relaxed text-foreground">
              {analysis.veredito}
            </p>
          </section>

          <div className="grid gap-7 lg:grid-cols-[1.2fr_.8fr]">
            <section>
              <h3 className="section-title">
                <Target />
                Raio-X da oportunidade
              </h3>
              <div className="grid gap-4 rounded-lg border p-5 sm:grid-cols-3">
                <div>
                  <p className="text-xs text-muted-foreground">Score da IA</p>
                  <p className="mt-1 font-display text-2xl font-bold">
                    {analysis.score}/100
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Dificuldade</p>
                  <p className="mt-1 font-display text-lg font-bold">
                    {analysis.dificuldade}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Prazo estimado</p>
                  <p className="mt-1 font-semibold">
                    {analysis.prazo_estimado}
                  </p>
                </div>
              </div>
            </section>

            <section>
              <h3 className="section-title">
                <DollarSign />
                Análise de orçamento
              </h3>
              <div className="divide-y rounded-lg border bg-card">
                <Budget
                  label="Informado pelo cliente"
                  value={analysis.orcamento_informado}
                />
                <Budget
                  label="Estimativa da IA"
                  value={analysis.faixa_preco}
                />
                <Budget
                  label="Orçamento justo"
                  value={analysis.orcamento_justo}
                  highlight
                />
              </div>
            </section>
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <section className="rounded-lg border p-5">
              <h3 className="section-title">
                <Clock3 />
                Prazo estimado
              </h3>
              <p className="font-semibold">{analysis.prazo_estimado}</p>
            </section>

            <section className="rounded-lg border p-5">
              <h3 className="section-title">
                <Code2 />
                Tecnologias
              </h3>
              <div className="flex flex-wrap gap-2">
                {analysis.tecnologias.map((item) => (
                  <Badge key={item} variant="secondary">
                    {item}
                  </Badge>
                ))}
              </div>
            </section>
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <InfoList
              title="Riscos"
              icon={<ShieldAlert />}
              items={analysis.riscos}
              danger
            />
            <InfoList
              title="Pontos a esclarecer"
              icon={<MessageSquareText />}
              items={analysis.pontos_esclarecer}
            />
          </div>

          <section>
            <h3 className="section-title">
              <Lightbulb />
              Por que a IA classificou assim?
            </h3>
            <p className="rounded-lg bg-muted p-5 text-sm leading-7 text-muted-foreground">
              {analysis.justificativa}
            </p>
          </section>

          <section
            className={cn(
              "rounded-lg border-2 p-5",
              analysis.vale_a_pena === "SIM"
                ? "border-success bg-success-soft"
                : analysis.vale_a_pena === "TALVEZ"
                  ? "border-warning bg-warning-soft"
                  : "border-danger bg-danger-soft",
            )}
          >
            <div className="flex gap-3">
              <CircleAlert className="mt-0.5 size-5 shrink-0" />
              <div>
                <p className="text-xs font-bold uppercase text-muted-foreground">
                  Veredito final
                </p>
                <p className="mt-1 font-display text-xl font-bold">
                  {analysis.vale_a_pena}
                </p>
                <p className="mt-1 text-sm">{analysis.veredito}</p>
              </div>
            </div>
          </section>

          <Button
            size="lg"
            className="h-12 w-full text-sm font-bold"
            asChild
          >
            <a
              href={project.url}
              target="_blank"
              rel="noreferrer"
            >
              ABRIR NO 99FREELAS
              <ExternalLink />
            </a>
          </Button>

          <section className="rounded-lg border">
            <Button
              variant="ghost"
              className="h-auto w-full justify-between rounded-lg p-4"
              onClick={() => setExpanded((value) => !value)}
            >
              <span className="flex items-center gap-2">
                <FileText />
                Detalhes originais do 99Freelas
              </span>
              <ChevronDown
                className={cn("transition-transform", expanded && "rotate-180")}
              />
            </Button>

            {expanded && (
              <div className="border-t p-5 text-sm leading-7 text-muted-foreground">
                <p>{project.descricao}</p>
                <dl className="mt-4 grid gap-2 sm:grid-cols-2">
                  <div>
                    <dt className="font-medium text-foreground">Experiência</dt>
                    <dd>{project.nivel_experiencia}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-foreground">Propostas</dt>
                    <dd>{project.propostas}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-foreground">Interessados</dt>
                    <dd>{project.interessados}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-foreground">
                      Última verificação
                    </dt>
                    <dd>
                      {project.ultima_verificacao
                        ? new Date(
                            project.ultima_verificacao,
                          ).toLocaleString("pt-BR")
                        : "Não disponível"}
                    </dd>
                  </div>
                </dl>
              </div>
            )}
          </section>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function Budget({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className={cn("p-4", highlight && "bg-success-soft")}>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p
        className={cn(
          "mt-1 font-display text-lg font-bold",
          highlight && "text-success",
        )}
      >
        {value}
      </p>
    </div>
  );
}

function InfoList({
  title,
  icon,
  items,
  danger = false,
}: {
  title: string;
  icon: React.ReactNode;
  items: string[];
  danger?: boolean;
}) {
  return (
    <section className="rounded-lg border p-5">
      <h3 className={cn("section-title", danger && "text-danger")}>
        {icon}
        {title}
      </h3>
      {items.length ? (
        <ul className="space-y-3">
          {items.map((item) => (
            <li
              key={item}
              className="flex gap-2 text-sm text-muted-foreground"
            >
              <CircleAlert className="mt-0.5 size-4 shrink-0" />
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">
          Nenhum item informado.
        </p>
      )}
    </section>
  );
}

export function ProjectRow({
  project,
  onOpen,
}: {
  project: Projeto;
  onOpen: () => void;
}) {
  return (
    <article className="grid gap-4 border-b p-5 transition-colors last:border-b-0 hover:bg-surface-subtle lg:grid-cols-[minmax(0,2fr)_1fr_1fr_110px_110px] lg:items-center">
      <div className="min-w-0">
        <div className="mb-1 flex items-center gap-2">
          {project.projeto_exclusivo && (
            <Crown className="size-4 text-primary" />
          )}
          <h3 className="truncate font-semibold">{project.titulo}</h3>
        </div>
        <p className="line-clamp-1 text-sm text-muted-foreground">
          {project.descricao}
        </p>
      </div>

      <div>
        <p className="text-sm font-medium">{project.categoria}</p>
        <p className="text-xs text-muted-foreground">
          {project.subcategoria}
        </p>
      </div>

      <div>
        <p className="text-sm font-semibold">{project.orcamento}</p>
        <p className="text-xs text-muted-foreground">
          {project.propostas}
        </p>
      </div>

      <div>
        {project.analise ? (
          <Score score={project.analise.score} compact />
        ) : (
          <Badge variant="secondary">Pendente</Badge>
        )}
      </div>

      <Button
        variant="outline"
        size="sm"
        disabled={!project.analise}
        onClick={onOpen}
      >
        {project.analise ? "Ver análise" : "Sem análise"}
      </Button>
    </article>
  );
}
