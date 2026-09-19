import axios from "axios";

export const API_BASE =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ||
  "http://127.0.0.1:8010";

const client = axios.create({ baseURL: API_BASE, timeout: 30000 });

// ---- Types ----
export interface Metrics {
  roc_auc: number;
  accuracy: number;
  f1: number;
  n_samples: number;
  n_positive: number;
  prevalence: number;
}

export interface FieldOption { value: string | number; label: string; }

export interface Field {
  name: string;
  label: string;
  type: "number" | "select" | "toggle";
  unit?: string;
  min?: number;
  max?: number;
  step?: number;
  default?: string | number;
  help?: string;
  options?: FieldOption[];
}

export interface DiseaseSummary {
  id: string;
  title: string;
  metrics: Metrics;
  n_fields: number;
}

export interface DiseaseSchema {
  id: string;
  title: string;
  positive_label: string;
  fields: Field[];
  metrics: Metrics;
}

export interface Factor {
  field: string;
  label: string;
  value: string;
  contribution: number;
  direction: "increases" | "decreases";
  impact_pct: number;
}

export interface Recommendation {
  category: string;
  title: string;
  detail: string;
  severity: "high" | "medium" | "info";
}

export interface PredictResult {
  disease: string;
  title: string;
  probability: number;
  risk_percent: number;
  base_rate: number;
  times_average: number;
  band: string;
  positive_label: string;
  top_factors: Factor[];
  all_factors: Factor[];
  recommendations: Recommendation[];
  model_metrics: Metrics;
  disclaimer: string;
}

// ---- Calls ----
export const getDiseases = () =>
  client.get<{ diseases: DiseaseSummary[] }>("/api/diseases").then((r) => r.data.diseases);

export const getSchema = (disease: string) =>
  client.get<DiseaseSchema>(`/api/diseases/${disease}/schema`).then((r) => r.data);

export const predict = (disease: string, features: Record<string, unknown>) =>
  client.post<PredictResult>(`/api/predict/${disease}`, { features }).then((r) => r.data);

export const getCapabilities = () =>
  client.get<{ copilot_enabled: boolean }>("/api/capabilities").then((r) => r.data);
