import { createContext, useContext, useState, type ReactNode } from "react";
import type { Filters } from "../types";

interface FilterContextValue {
  filters: Filters;
  setFilters: (f: Filters) => void;
  updateFilter: (key: keyof Filters, value: string | undefined) => void;
  clearFilters: () => void;
}

const FilterContext = createContext<FilterContextValue | undefined>(undefined);

export function FilterProvider({ children }: { children: ReactNode }) {
  const [filters, setFilters] = useState<Filters>({});

  const updateFilter = (key: keyof Filters, value: string | undefined) => {
    setFilters((prev) => {
      const next = { ...prev };
      if (value) {
        next[key] = value;
      } else {
        delete next[key];
      }
      return next;
    });
  };

  const clearFilters = () => setFilters({});

  return (
    <FilterContext.Provider value={{ filters, setFilters, updateFilter, clearFilters }}>
      {children}
    </FilterContext.Provider>
  );
}

export function useFilters() {
  const ctx = useContext(FilterContext);
  if (!ctx) throw new Error("useFilters must be used within FilterProvider");
  return ctx;
}
