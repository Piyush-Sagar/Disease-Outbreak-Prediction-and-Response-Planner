import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { DisclaimerBadge } from "@/components/ui";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Disease Outbreak Prediction & Response Planner",
  description:
    "AI-based dengue outbreak prediction and response planning (academic prototype ).",
};

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/regions", label: "Regions" },
  { href: "/predictions", label: "Predictions" },
  { href: "/response", label: "Response Plan" },
  { href: "/routes", label: "Response Routes" },
  { href: "/model", label: "Model" },
  { href: "/data", label: "Data" },
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-slate-100">
        <div className="flex min-h-screen">
          <aside className="flex w-60 shrink-0 flex-col border-r border-slate-800 bg-slate-900 text-slate-100">
            <div className="border-b border-slate-800 px-5 py-5">
              <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-400">
                AI-Based System
              </p>
              <h1 className="mt-1 text-sm font-bold leading-snug text-white">
                Disease Outbreak Prediction &amp; Response Planner
              </h1>
              <p className="mt-2 text-xs text-slate-400">Dengue risk · India (demo)</p>
            </div>
            <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
              {NAV.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center rounded-lg px-3 py-2 text-sm font-medium text-slate-300 transition hover:bg-slate-800 hover:text-white"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
            <div className="border-t border-slate-800 px-5 py-4">
              <DisclaimerBadge />
              <p className="mt-2 text-[10px] leading-relaxed text-slate-500">
                Academic prototype. Not for real-world healthcare decisions.
              </p>
            </div>
          </aside>
          <main className="flex flex-1 flex-col">
            <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
              <p className="text-sm text-slate-600">
                AI-Based Disease Outbreak Prediction and Response Planner{" "}
                <span className="text-slate-400">· v1.0.0</span>
              </p>
              <p className="text-xs text-slate-500">Prediction horizon: 1 week ahead · Random Forest + Logistic Regression</p>
            </header>
            <div className="flex-1 p-6">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}