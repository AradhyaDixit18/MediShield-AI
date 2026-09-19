import { motion } from "framer-motion";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import type { Factor } from "../lib/api";

interface Props { factors: Factor[]; }

/**
 * SHAP-style explanation: horizontal bars showing each factor's signed
 * contribution to the risk score. Red bars push risk up, green pull it down.
 */
export default function FactorChart({ factors }: Props) {
  const max = Math.max(...factors.map((f) => Math.abs(f.contribution)), 0.0001);

  return (
    <div className="space-y-3">
      {factors.map((f, i) => {
        const width = (Math.abs(f.contribution) / max) * 100;
        const up = f.direction === "increases";
        return (
          <motion.div
            key={f.field}
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.05 * i, duration: 0.4 }}
            className="group"
          >
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="flex items-center gap-2 font-medium text-slate-200">
                {up ? <ArrowUpRight size={15} className="text-rose-400" /> : <ArrowDownRight size={15} className="text-emerald-400" />}
                {f.label}
                <span className="text-slate-500">· {f.value}</span>
              </span>
              <span className={`tabular-nums text-xs ${up ? "text-rose-300" : "text-emerald-300"}`}>
                {f.impact_pct}%
              </span>
            </div>
            <div className="h-2.5 w-full overflow-hidden rounded-full bg-white/5">
              <motion.div
                className={`h-full rounded-full ${up ? "bg-gradient-to-r from-rose-500/70 to-rose-400" : "bg-gradient-to-r from-emerald-500/70 to-emerald-400"}`}
                initial={{ width: 0 }}
                animate={{ width: `${width}%` }}
                transition={{ delay: 0.05 * i + 0.15, duration: 0.6, ease: "easeOut" }}
              />
            </div>
          </motion.div>
        );
      })}
      <div className="flex items-center gap-4 pt-2 text-xs text-slate-500">
        <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-rose-400" /> increases risk</span>
        <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-emerald-400" /> decreases risk</span>
      </div>
    </div>
  );
}
