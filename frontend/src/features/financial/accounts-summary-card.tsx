import { ArrowDownCircle, ArrowUpCircle } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { useAccounts } from "@/features/financial/use-accounts";
import type { AccountsBucketResponse } from "@/lib/api-types";
import { formatCents } from "@/lib/utils";

function Bucket({
  title,
  bucket,
  tone,
  icon: Icon,
}: {
  title: string;
  bucket: AccountsBucketResponse;
  tone: "payable" | "receivable";
  icon: typeof ArrowUpCircle;
}) {
  const accent = tone === "payable" ? "text-destructive" : "text-emerald-600";
  return (
    <Card>
      <CardContent className="space-y-3 p-5">
        <div className="flex items-center gap-2">
          <Icon className={`size-5 ${accent}`} />
          <h3 className="font-semibold">{title}</h3>
        </div>
        <p className="text-2xl font-bold tabular-nums">{formatCents(bucket.total_cents)}</p>
        <dl className="space-y-1 text-sm">
          <div className="flex justify-between">
            <dt className="text-destructive">Vencido</dt>
            <dd className="font-medium tabular-nums text-destructive">
              {formatCents(bucket.overdue_cents)}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-muted-foreground">Vence em 7 dias</dt>
            <dd className="font-medium tabular-nums">{formatCents(bucket.due_soon_cents)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-muted-foreground">Depois</dt>
            <dd className="font-medium tabular-nums">{formatCents(bucket.upcoming_cents)}</dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}

export function AccountsSummaryCard({ companyId }: { companyId: string }) {
  const accounts = useAccounts(companyId);
  if (!accounts.data) return null;

  const { payable, receivable } = accounts.data;
  if (payable.total_cents === 0 && receivable.total_cents === 0) return null;

  return (
    <div className="mb-4 grid gap-3 md:grid-cols-2">
      <Bucket title="A pagar" bucket={payable} tone="payable" icon={ArrowUpCircle} />
      <Bucket title="A receber" bucket={receivable} tone="receivable" icon={ArrowDownCircle} />
    </div>
  );
}
