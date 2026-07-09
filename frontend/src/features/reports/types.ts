export type IncomeExpenseComparisonReport = {
  from_date: string | null;
  to_date: string | null;
  income: { rows: Record<string, string | number | null>[]; subtotal: number };
  expense: { rows: Record<string, string | number | null>[]; subtotal: number };
  net_amount: number;
};

export type ReportEnvelope = {
  report_type: string;
  title: string;
  generated_at: string;
  row_count: number;
  totals: Record<string, number | string>;
  applied_filters: Record<string, string>;
  rows: Record<string, unknown>[];
};

export type PagedReportEnvelope = {
  report_type: string;
  title: string;
  generated_at: string;
  total: number;
  limit: number;
  offset: number;
  totals: Record<string, number | string>;
  applied_filters: Record<string, string>;
  items: Record<string, unknown>[];
};

export type SingleMemberStatementReport = {
  member_id: number;
  member_code: string;
  member_name: string;
  plot_no: string | null;
  total_bill: number;
  paid_amount: number;
  due_amount: number;
  applied_filters: Record<string, string>;
  due_history: {
    head_name: string;
    period_display: string | null;
    total_bill: number;
    paid_amount: number;
    due_amount: number;
  }[];
  payment_history: {
    receipt_no: string;
    payment_date: string;
    amount: number;
    discount_amount: number;
    notes: string | null;
  }[];
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

export type MemberInformationDetailReport = {
  member_id: number;
  applied_filters: Record<string, string>;
  member_info: MemberInformationSummary;
  payment_history: SingleMemberStatementReport["payment_history"];
  due_history: SingleMemberStatementReport["due_history"];
  sms_history: {
    created_at: string;
    recipient: string;
    template_name: string | null;
    message_body: string;
    status: string;
  }[];
};

export type ReceiptDetailReport = {
  receipt_id: number;
  receipt_no: string;
  payment_date: string;
  member_name: string | null;
  member_code: string | null;
  subtotal_amount: number;
  discount_amount: number;
  total_amount: number;
  applied_filters: Record<string, string>;
  lines: { line_type: string; amount: number; charge_id: number | null }[];
};

export type TableReportType =
  | "due-members"
  | "collections"
  | "income-detail"
  | "expense-detail"
  | "charges"
  | "members"
  | "total-collection"
  | "total-due";

export const TABLE_REPORT_TYPES = new Set<TableReportType>([
  "due-members",
  "collections",
  "income-detail",
  "expense-detail",
  "charges",
  "members",
  "total-collection",
  "total-due",
]);
