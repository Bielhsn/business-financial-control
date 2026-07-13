import { motion } from "framer-motion";
import {
  ArrowRight,
  BarChart3,
  Building2,
  LayoutGrid,
  Lock,
  Sparkles,
  TrendingUp,
  Wallet,
} from "lucide-react";
import { Link } from "react-router-dom";

import { AurumLogo, AurumMark } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { BRAND } from "@/lib/brand";

const FEATURES = [
  {
    icon: Sparkles,
    title: "Onboarding com IA",
    description:
      "Descreva seu negócio com suas palavras — de barbearia a fintech — e a IA monta módulos, categorias e indicadores sob medida.",
  },
  {
    icon: LayoutGrid,
    title: "Painel por segmento",
    description:
      "Nada de dashboard genérico: cada empresa recebe as telas e métricas que fazem sentido para o seu ramo.",
  },
  {
    icon: Wallet,
    title: "Financeiro completo",
    description:
      "Fluxo de caixa, contas a pagar e receber, categorias organizadas e valores sempre exatos — sem erros de arredondamento.",
  },
  {
    icon: BarChart3,
    title: "Indicadores que calculam sozinhos",
    description:
      "KPIs sugeridos pela IA viram números reais: receita, margem, ticket médio, clientes ativos e evolução mensal.",
  },
  {
    icon: TrendingUp,
    title: "Insights automáticos",
    description:
      "Destaques, alertas e oportunidades gerados por IA sobre os seus números — interpretação, não achismo.",
  },
  {
    icon: Lock,
    title: "Segurança de verdade",
    description:
      "Isolamento total entre empresas, papéis por usuário, auditoria de ações sensíveis e criptografia forte de senhas.",
  },
];

const STEPS = [
  {
    number: "01",
    title: "Conte sobre o seu negócio",
    description: "Segmento, porte, cidade, como você vende. Duas telas, dois minutos.",
  },
  {
    number: "02",
    title: "A IA monta o seu painel",
    description:
      "Módulos, categorias financeiras, KPIs e campos de cliente específicos do seu segmento.",
  },
  {
    number: "03",
    title: "Gerencie e cresça",
    description:
      "Lance receitas e despesas, acompanhe indicadores e receba insights para decidir melhor.",
  },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4">
          <AurumLogo withProductSuffix />
          <nav className="flex items-center gap-2">
            <Button variant="ghost" asChild>
              <Link to="/login">Entrar</Link>
            </Button>
            <Button asChild>
              <Link to="/register">
                Começar agora <ArrowRight />
              </Link>
            </Button>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto w-full max-w-6xl px-4 pb-20 pt-16 text-center sm:pt-24">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
          <span className="inline-flex items-center gap-1.5 rounded-full border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
            <Sparkles className="size-3.5 text-primary" /> Impulsionado por inteligência artificial
          </span>
          <h1 className="mx-auto mt-6 max-w-3xl font-display text-4xl font-semibold leading-tight tracking-tight sm:text-6xl">
            {BRAND.slogan.replace(".", "")} para o seu negócio.
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-base text-muted-foreground sm:text-lg">
            {BRAND.description}
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button size="lg" asChild>
              <Link to="/register">
                Criar conta gratuita <ArrowRight />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link to="/login">Já tenho conta</Link>
            </Button>
          </div>
        </motion.div>

        {/* Mock preview do painel */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.15, ease: "easeOut" }}
          className="mx-auto mt-14 max-w-4xl"
          aria-hidden="true"
        >
          <div className="rounded-xl border bg-card p-4 shadow-lg sm:p-6">
            <div className="grid gap-3 sm:grid-cols-3">
              {[
                { label: "Receita do mês", value: "R$ 48.350,00", delta: "+12,4%" },
                { label: "Lucro", value: "R$ 19.702,00", delta: "+8,1%" },
                { label: "Ticket médio", value: "R$ 86,50", delta: "+3,2%" },
              ].map((stat) => (
                <div key={stat.label} className="rounded-lg border bg-background p-4 text-left">
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                  <p className="mt-1 text-lg font-semibold tracking-tight">{stat.value}</p>
                  <p className="mt-0.5 text-xs font-medium text-success">{stat.delta}</p>
                </div>
              ))}
            </div>
            <div className="mt-3 grid grid-cols-12 items-end gap-1.5 rounded-lg border bg-background p-4">
              {[35, 48, 42, 60, 55, 72, 66, 80, 74, 88, 82, 96].map((height, index) => (
                <div key={index} className="flex flex-col gap-1">
                  <div
                    className="w-full rounded-sm bg-primary/80"
                    style={{ height: `${height * 0.9}px` }}
                  />
                  <div
                    className="w-full rounded-sm bg-muted-foreground/25"
                    style={{ height: `${height * 0.45}px` }}
                  />
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section className="border-t bg-card/50">
        <div className="mx-auto w-full max-w-6xl px-4 py-20">
          <h2 className="text-center font-display text-3xl font-semibold tracking-tight">
            Um painel que entende o seu segmento
          </h2>
          <p className="mx-auto mt-3 max-w-lg text-center text-muted-foreground">
            Barbearia, hamburgueria, clínica, loja ou SaaS — o {BRAND.shortName} se adapta ao seu
            negócio, e não o contrário.
          </p>
          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-40px" }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <Card className="h-full">
                  <CardContent className="p-6">
                    <div className="flex size-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                      <feature.icon className="size-5" />
                    </div>
                    <h3 className="mt-4 font-medium">{feature.title}</h3>
                    <p className="mt-1.5 text-sm text-muted-foreground">{feature.description}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Como funciona */}
      <section className="mx-auto w-full max-w-6xl px-4 py-20">
        <h2 className="text-center font-display text-3xl font-semibold tracking-tight">
          Do cadastro ao painel em minutos
        </h2>
        <div className="mt-12 grid gap-8 sm:grid-cols-3">
          {STEPS.map((step) => (
            <div key={step.number} className="text-center sm:text-left">
              <span className="font-display text-4xl font-semibold text-primary/40">
                {step.number}
              </span>
              <h3 className="mt-2 font-medium">{step.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{step.description}</p>
            </div>
          ))}
        </div>
        <div className="mt-14 flex justify-center">
          <Button size="lg" asChild>
            <Link to="/register">
              <Building2 /> Cadastrar minha empresa
            </Link>
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t">
        <div className="mx-auto flex w-full max-w-6xl flex-col items-center justify-between gap-4 px-4 py-10 sm:flex-row">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <AurumMark className="size-5" />
            <span>
              © {new Date().getFullYear()} {BRAND.company}
            </span>
          </div>
          <p className="max-w-md text-center text-xs text-muted-foreground sm:text-right">
            Nossa missão: dar a qualquer empresa a inteligência financeira de uma grande corporação.
          </p>
        </div>
      </footer>
    </div>
  );
}
