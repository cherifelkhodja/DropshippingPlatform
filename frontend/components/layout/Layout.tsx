"use client";

import { ReactNode } from "react";
import { Sidebar } from "./Sidebar";

interface LayoutProps {
  children: ReactNode;
}

/**
 * Main layout component with sidebar.
 * Wraps the entire application content.
 */
export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-slate-950">
      <Sidebar />
      <main className="pl-64">
        <div className="min-h-screen">{children}</div>
      </main>
    </div>
  );
}

/**
 * Page wrapper component.
 * Provides consistent padding and max-width for page content.
 */
export function PageContent({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`p-6 ${className || ""}`}>
      <div className="max-w-7xl mx-auto">{children}</div>
    </div>
  );
}
