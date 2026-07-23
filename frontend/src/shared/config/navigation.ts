import { NavItem, WorkspaceTab } from '../types/models';

export const navItems: NavItem[] = [
  { key: "dashboard", label: "Dashboard", icon: "ri-dashboard-3-line", group: "Home" },
  { key: "categories", label: "Category Setup", icon: "ri-list-check-3", group: "Setup" },
  { key: "members", label: "Member Registration", icon: "ri-team-line", group: "Operations" },
  { key: "billing-heads-view", label: "Billing Head", icon: "ri-price-tag-3-line", group: "Setup" },
  { key: "billing-mappings-view", label: "Billing Mapping", icon: "ri-node-tree", group: "Setup" },
  { key: "billing", label: "Billing & Receipt", icon: "ri-file-list-3-line", group: "Operations" },
  { key: "billing-registers", label: "Billing Registers", icon: "ri-table-line", group: "Operations" },
  { key: "coa-view", label: "Chart Of Accounts", icon: "ri-book-2-line", group: "Accounting" },
  { key: "coa-entry", label: "Add Chart Account", icon: "ri-add-box-line", group: "Accounting" },
  { key: "income-view", label: "Income Entry", icon: "ri-money-dollar-circle-line", group: "Accounting" },
  { key: "income-entry", label: "Add Income Entries", icon: "ri-add-circle-line", group: "Accounting" },
  { key: "expense-view", label: "Expense Entry", icon: "ri-bank-card-line", group: "Accounting" },
  { key: "expense-entry", label: "Add Expense Entries", icon: "ri-add-circle-line", group: "Accounting" },
  { key: "reports", label: "Reports", icon: "ri-bar-chart-box-line", group: "Reporting" },
  { key: "messaging", label: "SMS", icon: "ri-message-3-line", group: "Reporting" },
  { key: "profile", label: "User Profile", icon: "ri-account-circle-line", group: "Profile" },
];
