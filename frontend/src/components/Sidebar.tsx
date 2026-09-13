import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, TrendingUp, Users, Package, Map, UserCog,
  LineChart, AlertTriangle, Layers, ShieldCheck, FileText, Settings as SettingsIcon,
} from 'lucide-react';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/sales', label: 'Sales', icon: TrendingUp },
  { to: '/customers', label: 'Customers', icon: Users },
  { to: '/products', label: 'Products', icon: Package },
  { to: '/regions', label: 'Regions', icon: Map },
  { to: '/employees', label: 'Employees', icon: UserCog },
  { to: '/forecast', label: 'Forecast', icon: LineChart },
  { to: '/churn', label: 'Churn Analysis', icon: AlertTriangle },
  { to: '/rfm', label: 'RFM Segmentation', icon: Layers },
  { to: '/data-quality', label: 'Data Quality', icon: ShieldCheck },
  { to: '/reports', label: 'Reports', icon: FileText },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
];

export function Sidebar() {
  return (
    <aside className="w-60 shrink-0 bg-[var(--color-nav-bg)] text-[var(--color-nav-ink)] flex flex-col h-screen sticky top-0">
      <div className="px-5 py-5 border-b border-[var(--color-nav-border)]">
        <div className="text-white font-semibold text-[15px] leading-tight">Enterprise Analytics Hub</div>
        <div className="text-[11px] text-[var(--color-nav-ink)] mt-0.5">Sales &amp; Revenue Platform</div>
      </div>
      <nav className="flex-1 overflow-y-auto py-3">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 mx-2 px-3 py-2 rounded-md text-[13px] font-medium transition-colors ${
                isActive
                  ? 'bg-white/10 text-[var(--color-nav-ink-active)]'
                  : 'hover:bg-white/5 hover:text-[var(--color-nav-ink-active)]'
              }`
            }
          >
            <Icon size={16} strokeWidth={2} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="px-5 py-4 border-t border-[var(--color-nav-border)] text-[11px] text-[var(--color-nav-ink)]">
        v1.0.0 &middot; Live data
      </div>
    </aside>
  );
}
