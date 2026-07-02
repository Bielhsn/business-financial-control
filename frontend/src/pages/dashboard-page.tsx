import { LayoutDashboard } from "lucide-react";

export function DashboardPage() {
  return (
    <div className="flex h-full min-h-[60vh] flex-col items-center justify-center gap-3 p-8 text-center">
      <div className="flex size-12 items-center justify-center rounded-full bg-accent text-accent-foreground">
        <LayoutDashboard className="size-6" />
      </div>
      <h1 className="text-xl font-semibold">Dashboard</h1>
      <p className="max-w-md text-sm text-muted-foreground">
        Os indicadores financeiros da sua empresa aparecerão aqui (próxima etapa do roadmap).
      </p>
    </div>
  );
}
