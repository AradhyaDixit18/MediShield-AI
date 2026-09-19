import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Loader2, Sparkles, Info, ShieldAlert, RotateCcw } from "lucide-react";
import { getSchema, predict, type DiseaseSchema, type Field, type PredictResult } from "../lib/api";
import { DISEASE_META, severityStyle, saveHistory } from "../lib/ui";
import RiskGauge from "../components/RiskGauge";
import FactorChart from "../components/FactorChart";

function defaultsOf(fields: Field[]): Record<string, string | number> {
  const o: Record<string, string | number> = {};
  fields.forEach((f) => { o[f.name] = f.default ?? (f.type === "number" ? f.min ?? 0 : ""); });
  return o;
}

export default function Assess() {
  const { disease = "" } = useParams();
  const meta = DISEASE_META[disease];
  const [schema, setSchema] = useState<DiseaseSchema | null>(null);
  const [values, setValues] = useState<Record<string, string | number>>({});
  const [result, setResult] = useState<PredictResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSchema(null); setResult(null); setError(null);
    getSchema(disease)
      .then((s) => { setSchema(s); setValues(defaultsOf(s.fields)); })
      .catch(() => setError("Could not load this assessment. Is the backend running?"));
  }, [disease]);

  const set = (name: string, v: string | number) => setValues((prev) => ({ ...prev, [name]: v }));
  const reset = () => { if (schema) { setValues(defaultsOf(schema.fields)); setResult(null); } };

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true); setError(null);
    try {
      const r = await predict(disease, values);
      setResult(r);
      saveHistory(r);
      setTimeout(() => document.getElementById("result")?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    } catch {
      setError("Prediction failed. Please check the backend connection.");
    } finally {
      setLoading(false);
    }
  }

  const grouped = useMemo(() => {
    if (!result) return { high: [], medium: [], info: [] as PredictResult["recommendations"] };
    return {
      high: result.recommendations.filter((r) => r.severity === "high"),
      medium: result.recommendations.filter((r) => r.severity === "medium"),
      info: result.recommendations.filter((r) => r.severity === "info"),
    };
  }, [result]);

  if (!meta) return <div className="mx-auto max-w-6xl px-5 py-20 text-slate-400">Unknown assessment.</div>;

  return (
    <div className="mx-auto max-w-6xl px-5 py-12">
      <Link to="/" className="mb-6 inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white">
        <ArrowLeft size={16} /> Back
      </Link>

      <div className="mb-8 flex items-end justify-between gap-4">
        <div>
          <span className="eyebrow" style={{ color: meta.accent }}>{meta.label} assessment</span>
          <h1 className="mt-2 font-display text-4xl font-bold text-white">{schema?.title ?? meta.label}</h1>
          <p className="mt-2 max-w-2xl text-slate-400">{meta.blurb}</p>
        </div>
        {schema && (
          <div className="hidden shrink-0 text-right sm:block">
            <div className="text-xs uppercase tracking-widest text-slate-500">Model ROC-AUC</div>
            <div className="font-display text-3xl font-bold" style={{ color: meta.accent }}>{schema.metrics.roc_auc}</div>
          </div>
        )}
      </div>

      {error && (
        <div className="glass mb-6 flex items-center gap-2 rounded-xl p-4 text-sm text-amber-300">
          <ShieldAlert size={18} /> {error}
        </div>
      )}

      <div className="grid gap-8 lg:grid-cols-[1fr_1fr]">
        {/* Form */}
        <form onSubmit={onSubmit} className="glass h-fit p-6 sm:p-7">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="font-display text-lg font-semibold text-white">Your indicators</h2>
            <button type="button" onClick={reset} className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white">
              <RotateCcw size={13} /> Reset
            </button>
          </div>

          {!schema ? (
            <div className="flex h-64 items-center justify-center text-slate-500">
              <Loader2 className="animate-spin" />
            </div>
          ) : (
            <div className="grid gap-5 sm:grid-cols-2">
              {schema.fields.map((f) => (
                <FieldInput key={f.name} field={f} value={values[f.name]} onChange={(v) => set(f.name, v)} accent={meta.accent} />
              ))}
            </div>
          )}

          <button type="submit" disabled={loading || !schema} className="btn-primary mt-7 w-full">
            {loading ? <><Loader2 size={18} className="animate-spin" /> Analyzing…</> : <><Sparkles size={18} /> Analyze risk</>}
          </button>
        </form>

        {/* Result */}
        <div id="result">
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                key="res" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                className="space-y-6"
              >
                <div className="glass flex flex-col items-center p-7">
                  <RiskGauge percent={result.risk_percent} band={result.band} timesAverage={result.times_average} />
                  <p className="mt-5 text-center text-sm text-slate-400">
                    Estimated probability of <span className="text-slate-200">{result.positive_label.toLowerCase()}</span>,
                    based on the values you entered.
                  </p>
                </div>

                <div className="glass p-6 sm:p-7">
                  <div className="mb-4 flex items-center gap-2">
                    <h3 className="font-display text-lg font-semibold text-white">Why this result</h3>
                    <span className="rounded-md bg-white/5 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-brand-300">SHAP</span>
                  </div>
                  <FactorChart factors={result.top_factors} />
                </div>

                <div className="glass p-6 sm:p-7">
                  <h3 className="mb-4 font-display text-lg font-semibold text-white">Preventive recommendations</h3>
                  <div className="space-y-4">
                    {(["high", "medium", "info"] as const).flatMap((sev) =>
                      grouped[sev].map((r, i) => {
                        const s = severityStyle(r.severity);
                        return (
                          <div key={`${sev}-${i}`} className="flex gap-3 rounded-xl border border-white/5 bg-white/[0.02] p-4">
                            <span className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${s.dot}`} />
                            <div>
                              <div className="flex items-center gap-2">
                                <span className={`text-xs font-semibold uppercase tracking-wide ${s.label}`}>{r.category}</span>
                              </div>
                              <h4 className="mt-0.5 font-medium text-white">{r.title}</h4>
                              <p className="mt-1 text-sm text-slate-400">{r.detail}</p>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>

                <p className="flex items-start gap-2 px-1 text-xs text-slate-500">
                  <Info size={14} className="mt-0.5 shrink-0" /> {result.disclaimer}
                </p>
              </motion.div>
            ) : (
              <motion.div
                key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="glass flex h-full min-h-[360px] flex-col items-center justify-center p-8 text-center"
              >
                <div className="mb-4 grid h-16 w-16 place-items-center rounded-2xl bg-white/5 text-slate-500">
                  <Sparkles size={28} />
                </div>
                <h3 className="font-display text-lg font-semibold text-white">Your result will appear here</h3>
                <p className="mt-2 max-w-xs text-sm text-slate-400">
                  Fill in the indicators and hit <span className="text-brand-400">Analyze risk</span> to see your
                  explained risk score.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

function FieldInput({ field, value, onChange, accent }: {
  field: Field; value: string | number; onChange: (v: string | number) => void; accent: string;
}) {
  const label = (
    <label className="mb-1.5 flex items-center gap-1.5 text-sm font-medium text-slate-300">
      {field.label}
      {field.unit && <span className="text-xs text-slate-500">({field.unit})</span>}
      {field.help && (
        <span className="group relative">
          <Info size={12} className="text-slate-500" />
          <span className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-1 hidden w-48 -translate-x-1/2 rounded-lg bg-ink-700 p-2 text-xs text-slate-200 shadow-card group-hover:block">
            {field.help}
          </span>
        </span>
      )}
    </label>
  );

  if (field.type === "toggle") {
    const on = String(value) === "1";
    return (
      <div className="sm:col-span-1">
        {label}
        <button
          type="button" onClick={() => onChange(on ? 0 : 1)}
          className={`flex w-full items-center justify-between rounded-xl border px-4 py-2.5 transition ${on ? "border-brand-500/50 bg-brand-500/10 text-white" : "border-white/10 bg-ink-850 text-slate-400"}`}
        >
          <span className="text-sm">{on ? "Yes" : "No"}</span>
          <span className={`relative h-5 w-9 rounded-full transition ${on ? "bg-brand-500" : "bg-white/15"}`}>
            <span className={`absolute top-0.5 h-4 w-4 rounded-full bg-white transition-all ${on ? "left-[1.15rem]" : "left-0.5"}`} />
          </span>
        </button>
      </div>
    );
  }

  if (field.type === "select") {
    return (
      <div>
        {label}
        <select className="input-field" value={String(value)} onChange={(e) => {
          const opt = field.options?.find((o) => String(o.value) === e.target.value);
          onChange(opt ? opt.value : e.target.value);
        }}>
          {field.options?.map((o) => (
            <option key={String(o.value)} value={String(o.value)}>{o.label}</option>
          ))}
        </select>
      </div>
    );
  }

  // number with slider
  return (
    <div>
      {label}
      <div className="flex items-center gap-3">
        <input
          type="range" min={field.min} max={field.max} step={field.step}
          value={Number(value)} onChange={(e) => onChange(Number(e.target.value))}
          className="h-1.5 flex-1 cursor-pointer appearance-none rounded-full bg-white/10 accent-brand-500"
          style={{ accentColor: accent }}
        />
        <input
          type="number" min={field.min} max={field.max} step={field.step}
          value={Number(value)} onChange={(e) => onChange(Number(e.target.value))}
          className="input-field w-20 px-2 py-1.5 text-center text-sm"
        />
      </div>
    </div>
  );
}
