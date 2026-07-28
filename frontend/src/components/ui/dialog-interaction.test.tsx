/**
 * Regressão do comportamento das modais.
 *
 * O sintoma relatado era "a modal fecha sozinha ao interagir com um bloco
 * interno". A causa não estava no Dialog: o HTML assume `type="submit"` para
 * todo <button> dentro de um <form>, então qualquer botão auxiliar submetia o
 * formulário — a mutação rodava e a modal fechava no meio do preenchimento.
 *
 * Estes testes travam a regra na base (Button + Dialog), que é onde a correção
 * vale para todas as telas de uma vez.
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

describe("Button", () => {
  it("é type=button por padrão para não submeter o formulário sem querer", () => {
    render(<Button>Adicionar variação</Button>);
    expect(screen.getByRole("button", { name: "Adicionar variação" })).toHaveAttribute(
      "type",
      "button",
    );
  });

  it("respeita type=submit quando o envio é explícito", () => {
    render(<Button type="submit">Salvar</Button>);
    expect(screen.getByRole("button", { name: "Salvar" })).toHaveAttribute("type", "submit");
  });
});

function FormDialog({ onSubmit }: { onSubmit: () => void }) {
  const [open, setOpen] = useState(false);
  const [itens, setItens] = useState(0);
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Novo lançamento</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Novo lançamento</DialogTitle>
        </DialogHeader>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            onSubmit();
            setOpen(false);
          }}
        >
          <Button onClick={() => setItens((v) => v + 1)}>Adicionar item</Button>
          <span data-testid="itens">{itens}</span>
          <Button type="submit">Salvar</Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}

describe("Dialog com formulário", () => {
  it("um botão auxiliar age sem submeter nem fechar a modal", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<FormDialog onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: "Novo lançamento" }));
    await user.click(await screen.findByRole("button", { name: "Adicionar item" }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByTestId("itens")).toHaveTextContent("1");
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("o botão de salvar continua submetendo e fechando", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<FormDialog onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: "Novo lançamento" }));
    await user.click(await screen.findByRole("button", { name: "Salvar" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
