"use client";

import { ReactNode } from "react";
import clsx from "clsx";

interface CardProps {
  children: ReactNode;
  className?: string;
}

interface CardHeaderProps {
  children: ReactNode;
  className?: string;
  action?: ReactNode;
}

interface CardBodyProps {
  children: ReactNode;
  className?: string;
}

/**
 * Card component for grouping content.
 * Uses a dark slate background with subtle border.
 */
export function Card({ children, className }: CardProps) {
  return (
    <div
      className={clsx(
        "bg-slate-900 rounded-lg border border-slate-800 shadow-lg",
        className
      )}
    >
      {children}
    </div>
  );
}

/**
 * Card header with optional action slot.
 */
export function CardHeader({ children, className, action }: CardHeaderProps) {
  return (
    <div
      className={clsx(
        "px-6 py-4 border-b border-slate-800 flex items-center justify-between",
        className
      )}
    >
      <div className="font-semibold text-slate-100">{children}</div>
      {action && <div>{action}</div>}
    </div>
  );
}

/**
 * Card body for main content.
 */
export function CardBody({ children, className }: CardBodyProps) {
  return <div className={clsx("px-6 py-4", className)}>{children}</div>;
}
