"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import {
  LayoutDashboard,
  Store,
  Eye,
  Bell,
  Settings,
  BarChart3,
  Activity,
  Search,
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
}

const mainNavItems: NavItem[] = [
  {
    label: "Dashboard",
    href: "/",
    icon: <LayoutDashboard className="w-5 h-5" />,
  },
  {
    label: "Search Ads",
    href: "/search",
    icon: <Search className="w-5 h-5" />,
  },
  {
    label: "Pages / Shops",
    href: "/pages",
    icon: <Store className="w-5 h-5" />,
  },
  {
    label: "Watchlists",
    href: "/watchlists",
    icon: <Eye className="w-5 h-5" />,
  },
  {
    label: "Alerts",
    href: "/alerts",
    icon: <Bell className="w-5 h-5" />,
  },
];

const secondaryNavItems: NavItem[] = [
  {
    label: "Monitoring",
    href: "/monitoring",
    icon: <Activity className="w-5 h-5" />,
  },
  {
    label: "Analytics",
    href: "/analytics",
    icon: <BarChart3 className="w-5 h-5" />,
    badge: "Soon",
  },
  {
    label: "Settings",
    href: "/settings",
    icon: <Settings className="w-5 h-5" />,
    badge: "Soon",
  },
];

function NavLink({ item, isActive }: { item: NavItem; isActive: boolean }) {
  return (
    <Link
      href={item.href}
      className={clsx(
        "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
        isActive
          ? "bg-blue-600/20 text-blue-400"
          : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
      )}
    >
      <span className={clsx(isActive && "text-blue-400")}>{item.icon}</span>
      <span className="flex-1">{item.label}</span>
      {item.badge && (
        <span className="px-1.5 py-0.5 text-[10px] font-semibold uppercase bg-slate-700 text-slate-400 rounded">
          {item.badge}
        </span>
      )}
    </Link>
  );
}

/**
 * Sidebar navigation component.
 * Shows main navigation items and secondary items at the bottom.
 */
export function Sidebar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/";
    }
    return pathname.startsWith(href);
  };

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
      {/* Logo / Brand */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-lg text-slate-100">
            DropInsight
          </span>
        </Link>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="mb-4">
          <p className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
            Main
          </p>
          {mainNavItems.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              isActive={isActive(item.href)}
            />
          ))}
        </div>

        <div className="pt-4 border-t border-slate-800">
          <p className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
            More
          </p>
          {secondaryNavItems.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              isActive={isActive(item.href)}
            />
          ))}
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-800">
        <div className="px-3 py-2 rounded-lg bg-slate-800/50">
          <p className="text-xs font-medium text-slate-400">Dashboard v0.2.0</p>
          <p className="text-xs text-slate-500">Sprint 8.1</p>
        </div>
      </div>
    </aside>
  );
}
