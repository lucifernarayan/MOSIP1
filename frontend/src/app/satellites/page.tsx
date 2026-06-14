"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain, Cpu, ShieldCheck, Gauge, TrendingUp, Target, FileText,
  CheckCircle, Play, RefreshCw, AlertTriangle, ShieldAlert, Activity,
  AlertOctagon, BookOpen, FileCheck, Printer,
} from "lucide-react";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip,
  LineChart, Line,
} from "recharts";
import { agentTimeline, sourceColor } from "@/utils/mosip-data";
import { assessNorad, searchSatellites, type AssessmentPayload, type RegulationSearchResult, type SatelliteSummary } from "@/utils/api";
import { DashboardCard } from "@/components/DashboardCard";

const agentIcons = [Brain, Cpu, ShieldCheck, Gauge, TrendingUp, Target, FileText, CheckCircle];

type AssessmentTab = "risk" | "compliance" | "sustainability" | "forecast" | "recommendations";

function sectionValue(section: Record<string, unknown> | undefined, key: string) {
  return section?.[key];
}

function sectionNumber(section: Record<string, unknown> | undefined, keys: string[]) {
  for (const key of keys) {
    const numeric = Number(sectionValue(section, key));
    if (Number.isFinite(numeric)) return numeric;
  }
  return 0;
}

function sectionString(section: Record<string, unknown> | undefined, keys: string[], fallback = "N/A") {
  for (const key of keys) {
    const value = sectionValue(section, key);
    if (typeof value === "string" && value.trim()) return value;
    if (typeof value === "number") return String(value);
  }
  return fallback;
}

function sectionList(section: Record<string, unknown> | undefined, keys: string[]) {
  for (const key of keys) {
    const value = sectionValue(section, key);
    if (Array.isArray(value)) return value.map(String);
  }
  return [];
}

function satelliteName(sat: SatelliteSummary | null) {
  return sat?.object_name ?? "Satellite Intelligence";
}

function satelliteNorad(sat: SatelliteSummary | null) {
  return sat?.norad_id ?? "";
}

function regulationTitle(reg: RegulationSearchResult) {
  return reg.document || reg.source || "Retrieved regulation";
}

function buildForecastData(assessment: AssessmentPayload | null) {
  const projections = assessment?.forecast?.projections;
  if (projections && typeof projections === "object") {
    const projectionMap = projections as Record<string, Record<string, unknown>>;
    return [
      {
        label: "Now",
        risk: sectionNumber(assessment?.forecast, ["baseline_risk_score"]),
        burden: sectionNumber(assessment?.sustainability_analysis, ["environmental_burden", "orbital_burden_score"]),
        compliance: sectionNumber(assessment?.compliance_analysis, ["compliance_score"]),
      },
      ...(["5yr", "10yr", "25yr"] as const).map((key) => ({
        label: key.replace("yr", "Y"),
        risk: Number(projectionMap[key]?.projected_risk_score) || 0,
        burden: Number(projectionMap[key]?.shell_growth_pct) || 0,
        compliance: sectionNumber(assessment?.compliance_analysis, ["compliance_score"]),
      })),
    ];
  }
  return [];
}

function calculateVelocity(altitudeKm: number, orbitType: string): string {
  if (!altitudeKm || altitudeKm <= 0) {
    return orbitType === "GEO" ? "3.07 km/s" : orbitType === "MEO" ? "3.90 km/s" : "7.50 km/s";
  }
  const GM = 3.986004418e5;
  const R_earth = 6371.0;
  const a = R_earth + altitudeKm;
  const vel = Math.sqrt(GM / a);
  return `${vel.toFixed(2)} km/s`;
}

function getComplianceGrade(score: number): string {
  if (score >= 90) return "A";
  if (score >= 80) return "B";
  if (score >= 70) return "C";
  if (score >= 60) return "D";
  return "F";
}

/* ── Agent Timeline Component ─────────────────────────────────────────────── */
function AgentTimeline({ active }: { active: boolean }) {
  const [completedCount, setCompletedCount] = useState(0);

  useEffect(() => {
    if (!active) {
      const reset = setTimeout(() => setCompletedCount(0), 0);
      return () => clearTimeout(reset);
    }
    let i = 0;
    const interval = setInterval(() => {
      i++;
      setCompletedCount(i);
      if (i >= agentTimeline.length) clearInterval(interval);
    }, 350);
    return () => clearInterval(interval);
  }, [active]);

  return (
    <div
      className="rounded overflow-hidden"
      style={{ background: "var(--c-surface-0)", border: "1px solid var(--c-border)", padding: "16px" }}
    >
      <div className="mb-4">
        <span className="label block mb-0.5">LANGGRAPH PIPELINE</span>
        <h3 className="font-display text-[11px] uppercase tracking-wider" style={{ color: "var(--t-primary)" }}>
          8-AGENT SEQUENTIAL EXECUTION
        </h3>
      </div>
      <div className="flex items-center overflow-x-auto pb-2">
        {agentTimeline.map((agent, i) => {
          const Icon = agentIcons[i];
          const done = completedCount > i;
          const active_node = active && completedCount === i;
          return (
            <div key={agent.name} className="flex items-center shrink-0">
              <motion.div
                className="flex flex-col items-center gap-1"
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: active ? 1 : 0.4, scale: active ? 1 : 0.9 }}
                transition={{ delay: i * 0.35, duration: 0.3 }}
              >
                <div
                  className="relative flex h-9 w-9 items-center justify-center rounded-full transition-all duration-500"
                  style={{
                    border: `1px solid ${done ? "var(--c-nominal)" : active_node ? "var(--c-cyan)" : "rgba(255,255,255,0.1)"}`,
                    background: done ? "rgba(61,232,155,0.07)" : active_node ? "var(--c-cyan-ghost)" : "rgba(255,255,255,0.02)",
                    boxShadow: done ? "0 0 8px rgba(61,232,155,0.18)" : active_node ? "0 0 8px rgba(77,217,245,0.15)" : "none",
                  }}
                >
                  <Icon
                    size={13}
                    style={{
                      color: done ? "var(--c-nominal)" : active_node ? "var(--c-cyan)" : "var(--t-meta)",
                    }}
                  />
                  {done && (
                    <motion.div
                      initial={{ scale: 0, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      className="absolute -top-0.5 -right-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full"
                      style={{ background: "var(--c-nominal)" }}
                    >
                      <CheckCircle size={8} style={{ color: "#040508" }} />
                    </motion.div>
                  )}
                </div>
                <span
                  className="font-data text-[7px] uppercase tracking-wider text-center max-w-[44px] leading-tight"
                  style={{ color: done ? "var(--t-secondary)" : "var(--t-meta)" }}
                >
                  {agent.name}
                </span>
                <span className="font-data text-[6px]" style={{ color: "var(--t-meta)" }}>{agent.latency}</span>
              </motion.div>
              {i < agentTimeline.length - 1 && (
                <div
                  className="mx-1 h-px w-6 shrink-0"
                  style={{ background: done ? "rgba(61,232,155,0.25)" : "var(--c-border)" }}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}



/* ── Sparkline ────────────────────────────────────────────────────────────── */
function Sparkline({ data, color }: { data: number[]; color: string }) {
  const pts = data.map((v, i) => ({ i, v }));
  return (
    <ResponsiveContainer width="100%" height={36}>
      <LineChart data={pts}>
        <Line type="monotone" dataKey="v" stroke={color} strokeWidth={1.5} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

/* ── Main Content ─────────────────────────────────────────────────────────── */
function SatelliteIntelContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const satelliteIdParam = searchParams.get("id");

  const [noradId, setNoradId] = useState(satelliteIdParam || "");
  const [selectedSat, setSelectedSat] = useState<SatelliteSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [assessment, setAssessment] = useState<AssessmentPayload | null>(null);
  const [activeTab, setActiveTab] = useState<AssessmentTab>("risk");
  const [timelineActive, setTimelineActive] = useState(false);

  const runAssessment = async (idToAssess: string) => {
    setLoading(true);
    setError(null);
    setAssessment(null);
    setTimelineActive(false);

    const stages = [
      "Supervisor: Dispatching agents...",
      "Orbital: Analyzing TLE coefficients...",
      "Collision: Evaluating debris density clusters...",
      "Compliance: Querying ESA/IADC RAG vectors...",
      "Sustainability: Computing ecological footprint...",
      "Forecast: Propagating 25-year trajectory...",
      "Mitigation: Synthesizing avoidance strategies...",
      "Documentation: Compiling executive brief...",
    ];

    let stageIdx = 0;
    setLoadingStep(stages[0]);
    const timer = setInterval(() => {
      stageIdx++;
      if (stageIdx < stages.length) setLoadingStep(stages[stageIdx]);
    }, 1100);

    try {
      const result = await assessNorad(idToAssess);
      clearInterval(timer);
      if (result.errors && result.errors.length > 0) throw new Error(result.errors[0]);
      setAssessment(result);
      setSelectedSat({
        norad_id: Number(result.satellite?.norad_id ?? idToAssess),
        object_name: sectionString(result.satellite, ["object_name", "name"], `NORAD ${idToAssess}`),
        object_id: sectionString(result.satellite, ["object_id"], ""),
        altitude_km: sectionNumber(result.orbital_analysis, ["altitude_km", "altitude"]),
        orbit_type: sectionString(result.orbital_analysis, ["orbit_type", "regime", "orbital_regime"], "UNKNOWN"),
        risk_score: sectionNumber(result.collision_analysis, ["risk_score"]),
        risk_level: sectionString(result.collision_analysis, ["risk_level"], "UNKNOWN"),
      });
      setTimelineActive(true);
    } catch (err: unknown) {
      clearInterval(timer);
      setError(err instanceof Error ? err.message : `Assessment failed for NORAD ${idToAssess}.`);
    } finally {
      setLoading(false);
      setLoadingStep("");
    }
  };

  useEffect(() => {
    if (satelliteIdParam) {
      void Promise.resolve().then(() => {
        setNoradId(satelliteIdParam);
        runAssessment(satelliteIdParam);
      });
    }
  }, [satelliteIdParam]);

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = noradId.trim();
    if (!trimmed) return;
    if (/^\d+$/.test(trimmed)) {
      router.push(`/satellites?id=${trimmed}`);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const payload = await searchSatellites(trimmed, 1);
      const match = payload.results[0];
      if (!match) throw new Error(`No satellite found for "${trimmed}".`);
      setSelectedSat(match);
      setNoradId(String(match.norad_id));
      router.push(`/satellites?id=${match.norad_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Satellite search failed.");
    } finally {
      setLoading(false);
    }
  };

  const sat = selectedSat;
  const forecastData = buildForecastData(assessment);
  const riskScore = Number((assessment?.collision_analysis as any)?.overall?.risk_score) || 0;
  const sustainabilityIndex = Number((assessment?.sustainability_analysis as any)?.sustainability_index) || 0;

  // 4 agent metric cards data
  const agentCards = assessment ? [
    {
      eyebrow: "Orbital Agent",
      metric: `${((assessment.orbital_analysis as any)?.altitude_km as number) || 0}`,
      unit: "km",
      detail: `${(assessment.orbital_analysis as any)?.orbit_type || "LEO"} · ${calculateVelocity(Number((assessment.orbital_analysis as any)?.altitude_km), String((assessment.orbital_analysis as any)?.orbit_type))}`,
      spark: [320, 350, 330, 365, 380, 370, 390],
      color: "#00d4ff",
    },
    {
      eyebrow: "Collision Agent",
      metric: `${riskScore}`,
      unit: "%",
      detail: `Risk level: ${(assessment.collision_analysis as any)?.overall?.risk_level || "NOMINAL"}`,
      spark: [20, 35, 28, 45, 40, 55, riskScore],
      color: riskScore >= 75 ? "#ff3366" : riskScore >= 55 ? "#ffb700" : "#00ff9d",
    },
    {
      eyebrow: "Compliance Agent",
      metric: `${getComplianceGrade(Number((assessment.compliance_analysis as any)?.compliance_score || 50))}`,
      unit: "",
      detail: `${(assessment.compliance_analysis as any)?.compliance_level || "UNKNOWN"} (${(assessment.compliance_analysis as any)?.compliance_score || 50}/100)`,
      spark: [90, 85, 88, 82, 86, 80, 84],
      color: "#00d4ff",
    },
    {
      eyebrow: "Sustainability Agent",
      metric: `${sustainabilityIndex}`,
      unit: "/100",
      detail: `Burden: ${(assessment.sustainability_analysis as any)?.environmental_burden || 0}/40`,
      spark: [80, 75, 78, 72, 70, 68, sustainabilityIndex || 70],
      color: "var(--c-nominal)",
    },
  ] : [];



  return (
    <div className="flex flex-col gap-5 p-5 lg:p-7 min-h-full" style={{ background: "var(--c-base)" }}>
      {/* ── Header ────────────────────────────────────────────────────── */}
      <header
        className="flex flex-col justify-between gap-4 pb-4 sm:flex-row sm:items-center"
        style={{ borderBottom: "1px solid var(--c-border)" }}
      >
        <div>
          <span className="label block mb-0.5">MULTI-AGENT SYNTHESIS ENGINE</span>
          <h1 className="font-display text-xl uppercase tracking-[0.1em]" style={{ color: "var(--t-primary)" }}>
            {satelliteName(sat)}
          </h1>
          {sat && (
            <div className="mt-1.5 flex items-center gap-2">
              <span className="font-data text-[9px]" style={{ color: "var(--t-meta)" }}>NORAD {satelliteNorad(sat)}</span>
              <span style={{ color: "var(--c-border-hi)" }}>·</span>
              <span
                className="status-tag"
                style={{
                  color: riskScore >= 75 ? "var(--c-critical)" : riskScore >= 55 ? "var(--c-elevated)" : "var(--c-nominal)",
                  borderColor: riskScore >= 75 ? "rgba(239,67,67,0.25)" : riskScore >= 55 ? "rgba(245,166,35,0.25)" : "rgba(61,232,155,0.22)",
                  background: riskScore >= 75 ? "rgba(239,67,67,0.06)" : riskScore >= 55 ? "rgba(245,166,35,0.06)" : "rgba(61,232,155,0.06)",
                }}
              >
                {riskScore >= 75 ? "CRITICAL" : riskScore >= 55 ? "ELEVATED" : "NOMINAL"}
              </span>
              <span className="font-data text-[9px]" style={{ color: "var(--t-meta)" }}>{sat.object_id || "CATALOGUED"}</span>
            </div>
          )}
        </div>

        {assessment && (
          <form onSubmit={handleSearchSubmit} className="flex gap-2">
            <input
              type="text"
              placeholder="NORAD ID or name..."
              value={noradId}
              onChange={(e) => setNoradId(e.target.value)}
              className="h-9 rounded border px-3 font-data text-[11px] outline-none w-[160px]"
              style={{
                background: "var(--c-surface-1)",
                border: "1px solid var(--c-border-hi)",
                color: "var(--t-primary)",
                caretColor: "var(--c-cyan)",
              }}
            />
            <button
              type="submit"
              disabled={loading}
              className="btn-primary h-9 flex items-center gap-1.5 px-4 font-data text-[9px] uppercase tracking-widest disabled:opacity-40"
            >
              {loading ? <RefreshCw size={11} className="animate-spin" /> : <Play size={11} />}
              ANALYZE
            </button>
          </form>
        )}
      </header>

      {/* ── Loading state ───────────────────────────────────────────── */}
      {loading && (
        <div
          className="p-10 flex flex-col items-center justify-center min-h-[300px] relative overflow-hidden rounded"
          style={{ background: "var(--c-surface-0)", border: "1px solid var(--c-border)" }}
        >
          <div className="relative z-10 flex flex-col items-center gap-5">
            {/* Multi-ring orbital indicator */}
            <div className="relative h-16 w-16">
              <div
                className="absolute inset-0 rounded-full"
                style={{ border: "1px solid rgba(77,217,245,0.15)", animation: "spin 12s linear infinite" }}
              />
              <div
                className="absolute inset-2 rounded-full"
                style={{ border: "1px solid rgba(77,217,245,0.3)", animation: "spin 8s linear infinite reverse" }}
              />
              <div className="absolute inset-0 grid place-items-center">
                <div
                  className="h-2 w-2 rounded-full"
                  style={{ background: "var(--c-cyan)", boxShadow: "0 0 8px var(--c-cyan)" }}
                />
              </div>
            </div>
            <div className="flex flex-col items-center gap-1">
              <p className="font-data text-[9px] uppercase tracking-[0.3em]" style={{ color: "var(--c-cyan)" }}>
                EXECUTING MULTI-AGENT GRAPH
              </p>
              <p className="font-data text-[9px] max-w-xs text-center" style={{ color: "var(--t-meta)" }}>
                {loadingStep}
              </p>
            </div>
            <div className="w-52 h-px" style={{ background: "rgba(255,255,255,0.06)" }}>
              <div
                className="h-full"
                style={{ background: "var(--c-cyan)", animation: "loading 9s ease-in-out forwards" }}
              />
            </div>
          </div>
        </div>
      )}

      {/* ── Error ────────────────────────────────────────────────────── */}
      {error && !loading && (
        <div className="cyber-panel cyber-panel-danger p-5 flex items-center gap-3">
          <AlertOctagon size={20} className="text-[#ff3366] shrink-0" />
          <div>
            <h3 className="font-semibold text-[#ff3366] uppercase tracking-wider text-xs">Assessment Ingestion Fault</h3>
            <p className="text-xs text-slate-400 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* ── Landing State when no satellite assessed yet ── */}
      {!loading && !assessment && (
        <div 
          className="flex-1 flex flex-col items-center justify-center min-h-[520px] rounded relative overflow-hidden border border-white/[0.04] shadow-2xl"
          style={{
            backgroundImage: "url('/collision_evasion.png')",
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        >
          {/* Dark cinematic filter for text readability */}
          <div className="absolute inset-0 z-0 bg-gradient-to-b from-[#080c12]/98 via-[#080c12]/80 to-[#080c12]/98" />
          
          {/* Futuristic grid */}
          <div className="cyber-grid absolute inset-0 opacity-10 z-0 pointer-events-none" />

          {/* Glowing central halo representing planet edge/shine behind content */}
          <div 
            className="absolute rounded-full pointer-events-none z-0 filter blur-[100px]"
            style={{
              width: "480px",
              height: "480px",
              background: "radial-gradient(circle, rgba(77,217,245,0.08) 0%, transparent 70%)",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
            }}
          />

          <div className="relative z-10 max-w-xl w-full px-6 text-center flex flex-col items-center gap-6">
            <div className="flex flex-col gap-2">
              <span className="font-data text-[8px] uppercase tracking-[0.35em] text-[var(--c-cyan)]">
                ORBITAL ASSESSMENT CORRIDOR
              </span>
              <h2 className="font-display text-3xl md:text-4xl uppercase tracking-wider text-white font-bold leading-tight">
                Multi-Agent<br/>Satellite Synthesis
              </h2>
              <p className="text-[11px] text-slate-400 leading-relaxed max-w-md mx-auto mt-1">
                Enter a catalog NORAD ID to dispatch the 8-agent sequential check swarm. The supervisor will compile live collision trajectory warnings, ESA/IADC regulatory compliant evidence, and calculate delta-v collision avoidance thrust briefs.
              </p>
            </div>

            {/* Central console search bar */}
            <form onSubmit={handleSearchSubmit} className="w-full max-w-md flex gap-2">
              <div className="flex-1 flex items-center gap-2 px-3 py-2 rounded border border-white/10 bg-slate-950/70 backdrop-blur-md focus-within:border-[var(--c-cyan)] transition-all">
                <input
                  type="text"
                  placeholder="Enter NORAD ID (e.g. 25544 for ISS)..."
                  value={noradId}
                  onChange={(e) => setNoradId(e.target.value)}
                  className="w-full bg-transparent font-data text-xs outline-none placeholder:text-slate-500"
                  style={{ color: "#fff", caretColor: "var(--c-cyan)" }}
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="btn-primary flex items-center gap-2 px-5 font-data text-xs uppercase tracking-widest disabled:opacity-40"
              >
                {loading ? <RefreshCw size={12} className="animate-spin" /> : <Play size={12} />}
                ANALYZE
              </button>
            </form>

            {/* Suggested Shortcuts */}
            <div className="flex flex-col items-center gap-2 mt-4">
              <span className="font-data text-[7px] uppercase tracking-[0.25em] text-slate-500">
                OR SELECT ACTIVE NORAD TARGET
              </span>
              <div className="flex flex-wrap gap-2 justify-center max-w-md">
                {[
                  { name: "ISS", id: "25544" },
                  { name: "CALSPHERE 1", id: "900" },
                  { name: "LAGEOS", id: "8820" },
                  { name: "STARLINK-1007", id: "44713" },
                ].map((shortcut) => (
                  <button
                    key={shortcut.id}
                    type="button"
                    onClick={() => {
                      setNoradId(shortcut.id);
                      runAssessment(shortcut.id);
                    }}
                    className="px-3 py-1 rounded border border-white/[0.04] bg-white/[0.02] hover:bg-[var(--c-cyan-ghost)] hover:border-[var(--c-cyan)] text-slate-400 hover:text-white font-data text-[9px] uppercase tracking-wider transition-all"
                  >
                    {shortcut.name} · {shortcut.id}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Results ─────────────────────────────────────────────────────────── */}
      {!loading && assessment && (
        <>
          {/* Agent Timeline */}
          <AgentTimeline active={timelineActive} />

          {/* 4 Agent Metric Cards — instrument-panel style */}
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {agentCards.map((card, i) => (
              <motion.div
                key={card.eyebrow}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08, duration: 0.3 }}
                className="p-4 rounded"
                style={{
                  background: "var(--c-surface-0)",
                  border: `1px solid ${card.color}18`,
                }}
              >
                <span className="label block mb-2">{card.eyebrow.toUpperCase()}</span>
                <div className="flex items-baseline gap-1 mb-1">
                  <span className="font-data text-2xl font-bold tabular-nums" style={{ color: card.color }}>
                    {card.metric}
                  </span>
                  <span className="font-data text-[10px]" style={{ color: "var(--t-meta)" }}>{card.unit}</span>
                </div>
                <p className="font-data text-[8px] uppercase tracking-widest mb-2" style={{ color: "var(--t-meta)" }}>
                  {card.detail}
                </p>
                <Sparkline data={card.spark} color={card.color} />
              </motion.div>
            ))}
          </div>

          {/* Tabs + Detail */}
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-5">
            <div className="xl:col-span-8">
              <div className="cyber-panel p-5">
                <nav className="flex flex-wrap gap-2 border-b border-white/[0.05] pb-4 mb-5">
                  {[
                    { id: "risk", label: "Collision Risk", icon: ShieldAlert },
                    { id: "compliance", label: "Compliance", icon: BookOpen },
                    { id: "sustainability", label: "Sustainability", icon: Activity },
                    { id: "forecast", label: "Forecast", icon: TrendingUp },
                    { id: "recommendations", label: "Mitigation", icon: FileCheck },
                  ].map((tab) => {
                    const Icon = tab.icon;
                    const active = activeTab === tab.id;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as AssessmentTab)}
                        className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 font-digital text-[10px] uppercase tracking-wider transition-all ${
                          active
                            ? "border-[#00d4ff]/30 bg-[#00d4ff]/08 text-[#00d4ff]"
                            : "border-white/[0.05] bg-white/[0.02] text-slate-500 hover:border-white/10 hover:text-slate-300"
                        }`}
                      >
                        <Icon size={11} />
                        {tab.label}
                      </button>
                    );
                  })}
                </nav>

                <div className="min-h-[260px]">
                  {/* Risk Tab */}
                  {activeTab === "risk" && (
                    <div className="flex flex-col gap-4">
                      <div className="flex items-center justify-between">
                        <h3 className="text-sm font-semibold uppercase tracking-wider text-white">Debris Collision Assessment</h3>
                        <span className="font-digital text-2xl font-bold" style={{ color: riskScore >= 75 ? "#ff3366" : riskScore >= 55 ? "#ffb700" : "#00ff9d" }}>
                          {riskScore}%
                        </span>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <ul className="flex flex-col gap-2">
                          {((assessment.collision_analysis?.risk_drivers as string[]) || []).map((d, i) => (
                            <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                              <AlertTriangle size={12} className="text-[#ffb700] mt-0.5 shrink-0" />
                              {d}
                            </li>
                          ))}
                        </ul>
                        <div className="bg-white/[0.02] border border-white/[0.05] p-3 rounded-lg font-digital text-xs">
                          <p className="eyebrow mb-2">Space Density Matrix</p>
                          <div className="flex justify-between py-1.5 border-b border-white/[0.05]">
                            <span className="text-slate-400">Debris Density Score</span>
                            <span className="text-white">{(assessment.collision_analysis as any)?.components?.debris_risk?.score as number || 0}/30</span>
                          </div>
                          <div className="flex justify-between py-1.5">
                            <span className="text-slate-400">Objects in Orbit Shell</span>
                            <span className="text-white">{(assessment.collision_analysis as any)?.congestion_context?.objects_in_shell as number || 0}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Compliance Tab */}
                  {activeTab === "compliance" && (
                    <div className="flex flex-col gap-4">
                      <div className="flex items-center justify-between">
                        <h3 className="text-sm font-semibold uppercase tracking-wider text-white">Regulatory Compliance</h3>
                        <span className="font-digital text-2xl font-bold text-[#00d4ff]">
                          {getComplianceGrade(Number(assessment.compliance_analysis?.compliance_score || 50))}
                        </span>
                      </div>
                      <div className="border-l-2 border-[#00d4ff]/20 pl-4 py-1 text-xs text-slate-300 leading-relaxed">
                        {assessment.compliance_analysis?.compliance_summary as string}
                      </div>
                      <div className="flex flex-col gap-1.5">
                        {((assessment.compliance_analysis?.failed_requirements as string[]) || []).length === 0 ? (
                          <div className="flex items-center gap-2 text-xs text-[#00ff9d] bg-[#00ff9d]/05 border border-[#00ff9d]/10 p-2.5 rounded-lg">
                            <ShieldCheck size={13} />
                            Zero safety or deorbit regulatory infractions detected.
                          </div>
                        ) : (
                          ((assessment.compliance_analysis?.failed_requirements as string[]) || []).map((v, i) => (
                            <div key={i} className="flex items-start gap-2 text-xs text-[#ff3366] bg-[#ff3366]/05 border border-[#ff3366]/15 p-2.5 rounded-lg">
                              <ShieldAlert size={13} className="mt-0.5 shrink-0" />
                              {v}
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}

                  {/* Sustainability Tab */}
                  {activeTab === "sustainability" && (
                    <div className="flex flex-col gap-4">
                      <h3 className="text-sm font-semibold uppercase tracking-wider text-white">Ecological Orbital Footprint</h3>
                      <div className="grid grid-cols-3 gap-3 font-digital">
                        {[
                          { label: "Sustainability Index", value: `${assessment.sustainability_analysis?.sustainability_index || 0}/100`, color: "#00ff9d" },
                          { label: "Environmental Burden", value: `${assessment.sustainability_analysis?.environmental_burden || 0}/40`, color: "#00d4ff" },
                          { label: "Orbital Footprint", value: `${assessment.sustainability_analysis?.orbital_footprint_score || 0}/40`, color: "#ffb700" },
                        ].map((m) => (
                          <div key={m.label} className="cyber-panel p-3 text-center">
                            <span className="block text-[8px] uppercase text-slate-500 mb-1">{m.label}</span>
                            <span className="block text-lg font-bold" style={{ color: m.color }}>{m.value}</span>
                          </div>
                        ))}
                      </div>
                      <p className="text-[11px] text-slate-400 leading-relaxed border border-white/[0.04] bg-white/[0.01] p-3 rounded-lg">
                        Local congestion shell of {assessment.sustainability_analysis?.congestion_contribution as number || 0} objects weighed against orbital lifetime and local congestion parameters. Lower index indicates elevated cascade collision potential.
                      </p>
                    </div>
                  )}

                  {/* Forecast Tab */}
                  {activeTab === "forecast" && (
                    <div className="flex flex-col gap-4">
                      <div className="flex items-center justify-between">
                        <h3 className="text-sm font-semibold uppercase tracking-wider text-white">25-Year Risk Propagation</h3>
                        <span className="font-digital text-xs text-slate-400">Decay est: {assessment.forecast?.decay_estimate_years as number || 0}y</span>
                      </div>
                      <div className="h-[180px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={forecastData}>
                            <defs>
                              <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={riskScore >= 75 ? "#ff3366" : "#ffb700"} stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#02040a" stopOpacity={0.1} />
                              </linearGradient>
                            </defs>
                            <XAxis dataKey="label" tick={{ fill: "#475569", fontSize: 9, fontFamily: "monospace" }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: "#475569", fontSize: 9, fontFamily: "monospace" }} axisLine={false} tickLine={false} domain={[0, 100]} />
                            <Tooltip contentStyle={{ backgroundColor: "#080810", borderColor: "rgba(0,212,255,0.15)", color: "#fff", fontSize: "10px", fontFamily: "monospace" }} />
                            <Area type="monotone" dataKey="risk" stroke={riskScore >= 75 ? "#ff3366" : "#ffb700"} strokeWidth={2} fill="url(#riskGrad)" />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}

                  {/* Recommendations Tab */}
                  {activeTab === "recommendations" && (
                    <div className="flex flex-col gap-3">
                      <h3 className="text-sm font-semibold uppercase tracking-wider text-white">Actionable Mitigation Mandates</h3>
                      {(assessment.recommendations || []).map((rec, i: number) => (
                        <div key={i} className="cyber-panel p-4 flex items-start gap-3">
                          <div className={`rounded-lg p-1.5 shrink-0 ${String(rec.priority || "") === "HIGH" ? "bg-[#ff3366]/10 text-[#ff3366]" : "bg-[#00d4ff]/10 text-[#00d4ff]"}`}>
                            <Brain size={14} />
                          </div>
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="text-xs font-semibold text-white uppercase tracking-wider">{String(rec.title || "Recommendation")}</h4>
                              <span className={`font-digital text-[8px] uppercase px-1.5 py-0.5 rounded ${String(rec.priority || "") === "HIGH" ? "bg-[#ff3366]/10 text-[#ff3366]" : "bg-white/[0.04] text-slate-400"}`}>
                                {String(rec.priority || "INFO")}
                              </span>
                            </div>
                            <p className="text-xs text-slate-300">{String(rec.action || "")}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Satellite Profile Card */}
            <div className="xl:col-span-4 flex flex-col gap-4">
              <DashboardCard title="Target Identity" eyebrow="Primary Orbital Properties" isActive>
                <div className="flex flex-col gap-3 font-digital text-xs">
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: "Operator", value: assessment.satellite?.object_id as string || "Catalogued" },
                      { label: "Regime", value: assessment.orbital_analysis?.orbit_type as string || "N/A" },
                      { label: "Altitude", value: `${assessment.orbital_analysis?.altitude_km as number || 0} km`, className: "text-[#00d4ff]" },
                      { label: "Velocity", value: calculateVelocity(Number(assessment.orbital_analysis?.altitude_km), String(assessment.orbital_analysis?.orbit_type)), className: "text-[#00d4ff]" },
                      { label: "Apogee", value: `${assessment.orbital_analysis?.apogee_km as number || 0} km` },
                      { label: "Perigee", value: `${assessment.orbital_analysis?.perigee_km as number || 0} km` },
                      { label: "Inclination", value: `${assessment.orbital_analysis?.inclination_deg as number || 0}°` },
                      { label: "Period", value: `${assessment.orbital_analysis?.period_minutes as number || 0} min` },
                    ].map((f) => (
                      <div key={f.label}>
                        <span className="block text-[8px] uppercase text-slate-500">{f.label}</span>
                        <span className={`block truncate ${f.className || "text-slate-200"}`}>{f.value}</span>
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={() => router.push(`/reports?id=${noradId}`)}
                    className="btn-ghost flex items-center justify-center gap-1.5 rounded-lg py-2 text-[10px] uppercase tracking-wider"
                  >
                    <Printer size={11} /> Generate Report
                  </button>
                </div>
              </DashboardCard>

              {/* RAG Regulations */}
              <div className="cyber-panel p-4">
                <span className="eyebrow block mb-3">RAG — Retrieved Regulations</span>
                <div className="bg-black/50 border border-white/[0.04] rounded-lg p-3 font-digital text-[10px] text-slate-400 space-y-3 max-h-[200px] overflow-y-auto">
                  {(assessment.regulations || []).slice(0, 3).map((reg, i) => (
                    <div key={`${reg.source || "reg"}-${reg.document || i}`}>
                      <div className="flex items-center gap-1.5 mb-1">
                        <span className="text-[8px] uppercase px-1.5 py-0.5 rounded" style={{ background: `${sourceColor(reg.source || "")}15`, color: sourceColor(reg.source || "") }}>{reg.source || "RAG"}</span>
                        <span className="text-white/60 truncate">{regulationTitle(reg)}</span>
                      </div>
                      <p className="text-slate-500 leading-relaxed line-clamp-2">§ {(reg.text || "").slice(0, 140)}...</p>
                    </div>
                  ))}
                  {(!assessment.regulations || assessment.regulations.length === 0) && (
                    <p className="text-slate-500">No regulation evidence returned by the assessment pipeline.</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default function SatelliteIntelligencePage() {
  return (
    <Suspense fallback={
      <div className="grid h-full min-h-screen place-items-center font-digital text-xs uppercase tracking-[0.3em] text-[#00d4ff]/40">
        Loading assessment engine...
      </div>
    }>
      <SatelliteIntelContent />
    </Suspense>
  );
}
