import { Sparkles } from "lucide-react";

export function OnboardingPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 p-8 text-center">
      <div className="flex size-12 items-center justify-center rounded-full bg-accent text-accent-foreground">
        <Sparkles className="size-6" />
      </div>
      <h1 className="text-xl font-semibold">Onboarding com IA</h1>
      <p className="max-w-md text-sm text-muted-foreground">
        O assistente de criação de empresa com IA chega na próxima etapa do roadmap.
      </p>
    </div>
  );
}
