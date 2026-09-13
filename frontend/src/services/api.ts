import axios from "axios";
import type { Filters } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

function toParams(filters?: Filters) {
  if (!filters) return {};
  const params: Record<string, string> = {};
  Object.entries(filters).forEach(([k, v]) => {
    if (v) params[k] = v;
  });
  return params;
}

async function get<T>(path: string, filters?: Filters, extra?: Record<string, unknown>): Promise<T> {
  const response = await apiClient.get<T>(path, { params: { ...toParams(filters), ...extra } });
  return response.data;
}

export const api = {
  health: () => get<{ status: string; database_connected: boolean }>("/api/health"),
  dashboard: (filters?: Filters) => get("/api/dashboard", filters),
  sales: (filters?: Filters) => get("/api/sales", filters),
  customers: (filters?: Filters, page = 1, pageSize = 25, search?: string) =>
    get("/api/customers", filters, { page, page_size: pageSize, ...(search ? { search } : {}) }),
  products: (filters?: Filters) => get("/api/products", filters),
  regions: (filters?: Filters) => get("/api/regions", filters),
  employees: (filters?: Filters) => get("/api/employees", filters),
  churn: (filters?: Filters) => get("/api/churn", filters),
  rfm: (filters?: Filters) => get("/api/rfm", filters),
  forecast: () => get("/api/forecast"),
  insights: (filters?: Filters) => get("/api/insights", filters),
  dataQuality: () => get("/api/data-quality"),
};
