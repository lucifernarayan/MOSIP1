"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, SearchX, RefreshCw } from "lucide-react";
import { sourceColor } from "@/utils/mosip-data";
import { askRegulation, searchRegulations, type RegulationAnswerPayload, type RegulationSearchResult } from "@/utils/api";

function resultTitle(reg: RegulationSearchResult) {
  return reg.document || reg.source || "Retrieved regulation";
}

function RegulationCard({ reg, index }: { reg: RegulationSearchResult; index: number }) {
  const source = reg.source || "RAG";
  const accentColor = sourceColor(source);
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.28, delay: index * 0.04 }}
      style={{
        background: "var(--c-surface-0)",
        border: "1px solid var(--c-border)",
        borderRadius: "var(--border-r)",
        borderLeft: `2px solid ${accentColor}`,
        overflow: "hidden",
      }}
    >
      <div className="flex" >
        <div className="flex-1 px-4 py-3">
          {/* Header: source badge + title + confidence */}
          <div className="flex items-start justify-between gap-2 mb-2">
            <div className="flex items-center gap-2 min-w-0">
              {/* Source badge */}
              <span
                className="font-data text-[7px] uppercase tracking-widest px-1.5 py-0.5 shrink-0"
                style={{
                  background: `${accentColor}12`,
                  border: `1px solid ${accentColor}28`,
                  color: accentColor,
                  borderRadius: "2px",
                }}
              >
                {source}
              </span>
              <span
                className="font-display text-[11px] truncate"
                style={{ color: "var(--t-primary)" }}
              >
                {resultTitle(reg)}
              </span>
            </div>
            {/* Confidence / relevance score */}
            {reg.score != null && (
              <div className="flex items-center gap-1.5 shrink-0">
                <span className="label">RELEVANCE</span>
                <div className="flex items-center gap-1">
                  {/* Small bar indicator */}
                  <div
                    className="h-1 w-14 rounded-sm"
                    style={{ background: "rgba(255,255,255,0.07)" }}
                  >
                    <div
                      className="h-full rounded-sm"
                      style={{
                        width: `${Math.round(reg.score * 100)}%`,
                        background: accentColor,
                        opacity: 0.7,
                      }}
                    />
                  </div>
                  <span className="font-data text-[9px] tabular-nums" style={{ color: "var(--t-meta)" }}>
                    {reg.score.toFixed(3)}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Regulatory text — monospace terminal style */}
          <div
            className="px-3 py-2"
            style={{
              background: "var(--c-surface-1)",
              border: "1px solid var(--c-border)",
              borderRadius: "3px",
            }}
          >
            <span className="font-data text-[8px]" style={{ color: "var(--t-meta)" }}>§&nbsp;</span>
            <span className="font-data text-[10px] leading-relaxed" style={{ color: "var(--t-secondary)" }}>
              {reg.text || "No excerpt returned."}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default function RegulationsPage() {
  const [query, setQuery] = useState("space debris mitigation post mission disposal");
  const [results, setResults] = useState<RegulationSearchResult[]>([]);
  const [answer, setAnswer] = useState<RegulationAnswerPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sourceGroups = results.reduce<Record<string, number>>((acc, result) => {
    const source = result.source || "RAG";
    acc[source] = (acc[source] || 0) + 1;
    return acc;
  }, {});

  const runQuery = async (event?: React.FormEvent) => {
    event?.preventDefault();
    const trimmed = query.trim();
    if (trimmed.length < 3) return;
    setLoading(true);
    setError(null);
    try {
      const [searchPayload, answerPayload] = await Promise.all([
        searchRegulations(trimmed),
        askRegulation(trimmed, 5),
      ]);
      setResults(searchPayload.results || []);
      setAnswer(answerPayload);
      if (searchPayload.error || answerPayload.error) {
        setError(searchPayload.error || answerPayload.error || null);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Regulation retrieval failed.");
      setResults([]);
      setAnswer(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void Promise.resolve().then(() => runQuery());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex h-[calc(100vh-var(--topbar-h))] flex-col overflow-hidden">

      {/* ── Page header strip ─────────────────────────────────────────────── */}
      <div
        className="flex items-center justify-between px-6 py-3 shrink-0"
        style={{ borderBottom: "1px solid var(--c-border)", background: "var(--c-surface-0)" }}
      >
        <div>
          <span className="label block mb-0.5">REGULATORY KNOWLEDGE BASE</span>
          <h1 className="font-display text-[13px] uppercase tracking-[0.12em]" style={{ color: "var(--t-primary)" }}>
            SPACE DEBRIS REGULATIONS — ESA / IADC / NASA
          </h1>
        </div>

        {/* Source group stats */}
        <div className="flex items-center gap-3">
          {Object.entries(sourceGroups).map(([src, count]) => (
            <div key={src} className="flex items-center gap-1.5">
              <span className="font-data text-[8px] uppercase" style={{ color: sourceColor(src) }}>
                {src}
              </span>
              <span className="font-data text-[10px] tabular-nums" style={{ color: "var(--t-secondary)" }}>
                {count}
              </span>
            </div>
          ))}
          {results.length > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="label">RETRIEVED</span>
              <span className="font-data text-[10px] tabular-nums" style={{ color: "var(--c-cyan)" }}>
                {results.length}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* ── Search bar ────────────────────────────────────────────────────── */}
      <div
        className="px-6 py-3 shrink-0"
        style={{ borderBottom: "1px solid var(--c-border)", background: "var(--c-surface-0)" }}
      >
        <form
          onSubmit={runQuery}
          className="flex items-center gap-3 h-10 px-4 rounded"
          style={{
            background: "var(--c-surface-1)",
            border: "1px solid var(--c-border-hi)",
          }}
        >
          <Search className="h-4 w-4 shrink-0" style={{ color: "var(--t-meta)" }} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Query the regulatory corpus..."
            className="h-full w-full bg-transparent font-data text-[11px] outline-none"
            style={{ color: "var(--t-primary)", caretColor: "var(--c-cyan)" }}
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="font-data text-[9px]"
              style={{ color: "var(--t-meta)" }}
            >
              ✕
            </button>
          )}
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1 rounded font-data text-[9px] uppercase tracking-widest shrink-0 disabled:opacity-40"
            style={{
              border: "1px solid rgba(77,217,245,0.25)",
              color: "var(--c-cyan)",
              background: "var(--c-cyan-ghost)",
            }}
          >
            {loading && <RefreshCw size={9} className="animate-spin" />}
            QUERY
          </button>
        </form>
        {(query || error) && (
          <p className="mt-1 font-data text-[8px] uppercase tracking-widest" style={{ color: error ? "var(--c-critical)" : "var(--t-meta)" }}>
            {error || `${results.length} evidence chunk${results.length !== 1 ? "s" : ""} retrieved`}
          </p>
        )}
      </div>

      {/* ── Main content area ─────────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── AI Grounded Answer Panel — violet accent ───────────────────── */}
        {answer?.answer && (
          <div
            className="w-[340px] shrink-0 flex flex-col overflow-hidden"
            style={{ borderRight: "1px solid var(--c-border)" }}
          >
            <div
              className="px-4 py-2 shrink-0"
              style={{ borderBottom: "1px solid rgba(167,139,250,0.15)", background: "var(--c-ai-ghost)" }}
            >
              <div className="flex items-center gap-2">
                {/* AI indicator dot */}
                <span className="pulse-dot" style={{ background: "var(--c-ai)" }} />
                <span className="ai-label">AI INTERPRETATION</span>
              </div>
              <p className="font-data text-[7px] mt-0.5" style={{ color: "rgba(167,139,250,0.4)" }}>
                REQUIRES REVIEW — LLM-GENERATED
              </p>
            </div>
            <div className="flex-1 overflow-y-auto p-4" style={{ background: "var(--c-ai-ghost)" }}>
              <p className="text-[11px] leading-relaxed" style={{ color: "var(--c-ai-dim)" }}>
                {answer.answer}
              </p>
            </div>
          </div>
        )}

        {/* ── Results list ──────────────────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto p-5">
          <AnimatePresence mode="wait">
            {results.length > 0 ? (
              <motion.div
                key="results"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col gap-3"
              >
                {results.map((reg, i) => (
                  <RegulationCard key={`${reg.source || "reg"}-${reg.document || i}-${i}`} reg={reg} index={i} />
                ))}
              </motion.div>
            ) : (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center justify-center h-full py-32"
              >
                <SearchX size={24} style={{ color: "var(--t-meta)" }} className="mb-3" />
                <span className="label">NO REGULATIONS RETRIEVED</span>
                <p className="mt-1 font-data text-[10px]" style={{ color: "var(--t-meta)" }}>
                  Confirm Qdrant vector store is online
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
