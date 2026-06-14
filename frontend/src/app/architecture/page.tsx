"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Database, GitMerge, Brain, Cpu, ShieldCheck, Gauge,
  TrendingUp, Target, FileText, Network, X, Zap, BookOpen,
} from "lucide-react";

type ArchNode = {
  id: string;
  title: string;
  subtitle: string;
  icon: any;
  tech: string;
  desc: string;
  color: string;
  column: 0 | 1 | 2 | 3;
};

const nodes: ArchNode[] = [
  {
    id: "postgres", title: "PostgreSQL DB", subtitle: "Active TLE Catalog",
    icon: Database, tech: "PostgreSQL 15 + SQLAlchemy ORM",
    desc: "Stores 19,000+ satellite records with names, countries, operators, and raw TLE parameters ingested from CelesTrak. Exposes query interfaces for orbit type filtering, pagination, risk scoring, and full profile retrieval.",
    color: "#00d4ff", column: 0,
  },
  {
    id: "qdrant", title: "Qdrant Vector Store", subtitle: "Regulatory RAG Knowledge Base",
    icon: Database, tech: "Qdrant DB + BAAI/bge-small-en-v1.5",
    desc: "Holds vector embeddings of space debris regulations (ESA, IADC, NASA). PDF documents are chunked into 120-character segments and encoded with a sentence-transformer model for semantic similarity retrieval.",
    color: "#7c3aed", column: 0,
  },
  {
    id: "fusion", title: "Unified Intelligence", subtitle: "Feature Fusion Layer",
    icon: GitMerge, tech: "satellite_intelligence.py — Feature Combiner",
    desc: "Bridges PostgreSQL orbital state data with regulatory context from Qdrant. Builds a comprehensive MOSIPState containing satellite parameters, computed risk scores, and top-K applicable regulatory clauses for the agent graph.",
    color: "#00ff9d", column: 1,
  },
  {
    id: "supervisor", title: "Supervisor Agent", subtitle: "LangGraph Orchestrator",
    icon: Brain, tech: "LangGraph StateGraph + ChatGoogleGenerativeAI",
    desc: "Root node of the 8-agent LangGraph reasoning chain. Decomposes orbital assessment tasks, routes execution to specialized tool agents sequentially, maintains global MOSIPState between steps, and synthesizes the final intelligence summary.",
    color: "#ff3366", column: 2,
  },
  {
    id: "orbital", title: "Orbital Agent", subtitle: "Trajectory & Kinematics",
    icon: Cpu, tech: "SGP4 propagation + Python orbital mechanics",
    desc: "Derives apogee, perigee, inclination, mean motion, orbital period, and velocity from raw TLE coefficients. Classifies the orbital regime (VLEO/LEO/MEO/GEO/HEO).",
    color: "#00d4ff", column: 3,
  },
  {
    id: "collision", title: "Collision Agent", subtitle: "Debris Shell Matrix",
    icon: Zap, tech: "Local density lookup models",
    desc: "Cross-references satellite's altitude band against historical debris fragment distributions, spatial population counts, and conjunction frequency estimations to derive a composite collision risk score.",
    color: "#ffb700", column: 3,
  },
  {
    id: "compliance", title: "Compliance Agent", subtitle: "RAG + LLM Policy Audit",
    icon: ShieldCheck, tech: "Qdrant RAG + LLM chain-of-thought",
    desc: "Retrieves the most relevant regulatory clauses from Qdrant, then passes them alongside orbital parameters to an LLM for compliance grading (A–F) and violation identification.",
    color: "#00d4ff", column: 3,
  },
  {
    id: "sustainability", title: "Sustainability Agent", subtitle: "Ecological Footprint",
    icon: Gauge, tech: "Cross-sectional burden & congestion formulas",
    desc: "Calculates the satellite's orbital space footprint using cross-sectional area, operational lifetime, and local debris shell population. Generates a 0–100 sustainability index.",
    color: "#00ff9d", column: 3,
  },
  {
    id: "forecast", title: "Forecast Agent", subtitle: "25-Year Trajectory Model",
    icon: TrendingUp, tech: "Passive propagation + risk growth models",
    desc: "Propagates orbital mechanics and risk escalation over 5, 10, and 25-year horizons using atmospheric drag models, debris population growth rates, and conjunction frequency projections.",
    color: "#ffb700", column: 3,
  },
  {
    id: "mitigation", title: "Mitigation Agent", subtitle: "Avoidance Directive Synthesizer",
    icon: Target, tech: "Priority-ordered action synthesis",
    desc: "Synthesizes prioritized avoidance maneuvers, deorbit recommendations, and passivation protocols from the upstream agent analyses. Generates actionable directives with delta-V budgets and urgency ratings.",
    color: "#ff3366", column: 3,
  },
  {
    id: "documentation", title: "Documentation Agent", subtitle: "Executive Brief Compiler",
    icon: FileText, tech: "Structured report generator",
    desc: "Compiles the complete multi-agent intelligence pipeline output into a formatted classified brief document with regulatory citations, risk tables, and mission-specific recommendations.",
    color: "#00d4ff", column: 3,
  },
];

const columnDefs = [
  { label: "Data Sources", icon: Database, color: "#00d4ff" },
  { label: "Fusion Layer", icon: GitMerge, color: "#00ff9d" },
  { label: "Supervisor", icon: Brain, color: "#ff3366" },
  { label: "Tool Agents", icon: Cpu, color: "#00d4ff" },
];

/* ── Flowing SVG Connector ──────────────────────────────────────────────────── */
function FlowConnector({ color = "#00d4ff" }: { color?: string }) {
  return (
    <div className="relative flex items-center self-stretch" style={{ width: 52 }}>
      <svg width="52" height="40" viewBox="0 0 52 40" className="absolute left-0 top-1/2 -translate-y-1/2">
        <line x1="0" y1="20" x2="52" y2="20" stroke={`${color}25`} strokeWidth="1" />
        <line
          x1="0" y1="20" x2="52" y2="20"
          stroke={color}
          strokeWidth="1.5"
          strokeDasharray="6 10"
          className="flow-path"
        />
        <polygon points="48,16 52,20 48,24" fill={color} opacity="0.5" />
      </svg>
    </div>
  );
}

/* ── Node Card ─────────────────────────────────────────────────────────────── */
function NodeCard({ node, onHover, hovered }: { node: ArchNode; onHover: (id: string | null) => void; hovered: boolean }) {
  const Icon = node.icon;
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      onMouseEnter={() => onHover(node.id)}
      onMouseLeave={() => onHover(null)}
      className="cyber-panel cursor-pointer p-3.5 transition-all duration-200"
      style={{
        borderColor: hovered ? `${node.color}35` : "rgba(0,212,255,0.08)",
        boxShadow: hovered ? `0 0 20px ${node.color}18` : "none",
        background: hovered ? `${node.color}06` : "rgba(255,255,255,0.025)",
      }}
    >
      <div className="flex items-center gap-2.5">
        <div
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
          style={{ background: `${node.color}12`, border: `1px solid ${node.color}25` }}
        >
          <Icon size={14} style={{ color: node.color }} />
        </div>
        <div className="min-w-0">
          <span className="block text-xs font-semibold text-white truncate">{node.title}</span>
          <span className="block font-digital text-[8px] text-slate-500 truncate">{node.subtitle}</span>
        </div>
      </div>
    </motion.div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════ */
export default function ArchitecturePage() {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const hoveredNode = nodes.find((n) => n.id === hoveredId) || null;

  const cols = [0, 1, 2, 3].map((c) => nodes.filter((n) => n.column === c));

  return (
    <div className="min-h-[calc(100vh-var(--topbar-h))] cyber-grid p-5 lg:p-7">
      <div className="mb-6">
        <span className="eyebrow block mb-1">LangGraph Agent Pipeline</span>
        <h1 className="text-2xl font-bold uppercase tracking-wider text-white">System Architecture</h1>
        <p className="text-sm text-slate-500 mt-1">Hover any node to inspect the tech stack and agent description</p>
      </div>

      <div className="flex gap-0 overflow-x-auto pb-4">
        {cols.map((colNodes, colIdx) => {
          const colDef = columnDefs[colIdx];
          const ColIcon = colDef.icon;
          return (
            <div key={colIdx} className="flex items-start">
              {/* Column */}
              <div className="flex flex-col gap-3 min-w-[200px] max-w-[210px]">
                {/* Column header */}
                <div className="flex items-center gap-2 px-1 mb-1">
                  <ColIcon size={12} style={{ color: colDef.color }} />
                  <span className="eyebrow" style={{ color: `${colDef.color}80` }}>{colDef.label}</span>
                </div>

                {/* Nodes */}
                {colNodes.map((node) => (
                  <NodeCard
                    key={node.id}
                    node={node}
                    onHover={setHoveredId}
                    hovered={hoveredId === node.id}
                  />
                ))}
              </div>

              {/* Connector between columns */}
              {colIdx < 3 && (
                <div className="flex flex-col items-center justify-center self-stretch pt-8">
                  <FlowConnector color={columnDefs[colIdx + 1].color} />
                </div>
              )}
            </div>
          );
        })}

        {/* ── Inspector Panel ────────────────────────────────────────────── */}
        <AnimatePresence>
          {hoveredNode && (
            <motion.div
              key={hoveredNode.id}
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 40 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
              className="ml-4 w-[240px] shrink-0"
            >
              <div
                className="cyber-panel p-5 h-full"
                style={{
                  borderColor: `${hoveredNode.color}25`,
                  boxShadow: `0 0 24px ${hoveredNode.color}10`,
                }}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-xl"
                    style={{ background: `${hoveredNode.color}12`, border: `1px solid ${hoveredNode.color}25` }}
                  >
                    {(() => { const Icon = hoveredNode.icon; return <Icon size={18} style={{ color: hoveredNode.color }} />; })()}
                  </div>
                  <button onClick={() => setHoveredId(null)} className="text-slate-600 hover:text-slate-400 transition-colors">
                    <X size={14} />
                  </button>
                </div>

                <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-0.5">{hoveredNode.title}</h3>
                <p className="font-digital text-[8px] uppercase tracking-wider mb-4" style={{ color: `${hoveredNode.color}70` }}>
                  {hoveredNode.subtitle}
                </p>

                {/* Tech Badge */}
                <div className="mb-4">
                  <span className="eyebrow block mb-1.5">Technology</span>
                  <div
                    className="rounded-lg px-3 py-2 font-digital text-[9px] text-slate-300"
                    style={{ background: `${hoveredNode.color}08`, border: `1px solid ${hoveredNode.color}18` }}
                  >
                    {hoveredNode.tech}
                  </div>
                </div>

                {/* Description */}
                <div>
                  <span className="eyebrow block mb-1.5">Description</span>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{hoveredNode.desc}</p>
                </div>

                {/* Active indicator */}
                <div className="mt-4 flex items-center gap-1.5">
                  <span className="pulse-dot" style={{ background: hoveredNode.color, width: 4, height: 4 }} />
                  <span className="font-digital text-[8px] uppercase tracking-wider" style={{ color: `${hoveredNode.color}60` }}>
                    Agent active
                  </span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Pipeline stats row */}
      <div className="mt-6 grid grid-cols-4 gap-4">
        {[
          { label: "Total Agents", value: "8", icon: Cpu, color: "#00d4ff" },
          { label: "Data Sources", value: "2", icon: Database, color: "#7c3aed" },
          { label: "Pipeline Steps", value: "Sequential", icon: Network, color: "#00ff9d" },
          { label: "RAG Knowledge Base", value: "10 Regs", icon: BookOpen, color: "#ffb700" },
        ].map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="cyber-panel p-4 flex items-center gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg" style={{ background: `${stat.color}10`, border: `1px solid ${stat.color}20` }}>
                <Icon size={15} style={{ color: stat.color }} />
              </div>
              <div>
                <span className="eyebrow block mb-0.5">{stat.label}</span>
                <span className="font-digital text-sm font-bold text-white">{stat.value}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
