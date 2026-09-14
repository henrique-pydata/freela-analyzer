import { SlidersHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export function FilterSelect({ value, onChange, placeholder, options }: { value: string; onChange: (value: string) => void; placeholder: string; options: { label: string; value: string }[] }) {
  return <Select value={value} onValueChange={onChange}><SelectTrigger className="min-w-40 bg-card"><SelectValue placeholder={placeholder} /></SelectTrigger><SelectContent>{options.map((option) => <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>)}</SelectContent></Select>;
}

export function FiltersBar({ children, onClear }: { children: React.ReactNode; onClear: () => void }) {
  return <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-card p-3 shadow-card"><span className="flex items-center gap-2 px-1 text-sm font-semibold"><SlidersHorizontal className="size-4" />Filtros</span>{children}<Button variant="ghost" size="sm" onClick={onClear} className="ml-auto">Limpar</Button></div>;
}