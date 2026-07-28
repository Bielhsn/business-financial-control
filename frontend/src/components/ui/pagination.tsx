/**
 * Paginação reutilizável para qualquer lista do sistema.
 *
 * Existe como componente único de propósito: sem isso, cada tela reinventa a
 * navegação com uma regra ligeiramente diferente — e o usuário aprende o padrão
 * de novo em cada módulo. Aqui a regra é uma só: página, tamanho, faixa exibida
 * e rótulo de contexto vêm do mesmo lugar.
 *
 * Nenhum registro é escondido: tudo continua alcançável navegando.
 */
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";

/** Padrão do produto: listas longas cansam mais do que paginar. */
export const DEFAULT_PAGE_SIZE = 5;

export interface PaginationState<T> {
  /** Só os itens da página atual — é isto que a tela renderiza. */
  pageItems: T[];
  page: number;
  setPage: (page: number) => void;
  totalPages: number;
  total: number;
  /** Posição do primeiro/último item da página no total (base 1, para exibir). */
  rangeStart: number;
  rangeEnd: number;
  pageSize: number;
}

/**
 * Fatia uma lista já carregada. Para volumes grandes, prefira paginar no
 * servidor e usar `usePagedQuery` — este hook é para coleções que já vêm
 * inteiras e cabem na memória sem custo.
 */
export function usePagination<T>(items: T[], pageSize: number = DEFAULT_PAGE_SIZE) {
  const [page, setPage] = useState(1);
  const total = items.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  // Filtrar/remover registros pode encolher a lista abaixo da página atual —
  // sem isto o usuário ficaria olhando uma página vazia sem entender por quê.
  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  const safePage = Math.min(page, totalPages);
  const pageItems = useMemo(
    () => items.slice((safePage - 1) * pageSize, safePage * pageSize),
    [items, safePage, pageSize],
  );

  return {
    pageItems,
    page: safePage,
    setPage,
    totalPages,
    total,
    rangeStart: total === 0 ? 0 : (safePage - 1) * pageSize + 1,
    rangeEnd: Math.min(safePage * pageSize, total),
    pageSize,
  } satisfies PaginationState<T>;
}

/**
 * Números de página a exibir, com reticências quando são muitas.
 * Ex.: 1 … 4 5 6 … 20 — mantém início, fim e a vizinhança da página atual.
 */
export function pageNumbers(current: number, totalPages: number, maxButtons = 5): (number | "…")[] {
  if (totalPages <= maxButtons) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }
  const pages = new Set<number>([1, totalPages, current]);
  pages.add(Math.max(1, current - 1));
  pages.add(Math.min(totalPages, current + 1));

  const sorted = [...pages].sort((a, b) => a - b);
  const result: (number | "…")[] = [];
  let previous = 0;
  for (const page of sorted) {
    if (previous !== 0 && page - previous > 1) {
      result.push("…");
    }
    result.push(page);
    previous = page;
  }
  return result;
}

interface PaginationProps {
  page: number;
  totalPages: number;
  total: number;
  rangeStart: number;
  rangeEnd: number;
  onPageChange: (page: number) => void;
  /** Como chamar o que está sendo listado: "clientes", "lançamentos"… */
  label?: string;
  className?: string;
}

export function Pagination({
  page,
  totalPages,
  total,
  rangeStart,
  rangeEnd,
  onPageChange,
  label = "registros",
  className,
}: PaginationProps) {
  // Uma página só: o rodapé viraria ruído — não há para onde navegar.
  if (totalPages <= 1) {
    return null;
  }

  return (
    <nav
      aria-label="Paginação"
      className={
        "flex flex-col items-center justify-between gap-3 border-t pt-3 sm:flex-row " +
        (className ?? "")
      }
    >
      <p className="text-xs text-muted-foreground" aria-live="polite">
        Exibindo {rangeStart}–{rangeEnd} de {total} {label}
      </p>
      <div className="flex items-center gap-1">
        <Button
          size="icon-sm"
          variant="outline"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          aria-label="Página anterior"
        >
          <ChevronLeft />
        </Button>
        {pageNumbers(page, totalPages).map((item, index) =>
          item === "…" ? (
            <span key={`gap-${index}`} className="px-1 text-xs text-muted-foreground">
              …
            </span>
          ) : (
            <Button
              key={item}
              size="icon-sm"
              variant={item === page ? "default" : "outline"}
              onClick={() => onPageChange(item)}
              aria-label={`Página ${item}`}
              aria-current={item === page ? "page" : undefined}
            >
              {item}
            </Button>
          ),
        )}
        <Button
          size="icon-sm"
          variant="outline"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          aria-label="Próxima página"
        >
          <ChevronRight />
        </Button>
      </div>
    </nav>
  );
}
