"use client";

import { useState } from "react";
import {
  Coins,
  ShieldCheck,
  Zap,
  ChevronRight,
  TrendingUp,
  FileCheck,
  Activity,
  Layers,
  ArrowUpRight,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

/* ── Custom Data for Micro-Charts ────────────────────────────────────────── */

// Data for Launchers: Regulatory approval timeline comparison (weeks vs hours)
const launchersData = [
  { stage: "Ingestion", manual: 4, mosip: 0.1 },
  { stage: "Trajectory", manual: 8, mosip: 0.2 },
  { stage: "Risk Audit", manual: 12, mosip: 0.5 },
  { stage: "Filing", manual: 20, mosip: 0.8 },
];

// Data for Operators: Propellant waste reduction (kg per satellite/year)
const operatorsData = [
  { fleetSize: "1 Sat", traditional: 45, mosip: 38 },
  { fleetSize: "10 Sat", traditional: 450, mosip: 340 },
  { fleetSize: "50 Sat", traditional: 2250, mosip: 1600 },
  { fleetSize: "100 Sat", traditional: 4500, mosip: 3100 },
];

// Data for Insurers: Dynamic Premium adjustments based on Compliance Rating
const insurersData = [
  { grade: "Grade F", premiumIndex: 100 },
  { grade: "Grade D", premiumIndex: 85 },
  { grade: "Grade C", premiumIndex: 68 },
  { grade: "Grade B", premiumIndex: 45 },
  { grade: "Grade A", premiumIndex: 20 },
];

export default function BusinessModelPage() {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const divisions = [
    {
      index: 0,
      title: "Pre-Launch Trajectory Auditing",
      target: "LAUNCH STARTUPS & LOGISTICS",
      image: "/debris_orbit.png",
      price: "$10,000 / launch",
      metric: "90% Faster Regulatory Clearance",
      accent: "var(--c-cyan)",
      accentGhost: "rgba(77,217,245,0.06)",
      icon: Layers,
      description:
        "Rocket launchers must prove to space authorities that planned orbital insertions won't impact active satellites or cross debris fields. MOSIP provides instant compliance reports checking thousands of flight trajectories.",
      bullets: [
        "Automatic FAA, FCC & IADC compliance generation",
        "Orbital shell overlap simulation models",
        "Pre-launch path optimization algorithms",
      ],
      chart: (
        <ResponsiveContainer width="100%" height={100}>
          <AreaChart data={launchersData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
            <XAxis dataKey="stage" stroke="rgba(255,255,255,0.3)" fontSize={8} />
            <YAxis stroke="rgba(255,255,255,0.3)" fontSize={8} label={{ value: "Weeks", angle: -90, position: "insideLeft", fill: "rgba(255,255,255,0.3)", fontSize: 8 }} />
            <Tooltip
              contentStyle={{ background: "#0b0f17", border: "1px solid var(--c-border)", fontSize: "9px" }}
              labelStyle={{ color: "#fff" }}
            />
            <Area type="monotone" dataKey="manual" name="Manual Audit" stroke="#ef4343" fill="rgba(239,67,67,0.1)" strokeWidth={1.5} />
            <Area type="monotone" dataKey="mosip" name="MOSIP Platform" stroke="#4dd9f5" fill="rgba(77,217,245,0.15)" strokeWidth={1.5} />
          </AreaChart>
        </ResponsiveContainer>
      ),
    },
    {
      index: 1,
      title: "Autonomous Fleet Evasion SaaS",
      target: "SATELLITE FLEET OPERATORS",
      image: "/collision_evasion.png",
      price: "$500 / satellite / mo",
      metric: "15% Fuel Lifetime Extension",
      accent: "var(--c-elevated)",
      accentGhost: "rgba(245,166,35,0.06)",
      icon: Zap,
      description:
        "Fleet operators face constant collision warnings. Manually checking warnings and planning thruster burns is slow. MOSIP automatically calculates thruster de-confliction paths.",
      bullets: [
        "Autonomous trajectory de-confliction scripts",
        "Real-time SGP4 conjunction monitoring",
        "Active fuel budget optimizations",
      ],
      chart: (
        <ResponsiveContainer width="100%" height={100}>
          <LineChart data={operatorsData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
            <XAxis dataKey="fleetSize" stroke="rgba(255,255,255,0.3)" fontSize={8} />
            <YAxis stroke="rgba(255,255,255,0.3)" fontSize={8} label={{ value: "Fuel (kg)", angle: -90, position: "insideLeft", fill: "rgba(255,255,255,0.3)", fontSize: 8 }} />
            <Tooltip
              contentStyle={{ background: "#0b0f17", border: "1px solid var(--c-border)", fontSize: "9px" }}
              labelStyle={{ color: "#fff" }}
            />
            <Line type="monotone" dataKey="traditional" name="Traditional Evasion" stroke="#7a8ba0" strokeWidth={1.5} activeDot={{ r: 4 }} />
            <Line type="monotone" dataKey="mosip" name="MOSIP Evasion" stroke="#f5a623" strokeWidth={1.5} activeDot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      ),
    },
    {
      index: 2,
      title: "Compliance & Risk Oracles",
      target: "SPACE INSURANCE UNDERWRITERS",
      image: "/orbital_compliance.png",
      price: "$2,500 / month",
      metric: "Dynamic Volatility Underwriting",
      accent: "var(--c-nominal)",
      accentGhost: "rgba(61,232,155,0.06)",
      icon: ShieldCheck,
      description:
        "Underwriters lack real-time telemetry analytics. MOSIP operates as an independent risk oracle, publishing dynamic rating indexes for compliance against space safety policies.",
      bullets: [
        "Dynamic A–F sustainability policy ratings",
        "Real-time spatial burden indexes",
        "Behavior-based dynamically priced premiums",
      ],
      chart: (
        <ResponsiveContainer width="100%" height={100}>
          <BarChart data={insurersData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
            <XAxis dataKey="grade" stroke="rgba(255,255,255,0.3)" fontSize={8} />
            <YAxis stroke="rgba(255,255,255,0.3)" fontSize={8} label={{ value: "Premium %", angle: -90, position: "insideLeft", fill: "rgba(255,255,255,0.3)", fontSize: 8 }} />
            <Tooltip
              contentStyle={{ background: "#0b0f17", border: "1px solid var(--c-border)", fontSize: "9px" }}
              labelStyle={{ color: "#fff" }}
            />
            <Bar dataKey="premiumIndex" name="Premium Index" fill="var(--c-nominal)" radius={[2, 2, 0, 0]} maxBarSize={15} />
          </BarChart>
        </ResponsiveContainer>
      ),
    },
  ];

  return (
    <div className="relative w-full overflow-y-auto main-scroll-container" style={{ background: "#000", height: "calc(100vh - var(--topbar-h))" }}>

      {/* ── Background Image Layer (Cross-Fade Transitions) ── */}
      {divisions.map((div) => {
        const isActive = hoveredIndex === div.index;
        return (
          <div
            key={div.index}
            className="absolute inset-0 z-0 transition-opacity duration-700 pointer-events-none"
            style={{
              backgroundImage: `url('${div.image}')`,
              backgroundSize: "cover",
              backgroundPosition: "center",
              opacity: isActive ? 0.22 : 0,
            }}
          />
        );
      })}

      {/* Static dim background overlay if no card is hovered */}
      <div
        className="absolute inset-0 z-0 transition-opacity duration-700 pointer-events-none"
        style={{
          background: "linear-gradient(to bottom, rgba(8,12,18,0.95), rgba(8,12,18,0.98))",
          opacity: hoveredIndex === null ? 1 : 0.82,
        }}
      />

      {/* Holographic scanner scanline effects */}
      <div className="cyber-grid absolute inset-0 opacity-10 pointer-events-none z-10" />

      {/* Main Content Layout */}
      <div className="relative z-20 max-w-6xl mx-auto px-6 py-8 flex flex-col h-full min-h-[calc(100vh-var(--topbar-h)-4rem)] justify-center">
        
        {/* Header Block */}
        <div className="mb-8 max-w-2xl shrink-0">
          <span className="font-data text-[8px] uppercase tracking-[0.35em] text-[var(--c-cyan)]">
            COMMERCIALIZATION FRAMEWORK // OPERATIONAL VALUE
          </span>
          <h1 className="font-display text-3xl md:text-4xl uppercase tracking-wider text-white mt-1 leading-tight">
            MOSIP Commercialization Engine
          </h1>
          <p className="text-[11px] md:text-xs text-slate-400 mt-2 leading-relaxed">
            Converting space traffic telemetry and safety audits into actionable business margins. MOSIP structures automated, low-latency intelligence pipelines across launchers, operational constellations, and underwriters.
          </p>
        </div>

        {/* 3-Column Division Layout */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch mb-4 flex-1">
          {divisions.map((div) => {
            const isHovered = hoveredIndex === div.index;
            const Icon = div.icon;

            return (
              <div
                key={div.index}
                onMouseEnter={() => setHoveredIndex(div.index)}
                onMouseLeave={() => setHoveredIndex(null)}
                className="rounded-sm flex flex-col justify-between transition-all duration-300 p-5 backdrop-blur-md"
                style={{
                  background: isHovered ? "rgba(11,15,23,0.85)" : "rgba(8,12,18,0.65)",
                  border: isHovered ? `1px solid ${div.accent}` : "1px solid var(--c-border)",
                  boxShadow: isHovered ? `0 0 20px ${div.accent}12` : "none",
                }}
              >
                {/* Upper Details */}
                <div>
                  {/* Category Target */}
                  <div className="flex justify-between items-center mb-3">
                    <span className="font-data text-[7.5px] uppercase tracking-[0.2em] text-slate-500">
                      {div.target}
                    </span>
                    <Icon size={12} style={{ color: isHovered ? div.accent : "rgba(255,255,255,0.3)" }} />
                  </div>

                  {/* Division Title */}
                  <h3 className="font-display text-[16px] uppercase tracking-wide text-white leading-tight mb-2">
                    {div.title}
                  </h3>

                  {/* Segment Details */}
                  <p className="text-[10.5px] leading-relaxed text-slate-400 mb-4">
                    {div.description}
                  </p>

                  {/* Bullet Highlights */}
                  <ul className="flex flex-col gap-1.5 mb-5 border-t border-white/[0.04] pt-4">
                    {div.bullets.map((bullet, idx) => (
                      <li key={idx} className="flex items-start gap-1.5 text-[9.5px] text-slate-300">
                        <ChevronRight size={10} className="shrink-0 mt-0.5" style={{ color: div.accent }} />
                        <span>{bullet}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Lower Metrics & Chart */}
                <div className="mt-4">
                  {/* Micro-Chart Visualization */}
                  <div className="mb-4 p-2 rounded bg-black/30 border border-white/[0.03]">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-data text-[7px] uppercase text-slate-500">METRICS PREVIEW</span>
                      <Activity size={8} style={{ color: div.accent }} />
                    </div>
                    {div.chart}
                  </div>

                  {/* Bottom Stats */}
                  <div className="flex items-end justify-between border-t border-white/[0.04] pt-3">
                    <div className="flex flex-col">
                      <span className="font-data text-[7px] uppercase text-slate-500">PRICING MODEL</span>
                      <span className="font-data text-xs font-bold text-white tracking-wide">{div.price}</span>
                    </div>
                    <div className="flex flex-col text-right">
                      <span className="font-data text-[7px] uppercase text-slate-500">IMPACT TARGET</span>
                      <span className="font-data text-[9.5px] font-semibold" style={{ color: div.accent }}>{div.metric}</span>
                    </div>
                  </div>
                </div>

              </div>
            );
          })}
        </div>

        {/* Global Footer CTA */}
        <div className="flex items-center justify-between border-t border-white/[0.04] pt-4 mt-2 shrink-0">
          <div className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-data text-[8px] uppercase tracking-wider text-slate-500">
              ORBITAL INCENTIVES IN OPERATION
            </span>
          </div>
          <button
            onClick={() => window.open("mailto:ops@mosip.space?subject=Demo Inquiry")}
            className="flex items-center gap-1.5 hover:bg-white hover:text-black border border-white/20 text-white font-data text-[9px] px-4 py-2 uppercase tracking-widest rounded-sm transition-all"
          >
            Request API Sandbox access
            <ArrowUpRight size={10} />
          </button>
        </div>

      </div>

    </div>
  );
}
