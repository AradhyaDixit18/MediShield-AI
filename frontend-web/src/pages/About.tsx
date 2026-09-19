import { useEffect, useState } from "react";
import { Brain, Database, Cpu, ShieldCheck, Layers } from "lucide-react";
import { getDiseases, type DiseaseSummary } from "../lib/api";

const STACK = [
  { icon: <Cpu size={18} />, title: "Machine learning", items: ["XGBoost gradient boosting", "scikit-learn preprocessing", "Per-disease trained models"] },
  { icon: <Brain size={18} />, title: "Explainable AI", items: ["SHAP TreeExplainer", "Per-factor attribution", "Signed contribution charts"] },
  { icon: <Layers size={18} />, title: "Backend", items: ["FastAPI + Pydantic", "Model registry & warm start", "REST prediction API"] },
  { icon: <Database size={18} />, title: "Frontend", items: ["React + TypeScript + Vite", "Tailwind CSS + Framer Motion", "Recharts visualizations"] },
];

export default function About() {
  const [diseases, setDiseases] = useState<DiseaseSummary[]>([]);
  useEffect(() => { getDiseases().then(setDiseases).catch(() => {}); }, []);

  return (
    <div className="mx-auto max-w-5xl px-5 py-12">
      <span className="eyebrow">About the project</span>
      <h1 className="mt-2 font-display text-4xl font-bold text-white">Explainable, preventive, honest</h1>
      <p className="mt-4 max-w-3xl text-lg leading-relaxed text-slate-400">
        MediShield AI is a preventive-healthcare intelligence platform. It predicts disease risk with real
        machine-learning models, then explains every prediction with SHAP so the result is transparent rather
        than a black box. Each model reports its own out-of-sample accuracy, and no result is presented as a
        diagnosis.
      </p>

      <div className="mt-10 grid gap-5 sm:grid-cols-2">
        {STACK.map((s) => (
          <div key={s.title} className="glass p-6">
            <div className="mb-3 flex items-center gap-2.5">
              <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand-500/10 text-brand-400 ring-1 ring-brand-500/20">{s.icon}</span>
              <h3 className="font-display font-semibold text-white">{s.title}</h3>
            </div>
            <ul className="space-y-1.5 text-sm text-slate-400">
              {s.items.map((i) => <li key={i} className="flex items-center gap-2"><span className="h-1 w-1 rounded-full bg-brand-400" />{i}</li>)}
            </ul>
          </div>
        ))}
      </div>

      {diseases.length > 0 && (
        <div className="glass mt-6 p-6 sm:p-7">
          <h3 className="mb-4 font-display text-lg font-semibold text-white">Model performance</h3>
          <div className="grid gap-4 sm:grid-cols-3">
            {diseases.map((d) => (
              <div key={d.id} className="rounded-xl border border-white/5 bg-white/[0.02] p-5">
                <div className="font-medium text-white">{d.title}</div>
                <div className="mt-3 space-y-1.5 text-sm text-slate-400">
                  <div className="flex justify-between"><span>ROC-AUC</span><b className="text-brand-300">{d.metrics.roc_auc}</b></div>
                  <div className="flex justify-between"><span>Accuracy</span><span className="text-slate-300">{d.metrics.accuracy}</span></div>
                  <div className="flex justify-between"><span>Samples</span><span className="text-slate-300">{d.metrics.n_samples.toLocaleString()}</span></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="glass mt-6 flex items-start gap-3 p-6">
        <ShieldCheck size={20} className="mt-0.5 shrink-0 text-brand-400" />
        <p className="text-sm leading-relaxed text-slate-400">
          <b className="text-slate-200">Medical disclaimer.</b> MediShield AI is intended for educational and
          preventive-awareness purposes only. It does not provide a medical diagnosis and is not a substitute for
          professional medical advice. Always consult a qualified healthcare provider.
        </p>
      </div>
    </div>
  );
}
