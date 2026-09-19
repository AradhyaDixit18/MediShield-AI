import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  UploadCloud, FileText, Loader2, AlertTriangle, CheckCircle2,
  Info, ArrowRight, ScanLine,
} from "lucide-react";
import { analyzeReport, type ReportResult, type MarkerResult } from "../lib/api";
import { DISEASE_META } from "../lib/ui";

function statusStyle(status: string) {
  if (status === "High") return { chip: "bg-rose-500/15 text-rose-300", bar: "bg-rose-400", dot: "bg-rose-400" };
  if (status === "Low") return { chip: "bg-amber-500/15 text-amber-300", bar: "bg-amber-400", dot: "bg-amber-400" };
  return { chip: "bg-emerald-500/15 text-emerald-300", bar: "bg-emerald-400", dot: "bg-emerald-400" };
}

// position of the value inside the reference range, clamped 0–100
function valuePosition(m: MarkerResult): number {
  const span = m.ref_high - m.ref_low || 1;
  const lo = m.ref_low - span * 0.4;
  const hi = m.ref_high + span * 0.4;
  return Math.min(100, Math.max(0, ((m.value - lo) / (hi - lo)) * 100));
}

export default function Report() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ReportResult | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function pick(f: File | null) {
    setError(null);
    if (!f) return;
    const ok = /\.(pdf|png|jpe?g|webp|bmp|tiff?)$/i.test(f.name);
    if (!ok) { setError("Please upload a PDF or an image (PNG/JPG)."); return; }
    if (f.size > 10 * 1024 * 1024) { setError("File is larger than 10 MB."); return; }
    setFile(f);
    setResult(null);
  }

  async function run() {
    if (!file) return;
    setLoading(true); setError(null);
    try {
      const r = await analyzeReport(file);
      setResult(r);
      setTimeout(() => document.getElementById("report-result")?.scrollIntoView({ behavior: "smooth" }), 100);
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || "Could not analyze this file. Try a clearer PDF or image.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-5 py-12">
      <span className="eyebrow">Report intelligence</span>
      <h1 className="mt-2 font-display text-4xl font-bold text-white">Analyze a medical report</h1>
      <p className="mt-2 max-w-2xl text-slate-400">
        Upload a lab or blood-test report as a PDF or image. MediShield AI reads the values, compares each
        against standard reference ranges, and explains what they mean in plain language.
      </p>

      {/* Upload */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); pick(e.dataTransfer.files?.[0] ?? null); }}
        className={`glass mt-8 flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-10 text-center transition
          ${dragging ? "border-brand-500/70 bg-brand-500/5" : "border-white/10"}`}
      >
        <input ref={inputRef} type="file" accept=".pdf,image/*" className="hidden"
          onChange={(e) => pick(e.target.files?.[0] ?? null)} />
        <div className="mb-4 grid h-16 w-16 place-items-center rounded-2xl bg-brand-500/10 text-brand-400 ring-1 ring-brand-500/20">
          {file ? <FileText size={28} /> : <UploadCloud size={28} />}
        </div>
        {file ? (
          <div>
            <p className="font-medium text-white">{file.name}</p>
            <p className="mt-1 text-xs text-slate-500">{(file.size / 1024).toFixed(0)} KB · ready to analyze</p>
          </div>
        ) : (
          <div>
            <p className="font-medium text-white">Drop your report here, or click to browse</p>
            <p className="mt-1 text-sm text-slate-500">PDF or image · up to 10 MB · processed only to generate your report</p>
          </div>
        )}
        <div className="mt-5 flex gap-3">
          <button onClick={() => inputRef.current?.click()} className="btn-ghost">Choose file</button>
          <button onClick={run} disabled={!file || loading} className="btn-primary">
            {loading ? <><Loader2 size={18} className="animate-spin" /> Analyzing…</> : <><ScanLine size={18} /> Analyze report</>}
          </button>
        </div>
        {error && (
          <p className="mt-4 flex items-center gap-2 text-sm text-amber-300"><AlertTriangle size={16} /> {error}</p>
        )}
      </div>

      {/* Result */}
      {result && (
        <motion.div id="report-result" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="mt-10 space-y-6">
          {/* Summary */}
          <div className="glass p-6 sm:p-7">
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 rounded-full bg-white/5 px-3 py-1 text-sm">
                <FileText size={14} className="text-slate-400" />
                {result.counts.total} values read
                <span className="text-slate-500">· {result.method === "pdf-text" ? "from PDF text" : result.method.includes("ocr") ? "via OCR" : result.method}</span>
              </div>
              <div className="flex items-center gap-2 rounded-full bg-rose-500/15 px-3 py-1 text-sm text-rose-300">
                <AlertTriangle size={14} /> {result.counts.abnormal} outside range
              </div>
              <div className="flex items-center gap-2 rounded-full bg-emerald-500/15 px-3 py-1 text-sm text-emerald-300">
                <CheckCircle2 size={14} /> {result.counts.normal} normal
              </div>
            </div>
            <p className="mt-4 leading-relaxed text-slate-300">{result.summary}</p>

            {result.related_assessments.length > 0 && (
              <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-white/5 pt-5">
                <span className="text-sm text-slate-400">Related risk assessments:</span>
                {result.related_assessments.map((id) => (
                  <Link key={id} to={`/assess/${id}`}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-sm text-brand-300 transition hover:border-brand-500/40">
                    {DISEASE_META[id]?.label ?? id} <ArrowRight size={14} />
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Flagged */}
          {result.flagged.length > 0 && (
            <div>
              <h2 className="mb-4 font-display text-xl font-semibold text-white">Flagged for attention</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                {result.flagged.map((m, i) => {
                  const s = statusStyle(m.status);
                  return (
                    <motion.div key={m.key} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                      className="glass p-5">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold text-white">{m.name}</h3>
                          <p className="text-xs text-slate-500">{m.category}</p>
                        </div>
                        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${s.chip}`}>{m.status}</span>
                      </div>
                      <div className="mt-3 flex items-baseline gap-2">
                        <span className="font-display text-2xl font-bold text-white">{m.value}</span>
                        <span className="text-sm text-slate-400">{m.unit}</span>
                        <span className="ml-auto text-xs text-slate-500">normal {m.ref_low}–{m.ref_high}</span>
                      </div>
                      <div className="relative mt-2 h-1.5 w-full rounded-full bg-white/10">
                        <div className="absolute inset-y-0 rounded-full bg-emerald-500/25"
                          style={{ left: "28%", right: "28%" }} />
                        <div className={`absolute top-1/2 h-3 w-3 -translate-y-1/2 rounded-full ${s.dot} ring-2 ring-ink-900`}
                          style={{ left: `calc(${valuePosition(m)}% - 6px)` }} />
                      </div>
                      <p className="mt-3 text-sm text-slate-400">{m.about}</p>
                      {m.note && <p className="mt-2 text-sm text-slate-300">{m.note}</p>}
                      {m.advice && (
                        <p className="mt-3 rounded-lg bg-white/[0.03] p-3 text-sm text-slate-300">
                          <span className="font-medium text-brand-300">What helps: </span>{m.advice}
                        </p>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Full results by category */}
          {result.categories.length > 0 && (
            <div>
              <h2 className="mb-4 font-display text-xl font-semibold text-white">All detected values</h2>
              <div className="space-y-4">
                {result.categories.map((cat) => (
                  <div key={cat.name} className="glass overflow-hidden">
                    <div className="border-b border-white/5 px-5 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
                      {cat.name}
                    </div>
                    {cat.markers.map((m) => {
                      const s = statusStyle(m.status);
                      return (
                        <div key={m.key} className="grid grid-cols-[1fr_auto_auto] items-center gap-4 border-b border-white/5 px-5 py-3 text-sm last:border-0">
                          <span className="flex items-center gap-2 text-slate-200"><span className={`h-2 w-2 rounded-full ${s.dot}`} />{m.name}</span>
                          <span className="tabular-nums text-slate-300">{m.value} <span className="text-slate-500">{m.unit}</span></span>
                          <span className={`w-16 rounded-full px-2 py-0.5 text-center text-xs font-semibold ${s.chip}`}>{m.status}</span>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          )}

          <p className="flex items-start gap-2 px-1 text-xs text-slate-500">
            <Info size={14} className="mt-0.5 shrink-0" /> {result.disclaimer}
          </p>
        </motion.div>
      )}
    </div>
  );
}
