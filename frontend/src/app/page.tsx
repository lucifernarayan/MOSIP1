"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Zap, AlertTriangle, Cpu, TrendingUp, Radio, Shield, ListCollapse } from "lucide-react";
import { riskGradient } from "@/utils/mosip-data";
import type { SatelliteTrack } from "@/utils/mosip-data";
import { GlobeWrapper } from "@/components/GlobeWrapper";
import { getMetricsSummary, listSatellites, searchSatellites, type MetricsSummaryPayload, type SatelliteSummary } from "@/utils/api";

/* ── Count-up Hook ─────────────────────────────────────────────────────────── */
function useCountUp(target: number, duration = 2000, deps: unknown[] = []) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    let start: number | null = null;
    let raf: number;
    const step = (ts: number) => {
      if (start === null) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(target * eased));
      if (progress < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target, duration, ...deps]);
  return value;
}

function orbitBorder(orbit: SatelliteTrack["orbit"]) {
  if (orbit === "LEO") return "border-[#00d4ff] text-[#00d4ff]";
  if (orbit === "MEO") return "border-[#ffb700] text-[#ffb700]";
  if (orbit === "GEO") return "border-[#00ff9d] text-[#00ff9d]";
  return "border-white/20 text-white/40";
}

function parseVel(v: string): number {
  return parseFloat(v.replace(/[^\d.]/g, "")) || 0;
}

function orbitType(value?: string | null): SatelliteTrack["orbit"] {
  if (value === "MEO" || value === "GEO" || value === "HEO") return value;
  return "LEO";
}

function propagateOrbit(noradId: number, altitudeKm: number, orbitType: string, timeMs: number) {
  const R_earth = 6371; // Earth radius in km
  const GM = 3.986004418e5; // km^3/s^2

  let alt = altitudeKm;
  if (!alt || alt <= 0) {
    alt = orbitType === "GEO" ? 35786 : orbitType === "MEO" ? 20200 : 550;
  }
  const a = R_earth + alt;
  const periodSec = 2 * Math.PI * Math.sqrt(Math.pow(a, 3) / GM);
  const periodMs = periodSec * 1000;

  const inclinationDeg = 30 + (noradId % 60); // 30 to 90 degrees
  const inclinationRad = (inclinationDeg * Math.PI) / 180;
  const raanDeg = (noradId * 13) % 360;
  const raanRad = (raanDeg * Math.PI) / 180;

  const timeSpeedup = 150;
  const phase = ((timeMs * timeSpeedup) / periodMs) * 2 * Math.PI;

  const x_orbit = a * Math.cos(phase);
  const y_orbit = a * Math.sin(phase);

  const x_eci = x_orbit * Math.cos(raanRad) - y_orbit * Math.sin(raanRad) * Math.cos(inclinationRad);
  const y_eci = x_orbit * Math.sin(raanRad) + y_orbit * Math.cos(raanRad) * Math.cos(inclinationRad);
  const z_eci = y_orbit * Math.sin(inclinationRad);

  const r = Math.sqrt(x_eci * x_eci + y_eci * y_eci + z_eci * z_eci);
  const lat = (Math.asin(z_eci / r) * 180) / Math.PI;
  let lng = (Math.atan2(y_eci, x_eci) * 180) / Math.PI;

  const earthRotationSpeed = 360 / (86164 * 1000);
  const rotationAngle = (timeMs * timeSpeedup * earthRotationSpeed) % 360;
  lng = ((lng - rotationAngle + 180) % 360) - 180;
  if (lng < -180) lng += 360;

  const vel = Math.sqrt(GM / a);

  return { lat, lng, vel };
}

function generateOrbitPath(noradId: number, altitudeKm: number, orbitType: string, timeMs: number) {
  const R_earth = 6371;
  const GM = 3.986004418e5;

  let alt = altitudeKm;
  if (!alt || alt <= 0) {
    alt = orbitType === "GEO" ? 35786 : orbitType === "MEO" ? 20200 : 550;
  }
  const a = R_earth + alt;
  const periodSec = 2 * Math.PI * Math.sqrt(Math.pow(a, 3) / GM);

  const inclinationDeg = 30 + (noradId % 60);
  const inclinationRad = (inclinationDeg * Math.PI) / 180;
  const raanDeg = (noradId * 13) % 360;
  const raanRad = (raanDeg * Math.PI) / 180;

  const timeSpeedup = 150;
  const earthRotationSpeed = 360 / (86164 * 1000);
  const rotationAngle = (timeMs * timeSpeedup * earthRotationSpeed) % 360;

  const points = [];
  const numPoints = 90;
  for (let i = 0; i <= numPoints; i++) {
    const phase = (i / numPoints) * 2 * Math.PI;
    const x_orbit = a * Math.cos(phase);
    const y_orbit = a * Math.sin(phase);

    const x_eci = x_orbit * Math.cos(raanRad) - y_orbit * Math.sin(raanRad) * Math.cos(inclinationRad);
    const y_eci = x_orbit * Math.sin(raanRad) + y_orbit * Math.cos(raanRad) * Math.cos(inclinationRad);
    const z_eci = y_orbit * Math.sin(inclinationRad);

    const r = Math.sqrt(x_eci * x_eci + y_eci * y_eci + z_eci * z_eci);
    const lat = (Math.asin(z_eci / r) * 180) / Math.PI;
    let lng = (Math.atan2(y_eci, x_eci) * 180) / Math.PI;

    lng = ((lng - rotationAngle + 180) % 360) - 180;
    if (lng < -180) lng += 360;

    points.push({ lat, lng });
  }
  return points;
}

function toTrack(sat: SatelliteSummary): SatelliteTrack {
  const orbit = orbitType(sat.orbit_type);
  const altitude = Math.round(Number(sat.altitude_km) || (orbit === "GEO" ? 35786 : orbit === "MEO" ? 20200 : 550));
  const risk = Math.round(Number(sat.risk_score) || 0);

  return {
    id: sat.norad_id,
    name: sat.object_name,
    orbit,
    lat: 0,
    lng: 0,
    alt: altitude,
    velocity: orbit === "GEO" ? "3.07 km/s" : orbit === "MEO" ? "3.90 km/s" : "7.50 km/s",
    risk,
    compliance: sat.risk_level || "N/A",
    sustainability: Math.max(0, 100 - risk),
    forecast: risk >= 75 ? "critical" : risk >= 55 ? "elevated" : risk >= 35 ? "watch" : "nominal",
    operator: sat.object_id || "Catalogued",
  };
}

/* ═══════════════════════════════════════════════════════════════════════════ */
export default function MissionControlPage() {
  const router = useRouter();
  const [satellites, setSatellites] = useState<SatelliteTrack[]>([]);
  const [metrics, setMetrics] = useState<MetricsSummaryPayload | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [timeMs, setTimeMs] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const interval = setInterval(() => {
      setTimeMs(Date.now() - start);
    }, 60);
    return () => clearInterval(interval);
  }, []);

  const selectedSat = useMemo(() => {
    const sat = satellites.find((s) => s.id === selectedId) ?? satellites[0] ?? null;
    if (!sat) return null;
    const pos = propagateOrbit(sat.id, sat.alt, sat.orbit, timeMs);
    return {
      ...sat,
      lat: pos.lat,
      lng: pos.lng,
      velocity: `${pos.vel.toFixed(2)} km/s`,
    };
  }, [satellites, selectedId, timeMs]);

  const propagatedSatellites = useMemo(() => {
    return satellites.map((sat) => {
      const pos = propagateOrbit(sat.id, sat.alt, sat.orbit, timeMs);
      return {
        ...sat,
        lat: pos.lat,
        lng: pos.lng,
      };
    });
  }, [satellites, timeMs]);

  const orbitPath = useMemo(() => {
    const sat = satellites.find((s) => s.id === selectedId) ?? satellites[0] ?? null;
    if (!sat) return undefined;
    return generateOrbitPath(sat.id, sat.alt, sat.orbit, timeMs);
  }, [satellites, selectedId, timeMs]);

  const filteredSatellites = useMemo(() => {
    if (!searchQuery.trim()) return satellites;
    const q = searchQuery.toLowerCase();
    return satellites.filter(
      (s) => s.name.toLowerCase().includes(q) || String(s.id).includes(q),
    );
  }, [searchQuery, satellites]);

  useEffect(() => {
    let cancelled = false;
    async function loadInitialData() {
      try {
        const [satPayload, metricsPayload] = await Promise.all([
          listSatellites(100, 0),
          getMetricsSummary(),
        ]);
        if (cancelled) return;
        const tracks = satPayload.satellites.map(toTrack);
        setSatellites(tracks);
        setMetrics(metricsPayload);
        setSelectedId(tracks[0]?.id ?? null);
      } catch (err: unknown) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Unable to load live satellite data.");
      }
    }
    loadInitialData();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const trimmed = searchQuery.trim();
    const timer = setTimeout(async () => {
      try {
        const payload = trimmed.length >= 2
          ? await searchSatellites(trimmed, 100)
          : await listSatellites(100, 0);
        if (cancelled) return;
        const nextSatellites = "results" in payload ? payload.results : payload.satellites;
        const tracks = nextSatellites.map(toTrack);
        setSatellites(tracks);
        setSelectedId((current) => tracks.some((sat) => sat.id === current) ? current : tracks[0]?.id ?? null);
      } catch (err: unknown) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Satellite search failed.");
      }
    }, 300);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [searchQuery]);

  const heroCount = useCountUp(metrics?.total_satellites ?? 0, 2200);
  const velNum = useCountUp(Math.round(parseVel(selectedSat?.velocity ?? "0") * 100), 800, [selectedId]);
  const altCount = useCountUp(selectedSat?.alt ?? 0, 800, [selectedId]);
  const riskCount = useCountUp(selectedSat?.risk ?? 0, 800, [selectedId]);

  const handleSelect = useCallback((sat: SatelliteTrack) => setSelectedId(sat.id), []);

  const riskColor = (selectedSat?.risk ?? 0) >= 75
    ? "var(--c-critical)"
    : (selectedSat?.risk ?? 0) >= 55
    ? "var(--c-elevated)"
    : "var(--c-nominal)";

  return (
    <div className="relative w-full overflow-y-auto main-scroll-container" style={{ background: "#000", height: "calc(100vh - var(--topbar-h))" }}>

      {/* ═══════════════════════════════════════════════════════════════════
          SECTION 1 — HERO VIEWPORT (60% Space Visor, 40% Control HUD Console)
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="relative w-full flex overflow-hidden shrink-0" style={{ height: "calc(100vh - var(--topbar-h))" }}>
        
        {/* ── LEFT SIDE: SPACE VISOR (60%) ── */}
        <div className="relative w-[60%] h-full overflow-hidden" style={{ borderRight: "1px solid var(--c-border)" }}>
          
          {/* Earth, Moon & ISS GlobeWrapper scene */}
          <div className="absolute inset-0 z-10">
            <GlobeWrapper
              satellites={propagatedSatellites}
              selectedId={selectedId ?? 0}
              onSelect={handleSelect}
              orbitPath={orbitPath}
            />
          </div>

          {/* Holographic grid scanner overlay on left visor */}
          <div className="absolute inset-0 pointer-events-none z-15 opacity-10"
            style={{
              backgroundImage: `
                linear-gradient(to right, var(--c-cyan) 1px, transparent 1px),
                linear-gradient(to bottom, var(--c-cyan) 1px, transparent 1px)
              `,
              backgroundSize: "60px 60px"
            }}
          />

          {/* Command tag overlay - top left */}
          <div className="absolute top-4 left-4 z-20 pointer-events-none">
            <div className="flex flex-col gap-0.5">
              <span className="font-data text-[7px] uppercase tracking-[0.35em]" style={{ color: "rgba(77,217,245,0.4)" }}>
                HUD VISUALIZATION REGION
              </span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="font-display text-[15px] uppercase tracking-wider text-white" style={{ textShadow: "0 0 20px rgba(255,255,255,0.4)" }}>
                  COCKPIT VIEWPORT
                </span>
                <span className="h-1.5 w-1.5 rounded-full" style={{ background: "var(--c-cyan)", boxShadow: "0 0 6px var(--c-cyan)" }} />
              </div>
            </div>
          </div>

          {/* Visor window corner brackets */}
          {["top-0 left-0", "top-0 right-0", "bottom-0 left-0", "bottom-0 right-0"].map((pos, i) => (
            <div
              key={i}
              className={`absolute ${pos} z-20 pointer-events-none`}
              style={{ width: 32, height: 32 }}
            >
              <div style={{
                position: "absolute", inset: 0,
                borderTop: (i < 2) ? "1.5px solid rgba(77,217,245,0.35)" : "none",
                borderBottom: (i >= 2) ? "1.5px solid rgba(77,217,245,0.35)" : "none",
                borderLeft: (i % 2 === 0) ? "1.5px solid rgba(77,217,245,0.35)" : "none",
                borderRight: (i % 2 === 1) ? "1.5px solid rgba(77,217,245,0.35)" : "none",
              }} />
            </div>
          ))}

          {/* Floating Bouncing Scroll Down Indicator (bottom center of left space view) */}
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center gap-1.5 pointer-events-none">
            <span className="font-data text-[7px] uppercase tracking-[0.3em]" style={{ color: "rgba(255,255,255,0.4)" }}>
              SCROLL FOR DEBRIS INTELLIGENCE
            </span>
            <motion.div
              animate={{ y: [0, 4, 0] }}
              transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
              style={{ color: "rgba(255,255,255,0.5)" }}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 5v14M19 12l-7 7-7-7" />
              </svg>
            </motion.div>
          </div>
        </div>

        {/* ── RIGHT SIDE: WORKSTATION CONSOLE (40%) ── */}
        <div className="relative w-[40%] h-full flex flex-col overflow-hidden" style={{ background: "rgba(8,12,18,0.96)", backdropFilter: "blur(20px)" }}>
          
          {/* Subtle header border grid */}
          <div className="absolute inset-x-0 top-0 h-px" style={{ background: "linear-gradient(to right, transparent, var(--c-cyan), transparent)" }} />

          {/* Console Identity Header */}
          <div className="px-5 py-4 shrink-0 flex items-center justify-between" style={{ borderBottom: "1px solid var(--c-border)" }}>
            <div>
              <span className="label block mb-0.5" style={{ color: "var(--c-cyan)" }}>MOSIP OPERATIONS SYSTEM v3.4</span>
              <h1 className="font-display text-[15px] uppercase tracking-[0.08em] text-white">
                SSA COMMAND DECK CONSOLE
              </h1>
            </div>
            <div className="flex items-center gap-2">
              <span className="pulse-dot" style={{ background: "var(--c-nominal)" }} />
              <span className="font-data text-[8px] uppercase tracking-widest text-[var(--c-nominal)]">ONLINE</span>
            </div>
          </div>

          {/* Live System Metrics Strip */}
          <div className="grid grid-cols-4 px-5 py-2.5 shrink-0 bg-white/[0.01]" style={{ borderBottom: "1px solid var(--c-border)" }}>
            {[
              { label: "TRACKING", value: heroCount.toLocaleString(), color: "var(--c-cyan)" },
              { label: "ALERTS", value: String(metrics?.critical_risk_count ?? "—"), color: (metrics?.critical_risk_count ?? 0) > 0 ? "var(--c-critical)" : "var(--t-secondary)" },
              { label: "AVG RISK", value: `${metrics?.average_risk_score ?? "—"}%`, color: "var(--c-elevated)" },
              { label: "AGENTS", value: "8/8", color: "var(--c-nominal)" }
            ].map(col => (
              <div key={col.label} className="flex flex-col">
                <span className="font-data text-[7px] uppercase tracking-wider text-slate-500">{col.label}</span>
                <span className="font-data text-[12px] font-bold tabular-nums" style={{ color: col.color }}>{col.value}</span>
              </div>
            ))}
          </div>

          {/* Satellite Catalog search */}
          <div className="px-4 py-2 shrink-0" style={{ borderBottom: "1px solid var(--c-border)" }}>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-sm" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--c-border)" }}>
              <Search size={10} style={{ color: "var(--c-cyan)", opacity: 0.7 }} />
              <input
                type="text"
                placeholder="Search catalog NORAD ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-transparent font-data text-[10px] outline-none placeholder:text-slate-600"
                style={{ color: "#fff", caretColor: "var(--c-cyan)" }}
              />
            </div>
          </div>

          {/* Scrollable Satellite Table list */}
          <div className="flex-1 overflow-y-auto min-h-0" style={{ borderBottom: "1px solid var(--c-border)" }}>
            <div className="grid grid-cols-12 px-4 py-1.5 shrink-0 border-b border-white/[0.02] bg-white/[0.005]">
              <span className="col-span-8 font-data text-[7px] uppercase text-slate-500">OBJECT IDENTIFIER</span>
              <span className="col-span-2 font-data text-[7px] uppercase text-slate-500 text-center">REGIME</span>
              <span className="col-span-2 font-data text-[7px] uppercase text-slate-500 text-right">RISK</span>
            </div>
            
            <AnimatePresence mode="popLayout">
              {filteredSatellites.map((sat) => {
                const isSelected = sat.id === selectedId;
                const rc = sat.risk >= 75 ? "var(--c-critical)" : sat.risk >= 55 ? "var(--c-elevated)" : "rgba(255,255,255,0.3)";
                return (
                  <motion.button
                    key={sat.id}
                    layout
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.1 }}
                    onClick={() => setSelectedId(sat.id)}
                    className="grid grid-cols-12 w-full px-4 py-2 text-left transition-all border-b border-white/[0.015]"
                    style={{
                      background: isSelected ? "rgba(77,217,245,0.06)" : "transparent",
                      borderLeft: `2.5px solid ${isSelected ? "var(--c-cyan)" : "transparent"}`,
                    }}
                  >
                    <div className="col-span-8 min-w-0 flex items-center gap-2">
                      <div className="h-1 w-1 rounded-full shrink-0" style={{ background: sat.risk >= 75 ? "var(--c-critical)" : sat.risk >= 55 ? "var(--c-elevated)" : "var(--c-nominal)" }} />
                      <div className="min-w-0">
                        <span className="block truncate font-data text-[10px]" style={{ color: isSelected ? "#fff" : "rgba(255,255,255,0.65)" }}>
                          {sat.name}
                        </span>
                        <span className="font-data text-[7px] text-slate-600">
                          NORAD {sat.id}
                        </span>
                      </div>
                    </div>
                    <div className="col-span-2 flex items-center justify-center">
                      <span className="font-data text-[7px] uppercase px-1 rounded-sm bg-white/[0.03] text-slate-400">
                        {sat.orbit}
                      </span>
                    </div>
                    <div className="col-span-2 flex items-center justify-end">
                      <span className="font-data text-[10px] tabular-nums font-bold" style={{ color: rc }}>
                        {sat.risk}
                      </span>
                    </div>
                  </motion.button>
                );
              })}
            </AnimatePresence>
            {filteredSatellites.length === 0 && (
              <div className="py-12 text-center">
                <span className="font-data text-[8px] uppercase tracking-wider text-slate-600">EMPTY CATALOG TARGET</span>
              </div>
            )}
          </div>

          {/* Telemetry Locked On HUD (at the bottom of console) */}
          {selectedSat && (
            <div className="p-4 shrink-0 bg-white/[0.005]" style={{ borderBottom: "1px solid var(--c-border)" }}>
              <div className="rounded p-3 flex flex-col gap-2.5" style={{ background: "rgba(4,9,15,0.5)", border: "1px solid var(--c-border)" }}>
                
                {/* ID Header */}
                <div className="flex items-center justify-between pb-1.5 border-b border-white/[0.04]">
                  <div className="flex items-center gap-1.5">
                    <span className="pulse-dot" style={{ background: riskColor }} />
                    <span className="font-data text-[8px] uppercase tracking-widest text-slate-500">LOCKED TELEMETRY</span>
                  </div>
                  <span className="font-data text-[8px] text-white/50">NORAD {selectedSat.id}</span>
                </div>

                {/* Name */}
                <span className="block font-display text-[13px] uppercase tracking-wider text-white truncate">
                  {selectedSat.name}
                </span>

                {/* Telemetry metrics */}
                <div className="grid grid-cols-3 gap-2 mt-1">
                  {[
                    { label: "VELOCITY", val: `${(velNum / 100).toFixed(2)}`, unit: "km/s", icon: TrendingUp },
                    { label: "ALTITUDE", val: altCount.toLocaleString(), unit: "km", icon: Cpu },
                    { label: "RISK INDEX", val: `${riskCount}`, unit: "", icon: AlertTriangle, color: riskColor }
                  ].map(cell => {
                    const Icon = cell.icon;
                    return (
                      <div key={cell.label} className="flex flex-col">
                        <div className="flex items-center gap-1 mb-0.5">
                          <Icon size={8} style={{ color: "var(--c-cyan)", opacity: 0.6 }} />
                          <span className="font-data text-[6.5px] uppercase tracking-wider text-slate-500">{cell.label}</span>
                        </div>
                        <span className="font-data text-[12px] font-bold tabular-nums" style={{ color: cell.color ?? "#fff" }}>
                          {cell.val}
                          <span className="text-[7.5px] font-normal ml-0.5 text-slate-500">{cell.unit}</span>
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Action Trigger panel */}
          <div className="p-4 shrink-0 flex gap-2">
            <motion.button
              whileTap={{ scale: 0.97 }}
              onClick={() => selectedId && router.push(`/satellites?id=${selectedId}`)}
              disabled={!selectedId}
              className="w-full h-9 flex items-center justify-center gap-1.5 rounded-sm font-data text-[9px] uppercase tracking-[0.2em] transition-all disabled:opacity-30 btn-primary"
            >
              <Zap size={10} />
              INITIATE ASSESSMENT
            </motion.button>
          </div>
        </div>

      </div>

      {/* ── Error Banner overlay (if API down) ── */}
      {error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="absolute top-14 left-1/2 -translate-x-1/2 z-30"
        >
          <div
            className="px-4 py-2 rounded font-data text-[9px] uppercase tracking-wider"
            style={{ background: "rgba(239,67,67,0.12)", border: "1px solid rgba(239,67,67,0.35)", color: "var(--c-critical)", backdropFilter: "blur(8px)" }}
          >
            ⚠ {error}
          </div>
        </motion.div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════
          SECTION 2 — DEBRIS MITIGATION SECTION (Slide 2: Full Screen Visual)
          ═══════════════════════════════════════════════════════════════════ */}
      <div 
        className="relative w-full h-screen overflow-hidden flex items-center justify-between shrink-0"
        style={{ 
          backgroundImage: "url('/debris_orbit.png')",
          backgroundSize: "cover",
          backgroundPosition: "center",
          borderTop: "1px solid var(--c-border)",
        }}
      >
        {/* Dark Cinematic overlay gradient (85% black on left to fade into space visual on right) */}
        <div className="absolute inset-0 z-10" style={{ background: "linear-gradient(to right, rgba(8,12,18,0.96) 45%, rgba(8,12,18,0.4) 100%)" }} />
        
        {/* Space Grid overlay */}
        <div className="cyber-grid absolute inset-0 opacity-10 z-12 pointer-events-none" />

        <div className="relative z-20 max-w-5xl mx-auto w-full px-8 md:px-12 flex flex-col md:flex-row items-center justify-between gap-12">
          {/* Slide Text Block */}
          <div className="flex flex-col gap-5 max-w-md">
            <span className="font-data text-[9px] uppercase tracking-[0.35em] text-[var(--c-cyan)]">
              MISSION THREAT // KESSLER SHELL DESTRUCTION
            </span>
            <h2 className="font-display text-4xl md:text-5xl uppercase tracking-wider text-white leading-tight font-bold">
              Cleaning Up<br/>The Orbit
            </h2>
            <p className="text-[13px] leading-relaxed text-slate-300">
              Low Earth Orbit (LEO) is cluttered with defunct payloads and cascading kinetic fragments traveling at speeds exceeding 7.5 km/s. MOSIP ingests raw telemetry to catalog conjunction risks, helping agencies visualize active orbital footprints before debris collisions occur.
            </p>
            <div className="pt-2">
              <button 
                onClick={() => {
                  const el = document.querySelector(".relative.w-full.flex.overflow-hidden.shrink-0");
                  el?.scrollIntoView({ behavior: "smooth" });
                }}
                className="border border-white hover:bg-white hover:text-black text-white font-data text-[10px] px-6 py-3 transition uppercase tracking-widest rounded-sm"
              >
                EXPLORE CATALOGUE →
              </button>
            </div>
          </div>

          {/* Slide Glassmorphism Data Overlay */}
          <div 
            className="p-5 rounded-sm max-w-sm w-full backdrop-blur-md border border-white/[0.06] flex flex-col gap-4"
            style={{ background: "rgba(11,15,23,0.7)" }}
          >
            <span className="label block border-b border-white/[0.04] pb-2">CONGESTION READOUTS</span>
            
            <div className="flex flex-col gap-3">
              {[
                { regime: "Debris & Defunct Satellites", percent: 68, count: "10,660 objs", color: "var(--c-critical)" },
                { regime: "Active Satellites", percent: 21, count: "3,290 objs", color: "var(--c-cyan)" },
                { regime: "MEO & GEO Regimes", percent: 11, count: "1,730 objs", color: "var(--c-nominal)" }
              ].map(r => (
                <div key={r.regime} className="flex flex-col gap-1">
                  <div className="flex justify-between font-data text-[9px]">
                    <span style={{ color: "rgba(255,255,255,0.7)" }}>{r.regime}</span>
                    <span className="font-bold" style={{ color: r.color }}>{r.count}</span>
                  </div>
                  <div className="risk-bar-track">
                    <div className="risk-bar-fill" style={{ width: `${r.percent}%`, background: r.color }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          SECTION 3 — REGULATORY COMPLIANCE SECTION (Slide 3: Rocket Visual)
          ═══════════════════════════════════════════════════════════════════ */}
      <div 
        className="relative w-full h-screen overflow-hidden flex items-center justify-between shrink-0"
        style={{ 
          backgroundImage: "url('/orbital_compliance.png')",
          backgroundSize: "cover",
          backgroundPosition: "center",
          borderTop: "1px solid var(--c-border)",
        }}
      >
        {/* Dark Cinematic overlay gradient (85% black on right to fade into launch visual on left) */}
        <div className="absolute inset-0 z-10" style={{ background: "linear-gradient(to left, rgba(8,12,18,0.96) 45%, rgba(8,12,18,0.4) 100%)" }} />
        
        <div className="cyber-grid absolute inset-0 opacity-10 z-12 pointer-events-none" />

        <div className="relative z-20 max-w-5xl mx-auto w-full px-8 md:px-12 flex flex-col md:flex-row items-center justify-between gap-12">
          
          {/* Slide Glassmorphism Data Overlay */}
          <div 
            className="p-5 rounded-sm max-w-sm w-full backdrop-blur-md border border-white/[0.06] flex flex-col gap-4 md:order-first order-last"
            style={{ background: "rgba(11,15,23,0.7)" }}
          >
            <span className="label block border-b border-white/[0.04] pb-2">POLICY AUDITS</span>
            
            <div className="flex flex-col gap-3 font-digital text-xs">
              <div className="flex justify-between items-center py-1">
                <span className="text-slate-300 font-data text-[10px]">25-Year Disposal Rule</span>
                <span className="status-tag critical">42% AUDIT FAIL</span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-slate-300 font-data text-[10px]">Kinetic Fragmentation Index</span>
                <span className="status-tag watch">ELEVATED BURDEN</span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-slate-300 font-data text-[10px]">De-orbit Energy Margins</span>
                <span className="status-tag nominal">92% COMPLIANT</span>
              </div>
            </div>
            
            <div className="text-[10px] text-slate-400 border-t border-white/[0.04] pt-2 leading-relaxed">
              All telemetry is validated against IADC space debris mitigation guidelines in real-time.
            </div>
          </div>

          {/* Slide Text Block */}
          <div className="flex flex-col gap-5 max-w-md">
            <span className="font-data text-[9px] uppercase tracking-[0.35em] text-[var(--c-ai)]">
              POLICY COMPLIANCE // COGNITIVE LAW AUDITOR
            </span>
            <h2 className="font-display text-4xl md:text-5xl uppercase tracking-wider text-white leading-tight font-bold">
              Enforcing<br/>Orbital Law
            </h2>
            <p className="text-[13px] leading-relaxed text-slate-300">
              Launching payloads demands adherence to safety treaties. MOSIP checks every cataloged trajectory against IADC and ESA orbital guidelines using vector semantic lookup in Qdrant, highlighting compliance grade violations instantly.
            </p>
            <div className="pt-2">
              <button 
                onClick={() => router.push("/regulations")}
                className="border border-white hover:bg-white hover:text-black text-white font-data text-[10px] px-6 py-3 transition uppercase tracking-widest rounded-sm"
              >
                QUERY POLICY BASE →
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          SECTION 4 — AUTOMATED AVOIDANCE SECTION (Slide 4: Thruster Visual)
          ═══════════════════════════════════════════════════════════════════ */}
      <div 
        className="relative w-full h-screen overflow-hidden flex items-center justify-between shrink-0"
        style={{ 
          backgroundImage: "url('/collision_evasion.png')",
          backgroundSize: "cover",
          backgroundPosition: "center",
          borderTop: "1px solid var(--c-border)",
        }}
      >
        {/* Dark Cinematic overlay gradient (85% black on left to fade into visual on right) */}
        <div className="absolute inset-0 z-10" style={{ background: "linear-gradient(to right, rgba(8,12,18,0.96) 45%, rgba(8,12,18,0.4) 100%)" }} />
        
        <div className="cyber-grid absolute inset-0 opacity-10 z-12 pointer-events-none" />

        <div className="relative z-20 max-w-5xl mx-auto w-full px-8 md:px-12 flex flex-col md:flex-row items-center justify-between gap-12">
          {/* Slide Text Block */}
          <div className="flex flex-col gap-5 max-w-md">
            <span className="font-data text-[9px] uppercase tracking-[0.35em] text-[var(--c-nominal)]">
              AUTONOMOUS NAVIGATION // EVASION THRESHOLD
            </span>
            <h2 className="font-display text-4xl md:text-5xl uppercase tracking-wider text-white leading-tight font-bold">
              Autonomous<br/>Evasion Maneuvers
            </h2>
            <p className="text-[13px] leading-relaxed text-slate-300">
              When threat indexes exceed safe parameters, MOSIP calculates precise thruster impulses (delta-v values) to guide satellites into safe orbits. The maneuver coordinates are structured by our autonomous agents and generated as executive command briefings using Groq LLM.
            </p>
            <div className="pt-2">
              <button 
                onClick={() => router.push("/simulator")}
                className="border border-white hover:bg-white hover:text-black text-white font-data text-[10px] px-6 py-3 transition uppercase tracking-widest rounded-sm"
              >
                RUN SIMULATIONS →
              </button>
            </div>
          </div>

          {/* Slide Glassmorphism Data Overlay */}
          <div 
            className="p-5 rounded-sm max-w-sm w-full backdrop-blur-md border border-white/[0.06] flex flex-col gap-4"
            style={{ background: "rgba(11,15,23,0.7)" }}
          >
            <span className="label block border-b border-white/[0.04] pb-2">MULTI-AGENT CHAIN STATUS</span>
            
            <div className="flex flex-col gap-3 font-digital text-[11px]">
              <div className="flex items-center gap-2">
                <div className="p-1 rounded bg-[var(--c-cyan-ghost)]">
                  <Cpu size={12} className="text-[var(--c-cyan)]" />
                </div>
                <div className="flex-1">
                  <span className="block font-semibold text-white">Surveillance & Risk</span>
                  <span className="text-[8px] text-slate-400">Monte Carlo conjunction assessment</span>
                </div>
                <span className="status-tag nominal text-[7px]">OK</span>
              </div>

              <div className="flex items-center gap-2">
                <div className="p-1 rounded bg-[var(--c-ai-ghost)]">
                  <Zap size={12} className="text-[var(--c-ai)]" />
                </div>
                <div className="flex-1">
                  <span className="block font-semibold text-white">Policy & Compliance</span>
                  <span className="text-[8px] text-slate-400">ESA/IADC policy vector query</span>
                </div>
                <span className="status-tag ai text-[7px]">OK</span>
              </div>

              <div className="flex items-center gap-2">
                <div className="p-1 rounded bg-emerald-500/10">
                  <AlertTriangle size={12} className="text-[var(--c-nominal)]" />
                </div>
                <div className="flex-1">
                  <span className="block font-semibold text-white">Maneuver & Avoidance</span>
                  <span className="text-[8px] text-slate-400">Delta-v propulsion trajectory computation</span>
                </div>
                <span className="status-tag nominal text-[7px]">ACTIVE</span>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
