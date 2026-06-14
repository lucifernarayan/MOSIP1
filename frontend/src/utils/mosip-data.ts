import {
  Activity,
  Binary,
  BookOpen,
  BrainCircuit,
  FileText,
  Gauge,
  Globe2,
  Network,
  Orbit,
  Radar,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

/* ── Severity levels ──────────────────────────────────────────────────────── */
export type Severity = "nominal" | "watch" | "elevated" | "critical";

/* ── Satellite type ───────────────────────────────────────────────────────── */
export type SatelliteTrack = {
  id: number;
  name: string;
  orbit: "LEO" | "MEO" | "GEO" | "HEO";
  lat: number;
  lng: number;
  alt: number;
  velocity: string;
  risk: number;
  compliance: string;
  sustainability: number;
  forecast: Severity;
  operator: string;
};

/* ── Agent step ───────────────────────────────────────────────────────────── */
export type AgentStep = {
  name: string;
  status: "complete" | "running" | "queued";
  latency: string;
  detail: string;
};

/* ── Metric point ─────────────────────────────────────────────────────────── */
export type NavItem = {
  href: string;
  label: string;
  eyebrow: string;
  icon: LucideIcon;
};

export const navItems: NavItem[] = [
  { href: "/", label: "Mission Control", eyebrow: "Live orbit map", icon: Globe2 },
  { href: "/satellites", label: "Satellite Intel", eyebrow: "NORAD assessment", icon: Radar },
  { href: "/simulator", label: "Simulator", eyebrow: "Pre-launch what-if", icon: Gauge },
  { href: "/regulations", label: "Regulations", eyebrow: "Semantic retrieval", icon: BookOpen },
  { href: "/reports", label: "Reports", eyebrow: "Executive output", icon: FileText },
  { href: "/architecture", label: "Architecture", eyebrow: "Agent graph", icon: Network },
];

/* ── Agent timeline ───────────────────────────────────────────────────────── */
export const agentTimeline: AgentStep[] = [
  { name: "Supervisor", status: "complete", latency: "00.18s", detail: "Assessment graph initialized" },
  { name: "Orbital", status: "complete", latency: "00.42s", detail: "Regime, apogee, perigee resolved" },
  { name: "Collision", status: "complete", latency: "00.71s", detail: "Debris density vectors scored" },
  { name: "Compliance", status: "complete", latency: "02.14s", detail: "ESA/IADC clauses retrieved via RAG" },
  { name: "Sustainability", status: "complete", latency: "01.31s", detail: "Orbital burden model computed" },
  { name: "Forecast", status: "complete", latency: "01.87s", detail: "5/10/25 year propagation complete" },
  { name: "Mitigation", status: "complete", latency: "01.56s", detail: "Action synthesis with priorities" },
  { name: "Documentation", status: "complete", latency: "00.94s", detail: "Executive report compiled" },
];

/* ── Architecture nodes ───────────────────────────────────────────────────── */
export const architectureNodes = [
  { title: "Satellite Data", subtitle: "CelesTrak + UCS + PostgreSQL", icon: Orbit },
  { title: "Regulatory Corpus", subtitle: "ESA, NASA, IADC PDF chunks", icon: BookOpen },
  { title: "Unified Intelligence", subtitle: "Feature fusion + RAG context", icon: Binary },
  { title: "LangGraph Agents", subtitle: "8-node orbital reasoning chain", icon: BrainCircuit },
  { title: "Executive Synthesis", subtitle: "Mitigations, evidence, reports", icon: Sparkles },
];

/* ── Color utilities ──────────────────────────────────────────────────────── */
export function severityColor(severity: Severity): string {
  if (severity === "critical") return "text-[#ff3366]";
  if (severity === "elevated") return "text-[#ffb700]";
  if (severity === "watch") return "text-[#00d4ff]";
  return "text-[#00ff9d]";
}

export function riskTone(score: number): string {
  if (score >= 75) return "text-[#ff3366]";
  if (score >= 55) return "text-[#ffb700]";
  return "text-[#00ff9d]";
}

export function riskBg(score: number): string {
  if (score >= 75) return "bg-[#ff3366]";
  if (score >= 55) return "bg-[#ffb700]";
  return "bg-[#00ff9d]";
}

export function riskLabel(score: number): string {
  if (score >= 75) return "CRITICAL";
  if (score >= 55) return "ELEVATED";
  if (score >= 35) return "WATCH";
  return "NOMINAL";
}

export function riskGradient(score: number): string {
  if (score >= 75) return "linear-gradient(90deg, #ff3366, #ff6b6b)";
  if (score >= 55) return "linear-gradient(90deg, #ffb700, #ff8c00)";
  if (score >= 35) return "linear-gradient(90deg, #00d4ff, #0099cc)";
  return "linear-gradient(90deg, #00ff9d, #00cc7a)";
}

export function sourceColor(source: string): string {
  if (source === "ESA") return "#00d4ff";
  if (source === "IADC") return "#ffb700";
  if (source === "NASA") return "#ff3366";
  return "#00ff9d";
}
