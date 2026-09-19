import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { useEffect, useState } from "react";
import { bandColor } from "../lib/ui";

interface Props {
  percent: number;
  band: string;
  timesAverage: number;
}

export default function RiskGauge({ percent, band, timesAverage }: Props) {
  const colors = bandColor(band);
  const size = 240;
  const stroke = 16;
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const target = Math.min(Math.max(percent, 0), 100);

  const count = useMotionValue(0);
  const [display, setDisplay] = useState(0);
  const offset = useTransform(count, (v) => circ - (v / 100) * circ);

  useEffect(() => {
    const controls = animate(count, target, { duration: 1.4, ease: "easeOut" });
    const unsub = count.on("change", (v) => setDisplay(v));
    return () => { controls.stop(); unsub(); };
  }, [target]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="relative flex flex-col items-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth={stroke} />
        <motion.circle
          cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={colors.hex} strokeWidth={stroke} strokeLinecap="round"
          strokeDasharray={circ} style={{ strokeDashoffset: offset }}
          filter="drop-shadow(0 0 8px currentColor)"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`font-display text-5xl font-bold ${colors.text}`}>{display.toFixed(1)}<span className="text-2xl">%</span></span>
        <span className="mt-1 text-xs uppercase tracking-widest text-slate-400">risk score</span>
      </div>
      <div className={`mt-5 rounded-full px-4 py-1.5 text-sm font-semibold ${colors.bg} ${colors.text}`}>
        {band}
      </div>
      <p className="mt-2 text-sm text-slate-400">
        <span className={`font-semibold ${colors.text}`}>{timesAverage}×</span> the population average
      </p>
    </div>
  );
}
