"use client";

import { ErrorBoundary as ReactErrorBoundary, FallbackProps } from "react-error-boundary";
import { motion } from "framer-motion";

function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex min-h-[400px] flex-col items-center justify-center rounded-2xl border border-red-500/20 bg-red-500/5 p-8 text-center"
    >
      <div className="mb-4 rounded-full bg-red-500/20 p-3 text-red-400">
        <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <h2 className="text-xl font-bold text-[hsl(var(--foreground))]">Something went wrong</h2>
      <p className="mt-2 text-sm text-[hsl(var(--muted-foreground))]">
        An unexpected UI error occurred. Our robust error boundary caught it gracefully.
      </p>
      <pre className="mt-4 max-w-lg overflow-auto rounded text-left text-xs text-red-400">
        {error.message}
      </pre>
      <button
        onClick={resetErrorBoundary}
        className="mt-6 rounded-xl bg-[hsl(var(--foreground))] px-6 py-2.5 text-sm font-semibold text-[hsl(var(--background))] transition-transform hover:scale-105"
      >
        Try again
      </button>
    </motion.div>
  );
}

export function ErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ReactErrorBoundary FallbackComponent={ErrorFallback}>
      {children}
    </ReactErrorBoundary>
  );
}
