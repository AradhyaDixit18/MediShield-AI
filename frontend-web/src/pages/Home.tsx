import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ShieldPlus, Droplet, HeartPulse, Activity, Brain, Sparkles,
  LineChart, Lock, ArrowRight, Stethoscope, FileScan,
} from "lucide-react";
import { getDiseases, type DiseaseSummary } from "../lib/api";
import { DISEASE_META } from "../lib/ui";

const ICONS: Record<string, React.ReactNode> = {
  diabetes: <Droplet size={22} />, heart: <HeartPulse size={22} />, stroke: <Activity size={22} />,
};

const FEATURES = [
  { icon: <Brain size={20} />, title: "Explainable by design", body: "Every prediction ships with SHAP attributions showing exactly which factors drove it, and by how much." },
  { icon: <Sparkles size={20} />, title: "Preventive guidance", body: "Personalized, evidence-informed recommendations mapped to your specific risk drivers." },
  { icon: <LineChart size={20} />, title: "Health dashboard", body: "Track every assessment over time and watch how your risk profile changes." },
  { icon: <Lock size={20} />, title: "Private by default", body: "Assessments run against the model API. Your history stays in your own browser." },
];

export default function Home() {
  const [diseases, setDiseases] = useState<DiseaseSummary[]>([]);
  const [err, setErr] = useState(false);

  useEffect(() => {
    getDiseases().then(setDiseases).catch(() => setErr(true));
  }, []);

  return (
    <div>
      {/* Hero */}
      <section className="relative mx-auto max-w-6xl px-5 pt-20 pb-16">
        <div className="grid items-center gap-12 lg:grid-cols-[1.15fr_0.85fr]">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <span className="eyebrow">Predict · Explain · Prevent</span>
            <h1 className="mt-4 font-display text-5xl font-bold leading-[1.05] tracking-tight text-white sm:text-6xl">
              Explainable preventive<br />
              <span className="bg-gradient-to-r from-brand-300 to-teal-400 bg-clip-text text-transparent">healthcare intelligence</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-slate-400">
              MediShield AI turns clinical indicators into transparent risk insight. Real machine-learning
              models, honest probabilities, and an explanation you can actually understand.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a href="#assessments" className="btn-primary">Start an assessment <ArrowRight size={18} /></a>
              <Link to="/dashboard" className="btn-ghost">View dashboard</Link>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.7, delay: 0.15 }}
            className="relative mx-auto"
          >
            <div className="animate-float glass grid h-64 w-64 place-items-center rounded-[2rem] shadow-glow">
              <ShieldPlus size={110} className="text-brand-400" strokeWidth={1.3} />
            </div>
            <div className="glass absolute -left-8 top-6 flex items-center gap-2 rounded-xl px-3 py-2 text-sm">
              <Stethoscope size={16} className="text-teal-300" /> 3 risk models
            </div>
            <div className="glass absolute -right-6 bottom-8 flex items-center gap-2 rounded-xl px-3 py-2 text-sm">
              <Brain size={16} className="text-brand-300" /> SHAP explained
            </div>
          </motion.div>
        </div>
      </section>

      {/* Assessments */}
      <section id="assessments" className="mx-auto max-w-6xl px-5 py-16">
        <div className="mb-10">
          <span className="eyebrow">Risk assessments</span>
          <h2 className="mt-3 font-display text-3xl font-bold text-white">Choose an assessment</h2>
          <p className="mt-2 text-slate-400">Each model is trained on a public medical dataset and reports its own accuracy.</p>
        </div>

        {err && (
          <div className="glass mb-6 rounded-xl p-4 text-sm text-amber-300">
            Cannot reach the model API. Make sure the backend is running (see the repo README).
          </div>
        )}

        <div className="grid gap-6 md:grid-cols-3">
          {(diseases.length ? diseases : Object.keys(DISEASE_META).map((id) => ({ id, title: DISEASE_META[id].label, metrics: null, n_fields: 0 } as unknown as DiseaseSummary))).map((d, i) => {
            const meta = DISEASE_META[d.id];
            return (
              <motion.div
                key={d.id}
                initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
              >
                <Link to={`/assess/${d.id}`} className="glass glass-hover group flex h-full flex-col p-6">
                  <div className="mb-4 grid h-12 w-12 place-items-center rounded-xl ring-1 ring-white/10"
                       style={{ color: meta?.accent, background: `${meta?.accent}1a` }}>
                    {ICONS[d.id] ?? <Activity size={22} />}
                  </div>
                  <h3 className="font-display text-xl font-semibold text-white">{meta?.label ?? d.title}</h3>
                  <p className="mt-2 flex-1 text-sm text-slate-400">{meta?.blurb}</p>
                  {d.metrics && (
                    <div className="mt-5 flex items-center gap-4 border-t border-white/5 pt-4 text-xs text-slate-400">
                      <span>ROC-AUC <b className="text-brand-300">{d.metrics.roc_auc}</b></span>
                      <span>{d.metrics.n_samples.toLocaleString()} samples</span>
                    </div>
                  )}
                  <span className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-brand-400 transition group-hover:gap-2.5">
                    Assess now <ArrowRight size={15} />
                  </span>
                </Link>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Report analysis banner */}
      <section className="mx-auto max-w-6xl px-5 py-10">
        <Link to="/report" className="glass glass-hover group flex flex-col items-start gap-5 p-8 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-brand-500/10 text-brand-400 ring-1 ring-brand-500/20">
              <FileScan size={24} />
            </div>
            <div>
              <span className="eyebrow">New</span>
              <h3 className="mt-1 font-display text-2xl font-semibold text-white">Analyze a lab report</h3>
              <p className="mt-1.5 max-w-xl text-sm text-slate-400">
                Upload a blood-test or lab report (PDF or image). MediShield reads every value, flags what's
                outside the normal range, and explains it in plain language.
              </p>
            </div>
          </div>
          <span className="btn-primary shrink-0">Upload a report <ArrowRight size={18} /></span>
        </Link>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-6xl px-5 py-16">
        <div className="mb-10">
          <span className="eyebrow">Why it's different</span>
          <h2 className="mt-3 font-display text-3xl font-bold text-white">Transparency, not a black box</h2>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="glass p-6"
            >
              <div className="mb-4 grid h-11 w-11 place-items-center rounded-xl bg-brand-500/10 text-brand-400 ring-1 ring-brand-500/20">
                {f.icon}
              </div>
              <h3 className="font-semibold text-white">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">{f.body}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Pipeline */}
      <section className="mx-auto max-w-6xl px-5 py-16">
        <div className="glass p-8 sm:p-10">
          <span className="eyebrow">How it works</span>
          <h2 className="mt-3 font-display text-3xl font-bold text-white">From input to explained insight</h2>
          <div className="mt-8 grid gap-4 md:grid-cols-4">
            {[
              { n: "01", t: "Enter indicators", d: "Provide clinical and lifestyle values through a guided form." },
              { n: "02", t: "Model predicts", d: "A gradient-boosted model estimates your risk probability." },
              { n: "03", t: "SHAP explains", d: "The platform attributes the result to each contributing factor." },
              { n: "04", t: "Act preventively", d: "Get tailored, evidence-informed preventive recommendations." },
            ].map((s) => (
              <div key={s.n} className="relative rounded-xl border border-white/5 bg-white/[0.02] p-5">
                <span className="font-display text-3xl font-bold text-brand-500/40">{s.n}</span>
                <h4 className="mt-2 font-semibold text-white">{s.t}</h4>
                <p className="mt-1.5 text-sm text-slate-400">{s.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
