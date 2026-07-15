import { Package, PackagePlus, Pencil, Plus, Wrench } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useParams } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { ProductFormDialog } from "@/features/catalog/product-form";
import { useAdjustStock, useCatalogItems } from "@/features/catalog/use-catalog";
import { extractErrorMessage } from "@/lib/api";
import type { CatalogItemResponse } from "@/lib/api-types";
import { useCompanyCurrency } from "@/features/companies/use-company-currency";
import { formatCents } from "@/lib/utils";

const adjustSchema = z.object({
  delta: z
    .number({ invalid_type_error: "Informe um número (use negativo para saída)." })
    .int()
    .refine((value) => value !== 0, "O ajuste não pode ser zero."),
  reason: z.string().min(1, "Informe o motivo (auditoria).").max(500),
});

type AdjustForm = z.infer<typeof adjustSchema>;

function AdjustStockDialog({ item, companyId }: { item: CatalogItemResponse; companyId: string }) {
  const [open, setOpen] = useState(false);
  const adjustStock = useAdjustStock(companyId);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<AdjustForm>({ resolver: zodResolver(adjustSchema) });

  const onSubmit = handleSubmit((values) => {
    adjustStock.mutate(
      { itemId: item.id, delta: values.delta, reason: values.reason },
      {
        onSuccess: () => {
          toast.success("Estoque ajustado!");
          reset();
          setOpen(false);
        },
        onError: (error) => toast.error(extractErrorMessage(error)),
      },
    );
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <PackagePlus /> Ajustar estoque
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Ajustar estoque — {item.name}</DialogTitle>
          <DialogDescription>
            Estoque atual: {item.stock_quantity ?? 0}. Todo ajuste fica registrado para auditoria.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          <div className="space-y-2">
            <Label htmlFor="delta">Quantidade (negativa para saída)</Label>
            <Input
              id="delta"
              type="number"
              placeholder="Ex.: 10 ou -3"
              {...register("delta", { valueAsNumber: true })}
            />
            {errors.delta && (
              <p role="alert" className="text-sm text-destructive">
                {errors.delta.message}
              </p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="reason">Motivo</Label>
            <Input
              id="reason"
              placeholder="Ex.: compra de fornecedor, venda, perda…"
              {...register("reason")}
            />
            {errors.reason && (
              <p role="alert" className="text-sm text-destructive">
                {errors.reason.message}
              </p>
            )}
          </div>
          <DialogFooter>
            <Button type="submit" disabled={adjustStock.isPending}>
              {adjustStock.isPending ? "Ajustando…" : "Confirmar ajuste"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function ItemCard({
  item,
  companyId,
  currency,
}: {
  item: CatalogItemResponse;
  companyId: string;
  currency: string;
}) {
  const stock = item.stock_quantity ?? 0;
  const belowMin = item.tracks_inventory && item.min_stock !== null && stock <= item.min_stock;

  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex gap-4">
          {item.images.length > 0 && (
            <img
              src={item.images[0]}
              alt={item.name}
              className="size-16 shrink-0 rounded-md border object-cover"
            />
          )}
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-2">
              <div className="flex min-w-0 items-center gap-2">
                {item.kind === "product" ? (
                  <Package className="size-4 shrink-0 text-primary" />
                ) : (
                  <Wrench className="size-4 shrink-0 text-primary" />
                )}
                <p className="truncate font-medium">{item.name}</p>
              </div>
              <div className="flex shrink-0 items-center gap-1">
                <Badge variant="secondary">{item.kind === "product" ? "Produto" : "Serviço"}</Badge>
                <ProductFormDialog
                  companyId={companyId}
                  item={item}
                  trigger={
                    <Button variant="ghost" size="icon-sm" aria-label={`Editar ${item.name}`}>
                      <Pencil />
                    </Button>
                  }
                />
              </div>
            </div>
            <p className="mt-1 truncate text-xs text-muted-foreground">
              {[item.sku && `SKU ${item.sku}`, item.category, item.brand]
                .filter(Boolean)
                .join(" · ")}
            </p>
            <div className="mt-2 flex flex-wrap items-baseline gap-x-2">
              {item.promo_price_cents !== null ? (
                <>
                  <p className="text-lg font-semibold">
                    {formatCents(item.promo_price_cents, currency)}
                  </p>
                  <p className="text-sm text-muted-foreground line-through">
                    {formatCents(item.price_cents, currency)}
                  </p>
                </>
              ) : (
                <p className="text-lg font-semibold">{formatCents(item.price_cents, currency)}</p>
              )}
              {item.margin_pct !== null && (
                <span className="text-xs text-muted-foreground">
                  margem {item.margin_pct.toLocaleString("pt-BR")}%
                </span>
              )}
            </div>
          </div>
        </div>

        {(item.short_description || item.description) && (
          <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">
            {item.short_description ?? item.description}
          </p>
        )}

        {item.variants.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {item.variants.map((variant) => (
              <Badge key={variant.name} variant="outline">
                {variant.name}
                {item.tracks_inventory ? ` · ${variant.stock_quantity}` : ""}
              </Badge>
            ))}
          </div>
        )}

        {item.tracks_inventory && (
          <div className="mt-3 flex items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-1">
              <Badge variant={stock > 0 ? "success" : "destructive"}>Estoque: {stock}</Badge>
              {belowMin && <Badge variant="destructive">Abaixo do mínimo</Badge>}
            </div>
            <AdjustStockDialog item={item} companyId={companyId} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function CatalogPage() {
  const { companyId } = useParams<{ companyId: string }>();
  const id = companyId ?? "";
  const { data: items, isLoading } = useCatalogItems(id);
  const currency = useCompanyCurrency(id);

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-8">
      <PageHeader
        title="Produtos & Serviços"
        description="Catálogo profissional: SKU, imagens, variações, preços e estoque."
      >
        <ProductFormDialog
          companyId={id}
          trigger={
            <Button>
              <Plus /> Novo item
            </Button>
          }
        />
      </PageHeader>

      {isLoading && <Skeleton className="h-64 w-full" />}

      {!isLoading && (items?.length ?? 0) === 0 && (
        <EmptyState
          icon={Package}
          title="Catálogo vazio"
          description="Cadastre os produtos e serviços que a sua empresa oferece."
        />
      )}

      {(items?.length ?? 0) > 0 && (
        <div className="grid gap-3 sm:grid-cols-2">
          {(items ?? []).map((item) => (
            <ItemCard key={item.id} item={item} companyId={id} currency={currency} />
          ))}
        </div>
      )}
    </div>
  );
}
