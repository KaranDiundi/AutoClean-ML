"use client";

import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import Header from "@/components/layout/Header";
import { AuditLogTable } from "@/components/pipeline/AuditLogTable";
import { createStatusStream, getPipelineResults, getDownloadUrl } from "@/lib/api";
import type { PipelineResults, PipelineStatus } from "@/lib/types";
import { useParams } from "next/navigation";

const STEPS: { key: PipelineStatus; label: string; icon: string }[] = [
  { key: "PENDING", label: "Queued", icon: "⏳" },
  { key: "PROFILING", label: "Profiling", icon: "🔍" },
  { key: "CLEANING", label: "Cleaning", icon: "🧹" },
  { key: "ENGINEERING", label: "Engineering", icon: "⚙️" },
  { key: "TRAINING", label: "Training", icon: "🤖" },
  { key: "COMPLETED", label: "Completed", icon: "✅" },
];

const CHART_COLORS = [
  "#667eea", "#764ba2", "#6366f1", "#818cf8", "#a5b4fc",
  "#4f46e5", "#7c3aed", "#8b5cf6", "#c084fc", "#6d28d9",
];

export default function PipelineResultsPage() {
  const params = useParams();
  const runId = params.id as string;
  const [status, setStatus] = useState<PipelineStatus>("PENDING");
  const [results, setResults] = useState<PipelineResults | null>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!runId) return;

    const es = createStatusStream(runId);
    esRef.current = es;

    es.addEventListener("status", (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        setStatus(data.status);
        
        if (data.error_message) {
          toast.error("Pipeline Error", { description: data.error_message });
        }

        if (data.status === "COMPLETED" || data.status === "FAILED") {
          es.close();
          if (data.status === "COMPLETED") {
            toast.success("Pipeline Completed!");
            getPipelineResults(runId).then(setResults).catch(console.error);
          }
        }
      } catch { /* empty */ }
    });

    es.addEventListener("error", () => {
      // SSE connection closed — try to fetch results anyway
      es.close();
      getPipelineResults(runId).then((r) => {
        setResults(r);
        setStatus(r.run.status as PipelineStatus);
        if (r.run.error_message) {
          toast.error("Pipeline Error", { description: r.run.error_message });
        }
      }).catch(console.error);
    });

    return () => es.close();
  }, [runId]);

  const activeStepIndex = STEPS.findIndex((s) => s.key === status);
  const isRunning = !["COMPLETED", "FAILED"].includes(status);
  const profile = results?.profile;
  const model = results?.model_result;
  const auditLogs = results?.audit_logs || [];

  return (
    <div className="min-h-screen">
      <Header />

      <div className="mx-auto max-w-7xl px-6 py-10">
        {/* Pipeline Stepper */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10"
        >
          <h1 className="text-3xl font-bold text-[hsl(var(--foreground))]">Pipeline Progress</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">Run ID: {runId}</p>

          <div className="mt-8 flex items-center justify-between">
            {STEPS.map((step, i) => {
              const isActive = i === activeStepIndex;
              const isDone = i < activeStepIndex || status === "COMPLETED";
              const isFailed = status === "FAILED" && i === activeStepIndex;

              return (
                <div key={step.key} className="flex flex-1 items-center">
                  <div className="flex flex-col items-center flex-1">
                    <div
                      className={`flex h-12 w-12 items-center justify-center rounded-2xl text-lg transition-all duration-500 ${
                        isDone
                          ? "bg-emerald-500/20 text-emerald-400 scale-100"
                          : isActive
                          ? "gradient-brand text-white scale-110 shadow-lg shadow-brand-500/30 animate-pulse-slow"
                          : isFailed
                          ? "bg-red-500/20 text-red-400"
                          : "bg-[hsl(var(--muted))] text-[hsl(var(--muted-foreground))]"
                      }`}
                    >
                      {isDone ? "✓" : step.icon}
                    </div>
                    <span
                      className={`mt-2 text-xs font-medium ${
                        isDone || isActive
                          ? "text-[hsl(var(--foreground))]"
                          : "text-[hsl(var(--muted-foreground))]"
                      }`}
                    >
                      {step.label}
                    </span>
                  </div>
                  {i < STEPS.length - 1 && (
                    <div className={`h-0.5 flex-1 mx-2 rounded transition-colors duration-500 ${
                      isDone ? "bg-emerald-500/50" : "bg-[hsl(var(--border))]"
                    }`} />
                  )}
                </div>
              );
            })}
          </div>

          {isRunning && (
            <div className="mt-6 flex items-center justify-center gap-3 text-[hsl(var(--muted-foreground))]">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-brand-400 border-t-transparent" />
              <span className="text-sm">Processing your data…</span>
            </div>
          )}
        </motion.div>

        {/* Results Grid */}
        {results && status === "COMPLETED" && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="space-y-8"
          >
            {/* Metric Cards */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {profile && (
                <>
                  <div className="metric-card">
                    <p className="text-xs font-medium uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Rows</p>
                    <p className="mt-1 text-2xl font-bold text-[hsl(var(--foreground))]">{profile.n_rows.toLocaleString()}</p>
                  </div>
                  <div className="metric-card">
                    <p className="text-xs font-medium uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Columns</p>
                    <p className="mt-1 text-2xl font-bold text-[hsl(var(--foreground))]">{profile.n_cols}</p>
                  </div>
                  <div className="metric-card">
                    <p className="text-xs font-medium uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Missing %</p>
                    <p className="mt-1 text-2xl font-bold text-[hsl(var(--foreground))]">{profile.total_missing_pct}%</p>
                  </div>
                </>
              )}
              {model && (
                <div className="metric-card">
                  <p className="text-xs font-medium uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Task Type</p>
                  <p className="mt-1 text-2xl font-bold capitalize gradient-text">{model.task_type}</p>
                </div>
              )}
            </div>

            {/* Model Metrics */}
            {model && (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {Object.entries(model.metrics)
                  .filter(([k]) => k !== "confusion_matrix")
                  .map(([key, val]) => (
                    <div key={key} className="metric-card">
                      <p className="text-xs font-medium uppercase tracking-wider text-[hsl(var(--muted-foreground))]">
                        {key.replace(/_/g, " ")}
                      </p>
                      <p className="mt-1 text-3xl font-bold gradient-text">
                        {typeof val === "number" ? val.toFixed(4) : String(val)}
                      </p>
                    </div>
                  ))}
              </div>
            )}

            {/* Feature Importances Chart */}
            {model && model.feature_importances.length > 0 && (
              <div className="rounded-2xl border border-[hsl(var(--border))] p-6">
                <h3 className="mb-4 text-lg font-semibold text-[hsl(var(--foreground))]">
                  📈 Feature Importances
                </h3>
                <div className="h-[400px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={model.feature_importances.slice(0, 15)}
                      layout="vertical"
                      margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
                    >
                      <XAxis type="number" stroke="hsl(215, 20%, 65%)" fontSize={12} />
                      <YAxis
                        dataKey="feature"
                        type="category"
                        width={90}
                        stroke="hsl(215, 20%, 65%)"
                        fontSize={11}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "hsl(222, 47%, 8%)",
                          border: "1px solid hsl(216, 34%, 17%)",
                          borderRadius: "12px",
                          color: "#fff",
                          fontSize: "12px",
                        }}
                      />
                      <Bar dataKey="importance" radius={[0, 6, 6, 0]}>
                        {model.feature_importances.slice(0, 15).map((_, i) => (
                          <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Confusion Matrix */}
            {model && model.metrics.confusion_matrix && (
              <div className="rounded-2xl border border-[hsl(var(--border))] p-6">
                <h3 className="mb-4 text-lg font-semibold text-[hsl(var(--foreground))]">
                  Confusion Matrix
                </h3>
                <div className="overflow-x-auto">
                  <table className="mx-auto">
                    <tbody>
                      {(model.metrics.confusion_matrix as number[][]).map((row, i) => (
                        <tr key={i}>
                          {row.map((val, j) => {
                            const max = Math.max(...(model.metrics.confusion_matrix as number[][]).flat());
                            const opacity = max > 0 ? val / max : 0;
                            return (
                              <td
                                key={j}
                                className="h-16 w-16 text-center text-sm font-bold rounded-lg m-0.5"
                                style={{
                                  background: `rgba(99, 102, 241, ${opacity * 0.7 + 0.05})`,
                                  color: opacity > 0.5 ? "white" : "hsl(215, 20%, 65%)",
                                }}
                              >
                                {val}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Audit Log Data Table */}
            {auditLogs.length > 0 && (
              <div className="rounded-2xl border border-[hsl(var(--border))] p-6 bg-[hsl(var(--background))]">
                <h3 className="mb-4 text-lg font-semibold text-[hsl(var(--foreground))]">
                  📝 Transformation Audit Log
                </h3>
                <AuditLogTable data={auditLogs} />
              </div>
            )}

            {/* Download */}
            <div className="flex justify-center">
              <a
                href={getDownloadUrl(runId)}
                className="inline-flex items-center gap-2 rounded-xl gradient-brand px-8 py-3.5 font-semibold text-white shadow-lg shadow-brand-500/25 transition-all duration-300 hover:shadow-xl hover:shadow-brand-500/30 hover:scale-[1.02]"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download Processed Dataset
              </a>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
