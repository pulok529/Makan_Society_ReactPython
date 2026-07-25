import { Auth } from "./features/auth/Auth";
import { Dashboard } from "./features/dashboard/Dashboard";
import { ChangeEvent, FormEvent, ReactNode, useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Swal from "sweetalert2";
import { getSmsBalance, sendTestSms, SmsBalanceResult } from "./api/sms";
import {
  loadIncomeExpenseReport,
  loadMemberInformationDetailReport,
  loadMemberStatementReport,
  loadPagedTableReport,
  loadReceiptDetailReport,
} from "./features/reports/api";
import {
  IncomeExpenseComparisonReport,
  MemberInformationDetailReport,
  PagedReportEnvelope,
  ReportEnvelope,
  ReceiptDetailReport,
  SingleMemberStatementReport,
  TABLE_REPORT_TYPES,
  TableReportType,
} from "./features/reports/types";
import { apiBaseUrl, apiRequest, settleRequest } from "./shared/api/client";
import { createBulkSmsJob, createReportExportJob } from "./shared/api/jobs";
import { AsyncSearchableDropdown } from "./shared/components/AsyncSearchableDropdown";
import { SearchableDropdown } from "./shared/components/SearchableDropdown";
import { useJobStatus } from "./shared/hooks/useJobStatus";
import { useDebouncedValue } from "./shared/hooks/useDebouncedValue";
import { PaginatedResponse } from "./shared/types/pagination";

const accessTokenKey = "society-modern-access-token";
const refreshTokenKey = "society-modern-refresh-token";
const assetBase = "/layout-template/assets";

import { UserProfile, TokenPair, Category, Package, MemberListItem, MemberSearchItem, MemberInformationSummary, MemberPackageAssignment, MemberDetail, BillingPeriod, ChargeItem, Charge, ReceiptLine, Receipt, BillingDashboard, BillingMemberSummary, BillingHead, BillingHeadMapping, BillingDueLine, BillingInvoice, Account, AccountingEntry, AccountingMasterEntry, AccountingSummary, AccountingVoucher, DataTableTotals, DataTableResponse, BillingChargeTableRow, BillingReceiptTableRow, BillingInvoiceTableRow, AccountingTransactionTableRow, IncomeTransferPendingItem, SmsTemplate, SmsMessage, SmsAttempt, SmsMessagePage, SmsAttemptPage, MemberPage, SmsIntegrationStatus, SmsProviderCheck, SmsProviderMode, AuthState, WorkspaceTab, NavItem, ThemeMode, LayoutMode, MenuColor, TopbarColor, SidenavSize, ThemeSettings } from './shared/types/models';

import { navItems } from './shared/config/navigation';

import { readThemeSettings, token, fetchProfile, getJQuery, reloadDataTable, fileNameFromDisposition, money, shortDate, dateKey, isWithinDateRange, currentMonthRange, invoiceStatus, invoiceStatusBadgeClass, chargeHeadSummary, pageTitle, statusBadge } from './shared/utils/formatters';

import { CardMenu, StatCard, MiniBars, MiniArea, EmptyState } from './shared/components/ui';

export function App() {
  const defaultMonthRange = currentMonthRange();
  const [authState, setAuthState] = useState<AuthState>("checking");
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [workspaceTab, setWorkspaceTab] = useState<WorkspaceTab>("dashboard");
  const [formMode, setFormMode] = useState<"login" | "bootstrap">("login");
  const [loginName, setLoginName] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("Makan Society workspace is ready.");
  const [messageTone, setMessageTone] = useState<"info" | "success" | "danger" | "warning">("info");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isWorkspaceLoading, setIsWorkspaceLoading] = useState(false);
  const [isDashboardReady, setIsDashboardReady] = useState(false);
  const [memberTotalCount, setMemberTotalCount] = useState(0);

  const [categories, setCategories] = useState<Category[]>([]);
  const [packages, setPackages] = useState<Package[]>([]);
  const [members, setMembers] = useState<MemberListItem[]>([]);
  const [selectedMember, setSelectedMember] = useState<MemberDetail | null>(null);
  const [billingPeriods, setBillingPeriods] = useState<BillingPeriod[]>([]);
  const [charges, setCharges] = useState<Charge[]>([]);
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [billingDashboard, setBillingDashboard] = useState<BillingDashboard | null>(null);
  const [memberDueSummaries, setMemberDueSummaries] = useState<BillingMemberSummary[]>([]);
  const [billingHeads, setBillingHeads] = useState<BillingHead[]>([]);
  const [billingHeadMappings, setBillingHeadMappings] = useState<BillingHeadMapping[]>([]);
  const [billingDueLines, setBillingDueLines] = useState<BillingDueLine[]>([]);
  const [billingInvoices, setBillingInvoices] = useState<BillingInvoice[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [accountingEntries, setAccountingEntries] = useState<AccountingEntry[]>([]);
  const [incomeMasterEntries, setIncomeMasterEntries] = useState<AccountingMasterEntry[]>([]);
  const [expenseMasterEntries, setExpenseMasterEntries] = useState<AccountingMasterEntry[]>([]);
  const [incomeVouchers, setIncomeVouchers] = useState<AccountingVoucher[]>([]);
  const [expenseVouchers, setExpenseVouchers] = useState<AccountingVoucher[]>([]);
  const [accountingSummary, setAccountingSummary] = useState<AccountingSummary | null>(null);
  const [incomeExpenseReport, setIncomeExpenseReport] = useState<IncomeExpenseComparisonReport | null>(null);
  const [currentReport, setCurrentReport] = useState<ReportEnvelope | null>(null);
  const [currentPagedReport, setCurrentPagedReport] = useState<PagedReportEnvelope | null>(null);
  const [reportViewerPage, setReportViewerPage] = useState(1);
  const [receiptReport, setReceiptReport] = useState<ReceiptDetailReport | null>(null);
  const [memberStatementReport, setMemberStatementReport] = useState<SingleMemberStatementReport | null>(null);
  const [memberInformationDetailReport, setMemberInformationDetailReport] = useState<MemberInformationDetailReport | null>(null);
  const [smsTemplates, setSmsTemplates] = useState<SmsTemplate[]>([]);
  const [smsMessages, setSmsMessages] = useState<SmsMessage[]>([]);
  const [smsAttempts, setSmsAttempts] = useState<SmsAttempt[]>([]);
  const [smsIntegrationStatus, setSmsIntegrationStatus] = useState<SmsIntegrationStatus | null>(null);
  const [smsProviderCheck, setSmsProviderCheck] = useState<SmsProviderCheck | null>(null);
  const [smsBalance, setSmsBalance] = useState<SmsBalanceResult | null>(null);

  const [categoryName, setCategoryName] = useState("");
  const [categoryCode, setCategoryCode] = useState("");
  const [categoryIsActive, setCategoryIsActive] = useState(true);
  const [categoryPageMode, setCategoryPageMode] = useState<"view" | "entry">("view");
  const [editingCategoryId, setEditingCategoryId] = useState<number | null>(null);
  const [packageName, setPackageName] = useState("");
  const [packageType, setPackageType] = useState("");
  const [packagePrice, setPackagePrice] = useState("0");
  const [packageCategoryId, setPackageCategoryId] = useState("");
  const [packageIsActive, setPackageIsActive] = useState(true);
  const [packagePageMode, setPackagePageMode] = useState<"view" | "entry">("view");
  const [editingPackageId, setEditingPackageId] = useState<number | null>(null);
  const [memberCode, setMemberCode] = useState("");
  const [memberName, setMemberName] = useState("");
  const [memberFatherName, setMemberFatherName] = useState("");
  const [memberMotherName, setMemberMotherName] = useState("");
  const [memberCell, setMemberCell] = useState("");
  const [memberEmail, setMemberEmail] = useState("");
  const [memberPresentAddress, setMemberPresentAddress] = useState("");
  const [memberPermanentAddress, setMemberPermanentAddress] = useState("");
  const [memberNationalId, setMemberNationalId] = useState("");
  const [memberPlotNo, setMemberPlotNo] = useState("");
  const [memberPlotCount, setMemberPlotCount] = useState("1");
  const [memberCategoryId, setMemberCategoryId] = useState("");
  const [memberClass, setMemberClass] = useState("");
  const [memberPackageId, setMemberPackageId] = useState("");
  const [memberIsActive, setMemberIsActive] = useState(true);
  const memberTableRef = useRef<HTMLTableElement | null>(null);
  const billingRegisterTableRef = useRef<HTMLTableElement | null>(null);
  const previousBillsTableRef = useRef<HTMLTableElement | null>(null);
  const incomeTableRef = useRef<HTMLTableElement | null>(null);
  const expenseTableRef = useRef<HTMLTableElement | null>(null);
  const [memberPageMode, setMemberPageMode] = useState<"view" | "entry">("view");
  const [editingMemberId, setEditingMemberId] = useState<number | null>(null);
  const [nomineeName, setNomineeName] = useState("");
  const [nomineeCell, setNomineeCell] = useState("");
  const [assignMemberId, setAssignMemberId] = useState("");
  const [assignPackageId, setAssignPackageId] = useState("");
  const [assignDate, setAssignDate] = useState("");
  const [periodYear, setPeriodYear] = useState(String(new Date().getFullYear()));
  const [periodMonth, setPeriodMonth] = useState(String(new Date().getMonth() + 1));
  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");
  const [generationPeriodId, setGenerationPeriodId] = useState("");
  const [receiptMemberId, setReceiptMemberId] = useState("");
  const [receiptChargeId, setReceiptChargeId] = useState("");
  const [receiptAmount, setReceiptAmount] = useState("");
  const [receiptDate, setReceiptDate] = useState("");
  const [receiptDiscount, setReceiptDiscount] = useState("0");
  const [billingHeadName, setBillingHeadName] = useState("");
  const [billingHeadType, setBillingHeadType] = useState<"Period" | "OneTime">("Period");
  const [billingHeadMode, setBillingHeadMode] = useState<"Mandatory" | "Optional">("Mandatory");
  const [billingHeadFee, setBillingHeadFee] = useState("500");
  const [billingHeadEffectiveDate, setBillingHeadEffectiveDate] = useState("2018-01-01");
  const [billingHeadEffectiveToDate, setBillingHeadEffectiveToDate] = useState("");
  const [billingHeadPageMode, setBillingHeadPageMode] = useState<"view" | "entry">("view");
  const [editingBillingHeadId, setEditingBillingHeadId] = useState<number | null>(null);
  const [mappingHeadId, setMappingHeadId] = useState("");
  const [mappingCoaId, setMappingCoaId] = useState("");
  const [billingMappingPageMode, setBillingMappingPageMode] = useState<"view" | "entry">("view");
  const [invoiceMemberId, setInvoiceMemberId] = useState("");
  const [invoiceMemberSearch, setInvoiceMemberSearch] = useState("");
  const [invoiceMemberDropdownOpen, setInvoiceMemberDropdownOpen] = useState(false);
  const [invoiceDate, setInvoiceDate] = useState(new Date().toISOString().slice(0, 10));
  const [invoiceDiscount, setInvoiceDiscount] = useState("0");
  const [invoiceReceipts, setInvoiceReceipts] = useState<Record<string, string>>({});
  const [lastGeneratedInvoice, setLastGeneratedInvoice] = useState<BillingInvoice | null>(null);
  const [invoiceReport, setInvoiceReport] = useState<BillingInvoice | null>(null);
  const [showInvoiceReport, setShowInvoiceReport] = useState(false);
  const [showReportViewer, setShowReportViewer] = useState(false);
  const [showPreviousBills, setShowPreviousBills] = useState(false);
  const [previousBillsFromDate, setPreviousBillsFromDate] = useState("");
  const [previousBillsToDate, setPreviousBillsToDate] = useState("");
  const [previousBillsTotals, setPreviousBillsTotals] = useState<DataTableTotals>({});
  const [manualBillingHeadId, setManualBillingHeadId] = useState("");
  const [manualBillingPeriod, setManualBillingPeriod] = useState(new Date().toISOString().slice(0, 7));
  const [manualBillingFee, setManualBillingFee] = useState("");
  const [billingRegisterTab, setBillingRegisterTab] = useState<"charges" | "receipts">("charges");
  const [billingRegisterFromDate, setBillingRegisterFromDate] = useState(defaultMonthRange.from);
  const [billingRegisterToDate, setBillingRegisterToDate] = useState(defaultMonthRange.to);
  const [billingRegisterTotals, setBillingRegisterTotals] = useState<DataTableTotals>({});
  const [accountCode, setAccountCode] = useState("");
  const [accountName, setAccountName] = useState("");
  const [accountType, setAccountType] = useState("income");
  const [editingAccountId, setEditingAccountId] = useState<number | null>(null);
  const [entryAccountId, setEntryAccountId] = useState("");
  const [entryAccountSearch, setEntryAccountSearch] = useState("");
  const [entryAccountDropdownOpen, setEntryAccountDropdownOpen] = useState(false);
  const [entryDate, setEntryDate] = useState(new Date().toISOString().slice(0, 10));
  const [entryFromDate, setEntryFromDate] = useState(defaultMonthRange.from);
  const [entryToDate, setEntryToDate] = useState(defaultMonthRange.to);
  const [entryTableTotals, setEntryTableTotals] = useState<Record<"income" | "expense", DataTableTotals>>({ income: {}, expense: {} });
  const [entryTableMode, setEntryTableMode] = useState<Record<"income" | "expense", string>>({ income: "voucher", expense: "voucher" });
  const [entryVoucherRemarks, setEntryVoucherRemarks] = useState("");
  const [entryAmount, setEntryAmount] = useState("");
  const [entryRemarks, setEntryRemarks] = useState("");
  const [entryMappedIncomeAmount, setEntryMappedIncomeAmount] = useState<number | null>(null);
  const [pendingEntries, setPendingEntries] = useState<{ account_id: number; account_label: string; amount: number; remarks: string | null }[]>([]);
  const [reportType, setReportType] = useState("due-members");
  const [reportMemberId, setReportMemberId] = useState("");
  const [reportMemberSearch, setReportMemberSearch] = useState("");
  const [reportMemberDropdownOpen, setReportMemberDropdownOpen] = useState(false);
  const [reportCategoryId, setReportCategoryId] = useState("");
  const [reportPeriodId, setReportPeriodId] = useState("");
  const [reportFromDate, setReportFromDate] = useState("");
  const [reportToDate, setReportToDate] = useState("");
  const [reportReceiptId, setReportReceiptId] = useState("");
  const [reportPlotNo, setReportPlotNo] = useState("");
  const [smsTemplateName, setSmsTemplateName] = useState("");
  const [smsTemplateType, setSmsTemplateType] = useState("");
  const [smsTemplateBody, setSmsTemplateBody] = useState("");
  const [editingSmsTemplateId, setEditingSmsTemplateId] = useState<number | null>(null);
  const [showSmsTemplateModal, setShowSmsTemplateModal] = useState(false);
  const [smsActiveTab, setSmsActiveTab] = useState<"send" | "delivery" | "gateway">("send");
  const [smsMemberId, setSmsMemberId] = useState("");
  const [smsMemberSearch, setSmsMemberSearch] = useState("");
  const [smsMemberDropdownOpen, setSmsMemberDropdownOpen] = useState(false);
  const [smsRecipient, setSmsRecipient] = useState("");
  const [smsSelectedTemplateId, setSmsSelectedTemplateId] = useState("");
  const [smsMessageBody, setSmsMessageBody] = useState("");
  const [smsTestRecipient, setSmsTestRecipient] = useState("");
  const [smsTestMessage, setSmsTestMessage] = useState("BulkSMSBD test message from Makan Society.");
  const [smsTargetMode, setSmsTargetMode] = useState<"single" | "all" | "due">("single");
  const [smsCategoryFilterId, setSmsCategoryFilterId] = useState("");
  const [smsRecipientSearch, setSmsRecipientSearch] = useState("");
  const [smsSelectedMemberIds, setSmsSelectedMemberIds] = useState<number[]>([]);
  const [smsSelectedMembersData, setSmsSelectedMembersData] = useState<MemberListItem[]>([]);
  const [smsBulkProgress, setSmsBulkProgress] = useState<{
    running: boolean;
    total: number;
    completed: number;
    success: number;
    failed: number;
    currentRecipient: string;
  }>({
    running: false,
    total: 0,
    completed: 0,
    success: 0,
    failed: 0,
    currentRecipient: "",
  });
  const [smsBulkProgressRows, setSmsBulkProgressRows] = useState<
    { memberId: number; name: string; phone: string; status: "sent" | "failed"; message: string }[]
  >([]);
  const [smsMessageSearch, setSmsMessageSearch] = useState("");
  const [smsAttemptSearch, setSmsAttemptSearch] = useState("");
  const [smsMessageOffset, setSmsMessageOffset] = useState(0);
  const [smsAttemptOffset, setSmsAttemptOffset] = useState(0);
  const [activeJobId, setActiveJobId] = useState<number | null>(null);
  const [activeJobLabel, setActiveJobLabel] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [displayEmail, setDisplayEmail] = useState("");
  const [displayPhone, setDisplayPhone] = useState("+8801700000000");
  const [displayRole, setDisplayRole] = useState("Admin Head");
  const [avatarUrl, setAvatarUrl] = useState(`${assetBase}/images/users/avatar-1.jpg`);
  const [showSettings, setShowSettings] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [menuSearch, setMenuSearch] = useState("");
  const [showMenuSearchResults, setShowMenuSearchResults] = useState(false);
  const [themeMode, setThemeMode] = useState<ThemeMode>(
    () => readThemeSettings().themeMode ?? (document.documentElement.getAttribute("data-bs-theme") as ThemeMode | null) ?? "dark",
  );
  const [layoutMode, setLayoutMode] = useState<LayoutMode>(
    () => readThemeSettings().layoutMode ?? (document.documentElement.getAttribute("data-layout-mode") as LayoutMode | null) ?? "fluid",
  );
  const [menuColor, setMenuColor] = useState<MenuColor>(
    () => readThemeSettings().menuColor ?? (document.documentElement.getAttribute("data-menu-color") as MenuColor | null) ?? "brand",
  );
  const [topbarColor, setTopbarColor] = useState<TopbarColor>(
    () => readThemeSettings().topbarColor ?? (document.documentElement.getAttribute("data-topbar-color") as TopbarColor | null) ?? "dark",
  );
  const [sidenavSize, setSidenavSize] = useState<SidenavSize>(
    () => readThemeSettings().sidenavSize ?? (document.documentElement.getAttribute("data-sidenav-size") as SidenavSize | null) ?? "default",
  );
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({});

  function showStatus(nextMessage: string, tone: "info" | "success" | "danger" | "warning" = "info") {
    setMessage(nextMessage);
    setMessageTone(tone);
  }

  function showError(nextMessage: string) {
    showStatus(nextMessage, "danger");
  }

  function showSuccess(nextMessage: string) {
    showStatus(nextMessage, "success");
  }

  const activeMembers = useMemo(() => members.filter((member) => member.is_active), [members]);
  const deferredMenuSearch = useDeferredValue(menuSearch);
  const filteredMenuItems = useMemo(() => {
    const needle = deferredMenuSearch.trim().toLowerCase();
    if (!needle) {
      return navItems.slice(0, 8);
    }
    return navItems.filter((item) => `${item.label} ${item.group ?? ""}`.toLowerCase().includes(needle)).slice(0, 10);
  }, [deferredMenuSearch]);
  const openCharges = useMemo(() => charges.filter((charge) => charge.due_amount > 0), [charges]);
  const incomeEntries = useMemo(
    () => accountingEntries.filter((entry) => entry.entry_type === "income"),
    [accountingEntries],
  );
  const expenseEntries = useMemo(
    () => accountingEntries.filter((entry) => entry.entry_type === "expense"),
    [accountingEntries],
  );
  const incomeAccounts = useMemo(
    () => accounts.filter((account) => account.is_active && ["income", "both", "income_expense"].includes(account.account_type)),
    [accounts],
  );
  const expenseAccounts = useMemo(
    () => accounts.filter((account) => account.is_active && ["expense", "both", "income_expense"].includes(account.account_type)),
    [accounts],
  );
  const selectedReceiptMemberId = receiptMemberId ? Number(receiptMemberId) : null;
  const availableChargesForReceipt = useMemo(
    () =>
      openCharges.filter((charge) =>
        selectedReceiptMemberId === null ? true : charge.member_id === selectedReceiptMemberId,
      ),
    [openCharges, selectedReceiptMemberId],
  );
  const totalCollection = billingDashboard?.total_collection_amount ?? 0;
  const dueByMemberId = useMemo(() => {
    const map = new Map<number, BillingMemberSummary>();
    memberDueSummaries.forEach((item) => map.set(item.member_id, item));
    return map;
  }, [memberDueSummaries]);
  const selectedSmsTemplate = useMemo(
    () => smsTemplates.find((template) => template.id === Number(smsSelectedTemplateId)) ?? null,
    [smsSelectedTemplateId, smsTemplates],
  );
  const smsSelectedMembers = useMemo(
    () => smsSelectedMembersData.filter((member) => smsSelectedMemberIds.includes(member.id)),
    [smsSelectedMemberIds, smsSelectedMembersData],
  );
  const memberClassOptions = useMemo(() => {
    const values = new Set<string>(["General", "Owner", "Tenant"]);
    if (memberClass.trim()) values.add(memberClass.trim());
    return [...values].sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
  }, [memberClass]);
  const billingLineKey = (line: BillingDueLine, index: number) => `${line.billing_head_id}-${line.period_date ?? "one"}-${index}`;
  const billingSelectedLines = useMemo(
    () =>
      billingDueLines
        .map((line, index) => ({
          line,
          index,
          receive: Number(invoiceReceipts[billingLineKey(line, index)] ?? 0),
        }))
        .filter((item) => item.receive > 0),
    [billingDueLines, invoiceReceipts],
  );
  const isLineSelected = (line: BillingDueLine, index: number) => Number(invoiceReceipts[billingLineKey(line, index)] ?? 0) > 0;
  const billingGridFeeTotal = useMemo(() => billingDueLines.reduce((sum, line, index) => isLineSelected(line, index) ? sum + Number(line.fee_amount || 0) : sum, 0), [billingDueLines, invoiceReceipts]);
  const billingGridPaidTotal = useMemo(() => billingDueLines.reduce((sum, line, index) => isLineSelected(line, index) ? sum + Number(line.paid_amount || 0) : sum, 0), [billingDueLines, invoiceReceipts]);
  const billingGridReceiveTotal = useMemo(
    () => billingDueLines.reduce((sum, line, index) => isLineSelected(line, index) ? sum + Number(invoiceReceipts[billingLineKey(line, index)] ?? 0) : sum, 0),
    [billingDueLines, invoiceReceipts],
  );
  const billingGridDueTotal = useMemo(() => billingDueLines.reduce((sum, line, index) => isLineSelected(line, index) ? sum + Number(line.due_amount || 0) : sum, 0), [billingDueLines, invoiceReceipts]);
  const billingAllRowsChecked = billingDueLines.length > 0 && billingDueLines.every((line, index) => isLineSelected(line, index));
  const billingSubtotal = useMemo(() => billingSelectedLines.reduce((sum, item) => sum + item.receive, 0), [billingSelectedLines]);
  const billingReceiveTotal = useMemo(
    () => billingSelectedLines.reduce((sum, item) => sum + item.receive, 0),
    [billingSelectedLines],
  );
  const billingDiscount = Number(invoiceDiscount || 0);
  const billingNetAmount = Math.max(billingSubtotal - billingDiscount, 0);
  const billingDueTotal = useMemo(
    () => billingSelectedLines.reduce((sum, item) => sum + Math.max(Number(item.line.due_amount) - item.receive, 0), 0),
    [billingSelectedLines],
  );
  const todayKey = new Date().toISOString().slice(0, 10);
  const todayInvoices = useMemo(() => billingInvoices.filter((invoice) => invoice.invoice_date === todayKey && !invoice.is_cancelled), [billingInvoices, todayKey]);
  const todayCollectionAmount = useMemo(() => todayInvoices.reduce((sum, invoice) => sum + Number(invoice.total_receive_amount || 0), 0), [todayInvoices]);
  const todayDueAmount = useMemo(() => todayInvoices.reduce((sum, invoice) => sum + Number(invoice.total_due_amount || 0), 0), [todayInvoices]);
  const todayCollectedMembers = useMemo(() => new Set(todayInvoices.filter((invoice) => invoice.total_receive_amount > 0).map((invoice) => invoice.member_id)).size, [todayInvoices]);
  const todayDiscountAmount = useMemo(() => todayInvoices.reduce((sum, invoice) => sum + Number(invoice.discount_amount || 0), 0), [todayInvoices]);
  const reportQueryString = useMemo(() => {
    const params = new URLSearchParams();
    if (reportFromDate) params.set("from_date", reportFromDate);
    if (reportToDate) params.set("to_date", reportToDate);
    if (reportMemberId) params.set("member_id", reportMemberId);
    if (reportCategoryId) params.set("category_id", reportCategoryId);
    if (reportPeriodId) params.set("billing_period_id", reportPeriodId);
    if (reportPlotNo.trim()) params.set("plot_no", reportPlotNo.trim());
    return params.toString();
  }, [reportCategoryId, reportFromDate, reportMemberId, reportPeriodId, reportPlotNo, reportToDate]);
  const currentAccessToken = authState === "authenticated" ? token() : null;
  const debouncedInvoiceMemberSearch = useDebouncedValue(invoiceMemberSearch, 300);
  const debouncedReportMemberSearch = useDebouncedValue(reportMemberSearch, 300);
  const debouncedSmsMemberSearch = useDebouncedValue(smsMemberSearch, 300);
  const debouncedSmsRecipientSearch = useDebouncedValue(smsRecipientSearch, 300);
  const debouncedSmsMessageSearch = useDebouncedValue(smsMessageSearch, 300);
  const debouncedSmsAttemptSearch = useDebouncedValue(smsAttemptSearch, 300);

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    enabled: !!currentAccessToken,
    queryFn: () => apiRequest<Category[]>("/api/categories", currentAccessToken!),
    staleTime: 5 * 60_000,
  });
  const packagesQuery = useQuery({
    queryKey: ["packages"],
    enabled: !!currentAccessToken,
    queryFn: () => apiRequest<Package[]>("/api/packages", currentAccessToken!),
    staleTime: 5 * 60_000,
  });
  const periodsQuery = useQuery({
    queryKey: ["billing-periods"],
    enabled: !!currentAccessToken,
    queryFn: () => apiRequest<BillingPeriod[]>("/api/billing/periods", currentAccessToken!),
    staleTime: 5 * 60_000,
  });
  const accountsQuery = useQuery({
    queryKey: ["accounts"],
    enabled: !!currentAccessToken,
    queryFn: () => apiRequest<Account[]>("/api/accounting/accounts", currentAccessToken!),
    staleTime: 5 * 60_000,
  });
  const billingHeadsQuery = useQuery({
    queryKey: ["billing-heads"],
    enabled: !!currentAccessToken,
    queryFn: () => apiRequest<BillingHead[]>("/api/billing/heads", currentAccessToken!),
    staleTime: 5 * 60_000,
  });
  const billingMappingsQuery = useQuery({
    queryKey: ["billing-head-mappings"],
    enabled: !!currentAccessToken,
    queryFn: () => apiRequest<BillingHeadMapping[]>("/api/billing/head-mappings", currentAccessToken!),
    staleTime: 5 * 60_000,
  });
  const dashboardQuery = useQuery({
    queryKey: ["billing-dashboard"],
    enabled: !!currentAccessToken,
    queryFn: () => apiRequest<BillingDashboard>("/api/billing/dashboard", currentAccessToken!),
  });
  const dueSummariesQuery = useQuery({
    queryKey: ["billing-due-summaries"],
    enabled: !!currentAccessToken,
    queryFn: () => apiRequest<BillingMemberSummary[]>("/api/billing/member-due-summary", currentAccessToken!),
  });
  const memberPreviewQuery = useQuery({
    queryKey: ["members", "preview"],
    enabled: !!currentAccessToken,
    queryFn: () => apiRequest<MemberPage>("/api/members/paged?limit=6&offset=0", currentAccessToken!),
  });
  const activeMemberCountQuery = useQuery({
    queryKey: ["members", "active-count"],
    enabled: !!currentAccessToken,
    queryFn: () => apiRequest<MemberPage>("/api/members/paged?limit=1&offset=0&is_active=true", currentAccessToken!),
  });
  const smsTemplatesQuery = useQuery({
    queryKey: ["sms-templates"],
    enabled: !!currentAccessToken,
    queryFn: () => apiRequest<SmsTemplate[]>("/api/messaging/templates", currentAccessToken!),
    staleTime: 5 * 60_000,
  });
  const smsStatusQuery = useQuery({
    queryKey: ["sms-status"],
    enabled: !!currentAccessToken,
    queryFn: () => apiRequest<SmsIntegrationStatus>("/api/messaging/status", currentAccessToken!),
  });
  const invoiceMemberOptionsQuery = useQuery({
    queryKey: ["members", "search", "invoice", debouncedInvoiceMemberSearch],
    enabled: !!currentAccessToken && debouncedInvoiceMemberSearch.trim().length >= 2,
    queryFn: () =>
      apiRequest<MemberSearchItem[]>(
        `/api/members/search?q=${encodeURIComponent(debouncedInvoiceMemberSearch.trim())}&limit=20`,
        currentAccessToken!,
      ),
  });
  const reportMemberOptionsQuery = useQuery({
    queryKey: ["members", "search", "report", debouncedReportMemberSearch],
    enabled: !!currentAccessToken && debouncedReportMemberSearch.trim().length >= 2,
    queryFn: () =>
      apiRequest<MemberSearchItem[]>(
        `/api/members/search?q=${encodeURIComponent(debouncedReportMemberSearch.trim())}&limit=20`,
        currentAccessToken!,
      ),
  });
  const smsMemberOptionsQuery = useQuery({
    queryKey: ["members", "search", "sms-single", debouncedSmsMemberSearch],
    enabled: !!currentAccessToken && debouncedSmsMemberSearch.trim().length >= 2,
    queryFn: () =>
      apiRequest<MemberSearchItem[]>(
        `/api/members/search?q=${encodeURIComponent(debouncedSmsMemberSearch.trim())}&limit=20&has_phone=true`,
        currentAccessToken!,
      ),
  });
  const smsRecipientMembersQuery = useQuery({
    queryKey: ["members", "paged-sms", smsTargetMode, smsCategoryFilterId, debouncedSmsRecipientSearch],
    enabled: !!currentAccessToken,
    queryFn: () => {
      const params = new URLSearchParams({
        limit: "50",
        offset: "0",
        has_phone: "true",
      });
      if (debouncedSmsRecipientSearch.trim()) params.set("search", debouncedSmsRecipientSearch.trim());
      if (smsCategoryFilterId) params.set("category_id", smsCategoryFilterId);
      if (smsTargetMode === "due") params.set("due_only", "true");
      return apiRequest<MemberPage>(`/api/members/paged?${params.toString()}`, currentAccessToken!);
    },
  });
  const smsMessagesQuery = useQuery({
    queryKey: ["sms-messages", debouncedSmsMessageSearch, smsMessageOffset],
    enabled: !!currentAccessToken,
    queryFn: () =>
      apiRequest<SmsMessagePage>(
        `/api/messaging/messages/paged?limit=8&offset=${smsMessageOffset}&search=${encodeURIComponent(debouncedSmsMessageSearch.trim())}`,
        currentAccessToken!,
      ),
  });
  const smsAttemptsQuery = useQuery({
    queryKey: ["sms-attempts", debouncedSmsAttemptSearch, smsAttemptOffset],
    enabled: !!currentAccessToken,
    queryFn: () =>
      apiRequest<SmsAttemptPage>(
        `/api/messaging/attempts/paged?limit=8&offset=${smsAttemptOffset}&search=${encodeURIComponent(debouncedSmsAttemptSearch.trim())}`,
        currentAccessToken!,
      ),
  });
  const selectedInvoiceMemberQuery = useQuery({
    queryKey: ["member-detail", "invoice", invoiceMemberId],
    enabled: !!currentAccessToken && !!invoiceMemberId,
    queryFn: () => apiRequest<MemberDetail>(`/api/members/${invoiceMemberId}`, currentAccessToken!),
  });
  const lastGeneratedMemberQuery = useQuery({
    queryKey: ["member-detail", "last-generated", lastGeneratedInvoice?.member_id],
    enabled: !!currentAccessToken && !!lastGeneratedInvoice?.member_id,
    queryFn: () => apiRequest<MemberDetail>(`/api/members/${lastGeneratedInvoice!.member_id}`, currentAccessToken!),
  });
  const smsSingleMemberQuery = useQuery({
    queryKey: ["member-detail", "sms-single", smsMemberId],
    enabled: !!currentAccessToken && !!smsMemberId,
    queryFn: () => apiRequest<MemberDetail>(`/api/members/${smsMemberId}`, currentAccessToken!),
  });
  const memberDropdownOptions = useMemo(
    () =>
      (invoiceMemberOptionsQuery.data ?? []).map((member) => ({
        value: String(member.id),
        label: `${member.member_code} - ${member.full_name}`,
        meta: [member.plot_no ? `Plot ${member.plot_no}` : null, `Plots ${member.plot_count ?? 1}`, member.cell_no, member.category_name].filter(Boolean).join(" | "),
      })),
    [invoiceMemberOptionsQuery.data],
  );
  const reportMemberOptions = useMemo(
    () =>
      (reportMemberOptionsQuery.data ?? []).map((member) => ({
        value: String(member.id),
        label: `${member.member_code} - ${member.full_name}`,
        meta: `${member.plot_no ? `Plot ${member.plot_no} | ` : ""}${member.cell_no ?? "No phone"}${member.category_name ? ` | ${member.category_name}` : ""}`,
      })),
    [reportMemberOptionsQuery.data],
  );
  const memberOptions = useMemo(
    () =>
      (smsMemberOptionsQuery.data ?? []).map((member) => ({
        value: String(member.id),
        label: `${member.member_code} - ${member.full_name}`,
        meta: `${member.plot_no ? `Plot ${member.plot_no} | ` : ""}${member.cell_no ?? "No phone"}${member.category_name ? ` | ${member.category_name}` : ""}`,
      })),
    [smsMemberOptionsQuery.data],
  );
  const smsEligibleMembers = useMemo(() => {
    const base = smsRecipientMembersQuery.data?.items ?? [];
    if (smsTargetMode === "single") {
      return smsSelectedMembersData.filter((member) => member.id === Number(smsMemberId));
    }
    return base;
  }, [smsMemberId, smsRecipientMembersQuery.data?.items, smsSelectedMembersData, smsTargetMode]);
  const smsFilteredMembers = smsEligibleMembers;
  const selectedInvoiceMember = selectedInvoiceMemberQuery.data ?? null;
  const lastGeneratedMember = lastGeneratedMemberQuery.data ?? null;
  const activeJobStatus = useJobStatus(activeJobId, currentAccessToken, !!activeJobId);

  const monthlyCollection = useMemo(() => {
    const totals = new Array(12).fill(0) as number[];
    receipts.forEach((receipt) => {
      const month = new Date(receipt.payment_date).getMonth();
      if (!Number.isNaN(month)) totals[month] += Number(receipt.total_amount);
    });
    return totals;
  }, [receipts]);
  const monthlyExpense = useMemo(() => {
    const totals = new Array(12).fill(0) as number[];
    expenseEntries.forEach((entry) => {
      const month = new Date(entry.created_at).getMonth();
      if (!Number.isNaN(month)) totals[month] += Number(entry.amount);
    });
    return totals;
  }, [expenseEntries]);
  const manualBillingHeadOptions = useMemo(
    () =>
      billingHeads.filter(
        (head) =>
          head.is_active &&
          (head.head_type === "Period" || (head.head_type === "OneTime" && head.billing_mode === "Optional")),
      ),
    [billingHeads],
  );

  useEffect(() => {
    const accessToken = token();
    if (!accessToken) {
      setAuthState("guest");
      return;
    }

    fetchProfile(accessToken)
      .then((data) => {
        setProfile(data);
        setAuthState("authenticated");
      })
      .catch(() => {
        localStorage.removeItem(accessTokenKey);
        localStorage.removeItem(refreshTokenKey);
        setAuthState("guest");
      });
  }, []);

  useEffect(() => {
    if (authState === "authenticated") {
      void loadWorkspace();
    }
  }, [authState]);

  useEffect(() => {
    if (!profile) return;
    setDisplayName(profile.username || "Admin");
    setDisplayEmail(profile.email ?? "admin@society.local");
  }, [profile]);

  useEffect(() => {
    if (categoriesQuery.data) setCategories(categoriesQuery.data);
  }, [categoriesQuery.data]);

  useEffect(() => {
    if (packagesQuery.data) setPackages(packagesQuery.data);
  }, [packagesQuery.data]);

  useEffect(() => {
    if (periodsQuery.data) setBillingPeriods(periodsQuery.data);
  }, [periodsQuery.data]);

  useEffect(() => {
    if (accountsQuery.data) setAccounts(accountsQuery.data);
  }, [accountsQuery.data]);

  useEffect(() => {
    if (billingHeadsQuery.data) setBillingHeads(billingHeadsQuery.data);
  }, [billingHeadsQuery.data]);

  useEffect(() => {
    if (billingMappingsQuery.data) setBillingHeadMappings(billingMappingsQuery.data);
  }, [billingMappingsQuery.data]);

  useEffect(() => {
    if (dashboardQuery.data) setBillingDashboard(dashboardQuery.data);
  }, [dashboardQuery.data]);

  useEffect(() => {
    if (dueSummariesQuery.data) setMemberDueSummaries(dueSummariesQuery.data);
  }, [dueSummariesQuery.data]);

  useEffect(() => {
    if (!memberPreviewQuery.data) return;
    setMembers(memberPreviewQuery.data.items);
    setMemberTotalCount(memberPreviewQuery.data.total);
  }, [memberPreviewQuery.data]);

  useEffect(() => {
    if (smsTemplatesQuery.data) setSmsTemplates(smsTemplatesQuery.data);
  }, [smsTemplatesQuery.data]);

  useEffect(() => {
    if (smsStatusQuery.data) {
      setSmsIntegrationStatus(smsStatusQuery.data);
      setSmsProviderCheck(
        smsStatusQuery.data.provider_check_ok == null
          ? null
          : {
              provider_name: smsStatusQuery.data.provider_name,
              provider_configured: smsStatusQuery.data.provider_configured,
              ok: smsStatusQuery.data.provider_check_ok,
              status_code: null,
              message: smsStatusQuery.data.provider_check_message ?? "Provider status available.",
              response_sample: null,
            },
      );
    }
  }, [smsStatusQuery.data]);

  useEffect(() => {
    if (smsMessagesQuery.data) setSmsMessages(smsMessagesQuery.data.items);
  }, [smsMessagesQuery.data]);

  useEffect(() => {
    if (smsAttemptsQuery.data) setSmsAttempts(smsAttemptsQuery.data.items);
  }, [smsAttemptsQuery.data]);

  useEffect(() => {
    const job = activeJobStatus.data;
    if (!job) return;
    if (job.job_type === "bulk_sms") {
      setSmsBulkProgress((current) => ({
        ...current,
        running: job.status === "pending" || job.status === "running",
        total: job.progress_total || current.total,
        completed: job.progress_current || current.completed,
        currentRecipient: job.result_summary ?? current.currentRecipient,
      }));
    }
    if (job.status === "completed") {
      setMessage(`${activeJobLabel || "Background job"} completed.`);
      if (job.output_filename) {
        void downloadAuthenticatedFile(`/api/jobs/${job.id}/download`, job.output_filename);
      }
      setActiveJobId(null);
      setActiveJobLabel("");
      if (job.job_type === "bulk_sms") {
        setSmsBulkProgress((current) => ({ ...current, running: false, completed: current.total }));
        void refreshMessagingWorkspace();
      }
      return;
    }
    if (job.status === "failed") {
      setMessage(`${activeJobLabel || "Background job"} failed: ${job.result_summary ?? "Unknown error"}`);
      if (job.job_type === "bulk_sms") {
        setSmsBulkProgress((current) => ({ ...current, running: false }));
      }
      setActiveJobId(null);
      setActiveJobLabel("");
      return;
    }
    const total = job.progress_total > 0 ? `${job.progress_current}/${job.progress_total}` : "Queued";
    setMessage(`${activeJobLabel || "Background job"} is running. ${total}`);
  }, [activeJobLabel, activeJobStatus.data]);

  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute("data-bs-theme", themeMode);
    root.setAttribute("data-layout-mode", layoutMode);
    root.setAttribute("data-menu-color", menuColor);
    root.setAttribute("data-topbar-color", topbarColor);
    root.setAttribute("data-sidenav-size", sidenavSize);
    document.body.setAttribute("data-bs-theme", themeMode);
    localStorage.setItem("society-modern-theme", JSON.stringify({ themeMode, layoutMode, menuColor, topbarColor, sidenavSize }));
  }, [layoutMode, menuColor, sidenavSize, themeMode, topbarColor]);

  useEffect(() => {
    if (smsTargetMode === "single" && smsMemberId) {
      setSmsSelectedMemberIds([Number(smsMemberId)]);
      return;
    }
    setSmsSelectedMemberIds((current) => current.filter((id) => smsEligibleMembers.some((member) => member.id === id)));
  }, [smsEligibleMembers, smsMemberId, smsTargetMode]);

  useEffect(() => {
    const next = new Map<number, MemberListItem>();
    smsSelectedMembersData.forEach((member) => next.set(member.id, member));
    (smsRecipientMembersQuery.data?.items ?? []).forEach((member) => {
      if (smsSelectedMemberIds.includes(member.id)) next.set(member.id, member);
    });
    if (smsSingleMemberQuery.data && smsSelectedMemberIds.includes(smsSingleMemberQuery.data.id)) {
      next.set(smsSingleMemberQuery.data.id, {
        id: smsSingleMemberQuery.data.id,
        member_code: smsSingleMemberQuery.data.member_code,
        full_name: smsSingleMemberQuery.data.full_name,
        plot_no: smsSingleMemberQuery.data.plot_no,
        plot_count: smsSingleMemberQuery.data.plot_count,
        cell_no: smsSingleMemberQuery.data.cell_no,
        category_id: smsSingleMemberQuery.data.category_id,
        category_name: smsSingleMemberQuery.data.category_name,
        joined_on: smsSingleMemberQuery.data.joined_on,
        is_active: smsSingleMemberQuery.data.is_active,
      });
    }
    const filtered = Array.from(next.values()).filter((member) => smsSelectedMemberIds.includes(member.id));
    setSmsSelectedMembersData(filtered);
  }, [smsRecipientMembersQuery.data?.items, smsSelectedMemberIds, smsSingleMemberQuery.data]);

  useEffect(() => {
    if (workspaceTab !== "members") return;
    const tableElement = memberTableRef.current;
    const jq = getJQuery();
    if (!tableElement || !jq?.fn?.DataTable) return;
    const clickHandler = (event: Event) => {
      const target = event.target as HTMLElement;
      const actionButton = target.closest<HTMLButtonElement>("button[data-member-action]");
      if (!actionButton) return;
      const memberId = Number(actionButton.dataset.memberId || 0);
      if (!memberId) return;
      if (actionButton.dataset.memberAction === "edit") {
        const member =
          memberPreviewQuery.data?.items.find((item) => item.id === memberId) ??
          smsSelectedMembersData.find((item) => item.id === memberId) ??
          null;
        if (member) {
          void startMemberEntry(member);
        } else {
          void (async () => {
            const accessToken = token();
            if (!accessToken) return;
            const detail = await apiRequest<MemberDetail>(`/api/members/${memberId}`, accessToken);
            await startMemberEntry({
              id: detail.id,
              member_code: detail.member_code,
              full_name: detail.full_name,
              plot_no: detail.plot_no,
              plot_count: detail.plot_count,
              cell_no: detail.cell_no,
              category_id: detail.category_id,
              category_name: detail.category_name,
              joined_on: detail.joined_on,
              is_active: detail.is_active,
            });
          })();
        }
      } else {
        void handleMemberSelect(memberId);
      }
    };
    tableElement.addEventListener("click", clickHandler);

    const timer = window.setTimeout(() => {
      try {
        jq(tableElement).DataTable({
          destroy: true,
          processing: true,
          serverSide: true,
          pageLength: 25,
          searchDelay: 300,
          lengthMenu: [25, 50, 100, 200],
          lengthChange: true,
          autoWidth: false,
          ajax: async (request: any, callback: (payload: any) => void) => {
            const accessToken = token();
            if (!accessToken) {
              callback({ draw: request.draw ?? 1, recordsTotal: 0, recordsFiltered: 0, data: [] });
              return;
            }
            const limit = request.length ?? 25;
            const offset = request.start ?? 0;
            const search = request.search?.value?.trim() ?? "";
            const payload = await apiRequest<MemberPage>(
              `/api/members/paged?limit=${limit}&offset=${offset}&search=${encodeURIComponent(search)}`,
              accessToken,
            );
            setMemberTotalCount(payload.total);
            callback({
              draw: request.draw ?? 1,
              recordsTotal: payload.total,
              recordsFiltered: payload.total,
              data: payload.items,
            });
          },
          columns: [
            { data: "member_code" },
            { data: "full_name" },
            { data: "plot_no", render: (value: string | null) => value ?? "N/A" },
            { data: "plot_count" },
            { data: "cell_no", render: (value: string | null) => value ?? "N/A" },
            { data: "category_name", render: (value: string | null) => value ?? "N/A" },
            {
              data: "is_active",
              render: (value: boolean) =>
                value
                  ? '<span class="badge bg-success-subtle text-success">Active</span>'
                  : '<span class="badge bg-danger-subtle text-danger">Inactive</span>',
            },
            {
              data: null,
              orderable: false,
              searchable: false,
              className: "text-end",
              render: (_: unknown, __: unknown, row: MemberListItem) =>
                `<div class="d-inline-flex gap-1">
                  <button class="btn btn-sm btn-soft-secondary" type="button" data-member-action="view" data-member-id="${row.id}">View</button>
                  <button class="btn btn-sm btn-soft-info" type="button" data-member-action="edit" data-member-id="${row.id}">Edit</button>
                </div>`,
            },
          ],
          order: [[0, "asc"]],
          language: {
            paginate: {
              previous: "<i class='ri-arrow-left-s-line'>",
              next: "<i class='ri-arrow-right-s-line'>",
            },
          },
          drawCallback() {
            jq(".dataTables_paginate > .pagination").addClass("pagination-rounded");
          },
        });
      } catch (error) {
        console.error("Failed to initialize member DataTable", error);
      }
    }, 0);

    return () => {
      window.clearTimeout(timer);
      tableElement.removeEventListener("click", clickHandler);
      try {
        if (tableElement && jq?.fn?.DataTable && jq.fn.DataTable.isDataTable(tableElement)) {
          jq(tableElement).DataTable().destroy();
        }
      } catch {
        // Ignore teardown errors during tab switches.
      }
    };
  }, [workspaceTab]);

  useEffect(() => {
    if (workspaceTab !== "billing-registers") return;
    const tableElement = billingRegisterTableRef.current;
    const jq = getJQuery();
    if (!tableElement || !jq?.fn?.DataTable) return;
    const isChargeTable = billingRegisterTab === "charges";
    const orderKeys = isChargeTable
      ? ["member", "date", "period", "head", "net", "paid", "due", "status"]
      : ["receipt", "member", "plot", "date", "total"];
    const timer = window.setTimeout(() => {
      try {
        jq(tableElement).DataTable({
          destroy: true,
          processing: true,
          serverSide: true,
          pageLength: 25,
          searchDelay: 500,
          lengthChange: true,
          ajax: async (request: any, callback: (payload: any) => void) => {
            const accessToken = token();
            if (!accessToken) {
              callback({ draw: request.draw ?? 1, recordsTotal: 0, recordsFiltered: 0, data: [] });
              return;
            }
            const order = request.order?.[0];
            const params = new URLSearchParams({
              draw: String(request.draw ?? 1),
              start: String(request.start ?? 0),
              length: String(request.length ?? 25),
              search_value: request.search?.value ?? "",
              order_key: orderKeys[order?.column ?? 1] ?? "date",
              order_dir: order?.dir ?? "desc",
            });
            if (billingRegisterFromDate) params.append("from_date", billingRegisterFromDate);
            if (billingRegisterToDate) params.append("to_date", billingRegisterToDate);
            try {
              const payload = await apiRequest<DataTableResponse<BillingChargeTableRow | BillingReceiptTableRow>>(
                `/api/billing/tables/${isChargeTable ? "charges" : "receipts"}?${params.toString()}`,
                accessToken,
              );
              setBillingRegisterTotals(payload.totals ?? {});
              callback(payload);
            } catch (error) {
              console.error("Unable to load billing register", error);
              setBillingRegisterTotals({});
              callback({ draw: request.draw ?? 1, recordsTotal: 0, recordsFiltered: 0, data: [] });
            }
          },
          columns: isChargeTable
            ? [
                {
                  data: null,
                  render: (_: unknown, __: unknown, row: BillingChargeTableRow) =>
                    `<div class="fw-semibold">${row.member_name}</div><div class="text-muted fs-12">${row.member_code}${row.plot_no ? ` | Plot ${row.plot_no}` : ""}</div>`,
                },
                { data: "created_at", render: (value: string) => shortDate(value) },
                { data: "billing_period_name", defaultContent: "N/A" },
                { data: "head_summary", defaultContent: "-" },
                { data: "net_amount", className: "text-end", render: (value: number) => money(value) },
                { data: "paid_amount", className: "text-end", render: (value: number) => money(value) },
                { data: "due_amount", className: "text-end", render: (value: number) => money(value) },
                { data: "status" },
              ]
            : [
                { data: "receipt_no" },
                {
                  data: null,
                  render: (_: unknown, __: unknown, row: BillingReceiptTableRow) =>
                    `${row.member_name ?? "N/A"}${row.plot_no ? `<div class="text-muted fs-12">Plot ${row.plot_no}</div>` : ""}`,
                },
                { data: "plot_no", defaultContent: "N/A" },
                { data: "payment_date", render: (value: string) => shortDate(value) },
                { data: "total_amount", className: "text-end", render: (value: number) => money(value) },
              ],
          order: [[1, "desc"]],
          language: {
            paginate: {
              previous: "<i class='ri-arrow-left-s-line'>",
              next: "<i class='ri-arrow-right-s-line'>",
            },
          },
          drawCallback() {
            jq(".dataTables_paginate > .pagination").addClass("pagination-rounded");
          },
        });
      } catch (error) {
        console.error("Failed to initialize billing register DataTable", error);
      }
    }, 0);

    return () => {
      window.clearTimeout(timer);
      try {
        if (tableElement && jq?.fn?.DataTable && jq.fn.DataTable.isDataTable(tableElement)) {
          jq(tableElement).DataTable().destroy();
        }
      } catch {
        // Ignore teardown errors while switching tabs.
      }
    };
  }, [billingRegisterFromDate, billingRegisterTab, billingRegisterToDate, workspaceTab]);

  useEffect(() => {
    if (!showPreviousBills || !invoiceMemberId) return;
    const tableElement = previousBillsTableRef.current;
    const jq = getJQuery();
    if (!tableElement || !jq?.fn?.DataTable) return;
    const orderKeys = ["invoice", "date", "subtotal", "discount", "received", "due", "status", "action"];
    const clickHandler = (event: Event) => {
      const target = event.target as HTMLElement;
      const actionButton = target.closest<HTMLButtonElement>("button[data-invoice-action]");
      if (!actionButton) return;
      const invoiceId = Number(actionButton.dataset.invoiceId || 0);
      if (!invoiceId) return;
      if (actionButton.dataset.invoiceAction === "view") {
        void openInvoiceReportById(invoiceId);
      } else if (actionButton.dataset.invoiceAction === "print") {
        void printInvoiceById(invoiceId);
      } else if (actionButton.dataset.invoiceAction === "delete") {
        void handleDeleteInvoice(invoiceId);
      }
    };
    tableElement.addEventListener("click", clickHandler);
    const timer = window.setTimeout(() => {
      try {
        jq(tableElement).DataTable({
          destroy: true,
          processing: true,
          serverSide: true,
          pageLength: 25,
          searchDelay: 500,
          ajax: async (request: any, callback: (payload: any) => void) => {
            const accessToken = token();
            if (!accessToken) {
              callback({ draw: request.draw ?? 1, recordsTotal: 0, recordsFiltered: 0, data: [] });
              return;
            }
            const order = request.order?.[0];
            const params = new URLSearchParams({
              draw: String(request.draw ?? 1),
              start: String(request.start ?? 0),
              length: String(request.length ?? 25),
              search_value: request.search?.value ?? "",
              order_key: orderKeys[order?.column ?? 1] ?? "date",
              order_dir: order?.dir ?? "desc",
              member_id: invoiceMemberId,
            });
            if (previousBillsFromDate) params.append("from_date", previousBillsFromDate);
            if (previousBillsToDate) params.append("to_date", previousBillsToDate);
            try {
              const payload = await apiRequest<DataTableResponse<BillingInvoiceTableRow>>(`/api/billing/tables/invoices?${params.toString()}`, accessToken);
              setPreviousBillsTotals(payload.totals ?? {});
              callback(payload);
            } catch (error) {
              console.error("Unable to load previous bills", error);
              setPreviousBillsTotals({});
              callback({ draw: request.draw ?? 1, recordsTotal: 0, recordsFiltered: 0, data: [] });
            }
          },
          columns: [
            { data: "invoice_no" },
            { data: "invoice_date", render: (value: string) => shortDate(value) },
            { data: "subtotal_amount", className: "text-end", render: (value: number) => money(value) },
            { data: "discount_amount", className: "text-end", render: (value: number) => money(value) },
            { data: "total_receive_amount", className: "text-end", render: (value: number) => money(value) },
            { data: "total_due_amount", className: "text-end", render: (value: number) => money(value) },
            {
              data: "status",
              render: (value: string) => `<span class="${invoiceStatusBadgeClass(value)}">${value}</span>`,
            },
            {
              data: null,
              orderable: false,
              searchable: false,
              className: "text-end",
              render: (_: unknown, __: unknown, row: BillingInvoiceTableRow) =>
                `<div class="d-inline-flex gap-1">
                  <button class="btn btn-sm btn-soft-info" type="button" data-invoice-action="view" data-invoice-id="${row.id}"><i class="ri-eye-line me-1"></i>View</button>
                  <button class="btn btn-sm btn-soft-primary" type="button" data-invoice-action="print" data-invoice-id="${row.id}"><i class="ri-printer-line me-1"></i>Print</button>
                  ${!row.status.includes('Cancelled') ? `<button class="btn btn-sm btn-soft-danger" type="button" data-invoice-action="delete" data-invoice-id="${row.id}"><i class="ri-delete-bin-line me-1"></i>Delete</button>` : ''}
                </div>`,
            },
          ],
          order: [[1, "desc"]],
          language: {
            paginate: {
              previous: "<i class='ri-arrow-left-s-line'>",
              next: "<i class='ri-arrow-right-s-line'>",
            },
          },
          drawCallback() {
            jq(".dataTables_paginate > .pagination").addClass("pagination-rounded");
          },
        });
      } catch (error) {
        console.error("Failed to initialize previous bills DataTable", error);
      }
    }, 0);
    return () => {
      window.clearTimeout(timer);
      tableElement.removeEventListener("click", clickHandler);
      try {
        if (tableElement && jq?.fn?.DataTable && jq.fn.DataTable.isDataTable(tableElement)) {
          jq(tableElement).DataTable().destroy();
        }
      } catch {
        // Ignore teardown errors while closing the modal.
      }
    };
  }, [invoiceMemberId, previousBillsFromDate, previousBillsToDate, showPreviousBills]);

  useEffect(() => {
    const tableElement = workspaceTab === "income-view" ? incomeTableRef.current : workspaceTab === "expense-view" ? expenseTableRef.current : null;
    const entryType: "income" | "expense" | null = workspaceTab === "income-view" ? "income" : workspaceTab === "expense-view" ? "expense" : null;
    const jq = getJQuery();
    if (!tableElement || !entryType || !jq?.fn?.DataTable) return;
    const orderKeys = ["reference", "date", "head", "amount", "remarks", "lines", "actions"];
    const clickHandler = (event: Event) => {
      const target = event.target as HTMLElement;
      const actionButton = target.closest<HTMLButtonElement>("button[data-voucher-action]");
      if (!actionButton) return;
      const voucherId = Number(actionButton.dataset.voucherId || 0);
      if (!voucherId) return;
      if (actionButton.dataset.voucherAction === "view") {
        void openVoucherReportById(voucherId);
      } else {
        void printVoucherById(voucherId);
      }
    };
    tableElement.addEventListener("click", clickHandler);
    const timer = window.setTimeout(() => {
      try {
        jq(tableElement).DataTable({
          destroy: true,
          processing: true,
          serverSide: true,
          pageLength: 25,
          searchDelay: 500,
          ajax: async (request: any, callback: (payload: any) => void) => {
            const accessToken = token();
            if (!accessToken) {
              callback({ draw: request.draw ?? 1, recordsTotal: 0, recordsFiltered: 0, data: [] });
              return;
            }
            const order = request.order?.[0];
            const params = new URLSearchParams({
              draw: String(request.draw ?? 1),
              start: String(request.start ?? 0),
              length: String(request.length ?? 25),
              search_value: request.search?.value ?? "",
              order_key: orderKeys[order?.column ?? 1] ?? "date",
              order_dir: order?.dir ?? "desc",
              from_date: entryFromDate,
              to_date: entryToDate,
            });
            try {
              const payload = await apiRequest<DataTableResponse<AccountingTransactionTableRow>>(`/api/accounting/tables/${entryType}?${params.toString()}`, accessToken);
              setEntryTableTotals((current) => ({ ...current, [entryType]: payload.totals ?? {} }));
              setEntryTableMode((current) => ({ ...current, [entryType]: payload.mode ?? "voucher" }));
              callback(payload);
            } catch (error) {
              console.error(`Unable to load ${entryType} table`, error);
              setEntryTableTotals((current) => ({ ...current, [entryType]: {} }));
              callback({ draw: request.draw ?? 1, recordsTotal: 0, recordsFiltered: 0, data: [] });
            }
          },
          columns: [
            { data: "reference_no" },
            { data: "transaction_date", render: (value: string) => shortDate(value) },
            { data: "head_name", defaultContent: "-" },
            { data: "amount", className: "text-end", render: (value: number) => money(value) },
            { data: "remarks", defaultContent: "-" },
            { data: "line_count", className: "text-center" },
            {
              data: null,
              orderable: false,
              searchable: false,
              className: "text-end",
              render: (_: unknown, __: unknown, row: AccountingTransactionTableRow) =>
                row.is_voucher
                  ? `<div class="d-inline-flex gap-1">
                      <button class="btn btn-sm btn-soft-info" type="button" data-voucher-action="view" data-voucher-id="${row.id}"><i class="ri-file-text-line me-1"></i>View Report</button>
                      <button class="btn btn-sm btn-soft-primary" type="button" data-voucher-action="print" data-voucher-id="${row.id}"><i class="ri-printer-line me-1"></i>Print</button>
                    </div>`
                  : "-",
            },
          ],
          order: [[1, "desc"]],
          language: {
            paginate: {
              previous: "<i class='ri-arrow-left-s-line'>",
              next: "<i class='ri-arrow-right-s-line'>",
            },
          },
          drawCallback() {
            jq(".dataTables_paginate > .pagination").addClass("pagination-rounded");
          },
        });
      } catch (error) {
        console.error(`Failed to initialize ${entryType} DataTable`, error);
      }
    }, 0);
    return () => {
      window.clearTimeout(timer);
      tableElement.removeEventListener("click", clickHandler);
      try {
        if (tableElement && jq?.fn?.DataTable && jq.fn.DataTable.isDataTable(tableElement)) {
          jq(tableElement).DataTable().destroy();
        }
      } catch {
        // Ignore teardown errors while switching accounting views.
      }
    };
  }, [entryFromDate, entryToDate, workspaceTab]);

  useEffect(() => {
    if (workspaceTab !== "income-entry") return;
    if (!entryAccountId) {
      setEntryMappedIncomeAmount(null);
      return;
    }
    void loadMappedIncomeAmount(entryAccountId, entryDate, false);
  }, [entryAccountId, entryDate, workspaceTab]);

  useEffect(() => {
    const accessToken = token();
    if (!accessToken || !receiptMemberId) {
      setCharges([]);
      return;
    }
    apiRequest<Charge[]>(`/api/billing/charges?member_id=${receiptMemberId}&due_only=true`, accessToken)
      .then((nextCharges) => setCharges(nextCharges))
      .catch(() => setCharges([]));
  }, [receiptMemberId]);

  useEffect(() => {
    if (reportType !== "member-statement" && reportType !== "member-information-detail") {
      setReportMemberDropdownOpen(false);
      setReportMemberSearch("");
    }
  }, [reportType]);

  useEffect(() => {
    if (!showReportViewer || !currentPagedReport || !TABLE_REPORT_TYPES.has(reportType as TableReportType)) return;
    const currentPage = Math.max(1, Math.floor(currentPagedReport.offset / Math.max(currentPagedReport.limit, 1)) + 1);
    if (currentPage === reportViewerPage) return;
    const accessToken = token();
    if (!accessToken) return;

    let cancelled = false;
    setIsSubmitting(true);
    void loadPagedTableReport(accessToken, reportType as TableReportType, reportQueryString, {
      limit: currentPagedReport.limit,
      offset: Math.max(reportViewerPage - 1, 0) * currentPagedReport.limit,
    })
      .then((payload) => {
        if (!cancelled) setCurrentPagedReport(payload);
      })
      .catch((error) => {
        if (!cancelled) setMessage(error instanceof Error ? error.message : "Unable to load report page");
      })
      .finally(() => {
        if (!cancelled) setIsSubmitting(false);
      });

    return () => {
      cancelled = true;
    };
  }, [currentPagedReport, reportQueryString, reportType, reportViewerPage, showReportViewer]);

  useEffect(() => {
    setSmsMessageBody(selectedSmsTemplate?.body ?? "");
  }, [selectedSmsTemplate]);

  async function loadWorkspace(selectedMemberId?: number) {
    const accessToken = token();
    if (!accessToken) return;
    const currentYear = new Date().getFullYear();
    const receiptRange = new URLSearchParams({
      from_date: `${currentYear}-01-01`,
      to_date: `${currentYear}-12-31`,
    }).toString();
    const invoiceRange = new URLSearchParams({
      from_date: defaultMonthRange.from,
      to_date: defaultMonthRange.to,
    }).toString();

    setIsWorkspaceLoading(true);
    if (!isDashboardReady) {
      setMessage("Loading dashboard...");
      setMessageTone("info");
    }
    try {
      const [receiptsResult, summaryResult] = await Promise.all([
        settleRequest<Receipt[]>(`/api/billing/receipts?${receiptRange}`, accessToken),
        settleRequest<AccountingSummary>("/api/accounting/summary", accessToken),
      ]);

      if (receiptsResult.ok) setReceipts(receiptsResult.value);
      if (summaryResult.ok) setAccountingSummary(summaryResult.value);

      const memberIdToLoad = selectedMemberId ?? selectedMember?.id ?? null;
      if (memberIdToLoad) {
        const detail = await apiRequest<MemberDetail>(`/api/members/${memberIdToLoad}`, accessToken);
        setSelectedMember(detail);
      } else if (!selectedMemberId) {
        setSelectedMember(null);
      }

      const coreFailedCount = [receiptsResult, summaryResult].filter((result) => !result.ok).length;

      setIsDashboardReady(true);
      setMessage(
        coreFailedCount === 0
          ? "Dashboard loaded. Loading the remaining sections in the background..."
          : `Dashboard loaded. ${coreFailedCount} core section${coreFailedCount === 1 ? "" : "s"} could not be refreshed.`,
      );

      const [invoicesResult] = await Promise.all([
        settleRequest<BillingInvoice[]>(`/api/billing/invoices?${invoiceRange}`, accessToken),
      ]);

      setCharges([]);
      setAccountingEntries([]);
      setIncomeMasterEntries([]);
      setExpenseMasterEntries([]);
      setIncomeVouchers([]);
      setExpenseVouchers([]);
      if (invoicesResult.ok) setBillingInvoices(invoicesResult.value);

      const failedCount = [receiptsResult, summaryResult, invoicesResult].filter((result) => !result.ok).length;

      setMessage(
        failedCount === 0
          ? "Makan Society workspace loaded with live society data."
          : `Workspace loaded with existing data. ${failedCount} section${failedCount === 1 ? "" : "s"} could not be refreshed.`,
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to load workspace");
    } finally {
      setIsWorkspaceLoading(false);
    }
  }

  async function refreshBillingWorkspace() {
    const accessToken = token();
    if (!accessToken) return;
    const currentYear = new Date().getFullYear();
    const receiptRange = new URLSearchParams({
      from_date: `${currentYear}-01-01`,
      to_date: `${currentYear}-12-31`,
    }).toString();
    const invoiceRange = new URLSearchParams({
      from_date: defaultMonthRange.from,
      to_date: defaultMonthRange.to,
    }).toString();

    const [periodsResult, receiptsResult, dashboardResult, dueSummaryResult, headsResult, mappingsResult, invoicesResult] =
      await Promise.all([
        settleRequest<BillingPeriod[]>("/api/billing/periods", accessToken),
        settleRequest<Receipt[]>(`/api/billing/receipts?${receiptRange}`, accessToken),
        settleRequest<BillingDashboard>("/api/billing/dashboard", accessToken),
        settleRequest<BillingMemberSummary[]>("/api/billing/member-due-summary", accessToken),
        settleRequest<BillingHead[]>("/api/billing/heads", accessToken),
        settleRequest<BillingHeadMapping[]>("/api/billing/head-mappings", accessToken),
        settleRequest<BillingInvoice[]>(`/api/billing/invoices?${invoiceRange}`, accessToken),
      ]);

    if (periodsResult.ok) setBillingPeriods(periodsResult.value);
    setCharges([]);
    if (receiptsResult.ok) setReceipts(receiptsResult.value);
    if (dashboardResult.ok) setBillingDashboard(dashboardResult.value);
    if (dueSummaryResult.ok) setMemberDueSummaries(dueSummaryResult.value);
    if (headsResult.ok) setBillingHeads(headsResult.value);
    if (mappingsResult.ok) setBillingHeadMappings(mappingsResult.value);
    if (invoicesResult.ok) setBillingInvoices(invoicesResult.value);
  }

  async function refreshAccountingWorkspace() {
    const accessToken = token();
    if (!accessToken) return;
    const [nextAccounts, nextSummary] = await Promise.all([
      apiRequest<Account[]>("/api/accounting/accounts", accessToken),
      apiRequest<AccountingSummary>("/api/accounting/summary", accessToken),
    ]);
    setAccounts(nextAccounts);
    setAccountingEntries([]);
    setIncomeMasterEntries([]);
    setExpenseMasterEntries([]);
    setIncomeVouchers([]);
    setExpenseVouchers([]);
    setAccountingSummary(nextSummary);
  }

  async function refreshMessagingWorkspace() {
    const accessToken = token();
    if (!accessToken) return;
    const [nextTemplates, nextMessages, nextAttempts, nextSmsStatus] = await Promise.all([
      apiRequest<SmsTemplate[]>("/api/messaging/templates", accessToken),
      apiRequest<SmsMessagePage>(`/api/messaging/messages/paged?limit=8&offset=${smsMessageOffset}&search=${encodeURIComponent(debouncedSmsMessageSearch.trim())}`, accessToken),
      apiRequest<SmsAttemptPage>(`/api/messaging/attempts/paged?limit=8&offset=${smsAttemptOffset}&search=${encodeURIComponent(debouncedSmsAttemptSearch.trim())}`, accessToken),
      apiRequest<SmsIntegrationStatus>("/api/messaging/status", accessToken),
    ]);
    setSmsTemplates(nextTemplates);
    setSmsMessages(nextMessages.items);
    setSmsAttempts(nextAttempts.items);
    setSmsIntegrationStatus(nextSmsStatus);
    setSmsProviderCheck(
      nextSmsStatus.provider_check_message
        ? {
            provider_name: nextSmsStatus.provider_name,
            provider_configured: nextSmsStatus.provider_configured,
            ok: Boolean(nextSmsStatus.provider_check_ok),
            status_code: null,
            message: nextSmsStatus.provider_check_message,
            response_sample: null,
          }
        : null,
    );
  }

  async function handleSmsProviderMode(providerMode: SmsProviderMode) {
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      const nextStatus = await apiRequest<SmsIntegrationStatus>("/api/messaging/provider-mode", accessToken, {
        method: "POST",
        body: JSON.stringify({ provider_mode: providerMode }),
      });
      setSmsIntegrationStatus(nextStatus);
      setMessage(providerMode === "bulksmsbd" ? "BulkSMSBD real API is active." : "SMS simulation mode is active.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to change SMS provider mode");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSmsProviderCheck() {
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      const providerCheck = await apiRequest<SmsProviderCheck>("/api/messaging/provider-check", accessToken);
      const nextStatus = await apiRequest<SmsIntegrationStatus>("/api/messaging/status", accessToken);
      setSmsProviderCheck(providerCheck);
      setSmsIntegrationStatus(nextStatus);
      setMessage(providerCheck.ok ? "SMS API responded. No SMS was sent." : providerCheck.message);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to check SMS API");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSmsBalanceCheck() {
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      const balance = await getSmsBalance(accessToken);
      setSmsBalance(balance);
      setMessage(balance.success ? balance.provider_message : friendlySmsError(balance.provider_code, balance.provider_message));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to check SMS balance");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleTestSmsSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      const result = await sendTestSms(accessToken, smsTestRecipient, smsTestMessage);
      await refreshMessagingWorkspace();
      setMessage(result.success ? "SMS submitted successfully" : friendlySmsError(result.provider_code, result.provider_message));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to send test SMS");
    } finally {
      setIsSubmitting(false);
    }
  }

  function friendlySmsError(code: string | null, fallback: string) {
    if (code === "1007") return "Insufficient SMS balance";
    if (code === "1002") return "Sender ID is invalid or disabled";
    if (code === "1003") return "Required SMS fields are missing";
    if (!code && fallback.toLowerCase().includes("invalid bangladeshi")) return "Invalid phone number";
    if (!code && fallback.toLowerCase().includes("timeout")) return "SMS provider unavailable";
    return fallback || "SMS provider unavailable";
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setMessage("Signing in...");
    try {
      const response = await fetch(`${apiBaseUrl}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ login_name: loginName, password }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail ?? "Login failed");
      }
      const payload = (await response.json()) as TokenPair;
      localStorage.setItem(accessTokenKey, payload.access_token);
      localStorage.setItem(refreshTokenKey, payload.refresh_token);
      const user = await fetchProfile(payload.access_token);
      setProfile(user);
      setAuthState("authenticated");
      setMessage("Signed in.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Login failed");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleBootstrap(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setMessage("Creating first admin...");
    try {
      await fetch(`${apiBaseUrl}/api/auth/bootstrap-admin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, login_name: loginName, email: email || null, password }),
      }).then(async (response) => {
        if (!response.ok) {
          const payload = await response.json().catch(() => null);
          throw new Error(payload?.detail ?? "Unable to create admin");
        }
      });
      setFormMode("login");
      setMessage("Admin created. Log in with the same credentials.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to create admin");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleLogout() {
    localStorage.removeItem(accessTokenKey);
    localStorage.removeItem(refreshTokenKey);
    setShowUserMenu(false);
    setProfile(null);
    setIsDashboardReady(false);
    setAuthState("guest");
    setMessage("Signed out.");
  }

  function resetCategoryForm() {
    setEditingCategoryId(null);
    setCategoryName("");
    setCategoryCode("");
    setCategoryIsActive(true);
  }

  function startCategoryEntry(category?: Category) {
    if (category) {
      setEditingCategoryId(category.id);
      setCategoryName(category.name);
      setCategoryCode(category.code ?? "");
      setCategoryIsActive(category.is_active);
    } else {
      resetCategoryForm();
    }
    setCategoryPageMode("entry");
  }

  function resetPackageForm() {
    setEditingPackageId(null);
    setPackageName("");
    setPackageType("");
    setPackagePrice("0");
    setPackageCategoryId("");
    setPackageIsActive(true);
  }

  function startPackageEntry(item?: Package) {
    if (item) {
      setEditingPackageId(item.id);
      setPackageName(item.name);
      setPackageType(item.package_type ?? "");
      setPackagePrice(String(item.default_price));
      setPackageCategoryId(String(item.category_id));
      setPackageIsActive(item.is_active);
    } else {
      resetPackageForm();
    }
    setPackagePageMode("entry");
  }

  function resetMemberForm() {
    setEditingMemberId(null);
    setMemberCode("");
    setMemberName("");
    setMemberFatherName("");
    setMemberMotherName("");
    setMemberCell("");
    setMemberEmail("");
    setMemberPresentAddress("");
    setMemberPermanentAddress("");
    setMemberNationalId("");
    setMemberPlotNo("");
    setMemberPlotCount("1");
    setMemberCategoryId("");
    setMemberClass("General");
    setMemberIsActive(true);
    setNomineeName("");
    setNomineeCell("");
  }

  async function startMemberEntry(member?: MemberListItem) {
    if (!member) {
      resetMemberForm();
      setMemberPageMode("entry");
      return;
    }

    const accessToken = token();
    if (!accessToken) return;
    const detail = await apiRequest<MemberDetail>(`/api/members/${member.id}`, accessToken);
    setEditingMemberId(detail.id);
    setMemberCode(detail.member_code);
    setMemberName(detail.full_name);
    setMemberFatherName(detail.father_name ?? "");
    setMemberMotherName(detail.mother_name ?? "");
    setMemberCell(detail.cell_no ?? "");
    setMemberEmail(detail.email ?? "");
    setMemberPresentAddress(detail.present_address ?? "");
    setMemberPermanentAddress(detail.permanent_address ?? "");
    setMemberNationalId(detail.national_id ?? "");
    setMemberPlotNo((detail.plot_no ?? detail.member_id_text ?? "").replace(/^Reg-/i, ""));
    setMemberPlotCount(String(detail.plot_count ?? 1));
    setMemberCategoryId(detail.category_id ? String(detail.category_id) : "");
    setMemberClass(detail.member_class ?? "General");
    setMemberIsActive(detail.is_active);
    setNomineeName(detail.nominee_name ?? "");
    setNomineeCell(detail.nominee_cell ?? "");
    setSelectedMember(detail);
    setMemberPageMode("entry");
  }

  async function handleCategorySubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      const wasEditing = editingCategoryId !== null;
      await apiRequest<Category>(editingCategoryId ? `/api/categories/${editingCategoryId}` : "/api/categories", accessToken, {
        method: editingCategoryId ? "PUT" : "POST",
        body: JSON.stringify({ name: categoryName, code: categoryCode || null, is_active: categoryIsActive }),
      });
      resetCategoryForm();
      setCategoryPageMode("view");
      await loadWorkspace();
      showSuccess(wasEditing ? "Category saved successfully." : "Category saved successfully.");
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to save category");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handlePackageSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      const wasEditing = editingPackageId !== null;
      await apiRequest<Package>(editingPackageId ? `/api/packages/${editingPackageId}` : "/api/packages", accessToken, {
        method: editingPackageId ? "PUT" : "POST",
        body: JSON.stringify({
          category_id: Number(packageCategoryId),
          name: packageName,
          package_type: packageType || null,
          default_price: Number(packagePrice),
          is_active: packageIsActive,
        }),
      });
      resetPackageForm();
      setPackagePageMode("view");
      await loadWorkspace();
      showSuccess(wasEditing ? "Package saved successfully." : "Package saved successfully.");
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to save package");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleMemberSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const accessToken = token();
    if (!accessToken) return;
    const normalizedPlotNo = memberPlotNo.trim().replace(/^Reg[\s\-_:]*/i, "").trim();
    const normalizedPhone = memberCell.trim();
    const normalizedNomineePhone = nomineeCell.trim();
    if (normalizedPhone && !/^\d+$/.test(normalizedPhone)) {
      showError("Phone number must contain digits only.");
      return;
    }
    if (normalizedNomineePhone && !/^\d+$/.test(normalizedNomineePhone)) {
      showError("Nominee phone number must contain digits only.");
      return;
    }
    const normalizedPlotCount = Math.max(Number(memberPlotCount || 1), 1);
    setIsSubmitting(true);
    try {
      const wasEditing = editingMemberId !== null;
      const payload = {
        member_code: memberCode,
        member_id_text: normalizedPlotNo || null,
        plot_no: normalizedPlotNo || null,
        plot_count: normalizedPlotCount,
        full_name: memberName,
        father_name: memberFatherName || null,
        mother_name: memberMotherName || null,
        present_address: memberPresentAddress || null,
        permanent_address: memberPermanentAddress || null,
        cell_no: normalizedPhone || null,
        email: memberEmail || null,
        national_id: memberNationalId || null,
        category_id: memberCategoryId ? Number(memberCategoryId) : null,
        member_class: memberClass || null,
        is_active: memberIsActive,
        nominee: nomineeName || normalizedNomineePhone ? { nominee_name: nomineeName || null, nominee_cell: normalizedNomineePhone || null } : null,
      };
      const saved = await apiRequest<MemberDetail>(editingMemberId ? `/api/members/${editingMemberId}` : "/api/members", accessToken, {
        method: editingMemberId ? "PUT" : "POST",
        body: JSON.stringify(payload),
      });
      resetMemberForm();
      setMemberPageMode("view");
      await loadWorkspace(saved.id);
      showSuccess(wasEditing ? "Member saved successfully." : "Member saved successfully.");
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to save member");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleMemberSelect(memberId: number) {
    const accessToken = token();
    if (!accessToken) return;
    const detail = await apiRequest<MemberDetail>(`/api/members/${memberId}`, accessToken);
    setSelectedMember(detail);
  }

  async function handlePackageAssignmentSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      await apiRequest<MemberPackageAssignment>(`/api/members/${assignMemberId}/packages`, accessToken, {
        method: "POST",
        body: JSON.stringify({
          package_id: Number(assignPackageId),
          assigned_on: assignDate,
          ended_on: null,
          is_active: true,
        }),
      });
      setAssignMemberId("");
      setAssignPackageId("");
      setAssignDate("");
      await loadWorkspace(Number(assignMemberId));
      showSuccess("Package assigned successfully.");
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to assign package");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handlePeriodSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      await apiRequest<BillingPeriod>("/api/billing/periods", accessToken, {
        method: "POST",
        body: JSON.stringify({
          year: Number(periodYear),
          month: Number(periodMonth),
          starts_on: periodStart,
          ends_on: periodEnd,
        }),
      });
      setPeriodStart("");
      setPeriodEnd("");
      setWorkspaceTab("billing");
      await refreshBillingWorkspace();
      showSuccess("Billing period saved successfully.");
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to save billing period");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleBillingGeneration(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      await apiRequest<Charge[]>("/api/billing/generate", accessToken, {
        method: "POST",
        body: JSON.stringify({ billing_period_id: Number(generationPeriodId), charge_type: "monthly" }),
      });
      setGenerationPeriodId("");
      await refreshBillingWorkspace();
      showSuccess("Billing generated successfully.");
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to generate billing");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleReceiptSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      await apiRequest<Receipt>("/api/billing/receipts", accessToken, {
        method: "POST",
        body: JSON.stringify({
          member_id: Number(receiptMemberId),
          payment_date: receiptDate,
          notes: null,
          discount_amount: Number(receiptDiscount || 0),
          lines: [{ charge_id: Number(receiptChargeId), amount: Number(receiptAmount) }],
        }),
      });
      setReceiptMemberId("");
      setReceiptChargeId("");
      setReceiptAmount("");
      setReceiptDate("");
      setReceiptDiscount("0");
      await refreshBillingWorkspace();
      await refreshAccountingWorkspace();
      showSuccess("Receipt saved successfully.");
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to post receipt");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleBillingHeadSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      const wasEditing = editingBillingHeadId !== null;
      await apiRequest<BillingHead>(editingBillingHeadId ? `/api/billing/heads/${editingBillingHeadId}` : "/api/billing/heads", accessToken, {
        method: editingBillingHeadId ? "PUT" : "POST",
        body: JSON.stringify({
          head_name: billingHeadName,
          head_type: billingHeadType,
          billing_mode: billingHeadType === "Period" ? "Mandatory" : billingHeadMode,
          fee_amount: Number(billingHeadFee),
          effective_from_month: billingHeadType === "Period" ? Number(billingHeadEffectiveDate.slice(5, 7)) : null,
          effective_from_year: billingHeadType === "Period" ? Number(billingHeadEffectiveDate.slice(0, 4)) : null,
          effective_from_date: billingHeadType === "Period" ? billingHeadEffectiveDate : null,
          effective_to_date: billingHeadType === "Period" ? (billingHeadEffectiveToDate || null) : null,
          is_active: true,
        }),
      });
      setBillingHeadName("");
      setBillingHeadMode("Mandatory");
      setBillingHeadFee("500");
      setBillingHeadType("Period");
      setBillingHeadEffectiveDate("2018-01-01");
      setBillingHeadEffectiveToDate("");
      setEditingBillingHeadId(null);
      setWorkspaceTab("billing-heads-view");
      await refreshBillingWorkspace();
      showSuccess(wasEditing ? "Billing head saved successfully." : "Billing head saved successfully.");
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to save billing head");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleBillingMappingSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      await apiRequest<BillingHeadMapping>("/api/billing/head-mappings", accessToken, {
        method: "POST",
        body: JSON.stringify({ billing_head_id: Number(mappingHeadId), coa_id: Number(mappingCoaId), is_active: true }),
      });
      setMappingHeadId("");
      setMappingCoaId("");
      setWorkspaceTab("billing-mappings-view");
      await refreshBillingWorkspace();
      showSuccess("Billing head mapped successfully.");
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to save mapping");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleLoadMemberDues() {
    const accessToken = token();
    if (!accessToken || !invoiceMemberId) return;
    setIsSubmitting(true);
    try {
      const dues = await apiRequest<BillingDueLine[]>(`/api/billing/members/${invoiceMemberId}/dues`, accessToken);
      setBillingDueLines(dues);
      setInvoiceReceipts(Object.fromEntries(dues.map((line, index) => [`${line.billing_head_id}-${line.period_date ?? "one"}-${index}`, "0"])));
      showStatus(`${dues.length} dues loaded month-wise.`, "info");
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to load dues");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function openInvoiceReport(invoice: BillingInvoice) {
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      const freshInvoice = await apiRequest<BillingInvoice>(`/api/billing/invoices/${invoice.id}`, accessToken);
      setInvoiceReport(freshInvoice);
      setShowInvoiceReport(true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to open invoice report");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDeleteInvoice(invoiceId: number) {
    const { value: reason } = await Swal.fire({
      title: "Void Invoice",
      text: "Are you sure you want to delete/void this invoice? Please enter a reason:",
      input: "text",
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Yes, delete it",
      confirmButtonColor: "#f06548",
      cancelButtonText: "Cancel",
      inputValidator: (value) => {
        if (!value || value.trim() === "") {
          return "You need to provide a reason!";
        }
      }
    });

    if (!reason) return; // User cancelled
    
    const accessToken = token();
    if (!accessToken) return;
    
    try {
      await apiRequest<BillingInvoice>(`/api/billing/invoices/${invoiceId}/cancel`, accessToken, {
        method: "POST",
        body: JSON.stringify({ cancel_reason: reason.trim() }),
      });
      
      // Reload the datatable to show it's deleted/cancelled
      const tableElement = previousBillsTableRef.current;
      if (tableElement && getJQuery()?.fn?.DataTable && getJQuery().fn.DataTable.isDataTable(tableElement)) {
        getJQuery()(tableElement).DataTable().ajax.reload(null, false);
      }
      
      // Also reload dues just in case
      void handleLoadMemberDues();
      void Swal.fire("Deleted!", "Invoice successfully deleted and archived!", "success");
    } catch (error) {
      console.error(error);
      const msg = error instanceof Error ? error.message : "An error occurred while deleting the invoice.";
      void Swal.fire("Failed!", `Failed to delete invoice: ${msg}`, "error");
    }
  }

  async function openInvoiceReportById(invoiceId: number) {
    const accessToken = token();
    if (!accessToken) return;
    const freshInvoice = await apiRequest<BillingInvoice>(`/api/billing/invoices/${invoiceId}`, accessToken);
    setInvoiceReport(freshInvoice);
    setShowInvoiceReport(true);
  }

  async function printInvoiceById(invoiceId: number) {
    const accessToken = token();
    if (!accessToken) return;
    const freshInvoice = await apiRequest<BillingInvoice>(`/api/billing/invoices/${invoiceId}`, accessToken);
    printInvoiceReport(freshInvoice);
  }

  function printInvoiceReport(invoice: BillingInvoice | null = invoiceReport) {
    if (!invoice) return;
    const member = members.find((item) => item.id === invoice.member_id);
    const reportLogoUrl = `${window.location.origin}/makan-logo-3.png`;
    const escapeHtml = (value: string | number | null | undefined) =>
      String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    const rows = invoice.details
      .map(
        (detail, index) => `
          <tr>
            <td>${index + 1}</td>
            <td>${escapeHtml(detail.head_name_snapshot)}</td>
            <td>${escapeHtml(detail.period_display ?? "-")}</td>
            <td class="right">${money(detail.fee_amount)}</td>
            <td class="right">${money(detail.receive_amount)}</td>
            <td class="right">${money(detail.due_amount)}</td>
          </tr>`,
      )
      .join("");
    const printWindow = window.open("about:blank", "_blank", "width=980,height=720");
    if (!printWindow) {
      setMessage("Allow browser popups to print the invoice.");
      return;
    }
    printWindow.document.write(`
      <!doctype html>
      <html>
        <head>
          <title>${escapeHtml(invoice.invoice_no)}</title>
          <style>
            * { box-sizing: border-box; }
            body { margin: 0; background: #fff; color: #111827; font-family: Arial, Helvetica, sans-serif; font-size: 13px; }
            .sheet { width: 210mm; min-height: 297mm; margin: 0 auto; padding: 16mm 14mm; }
            .header { border-bottom: 2px solid #111827; padding-bottom: 18px; }
            .report-logo { display: block; width: 100%; max-height: 118px; object-fit: contain; margin-bottom: 14px; }
            .title-row, .meta, .summary, .signatures { display: flex; justify-content: space-between; gap: 24px; }
            .brand { font-size: 24px; font-weight: 800; }
            .muted { color: #6b7280; }
            .title { margin: 10px 0 4px; font-size: 30px; font-weight: 800; text-align: right; }
            .badge { display: inline-block; padding: 5px 10px; border-radius: 4px; background: ${invoice.total_due_amount <= 0 ? "#dcfce7" : "#fef3c7"}; color: ${invoice.total_due_amount <= 0 ? "#166534" : "#92400e"}; font-weight: 700; }
            .meta { margin: 22px 0; padding: 14px; border: 1px solid #e5e7eb; background: #f8fafc; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #d1d5db; padding: 8px; vertical-align: top; }
            th { background: #eef2f7; text-align: left; }
            .right { text-align: right; }
            .summary { align-items: flex-start; margin-top: 22px; }
            .note { max-width: 420px; color: #4b5563; }
            .totals { width: 340px; border: 1px solid #e5e7eb; }
            .totals div { display: flex; justify-content: space-between; padding: 9px 12px; border-bottom: 1px solid #e5e7eb; }
            .totals div:last-child { border-bottom: 0; }
            .grand { background: #111827; color: #fff; font-weight: 800; }
            .signatures { margin-top: 54px; }
            .signatures div { width: 30%; text-align: center; color: #374151; }
            .signatures span { display: block; border-top: 1px solid #111827; margin-bottom: 8px; }
            @page { size: A4; margin: 0; }
            @media print { .sheet { margin: 0; } }
          </style>
        </head>
        <body>
          <main class="sheet">
            <section class="header">
              <img class="report-logo" src="${reportLogoUrl}" alt="Darul Mohan Plot Owners Society" />
              <div class="title-row">
                <div>
                  <div class="brand">Billing invoice and money receipt</div>
                  <div class="muted">Makan Society</div>
                </div>
                <div>
                  <span class="badge">${invoice.total_due_amount <= 0 ? "Paid" : invoice.total_receive_amount > 0 ? "Partial" : "Due"}</span>
                  <div class="title">Invoice</div>
                  <strong>${escapeHtml(invoice.invoice_no)}</strong>
                </div>
              </div>
            </section>
            <section class="meta">
              <div>
                Bill To: ${escapeHtml(invoice.member_name)}<br />
                Plot No: ${escapeHtml(invoice.plot_no || "")}<br />
                Member ID: ${escapeHtml(invoice.member_code || "")}
              </div>
              <div class="right">
                <span class="muted">Invoice Date</span><br />
                <strong>${shortDate(invoice.invoice_date)}</strong><br />
                Generated: ${shortDate(invoice.created_at)}
              </div>
            </section>
            <table>
              <thead>
                <tr><th style="width:44px">SL</th><th>Billing Head</th><th>Period</th><th class="right">Fee</th><th class="right">Received</th><th class="right">Due</th></tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
            <section class="summary">
              <div class="note">
                <strong>Note</strong>
                <p>This invoice is generated from saved billing data. Old invoice values remain unchanged after setup edits.</p>
              </div>
              <div class="totals">
                <div><span>Subtotal</span><strong>${money(invoice.subtotal_amount)}</strong></div>
                <div><span>Discount</span><strong>${money(invoice.discount_amount)}</strong></div>
                <div><span>Net Amount</span><strong>${money(invoice.net_amount)}</strong></div>
                <div><span>Received</span><strong>${money(invoice.total_receive_amount)}</strong></div>
                <div class="grand"><span>Due</span><strong>${money(invoice.member_outstanding_due)}</strong></div>
              </div>
            </section>
            <section class="signatures">
              <div><span></span>Prepared By<br/>User Name: ${escapeHtml(profile?.username || "")}</div>
              <div><span></span>Received By</div>
              <div><span></span>Authorized Signature</div>
            </section>
          </main>
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    const printAfterLogo = () => window.setTimeout(() => printWindow.print(), 150);
    const logo = printWindow.document.querySelector(".report-logo") as HTMLImageElement | null;
    if (!logo || logo.complete) {
      printAfterLogo();
    } else {
      logo.onload = printAfterLogo;
      logo.onerror = printAfterLogo;
    }
  }

  function formatReportCell(key: string, value: unknown) {
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

  function reportViewerTitle() {
    if (memberStatementReport) return `Member Statement - ${memberStatementReport.member_code}`;
    if (memberInformationDetailReport) return `Member Detail - ${memberInformationDetailReport.member_info.member_code}`;
    if (receiptReport) return `Receipt Detail - ${receiptReport.receipt_no}`;
    if (incomeExpenseReport) return "Income And Expense Report";
    if (currentPagedReport) return currentPagedReport.title;
    if (currentReport) return currentReport.title;
    return "Report Viewer";
  }

  function reportViewerSubtitle() {
    if (memberStatementReport) {
      return `${memberStatementReport.member_name}${memberStatementReport.plot_no ? ` | Plot ${memberStatementReport.plot_no}` : ""}`;
    }
    if (memberInformationDetailReport) {
      return `${memberInformationDetailReport.member_info.full_name}${memberInformationDetailReport.member_info.plot_no ? ` | Plot ${memberInformationDetailReport.member_info.plot_no}` : ""}`;
    }
    if (receiptReport) return shortDate(receiptReport.payment_date);
    if (incomeExpenseReport) return `${incomeExpenseReport.from_date ?? "Start"} to ${incomeExpenseReport.to_date ?? "Today"}`;
    if (currentPagedReport) return `${currentPagedReport.total} row${currentPagedReport.total === 1 ? "" : "s"} available`;
    if (currentReport) return `${currentReport.row_count} row${currentReport.row_count === 1 ? "" : "s"} generated`;
    return "";
  }

  function escapePrintHtml(value: unknown) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function buildPaginatedTableReportMarkup(report: ReportEnvelope | PagedReportEnvelope) {
    const isPagedReport = "items" in report;
    const sourceRows = isPagedReport ? report.items : report.rows;
    const columns = sourceRows.length > 0 ? Object.keys(sourceRows[0]) : [];
    const rowsPerPage = 22;
    const pageChunks: Array<typeof sourceRows> = [];
    if (isPagedReport) {
      pageChunks.push(sourceRows);
    } else {
      for (let index = 0; index < sourceRows.length; index += rowsPerPage) {
        pageChunks.push(sourceRows.slice(index, index + rowsPerPage));
      }
    }
    if (pageChunks.length === 0) pageChunks.push([]);

    const totalPages = isPagedReport ? Math.max(1, Math.ceil(report.total / Math.max(report.limit, 1))) : pageChunks.length;
    const activePage = isPagedReport ? Math.max(1, Math.floor(report.offset / Math.max(report.limit, 1)) + 1) : reportViewerPage;
    const totalsMarkup = Object.entries(report.totals)
      .map(
        ([key, value]) => `
          <div class="report-meta-card">
            <span class="text-muted">${escapePrintHtml(key.replace(/_/g, " "))}</span>
            <strong>${escapePrintHtml(formatReportCell(key, value))}</strong>
          </div>
        `,
      )
      .join("");

    return pageChunks
      .map((rows, pageIndex) => {
        const rowMarkup = rows.length
          ? rows
              .map(
                (row) => `
                  <tr>
                    ${columns
                      .map((column) => {
                        const alignClass = ["amount", "bill", "paid", "due", "collection", "discount", "subtotal", "total", "net"].some((token) =>
                          column.toLowerCase().includes(token),
                        )
                          ? "text-end"
                          : "";
                        return `<td class="${alignClass}">${escapePrintHtml(formatReportCell(column, row[column]))}</td>`;
                      })
                      .join("")}
                  </tr>
                `,
              )
              .join("")
          : `<tr><td colspan="${Math.max(columns.length, 1)}" class="empty-cell">No rows returned for this filter.</td></tr>`;

        return `
          <section class="print-page">
            <div class="print-page-inner">
              <div class="report-sheet-header">
                <img src="/makan-logo-3.png" alt="Darul Mohan Plot Owners Society" class="report-logo" />
                <div class="page-head">
                  <div>
                    <div class="section-title">Report Viewer</div>
                    <div class="text-muted">Makan Society</div>
                  </div>
                  <div class="text-end">
                    <h2 class="report-title">${escapePrintHtml(report.title)}</h2>
                    <div class="text-muted">Generated ${escapePrintHtml(shortDate(report.generated_at))}</div>
                    <div class="page-number">Page ${isPagedReport ? activePage : pageIndex + 1} of ${totalPages}</div>
                  </div>
                </div>
              </div>
              ${
                pageIndex === 0
                  ? `
                <div class="report-filter-grid">
                  <div class="report-meta-card">
                    <span class="text-muted">Report Type</span>
                    <strong>${escapePrintHtml(report.report_type)}</strong>
                  </div>
                  <div class="report-meta-card">
                    <span class="text-muted">Rows</span>
                    <strong>${escapePrintHtml(isPagedReport ? report.total : report.row_count)}</strong>
                  </div>
                  ${Object.entries(report.applied_filters ?? {})
                    .map(
                      ([key, value]) => `
                    <div class="report-meta-card">
                      <span class="text-muted">${escapePrintHtml(key.replace(/_/g, " "))}</span>
                      <strong>${escapePrintHtml(value)}</strong>
                    </div>
                  `,
                    )
                    .join("")}
                  ${totalsMarkup}
                </div>
              `
                  : ""
              }
              <table>
                <thead>
                  <tr>
                    ${columns.map((column) => `<th>${escapePrintHtml(column.replace(/_/g, " "))}</th>`).join("")}
                  </tr>
                </thead>
                <tbody>
                  ${rowMarkup}
                </tbody>
              </table>
            </div>
          </section>
        `;
      })
      .join("");
  }

  function buildPaginatedMemberStatementMarkup(report: SingleMemberStatementReport) {
    const dueRowsPerPage = 18;
    const paymentRowsPerPage = 20;
    const dueChunks: Array<typeof report.due_history> = [];
    const paymentChunks: Array<typeof report.payment_history> = [];

    for (let index = 0; index < report.due_history.length; index += dueRowsPerPage) {
      dueChunks.push(report.due_history.slice(index, index + dueRowsPerPage));
    }
    for (let index = 0; index < report.payment_history.length; index += paymentRowsPerPage) {
      paymentChunks.push(report.payment_history.slice(index, index + paymentRowsPerPage));
    }
    if (dueChunks.length === 0) dueChunks.push([]);
    if (paymentChunks.length === 0) paymentChunks.push([]);

    const pageEntries: Array<{
      section: "due" | "payment";
      rows: SingleMemberStatementReport["due_history"] | SingleMemberStatementReport["payment_history"];
      firstInSection: boolean;
    }> = [
      ...dueChunks.map((rows, index) => ({ section: "due" as const, rows, firstInSection: index === 0 })),
      ...paymentChunks.map((rows, index) => ({ section: "payment" as const, rows, firstInSection: index === 0 })),
    ];

    return pageEntries
      .map((entry, pageIndex) => {
        const reportTable =
          entry.section === "due"
            ? `
              <h3 class="subsection-title">Outstanding Dues By Period</h3>
              <table>
                <thead>
                  <tr>
                    <th>Billing Head</th>
                    <th>Period</th>
                    <th class="text-end">Bill</th>
                    <th class="text-end">Paid</th>
                    <th class="text-end">Due</th>
                  </tr>
                </thead>
                <tbody>
                  ${
                    entry.rows.length
                      ? (entry.rows as SingleMemberStatementReport["due_history"])
                          .map(
                            (item) => `
                          <tr>
                            <td>${escapePrintHtml(item.head_name)}</td>
                            <td>${escapePrintHtml(item.period_display ?? "One Time")}</td>
                            <td class="text-end">${escapePrintHtml(money(item.total_bill))}</td>
                            <td class="text-end">${escapePrintHtml(money(item.paid_amount))}</td>
                            <td class="text-end">${escapePrintHtml(money(item.due_amount))}</td>
                          </tr>
                        `,
                          )
                          .join("")
                      : `<tr><td colspan="5" class="empty-cell">No outstanding dues found.</td></tr>`
                  }
                </tbody>
              </table>
            `
            : `
              <h3 class="subsection-title">Payment History</h3>
              <table>
                <thead>
                  <tr>
                    <th>Receipt No</th>
                    <th>Date</th>
                    <th class="text-end">Paid</th>
                    <th class="text-end">Discount</th>
                  </tr>
                </thead>
                <tbody>
                  ${
                    entry.rows.length
                      ? (entry.rows as SingleMemberStatementReport["payment_history"])
                          .map(
                            (item) => `
                          <tr>
                            <td>${escapePrintHtml(item.receipt_no)}</td>
                            <td>${escapePrintHtml(shortDate(item.payment_date))}</td>
                            <td class="text-end">${escapePrintHtml(money(item.amount))}</td>
                            <td class="text-end">${escapePrintHtml(money(item.discount_amount))}</td>
                          </tr>
                        `,
                          )
                          .join("")
                      : `<tr><td colspan="4" class="empty-cell">No payment history found.</td></tr>`
                  }
                </tbody>
              </table>
            `;

        return `
          <section class="print-page">
            <div class="print-page-inner">
              <div class="report-sheet-header">
                <img src="/makan-logo-3.png" alt="Darul Mohan Plot Owners Society" class="report-logo" />
                <div class="page-head">
                  <div>
                    <div class="section-title">Single Member Due And Paid Statement</div>
                    <div class="text-muted">Makan Society</div>
                  </div>
                  <div class="text-end">
                    <h2 class="report-title">${escapePrintHtml(report.member_code)}</h2>
                    <div>${escapePrintHtml(report.member_name)}</div>
                    ${report.plot_no ? `<div class="text-muted">Plot No: ${escapePrintHtml(report.plot_no)}</div>` : ""}
                    <div class="page-number">Page ${pageIndex + 1} of ${pageEntries.length}</div>
                  </div>
                </div>
              </div>
              ${
                pageIndex === 0
                  ? `
                <div class="report-summary-grid">
                  <div class="statement-summary-card">
                    <span class="text-muted">Total Paid</span>
                    <strong>${escapePrintHtml(money(report.paid_amount))}</strong>
                  </div>
                  <div class="statement-summary-card highlight">
                    <span class="text-muted">Outstanding Due</span>
                    <strong>${escapePrintHtml(money(report.due_amount))}</strong>
                  </div>
                  <div class="statement-summary-card highlight">
                    <span class="text-muted">Outstanding Bill Total</span>
                    <strong>${escapePrintHtml(money(report.total_bill))}</strong>
                  </div>
                </div>
                ${
                  Object.entries(report.applied_filters ?? {}).length
                    ? `
                  <div class="report-filter-grid">
                    ${Object.entries(report.applied_filters ?? {})
                      .map(
                        ([key, value]) => `
                      <div class="report-meta-card">
                        <span class="text-muted">${escapePrintHtml(key.replace(/_/g, " "))}</span>
                        <strong>${escapePrintHtml(value)}</strong>
                      </div>
                    `,
                      )
                      .join("")}
                  </div>
                `
                    : ""
                }
              `
                  : ""
              }
              ${reportTable}
            </div>
          </section>
        `;
      })
      .join("");
  }

  function printReportViewer() {
    const printArea = document.getElementById("report-viewer-print-area");
    if (!printArea) {
      setMessage("Load a report first.");
      return;
    }
    const printWindow = window.open("about:blank", "_blank", "width=980,height=720");
    if (!printWindow) {
      setMessage("Allow browser popups to print the report.");
      return;
    }
    const title = reportViewerTitle();
    const printableMarkup = currentReport || currentPagedReport
      ? buildPaginatedTableReportMarkup(currentPagedReport ?? currentReport!)
      : memberStatementReport
        ? buildPaginatedMemberStatementMarkup(memberStatementReport)
        : `<main class="sheet">${printArea.innerHTML}</main>`;
    printWindow.document.write(`
      <!doctype html>
      <html>
        <head>
          <title>${title}</title>
          <base href="${window.location.origin}" />
          <style>
            * { box-sizing: border-box; }
            body { margin: 0; background: #fff; color: #111827; font-family: Arial, Helvetica, sans-serif; font-size: 13px; }
            .sheet { width: 210mm; min-height: 297mm; margin: 0 auto; padding: 16mm 14mm; }
            .print-page { width: 210mm; min-height: 297mm; margin: 0 auto; padding: 14mm 12mm; page-break-after: always; }
            .print-page:last-child { page-break-after: auto; }
            .print-page-inner { min-height: calc(297mm - 28mm); display: flex; flex-direction: column; }
            .page-head { display: flex; justify-content: space-between; gap: 18px; }
            .section-title { font-weight: 700; }
            .report-title { margin: 0 0 4px; font-size: 30px; font-weight: 800; }
            .page-number { margin-top: 6px; font-weight: 700; }
            .subsection-title { margin: 8px 0 0; font-size: 20px; font-weight: 700; }
            .report-logo { display: block; width: 100%; max-height: 118px; object-fit: contain; margin-bottom: 14px; }
            .invoice-report-sheet, .report-sheet { width: 100%; }
            .invoice-report-header, .report-sheet-header { border-bottom: 2px solid #111827; padding-bottom: 18px; margin-bottom: 18px; }
            .invoice-report-meta, .report-meta, .report-summary-grid, .invoice-report-summary, .invoice-report-signatures, .report-filter-grid { display: flex; justify-content: space-between; gap: 18px; flex-wrap: wrap; }
            .report-filter-grid { margin: 14px 0 18px; }
            .report-meta-card, .statement-summary-card, .invoice-report-note { flex: 1 1 180px; border: 1px solid #e5e7eb; background: #f8fafc; padding: 12px 14px; border-radius: 8px; }
            .statement-summary-card strong, .report-meta-card strong { display: block; font-size: 18px; margin-top: 6px; }
            .invoice-report-totals, .statement-summary-card.highlight { border: 1px solid #dbeafe; background: #eff6ff; }
            table { width: 100%; border-collapse: collapse; margin-top: 16px; }
            th, td { border: 1px solid #d1d5db; padding: 8px; vertical-align: top; text-align: left; }
            th { background: #eef2f7; }
            .text-end, .right { text-align: right; }
            .text-muted, .muted { color: #6b7280; }
            .empty-cell { text-align: center; color: #6b7280; padding: 24px 12px; }
            .badge { display: inline-block; padding: 5px 10px; border-radius: 4px; font-weight: 700; }
            .bg-success-subtle { background: #dcfce7; }
            .text-success { color: #166534; }
            .bg-warning-subtle { background: #fef3c7; }
            .text-warning { color: #92400e; }
            .bg-info-subtle { background: #dbeafe; }
            .text-info { color: #1d4ed8; }
            .report-panel { border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px; margin-top: 16px; }
            .report-panel.income { background: #f0fdf4; }
            .report-panel.expense { background: #fef2f2; }
            .net-banner { margin-top: 16px; padding: 12px 16px; border-radius: 10px; font-weight: 700; display: flex; justify-content: space-between; }
            .net-banner.positive { background: #dcfce7; color: #166534; }
            .net-banner.negative { background: #fee2e2; color: #991b1b; }
            @page { size: A4; margin: 0; }
          </style>
        </head>
        <body>
          ${printableMarkup}
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    window.setTimeout(() => printWindow.print(), 180);
  }

  function renderReportEnvelopeContent(report: ReportEnvelope | PagedReportEnvelope) {
    const isPagedReport = "items" in report;
    const rows = isPagedReport ? report.items : report.rows;
    const columns = rows.length > 0 ? Object.keys(rows[0]) : [];
    const pageSize = isPagedReport ? Math.max(report.limit, 1) : 15;
    const totalRows = isPagedReport ? report.total : report.row_count;
    const totalPages = Math.max(1, Math.ceil(totalRows / pageSize));
    const activePage = isPagedReport ? Math.max(1, Math.floor(report.offset / pageSize) + 1) : Math.min(reportViewerPage, totalPages);
    const startIndex = isPagedReport ? report.offset : (activePage - 1) * pageSize;
    const pagedRows = isPagedReport ? rows : rows.slice(startIndex, startIndex + pageSize);
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
              <div className="text-muted">Generated {shortDate(report.generated_at)}</div>
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
              <strong>{formatReportCell(key, value)}</strong>
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
                {pagedRows.map((row, index) => (
                  <tr key={`${report.report_type}-${startIndex + index}`}>
                    {columns.map((column) => (
                      <td
                        className={["amount", "bill", "paid", "due", "collection", "discount", "subtotal", "total", "net"].some((token) => column.toLowerCase().includes(token)) ? "text-end" : ""}
                        key={`${report.report_type}-${startIndex + index}-${column}`}
                      >
                        {formatReportCell(column, row[column])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <EmptyState label="No rows returned for this filter." />
          )}
        </div>
        {totalRows > pageSize ? (
          <div className="report-pagination-bar">
            <div className="report-pagination-summary">
              Showing {Math.min(startIndex + 1, totalRows)}-{Math.min(startIndex + pagedRows.length, totalRows)} of {totalRows}
            </div>
            <div className="report-pagination-controls">
              <button
                className="btn btn-outline-secondary btn-sm"
                disabled={activePage <= 1}
                onClick={() => setReportViewerPage((page) => Math.max(1, page - 1))}
                type="button"
              >
                Previous
              </button>
              <span className="report-pagination-current">Page {activePage} of {totalPages}</span>
              <button
                className="btn btn-outline-secondary btn-sm"
                disabled={activePage >= totalPages}
                onClick={() => setReportViewerPage((page) => Math.min(totalPages, page + 1))}
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

  function renderReceiptReportContent(report: ReceiptDetailReport) {
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

  function renderIncomeExpenseReportContent(report: IncomeExpenseComparisonReport) {
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

  function renderMemberStatementReportContent(report: SingleMemberStatementReport) {
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
                  {report.payment_history.length === 0 ? <EmptyState label="No payment history found." /> : null}
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
                  {report.due_history.length === 0 ? <EmptyState label="No outstanding dues found." /> : null}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  function renderMemberInformationDetailReportContent(report: MemberInformationDetailReport) {
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
                  {report.payment_history.length === 0 ? <EmptyState label="No payment history found." /> : null}
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
                  {report.due_history.length === 0 ? <EmptyState label="No dues found." /> : null}
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
                  {report.sms_history.length === 0 ? <EmptyState label="No SMS history found." /> : null}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  function renderReportViewerContent() {
    if (memberInformationDetailReport) return renderMemberInformationDetailReportContent(memberInformationDetailReport);
    if (memberStatementReport) return renderMemberStatementReportContent(memberStatementReport);
    if (receiptReport) return renderReceiptReportContent(receiptReport);
    if (incomeExpenseReport) return renderIncomeExpenseReportContent(incomeExpenseReport);
    if (currentPagedReport) return renderReportEnvelopeContent(currentPagedReport);
    if (currentReport) return renderReportEnvelopeContent(currentReport);
    return <EmptyState label="Load a report to preview it here." />;
  }

  function renderReportViewerModal() {
    if (!showReportViewer) return null;
    return (
      <>
        <div className="modal fade show d-block invoice-report-modal" tabIndex={-1}>
          <div className="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
            <div className="modal-content">
              <div className="modal-header invoice-report-actions">
                <div>
                  <h5 className="modal-title">{reportViewerTitle()}</h5>
                  <span className="text-muted">{reportViewerSubtitle()}</span>
                </div>
                <div className="d-flex gap-2">
                  <button className="btn btn-primary" onClick={printReportViewer} type="button">
                    <i className="ri-printer-line me-1" />
                    Print
                  </button>
                  <button className="btn-close" onClick={() => setShowReportViewer(false)} type="button" />
                </div>
              </div>
              <div className="modal-body invoice-report-print-area">
                <div id="report-viewer-print-area">{renderReportViewerContent()}</div>
              </div>
            </div>
          </div>
        </div>
        <div className="modal-backdrop fade show invoice-report-actions" />
      </>
    );
  }

  function handleAddManualBillingLine() {
    const head = billingHeads.find((item) => item.id === Number(manualBillingHeadId));
    if (!head) {
      showError("Select a billing head first.");
      return;
    }
    const plotCount = Math.max(Number(selectedInvoiceMember?.plot_count ?? 1), 1);
    const baseFeeAmount = head.head_type === "OneTime" && head.billing_mode === "Optional" ? Number(manualBillingFee || 0) : Number(head.fee_amount);
    const feeAmount = head.head_type === "Period" ? baseFeeAmount * plotCount : baseFeeAmount;
    if (feeAmount <= 0) {
      showError("Enter a valid fee amount.");
      return;
    }
    const periodDate = head.head_type === "Period" ? `${manualBillingPeriod}-01` : null;
    const periodDisplay = head.head_type === "Period" ? `${manualBillingPeriod.slice(5, 7)}-${manualBillingPeriod.slice(0, 4)}` : null;
    setBillingDueLines((current) => [
      ...current,
      {
        member_id: Number(invoiceMemberId || 0),
        billing_head_id: head.id,
        head_name: head.head_name,
        head_type: head.head_type,
        billing_mode: head.billing_mode,
        period_date: periodDate,
        period_display: periodDisplay,
        plot_count: plotCount,
        base_fee_amount: baseFeeAmount,
        fee_amount: feeAmount,
        paid_amount: 0,
        due_amount: feeAmount,
        coa_id_snapshot: null,
      },
    ]);
    setManualBillingHeadId("");
    setManualBillingFee("");
    showStatus(`${head.head_name} added to billing grid.`, "info");
  }

  async function handleInvoiceSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const accessToken = token();
    if (!accessToken || !invoiceMemberId) return;
    if (billingDueLines.length === 0) {
      showError("Load dues or add at least one billing head.");
      return;
    }
    if (billingSelectedLines.length === 0) {
      showError("Enter receive amount for at least one row.");
      return;
    }
    if (billingDiscount > billingSubtotal) {
      showError("Discount cannot exceed received subtotal.");
      return;
    }
    setIsSubmitting(true);
    try {
      const invoice = await apiRequest<BillingInvoice>("/api/billing/invoices", accessToken, {
        method: "POST",
        body: JSON.stringify({
          member_id: Number(invoiceMemberId),
          invoice_date: invoiceDate,
          discount_amount: Number(invoiceDiscount || 0),
          lines: billingSelectedLines.map((item) => ({
            billing_head_id: item.line.billing_head_id,
            period_date: item.line.period_date,
            fee_amount: item.line.due_amount,
            receive_amount: item.receive,
            discount_amount: 0,
          })),
        }),
      });
      setLastGeneratedInvoice(invoice);
      setInvoiceReport(invoice);
      setShowInvoiceReport(true);
      setBillingDueLines([]);
      setInvoiceReceipts({});
      setInvoiceDiscount("0");
      await refreshBillingWorkspace();
      showSuccess(`Invoice ${invoice.invoice_no} generated successfully.`);
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to generate invoice");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleAccountSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      const existingAccount = editingAccountId ? accounts.find((account) => account.id === editingAccountId) : null;
      await apiRequest<Account>(editingAccountId ? `/api/accounting/accounts/${editingAccountId}` : "/api/accounting/accounts", accessToken, {
        method: editingAccountId ? "PUT" : "POST",
        body: JSON.stringify({ code: accountCode, name: accountName, account_type: accountType, is_active: existingAccount?.is_active ?? true }),
      });
      setAccountCode("");
      setAccountName("");
      setAccountType("income");
      setEditingAccountId(null);
      await refreshAccountingWorkspace();
      setWorkspaceTab("coa-view");
      showSuccess("Account saved successfully.");
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to save account");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleAccountEdit(account: Account) {
    setEditingAccountId(account.id);
    setAccountCode(account.code);
    setAccountName(account.name);
    setAccountType(account.account_type);
    setWorkspaceTab("coa-entry");
  }

  async function handleAccountActiveChange(account: Account, isActive: boolean) {
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      await apiRequest<Account>(`/api/accounting/accounts/${account.id}`, accessToken, {
        method: "PUT",
        body: JSON.stringify({ code: account.code, name: account.name, account_type: account.account_type, is_active: isActive }),
      });
      await refreshAccountingWorkspace();
      showSuccess(isActive ? "Account activated successfully." : "Account inactivated successfully.");
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to update account");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleAccountDelete(accountId: number) {
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      await apiRequest<void>(`/api/accounting/accounts/${accountId}`, accessToken, { method: "DELETE" });
      await refreshAccountingWorkspace();
      showSuccess("Account deleted successfully.");
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to delete account");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleAddEntryToList(entryType: "income" | "expense", event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!entryAccountId) {
      setMessage("Select an account from chart of accounts first.");
      return;
    }
    const selectedAccount = accounts.find((account) => account.id === Number(entryAccountId));
    const amount = Number(entryAmount);
    if (!selectedAccount || !amount || amount <= 0) {
      setMessage("Select account and enter a valid amount.");
      return;
    }
    setPendingEntries((current) => [
      ...current,
      {
        account_id: selectedAccount.id,
        account_label: `${selectedAccount.code} - ${selectedAccount.name}`,
        amount,
        remarks: entryRemarks || null,
      },
    ]);
    setEntryAccountId("");
    setEntryAccountSearch("");
    setEntryAmount("");
    setEntryMappedIncomeAmount(null);
    setEntryRemarks("");
    setMessage(`${entryType === "income" ? "Income" : "Expense"} line added to list.`);
  }

  async function loadMappedIncomeAmount(coaId: string, asOfDate: string, shouldApplyDefaultRemarks: boolean) {
    const accessToken = token();
    if (!accessToken) return;

    try {
      const pending = await apiRequest<IncomeTransferPendingItem[]>(
        `/api/accounting/income-transfer-pending?coa_id=${coaId}&as_of_date=${asOfDate}`,
        accessToken,
      );
      const total = pending.reduce((sum, item) => sum + Number(item.amount), 0);
      if (total > 0) {
        setEntryAmount(total.toFixed(2));
        setEntryMappedIncomeAmount(total);
        if (shouldApplyDefaultRemarks && !entryRemarks.trim()) {
          setEntryRemarks("Mapped billing collection transfer");
        }
      } else {
        setEntryAmount("");
        setEntryMappedIncomeAmount(null);
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to load mapped billing total");
    }
  }

  async function handleEntryAccountChange(value: string, entryType: "income" | "expense") {
    setEntryAccountId(value);
    setEntryMappedIncomeAmount(null);

    if (entryType !== "income" || !value) {
      if (entryType !== "income") {
        setEntryAmount("");
      }
      return;
    }

    await loadMappedIncomeAmount(value, entryDate, true);
  }

  async function handleSavePendingEntries(entryType: "income" | "expense") {
    const accessToken = token();
    if (!accessToken) return;
    if (pendingEntries.length === 0) {
      setMessage("Add at least one line before saving.");
      return;
    }
    setIsSubmitting(true);
    try {
      const voucher = await apiRequest<AccountingVoucher>(`/api/accounting/vouchers/${entryType}`, accessToken, {
        method: "POST",
        body: JSON.stringify({
          voucher_date: entryDate,
          remarks: entryVoucherRemarks || null,
          lines: pendingEntries.map((item) => ({ coa_id: item.account_id, amount: item.amount, remarks: item.remarks })),
        }),
      });
      setPendingEntries([]);
      setEntryMappedIncomeAmount(null);
      setEntryVoucherRemarks("");
      await refreshAccountingWorkspace();
      setWorkspaceTab(entryType === "income" ? "income-view" : "expense-view");
      showSuccess(`${entryType === "income" ? "Income" : "Expense"} saved successfully.`);
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to save accounting entry");
    } finally {
      setIsSubmitting(false);
    }
  }

  function printAccountingVoucher(voucher: AccountingVoucher) {
    const title = voucher.voucher_type === "income" ? "Receive Voucher" : "Payment Voucher";
    const rows = voucher.lines.map((line, index) => `<tr><td>${index + 1}</td><td>${line.coa_name ?? ""}</td><td>${line.remarks ?? ""}</td><td class="right">${money(line.amount)}</td></tr>`).join("");
    const reportLogoUrl = `${window.location.origin}/makan-logo-3.png`;
    const printWindow = window.open("about:blank", "_blank", "width=980,height=720");
    if (!printWindow) return;
    printWindow.document.write(`<!doctype html><html><head><title>${voucher.voucher_no}</title><style>body{font-family:Arial;margin:0;color:#111827}.sheet{width:210mm;min-height:297mm;margin:auto;padding:16mm 14mm}.head{border-bottom:2px solid #111827;padding-bottom:14px}.report-logo{display:block;width:100%;max-height:118px;object-fit:contain;margin-bottom:14px}.voucher-head{display:flex;justify-content:space-between;gap:20px}.title{text-align:right;font-size:28px;font-weight:800}table{width:100%;border-collapse:collapse;margin-top:22px}th,td{border:1px solid #d1d5db;padding:8px}th{background:#eef2f7}.right{text-align:right}.total{background:#111827;color:#fff;font-weight:800}.muted{color:#6b7280}.sign{display:flex;justify-content:space-between;margin-top:60px}.sign div{width:30%;text-align:center}.sign span{display:block;border-top:1px solid #111827;margin-bottom:8px}@page{size:A4;margin:0}</style></head><body><main class="sheet"><section class="head"><img class="report-logo" src="${reportLogoUrl}"/><div class="voucher-head"><div><strong>Accounting voucher report</strong><div class="muted">Makan Society</div></div><div><div class="title">${title}</div><strong>${voucher.voucher_no}</strong><br/>Date: ${shortDate(voucher.voucher_date)}</div></div></section><table><thead><tr><th>SL</th><th>COA</th><th>Remarks</th><th class="right">Amount</th></tr></thead><tbody>${rows}<tr class="total"><td colspan="3" class="right">Total</td><td class="right">${money(voucher.total_amount)}</td></tr></tbody></table><p>Remarks: ${voucher.remarks ?? ""}</p><section class="sign"><div><span></span>Prepared By</div><div><span></span>Checked By</div><div><span></span>Authorized Signature</div></section></main></body></html>`);
    printWindow.document.close();
    printWindow.focus();
    const printAfterLogo = () => window.setTimeout(() => printWindow.print(), 150);
    const logo = printWindow.document.querySelector(".report-logo") as HTMLImageElement | null;
    if (!logo || logo.complete) {
      printAfterLogo();
    } else {
      logo.onload = printAfterLogo;
      logo.onerror = printAfterLogo;
    }
  }

  async function openVoucherReportById(voucherId: number) {
    const accessToken = token();
    if (!accessToken) return;
    const voucher = await apiRequest<AccountingVoucher>(`/api/accounting/vouchers/item/${voucherId}`, accessToken);
    printAccountingVoucher(voucher);
  }

  async function printVoucherById(voucherId: number) {
    const accessToken = token();
    if (!accessToken) return;
    const voucher = await apiRequest<AccountingVoucher>(`/api/accounting/vouchers/item/${voucherId}`, accessToken);
    printAccountingVoucher(voucher);
  }

  async function handleEntryDelete(entryId: number) {
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      await apiRequest<void>(`/api/accounting/entries/${entryId}`, accessToken, { method: "DELETE" });
      await refreshAccountingWorkspace();
      showSuccess("Entry deleted successfully.");
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to delete entry");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function loadPagedReportPreview(accessToken: string, report: TableReportType, page: number) {
    const limit = 50;
    const offset = Math.max(page - 1, 0) * limit;
    const payload = await loadPagedTableReport(accessToken, report, reportQueryString, { limit, offset });
    setCurrentPagedReport(payload);
    setCurrentReport(null);
    setReceiptReport(null);
    setIncomeExpenseReport(null);
    setMemberStatementReport(null);
    setMemberInformationDetailReport(null);
    setShowReportViewer(true);
  }

  async function handleReportLoad(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const accessToken = token();
    if (!accessToken) return;
    if (reportType === "receipt-detail" && !reportReceiptId) {
      setMessage("Select a receipt first.");
      return;
    }
    if ((reportType === "member-statement" || reportType === "member-information-detail") && !reportMemberId) {
      setMessage("Select a member for this report.");
      return;
    }
    setIsSubmitting(true);
    try {
      setShowReportViewer(false);
      setReportViewerPage(1);
      setCurrentPagedReport(null);
      if (reportType === "income-expense") {
        const params = new URLSearchParams();
        if (reportFromDate) params.set("from_date", reportFromDate);
        if (reportToDate) params.set("to_date", reportToDate);
        const payload = await loadIncomeExpenseReport(accessToken, params);
        setIncomeExpenseReport(payload);
        setCurrentReport(null);
        setCurrentPagedReport(null);
        setReceiptReport(null);
        setMemberStatementReport(null);
        setMemberInformationDetailReport(null);
        setShowReportViewer(true);
        setMessage("Income expense report loaded.");
        return;
      }
      if (reportType === "receipt-detail") {
        const payload = await loadReceiptDetailReport(accessToken, reportReceiptId);
        setReceiptReport(payload);
        setCurrentReport(null);
        setCurrentPagedReport(null);
        setIncomeExpenseReport(null);
        setMemberStatementReport(null);
        setMemberInformationDetailReport(null);
        setShowReportViewer(true);
      } else if (reportType === "member-statement") {
        const payload = await loadMemberStatementReport(accessToken, reportQueryString);
        setMemberStatementReport(payload);
        setCurrentReport(null);
        setCurrentPagedReport(null);
        setReceiptReport(null);
        setIncomeExpenseReport(null);
        setMemberInformationDetailReport(null);
        setShowReportViewer(true);
      } else if (reportType === "member-information-detail") {
        const payload = await loadMemberInformationDetailReport(accessToken, reportQueryString);
        setMemberInformationDetailReport(payload);
        setCurrentReport(null);
        setCurrentPagedReport(null);
        setReceiptReport(null);
        setIncomeExpenseReport(null);
        setMemberStatementReport(null);
        setShowReportViewer(true);
      } else {
        await loadPagedReportPreview(accessToken, reportType as TableReportType, 1);
      }
      setMessage("Report loaded.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to load report");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function downloadAuthenticatedFile(path: string, fallbackFileName: string) {
    const accessToken = token();
    if (!accessToken) {
      setMessage("Please log in again.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(`${apiBaseUrl}${path}`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail ?? "Unable to download file");
      }

      const blob = await response.blob();
      const fileName = fileNameFromDisposition(response.headers.get("Content-Disposition"), fallbackFileName);
      const downloadUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);
      setMessage("Excel download started.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to download file");
    } finally {
      setIsSubmitting(false);
    }
  }

  function openReportExport(kind: "html" | "xlsx") {
    const exportableReports = new Set([
      "due-members",
      "collections",
      "income-detail",
      "expense-detail",
      "charges",
      "members",
      "total-collection",
      "total-due",
      "member-statement",
      "member-information-detail",
      "receipt-detail",
      "income-expense",
    ]);
    if (!exportableReports.has(reportType)) {
      setMessage("This report type is not available for export.");
      return;
    }
    const accessToken = token();
    if (!accessToken) return;
    const params = new URLSearchParams(reportQueryString);
    params.set("report_type", reportType);
    params.set("kind", kind === "html" ? "html" : "xlsx");
    if (reportType === "receipt-detail") {
      if (!reportReceiptId) {
        setMessage("Select a receipt first.");
        return;
      }
      params.set("receipt_id", reportReceiptId);
    }
    if ((reportType === "member-statement" || reportType === "member-information-detail") && !reportMemberId) {
      setMessage("Select a member first.");
      return;
    }
    void createReportExportJob(accessToken, params)
      .then((job) => {
        setActiveJobId(job.id);
        setActiveJobLabel(`Report export (${reportType})`);
        setMessage("Report export queued in the background.");
      })
      .catch((error) => {
        setMessage(error instanceof Error ? error.message : "Unable to queue report export");
      });
  }

  async function handleSmsTemplateSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      await apiRequest<SmsTemplate>(editingSmsTemplateId ? `/api/messaging/templates/${editingSmsTemplateId}` : "/api/messaging/templates", accessToken, {
        method: editingSmsTemplateId ? "PUT" : "POST",
        body: JSON.stringify({ name: smsTemplateName, body: smsTemplateBody, template_type: smsTemplateType || null }),
      });
      const wasEditingSelected = editingSmsTemplateId !== null && smsSelectedTemplateId === String(editingSmsTemplateId);
      setSmsTemplateName("");
      setSmsTemplateType("");
      setSmsTemplateBody("");
      setEditingSmsTemplateId(null);
      setShowSmsTemplateModal(false);
      await refreshMessagingWorkspace();
      if (wasEditingSelected) {
        setSmsMessageBody(smsTemplateBody);
      }
      showSuccess("SMS template saved successfully.");
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to save SMS template");
    } finally {
      setIsSubmitting(false);
    }
  }

  function openSmsTemplateModal(template?: SmsTemplate) {
    setEditingSmsTemplateId(template?.id ?? null);
    setSmsTemplateName(template?.name ?? "");
    setSmsTemplateType(template?.template_type ?? "");
    setSmsTemplateBody(template?.body ?? "");
    setShowSmsTemplateModal(true);
  }

  function buildSmsVariables(member: MemberListItem | null) {
    if (!member) {
      return {};
    }
    const dueAmount = dueByMemberId.get(member.id)?.total_due ?? 0;
    return {
      name: member.full_name,
      bill: dueAmount.toFixed(2),
      due: dueAmount.toFixed(2),
      member_code: member.member_code,
      phone: member.cell_no ?? "",
    };
  }

  function renderSmsPreview(member: MemberListItem | null) {
    const variables = buildSmsVariables(member);
    const source = selectedSmsTemplate?.body || smsMessageBody || "";
    return Object.entries(variables).reduce((rendered, [key, value]) => {
      return rendered.split(`{{${key}}}`).join(value).split(`(${key})`).join(value);
    }, source);
  }

  function toggleSmsMemberSelection(memberId: number) {
    setSmsSelectedMemberIds((current) =>
      current.includes(memberId) ? current.filter((item) => item !== memberId) : [...current, memberId],
    );
    const currentMember =
      (smsRecipientMembersQuery.data?.items ?? []).find((member) => member.id === memberId) ??
      (smsSingleMemberQuery.data && smsSingleMemberQuery.data.id === memberId
        ? {
            id: smsSingleMemberQuery.data.id,
            member_code: smsSingleMemberQuery.data.member_code,
            full_name: smsSingleMemberQuery.data.full_name,
            plot_no: smsSingleMemberQuery.data.plot_no,
            plot_count: smsSingleMemberQuery.data.plot_count,
            cell_no: smsSingleMemberQuery.data.cell_no,
            category_id: smsSingleMemberQuery.data.category_id,
            category_name: smsSingleMemberQuery.data.category_name,
            joined_on: smsSingleMemberQuery.data.joined_on,
            is_active: smsSingleMemberQuery.data.is_active,
          }
        : null);
    if (currentMember) {
      setSmsSelectedMembersData((current) => {
        const exists = current.some((member) => member.id === memberId);
        if (exists) return current.filter((member) => member.id !== memberId);
        return [...current, currentMember];
      });
    }
  }

  function toggleAllSmsMembers(checked: boolean) {
    const filteredIds = smsFilteredMembers.map((member) => member.id);
    setSmsSelectedMemberIds((current) => {
      if (checked) {
        return Array.from(new Set([...current, ...filteredIds]));
      }
      return current.filter((memberId) => !filteredIds.includes(memberId));
    });
  }

  async function handleSmsQueueSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      const selectedMember =
        smsSingleMemberQuery.data && smsMemberId
          ? {
              id: smsSingleMemberQuery.data.id,
              member_code: smsSingleMemberQuery.data.member_code,
              full_name: smsSingleMemberQuery.data.full_name,
              plot_no: smsSingleMemberQuery.data.plot_no,
              plot_count: smsSingleMemberQuery.data.plot_count,
              cell_no: smsSingleMemberQuery.data.cell_no,
              category_id: smsSingleMemberQuery.data.category_id,
              category_name: smsSingleMemberQuery.data.category_name,
              joined_on: smsSingleMemberQuery.data.joined_on,
              is_active: smsSingleMemberQuery.data.is_active,
            }
          : null;
      await apiRequest<SmsMessage>("/api/messaging/queue", accessToken, {
        method: "POST",
        body: JSON.stringify({
          member_id: smsMemberId ? Number(smsMemberId) : null,
          template_id: smsSelectedTemplateId ? Number(smsSelectedTemplateId) : null,
          recipient: smsRecipient || null,
          message_body: smsMessageBody || null,
          variables: buildSmsVariables(selectedMember),
          send_now: true,
        }),
      });
      setSmsMemberId("");
      setSmsRecipient("");
      setSmsSelectedTemplateId("");
      setSmsMessageBody("");
      await refreshMessagingWorkspace();
      setMessage("SMS queued.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to queue SMS");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleBulkSmsSend() {
    const accessToken = token();
    if (!accessToken) return;
    const selectedMembers = smsSelectedMembers.filter((member) => (member.cell_no ?? "").replace(/\D/g, "").length >= 11);
    if (selectedMembers.length === 0) {
      setMessage("Select at least one customer before sending SMS.");
      return;
    }
    if (!smsSelectedTemplateId && !smsMessageBody.trim()) {
      setMessage("Select a template or write a custom message first.");
      return;
    }

    setIsSubmitting(true);
    try {
      const job = await createBulkSmsJob(accessToken, {
        member_ids: selectedMembers.map((member) => member.id),
        template_id: smsSelectedTemplateId ? Number(smsSelectedTemplateId) : null,
        message_body: smsMessageBody || null,
      });
      setSmsBulkProgress({
        running: true,
        total: selectedMembers.length,
        completed: 0,
        success: 0,
        failed: 0,
        currentRecipient: "",
      });
      setSmsBulkProgressRows([]);
      setActiveJobId(job.id);
      setActiveJobLabel("Bulk SMS");
      setMessage("Bulk SMS queued in the background.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSmsSendNow(messageId: number) {
    const accessToken = token();
    if (!accessToken) return;
    setIsSubmitting(true);
    try {
      await apiRequest<SmsMessage>(`/api/messaging/messages/${messageId}/send`, accessToken, { method: "POST" });
      await refreshMessagingWorkspace();
      setMessage("SMS send attempt recorded.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to send SMS");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleAvatarChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setAvatarUrl(URL.createObjectURL(file));
  }

    function renderDashboard() {
    return (
      <Dashboard
        isDashboardReady={isDashboardReady}
        isWorkspaceLoading={isWorkspaceLoading}
        members={members}
        categories={categories}
        billingDashboard={billingDashboard}
        receipts={receipts}
        smsMessages={smsMessages}
        memberTotalCount={memberTotalCount}
        activeMemberCountQuery={activeMemberCountQuery}
        activeMembers={activeMembers}
        totalCollection={totalCollection}
        smsIntegrationStatus={smsIntegrationStatus}
        smsMessagesQuery={smsMessagesQuery}
        smsAttemptsQuery={smsAttemptsQuery}
        smsAttempts={smsAttempts}
        accountingSummary={accountingSummary}
        monthlyCollection={monthlyCollection}
        monthlyExpense={monthlyExpense}
        memberDueSummaries={memberDueSummaries}
        setWorkspaceTab={setWorkspaceTab}
      />
    );
  }

  function renderCategories() {
    if (categoryPageMode === "entry") {
      return (
        <div className="row justify-content-center">
          <div className="col-xl-7">
            <div className="card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h4 className="header-title">{editingCategoryId ? "Edit Category" : "Add Category"}</h4>
                <button className="btn btn-sm btn-light" onClick={() => setCategoryPageMode("view")} type="button">
                  <i className="ri-arrow-left-line me-1" />
                  View Categories
                </button>
              </div>
              <div className="card-body">
                <form onSubmit={handleCategorySubmit}>
                  <div className="mb-3">
                    <label className="form-label">Category Name</label>
                    <input className="form-control" value={categoryName} onChange={(event) => setCategoryName(event.target.value)} required />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Code</label>
                    <input className="form-control" value={categoryCode} onChange={(event) => setCategoryCode(event.target.value)} />
                  </div>
                  <div className="mb-3">
                    <label className="form-label d-block">Status</label>
                    <div className="d-flex gap-3">
                      <div className="form-check">
                        <input className="form-check-input" checked={categoryIsActive} onChange={() => setCategoryIsActive(true)} type="radio" id="category-active" />
                        <label className="form-check-label" htmlFor="category-active">Active</label>
                      </div>
                      <div className="form-check">
                        <input className="form-check-input" checked={!categoryIsActive} onChange={() => setCategoryIsActive(false)} type="radio" id="category-inactive" />
                        <label className="form-check-label" htmlFor="category-inactive">Inactive</label>
                      </div>
                    </div>
                  </div>
                  <div className="d-flex gap-2">
                    <button className="btn btn-primary" disabled={isSubmitting} type="submit">
                      {editingCategoryId ? "Update Category" : "Save Category"}
                    </button>
                    <button className="btn btn-light" onClick={resetCategoryForm} type="button">Clear</button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="row">
        <div className="col-12">
          <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h4 className="header-title">Category List</h4>
              <div className="d-flex align-items-center gap-2">
                <span className="badge bg-primary-subtle text-primary">{categories.length} records</span>
                <button className="btn btn-primary btn-sm" onClick={() => startCategoryEntry()} type="button">
                  <i className="ri-add-line me-1" />
                  Add Category
                </button>
              </div>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-custom table-centered table-nowrap table-hover mb-0">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Code</th>
                      <th>Status</th>
                      <th className="text-end">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {categories.map((category) => (
                      <tr key={category.id}>
                        <td>{category.name}</td>
                        <td>{category.code ?? "N/A"}</td>
                        <td>{statusBadge(category.is_active)}</td>
                        <td className="text-end">
                          <button className="btn btn-sm btn-soft-info" onClick={() => startCategoryEntry(category)} type="button">
                            <i className="ri-edit-2-line me-1" />
                            Edit
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {categories.length === 0 ? <EmptyState label="No categories found" /> : null}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  function renderPackages() {
    if (packagePageMode === "entry") {
      return (
        <div className="row justify-content-center">
          <div className="col-xl-7">
            <div className="card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h4 className="header-title">{editingPackageId ? "Edit Package" : "Add Package"}</h4>
                <button className="btn btn-sm btn-light" onClick={() => setPackagePageMode("view")} type="button">
                  <i className="ri-arrow-left-line me-1" />
                  View Packages
                </button>
              </div>
              <div className="card-body">
                <form onSubmit={handlePackageSubmit}>
                  <div className="mb-3">
                    <label className="form-label">Category</label>
                    <select className="form-select" value={packageCategoryId} onChange={(event) => setPackageCategoryId(event.target.value)} required>
                      <option value="">Select category</option>
                      {categories.map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.code ?? "-"} - {category.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Package Name</label>
                    <input className="form-control" value={packageName} onChange={(event) => setPackageName(event.target.value)} required />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Package Type</label>
                    <input className="form-control" value={packageType} onChange={(event) => setPackageType(event.target.value)} />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Default Price</label>
                    <input className="form-control" type="number" value={packagePrice} onChange={(event) => setPackagePrice(event.target.value)} required />
                  </div>
                  <div className="mb-3">
                    <label className="form-label d-block">Status</label>
                    <div className="d-flex gap-3">
                      <div className="form-check">
                        <input className="form-check-input" checked={packageIsActive} onChange={() => setPackageIsActive(true)} type="radio" id="package-active" />
                        <label className="form-check-label" htmlFor="package-active">Active</label>
                      </div>
                      <div className="form-check">
                        <input className="form-check-input" checked={!packageIsActive} onChange={() => setPackageIsActive(false)} type="radio" id="package-inactive" />
                        <label className="form-check-label" htmlFor="package-inactive">Inactive</label>
                      </div>
                    </div>
                  </div>
                  <div className="d-flex gap-2">
                    <button className="btn btn-primary" disabled={isSubmitting} type="submit">
                      {editingPackageId ? "Update Package" : "Save Package"}
                    </button>
                    <button className="btn btn-light" onClick={resetPackageForm} type="button">Clear</button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="row">
        <div className="col-12">
          <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h4 className="header-title">Package List</h4>
              <div className="d-flex align-items-center gap-2">
                <span className="badge bg-primary-subtle text-primary">{packages.length} records</span>
                <button className="btn btn-primary btn-sm" onClick={() => startPackageEntry()} type="button">
                  <i className="ri-add-line me-1" />
                  Add Package
                </button>
              </div>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-custom table-centered table-nowrap table-hover mb-0">
                  <thead>
                    <tr>
                      <th>Code</th>
                      <th>Name</th>
                      <th>Category</th>
                      <th>Type</th>
                      <th>Price</th>
                      <th>Status</th>
                      <th className="text-end">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {packages.map((item) => (
                      <tr key={item.id}>
                        <td>{item.package_code}</td>
                        <td>{item.name}</td>
                        <td>{item.category_name}</td>
                        <td>{item.package_type ?? "General"}</td>
                        <td>{money(item.default_price)}</td>
                        <td>{statusBadge(item.is_active)}</td>
                        <td className="text-end">
                          <button className="btn btn-sm btn-soft-info" onClick={() => startPackageEntry(item)} type="button">
                            <i className="ri-edit-2-line me-1" />
                            Edit
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {packages.length === 0 ? <EmptyState label="No packages found" /> : null}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  function renderMembers() {
    if (memberPageMode === "entry") {
      return (
        <div className="row justify-content-center">
          <div className="col-xl-9">
            <div className="card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h4 className="header-title">{editingMemberId ? "Edit Member" : "Register Member"}</h4>
                <button className="btn btn-sm btn-light" onClick={() => setMemberPageMode("view")} type="button">
                  <i className="ri-arrow-left-line me-1" />
                  View Members
                </button>
              </div>
              <div className="card-body">
	                <form onSubmit={handleMemberSubmit}>
	                  <div className="row">
	                    <div className="col-lg-6">
	                      <div className="mb-3">
	                        <label className="form-label">Member Name</label>
                        <input className="form-control" value={memberName} onChange={(event) => setMemberName(event.target.value)} required />
                      </div>
                      <div className="mb-3">
                        <label className="form-label">Father Name</label>
                        <input className="form-control" value={memberFatherName} onChange={(event) => setMemberFatherName(event.target.value)} />
                      </div>
                      <div className="mb-3">
                        <label className="form-label">Phone Number</label>
                        <input
                          className="form-control"
                          inputMode="numeric"
                          pattern="^[0-9]+$"
                          title="Use digits only."
                          value={memberCell}
                          onChange={(event) => setMemberCell(event.target.value.replace(/[^\d]/g, ""))}
                        />
                      </div>
                      <div className="mb-3">
                        <label className="form-label">Present Address</label>
                        <textarea className="form-control" rows={3} value={memberPresentAddress} onChange={(event) => setMemberPresentAddress(event.target.value)} required />
                      </div>
                      <div className="mb-3">
                        <label className="form-label">Nominee Name</label>
                        <input className="form-control" value={nomineeName} onChange={(event) => setNomineeName(event.target.value)} />
                      </div>
                      <div className="mb-3">
                        <label className="form-label">Category</label>
                        <select className="form-select" value={memberCategoryId} onChange={(event) => setMemberCategoryId(event.target.value)} required>
                          <option value="">Select category</option>
                          {categories.map((category) => (
                            <option key={category.id} value={category.id}>
                              {category.code ?? "-"} - {category.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="mb-3">
                        <label className="form-label">Member Category</label>
                        <select className="form-select" value={memberClass} onChange={(event) => setMemberClass(event.target.value)} required>
                          <option value="">Select member category</option>
                          {memberClassOptions.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <div className="col-lg-6">
                      <div className="mb-3">
                        <label className="form-label">National ID</label>
                        <input className="form-control" value={memberNationalId} onChange={(event) => setMemberNationalId(event.target.value)} required />
                      </div>
                      <div className="mb-3">
                        <label className="form-label">Member ID</label>
                        <input className="form-control" value={memberCode} onChange={(event) => setMemberCode(event.target.value)} required />
                      </div>
                      <div className="mb-3">
                        <label className="form-label">Mother Name</label>
                        <input className="form-control" value={memberMotherName} onChange={(event) => setMemberMotherName(event.target.value)} />
                      </div>
                      <div className="mb-3">
                        <label className="form-label">E-mail</label>
                        <input className="form-control" type="email" value={memberEmail} onChange={(event) => setMemberEmail(event.target.value)} />
                      </div>
                      <div className="mb-3">
                        <label className="form-label">Permanent Address</label>
                        <textarea className="form-control" rows={3} value={memberPermanentAddress} onChange={(event) => setMemberPermanentAddress(event.target.value)} required />
                      </div>
                      <div className="mb-3">
                        <label className="form-label">Nominee Phone No</label>
                        <input
                          className="form-control"
                          inputMode="numeric"
                          pattern="^[0-9]+$"
                          title="Use digits only."
                          value={nomineeCell}
                          onChange={(event) => setNomineeCell(event.target.value.replace(/[^\d]/g, ""))}
                        />
                      </div>
	                      <div className="mb-3">
	                        <label className="form-label">Plot No</label>
	                        <div className="input-group">
	                          <span className="input-group-text">Reg-</span>
	                          <input
	                            className="form-control"
	                            placeholder="Enter plot no"
	                            value={memberPlotNo}
	                            onChange={(event) => setMemberPlotNo(event.target.value.replace(/^Reg[\s\-_:]*/i, ""))}
	                            required
	                          />
	                        </div>
	                      </div>
	                      <div className="mb-3">
	                        <label className="form-label">Plot Count</label>
	                        <input
	                          className="form-control"
	                          type="number"
	                          min="1"
	                          value={memberPlotCount}
	                          onChange={(event) => setMemberPlotCount(event.target.value)}
	                          required
	                        />
	                      </div>
	                    </div>
                  </div>
                  <div className="mb-3">
                    <label className="form-label d-block">Status</label>
                    <div className="d-flex gap-3 pt-1">
                      <div className="form-check">
                        <input className="form-check-input" checked={memberIsActive} onChange={() => setMemberIsActive(true)} type="radio" id="member-active" />
                        <label className="form-check-label" htmlFor="member-active">Active</label>
                      </div>
                      <div className="form-check">
                        <input className="form-check-input" checked={!memberIsActive} onChange={() => setMemberIsActive(false)} type="radio" id="member-inactive" />
                        <label className="form-check-label" htmlFor="member-inactive">Inactive</label>
                      </div>
                    </div>
                  </div>
                  <div className="d-flex gap-2">
                    <button className="btn btn-primary" disabled={isSubmitting} type="submit">
                      {editingMemberId ? "Update Member" : "Save Member"}
                    </button>
                    <button className="btn btn-light" onClick={resetMemberForm} type="button">Clear</button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return (
      <>
        <div className="row">
          <div className="col-12">
            <div className="card">
              <div className="card-header d-flex justify-content-between align-items-center gap-2 flex-wrap">
                <h4 className="header-title">Member Register</h4>
                <div className="d-flex align-items-center gap-2 flex-wrap">
                  <span className="badge bg-primary-subtle text-primary">{memberTotalCount} records</span>
                  <button className="btn btn-primary btn-sm" onClick={() => void startMemberEntry()} type="button">
                    <i className="ri-add-line me-1" />
                    Add Member
                  </button>
                </div>
              </div>
              <div className="card-body p-0">
                <div className="table-responsive">
                  <table ref={memberTableRef} className="table table-custom table-centered table-nowrap table-hover mb-0" id="member-datatable">
                    <thead>
	                      <tr>
	                        <th>Code</th>
	                        <th>Name</th>
	                        <th>Plot No</th>
	                        <th>Plot Count</th>
	                        <th>Cell</th>
                        <th>Category</th>
                        <th>Status</th>
                        <th className="text-end">Action</th>
                      </tr>
                    </thead>
                    <tbody />
                  </table>
                  {memberTotalCount === 0 ? <EmptyState label="No members found" /> : null}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="row">
          <div className="col-xl-12">
            <div className="card">
              <div className="card-header">
                <h4 className="header-title">Member Detail</h4>
              </div>
              <div className="card-body">
                {selectedMember ? (
                  <>
                    <div className="d-flex align-items-center gap-3 mb-3">
                      <img src={avatarUrl} className="rounded-circle avatar-lg" alt="member" />
                      <div>
                        <h4 className="mb-1">{selectedMember.full_name}</h4>
                        <p className="text-muted mb-0">
                          {selectedMember.member_code} | {selectedMember.category_name ?? "No category"}
                        </p>
                      </div>
                    </div>
                    <div className="row">
	                      {[
	                        ["Cell", selectedMember.cell_no ?? "N/A"],
	                        ["Email", selectedMember.email ?? "N/A"],
	                        ["Plot No", selectedMember.plot_no ?? "N/A"],
	                        ["Plot Count", String(selectedMember.plot_count ?? 1)],
	                        ["Class", selectedMember.member_class ?? "N/A"],
                        ["Joined", shortDate(selectedMember.joined_on)],
                        ["Nominee", selectedMember.nominee_name ?? "N/A"],
                        ["Nominee Cell", selectedMember.nominee_cell ?? "N/A"],
                      ].map(([label, value]) => (
                        <div className="col-md-4 mb-3" key={label}>
                          <span className="text-muted fs-12">{label}</span>
                          <h5 className="fs-14 mt-1">{value}</h5>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <EmptyState label="Select a member to see details" />
                )}
              </div>
            </div>
          </div>
        </div>
      </>
    );
  }

  function renderBillingHeadsSetup() {
    if (workspaceTab === "billing-heads-entry") {
      return (
        <div className="row justify-content-center">
          <div className="col-xl-7">
            <div className="card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h4 className="header-title">{editingBillingHeadId ? "Edit Billing Head" : "Add Billing Head"}</h4>
                <button className="btn btn-sm btn-light" onClick={() => setWorkspaceTab("billing-heads-view")} type="button">
                  <i className="ri-arrow-left-line me-1" />
                  View Heads
                </button>
              </div>
              <div className="card-body">
                <form onSubmit={handleBillingHeadSubmit}>
                  <div className="mb-3">
                    <label className="form-label">Head Name</label>
                    <input className="form-control" value={billingHeadName} onChange={(event) => setBillingHeadName(event.target.value)} required />
                  </div>
	                  <div className="row">
	                    <div className="col-md-6 mb-3">
	                      <label className="form-label">Head Type</label>
	                      <select
	                        className="form-select"
	                        value={billingHeadType}
	                        onChange={(event) => {
	                          const nextType = event.target.value as "Period" | "OneTime";
	                          setBillingHeadType(nextType);
	                          if (nextType === "Period") {
	                            setBillingHeadMode("Mandatory");
	                          }
	                        }}
	                      >
	                        <option value="Period">Period</option>
	                        <option value="OneTime">OneTime</option>
	                      </select>
	                    </div>
	                    <div className="col-md-6 mb-3">
	                      <label className="form-label">Mode</label>
	                      <select
	                        className="form-select"
	                        value={billingHeadType === "Period" ? "Mandatory" : billingHeadMode}
	                        onChange={(event) => setBillingHeadMode(event.target.value as "Mandatory" | "Optional")}
	                        disabled={billingHeadType === "Period"}
	                      >
	                        <option value="Mandatory">Mandatory</option>
	                        <option value="Optional">Optional</option>
	                      </select>
	                    </div>
	                  </div>
	                  <div className="row">
	                    <div className="col-md-6 mb-3">
	                      <label className="form-label">Fee</label>
	                      <input
	                        className="form-control"
	                        type="number"
	                        value={billingHeadFee}
	                        onChange={(event) => setBillingHeadFee(event.target.value)}
	                        required={billingHeadType === "Period" || billingHeadMode === "Mandatory"}
	                      />
	                    </div>
	                  </div>
                  {billingHeadType === "Period" ? (
                    <div className="row">
                      <div className="col-md-6 mb-3">
                        <label className="form-label">Effective From</label>
                        <input className="form-control" type="date" value={billingHeadEffectiveDate} onChange={(event) => setBillingHeadEffectiveDate(event.target.value)} required />
                      </div>
                      <div className="col-md-6 mb-3">
                        <label className="form-label">Effective To</label>
                        <input className="form-control" type="date" value={billingHeadEffectiveToDate} onChange={(event) => setBillingHeadEffectiveToDate(event.target.value)} />
                        <small className="text-muted">Leave empty if the head continues without an end date.</small>
                      </div>
                    </div>
                  ) : null}
                  <button className="btn btn-primary" disabled={isSubmitting} type="submit">{editingBillingHeadId ? "Update As New Version" : "Save Head"}</button>
                </form>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h4 className="header-title">Billing Head Setup</h4>
          <button
            className="btn btn-primary btn-sm"
	            onClick={() => {
	              setEditingBillingHeadId(null);
	              setBillingHeadName("");
	              setBillingHeadType("Period");
	              setBillingHeadMode("Mandatory");
	              setBillingHeadFee("500");
	              setBillingHeadEffectiveDate("2018-01-01");
                setBillingHeadEffectiveToDate("");
              setWorkspaceTab("billing-heads-entry");
            }}
            type="button"
          >
            <i className="ri-add-line me-1" />
            Add Head
          </button>
        </div>
        <div className="card-body p-0">
          <div className="table-responsive">
            <table className="table table-custom table-centered table-nowrap table-hover mb-0">
              <thead>
                <tr>
	                  <th>Head</th>
	                  <th>Type</th>
	                  <th>Mode</th>
	                  <th>Fee</th>
                  <th>Effective From</th>
                  <th>Effective To</th>
                  <th>Status</th>
                  <th className="text-end">Action</th>
                </tr>
              </thead>
              <tbody>
                {billingHeads.map((head) => (
                  <tr key={head.id}>
	                    <td>{head.head_name}</td>
	                    <td>{head.head_type}</td>
	                    <td>{head.billing_mode}</td>
	                    <td>{money(head.fee_amount)}</td>
                    <td>{shortDate(head.effective_from_date)}</td>
                    <td>{shortDate(head.effective_to_date)}</td>
                    <td>{statusBadge(head.is_active)}</td>
                    <td className="text-end">
                      {head.is_active ? (
                        <button
                          className="btn btn-sm btn-soft-info"
                          onClick={() => {
	                            setEditingBillingHeadId(head.id);
	                            setBillingHeadName(head.head_name);
	                            setBillingHeadType(head.head_type);
	                            setBillingHeadMode(head.billing_mode);
	                            setBillingHeadFee(String(head.fee_amount));
                            setBillingHeadEffectiveDate(head.effective_from_date ?? "2018-01-01");
                            setBillingHeadEffectiveToDate(head.effective_to_date ?? "");
                            setWorkspaceTab("billing-heads-entry");
                          }}
                          type="button"
                        >
                          <i className="ri-edit-2-line me-1" />
                          Edit
                        </button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {billingHeads.length === 0 ? <EmptyState label="No billing heads found" /> : null}
          </div>
        </div>
      </div>
    );
  }

  function renderBillingMappingsSetup() {
    if (workspaceTab === "billing-mappings-entry") {
      return (
        <div className="row justify-content-center">
          <div className="col-xl-7">
            <div className="card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h4 className="header-title">Add Head To COA Mapping</h4>
                <button className="btn btn-sm btn-light" onClick={() => setWorkspaceTab("billing-mappings-view")} type="button">
                  <i className="ri-arrow-left-line me-1" />
                  View Mappings
                </button>
              </div>
              <div className="card-body">
                <form onSubmit={handleBillingMappingSubmit}>
                  <div className="mb-3">
                    <label className="form-label">Billing Head</label>
                    <select className="form-select" value={mappingHeadId} onChange={(event) => setMappingHeadId(event.target.value)} required>
                      <option value="">Select head</option>
                      {billingHeads.map((head) => <option key={head.id} value={head.id}>{head.head_name}</option>)}
                    </select>
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Income COA</label>
                    <select className="form-select" value={mappingCoaId} onChange={(event) => setMappingCoaId(event.target.value)} required>
                      <option value="">Select COA</option>
                      {incomeAccounts.map((account) => <option key={account.id} value={account.id}>{account.code} - {account.name}</option>)}
                    </select>
                  </div>
                  <button className="btn btn-primary" disabled={isSubmitting} type="submit">Save Mapping</button>
                </form>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h4 className="header-title">Billing Head COA Mapping</h4>
          <button className="btn btn-primary btn-sm" onClick={() => setWorkspaceTab("billing-mappings-entry")} type="button">
            <i className="ri-add-line me-1" />
            Add Mapping
          </button>
        </div>
        <div className="card-body p-0">
          <div className="table-responsive">
            <table className="table table-custom table-centered table-nowrap table-hover mb-0">
              <thead><tr><th>Billing Head</th><th>COA</th><th>Status</th><th>Created</th></tr></thead>
              <tbody>
                {billingHeadMappings.map((mapping) => (
                  <tr key={mapping.id}>
                    <td>{mapping.billing_head_name}</td>
                    <td>{mapping.coa_name}</td>
                    <td>{statusBadge(mapping.is_active)}</td>
                    <td>{shortDate(mapping.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {billingHeadMappings.length === 0 ? <EmptyState label="No billing head mappings found" /> : null}
          </div>
        </div>
      </div>
    );
  }

  function renderInvoiceReport(invoice: BillingInvoice) {
    const member = members.find((item) => item.id === invoice.member_id);
    const paidStatus = invoiceStatus(invoice);
    return (
      <div className="invoice-report-sheet">
        <div className="invoice-report-header">
          <div className="invoice-report-brand">
            <img src="/makan-logo-3.png" alt="Darul Mohan Plot Owners Society" className="report-header-logo" />
          </div>
          <div className="d-flex justify-content-between gap-3">
            <div>
              <div className="fw-semibold">Billing invoice and money receipt</div>
              <div className="text-muted">Makan Society</div>
            </div>
            <div className="text-end">
            <span className={invoiceStatusBadgeClass(paidStatus)}>
              {paidStatus}
            </span>
            <h3 className="invoice-report-title">Invoice</h3>
            <div className="fw-semibold">{invoice.invoice_no}</div>
            </div>
          </div>
        </div>

        <div className="invoice-report-meta">
          <div>
            <div>Bill To: {invoice.member_name}</div>
            <div>Plot No: {invoice.plot_no || ""}</div>
            <div>Member ID: {invoice.member_code || ""}</div>
          </div>
          <div className="text-md-end">
            <span className="text-muted d-block">Invoice Date</span>
            <strong>{shortDate(invoice.invoice_date)}</strong>
            <div>Generated: {shortDate(invoice.created_at)}</div>
          </div>
        </div>

        <div className="table-responsive">
          <table className="table table-bordered invoice-report-table mb-0">
            <thead>
              <tr>
                <th style={{ width: "44px" }}>SL</th>
                <th>Billing Head</th>
                <th>Period</th>
                <th className="text-end">Fee</th>
                <th className="text-end">Received</th>
                <th className="text-end">Due</th>
              </tr>
            </thead>
            <tbody>
              {invoice.details.map((detail, index) => (
                <tr key={detail.id}>
                  <td>{index + 1}</td>
                  <td>{detail.head_name_snapshot}</td>
                  <td>{detail.period_display ?? "-"}</td>
                  <td className="text-end">{money(detail.fee_amount)}</td>
                  <td className="text-end">{money(detail.receive_amount)}</td>
                  <td className="text-end">{money(detail.due_amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="invoice-report-summary">
          <div className="invoice-report-note">
            <strong>Note</strong>
            <p className="mb-0">This invoice is generated from saved billing data. Old invoice values remain unchanged after setup edits.</p>
          </div>
          <div className="invoice-report-totals">
            <div><span>Subtotal</span><strong>{money(invoice.subtotal_amount)}</strong></div>
            <div><span>Discount</span><strong>{money(invoice.discount_amount)}</strong></div>
            <div><span>Net Amount</span><strong>{money(invoice.net_amount)}</strong></div>
            <div><span>Received</span><strong>{money(invoice.total_receive_amount)}</strong></div>
            <div className="grand-total"><span>Due</span><strong>{money(invoice.member_outstanding_due)}</strong></div>
          </div>
        </div>

        <div className="invoice-report-signatures">
          <div><span />Prepared By<br/>User Name: {profile?.username || ""}</div>
          <div><span />Received By</div>
          <div><span />Authorized Signature</div>
        </div>
      </div>
    );
  }

  function renderInvoiceReportModal() {
    if (!showInvoiceReport || !invoiceReport) return null;
    return (
      <>
        <div className="modal fade show d-block invoice-report-modal" tabIndex={-1}>
          <div className="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
            <div className="modal-content">
              <div className="modal-header invoice-report-actions">
                <div>
                  <h5 className="modal-title">Invoice Report</h5>
                  <span className="text-muted">{invoiceReport.invoice_no}</span>
                </div>
                <div className="d-flex gap-2">
                  <button className="btn btn-primary" onClick={() => printInvoiceReport(invoiceReport)} type="button">
                    <i className="ri-printer-line me-1" />
                    Print
                  </button>
                  <button className="btn-close" onClick={() => setShowInvoiceReport(false)} type="button" />
                </div>
              </div>
              <div className="modal-body invoice-report-print-area">{renderInvoiceReport(invoiceReport)}</div>
            </div>
          </div>
        </div>
        <div className="modal-backdrop fade show invoice-report-actions" />
      </>
    );
  }

  function renderPreviousBillsModal() {
    if (!showPreviousBills) return null;
    return (
      <>
        <div className="modal fade show d-block" tabIndex={-1}>
          <div className="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
            <div className="modal-content">
              <div className="modal-header">
                <div>
                  <h5 className="modal-title">Previous Bills</h5>
                  <span className="text-muted">
                    {selectedInvoiceMember ? `${selectedInvoiceMember.member_code} - ${selectedInvoiceMember.full_name}` : "Select a member"}
                  </span>
                </div>
                <button className="btn-close" onClick={() => setShowPreviousBills(false)} type="button" />
              </div>
              <div className="modal-body">
                <div className="row g-3 align-items-end mb-3">
                  <div className="col-md-4">
                    <label className="form-label">From Date</label>
                    <input className="form-control" type="date" value={previousBillsFromDate} onChange={(event) => setPreviousBillsFromDate(event.target.value)} />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label">To Date</label>
                    <input className="form-control" type="date" value={previousBillsToDate} onChange={(event) => setPreviousBillsToDate(event.target.value)} />
                  </div>
                  <div className="col-md-4">
                    <button className="btn btn-outline-secondary" onClick={() => { setPreviousBillsFromDate(defaultMonthRange.from); setPreviousBillsToDate(defaultMonthRange.to); }} type="button">
                      Reset To Current Month
                    </button>
                  </div>
                </div>
                <div className="table-responsive billing-register-table">
                  <table ref={previousBillsTableRef} className="table table-custom table-centered table-nowrap table-hover mb-0">
                    <thead>
                      <tr>
                        <th>Invoice No</th>
                        <th>Date</th>
                        <th className="text-end">Subtotal</th>
                        <th className="text-end">Discount</th>
                        <th className="text-end">Received</th>
                        <th className="text-end">Due</th>
                        <th>Status</th>
                        <th className="text-end">Action</th>
                      </tr>
                    </thead>
                  </table>
                </div>
                <div className="row g-3 mt-3">
                  <div className="col-md-4"><div className="border rounded p-3"><div className="text-muted fs-13">Total Bill</div><div className="fw-semibold">{money(previousBillsTotals.total_bill_amount)}</div></div></div>
                  <div className="col-md-4"><div className="border rounded p-3"><div className="text-muted fs-13">Total Paid</div><div className="fw-semibold">{money(previousBillsTotals.total_paid)}</div></div></div>
                  <div className="col-md-4"><div className="border rounded p-3"><div className="text-muted fs-13">Total Due</div><div className="fw-semibold">{money(previousBillsTotals.total_due)}</div></div></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="modal-backdrop fade show" />
      </>
    );
  }

  function renderBilling() {
    return (
      <>
        <div className="row row-cols-xl-4 row-cols-md-2 row-cols-1">
          <StatCard title="Collection Today" value={money(todayCollectionAmount)} subtitle="Received amount" icon="ri-wallet-3-line" tone="success" />
          <StatCard title="Dues Today" value={money(todayDueAmount)} subtitle="Invoice balance" icon="ri-error-warning-line" tone="warning" />
          <StatCard title="Members Collected" value={String(todayCollectedMembers)} subtitle="Today" icon="ri-user-received-2-line" tone="primary" />
          <StatCard title="Discount Today" value={money(todayDiscountAmount)} subtitle="Given on bills" icon="ri-coupon-3-line" tone="info" />
        </div>

        <div className="card">
          <div className="card-header"><h4 className="header-title">Invoice Generation</h4></div>
          <div className="card-body">
            {lastGeneratedInvoice ? (
              <div className="alert alert-success border-0 mb-4">
                <div className="row align-items-end g-2">
                  <div className="col-lg-5">
                    <label className="form-label text-success fw-semibold">Generated Invoice No</label>
                    <input className="form-control bg-white fw-bold" readOnly value={lastGeneratedInvoice.invoice_no} />
                  </div>
                  <div className="col-lg-4">
                    <div className="text-muted fs-13">Member</div>
                    <div className="fw-semibold">{lastGeneratedMember?.member_code ? `${lastGeneratedMember.member_code} - ` : ""}{lastGeneratedInvoice.member_name}</div>
                    <div className="fs-13">Net: {money(lastGeneratedInvoice.net_amount)} | Due: {money(lastGeneratedInvoice.total_due_amount)}</div>
                  </div>
                  <div className="col-lg-3 d-flex gap-2 justify-content-lg-end">
                    <button className="btn btn-primary" onClick={() => void openInvoiceReport(lastGeneratedInvoice)} type="button">
                      <i className="ri-file-text-line me-1" />
                      View Invoice
                    </button>
                    <button className="btn btn-light" onClick={() => printInvoiceReport(lastGeneratedInvoice)} type="button">
                      <i className="ri-printer-line" />
                    </button>
                  </div>
                </div>
              </div>
            ) : null}
            <form onSubmit={handleInvoiceSubmit}>
              <div className="row g-3 align-items-end">
                <div className="col-xl-2 col-lg-3">
                  <label className="form-label">Invoice Date</label>
                  <input className="form-control" type="date" value={invoiceDate} onChange={(event) => setInvoiceDate(event.target.value)} required />
                </div>
                <div className="col-xl-4 col-lg-5">
                  <AsyncSearchableDropdown
                    isOpen={invoiceMemberDropdownOpen}
                    isLoading={invoiceMemberOptionsQuery.isFetching}
                    label="Member"
                    onChange={(value) => {
                      setInvoiceMemberId(value);
                      setBillingDueLines([]);
                      setInvoiceReceipts({});
                    }}
                    onOpenChange={setInvoiceMemberDropdownOpen}
                    onSearchChange={setInvoiceMemberSearch}
                    options={memberDropdownOptions}
                    placeholder="Search member by code, name, or number"
                    search={invoiceMemberSearch}
                    value={invoiceMemberId}
                    helperText="Type at least 2 characters to search members."
                  />
                </div>
              </div>

              <div className="card border mt-3">
                <div className="card-header d-flex align-items-center justify-content-between gap-2 flex-wrap">
                  <h5 className="header-title mb-0">Member Details</h5>
                  <div className="d-flex gap-2">
                    <button className="btn btn-outline-info" disabled={!invoiceMemberId || isSubmitting} onClick={() => void handleLoadMemberDues()} type="button">
                      <i className="ri-search-eye-line me-1" />
                      View Due
                    </button>
                    <button className="btn btn-secondary" disabled={!invoiceMemberId} onClick={() => setShowPreviousBills(true)} type="button">
                      <i className="ri-file-list-2-line me-1" />
                      Previous Bill
                    </button>
                  </div>
                </div>
                <div className="card-body">
                  {selectedInvoiceMember ? (
                    <div className="row g-3">
                      <div className="col-lg-4 col-md-6">
                        <div className="text-muted fs-13">Member</div>
                        <div className="fw-semibold">{selectedInvoiceMember.member_code} - {selectedInvoiceMember.full_name}</div>
                      </div>
                      <div className="col-lg-2 col-md-6">
                        <div className="text-muted fs-13">Plot No</div>
                        <div className="fw-semibold">{selectedInvoiceMember.plot_no ?? "N/A"}</div>
                      </div>
                      <div className="col-lg-2 col-md-6">
                        <div className="text-muted fs-13">Plots</div>
                        <div className="fw-semibold">{selectedInvoiceMember.plot_count ?? 1}</div>
                      </div>
                      <div className="col-lg-2 col-md-6">
                        <div className="text-muted fs-13">Phone</div>
                        <div className="fw-semibold">{selectedInvoiceMember.cell_no ?? "N/A"}</div>
                      </div>
                      <div className="col-lg-2 col-md-6">
                        <div className="text-muted fs-13">Category</div>
                        <div className="fw-semibold">{selectedInvoiceMember.category_name ?? "N/A"}</div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-muted">Select a member to view billing details.</div>
                  )}
                </div>
              </div>

              <div className="border-top border-dashed mt-4 pt-3">
                <h5 className="fs-15 mb-3">Add Manual Head</h5>
                <div className="row g-3 align-items-end">
                  <div className="col-xl-7 col-lg-7">
                    <label className="form-label">Billing Head</label>
                    <div className="input-group billing-head-select">
                      <span className="input-group-text">
                        <i className="ri-price-tag-3-line" />
                      </span>
	                      <select className="form-select" value={manualBillingHeadId} onChange={(event) => setManualBillingHeadId(event.target.value)}>
	                        <option value="">Select head</option>
	                        {manualBillingHeadOptions.map((head) => <option key={head.id} value={head.id}>{head.head_name} - {head.head_type} - {head.billing_mode} - {money(head.fee_amount)}</option>)}
	                      </select>
	                    </div>
	                  </div>
	                  {billingHeads.find((head) => head.id === Number(manualBillingHeadId))?.head_type === "Period" ? (
	                    <div className="col-xl-2 col-lg-2">
                      <label className="form-label">Period</label>
	                      <input className="form-control" type="month" value={manualBillingPeriod} onChange={(event) => setManualBillingPeriod(event.target.value)} />
	                    </div>
	                  ) : null}
	                  {billingHeads.find((head) => head.id === Number(manualBillingHeadId))?.head_type === "OneTime" &&
	                  billingHeads.find((head) => head.id === Number(manualBillingHeadId))?.billing_mode === "Optional" ? (
	                    <div className="col-xl-2 col-lg-2">
	                      <label className="form-label">Fee</label>
	                      <input className="form-control" type="number" value={manualBillingFee} onChange={(event) => setManualBillingFee(event.target.value)} />
	                    </div>
	                  ) : null}
	                  <div className={billingHeads.find((head) => head.id === Number(manualBillingHeadId))?.head_type === "Period" ? "col-xl-3 col-lg-3" : "col-xl-3 col-lg-3"}>
	                    <button className="btn btn-info w-100" disabled={!manualBillingHeadId || !invoiceMemberId} onClick={handleAddManualBillingLine} type="button">Add To Grid</button>
	                  </div>
                </div>
              </div>

              <div className="billing-grid-shell mt-4">
                <div className="d-flex align-items-center justify-content-between flex-wrap gap-2 billing-grid-title">
                  <div>
                    <h5 className="fs-15 mb-1">Billing Grid</h5>
                    <p className="text-muted mb-0 fs-13">Check rows to fill receive amount and prepare invoice.</p>
                  </div>
                  <span className="badge bg-info-subtle text-info">{billingSelectedLines.length} selected</span>
                </div>
                <div className="table-responsive">
                <table className="table table-custom table-centered table-nowrap table-hover mb-0 billing-grid-table">
                  <thead>
                    <tr>
                      <th className="text-center" style={{ width: "48px" }}>
                        <input
                          className="form-check-input"
                          checked={billingAllRowsChecked}
                          onChange={(event) => {
                            if (event.target.checked) {
                              setInvoiceReceipts(Object.fromEntries(billingDueLines.map((line, index) => [billingLineKey(line, index), String(line.due_amount)])));
                            } else {
                              setInvoiceReceipts({});
                            }
                          }}
                          type="checkbox"
                        />
                      </th>
                      <th className="text-start">Head Name</th>
                      <th className="text-center">Period</th>
                      <th className="text-center">Plot Count</th>
                      <th className="text-end">Base Amount</th>
                      <th className="text-end">Fee Amount</th>
                      <th className="text-end">Paid Amount</th>
                      <th className="text-end">Due Amount</th>
                      <th className="text-end">Receive Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {billingDueLines.map((line, index) => {
                      const key = billingLineKey(line, index);
                      const receive = Number(invoiceReceipts[key] ?? 0);
                      return (
                        <tr key={key}>
                          <td className="text-center">
                            <input
                              className="form-check-input"
                              checked={receive > 0}
                              onChange={(event) =>
                                setInvoiceReceipts((current) => {
                                  const next = { ...current };
                                  if (event.target.checked) next[key] = String(line.due_amount);
                                  else delete next[key];
                                  return next;
                                })
                              }
                              type="checkbox"
                            />
                          </td>
                          <td className="text-start text-wrap fw-semibold">{line.head_name}</td>
                          <td className="text-center"><span className="badge bg-secondary-subtle text-secondary">{line.period_display ?? "One Time"}</span></td>
                          <td className="text-center">{line.plot_count ?? 1}</td>
                          <td className="text-end">{money(line.base_fee_amount ?? line.fee_amount)}</td>
                          <td className="text-end">{money(line.fee_amount)}</td>
                          <td className="text-end">{money(line.paid_amount ?? 0)}</td>
                          <td className="text-end">{money(line.due_amount)}</td>
                          <td className="text-end">
                            <input className="form-control form-control-sm billing-receive-input ms-auto" style={{ maxWidth: "120px" }} type="number" min="0" max={line.due_amount} onFocus={(e) => e.target.select()} value={invoiceReceipts[key] ?? "0"} onChange={(event) => {
                              const val = Number(event.target.value);
                              if (val > line.due_amount) {
                                setInvoiceReceipts((current) => ({ ...current, [key]: String(line.due_amount) }));
                              } else {
                                setInvoiceReceipts((current) => ({ ...current, [key]: event.target.value }));
                              }
                            }} />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                  {billingDueLines.length > 0 ? (
                    <tfoot>
                      <tr>
                        <th className="text-end" colSpan={5}>Total (Selected Rows)</th>
                        <th className="text-end">{money(billingGridFeeTotal)}</th>
                        <th className="text-end">{money(billingGridPaidTotal)}</th>
                        <th className="text-end">{money(billingGridDueTotal)}</th>
                        <th className="text-end">{money(billingGridReceiveTotal)}</th>
                      </tr>
                    </tfoot>
                  ) : null}
                </table>
                </div>
                {billingDueLines.length === 0 ? <EmptyState label="Select a member and load dues, or add a billing head manually" /> : null}
              </div>

              <div className="border-top border-dashed mt-4 pt-3">
                <div className="row justify-content-end">
                  <div className="col-xl-4 col-lg-5">
                    <div className="d-flex justify-content-between mb-2"><span>Subtotal</span><strong>{money(billingSubtotal)}</strong></div>
                    <div className="mb-2">
                      <label className="form-label">Discount</label>
                      <input className="form-control" type="number" value={invoiceDiscount} onChange={(event) => setInvoiceDiscount(event.target.value)} />
                    </div>
                    <div className="d-flex justify-content-between mb-2"><span>Net Amount</span><strong>{money(billingNetAmount)}</strong></div>
                    <div className="d-flex justify-content-between mb-3"><span>Due Amount</span><strong>{money(billingDueTotal)}</strong></div>
                    <button className="btn btn-success w-100" disabled={isSubmitting || billingDueLines.length === 0} type="submit">Generate Invoice</button>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </div>
      </>
    );
  }

  function renderBillingRegisters() {
    return (
      <div className="card">
        <div className="card-header pb-0">
          <ul className="nav nav-tabs nav-bordered">
            <li className="nav-item">
              <button className={billingRegisterTab === "charges" ? "nav-link active" : "nav-link"} onClick={() => setBillingRegisterTab("charges")} type="button">
                Open Charge Register
              </button>
            </li>
            <li className="nav-item">
              <button className={billingRegisterTab === "receipts" ? "nav-link active" : "nav-link"} onClick={() => setBillingRegisterTab("receipts")} type="button">
                Recent Receipts
              </button>
            </li>
          </ul>
        </div>
        <div className="card-body">
          <div className="row align-items-end g-3 mb-3">
            <div className="col-md-3">
              <label className="form-label">From Date</label>
              <input className="form-control" type="date" value={billingRegisterFromDate} onChange={(event) => setBillingRegisterFromDate(event.target.value)} />
            </div>
            <div className="col-md-3">
              <label className="form-label">To Date</label>
              <input className="form-control" type="date" value={billingRegisterToDate} onChange={(event) => setBillingRegisterToDate(event.target.value)} />
            </div>
            <div className="col-md-3">
              <button className="btn btn-outline-secondary" onClick={() => { setBillingRegisterFromDate(defaultMonthRange.from); setBillingRegisterToDate(defaultMonthRange.to); reloadDataTable(billingRegisterTableRef.current); }} type="button">
                Current Month
              </button>
            </div>
          </div>
          <div className="table-responsive billing-register-table">
            <table ref={billingRegisterTableRef} className="table table-custom table-centered table-nowrap table-hover mb-0">
              <thead>
                {billingRegisterTab === "charges" ? (
                  <tr>
                    <th>Member</th>
                    <th>Date</th>
                    <th>Period</th>
                    <th>Expense Head</th>
                    <th>Bill Amount</th>
                    <th>Paid</th>
                    <th>Due</th>
                    <th>Status</th>
                  </tr>
                ) : (
                  <tr>
                    <th>Receipt</th>
                    <th>Member</th>
                    <th>Plot No</th>
                    <th>Date</th>
                    <th>Total</th>
                  </tr>
                )}
              </thead>
            </table>
          </div>
          <div className="row g-3 mt-3">
            {billingRegisterTab === "charges" ? (
              <>
                <div className="col-md-4"><div className="border rounded p-3"><div className="text-muted fs-13">Total Bill Amount</div><div className="fw-semibold">{money(billingRegisterTotals.total_bill_amount)}</div></div></div>
                <div className="col-md-4"><div className="border rounded p-3"><div className="text-muted fs-13">Total Paid</div><div className="fw-semibold">{money(billingRegisterTotals.total_paid)}</div></div></div>
                <div className="col-md-4"><div className="border rounded p-3"><div className="text-muted fs-13">Total Due</div><div className="fw-semibold">{money(billingRegisterTotals.total_due)}</div></div></div>
              </>
            ) : (
              <div className="col-md-4"><div className="border rounded p-3"><div className="text-muted fs-13">Total Collection</div><div className="fw-semibold">{money(billingRegisterTotals.total_collection)}</div></div></div>
            )}
          </div>
        </div>
      </div>
    );
  }

  function renderChartAccountsView() {
    return (
      <div className="card">
        <div className="card-header d-flex align-items-center justify-content-between gap-2">
          <h4 className="header-title mb-0">Chart Of Accounts</h4>
          <button
            className="btn btn-primary"
            onClick={() => {
              setEditingAccountId(null);
              setAccountCode("");
              setAccountName("");
              setAccountType("income");
              setWorkspaceTab("coa-entry");
            }}
            type="button"
          >
            <i className="ri-add-line me-1" />
            Add Account
          </button>
        </div>
        <div className="card-body p-0">
          <div className="table-responsive">
            <table className="table table-custom table-centered table-nowrap table-hover mb-0">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Account</th>
                  <th>Type</th>
                  <th>Active</th>
                  <th className="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                {accounts.map((account) => (
                  <tr key={account.id}>
                    <td>{account.code}</td>
                    <td>{account.name}</td>
                    <td>
                      <span className="badge bg-primary-subtle text-primary text-uppercase">{account.account_type}</span>
                    </td>
                    <td>
                      <div className="form-check form-switch mb-0">
                        <input
                          checked={account.is_active}
                          className="form-check-input"
                          disabled={isSubmitting}
                          onChange={(event) => void handleAccountActiveChange(account, event.target.checked)}
                          type="checkbox"
                        />
                      </div>
                    </td>
                    <td className="text-end">
                      <button className="btn btn-sm btn-light me-1" disabled={isSubmitting} onClick={() => handleAccountEdit(account)} type="button">
                        <i className="ri-pencil-line" />
                      </button>
                      <button className="btn btn-sm btn-danger" disabled={isSubmitting} onClick={() => void handleAccountDelete(account.id)} type="button">
                        <i className="ri-delete-bin-line" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {accounts.length === 0 ? <EmptyState label="No chart accounts found" /> : null}
          </div>
        </div>
      </div>
    );
  }

  function renderChartAccountEntry() {
    return (
      <div className="row justify-content-center">
        <div className="col-xl-6">
          <div className="card">
            <div className="card-header d-flex align-items-center justify-content-between gap-2">
              <h4 className="header-title mb-0">{editingAccountId ? "Edit Chart Account" : "Add Chart Account"}</h4>
              <button className="btn btn-light" onClick={() => setWorkspaceTab("coa-view")} type="button">
                Back To View
              </button>
            </div>
            <div className="card-body">
              <form onSubmit={handleAccountSubmit}>
                <div className="mb-3">
                  <label className="form-label">Code</label>
                  <input className="form-control" placeholder="Example: INC-001" value={accountCode} onChange={(event) => setAccountCode(event.target.value)} required />
                </div>
                <div className="mb-3">
                  <label className="form-label">Name</label>
                  <input className="form-control" placeholder="Example: Monthly Subscription" value={accountName} onChange={(event) => setAccountName(event.target.value)} required />
                </div>
                <div className="mb-3">
                  <label className="form-label">Account Type</label>
                  <select className="form-select" value={accountType} onChange={(event) => setAccountType(event.target.value)}>
                    <option value="income">Income</option>
                    <option value="expense">Expense</option>
                    <option value="both">Both</option>
                  </select>
                </div>
                <button className="btn btn-primary" disabled={isSubmitting} type="submit">
                  {editingAccountId ? "Update Account" : "Save Account"}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    );
  }

  function renderEntryView(entryType: "income" | "expense") {
    const amountLabel = entryType === "income" ? "Collection" : "Expense";
    const label = entryType === "income" ? "Receive" : "Payment";
    const tableRef = entryType === "income" ? incomeTableRef : expenseTableRef;
    const totals = entryTableTotals[entryType];
    const mode = entryTableMode[entryType];
    return (
      <>
          <div className="row row-cols-md-3 row-cols-1">
            <StatCard title="Income" value={money(accountingSummary?.total_income)} subtitle="All income entries" icon="ri-arrow-down-circle-line" tone="success" />
            <StatCard title="Expense" value={money(accountingSummary?.total_expense)} subtitle="All expense entries" icon="ri-arrow-up-circle-line" tone="warning" />
            <StatCard title="Net Balance" value={money(accountingSummary?.net_balance)} subtitle="Income less expense" icon="ri-bank-line" tone="info" />
          </div>
          <div className="card mb-3">
            <div className="card-header">
              <h4 className="header-title mb-0">Search by Date</h4>
            </div>
            <div className="card-body">
              <div className="row g-3 align-items-end">
                <div className="col-md-3">
                  <label className="form-label">From Date</label>
                  <input className="form-control" type="date" value={entryFromDate} onChange={(event) => setEntryFromDate(event.target.value)} />
                </div>
                <div className="col-md-3">
                  <label className="form-label">To Date</label>
                  <input className="form-control" type="date" value={entryToDate} onChange={(event) => setEntryToDate(event.target.value)} />
                </div>
                <div className="col-md-3">
                  <button
                    className="btn btn-outline-secondary me-2"
                    onClick={() => {
                      setEntryFromDate(defaultMonthRange.from);
                      setEntryToDate(defaultMonthRange.to);
                      reloadDataTable(tableRef.current);
                    }}
                    type="button"
                  >
                    Current Month
                  </button>
                </div>
              </div>
              <div className="text-muted small mt-2">
                If only <strong>From Date</strong> is set, the table shows that exact day&apos;s data.
              </div>
            </div>
          </div>
          <div className="card">
            <div className="card-header d-flex align-items-center justify-content-between gap-2">
              <h4 className="header-title mb-0">{label} Voucher Register</h4>
              <button
                className="btn btn-primary"
                onClick={() => {
                  setPendingEntries([]);
                  setWorkspaceTab(entryType === "income" ? "income-entry" : "expense-entry");
                }}
                type="button"
              >
                <i className="ri-add-line me-1" />
                Add {label} Voucher
              </button>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive accounting-grid-shell">
                <table ref={tableRef} className="table table-custom table-centered table-nowrap table-hover mb-0 accounting-grid-table">
                  <thead>
                    <tr>
                      <th>{mode === "voucher" ? `${label} Voucher` : `${label} Entry`}</th>
                      <th>Date</th>
                      <th>{entryType === "income" ? "Income Head" : "Expense Head"}</th>
                      <th>{amountLabel}</th>
                      <th>Remarks</th>
                      <th>Lines</th>
                      <th className="text-end">Actions</th>
                    </tr>
                  </thead>
                </table>
              </div>
              <div className="row g-3 p-3">
                <div className="col-md-4">
                  <div className="border rounded p-3">
                    <div className="text-muted fs-13">{entryType === "income" ? "Total Collection" : "Total Expense"}</div>
                    <div className="fw-semibold">{money(totals.grand_total)}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
      </>
    );
  }

  function renderEntryBatch(entryType: "income" | "expense") {
    const accountChoices = entryType === "income" ? incomeAccounts : expenseAccounts;
    const label = entryType === "income" ? "Receive" : "Payment";
    const accountOptions = accountChoices.map((account) => ({
      value: String(account.id),
      label: `${account.code} - ${account.name}`,
      meta: `${account.account_type.toUpperCase()} account`,
    }));
    return (
      <>
        <div className="row">
        <div className="col-xl-4">
          <div className="card voucher-date-card">
            <div className="card-header d-flex align-items-center justify-content-between gap-2">
              <h4 className="header-title mb-0">{label} Voucher Date</h4>
              <button className="btn btn-light" onClick={() => setWorkspaceTab(entryType === "income" ? "income-view" : "expense-view")} type="button">
                Back
              </button>
            </div>
            <div className="card-body">
              <label className="form-label">Date</label>
              <div className="input-group input-group-lg">
                <span className="input-group-text"><i className="ri-calendar-event-line" /></span>
                <input className="form-control" type="date" value={entryDate} onChange={(event) => setEntryDate(event.target.value)} />
              </div>
              <label className="form-label mt-3">Voucher Remarks</label>
              <textarea
                className="form-control voucher-remarks-textarea"
                value={entryVoucherRemarks}
                onChange={(event) => setEntryVoucherRemarks(event.target.value)}
                placeholder="Write voucher remarks"
              />
            </div>
          </div>
        </div>
        <div className="col-xl-8">
          <div className="card">
            <div className="card-header">
              <h4 className="header-title mb-0">Add {label} Item</h4>
            </div>
            <div className="card-body">
              <form onSubmit={(event) => handleAddEntryToList(entryType, event)}>
                <div className="row g-3 align-items-end">
                <div className="col-lg-5">
                  <SearchableDropdown
                    isOpen={entryAccountDropdownOpen}
                    label="Account"
                    onChange={(value) => {
                      void handleEntryAccountChange(value, entryType);
                    }}
                    onOpenChange={setEntryAccountDropdownOpen}
                    onSearchChange={setEntryAccountSearch}
                    options={accountOptions}
                    placeholder={`Search ${entryType} account`}
                    search={entryAccountSearch}
                    value={entryAccountId}
                  />
                </div>
                <div className="col-lg-3">
                  <label className="form-label">Amount</label>
                  <input className="form-control" type="number" value={entryAmount} onChange={(event) => setEntryAmount(event.target.value)} required />
                  {entryType === "income" && entryMappedIncomeAmount !== null ? (
                    <div className="form-text">
                      Auto-filled from mapped billing collection: {money(entryMappedIncomeAmount)}
                    </div>
                  ) : null}
                </div>
                <div className="col-lg-3">
                  <label className="form-label">Remarks</label>
                  <textarea
                    className="form-control entry-remarks-textarea"
                    value={entryRemarks}
                    onChange={(event) => setEntryRemarks(event.target.value)}
                    placeholder="Item remarks"
                  />
                </div>
                <div className="col-lg-1">
                  <button className="btn btn-primary w-100" type="submit"><i className="ri-add-line" /></button>
                </div>
                </div>
                {accountChoices.length === 0 ? (
                  <p className="text-warning fs-13 mb-0 mt-2">Add an active {entryType} chart account before posting.</p>
                ) : null}
              </form>
            </div>
          </div>
        </div>
        <div className="col-xl-12">
          <div className="card">
            <div className="card-header d-flex align-items-center justify-content-between gap-2">
              <h4 className="header-title mb-0">{label} Voucher Items</h4>
              <button className="btn btn-success" disabled={isSubmitting || pendingEntries.length === 0} onClick={() => void handleSavePendingEntries(entryType)} type="button">
                Save {label} Voucher
              </button>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-custom table-centered table-nowrap table-hover mb-0">
                  <thead>
                    <tr>
                      <th>Account</th>
                      <th className="text-end">Amount</th>
                      <th>Remarks</th>
                      <th className="text-end">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingEntries.map((entry, index) => (
                      <tr key={`${entry.account_id}-${index}`}>
                        <td>{entry.account_label}</td>
                        <td className="text-end">{money(entry.amount)}</td>
                        <td>{entry.remarks ?? "N/A"}</td>
                        <td className="text-end">
                          <button className="btn btn-sm btn-danger" onClick={() => setPendingEntries((current) => current.filter((_, itemIndex) => itemIndex !== index))} type="button">
                            <i className="ri-delete-bin-line" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  {pendingEntries.length > 0 ? (
                    <tfoot><tr><th>Total</th><th className="text-end">{money(pendingEntries.reduce((sum, item) => sum + item.amount, 0))}</th><th colSpan={2}></th></tr></tfoot>
                  ) : null}
                </table>
                {pendingEntries.length === 0 ? <EmptyState label="No pending entries added" /> : null}
              </div>
            </div>
          </div>
        </div>
      </div>
      </>
    );
  }

  function renderReports() {
    return (
      <>
        <div className="card">
          <div className="card-header">
            <h4 className="header-title">Report Filters</h4>
          </div>
          <div className="card-body">
            <form onSubmit={handleReportLoad}>
              <div className="row">
                <div className="col-xl-3 col-md-6 mb-3">
                  <label className="form-label">Report Type</label>
                  <select className="form-select" value={reportType} onChange={(event) => setReportType(event.target.value)}>
                    <option value="due-members">Due Members</option>
                    <option value="collections">Collections</option>
                    <option value="electricity-collection">Electricity Collection Report</option>
                    <option value="income-detail">Income Detail</option>
                    <option value="expense-detail">Expense Detail</option>
                    <option value="total-collection">Total Collection</option>
                    <option value="total-due">Total Due</option>
                    <option value="members">Total Member Summary</option>
                    <option value="member-statement">Single Member Due & Paid</option>
                    <option value="member-information-detail">Member Information Detail</option>
                    <option value="charges">Charges</option>
                    <option value="receipt-detail">Receipt Detail</option>
                    <option value="income-expense">Income vs Expense</option>
                  </select>
                </div>
                <div className="col-xl-3 col-md-6 mb-3">
                  <AsyncSearchableDropdown
                    isOpen={reportMemberDropdownOpen}
                    isLoading={reportMemberOptionsQuery.isFetching}
                    label="Member"
                    onChange={setReportMemberId}
                    onOpenChange={setReportMemberDropdownOpen}
                    onSearchChange={setReportMemberSearch}
                    options={reportMemberOptions}
                    placeholder={reportType === "member-statement" || reportType === "member-information-detail" ? "Search member" : "Optional member filter"}
                    search={reportMemberSearch}
                    value={reportMemberId}
                    helperText="Type at least 2 characters to search members."
                  />
                </div>
                <div className="col-xl-3 col-md-6 mb-3">
                  <label className="form-label">Category</label>
                  <select className="form-select" value={reportCategoryId} onChange={(event) => setReportCategoryId(event.target.value)}>
                    <option value="">All categories</option>
                    {categories.map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-xl-3 col-md-6 mb-3">
                  <label className="form-label">Period</label>
                  <select className="form-select" value={reportPeriodId} onChange={(event) => setReportPeriodId(event.target.value)}>
                    <option value="">All periods</option>
                    {billingPeriods.map((period) => (
                      <option key={period.id} value={period.id}>
                        {period.period_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-xl-3 col-md-6 mb-3">
                  <label className="form-label">From Date</label>
                  <input className="form-control" type="date" value={reportFromDate} onChange={(event) => setReportFromDate(event.target.value)} />
                </div>
                <div className="col-xl-3 col-md-6 mb-3">
                  <label className="form-label">To Date</label>
                  <input className="form-control" type="date" value={reportToDate} onChange={(event) => setReportToDate(event.target.value)} />
                </div>
                <div className="col-xl-3 col-md-6 mb-3">
                  <label className="form-label">Receipt</label>
                  <select className="form-select" value={reportReceiptId} onChange={(event) => setReportReceiptId(event.target.value)}>
                    <option value="">Select receipt</option>
                    {receipts.map((receipt) => (
                      <option key={receipt.id} value={receipt.id}>
                        {receipt.receipt_no}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-xl-3 col-md-6 mb-3">
                  <label className="form-label">Plot No</label>
                  <input
                    className="form-control"
                    placeholder="Filter by plot no"
                    type="text"
                    value={reportPlotNo}
                    onChange={(event) => setReportPlotNo(event.target.value)}
                  />
                </div>
                <div className="col-xl-3 col-md-6 mb-3 d-flex align-items-end gap-2">
                  <button className="btn btn-primary" disabled={isSubmitting} type="submit">
                    Load Report
                  </button>
                  <button className="btn btn-light" onClick={() => openReportExport("html")} type="button">
                    HTML
                  </button>
                  <button className="btn btn-light" onClick={() => openReportExport("xlsx")} type="button">
                    XLSX
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
        {(currentReport || currentPagedReport || incomeExpenseReport || receiptReport || memberStatementReport || memberInformationDetailReport) && !showReportViewer ? (
          <div className="alert alert-info border-0">
            Last loaded report is ready. Click <strong>Load Report</strong> again to reopen the preview and print it.
          </div>
        ) : null}
      </>
    );
  }

  function renderMessaging() {
    const previewMember =
      smsEligibleMembers.find((member) => member.id === smsSelectedMemberIds[0]) ??
      (smsSingleMemberQuery.data && smsMemberId
        ? {
            id: smsSingleMemberQuery.data.id,
            member_code: smsSingleMemberQuery.data.member_code,
            full_name: smsSingleMemberQuery.data.full_name,
            plot_no: smsSingleMemberQuery.data.plot_no,
            plot_count: smsSingleMemberQuery.data.plot_count,
            cell_no: smsSingleMemberQuery.data.cell_no,
            category_id: smsSingleMemberQuery.data.category_id,
            category_name: smsSingleMemberQuery.data.category_name,
            joined_on: smsSingleMemberQuery.data.joined_on,
            is_active: smsSingleMemberQuery.data.is_active,
          }
        : smsEligibleMembers[0] ?? null);
    const allSelected = smsFilteredMembers.length > 0 && smsFilteredMembers.every((member) => smsSelectedMemberIds.includes(member.id));
    const progressPercent =
      smsBulkProgress.total > 0 ? Math.round((smsBulkProgress.completed / smsBulkProgress.total) * 100) : 0;

    return (
      <>
        <ul className="nav nav-tabs nav-bordered mb-3">
          <li className="nav-item">
            <button className={smsActiveTab === "send" ? "nav-link active" : "nav-link"} onClick={() => setSmsActiveTab("send")} type="button">
              Send SMS
            </button>
          </li>
          <li className="nav-item">
            <button className={smsActiveTab === "delivery" ? "nav-link active" : "nav-link"} onClick={() => setSmsActiveTab("delivery")} type="button">
              Delivery & Recent
            </button>
          </li>
          <li className="nav-item">
            <button className={smsActiveTab === "gateway" ? "nav-link active" : "nav-link"} onClick={() => setSmsActiveTab("gateway")} type="button">
              Gateway Status
            </button>
          </li>
        </ul>

        {smsActiveTab === "send" ? (
          <>
            <div className="card">
              <div className="card-header d-flex align-items-center justify-content-between gap-2">
                <h4 className="header-title mb-0">Message Template</h4>
                <button className="btn btn-primary" onClick={() => openSmsTemplateModal()} type="button">
                  <i className="ri-add-line me-1" />
                  New Template
                </button>
              </div>
              <div className="card-body">
                <div className="row">
                  <div className="col-xl-8">
                    <label className="form-label">Template</label>
                    <select className="form-select" value={smsSelectedTemplateId} onChange={(event) => setSmsSelectedTemplateId(event.target.value)}>
                      <option value="">No template</option>
                      {smsTemplates.map((template) => (
                        <option key={template.id} value={template.id}>
                          {template.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="col-xl-4 d-flex align-items-end mt-2 mt-xl-0">
                    <button
                      className="btn btn-light w-100"
                      disabled={!selectedSmsTemplate}
                      onClick={() => selectedSmsTemplate && openSmsTemplateModal(selectedSmsTemplate)}
                      type="button"
                    >
                      <i className="ri-pencil-line me-1" />
                      Edit Selected
                    </button>
                  </div>
                </div>
                <div className="mt-3">
                    <label className="form-label">Message Body</label>
                  <textarea className="form-control" rows={5} value={smsMessageBody} onChange={(event) => setSmsMessageBody(event.target.value)} />
                  </div>
                <div className="alert alert-secondary py-2 mb-0 mt-3">
                  Placeholders: `(name)`, `(bill)`, `(due)`, `(member_code)`, `(phone)`, `{"{{name}}"}`, `{"{{bill}}"}`, `{"{{due}}"}`, `{"{{member_code}}"}`, `{"{{phone}}"}`
                  </div>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h4 className="header-title">Recipient Selection And Progress</h4>
              </div>
              <div className="card-body">
                <div className="row mb-3 align-items-end">
                  <div className="col-md-4 mb-3 mb-md-0">
                    <label className="form-label">Send Type</label>
                    <select
                      className="form-select"
                      value={smsTargetMode}
                      onChange={(event) => {
                        setSmsTargetMode(event.target.value as "single" | "all" | "due");
                        setSmsMemberId("");
                        setSmsMemberSearch("");
                        setSmsRecipientSearch("");
                      }}
                    >
                      <option value="single">Single Customer</option>
                      <option value="all">All Customer</option>
                      <option value="due">Due Customer</option>
                    </select>
                  </div>
                  <div className="col-md-4 mb-3 mb-md-0">
                    <label className="form-label">Category</label>
                    <select className="form-select" value={smsCategoryFilterId} onChange={(event) => setSmsCategoryFilterId(event.target.value)}>
                      <option value="">All categories</option>
                      {categories.map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  {smsTargetMode === "single" ? (
                    <div className="col-md-4">
                      <AsyncSearchableDropdown
                        isOpen={smsMemberDropdownOpen}
                        isLoading={smsMemberOptionsQuery.isFetching}
                        label="Member"
                        onChange={setSmsMemberId}
                        onOpenChange={setSmsMemberDropdownOpen}
                        onSearchChange={setSmsMemberSearch}
                        options={memberOptions}
                        placeholder="Search member"
                        search={smsMemberSearch}
                        value={smsMemberId}
                        helperText="Type at least 2 characters to search members with phone numbers."
                      />
                    </div>
                  ) : null}
                </div>

                <div className="row mb-3">
                  <div className="col-md-4">
                    <span className="text-muted fs-12">Eligible Customers</span>
                    <h5 className="fs-14 mt-1 mb-0">{smsEligibleMembers.length}</h5>
                  </div>
                  <div className="col-md-4">
                    <span className="text-muted fs-12">Selected</span>
                    <h5 className="fs-14 mt-1 mb-0">{smsSelectedMemberIds.length}</h5>
                  </div>
                  <div className="col-md-4">
                    <span className="text-muted fs-12">Preview Customer</span>
                    <h5 className="fs-14 mt-1 mb-0">{previewMember?.full_name ?? "None"}</h5>
                  </div>
                </div>

                {smsBulkProgress.total > 0 ? (
                  <div className="mb-3">
                    <div className="d-flex justify-content-between mb-1">
                      <span className="text-muted fs-12">Sending Progress</span>
                      <span className="text-muted fs-12">
                        {smsBulkProgress.completed}/{smsBulkProgress.total} ({progressPercent}%)
                      </span>
                    </div>
                    <div className="progress mb-2" style={{ height: '10px' }}>
                      <div
                        className="progress-bar progress-bar-striped progress-bar-animated"
                        role="progressbar"
                        style={{ width: `${progressPercent}%` }}
                      />
                    </div>
                    <div className="d-flex gap-3 flex-wrap text-muted fs-12">
                      <span>Current: {smsBulkProgress.currentRecipient || "Waiting"}</span>
                      <span>Success: {smsBulkProgress.success}</span>
                      <span>Failed: {smsBulkProgress.failed}</span>
                    </div>
                    {smsBulkProgressRows.length > 0 ? (
                      <div className="table-responsive mt-2" style={{ maxHeight: "180px", overflowY: "auto" }}>
                        <table className="table table-sm table-custom table-centered mb-0">
                          <tbody>
                            {smsBulkProgressRows.map((row) => (
                              <tr key={`${row.memberId}-${row.status}-${row.phone}`}>
                                <td>{row.name}</td>
                                <td>{row.phone}</td>
                                <td>
                                  <span className={row.status === "sent" ? "badge bg-success-subtle text-success" : "badge bg-danger-subtle text-danger"}>
                                    {row.status}
                                  </span>
                                </td>
                                <td className="text-muted">{row.message}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : null}
                  </div>
                ) : null}

                <div className="border rounded p-3 mb-3 bg-body-tertiary">
                  <span className="text-muted fs-12">Personalized Preview</span>
                  <p className="mb-0 mt-2">{renderSmsPreview(previewMember) || "Write or select a template to preview the final SMS."}</p>
                </div>

                <div className="row g-3">
                  <div className="col-xl-7">
                    <div className="d-flex align-items-center justify-content-between gap-2 mb-2">
                      <div>
                        <h5 className="fs-15 mb-1">Customer Selection</h5>
                        <span className="text-muted fs-12">
                          Showing {smsFilteredMembers.length} of {smsEligibleMembers.length} customers
                        </span>
                      </div>
                      <button className="btn btn-sm btn-light" onClick={() => setSmsSelectedMemberIds([])} type="button">
                        Clear
                      </button>
                    </div>
                    <div className="input-group mb-2">
                      <span className="input-group-text">
                        <i className="ri-search-line" />
                      </span>
                      <input
                        className="form-control"
                        onChange={(event) => setSmsRecipientSearch(event.target.value)}
                        placeholder="Search by name, code, or number"
                        value={smsRecipientSearch}
                      />
                      {smsRecipientSearch ? (
                        <button className="btn btn-light" onClick={() => setSmsRecipientSearch("")} type="button">
                          <i className="ri-close-line" />
                        </button>
                      ) : null}
                    </div>
                    <div className="table-responsive border rounded" style={{ maxHeight: "420px", overflowY: "auto" }}>
                      <table className="table table-custom table-centered table-nowrap table-hover mb-0">
                        <thead>
                          <tr>
                            <th style={{ width: "48px" }}>
                              <input checked={allSelected} onChange={(event) => toggleAllSmsMembers(event.target.checked)} type="checkbox" />
                            </th>
                            <th>Customer</th>
                            <th>Phone</th>
                            <th>Due</th>
                            <th />
                          </tr>
                        </thead>
                        <tbody>
                          {smsFilteredMembers.map((member) => (
                            <tr key={member.id}>
                              <td>
                                <input checked={smsSelectedMemberIds.includes(member.id)} onChange={() => toggleSmsMemberSelection(member.id)} type="checkbox" />
                              </td>
                              <td>
                                <span className="fw-semibold d-block">{member.full_name}</span>
                                <span className="text-muted fs-12">
                                  {member.member_code}
                                  {member.category_name ? ` | ${member.category_name}` : ""}
                                </span>
                              </td>
                              <td>{member.cell_no ?? "N/A"}</td>
                              <td>{money(dueByMemberId.get(member.id)?.total_due ?? 0)}</td>
                              <td>
                                <button className="btn btn-sm btn-light" onClick={() => setSmsSelectedMemberIds([member.id])} type="button">
                                  Only
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {smsFilteredMembers.length === 0 ? <EmptyState label="No SMS recipients found for the current search" /> : null}
                    </div>
                  </div>

                  <div className="col-xl-5">
                    <div className="d-flex align-items-center justify-content-between gap-2 mb-2">
                      <div>
                        <h5 className="fs-15 mb-1">Ready To Send</h5>
                        <span className="text-muted fs-12">{smsSelectedMembers.length} customers selected for one-by-one sending</span>
                      </div>
                      <span className="badge bg-info-subtle text-info">{smsSelectedMembers.length}</span>
                    </div>
                    <div className="table-responsive border rounded" style={{ maxHeight: "420px", overflowY: "auto" }}>
                      <table className="table table-custom table-centered table-nowrap table-hover mb-0">
                        <thead>
                          <tr>
                            <th>Customer</th>
                            <th>Phone</th>
                            <th />
                          </tr>
                        </thead>
                        <tbody>
                          {smsSelectedMembers.map((member) => (
                            <tr key={member.id}>
                              <td>
                                <span className="fw-semibold d-block">{member.full_name}</span>
                                <span className="text-muted fs-12">{member.member_code}</span>
                              </td>
                              <td>{member.cell_no ?? "N/A"}</td>
                              <td>
                                <button className="btn btn-sm btn-soft-danger" onClick={() => toggleSmsMemberSelection(member.id)} type="button">
                                  Remove
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {smsSelectedMembers.length === 0 ? <EmptyState label="Select customers from the left grid" /> : null}
                    </div>
                  </div>
                </div>

                <div className="d-flex justify-content-end mt-3">
                  <button className="btn btn-success" disabled={isSubmitting || smsBulkProgress.running} onClick={() => void handleBulkSmsSend()} type="button">
                    Send SMS To Selected
                  </button>
                </div>
              </div>
            </div>
          </>
        ) : null}

        {smsActiveTab === "delivery" ? (
          <>
            <div className="row">
              <div className="col-xl-6">
                <div className="card">
                  <div className="card-header">
                    <h4 className="header-title">Templates</h4>
                  </div>
                  <div className="card-body p-0">
                    <div className="table-responsive">
                      <table className="table table-custom table-centered table-sm table-nowrap table-hover mb-0">
                        <tbody>
                          {smsTemplates.map((template) => (
                            <tr key={template.id}>
                              <td>
                                <h5 className="fs-14 mt-1">{template.name}</h5>
                                <span className="text-muted fs-12">{template.template_type ?? "General"}</span>
                              </td>
                              <td>{template.body}</td>
                              <td>
                                <button className="btn btn-sm btn-light" onClick={() => openSmsTemplateModal(template)} type="button">
                                  Edit
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
              <div className="col-xl-6">
                <div className="card">
                  <div className="card-header d-flex align-items-center justify-content-between gap-2 flex-wrap">
                    <h4 className="header-title mb-0">Recent Messages</h4>
                    <div className="d-flex gap-2 align-items-center">
                      <input
                        className="form-control form-control-sm"
                        placeholder="Search recipient or status"
                        value={smsMessageSearch}
                        onChange={(event) => {
                          setSmsMessageOffset(0);
                          setSmsMessageSearch(event.target.value);
                        }}
                        style={{ width: "220px" }}
                      />
                      <span className="badge bg-primary-subtle text-primary">{smsMessagesQuery.data?.total ?? smsMessages.length}</span>
                    </div>
                  </div>
                  <div className="card-body p-0">
                    <div className="table-responsive">
                      <table className="table table-custom table-centered table-sm table-nowrap table-hover mb-0">
                        <thead>
                          <tr>
                            <th>Recipient</th>
                            <th>Status</th>
                            <th>Created</th>
                            <th />
                          </tr>
                        </thead>
                        <tbody>
                          {smsMessages.map((sms) => (
                            <tr key={sms.id}>
                              <td>{sms.recipient}</td>
                              <td>
                                <span className="badge bg-info-subtle text-info">{sms.status}</span>
                              </td>
                              <td>{shortDate(sms.created_at)}</td>
                              <td>
                                <button className="btn btn-sm btn-light" disabled={isSubmitting} onClick={() => void handleSmsSendNow(sms.id)} type="button">
                                  Send Now
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      <div className="d-flex justify-content-between align-items-center px-3 py-2 border-top">
                        <small className="text-muted">
                          Showing {smsMessages.length} of {smsMessagesQuery.data?.total ?? smsMessages.length}
                        </small>
                        <div className="d-flex gap-2">
                          <button className="btn btn-sm btn-light" disabled={smsMessageOffset === 0} onClick={() => setSmsMessageOffset((current) => Math.max(current - 8, 0))} type="button">
                            Previous
                          </button>
                          <button
                            className="btn btn-sm btn-light"
                            disabled={smsMessageOffset + smsMessages.length >= (smsMessagesQuery.data?.total ?? 0)}
                            onClick={() => setSmsMessageOffset((current) => current + 8)}
                            type="button"
                          >
                            Next
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-header d-flex align-items-center justify-content-between gap-2 flex-wrap">
                <h4 className="header-title mb-0">Delivery Attempts</h4>
                <div className="d-flex gap-2 align-items-center">
                  <input
                    className="form-control form-control-sm"
                    placeholder="Search attempts"
                    value={smsAttemptSearch}
                    onChange={(event) => {
                      setSmsAttemptOffset(0);
                      setSmsAttemptSearch(event.target.value);
                    }}
                    style={{ width: "220px" }}
                  />
                  <span className="badge bg-primary-subtle text-primary">{smsAttemptsQuery.data?.total ?? smsAttempts.length}</span>
                </div>
              </div>
              <div className="card-body p-0">
                <div className="table-responsive">
                  <table className="table table-custom table-centered table-sm table-nowrap table-hover mb-0">
                    <tbody>
                      {smsAttempts.map((attempt) => (
                        <tr key={attempt.id}>
                          <td>Message #{attempt.sms_message_id}</td>
                          <td>{attempt.provider_name ?? "provider"}</td>
                          <td>{attempt.provider_status ?? "unknown"}</td>
                          <td>{shortDate(attempt.attempted_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <div className="d-flex justify-content-between align-items-center px-3 py-2 border-top">
                    <small className="text-muted">
                      Showing {smsAttempts.length} of {smsAttemptsQuery.data?.total ?? smsAttempts.length}
                    </small>
                    <div className="d-flex gap-2">
                      <button className="btn btn-sm btn-light" disabled={smsAttemptOffset === 0} onClick={() => setSmsAttemptOffset((current) => Math.max(current - 8, 0))} type="button">
                        Previous
                      </button>
                      <button
                        className="btn btn-sm btn-light"
                        disabled={smsAttemptOffset + smsAttempts.length >= (smsAttemptsQuery.data?.total ?? 0)}
                        onClick={() => setSmsAttemptOffset((current) => current + 8)}
                        type="button"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                  {smsAttempts.length === 0 ? <EmptyState label="No delivery attempts logged yet" /> : null}
                </div>
              </div>
            </div>
          </>
        ) : null}

        {smsActiveTab === "gateway" ? (
          <div className="card">
            <div className="card-header">
              <h4 className="header-title">SMS Gateway Status</h4>
            </div>
            <div className="card-body">
              <div className="row g-3">
                <div className="col-md-3">
                  <span className="text-muted fs-12">Provider</span>
                  <h5 className="fs-14 mt-1 mb-0">{smsIntegrationStatus?.provider_name ?? "unknown"}</h5>
                </div>
                <div className="col-md-3">
                  <span className="text-muted fs-12">Mode</span>
                  <h5 className="fs-14 mt-1 mb-0 text-uppercase">{smsIntegrationStatus?.provider_mode ?? "unknown"}</h5>
                </div>
                <div className="col-md-3">
                  <span className="text-muted fs-12">Configured</span>
                  <h5 className="fs-14 mt-1 mb-0">
                    {smsIntegrationStatus?.provider_configured ? (
                      <span className="badge bg-success-subtle text-success">Yes</span>
                    ) : (
                      <span className="badge bg-warning-subtle text-warning">No</span>
                    )}
                  </h5>
                </div>
                <div className="col-md-3">
                  <span className="text-muted fs-12">API Response</span>
                  <h5 className="fs-14 mt-1 mb-0">
                    {smsProviderCheck?.ok || smsIntegrationStatus?.provider_check_ok ? (
                      <span className="badge bg-success-subtle text-success">Responding</span>
                    ) : (
                      <span className="badge bg-danger-subtle text-danger">Not responding</span>
                    )}
                  </h5>
                </div>
                <div className="col-md-3">
                  <span className="text-muted fs-12">SMS Count</span>
                  <h5 className="fs-14 mt-1 mb-0">{smsIntegrationStatus?.message_count ?? smsMessages.length}</h5>
                </div>
                <div className="col-md-3">
                  <span className="text-muted fs-12">Sent Count</span>
                  <h5 className="fs-14 mt-1 mb-0">{smsIntegrationStatus?.sent_count ?? 0}</h5>
                </div>
                <div className="col-md-3">
                  <span className="text-muted fs-12">Attempt Count</span>
                  <h5 className="fs-14 mt-1 mb-0">{smsIntegrationStatus?.attempt_count ?? smsAttempts.length}</h5>
                </div>
                <div className="col-md-3">
                  <span className="text-muted fs-12">Balance</span>
                  <h5 className="fs-14 mt-1 mb-0">
                    {smsBalance?.dry_run ? "Dry run" : smsBalance?.balance ?? "Not checked"}
                  </h5>
                </div>
              </div>
              <div className="alert alert-warning mt-3 mb-0">
                {smsProviderCheck?.message ?? smsIntegrationStatus?.provider_check_message ?? "Check the provider without sending SMS."}
              </div>
              {smsProviderCheck?.response_sample ? (
                <div className="alert alert-secondary py-2 mt-3 mb-0 text-break">
                  <span className="fw-semibold">Provider reply:</span> {smsProviderCheck.response_sample}
                </div>
              ) : null}
              <div className="d-flex gap-2 flex-wrap mt-3">
                <button className="btn btn-info" disabled={isSubmitting} onClick={() => void handleSmsProviderCheck()} type="button">
                  Check API Response
                </button>
                <button className="btn btn-primary" disabled={isSubmitting} onClick={() => void handleSmsBalanceCheck()} type="button">
                  Check Balance
                </button>
                <button
                  className="btn btn-success"
                  disabled={isSubmitting || smsIntegrationStatus?.provider_mode === "bulksmsbd"}
                  onClick={() => void handleSmsProviderMode("bulksmsbd")}
                  type="button"
                >
                  Use BulkSMSBD
                </button>
                <button
                  className="btn btn-light"
                  disabled={isSubmitting || smsIntegrationStatus?.provider_mode === "simulated"}
                  onClick={() => void handleSmsProviderMode("simulated")}
                  type="button"
                >
                  Use Simulation
                </button>
              </div>
              <form className="border rounded p-3 mt-4" onSubmit={handleTestSmsSubmit}>
                <div className="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-3">
                  <div>
                    <h5 className="fs-15 mb-1">Send Test SMS</h5>
                    <p className="text-muted mb-0 fs-13">This uses the backend only. Dry-run mode will not spend credits.</p>
                  </div>
                  <span className={smsBalance?.dry_run ? "badge bg-warning-subtle text-warning" : "badge bg-info-subtle text-info"}>
                    {smsBalance?.dry_run ? "Dry run active" : "Server-side secured"}
                  </span>
                </div>
                <div className="row g-3">
                  <div className="col-md-4">
                    <label className="form-label">Recipient</label>
                    <input
                      className="form-control"
                      onChange={(event) => setSmsTestRecipient(event.target.value)}
                      placeholder="017XXXXXXXX"
                      value={smsTestRecipient}
                    />
                  </div>
                  <div className="col-md-8">
                    <label className="form-label">Message</label>
                    <textarea
                      className="form-control"
                      maxLength={918}
                      onChange={(event) => setSmsTestMessage(event.target.value)}
                      rows={3}
                      value={smsTestMessage}
                    />
                  </div>
                </div>
                <div className="d-flex justify-content-end mt-3">
                  <button className="btn btn-success" disabled={isSubmitting} type="submit">
                    Send Test SMS
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : null}

        {showSmsTemplateModal ? (
          <>
            <div className="modal fade show d-block" tabIndex={-1}>
              <div className="modal-dialog modal-lg modal-dialog-centered">
                <div className="modal-content">
                  <div className="modal-header">
                    <h5 className="modal-title">{editingSmsTemplateId ? "Edit SMS Template" : "New SMS Template"}</h5>
                    <button className="btn-close" onClick={() => setShowSmsTemplateModal(false)} type="button" />
                  </div>
                  <form onSubmit={handleSmsTemplateSubmit}>
                    <div className="modal-body">
                      <div className="mb-3">
                        <label className="form-label">Template Name</label>
                        <input className="form-control" value={smsTemplateName} onChange={(event) => setSmsTemplateName(event.target.value)} required />
                      </div>
                      <div className="mb-3">
                        <label className="form-label">Template Type</label>
                        <input className="form-control" value={smsTemplateType} onChange={(event) => setSmsTemplateType(event.target.value)} />
                      </div>
                      <div className="mb-3">
                        <label className="form-label">Body</label>
                        <textarea className="form-control" rows={6} value={smsTemplateBody} onChange={(event) => setSmsTemplateBody(event.target.value)} required />
                      </div>
                      <div className="alert alert-secondary py-2 mb-0">
                        Placeholders: `(name)`, `(bill)`, `(due)`, `(member_code)`, `(phone)`, `{"{{name}}"}`, `{"{{due}}"}`, `{"{{phone}}"}`
                      </div>
                    </div>
                    <div className="modal-footer">
                      <button className="btn btn-light" onClick={() => setShowSmsTemplateModal(false)} type="button">
                        Cancel
                      </button>
                      <button className="btn btn-primary" disabled={isSubmitting} type="submit">
                        Save Template
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
            <div className="modal-backdrop fade show" />
          </>
        ) : null}
      </>
    );
  }

  function renderProfile() {
    return (
      <div className="row">
        <div className="col-xl-4">
          <div className="card text-center">
            <div className="card-body">
              <img src={avatarUrl} className="rounded-circle avatar-xl img-thumbnail" alt="user" />
              <h4 className="mb-0 mt-2">{displayName}</h4>
              <p className="text-muted mb-3">{displayRole}</p>
              <span className="badge bg-success-subtle text-success">{profile?.is_active ? "Active account" : "Inactive account"}</span>
            </div>
          </div>
          <div className="card">
            <div className="card-header">
              <h4 className="header-title">Permissions</h4>
            </div>
            <div className="card-body">
              <div className="d-flex flex-wrap gap-2">
                {profile?.permissions.map((permission) => (
                  <span className="badge bg-primary-subtle text-primary fs-12" key={permission}>
                    {permission}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
        <div className="col-xl-8">
          <div className="card">
            <div className="card-header">
              <h4 className="header-title">Edit User Information</h4>
            </div>
            <div className="card-body">
              <form>
                <div className="row">
                  <div className="col-md-6 mb-3">
                    <label className="form-label">Display Name</label>
                    <input className="form-control" value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
                  </div>
                  <div className="col-md-6 mb-3">
                    <label className="form-label">Role</label>
                    <input className="form-control" value={displayRole} onChange={(event) => setDisplayRole(event.target.value)} />
                  </div>
                  <div className="col-md-6 mb-3">
                    <label className="form-label">Email</label>
                    <input className="form-control" value={displayEmail} onChange={(event) => setDisplayEmail(event.target.value)} />
                  </div>
                  <div className="col-md-6 mb-3">
                    <label className="form-label">Phone</label>
                    <input className="form-control" value={displayPhone} onChange={(event) => setDisplayPhone(event.target.value)} />
                  </div>
                  <div className="col-md-12 mb-3">
                    <label className="form-label">Profile Image</label>
                    <input className="form-control" type="file" accept="image/*" onChange={handleAvatarChange} />
                  </div>
                </div>
                <button className="btn btn-primary" onClick={() => setMessage("Profile display updated locally.")} type="button">
                  Save Display Profile
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    );
  }

  function isGroupOpen(group: string, activeTabs: WorkspaceTab[]) {
    void activeTabs;
    return openGroups[group] ?? false;
  }

  function toggleGroup(group: string) {
    setOpenGroups((current) => (current[group] ? {} : { [group]: true }));
  }

  function handleWorkspaceNavigation(tab: WorkspaceTab) {
    if (tab === "categories") setCategoryPageMode("view");
    if (tab === "packages") setPackagePageMode("view");
    if (tab === "members") setMemberPageMode("view");
    setWorkspaceTab(tab);
  }

  function handleMenuSearchNavigation(tab: WorkspaceTab) {
    handleWorkspaceNavigation(tab);
    setMenuSearch("");
    setShowMenuSearchResults(false);
  }

  function renderNavLink(item: NavItem, isSubMenu = false) {
    return (
      <li className="side-nav-item" key={item.key}>
        <button
          className={workspaceTab === item.key ? "side-nav-link active" : "side-nav-link"}
          onClick={() => handleWorkspaceNavigation(item.key)}
          type="button"
        >
          {!isSubMenu ? (
            <span className="menu-icon">
              <i className={item.icon} />
            </span>
          ) : null}
          <span className="menu-text">{item.label}</span>
          {item.badge ? <span className="badge bg-danger rounded-pill">{item.badge}</span> : null}
        </button>
      </li>
    );
  }

  function renderNavGroup(group: string, label: string, icon: string, children: NavItem[]) {
    const activeTabs = children.map((child) => child.key);
    const open = isGroupOpen(group, activeTabs);

    return (
      <li className="side-nav-item">
        <button
          className={`${activeTabs.includes(workspaceTab) ? "side-nav-link active" : "side-nav-link"}${open ? " menu-open" : ""}`}
          onClick={() => toggleGroup(group)}
          type="button"
        >
          <span className="menu-icon">
            <i className={icon} />
          </span>
          <span className="menu-text">{label}</span>
          <span className="menu-arrow" />
        </button>
        <div className={open ? "side-nav-collapse show" : "side-nav-collapse"}>
          <ul className="sub-menu">{children.map((child) => renderNavLink(child, true))}</ul>
        </div>
      </li>
    );
  }

  function renderSettingsPanel() {
    if (!showSettings) return null;

    function radioCard(active: boolean, label: string, onClick: () => void, preview: ReactNode, cols = "col-4") {
      return (
        <div className={cols}>
          <div className="form-check card-radio">
            <input className="form-check-input" type="radio" checked={active} onChange={onClick} />
            <button className="form-check-label p-0 w-100 theme-card-button" onClick={onClick} type="button">
              {preview}
            </button>
          </div>
          <h5 className="fs-14 text-center text-muted mt-2">{label}</h5>
        </div>
      );
    }

    function colorDot(colorClass: string) {
      return (
        <span className="d-flex align-items-center justify-content-center h-100">
          <span className={`p-2 d-inline-flex shadow rounded-circle ${colorClass}`} />
        </span>
      );
    }

    function layoutPreview(mode: "fluid" | "detached") {
      return (
        <span className={mode === "detached" ? "theme-preview detached" : "theme-preview"}>
          <span className="theme-preview-top" />
          <span className="theme-preview-body">
            <span className="theme-preview-menu" />
            <span className="theme-preview-content" />
          </span>
        </span>
      );
    }

    function sidebarPreview(size: SidenavSize) {
      return (
        <span className={`theme-preview sidebar-${size}`}>
          <span className="theme-preview-body">
            <span className="theme-preview-menu">
              <span />
              <span />
              <span />
              <span />
            </span>
            <span className="theme-preview-content" />
          </span>
        </span>
      );
    }

    return (
      <>
        <div className="offcanvas offcanvas-end show theme-settings-panel" id="theme-settings-offcanvas" tabIndex={-1}>
          <div className="d-flex align-items-center gap-2 px-3 py-3 offcanvas-header border-bottom border-dashed">
            <h5 className="flex-grow-1 mb-0">Theme Settings</h5>
            <button className="btn-close" onClick={() => setShowSettings(false)} type="button" />
          </div>

          <div className="offcanvas-body p-0 h-100">
            <div className="p-3 border-bottom border-dashed">
              <h5 className="mb-3 fs-16 fw-bold">Color Scheme</h5>
              <div className="row">
                {radioCard(themeMode === "light", "Light", () => setThemeMode("light"), <span className="avatar-xl w-100 d-flex align-items-center justify-content-center"><i className="ri-sun-line fs-32 text-muted" /></span>)}
                {radioCard(themeMode === "dark", "Dark", () => setThemeMode("dark"), <span className="avatar-xl w-100 d-flex align-items-center justify-content-center"><i className="ri-moon-line fs-32 text-muted" /></span>)}
              </div>
            </div>

            <div className="p-3 border-bottom border-dashed">
              <h5 className="mb-3 fs-16 fw-bold">Layout Mode</h5>
              <div className="row">
                {radioCard(layoutMode === "fluid", "Fluid", () => setLayoutMode("fluid"), layoutPreview("fluid"))}
                {radioCard(layoutMode === "detached", "Detached", () => setLayoutMode("detached"), layoutPreview("detached"))}
              </div>
            </div>

            <div className="p-3 border-bottom border-dashed">
              <h5 className="mb-3 fs-16 fw-bold">Topbar Color</h5>
              <div className="row">
                {radioCard(topbarColor === "light", "Light", () => setTopbarColor("light"), <span className="avatar-lg w-100 bg-light">{colorDot("bg-white")}</span>, "col-3")}
                {radioCard(topbarColor === "dark", "Dark", () => setTopbarColor("dark"), <span className="avatar-lg w-100 bg-light">{colorDot("bg-dark")}</span>, "col-3")}
                {radioCard(topbarColor === "brand", "Brand", () => setTopbarColor("brand"), <span className="avatar-lg w-100 bg-light">{colorDot("bg-primary")}</span>, "col-3")}
              </div>
            </div>

            <div className="p-3 border-bottom border-dashed">
              <h5 className="mb-3 fs-16 fw-bold">Menu Color</h5>
              <div className="row">
                {radioCard(menuColor === "light", "Light", () => setMenuColor("light"), <span className="avatar-lg w-100 bg-light">{colorDot("bg-white")}</span>, "col-3")}
                {radioCard(menuColor === "dark", "Dark", () => setMenuColor("dark"), <span className="avatar-lg w-100 bg-light">{colorDot("bg-dark")}</span>, "col-3")}
                {radioCard(menuColor === "brand", "Brand", () => setMenuColor("brand"), <span className="avatar-lg w-100 bg-light">{colorDot("bg-primary")}</span>, "col-3")}
              </div>
            </div>

            <div className="p-3 border-bottom border-dashed">
              <h5 className="mb-3 fs-16 fw-bold">Sidebar Size</h5>
              <div className="row">
                {radioCard(sidenavSize === "default", "Default", () => setSidenavSize("default"), sidebarPreview("default"))}
                {radioCard(sidenavSize === "compact", "Compact", () => setSidenavSize("compact"), sidebarPreview("compact"))}
                {radioCard(sidenavSize === "condensed", "Condensed", () => setSidenavSize("condensed"), sidebarPreview("condensed"))}
                {radioCard(sidenavSize === "sm-hover", "Hover View", () => setSidenavSize("sm-hover"), sidebarPreview("sm-hover"))}
                {radioCard(sidenavSize === "full", "Full Layout", () => setSidenavSize("full"), sidebarPreview("full"))}
                {radioCard(sidenavSize === "fullscreen", "Hidden", () => setSidenavSize("fullscreen"), sidebarPreview("fullscreen"))}
              </div>
            </div>
          </div>

          <div className="d-flex align-items-center gap-2 px-3 py-2 offcanvas-header border-top border-dashed">
            <button
              className="btn w-50 btn-soft-danger"
              onClick={() => {
                setThemeMode("dark");
                setLayoutMode("fluid");
                setMenuColor("brand");
                setTopbarColor("dark");
                setSidenavSize("default");
              }}
              type="button"
            >
              Reset
            </button>
            <button className="btn w-50 btn-soft-info" onClick={() => setShowSettings(false)} type="button">
              Apply
            </button>
          </div>
        </div>
        <div className="offcanvas-backdrop fade show" onClick={() => setShowSettings(false)} />
      </>
    );
  }

  function renderCurrentPage() {
    if (workspaceTab === "dashboard") return renderDashboard();
    if (workspaceTab === "categories") return renderCategories();
    if (workspaceTab === "packages") return renderPackages();
    if (workspaceTab === "members") return renderMembers();
    if (workspaceTab === "billing-heads-view" || workspaceTab === "billing-heads-entry") return renderBillingHeadsSetup();
    if (workspaceTab === "billing-mappings-view" || workspaceTab === "billing-mappings-entry") return renderBillingMappingsSetup();
    if (workspaceTab === "billing") return renderBilling();
    if (workspaceTab === "billing-registers") return renderBillingRegisters();
    if (workspaceTab === "coa-view") return renderChartAccountsView();
    if (workspaceTab === "coa-entry") return renderChartAccountEntry();
    if (workspaceTab === "income-view") return renderEntryView("income");
    if (workspaceTab === "income-entry") return renderEntryBatch("income");
    if (workspaceTab === "expense-view") return renderEntryView("expense");
    if (workspaceTab === "expense-entry") return renderEntryBatch("expense");
    if (workspaceTab === "reports") return renderReports();
    if (workspaceTab === "messaging") return renderMessaging();
    return renderProfile();
  }

  if (authState === "checking") {
    return (
      <div className="auth-bg d-flex min-vh-100 justify-content-center align-items-center">
        <div className="spinner-border text-primary" role="status" />
      </div>
    );
  }

    if (authState !== "authenticated" || !profile) {
    return <Auth onLoginSuccess={(user) => { setProfile(user); setAuthState("authenticated"); }} />;
  }

  return (
    <div className="wrapper">
      <div className="sidenav-menu">
        <a href="#" onClick={(event) => event.preventDefault()} className="logo">
          <span className="logo-light">
            <span className="logo-lg">
              <img src="/makan-logo-2.png" alt="Makan Society" className="app-brand-logo" />
            </span>
            <span className="logo-sm">
              <img src="/makan-logo-2.png" alt="Makan Society" className="app-brand-logo-sm" />
            </span>
          </span>
          <span className="logo-dark">
            <span className="logo-lg">
              <img src="/makan-logo-2.png" alt="Makan Society" className="app-brand-logo" />
            </span>
            <span className="logo-sm">
              <img src="/makan-logo-2.png" alt="Makan Society" className="app-brand-logo-sm" />
            </span>
          </span>
        </a>

        <button className="button-sm-hover" type="button">
          <i className="ri-circle-line align-middle" />
        </button>
        <button className="button-close-fullsidebar" type="button">
          <i className="ri-close-line align-middle" />
        </button>

        <div data-simplebar>
          <ul className="side-nav">
            <li className="side-nav-title">Navigation</li>
            {renderNavLink({ key: "dashboard", label: "Dashboard", icon: "ri-dashboard-3-line", badge: "5" })}
            {renderNavGroup("setup", "Setup", "ri-pages-line", [
              { key: "categories", label: "Category Setup", icon: "ri-list-check-3" },
              { key: "packages", label: "Package Setup", icon: "ri-stack-line" },
              { key: "billing-heads-view", label: "Billing Head", icon: "ri-price-tag-3-line" },
              { key: "billing-mappings-view", label: "Billing Mapping", icon: "ri-node-tree" },
            ])}
            {renderNavGroup("operations", "Operations", "ri-file-paper-line", [
              { key: "members", label: "Member Registration", icon: "ri-team-line" },
              { key: "billing", label: "Billing & Receipt", icon: "ri-file-list-3-line" },
              { key: "billing-registers", label: "Billing Registers", icon: "ri-table-line" },
            ])}
            {renderNavGroup("accounting", "Accounting", "ri-bank-line", [
              { key: "coa-view", label: "Chart Of Accounts", icon: "ri-book-2-line" },
              { key: "income-view", label: "Income Entry", icon: "ri-money-dollar-circle-line" },
              { key: "expense-view", label: "Expense Entry", icon: "ri-bank-card-line" },
            ])}
            {renderNavGroup("reporting", "Reporting", "ri-bar-chart-box-line", [
              { key: "reports", label: "Reports", icon: "ri-bar-chart-box-line" },
              { key: "messaging", label: "SMS", icon: "ri-message-3-line" },
            ])}
            <li className="side-nav-title">More</li>
            <li className="side-nav-item">
              <button className="side-nav-link" onClick={() => void loadWorkspace()} type="button">
                <span className="menu-icon">
                  <i className="ri-refresh-line" />
                </span>
                <span className="menu-text">Refresh Data</span>
              </button>
            </li>
          </ul>

          <div className="help-box text-center">
            <h5 className="fw-semibold fs-16">Makan Society</h5>
            <p className="mb-0 opacity-75">{message}</p>
          </div>
          <div className="clearfix" />
        </div>
      </div>

      <div className="color-line" />

      <header className="app-topbar">
        <div className="page-container topbar-menu">
          <div className="d-flex align-items-center gap-2">
            <a href="#" onClick={(event) => event.preventDefault()} className="logo">
              <span className="logo-light">
                <span className="logo-lg">
                  <img src="/makan-logo-2.png" alt="Makan Society" className="app-brand-logo" />
                </span>
                <span className="logo-sm">
                  <img src="/makan-logo-2.png" alt="Makan Society" className="app-brand-logo-sm" />
                </span>
              </span>
            </a>
            <button className="sidenav-toggle-button px-2" type="button">
              <i className="ri-menu-5-line fs-24" />
            </button>
            <div className="topbar-item d-none d-md-flex">
              <div>
                <h4 className="page-title fs-18 fw-bold mb-0">{pageTitle(workspaceTab)}</h4>
              </div>
            </div>
          </div>

          <div className="d-flex align-items-center gap-2">
            <div className="topbar-search d-none d-xl-flex me-2 align-items-center">
              <div className={`menu-search-box ${showMenuSearchResults ? "open" : ""}`}>
                <div className="menu-search-input-wrap">
                  <i className="ri-search-line fs-18" />
                  <input
                    className="menu-search-input"
                    onBlur={() => window.setTimeout(() => setShowMenuSearchResults(false), 120)}
                    onChange={(event) => {
                      setMenuSearch(event.target.value);
                      setShowMenuSearchResults(true);
                    }}
                    onFocus={() => setShowMenuSearchResults(true)}
                    onKeyDown={(event) => {
                      if (event.key === "Escape") {
                        setShowMenuSearchResults(false);
                        return;
                      }
                      if (event.key === "Enter" && filteredMenuItems.length > 0) {
                        event.preventDefault();
                        handleMenuSearchNavigation(filteredMenuItems[0].key);
                      }
                    }}
                    placeholder="Search menu and go to page"
                    value={menuSearch}
                  />
                </div>
                {showMenuSearchResults ? (
                  <div className="menu-search-results">
                    {filteredMenuItems.length > 0 ? (
                      filteredMenuItems.map((item) => (
                        <button
                          className="menu-search-result"
                          key={item.key}
                          onMouseDown={(event) => {
                            event.preventDefault();
                            handleMenuSearchNavigation(item.key);
                          }}
                          type="button"
                        >
                          <span className="menu-search-result-icon">
                            <i className={item.icon} />
                          </span>
                          <span className="menu-search-result-copy">
                            <strong>{item.label}</strong>
                            <small>{item.group ?? "Menu"}</small>
                          </span>
                        </button>
                      ))
                    ) : (
                      <div className="menu-search-empty">No menu found</div>
                    )}
                  </div>
                ) : null}
              </div>
            </div>
            <div className="topbar-item d-none d-sm-flex">
              <button className="topbar-link" onClick={() => window.location.reload()} type="button">
                <i className="ri-refresh-line fs-22" />
              </button>
            </div>
            <div className="topbar-item d-none d-sm-flex">
              <button className="topbar-link" onClick={() => setShowSettings(true)} type="button">
                <i className="ri-settings-4-line fs-22" />
              </button>
            </div>
            <div className="topbar-item d-none d-sm-flex">
              <button className="topbar-link" onClick={() => setThemeMode(themeMode === "dark" ? "light" : "dark")} type="button">
                <i className={themeMode === "dark" ? "ri-sun-line fs-22" : "ri-moon-line fs-22"} />
              </button>
            </div>
            <div className="topbar-item nav-user">
              <button
                className="topbar-link dropdown-toggle drop-arrow-none px-2"
                onClick={() => setShowUserMenu((current) => !current)}
                type="button"
              >
                <img src={avatarUrl} width="32" className="rounded-circle me-lg-2 d-flex" alt="user" />
                <span className="d-lg-flex flex-column gap-1 d-none nav-user-text">
                  <h5 className="my-0">{displayName}</h5>
                </span>
                <i className="ri-arrow-down-s-line d-none d-lg-block align-middle ms-2" />
              </button>
              <div className={`dropdown-menu dropdown-menu-end profile-dropdown ${showUserMenu ? "show" : ""}`}>
                <div className="dropdown-header noti-title">
                  <h6 className="text-overflow m-0">Welcome!</h6>
                </div>
                <button
                  className="dropdown-item"
                  onClick={() => {
                    setWorkspaceTab("profile");
                    setShowUserMenu(false);
                  }}
                  type="button"
                >
                  <i className="ri-account-circle-line me-1 fs-16 align-middle" />
                  <span>My Profile</span>
                </button>
                <button className="dropdown-item text-danger" onClick={handleLogout} type="button">
                  <i className="ri-logout-box-line me-1 fs-16 align-middle" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

	      <div className="page-content">
	        <div className="page-container">
	          {message ? (
	            <div className={`alert alert-${messageTone} border-0 mb-3`} role="alert">
	              {message}
	            </div>
	          ) : null}
	          {renderCurrentPage()}
	        </div>
	      </div>
      {renderSettingsPanel()}
      {renderPreviousBillsModal()}
      {renderInvoiceReportModal()}
      {renderReportViewerModal()}
    </div>
  );
}

