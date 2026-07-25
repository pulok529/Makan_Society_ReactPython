import { PaginatedResponse } from "./pagination";

export type UserProfile = {
  id: number;
  username: string;
  login_name: string;
  email: string | null;
  is_active: boolean;
  permissions: string[];
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type Category = {
  id: number;
  name: string;
  code: string | null;
  is_active: boolean;
};

export type Package = {
  id: number;
  package_code: string;
  category_id: number;
  category_name: string;
  name: string;
  package_type: string | null;
  default_price: number;
  is_active: boolean;
  created_at: string;
};

export type MemberListItem = {
  id: number;
  member_code: string;
  full_name: string;
  plot_no: string | null;
  plot_count: number;
  cell_no: string | null;
  category_id: number | null;
  category_name: string | null;
  joined_on: string | null;
  is_active: boolean;
};

export type MemberSearchItem = {
  id: number;
  member_code: string;
  full_name: string;
  plot_no: string | null;
  plot_count: number;
  cell_no: string | null;
  category_name: string | null;
  is_active: boolean;
};

export type MemberInformationSummary = {
  member_code: string;
  full_name: string;
  plot_no: string | null;
  plot_count: number;
  category_name: string | null;
  national_id: string | null;
  cell_no: string | null;
  email: string | null;
  member_class: string | null;
  joined_on: string | null;
  is_active: boolean;
  father_name: string | null;
  mother_name: string | null;
  present_address: string | null;
  permanent_address: string | null;
  reference: string | null;
  nominee_name: string | null;
  nominee_cell: string | null;
  total_collection_amount: number;
  total_due_amount: number;
};

export type MemberPackageAssignment = {
  id: number;
  package_id: number;
  package_name: string;
  assigned_on: string;
  ended_on: string | null;
  is_active: boolean;
};

export type MemberDetail = {
  id: number;
  member_code: string;
  member_id_text: string | null;
  plot_no: string | null;
  plot_count: number;
  full_name: string;
  father_name: string | null;
  mother_name: string | null;
  present_address: string | null;
  permanent_address: string | null;
  cell_no: string | null;
  email: string | null;
  reference: string | null;
  national_id: string | null;
  category_id: number | null;
  category_name: string | null;
  member_class: string | null;
  joined_on: string | null;
  is_active: boolean;
  created_at: string;
  entry_at: string;
  nominee_name: string | null;
  nominee_cell: string | null;
  packages: MemberPackageAssignment[];
};

export type BillingPeriod = {
  id: number;
  year: number;
  month: number;
  period_name: string;
  starts_on: string;
  ends_on: string;
  is_closed: boolean;
};

export type ChargeItem = {
  id: number;
  package_id: number | null;
  package_name: string | null;
  item_type: string;
  description: string | null;
  quantity: number;
  unit_amount: number;
  line_amount: number;
};

export type Charge = {
  id: number;
  member_id: number;
  member_name: string;
  member_code: string;
  billing_period_id: number | null;
  billing_period_name: string | null;
  charge_type: string;
  status: string;
  total_amount: number;
  discount_amount: number;
  net_amount: number;
  due_amount: number;
  created_at: string;
  items: ChargeItem[];
};

export type ReceiptLine = {
  id: number;
  charge_id: number | null;
  charge_item_id: number | null;
  line_type: string;
  amount: number;
};

export type Receipt = {
  id: number;
  receipt_no: string;
  member_id: number | null;
  member_name: string | null;
  collected_by_user_id: number | null;
  receipt_type: string;
  payment_date: string;
  subtotal_amount: number;
  discount_amount: number;
  total_amount: number;
  notes: string | null;
  created_at: string;
  lines: ReceiptLine[];
};

export type BillingDashboard = {
  total_members_with_due: number;
  total_due_amount: number;
  total_open_charges: number;
  total_receipts: number;
  total_collection_amount: number;
};

export type BillingMemberSummary = {
  member_id: number;
  member_code: string;
  member_name: string;
  total_charged: number;
  total_due: number;
  open_charge_count: number;
};

export type BillingHead = {
  id: number;
  head_name: string;
  head_type: "Period" | "OneTime";
  billing_mode: "Mandatory" | "Optional";
  fee_amount: number;
  effective_from_month: number | null;
  effective_from_year: number | null;
  effective_from_date: string | null;
  effective_to_date: string | null;
  is_active: boolean;
  created_at: string;
  created_by: number | null;
};

export type BillingHeadMapping = {
  id: number;
  billing_head_id: number;
  billing_head_name: string;
  coa_id: number;
  coa_name: string;
  is_active: boolean;
  created_at: string;
  created_by: number | null;
};

export type BillingDueLine = {
  member_id: number;
  billing_head_id: number;
  head_name: string;
  head_type: string;
  billing_mode: "Mandatory" | "Optional";
  period_date: string | null;
  period_display: string | null;
  plot_count: number;
  base_fee_amount: number;
  fee_amount: number;
  paid_amount: number;
  due_amount: number;
  coa_id_snapshot: number | null;
};

export type BillingInvoice = {
  id: number;
  invoice_no: string;
  member_id: number;
  member_code: string;
  member_name: string;
  plot_no: string | null;
  invoice_date: string;
  subtotal_amount: number;
  discount_amount: number;
  net_amount: number;
  total_receive_amount: number;
  total_due_amount: number;
  is_cancelled: boolean;
  cancel_reason: string | null;
  created_at: string;
  details: {
    id: number;
    head_name_snapshot: string;
    period_display: string | null;
    fee_amount: number;
    receive_amount: number;
    due_amount: number;
    income_voucher_id?: number | null;
    is_income_transferred: boolean;
  }[];
};

export type Account = {
  id: number;
  code: string;
  name: string;
  account_type: string;
  is_active: boolean;
};

export type AccountingEntry = {
  id: number;
  account_id: number | null;
  account_name: string | null;
  entry_type: string;
  amount: number;
  remarks: string | null;
  created_at: string;
};

export type AccountingMasterEntry = {
  id: number;
  coa_id: number;
  coa_name: string | null;
  amount: number;
  remarks: string | null;
  created_at: string;
  income_date?: string;
  expense_date?: string;
};

export type AccountingSummary = {
  total_income: number;
  total_expense: number;
  net_balance: number;
};

export type AccountingVoucher = {
  id: number;
  voucher_no: string;
  voucher_type: "income" | "expense";
  voucher_date: string;
  total_amount: number;
  remarks: string | null;
  created_at: string;
  created_by: number | null;
  lines: {
    id: number;
    coa_id: number;
    coa_name: string | null;
    amount: number;
    remarks: string | null;
  }[];
};

export type DataTableTotals = Record<string, number>;

export type DataTableResponse<T> = {
  draw: number;
  recordsTotal: number;
  recordsFiltered: number;
  data: T[];
  totals?: DataTableTotals;
  mode?: string;
};

export type BillingChargeTableRow = {
  id: number;
  member_name: string;
  member_code: string;
  plot_no: string | null;
  created_at: string;
  billing_period_name: string | null;
  head_summary: string;
  net_amount: number;
  paid_amount: number;
  due_amount: number;
  status: string;
};

export type BillingReceiptTableRow = {
  id: number;
  receipt_no: string;
  member_name: string | null;
  member_code: string | null;
  plot_no: string | null;
  payment_date: string;
  total_amount: number;
  notes: string | null;
};

export type BillingInvoiceTableRow = {
  id: number;
  invoice_no: string;
  invoice_date: string;
  subtotal_amount: number;
  discount_amount: number;
  total_receive_amount: number;
  total_due_amount: number;
  status: string;
};

export type AccountingTransactionTableRow = {
  id: number;
  reference_no: string;
  transaction_date: string;
  head_name: string;
  amount: number;
  remarks: string | null;
  line_count: number;
  is_voucher: boolean;
};

export type IncomeTransferPendingItem = {
  billing_detail_id: number;
  invoice_no: string;
  member_name: string;
  coa_id: number;
  amount: number;
  head_name: string;
  period_display: string | null;
};

export type SmsTemplate = {
  id: number;
  name: string;
  body: string;
  template_type: string | null;
};

export type SmsMessage = {
  id: number;
  member_id: number | null;
  member_name: string | null;
  template_id: number | null;
  template_name: string | null;
  recipient: string;
  message_body: string;
  status: string;
  created_at: string;
  sent_at: string | null;
};

export type SmsAttempt = {
  id: number;
  sms_message_id: number;
  provider_name: string | null;
  provider_message_id: string | null;
  provider_status: string | null;
  error_detail: string | null;
  attempted_at: string;
};

export type SmsMessagePage = PaginatedResponse<SmsMessage>;
export type SmsAttemptPage = PaginatedResponse<SmsAttempt>;
export type MemberPage = PaginatedResponse<MemberListItem>;

export type SmsIntegrationStatus = {
  provider_mode: string;
  provider_name: string;
  provider_configured: boolean;
  external_status_check_supported: boolean;
  provider_check_ok: boolean | null;
  provider_check_message: string | null;
  template_count: number;
  message_count: number;
  sent_count: number;
  attempt_count: number;
};

export type SmsProviderCheck = {
  provider_name: string;
  provider_configured: boolean;
  ok: boolean;
  status_code: number | null;
  message: string;
  response_sample: string | null;
};

export type SmsProviderMode = "simulated" | "bulksmsbd";

export type AuthState = "checking" | "guest" | "authenticated";
export type WorkspaceTab =
  | "dashboard"
  | "profile"
  | "categories"
  | "packages"
  | "members"
  | "billing-heads-view"
  | "billing-heads-entry"
  | "billing-mappings-view"
  | "billing-mappings-entry"
  | "billing"
  | "billing-registers"
  | "coa-view"
  | "coa-entry"
  | "income-view"
  | "income-entry"
  | "expense-view"
  | "expense-entry"
  | "reports"
  | "messaging";

export type NavItem = {
  key: WorkspaceTab;
  label: string;
  icon: string;
  badge?: string;
  group?: string;
};

export type ThemeMode = "light" | "dark";
export type LayoutMode = "fluid" | "detached";
export type MenuColor = "brand" | "dark" | "light";
export type TopbarColor = "light" | "dark" | "brand";
export type SidenavSize = "default" | "compact" | "condensed" | "sm-hover" | "sm-hover-active" | "full" | "fullscreen";
export type ThemeSettings = {
  themeMode: ThemeMode;
  layoutMode: LayoutMode;
  menuColor: MenuColor;
  topbarColor: TopbarColor;
  sidenavSize: SidenavSize;
};


