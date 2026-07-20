/** Tipos espelhando os schemas Pydantic do backend (backend/app/schemas). */

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export type CompanyRole = "owner" | "admin" | "manager" | "employee" | "viewer";

export interface CompanyResponse {
  id: string;
  name: string;
  segment: string;
  employee_count: number;
  average_customer_count: number;
  city: string;
  state: string;
  country: string;
  size: string;
  tax_regime: string | null;
  additional_info: string | null;
  currency: string;
  sales_channels: string[];
  sales_mode: string | null;
  main_offerings: string | null;
  brand_logo: string | null;
  brand_primary_color: string | null;
  brand_theme: "light" | "dark" | null;
  legal_name: string | null;
  trade_name: string | null;
  cnpj: string | null;
  subsegment: string | null;
  monthly_revenue_cents: number | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  social_links: Record<string, string>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MemberResponse {
  user_id: string;
  email: string;
  full_name: string;
  role: CompanyRole;
}

export interface InvitationResponse {
  id: string;
  email: string;
  role: CompanyRole;
  status: string;
  created_at: string;
  expires_at: string;
}

export interface CnpjLookupResponse {
  cnpj: string;
  legal_name: string | null;
  trade_name: string | null;
  status: string | null;
  is_active: boolean;
  city: string | null;
  state: string | null;
  email: string | null;
  phone: string | null;
  main_activity: string | null;
}

export interface CompanyWithRoleResponse {
  company: CompanyResponse;
  role: CompanyRole;
}

export interface CreateCompanyRequest {
  name: string;
  segment: string;
  employee_count: number;
  average_customer_count: number;
  city: string;
  state: string;
  country: string;
  size: string;
  tax_regime: string | null;
  additional_info: string | null;
  currency: string;
  sales_channels: string[];
  sales_mode: string | null;
  main_offerings: string | null;
  legal_name?: string | null;
  trade_name?: string | null;
  cnpj?: string | null;
  subsegment?: string | null;
  monthly_revenue_cents?: number | null;
  phone?: string | null;
  email?: string | null;
  website?: string | null;
  social_links?: Record<string, string>;
}

export type FinancialCategoryType = "income" | "expense";
export type TransactionStatus = "pending" | "paid" | "cancelled";

export interface FinancialCategoryResponse {
  id: string;
  name: string;
  type: FinancialCategoryType;
  is_active: boolean;
  created_at: string;
}

export interface FinancialTransactionResponse {
  id: string;
  category_id: string;
  type: FinancialCategoryType;
  amount_cents: number;
  description: string;
  status: TransactionStatus;
  due_date: string | null;
  paid_at: string | null;
  notes: string | null;
  client_id: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export type KPIMetric =
  | "total_revenue"
  | "total_expenses"
  | "profit"
  | "profit_margin"
  | "average_ticket"
  | "transaction_count"
  | "active_clients";

export type KPIUnit = "cents" | "percentage" | "count";

export interface BlueprintKPI {
  key: string;
  name: string;
  description: string;
  metric: KPIMetric;
}

export type CustomFieldType = "text" | "number" | "date" | "boolean" | "select";

export interface BlueprintCustomField {
  key: string;
  label: string;
  type: CustomFieldType;
}

export interface BlueprintSuggestedCategory {
  name: string;
  type: FinancialCategoryType;
}

export interface CompanyBlueprintResponse {
  id: string;
  company_id: string;
  modules: string[];
  financial_categories: BlueprintSuggestedCategory[];
  kpis: BlueprintKPI[];
  client_custom_fields: BlueprintCustomField[];
  integrations: string[];
  ai_provider: string;
  generated_at: string;
}

export interface ClientResponse {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  notes: string | null;
  custom_fields: Record<string, string>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ClientSummaryResponse {
  client_id: string;
  total_spent_cents: number;
  purchase_count: number;
  last_purchase_at: string | null;
}

export type CatalogItemKind = "product" | "service";

export interface ProductVariantResponse {
  name: string;
  sku: string | null;
  barcode: string | null;
  price_cents: number | null;
  promo_price_cents: number | null;
  stock_quantity: number;
}

export interface CatalogItemResponse {
  id: string;
  name: string;
  description: string | null;
  price_cents: number;
  kind: CatalogItemKind;
  tracks_inventory: boolean;
  stock_quantity: number | null;
  is_active: boolean;
  sku: string | null;
  barcode: string | null;
  brand: string | null;
  supplier: string | null;
  category: string | null;
  subcategory: string | null;
  short_description: string | null;
  tags: string[];
  cost_price_cents: number | null;
  promo_price_cents: number | null;
  min_stock: number | null;
  max_stock: number | null;
  stock_location: string | null;
  images: string[];
  variants: ProductVariantResponse[];
  margin_cents: number | null;
  margin_pct: number | null;
  created_at: string;
  updated_at: string;
}

export interface EmployeeResponse {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  role_title: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MonthlyBreakdownResponse {
  year: number;
  month: number;
  revenue_cents: number;
  expense_cents: number;
  profit_cents: number;
}

export interface CategoryBreakdownResponse {
  category_id: string;
  category_name: string;
  total_cents: number;
}

export interface PeriodComparisonResponse {
  revenue_change_pct: number | null;
  expense_change_pct: number | null;
  profit_change_pct: number | null;
}

export interface ComputedKPIResponse {
  key: string;
  name: string;
  description: string;
  metric: KPIMetric;
  unit: KPIUnit;
  value: number;
}

export interface DashboardSummaryResponse {
  start: string;
  end: string;
  revenue_cents: number;
  expense_cents: number;
  profit_cents: number;
  profit_margin_pct: number | null;
  average_ticket_cents: number;
  transaction_count: number;
  active_clients: number;
  monthly_breakdown: MonthlyBreakdownResponse[];
  top_income_categories: CategoryBreakdownResponse[];
  top_expense_categories: CategoryBreakdownResponse[];
  comparison: PeriodComparisonResponse;
  kpis: ComputedKPIResponse[];
}

export type InsightKind = "highlight" | "warning" | "opportunity";

export interface InsightResponse {
  kind: InsightKind;
  title: string;
  message: string;
}

export interface InsightsResponse {
  start: string;
  end: string;
  insights: InsightResponse[];
}

export type AppointmentStatus = "scheduled" | "completed" | "cancelled" | "no_show";

export interface AppointmentResponse {
  id: string;
  company_id: string;
  title: string;
  starts_at: string;
  duration_minutes: number;
  status: AppointmentStatus;
  client_id: string | null;
  client_name: string | null;
  employee_id: string | null;
  employee_name: string | null;
  catalog_item_id: string | null;
  price_cents: number | null;
  notes: string | null;
  revenue_transaction_id: string | null;
  created_at: string;
  updated_at: string;
}

export type SignalKind =
  "stock_zero" | "stock_low" | "low_margin" | "revenue_drop" | "overdue_bills";

export type SignalSeverity = "info" | "warning" | "critical";

export interface BusinessSignalResponse {
  kind: SignalKind;
  severity: SignalSeverity;
  title: string;
  detail: string;
}

export interface SignalsResponse {
  signals: BusinessSignalResponse[];
}

export interface RecommendationsResponse {
  signals: BusinessSignalResponse[];
  recommendations: string;
}

export type ConnectionStatus = "connected" | "error";

export interface CredentialFieldResponse {
  key: string;
  label: string;
  secret: boolean;
  help_text: string | null;
}

export interface ConnectorDefinitionResponse {
  provider: string;
  name: string;
  group: string;
  description: string;
  credential_fields: CredentialFieldResponse[];
  capabilities: string[];
}

export interface ConnectionResponse {
  id: string;
  company_id: string;
  provider: string;
  status: ConnectionStatus;
  config: Record<string, string>;
  last_synced_at: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface SyncResultResponse {
  provider: string;
  imported: number;
  skipped: number;
  details: Record<string, number>;
}

export interface ApiErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

// Planos e assinatura (Etapa 29)
export type PlanTier = "starter" | "professional" | "business" | "enterprise";
export type SubscriptionStatus = "trialing" | "active" | "past_due" | "canceled";
export type BillingCycle = "monthly" | "yearly";

export interface PlanLimitsResponse {
  max_members: number;
  max_integrations: number;
  max_ai_insights_per_month: number;
  max_catalog_items: number;
}

export interface PlanResponse {
  tier: PlanTier;
  name: string;
  tagline: string;
  target_audience: string;
  price_cents_monthly: number;
  price_cents_yearly: number;
  limits: PlanLimitsResponse;
  features: string[];
  highlights: string[];
  is_contact_sales: boolean;
  badge: string | null;
}

export interface PlanCatalogResponse {
  plans: PlanResponse[];
}

export interface UsageResponse {
  members: number;
  integrations: number;
}

export interface SubscriptionResponse {
  tier: PlanTier;
  status: SubscriptionStatus;
  billing_cycle: BillingCycle;
  trial_ends_at: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  features: string[];
  limits: PlanLimitsResponse;
  usage: UsageResponse;
}

export interface ChangePlanRequest {
  tier: PlanTier;
  billing_cycle?: BillingCycle;
  start_trial?: boolean;
}

// Painel administrativo do SaaS (Etapa 30)
export interface AdminRevenueMetrics {
  mrr_cents: number;
  arr_cents: number;
  active_paying: number;
  trials: number;
  platform_gmv_cents: number;
  platform_expenses_cents: number;
}

export interface AdminCustomerMetrics {
  total_companies: number;
  active_companies: number;
  inactive_companies: number;
  new_this_month: number;
  churned: number;
  churn_rate_pct: number;
}

export interface AdminSegmentMetric {
  segment: string;
  company_count: number;
}

export interface AdminPlanBreakdown {
  tier: PlanTier;
  subscribers: number;
  mrr_cents: number;
}

export interface AdminSubscriptionMetrics {
  by_status: Record<string, number>;
  by_plan: AdminPlanBreakdown[];
  past_due: number;
}

export interface AdminSystemMetrics {
  total_users: number;
  total_companies: number;
  total_connections: number;
  connections_with_error: number;
}

export interface AdminOverviewResponse {
  revenue: AdminRevenueMetrics;
  customers: AdminCustomerMetrics;
  segments: AdminSegmentMetric[];
  subscriptions: AdminSubscriptionMetrics;
  system: AdminSystemMetrics;
}
