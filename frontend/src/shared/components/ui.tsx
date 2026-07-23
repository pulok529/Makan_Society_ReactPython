import React from 'react';

export function CardMenu() {
  return (
    <div className="dropdown">
      <a href="#" className="dropdown-toggle drop-arrow-none card-drop" data-bs-toggle="dropdown" aria-expanded="false">
        <i className="ri-more-2-fill fs-18" />
      </a>
      <div className="dropdown-menu dropdown-menu-end">
        <span className="dropdown-item">Refresh</span>
        <span className="dropdown-item">Export</span>
        <span className="dropdown-item">Details</span>
      </div>
    </div>
  );
}

export function StatCard({
  title,
  value,
  subtitle,
  icon,
  tone,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: string;
  tone: "primary" | "success" | "warning" | "info";
}) {
  return (
    <div className="col">
      <div className="card">
        <div className="card-body">
          <div className="d-flex align-items-center gap-2 justify-content-between">
            <div>
              <h5 className="text-muted fs-13 fw-bold text-uppercase">{title}</h5>
              <h3 className="my-2 py-1 fw-bold">{value}</h3>
              <p className="mb-0 text-muted">
                <span className="text-success me-1">
                  <i className="ri-arrow-left-up-box-line" /> Live
                </span>
                <span className="text-nowrap">{subtitle}</span>
              </p>
            </div>
            <div className="avatar-xl flex-shrink-0">
              <span className={`avatar-title bg-${tone}-subtle text-${tone} rounded-circle fs-42`}>
                <i className={icon} />
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function MiniBars({ values, labels }: { values: number[]; labels: string[] }) {
  const max = Math.max(...values, 1);
  return (
    <div className="template-bars">
      {values.map((value, index) => (
        <div className="template-bar-column" key={`${labels[index]}-${index}`}>
          <div className="template-bar-track">
            <span className="template-bar-fill primary" style={{ height: `${Math.max((value / max) * 100, 6)}%` }} />
            <span
              className="template-bar-fill secondary"
              style={{ height: `${Math.max(((max - value / 2) / max) * 72, 8)}%` }}
            />
          </div>
          <span className="template-bar-label">{labels[index]}</span>
        </div>
      ))}
    </div>
  );
}

export function MiniArea({ income, expense }: { income: number[]; expense: number[] }) {
  const values = [...income, ...expense, 1];
  const max = Math.max(...values);
  const makePoints = (series: number[]) =>
    series
      .map((value, index) => {
        const x = 20 + index * (460 / Math.max(series.length - 1, 1));
        const y = 190 - (value / max) * 150;
        return `${x},${y}`;
      })
      .join(" ");

  return (
    <svg className="template-area" viewBox="0 0 520 220" role="img" aria-label="Collection and expense trend">
      {[40, 80, 120, 160, 200].map((y) => (
        <line className="template-grid-line" key={y} x1="15" x2="500" y1={y} y2={y} />
      ))}
      <polyline className="template-area-line income" points={makePoints(income)} />
      <polyline className="template-area-line expense" points={makePoints(expense)} />
    </svg>
  );
}

export function EmptyState({ label }: { label: string }) {
  return (
    <div className="text-center text-muted py-4">
      <i className="ri-inbox-2-line fs-28 d-block mb-1" />
      {label}
    </div>
  );
}
