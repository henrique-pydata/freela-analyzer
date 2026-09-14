import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, BarChart3, BriefcaseBusiness, CircleCheckBig, Gauge, Sparkles, Zap } from "lucide-react";
import { useState } from "react";
import { useFreelaData } from "@/components/freela/app-context";
import { AnalysisDialog, OpportunityCard } from "@/components/freela/project-ui";
import type { Projeto } from "@/lib/freela-data";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [
    { title: "Visão geral — Freela Analyzer" },
    { name: "description", content: "Veja os melhores projetos freelance por score, dificuldade e retorno." },
    { property: "og:title", content: "Visão geral — Freela Analyzer" },
    { property: "og:description", content: "Veja os melhores projetos freelance por score, dificuldade e retorno." },
    { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" },
  ] }),
  component: Dashboard,
});

function Dashboard() {
  const { stats, projects, apiOnline, loading } = useFreelaData();
  const [selected, setSelected] = useState<Projeto | null>(null);
  const opportunities = projects.filter((project) => project.analise && project.analise.score >= 70).sort((a, b) => (b.analise?.score ?? 0) - (a.analise?.score ?? 0)).slice(0, 4);
  const cards = [
    { label: "Total de projetos", value: stats.total_projetos, suffix: "projetos", icon: BriefcaseBusiness, destination: "projects" },
    { label: "Projetos analisados", value: stats.projetos_analisados, suffix: "analisados", icon: BarChart3, destination: "analyses" },
    { label: "Melhores oportunidades", value: stats.vale_a_pena.SIM, suffix: "bons", icon: CircleCheckBig, destination: "best" },
    { label: "Projetos fáceis", value: stats.dificuldade.BAIXA, suffix: "projetos", icon: Zap, destination: "easy" },
  ];
  return <>
    <section className="mb-8"><div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><div><p className="mb-2 flex items-center gap-2 text-sm font-semibold text-primary"><Gauge className="size-4" />PAINEL DE OPORTUNIDADES</p><h1 className="font-display text-2xl font-bold sm:text-3xl">Quais projetos valem seu tempo?</h1><p className="mt-2 text-muted-foreground">Compare oportunidades e priorize propostas com mais potencial.</p></div><p className="text-xs text-muted-foreground">{loading ? "Atualizando dados…" : apiOnline ? "Dados sincronizados com a API" : "API indisponível"}</p></div></section>
    <section aria-label="Resumo" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{cards.map(({ label, value, suffix, icon: Icon, destination }) => {
      const content = <><div className="mb-5 flex items-start justify-between"><span className="grid size-10 place-items-center rounded-md bg-primary-soft text-primary"><Icon className="size-5" /></span><ArrowRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-1 group-hover:text-primary" /></div><p className="text-sm text-muted-foreground">{label}</p><div className="mt-1 flex items-baseline gap-2"><strong className="font-display text-3xl">{value}</strong><span className="text-xs text-muted-foreground">{suffix}</span></div></>;
      const className = "group rounded-lg border bg-card p-5 shadow-card transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-card-hover";
      if (destination === "projects") return <Link key={label} to="/projetos" className={className}>{content}</Link>;
      const defaults = { score: 0, vale: "todos" as const, dificuldade: "todas" as const, exclusivo: false, melhores: false, preco: "todos" as const, ordem: "score" as const };
      const target = destination === "best" ? { ...defaults, score: 70, melhores: true } : destination === "easy" ? { ...defaults, dificuldade: "BAIXA" as const, ordem: "dificuldade" as const } : defaults;
      return <Link key={label} to="/analises" search={target} className={className}>{content}</Link>;
    })}</section>
    <section className="mt-10"><div className="mb-5 flex items-center justify-between"><div><h2 className="flex items-center gap-2 font-display text-xl font-bold"><Sparkles className="size-5 text-primary" />Melhores oportunidades</h2><p className="mt-1 text-sm text-muted-foreground">Projetos com maior score e melhor avaliação da IA.</p></div><Link to="/analises" search={{ score: 70, vale: "todos", dificuldade: "todas", exclusivo: false, melhores: true, preco: "todos", ordem: "score" }} className="hidden items-center gap-2 text-sm font-semibold text-primary hover:underline sm:flex">Ver todas<ArrowRight className="size-4" /></Link></div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{opportunities.map((project) => <OpportunityCard key={project.id} project={project} onOpen={() => setSelected(project)} />)}</div>
    </section>
    <AnalysisDialog project={selected} open={Boolean(selected)} onOpenChange={(open) => !open && setSelected(null)} />
  </>;
}