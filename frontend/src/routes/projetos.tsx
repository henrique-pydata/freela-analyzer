import { createFileRoute } from "@tanstack/react-router";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { z } from "zod";
import { useFreelaData } from "@/components/freela/app-context";
import { AnalysisDialog, ProjectRow } from "@/components/freela/project-ui";
import { FiltersBar, FilterSelect } from "@/components/freela/filters";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { Projeto } from "@/lib/freela-data";
import { cn } from "@/lib/utils";

const searchSchema = z.object({ status: z.enum(["todos", "analisados", "pendentes"]).catch("todos"), categoria: z.string().catch("todos"), experiencia: z.string().catch("todos"), exclusivo: z.enum(["todos", "sim", "nao"]).catch("todos"), propostas: z.string().catch("todas"), ordem: z.enum(["recente", "mais-propostas", "menos-propostas"]).catch("recente"), busca: z.string().catch("") });

export const Route = createFileRoute("/projetos")({
  validateSearch: (search) => searchSchema.parse(search),
  head: () => ({ meta: [
    { title: "Projetos — Freela Analyzer" }, { name: "description", content: "Explore e filtre projetos coletados do 99Freelas." },
    { property: "og:title", content: "Projetos — Freela Analyzer" }, { property: "og:description", content: "Explore e filtre projetos coletados do 99Freelas." },
    { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" },
  ] }), component: ProjectsPage,
});

function ProjectsPage() {
  const { projects } = useFreelaData(); const search = Route.useSearch(); const navigate = Route.useNavigate(); const [selected, setSelected] = useState<Projeto | null>(null);
  const update = (next: Partial<typeof search>) => navigate({ search: (previous) => ({ ...previous, ...next }) });
  const categories = [...new Set(projects.map((project) => project.categoria).filter(Boolean))] as string[];
  const filtered = useMemo(() => projects.filter((project) => {
    if (search.status === "analisados" && !project.analise) return false; if (search.status === "pendentes" && project.analise) return false;
    if (search.categoria !== "todos" && project.categoria !== search.categoria) return false; if (search.experiencia !== "todos" && project.nivel_experiencia !== search.experiencia) return false;
    if (search.exclusivo === "sim" && !project.projeto_exclusivo) return false; if (search.exclusivo === "nao" && project.projeto_exclusivo) return false;
    const proposalCount = Number.parseInt(project.propostas ?? "0"); if (search.propostas === "ate-10" && proposalCount > 10) return false; if (search.propostas === "10-plus" && proposalCount < 10) return false;
    return project.titulo.toLowerCase().includes(search.busca.toLowerCase());
  }).sort((a, b) => search.ordem === "mais-propostas" ? Number.parseInt(b.propostas ?? "0") - Number.parseInt(a.propostas ?? "0") : search.ordem === "menos-propostas" ? Number.parseInt(a.propostas ?? "0") - Number.parseInt(b.propostas ?? "0") : new Date(b.data_coleta).getTime() - new Date(a.data_coleta).getTime()), [projects, search]);
  const tabs = [["todos", "Todos"], ["analisados", "Analisados"], ["pendentes", "Não analisados"]] as const;
  return <><header className="mb-7"><h1 className="font-display text-2xl font-bold sm:text-3xl">Projetos</h1><p className="mt-2 text-muted-foreground">Projetos originais coletados do 99Freelas.</p></header>
    <div className="mb-4 flex gap-1 border-b">{tabs.map(([value, label]) => <Button key={value} variant="ghost" onClick={() => update({ status: value })} className={cn("rounded-none border-b-2 border-transparent px-4", search.status === value && "border-primary text-primary")}>{label}</Button>)}</div>
    <div className="mb-4 relative"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><Input className="bg-card pl-9" placeholder="Buscar projeto por título..." value={search.busca} onChange={(event) => update({ busca: event.target.value })} /></div>
    <FiltersBar onClear={() => navigate({ search: { status: "todos", categoria: "todos", experiencia: "todos", exclusivo: "todos", propostas: "todas", ordem: "recente", busca: "" } })}><FilterSelect value={search.categoria} onChange={(categoria) => update({ categoria })} placeholder="Categoria" options={[{ label: "Todas as categorias", value: "todos" }, ...categories.map((value) => ({ label: value, value }))]} /><FilterSelect value={search.experiencia} onChange={(experiencia) => update({ experiencia })} placeholder="Experiência" options={[{label:"Todos os níveis",value:"todos"},{label:"Iniciante",value:"Iniciante"},{label:"Intermediário",value:"Intermediário"},{label:"Especialista",value:"Especialista"}]} /><FilterSelect value={search.exclusivo} onChange={(exclusivo) => update({ exclusivo: exclusivo as typeof search.exclusivo })} placeholder="Exclusivo" options={[{label:"Todos",value:"todos"},{label:"Somente exclusivos",value:"sim"},{label:"Não exclusivos",value:"nao"}]} /><FilterSelect value={search.propostas} onChange={(propostas) => update({ propostas })} placeholder="Propostas" options={[{label:"Qualquer quantidade",value:"todas"},{label:"Até 10 propostas",value:"ate-10"},{label:"10 ou mais",value:"10-plus"}]} /><FilterSelect value={search.ordem} onChange={(ordem) => update({ ordem: ordem as typeof search.ordem })} placeholder="Ordenar" options={[{label:"Mais recentes",value:"recente"},{label:"Mais propostas",value:"mais-propostas"},{label:"Menos propostas",value:"menos-propostas"}]} /></FiltersBar>
    <div className="mt-5 overflow-hidden rounded-lg border bg-card shadow-card"><div className="hidden grid-cols-[minmax(0,2fr)_1fr_1fr_110px_110px] gap-4 border-b bg-surface-subtle px-5 py-3 text-xs font-semibold uppercase text-muted-foreground lg:grid"><span>Projeto</span><span>Categoria</span><span>Orçamento</span><span>Score</span><span>Ação</span></div>{filtered.length ? filtered.map((project) => <ProjectRow key={project.id} project={project} onOpen={() => setSelected(project)} />) : <div className="p-12 text-center text-sm text-muted-foreground">Nenhum projeto corresponde aos filtros.</div>}</div>
    <p className="mt-3 text-xs text-muted-foreground">Exibindo {filtered.length} de {projects.length} projetos</p><AnalysisDialog project={selected} open={Boolean(selected)} onOpenChange={(open) => !open && setSelected(null)} /></>;
}