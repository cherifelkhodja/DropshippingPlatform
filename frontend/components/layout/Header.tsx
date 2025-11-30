"use client";

import { useState } from "react";
import { Search, RefreshCw } from "lucide-react";
import { Input } from "@/components/ui";

interface HeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  onSearch?: (query: string) => void;
  showSearch?: boolean;
}

/**
 * Page header component.
 * Shows page title, optional search bar, and action buttons.
 */
export function Header({
  title,
  subtitle,
  actions,
  onSearch,
  showSearch = false,
}: HeaderProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch?.(searchQuery);
  };

  return (
    <header className="h-16 flex items-center justify-between px-6 bg-slate-900/50 backdrop-blur-sm border-b border-slate-800">
      <div className="flex items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100">{title}</h1>
          {subtitle && (
            <p className="text-sm text-slate-400">{subtitle}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-4">
        {showSearch && (
          <form onSubmit={handleSearch} className="w-64">
            <Input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              leftIcon={<Search className="w-4 h-4" />}
            />
          </form>
        )}
        {actions}
      </div>
    </header>
  );
}

/**
 * Breadcrumb navigation component.
 */
export function Breadcrumbs({
  items,
}: {
  items: { label: string; href?: string }[];
}) {
  return (
    <nav className="flex items-center gap-2 text-sm text-slate-400">
      {items.map((item, index) => (
        <span key={index} className="flex items-center gap-2">
          {index > 0 && <span>/</span>}
          {item.href ? (
            <a
              href={item.href}
              className="hover:text-slate-200 transition-colors"
            >
              {item.label}
            </a>
          ) : (
            <span className="text-slate-200">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}

/**
 * Refresh button with loading state.
 */
export function RefreshButton({
  onClick,
  isLoading = false,
}: {
  onClick: () => void;
  isLoading?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={isLoading}
      className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors disabled:opacity-50"
      title="Refresh data"
    >
      <RefreshCw className={`w-5 h-5 ${isLoading ? "animate-spin" : ""}`} />
    </button>
  );
}
