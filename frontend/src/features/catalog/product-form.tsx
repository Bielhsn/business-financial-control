import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, ArrowRight, ImagePlus, Plus, Star, Trash2 } from "lucide-react";
import { useMemo, useRef, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import { Textarea } from "@/components/ui/textarea";
import {
  useCreateCatalogItem,
  useUpdateCatalogItem,
  type CatalogItemInput,
  type ProductVariantInput,
} from "@/features/catalog/use-catalog";
import { extractErrorMessage } from "@/lib/api";
import type { CatalogItemResponse } from "@/lib/api-types";
import { centsToInput, marginPct, parseCurrencyToCents } from "@/lib/money";

// Mesmos limites do backend (schemas/catalog.py): 6 imagens de até ~150 KB
// (~200k chars em data URL base64).
const MAX_IMAGES = 6;
const MAX_IMAGE_CHARS = 200_000;

const optionalPrice = z
  .string()
  .optional()
  .refine(
    (value) => !value || parseCurrencyToCents(value) !== null,
    "Valor inválido — use o formato 1.234,56.",
  );

const productSchema = z.object({
  name: z.string().min(1, "Informe o nome.").max(200),
  kind: z.enum(["product", "service"]),
  price: z
    .string()
    .min(1, "Informe o preço.")
    .refine((value) => {
      const cents = parseCurrencyToCents(value);
      return cents !== null && cents > 0;
    }, "Preço inválido — use o formato 1.234,56."),
  cost_price: optionalPrice,
  promo_price: optionalPrice,
  sku: z.string().max(64).optional(),
  barcode: z.string().max(64).optional(),
  brand: z.string().max(120).optional(),
  supplier: z.string().max(200).optional(),
  category: z.string().max(120).optional(),
  subcategory: z.string().max(120).optional(),
  tags: z.string().max(600).optional(),
  short_description: z.string().max(300).optional(),
  description: z.string().max(5000).optional(),
  tracks_inventory: z.enum(["yes", "no"]),
  stock_quantity: z.string().optional(),
  min_stock: z.string().optional(),
  max_stock: z.string().optional(),
  stock_location: z.string().max(200).optional(),
});

type ProductForm = z.infer<typeof productSchema>;

interface VariantRow {
  name: string;
  sku: string;
  price: string;
  stock: string;
}

function toOptionalInt(raw: string | undefined): number | null {
  if (!raw || raw.trim() === "") {
    return null;
  }
  const value = Number(raw);
  return Number.isInteger(value) && value >= 0 ? value : null;
}

function defaultsFromItem(item: CatalogItemResponse | undefined): ProductForm {
  return {
    name: item?.name ?? "",
    kind: item?.kind ?? "product",
    price: item ? centsToInput(item.price_cents) : "",
    cost_price: item?.cost_price_cents != null ? centsToInput(item.cost_price_cents) : "",
    promo_price: item?.promo_price_cents != null ? centsToInput(item.promo_price_cents) : "",
    sku: item?.sku ?? "",
    barcode: item?.barcode ?? "",
    brand: item?.brand ?? "",
    supplier: item?.supplier ?? "",
    category: item?.category ?? "",
    subcategory: item?.subcategory ?? "",
    tags: item?.tags.join(", ") ?? "",
    short_description: item?.short_description ?? "",
    description: item?.description ?? "",
    tracks_inventory: item?.tracks_inventory ? "yes" : "no",
    stock_quantity: "0",
    min_stock: item?.min_stock != null ? String(item.min_stock) : "",
    max_stock: item?.max_stock != null ? String(item.max_stock) : "",
    stock_location: item?.stock_location ?? "",
  };
}

function variantsFromItem(item: CatalogItemResponse | undefined): VariantRow[] {
  return (item?.variants ?? []).map((variant) => ({
    name: variant.name,
    sku: variant.sku ?? "",
    price: variant.price_cents != null ? centsToInput(variant.price_cents) : "",
    stock: String(variant.stock_quantity),
  }));
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <p className="border-b pb-1 text-sm font-semibold text-muted-foreground">{children}</p>;
}

/** Formulário completo de produto/serviço — criação (sem `item`) ou edição. */
export function ProductFormDialog({
  companyId,
  item,
  trigger,
}: {
  companyId: string;
  item?: CatalogItemResponse;
  trigger: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [images, setImages] = useState<string[]>(item?.images ?? []);
  const [variants, setVariants] = useState<VariantRow[]>(variantsFromItem(item));
  const fileInputRef = useRef<HTMLInputElement>(null);
  const createItem = useCreateCatalogItem(companyId);
  const updateItem = useUpdateCatalogItem(companyId);
  const isEditing = item !== undefined;

  const {
    register,
    handleSubmit,
    control,
    watch,
    reset,
    formState: { errors },
  } = useForm<ProductForm>({
    resolver: zodResolver(productSchema),
    defaultValues: defaultsFromItem(item),
  });

  const kind = watch("kind");
  const tracksInventory = watch("tracks_inventory") === "yes" && kind === "product";
  const priceValue = watch("price");
  const costValue = watch("cost_price");
  const promoValue = watch("promo_price");

  const previewMargin = useMemo(() => {
    const price = parseCurrencyToCents(priceValue ?? "");
    const cost = costValue ? parseCurrencyToCents(costValue) : null;
    const promo = promoValue ? parseCurrencyToCents(promoValue) : null;
    if (price === null || cost === null) {
      return null;
    }
    return marginPct(price, cost, promo);
  }, [priceValue, costValue, promoValue]);

  function resetAll() {
    reset(defaultsFromItem(item));
    setImages(item?.images ?? []);
    setVariants(variantsFromItem(item));
  }

  function handleOpenChange(next: boolean) {
    setOpen(next);
    if (next) {
      resetAll();
    }
  }

  function addImages(files: FileList | null) {
    if (!files) {
      return;
    }
    for (const file of Array.from(files)) {
      if (!file.type.startsWith("image/")) {
        toast.error(`${file.name}: apenas imagens são aceitas.`);
        continue;
      }
      const reader = new FileReader();
      reader.onload = () => {
        const dataUrl = String(reader.result ?? "");
        if (dataUrl.length > MAX_IMAGE_CHARS) {
          toast.error(`${file.name}: imagem acima de ~150 KB.`);
          return;
        }
        setImages((current) => (current.length >= MAX_IMAGES ? current : [...current, dataUrl]));
      };
      reader.readAsDataURL(file);
    }
  }

  function moveImage(index: number, direction: -1 | 1) {
    setImages((current) => {
      const target = index + direction;
      if (target < 0 || target >= current.length) {
        return current;
      }
      const a = current[index];
      const b = current[target];
      if (a === undefined || b === undefined) {
        return current;
      }
      const next = [...current];
      next[index] = b;
      next[target] = a;
      return next;
    });
  }

  const onSubmit = handleSubmit((values) => {
    const price = parseCurrencyToCents(values.price);
    if (price === null) {
      return;
    }
    const variantPayload: ProductVariantInput[] = [];
    for (const row of variants) {
      if (!row.name.trim()) {
        toast.error("Toda variação precisa de um nome (ex.: Azul / M).");
        return;
      }
      const variantPrice = row.price ? parseCurrencyToCents(row.price) : null;
      variantPayload.push({
        name: row.name.trim(),
        sku: row.sku.trim() || null,
        price_cents: variantPrice,
        stock_quantity: toOptionalInt(row.stock) ?? 0,
      });
    }

    const payload: CatalogItemInput = {
      name: values.name,
      kind: values.kind,
      price_cents: price,
      description: values.description?.trim() || null,
      short_description: values.short_description?.trim() || null,
      tracks_inventory: tracksInventory,
      sku: values.sku?.trim() || null,
      barcode: values.barcode?.trim() || null,
      brand: values.brand?.trim() || null,
      supplier: values.supplier?.trim() || null,
      category: values.category?.trim() || null,
      subcategory: values.subcategory?.trim() || null,
      tags: (values.tags ?? "")
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean),
      cost_price_cents: values.cost_price ? parseCurrencyToCents(values.cost_price) : null,
      promo_price_cents: values.promo_price ? parseCurrencyToCents(values.promo_price) : null,
      min_stock: toOptionalInt(values.min_stock),
      max_stock: toOptionalInt(values.max_stock),
      stock_location: values.stock_location?.trim() || null,
      images,
      variants: kind === "product" ? variantPayload : [],
    };

    const options = {
      onSuccess: () => {
        toast.success(isEditing ? "Item atualizado!" : "Item criado!");
        setOpen(false);
      },
      onError: (error: unknown) => toast.error(extractErrorMessage(error)),
    };

    if (isEditing) {
      // Estoque não é editado aqui — ajustes passam por "Ajustar estoque",
      // que mantém o histórico de movimentações para auditoria.
      updateItem.mutate({ itemId: item.id, ...payload }, options);
    } else {
      createItem.mutate(
        {
          ...payload,
          stock_quantity: tracksInventory ? (toOptionalInt(values.stock_quantity) ?? 0) : null,
        },
        options,
      );
    }
  });

  const isPending = createItem.isPending || updateItem.isPending;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-h-[88vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? `Editar — ${item.name}` : "Novo produto ou serviço"}
          </DialogTitle>
          <DialogDescription>
            Só nome, tipo e preço são obrigatórios — os demais campos completam a ficha profissional
            do item.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-5" noValidate>
          <SectionTitle>Básico</SectionTitle>
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
                  <Select value={field.value} onValueChange={field.onChange} disabled={isEditing}>
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
            <div className="space-y-2">
              <Label htmlFor="item-category">Categoria</Label>
              <Input id="item-category" placeholder="Ex.: Vestuário" {...register("category")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="item-subcategory">Subcategoria</Label>
              <Input
                id="item-subcategory"
                placeholder="Ex.: Camisetas"
                {...register("subcategory")}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="item-brand">Marca</Label>
              <Input id="item-brand" {...register("brand")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="item-supplier">Fornecedor</Label>
              <Input id="item-supplier" {...register("supplier")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="item-sku">SKU</Label>
              <Input id="item-sku" placeholder="Ex.: CAM-001" {...register("sku")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="item-barcode">Código de barras</Label>
              <Input id="item-barcode" inputMode="numeric" {...register("barcode")} />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="item-tags">Tags (separadas por vírgula)</Label>
            <Input id="item-tags" placeholder="algodão, básico, verão" {...register("tags")} />
          </div>

          <SectionTitle>Preços</SectionTitle>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="item-cost">Custo (R$)</Label>
              <Input
                id="item-cost"
                inputMode="decimal"
                placeholder="32,00"
                {...register("cost_price")}
              />
              {errors.cost_price && (
                <p role="alert" className="text-sm text-destructive">
                  {errors.cost_price.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="item-price">Venda (R$)</Label>
              <Input
                id="item-price"
                inputMode="decimal"
                placeholder="79,90"
                {...register("price")}
              />
              {errors.price && (
                <p role="alert" className="text-sm text-destructive">
                  {errors.price.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="item-promo">Promocional (R$)</Label>
              <Input
                id="item-promo"
                inputMode="decimal"
                placeholder="59,90"
                {...register("promo_price")}
              />
              {errors.promo_price && (
                <p role="alert" className="text-sm text-destructive">
                  {errors.promo_price.message}
                </p>
              )}
            </div>
          </div>
          {previewMargin !== null && (
            <p className="text-sm text-muted-foreground">
              Margem estimada:{" "}
              <span
                className={
                  previewMargin >= 0 ? "font-medium text-primary" : "font-medium text-destructive"
                }
              >
                {previewMargin.toLocaleString("pt-BR")}%
              </span>{" "}
              sobre o preço efetivo de venda.
            </p>
          )}

          {kind === "product" && (
            <>
              <SectionTitle>Estoque</SectionTitle>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Controlar estoque?</Label>
                  <Controller
                    control={control}
                    name="tracks_inventory"
                    render={({ field }) => (
                      <Select
                        value={field.value}
                        onValueChange={field.onChange}
                        disabled={isEditing}
                      >
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
                  {isEditing && item.tracks_inventory && (
                    <p className="text-xs text-muted-foreground">
                      Quantidade em estoque é alterada por “Ajustar estoque”, que mantém o histórico
                      para auditoria.
                    </p>
                  )}
                </div>
                {tracksInventory && !isEditing && (
                  <div className="space-y-2">
                    <Label htmlFor="item-stock">Estoque inicial</Label>
                    <Input id="item-stock" type="number" min={0} {...register("stock_quantity")} />
                  </div>
                )}
                {tracksInventory && (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="item-min-stock">Estoque mínimo (alerta)</Label>
                      <Input id="item-min-stock" type="number" min={0} {...register("min_stock")} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="item-max-stock">Estoque máximo</Label>
                      <Input id="item-max-stock" type="number" min={0} {...register("max_stock")} />
                    </div>
                    <div className="space-y-2 sm:col-span-2">
                      <Label htmlFor="item-location">Localização no estoque</Label>
                      <Input
                        id="item-location"
                        placeholder="Ex.: Prateleira A3"
                        {...register("stock_location")}
                      />
                    </div>
                  </>
                )}
              </div>
            </>
          )}

          <SectionTitle>Descrições</SectionTitle>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="item-short-description">Descrição curta</Label>
              <Input
                id="item-short-description"
                placeholder="Resumo em uma frase (aparece em listagens)."
                {...register("short_description")}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="item-description">Descrição completa</Label>
              <Textarea id="item-description" rows={4} {...register("description")} />
            </div>
          </div>

          <SectionTitle>
            Imagens ({images.length}/{MAX_IMAGES})
          </SectionTitle>
          <div className="space-y-3">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              aria-label="Adicionar imagens"
              onChange={(event) => {
                addImages(event.target.files);
                event.target.value = "";
              }}
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={images.length >= MAX_IMAGES}
              onClick={() => fileInputRef.current?.click()}
            >
              <ImagePlus /> Adicionar imagens
            </Button>
            {images.length > 0 && (
              <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
                {images.map((image, index) => (
                  <div key={`${index}-${image.slice(-24)}`} className="space-y-1">
                    <div className="relative overflow-hidden rounded-md border">
                      <img
                        src={image}
                        alt={`Imagem ${index + 1}`}
                        className="aspect-square w-full object-cover"
                      />
                      {index === 0 && (
                        <Badge className="absolute left-1 top-1" variant="secondary">
                          Principal
                        </Badge>
                      )}
                    </div>
                    <div className="flex justify-center gap-1">
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon-sm"
                        aria-label={`Mover imagem ${index + 1} para a esquerda`}
                        disabled={index === 0}
                        onClick={() => moveImage(index, -1)}
                      >
                        <ArrowLeft />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon-sm"
                        aria-label={`Definir imagem ${index + 1} como principal`}
                        disabled={index === 0}
                        onClick={() =>
                          setImages((current) => {
                            const chosen = current[index];
                            if (chosen === undefined) {
                              return current;
                            }
                            return [chosen, ...current.filter((_, i) => i !== index)];
                          })
                        }
                      >
                        <Star />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon-sm"
                        aria-label={`Mover imagem ${index + 1} para a direita`}
                        disabled={index === images.length - 1}
                        onClick={() => moveImage(index, 1)}
                      >
                        <ArrowRight />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon-sm"
                        aria-label={`Excluir imagem ${index + 1}`}
                        onClick={() =>
                          setImages((current) => current.filter((_, i) => i !== index))
                        }
                      >
                        <Trash2 />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {kind === "product" && (
            <>
              <SectionTitle>Variações (cor, tamanho…)</SectionTitle>
              <div className="space-y-3">
                {variants.map((variant, index) => (
                  <div
                    key={index}
                    className="grid grid-cols-[1fr_auto] items-end gap-2 sm:grid-cols-[2fr_1fr_1fr_1fr_auto]"
                  >
                    <div className="space-y-1 sm:col-span-1">
                      <Label htmlFor={`variant-name-${index}`}>Nome</Label>
                      <Input
                        id={`variant-name-${index}`}
                        placeholder="Ex.: Azul / M"
                        value={variant.name}
                        onChange={(event) =>
                          setVariants((current) =>
                            current.map((row, i) =>
                              i === index ? { ...row, name: event.target.value } : row,
                            ),
                          )
                        }
                      />
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor={`variant-sku-${index}`}>SKU</Label>
                      <Input
                        id={`variant-sku-${index}`}
                        value={variant.sku}
                        onChange={(event) =>
                          setVariants((current) =>
                            current.map((row, i) =>
                              i === index ? { ...row, sku: event.target.value } : row,
                            ),
                          )
                        }
                      />
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor={`variant-price-${index}`}>Preço (R$)</Label>
                      <Input
                        id={`variant-price-${index}`}
                        inputMode="decimal"
                        placeholder="Herda o do item"
                        value={variant.price}
                        onChange={(event) =>
                          setVariants((current) =>
                            current.map((row, i) =>
                              i === index ? { ...row, price: event.target.value } : row,
                            ),
                          )
                        }
                      />
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor={`variant-stock-${index}`}>Estoque</Label>
                      <Input
                        id={`variant-stock-${index}`}
                        type="number"
                        min={0}
                        value={variant.stock}
                        onChange={(event) =>
                          setVariants((current) =>
                            current.map((row, i) =>
                              i === index ? { ...row, stock: event.target.value } : row,
                            ),
                          )
                        }
                      />
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      aria-label={`Remover variação ${index + 1}`}
                      onClick={() =>
                        setVariants((current) => current.filter((_, i) => i !== index))
                      }
                    >
                      <Trash2 />
                    </Button>
                  </div>
                ))}
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setVariants((current) => [
                      ...current,
                      { name: "", sku: "", price: "", stock: "0" },
                    ])
                  }
                >
                  <Plus /> Adicionar variação
                </Button>
              </div>
            </>
          )}

          <DialogFooter>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Salvando…" : isEditing ? "Salvar alterações" : "Criar item"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
