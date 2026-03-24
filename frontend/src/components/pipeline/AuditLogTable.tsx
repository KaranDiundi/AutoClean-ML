"use client";

import { useState } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  flexRender,
  ColumnDef,
  SortingState,
} from "@tanstack/react-table";
import { motion, AnimatePresence } from "framer-motion";
import type { AuditLogEntry } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const severityBg: Record<string, string> = {
  INFO: "bg-blue-500/10 text-blue-400 border border-blue-500/20",
  ACTION: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
  WARNING: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
};

const phaseColor: Record<string, string> = {
  CLEANING: "text-blue-400",
  ENGINEERING: "text-purple-400",
  MODELING: "text-emerald-400",
};

export function AuditLogTable({ data }: { data: AuditLogEntry[] }) {
  const [sorting, setSorting] = useState<SortingState>([]);
  
  const columns: ColumnDef<AuditLogEntry>[] = [
    {
      accessorKey: "created_at",
      header: "Timestamp",
      cell: ({ row }) => <span className="text-xs font-mono text-[hsl(var(--muted-foreground))]">{formatDate(row.original.created_at)}</span>,
    },
    {
      accessorKey: "severity",
      header: "Severity",
      cell: ({ row }) => (
        <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold tracking-wider ${severityBg[row.original.severity] || ""}`}>
          {row.original.severity}
        </span>
      ),
    },
    {
      accessorKey: "phase",
      header: "Phase",
      cell: ({ row }) => (
        <span className={`text-xs font-semibold ${phaseColor[row.original.phase] || "text-[hsl(var(--muted-foreground))]"}`}>
          {row.original.phase}
        </span>
      ),
    },
    {
      accessorKey: "message",
      header: "Transformation Detail",
      cell: ({ row }) => <span className="text-sm font-medium text-[hsl(var(--foreground))]">{row.original.message}</span>,
    },
  ];

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 15 } },
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-2xl border border-[hsl(var(--border))] overflow-hidden bg-[hsl(var(--card))]">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-[hsl(var(--muted))] text-[hsl(var(--muted-foreground))]">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th 
                      key={header.id} 
                      className="px-6 py-4 font-semibold uppercase tracking-wider text-xs cursor-pointer select-none hover:bg-[hsl(var(--border))]/50 transition-colors"
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      <div className="flex items-center gap-2">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {header.column.getIsSorted() === "asc" ? " ↑" : header.column.getIsSorted() === "desc" ? " ↓" : ""}
                      </div>
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="divide-y divide-[hsl(var(--border))]">
              <AnimatePresence>
                {table.getRowModel().rows.map((row) => (
                  <motion.tr 
                    key={row.id}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="hover:bg-[hsl(var(--muted))]/50 transition-colors"
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-6 py-3">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </motion.tr>
                ))}
              </AnimatePresence>
              {table.getRowModel().rows.length === 0 && (
                <tr>
                  <td colSpan={columns.length} className="px-6 py-8 text-center text-[hsl(var(--muted-foreground))]">
                    No transformation logs available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Pagination Controls */}
      <div className="flex items-center justify-between px-2 text-sm text-[hsl(var(--muted-foreground))]">
        <div>
          Showing <span className="font-semibold text-[hsl(var(--foreground))]">{table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1}</span> to <span className="font-semibold text-[hsl(var(--foreground))]">{Math.min((table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize, data.length)}</span> of <span className="font-semibold text-[hsl(var(--foreground))]">{data.length}</span> logs
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="rounded-lg border border-[hsl(var(--border))] px-3 py-1.5 hover:bg-[hsl(var(--muted))] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Previous
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="rounded-lg border border-[hsl(var(--border))] px-3 py-1.5 hover:bg-[hsl(var(--muted))] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
