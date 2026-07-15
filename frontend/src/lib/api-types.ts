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
  is_active: boolean;
  created_at: string;
  updated_at: string;
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

export interface ApiErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}
