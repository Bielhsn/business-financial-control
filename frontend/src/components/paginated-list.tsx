/**
 * Lista paginada pronta: recebe a coleção inteira, renderiza uma página e cuida
 * do rodapé de navegação.
 *
 * A alternativa seria repetir `usePagination` + `<Pagination>` em cada tela —
 * dez chances de divergir no tamanho da página, no rótulo ou em esquecer o
 * rodapé. Aqui a tela só diz o que listar e como desenhar cada item.
 */
import type { ReactNode } from "react";

import { DEFAULT_PAGE_SIZE, Pagination, usePagination } from "@/components/ui/pagination";

interface PaginatedListProps<T> {
  items: T[];
  /** Como desenhar um item. Lembre-se da `key`. */
  children: (item: T, index: number) => ReactNode;
  /** Como chamar o que está sendo listado, no rodapé: "clientes", "produtos"… */
  label?: string;
  pageSize?: number;
  /** Classes do contêiner dos itens (grade, divisórias…). */
  className?: string;
  /** Classes do rodapé — útil quando o cartão em volta não tem respiro. */
  paginationClassName?: string;
  /**
   * Elemento do contêiner. Precisa existir porque `<ul>` só aceita `<li>` como
   * filho: envolver itens de lista num `<div>` gera HTML inválido e quebra a
   * semântica que os leitores de tela usam para anunciar "lista de N itens".
   */
  as?: "div" | "ul";
}

export function PaginatedList<T>({
  items,
  children,
  label,
  pageSize = DEFAULT_PAGE_SIZE,
  className,
  paginationClassName,
  as: Container = "div",
}: PaginatedListProps<T>) {
  const { pageItems, page, setPage, totalPages, total, rangeStart, rangeEnd } = usePagination(
    items,
    pageSize,
  );

  return (
    <>
      <Container className={className}>
        {pageItems.map((item, index) => children(item, index))}
      </Container>
      <Pagination
        page={page}
        totalPages={totalPages}
        total={total}
        rangeStart={rangeStart}
        rangeEnd={rangeEnd}
        onPageChange={setPage}
        label={label}
        className={paginationClassName}
      />
    </>
  );
}
