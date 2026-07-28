import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderHook, act } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Pagination, pageNumbers, usePagination } from "@/components/ui/pagination";

const itens = Array.from({ length: 23 }, (_, index) => `item-${index + 1}`);

describe("usePagination", () => {
  it("fatia em páginas de 5 e descreve a faixa exibida", () => {
    const { result } = renderHook(() => usePagination(itens));

    expect(result.current.pageItems).toEqual(["item-1", "item-2", "item-3", "item-4", "item-5"]);
    expect(result.current.totalPages).toBe(5);
    expect(result.current.total).toBe(23);
    expect(result.current.rangeStart).toBe(1);
    expect(result.current.rangeEnd).toBe(5);
  });

  it("navega até a última página, que pode ficar incompleta", () => {
    const { result } = renderHook(() => usePagination(itens));

    act(() => result.current.setPage(5));

    expect(result.current.pageItems).toEqual(["item-21", "item-22", "item-23"]);
    expect(result.current.rangeStart).toBe(21);
    expect(result.current.rangeEnd).toBe(23);
  });

  it("todos os registros continuam alcançáveis navegando", () => {
    const { result } = renderHook(() => usePagination(itens));
    const vistos: string[] = [];

    for (let page = 1; page <= result.current.totalPages; page += 1) {
      act(() => result.current.setPage(page));
      vistos.push(...result.current.pageItems);
    }

    expect(vistos).toEqual(itens);
  });

  it("recua quando a lista encolhe e a página atual deixa de existir", () => {
    const { result, rerender } = renderHook(({ lista }) => usePagination(lista), {
      initialProps: { lista: itens },
    });

    act(() => result.current.setPage(5));
    rerender({ lista: itens.slice(0, 6) });

    // 6 itens = 2 páginas; a página 5 não existe mais.
    expect(result.current.page).toBe(2);
    expect(result.current.pageItems).toEqual(["item-6"]);
  });

  it("lista vazia não quebra a faixa exibida", () => {
    const { result } = renderHook(() => usePagination([]));

    expect(result.current.totalPages).toBe(1);
    expect(result.current.rangeStart).toBe(0);
    expect(result.current.rangeEnd).toBe(0);
  });
});

describe("pageNumbers", () => {
  it("mostra todas quando são poucas", () => {
    expect(pageNumbers(1, 4)).toEqual([1, 2, 3, 4]);
  });

  it("resume com reticências mantendo início, fim e vizinhança", () => {
    expect(pageNumbers(10, 20)).toEqual([1, "…", 9, 10, 11, "…", 20]);
  });
});

describe("Pagination", () => {
  it("informa o contexto e navega", async () => {
    const user = userEvent.setup();
    const onPageChange = vi.fn();
    render(
      <Pagination
        page={1}
        totalPages={5}
        total={23}
        rangeStart={1}
        rangeEnd={5}
        onPageChange={onPageChange}
        label="lançamentos"
      />,
    );

    expect(screen.getByText("Exibindo 1–5 de 23 lançamentos")).toBeInTheDocument();
    expect(screen.getByLabelText("Página anterior")).toBeDisabled();

    await user.click(screen.getByLabelText("Próxima página"));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it("some quando há uma página só", () => {
    const { container } = render(
      <Pagination
        page={1}
        totalPages={1}
        total={3}
        rangeStart={1}
        rangeEnd={3}
        onPageChange={vi.fn()}
      />,
    );
    expect(container).toBeEmptyDOMElement();
  });
});
