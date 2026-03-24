"use client";

import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDropzone } from "react-dropzone";
import { toast } from "sonner";
import Header from "@/components/layout/Header";
import {
  uploadDataset,
  listDatasets,
  getDatasetColumns,
  triggerPipeline,
  deleteDataset,
} from "@/lib/api";
import type { Dataset } from "@/lib/types";
import { formatBytes, formatDate } from "@/lib/utils";
import { useRouter } from "next/navigation";
import { useAppStore } from "@/lib/store";

export default function DashboardPage() {
  const router = useRouter();
  
  // Zustand State
  const { 
    datasets, 
    setDatasets, 
    addDataset, 
    removeDataset, 
    selectedDataset, 
    setSelectedDataset 
  } = useAppStore();

  const [uploading, setUploading] = useState(false);
  const [columns, setColumns] = useState<string[]>([]);
  const [targetColumn, setTargetColumn] = useState("");
  const [running, setRunning] = useState(false);

  // Fetch initial datasets
  const fetchDatasets = useCallback(async () => {
    try {
      const data = await listDatasets();
      setDatasets(data);
    } catch (e: any) {
      toast.error("Failed to load datasets", { description: e.message });
    }
  }, [setDatasets]);

  useEffect(() => { fetchDatasets(); }, [fetchDatasets]);

  // Dropzone setup
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    const toastId = toast.loading("Uploading dataset...");
    
    try {
      const ds = await uploadDataset(file);
      addDataset(ds);
      setSelectedDataset(ds);
      
      const cols = await getDatasetColumns(ds.id);
      setColumns(cols);
      setTargetColumn(cols[cols.length - 1] || "");
      
      toast.success("Upload complete!", { 
        id: toastId,
        description: `${ds.original_name} is ready for processing.`
      });
    } catch (e: any) {
      toast.error("Upload failed", { 
        id: toastId,
        description: e.message || "An unknown error occurred" 
      });
    } finally {
      setUploading(false);
    }
  }, [addDataset, setSelectedDataset]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.apache.parquet": [".parquet"]
    },
    maxSize: 200 * 1024 * 1024, // 200MB
    multiple: false
  });

  const handleSelect = async (ds: Dataset) => {
    setSelectedDataset(ds);
    try {
      const cols = await getDatasetColumns(ds.id);
      setColumns(cols);
      setTargetColumn(cols[cols.length - 1] || "");
    } catch (e: any) {
      toast.error("Failed to fetch columns", { description: e.message });
    }
  };

  const handleRunPipeline = async () => {
    if (!selectedDataset || !targetColumn) return;
    setRunning(true);
    const toastId = toast.loading("Launching autonomous pipeline...");
    
    try {
      const run = await triggerPipeline(selectedDataset.id, targetColumn);
      toast.success("Pipeline running", { id: toastId });
      router.push(`/pipeline/${run.id}`);
    } catch (e: any) {
      toast.error("Pipeline failed to start", { 
        id: toastId,
        description: e.message 
      });
      setRunning(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    try {
      await deleteDataset(id);
      removeDataset(id);
      if (selectedDataset?.id === id) setColumns([]);
      toast.success("Dataset deleted", { description: name });
    } catch (e: any) {
      toast.error("Failed to delete", { description: e.message });
    }
  };

  return (
    <div className="min-h-screen">
      <Header />

      {/* Hero section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-600/20 via-transparent to-purple-600/10" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 h-[500px] w-[800px] rounded-full bg-brand-500/10 blur-[120px]" />

        <div className="relative mx-auto max-w-7xl px-6 py-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <h1 className="text-5xl font-extrabold tracking-tight md:text-6xl">
              <span className="gradient-text">Autonomous</span>{" "}
              <span className="text-[hsl(var(--foreground))]">Data Pipeline</span>
            </h1>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-[hsl(var(--muted-foreground))]">
              Upload your dataset, select a target, and let AI clean, engineer features,
              and train a baseline model — all in one click.
            </p>
          </motion.div>

          {/* Upload Zone */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mx-auto mt-10 max-w-2xl"
          >
            <div
              {...getRootProps()}
              className={`relative rounded-2xl border-2 border-dashed p-12 text-center transition-all duration-300 cursor-pointer ${
                isDragReject
                  ? "border-red-500 bg-red-500/10 scale-[1.02]"
                  : isDragActive
                  ? "border-brand-400 bg-brand-500/10 scale-[1.02]"
                  : "border-[hsl(var(--border))] hover:border-brand-400/50 hover:bg-brand-500/5"
              }`}
            >
              <input {...getInputProps()} />
              {uploading ? (
                <div className="flex flex-col items-center gap-3">
                  <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-400 border-t-transparent" />
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">Processing upload…</p>
                </div>
              ) : (
                <>
                  <div className={`mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl ${isDragReject ? 'bg-red-500/10' : 'bg-brand-500/10'}`}>
                    <svg className={`h-7 w-7 ${isDragReject ? 'text-red-400' : 'text-brand-400'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                    </svg>
                  </div>
                  <p className="text-base font-medium text-[hsl(var(--foreground))]">
                    {isDragReject ? "File type not supported" : isDragActive ? "Drop to upload" : "Drop your dataset here, or click to browse"}
                  </p>
                  <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                    CSV or Parquet • Max 200MB
                  </p>
                </>
              )}
            </div>
          </motion.div>
        </div>
      </div>

      {/* Configuration + Dataset list */}
      <div className="mx-auto max-w-7xl px-6 pb-20">
        <div className="grid gap-8 lg:grid-cols-5">
          {/* Dataset List */}
          <div className="lg:col-span-3">
            <h2 className="mb-4 text-lg font-semibold text-[hsl(var(--foreground))]">
              Uploaded Datasets
            </h2>
            {datasets.length === 0 ? (
              <div className="rounded-2xl border border-[hsl(var(--border))] p-8 text-center text-[hsl(var(--muted-foreground))]">
                No datasets yet. Upload one above to get started.
              </div>
            ) : (
              <div className="space-y-3">
                <AnimatePresence>
                  {datasets.map((ds, i) => (
                    <motion.div
                      key={ds.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ delay: Math.min(i * 0.05, 0.5) }}
                      onClick={() => handleSelect(ds)}
                      className={`cursor-pointer rounded-2xl border p-4 transition-all duration-200 hover:shadow-lg ${
                        selectedDataset?.id === ds.id
                          ? "border-brand-400 bg-brand-500/5 shadow-lg shadow-brand-500/10"
                          : "border-[hsl(var(--border))] hover:border-brand-400/30"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-[hsl(var(--foreground))]">
                            {ds.original_name}
                          </p>
                          <div className="mt-1 flex items-center gap-3 text-xs text-[hsl(var(--muted-foreground))]">
                            <span>{formatBytes(ds.file_size_bytes)}</span>
                            <span>•</span>
                            <span>{ds.row_count?.toLocaleString()} rows</span>
                            <span>•</span>
                            <span>{ds.column_count} cols</span>
                            <span>•</span>
                            <span>{formatDate(ds.created_at)}</span>
                          </div>
                        </div>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDelete(ds.id, ds.original_name); }}
                          className="rounded-lg p-2 text-[hsl(var(--muted-foreground))] hover:bg-red-500/10 hover:text-red-400 transition-colors"
                          aria-label={`Delete ${ds.original_name}`}
                        >
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )}
          </div>

          {/* Pipeline Config */}
          <div className="lg:col-span-2">
            <h2 className="mb-4 text-lg font-semibold text-[hsl(var(--foreground))]">
              Pipeline Configuration
            </h2>
            <div className="rounded-2xl border border-[hsl(var(--border))] p-6 space-y-5 relative overflow-hidden">
              {selectedDataset ? (
                <>
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                    <p className="text-xs font-medium uppercase tracking-wider text-[hsl(var(--muted-foreground))]">
                      Selected Dataset
                    </p>
                    <p className="mt-1 font-semibold text-[hsl(var(--foreground))] truncate">
                      {selectedDataset.original_name}
                    </p>
                  </motion.div>

                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
                    <label className="text-xs font-medium uppercase tracking-wider text-[hsl(var(--muted-foreground))]">
                      Target Variable
                    </label>
                    <select
                      value={targetColumn}
                      onChange={(e) => setTargetColumn(e.target.value)}
                      className="mt-2 w-full rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] px-4 py-2.5 text-sm text-[hsl(var(--foreground))] focus:border-brand-400 focus:outline-none focus:ring-1 focus:ring-brand-400 transition-shadow"
                    >
                      <option value="" disabled>Select target column</option>
                      {columns.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </motion.div>

                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
                    <button
                      onClick={handleRunPipeline}
                      disabled={running || !targetColumn}
                      className="w-full rounded-xl gradient-brand py-3 font-semibold text-white shadow-lg shadow-brand-500/25 transition-all duration-300 hover:shadow-xl hover:shadow-brand-500/30 hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
                    >
                      {running ? (
                        <span className="flex items-center justify-center gap-2">
                          <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                          Launching…
                        </span>
                      ) : (
                        "🚀 Run Autonomous Pipeline"
                      )}
                    </button>
                  </motion.div>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center py-8 opacity-60">
                  <svg className="h-12 w-12 text-[hsl(var(--muted-foreground))] mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <p className="text-sm text-[hsl(var(--muted-foreground))] text-center">
                    Select a dataset from the left<br/>to begin configuring the pipeline.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
