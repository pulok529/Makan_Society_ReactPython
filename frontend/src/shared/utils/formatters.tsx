import React from 'react';
import { ThemeSettings, UserProfile, Charge, WorkspaceTab } from '../types/models';
import { navItems } from '../config/navigation';
import { apiBaseUrl } from '../../shared/api/client';
const accessTokenKey = "society-modern-access-token";

export function readThemeSettings(): Partial<ThemeSettings> {
  try {
    return JSON.parse(localStorage.getItem("society-modern-theme") ?? "{}") as Partial<ThemeSettings>;
  } catch {
    return {};
  }
}

export function token() {
  return localStorage.getItem(accessTokenKey);
}

export async function fetchProfile(accessToken: string): Promise<UserProfile> {
  const response = await fetch(`${apiBaseUrl}/api/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  if (!response.ok) {
    throw new Error("Unable to load user profile");
  }

  return response.json();
}

export function getJQuery() {
  return (window as Window & { $?: any; jQuery?: any }).jQuery ?? (window as Window & { $?: any; jQuery?: any }).$;
}

export function reloadDataTable(tableElement: HTMLTableElement | null) {
  const jq = getJQuery();
  if (!tableElement || !jq?.fn?.DataTable || !jq.fn.DataTable.isDataTable(tableElement)) return;
  jq(tableElement).DataTable().ajax.reload(null, false);
}

export function fileNameFromDisposition(header: string | null, fallback: string) {
  if (!header) return fallback;
  const utf8Match = header.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1]);
    } catch {
      return utf8Match[1];
    }
  }
  const plainMatch = header.match(/filename=\"?([^\";]+)\"?/i);
  return plainMatch?.[1] ?? fallback;
}

export function money(value: number | null | undefined) {
  return Number(value ?? 0).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function shortDate(value: string | null | undefined) {
  if (!value) return "Not set";
  const dateOnlyMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (dateOnlyMatch) {
    const [, year, month, day] = dateOnlyMatch;
    return new Date(Number(year), Number(month) - 1, Number(day)).toLocaleDateString();
  }
  return new Date(value).toLocaleDateString();
}

export function dateKey(value: string | null | undefined) {
  if (!value) return "";
  const dateOnlyMatch = /^(\d{4}-\d{2}-\d{2})/.exec(value);
  if (dateOnlyMatch) return dateOnlyMatch[1];
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "";
  const year = parsed.getFullYear();
  const month = String(parsed.getMonth() + 1).padStart(2, "0");
  const day = String(parsed.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function isWithinDateRange(value: string | null | undefined, fromDate: string, toDate: string) {
  const key = dateKey(value);
  if (!key) return false;
  if (!fromDate && !toDate) return true;
  if (fromDate && !toDate) return key === fromDate;
  if (!fromDate && toDate) return key === toDate;
  const start = fromDate <= toDate ? fromDate : toDate;
  const end = fromDate <= toDate ? toDate : fromDate;
  return key >= start && key <= end;
}

export function currentMonthRange() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const firstDay = `${year}-${month}-01`;
  const lastDay = new Date(year, now.getMonth() + 1, 0).toISOString().slice(0, 10);
  return { from: firstDay, to: lastDay };
}

export function invoiceStatus(invoice: { is_cancelled: boolean; total_due_amount: number; total_receive_amount: number }) {
  if (invoice.is_cancelled) return "Cancelled";
  if (Number(invoice.total_due_amount) <= 0) return "Paid";
  if (Number(invoice.total_receive_amount) > 0) return "Partial";
  return "Due";
}

export function invoiceStatusBadgeClass(status: string) {
  if (status === "Cancelled") return "badge bg-secondary-subtle text-secondary";
  if (status === "Paid") return "badge bg-success-subtle text-success";
  if (status === "Partial") return "badge bg-warning-subtle text-warning";
  return "badge bg-danger-subtle text-danger";
}

export function chargeHeadSummary(charge: Charge) {
  const parts = charge.items
    .map((item) => item.description?.trim() || item.package_name?.trim() || item.item_type?.trim())
    .filter((value): value is string => Boolean(value));
  if (parts.length > 0) return parts.join(", ");
  return charge.charge_type;
}

export function pageTitle(tab: WorkspaceTab) {
  const item = navItems.find((navItem) => navItem.key === tab);
  return item?.label ?? "Dashboard";
}

export function statusBadge(active: boolean) {
  return active ? (
    <span className="badge bg-success-subtle text-success">Active</span>
  ) : (
    <span className="badge bg-danger-subtle text-danger">Inactive</span>
  );
}
