import { apiRequest } from "../../shared/api/client";
import {
  IncomeExpenseComparisonReport,
  MemberInformationDetailReport,
  PagedReportEnvelope,
  ReceiptDetailReport,
  ReportEnvelope,
  SingleMemberStatementReport,
  TableReportType,
} from "./types";

const tableReportPathMap: Record<TableReportType, string> = {
  "due-members": "/api/reports/due-members",
  collections: "/api/reports/collections",
  "income-detail": "/api/reports/income-detail",
  "expense-detail": "/api/reports/expense-detail",
  charges: "/api/reports/charges",
  members: "/api/reports/members",
  "electricity-collection": "/api/reports/electricity-collection",
  "total-collection": "/api/reports/total-collection",
  "total-due": "/api/reports/total-due",
};

function withQuery(path: string, params: URLSearchParams | string) {
  const query = typeof params === "string" ? params : params.toString();
  return query ? `${path}?${query}` : path;
}

export function loadIncomeExpenseReport(accessToken: string, query: URLSearchParams | string) {
  return apiRequest<IncomeExpenseComparisonReport>(withQuery("/api/accounting/income-expense-report", query), accessToken);
}

export function loadReceiptDetailReport(accessToken: string, receiptId: string | number) {
  return apiRequest<ReceiptDetailReport>(`/api/reports/receipt/${receiptId}`, accessToken);
}

export function loadMemberStatementReport(accessToken: string, query: URLSearchParams | string) {
  return apiRequest<SingleMemberStatementReport>(withQuery("/api/reports/member-statement", query), accessToken);
}

export function loadMemberInformationDetailReport(accessToken: string, query: URLSearchParams | string) {
  return apiRequest<MemberInformationDetailReport>(withQuery("/api/reports/member-information-detail", query), accessToken);
}

export function loadTableReport(accessToken: string, reportType: TableReportType, query: URLSearchParams | string) {
  return apiRequest<ReportEnvelope>(withQuery(tableReportPathMap[reportType], query), accessToken);
}

export function loadPagedTableReport(
  accessToken: string,
  reportType: TableReportType,
  query: URLSearchParams | string,
  pagination: { limit: number; offset: number },
) {
  const params = new URLSearchParams(typeof query === "string" ? query : query.toString());
  params.set("limit", String(pagination.limit));
  params.set("offset", String(pagination.offset));
  return apiRequest<PagedReportEnvelope>(`/api/reports/paged/${reportType}?${params.toString()}`, accessToken);
}
