import { SearchableDropdown, SearchableOption } from "./SearchableDropdown";

type AsyncSearchableDropdownProps = {
  label: string;
  placeholder: string;
  options: SearchableOption[];
  value: string;
  search: string;
  isOpen: boolean;
  isLoading?: boolean;
  helperText?: string;
  onSearchChange: (value: string) => void;
  onOpenChange: (value: boolean) => void;
  onChange: (value: string) => void;
};

export function AsyncSearchableDropdown({
  label,
  placeholder,
  options,
  value,
  search,
  isOpen,
  isLoading = false,
  helperText,
  onSearchChange,
  onOpenChange,
  onChange,
}: AsyncSearchableDropdownProps) {
  const loadingOption = isLoading ? [{ value: "__loading__", label: "Loading...", meta: "Searching the server" }] : [];
  const safeOptions = isLoading ? loadingOption : options;

  return (
    <div>
      <SearchableDropdown
        label={label}
        placeholder={placeholder}
        options={safeOptions}
        value={value}
        search={search}
        isOpen={isOpen}
        onSearchChange={onSearchChange}
        onOpenChange={onOpenChange}
        onChange={(nextValue) => {
          if (nextValue === "__loading__") return;
          onChange(nextValue);
        }}
      />
      {helperText ? <div className="form-text">{helperText}</div> : null}
    </div>
  );
}
