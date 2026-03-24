"use client";

import { ThemeProvider } from "next-themes";
import { Toaster } from "sonner";
import { ErrorBoundary } from "@/components/layout/ErrorBoundary";
import "./globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <title>AutoClean — Autonomous Data Cleaning & Feature Engineering</title>
        <meta
          name="description"
          content="Enterprise-grade autonomous data cleaning, feature engineering, and baseline model training platform."
        />
      </head>
      <body className="min-h-screen bg-[hsl(var(--background))] font-sans antialiased">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <ErrorBoundary>
            {children}
            <Toaster position="bottom-right" richColors theme="system" />
          </ErrorBoundary>
        </ThemeProvider>
      </body>
    </html>
  );
}
