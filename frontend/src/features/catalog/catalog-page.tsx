import { zodResolver } from "@hookform/resolvers/zod";
import { Package, PackagePlus, Plus, Wrench } from "lucide-react";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useAdjustStock,
  useCatalogItems,
  useCreateCatalogItem,
} from "@/features/catalog/use-catalog";
import { extractErrorMessage } from "@/lib/api";
import type { CatalogItemResponse } from "@/lib/api-types";
import { parseCurrencyToCents } from "@/lib/money";
import { formatCents } from "@/lib/utils";

const itemSchema = z.object({
  name: z.string().min(1, "Informe o nome.").max(200),
  kind: z.enum(["product", "service"]),
  price: z
    .string()
    .min(1, "Informe o preço.")
    .refine((value) => {
      const cents = parseCurrencyToCents(value);
      return cents !== null && cents > 0;
    }, "Preço inválido — use o formato 1.234,56."),
  tracks_inventory: z.enum(["yes", "no"]),
  stock_quantity: z.string().optional(),
  description: z.string().max(2000).optional(),
});

type ItemForm = z.infer<typeof itemSchema>;

function NewItemDialog({ companyId }: { companyId: string }) {
  const [open, setOpen] = useState(false);
  const createItem = useCreateCatalogItem(companyId);

  const {
    register,
    handleSubmit,
    control,
    watch,
    reset,
    formState: { errors },
  } = useForm<ItemForm>({
    resolver: zodResolver(itemSchema),
    defaultValues: { kind: "product", tracks_inventory: "no" },
  });

  const kind = watch("kind");
  const tracksInventory = watch("tracks_inventory") === "yes" && kind === "product";

  const onSubmit = handleSubmit((values) => {
    const cents = parseCurrencyToCents(values.price);
    if (cents === null) {
      return;
    }
    createItem.mutate(
      {
        name: values.name,
        kind: values.kind,
        price_cents: cents,
        description: values.description || null,
        tracks_inventory: tracksInventory,
        stock_quantity: tracksInventory ? Number(values.stock_quantity || 0) : null,
      },
      {
        onSuccess: () => {
          toast.success("Item criado!");
          reset({ kind: values.kind, tracks_inventory: "no" });
          setOpen(false);
        },
        onError: (error) => toast.error(extractErrorMessage(error)),
      },
    );
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus /> Novo item
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Novo produto ou serviço</DialogTitle>
          <DialogDescription>
            Produtos podem controlar estoque; serviços não têm estoque.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="item-name">Nome</Label>
              <Input id="item-name" {...register("name")} />
              {errors.name && (
                <p role="alert" className="text-sm text-destructive">
                  {errors.name.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label>Tipo</Label>
              <Controller
                control={control}
                name="kind"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger aria-label="Tipo do item">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="product">Produto</SelectItem>
                      <SelectItem value="service">Serviço</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="item-price">Preço (R$)</Label>
              <Input
                id="item-price"
                inputMode="decimal"
                placeholder="99,90"
                {...register("price")}
              />
              {errors.price && (
                <p role="alert" className="text-sm text-destructive">
                  {errors.price.message}
                </p>
              )}
            </div>
            {kind === "product" && (
              <div className="space-y-2">
                <Label>Controlar estoque?</Label>
                <Controller
                  control={control}
                  name="tracks_inventory"
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger aria-label="Controlar estoque">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="no">Não</SelectItem>
                        <SelectItem value="yes">Sim</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
            )}
          </div>

          {tracksInventory && (
            <div className="space-y-2">
              <Label htmlFor="item-stock">Estoque inicial</Label>
              <Input
                id="item-stock"
                type="number"
                min={0}
                defaultValue={0}
                {...register("stock_quantity")}
              />
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="item-description">Descrição (opcional)</Label>
            <Input id="item-description" {...register("description")} />
          </div>

          <DialogFooter>
            <Button type="submit" disabled={createItem.isPending}>
              {createItem.isPending ? "Salvando…" : "Criar item"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

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

export function CatalogPage() {
  const { companyId } = useParams<{ companyId: string }>();
  const id = companyId ?? "";
  const { data: items, isLoading } = useCatalogItems(id);

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-8">
      <PageHeader
        title="Produtos & Serviços"
        description="Catálogo do que a sua empresa vende, com controle de estoque para produtos."
      >
        <NewItemDialog companyId={id} />
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
            <Card key={item.id}>
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    {item.kind === "product" ? (
                      <Package className="size-4 text-primary" />
                    ) : (
                      <Wrench className="size-4 text-primary" />
                    )}
                    <p className="font-medium">{item.name}</p>
                  </div>
                  <Badge variant="secondary">
                    {item.kind === "product" ? "Produto" : "Serviço"}
                  </Badge>
                </div>
                <p className="mt-2 text-lg font-semibold">{formatCents(item.price_cents)}</p>
                {item.description && (
                  <p className="mt-1 text-sm text-muted-foreground">{item.description}</p>
                )}
                {item.tracks_inventory && (
                  <div className="mt-3 flex items-center justify-between">
                    <Badge variant={(item.stock_quantity ?? 0) > 0 ? "success" : "destructive"}>
                      Estoque: {item.stock_quantity ?? 0}
                    </Badge>
                    <AdjustStockDialog item={item} companyId={id} />
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
