/** Espelha o INTEGRATION_REGISTRY do backend
 * (backend/app/domain/blueprint/integration_registry.py) — apenas rótulos de UI;
 * o backend segue sendo a única fonte de verdade sobre ids válidos. */

export interface IntegrationInfo {
  id: string;
  name: string;
  group: string;
}

export const INTEGRATIONS: IntegrationInfo[] = [
  { id: "ifood", name: "iFood", group: "Delivery" },
  { id: "rappi", name: "Rappi", group: "Delivery" },
  { id: "uber_eats", name: "Uber Eats", group: "Delivery" },
  { id: "anota_ai", name: "Anota AI", group: "Delivery" },
  { id: "goomer", name: "Goomer", group: "Delivery" },
  { id: "kds", name: "Sistema de cozinha (KDS)", group: "Restaurantes" },
  { id: "shopify", name: "Shopify", group: "E-commerce" },
  { id: "nuvemshop", name: "Nuvemshop", group: "E-commerce" },
  { id: "tray", name: "Tray", group: "E-commerce" },
  { id: "loja_integrada", name: "Loja Integrada", group: "E-commerce" },
  { id: "woocommerce", name: "WooCommerce", group: "E-commerce" },
  { id: "mercado_livre", name: "Mercado Livre", group: "Marketplaces" },
  { id: "amazon", name: "Amazon", group: "Marketplaces" },
  { id: "shopee", name: "Shopee", group: "Marketplaces" },
  { id: "magalu", name: "Magalu", group: "Marketplaces" },
  { id: "tiktok_shop", name: "TikTok Shop", group: "Social commerce" },
  { id: "meta_commerce", name: "Meta Commerce (Instagram/Facebook)", group: "Social commerce" },
  { id: "google_merchant", name: "Google Merchant Center", group: "Social commerce" },
  { id: "melhor_envio", name: "Melhor Envio", group: "Logística" },
  { id: "correios", name: "Correios", group: "Logística" },
  { id: "jadlog", name: "Jadlog", group: "Logística" },
  { id: "loggi", name: "Loggi", group: "Logística" },
  { id: "mercado_pago", name: "Mercado Pago", group: "Pagamentos" },
  { id: "stripe", name: "Stripe", group: "Pagamentos" },
  { id: "pagseguro", name: "PagSeguro", group: "Pagamentos" },
  { id: "asaas", name: "Asaas", group: "Pagamentos" },
  { id: "pagarme", name: "Pagar.me", group: "Pagamentos" },
  { id: "pix", name: "Pix", group: "Pagamentos" },
  { id: "maquininhas", name: "Maquininhas de cartão", group: "Pagamentos" },
  { id: "pagamentos_recorrentes", name: "Pagamentos recorrentes", group: "Pagamentos" },
  { id: "nubank_pj", name: "Nubank PJ", group: "Bancos" },
  { id: "inter", name: "Inter Empresas", group: "Bancos" },
  { id: "itau", name: "Itaú", group: "Bancos" },
  { id: "c6", name: "C6 Bank", group: "Bancos" },
  { id: "omie", name: "Omie", group: "Contabilidade e fiscal" },
  { id: "conta_azul", name: "Conta Azul", group: "Contabilidade e fiscal" },
  { id: "bling", name: "Bling", group: "Contabilidade e fiscal" },
  { id: "nota_fiscal", name: "Emissão de Nota Fiscal", group: "Contabilidade e fiscal" },
  { id: "google_agenda", name: "Google Agenda", group: "Agendamento" },
  { id: "calendly", name: "Calendly", group: "Agendamento" },
  { id: "gympass", name: "Wellhub (Gympass)", group: "Fitness" },
  { id: "totalpass", name: "TotalPass", group: "Fitness" },
  { id: "catraca", name: "Controle de acesso (catraca)", group: "Fitness" },
  { id: "convenios", name: "Convênios de saúde", group: "Saúde" },
  { id: "hubspot", name: "HubSpot", group: "CRM e marketing" },
  { id: "pipedrive", name: "Pipedrive", group: "CRM e marketing" },
  { id: "rd_station", name: "RD Station", group: "CRM e marketing" },
  { id: "salesforce", name: "Salesforce", group: "CRM e marketing" },
  { id: "email_marketing", name: "E-mail marketing", group: "CRM e marketing" },
  { id: "programa_fidelidade", name: "Programa de fidelidade", group: "CRM e marketing" },
  { id: "whatsapp", name: "WhatsApp Business", group: "Comunicação" },
  { id: "slack", name: "Slack", group: "Comunicação" },
  { id: "discord", name: "Discord", group: "Comunicação" },
  { id: "instagram", name: "Instagram", group: "Comunicação" },
  { id: "google_analytics", name: "Google Analytics", group: "Analytics e produto" },
  { id: "mixpanel", name: "Mixpanel", group: "Analytics e produto" },
  { id: "posthog", name: "PostHog", group: "Analytics e produto" },
  { id: "sentry", name: "Sentry", group: "Analytics e produto" },
  { id: "github", name: "GitHub", group: "Analytics e produto" },
];

export function integrationInfo(id: string): IntegrationInfo | undefined {
  return INTEGRATIONS.find((item) => item.id === id);
}
