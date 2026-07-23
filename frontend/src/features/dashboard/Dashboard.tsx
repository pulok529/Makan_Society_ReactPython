import React from 'react';
import { CardMenu, StatCard, MiniBars, MiniArea, EmptyState } from '../../shared/components/ui';
import { money, shortDate } from '../../shared/utils/formatters';
import { WorkspaceTab } from '../../shared/types/models';

const assetBase = "/layout-template/assets";

type DashboardProps = {
  isDashboardReady: boolean;
  isWorkspaceLoading: boolean;
  members: any[];
  categories: any[];
  billingDashboard: any;
  receipts: any[];
  smsMessages: any[];
  memberTotalCount: number;
  activeMemberCountQuery: any;
  activeMembers: any[];
  totalCollection: number;
  smsIntegrationStatus: any;
  smsMessagesQuery: any;
  smsAttemptsQuery: any;
  smsAttempts: any[];
  accountingSummary: any;
  monthlyCollection: number[];
  monthlyExpense: number[];
  memberDueSummaries: any[];
  setWorkspaceTab: (tab: WorkspaceTab) => void;
};

export function Dashboard({
  isDashboardReady,
  isWorkspaceLoading,
  members,
  categories,
  billingDashboard,
  receipts,
  smsMessages,
  memberTotalCount,
  activeMemberCountQuery,
  activeMembers,
  totalCollection,
  smsIntegrationStatus,
  smsMessagesQuery,
  smsAttemptsQuery,
  smsAttempts,
  accountingSummary,
  monthlyCollection,
  monthlyExpense,
  memberDueSummaries,
  setWorkspaceTab
}: DashboardProps) {
    if (!isDashboardReady && isWorkspaceLoading) {
      return (
        <div className="card">
          <div className="card-body py-5 text-center">
            <div className="spinner-border text-primary mb-3" role="status" aria-hidden="true" />
            <h4 className="mb-2">Loading dashboard data...</h4>
            <p className="text-muted mb-0">We&apos;re pulling the main society totals first so the software opens faster.</p>
          </div>
        </div>
      );
    }

    const totalPlots = members.reduce((sum, member) => sum + Number(member.plot_count ?? 1), 0);
    const operationValues = [
      categories.length,
      members.length,
      totalPlots,
      billingDashboard?.total_open_charges ?? 0,
      receipts.length,
      smsMessages.length,
    ];
    const operationLabels = ["Cat", "Mem", "Plot", "Due", "Rec", "SMS"];

    return (
      <>
        {isWorkspaceLoading ? (
          <div className="alert alert-info border-0 d-flex align-items-center gap-2" role="alert">
            <span className="spinner-border spinner-border-sm" aria-hidden="true" />
            <span>Dashboard is ready. Remaining sections are still refreshing in the background.</span>
          </div>
        ) : null}

        <div className="row row-cols-xxl-4 row-cols-md-2 row-cols-1">
          <StatCard title="Total Members" value={String(memberTotalCount)} subtitle={`${activeMemberCountQuery.data?.total ?? activeMembers.length} active`} icon="ri-team-line" tone="primary" />
          <StatCard title="Total Collection" value={money(totalCollection)} subtitle={`${receipts.length} receipts`} icon="ri-wallet-3-line" tone="success" />
          <StatCard
            title="Open Due"
            value={money(billingDashboard?.total_due_amount)}
            subtitle={`${billingDashboard?.total_members_with_due ?? 0} members`}
            icon="ri-file-warning-line"
            tone="warning"
          />
          <StatCard title="SMS Messages" value={String(smsIntegrationStatus?.message_count ?? smsMessagesQuery.data?.total ?? smsMessages.length)} subtitle={`${smsIntegrationStatus?.attempt_count ?? smsAttemptsQuery.data?.total ?? smsAttempts.length} attempts`} icon="ri-message-3-line" tone="info" />
        </div>

        <div className="row">
          <div className="col-xl-6">
            <div className="card">
              <div className="d-flex card-header justify-content-between align-items-center">
                <h4 className="header-title">Statistics</h4>
                <CardMenu />
              </div>
              <div className="card-body px-0 pt-0">
                <div className="bg-light bg-opacity-50">
                  <div className="row text-center">
                    <div className="col-md-3 col-6">
                      <p className="text-muted mt-3 mb-1">Total Income</p>
                      <h4 className="mb-3">
                        <span className="ri-arrow-left-down-box-line text-success me-1" />
                        <span>{money(accountingSummary?.total_income)}</span>
                      </h4>
                    </div>
                    <div className="col-md-3 col-6">
                      <p className="text-muted mt-3 mb-1">Total Expenditure</p>
                      <h4 className="mb-3">
                        <span className="ri-arrow-left-up-box-line text-danger me-1" />
                        <span>{money(accountingSummary?.total_expense)}</span>
                      </h4>
                    </div>
                    <div className="col-md-3 col-6">
                      <p className="text-muted mt-3 mb-1">Open Charges</p>
                      <h4 className="mb-3">
                        <span className="ri-bar-chart-line me-1" />
                        <span>{billingDashboard?.total_open_charges ?? 0}</span>
                      </h4>
                    </div>
                    <div className="col-md-3 col-6">
                      <p className="text-muted mt-3 mb-1">Net Savings</p>
                      <h4 className="mb-3">
                        <span className="ri-bank-line me-1" />
                        <span>{money(accountingSummary?.net_balance)}</span>
                      </h4>
                    </div>
                  </div>
                </div>
                <div className="px-3">
                  <MiniBars values={operationValues} labels={operationLabels} />
                </div>
              </div>
            </div>
          </div>

          <div className="col-xl-6">
            <div className="card">
              <div className="d-flex card-header justify-content-between align-items-center">
                <h4 className="header-title">Total Revenue</h4>
                <CardMenu />
              </div>
              <div className="card-body px-0 pt-0">
                <div className="border-top border-bottom border-light border-dashed">
                  <div className="row text-center align-items-center">
                    <div className="col-md-3 col-6">
                      <p className="text-muted mt-3 mb-1">Revenue</p>
                      <h4 className="mb-3 text-success">{money(accountingSummary?.total_income)}</h4>
                    </div>
                    <div className="col-md-3 col-6 bg-light bg-opacity-50 border-start border-light border-dashed">
                      <p className="text-muted mt-3 mb-1">Expenses</p>
                      <h4 className="mb-3 text-danger">{money(accountingSummary?.total_expense)}</h4>
                    </div>
                    <div className="col-md-3 col-6 border-start border-end border-light border-dashed">
                      <p className="text-muted mt-3 mb-1">Due</p>
                      <h4 className="mb-3">{money(billingDashboard?.total_due_amount)}</h4>
                    </div>
                    <div className="col-md-3 col-6">
                      <img src={`${assetBase}/images/cards/american-express.svg`} alt="card" height="30" />
                      <img src={`${assetBase}/images/cards/discover-card.svg`} alt="card" height="30" />
                      <img src={`${assetBase}/images/cards/mastercard.svg`} alt="card" height="30" />
                    </div>
                  </div>
                </div>
                <div className="px-3">
                  <MiniArea income={monthlyCollection} expense={monthlyExpense} />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="row">
          <div className="col-xxl-4">
            <div className="card">
              <div className="d-flex card-header justify-content-between align-items-center">
                <h4 className="header-title">Transactions</h4>
                <button className="btn btn-sm btn-light" onClick={() => setWorkspaceTab("billing")} type="button">
                  Add New <i className="ri-add-line ms-1" />
                </button>
              </div>
              <div className="card-body p-0">
                <div className="bg-light bg-opacity-50 py-1 text-center">
                  <p className="m-0">
                    <b>{billingDashboard?.total_receipts ?? receipts.length}</b> receipts against <span className="fw-medium">{billingDashboard?.total_open_charges ?? 0}</span> open charges
                  </p>
                </div>
                <div className="table-responsive">
                  <table className="table table-custom table-centered table-sm table-nowrap table-hover mb-0">
                    <tbody>
                      {receipts.slice(0, 6).map((receipt) => (
                        <tr key={receipt.id}>
                          <td>
                            <span className="text-muted fs-12">Receipt No</span>
                            <h5 className="fs-14 mt-1">{receipt.receipt_no}</h5>
                          </td>
                          <td>
                            <span className="text-muted fs-12">Date</span>
                            <h5 className="fs-14 mt-1 fw-normal">{shortDate(receipt.payment_date)}</h5>
                          </td>
                          <td>
                            <span className="text-muted fs-12">Amount</span>
                            <h5 className="fs-14 mt-1 fw-normal">{money(receipt.total_amount)}</h5>
                          </td>
                          <td>
                            <span className="text-muted fs-12">Status</span>
                            <h5 className="fs-14 mt-1 fw-normal">
                              <i className="ri-circle-fill fs-12 text-success" /> Completed
                            </h5>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {receipts.length === 0 ? <EmptyState label="No receipts yet" /> : null}
                </div>
              </div>
            </div>
          </div>

          <div className="col-xxl-4">
            <div className="card card-h-100">
              <div className="card-header d-flex flex-wrap align-items-center gap-2">
                <h4 className="header-title me-auto">Recent New Members</h4>
                <button className="btn btn-sm btn-primary" onClick={() => setWorkspaceTab("members")} type="button">
                  Export <i className="ri-export-line ms-1" />
                </button>
              </div>
              <div className="card-body p-0">
                <div className="bg-light bg-opacity-50 py-1 text-center">
                  <p className="m-0">
                    <b>{activeMemberCountQuery.data?.total ?? activeMembers.length}</b> active members out of <span className="fw-medium">{memberTotalCount}</span>
                  </p>
                </div>
                <div className="table-responsive">
                  <table className="table table-custom table-centered table-sm table-nowrap table-hover mb-0">
                    <tbody>
                      {members.slice(0, 6).map((member, index) => (
                        <tr key={member.id}>
                          <td>
                            <div className="d-flex align-items-center">
                              <div className="avatar-md flex-shrink-0 me-2">
                                <span className="avatar-title bg-primary-subtle rounded-circle">
                                  <img src={`${assetBase}/images/users/avatar-${(index % 6) + 1}.jpg`} alt="" height="26" className="rounded-circle" />
                                </span>
                              </div>
                              <div>
                                <span className="text-muted fs-12">Name</span>
                                <h5 className="fs-14 mt-1">{member.full_name}</h5>
                              </div>
                            </div>
                          </td>
                          <td>
                            <span className="text-muted fs-12">Category</span>
                            <h5 className="fs-14 mt-1 fw-normal">{member.category_name ?? "None"}</h5>
                          </td>
                          <td>
                            <span className="text-muted fs-12">Status</span>
                            <h5 className="fs-14 mt-1 fw-normal">
                              <i className={`ri-circle-fill fs-12 ${member.is_active ? "text-success" : "text-danger"}`} />{" "}
                              {member.is_active ? "Active" : "Inactive"}
                            </h5>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {members.length === 0 ? <EmptyState label="No members yet" /> : null}
                </div>
              </div>
            </div>
          </div>

          <div className="col-xxl-4">
            <div className="card">
              <div className="d-flex card-header justify-content-between align-items-center">
                <h4 className="header-title">Due Members</h4>
                <button className="btn btn-sm btn-primary" onClick={() => setWorkspaceTab("reports")} type="button">
                  Refresh <i className="ri-refresh-line ms-1" />
                </button>
              </div>
              <div className="card-body p-0">
                <div className="table-responsive">
                  <table className="table table-custom table-centered table-sm table-nowrap table-hover mb-0">
                    <tbody>
                      {memberDueSummaries.slice(0, 6).map((summary) => (
                        <tr key={summary.member_id}>
                          <td>
                            <span className="text-muted fs-12">Member</span>
                            <h5 className="fs-14 mt-1">{summary.member_name}</h5>
                          </td>
                          <td>
                            <span className="text-muted fs-12">Open</span>
                            <h5 className="fs-14 mt-1 fw-normal">{summary.open_charge_count}</h5>
                          </td>
                          <td>
                            <span className="text-muted fs-12">Due</span>
                            <h5 className="fs-14 mt-1 fw-normal text-danger">{money(summary.total_due)}</h5>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {memberDueSummaries.length === 0 ? <EmptyState label="No open due" /> : null}
                </div>
              </div>
            </div>
          </div>
        </div>
      </>
    );
}
