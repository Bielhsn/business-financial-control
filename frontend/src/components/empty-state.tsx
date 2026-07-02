import type { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  children?: React.ReactNode;
}

export function EmptyState({ icon: Icon, title, description, children }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed py-14 text-center">
      <div className="flex size-11 items-center justify-center rounded-full bg-accent text-accent-foreground">
        <Icon className="size-5" />
      </div>
      <div className="space-y-1">
        <p className="font-medium">{title}</p>
        <p className="mx-auto max-w-sm text-sm text-muted-foreground">{description}</p>
      </div>
      {children}
    </div>
  );
}
