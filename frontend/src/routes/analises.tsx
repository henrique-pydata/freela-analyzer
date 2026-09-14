import { createFileRoute } from "@tanstack/react-router";
import { Flame, Sparkles, TrendingUp, Zap } from "lucide-react";
import { useMemo, useState } from "react";
import { z } from "zod";
import { useFreelaData } from "@/components/freela/app-context";
import { AnalysisDialog, OpportunityCard } from "@/components/freela/project-ui";
import { FiltersBar, FilterSelect } from "@/components/freela/filters";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import type { Difficulty, Projeto, Verdict } from "@/lib/freela-data";
import { cn } from "@/lib/utils";

const schema = z.object({ score: z.coerce.number().min(0).max(100).catch(0), vale: z.enum(["todos", "SIM", "NÃO", "TALVEZ"]).catch("todos"), dificuldade: z.enum(["todas", "BAIXA", "MÉDIA", "ALTA"]).catch("todas"), exclusivo: z.coerce.boolean().catch(false), melhores: z.coerce.boolean().catch(false), preco: z.enum(["todos", "ate-2000", "2000-5000", "5000-plus"]).catch("todos"), ordem: z.enum(["score", "dificuldade", "valor", "recente"]).catch("score") });
export const Route = createFileRoute("/analises")({ validateSearch: (search) => schema.parse(search), head: () => ({ meta: [
  { title: "Análises — Freela Analyzer" }, { name: "description", content: "Compare análises de IA e encontre as oportunidades mais promissoras." },
  { property: "og:title", content: "Análises — Freela Analyzer" }, { property: "og:description", content: "Compare análises de IA e encontre as oportunidades mais promissoras." },
  { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" },
] }), component: AnalysesPage });

function money(value: string) { const matches = value.match(/[\d.]+/g); return matches ? Number(matches.at(-1)?.replaceAll(".", "")) : 0; }
function AnalysesPage() {
  const { projects } = useFreelaData(); const search = Route.useSearch(); const navigate = Route.useNavigate(); const [selected, setSelected] = useState<Projeto | null>(null);
  const update = (next: Partial<typeof search>) => navigate({ search: (previous) => ({ ...previous, ...next }) });
  const shortcuts = [
    { label: "Score 70+", onClick: () => update({ score: 70 }), active: search.score === 70 },
    { label: "Vale a pena", onClick: () => update({ vale: "SIM" }), active: search.vale === "SIM" },
    { label: "Baixa", onClick: () => update({ dificuldade: "BAIXA" }), active: search.dificuldade === "BAIXA" },
    { label: "Exclusivos", onClick: () => update({ exclusivo: !search.exclusivo }), active: search.exclusivo },
    { label: "Melhores", icon: Flame, onClick: () => update({ melhores: true, score: 80 }), active: search.melhores },
    { label: "Fáceis", icon: Zap, onClick: () => update({ dificuldade: "BAIXA", ordem: "dificuldade" }), active: search.dificuldade === "BAIXA" },
    { label: "Maior potencial", icon: TrendingUp, onClick: () => update({ ordem: "valor" }), active: search.ordem === "valor" },
  ];
  const filtered = useMemo(() => projects.filter((project) => { const a = project.analise; if (!a || a.score < search.score) return false; if (search.vale !== "todos" && a.vale_a_pena !== search.vale) return false; if (search.dificuldade !== "todas" && a.dificuldade !== search.dificuldade) return false; if (search.exclusivo && !project.projeto_exclusivo) return false; const value = money(a.faixa_preco); if (search.preco === "ate-2000" && value > 2000) return false; if (search.preco === "2000-5000" && (value < 2000 || value > 5000)) return false; if (search.preco === "5000-plus" && value < 5000) return false; return true; }).sort((a,b) => search.ordem === "dificuldade" ? ({BAIXA:1,MÉDIA:2,ALTA:3}[a.analise?.dificuldade as Difficulty] - {BAIXA:1,MÉDIA:2,ALTA:3}[b.analise?.dificuldade as Difficulty]) : search.ordem === "valor" ? money(b.analise?.faixa_preco ?? "") - money(a.analise?.faixa_preco ?? "") : search.ordem === "recente" ? new Date(b.data_coleta).getTime()-new Date(a.data_coleta).getTime() : (b.analise?.score ?? 0)-(a.analise?.score ?? 0)), [projects, search]);
  return <><header className="mb-7"><p className="mb-2 flex items-center gap-2 text-sm font-semibold text-primary"><Sparkles className="size-4" />INTELIGÊNCIA DE OPORTUNIDADE</p><h1 className="font-display text-2xl font-bold sm:text-3xl">Análises</h1><p className="mt-2 text-muted-foreground">Somente projetos avaliados pela IA, prontos para comparar.</p></header>
    <div className="mb-4 flex gap-2 overflow-x-auto pb-2">{shortcuts.map(({ label, icon: Icon, onClick, active }) => <Button key={label} variant={active ? "default" : "outline"} size="sm" onClick={onClick} className="shrink-0">{Icon && <Icon />}{label}</Button>)}</div>
    <FiltersBar onClear={() => navigate({ search: { score: 0, vale: "todos", dificuldade: "todas", exclusivo: false, melhores: false, preco: "todos", ordem: "score" } })}><FilterSelect value={search.vale} onChange={(vale) => update({ vale: vale as Verdict | "todos" })} placeholder="Vale a pena" options={[{label:"Todos",value:"todos"},{label:"SIM",value:"SIM"},{label:"TALVEZ",value:"TALVEZ"},{label:"NÃO",value:"NÃO"}]} /><FilterSelect value={search.dificuldade} onChange={(dificuldade) => update({ dificuldade: dificuldade as Difficulty | "todas" })} placeholder="Dificuldade" options={[{label:"Todas",value:"todas"},{label:"BAIXA",value:"BAIXA"},{label:"MÉDIA",value:"MÉDIA"},{label:"ALTA",value:"ALTA"}]} /><FilterSelect value={search.preco} onChange={(preco) => update({ preco: preco as typeof search.preco })} placeholder="Faixa de preço" options={[{label:"Qualquer valor",value:"todos"},{label:"Até R$ 2 mil",value:"ate-2000"},{label:"R$ 2 mil a R$ 5 mil",value:"2000-5000"},{label:"Acima de R$ 5 mil",value:"5000-plus"}]} /><FilterSelect value={search.ordem} onChange={(ordem) => update({ ordem: ordem as typeof search.ordem })} placeholder="Ordenar" options={[{label:"Maior score",value:"score"},{label:"Menor dificuldade",value:"dificuldade"},{label:"Maior valor estimado",value:"valor"},{label:"Mais recentes",value:"recente"}]} /><div className="min-w-48 px-2"><div className="mb-2 flex justify-between text-xs"><span>Score mínimo</span><strong>{search.score}</strong></div><Slider value={[search.score]} max={100} step={5} onValueChange={([score]) => update({ score: score ?? 0 })} /></div></FiltersBar>
    <div className="mt-5 flex items-center justify-between"><p className="text-sm text-muted-foreground"><strong className="text-foreground">{filtered.length}</strong> análises encontradas</p><span className={cn("text-xs", filtered.length ? "text-muted-foreground" : "text-warning-foreground")}>{search.score > 0 && `Score mínimo: ${search.score}`}</span></div>
    <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{filtered.map((project) => <OpportunityCard key={project.id} project={project} onOpen={() => setSelected(project)} />)}</div>{!filtered.length && <div className="mt-4 rounded-lg border bg-card p-12 text-center text-sm text-muted-foreground">Nenhuma análise corresponde aos filtros escolhidos.</div>}
    <AnalysisDialog project={selected} open={Boolean(selected)} onOpenChange={(open) => !open && setSelected(null)} /></>;
}