import { ReactNode } from "react";

import {
  IncomeExpenseComparisonReport,
  MemberInformationDetailReport,
  PagedReportEnvelope,
  ReceiptDetailReport,
  ReportEnvelope,
  SingleMemberStatementReport,
} from "./types";

type Formatters = {
  money: (value: number | null | undefined) => string;
  shortDate: (value: string | null | undefined) => string;
};

type ReportViewerContentProps = Formatters & {
  currentReport: ReportEnvelope | null;
  currentPagedReport: PagedReportEnvelope | null;
  incomeExpenseReport: IncomeExpenseComparisonReport | null;
  receiptReport: ReceiptDetailReport | null;
  memberStatementReport: SingleMemberStatementReport | null;
  memberInformationDetailReport: MemberInformationDetailReport | null;
  reportViewerPage: number;
  onReportViewerPageChange: (page: number) => void;
  emptyState: ReactNode;
};

type PrintMarkupProps = Formatters & {
  currentReport: ReportEnvelope | null;
  currentPagedReport: PagedReportEnvelope | null;
  incomeExpenseReport: IncomeExpenseComparisonReport | null;
  receiptReport: ReceiptDetailReport | null;
  memberStatementReport: SingleMemberStatementReport | null;
  memberInformationDetailReport: MemberInformationDetailReport | null;
  reportViewerPage: number;
};

function formatReportCell(key: string, value: unknown, money: Formatters["money"], shortDate: Formatters["shortDate"]) {
  if (value === null || value === undefined || value === "") return "";
  const lowerKey = key.toLowerCase();
  if (
    typeof value === "number" &&
    ["amount", "bill", "paid", "due", "collection", "discount", "subtotal", "total", "net"].some((token) => lowerKey.includes(token))
  ) {
    return money(value);
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }
  if (typeof value === "string" && lowerKey.includes("date") && /^\d{4}-\d{2}-\d{2}/.test(value)) {
    return shortDate(value);
  }
  return String(value);
}

function escapePrintHtml(value: unknown) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderAppliedFilterCards(filters: Record<string, string>) {
  const entries = Object.entries(filters ?? {}).filter(([, value]) => String(value ?? "").trim() !== "");
  if (entries.length === 0) return null;

  return (
    <div className="report-filter-grid mt-3">
      {entries.map(([key, value]) => (
        <div className="report-meta-card" key={`special-filter-${key}`}>
          <span className="text-muted d-block text-capitalize">{key.replace(/_/g, " ")}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </div>
  );
}

function renderReceiptReportContent(report: ReceiptDetailReport, { money, shortDate }: Formatters) {
  return (
    <div className="report-sheet">
      <div className="report-sheet-header">
        <img src="/makan-logo-3.png" alt="Darul Mohan Plot Owners Society" className="report-header-logo" />
        <div className="d-flex justify-content-between gap-3">
          <div>
            <div className="fw-semibold">Money Receipt Detail</div>
            <div className="text-muted">Makan Society</div>
          </div>
          <div className="text-end">
            <h3 className="invoice-report-title mb-1">Receipt</h3>
            <div className="fw-semibold">{report.receipt_no}</div>
          </div>
        </div>
      </div>
      <div className="report-summary-grid">
        {[
          ["Member Name", report.member_name ?? "Unknown"],
          ["Member Code", report.member_code ?? "Unknown"],
          ["Payment Date", shortDate(report.payment_date)],
          ["Subtotal", money(report.subtotal_amount)],
          ["Discount", money(report.discount_amount)],
          ["Collected", money(report.total_amount)],
        ].map(([label, value]) => (
          <div className="statement-summary-card" key={label}>
            <span className="text-muted d-block">{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      {renderAppliedFilterCards(report.applied_filters)}
      <div className="table-responsive">
        <table className="table table-bordered invoice-report-table mb-0">
          <thead>
            <tr>
              <th>Line Type</th>
              <th>Charge ID</th>
              <th className="text-end">Amount</th>
            </tr>
          </thead>
          <tbody>
            {report.lines.map((line, index) => (
              <tr key={`${line.charge_id ?? "line"}-${index}`}>
                <td>{line.line_type}</td>
                <td>{line.charge_id ?? "N/A"}</td>
                <td className="text-end">{money(line.amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function renderIncomeExpenseReportContent(report: IncomeExpenseComparisonReport, { money }: Formatters) {
  return (
    <div className="report-sheet">
      <div className="report-sheet-header">
        <img src="/makan-logo-3.png" alt="Darul Mohan Plot Owners Society" className="report-header-logo" />
        <div className="d-flex justify-content-between gap-3">
          <div>
            <div className="fw-semibold">Income And Expense Statement</div>
            <div className="text-muted">Makan Society</div>
          </div>
          <div className="text-end">
            <h3 className="invoice-report-title mb-1">Summary</h3>
            <div className="text-muted">{report.from_date ?? "Start"} to {report.to_date ?? "Today"}</div>
          </div>
        </div>
      </div>
      <div className="row g-3">
        {(["income", "expense"] as const).map((section) => {
          const data = report[section];
          return (
            <div className="col-xl-6" key={section}>
              <div className={section === "income" ? "report-panel income" : "report-panel expense"}>
                <h5 className="text-capitalize">{section}</h5>
                <table className="table table-bordered table-sm mb-0">
                  <thead>
                    <tr>
                      <th>COA</th>
                      <th className="text-end">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.rows.map((row, index) => (
                      <tr key={`${section}-${index}`}>
                        <td>{String(row.coa_name ?? "")}</td>
                        <td className="text-end">{money(Number(row.amount ?? 0))}</td>
                      </tr>
                    ))}
                    <tr className="fw-bold">
                      <td>Subtotal</td>
                      <td className="text-end">{money(data.subtotal)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          );
        })}
      </div>
      {renderAppliedFilterCards(
        Object.fromEntries(
          [
            report.from_date ? ["from_date", report.from_date] : null,
            report.to_date ? ["to_date", report.to_date] : null,
          ].filter((entry): entry is [string, string] => entry !== null),
        ),
      )}
      <div className={report.net_amount >= 0 ? "net-banner positive" : "net-banner negative"}>
        <span>Net Income - Expense</span>
        <strong>{money(report.net_amount)}</strong>
      </div>
    </div>
  );
}

function renderMemberStatementReportContent(report: SingleMemberStatementReport, { money, shortDate }: Formatters, emptyState: ReactNode) {
  return (
    <div className="report-sheet">
      <div className="report-sheet-header">
        <img src="/makan-logo-3.png" alt="Darul Mohan Plot Owners Society" className="report-header-logo" />
        <div className="d-flex justify-content-between gap-3">
          <div>
            <div className="fw-semibold">Single Member Due And Paid Statement</div>
            <div className="text-muted">Makan Society</div>
          </div>
          <div className="text-end">
            <h3 className="invoice-report-title mb-1">{report.member_code}</h3>
            <div>{report.member_name}</div>
            {report.plot_no ? <div className="text-muted">Plot No: {report.plot_no}</div> : null}
          </div>
        </div>
      </div>
      <div className="report-summary-grid">
        <div className="statement-summary-card">
          <span className="text-muted d-block">Total Paid</span>
          <strong>{money(report.paid_amount)}</strong>
        </div>
        <div className="statement-summary-card highlight">
          <span className="text-muted d-block">Outstanding Due</span>
          <strong>{money(report.due_amount)}</strong>
        </div>
        <div className="statement-summary-card highlight">
          <span className="text-muted d-block">Outstanding Bill Total</span>
          <strong>{money(report.total_bill)}</strong>
        </div>
      </div>
      {renderAppliedFilterCards(report.applied_filters)}
      <div className="row g-3 mt-1">
        <div className="col-xl-6">
          <div className="card mb-0">
            <div className="card-header"><h5 className="mb-0">Payment History</h5></div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-bordered table-sm mb-0">
                  <thead>
                    <tr>
                      <th>Receipt No</th>
                      <th>Date</th>
                      <th className="text-end">Paid</th>
                      <th className="text-end">Discount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.payment_history.map((item) => (
                      <tr key={item.receipt_no}>
                        <td>{item.receipt_no}</td>
                        <td>{shortDate(item.payment_date)}</td>
                        <td className="text-end">{money(item.amount)}</td>
                        <td className="text-end">{money(item.discount_amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {report.payment_history.length === 0 ? emptyState : null}
              </div>
            </div>
          </div>
        </div>
        <div className="col-xl-6">
          <div className="card mb-0">
            <div className="card-header"><h5 className="mb-0">Outstanding Dues By Period</h5></div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-bordered table-sm mb-0">
                  <thead>
                    <tr>
                      <th>Billing Head</th>
                      <th>Period</th>
                      <th className="text-end">Bill</th>
                      <th className="text-end">Paid</th>
                      <th className="text-end">Due</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.due_history.map((item, index) => (
                      <tr key={`${item.head_name}-${item.period_display ?? "one-time"}-${index}`}>
                        <td>{item.head_name}</td>
                        <td>{item.period_display ?? "One Time"}</td>
                        <td className="text-end">{money(item.total_bill)}</td>
                        <td className="text-end">{money(item.paid_amount)}</td>
                        <td className="text-end">{money(item.due_amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {report.due_history.length === 0 ? emptyState : null}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function renderMemberInformationDetailReportContent(
  report: MemberInformationDetailReport,
  { money, shortDate }: Formatters,
  emptyState: ReactNode,
) {
  const info = report.member_info;
  return (
    <div className="report-sheet">
      <div className="report-sheet-header">
        <img src="/makan-logo-3.png" alt="Darul Mohan Plot Owners Society" className="report-header-logo" />
        <div className="d-flex justify-content-between gap-3">
          <div>
            <div className="fw-semibold">Member Information Detail</div>
            <div className="text-muted">Makan Society</div>
          </div>
          <div className="text-end">
            <h3 className="invoice-report-title mb-1">{info.member_code}</h3>
            <div>{info.full_name}</div>
            {info.plot_no ? <div className="text-muted">Plot No: {info.plot_no}</div> : null}
          </div>
        </div>
      </div>
      {renderAppliedFilterCards(report.applied_filters)}
      <div className="row g-3">
        <div className="col-xl-6">
          <div className="card mb-0">
            <div className="card-header"><h5 className="mb-0">Member Information</h5></div>
            <div className="card-body">
              <div className="row g-3">
                {[
                  ["Member Code", info.member_code],
                  ["Full Name", info.full_name],
                  ["Plot No", info.plot_no ?? "N/A"],
                  ["Category", info.category_name ?? "N/A"],
                  ["National ID", info.national_id ?? "N/A"],
                  ["Phone", info.cell_no ?? "N/A"],
                  ["Email", info.email ?? "N/A"],
                  ["Member Class", info.member_class ?? "N/A"],
                  ["Plot Count", String(info.plot_count ?? 1)],
                  ["Joined On", info.joined_on ? shortDate(info.joined_on) : "N/A"],
                  ["Status", info.is_active ? "Active" : "Inactive"],
                  ["Father Name", info.father_name ?? "N/A"],
                  ["Mother Name", info.mother_name ?? "N/A"],
                  ["Present Address", info.present_address ?? "N/A"],
                  ["Permanent Address", info.permanent_address ?? "N/A"],
                  ["Reference", info.reference ?? "N/A"],
                  ["Nominee Name", info.nominee_name ?? "N/A"],
                  ["Nominee Cell", info.nominee_cell ?? "N/A"],
                  ["Total Collection", money(info.total_collection_amount)],
                  ["Total Due", money(info.total_due_amount)],
                ].map(([label, value]) => (
                  <div className="col-md-6" key={String(label)}>
                    <div className="report-meta-card h-100">
                      <span className="text-muted d-block">{label}</span>
                      <strong>{value}</strong>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
        <div className="col-xl-6">
          <div className="card mb-0">
            <div className="card-header"><h5 className="mb-0">Payment History</h5></div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-bordered table-sm mb-0">
                  <thead>
                    <tr>
                      <th>Receipt No</th>
                      <th>Date</th>
                      <th className="text-end">Paid</th>
                      <th className="text-end">Discount</th>
                      <th>Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.payment_history.map((item) => (
                      <tr key={item.receipt_no}>
                        <td>{item.receipt_no}</td>
                        <td>{shortDate(item.payment_date)}</td>
                        <td className="text-end">{money(item.amount)}</td>
                        <td className="text-end">{money(item.discount_amount)}</td>
                        <td>{item.notes ?? "N/A"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {report.payment_history.length === 0 ? emptyState : null}
              </div>
            </div>
          </div>
        </div>
        <div className="col-xl-6">
          <div className="card mb-0">
            <div className="card-header"><h5 className="mb-0">Due List</h5></div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-bordered table-sm mb-0">
                  <thead>
                    <tr>
                      <th>Billing Head</th>
                      <th>Period</th>
                      <th className="text-end">Bill</th>
                      <th className="text-end">Paid</th>
                      <th className="text-end">Due</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.due_history.map((item, index) => (
                      <tr key={`${item.head_name}-${item.period_display ?? "one-time"}-${index}`}>
                        <td>{item.head_name}</td>
                        <td>{item.period_display ?? "One Time"}</td>
                        <td className="text-end">{money(item.total_bill)}</td>
                        <td className="text-end">{money(item.paid_amount)}</td>
                        <td className="text-end">{money(item.due_amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {report.due_history.length === 0 ? emptyState : null}
              </div>
            </div>
          </div>
        </div>
        <div className="col-xl-6">
          <div className="card mb-0">
            <div className="card-header"><h5 className="mb-0">SMS History</h5></div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-bordered table-sm mb-0">
                  <thead>
                    <tr>
                      <th>Created</th>
                      <th>Recipient</th>
                      <th>Template</th>
                      <th>Message</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.sms_history.map((item, index) => (
                      <tr key={`${item.recipient}-${item.created_at}-${index}`}>
                        <td>{shortDate(item.created_at)}</td>
                        <td>{item.recipient}</td>
                        <td>{item.template_name ?? "N/A"}</td>
                        <td>{item.message_body}</td>
                        <td>{item.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {report.sms_history.length === 0 ? emptyState : null}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function renderTableReportContent(
  report: ReportEnvelope | PagedReportEnvelope,
  options: Formatters & {
    reportViewerPage: number;
    onReportViewerPageChange: (page: number) => void;
    emptyState: ReactNode;
  },
) {
  const isPaged = "items" in report;
  const rows = isPaged ? report.items : report.rows;
  const columns = rows.length > 0 ? Object.keys(rows[0]) : [];
  const pageSize = isPaged ? report.limit : 15;
  const totalRows = isPaged ? report.total : report.row_count;
  const activePage = isPaged ? Math.max(1, Math.floor(report.offset / Math.max(report.limit, 1)) + 1) : Math.min(options.reportViewerPage, Math.max(1, Math.ceil(totalRows / pageSize)));
  const pageRows = isPaged ? rows : rows.slice((activePage - 1) * pageSize, (activePage - 1) * pageSize + pageSize);
  const totalPages = Math.max(1, Math.ceil(totalRows / pageSize));
  const startIndex = isPaged ? report.offset : (activePage - 1) * pageSize;

  return (
    <div className="report-sheet">
      <div className="report-sheet-header">
        <img src="/makan-logo-3.png" alt="Darul Mohan Plot Owners Society" className="report-header-logo" />
        <div className="d-flex justify-content-between gap-3">
          <div>
            <div className="fw-semibold">Report Viewer</div>
            <div className="text-muted">Makan Society</div>
          </div>
          <div className="text-end">
            <h3 className="invoice-report-title mb-1">{report.title}</h3>
            <div className="text-muted">Generated {options.shortDate(report.generated_at)}</div>
          </div>
        </div>
      </div>
      <div className="report-filter-grid">
        <div className="report-meta-card">
          <span className="text-muted d-block">Report Type</span>
          <strong>{report.report_type}</strong>
        </div>
        <div className="report-meta-card">
          <span className="text-muted d-block">Rows</span>
          <strong>{totalRows}</strong>
        </div>
        <div className="report-meta-card">
          <span className="text-muted d-block">Page</span>
          <strong>{activePage} / {totalPages}</strong>
        </div>
        {Object.entries(report.applied_filters ?? {}).map(([key, value]) => (
          <div className="report-meta-card" key={`filter-${key}`}>
            <span className="text-muted d-block text-capitalize">{key.replace(/_/g, " ")}</span>
            <strong>{value}</strong>
          </div>
        ))}
        {Object.entries(report.totals).map(([key, value]) => (
          <div className="report-meta-card" key={key}>
            <span className="text-muted d-block text-capitalize">{key.replace(/_/g, " ")}</span>
            <strong>{formatReportCell(key, value, options.money, options.shortDate)}</strong>
          </div>
        ))}
      </div>
      <div className="table-responsive">
        {rows.length > 0 ? (
          <table className="table table-bordered invoice-report-table mb-0">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column}>{column.replace(/_/g, " ")}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pageRows.map((row, index) => (
                <tr key={`${report.report_type}-${startIndex + index}`}>
                  {columns.map((column) => (
                    <td
                      className={["amount", "bill", "paid", "due", "collection", "discount", "subtotal", "total", "net"].some((token) => column.toLowerCase().includes(token)) ? "text-end" : ""}
                      key={`${report.report_type}-${startIndex + index}-${column}`}
                    >
                      {formatReportCell(column, row[column], options.money, options.shortDate)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          options.emptyState
        )}
      </div>
      {totalRows > pageSize ? (
        <div className="report-pagination-bar">
          <div className="report-pagination-summary">
            Showing {Math.min(startIndex + 1, totalRows)}-{Math.min(startIndex + pageRows.length, totalRows)} of {totalRows}
          </div>
          <div className="report-pagination-controls">
            <button
              className="btn btn-outline-secondary btn-sm"
              disabled={activePage <= 1}
              onClick={() => options.onReportViewerPageChange(Math.max(1, activePage - 1))}
              type="button"
            >
              Previous
            </button>
            <span className="report-pagination-current">Page {activePage} of {totalPages}</span>
            <button
              className="btn btn-outline-secondary btn-sm"
              disabled={activePage >= totalPages}
              onClick={() => options.onReportViewerPageChange(Math.min(totalPages, activePage + 1))}
              type="button"
            >
              Next
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function ReportViewerContent(props: ReportViewerContentProps) {
  if (props.memberInformationDetailReport) {
    return renderMemberInformationDetailReportContent(props.memberInformationDetailReport, props, props.emptyState);
  }
  if (props.memberStatementReport) {
    return renderMemberStatementReportContent(props.memberStatementReport, props, props.emptyState);
  }
  if (props.receiptReport) return renderReceiptReportContent(props.receiptReport, props);
  if (props.incomeExpenseReport) return renderIncomeExpenseReportContent(props.incomeExpenseReport, props);
  if (props.currentPagedReport) {
    return renderTableReportContent(props.currentPagedReport, props);
  }
  if (props.currentReport) return renderTableReportContent(props.currentReport, props);
  return <>{props.emptyState}</>;
}

export function reportViewerTitle(props: Omit<ReportViewerContentProps, "emptyState" | "onReportViewerPageChange">) {
  if (props.memberStatementReport) return `Member Statement - ${props.memberStatementReport.member_code}`;
  if (props.memberInformationDetailReport) return `Member Detail - ${props.memberInformationDetailReport.member_info.member_code}`;
  if (props.receiptReport) return `Receipt Detail - ${props.receiptReport.receipt_no}`;
  if (props.incomeExpenseReport) return "Income And Expense Report";
  if (props.currentPagedReport) return props.currentPagedReport.title;
  if (props.currentReport) return props.currentReport.title;
  return "Report Viewer";
}

export function reportViewerSubtitle(props: Omit<ReportViewerContentProps, "emptyState" | "onReportViewerPageChange">) {
  if (props.memberStatementReport) {
    return `${props.memberStatementReport.member_name}${props.memberStatementReport.plot_no ? ` | Plot ${props.memberStatementReport.plot_no}` : ""}`;
  }
  if (props.memberInformationDetailReport) {
    return `${props.memberInformationDetailReport.member_info.full_name}${props.memberInformationDetailReport.member_info.plot_no ? ` | Plot ${props.memberInformationDetailReport.member_info.plot_no}` : ""}`;
  }
  if (props.receiptReport) return props.shortDate(props.receiptReport.payment_date);
  if (props.incomeExpenseReport) return `${props.incomeExpenseReport.from_date ?? "Start"} to ${props.incomeExpenseReport.to_date ?? "Today"}`;
  if (props.currentPagedReport) return `${props.currentPagedReport.total} row${props.currentPagedReport.total === 1 ? "" : "s"} available`;
  if (props.currentReport) return `${props.currentReport.row_count} row${props.currentReport.row_count === 1 ? "" : "s"} generated`;
  return "";
}

function buildPaginatedTableReportMarkup(
  report: ReportEnvelope | PagedReportEnvelope,
  reportViewerPage: number,
  money: Formatters["money"],
  shortDate: Formatters["shortDate"],
) {
  const isPaged = "items" in report;
  const rows = isPaged ? report.items : report.rows;
  const columns = rows.length > 0 ? Object.keys(rows[0]) : [];
  const pageSize = isPaged ? report.limit : 15;
  const totalRows = isPaged ? report.total : report.row_count;
  const activePage = isPaged ? Math.max(1, Math.floor(report.offset / Math.max(report.limit, 1)) + 1) : Math.min(reportViewerPage, Math.max(1, Math.ceil(totalRows / pageSize)));
  const totalPages = Math.max(1, Math.ceil(totalRows / pageSize));
  const startIndex = isPaged ? report.offset : (activePage - 1) * pageSize;
  const pageRows = isPaged ? rows : rows.slice(startIndex, startIndex + pageSize);

  return `
    <main class="sheet report-sheet">
      <section class="report-sheet-header">
        <img class="report-logo" src="/makan-logo-3.png" alt="Darul Mohan Plot Owners Society" />
        <div class="page-head">
          <div>
            <div class="section-title">Report Viewer</div>
            <div class="text-muted">Makan Society</div>
          </div>
          <div class="right">
            <h1 class="report-title">${escapePrintHtml(report.title)}</h1>
            <div class="text-muted">Generated ${escapePrintHtml(shortDate(report.generated_at))}</div>
            <div class="page-number">Page ${activePage} of ${totalPages}</div>
          </div>
        </div>
        <div class="report-filter-grid">
          <div class="report-meta-card">
            <span class="text-muted d-block">Rows</span>
            <strong>${totalRows}</strong>
          </div>
          ${Object.entries(report.applied_filters)
            .map(
              ([key, value]) => `
                <div class="report-meta-card">
                  <span class="text-muted d-block text-capitalize">${escapePrintHtml(key.replace(/_/g, " "))}</span>
                  <strong>${escapePrintHtml(value)}</strong>
                </div>`,
            )
            .join("")}
          ${Object.entries(report.totals)
            .map(
              ([key, value]) => `
                <div class="report-meta-card">
                  <span class="text-muted d-block text-capitalize">${escapePrintHtml(key.replace(/_/g, " "))}</span>
                  <strong>${escapePrintHtml(formatReportCell(key, value, money, shortDate))}</strong>
                </div>`,
            )
            .join("")}
        </div>
      </section>
      ${
        pageRows.length > 0
          ? `
          <table>
            <thead>
              <tr>${columns.map((column) => `<th>${escapePrintHtml(column.replace(/_/g, " "))}</th>`).join("")}</tr>
            </thead>
            <tbody>
              ${pageRows
                .map(
                  (row) => `
                    <tr>
                      ${columns
                        .map((column) => {
                          const alignClass = ["amount", "bill", "paid", "due", "collection", "discount", "subtotal", "total", "net"].some((token) =>
                            column.toLowerCase().includes(token),
                          )
                            ? "right"
                            : "";
                          return `<td class="${alignClass}">${escapePrintHtml(formatReportCell(column, row[column], money, shortDate))}</td>`;
                        })
                        .join("")}
                    </tr>`,
                )
                .join("")}
            </tbody>
          </table>
          <div class="text-muted" style="margin-top: 12px;">Showing ${Math.min(startIndex + 1, totalRows)}-${Math.min(startIndex + pageRows.length, totalRows)} of ${totalRows}</div>
        `
          : `<div class="report-panel"><div class="empty-cell">No rows returned for this filter.</div></div>`
      }
    </main>
  `;
}

export function buildReportPrintMarkup(props: PrintMarkupProps) {
  if (props.currentPagedReport) {
    return buildPaginatedTableReportMarkup(props.currentPagedReport, props.reportViewerPage, props.money, props.shortDate);
  }
  if (props.currentReport) {
    return buildPaginatedTableReportMarkup(props.currentReport, props.reportViewerPage, props.money, props.shortDate);
  }
  if (props.receiptReport) {
    return `<main class="sheet">${escapePrintHtml(JSON.stringify(props.receiptReport))}</main>`;
  }
  if (props.memberStatementReport) {
    return `<main class="sheet">${escapePrintHtml(JSON.stringify(props.memberStatementReport))}</main>`;
  }
  if (props.memberInformationDetailReport) {
    return `<main class="sheet">${escapePrintHtml(JSON.stringify(props.memberInformationDetailReport))}</main>`;
  }
  if (props.incomeExpenseReport) {
    return `<main class="sheet">${escapePrintHtml(JSON.stringify(props.incomeExpenseReport))}</main>`;
  }
  return `<main class="sheet"><div class="empty-cell">No report loaded.</div></main>`;
}
