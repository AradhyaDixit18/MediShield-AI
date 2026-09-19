import type { PredictResult } from "./api";

export const DISEASE_META: Record<string, { label: string; blurb: string; accent: string; icon: string }> = {
  diabetes: { label: "Diabetes", blurb: "Estimate diabetes risk from clinical and lifestyle indicators.", accent: "#10b981", icon: "droplet" },
  heart: { label: "Heart Disease", blurb: "Assess cardiovascular risk from ECG, blood pressure and lipid factors.", accent: "#f43f5e", icon: "heart" },
  stroke: { label: "Stroke", blurb: "Gauge stroke susceptibility from vascular and demographic factors.", accent: "#38bdf8", icon: "activity" },
  oral: { label: "Oral & Dental", blurb: "Screen your oral-health risk from diet, hygiene, and symptoms.", accent: "#a78bfa", icon: "smile" },
};

export function bandColor(band: string): { text: string; ring: string; hex: string; bg: string } {
  switch (band) {
    case "Below average":
    case "Low":
      return { text: "text-emerald-400", ring: "stroke-emerald-400", hex: "#34d399", bg: "bg-emerald-500/10" };
    case "Moderate":
      return { text: "text-amber-400", ring: "stroke-amber-400", hex: "#fbbf24", bg: "bg-amber-500/10" };
    case "High":
      return { text: "text-orange-400", ring: "stroke-orange-400", hex: "#fb923c", bg: "bg-orange-500/10" };
    default:
      return { text: "text-rose-400", ring: "stroke-rose-400", hex: "#fb7185", bg: "bg-rose-500/10" };
  }
}

export function severityStyle(sev: string): { dot: string; label: string } {
  switch (sev) {
    case "high": return { dot: "bg-rose-400", label: "text-rose-300" };
    case "medium": return { dot: "bg-amber-400", label: "text-amber-300" };
    default: return { dot: "bg-brand-400", label: "text-brand-300" };
  }
}

// ---- Prediction history (localStorage; per-viewer, best-effort) ----
export interface HistoryEntry {
  id: string;
  disease: string;
  title: string;
  risk_percent: number;
  band: string;
  times_average: number;
  at: number;
}

const KEY = "medishield.history.v1";

export function loadHistory(): HistoryEntry[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) || "[]");
  } catch {
    return [];
  }
}

export function saveHistory(result: PredictResult): HistoryEntry[] {
  const entry: HistoryEntry = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    disease: result.disease,
    title: result.title,
    risk_percent: result.risk_percent,
    band: result.band,
    times_average: result.times_average ?? 0,
    at: Date.now(),
  };
  try {
    const next = [entry, ...loadHistory()].slice(0, 50);
    localStorage.setItem(KEY, JSON.stringify(next));
    return next;
  } catch {
    return loadHistory();
  }
}

export function clearHistory() {
  try { localStorage.removeItem(KEY); } catch { /* ignore */ }
}
