"use client";

import { useEffect, useMemo, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  AlertOctagon,
  Download,
  Printer,
  Search,
} from "lucide-react";
import {
  assessNorad,
  listSatellites,
  searchSatellites,
  type AssessmentSection,
  type AssessmentPayload,
  type SatelliteSummary,
} from "@/utils/api";

type SatelliteLike = SatelliteSummary | AssessmentSection | undefined;

function fieldValue(source: SatelliteLike, key: string) {
  return source ? source[key as keyof typeof source] : undefined;
}

function fieldString(source: SatelliteLike, keys: string[], fallback = "") {
  for (const key of keys) {
    const value = fieldValue(source, key);
    if (typeof value === "string" && value.trim()) return value;
    if (typeof value === "number") return String(value);
  }
  return fallback;
}

function fieldNumber(source: SatelliteLike, keys: string[]) {
  for (const key of keys) {
    const value = fieldValue(source, key);
    const numeric = Number(value);
    if (Number.isFinite(numeric)) return numeric;
  }
  return undefined;
}

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

function satelliteName(sat?: SatelliteLike) {
  return fieldString(sat, ["object_name", "name"], "Unknown Satellite");
}

function satelliteNorad(sat?: SatelliteLike) {
  return fieldNumber(sat, ["norad_id", "id"]) ?? null;
}

function normalizeRisk(value: unknown) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? Math.round(numeric) : 0;
}

function riskColor(score: number) {
  if (score >= 75) return "var(--c-critical)";
  if (score >= 55) return "var(--c-elevated)";
  return "var(--c-nominal)";
}

function reportFromAssessment(assessment: AssessmentPayload | null) {
  if (!assessment) return "";
  return assessment.report?.trim() || "";
}

function ReportCenterContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const idParam = searchParams.get("id");

  const [query, setQuery] = useState("");
  const [targets, setTargets] = useState<SatelliteSummary[]>([]);
  const [selectedId, setSelectedId] = useState(idParam || "");
  const [assessment, setAssessment] = useState<AssessmentPayload | null>(null);
  const [loadingTargets, setLoadingTargets] = useState(true);
  const [loadingReport, setLoadingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedSat = useMemo(() => {
    const fromList = targets.find((sat) => String(sat.norad_id) === selectedId);
    if (fromList) return fromList;
    if (assessment?.satellite) {
      return {
        norad_id: Number(satelliteNorad(assessment.satellite) ?? selectedId),
        object_name: satelliteName(assessment.satellite),
        altitude_km: fieldNumber(assessment.satellite, ["altitude_km"]),
        orbit_type: fieldString(assessment.satellite, ["orbit_type"]) || null,
        risk_score: fieldNumber(assessment.satellite, ["risk_score"]),
        risk_level: fieldString(assessment.satellite, ["risk_level"]) || null,
      };
    }
    return null;
  }, [assessment, selectedId, targets]);

  const reportText = reportFromAssessment(assessment);
  const riskScore = normalizeRisk(
    fieldValue(assessment?.collision_analysis, "risk_score") ??
      fieldValue(assessment?.satellite, "risk_score") ??
      selectedSat?.risk_score,
  );

  useEffect(() => {
    let cancelled = false;

    async function loadInitialTargets() {
      setLoadingTargets(true);
      setError(null);
      try {
        const payload = await listSatellites(75, 0);
        if (cancelled) return;
        setTargets(payload.satellites);
        const firstId = idParam || String(payload.satellites[0]?.norad_id ?? "");
        setSelectedId(firstId);
      } catch (err: unknown) {
        if (!cancelled) {
          setError(errorMessage(err, "Unable to load satellites from MOSIP API."));
        }
      } finally {
        if (!cancelled) setLoadingTargets(false);
      }
    }

    loadInitialTargets();
    return () => {
      cancelled = true;
    };
  }, [idParam]);

  useEffect(() => {
    if (!selectedId) return;
    let cancelled = false;

    async function loadReport() {
      setLoadingReport(true);
      setError(null);
      try {
        const result = await assessNorad(selectedId);
        if (cancelled) return;
        if (result.errors?.length) throw new Error(result.errors[0]);
        setAssessment(result);
      } catch (err: unknown) {
        if (!cancelled) {
          setAssessment(null);
          setError(errorMessage(err, `Unable to generate assessment for NORAD ${selectedId}.`));
        }
      } finally {
        if (!cancelled) setLoadingReport(false);
      }
    }

    loadReport();
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  const runSearch = async (event?: React.FormEvent) => {
    event?.preventDefault();
    const trimmed = query.trim();
    setLoadingTargets(true);
    setError(null);

    try {
      const payload = trimmed.length >= 2
        ? await searchSatellites(trimmed, 50)
        : await listSatellites(75, 0);
      const nextTargets = "results" in payload ? payload.results : payload.satellites;
      setTargets(nextTargets);
      if (nextTargets.length && !nextTargets.some((sat) => String(sat.norad_id) === selectedId)) {
        const nextId = String(nextTargets[0].norad_id);
        setSelectedId(nextId);
        router.push(`/reports?id=${nextId}`);
      }
    } catch (err: unknown) {
      setError(errorMessage(err, "Satellite search failed."));
    } finally {
      setLoadingTargets(false);
    }
  };

  const selectSatellite = (noradId: number) => {
    const nextId = String(noradId);
    setSelectedId(nextId);
    router.push(`/reports?id=${nextId}`);
  };

  const handlePrint = () => {
    if (!reportText || !selectedSat) return;
    const w = window.open("", "_blank");
    if (!w) return;
    w.document.write(`<html><head><title>MOSIP Report - ${satelliteName(selectedSat)}</title>
      <style>body{background:#04050a;color:#8899aa;font-family:'Courier New',monospace;font-size:11px;padding:32px;white-space:pre-wrap;line-height:1.8}</style>
      </head><body>${reportText.replace(/[&<>]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[char] || char)}</body></html>`);
    w.document.close();
    w.print();
  };

  const handleDownload = () => {
    if (!reportText || !selectedSat) return;
    const blob = new Blob([reportText], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `MOSIP-${selectedSat.norad_id}-report.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <div className="flex h-[calc(100vh-var(--topbar-h))] overflow-hidden">

      {/* ── Target selector sidebar ──────────────────────────────────── */}
      <div
        className="w-[300px] shrink-0 flex flex-col"
        style={{ borderRight: "1px solid var(--c-border)", background: "var(--c-surface-0)" }}
      >
        {/* Sidebar header */}
        <div
          className="px-4 py-3 shrink-0"
          style={{ borderBottom: "1px solid var(--c-border)" }}
        >
          <span className="label block mb-0.5">POSTGRESQL CATALOG</span>
          <h2 className="font-display text-[11px] uppercase tracking-wider" style={{ color: "var(--t-primary)" }}>
            REPORT TARGET
          </h2>
          <form onSubmit={runSearch} className="mt-3 flex items-center gap-2 h-8 px-3 rounded"
            style={{ background: "var(--c-surface-1)", border: "1px solid var(--c-border)" }}>
            <Search size={10} style={{ color: "var(--t-meta)", flexShrink: 0 }} />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Name or NORAD ID..."
              className="min-w-0 flex-1 bg-transparent font-data text-[10px] outline-none"
              style={{ color: "var(--t-primary)", caretColor: "var(--c-cyan)" }}
            />
            <button
              type="submit"
              disabled={loadingTargets}
              className="font-data text-[8px] uppercase tracking-widest disabled:opacity-40"
              style={{ color: "var(--c-cyan)" }}
            >
              {loadingTargets ? "..." : "GO"}
            </button>
          </form>
        </div>

        {/* Column headers */}
        <div
          className="grid px-3 py-1.5 shrink-0"
          style={{
            gridTemplateColumns: "1fr 36px",
            borderBottom: "1px solid var(--c-border)",
          }}
        >
          <span className="label">OBJECT</span>
          <span className="label text-right">RISK</span>
        </div>

        {/* Target list */}
        <div className="flex-1 overflow-y-auto">
          {targets.map((sat) => {
            const isSelected = String(sat.norad_id) === selectedId;
            const score = normalizeRisk(sat.risk_score);
            const scoreColor = riskColor(score);
            return (
              <button
                key={sat.norad_id}
                onClick={() => selectSatellite(sat.norad_id)}
                className="grid w-full px-3 py-2 text-left transition-all"
                style={{
                  gridTemplateColumns: "1fr 36px",
                  background: isSelected ? "var(--c-cyan-ghost)" : "transparent",
                  borderLeft: `2px solid ${isSelected ? "var(--c-cyan)" : "transparent"}`,
                  borderBottom: "1px solid rgba(255,255,255,0.025)",
                }}
              >
                <div className="min-w-0">
                  <span
                    className="block truncate font-data text-[10px]"
                    style={{ color: isSelected ? "var(--t-primary)" : "var(--t-secondary)" }}
                  >
                    {sat.object_name}
                  </span>
                  <span className="font-data text-[8px]" style={{ color: "var(--t-meta)" }}>
                    {sat.norad_id}&nbsp;&middot;&nbsp;{sat.orbit_type || "--"}
                  </span>
                </div>
                {sat.risk_score != null && (
                  <div className="flex items-center justify-end">
                    <span className="font-data text-[10px] tabular-nums" style={{ color: scoreColor }}>
                      {score}
                    </span>
                  </div>
                )}
              </button>
            );
          })}

          {!loadingTargets && targets.length === 0 && (
            <div className="px-4 py-10 text-center">
              <span className="label">NO TARGETS FOUND</span>
            </div>
          )}
        </div>
      </div>

      {/* ── Report workspace ──────────────────────────────────────────── */}
      <div className="flex flex-1 flex-col overflow-hidden">

        {/* Report header bar */}
        <div
          className="flex items-center justify-between px-5 py-2.5 shrink-0"
          style={{ borderBottom: "1px solid var(--c-border)", background: "var(--c-surface-0)" }}
        >
          <div className="flex items-center gap-3">
            <div>
              <span className="label block mb-0.5">LANGGRAPH MULTI-AGENT REPORT</span>
              <span className="font-display text-[12px] uppercase tracking-wider" style={{ color: "var(--t-primary)" }}>
                {selectedSat ? satelliteName(selectedSat) : "NO TARGET SELECTED"}
              </span>
            </div>
            {selectedSat && (
              <span
                className="font-data text-[8px] uppercase px-2 py-0.5 rounded-sm"
                style={{
                  border: `1px solid ${riskColor(riskScore)}44`,
                  color: riskColor(riskScore),
                  background: `${riskColor(riskScore)}06`,
                }}
              >
                NORAD&nbsp;{selectedSat.norad_id}&nbsp;&middot;&nbsp;{selectedSat.orbit_type || "ORBIT PENDING"}&nbsp;&middot;&nbsp;{riskScore || "N/A"}%
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleDownload}
              disabled={!reportText}
              className="btn-ghost flex items-center gap-1.5 px-3 py-1.5 font-data text-[9px] uppercase tracking-widest rounded disabled:opacity-40"
            >
              <Download size={11} />
              DOWNLOAD .TXT
            </button>
            <button
              onClick={handlePrint}
              disabled={!reportText}
              className="btn-ghost flex items-center gap-1.5 px-3 py-1.5 font-data text-[9px] uppercase tracking-widest rounded disabled:opacity-40"
            >
              <Printer size={11} />
              PRINT / PDF
            </button>
          </div>
        </div>

        <motion.div
          key={selectedId || "empty"}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="flex-1 overflow-y-auto p-5"
        >
          {error && (
            <div
              className="mb-4 flex items-start gap-3 p-4 rounded"
              style={{ border: "1px solid rgba(239,67,67,0.25)", background: "rgba(239,67,67,0.04)" }}
            >
              <AlertOctagon size={16} style={{ color: "var(--c-critical)", flexShrink: 0, marginTop: 2 }} />
              <div>
                <h3 className="font-data text-[9px] uppercase tracking-widest" style={{ color: "var(--c-critical)" }}>
                  BACKEND CONNECTION FAULT
                </h3>
                <p className="mt-1 text-[11px]" style={{ color: "var(--t-secondary)" }}>{error}</p>
                <p className="mt-0.5 font-data text-[9px]" style={{ color: "var(--t-meta)" }}>
                  Ensure FastAPI is running on port 8000. Check PostgreSQL + Qdrant health.
                </p>
              </div>
            </div>
          )}

          {/* Report terminal viewer */}
          <div
            className="relative overflow-hidden"
            style={{
              background: "#040508",
              border: "1px solid var(--c-border)",
              borderRadius: "var(--border-r)",
              minHeight: "520px",
            }}
          >
            {/* Loading — "Build Log" sequence */}
            {loadingReport && (
              <div
                className="absolute inset-0 z-20 flex flex-col justify-center items-center gap-3"
                style={{ background: "rgba(4,5,8,0.92)", backdropFilter: "blur(4px)" }}
              >
                <div className="flex flex-col gap-1.5 w-52">
                  {[
                    "INITIALIZING AGENT GRAPH",
                    "LOADING ORBITAL PARAMETERS",
                    "QUERYING REGULATORY CORPUS",
                    "SYNTHESIZING ASSESSMENT",
                    "COMPILING REPORT",
                  ].map((step, i) => (
                    <div key={step} className="flex items-center gap-2">
                      <span className="font-data text-[7px] tabular-nums" style={{ color: "var(--t-meta)" }}>
                        {String(i + 1).padStart(2, "0")}
                      </span>
                      <span
                        className="font-data text-[8px] uppercase tracking-widest"
                        style={{ color: i === 2 ? "var(--c-cyan)" : "var(--t-meta)" }}
                      >
                        {step}
                      </span>
                      {i <= 2 && (
                        <span className="font-data text-[7px]" style={{ color: "var(--c-nominal)" }}>OK</span>
                      )}
                    </div>
                  ))}
                </div>
                <div
                  className="mt-2 w-52 h-px"
                  style={{ background: "rgba(255,255,255,0.06)" }}
                >
                  <div
                    className="h-full"
                    style={{ background: "var(--c-cyan)", animation: "loading 9s ease-in-out forwards" }}
                  />
                </div>
              </div>
            )}

            {/* Report terminal header */}
            <div
              className="flex items-center gap-2 px-4 py-2"
              style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}
            >
              <div className="flex gap-1">
                <div className="h-2 w-2 rounded-full" style={{ background: "rgba(239,67,67,0.4)" }} />
                <div className="h-2 w-2 rounded-full" style={{ background: "rgba(245,166,35,0.4)" }} />
                <div className="h-2 w-2 rounded-full" style={{ background: "rgba(61,232,155,0.4)" }} />
              </div>
              <span className="font-data text-[8px] uppercase tracking-widest" style={{ color: "var(--t-meta)" }}>
                MOSIP / ASSESSMENT / {selectedSat?.norad_id || "--"}
              </span>
            </div>

            <pre
              className="relative z-10 p-5 font-data text-[10px] leading-[1.8] whitespace-pre-wrap select-text"
              style={{ color: "var(--t-secondary)" }}
            >
              {reportText || "Select a target from the sidebar to generate a live MOSIP intelligence report."}
            </pre>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

export default function ReportsPage() {
  return (
    <Suspense fallback={
      <div className="grid h-full min-h-screen place-items-center font-data text-[9px] uppercase tracking-[0.3em]" style={{ color: "rgba(77,217,245,0.4)" }}>
        LOADING REPORT ENGINE...
      </div>
    }>
      <ReportCenterContent />
    </Suspense>
  );
}
