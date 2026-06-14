"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

type DashboardCardProps = {
  title: string;
  eyebrow?: string;
  children: ReactNode;
  glowColor?: string;
  isActive?: boolean;
  className?: string;
  noPad?: boolean;
  danger?: boolean;
};

export function DashboardCard({
  title,
  eyebrow,
  children,
  isActive = false,
  className = "",
  noPad = false,
  danger = false,
}: DashboardCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`overflow-hidden ${className}`}
      style={{
        background: "var(--c-surface-0)",
        border: `1px solid ${danger ? "rgba(239,67,67,0.25)" : isActive ? "rgba(77,217,245,0.2)" : "var(--c-border)"}`,
        borderRadius: "var(--border-r)",
        boxShadow: isActive
          ? "0 0 16px rgba(77,217,245,0.07)"
          : danger
          ? "0 0 14px rgba(239,67,67,0.05)"
          : "none",
      }}
    >
      {/* Card header */}
      <div
        className="flex items-center justify-between px-4 py-2.5"
        style={{ borderBottom: "1px solid var(--c-border)" }}
      >
        <div>
          {eyebrow && (
            <span className="eyebrow block mb-0.5">{eyebrow}</span>
          )}
          <h3
            className="font-display text-[11px] uppercase tracking-[0.12em]"
            style={{ color: "var(--t-primary)" }}
          >
            {title}
          </h3>
        </div>
        {isActive && (
          <div className="flex items-center gap-1.5">
            <span className="pulse-dot" style={{ background: "var(--c-cyan)" }} />
          </div>
        )}
        {danger && (
          <div className="flex items-center gap-1.5">
            <span className="pulse-dot" style={{ background: "var(--c-critical)" }} />
          </div>
        )}
      </div>
      <div className={noPad ? "" : "p-4"}>{children}</div>
    </motion.div>
  );
}
