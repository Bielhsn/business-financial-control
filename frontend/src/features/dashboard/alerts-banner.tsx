import { AlertTriangle, ArrowRight, Bell, Info } from "lucide-react";
import { Link } from "react-router-dom";

import { useAlerts } from "@/features/dashboard/use-alerts";
import type { AlertResponse, AlertSeverity } from "@/lib/api-types";
import { cn } from "@/lib/utils";

const STYLES: Record<AlertSeverity, { box: string; icon: string }> = {
  critical: {
    box: "border-destructive/40 bg-destructive/5",
    icon: "text-destructive",
  },
  warning: {
    box: "border-warning/40 bg-warning/5",
    icon: "text-warning",
  },
  info: {
    box: "border-border bg-muted/40",
    icon: "text-muted-foreground",
  },
};

function AlertIcon({ severity }: { severity: AlertSeverity }) {
  const className = cn("mt-0.5 size-4 shrink-0", STYLES[severity].icon);
  if (severity === "info") {
    return <Info className={className} />;
  }
  return <AlertTriangle className={className} />;
}

export function AlertsBanner({ companyId }: { companyId: string }) {
  const { data: alerts } = useAlerts(companyId);

  if (!alerts || alerts.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      <p className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <Bell className="size-4" /> Alertas e recomendações
      </p>
      {alerts.map((alert) => (
        <AlertRow key={alert.code} companyId={companyId} alert={alert} />
      ))}
    </div>
  );
}

function AlertRow({ companyId, alert }: { companyId: string; alert: AlertResponse }) {
  const styles = STYLES[alert.severity];
  return (
    <div className={cn("flex items-start gap-3 rounded-lg border p-3", styles.box)}>
      <AlertIcon severity={alert.severity} />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium">{alert.title}</p>
        <p className="text-xs text-muted-foreground">{alert.message}</p>
      </div>
      {alert.action !== null && (
        <Link
          to={alert.action === "" ? `/c/${companyId}` : `/c/${companyId}/${alert.action}`}
          className="mt-0.5 flex shrink-0 items-center gap-1 text-xs font-medium text-primary hover:underline"
        >
          Resolver <ArrowRight className="size-3" />
        </Link>
      )}
    </div>
  );
}
