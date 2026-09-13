export interface Filters {
  date_from?: string;
  date_to?: string;
  region?: string;
  category?: string;
  customer_segment?: string;
  salesperson?: string;
}

export interface DashboardKPIs {
  total_orders: number;
  total_revenue: number;
  total_profit: number;
  profit_margin_pct: number;
  active_customers: number;
  yoy_growth_pct: number | null;
}

export interface RevenueTrendPoint {
  month: string;
  revenue: number;
  profit: number;
}

export interface RegionRevenue {
  region: string;
  revenue: number;
}

export interface CategoryRevenue {
  category: string;
  revenue: number;
}

export interface TopProduct {
  product_name: string;
  revenue: number;
}

export interface SegmentDistribution {
  customer_segment: string;
  customer_count: number;
}

export interface DashboardResponse {
  kpis: DashboardKPIs;
  revenue_trend: RevenueTrendPoint[];
  revenue_by_region: RegionRevenue[];
  revenue_by_category: CategoryRevenue[];
  top_products: TopProduct[];
  customer_segment_distribution: SegmentDistribution[];
}

export interface ApiError {
  message: string;
}
