type SearchableOption = {
  value: string;
  label: string;
  meta?: string;
};

type SearchableDropdownProps = {
  label: string;
  placeholder: string;
  options: SearchableOption[];
  value: string;
  search: string;
  isOpen: boolean;
  onSearchChange: (value: string) => void;
  onOpenChange: (value: boolean) => void;
  onChange: (value: string) => void;
};

export function SearchableDropdown({
  label,
  placeholder,
  options,
  value,
  search,
  isOpen,
  onSearchChange,
  onOpenChange,
  onChange,
}: SearchableDropdownProps) {
  const selected = options.find((option) => option.value === value);
  const filtered = options.filter((option) => {
    const needle = search.trim().toLowerCase();
    if (!needle) return true;
    return `${option.label} ${option.meta ?? ""}`.toLowerCase().includes(needle);
  });

  return (
    <div className="position-relative">
      <label className="form-label">{label}</label>
      <div className={`dropdown ${isOpen ? "show" : ""}`}>
        <div className="input-group">
          <span className="input-group-text">
            <i className="ri-search-line" />
          </span>
          <input
            className="form-control"
            onBlur={() => window.setTimeout(() => onOpenChange(false), 150)}
            onChange={(event) => {
              onSearchChange(event.target.value);
              onOpenChange(true);
            }}
            onFocus={() => onOpenChange(true)}
            placeholder={selected ? selected.label : placeholder}
            value={isOpen ? search : selected?.label ?? search}
          />
          {value ? (
            <button
              className="btn btn-light"
              onClick={() => {
                onChange("");
                onSearchChange("");
              }}
              type="button"
            >
              <i className="ri-close-line" />
            </button>
          ) : null}
        </div>
        <div className={`dropdown-menu w-100 ${isOpen ? "show" : ""}`} style={{ maxHeight: "260px", overflowY: "auto" }}>
          {filtered.map((option) => (
            <button
              className={option.value === value ? "dropdown-item active" : "dropdown-item"}
              key={option.value}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => {
                onChange(option.value);
                onSearchChange("");
                onOpenChange(false);
              }}
              type="button"
            >
              <span className="d-block fw-semibold">{option.label}</span>
              {option.meta ? <span className="d-block fs-12 opacity-75">{option.meta}</span> : null}
            </button>
          ))}
          {filtered.length === 0 ? <span className="dropdown-item text-muted">No results found</span> : null}
        </div>
      </div>
    </div>
  );
}

export type { SearchableOption };
