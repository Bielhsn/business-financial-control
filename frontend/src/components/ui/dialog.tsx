import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";

const Dialog = DialogPrimitive.Root;
const DialogTrigger = DialogPrimitive.Trigger;
const DialogClose = DialogPrimitive.Close;

/**
 * Selects, dropdowns e popovers do Radix renderizam em portal — o conteúdo deles
 * fica FORA do DOM do dialog. Sem este guarda, escolher uma opção no select conta
 * como "clique fora" e o dialog inteiro fecha junto, perdendo o que o usuário
 * digitou. Aqui, eventos vindos de qualquer camada flutuante são ignorados: só
 * clique no overlay de verdade fecha.
 *
 * A lista cobre seletor por atributo do Radix (popper/select/dropdown) e também
 * o toaster do sonner, que aparece por cima da modal — um aviso de erro que
 * fechasse o formulário ao ser tocado seria o pior momento possível para perder
 * o que foi digitado.
 */
const FLOATING_LAYER_SELECTORS = [
  "[data-radix-popper-content-wrapper]",
  "[data-radix-select-content]",
  "[data-radix-select-viewport]",
  "[data-radix-menu-content]",
  "[role='listbox']",
  "[role='menu']",
  "[data-sonner-toaster]",
] as const;

function isInsideFloatingLayer(target: EventTarget | null): boolean {
  if (!(target instanceof Element)) {
    return false;
  }
  return FLOATING_LAYER_SELECTORS.some((selector) => target.closest(selector) !== null);
}

function DialogContent({
  className,
  children,
  onPointerDownOutside,
  onInteractOutside,
  ...props
}: React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60 data-[state=open]:animate-in data-[state=open]:fade-in-0" />
      <DialogPrimitive.Content
        className={cn(
          "fixed left-1/2 top-1/2 z-50 grid max-h-[90dvh] w-full max-w-lg -translate-x-1/2 -translate-y-1/2 gap-4 overflow-y-auto border bg-card p-6 shadow-lg sm:rounded-xl",
          className,
        )}
        onPointerDownOutside={(event) => {
          if (isInsideFloatingLayer(event.target)) {
            event.preventDefault();
            return;
          }
          onPointerDownOutside?.(event);
        }}
        onInteractOutside={(event) => {
          if (isInsideFloatingLayer(event.target)) {
            event.preventDefault();
            return;
          }
          onInteractOutside?.(event);
        }}
        {...props}
      >
        {children}
        <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring">
          <X className="size-4" />
          <span className="sr-only">Fechar</span>
        </DialogPrimitive.Close>
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}

function DialogHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col space-y-1.5 text-center sm:text-left", className)}
      {...props}
    />
  );
}

function DialogFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2", className)}
      {...props}
    />
  );
}

function DialogTitle({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>) {
  return (
    <DialogPrimitive.Title
      className={cn("text-lg font-semibold leading-none tracking-tight", className)}
      {...props}
    />
  );
}

function DialogDescription({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>) {
  return (
    <DialogPrimitive.Description
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  );
}

export {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
};
