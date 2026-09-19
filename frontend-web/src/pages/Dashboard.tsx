import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import { Trash2, Activity, TrendingUp } from "lucide-react";
import { loadHistory, clearHistory, bandColor, DISEASE_META, type HistoryEntry } from "../lib/ui";

export default function Dashboard() {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  useEffect(() => { setHistory(loadHistory()); }, []);

  const chartData = [...history].reverse().map((h, i) => ({
    idx: i + 1,
    risk: h.risk_percent,
    label: `${DISEASE_META[h.disease]?.label ?? h.disease}`,
    when: new Date(h.at).toLocaleDateString(),
  }));

  const avg = history.length ? (history.reduce((s, h) => s + h.risk_percent, 0) / history.length) : 0;

  return (
    <div className="mx-auto max-w-6xl px-5 py-12">
      <div className="mb-8 flex items-end justify-between">
        <div>
          <span className="eyebrow">Health intelligence</span>
          <h1 className="mt-2 font-display text-4xl font-bold text-white">Your dashboard</h1>
          <p className="mt-2 text-slate-400">Every assessment you run is tracked here, on this device.</p>
        </div>
        {history.length > 0 && (
          <button
            onClick={() => { clearHistory(); setHistory([]); }}
            className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-2 text-sm text-slate-400 hover:border-rose-500/40 hover:text-rose-300"
          >
            <Trash2 size={15} /> Clear
          </button>
        )}
      </div>

      {history.length === 0 ? (
        <div className="glass flex min-h-[320px] flex-col items-center justify-center p-10 text-center">
          <div className="mb-4 grid h-16 w-16 place-items-center rounded-2xl bg-white/5 text-slate-500">
            <Activity size={28} />
          </div>
          <h3 className="font-display text-lg font-semibold text-white">No assessments yet</h3>
          <p className="mt-2 max-w-sm text-sm text-slate-400">Run your first risk assessment and it will show up here with trends over time.</p>
          <Link to="/" className="btn-primary mt-6">Start an assessment</Link>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid gap-5 sm:grid-cols-3">
            <Stat label="Assessments run" value={String(history.length)} />
            <Stat label="Average risk score" value={`${avg.toFixed(1)}%`} />
            <Stat label="Latest" value={`${history[0].risk_percent}%`} sub={history[0].band} />
          </div>

          <div className="glass p-6 sm:p-7">
            <div className="mb-5 flex items-center gap-2">
              <TrendingUp size={18} className="text-brand-400" />
              <h3 className="font-display text-lg font-semibold text-white">Risk over time</h3>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 6, right: 6, bottom: 0, left: -18 }}>
                  <defs>
                    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#10b981" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="idx" stroke="#64748b" fontSize={12} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={12} tickLine={false} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{ background: "#0d1526", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12, color: "#e2e8f0" }}
                    formatter={(v) => [`${v}%`, "Risk"]}
                    labelFormatter={(_l, p) => (p?.[0]?.payload ? `${p[0].payload.label} · ${p[0].payload.when}` : "")}
                  />
                  <Area type="monotone" dataKey="risk" stroke="#10b981" strokeWidth={2.5} fill="url(#g)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="glass overflow-hidden">
            <div className="grid grid-cols-[1fr_auto_auto_auto] gap-4 border-b border-white/5 px-6 py-3 text-xs uppercase tracking-wider text-slate-500">
              <span>Assessment</span><span>Risk</span><span>Band</span><span>Date</span>
            </div>
            {history.map((h) => {
              const c = bandColor(h.band);
              return (
                <div key={h.id} className="grid grid-cols-[1fr_auto_auto_auto] items-center gap-4 border-b border-white/5 px-6 py-3.5 text-sm last:border-0">
                  <span className="font-medium text-slate-200">{DISEASE_META[h.disease]?.label ?? h.title}</span>
                  <span className="tabular-nums text-slate-300">{h.risk_percent}%</span>
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${c.bg} ${c.text}`}>{h.band}</span>
                  <span className="text-slate-500">{new Date(h.at).toLocaleDateString()}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="glass p-6">
      <div className="text-xs uppercase tracking-widest text-slate-500">{label}</div>
      <div className="mt-2 font-display text-3xl font-bold text-white">{value}</div>
      {sub && <div className="mt-1 text-sm text-brand-400">{sub}</div>}
    </div>
  );
}
